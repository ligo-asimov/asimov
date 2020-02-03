"""
Code for interacting with the condor scheduler.
"""

import htcondor

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
        
    def get_data(self):
        for schedd_ad in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
        schedd = htcondor.Schedd(schedd_ad)
        jobs = schedd.xquery(requirements="ClusterId == {}".format(self.cluster))
        for job in jobs:
            self.data = job
    return self.data
