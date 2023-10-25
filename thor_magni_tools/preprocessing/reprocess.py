import os
import logging
import pandas as pd

from .filtering import Filterer3DOF, Filterer6DOF
from ..data_tests.logger import CustomFormatter
from ..utils.load import load_csv_metadata, preprocessing_header
from ..io import create_dir


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


class TrajectoriesReprocessor:
    def __init__(
        self, csv_path: str, out_path: str, preprocessing_type: str, **kwargs
    ) -> None:
        self.csv_path = csv_path
        self.out_dir = out_path
        self.pp_type = preprocessing_type
        self.args = kwargs

    @staticmethod
    def interpolate_with_rule(
        input_df: pd.DataFrame, column_name: str, max_consecutive_nans: int
    ) -> pd.DataFrame:
        """interpolate given a max number of consecutive nans"""
        mask = input_df[column_name].isna()
        groups = mask.ne(mask.shift()).cumsum()

        interpolated_column = input_df[column_name].interpolate(method="linear")

        interpolated_column = interpolated_column.where(
            groups.groupby(groups).transform("size") <= max_consecutive_nans,
            input_df[column_name],
        )

        input_df[column_name] = interpolated_column
        return input_df

    @staticmethod
    def interpolate(input_df: pd.DataFrame, max_nans_interpolate: int) -> pd.DataFrame:
        """interpolate dataframe"""
        faulty_columns = input_df.columns[
            input_df.columns.str.startswith(("x", "y", "z", "rot"))
        ]
        agents_in_scenario = input_df["ag_id"].unique()
        agents_preprocessed = []
        for agent_id in agents_in_scenario:
            target_agent = input_df[input_df["ag_id"] == agent_id]
            target_agent_rule_int = target_agent.copy()
            for col_name in faulty_columns:
                target_agent_rule_int = TrajectoriesReprocessor.interpolate_with_rule(
                    target_agent_rule_int, col_name, max_nans_interpolate
                )
            agents_preprocessed.append(target_agent_rule_int)
        interpolated_df = pd.concat(agents_preprocessed, axis=0).sort_index()
        return interpolated_df

    def get_target_columns_attributes(self, traj_metadata) -> dict:
        target_agents = tuple(
            body_name
            for body_name, meta_data in traj_metadata.items()
            if len(meta_data["MARKERS_NAMES"]) > 0
        )

        columns_suff = ("X", "Y", "Z")
        if self.pp_type == "6D":
            columns_axis = tuple(f"Centroid_{axis}" for axis in columns_suff)
            columns_rot = tuple(f"R{rot}" for rot in range(9))
            columns_suff = columns_axis + columns_rot
        return dict(
            target_agents=target_agents,
            target_columns_suffix=columns_suff,
        )

    def run(self):
        split_path = self.csv_path.split("/")
        scenario_id, file_name = split_path[-2], split_path[-1]
        raw_df, header_dict = load_csv_metadata(self.csv_path)
        pp_header_dict = preprocessing_header(header_dict)
        traj_metadata = pp_header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"]

        target_columns_atts = self.get_target_columns_attributes(traj_metadata)
        target_agents = target_columns_atts["target_agents"]
        target_columns_suffix = target_columns_atts["target_columns_suffix"]

        df = raw_df.dropna(axis=1, how="all")
        filtered_columns = [
            col
            for col in df.columns
            if (col.startswith(target_agents) and col.endswith(target_columns_suffix))
        ]

        target_data = df[["Frame"] + filtered_columns]
        roles = {k: metadata["ROLE"] for k, metadata in traj_metadata.items()}
        if self.pp_type == "6D":
            filtered_df = Filterer6DOF.reorganize_df(target_data, target_agents, roles)
            col_nans = "x_centroid"
        elif self.pp_type == "3D":
            filtered_df = Filterer3DOF.filter_best_markers(target_data, roles)
            col_nans = "x"

        pre_nans_counter = {
            body_name: filtered_df[filtered_df["ag_id"] == body_name][col_nans]
            .isna()
            .sum()
            for body_name in target_agents
        }
        LOGGER.debug("Pre running the preprocessing # NaNs: %s", pre_nans_counter)

        pp_df = TrajectoriesReprocessor.interpolate(
            filtered_df, self.args["max_nans_interpolate"]
        )
        postprocessed_nans_counter = {
            body_name: pp_df[pp_df["ag_id"] == body_name][col_nans].isna().sum()
            for body_name in target_agents
        }
        LOGGER.debug(
            "After running the preprocessing # NaNs: %s", postprocessed_nans_counter
        )
        create_dir(os.path.join(self.out_dir, scenario_id))
        pp_df.to_csv(os.path.join(self.out_dir, scenario_id, file_name))
        LOGGER.info("%s preprocessed!", file_name)
