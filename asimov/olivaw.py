import os
import collections
import json

from math import floor

import click

from asimov import logging
from asimov import condor
import asimov.pipelines

# Replace this with a better logfile handling module please
#from glob import glob


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

@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
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
