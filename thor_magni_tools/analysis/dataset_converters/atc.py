import pandas as pd


class ATCConverter:
    @staticmethod
    def convert(data_path: str):
        return pd.read_csv(
            data_path,
            names=[
                "Time",
                "ag_id",
                "x",
                "y",
                "z",
                "velocity",
                "angle of motion",
                "facing angle",
            ],
            index_col=0,
        )
