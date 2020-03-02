import ast

from supervisor import gitlab, mattermost
from supervisor import config
from supervisor import condor, git
from supervisor.ini import RunConfiguration

import os, glob

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(3816)

def get_psds_rundir(rundir):
    psds = {}
    dets = ['L1', 'H1', 'V1']
    for det in dets:
        asset = f"{rundir}/ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
        if os.path.exists(asset):
            psds[det] = asset
    return psds

uber_repository = git.MetaRepository("/home/daniel.williams/events/O3/o3a_catalog_events")

events = gitlab.find_events(repository, milestone="PE: C01 Reruns")

mattermost = mattermost.Mattermost()

mattermost.send_message(":mega: The run supervising robot is running. :robot:", "@daniel-williams")

message = """# Run updates\n"""
message += """| Event | IFOS | Cluster | Production | Status | PSDs |\n"""
message += """|---|---|---|---|---|---|\n"""



for event in events:
    print(event.title)
    if event.state == None:
        continue
    if "Special" in event.labels:
        continue

    if "DAQ::Needs BW" in event.labels and not (event.state in ["Ready to start", "Productions running"]):
        continue

    try:
        repo = uber_repository.get_repo(event.title)
    except:
        print(f"{event.title} missing from the uberrepo")
        continue

    repo.update()

    try:
        event_prods = repo.find_prods("C01_offline")
    except:
        print(f"No C01 runs in this repository")
        continue
    
    event_psds = set(["L1", "H1", "V1"])

    if event.state == "Ready to start":
        print(f"I'm going to try to start {event.title}")
        try:
            out = repo.build_dag("C01_offline", "Prod0", psds_dict)
            status = "DAG ready"
        except ValueError as e:
            status = "DAG generation failed."
            print(e)
            continue
        try:
            cluster = repo.submit_dag("C01_offline", "Prod0")
            job = condor.CondorJob(cluster)
            event.data[f"Prod0_rundir"] = job.run_directory
            event.data["Prod0"] = cluster
            event.update_data()
            event.state = "Generating PSDs"
        except ValueError as e:            
            status = "Submission error"
            print(e)
            cluster = None

    elif event.state == "Stuck":
        status = "Stuck"

    elif event.state in ["Generating PSDs", "Productions running"]:
        psds_dict = {}
        prod_keys = [key for key in event.data.keys() if "Prod" in key[0:5]]
        for prod in event_prods:
            prod = prod.split("_")[0]
            if prod in event.data:
                cluster = event.data[prod]
                # if cluster.lower() == "finished": 
                #     status = "Finished"
                #     continue
                
                if cluster.lower() == "blocked":
                    status = "Blocked"
                    continue

                if cluster.lower() == "restart":
                    status = "Restarting"

                    psds_dict = get_psds_rundir(event.data['Prod0_rundir'])

                    try:
                        out = repo.build_dag("C01_offline", prod, psds_dict)
                        status = "DAG ready"
                    except ValueError as e:
                        status = "ini error"
                        print(e)

                    try: 
                        cluster = repo.submit_dag("C01_offline", prod)
                        job = condor.CondorJob(cluster)
                        event.data[prod] = cluster
                        event.data[f"{prod}_rundir"] = f"/home/daniel.williams/events/O3/o3a_catalog/{event.title}/C01_offline/"+job.run_directory
                        event.update_data()
                        event.state = "Productions running"
                    except ValueError as e:
                        status = "Submission error"
                        print(e)
                        cluster = None

                print(f"{prod}")
                if f"{gitlab.STATE_PREFIX}:{prod} finished" in event.labels or cluster.lower() == "finished":

                   if not event.data[f"{prod}"].lower() == "uploaded"  and not event.data[f"{prod}"].lower() == "manualupload":
                        # Upload the event data
                        try:
                            repo.upload_prod(prod, event.data[f"{prod}_rundir"])
                        except ValueError as e:
                            if "already in table" in str(e):
                                pass
                            else:
                                status = "Upload error"
                                continue
                        event.data[f"{prod}"] = "Uploaded"
                        event.update_data()
                        mattermost.send_message(f":mega: {event.title} {prod} has been uploaded. :robot:", "o3a-catalog-paper")
                        mattermost.send_message(f":mega: {event.title} {prod} has been uploaded. :robot:")

                try:
                    job = condor.CondorJob(event.data[prod])
                    status = job.status
                except ValueError:
                    # There seems to be a problem finding this job, let's mark it as stuck
                    
                    rundir = event.data[f"{prod}_rundir"]
                    if (event.data[f"{prod}"].lower() != "uploaded") and (event.data[f"{prod}"].lower() != "manualupload") and (len(glob.glob(f"{rundir}/posterior_samples/*.hdf5"))>0):

                        event.add_label(f"{prod} finished")
                        
                        event.data[f"{prod}"] = "Finished"
                        event.update_data()
                        continue
                    
                    elif event.data[f"{prod}"].lower() == "uploaded":
                        continue

                    elif event.data[f"{prod}"].lower() == "manualupload":
                        continue

                    else:
                        print(f"Problem with {event.title} production {prod}")
                        event.state = "Stuck"
                        event.add_note(f"An unknown error has been encountered with {prod}")
                        mattermost.send_message(f":mega: I've run into a problem with {event.title} {prod}. :robot:")

                        status = "Not running"
                        ifos = "Unknown"
                        continue
                except RuntimeError:
                    pass

                if status in ['Removed', 'Held', 'Submission error', 'Unexplained']:
                    event.state = "Stuck"

                #if prod == "Prod0":
                run_dir = event.data[f"{prod}_rundir"]
                prod0_run_dir = event.data[f"Prod0_rundir"]
                prod0_ini = RunConfiguration([ini for ini in event_prods if "Prod0" in ini][0])
                ifos = prod0_ini.get_ifos()
                psds = get_psds_rundir(prod0_run_dir)
                event_psds = set(ifos) - set(psds)
                #else:
                if (set(ifos)==set(psds)) and event.state != "Stuck":
                        event.state = "Productions running"
                else:
                        status = status + " waiting on PSDs {}".format(event_psds)
            
            else: # This production is not running at the moment
                if "Prod0" in event.data:
                    prod0_status = event.data["Prod0"].lower()
                    prod0_ini = RunConfiguration([ini for ini in event_prods if "Prod0" in ini][0])
                    ifos = prod0_ini.get_ifos()
                    prod0_run_dir = event.data[f"Prod0_rundir"]
                    psds = get_psds_rundir(prod0_run_dir)
                else:
                    prod0_status = None
                    ifos = ["L1"]
                    psds = []
                if (set(ifos) == set(psds)) or prod0_status:
                    psds_dict = get_psds_rundir(event.data['Prod0_rundir'])

                    try:
                        out = repo.build_dag("C01_offline", prod, psds_dict)
                        status = "DAG ready"
                    except ValueError as e:
                        status = "ini error"
                        print(e)

                    try: 
                        cluster = repo.submit_dag("C01_offline", prod)
                        job = condor.CondorJob(cluster)
                        event.data[prod] = cluster
                        event.data[f"{prod}_rundir"] = f"/home/daniel.williams/events/O3/o3a_catalog/{event.title}/C01_offline/"+job.run_directory
                        event.update_data()
                        event.state = "Productions running"
                    except ValueError as e:
                        status = "Submission error"
                        print(e)
                        cluster = None

                else:
                    status = "Not ready"
                    cluster = None
                    ifos = "Unknown"
                    psds = ""

            message += f"""| {event.title} | {event.state} | {cluster} | {prod} | {status} | \n"""
 

mattermost.submit_payload(message)
