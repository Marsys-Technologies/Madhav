"""test_n236_service_wiring.py: Earn.service_state from a declared, source-CHECKED service wiring (SS N-236).

bg_ephemeris_engine and bg_panchanga are table-less service probes. Their recorded health goes stale (a probe nobody re-ran in 30 days reads NO_DETECTOR). `service_wiring` is the checked form of "the probe exists and is
wired": the probe function exists (AST), the dispatcher routes the declared probe type to it (AST), the cockpit module lists the asset (text of the array). Every link is broken in turn and the cell must stop reading PASS.
Offline (a virtual file reader over the real sources).
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

DECL = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
AIDS = ("bg_ephemeris_engine", "bg_panchanga")
SP = "platform/python-sidecar/pipeline/orchestrator/service_probes.py"
TS = "platform/src/lib/cockpit/serviceProbeContract.ts"


def _reader(over=None):
    over = over or {}

    def rd(rel):
        if rel in over:
            return over[rel]
        p = ac.ROOT / rel
        return p.read_text(encoding="utf-8") if p.is_file() else None
    return rd


def _rec(aid, health="healthy", age=1005.0, ptype=None):
    return {aid: dict(asset_id=aid, service_health=health, probe_type=ptype or DECL[aid]["service_probe"]["probe_type"], selftest_age_hours=age)}


@pytest.mark.parametrize("aid", AIDS)
def test_the_real_declarations_are_sound_and_the_real_wiring_verifies(aid):
    assert ac.service_wiring_problem(DECL[aid]) is None
    ac.validate_service_wiring_declaration(aid, DECL[aid])
    w = ac.service_wiring_check(aid, DECL[aid])
    assert w["ok"] is True, w


@pytest.mark.parametrize("aid", AIDS)
def test_a_stale_healthy_record_with_verified_wiring_reads_partial_wired_is_not_working(aid):
    w = ac.service_wiring_check(aid, DECL[aid])
    g = ac.grade_service_state(aid, DECL[aid], _rec(aid, age=1005.0), w)
    assert g["v"] == ac.PARTIAL and g["basis"] == "wired-stale" and "STALE" in g["measured"] and "wired is not working" in g["measured"], g
    assert g["service_wiring"]["verified"] is True and g["service_wiring"]["stale_hours"] == 1005.0
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=1005.0), None)["v"] == ac.NO_DET   # without the declared form the stale record is exactly what it was


@pytest.mark.parametrize("aid", AIDS)
def test_the_fresh_window_is_24_hours_and_a_record_just_inside_passes_just_outside_is_partial(aid):
    w = ac.service_wiring_check(aid, DECL[aid])
    assert ac.SERVICE_FRESH_HOURS == 24
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=23.9), w)["v"] == ac.PASS
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=24.0), w)["v"] == ac.PASS
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=24.1), w)["v"] == ac.PARTIAL
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=300.0), w)["v"] == ac.PARTIAL      # the declared 720 h no longer widens a WIRED service's window


@pytest.mark.parametrize("aid", AIDS)
def test_a_fresh_healthy_record_passes_only_with_verified_wiring_or_within_its_declared_window(aid):
    w = ac.service_wiring_check(aid, DECL[aid])
    g = ac.grade_service_state(aid, DECL[aid], _rec(aid, age=3.0), w)
    assert g["v"] == ac.PASS and "basis" not in g and "within 24h" in g["measured"], g
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=3.0), None)["v"] == ac.PASS         # unwired service: the pre-existing rule


@pytest.mark.parametrize("health,expect", [("unhealthy", ac.FAIL), ("degraded", ac.PARTIAL), (None, ac.NO_DET), ("unknown", ac.NO_DET)])
def test_the_wiring_never_overrides_recorded_evidence(health, expect):
    aid = AIDS[0]
    w = ac.service_wiring_check(aid, DECL[aid])
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, health=health), w)["v"] == expect


def test_a_missing_or_future_selftest_time_stays_no_detector_even_when_wired():
    aid = AIDS[0]
    w = ac.service_wiring_check(aid, DECL[aid])
    for age in (None, -3.0, True):
        assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=age), w)["v"] == ac.NO_DET


def test_a_probe_type_the_registry_does_not_name_stays_no_detector():
    aid = AIDS[0]
    w = ac.service_wiring_check(aid, DECL[aid])
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, ptype="something_else"), w)["v"] == ac.NO_DET
    assert ac.grade_service_state(aid, DECL[aid], None, w)["v"] == ac.NO_DET                     # unreadable record


# ───────────────────────── FORGERY / MUTATION: break each link, the cell stops reading PASS ─────────────────────────

def _broken(aid, over):
    return ac.service_wiring_check(aid, DECL[aid], read=_reader(over))


def _must_not_pass(aid, w, why_has):
    assert w["ok"] is False and why_has in w["why"], w
    g = ac.grade_service_state(aid, DECL[aid], _rec(aid), w)
    assert g["v"] == ac.NO_DET and "NOT verified" in g["measured"], g
    assert ac.grade_service_state(aid, DECL[aid], _rec(aid, age=2.0), w)["v"] == ac.NO_DET        # not even a fresh healthy record passes a declared-but-broken wiring


@pytest.mark.parametrize("aid", AIDS)
def test_MUTATION_the_probe_function_is_renamed_or_removed(aid):
    fn = DECL[aid]["service_wiring"]["function"].split("::")[1]
    src = (ac.ROOT / SP).read_text(encoding="utf-8")
    _must_not_pass(aid, _broken(aid, {SP: src.replace(f"def {fn}(", "def _renamed_probe(")}), "defines no function")


@pytest.mark.parametrize("aid", AIDS)
def test_MUTATION_the_dispatch_branch_is_removed_or_points_elsewhere(aid):
    pt = DECL[aid]["service_probe"]["probe_type"]
    fn = DECL[aid]["service_wiring"]["function"].split("::")[1]
    src = (ac.ROOT / SP).read_text(encoding="utf-8")
    assert f'probe_type == "{pt}"' in src
    _must_not_pass(aid, _broken(aid, {SP: src.replace(f'probe_type == "{pt}"', 'probe_type == "nothing"')}), "does not reach the probe function")
    _must_not_pass(aid, _broken(aid, {SP: re.sub(rf"return {fn}\(probe_spec\)", "return {}", src)}), "does not reach the probe function")


@pytest.mark.parametrize("aid", AIDS)
def test_MUTATION_the_asset_is_dropped_from_the_cockpit_registration(aid):
    ts = (ac.ROOT / TS).read_text(encoding="utf-8")
    _must_not_pass(aid, _broken(aid, {TS: ts.replace(f"'{aid}',", "")}), "does not list")
    # the id merely appearing elsewhere in the module (a comment, another constant) is not the registration
    _must_not_pass(aid, _broken(aid, {TS: ts.replace(f"'{aid}',", "") + f"\n// {aid}\nexport const OTHER = ['{aid}']\n"}), "does not list")


def test_MUTATION_a_missing_file_or_a_syntax_error_is_not_wiring():
    aid = AIDS[0]
    assert _broken(aid, {SP: None})["ok"] is False
    assert _broken(aid, {SP: "def broken(:\n"})["ok"] is False
    assert _broken(aid, {TS: None})["ok"] is False


def test_FORGERY_a_declaration_naming_a_function_that_exists_elsewhere_is_not_the_probe():
    """The function exists, but the dispatcher routes the probe type to a DIFFERENT function: the declaration cannot make it the probe."""
    aid = AIDS[0]
    e = copy.deepcopy(DECL[aid])
    e["service_wiring"]["function"] = f"{SP}::_probe_panchanga_engine"
    w = ac.service_wiring_check(aid, e)
    assert w["ok"] is False and "does not reach the probe function" in w["why"], w


def test_FORGERY_malformed_declarations_are_refused_and_check_as_not_ok():
    aid = AIDS[0]
    for mut in (lambda e: e.pop("service_probe"), lambda e: e.__setitem__("kind", "data"),
                lambda e: e["service_wiring"].__setitem__("function", "not a ref"), lambda e: e["service_wiring"].__setitem__("registered_in", "x.py"),
                lambda e: e["service_wiring"].__setitem__("evidence", "unverified: looked fine"), lambda e: e["service_wiring"].__setitem__("evidence", "platform/no/such.py:1"),
                lambda e: e["service_wiring"].__setitem__("why", "ok"), lambda e: e["service_wiring"].__setitem__("extra", 1)):
        e = copy.deepcopy(DECL[aid])
        mut(e)
        assert ac.service_wiring_problem(e), e
        with pytest.raises(ac.DeclarationsError):
            ac.validate_service_wiring_declaration(aid, e)
        assert ac.service_wiring_check(aid, e)["ok"] is False


def test_the_registry_text_names_the_form():
    t = ac.CRITERION_REGISTRY["Earn.service_state"]["applicability"]
    assert "service_wiring" in t and "N-236" in t and "N-239" in t and "COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS" in t
