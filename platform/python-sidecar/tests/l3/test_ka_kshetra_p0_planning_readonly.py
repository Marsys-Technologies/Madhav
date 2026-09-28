"""KSH-P0: `ka_kshetra.plan_substeps` is READ-ONLY, proven by execution.

`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §5 row P0, first hazard:

    "Kshetra planning deletes data before resume filtering."
    Required: "Make planning read-only; move replacement into the owned
    execution partition."
    Exit evidence: "Zero planning/dry-run mutations; crash/resume and
    empty-generation tests; restore prior data/outcomes."

The repair in the code under test (`services/ka_kshetra/writer.py`) is that
replacement lives in the `prepare:replace` EXECUTION substep
(`_run_prepare_replace` → `_delete_prior_rows`), not in `plan_substeps`. A
prior session READ that and believed it. Per CLAUDE.md §N.8 a fix with no
detector behind it is null, not green — so this module runs the real
`plan_substeps(ctx)` against a live Postgres and MEASURES.

Three independent detectors, so no single one can be vacuously true:
  D1  `txid_current_if_assigned()` stays NULL   (a write assigns an xid, even
      one that is later rolled back)
  D2  the same call inside `SET TRANSACTION READ ONLY`  (a write RAISES)
  D3  per-chart row-count + content digest of every writer-owned table is
      byte-identical across the call

MEASURED LIMITS OF EACH DETECTOR (established by running the negative fixture,
not assumed — §N.8):
  • D1 and D3 are BLIND to a write statement that modifies zero rows: Postgres
    assigns an xid only when a tuple is actually changed, and a no-op DELETE
    changes no content either. Every D1/D3 test therefore seeds a committed
    SENTINEL row first, so a planted DELETE has something to destroy. Without
    that seeding these two detectors are close to vacuous on an empty chart.
  • D2 has no such blind spot — `SET TRANSACTION READ ONLY` rejects the write
    STATEMENT, whether or not it would have matched a row. It is the strongest
    of the three and the one that survives an empty fixture.

`test_negative_fixture_*` plants a mutation in the planning path and asserts
ALL THREE fire — a test that has never failed is not a detector (F28).
"""
from __future__ import annotations

import pytest

from tests.l3._p0_harness import (
    CANONICAL_CHART_ID,
    connect,
    content_digest,
    make_ctx,
    owned_tables,
    xid,
)

ASSET = "ka_kshetra"
#: Tables planning reads that are NOT writer-owned; a planner that wrote to one
#: of these would escape the owned-table digest, so they are watched too.
WATCHED_EXTRA = ["build_substep_progress", "bodha_pratijna"]


@pytest.fixture
def conn():
    c = connect()
    yield c
    c.rollback()
    c.close()


@pytest.fixture
def writer():
    from services.ka_kshetra.writer import KaKshetraWriter

    return KaKshetraWriter()


@pytest.fixture
def sentinel(conn):
    """A committed row in two writer-owned tables, removed afterwards.

    Exists so D1/D3 are not vacuous: Postgres assigns no xid for a DELETE that
    matches nothing, and a no-op DELETE changes no digest either.
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_field_kinematics"
            " (chart_id, event_kind, body, t_days, event_ts, ayanamsha_id)"
            " VALUES (%s,'station','Sun',1.0,'2001-01-01T00:00:00Z','lahiri')",
            (CANONICAL_CHART_ID,),
        )
        cur.execute(
            "INSERT INTO kala_insights"
            " (chart_id, insight_id, insight_type, statement_key, statement_params,"
            "  fact_ids, surprise_basis, robustness, insight_score, weights_version,"
            "  lel_derived, field_snapshot_id)"
            " VALUES (%s,'p0-sentinel','concurrence','k','{}'::jsonb,"
            " ARRAY[]::text[],'none','{}'::jsonb, 0.5,'v0_classical', FALSE,"
            " 'p0-sentinel-snapshot')",
            (CANONICAL_CHART_ID,),
        )
    conn.commit()
    try:
        yield
    finally:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_field_kinematics WHERE chart_id = %s",
                        (CANONICAL_CHART_ID,))
            cur.execute("DELETE FROM kala_insights WHERE chart_id = %s",
                        (CANONICAL_CHART_ID,))
        conn.commit()


def _watched():
    return owned_tables() + WATCHED_EXTRA


# ── D1 + D3: the plain planning call ─────────────────────────────────────────

def test_planning_assigns_no_transaction_id_and_changes_no_content(conn, writer, sentinel):
    """The headline claim: planning performs ZERO mutations.

    Runs against a chart whose writer-owned slice is NOT empty (the `sentinel`
    fixture), so D1 and D3 have real content to lose — see the module docstring
    on why an empty fixture would leave both nearly vacuous.
    """
    assert xid(conn) is None, "fixture precondition: transaction has not written"
    before = content_digest(conn, _watched())
    assert before["kala_field_kinematics"][0] > 0 and before["kala_insights"][0] > 0, (
        "sentinel precondition: the detectors must have content to lose"
    )

    steps = writer.plan_substeps(make_ctx(conn, ASSET))

    assert xid(conn) is None, (
        "D1 FAILED: plan_substeps assigned a transaction id, which Postgres does "
        "only for a transaction that has written. Planning is not read-only."
    )
    after = content_digest(conn, _watched())
    assert after == before, f"D3 FAILED: planning changed content: {before} -> {after}"
    assert steps, "planning returned no substeps — the harness seed is wrong, not the writer"
    assert steps[0].key == "prepare:replace", (
        "replacement must be the LEADING EXECUTION substep (strategy P0: 'move "
        f"replacement into the owned execution partition'); got {steps[0].key!r}"
    )


# ── D2: an independent, server-enforced detector ─────────────────────────────

def test_planning_succeeds_inside_a_read_only_transaction(conn, writer, sentinel):
    """Server-side proof. In a READ ONLY transaction any write RAISES 25006."""
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SHOW transaction_read_only")
        assert cur.fetchone()["transaction_read_only"] == "on"

    steps = writer.plan_substeps(make_ctx(conn, ASSET))

    assert steps, "planning returned no substeps under a read-only transaction"
    assert xid(conn) is None


def test_read_only_transaction_detector_is_not_vacuous(conn):
    """D2's own control: prove the read-only transaction really does reject writes."""
    import psycopg

    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_field_kinematics WHERE chart_id = %s",
                (CANONICAL_CHART_ID,),
            )


# ── dry-run: the strategy says "planning/dry-run mutations", both ────────────

def test_dry_run_planning_and_dry_run_prepare_mutate_nothing(conn, writer, sentinel):
    """`ctx.dry_run` planning AND the dry-run prepare substep both write nothing."""
    before = content_digest(conn, _watched())
    ctx = make_ctx(conn, ASSET, dry_run=True)
    steps = writer.plan_substeps(ctx)
    assert xid(conn) is None, "D1 FAILED for dry-run planning"

    prepare = [s for s in steps if s.key == "prepare:replace"]
    assert prepare, "dry-run plan must still contain prepare:replace"
    result = writer.run_substep(ctx, prepare[0])

    assert xid(conn) is None, "D1 FAILED: the dry-run prepare substep wrote"
    assert content_digest(conn, _watched()) == before
    assert result.rows_inserted == 0
    assert "dry-run" in result.notes


# ── F28 negative fixture: prove the detectors CAN read false ─────────────────

def test_negative_fixture_detectors_catch_a_planted_planning_mutation(
    conn, writer, monkeypatch
):
    """Plant the P0 hazard back into the planning path; all three detectors fire.

    `plan_substeps` folds in each landed stage lane's planner via
    `_optional_stage_plugins`. Those planners are pure today. Here one of them
    is replaced with a planner that DELETES — the exact shape of the original
    hazard ("Kshetra planning deletes data before resume filtering") — and the
    test asserts the detectors report FAILURE. A detector that has never
    reported false is not a detector (F28).

    Reverted automatically by monkeypatch; nothing is committed.
    """
    import psycopg

    import services.ka_kshetra.stage0_kinematics as stage0
    from pipeline.orchestrator.writers import SubStep

    def mutating_planner(ctx):
        with ctx.db_conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_field_kinematics WHERE chart_id = %s",
                (ctx.config["chart_id"],),
            )
        return [SubStep(key="stage0:Sun", label="kinematics Sun")]

    # A sentinel row so D3 has real content to lose.
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_field_kinematics"
            " (chart_id, event_kind, body, t_days, event_ts, ayanamsha_id)"
            " VALUES (%s,'station','Sun',1.0, now(),'lahiri')",
            (CANONICAL_CHART_ID,),
        )
    before = content_digest(conn, _watched())
    assert before["kala_field_kinematics"][0] == 1
    conn.commit()  # commit the sentinel so the detectors start from a clean xid

    assert xid(conn) is None
    monkeypatch.setattr(stage0, "plan_substeps", mutating_planner)

    writer.plan_substeps(make_ctx(conn, ASSET))

    # D1 fires.
    assert xid(conn) is not None, "D1 is vacuous: a real DELETE assigned no xid"
    # D3 fires.
    after = content_digest(conn, _watched())
    assert after != before, "D3 is vacuous: a real DELETE changed no digest"
    assert after["kala_field_kinematics"][0] == 0

    conn.rollback()

    # D2 fires: the same planted planner under a READ ONLY transaction RAISES.
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        writer.plan_substeps(make_ctx(conn, ASSET))

    conn.rollback()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM kala_field_kinematics WHERE chart_id = %s",
            (CANONICAL_CHART_ID,),
        )
    conn.commit()


# ── crash / resume, and restore-prior-data ───────────────────────────────────

def test_resume_planning_filters_completed_substeps_and_preserves_committed_rows(
    conn, writer
):
    """The hazard's actual failure mode, exercised end to end.

    The original defect was ordering: planning deleted, THEN filtered for
    resume — so a resumed build destroyed the work it was resuming. Here a
    first attempt commits `prepare:replace` plus a stage-0 receipt and a real
    committed row; then a SECOND writer instance re-plans on a fresh
    transaction, standing in for the crashed process.

    Asserts: (a) re-planning assigns no xid, (b) the committed row survives
    re-planning byte-for-byte, (c) the completed keys are filtered OUT of the
    resumed plan, and (d) the resumed plan is strictly bounded — smaller than
    the original.
    """
    from services.ka_kshetra.writer import KaKshetraWriter

    # ── attempt 1: plan, run prepare:replace, commit (as the orchestrator does)
    ctx = make_ctx(conn, ASSET)
    first_plan = writer.plan_substeps(ctx)
    n_first = len(first_plan)
    writer.run_substep(ctx, first_plan[0])          # prepare:replace
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_field_kinematics"
            " (chart_id, event_kind, body, t_days, event_ts, ayanamsha_id)"
            " VALUES (%s,'station','Sun',1.0,'2001-01-01T00:00:00Z','lahiri')",
            (CANONICAL_CHART_ID,),
        )
    writer._record_substep(conn, "stage0:Sun", 1)
    conn.commit()

    committed = content_digest(conn, ["kala_field_kinematics"])
    assert committed["kala_field_kinematics"][0] == 1

    try:
        # ── the crash: a brand-new writer object on a brand-new transaction
        resumed_writer = KaKshetraWriter()
        assert xid(conn) is None
        resumed_plan = resumed_writer.plan_substeps(make_ctx(conn, ASSET))

        assert xid(conn) is None, (
            "RESUME HAZARD: re-planning wrote. This is the P0 defect — planning "
            "mutating before resume filtering."
        )
        assert content_digest(conn, ["kala_field_kinematics"]) == committed, (
            "RESUME HAZARD: re-planning destroyed a committed row"
        )
        keys = {s.key for s in resumed_plan}
        assert "prepare:replace" not in keys, "resume re-ran replacement"
        assert "stage0:Sun" not in keys, "resume re-ran a completed substep"
        assert len(resumed_plan) < n_first, "resumed plan is not bounded"
        assert len(resumed_plan) == n_first - 2
    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_field_kinematics WHERE chart_id = %s",
                (CANONICAL_CHART_ID,),
            )
            cur.execute(
                "DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = %s",
                (CANONICAL_CHART_ID, ASSET),
            )
        conn.commit()


def test_prepare_replace_fails_closed_on_a_populated_slice_without_deleting(conn, writer):
    """Restore-prior-data, positive form: a populated chart is HELD, not wiped.

    `_run_prepare_replace` raises `KshetraReplacementHeld` rather than deleting
    when any writer-owned table already has rows (DP-SD-017 W0: no immutable
    generation schema yet). This is the guarantee "restore prior data" rests on
    — the prior data is never removed in the first place.
    """
    from services.ka_kshetra.writer import KshetraReplacementHeld

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_field_kinematics"
            " (chart_id, event_kind, body, t_days, event_ts, ayanamsha_id)"
            " VALUES (%s,'station','Mars',2.0,'2002-02-02T00:00:00Z','lahiri')",
            (CANONICAL_CHART_ID,),
        )
    conn.commit()
    prior = content_digest(conn, _watched())

    try:
        ctx = make_ctx(conn, ASSET)
        plan = writer.plan_substeps(ctx)
        assert plan[0].key == "prepare:replace"
        with pytest.raises(KshetraReplacementHeld):
            writer.run_substep(ctx, plan[0])
        conn.rollback()
        assert content_digest(conn, _watched()) == prior, (
            "prior data was not restored after the held replacement"
        )
    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_field_kinematics WHERE chart_id = %s",
                (CANONICAL_CHART_ID,),
            )
        conn.commit()
