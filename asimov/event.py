"""
Trigger handling code.
"""

import yaml
import os
import glob

import networkx as nx

from .ini import RunConfiguration
from .git import EventRepo
from asimov import config

from liquid import Liquid

from ligo.gracedb.rest import GraceDb, HTTPError
from copy import copy

class DescriptionException(Exception):
    """Exception for event description problems."""
    def __init__(self, message, issue=None, production=None):
        super(DescriptionException, self).__init__(message)
        self.message = message
        self.issue = issue
        self.production = production

    def __repr__(self):
        text = f"""
An error was detected with the YAML markup in this issue.
Please fix the error and then remove the `yaml-error` label from this issue.
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
            self.issue.add_label("yaml-error", state=False)
            self.issue.add_note(self.__repr__())


class Event:
    """
    A specific gravitational wave event or trigger.
    """

    def __init__(self, name, repository, **kwargs):
        self.name = name
        if "working_directory" in kwargs:
            self.work_dir = kwargs['working_directory']
        else:
            self.work_dir = None

        if "disable_repo" not in kwargs:
            self.repository = EventRepo.from_url(repository,
                                             self.name,
                                             self.work_dir)
        else:
            self.repository = repository
            
        self.productions = []
        if "psds" in kwargs:
            self.psds = kwargs["psds"]
        else:
            self.psds = {}
            
        self.meta = kwargs
        self._check_required()

        try:
            self._check_calibration()
        except DescriptionException:
            print("No calibration envelopes found.")
        #self._check_psds()

        self.graph = nx.DiGraph()

    def _check_required(self):
        """
        Find all of the required metadata is provided.
        """
        required = {"interferometers"}
        if not (required <= self.meta.keys()):
            raise DescriptionException(f"Some of the required parameters are missing from this issue. {required-self.meta.keys()}")
        else:
            return True
        
    def _check_calibration(self):
        """
        Find the calibration envelope locations.
        """
        if ("calibration" in self.meta) and (set(self.meta['interferometers']) == set(self.meta['calibration'].keys())):
            pass
        else:
            raise DescriptionException(f"Some of the required calibration envelopes are missing from this issue. {set(self.meta['interferometers']) - set(self.meta['calibration'].keys())}")

    def _check_psds(self):
        """
        Find the psd locations.
        """
        if ("calibration" in self.meta) and (set(self.meta['interferometers']) == set(self.psds.keys())):
            pass
        else:
            raise DescriptionException(f"Some of the required psds are missing from this issue. {set(self.meta['interferometers']) - set(self.meta['calibration'].keys())}")

    @property
    def webdir(self):
        """
        Get the web directory for this event.
        """
        if "webdir" in self.meta:
            return self.meta['webdir']
        else:
            return None
        
    def add_production(self, production):
        """
        Add an additional production to this event.
        """
        self.productions.append(production)
        self.graph.add_node(production)

        if production.dependencies:
            dependencies = production.dependencies
            dependencies = [production for production in self.productions
                            if production.name in dependencies]
            for dependency in dependencies:
                self.graph.add_edge(dependency, production)
        
    def __repr__(self):
        return f"<Event {self.name}>"

    @classmethod
    def from_yaml(cls, data, issue=None):
        """
        Parse YAML to generate this event.

        Parameters
        ----------
        data : str
           YAML-formatted event specification.
        issue : int
           The gitlab issue which stores this event.

        Returns
        -------
        Event
           An event.
        """
        data = yaml.safe_load(data)
        if not {"name", "repository"} <= data.keys():
            raise DescriptionException(f"Some of the required parameters are missing from this issue.")
        event = cls(**data)
        if issue:
            event.issue_object = issue
            event.from_notes()
        for production in data['productions']:
            try:
                event.add_production(
                    Production.from_dict(production, event=event, issue=issue))
            except DescriptionException as error:
                error.submit_comment()
        return event

    @classmethod
    def from_issue(cls, issue):
        """
        Parse an issue description to generate this event.
        """

        text = issue.text.split("---")

        event = cls.from_yaml(text[1], issue)
        event.text = text

        return event

    def from_notes(self):
        
        notes_data = self.issue_object.parse_notes()
        for note in notes_data:
            for key, value in notes_data.items():
                if key in self.meta:
                    self.meta[key] = value

    def get_gracedb(self, gfile, destination):
        """
        Get a file from Gracedb, and store it in the event repository.

        Parameters
        ----------
        gfile : str
           The name of the gracedb file, e.g. `coinc.xml`.
        destination : str
           The location in the repository for this file.
        """


        gid = self.meta['gid']
        client = GraceDb(service_url=config.get("gracedb", "url"))
        file_obj = client.files(gid, gfile)

        with open("download.file", "w") as dest_file:
            dest_file.write(file_obj.read().decode())

        self.repository.add_file("download.file", destination,
                                 commit_message = f"Downloaded {gfile} from GraceDB")
    
    def to_yaml(self):
        """Serialise this object as yaml"""
        data = {}
        data['name'] = self.name
        data['repository'] = self.repository.url
        for key, value in self.meta.items():
            data[key] = value
        try:
            data['repository'] = self.repository.url
        except AttributeError:
            pass
        data['productions'] = []
        
        for production in self.productions:
            # Remove duplicate data
            prod_dict = production.to_dict()[production.name]
            dupes = []
            for key, value in prod_dict.items():
                if key in data:
                    if data[key] == value:
                        dupes.append(key)
            for dupe in dupes:
                prod_dict.pop(dupe)
            data['productions'].append({production.name: prod_dict})

        return yaml.dump(data, default_flow_style=False)

    def to_issue(self):
        self.text[1] = "\n"+self.to_yaml()
        return "---".join(self.text)

    def draw_dag(self):
        """
        Draw the dependency graph for this event.
        """
        return nx.draw(self.graph, labelled=True)

    def get_all_latest(self):
        """
        Get all of the jobs which are not blocked by an unfinished job
        further back in their history.

        Returns
        -------
        set
            A set of independent jobs which are not finished execution.
        """
        unfinished = self.graph.subgraph([production for production in self.productions
                                          if production.finished == False])
        ends = [x for x in unfinished.reverse().nodes() if unfinished.reverse().out_degree(x)==0]
        return set(ends) # only want to return one version of each production!

    
class Production:
    """
    A specific production run.

    Parameters
    ----------
    event : `asimov.event`
        The event this production is running on.
    name : str
        The name of this production.
    status : str
        The status of this production.
    pipeline : str
        This production's pipeline.
    comment : str
        A comment on this production.
    """
    def __init__(self, event, name, status, pipeline, comment=None, **kwargs):
        self.event = event
        self.name = name
        self.status_str = status.lower()
        self.pipeline = pipeline.lower()
        self.comment = comment
        self.meta = copy(self.event.meta)
        if "productions" in self.meta:
            self.meta.pop("productions")
        self.meta.update(kwargs)

        # Get the data quality recommendations
        if 'quality' in self.event.meta:
            self.quality = self.event.meta['quality']
        else:
            self.quality = {}
        if 'quality' in kwargs:
            self.quality.update(kwargs['quality'])
            
        quality_required = {"lower-frequency", "psd-length", "sample-rate", "segment-length", "window-length"}
        if not (quality_required <= self.quality.keys()):
            raise DescriptionException(f"Some of the required parameters are missing from this production's metadata.\n{quality_required-self.meta.keys()}",
                                       issue = self.event.issue_object,
                                       production = self)

        
        # Need to fetch the correct PSDs for this sample rate
        if 'psds' in self.meta:
            if self.quality['sample-rate'] in self.meta['psds']:
                self.psds = self.meta['psds'][self.quality['sample-rate']]
            else:
                raise DescriptionException(f"No PSDs were found for this event at the correct sampling rate.\n{self.quality['sample-rate']}",
                                       issue = self.event.issue_object,
                                       production = self)
        else:
            raise DescriptionException(f"No PSDs were found for this event.",
                                       issue = self.event.issue_object,
                                       production = self)

        for ifo, psd in self.psds.items():
            self.psds[ifo] = os.path.join(self.event.repository.directory, psd)

        if "Prod" in self.name:
            self.category = "C01_offline"
        else:
            self.category = "online"

        if "needs" in self.meta:
            self.dependencies = self._process_dependencies(self.meta['needs'])
        else:
            self.dependencies = None

    def _process_dependencies(self, needs):
        """
        Process the dependencies list for this production.
        """
        return needs

    def get_meta(self, key):
        """
        Get the value of a metadata attribute, or return None if it doesn't
        exist.
        """
        if key in self.meta:
            return self.meta[key]
        else:
            return None

    def set_meta(self, key, value):
        """
        Set a metadata attribute which doesn't currently exist.
        """
        if key not in self.meta:
            self.meta[key] = value
            self.event.issue_object.update_data()
        else:
            raise ValueError

    @property
    def finished(self):
        finished_states = ["finished"]
        return self.status in finished_states
        
    @property
    def status(self):
        return self.status_str.lower()

    @status.setter
    def status(self, value):
        self.status_str = value.lower()
        if hasattr(self.event, "issue_object"):
            self.event.issue_object.update_data()

    @property
    def job_id(self):
        if "job id" in self.meta:
            return self.meta['job id']
        else:
            return None

    @job_id.setter
    def job_id(self, value):
        self.meta["job id"] = value
        self.event.issue_object.update_data()
        
    def to_dict(self):
        output = {self.name: {}}
        output[self.name]['status'] = self.status
        output[self.name]['pipeline'] = self.pipeline.lower()
        output[self.name]['comment'] = self.comment
        for key, value in self.meta.items():
            output[self.name][key] = value
        if "repository" in self.meta:
            output[self.name]['repository'] = self.repository.url
        return output

    @property
    def rundir(self):
        """
        Return the run directory for this event.
        """
        if "rundir" in self.meta:
            return self.meta['rundir']
        elif "working directory" in self.event.meta:
            value = os.path.join(self.event.meta['working directory'], self.name)
            self.meta["rundir"] = value
            self.event.issue_object.update_data()
            return value
        else:
            return None

    @rundir.setter
    def rundir(self, value):
        """
        Set the run directory.
        """
        if "rundir" not in self.meta:
            self.meta["rundir"] = value
            if hasattr(self.event, "issue_object"):
                self.event.issue_object.update_data()
        else:
            raise ValueError

    def get_psds(self, format="ascii", sample_rate=None):
        """
        Get the PSDs for this production.

        Parameters
        ----------
        format : {ascii, xml}
           The format of the PSD to be returned. 
           Defaults to the ascii format.
        sample_rate : int
           The sample rate of the PSD to be returned.
           Defaults to None, in which case the sample rate in the event data is used.

        Returns
        -------
        list
           A list of PSD files for the production.
        """
        if sample_rate == None:
            try:
                if "quality" in self.meta and "sample-rate" in self.meta['quality']:
                    sample_rate = self.meta['quality']['sample-rate']
                else:
                    raise DescriptionException(f"The sample rate for this event cannot be found.",
                                           issue=self.event.issue_object,
                                           production=self.name)
            except Exception as e:
                raise DescriptionException(f"The sample rate for this event cannot be found.",
                                           issue=self.event.issue_object,
                                           production=self.name)
            
        if (len(self.psds)>0) and (format=="ascii"):
            return self.psds
        elif (format=="ascii"):
            files = glob.glob(f"{self.event.repository.directory}/{self.category}/psds/{sample_rate}/*.dat")
            if len(files)>0:
                return files
            else:
                raise DescriptionException(f"The PSDs for this event cannot be found.",
                                           issue=self.event.issue_object,
                                           production=self.name)
        elif (format=="xml"):
            files = glob.glob(f"{self.event.repository.directory}/{self.category}/psds/{sample_rate}/*.xml.gz")
            return files
            
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
            self.event.get_gracedb("coinc.xml", os.path.join(self.event.repository.directory, self.category, "coinc.xml"))
    
    def get_configuration(self):
        """
        Get the configuration file contents for this event.
        """
        if "ini" in self.meta:
            ini_loc = self.meta['ini']
        else:
            # We'll need to search the repository for it.
            try:
                ini_loc = self.event.repository.find_prods(self.name,
                                                       self.category)[0]
            except IndexError:
                raise ValueError("Could not open the ini file.")
        try:
            ini = RunConfiguration(ini_loc)
        except ValueError:
            raise ValueError("Could not open the ini file")

        return ini

    @classmethod
    def from_dict(cls, parameters, event, issue=None):
        name, pars = list(parameters.items())[0]
        # Check that pars is a dictionary
        if not isinstance(pars, dict):
            raise DescriptionException("One of the productions is misformatted.", issue, None)
        # Check all of the required parameters are included
        if not {"status", "pipeline"} <= pars.keys():
            raise DescriptionException(f"Some of the required parameters are missing from {name}", issue, name)
        if not "comment" in pars:
            pars['comment'] = None
        return cls(event, name, **pars)
    
    def __repr__(self):
        return f"<Production {self.name} for {self.event} | status: {self.status}>"


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

        if not template_directory:
            template_directory = config.get("templating", "directory")

        #try:
        with open(os.path.join(f"{template_directory}", f"{self.pipeline}.ini"), "r") as template_file:
                liq = Liquid(template_file.read())
                rendered = liq.render(production=self)
        #except Exception as e:
        #    raise DescriptionException(f"There was a problem writing the configuration file.\n\n{e}",
        #                               production=self)

        with open(filename, "w") as output_file:
            output_file.write(rendered)
