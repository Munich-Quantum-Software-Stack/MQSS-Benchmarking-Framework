<!----------------------------------------------------------------------------
Copyright 2026 Munich Quantum Software Stack Project

Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
"License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://github.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/blob/develop/LICENSE

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
-------------------------------------------------------------------------- -->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/develop/docs/assets/mqss_logo_dark.svg" width="20%">
    <img src="https://raw.githubusercontent.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/develop/docs/assets/mqss_logo.svg" width="20%">
  </picture>
</p>

# MQSS Benchmarking Framework

<p align="center">
  <a href="https://munich-quantum-software-stack.github.io/MQSS-Benchmarking-Framework/">
  <img style="min-width: 200px !important; width: 30%;" src="https://img.shields.io/badge/documentation-blue?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0NDggNTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNi4wIGJ5IEBmb250YXdlc29tZSAtIGh0dHBzOi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNlbnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2ZmZmZmZiIgZD0iTTk2IDBDNDMgMCAwIDQzIDAgOTZMMCA0MTZjMCA1MyA0MyA5NiA5NiA5NmwyODggMCAzMiAwYzE3LjcgMCAzMi0xNC4zIDMyLTMycy0xNC4zLTMyLTMyLTMybDAtNjRjMTcuNyAwIDMyLTE0LjMgMzItMzJsMC0zMjBjMC0xNy43LTE0LjMtMzItMzItMzJMMzg0IDAgOTYgMHptMCAzODRsMjU2IDAgMCA2NEw5NiA0NDhjLTE3LjcgMC0zMi0xNC4zLTMyLTMyczE0LjMtMzIgMzItMzJ6bTMyLTI0MGMwLTguOCA3LjItMTYgMTYtMTZsMTkyIDBjOC44IDAgMTYgNy4yIDE2IDE2cy03LjIgMTYtMTYgMTZsLTE5MiAwYy04LjggMC0xNi03LjItMTYtMTZ6bTE2IDQ4bDE5MiAwYzguOCAwIDE2IDcuMiAxNiAxNnMtNy4yIDE2LTE2IDE2bC0xOTIgMGMtOC44IDAtMTYtNy4yLTE2LTE2czcuMi0xNiAxNi0xNnoiLz48L3N2Zz4=" alt="Documentation" />
  </a>
</p>

The **MQSS Benchmarking Framework** is a general-purpose, platform-agnostic, extensible quantum benchmarking framework designed to serve as the central orchestration and integration layer for the quantum benchmarking ecosystem. It provides a unified infrastructure that brings together benchmarks, hardware backends, simulators, circuit providers, benchmark suites, and benchmarking frameworks under a single, consistent environment, covering the full spectrum of benchmarking experiments.

MQSS Benchmarking Framework is built around a principled architecture based on a registry-driven component system, abstract interfaces for extensible components, and a plugin discovery mechanism. This design allows benchmarks, hardware backends, and tools to be integrated as first-class components within the framework. The framework is under active development, with an initial core library already in place and more components planned as the architecture evolves.


## FAQ

### What is MQSS?

_MQSS_ stands for _Munich Quantum Software Stack_ and is a project of the _Munich Quantum Valley_
initiative. It is jointly developed by the _Munich Quantum Valley (MQV) gGmbH_, _Leibniz
Supercomputing Centre (LRZ)_, the _Chair for Design Automation (CDA)_, and the _Chair of Computer
Architecture and Parallel Systems (CAPS)_ at TUM. It provides a comprehensive compilation and
runtime infrastructure for on-premise and remote quantum devices, support for modern compilation and
optimization techniques, and enables both current and future high-level abstractions for quantum
programming. This stack is designed to be capable of deployment in a variety of scenarios via
flexible configuration options. This includes stand-alone scenarios for individual systems, cloud
access to a variety of devices, as well as tight integration into HPC environments supporting
quantum acceleration. Concrete instances of the _MQSS_ are deployed at the LRZ and MQV gGmbH,
providing unified access to all of their quantum devices through multiple compatible access paths.
This includes a web portal, command line access via web credentials, as well as the option for
hybrid access with tight integration with HPC systems.It facilitates the connection between
end-users and quantum computing platforms by its integration within HPC infrastructures, such as
those found at the LRZ.

### Where can I find the getting started guide?

A step-by-step guide is available in the documentation site at [Getting Started](docs/user_guide/getting_started.md).

### How can I contribute to the project?

Contribution guidelines are available in [CONTRIBUTING.md](CONTRIBUTING.md).


### Under which license is MQSS Benchmarking Framework released?

**MQSS Benchmarking Framework** is released under the Apache License v2.0. See
[LICENSE](https://github.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/blob/develop/LICENSE) for
more information. Any contribution to the project is assumed to be under the same license.

## Contact

The development of this project is led by the QCT department at the LRZ and the QSI department at
MQV gGmbH. You can also always reach us at
[mqss@munich-quantum-valley.de](mailto:mqss@munich-quantum-valley.de).

Please try to use the publicly accessible GitHub channels
([issues](https://github.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/issues),
[discussions](https://github.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/discussions),
[pull requests](https://github.com/Munich-Quantum-Software-Stack/MQSS-Benchmarking-Framework/pulls)) to allow for a
transparent and open discussion as much as possible.
