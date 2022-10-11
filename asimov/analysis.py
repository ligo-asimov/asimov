"""
Code to handle the various kinds of analysis which asimov can handle.

Asimov defintes three types of analysis, depending on the inputs of the analysis.

Simple analyses
  These analyses operate only on a single event,
  and will generally use a very specific set of configuration settings.
  An example of a simple analysis is a bilby or RIFT parameter estimation analysis,
  as these only require access to the data for a single event.
  Before version 0.4 these were called `Productions`.

Event analyses
  These analyses can access the results of all of the simple analyses which have been
  performed on a single event, or a subset of them.
  An example of an event analysis is the production of mixed posterior samples from multiple
  PE analyses.

Project analyses
  These are the most general type of analysis, and have access to the results of all analyses
  on all events, including event and simple analyses.
  This type of analysis is useful for defining a population analysis, for example.

"""
import os
import configparser
from copy import deepcopy
from warnings import warn

from liquid import Liquid

from asimov import config
from asimov.pipelines import known_pipelines
from asimov.utils import update
from asimov.storage import Store


class Analysis:
    """
    The base class for all other types of analysis.

    TODO: Add a check to make sure names cannot conflict
    """

    @property
    def review(self):
        """
        Return the review information attached to the analysis.
        """

    def _process_dependencies(self, needs):
        """
        Process the dependencies list for this production.
        """
        return needs

    @property
    def dependencies(self):
        if "needs" in self.meta:
            dependencies = self._process_dependencies(self.meta["needs"])
        else:
            dependencies = None
        return dependencies

    @property
    def priors(self):
        if "priors" in self.meta:
            priors = self.meta["priors"]
        else:
            priors = None
        return priors

    @property
    def finished(self):
        finished_states = ["uploaded"]
        return self.status in finished_states

    @property
    def status(self):
        return self.status_str.lower()

    @status.setter
    def status(self, value):
        self.status_str = value.lower()
        if self.event.issue_object is not None:
            self.event.issue_object.update_data()

    def results(self, filename=None, handle=False, hash=None):
        store = Store(root=config.get("storage", "results_store"))
        if not filename:
            try:
                items = store.manifest.list_resources(self.subject.name, self.name)
                return items
            except KeyError:
                return None
        elif handle:
            return open(
                store.fetch_file(self.subject.name, self.name, filename, hash), "r"
            )
        else:
            return store.fetch_file(self.subject.name, self.name, filename, hash=hash)

    @property
    def rundir(self):
        """
        Return the run directory for this event.
        """
        if "rundir" in self.meta:
            return self.meta["rundir"]
        elif "working directory" in self.subject.meta:
            value = os.path.join(self.subject.meta["working directory"], self.name)
            self.meta["rundir"] = value
            # TODO: Make sure this is saved back to the ledger
        else:
            return None

    def make_config(self, filename, template_directory=None):
        """
        Make the configuration file for this production.

        Parameters
        ----------
        filename : str
           The location at which the config file should be saved.
        template_directory : str, optional
           The path to the directory containing the pipeline config templates.
           Defaults to the directory specified in the asimov configuration file.
        """

        if "template" in self.meta:
            template = f"{self.meta['template']}.ini"
        else:
            template = f"{self.pipeline}.ini"

        pipeline = known_pipelines[self.pipeline]
        if hasattr(pipeline, "config_template"):
            template_file = pipeline.config_template
        else:
            try:
                template_directory = config.get("templating", "directory")
                template_file = os.path.join(f"{template_directory}", template)
            except configparser.NoOptionError:
                from pkg_resources import resource_filename

                template_file = resource_filename("asimov", f"configs/{template}")

        liq = Liquid(template_file)
        rendered = liq.render(production=self, config=config)

        with open(filename, "w") as output_file:
            output_file.write(rendered)


class SimpleAnalysis(Analysis):
    """
    A single subject, single pipeline analysis.
    """

    def __init__(self, subject, name, pipeline, status=None, comment=None, **kwargs):
        self.event = self.subject = subject
        self.name = name

        if status:
            self.status_str = status.lower()
        else:
            self.status_str = "none"
            self.pipeline = pipeline.lower()
            self.comment = comment
            self.meta = deepcopy(self.subject.meta)
            self.meta = update(self.meta, kwargs)


class SubjectAnalysis(Analysis):
    """
    A single subject analysis which requires results from multiple pipelines.
    """

    pass


class ProjectAnalysis(Analysis):
    """
    A multi-subject analysis.
    """

    def __init__(
        self, subjects, analyses, name, pipeline, status=None, comment=None, **kwargs
    ):
        """ """
        super().__init__()

        self.subjects = subjects
        self.analyses = analyses


class GravitationalWaveTransient(SimpleAnalysis):
    """
    A single subject, single pipeline analysis for a gravitational wave transient.
    """

    def __init__(self, subject, name, pipeline, status=None, comment=None, **kwargs):
        super().init(subject, name, pipeline, status=None, comment=None, **kwargs)
        self._checks()

    def _checks(self):
        """
        Carry-out a number of data consistency checks on the information from the ledger.
        """
        # Check that the upper frequency is included, otherwise calculate it
        if self.quality:
            if ("high-frequency" not in self.quality) and (
                "sample-rate" in self.quality
            ):
                # Account for the PSD roll-off with the 0.875 factor
                self.meta["quality"]["high-frequency"] = int(
                    0.875 * self.meta["quality"]["sample-rate"] / 2
                )
            elif ("high-frequency" in self.quality) and ("sample-rate" in self.quality):
                if self.meta["quality"]["high-frequency"] != int(
                    0.875 * self.meta["quality"]["sample-rate"] / 2
                ):
                    warn(
                        "The upper-cutoff frequency is not equal to 0.875 times the Nyquist frequency."
                    )

    @property
    def quality(self):
        if "quality" in self.meta:
            return self.meta["quality"]
        else:
            return None

    @property
    def reference_frame(self):
        """
        Calculate the appropriate reference frame.
        """
        ifos = self.meta["interferometers"]
        if len(ifos) == 1:
            return ifos[0]
        else:
            return "".join(ifos[:2])

    @property
    def psds(self):
        """
        Return the PSDs stored for this transient event.
        """
        if "psds" in self.meta and self.quality:
            if self.quality["sample-rate"] in self.meta["psds"]:
                self.psds = self.meta["psds"][self.quality["sample-rate"]]
            else:
                self.psds = {}
        else:
            self.psds = {}

        for ifo, psd in self.psds.items():
            if self.subject.repository:
                self.psds[ifo] = os.path.join(self.subject.repository.directory, psd)
            else:
                self.psds[ifo] = psd

    def get_timefile(self):
        """
        Find this event's time file.

        Returns
        -------
        str
           The location of the time file.
        """
        return self.event.repository.find_timefile(self.category)

    def get_coincfile(self):
        """
        Find this event's coinc.xml file.

        Returns
        -------
        str
           The location of the time file.
        """
        try:
            coinc = self.event.repository.find_coincfile(self.category)
            return coinc
        except FileNotFoundError:
            self.event.get_gracedb(
                "coinc.xml",
                os.path.join(
                    self.event.repository.directory, self.category, "coinc.xml"
                ),
            )
            coinc = self.event.repository.find_coincfile(self.category)
            return coinc


class Production(SimpleAnalysis):
    pass
