import re
from typing import List
from collections import defaultdict
import pandas as pd
import numpy as np

from thor_magni_tools.preprocessing.filtering import Filterer3DOF
from thor_magni_tools.utils.load import load_json_file


class ThorConverter:
    @staticmethod
    def get_roles(roles_info: dict, scenario_id: int, run_id: int):
        """transforms roles.json, being the experiment id and run the run id,
        into {helmet_id: role}

        Parameters
        ----------
        roles_info
            json file
        scenario_id
            scenario number
        run_id
            run number

        Returns
        -------
            dict s.t {helmet_id: role}
        """
        scenario_id, run_id = f"Scenario_{scenario_id}", f"run_{run_id}"
        helmets_roles = roles_info[scenario_id][run_id]
        roles = defaultdict(lambda: None)
        roles.update({f"Helmet_{hid}": role for hid, role in helmets_roles.items()})
        return roles

    @staticmethod
    def get_dynamic_agents_prefix(scenario_id: str):
        # if scenario_id in ["Scenario_1", "Scenario_3"]:
        #     return ("Helmet",)
        # return ("Helmet", "Citi_1")
        return ("Helmet", )

    @staticmethod
    def get_markers_col_names(input_df: pd.DataFrame) -> List[list]:
        pattern = re.compile(r"((.*?) - (\d+)) (X|Y|Z)$")
        column_groups = {}

        for col in input_df.columns:
            match = pattern.match(col)
            if match:
                prefix = match.group(1)
                suffix = match.group(4)

                if prefix not in column_groups:
                    column_groups[prefix] = []
                column_groups[prefix].append(f"{prefix} {suffix}")

        return list(column_groups.values())

    @staticmethod
    def replace_zeros_by_nans(input_df: pd.DataFrame) -> pd.DataFrame:
        markers_col_names = ThorConverter.get_markers_col_names(input_df)
        dfs = []
        for marker_cols_names in markers_col_names:
            target_df = input_df[marker_cols_names]
            target_df.values[target_df.values.sum(axis=1) == 0] = np.nan
            dfs.append(target_df)
        dfs = pd.concat(dfs, axis=1)
        dfs["Frame"] = input_df["Frame"]
        return dfs

    @staticmethod
    def convert(data_path: str, roles_path: str, filtering_markers: str):
        data_path_split = data_path.split("/")
        file_name, scenario_id = data_path_split[-1], data_path_split[-2]
        re_pattern = re.compile(r"Exp_(\d)_run_(\d)")
        out_regex = re.findall(re_pattern, file_name)
        scenario_id, run_id = out_regex[0]
        raw_df = pd.read_csv(
            data_path,
            sep="\t",
            header=10,
            index_col=1,
        ).dropna(axis=1, how="all")
        all_roles = load_json_file(roles_path)
        scenario_roles = ThorConverter.get_roles(all_roles, scenario_id, run_id)
        raw_df = ThorConverter.replace_zeros_by_nans(raw_df)
        if filtering_markers == "3D-best_marker":
            filtered_markers_traj = Filterer3DOF.filter_best_markers(
                raw_df, scenario_roles
            )
        elif filtering_markers == "3D-restoration":
            filtered_markers_traj = Filterer3DOF.restore_markers(raw_df, scenario_roles)
        dynamic_agents_name = ThorConverter.get_dynamic_agents_prefix(
            scenario_id=scenario_id
        )
        dynamic_agents = filtered_markers_traj[
            filtered_markers_traj.ag_id.str.startswith(dynamic_agents_name)
        ]
        dynamic_agents_meters = dynamic_agents.copy()
        dynamic_agents_meters[["x", "y", "z"]] /= 1000
        return dynamic_agents_meters
