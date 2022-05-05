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

    .. http:get:: /productions

       :statuscode 200: Successful
    
       

       Example
       -------

       .. http:example:: curl wget python-requests

          GET /productions/ HTTP/1.1
          Content-Type: application/json


          HTTP/1.1 200 OK
          Content-Type: application/json

          [
             {
               "calibration": {},
               "comment": null,
               "event": "GW150914",
               "event time": 678,
               "pipeline": "bayeswave",
               "review": [],
               "status": "ready",
               "working directory": "working/GW150914"
             },
             {
                 "approximant": "SEOBNRv4PHM",
                 "calibration": {
                   "H1": "C01_offline/calibration/H1.dat",
                   "L1": "C01_offline/calibration/L1.dat",
                   "V1": "C01_offline/calibration/V1.dat"
                 },
                 "combination": {
                   "job": 231253218,
                   "productions": []
                 },
                 "comment": "RIFT job",
                 "data": {
                   "channels": {
                     "H1": "H1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01",
                     "L1": "L1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01",
                     "V1": "V1:Hrec_hoft_16384Hz"
                   },
                   "frame-types": {
                     "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
                     "L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
                     "V1": "V1Online"
                   }
                 },
                 ...
               }
             ]

    .. http:get:: /productions/(event_id)

       Fetch the events for a single event ID.

       .. http:example:: curl wget python-requests

          GET /productions/GW150914 HTTP/1.1
          Content-Type: application/json


          HTTP/1.1 200 OK
          Content-Type: application/json

          [
            {
              "calibration": {},
              "comment": null,
              "event": "GW150914",
              "event time": 678,
              "pipeline": "bayeswave",
              "review": [],
              "status": "ready",
              "working directory": "working/GW150914"
            },
            {
              "approximant": "IMRPhenomXPHM",
              "calibration": {},
              "comment": "A test production",
              "event": "GW150914",
              "event time": 678,
              "pipeline": "bilby",
              "review": [],
              "status": "ready",
              "working directory": "working/GW150914"
            }
          ]

       :statuscode 200: Successful

    .. http:post:: /productions/(event_id)

       .. http:example:: curl wget python-requests

          POST /productions/GW170817 HTTP/1.1
          Content-Type: application/json

          {"approximant": "IMRPhenomXPHM",
           "comment": "A test production",
           "status": "ready",
           "pipeline": "bilby"}

       .. http:example:: curl wget python-requests

          POST /productions/ HTTP/1.1
          Content-Type: application/json

          {"approximant": "IMRPhenomXPHM",
           "event": "GW170817",
           "comment": "A test production",
           "status": "ready",
           "pipeline": "bilby"}

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


