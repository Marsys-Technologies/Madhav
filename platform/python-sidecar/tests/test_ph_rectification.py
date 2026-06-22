"""
test_ph_rectification.py — R4 birth-time rectification (L4 Phala remediation).

DB-free tests for services.ph_rectification.engine + writer-contract AST checks.
A deterministic stub ascendant function is injected so these tests are fully
PyJHora-independent (no swisseph, no DB). The stub mirrors the real adapter's
behavior near the recorded birth: the lagna sign is stable for offsets ≥ -5 and
shifts to the previous sign for offsets < -5 (matching the empirical PyJHora
scan: Capricorn near 10:43, Sagittarius at ≈ -10 min and earlier).

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
# Mirrors the empirical PyJHora scan: Capricorn for offsets ≥ -5, Sagittarius
# earlier. degree advances ~0.26 deg/min so the longitude is monotonic.
_BASE_DEG = 272.1  # Capricorn ~2.1 deg at offset 0 (sidereal long 9*30+2.1, lahiri)


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
    assert all(r.lagna_sign == "Capricorn" for r in near)


def test_lagna_unstable_at_extreme_early_offset():
    rows = run_rectification(_stub_ascendant)
    early = [r for r in rows if r.offset_minutes == -90]
    assert all(not r.lagna_stable for r in early)
    # sign has shifted away from the recorded-time sign
    assert all(r.lagna_sign != "Capricorn" for r in early)


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
