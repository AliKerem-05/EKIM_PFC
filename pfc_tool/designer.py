import math
from typing import Dict, List, Optional

from .catalog import build_catalog
from .materials import (
    dc_flux_density_koolmu,
    losses_copper_ac_dowell,
    permeability_dc_bias_ratio,
    permeability_temp_ratio,
    steinmetz_loss,
    thermal_estimate_hurley,
)


_CATALOG = build_catalog()
_CORE_MAP = {item["id"]: item for item in _CATALOG["cores"]}
_WIRE_MAP = {item["id"]: item for item in _CATALOG["wires"]}


def _to_float(payload: Dict, key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if value in (None, ""):
        return default
    return float(value)


def _to_int(payload: Dict, key: str, default: int = 0) -> int:
    value = payload.get(key, default)
    if value in (None, ""):
        return default
    return int(value)


def _value_set(value: Optional[object]) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    if isinstance(value, str):
        return {item.strip().lower() for item in value.split(",") if item.strip()}
    return {str(value).strip().lower()} if str(value).strip() else set()


def _derive_operating_point(payload: Dict) -> Dict[str, float]:
    mode = payload.get("design_mode", "pfc")
    f_sw_hz = _to_float(payload, "f_sw_khz", 65.0) * 1000.0

    if mode == "direct":
        target_inductance_uH = _to_float(payload, "target_inductance_uH")
        return {
            "mode": "direct",
            "target_inductance_uH": target_inductance_uH,
            "i_avg_a": _to_float(payload, "i_avg_a"),
            "delta_i_pp_a": _to_float(payload, "delta_i_pp_a"),
            "i_pk_a": _to_float(payload, "i_avg_a") + _to_float(payload, "delta_i_pp_a") / 2.0,
            "i_min_a": _to_float(payload, "i_avg_a") - _to_float(payload, "delta_i_pp_a") / 2.0,
            "i_rms_a": math.sqrt(_to_float(payload, "i_avg_a") ** 2 + (_to_float(payload, "delta_i_pp_a") ** 2) / 12.0),
            "f_sw_hz": f_sw_hz,
            "notes": [
                "Manual target inductance was used directly.",
                f"Target inductance = {target_inductance_uH:.1f} uH.",
                "Current inputs are entered as Iavg and ripple peak-to-peak current; Ipk and Irms are derived.",
            ],
        }

    vin_rms_min = _to_float(payload, "vin_rms_min_v")
    vout_v = _to_float(payload, "vout_v")
    pout_w = _to_float(payload, "pout_w")
    eta = _to_float(payload, "eta_est", 0.95)
    ripple_pct = _to_float(payload, "ripple_pct", 25.0)

    pin_w = pout_w / max(eta, 1e-6)
    vin_pk = math.sqrt(2.0) * vin_rms_min
    duty = 1.0 - vin_pk / max(vout_v, 1e-6)
    i_line_rms = pin_w / max(vin_rms_min, 1e-6)
    i_line_pk = math.sqrt(2.0) * i_line_rms
    delta_i_pp = (ripple_pct / 100.0) * i_line_pk
    target_inductance_h = vin_pk * max(duty, 0.01) / max(f_sw_hz * max(delta_i_pp, 1e-6), 1e-9)

    return {
        "mode": "pfc",
        "target_inductance_uH": target_inductance_h * 1e6,
        "i_avg_a": i_line_pk,
        "i_rms_a": math.sqrt(i_line_pk ** 2 + (delta_i_pp ** 2) / 12.0),
        "i_pk_a": i_line_pk + delta_i_pp / 2.0,
        "i_min_a": i_line_pk - delta_i_pp / 2.0,
        "delta_i_pp_a": delta_i_pp,
        "f_sw_hz": f_sw_hz,
        "duty_at_low_line": duty,
        "vin_pk_v": vin_pk,
        "notes": [
            "Target inductance was derived from low-line CCM ripple.",
            f"Low-line average current = {i_line_pk:.2f} A.",
            f"Derived peak current = {i_line_pk + delta_i_pp / 2.0:.2f} A and ripple pp = {delta_i_pp:.2f} A.",
        ],
    }


def _magnetic_field_oe(turns: int, current_a: float, le_mm: float) -> float:
    h_a_per_m = turns * current_a / max(le_mm * 1e-3, 1e-9)
    return h_a_per_m / 79.5774715459


def _build_parallel_wire(wire: Dict[str, float], i_rms_a: float, payload: Dict) -> Dict[str, float]:
    fixed_parallel = _to_int(payload, "fixed_parallel_count", 0)
    if fixed_parallel > 0:
        parallel_count = fixed_parallel
    else:
        target_j = max(_to_float(payload, "target_j_a_per_mm2", 4.0), 0.5)
        required_area = i_rms_a / target_j
        parallel_count = max(1, math.ceil(required_area / max(wire["area_mm2"], 1e-9)))
    effective_area = wire["area_mm2"] * parallel_count
    effective_diameter = wire["diameter_mm"] * math.sqrt(parallel_count) * 1.12
    return {
        "parallel_count": parallel_count,
        "effective_area_mm2": effective_area,
        "effective_diameter_mm": effective_diameter,
        "R20_ohm_per_m": wire["R20_ohm_per_m"] / parallel_count,
        "d_strand_mm": wire["d_strand_mm"],
        "base_awg": wire["awg"],
        "name": f"{parallel_count}x AWG {wire['awg']}",
    }


def _winding_geometry(core: Dict[str, float], bundle: Dict[str, float], turns: int, max_layers: int) -> Dict[str, float]:
    d_eff_mm = bundle["effective_diameter_mm"] * 1.05
    turns_per_layer = max(1, int((math.pi * core["id_mm"]) // max(d_eff_mm, 1e-9)))
    layers = max(1, math.ceil(turns / turns_per_layer))
    total_capacity = turns_per_layer * max_layers
    occupancy = turns / max(total_capacity, 1)
    inner_window_area_mm2 = max(core["id_mm"] * core["height_mm"], 1e-9)
    ku_inner = (turns * bundle["effective_area_mm2"]) / inner_window_area_mm2
    mean_turn_length_mm = math.pi * ((core["od_mm"] + core["id_mm"]) / 2.0 + (layers - 1) * d_eff_mm)
    length_m = mean_turn_length_mm * turns / 1000.0
    return {
        "turns_per_layer": turns_per_layer,
        "layers": layers,
        "max_layers": max_layers,
        "occupancy": occupancy,
        "ku_inner": ku_inner,
        "inner_window_area_mm2": inner_window_area_mm2,
        "length_m": length_m,
        "d_bundle_mm_eff": d_eff_mm,
        "fits": layers <= max_layers and turns <= total_capacity and ku_inner <= 1.0,
        "total_capacity": total_capacity,
    }


def _evaluate_turn(core: Dict[str, float], wire: Dict[str, float], operating: Dict[str, float], payload: Dict, turns: int) -> Dict:
    target_l_uh = operating["target_inductance_uH"]
    delta_i_pp_a = max(operating["delta_i_pp_a"], 0.0)
    f_sw_hz = operating["f_sw_hz"]
    i_pk_a = operating["i_pk_a"]
    i_rms_a = operating["i_rms_a"]
    ae_m2 = core["ae_mm2"] * 1e-6
    ve_m3 = core["ve_mm3"] * 1e-9
    al_25 = core["al_nh_t2"]
    max_layers = max(1, min(2, _to_int(payload, "max_layers", 2)))

    bundle = _build_parallel_wire(wire, i_rms_a, payload)
    geom = _winding_geometry(core, bundle, turns, max_layers)
    if not geom["fits"]:
        reason = "ku_inner_limit" if geom["ku_inner"] > 1.0 else "inner_diameter_capacity"
        return {"feasible": False, "reason": reason, "turns": turns, "layers": geom["layers"], "parallel_count": bundle["parallel_count"]}

    temp_guess_c = _to_float(payload, "ambient_c", 40.0) + min(_to_float(payload, "rise_limit_c", 60.0) * 0.5, 40.0)
    result = None
    for _ in range(4):
        h_oe = _magnetic_field_oe(turns, i_pk_a, core["le_mm"])
        mu_bias = permeability_dc_bias_ratio(core["permeability"], h_oe)
        mu_temp = permeability_temp_ratio(core["permeability"], temp_guess_c)
        al_eff = al_25 * mu_bias * mu_temp
        l_uh = al_eff * (turns ** 2) / 1000.0
        b_dc_t = dc_flux_density_koolmu(core["permeability"], h_oe)
        b_ac_pk_t = (l_uh * 1e-6) * delta_i_pp_a / max(2.0 * turns * ae_m2, 1e-12)
        pv_wpm3, p_core_w = steinmetz_loss(f_sw_hz, max(b_ac_pk_t, 1e-6), ve_m3, core["permeability"])

        loss_wire = {
            "R20_ohm_per_m": bundle["R20_ohm_per_m"],
            "d_strand_mm": wire["d_strand_mm"],
            "area_mm2": bundle["effective_area_mm2"],
        }
        geom_loss = {
            "Nl": geom["layers"],
            "N_per_layer": geom["turns_per_layer"],
            "H_mm": max(core["height_mm"], geom["d_bundle_mm_eff"]),
            "lw_total_m": geom["length_m"],
            "d_bundle_mm_eff": geom["d_bundle_mm_eff"],
        }
        p_cu_w, rac_ohm, fr, copper_details = losses_copper_ac_dowell(loss_wire, f_sw_hz, i_rms_a, geom_loss, temp_guess_c)
        rth_c_per_w, t_core_c, thermal_details = thermal_estimate_hurley(
            core,
            p_cu_w + p_core_w,
            _to_float(payload, "ambient_c", 40.0),
            ventilation=payload.get("ventilation", "natural"),
            air_speed_m_s=(_to_float(payload, "air_speed_m_s", float('nan')) if str(payload.get("air_speed_m_s", "")).strip() else None),
            k=(_to_float(payload, "thermal_k", float('nan')) if str(payload.get("thermal_k", "")).strip() else None),
            rth_scale=_to_float(payload, "rth_scale", 1.0),
        )
        temp_guess_c = t_core_c
        result = {
            "turns": turns,
            "l_uH": l_uh,
            "l_error_pct": 100.0 * (l_uh - target_l_uh) / max(target_l_uh, 1e-9),
            "al_eff_nh_t2": al_eff,
            "mu_bias_ratio": mu_bias,
            "mu_temp_ratio": mu_temp,
            "h_oe": h_oe,
            "b_dc_t": b_dc_t,
            "b_ac_pk_t": b_ac_pk_t,
            "b_total_pk_t": b_dc_t + b_ac_pk_t,
            "p_core_w": p_core_w,
            "pv_wpm3": pv_wpm3,
            "p_cu_w": p_cu_w,
            "p_tot_w": p_cu_w + p_core_w,
            "rac_total_ohm": rac_ohm,
            "fr": fr,
            "t_core_c": t_core_c,
            "rth_c_per_w": rth_c_per_w,
            "occupancy": geom["occupancy"],
            "ku_inner": geom["ku_inner"],
            "inner_window_area_mm2": geom["inner_window_area_mm2"],
            "length_m": geom["length_m"],
            "layers": geom["layers"],
            "turns_per_layer": geom["turns_per_layer"],
            "total_capacity": geom["total_capacity"],
            "wire_current_density_a_per_mm2": i_rms_a / max(bundle["effective_area_mm2"], 1e-9),
            "parallel_count": bundle["parallel_count"],
            "effective_area_mm2": bundle["effective_area_mm2"],
            "effective_diameter_mm": bundle["effective_diameter_mm"],
            "bundle_name": bundle["name"],
            "feasible": True,
            "loss_details": copper_details,
            "thermal_details": thermal_details,
        }

    temp_limit_c = _to_float(payload, "ambient_c", 40.0) + _to_float(payload, "rise_limit_c", 60.0)
    result["feasible"] = (
        abs(result["l_error_pct"]) <= _to_float(payload, "l_tolerance_pct", 10.0)
        and result["t_core_c"] <= temp_limit_c
        and result["b_total_pk_t"] <= _to_float(payload, "b_limit_t", 1.0)
    )
    if not result["feasible"]:
        if abs(result["l_error_pct"]) > _to_float(payload, "l_tolerance_pct", 10.0):
            result["reason"] = "inductance_out_of_band"
        elif result["t_core_c"] > temp_limit_c:
            result["reason"] = "thermal_limit"
        else:
            result["reason"] = "flux_limit"
    return result


def _passes_filters(core: Dict, wire: Dict, payload: Dict) -> bool:
    if core["part_number"].lower() in _value_set(payload.get("exclude_core_ids")):
        return False
    if core["permeability"].lower() in _value_set(payload.get("exclude_permeabilities")):
        return False
    if wire["awg"].lower() in _value_set(payload.get("exclude_wire_awgs")):
        return False

    min_ve = _to_float(payload, "min_ve_mm3", 0.0)
    max_ve = _to_float(payload, "max_ve_mm3", 0.0)
    if min_ve > 0 and core["ve_mm3"] < min_ve:
        return False
    if max_ve > 0 and core["ve_mm3"] > max_ve:
        return False
    return True


def _turn_range(core: Dict, operating: Dict, payload: Dict) -> range:
    fixed_turns = _to_int(payload, "fixed_turns", 0)
    if fixed_turns > 0:
        return range(fixed_turns, fixed_turns + 1)
    est_turns = math.sqrt(max(operating["target_inductance_uH"] * 1000.0 / max(core["al_nh_t2"], 1e-9), 1.0))
    n_min = max(1, int(math.floor(est_turns * 0.45)))
    n_max = max(n_min + 6, int(math.ceil(est_turns * 1.8)) + 8)
    return range(n_min, n_max + 1)


def _select_cores(payload: Dict) -> List[Dict]:
    return list(_CORE_MAP.values())[: _to_int(payload, "max_search_cores", len(_CORE_MAP))]


def _select_wires(payload: Dict) -> List[Dict]:
    return list(_WIRE_MAP.values())


def _apply_minmax_score(results: List[Dict], payload: Dict) -> None:
    if not results:
        return
    v_values = [item["core"]["ve_mm3"] for item in results]
    p_values = [item["p_tot_w"] for item in results]
    v_min, v_max = min(v_values), max(v_values)
    p_min, p_max = min(p_values), max(p_values)
    w_vol = _to_float(payload, "best_w_vol", 0.6)
    w_loss = _to_float(payload, "best_w_loss", 0.4)
    for item in results:
        nv = 0.0 if v_max <= v_min else (item["core"]["ve_mm3"] - v_min) / (v_max - v_min)
        np = 0.0 if p_max <= p_min else (item["p_tot_w"] - p_min) / (p_max - p_min)
        item["rank_score"] = w_vol * nv + w_loss * np


def _build_warnings(best: Optional[Dict], operating: Dict, payload: Dict, result_count: int) -> List[str]:
    if not best:
        return ["No valid candidate was found in the brute-force scan."]
    warnings = []
    if best.get("wire_current_density_a_per_mm2", 0.0) > 4.5:
        warnings.append("Current density is high; increase parallel count or use a larger wire.")
    if best.get("layers", 0) == 2:
        warnings.append("Best result uses 2 layers; winding layout should be checked carefully.")
    if best.get("b_total_pk_t", 0.0) > 0.8:
        warnings.append("Peak flux is high; validate the margin experimentally.")
    if best.get("t_core_c", 0.0) > _to_float(payload, "ambient_c", 40.0) + 0.9 * _to_float(payload, "rise_limit_c", 60.0):
        warnings.append("Core temperature is close to the configured rise limit.")
    warnings.append(f"Brute-force found {result_count} valid combinations after filtering.")
    return warnings


def bruteforce_search_pfc_inductors(payload: Dict, progress_callback=None) -> Dict:
    operating = _derive_operating_point(payload)
    cores = _select_cores(payload)
    wires = _select_wires(payload)
    valid_results: List[Dict] = []
    total_cores = len(cores)

    for index, core in enumerate(cores, start=1):
        core_valid = 0
        for wire in wires:
            if not _passes_filters(core, wire, payload):
                continue
            for turns in _turn_range(core, operating, payload):
                candidate = _evaluate_turn(core, wire, operating, payload, turns)
                if not candidate.get("feasible"):
                    continue
                candidate["core_id"] = core["id"]
                candidate["wire_id"] = wire["id"]
                candidate["core"] = core
                candidate["wire"] = wire
                valid_results.append(candidate)
                core_valid += 1
        if progress_callback:
            progress_callback(index, total_cores, core["part_number"], core_valid)

    total_valid = len(valid_results)
    _apply_minmax_score(valid_results, payload)
    valid_results.sort(key=lambda item: (item.get("rank_score", 1e9), item["p_tot_w"], item["core"]["ve_mm3"]))
    result_limit = max(1, _to_int(payload, "result_limit", 200))
    shown_results = valid_results[:result_limit]
    best = shown_results[0] if shown_results else None
    return {
        "operating_point": operating,
        "best": best,
        "results": shown_results,
        "count": total_valid,
        "shown_count": len(shown_results),
        "search_summary": {
            "mode": "bruteforce",
            "scanned_cores": total_cores,
            "fixed_parallel_count": _to_int(payload, "fixed_parallel_count", 0),
            "max_layers": max(1, min(2, _to_int(payload, "max_layers", 2))),
        },
        "warnings": _build_warnings(best, operating, payload, len(valid_results)),
    }


def evaluate_pfc_inductor(payload: Dict) -> Dict:
    result = bruteforce_search_pfc_inductors(dict(payload, max_search_cores=1), progress_callback=None)
    return {
        "selection": {"core": result["best"]["core"] if result["best"] else None, "wire": result["best"]["wire"] if result["best"] else None},
        "operating_point": result["operating_point"],
        "best": result["best"],
        "top_candidates": result["results"][:20],
        "feasible_count": result["count"],
        "warnings": result["warnings"],
    }


def search_pfc_inductors(payload: Dict) -> Dict:
    return bruteforce_search_pfc_inductors(payload, progress_callback=None)


def get_catalog() -> Dict:
    return _CATALOG
