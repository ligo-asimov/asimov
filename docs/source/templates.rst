Making pipeline configurations
==============================

Asimov is capable of producing configuration files for its supported pipelines using pre-made template files.

Set Up
------

In order to allow ``asimov`` to discover templates the directory containing them should be provided in the configuration file for the package (i.e. ``/etc/asimov.conf``, ``~/.asimov``, or ``./asimov.conf``).

This should be stored in the ``templating>directory`` variable, e.g.

::

   [templating]
   directory = config-templates


Writing templates
-----------------

Templating in ``asimov`` is handled by the ``liquidpy`` (https://liquidpy.readthedocs.io/en/latest/) templating engine, which implements a non-strict superset of the liquid templating language.

The template has access to all of the metadata for a given production, as specified in its YAML block.

The template should be saved in the templates directory with the name ``<PIPELINE>.ini``, with ``<PIPELINE>`` replaced with the name of the pipeline, e.g. ``lalinference.ini``.


Example template
----------------

This is an example of a template for a ``lalinference`` job.

::

   {# This is a template file for LALInference Pipe #}
   [analysis]
   ifos={{ production.meta['interferometers'] }}
   engine={{ production.meta['engine'] }}
   nparallel=4
   roq = False
   coherence-test=False
   upload-to-gracedb=False
   singularity=False
   osg=False


   [paths]
   webdir=


   [input]
   max-psd-length=10000
   padding=16
   minimum_realizations_number=8
   events=all
   analyse-all-time=False
   timeslides=False
   ignore-gracedb-psd=True
   threshold-snr=3
   gps-time-file = 
   ignore-state-vector = True 

   [condor]
   lalsuite-install=/cvmfs/oasis.opensciencegrid.org/ligo/sw/conda/envs/igwn-py37-20200118/
   datafind=%(lalsuite-install)s/bin/gw_data_find
   mergeNSscript=%(lalsuite-install)s/bin/lalinference_nest2pos
   mergeMCMCscript=%(lalsuite-install)s/bin/cbcBayesMCMC2pos
   combinePTMCMCh5script=%(lalsuite-install)s/bin/cbcBayesCombinePTMCMCh5s
   resultspage=%(lalsuite-install)s/bin/cbcBayesPostProc
   segfind=%(lalsuite-install)s/bin/ligolw_segment_query
   ligolw_print=%(lalsuite-install)s/bin/ligolw_print
   coherencetest=%(lalsuite-install)s/bin/lalinference_coherence_test
   lalinferencenest=%(lalsuite-install)s/bin/lalinference_nest
   lalinferencemcmc=%(lalsuite-install)s/bin/lalinference_mcmc
   lalinferencebambi=%(lalsuite-install)s/bin/lalinference_bambi
   lalinferencedatadump=%(lalsuite-install)s/bin/lalinference_datadump
   ligo-skymap-from-samples=%(lalsuite-install)s/bin/ligo-skymap-from-samples
   ligo-skymap-plot=%(lalsuite-install)s/bin/ligo-skymap-plot
   processareas=%(lalsuite-install)s/bin/process_areas
   computeroqweights=%(lalsuite-install)s/bin/lalinference_compute_roq_weights
   mpiwrapper=%(lalsuite-install)s/bin/lalinference_mpi_wrapper
   gracedb=%(lalsuite-install)s/bin/gracedb
   ppanalysis=%(lalsuite-install)s/bin/cbcBayesPPAnalysis
   pos_to_sim_inspiral=%(lalsuite-install)s/bin/cbcBayesPosToSimInspiral

   mpirun = %(lalsuite-install)s/bin/mpirun

   accounting_group=ligo.prod.o3.cbc.pe.lalinference
   accounting_group_user=

   [datafind]
   url-type=file
   types = {'H1': '{{ production.meta['data']['frame-types']['H1'] }}', 'L1': '{{ production.meta['data']['frame-types']['L1'] }}', 'V1': '{{ production.meta['data']['frame-types']['V1'] }}'}

   [data]
   channels = {'H1': '{{ production.meta['data']['channels']['H1'] }}','L1': '{{ production.meta['data']['channels']['L1'] }}', 'V1': '{{ production.meta['data']['channels']['V1'] }}'}

   [lalinference]
   flow = {'H1': {{ production.meta['quality']['lower-frequency']['H1'] }}, 'L1': {{ production.meta['quality']['lower-frequency']['L1']}},  'V1': {{ production.meta['quality']['lower-frequency']['V1']}} }
   {# fake-cache = {'H1':'/home/geraint.pratten/O3/S190924h/Caches/H-H1_HOFT_C01_CACHE-1253326730-17.lcf', 'L1':'/home/geraint.pratten/O3/S190924h/Caches/L-L1_HOFT_C01_T1700406_v4-1253322752-4096.lcf','V1':'/home/geraint.pratten/O3/S190924h/Caches/V-V1O3Repro1A_CACHE-1253326730-17.lcf'} #}
   [engine]

   fref=20
   approx = {{ production.meta['approximant'] }}
   amporder = 0

   seglen = {{ production.meta['quality']['segment-length'] }}
   srate =  {{ production.meta['quality']['sample-rate'] }}

   neff=1000
   nlive=2048
   maxmcmc = 5000
   tolerance=0.1
   ntemps=8
   resume=
   adapt-temps=
   progress=

   enable-spline-calibration =
   spcal-nodes = 10
   {% if "H1" in production.meta['interferometers'] %}H1-spcal-envelope = {{ production.meta['calibration']['H1'] }}{% endif %}
   {% if "L1" in production.meta['interferometers'] %}L1-spcal-envelope = {{ production.meta['calibration']['L1'] }}{% endif %}
   {% if "V1" in production.meta['interferometers'] %}V1-spcal-envelope = {{ production.meta['calibration']['V1'] }}{% endif %}

   {% if "H1" in production.psds %}H1-psd = {{ production.psds['H1'] }}{% endif %}
   {% if "L1" in production.psds %}L1-psd = {{ production.psds['L1'] }}{% endif %}
   {% if "V1" in production.psds %}V1-psd = {{ production.psds['V1'] }}{% endif %}

   a_spin1-max = 0.99
   a_spin2-max = 0.99

   chirpmass-min = 6
   chirpmass-max = 7
   q-min = 0.0555555556
   comp-min = 1
   comp-max = 50

   distance-max = 1500

   {#
   # Uncomment lines below when running aligned-spin approximants
   # aligned-spin =
   # alignedspin-zprior =
   #}

   [mpi]
   mpi_task_count=8
   machine-count=8
   machine-memory=4000

   [bayeswave]
   Niter = 4000000
   Nchain = 20
   Dmax = 200

   [skyarea]
   maxpts=2000

   [resultspage]
   skyres=0.5
   deltaLogP = 7.5

   [statevector]
   state-vector-channel={'H1': 'H1:GDS-CALIB_STATE_VECTOR_C01', 'L1': 'L1:GDS-CALIB_STATE_VECTOR_C01', 'V1': 'V1:DQ_ANALYSIS_STATE_VECTOR'}
   bits=['Bit 0', 'Bit 1', 'Bit 2']

   [ligo-skymap-from-samples]
   enable-multiresolution=

   [ligo-skymap-plot]
   annotate=
   contour= 50 90
