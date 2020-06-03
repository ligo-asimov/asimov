import os
import glob
import subprocess
import re
import getpass

import git

from .ini import RunConfiguration


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

    def upload_prod(self, production, rundir, preferred=False, category="C01_offline", rootdir="public_html/LVC/projects/O3/C01/", rename = False):
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
        
        preferred_list = ["--preferred", "--append_preferred"]
        web_path = os.path.join(os.path.expanduser("~"), *rootdir.split("/"), self.event, production) # TODO Make this generic
        if rename:
            prod_name = rename
        else:
            prod_name = production

        command = ["/home/charlie.hoy/gitlab/pesummary-config/upload_to_event_repository.sh", 
                                   "--event", self.event,
                                   "--exp", prod_name,
                                   "--rundir", rundir,
                                   "--webdir", web_path,
                                   "--edit_homepage_table"]
        print(command)
        if preferred: 
            command += preferred_list
        dagman = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = dagman.communicate()

        if err or  not "master -> master" in str(out):
            raise ValueError(f"Sample upload failed.\n{out}\n{err}")
        else:
            return out

    def upload_preferred(self, event, prods):
        """
        Prepare the preferred PESummary file by combining all of the productions for an event which are
        marked as `Preferred` or `Finalised`.

        Parameters
        ----------
        event : `asimov.gitlab.EventIssue`
           The event which the preferred upload is being prepared for.
        prods : list
           A list of all of the productions which should be included in the preferred file.
        """

        samples = []
        labels = []
        configs = []

        for prod in prods:
            samples.append(glob.glob(str(os.path.join(event.data[f"{prod}_rundir"], "posterior_samples"),)+"/*.hdf5")[0])
            run_ini = os.path.join(event.data[f"{prod}_rundir"], "config.ini")
            actual_config = RunConfiguration(run_ini)
            engine_data = actual_config.get_engine()
            labels.append(f"C01:{engine_data['approx']}")
            configs.append(str(os.path.join(event.data[f"{prod}_rundir"], "config.ini")))


        os.chdir(os.path.join(self.directory, "Preferred", "PESummary_metafile"))

        command = ["summarycombine",
                   "--webdir", f"/home/daniel.williams/public_html/LVC/projects/O3/preferred/{event.title}",
                   "--samples", ]
        command += samples
        command += ["--labels"]
        command += labels
        command += ["--config"]
        command += configs
        command += ["--gw"]

        dagman = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = dagman.communicate()

        print(out)
        print(err)

        copy(f"/home/daniel.williams/public_html/LVC/projects/O3/preferred/{event.title}/samples/posterior_samples.h5", os.path.join(self.directory, "Preferred", "PESummary_metafile"))
        self.repo.git.add("Preferred/PESummary_metafile/posterior_samples.h5")
        self.repo.git.commit("-m", "Updated the preferred sample metafile.")
        self.repo.git.push()

        event.labels += ["Preferred cleaned"]
        event.issue_object.save()

        return True



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
        """
        Construct a DAG file in order to submit a production to the condor cluster using LALInferencePipe.

        Parameters
        ----------
        category : str, optional
           The category of the job.
           Defaults to "C01_offline".
        production : str
           The production name.
        psds : dict, optional
           The PSDs which should be used for this DAG. If no PSDs are provided the PSD files specified in the ini file will be used instead.
        user : str
           The user accounting tag which should be used to run the job.
        """
        
        os.chdir(os.path.join(self.directory, category))
        gps_file = glob.glob("*gps*.txt")[0]
        ini_loc = glob.glob(f"*{production}*.ini")[0]

        try: 
            ini = RunConfiguration(ini_loc)
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
        """
        Submit a DAG file to the condor cluster.
        

        Parameters
        ----------
        category : str, optional
           The category of the job.
           Defaults to "C01_offline".
        production : str
           The production name.

        Returns
        -------
        int
           The cluster ID assigned to the running DAG file.
        """
        os.chdir(os.path.join(self.directory, category))
        dagman = subprocess.Popen(["condor_submit_dag", os.path.join(production, "multidag.dag")], stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT   )
        stdout,stderr = dagman.communicate()

        if "submitted to cluster" in str(stdout):
            cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
            return cluster
        else:
            raise ValueError(f"The DAG file could not be submitted. {stdout} {stderr}")

        
