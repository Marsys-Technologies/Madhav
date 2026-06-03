"""
test_ephemeris_derivations.py — pytest unit tests for ephemeris_derivations.

FORENSIC ground-truth assertions for native 1984-02-05, Bhubaneswar, IST.
Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md.

[BRAHMA-BG-0-1]
"""
import sys
import os

# Ensure the pipeline module is importable from the python-sidecar root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from pipeline.ephemeris_derivations import (
    compute_dignity,
    compute_combust,
    compute_vargottama,
    compute_whole_sign_house,
    compute_sign_ingress,
    NATIVE_LAGNA_IDX,
)


# ── TEST 8.1 — Saturn dignity on native birth date is exalted ─────────────────

def test_saturn_dignity_exalted_1984():
    """Saturn was in Libra at ~27° on 1984-02-05 (FORENSIC v8.0). Must be exalted."""
    result = compute_dignity('saturn', 'Libra', 27.3)
    assert result == 'exalted', f"Expected 'exalted', got {result!r}"


# ── TEST 8.2 — Sun in Capricorn is neutral (no special dignity) ───────────────

def test_sun_capricorn_neutral():
    """Sun in Capricorn at 15° has no special dignity (not exalted/debilitated/own)."""
    result = compute_dignity('sun', 'Capricorn', 15.0)
    assert result == 'neutral', f"Expected 'neutral', got {result!r}"


# ── TEST 8.3 — compute_combust returns True for Moon within 12° of Sun ────────

def test_moon_combust_within_12():
    """Moon within 12° of Sun is combust per BPHS classical threshold."""
    sun_lon = 295.0
    moon_lon = 300.0  # 5° ahead of sun
    result, orb = compute_combust('moon', moon_lon, sun_lon, is_retrograde=False)
    assert result is True, f"Expected combust=True, got {result!r}"
    assert orb is not None and orb < 12.0, f"Expected orb < 12.0, got {orb!r}"


# ── TEST 8.4 — whole_sign_house for Saturn in Libra from Aries lagna ──────────

def test_saturn_7th_house_from_aries():
    """Libra is the 7th sign from Aries lagna (whole-sign system)."""
    result = compute_whole_sign_house('Libra', NATIVE_LAGNA_IDX)
    assert result == 7, f"Expected house 7, got {result}"


# ── Additional sanity tests ───────────────────────────────────────────────────

def test_sun_exalted_in_aries():
    """Sun is exalted at 10° Aries (BPHS canonical)."""
    assert compute_dignity('sun', 'Aries', 10.0) == 'exalted'


def test_jupiter_debilitated_in_capricorn():
    """Jupiter is debilitated at 5° Capricorn (BPHS canonical)."""
    assert compute_dignity('jupiter', 'Capricorn', 5.0) == 'debilitated'


def test_moon_not_combust_beyond_threshold():
    """Moon at 25° from Sun is NOT combust (threshold is 12°)."""
    result, orb = compute_combust('moon', 320.0, 295.0, is_retrograde=False)
    assert result is False, f"Expected combust=False, got {result!r}"


def test_rahu_exalted_in_taurus():
    """Rahu is exalted in Taurus (sign-only check, no degree threshold)."""
    assert compute_dignity('rahu', 'Taurus', 0.0) == 'exalted'
    assert compute_dignity('rahu', 'Taurus', 29.9) == 'exalted'


def test_sun_not_combust_na():
    """Sun itself cannot be combust (N/A). compute_combust returns (False, None)."""
    result, orb = compute_combust('sun', 100.0, 100.0, is_retrograde=False)
    assert result is False
    assert orb is None


def test_sign_ingress_false_on_first_day():
    """First day in range has no prior sign, so ingress is False."""
    assert compute_sign_ingress('Aries', None) is False


def test_sign_ingress_true_when_changed():
    """If today_sign differs from prior_day_sign, ingress is True."""
    assert compute_sign_ingress('Taurus', 'Aries') is True


def test_sign_ingress_false_when_same():
    """If sign is unchanged from prior day, ingress is False."""
    assert compute_sign_ingress('Aries', 'Aries') is False
