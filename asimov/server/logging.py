"""
Logging endpoints
=================


Blueprints for the logging interface.
"""
import datetime

from flask import Blueprint, jsonify, make_response


from flask import Flask
from flask import request

from asimov.server import database

bp = Blueprint("logging", __name__, url_prefix="/log")


@bp.route("/", methods=["POST"])
def add_logging_event():
    """Add a new logging event to the database

    Examples
    --------

    .. http:example:: curl wget python-requests

       POST /log HTTP/1.1
       Content-Type: application/json

       {
         "event":"GW150914",
         "level":"update",
         "message":"This is a test message.",
         "module":"sampling",
         "pipeline":"pycbc",
         "production":"ProdX10"
       }

    """
    if request.is_json:
        req = request.get_json()

    entry = database.Logger(pipeline=req['pipeline'],
                            module=req['module'],
                            level=req['level'],
                            time=datetime.datetime.now(),
                            event=req['event'],
                            production=req['production'],
                            message=req['message']
                            )
    entry.save()
    return make_response({}, 200)


@bp.route("/", methods=["GET"])
def list_logging_events():
    """List all of the log events which match filters given as GET arguments

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /log HTTP/1.1
       Content-Type: application/json

       :query pipeline: RIFT
    """
    filters = request.args
    events = database.Logger.list(**filters)
    return make_response(jsonify([event.__dictrepr__() for event in events]), 200)
