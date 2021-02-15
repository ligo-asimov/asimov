Olivaw
######

The main "bot" script which comes packaged with.
``Olivaw`` is designed to oversee the workflow for compact binary coalesence parameter estimation jobs.

Features
--------

- Load events from GraceDB
- Load default data from yaml files
- Load PEConfigurator results from json files
- Generate pipeline configurations
- Generate and ubmit DAG files for pipelined analyses

Build
-----

The build command, which can be run as

.. code-block:: console

   $ olivaw build [OPTIONS]

will build the configuration files for all productions which are ready (that is, all of their dependencies are met, and they are themselves marked as ``ready``).
By default all of the available events will be processed, but by passing a specific event ID this can be restricted to a single event, for example

.. code-block:: console

   $ olivaw build --event GW150914

Options
~~~~~~~

--event event_id
   The event which the configurations should be built for.

Submit
------

The submit command, which can be run as

.. code-block:: console

   $ olivaw submit [OPTIONS]

will generate and submit the DAG files to the scheduler for all productions which are ready (that is, all of their dependencies are met, and they are themselves marked as ``ready``).
By default all of the available events will be processed, but by passing a specific event ID this can be restricted to a single event, for example

.. code-block:: console

   $ olivaw submit --event GW150914

Options
~~~~~~~

--event event_id
   The event which the configurations should be submitted for.
--update {True|False}
   Determines whether the git repositories for the events should be pulled from.
   This can be used to prevent an excessive number of requests being made to a rate-limited repository server.

Monitor
-------

The ``olivaw monitor`` command performs a large number of checks on running jobs, including identifying when a job's execution has completed, and beginning the postprocessing and uploading of results.

Ledger
------
