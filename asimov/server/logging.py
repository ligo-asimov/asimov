"""
Logging endpoints
=================


Blueprints for the logging interface.
"""
import datetime

from flask import Blueprint, jsonify, make_response


from flask import Flask
from flask import request

# from asimov.server import database
from asimov import logger

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


       HTTP/1.1 201 OK
       Content-Type: application/json
    
       {}
    """
    if request.is_json:
        req = request.get_json()

    entry = logger.log(pipeline=req['pipeline'],
                       module=req['module'],
                       level=req['level'],
                       time=datetime.datetime.now(),
                       event=req['event'],
                       production=req['production'],
                       message=req['message']
                       )
    return make_response({}, 201)


@bp.route("/", methods=["GET"])
def list_logging_events():
    """List all of the log events which match filters given as GET arguments

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /log HTTP/1.1
       Content-Type: application/json
       
       :query pipeline: RIFT

       
       HTTP/1.1 200 OK
       Content-Type: application/json

       [
         {
           "level": "debug", 
           "message": "Looking-up logs with filterings", 
           "module": "asimov"
         }, 
         {
           "level": "debug", 
           "message": "Looking-up logs with filterings", 
           "module": "asimov"
         }, 
         {
           "level": "debug", 
           "message": "Looking-up logs with filterings", 
           "module": "asimov"
         }
       ]
    """
    filters = request.args
    logger.log(level="debug", message=f"Looking-up logs with filterings: {filters}")
    events = logger.list(**filters)
    return make_response(jsonify([event.__dictrepr__() for event in events]), 200)
