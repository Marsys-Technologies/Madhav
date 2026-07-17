"""
tests/l3/test_taranga_promise_formula.py — wave/D-3/T-3 PROMISE lock formula.

Covers:
  1. compute_promise — the five-factor product, clamped [0,1].
  2. nbry_deferral_semantics — the NBRY (Neecha-Bhanga) deferral-timing term,
     including the brief's illustrative "Venus-via-Mercury" type specimen:
     a Venus debility cancelled by Mercury shifts PROMISE-timing weight
     toward MERCURY's daśā periods, not Venus's.
  3. CR-87 required-chart-context checks on both compute_promise (via
     PromiseInputs) and nbry_deferral_semantics — chart_id must be a
     required parameter, never defaulted.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.taranga_kernel.promise import (
    PromiseInputs,
    compute_promise,
    nbry_deferral_semantics,
)

_ABHISEK_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


# ─── nbry_deferral_semantics ─────────────────────────────────────────────────

class TestNbryDeferralSemanticsVenusViaMercury:
    """The brief's illustrative type specimen: Venus debilitated in Virgo,
    cancelled by Mercury (nbry_rule_1_dispositor_kendra: Mercury as
    dispositor-of-debilitation-sign in a kendra) — PROMISE-timing weight
    must shift toward MERCURY's own daśā periods."""

    def test_active_during_cancellers_own_dasha(self):
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury"],
            dasha_lord="Mercury",
        )
        assert w == pytest.approx(1.0)

    def test_deferred_during_the_cancelled_planets_own_dasha(self):
        """During VENUS's own daśā — not Mercury's — the promise is deferred
        (present, but not at peak weight): this is the whole point of the
        'not just the debilitated planet's' semantics the brief names."""
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury"],
            dasha_lord="Venus",
        )
        assert w == pytest.approx(0.4)
        assert w < 1.0

    def test_deferred_during_an_unrelated_dasha(self):
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury"],
            dasha_lord="Saturn",
        )
        assert w == pytest.approx(0.4)

    def test_deferred_when_dasha_lord_unresolved(self):
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury"],
            dasha_lord=None,
        )
        assert w == pytest.approx(0.4)

    def test_active_when_any_of_multiple_cancellers_is_the_dasha_lord(self):
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury", "Jupiter"],
            dasha_lord="Jupiter",
        )
        assert w == pytest.approx(1.0)

    def test_custom_weights_are_respected(self):
        w = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID,
            cancelled_planet="Venus",
            canceller_planets=["Mercury"],
            dasha_lord="Mercury",
            active_weight=0.9,
            inactive_weight=0.2,
        )
        assert w == pytest.approx(0.9)


class TestNbryDeferralSemanticsGuards:
    def test_empty_canceller_planets_raises(self):
        with pytest.raises(ValueError):
            nbry_deferral_semantics(
                chart_id=_ABHISEK_CHART_ID,
                cancelled_planet="Venus",
                canceller_planets=[],
                dasha_lord="Mercury",
            )

    def test_cancelled_planet_in_canceller_planets_raises(self):
        """A planet cannot cancel its own debility under this codebase's
        classical NBRY rules — ga_yoga_writer.py's nbry_rule_* functions
        never return the debilitated planet as its own supporting_planet."""
        with pytest.raises(ValueError):
            nbry_deferral_semantics(
                chart_id=_ABHISEK_CHART_ID,
                cancelled_planet="Venus",
                canceller_planets=["Venus"],
                dasha_lord="Venus",
            )

    def test_missing_chart_id_raises(self):
        with pytest.raises(ValueError):
            nbry_deferral_semantics(
                chart_id="",
                cancelled_planet="Venus",
                canceller_planets=["Mercury"],
                dasha_lord="Mercury",
            )

    def test_chart_id_is_a_required_positional_or_keyword_param_with_no_default(self):
        sig = inspect.signature(nbry_deferral_semantics)
        assert sig.parameters["chart_id"].default is inspect.Parameter.empty


# ─── compute_promise ──────────────────────────────────────────────────────────

class TestComputePromise:
    def test_all_neutral_factors_product(self):
        inputs = PromiseInputs(
            chart_id=_ABHISEK_CHART_ID,
            salience=0.8,
            functional_valence=0.6,
            varga_ratification=1.2,
            nbry_deferral=1.0,
            mechanism_graph_weight=1.0,
        )
        expected = max(0.0, min(1.0, 0.8 * 0.6 * 1.2 * 1.0 * 1.0))
        assert compute_promise(inputs) == pytest.approx(expected)

    def test_negative_functional_valence_clamps_to_zero_not_negative(self):
        """A malefic functional-lordship configuration (signed negative
        valence) must never surface as a negative PROMISE — clamps to 0.0
        (no promise), never re-signed or inverted."""
        inputs = PromiseInputs(
            chart_id=_ABHISEK_CHART_ID,
            salience=0.9,
            functional_valence=-0.7,
            varga_ratification=1.1,
            nbry_deferral=1.0,
            mechanism_graph_weight=1.5,
        )
        assert compute_promise(inputs) == pytest.approx(0.0)

    def test_high_terms_clamp_to_one_not_above(self):
        inputs = PromiseInputs(
            chart_id=_ABHISEK_CHART_ID,
            salience=1.0,
            functional_valence=1.0,
            varga_ratification=1.4,
            nbry_deferral=1.0,
            mechanism_graph_weight=2.0,
        )
        # raw product = 1*1*1.4*1*2 = 2.8 -> clamps to 1.0
        assert compute_promise(inputs) == pytest.approx(1.0)

    def test_nbry_deferral_term_actually_moves_the_score(self):
        """Concrete demonstration that wiring nbry_deferral_semantics'
        output into PROMISE actually changes the timing-facing score between
        the canceller's own dasha and any other dasha — this is the CR-88
        payoff: PROMISE is no longer a flat 0.5-defaulted dignity_score."""
        base_kwargs = dict(
            chart_id=_ABHISEK_CHART_ID,
            salience=0.7,
            functional_valence=0.6,
            varga_ratification=1.0,
            mechanism_graph_weight=1.0,
        )
        during_mercury = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID, cancelled_planet="Venus",
            canceller_planets=["Mercury"], dasha_lord="Mercury",
        )
        during_saturn = nbry_deferral_semantics(
            chart_id=_ABHISEK_CHART_ID, cancelled_planet="Venus",
            canceller_planets=["Mercury"], dasha_lord="Saturn",
        )
        promise_mercury = compute_promise(PromiseInputs(nbry_deferral=during_mercury, **base_kwargs))
        promise_saturn = compute_promise(PromiseInputs(nbry_deferral=during_saturn, **base_kwargs))
        assert promise_mercury > promise_saturn
        # Not a flat 0.5 default anywhere in this chain (CR-88's failure mode).
        assert promise_mercury != 0.5
        assert promise_saturn != 0.5


class TestPromiseInputsCR87Shape:
    def test_missing_chart_id_raises(self):
        with pytest.raises(ValueError):
            PromiseInputs(
                chart_id="",
                salience=0.5, functional_valence=0.5, varga_ratification=1.0,
                nbry_deferral=1.0, mechanism_graph_weight=1.0,
            )

    def test_chart_id_is_a_required_field_with_no_default(self):
        sig = inspect.signature(PromiseInputs.__init__)
        assert sig.parameters["chart_id"].default is inspect.Parameter.empty

    def test_two_charts_same_raw_factors_are_independently_traceable(self):
        """Not a numeric-divergence guard (the factors are identical here by
        construction) — proves chart_id survives untouched as a distinguishing
        identity on the inputs object, so a caller building a PROMISE batch
        across two charts can never silently conflate which chart a given
        PromiseInputs came from."""
        common = dict(salience=0.5, functional_valence=0.5, varga_ratification=1.0,
                       nbry_deferral=1.0, mechanism_graph_weight=1.0)
        a = PromiseInputs(chart_id=_ABHISEK_CHART_ID, **common)
        b = PromiseInputs(chart_id=_ABHINANDAN_CHART_ID, **common)
        assert a.chart_id != b.chart_id
        assert compute_promise(a) == compute_promise(b)  # same math, different provenance
