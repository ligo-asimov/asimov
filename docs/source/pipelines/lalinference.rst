LALInference Pipelines
======================

Asimov provides full support for the LALInference pipeline.
While LALInference has been largely superseded by newer sampling techniques it can still be helpful to be able to run jobs using it both for carrying-out cross checks, and for replicating older analyses.

Review status
-------------

.. info::
   The current integration with LALInference is fully reviewed and is suitable for use in collaboration analyses. 

Examples
--------

LALInference with Markov Chain Monte Carlo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   - Prod0:
       pipeline: lalinference
       approximant: IMRPhenomXPHM
       nparallel: 25
       engine: lalinferencemcmc
       status: ready

LALInference with Nested sampling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
       
.. code-block:: yaml

   - Prod0:
       pipeline: lalinference
       approximant: IMRPhenomXPHM
       nparallel: 25
       engine: lalinferencenest
       status: ready
