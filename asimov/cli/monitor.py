import shutil
import configparser
import sys
import click

from asimov.cli import ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov import config
from asimov import current_ledger as ledger
from asimov import logger
from asimov import condor

@click.argument("event", default=None, required=False)
@click.option(
    "--update",
    "update",
    default=False,
    help="Force the git repos to be pulled before submission occurs.",
)
@click.option("--dry-run", "-n", "dry_run", is_flag=True)
@click.option(
    "--chain",
    "-c",
    "chain",
    default=False,
    is_flag=True,
    help="Chain multiple asimov commands",
)
@click.command()
@click.pass_context
def monitor(ctx, event, update, dry_run, chain):
    """
    Monitor condor jobs' status, and collect logging information.
    """
    for event in ledger.get_event(event):
        stuck = 0
        running = 0
        finish = 0
        click.secho(f"{event.name}", bold=True)
        on_deck = [production
                   for production in event.productions
                   if production.status.lower() in ACTIVE_STATES]
        for production in on_deck:

            click.echo(f"\t- " + click.style(f"{production.name}", bold=True) + click.style(f"[{production.pipeline}]", fg = "green"))

            # Jobs marked as ready can just be ignored as they've not been stood-up
            if production.status.lower() == "ready":
                click.secho(f"  \t  ● {production.status.lower()}", fg="green")
                continue
            
            # Deal with jobs which need to be stopped first
            if production.status.lower() == "stop":
                pipe = production.pipeline(production, "C01_offline")
                if not dry_run:
                    pipe.eject_job()
                    production.status = "stopped"
                    click.secho(f"  \tStopped", fg="red")
                else:
                    click.echo("\t\t{production.name} --> stopped")
                continue

            # Get the condor jobs
            try:
                if "job id" in production.meta:
                    if not dry_run:
                        if production.meta["job id"] in job_list.jobs:
                            job = job_list.jobs[production.meta["job id"]]
                        else:
                            job = None
                    else:
                        logger.debug(
                            f"Running analysis: {event}/{production.name}, cluster {production.meta['job id']}"
                        )
                        click.echo("\t\tRunning under condor")
                else:
                    raise ValueError  # Pass to the exception handler

                if not dry_run:
                    if job.status.lower() == "running":
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.status.lower()} is running (condor id: {production.meta['job id']})")
                    elif job.status.lower() == "processing":
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.status.lower()} is postprocessing (condor id: {production.meta['job id']})")
                    elif job.status.lower() == "stuck":
                        click.echo(f"  \t  " + click.style("●", "orange") + f" {production.status.lower()} is stuck on the scheduler (condor id: {production.meta['job id']})")
                        production.status = "stuck"
                        stuck += 1
                    else:
                        running += 1

            except ValueError as e:
                click.echo(e)
                click.echo(f"\t\t{production.status.lower()}")
                if production.pipeline:
                    #click.echo("Investigating...")
                    pipe = production.pipeline

                    if production.status.lower() == "stop":
                        pipe.eject_job()
                        production.status = "stopped"
                        click.echo(f"  \t  " + click.style("●", "red") + f" {production.status.lower()} has been stopped")
                    elif production.status.lower() == "finished":
                        pipe.after_completion()
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.status.lower()} has finished and post-processing has been started")
                    elif production.status.lower() == "processing":
                        # Need to check the upload has completed
                        if pipe.detect_completion_processing():
                            try:
                                pipe.after_processing()
                                click.echo(
                                    "  \t  "
                                    + click.style("●", "green")
                                    + f" {production.name} has been finalised and stored"
                                )
                            except ValueError as e:
                                click.echo(e)
                        else:
                            click.echo(
                                "  \t  "
                                + click.style("●", "green")
                                + f" {production.name} has finished and post-processing"
                                + f" is stuck ({production.meta['job id']})"
                            )
                            production.meta["postprocessing"]["status"] = "stuck"
                    elif (
                        pipe.detect_completion()
                        and production.status.lower() == "processing"
                    ):
                        click.echo(
                            "  \t  "
                            + click.style("●", "green")
                            + f" {production.name} has finished and post-processing is running"
                        )
                    elif (
                        pipe.detect_completion()
                        and production.status.lower() == "running"
                    ):
                        # The job has been completed, collect its assets
                        if "profiling" not in production.meta:
                            production.meta["profiling"] = {}
                        try:
                            production.meta["profiling"] = condor.collect_history(
                                production.meta["job id"]
                            )
                            production.meta["job id"] = None
                        except ValueError as e:
                            click.echo(e)
                            production.meta['stage'] = "after processing"

                        finish += 1
                        production.status = "finished"
                        pipe.after_completion()
                        click.secho(f"  \t  ● {production.status.lower()} - Completion detected", fg="green")
                    else:
                        # It looks like the job has been evicted from the cluster
                        click.echo(f"  \t  " + click.style("●", "orange") + f" {production.status.lower()} is stuck; attempting a rescue")
                        try:
                            pipe.resurrect()
                        except Exception:  # Sorry, but there are many ways the above command can fail
                            production.status = "stuck"
                            click.echo(f"  \t  " + click.style("●", "red") + f" {production.status.lower()} is stuck; automatic rescue was not possible")

                if production.status == "stuck":
                    click.echo(f"  \t  " + click.style("●", "orange") + f" {production.status.lower()} is stuck")
                    
                ledger.update_event(event)
