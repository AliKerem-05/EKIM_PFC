import math
from typing import Dict, Optional, Tuple, Union

from KoolMu_toroid_core_library import KoolMuToroidCoreLibrary


_KOOL_MU_LIBRARY = KoolMuToroidCoreLibrary()
_MW_PER_CM3_TO_W_PER_M3 = 1000.0


def _normalize_perm(permeability: Union[str, int]) -> str:
    key = str(permeability).strip().lower()
    if not key.endswith("u"):
        key = f"{key}u"
    return key


def get_koolmu_material_coeffs(permeability: Union[str, int]) -> Dict[str, Optional[dict]]:
    return _KOOL_MU_LIBRARY.get_material_coefficients(_normalize_perm(permeability))


def permeability_dc_bias_ratio(permeability: Union[str, int], h_oe: float) -> float:
    coeffs = get_koolmu_material_coeffs(permeability)["dc_bias"]
    if not coeffs:
        return 1.0
    h_oe = max(h_oe, 0.0)
    percent_initial = 1.0 / (coeffs["a"] + coeffs["b"] * (h_oe ** coeffs["c"]))
    return max(percent_initial / 100.0, 0.05)


def permeability_temp_ratio(permeability: Union[str, int], temp_c: float) -> float:
    coeffs = get_koolmu_material_coeffs(permeability)["temperature"]
    if not coeffs:
        return 1.0
    delta = (
        coeffs["a"]
        + coeffs["b"] * temp_c
        + coeffs["c"] * (temp_c ** 2)
        + coeffs["d"] * (temp_c ** 3)
        + coeffs["e"] * (temp_c ** 4)
    )
    return max(1.0 + delta, 0.1)


def dc_flux_density_koolmu(permeability: Union[str, int], h_oe: float) -> float:
    coeffs = get_koolmu_material_coeffs(permeability)["dc_magnetization"]
    if not coeffs:
        return 0.0
    h_oe = max(h_oe, 0.0)
    numerator = coeffs["a"] + coeffs["b"] * h_oe + coeffs["c"] * (h_oe ** 2)
    denominator = 1.0 + coeffs["d"] * h_oe + coeffs["e"] * (h_oe ** 2)
    if denominator <= 0:
        return 0.0
    return max((numerator / denominator) ** coeffs["x"], 0.0)


def steinmetz_loss(
    f_hz: float,
    b_t: float,
    ve_m3: float,
    coeffs_or_mat: Union[str, dict, Tuple[float, float, float]],
    temp: Optional[Union[str, float]] = None,
):
    if f_hz <= 0 or b_t <= 0:
        return 0.0, 0.0

    if isinstance(coeffs_or_mat, (tuple, list)) and len(coeffs_or_mat) == 3:
        coeffs = {"a": coeffs_or_mat[0], "b": coeffs_or_mat[1], "c": coeffs_or_mat[2]}
    elif isinstance(coeffs_or_mat, dict):
        coeffs = coeffs_or_mat
    else:
        coeffs = get_koolmu_material_coeffs(str(coeffs_or_mat))["core_loss"]
        if not coeffs:
            raise ValueError(f"Steinmetz coefficients not available for material {coeffs_or_mat}")

    f_khz = f_hz / 1000.0
    pv_mw_per_cm3 = coeffs["a"] * (b_t ** coeffs["b"]) * (f_khz ** coeffs["c"])
    pv_w_per_m3 = pv_mw_per_cm3 * _MW_PER_CM3_TO_W_PER_M3
    return pv_w_per_m3, pv_w_per_m3 * ve_m3


def losses_copper_ac_dowell(wire: dict, f_hz: float, i_rms_a: float, geom: dict, t_c: float = 20.0):
    mu0 = 4.0 * math.pi * 1e-7
    rho20 = 1.724e-8
    alpha = 0.00393

    if wire.get("R20_ohm_per_m"):
        r20 = wire["R20_ohm_per_m"]
    elif wire.get("resistance_ohm_per_km"):
        r20 = wire["resistance_ohm_per_km"] / 1000.0
    elif wire.get("area_mm2"):
        r20 = rho20 / (wire["area_mm2"] * 1e-6)
    else:
        raise ValueError("Wire R20 data missing")

    rho_t = rho20 * (1.0 + alpha * (t_c - 20.0))
    rdc_per_m_t = r20 * (1.0 + alpha * (t_c - 20.0))
    delta = math.sqrt(rho_t / (math.pi * mu0 * f_hz))

    h_mm = geom["H_mm"]
    nl = max(1, int(math.ceil(geom["Nl"])))
    npl = max(1, int(math.ceil(geom["N_per_layer"])))
    d_bundle_m = geom["d_bundle_mm_eff"] * 1e-3
    d_strand_m = wire["d_strand_mm"] * 1e-3
    p_m = max((h_mm * 1e-3) / npl, d_bundle_m)

    a_term = (math.pi / 4.0) ** 0.75 * (d_strand_m / max(delta, 1e-12)) * math.sqrt(d_bundle_m / max(p_m, 1e-12))
    term1_den = math.cosh(2.0 * a_term) - math.cos(2.0 * a_term)
    term2_den = math.cosh(a_term) + math.cos(a_term)
    if abs(term1_den) < 1e-12 or abs(term2_den) < 1e-12:
        fr = 1.0
    else:
        term1 = (math.sinh(2.0 * a_term) + math.sin(2.0 * a_term)) / term1_den
        term2 = (math.sinh(a_term) - math.sin(a_term)) / term2_den
        fr = max(a_term * (term1 + (2.0 * (nl ** 2 - 1) / 3.0) * term2), 1.0)

    rdc_total_ohm = rdc_per_m_t * geom["lw_total_m"]
    rac_total_ohm = fr * rdc_total_ohm
    p_ac_w = (i_rms_a ** 2) * rac_total_ohm
    out = {
        "delta_m": delta,
        "Rdc_per_m_T": rdc_per_m_t,
        "Rdc_total_ohm": rdc_total_ohm,
        "skin_depth_mm": delta * 1e3,
    }
    return p_ac_w, rac_total_ohm, fr, out


def thermal_estimate_hurley(core: dict, p_tot_w: float, t_amb_c: float, ventilation: str = "natural", air_speed_m_s: Optional[float] = None, k: Optional[float] = None, rth_scale: float = 1.0):
    # Hurley-style lumped model:
    #   Rth ~= k / sqrt(Vc)
    # with Vc expressed in m^3.
    # Therefore k is not dimensionless; it implicitly carries units of
    # C * m^(3/2) / W so that Rth ends up in C/W.
    if core.get("ve_mm3") and core["ve_mm3"] > 0:
        vc_m3 = core["ve_mm3"] * 1e-9
    else:
        vc_m3 = max((core["ae_mm2"] * 1e-6) * (core["le_mm"] * 1e-3), 1e-12)

    if k is not None and k > 0:
        k_used = k
        k_source = "manual"
    else:
        vent = str(ventilation).strip().lower()
        base_map = {
            "natural": 0.06,
            "fan-small": 0.03,
            "fan": 0.03,
            "fan-strong": 0.02,
            "heatsink": 0.015,
        }
        k_used = base_map.get(vent, 0.06)
        k_source = "ventilation-map"
        if air_speed_m_s is not None:
            points = [(0.0, 0.06), (1.0, 0.03), (3.0, 0.02), (6.0, 0.015)]
            speed = max(0.0, air_speed_m_s)
            if speed <= points[0][0]:
                k_from_speed = points[0][1]
            elif speed >= points[-1][0]:
                x0, y0 = points[-2]
                x1, y1 = points[-1]
                k_from_speed = y0 + (speed - x0) * (y1 - y0) / (x1 - x0)
            else:
                k_from_speed = points[-1][1]
                for (x0, y0), (x1, y1) in zip(points, points[1:]):
                    if x0 <= speed <= x1:
                        k_from_speed = y0 + (speed - x0) * (y1 - y0) / (x1 - x0)
                        break
            k_used = min(k_used, k_from_speed)
            k_source = "airspeed-interp"

    k_used = min(max(k_used, 0.008), 0.10)
    rth_c_per_w = (k_used / math.sqrt(vc_m3)) * rth_scale
    t_core_c = t_amb_c + rth_c_per_w * max(p_tot_w, 0.0)
    details = {
        "Vc_m3": vc_m3,
        "k_used": k_used,
        "k_units": "C*m^(3/2)/W",
        "k_source": k_source,
        "RthScale": rth_scale,
        "Ventilation": ventilation,
        "AirSpeed_m_s": air_speed_m_s,
        "model_note": "Hurley-type empirical model with Vc in m^3",
    }
    return rth_c_per_w, t_core_c, details
