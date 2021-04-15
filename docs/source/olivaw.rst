Managing projects with Olivaw
=============================

Olivaw is the commandline interface for asimov which is designed to make working with your project easier.

Creating projects
-----------------

You can use olivaw to produce a new project, and set up the required directory structure automatically.

The easiest way to do this is by running

.. code-block:: console

		$ olivaw init "Test project"

Which will convert the current directory into an asimov project directory, including producing the ledger file, and creating directories for results storage.

It is possible to customise the project in a number of ways, including specifying alternative locations for the various subdirectories (though you should do this with care).

.. click:: asimov.olivaw:olivaw
   :prog: olivaw
   :commands: init
   :nested: full

