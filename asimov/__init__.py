"""
Supervisor: A package for interacting with 
long-running data analysis jobs.
"""


__author__ = """Daniel Williams"""
__email__ = 'daniel.williams@ligo.org'
__packagename__ = __name__

from pkg_resources import get_distribution, DistributionNotFound
from pkg_resources import resource_string
import os

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
default_config = resource_string(__name__, '{}.conf'.format(__packagename__))

config = configparser.ConfigParser()
#if not config_file:

config.read_string(default_config.decode("utf8"))
config_locations = [os.path.join(os.curdir, "{}.conf".format(__packagename__)),
                    os.path.join(os.path.expanduser("~"),
                                 ".config", __packagename__, "{}.conf".format(__packagename__)),
                    os.path.join(os.path.expanduser("~"),
                                 ".{}".format(__packagename__)),
                    "/etc/{}".format(__packagename__)]

config_locations.reverse()

config.read([conffile for conffile in config_locations])
