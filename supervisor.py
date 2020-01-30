#! /usr/bin/env python3

"""
This script is designed to interface with a gitlab project
and use issues defined in its issue tracker to run Parameter Estimation 
jobs, and manage them.

Authors
-------
Daniel Williams <daniel.williams@ligo.org>
"""

import gitlab
import json
import time
import os

import htcondor

access_token = os.environ['GITLAB_TOKEN'] # 
project_id = 3816
uber_repo = "" # The repository which contains all of the submodularised event repositories.

gl = gitlab.Gitlab('https://git.ligo.org', private_token=access_token)
pe_catalogue = gl.projects.get(project_id)

with open("pe-robot.json", "r") as data:
    runs = json.load(data)

schedd_ad = htcondor.Collector().locate(htcondor.DaemonTypes.Schedd)
schedd = htcondor.Schedd(schedd_ad)


if __name__ == "__main__":
    while True:
        for issue in pe_catalogue.issues.list(labels=['trigger'], per_page=100):
            if not issue.title in runs.keys():
                # This is an event we've not seen before
                runs[issue.title] = {}
                runs[issue.title]['issue_id'] = issue.id
                runs[issue.title]['issue_labels'] = issue.labels
            if "C01::Robot" in issue.labels:
                print(f("I need to start {issue.title}"))
            elif "C01::Prod0 Running" in issue.labels:
                try:
                    cluster_id = runs[issue.title]['cluster_id']
                except:
                    print(f"I can't find the cluster ID for {issue.title}.")
                jobs = schedd.xquery(requirements="ClusterId == {}".format(cluster_id))
                for job in jobs:
                    if job['JobStatus'] == 2:
                        # The job is still running
                        pass
                    elif job['JobStatus'] == 5:
                        # The job is held.
                        # Mark it as stuck
                        issue.labels = issue.labels + ["C01::Stuck"]
                        issue.notes.create({'body': 'This job was held at {}'.format(time.now())})
                print(f"I need to check if the PSDs are ready for {issue.title}")
            elif "C01::Prod1 Running" in issue.labels:
                print(f"I need to check if the jobs are finished for {issue.title}")
            else:
                print(f"I need to check if {issue.title} is running")
        time.sleep(300)
