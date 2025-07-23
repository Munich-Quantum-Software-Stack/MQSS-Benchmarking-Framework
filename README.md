<a href="https://gitmoji.dev">
  <img
    src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square"
    alt="Gitmoji"
  />
</a>

# MQSS Benchmarking Suite

## Overview

MQSS Benchmarking Suite is an automated and reproducable tool for uniting Quantum Computing Benchmarks. It has 4 main pillars: 

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

   This will install all required dependencies as specified in the project configuration.

## 🚀 Usage

This project is intended to be an off-to-shelf python library, and the goal is to allow users to use it as follows:

```python
from mqss.benchmarking_suite import BenchmarkManager

list_of_benchmarks = BenchmarkManager.get_available_benchmarks("HW")

config = {
    "benchmark_type": "HW",
    "benchmark_name": "RB",
    "interface": "pennylane",
    "backend": "QLM",
    "integrator": "MQSS",
    "credentials": {
        "mqss_token": "<TOKEN>"
    },
    "wires": 2,
    "params": {}
}

benchmark_manager = BenchmarkManager(config)
benchmark_manager.dispatch()
```
A complete list of configuration options will be listed and constantly updated for the upcoming releases

## 🛠️ Upcoming Features
- Integration of the [Toolchain Project]([https://pages.github.com/](https://gitlab.lrz.de/qcbm/benchmark-comparison)) to the Suite for Simulator Benchmarks
- Connecting the Qiskit Adapter as an alternative interface
- Improving the benchmark set for all types of benchmarks
## Contributing

Feel free to open issues or submit pull requests to improve this project!
