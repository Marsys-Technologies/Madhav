"""
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

import sys
import uuid
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
LIVE_DSN = "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis"
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
    """The real, empirical Circularity-Guard invariance test — see module docstring for the
    full method + why the chosen proxy (`ka_jivana_parva`) is honest and provisional."""
    try:
        import psycopg
        import psycopg.rows
    except ImportError:
        pytest.skip("psycopg not installed in this environment")

    try:
        conn = psycopg.connect(LIVE_DSN, row_factory=psycopg.rows.dict_row, connect_timeout=5)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")

    conn.autocommit = False
    as_of = date.today()  # captured ONCE, reused for both runs — no midnight-boundary flake.

    try:
        from pipeline.orchestrator.writers import ContextSpec
        from pipeline.orchestrator.writers.ka_jivana_parva import KaJivanaParvaWriter

        def make_ctx() -> ContextSpec:
            return ContextSpec(
                asset_id="ka_jivana_parva",
                build_id="circularity-guard-lel-invariance-test",
                db_conn=conn,
                config={
                    "chart_id": CHART_ID,
                    "as_of_date": as_of,
                    "birth_params": BIRTH_PARAMS,
                },
            )

        writer = KaJivanaParvaWriter()

        # ── baseline run ──
        baseline_result = writer.run(make_ctx())
        assert baseline_result.rows_inserted > 0, (
            "baseline ka_jivana_parva build produced zero rows for the canonical chart "
            f"({CHART_ID}) — cannot assert invariance over an empty computation; check "
            "chart_dashas is populated (level_n IN (1,2), system_id='vimshottari', "
            "ayanamsha_id='lahiri_chitrapaksha')."
        )
        baseline_snapshot = _snapshot_parvas(conn, CHART_ID)
        assert len(baseline_snapshot) > 0

        # ── mutate: append ONE synthetic LEL row, same uncommitted transaction ──
        synthetic_event_id = f"circularity-guard-test-{uuid.uuid4()}"
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO life_events
                    (chart_id, event_id, event_date, event_type, description,
                     domain, outcome_observed, source_citation, recorded_at,
                     category, source_section, build_id, chart_state, provenance)
                VALUES (%s, %s, %s, %s, %s,
                        %s, %s, %s, now(),
                        %s, %s, %s, %s::jsonb, %s::jsonb)
                """,
                (
                    CHART_ID, synthetic_event_id, "1900-01-01", "test",
                    "CIRCULARITY GUARD CI TEST synthetic row — never committed, rolled back "
                    "at test teardown; must never appear in real data.",
                    "test/circularity_guard", True,
                    "CIRCULARITY_GUARD_TEST (ka_jivana_parva LEL-invariance, item 10)",
                    "test", "§CIRCULARITY_GUARD_TEST",
                    "circularity-guard-lel-invariance-test",
                    "{}", "{}",
                ),
            )

        # Sanity: the row IS visible in THIS transaction (read-your-own-writes) — otherwise
        # a failed insert would make the "no perturbation" result vacuous, not a real proof.
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM life_events WHERE chart_id = %s AND event_id = %s",
                (CHART_ID, synthetic_event_id),
            )
            assert cur.fetchone()["n"] == 1, (
                "synthetic LEL row failed to insert (or isn't visible in this transaction) — "
                "the invariance check below would be vacuous, not a real proof."
            )

        # ── re-run the SAME production writer, re-snapshot ──
        mutated_result = writer.run(make_ctx())
        mutated_snapshot = _snapshot_parvas(conn, CHART_ID)

        assert mutated_result.rows_inserted == baseline_result.rows_inserted, (
            "ka_jivana_parva's row count changed after appending an LEL row — CIRCULARITY "
            "GUARD VIOLATION (SHAD_DARSHANA_BRIEF_v2_0.md §7): the field-adjacent "
            "computation appears to be reading life_events."
        )
        assert mutated_snapshot == baseline_snapshot, (
            "ka_jivana_parva's output changed after appending an LEL row — CIRCULARITY "
            "GUARD VIOLATION (SHAD_DARSHANA_BRIEF_v2_0.md §7: 'the field never reads the "
            "LEL'). If this fails: either (a) ka_jivana_parva genuinely started reading "
            "life_events — a hard-stop bug, fix it before merging anything else — or "
            "(b) this proxy has gone stale and must be re-pointed at ka_kshetra/mi_bhara "
            "(W2) per this file's module docstring."
        )
    finally:
        conn.rollback()
        conn.close()
