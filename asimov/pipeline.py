"""Defines the interface with generic analysis pipelines."""
import configparser
import os
import subprocess
import time
import warnings
from copy import deepcopy

warnings.filterwarnings("ignore", module="htcondor")


import htcondor  # NoQA

from asimov import utils  # NoQA
from asimov import config, logger, logging, LOGGER_LEVEL  # NoQA

import otter  # NoQA
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

        self.logger = logger.getChild(
            f"analysis.{production.event.name}/{production.name}"
        )
        self.logger.setLevel(LOGGER_LEVEL)

    def __repr__(self):
        return self.name.lower()

    def detect_completion(self):
        """
        Check to see if the job has in fact completed.
        """
        pass

    def before_config(self, dryrun=False):
        """
        Define a hook to run before the config file for the pipeline is generated.
        """
        pass

    def before_build(self, dryrun=False):
        """
        Define a hook to be run before the DAG is built.
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
        # self.production.meta.pop("job id")

        # post_pipeline = PESummary(production=self.production, subject=self.production.subject)
        # cluster = post_pipeline.submit_dag()
        # self.production.meta["job id"] = int(cluster)

    def collect_assets(self):
        """
        Add the various analysis assets from the run directory to the git repository.
        """
        repo = self.production.event.repository

        for asset in self.assets:
            repo.add_file(asset[0], asset[1])

    def collect_logs(self):
        return {}

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
                "pesummary",
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
            "pesummary",
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

    def build_report(self, reportformat="html"):
        """
        Build an entire report on this pipeline, including logs and configs.
        """
        webdir = config.get("general", "webroot")
        if reportformat == "html":
            # report = otter.Otter(
            #     f"{webdir}/{self.production.event.name}/{self.production.name}/index.html",
            #     author="Asimov",
            #     title="Asimov analysis report",
            # )
            report_logs = otter.Otter(
                f"{webdir}/{self.production.event.name}/{self.production.name}/logs.html",
                author="Asimov",
                title="Asimov analysis logs",
            )
            # report_config = otter.Otter(
            #     f"{webdir}/{self.production.event.name}/{self.production.name}/config.html",
            #     author="Asimov",
            #     title="Asimov analysis configuration",
            # )
            with report_logs:
                for log in self.collect_logs().values():
                    for message in log.split("\n"):
                        report_logs + message
            # with report_config:
            #     report_config + self.


class PostPipeline:
    """This class describes post processing pipelines which are a
    class of pipelines which can be run on multiple analyses for a
    subject.

    Postprocessing pipelines take the results of analyses and run
    additional steps on them, and unlike a normal analysis they are
    not immutable, and can be re-run each time a new analyis is
    completed which satisfies the conditions of the postprocessing
    job.

    """

    style = "multiplex"

    def __init__(self, subject, **kwargs):
        """
        Post processing pipeline factory class.

        """

        if "ledger" in kwargs:
            self.ledger = kwargs["ledger"]
        else:
            self.ledger = None

        self.subject = subject
        # self.category = category if category else production.category
        self.logger = logger
        # self.meta = self.production.meta["postprocessing"][self.name.lower()]
        self.meta = kwargs

        self.outputs = os.path.join(
            config.get("project", "root"),
            config.get("general", "webroot"),
            self.subject.name,
        )
        if self.style == "simplex":
            self.outputs = os.path.join(self.outputs, self.analyses[0].name)

    def __repr__(self):
        output = ""
        output += "-------------------------------------------------------" + "\n"
        output += "Asimov postprocessing pipeline" + "\n"
        output += f"{self.name}" + "\n"
        output += (
            f"""Currently contains: {(chr(10)+"                    ").join(self.current_list)}"""
            + "\n"
        )
        output += (
            """Designed to contain: """
            + f"""{(chr(10)+"                     ").join([analysis.name for analysis in self.analyses])}"""
            + "\n"
        )
        output += f"""Is fresh?: {self.fresh}""" + "\n"
        output += "-------------------------------------------------------" + "\n"
        return output

    def _process_analyses(self):
        """
        Process the analysis list for this production.

        The dependencies can be provided either as the name of an analysis,
        or a query against the analysis's attributes.

        Parameters
        ----------
        needs : list
           A list of all the analyses which this should be applied to

        Returns
        -------
        list
           A list of all the analysis specifiations processed for evaluation.
        """
        all_requirements = []
        post_requirements = []
        for need in self.meta["analyses"]:
            try:
                requirement = need.split(":")
                requirement = [requirement[0].split("."), requirement[1]]
            except IndexError:
                requirement = [["name"], need]
            if requirement[0][0] == "postprocessing" and requirement[0][1] == "name":
                post_requirements.append(requirement)
            else:
                all_requirements.append(requirement)

        analyses = []
        post = []
        if self.meta["analyses"]:
            matches = set(self.subject.analyses)
            for attribute, match in all_requirements:
                filtered_analyses = list(
                    filter(
                        lambda x: x.matches_filter(attribute, match),
                        self.subject.analyses,
                    )
                )
                matches = set.intersection(matches, set(filtered_analyses))
                for analysis in matches:
                    analyses.append(analysis)

            matches = set(self.ledger.postprocessing)
            for attribute, match in post_requirements:
                filtered_posts = list(
                    filter(lambda x: x == match, self.ledger.postprocessing.keys())
                )
                matches = set.intersection(
                    self.ledger.postprocessing, set(filtered_posts)
                )
                for analysis in matches:
                    post.append(analysis)
        return analyses

    @property
    def current_list(self):
        """
        Return the list of analyses which are included in the current results.
        """
        if "current list" in self.meta:
            return self.meta["current list"]
        else:
            return []

    @current_list.setter
    def current_list(self, data):
        """
        Return the list of analyses which are included in the current results.
        """
        self.meta["current list"] = [analysis.name for analysis in data]
        if self.ledger:
            self.ledger.save()

    @property
    def fresh(self):
        """
        Check if the post-processing job is fresh.

        Tries to work out if any of the samples which should have been
        included for post-processing are newer than the most recent
        files produced by this job.  If they are all older then the
        results are fresh, otherwise they are stale, and the
        post-processing will need to run again.

        Returns
        -------
        bool
           If the job is fresh True is returned.
           Otherwise False.
        """
        # Check if there are any finished analyses
        finished = []
        for analysis in self.analyses:
            if analysis.finished:
                finished.append(analysis)
        if len(finished) > 0:
            if not all([os.path.exists(result) for result in self.results().values()]):
                return False
            try:
                for analysis in self.analyses:
                    self._check_ages(
                        analysis.pipeline.samples(),
                        self.results().values(),
                    )
            except AssertionError:
                return False
            return True
        else:
            return True

    def _check_ages(self, listA, listB):
        """
        Check that the ages of all the samples from listA are younger than all the files from listB.
        """

        for sample in listA:
            for comparison in listB:
                assert os.stat(sample).st_mtime < os.stat(comparison).st_mtime

    @property
    def analyses(self):
        """
        Return a list of productions which this pipeline should apply to.

        Post-processing pipelines can either apply to individual
        analyses, or to a subset of all the analyses on a given
        subject.  This property returns a list of all the productions
        which this pipeline will be applied to.

        Returns
        -------
        list
           A list of all analyses which the pipeline will be applied to.
        """
        return self._process_analyses()

    def run(self, dryrun=False):
        """
        Run all of the steps required to build and submit this pipeline.
        """
        cluster = self.submit_dag(dryrun=dryrun)
        self.current_list = [
            analysis for analysis in self.analyses if analysis.finished
        ]
        self.meta["job id"] = cluster
        self.meta["status"] = "running"
        if self.ledger:
            self.ledger.save()

    def to_dict(self):
        """
        Convert this pipeline into a dictionary.
        """
        output = {}
        output.update(deepcopy(self.meta))
        output.pop("ledger")
        output["pipeline"] = self.name
        return output

    @property
    def status(self):
        if "status" in self.meta:
            return self.meta["status"]
        else:
            return None

    @property
    def job_id(self):
        if "job id" in self.meta:
            return self.meta["job id"]
        else:
            return None
