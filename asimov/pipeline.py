"""Defines the interface with generic analysis pipelines."""
import configparser
import os
import subprocess
import time
import warnings

warnings.filterwarnings("ignore", module="htcondor")


import htcondor  # NoQA

from asimov import config, logger, logging  # NoQA

from .storage import Store  # NoQA


class PipelineException(Exception):
    """Exception for pipeline problems."""

    def __init__(self, message, issue=None, production=None):
        super(PipelineException, self).__init__(message)
        self.message = message
        self.issue = issue
        self.production = production

    def __repr__(self):
        text = f"""
An error was detected when assembling the pipeline for a production on this event.
Please fix the error and then remove the `pipeline-error` label from this issue.
<p>
  <details>
     <summary>Click for details of the error</summary>
     <p><b>Production</b>: {self.production}</p>
     <p>{self.message}</p>
  </details>
</p>

- [ ] Resolved
"""
        return text

    def submit_comment(self):
        """
        Submit this exception as a comment on the gitlab
        issue for the event.
        """
        if self.issue:
            self.issue.add_label("pipeline-error", state=False)
            self.issue.add_note(self.__repr__())


class PipelineLogger:
    """Log things for pipelines."""

    def __init__(self, message, issue=None, production=None):
        self.message = message  # .decode()
        self.issue = issue
        self.production = production

    def __repr__(self):
        text = f"""
One of the productions ({self.production}) produced a log message.
It is copied below.
<p>
  <details>
     <summary>Click for details of the message</summary>
     <p><b>Production</b>: {self.production}</p>
     <p>{self.message}</p>
  </details>
</p>
"""
        return text

    def submit_comment(self):
        """
        Submit this exception as a comment on the gitlab
        issue for the event.
        """
        if self.issue:
            self.issue.add_note(self.__repr__())


class Pipeline:
    """
    Factory class for pipeline specification.
    """

    name = "Asimov Pipeline"

    def __init__(self, production, category=None):
        self.production = production

        self.category = production.category
        self.logger = logger

    def __repr__(self):
        return self.name.lower()

    def detect_completion(self):
        """
        Check to see if the job has in fact completed.
        """
        pass

    def before_submit(self, dryrun=False):
        """
        Define a hook to run before the DAG file is generated and submitted.

        Note, this method should be over-written in the specific pipeline implementation
        if required.
        It allows the `dryrun` option to be specified in order to only print the commands
        rather than run them.
        """
        pass

    def after_completion(self):
        """
        Define a hook to run after the DAG has completed execution successfully.

        Note, this method should take no arguments, and should be over-written in the
        specific pipeline implementation if required.
        """
        self.production.status = "finished"
        self.production.meta.pop("job id")

    def collect_assets(self):
        """
        Add the various analysis assets from the run directory to the git repository.
        """
        repo = self.production.event.repository

        for asset in self.assets:
            repo.add_file(asset[0], asset[1])

    def collect_logs(self):
        return {}

    def run_pesummary(self, dryrun=False):
        """
        Run PESummary on the results of this job.
        """

        psds = self.production.psds
        calibration = [
            os.path.join(self.production.event.repository.directory, cal)
            for cal in self.production.meta["data"]["calibration"].values()
        ]
        configfile = self.production.event.repository.find_prods(
            self.production.name, self.category
        )[0]
        command = [
            "--webdir",
            os.path.join(
                config.get("general", "webroot"),
                self.production.event.name,
                self.production.name,
                "results",
            ),
            "--labels",
            self.production.name,
            "--gw",
            "--cosmology",
            config.get("pesummary", "cosmology"),
            "--redshift_method",
            config.get("pesummary", "redshift"),
            "--nsamples_for_skymap",
            config.get("pesummary", "skymap_samples"),
            "--evolve_spins",
            "True",
            "--multi_process",
            "4",
            "--approximant",
            self.production.meta["approximant"],
            "--f_low",
            str(min(self.production.meta["quality"]["minimum frequency"].values())),
            "--f_ref",
            str(self.production.meta["likelihood"]["reference frequency"]),
            "--regenerate",
            "redshift mass_1_source mass_2_source chirp_mass_source"
            " total_mass_source final_mass_source final_mass_source_non_evolved radiated_energy",
            "--config",
            os.path.join(
                self.production.event.repository.directory, self.category, configfile
            ),
        ]
        # Samples
        command += ["--samples"]
        command += self.samples()
        # Calibration information
        command += ["--calibration"]
        command += calibration
        # PSDs
        command += ["--psd"]
        command += psds.values()

        self.logger.info(
            f"Submitted PE summary run. Command: {config.get('pesummary', 'executable')} {' '.join(command)}",
            production=self.production,
            channels=["file"],
        )

        if dryrun:
            print(command)

        submit_description = {
            "executable": config.get("pesummary", "executable"),
            "arguments": " ".join(command),
            "accounting_group": config.get("pipelines", "accounting"),
            "output": f"{self.production.rundir}/pesummary.out",
            "error": f"{self.production.rundir}/pesummary.err",
            "log": f"{self.production.rundir}/pesummary.log",
            "request_cpus": "4",
            "getenv": "true",
            "batch_name": f"PESummary/{self.production.event.name}/{self.production.name}",
            "request_memory": "8192MB",
            "request_disk": "8192MB",
        }

        if dryrun:
            print("SUBMIT DESCRIPTION")
            print("------------------")
            print(submit_description)

        if not dryrun:

            hostname_job = htcondor.Submit(submit_description)

            try:
                # There should really be a specified submit node, and if there is, use it.
                schedulers = htcondor.Collector().locate(
                    htcondor.DaemonTypes.Schedd, config.get("condor", "scheduler")
                )
                schedd = htcondor.Schedd(schedulers)
            except:  # NoQA
                # If you can't find a specified scheduler, use the first one you find
                schedd = htcondor.Schedd()
            with schedd.transaction() as txn:
                cluster_id = hostname_job.queue(txn)

        else:
            cluster_id = 0

        return cluster_id

    def store_results(self):
        """
        Store the PE Summary results
        """

        files = [
            f"{self.production.name}_pesummary.dat",
            "posterior_samples.h5",
            f"{self.production.name}_skymap.fits",
        ]

        for filename in files:
            results = os.path.join(
                config.get("general", "webroot"),
                self.production.event.name,
                self.production.name,
                "results",
                "samples",
                filename,
            )
            store = Store(root=config.get("storage", "directory"))
            store.add_file(
                self.production.event.name, self.production.name, file=results
            )

    def detect_completion_processing(self):
        files = f"{self.production.name}_pesummary.dat"
        results = os.path.join(
            config.get("general", "webroot"),
            self.production.event.name,
            self.production.name,
            "results",
            "samples",
            files,
        )
        if os.path.exists(results):
            return True
        else:
            return False

    def after_processing(self):
        """
        Run the after processing jobs.
        """
        try:
            self.store_results()
            self.production.status = "uploaded"
        except Exception as e:
            raise ValueError(e)

    def eject_job(self):
        """
        Remove a job from the cluster.
        """
        command = ["condor_rm", f"{self.production.meta['job id']}"]
        try:
            dagman = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

        except FileNotFoundError as error:
            raise PipelineException(
                "It looks like condor isn't installed on this system.\n"
                f"""I wanted to run {" ".join(command)}."""
            ) from error

        stdout, stderr = dagman.communicate()
        if not stderr:
            time.sleep(20)
            self.production.meta.pop("job id")

    def clean(self, dryrun=False):
        """
        Remove all of the artefacts from a job from the working directory.
        """
        pass

    def submit_dag(self):
        """
        Submit the DAG for this pipeline.
        """
        raise NotImplementedError

    def resurrect(self):
        pass

    @classmethod
    def read_ini(cls, filepath):
        """
        Read and parse a pipeline configuration file.

        Parameters
        ----------
        filepath: str
           The path to the ini file.
        """

        with open(filepath, "r") as f:
            file_content = f.read()

        config_parser = configparser.RawConfigParser()
        config_parser.read_string(file_content)

        return config_parser

    def check_progress(self):
        pass

    def html(self):
        """
        Return an HTML representation of this pipeline object.
        """

        out = ""
        out += """<div class="asimov-pipeline">"""
        out += f"""<p class="asimov-pipeline-name">{self.name}</p>"""
        out += """</div>"""

        return out

    def collect_pages(self):
        pass
