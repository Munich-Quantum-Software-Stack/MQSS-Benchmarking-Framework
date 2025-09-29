from mqt.bench import BenchmarkLevel, get_benchmark


# TODO: Add dynamic args for different inputs
def get_sw_benchmark_by_name(
    name: str, num_qubits: int, level: BenchmarkLevel = BenchmarkLevel.ALG
):
    """Given a name and number of qubits, returns a benchmark from mqt.bench as a qiskit.QuantumCircuit object.

    Args:
        name (str): Name of the algorithm
        num_qubits (int): Number of qubitts
        level (_type_, optional): Level of optimization. Defaults to BenchmarkLevel.ALG.
    """
    circuit = get_benchmark(
        benchmark=name, level=BenchmarkLevel.ALG, circuit_size=num_qubits
    )

    return circuit
