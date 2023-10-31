import os
import logging
from typing import Optional

from ...data_tests.logger import CustomFormatter
from .dataset_analyzer import DatasetAnalyzer
from ..utils import log_metrics, AVAILABLE_SCENARIOS


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


class GlobalAnalyzer:
    def __init__(
        self,
        interpolation: Optional[int],
        tracking_duration: bool,
        perception_noise: bool,
        benchmark_metrics: bool,
    ) -> None:
        self.interpolation = interpolation
        self.tracking_duration = tracking_duration
        self.perception_noise = perception_noise
        self.benchmark_metrics = benchmark_metrics

    def organize_metrics(self, metrics: dict) -> dict:
        new_metrics = {
            metric_name: [] for metric_name in metrics[list(metrics.keys())[0]]
        }
        for _, metrics_details in metrics.items():
            for metric_name, metric_values in metrics_details.items():
                new_metrics[metric_name].extend(metric_values)
        return new_metrics

    def run(self, dataset_name, data_path: str):
        metrics = {}
        for root, _, files in os.walk(data_path, topdown=True):
            if len(files) > 0:
                scenario_id = [
                    split
                    for split in root.split("/")
                    for ds in AVAILABLE_SCENARIOS
                    if ds in split
                ][0]
                metrics[scenario_id] = {}
                for i, file_id in enumerate(files):
                    LOGGER.debug("Running metrics on %s", file_id)
                    file_path = os.path.join(root, file_id)
                    dataset_analyzer = DatasetAnalyzer(
                        interpolation=self.interpolation,
                        tracking_duration=self.tracking_duration,
                        perception_noise=self.perception_noise,
                        benchmark_metrics=self.benchmark_metrics,
                    )
                    metrics_dataset = dataset_analyzer.run(dataset_name, file_path)
                    if i == 0:
                        metrics[scenario_id] = {
                            metric_name: [] for metric_name in metrics_dataset.keys()
                        }
                    for metric_name, metric_value in metrics_dataset.items():
                        metrics[scenario_id][metric_name].extend(metric_value)
                scenario_metrics = metrics[scenario_id]
                log_metrics(LOGGER, scenario_metrics)
        global_metrics = self.organize_metrics(metrics)
        return global_metrics
