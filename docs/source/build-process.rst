How asimov creates analyses
===========================

When you're setting up an analysis it can be useful to understand the steps which asimov needs to take to get everything started.
There are two commands in asimov which do a lot of heavy lifting, ``olivaw manage build`` and ``olivaw manage submit``, and this guide goes into a little more detail about what's actually happening under the hood when you run these.

Introduction to asimov pipelines
--------------------------------

Asimov has been designed to work with a number of pre-existing analysis pipelines.

The pipelines which Asimov is designed to operate with typically use a configuration file to store the settings which will be required for the analysis, and may need access to a number of other auxilliary files.

Asimov is capable of generating or retrieving all of these files for the various pipelines it provides support for.

This document provides an overview of how an analysis is built, with pointers to the documentation for the individual steps.

Project management with asimov
------------------------------

Asimov was originally designed to handle analyses on gravitational wave events, and much of its terminology originates from this, however the hierarchy it imposes on analyses can be adapted to other purposes and does not need to be considered exclusively for use with transient events.

The fundamental organisational unit in asimov is a *project*.
Projects were designed to keep all of the analysis which were destined for a given publications in a single place.

Within a project asimov sorts things as *events*.
This is a legacy of its original development for the analysis of gravitational wave transient signals, but these could be used to sort analyses together by, for example, different astronomical objects, rather than temporally distinct events.

.. note:: Objects and events
	  
	  We anticipate that in the near future we will add the concept of "objects" or something similar in parallel with "events" to allow more natural handling of non-transient analyses.

Finally, each event can have any number of *productions* assosciated with it.
A production is simply an analysis using one of asimov's supported analysis pipelines.
This allows each event to have analyses using multiple different pipelines and also analyses using the same pipeline but multiple different settings.

This hierarchy allows default settings for analyses to be set at various levels.
For example it may be desirable to use the same setting across all analyses within a project in all analysis pipelines, or just for all of the productions in a given event.
Per-project and per-event defaults can be overloaded in each production, to allow for exploratory runs with different settings, or to allow for edge cases.

To give a concrete example, say we wish to write a paper which analyses the three gravitational wave transient events which were discovered in the first observing run of the LIGO detectors.
We could create a project for our paper, and then add GW150914, GW151012, and GW151226 as events to the project.
We often want to analyse each event with multiple different samplers and analysis frameworks to help to reduce uncertainty introduced into our analyses by the software itself.
We could then add a production using the ``bilby`` pipeline and a production using the ``lalinference`` pipeline to each event.

The ``bilby`` and ``lalinference`` analyses will inherit things like the event time from the metadata for the event, which would be the same for all of a given event's analyses, and things like the data channel would be set at the project level and inherited by all of the analysis productions.
It's not unusual to need to specify a different data channel for a small number of events being analysed to access things like deglitched data, and these could be specified either on the event or individual productions.

Alternatively, suppose we wish to analyse the signals from a set of pulsars.
We could again make a new project, but this time include each pulsar as an event, giving e.g. the sky location of each object which would then be inherited by each analysis production.

Production metadata
-------------------

Each analysis handled by asimov is handled as an individual ``Production``, and metadata about the production and its assosciated ``Event`` are recorded in the ledger for the event.
This information is used to produce the configurations for each production analysis.

An example of an event ledger might look something like this, which is for ``GW150914``:

.. code-block:: yaml

		calibration:
		  H1: C01_offline/calibration/H1.dat
		  L1: C01_offline/calibration/L1.dat
		data:
		  channels:
		    H1: H1:DCS-CALIB_STRAIN_C02
		    L1: L1:DCS-CALIB_STRAIN_C02
		  frame-types:
		    H1: H1_HOFT_C02
		    L1: L1_HOFT_C02
		event time: 1126259462.391
		gid: G190047
		interferometers:
		- H1
		- L1
		name: GW150914
		priors:
		  amp order: 1
		  chirp-mass:
		  - 21.418182160215295
		  - 41.97447913941358
		  component:
		  - 1
		  - 1000
		  distance:
		  - 10
		  - 10000
		  q:
		  - 0.05
		  - 1.0
		productions:
		- ProdF0:
		    comment: Bayeswave PSD job
		    pipeline: bayeswave
		    status: ready
		- ProdF1:
		    approximant: IMRPhenomXPHM
		    comment: Bilby PSD job
		    needs:
		    - ProdF0
		    pipeline: bilby
		    status: ready
		- ProdF2:
		    approximant: SEOBNRv4PHM
		    comment: RIFT job
		    needs:
		    - ProdF0
		    pipeline: rift
		    status: ready
		psds:
		  2048:
		    H1: C01_offline/psds/2048/H1-psd.dat
		    L1: C01_offline/psds/2048/L1-psd.dat
		quality:
		  lower-frequency:
		    H1: 20
		    L1: 20
		  psd-length: 4
		  reference-frequency: 20
		  sample-rate: 2048
		  segment-length: 4
		  start-frequency: 13.333333333333334
		  upper-frequency: 896
		  window-length: 4
		repository: git@git.ligo.org:pe/O1/GW150914
		working directory: /home/daniel.williams/events/O3/o3a/run_directories/GW150914


This ledger contains all of the information required to set up three analyses; a Bayeswave analysis (to produce the PSD files for the other analyses), a bilby analysis, and a RIFT analysis.

The metadata contained in sections such as ``quality`` and ``priors`` is then used to create the configuration files for each pipeline using a template.

Individual productions can overwrite the event metadata for any of the templatable values, allowing asimov, for example, to set up two analyses with different sample-rates.

``olivaw manage build``
-----------------------

The command line utility ``olivaw manage build`` is used to construct pipeline configurations by combining a configuration template for the pipeline with data from the production ledger.

This runs the ``Production.make_config()`` method, which determines the pipeline from the ledger.
If a template is provided in the metadata for the production (under the ``template`` value) then this template is used to construct the configuration file.
Otherwise the appropriate pipeline configuration template is used (e.g. ``bilby.template`` for the ``bilby`` configuration).

Metadata is then substituted into the configuration file, and the final file is committed to the event's repository, under than production's name. For example, a production called ``Prod1`` will produce an ``ini`` file called ``Prod1.ini``.

This step does not require pipeline-specific code, and so it uses only code from the ``asimov.event`` module.
This allows configurations to be generated in environments which do not have the pipelines installed.

The next step is then used to invoke pipeline-specific code.

``olivaw manage submit``
------------------------

Once a configuration has been generated it can be used to generate an ``htcondor`` DAG file for execution on a cluster.

The process for this step is different for each analysis pipeline.
An object for that pipeline is then created with the metadata from the production.

First running ``olivaw manage submit`` determines the correct pipeline for the production from the ``pipeline`` value in the ledger.

First the ``build_dag`` method is called on the pipeline object.
In general each pipeline will then execute the pipeline construction utility and any additional steps required to build a DAG file (for ``bilby``, for example, the ``bilby_pipe`` tool is used to produce the DAG.

The second step performs the submission of the DAG to the cluster.
The ``submit_dag`` method is called on the pipeline object.
In general a pipeline will first run its ``before_submit`` method, which can be used by the pipeline to download any additional files, for example.
Then the DAG file is submitted to the ``htcondor`` submit node using the ``condor_submit_dag`` tool.
The ``cluster id`` for the submitted DAG is then retrieved, and stored in the manifest under the ``job id`` value for the production.

