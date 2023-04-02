"""Defines the interface with generic analysis pipelines."""
import configparser
import os
import subprocess
import time
import warnings

warnings.filterwarnings("ignore", module="htcondor")


import htcondor  # NoQA

from asimov import utils  # NoQA
from asimov import config, logger, logging, LOGGER_LEVEL  # NoQA

import otter  # NoQA
from ..storage import Store  # NoQA
from ..pipeline import PostPipeline, PipelineException, PipelineLogger

class PESummary(PostPipeline):
    """
    A postprocessing pipeline add-in using PESummary.
    """
    executable = "summarypages"
    name = "PESummary"
    style = "multiplex"
    
    def results(self):
        """
        Fetch the results file from this post-processing step.

        A dictionary of results will be returned with the description
        of each results file as the key.  These may be nested if it
        makes sense for the output, for example skymaps.

        For example

        {'metafile': '/home/asimov/working/samples/metafile.hd5',
         'skymaps': {'H1': '/another/file/path', ...}
        }

        Returns
        -------
        dict
           A dictionary of the results.
        """
        self.outputs = os.path.join(
            config.get("project", "root"),
            config.get("general", "webroot"),
            self.subject.name,
        )
        if self.style == "simplex":
            self.outputs = os.path.join(self.outputs, self.analyses[0].name)
        self.outputs = os.path.join(self.outputs, "pesummary")

        metafile = os.path.join(self.outputs, "samples", "posterior_samples.h5")

        return dict(metafile=metafile)

    def submit_dag(self, dryrun=False):
        """
        Run PESummary on the results of this job.
        """

        command = []
        analyses = self.analyses
        
        for production in self.analyses:

            label = str(production.name)
            
            psds = {ifo: os.path.abspath(psd) for ifo, psd in production.psds.items()}
            
            # PSDs
            command += [f"--{label}_psd"]
            for key, value in psds.items():
                command += [f"{key}:{value}"]

            # Calibration
            calibration = [
                os.path.abspath(os.path.join(production.repository.directory, cal))
                if not cal[0] == "/"
                else cal
                for cal in production.meta["data"]["calibration"].values()
            ]
            command += [f"--{label}_calibration"]
            command += calibration

        if os.path.exists(self.outputs):
            command += ["--add_to_existing", self.outputs]
        else:
            command += ["--webdir", self.outputs]

        command += [
            "--gw",
            "--labels", " ".join([analysis.name for analysis in analyses]),
            "--approximant", " ".join([analysis.meta["waveform"]["approximant"] for analysis in analyses]),
            "--f_low", " ".join([str(min(analysis.meta["quality"]["minimum frequency"].values())) for analysis in analyses]),
            "--f_ref", " ".join([str(analysis.meta["waveform"]["reference frequency"].values()) for analysis in analyses]),
        ]

        if "cosmology" in self.meta:
            command += [
                "--cosmology",
                self.meta["cosmology"],
            ]
        if "redshift" in self.meta:
            command += ["--redshift_method", self.meta["redshift"]]
        if "skymap samples" in self.meta:
            command += [
                "--nsamples_for_skymap",
                str(
                    self.meta["skymap samples"]
                ),  # config.get('pesummary', 'skymap_samples'),
            ]

        if "evolve spins" in self.meta:
            if "forwards" in self.meta["evolve spins"]:
                command += ["--evolve_spins_fowards", "True"]
            if "backwards" in self.meta["evolve spins"]:
                command += ["--evolve_spins_backwards", "precession_averaged"]

        if any(["nrsur" in production.meta["waveform"]["approximant"].lower() for production in analyses]):
            command += ["--NRSur_fits"]

        if "multiprocess" in self.meta:
            command += ["--multi_process", str(self.meta["multiprocess"])]

        if "regenerate" in self.meta:
            command += ["--regenerate", " ".join(self.meta["regenerate posteriors"])]

        # Config file
        command += ["--config"]
        for production in analyses:
            configfile = production.event.repository.find_prods(
                production.name, production.category
            )[0]
            command += [os.path.join(
                production.event.repository.directory, production.category, configfile
            )]
        # Samples
        command += ["--samples"]
        samples = [analysis.pipeline.samples(absolute=True)[0] for analysis in self.analyses]
        command += samples

        with utils.set_directory(self.subject.work_dir):
            with open("pesummary.sh", "w") as bash_file:
                bash_file.write(
                    f"{self.executable} " + " ".join(command)
                )

        self.logger.info(
            f"PE summary command: {self.executable} {' '.join(command)}",
        )

        if dryrun:
            print("PESUMMARY COMMAND")
            print("-----------------")
            print(command)

        submit_description = {
            "executable": self.executable,
            "arguments": " ".join(command),
            "accounting_group": self.meta["accounting group"],
            "output": f"{self.subject.work_dir}/pesummary.out",
            "error": f"{self.subject.work_dir}/pesummary.err",
            "log": f"{self.subject.work_dir}/pesummary.log",
            "request_cpus": self.meta["multiprocess"],
            "getenv": "true",
            "batch_name": f"Summary Pages/{self.subject.name}",
            "request_memory": "8192MB",
            "should_transfer_files": "YES",
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
