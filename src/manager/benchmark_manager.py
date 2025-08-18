from handlers import HardwareBenchmarkHandler
from handlers import SoftwareBenchmarkHandler


class BenchmarkManager:

    def __init__(self, config: dict):
        self.config = config

    def get_benchmark_types(self):
        return ["HW", "SW", "Algorithm", "Simulator"]

    def get_available_benchmarks(self, bench_type: str = "HW"):
        if bench_type == "HW":
            return ["RB", "single-CRB", "multi-CRB", "DRB", "BRB", "MRB", "Dihedral-RB", "Simultaneous-RB", "IRB", "EPLG", 
                    "Quantum-supremacy", "QV", "CLOPS"]
        elif bench_type == "SW":
            return ["MQT-Bench"]
        elif bench_type == "Algorithm":
            raise NotImplementedError("Algorithmic benchmarks not implemented yet")
        elif bench_type == "Simulator":
            raise NotImplementedError("Simulator benchmarks not implemented yet")
        else:
            raise ValueError(f"Unsupported benchmark type: {bench_type}")

    def dispatch(self):

        benchmark_type = self.config["benchmark_type"]

        if benchmark_type == "HW":
            handler = HardwareBenchmarkHandler(self.config)
        elif benchmark_type == "SW":
            handler = SoftwareBenchmarkHandler(self.config)
        elif benchmark_type == "Algorithm":
            raise NotImplementedError("Algorithmic benchmark builder not implemented yet")
        elif benchmark_type == "Simulator":
            raise NotImplementedError("Simulator benchmark builder not implemented yet")
        else:
            raise ValueError(f"Unsupported benchmark type: {benchmark_type}")
        
        # build circuit
        handler.build_circuit()

        # run circuit
        # result = handler.run()

        # return result
        return 0
