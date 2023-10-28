import logging
from argparse import ArgumentParser


from .data_tests.logger import CustomFormatter
from .analysis.global_analysis.dataset_analyzer import DatasetAnalyzer
from .analysis.global_analysis.global_analyzer import GlobalAnalyzer
from .analysis.utils import log_metrics


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)

parser = ArgumentParser(description="Trajectory Data Analyzer")

parser.add_argument(
    "--dataset_name",
    type=str,
    required=True,
    choices=["thor_magni", "thor", "eth_ucy", "sdd"],
    help="Name of the dataset",
)

parser.add_argument(
    "--data_path",
    type=str,
    required=True,
    help="Path to data",
)

parser.add_argument(
    "--interpolation",
    type=int,
    required=False,
    default=None,
    help="Interpolation max leap",
)

args = parser.parse_args()
data_path = args.data_path
dataset_name = args.dataset_name

run_batch = True
if args.data_path.endswith((".csv", ".tsv", ".txt")):
    run_batch = False


if run_batch:
    global_analyzer = GlobalAnalyzer(
        interpolation=args.interpolation,
        tracking_duration=True,
        perception_noise=True,
        benchmark_metrics=True,
    )
    global_metrics = global_analyzer.run(dataset_name, data_path)
    LOGGER.debug("===Logging Global Metrics===")
    log_metrics(LOGGER, global_metrics)

else:
    dataset_analyzer = DatasetAnalyzer(
        interpolation=args.interpolation,
        tracking_duration=True,
        perception_noise=True,
        benchmark_metrics=True,
    )
    metrics = dataset_analyzer.run(dataset_name, data_path)
    LOGGER.debug("Metrics for %s:", data_path.split("/")[-1])
    log_metrics(LOGGER, metrics)
