"""
test_ga_medical_f_e5_sun_forensic_guard.py — F-E5
(L1_W1_ANALYSIS_BATCH_E.md): `ga_medical_writer.py`'s FORENSIC guard halted the
whole build if Sun's indication_strength != 'strong', on the stated ground
"Sun debilitated in Capricorn" -- Sun's actual debilitation sign is Libra,
not Capricorn; Capricorn (Saturn's sign) is merely Sun's classical
enemy_sign. The identical error was already found and removed from
ga_vastu_writer.py. It passed today only by coincidence: enemy_sign's score
(0.26) also falls under the 0.4 threshold a genuinely debilitated Sun would
produce (§N.8: the assertion never measured the claim it stated).

Fix: downgraded from a build-halting AssertionError to a non-fatal warning
(§N.4 S7 precedent), and corrected the classical claim in both the code
comment and the warning text itself.

DB-free: sun_forensic_guard_warning is a pure function.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_medical_writer import (  # noqa: E402
    indication_strength_from_score,
    sun_forensic_guard_warning,
)


def test_measured_enemy_sign_score_produces_no_warning():
    """The exact live reproducer: Sun's measured condition_score in Capricorn
    (enemy_sign) is 0.26, which resolves to 'strong' -- no warning fires."""
    assert indication_strength_from_score(0.26) == "strong"
    assert sun_forensic_guard_warning(0.26) is None


def test_warning_fires_when_strength_is_not_strong():
    assert indication_strength_from_score(0.5) == "moderate"
    warning = sun_forensic_guard_warning(0.5)
    assert warning is not None


def test_warning_text_names_the_correct_classical_relationship():
    """The warning must never repeat the false 'debilitated' claim, and must
    correctly identify enemy_sign + Sun's real debilitation sign."""
    warning = sun_forensic_guard_warning(0.5)
    assert warning is not None
    assert "debilitated" not in warning.lower()  # the false claim this fix removes
    assert "enemy_sign" in warning
    assert "Libra" in warning


def test_none_score_produces_a_warning_not_a_crash():
    """condition_score unavailable -> 'unknown' tier -> non-fatal warning, never
    an unhandled exception (this used to be an AssertionError path too)."""
    assert indication_strength_from_score(None) == "unknown"
    warning = sun_forensic_guard_warning(None)
    assert warning is not None
