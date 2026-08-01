"""Tests for `bg_class_lifetime_counts` — the N_e structural priors (ADJUDICATION-2).

Three tiers, matching this directory's convention (see `test_bg_cohort.py`):

1. SEED-MODULE tests (always run, no DB): the citation-completeness contract. Every
   seeded row carries all six Tier N-i citation elements, a raw figure, and a
   conversion string; every `prior_basis` is one of the two permitted values; no
   value is <= 0; no class is duplicated. Crucially these tests also prove the
   validator can FAIL — a validator that cannot produce a red is not a check
   (CLAUDE.md §N.8), so each rule is exercised against a deliberately-broken row.

2. WRITER tests (always run, no DB): the FROZEN-contract conformance surface —
   registration under the right asset_id, the reserved write coordinate, and the
   fact that the writer never commits `ctx.db_conn`, asserted against a fake
   connection that records every call.

3. LIVE tests (skipped unless DATABASE_URL is set): the real upsert, its idempotency,
   and the DB CHECK constraint actually rejecting an unsourced row.

ANTI-CIRCULARITY: nothing in this file, or in the module under test, reads the LEL.
"""
from __future__ import annotations

import os

import pytest

from brahmagyan import l0_class_lifetime_counts as m
from brahmagyan.l0_class_lifetime_counts import (
    FACT_KIND,
    LIFETIME_COUNT_ROWS,
    PRIOR_VERSION,
    VALID_PRIOR_BASES,
    LifetimeCountRow,
    compose_citation,
    compose_source_ref,
    validate_rows,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _good_row(**overrides) -> LifetimeCountRow:
    """A structurally-complete row, used ONLY to prove the validator can go red.

    Its numbers are deliberately nonsense placeholders and it is never written to
    any database — it exists to exercise failure paths, which is the opposite of
    seeding a placeholder.
    """
    base = dict(
        event_class_id="test_class",
        n_e_per_100y=1.0,
        prior_basis="demographic_structural",
        reference_population="Testland, cohort 1900-1901",
        publisher="Test Publisher",
        edition="Test Edition",
        edition_year="1900",
        indicator_id="Table T-1",
        source_url="https://example.invalid/t1",
        raw_figure="1.0 per person",
        inclusion_criteria="test only",
        conversion_arithmetic="1.0 = 1.0",
        ratified_by="test",
    )
    base.update(overrides)
    return LifetimeCountRow(**base)


# ══ 1. SEED-MODULE / CITATION-COMPLETENESS ═══════════════════════════════════

def test_prior_version_is_zero_padded():
    """ka_kshetra does `ORDER BY prior_version DESC` — a STRING sort. Unpadded
    `ne_v10` would sort BELOW `ne_v2`, silently pinning a stale revision.
    ADJUDICATION-2 item 4 calls the padding mandatory; this is the guard."""
    assert PRIOR_VERSION.startswith("ne_v")
    suffix = PRIOR_VERSION[len("ne_v"):]
    assert suffix.isdigit(), f"prior_version suffix must be numeric, got {suffix!r}"
    assert len(suffix) >= 2, (
        f"prior_version {PRIOR_VERSION!r} is not zero-padded to at least 2 digits — "
        "string-sorted version selection would break at ne_v10"
    )


def test_fact_kind_is_the_reserved_coordinate():
    """The coordinate is a contract with `ka_kshetra.load_class_lifetime_count`;
    a typo here writes rows nothing will ever read."""
    assert FACT_KIND == "lifetime_count_per_100y"


def test_shipped_rows_validate():
    validate_rows()


def test_every_shipped_row_has_all_six_citation_elements():
    """The Tier N-i contract, asserted field-by-field on the SHIPPED table.

    Six elements: publisher · edition/survey round · year · indicator/table id ·
    geography+cohort · retrievable URL or DOI.
    """
    for row in LIFETIME_COUNT_ROWS:
        assert row.publisher.strip(), f"{row.event_class_id}: missing publisher"
        assert row.edition.strip(), f"{row.event_class_id}: missing edition/survey round"
        assert row.edition_year.strip(), f"{row.event_class_id}: missing year"
        assert row.indicator_id.strip(), f"{row.event_class_id}: missing indicator/table id"
        assert row.reference_population.strip(), (
            f"{row.event_class_id}: missing geography+cohort. The reference population is "
            "a property of the L0 row; a non-Indian chart must inherit a LABELLED mismatch, "
            "never a hidden one (Elevation Law 4)."
        )
        assert row.source_url.strip(), f"{row.event_class_id}: missing retrievable URL/DOI"


def test_every_shipped_row_stores_raw_figure_and_conversion():
    """"Store the raw source figure AND the conversion string" — the ruling's
    arithmetic convention, verbatim. Without both, a Verifier cannot re-derive."""
    for row in LIFETIME_COUNT_ROWS:
        assert row.raw_figure.strip(), f"{row.event_class_id}: missing raw_figure"
        assert row.conversion_arithmetic.strip(), (
            f"{row.event_class_id}: missing conversion_arithmetic"
        )
        assert row.inclusion_criteria.strip(), (
            f"{row.event_class_id}: missing inclusion_criteria — the field against which "
            "the class's magnitude_floor match is judged"
        )


def test_every_shipped_row_has_a_permitted_prior_basis():
    for row in LIFETIME_COUNT_ROWS:
        assert row.prior_basis in VALID_PRIOR_BASES, (
            f"{row.event_class_id}: prior_basis={row.prior_basis!r} is outside the two "
            f"tiers the DB CHECK permits"
        )


def test_every_shipped_row_is_strictly_positive_and_3sf():
    """`CHECK (class_prior > 0)` is respected by NOT SEEDING, never by flooring.
    3-significant-figure rounding is the ruling's binding convention."""
    for row in LIFETIME_COUNT_ROWS:
        assert row.n_e_per_100y > 0, f"{row.event_class_id}: non-positive N_e"
        assert float(f"{row.n_e_per_100y:.3g}") == row.n_e_per_100y, (
            f"{row.event_class_id}: N_e={row.n_e_per_100y} carries more than 3 significant "
            "figures. False precision on a population statistic is a claim the source "
            "does not support."
        )


def test_at_most_once_classes_never_exceed_one():
    """Lifetime prevalence p for an at-most-once class → N_e = p, NEVER > 1.

    `foreign_settlement` is the case in point: its irreversibility milestone is
    `residency_established`, and the sourced quantity is a PREVALENCE (fraction of
    Indian-born persons living abroad), so a value above 1 would mean the conversion
    silently switched conventions mid-table.
    """
    at_most_once = {"foreign_settlement"}
    for row in LIFETIME_COUNT_ROWS:
        if row.event_class_id in at_most_once:
            assert row.n_e_per_100y <= 1.0, (
                f"{row.event_class_id}: N_e={row.n_e_per_100y} > 1 for a prevalence-based "
                "at-most-once class — the conversion convention was not applied"
            )


def test_no_shipped_row_cites_a_classical_text():
    """FORECLOSED, not merely unavailable: every classical count statement is
    chart-conditional and already lives in P_e. Seeding one here would double-count
    inside a multiplicative hazard and seat an interpretation in the base-rate slot."""
    forbidden = (
        "bphs", "parashara", "brihat", "jaimini", "phaladeepika", "saravali",
        "muhurta", "chintamani", "sutram", "samhita", "shastra", "śāstra",
    )
    for row in LIFETIME_COUNT_ROWS:
        blob = " ".join([row.publisher, row.edition, row.indicator_id,
                         row.source_url, row.raw_figure]).lower()
        for token in forbidden:
            assert token not in blob, (
                f"{row.event_class_id}: cites {token!r}. Classical-text-derived counts are "
                "FORECLOSED for N_e (ADJUDICATION-2)."
            )


def test_no_shipped_row_cites_the_lel_or_the_cohort():
    """The CIRCULARITY GUARD. λ⁰ fitted from the LEL invalidates the time-rescaling
    GOF that is supposed to falsify it."""
    forbidden = ("life_event_log", "lifeeventlog", "lel", "bg_cohort",
                 "bg_synthetic_cohort", "chart_facts")
    for row in LIFETIME_COUNT_ROWS:
        blob = " ".join(row).lower() if all(isinstance(f, str) for f in row) else " ".join(
            str(f) for f in row
        ).lower()
        for token in forbidden:
            assert token not in blob.split() and token not in blob.replace("·", " ").split(), (
                f"{row.event_class_id}: references {token!r}. The field NEVER reads the LEL, "
                "and the synthetic cohort carries no outcome data."
            )


TRANCHE_1 = {
    "childbirth", "marriage", "separation", "relocation", "surgery",
    "foreign_settlement",
}


def test_all_six_tranche_1_classes_are_seeded():
    """ADJUDICATION-2's HARD STOP, made into a detector rather than a promise.

    "If the seeding lane cannot obtain and cite at least the six Tranche-1 classes
    at Tier N-i, it seeds ZERO rows and W2 remains PARKED-HONEST." So the shipped
    table is well-formed in exactly two states — all six present, or empty. A
    partial Tranche-1 seed is the one outcome the ruling forbids, and this is the
    test that would catch a future edit silently producing it.
    """
    seeded = {r.event_class_id for r in LIFETIME_COUNT_ROWS}
    if not seeded:
        pytest.skip("zero rows seeded — the ruling's PARKED-HONEST outcome, also valid")
    missing = TRANCHE_1 - seeded
    assert not missing, (
        f"Tranche-1 classes missing from a NON-EMPTY seed: {sorted(missing)}. "
        "The ruling permits all six or none, never a partial Tranche 1."
    )


def test_excluded_and_deferred_classes_are_not_seeded():
    """`birth_anchor` is the coordinate origin, not an event (EXCLUDED — not a
    predictable class). The three DEFER classes have no defensible population
    statistic at their own definition and the ruling says do not attempt."""
    seeded = {r.event_class_id for r in LIFETIME_COUNT_ROWS}
    for cls in ("birth_anchor", "psychological_arc", "achievement_recognition",
                "spiritual_turn"):
        assert cls not in seeded, f"{cls} is EXCLUDED/DEFER and must never be seeded"


def test_no_duplicate_event_classes():
    ids = [r.event_class_id for r in LIFETIME_COUNT_ROWS]
    assert len(ids) == len(set(ids))


def test_compose_source_ref_contains_all_six_elements():
    for row in LIFETIME_COUNT_ROWS:
        ref = compose_source_ref(row)
        for element in (row.publisher, row.edition, row.edition_year,
                        row.indicator_id, row.reference_population, row.source_url):
            assert element in ref


def test_compose_citation_contains_figure_and_conversion():
    for row in LIFETIME_COUNT_ROWS:
        cit = compose_citation(row)
        assert row.raw_figure in cit
        assert row.conversion_arithmetic in cit
        assert row.inclusion_criteria in cit


# ── the validator must be able to go RED (§N.8: a check that cannot fail is not
#    a check). Each rule is exercised against a deliberately-broken row. ───────

@pytest.mark.parametrize("field", [
    "publisher", "edition", "edition_year", "indicator_id",
    "reference_population", "source_url", "raw_figure",
    "inclusion_criteria", "conversion_arithmetic",
])
def test_validator_rejects_a_blank_citation_element(field):
    with pytest.raises(ValueError):
        validate_rows([_good_row(**{field: "   "})])


def test_validator_rejects_a_non_retrievable_source_url():
    with pytest.raises(ValueError, match="retrievable"):
        validate_rows([_good_row(source_url="see the 2011 census")])


def test_validator_accepts_a_doi():
    validate_rows([_good_row(source_url="10.1016/S0140-6736(15)60160-X")])


def test_validator_rejects_an_unpermitted_prior_basis():
    with pytest.raises(ValueError, match="prior_basis"):
        validate_rows([_good_row(prior_basis="expert_judgement")])


def test_validator_rejects_a_non_positive_value():
    with pytest.raises(ValueError, match="NOT SEEDING"):
        validate_rows([_good_row(n_e_per_100y=0.0)])


def test_validator_rejects_a_duplicate_class():
    with pytest.raises(ValueError, match="duplicate"):
        validate_rows([_good_row(), _good_row()])


# ══ 2. WRITER / FROZEN-CONTRACT CONFORMANCE ══════════════════════════════════

def test_writer_is_registered_under_the_right_asset_id():
    from pipeline.orchestrator.writers import get_writer
    import pipeline.orchestrator.writers.bg_class_lifetime_counts  # noqa: F401
    writer = get_writer("bg_class_lifetime_counts")
    assert writer is not None
    assert writer.asset_id == "bg_class_lifetime_counts"


class _RecordingCursor:
    def __init__(self, sink):
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.sink["statements"].append((sql, params))

    def fetchone(self):
        # information_schema column-presence probe → both columns present;
        # unseeded-class count → 0.
        return {"count": 2 if len(self.sink["statements"]) == 1 else 0}


class _RecordingConn:
    """A fake connection that records commit/close so the FROZEN-contract rule
    'a writer NEVER commits or closes ctx.db_conn' is asserted, not assumed."""

    def __init__(self):
        self.sink = {"statements": [], "commits": 0, "closes": 0}

    def cursor(self):
        return _RecordingCursor(self.sink)

    def commit(self):
        self.sink["commits"] += 1

    def close(self):
        self.sink["closes"] += 1


def test_seed_never_commits_when_caller_owns_the_transaction():
    """§N.2: the orchestrator owns the transaction and the savepoint per sub-step.
    A writer that commits breaks rollback for every OTHER asset in the build."""
    conn = _RecordingConn()
    m.seed_class_lifetime_counts(conn, autocommit=False)
    assert conn.sink["commits"] == 0
    assert conn.sink["closes"] == 0


def test_seed_writes_at_the_reserved_coordinate_only():
    """Every INSERT must land at fact_kind='lifetime_count_per_100y',
    source_subsystem='*', signal_tradition='*', prior_version='ne_v01'. A row at any
    other coordinate is invisible to `ka_kshetra` AND visible to `bo_laksana` /
    `mi_kula`, which would be a live regression on two shipped consumers."""
    conn = _RecordingConn()
    m.seed_class_lifetime_counts(conn, autocommit=False)
    inserts = [(s, p) for (s, p) in conn.sink["statements"]
               if "INSERT INTO brahma_class_priors" in s]
    assert len(inserts) == len(LIFETIME_COUNT_ROWS)
    for sql, params in inserts:
        assert "'*', '*'" in sql, "source_subsystem/signal_tradition must both be '*'"
        assert params[0] == PRIOR_VERSION
        assert params[2] == FACT_KIND
    assert all("ON CONFLICT" in s and "DO UPDATE" in s for s, _ in inserts), (
        "§N.3: L0 idempotency is ON CONFLICT DO UPDATE"
    )


def test_seed_refuses_to_write_without_migration_522():
    """Writing N_e rows into a table lacking prior_basis/source_ref would bypass
    `brahma_class_priors_lifetime_basis_ck` entirely — the one thing that makes the
    DATA-HONESTY RAIL machine-enforced."""
    class _NoColumnsCursor(_RecordingCursor):
        def fetchone(self):
            return {"count": 0}

    class _NoColumnsConn(_RecordingConn):
        def cursor(self):
            return _NoColumnsCursor(self.sink)

    with pytest.raises(RuntimeError, match="migration 522"):
        m.seed_class_lifetime_counts(_NoColumnsConn(), autocommit=False)


def test_dry_run_reports_unknown_coverage_not_zero():
    """0 unseeded classes would read as FULL COVERAGE. A dry run has not measured
    anything, so it must say so (-1 = unknown), never imply a clean result
    (CLAUDE.md §N.7 item 4 / §N.8)."""
    conn = _RecordingConn()
    out = m.seed_class_lifetime_counts(conn, dry_run=True)
    assert out["classes_not_seeded"] == -1
    assert conn.sink["statements"] == []


# ══ 3. LIVE (DATABASE_URL) ═══════════════════════════════════════════════════

pytestmark_live = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="live DB test — set DATABASE_URL to run",
)


@pytestmark_live
def test_live_upsert_is_idempotent_and_lands_at_the_coordinate():
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row) as conn:
        first = m.seed_class_lifetime_counts(conn, autocommit=False)
        second = m.seed_class_lifetime_counts(conn, autocommit=False)
        assert first["brahma_class_priors"] == second["brahma_class_priors"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM brahma_class_priors "
                "WHERE fact_kind = %s AND prior_version = %s",
                (FACT_KIND, PRIOR_VERSION),
            )
            assert cur.fetchone()["c"] == len(LIFETIME_COUNT_ROWS)

            # The 164 legacy salience priors must be untouched and still invisible
            # to the new coordinate.
            cur.execute(
                "SELECT COUNT(*) AS c FROM brahma_class_priors "
                "WHERE prior_version = '1.0' AND fact_kind = %s",
                (FACT_KIND,),
            )
            assert cur.fetchone()["c"] == 0
        conn.rollback()


@pytestmark_live
def test_live_check_constraint_rejects_an_unsourced_lifetime_row():
    """The DB-side detector for the DATA-HONESTY RAIL. If this passes silently, the
    constraint is not doing its job and every guarantee above is self-report only."""
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO brahma_class_priors "
                    "(prior_version, signal_type_class, fact_kind, source_subsystem, "
                    " signal_tradition, class_prior) "
                    "VALUES ('ne_test', 'unsourced', %s, '*', '*', 1.0)",
                    (FACT_KIND,),
                )
        conn.rollback()
