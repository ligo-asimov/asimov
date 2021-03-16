@click.group()
def collection():
    """
    Commands to handle collections.
    """
    pass

@click.option("--namefile", "names", default=None, help="The mapping between old and new names for events.")
@click.option("--old", "oldname", default=None, help="The old superevent ID for this event.")
@click.argument("name")
@click.argument("superevent")
@olivaw.command()
def create(superevent, name, names=None, oldname=None):
    """
    Create a new event record on the git issue tracker from the GraceDB dev server.

    Parameters
    ----------
    superevent : str
       The ID of the superevent to be used from GraceDB
    name : str
       The name of the event to be recorded in the issue tracker
    names : path, optional
        The path to the name file which maps between old and new super event IDs
    oldname: str, optional
        The old name of the event.
    """
    server, repository = connect_gitlab()
    from ligo.gracedb.rest import GraceDb, HTTPError 
    client = GraceDb(service_url=config.get("gracedb", "url"))
    r = client.ping()
    data = client.superevent(superevent).json()
    event_data = client.event(data['preferred_event']).json()

    if names:
        with open(names, "r") as datafile:
            names = json.load(datafile)
        old_superevent = names['SNAME'][name]
    elif oldname:
        old_superevent = oldname
    else:
        old_superevent = superevent
        
    event_url = f"https://catalog-dev.ligo.org/events/{data['preferred_event']}/view/"
    event = Event(name=name,
                  repository=f"git@git.ligo.org:pe/O3/{old_superevent}",
                  #gid=data['preferred_event'],
                  #gid_url=event_url,
                  calibration = {},
                  interferometers=event_data['instruments'].split(","),
    )
    event.meta['old superevent'] = old_superevent
    event.meta['event time'] = event_data['gpstime']
    event.meta['working directory'] = f"{config.get('general', 'rundir_default')}/{name}"
    gitlab.EventIssue.create_issue(repository, event, issue_template="/home/daniel.williams/repositories/asimov/scripts/outline.md")

@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--pipeline", "pipeline", default=None, help="The pipeline which the job should use")
@click.option("--family", "family", default=None, help="The family name of the production, e.g. `prod`.")
@click.option("--comment", "comment", default=None, help="A comment to attach to the production")
@click.option("--needs", "needs", default=None, help="A list of productions which are requirements")
@click.option("--template", "template", default=None, help="The configuration template for the production.")
@click.option("--status", "status", default=None, help="The initial status of the production.")
@olivaw.command(help="Add a new production to an event")
def production(event, pipeline, family, comment, needs, template, status):
    """
    Add a new production to an event.

    """
    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)
    event = gitlab_event[0].event_object
    #
    event_prods = event.productions
    names = [production.name for production in event_prods]
    family_entries = [int(name.split(family)[1]) for name in names if family in name]
    #
    if "bayeswave" in needs:
        bw_entries = [production.name for production in event_prods if "bayeswave" in production.pipeline.lower()]
        needs = bw_entries
    #
    production = {"comment": comment, "pipeline": pipeline, "status": status}
    if needs:
        production['needs'] = needs
    if template:
        production['template'] = template
    if len(family_entries)>0:
        number = max(family_entries)+1
    else:
        number = 0
    production_dict = {f"{family}{number}": production}
    production = Production.from_dict(production_dict, event=event)
    #
    click.echo(production)
    event.add_production(production)
    gitlab_event[0].update_data()
    
@click.option("--event", "event", help="The event to be populated.")
@click.option("--yaml", "yaml", default=None)
@click.option("--ini", "ini", default=None)
@olivaw.command()
def populate(event, yaml, ini):
    """
    Populate an event ledger with data from ini or yaml files.
    """
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=[event])
    event = gitlab_events[0]
    event_o = event.event_object
    # Check the calibration files for this event
    click.echo("Check the calibration.")
    calibration(event_o.name)
    # Check the IFOs for this event
    click.echo("Check the IFO list")
    try:
        checkifo(event_o.name)
    except:
        pass

    # Add default data
    click.echo("Add in default channel data.")
    if yaml:
        add_data(event_o.name, yaml)

@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--json", "json_data", default=None)
@olivaw.command(help="Add data from the configurator.")
def configurator(event, json_data=None):    
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

   
    if json_data:
        with open(json_data, "r") as datafile:
            data = json.load(datafile)

    new_data = {"quality": {}, "priors": {}}
    new_data["quality"]["sample-rate"] = data["srate"]
    new_data["quality"]["lower-frequency"] = {}
    new_data["quality"]["upper-frequency"] = int(0.875 * data["srate"]/2)
    new_data["quality"]["start-frequency"] = data['f_start']
    new_data["quality"]["segment-length"] = data['seglen']
    new_data["quality"]["window-length"] = data['seglen']
    new_data["quality"]["psd-length"] = data['seglen']

    def decide_fref(freq):
        if (freq >= 5) and (freq < 10):
            return 5
        else:
            return floor(freq/10)*10

    new_data["quality"]["reference-frequency"] = decide_fref(data['f_ref'])

    new_data["priors"]["amp order"] = data['amp_order']
    new_data["priors"]["chirp-mass"] = [data["chirpmass_min"], data["chirpmass_max"]]

    update(gitlab_event[0].event_object.meta, new_data)
    print(gitlab_event[0].event_object.meta)
    gitlab_event[0].update_data()


#@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
#@olivaw.command()
def checkifo(event):
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=event)

    for event in gitlab_events:
        if "event time" not in event.event_object.meta:
            print(f"Time not found {event.event_object.name}")
        time = event.event_object.meta['event time']
        gpsstart=time-600
        gpsend=time+600
        bits = ['Bit 0', 'Bit 1', 'Bit 2']

        active_ifo = []
        for ifo in ["L1", "H1", "V1"]:
    
            urls = find_urls(site=f"{ifo[0]}", frametype=frametypes[ifo], gpsstart=gpsstart, gpsend=gpsend)
            datacache = Cache.from_urls(urls)
            if len(datacache) == 0:
                print(f"No {ifo} data found.")
                continue
            state = gwpy.timeseries.StateVector.read(
                datacache, state_vector_channel[ifo], start=gpsstart, end=gpsend,
                pad=0  # padding data so that errors are not raised even if found data are not continuous.
            )
            if not np.issubdtype(state.dtype, np.unsignedinteger):
                # if data are not unsigned integers, cast to them now so that
                # we can determine the bit content for the flags
                state = state.astype(
                    "uint32",
                    casting="unsafe",
                    subok=True,
                    copy=False,
                )
            flags = state.to_dqflags()

            segments = flags[bits[0]].active
            for bit in bits:
                segments -= ~flags[bit].active

            if len(segments)>0: active_ifo += [ifo]
        print(event.event_object.name)
        if event.event_object.meta['interferometers'] != active_ifo:
            print(f"Gitlab data\t{event.event_object.meta['interferometers']}")
            print(f"Recommended IFOS\t{active_ifo}")
        event.event_object.meta['interferometers'] = active_ifo
        event.update_data()




