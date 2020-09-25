"""
Make the event issues on the gitlab issue tracker from gracedb.
"""


import asimov
from asimov.event import Event
from asimov import config

from asimov import gitlab
from asimov import config

from ligo.gracedb.rest import GraceDb, HTTPError 
client = GraceDb(service_url=config.get("gracedb", "url"))
r = client.ping()

superevent_iterator = client.superevents('O3B_CBC_CATALOG')
superevent_ids = [superevent['superevent_id'] for superevent in superevent_iterator]

server = gitlab.gitlab.Gitlab(config.get("gitlab", "url"), private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))


gitlab_events = gitlab.find_events(repository)

super_events = set(superevent_ids) - {event.title for event in gitlab_events}

# Add the new events
for superevent in list(super_events):

    data = client.superevent(superevent).json()
    event_data = client.event(data['preferred_event']).json()
    
    event_url = f"https://catalog-dev.ligo.org/events/{data['preferred_event']}/view/"
    
    event = Event(name=superevent,
                  repository=f"git@git.ligo.org:pe/O3/{superevent}",
                  gid=data['preferred_event'],
                  gid_url=event_url,
                  calibration = {},
                  interferometers=event_data['instruments'].split(","),
                  disable_repo=True
    )
    gitlab.EventIssue.create_issue(repository, event, issue_template="scripts/outline.md")


def find_calibrations(time):
    with open("../scripts/LLO_calibs.txt") as llo_file:
        data_llo = llo_file.read().split("\n")
        data_llo = [datum for datum in data_llo if datum[-16:]=="FinalResults.txt"]
        times_llo = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_llo}
    
    with open("../scripts/LHO_calibs.txt") as llo_file:
        data_lho = llo_file.read().split("\n")
        data_lho = [datum for datum in data_lho if datum[-16:]=="FinalResults.txt"]
        times_lho = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_lho}
        
    keys_llo = np.array(list(times_llo.keys())) 
    keys_lho = np.array(list(times_lho.keys())) 
    return {"LHO": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]], "LLO": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]]}

    
# Update existing events
for event in gitlab_events:
    data = client.superevent(event.title).json()
    event_data = client.event(data['preferred_event']).json()

    print(event_data['gpstime'])
    
    event.event_object.meta['event time'] = event_data['gpstime']
    event.update_data()
