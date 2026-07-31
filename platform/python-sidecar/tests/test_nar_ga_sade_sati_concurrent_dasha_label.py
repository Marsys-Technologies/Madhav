"""
test_nar_ga_sade_sati_concurrent_dasha_label.py — B-NAR-GA regression test for
SAMĀPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §4.2 P2 finding at
ga_sade_sati_writer.py:974.

Prior defect: _emit_cycle_rows' per-phase concurrent-dasha-lord loop built
citation_human from the raw snake_case fact_key itself —
    f"{dasha_key} during {cy_id} {phase_name}: {dasha_val} ({ayanamsha_id})."
e.g. "concurrent_vimshottari_maha_lord during CYCLE_1 VISHAKHA: MARS
(Lahiri)." — an internal machine identifier narrated verbatim as if it were
prose. This is a drift against the sibling
sade_sati_concurrent_dasha_overlay block (cycle-start variant, same file,
same 7 keys) which already carries a proper human label for each key
("Vimshottari mahadasha lord at cycle start: MARS (Lahiri).").

Fix: a new CONCURRENT_DASHA_LABELS map gives the phase-level loop the same
human labels its cycle-start sibling already uses (minus the "at cycle
start" suffix, since this fires per-phase). fact_key (the DB column) is
unchanged — only citation_human (the narrated sentence) is fixed.

Uses this test directory's existing fixture style (test_ga9_writer.py):
MOCK_NATAL_FACTS + a real cycle built via build_sade_sati_cycles, then
_emit_cycle_rows called directly (DB-free).
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from ga_writers.ga_sade_sati_writer import (  # noqa: E402
    CANONICAL_CHART_ID,
    CONCURRENT_DASHA_LABELS,
    build_sade_sati_cycles,
    _emit_cycle_rows,
)

CHART_ID = CANONICAL_CHART_ID
AYANAMSHA = "lahiri_chitrapaksha"
BUILD_ID = "test-build-id-nar-ga"
COMPUTED_AT = "2026-07-31T00:00:00+00:00"

CONCURRENT_DASHA_KEYS = [
    "concurrent_vimshottari_maha_lord",
    "concurrent_vimshottari_antar_lord",
    "concurrent_yogini_period_lord",
    "concurrent_ashtottari_lord",
    "concurrent_chara_karaka_sign",
    "concurrent_naisargika_age_bracket",
    "concurrent_mudda_lord",
]


def _make_dt(year: int, month: int = 1, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


AQUARIUS_SIGN_CHANGES = [
    {"date_utc": _make_dt(1958, 1, 12), "sign_from": "Sagittarius", "sign_to": "Capricorn"},
    {"date_utc": _make_dt(1960, 3, 5),  "sign_from": "Capricorn",   "sign_to": "Aquarius"},
    {"date_utc": _make_dt(1962, 5, 10), "sign_from": "Aquarius",    "sign_to": "Pisces"},
    {"date_utc": _make_dt(1964, 7, 20), "sign_from": "Pisces",      "sign_to": "Aries"},
]

MOCK_NATAL_FACTS: dict[str, Any] = {
    "moon_pada": 4,
    "saturn_yoga_karaka": False,
    "natal_saturn_aspects_natal_moon": False,
    "saturn_moon_parivartana": False,
    "moon_sign_lord_strong": False,
    "jupiter_aspects_saturn_during_cycle": False,
    "d10_karya_bhava_activation_flag": False,
    "d10_karya_activation_facts": [],
    "argala_during_period": [],
    "tara_bala_at_janma_peak": "PENDING_GA4_LOOKUP",
    "mars_aspect_during_period": False,
    "jupiter_aspect_during_period": False,
    "saturn_rahu_axis_flag": False,
    "eclipse_during_period": False,
    "concurrent_saturn_return": False,
    "saturn_vargottama_natal": False,
    # One real, resolved GA7 lookup — Mars is Vishakha-phase Vimshottari
    # mahadasha lord for this synthetic fixture cycle.
    "concurrent_vimshottari_maha_lord_at_vishakha": "MARS",
}


def _emit_rows_for_cycle_1() -> list[dict]:
    cycles = build_sade_sati_cycles("Aquarius", AQUARIUS_SIGN_CHANGES)
    assert len(cycles) >= 1
    return _emit_cycle_rows(
        CHART_ID, AYANAMSHA, BUILD_ID, cycles[0], [], MOCK_NATAL_FACTS, COMPUTED_AT,
    )


class TestConcurrentDashaCitationUsesHumanLabelNotRawKey:
    def test_all_7_keys_have_a_label_defined(self):
        for key in CONCURRENT_DASHA_KEYS:
            assert key in CONCURRENT_DASHA_LABELS, f"No human label defined for {key}"
            assert CONCURRENT_DASHA_LABELS[key][0].isupper() or " " in CONCURRENT_DASHA_LABELS[key]

    def test_citation_human_never_contains_the_raw_snake_case_key(self):
        # THE regression this test locks: pre-fix code embedded the literal
        # fact_key string (e.g. "concurrent_vimshottari_maha_lord") inside
        # citation_human's prose. A caller's narration should never expose an
        # internal identifier as if it were a natural-language label.
        rows = _emit_rows_for_cycle_1()
        dasha_rows = [r for r in rows if r["fact_key"] in CONCURRENT_DASHA_KEYS]
        assert len(dasha_rows) > 0, "expected concurrent-dasha rows to be emitted"
        for r in dasha_rows:
            assert r["fact_key"] not in r["citation_human"], (
                f"citation_human leaks the raw fact_key '{r['fact_key']}' verbatim: "
                f"{r['citation_human']!r}"
            )

    def test_citation_human_contains_the_proper_human_label(self):
        rows = _emit_rows_for_cycle_1()
        maha_rows = [r for r in rows if r["fact_key"] == "concurrent_vimshottari_maha_lord"]
        assert len(maha_rows) > 0
        for r in maha_rows:
            assert "Vimshottari mahadasha lord" in r["citation_human"], (
                f"Expected the human label in citation_human, got: {r['citation_human']!r}"
            )

    def test_resolved_lookup_narrates_the_real_value(self):
        # The one key this fixture actually resolves (MARS, Vishakha phase)
        # must appear narrated under its proper label.
        rows = _emit_rows_for_cycle_1()
        vishakha_maha_rows = [
            r for r in rows
            if r["fact_key"] == "concurrent_vimshottari_maha_lord"
            and "VISHAKHA" in r["citation_human"]
        ]
        assert len(vishakha_maha_rows) > 0
        assert any("MARS" in r["citation_human"] for r in vishakha_maha_rows)
