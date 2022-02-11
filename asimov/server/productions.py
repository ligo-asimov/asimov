"""
Endpoints for productions.

Asimov enables a number of interactions with analyses (productions)
it is monitoring to be made via the web API.

These are:

+ Production creation
+ Production deletion
+ Updating unstarted productions
+ Changing the run status of a production
"""

from flask import Blueprint, request, jsonify, make_response, json
from asimov import ledger
from asimov.event import Production, DescriptionException

prods_bp = Blueprint("productions", __name__, url_prefix="/productions")


@prods_bp.route("/", methods=['GET', 'POST'])
@prods_bp.route("/<event>", methods=['GET', 'POST'])
def show_event_productions(event=None):
    """Return all of the productions in the ledger for a given event.

    Examples
    --------
    .. http:example:: curl wget python-requests

       GET /productions/event HTTP/1.1
       Content-Type: application/json

    """
    if request.method == "POST":
        return add_event_production(event)
    elif request.method == "GET":
        productions = ledger.get_productions(event=event, filters=request.args.to_dict())
        
    return make_response(
        jsonify([production.to_dict()[production.name] for production in productions]),
        200)


def add_event_production(event=None):
    """Add a new production to an event.

    Examples
    --------
    .. http:example:: curl wget python-requests

       POST /productions/event HTTP/1.1
       Content-Type: application/json

    """
    data = request.get_json()
    print("data", data)

    if not event:
        event = data['event']
    
    event = ledger.get_event(event)
    event_prods = event.productions
    names = [production.name for production in event_prods]
    
    #if "family" in data:
    #    family = data.pop("family")
    #else:
    #    family = "Prod"
    #family_entries = [int(name.split(family)[1]) for name in names if family in name]
        
    #
    print("GET JSON")
    production = request.get_json()
    print("GOT JSON")
    
    #if len(family_entries)>0:
    #    number = max(family_entries)+1
    #else:
    #    number = 0
    #production_dict = {f"{family}{number}": production}
    #print("dict", production_dict)

    production_dict = {"Test0": production}

    print("GET DICT")
    production = Production.from_dict(parameters=production_dict, event=event, issue=None)
    print("END")
    #
    try:
        ledger.add_production(event, production)
        response = make_response(jsonify(production.to_dict()), 201)
    except DescriptionException as e:
        response = make_response(jsonify({"_message": e}), 400)
    
    return response


