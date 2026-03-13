from pathlib import Path
from typing import Dict

from Ferrit_toroid_core_library import ToroidProperties
from toroid_visualizer import plot_toroid, plot_toroid_3d_interactive

from .designer import get_catalog


_CATALOG = get_catalog()
_CORE_MAP = {item["id"]: item for item in _CATALOG["cores"]}


def _to_toroid_props(core: Dict) -> ToroidProperties:
    return ToroidProperties(
        part_number=f"{core['part_number']}-{core['permeability']}",
        le_mm=core["le_mm"],
        ae_mm2=core["ae_mm2"],
        ve_mm3=core["ve_mm3"],
        waac_cm4=None,
        od_mm=core["od_mm"],
        id_mm=core["id_mm"],
        height_mm=core["height_mm"],
        al_l_750u_nh_t2=None,
        al_r_2300u_nh_t2=None,
        al_p_2500u_nh_t2=None,
        al_f_3000u_nh_t2=None,
        al_t_3000u_nh_t2=None,
        al_j_5000u_nh_t2=None,
        al_w_10000u_nh_t2=None,
        al_m_15000u_nh_t2=None,
        al_c_900u_nh_t2=None,
    )


def build_candidate_visuals(core_id: str, wire_id: str, turns: int) -> Dict[str, str]:
    core = _CORE_MAP.get(core_id)
    if not core:
        raise ValueError("Core not found for visualization")
    toroid = _to_toroid_props(core)
    out_2d = plot_toroid(toroid, turns=turns, awg=wire_id, show=False)
    out_3d = plot_toroid_3d_interactive(toroid, turns=turns, awg=wire_id)
    return {
        "image_2d": "/artifacts/" + Path(out_2d).name,
        "image_2d_path": str(Path(out_2d).resolve()),
        "html_3d": "/artifacts/" + Path(out_3d).name,
        "html_3d_path": str(Path(out_3d).resolve()),
    }
