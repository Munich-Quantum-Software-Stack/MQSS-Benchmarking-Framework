"""
Example MQSSBench plugin.
"""

PLUGIN_ORIGIN = "example_plugin"

def register() -> None:
    """Register all implementations provided by this plugin."""

    from . import example_adapter
    from . import example_benchmark

    example_adapter.register()
    example_benchmark.register()