import ast

from supervisor import gitlab, mattermost
from supervisor import config
from supervisor import condor

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

uber_repository = "/home/daniel.williams/events/O3/o3a_catalog_events"

events = gitlab.find_events(repository)

mattermost = mattermost.Mattermost()

message = """# Run updates\n"""
message += """| Event | IFOS | Cluster | Production | Status | PSDs |\n"""
message += """|---|---|---|---|---|---|\n"""

for event in events:

    prod_keys = [key for key in event.data.keys() if "Prod" in key[0:5]]

    print(event.title)
    print(event.state)
    
    for prod in prod_keys:
 
        print(event.data[prod])
        cluster = event.data[prod]
        try:
            job = condor.CondorJob(event.data[prod])
            status = job.status

            if prod == "Prod0":
                for det, psd in get_psds(job):
                    psds += f"{det}"
                try:
                    ifos = job.get_config().get("analysis", "ifos")
                except:
                    ifos = "Error" 

        except ValueError:
            status = "Not running"
            ifos = "Unknown"

        message += f"""| {event.title} | {ifos} | {cluster} | {prod} | {status} | {psds} | \n"""
 

mattermost.submit_payload(message)
