"""Unit-Tests für core/arrhenius.py."""

import math
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.arrhenius import arrhenius_factor, ph_factor

R = 8.314


def test_arrhenius_at_ref_temp_equals_one():
    """f(T_ref) muss 1.0 sein — keine Korrektur bei Referenztemperatur."""
    ea = 50000.0
    result = arrhenius_factor(ea=ea, temp_celsius=30.0, t_ref_celsius=30.0)
    assert abs(result - 1.0) < 1e-14


def test_arrhenius_monotone_increasing_with_temperature():
    """Höhere Temperatur → höherer Faktor (Arrhenius ist monoton steigend)."""
    ea = 50000.0
    f25 = arrhenius_factor(ea=ea, temp_celsius=25.0)
    f30 = arrhenius_factor(ea=ea, temp_celsius=30.0)
    f60 = arrhenius_factor(ea=ea, temp_celsius=60.0)
    assert f25 < f30 < f60


def test_arrhenius_above_ref_greater_than_one():
    """Arrhenius-Faktor bei T > T_ref muss > 1 sein (schnellere Reaktion)."""
    f = arrhenius_factor(ea=48000.0, temp_celsius=50.0, t_ref_celsius=30.0)
    assert f > 1.0


def test_arrhenius_zero_activation_energy():
    """Ea=0 muss f=1 ergeben (kein Temperatureinfluss), unabhängig von T."""
    result = arrhenius_factor(ea=0.0, temp_celsius=55.0)
    assert abs(result - 1.0) < 1e-14


def test_ph_factor_optimum_at_7():
    """pH-Faktor bei pH=7.0 muss 1.0 sein."""
    assert abs(ph_factor(7.0) - 1.0) < 1e-15


def test_ph_factor_decreases_away_from_optimum():
    """pH-Faktor nimmt mit Abstand vom Optimum ab."""
    assert ph_factor(7.0) > ph_factor(6.0) > ph_factor(5.0)
    assert ph_factor(7.0) > ph_factor(8.0) > ph_factor(9.0)


def test_arrhenius_negative_ea_raises():
    with pytest.raises(ValueError):
        arrhenius_factor(ea=-1000.0, temp_celsius=25.0)
