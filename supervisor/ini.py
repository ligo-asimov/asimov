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

    def update_psds(self, psds, clobber=False):
        """
        Update the locations of the PSDs in the ini file.
        
        Parameters
        ----------
        psds : dict
           A dictionary of the various PSDs.
        """
        for det, location in psds.items():
            try:
                self.ini.get("engine", f"{det}-psd")
            except:
                needs_psd = True
        if needs_psd or clobber:
            self.ini.set("engine", f"{det}-psd", location)

    def run_bayeswave(self, status=True):
        """
        Ensure that Bayeswave is run for this job.

        This should be run in order to add Bayeswave to produce PSDs for an event.

        Parameters
        ----------
        status : bool, optional
           If set to true (the default) then a line will be added to ensure that Bayeswave is run to generate PSDs. If False then this line will be removed from the ini file if it exists.
        """
        if status:
            self.ini.set("condor", "bayeswave", "%(lalsuite-install)s/bin/BayesWave")
        else:
            try:
                self.ini.remove_option("condor", "bayeswave")
            except:
                pass
        
            
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

    def update_accounting(self, user=None):
        """
        Update the accounting tag for this job.
        Defaults to the user account running the supervisor.
        
        Parameters
        ----------
        user : str 
           The accounting user to be added to the ini file.
        """
        
        if not user:
            user = self._get_user()
        self.ini.set("condor", "accounting_group_user", user)

    def update_webdir(self, event, prod, rootdir="public_html/LVC/projects/O3/C01/"):
        """
        Update the web directory in the ini file.
        """
        
        web_path = os.path.join(os.path.expanduser("~"), *rootdir.split("/"), event, prod) # TODO Make this generic
        self.ini.set("paths", "webdir", web_path)

    def _get_user(self):
        user = getpass.getuser()
        return user

    def save(self):
        with open(self.ini_loc, "w") as fp:
            self.ini.write(fp)

