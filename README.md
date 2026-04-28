<a href="https://gitmoji.dev">
  <img
    src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square"
    alt="Gitmoji"
  />
</a>

# MQSS Benchmarking Framework

## Overview

MQSS Benchmarking Framework is an automated and reproducable tool for uniting Quantum Computing Benchmarks. It has 4 main pillars:

- Hardware Benchmarks
- Software Benchmarks
- Simulator Benchmarks
- Algorithmic Benchmarks

## 🛠️ Installation

This project leverages [uv](https://github.com/astral-sh/uv) for dependency management and reproducibility, making setup and collaboration straightforward.
To get started, ensure you have Python installed. Then, follow these steps to set up your environment using `uv`:

1. **Install uv** (if you don't have it already):

   ```bash
   pip install uv
   ```

2. **Sync your environment with the project's dependencies:**

   ```bash
   uv sync
   ```

## 🚀 Usage

MQSS Benchmarking Framework can be used in two ways: through a simple command-line interface or directly as a Python library.

## 💻 CLI Usage

After installation, the command `mqssbench` becomes available system-wide.

### Listing benchmarks

```bash
mqssbench list
```

This prints every benchmark registered under the `origin/source/name` structure, including internal, external and user-defined benchmarks.

### Running benchmarks

```bash
mqssbench run --config path/to/config.yaml
```

The `--config` file may contain either:
1. a single benchmark configuration (dict)
2. or a list of benchmark configurations (each a full config dict)

When a list is provided, mqssbench runs each benchmark sequentially using the same execution engine.

In development setups, you can run the CLI commands through `uv`:

```bash
uv run mqssbench list
uv run mqssbench run --config path/to/config.yaml
```

To explore all available commands and options:

```bash
mqssbench --help
```

### Verbosity and logging

The CLI supports adjustable logging verbosity for debugging and inspection.

By default, only warnings and errors are shown.

Increase verbosity by repeating the `-v` / `--verbose` flag:

- No `-v` → WARNING (default)
- `-v` → INFO
- `-vv` → DEBUG

Examples:
```bash
mqssbench -v run --config path/to/config.yaml
mqssbench -vv run --config path/to/config.yaml
```

Benchmark results are printed to standard output, while logs are sent to standard error.

### Configuration file format

A typical benchmark configuration file follows the structure shown below:

```yaml
# Benchmark configuration template

# Specify the benchmark to run. Two formats are supported:
# 1. String format: "origin/source/name"
# 2. Structured format:
#      origin: <ORIGIN>
#      source: <SOURCE>
#      name: <BENCHMARK_NAME>
benchmark: <ORIGIN>/<SOURCE>/<BENCHMARK_NAME>

# Benchmark specific parameters
benchmark_params:
  <PARAM_1>: <VALUE_1>
  <PARAM_2>: <VALUE_2>
  <PARAM_3>: <VALUE_3>

# Adapter configuration
adapter: <ADAPTER_NAME>
adapter_params:
  <ADAPTER_PARAM_1>: <VALUE_1>
  <ADAPTER_PARAM_2>: <VALUE_2>
  <ADAPTER_PARAM_3>: <VALUE_3>

# output directory
output_dir: <PATH>

# Controls what is generated (analysis, visualizations, reports)
report:
  analysis:
    enabled: <true_or_false>
      visualization: <true_or_false>
        enabled: <true_or_false>
        show: <true_or_false>

# Controls how results are persisted
storage:
  enabled: <true_or_false>
  type: <STORAGE_TYPE>  # "file" or "sqlite"
  file:
    format: <FILE_FORMAT> #"json"
  sqlite: # this will be implemeted in future
    db_path: <DATABASE_PATH>

# Profiling controls
profiling:
  enabled: <true_or_false>
  metrics:
    # List of profiling metrics. If omitted, all supported metrics are collected.
    # Available metrics depend on your selected adaptor.
    # For example, for MQSS adaptors, these are valid metrics:
    #   mqp_api, quantum_database, quantum_job_runner, isv_job_runner,
    #   quantum_daemon_job_runner, generator, scheduler, pass_runner,
    #   transpiler, submitter, pass_selection, knitter, job_execution
    - <METRIC_1>
    - <METRIC_2>
```

Example of a Single benchmark config:
```yaml
benchmark: core/native/randomized_benchmarking

benchmark_params:
  num_qubits: 2
  lengths: [2, 4, 8, 16]
  num_sequences: 2

adapter: mqss_qiskit
adapter_params:
  backend: QExa20
  backend_params:
    queued: true
  credentials:
    mqss_token: ""
  shots: 1000

output_dir: "./results"

report:
  analysis:
    enabled: true
    visualization:
      enabled: true
      show: false

storage:
  enabled: true
  type: "file" 
  file:
    format: "json"

profiling:
  enabled: true
  metrics:
    - transpiler
    - submitter
```


Example of a multi benchmark config:

```yaml
- benchmark: core/native/randomized_benchmarking
  benchmark_params:
    num_qubits: 2
    lengths: [2, 4, 8]
    num_sequences: 2
  adapter: mqss_qiskit
  adapter_params:
    backend: QExa20
    credentials:
      mqss_token: ""
    shots: 200
  output_dir: "./results"
  storage:
    enabled: true
    type: "file" 
    file:
      format: "json"

- benchmark: core/native/quantum_volume
  benchmark_params:
    num_qubits: 3
    depth: 3
    trials: 2
  adapter: mqss_qiskit
  adapter_params:
    backend: QExa20
    credentials:
      mqss_token: ""
    shots: 200
  output_dir: "./results"
  storage:
    enabled: true
    type: "file" 
    file:
      format: "json"
```

## 🧩 Python API Usage

MQSS Benchmarking Framework can also be used directly as a Python library when more control is needed.

```python
from mqssbench.runtime import BenchmarkManager

list_of_benchmarks = BenchmarkManager.get_available_benchmarks()

config = {
  "benchmark": "core/native/randomized_benchmarking",

  "benchmark_params": {
    "num_qubits": 2,
    "lengths": [2, 4, 8, 16],
    "num_sequences": 2
  },

  "adapter": "mqss_qiskit",
  "adapter_params": {
    "backend": "QExa20",
    "credentials": {
      "mqss_token": ""
    },
    "shots": 1000
  },

  "output_dir": "./results",

  "report": {
    "analysis": {
      "enabled": True,
      "visualization": {
        "enabled": True
      }
    }
  },

  "storage": {
    "enabled": True,
    "type": "file",
    "file": {
      "format": "json"
    }
  },
  
  "profiling": {
    "enabled": True,
    "metrics": ["transpiler", "submitter"]
  }
}

benchmark_manager = BenchmarkManager(config)
benchmark_manager.dispatch()
```

The `benchmark` field must always follow the strict `origin/source/name` format. For example:

- Core native benchmark: `core/native/quantum_volume` - uses `native` (native provider) as source
- Core provider benchmark: `core/mqt_bench/vqe_su2` - uses `mqt_bench` (a circuit provider) as source
- User defined benchmark: `user/my_source/my_benchmark_name` — uses `my_source` (arbitrary user source), can also leverage circuit providers

Both CLI and Python API share the same execution engine, registry system, and adapter logic.

### Latest supported adapters
- Qiskit Adapter (config value `mqss_qiskit`)
- Pennylane Adapter (config value `mqss_pennylane`)

A complete list of configuration options will be listed and constantly updated for the upcoming releases

## 🛠️ Upcoming Features
- Integration of the [Toolchain Project]([https://pages.github.com/](https://gitlab.lrz.de/qcbm/benchmark-comparison)) to the Framework for Simulator Benchmarks
- Improving the benchmark set for all types of benchmarks
## 📝 Contributing

Feel free to open issues or submit pull requests to improve this project!
