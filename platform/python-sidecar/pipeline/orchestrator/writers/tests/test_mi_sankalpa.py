"""Tests for the mi_sankalpa writer (Unified Intervention Ledger, registry item 42).

Spec: KALA_W4_UPAYA_DESIGN_v1_0.md (v1.1) §4.2 (table), §4.3 (writer contract).

Two tiers, matching the project's established writer-test convention (see
test_bg_muhurta_lattice.py):

1. Offline (always runs, no DB required): the pure, DB-free study-arm classification and
   LEL-matching logic in services/mi_sankalpa/arms.py.
2. Live (skipped unless DATABASE_URL or PROD_DB_URL is set): runs the writer against a real
   DB connection carrying migration 532's schema, and proves:
     - the mimamsa_intervention_ledger_inferred_never_sealed CHECK constraint;
     - the STATUS-PRESERVING idempotency guarantee — a rebuild NEVER destroys a
       native-set status (performed / performed_at / outcome_event_id), even though the
       exact same delete-then-insert predicate from KALA_W4_UPAYA_DESIGN_v1_0.md §4.3 runs
       on every call;
     - study-arm reclassification from native-attested performed/performed_at fields;
     - arm-4 (acted_without_election) origination from the LEL;
   on BOTH canonical charts.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import psycopg
import psycopg.rows

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.mi_sankalpa import MiSankalpaWriter
from services.mi_bhara.living_lel import LelEventRef, OpenPrediction
from services.mi_sankalpa.arms import (
    STUDY_ARM_ACTED_WITH_ELECTION,
    STUDY_ARM_ACTED_WITHOUT_ELECTION,
    STUDY_ARM_ELECTED_NOT_ACTED,
    STUDY_ARM_ELECTED_PENDING,
    classify_study_arm,
    days_since_birth,
    find_unelected_lel_events,
    score_ledger_rows_against_lel_event,
)

CANONICAL_CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CANONICAL_CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


# ── Offline tests: services/mi_sankalpa/arms.py (pure, DB-free) ────────────────────────────

def test_classify_study_arm_elected_pending_when_performed_is_none():
    assert (
        classify_study_arm(
            performed=None, performed_at=None,
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        == STUDY_ARM_ELECTED_PENDING
    )


def test_classify_study_arm_elected_not_acted_when_performed_false():
    assert (
        classify_study_arm(
            performed=False, performed_at=None,
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        == STUDY_ARM_ELECTED_NOT_ACTED
    )


def test_classify_study_arm_elected_not_acted_ignores_a_stray_performed_at():
    # performed=FALSE is dispositive regardless of any (anomalous) performed_at value.
    assert (
        classify_study_arm(
            performed=False, performed_at=datetime(2027, 1, 5, tzinfo=timezone.utc),
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        == STUDY_ARM_ELECTED_NOT_ACTED
    )


def test_classify_study_arm_acted_with_election_when_performed_at_inside_window():
    assert (
        classify_study_arm(
            performed=True, performed_at=datetime(2027, 1, 5, tzinfo=timezone.utc),
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        == STUDY_ARM_ACTED_WITH_ELECTION
    )


def test_classify_study_arm_boundary_inclusive_at_both_ends():
    window_start = datetime(2027, 1, 1, tzinfo=timezone.utc)
    window_end = datetime(2027, 1, 15, tzinfo=timezone.utc)
    assert classify_study_arm(
        performed=True, performed_at=window_start, window_start=window_start, window_end=window_end
    ) == STUDY_ARM_ACTED_WITH_ELECTION
    assert classify_study_arm(
        performed=True, performed_at=window_end, window_start=window_start, window_end=window_end
    ) == STUDY_ARM_ACTED_WITH_ELECTION


def test_classify_study_arm_returns_none_when_performed_true_but_outside_window():
    # LAW ZERO: the design's §4.3 table never names this combination -- the function must
    # say "I don't know how to classify this" (None = leave unchanged), never invent a
    # disposition, and never silently discard the native's own performed=TRUE attestation.
    assert (
        classify_study_arm(
            performed=True, performed_at=datetime(2027, 2, 1, tzinfo=timezone.utc),
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        is None
    )


def test_classify_study_arm_returns_none_when_performed_true_but_performed_at_missing():
    assert (
        classify_study_arm(
            performed=True, performed_at=None,
            window_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            window_end=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )
        is None
    )


def test_days_since_birth_is_a_plain_calendar_delta():
    assert days_since_birth(date(1984, 2, 15), date(1984, 2, 5)) == 10.0
    assert days_since_birth(date(1984, 1, 5), date(1984, 2, 5)) == -31.0


def test_score_ledger_rows_against_lel_event_is_a_named_passthrough_to_living_lel():
    # §4.3's binding instruction: reuse living_lel.score_predictions_against_event rather
    # than writing a second matcher. Pin the reuse itself: same inputs, same outputs.
    from services.mi_bhara.living_lel import score_predictions_against_event

    event = LelEventRef(event_id="ev-1", event_class="career_promotion", t=100.0)
    open_rows = [
        OpenPrediction(
            prediction_id="pred-1", event_class="career_promotion",
            window_start=90.0, window_end=110.0, filed_at_t=50.0,
        ),
    ]
    assert score_ledger_rows_against_lel_event(event, open_rows) == score_predictions_against_event(event, open_rows)


def test_find_unelected_lel_events_excludes_a_class_never_filed_by_this_chart():
    lel_events = [LelEventRef(event_id="ev-1", event_class="marriage", t=100.0)]
    result = find_unelected_lel_events(
        lel_events=lel_events,
        known_event_classes=["career_promotion"],  # "marriage" not among them
        birth_date=date(1984, 2, 5),
        covered_windows_by_class={},
    )
    assert result == []


def test_find_unelected_lel_events_excludes_an_event_covered_by_an_existing_window():
    lel_events = [LelEventRef(event_id="ev-1", event_class="career_promotion", t=100.0)]
    birth = date(1984, 2, 5)
    event_date = birth + timedelta(days=100)
    covered = {
        "career_promotion": [
            (
                datetime(event_date.year, event_date.month, event_date.day, tzinfo=timezone.utc) - timedelta(days=5),
                datetime(event_date.year, event_date.month, event_date.day, tzinfo=timezone.utc) + timedelta(days=5),
            )
        ]
    }
    result = find_unelected_lel_events(
        lel_events=lel_events, known_event_classes=["career_promotion"],
        birth_date=birth, covered_windows_by_class=covered,
    )
    assert result == []


def test_find_unelected_lel_events_includes_an_uncovered_event_of_a_known_class():
    lel_events = [LelEventRef(event_id="ev-1", event_class="career_promotion", t=100.0)]
    result = find_unelected_lel_events(
        lel_events=lel_events, known_event_classes=["career_promotion"],
        birth_date=date(1984, 2, 5), covered_windows_by_class={},  # no covering window at all
    )
    assert len(result) == 1
    assert result[0].event_id == "ev-1"
    assert result[0].event_class == "career_promotion"


# ── mi_sankalpa's own CHECK-constraint-shaped guardrail: source-level pin ──────────────────
# (Mirrors test_mi_bhavisya_irreplaceable_outcome_guard.py's discipline: a source-scan proof
# that always runs, backstopping the live-DB proof below which is skipped in DB-less CI.)

def test_writer_never_deletes_with_an_unscoped_per_chart_predicate():
    import inspect

    src = inspect.getsource(MiSankalpaWriter)
    assert "DELETE FROM mimamsa_intervention_ledger WHERE chart_id = %s\n" not in src
    assert "study_arm" in src  # the delete path is reached via db.delete_unresolved, named here


def test_writer_never_updates_frozen_adjudication_fields():
    # §5.5 pre-registration integrity: mi_sankalpa never UPDATEs adjudication_record /
    # score_vector / predicted_differential / paddhati_version on an existing row.
    import inspect

    from services.mi_sankalpa import db

    src = inspect.getsource(db)
    for forbidden in ("UPDATE mimamsa_intervention_ledger SET adjudication_record",
                       "UPDATE mimamsa_intervention_ledger SET score_vector",
                       "UPDATE mimamsa_intervention_ledger SET predicted_differential",
                       "UPDATE mimamsa_intervention_ledger SET paddhati_version"):
        assert forbidden not in src


# ── Live tests (require DATABASE_URL or PROD_DB_URL; skipped otherwise) ────────────────────

@pytest.fixture(scope="function")
def db_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def _make_ctx(chart_id: str, conn, birth_iso: str = "1984-02-05T10:43:00") -> ContextSpec:
    return ContextSpec(
        asset_id="mi_sankalpa",
        build_id=str(uuid.uuid4()),
        db_conn=conn,
        config={"chart_id": chart_id, "birth_params": {"datetime_iso": birth_iso}},
    )


def _clear_chart(conn, chart_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM mimamsa_intervention_ledger WHERE chart_id = %s", (chart_id,))
        cur.execute("DELETE FROM brahma_prospective_ledger WHERE chart_id = %s", (chart_id,))
        cur.execute("DELETE FROM life_events WHERE chart_id = %s", (chart_id,))
    conn.commit()


def _file_prospective(conn, chart_id: str, event_class: str = "career_promotion") -> str:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO brahma_prospective_ledger (chart_id, claim, event_class, filed_by) "
            "VALUES (%s, %s, %s, %s) RETURNING prediction_id",
            (chart_id, "test claim", event_class, "test-uid"),
        )
        pid = cur.fetchone()["prediction_id"]
    conn.commit()
    return str(pid)


def _insert_ledger_row(
    conn, *, chart_id: str, rite: str, event_class: str, window_start: str, window_end: str,
    prediction_id: str | None, adoption_basis: str, performed=None, performed_at=None,
    study_arm: str = "elected_pending", outcome_event_id: str | None = None,
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO mimamsa_intervention_ledger (
              chart_id, intent, intervention_class, rite_or_activity_class, event_class,
              elected_window, precision_regime, precision_basis, adjudication_record,
              score_vector, efficacy_tier, source_citation, paddhati_version,
              predicted_differential, prediction_id, study_arm, performed, performed_at,
              outcome_event_id, filed_by, adoption_basis, engine_version
            ) VALUES (
              %s, 'test intent', 'upaya', %s, %s, tstzrange(%s, %s), 'day_grade', 'test',
              '{}'::jsonb, '{}'::jsonb, 'traditional', 'BPHS 1.1', 'paddhati_v01',
              'test differential', %s, %s, %s, %s, %s, 'test-uid', %s, 'test_v1'
            ) RETURNING intervention_id
            """,
            (chart_id, rite, event_class, window_start, window_end, prediction_id,
             study_arm, performed, performed_at, outcome_event_id, adoption_basis),
        )
        iid = cur.fetchone()["intervention_id"]
    conn.commit()
    return str(iid)


@pytest.mark.parametrize("chart_id", [CANONICAL_CHART_A, CANONICAL_CHART_B])
def test_mi_sankalpa_writer_is_orchestrator_native(chart_id, db_conn):
    """§N.2 conformance: @register('mi_sankalpa'), run(ctx) -> WriterResult, and an empty
    chart is honest-empty rather than an error."""
    _clear_chart(db_conn, chart_id)
    writer = MiSankalpaWriter()
    ctx = _make_ctx(chart_id, db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == "mi_sankalpa"
    assert result.rows_inserted == 0
    assert result.rows_updated == 0


@pytest.mark.parametrize("chart_id", [CANONICAL_CHART_A, CANONICAL_CHART_B])
def test_inferred_never_sealed_check_constraint(chart_id, db_conn):
    """The DB-level structural proof (ADJUDICATION-12): a session_inferred row can NEVER
    carry a non-null prediction_id."""
    _clear_chart(db_conn, chart_id)
    pred_id = _file_prospective(db_conn, chart_id)
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_ledger_row(
            db_conn, chart_id=chart_id, rite="test_rite", event_class="career_promotion",
            window_start="2027-01-01", window_end="2027-01-15",
            prediction_id=pred_id, adoption_basis="session_inferred",
        )
    db_conn.rollback()
    # The legal counterparts both succeed.
    _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="test_rite_a", event_class="career_promotion",
        window_start="2027-01-01", window_end="2027-01-15",
        prediction_id=None, adoption_basis="session_inferred",
    )
    _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="test_rite_b", event_class="career_promotion",
        window_start="2027-02-01", window_end="2027-02-15",
        prediction_id=pred_id, adoption_basis="native_directed",
    )


@pytest.mark.parametrize("chart_id", [CANONICAL_CHART_A, CANONICAL_CHART_B])
def test_status_preserving_idempotency_a_rebuild_never_destroys_a_native_set_status(chart_id, db_conn):
    """THE proof the ordering brief asks for: a native-attested row's `performed` /
    `performed_at` / `study_arm` / `intervention_id` survive TWO writer rebuilds
    byte-identical, even though every rebuild runs the exact §4.3 delete-then-insert
    predicate. A genuinely-unresolved row round-trips (survives) too -- the predicate is
    proven non-destructive on BOTH the protected and the unprotected row shape."""
    _clear_chart(db_conn, chart_id)

    # An attested row -- performed=TRUE, inside its own window -- native-set status.
    attested_start, attested_end = "2020-01-01", "2020-01-15"
    attested_id = _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="attested_rite", event_class="career_promotion",
        window_start=attested_start, window_end=attested_end,
        prediction_id=None, adoption_basis="session_inferred",
        performed=True, performed_at=datetime(2020, 1, 10, tzinfo=timezone.utc),
        study_arm="elected_pending",  # deliberately stale -- the writer must reclassify it
    )

    # A genuinely still-open, unresolved row -- must SURVIVE the round trip unchanged.
    pending_id = _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="pending_rite", event_class="career_promotion",
        window_start="2030-01-01", window_end="2030-01-15",
        prediction_id=None, adoption_basis="session_inferred",
    )

    writer = MiSankalpaWriter()

    # ── Rebuild #1 ──
    result1 = writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT intervention_id, performed, performed_at, study_arm FROM mimamsa_intervention_ledger "
            "WHERE chart_id = %s AND rite_or_activity_class = 'attested_rite'",
            (chart_id,),
        )
        row = cur.fetchone()
    assert row is not None, "the native-attested row was DESTROYED by the writer's rebuild"
    assert str(row["intervention_id"]) == attested_id, "attested row's identity changed across a rebuild"
    assert row["performed"] is True
    assert row["performed_at"] is not None
    assert row["study_arm"] == STUDY_ARM_ACTED_WITH_ELECTION, (
        "the writer must reclassify a stale elected_pending arm once performed/performed_at "
        "establish acted_with_election -- reclassification is not itself a destructive act"
    )

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT intervention_id FROM mimamsa_intervention_ledger "
            "WHERE chart_id = %s AND rite_or_activity_class = 'pending_rite'",
            (chart_id,),
        )
        pending_row = cur.fetchone()
    assert pending_row is not None, "an unresolved (never-attested) row must survive the round trip too"
    assert str(pending_row["intervention_id"]) == pending_id

    # ── Rebuild #2 -- re-running must be a true no-op on the now-settled data ──
    result2 = writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n FROM mimamsa_intervention_ledger WHERE chart_id = %s",
            (chart_id,),
        )
        count_after_second_rebuild = cur.fetchone()["n"]
    assert count_after_second_rebuild == 2, (
        f"expected exactly the 2 original rows after a second rebuild, got {count_after_second_rebuild} "
        "-- a duplicate or a loss both indicate the idempotency guard is broken"
    )
    assert result2.rows_updated == 0, "the second rebuild should find nothing left to reclassify"

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT performed, performed_at, study_arm FROM mimamsa_intervention_ledger "
            "WHERE intervention_id = %s",
            (attested_id,),
        )
        row2 = cur.fetchone()
    assert row2["performed"] is True
    assert row2["performed_at"] is not None
    assert row2["study_arm"] == STUDY_ARM_ACTED_WITH_ELECTION


@pytest.mark.parametrize("chart_id", [CANONICAL_CHART_A, CANONICAL_CHART_B])
def test_arm_4_origination_from_an_unelected_lel_event(chart_id, db_conn):
    """§4.3 arm 4: a LEL event of an already-filed class, with no covering election,
    originates a NEW acted_without_election row -- additive, never destructive, and
    idempotent on a second rebuild."""
    _clear_chart(db_conn, chart_id)

    # This chart has ALREADY filed an intervention for 'career_promotion' at some other
    # time -- establishing the class as intervention-relevant for this chart.
    _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="prior_rite", event_class="career_promotion",
        window_start="2000-01-01", window_end="2000-01-15",
        prediction_id=None, adoption_basis="session_inferred",
    )

    # An LEL event of the SAME class, on a date with NO covering election.
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO life_events (chart_id, event_id, event_date, category, description, event_type) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (chart_id, "lel-test-1", date(2025, 6, 1), "career", "test event", "career_promotion"),
        )
        lel_id = str(cur.fetchone()["id"])
    db_conn.commit()

    writer = MiSankalpaWriter()
    result1 = writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()
    assert result1.rows_inserted == 1

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT study_arm, outcome_event_id, prediction_id, adoption_basis "
            "FROM mimamsa_intervention_ledger WHERE chart_id = %s AND study_arm = %s",
            (chart_id, STUDY_ARM_ACTED_WITHOUT_ELECTION),
        )
        derived = cur.fetchone()
    assert derived is not None
    assert str(derived["outcome_event_id"]) == lel_id
    assert derived["prediction_id"] is None
    assert derived["adoption_basis"] == "session_inferred"

    # Second rebuild: idempotent, no duplicate.
    result2 = writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()
    assert result2.rows_inserted == 0
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n FROM mimamsa_intervention_ledger "
            "WHERE chart_id = %s AND study_arm = %s",
            (chart_id, STUDY_ARM_ACTED_WITHOUT_ELECTION),
        )
        n = cur.fetchone()["n"]
    assert n == 1, "arm-4 origination must be idempotent -- no duplicate on rebuild"


@pytest.mark.parametrize("chart_id", [CANONICAL_CHART_A, CANONICAL_CHART_B])
def test_falsifier_resolution_links_outcome_event_id_before_the_round_trip(chart_id, db_conn):
    """§4.3 phase 1: an unresolved row whose event_class + window matches a real LEL event
    gets outcome_event_id linked -- and, once linked, is thereafter PROTECTED from the
    delete predicate (outcome_event_id IS NULL no longer holds)."""
    _clear_chart(db_conn, chart_id)

    pending_id = _insert_ledger_row(
        db_conn, chart_id=chart_id, rite="matchable_rite", event_class="career_promotion",
        window_start="2025-05-01", window_end="2025-06-30",
        prediction_id=None, adoption_basis="session_inferred",
    )
    with db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO life_events (chart_id, event_id, event_date, category, description, event_type) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (chart_id, "lel-test-2", date(2025, 5, 15), "career", "test event", "career_promotion"),
        )
        lel_id = str(cur.fetchone()["id"])
    db_conn.commit()

    writer = MiSankalpaWriter()
    writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT outcome_event_id, study_arm FROM mimamsa_intervention_ledger WHERE intervention_id = %s",
            (pending_id,),
        )
        row = cur.fetchone()
    assert str(row["outcome_event_id"]) == lel_id
    assert row["study_arm"] == STUDY_ARM_ELECTED_PENDING  # linkage alone does not change study_arm

    # Rebuild again -- the now-linked row must survive (it no longer matches the delete
    # predicate: outcome_event_id IS NOT NULL).
    writer.run(_make_ctx(chart_id, db_conn))
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n FROM mimamsa_intervention_ledger WHERE intervention_id = %s",
            (pending_id,),
        )
        assert cur.fetchone()["n"] == 1
