import pandas as pd

from .common import log_msg


def validate_header(file_name: str, header_dict: dict) -> None:
    """Validate header in the csv file"""
    if header_dict["FILE_ID"] not in file_name:
        log_msg("File name does not match", "fail")
        return

    header_nbodies = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_BODIES"]
    header_nmarkers = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_MARKERS"]

    header_desc_bodies = list(
        header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"].keys()
    )

    header_desc_markers = [
        desc["NUMBER_OF_MARKERS"]
        for desc in header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"].values()
    ]

    if header_nbodies != len(header_desc_bodies):
        log_msg(
            f"[HEADER FAIL] N_BODIES = {header_nbodies} but got description for \
            {len(header_desc_bodies)} :( \n Verbose: {header_desc_bodies}",
            "fail",
        )
        return
    if header_nmarkers != sum(header_desc_markers):
        log_msg(
            f"[HEADER FAIL] N_MAKERS={header_nmarkers} but got description for \
            {sum(header_desc_markers)} :( \n Verbose: {header_desc_markers}",
            "fail",
        )
        return

    log_msg("Header validated! All keys match!", "pass")


def validate_header_with_dataframe(header_dict: dict, raw_df: pd.DataFrame):
    """Validate header in the csv file by comparing with dataframe"""
    header_nframes = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_FRAMES"]
    df_nframes = raw_df.Frame.iloc[-1]
    if header_nframes != df_nframes + 1:
        log_msg(
            f"[HEADER/DF MISMATCH] N_FRAMES from header={header_nframes} but got {df_nframes + 1} \
            on the df :(",
            "fail",
        )
        return
