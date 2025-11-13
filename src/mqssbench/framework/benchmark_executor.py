"""Benchmark executor abstraction."""

from abc import ABC, abstractmethod
from typing import Any, List

from .types import CircuitSpec, RunContext, ExecutionResult


class BenchmarkExecutor(ABC):
    """Abstract base class for benchmark executors."""
    
    def __init__(self, context: RunContext):
        self.context = context

    @abstractmethod
    def run(self, circuits: List[CircuitSpec], context: RunContext) -> List[ExecutionResult]:
        """Execute the provided circuits."""
        ...


class DefaultBenchmarkExecutor(BenchmarkExecutor):
    """Default implementation of benchmark executor."""
    
    def run(self, circuits: List[CircuitSpec], context: RunContext) -> List[ExecutionResult]:
        """Execute circuits using the adapter from context."""
        results: List[ExecutionResult] = []
        for spec in circuits:
            circuit_payload = spec.circuit
            if "num_qubits" not in spec.metadata:
                raise ValueError("CircuitSpec.metadata must include a 'num_qubits' entry.")
            num_qubits = spec.metadata["num_qubits"]
            
            run_result: ExecutionResult
            if callable(circuit_payload):
                run_result = context.adapter.execute_circuit(context, circuit_payload, num_qubits=num_qubits)
            else:
                run_result = context.adapter.execute_circuit(context, lambda: circuit_payload, num_qubits=num_qubits)
            
            # set metadata in in new instance for immutability
            run_result = ExecutionResult(
                counts=run_result.counts,
                profiling_metrics=run_result.profiling_metrics,
                metadata=dict(spec.metadata)
            )
            results.append(run_result)
        return results

