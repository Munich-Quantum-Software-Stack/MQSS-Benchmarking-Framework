# MQSS-Benchmarking-Suite

This is a benchmarking suite for evaluating quantum circuits and hardware performance. It provides structured benchmarks along with circuit feature extraction, and standardized experimental runtime/power metrics.

## Benchmark Groups

### 1. Hardware Benchmarks
Low-level tests designed to evaluate physical hardware characteristics.
- Randomized Benchmarking (RB)
- Quantum Volume circuits
- Clifford+T circuits
- Crosstalk detection circuits

### 2. Algorithm Benchmarks
Standard quantum algorithms used to evaluate compilation, optimization, and logical execution.
- Quantum Phase Estimation
- Grover’s Search
- Quantum Fourier Transform (QFT)
- Variational Quantum Eigensolver (VQE)

### 3. Application Benchmarks
End-user workloads that represent realistic quantum applications.
- Molecular simulation (e.g., H2, LiH)
- Optimization (e.g., MaxCut)
- Quantum machine learning (e.g., QNN, QSVM)

Each circuit is tagged with metadata including domain, complexity, and required capabilities.

---

## Dataformat: Circuit Features

Each circuit is automatically analyzed to extract structural and logical features:

- `circuit_name`
- `num_qubits`
- `circuit_depth`
- `num_1q_gates`
- `num_2q_gates`
- `gate_counts` (e.g., {"H": 10, "CX": 20})
- `width`
- `entanglement_ratio`
- `gate_density`
- `qubit_connectivity_req`

Additional metrics (optional):
- Circuit graph diameter
- Treewidth
- Simulability (tensor contraction complexity)

---

## Dataformat: Experimental Benchmark Metrics

The benchmarking system captures standardized runtime data from simulators and real quantum devices:

| Metric                | Description                          |
|-----------------------|--------------------------------------|
| `submitted_time`      | Time job was submitted               |
| `start_time`          | Time execution began                 |
| `end_time`            | Time execution ended                 |
| `queue_delay`         | Time spent waiting in queue          |
| `runtime`             | Actual execution duration            |
| `power_usage_peak`    | Max power usage (if available)       |
| `power_usage_avg`     | Average power usage                  |
| `shots`               | Number of circuit repetitions        |
| `backend_name`        | Device or simulator used             |
| `temperature_drift`   | Change in qubit/control stability    |
| `result_fidelity`     | Output accuracy vs ideal simulation  |
| `error_mitigation_applied` | Whether error mitigation used |

---

## Tooling & Automation

TBA: job scripts for performing the benchmarks.

---

## Output & Reporting

Benchmark results are exportable as JSON or CSV and can be visualized through custom dashboards.

---

## Contribution

TBD

---

## License

TBD
