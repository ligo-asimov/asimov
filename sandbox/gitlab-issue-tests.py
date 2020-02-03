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
    if "Prod0" in event.data:
        print(event.title)
        print(event.state)
        print(event.data['Prod0'])
        cluster = event.data['Prod0']
        try:
            job = condor.CondorJob(event.data['Prod0'])
            status = job.status

            for det, psd in get_psds(job):
                psds += f"{det}"
            try:
                ifos = job.get_config().get("analysis", "ifos")
            except KeyError:
                ifos = "Error"
        
        
            

        except ValueError:
            status = "Not running"
            ifos = "Unknown"

        message += f"""| {event.title} | {ifos} | {cluster} | Prod0 | {status} | {psds} | \n"""

    elif "Prod1" in event.data:
        print(event.title)
        print(event.state)
        print(event.data['Prod1'])
        cluster = event.data['Prod1']
        try:
            job = condor.CondorJob(event.data['Prod1'])
            status = job.status

        except ValueError:
            status = "Not running"

        message += f"""| {event.title} | |  {cluster} | Prod1 | {status} |\n"""        

mattermost.submit_payload(message)
