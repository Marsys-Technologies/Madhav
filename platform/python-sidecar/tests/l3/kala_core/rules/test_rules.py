from services.kala_core.rules import (
    admit,
    drishti_angles,
    read_ashtakavarga_bindu,
    read_path,
    registry_predicates,
)


def test_unqualified_kakshya_contributes_no_activity():
    admission = admit(
        prerequisites_satisfied=True,
        is_kakshya_crossing=True,
        av_bindu=None,
    )

    assert admission.admitted is False


def test_resolved_zero_bindu_is_not_missing():
    assert admit(
        prerequisites_satisfied=True,
        is_kakshya_crossing=True,
        av_bindu=0,
    ).admitted is True


def test_ashtakavarga_read_does_not_substitute_sav_or_duplicate_facts():
    assert read_ashtakavarga_bindu(
        [{"graha": "Saturn", "sign": "Aries", "bindu": 0, "sav": 28}],
        graha="Saturn",
        sign="Aries",
    ) == 0
    assert read_ashtakavarga_bindu(
        [{"graha": "Saturn", "sign": "Aries", "bindu": 4}] * 2,
        graha="Saturn",
        sign="Aries",
    ) is None


def test_nodes_cast_no_drishti_through_this_module():
    assert drishti_angles("Rahu") == ()


def test_rule_path_keeps_prerequisites_in_evaluation_order():
    path = read_path(
        {
            "path_id": "P5",
            "rule_version": "1.0.0",
            "prerequisites": [
                {"predicate_id": "second", "rule_version": "1", "evaluation_order": 2},
                {"predicate_id": "first", "rule_version": "1", "evaluation_order": 1},
            ],
            "soft_factors": [],
        }
    )

    assert [item.predicate_id for item in path.prerequisites] == ["first", "second"]


def test_registry_read_is_available_without_a_writer():
    assert {row["predicate_id"] for row in registry_predicates()} >= {"period_running_at"}
