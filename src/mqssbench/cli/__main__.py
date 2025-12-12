import argparse
import yaml
import logging
import sys
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, 
                    level=logging.WARNING,
                    format="[%(levelname)s] %(name)s: %(message)s")

from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists


def cli_run(config_path: str):
    if(not config_path):
        raise ValueError("No config path provided")

    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError("No config found at provided path, %s" % config_path)

    manager = BenchmarkManager(cfg)
    results = manager.dispatch()

    for r in results:
        print(format_benchmark_result(r))
        print()  # blank line between runs    


def cli_list():
    formatted = format_registry_lists(
        benchmarks=BenchmarkManager.get_available_benchmarks(),
        providers=BenchmarkManager.get_available_providers(),
        adapters=BenchmarkManager.get_available_adapters(),
    )
    print(formatted)


def main():
    parser = argparse.ArgumentParser(prog="mqssbench")
    subparsers = parser.add_subparsers(dest="command")

    # mqssbench run
    run_parser = subparsers.add_parser("run", help="Run a benchmark from config file")
    run_parser.add_argument("-c", "--config", required=True, help="Path to config YAML")

    # mqssbench list
    subparsers.add_parser("list", help="List available benchmarks, circuit providers, and adapters")

    args = parser.parse_args()

    if args.command == "run":
        cli_run(args.config)
    elif args.command == "list":
        cli_list()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
