import click
from asimov import config

@click.group()
def configuration():
    """Group for all of the configuration-related command line stuff."""
    pass

@configuration.command()
def show():
    """Show all configuration values"""
    for section, values in config._sections.items():
        click.echo(click.style(section, fg='black', bg='white'))
        for key, value in values.items():
            click.secho(f"\t{key:30}\t{value}", bold=False)
