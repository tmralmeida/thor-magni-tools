import json
import yaml


def dump_json_file(data_to_save: dict, save_path: str):
    """save json file"""
    file_o = open(save_path, "w")
    json.dump(data_to_save, file_o)


def load_json_file(load_path: str):
    with open(load_path, "rb") as f:
        data = json.load(f)
    return data


def load_yaml_file(load_path: str) -> dict:
    """load yaml file"""
    with open(load_path, "r") as f:
        yaml_dict = yaml.safe_load(f)
    return yaml_dict
