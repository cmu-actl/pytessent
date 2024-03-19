from pytessent import PyTessent
from pytessent.circuit import Circuit, Pattern
from get_backcone_details import read_backcone_yaml, setup_pytessent
from pathlib import Path


def backcone_interactive(
    backcone_yaml: Path,
    backcone_pickle: Path,
    tessent_log: Path | None = Path("tessent.log"),
) -> tuple[Circuit, list[Pattern]]:
    bccfg = read_backcone_yaml(backcone_yaml)

    pt = setup_pytessent(
        flatmodel=bccfg.flatmodel,
        pat_file=bccfg.binpat
        if (bccfg.binpat and bccfg.binpat.exists())
        else bccfg.patdb,
        logfile=tessent_log,
    )

    c, failpatterns = Circuit.from_pickle(backcone_pickle, pt)

    return c, failpatterns