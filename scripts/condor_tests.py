from asimov import config
from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov.condor import CondorJobList, CondorJob
import yaml

# server, repository = connect_gitlab()
# events = gitlab.find_events(repository,
#                             #milestone=config.get("olivaw", "milestone"),
#                             subset=["GW200115A"],
#                             update=False,
#                             repo=True)

ledger = "/home/pe.o3/public_html/LVC/o3a-final/ledger.yaml"
with open(ledger, "r") as filehandle:
    events = yaml.safe_load(filehandle.read())

def get_jobs():
    """
    Return the cluster IDs of all of the jobs running for the current user.
    """
    
class CondorJob:
    """
    Represent a specific condor Job.
    """

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
        cls.status = dictionary['status']
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


from asimov import config
from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov.condor import CondorJobList, CondorJob
import yaml

# server, repository = connect_gitlab()
# events = gitlab.find_events(repository,
#                             #milestone=config.get("olivaw", "milestone"),
#                             subset=["GW200115A"],
#                             update=False,
#                             repo=True)

ledger = "/home/pe.o3/public_html/LVC/o3a-final/ledger.yaml"
with open(ledger, "r") as filehandle:
    events = yaml.safe_load(filehandle.read())

def get_jobs():
    """
    Return the cluster IDs of all of the jobs running for the current user.
    """
    
class CondorJob:
    """
    Represent a specific condor Job.
    """

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
        cls.status = dictionary['status']
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


from asimov import config
from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov.condor import CondorJobList, CondorJob
import yaml

# server, repository = connect_gitlab()
# events = gitlab.find_events(repository,
#                             #milestone=config.get("olivaw", "milestone"),
#                             subset=["GW200115A"],
#                             update=False,
#                             repo=True)

ledger = "/home/pe.o3/public_html/LVC/o3a-final/ledger.yaml"
with open(ledger, "r") as filehandle:
    events = yaml.safe_load(filehandle.read())

def get_jobs():
    """
    Return the cluster IDs of all of the jobs running for the current user.
    """
    
class CondorJob:
    """
    Represent a specific condor Job.
    """

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
        cls.status = dictionary['status']
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


from asimov import config
from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab

# server, repository = connect_gitlab()
# events = gitlab.find_events(repository,
#                             #milestone=config.get("olivaw", "milestone"),
#                             subset=["GW200115A"],
#                             update=False,
#                             repo=True)

jobs = CondorJobList()
jobs.refresh()

for job in jobs.jobs.values():
    print(job)

# for event in events:

#     on_deck = [production
#                for production in event.productions
#                if production.status.lower() in ACTIVE_STATES]
#     for production in on_deck:
#         print(production.name)
#         print(production.meta['job id'] in jobs.jobs.keys())

jobs = CondorJobList()

#for job in jobs.jobs.values():
#    print(job)

for event in events:
    productions = {}
    for prod in event['productions']:
        productions.update(prod)

    for name, production in productions.items():
        if production['status'] == "running":
            print(event['name'], name)
            if not "job id" in production:
                print("Job ID is missing")
                continue
            if production['job id'] in jobs.jobs:
                print(jobs.jobs[production['job id']])
            else:
                print("\t Job is not running")

#     on_deck = [production
#                for production in event.productions
#                if production.status.lower() in ACTIVE_STATES]
#     for production in on_deck:
#         print(production.name)
#         print(production.meta['job id'] in jobs.jobs.keys())

jobs = CondorJobList()

#for job in jobs.jobs.values():
#    print(job)

for event in events:
    productions = {}
    for prod in event['productions']:
        productions.update(prod)

    for name, production in productions.items():
        if production['status'] == "running":
            print(event['name'], name)
            if not "job id" in production:
                print("Job ID is missing")
                continue
            if production['job id'] in jobs.jobs:
                print(jobs.jobs[production['job id']])
            else:
                print("\t Job is not running")

#     on_deck = [production
#                for production in event.productions
#                if production.status.lower() in ACTIVE_STATES]
#     for production in on_deck:
#         print(production.name)
#         print(production.meta['job id'] in jobs.jobs.keys())

jobs = CondorJobList()

#for job in jobs.jobs.values():
#    print(job)

for event in events:
    productions = {}
    for prod in event['productions']:
        productions.update(prod)

    for name, production in productions.items():
        if production['status'] == "running":
            print(event['name'], name)
            if not "job id" in production:
                print("Job ID is missing")
                continue
            if production['job id'] in jobs.jobs:
                print(jobs.jobs[production['job id']])
            else:
                print("\t Job is not running")

#     on_deck = [production
#                for production in event.productions
#                if production.status.lower() in ACTIVE_STATES]
#     for production in on_deck:
#         print(production.name)
#         print(production.meta['job id'] in jobs.jobs.keys())


