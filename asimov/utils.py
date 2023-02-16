import collections
import glob
import os
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import numpy as np

from asimov import logger


@contextmanager
def set_directory(path: (Path, str)):
    """
    Change to a different directory for the duration of the context.

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """

    origin = Path().absolute()
    try:
        logger.info(f"Working temporarily in {path}")
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)
        logger.info(f"Now working in {origin} again")


def find_calibrations(time):
    """
    Find the calibration file for a given time.
    """
    if time < 1190000000:
        dir = "/home/cal/public_html/uncertainty/O2C02"
        virgo = "/home/carl-johan.haster/projects/O2/C02_reruns/V_calibrationUncertaintyEnvelope_magnitude5p1percent_phase40mraddeg20microsecond.txt"  # NoQA
    elif time < 1290000000:
        dir = "/home/cal/public_html/uncertainty/O3C01"
        virgo = "/home/cbc/pe/O3/calibrationenvelopes/Virgo/V_O3a_calibrationUncertaintyEnvelope_magnitude5percent_phase35milliradians10microseconds.txt"  # NoQA
    data_llo = glob.glob(f"{dir}/L1/*LLO*FinalResults.txt")
    times_llo = {
        int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_llo
    }

    data_lho = glob.glob(f"{dir}/H1/*LHO*FinalResults.txt")
    times_lho = {
        int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_lho
    }

    keys_llo = np.array(list(times_llo.keys()))
    keys_lho = np.array(list(times_lho.keys()))

    return {
        "H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]],
        "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]],
        "V1": virgo,
    }


def update(d, u, inplace=True):
    """Recursively update a dictionary."""
    if not inplace:
        d = deepcopy(d)
        u = deepcopy(u)
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
