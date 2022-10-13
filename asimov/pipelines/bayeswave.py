"""BayesWave Pipeline specification."""

import configparser
import glob
import os
import re
import subprocess
from shutil import copyfile, copytree

import numpy as np

from asimov import config, logger
from asimov.utils import set_directory

from ..git import AsimovFileNotFound
from ..pipeline import Pipeline, PipelineException, PipelineLogger
from ..storage import AlreadyPresentException, Store


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

    name = "BayesWave"
    STATUS = {"wait", "stuck", "stopped", "running", "finished"}

    def __init__(self, production, category=None):
        super(BayesWave, self).__init__(production, category)
        self.logger = logger
        if not production.pipeline.lower() == "bayeswave":
            raise PipelineException

        try:
            self.category = config.get("general", "calibration_directory")
        except configparser.NoOptionError:
            self.category = "C01_offline"
            self.logger.info("Assuming C01_offline calibration.")

    def build_dag(self, user=None, dryrun=False):
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
        if self.production.event.repository:
            try:
                gps_file = self.production.get_timefile()
            except AsimovFileNotFound:
                if "event time" in self.production.meta:
                    gps_time = self.production.get_meta("event time")
                    with set_directory(
                        os.path.join(
                            self.production.event.repository.directory, self.category
                        )
                    ):
                        with open("gpstime.txt", "w") as f:
                            f.write(str(gps_time))
                            gps_file = os.path.join(
                                f"{self.production.category}", "gpstime.txt"
                            )
                            self.production.event.repository.add_file(
                                "gpstime.txt", gps_file
                            )
                else:
                    raise PipelineException("Cannot find the event time.")
        else:
            gps_time = self.production.get_meta("event time")
            with open("gpstime.txt", "w") as f:
                f.write(str(gps_time))
                gps_file = os.path.join("gpstime.txt")

        if self.production.event.repository:
            ini = self.production.get_configuration()
            if not user:
                if self.production.get_meta("user"):
                    user = self.production.get_meta("user")
                else:
                    user = ini._get_user()

            ini.update_accounting(user)

            if "queue" in self.production.meta:
                queue = self.production.meta["queue"]
            else:
                queue = "Priority_PE"

            ini.set_queue(queue)

            ini.save()

            ini = ini.ini_loc

        else:
            ini = f"{self.production.name}.ini"

        if self.production.rundir:
            rundir = self.production.rundir
        else:
            rundir = os.path.join(
                config.get("general", "rundir_default"),
                self.production.event.name,
                self.production.name,
            )
            self.production.rundir = rundir

        gps_time = self.production.get_meta("event time")

        pipe_cmd = os.path.join(
            config.get("pipelines", "environment"), "bin", "bayeswave_pipe"
        )

        command = [
            pipe_cmd,
            # "-l", f"{gps_file}",
            f"--trigger-time={gps_time}",
            "-r",
            self.production.rundir,
            ini,
        ]

        self.logger.info(" ".join(command))

        if dryrun:
            print(" ".join(command))
        else:

            pipe = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            out, err = pipe.communicate()
            if "To submit:" not in str(out):
                self.production.status = "stuck"

                raise PipelineException(
                    f"DAG file could not be created.\n{command}\n{out}\n\n{err}",
                    production=self.production.name,
                )
            else:
                if hasattr(self.production.event, "issue_object"):
                    return PipelineLogger(
                        message=out,
                        issue=self.production.event.issue_object,
                        production=self.production.name,
                    )
                else:
                    return PipelineLogger(message=out, production=self.production.name)

    def detect_completion(self):
        psds = self.collect_assets()["psds"]
        if len(list(psds.values())) > 0:
            return True
        else:
            self.logger.info("Bayeswave job completion was not detected.")
            return False

    def after_completion(self):

        try:
            self.collect_pages()
        except FileNotFoundError:
            PipelineLogger(
                message=b"Failed to copy megaplot pages.",
                production=self.production.name,
            )

        try:
            self.collect_assets()
            self.store_assets()
        except Exception:
            PipelineLogger(
                message=b"Failed to store PSDs.",
                issue=self.production.event.issue_object,
                production=self.production.name,
            )

        if "supress" in self.production.meta["quality"]:
            for ifo in self.production.meta["quality"]["supress"]:
                if ifo in self.production.meta["interferometers"]:
                    self.supress_psd(
                        ifo,
                        self.production.meta["quality"]["supress"][ifo]["lower"],
                        self.production.meta["quality"]["supress"][ifo]["upper"],
                    )
        self.production.status = "uploaded"

    def before_submit(self):
        """
        Horribly hack the sub files to add `request_disk`
        """
        sub_files = glob.glob(f"{self.production.rundir}/*.sub")
        for sub_file in sub_files:
            with open(sub_file, "r") as f_handle:
                original = f_handle.read()
            with open(sub_file, "w") as f_handle:
                f_handle.write(f"request_disk = {64000}\n" + original)

    def submit_dag(self, dryrun=False):
        """
        Submit a DAG file to the condor cluster.

        Parameters
        ----------
        dryrun: bool
           If True then the DAG will not be submitted but all of the
           commands will be printed to stdout.

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
        self.before_submit()
        with set_directory(self.production.rundir):

            command = [
                "condor_submit_dag",
                "-batch-name",
                f"bwave/{self.production.event.name}/{self.production.name}",
                f"{self.production.name}.dag",
            ]

            if dryrun:
                print(" ".join(command))
            else:
                try:
                    dagman = subprocess.Popen(
                        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    )
                except FileNotFoundError:
                    raise PipelineException(
                        "It looks like condor isn't installed on this system.\n"
                        f"""I wanted to run {" ".join(command)}."""
                    )

                stdout, stderr = dagman.communicate()

                if "submitted to cluster" in str(stdout):
                    cluster = re.search(
                        r"submitted to cluster ([\d]+)", str(stdout)
                    ).groups()[0]
                    self.production.status = "running"
                    self.production.job_id = int(cluster)
                    return int(cluster), PipelineLogger(stdout)
                else:
                    logger.info(stdout)
                    logger.error(stderr)
                    raise PipelineException(
                        f"The DAG file could not be submitted.\n\n{stdout}\n\n{stderr}",
                        issue=self.production.event.issue_object,
                        production=self.production.name,
                    )

    def upload_assets(self):
        """
        Upload the PSDs from this job.
        """
        sample = self.production.meta["likelihood"]["sample rate"]
        git_location = os.path.join(self.category, "psds")

        for detector, asset in self.collect_assets()["psds"]:
            self.production.event.repository.add_file(
                asset,
                os.path.join(git_location, str(sample), f"psd_{detector}.dat"),
                commit_message=f"Added the PSD for {detector}.",
            )

    def store_assets(self):
        """
        Add the assets to the store.
        """

        sample_rate = self.production.meta["quality"]["sample-rate"]
        for detector, asset in self.collect_assets()["psds"]:
            store = Store(root=config.get("storage", "directory"))
            try:
                store.add_file(
                    self.production.event.name,
                    self.production.name,
                    file=f"{detector}-{sample_rate}-psd.dat",
                )
            except Exception as e:
                error = PipelineLogger(
                    f"There was a problem committing the PSD for {detector} to the store.\n\n{e}",
                    issue=self.production.event.issue_object,
                    production=self.production.name,
                )
                error.submit_comment()

    def collect_logs(self):
        """
        Collect all of the log files which have been produced by this production and
        return their contents as a dictionary.
        """
        logs = glob.glob(f"{self.production.rundir}/logs/*.err") + glob.glob(
            f"{self.production.rundir}/*.err"
        )
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
        psds = {}
        for det in self.production.meta["interferometers"]:
            asset = os.path.join(
                results_dir, "post", "clean", f"glitch_median_PSD_forLI_{det}.dat"
            )
            if os.path.exists(asset):
                psds[det] = asset

        outputs = {}
        outputs["psds"] = psds
        return outputs

    def supress_psd(self, ifo, fmin, fmax):
        """
        Suppress portions of a PSD.
        Author: Carl-Johan Haster - August 2020
        (Updated for asimov by Daniel Williams - November 2020
        """
        store = Store(root=config.get("storage", "directory"))
        sample_rate = self.production.meta["quality"]["sample-rate"]
        orig_PSD_file = np.genfromtxt(
            os.path.join(
                self.production.event.repository.directory,
                self.category,
                "psds",
                str(sample_rate),
                f"{ifo}-psd.dat",
            )
        )

        freq = orig_PSD_file[:, 0]
        PSD = orig_PSD_file[:, 1]

        suppression_region = np.logical_and(
            np.greater_equal(freq, fmin), np.less_equal(freq, fmax)
        )

        # Suppress the PSD in this region

        PSD[suppression_region] = 1.0

        new_PSD = np.vstack([freq, PSD]).T

        asset = f"{ifo}-psd.dat"
        np.savetxt(asset, new_PSD, fmt="%+.5e")

        destination = os.path.join(
            self.category, "psds", str(sample_rate), f"{ifo}-psd.dat"
        )

        try:
            self.production.event.repository.add_file(
                asset, destination
            )  # , message=f"Added the supresed {ifo} PSD")
        except Exception as e:
            raise PipelineException(
                f"There was a problem committing the suppresed PSD for {ifo} to the repository.\n\n{e}",
                issue=self.production.event.issue_object,
                production=self.production.name,
            )
        copyfile(asset, f"{ifo}-{sample_rate}-psd-suppresed.dat")
        try:
            store.add_file(
                self.production.event.name,
                self.production.name,
                file=f"{ifo}-{sample_rate}-psd-suppresed.dat",
            )
        except AlreadyPresentException:
            pass
        self.logger.info(f"PSD supression applied to {ifo} between {fmin} and {fmax}")

    def resurrect(self):
        """
        Attempt to ressurrect a failed job.
        """
        count = len(glob.glob(os.path.join(self.production.rundir, "*.dag.rescue*")))

        if (count < 5) and (count > 0):
            self.submit_dag()
            self.logger.info(f"Bayeswave job was resurrected for the {count} time.")
        else:
            self.logger.error(
                "Bayeswave resurrection not completed as there have already been 5 attempts"
            )

    def html(self):
        """Return the HTML representation of this pipeline."""
        pages_dir = os.path.join(self.production.event.name, self.production.name)
        out = ""
        if self.production.status in {"finished", "uploaded"}:
            out += """<div class="asimov-pipeline">"""
            out += (
                f"""<p><a href="{pages_dir}/index.html">Full Megaplot output</a></p>"""
            )
            out += f"""<img height=200 src="{pages_dir}/plots/clean_whitened_residual_histograms.png"</src>"""

            out += """</div>"""

        return out

    def collect_pages(self):
        """Collect the HTML output of the pipeline."""
        results_dir = glob.glob(f"{self.production.rundir}/trigtime_*")[0]
        pages_dir = os.path.join(
            config.get("general", "webroot"),
            self.production.event.name,
            self.production.name,
        )
        os.makedirs(pages_dir, exist_ok=True)
        copyfile(
            os.path.join(results_dir, "index.html"),
            os.path.join(pages_dir, "index.html"),
        )
        copytree(
            os.path.join(results_dir, "html"),
            os.path.join(pages_dir, "html"),
            dirs_exist_ok=True,
        )
        copytree(
            os.path.join(results_dir, "plots"),
            os.path.join(pages_dir, "plots"),
            dirs_exist_ok=True,
        )
