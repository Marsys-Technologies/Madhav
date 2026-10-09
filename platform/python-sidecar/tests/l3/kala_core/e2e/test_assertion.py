"""K0a-4 envelope and evidence oracles; literals come from the pinned plan."""
import importlib.util
from copy import deepcopy

import pytest


def envelope():
    return dict(
        assertion_id="negative:window:11", chart_id="00000000-0000-0000-0000-000000000001",
        generation="candidate-a", stage="negative_space", method="fixture:vedha", rule_version="fixture-v1",
        subject={"event_class": "career", "affected_person": "native", "objects": ["SUN"]},
        frame="moon", period_anchor={"system": "vimshottari", "MD": "SAT", "AD": "MER", "applicability": "applicable"},
        interval={"t0": "2026-10-01T00:00:00Z", "t1": "2026-10-03T00:00:00Z"}, grain="day",
        resolution={"computation": "day", "source_licensed": "day", "empirically_supported": None},
        role="explains", roots={"record_ids": ["11"], "contact_ids": [], "fact_ids": []},
        derivation_parents=["judge:window:11"], used_for_selection=[],
        source={"text": "fixture judge window", "locator": "CODEX-K0a-4/window/11"},
        provenance="uncited_extension", operator_role="scored", null_reason=None, coverage_ref="fixture:coverage",
        precision={"method": "fixture-day", "delta_lambda": None, "delta_t": 86400}, input_vector_hash="a" * 64,
        payload={"kind": "negative_space", "exposure": "in_risk_set", "knowledge": "evaluated",
                 "rule_conclusion": "obstruction_present", "defeat_state": "cancelled",
                 "effective_state": "obstruction_cancelled", "measurement": "not_measured_here",
                 "what": "vedha", "by_what": "fixture protection", "release": {"kind": "unknown"}},
    )


def api():
    assert importlib.util.find_spec("services.kala_core.assertion"), "typed assertion envelope is missing"
    from services.kala_core.assertion import Assertion, increment_allowed
    return Assertion, increment_allowed


def test_envelope_carries_the_five_axes_without_a_score():
    Assertion, _ = api()
    assert Assertion.model_validate(envelope()).payload.effective_state == "obstruction_cancelled"


@pytest.mark.parametrize("mutant", ["generation_unpinned", "restated_l1", "missing_source_id", "cancelled_active"])
def test_invalid_envelope_mutations_are_refused(mutant):
    Assertion, _ = api()
    row = deepcopy(envelope())
    if mutant == "generation_unpinned": row["generation"] = ""
    if mutant == "restated_l1": row["subject"]["longitude_sidereal"] = 120
    if mutant == "missing_source_id": row["roots"]["record_ids"] = []
    if mutant == "cancelled_active": row["payload"]["effective_state"] = "obstruction_active"
    with pytest.raises(ValueError):
        Assertion.model_validate(row)


def test_testimony_and_selection_never_increment():
    Assertion, increment_allowed = api()
    row = envelope()
    row["operator_role"] = "testimony"
    assert increment_allowed(Assertion.model_validate(row), "11", set()) == 0
    row["operator_role"] = "scored"
    row["used_for_selection"] = ["11"]
    assert increment_allowed(Assertion.model_validate(row), "11", set()) == 0


def test_duplicate_root_and_stage_relocation_never_add_evidence():
    Assertion, increment_allowed = api()
    row = Assertion.model_validate(envelope())
    assert increment_allowed(row, "11", {"11"}) == 0
    assert increment_allowed(row, "11", set()) == 1


@pytest.mark.parametrize("stage", ["judge", "negative_space", "jury", "forecaster"])
def test_one_shared_envelope_for_every_stage(stage):
    api()
    from services.kala_core.assertion import AssertionEnvelope
    row = envelope()
    row.pop("payload")
    row["stage"] = stage
    assert AssertionEnvelope.model_validate(row).roots.record_ids == ("11",)


def test_unavailable_is_not_silent_and_unknown_release_is_honest():
    Assertion, _ = api()
    row = envelope()
    row["payload"].update(knowledge="unavailable", rule_conclusion="not_evaluated",
                          defeat_state="not_evaluated", effective_state="information_unavailable")
    assert Assertion.model_validate(row).payload.release.kind == "unknown"
    row["payload"]["effective_state"] = "evaluated_silent"
    with pytest.raises(ValueError):
        Assertion.model_validate(row)
