
Managing projects with Olivaw
=============================

Olivaw is the commandline interface for asimov which is designed to make working with your project easier.

Creating projects
-----------------

You can use olivaw to produce a new project, and set up the required directory structure automatically.

The easiest way to do this is by running

.. code-block:: console

		$ olivaw init "Test project"

Which will convert the current directory into an asimov project directory, including producing the ledger file, and creating directories for results storage.

It is possible to customise the project in a number of ways, including specifying alternative locations for the various subdirectories (though you should do this with care).

.. click:: asimov.olivaw:olivaw
   :prog: olivaw
   :commands: init
   :nested: full



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
