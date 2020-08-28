import ast
import os, glob, datetime
import click

@click.command()
def main():
    """

    """

    from asimov import gitlab
    from asimov import config
    from asimov import condor, git
    from asimov.ini import RunConfiguration


    import otter

    print("Running olivaw")

    server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
    repository = server.projects.get(config.get("olivaw", "tracking_repository"))

    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    for event in events:
        print(event.title)
        print ("----------")
        print(event.meta)
        print("-----------")
        print(event.get_all_latest())
