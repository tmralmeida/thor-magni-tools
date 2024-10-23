import os
import logging
from argparse import ArgumentParser
import pandas as pd

from thor_magni_tools.data_tests.logger import CustomFormatter
from thor_magni_tools.preprocessing import TrajectoriesReprocessor
from .utils import Loader, visualize_trajectories


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


parser = ArgumentParser(description="Trajectory-Gazes Visualization")


parser.add_argument(
    "--raw_file",
    type=str,
    required=True,
    help="Path to the raw csv file",
)


parser.add_argument(
    "--max_nans_interpolate",
    type=int,
    required=False,
    default=100,
    help="Number of nans in trajectory data to interpolate * 0.01s => max time to interpolate",
)

parser.add_argument(
    "--visualization_step",
    type=int,
    required=False,
    default=10,
    help="Number of frame leaps on the visualization",
)


args = parser.parse_args()
if not args.raw_file.endswith(".csv"):
    raise ValueError("You must pass csv file!")

preprocessing_type = "6D"  # forced preprocessing type
preprocessing_type_options = dict(resampling_rule=None, average_window=None)

preprocessor = TrajectoriesReprocessor(
        csv_path=args.raw_file,
        out_path=None,
        preprocessing_type="6D",
        max_nans_interpolate=100,
        **preprocessing_type_options
    )
raw_df = preprocessor.run()
trajectories_df = Loader.get_eyt_helmets(raw_df)
tobii_data = Loader.filter_tobii_data(trajectories_df)

thor_magni_raw_path = os.path.join(*args.raw_file.split("/")[:-3])

goals_path = os.path.join(thor_magni_raw_path, "goals_positions.csv")
goals_df = pd.read_csv(goals_path)

file_info = args.raw_file.split("/")[-1].split("THOR-Magni_")[1]
day = int(file_info[:4])
goals_loc = goals_df[goals_df["day"] == day][["x", "y"]].values

videos_path = os.path.join(thor_magni_raw_path, "MP4_Videos", "Files")
video_day = str(day) + "22_"
video_file_sc = video_day + file_info.split(video_day)[1][:-4]
visualize_trajectories(
    df=tobii_data,
    goal_points=goals_loc,
    video_paths=(videos_path, video_file_sc),
    step=args.visualization_step,
)