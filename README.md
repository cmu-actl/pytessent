# PyTessent
This contains a small library enabling creation of `tessent -shell` subprocesses that can receive commands as strings sent from Python and return resulting output strings.


## Example Usage
```python
import pytessent

ptf = pytessent.PyTessentFactory()  # create PyTessentFactory object
pt = ptf.launch()  # create "tessent -shell" process

pt.sendCommand("set_context patterns -scan")  # send tessent command to set context

# read flat model (from GF)
flat_model_path = "/storage/industry_data/globalfoundries/12LP_STS/12LP_STS_Flatmodels/v1.0_12LPQTV_STS_lym0_stuck.flat.gz"
pt.sendCommand(f"read_flat_model {flat_model_path} -enable_full_introspection on")

# add faults to design, create patterns
pt.sendCommand("add_faults -all")
pt.sendCommand("create_patterns")

# report coverage stats, store in string (for parsing, etc...)
stats_str = pt.sendCommand("report_statistics")

# close tessent -shell process
pt.close()

```

## Notes

**Requires:**
- *pexpect* Python Library [https://pexpect.readthedocs.io/en/stable/](https://pexpect.readthedocs.io/en/stable/)

**Assumes:**
- `$PATH` variable contains command enabling direct `tessent -shell` call
- `SETUP> ` and `ANALYSIS> ` are the two prompts that are expected from Tessent shell subprocess, used by *pexpect* library to determine when command has completed.