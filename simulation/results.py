"""Aggregation von Monte-Carlo-Ergebnissen mit Konfidenzintervallen."""

import numpy as np
import pandas as pd
from scipy import stats


def aggregate_results(mc_df: pd.DataFrame) -> dict:
    """Aggregiert Monte-Carlo-Ergebnisse und berechnet 95%-Konfidenzintervalle.

    Args:
        mc_df: DataFrame aus run_monte_carlo() mit Spalten
               final_tpa (mM), max_rate (µmol/min/mg), t_half (min)

    Returns:
        Dict mit Keys:
            mean_final_tpa (mM), std_final_tpa (mM),
            ci_95_lower (mM), ci_95_upper (mM),
            max_rate (µmol/min/mg),        # Maximum aller Runs
            mean_max_rate (µmol/min/mg),   # Mittelwert der max_rate
            mean_t_half (min),
            n_runs (int), n_valid (int)
    """
    valid = mc_df.dropna(subset=["final_tpa", "max_rate"])
    n_valid = len(valid)

    if n_valid == 0:
        return {
            "mean_final_tpa": float("nan"),
            "std_final_tpa": float("nan"),
            "ci_95_lower": float("nan"),
            "ci_95_upper": float("nan"),
            "max_rate": float("nan"),
            "mean_max_rate": float("nan"),
            "mean_t_half": float("nan"),
            "n_runs": len(mc_df),
            "n_valid": 0,
        }

    tpa_values = valid["final_tpa"].to_numpy()
    mean_tpa = float(np.mean(tpa_values))
    std_tpa = float(np.std(tpa_values, ddof=1))
    sem_tpa = std_tpa / np.sqrt(n_valid)

    ci = stats.norm.interval(0.95, loc=mean_tpa, scale=sem_tpa)

    rate_values = valid["max_rate"].to_numpy()
    t_half_values = mc_df["t_half"].dropna().to_numpy()

    return {
        "mean_final_tpa": mean_tpa,
        "std_final_tpa": std_tpa,
        "ci_95_lower": float(ci[0]),
        "ci_95_upper": float(ci[1]),
        "max_rate": float(np.max(rate_values)),
        "mean_max_rate": float(np.mean(rate_values)),
        "mean_t_half": float(np.mean(t_half_values)) if len(t_half_values) > 0 else float("nan"),
        "n_runs": len(mc_df),
        "n_valid": n_valid,
    }
