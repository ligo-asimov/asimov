==================
Pipeline interface
==================

In order to interact with the various pipelines asimov needs some additional glue code.

An interface for any pipeline can be constructed, provided that pipeline can be submitted to a condor scheduler using a DAG file.

The ``asimov.pipeline`` module defines the factory classes for these interfaces, and individual interfaces can be found in the ``asimov.pipelines`` module.

Adding new pipelines
--------------------

New pipelines can be added to asimov by overloading the various methods in the :class:``asimov.pipeline.Pipeline`` class.
The most important of these is the ``build_dag`` method, which is used by the asimov framework to construct the DAG file to be submitted to the condor scheduler.

An example of a complete pipeline interface can be seen in the code for :class:``asimov.pipelines.lalinference.LALinference``.


Pipeline hooks
--------------

It is possible to customise the run process of the asimov pipeline runner using hooks.
By overloading the hook methods (listed below) inherited from the ``asimov.pipeline.Pipeline`` class additional operations can
be conducted during the processing workflow.
Hooks should take no arguments.

Implemented hooks are:

::

   before_submit()    --- Executed immediately before the DAG file for a pipeline is generated.
   after_completion() --- Executed once execution has successfully completed.

Supported Pipelines
-------------------

The following pipelines currently have support bundled with asimov:

+ ``LALInference``
+ ``BayesWave``
+ ``bilby``
+ ``RIFT``

LALInference interface
----------------------

The LALInference interface can be used to submit jobs to condor clusters which use lalinference as the inference engine.
LALInference jobs must be specified by an appropriately formatted ``ini`` file.

Status messages
~~~~~~~~~~~~~~~

Events run by the LALInference pipeline can have the following status values:

``wait``
   In this state the pipeline will ignore the production

``ready``
   In this state asimov will attempt to submit the job to the condor scheduler

``running``
   Applied after the job is submitted to the cluster

``stuck``
   Applied when the job is held or an error is detected in the pipeline's execution

``finished``
   Applied when normal termination of the pipeline is detected.


Event metadata
~~~~~~~~~~~~~~

In addition to the required event metadata, the LALInferance interface accepts the following event metadata fields:

``rundir``
   The run directory for this event (this will become the parent for unspecified production run directories).

``webdir``
   The web directory for this event (this will become the parent for production web directories).

Production metadata
~~~~~~~~~~~~~~~~~~~

In addition to the required production metadata the LALInference interface accepts the following metadata fields:

``queue``
   The condor queue which the job should be submitted to.
   Defaults to ``Priority_PE`` if not specified.

``rundir``
   The desired run directory for the job.
   DEfaults to ``<event.rundir>/<production.name>`` if event run directory is specified.
   Defaults to ``~/event/production`` if the event run directory specified.

Run data
~~~~~~~~

The following values will be added to the production meta data by asimov as a production is running

``user``
   The accounting user who submitted the event.

``job id``
   The JobID for this event on the condor cluster.


BayesWave interface
-------------------

The BayesWave interface can be used to submit jobs to condor clusters which use bayeswave as the inference engine.
BayesWave jobs must be specified by an appropriately formatted ``ini`` file.

.. todo::

   This needs full documentation once it's clear what the overall requirements of the BW interface will be.

Bilby interface
---------------

The Bilby interface allows for some bilby-specific metadata.


``job label``, optional.
   The label for the job.
   
``prior``
   The prior file to be used for this production.
   Note, this may be semi-automated in the future, but this value will still be available to over-ride the underlying default.

RIFT interface
--------------

Production metadata
~~~~~~~~~~~~~~~~~~~

``approximant``
    The approximant which should be used for this RIFT run.

``cip jobs``, optional
    Used to specify the number of independent sampler jobs which should be run.
    Defaults to 3 if a value is not supplied.

``lmax``
    The highest order of harmonic to be included in the analysis.

``bootstrap``, optional
    A previous production which can be used to "bootstrap" the sampler.
    You should combine this with a ``needs`` instruction, so that the RIFT job isn't run until the bootstrapping job has completed.

::

   bootstrap: Prod1
   needs: Prod1

