"""AM-13 (ruled): activity_kernel@1.1.0 applicability by object kind; P3/P4/P5 rule_version 1.1.0.
Assertions run the production registry and evaluator; nothing is re-implemented here."""
import copy

import pytest

from services.gochara_rules import registry
from services.gochara_rules import kernel_factor
from services.gochara_rules.kernel_factor import activity_kernel
from services.gochara_rules.registry import (
    ANGULAR_OBJECT_KINDS, FACTORS, KERNEL_VERSION, RULE_PATHS, RULE_VERSION, SPAN_OBJECT_KINDS,
    SUPERSEDED_FACTORS, SUPERSEDED_PATHS, composite_ref,
)

# the 1155 object-kind CHECK, read from the migration itself (not retyped)
def _db_object_kinds():
    import pathlib, re
    sql = (pathlib.Path(__file__).resolve().parents[4] / "migrations" / "1155_gochara_relationship_record.sql").read_text()
    m = re.search(r"kgrr_object_kind_ck CHECK \(object_kind IN\s*\((.*?)\)\)", sql, re.S)
    return set(re.findall(r"'([a-z_]+)'", m.group(1)))


def test_span_is_a_membership_step_not_unqualified():
    for kind in SPAN_OBJECT_KINDS:
        assert activity_kernel(kind, inside=True)["value"] == 1.0
        assert activity_kernel(kind, inside=False)["value"] == 0.0
    r = activity_kernel("house_span", inside=None)       # a missing membership operand is NOT silently anything
    assert r["value"] is None and r["reason"] == "span_membership_operand_missing"


def test_point_and_star_stay_unqualified_until_the_orb_is_a_recorded_decision():
    for kind in ANGULAR_OBJECT_KINDS:
        r = activity_kernel(kind, delta_lambda_deg=0.0)
        assert r["value"] is None and r["reason"] == "orb_not_ratified", kind
        assert r["null_state"] == "unqualified"
    # no caller can smuggle an orb in: the evaluator takes none, and the row's orb is None
    with pytest.raises(TypeError):
        activity_kernel("degree_point", delta_lambda_deg=0.0, orb_deg=5.0)   # type: ignore[call-arg]
    assert FACTORS[kernel_factor.FACTOR_REF]["applicability"]["angular"]["orb_deg"] is None


def test_once_an_orb_is_decided_the_angular_kernel_is_linear(monkeypatch):
    row = copy.deepcopy(FACTORS[kernel_factor.FACTOR_REF])
    row["applicability"]["angular"]["orb_deg"] = 2.0      # a stand-in decision, set ON THE ROW (the only legal place)
    monkeypatch.setitem(FACTORS, kernel_factor.FACTOR_REF, row)
    assert activity_kernel("degree_point", delta_lambda_deg=0.0)["value"] == 1.0
    assert activity_kernel("degree_point", delta_lambda_deg=1.0)["value"] == 0.5
    assert activity_kernel("star", delta_lambda_deg=-1.0)["value"] == 0.5
    assert activity_kernel("saham", delta_lambda_deg=3.0)["value"] == 0.0          # outside the orb: computed 0, not null
    assert activity_kernel("degree_point", delta_lambda_deg=None)["reason"] == "delta_lambda_operand_missing"
    assert activity_kernel("degree_point", delta_lambda_deg=float("nan"))["value"] is None


def test_uncovered_object_kinds_are_unqualified_never_one():
    for kind in ("varga_position", "no_such_kind"):
        r = activity_kernel(kind, inside=True, delta_lambda_deg=0.0)
        assert r["value"] is None and r["reason"] == "object_kind_not_covered_by_applicability"


def test_every_db_object_kind_is_classified_or_explicitly_left_out():
    declared = set(SPAN_OBJECT_KINDS) | set(ANGULAR_OBJECT_KINDS)
    left_out = _db_object_kinds() - declared
    assert declared <= _db_object_kinds()                     # no kind the DB would refuse
    assert left_out == {"varga_position"}                     # the ONE kind the ruling did not classify


def test_old_rows_are_untouched_and_new_versions_supersede_them():
    old = FACTORS[composite_ref("activity_kernel", RULE_VERSION)]
    assert "applicability" not in old and old["operand"] == "angular distance |Δλ| to exact contact"
    for fid in ("activity_kernel", "graduated_drishti"):
        assert SUPERSEDED_FACTORS[composite_ref(fid, RULE_VERSION)]["superseded_by"] == composite_ref(fid, KERNEL_VERSION)
    for pid in ("P3", "P4", "P5"):
        assert SUPERSEDED_PATHS[composite_ref(pid, RULE_VERSION)]["superseded_by"] == composite_ref(pid, KERNEL_VERSION)
        old_p, new_p = RULE_PATHS[composite_ref(pid, RULE_VERSION)], RULE_PATHS[composite_ref(pid, KERNEL_VERSION)]
        assert new_p["rule_version"] == KERNEL_VERSION
        assert new_p["prerequisites"] == old_p["prerequisites"]                       # predicates unchanged
        assert {k: v for k, v in new_p.items() if k not in ("rule_version", "soft_factors")} == \
               {k: v for k, v in old_p.items() if k not in ("rule_version", "soft_factors")}
        assert composite_ref("activity_kernel", KERNEL_VERSION) in new_p["soft_factors"]
        assert composite_ref("activity_kernel", RULE_VERSION) not in new_p["soft_factors"]
    assert composite_ref("graduated_drishti", KERNEL_VERSION) in RULE_PATHS[composite_ref("P3", KERNEL_VERSION)]["soft_factors"]
    # P1/P2/P6 are not touched
    for pid in ("P1", "P2", "P6"):
        assert composite_ref(pid, KERNEL_VERSION) not in RULE_PATHS


def test_every_soft_factor_reference_resolves():
    for key, path in RULE_PATHS.items():
        for ref in path.get("soft_factors", []):
            assert ref in FACTORS, (key, ref)


def test_graduated_drishti_declares_aspect_only_applicability():
    row = FACTORS[composite_ref("graduated_drishti", KERNEL_VERSION)]
    assert row["applicability"] == {"relations": ["aspect"]}
