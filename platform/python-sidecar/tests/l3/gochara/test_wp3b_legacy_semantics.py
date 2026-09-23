"""WP3b — factor-by-factor equivalence of the span-aware legacy algebra.

Two independent specifications of the same scoring algebra are compared
here, exactly as WP3b's exit gate requires:

  (A) tests/l3/gochara/oracle.py — the WP2 hand-specified factorized scorer
      oracle (pinned formula, pinned ±5-day box, noisy-OR).
  (B) services/gochara_kernel/legacy_semantics.py — the span-aware
      reproduction of the served gochara_v3 engine's pre-fix semantics.

Every WP2 oracle example (E1-E4) is pushed through BOTH and must agree
exactly. In addition, golden cases demonstrate each classified artifact
(F-08 exception->0.0->active and the step function, F-09 fixture-on-served-
path, F-10 era truncation + decade-edge declaration, F-11 unknown-as-clear,
plateau first-point retention) — each REPRODUCED and LABELLED, never fixed
(fixing is WP5's job).

A final test performs the real-behavior equivalence check (deliverable D):
one engine function from services.gochara_v3 run against this reproduction
on identical synthetic inputs. If the heavy import fails, the check reports
NOT_RUN with the error (earned-signal principle — never a faked pass).
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

import pytest

# Load legacy_semantics by file path: the gochara_kernel package __init__ is
# being built concurrently by WP3a, so importing through the package would
# couple this baseline to another workstream's in-flight module set.
import importlib.util as _ilu
import sys as _sys

_LS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "services", "gochara_kernel", "legacy_semantics.py",
)
_spec = _ilu.spec_from_file_location("wp3b_legacy_semantics", os.path.abspath(_LS_PATH))
LS = _ilu.module_from_spec(_spec)
_sys.modules[_spec.name] = LS  # dataclasses resolves annotations via sys.modules
_spec.loader.exec_module(LS)

from tests.l3.gochara.oracle import score_lambda

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "wp2_honesty.json")

DAY = 1.0  # JD units: 1 day
T0 = 2461042.0  # 2026-01-01 noon UTC (threshold.py:81 reference)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Oracle <-> legacy_semantics equivalence on the WP2 matrix (E1-E4)
# ---------------------------------------------------------------------------

class TestOracleEquivalence:
    """The two independent specifications must agree exactly on the WP2
    hand-worked examples (WP2_FIXTURES.md §9)."""

    def test_e1_single_exact_episode_lambda_0_8(self):
        t_exact = datetime(2026, 3, 1, tzinfo=timezone.utc)
        # Oracle episode: linear motion through exact, decay 1.0 at t_exact.
        oracle_factors = {
            "promise": 0.8, "permission": 1.0, "tara_modifier": 1.0,
            "w30_modifier": 1.0, "quality_gates": 1.0, "channel": "benefic",
            "episodes": [{
                "t_in": _iso(t_exact - timedelta(days=10)),
                "t_exact": _iso(t_exact),
                "t_out": _iso(t_exact + timedelta(days=10)),
                "speed_deg_per_day": 0.05, "orb_max_deg": 1.0,
            }],
            "query_span": [_iso(t_exact), _iso(t_exact)],
        }
        oracle = score_lambda(oracle_factors)
        assert oracle["state"] == "ok"
        assert oracle["activity"] == 1.0
        assert oracle["lambda_raw"] == pytest.approx(0.8)
        assert oracle["lambda_signed"] == pytest.approx(0.8)

        # Legacy reproduction: same instant queried span-aware. An exact
        # contact (orb 0 at the event) has orb_decay 1.0; the contribution
        # lives over [t_exact - 5d, t_exact + 5d] and the query instant
        # sits at the box centre.
        sentence = LS.Sentence(
            primitive="degree_contact",
            target_ref="wp2synth.target",
            transit_planet="Jupiter",
            event_jd=T0,
            detail={"orb_degrees": 0.0},
        )
        activity, contributions = LS.legacy_activity_at(
            [sentence], {"wp2synth.target": 1.0}, T0,
        )
        assert len(contributions) == 1
        assert contributions[0]["orb_decay"] == 1.0
        assert contributions[0]["p_i"] == pytest.approx(1.0)
        assert activity == pytest.approx(oracle["activity"])

        assembled = LS.assemble_lambda_v3(
            promise=0.8, permission=1.0, activity=activity,
            tara_modifier=1.0, w30_modifier=1.0, quality_gates=1.0,
            is_adverse=False,
        )
        assert assembled["lambda_raw"] == pytest.approx(oracle["lambda_raw"])
        assert assembled["lambda_signed"] == pytest.approx(oracle["lambda_signed"])

    def test_e2_query_outside_box_lambda_0(self):
        t_exact = datetime(2026, 3, 1, tzinfo=timezone.utc)
        q = t_exact + timedelta(days=8)
        oracle = score_lambda({
            "promise": 0.8, "permission": 1.0, "tara_modifier": 1.0,
            "w30_modifier": 1.0, "quality_gates": 1.0, "channel": "benefic",
            "episodes": [{
                "t_in": _iso(t_exact - timedelta(days=10)),
                "t_exact": _iso(t_exact),
                "t_out": _iso(t_exact + timedelta(days=10)),
                "speed_deg_per_day": 0.05, "orb_max_deg": 1.0,
            }],
            "query_span": [_iso(q), _iso(q)],
        })
        assert oracle["lambda_raw"] == 0.0

        sentence = LS.Sentence(
            primitive="degree_contact", target_ref="t", event_jd=T0,
            detail={"orb_degrees": 0.0},
        )
        activity, contributions = LS.legacy_activity_at(
            [sentence], {"t": 1.0}, T0 + 8.0,
        )
        assert contributions == []
        assert activity == 0.0

        box = LS.contribution_box(sentence)
        assert box == (T0 - 5.0, T0 + 5.0)  # the pinned ±5-day legacy box
        assert box[1] < T0 + 8.0  # 8 d > 5 d box -> empty clip at the query

    def test_e3_noisy_or_two_half_contributions_lambda_0_6(self):
        t_exact = datetime(2026, 3, 1, tzinfo=timezone.utc)
        q = t_exact + timedelta(days=5)  # decay = 1 - 0.1*5/1.0 = 0.5
        ep = {
            "t_in": _iso(t_exact - timedelta(days=10)),
            "t_exact": _iso(t_exact),
            "t_out": _iso(t_exact + timedelta(days=10)),
            "speed_deg_per_day": 0.1, "orb_max_deg": 1.0,
        }
        oracle = score_lambda({
            "promise": 0.8, "permission": 1.0, "tara_modifier": 1.0,
            "w30_modifier": 1.0, "quality_gates": 1.0, "channel": "benefic",
            "episodes": [dict(ep), dict(ep)],  # H-6: duplicate counts once
            "query_span": [_iso(q), _iso(q)],
        })
        # Pinned expectation (WP2 §9 E3): activity 0.75 — NOT 1.0 (noisy-OR,
        # not saturation-by-sum) and NOT 0.5 (independence).
        assert oracle["activity"] == pytest.approx(0.75)
        assert oracle["lambda_raw"] == pytest.approx(0.6)

        # Legacy reproduction at the same instant: each exact contact has
        # orb_decay 1.0 and (pinned legacy default) target_weight 0.5 ->
        # p_i = 0.5; the query instant is inside both ±5-day boxes.
        s1 = LS.Sentence(primitive="degree_contact", target_ref="a",
                         event_jd=T0, detail={"orb_degrees": 0.0})
        s2 = LS.Sentence(primitive="drishti_contact", target_ref="b",
                         event_jd=T0, detail={"orb_degrees": 0.0})
        activity, contributions = LS.legacy_activity_at(
            [s1, s2], {"a": 0.5, "b": 0.5}, T0 + 5.0,
        )
        assert sorted(c["p_i"] for c in contributions) == [0.5, 0.5]
        assert activity == pytest.approx(oracle["activity"])  # 0.75
        assembled = LS.assemble_lambda_v3(
            promise=0.8, permission=1.0, activity=activity,
            tara_modifier=1.0, w30_modifier=1.0, quality_gates=1.0,
        )
        assert assembled["lambda_raw"] == pytest.approx(oracle["lambda_raw"])  # 0.6

    def test_e4_quality_gates_none_unavailable(self):
        # Oracle honesty rule (WP2 §9 E4 / oracle.py:34-38).
        oracle = score_lambda({
            "promise": 0.8, "permission": 1.0, "tara_modifier": 1.0,
            "w30_modifier": 1.0, "quality_gates": None, "channel": "benefic",
            "episodes": [],
        })
        assert oracle["state"] == "unavailable"
        assert oracle["lambda_raw"] is None

        # Legacy engine semantics: W1.3 ALWAYS returns a float; the honest
        # 'unavailable' state does not exist on the legacy path. The
        # reproduction refuses None (mirroring the oracle's rule that an
        # unknown input is never silently treated as empty).
        with pytest.raises(ValueError):
            LS.assemble_lambda_v3(
                promise=0.8, permission=1.0, activity=0.0,
                tara_modifier=1.0, w30_modifier=1.0, quality_gates=None,
            )

    def test_orb_strength_preferred_over_orb_degrees(self):
        """orb_decay_from_detail mirrors engine.py:863-876 priority."""
        assert LS.orb_decay_from_detail({"orb_strength": 0.7}) == 0.7
        assert LS.orb_decay_from_detail({"orb_strength": 1.7}) == 1.0
        assert LS.orb_decay_from_detail({"orb_degrees": 2.5}) == pytest.approx(0.5)
        assert LS.orb_decay_from_detail({"orb_degrees": -9.0}) == 0.0
        assert LS.orb_decay_from_detail({}) == 0.5  # documented fallback

    def test_activity_primitive_filter_and_cancelled_vedha(self):
        """Mirrors engine.py:850-853: non-activity primitives skipped;
        cancelled gochara_vedha_pair excluded."""
        s_skip = LS.Sentence(primitive="av_threshold_state", target_ref="t",
                             event_jd=T0, detail={"orb_strength": 1.0})
        s_cancelled = LS.Sentence(
            primitive="gochara_vedha_pair", target_ref="t", event_jd=T0,
            detail={"cancelled": True, "orb_strength": 1.0},
        )
        s_live = LS.Sentence(primitive="degree_contact", target_ref="t",
                             event_jd=T0, detail={"orb_strength": 0.4})
        activity, detail, tb = LS.compute_activity_v3(
            [s_skip, s_cancelled, s_live], {"t": 1.0},
        )
        assert activity == pytest.approx(0.4)
        assert detail["sentence_count_active"] == 1
        assert tb == {"degree_contact": pytest.approx(0.4)}


# ---------------------------------------------------------------------------
# Factor golden cases (hand-specified, independent of the oracle)
# ---------------------------------------------------------------------------

class TestFactorGoldenCases:
    def test_promise_noisy_or(self):
        p0, _ = LS.compute_promise([])
        assert p0 == 0.0
        p1, _ = LS.compute_promise([0.5])
        assert p1 == pytest.approx(0.5)
        p2, _ = LS.compute_promise([0.5, 0.5])
        assert p2 == pytest.approx(0.75)  # noisy-OR, not sum
        p_clamp, _ = LS.compute_promise([1.5, -0.5])
        assert p_clamp == pytest.approx(1.0)  # clamped to [0,1]

    def test_permission_weighted_fraction(self):
        # SYSTEM_WEIGHTS sums to 1.0 (permission.py:100-114)
        assert sum(LS.SYSTEM_WEIGHTS.values()) == pytest.approx(1.0)
        assert LS.compute_permission({}) == 0.0
        assert LS.compute_permission({"vimshottari": True}) == pytest.approx(0.16)
        both = LS.compute_permission({"vimshottari": True, "sade_sati": True})
        assert both == pytest.approx(0.26)

    def test_tara_modifier_table(self):
        # w23_tara_bala.py:22-31 table, hand-checks:
        # natal nak 1, transit nak 3 -> position ((3-1) % 27) % 9 + 1 = 3 -> vipat 0.75
        tara, mod = LS.compute_tara(3, 1)
        assert tara == "vipat" and mod == 0.75
        # transit nak 1 (same as natal) -> janma 1.00
        tara, mod = LS.compute_tara(1, 1)
        assert tara == "janma" and mod == 1.0
        # transit nak 9 -> paramamitra 1.20
        tara, mod = LS.compute_tara(9, 1)
        assert tara == "paramamitra" and mod == 1.20
        # skip paths -> 1.0 (engine.py:598-612 honest skip)
        skip = LS.tara_modifier(None, 100.0)
        assert skip["modifier"] == 1.0 and skip["skipped"]
        # nakshatra index conversion: lon 0 -> nak 1
        assert LS.longitude_to_nakshatra_index(0.0) == 1
        assert LS.longitude_to_nakshatra_index(360.0 / 27.0) == 2

    def test_w30_modifier_geometric_mean(self):
        # rahu lon 10 deg -> rahu_sign 0 (Aries); ketu_sign 6 (Libra).
        # Aspected = {(0+4)%12=4, 6, 8, (6+4)=10, (6+6)=0, (6+8)=2}
        aspected = LS.w30_aspected_signs(0)
        assert aspected == frozenset({0, 2, 4, 6, 8, 10})
        # one target in Leo (sign 4): 5th from Rahu -> 1.05
        one = LS.w30_modifier(10.0, ["Leo"])
        assert one["modifier"] == pytest.approx(1.05)
        assert one["rahu_sign"] == 0 and one["ketu_sign"] == 6
        # two targets: Leo (1.05 via Rahu) + Aquarius (sign 10: 5th from
        # Ketu -> 1.05) -> geometric mean 1.05
        two = LS.w30_modifier(10.0, ["Leo", "Aquarius"])
        assert two["modifier"] == pytest.approx(1.05)
        # opposition: Aries itself (sign 0) is the 7th from Ketu -> 0.95
        opp = LS.w30_modifier(10.0, ["Aries"])
        assert opp["modifier"] == pytest.approx(0.95)
        # no targets aspected -> 1.0 passthrough
        none = LS.w30_modifier(10.0, ["Taurus"])
        assert none["modifier"] == 1.0 and not none["skipped"]

    def test_quality_gates_multiplicative_and_latta(self):
        scale = {1: "fear", 2: "grade_2", 3: "grade_3", 4: "grade_4", 5: "ignominy"}
        v1 = {"window_start": "2026-03-01", "window_end": "2026-03-20",
              "vedha_kind": "house_vedha", "graha": "saturn",
              "detail": {"malefic_count": 2}, "classical_citation": "x"}
        v2 = {"window_start": "2026-03-10", "window_end": "2026-03-30",
              "vedha_kind": "house_vedha", "graha": "mars",
              "detail": {"malefic_count": 0}, "classical_citation": "x"}
        qg, detail = LS.compute_quality_gates([v1, v2], "2026-03-05", "2026-03-15", scale)
        assert qg == pytest.approx(0.65 * 0.85)  # grade_2 * zero-malefic
        assert detail["vedha_fired_count"] == 2
        # non-overlapping row ignored
        v_far = {"window_start": "2027-01-01", "window_end": "2027-02-01",
                 "vedha_kind": "house_vedha", "graha": "mars",
                 "detail": {"malefic_count": 5}, "classical_citation": "x"}
        qg2, _ = LS.compute_quality_gates([v_far], "2026-03-05", "2026-03-15", scale)
        assert qg2 == 1.0  # F-11 unknown-as-clear: no overlap -> 1.0
        # latta path: effective malefic count 3 -> grade_3 -> 0.55
        vl = {"window_start": "2026-03-01", "window_end": "2026-03-20",
              "vedha_kind": "latta", "graha": "rahu", "detail": {},
              "classical_citation": "x"}
        qgl, _ = LS.compute_quality_gates([vl], "2026-03-05", "2026-03-15", scale)
        assert qgl == pytest.approx(0.55)

    def test_lambda_assembly_and_term_breakdown(self):
        out = LS.assemble_lambda_v3(
            promise=0.5, permission=0.5, activity=0.5,
            tara_modifier=1.1, w30_modifier=1.0, quality_gates=0.8,
        )
        # 0.5*0.5*0.5*1.1*1.0*0.8 = 0.11
        assert out["lambda_raw"] == pytest.approx(0.11)
        assert out["lambda_signed"] == pytest.approx(0.11)
        adverse = LS.assemble_lambda_v3(
            promise=0.5, permission=0.5, activity=0.5,
            tara_modifier=1.0, w30_modifier=1.0, quality_gates=0.8,
            is_adverse=True,
        )
        assert adverse["lambda_signed"] == pytest.approx(-0.1)
        tb = out["term_breakdown"]
        assert tb["formula"] == LS.TERM_BREAKDOWN_FORMULA
        assert tb["lambda_v3"] == round(out["lambda_raw"], 8)
        # clamping
        clamped = LS.assemble_lambda_v3(
            promise=1.0, permission=1.0, activity=1.0,
            tara_modifier=1.2, w30_modifier=1.05, quality_gates=1.0,
        )
        assert clamped["lambda_raw"] == 1.0


# ---------------------------------------------------------------------------
# Classified artifacts — each REPRODUCED and LABELLED (fixing is WP5's job)
# ---------------------------------------------------------------------------

class TestClassifiedArtifacts:
    def test_f08_exception_zero_certified_active(self):
        """F-08 / H-2: _eval_single swallows an evaluation exception and
        returns 0.0; the threshold predicate is >=, so with the
        all-zero-century distribution's lambda_thresh = 0.0 the FAILED
        evaluation is certified 'active'. REPRODUCED, labelled — not fixed.
        """
        def failing_eval(jd: float) -> float:
            raise RuntimeError("kakshya boundary row missing (wp2-synth-011)")

        # The exception path: legacy eval returns 0.0, not a raise.
        assert LS.eval_single_legacy(failing_eval, T0) == 0.0

        # Threshold from an all-zero distribution (e.g. every evaluation in
        # the century failed, or genuine zero activity): lambda_thresh=0.0.
        cfg = LS.compute_threshold_config([0.0] * 5200, base_rate=None)
        assert cfg.lambda_thresh == 0.0
        assert cfg.fallback_used is True

        # The certification: 0.0 >= 0.0 -> 'active' (threshold.py:386-393).
        lam = LS.eval_single_legacy(failing_eval, T0)
        assert LS.is_above_threshold(lam, cfg) is True  # ARTIFACT F-08

        # The honest contrast (WP2 case 11): the exception must propagate as
        # a failure state, never as a certified score. This is the contract
        # the baseline is measured against, NOT what the legacy engine does.
        with pytest.raises(RuntimeError):
            failing_eval(T0)

    def test_f08_step_function_activity(self):
        """F-08: legacy activity is a STEP — full contribution at any instant
        inside the ±5-day box, zero outside; no decay by |t - event|. The
        oracle's span-aware linear decay (max over the window) agrees at
        t_exact and at box-edge ONLY by construction; the plateau in
        between is the classified artifact. REPRODUCED, labelled."""
        s = LS.Sentence(primitive="degree_contact", target_ref="t",
                        event_jd=T0, detail={"orb_degrees": 0.0})
        w = {"t": 1.0}
        at_exact, _ = LS.legacy_activity_at([s], w, T0)
        at_edge, _ = LS.legacy_activity_at([s], w, T0 + 4.9)
        outside, _ = LS.legacy_activity_at([s], w, T0 + 5.1)
        assert at_exact == 1.0
        assert at_edge == 1.0   # ARTIFACT: undecayed 4.9 days from exact
        assert outside == 0.0   # hard cliff at the box boundary
        # box membership is inclusive at exactly ±5d
        at_boundary, _ = LS.legacy_activity_at([s], w, T0 + 5.0)
        assert at_boundary == 1.0

    def test_f09_fixture_on_served_path_and_saturation(self):
        """F-09: kakshya_cell_crossing runs on the served path with
        conn=None, degrading to the equal-eighths fixture
        (primitives.py:692-699); its sentences carry NO orb fields, so the
        activity term assigns the documented 0.5 fallback
        (engine.py:872-876); ~147 such sentences saturate noisy-OR to
        ~0.9996..1.0 (the F-15 measured band). REPRODUCED, labelled."""
        # The served-path fixture grid (primitives.py:693-696): 8 equal
        # 3.75-degree divisions per sign -- identical to L1's
        # ashtakavarga_kakshya_boundary grid (F-27), hence a provenance
        # swap changes the citation, not the numbers.
        sign_start = 240.0  # Sagittarius
        fixture_boundaries = [sign_start + i * (30.0 / 8.0) for i in range(8)]
        assert fixture_boundaries == [240.0, 243.75, 247.5, 251.25,
                                      255.0, 258.75, 262.5, 266.25]
        # A kakshya sentence as emitted on the served path (detail carries
        # boundary_deg/kakshya_index/source only — no orb_strength, no
        # orb_degrees):
        kak = LS.Sentence(
            primitive="kakshya_cell_crossing", target_ref="bhava:9",
            transit_planet="Saturn", event_jd=T0,
            detail={"boundary_deg": 243.75, "kakshya_index": 1,
                    "source": "equal_eighths_fixture_approximation"},
        )
        assert LS.orb_decay_from_detail(kak.detail) == 0.5  # documented fallback
        # Saturation demo: 147 sentences, p_i = 0.5 * weight(0.5 default)
        many = [LS.Sentence(primitive="kakshya_cell_crossing",
                            target_ref=f"bhava:{i % 12}", event_jd=T0,
                            detail={"source": "equal_eighths_fixture_approximation"})
                for i in range(147)]
        weights = {f"bhava:{i}": 0.5 for i in range(12)}
        activity, _, _ = LS.compute_activity_v3(many, weights)
        assert 0.999 <= activity <= 1.0  # the served [0.99964844, 1.0] band

    def test_f10_peak_cap_truncation(self):
        """F-10 / H-5: MAX_PEAKS_PER_ERA_WINDOW=3 truncates admitted peaks
        BEFORE persistence — truncation as absence. REPRODUCED, labelled.

        LEGACY BASELINE, SUPERSEDED (N-17/H-5, 2026-09-24,
        GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.2): this pins the FROZEN
        pre-H-5 semantics reproduced in services/gochara_kernel/
        legacy_semantics.py — the WP3b baseline, which must NOT be
        "modernised". The LIVE pipeline (services/gochara_v3/
        resolution_hierarchy.py) no longer caps or trims at admission:
        every admitted peak persists by default and the 90-day separation
        filter is an explicit serve-time trim parameter. See
        services/gochara_v3/tests/test_w33_resolution_hierarchy.py
        TestN17CapFreeAdmission for the live golden."""
        admitted = [LS.PeakCandidate(jd=float(T0 + 100 * i), lam=0.9 - 0.01 * i)
                    for i in range(6)]  # 6 well-separated candidates
        retained = LS.retain_candidates(admitted)
        assert len(retained) == 3  # the cap
        assert retained[0].lam == pytest.approx(0.9)  # highest first
        # separation enforcement: two candidates 10 days apart keep only
        # the higher one
        close = [LS.PeakCandidate(jd=T0, lam=0.8),
                 LS.PeakCandidate(jd=T0 + 10, lam=0.9)]
        retained_close = LS.retain_candidates(close)
        assert len(retained_close) == 1
        assert retained_close[0].lam == pytest.approx(0.9)

    def test_f10_era_window_declared_over_zero_score_range(self):
        """F-10 / H-3: when the coarse series starts above threshold, the
        era window's enter_jd is clamped to the sweep start with no check
        that the crossing is there — the window is declared over a range
        where lambda is below threshold. REPRODUCED, labelled."""
        # lambda above threshold ONLY in a narrow band away from the start;
        # the first coarse sample is inside the band's leading edge... to
        # force the artifact we make sample[0] above threshold but sample[1]
        # below: enter_jd must then be clamped to series[0].
        calls = []

        def eval_fn(jd: float) -> float:
            calls.append(jd)
            rel = jd - T0
            if rel < 0.0:
                return 0.0
            # above threshold only inside (0, 20)
            return 0.8 if 0.0 < rel < 20.0 else 0.1

        intervals, jds, lams = LS.find_threshold_crossings(
            eval_fn, T0, T0 + 100, lambda_thresh=0.5, return_series=True,
        )
        assert len(intervals) == 1
        # The true upward crossing is at rel=0.0 (T0); the artifact is that
        # enter_jd is fine here only because the series STARTS below.
        assert intervals[0].enter_jd >= T0
        # Now the artifact itself: series starts ABOVE (band begins before
        # the sweep range) -> enter_jd is clamped to the sweep start even
        # though the score at the sweep start... is above. The zero-range
        # declaration appears with the EXIT clamp: series ends above ->
        # exit_jd = last sample regardless of the true crossing.
        def eval_fn2(jd: float) -> float:
            rel = jd - T0
            return 0.8 if rel < 20.0 else 0.1  # above at the sweep start

        intervals2, _, _ = LS.find_threshold_crossings(
            eval_fn2, T0, T0 + 100, lambda_thresh=0.5, return_series=True,
        )
        assert len(intervals2) == 1
        # ARTIFACT: enter_jd is the first coarse sample (T0) — the era
        # window is declared from the sweep edge; the true crossing
        # predates the sweep and the declared window covers a range whose
        # boundary the sweep never measured.
        assert intervals2[0].enter_jd == pytest.approx(T0)

    def test_f11_overlay_absent_quality_gates_one(self):
        """F-11: an interval where the Vedha/Moorti overlay was never built
        (beyond its coverage) reads as quality_gates=1.0 — unknown-as-clear.
        REPRODUCED, labelled. (WP2 case 10's honest 'unavailable' is the
        oracle contract, not the legacy engine's.)"""
        with open(FIXTURES) as fh:
            case10 = json.load(fh)["cases"]["case_10_missing_overlay"]
        # Legacy: zero vedha rows overlap -> product stays 1.0.
        qg, detail = LS.compute_quality_gates(
            [], "2028-01-01", "2028-03-01", {1: "fear"},
        )
        assert qg == 1.0
        assert detail["vedha_fired_count"] == 0
        assert case10["expected"]["quality_gates"] is None  # honest contract
        assert case10["expected"]["quality_gates_defaulted_to_one"] is False

    def test_plateau_first_point_retention_legacy(self):
        """Legacy find_local_maxima admits a plateau's flat top EXACTLY ONCE,
        at its FIRST point (resolution_hierarchy.py:374-376, documented) —
        in tension with WP2 case 12's pinned tie-break (ALL tied maxima
        admitted, same rank). Classified DELIBERATE-legacy in
        WP3b_CLASSIFICATION.md (P-1); WP4 diffs against the new contract."""
        # ramp up to 1.0, flat 4 samples, ramp down (WP2 case 12 shape)
        lams = [0.5, 0.7, 0.9, 1.0, 1.0, 1.0, 1.0, 0.9, 0.7, 0.5]
        jds = [T0 + i for i in range(len(lams))]
        cands = LS.find_local_maxima(jds, lams)
        assert len(cands) == 1            # legacy: first plateau point only
        assert cands[0].jd == T0 + 3      # 2026-01-04 in series order
        assert cands[0].lam == 1.0

    def test_decade_slices_whole_decade_era_ranges(self):
        """F-10's era ranges: 10 decade slices of exactly 10*365.25 days
        from the birth epoch (writer:652-683)."""
        slices = LS.build_decade_slices(2445779.5, 1984)
        assert len(slices) == 10
        assert slices[0].era_slice_key == "g3_1984_1994"
        assert slices[0].start_jd == 2445779.5
        assert slices[0].end_jd == pytest.approx(2445779.5 + 10 * 365.25)
        assert slices[9].era_slice_key == "g3_2074_2084"
        for a, b in zip(slices, slices[1:]):
            assert b.start_jd == pytest.approx(a.end_jd)

    def test_threshold_percentile_formula(self):
        """threshold.py:293-304: P = 1 - base_rate, clamped to
        [0.05, 0.999]; lambda_thresh = P-th percentile (linear interp)."""
        cfg = LS.compute_threshold_config([0.1 * i for i in range(11)],
                                          base_rate=0.1)
        assert cfg.percentile_used == pytest.approx(0.9)
        # 90th percentile of 0.0..1.0 step 0.1 = 0.9
        assert cfg.lambda_thresh == pytest.approx(0.9)
        assert cfg.fallback_used is False
        # clamp: base_rate 0.9999 -> P clamps to 0.05
        cfg2 = LS.compute_threshold_config([0.5, 0.6], base_rate=0.9999)
        assert cfg2.percentile_used == 0.05
        # fallback path: UNIFORM_BASE_RATE=0.20 -> P=0.80
        cfg3 = LS.compute_threshold_config([0.2, 0.4, 0.6], base_rate=None)
        assert cfg3.fallback_used is True
        assert cfg3.density_flag == "no_base_rate"
        # P80 of {0.2,0.4,0.6}: rank 1.6 -> 0.52
        assert cfg3.lambda_thresh == pytest.approx(0.52)
        # explicit base_rate=0.5 -> P50 = 0.4 exactly
        cfg5 = LS.compute_threshold_config([0.2, 0.4, 0.6], base_rate=0.5)
        assert cfg5.percentile_used == 0.5
        assert cfg5.lambda_thresh == pytest.approx(0.4)
        # empty distribution -> 0.0 threshold (feeds the F-08 certification)
        cfg4 = LS.compute_threshold_config([], base_rate=None)
        assert cfg4.lambda_thresh == 0.0

    def test_wp2_honesty_fixture_negative_targets_have_no_algebra_filter(self):
        """F-19 (upstream, WP3c's fix): the scoring algebra has NO value
        filter — a negative-result sensitive-degree target fed to it would
        be scored like any other target. The baseline documents that the
        defect lives in the resonance target construction (pre-fix
        writer.py:293-301 built a target for EVERY check row), not in the
        algebra. WP3c R-1 removes the rows upstream."""
        with open(FIXTURES) as fh:
            case07 = json.load(fh)["cases"]["case_07_negative_sensitive_degree_zero_targets"]
        assert case07["expected"]["resolved_target_count"] == 0
        # The algebra would happily score any target it is handed:
        s = LS.Sentence(primitive="degree_contact",
                        target_ref=case07["inputs"]["resonance_rows"][0]["target_ref"],
                        event_jd=T0, detail={"orb_degrees": 0.0})
        activity, _ = LS.legacy_activity_at([s], {"wp2synth.moon.gandanta.check": 1.0}, T0)
        assert activity == 1.0  # no predicate filtering in the algebra


# ---------------------------------------------------------------------------
# Hierarchy end-to-end on a synthetic decade (pre-H-5 semantics)
# ---------------------------------------------------------------------------

class TestHierarchyEndToEnd:
    def test_hierarchy_builds_era_month_day(self):
        """A synthetic decade with one above-threshold band produces
        era + month + day tiers with the pooled 3-peak cap (pre-H-5)."""
        def eval_fn(jd: float) -> float:
            rel = jd - T0
            # one hump peaking at rel = 28 (sigma 12d), wide enough that
            # >=3 weekly coarse samples land inside the above-threshold
            # band with a rise-and-fall (21d, 28d, 35d at threshold 0.5)
            return 0.8 * math.exp(-((rel - 28.0) / 12.0) ** 2)

        result = LS.build_resolution_hierarchy(eval_fn, T0, T0 + 84, 0.5)
        assert result["era_window_count"] == 1
        era = result["era_windows"][0]
        assert era.enter_jd < 28 + T0 < era.exit_jd
        assert result["peaks_retained"] == 1
        assert len(result["month_windows"]) == 1
        assert len(result["day_windows"]) == 1
        day = result["day_windows"][0]
        month = result["month_windows"][0]
        assert day.parent_window_id == month.window_id
        assert month.parent_window_id == era.window_id
        assert day.enter_jd == day.exit_jd  # a single date (R8.6)
        # the day-refined peak sits at the hump's argmax (rel ~ 28)
        assert abs(day.peak_jd - (T0 + 28.0)) <= 1.0

    def test_eval_exception_inside_hierarchy_is_zero(self):
        """F-08 inside the hierarchy: an evaluator that raises partway is
        silently 0.0 at every failing sample — windows and peaks are built
        on the degraded series without any failure state surfacing."""
        def flaky(jd: float) -> float:
            if abs(jd - (T0 + 14.0)) < 0.01:  # one coarse sample raises
                raise RuntimeError("near_station_unresolved")
            return 0.8

        intervals, jds, lams = LS.find_threshold_crossings(
            flaky, T0, T0 + 28, 0.5, return_series=True,
        )
        assert 0.0 in lams  # the failed sample is indistinguishable from
        assert all(l == 0.8 or l == 0.0 for l in lams)  # genuine zero


# ---------------------------------------------------------------------------
# Deliverable D — real-behavior equivalence against services.gochara_v3
# ---------------------------------------------------------------------------

class TestRealBehaviorEquivalence:
    """Run ONE real engine function against the reproduction on identical
    synthetic inputs. If the heavy import fails, NOT_RUN with the error —
    never a faked pass (earned-signal principle)."""

    def test_engine_compute_activity_v3_agrees(self):
        pytest.importorskip("numpy", reason="engine needs numpy")
        try:
            from services.gochara_grammar.models import ConfigurationSentence
            from services.gochara_v3 import engine as real_engine
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"NOT_RUN: services.gochara_v3.engine import failed: {exc!r}")

        weights = {"t1": 1.0, "t2": 0.5, "t3": -0.8}
        real_sentences = [
            ConfigurationSentence(
                primitive="degree_contact", chart_id="wp2-synth", event_class="marriage",
                target_type="karaka", target_ref="t1", transit_planet="Jupiter",
                secondary_planet=None, event_jd=T0, event_datetime_ist="x",
                temporal_shape="point", fact_ids=[], classical_citation=None,
                uncited_extension=True,
                detail={"orb_strength": 0.7},
            ),
            ConfigurationSentence(
                primitive="drishti_contact", chart_id="wp2-synth", event_class="marriage",
                target_type="karaka", target_ref="t2", transit_planet="Saturn",
                secondary_planet=None, event_jd=T0, event_datetime_ist="x",
                temporal_shape="point", fact_ids=[],
                classical_citation="BPHS Ch.26 (Graha Drishti)",
                uncited_extension=False,
                detail={"orb_degrees": 2.5},
            ),
            ConfigurationSentence(
                primitive="sign_ingress", chart_id="wp2-synth", event_class="marriage",
                target_type="bhava", target_ref="t3", transit_planet="Mars",
                secondary_planet=None, event_jd=T0, event_datetime_ist="x",
                temporal_shape="point", fact_ids=[],
                classical_citation="BPHS Ch.29 (Gochara Phala)",
                uncited_extension=False,
                detail={},  # no orb info -> 0.5 fallback
            ),
            ConfigurationSentence(
                primitive="av_threshold_state", chart_id="wp2-synth",
                event_class="marriage", target_type="bhava", target_ref="t1",
                transit_planet="Saturn", secondary_planet=None, event_jd=T0,
                event_datetime_ist="x", temporal_shape="point", fact_ids=[],
                classical_citation="BPHS Ch.66-68 + Phaladeepika Ch.26",
                uncited_extension=False,
                detail={"orb_strength": 1.0},  # NOT an activity primitive
            ),
        ]
        real_activity, real_detail, real_tb = real_engine._compute_activity_v3(
            real_sentences, weights,
        )

        mine = [
            LS.Sentence(primitive=s.primitive, target_ref=s.target_ref,
                        transit_planet=s.transit_planet, event_jd=s.event_jd,
                        detail=dict(s.detail), event_datetime_ist=s.event_datetime_ist)
            for s in real_sentences
        ]
        my_activity, my_detail, my_tb = LS.compute_activity_v3(mine, weights)

        assert my_activity == pytest.approx(real_activity)
        assert my_tb.keys() == real_tb.keys()
        for k in real_tb:
            assert my_tb[k] == pytest.approx(real_tb[k]), f"term_breakdown[{k}]"
        assert my_detail["sentence_count_active"] == real_detail["sentence_count_active"]
        assert my_detail["sentence_count_total_gathered"] == real_detail["sentence_count_total_gathered"]

    def test_engine_threshold_predicate_agrees(self):
        """threshold.is_above_threshold (>=) against the reproduction."""
        try:
            from services.gochara_v3.threshold import (
                ThresholdConfig as RealCfg, is_above_threshold as real_above,
            )
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"NOT_RUN: services.gochara_v3.threshold import failed: {exc!r}")

        cfg = LS.compute_threshold_config([0.0] * 100, base_rate=None)
        real_cfg = RealCfg(
            percentile_used=cfg.percentile_used, lambda_thresh=cfg.lambda_thresh,
            implied_density=cfg.implied_density, base_rate_cited=cfg.base_rate_cited,
            age_band_used=cfg.age_band_used, density_flag=cfg.density_flag,
            fallback_used=cfg.fallback_used, sample_count=cfg.sample_count,
        )
        assert cfg.lambda_thresh == 0.0
        for lam in (0.0, 0.0001, 0.5, 1.0):
            assert LS.is_above_threshold(lam, cfg) == real_above(lam, real_cfg)
        # the F-08 edge: 0.0 >= 0.0 is True on BOTH sides (reproduced)
        assert real_above(0.0, real_cfg) is True
