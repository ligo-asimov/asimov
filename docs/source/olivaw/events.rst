
Creating and managing events
============================

Once you've created an asimov project you'll need to add some gravitational wave events to it to analyse.

You can do this completely manually, or you can retrieve a pre-existing event from LIGO's event database, GraceDB.

Creating an event from a YAML file
----------------------------------

.. todo:: Add instructions about using YAML files and the ``asimov apply`` command.

Creating an event
-----------------

The simplest way to make a new event is manually (however you'll need to specify all of its details manually later).

For example, if we want to make an event, and call it "GW150914" we can run

.. code-block:: console

		$ olivaw event create GW150914

The ledger file will then be updated to include the new event:

.. code-block:: yaml

		events:
		- calibration: {}
		  interferometers: []
		  name: GW150914
		  productions: []
		  working directory: working/GW150914

In most situations we'll want to pull some additional information about an event automatically.
This can be done using asimov's integration with GraceDB, and all we need is either the ``GID`` of the preferred event, or the ``SID`` of the superevent.

Let's try the GID approach first, because GW150914, for historical reasons, doesn't have a superevent.

.. note::

   You may need to use ``ligo-proxy-init`` to generate login credentials before running this command.

.. code-block:: console

		$ olivaw event create --gid G190047

Then we can see that the ledger has been updated with the event information from the GraceDB server:

.. code-block:: yaml

		- calibration: {}
		  event time: 1126259462.426435
		  interferometers:
		  - H1
		  - L1
		  name: GW150914
		  productions: []
		  working directory: working/GW150914


Equivalently, if we have a superevent we can use the ``--superevent`` option, and the preferred event will be found automatically.

.. code-block:: console

		 $ olivaw event create GW190425 --superevent S190425z

If this event has an external git repository for storing configurations you can tell asimov about it here as well, and it will be checked-out, and asimov will add configurations to it automatically.

For example:

.. code-block:: console

		$ olivaw event create --gid G190047 --repository git@git.ligo.org/pe/O1/GW150914

Adding configurations
---------------------

While it's possible to manually update the configuration for each event (e.g. data quality information, and prior information) these can also be imported from other locations.

Asimov supports importing configurations from both json and yaml files; these can either be files of default information, or information produced by the ``PEConfigurator`` program.


As an example, suppose we have some default data to add to an event, and this is in yaml format, saved in a file called ``data.yaml``.

.. code-block:: yaml

		data:
		  channels:
		    H1: H1:DCH-CALIB_STRAIN_C02
		    L1: L1:DCH-CALIB_STRAIN_C02
		    V1: Hrec_hoft_V1O2Repro2A_16384Hz
		  frame-types:
		    H1: H1_HOFT_C02
		    L1: L1_HOFT_C02
		    V1: V1O2Repro2A

		priors: 
		    distance: [None, 10000]
		    component: [1, 1000]
		    q: [0.05, 1.0]

In order to add these default data to an existing event we can use the ``olivaw event load`` command:

.. code-block:: console

		$ olivaw event load GW170817 data.yaml

These will then be added to the event record in the ledger.

If we have a JSON file from the PEConfigurator we need to use the ``olivaw event configurator`` command, which maps the outputs from the configurator to asimov's data format:

.. code-block:: console

		$ olivaw event configurator GW170817 --json gw170817.json

Adding calibration evelopes
---------------------------

Many analyses will require access to calibration envelopes for the detectors.
Asimov includes a tool for locating the appropriate envelopes for events.

Provided you've already added a gpstime to the event (either manually, or from GraceDB) you can run

.. note::

   This should work on LIGO clusters, but you'll need to follow the instructions for adding calibration information manually if you're running the command elsewhere.

.. code-block:: console

		$ olivaw event calibration GW170817

This will search for the calibration files for all of the available detectors, and add them to the event record in the ledger.

If you need to add calibrations manually you can do that by specifying them as options:

.. code-block:: console

		$ olivaw event calibration GW150914 --calibration H1:h1-cal.dat -- calibration L1:l1-cal.dat


Command documentation
---------------------
.. click:: asimov.olivaw:olivaw
   :prog: olivaw
   :commands: event
   :nested: full
