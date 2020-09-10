"""RIFT Pipeline specification."""


import os
import shutil
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..ini import RunConfiguration
from asimov import config


class Rift(Pipeline):
    """
    The RIFT Pipeline.

    Parameters
    ----------
    production : :class:`asimov.Production`
       The production object.
    category : str, optional
        The category of the job.
        Defaults to "C01_offline".
    """

    STATUS = {"wait", "stuck", "stopped", "running", "finished"}

    def __init__(self, production, category=None):
        super(BayesWave, self).__init__(production, category)

        if not production.pipeline.lower() == "rift":
            raise PipelineException

    def _activate_environment(self):
        """
        Activate the python virtual environment for the pipeline.
        """
        env = config.get("rift", "environment")
        command = ["source", f"{env}/bin/activate"]

        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()

        if err:
            self.production.status = "stuck"
            if hasattr(self.production.event, "issue_object"):
                raise PipelineException(f"The virtual environment could not be initiated.\n{command}\n{out}\n\n{err}",
                                            issue=self.production.event.issue_object,
                                            production=self.production.name)
            else:
                raise PipelineException(f"The virtual environment could not be initiated.\n{command}\n{out}\n\n{err}",
                                        production=self.production.name)
        

    def _convert_psd(self, ascii_format):
        """
        Convert an ascii format PSD to XML.

        Parameters
        ----------
        ascii_format : str
           The location of the ascii format file.
        """
        self._activate_environment()
        
        
                   
        command = ["convert_psd_ascii2xml",
                   "--fname-psd-ascii", f"{ascii_format}",
                   "--conventional-postfix",
                   "--ifo",  f"{ifo}"]
            
        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        if err:
            self.production.status = "stuck"
            if hasattr(self.production.event, "issue_object"):
                raise PipelineException(f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err}",
                                            issue=self.production.event.issue_object,
                                            production=self.production.name)
            else:
                raise PipelineException(f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err}",
                                        production=self.production.name)
            
    def before_submit(self):
        """
        Convert the text-based PSD to an XML psd if the xml doesn't exist already.
        """
        category = "C01_offline" # Fix me: this shouldn't be hard-coded
        if len(production.get_psds("xml"))==0:
            for ifo in production.meta['interferometers']:
                os.chdir(f"{event.repository.directory}/{category}")
                os.mkdir(f"psds")
                os.chdir("psds")
                self._convert_psd(production['psds'][ifo])
                event.repository.repo.git.add(f"{ifo.upper()}-psd.xml")
            event.repository.repo.git.commit("Added converted xml psds")
            event.repository.repo.git.push()
            

    def build_dag(self, user=None):
        """
        Construct a DAG file in order to submit a production to the
        condor scheduler using util_RIFT_pseudo_pipe.py

        Parameters
        ----------
        production : str
           The production name.
        user : str
           The user accounting tag which should be used to run the job.

        Raises
        ------
        PipelineException
           Raised if the construction of the DAG fails.

        Notes
        -----

        In order to assemble the pipeline the RIFT runner requires additional
        production metadata: at least the l_max value.
        An example RIFT production specification would then look something like:
        
        ::
           
           - Prod0:
               rundir: {0}/tests/tmp/s000000xx/Prod0
               pipeline: rift
               approximant: IMRPhenomPv3
               lmax: 2
               cip jobs: 5 # This is optional, and will default to 3
               comment: RIFT production run.
               status: wait

        
        """

        self._activate_environment()
        
        os.chdir(os.path.join(self.production.event.repository.directory,
                              self.category))
        gps_file = self.production.get_timefile()
        coinc_file = self.production.get_coincfile()
        
        ini = self.production.get_configuration()

        if not user:
            if self.production.get_meta("user"):
                user = self.production.get_meta("user")
        else:
            user = ini._get_user()
            self.production.set_meta("user", user)

        ini.update_accounting(user)

        if 'queue' in self.production.meta:
            queue = self.production.meta['queue']
        else:
            queue = 'Priority_PE'

        # FIXME Really we don't want this to be hard-coded.
        calibration = "C01"

        approximant = self.production.meta['approximant']
        
        ini.set_queue(queue)

        ini.save()

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(os.path.expanduser("~"),
                                  self.production.event.name,
                                  self.production.name)
            self.production.rundir = rundir

        # TODO lmax needs to be determined for each waveform (it's the maximum harmonic order)
        # for now it will be fetched from the production metadata
        lmax = self.production.meta['lmax']
        
        if "cip jobs" in self.production.meta:
            cip = self.production.meta['cip jobs']
        else:
            cip = 3
            
        # TODO The main command-line for RIFT-pseudo-pipe takes a $@ from its script, so this may be missing some things!
        command = ["util_RIFT_pseudo_pipe.py",
                   "--use-coinc", f"{coinc_file}",
                   "--l-max", f"{lmax}",
                   "--calibration", f"{calibration}",
                   "--add-extrinsic",
                   "--archive-pesummary-label", "{calibration}:{approximant}",
                   "--archive-pesummary-event-label", "{calibration}:{approximant}",
                   "--cip-explode-jobs", cip,
                   "--use-rundir", self.production.rundir,
                   "--use-ini", ini.ini_loc
        ]
            
        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        if err or "Successfully created DAG file." not in str(out):
            self.production.status = "stuck"
            if hasattr(self.production.event, "issue_object"):
                raise PipelineException(f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                                            issue=self.production.event.issue_object,
                                            production=self.production.name)
            else:
                raise PipelineException(f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                                        production=self.production.name)
        else:
            if hasattr(self.production.event, "issue_object"):
                return PipelineLogger(message=out,
                                      issue=self.production.event.issue_object,
                                      production=self.production.name)
            else:
                return PipelineLogger(message=out,
                                      production=self.production.name)
