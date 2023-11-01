import pandas as pd

SDD_cols = [
    "ag_id",
    "xmin",
    "ymin",
    "xmax",
    "ymax",
    "frame_id",
    "lost",
    "occluded",
    "generated",
    "data_label",
]
STEP = 1


class SDDConverter:
    @staticmethod
    def convert(data_path: str):
        raw_df = pd.read_csv(
            data_path,
            header=0,
            delimiter=" ",
            names=SDD_cols,
        )
        raw_df = raw_df[raw_df["lost"] == 0]
        raw_df["x"] = (raw_df["xmax"] + raw_df["xmin"]) / 2
        raw_df["y"] = (raw_df["ymax"] + raw_df["ymin"]) / 2
        converted_df = raw_df.drop(
            columns=[
                "xmin",
                "xmax",
                "ymin",
                "ymax",
                "occluded",
                "generated",
                "lost",
            ]
        )
        converted_df.index = converted_df.index * STEP / 30
        return converted_df
