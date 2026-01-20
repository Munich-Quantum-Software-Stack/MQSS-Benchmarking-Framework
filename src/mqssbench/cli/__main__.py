import argparse
import yaml
import logging
import sys

from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists

logger = logging.getLogger(__name__)

def setup_logging(verbosity: int):
    """
    Map repeatable verbosity to logging levels:
      0 -> WARNING
      1 -> INFO
      >=2 -> DEBUG
    Logs are sent to stderr so stdout remains for program output.
    """
    v = verbosity or 0

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
        print()

def cli_list():
    formatted = format_registry_lists(
        benchmarks=BenchmarkManager.get_available_benchmarks(),
        providers=BenchmarkManager.get_available_providers(),
        adapters=BenchmarkManager.get_available_adapters(),
    )
    print(formatted)

def main():
    EXAMPLES = """Examples:
    mqssbench list
    mqssbench run --config path/to/config.yaml
    mqssbench -v run --config path/to/config.yaml
    """

    parser = argparse.ArgumentParser(
        prog="mqssbench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)."
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a benchmark from config file")
    run_parser.add_argument("-c", "--config", required=True, help="Path to config YAML")

    subparsers.add_parser(
        "list",
        help="List available benchmarks, circuit providers, and adapters"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command == "run":
        cli_run(args.config)
    elif args.command == "list":
        cli_list()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
