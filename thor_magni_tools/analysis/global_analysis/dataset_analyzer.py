from typing import List, Optional
import pandas as pd

from thor_magni_tools.utils.load import load_csv_metadata, preprocessing_header
from thor_magni_tools.preprocessing.filtering import Filterer3DOF
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
    def get_dynamic_agents_prefix(scenario_id: str):
        if scenario_id == "Scenario_1":
            return ("Helmet",)
        if scenario_id in ["Scenario_2", "Scenario_3"]:
            return ("Helmet", "DARKO_Robot", "LO1")
        if scenario_id in ["Scenario_4", "Scenario_5"]:
            return ("Helmet", "DARKO_Robot")

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
            if num_tracklets > 0:
                tracklets = [
                    group.iloc[i * tracklet_len: (i + 1) * tracklet_len]
                    for i in range(num_tracklets)
                ]
                speed_tracklets = SpatioTemporalFeatures.get_speed(tracklets)
                path_eff_tracklets = SpatioTemporalFeatures.get_path_efficiency_index(
                    speed_tracklets
                )
                for speed_track, path_eff_track in zip(
                    speed_tracklets, path_eff_tracklets
                ):
                    agent_metrics["motion_speed"].extend(
                        speed_track["speed"].values.tolist()
                    )
                    agent_metrics["path_efficiency"].append(
                        path_eff_track["path_efficiency"].iloc[-1]
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
        input_df: pd.DataFrame, scenario_id: str, metrics_names: List[str] | str
    ):
        metrics_names = (
            [metrics_names] if isinstance(metrics_names, str) else metrics_names
        )
        dynamic_agents_name = DatasetAnalyzer.get_dynamic_agents_prefix(scenario_id)
        dynamic_agents = input_df[input_df.ag_id.str.startswith(dynamic_agents_name)]
        dynamic_agents_meters = dynamic_agents.copy()
        dynamic_agents_meters[["x", "y", "z"]] /= 1000
        benchmark_metrics = {}
        for ag_id in dynamic_agents_meters.ag_id.unique():
            dynamic_object_data = dynamic_agents_meters[
                dynamic_agents_meters["ag_id"] == ag_id
            ]
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
    def get_dataset_tracking_durations(input_df: pd.DataFrame, scenario_id: str):
        dynamic_agents_name = DatasetAnalyzer.get_dynamic_agents_prefix(scenario_id)
        dynamic_agents = input_df[input_df.ag_id.str.startswith(dynamic_agents_name)]
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
    def get_dataset_perception_noise(input_df: pd.DataFrame, scenario_id: str):
        dynamic_agents_name = DatasetAnalyzer.get_dynamic_agents_prefix(scenario_id)
        dynamic_agents = input_df[input_df.ag_id.str.startswith(dynamic_agents_name)]
        dynamic_agents_meters = dynamic_agents.copy()
        dynamic_agents_meters[["x", "y", "z"]] /= 1000
        perception_noise = {}
        for ag_id in dynamic_agents.ag_id.unique():
            dynamic_object_data = dynamic_agents_meters[
                dynamic_agents_meters["ag_id"] == ag_id
            ]
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

    def load_data(self, data_path: str):
        raw_df, header_dict = load_csv_metadata(data_path)
        new_header_dict = preprocessing_header(header_dict)
        traj_metadata = new_header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"]
        roles = {k: metadata["ROLE"] for k, metadata in traj_metadata.items()}
        return raw_df, roles

    def run(self, data_path: str):
        scenario_id = data_path.split("/")[-2]
        raw_df, roles = self.load_data(data_path)
        best_markers_traj = Filterer3DOF.filter_best_markers(raw_df, roles)
        if self.interpolation:
            best_markers_traj = TrajectoriesReprocessor.reprocessing(
                best_markers_traj,
                max_nans_interpolate=self.interpolation,
                resampling_rule=None,
                average_window=None,
            )
        metrics = {}
        if self.tracking_duration:
            dataset_tracking_durations = DatasetAnalyzer.get_dataset_tracking_durations(
                best_markers_traj, scenario_id
            )
            metrics.update(tracking_duration=dataset_tracking_durations)
        if self.perception_noise:
            dataset_perception_noise = DatasetAnalyzer.get_dataset_perception_noise(
                best_markers_traj, scenario_id
            )
            metrics.update(perception_noise=dataset_perception_noise)
        if self.benchmark_metrics:
            best_markers_traj = TrajectoriesReprocessor.reprocessing(
                best_markers_traj,
                max_nans_interpolate=self.interpolation,
                resampling_rule="400ms",
                average_window="800ms",
            )
            benchmark_metrics = DatasetAnalyzer.get_benchmark_metrics(
                best_markers_traj,
                scenario_id,
                metrics_names=["motion_speed", "path_efficiency"],
            )
            metrics.update(benchmark_metrics)
        return metrics
