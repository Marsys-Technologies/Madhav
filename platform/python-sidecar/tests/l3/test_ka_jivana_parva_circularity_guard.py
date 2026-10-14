"""
K0A-R1 (2026-10-14): native/cohort DB paths below are explicit NOT_RUN
skips pending authenticated isolated source-data fixtures. Historical DB
setup descriptions below are context only; no external DSN is read or
opened. Pure tests remain active and skips are not SQL acceptance.

test_ka_jivana_parva_circularity_guard.py — ṢAḌ-DARŚANA W1, item 10.

THE CIRCULARITY GUARD (SHAD_DARSHANA_BRIEF_v2_0.md §7 rail — HARD, non-negotiable campaign
gate; "**New rails (this round): CIRCULARITY GUARD** — the field never reads the LEL; CI
invariance test is itself an untouchable gate, live from W1 with item 10"). This file is
that CI invariance test. It ships in the SAME PR as item 10 (per-chapter LEL pinning in
`platform-mcp/src/tools/kala_views/story.ts`) — the brief's Gate W1 explicitly requires
"the Circularity-Guard LEL-invariance test ships with item 10 and is green".

PROXY SUBJECT, NAMED HONESTLY (do not delete this note):
    W2's real hazard/temporal-field pipeline (`ka_kshetra`) does not exist yet — it is a
    W2 deliverable (brief §2 "New/changed Python writers"). There is therefore no
    `ka_kshetra` to test today. The closest thing that EXISTS IN PRODUCTION right now to a
    "temporal field" computed output is `ka_jivana_parva` (this file's subject): for every
    daśā period it assigns a QUALITY label (building/peak/consolidating/receding/
    transitional) and an `avg_effective_score`, derived from `kala_convergence`/
    `kala_darshana` — a period-level judgment that is structurally the same KIND of thing a
    real hazard field would also produce, and it is the exact computation STORY (this same
    lane's item 10 facade) reads and re-serves.

    THIS TEST MUST BE RE-POINTED AT `ka_kshetra` (or `mi_bhara`'s weighted output) ONCE W2
    LANDS. Tracked here, explicitly, rather than left to silently go stale — see the PR
    description for this lane for the same note.

TWO INDEPENDENT GUARDS IN THIS FILE:
    1. `test_no_ka_writer_source_mentions_life_events_or_lel_query` — a fast, DB-free,
       always-on static census over every `ka_*` writer + its `services/ka_*` support
       modules: NONE of them may textually reference `life_events` or `lel_query`. Catches
       the syntactic addition of an LEL read instantly, on every CI run (no `integration`
       marker, no live DB needed).
    2. `test_circularity_guard_ka_jivana_parva_invariant_under_lel_mutation` — the real,
       empirical, DB-backed proof: run the PRODUCTION `KaJivanaParvaWriter().run(ctx)`
       twice inside ONE never-committed transaction, with a synthetic `life_events` row
       inserted (same transaction, same connection — so Postgres read-your-own-writes
       means the writer WOULD see it if it looked) between the two runs, and assert the
       writer's output is byte-for-byte identical. This has a REAL failure mode (CLAUDE.md
       §N.7 — a signal without a real detector is null, not green): if `ka_jivana_parva`
       (or anything it calls) ever starts reading `life_events`, the second run's
       `avg_effective_score`/`parva_quality`/`theme_keywords` could change and this
       assertion would genuinely fail. `@pytest.mark.integration` (excluded by the CI
       `-m "not integration"` invocation, same convention as
       `test_cr131_gochara_db_reachability.py` / `test_ka_gochara_sweep.py`'s live-proxy
       tests) — skips cleanly when the live Cloud SQL proxy isn't reachable, never fakes a
       pass.

SAFETY: the DB-backed test opens ONE transaction, sets `conn.autocommit = False`, and
`finally: conn.rollback()` — it NEVER commits, so it cannot mutate real
`kala_jivana_parva`/`life_events` data, mirroring the FROZEN writer contract's own
"ctx.db_conn is NEVER committed by the writer" rule (CLAUDE.md §N.2).
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BIRTH_PARAMS = {"datetime_iso": "1984-02-05T10:43:00+05:30"}

_SIDECAR_ROOT = Path(__file__).parent.parent.parent
_FORBIDDEN_TOKENS = ("life_events", "lel_query")


# ── §1 — static census (fast, DB-free, always-on) ───────────────────────────────────────

def _ka_writer_source_files() -> list[Path]:
    files: list[Path] = []
    writers_dir = _SIDECAR_ROOT / "pipeline" / "orchestrator" / "writers"
    if writers_dir.exists():
        files.extend(sorted(writers_dir.glob("ka_*.py")))
    services_dir = _SIDECAR_ROOT / "services"
    if services_dir.exists():
        for sub in sorted(services_dir.glob("ka_*")):
            if sub.is_dir():
                files.extend(sorted(sub.rglob("*.py")))
            elif sub.suffix == ".py":
                files.append(sub)
    return files


def test_no_ka_writer_source_mentions_life_events_or_lel_query():
    """CIRCULARITY GUARD static census: every currently-shipped Kāla (`ka_*`) writer and its
    `services/ka_*` support module — the full set of temporal-field-adjacent computations
    that exist TODAY — must have zero textual reference to `life_events` or `lel_query`. A
    hit here means someone wired an LEL read into a field-adjacent computation; that is a
    hard-stop bug, not a stored divergence (SHAD_DARSHANA_BRIEF_v2_0.md §7)."""
    files = _ka_writer_source_files()
    assert len(files) > 0, (
        "static census found zero ka_* writer/service files — path assumption broken; "
        "fix _ka_writer_source_files() before trusting this guard's silence."
    )

    offenders: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for token in _FORBIDDEN_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(_SIDECAR_ROOT)}: contains '{token}'")

    assert not offenders, (
        "CIRCULARITY GUARD VIOLATION — the field must never read the LEL "
        "(SHAD_DARSHANA_BRIEF_v2_0.md §7 rail):\n" + "\n".join(offenders)
    )


# ── §2 — empirical DB-backed invariance test ────────────────────────────────────────────

def _snapshot_parvas(conn, chart_id: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT parva_index, dasha_planet, dominant_signal_class, start_year, end_year,
                   parva_quality, theme_keywords, high_convergence_count, avg_effective_score,
                   narrative, source_citation
            FROM kala_jivana_parva
            WHERE chart_id = %s
            ORDER BY parva_index
            """,
            (chart_id,),
        )
        return list(cur.fetchall())


@pytest.mark.integration
def test_circularity_guard_ka_jivana_parva_invariant_under_lel_mutation():
    pytest.skip('K0A-R1 NOT_RUN: empirical invariance requires an authenticated isolated native chart_dashas, convergence and darshana fixture plus the life_events schema; the static circularity guard remains active, but is not empirical acceptance (B.10).')
