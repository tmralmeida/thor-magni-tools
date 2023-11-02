from thor_magni_tools.preprocessing.filtering import Filterer3DOF
from thor_magni_tools.utils.load import (
    load_csv_metadata_magni,
    preprocessing_header_magni,
)


class ThorMagniConverter:
    @staticmethod
    def get_dynamic_agents_prefix(scenario_id: str):
        if scenario_id == "Scenario_1":
            return ("Helmet",)
        elif scenario_id in ["Scenario_2", "Scenario_3"]:
            return ("Helmet", "DARKO_Robot", "LO1")
        return ("Helmet", "DARKO_Robot")

    @staticmethod
    def convert(data_path: str, filtering_markers: str):
        scenario_id = data_path.split("/")[-2]
        raw_df, header_dict = load_csv_metadata_magni(data_path)
        new_header_dict = preprocessing_header_magni(header_dict)
        traj_metadata = new_header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"]
        roles = {k: metadata["ROLE"] for k, metadata in traj_metadata.items()}

        if filtering_markers == "3D-best_marker":
            filtered_markers_traj = Filterer3DOF.filter_best_markers(raw_df, roles)
        elif filtering_markers == "3D-restoration":
            filtered_markers_traj = Filterer3DOF.restore_markers(raw_df, roles)
        dynamic_agents_name = ThorMagniConverter.get_dynamic_agents_prefix(
            scenario_id=scenario_id
        )
        dynamic_agents = filtered_markers_traj[
            filtered_markers_traj.ag_id.str.startswith(dynamic_agents_name)
        ]
        dynamic_agents_meters = dynamic_agents.copy()
        dynamic_agents_meters[["x", "y", "z"]] /= 1000
        return dynamic_agents_meters
