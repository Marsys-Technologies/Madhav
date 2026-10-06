"""
tests/test_ga_panchanga_narr_golden.py -- Narr golden-value test for ga_panchanga

``chart_facts.citation_human`` is narration: the sentence a reader sees for a panchanga fact
(CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on the pure row emitters ``_emit_tithi`` / ``_emit_vara`` / ``_emit_yoga`` /
``_emit_karana`` (no database, hand-built PanchangaInstant stand-in carrying the native's
birth anchors): the sentences name the tithi (Shukla Tritiya, number 3, Shukla paksha), the
vara (Ravivara, the Sun's day, number 1), the yoga (Shiva, number 20 of 27) and the karana
(Garaja), and the end-time sentence states the fixture timestamp.
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from ga_writers.ga_panchanga_writer import (
    _emit_karana,
    _emit_tithi,
    _emit_vara,
    _emit_yoga,
)

PI = SimpleNamespace(
    tithi=SimpleNamespace(id=3, name="Shukla Tritiya", end_utc=datetime(1984, 2, 5, 11, 30, tzinfo=timezone.utc)),
    tithi_attrs=SimpleNamespace(anga_type="nanda", deity="Gauri", lord="Mars", pct_elapsed=0.25),
    vara=SimpleNamespace(id=1, name="Ravivara"),
    yoga=SimpleNamespace(id=20, name="Shiva", end_utc=datetime(1984, 2, 5, 14, 0, tzinfo=timezone.utc)),
    karana=SimpleNamespace(id=5, name="Garaja", end_utc=datetime(1984, 2, 5, 11, 30, tzinfo=timezone.utc)),
)


def test_panchanga_citation_human_birth_anchor_sentences() -> None:
    tithi = {r["fact_key"]: r for r in _emit_tithi(PI, "chart-fixture", "build-fixture", "2026-01-01T00:00:00+00:00")}
    vara = {r["fact_key"]: r for r in _emit_vara(PI, "chart-fixture", "build-fixture", "2026-01-01T00:00:00+00:00")}
    yoga = {r["fact_key"]: r for r in _emit_yoga(PI, "chart-fixture", "build-fixture", "2026-01-01T00:00:00+00:00")}
    karana = {r["fact_key"]: r for r in _emit_karana(PI, "chart-fixture", "build-fixture", "2026-01-01T00:00:00+00:00")}

    assert tithi["name"]["citation_human"] == "Tithi at birth: Shukla Tritiya."
    assert tithi["number_in_lunar_month"]["citation_human"] == "Tithi number: 3 (of 30)."
    assert tithi["paksha"]["citation_human"] == "Paksha: Shukla."
    assert tithi["end_iso"]["citation_human"] == "Tithi ends: 1984-02-05T11:30:00+00:00."
    assert vara["name"]["citation_human"] == "Vara at birth: Ravivara."
    assert vara["lord"]["citation_human"] == "Vara lord: Sun."
    assert yoga["name"]["citation_human"] == "Yoga at birth: Shiva."
    assert yoga["number"]["citation_human"] == "Yoga number: 20 (1=Vishkambha, 27=Vaidhriti)."
    assert yoga["inauspicious_flag"]["citation_human"] == "Yoga inauspicious: False."
    assert karana["name"]["citation_human"] == "Karana at birth: Garaja."
