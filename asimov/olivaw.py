#import ast
#import os, glob, datetime
import click


@click.command()
def main():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """

    from asimov import gitlab
    from asimov import config, config_locations
#    from asimov import condor, git
#    from asimov.ini import RunConfiguration
#    import otter
    print("Running olivaw")
    print(config_locations)
    print(config.get("gitlab", "token"))

    server = gitlab.gitlab.Gitlab('https://git.ligo.org',
                                  private_token=config.get("gitlab", "token"))
    repository = server.projects.get(config.get("olivaw", "tracking_repository"))

    events = gitlab.find_events(repository,
                                milestone=config.get("olivaw", "milestone"))


    for event in events:
        print(event.title)
        print("----------")
        print(event.event_object.meta)
        print("-----------")
        print(event.event_object.get_all_latest())
