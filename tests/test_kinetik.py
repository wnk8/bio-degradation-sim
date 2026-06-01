"""Unit-Tests für core/kinetik.py."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.kinetik import michaelis_menten


def test_v_equals_half_vmax_at_km():
    """Bei substrate == Km muss v = Vmax/2 gelten."""
    v_max = 1.0
    km = 0.5
    result = michaelis_menten(v_max=v_max, km=km, substrate=km)
    assert abs(result - v_max / 2) < 1e-12


def test_zero_substrate_gives_zero_velocity():
    """substrate=0 muss v=0 ergeben."""
    assert michaelis_menten(v_max=0.026, km=0.15, substrate=0.0) == 0.0


def test_high_substrate_approaches_vmax():
    """Bei sehr hoher Substratkonzentration nähert sich v Vmax an (>99%)."""
    v_max = 0.083
    km = 0.21
    v = michaelis_menten(v_max=v_max, km=km, substrate=1000.0)
    assert v > 0.99 * v_max


def test_literature_petase_values():
    """Literaturwerte PETase (Yoshida 2016): plausible Rate bei 1 mM PET."""
    v = michaelis_menten(v_max=0.026, km=0.15, substrate=1.0)
    assert 0.02 < v < 0.026


def test_negative_substrate_raises():
    with pytest.raises(ValueError):
        michaelis_menten(v_max=1.0, km=0.5, substrate=-0.1)


def test_nonpositive_km_raises():
    with pytest.raises(ValueError):
        michaelis_menten(v_max=1.0, km=0.0, substrate=1.0)
