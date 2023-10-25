import pandas as pd
import matplotlib.pyplot as plt


def visualize_scenario(trajectories_df: pd.DataFrame, roles):
    plt.figure(figsize=(16, 8))
    for agent_id in trajectories_df.ag_id.unique():
        traj_agent = trajectories_df[trajectories_df["ag_id"] == agent_id]
        role = roles[agent_id]
        plt.plot(traj_agent["x"], traj_agent["y"], label=agent_id + f" ({role})")
    plt.legend();  # Noqa E703
