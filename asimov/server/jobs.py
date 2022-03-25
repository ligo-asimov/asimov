"""
Job endpoints
=============

This module provides endpoints for interaction with job schedulers and individual analysis jobs.

"""

from flask import Blueprint, request, jsonify, make_response
import asimov
from asimov.condor import CondorJobList

bp = Blueprint("asimov", __name__, url_prefix="jobs")

@bp.route("/", methods=['GET'])
def job_list():
    """
    Get the list of all running jobs for this user.

    Example
    -------

    .. http:example:: curl wget python-requests

       GET /jobs/ HTTP/1.1
       Content-Type: application/json


       HTTP/1.1 200 OK
       Content-Type: application/json

       "asimov"

    """

    return make_response(jsonify(CondorJobList()), 200)
