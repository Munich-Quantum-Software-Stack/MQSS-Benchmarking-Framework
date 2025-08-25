from manager import benchmark_manager as bm

import pandas as pd
import numpy as np
import json
import datetime
import time

def count_1q_gates(circuit):
    num_1q_gates = 0
    for gate in circuit.count_ops():
        if 'Clifford-1Q' in gate:
            num_1q_gates += 1
    return num_1q_gates

def count_2q_gates(circuit):
    num_2q_gates = 0
    for gate in circuit.count_ops():
        if 'Clifford-2Q' in gate:
            num_2q_gates += 1
    return num_2q_gates

config = json.load(open("./hw_benchmark_config.json"))

# Test avaiable benchmarks
# available_benchmarks = bm.BenchmarkManager.get_available_benchmarks("HW")
# print("-----------------------------------------")
# print("Available benchmarks:", available_benchmarks)
# print("-----------------------------------------")

# Benchmark dataframe
benchmark_df = pd.DataFrame(columns=[
    "circuit_name", "num_qubits", "num_shots", "depth", "num_1q_gates", "num_2q_gates", "gate_counts", 
    "circuit_width", "backend_name", "submit_time", "start_time", "end_time", "run_time",
    "entanglement_ratio", "gate_density", "qubit_connectivity_req",
    "power_usage_peak", "power_usage_avg", "result_fidelity"
])

# Test class benchmark manager and generate circuits
benchmark_manager = bm.BenchmarkManager(config)
list_of_hw_bench_circuits = benchmark_manager.generate_benchmark_circuits()
print("List of HW benchmark circuits: ")
for id, circuit in enumerate(list_of_hw_bench_circuits):
    circuit_name = "RB_Standard" + str(id)
    num_qubits = circuit.num_qubits
    depth = circuit.depth()
    num_1q_gates = count_1q_gates(circuit)
    num_2q_gates = count_2q_gates(circuit)
    gate_counts = len(circuit.count_ops())
    circuit_width = circuit.width()
    backend_name = 'QExa20'
    num_shots = 1000
    entanglement_ratio = None
    gate_density = None
    qubit_connectivity_req = None
    print(f"Circuit: {circuit_name} | Qubits: {num_qubits} | Depth: {depth} \
          | 1Q gates: {num_1q_gates} | 2Q gates: {num_2q_gates} \
          | Gate counts: {gate_counts} | Width: {circuit_width}")
    
    # submit the circuit to MQSS backend
    submit_time = datetime.datetime.now()

    # start time
    time.sleep(1)
    start_time = datetime.datetime.now()

    # run the benchmark circuit
    time.sleep(1)

    # end time
    end_time = datetime.datetime.now()

    # run time
    run_time = (end_time - start_time).total_seconds()

    # other info
    power_usage_peak = None
    power_usage_avg = None
    result_fidelity = None

    # append to dataframe
    benchmark_df = pd.concat([benchmark_df, pd.DataFrame([{
        "circuit_name": circuit_name,
        "num_qubits": num_qubits,
        "num_shots": num_shots,
        "depth": depth,
        "num_1q_gates": num_1q_gates,
        "num_2q_gates": num_2q_gates,
        "gate_counts": gate_counts,
        "circuit_width": circuit_width,
        "backend_name": backend_name,
        "submit_time": submit_time,
        "start_time": start_time,
        "end_time": end_time,
        "run_time": run_time,
        "entanglement_ratio": entanglement_ratio,
        "gate_density": gate_density,
        "qubit_connectivity_req": qubit_connectivity_req,
        "power_usage_peak": power_usage_peak,
        "power_usage_avg": power_usage_avg,
        "result_fidelity": result_fidelity
    }])], ignore_index=True)

print("--------------------------------------------------")
print(benchmark_df)
print("--------------------------------------------------")
benchmark_df.to_csv("../results/data_hw_rb_benchmark.csv", sep=',', index=False)


