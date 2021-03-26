"""
Project management tools.
"""

import os

import click

from asimov import config
from asimov import storage
from asimov import ledger

@click.command()
@click.argument("name")
@click.option("--root", default=os.getcwd(),
              help="Location to create the project, default is the current directory.")
@click.option("--working", default="working",
              help="The location to store working directories, default is a directory called 'working' inside the current directory.")
@click.option("--checkouts", default="checkouts",
              help="The location to store cloned git repositories.")
@click.option("--results", default="results",
              help="The location where the results store should be created.")
def init(name, root, working="working", checkouts="checkouts", results="results"):
    """
    Roll-out a new project.
    """
    import venv
    import pathlib

    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    os.chdir(root)

    config.set("project", "name", name)
    config.set("project", "root", root)
    

    project_name = name

    ## Make the virtual environment
    builder = venv.EnvBuilder(system_site_packages=False,
                              clear=False,
                              symlinks=False,
                              upgrade=False,
                              with_pip=True,
                              prompt=f"Asimov {project_name}")

    builder.create("environment")

    config.set("general", "environment", "environment")

    ## Make the working directory
    pathlib.Path(working).mkdir(parents=True, exist_ok=True)
    config.set("general", "rundir_default", working)

    ## Make the git directory
    pathlib.Path(checkouts).mkdir(parents=True, exist_ok=True)
    config.set("general", "git_default", checkouts)

    ## Make the results store
    storage.Store.create(root=results, name=f"{project_name} storage")
    config.set("storage", "root", results)

    ## Make the ledger
    ledger.Ledger.create()
    config.set("ledger", "engine", "yamlfile")
    config.set("ledger", "location", "ledger.yaml")

    with open("asimov.conf", "w") as config_file:
        config.write(config_file)
