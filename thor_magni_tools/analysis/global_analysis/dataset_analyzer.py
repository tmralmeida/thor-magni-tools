import logging
from itertools import combinations
from typing import List, Optional
import pandas as pd
import numpy as np

from thor_magni_tools.data_tests.logger import CustomFormatter
from thor_magni_tools.analysis.dataset_converters import convert_dataset
from thor_magni_tools.preprocessing import TrajectoriesReprocessor
from thor_magni_tools.analysis.features import (
    SpatioTemporalFeatures,
    pairwise_distances,
)


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


class DatasetAnalyzer:
    def __init__(
        self,
        dataset_name: str,
        interpolation: Optional[int],
        average_window: Optional[str],
        tracking_duration: bool,
        min_social_distance: bool,
        benchmark_metrics: bool,
    ) -> None:
        self.dataset_name = dataset_name
        self.interpolation = interpolation
        self.average_window = average_window
        self.tracking_duration = tracking_duration
        self.benchmark_metrics = benchmark_metrics
        self.min_social_distance = min_social_distance

    @staticmethod
    def get_tracking_columns(df):
        return df.columns[df.columns.str.startswith(("x", "y", "z", "rot"))].tolist()

    @staticmethod
    def get_groups_continuous_tracking(dynamic_agent_data: pd.DataFrame):
        mask = dynamic_agent_data[["x", "y", "z"]].isna().any(axis=1)
        groups = (mask != mask.shift()).cumsum()
        groups_of_continuous_tracking = dynamic_agent_data.groupby(groups)
        return groups_of_continuous_tracking

    @staticmethod
    def get_continuous_bechmark_metrics(
        dynamic_agent_data: pd.DataFrame,
        metrics_names: List[str] | str,
        tracklet_len: int = 20,
    ) -> dict:
        groups_of_continuous_tracking = DatasetAnalyzer.get_groups_continuous_tracking(
            dynamic_agent_data
        )
        tracking_cols = DatasetAnalyzer.get_tracking_columns(dynamic_agent_data)
        agent_metrics = {metric_name: [] for metric_name in metrics_names}
        for _, group in groups_of_continuous_tracking:
            if group[tracking_cols].isna().any(axis=0).all():
                continue
            num_tracklets = len(group) // tracklet_len
            if num_tracklets == 0:
                continue
            tracklets = [
                group.iloc[i * tracklet_len: (i + 1) * tracklet_len]
                for i in range(num_tracklets)
            ]
            speed_tracklets = SpatioTemporalFeatures.get_speed(tracklets)
            path_eff_tracklets = SpatioTemporalFeatures.get_path_efficiency_index(
                speed_tracklets
            )
            for speed_track, path_eff_track in zip(speed_tracklets, path_eff_tracklets):
                agent_metrics["motion_speed"].extend(
                    speed_track.iloc[1:]["speed"].values.tolist()
                )
                agent_metrics["path_efficiency"].append(
                    path_eff_track.iloc[1:]["path_efficiency"].iloc[-1]
                )
        return agent_metrics

    @staticmethod
    def get_continuous_tracking_metrics(
        dynamic_agent_data: pd.DataFrame, metric_name: str
    ) -> List[float]:
        groups_of_continuous_tracking = DatasetAnalyzer.get_groups_continuous_tracking(
            dynamic_agent_data
        )
        tracking_cols = DatasetAnalyzer.get_tracking_columns(dynamic_agent_data)
        continous_tracking_metrics = []
        for _, group in groups_of_continuous_tracking:
            if group[tracking_cols].isna().any(axis=0).all():
                continue
            continous_tracking_metrics.append(group.index[-1] - group.index[0])
        return continous_tracking_metrics

    @staticmethod
    def get_benchmark_metrics(
        dynamic_agents: pd.DataFrame, metrics_names: List[str] | str
    ):
        metrics_names = (
            [metrics_names] if isinstance(metrics_names, str) else metrics_names
        )
        benchmark_metrics = {}
        for ag_id in dynamic_agents.ag_id.unique():
            dynamic_object_data = dynamic_agents[dynamic_agents["ag_id"] == ag_id]
            agent_metrics = DatasetAnalyzer.get_continuous_bechmark_metrics(
                dynamic_object_data, metrics_names
            )
            benchmark_metrics[ag_id] = agent_metrics
        overall_benchmark_metrics = {metric_name: [] for metric_name in metrics_names}
        for agent_metrics in benchmark_metrics.values():
            for metric_name in metrics_names:
                overall_benchmark_metrics[metric_name].extend(
                    agent_metrics[metric_name]
                )
        return overall_benchmark_metrics

    @staticmethod
    def get_dataset_tracking_durations(dynamic_agents: pd.DataFrame):
        tracking_duration = {}
        for ag_id in dynamic_agents.ag_id.unique():
            dynamic_object_data = dynamic_agents[dynamic_agents["ag_id"] == ag_id]
            continuous_tracking_durations = (
                DatasetAnalyzer.get_continuous_tracking_metrics(
                    dynamic_object_data, "tracking_duration"
                )
            )
            tracking_duration[ag_id] = continuous_tracking_durations
        overall_tracking_durations = []
        for tracking_durations in tracking_duration.values():
            overall_tracking_durations.extend(tracking_durations)
        return overall_tracking_durations

    @staticmethod
    def get_dataset_min_social_distances(dynamic_agents: pd.DataFrame):
        if dynamic_agents.ag_id.dtype == str:
            humans = dynamic_agents[~dynamic_agents.ag_id.str.startswith(("DARKO", "LO"))]
        else:
            humans = dynamic_agents
        grouped_frames = humans.groupby("frame_id")
        distances, min_distances = {}, []
        for frame, group in grouped_frames:
            distances[frame], distances_ts = [], []
            points = group[["x", "y"]].values
            agents_ids = group["ag_id"].values
            pairwise_dist_matrix = pairwise_distances(points)
            np.fill_diagonal(pairwise_dist_matrix, np.inf)
            agents_combinations = list(combinations(range(len(agents_ids)), 2))
            for i, j in agents_combinations:
                if not np.isnan(pairwise_dist_matrix[i, j]):
                    distances[frame].append(
                        {
                            "ag_id1": agents_ids[i],
                            "ag_id2": agents_ids[j],
                            "distance": pairwise_dist_matrix[i, j],
                        }
                    )

                    distances_ts.append(pairwise_dist_matrix[i, j])
            if len(distances_ts) > 0:
                min_distances.append(min(distances_ts))
        return min_distances

    def run(self, data_path: str, **kwargs):
        dynamic_agents = convert_dataset(self.dataset_name, data_path, **kwargs)
        if self.interpolation or self.average_window:
            dynamic_agents = TrajectoriesReprocessor.reprocessing(
                dynamic_agents,
                max_nans_interpolate=self.interpolation,
                resampling_rule=None,
                average_window=self.average_window,
            )
            LOGGER.debug("Dataset reprocessed")
        metrics = {}
        if self.tracking_duration:
            dataset_tracking_durations = DatasetAnalyzer.get_dataset_tracking_durations(
                dynamic_agents
            )
            metrics.update(tracking_duration=dataset_tracking_durations)
            LOGGER.info("Tracking duration computed")
        if self.min_social_distance:
            dataset_min_social_distances = (
                DatasetAnalyzer.get_dataset_min_social_distances(dynamic_agents)
            )
            metrics.update(min_social_distances=dataset_min_social_distances)
            LOGGER.info("Min. social distances computed")
        if self.benchmark_metrics:
            if self.dataset_name in ["thor", "thor_magni"]:
                dynamic_agents = TrajectoriesReprocessor.reprocessing(
                    dynamic_agents,
                    max_nans_interpolate=150,
                    resampling_rule="400ms",
                    average_window="800ms",
                )
            benchmark_metrics = DatasetAnalyzer.get_benchmark_metrics(
                dynamic_agents,
                metrics_names=["motion_speed", "path_efficiency"],
            )
            metrics.update(benchmark_metrics)
            LOGGER.info("Benchmark metrics computed")
        return metrics
