import pandas as pd


class ETHUCYConverter:
    @staticmethod
    def convert(data_path: str):
        # load the csv
        file_name = data_path.split("/")[-1]
        dataset_name = file_name.split(".txt")[0]
        df = pd.read_csv(
            data_path,
            delimiter="\t",
            names=["frame_id", "ag_id", "x", "y"],
            index_col=None,
        )
        # transform to frame_id, ag_id, x, y,
        df.loc[:, "time"] = (
            df.frame_id * (2 / 3) / 10.0
            if dataset_name == "biwi_eth"
            else df.frame_id * 0.4 / 10.0
        )
        df = df.set_index("time")
        return df

