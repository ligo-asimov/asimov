HTTP RESTful API
================

Asimov implements an HTTP API using a RESTful interface.
This allows external applications to readily interact with a running asimov instance.

.. warning:: This documentation is for an unreleased feature in asimov.

You can find a detailed listing of all of the available endpoints in the :ref:`routingtable`.
This page shows some basic examples of how to access the API using ``curl`` and the python ``requests`` library.


Basics
------

Asimov provides access to some basic information about the system it's running on via the API.

Endpoints
^^^^^^^^^

.. autoflask:: asimov.server:create_app()
   :undoc-static:
   :blueprints: asimov


