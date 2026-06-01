"""Arrhenius-Temperaturkorrektur für Enzymreaktionen."""

import math

R = 8.314       # universelle Gaskonstante, J/mol·K
T_REF_K = 303.15  # Referenztemperatur 30°C in Kelvin (Messbedingung der Literaturwerte)


def arrhenius_factor(ea: float, temp_celsius: float, t_ref_celsius: float = 30.0) -> float:
    """Relativer Arrhenius-Korrekturfaktor f(T) = exp(Ea/R * (1/T_ref - 1/T)).

    Die Literatur-Vmax-Werte (Yoshida 2016, Tournier 2020) wurden bei ~30°C gemessen.
    Der Faktor ist 1.0 bei T=T_ref und steigt mit der Temperatur.

    Beziehung zur absoluten Form: f(T) = exp(-Ea/RT) / exp(-Ea/RT_ref).

    Args:
        ea: Aktivierungsenergie (J/mol)
        temp_celsius: Simulationstemperatur (°C)
        t_ref_celsius: Referenztemperatur, bei der Vmax gemessen wurde (°C), Default 30.0

    Returns:
        Dimensionsloser Korrekturfaktor; 1.0 bei T=T_ref, >1 bei höherer Temperatur
    """
    if ea < 0:
        raise ValueError(f"Aktivierungsenergie muss nicht-negativ sein: {ea}")
    T = temp_celsius + 273.15
    T_ref = t_ref_celsius + 273.15
    if T <= 0:
        raise ValueError(f"Absolute Temperatur muss positiv sein: {T} K")
    if T_ref <= 0:
        raise ValueError(f"Referenztemperatur muss positiv sein: {T_ref} K")
    return math.exp((ea / R) * (1.0 / T_ref - 1.0 / T))


def ph_factor(ph: float, ph_opt: float = 7.0, sigma_ph: float = 1.0) -> float:
    """Gaussförmiger pH-Korrekturfaktor mit Optimum bei ph_opt.

    Args:
        ph: Aktueller pH-Wert
        ph_opt: Optimaler pH-Wert (dimensionslos), Default 7.0
        sigma_ph: Breite der Gauss-Kurve (dimensionslos), Default 1.0

    Returns:
        Dimensionsloser Faktor in (0, 1]
    """
    return math.exp(-0.5 * ((ph - ph_opt) / sigma_ph) ** 2)
