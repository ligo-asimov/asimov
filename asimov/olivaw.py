import os
import sys
import collections
import json

from math import floor

import click

# Ignore warnings from the condor module
import warnings
warnings.filterwarnings("ignore", module="htcondor")

from asimov import logging
from asimov import current_ledger as ledger
from asimov import condor
import asimov.pipelines

# Replace this with a better logfile handling module please
#from glob import glob
import asimov

from git.exc import GitCommandError

# Import CLI bits from elsewhere
from asimov import cli
from asimov.cli import configuration
from asimov.cli import report
from asimov.cli import monitor
from asimov.cli import review
from asimov.cli import manage
from asimov.cli import event
from asimov.cli import project
from asimov.cli import production
from asimov.cli import application


@click.version_option(asimov.__version__)
@click.group()
@click.pass_context
def olivaw(ctx):
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """

    # Check that we're running in an actual asimov project
    if not os.path.exists("asimov.conf") and ctx.invoked_subcommand != "init":
        # This isn't the root of an asimov project, let's fail.
        click.secho("This isn't an asimov project", fg="white", bg="red")
        sys.exit(1)
    pass

# Project initialisation
olivaw.add_command(project.init)
olivaw.add_command(project.clone)

olivaw.add_command(event.event)

# Building and submission
olivaw.add_command(manage.manage)
# Reporting commands
olivaw.add_command(report.report)
# Configuration commands
olivaw.add_command(configuration.configuration)
# Monitoring commands
olivaw.add_command(monitor.monitor)
olivaw.add_command(event.event)
olivaw.add_command(production.production)
# Review commands
olivaw.add_command(review.review)
olivaw.add_command(application.apply)
