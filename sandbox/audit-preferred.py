import ast
import subprocess
from shutil import copy
from asimov import gitlab, mattermost
from asimov import config
from asimov import condor, git
from asimov.ini import RunConfiguration

import os, glob, datetime

import otter

import click

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))


uber_repository = git.MetaRepository(config.get("olivaw", "metarepository"))

events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

mattermost = mattermost.Mattermost()
from pesummary.gw.file.read import read

def get_psds_rundir(rundir):
    psds = {}
    dets = ['L1', 'H1', 'V1']
    for det in dets:
        asset = f"{rundir}/ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
        if os.path.exists(asset):
            psds[det] = asset
    return psds


def upload_results(repo, event, prods, report):


    print("*"*15)
    print(f"Adding {prods} to the preferred summary file.")
    print("*"*15)

    samples = []
    labels = []
    configs = []
    
    calibration = []
    for prod in prods:
        rundir = event.data[f"{prod}_rundir"]
        samples.append(glob.glob(str(os.path.join(rundir, "posterior_samples"),)+"/*.hdf5")[0])

        run_ini = os.path.join(event.data[f"{prod}_rundir"], "config.ini")
        actual_config = RunConfiguration(run_ini)
        engine_data = actual_config.get_engine()
        psds = actual_config.get_psds()
        if len(psds) == 0:
            psds = get_psds_rundir(rundir)
        calib = actual_config.get_calibration()
        run_name = engine_data['approx'].replace('pseudoFourPN','')
        labels.append(f"C01:{run_name}")
        configs.append(str(os.path.join(event.data[f"{prod}_rundir"], "config.ini")))


    os.chdir(os.path.join(repo.directory, "Preferred", "PESummary_metafile"))

    command = ["summarycombine",
               "--webdir", f"/home/daniel.williams/public_html/LVC/projects/O3/preferred/{event.title}",
               "--samples", ]
    command += samples
    command += ["--labels"]
    command += labels
    command += ["--config"]
    command += configs
    command += ["--calibration"]
    command += [f"{key}:{value}" for key, value in calib.items()]
    command += ["--psd"]
    command += [f"{key}:{value}" for key, value in psds.items()]
    command += ["--gracedb"]
    command += [event.title]
    command += ["--redshift_method",  "exact"]
    command += ["--cosmology", "Planck15_lal"]
    command += ["--gw"]

    print(command)
    with report:
        report + f"```\n {command}```"

    dagman = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = dagman.communicate()

    print(out)
    print(err)

    copy(f"/home/daniel.williams/public_html/LVC/projects/O3/preferred/{event.title}/samples/posterior_samples.h5", os.path.join(repo.directory, "Preferred", "PESummary_metafile"))
    repo.repo.git.add("Preferred/PESummary_metafile/posterior_samples.h5")
    repo.repo.git.commit("-m", "Updated the preferred sample metafile.")
    repo.repo.git.push()

    event.labels += ["Preferred cleaned"]
    event.issue_object.save()

    return True

import click

@click.command()
@click.option('--event', "eventflag", default=None, help='The event to rebuild')
def main(eventflag):

    report = otter.Otter(filename="/home/daniel.williams/public_html/LVC/projects/O3/C01/audit_current.html", 
                         author="R. Daniel Williams",
                         title="Asimov/Olivaw : Preferred run audit report"
    )

    with report:
        report + "This report contains the latest updates on the run status of the various PE runs ongoing at CIT."
        report + "Supervisor last checked these events at " + str(datetime.datetime.now())

    global events


    if eventflag:
        events = [event for event in events if event.title == eventflag]

    for event in events:
        print(event.title)

        # if event.state == None:
        #     continue
        # if "Special" in event.labels:
        #    continue
        # if "Preferred cleaned" in event.labels:
        #    continue

        try:
            repo = uber_repository.get_repo(event.title)
        except:
            print(f"{event.title} missing from the uberrepo")
            continue

        repo.update(stash=True)

        with report:
            report + f"#{event.title}"

        preferred_summary = os.path.join(repo.directory, "Preferred", "PESummary_metafile", "posterior_samples.h5")

        try:
            print(preferred_summary)
            data = read(preferred_summary)

            print(data.labels)

            with report:
                report + f"{data.labels}"
        except OSError:
            with report:
                report + f"There is no preferred file in this repository."


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
                    cluster = event.data[prod]

                    run_ini = os.path.join(event.data[f"{prod}_rundir"], "config.ini")
                    actual_config = RunConfiguration(run_ini)
                    engine_data = actual_config.get_engine()

                    if "finalised" in cluster.lower():
                        print(f"{prod} is the preferred production")
                        pref_prod.append(prod)
            try:
                if len(pref_prod)==0: continue
                upload_results(repo, event, pref_prod, report=report)
            except FileNotFoundError as e:
                print(e)

if __name__ == "__main__":

   main()
