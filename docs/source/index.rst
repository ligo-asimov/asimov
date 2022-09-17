Asimov : The PE Automator and Manager
=====================================

`Asimov` is a python package to help with setting-up, automating, and monitoring scientific data analysis.
It is designed to make organising a scientific project, simplifying your workflow, and making your analysis easier to reproduce.

Asimov makes setting-up and running parameter estimation jobs easier.
It can generate configuration files for several parameter estimation pipelines, and handle submitting these to a cluster.
Whether you're setting-up a preliminary analysis for a single gravitational wave event, or analysing hundreds of events for a catalog, Asimov can help.

Features
--------

Scientific analysis management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Asimov is able to interact with high throughput job management tools, and can submit jobs to clusters, monitor them for problems, and initiate post-processing tasks.
Once your analysis is completed asimov can manage the data products and results, and prepare them for publication and distribution.

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

Asimov is available on ``pypi`` and can be installed via ``pip install asimov``.



Tutorials
---------

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   starting-project
   starting-analysis

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

.. toctree::
   :maxdepth: 2
   :caption: The Ledger

   ledger
      
   
.. toctree::
   :maxdepth: 1
   :caption: Pipeline Guides

   pipelines
   pipelines/lalinference
   pipelines/bilby
   pipelines/rift
   pipelines/bayeswave
   
Advanced topics
---------------

.. toctree::
   :maxdepth: 2
   :caption: Advanced topics
	     
   configuration
   yamlformat
   gitlab-interface
   test-interface
   clusters

Developers' Guide
-----------------

.. toctree::
   :caption: Development Guide

   ../../CONTRIBUTING.rst
   ../../CODE-OF-CONDUCT.rst

   pipelines-dev
   
   restful-api
   
Module documentation
--------------------

.. toctree::
   :maxdepth: 1
   :caption: Modules

   api/git
   state
   pipelines
   storage
   config
	     
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`routingtable`
