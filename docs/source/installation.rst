.. _installationguide:

Installation Guide
==================

Using pip
---------

The preferred method for installing `Asimov` is to use `pip`, and install in a virtual environment.::
   
   pip install asimov

Using conda
-----------

If you use conda environments you can install `asimov` from conda forge by running::

  conda install -c conda-forge ligo-asimov 

Installing from source
----------------------
   
You can also install `Asimov` directly from its source, either by cloning its repository and running::
  
   pip install .

In the root of the repository, or alternatively directly from the master branch on the LIGO gitlab server by running::
  
   pip install git+https://git.ligo.org/asimov/asimov.git

You should use the package with care if installing from source; while the master branch should represent stable code, it may contain new or undocumented features, or behave unexpectedly.
