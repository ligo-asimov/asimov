Starting a new project using Asimov
===================================

Asimov is designed to help manage large analysis projects which might involve performing numerous different analyses on numerous gravitational wave events.

Asimov can also handle setting jobs up both on clusters, or on a local machine which has a condor scheduller installed.

Basic concepts
--------------

Asimov aggregates analyses together into *projects*.
An example of a project might be a gravitational wave event catalogue publication, or it might be an exceptional event paper.
A project can involve just one event, or hundreds.

Each event within a project can have multiple "productions".
A production is a specific analysis; you might want to run an analysis with several different analysis pipelines, or you might want to run with the same pipeline, but different priors.


Creating a project
------------------

You can create a new Asimov project by running

.. code-block:: console

		$ olivaw init

in a directory.
Asimov will create a number of new directories and files to assist with the process of managing your project.
The ``olivaw`` program is Asimov's built-in command-line interface, but you can also interact with projects via the Python API.


Asimov categorises jobs hierarchically, sorting them first by the ``event`` which you're analysing, and then by ``production``, which is the specific analysis.

Adding an event
---------------

To add a new event (let's call this one "GW150914") to the project you can run

.. code-block:: console

		$ olivaw event create GW150914


Each event can have multiple different productions, so that you can run different exploratory investigations on the same data.


Adding a production
-------------------

Adding a new production to an event is also straight-forward. Let's add a ``lalinference`` job:

.. code-block:: console

		$ olivaw production --event GW150914 --pipeline lalinference

Once we've added a production to the project it gets stored in the project's ledger.
By default this is stored in a file called ``ledger.yml`` in the root of the project directory.
The ledger is used to populate configuration files for the individual analysis pipelines from templates, but you can also add your own templates (see the :ref:`templating <Making pipeline configurations>` documentation).

Running your analyses
---------------------

The configuration files need to be created by running the ``build`` command:

.. code-block:: console

		$ olivaw manage build --event GW150914

You can omit the ``--event`` argument, and ``asimov`` will attempt to build configurations for every event in the project.

Finally, to submit your jobs to the condor scheduler run

.. code-block:: console

		$ olivaw manage submit --event GW150914


Monitoring your analyses
------------------------
		
Once your job is up and running you can keep track of its progress on the cluster using asimov.
First we need to update the ledger with the lastest run information; we can do this with the ``olivaw monitor`` command:

.. code-block:: console

		$ olivaw monitor

We can then use a number of tools to get a quick overview of the status of the project's jobs.
The first of these is ``olivaw report status`` which just prints the status of each job to the terminal.
Alternatively we can use ``olivaw report html`` to produce a more detailed report in html format.
