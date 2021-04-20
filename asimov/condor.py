"""
Code for interacting with the condor scheduler.
"""
import os
from configparser import ConfigParser

import htcondor

from . import ini

class CondorJob(object):
    """
    An object to represent a running condor job.

    Parameters
    ----------
    cluster_id : int
       The cluster ID for this job.
    """

    def __init__(self, cluster_id):
        self.cluster = cluster_id
        self.data = {}
        self.get_data()

    @property
    def status(self):
        data = self.get_data()

        job_status = data['JobStatus']
        statuses = {0: "Unexplained",
                    1: "Idle",
                    2: "Running",
                    3: "Removed",
                    4: "Completed",
                    5: "Held",
                    6: "Submission error"}
        return statuses[job_status]

    @property
    def run_directory(self):
        """
        Find the run directory.
        """
        if not "Err" in self.data:
            raise ValueError
        error_file = self.data['Err']
        rundir = "/".join(error_file.split("/")[:-1])
        return rundir

    def get_asset(self, path):
        """
        Find an asset related to this job.
        """
        path = os.path.join(self.run_directory, path)
        if os.path.exists(path):
            return path
        else:
            return None

    def get_config(self):
        """
        Open the configuration file for this job.
        """
        ini_location = os.path.join(self.run_directory,
                                    "config.ini")

        P = ini.RunConfiguration(ini_location)
        return P

    def get_data(self):
        data = {}
        for schedd_ad in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
            schedd = htcondor.Schedd(schedd_ad)
            try:
                jobs = schedd.xquery(constraint="ClusterId == {}".format(self.cluster))
                for job in jobs:
                    data = job
                    break
            except RuntimeError as e:
                print(e)
        if len(list(data.keys()))==0:
            raise ValueError
        self.data = data
        return data
    
