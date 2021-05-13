import click

from asimov.cli import connect_gitlab, ACTIVE_STATES, known_pipelines
from asimov import gitlab
from asimov import config
from asimov import logging
from asimov import condor

@click.argument("event", default=None, required=False)
@click.option("--update", "update", default=False,
              help="Force the git repos to be pulled before submission occurs.")
@click.option("--dry-run", "-n", "dry_run", is_flag=True)
@click.command()
def monitor(event, update, dry_run):
    """
    Monitor condor jobs' status, and collect logging information.
    """
    server, repository = connect_gitlab()
    events = gitlab.find_events(repository,
                                milestone=config.get("olivaw", "milestone"),
                                subset=[event],
                                update=update,
                                repo=True)
    
    for event in events:
        stuck = 0
        running = 0
        ready = 0
        finish = 0
        click.secho(f"{event.title}", bold=True)
        on_deck = [production
                   for production in event.productions
                   if production.status.lower() in ACTIVE_STATES]
        for production in on_deck:

            click.secho(f"\t{production.name}", bold=True)

            if not dry_run:
                logger = logging.AsimovLogger(event=event.event_object)
            else:
                logger = None
                
            # Deal with jobs which need to be stopped first
            if production.status.lower() == "stop":
                pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
                if not dry_run:
                    pipe.eject_job()
                    production.status = "stopped"
                    click.echo(f"\t\t{production.name} stopped")
                else:
                    click.echo("\t\t{production.name} --> stopped")
                continue

            # Get the condor jobs
            try:
                if "job id" in production.meta:
                    if not dry_run:
                        job = condor.CondorJob(production.meta['job id'])
                    else:
                        click.echo(f"\t\tRunning under condor")
                else:
                    raise ValueError # Pass to the exception handler

                if not dry_run:
                    if job.status.lower() == "running":
                        pass

                    if job.status.lower() == "processing":
                        pass

                    if event.state == "running" and job.status.lower() == "stuck":
                        click.echo("\t\tJob is stuck on condor")
                        event.state = "stuck"
                        production.status = "stuck"
                        stuck += 1
                        production.meta['stage'] = 'production'
                    elif event.state == "processing" and job.status.lower() == "stuck":
                        click.echo("\t\tPost-processing is stuck on condor")
                        production.status = "stuck"
                        stuck += 1
                        production.meta['stage'] = "post"
                    else:
                        running += 1

            except ValueError as e:
                click.echo(e)
                click.echo(f"\t\t{production.name}\t{production.status.lower()}")
                if production.pipeline.lower() in known_pipelines:
                    click.echo("Investigating...")
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")

                    if production.status.lower() == "stop":
                        pipe.eject_job()
                        production.status = "stopped"

                    elif production.status.lower() == "finished":
                        click.echo("Finished")
                        pipe.after_completion()

                    elif production.status.lower() == "processing":
                    # Need to check the upload has completed
                        try:
                            pipe.after_processing()
                        except ValueError as e:
                            click.echo(e)
                            #production.status = "stuck"
                            #stuck += 1
                            production.meta['stage'] = "after processing"

                    elif pipe.detect_completion() and production.status.lower() == "running":
                        # The job has been completed, collect its assets
                        production.meta['job id'] = None
                        finish += 1
                        production.status = "finished"
                        pipe.after_completion()

                    else:
                        # It looks like the job has been evicted from the cluster
                        click.echo(f"Attempting to rescue {production.name}")
                        #event.state = "stuck"
                        #production.status = "stuck"
                        #production.meta['stage'] = 'production'
                        try:
                            pipe.resurrect()
                        except:
                            production.status = "stuck"
                            production.meta['error'] = "resurrection error"

                if production.status == "stuck":
                    event.state = "stuck"
                production.event.issue_object.update_data()

            if (running > 0) and (stuck == 0):
                event.state = "running"
            elif (stuck == 0) and (running == 0) and (finish > 0):
                event.state = "finished"
