import os
import glob
import git


class MetaRepository(object):

    def __init__(self, directory):
        self.directory = directory

        repos_list = glob.glob("*")
        self.repos = {event, os.path.join(directory, event) for event in repos_list}

    def get_repo(self, event):
        return EventRepo(self.repos[event])
        



class EventRepo(object):
    pass
