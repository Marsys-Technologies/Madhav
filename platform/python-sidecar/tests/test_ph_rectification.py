"""
test_ph_rectification.py — R4 birth-time rectification (L4 Phala remediation).

DB-free tests for services.ph_rectification.engine + writer-contract AST checks.
A deterministic stub ascendant function is injected so these tests are fully
PyJHora-independent (no swisseph, no DB). The stub mirrors the real adapter's
behavior near the recorded birth: the lagna sign is stable for offsets ≥ -40 and
shifts to Pisces for earlier offsets (matching the empirical PyJHora LOCAL-JD
scan: Aries near 10:43, Pisces at ≈ -45 min and earlier, Taurus at ≈ +70 min and later).

Constraints exercised:
  - 37 candidate offsets (±90 min, 5-min steps)
  - LEAKAGE-FIREWALL excludes post-2020 + LEL v1.7 M5-A-S1 enrichment events
  - lagna_stable True near recorded time, False at extreme early offsets
  - best candidate has the highest mean lel_fit_score
  - confidence_label thresholds (decisive ≥ 0.10, probable ≥ 0.05, else unresolved)
  - writer never commits/closes ctx.db_conn (source AST check)
  - writer writes ONLY phala_rectification + phala_rectification_best
  - D43 NO-AUTO-OVERRIDE: writer never executes UPDATE on charts; auto_action fixed
"""
from __future__ import annotations

import ast
import dataclasses
import os
from datetime import datetime, timezone

import pytest

from services.ph_rectification import engine as E
from services.ph_rectification.engine import (
    AYANAMSHAS,
    AUTO_ACTION,
    RECORDED_BIRTH_UTC,
    TrainingEvent,
    build_candidate_offsets,
    domain_significator_houses,
    run_rectification,
    select_best,
    score_candidate,
    _firewall_filter,
)

WRITER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "pipeline", "orchestrator",
    "writers", "ph_rectification", "__init__.py",
)

# ── Stub ascendant ───────────────────────────────────────────────────────────
# Mirrors the empirical PyJHora scan (LOCAL JD): Aries ~12.4° at offset 0,
# Pisces at ≈ -45 min and earlier, Taurus at ≈ +70 min and later.
_BASE_DEG = 12.421  # Aries ~12.4 deg at offset 0 (sidereal long 0*30+12.4, lahiri)


def _stub_ascendant(offset_minutes: int, ayanamsha_id: str) -> dict:
    long_deg = (_BASE_DEG + offset_minutes * 0.26) % 360.0
    sign_idx = int(long_deg // 30)
    names = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    return {
        "sign": names[sign_idx],
        "longitude_deg": long_deg,
        "degree_in_sign": long_deg - sign_idx * 30,
    }


# ── Candidate generation ─────────────────────────────────────────────────────
def test_exactly_37_offsets():
    offsets = build_candidate_offsets()
    assert len(offsets) == 37
    assert offsets[0] == -90 and offsets[-1] == 90
    assert all((b - a) == 5 for a, b in zip(offsets, offsets[1:]))


def test_run_produces_37x5_rows():
    rows = run_rectification(_stub_ascendant)
    assert len(rows) == 37 * len(AYANAMSHAS) == 185
    assert len({r.offset_minutes for r in rows}) == 37
    assert {r.ayanamsha_id for r in rows} == set(AYANAMSHAS)


# ── Leakage firewall ─────────────────────────────────────────────────────────
def test_firewall_excludes_post_2020():
    evs = (
        TrainingEvent("EVT.2018.11.28.01", datetime(2018, 11, 28, tzinfo=timezone.utc),
                      "loss", "Mercury", "exact"),
        TrainingEvent("EVT.2021.01.15.01", datetime(2021, 1, 15, tzinfo=timezone.utc),
                      "health", "Mercury", "month-exact"),
    )
    clean = _firewall_filter(evs)
    ids = {e.event_id for e in clean}
    assert "EVT.2018.11.28.01" in ids
    assert "EVT.2021.01.15.01" not in ids


def test_firewall_excludes_m5a_enrichment():
    # A v1.7 M5-A-S1 enrichment id, even if pre-2020, must be held out.
    evs = (
        TrainingEvent("EVT.1998.XX.XX.02", datetime(1998, 6, 1, tzinfo=timezone.utc),
                      "spiritual", "Saturn", "exact"),
    )
    assert _firewall_filter(evs) == []


def test_default_training_set_all_clean():
    clean = _firewall_filter(E.TRAINING_EVENTS)
    cutoff = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert len(clean) == len(E.TRAINING_EVENTS)  # authored already-clean
    assert all(e.date < cutoff for e in clean)
    assert all(e.date_confidence in ("exact", "month-exact") for e in clean)


# ── Lagna stability ──────────────────────────────────────────────────────────
def test_lagna_stable_near_recorded_time():
    rows = run_rectification(_stub_ascendant)
    near = [r for r in rows if r.offset_minutes == 0]
    assert all(r.lagna_stable for r in near)
    assert all(r.lagna_sign == "Aries" for r in near)


def test_lagna_unstable_at_extreme_early_offset():
    rows = run_rectification(_stub_ascendant)
    early = [r for r in rows if r.offset_minutes == -90]
    assert all(not r.lagna_stable for r in early)
    # sign has shifted away from the recorded-time sign
    assert all(r.lagna_sign != "Aries" for r in early)


def test_unstable_candidate_has_no_fit_score():
    rows = run_rectification(_stub_ascendant)
    early = [r for r in rows if r.offset_minutes == -90]
    assert all(r.lel_fit_score is None for r in early)


# ── Best selection ───────────────────────────────────────────────────────────
def test_best_has_highest_mean_score():
    rows = run_rectification(_stub_ascendant)
    best = select_best(rows)
    # recompute mean per offset; best score must be the max
    by_off: dict[int, list[float]] = {}
    for r in rows:
        if r.lel_fit_score is not None:
            by_off.setdefault(r.offset_minutes, []).append(r.lel_fit_score)
    max_mean = max((sum(v) / len(v)) for v in by_off.values())
    assert best.best_lel_fit_score == pytest.approx(max_mean, abs=1e-4)
    assert best.best_candidate is not None
    assert best.best_lagna_sign is not None


def test_best_auto_action_is_stage_for_review():
    rows = run_rectification(_stub_ascendant)
    best = select_best(rows)
    assert best.auto_action == AUTO_ACTION == "stage_for_review"


def test_confidence_label_thresholds():
    assert E._confidence_label(0.20) == "decisive"
    assert E._confidence_label(0.10) == "decisive"
    assert E._confidence_label(0.07) == "probable"
    assert E._confidence_label(0.05) == "probable"
    assert E._confidence_label(0.02) == "unresolved"
    assert E._confidence_label(0.0) == "unresolved"


def test_confidence_interval_widens_below_one():
    rows = run_rectification(_stub_ascendant)
    best = select_best(rows)
    assert best.confidence_low <= best.best_lel_fit_score <= best.confidence_high


def test_competing_candidates_top_3():
    rows = run_rectification(_stub_ascendant)
    best = select_best(rows)
    assert len(best.competing_candidates) <= 3
    scores = [c["mean_lel_fit_score"] for c in best.competing_candidates]
    assert scores == sorted(scores, reverse=True)


# ── Domain significator mapping ──────────────────────────────────────────────
def test_domain_houses_known_and_unknown():
    assert 10 in domain_significator_houses("career")
    assert 7 in domain_significator_houses("relationship")
    assert domain_significator_houses("nonsense_domain") == ()


def test_domain_houses_dual_tag_union():
    houses = domain_significator_houses("residential+travel")
    assert set(houses) >= set(domain_significator_houses("travel"))
    assert set(houses) >= set(domain_significator_houses("residential"))


# ── Sign-level scan behavior (documented limitation) ─────────────────────────
def test_uniform_scores_within_stable_window_is_expected():
    """Sign-level scan: all stable candidates share the same lagna sign
    → same dasha-lord house → same fit score. This is by design.
    The tiebreaker (abs(offset)=0) selects the recorded birth time.
    confidence_label='unresolved' is the honest B.10-compliant output."""
    rows = run_rectification(_stub_ascendant)
    # verify all stable candidates have the same fit score
    stable_scores = {r.lel_fit_score for r in rows if r.lagna_stable and r.lel_fit_score is not None}
    assert len(stable_scores) == 1, (
        f"Expected exactly one unique fit score across stable candidates (sign-level scan), "
        f"got {stable_scores}"
    )
    # verify best_offset == 0 (recorded time selected as tiebreaker)
    best = select_best(rows)
    assert best.offset_minutes == 0, (
        f"Expected tiebreaker to select recorded birth time (offset=0), got {best.offset_minutes}"
    )
    # verify confidence_label == 'unresolved' (zero win margin → honest output)
    assert best.confidence_label == "unresolved", (
        f"Expected 'unresolved' when all stable candidates score equally, got {best.confidence_label!r}"
    )


# ── Determinism ──────────────────────────────────────────────────────────────
def test_engine_is_deterministic():
    a = select_best(run_rectification(_stub_ascendant))
    b = select_best(run_rectification(_stub_ascendant))
    assert a.best_lel_fit_score == b.best_lel_fit_score
    assert a.offset_minutes == b.offset_minutes


def test_recorded_birth_utc_canonical():
    # 10:43 IST (UTC+5:30) == 05:13:00 UTC on 1984-02-05. Never fabricate.
    assert RECORDED_BIRTH_UTC == datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)


# ── Writer contract (source AST / text checks; no DB) ────────────────────────
def _writer_source() -> str:
    with open(WRITER_PATH) as f:
        return f.read()


def _writer_code_lines() -> str:
    src = _writer_source()
    lines = [
        ln for ln in src.splitlines()
        if not ln.strip().startswith("#") and '"""' not in ln and "'''" not in ln
    ]
    return "\n".join(lines)


def test_writer_never_commits_or_closes():
    code = _writer_code_lines()
    assert ".commit()" not in code
    assert ".rollback()" not in code
    assert ".close()" not in code


def test_writer_only_writes_rectification_tables():
    """Anti-drift: every INSERT/DELETE/UPDATE targets a phala_rectification* table."""
    code = _writer_code_lines().lower()
    # Tables touched by DML in the writer.
    import re
    targets = set()
    for m in re.finditer(r"\b(insert into|delete from|update)\s+([a-z_]+)", code):
        targets.add(m.group(2))
    assert targets <= {"phala_rectification", "phala_rectification_best"}, targets


def test_writer_no_auto_override_of_charts():
    """D43: writer must NEVER execute UPDATE/DELETE/INSERT against charts."""
    code = _writer_code_lines().lower()
    import re
    assert not re.search(r"update\s+charts\b", code)
    assert not re.search(r"delete\s+from\s+charts\b", code)
    assert not re.search(r"insert\s+into\s+charts\b", code)


def test_writer_auto_action_literal_present():
    """auto_action is bound to the engine's AUTO_ACTION constant (stage_for_review)."""
    src = _writer_source()
    assert "AUTO_ACTION" in src
    assert "stage_for_review" in src  # engine constant value; D43 hard gate


def test_writer_registers_asset_id():
    src = _writer_source()
    assert "@register(\"ph_rectification\")" in src or "@register('ph_rectification')" in src
    assert "WriterResult(asset_id=\"ph_rectification\"" in src \
        or "WriterResult(asset_id='ph_rectification'" in src


def test_writer_parses_as_valid_python():
    ast.parse(_writer_source())


# ── JL-017 contamination gate (BA Phase 2.5 #11) ────────────────────────────

def test_writer_no_longer_hard_refuses_non_native():
    """BA-P3 (native directive 2026-07-06): rectification is a per-chart asset
    every chart gets. The writer must NOT hard-raise for non-native charts;
    it sources each chart's OWN corpus instead (see the per-chart loaders)."""
    src = _writer_source()
    assert "Refusing rather than guessing" not in src
    assert "_load_chart_training_events" in src
    assert "_load_chart_natal_sign_index" in src


def test_writer_passes_explicit_training_events_for_non_native():
    """Contamination firewall: for a non-native chart the writer must pass
    EXPLICIT training_events (never None) so the engine's native-default
    fallback (TRAINING_EVENTS) is never reached."""
    src = _writer_source()
    # native -> None (embedded); else -> explicit per-chart lists
    assert "training_events = _load_chart_training_events(conn, chart_id)" in src
    assert "dasha_lord_natal_sign_index=natal_sign_index" in src


# ── per-chart loader unit tests (DB-free) ────────────────────────────────────

class _DictCursor:
    def __init__(self, script):
        # script: list of (matcher_substr, rows) consumed in order per execute
        self._script = script
        self._result: list = []

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        for matcher, rows in self._script:
            if matcher in s:
                self._result = list(rows)
                return
        self._result = []

    def fetchall(self): return list(self._result)
    def fetchone(self): return self._result[0] if self._result else None


class _ScriptConn:
    def __init__(self, script): self._script = script
    def cursor(self, *a, **k): return _DictCursor(self._script)


def test_load_training_events_chart_scoped_no_contamination():
    """BA-P4 R2.2/W2.2: post-migration-423 life_events is chart-scoped, so a chart
    reads ONLY its own events via WHERE chart_id = %s (that filter IS the JL-017
    contamination firewall). A chart with no rows of its own yields []. There is
    no native-identity short-circuit — every chart queries the same way."""
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    other_chart = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
    conn = _ScriptConn([
        # This chart has one own event; the WHERE chart_id filter scopes it.
        ("FROM life_events", [{"event_id": "EVT.2011.03.03", "event_date": datetime(2011, 3, 3),
                                "category": "career", "domain": "career"}]),
        ("FROM chart_dashas", [{"lord_graha": "Venus"}]),
    ])
    evs = _load_chart_training_events(conn, other_chart)
    assert len(evs) == 1
    assert evs[0].maha_dasha_lord == "Venus"  # this chart's own MD lord


def test_load_training_events_empty_when_no_life_events():
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    from services.ph_rectification.engine import NATIVE_CHART_ID
    conn = _ScriptConn([("FROM life_events", [])])
    assert _load_chart_training_events(conn, NATIVE_CHART_ID) == []


def test_load_training_events_missing_column_is_structural_not_crash():
    """Pre-423 schema (no chart_id column) → the chart-scoped read raises; the
    writer swallows it and returns [] (structural-only), never a hard failure."""
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    class _RaisingConn:
        def cursor(self, *a, **k):
            raise RuntimeError('column "chart_id" does not exist')
    assert _load_chart_training_events(_RaisingConn(), "any-chart") == []


def test_load_training_events_skips_event_when_no_own_md_lord():
    """An event whose per-chart mahadasha lord can't be found in THIS chart's
    chart_dashas is skipped — never fabricated, never native-defaulted."""
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    from services.ph_rectification.engine import NATIVE_CHART_ID
    conn = _ScriptConn([
        ("FROM life_events", [{"event_id": "EVT.2001.01.01", "event_date": datetime(2001, 1, 1),
                                "category": "career", "domain": "career"}]),
        ("FROM chart_dashas", []),  # no MD lord for this chart on that date
    ])
    assert _load_chart_training_events(conn, NATIVE_CHART_ID) == []


def test_load_training_events_uses_this_charts_own_md_lord():
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    from services.ph_rectification.engine import NATIVE_CHART_ID
    conn = _ScriptConn([
        ("FROM life_events", [{"event_id": "EVT.2001.01.01", "event_date": datetime(2001, 1, 1),
                                "category": "career", "domain": "career"}]),
        ("FROM chart_dashas", [{"lord_graha": "Jupiter"}]),  # THIS chart's own lord
    ])
    evs = _load_chart_training_events(conn, NATIVE_CHART_ID)
    assert len(evs) == 1
    assert evs[0].maha_dasha_lord == "Jupiter"  # the chart's own, not the native's
    assert evs[0].domain == "career"


def test_load_natal_sign_index_maps_this_charts_positions():
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_natal_sign_index
    conn = _ScriptConn([
        ("FROM chart_facts", [{"fact_subject": "SUN", "fact_value_text": "Aquarius"},
                               {"fact_subject": "SATURN", "fact_value_text": "Libra"}]),
    ])
    idx = _load_chart_natal_sign_index(conn, "chart-x")
    assert idx == {"Sun": 10, "Saturn": 6}


# ── Antar-dasha double-match extension (BA Phase 2.5 Phase 3, J7) ───────────

def test_antar_dasha_lord_derived_for_all_training_events():
    """All 19 embedded training events fall inside the Saturn or Mercury MD
    window, so the deterministic AD derivation must resolve a lord for all of
    them (no fabrication needed — pure classical proportion math)."""
    assert len(E.TRAINING_EVENTS) == 19
    assert all(ev.antar_dasha_lord is not None for ev in E.TRAINING_EVENTS)


def test_antar_dasha_lord_is_classically_consistent():
    """Spot check: the first AD sub-period of any MD is the MD lord's own AD
    (Vimshottari sequence always starts with the MD lord itself)."""
    saturn_start = datetime(1991, 8, 19, tzinfo=timezone.utc)
    assert E._antar_dasha_lord("Saturn", saturn_start) == "Saturn"
    mercury_start = datetime(2010, 8, 18, tzinfo=timezone.utc)
    assert E._antar_dasha_lord("Mercury", mercury_start) == "Mercury"


def test_antar_dasha_lord_none_outside_documented_md_window():
    assert E._antar_dasha_lord("Saturn", datetime(2015, 1, 1, tzinfo=timezone.utc)) is None
    assert E._antar_dasha_lord("Venus", datetime(2000, 1, 1, tzinfo=timezone.utc)) is None


def test_double_match_scores_higher_than_md_only_match():
    """A candidate whose training event has BOTH its MD lord and AD lord in a
    domain-significator house must score higher than one where only the MD
    lord matches — the 'double match' the J7 extension adds."""
    # Mercury MD, career domain -> significator houses (1, 6, 10, 11).
    # Event date 2010-12-15 falls in Mercury's own AD sub-period (the first AD
    # of the Mercury MD, per test_antar_dasha_lord_is_classically_consistent-
    # style reasoning), so its antar_dasha_lord resolves to "Mercury" too.
    event_md_only = TrainingEvent(
        "EVT.TEST.MD_ONLY", datetime(2010, 12, 15, tzinfo=timezone.utc),
        "career", "Mercury", "exact", antar_dasha_lord=None,
    )
    event_double = [ev for ev in E.TRAINING_EVENTS if ev.event_id == "EVT.2010.12.15.01"][0]
    assert event_double.antar_dasha_lord == "Mercury"
    assert event_double.domain == "travel"
    # Re-tag domain to career for an apples-to-apples comparison, keeping the
    # same dates/lords (both are pre-2020 dates already in TRAINING_EVENTS).
    event_double_career = dataclasses.replace(event_double, domain="career")

    dasha_map = {"Mercury": 9}  # Capricorn — arbitrary lagna-independent test map
    lagna_idx = 0  # Aries lagna: Capricorn (9) from Aries -> house 10 (career significator)

    md_only_score = E._score_dasha_match(lagna_idx, [event_md_only], dasha_map)
    double_score = E._score_dasha_match(lagna_idx, [event_double_career], dasha_map)

    assert md_only_score == 1
    assert double_score == 2
    assert double_score > md_only_score


def test_antar_dasha_none_falls_back_to_md_only_backward_compatible():
    """When antar_dasha_lord is None (e.g. a caller-supplied TrainingEvent that
    doesn't set it), scoring must behave exactly as it did before J7 — MD-only
    matching, matched in {0, 1} per event."""
    ev = TrainingEvent(
        "EVT.TEST.NO_AD", datetime(2010, 12, 15, tzinfo=timezone.utc),
        "career", "Mercury", "exact",
    )
    assert ev.antar_dasha_lord is None
    dasha_map = {"Mercury": 9}
    lagna_idx = 0
    assert E._score_dasha_match(lagna_idx, [ev], dasha_map) == 1


def test_run_rectification_accepts_explicit_training_events_and_dasha_map():
    """A caller-supplied training_events + dasha_lord_natal_sign_index must be
    used verbatim rather than silently falling back to the native's own data."""
    custom_events = [TrainingEvent("EVT.CUSTOM.01", datetime(2015, 1, 1, tzinfo=timezone.utc),
                                    "career", "Mars", "exact")]
    custom_map = {"Mars": 0}  # Aries

    candidates = run_rectification(
        _stub_ascendant,
        recorded_birth_utc=RECORDED_BIRTH_UTC,
        training_events=custom_events,
        dasha_lord_natal_sign_index=custom_map,
    )
    # lel_events_tested reflects the custom (1-event) set, not the native's 19.
    assert all(c.lel_events_tested == 1 for c in candidates)

    best = select_best(candidates, training_events=custom_events)
    assert best.lel_training_events == 1
