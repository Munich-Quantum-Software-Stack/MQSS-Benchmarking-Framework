import os
import math
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt

from qiskit_aer import AerSimulator

from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
from qiskit.quantum_info.operators import Operator
from qiskit.primitives import BackendSampler

from time import process_time, sleep
from scipy.optimize import minimize

from mqss.qiskit_adapter import MQSSQiskitAdapter

# for setting up logging
logger = logging.getLogger("ghz_example")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")

# for processing the arguments
parser = argparse.ArgumentParser()
parser.add_argument("-bak", "--backend", type=str, default="AerSimulator", 
                    help="Type of the backend we want to run")
parser.add_argument("-qub", "--qubits", type=int, default=4, 
                    help="The amount of numbers/qubits we want to randomly generate")
parser.add_argument("-sho", "--shots", type=int, default=1000, 
                    help="The numbers of shots we want to run the circuit with")
args = vars(parser.parse_args())
backend_name    = args["backend"]
num_qubits      = args["qubits"]
num_shots       = args["shots"]

logger.info('------------------------------------------')
logger.info('Testing GHZ example:')
logger.info(' + Num. qubits: %d', num_qubits)
logger.info(' + Backend: %s', backend_name)
logger.info(' + Num. shots: %d', num_shots)
logger.info('------------------------------------------')

# for setting up the quantum backend
if backend_name == "AerSimulator":
    backend = AerSimulator()
else:
    token_val = "hskHPJhuLBkh2WvhNemZRjUBpySy4LoeWW3Gjh8HFsgxtAega9zxwU8b4Bn4NMCC"
    mqss_adapter = MQSSQiskitAdapter(token=token_val)
    [backend] = mqss_adapter.backends(name=backend_name)

# for setting up the circuit
qc = QuantumCircuit(num_qubits)
qc.h(0)
for i in range(num_qubits - 1):
    qc.cx(0, i+1)
qc.measure_all()

# submit the jobs
start_submit_time = process_time()
job = backend.run(qc, shots=1000)
end_submit_time = process_time()

logger.info(f'Start submit time: {start_submit_time}')
logger.info(f'End submit time: {end_submit_time}')
logger.info(f'Submit latency: {end_submit_time - start_submit_time}s')

# get the results
results = job.result().get_counts()
get_result_time = process_time()

logger.info(f'Get result time: {get_result_time}')
logger.info(f'Completion time: {get_result_time - start_submit_time}s')

logger.info('------------------------------------------')
logger.info(f'Counts for GHZ example: {results}')
logger.info('------------------------------------------')