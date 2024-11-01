Integrating a new pipeline with Asimov
======================================

This guide is intended to help you to make your code with asimov.

Asimov is able to automate the process of configuring, running, and monitoring analyses at scale, and can make managing large numbers of similar analyses easy while ensuring that everything is readily reproducible.

First steps
-----------

In this tutorial we'll assume that you're extending an analysis which has been written in Python, however asimov can automate analyses written in any language. Writing shims for non-Python pipelines will be covered in their own tutorial in the future. We'll also assume that your code either runs as a script in a terminal, or produces submission information for the ``htcondor`` job scheduler. While we hope to provide support for other schedulers in the future, asimov v0.5 can only work with ``htcondor``.

In order to provide concrete examples in this tutorial I'll discuss the process of integrating the ``pyring`` package with asimov. ``pyring`` is a gravitational wave analysis code, and as a result there may be some gravitational-wave specific references in the tutorial. However asimov can run any code (and from asimov 0.6 onwards we'll make this easier by further separating GW-specific code from the main codebase).

The main ``pyring`` repository looks something like this:

.. code-block:: bash

   $ ls
   AUTHORS.md    LICENSE      README.rst  pyRing                pyproject.toml    scripts    setup.py
   CHANGELOG.md  MANIFEST.in  docs        pypi_description.rst  requirements.txt  setup.cfg

we'll add the `asimov.py` file in the ``pyRing`` directory.

We need to tell asimov at least four things about our pipeline:

1. How to run it
2. How to submit it to ``htcondor``
3. How to check it's finished running
4. How to find its assets, e.g. results files

All of these are handled by methods on a class which we can make by subclassing the ``asimov.pipeline.Pipeline`` class.

For example, here we'll start by writing this to make the class:

.. code-block:: python

   import asimov.pipeline.Pipeline

   class pyRing(asimov.pipeline.Pipeline):
     """
     The pyRing Pipeline.
     """
     name = "pyRing"
     _pipeline_command = "pyring"

we can now add various bits of logic as methods on this class which will overload the base class's methods.

``build_dag``
-------------

The ``build_dag`` method is used to tell asimov how to run the pipeline (and is only required if the pipeline constructs its own submission information for the ``htcondor`` scheduler. pyRing does not do this, so we can skip this method in this instance.

``submit_dag``
--------------

The ``submit_dag`` method is used to tell asimov how to submit the job to the scheduler; if we've been able to write a ``build_dag`` method we can simply tell asimov how to submit the dag file it produced, but we'll need to do a bit more work for pyRing.

First we need to look at the normal command-line for pyRing. Normally we run it like this:

``pyring --config config.ini``

where ``config.ini`` is the path to a config file (more on that later).

The executable here is ``pyring``, and the arguments are ``--config config.ini``.

Submission to ``htcondor`` can be handled directly by asimov without the need to write a submit file, but we need to construct the same information in python. We can do this by constructing a description dictionary:

.. code-block:: python

   executable = f"{os.path.join(config.get('pipelines', 'environment'), 'bin', self._pipeline_command)}"
   command = ["--config", ini]

   description = {
           "executable": executable,
           "arguments": " ".join(command),
           "output": f"{name}.out",
           "error": f"{name}.err",
           "log": f"{name}.log",
           "getenv": "True",
           "request_memory": "4096 MB",
           "batch_name": f"{self.name}/{self.production.event.name}/{name}",
           "accounting_group_user": config.get('condor', 'user'),
           "accounting_group": self.production.meta['scheduler']["accounting group"],
           "request_disk": "8192MB",
           "+flock_local": "True",
           "+DESIRED_Sites": htcondor.classad.quote("nogrid"),
   }

this has all of the information which is normally conveyed in the submit file, including the location of error files, and accounting information.

We've also included information at the end of the dictionary which prevents the code from being flocked (e.g. to the OSG or the IGWN pool for LIGO jobs). We'll need to set up file transfers for this to work, which is slightly beyond the scope of this tutorial.

This is the vast majority of the required information, and we can submit this to the cluster with ``job = htcondor.Submit(description)``. We also need to gather the cluster ID from condor to report back to asimov so it can track the job's progress. This is shown in the full code example below, as it requires a little work to identify.

In the full example below I've also written out two extra files; a bash script which contains the full command (this is really helpful for debugging things, so we can run the precise analysis on the command line), and the submit file.

Putting everything together our ``build_dag`` method looks like this:

.. code-block:: python

   def build_dag(self, dryrun=False):
      name = self.production.name
      ini = self.production.event.repository.find_prods(name, self.category)[0]
      meta = self.production.meta
      
      executable = f"{os.path.join(config.get('pipelines', 'environment'), 'bin', self._pipeline_command)}"
      command = ["--config", ini]
      
      description = {
               "executable": executable,
               "arguments": " ".join(command),
               "output": f"{name}.out",
               "error": f"{name}.err",
               "log": f"{name}.log",
               "getenv": "True",
               "request_memory": "4096 MB",
               "batch_name": f"{self.name}/{self.production.event.name}/{name}",
               "accounting_group_user": config.get('condor', 'user'),
               "accounting_group": self.production.meta['scheduler']["accounting group"],
               "request_disk": "8192MB",
               "+flock_local": "True",
               "+DESIRED_Sites": htcondor.classad.quote("nogrid"),
      }
    
       job = htcondor.Submit(description)
       os.makedirs(self.production.rundir, exist_ok=True)
       with set_directory(self.production.rundir):
           os.makedirs("results", exist_ok=True)

           with open(f"{name}.sub", "w") as subfile:
               subfile.write(job.__str__()+r"\n queue")

           with open(f"{name}.sh", "w") as bashfile:
               bashfile.write(str(full_command))

       with set_directory(self.production.rundir):
           try:
               schedulers = htcondor.Collector().locate(htcondor.DaemonTypes.Schedd, config.get("condor", "scheduler"))
           except configparser.NoOptionError:
               schedulers = htcondor.Collector().locate(htcondor.DaemonTypes.Schedd)
           schedd = htcondor.Schedd(schedulers)
           with schedd.transaction() as txn:
               cluster_id = job.queue(txn)

       self.clusterid = cluster_id

Analysis assets
---------------

When our pipeline runs it will probably produce a number of output files and data products. In the case of pyRing one of these files contains the posterior samples from the analysis. We need to tell asimov where to find these outputs; it can then ensure these are passed along to subsequent analyses, and also make them easily available to you.

The ``collect_assets`` method should return a dictionary of all the assets you want to declare to asimov. In the simple case of wishing to only declare the samples file this method can be as simple as this:

.. code-block:: python

       def collect_assets(self):
           """
           Gather all of the results assets for this job.
           """
           return {"samples": os.path.join(self.production.rundir,
                                           "Nested_sampler",
                                           "posterior.dat"),
                   }

Here asimov will return the ``Nested_sampler/posterior.dat`` file in the analysis's run directory. We could (and probably should!) add some additional logic to ensure this file actually exists, but in the interest of simplicity for this tutorial I'll just return the expected path.

Checking for completion
-----------------------

asimov needs to be told how to confirm that a job has completed successfully (simply checking the status of a job on ``htcondor`` is not a reliable way of doing this.

Typically the easiest way to do this is to check for the existence of a result file, or a set of results files. Since we already have the posterior samples file for pyRing available in the dictionary returned by ``collect_assets`` we can simply check the path exists:

.. code-block:: python

       def detect_completion(self):
           """
           Detect if the outputs have been created, and if they have,
           assert that the job is complete.
           """
           if os.path.exists(self.collect_assets().get('samples')):
               return True
           else:
               return False

There might be circumstances where simply checking for the existence of a file is insufficient to demonstrate that an analysis has finished, but you can include arbitrary code in this method to account for that.

Templating your config file
---------------------------

Telling asimov about your pipeline
----------------------------------

Writing blueprints for your pipeline
------------------------------------
