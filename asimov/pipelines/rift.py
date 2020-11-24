"""RIFT Pipeline specification."""

import re
import os
import shutil
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..ini import RunConfiguration
from asimov import config
from asimov import logging


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
        super(Rift, self).__init__(production, category)
        self.logger = logger = logging.AsimovLogger(event=production.event)
        if not production.pipeline.lower() == "rift":
            raise PipelineException
        
        if "bootstrap" in self.production.meta:
            self.bootstrap = self.production.meta
        else:
            self.bootstrap = False

    def _activate_environment(self):
        """
        Activate the python virtual environment for the pipeline.
        """
        env = config.get("rift", "environment")
        command = ["/bin/bash", "-c", "source", f"{env}/bin/activate"]

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
        
    def after_completion(self):
        cluster = self.run_pesummary()
        self.production.meta['job id'] = int(cluster)
        self.production.status = "processing"


    def _convert_psd(self, ascii_format, ifo):
        """
        Convert an ascii format PSD to XML.

        Parameters
        ----------
        ascii_format : str
           The location of the ascii format file.
        ifo : str
           The IFO which this PSD is for.
        """
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
        event = self.production.event
        category = config.get("general", "calibration_directory")
        
        if len(self.production.get_psds("xml"))==0:
            for ifo in self.production.meta['interferometers']:
                os.chdir(f"{event.repository.directory}/")
                sample = self.production.meta['quality']['sample-rate']
                self._convert_psd(self.production.meta['psds'][sample][ifo], ifo)
                asset = f"{ifo.upper()}-psd.xml.gz"
                git_location = os.path.join(category, "psds")
                self.production.event.repository.add_file(
                    asset,
                    os.path.join(git_location, str(sample), f"psd_{ifo}.xml.gz"),
                    commit_message = f"Added the xml format PSD for {ifo}.")
            

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
           
           - Prod3:
               rundir: tests/tmp/s000000xx/Prod3
               pipeline: rift
               approximant: IMRPhenomPv3
               lmax: 2
               cip jobs: 5 # This is optional, and will default to 3
               bootstrap: Prod1
               bootstrap fmin: 20
               needs: Prod1
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

        os.environ['LIGO_USER_NAME'] = user
        os.environ['LIGO_ACCOUNTING'] = config.get('pipelines', 'accounting')

        try:
            calibration = config.get("general", "calibration")
        except:
            calibration = "C01"

        approximant = self.production.meta['approximant']

        ini.save()

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(os.path.expanduser("~"),
                                  self.production.event.name,
                                  self.production.name)
            self.production.rundir = rundir

        lmax = self.production.meta['lmax']
        
        if "cip jobs" in self.production.meta:
            cip = self.production.meta['cip jobs']
        else:
            cip = 3
            
        
        command = [os.path.join(config.get("pipelines", "environment"), "bin", "util_RIFT_pseudo_pipe.py"),
                   "--use-coinc", os.path.join(self.production.event.repository.directory, "C01_offline",
                                               coinc_file),
                   "--l-max", f"{lmax}",
                   "--calibration", f"{calibration}",
                   "--add-extrinsic",
                   "--approx", f"{approximant}",
                   "--cip-explode-jobs", str(cip),
                   "--use-rundir", self.production.rundir,
                   "--use-ini", os.path.join(self.production.event.repository.directory, "C01_offline",  ini.ini_loc)
        ]

        # Placeholder LI grid bootstrapping; conditional on it existing and location specification
        
        if self.bootstrap:

            # Find the appropriate production in the ledger
            productions = self.production.event.productions
            bootstrap_production = [production for production in productions if production.name == self.bootstrap]

            if len(bootstrap_production) == 0:
                raise PipelineException(f"Unable to find the bootstrapping production for {self.production.name}.",
                                        issue=self.production.event.issue_object,
                                        production=self.production.name)
            else:
                bootstrap_production = bootstrap_production[0]
            
            shutil.copy(f"{bootstrap_production.rundir}/posterior_samples.dat", f"{self.production.rundir}/LI_samples.dat")
            convcmd = ["convert_output_format_inferance2ile",
                       "--posterior-samples", f"{self.production.rundir}/LI_samples.dat",
                       "--output-xml", f"bootstrap-grid.xml.gz",
                       "--fmin", f"{self.production.meta['bootstrap fmin']}"] 
            pipe = subprocess.Popen(convcmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            out,err = pipe.communicate()
            if err:
                self.production.status = "stuck"
                if hasattr(self.production.event, "issue_object"):
                    raise PipelineException(f"Unable to convert LI posterior into ILE starting grid.\n{convcmd}\n{out}\n\n{err}",
                                            issue=self.production.event.issue_object,
                                            production=self.production.name)
                else:
                    raise PipelineException(f"Unable to convert LI posterior into ILE starting grid.\n{convcmd}\n{out}\n\n{err}",
                                        production=self.production.name)
            else:
                command += ["--manual-initial-grid", os.path.join(self.production.rundir, "bootstrap-grid.xml.gz")]
        
        self.logger.info(command, production = self.production)
        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()


        if err:
            self.production.status = "stuck"
            if hasattr(self.production.event, "issue_object"):
                self.logger.info(out, production = self.production)
                self.logger.error(err, production = self.production)
                raise PipelineException(f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                                            issue=self.production.event.issue_object,
                                            production=self.production.name)
            else:
                self.logger.info(out, production = self.production)
                self.logger.error(err, production = self.production)
                raise PipelineException(f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                                        production=self.production.name)
        else:
            #os.makedirs(self.production.rundir, exist_ok=True)
            os.chdir(self.production.rundir)
            for psdfile in self.production.get_psds("xml"):
                ifo = psdfile.split("/")[-1].split("_")[1].split(".")[0]
                os.system(f"cp {psdfile} {ifo}-psd.xml.gz")

            os.system("cat *_local.cache > local.cache")

            if hasattr(self.production.event, "issue_object"):
                return PipelineLogger(message=out,
                                      issue=self.production.event.issue_object,
                                      production=self.production.name)
            else:
                return PipelineLogger(message=out,
                                      production=self.production.name)
    
    def submit_dag(self):
        """
        Submit a DAG file to the condor cluster (using the RIFT dag name). This is an overwrite of the near identical parent function submit_dag()

        Parameters
        ----------
        category : str, optional
           The category of the job.
           Defaults to "C01_offline".
        production : str
           The production name.

        Returns
        -------
        int
           The cluster ID assigned to the running DAG file.
        PipelineLogger
           The pipeline logger message.

        Raises
        ------
        PipelineException
           This will be raised if the pipeline fails to submit the job.
        """
        os.chdir(self.production.rundir)
        self.before_submit()
         
        try:
            command = ["condor_submit_dag", 
                       "-batch-name", f"rift/{self.production.event.name}/{self.production.name}",
                       os.path.join(self.production.rundir, "marginalize_intrinsic_parameters_BasicIterationWorkflow.dag")]
            dagman = subprocess.Popen(command,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
        except FileNotFoundError as error:
            raise PipelineException("It looks like condor isn't installed on this system.\n"
                                    f"""I wanted to run {" ".join(command)}.""")

        stdout, stderr = dagman.communicate()


        if "submitted to cluster" in str(stdout):
            cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
            self.production.status = "running"
            self.production.job_id = int(cluster)
            return cluster, PipelineLogger(stdout)
        else:
            raise PipelineException(f"The DAG file could not be submitted.\n\n{stdout}\n\n{stderr}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)

    def resurrect(self):
        """
        Attempt to ressurrect a failed job.
        """
        try:
            count = self.production.meta['resurrections']
        except:
            count = 0
        if (count < 5) and (len(glob.glob(os.path.join(self.production.rundir, "marginalize_intrinsic_parameters_BasicIterationWorkflow.dag.rescue*")))>0):
            count +=1
            self.submit_dag()

    def collect_logs(self):
        """
        Collect all of the log files which have been produced by this production and 
        return their contents as a dictionary.
        """
        logs = glob.glob(f"{self.production.rundir}/*.err") #+ glob.glob(f"{self.production.rundir}/*/logs/*")
        logs += glob.glob(f"{self.production.rundir}/*.out")
        messages = {}
        for log in logs:
            with open(log, "r") as log_f:
                message = log_f.read()
                messages[log.split("/")[-1]] = message
        return messages
