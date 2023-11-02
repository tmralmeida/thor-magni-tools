import os
from typing import List
import pandas as pd
import numpy as np

from ..io import create_dir, dump_json_file


AVAILABLE_SCENARIOS = [
    "Scenario",
    "eth",
    "univ",
    "zara1",
    "zara2",
    "hotel",
    "gates",
    "little",
    "nexus",
    "coupa",
    "bookstore",
    "deathCircle",
    "quad",
    "hyang",
    "atc-tracking-part1"
]


def log_metrics(logger, metrics):
    for metric_name, metric_value in metrics.items():
        metric_value = np.array(metric_value)
        if metric_name == "perception_noise":
            metric_value = np.absolute(metric_value)
        logger.debug(
            "%s: %1.2f+-%1.2f",
            metric_name,
            metric_value.mean(),
            metric_value.std(),
        )
        if metric_name == "path_efficiency":
            logger.debug("Number of tracklets in the benchmark: %d", len(metric_value))


class ResultSaver:
    def __init__(self, save_path: str) -> None:
        create_dir(save_path)
        self.save_path = save_path

    def fill_results(
        self, metric_name: str, metric_values: List[float], results_df: dict
    ) -> None:
        metric_values = np.array(metric_values)
        if metric_name == "perception_noise":
            metric_values = np.absolute(metric_values)
        metric_mean, metric_std = metric_values.mean(), metric_values.std()
        results_df[metric_name] = f"{metric_mean:1.2f}+-{metric_std:1.2f}"
        if metric_name == "path_efficiency":
            results_df["num_tracklets"] = len(metric_values)

    def save_scenarios_results(self, scenarios_metrics: dict) -> None:
        results_df = {scenario_id: {} for scenario_id in scenarios_metrics.keys()}
        for scenario, scenario_metrics in scenarios_metrics.items():
            for metric_name, metric_values in scenario_metrics.items():
                self.fill_results(metric_name, metric_values, results_df[scenario])

        results_df = pd.DataFrame.from_dict(results_df)
        results_df.to_csv(os.path.join(self.save_path, "scenes_results.csv"))

    def save_global_results(self, global_metrics: dict) -> None:
        results_df = {metric_name: "" for metric_name in global_metrics.keys()}
        for metric_name, metric in global_metrics.items():
            self.fill_results(metric_name, metric, results_df)
        dump_json_file(results_df, os.path.join(self.save_path, "global_results.json"))
