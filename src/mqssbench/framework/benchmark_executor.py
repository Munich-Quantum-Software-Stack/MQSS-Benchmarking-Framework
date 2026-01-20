"""Benchmark executor abstraction."""

from abc import ABC, abstractmethod
from typing import List

from mqssbench.framework.circuit_generator import CircuitGenerator

from .types import CircuitSpec, ProfilingMetrics, RunContext, ExecutionResult
from scipy.optimize import minimize
import time


class BenchmarkExecutor(ABC):
    """Abstract base class for benchmark executors."""

    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def run(
        self, circuits: List[CircuitSpec], context: RunContext
    ) -> List[ExecutionResult]:
        """Execute the provided circuits."""
        ...


class DefaultBenchmarkExecutor(BenchmarkExecutor):
    """Default implementation of benchmark executor."""

    def run(
        self, circuits: List[CircuitSpec], context: RunContext
    ) -> List[ExecutionResult]:
        """Execute circuits using the adapter from context."""
        results: List[ExecutionResult] = []
        for spec in circuits:
            circuit_payload = spec.circuit
            if "num_qubits" not in spec.metadata:
                raise ValueError(
                    "CircuitSpec.metadata must include a 'num_qubits' entry."
                )
            num_qubits = spec.metadata["num_qubits"]

            run_result: ExecutionResult
            if callable(circuit_payload):
                run_result = context.adapter.execute_circuit(
                    context, circuit_payload, num_qubits=num_qubits
                )
            else:
                run_result = context.adapter.execute_circuit(
                    context, lambda: circuit_payload, num_qubits=num_qubits
                )

            # set metadata in in new instance for immutability
            run_result = ExecutionResult(
                job_id=run_result.job_id,
                counts=run_result.counts,
                profiling_metrics=run_result.profiling_metrics,
                metadata=dict(spec.metadata),
            )
            results.append(run_result)
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
        """Execute hybrid circuits using the adapter from context."""
        results: List[ExecutionResult] = []
        context.params["expval"] = []
        iteration = 0
        iteration_times: list[float] = []
        computation_times: list[float] = []

        objective_values: list[ExecutionResult] = []

        def objective(x):
            start = time.time()
            nonlocal iteration

            params = context.params

            params["parameters"] = x

            circuits = generator.generate(params)

            results = []
            for spec in circuits:
                start_computation = time.time()
                result = context.adapter.execute_circuit(
                    context,
                    lambda: spec.circuit,
                    num_qubits=spec.metadata["num_qubits"],
                )
                end_computation = time.time()
                computation_times.append(end_computation - start_computation)
                objective_values.append(result)

                expectation_result = (
                    maxcut_expectation(result.counts, spec.metadata["edges"]) * -1
                )
                context.params["expval"].append(expectation_result)
                end = time.time()
                print(f"Time elapsed: {end - start} seconds")
                iteration_times.append(end - start)
                print(f"Iteration {iteration}: Exp. value: {expectation_result}")
                iteration += 1
                results.append(expectation_result)

            return results[0]

        res = minimize(
            objective,
            x0=context.params["parameters"],
            method="COBYLA",
            options={"maxiter": 250},
        )

        params = context.params
        params["parameters"] = res.x.tolist()

        circuits = generator.generate(params)

        circuits[0].metadata["result"] = res.fun.tolist()
        circuits[0].metadata["opt_params"] = res.x.tolist()

        profiling_metrics = ProfilingMetrics(
            params=objective_values[-1].profiling_metrics.params,
            iteration_duration=iteration_times,
            multiple_execution_duration=computation_times,
        )

        # set metadata in in new instance for immutability
        run_result = ExecutionResult(
            job_id=objective_values[-1].job_id,
            counts=objective_values[-1].counts,
            profiling_metrics=profiling_metrics,
            metadata=dict(circuits[0].metadata),
            exp_value=res.fun.tolist(),
            optimal_params=res.x.tolist(),
        )
        results.append(run_result)
        return results
