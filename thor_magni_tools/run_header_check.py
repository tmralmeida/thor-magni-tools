import os
import logging
from argparse import ArgumentParser

from .data_tests.logger import CustomFormatter
from .utils.load import load_csv_metadata, preprocessing_header
from .data_tests.test_csv import validate_header, validate_header_with_dataframe


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
LOGGER.addHandler(ch)


parser = ArgumentParser(description="CSV Data Validator")

parser.add_argument(
    "--dir_path",
    type=str,
    required=True,
    help="Path to the Dataset",
)
parser.add_argument(
    "--sc_id",
    type=str,
    required=True,
    help="Scenario ID. E.g: Scenario_1",
)

args = parser.parse_args()

root_path = os.path.join(args.dir_path, args.sc_id)
files_list = os.listdir(root_path)


for _fn in files_list:
    LOGGER.warning("Running file: %s", _fn)
    raw_df, header_dict = load_csv_metadata(os.path.join(root_path, _fn))
    new_header_dict = preprocessing_header(header_dict)
    validate_header(_fn, new_header_dict)
    validate_header_with_dataframe(new_header_dict, raw_df)
