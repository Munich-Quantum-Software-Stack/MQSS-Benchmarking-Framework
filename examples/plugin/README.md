# MQSSBench Example Plugin

This example demonstrates how to create a third-party MQSSBench plugin.

## Install

From the repository root:

```bash
uv pip install -e .
uv pip install -e examples/plugin
```

## Verify

List available benchmarks:

```bash
uv run mqssbench list
```

In the benchmark list you should see:

```
example_plugin/native/example_benchmark
```

And in the adapter list you should see:

```
example_adapter
```