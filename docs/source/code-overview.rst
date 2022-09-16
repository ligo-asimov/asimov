========================
Code overview for asimov
========================

User interface
--------------

Python modules
--------------

.. graphviz::

   digraph {
         "asimov" -> ".analysis";
	 "asimov" -> ".condor";
	 "asimov" -> ".database";
	 "asimov" -> ".event";
	 "asimov" -> ".git";
	 "asimov" -> ".gitlab";
	 "asimov" -> ".ini";
	 "asimov" -> ".ledger";
	 "asimov" -> ".locutus";
	 "asimov" -> ".logging";
	 "asimov" -> ".mattermost";
	 "asimov" -> ".olivaw";
         "asimov" -> ".pipelines";
	 "asimov" -> ".pipeline";
	 ".pipeline" -> ".bilby";
	 ".pipeline" -> ".rift";
	 ".pipeline" -> ".lalinference";
	 ".pipeline" -> ".bayeswave";
	 "asimov" -> ".review";
	 "asimov" -> ".storage";
 	 "asimov" -> ".testing";
         "asimov" -> ".utils";
            }

Workflow
--------
