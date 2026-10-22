"""Oracle for the harness's trial-scoped class census (CENSUS_DIAG §3). Source of the rule: G8 steward GAPS-G8-G9 / migration 1306 header —
a generation must "claim EXACTLY the pinned classes"; for a deliberate slice the expected set is the trial's class list. Uses the REAL
`class_census_violations` from the checkout; only `_claimed_classes` (a DB read) is stubbed."""
import types

import pytest

vjmod = pytest.importorskip("services.gochara_kernel.verification_job")
import trial_slice  # noqa: E402

PIN26 = {"scored_classes": sorted(f"c{i:02d}" for i in range(26))}
TRIAL = ["c00", "c01", "c02", "c03"]


def _vj(claimed):
    return types.SimpleNamespace(VerificationRefused=vjmod.VerificationRefused, class_census_violations=vjmod.class_census_violations,
                                 _claimed_classes=lambda conn, chart_id, generation, found: sorted(set(claimed) | set(found)))


def _run(claimed, trial=TRIAL, vector=PIN26):
    trial_slice.make_trial_census(_vj(claimed), trial)(None, chart_id="x", generation="g", vector=vector, found=())


def test_exact_trial_claim_passes_against_26_pin():
    _run(TRIAL)


def test_production_census_refuses_the_same_slice():                     # the logged refusal: 22 missing, so the harness needs its own
    assert len(vjmod.class_census_violations(PIN26, TRIAL)) == 22


def test_lost_class_is_refused_by_name():
    with pytest.raises(vjmod.VerificationRefused) as e:
        _run(TRIAL[:3])
    assert e.value.code == "class_census_mismatch" and "c03" in e.value.detail


def test_stray_class_is_refused_by_name():
    with pytest.raises(vjmod.VerificationRefused) as e:
        _run(TRIAL + ["c09"])
    assert e.value.code == "class_census_mismatch" and "c09" in e.value.detail


def test_trial_class_outside_pin_is_refused():
    with pytest.raises(vjmod.VerificationRefused):
        _run(TRIAL + ["zz"], trial=TRIAL + ["zz"])
