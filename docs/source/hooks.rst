================
Extending Asimov
================

Asimov is designed to be easy to extend with your own code which can "hook" into the various operations it carries out.

The Monitor Loop
----------------

The monitor loop in asimov does all of the heavy lifting of checking that analyses are still running, and if they've finished, checking and storing the results.
You can hook in to this loop in order to modify its behaviour, and add functionality with your own code.

`asimov.hooks.postmonitor`
~~~~~~~~~~~~~~~~~~~~~~~~~~

The post-monitor hook is run at the end of the monitor loop, and is an ideal place to put code which needs to collate or report on the status of an entire asimov project.

To use this hook you'll need to advertise your hook using the `asimov.hooks.postmonitor` endpoint, and add the name of your hook to the `hooks/postmonitor` list in the ledger file.
It is easiest to do this when you're setting-up your project by applying a file containing e.g.

.. code-block:: yaml

		kind: config
		hooks:
		  postmonitor:
		    - MyMonitorHook

		      
