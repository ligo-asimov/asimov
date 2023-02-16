---------------------
The production ledger
---------------------

In order to construct and monitor on-going PE jobs, asimov stores metadata for each gravitational wave event and for each PE job (or "production" in `asimov` terminology).

These metadata are stored in the event's *production ledger*, which is specified in `yaml` format.

A number of fields are required for `asimov` to correctly process an event, while a number of additional fields will allow it to perform more operations automatically, or over-ride defaults.

Normally you shouldn't need to edit the ledger file directly, but if you're setting up new analyses or want to check the configuration of a pre-existing analysis then it can be helpful to have an understanding of the quantities contained in it.

