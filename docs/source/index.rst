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

Asimov is available on ``pypi`` and can be installed via ``pip install asimov``.
You can find more details about installing ``asimov`` in the :ref:`installationguide`.



Tutorials & Introductions
-------------------------

Asimov is designed to be capable of running many different kinds of analyses, and to be flexible and extendable.
However, it can be a little overwhelming to jump right in the deep end, so we've put together some tutorials which show how to use the core functionality of the package, including project management and analysis creation.

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   starting-project
   build-process

Users' guide
------------

The full users' guide for asimov covers everything you might need in the day-to-day use of asimov, but doesn't cover details about adding new pipelines or dealing in detail with the various databases asimov uses to manage its analyses.

.. toctree::
   :maxdepth: 1
   :caption: Users' guide

   installation
   olivaw/projects
   olivaw/events
   olivaw/productions
   olivaw/running
   olivaw/reporting
   olivaw/review

Advanced topics
---------------

These sections of the documentation cover the technical designs of various aspects of the software, including how various interfaces with external packkages work, and the specifications for data storage.

.. toctree::
   :maxdepth: 1
   :caption: Advanced topics
	     
   configuration
   yamlformat
   gitlab-interface
   test-interface
   templates
   reports

Developers' Guide
-----------------

We always welcome new contributions to the asimov package from both members of the gravitational wave community, and the general public.
Please familiarise yourself with the contributors' guidelines for more information.

.. toctree::
   :maxdepth: 1
   :caption: Development Guide

   Contributors' Guide <contributing>
   Contributors' Code of Conduct <code-of-conduct>
   building-docs
   
   
Module documentation
--------------------

This section of the guide contains the code-level documentation for asimov, and may be useful for developers, but you shouldn't normally need it as a normal user of asimov!

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
