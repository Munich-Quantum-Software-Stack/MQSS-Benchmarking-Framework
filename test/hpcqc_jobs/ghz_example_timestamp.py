import os
import math
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt

from qiskit_aer import AerSimulator

from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
from qiskit.quantum_info.operators import Operator

from time import process_time, sleep, perf_counter
from datetime import datetime, timezone
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
# local wall-clock timestamps for correlation with server times
local_start_dt = datetime.now()
start_run_time = perf_counter()
job = backend.run(qc, shots=num_shots)
results = job.result()
end_run_time = perf_counter()
local_end_dt = datetime.now()

result_dict = job.result().to_dict()
ts = result_dict["timestamps"]
fmt = "%Y-%m-%d %H:%M:%S.%f"
qserver_submitted_dt = ts["submitted"] # datetime.strptime(ts["submitted"], fmt)
qserver_scheduled_dt = ts["scheduled"] # datetime.strptime(ts["scheduled"], fmt)
qserver_completed_dt = ts["completed"] # datetime.strptime(ts["completed"], fmt)

print(f'------------------------------------------')
print(f'Completion time: {end_run_time-start_run_time:.3f}s')
print(f'------------------------------------------')
print(f'Quantum server submitted time: {qserver_submitted_dt}')
print(f'Quantum server scheduled time: {qserver_scheduled_dt}')
print(f'Quantum server completed time: {qserver_completed_dt}')
print(f'Quantum server queue wait latency (scheduled-submitted): {(qserver_scheduled_dt - qserver_submitted_dt).total_seconds():.3f}s')
print(f'Quantum server completion time (completed-scheduled): {(qserver_completed_dt - qserver_scheduled_dt).total_seconds():.3f}s')
print(f'------------------------------------------')
# local vs server correlation (only meaningful if clocks are comparable)
print(f"Local<->server submit latency (submitted-local_start_run): {(qserver_submitted_dt - local_start_dt).total_seconds():.3f}s")
print(f"Local<->server result-receiv completion latency (local_end-completed): {(local_end_dt - qserver_completed_dt).total_seconds():.3f}s")
print(f'------------------------------------------')

counts = results.get_counts()
print('------------------------------------------')
print(f'Counts for GHZ example: {counts}')
print('------------------------------------------')