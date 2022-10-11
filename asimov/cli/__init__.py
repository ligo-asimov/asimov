"""
Provide the command line interface components for asimov.
"""

frametypes = {
    "L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
    "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
    "V1": "V1Online",
}

CALIBRATION_NOTE = """
## Calibration envelopes
The following calibration envelopes have been found.
```yaml
---
{}
---
```
"""


ACTIVE_STATES = {"ready", "running", "stuck", "finished", "processing", "stop"}
