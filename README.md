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

```$ olivaw```

on the command line. Note that this is expected to change in the near future as the package develops, however.

#### Configuration

In order to run you should ensure that the `asimov` config file has the following values set:
```

```
[gitlab]
# Gitlab access settings
# To use the gitlab issue tracker the bot needs to have a gitlab access token, which should be 
# added here. Make sure that this is secure, as it allows considerable access to your gitlab
# account
token = 
# Set the event_label to the label which is used to indicate that an issue on the tracker represents an
# event, e.g. `trigger`
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

