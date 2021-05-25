"""
Trigger handling code.
"""

import collections.abc
import yaml
import os
import glob


import networkx as nx

from .ini import RunConfiguration
from .git import EventRepo
from .review import Review
from asimov import config
from asimov.storage import Store

from liquid import Liquid

from ligo.gracedb.rest import GraceDb, HTTPError
from copy import copy, deepcopy


def update(d, u):
    """Recursively update a dictionary."""
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

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
        else:
            print(self.__repr__())



            
class Event:
    """
    A specific gravitational wave event or trigger.
    """

    def __init__(self, name, repository=None, update=False, **kwargs):
        """
        Parameters
        ----------
        update : bool
           Flag to determine if the event repo should be updated 
           when it is loaded. Defaults to False.
        """
        self.name = name
        if "working_directory" in kwargs:
            self.work_dir = kwargs['working_directory']
        else:
            self.work_dir = None

        if repository:
            if "git@" in repository or "https://" in repository:
                self.repository = EventRepo.from_url(repository,
                                                     self.name,
                                                     self.work_dir,
                                                     update=update)
            else:
                self.repository = EventRepo(repository)
        else:
            self.repository = repository

        if "psds" in kwargs:
            self.psds = kwargs["psds"]
        else:
            self.psds = {}
            
        self.meta = kwargs

        self.issue_object = None
        if "issue" in kwargs:
            if kwargs['issue']:
                self.issue_object = kwargs.pop("issue")
                self.from_notes()
        else:
            self.issue_object = None

        self.productions = []
        self.graph = nx.DiGraph()
        
        if 'productions' in kwargs:
            for production in kwargs['productions']:
                try:
                    self.add_production(
                        Production.from_dict(production, event=self, issue=self.issue_object))
                except DescriptionException as error:
                    error.submit_comment()
            

        self.productions = []
        self.graph = nx.DiGraph()
        
        if 'productions' in kwargs:
            for production in kwargs['productions']:
                try:
                    self.add_production(
                        Production.from_dict(production, event=self, issue=self.issue_object))
                except DescriptionException as error:
                    error.submit_comment()
            

        self._check_required()
        
        if ("interferometers" in self.meta) and ("calibration" in self.meta):
            try:
                self._check_calibration()
            except DescriptionException:
                pass        

    def _check_required(self):
        """
        Find all of the required metadata is provided.
        """
        return True
        #required = {"interferometers"}
        #if not (required <= self.meta.keys()):
        #    raise DescriptionException(f"Some of the required parameters are missing from this issue. {required-self.meta.keys()}")
        #else:
        #    return True
        
    def _check_calibration(self):
        """
        Find the calibration envelope locations.
        """
        if ("calibration" in self.meta) and (set(self.meta['interferometers']).issubset(set(self.meta['calibration'].keys()))):
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
    def from_yaml(cls, data, issue=None, update=False, repo=True):
        """
        Parse YAML to generate this event.

        Parameters
        ----------
        data : str
           YAML-formatted event specification.
        issue : int
           The gitlab issue which stores this event.
        update : bool 
           Flag to determine if the repository is updated when loaded.
           Defaults to False.

        Returns
        -------
        Event
           An event.
        """
        data = yaml.safe_load(data)
        if not {"name",} <= data.keys():
            raise DescriptionException(f"Some of the required parameters are missing from this issue.")
        if not repo and "repository" in data:
            data.pop("repository")
        event = cls(**data, issue=issue, update=update)

        if issue:
            event.issue_object = issue
            event.from_notes()

        #for production in data['productions']:
        #    try:
        #        event.add_production(
        #            Production.from_dict(production, event=event, issue=issue))
        #    except DescriptionException as error:
        #        error.submit_comment()
        return event

    @classmethod
    def from_issue(cls, issue, update=False, repo=True):
        """
        Parse an issue description to generate this event.


        Parameters
        ----------
        update : bool 
           Flag to determine if the repository is updated when loaded.
           Defaults to False.
        """

        text = issue.text.split("---")

        event = cls.from_yaml(text[1], issue, update=update, repo=repo)
        event.text = text
        # event.from_notes()

        return event

    def from_notes(self):
        """
        Update the event data from information in the issue comments.

        Uses nested dictionary update code from
        https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth#3233356
        """


        notes_data = self.issue_object.parse_notes()
        for note in notes_data:
            update(self.meta, note)

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

    def to_dict(self):
        data = {}
        data['name'] = self.name

        if "repository" in data:        
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
            prod_names = []
            for key, value in prod_dict.items():
                if production.name in prod_names: continue
                if key in data:
                    if data[key] == value:
                        dupes.append(key)
            for dupe in dupes:
                prod_dict.pop(dupe)
            prod_names.append(production.name)
            data['productions'].append({production.name: prod_dict})

        if "issue" in data:
            data.pop("issue")

        return data
        
    def to_yaml(self):
        """Serialise this object as yaml"""
        data = self.to_dict()

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
        if status:
            self.status_str = status.lower()
        else:
            self.status_str = "none"
        self.pipeline = pipeline.lower()
        self.comment = comment
        self.meta = deepcopy(self.event.meta)
        if "productions" in self.meta:
            self.meta.pop("productions")

        self.meta = update(self.meta, kwargs)

        if "review" in self.meta:
            self.review = Review.from_dict(self.meta['review'], production=self)
            self.meta.pop("review")
        else:
            self.review = Review()
        
        # Check that the upper frequency is included, otherwise calculate it
        if "quality" in self.meta:
            if ("high-frequency" not in self.meta['quality']) and ("sample-rate" in self.meta['quality']):
                # Account for the PSD roll-off with the 0.875 factor
                self.meta['quality']['high-frequency'] = int(0.875 * self.meta['quality']['sample-rate']/2)


                
        # Get the data quality recommendations
        if 'quality' in self.event.meta:
            self.quality = self.event.meta['quality']
        else:
            self.quality = {}

        if ('quality' in self.meta):
            if ('quality' in kwargs):
               self.meta['quality'].update(kwargs['quality'])
            self.quality = self.meta['quality']
            
        if ('quality' in self.meta) and ("event time" in self.meta):
            if "segment start" not in self.meta['quality']:
                self.meta['quality']['segment start'] = self.meta['event time'] - self.meta['quality']['segment-length'] + 2
                self.event.meta['quality']['segment start'] = self.meta['quality']['segment start']

            
        # Gather the appropriate prior data for this production
        if 'priors' in self.meta:
            self.priors = self.meta['priors']

        # Need to fetch the correct PSDs for this sample rate
        if 'psds' in self.meta:
            if self.quality['sample-rate'] in self.meta['psds']:
                self.psds = self.meta['psds'][self.quality['sample-rate']]
            else:
                self.psds = {}
        else:
            self.psds = {}


            
        for ifo, psd in self.psds.items():
            if self.event.repository:
                self.psds[ifo] = os.path.join(self.event.repository.directory, psd)
            else:
                self.psds[ifo] = psd

        self.category = config.get("general", "calibration_directory")
        if "needs" in self.meta:
            self.dependencies = self._process_dependencies(self.meta['needs'])
        else:
            self.dependencies = None

    def _process_dependencies(self, needs):
        """
        Process the dependencies list for this production.
        """
        return needs


    def results(self, filename=None, handle=False, hash=None):
        store = Store(root=config.get("storage", "results_store"))
        if not filename:
            try:
                items = store.manifest.list_resources(self.event.name, self.name)
                return items
            except KeyError:
                return None
        elif handle:
            return open(store.fetch_file(self.event.name, self.name, filename, hash), "r")
        else:
            return store.fetch_file(self.event.name, self.name, filename, hash=hash)

    @property
    def rel_psds(self):
        """
        Return the relative path to a PSD for a given event repo.
        """
        rels = {}
        for ifo, psds in self.psds.items():
            psd = self.psds[ifo]
            psd = psd.split("/")
            rels[ifo] = "/".join(psd[-3:])
        return rels

    @property
    def reference_frame(self):
        """
        Calculate the appropriate reference frame.
        """
        ifos = self.meta['interferometers']
        if len(ifos) == 1:
            return ifos[0]
        else:
            return "".join(ifos[:2])

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
        finished_states = ["uploaded"]
        return self.status in finished_states
        
    @property
    def status(self):
        return self.status_str.lower()

    @status.setter
    def status(self, value):
        self.status_str = value.lower()
        if self.event.issue_object != None:
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

        output[self.name]['review'] = self.review.to_dicts()
        
        if "quality" in self.meta:
            output[self.name]['quality'] = self.meta['quality']
        if "priors" in self.meta:
            output[self.name]['priors'] = self.meta['priors']
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
            if self.event.issue_object != None:
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
            if self.event.issue_object != None:
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
            coinc = self.event.repository.find_coincfile(self.category)
            return coinc

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


        if "template" in self.meta:
            template = f"{self.meta['template']}.ini"
        else:
            template = f"{self.pipeline}.ini"

        try:
            template_directory = config.get("templating", "directory")
            template_file = os.path.join(f"{template_directory}", template)
        except:
            from pkg_resources import resource_filename
            template_file = resource_filename("asimov", f'configs/{template}')
        
        config_dict = {s: dict(config.items(s)) for s in config.sections()}

        with open(template_file, "r") as template_file:
            liq = Liquid(template_file.read())
            rendered = liq.render(production=self, config=config)

        with open(filename, "w") as output_file:
            output_file.write(rendered)
