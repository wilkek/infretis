"""The functions to be used to run infretis via the terminal."""

import argparse

from infretis.scheduler import scheduler
from infretis.setup import setup_config
import sys


def infretisrun():
    """Read input and runs infretis."""
    # print python version
    print(f"Python version: {sys.version}")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", help="Location of infretis input file", required=True
    )

    args_dict = vars(parser.parse_args())
    input_file = args_dict["input"]
    config = setup_config(input_file)
    if config is None:
        return
    scheduler(config)
