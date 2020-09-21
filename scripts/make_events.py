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
