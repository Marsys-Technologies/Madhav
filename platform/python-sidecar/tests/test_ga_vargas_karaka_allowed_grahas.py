"""TI-ga-vargas-karaka-residual-001 (KARAKA_ROLES_LANE_INTENT v1.2, D4 + KNOWN-WRONG-COMMENTS).

D4: ga_vargas READS ga_sensitive's stored kn_rao karaka assignments. The shared reader takes `allowed_grahas`,
but only ga_dashas passed it, so ga_vargas accepted ANY stored graha text ("Ketu", "Pluto"). It must refuse a
karaka graha outside the seven classical grahas + Rahu, with the SAME allowed set as ga_dashas.

Comments: three comments on main contradicted the code (the alias row's tier; "the Matrikaraka doubles as
Pitrikaraka"; no tie-rule note). Comment-only edits; pinned here so they cannot silently regress.

No database: the pure core `_karakas_from_rows` takes stored (subject, key, text, num) rows.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ga_writers import _karaka_roles as kr
from ga_writers import ga_dashas_writer as gd
from ga_writers import ga_vargas_writer as gv

GW = Path(__file__).resolve().parents[1] / "ga_writers"
CHART, AY = "482012f1-710e-4a25-994a-93821f5871aa", "lahiri_chitrapaksha"
CANONICAL = ["Moon", "Saturn", "Sun", "Venus", "Mars", "Rahu", "Jupiter", "Mercury"]  # ranks 1..8 (native, Lahiri)


def _rows(grahas):
    out = []
    for i, (subject, graha) in enumerate(zip(kr.KARAKA_ROLES_8, grahas), start=1):
        out.append((subject, "assigned_graha", graha, None))
        out.append((subject, "karaka_rank", None, float(i)))
    return out


def test_valid_assignment_still_maps_ak_to_dk():
    assert gv._karakas_from_rows(_rows(CANONICAL), CHART, AY) == dict(zip(kr.KARAKA_ABBREVIATIONS_8, CANONICAL))


@pytest.mark.parametrize("bad", ["Ketu", "Pluto", "Uranus", "", "moon"])
def test_ga_vargas_refuses_a_karaka_graha_outside_the_seven_plus_rahu(bad):
    grahas = list(CANONICAL)
    grahas[7] = bad  # Darakaraka
    if not bad:
        grahas[7] = "Mercury "  # not in the set either
    with pytest.raises(gv.KarakaDependencyMissing, match="drawn from"):
        gv._karakas_from_rows(_rows(grahas), CHART, AY)


def test_ga_vargas_and_ga_dashas_use_the_same_allowed_graha_set():
    assert set(kr.KARAKA_ALLOWED_GRAHAS) == set(gd._KARAKAS_ACTIVE_GRAHA_ORDER)
    assert tuple(kr.KARAKA_ALLOWED_GRAHAS) == tuple(gd._KARAKAS_ACTIVE_GRAHA_ORDER)
    assert len(kr.KARAKA_ALLOWED_GRAHAS) == 8 and "Ketu" not in kr.KARAKA_ALLOWED_GRAHAS


def test_ga_dashas_still_refuses_the_same_input_so_both_consumers_agree():
    grahas = list(CANONICAL)
    grahas[7] = "Ketu"
    with pytest.raises(kr.KarakaDependencyMissing):
        kr.kn_rao_graha_by_rank(_rows(grahas), CHART, AY, consumer="ga_dashas", allowed_grahas=gd._KARAKAS_ACTIVE_GRAHA_ORDER)


def test_ga_vargas_call_site_passes_allowed_grahas():
    src = (GW / "ga_vargas_writer.py").read_text(encoding="utf-8")
    assert 'consumer="ga_vargas", allowed_grahas=KARAKA_ALLOWED_GRAHAS' in src


# ── known-wrong comments (comment-only fixes) ────────────────────────────────

def test_matrikaraka_doubles_as_pitrikaraka_claim_is_gone():
    for f in ("_karaka_roles.py", "ga_sensitive_writer.py"):
        assert "doubles as Pitrikaraka" not in (GW / f).read_text(encoding="utf-8"), f


def test_alias_tier_comment_matches_the_code_single():
    src = (GW / "ga_sensitive_writer.py").read_text(encoding="utf-8")
    assert "TWO_PASS_VERIFIED via _make_row" not in src
    assert "the alias is stored `single`" in src


def test_alias_row_really_is_single_tier():
    import inspect
    from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT
    from ga_writers import ga_sensitive_writer as gs
    assert inspect.signature(gs._make_row).parameters["verification_pass_status"].default == UNVERIFIED_DEFAULT


def test_tie_rule_comment_is_present():
    src = (GW / "ga_sensitive_writer.py").read_text(encoding="utf-8")
    assert "Exact-float ties keep Sun,Moon,Mars,Mercury,Jupiter,Venus,Saturn,Rahu order" in src
    assert "BPHS 32.3-8 minute/second tie rule not applied" in src
