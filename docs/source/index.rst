Asimov : The PE Automator and Manager
=====================================

`Asimov` is a python package to help with setting-up, automating, and monitoring parameter estimation workflows for gravitational wave signals.

Asimov makes setting-up and running parameter estimation jobs easier.
It can generate configuration files for several parameter estimation pipelines, and handle submitting these to a cluster.
Whether you're setting-up a preliminary analysis for a single gravitational wave event, or analysing hundreds of events for a catalog, Asimov can help.

Features
--------

Job monitoring and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Asimov is able to interact with high throughput job management tools, and can submit jobs to clusters, monitor them for problems, and initiate post-processing tasks.

Uniform pipeline interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

Asimov provides an API layer which allows a single configuration to be deployed to numerous different analysis pipelines.
Current gravitational wave pipelines which are supported are ``lalinference``, ``bayeswave``, ``RIFT``, and ``bilby``.

Centralised configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Asimov records all ongoing, completed, and scheduled analyses, allowing jobs, configurations, and results to be found easily.

Reporting overview
~~~~~~~~~~~~~~~~~~

Asimov can provide both machine-readible and human-friendly reports of all jobs it is monitoring, while collating relevant log files and outputs.

Quick installation
------------------

Asimov is available on ``pypi`` and can be installed via ``pip install ligo-asimov``.



Tutorials
---------

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   starting-project
   starting-analysis
   gitlab-interface

Users' guide
------------

.. toctree::
   :maxdepth: 2
   :caption: Users' guide

   installation
   olivaw/projects
   olivaw/events
   olivaw/productions
   olivaw/running
   olivaw/reporting
   olivaw/review
   configuration

Module documentation
--------------------

.. toctree::
   :maxdepth: 1
   :caption: Modules

   api/git
   state
   yamlformat
   pipelines
   storage
   config
	     
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
