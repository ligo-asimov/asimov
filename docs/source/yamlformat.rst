---------------------
The production ledger
---------------------

In order to construct and monitor on-going PE jobs, asimov stores metadata for each gravitational wave event and for each PE job (or "production" in `asimov` terminology).

These metadata are stored in the event's *production ledger*, which is specified in `yaml` format.

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

``working directory``
+++++++++++++++++++++

The working directory in which run directories for each production should be stored.

For example

.. code-block:: yaml

   working directory: /home/daniel.williams/events/O3/o3b/run_directories/S200224a
   
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

The precise metadata required for each production will vary depending on the pipeline, and any additional data it requries.

It is also possible to specify specific data quality, prior, or data attributes for individual productions by specifying these within the production block.

For example, to set a different sampling rate for ``Prod1`` above:

.. code-block:: yaml
   
   productions:
	- Prod0: 
		status: Wait
		pipeline: bayeswave
		comment: PSD production
	- Prod1:
		status: Wait
		pipeline: lalinference
		quality:
		  sample-rate: 4096    
		comment: IMRPhenomD

Then this production will use 4096-Hz as its sampling rate rather than the default specified in the event's ``quality`` block.

The value of `status` can be used both to track the current state of the production of the job as it is being processed, or to affect its processing.
This defines a simple state machine which is described in :ref:`Asimov state<Asimov's states>`.

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
+ ``lower-frequency``: the lower frequency integration cut-off (f_low), in hertz.
+ ``sample-rate``: the sampling frequency, in hertz
+ ``padding``: the padding to be applied to the data
+ ``window-length``: the window length, in seconds
+ ``reference-frequency``: the reference frequency for the waveform.
+ ``start-frequency``: the lowest frequency at which the waveform should be generated.  

For example:

.. code-block:: yaml

   quality:
     lower-frequency:
       H1: 20
       L1: 20
       V1: 20
     start-frequency: 13.333333333333334
     psd-length: 4.0
     reference-frequency: 20
     sample-rate: 1024
     segment-length: 4.0


The ``supress`` value can be used to specify frequency ranges which should be excluded from the analysis.
This can be used to remove regions with poor calibration from the analysis, and is performed by setting the PSD to zero at these locations.
This must be set on a per-detector basis with the structure below:

.. code-block:: yaml

   quality:
     supress:
       V1:
         lower: 46.0
         upper: 51.0

	
``event time``
++++++++++++++

The geocentric gps time of the event.

For example:

.. code-block:: yaml
		
   event time: 1266618172.401773

``gid``
+++++++

The gracedb ID for the preferred event.

.. code-block:: yaml
		
   gid: G365380

`priors`
++++++++

The prior ranges for the event.

Each parameter can have an upper and lower boundary defined; if no lower or upper bound is to be specified it should be explicitly stated as `None`.

Currently-supported values here are the maximum amplitude order of the waveform (if supported) `amp order`, the chirp mass `chirp-mass`, the component mass `component`, the distance `distance`, and the mass ratio `q`.

.. code-block:: yaml

  priors:
    amp order: 1
    chirp-mass:
    - 22.852486906183355
    - 57.65416902042432
    component:
    - 1
    - 1000
    distance:
    - None
    - 10000
    q:
    - 0.05
    - 1.0



``calibration``
+++++++++++++++

This section should provide the location of the files which define the calibration envelopes for this event.
These should be specified relative to the root of the event's git repository, as defined in the `repository` value.

For example:

.. code-block:: yaml
	
   calibration:
     H1: C01_offline/calibration/H1.dat
     L1: C01_offline/calibration/L1.dat
     V1: C01_offline/calibration/V1.dat

A calibration envelope should be specified for each interferometer which will be used in the analysis.

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
   
``psds``
++++++++

This section records details of all of the PSDs for the event.
These are often added by production processes to the ledger, and will not normally need to be manually specified.

This value takes a nested structure, with the sampling frequency of the PSD used as the primary key, and the interferometer abbreviation as the secondary.

.. code-block:: yaml

   psds:
     1024:
       H1: /home/daniel.williams/events/O3/event_repos/S200224a/C01_offline/psds/1024/H1-psd.dat
       L1: /home/daniel.williams/events/O3/event_repos/S200224a/C01_offline/psds/1024/L1-psd.dat
       V1: /home/daniel.williams/events/O3/event_repos/S200224a/C01_offline/psds/1024/V1-psd.dat



