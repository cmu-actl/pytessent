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
    with PyTessent(log_file=tessent_log, replace=replace) as pt:
        pt.send_command("set_context pattern -scan")
        pt.send_command(f"read_flat_model {flatmodel}")

        if faulttype:
            pt.send_command(f"set_fault_type {faulttype}")

        pt.send_command("add_faults -all")
        pt.send_command(f"create_patterns -coverage_effort {coverageeffort}")

        pt.send_command(
            f"write_patterns {outfile} -{outformat} {'-replace' if replace else ''} -pattern_sets scan"
        )

    if not outfile.exists():
        raise FileNotFoundError(f"Did not find pattern file generated at {outfile}")


def create_random_patterns(
    flatmodel: Path,
    output_file: Path,
    output_format: PatternFormat = "patdb",
    fault_type: FaultType | None = None,
    num_patterns: int = 100,
    log_file: str | Path | None = None,
    replace: bool = True,
) -> None:
    with PyTessent(log_file=log_file, replace=replace) as pt:
        pt.send_command("set_context pattern -scan")
        pt.send_command(f"read_flat_model {flatmodel}")

        if fault_type:
            pt.send_command(f"set_fault_type {fault_type}")
        pt.send_command("add_faults -all")
        if fault_type == "transition":
            pt.send_command("set_pattern_type -sequential 2")
            pt.send_command("set_random_clocks clock")
        pt.send_command(f"set_random_patterns {num_patterns}")

        pt.send_command("simulate_patterns -source random -store_patterns all")

        pt.send_command(
            f"write_patterns {output_file} -{output_format} {'-replace' if replace else ''} -pattern_sets scan"
        )

    if not output_file.exists():
        raise FileNotFoundError(f"Did not find pattern file generated at {output_file}")
