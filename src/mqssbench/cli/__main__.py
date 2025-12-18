import argparse
import yaml
import logging
import sys

from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists

logger = logging.getLogger(__name__)

def setup_logging(verbosity: int):
    """
    Map numeric verbosity to logging levels:
      0 -> WARNING
      1 -> INFO
      >=2 -> DEBUG
    Logs are sent to stderr so stdout remains for program output.
    """
    v = max(0, int(verbosity))
    if v >= 2:
        level = logging.DEBUG
    elif v == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="[%(levelname)s] %(name)s: %(message)s"
    )

def cli_run(config_path: str):
    if not config_path:
        raise ValueError("No config path provided")

    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"No config found at provided path: {config_path}")

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

def non_negative_int(value: str) -> int:
    """
    argparse type for non negative integers. Raises ArgumentTypeError on invalid input.
    """
    try:
        iv = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}")
    if iv < 0:
        raise argparse.ArgumentTypeError("verbosity must be a non-negative integer")
    return iv

def main():
    EXAMPLES = """Examples:
    mqssbench list
    mqssbench run --verbose=1 --config=path/to/config.yaml
    mqssbench run -v 2 -c path/to/config.yaml
    """
    parser = argparse.ArgumentParser(
        prog="mqssbench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES)

    parser.add_argument(
        "-v",
        "--verbose",
        type=non_negative_int,
        default=0,
        metavar="LEVEL",
        help="Set verbosity level (integer). 0=WARNING, 1=INFO, 2=DEBUG. Default is 0."
    )

    subparsers = parser.add_subparsers(dest="command")

    # mqssbench run
    run_parser = subparsers.add_parser("run", help="Run a benchmark from config file")
    run_parser.add_argument("-c", "--config", required=True, help="Path to config YAML")

    # mqssbench list
    subparsers.add_parser("list", help="List available benchmarks, circuit providers, and adapters")

    args = parser.parse_args()

    # resolve and configure logging
    verbosity = args.verbose
    setup_logging(verbosity)

    if args.command == "run":
        cli_run(args.config)
    elif args.command == "list":
        cli_list()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
