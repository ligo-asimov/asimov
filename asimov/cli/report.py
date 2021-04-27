"""
Reporting functions
"""
import yaml
import glob
from datetime import datetime
import pytz
import os

import click

tz = pytz.timezone('Europe/London')


import otter
import otter.bootstrap as bt

from asimov.cli import connect_gitlab, known_pipelines
from asimov import gitlab
from asimov import config

@click.group()
def report():
    pass

@click.option("--location", "webdir", default=None, help="The place to save the report to")
@click.argument("event", default=None, required=False)
@report.command()
def html(event, webdir):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """
    server, repository = connect_gitlab()
    if not webdir:
        webdir = config.get("report", "report_root")
    click.echo("Getting events...")
    events = gitlab.find_events(repository,
                                milestone=config.get("olivaw", "milestone"),
                                subset=[event],
                                repo=False,
                                update=False)
    click.echo("Got events")
    if len(glob.glob("asimov.conf"))>0:
        config_file = "asimov.conf"
    else:
        config_file = None

    report = otter.Otter(f"{webdir}/index.html", 
                         author="Olivaw", 
                         title="Olivaw PE Report", 
                         author_email=config.get("report", "report_email"),
                         config_file=config_file)

    with report:
        navbar = bt.Navbar("Asimov", background="navbar-dark bg-primary")
        report + navbar

    with report:
        time = bt.Container()

        time + f"Report generated at {str(datetime.now(tz))}"
        report + time

    cards = []
    container = bt.Container()
    container + "# All PE Productions"
    for event in events:
        click.secho(event.title, bold=True)

        event_report =  otter.Otter(f"{webdir}/{event.title}.html", 
                         author="Olivaw", 
                         title=f"Olivaw PE Report | {event.title}", 
                         author_email="daniel.williams@ligo.org", 
                                    config_file=config_file)

        with event_report:
            navbar = bt.Navbar("Asimov", background="navbar-dark bg-primary")
            event_report + navbar

        card = bt.Card(title=f"<a href='{event.title}.html'>{event.title}</a>")

        toc = bt.Container()

        for production in event.productions:
            toc + f"* [{production.name}](#{production.name}) | {production.pipeline} |"# + bt.Badge({production.pipeline}, "info")

        with event_report:
            title_c = bt.Container()
            title_c + f"#{event.title}"
            event_report + title_c
            event_report + toc

        production_list = bt.ListGroup()
        for production in event.productions:
            click.echo(f"{event.title}\t{production.name}")
            if production.pipeline.lower() in known_pipelines:
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")

            event_log =  otter.Otter(f"{webdir}/{event.title}-{production.name}.html", 
                                     author="Olivaw", 
                                     title=f"Olivaw PE Report | {event.title} | {production.name}", 
                                     author_email="daniel.williams@ligo.org", 
                                     config_file=config_file)

            

            
            
            status_map = {"cancelled": "light",
                          "finished": "success",
                          "uploaded": "success",
                          "processing": "primary",
                          "running": "primary",
                          "stuck": "warning",
                          "restart": "secondary",
                          "ready": "secondary",
                          "wait": "light",
                          "stop": "danger",
                          "manual": "light",
                          "stopped": "light"}
            with event_report:
                container = bt.Container()
                container + f"## {production.name}"
                container + f"<a id='{production.name}'/>"
                container + "### Ledger"
                container + production.meta

            if production.pipeline.lower() == "bilby":
                container +f"### Progress"
                progress_line = []
                procs = pipe.check_progress()
                for proc, val in procs.items():
                    container + f"- {proc.split('_')[-1]}\t{val[0]}\t{val[1]}"
                    progress_line.append(f"{val[1]}")
            else:
                progress_line = []
            if production.status.lower() == "running":
                progress = str(bt.Badge("|".join(progress_line)))
            else:
                progress = ""

            if production.status.lower() == "uploaded":
                link = os.path.join("https://ldas-jobs.ligo.caltech.edu", config.get('general', 'webroot').replace("/home/", "~").replace("public_html/", ""), production.event.name, production.name,  "results", "home.html")
                item_text = f"<a href='{link}'>{production.name}</a>" 
            else:
                item_text = f"<a href='{event.title}.html#{production.name}'>{production.name}</a>" 
            production_list.add_item(item_text
                                     + str(bt.Badge(f"{production.pipeline}", "info")) 
                                     + progress
                                     + str(bt.Badge(f"{production.status}")), 
                                     context=status_map[production.status])

            # logs = pipe.collect_logs()
            # container + f"### Log files"
            # container + f"<a href='{event.title}-{production.name}.html'>Log file page</a>"
            # with event_log:

            #     for log, message in logs.items():
            #         log_card = bt.Card(title=f"{log}")
            #         log_card.add_content("<div class='card-body'><pre>"+message+"</pre></div>")
            #         event_log + log_card

            with event_report:
                event_report + container

        card.add_content(production_list)
        cards.append(card)



    with report:
        if len(cards) == 1:
            report + card
        else:
            for i, card in enumerate(cards):
                if i%2==0:
                    deck = bt.CardDeck()
                deck + card
                if i%2==1:
                    report + deck

@click.argument("event", default=None, required=False)
@report.command()
def status(event):
    """
    Provide a simple summary of the status of a given event.

    Arguments
    ---------
    name : str, optional
       The name of the event.

    """
    server, repository = connect_gitlab()

    events = gitlab.find_events(repository,
                                milestone=config.get("olivaw", "milestone"),
                                subset=[event],
                                update=False,
                                repo=False)
    for event in events:
        click.secho(f"{event.title:30}", bold=True)
        if len(event.event_object.meta['productions'])>0:
            click.secho("\tProductions", bold=True)
            for production in event.event_object.meta['productions']:
                click.echo(f"\t\t{list(production.keys())[0]}")
        if len(event.event_object.get_all_latest())>0:
            click.secho("\tJobs waiting", bold=True)
            waiting = event.event_object.get_all_latest()
            for awaiting in waiting:
                click.echo(f"\t\t{awaiting.name}\t{awaiting.status}")

@click.option("--yaml", "yaml_f", default=None, help="A YAML file to save the ledger to.")
@click.argument("event", default=None, required=False)
@report.command()
def ledger(event, yaml_f):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """

    server, repository = connect_gitlab()

    events = gitlab.find_events(repository,
                                milestone=config.get("olivaw", "milestone"),
                                subset=[event],
                                update=False,
                                repo=False)

    total = []
    for event in events:
        total.append(yaml.safe_load(event.event_object.to_yaml()))

    click.echo(yaml.dump(total))

    if yaml_f:
        with open(yaml_f, "w") as f:
            f.write(yaml.dump(total))
