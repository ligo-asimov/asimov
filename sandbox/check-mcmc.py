import ast
import subprocess
from shutil import copy
from asimov import gitlab, mattermost
from asimov import config
from asimov import condor, git
from asimov.ini import RunConfiguration

import os, glob, datetime

from subprocess import check_output as bash


import otter

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))


uber_repository = git.MetaRepository(config.get("olivaw", "metarepository"))

events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

mattermost = mattermost.Mattermost()
from pesummary.gw.file.read import read


def get_all_jobs():

    all_jobs = bash('condor_q -af:j Iwd'.split(' '), universal_newlines=True)
    #print(all_jobs)
    all_jobs = str(all_jobs).split('\n')
    #print(all_jobs)
    all_jobs = filter( lambda x: x, all_jobs)

    wds = []
    ids = []
    for z in all_jobs:
        wds.append(z.split()[1])
        ids.append(z.split()[0])
    return ids, wds

def main():

    report = otter.Otter(filename="/home/daniel.williams/public_html/LVC/projects/O3/C01/audit_mcmc.html", 
                         author="R. Daniel Williams",
                         title="Asimov/Olivaw : Preferred run audit report"
    )

    with report:
        report + "This report contains the latest updates on the run status of the various PE runs ongoing at CIT."
        report + "Supervisor last checked these events at " + str(datetime.datetime.now())

    all_ids, all_wds = get_all_jobs()

    for event in events:
        print(event.title)

        if event.state == None:
            continue
        if "Special" in event.labels:
           continue
        try:
            repo = uber_repository.get_repo(event.title)
        except:
            print(f"{event.title} missing from the uberrepo")
            continue

        repo.update(stash=True)

        with report:
            report + f"#{event.title}"

        try:
            event_prods = repo.find_prods(config.get("olivaw", "run_category"))
        except:
            print(f"No runs in this repository")
            continue

        if event.state in ["Generating PSDs", "Productions running", "Stuck"]:
            psds_dict = {}
            prod_keys = [key for key in event.data.keys() if "Prod" in key[0:5]]
            n_productions = len(event_prods)
            event_psds_l = []

            pref_prod = []
            for prod in event_prods:
                prod = prod.split("_")[0]
                if prod in event.data:
                    if "blocked" in event.data[prod].lower(): continue
                    cluster = event.data[prod]
                    prod_rundir = event.data[f"{prod}_rundir"]
                    run_ini = os.path.join(prod_rundir, "config.ini")
                    actual_config = RunConfiguration(run_ini)
                    try:
                        engine_data = actual_config.get_engine()
                    except:
                        continue

                    if not "daniel.williams" in prod_rundir: 
                        continue

                    if actual_config.ini.get("analysis", "engine") == "lalinferencemcmc":
                        # Keep only lists that correspond to the working directory 
                        job_ids = [ number for number, directory in zip(all_ids, all_wds) if (prod in directory) and (event.title in directory) ]
                        print(job_ids)
                        if len(job_ids) > 0:
                            report += job_ids
                        tmp = "tmp"
                        try:
                            os.makedirs(tmp)
                        except:
                            pass

                        try:
                            os.makedirs(f"{prod_rundir}/{tmp}/html")
                            #os.popen(f"rm -r /home/john.veitch/projects/O3/SEOBNRv4P_rota_runs/{event.title}/{prod}")
                            os.makedirs(f"/home/john.veitch/projects/O3/SEOBNRv4P_rota_runs/{event.title}/{prod}-robot")
                        except:
                            pass

                        raw_pp_str = os.popen(f'grep cbcBayesPostProc {prod_rundir}/lalinference*.sh').read()
                        pspath0 = raw_pp_str.split('hdf5_snr.txt ')[-1].split(' ')[0]
                        for job in job_ids:
                            os.system(f'condor_ssh_to_job -ssh scp {job} remote:./*.hdf* {prod_rundir}/{tmp}')
                        
                        for h5file in glob.glob(f"{prod_rundir}/{tmp}/*.hdf5"):
                            pspath1 = h5file # os.path.join(prod_rundir, tmp,'*.hdf5')
                            # print(pspath1)
                            file = h5file.split("/")[-1]
                            copy(h5file, f"/home/john.veitch/projects/O3/SEOBNRv4P_rota_runs/{event.title}/{prod}-robot/{file}")
                            pspath = raw_pp_str.replace(pspath0,pspath1)
                            webpath = pspath.split("--outpath")[1].split()[0]
                        
                        
                            new_webpath = f"{prod_rundir}/{tmp}/html"
                            print(pspath.replace(webpath, new_webpath))
                            # os.popen(pspath.replace(webpath, new_webpath))

main()
