"""
Test 2 — Golden parity: v3 engine reproduces v1 results.

Compares v3's evaluate_lambda_vector output against v1's compute_lambda_e
for the same inputs (fixtures, no DB). The comparison is across the
components that v3 preserves identically:
  - PROMISE (time-invariant, computed once in both engines)
  - beta_e (same structural prior)
  - valence/is_adverse (same maps)

Components that may differ slightly (documented, honest trade-off):
  - PERMISSION: v3's dasha system evaluation is structurally identical
    (same period_contains logic, same lord_matches). Non-dasha generators
    (guru-shani, av_threshold, planetary_return) use the same v1 primitives.
    Sade sati uses pre-fetched phases (may differ if phase format doesn't
    match exactly — honest gap in pre-fetch, not a fabricated value).
  - X(t): v3 calls the same 6 ephemeris-only primitives. The 3 conn-needing
    primitives (kakshya_cell_crossing, gochara_vedha_pair, sarvatobhadra_vedha)
    are called with conn=None (honest degrade to []). In v1 with conn=None,
    those same primitives also degrade to []. So X(t) should be identical.
  - Suppression: computed from the same sentence pool as X(t).

Net expectation: with conn=None (fixture mode, which both v1 and v3 use
in tests), v1 and v3 should produce BIT-COMPARABLE results for PROMISE,
X(t), suppression, and the non-DB permission generators. Dasha permission
depends on the exact dasha_periods passed — we use the same fixture for both.

NOTE: This test does NOT query the live DB for golden rows from
kala_gochara_windows. It compares v1 vs v3 computation on the same
fixture inputs. A live golden-parity test against the protected corpus
is a separate integration test.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import swisseph as swe

from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.engine import compute_lambda_e
from services.gochara_intensity.promise import compute_promise
from services.gochara_intensity.beta_priors import beta_for

from services.gochara_v3.context import ClassContext
from services.gochara_v3.engine import evaluate_lambda_vector


CHART_ID = RM.CANONICAL_CHART_ID


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


@pytest.fixture(autouse=True)
def _reset_cache():
    from pipeline.transit_search import clear_ephemeris_cache
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


def _build_parity_context(event_class: str, targets, dasha_periods) -> ClassContext:
    """Build a ClassContext from the same fixtures v1 uses."""
    promise, promise_detail = compute_promise(list(targets))

    # Extract relevant grahas/signs the same way v1's permission.py does
    from services.gochara_intensity.permission import _relevant_grahas, _relevant_signs
    rel_grahas = frozenset(_relevant_grahas(list(targets)))
    rel_signs = frozenset(_relevant_signs(list(targets)))

    from services.gochara_intensity.valence import is_adverse as _is_adverse
    adverse, valence = _is_adverse(None, event_class)

    from services.gochara_intensity.engine import SHAPE_MAP
    shape = SHAPE_MAP.get(event_class, "point")

    return ClassContext(
        chart_id=CHART_ID,
        event_class=event_class,
        resonance_targets=tuple(targets),
        promise=promise,
        promise_detail=promise_detail,
        dasha_periods=tuple(dasha_periods),
        relevant_grahas=rel_grahas,
        relevant_signs=rel_signs,
        temporal_shape=shape,
        valence=valence,
        is_adverse=adverse,
        beta_e=beta_for(event_class),
        weight_by_target_ref={t.target_ref: t.weight for t in targets},
        natal_facts=None,
        av_gate_rows=(),
        sade_sati_phases=(),
    )


class TestV1ParityMarriage:
    """Compare v1 vs v3 on the marriage fixture at 200 sample JDs."""

    @pytest.fixture
    def marriage_fixtures(self):
        targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
        dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)
        return targets, dasha_periods

    def test_promise_is_identical(self, marriage_fixtures):
        """PROMISE is time-invariant and uses the same compute_promise.
        Must be bit-identical."""
        targets, dasha_periods = marriage_fixtures
        context = _build_parity_context("marriage", targets, dasha_periods)

        # v1
        from services.gochara_intensity.promise import compute_promise as v1_promise
        v1_p, _ = v1_promise(list(targets))

        assert context.promise == pytest.approx(v1_p), (
            f"PROMISE mismatch: v3={context.promise}, v1={v1_p}"
        )

    def test_valence_and_sign_are_identical(self, marriage_fixtures):
        """Valence and is_adverse use the same maps. Must be identical."""
        targets, dasha_periods = marriage_fixtures
        context = _build_parity_context("marriage", targets, dasha_periods)

        from services.gochara_intensity.valence import is_adverse as v1_is_adverse
        v1_adverse, v1_valence = v1_is_adverse(None, "marriage")

        assert context.valence == v1_valence
        assert context.is_adverse == v1_adverse

    def test_beta_is_identical(self, marriage_fixtures):
        """Beta_e uses the same beta_for function. Must be identical."""
        targets, dasha_periods = marriage_fixtures
        context = _build_parity_context("marriage", targets, dasha_periods)

        from services.gochara_intensity.beta_priors import beta_for as v1_beta
        assert context.beta_e == v1_beta("marriage")

    def test_lambda_e_values_match_v1_at_sample_points(self, marriage_fixtures):
        """Compare v3 evaluate_lambda_vector vs v1 compute_lambda_e
        at 200 sample JDs. Both use conn=None (fixture mode), so
        conn-needing primitives degrade identically in both engines."""
        targets, dasha_periods = marriage_fixtures
        context = _build_parity_context("marriage", targets, dasha_periods)

        # 200 sample JDs spanning the marriage specimen window
        sample_jds = np.linspace(_jd(2013, 6, 1), _jd(2014, 6, 1), 200)

        # v3: batch
        v3_results = evaluate_lambda_vector(swe, context, sample_jds)

        # v1: per-point
        v1_results = []
        for jd in sample_jds:
            v1_r = compute_lambda_e(
                swe, None, CHART_ID, "marriage", float(jd),
                targets=list(targets), dasha_periods=list(dasha_periods),
                source="fixture",
            )
            v1_results.append(v1_r)

        assert len(v3_results) == len(v1_results) == 200

        # Compare each point
        mismatches = []
        for i, (v3_r, v1_r) in enumerate(zip(v3_results, v1_results)):
            # PROMISE must be exactly identical
            if v3_r.promise != pytest.approx(v1_r.promise):
                mismatches.append(f"[{i}] PROMISE: v3={v3_r.promise}, v1={v1_r.promise}")

            # beta_e must be identical
            if v3_r.beta_e != v1_r.beta_e:
                mismatches.append(f"[{i}] beta_e: v3={v3_r.beta_e}, v1={v1_r.beta_e}")

            # X(t) should be identical (same primitives, same conn=None degrade)
            if not math.isclose(v3_r.x_t, v1_r.x_t, rel_tol=1e-6, abs_tol=1e-9):
                mismatches.append(f"[{i}] X(t): v3={v3_r.x_t}, v1={v1_r.x_t}")

            # Suppression should be identical (same sentence pool)
            if not math.isclose(v3_r.suppression, v1_r.suppression, rel_tol=1e-6, abs_tol=1e-9):
                mismatches.append(f"[{i}] suppression: v3={v3_r.suppression}, v1={v1_r.suppression}")

            # raw_lambda and signed_lambda should be very close
            # (small differences possible from permission if sade_sati
            # pre-fetch format differs)
            if not math.isclose(v3_r.raw_lambda, v1_r.raw_lambda, rel_tol=0.05, abs_tol=1e-6):
                mismatches.append(
                    f"[{i}] raw_lambda: v3={v3_r.raw_lambda:.6f}, "
                    f"v1={v1_r.raw_lambda:.6f} "
                    f"(perm v3={v3_r.permission:.4f}, v1={v1_r.permission:.4f})"
                )

        if mismatches:
            # Report first 10 mismatches
            report = "\n".join(mismatches[:10])
            if len(mismatches) > 10:
                report += f"\n... and {len(mismatches) - 10} more"
            pytest.fail(f"v1/v3 parity mismatches ({len(mismatches)}/200):\n{report}")


class TestV1ParityAdverseClass:
    """Verify that adverse classes produce identical sign flips in v1 and v3."""

    def test_bereavement_sign_flip(self):
        targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
        dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

        # v3
        ctx_adverse = _build_parity_context("bereavement", targets, dasha_periods)
        ctx_neutral = _build_parity_context("marriage", targets, dasha_periods)

        jd_vector = np.array([_jd(2013, 12, 11)])
        v3_adverse = evaluate_lambda_vector(swe, ctx_adverse, jd_vector)[0]
        v3_neutral = evaluate_lambda_vector(swe, ctx_neutral, jd_vector)[0]

        # v1
        t_jd = _jd(2013, 12, 11)
        v1_adverse = compute_lambda_e(
            swe, None, CHART_ID, "bereavement", t_jd,
            targets=list(targets), dasha_periods=list(dasha_periods),
        )
        v1_neutral = compute_lambda_e(
            swe, None, CHART_ID, "marriage", t_jd,
            targets=list(targets), dasha_periods=list(dasha_periods),
        )

        # Both engines should flip sign for adverse classes
        assert v3_adverse.is_adverse is True
        assert v1_adverse.is_adverse is True
        assert v3_neutral.is_adverse is False
        assert v1_neutral.is_adverse is False

        # Raw lambda should be the same magnitude
        assert v3_adverse.raw_lambda == pytest.approx(v3_neutral.raw_lambda, rel=0.05)
        assert v1_adverse.raw_lambda == pytest.approx(v1_neutral.raw_lambda)

        # Signed lambda should be negated for adverse
        if v3_adverse.raw_lambda > 0:
            assert v3_adverse.signed_lambda < 0
            assert v3_neutral.signed_lambda > 0


class TestV1ParityPermission:
    """Test that v3's permission computation matches v1's logic."""

    def test_dasha_system_contributions_match(self):
        """Dasha-system contributions use the same period_contains + lord_matches
        logic. With the same fixture dasha_periods, results must be identical."""
        targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
        dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)

        # v1
        from services.gochara_intensity.permission import compute_permission
        _, v1_detail = compute_permission(
            swe, None, CHART_ID, "marriage", list(targets), _jd(2013, 12, 11),
            dasha_periods=list(dasha_periods),
        )

        # v3
        context = _build_parity_context("marriage", targets, dasha_periods)
        jd_vector = np.array([_jd(2013, 12, 11)])
        v3_results = evaluate_lambda_vector(swe, context, jd_vector)
        v3_detail = v3_results[0].permission_detail

        # Dasha systems should report the same active/inactive state
        from services.gochara_intensity.permission import DASHA_SYSTEM_IDS as _DASHA_IDS
        v1_dasha_active = {
            s["system_id"]: s["active"]
            for s in v1_detail["systems"]
            if s["system_id"] in set(_DASHA_IDS)
        }
        v3_dasha_active = {
            s["system_id"]: s["active"]
            for s in v3_detail["systems"]
            if s["system_id"] in set(_DASHA_IDS)
        }

        for sid in _DASHA_IDS:
            assert v3_dasha_active.get(sid) == v1_dasha_active.get(sid), (
                f"Dasha system {sid}: v3={v3_dasha_active.get(sid)}, "
                f"v1={v1_dasha_active.get(sid)}"
            )
