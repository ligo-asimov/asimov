"""
Provide the command line interface components for asimov.
"""

from asimov import config
from asimov import gitlab

from asimov.pipelines.bayeswave import BayesWave
from asimov.pipelines.lalinference import LALInference
from asimov.pipelines.rift import Rift
from asimov.pipelines.bilby import Bilby


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


ACTIVE_STATES = {"running", "stuck", "finished", "processing", "stop"}

known_pipelines = {"bayeswave": BayesWave,
                   "bilby": Bilby,
                   "rift": Rift,
                   "lalinference": LALInference}


def connect_gitlab():
    """
    Connect to the gitlab server.

    Returns
    -------
    server : `Gitlab`
       The gitlab server.
    repository: `Gitlab.project`
       The gitlab project.
    """
    server = gitlab.gitlab.Gitlab('https://git.ligo.org',
                              private_token=config.get("gitlab", "token"))
    repository = server.projects.get(config.get("olivaw", "tracking_repository"))
    return server, repository


def find_calibrations(time):
    with open("/home/daniel.williams/repositories/asimov/scripts/LLO_calibs.txt") as llo_file:
        data_llo = llo_file.read().split("\n")
        data_llo = [datum for datum in data_llo if datum[-16:]=="FinalResults.txt"]
        times_llo = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_llo}
    
    with open("/home/daniel.williams/repositories/asimov/scripts/LHO_calibs.txt") as llo_file:
        data_lho = llo_file.read().split("\n")
        data_lho = [datum for datum in data_lho if datum[-16:]=="FinalResults.txt"]
        times_lho = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_lho}
        
    keys_llo = np.array(list(times_llo.keys())) 
    keys_lho = np.array(list(times_lho.keys())) 

    return {"H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]], "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]], "V1": "/home/cbc/pe/O3/calibrationenvelopes/Virgo/V_O3a_calibrationUncertaintyEnvelope_magnitude5percent_phase35milliradians10microseconds.txt"}

def calibration(event):
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=event)
    # Update existing events
    for event in gitlab_events:
        if "disable_repo" in event.event_object.meta:
            if event.event_object.meta['disable_repo'] == True:
                continue
        try:
            event.event_object._check_calibration()
        except DescriptionException:
            print(event.title)
            time = event.event_object.meta['event time'] 

            calibrations = find_calibrations(time)
            print(calibrations)
            # try:
            for ifo, envelope in calibrations.items():
                description = f"Added calibration {envelope} for {ifo}."
                try:
                    event.event_object.repository.add_file(os.path.join(f"/home/cal/public_html/uncertainty/O3C01/{ifo}", envelope), f"C01_offline/calibration/{ifo}.dat", 
                                                       commit_message=description)
                except GitCommandError as e:
                    if "nothing to commit," in e.stderr:
                        pass
                calibrations[ifo] = f"C01_offline/calibration/{ifo}.dat"
            envelopes = yaml.dump({"calibration": calibrations})
            event.add_note(CALIBRATION_NOTE.format(envelopes))


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

        
