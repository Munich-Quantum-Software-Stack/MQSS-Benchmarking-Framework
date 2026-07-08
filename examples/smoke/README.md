# Smoke checks

Minimal manual checks to verify device adapters work end-to-end. These are not production benchmarks.

## Run

From the repo root:

```bash
# all smoke tests
uv run python examples/smoke/run.py

# one test
uv run python examples/smoke/run.py mqss_pennylane_bell
uv run python examples/smoke/run.py mqss_qiskit_bell
```

Set `MQSS_TOKEN` or fill in `credentials.mqss_token` inside each smoke file before running against a real backend.

## Add a new smoke test

Add a new `*.py` file in this folder with:

1. a benchmark registered under `user/smoke/...`
2. a `SMOKE_CONFIG` dict at the bottom

`run.py` picks it up automatically, no changes needed there.
