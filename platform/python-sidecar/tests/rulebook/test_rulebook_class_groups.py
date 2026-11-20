"""CR-007-WAVE2-ENABLEMENT-20261028: the 13 Wave-2 class groups follow the original 7, in this exact order,
in the v1.2 schema, the compiler and the harness schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.rulebook import compiler
from services.rulebook import constants as C
from services.rulebook.compiler import compile_card
from services.rulebook.schema import load_schema, validate_card

from . import _cards as K

EXPECTED = [
    "illness_chronic_surgery",
    "relocation_travel",
    "major_gain",
    "major_loss",
    "career_adv_change_entry",
    "business_launch",
    "cross_cutting",
    "marriage_relationship_begin",
    "separation_relationship_end",
    "bereavement_parent",
    "childbirth_progeny",
    "education_learning",
    "achievement_recognition",
    "deception_fraud",
    "foreign_residence",
    "parent_affairs_non_death",
    "property_acquisition",
    "mental_distress",
    "spiritual_renunciation",
    "career_setback",
]
HARNESS_SCHEMA = Path(
    "/Users/Dev/scratch.noindex/claude/madhav/20261027-rulebook-prereq/harness/RULE_CARD_SCHEMA_v1_2.json"
)


def _enums(schema):
    f2 = schema["$defs"]["card"]["properties"]["field2_target_scope"]["properties"]
    return f2["class_group"]["enum"], f2["class_groups"]["items"]["enum"]


def test_repo_enums_in_order():
    single, multi = _enums(load_schema())
    assert single == EXPECTED and multi == EXPECTED
    assert list(C.CLASS_GROUPS) == EXPECTED
    assert compiler._CLASS_GROUPS == frozenset(EXPECTED)


@pytest.mark.parametrize("group", EXPECTED[7:])
def test_wave2_groups_validate_and_compile(group):
    card = K.natal_card()
    card["field2_target_scope"]["class_group"] = group
    assert validate_card(card) == []
    r = compile_card(card)
    assert r.status == "active" and r.ir["class_groups"] == [group]
    v12 = K.v12(K.natal_card())
    v12["field2_target_scope"].pop("class_group")
    v12["field2_target_scope"]["class_groups"] = [group, "cross_cutting"]
    assert validate_card(v12) == []


def test_unknown_group_still_rejected():
    card = K.natal_card()
    card["field2_target_scope"]["class_group"] = "career_setbacks"
    assert validate_card(card)


@pytest.mark.skipif(not HARNESS_SCHEMA.exists(), reason="harness scratch path not present (CI)")
def test_repo_enum_equals_harness_enum():
    harness = json.loads(HARNESS_SCHEMA.read_text(encoding="utf-8"))
    assert _enums(harness) == _enums(load_schema())
