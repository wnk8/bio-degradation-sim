"""ODE-System für den gekoppelten PETase/MHETase-Abbauweg."""

from typing import Any
import numpy as np
from scipy.integrate import solve_ivp

from .kinetik import michaelis_menten
from .arrhenius import arrhenius_factor, ph_factor


def solve_degradation(
    params: dict[str, Any],
    t_span: tuple[float, float] = (0.0, 120.0),
    n_points: int = 300,
) -> dict[str, np.ndarray]:
    """Löst das gekoppelte ODE-System PET → MHET → TPA.

    Reaktionen:
        v1 = MM(Vmax_PETase,  Km_PETase,  [PET])  * Arrhenius(Ea_PETase,  T) * pH-Faktor
        v2 = MM(Vmax_MHETase, Km_MHETase, [MHET]) * Arrhenius(Ea_MHETase, T) * pH-Faktor

        d[PET]/dt  = -v1
        d[MHET]/dt =  v1 - v2
        d[TPA]/dt  =  v2

    Args:
        params: Dict mit folgenden Keys:
            vmax_petase  (µmol/min/mg), km_petase  (mM), ea_petase  (J/mol),
            vmax_mhetase (µmol/min/mg), km_mhetase (mM), ea_mhetase (J/mol),
            temp_celsius (°C), ph (dimensionslos),
            pet0 (mM, Anfangskonzentration PET),
            mhet0 (mM, Anfangskonzentration MHET, Default 0)
        t_span: (t_start, t_end) in Minuten, Default (0, 120)
        n_points: Anzahl Ausgabepunkte, Default 300

    Returns:
        Dict mit Arrays: t (min), PET (mM), MHET (mM), TPA (mM)
    """
    vmax_p = params["vmax_petase"]
    km_p = params["km_petase"]
    ea_p = params["ea_petase"]
    vmax_m = params["vmax_mhetase"]
    km_m = params["km_mhetase"]
    ea_m = params["ea_mhetase"]
    temp = params["temp_celsius"]
    ph = params.get("ph", 7.0)
    pet0 = params["pet0"]
    mhet0 = params.get("mhet0", 0.0)

    arr_p = arrhenius_factor(ea_p, temp)
    arr_m = arrhenius_factor(ea_m, temp)
    f_ph = ph_factor(ph)

    eff_vmax_p = vmax_p * arr_p * f_ph
    eff_vmax_m = vmax_m * arr_m * f_ph

    def odes(t: float, y: np.ndarray) -> list[float]:
        pet, mhet, tpa = y
        pet = max(pet, 0.0)
        mhet = max(mhet, 0.0)
        v1 = michaelis_menten(eff_vmax_p, km_p, pet)
        v2 = michaelis_menten(eff_vmax_m, km_m, mhet)
        return [-v1, v1 - v2, v2]

    y0 = [pet0, mhet0, 0.0]
    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    sol = solve_ivp(
        odes,
        t_span,
        y0,
        method="RK45",
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-9,
    )

    return {
        "t": sol.t,
        "PET": sol.y[0],
        "MHET": sol.y[1],
        "TPA": sol.y[2],
    }
