# Backcone Analysis

- *get_backcone_details.py*: Reads a Backcone YAML file, loads design/pattern details, and performs backcone analysis of failing flops.
```sh
Usage: get_backcone_details.py [OPTIONS] BACKCONEYAML

Arguments:
  BACKCONEYAML  Input YAML file for backcone processing  [required]

Options:
  --tessent-log PATH              Tessent log file
  --analyze-patterns / --no-analyze-patterns
                                  Run analysis on failing patterns?  [default:
                                  analyze-patterns]
  --write-verilog / --no-write-verilog
                                  Write Verliog file of subcircuit?  [default:
                                  no-write-verilog]
  --write-pickle / --no-write-pickle
                                  Write Pickle file of subcircuit?  [default:
                                  no-write-pickle]
  --from-pickle PATH              Read Backcone from pre-existing Pickle file?
  --plot-graph / --no-plot-graph  Plot graph of subcircuit?  [default: no-
                                  plot-graph]
  --help                          Show this message and exit.
```