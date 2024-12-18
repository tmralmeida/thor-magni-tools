import os
import logging
from argparse import ArgumentParser
import ray

from .data_tests.logger import CustomFormatter
from .preprocessing import ActionsMerger


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


parser = ArgumentParser(description="Trajectory Data and actions Merger")

parser.add_argument(
    "--actions_path",
    type=str,
    required=True,
    help="Path to the actions raw file",
)


parser.add_argument(
    "--files_dir",
    type=str,
    required=True,
    help="Path to trajectories file(s) after run_preprocessing",
)

parser.add_argument(
    "--out_path",
    type=str,
    required=False,
    default="thor_magni_tools/outputs/data",
    help="Data to store the merged files",
)


args = parser.parse_args()
files_path = args.files_dir
run_batch = True
if files_path.endswith(".csv"):
    run_batch = False


if run_batch:

    @ray.remote
    def ray_run_processor(processor):
        return processor.run()

    ray.init()
    mergers = [
        ActionsMerger(
            actions_path=args.actions_path,
            csv_path=os.path.join(files_path, file_name),
            out_dir=args.out_path,
        )
        for file_name in os.listdir(files_path)
    ]
    ray.get([ray_run_processor.remote(merger) for merger in mergers])
else:
    merger = ActionsMerger(
        actions_path=args.actions_path, csv_path=files_path, out_dir=args.out_path
    )
    merger.run()
