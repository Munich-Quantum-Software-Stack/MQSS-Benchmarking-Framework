
# Contributing to MQSS Benchmarking Framework

Thanks for your interest in contributing to **MQSS Benchmarking Framework**. This project is Python-based and uses `uv` for dependency management, `ruff` for linting, and `pytest` for tests.

This document explains how to propose and implement changes in a way that fits a production-quality workflow.

## Table of Contents

- [Getting Setup](#getting-setup)
- [Branching & Workflow](#branching--workflow)
- [Tips for Coding](#tips-for-coding)
- [How to Test](#how-to-test)
- [How to Lint](#how-to-lint)
- [Writing/Updating Tests](#writingupdating-tests)
- [Pull Request Checklist](#pull-request-checklist)
- [Notes for Benchmark Changes](#notes-for-benchmark-changes)

## Getting Setup

### Prerequisites

- Python **>= 3.12**
- `uv` installed

### Install dependencies

```bash
pip install uv
uv sync --all-extras --dev
````

## Branching & Workflow

### Base branch

* All contribution branches are created from: `develop`

### Branch naming (required)

For contribution work, use the following convention:

* `feat/<author_initials>/<short-name>` for new features or improvements
* `bug/<author_initials>/<short-name>` for bug fixes
* Use **lowercase** letters and digits.
* Use hyphens (`-`) in `<short-name>`.
* Keep `<author_initials>` to 1-3 lowercase characters (as shown above).

Examples (based on existing branches in this repo):

* `feat/bm/add-qaoa-benchmark`
* `feat/aa/architecture-overhaul`

### Pull requests

* Target branch for PRs: `develop`
* Keep PRs focused on **one main goal** (feature, fix, or refactor with a clear justification).

## Tips for Coding

* Follow the project's style and structure.
* `src/mqssbench/framework` contains the core abstraction classes, types, and registries. It should have minimal external dependencies and no dependency on other parts of the project.
  `src/mqssbench/library` contains built-ins and implementations based on the framework. This is a good place to start contributing (e.g., adding a new adapter, benchmark, or provider).
* Ensure type safety.
* Do not commit secrets (tokens, credentials).
* Avoid adding debug prints to production paths.

## How to Test

### Run tests locally

```bash
uv run pytest
```

Notes specific to this repo:

* Tests are discovered from the `test/` directory (`pytest.ini`).
* The `src/` folder is added to `PYTHONPATH` via pytest configuration.
* The test suite configures `matplotlib` to use a headless backend (`Agg`) to avoid CI hangs.

What `good` looks like:

* All tests pass locally before opening a PR.
* New behavior is backed by tests.

## How to Lint

### Ruff checks

This repo's CI runs `ruff check`, and pre-commit is configured to auto-fix.

Run:

```bash
uv run ruff check .
```

If you want Ruff to attempt automatic fixes:

```bash
uv run ruff check --fix .
```

## Writing/Updating Tests

* Unit and integration tests live under `test/`
* Tests mirror the source code path and naming
* If your change touches registry behavior, be mindful of concurrency and registry isolation

## Pull Request Checklist

Before opening a PR, please ensure:

* [ ] Branch name follows the mentioned structure
* [ ] PR targets `develop`
* [ ] You ran tests
* [ ] You ran lint
* [ ] No secrets or credentials were added
* [ ] Tests for the changed behavior exist and pass
* [ ] Documentation is updated

Maintainers may request additional changes during review. Respond to feedback respectfully and update the PR as needed.

Thanks