Working with analyses
=====================

Once we have a project and at least one event we can start to add analyses.
A single analysis with asimov is called a "production".

Asimov interacts with a number of different analysis pipelines in order to produce configuration files, generate DAGs (files used to launch the jobs on compute clusters), submit those jobs to clusters, and then handle any post-processing of the results.

In order to make starting an analysis as easy as possible asimov maps its standard configuration values to all of its supported pipelines.
This means that setting-up equivalent jobs with two different pipelines requires only a couple of commands.

Adding an analysis from a YAML file
-----------------------------------

.. todo:: Add instructions on using YAML files and the ``asimov apply`` command.

Adding a new production
-----------------------

Let's try adding a `lalinference` production to an event called GW150914.
Provided we don't need to perform any customisation to our production we can just run

.. code-block:: console

		$ olivaw production create GW150914 lalinference --approximant IMRPhenomPv2

If we now look at the ledger we can see that the GW150914 event has been updated to include a productions section, and the lalinference job has been added:

.. code-block:: yaml

		events:
		- calibration: {}
		  event time: 1126259462.426435
		  interferometers:
		  - H1
		  - L1
		  name: GW150914
		  productions:
		  - Prod0:
		      approximant: IMRPhenomPv2
		      comment: null
		      pipeline: lalinference
		      review: []
		      status: wait
		  working directory: working/GW150914

When creating the production we can also add a comment, which may be useful to help distinguish it from similar analyses when we're looking at many jobs.
We can do that by adding the ``--comment`` option:

.. code-block:: console

		$ olivaw production create GW150914 lalinference --comment "Higher mode analysis"


Naming productions
------------------
		  
Asimov names productions automatically, with the first becoming ``Prod0`` by default, and future jobs being incremented, so ``Prod1``, ``Prod2``, and so on.
We can customise the prefix of the name with the ``--family`` option.
For example, if you wanted to call your exploratory runs ``Exp0``, ``Exp1``, and so-forth you could do that by using this command:

.. code-block:: console

		$ olivaw production create GW150914 lalinference --family Exp

Analysis dependencies
---------------------

When we create the production we can supply some additional information, including a list of dependencies.
Any production can have multiple other productions as a dependency; asimov will construct a graph by analysing the dependencies for all productions, and will ensure that they are executed in the correct order.

Suppose you have set up a job which produces PSDs which are required for all subsequent analyses.
This production is called ``Prod0``.
Then we can set up  a subsequent analysis with

.. code-block:: console

		$ olivaw production create GW150914 lalinference --needs Prod0

This production will not be set-up and run until ``Prod0`` has been completed.
		
.. note::

   If you need to add multiple dependencies, just add the ``--needs`` option several times, e.g. ``--needs Prod0 --needs Prod1``.


Analysis status
---------------

Asimov uses its ledger to record the last known state of a production, in the form of a state machine.
Details of the possible states are documented on the :ref:`../state.rst<states page>` of the documentation.

By default a new production is assigned a ``wait`` state, which prevents asimov from generating the configuration file for the pipeline, or starting the analysis.
This is a useful state to put jobs into until you're happy that all of the settings are correct.

If you want a production to be ready to start as soon as it is created, however, you can pass the ``--status`` option, for example

.. code-block:: console

		$ olivaw production create GW150914 lalinference --status ready


Pipeline template
-----------------

In order to start an analysis using one of the pipelines asimov must produce an appropriate configuration file for the pipeline generator.
These are generated using template files, which are specific to each pipeline.
When asimov builds pipelines it substitutes configuration values for each production into these templates.

A default template is included with asimov for each supported pipeline, however there may be situations where these are insufficient and another template is required.

A custom template can be included using the ``--template`` option, for example

.. code-block:: console

		$ olivaw production create GW150914 lalinference --template testinggr.ini


You can find more information about configuration templates at the `templates` page of the documentation.
