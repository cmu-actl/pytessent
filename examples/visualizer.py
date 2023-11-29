from pathlib import Path
from pytessent import PyTessentFactory, PyTessent


ptf = PyTessentFactory()
pt = ptf.launch(timeout=None, replace=True, logfile="tessent_visualizer.log")


flatmodel = Path(
    "/storage/industry_data/globalfoundries/12LP_STS/12LP_STS_Flatmodels/v1.0_12LPQTV_STS_lym0_stuck.flat.gz"
)
pattern = Path(
    "/storage/industry_data/globalfoundries/12LP_STS/12LP_STS_Patterns/v1.0_12LPQTV_STS_lym0_par_fulltest_stuck.wgl.gz"
)

pt.sendCommand("set_context pattern -scan")
pt.sendCommand(f"read_flat_model {flatmodel}")
pt.sendCommand(f"read_patterns {pattern}")


pins = [
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_1__i_sbox/U161/Z",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/C187/B",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U100/B",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U103/B",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U106/A",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U109/B",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U116/A",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U165/A",
    "lym_i0/lym_i0/lym_i/lym_glm_i/i_lym_glm_cluster_0_11/i_sbox_chain/inst_sbox_2__i_sbox/U178/A2",
]

for pin in pins:
    pt.sendCommand(f"add_schematic_objects {pin}")


pt.close()