"""BayesWave Pipeline specification."""


import os
import re
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..ini import RunConfiguration
from ..git import AsimovFileNotFound
from ..storage import Store
from asimov import config
from shutil import copyfile


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
        try:
            gps_file = self.production.get_timefile()
        except AsimovFileNotFound:
            if "event time" in self.production.meta:
                gps_time = self.production.get_meta("event time")
                with open("gpstime.txt", "w") as f:
                    f.write(str(gps_time))
                gps_file = os.path.join(f"{self.production.category}", f"gpstime.txt")
                self.production.event.repository.add_file(f"gpstime.txt", gps_file)
            else:
                raise PipelineException("Cannot find the event time.")
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

        try:
            pathlib.Path(directory).mkdir(parents=True, exist_ok=False)
        except:
            pass

        gps_time = self.production.get_meta("event time")
            

        pipe_cmd = os.path.join(config.get("pipelines", "environment"), "bin", "bayeswave_pipe")

        command = [pipe_cmd,
                   #"-l", f"{gps_file}",
                   f"--trigger-time={gps_time}",
                   "-r", self.production.rundir,
                   ini.ini_loc
        ]
            
        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        if "To submit:" not in str(out):
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

    def detect_completion(self):
         results_dir = glob.glob(f"{self.production.rundir}/trigtime_*")
         if len(results_dir)>0:
             if len(glob.glob(os.path.join(results_dir[0], "post", "clean", f"glitch_median_PSD_forLI_*.dat"))) > 0:
                 return True
             else:
                 return False
         else:
             return False
            
    def after_completion(self):
        self.collect_assets()

        if "supress" in self.production.meta:
            for ifo in self.production.meta['supress']:
                self.supress_psd(ifo, 
                                 self.production.meta['supress'][ifo]['lower'],
                                 self.production.meta['supress'][ifo]['upper'])
        
    def before_submit(self):
        pass


    def submit_dag(self):
        """
        Submit a DAG file to the condor cluster.

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
                       "-batch-name", f"bwave/{self.production.event.name}/{self.production.name}",
                                   os.path.join(self.production.rundir, f"{self.production.name}.dag")]
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
            self.production.job_id = cluster
            return cluster, PipelineLogger(stdout)
        else:
            raise PipelineException(f"The DAG file could not be submitted.\n\n{stdout}\n\n{stderr}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)
    
    def upload_assets(self):
        """
        Upload the PSDs from this job.
        """
        psds = {}
        detectors = self.production.meta['interferometers']
        sample = self.production.meta["quality"]["sample-rate"]
        git_location = os.path.join(self.category, "psds")
        
        for det in dets:
            asset = f"{self.production.rundir}/ROQdata/0/BayesWave_PSD_{det}/post/clean/glitch_median_PSD_forLI_{det}.dat"
            if os.path.exists(asset):
                psds[det] = asset
                self.production.event.repository.add_file(
                    asset,
                    os.path.join(git_location, str(sample), f"psd_{det}.dat"),
                    commit_message = f"Added the PSD for {det}.")

    def collect_logs(self):
        """
        Collect all of the log files which have been produced by this production and 
        return their contents as a dictionary.
        """
        logs = glob.glob(f"{self.production.rundir}/logs/*.err") + glob.glob(f"{self.production.rundir}/*.err")
        messages = {}
        for log in logs:
            with open(log, "r") as log_f:
                message = log_f.read()
                messages[log.split("/")[-1]] = message
        return messages
                
        
    def collect_assets(self):
        """
        Collect the assets for this job and commit them to the event repository.
        Since this job also generates the PSDs these should be added to the production ledger.
        """
        results_dir = glob.glob(f"{self.production.rundir}/trigtime_*")[0]
        sample_rate = self.production.meta['quality']['sample-rate']

        store = Store(root=config.get("storage", "directory"))
        
        for det in self.production.meta['interferometers']:
            asset = os.path.join(results_dir, "post", "clean", f"glitch_median_PSD_forLI_{det}.dat")
            destination = os.path.join(self.category, "psds", str(sample_rate), f"{det}-psd.dat")

            try:
                self.production.event.repository.add_file(asset, destination)
            except Exception as e:
                raise PipelineException(f"There was a problem committing the PSD for {det} to the repository.\n\n{e}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)

            # Add to the event ledger
            if "psds" not in self.production.event.meta:
                self.production.event.meta['psds'] = {}
            if sample_rate not in self.production.event.meta['psds']:
                self.production.event.meta['psds'][sample_rate] = {}
                
            self.production.event.meta['psds'][sample_rate][det] = destination
            # Let's have a better way of doing this
            # TODO improve the event metadata interface
            self.production.event.issue_object.update_data()
            copyfile(asset, f"{det}-{sample_rate}-psd.dat")
            store.add_file(self.production.event.name, self.production.name,
                           file = f"{det}-{sample_rate}-psd.dat")
            
    def supress_psd(self, ifo, fmin, fmax):
        """
        Suppress portions of a PSD.
        Author: Carl-Johan Haster - August 2020
        """
        sample_rate = self.production.meta['quality']['sample-rate']
        orig_PSD_file = np.genfromtxt(os.path.join(self.production.event.repository.directory, self.category, "psds", sample_rate, f"{ifo}-psd.dat"))

        freq = orig_PSD_file[:,0]
        PSD = orig_PSD_file[:,1]

        suppression_region = np.logical_and(np.greater_equal(freq, fmin), np.less_equal(freq, fmax))

        #Suppress the PSD in this region

        PSD[suppression_region] = 1.

        new_PSD = np.vstack([freq, PSD]).T

        asset = f"{ifo}-psd.dat"
        np.savetxt(asset, new_PSD, fmt='%+.5e')
        
        destination = os.path.join(self.category, "psds", str(sample_rate), f"{det}-psd.dat")

        try:
            self.production.event.repository.add_file(asset, destination, message=f"Added the supresed {ifo} PSD")
        except Exception as e:
            raise PipelineException(f"There was a problem committing the suppresed PSD for {det} to the repository.\n\n{e}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)
        copyfile(asset, f"{det}-{sample_rate}-psd-suppresed.dat")
        store.add_file(self.production.event.name, self.production.name,
                       file = f"{det}-{sample_rate}-psd-suppresed.dat")
