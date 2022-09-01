Developing new pipelines
========================

Asimov only supports a small number of pipelines "out of the box", but allows for new pipelines to be added as plugins.

There are two broad approaches to writing a plugin for asimov.
Either you can incorporate it directly into your codebase, which is especially suitable if your pipeline is written in python, or you can write an interface plugin which allows interaction between asimov and the pipeline.

Asimov uses a feature of python packages called an "entrypoint" in order to identify pipelines which are installed with an asimov interface.

Creating an interface
---------------------

An asimov pipeline interface is simply a python class which subclasses ``asimov.pipeline.Pipeline``, and provides the pipeline specific logic to allow asimov to interact with it.

Adding an entrypoint
--------------------

In these examples we assume that the pipeline interface is a class called ``MyPipeline`` (which subclasses ``asimov.pipeline.Pipeline``), and is located in a file called ``asimov.py`` in the main package, i.e.

.. code-block::

   |- setup.py
   |- mypipeline
      |- __init__.py
      |- ...
      |- asimov.py
      |- ...
   |- ...
   

There are a number of different python packaging technologies, so we will provide examples for just a few here.
   
``setup.cfg``
~~~~~~~~~~~~~~

.. code-block:: toml

   [options]
   install_requires =
		    asimov
		    mypipeline

   [metadata]
   name = mypipeline
   version = attr: mypipeline.__version__
   description = A pipeline integration between asimov and mypipeline

   [options.entry_points]
   asimov.pipelines =
		    mypipeline = asimov:MyPipeline
