# PyTessent
This contains a small library enabling creation of `tessent -shell` subprocesses that can receive commands as strings sent from Python and return resulting output strings.


## Example Usage
```python
from pytessent import PyTessent

# create "tessent -shell" process and write log file to tessent.log
pt = PyTessent.launch(timeout=None, logfile="tessent.log")

# send tessent command to set context
pt.sendCommand("set_context patterns -scan")

# Read Tessent flat model
flat_model_path = "/storage/industry_data/globalfoundries/12LP_STS/12LP_STS_Flatmodels/v1.0_12LPQTV_STS_lym0_stuck.flat.gz"
pt.sendCommand(f"read_flat_model {flat_model_path}")

# add faults to design, create patterns
pt.sendCommand("add_faults -all")
pt.sendCommand("create_patterns")

# report coverage stats, store in string (for parsing, etc...)
stats_str = pt.sendCommand("report_statistics")

# close tessent -shell process
pt.close()
```

## Installation




## Notes

**Requires:**
- *pexpect* Python Library [https://pexpect.readthedocs.io/en/stable/](https://pexpect.readthedocs.io/en/stable/)

**Assumes:**
- `SETUP> ` and `ANALYSIS> ` are the two prompts that are expected from Tessent shell subprocess, used by *pexpect* library to determine when command has completed.