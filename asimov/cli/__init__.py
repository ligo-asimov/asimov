"""
Provide the command line interface components for asimov.
"""

import glob

import numpy as np

from asimov import config
from asimov import gitlab

from asimov.utils import find_calibrations
from asimov.pipelines import known_pipelines


frametypes= {"L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
             "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
             "V1": "V1Online"}

CALIBRATION_NOTE = """
## Calibration envelopes
The following calibration envelopes have been found.
```yaml
---
{}
---
```
"""


ACTIVE_STATES = {"ready", "running", "stuck", "finished", "processing", "stop"}


def add_data(event, yaml_data, json_data=None):
    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

   
    if yaml_data:
        with open(yaml_data, "r") as datafile:
            data = yaml.safe_load(datafile.read())

        gitlab_event[0].event_object.meta = update(gitlab_event[0].event_object.meta, data)
        gitlab_event[0].update_data()
        print(gitlab_event[0].event_object.meta)

        
