"""Integrations-Tests für core/ode_solver.py."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.ode_solver import solve_degradation

BASE_PARAMS = {
    "vmax_petase": 0.026,
    "km_petase": 0.15,
    "ea_petase": 50000,
    "vmax_mhetase": 0.083,
    "km_mhetase": 0.21,
    "ea_mhetase": 48000,
    "temp_celsius": 30.0,
    "ph": 7.0,
    "pet0": 1.0,
    "mhet0": 0.0,
}


def test_pet_decreases_over_time():
    """PET-Konzentration muss über die Zeit abnehmen."""
    result = solve_degradation(BASE_PARAMS)
    assert result["PET"][-1] < result["PET"][0]


def test_tpa_increases_over_time():
    """TPA-Konzentration muss über die Zeit zunehmen."""
    result = solve_degradation(BASE_PARAMS)
    assert result["TPA"][-1] > 0.0
    assert result["TPA"][-1] > result["TPA"][0]


def test_mass_conservation():
    """Massenerhalt: PET+MHET+TPA muss konstant bleiben (±1%)."""
    result = solve_degradation(BASE_PARAMS)
    total = result["PET"] + result["MHET"] + result["TPA"]
    initial_mass = total[0]
    max_deviation = np.max(np.abs(total - initial_mass)) / initial_mass
    assert max_deviation < 0.01, f"Massenabweichung zu groß: {max_deviation:.4f}"


def test_all_concentrations_non_negative():
    """Alle Konzentrationen müssen nicht-negativ bleiben."""
    result = solve_degradation(BASE_PARAMS)
    assert np.all(result["PET"] >= -1e-10)
    assert np.all(result["MHET"] >= -1e-10)
    assert np.all(result["TPA"] >= -1e-10)


def test_higher_temperature_gives_faster_degradation():
    """Höhere Temperatur → schnellerer Abbau (mehr TPA nach 120 min)."""
    params_30 = {**BASE_PARAMS, "temp_celsius": 30.0}
    params_50 = {**BASE_PARAMS, "temp_celsius": 50.0}
    r30 = solve_degradation(params_30)
    r50 = solve_degradation(params_50)
    assert r50["TPA"][-1] > r30["TPA"][-1]


def test_output_keys_present():
    """Rückgabe-Dict muss t, PET, MHET, TPA enthalten."""
    result = solve_degradation(BASE_PARAMS)
    for key in ("t", "PET", "MHET", "TPA"):
        assert key in result
        assert len(result[key]) > 0
