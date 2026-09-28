import argparse
import yaml
import logging
import sys

from mqssbench.runtime.benchmark_manager import BenchmarkManager
from mqssbench.runtime.benchmark_runner import BenchmarkRunner
from mqssbench.framework.checkpoint import CheckpointedRunError, is_checkpoint_file
from mqssbench.cli.formatting import format_benchmark_result, format_registry_lists
from mqssbench.profiling import Profiler

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

    if is_checkpoint_file(config_path):
        runner = BenchmarkRunner.from_checkpoint(config_path)
        try:
            result = runner.run()
        except CheckpointedRunError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print(format_benchmark_result(result))
        print()
        return

    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"No config found at provided path: {config_path}")

    manager = BenchmarkManager(cfg)
    try:
        results = manager.dispatch()
    except CheckpointedRunError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

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

def cli_profile(results_path: str, execution_index: int, make_plot: bool, output: str, show: bool):
    profiler = Profiler.from_file(results_path)
    print(profiler.report(execution_index=execution_index))

    if not make_plot:
        return

    plot_path = profiler.plot(execution_index=execution_index, output_path=output, show=show)
    if plot_path is None:
        print("\nNo numeric profiling metrics available to plot.")
        return

    print(f"\nPlot saved to: {plot_path}")

    pie_path = profiler.plot_pie(execution_index=execution_index, show=show)
    if pie_path:
        print(f"Pie chart saved to: {pie_path}")

def main():
    EXAMPLES = """Examples:
    mqssbench list
    mqssbench run --config path/to/config.yaml
    mqssbench -v run --config path/to/config.yaml
    mqssbench run --config path/to/results/<run_tag>/checkpoint.json  # resume a failed run
    mqssbench run --config path/to/results/<run_tag>/                 # same, via the run folder
    mqssbench profile path/to/results.json
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
    run_parser.add_argument(
        "-c", "--config", required=True,
        help=(
            "Path to config YAML, or to a checkpoint.json (or its run directory) "
            "to resume a previously failed run"
        ),
    )

    subparsers.add_parser(
        "list",
        help="List available benchmarks, circuit providers, and adapters"
    )

    profile_parser = subparsers.add_parser(
        "profile",
        help="Profile a completed run's job cycle (queue/compile/quantum/classical breakdown)"
    )
    profile_parser.add_argument("results", help="Path to a saved results.json file")
    profile_parser.add_argument(
        "--execution", type=int, default=0,
        help="Index of the execution result to profile (default: 0)"
    )
    profile_parser.add_argument("--no-plot", action="store_true", help="Skip generating a plot")
    profile_parser.add_argument("--output", help="Path to save the plot (default: alongside the results file)")
    profile_parser.add_argument("--show", action="store_true", help="Open the generated plot")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command == "run":
        cli_run(args.config)
    elif args.command == "list":
        cli_list()
    elif args.command == "profile":
        cli_profile(args.results, args.execution, not args.no_plot, args.output, args.show)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
