==================
Pipeline interface
==================

In order to interact with the various pipelines asimov needs some additional glue code.

An interface for any pipeline can be constructed, provided that pipeline can be submitted to a condor scheduler using a DAG file.

The ``asimov.pipeline`` module defines the factory classes for these interfaces, and individual interfaces can be found in the ``asimov.pipelines`` module.

Supported Pipelines
-------------------

The following pipelines currently have support bundled with asimov:

+ :ref:`lalinference<LALInference pipelines>`
+ :ref:`bayeswave<pipelines/BayesWave pipelines>`
+ ``bilby``
+ ``RIFT``

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
   after_completion() --- Executed once execution has successfully   
