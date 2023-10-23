import logging
import pandas as pd


from .common import log_msg
from .logger import CustomFormatter


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


def validate_header(file_name: str, header_dict: dict) -> None:
    """Validate header in the csv file"""
    validated = True
    if header_dict["FILE_ID"] not in file_name:
        validated = False
        log_msg(LOGGER, "File name does not match", "fail")

    header_nbodies = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_BODIES"]
    header_nmarkers = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_MARKERS"]

    header_desc_bodies = list(
        header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"].keys()
    )

    if header_nbodies != len(header_desc_bodies):
        validated = False
        log_msg(
            LOGGER,
            f"[HEADER FAIL] N_BODIES = {header_nbodies} but got description for \
            {len(header_desc_bodies)} :( \n Verbose: {header_desc_bodies}",
            "fail",
        )

    header_desc_markers = []
    for body_name, desc in header_dict["SENSOR_DATA"]["TRAJECTORIES"][
        "METADATA"
    ].items():
        if desc["NUMBER_OF_MARKERS"] != len(desc["MARKERS_NAMES"]):
            validated = False
            log_msg(
                LOGGER,
                f"[HEADER FAIL]{body_name} NUMBER OF MARKERS ({desc['NUMBER_OF_MARKERS']}) \
                does not match size of MARKERS_NAMES ({len(desc['MARKERS_NAMES'])})",
                "fail",
            )
        header_desc_markers.append(desc["NUMBER_OF_MARKERS"])
    if header_nmarkers != sum(header_desc_markers):
        validated = False
        log_msg(
            LOGGER,
            f"[HEADER FAIL] N_MAKERS={header_nmarkers} but got description for \
            {sum(header_desc_markers)} :( \n Verbose: {header_desc_markers}",
            "fail",
        )
    if validated:
        log_msg(LOGGER, "Header validated! All keys match!", "pass")


def validate_header_with_dataframe(header_dict: dict, raw_df: pd.DataFrame):
    """Validate header in the csv file by comparing with dataframe"""
    validated = True
    header_nframes = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_FRAMES"]
    df_nframes = raw_df.Frame.iloc[-1]
    if header_nframes != df_nframes + 1:
        log_msg(
            LOGGER,
            f"[HEADER/DF MISMATCH] N_FRAMES from header={header_nframes} but got {df_nframes + 1} \
            on the df :(",
            "fail",
        )

    # Validate n_bodies
    df_nbodies = set(col.split(" ")[0] for col in raw_df.columns if col != "Frame")
    header_nbodies = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_BODIES"]
    if header_nbodies != len(df_nbodies):
        validated = False
        log_msg(
            LOGGER,
            f"[HEADER/DF MISMATCH] N_BODIES = {header_nbodies} in header but got \
            {len(df_nbodies)} from the dataframe :( \n Verbose: {df_nbodies}",
            "fail",
        )

    # Validate n_markers
    df_possible_bodies_names = set(
        col.split(" ")[0] for col in raw_df.columns if col != "Frame"
    )
    filtered_columns = [
        col
        for col in raw_df.columns
        if any(col.startswith(prefix) for prefix in df_possible_bodies_names)
    ]
    df_columns_markers = [
        col[:-2]
        for col in filtered_columns
        if any(char.isdigit() for char in col) and " - " in col and col.endswith("X")
    ]
    df_bodies_markers = {}
    for item in df_columns_markers:
        key, value = item.split(" - ")
        key = key.strip()  # Remove extra spaces around the key
        value = int(value)  # Convert the last digits to integers
        if key not in df_bodies_markers.keys():
            df_bodies_markers.setdefault(key, [])
        df_bodies_markers[key].append(value)

    header_metadata = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"]
    for df_body_name, df_markers in df_bodies_markers.items():
        if header_metadata[df_body_name]["NUMBER_OF_MARKERS"] != len(
            df_markers
        ):
            validated = False
            log_msg(
                LOGGER,
                f"[HEADER/DF MISMATCH] for {df_body_name}: \
                Given by header: {header_metadata[df_body_name]['NUMBER_OF_MARKERS']} \
                Given by dataframe: {len(df_markers)}",
                "fail",
            )

    if validated:
        log_msg(LOGGER, "Header validated with the dataframe!", "pass")
