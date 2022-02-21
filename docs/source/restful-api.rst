HTTP RESTful API
================

Asimov implements an HTTP API using a RESTful interface.
This allows external applications to readily interact with a running asimov instance.

.. warning:: This documentation is for an unreleased feature in asimov.

* :ref:`routingtable`


Productions
-----------

In asimov every analysis is handled by an asimov "production", which contains all of the details required to create an analysis pipleine, for example the choice of waveform approximant, analysis pipeline, and analysis specific settings.
Every analysis is attached to an event, which represents an individual gravitational wave event, and information which applies to all analyses of that event.
Normally a production will inherit most of its settings from the event, but these can be over-loaded for each individual production.
For example, the event time will be stored within the event, but if an earlier start time was desired for a single analysis this can be specified on the production.

Endpoints
^^^^^^^^^

Asimov exposes API endpoints for viewing and creating productions, in addition to changing the state of each production (e.g. starting or stopping an analysis).

.. http:get:: /productions

   List all of the productions available to asimov.
   A list of events will be returned in JSON format, with all of the details for each production returned by default.

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

	 
   :statuscode 200: Successful
   :reqheader Content-Type: application/json

.. http:get:: /productions/(event_id)

   Fetch the events for a single event, called `event_id`.
   
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

   Create a new production for the event called `event_id`.
	       
   .. http:example:: curl wget python-requests

      POST /productions/GW170817 HTTP/1.1
      Content-Type: application/json

      {"approximant": "IMRPhenomXPHM",
       "comment": "A test production",
       "status": "ready",
       "pipeline": "bilby"}

.. http:post:: /productions/

   Create a new production.
   Optional parameters can be passed within the JSON body of the request.
       
   .. http:example:: curl wget python-requests

      POST /productions/ HTTP/1.1
      Content-Type: application/json

      {"approximant": "IMRPhenomXPHM",
       "event": "GW170817",
       "comment": "A test production",
       "status": "ready",
       "pipeline": "bilby"}

   :jsonparam string event: The event ID to which the production should be added.
   :jsonparam string pipeline: The pipeline which this production will run.

   :statuscode 201: Event was created successfully.


Models
^^^^^^

A number of production endpoints return a production model containing data about the production.

.. jsonschema::

   {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Production",
    "description": "An asimov analysis production.",
    "type": "object",
    "properties": {
	"event": {
	    "description": "The ID of the event this production is applied to.",
	    "type": "string"
	}
    },
    "required": ["event"]
   }
       
Events
------

.. autoflask:: asimov.server:create_app()
   :undoc-static:
   :blueprints: events


Monitoring
----------

.. autoflask:: asimov.server:create_app()
   :blueprints: monitor
