"""
Code for interacting with the condor scheduler.

An important function of asimov is interaction with condor schedulers in order to track the status of running jobs.

In order to improve performance the code caches results from the query to the scheduler.

"""
import os
import datetime
from dateutil import tz
import htcondor
import yaml

from asimov import config, logger, LOGGER_LEVEL

class CondorJob:
    """
    Represent a specific condor Job.
    """
    return datetime.datetime.utcfromtimestamp(dt).replace(tzinfo=tzinfo)

    def __init__(self, idno, command, hosts, status, **kwargs):
        """
        A representation of a condor job on a scheduler.

        Parameters
        ----------
        idno : int
           The jobId or ClusterId for the job.
        command: str
           The command being run.
        hosts: int
           The number of hosts currently processing the job.
        status: int
           The status condition for the job.
       
        
        """

        self.idno = idno
        self.command = command
        self.hosts = hosts
        self.status = status

        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def __repr__(self):
        return f"<htcondor job | {self.idno} | {self.status} | {self.hosts} | {self.name} | {len(self.subjobs)} subjobs >"

    def __str__(self):
        return repr(self)

    @classmethod
    def from_dict(cls, dictionary):
        """
        Create a respresentation from a dictionary.
        """
        cls = cls()
        cls.idno = dictionary['id']
        cls.command = dictionary['command']
        cls.hosts = dictionary['hosts']
        cls._status = dictionary['status']
        if "name" in dictionary:
            cls.name = dictionary['name']
        else:
            cls.name = "asimov job"
        if "dag id" in dictionary:
            cls.dag = dictionary['dag id']
        else:
            cls.dag = None
        cls.subjobs = []

        return cls

    def add_subjob(self, job):
        """
        Add a subjob of this job.
        """
        self.subjobs.append(job)
        
    @property
    def status(self):
        statuses = {0: "Unexplained",
                    1: "Idle",
                    2: "Running",
                    3: "Removed",
                    4: "Completed",
                    5: "Held",
                    6: "Submission error"}
        return statuses[self._status]


        
class CondorJobList:
    """
    Store the list of running condor jobs.
    """
    def __init__(self):
        self.jobs = {}
        
    def refresh(self):
        """
        Poll the schedulers to get the list of running jobs and update the database.
        """
        data = []
        for schedd_ad in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
            try:
                schedd = htcondor.Schedd(schedd_ad)
                jobs = schedd.query(opts=htcondor.htcondor.QueryOpts.DefaultMyJobsOnly,
                                    projection=["ClusterId", "Cmd", "CurrentHosts", "HoldReason", "JobStatus", "DAG_Status", "JobBatchName", "DAGManJobId"],
                )
                data += jobs
            except:
                pass
        retdat = []

        for datum in data:
            if "ClusterId" in datum:
                job = dict(id=int(float(datum['ClusterId'])),
                           command=datum['Cmd'],
                           hosts=datum["CurrentHosts"],
                           status=datum["JobStatus"]
                       )
                if "HoldReason" in datum:
                    job["hold"] =  datum["HoldReason"]
                if "JobBatchName" in datum:
                    job["name"] =  datum["JobBatchName"]
                if not "DAG_Status" in datum and "DAGManJobID" in datum:
                    job["dag id"] = int(float(datum['DAGManJobId']))
            retdat.append(CondorJob.from_dict(job))

        for datum in retdat:
            
            if not datum.dag:
                self.jobs[datum.idno] = datum
        # # Now search for subjobs
        for datum in retdat:
           if datum.dag:
               if datum.dag in self.jobs:
                   self.jobs[datum.dag].add_subjob(datum)
               else:
                   self.jobs[datum.idno] = datum
