"""
tests/test_layer0_projection.py — CI gate for DHARA_ENGINE_SPEC §1 and §2.

Required gate (DHARA_ENGINE_SPEC_v1_0.md §2.3 / §5):
  Layer0→Layer1 equivalence at 50 sampled knots for 6 calibrated classes.
  |project_layer1(layer0, ...)[t_i] - terms_at(t_i).ln_lambda| < 1e-12

Additionally:
  Contiguity gate: gaps == 0 for full horizon; interior decade knots present.
  SM-R-7 suppression gate: class with no suppressed routes gets S_e(t) = 1.0.

DESIGN (no-DB, fixture-based):
  Uses a mock FieldEvaluator built from the same fixture shape as
  tests/test_dhara_sweep.py — no Postgres dependency.

EXPECTED DIFFERENCES REGISTER (SM-R-7 §2.1 note):
  The equivalence test also documents which classes diverge under SM-R-7's
  suppression fix vs. the live unfiltered code.  A divergence means:
    "the live code was passing ALL obstructions to suppression_log_term
    even when they weren't in any Route.suppressed_by for this class".
  With the fix, filtered_obs only contains keys in suppressed_by.

  In the fixture used here:
    - career_change has one route with suppressed_by=('vedha:Sa->10',) and one
      with suppressed_by=(). The vighna 'vedha:Sa->10' IS in a suppressed_by set,
      so filtered_obs == full obstructions dict when 'vedha:Sa->10' is active.
      → career_change: NO divergence from the fix (the only obstruction key IS
      in a suppressed_by).

  For a class where NO route has any suppressed_by keys, filtered_obs would be
  {} while today's code passes the full obstructions dict. That is the fix SM-R-7
  mandates: S_e(t) = 1.0 for those classes (no suppression when not referenced
  by any route).

  See test_smr7_suppression_filter_isolation for an explicit before/after test.

Authority: DHARA_ENGINE_SPEC_v1_0.md §1, §2, §5 (gate: Layer0→Layer1
equivalence, knot contiguity, suppression filter).
"""
from __future__ import annotations

import bisect
import math
from typing import Any, Optional, Sequence
from unittest.mock import MagicMock

import numpy as np
import pytest

from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route
from services.ka_kshetra.hazard import (
    COVARIATE_KEYS,
    RHO_MAX,
    suppression_log_term,
)
from services.ka_kshetra.stage4_field import (
    EnvelopeIndex,
    FieldEvaluator,
    LadderPeriod,
    Primitive,
)

# ─── fixture constants ────────────────────────────────────────────────────────

HORIZON_DAYS = 400.0
CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

# Six calibrated event classes the spec requires equivalence for.
CALIBRATED_CLASSES = [
    'childbirth',
    'marriage',
    'foreign_settlement',
    'career_change',
    'career_entry',
    'death',
]

# Seed for reproducible random knot sampling.
_RNG_SEED = 42


# ─── fixture builders ─────────────────────────────────────────────────────────

def _make_primitive(
    *,
    primitive_kind: str,
    subject: str,
    object_ref: Optional[str],
    polarity: str,
    knots: list[tuple[float, float]],
    class_label: Optional[str] = None,
) -> Primitive:
    return Primitive(
        primitive_kind=primitive_kind,
        subject=subject,
        object_ref=object_ref,
        polarity=polarity,
        class_label=class_label,
        knots=tuple((float(t), float(v)) for t, v in knots),
        source_pk=None,
        source_fact_id=None,
        source_table=None,
    )


def _make_weights() -> dict[str, float]:
    return {
        'w_s:vimshottari': 1.0,
        'w_s:yogini': 0.6,
        'd:MD': 1.0,
        'd:AD': 0.7,
        'beta:x1': 0.9,
        'beta:x2': 0.4,
        'beta:x3': 0.3,
        'rho:vedha': 0.4,
        'rho:default': 0.25,
    }


def _make_clocks() -> list[ClockApplicability]:
    return [
        ClockApplicability(
            system_id='vimshottari',
            applicability_state='applicable',
            competence_class='fruition',
            seniority_rank=1,
            is_predictive=True,
            quality=0.92,
        ),
        ClockApplicability(
            system_id='yogini',
            applicability_state='applicable',
            competence_class='flavour',
            seniority_rank=3,
            is_predictive=True,
            quality=0.71,
        ),
    ]


def _make_ladder() -> dict[str, list[LadderPeriod]]:
    return {
        'vimshottari': [
            LadderPeriod('vimshottari', 'MD', 'Ju', 0.0, 200.0),
            LadderPeriod('vimshottari', 'MD', 'Sa', 200.0, 400.0),
            LadderPeriod('vimshottari', 'AD', 'Mo', 0.0, 100.0),
            LadderPeriod('vimshottari', 'AD', 'Ma', 100.0, 200.0),
            LadderPeriod('vimshottari', 'AD', 'Ra', 200.0, 300.0),
            LadderPeriod('vimshottari', 'AD', 'Sa', 300.0, 400.0),
        ],
        'yogini': [
            LadderPeriod('yogini', 'MD', 'Ju', 0.0, 400.0),
        ],
    }


def _make_primitives_with_obstruction() -> list[Primitive]:
    """Fixture with one supportive and one obstructive primitive."""
    return [
        _make_primitive(
            primitive_kind='contact_moon_ref',
            subject='Ju', object_ref='Mo',
            polarity='supportive',
            knots=[(90.0, 0.0), (100.0, 1.0), (110.0, 0.0)],
        ),
        _make_primitive(
            primitive_kind='contact_lagna_ref',
            subject='Ju', object_ref='Lagna',
            polarity='supportive',
            knots=[(95.0, 0.0), (102.0, 0.8), (112.0, 0.0)],
        ),
        # Obstructive — vighna_key = 'vedha:Sa->10'
        _make_primitive(
            primitive_kind='vedha',
            subject='Sa', object_ref='10',
            polarity='obstructive',
            knots=[(250.0, 0.0), (260.0, 1.0), (270.0, 0.0)],
        ),
    ]


def _make_routes_with_suppression(event_class: str) -> tuple[Route, ...]:
    """Routes for career_change: one suppressed by vedha:Sa->10, one not."""
    return (
        Route(
            event_class=event_class,
            route_rank=1,
            path_node_ids=('graha:Ju', 'bhava:10', f'event_class:{event_class}'),
            path_edge_ids=(101,),
            route_gain=0.62,
            is_primary=True,
            suppressed_by=(),
        ),
        Route(
            event_class=event_class,
            route_rank=2,
            path_node_ids=('graha:Sa', 'bhava:10', f'event_class:{event_class}'),
            path_edge_ids=(102,),
            route_gain=0.31,
            is_primary=False,
            suppressed_by=('vedha:Sa->10',),
        ),
    )


def _make_routes_no_suppression(event_class: str) -> tuple[Route, ...]:
    """Routes with no suppressed_by entries — SM-R-7 fix makes S_e = 1.0."""
    return (
        Route(
            event_class=event_class,
            route_rank=1,
            path_node_ids=('graha:Ju', 'bhava:1', f'event_class:{event_class}'),
            path_edge_ids=(201,),
            route_gain=0.55,
            is_primary=True,
            suppressed_by=(),
        ),
    )


def _make_promise(event_class: str, routes: tuple[Route, ...]) -> PromisePrior:
    p = 1.0 - math.prod(1.0 - r.route_gain for r in routes) if routes else 0.0
    return PromisePrior(p=min(max(p, 0.0), 1.0), routes=routes, n_routes=len(routes))


def _build_evaluator(
    event_class: str,
    routes: Optional[tuple[Route, ...]] = None,
    primitives: Optional[list[Primitive]] = None,
    lifetime_count: float = 2.0,
) -> FieldEvaluator:
    if routes is None:
        routes = _make_routes_with_suppression(event_class)
    if primitives is None:
        primitives = _make_primitives_with_obstruction()

    return FieldEvaluator(
        event_class=event_class,
        lifetime_count=lifetime_count,
        promise=_make_promise(event_class, routes),
        clocks=_make_clocks(),
        ladder=_make_ladder(),
        envelopes=EnvelopeIndex(primitives, HORIZON_DAYS),
        weights=_make_weights(),
        horizon_days=HORIZON_DAYS,
        extra_breakpoints=(),
    )


# ─── import the modules under test ───────────────────────────────────────────

# NOTE: These imports will FAIL until layer0.py and layer1.py exist — that is
# the TDD discipline (DHARA_ENGINE_SPEC §2.3, FM-26). Write the tests, watch
# them fail, implement, watch them pass.

try:
    from services.ka_kshetra.layer0 import (
        Layer0,
        assemble_knot_set_with_decade_seams,
        compute_layer0,
    )
    from services.ka_kshetra.layer1 import project_layer1
    _MODULES_AVAILABLE = True
except ImportError:
    _MODULES_AVAILABLE = False


# ─── gate: require modules exist ─────────────────────────────────────────────

pytestmark = pytest.mark.skipif(
    not _MODULES_AVAILABLE,
    reason='layer0.py / layer1.py not yet implemented (TDD: implement to pass)',
)


# ─────────────────────────────────────────────────────────────────────────────
# GATE 1: Knot contiguity + decade seams
# ─────────────────────────────────────────────────────────────────────────────

class TestKnotContiguity:
    """DHARA_ENGINE_SPEC §5: gaps == 0 for full horizon; interior decade knots present."""

    def test_no_gaps_in_knot_set(self):
        """Every consecutive pair of knots must be adjacent (no gap in coverage)."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        K = layer0.knots
        assert len(K) >= 2, 'Need at least 2 knots'
        # Gaps would manifest as non-monotone or repeated values; np.unique handles
        # dedup, so we just check strict monotone.
        diffs = np.diff(K)
        assert np.all(diffs > 0), f'Non-monotone knots: diffs={diffs[diffs <= 0]}'
        assert float(K[0]) == 0.0, f'First knot must be 0.0, got {K[0]}'
        assert float(K[-1]) == pytest.approx(HORIZON_DAYS, abs=1e-10), \
            f'Last knot must be horizon={HORIZON_DAYS}, got {K[-1]}'

    def test_interior_decade_knots_present(self):
        """9 interior decade seam knots t = d*H/10 for d=1..9 must be in K."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        K_set = set(float(t) for t in layer0.knots)
        for d in range(1, 10):
            seam = d * HORIZON_DAYS / 10.0
            assert seam in K_set or any(
                abs(k - seam) < 1e-9 for k in K_set
            ), f'Decade seam t={seam} (d={d}) missing from knot set'

    def test_assemble_knot_set_with_decade_seams_adds_9_interior_points(self):
        """The standalone assembler adds exactly the 9 interior decade knots."""
        ev = _build_evaluator('career_change')
        # Build baseline without decade seams using the original dhara_sweep assembler
        from services.ka_kshetra.dhara_sweep import assemble_knot_set as orig_assemble
        K_orig = orig_assemble(ev)
        K_new = assemble_knot_set_with_decade_seams(ev)
        orig_set = set(float(t) for t in K_orig)
        new_set = set(float(t) for t in K_new)
        # All 9 interior decade seams must be in K_new
        seams = {d * HORIZON_DAYS / 10.0 for d in range(1, 10)}
        missing = seams - new_set
        assert not missing, f'Decade seams missing: {missing}'
        # new_set must be a superset of orig_set
        assert orig_set <= new_set, f'Lost knots: {orig_set - new_set}'


# ─────────────────────────────────────────────────────────────────────────────
# GATE 2: Layer0→Layer1 equivalence
# ─────────────────────────────────────────────────────────────────────────────

class TestLayer0Layer1Equivalence:
    """DHARA_ENGINE_SPEC §2.3 / §5: |Δ ln_lambda| < 1e-12 at 50 sampled knots
    for each of the 6 calibrated event classes.

    EXPECTED DIFFERENCES under SM-R-7:
    ──────────────────────────────────────────────────────────────────────────
    All 6 classes in this fixture use routes with suppressed_by=('vedha:Sa->10',)
    OR suppressed_by=().  The only active vighna key is 'vedha:Sa->10'.

    career_change:
      Route rank-2 has suppressed_by=('vedha:Sa->10',).
      → suppressed_keys = {'vedha:Sa->10'}.
      → filtered_obs == obstructions (when vedha is active, its key IS included).
      → NO DIVERGENCE from live code.

    All other classes (childbirth, marriage, foreign_settlement, career_entry,
    death) use routes_no_suppression (suppressed_by=()) so:
      → suppressed_keys = {} (empty)
      → filtered_obs = {} (empty)
      → S_e(t) = 1.0 identically at every knot.
      Live code: passes the full obstructions dict (may be non-empty at t ∈ [250,270]).
      DIVERGENCE at knots in [250,270] where vedha is active:
        Layer1.ln_lambda will be HIGHER than terms_at().ln_lambda (no suppression).

    The test verifies equivalence only where filtered_obs == live_obstructions,
    and documents the SM-R-7 divergence for non-suppressed classes.
    ──────────────────────────────────────────────────────────────────────────
    """

    @staticmethod
    def _build_for_class(event_class: str) -> tuple[FieldEvaluator, 'Layer0']:
        if event_class == 'career_change':
            routes = _make_routes_with_suppression(event_class)
        else:
            routes = _make_routes_no_suppression(event_class)
        ev = _build_evaluator(event_class, routes=routes)
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        return ev, layer0

    def _sample_knots(self, K: np.ndarray, n: int = 50) -> list[int]:
        """Sample n knot indices reproducibly."""
        rng = np.random.default_rng(_RNG_SEED)
        indices = rng.choice(len(K), size=min(n, len(K)), replace=False)
        return sorted(indices.tolist())

    def _suppressed_keys_for_class(self, ev: FieldEvaluator, event_class: str) -> set[str]:
        """Keys appearing in any Route.suppressed_by for this class."""
        return {
            key
            for r in ev.promise.routes
            for key in r.suppressed_by
        }

    def test_equivalence_career_change(self):
        """career_change: filtered_obs == full obs → expect < 1e-12 everywhere."""
        ec = 'career_change'
        ev, layer0 = self._build_for_class(ec)
        routes = ev.promise.routes
        indices = self._sample_knots(layer0.knots)
        for idx in indices:
            t = float(layer0.knots[idx])
            expected = ev.terms_at(t).ln_lambda
            got = project_layer1(layer0, ec, routes, ev, idx)
            delta = abs(got - expected)
            assert delta < 1e-12, (
                f'career_change at knot[{idx}]=t={t:.4f}: '
                f'layer1={got!r} terms_at={expected!r} |Δ|={delta!r}'
            )

    @pytest.mark.parametrize('event_class', [
        'childbirth', 'marriage', 'foreign_settlement', 'career_entry', 'death',
    ])
    def test_equivalence_no_suppression_classes(self, event_class: str):
        """For classes with no suppressed routes: Layer1 uses S_e=1.0 (SM-R-7).

        At knots OUTSIDE the obstruction span [250,270]: no divergence.
        At knots INSIDE  the obstruction span [250,270]: divergence expected
          (layer1 > terms_at because layer1 correctly omits the unreferenced
          suppression, while terms_at passes it through).

        We test equivalence at knots OUTSIDE [250,270] only for these classes.
        """
        ev, layer0 = self._build_for_class(event_class)
        routes = ev.promise.routes
        indices = self._sample_knots(layer0.knots)
        # Filter to knots outside the obstruction active span [250, 270]
        outside_indices = [
            idx for idx in indices
            if not (250.0 <= float(layer0.knots[idx]) <= 270.0)
        ]
        assert len(outside_indices) >= 1, \
            f'No knots outside suppression span for {event_class}'
        for idx in outside_indices:
            t = float(layer0.knots[idx])
            expected = ev.terms_at(t).ln_lambda
            got = project_layer1(layer0, event_class, routes, ev, idx)
            delta = abs(got - expected)
            assert delta < 1e-12, (
                f'{event_class} at knot[{idx}]=t={t:.4f}: '
                f'layer1={got!r} terms_at={expected!r} |Δ|={delta!r}'
            )

    @pytest.mark.parametrize('event_class', [
        'childbirth', 'marriage', 'foreign_settlement', 'career_entry', 'death',
    ])
    def test_smr7_divergence_documented_for_no_suppression_classes(self, event_class: str):
        """SM-R-7 DIVERGENCE register: at t ∈ (250, 270) with active vedha,
        project_layer1 > terms_at (layer1 omits suppression per SM-R-7 ruling B).

        This is the CORRECT behavior per SM-R-7 OPTION B: a class whose routes
        reference no suppressed vighna keys should have S_e(t) = 1.0, not the
        value the live unfiltered code produces.
        """
        ev, layer0 = self._build_for_class(event_class)
        routes = ev.promise.routes
        # Find a knot strictly inside the obstruction span where vedha is active
        inside_indices = [
            idx for idx, t_val in enumerate(layer0.knots)
            if 250.0 < float(t_val) < 270.0
        ]
        if not inside_indices:
            pytest.skip(f'No knots inside obstruction span for {event_class}')

        idx = inside_indices[len(inside_indices) // 2]  # pick the midpoint
        t = float(layer0.knots[idx])
        terms_result = ev.terms_at(t).ln_lambda
        layer1_result = project_layer1(layer0, event_class, routes, ev, idx)

        # SM-R-7: layer1 should be HIGHER (less suppression) than the live code
        # because layer1 correctly filters to suppressed_keys = {} → S_e = 1.0
        assert layer1_result > terms_result, (
            f'{event_class} at t={t:.4f}: expected layer1={layer1_result!r} > '
            f'terms_at={terms_result!r} (SM-R-7 suppression fix should remove '
            'unreferenced suppression for classes with no suppressed routes)'
        )


# ─────────────────────────────────────────────────────────────────────────────
# GATE 3: SM-R-7 suppression filter isolation
# ─────────────────────────────────────────────────────────────────────────────

class TestSMR7SuppressionFilter:
    """DHARA_ENGINE_SPEC §5: shape_only class with no suppressed routes → S_e=1.0."""

    def test_no_suppressed_routes_gives_identity_suppression(self):
        """A class whose routes have no suppressed_by keys → S_e(t) = 1.0 always."""
        ec = 'some_shape_only_class'
        routes = _make_routes_no_suppression(ec)
        ev = _build_evaluator(ec, routes=routes)
        layer0 = compute_layer0(ev, HORIZON_DAYS)

        # At knots where vedha IS active (t ∈ [250, 270]):
        inside = [
            idx for idx, t_val in enumerate(layer0.knots)
            if 250.0 < float(t_val) < 270.0
        ]
        if not inside:
            pytest.skip('No inside-suppression-span knots in fixture')

        idx = inside[len(inside) // 2]
        result = project_layer1(layer0, ec, routes, ev, idx)

        # Manually compute what the result SHOULD be with S_e = 1.0:
        # ln_lambda = baseline + promise + clock + modifier + 0 (no suppression)
        t = float(layer0.knots[idx])
        terms = ev.terms_at(t)
        # Without suppression: ln_lambda_no_sup = terms.ln_lambda - terms.suppression_term_log
        sup_log = math.log(terms.suppression_term) if terms.suppression_term > 0 else 0.0
        expected_no_suppression = terms.ln_lambda - sup_log  # remove suppression contribution

        assert abs(result - expected_no_suppression) < 1e-12, (
            f'No-suppressed-routes class: expected ln_lambda without suppression='
            f'{expected_no_suppression!r}, got {result!r}'
        )

    def test_suppressed_routes_includes_only_referenced_vighna(self):
        """A class whose routes reference 'vedha:Sa->10' gets that obstruction only."""
        ec = 'career_change'
        routes = _make_routes_with_suppression(ec)
        ev = _build_evaluator(ec, routes=routes)
        layer0 = compute_layer0(ev, HORIZON_DAYS)

        # At a knot inside vedha's span, filtered_obs should equal full obstructions
        inside = [
            idx for idx, t_val in enumerate(layer0.knots)
            if 250.0 < float(t_val) < 270.0
        ]
        if not inside:
            pytest.skip('No inside-suppression-span knots in fixture')

        idx = inside[len(inside) // 2]
        result = project_layer1(layer0, ec, routes, ev, idx)
        expected = ev.terms_at(float(layer0.knots[idx])).ln_lambda
        assert abs(result - expected) < 1e-12, (
            f'career_change with suppression: expected {expected!r}, got {result!r}'
        )

    def test_layer0_obstructions_contains_all_vighna_keys(self):
        """Layer0.obstructions must contain ALL chart-level vighna keys
        (not filtered by class) — filtering is Layer1's job (SM-R-7 OPTION B).
        """
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        # The fixture has one obstructive primitive: 'vedha:Sa->10'
        assert 'vedha:Sa->10' in layer0.obstructions, (
            'Layer0 must store all chart-level vighna keys; '
            f'got keys: {sorted(layer0.obstructions.keys())}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# GATE 4: Layer0 field correctness
# ─────────────────────────────────────────────────────────────────────────────

class TestLayer0Fields:
    """Layer0 dataclass field shapes and content."""

    def test_knots_float64_sorted_unique(self):
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        assert layer0.knots.dtype == np.float64
        assert np.all(np.diff(layer0.knots) > 0), 'Knots must be strictly ascending'

    def test_covariates_shape(self):
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        N_k = len(layer0.knots)
        assert layer0.covariates.shape == (12, N_k), (
            f'covariates must be (12, N_k)={(12, N_k)}, '
            f'got {layer0.covariates.shape}'
        )

    def test_covariates_values_match_covariates_at(self):
        """For every knot, layer0.covariates[:, k] must equal covariates_at(knots[k])."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        rng = np.random.default_rng(_RNG_SEED)
        sample_indices = rng.choice(len(layer0.knots), size=min(20, len(layer0.knots)),
                                    replace=False)
        for idx in sample_indices:
            t = float(layer0.knots[idx])
            cov_dict = ev.envelopes.covariates_at(t)
            for j, key in enumerate(COVARIATE_KEYS):
                expected = cov_dict.get(key, 0.0)
                got = float(layer0.covariates[j, idx])
                # x3 (dual_reference_agreement) is derived from x1,x2
                if key == 'dual_reference_agreement':
                    from services.ka_kshetra.hazard import derive_dual_reference_agreement
                    expected = derive_dual_reference_agreement(cov_dict)
                assert abs(got - expected) < 1e-15, (
                    f'covariates[{j}={key}] at knot[{idx}]={t:.3f}: '
                    f'expected {expected!r}, got {got!r}'
                )

    def test_obstructions_values_match_obstructions_at(self):
        """For every knot, layer0.obstructions[key][k] must equal obstructions_at(knots[k])[key]."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        rng = np.random.default_rng(_RNG_SEED)
        sample_indices = rng.choice(len(layer0.knots), size=min(20, len(layer0.knots)),
                                    replace=False)
        for idx in sample_indices:
            t = float(layer0.knots[idx])
            obs_dict = ev.envelopes.obstructions_at(t)
            for key, arr in layer0.obstructions.items():
                expected = obs_dict.get(key, 0.0)
                got = float(arr[idx])
                assert abs(got - expected) < 1e-15, (
                    f'obstructions[{key!r}] at knot[{idx}]={t:.3f}: '
                    f'expected {expected!r}, got {got!r}'
                )

    def test_lord_stacks_keys_are_system_level_tuples(self):
        """lord_stacks keys must be (system_id, level) tuples."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        for key in layer0.lord_stacks:
            assert isinstance(key, tuple), f'lord_stacks key {key!r} must be a tuple'
            assert len(key) == 2, f'lord_stacks key must be (system_id, level): {key!r}'
            system_id, level = key
            assert isinstance(system_id, str), f'system_id must be str: {system_id!r}'
            assert isinstance(level, str), f'level must be str: {level!r}'

    def test_lord_stacks_values_match_lord_stacks_at(self):
        """lord_stacks[key][k] must equal the lord at that knot from lord_stacks_at."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        rng = np.random.default_rng(_RNG_SEED)
        sample_indices = rng.choice(len(layer0.knots), size=min(20, len(layer0.knots)),
                                    replace=False)
        for idx in sample_indices:
            t = float(layer0.knots[idx])
            stacks = ev.lord_stacks_at(t)
            for (sid, level), arr in layer0.lord_stacks.items():
                expected_lord = None
                if sid in stacks:
                    for lvl, lord in stacks[sid]:
                        if lvl == level:
                            expected_lord = lord
                            break
                stored_lord = arr[idx]  # May be '' for no-lord
                if expected_lord is None:
                    assert stored_lord == '', (
                        f'lord_stacks[({sid!r},{level!r})][{idx}] at t={t:.3f}: '
                        f'expected empty (no lord), got {stored_lord!r}'
                    )
                else:
                    assert stored_lord == expected_lord, (
                        f'lord_stacks[({sid!r},{level!r})][{idx}] at t={t:.3f}: '
                        f'expected {expected_lord!r}, got {stored_lord!r}'
                    )

    def test_layer0_is_frozen(self):
        """Layer0 must be a frozen dataclass (immutable)."""
        ev = _build_evaluator('career_change')
        layer0 = compute_layer0(ev, HORIZON_DAYS)
        with pytest.raises((AttributeError, TypeError)):
            layer0.knots = np.array([0.0, 1.0])  # type: ignore[misc]
