from pathlib import Path

from pytessent import PyTessent
from pytessent.circuit import PinPath


def create_pdf_tests(
    pinpaths: list[PinPath],
    pt: PyTessent,
    robust: bool = True,
    hazardfree: bool = False,
    pdf_file: Path | None = None,
    pattern_file: Path | None = None,
) -> None:
    """Generate path delay fault tests for a defined set of paths.

    Parameters
    ----------
    pinpaths : list[PinPath]
        List of PinPath objects defining paths for PDFs.
    pt : PyTessent
        PyTessent instance to use for generating patterns (must include pinpaths).
    robust : bool, optional
        Require robust PDF detection?, by default True
    hazardfree : bool, optional
        Require hazard-free robust detection?, by default False
    pdf_file : Path, optional
        Name for fault definition file, by default "pdf_temp.faults"
    pattern_file : Path, optional
        Path to write out pattern file to, by default don't write pattern file.
    """
    pt.send_command("set_pattern_type -sequential 2")
    pt.send_command("set_fault_type path_delay")

    if not pdf_file:
        pdf_file = Path("pdf_temp.faults")

    with open(pdf_file, "w") as f:
        for pinpath in pinpaths:
            f.write(pinpath.get_pdf_string())
            f.write("\n\n")

    pt.send_command(f"read_fault_sites {pdf_file}")

    faulttype_cmd = "set_fault_type path_delay -mask_nonobservation_points"
    faulttype_cmd += " -robust_detection_only" if robust and not hazardfree else ""
    faulttype_cmd += (
        " -robust_detection_only -hazard_free_robust_detections" if hazardfree else ""
    )
    pt.send_command(faulttype_cmd)

    pt.send_command("add_faults -all")
    pt.send_command("create_patterns")

    if pattern_file:
        ext = pattern_file.suffix
        pt.send_command(
            f"write_patterns {pattern_file} -{ext} -pattern_sets scan -replace"
        )


def subcircuit_pytessent_from_verilog(verilog: Path, tessent_log: Path) -> PyTessent:
    """From a subcircuit verilog file, produce a corresponding PyTessent instance.

    Parameters
    ----------
    verilog : Path
        Subcircuit Verilog file.
    ptf : PyTessentFactory
        PyTessentFactory for creating new subcircuit PyTessent instance.
    tessent_log : Path
        Log file for PyTessent instance

    Returns
    -------
    PyTessent
        PyTessent instance with subcircuit loaded.
    """
    pt = PyTessent(log_file=tessent_log, replace=True)
    pt.send_command("set_context pattern -scan")
    celllib_dir = Path("/project/voxel_test/tessent_libs/standard_cells/")

    for celllib_file in celllib_dir.glob("*lib"):
        pt.send_command(f"read_cell_library {celllib_file}")

    pt.send_command(f"read_verilog {verilog}")
    pt.send_command("set_design_level top")
    pt.send_command("set_system_mode analysis")

    return pt
