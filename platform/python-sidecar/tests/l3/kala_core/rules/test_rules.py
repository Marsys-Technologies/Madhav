from services.kala_core.rules import (
    admit,
    drishti_angles,
    read_ashtakavarga_bindu,
    read_path,
    registry_predicates,
)
from services.gochara_kernel import rule_registry


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


def test_negative_bindu_is_unqualified_not_an_activity_operand():
    assert read_ashtakavarga_bindu(
        [{"graha": "Saturn", "sign": "Aries", "bindu": -1}],
        graha="Saturn",
        sign="Aries",
    ) is None
    assert admit(
        prerequisites_satisfied=True,
        is_kakshya_crossing=True,
        av_bindu=read_ashtakavarga_bindu(
            [{"graha": "Saturn", "sign": "Aries", "bindu": -1}],
            graha="Saturn",
            sign="Aries",
        ),
    ).admitted is False


def test_unsatisfied_prerequisite_refuses_admission():
    admission = admit(prerequisites_satisfied=False)

    assert (admission.admitted, admission.reason) == (False, "prerequisite_unsatisfied")


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


def test_rule_path_keeps_member_versions_and_kernel_registry_membership():
    row = next(row for row in rule_registry.path_rows() if row["path_id"] == "P5")
    path = read_path(row)

    assert [(item.predicate_id, item.version) for item in path.prerequisites] == [
        ("av_polarity_declaration_exists", "1.0.0")
    ]
    assert [(item.factor_id, item.version) for item in path.soft_factors] == [
        ("activity_kernel", "1.0.0")
    ]
    assert path.source_locators[0].source.startswith("BPHS ch.66")


def test_rule_path_uses_ordinal_and_member_versions_not_parent_version():
    path = read_path(
        {
            "path_id": "P5",
            "rule_version": "1.0.0",
            "prerequisites": [
                {"predicate_id": "second", "predicate_rule_version": "2.0.0", "ordinal": 2},
                {"predicate_id": "first", "predicate_rule_version": "3.0.0", "ordinal": 1},
            ],
            "soft_factors": [
                {"factor_id": "activity_kernel", "factor_rule_version": "1.2.0"},
            ],
        }
    )

    assert [(item.predicate_id, item.version) for item in path.prerequisites] == [
        ("first", "3.0.0"), ("second", "2.0.0")
    ]
    assert path.soft_factors[0].version == "1.2.0"


def test_registry_read_is_available_without_a_writer():
    assert {row["predicate_id"] for row in registry_predicates()} >= {"period_running_at"}
