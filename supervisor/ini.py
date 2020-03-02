"""
Handle run configuration files.
"""
from configparser import ConfigParser, NoOptionError
import os
import getpass
import ast

class RunConfiguration(object):

    def __init__(self, path):
        """
        Open the run configuration file.
        """
        self.ini_loc = path
        ini = ConfigParser()
        ini.optionxform=str

        try: 
            ini.read(path)
        except:
            raise ValueError("Could not open the ini file")

        self.ini = ini

    def check_fakecache(self):
        """
        Check to see if this file contains a fake-cache.

        Returns
        -------
        bool 
           Returns true if a fake cache has been used for this file.
        """
        try:
            if len(self.ini.get("lalinference", "fake-cache"))>0:
                return True
            else:
                return False
        except NoOptionError:
            return False

    def set_lalinference(self, **kwargs):
        for key, value in kwargs:
            self.ini.set("lalinference", key, value)

    def update_psds(self, psds):
        """
        Update the locations of the PSDs in the ini file.
        
        Parameters
        ----------
        psds : dict
           A dictionary of the various PSDs.
        """

        for det, location in psds.items():
                self.ini.set("engine", f"{det}-psd", location)

    def get_ifos(self):
        return ast.literal_eval(self.ini.get("analysis", "ifos"))

    def get_channels(self):
        return ast.literal_eval(self.ini.get("data", "channels"))

    def set_approximant(self, approximant, amporder, fref):
        self.ini.set("engine", "approx", approximant)
        self.ini.set("engine", "amporder", amporder)
        self.ini.set("engine", "fref", fref)

    def set_queue(self, queue="Priority_PE"):
        self.ini.set("condor", "queue", queue)

    def update_accounting(self):
        self.ini.set("condor", "accounting_group_user", self._get_user())

    def update_webdir(self, event, rootdir="public_html/LVC/projects/O3/C01/"):
        web_path = os.path.join(os.path.expanduser("~"), *rootdir.split("/"), event) # TODO Make this generic
        self.ini.set("paths", "webdir", web_path)

    def _get_user(self):
        user = getpass.getuser()
        return user

    def save(self):
        with open(self.ini_loc, "w") as fp:
            self.ini.write(fp)

