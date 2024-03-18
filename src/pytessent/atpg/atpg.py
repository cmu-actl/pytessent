from pytessent import PyTessent
from pathlib import Path
from typing import Literal

PatternFormat = Literal["stil", "ascii", "bin", "patdb"]
FaultType = Literal["stuck", "transition"]
CoverageEffort = Literal["low", "medium", "high"]


def create_atpg_patterns(
    flatmodel: Path,
    outfile: Path,
    outformat: PatternFormat = "patdb",
    tessent_log: Path | None = None,
    faulttype: FaultType | None = None,
    coverageeffort: CoverageEffort = "high",
    replace: bool = True,
    ) -> None:

    pt = PyTessent.launch(logfile=tessent_log, replace=replace)
    pt.sendCommand("set_context pattern -scan")
    pt.sendCommand(f"read_flat_model {flatmodel}")

    if faulttype:
        pt.sendCommand(f"set_fault_type {faulttype}")

    pt.sendCommand("add_faults -all")
    pt.sendCommand(f"create_patterns -coverage_effort {coverageeffort}")

    pt.sendCommand(
        f"write_patterns {outfile} -{outformat} {'-replace' if replace else ''} -pattern_sets scan"
    )

    pt.close()

    if not outfile.exists():
        raise FileNotFoundError(f"Did not find pattern file generated at {outfile}")

def create_random_patterns(
    flatmodel: Path,
    outfile: Path,
    outformat: PatternFormat = "patdb",
    tessent_log: Path | None = None,
    faulttype: FaultType | None = None,
    num_patterns: int = 100,
    replace: bool = True,
) -> None:

    pt = PyTessent.launch(logfile=tessent_log, replace=replace)
    pt.sendCommand("set_context pattern -scan")
    pt.sendCommand(f"read_flat_model {flatmodel}")

    if faulttype:
        pt.sendCommand(f"set_fault_type {faulttype}")
    pt.sendCommand("add_faults -all")
    if faulttype == "transition":
        pt.sendCommand("set_pattern_type -sequential 2")
        pt.sendCommand("set_random_clocks clock")
    pt.sendCommand(f"set_random_patterns {num_patterns}")

    pt.sendCommand("simulate_patterns -source random -store_patterns all")

    pt.sendCommand(
        f"write_patterns {outfile} -{outformat} {'-replace' if replace else ''} -pattern_sets scan"
    )

    pt.close()

    if not outfile.exists():
        raise FileNotFoundError(f"Did not find pattern file generated at {outfile}")
