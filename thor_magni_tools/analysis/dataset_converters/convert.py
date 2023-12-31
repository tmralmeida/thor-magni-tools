from .thor_magni import ThorMagniConverter
from .thor import ThorConverter
from .eth_ucy import ETHUCYConverter
from .sdd import SDDConverter
from .atc import ATCConverter

ROLES_PATH = "/home/tmr/Documents/PhD/My_PhD/code/datasets/thor/roles.json"


def convert_dataset(dataset_name: str, data_path: str, **kwargs):
    if dataset_name == "thor_magni":
        dynamic_agents = ThorMagniConverter.convert(data_path, kwargs["filtering_markers"])
    elif dataset_name == "thor":
        dynamic_agents = ThorConverter.convert(data_path, ROLES_PATH, kwargs["filtering_markers"])
    elif dataset_name == "eth_ucy":
        dynamic_agents = ETHUCYConverter.convert(data_path)
    elif dataset_name == "sdd":
        dynamic_agents = SDDConverter.convert(data_path)
    elif dataset_name == "atc":
        dynamic_agents = ATCConverter.convert(data_path)
    return dynamic_agents
