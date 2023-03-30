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

        psds = {ifo: os.path.abspath(psd) for ifo, psd in self.production.psds.items()}

        calibration = [
            os.path.abspath(os.path.join(self.production.repository.directory, cal))
            if not cal[0] == "/"
            else cal
            for cal in self.production.meta["data"]["calibration"].values()
        ]
        configfile = self.production.event.repository.find_prods(
            self.production.name, self.category
        )[0]
        if os.path.exists(self.outputs):
            command = ["--add_to_existing", self.outputs]
        else:
            command = ["--webdir", self.outputs]

        command += [
            "--labels",
            self.production.name,
            "--gw",
            "--approximant",
            self.production.meta["waveform"]["approximant"],
            "--f_low",
            str(min(self.production.meta["quality"]["minimum frequency"].values())),
            "--f_ref",
            str(self.production.meta["waveform"]["reference frequency"]),
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

        if "nrsur" in self.production.meta["waveform"]["approximant"].lower():
            command += ["--NRSur_fits"]

        if "multiprocess" in self.meta:
            command += ["--multi_process", str(self.meta["multiprocess"])]

        if "regenerate" in self.meta:
            command += ["--regenerate", " ".join(self.meta["regenerate posteriors"])]

        # Config file
        command += [
            "--config",
            os.path.join(
                self.production.event.repository.directory, self.category, configfile
            ),
        ]
        # Samples
        command += ["--samples"]
        command += self.production.pipeline.samples(absolute=True)
        # Calibration information
        command += ["--calibration"]
        command += calibration
        # PSDs
        command += ["--psd"]
        for key, value in psds.items():
            command += [f"{key}:{value}"]

        with utils.set_directory(self.production.rundir):
            with open(f"{self.production.name}_pesummary.sh", "w") as bash_file:
                bash_file.write(
                    f"{config.get('pesummary', 'executable')} " + " ".join(command)
                )

        self.logger.info(
            f"PE summary command: {config.get('pesummary', 'executable')} {' '.join(command)}",
            production=self.production,
            channels=["file"],
        )

        if dryrun:
            print("PESUMMARY COMMAND")
            print("-----------------")
            print(command)

        submit_description = {
            "executable": config.get("pesummary", "executable"),
            "arguments": " ".join(command),
            "accounting_group": self.meta["accounting group"],
            "output": f"{self.production.rundir}/pesummary.out",
            "error": f"{self.production.rundir}/pesummary.err",
            "log": f"{self.production.rundir}/pesummary.log",
            "request_cpus": self.meta["multiprocess"],
            "getenv": "true",
            "batch_name": f"PESummary/{self.production.event.name}/{self.production.name}",
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
