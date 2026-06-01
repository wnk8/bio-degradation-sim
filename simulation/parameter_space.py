"""Parametergitter für Temp × pH-Heatmap-Analysen."""

import numpy as np
from typing import Any


def generate_parameter_grid(
    temp_range: list[float],
    ph_range: list[float],
    base_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Erstellt ein Meshgrid aus Temperatur- und pH-Werten als Parameterliste.

    Args:
        temp_range: Liste von Temperaturen (°C), z.B. [20, 30, 40, 50, 60]
        ph_range: Liste von pH-Werten, z.B. [5, 6, 7, 8, 9]
        base_params: Basis-Parameterdict; bei None werden Literaturwerte verwendet

    Returns:
        Liste von Parameterdicts, je ein Dict pro (temp, ph)-Kombination.
        Jedes Dict enthält zusätzlich den Key 'grid_temp' und 'grid_ph'.
    """
    if base_params is None:
        base_params = _default_params()

    temps = np.asarray(temp_range, dtype=float)
    phs = np.asarray(ph_range, dtype=float)

    temp_grid, ph_grid = np.meshgrid(temps, phs)

    grid = []
    for t, p in zip(temp_grid.ravel(), ph_grid.ravel()):
        entry = {
            **base_params,
            "temp_celsius": float(t),
            "ph": float(p),
            "grid_temp": float(t),
            "grid_ph": float(p),
        }
        grid.append(entry)

    return grid


def _default_params() -> dict[str, Any]:
    return {
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
