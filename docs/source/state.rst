------------
Asimov state
------------

In order to track each of the jobs asimov monitors it employs a simple state machine on each production.
This state is tracked within :ref:`the production ledger` for each production with the value of ``status``.

Under normal running conditions the sequence of these states is
```
ready --> <job id> --> finished --> processing --> uploaded (--> Finalised)*

* The finalised step is only reached if the run is manually marked as preferred, see below for details.

A number of additional states are also possible which interupt the normal flow of the job through ``asimov``'s workflow.
  
```

+ ``ready`` : This job should be started automatically. This state must be applied manually. The job will then be started once its dependencies are met.
+ ``stopped`` : This run has been manually stopped; stop tracking it. Must be applied manually. 
+ ``stuck`` : A problem has been discovered with this run, and needs manual intervention.
+ ``uploaded`` : This event has been uploaded to the event repository.
+ ``restart`` : This job should be restarted by Olivaw. Must be applied manually.
+ ``finished`` : This job has finished running and the results are ready to be processed on the next bot check.
+ ``processing`` : The results of this job are currently being processed by ``PESummary``.
+ ``uploaded`` : This job has been uploaded to the data store.
