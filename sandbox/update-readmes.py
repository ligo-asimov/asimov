import ast
import subprocess, os
from shutil import copy
from asimov import gitlab, mattermost
from asimov import config
from asimov import condor, git
from asimov.ini import RunConfiguration

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))


uber_repository = git.MetaRepository(config.get("olivaw", "metarepository"))

events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

from pesummary.gw.file.read import read


class SummaryTable(object):
    """
    Construct a summary table which describes the contents of a PE Summary file.
    """

    def __init__(self, event, summaryfile):
        """
        Load a PE Summary file to... summarise..

        Parameters
        ----------
        event : EventIssue
           The event issue for this event.
        summaryfile : str or path-like object
           The location of the summary file to be summarised.
        """

        self.summaryfile = read(summaryfile)
        self.event = event
        self.webdir = f"https://ldas-jobs.ligo.caltech.edu/~daniel.williams/LVC/projects/O3/preferred/{event.title}"

    def summarise(self):
        """
        Produce a markdown-formatted output which fully describes this summary.
        """
        
        output = """"""
        output += f"# {self.event.title}\n"

        output += """
| Run  | Code Version | Approx | IFOs | flow (Hz) | Results | Samples | PSDs | Calibration | Notes | Contact 
|----- | -----------  | ------ | ---- | --------  | -----  | -----  | ----- | -----  | -----  | -----|\n"""
        priors = {}
        for label in self.summaryfile.labels:
            run_config = RunConfiguration(self.summaryfile.config[label])
            engine = run_config.get_engine()
            priors[label] = engine
            flow = run_config.ini.get("lalinference", "flow")
            psds = len(self.summaryfile.psd[label])
            calibration = len(self.summaryfile.calibration[label])
            output += f"| {label} | | {engine['approx']} | {run_config.get_ifos()} | {flow} | | | {psds} | {calibration} | | daniel.williams | \n"

        output += "\n## Priors\n"
        for label in self.summaryfile.labels:
            output += f"## {label}\n"
            output += f"```\n"
            for key, value in priors[label].items():
                output += f"{key} = {value}\n"
            output += "```\n"


        return output
        

    def __repr__(self):
        return self.summarise()
    
    def __str__(self):
        return self.summarise()

def main():
    
    for event in events:
        print(event.title)
        if not "Preferred cleaned" in event.labels:
           continue

        try:
            repo = uber_repository.get_repo(event.title)
        except:
            print(f"{event.title} missing from the uberrepo")
            continue

        try:
            preferred_file = os.path.join(repo.directory, "Preferred", "PESummary_metafile", "posterior_samples.h5")
            preferred_readme = os.path.join(repo.directory, "Preferred", "README.md")
            table = SummaryTable(event=event, summaryfile=preferred_file)
        except OSError as e:
            print(e)
            continue

        readme_path = os.path.join(repo.directory, "Preferred", "README.md")


        with open(readme_path, "w") as preferred_readme:
                  print(preferred_readme.write(table.summarise()))

        try:
            repo.repo.git.add(readme_path)
            repo.repo.git.commit(m=":robot: Updated the preferred directory readme.")
            repo.repo.git.push()
        except git.git.exc.GitCommandError as e:
            print(e)

main()
