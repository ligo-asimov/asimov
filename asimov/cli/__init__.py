"""
Provide the command line interface components for asimov.
"""

frametypes = {
    "L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
    "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
    "V1": "V1Online",
}

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

known_pipelines = {"bayeswave": BayesWave,
                   "bilby": Bilby,
                   "rift": Rift,
                   "lalinference": LALInference}




def find_calibrations(time):
    """
    Find the calibration file for a given time.
    """
    if time < 1190000000:
        dir = "/home/cal/public_html/uncertainty/O2C02"
        virgo = "/home/carl-johan.haster/projects/O2/C02_reruns/V_calibrationUncertaintyEnvelope_magnitude5p1percent_phase40mraddeg20microsecond.txt"
    elif time < 1290000000:
        dir = "/home/cal/public_html/uncertainty/O3C01"
        virgo = "/home/cbc/pe/O3/calibrationenvelopes/Virgo/V_O3a_calibrationUncertaintyEnvelope_magnitude5percent_phase35milliradians10microseconds.txt"
    data_llo = glob.glob(f"{dir}/L1/*LLO*FinalResults.txt")
    times_llo = {int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_llo}
    
    data_lho = glob.glob(f"{dir}/H1/*LHO*FinalResults.txt")
    times_lho = {int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_lho}
        
    keys_llo = np.array(list(times_llo.keys())) 
    keys_lho = np.array(list(times_lho.keys())) 

    return {"H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]], 
            "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]], 
            "V1": virgo}



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

        
