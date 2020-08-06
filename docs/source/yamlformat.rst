----------------------------
The event specification format
----------------------------

In order to construct and monitor on-going PE jobs, asimov stores metadata for each gravitational wave event and for each PE job (or "production" in asimov terminology).

A number of fields are required for `asimov` to correctly process an event, while a number of additional fields will allow it to perform more operations automatically, or over-ride defaults.

Required fields
~~~~~~~~~~~~~~~


``name``
++++++++

This field must contain the name of the event.
For example:

.. code-block:: yaml
   
   name: S200311bg


``repository``
++++++++++++++

This field should contain an https link to this event's git repository where production specification files, and data are stored.
For example:

.. code-block:: yaml
   
   repository: https://git.ligo.org/pe/O3/S200311bg

Optional fields
~~~~~~~~~~~~~~~

``productions``
+++++++++++++++

This field should contain a list of named productions which should be (or are) running on this event.
Details of the format of each production are included :ref:`in the productions section<Production Format>`.

For example:

.. code-block:: yaml
   
   productions:
	- Prod0: 
		- status: Wait
		- pipeline: bayeswave
		- comment: PSD production
	- Prod1:
		- status: Wait
		- pipeline: lalinference
		- comment: IMRPhenomD
	- Prod2:
		- status: Wait
		- pipeline: bilby
		- comment: NRSur
		- needs:
		  - Prod0


Production format
~~~~~~~~~~~~~~~~~

The details of each production should be included in a named list.
Each production MUST have a name, a status, and a pipeline.
Other values MAY also be included, and these will be passed to the appropriate pipeline management infrastructure.

The basic format of each production is

.. code-block:: yaml
   
   - <NAME>:
         - status: <STATUS>
	 - pipeline: <PIPELINE>
	 - needs: <PRODUCTION NAME>

The value of ``pipeline`` MUST be one of the analysis pipelines supported by asimov.
A list of these can be found on the :ref:`Supported Pipelines` page.

The value of ``status`` MAY either be one of the values listed on the :ref:`Standard Statuses` page, or may be specific to a given pipeline. The value of this field will be updated by the monitoring script as the job runs, but may also be changed to affect the behaviour of the analysis process.

Dependencies for jobs can be specified using the value of ``needs``. This field is optional.
If a production, or list of productions is provided, a directed acyclic graph (DAG) will be constructed to prevent the execution of jobs before their dependency jobs have been marked as finished.
