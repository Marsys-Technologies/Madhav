"""
test_mi_sambandha.py — hermetic tests for the F-35 earned-signal fix and the
F-147 composite_verdict vocabulary fix that made F-35 reachable.

F-35 narrowed mi_sambandha's grade predicate so 'empirical' requires >=5 SCORED
outcomes rather than >=5 raw assignments. F-147 found that the scored-ness test
itself compared against a vocabulary no writer has ever emitted:

    if verdict in ("confirmed", "partial", "denied"):   # <-- matched nothing

mimamsa_calibration.composite_verdict is written by exactly one code path,
mi_pramana._verdict_v2, which emits UPPERCASE from a closed set of five:
CONFIRMED / PARTIAL / REFUTED / UNRESOLVED / FALSE_ALARM. Production confirms
it: the live table holds only UNRESOLVED, PARTIAL, REFUTED and CONFIRMED.
'denied' is not a casing variant of anything — it is a word no writer emits.

The lowercase triple came from migration 348's stale inline column comment
(`-- 'confirmed'|'partial'|'denied'|'pending'`). Both the source AND the
original version of this test inherited the wrong vocabulary from that comment,
so the test passed while the production computation was inert — a bug-compatible
test, not a check. These tests therefore use the REAL vocabulary only, and
`_FICTIONAL_VERDICTS` guards the specific words that must never count again.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers.mi_sambandha import MiSambandhaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Index map for the INSERT column list in mi_sambandha.py:
#   chart_id 0, origin_kind 1, origin_ref 2, channel_id 3, domain 4,
#   fire_count 5, opportunity_count 6, scored_count 7, channel_propensity 8,
#   prior_propensity 9, propensity_delta 10, n_support 11, confidence_band 12,
#   evidence_grade 13, citation_ref 14, grammar_formula_version 15
CHANNEL_ID, FIRE, OPP, SCORED, PROPENSITY, EVIDENCE_GRADE = 3, 5, 6, 7, 8, 13

# The real, production-confirmed vocabulary.
ADJUDICATED = ["CONFIRMED", "PARTIAL", "REFUTED"]
NOT_ADJUDICATED = ["UNRESOLVED", "FALSE_ALARM"]

# Words the pre-F-147 code tested for that no writer emits. If any of these ever
# counts as scored again, this module has regressed to the fictional vocabulary.
_FICTIONAL_VERDICTS = ["confirmed", "partial", "denied", "DENIED", "pending"]


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "FROM mimamsa_manifestation_sets" in s:
            self._result = list(self._conn.mset_rows)
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_manifestation_grammar" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, mset_rows):
        self.mset_rows = list(mset_rows)
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


class _FakeCtx:
    def __init__(self, chart_id, db_conn, dry_run=False):
        self.config = {"chart_id": chart_id}
        self.db_conn = db_conn
        self.dry_run = dry_run


def _assignment(i, verdict, channel_id="ch_career_verbal",
                domain="career", fired_channel=None):
    """One manifestation-set assignment LEFT JOINed to its calibration row.

    verdict=None models the join finding no calibration row at all (both
    columns NULL) — F-35's live repro shape.
    """
    return {
        "prediction_id": f"pred_{i}",
        "channel_id": channel_id,
        "domain": domain,
        "is_literal": True,
        "composite_verdict": verdict,
        "manifestation_channel": fired_channel,
    }


def _run(rows):
    conn = _FakeConn(rows)
    MiSambandhaWriter().run(_FakeCtx(NATIVE_CHART_ID, conn, dry_run=False))
    return conn.inserted_rows


def _row_for(inserted, channel_id="ch_career_verbal"):
    return next(r for r in inserted if r[CHANNEL_ID] == channel_id)


# ---------------------------------------------------------------------------
# F-35 regression guards (unchanged intent, real vocabulary)
# ---------------------------------------------------------------------------

def test_nine_unscored_assignments_do_not_earn_empirical_grade():
    """F-35: opp=9 with zero scored outcomes must grade 'assignment_only'."""
    row = _row_for(_run([_assignment(i, None) for i in range(9)]))
    assert row[SCORED] == 0
    assert row[OPP] == 9
    assert row[EVIDENCE_GRADE] == "assignment_only"


def test_five_adjudicated_assignments_earn_empirical_grade():
    """F-35 positive case, now stated in the REAL vocabulary: 3 CONFIRMED +
    2 REFUTED = 5 adjudicated outcomes, which must still grade 'empirical'.

    This is the test that F-147 broke open: it previously used 'confirmed' and
    'denied' and passed against the equally-wrong source.
    """
    rows = (
        [_assignment(f"c{i}", "CONFIRMED", fired_channel="ch_career_verbal") for i in range(3)]
        + [_assignment(f"r{i}", "REFUTED", fired_channel="ch_career_material") for i in range(2)]
    )
    row = _row_for(_run(rows))
    assert row[SCORED] == 5
    assert row[EVIDENCE_GRADE] == "empirical"


# ---------------------------------------------------------------------------
# F-147: the vocabulary itself
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("verdict", ADJUDICATED)
def test_each_adjudicated_verdict_counts_as_scored(verdict):
    """Every member of the real adjudicated set must increment scored_count."""
    row = _row_for(_run([_assignment(i, verdict) for i in range(5)]))
    assert row[SCORED] == 5, f"{verdict} must count toward scored_count"
    assert row[EVIDENCE_GRADE] == "empirical"


@pytest.mark.parametrize("verdict", NOT_ADJUDICATED)
def test_non_adjudicated_verdicts_do_not_count_as_scored(verdict):
    """UNRESOLVED (window still open) and FALSE_ALARM (control prediction) are
    real verdicts but NOT evidence — they must never earn 'empirical'."""
    row = _row_for(_run([_assignment(i, verdict) for i in range(9)]))
    assert row[SCORED] == 0, f"{verdict} must not count toward scored_count"
    assert row[EVIDENCE_GRADE] == "assignment_only"


@pytest.mark.parametrize("verdict", _FICTIONAL_VERDICTS)
def test_fictional_vocabulary_never_counts_as_scored(verdict):
    """The pre-F-147 literals are not a casing variant of the real set —
    'denied'/'pending' are words no writer emits. Counting them again would mean
    the fictional vocabulary had been reintroduced.

    Note 'confirmed'/'partial' DO count here via .upper() normalization, which is
    correct and deliberate; they are excluded from this guard's assertion set.
    """
    if verdict.upper() in ADJUDICATED:
        pytest.skip(f"{verdict!r} is a casing variant of a real verdict")
    row = _row_for(_run([_assignment(i, verdict) for i in range(9)]))
    assert row[SCORED] == 0, f"fictional verdict {verdict!r} must not be scored"
    assert row[EVIDENCE_GRADE] == "assignment_only"


def test_verdict_comparison_is_case_insensitive():
    """composite_verdict is an unconstrained `text` column (migration 348 has no
    CHECK). The sole writer emits uppercase, but normalization must hold so a
    future writer cannot silently re-open F-147."""
    rows = [_assignment(i, v) for i, v in enumerate(
        ["confirmed", "Partial", "REFUTED", "cOnFiRmEd", "partial"]
    )]
    row = _row_for(_run(rows))
    assert row[SCORED] == 5
    assert row[EVIDENCE_GRADE] == "empirical"


# ---------------------------------------------------------------------------
# fire_count / channel_propensity
# ---------------------------------------------------------------------------

def test_fire_count_requires_confirmed_or_partial_and_matching_channel():
    """fire_count counts only outcomes that actually occurred (CONFIRMED /
    PARTIAL) AND fired on the channel being graded. REFUTED is adjudicated —
    it counts as scored — but is by definition not a firing."""
    rows = [
        _assignment(0, "CONFIRMED", fired_channel="ch_career_verbal"),    # fires
        _assignment(1, "PARTIAL",   fired_channel="ch_career_verbal"),    # fires
        _assignment(2, "REFUTED",   fired_channel="ch_career_verbal"),    # scored, no fire
        _assignment(3, "CONFIRMED", fired_channel="ch_career_material"),  # other channel
        _assignment(4, "UNRESOLVED", fired_channel="ch_career_verbal"),   # not adjudicated
    ]
    row = _row_for(_run(rows))
    assert row[OPP] == 5
    assert row[SCORED] == 4, "CONFIRMED x2 + PARTIAL + REFUTED"
    assert row[FIRE] == 2, "only CONFIRMED/PARTIAL on the matching channel"


def test_channel_propensity_is_fire_over_opportunity():
    """channel_propensity must be the real ratio, not 0.0-by-inertness."""
    rows = [
        _assignment(i, "CONFIRMED", fired_channel="ch_career_verbal") for i in range(3)
    ] + [
        _assignment(i + 3, "REFUTED", fired_channel="ch_career_material") for i in range(5)
    ]
    row = _row_for(_run(rows))
    assert row[OPP] == 8
    assert row[FIRE] == 3
    assert row[SCORED] == 8
    assert row[PROPENSITY] == pytest.approx(0.375)  # 3/8
    assert row[EVIDENCE_GRADE] == "empirical"


# ---------------------------------------------------------------------------
# Production-shaped end-to-end check
# ---------------------------------------------------------------------------

def test_production_verdict_distribution_produces_nonzero_scored_count():
    """The live mimamsa_calibration distribution for the canonical chart is
    UNRESOLVED=25, PARTIAL=23, REFUTED=7, CONFIRMED=2 (verified against
    production). Scaled to one channel, the adjudicated subset (PARTIAL +
    REFUTED + CONFIRMED = 32) must be counted and UNRESOLVED excluded.

    Pre-F-147 this whole distribution computed scored_count=0 — the exact
    production symptom that made 'empirical' unreachable.
    """
    dist = {"UNRESOLVED": 25, "PARTIAL": 23, "REFUTED": 7, "CONFIRMED": 2}
    rows, i = [], 0
    for verdict, n in dist.items():
        for _ in range(n):
            rows.append(_assignment(i, verdict, domain="relationship",
                                    channel_id="ch_relationship_verbal"))
            i += 1

    row = _row_for(_run(rows), channel_id="ch_relationship_verbal")
    assert row[OPP] == 57
    assert row[SCORED] == 32, "PARTIAL(23) + REFUTED(7) + CONFIRMED(2)"
    assert row[EVIDENCE_GRADE] == "empirical"
