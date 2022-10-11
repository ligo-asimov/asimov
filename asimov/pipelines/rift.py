"""RIFT Pipeline specification."""

import configparser
import glob
import os
import re
import subprocess

from ligo.gracedb.rest import HTTPError

from asimov import config, logger
from asimov.utils import set_directory

from ..pipeline import Pipeline, PipelineException, PipelineLogger


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

    name = "RIFT"
    STATUS = {"wait", "stuck", "stopped", "running", "finished"}

    def __init__(self, production, category=None):
        super(Rift, self).__init__(production, category)
        self.logger = logger
        if not production.pipeline.lower() == "rift":
            raise PipelineException

        if "bootstrap" in self.production.meta:
            self.bootstrap = self.production.meta["bootstrap"]
        else:
            self.bootstrap = False

    def after_completion(self):
        self.logger.info(
            "Job has completed. Running PE Summary.",
            production=self.production,
            channels=["mattermost"],
        )
        cluster = self.run_pesummary()
        self.production.meta["job id"] = int(cluster)
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
        command = [
            "convert_psd_ascii2xml",
            "--fname-psd-ascii",
            f"{ascii_format}",
            "--conventional-postfix",
            "--ifo",
            f"{ifo}",
        ]

        pipe = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        out, err = pipe.communicate()
        self.logger.info(command, production=self.production)
        if err:
            self.production.status = "stuck"
            if hasattr(self.production.event, "issue_object"):
                raise PipelineException(
                    f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err}",
                    issue=self.production.event.issue_object,
                    production=self.production.name,
                )
            else:
                raise PipelineException(
                    f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err}",
                    production=self.production.name,
                )

    def before_submit(self, dryrun=False):
        """
        Convert the text-based PSD to an XML psd if the xml doesn't exist already.
        """
        event = self.production.event
        category = config.get("general", "calibration_directory")
        if len(self.production.get_psds("xml")) == 0 and "psds" in self.production.meta:
            for ifo in self.production.meta["interferometers"]:
                with set_directory(f"{event.work_dir}"):
                    sample = self.production.meta["quality"]["sample-rate"]
                    self._convert_psd(
                        self.production.meta["psds"][sample][ifo], ifo, dryrun=dryrun
                    )
                    asset = f"{ifo.upper()}-psd.xml.gz"
                    git_location = os.path.join(category, "psds")
                    self.production.event.repository.add_file(
                        asset,
                        os.path.join(git_location, str(sample), f"psd_{ifo}.xml.gz"),
                        commit_message=f"Added the xml format PSD for {ifo}.",
                    )

    def build_dag(self, user=None, dryrun=False):
        """
        Construct a DAG file in order to submit a production to the
        condor scheduler using util_RIFT_pseudo_pipe.py

        Parameters
        ----------
        user : str
           The user accounting tag which should be used to run the job.
        dryrun: bool
           If set to true the commands will not be run, but will be printed to standard output. Defaults to False.

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
        cwd = os.getcwd()
        if self.production.event.repository:
            try:

                coinc_file = self.production.get_coincfile()
                calibration = config.get("general", "calibration_directory")
                coinc_file = os.path.join(
                    self.production.event.repository.directory, calibration, coinc_file
                )
            except HTTPError:
                print(
                    "Unable to download the coinc file because it was not possible to connect to GraceDB"
                )
                coinc_file = "COINC MISSING"

            try:

                ini = self.production.get_configuration().ini_loc
                calibration = config.get("general", "calibration_directory")
                ini = os.path.join(
                    self.production.event.repository.directory, calibration, ini
                )
            except ValueError:
                print(
                    "Unable to find the configuration file. Have you run `$ asimov manage build` yet?"
                )
                ini = "INI MISSING"
        else:
            ini = "INI MISSING"
            coinc_file = os.path.join(cwd, "coinc.xml")

        if self.production.get_meta("user"):
            user = self.production.get_meta("user")
        else:
            user = config.get("condor", "user")
            self.production.set_meta("user", user)

        os.environ["LIGO_USER_NAME"] = f"{user}"
        os.environ["LIGO_ACCOUNTING"] = f"{config.get('pipelines', 'accounting')}"

        try:
            calibration = config.get("general", "calibration")
        except configparser.NoOptionError:
            calibration = "C01"

        approximant = self.production.meta["approximant"]

        if self.production.rundir:
            rundir = os.path.relpath(self.production.rundir, os.getcwd())
        else:
            rundir = os.path.join(
                os.path.expanduser("~"),
                self.production.event.name,
                self.production.name,
            )
            self.production.rundir = rundir

        # lmax = self.production.meta['priors']['amp order']

        if "lmax" in self.production.meta:
            lmax = self.production.meta["likelihood"]["lmax"]
        elif "HM" in self.production.meta["approximant"]:
            lmax = 4
        else:
            lmax = 2

        if "cip jobs" in self.production.meta["sampler"]:
            cip = self.production.meta["cip jobs"]
        else:
            cip = 3

        command = [
            os.path.join(
                config.get("pipelines", "environment"),
                "bin",
                "util_RIFT_pseudo_pipe.py",
            ),
            "--use-coinc",
            coinc_file,
            "--l-max",
            f"{lmax}",
            "--calibration",
            f"{calibration}",
            "--add-extrinsic",
            "--approx",
            f"{approximant}",
            "--cip-explode-jobs",
            str(cip),
            "--use-rundir",
            rundir,
            "--ile-force-gpu",
            "--use-ini",
            ini,
        ]

        # If a starting frequency is specified, add it
        if "start-frequency" in self.production.meta:
            command += ["--fmin-template", self.production.quality["start-frequency"]]

        # Placeholder LI grid bootstrapping; conditional on it existing and location specification

        if self.bootstrap:
            if self.bootstrap == "manual":
                if self.production.event.repository:
                    bootstrap_file = os.path.join(
                        self.production.event.repository.directory,
                        "C01_offline",
                        f"{self.production.name}_bootstrap.xml.gz",
                    )
                else:
                    bootstrap_file = "{self.production.name}_bootstrap.xml.gz"
            else:
                raise PipelineException(
                    f"Unable to find the bootstrapping production for {self.production.name}.",
                    issue=self.production.event.issue_object,
                    production=self.production.name,
                )

            command += ["--manual-initial-grid", bootstrap_file]

        if dryrun:
            print(" ".join(command))

        else:
            self.logger.info(" ".join(command), production=self.production)

            with set_directory(self.production.event.work_dir):
                pipe = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                out, err = pipe.communicate()
                if err:
                    self.production.status = "stuck"
                    if hasattr(self.production.event, "issue_object"):
                        self.logger.info(out, production=self.production)
                        self.logger.error(err, production=self.production)
                        raise PipelineException(
                            f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                            issue=self.production.event.issue_object,
                            production=self.production.name,
                        )
                    else:
                        self.logger.info(out, production=self.production)
                        self.logger.error(err, production=self.production)
                        raise PipelineException(
                            f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                            production=self.production.name,
                        )
                else:
                    if self.production.event.repository:
                        with set_directory(self.production.rundir):
                            for psdfile in self.production.get_psds("xml"):
                                ifo = psdfile.split("/")[-1].split("_")[1].split(".")[0]
                                os.system(f"cp {psdfile} {ifo}-psd.xml.gz")

                            # os.system("cat *_local.cache > local.cache")

                            if hasattr(self.production.event, "issue_object"):
                                return PipelineLogger(
                                    message=out,
                                    issue=self.production.event.issue_object,
                                    production=self.production.name,
                                )
                            else:
                                return PipelineLogger(
                                    message=out, production=self.production.name
                                )

    def submit_dag(self, dryrun=False):
        """
        Submit a DAG file to the condor cluster (using the RIFT dag name).
        This is an overwrite of the near identical parent function submit_dag()

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
        if not os.path.exists(self.production.rundir):
            os.makedirs(self.production.rundir)

        self.before_submit()
        with set_directory(self.production.rundir):
            if not dryrun:
                os.system("cat *_local.cache > local.cache")

            for psdfile in self.production.get_psds("xml"):
                ifo = psdfile.split("/")[-1].split("_")[1].split(".")[0]
                os.system(f"cp {psdfile} {ifo}-psd.xml.gz")

            command = [
                "condor_submit_dag",
                "-batch-name",
                f"rift/{self.production.event.name}/{self.production.name}",
                os.path.join(
                    self.production.rundir,
                    "marginalize_intrinsic_parameters_BasicIterationWorkflow.dag",
                ),
            ]

            if dryrun:
                print(" ".join(command))
            else:
                try:
                    dagman = subprocess.Popen(
                        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    )
                    self.logger.info(command, production=self.production)
                except FileNotFoundError as exception:
                    raise PipelineException(
                        "It looks like condor isn't installed on this system.\n"
                        f"""I wanted to run {" ".join(command)}."""
                    ) from exception

                stdout, stderr = dagman.communicate()

                if "submitted to cluster" in str(stdout):
                    cluster = re.search(
                        r"submitted to cluster ([\d]+)", str(stdout)
                    ).groups()[0]
                    self.production.status = "running"
                    self.production.job_id = int(cluster)
                    return cluster, PipelineLogger(stdout)
                else:
                    raise PipelineException(
                        f"The DAG file could not be submitted.\n\n{stdout}\n\n{stderr}",
                        issue=self.production.event.issue_object,
                        production=self.production.name,
                    )

    def resurrect(self):
        """
        Attempt to ressurrect a failed job.
        """
        try:
            count = self.production.meta["resurrections"]
        except KeyError:
            count = 0
        count = len(
            glob.glob(
                os.path.join(
                    self.production.rundir,
                    "marginalize_intrinsic_parameters_BasicIterationWorkflow.dag.rescue*",
                )
            )
        )
        if "allow ressurect" in self.production.meta:
            count = 0
        if (count < 90) and (
            len(
                glob.glob(
                    os.path.join(
                        self.production.rundir,
                        "marginalize_intrinsic_parameters_BasicIterationWorkflow.dag.rescue*",
                    )
                )
            )
            > 0
        ):
            count += 1
            # os.system("cat *_local.cache > local.cache")
            self.submit_dag()
        else:
            raise PipelineException(
                "This job was resurrected too many times.",
                issue=self.production.event.issue_object,
                production=self.production.name,
            )

    def collect_logs(self):
        """
        Collect all of the log files which have been produced by this production and
        return their contents as a dictionary.
        """
        logs = glob.glob(
            f"{self.production.rundir}/*.err"
        )  # + glob.glob(f"{self.production.rundir}/*/logs/*")
        logs += glob.glob(f"{self.production.rundir}/*.out")
        messages = {}
        for log in logs:
            with open(log, "r") as log_f:
                message = log_f.read()
                messages[log.split("/")[-1]] = message
        return messages

    def detect_completion(self):
        """
        Check for the production of the posterior file to signal that the job has completed.
        """
        results_dir = glob.glob(f"{self.production.rundir}")
        if len(results_dir) > 0:  # dynesty_merge_result.json
            if (
                len(
                    glob.glob(
                        os.path.join(results_dir[0], "extrinsic_posterior_samples.dat")
                    )
                )
                > 0
            ):
                return True
            else:
                return False
        else:
            return False

    def samples(self):
        """
        Collect the combined samples file for PESummary.
        """
        return glob.glob(
            os.path.join(self.production.rundir, "extrinsic_posterior_samples.dat")
        )
