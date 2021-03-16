import os
import collections
import json

from math import floor

import click

from datetime import datetime
import pytz

tz = pytz.timezone('Europe/London')

import numpy as np

#from asimov import gitlab
from asimov.event import Event, DescriptionException, Production
#from asimov import config
from asimov import logging
from asimov.pipeline import PipelineException
from asimov import condor
import asimov.pipelines

# Replace this with a better logfile handling module please
from glob import glob


from git.exc import GitCommandError

# Import CLI bits from elsewhere
from asimov import cli
from asimov.cli import configuration
from asimov.cli import report
from asimov.cli import monitor
from asimov.cli import review

state_vector_channel = {"L1": "L1:DCS-CALIB_STATE_VECTOR_C01",
                        "H1": "H1:DCS-CALIB_STATE_VECTOR_C01",
                        "V1": "V1:DQ_ANALYSIS_STATE_VECTOR"}


@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
    global rundir
    rundir = os.getcwd()


# Reporting commands
olivaw.add_command(report.report)
# Configuration commands
olivaw.add_command(configuration.configuration)
# Monitoring commands
olivaw.add_command(monitor.monitor)
# Review commands
olivaw.add_command(review.review)
