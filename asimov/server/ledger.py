"""
Ledger-related blueprints.
Functions for things like adding new events and productions.
"""

from flask import Blueprint, request, jsonify, make_response, json
from asimov import ledger

events_bp = Blueprint("events", __name__, url_prefix="/events")

@events_bp.route("/", methods=["GET"])
def show_ledger():
    """Return the entire contents of the ledger.

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /events HTTP/1.1
       Content-Type: application/json

    """

    events = ledger.events
    return make_response(jsonify(events), 200)

@events_bp.route("/<event>", methods=["GET"])
def show_event(event):
    """Return the entire contents of the ledger for a single event.

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /events/<event> HTTP/1.1

    """

    event = ledger.get_event(event=event)
    return make_response(event.to_dict(), 200)

@events_bp.route("/<event>", methods=["POST"])
def create_event(event):
    """Add a new event to the ledger.

    Examples
    --------
    .. http:example:: curl wget python-requests

       POST /events/<event> HTTP/1.1
       Content-Type: application/json

    """
    from asimov.event import Event
    new_event = Event(name=event, **request.get_json())
    ledger.add_event(new_event)
    return make_response(new_event.to_dict(), 201)

@events_bp.route("/<event>/productions", methods=['GET'])
def show_productions(event):
    """Return all of the productions for a given event.

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /events/<event>/productions HTTP/1.1
       Content-Type: application/json

    """

    filters = request.args

    event = ledger.get_event(event=event)
    return make_response(
        jsonify([production.to_dict() for production in event.productions]),
        200)


