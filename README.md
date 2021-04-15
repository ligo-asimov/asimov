# Asimov

Asimov is a workflow management and automation platform for scientific analyses.

It was developed to manage and automate the parameter estimation analyses used by the LIGO, Virgo, and KAGRA collaborations to analyse gravitational wave signals, but it aims to provide tools which can be used for other workflows.

## Features

### Job monitoring and management

Asimov is able to interact with high throughput job management tools, and can submit jobs to clusters, monitor them for problems, and initiate post-processing tasks.

### Uniform pipeline interface

Asimov provides an API layer which allows a single configuration to be deployed to numerous different analysis pipelines.
Current gravitational wave pipelines which are supported are ``lalinference``, ``bayeswave``, ``RIFT``, and ``bilby``.

### Centralised configuration

Asimov records all ongoing, completed, and scheduled analyses, allowing jobs, configurations, and results to be found easily.

### Reporting overview

Asimov can provide both machine-readible and human-friendly reports of all jobs it is monitoring, while collating relevant log files and outputs.

### Results management

Your results are important, and Asimov provides special tools to help manage the outputs of analyses as well as ensuring their veracity.

## Do I need Asimov?

Asimov makes setting-up and running parameter estimation jobs easier.
It can generate configuration files for several parameter estimation pipelines, and handle submitting these to a cluster.
Whether you're setting-up a preliminary analysis for a single gravitational wave event, or analysing hundreds of events for a catalog, Asimov can help.

## Installing Asimov

Asimov is written in Python, and is available on ``pypi``. 
It can be installed by running
```
$ pip install ligo-asimov
```

## Get started

Asimov supports a variety of different ways of running, but the simplest way, running a workflow on a local machine, can be set up with a single command:

```
$ olivaw init
```

``olivaw`` is asimov's built-in management interface.

A new event can be added to your project by running

```
$ olivaw event create GW150914
```

Many analyses can be run on a single event (these are called "productions" in asimov parlence).
You can add a new lalinference production to an event as such:
```
$ olivaw production --event GW150914 --pipeline lalinference
```
For a full description of the workflow management process see the documentation.


## I want to help develop new features, or add a new pipeline

Great! We're always looking for help with developing asimov!
Please take a look at our [contributors' guide](CONTRIBUTING.rst) to get started!


## Roadmap

### Gravitic pipelines

While Asimov already supports a large number of pre-existing pipelines, and provides a straightforward interface for adding new pipelines, we also intend to support pipelines constructed using [gravitic](https://github.com/transientlunatic/gravitic), allowing experimental tools to be used without constructing an entire new pipeline, while also allowing asimov to manage the training of machine learning algorithms.


### Workflow replication, extension and duplication

Asimov will allow an existing workflow to be duplicated, in a similar way to a ``git clone``, and then extended, with new jobs gaining access to the completed jobs in the workflow.
It will also allow entire workflows to be re-run, providing a straightforward way to replicate results, or make minor modifications.


## Authors

Asimov is made by the LIGO, Virgo, and KAGRA collaborations.
The primary maintainer of the project is Daniel Williams.
Its development is supported by the Science and Technology Facilities Council.
