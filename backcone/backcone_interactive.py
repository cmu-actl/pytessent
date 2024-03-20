from pytessent.circuit import Circuit
from get_backcone_details import read_backcone_yaml, setup_pytessent
from pathlib import Path

backconeyaml = Path("backcone_yaml/m3.yaml")
tessent_log = Path("tessent_int_m3.log")
bccfg = read_backcone_yaml(backconeyaml)

pt = setup_pytessent(
    flat_model=bccfg.flatmodel,
    pat_file=bccfg.binpat if (bccfg.binpat and bccfg.binpat.exists()) else bccfg.patdb,
    log_file=tessent_log,
)

c, failpatterns = Circuit.from_pickle(Path("backcone_m3/backcone.pickle"), pt)
