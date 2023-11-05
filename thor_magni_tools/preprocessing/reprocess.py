import os
import logging
from typing import Optional
import pandas as pd

from .filtering import Filterer3DOF, Filterer6DOF
from ..utils.load import load_csv_metadata_magni, preprocessing_header_magni
from ..data_tests.logger import CustomFormatter
from ..io import create_dir


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


class TrajectoriesReprocessor:
    def __init__(
        self,
        csv_path: str,
        out_path: str,
        preprocessing_type: str,
        max_nans_interpolate: int,
        **kwargs,
    ) -> None:
        self.csv_path = csv_path
        self.out_dir = out_path
        self.pp_type = preprocessing_type
        self.max_nans_interpolate = max_nans_interpolate
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
    def reprocessing(
        input_df: pd.DataFrame, max_nans_interpolate: Optional[int], **kwargs
    ) -> pd.DataFrame:
        """Repreocessing tha dataframe: interpolation.
        Optionally: resampling + moving average filter

        Parameters
        ----------
        input_df
            raw input dataframe
        max_nans_interpolate
            max number of untracked locations to be interpolated

        Returns
        -------
            preprocessed dataframe
        """
        faulty_columns = input_df.columns[
            input_df.columns.str.startswith(("x", "y", "z", "rot"))
        ].tolist()
        agents_in_scenario = input_df["ag_id"].unique()
        data_lbl_col = True if "data_label" in input_df.columns else False
        agents_preprocessed = []
        for agent_id in agents_in_scenario:
            target_agent = input_df[input_df["ag_id"] == agent_id]
            target_agent_rule_int = target_agent.copy()
            if max_nans_interpolate:
                for col_name in faulty_columns:
                    target_agent_rule_int = TrajectoriesReprocessor.interpolate_with_rule(
                        target_agent_rule_int, col_name, max_nans_interpolate
                    )
                LOGGER.debug("interpolation applied!")
            if data_lbl_col:
                data_label = target_agent_rule_int["data_label"].iloc[0]
            marker_id = (
                target_agent_rule_int["marker_id"].iloc[0]
                if "marker_id" in target_agent_rule_int.columns
                else None
            )
            if kwargs["resampling_rule"] or kwargs["average_window"]:
                target_agent_rule_int = target_agent_rule_int.copy()[
                    ["frame_id"] + faulty_columns
                ]
                target_agent_rule_int.index = pd.TimedeltaIndex(
                    target_agent_rule_int.index, unit="s"
                )
            if kwargs["resampling_rule"]:
                target_agent_rule_int = target_agent_rule_int.resample(
                    rule=kwargs["resampling_rule"]
                ).first()
                LOGGER.debug("resampling applied!")
            if kwargs["average_window"]:
                target_agent_rule_int[faulty_columns] = (
                    target_agent_rule_int[faulty_columns]
                    .rolling(kwargs["average_window"])
                    .mean()
                )
                LOGGER.debug("average window applied!")
            if target_agent_rule_int.index.dtype != float:
                target_agent_rule_int.index = (
                    target_agent_rule_int.index.total_seconds()
                )
                target_agent_rule_int["ag_id"] = agent_id
                if data_lbl_col:
                    target_agent_rule_int["data_label"] = data_label
                if marker_id:
                    target_agent_rule_int["marker_id"] = marker_id

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
        raw_df, header_dict = load_csv_metadata_magni(self.csv_path)
        pp_header_dict = preprocessing_header_magni(header_dict)
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
        elif self.pp_type == "3D-best_marker":
            filtered_df = Filterer3DOF.filter_best_markers(target_data, roles)
            col_nans = "x"
        elif self.pp_type == "3D-restoration":
            filtered_df = Filterer3DOF.restore_markers(target_data, roles)
            col_nans = "x"

        pre_nans_counter = {
            body_name: filtered_df[filtered_df["ag_id"] == body_name][col_nans]
            .isna()
            .sum()
            for body_name in target_agents
        }
        LOGGER.debug("Pre running the preprocessing # NaNs: %s", pre_nans_counter)

        pp_df = TrajectoriesReprocessor.reprocessing(
            input_df=filtered_df,
            max_nans_interpolate=self.max_nans_interpolate,
            resampling_rule=self.args["resampling_rule"],
            average_window=self.args["average_window"],
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
