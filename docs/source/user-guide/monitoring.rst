Monitoring Analyses
===================

Once a pipeline for an analysis has been built and submitted to a computing cluster asimov can be used to monitor the progress of the analysis job, and perform a number of tasks based on what it finds.

The ``asimov monitor`` command automates several different tasks when checking an analysis.

For example,

.. code-block:: console

		$ asimov monitor

		GW150914_095045
		- Prod0[bayeswave]
		  ● Prod0 has finished and post-processing is running
		- Prod1[bilby]
		  ● ready

The output of this command tells us that the event called ``GW150914_095045`` has two analyses.
- ``Prod0`` is a ``bayeswave`` analysis, and it's finished, and asimov has started running post-processing on the results.
- ``Prod1`` is a ``bilby`` job, and it's ready to run. It could be started by running ``asimov manage build submit``.

Problems
--------

Held analyses
~~~~~~~~~~~~~

Asimov will also report problems with analyses when it finds them.
For example, if the job running the analysis on the scheduler is held then you might see something like this:


.. code-block:: console

		$ asimov monitor

		GW150914_095045
		- Prod0[bayeswave]
		  Job is stuck on condor

or if the post-processing job for the analysis is stuck you might see this:

.. code-block:: console

		$ asimov monitor

		GW150914_095045
		- Prod0[bayeswave]
		  Post-processing job is stuck on condor

In both cases these are scenarios ``asimov`` cannot resolve on its own.
It might be because the cluster has been taken down for maintenance, or because of a resource requirements problem.
You can diagnose this using the ``condor_q -hold`` command, for example:

.. code-block:: console

		$ condor_q -hold

		-- Schedd: ldas-grid.ligo.caltech.edu : <10.14.0.12:9618?... @ 10/31/22 09:48:45
		ID           OWNER          HELD_SINCE  HOLD_REASON
		286778866.0   daniel.william 10/31 04:03 The system macro SYSTEM_PERIODIC_HOLD expression '(NumShadowExceptions > 20)' evaluated to TRUE




Finished analyses
~~~~~~~~~~~~~~~~~

When asimov finds that an analysis has finished it will start running whatever post-processing the analysis pipeline specifies.
When the post-processing has finished the processed results are copied to the project's results store.

Rescuing jobs
~~~~~~~~~~~~~

If asimov finds that an analysis should be running, but is no longer running on the scheduler, it will attempt to rescue the job, using whatever rescue logic the pipeline specifies.
This will often just involve resubmitting the job's "rescue DAG" to the cluster.

Stopping analyses
-----------------

Analyses which are marked with a status of ``stop`` will be removed from the scheduler by the ``asimov monitor`` command.

.. note:: Stopping an analysis

	  You can set an analysis to stop using the ``asimov production set`` command, for example

	  .. code-block:: console

			  $ asimov production set GW150914 Prod0 --status stop
