# Asimov

Asimov is a python package used to construct automated bots to do various things with parameter esimation jobs for LIGO data analysis.
There are a number of bits of code which are designed to make writing your own bot easier, and these are importable, but there are also pre-baked bots.

## Configuration

Asimov uses `INI` files in order to store configurations for the running bots.
There are a number of places where it will look for these files, in order of precedence:
```
	asimov.conf              # in the current working directory
	~/.config/asimov.conf    # in the current user's home directory
	~/.asimov                # in the current user's home directory
	/etc/asimov              # For system-wide defaults
```
Please look at the defaults which are set in the sample `.ini` file in this repository [here](asimov/asimov.conf "default config").

## Pre-made bots

### Olivaw

Olivaw is the bot which was written to manage parameter estimation jobs for the O3a catalogue paper.
Once this package is installed it can be run as 

```
$ olivaw 
```

on the command line. Note that this is expected to change in the near future as the package develops, however.

#### Job status

Olivaw keeps track of the status of PE jobs using the LIGO gitlab issue tracker.
To do this it uses a combination of issue tags and comments on the issue.

Issue tags are used to track the high-level status of the PE on an entire event.
For example, that the event is "Running" or "Ready to Run" or "Stuck".
This allows the broad behaviour of the PE on this event to be tracked through the issue boards interface on gitlab.

The current sequence of tags supported by `Olivaw` are
```
Ready to Run --> Generating PSDs --> Productions running --> Runs complete
                \                       \
             	 -------------------------------------------> Stuck
```

Each of these states is implemented as a *scoped label* in gitlab, so each state is prefixed with e.g. `C01::` in order to prevent multiple tags from this sequence being applied simultaneously.

+ The `Ready to Run` tag should be applied once the bot should start running this event. This state must be applied manually to begin job submission.
+ The `Generating PSDs` state will be applied by the bot while the `Prod0` job is running Bayeswave to produce the PSDs for the analysis.
+ The `Productions running` state will be applied once the PSDs have been generated.
+ The `Runs complete` state is applied once all of the productions have completed.
In addition to these standard states
+ The `Stuck` state will be applied if the bot detects a problem with one of the running productions.

Each production is tracked using the description on a git issue for the event.
This data will have the general form of
```
# Run information
Some text about the robot tracking here.
---
name: S200311bg
repository: https://git.ligo.org/pe/O3/S200311bg

productions:
	- Prod0: 
		- status: Wait
		- pipeline: bayeswave
		- comment: PSD production
	- Prod1:
		- status: Wait
		- pipeline: lalinference
		- comment: IMRPhenomD
	- Prod2:
		- status: Wait
		- pipeline: bilby
		- comment: NRSur
---
```
where it's essential that at least the name and the repository for the event are specified.

The full specification for this format can be found in the documentation for the package.

For each production:
The `rundir` line simply records the location of the run directory on the cluster's file system.

The `status` line tracks the state of the job. 
The sequence of these states is
```
Start --> <job id> --> Finished --> Uploaded (--> Finalised)*

* The finalised step is only reached if the run is manually marked as preferred, see below for details.
```

+ `Start` : This job should be started automatically. This state must be applied manually.
+ `Blocked` : Do not start this job automatically. (Deprecated; the bot now only starts productions which are labelled with the `Start` state)
+ `Preferred` : This production is the preferred run; Upload it as the preferred run. Must be applied manually to runs which have been marked as `uploaded`.
+ `Stopped` : This run has been manually stopped; stop tracking it. Must be applied manually. 
+ `Stuck` : A problem has been discovered with this run, and needs manual intervention.
+ `Uploaded` : This event has been uploaded to the event repository.
+ `Restart` : This job should be restarted by Olivaw. Must be applied manually.
+ `Manualupload` : The results of this run should not be uploaded by the bot. Must be applied manually.
+ `Finised` : This job has finished running and the results are ready to be uploaded on the next bot check.
+ `Finalised` : This job has been uploaded as the preferred job and is therefore finalised.

In addition to these string states, the bot will apply an integer state which indicates the condor job number of a running job.

Some states can be combined, and separated with a comma: for example, preferred should always be applied to a job which has been marked as "uploaded", so should appear as "uploaded, preferred" in order for Olivaw to attempt to finalise this run.



#### Configuration

In order to run you should ensure that the `asimov` config file has the following values set:

```
[gitlab]
# Gitlab access settings
# To use the gitlab issue tracker the bot needs to have a gitlab access token, which should be 
# added here. Make sure that this is secure, as it allows considerable access to your gitlab
# account
token = 
# Set the event_label to the label which is used to indicate that an issue on the tracker represents an
# event, e.g. trigger
event_label = trigger

[mattermost]
# In order to post to mattermost the bot needs a webhook url
webhook_url = 

[olivaw]
# The tracking_repository is the git repository on gitlab which will be used for issue tracking
# You'll need to put the repository's numerical id here
tracking_repository = 
# The location where you've cloned the metarepository of all event repositories to
metarepository = /home/daniel.williams/events/O3/o3a_catalog_events
# The milestone which indicates that an issue is being tracked by this bot
milestone = PE: C01 Reruns
# The location where the bot should output summary information about its run
summary_report = /home/daniel.williams/public_html/LVC/projects/O3/C01/summary.html
# The types of run which are being monitored
run_category = C01_offline
```

