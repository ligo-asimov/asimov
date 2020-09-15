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

``interferometers``
+++++++++++++++++++

This section should provide a list of interferometers which are to be included in the analysis for a given event.
The normal two-character identifier should be used here, e.g. "H1" for the 4-km detector at LIGO Hanford Observatory.
For example:

.. code-block:: yaml

   interferometers: ['L1', 'H1', 'K1']

``quality``
+++++++++++

This section will store detector characterisation and data quality information which is relevant to this event.
``asimov`` will recognise a number of fields stored in this section.

+ ``psd-length``: the length of the PSD in seconds.
+ ``segment-length``: the length of the analysis segment, in seconds.
+ ``lower-frequency``: the lower frequency cut-off (f_low), in hertz.
+ ``sample-rate``: the sampling frequency, in hertz
+ ``padding``: the padding to be applied to the data
+ ``window-length``: the window length, in seconds

For example:

.. code-block:: yaml

   quality:
      - psd-length: 8.0
      - segment-length: 8.0
      - lower-frequency: 11
      - sample-rate: 1024
      - window-length: 2.0


``data``
+++++++++

This section should provide details of where the data for this event are located.

This information will be used to generate production configurations.

The two sections which ``asimov`` understands for this section are ``frame-types`` and ``channels``.

+ ``frame-types`` should be a list of key:value pairs for each detector's frame type (see the example below)
+ ``channels`` should be a list of key:value pairs for each detector's data channel (see the example below)

.. code-block:: yaml

   data:
      - frame-types:
	- H1: 'H1_HOFT_CLEAN_SUB60HZ_C01'
	- L1: 'L1_HOFT_CLEAN_SUB60HZ_C01'
	- V1: 'V1Online'
      - channels:
	- H1: 'H1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01'
	  L1: 'L1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01'
	  V1: 'V1:Hrec_hoft_16384Hz'
   
