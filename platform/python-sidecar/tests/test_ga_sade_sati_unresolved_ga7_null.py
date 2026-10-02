"""TI-l1-min-fixes-001 addendum -- an unresolved GA7 concurrent-dasha lookup is a NULL with a
named reason, never a stored placeholder string.

Defect: `_emit_cycle_rows` defaulted `natal_facts.get(<key>, "PENDING_GA7_LOOKUP")` and stored
that literal as `fact_value_text` when the real chart_dashas lookup returned nothing: 130
production rows, all `concurrent_mudda_lord` (categories sade_sati_phase 100 and
sade_sati_concurrent_dasha_overlay 30), where the mudda dasha table's horizon (to 2032) ends
before the Sade Sati phase date. A placeholder presented as a value (CLAUDE.md §N.7 item 6: an
honest null beats an invented judgment).

Fix: the row is still emitted (row counts and the live integrity conjunct (o), which pins the
overlay category's tier to 'single', are unaffected), `fact_value_text` is NULL, and the
citation sentence carries the named reason `no_ga7_period_covers_date`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ga_writers.ga_sade_sati_writer import (
    DASHA_LOOKUP_SPECS,
    GA4_NO_TARA_REASON,
    GA7_NO_PERIOD_REASON,
    _emit_cycle_rows,
    build_sade_sati_cycles,
)
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

CHART_ID = "11111111-1111-4111-8111-111111111111"
AYANAMSHA = "lahiri_chitrapaksha"
BUILD_ID = "22222222-2222-4222-8222-222222222222"
COMPUTED_AT = "2026-10-02T00:00:00+00:00"


def _dt(y: int, m: int = 1, d: int = 1) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


SIGN_CHANGES = [
    {"date_utc": _dt(1958, 1, 12), "sign_from": "Sagittarius", "sign_to": "Capricorn"},
    {"date_utc": _dt(1960, 3, 5), "sign_from": "Capricorn", "sign_to": "Aquarius"},
    {"date_utc": _dt(1962, 5, 10), "sign_from": "Aquarius", "sign_to": "Pisces"},
    {"date_utc": _dt(1964, 7, 20), "sign_from": "Pisces", "sign_to": "Aries"},
]

BASE_FACTS: dict[str, Any] = {
    "moon_pada": 4, "saturn_yoga_karaka": False, "natal_saturn_aspects_natal_moon": False,
    "saturn_moon_parivartana": False, "moon_sign_lord_strong": False,
    "jupiter_aspects_saturn_during_cycle": False, "d10_karya_bhava_activation_flag": False,
    "d10_karya_activation_facts": [], "argala_during_period": [],
    "mars_aspect_during_period": False, "jupiter_aspect_during_period": False,
    "saturn_rahu_axis_flag": False, "eclipse_during_period": False,
    "concurrent_saturn_return": False, "saturn_vargottama_natal": False,
}

_OVERLAY = "sade_sati_concurrent_dasha_overlay"
_PHASE = "sade_sati_phase"


def _resolved(skip_dk: str | None = None) -> dict[str, Any]:
    facts = dict(BASE_FACTS)
    for dk, _sys, _lvl in DASHA_LOOKUP_SPECS:
        if dk == skip_dk:
            continue
        for at in ("cycle_start", "vishakha", "janma", "anumukha"):
            facts[f"concurrent_{dk}_at_{at}"] = "SATURN"
    return facts


def _rows(facts: dict[str, Any]) -> list[dict]:
    cycles = build_sade_sati_cycles("Aquarius", SIGN_CHANGES)
    assert cycles
    return _emit_cycle_rows(CHART_ID, AYANAMSHA, BUILD_ID, cycles[0], [], facts, COMPUTED_AT)


def _mudda(rows: list[dict], category: str) -> list[dict]:
    return [r for r in rows if r["fact_category"] == category and r["fact_key"] == "concurrent_mudda_lord"]


def test_unresolved_mudda_is_null_with_named_reason_not_a_placeholder_string():
    rows = _rows(_resolved(skip_dk="mudda_lord"))
    overlay, phase = _mudda(rows, _OVERLAY), _mudda(rows, _PHASE)
    assert len(overlay) == 1 and len(phase) == 3  # one per cycle, one per phase: still emitted
    for r in overlay + phase:
        assert r["fact_value_text"] is None
        assert r["fact_value_num"] is None and r["fact_value_jsonb"] is None
        assert GA7_NO_PERIOD_REASON in r["citation_human"]
        assert "mudda level-1" in r["citation_human"]
        # integrity (o) pins the overlay category's tier to 'single'; keep the honest tier everywhere
        assert r["verification_pass_status"] == UNVERIFIED_DEFAULT == "single"
    # no stored value, anywhere, is a PENDING_GA7 placeholder
    for r in rows:
        assert "PENDING_GA7_LOOKUP" not in str(r["fact_value_text"])
        assert "PENDING_GA7_LOOKUP" not in r["citation_human"]


def test_resolved_values_are_unchanged_and_row_counts_identical():
    resolved = _rows(_resolved())
    unresolved = _rows(_resolved(skip_dk="mudda_lord"))
    assert len(resolved) == len(unresolved)  # null, not omit: counts (and count_sql) unaffected
    assert [(r["fact_category"], r["fact_subject"], r["fact_key"]) for r in resolved] == [
        (r["fact_category"], r["fact_subject"], r["fact_key"]) for r in unresolved
    ]
    for r in _mudda(resolved, _OVERLAY) + _mudda(resolved, _PHASE):
        assert r["fact_value_text"] == "SATURN"
        assert GA7_NO_PERIOD_REASON not in r["citation_human"]
    # the only rows that differ are the 4 mudda rows
    diff = [
        (a["fact_category"], a["fact_key"]) for a, b in zip(resolved, unresolved)
        if a["fact_value_text"] != b["fact_value_text"]
    ]
    assert sorted(diff) == sorted([(_OVERLAY, "concurrent_mudda_lord")] + [(_PHASE, "concurrent_mudda_lord")] * 3)


def test_every_one_of_the_seven_keys_gets_the_same_treatment():
    for dk, system_id, level_n in DASHA_LOOKUP_SPECS:
        rows = _rows(_resolved(skip_dk=dk))
        hit = [r for r in rows if r["fact_key"] == f"concurrent_{dk}"]
        assert len(hit) == 4
        for r in hit:
            assert r["fact_value_text"] is None
            assert f"{system_id} level-{level_n}" in r["citation_human"]


# ── sibling: GA4 Tara-bala (was the PENDING_GA4_LOOKUP default; 0 live stored rows) ────────────

def _tara_rows(rows: list[dict]) -> list[dict]:
    return [
        r for r in rows
        if (r["fact_category"], r["fact_key"]) in (
            ("sade_sati_phase", "tara_bala_during_peak"),
            ("sade_sati_downstream_cross_reference", "tara_bala_baseline_ref"),
        )
    ]


def test_unresolved_tara_bala_is_null_with_named_reason():
    rows = _rows(_resolved())  # BASE_FACTS carries no tara_bala_at_janma_peak
    tara = _tara_rows(rows)
    assert len(tara) == 2  # still emitted: JANMA phase row + cycle cross-reference row
    for r in tara:
        assert r["fact_value_text"] is None
        assert GA4_NO_TARA_REASON in r["citation_human"]
        assert r["verification_pass_status"] == "single"
    for r in rows:
        assert "PENDING_GA4_LOOKUP" not in str(r["fact_value_text"])
        assert "PENDING_GA4_LOOKUP" not in r["citation_human"]


def test_resolved_tara_bala_is_stored_as_is():
    tara = _tara_rows(_rows({**_resolved(), "tara_bala_at_janma_peak": "Sampat"}))
    assert [r["fact_value_text"] for r in tara] == ["Sampat", "Sampat"]
    assert all(GA4_NO_TARA_REASON not in r["citation_human"] for r in tara)
