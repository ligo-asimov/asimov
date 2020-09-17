"""BayesWave Pipeline specification."""


import os
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..ini import RunConfiguration
from asimov import config


class BayesWave(Pipeline):
    """
    The BayesWave Pipeline.

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

        if not production.pipeline.lower() == "bayeswave":
            raise PipelineException

        try:
            self.category = config.get("general", "category")
        except:
            self.category = "C01_offline"

    def build_dag(self, user=None):
        """
        Construct a DAG file in order to submit a production to the
        condor scheduler using bayeswave_pipe

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
        """
        # TODO: BayesWave ini file needs the following sections (with example values) to be read from the LALInference ini file:
        #   [input]
        #   seglen=8.0
        #   window=2.0
        #   flow=11
        #   srate=1024
        #   PSDlength=8.0
        #   ifo-list=['H1', 'L1', 'V1']
        #   [datafind]
        #   frtype-list={'H1': 'H1_HOFT_CLEAN_SUB60HZ_C01', 'L1': 'L1_HOFT_CLEAN_SUB60HZ_C01','V1': 'V1Online'}
        #   channel-list={'H1': 'H1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01', 'L1': 'L1:DCS-CALIB_STRAIN_CLEAN_SUB60HZ_C01','V1': 'V1:Hrec_hoft_16384Hz'}

        os.chdir(os.path.join(self.production.event.repository.directory,
                              self.category))
        gps_file = self.production.get_timefile()

        # FIXME currently no distinction between bayeswave and lalinference ini files
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

        ini.set_queue(queue)

        ini.save()

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(os.path.expanduser("~"),
                                  self.production.event.name,
                                  self.production.name)
            self.production.rundir = rundir

        command = ["bayeswave_pipe",
                   "-l", f"{gps_file}",
                   "-r", self.production.rundir,
                   ini.ini_loc
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

    def after_completion(self):
        pass

    def before_submit(self):
        pass

    
    def upload_assets(self):
        """
        Upload the PSDs from this job.
        """
        psds = {}
        detectors = self.production.meta['interferometers']

        git_location = os.path.join(self.category, "psds")
        
        for det in dets:
            asset = f"{self.production.rundir}/ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
            if os.path.exists(asset):
                psds[det] = asset
                self.production.event.production.add_file(
                    asset,
                    os.path.join(git_location, f"psd_{det}.dat"),
                    commit_message = f"Added the PSD for {det}.")
        
