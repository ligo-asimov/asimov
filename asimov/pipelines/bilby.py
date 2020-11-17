"""Bilby Pipeline specification."""


import os
import glob
import subprocess
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..ini import RunConfiguration
from .. import config
from asimov import logging
import re
import numpy as np

import htcondor

class Bilby(Pipeline):
    """
    The Bilby Pipeline.

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
        super(Bilby, self).__init__(production, category)
        self.logger = logger = logging.AsimovLogger(event=production.event)
        if not production.pipeline.lower() == "bilby":
            raise PipelineException

    def detect_completion(self):
        """
        Check for the production of the posterior file to signal that the job has completed.
        """
        results_dir = glob.glob(f"{self.production.rundir}/result")
        if len(results_dir)>0:
            if len(glob.glob(os.path.join(results_dir[0], f"*_result.json"))) > 0:
                return True
            else:
                return False
        else:
            return False


    def _activate_environment(self):
        """
        Activate the python virtual environment for the pipeline.
        """
        # env = config.get("bilby", "environment")
        # command = ["source", f"{env}/bin/activate"]

        # pipe = subprocess.Popen(command, 
        #                         stdout=subprocess.PIPE,
        #                         stderr=subprocess.STDOUT)
        # out, err = pipe.communicate()

        # if err:
        #     self.production.status = "stuck"
        #     if hasattr(self.production.event, "issue_object"):
        #         raise PipelineException(f"The virtual environment could not be initiated.\n{command}\n{out}\n\n{err}",
        #                                     issue=self.production.event.issue_object,
        #                                     production=self.production.name)
        #     else:
        #         raise PipelineException(f"The virtual environment could not be initiated.\n{command}\n{out}\n\n{err}",
        #                                 production=self.production.name)
        pass

    def _determine_prior(self):
        """
        Determine the correct choice of prior file for this production.
        """

        if "prior file" in self.production.meta:
            return self.production.meta['prior file']
        else:

            DEFAULT_DISTANCE_LOOKUPS = {
                "high_mass": (1e2, 5e3),
                "4s": (1e2, 5e3),
                "8s": (1e2, 5e3),
                "16s": (1e2, 4e3),
                "32s": (1e2, 3e3),
                "64s": (50, 2e3),
                "128s": (1, 5e2),
                "128s_tidal": (1, 5e2),
                "128s_tidal_lowspin": (1, 5e2),
            }
            duration = int(self.production.meta['quality']['segment-length'])
            roq_folder = f"/home/cbc/ROQ_data/IMRPhenomPv2/{duration}s"
            if os.path.isdir(roq_folder) is False:
                self.logger.warning("Requested ROQ folder does not exist")
                return f"{duration}s", None, duration, 20, 1024

            roq_params = np.genfromtxt(os.path.join(roq_folder, "params.dat"), names=True)
    
            scale_factor = 1 # Check this
            template = None
            
            distance_bounds = DEFAULT_DISTANCE_LOOKUPS[str(duration) + "s"]
            mc_min = roq_params["chirpmassmin"] / scale_factor
            mc_max = roq_params["chirpmassmax"] / scale_factor
            comp_min = roq_params["compmin"] / scale_factor
            
            if template is None:
                template = os.path.join(
                    config.get("bilby", "priors"), "roq.prior.template"
            )

            with open(template, "r") as old_prior:
                prior_string = old_prior.read().format(
                    mc_min=mc_min,
                    mc_max=mc_max,
                    comp_min=comp_min,
                    d_min=distance_bounds[0],
                    d_max=distance_bounds[1],
                )
            prior_file = os.path.join(os.getcwd(), f"{self.production.name}.prior")
            with open(prior_file, "w") as new_prior:
                new_prior.write(prior_string)
            return prior_file

        
    def build_dag(self, psds=None, user=None, clobber_psd=False):
        """
        Construct a DAG file in order to submit a production to the
        condor scheduler using bilby_pipe.

        Parameters
        ----------
        production : str
           The production name.
        psds : dict, optional
           The PSDs which should be used for this DAG. If no PSDs are
           provided the PSD files specified in the ini file will be used
           instead.
        user : str
           The user accounting tag which should be used to run the job.

        Raises
        ------
        PipelineException
           Raised if the construction of the DAG fails.
        """

        #self._activate_environment()
        
        os.chdir(os.path.join(self.production.event.repository.directory,
                              self.category))
        gps_file = self.production.get_timefile()
        ini = self.production.event.repository.find_prods(self.production.name,
                                                          self.category)[0]

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(os.path.expanduser("~"),
                                  self.production.event.name,
                                  self.production.name)
            self.production.rundir = rundir

        if "job label" in self.production.meta:
            job_label = self.production.meta['job label']
        else:
            job_label = self.production.name

        prior_file = self._determine_prior()
        
        os.chdir(self.production.event.meta['working directory'])   
        # TODO: Check if bilby supports loading a gps time file
        command = ["bilby_pipe",
                   os.path.join(self.production.event.repository.directory, self.category,  ini),
                   "--label", job_label,
                   "--prior-file", prior_file,
                   "--outdir", self.production.rundir,
                   "--accounting", config.get("bilby", "accounting")
        ]
            
        pipe = subprocess.Popen(command, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        if err or "DAG generation complete, to submit jobs" not in str(out):
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

        Notes
        -----
        This overloads the default submission routine, as bilby seems to store
        its DAG files in a different location
        """
        os.chdir(self.production.event.meta['working directory'])   
        #os.chdir(os.path.join(self.production.event.repository.directory,
        #                      self.category))


        self.before_submit()
        
        try:
            # to do: Check that this is the correct name of the output DAG file for billby (it
            # probably isn't)
            if "job label" in self.production.meta:
                job_label = self.production.meta['job label']
            else:
                job_label = self.production.name
            dag_filename = f"dag_{job_label}.submit"
            command = ["condor_submit_dag",
                       "-batch-name", f"bilby/{self.production.event.name}/{self.production.name}",
                                   os.path.join(self.production.rundir, "submit", dag_filename)]
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

    def collect_assets(self):
        """
        Gather all of the results assets for this job.
        """
        pass

    def samples(self):
        """
        Collect the combined samples file for PESummary.
        """
        return glob.glob(os.path.join(self.production.rundir, "result", "*_merge_result.json"))
        
    def after_completion(self):
        cluster = self.run_pesummary()
        self.production.meta['job id'] = int(cluster)
        self.production.status = "processing"

    def collect_logs(self):
        """
        Collect all of the log files which have been produced by this production and 
        return their contents as a dictionary.
        """
        logs = glob.glob(f"{self.production.rundir}/submit/*.err") + glob.glob(f"{self.production.rundir}/log*/*.err")
        logs += glob.glob(f"{self.production.rundir}/*/*.out")
        messages = {}
        for log in logs:
            with open(log, "r") as log_f:
                message = log_f.read()
                messages[log.split("/")[-1]] = message
        return messages
