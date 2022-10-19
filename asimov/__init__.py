"""
Supervisor: A package for interacting with
long-running data analysis jobs.
"""


__author__ = """Daniel Williams"""
__email__ = "daniel.williams@ligo.org"
__packagename__ = __name__

import os
import logging

from pkg_resources import DistributionNotFound, get_distribution, resource_string

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "dev"
    pass

try:
    import ConfigParser as configparser
except ImportError:
    import configparser
default_config = resource_string(__name__, "{}.conf".format(__packagename__))

config = configparser.ConfigParser()
# if not config_file:

config.read_string(default_config.decode("utf8"))
config_locations = [
    os.path.join(os.curdir, "{}.conf".format(__packagename__)),
    os.path.join(
        os.path.expanduser("~"),
        ".config",
        __packagename__,
        "{}.conf".format(__packagename__),
    ),
    os.path.join(os.path.expanduser("~"), ".{}".format(__packagename__)),
    "/etc/{}".format(__packagename__),
]

config_locations.reverse()

config.read([conffile for conffile in config_locations])



logger_name = "asimov"
logger = logging.getLogger(logger_name)

ch = logging.StreamHandler()
print_formatter = logging.Formatter('[%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
ch.setFormatter(print_formatter)
ch.setLevel(logging.ERROR)

logfile = "asimov.log"
fh = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s [%(name)s][%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
# fh.setLevel()

logger.addHandler(ch)
logger.addHandler(fh)


try:
    if config.get("ledger", "engine") == "gitlab":
        from .gitlab import GitlabLedger

        current_ledger = GitlabLedger()
    elif config.get("ledger", "engine") == "yamlfile":
        from .ledger import YAMLLedger

        current_ledger = YAMLLedger(config.get("ledger", "location"))
    else:
        current_ledger = None
except FileNotFoundError:
    #logger.error("Could not find a valid ledger file.")
    current_ledger = None
