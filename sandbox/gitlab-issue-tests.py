import ast

from supervisor import gitlab, mattermost
from supervisor import config
from supervisor import condor, git

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(3816)

def get_psds(job):
    config = job.get_config()
    dets = ast.literal_eval(config.get("analysis", "ifos"))
    psds = {}
    for det in dets:
        asset = f"ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
        psds[det] = job.get_asset(asset)
    return psds

uber_repository = git.MetaRepository("/home/daniel.williams/events/O3/o3a_catalog_events")

events = gitlab.find_events(repository)

mattermost = mattermost.Mattermost()

message = """# Run updates\n"""
message += """| Event | IFOS | Cluster | Production | Status | PSDs |\n"""
message += """|---|---|---|---|---|---|\n"""



for event in events:

    repo = uber_repository.get_repo(event)
    event_prods = repo.get_prods("C01_offline")
    
    prod_keys = [key for key in event.data.keys() if "Prod" in key[0:5]]
    for prod in event_prods:
        if prod in event.data:
            cluster = event.data[prod]
            try:
                job = condor.CondorJob(event.data[prod])
                status = job.status

                if prod == "Prod0":
                    psds = ""
                    for det, psd in get_psds(job):
                        psds += f"{det}"
                    try:
                        ifos = job.get_config().get("analysis", "ifos")
                    except:
                        ifos = "Error" 

            except:
                status = "Not running"
                ifos = "Unknown"
        else:
            status = "Not ready"
            ifos = "Unknown"
            psds = ""

        message += f"""| {event.title} | {event.state} | {ifos} | {cluster} | {prod} | {status} | {psds} | \n"""
 

mattermost.submit_payload(message)
