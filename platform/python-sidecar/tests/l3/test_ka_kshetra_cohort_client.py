"""
Tests for services.ka_kshetra.cohort_client — KALA_W2_FIELD_DESIGN_v1_0.md §6.3.

ALL tests in this module run against a REAL throwaway Postgres instance loaded
with the REAL production schema (migrations 472/484, applied verbatim) and
REAL cohort data computed by the actual `pipeline.orchestrator.writers.
bg_cohort` functions (`sample_birth_params`, `compute_synthetic_positions`,
`compute_md_lord_chain`) — never a mocked connection or a hand-rolled fixture
shape. This mirrors the campaign's own W1 reverify finding (real defects hide
behind mocks that don't match live substrate) by construction: there is no
mock path here to hide behind.

Three throwaway databases are used (env-var configurable, safe local
defaults):
  LANE_D_COHORT_DSN         — the full N=10,000 cohort (the "normal" cases).
  LANE_D_COHORT_SMALL_DSN   — N=50 cohort, below the 10,000 floor (rule 4).
  LANE_D_COHORT_HETERO_DSN  — N=10,000 with 2 distinct sampling_method values
                              on 5 rows (the cohort_heterogeneous fallback).

If none of these are reachable, the whole module is skipped with a clear
reason (CI environments without a local Postgres) -- exactly the existing
`@pytest.mark.integration` convention in tests/l3/test_ka_dasha_kala.py.
"""
from __future__ import annotations

import os
import sys

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_kshetra.cohort_client import (
    MIN_MATCHED_SUBCOHORT_N,
    MIN_VIABLE_COHORT_N,
    CohortRate,
    _resolve_feature,
    cohort_base_rate,
)

_DSN = os.environ.get(
    "LANE_D_COHORT_DSN",
    "postgresql://postgres@/laned_test?host=/tmp/laned_pg_sock&port=55532",
)
_SMALL_DSN = os.environ.get(
    "LANE_D_COHORT_SMALL_DSN",
    "postgresql://postgres@/laned_test_small?host=/tmp/laned_pg_sock&port=55532",
)
_HETERO_DSN = os.environ.get(
    "LANE_D_COHORT_HETERO_DSN",
    "postgresql://postgres@/laned_test_hetero?host=/tmp/laned_pg_sock&port=55532",
)


def _connect(dsn: str):
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        return conn
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"throwaway Postgres not available at {dsn!r}: {exc}")


@pytest.fixture(scope="module")
def conn():
    c = _connect(_DSN)
    yield c
    c.rollback()
    c.close()


@pytest.fixture(scope="module")
def small_conn():
    c = _connect(_SMALL_DSN)
    yield c
    c.rollback()
    c.close()


@pytest.fixture(scope="module")
def hetero_conn():
    c = _connect(_HETERO_DSN)
    yield c
    c.rollback()
    c.close()


# ---------------------------------------------------------------------------
# Whitelist resolution (pure, no DB)
# ---------------------------------------------------------------------------

class TestResolveFeature:
    def test_lagna_sign_resolves(self):
        assert _resolve_feature("lagna_sign") == ("Lagna", "sign_id", "int")

    def test_lagna_nakshatra_resolves(self):
        assert _resolve_feature("lagna_nakshatra") == ("Lagna", "nakshatra_id", "int")

    def test_moon_nakshatra_resolves(self):
        assert _resolve_feature("moon_nakshatra") == ("Moon", "nakshatra_id", "int")

    def test_generic_graha_pada_resolves(self):
        assert _resolve_feature("venus_pada") == ("Venus", "nakshatra_pada", "int")

    def test_generic_graha_retrograde_resolves(self):
        assert _resolve_feature("saturn_retrograde") == ("Saturn", "is_retrograde", "bool")

    def test_unknown_key_returns_none(self):
        assert _resolve_feature("dispositor_of_10th_lord") is None

    def test_ke_abbreviation_is_not_whitelisted(self):
        """§6.3: 'Ketu', not 'Ke' -- a bogus abbreviation must not resolve."""
        assert _resolve_feature("ke_sign") is None


@pytest.mark.integration
class TestCohortBaseRateGlobal:
    """Rule 1: matched_by=None -> the global rate."""

    def test_global_rate_lagna_sign_is_roughly_uniform(self, conn):
        rate = cohort_base_rate("lagna_sign", 1, conn=conn)
        assert isinstance(rate, CohortRate)
        assert rate.matched is False
        assert rate.fallback_reason is None
        assert rate.p is not None
        # 12 signs, uniform-ish sampling -> roughly 1/12, generous tolerance
        assert 0.03 < rate.p < 0.20
        assert rate.n_total == MIN_VIABLE_COHORT_N
        assert rate.n > 0
        assert rate.feature_expr == "positions->'Lagna'->>'sign_id'"

    def test_global_rate_moon_nakshatra(self, conn):
        rate = cohort_base_rate("moon_nakshatra", 10, conn=conn)  # Magha
        assert rate.p is not None
        assert 0.01 < rate.p < 0.10  # 27 nakshatras -> ~1/27 baseline

    def test_global_rate_retrograde_bool(self, conn):
        rate = cohort_base_rate("mars_retrograde", True, conn=conn)
        assert rate.p is not None
        assert 0.0 < rate.p < 1.0

    def test_cohort_version_is_stable_and_pinned(self, conn):
        r1 = cohort_base_rate("lagna_sign", 1, conn=conn)
        r2 = cohort_base_rate("lagna_sign", 2, conn=conn)
        assert r1.cohort_version == r2.cohort_version
        assert r1.cohort_version.startswith("bgc_")


@pytest.mark.integration
class TestCohortBaseRateFeatureNotInCohort:
    """Rule 3: feature_key not in the closed whitelist."""

    def test_unknown_feature_key(self, conn):
        rate = cohort_base_rate("has_raja_yoga", True, conn=conn)
        assert rate.p is None
        assert rate.fallback_reason == "feature_not_in_cohort"
        assert rate.n_total == MIN_VIABLE_COHORT_N  # still reports the global n_total


@pytest.mark.integration
class TestCohortBaseRateMatched:
    """Rule 2: matched sub-cohort (E7.3), including the md_lord age-interval join."""

    def test_matched_by_md_lord_alone_succeeds(self, conn):
        # Real fixture from the seeded cohort: n=404 charts are in a Ketu MD
        # at age 25.0 globally -- clears the n>=200 floor.
        rate = cohort_base_rate(
            "lagna_sign", 12,
            matched_by={"md_lord": "Ketu"},
            native_age_at_reference_years=25.0,
            conn=conn,
        )
        assert rate.matched is True
        assert rate.fallback_reason is None
        assert rate.p is not None
        assert rate.n_total >= MIN_MATCHED_SUBCOHORT_N

    def test_matched_subcohort_too_small_falls_back_to_global(self, conn):
        # md_lord=Ketu @ age 25 AND lagna_sign=12 -> n=26 in the real fixture,
        # well under the 200 floor -> falls back to the GLOBAL rate.
        matched = cohort_base_rate(
            "lagna_sign", 12,
            matched_by={"md_lord": "Ketu", "lagna_sign": 12},
            native_age_at_reference_years=25.0,
            conn=conn,
        )
        assert matched.matched is False
        assert matched.fallback_reason is not None
        assert matched.fallback_reason.startswith("matched_subcohort_too_small")

        global_only = cohort_base_rate("lagna_sign", 12, conn=conn)
        assert matched.p == global_only.p
        assert matched.n_total == global_only.n_total

    def test_md_lord_without_reference_age_is_honest_null(self, conn):
        rate = cohort_base_rate(
            "lagna_sign", 1, matched_by={"md_lord": "Ketu"},
            native_age_at_reference_years=None, conn=conn,
        )
        assert rate.p is None
        assert rate.fallback_reason == "md_match_requires_reference_age"

    def test_bogus_matched_by_key_is_honest_null(self, conn):
        rate = cohort_base_rate(
            "lagna_sign", 1, matched_by={"has_yoga_x": True}, conn=conn,
        )
        assert rate.p is None
        assert rate.fallback_reason == "feature_not_in_cohort"


@pytest.mark.integration
class TestCohortBelowMinimum:
    """Rule 4: minimum viable cohort n_total >= 10_000, checked GLOBALLY."""

    def test_small_cohort_returns_p_none_for_every_call(self, small_conn):
        rate = cohort_base_rate("lagna_sign", 1, conn=small_conn)
        assert rate.p is None
        assert rate.fallback_reason is not None
        assert rate.fallback_reason.startswith("cohort_below_minimum")
        assert rate.n_total == 50

    def test_small_cohort_matched_by_also_gated(self, small_conn):
        rate = cohort_base_rate(
            "lagna_sign", 1, matched_by={"md_lord": "Ketu"},
            native_age_at_reference_years=25.0, conn=small_conn,
        )
        assert rate.p is None
        assert rate.fallback_reason.startswith("cohort_below_minimum")


@pytest.mark.integration
class TestCohortHeterogeneous:
    """Added fallback: cohort assembled from >1 sampling_method is not a base-rate population."""

    def test_heterogeneous_cohort_is_never_scored(self, hetero_conn):
        rate = cohort_base_rate("lagna_sign", 1, conn=hetero_conn)
        assert rate.p is None
        assert rate.fallback_reason == "cohort_heterogeneous"


@pytest.mark.integration
class TestHonestNullAccounting:
    """Acceptance test 5 (§6.3): a null-Lagna row is excluded, never scored as a non-match."""

    def test_null_lagna_row_excluded_from_denominator(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bg_synthetic_cohort
                  (synthetic_id, birth_datetime_utc, birth_lat, birth_lon,
                   ayanamsha_key, positions, sampling_method, source_citation, computed_at)
                VALUES
                  (999999, '2000-01-01T00:00:00Z', 89.0, 0.0, 'lahiri',
                   %s::jsonb, 'uniform_1900_2099_lat60_lon180_v1', 'poison-row-for-test', NOW())
                """,
                (
                    '{"Sun":{"sidereal_longitude":1,"sign_id":1,"sign":"Aries",'
                    '"nakshatra_id":1,"nakshatra":"Ashwini","nakshatra_pada":1,'
                    '"is_retrograde":false},"Moon":{"sidereal_longitude":1,"sign_id":1,'
                    '"sign":"Aries","nakshatra_id":1,"nakshatra":"Ashwini",'
                    '"nakshatra_pada":1,"is_retrograde":false},"Lagna":null}',
                ),
            )
        try:
            rate = cohort_base_rate("lagna_sign", 1, conn=conn)
            # The poison row must be excluded from BOTH numerator and
            # denominator via the null-safety clause, never counted as a
            # non-match for lagna_sign=1.
            assert rate.n_total == MIN_VIABLE_COHORT_N  # unchanged: the null row is excluded
            assert rate.n_excluded_honest_null == 1
        finally:
            conn.rollback()  # never persist the poison row


@pytest.mark.integration
class TestPredicateFormEquivalence:
    """Acceptance test 4 (§6.3): @> containment and ->> extraction must agree."""

    @pytest.mark.parametrize("feature_key,value", [
        ("lagna_sign", 3), ("moon_nakshatra", 10), ("sun_pada", 2),
    ])
    def test_containment_and_extraction_agree(self, conn, feature_key, value):
        graha, field, _kind = _resolve_feature(feature_key)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM bg_synthetic_cohort WHERE positions @> %s::jsonb",
                (f'{{"{graha}":{{"{field}":{value}}}}}',),
            )
            containment_n = cur.fetchone()[0]
            cur.execute(
                f"SELECT count(*) FROM bg_synthetic_cohort WHERE positions->'{graha}'->>'{field}' = %s",
                (str(value),),
            )
            extraction_n = cur.fetchone()[0]
        assert containment_n == extraction_n


@pytest.mark.integration
class TestFingerprintSensitivity:
    """Acceptance test 6 (§6.3): mutating cohort content changes cohort_version."""

    def test_mutation_changes_fingerprint(self, conn):
        # The fingerprint SQL (§6.3, verbatim) hashes `positions::text`, not
        # birth_lat/lon/datetime -- so the mutation must touch `positions`
        # itself for this to be a meaningful test of the digest.
        before = cohort_base_rate("lagna_sign", 1, conn=conn).cohort_version
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bg_synthetic_cohort "
                "SET positions = jsonb_set(positions, '{Sun,sidereal_longitude}', "
                "((positions->'Sun'->>'sidereal_longitude')::numeric + 0.0001)::text::jsonb) "
                "WHERE synthetic_id = 1"
            )
        try:
            after = cohort_base_rate("lagna_sign", 1, conn=conn).cohort_version
            assert after != before
        finally:
            conn.rollback()

        reverted = cohort_base_rate("lagna_sign", 1, conn=conn).cohort_version
        assert reverted == before


@pytest.mark.integration
class TestMdChainInvariantsAgainstRealData:
    """
    Acceptance tests 2/3 (§6.3), run against the REAL seeded bg_synthetic_cohort_md
    data (bg_cohort.py is not a Lane D file, but cohort_client.py's age-interval
    join logic depends on both invariants holding, so this lane verifies them
    directly against the live table it reads).
    """

    def test_stored_parse_agreement_across_all_rows(self, conn):
        """Acceptance test 2: derived nak0+1 == stored positions Moon nakshatra_id.

        `compute_md_lord_chain` (bg_cohort.py) raises `MdChainAuthorityDivergence`
        at WRITE time if this ever disagrees (§N.5 halt-worthy), so the mere
        presence of md_index=1 rows for every synthetic_id in this live table is
        itself evidence the invariant held for the entire seeded cohort. This
        query re-derives it independently as a live, second detector.
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*) FROM bg_synthetic_cohort c
                JOIN bg_synthetic_cohort_md m
                  ON m.synthetic_id = c.synthetic_id AND m.md_index = 1
                WHERE (floor((c.positions->'Moon'->>'sidereal_longitude')::numeric
                             / (360.0/27.0))::int + 1)
                      != (c.positions->'Moon'->>'nakshatra_id')::int
                """
            )
            mismatches = cur.fetchone()[0]
        assert mismatches == 0

    def test_gapless_half_open_cover(self, conn):
        """Acceptance test 3: for ~20 reference ages, the age join returns
        exactly one row per chart (count(*) == count(DISTINCT synthetic_id))."""
        with conn.cursor() as cur:
            for ref_age in [i * 6.0 for i in range(20)]:  # 0, 6, 12, ..., 114
                cur.execute(
                    """
                    SELECT count(*), count(DISTINCT synthetic_id)
                    FROM bg_synthetic_cohort_md
                    WHERE %(age)s >= start_age_years AND %(age)s < end_age_years
                    """,
                    {"age": ref_age},
                )
                n, n_distinct = cur.fetchone()
                assert n == n_distinct, f"age {ref_age}: {n} rows but {n_distinct} distinct charts"

    def test_max_end_age_is_exactly_120_and_min_start_is_zero(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT min(min_start), max(max_end) FROM (
                  SELECT synthetic_id, min(start_age_years) AS min_start,
                         max(end_age_years) AS max_end
                  FROM bg_synthetic_cohort_md GROUP BY synthetic_id
                ) t
                """
            )
            min_start, max_end = cur.fetchone()
        assert float(min_start) == 0.0
        assert abs(float(max_end) - 120.0) < 1e-6
