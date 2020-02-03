import os
import glob
import git


class MetaRepository(object):

    def __init__(self, directory):
        self.directory = directory
        os.chdir(directory)
        repos_list = glob.glob("*")
        self.repos = {event: os.path.join(directory, event) for event in repos_list}

    def get_repo(self, event):
        return EventRepo(self.repos[event])
        



class EventRepo(object):

    def __init__(self, directory):
        self.directory = directory
        self.repo = git.Repo(directory)
    
    def find_prods(self, category="C01_offline"):
        os.chdir(os.path.join(self.directory, category))
        prods = glob.glob("Prod*.ini")
        return prods
