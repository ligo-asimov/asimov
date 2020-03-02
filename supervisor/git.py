import os
import glob
import subprocess
import re
import getpass

import git

from . import ini


class MetaRepository(object):

    def __init__(self, directory):
        self.directory = directory
        os.chdir(directory)
        repos_list = glob.glob("*")
        self.repos = {event: os.path.join(directory, event) for event in repos_list}

    def get_repo(self, event):
        return EventRepo(self.repos[event])
        



class EventRepo(object):

    def __init__(self, directory):
        """
        Read a git repository containing event PE information.

        Parameters
        ----------
        directory : str 
           The path to the git repository on the filesystem.
        """
        self.event = directory.split("/")[-1]
        self.directory = directory
        self.repo = git.Repo(directory)
    
    def find_prods(self, category="C01_offline"):
        """
        Find all of the productions for a relevant category of runs
        in the event repository.

        Parameters
        ----------
        category : str, optional
           The category of run. Defaults to "C01_offline".
        """
        
        os.chdir(os.path.join(self.directory, category))
        prods = glob.glob("Prod*.ini")
        return prods

    def upload_prod(self, production, rundir, category="C01_offline"):
        """
        Upload the results of a PE job to the event repostory.

        Parameters
        ----------
        category : str, optional
           The category of the job.
           Defaults to "C01_offline".
        production : str
           The production name.
        rundir : str 
           The run directory of the PE job.
        """
        os.chdir(os.path.join(self.directory, category))

        dagman = subprocess.Popen(["/home/charlie.hoy/gitlab/pesummary-config/upload_to_event_repository.sh", 
                                   "--event", self.event,
                                   "--exp", production,
                                   "--rundir", rundir,
                                   "--edit_homepage_table"]
                                   , stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT   )
        out, err = dagman.communicate()

        if err or  not "master -> master" in str(out):
            raise ValueError(f"Sample upload failed.\n{out}\n{err}")
        else:
            return out

    def update(self, stash=False, branch="master"):
        """
        Pull the latest updates to the repository.

        Parameters
        ----------
        stash : bool, optional
           If true any changes which are in the local version
           of the repository are first stashed.
           Default is False.
        branch : str, optional
           The branch which should be checked-out.
           Default is master.
        """
        if stash:
            self.repo.git.stash()

        self.repo.git.checkout(branch)
        self.repo.git.pull()

        
        
    def build_dag(self, category, production, psds=None, user = None):
        gps_file = glob.glob("*gps*.txt")[0]
        os.chdir(os.path.join(self.directory, category))
        ini_loc = glob.glob(f"*{production}*.ini")[0]

        try: 
            ini = ini.RunConfiguration(ini_loc)
        except ValueError:
            raise ValueError("Could not open the ini file")

        ini.update_accounting(user)

        ini.set_queue("Priority_PE")

        if psds:
            ini.update_psds(psds, clobber=False)
            ini.run_bayeswave(False)
        else:
            # Need to generate PSDs as part of this job.
            ini.run_bayeswave(True)

        ini.update_webdir(self.event, production)
        ini.save()

        pipe = subprocess.Popen(["lalinference_pipe", "-g", f"{gps_file}", "-r", production, ini_loc],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        
        if err or  not "Successfully created DAG file." in str(out):
            raise ValueError(f"DAG file could not be created. {out} {err}")
        else:
            return out

    def submit_dag(self, category, production):
        os.chdir(os.path.join(self.directory, category))
        dagman = subprocess.Popen(["condor_submit_dag", os.path.join(production, "multidag.dag")], stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT   )
        stdout,stderr = dagman.communicate()

        if "submitted to cluster" in str(stdout):
            cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
            return cluster
        else:
            raise ValueError(f"The DAG file could not be submitted. {stdout} {stderr}")

        
