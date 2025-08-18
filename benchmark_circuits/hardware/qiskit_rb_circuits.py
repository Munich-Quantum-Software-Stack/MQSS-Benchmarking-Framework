import numpy as np
import qiskit.circuit.library as circuits

from qiskit_experiments.library import StandardRB, InterleavedRB
from qiskit_experiments.framework import ParallelExperiment, BatchExperiment

# For simulation
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeAlmadenV2

backend = AerSimulator.from_backend(FakeAlmadenV2())

lengths = np.arange(1, 800, 200)
num_samples = 10
seed = 1010
qubits = [0]

# Run an RB experiment on qubit 0
exp1 = StandardRB(qubits, lengths, num_samples=num_samples, seed=seed)
expdata1 = exp1.run(backend).result()
results1 = expdata1.analysis_results()

# View result data
print("Gate error ratio: %s" % expdata1.experiment.analysis.options.gate_error_ratio)
for result in results1:
    print(result)