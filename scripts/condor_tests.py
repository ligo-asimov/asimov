from asimov import config
from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov.condor import CondorJobList, CondorJob
import yaml

# server, repository = connect_gitlab()
# events = gitlab.find_events(repository,
#                             #milestone=config.get("olivaw", "milestone"),
#                             subset=["GW200115A"],
#                             update=False,
#                             repo=True)

ledger = "/home/pe.o3/public_html/LVC/o3a-final/ledger.yaml"
with open(ledger, "r") as filehandle:
    events = yaml.safe_load(filehandle.read())


jobs = CondorJobList()

#for job in jobs.jobs.values():
#    print(job)

for event in events:
    productions = {}
    for prod in event['productions']:
        productions.update(prod)

    for name, production in productions.items():
        if production['status'] == "running":
            print(event['name'], name)
            if not "job id" in production:
                print("Job ID is missing")
                continue
            if production['job id'] in jobs.jobs:
                print(jobs.jobs[production['job id']])
            else:
                print("\t Job is not running")

#     on_deck = [production
#                for production in event.productions
#                if production.status.lower() in ACTIVE_STATES]
#     for production in on_deck:
#         print(production.name)
#         print(production.meta['job id'] in jobs.jobs.keys())


