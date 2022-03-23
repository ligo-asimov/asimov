
import htcondor

def get_running():
    data = []
    for schedd_ad in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd):
        schedd = htcondor.Schedd(schedd_ad)
        jobs = schedd.query(opts=htcondor.htcondor.QueryOpts.DefaultMyJobsOnly,
                            projection=["JobBatchId"],
)
        data += jobs
    retdat = []
    for datum in data:
        if "JobBatchId" in datum:
            retdat.append(int(float(datum['JobBatchId'])))
    return retdat


data = get_running()

print(data)
