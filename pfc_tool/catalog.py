from typing import Dict, List

from KoolMu_toroid_core_library import KoolMuToroidCoreLibrary
from wire_lib_solid_awg import SolarisWireLibrary


_CORE_LIBRARY = KoolMuToroidCoreLibrary()
_WIRE_LIBRARY = SolarisWireLibrary()


def _wire_to_dict(wire) -> Dict[str, float]:
    return {
        "id": wire.awg,
        "name": f"AWG {wire.awg}",
        "awg": wire.awg,
        "diameter_mm": wire.diameter_mm,
        "area_mm2": wire.area_mm2,
        "resistance_ohm_per_km": wire.resistance_ohm_per_km,
        "R20_ohm_per_m": wire.resistance_ohm_per_km / 1000.0,
        "d_strand_mm": wire.diameter_mm,
        "max_current_amps": wire.max_current_amps,
        "max_freq_hz": wire.max_freq_hz,
    }


def _core_to_dict(core, permeability: str, al_nh_t2: float) -> Dict[str, float]:
    coeffs = _CORE_LIBRARY.get_material_coefficients(permeability)
    return {
        "id": f"{core.part_number}:{permeability}",
        "part_number": core.part_number,
        "family": core.family,
        "permeability": permeability,
        "al_nh_t2": al_nh_t2,
        "le_mm": core.le_mm,
        "ae_mm2": core.ae_mm2,
        "ve_mm3": core.ve_mm3,
        "od_mm": core.od_mm,
        "id_mm": core.id_mm,
        "height_mm": core.height_mm,
        "coefficients_available": all(coeffs.values()),
    }


def build_catalog() -> Dict[str, List[Dict[str, float]]]:
    supported_perms = _CORE_LIBRARY.list_supported_permeabilities()
    cores = []
    for part_number in _CORE_LIBRARY.list_part_numbers():
        core = _CORE_LIBRARY.get_core(part_number)
        for permeability in supported_perms:
            al_nh_t2 = _CORE_LIBRARY.get_al_value(part_number, permeability)
            if al_nh_t2 is None:
                continue
            cores.append(_core_to_dict(core, permeability, al_nh_t2))

    wires = [_wire_to_dict(_WIRE_LIBRARY.get_wire(key)) for key in _WIRE_LIBRARY._data.keys()]
    wires.sort(key=lambda item: item["area_mm2"])
    cores.sort(key=lambda item: (item["ve_mm3"], item["part_number"], item["permeability"]))

    return {
        "families": ["Kool Mu Toroid"],
        "cores": cores,
        "wires": wires,
        "defaults": {
            "core_id": "206:60u",
            "wire_id": "14",
            "ambient_c": 40.0,
            "rise_limit_c": 60.0,
            "f_sw_khz": 65.0,
        },
    }
