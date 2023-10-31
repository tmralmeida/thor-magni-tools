from typing import List, Optional
import pandas as pd

from thor_magni_tools.analysis.dataset_converters import convert_dataset
from thor_magni_tools.preprocessing import TrajectoriesReprocessor
from thor_magni_tools.analysis.features import SpatioTemporalFeatures


class DatasetAnalyzer:
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

    @staticmethod
    def get_tracking_columns(df):
        return df.columns[df.columns.str.startswith(("x", "y", "z", "rot"))].tolist()

    @staticmethod
    def get_groups_continuous_tracking(dynamic_agent_data: pd.DataFrame):
        mask = dynamic_agent_data[["x", "y", "x"]].isna().any(axis=1)
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
            if metric_name == "tracking_duration":
                continous_tracking_metrics.append(group.index[-1] - group.index[0])
            elif metric_name == "perception_noise":
                continous_tracking_metrics.extend(group["acceleration"].values.tolist())
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
    def get_dataset_perception_noise(dynamic_agents: pd.DataFrame):
        perception_noise = {}
        for ag_id in dynamic_agents.ag_id.unique():
            dynamic_object_data = dynamic_agents[dynamic_agents["ag_id"] == ag_id]
            dynamic_object_data = SpatioTemporalFeatures.get_acceleration(
                dynamic_object_data
            )[0]
            perception_noises = DatasetAnalyzer.get_continuous_tracking_metrics(
                dynamic_object_data, "perception_noise"
            )
            perception_noise[ag_id] = perception_noises
        overall_perception_noise = []
        for perception_noises in perception_noise.values():
            overall_perception_noise.extend(perception_noises)
        return overall_perception_noise

    def run(self, dataset_name: str, data_path: str):
        dynamic_agents = convert_dataset(dataset_name, data_path)
        best_markers_traj = TrajectoriesReprocessor.reprocessing(
            dynamic_agents,
            max_nans_interpolate=self.interpolation,
            resampling_rule=None,
            average_window=None,
        )
        metrics = {}
        if self.tracking_duration:
            dataset_tracking_durations = DatasetAnalyzer.get_dataset_tracking_durations(
                best_markers_traj
            )
            metrics.update(tracking_duration=dataset_tracking_durations)
        if self.perception_noise:
            dataset_perception_noise = DatasetAnalyzer.get_dataset_perception_noise(
                best_markers_traj
            )
            metrics.update(perception_noise=dataset_perception_noise)
        if self.benchmark_metrics:
            if dataset_name in ["thor", "thor_magni"]:
                best_markers_traj = TrajectoriesReprocessor.reprocessing(
                    best_markers_traj,
                    max_nans_interpolate=self.interpolation,
                    resampling_rule="400ms",
                    average_window="800ms",
                )
            benchmark_metrics = DatasetAnalyzer.get_benchmark_metrics(
                best_markers_traj,
                metrics_names=["motion_speed", "path_efficiency"],
            )
            metrics.update(benchmark_metrics)
        return metrics
