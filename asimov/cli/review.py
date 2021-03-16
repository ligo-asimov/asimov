@click.option("--event", "event", default=None, help="The event which will be updated")
def audit(event):
    """
    Conduct an audit of the contents of production ini files against
    the production ledger.

    Parameters
    ----------
    event : str, optional
       The event to be checked. 
       Optional; if the event isn't provided all events will be audited.
    """

    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)

    for production in gitlab_event[0].productions:
        pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")

        click.echo(pipe.read_ini())
        
