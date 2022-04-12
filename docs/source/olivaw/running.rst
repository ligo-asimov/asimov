Running and monitoring analyses
===============================

One of the major problems with large projects is making sure that all of the analyses are running as planned, and diagnosing faults when they aren't.
Asimov monitors the underlying job scheduller in order to ensure that problems are caught and reported.

Preparing and submitting an analysis
------------------------------------

For the rest of this document we'll assume that you've got a production set up and have built its configuration file using ``olivaw manage build``, and submitted it to a cluster using ``olivaw manage submit``.

When the job has been submitted to the compute cluster asimov will record a unique identifier for the job which it can use to track its status.
In the case of ``htcondor`` this is the cluster ID.

Monitoring job status
---------------------

In order to manually check the status of all of the ongoing analyses in a given project you can simply run ``olivaw monitor`` in the root directory of the project.
You can think of this as being similar to running ``condor_q``, but in addition to checking the status of jobs this step will also advance a finished job to the next step in its process (e.g. starting post-processing), or gather error information.

If you just want to check the status of a single event you can pass the event name as an argument to ``olivaw monitor``, for example ::

  olivaw monitor GW150914

Producing a human-readable report
---------------------------------

A summary webpage for all ongoing analysis productions in a project can be produced by running ::

  olivaw report html

Which will show at a glance which analyses have completed, are still running, or have become stuck.
