from .benchmark import Benchmark


_REGISTRY: dict[str, type[Benchmark]] = {}


def register_benchmark(benchmark_cls: type[Benchmark]):
    _REGISTRY[benchmark_cls.name()] = benchmark_cls


def get_benchmark_class(name: str) -> type[Benchmark]:
    if name not in _REGISTRY:
        raise ValueError(f"Unsupported benchmark: {name}")
    return _REGISTRY[name]

def list_registerd_benchmarks() -> list[str]:
    return list(_REGISTRY.keys())
