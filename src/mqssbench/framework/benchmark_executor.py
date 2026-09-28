"""Executors that run quantum circuits and collect results.

Three executor types are available:
- ``BenchmarkExecutor``: base class for custom executors.
- ``DefaultBenchmarkExecutor``: runs circuits sequentially via the adapter.
- ``HybridBenchmarkExecutor``: iterative optimization loop (variational algorithms).
"""

from abc import ABC, abstractmethod
from typing import List

from mqssbench.framework.circuit_generator import CircuitGenerator

from .checkpoint import (
    CheckpointedRunError,
    CheckpointState,
    execution_result_from_dict,
    execution_result_to_dict,
    save_checkpoint,
)
from .types import BenchmarkRunStatus, CircuitSpec, ProfilingMetrics, RunContext, ExecutionResult
from scipy.optimize import minimize
import time
from datetime import datetime

DEFAULT_HYBRID_MAXITER = 250


class BenchmarkExecutor(ABC):
    """Base class for benchmark executors.

    Executors receive circuits or generators and produce execution results.
    Each executor encapsulates a specific execution strategy.
    The ``context`` is available during execution for accessing the adapter,
    parameters, and other run metadata.
    """

    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def run(
        self, circuits: List[CircuitSpec], context: RunContext
    ) -> List[ExecutionResult]:
        """Execute the provided circuits."""
        ...


class DefaultBenchmarkExecutor(BenchmarkExecutor):
    """Sequential circuit executor.

    Takes a list of ``CircuitSpec`` objects and runs them sequentially using
    the adapter from the ``context``. Preserves circuit metadata in each result.
    Suitable for non-adaptive benchmarks.
    """

    def run(
        self, circuits: List[CircuitSpec], context: RunContext
    ) -> List[ExecutionResult]:
        """Execute circuits using the adapter from context.

        Checkpoints progress after every circuit (via ``context.checkpoint_path``)
        so a failed job submission can be resumed without re-running circuits
        that already completed. If ``context.resume_state`` is set, execution
        picks up right after the last checkpointed circuit.
        """
        resume_state = context.resume_state
        if resume_state is not None:
            results = [
                execution_result_from_dict(d) for d in resume_state.completed_results
            ]
            start_index = resume_state.next_circuit_index
        else:
            results = []
            start_index = 0

        def checkpoint(status: BenchmarkRunStatus, error: str | None = None) -> None:
            if context.checkpoint_path is None:
                return
            save_checkpoint(
                CheckpointState(
                    run_id=context.run_id,
                    run_dir=context.run_dir,
                    config=context.metadata.get("raw_config", {}),
                    status=status,
                    error=error,
                    next_circuit_index=len(results),
                    completed_results=[execution_result_to_dict(r) for r in results],
                )
            )

        for spec in circuits[start_index:]:
            circuit_payload = spec.circuit
            if "num_qubits" not in spec.metadata:
                raise ValueError(
                    "CircuitSpec.metadata must include a 'num_qubits' entry."
                )
            num_qubits = spec.metadata["num_qubits"]

            run_result: ExecutionResult
            try:
                if callable(circuit_payload):
                    run_result = context.adapter.execute_circuit(
                        context, circuit_payload, num_qubits=num_qubits
                    )
                else:
                    run_result = context.adapter.execute_circuit(
                        context, lambda: circuit_payload, num_qubits=num_qubits
                    )
            except Exception as exc:
                checkpoint(BenchmarkRunStatus.FAILED, error=str(exc))
                if context.checkpoint_path is not None:
                    raise CheckpointedRunError(context.checkpoint_path, exc) from exc
                raise

            # set metadata in in new instance for immutability
            run_result = ExecutionResult(
                job_id=run_result.job_id,
                counts=run_result.counts,
                profiling_metrics=run_result.profiling_metrics,
                metadata=dict(spec.metadata),
                circuit_depth=run_result.circuit_depth,
            )
            results.append(run_result)
            checkpoint(BenchmarkRunStatus.RUNNING)

        checkpoint(BenchmarkRunStatus.COMPLETED)
        return results


def maxcut_expectation(counts: dict, edges: list[tuple[int, int]]) -> float:
    """
    Calculate the MaxCut expectation value for a given bitstring and edge list.
    Each edge contributes +1 if the bits are different, 0 otherwise.
    """
    value = 0
    for bitstring, count in counts.items():
        for i, j in edges:
            if bitstring[i] != bitstring[j]:
                value += count
            # else:
            #     value -= count
    value /= sum(counts.values())
    return value


class HybridBenchmarkExecutor(BenchmarkExecutor):
    """Hybrid benchmark executor for circuits that require both quantum and classical processing."""

    def run(
        self, generator: CircuitGenerator, context: RunContext
    ) -> List[ExecutionResult]:
        """Execute hybrid circuits using the adapter from context.

        Checkpoints progress after every fully-completed optimizer iteration
        (via ``context.checkpoint_path``). If a job submission fails mid-iteration,
        that in-flight iteration's results are discarded and only prior completed
        iterations are checkpointed - ``scipy.optimize.minimize`` does not expose a
        way to serialize/restore its internal optimizer state (e.g. COBYLA's
        simplex), so resuming re-enters ``minimize`` as a warm start from the last
        completed iteration's parameters rather than a true mid-optimization resume.
        """
        resume_state = context.resume_state
        initial_params = list(context.params["parameters"])

        if resume_state is not None:
            iteration = resume_state.iteration
            iteration_times: list[float] = list(resume_state.iteration_times)
            computation_times: list[float] = list(resume_state.computation_times)
            execution_start_times: list[str] = list(resume_state.execution_start_times)
            execution_end_times: list[str] = list(resume_state.execution_end_times)
            objective_values: list[ExecutionResult] = [
                execution_result_from_dict(d) for d in resume_state.completed_results
            ]
            context.params["expval"] = list(resume_state.expval_history)
            last_x = resume_state.last_params or initial_params
            total_maxiter = resume_state.total_maxiter or DEFAULT_HYBRID_MAXITER
            x0 = last_x
        else:
            iteration = 0
            iteration_times = []
            computation_times = []
            execution_start_times = []
            execution_end_times = []
            objective_values = []
            context.params["expval"] = []
            last_x = initial_params
            total_maxiter = DEFAULT_HYBRID_MAXITER
            x0 = initial_params

        results: List[ExecutionResult] = []

        def checkpoint(status: BenchmarkRunStatus, error: str | None = None) -> None:
            if context.checkpoint_path is None:
                return
            save_checkpoint(
                CheckpointState(
                    run_id=context.run_id,
                    run_dir=context.run_dir,
                    config=context.metadata.get("raw_config", {}),
                    status=status,
                    error=error,
                    iteration=iteration,
                    last_params=list(last_x),
                    total_maxiter=total_maxiter,
                    iteration_times=list(iteration_times),
                    computation_times=list(computation_times),
                    execution_start_times=list(execution_start_times),
                    execution_end_times=list(execution_end_times),
                    expval_history=list(context.params["expval"]),
                    completed_results=[
                        execution_result_to_dict(r) for r in objective_values
                    ],
                )
            )

        def objective(x):
            start = time.time()
            nonlocal iteration, last_x

            params = context.params

            params["parameters"] = [float(v) for v in x]

            circuits = generator.generate(params)

            total_value = 0.0
            for spec in circuits:
                weight = spec.metadata.get("weight", 1.0)

                if spec.metadata.get("skip_execution"):
                    # Purely classical term (e.g. a Hamiltonian's identity
                    # coefficient) - nothing to execute on the adapter.
                    total_value += weight * spec.metadata.get("constant_value", 0.0)
                    continue

                start_time = datetime.now().strftime("%a %d-%m-%Y %H:%M:%S.%f")[:-3]
                start_computation = time.time()
                try:
                    result = context.adapter.execute_circuit(
                        context,
                        lambda: spec.circuit,
                        num_qubits=spec.metadata["num_qubits"],
                    )
                except Exception as exc:
                    checkpoint(BenchmarkRunStatus.FAILED, error=str(exc))
                    if context.checkpoint_path is not None:
                        raise CheckpointedRunError(context.checkpoint_path, exc) from exc
                    raise
                end_computation = time.time()
                end_time = datetime.now().strftime("%a %d-%m-%Y %H:%M:%S.%f")[:-3]
                computation_times.append(end_computation - start_computation)
                objective_values.append(result)
                execution_start_times.append(start_time)
                execution_end_times.append(end_time)
                

                cost_fn = spec.metadata.get("cost_fn")
                if cost_fn is not None:
                    term_value = cost_fn(result.counts)
                else:
                    # Default cost model (e.g. QAOA/MaxCut): frame a
                    # maximization as minimizing its negation.
                    term_value = maxcut_expectation(result.counts, spec.metadata["edges"]) * -1
                total_value += weight * term_value

            context.params["expval"].append(total_value)
            end = time.time()
            
            iteration_times.append(end - start)
            
            iteration += 1
            last_x = [float(v) for v in x]
            checkpoint(BenchmarkRunStatus.RUNNING)

            return total_value

        optimizer_start = time.perf_counter()
       
        res = minimize(
            objective,
            x0=context.params["parameters"],
            method="COBYLA",
            options={"maxiter": 10},
        )
        optimizer_duration = time.perf_counter() - optimizer_start
        
        params = context.params
        params["parameters"] = res.x.tolist()
        circuits = generator.generate(params)

        circuits[0].metadata["result"] = res.fun.tolist()
        circuits[0].metadata["opt_params"] = res.x.tolist()

        quantum_execution_time = sum(computation_times)
        classical_execution_time = max(optimizer_duration - quantum_execution_time, 0.0)
        print(
            f"Optimizer finished in {optimizer_duration:.3f}s "
            f"(quantum: {quantum_execution_time:.3f}s, classical: {classical_execution_time:.3f}s)"
        )

        last_params = dict(objective_values[-1].profiling_metrics.params or {})
        profiling_metrics = ProfilingMetrics(
            params={
                **last_params,
                "quantum_execution": quantum_execution_time,
                "classical_execution": classical_execution_time,
            },
            iteration_duration=iteration_times,
            multiple_execution_duration=computation_times,
            execution_start_times=execution_start_times,
            execution_end_times=execution_end_times,
        )

        # set metadata in in new instance for immutability
        run_result = ExecutionResult(
            job_id=objective_values[-1].job_id,
            counts=objective_values[-1].counts,
            profiling_metrics=profiling_metrics,
            metadata=dict(circuits[0].metadata),
            exp_value=res.fun.tolist(),
            optimal_params=res.x.tolist(),
            circuit_depth=objective_values[-1].circuit_depth,
        )
        results.append(run_result)
        checkpoint(BenchmarkRunStatus.COMPLETED)
        return results
