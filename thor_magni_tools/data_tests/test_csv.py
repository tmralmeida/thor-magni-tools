import logging
import pandas as pd

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
        LOGGER.error("File name does not match")

    header_nbodies = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_BODIES"]
    header_nmarkers = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_MARKERS"]

    header_desc_bodies = list(
        header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"].keys()
    )

    if header_nbodies != len(header_desc_bodies):
        validated = False
        LOGGER.error(
            "[HEADER FAIL] N_BODIES = %d but got description for \
            %d :( \n Verbose: %s",
            header_nbodies,
            len(header_desc_bodies),
            header_desc_bodies,
        )

    header_desc_markers = []
    for body_name, desc in header_dict["SENSOR_DATA"]["TRAJECTORIES"][
        "METADATA"
    ].items():
        if desc["NUMBER_OF_MARKERS"] != len(desc["MARKERS_NAMES"]):
            validated = False
            LOGGER.error(
                "[HEADER FAIL]%s NUMBER OF MARKERS (%d) \
                does not match size of MARKERS_NAMES (%d)",
                body_name,
                desc["NUMBER_OF_MARKERS"],
                len(desc["MARKERS_NAMES"]),
            )
        header_desc_markers.append(desc["NUMBER_OF_MARKERS"])
    if header_nmarkers != sum(header_desc_markers):
        validated = False
        LOGGER.error(
            "[HEADER FAIL] N_MAKERS=%d but got description for \
            %d :( \n Verbose: %s",
            header_nmarkers,
            sum(header_desc_markers),
            header_desc_markers,
        )
    if validated:
        LOGGER.info("Header validated! All keys match!")


def validate_header_with_dataframe(header_dict: dict, raw_df: pd.DataFrame):
    """Validate header in the csv file by comparing with dataframe"""
    validated = True
    header_nframes = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_FRAMES"]
    df_nframes = raw_df.Frame.iloc[-1]
    if header_nframes != df_nframes + 1:
        LOGGER.error(
            "[HEADER/DF MISMATCH] N_FRAMES from header=%d but got %d \
            on the df :(",
            header_nframes,
            df_nframes + 1,
        )

    # Validate n_bodies
    df_nbodies = set(col.split(" ")[0] for col in raw_df.columns if col != "Frame")
    header_nbodies = header_dict["SENSOR_DATA"]["TRAJECTORIES"]["N_BODIES"]
    if header_nbodies != len(df_nbodies):
        validated = False
        LOGGER.error(
            "[HEADER/DF MISMATCH] N_BODIES = %d in header but got \
            %d from the dataframe :( \n Verbose: %s",
            header_nbodies,
            len(df_nbodies),
            df_nbodies,
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
        if header_metadata[df_body_name]["NUMBER_OF_MARKERS"] != len(df_markers):
            validated = False
            LOGGER.error(
                "[HEADER/DF MISMATCH] for %s: \
                Given by header: %d \
                Given by dataframe: %d",
                df_body_name,
                header_metadata[df_body_name]["NUMBER_OF_MARKERS"],
                len(df_markers),
            )

    if validated:
        LOGGER.info("Header validated with the dataframe!")
