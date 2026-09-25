"""BHAV-P0: `ka_bhavishya_lekha` preserves outcomes across an EMPTY rebuild.

`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §5 row P0, second hazard:

    "Bhavishya's empty-input early return follows deletion but precedes its
     outcome-preservation guard."
    Required: "preserve outcome identity independently of rebuildable
     projection, including empty results."
    Exit evidence: "Zero planning/dry-run mutations; crash/resume and
     empty-generation tests; restore prior data/outcomes."

`tests/l3/test_bhavishya_p0_safety.py` already covers this shape against a
hand-written `_StrictConnection` fake. A fake cannot catch a CHECK/FK/trigger
disagreement, and it is not what the strategy asks for. THIS module runs the
real `KaBhavishyaLekhaWriter.run(ctx)` against a live Postgres carrying
production's schema AND its trigger layer, and MEASURES the outcome columns.

`outcome_recorded` / `outcome_notes` are the only columns in `kala_bhavishya` a
writer cannot regenerate — they record what happened, not what was derived
(L3-U10 / F17 / F19: "candidate regeneration does not reset a delivered
forecast"; "empty rebuild preserves observations").
"""
from __future__ import annotations

import datetime as _dt
import uuid

import pytest

from tests.l3._p0_harness import (
    CANONICAL_CHART_ID,
    connect,
    content_digest,
    make_ctx,
    xact_tuple_counters,
    xid,
)

ASSET = "ka_bhavishya_lekha"
WATCHED = ["kala_bhavishya", "kala_darshana", "kala_convergence", "phala_anchors"]

SIGNAL_ID = "11111111-1111-4111-8111-111111111111"
SIGNAL_ID_2 = "22222222-2222-4222-8222-222222222222"
CONVERGENCE_ID_2 = 900000002
CONVERGENCE_ID = 900000001   # kala_convergence.convergence_id is bigint
PEAK_DATE = _dt.date.today() + _dt.timedelta(days=365)


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def conn():
    c = connect()
    _reset(c)
    yield c
    c.rollback()
    _reset(c)
    c.close()


@pytest.fixture
def writer():
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import KaBhavishyaLekhaWriter

    return KaBhavishyaLekhaWriter()


def _reset(conn):
    with conn.cursor() as cur:
        for table in ("phala_anchors", "kala_bhavishya", "kala_darshana", "kala_convergence"):
            cur.execute(f"DELETE FROM {table} WHERE chart_id = %s", (CANONICAL_CHART_ID,))
    conn.commit()


def _seed_second_candidate(conn):
    """A SECOND, previously-unseen candidate identity — the writer must INSERT it.

    Needed by the crash/resume test: rolling back a run that changed nothing
    would prove nothing about restore.
    """
    _seed_signal(conn, signal_id=SIGNAL_ID_2)
    peak = PEAK_DATE + _dt.timedelta(days=30)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kala_convergence (convergence_id, chart_id, signal_id,
                window_start, window_end, convergence_score, source_citation,
                confidence_label, rarity_years, mode, tier_basis, horizon_tier,
                computed_at)
            VALUES (%s,%s,%s,%s,%s,0.60,'harness','moderate',8.0,'A',
                    'relative_uncalibrated','near', now())
            ON CONFLICT (convergence_id) DO NOTHING
            """,
            (CONVERGENCE_ID_2, CANONICAL_CHART_ID, SIGNAL_ID_2,
             peak - _dt.timedelta(days=14), peak + _dt.timedelta(days=14)),
        )
        cur.execute(
            """
            INSERT INTO kala_darshana (chart_id, convergence_id, signal_id,
                net_label, effective_score, peak_date, window_start, window_end,
                narrative, obstruction_summary, source_citation)
            VALUES (%s,%s,%s,'auspicious_moderate',0.60,%s,%s,%s,
                    '"candidate2"'::jsonb,'"none"'::jsonb,'harness')
            """,
            (CANONICAL_CHART_ID, CONVERGENCE_ID_2, SIGNAL_ID_2, peak,
             peak - _dt.timedelta(days=14), peak + _dt.timedelta(days=14)),
        )
    conn.commit()


def _seed_signal(conn, signal_id=SIGNAL_ID):
    """One MSR signal for the FK. `bodha_msr_signals` carries production's
    `l2_data_plane_mutation_guard`, which refuses any write not authenticated as
    `data_plane_builder` inside an admitted L2 generation. The guard is
    suspended for THIS SEED ONLY and restored immediately; it is live for every
    writer call the tests make (these writers only ever READ that table).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM bodha_msr_signals WHERE signal_id = %s", (signal_id,))
        if cur.fetchone():
            return
        cur.execute("ALTER TABLE bodha_msr_signals DISABLE TRIGGER USER")
        cur.execute(
            """
            INSERT INTO bodha_msr_signals (
                signal_id, chart_id, ayanamsha_id, build_id, signal_type_id,
                signal_type_class, signal_tradition, fact_kind, source_l1_asset,
                source_subsystem, configuration_jsonb, constituent_facts_array,
                deterministic_strength, verification_certainty, computed_salience,
                salience_formula_version, domains_affected_array, domain_salience_jsonb,
                active_duration_class, verification_pass_status, citation_ref,
                citation_human, computed_at, engine_version, producer_asset_id)
            VALUES (%s, %s, 'lahiri', %s, 'raja_yoga_p0', 'yoga', 'parashari',
                    'derived', 'ga_structural', 'p0_harness', '{}'::jsonb,
                    ARRAY[]::text[], 0.5, 0.5, 0.5, 'v1', ARRAY['career']::text[],
                    '{}'::jsonb, 'long', 'single', 'harness', 'harness', now(),
                    'p0-harness', 'bo_laksana')
            """,
            (signal_id, CANONICAL_CHART_ID, str(uuid.uuid4())),
        )
        cur.execute("ALTER TABLE bodha_msr_signals ENABLE TRIGGER USER")
    conn.commit()


def _seed_candidate(conn):
    """A future darshana window + its convergence — i.e. NON-empty input."""
    _seed_signal(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kala_convergence (convergence_id, chart_id, signal_id,
                window_start, window_end, convergence_score, source_citation,
                confidence_label, rarity_years, mode, tier_basis, horizon_tier,
                computed_at)
            VALUES (%s,%s,%s,%s,%s,0.78,'harness','high',12.0,'A',
                    'relative_uncalibrated','near', now())
            ON CONFLICT (convergence_id) DO NOTHING
            """,
            (CONVERGENCE_ID, CANONICAL_CHART_ID, SIGNAL_ID,
             PEAK_DATE - _dt.timedelta(days=14), PEAK_DATE + _dt.timedelta(days=14)),
        )
        cur.execute(
            """
            INSERT INTO kala_darshana (chart_id, convergence_id, signal_id,
                net_label, effective_score, peak_date, window_start, window_end,
                narrative, obstruction_summary, source_citation)
            VALUES (%s,%s,%s,'auspicious_strong',0.78,%s,%s,%s,
                    '"candidate"'::jsonb,'"none"'::jsonb,'harness')
            """,
            (CANONICAL_CHART_ID, CONVERGENCE_ID, SIGNAL_ID, PEAK_DATE,
             PEAK_DATE - _dt.timedelta(days=14), PEAK_DATE + _dt.timedelta(days=14)),
        )
    conn.commit()


def _exact_writer_claim():
    """The claim content the writer itself would compute for the seeded candidate.

    Built from the writer's OWN helpers rather than hand-typed, so a seeded
    "existing" row is byte-identical to a regenerated one. That is what makes
    the matched-identity path exercise UPDATE/skip rather than the writer's
    protected-claim refusal — and it means a change to those helpers surfaces
    here instead of being masked by a stale literal.
    """
    import json

    from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
        _assign_tier,
        _build_falsifiability,
        _build_projection_narrative,
    )

    tier = _assign_tier(0.78, "auspicious_strong")
    domain = "career"
    return {
        "probability_tier": tier,
        "domain": domain,
        "falsifiability": json.dumps(
            _build_falsifiability(tier, domain, PEAK_DATE, 0.78)
        ),
        "source_chain": json.dumps(
            [{"convergence_id": CONVERGENCE_ID, "mode": "A", "confidence": "high"}]
        ),
        "narrative": json.dumps(
            _build_projection_narrative(
                tier=tier, domain=domain, peak_date=PEAK_DATE, eff_score=0.78,
                conf_label="high", rarity=12.0, net_label="auspicious_strong",
                tier_basis="relative_uncalibrated",
            )
        ),
    }


def _seed_existing_projection(conn, *, outcome_recorded, outcome_notes,
                              with_convergence=True, exact_claim=False):
    _seed_signal(conn)
    with conn.cursor() as cur:
        if with_convergence:
            cur.execute("SELECT 1 FROM kala_convergence WHERE convergence_id = %s",
                        (CONVERGENCE_ID,))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO kala_convergence (convergence_id, chart_id, signal_id,
                        window_start, window_end, convergence_score, source_citation,
                        confidence_label, rarity_years, mode, tier_basis, horizon_tier,
                        computed_at)
                    VALUES (%s,%s,%s,%s,%s,0.78,'harness','high',12.0,'A',
                            'relative_uncalibrated','near', now())
                    """,
                    (CONVERGENCE_ID, CANONICAL_CHART_ID, SIGNAL_ID,
                     PEAK_DATE - _dt.timedelta(days=14), PEAK_DATE + _dt.timedelta(days=14)),
                )
        claim = _exact_writer_claim() if exact_claim else {
            "probability_tier": "tier_1_high", "domain": "career",
            "falsifiability": "{}", "source_chain": "[]", "narrative": "{}",
        }
        cur.execute(
            """
            INSERT INTO kala_bhavishya (chart_id, projection_rank, probability_tier,
                domain, peak_date, window_start, window_end, convergence_id, signal_id,
                effective_score, falsifiability, source_chain, narrative,
                outcome_recorded, outcome_notes, source_citation)
            VALUES (%s,1,%s,%s,%s,%s,%s,%s,%s,0.78,
                    %s::jsonb,%s::jsonb,%s::jsonb,%s,%s,
                    'ka_bhavishya_lekha:v1.0:rank=1')
            RETURNING id
            """,
            (CANONICAL_CHART_ID, claim["probability_tier"], claim["domain"], PEAK_DATE,
             PEAK_DATE - _dt.timedelta(days=14), PEAK_DATE + _dt.timedelta(days=14),
             CONVERGENCE_ID if with_convergence else None, SIGNAL_ID,
             claim["falsifiability"], claim["source_chain"], claim["narrative"],
             outcome_recorded, outcome_notes),
        )
        row_id = cur.fetchone()["id"]
    conn.commit()
    return row_id


def _outcomes(conn):
    """THE detector: the non-regenerable observation columns, by row id."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, signal_id, peak_date, outcome_recorded, outcome_notes"
            "  FROM kala_bhavishya WHERE chart_id = %s ORDER BY id",
            (CANONICAL_CHART_ID,),
        )
        return {r["id"]: (bool(r["outcome_recorded"]), r["outcome_notes"]) for r in cur.fetchall()}


def _assert_outcomes_preserved(before, after):
    """Shared assertion used by BOTH the positive tests and the F28 negative
    fixture, so the negative fixture proves THIS function can report false."""
    missing = {k: v for k, v in before.items() if v != (False, None) and k not in after}
    assert not missing, (
        f"OUTCOME LOSS: recorded observation(s) destroyed by the rebuild: {missing}"
    )
    for row_id, value in before.items():
        if value == (False, None):
            continue
        assert after[row_id] == value, (
            f"OUTCOME DRIFT: row {row_id} outcome {value!r} became {after[row_id]!r}"
        )


# ── empty generation, the headline case ──────────────────────────────────────

def test_empty_input_with_a_recorded_outcome_refuses_and_mutates_nothing(conn, writer):
    """Empty candidate plan + retained outcome ⇒ refuse, and write NOTHING.

    The original hazard deleted first and returned early on empty input, so the
    recorded outcome was gone before the preservation guard could see it. The
    repaired writer reads and validates existing history BEFORE any DML.
    """
    row_id = _seed_existing_projection(
        conn, outcome_recorded=True, outcome_notes="observed: promotion 2027-02"
    )
    before = _outcomes(conn)
    digest_before = content_digest(conn, WATCHED)
    counters_before = xact_tuple_counters(conn, WATCHED)
    assert before[row_id] == (True, "observed: promotion 2027-02")

    with pytest.raises(RuntimeError) as exc:
        writer.run(make_ctx(conn, ASSET))

    assert "empty" in str(exc.value).lower()
    assert "no rows were mutated" in str(exc.value).lower()
    # NOTE the instrument. This writer deliberately takes `SELECT ... FOR UPDATE`
    # on the chart's existing projections BEFORE deciding, and a row lock assigns
    # a transaction id without modifying a tuple (measured on the harness — see
    # `_p0_harness.xact_tuple_counters`). So `xid()` is NOT the detector here;
    # per-relation transaction tuple counters are.
    assert xact_tuple_counters(conn, WATCHED) == counters_before, (
        "MUTATION BEFORE REFUSAL: the empty-input path modified tuples before "
        "refusing — the P0 hazard."
    )
    assert content_digest(conn, WATCHED) == digest_before
    conn.rollback()
    _assert_outcomes_preserved(before, _outcomes(conn))
    assert content_digest(conn, WATCHED) == digest_before


def test_empty_input_with_no_existing_rows_is_an_honest_empty(conn, writer):
    """Nothing to rebuild and nothing to lose ⇒ honest empty, zero mutation."""
    assert xid(conn) is None
    counters_before = xact_tuple_counters(conn, WATCHED)
    result = writer.run(make_ctx(conn, ASSET))

    assert result.rows_inserted == 0
    assert "no future darshana windows" in result.notes.lower()
    assert xid(conn) is None, "the honest-empty path wrote (and took no row lock)"
    assert xact_tuple_counters(conn, WATCHED) == counters_before
    assert content_digest(conn, WATCHED)["kala_bhavishya"][0] == 0


def test_empty_input_with_unrecorded_rows_still_refuses_rather_than_silently_emptying(
    conn, writer
):
    """Even with NO recorded outcome, an empty plan against existing rows refuses.

    §N.8: reporting a successful empty rebuild while stale rows stay servable
    would be a green signal with no detector behind it.
    """
    _seed_existing_projection(conn, outcome_recorded=False, outcome_notes=None)
    digest_before = content_digest(conn, WATCHED)
    counters_before = xact_tuple_counters(conn, WATCHED)

    with pytest.raises(RuntimeError):
        writer.run(make_ctx(conn, ASSET))

    assert xact_tuple_counters(conn, WATCHED) == counters_before
    conn.rollback()
    assert content_digest(conn, WATCHED) == digest_before


# ── candidate regeneration must not reset a delivered forecast (L3-U10) ──────

def test_rebuild_with_matching_candidate_preserves_outcome_and_row_identity(conn, writer):
    """A normal, NON-empty rebuild carries the observation and the row id across.

    Row identity matters independently: `phala_anchors.bhavishya_id` is an
    ON DELETE SET NULL FK, so a delete/reinsert would sever accepted downstream
    provenance even inside a successful transaction.
    """
    row_id = _seed_existing_projection(
        conn, outcome_recorded=True, outcome_notes="observed: promotion 2027-02",
        exact_claim=True,
    )
    _seed_candidate(conn)
    before = _outcomes(conn)

    result = writer.run(make_ctx(conn, ASSET))
    conn.commit()

    after = _outcomes(conn)
    _assert_outcomes_preserved(before, after)
    assert row_id in after, "row identity was not preserved across the rebuild"
    assert after[row_id] == (True, "observed: promotion 2027-02")
    assert result.rows_inserted == 0, "a matched identity must UPDATE, never re-INSERT"
    assert result.rows_skipped == 1, (
        "the regenerated claim is identical, so the row must be left alone entirely"
    )


# ── F28: prove the detector can read false ───────────────────────────────────

def test_negative_fixture_legacy_delete_then_early_return_loses_the_outcome(conn):
    """Reconstruct the ORIGINAL hazard ordering and show the detector FIRES.

    `_LegacyOrderWriter.run` is the pre-repair shape the strategy describes:
    DELETE the chart's projections, then early-return on empty input — the
    outcome-preservation guard never runs. The SAME `_assert_outcomes_preserved`
    helper the positive tests use must report failure here. A test that has
    never failed is not a detector (F28).

    Nothing here is production code and nothing is committed.
    """
    from pipeline.orchestrator.writers import WriterResult

    class _LegacyOrderWriter:
        """Pre-repair ordering. Deliberately wrong; test-local only."""

        def run(self, ctx):
            conn = ctx.db_conn
            chart_id = ctx.config["chart_id"]
            with conn.cursor() as cur:                      # (1) DELETE first
                cur.execute("DELETE FROM kala_bhavishya WHERE chart_id = %s", (chart_id,))
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM kala_darshana WHERE chart_id = %s AND peak_date >= %s",
                    (chart_id, _dt.date.today()),
                )
                rows = cur.fetchall()
            if not rows:                                    # (2) early return
                return WriterResult(asset_id=ASSET, rows_inserted=0, notes="legacy empty")
            raise AssertionError("fixture expects the empty path")

    row_id = _seed_existing_projection(
        conn, outcome_recorded=True, outcome_notes="observed: promotion 2027-02"
    )
    before = _outcomes(conn)
    assert before[row_id] == (True, "observed: promotion 2027-02")

    result = _LegacyOrderWriter().run(make_ctx(conn, ASSET))
    assert result.rows_inserted == 0

    assert xid(conn) is not None, "the legacy path wrote nothing — fixture is wrong"
    after = _outcomes(conn)
    assert row_id not in after

    with pytest.raises(AssertionError, match="OUTCOME LOSS"):
        _assert_outcomes_preserved(before, after)

    conn.rollback()
    assert _outcomes(conn) == before, "rollback did not restore the prior outcomes"


# ── crash / resume + restore-prior-data ──────────────────────────────────────

def test_crash_mid_run_restores_prior_data_and_resume_is_bounded(conn, writer):
    """Interrupt the writer inside its substep; prove restore and bounded resume.

    `ka_bhavishya_lekha` is a LIGHT writer: the orchestrator gives it exactly
    ONE substep, wrapped in ONE savepoint. So the honest crash/resume statement
    is: a crash rolls the whole substep back, prior data and outcomes come back
    byte-identical, and the resumed work is bounded at that single substep — the
    writer does not accrete partial state a resume would have to reconcile.
    """
    row_id = _seed_existing_projection(
        conn, outcome_recorded=True, outcome_notes="observed: promotion 2027-02",
        exact_claim=True,
    )
    _seed_candidate(conn)
    _seed_second_candidate(conn)          # a genuinely NEW identity the run must INSERT
    before = _outcomes(conn)
    digest_before = content_digest(conn, WATCHED)
    assert digest_before["kala_bhavishya"][0] == 1

    ctx = make_ctx(conn, ASSET)
    plan = writer.plan_substeps(ctx)
    assert len(plan) == 1, (
        "resume bound: a light writer must expose exactly one substep, so a crash "
        f"replays exactly that unit; got {[s.key for s in plan]}"
    )

    with conn.cursor() as cur:
        cur.execute("SAVEPOINT substep")          # what asset_runner does per substep
    mid = writer.run(ctx)
    assert mid.rows_inserted == 1, "the run must have made a real change to restore from"
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM kala_bhavishya WHERE chart_id = %s",
                    (CANONICAL_CHART_ID,))
        assert cur.fetchone()["n"] == 2
    with conn.cursor() as cur:                    # the crash
        cur.execute("ROLLBACK TO SAVEPOINT substep")

    restored = content_digest(conn, WATCHED)
    assert restored == digest_before, (
        f"RESTORE FAILED: prior data was not restored by the substep rollback: "
        f"{digest_before} -> {restored}"
    )
    _assert_outcomes_preserved(before, _outcomes(conn))
    assert _outcomes(conn)[row_id] == (True, "observed: promotion 2027-02")
    conn.rollback()

    # and the resumed run succeeds, still preserving the observation
    resumed = writer.run(make_ctx(conn, ASSET))
    conn.commit()
    _assert_outcomes_preserved(before, _outcomes(conn))
    assert resumed.rows_inserted == 1, "the resumed run did not replay the lost work"
    assert resumed.rows_skipped == 1, "the resumed run rewrote an unchanged protected row"
    assert _outcomes(conn)[row_id] == (True, "observed: promotion 2027-02")


def test_dry_run_contract_is_absent_and_that_is_reported_not_assumed(conn, writer):
    """`ka_bhavishya_lekha.run()` does NOT branch on `ctx.dry_run`.

    The strategy's exit evidence says "zero planning/dry-run mutations".
    Planning for this LIGHT writer is the inherited default `plan_substeps`,
    which touches no DB at all — asserted here. `run()` itself has no dry-run
    branch: a dry-run invocation would write. That is a real, narrow gap and it
    is asserted as the CURRENT behaviour rather than papered over, so this test
    turns red the day someone adds the branch and the doc can be corrected.
    """
    ctx = make_ctx(conn, ASSET, dry_run=True)
    plan = writer.plan_substeps(ctx)
    assert len(plan) == 1
    assert xid(conn) is None, "planning for the light writer touched the database"

    import inspect

    src = inspect.getsource(type(writer).run)
    assert "dry_run" not in src, (
        "ka_bhavishya_lekha.run() has grown a dry-run branch — update "
        "PHASE0_2_P0_SAFETY_EVIDENCE.md §4, which records its absence."
    )
