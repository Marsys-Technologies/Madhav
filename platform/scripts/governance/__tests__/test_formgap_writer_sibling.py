"""test_formgap_writer_sibling.py: the `writer_sibling` form of Build.registered (SS N-203).

A registry sibling (kind `rider`, has_writer=false) whose writer class is its primary's: Build.registered used to read FAIL ("@register ... but registry says has_writer=false"). It reads PASS ONLY when the
declared primary is a registry asset with has_writer=true in the SAME writer file and is not itself a sibling, the declared tables include the sibling's target table and sit inside the primary writer's
produced set (its declared produced_tables when it declares any, AND the writer scan sees it write them). Every condition has a mutation; the registry is never flipped. Pure functions over what measure() knows,
plus the REAL writer scan of the two real primaries.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

PASS, FAIL, NO_DET = ac.PASS, ac.FAIL, ac.NO_DET
EV = "platform/python-sidecar/pipeline/orchestrator/writers/bg_medical_mappings.py:26"
W = "bg_medical_mappings.py"


def _ws(**kw):
    d = dict(primary="bg_medical_mappings", tables=["bg_nakshatra_medical"], why="the writer class of the primary is also registered as this asset and seeds its table in the same run", evidence=EV)
    d.update(kw)
    return d


def _entry(**kw):
    e = {"kind": "rider", "writer_sibling": _ws()}
    e.update(kw)
    return e


# ───────────────────────────── the validator ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.WRITER_SIBLING_FIELDS == ("primary", "tables", "why", "evidence") and "writer_sibling" in ac.DECL_FORMGAP_KEYS
    assert ac.writer_sibling_problem("bg_nakshatra_medical", _entry()) is None
    assert ac.writer_sibling_problem("bg_nakshatra_medical", {"kind": "data"}) is None


@pytest.mark.parametrize("ws,needle", [
    (_ws(extra=1), "exactly the fields"),
    ({k: v for k, v in _ws().items() if k != "why"}, "exactly the fields"),
    (_ws(primary="bg_nakshatra_medical"), "self-sibling"),
    (_ws(primary="Bad Id"), "primary must be"),
    (_ws(tables=[]), "1 to 8"),
    (_ws(tables=["a", "a"]), "1 to 8"),
    (_ws(tables=["bad table"]), "1 to 8"),
    (_ws(why="tbd"), "writer_sibling.why"),
    (_ws(evidence="unverified: it shares a writer somewhere"), "evidence"),
    (_ws(evidence="platform/scripts/governance/golden_test_scan.py:1"), "must name the sibling"),
])
def test_a_malformed_writer_sibling_is_refused(ws, needle):
    got = ac.writer_sibling_problem("bg_nakshatra_medical", _entry(writer_sibling=ws))
    assert got is not None and needle in got, got


@pytest.mark.parametrize("kind", ["data", "service", "static", None])
def test_only_a_declared_rider_may_claim_a_sibling_writer(kind):
    got = ac.writer_sibling_problem("bg_nakshatra_medical", _entry(kind=kind))
    assert got is not None and "kind `rider`" in got and "writer-built asset cannot claim" in got


def test_the_primary_may_not_itself_be_a_sibling_and_must_be_a_registry_asset():
    assets = {"a": _entry(writer_sibling=_ws(primary="b")), "b": _entry(writer_sibling=_ws(primary="c"))}
    assert "itself declares writer_sibling" in ac.writer_sibling_cross_problem(assets, {"a", "b", "c"})
    assert ac.writer_sibling_cross_problem({"a": _entry(writer_sibling=_ws(primary="b")), "b": {"kind": "data"}}, {"a", "b"}) is None
    assert "not in the census registry set" in ac.writer_sibling_cross_problem({"a": _entry(writer_sibling=_ws(primary="zzz"))}, {"a"})
    cyc = {"a": _entry(writer_sibling=_ws(primary="b")), "b": _entry(writer_sibling=_ws(primary="a"))}
    assert ac.writer_sibling_cross_problem(cyc, {"a", "b"}) is not None                                   # a cycle cannot form


def test_validate_declarations_refuses_a_bad_sibling_in_a_whole_document():
    doc = copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8")))
    doc["assets"]["bg_nakshatra_medical"]["writer_sibling"] = _ws(primary="bg_nakshatra_medical")
    with pytest.raises(ac.DeclarationsError, match="self-sibling"):
        ac.validate_declarations(doc)
    doc["assets"]["bg_nakshatra_medical"]["writer_sibling"] = _ws()
    doc["assets"]["bg_nakshatra_medical"]["kind"] = "data"
    with pytest.raises(ac.DeclarationsError, match="kind `rider`"):
        ac.validate_declarations(doc)
    doc["assets"]["bg_nakshatra_medical"]["kind"] = "rider"
    doc["assets"]["bg_medical_mappings"]["writer_sibling"] = _ws(primary="bg_nakshatra_medical")
    with pytest.raises(ac.DeclarationsError, match="itself declares writer_sibling"):
        ac.validate_declarations(doc)


# ───────────────────────────── the detector (pure, the writer scan stood in) ─────────────────────────────

SIB = dict(has_writer=False, target_table="bg_nakshatra_medical")
PRI = dict(has_writer=True, target_table="bg_medical_mappings")
PDECL = {"produced_tables": [{"table": "bg_medical_mappings"}, {"table": "bg_nakshatra_medical"}]}
SCAN = dict(written=["bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"], update_only=[], delete_only=[], complete=True)


def _rec(monkeypatch, r=SIB, files=(W,), ws=None, preg=PRI, pfiles=(W,), pdecl=PDECL, scan=SCAN):
    monkeypatch.setattr(ac, "produced_set_written", lambda a, f: scan if not isinstance(scan, Exception) else (_ for _ in ()).throw(scan))
    return ac.writer_sibling_record("bg_nakshatra_medical", dict(r), list(files), ws or _ws(), preg, list(pfiles), pdecl)


def test_PASS_when_every_condition_holds_and_the_registry_is_not_flipped(monkeypatch):
    got = _rec(monkeypatch)
    assert got["v"] == PASS and "has_writer=false and is not flipped" in got["measured"] and "inside the primary's declared produced_tables" in got["measured"]
    b = got["writer_sibling"]
    assert b["verified"] is True and b["primary"] == "bg_medical_mappings" and b["scan_complete"] is True and SIB["has_writer"] is False


def test_PASS_with_no_declared_produced_set_says_the_scan_is_the_only_evidence(monkeypatch):
    got = _rec(monkeypatch, pdecl={"kind": "data"})
    assert got["v"] == PASS and "the primary declares no produced_tables, so the scan is the only produced-set evidence" in got["measured"] and got["writer_sibling"]["declared_produced"] is None


@pytest.mark.parametrize("kw,needle", [
    (dict(r=dict(SIB, has_writer=True)), "a writer-built asset cannot claim a sibling writer"),                       # a writer-built claimant
    (dict(files=()), "no @register names it"),
    (dict(files=(W, "other.py")), "registered in 2 files"),
    (dict(preg=None), "not a registered asset"),
    (dict(preg=dict(PRI, has_writer=False)), "has has_writer=false in the registry"),                                   # a primary without a writer
    (dict(pdecl=dict(PDECL, writer_sibling=_ws())), "itself a declared sibling"),
    (dict(pfiles=("bg_other.py",)), "do not share a writer class"),
    (dict(r=dict(SIB, target_table="bg_sign_medical")), "does not include the asset's own target table"),
    (dict(pdecl={"produced_tables": [{"table": "bg_medical_mappings"}]}), "outside the declared produced_tables"),      # a table outside the primary's declared produced set
    (dict(scan=dict(SCAN, written=["bg_medical_mappings"])), "does not see it write bg_nakshatra_medical"),            # the scan does not see the primary write it
])
def test_FAIL_names_the_reason(monkeypatch, kw, needle):
    got = _rec(monkeypatch, **kw)
    assert got["v"] == FAIL and needle in got["measured"], got


def test_an_incomplete_scan_is_no_detector_never_pass(monkeypatch):
    got = _rec(monkeypatch, scan=dict(SCAN, written=["bg_medical_mappings"], complete=False))
    assert got["v"] == NO_DET and "incomplete" in got["measured"]
    got = _rec(monkeypatch, scan=ac.Unknown("the writer file could not be read"))
    assert got["v"] == NO_DET and "could not be read" in got["measured"]
    got = _rec(monkeypatch, scan=dict(SCAN, complete=False))                                                          # incomplete but the table IS seen written: proven
    assert got["v"] == PASS


def test_an_update_only_table_counts_as_written_by_the_primary(monkeypatch):
    assert _rec(monkeypatch, scan=dict(SCAN, written=["bg_medical_mappings"], update_only=["bg_nakshatra_medical"]))["v"] == PASS


# ───────────────────────────── the real writer scan of the two real primaries ─────────────────────────────

def test_REAL_SCAN_the_two_primaries_write_their_siblings_tables():
    reg = ac.registered_ids("")
    a = ac.produced_set_written("bg_medical_mappings", reg["bg_medical_mappings"])
    b = ac.produced_set_written("bg_transit_rules", reg["bg_transit_rules"])
    assert a["complete"] and {"bg_nakshatra_medical", "bg_sign_medical", "bg_medical_mappings"} <= set(a["written"])
    assert b["complete"] and {"bg_transit_engine", "bg_transit_rules", "bg_transit_moorti"} <= set(b["written"])
    assert reg["bg_nakshatra_medical"] == reg["bg_medical_mappings"] and reg["bg_transit_engine"] == reg["bg_transit_rules"]          # one shared writer file each


def test_REAL_SCAN_mutation_a_table_the_writer_never_writes_is_a_FAIL():
    reg = ac.registered_ids("")
    got = ac.writer_sibling_record("bg_nakshatra_medical", dict(SIB, target_table="bg_ghost_table"), reg["bg_nakshatra_medical"], _ws(tables=["bg_ghost_table"]), PRI, reg["bg_medical_mappings"], {"kind": "data"})
    assert got["v"] == FAIL and "does not see it write bg_ghost_table" in got["measured"]


# ───────────────────────────── the criterion ─────────────────────────────

def test_only_build_registered_changed_its_text_and_its_revision():
    e = ac.CRITERION_REGISTRY["Build.registered"]
    assert e["revision"] == 3 and "writer_sibling" in e["applicability"] and "SS N-203" in e["applicability"] and "NOT flipped" in e["applicability"]


def test_the_measure_branch_is_wired_before_the_old_chain():
    src = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")
    i = src.index("# Build.registered\n        _wsd = ")
    assert "writer_sibling_record(aid, r, files, _wsd" in src[i:i + 900] and src.index("elif len(files) == 1 and r[\"has_writer\"]:", i) > i


# ───────────────────────────── review fix MED 8: the sibling must ride the primary's CLASS, not just its file ─────────────────────────────

def _two_registrations(tmp_path, same_class: bool):
    body = ("@register('bg_medical_mappings')\n@register('bg_nakshatra_medical')\nclass One(WriterBase):\n    pass\n" if same_class else
            "@register('bg_medical_mappings')\nclass One(WriterBase):\n    pass\n\n\n@register('bg_nakshatra_medical')\nclass Two(WriterBase):\n    pass\n")
    f = tmp_path / ("same_class_writer.py" if same_class else "two_class_writer.py")
    f.write_text(body, encoding="utf-8")
    return f


def test_FORGERY_two_assets_registered_in_one_file_on_different_classes_do_not_share_a_writer(monkeypatch, tmp_path):
    f = _two_registrations(tmp_path, same_class=False)
    monkeypatch.setattr(ac, "_writer_path", lambda name: f)
    got = _rec(monkeypatch, files=("two_class_writer.py",), pfiles=("two_class_writer.py",))
    assert got["v"] == FAIL and "a shared FILE is not a shared writer class" in got["measured"] and "class One" in got["measured"] and "class Two" in got["measured"], got


def test_PASS_two_registrations_on_one_class_share_the_writer(monkeypatch, tmp_path):
    f = _two_registrations(tmp_path, same_class=True)
    monkeypatch.setattr(ac, "_writer_path", lambda name: f)
    got = _rec(monkeypatch, files=("same_class_writer.py",), pfiles=("same_class_writer.py",))
    assert got["v"] == PASS and got["writer_sibling"]["writer_class"] == "One", got


def test_FORGERY_a_file_with_no_class_registered_for_the_sibling_fails(monkeypatch, tmp_path):
    f = tmp_path / "only_primary_writer.py"
    f.write_text("@register('bg_medical_mappings')\nclass One(WriterBase):\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(ac, "_writer_path", lambda name: f)
    got = _rec(monkeypatch, files=("only_primary_writer.py",), pfiles=("only_primary_writer.py",))
    assert got["v"] == FAIL and "no class in" in got["measured"], got
