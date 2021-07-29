v0.3.3
======
Update to LALInference

- Updates the handling of LALInference pipelines to allow them to be templated using liquid.
- Corrects a bug in the handling of review information

v0.3.2
======
Minor bug fix.

- Corrects a bug in the PESummary call which prevented spin evolution being correctly calculated.

v0.3.1
======
Minor bug-fixes.

- Adds redshift regeneration to the PESummary call at production completion.
- Removes writing of user to bayeswave productions in ledger.

v0.3.0
======
First fully reviewed version.

Reviewed support for:
- bilby
- RIFT
- bayeswave
job creation.

Prepared for the O3a and O3b parameter estimation projects.
