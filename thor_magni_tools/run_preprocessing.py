import os
import logging
from argparse import ArgumentParser
import ray

from .data_tests.logger import CustomFormatter
from .io import load_yaml_file
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
    required=False,
    default="thor_magni_tools/preprocessing/cfg.yaml",
    help="Path to the config file",
)

args = parser.parse_args()
cfg = load_yaml_file(args.cfg_file)

run_batch = True
if cfg["in_path"].endswith(".csv"):
    run_batch = False

if run_batch:

    @ray.remote
    def ray_run_processor(processor):
        return processor.run()

    ray.init()
    processors = [
        TrajectoriesReprocessor(
            csv_path=os.path.join(cfg["in_path"], file_name),
            out_path=cfg["out_path"],
            preprocessing_type=cfg["preprocessing_type"],
            **cfg["options"]
        )
        for file_name in os.listdir(cfg["in_path"])
    ]
    ray.get(
            [ray_run_processor.remote(processor) for processor in processors]
        )

else:
    preprocessor = TrajectoriesReprocessor(
        csv_path=cfg["in_path"],
        out_path=cfg["out_path"],
        preprocessing_type=cfg["preprocessing_type"],
        **cfg["options"]
    )
    preprocessor.run()
