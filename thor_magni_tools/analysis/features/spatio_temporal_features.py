import logging
from typing import List, Union
import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean

LOGGER = logging.getLogger(__name__)


class SpatioTemporalFeatures:
    @staticmethod
    def get_delta_columns(input_df: pd.DataFrame):
        out_df = input_df.copy()
        out_df = out_df.diff().add_suffix("_delta")
        out_df.loc[:, "Time_delta"] = out_df.index.to_series().diff()
        return out_df

    @staticmethod
    def get_acceleration(
        trajectories: Union[pd.DataFrame, List[pd.DataFrame]],
        speed_col_name: str = "speed",
        out_col_name: str = "acceleration",
    ) -> List[pd.DataFrame]:
        """it receives a list of pandas dataframes of trajectories and it computes the acceleration
        time must be passed as the index of the dataframe

        trajectories[index]:
            | frame_id | ag_id | x | y | z |

        Returns accelerations[index]:
            | frame_id | ag_id | x | y | z | acceleration |
        """
        trajectories = (
            trajectories if isinstance(trajectories, list) else [trajectories]
        )
        if speed_col_name not in trajectories[0].columns:
            trajectories_speeds = SpatioTemporalFeatures.get_speed(trajectories)
        acceleration_dfs = []
        target_cols_name = [
            out_col_name,
            f"x_{out_col_name}",
            f"y_{out_col_name}",
        ]
        for trajectory in trajectories_speeds:
            delta_df = SpatioTemporalFeatures.get_delta_columns(
                trajectory[[f"x_{speed_col_name}", f"y_{speed_col_name}"]]
            )
            delta_df["n_speed_deltas"] = np.sqrt(
                np.square(
                    delta_df[[f"x_{speed_col_name}_delta", f"y_{speed_col_name}_delta"]]
                ).sum(axis=1)
            )
            delta_df.loc[:, [f"x_{out_col_name}", f"y_{out_col_name}"]] = (
                delta_df[[f"x_{speed_col_name}_delta", f"y_{speed_col_name}_delta"]]
                .div(delta_df["Time_delta"].values, axis=0)
                .values
            )
            delta_df.loc[:, out_col_name] = (
                delta_df["n_speed_deltas"]
                .div(delta_df["Time_delta"].values, axis=0)
                .values
            )
            delta_df[target_cols_name] = delta_df[target_cols_name].fillna(value=0.0)
            trajectory = trajectory.join(
                delta_df[["n_speed_deltas"] + target_cols_name]
            )
            acceleration_dfs.append(trajectory)

        return acceleration_dfs

    @staticmethod
    def get_speed(
        trajectories: Union[pd.DataFrame, List[pd.DataFrame]],
        out_col_name: str = "speed",
    ) -> List[pd.DataFrame]:
        """it receives a list of pandas dataframes of trajectories and it computes the speed
        time must be passed as the index of the dataframe

        trajectories[index]:
            | frame_id | ag_id | x | y | z |

        Returns speeds[index]:
            | frame_id | ag_id | x | y | z | speed |
        """
        trajectories = (
            trajectories if isinstance(trajectories, list) else [trajectories]
        )
        speed_dfs = []
        target_cols_name = [
            "x_delta",
            "y_delta",
            out_col_name,
            f"x_{out_col_name}",
            f"y_{out_col_name}",
        ]
        for trajectory in trajectories:
            delta_df = SpatioTemporalFeatures.get_delta_columns(trajectory[["x", "y"]])
            delta_df["n_deltas"] = np.sqrt(
                np.square(delta_df[["x_delta", "y_delta"]]).sum(axis=1)
            )
            delta_df.loc[:, [f"x_{out_col_name}", f"y_{out_col_name}"]] = (
                delta_df[["x_delta", "y_delta"]]
                .div(delta_df["Time_delta"].values, axis=0)
                .values
            )
            delta_df.loc[:, out_col_name] = (
                delta_df["n_deltas"].div(delta_df["Time_delta"].values, axis=0).values
            )
            delta_df[target_cols_name] = delta_df[target_cols_name].fillna(value=0.0)
            trajectory = trajectory.join(delta_df[["n_deltas"] + target_cols_name])
            speed_dfs.append(trajectory)
        return speed_dfs

    @staticmethod
    def get_path_efficiency_index(
        trajectories: Union[pd.DataFrame, List[pd.DataFrame]],
        out_col_name: str = "path_efficiency",
    ) -> List[pd.DataFrame]:
        """it receives a list of pandas dataframes of trajectories and it computes the path
        efficiency. This feature is given by the distance between the origin and destination
        divided by the cumulative displacements between the origin and the destination.
        time must be passed as the index of the dataframe

        trajectories[index]:
            | frame_id | ag_id | x | y | z |

        Returns path_effficiency[index]:
            | frame_id | ag_id | x | y | z | path_effficiency |
        """
        trajectories = (
            trajectories if isinstance(trajectories, list) else [trajectories]
        )
        si_dfs = []
        for input_df in trajectories:
            trajectory = input_df.copy()
            if not set(["x_delta", "y_delta"]).issubset(trajectory.columns):
                trajectory = SpatioTemporalFeatures.get_delta_columns(
                    trajectory[["x", "y"]]
                )
            if "n_deltas" not in trajectory.columns:
                trajectory["n_deltas"] = np.sqrt(
                    np.square(trajectory[["x_delta", "y_delta"]]).sum(axis=1)
                )
            trajectory["cumsum_delta"] = trajectory["n_deltas"].cumsum()
            first_location = trajectory["x"].iloc[0], trajectory["y"].iloc[0]
            trajectory["dist_origin_loc_i"] = trajectory.apply(
                lambda row: euclidean(first_location, (row["x"], row["y"])), axis=1
            )
            trajectory[out_col_name] = (
                trajectory["dist_origin_loc_i"] / trajectory["cumsum_delta"]
            )
            trajectory[out_col_name] = trajectory[out_col_name].fillna(1.0)
            si_dfs.append(trajectory)
        LOGGER.info("%s created", out_col_name)
        return si_dfs

    @staticmethod
    def get_curvature(
        trajectories: Union[pd.DataFrame, List[pd.DataFrame]],
        out_col_name: str = "curvature",
    ) -> List[pd.DataFrame]:
        """it receives a list of pandas dataframes of trajectories and it computes the curvature of
        each trajectory.
        https://www.whitman.edu/mathematics/calculus_online/section13.03.html

        trajectories[index]:
            | frame_id | ag_id | x | y | z |

        Returns curvatures[index]:
            | frame_id | ag_id | x | y | z | curvature |
        """
        trajectories = (
            trajectories if isinstance(trajectories, list) else [trajectories]
        )
        curvature_dfs = []
        for input_df in trajectories:
            trajectory = input_df.copy()
            if not set(["x_delta", "y_delta"]).issubset(trajectory.columns):
                trajectory = SpatioTemporalFeatures.get_delta_columns(
                    trajectory[["x", "y"]]
                )

            dx = trajectory["x_delta"]
            dy = trajectory["y_delta"]
            if np.square(dx * dx + dy * dy).sum() < 1.0:
                curvature = 0.0
            else:
                d2x = np.gradient(dx)
                d2y = np.gradient(dy)
                curvature = np.abs(d2x * dy - dx * d2y) / np.power(
                    dx * dx + dy * dy, 1.5
                )
            trajectory[out_col_name] = curvature
            trajectory[out_col_name] = trajectory[out_col_name].fillna(0.0)
            curvature_dfs.append(trajectory)
        LOGGER.info("%s created", out_col_name)
        return curvature_dfs
