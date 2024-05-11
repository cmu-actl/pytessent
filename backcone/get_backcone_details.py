from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import typer
import yaml
from pytessent import PyTessent
from pytessent.circuit import Circuit, Pin, Pattern
from tqdm import tqdm


@dataclass
class BackconeConfig:
    name: str
    flatmodel: Path
    patdb: Path
    binpat: Path | None = None
    failbits: list[FailBit] = field(default_factory=list)
    defectsites: list[str] = field(default_factory=list)


@dataclass
class FailBit:
    chain: str
    cell: int
    failpatterns: list[int] = field(default_factory=list)


def read_backcone_yaml(bc_yaml: Path) -> BackconeConfig:
    with open(bc_yaml, "rt") as f:
        bc_fields = yaml.safe_load(f)

    failbits = [
        FailBit(
            chain=failbit["chain"],
            cell=failbit["cell"],
            failpatterns=failbit["failpatterns"],
        )
        for failbit in bc_fields["failbits"]
    ]
    bccfg = BackconeConfig(
        name=bc_fields["name"],
        flatmodel=Path(bc_fields["flatmodel"]),
        patdb=Path(bc_fields["patdb"]),
        binpat=Path(bc_fields["binpat"]),
        failbits=failbits,
        defectsites=bc_fields["defectsites"],
    )

    return bccfg


def setup_pytessent(
    flat_model: Path, pat_file: Path, log_file: str | Path | None = None
) -> PyTessent:
    pt = PyTessent(log_file=log_file, replace=True)
    pt.send_command("set_context pattern -scan")
    pt.send_command(f"read_flat_model {flat_model}")
    pt.send_command(f"read_patterns {pat_file}")

    return pt


def get_scancell_pin(chain: str, cell: int, c: Circuit) -> Pin:
    """From a scan chain name and cell index, get the corresponding scan cell pin (using
    Tessent report_scan_cells)

    Arguments:
        chain: name of scan chain.
        cell: index of scan cell in scan chain.
        pt: PyTessent instance.

    Returns:
        name of scan cell pin.
    """

    # query tessent for scan cell report
    scr_str = c.pt.send_command(f"report_scan_cell {chain} -range {cell} {cell}")

    # pull out line with instance
    scr_line = scr_str.split("\n")[-1]

    # put together fields to get primitive
    inst, prim = scr_line.split()[9:11]

    # depending on primitive, use string replacement to get pin
    if prim == '""':
        sc_pin = f"{inst}/d"
    else:
        pin_name = prim.replace("bit", "d").replace(
            "_inst", ""
        )  # change "/bit" to "/d", remove "_inst" at the end
        sc_pin = f"{inst}/{pin_name}"

    # remove potential leading slash
    if sc_pin.startswith("/"):
        sc_pin = sc_pin[1:]

    return c.get_pin(sc_pin)


def get_backcone_flop_pins(pin: Pin, c: Circuit) -> list[Pin]:
    # use tessent to find flops on backcone
    res_str = c.pt.send_command(
        "get_attribute_value_list "
        f"[trace_flat_model -from {pin.name} -direction backward -map_tag_to_design_module_boundary on] "
        "-name name"
    )
    back_pins = res_str.split()

    return [c.get_pin(p) for p in back_pins]


def get_backcone_pins(pin: Pin, endpoints: list[Pin]) -> set[Pin]:
    """Given a start pin and points to stop the trace, get all the pins on the backcone.

    Parameters
    ----------
    pin : Pin
        Starting point Pins for trace.
    endpoints : list[Pin]
        Ending point Pins for trace.

    Returns
    -------
    set[Pin]
        Complete set of pins found on backcone.
    """
    pin_queue = {pin}
    bc_pins = set()
    while pin_queue:
        # get next pin from set
        cur_pin = pin_queue.pop()

        # skip any previously-seen pins
        if cur_pin in bc_pins:
            continue

        bc_pins.add(cur_pin)

        # if endpoint pin is reached, add but don't keep tracing
        if cur_pin in endpoints:
            continue

        # add fanin of current pin to queue
        pin_queue.update(cur_pin.fanin)

    return bc_pins


def main(
    backconeyaml: Path = typer.Argument(
        ..., help="Input YAML file for backcone processing"
    ),
    tessent_log: Path = typer.Option(None, help="Tessent log file"),
    analyze_patterns: bool = typer.Option(
        True, help="Run analysis on failing patterns?"
    ),
    write_verilog: bool = typer.Option(False, help="Write Verliog file of subcircuit?"),
    write_pickle: bool = typer.Option(False, help="Write Pickle file of subcircuit?"),
    from_pickle: Path = typer.Option(
        None, help="Read Backcone from pre-existing Pickle file?"
    ),
    plot_graph: bool = typer.Option(False, help="Plot graph of subcircuit?"),
) -> Circuit:
    bccfg = read_backcone_yaml(backconeyaml)

    outdir = Path(f"backcone_{bccfg.name}")
    outdir.mkdir(exist_ok=True)

    if not tessent_log:
        tessent_log = outdir / "tessent.log"

    # set up pytessent
    pt = setup_pytessent(
        flat_model=bccfg.flatmodel,
        pat_file=bccfg.binpat
        if (bccfg.binpat and bccfg.binpat.exists())
        else bccfg.patdb,
        log_file=tessent_log,
    )

    if from_pickle:
        c, failpatterns = Circuit.from_pickle(from_pickle, pt)
    else:
        c = Circuit.empty(bccfg.name, pt)

        failpatterns = []
        for failbit in bccfg.failbits:
            # get scancell pin, define as output to circuit
            sc_pin = get_scancell_pin(failbit.chain, failbit.cell, c)
            c.define_output(sc_pin)

            # get pins of flops on backcone, define as inputs to circuit
            bc_flop_pins = get_backcone_flop_pins(sc_pin, c)
            [c.define_input(p) for p in bc_flop_pins]

            # get all backcone flops from output pin to input pins, add to circuit
            bc_pins = get_backcone_pins(sc_pin, bc_flop_pins)
            [c.add_pin(pin) for pin in bc_pins]

            # define defect sites
            [c.define_defectsite(p) for p in c.pins if p.name in bccfg.defectsites]

            failpatterns = [Pattern(p) for p in failbit.failpatterns]
            if analyze_patterns:
                # cycle through patterns, extract values of each pin in backcone
                failpaths_per_pattern = {}
                for failpat in tqdm(failpatterns, desc="Fail Patterns"):
                    failpaths = []
                    failpat.get_circuit_values(c)
                    failpat.create_pattern_sim_context(c)
                    for ipin in tqdm(c.inputs, desc="Input X Simulation"):
                        if (
                            failpat.pinvalues[ipin][0] != failpat.pinvalues[ipin][1]
                        ):  # transitions
                            x_pins, fail_outputs = failpat.simulate_x_at_pin(c, ipin)
                            if fail_outputs:  # fails for some output
                                [
                                    failpat.add_activated_pinpath(pinpath)
                                    for pinpath in c.get_pinpaths(
                                        from_pin=ipin, to_pin=sc_pin
                                    )
                                    if pinpath.is_activated(x_pins)
                                ]
                    failpaths_per_pattern[failpat] = failpat.activatedpinpaths

                with open(outdir / "failpaths.txt", "w") as f:
                    for pat, failpaths in failpaths_per_pattern.items():
                        f.write(f"Pattern {pat.index}\n")
                        for i, failpath in enumerate(failpaths):
                            f.write(f"  Path {failpath.index} ({i+1}):\n")
                            for pin in failpath.pins:
                                f.write(
                                    f"    {pin.name} {pin.gate.celltype.name} "
                                    f"({''.join(pat.pinvalues[pin])}) "
                                    f"{'*' if pin in c.defectsites else ''}\n"
                                )
                            f.write("\n")
                        f.write("\n")

    if write_pickle:
        c.to_pickle(outdir / "backcone.pickle", failpatterns)

    if write_verilog:
        c.to_verilog(outdir / "backcone.v")

    if plot_graph:
        c.plot_graph(outdir / "backcone.png")

    return c


if __name__ == "__main__":
    typer.run(main)
