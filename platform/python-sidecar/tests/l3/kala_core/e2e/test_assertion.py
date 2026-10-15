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


@pytest.mark.parametrize("system,lord", [
    ("vimshottari", "Aries"), ("chara", "SAT"), ("yogini", "MOON"),
    ("unknown_system", "SAT"), ("mula", "SAT"),
])
@pytest.mark.parametrize("level", ["MD", "AD", "PD"])
def test_period_anchor_refuses_unknown_or_wrong_kind_lords(system, lord, level):
    Assertion, _ = api()
    row = envelope()
    valid = {"chara": "Aries", "yogini": "Mangala"}.get(system, "SAT")
    row["period_anchor"].update(system=system, MD=valid, AD=valid, PD=valid)
    row["period_anchor"][level] = lord
    with pytest.raises(ValueError):
        Assertion.model_validate(row)


@pytest.mark.parametrize("frame", ["unrecognised_frame", "graha:Aries", "graha:unknown"])
def test_assertion_refuses_unknown_frames(frame):
    Assertion, _ = api()
    row = envelope()
    row["frame"] = frame
    with pytest.raises(ValueError):
        Assertion.model_validate(row)


@pytest.mark.parametrize("system,lord,canonical", [
    ("vimshottari", "Saturn", "SAT"), ("chara_karaka", "Aries", "Aries"),
    ("yogini", "Mangala", "Mangala"), ("kalachakra", "Cancer", "Cancer"),
])
def test_assertion_keeps_method_specific_lord_identities_on_the_wire(system, lord, canonical):
    Assertion, _ = api()
    row = envelope()
    row["period_anchor"].update(system=system, MD=lord, AD=lord, PD=lord)
    row["frame"] = "graha:Saturn"
    encoded = Assertion.model_validate(row).model_dump(mode="json")
    assert encoded["period_anchor"] == {
        "system": "chara" if system == "chara_karaka" else system,
        "MD": canonical, "AD": canonical, "PD": canonical, "applicability": "applicable",
    }
    assert encoded["frame"] == "graha:SAT"


@pytest.mark.parametrize("mutation", ["frame", "lord"])
def test_fixture_slice_refuses_bad_identities_before_candidate_writes(mutation):
    from types import SimpleNamespace
    from services.kala_core.assertion.slice import _run_fixture_slice

    class BoundCandidate:
        calls = 0

        def execute(self, query, params=()):
            self.calls += 1
            assert query.startswith("SELECT generation FROM kala_layer_candidate"), "invalid envelope reached storage"
            return SimpleNamespace(fetchone=lambda: ("candidate-a",))

    row = envelope()
    if mutation == "frame":
        row["frame"] = "unrecognised_frame"
    else:
        row["period_anchor"]["MD"] = "Aries"
    conn = BoundCandidate()
    ctx = SimpleNamespace(build_id="build", dry_run=False,
                          config={"chart_id": row["chart_id"], "kala_assertion_fixture": row})
    with pytest.raises(ValueError):
        _run_fixture_slice(ctx, conn)
    assert conn.calls == 1
