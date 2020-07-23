"""Defines the interface with generic analysis pipelines."""

import os
import subprocess
import glob

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


class Pipeline():
    """
    Factory class for pipeline specification.
    """

    def __init__(self, production, category=None):
        self.production = production

        if not category:
            if "Prod" in production.name:
                self.category = "C01_offline"
            else:
                self.category = "online"
        else:
            self.category = category

    def detect_completion(self):
        """
        Detect if the job has completed normally.
        Looks to see if posterior sample files have been produced.
        """
        if len(glob.glob(f"{self.production.rundir}/posterior_samples/*hdf5")) > 0:
            return True
        else:
            return False

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
        """
        os.chdir(self.production.rundir)
        dagman = subprocess.Popen(["condor_submit_dag",
                                   os.path.join(self.production.rundir, "multidag.dag")],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        stdout, stderr = dagman.communicate()

        if "submitted to cluster" in str(stdout):
            cluster = re.search("submitted to cluster ([\d]+)", str(stdout)).groups()[0]
            self.production.status = "running"
            self.production.job_id = cluster
            return cluster
        else:
            raise PipelineException(f"The DAG file could not be submitted.\n\n{stdout}\n\n{stderr}",
                                    issue=self.production.event.issue_object,
                                    production=self.production.name)
