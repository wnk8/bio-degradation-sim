"""Monte-Carlo-Analyse mit normalverteilter Parameterstreuung."""

import numpy as np
import pandas as pd
from typing import Any

from core.ode_solver import solve_degradation


def run_monte_carlo(
    base_params: dict[str, Any],
    n_runs: int = 500,
    noise_fraction: float = 0.15,
    seed: int | None = None,
) -> pd.DataFrame:
    """Führt N Monte-Carlo-Runs mit ±noise_fraction Streuung auf Vmax und Km durch.

    Für jeden Run werden Vmax_PETase, Km_PETase, Vmax_MHETase, Km_MHETase
    aus einer Normalverteilung N(mu, sigma=noise_fraction*mu) gezogen.
    Negative Stichproben werden auf einen Minimalwert (1% des mu) geclamped.

    Args:
        base_params: Basis-Parameterdict (siehe core.ode_solver.solve_degradation)
        n_runs: Anzahl Monte-Carlo-Runs (Default 500)
        noise_fraction: Relative Standardabweichung, z.B. 0.15 für ±15% (Default 0.15)
        seed: Zufallsseed für Reproduzierbarkeit (Default None)

    Returns:
        DataFrame mit Spalten:
            run_id, vmax_petase, km_petase, vmax_mhetase, km_mhetase,
            final_tpa (mM), max_rate (µmol/min/mg), t_half (min oder NaN)
    """
    rng = np.random.default_rng(seed)

    vmax_p_mu = base_params["vmax_petase"]
    km_p_mu = base_params["km_petase"]
    vmax_m_mu = base_params["vmax_mhetase"]
    km_m_mu = base_params["km_mhetase"]

    vmax_p_samples = rng.normal(vmax_p_mu, noise_fraction * vmax_p_mu, n_runs)
    km_p_samples = rng.normal(km_p_mu, noise_fraction * km_p_mu, n_runs)
    vmax_m_samples = rng.normal(vmax_m_mu, noise_fraction * vmax_m_mu, n_runs)
    km_m_samples = rng.normal(km_m_mu, noise_fraction * km_m_mu, n_runs)

    # Clamp auf positiven Minimalwert
    vmax_p_samples = np.maximum(vmax_p_samples, 0.01 * vmax_p_mu)
    km_p_samples = np.maximum(km_p_samples, 0.01 * km_p_mu)
    vmax_m_samples = np.maximum(vmax_m_samples, 0.01 * vmax_m_mu)
    km_m_samples = np.maximum(km_m_samples, 0.01 * km_m_mu)

    records = []
    for i in range(n_runs):
        params = {
            **base_params,
            "vmax_petase": float(vmax_p_samples[i]),
            "km_petase": float(km_p_samples[i]),
            "vmax_mhetase": float(vmax_m_samples[i]),
            "km_mhetase": float(km_m_samples[i]),
        }
        try:
            result = solve_degradation(params)
            final_tpa = float(result["TPA"][-1])
            # max_rate: maximale Änderungsrate von TPA (Vorwärtsdifferenz)
            dt = np.diff(result["t"])
            dtpa = np.diff(result["TPA"])
            rates = dtpa / dt
            max_rate = float(np.max(rates)) if len(rates) > 0 else 0.0
            # t_half: Zeitpunkt, zu dem PET auf 50% des Anfangswerts gefallen ist
            pet0 = params["pet0"]
            half = pet0 / 2.0
            idx = np.where(result["PET"] <= half)[0]
            t_half = float(result["t"][idx[0]]) if len(idx) > 0 else float("nan")
        except Exception:
            final_tpa = float("nan")
            max_rate = float("nan")
            t_half = float("nan")

        records.append(
            {
                "run_id": i,
                "vmax_petase": float(vmax_p_samples[i]),
                "km_petase": float(km_p_samples[i]),
                "vmax_mhetase": float(vmax_m_samples[i]),
                "km_mhetase": float(km_m_samples[i]),
                "final_tpa": final_tpa,
                "max_rate": max_rate,
                "t_half": t_half,
            }
        )

    return pd.DataFrame(records)
