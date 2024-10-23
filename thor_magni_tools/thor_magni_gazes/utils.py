import os
from typing import List, Tuple
import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
import cv2


def extract_target_columns(input_df: pd.DataFrame, target_cols_init=Tuple[str]) -> pd.DataFrame:
    target_cols = input_df.columns[input_df.columns.str.startswith(target_cols_init)]
    input_df = input_df[target_cols].dropna(subset=target_cols, how="any")
    return input_df


class Loader:
    def __init__(self, scenario_dir: str) -> None:
        self.scenario_dir = scenario_dir

    @staticmethod
    def load_raw_csv(path: str) -> pd.DataFrame:
        return pd.read_csv(path, index_col="Time")

    @staticmethod
    def get_eyt_helmets(
        input_df: pd.DataFrame, eyt_names: List[str] = ["TB2", "TB3", "PPL"]
    ) -> pd.DataFrame:
        agents_group = input_df.groupby("ag_id")
        eyt_agents = []
        for _, group in agents_group:
            for eyt in eyt_names:
                if group[f"{eyt}_G2D_X"].isna().sum() != len(group):
                    eyt_agents += [group]
        out_df = pd.concat(eyt_agents).sort_index()
        return out_df

    @staticmethod
    def filter_tobii_data(eyt_helmets_df: pd.DataFrame) -> pd.DataFrame:
        agents_group = eyt_helmets_df.groupby("ag_id")
        initial_col_names = ("frame_id", "ag_id", "agent_type", "x", "y", "z", "rot")
        target_dfs = []
        for _, group in agents_group:
            if group["TB2_G2D_X"].isna().sum() != len(group):
                eyt = "TB2"
            elif group["TB3_G2D_X"].isna().sum() != len(group):
                eyt = "TB3"
            else:
                continue
            target_df = extract_target_columns(group, initial_col_names + (eyt,))
            target_df = target_df.rename(
                {
                    column: "eyt" + column.split(eyt)[1]
                    for column in target_df.columns
                    if column.startswith(eyt)
                },
                axis=1,
            )
            target_df["eyt_device"] = eyt
            target_dfs.append(target_df)
        prepared_df = pd.concat(target_dfs).sort_index()
        prepared_df = prepared_df.rename(
            {
                f"eyt_{gt}_{axis}": f"{axis.lower()}_eyt_{gt}"
                for gt in ["G2D", "G3D"]
                for axis in ["X", "Y", "Z"]
            },
            axis=1,
        )
        return prepared_df


def visualize_trajectories(
    df: pd.DataFrame, goal_points: np.array, video_paths: Tuple[str, str], step: int = 50
):
    """
    Visualizes the rolling 3D trajectories with gaze vectors for all agents at each time step,
    updated by key press.
    """
    agent_ids = df["ag_id"].unique()
    colors = plt.cm.get_cmap("tab10", len(agent_ids))

    tobii_devices = df["eyt_device"].unique()
    fig = plt.figure()
    ax = fig.add_subplot(211, projection="3d")

    caps_obj, imgs_obj, axs_obj = {}, {}, {}
    for i, tobii_device in enumerate(tobii_devices):
        tb_ag = df[df["eyt_device"] == tobii_device]["ag_id"].iloc[0].replace("Helmet_", "H")
        tb_video_file_name = (
            tobii_device.replace("TB", "Tobii") + "_" + video_paths[1] + "_" + tb_ag + ".mp4"
        )
        caps_obj[tobii_device] = cv2.VideoCapture(os.path.join(video_paths[0], tb_video_file_name))
        axs_obj[tobii_device] = fig.add_subplot(int(f"22{i + 3}"))
        axs_obj[tobii_device].axis("off")

        ret, frame = caps_obj[tobii_device].read()
        if not ret:
            print("Failed to open video")
            continue
        imgs_obj[tobii_device] = axs_obj[tobii_device].imshow(
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        )

    frame_idx = 0
    time_steps = df.index.unique()
    num_steps = len(time_steps)

    def plot_frame():
        nonlocal frame_idx
        time_step = time_steps[frame_idx]
        for tobii_device in tobii_devices:
            target_df = df[df["eyt_device"] == tobii_device]
            et_frame = target_df[target_df.index == time_step]
            et_frame_idx = et_frame["eyt_scene_id"]
            if len(et_frame_idx) == 0:
                continue
            else:
                et_frame_idx = int(et_frame_idx.iloc[0])
            caps_obj[tobii_device].set(cv2.CAP_PROP_POS_FRAMES, et_frame_idx)
            ret, frame = caps_obj[tobii_device].read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame = cv2.circle(
                rgb_frame,
                (int(et_frame["x_eyt_G2D"].values[0]), int(et_frame["y_eyt_G2D"].values[0])),
                radius=20,
                color=(255, 0, 0),
                thickness=-1,
            )
            imgs_obj[tobii_device].set_data(rgb_frame)
            axs_obj[tobii_device].set_title(f"{tobii_device}-{et_frame_idx}", fontsize=30)

        """Plots a single frame for the current time step with all agents."""
        ax.cla()

        ax.text(
            df["x_centroid"].min() - 500,
            df["y_centroid"].min() - 500,
            df["z_centroid"].max(),
            f"Time: {time_step}",
            color="black",
            fontsize=20,
        )
        frame_data = df[df.index == time_step]
        for goal in goal_points:
            ax.scatter(
                goal[0],
                goal[1],
                500,
                marker="*",
                s=500,
                color="red",
                edgecolor="black",
            )

        for i, agent_id in enumerate(agent_ids):
            agent_df = frame_data[frame_data["ag_id"] == agent_id]

            if agent_df.empty:
                continue  # Skip if no data for the agent in this timestep

            row = agent_df.iloc[0]
            head_pos = np.array([row["x_centroid"], row["y_centroid"], row["z_centroid"]])
            gaze_vector = np.array([row["x_eyt_G3D"], row["y_eyt_G3D"], row["z_eyt_G3D"]])
            rotations = row[[f"rot_{i}" for i in range(9)]].values
            rotations_reshaped = rotations.reshape(3, 3).T
            x_rep = np.array([[10**3, 0, 0]])
            y_rep = np.array([[0, 10**3, 0]])
            z_rep = np.array([[0, 0, 10**3]])
            x_rotated = np.matmul(x_rep, rotations_reshaped).squeeze()
            y_rotated = np.matmul(y_rep, rotations_reshaped).squeeze()
            z_rotated = np.matmul(z_rep, rotations_reshaped).squeeze()

            color = colors(i)
            ax.scatter(*head_pos, color=color, s=250, label=f"Agent {agent_id}")

            gaze_trans = gaze_vector - head_pos
            ax.quiver(*head_pos, *gaze_trans, length=1, color="black")
            ax.quiver(*head_pos, *x_rotated, length=1, color="red")
            ax.quiver(*head_pos, *y_rotated, length=1, color="green")
            ax.quiver(*head_pos, *z_rotated, length=1, color="blue")

            ax.text(
                *head_pos,
                f"{row['agent_type']}\n{row['eyt_device']}\n{row['eyt_movement']}",
                color=color,
                fontsize=10,
            )

        # Set limits and labels
        ax.set_xlim([goal_points[:, 0].min() - 250, goal_points[:, 0].max() + 250])
        ax.set_ylim([goal_points[:, 1].min() - 250, goal_points[:, 1].max() + 250])
        ax.set_zlim([0, 2500])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

        ax.legend()
        fig.canvas.draw_idle()

    def on_key(event):
        nonlocal frame_idx
        if event.key == "right" and frame_idx < num_steps - step:
            frame_idx += step
        elif event.key == "left" and frame_idx >= step:
            frame_idx -= step
        plot_frame()

    plot_frame()
    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.subplots_adjust(
        left=0.0,
        right=1,
        top=1,
        bottom=0,
        wspace=0,
        hspace=0,
    )

    plt.show()
    for tobii_device in tobii_devices:
        caps_obj[tobii_device].release()
