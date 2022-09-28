import shutil

import click

from asimov.cli import ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov import config
from asimov import current_ledger as ledger
from asimov import logger
from asimov import condor

from asimov.cli import manage
from asimov.cli import report

@click.option("--dry-run", "-n", "dry_run", is_flag=True)
@click.command()
def start(dry_run):
    """Set up a cron job on condor to monitor the project."""

    submit_description = {
          "executable": shutil.which("asimov"),  
          "arguments": "monitor --chain",
          "accounting_group": config.get("pipelines", "accounting"),
          "output": f"asimov_cron.out",
          "on_exit_remove": "false",
          "error": f"asimov_cron.err",
          "log": f"asimov_cron.log",
          "request_cpus": "1",
          "cron_minute": "*/15",
          "getenv": "true",
          "batch_name": f"asimov/monitor/{ledger.data['project']['name']}",
          "request_memory": "8192MB",
          "request_disk": "8192MB",
    }
    cluster = condor.submit_job(submit_description)
    ledger.data['cronjob'] = cluster
    ledger.save()
    click.secho(f"  \t  ● Asimov is running ({cluster})", fg="green")
    
@click.option("--dry-run", "-n", "dry_run", is_flag=True)
@click.command()
def stop(dry_run):
    """Set up a cron job on condor to monitor the project."""
    cluster = ledger.data['cronjob']
    condor.delete_job(cluster)
    click.secho(f"  \t  ● Asimov has been stopped", fg="red")
    
@click.argument("event", default=None, required=False)
@click.option("--update", "update", default=False,
              help="Force the git repos to be pulled before submission occurs.")
@click.option("--dry-run", "-n", "dry_run", is_flag=True)
@click.option("--chain", "-c", "chain", default=False,
              is_flag=True,
              help="Chain multiple asimov commands")
@click.command()
@click.pass_context
def monitor(ctx, event, update, dry_run, chain):
    """
    Monitor condor jobs' status, and collect logging information.
    """

    if chain:
        ctx.invoke(manage.build, event=event)
        ctx.invoke(manage.submit, event=event)
    
    # First pull the condor job listing
    job_list = condor.CondorJobList()
    
    for event in ledger.get_event(event):
        stuck = 0
        running = 0
        ready = 0
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
                pipe = production.pipeline
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
                        if production.meta['job id'] in job_list.jobs:
                            job = job_list.jobs[production.meta['job id']]
                        else:
                            job = None
                    else:
                        click.echo(f"\t\tRunning under condor")
                else:
                    raise ValueError # Pass to the exception handler

                if not dry_run:
                    if job.status.lower() == "running" and production.status == "processing":
                        click.echo(f"  \t  " + click.style("●", "green") + f" Postprocessing for {production.name} is running (condor id: {production.meta['job id']})")
                    elif job.status.lower() == "running":
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} is running (condor id: {production.meta['job id']})")
                        if not "profiling" in production.meta: production.meta['profiling'] = {}
                        #production.meta['profiling'] = job.get_data()['WallClockCheckpoint']
                        production.status = "running"
                    elif job.status.lower() == "completed":
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} has completed")
                    #elif job.status.lower() == "processing":
                    #    click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} is postprocessing (condor id: {production.meta['job id']})")
                    elif job.status.lower() == "held":
                        click.echo(f"  \t  " + click.style("●", "yellow") + f" {production.name} is held on the scheduler (condor id: {production.meta['job id']})")
                        production.status = "stuck"
                        stuck += 1
                    else:
                        running += 1

            except (ValueError, AttributeError) as e:
                if production.pipeline:
                    
                    pipe = production.pipeline

                    if production.status.lower() == "stop":
                        pipe.eject_job()
                        production.status = "stopped"
                        click.echo(f"  \t  " + click.style("●", "red") + f" {production.name} has been stopped")
                        job_list.refresh()                        
                    elif production.status.lower() == "finished":
                        pipe.after_completion()
                        click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} has finished and post-processing has been started")
                        job_list.refresh()
                    elif production.status.lower() == "processing":
                    # Need to check the upload has completed
                        if pipe.detect_completion_processing():
                            try:
                                pipe.after_processing()
                                click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} has been finalised and stored")
                            except ValueError as e:
                                click.echo(e)
                        else:
                            click.echo(f"  \t  " + click.style("●", "green") + f" {production.name} has finished and post-processing is running")
                    elif pipe.detect_completion() and production.status.lower() == "running":
                        # The job has been completed, collect its assets
                        if not "profiling" in production.meta: production.meta['profiling'] = {}
                        try:
                            production.meta['profiling'] = condor.collect_history(production.meta['job id'])
                            production.meta['job id'] = None
                        except condor.htcondor.HTCondorIOError:
                            #self.logger.error("Could not collect condor profiling data.")
                            pass

                        finish += 1
                        production.status = "finished"
                        pipe.after_completion()
                        click.secho(f"  \t  ● {production.name} - Completion detected", fg="green")
                        job_list.refresh()
                    else:
                        # It looks like the job has been evicted from the cluster
                        click.echo(f"  \t  " + click.style("●", "yellow") + f" {production.name} is stuck; attempting a rescue")
                        try:
                            pipe.resurrect()
                        except:
                            production.status = "stuck"
                            click.echo(f"  \t  " + click.style("●", "red") + f" {production.name} is stuck; automatic rescue was not possible")

                if production.status == "stuck":
                    click.echo(f"  \t  " + click.style("●", "yellow") + f" {production.name} is stuck")
                    
            ledger.update_event(event)

            if chain:
                ctx.invoke(report.html)
