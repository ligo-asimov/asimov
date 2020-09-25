import click

from asimov import gitlab
from asimov import config, config_locations

@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
    click.echo("Running olivaw")

@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def ledger(event):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """
    
    server = gitlab.gitlab.Gitlab('https://git.ligo.org',
                                  private_token=config.get("gitlab", "token"))
    repository = server.projects.get(config.get("olivaw", "tracking_repository"))

    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    if event:
        events = [event_i for event_i in events if event_i.title == event]
    
    for event in events:
        click.echo(f"{event.title:30}")
        click.echo("-"*45)
        if len(event.event_object.meta['productions'])>0:
            click.echo(event.event_object.meta['productions'])
            click.echo("-"*45)
        if len(event.event_object.get_all_latest())>0:
            click.echo("Jobs waiting")
            click.echo("-"*45)
            click.echo(event.event_object.get_all_latest())
