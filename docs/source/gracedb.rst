=========================
Getting data from GraceDB
=========================

One of the major sources of data about gravitational wave events is `GraceDB`, a database of gravitational wave triggers which have been identified by one of many searches.

GraceDB clusters these triggers into "superevents", and normally we will want to request data from one of these superevents in order to start an analysis with `asimov`.


Adding an event from the CLI
----------------------------

If you're interacting with an asimov project using the command line interface you can directly download information about a trigger and create an event in the project.

If you want to pull information from non-public events you'll first need to ensure that you have a LIGO proxy set up.
The easiest way to do this as a normal user is just to run `ligo_proxy_init`:
::
   $ ligo_proxy_init isaac.asimov

and then provide your password to set up a proxy.
If you're working with publically available triggers then you can skip this step, and asimov will gather all of the publically available data which it can.

::
   $ asimov event create --superevent S200316bj

.. note::
   
   `GraceDB` will only provide a small amount of the total information which is needed to set up an analysis.
   You'll need things like default data settings before you can start an analysis.

Getting a set of events from `GraceDB`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes it's helpful to be able to gather a large set of events from `GraceDB` according to some criteria.
You can do this by specifying the search criterion on the command line, and all of the retrieved events will be created in the project.
For example:

::
   $ asimov event create --search "label: PE_READY"

will search `GraceDB` for all events marked as "PE READY" and will add them to the project.

A complete description of the query language for `GraceDB` can be found in its documentation: https://gracedb.ligo.org/documentation/queries.html.


