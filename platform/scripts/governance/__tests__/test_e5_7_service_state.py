"""test_e5_7_service_state.py: the real Earn.service_state detector (criterion revision 2).

A service's rows_written cannot tell healthy-and-idle from broken, so the detector reads the probe the asset DECLARES (`service_probe`:
probe_type, max_age_hours) against what the registry recorded when the engine ran that probe (service_health, last_selftest_at,
health_probe.probe_type): PASS = declared probe registered, healthy, fresh; FAIL = unhealthy; PARTIAL = degraded; NO_DETECTOR (naming what
is missing) otherwise. Offline: the registry read is a function (`service_records`) replaced by a fake; the committed rev-25 L0 census
file and the real declarations file are the fixtures. No database, no network.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402

REPO = HERE.parents[3]
L0_FILE = REPO / "00_ARCHITECTURE" / "control" / "census" / "asset_census_2026-10-04T193639+0530.json"
T0_MANIFEST = REPO / "00_ARCHITECTURE" / "control" / "NIRMANA_T0_MANIFEST_v1_1.json"
SERVICES = {"bg_panchanga": "panchanga_engine", "bg_ephemeris_engine": "ephemeris_engine"}
PASS, FAIL, PARTIAL, NO_DET = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET


def decl(ptype="panchanga_engine", hours=720):
    return {"kind": "service", "service_probe": dict(probe_type=ptype, max_age_hours=hours)}


def rec(aid="s", ptype="panchanga_engine", health="healthy", age=5.0):
    return {aid: dict(asset_id=aid, service_health=health, probe_type=ptype, selftest_age_hours=age)}


def grade(d=None, r=None, aid="s"):
    return ac.grade_service_state(aid, decl() if d is None else d, rec() if r is None else r)


# ───────────────────────── the grader ─────────────────────────

def test_pass_when_declared_probe_is_registered_healthy_and_fresh():
    g = grade()
    assert g["v"] == PASS and "healthy and fresh" in g["measured"] and "panchanga_engine" in g["measured"]


def test_pass_at_exactly_the_declared_age():
    assert grade(r=rec(age=720))["v"] == PASS and grade(r=rec(age=720.01))["v"] == NO_DET


def test_unhealthy_reads_fail_and_degraded_reads_partial():
    assert grade(r=rec(health="unhealthy"))["v"] == FAIL and "recorded unhealthy" in grade(r=rec(health="unhealthy"))["measured"]
    assert grade(r=rec(health="degraded"))["v"] == PARTIAL


def test_unhealthy_is_fail_even_when_stale():
    assert grade(r=rec(health="unhealthy", age=9999))["v"] == FAIL


@pytest.mark.parametrize("d,r,needle", [
    ({"kind": "service"}, None, "no `service_probe` declaration"),
    (None if False else {"kind": "service", "service_probe": None}, None, "no `service_probe` declaration"),
    ({"kind": "service", "service_probe": {"probe_type": "panchanga_engine"}}, None, "malformed"),
    ({"kind": "service", "service_probe": {"probe_type": "panchanga_engine", "max_age_hours": True}}, None, "malformed"),
    ({"kind": "service", "service_probe": {"probe_type": "panchanga_engine", "max_age_hours": 0}}, None, "malformed"),
    (None, {}, "holds no active service-kind row"),
    (None, rec(ptype="other_probe"), "'other_probe'"),
    (None, rec(ptype=None), "None"),
    (None, rec(health=None), "never probed"),
    (None, rec(health="unknown"), "never probed"),
    (None, rec(age=None), "freshness cannot be told"),
    (None, rec(age=-3), "freshness cannot be told"),
    (None, rec(age=721), "stale"),
])
def test_no_detector_names_what_is_missing(d, r, needle):
    g = ac.grade_service_state("s", d if d is not None else decl(), r if r is not None else rec())
    assert g["v"] == NO_DET and g["measured"].startswith("NO_DETECTOR") and needle in g["measured"], g


def test_no_declarations_file_or_asset_entry_is_no_detector_never_pass():
    assert ac.grade_service_state("s", None, rec())["v"] == NO_DET
    assert ac.grade_service_state("s", "garbage", rec())["v"] == NO_DET


def test_unreadable_record_is_no_detector_never_healthy():
    g = ac.grade_service_state("s", decl(), None)
    assert g["v"] == NO_DET and "could not be read" in g["measured"]


def test_generic_no_asset_id_is_hard_coded():
    r = rec("zz_any_service", ptype="whatever_probe")
    assert ac.grade_service_state("zz_any_service", decl("whatever_probe", 24), r)["v"] == PASS
    assert ac.grade_service_state("zz_any_service", decl("whatever_probe", 24), rec("zz_any_service", "whatever_probe", age=25))["v"] == NO_DET


# ───────────────────────── the registry read ─────────────────────────

def test_service_records_reads_service_rows_of_the_layer_and_never_raises(monkeypatch):
    seen = []

    def fake(sql):
        seen.append(sql)
        return json.dumps([{"asset_id": "bg_x", "service_health": "healthy", "probe_type": "p", "selftest_age_hours": 1.5}])
    monkeypatch.setattr(ac, "scalar", fake)
    out = ac.service_records("L0")
    assert out == {"bg_x": {"asset_id": "bg_x", "service_health": "healthy", "probe_type": "p", "selftest_age_hours": 1.5}}
    sql = seen[0]
    assert "asset_kind = 'service'" in sql and f"layer = '{ac.LAYERS['L0']['registry_layer']}'" in sql
    assert "service_health" in sql and "last_selftest_at" in sql and "health_probe->>'probe_type'" in sql
    assert sql.lstrip().upper().startswith("SELECT") and "UPDATE" not in sql.upper().split("FROM")[0]

    def boom(sql):
        raise RuntimeError("psql: connection to host=10.0.0.9 refused")
    monkeypatch.setattr(ac, "scalar", boom)
    assert ac.service_records("L0") is None                  # unreadable: None, the reason (which could carry a host) is not echoed


# ───────────────────────── measure() and the rollup, on real fixtures ─────────────────────────

def test_measure_grades_registry_services_only_and_reads_the_record_once(monkeypatch, tmp_path):
    reg = {"s1": na_causes._reg_row("s1", asset_kind="service"), "s2": na_causes._reg_row("s2", asset_kind="service"),
           "s3": na_causes._reg_row("s3", asset_kind="service"), "d": na_causes._reg_row("d", asset_kind="data"),
           "u": na_causes._reg_row("u", asset_kind="data")}
    declared = {"s1": decl("p1"), "s2": decl("p2"), "s3": {"kind": "service"}, "d": {"kind": "data"}, "u": {"kind": None}}
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: declared)
    calls = []
    monkeypatch.setattr(ac, "service_records", lambda layer: calls.append(layer) or {
        **rec("s1", "p1"), **rec("s2", "p2", health="unhealthy")})
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["s1"]["Earn.service_state"]["v"] == PASS
    assert ms["s2"]["Earn.service_state"]["v"] == FAIL
    assert ms["s3"]["Earn.service_state"]["v"] == NO_DET and "no `service_probe` declaration" in ms["s3"]["Earn.service_state"]["measured"]
    assert ms["d"]["Earn.service_state"]["v"] == ac.NA and ms["d"]["Earn.service_state"]["cause"] == "not-a-service"   # a data kind stays the ruled N/A
    assert "Earn.service_state" not in ms["u"]                  # undeclared, not a registry service: unchanged
    assert calls == ["L0"]


def test_measure_reads_no_service_record_when_the_layer_has_no_service(monkeypatch, tmp_path):
    na_causes._stub_layer(monkeypatch, tmp_path, {"d": na_causes._reg_row("d", asset_kind="data")})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"d": {"kind": "data"}})
    monkeypatch.setattr(ac, "service_records", lambda layer: pytest.fail("no service in the layer: nothing to read"))
    ac.measure("L0")


def test_measure_with_unreadable_record_reads_no_detector(monkeypatch, tmp_path):
    na_causes._stub_layer(monkeypatch, tmp_path, {"s": na_causes._reg_row("s", asset_kind="service")})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"s": decl()})
    monkeypatch.setattr(ac, "service_records", lambda layer: None)
    ms = ac.measure("L0")["assets"][0]["measurements"]
    assert ms["Earn.service_state"]["v"] == NO_DET and "could not be read" in ms["Earn.service_state"]["measured"]


def _real_l0_assets():
    d = json.loads(L0_FILE.read_text(encoding="utf-8"))
    return {a["asset_id"]: a for a in d["L0"]["assets"]}, d["rollup"]["layers"]["L0"]


def _cell(cells, crit):
    return next(c for g in cells.values() for c in g["checks"] if c["criterion"] == crit)


def test_real_rev25_census_the_two_services_read_no_detector_before_and_now_read_by_record():
    assets, rolled = _real_l0_assets()
    assert set(SERVICES) <= set(assets)
    declarations = ac.load_asset_declarations()
    for aid, ptype in SERVICES.items():
        a = assets[aid]
        assert a["asset_kind"] == "service" and "Earn.service_state" not in a["measurements"]
        assert _cell(rolled[aid], "Earn.service_state")["v"] == NO_DET             # the committed census: undetected
        facts = dict(asset_kind=a["asset_kind"], columns=a["target_columns"])
        for health, age, want in (("healthy", 3.0, PASS), ("unhealthy", 3.0, FAIL), ("healthy", 800.0, NO_DET), (None, None, NO_DET)):
            m = copy.deepcopy(a["measurements"])
            m["Earn.service_state"] = ac.grade_service_state(aid, declarations[aid], rec(aid, ptype, health, age))
            cells = ac.rollup_asset("L0", m, facts)
            assert _cell(cells, "Earn.service_state")["v"] == want, (aid, health, age)
            # nothing else in the asset's rollup moved: every other criterion keeps its committed verdict
            for g in rolled[aid].values():
                for c in g["checks"]:
                    if c["criterion"] != "Earn.service_state":
                        assert _cell(cells, c["criterion"])["v"] == c["v"], (aid, c["criterion"])


def test_real_rev25_census_no_declaration_for_the_service_reads_no_detector_naming_it():
    assets, _ = _real_l0_assets()
    for aid in SERVICES:
        g = ac.grade_service_state(aid, {"kind": "service"}, rec(aid, SERVICES[aid]))
        assert g["v"] == NO_DET and aid in g["measured"] and "service_probe" in g["measured"]


def test_real_declarations_name_the_registered_probe_of_each_l0_service():
    """The declared probe_type is the one the registry's health_probe carries (the T0 manifest is the committed copy of those registry rows)."""
    declarations = ac.load_asset_declarations()
    m = json.loads(T0_MANIFEST.read_text(encoding="utf-8"))
    probes = {}

    def walk(o):
        if isinstance(o, dict):
            hp = (o.get("registry_contract") or {}).get("health_probe")
            if o.get("asset_id") in SERVICES and isinstance(hp, dict):
                probes[o["asset_id"]] = hp.get("probe_type")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(m)
    assert probes == SERVICES
    for aid, ptype in SERVICES.items():
        sp = declarations[aid]["service_probe"]
        assert sp["probe_type"] == ptype == probes[aid] and isinstance(sp["max_age_hours"], int)
    assert [a for a, e in declarations.items() if e.get("service_probe") is not None and e.get("kind") != "service"] == []


def test_other_service_kind_assets_without_a_declaration_stay_no_detector():
    d = ac.load_asset_declarations()
    undeclared = [a for a, e in d.items() if e.get("kind") == "service" and a not in SERVICES]
    assert undeclared                                         # the six other services: not this task's declarations
    for a in undeclared:
        assert ac.grade_service_state(a, d[a], rec(a))["v"] == NO_DET


# ───────────────────────── the declaration schema ─────────────────────────

def _doc(entry):
    return dict(version="1.0.0", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_s": entry})


GOOD = dict(probe_type="panchanga_engine", max_age_hours=720,
            why="read against the registered health probe the engine runs as the service build",
            evidence="platform/python-sidecar/pipeline/orchestrator/service_probes.py:169")


def test_validator_accepts_a_good_declaration_and_the_fields_list():
    ac.validate_declarations(_doc(dict(kind="service", service_probe=GOOD)))
    d = _doc(dict(kind="service", service_probe=GOOD))
    d["service_probe_declaration_fields"] = list(ac.SERVICE_PROBE_DECL_FIELDS)
    ac.validate_declarations(d)
    d["service_probe_declaration_fields"] = ["probe_type"]
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(d)


@pytest.mark.parametrize("mut,needle", [
    (lambda e: e.update(kind="data"), "only for a declared kind 'service'"),
    (lambda e: e.update(kind=None), "only for a declared kind 'service'"),
    (lambda e: e["service_probe"].update(max_age_hours=0), "max_age_hours"),
    (lambda e: e["service_probe"].update(max_age_hours=True), "max_age_hours"),
    (lambda e: e["service_probe"].update(max_age_hours=ac.SERVICE_MAX_AGE_HOURS_CAP + 1), "max_age_hours"),
    (lambda e: e["service_probe"].update(max_age_hours="720"), "max_age_hours"),
    (lambda e: e["service_probe"].update(probe_type="not a name"), "probe_type"),
    (lambda e: e["service_probe"].update(probe_type=None), "probe_type"),
    (lambda e: e["service_probe"].update(why="tbd"), "why"),
    (lambda e: e["service_probe"].update(evidence="no/such/file.py:1"), "evidence"),
    (lambda e: e["service_probe"].update(verdict="PASS"), "unknown field"),       # a declaration never states a verdict
    (lambda e: e.update(service_probe="panchanga_engine"), "must be an object"),
])
def test_validator_refuses(mut, needle):
    e = dict(kind="service", service_probe=copy.deepcopy(GOOD))
    mut(e)
    with pytest.raises(ac.DeclarationsError, match=needle):
        ac.validate_declarations(_doc(e))


def test_the_registry_entry_is_a_real_detector_at_revision_2():
    e = ac.CRITERION_REGISTRY["Earn.service_state"]
    assert e["revision"] == 2 and e["detector"] != "NONE" and e["asset_kinds"] == ("service",)
    assert "service_probe" in e["applicability"]
