import os
import math
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt

from qiskit_aer import AerSimulator

from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
from qiskit.quantum_info.operators import Operator

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

print('------------------------------------------')
print('Testing GHZ example:')
print(' + Num. qubits: ', num_qubits)
print(' + Backend: ', backend_name)
print(' + Num. shots: ', num_shots)
print('------------------------------------------')

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
results = job.result()
end_submit_time = process_time()

result_dict = job.result().to_dict()
qserver_submit_time = result_dict["timestamps"]["submitted"]
qserver_scheduled_time = result_dict["timestamps"]["scheduled"]
qserver_completed_time = result_dict["timestamps"]["completed"]

print(f'Completion time: {start_submit_time - end_submit_time}s')
print(f'Server submitted time: {qserver_submit_time}')
print(f'Server scheduled time: {qserver_scheduled_time}')
print(f'Server completed time: {qserver_completed_time}')
# print(f'Submit latency: {qserver_scheduled_time - start_submit_time}s')
# print(f'Get-back-result latency: {end_submit_time - qserver_completed_time}s')

counts = results.get_counts()
print('------------------------------------------')
print(f'Counts for GHZ example: {counts}')
print('------------------------------------------')