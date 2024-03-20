# PyTessent
PyTessent is a small library enabling creation of interactive `tessent -shell` subprocesses that can be controlled from python.

It uses the python [pexpect](https://pexpect.readthedocs.io/en/stable/) library to facilitate communication with the Tessent process.


## Installation

```shell
git clone https://github.com/cmu-actl/pytessent.git
cd pytessent
pip install -e .
```


## Example Usage
```python
from pytessent import PyTessent

# create "tessent -shell" process and write log file to tessent.log
pt = PyTessent(log_file="tessent.log")

# send tessent command to set context
pt.send_command("set_context patterns -scan")

# Read Tessent flat model
flat_model_path = "/storage/industry_data/globalfoundries/12LP_STS/12LP_STS_Flatmodels/v1.0_12LPQTV_STS_lym0_stuck.flat.gz"
pt.send_command(f"read_flat_model {flat_model_path}")

# add faults to design, create patterns
pt.send_command("add_faults -all")
pt.send_command("create_patterns")

# report coverage stats, store in string (for parsing, etc...)
stats_str = pt.send_command("report_statistics")

# close tessent -shell process
pt.close()
```


## Compatability

PyTessent should be compatiably with a wide array of Tessent versions. The only assumptions it makes are that `tessent -shell` accepts `-dofile`, `-logfile`, `-replace`, and `-arguments` as arguments, and that the shell itself uses the following two prompts: `SETUP> ` and `ANALYSIS> `.
