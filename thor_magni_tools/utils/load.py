from typing import Tuple
import ast

import csv
import pandas as pd


def load_csv_metadata(path: str, header_size: int = 16) -> Tuple[pd.DataFrame, dict]:
    """Path to the csv file

    Parameters
    ----------
    path
        Path to the csv file
    header_size
        Number of rows for the header

    Returns
    -------
        Panda DataFrame and Dictionary with the metadata
    """
    raw_df = pd.read_csv(
        path,
        sep=",",
        header=header_size,
        index_col=1,
    )
    header_dict = {}
    with open(path, "r", newline="\n") as csvfile:
        csvreader = csv.reader(csvfile)

        # Read the first 16 rows and store them in the list
        for i, row in enumerate(csvreader):
            if i > header_size - 1:
                break
            key = row[0]
            values = row[1:]
            values = filter(lambda x: x != "", values)
            values = [int(v) if v.isnumeric() else v for v in values]
            header_dict[key] = values
    return raw_df, header_dict


def preprocessing_header(header_dict: dict) -> dict:
    """return header in a more readable manner"""
    new_header_dict = {
        "FILE_ID": header_dict["FILE_ID"][0],
        "MODALITIES": dict(
            zip(
                header_dict["MODALITIES_WITH_UNITS"],
                header_dict["MODALITIES_UNITS_SPECIFIED"],
            )
        ),
        "SENSOR_DATA": {
            "TRAJECTORIES": {
                "N_FRAMES": header_dict["N_FRAMES_QTM"][0],
                "N_BODIES": header_dict["N_BODIES"][0],
                "N_MARKERS": header_dict["N_MARKERS"][0],
                "CONTIGUOUS_ROTATION_MATRIX": ast.literal_eval(
                    header_dict["CONTIGUOUS_ROTATION_MATRIX"][0]
                ),
                "METADATA": {},
            },
            "EYETRACKING": {},
        },
    }

    trajectories_metadata = {
        body_name: {
            "ROLE": body_role,
            "NUMBER_OF_MARKERS": n_markers,
            "MARKERS_NAMES": [],
        }
        for body_name, body_role, n_markers in zip(
            header_dict["BODY_NAMES"],
            header_dict["BODY_ROLES"],
            header_dict["BODY_NR_MARKERS"],
        )
    }

    for marker_name in header_dict["MARKER_NAMES"]:
        body_name, marker_id = marker_name.split(" - ")
        trajectories_metadata[body_name]["MARKERS_NAMES"].append(marker_id)

    new_header_dict["SENSOR_DATA"]["TRAJECTORIES"]["METADATA"] = trajectories_metadata

    eyetracking_metadata = {
        eyetracking_device: {
            "FREQUENCY_IR": freq_ir,
            "FREQUENCY_SCENE_CAMERA": freq_cam,
            "METADATA": {},
        }
        for eyetracking_device, freq_ir, freq_cam in zip(
            header_dict["EYETRACKING_DEVICES"],
            header_dict["EYETRACKING_FREQUENCY_IR"],
            header_dict["EYETRACKING_FREQUENCY_SCENE_CAMERA"],
        )
    }
    for i, eye_tracking_data in enumerate(header_dict["EYETRACKING_DATA_INCLUDED"]):
        eyetracking_device, data_type = eye_tracking_data.split("_")
        eyetracking_metadata[eyetracking_device]["METADATA"].update(
            {f"{data_type}_N_FRAMES": header_dict["EYETRACKING_DATA_N_FRAMES"][i]}
        )
    new_header_dict["SENSOR_DATA"]["EYETRACKING"] = eyetracking_metadata

    return new_header_dict
