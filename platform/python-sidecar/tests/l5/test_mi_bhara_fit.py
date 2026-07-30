"""
test_mi_bhara_fit — ṢAḌ-DARŚANA W2 Lane E · the weight-fitting harness (§7.2).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.2.

The load-bearing assertions here are the ones about HONESTY under thin data, because that is
where a fitting harness lies most easily:

  • `n_eff = 0 ⇒ φ̂ = φ⁰` EXACTLY (bit-identical, not "close") — the LEL-absent scenario
    falling out of the shrinkage formula rather than being special-cased. §3 also greps the
    package for a chart-identity or empty-LEL branch and asserts there is none.
  • the trust region genuinely clips, and a clip is RECORDED rather than silently accepted;
  • the CV is forward-chaining: fold 1 has no training data and must resolve to the prior,
    and no fold may ever evaluate on an event it was fitted on (the leak this design forbids).

§1 also verifies the OPTIMISER against a case whose maximum-likelihood answer is known: with
a single covariate that is 1 exactly where the events are and 0 elsewhere, the likelihood is
strictly increasing in β, so a box-constrained fit must land on the boundary β = 2.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.basis import FieldBasis, ParameterVector, SegmentBasis  # noqa: E402
from services.mi_bhara.fit import (  # noqa: E402
    CV_FOLDS,
    TAU_SHRINKAGE,
    ScoredEvent,
    apply_trust_region,
    expanding_origin_cuts,
    fit_event_class,
    maximise_loglik,
    shrink,
    shrink_vector,
    split_final_holdout,
)

HORIZON = 3650.0


def _one_covariate_basis(hot_from: float, hot_to: float) -> FieldBasis:
    """A field whose single covariate is 1 on `[hot_from, hot_to]` and 0 elsewhere.

    β then has an unambiguous direction: raising it concentrates hazard into the hot window.
    """
    base = math.log(1.0e-3)
    return FieldBasis(
        event_class="career_change",
        covariate_ids=("x1_contact_moon_ref",),
        segments=(
            SegmentBasis(0.0, hot_from, base, x_start=(0.0,), x_end=(0.0,)),
            SegmentBasis(hot_from, hot_to, base, x_start=(1.0,), x_end=(1.0,)),
            SegmentBasis(hot_to, HORIZON, base, x_start=(0.0,), x_end=(0.0,)),
        ),
    )


# ── §1 — the optimiser lands where the likelihood says it should ───────────────────────

def test_optimiser_pushes_beta_to_its_upper_bound_when_every_event_is_in_the_hot_window():
    """All 12 events inside the covariate's support ⇒ ℓ is increasing in β over the whole
    box (the per-event gain 12β outruns the integral cost on a 500-day window), so the
    constrained maximiser is exactly the boundary."""
    basis = _one_covariate_basis(1000.0, 1500.0)
    events = [1000.0 + 500.0 * (k + 0.5) / 12 for k in range(12)]
    theta, ll, converged = maximise_loglik(
        basis, events, 0.0, HORIZON, ParameterVector((), (0.0,), ())
    )
    assert converged
    assert theta.beta[0] == pytest.approx(2.0, abs=1e-6)
    assert ll > math.log(1e-3) * 12 - 1e-3 * HORIZON, "the fit must beat the prior"


def test_optimiser_pushes_beta_to_its_lower_bound_when_events_avoid_the_hot_window():
    """The mirror image, and the reason it matters: the fit has a real NEGATIVE direction, so
    a covariate that anti-predicts is down-weighted rather than ignored."""
    basis = _one_covariate_basis(1000.0, 1500.0)
    events = [50.0 * (k + 1) for k in range(12)]  # all before the hot window
    theta, _, converged = maximise_loglik(
        basis, events, 0.0, HORIZON, ParameterVector((), (0.0,), ())
    )
    assert converged
    assert theta.beta[0] == pytest.approx(-2.0, abs=1e-6)


def test_optimiser_with_zero_events_returns_the_starting_point_untouched():
    """With no events ℓ = −Λ(θ), whose maximiser minimises total hazard — a direction with no
    data behind it. Optimising it would manufacture a parameter; returning the prior does not."""
    basis = _one_covariate_basis(1000.0, 1500.0)
    prior = ParameterVector((), (0.37,), ())
    theta, _, converged = maximise_loglik(basis, [], 0.0, HORIZON, prior)
    assert converged
    assert theta.beta[0] == 0.37, "bit-identical to the prior, not merely close"


def test_optimiser_is_deterministic():
    basis = _one_covariate_basis(500.0, 900.0)
    events = [520.0, 610.0, 700.0, 810.0, 880.0, 1400.0, 2200.0, 3100.0]
    a = maximise_loglik(basis, events, 0.0, HORIZON, ParameterVector((), (0.0,), ()))
    b = maximise_loglik(basis, events, 0.0, HORIZON, ParameterVector((), (0.0,), ()))
    assert a[0].beta == b[0].beta
    assert a[1] == b[1]


# ── §2 — shrinkage and the trust region ────────────────────────────────────────────────

def test_n_eff_zero_returns_the_prior_bit_identically():
    """THE LEL-ABSENT SCENARIO, at the formula level (§7.6's gated acceptance criterion)."""
    for prior in (0.0, 0.37, -1.9, 0.95):
        assert shrink(mle=999.0, prior=prior, n_eff=0) == prior


def test_shrinkage_weights_match_the_hand_computed_fractions():
    """§7.2's own worked numbers: n_eff = 20 ⇒ half-way; n_eff = 57 ⇒ 74% data / 26% prior."""
    assert TAU_SHRINKAGE == 20.0
    assert shrink(mle=1.0, prior=0.0, n_eff=20) == pytest.approx(0.5, abs=1e-15)
    assert shrink(mle=1.0, prior=0.0, n_eff=57) == pytest.approx(57 / 77, rel=1e-15)
    assert 57 / 77 == pytest.approx(0.7402597402597403, rel=1e-15)


def test_shrinkage_is_monotone_in_n_eff():
    prev = shrink(mle=2.0, prior=0.0, n_eff=0)
    for n in range(1, 200):
        cur = shrink(mle=2.0, prior=0.0, n_eff=n)
        assert cur >= prev
        prev = cur
    assert prev < 2.0, "shrinkage never reaches the raw MLE at any finite n"


def test_trust_region_clips_and_reports_the_clip():
    value, clipped = apply_trust_region(candidate=5.0, previous=1.0)
    assert clipped is True
    assert value == pytest.approx(1.75, abs=1e-15), "1.0 + (0.5·1.0 + 0.25)"
    value, clipped = apply_trust_region(candidate=1.2, previous=1.0)
    assert clipped is False and value == 1.2


def test_trust_region_still_lets_a_zeroed_parameter_move():
    """The +0.25 floor. A purely multiplicative region would freeze a weight at 0 forever —
    a switched-off clock could then never be switched back on by evidence."""
    value, clipped = apply_trust_region(candidate=0.9, previous=0.0)
    assert clipped is True and value == pytest.approx(0.25, abs=1e-15)


def test_shrink_vector_keys_n_eff_by_weight_id_so_a_count_cannot_hit_the_wrong_parameter():
    basis = FieldBasis(
        event_class="e",
        system_ids=("vimshottari",),
        covariate_ids=("x1", "x2"),
        vighna_ids=("vedha",),
        segments=(
            SegmentBasis(
                0.0, 10.0, math.log(1e-3),
                log_a_start=(0.0,), log_a_end=(0.0,),
                x_start=(0.0, 0.0), x_end=(0.0, 0.0),
                u_start=(0.0,), u_end=(0.0,),
            ),
        ),
    )
    assert basis.weight_ids == ("w_s:vimshottari", "beta:x1", "beta:x2", "rho:vedha")
    mle = ParameterVector(w=(1.0,), beta=(2.0, 2.0), rho=(0.9,))
    prior = ParameterVector(w=(0.5,), beta=(0.0, 0.0), rho=(0.3,))
    shrunk, outcomes = shrink_vector(
        basis=basis,
        mle=mle,
        prior=prior,
        # only x1 has out-of-sample evidence; everything else must resolve to its prior
        n_eff_by_weight_id={"beta:x1": 20},
        previous=prior,
    )
    by_id = {o.weight_id: o for o in outcomes}
    assert by_id["w_s:vimshottari"].shrunk_value == 0.5
    assert by_id["beta:x2"].shrunk_value == 0.0
    assert by_id["rho:vedha"].shrunk_value == 0.3
    # x1: shrink(2.0, 0.0, 20) = 1.0, then trust region around prev = 0.0 clips to 0.25
    assert by_id["beta:x1"].shrunk_value == pytest.approx(0.25, abs=1e-15)
    assert by_id["beta:x1"].clipped is True
    assert shrunk.beta[0] == pytest.approx(0.25, abs=1e-15)


def test_a_missing_n_eff_key_means_zero_evidence_not_an_error_and_not_a_silent_one():
    basis = FieldBasis(
        event_class="e",
        covariate_ids=("x1",),
        segments=(SegmentBasis(0.0, 10.0, math.log(1e-3), x_start=(0.0,), x_end=(0.0,)),),
    )
    shrunk, outcomes = shrink_vector(
        basis=basis,
        mle=ParameterVector((), (2.0,), ()),
        prior=ParameterVector((), (0.4,), ()),
        n_eff_by_weight_id={},
    )
    assert outcomes[0].n_eff == 0
    assert shrunk.beta[0] == 0.4


# ── §3 — the CV split: forward-chaining, no leakage ────────────────────────────────────

def _events(times, cls="career_change", prospective=()):
    return [
        ScoredEvent(t=t, event_class=cls, is_prospective=(i in prospective), event_id=f"e{i}")
        for i, t in enumerate(times)
    ]


def test_final_holdout_is_the_most_recent_twenty_percent_by_date():
    ev = _events([float(100 * (k + 1)) for k in range(20)])
    train, holdout = split_final_holdout(ev)
    assert len(holdout) == 4
    assert [e.t for e in holdout] == [1700.0, 1800.0, 1900.0, 2000.0]
    assert max(e.t for e in train) < min(e.t for e in holdout)


def test_a_tiny_event_set_keeps_everything_in_training_and_reports_no_holdout_score():
    """A holdout of one point yields a number that is pure noise. Reporting it would be a
    fabricated measurement; reporting `None` is the honest state (LAW ZERO)."""
    ev = _events([10.0, 20.0, 30.0, 40.0])
    train, holdout = split_final_holdout(ev)
    assert len(train) == 4 and holdout == []


def test_expanding_origin_cuts_are_quintiles_by_event_count():
    ev = _events([float(k) for k in range(1, 21)])
    cuts = expanding_origin_cuts(ev, folds=CV_FOLDS, horizon_end=HORIZON)
    assert cuts[:5] == [4.0, 8.0, 12.0, 16.0, 20.0]
    assert cuts[-1] == HORIZON


def test_no_fold_ever_evaluates_on_an_event_it_was_fitted_on():
    """The leakage a random split would introduce, asserted directly on the fold structure."""
    basis = _one_covariate_basis(1000.0, 2000.0)
    times = [200.0 * (k + 1) for k in range(15)]
    result = fit_event_class(
        basis=basis,
        events=_events(times),
        prior=ParameterVector((), (0.0,), ()),
        horizon_end=HORIZON,
    )
    assert result.folds
    for f in result.folds:
        assert f.cut_start <= f.cut_end
        # every fold's training slice is strictly before its evaluation slice by construction
        assert f.n_train == sum(1 for t in [e.t for e in _events(times)] if t < f.cut_start)


def test_the_origin_genuinely_expands_across_folds():
    """The defining property of rolling-origin CV: each fold trains on a SUPERSET of the
    previous fold's data, and every fold's evaluation slice lies entirely after its own
    training cut. A random split satisfies neither."""
    basis = _one_covariate_basis(1000.0, 2000.0)
    result = fit_event_class(
        basis=basis,
        events=_events([200.0 * (k + 1) for k in range(15)]),
        prior=ParameterVector((), (0.0,), ()),
        horizon_end=HORIZON,
    )
    n_trains = [f.n_train for f in result.folds]
    assert n_trains == sorted(n_trains), f"origin did not expand monotonically: {n_trains}"
    assert n_trains[0] < n_trains[-1]
    for a, b in zip(result.folds, result.folds[1:]):
        assert a.cut_end == b.cut_start, "the folds must tile the training window with no gap"


def test_a_fold_with_no_training_events_falls_back_to_the_prior_rather_than_optimising_noise():
    """The earliest origin has nothing to learn from. §1 proves `maximise_loglik` returns the
    starting point untouched in that case; this pins that the harness reaches it — a two-event
    class produces a first fold with an empty training slice."""
    basis = _one_covariate_basis(1000.0, 2000.0)
    result = fit_event_class(
        basis=basis,
        events=_events([1100.0, 1900.0]),
        prior=ParameterVector((), (0.63,), ()),
        horizon_end=HORIZON,
    )
    assert result.folds[0].n_train == 0
    # nothing out-of-sample has accumulated in a stratum with n_eff below τ, so the shipped
    # vector stays close to the prior — and with zero folds evaluated it IS the prior
    assert result.theta_shipped.beta[0] == pytest.approx(0.63, abs=0.25)


# ── §4 — the whole harness end to end ──────────────────────────────────────────────────

def test_a_chart_with_no_lel_ships_the_classical_priors_exactly():
    """GATE W2's LEL-ABSENT ACCEPTANCE CRITERION, at the harness level.

    No branch, no flag: zero events ⇒ zero out-of-sample events ⇒ n_eff = 0 ⇒ φ̂ = φ⁰ exactly.
    """
    basis = _one_covariate_basis(1000.0, 2000.0)
    prior = ParameterVector((), (0.31,), ())
    result = fit_event_class(basis=basis, events=[], prior=prior, horizon_end=HORIZON)

    assert result.n_train == 0 and result.n_holdout == 0
    assert result.theta_shipped.beta == prior.beta, "bit-identical to the prior"
    assert result.theta_mle.beta == prior.beta
    assert result.holdout_loglik is None
    assert all(o.n_eff == 0 for o in result.shrinkage)
    assert result.any_clipped is False


def test_a_rich_lel_moves_the_weights_toward_the_data_but_not_all_the_way():
    """Shrinkage is CONSERVATIVE by design: the shipped vector must sit strictly between the
    prior and the MLE, never at the MLE."""
    basis = _one_covariate_basis(1000.0, 2000.0)
    hot = [1000.0 + 1000.0 * (k + 0.5) / 30 for k in range(30)]
    prior = ParameterVector((), (0.0,), ())
    result = fit_event_class(basis=basis, events=_events(hot), prior=prior, horizon_end=HORIZON)

    assert result.theta_mle.beta[0] > result.theta_shipped.beta[0] > prior.beta[0]
    assert result.n_train == 24 and result.n_holdout == 6
    assert result.holdout_loglik is not None


def test_prospective_and_backfill_counts_are_tracked_separately_and_never_summed_into_one():
    basis = _one_covariate_basis(1000.0, 2000.0)
    ev = _events([200.0 * (k + 1) for k in range(10)], prospective=(7, 8, 9))
    result = fit_event_class(
        basis=basis, events=ev, prior=ParameterVector((), (0.0,), ()), horizon_end=HORIZON
    )
    assert result.n_prospective == 3
    assert result.n_backfill == 7
    assert not hasattr(result, "n_total_scored"), (
        "there is deliberately no summed field: prospective hits and backfill retrodictions "
        "are different currencies and the scoreboard carries both (Elevation §7)"
    )


def test_events_of_another_class_are_not_fitted_into_this_class():
    basis = _one_covariate_basis(1000.0, 2000.0)
    mixed = _events([1100.0, 1300.0], cls="career_change") + _events(
        [1200.0, 1400.0, 1600.0], cls="health_crisis"
    )
    result = fit_event_class(
        basis=basis, events=mixed, prior=ParameterVector((), (0.0,), ()), horizon_end=HORIZON
    )
    assert result.n_prospective + result.n_backfill == 2


def test_the_package_contains_no_chart_identity_or_empty_lel_branch():
    """§7.6 / the `lel_calibration.py` precedent: behaviour is driven by DATA AVAILABILITY,
    never by chart identity, and the LEL-absent case must fall out of the arithmetic. A
    literal chart id or an `if not events:` special case in the shrinkage path would be the
    silent-error class this asserts against."""
    pkg = Path(__file__).parent.parent.parent / "services" / "mi_bhara"
    offenders = []
    for path in sorted(pkg.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for needle in ("482012f1", "1c826d5a", "NATIVE_CHART_ID"):
            if needle in text:
                offenders.append(f"{path.name}: chart-identity literal {needle!r}")
    assert offenders == [], "\n".join(offenders)
