#! /usr/bin/env python3

"""
This script is designed to interface with a gitlab project
and use issues defined in its issue tracker to run Parameter Estimation 
jobs, and manage them.

Authors
-------
Daniel Williams <daniel.williams@ligo.org>
"""

import gitlab
import json
import time
import os
import glob

import htcondor

import subprocess
from configparser import ConfigParser

import re

import datetime
import git

import ast

access_token = os.environ['GITLAB_TOKEN'] # 
project_id = 3816
uber_repo = "/home/daniel.williams/events/O3/o3a_catalog_events" # The repository which contains all of the submodularised event repositories.

gl = gitlab.Gitlab('https://git.ligo.org', private_token=access_token)
pe_catalogue = gl.projects.get(project_id)

#with open("pe-robot.json", "r") as data:
#    runs = json.load(data)

runs = {}

schedd_ad = htcondor.Collector().locate(htcondor.DaemonTypes.Schedd)
schedd = htcondor.Schedd(schedd_ad)

def fix_ini_caps(ini):

    try:
        ini.set("condor", "mergeNSscript", ini.get("condor", "mergensscript"))
        ini.set("condor", "mergeMCMCscript", ini.get("condor", "mergemcmcscript"))
        ini.set("condor", "combinePTMCMCh5script", ini.get("condor", "combineptmcmch5script"))
    except:
        pass
    dets = ['H1', 'L1', 'V1']
    for det in dets:
        try:
            ini.set("engine", f"{det}-spcal-envelope", ini.get("engine", "{}-spcal-envelope".format(det.lower())))
        except:
            pass

    return ini

def get_psds(rundir):
    dets = ['H1', 'L1', 'V1']
    files = {}
    for det in dets:
        psd_dir = f"ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
        psd_file = os.path.join(rundir, psd_dir)
        exists = os.path.exists(psd_file)
        if exists:
            files[det] =psd_file
    return files

def check_for_psd(rundir):

    files = get_psds(rundir)
    if len(files.keys()) >=1:
        return True
    else:
        return False

def check_for_ini(event_dir, event):
    c01_dir = os.path.join(event_dir, "C01_offline")
    ini = glob.glob(os.path.join(c01_dir, "*.ini"))
    return ini

def start_Prod1(event, prod0_dir):
    event_repo = os.path.join(uber_repo, event)

    repo = git.Repo(event_repo)
    repo.git.checkout("master")
    repo.git.pull()

    if not os.path.exists(event_repo):
        print("++ I can't find the repository for this event.")

    ini_files = check_for_ini(event_repo, event)

    if not len(ini_files)>=2:
        print("++ I can't find the all the ini files")


    c01_dir = os.path.join(event_repo, "C01_offline")

    os.chdir(c01_dir)

    gps_file = f"{event}_gpsTime.txt"
    if not os.path.exists(os.path.join(c01_dir, gps_file)):
        gps_file = f"{event}_gps_time.txt"

    for filename in ini_files:
        if "Prod1" in filename:
            prod1_ini = filename
    
    # Update the ini file
    P = ConfigParser()
    P.optionxform=str
    try:
        P.read(prod1_ini)
    except:
        print(f"There's been a problem with the Prod1 ini for {event}")

    psds = get_psds(prod0_dir)
    dets = ast.literal_eval(P.get("analysis", "ifos"))
    for det in dets:

        if det not in psds.keys():
            print(f"/{det}/ not found in {psds.keys()}")
            return None
        else:
            P.set("engine", f"{det}-psd", psds[det])

    P.set("paths", "webdir", os.path.join("/home/daniel.williams/public_html/LVC/projects/O3/C01/", event))

    P = fix_ini_caps(P)

    with open(prod1_ini,'w') as fp:
        P.write(fp)


    pipe_ret = subprocess.call(["lalinference_pipe", "-g", f"{gps_file}", "-r", "Prod1", f"{prod1_ini}"])

    if not pipe_ret == 0:
        # This job has failed
        return None

    dagman = subprocess.Popen(["condor_submit_dag", os.path.join(event_repo, "C01_offline", "Prod1", "multidag.dag")], stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT   )
    stdout,stderr = dagman.communicate()

    if "submitted to cluster" in str(stdout):
        cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
        return cluster
    else:
        print(stdout)
        print(stderr)
        return None
    


def start_run(event):
    event_repo = os.path.join(uber_repo, event)

    repo = git.Repo(event_repo)
    repo.git.checkout("master")
    repo.git.pull()

    if not os.path.exists(event_repo):
        print("++ I can't find the repository for this event.")

    ini_files = check_for_ini(event_repo, event)

    if not len(ini_files)>=2:
        print("++ I can't find the all the ini files")


    c01_dir = os.path.join(event_repo, "C01_offline")

    os.chdir(c01_dir)

    gps_file = f"{event}_gpsTime.txt"
    if not os.path.exists(os.path.join(c01_dir, gps_file)):
        gps_file = f"{event}_gps_time.txt"

    for filename in ini_files:
        if "Prod0" in filename:
            prod0_ini = filename
    
    # Update the ini file
    P = ConfigParser()
    P.optionxform=str
    P.read(prod0_ini)

    P.set("paths", "webdir", os.path.join("/home/daniel.williams/public_html/LVC/projects/O3/C01/", event))

    P = fix_ini_caps(P)

    with open(prod0_ini,'w') as fp:
        P.write(fp)


    pipe_ret = subprocess.call(["lalinference_pipe", "-g", f"{gps_file}", "-r", "Prod0", f"{prod0_ini}"])

    if not pipe_ret == 0:
        # This job has failed
        return None

    dagman = subprocess.Popen(["condor_submit_dag", os.path.join(event_repo, "C01_offline", "Prod0", "multidag.dag")], stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT   )
    stdout,stderr = dagman.communicate()

    if "submitted to cluster" in str(stdout):
        cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
    else:
        print(stdout)
        print(stderr)

    return cluster

def get_rundir_from_condor(job_data):
    error_file = job_data['Err']
    rundir = "/".join(error_file.split("/")[:-1])
    return rundir

def get_condor_status(cluster_id):
    data = {}
    for schedd_ad in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
        schedd = htcondor.Schedd(schedd_ad)
        jobs = schedd.xquery(requirements="ClusterId == {}".format(cluster_id))
        for job in jobs:
            data = job
    return data

def get_run_info(issue):
    notes = issue.notes
    data = {}
    for note in reversed(notes.list()):
        if "# Run information" in note.body:
            rows = note.body.split('\n')[2:]
            
            for row in rows:
                try:
                    key, value = row.split(":")
                    data[key.strip()] = value.strip()
                except:
                    pass
    return data

if __name__ == "__main__":
    while True:
        gl = gitlab.Gitlab('https://git.ligo.org', private_token=access_token)
        for issue in pe_catalogue.issues.list(labels=['trigger'], per_page=100):
            if not issue.title in runs.keys():
                # This is an event we've not seen before
                runs[issue.title] = {}
                runs[issue.title]['issue_id'] = issue.id
                runs[issue.title]['issue_labels'] = issue.labels
            if "C01::Robot" in issue.labels:
                print(f("I need to start {issue.title}"))
            elif "C01::Prod0 Running" in issue.labels:
                try:
                    cluster_id = runs[issue.title]['Prod0_cluster_id']
                except:
                    data = get_run_info(issue)
                    if 'Prod0' in data.keys():
                        cluster_id = data['Prod0']
                    else:
                        cluster_id = None
                        issue.labels += ["C01 cluster missing"]

                if cluster_id:
                    job = get_condor_status(cluster_id)
                    if not 'JobStatus' in job:
                        print(f"Something's wrong with {issue.title}")
                        issue.labels.remove("C01::Prod0 Running")
                        issue.labels += ["C01::Stuck"]
                        #rundir = get_rundir_from_condor(job)
                        #issue.notes.create({'body': '# Run problem\nThe Prod0 job ran into an unknown error at {}.\nThe run directory is {}'.format(datetime.datetime.now(), rundir)})
                        issue.save()
                        continue
                    elif job['JobStatus'] == 2:
                        # The job is still running
                        #print(f"* {issue.title} is running.")
                        pass
                    elif job['JobStatus'] == 4:
                        # The job has completed
                        issue.labels += ["C01 Prod0 run complete"]
                    elif job['JobStatus'] == 5:
                        # The job is held.
                        # Mark it as stuck
                        issue.labels = issue.labels + ["C01::Stuck"]
                        issue.notes.create({'body': '# Job hold\nThe Prod0 job was held at {}'.format(datetime.datetime.now())})
                        issue.save()
                if not "PSD Ready" in issue.labels:

                    #print(f"I need to check if the PSDs are ready for {issue.title}")
                    if cluster_id:
                        rundir = get_rundir_from_condor(job)
                        ready = check_for_psd(rundir)
                        psds = get_psds(rundir)
                        #print(f"The rundir is {rundir}")
                        if ready:
                            print(f"The PSD files for {issue.title} are ready.")
                            issue.labels += ["PSD Ready"]
                            
                            issue.notes.create({'body': f'# PSD Files\nThe PSD files for this event have been created. Remember to update the ini file for Prod1 to include these.\nThe PSDs are located at {psds}.'})

                elif "PSD Ready" in issue.labels:
                    prod0_rundir = get_rundir_from_condor(job)
                    print(f"* {issue.title} Prod1 may be ready to start.")
                    cluster_p1 = start_Prod1(issue.title, prod0_rundir)

                    if cluster_p1:
                        print(f"Submitted to cluster {cluster_p1}")
                        issue.labels.remove("C01::Prod0 Running")
                        issue.labels = issue.labels + ["C01::Prod1 Running"]
                        issue.notes.create({'body': f"# Run information\n\nProd1: {cluster_p1}"})
                        issue.assignee_ids = [246]
                        issue.save()

            elif "C01::Prod1 Running" in issue.labels:
                try:
                    cluster_id = runs[issue.title]['Prod1_cluster_id']
                except:
                    data = get_run_info(issue)
                    if 'Prod1' in data.keys():
                        cluster_id = data['Prod1']
                    else:
                        cluster_id = None
                        issue.labels += ["C01 cluster missing"]
                        

                if cluster_id:
                    job = get_condor_status(cluster_id)
                    if not 'JobStatus' in job:
                        print(f"Something's weird with Prod1 for {issue.title}")
                        issue.labels.remove("C01::Prod1 Running")
                        #rundir = get_rundir_from_condor(job)
                        issue.labels +=  ["C01::Stuck"]
                        issue.notes.create({'body': '# Run problem\nThe Prod1 job ran into an unknown error at {}\n'.format(datetime.datetime.now())})
                        issue.save()
                    elif job['JobStatus'] == 2:
                        # The job is still running
                        pass
                    elif job['JobStatus'] == 4:
                        # The job has completed
                        issue.labels += ["C01 Prod1 run complete"]

                #print(f"I need to check if the jobs are finished for {issue.title}")

            elif "C01::Ready to start" in issue.labels:
                print(f"* {issue.title} is marked ready to start.")
                cluster = start_run(issue.title)
                print(f"Submitted to cluster {cluster}")
                if cluster:
                    issue.labels += ["C01::Prod0 Running"]
                    issue.notes.create({'body': f"# Run information\n\nProd0: {cluster}"})
                    issue.assignee_ids = [246]
            issue.save()

        # with open("pe-robot.json", "w") as data:
        #     json.dump(runs, data)

        time.sleep(300)
