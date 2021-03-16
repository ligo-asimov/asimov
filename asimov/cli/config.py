import click

@click.group()
def configuration():
    """Group for all of the configuration-related command line stuff."""
    pass

@config.command()
def ls():
    pass
