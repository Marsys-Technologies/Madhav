"""test_e6_5_registry_check.py: E6.5, `asset_census.py --registry-check` (registry-only coverage report, SS N-97(1), N-102).

Offline (psql is made to raise). Every detector below is proven able to FAIL by a mutation of the registry, the N/A rules, the
revision, the deferrals file or the report bytes: a green here is not "it usually holds". The committed-report test is the CI drift
guard. Exit-code numerals are pinned literally (the table lives next to EXIT_SCOPE in asset_census.py)."""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

REPO = HERE.parents[3]
COMMITTED = REPO / ac.REGISTRY_COVERAGE_REPORT_REL
SHA_A, SHA_B = "a" * 40, "b" * 40
D2 = "Carr.D2"
NONE3 = (D2,)      # E5.7: Earn.service_state (revision 2) and Carr.D3 (N-156) have real detectors, so one core criterion is still detector NONE
PEND3 = {c: "N-97" for c in NONE3}
DEFERRED = ["bg_gochara_citation_resolution", "bg_kota_chakra_rings", "bg_medical_mappings", "bg_nakshatra_medical",
            "bg_sign_medical", "bg_vastu_directions"]


def _report(**kw):
    return ac.registry_coverage_report(**kw)


def _text(rep, sha=SHA_A):
    return ac.registry_report_text({**rep, "inspector_commit": sha})


def _run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["asset_census.py", *argv])
    return ac.main()


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("--registry-check must never touch the database")
    monkeypatch.setattr(ac, "psql", boom)
    monkeypatch.setattr(ac, "scalar", boom)


@pytest.fixture
def git_sha(monkeypatch):
    """Generation needs a commit sha for the report head. Real git when present; the named skip when it is not."""
    if ac._inspector_commit() is None:
        pytest.skip("git is unavailable or does not track asset_census.py here: the generator refuses to write a report without an "
                    "inspector_commit (tested separately with a stubbed value)")


@pytest.fixture
def stub_sha(monkeypatch):
    monkeypatch.setattr(ac, "_inspector_commit", lambda: SHA_A)


# ───────────────────────── shape, counts, determinism ─────────────────────────

def test_schema_and_tracker_keys():
    r = _report()
    for k in ("registry_revision", "inspector_commit", "covered_cells", "uncovered_required_criteria", "per_asset_pending",
              "na_rules", "registry_fingerprint", "expected_cells"):
        assert k in r
    assert r["registry_revision"] == ac.REGISTRY_REVISION and r["registry_fingerprint"] == ac.registry_fingerprint()
    assert isinstance(r["covered_cells"], int) and r["covered_cells"] > 0
    assert r["expected_cells"] == 54 and r["schema"] == 2


def test_three_candidate_counts_side_by_side():
    cc = _report()["candidate_cell_counts"]
    assert cc["gate_x_layer"]["total"] == 54 and cc["gate_x_layer"]["pinned"] is True
    assert cc["core_criterion_x_layer"]["total"] == 150 and cc["core_criterion_x_layer"]["pinned"] is False
    assert cc["gate_x_asset"]["total"] is None and "offline" in cc["gate_x_asset"]["omitted_reason"]
    assert cc["core_criterion_x_layer"]["auto_measured"] + cc["core_criterion_x_layer"]["detector_none"] == 150


def test_today_uncovered_are_the_two_detector_none_core_criteria():
    r = _report()
    assert r["uncovered_required_criteria"] == [D2]
    assert r["per_asset_pending"] == [] and r["per_asset_pending_decisions"] == {} and r["pending_cells"] == 0
    assert r["non_core_detector_none"] == ["Completeness.depth.dasha_link"]      # information, never a core cell
    assert "not gate-scoped" in r["non_core_detector_none_note"]
    assert r["covered_cells"] == 48      # Carr x6 holds the uncovered criteria; every Earn cell is covered
    assert "per-asset emission" in r["covered_cells_unit"]


def test_deterministic_and_no_timestamps():
    a, b = _text(_report()), _text(_report())
    assert a == b and a.endswith("\n")
    low = a.lower()
    assert "timestamp" not in low and "generated_at" not in low
    assert json.loads(a)["cells"] == _report()["cells"]


def test_na_rules_listed_with_decisions_and_undeclared_reported():
    r = _report()
    assert [x["rule_id"] for x in r["na_rules"]] == sorted(ac.NA_RULE_DECISIONS)
    assert all(x["decision"] == ac.NA_RULE_DECISIONS[x["rule_id"]] for x in r["na_rules"])
    assert "Vocab.alias#columns_any" in r["undeclared_na_pattern_ids"] and len(r["undeclared_na_pattern_ids"]) == 4
    assert not set(r["undeclared_na_causes"]) & set(ac.NA_RULE_DECISIONS)


def test_inspector_commit_is_documented_as_a_pointer_not_reachability():
    note = _report()["inspector_commit_note"]
    assert "not a reachability claim" in note and "--check never compares it" in note


# ───────────────────────── exit-code table ─────────────────────────

def test_exit_code_numerals_are_pinned():
    assert (ac.EXIT_SCOPE, ac.EXIT_REG_DRIFT, ac.EXIT_REG_CELLS, ac.EXIT_REG_UNCOVERED, ac.EXIT_REG_PARITY) == (6, 9, 10, 11, 12)
    taken = {0, 2, 3, 4, 5, 6, 7}        # 7 is reserved for the emit_gaps withholding guard (PR #3041)
    assert not taken & {ac.EXIT_REG_DRIFT, ac.EXIT_REG_CELLS, ac.EXIT_REG_UNCOVERED, ac.EXIT_REG_PARITY}
    assert len({ac.EXIT_REG_DRIFT, ac.EXIT_REG_CELLS, ac.EXIT_REG_UNCOVERED, ac.EXIT_REG_PARITY}) == 4


# ───────────────────────── mutation: each detector can fail ─────────────────────────

def test_detector_none_without_rule_is_uncovered(monkeypatch):
    base = _report()
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Idem.zz_probe",
                        dict(ac.CRITERION_REGISTRY["Idem.pattern"], check="zz_probe", detector="NONE"))
    r = _report()
    assert "Idem.zz_probe" in r["uncovered_required_criteria"]
    assert r["covered_cells"] == base["covered_cells"] - 6      # the Idem cell of every layer loses coverage
    assert r["candidate_cell_counts"]["core_criterion_x_layer"]["total"] == 156


def test_a_measured_detector_removes_the_uncovered_entry(monkeypatch):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, D2, dict(ac.CRITERION_REGISTRY[D2], detector="asset_census.py:measure()"))
    r = _report()
    assert D2 not in r["uncovered_required_criteria"] and r["covered_cells"] == 54      # Carr.D3 already has its detector: D2 was the last open Carr criterion


def test_a_bogus_detector_string_is_refused_never_counted(monkeypatch):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, D2, dict(ac.CRITERION_REGISTRY[D2], detector="bogus"))
    with pytest.raises(ValueError, match="closed set"):
        _report()
    assert ac.registry_check_main("unused.json", True) == 5
    assert ac.KNOWN_DETECTORS == ("NONE", "asset_census.py:measure()")


def test_layer_narrowing_changes_required_and_cells(monkeypatch):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, D2, dict(ac.CRITERION_REGISTRY[D2], layers=("L1",)))
    cc = _report()["candidate_cell_counts"]["core_criterion_x_layer"]
    assert cc["total"] == 145


def test_declared_na_rule_does_not_cover_a_detector_none_criterion():
    r = _report()
    assert f"{D2}#measured:not-the-declared-carriage" in ac.NA_RULE_DECISIONS      # a rule exists for Carr.D2 ...
    assert D2 in r["uncovered_required_criteria"]                                   # ... and it is still uncovered
    cell = next(c for c in r["cells"] if c["gate"] == "Carr" and c["layer"] == "L2")
    assert f"{D2}#measured:not-the-declared-carriage" in cell["declared_na_rules"] and D2 in cell["uncovered"]
    assert cell["status"] == "uncovered"


def test_removing_an_na_rule_changes_the_report(monkeypatch):
    base = _report()
    rid = "Narr.lint#measured:no-prose"
    monkeypatch.delitem(ac.NA_RULE_DECISIONS, rid)
    r = _report()
    assert rid not in [x["rule_id"] for x in r["na_rules"]] and rid in r["undeclared_na_causes"]
    assert r["registry_fingerprint"] != base["registry_fingerprint"]
    assert _text(r) != _text(base)


def test_na_rule_validation_is_called_by_the_report_and_the_cli(monkeypatch, tmp_path, stub_sha):
    monkeypatch.setitem(ac.NA_RULE_DECISIONS, "Build.dag#measured:not-a-registered-cause", "N-0")
    with pytest.raises(ValueError, match="not a rule id"):
        _report()
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 5 and not out.exists()


def test_fingerprint_and_revision_change_change_the_report(monkeypatch):
    base = _report()
    monkeypatch.setattr(ac, "REGISTRY_REVISION", ac.REGISTRY_REVISION + 1)
    bumped = _report()
    assert bumped["registry_revision"] == base["registry_revision"] + 1 and _text(bumped) != _text(base)
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Build.dag", dict(ac.CRITERION_REGISTRY["Build.dag"], revision=99))
    assert _report()["registry_fingerprint"] != base["registry_fingerprint"]


# ───────────────────────── per-asset-pending hook ─────────────────────────

def test_pending_is_excluded_from_uncovered_but_never_counted_covered():
    r = _report(pending=PEND3)
    assert r["per_asset_pending"] == sorted(NONE3) and r["uncovered_required_criteria"] == []
    assert r["covered_cells"] == 48 and r["pending_cells"] == 6      # Carr x6 are pending, not covered
    assert r["candidate_cell_counts"]["gate_x_layer"] == dict(total=54, pinned=True, with_auto_detector=54, fully_covered=48,
                                                              pending_only=6)
    assert r["per_asset_pending_decisions"] == dict(sorted(PEND3.items()))
    assert {c["status"] for c in r["cells"] if c["gate"] == "Carr"} == {"pending"}


def test_pending_contents_are_part_of_the_report_bytes():
    assert _text(_report(pending={D2: "N-97"})) != _text(_report(pending={D2: "N-98"})) != _text(_report())


def test_pending_hook_refuses_a_measured_unknown_or_undecided_entry():
    for bad in ({"Build.dag": "N-1"}, {"No.such": "N-1"}, {D2: ""}, {D2: "SS-decision-x"}, {D2: "n-97"}, {D2: "N-"},
                {"Completeness.depth.dasha_link": "N-1"}):
        with pytest.raises(ValueError):
            _report(pending=bad)


# ───────────────────────── static registry -> emission parity ─────────────────────────

def test_emission_table_reads_reachability_not_mere_presence():
    src = '''
X = ("A.b1", "A.b2")
Y = ("A.zz", 3)
def measure():
    helper()
    return {"A.direct": 1, **{k: 1 for k in X}, "n": Y}
def helper():
    return "H.deep"
def orphan():
    return "O.never"
'''
    t = ac._emission_sites_from(src)
    assert t == {"A.b1": ("measure",), "A.b2": ("measure",), "A.direct": ("measure",), "H.deep": ("helper",)}


def test_every_registry_detector_is_emitted_today_and_carr_d1_resolves_through_its_bundle():
    r = _report()
    assert r["declared_detector_never_emitted"] == []
    by = {x["criterion"]: x for x in r["criterion_emission"]}
    assert set(by) == set(ac.CRITERION_REGISTRY)
    assert by["Carr.D1"]["emitted_by_measure"] and "carr_checks" in by["Carr.D1"]["sites"]
    assert by["Build.dag"]["emitted_by_measure"] and by["Build.dag"]["detector"] == "asset_census.py:measure()"


def test_a_declared_detector_that_nothing_emits_fails_with_the_parity_exit(monkeypatch, tmp_path, stub_sha):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Idem.zz_ghost",
                        dict(ac.CRITERION_REGISTRY["Idem.pattern"], check="zz_ghost"))
    r = _report()
    assert r["declared_detector_never_emitted"] == ["Idem.zz_ghost"]
    assert (ac.EXIT_REG_PARITY, ) == tuple(c for c, _ in ac.registry_report_problems(r) if c == ac.EXIT_REG_PARITY)
    assert _run(monkeypatch, "--registry-check", "--out", str(tmp_path / "r.json")) == 12


def test_parity_detector_reads_the_emission_table(monkeypatch):
    monkeypatch.setattr(ac, "_emission_sites", lambda: {})
    assert len(_report()["declared_detector_never_emitted"]) == sum(1 for e in ac.CRITERION_REGISTRY.values() if e["detector"] != "NONE")      # every non-NONE criterion loses its emission


# ───────────────────────── gating (SS N-97(1)) ─────────────────────────

def test_gate_reports_uncovered_and_passes_when_all_pending():
    assert any(c == ac.EXIT_REG_UNCOVERED and "Carr.D2" in m for c, m in ac.registry_report_problems(_report()))
    assert ac.registry_report_problems(_report(pending=PEND3)) == []


def test_gate_fails_when_cell_count_is_not_54(monkeypatch):
    monkeypatch.setattr(ac, "CELL_GATES", ac.CELL_GATES[:-1])
    r = _report(pending={})
    assert r["candidate_cell_counts"]["gate_x_layer"]["total"] == 48
    assert any(c == ac.EXIT_REG_CELLS and "48" in m and "54" in m for c, m in ac.registry_report_problems(r))


# ───────────────────────── the CLI through main() ─────────────────────────

def test_write_mode_exit_is_zero_without_require_covered_and_eleven_with_it(monkeypatch, tmp_path, stub_sha):
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 0 and out.exists()
    assert json.loads(out.read_text())["inspector_commit"] == SHA_A
    assert _run(monkeypatch, "--registry-check", "--require-covered", "--out", str(out)) == 11
    monkeypatch.setattr(ac, "PER_ASSET_PENDING", PEND3)
    assert _run(monkeypatch, "--registry-check", "--require-covered", "--out", str(out)) == 0


def test_check_is_drift_only(monkeypatch, tmp_path, stub_sha):
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 0
    assert _run(monkeypatch, "--registry-check", "--check", "--out", str(out)) == 0      # coverage is red, drift is clean: 0
    assert _run(monkeypatch, "--registry-check", "--check", "--require-covered", "--out", str(out)) == 11
    out.write_text(out.read_text().replace('"covered_cells": 48', '"covered_cells": 54'), encoding="utf-8")
    assert _run(monkeypatch, "--registry-check", "--check", "--out", str(out)) == 9
    assert _run(monkeypatch, "--registry-check", "--check", "--require-covered", "--out", str(out)) == 9
    assert _run(monkeypatch, "--registry-check", "--check", "--out", str(tmp_path / "missing.json")) == 9
    (tmp_path / "bin.json").write_bytes(b"\xff\xfe")
    assert _run(monkeypatch, "--registry-check", "--check", "--out", str(tmp_path / "bin.json")) == 9


def test_cell_count_exit_through_main_and_priority(monkeypatch, tmp_path, stub_sha):
    monkeypatch.setattr(ac, "CELL_GATES", ac.CELL_GATES[:-1])
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--require-covered", "--out", str(out)) == 10      # beats uncovered (11)
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Idem.zz_ghost", dict(ac.CRITERION_REGISTRY["Idem.pattern"], check="zz_ghost"))
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 10                              # beats parity (12)


def test_writing_without_an_inspector_commit_is_refused_but_checking_is_not(monkeypatch, tmp_path, stub_sha):
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 0
    monkeypatch.setattr(ac, "_inspector_commit", lambda: None)
    fresh = tmp_path / "fresh.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(fresh)) == 5 and not fresh.exists()
    assert _run(monkeypatch, "--registry-check", "--check", "--out", str(out)) == 0


def test_write_is_atomic_a_failed_replace_leaves_the_old_report_and_no_tmp(monkeypatch, tmp_path, stub_sha):
    out = tmp_path / "r.json"
    out.write_text("OLD", encoding="utf-8")

    def broken(*a, **k):
        raise OSError("disk says no")
    monkeypatch.setattr(os, "replace", broken)
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 5
    assert out.read_text() == "OLD" and [p.name for p in tmp_path.iterdir()] == ["r.json"]


def test_incompatible_flag_combinations_are_refused(monkeypatch, tmp_path):
    for extra in (["--emit-gaps"], ["--layer", "L1"], ["--assets", "bg_x"], ["--rollup"]):
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, "--registry-check", "--out", str(tmp_path / "r.json"), *extra)
        assert e.value.code == 2
    for solo in ("--check", "--require-covered"):
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, solo)
        assert e.value.code == 2


def test_real_git_head_names_the_inspector_commit(git_sha, monkeypatch, tmp_path):
    out = tmp_path / "r.json"
    assert _run(monkeypatch, "--registry-check", "--out", str(out)) == 0
    assert ac._GIT_SHA.fullmatch(json.loads(out.read_text())["inspector_commit"])


# ───────────────────────── owner deferrals (SS N-102) ─────────────────────────

def _entry(aid="bg_sign_medical", **kw):
    return {**dict(asset_id=aid, criterion_gate="Carr", decision="N-102", state="deferred by owner (N-102)"), **kw}


def _six(**over):
    return [_entry(a, **over) for a in DEFERRED]


def _write_deferrals(tmp_path, entries, monkeypatch):
    p = tmp_path / "owner_deferrals.json"
    p.write_text(json.dumps({"schema": 1, "deferrals": entries}), encoding="utf-8")
    monkeypatch.setattr(ac, "OWNER_DEFERRALS_PATH", p)
    return p


def test_listed_deferrals_appear_exactly_and_apart_from_uncovered():
    r = _report()
    assert [d["asset_id"] for d in r["deferred_by_owner"]] == DEFERRED == list(ac.OWNER_DEFERRAL_IDS)
    assert all(d == _entry(d["asset_id"]) for d in r["deferred_by_owner"])
    assert not set(DEFERRED) & set(r["uncovered_required_criteria"]) and r["covered_cells"] == 48
    assert len(r["owner_deferrals_sha256"]) == 64


def test_deferrals_never_fail_the_gate_or_count_as_cells():
    allp = _report(pending=PEND3)
    assert allp["deferred_by_owner"] and ac.registry_report_problems(allp) == []
    assert allp["candidate_cell_counts"]["gate_x_layer"]["total"] == 54 and allp["covered_cells"] == 48


def test_unknown_asset_id_refuses(tmp_path, monkeypatch, stub_sha):
    _write_deferrals(tmp_path, [*_six()[:-1], _entry("bg_no_such_asset")], monkeypatch)
    with pytest.raises(ValueError, match="bg_no_such_asset"):
        _report()
    assert _run(monkeypatch, "--registry-check", "--out", str(tmp_path / "o.json")) == 5 and not (tmp_path / "o.json").exists()


@pytest.mark.parametrize("bad", [
    _entry(criterion_gate="Nope"), _entry(criterion_gate="Build"), _entry(decision="102"), _entry(decision="N-103"),
    _entry(state=" "), _entry(state="deferred by owner (N-103)"), {**_entry(), "extra": "x"},
    {"asset_id": "bg_sign_medical"}, "bg_sign_medical", _entry(asset_id=7)])
def test_malformed_or_off_ruling_entry_refuses(tmp_path, monkeypatch, bad):
    _write_deferrals(tmp_path, [bad, *_six()[1:]], monkeypatch)
    with pytest.raises(ValueError):
        _report()


def test_duplicate_entry_refuses(tmp_path, monkeypatch):
    _write_deferrals(tmp_path, [*_six(), _entry()], monkeypatch)
    with pytest.raises(ValueError, match="duplicate"):
        _report()


def test_the_set_is_exactly_the_six_removing_or_adding_refuses(tmp_path, monkeypatch):
    _write_deferrals(tmp_path, _six()[:-1], monkeypatch)
    with pytest.raises(ValueError, match="missing"):
        _report()
    extra = sorted(ac._seed_active_asset_ids() - set(DEFERRED))[0]      # a real, active, but un-ruled asset
    _write_deferrals(tmp_path, [*_six(), _entry(extra)], monkeypatch)
    with pytest.raises(ValueError, match="extra"):
        _report()
    _write_deferrals(tmp_path, [], monkeypatch)
    with pytest.raises(ValueError):
        _report()


def test_missing_or_invalid_file_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "OWNER_DEFERRALS_PATH", tmp_path / "absent.json")
    with pytest.raises(ValueError):
        _report()
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(ac, "OWNER_DEFERRALS_PATH", tmp_path / "bad.json")
    with pytest.raises(ValueError):
        _report()
    (tmp_path / "v2.json").write_text('{"schema": 2, "deferrals": []}', encoding="utf-8")
    monkeypatch.setattr(ac, "OWNER_DEFERRALS_PATH", tmp_path / "v2.json")
    with pytest.raises(ValueError):
        _report()


def _seed(actives):
    rows = "".join(f"  {{\n    asset_id: '{a}',\n    layer: 'brahmagyan', sort_order: 0,\n    depends_on: [],\n"
                   f"    scope: 'global', is_active: {'true' if on else 'false'}, estimated_seconds: null,\n  }},\n" for a, on in actives)
    return f"export const ASSETS: AssetDef[] = [\n{rows}];\n"


def test_an_inactive_seed_asset_is_refused(tmp_path, monkeypatch):
    seed = tmp_path / "seed.ts"
    monkeypatch.setattr(ac, "REGISTRY_SEED_PATH", seed)
    seed.write_text(_seed([(a, True) for a in DEFERRED]), encoding="utf-8")
    assert [d["asset_id"] for d in _report()["deferred_by_owner"]] == DEFERRED       # the fixture itself is valid
    seed.write_text(_seed([(a, a != "bg_sign_medical") for a in DEFERRED]), encoding="utf-8")
    with pytest.raises(ValueError, match="bg_sign_medical.*not an active registry asset"):
        _report()


def test_deferrals_file_bytes_are_part_of_the_report_and_the_drift_check(tmp_path, monkeypatch):
    base_text = _text(_report())
    p = _write_deferrals(tmp_path, _six(), monkeypatch)
    same_entries = _report()
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")        # byte-only edit, same entries
    edited = _report()
    assert edited["deferred_by_owner"] == same_entries["deferred_by_owner"]
    assert edited["owner_deferrals_sha256"] != same_entries["owner_deferrals_sha256"]
    assert _text(edited) != base_text and ac.registry_report_drift(base_text, _text(edited))


def test_committed_deferrals_file_matches_committed_report():
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    entries, sha = ac.load_owner_deferrals()
    assert committed["deferred_by_owner"] == entries and committed["owner_deferrals_sha256"] == sha


# ───────────────────────── drift: committed report == fresh regeneration ─────────────────────────

def test_drift_detector_can_fail_and_only_normalises_inspector_commit():
    t = _text(_report(), SHA_A)
    assert ac.registry_report_drift(t, _text(_report(), SHA_B)) is None             # another commit sha: not drift
    assert ac.registry_report_drift(t.replace('"covered_cells": 48', '"covered_cells": 49'), t)
    assert ac.registry_report_drift(t.replace('"expected_cells": 54', '"expected_cells": 150'), t)
    assert ac.registry_report_drift(t.replace("\n ", "\n  ", 1), t)                  # formatting is part of the bytes
    assert ac.registry_report_drift(t + "\n", t)
    assert ac.registry_report_drift(t.replace(SHA_A, "abc123"), t)                   # abbreviated sha refused
    assert ac.registry_report_drift(t.replace(f'"{SHA_A}"', "null"), t)


def test_committed_report_equals_fresh_regeneration():
    assert COMMITTED.exists(), "00_ARCHITECTURE/control/registry_coverage_report.json must be committed"
    rep = _report()
    rep["inspector_commit"] = SHA_A
    assert ac.registry_report_drift(COMMITTED.read_text(encoding="utf-8"), ac.registry_report_text(rep)) is None
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed["registry_fingerprint"] == ac.registry_fingerprint()
    assert committed["registry_revision"] == ac.REGISTRY_REVISION and committed["expected_cells"] == 54
