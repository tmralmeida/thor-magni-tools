from typing import Tuple
import pandas as pd


class Filterer3DOF:
    @staticmethod
    def get_best_markers(input_df: pd.DataFrame) -> pd.DataFrame:
        """Get markers with lowest amount of NaN values"""
        x_coordinate = input_df[input_df.columns[input_df.columns.str.endswith("X")]]
        x_cols = x_coordinate.columns

        instances = set(x_coordinate.columns.str.split(" - ").str[0])
        instances = list(filter(lambda x: len(x.split(" ")) == 1, instances))
        nan_counter_by_marker = {}
        for instance_id in instances:
            nan_counter_by_marker[instance_id] = {}
            markers = (
                x_coordinate[x_cols[x_cols.str.startswith(f"{instance_id} -")]]
                .columns.str.split(regex=r" (/d) ")
                .str[2]
            )
            for marker_id in markers:
                n_nans = x_coordinate[f"{instance_id} - {marker_id} X"].isna().sum()
                nan_counter_by_marker[instance_id][marker_id] = n_nans
        return nan_counter_by_marker

    @staticmethod
    def reorganize_df(
        input_df: pd.DataFrame, ag_id: str, best_marker_id: int, role: str
    ) -> pd.DataFrame:
        """Reorganize DataFrame structure
        Output:
            |Time|frame_id|ag_id|x|y|z|data_label|marker_id
        Parameters
        ----------
        input_df
            raw df
        ag_id
            agent id
        best_marker_id
            number of best marker based on argmin(NaNs)
        role
            ongoing activity wrt the trajectory

        Returns
        -------
            reorganized pandas DataFrame
        """
        return pd.DataFrame(
            {
                "frame_id": input_df.Frame,
                "ag_id": ag_id,
                "x": input_df[f"{ag_id} - {best_marker_id} X"],
                "y": input_df[f"{ag_id} - {best_marker_id} Y"],
                "z": input_df[f"{ag_id} - {best_marker_id} Z"],
                "data_label": role,
                "marker_id": best_marker_id,
            }
        )

    @staticmethod
    def filter_best_markers(input_df: pd.DataFrame, roles: dict) -> pd.DataFrame:
        """Filtering 3D trajectories based on the best marker.
        Output:
        |Time|frame_id|ag_id|x|y|z|data_label|marker_id

        marker_id column -> best marker based on the argmin(NaNs)

        Parameters
        ----------
        input_df
            raw_df
        nan_counter_by_marker
            counter of number of NaNs per marker
        roles
            ongoing activity wrt the trajectory
        Returns
        -------
            Filtered DataFrame
        """
        nan_counter_by_marker = Filterer3DOF.get_best_markers(input_df)
        elements_filtered_by_best_marker = []
        for instance_id, nans_counter in nan_counter_by_marker.items():
            best_marker_id = min(
                nans_counter,
                key=nans_counter.get,
            )
            out_df = Filterer3DOF.reorganize_df(
                input_df, instance_id, best_marker_id, roles[instance_id]
            )
            elements_filtered_by_best_marker.append(out_df)
        out_df = pd.concat(elements_filtered_by_best_marker, axis=0)
        out_df = out_df.sort_index()
        return out_df


class Filterer6DOF:
    @staticmethod
    def reorganize_df(
        input_df: pd.DataFrame, target_agents: Tuple[str], roles: dict
    ) -> pd.DataFrame:
        """Output:
            |Time|frame_id|ag_id|x|y|z|data_label|marker_id

        Parameters
        ----------
        input_df
            raw df
        target_agents
            agents ids
        roles
            ongoing activities wrt the trajectory

        Returns
        -------
            reorganized pandas DataFrame
        """
        agents_reorganized = []
        for agent_id in target_agents:
            df_dict = {
                "frame_id": input_df.Frame,
                "ag_id": agent_id,
                "x_centroid": input_df[f"{agent_id} Centroid_X"],
                "y_centroid": input_df[f"{agent_id} Centroid_Y"],
                "z_centroid": input_df[f"{agent_id} Centroid_Z"],
                "data_label": roles[agent_id],
            }
            df_dict.update({f"rot_{i}": input_df[f"{agent_id} R{i}"] for i in range(9)})
            out_df = pd.DataFrame(df_dict)
            agents_reorganized.append(out_df)
        out_df = pd.concat(agents_reorganized, axis=0)
        out_df = out_df.sort_index()
        return out_df
