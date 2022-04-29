"""
Endpoints for monitoring asimov jobs.

Asimov exposes a number of end-point which can be used to
get a rapid overview of the run status of a set of analyses
it is managing.
"""
from flask import Blueprint, request, jsonify, make_response, json
from asimov import ledger

monitor_bp = Blueprint("monitor", __name__, url_prefix="/monitor")

@monitor_bp.route("/", methods=["GET"])
@monitor_bp.route("/<event>/", methods=["GET"])
@monitor_bp.route("/<event>/<production>", methods=["GET"])
def show_production_status(event=None, production=None):
    """Show the run status of either a given production, 
    all the productions for an event, or all of the productions
    in the project.

    .. http::get:: /monitor/
    
       Monitor all productions.

       .. http:example:: curl wget python-requests

          GET /monitor/ HTTP/1.1
          Content-Type: application/json
    """
    return make_response(jsonify(None), 200)

