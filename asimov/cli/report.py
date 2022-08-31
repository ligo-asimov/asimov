"""
Reporting functions
"""
from datetime import datetime

import click
import pytz
import yaml
from pkg_resources import resource_filename

import otter
import otter.bootstrap as bt

from asimov import current_ledger
from asimov.cli import known_pipelines
from asimov import config

@click.group()
def report():
    """Produce reports about the state of the project."""
    pass


@click.option(
    "--location", "webdir", default=None, help="The place to save the report to"
)
@click.argument("event", default=None, required=False)
@report.command()
def html(event, webdir):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """

    events = current_ledger.get_event(event)

    if not webdir:
        webdir = config.get("general", "webroot")

    report = otter.Otter(f"{webdir}/index.html", 
                         author="Olivaw", 
                         title="Olivaw PE Report", 
                         #author_email=config.get("report", "report_email"),
                         #config_file=config_file
    )
    with report:

        style = """
<style>
        .review-deprecated, .status-cancelled, .review-rejected {
        display: none;
        }

        .event-data {
        margin-bottom: 2rem;
        }

        .asimov-sidebar {
        position: sticky;
        top: 4rem;
        height: calc(100vh - 4rem);
        overflow-y: auto;
        }
</style>
        """
        report + style

        style = """
<style>
        body {
        background-color: #f2f2f2;
        }

        .review-deprecated, .status-cancelled, .review-rejected {
        display: none;
        }

        .event-data {
        margin: 1rem;
        margin-bottom: 2rem;
        }

        .asimov-sidebar {
        position: sticky;
        top: 4rem;
        height: calc(100vh - 4rem);
        overflow-y: auto;
        }

        .asimov-analysis {
        padding: 1rem;
        background: lavenderblush;
        margin: 0.5rem;
        border-radius: 0.5rem;
        }

        .asimov-analysis-running, .asimov-analysis-processing {
        background: #DEEEFF;
        }

        .asimov-analysis-finished, .asimov-analysis-uploaded {
        background: #E1EDE4;
        }
        .asimov-analysis-stuck {
        background: #FFF5D9;
        }

        .asimov-status {
        float: right;
        clear: both;
        }
</style>
        """
        report + style

        script = """
<script type="text/javascript">
    window.onload = setupRefresh;

    function setupRefresh() {
      setTimeout("refreshPage();", 1000*60*15); // milliseconds
    }
    function refreshPage() {
       window.location = location.href;
    }
</script>
        """
        report + script
    with report:
        navbar = bt.Navbar(
            f"Asimov  |  {current_ledger.data['project']['name']}",
            background="navbar-dark bg-primary",
        )
        report + navbar

    events = sorted(events, key=lambda a: a.name)
    cards = "<div class='container-fluid'><div class='row'><div class='col-12 col-md-3 col-xl-2  asimov-sidebar'>"

        time + f"Report generated at {str(datetime.now(tz))}"
        report + time
    events = sorted(events, key = lambda a: a.name)
    cards = "<div class='container-fluid'><div class='row'><div class='col-12 col-md-3 col-xl-2  asimov-sidebar'>"
    
    toc = """<nav><ul class="list-unstyled">"""
    for event in events:
        toc += f"""<li><a href="#card-{event.name}">{event.name}</a></li>"""
        
    toc += "</ul></nav>"

    cards += toc
    cards += """</div><div class='events col-md-9 col-xl-10' data-isotope='{ "itemSelector": ".production-item", "layoutMode": "fitRows" }'>"""
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

    review_map = {"deprecated": "warning",
                  "none": "default",
                  "approved": "success",
                  "rejected": "danger",
                  "checked": "info"
                  }


    for event in events:
        # This is a quick test to try and improve readability


        card = f"""
<div class="card event-data" id="card-{event.name}">
<div class="card-body">
<h3 class="card-title">{event.name}</h3>
"""

        prods = {}
        for prod in event.productions:
            prods[prod.name] = prod

        card += """<div class="list-group">"""



        for production_name, production in prods.items():

            card += production.html()
            
        card += """</div>"""
        
        # card += """<p class="card-text">Card text</p>""" # 
        card += """
</div>
</div>"""
        cards += card

    cards += "</div></div>"
    with report:
        report + cards


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
    for event in current_ledger.get_event(event):
        click.secho(f"{event.name:30}", bold=True)
        if len(event.productions)>0:
            click.secho("\tProductions", bold=True)
            for production in event.productions:
                click.echo(f"\t- {production.name} " + click.style(f"{production.pipeline}") + " " + click.style(f"{production.status}"))
        if len(event.get_all_latest())>0:
            click.secho("\tProductions waiting: ", bold=True, nl=False)
            waiting = event.get_all_latest()
            for awaiting in waiting:
                click.echo(f"{awaiting.name} ", nl=False)
            click.echo("")

@click.option(
    "--yaml", "yaml_f", default=None, help="A YAML file to save the ledger to."
)
@click.argument("event", default=None, required=False)
@report.command()
def ledger(event, yaml_f):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """
    total = []
    for event in current_ledger.get_event(event):
        total.append(yaml.safe_load(event.to_yaml()))

    click.echo(yaml.dump(total))

    if yaml_f:
        with open(yaml_f, "w") as f:
            f.write(yaml.dump(total))
