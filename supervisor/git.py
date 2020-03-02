import os
import glob
import subprocess
import re
from configparser import ConfigParser
import getpass

import git


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
        self.event = directory.split("/")[-1]
        self.directory = directory
        self.repo = git.Repo(directory)
    
    def find_prods(self, category="C01_offline"):
        os.chdir(os.path.join(self.directory, category))
        prods = glob.glob("Prod*.ini")
        return prods

    def upload_prod(self, production, rundir, category="C01_offline"):
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


        
    def build_dag(self, category, production, psds=None):
        gps_file = glob.glob("*gps*.txt")[0]
        os.chdir(os.path.join(self.directory, category))
        ini_loc = glob.glob(f"*{production}*.ini")[0]

        ini = ConfigParser()
        ini.optionxform=str

        try: 
            ini.read(ini_loc)
        except:
            raise ValueError("Could not open the ini file")

        #try:
        user = getpass.getuser()
        ini.set("condor", "accounting_group_user", user)
        #except:
        #    pass

        ini.set("condor", "queue", "Priority_PE")

        need_psds = False
        try:
            for det in psds.keys():
                ini.get("engine", f"{det}-psd")
        except:
            need_psds =True

        if psds and not production == "Prod0" and need_psds:
            for det, location in psds.items():
                ini.set("engine", f"{det}-psd", location)
        elif not production == "Prod0" and need_psds:
            raise ValueError("No PSD files were provided.")

        web_path = os.path.join(os.path.expanduser("~"), "public_html", "LVC", "projects", "O3", "C01", self.event, production) # TODO Make this generic
        print("web-path is {}".format(web_path))
        ini.set("paths", "webdir", web_path)

        with open(ini_loc, "w") as fp:
            ini.write(fp)

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

        
