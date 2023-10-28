from .thor_magni import ThorMagniConverter
from .thor import ThorConverter

ROLES_PATH = "/home/tmr/Documents/PhD/My_PhD/code/datasets/thor/roles.json"


def convert_dataset(dataset_name: str, data_path: str):
    if dataset_name == "thor_magni":
        dynamic_agents = ThorMagniConverter.convert(data_path)
    elif dataset_name == "thor":
        dynamic_agents = ThorConverter.convert(data_path, ROLES_PATH)
    return dynamic_agents
