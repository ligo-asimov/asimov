import os
import glob
import git


class MetaRepository(object):

    def __init__(self, directory):
        self.directory = directory

        repos_list = glob.glob("*")
        self.repos = {event: os.path.join(directory, event) for event in repos_list}

    def get_repo(self, event):
        return EventRepo(self.repos[event])
        



class EventRepo(object):

    def __init__(self, directory):

        self.repo = git.Repo(directory)
    
    def find_prods(self, category="C01_offline"):
        prods = glob.glob(os.path.join(directory, category, "Prod*.ini"))
        return prods
