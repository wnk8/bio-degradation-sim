"""Michaelis-Menten-Enzymkinetik."""


def michaelis_menten(v_max: float, km: float, substrate: float) -> float:
    """Berechnet die Reaktionsgeschwindigkeit nach Michaelis-Menten.

    Args:
        v_max: Maximale Reaktionsgeschwindigkeit (µmol/min/mg Enzym)
        km: Michaelis-Konstante, Substratkonzentration bei v = Vmax/2 (mM)
        substrate: Aktuelle Substratkonzentration (mM)

    Returns:
        Reaktionsgeschwindigkeit v (µmol/min/mg Enzym)
    """
    if substrate < 0:
        raise ValueError(f"Substratkonzentration darf nicht negativ sein: {substrate}")
    if km <= 0:
        raise ValueError(f"Km muss positiv sein: {km}")
    if v_max < 0:
        raise ValueError(f"Vmax darf nicht negativ sein: {v_max}")
    return (v_max * substrate) / (km + substrate)
