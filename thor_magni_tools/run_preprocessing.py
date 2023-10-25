import logging
from argparse import ArgumentParser

from .data_tests.logger import CustomFormatter
from .io import load_yaml_file, create_dir
from .preprocessing import TrajectoriesReprocessor


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


parser = ArgumentParser(description="Trajectory Data Preprocessor")

parser.add_argument(
    "--cfg_file",
    type=str,
    required=True,
    help="Path to the config file",
)

args = parser.parse_args()
cfg = load_yaml_file(args.cfg_file)

run_batch = True
if cfg["in_path"].endswith(".csv"):
    run_batch = False
create_dir(cfg["out_path"])

preprocessor = TrajectoriesReprocessor(
    csv_path=cfg["in_path"],
    out_path=cfg["out_path"],
    preprocessing_type=cfg["preprocessing_type"],
    **cfg["options"]
)
preprocessor.run()
