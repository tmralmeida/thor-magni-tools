from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt


def visualize_scenario(trajectories_df: pd.DataFrame, roles: Optional[dict] = None):
    plt.figure(figsize=(16, 8))
    for agent_id in trajectories_df.ag_id.unique():
        traj_agent = trajectories_df[trajectories_df["ag_id"] == agent_id]
        label = agent_id + f" ({roles[agent_id]})" if roles else ""
        plt.plot(traj_agent["x"], traj_agent["y"], label)
    plt.legend()
