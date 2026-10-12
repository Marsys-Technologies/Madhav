"""J-0c acceptance: execute the real CLI against pinned inventories and mutations."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

FLEET = Path(__file__).resolve().parents[1]
SCRIPT = FLEET / "accept/j0_disposition.py"
FIXTURE = FLEET / "tests/fixtures/accept_j0c"
REPO = FLEET.parents[3]
REAL = Path("/Users/Dev/kalayantra/run")


@pytest.fixture
def world(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "evidence.md").write_text("offline evidence\n")
    paths = {}
    for name in ("disposition", "prs", "state"):
        path = tmp_path / (name + ".json")
        path.write_bytes((FIXTURE / path.name).read_bytes())
        paths[name] = path
    return paths, repo


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def mutate(world, change):
    paths, _ = world
    data = read(paths["disposition"])
    change(data)
    write(paths["disposition"], data)


def run(world):
    paths, repo = world
    done = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "check", str(paths["disposition"]),
         "--inventory-prs", str(paths["prs"]), "--inventory-state", str(paths["state"]),
         "--repo", str(repo)], capture_output=True, text=True)
    assert done.stdout, done.stderr
    report = json.loads(done.stdout)
    assert report["schema"] == "ky.accept/1" and report["item"] == "J-0c"
    assert set(report) == {"schema", "item", "result", "violations"}
    assert all(set(v) == {"code", "row", "detail"} for v in report["violations"])
    return done, report


def refused(world, code):
    done, report = run(world)
    assert done.returncode == 1, done.stdout + done.stderr
    assert report["result"] == "refused"
    assert code in [v["code"] for v in report["violations"]], report
    return report


def state_row(data, item):
    return next(r for r in data["state_dispositions"] if r["id"] == item)


def test_faithful_fixture_passes_deterministically_without_writes(world):
    paths, repo = world
    before = {p: p.read_bytes() for p in [*paths.values(), repo / "evidence.md"]}
    first, report = run(world)
    assert first.returncode == 0 and report["result"] == "accepted"
    assert report["violations"] == [] and first.stderr == ""
    assert run(world)[0].stdout == first.stdout
    assert {p: p.read_bytes() for p in before} == before
    assert sorted(p.name for p in repo.iterdir()) == ["evidence.md"]


@pytest.mark.parametrize("kind", ["pr", "state"])
def test_omitted_row(world, kind):
    mutate(world, lambda d: d[kind + "_dispositions"].pop())
    refused(world, "coverage_missing")


@pytest.mark.parametrize("kind", ["pr", "state"])
def test_duplicated_row(world, kind):
    mutate(world, lambda d: d[kind + "_dispositions"].append(copy.deepcopy(d[kind + "_dispositions"][0])))
    refused(world, "coverage_duplicate")


@pytest.mark.parametrize("field", ["open_prs", "state_entries", "total_entries", "duplicates", "missing",
                                   "decisions", "sealed_decisions", "holds"])
def test_wrong_aggregate(world, field):
    mutate(world, lambda d: d["coverage"].update({field: 999}))
    refused(world, "coverage_count")


@pytest.mark.parametrize("field", ["decisions", "sealed_decisions", "holds"])
def test_missing_aggregate(world, field):
    mutate(world, lambda d: d["coverage"].pop(field))
    refused(world, "coverage_count")


@pytest.mark.parametrize("kind,field,value,code", [
    ("pr", "evidence", " ", "evidence_missing"),
    ("state", "evidence", None, "evidence_missing"),
    ("pr", "head", "xyz1234", "commit_invalid"),
    ("state", "owner", "", "row_contract"),
    ("state", "proposal", "completed", "row_contract"),
    ("state", "dependencies", None, "row_contract"),
    ("state", "phase", 0, "row_contract"),
    ("state", "phase", 13, "row_contract"),
    ("state", "phase", True, "row_contract"),
])
def test_row_fields(world, kind, field, value, code):
    mutate(world, lambda d: d[kind + "_dispositions"][0].update({field: value}))
    refused(world, code)


@pytest.mark.parametrize("evidence,code", [
    ("read evidence/absent.md:12", "path_unresolved"),
    ("read `absent.md`", "path_unresolved"),
    ("PR #9999", "pr_unresolved"),
    ("commit xyz1234", "commit_invalid"),
    ("sha: abc123", "commit_invalid"),
    ("https://github.com/Marsys-Technologies/Madhav/pull/9999", "pr_unresolved"),
])
def test_offline_evidence_reference(world, evidence, code):
    mutate(world, lambda d: d["pr_dispositions"][0].update(evidence=evidence))
    refused(world, code)


def test_all_references_in_one_field_are_checked(world):
    mutate(world, lambda d: d["pr_dispositions"][0].update(
        evidence="`evidence.md` then absent.md; PR #3141 then PR #9999; commit abc1234 then commit nope"))
    report = refused(world, "path_unresolved")
    assert {v["code"] for v in report["violations"]} >= {"path_unresolved", "pr_unresolved", "commit_invalid"}


def test_unknown_pr_row(world):
    mutate(world, lambda d: d["pr_dispositions"][0].update(pr=9999))
    refused(world, "coverage_extra")


def test_earlier_phase_than_state_dependency(world):
    mutate(world, lambda d: state_row(d, "A5.5m").update(phase=7))
    report = refused(world, "phase_order")
    assert any(v["row"] == "A5.5m" and "A5.5l" in v["detail"] for v in report["violations"])


def test_pr_dependency_phase_order(world):
    mutate(world, lambda d: d["pr_dispositions"][1].update(phase=7, dependencies=["PR #3141"]))
    refused(world, "phase_order")


@pytest.mark.parametrize("item,phase", [
    ("A5.5h", 5), ("A5.5j", 5), ("A5.5m", 5), ("A5.5k", 7), ("A5.5l", 5),
    *[(item, phase) for item in ("A5.6", "B5.4", "J2") for phase in range(1, 10)],
])
def test_every_named_phase_refusal_mutation(world, item, phase):
    mutate(world, lambda d: state_row(d, item).update(phase=phase))
    refused(world, "phase_constraint")


@pytest.mark.parametrize("item", ["A5.6", "B5.4", "J2", "J3"])
def test_each_named_source_dependency_replacement(world, item):
    mutate(world, lambda d: state_row(d, item)["dependencies"].__setitem__(0, "replacement"))
    refused(world, "source_dependency")


@pytest.mark.parametrize("phase", [1, 7, 9])
def test_small_test_census_pr_only_in_phase_eight(world, phase):
    mutate(world, lambda d: d["pr_dispositions"][0].update(phase=phase))
    refused(world, "small_test_constraint")


@pytest.mark.parametrize("kind", ["hold", "decision"])
def test_reserved_unresolved_rulings_route_to_adhikarin(world, kind):
    mutate(world, lambda d: next(r for r in d["unresolved"] if r["kind"] == kind).update(proposal="exercise"))
    refused(world, "reserved_ruling")


def test_reserved_item_owner(world):
    mutate(world, lambda d: state_row(d, "N-G9").update(owner="J-4d"))
    refused(world, "reserved_ruling")


def test_observation_timestamp_missing(world):
    mutate(world, lambda d: d.pop("observed_at"))
    refused(world, "observation_missing")


@pytest.mark.parametrize("field", ["artifact", "item"])
def test_wrong_artifact_identity(world, field):
    mutate(world, lambda d: d.update({field: "other"}))
    refused(world, "artifact_identity")


def test_minimum_artifact_size(world):
    world[0]["disposition"].write_text('{"sources":' + json.dumps(read(world[0]["disposition"])["sources"]) + '}')
    # The inventories still pin; a short input is tested with just the two required pins.
    data = read(world[0]["disposition"])
    data["sources"] = {k: {"sha256": v["sha256"]} for k, v in data["sources"].items()
                       if k in {"pr_inventory", "state_inventory"}}
    world[0]["disposition"].write_text(json.dumps(data, separators=(",", ":")))
    assert world[0]["disposition"].stat().st_size < 300
    refused(world, "artifact_size")


def test_malformed_source_hash(world):
    mutate(world, lambda d: d["sources"]["pravaha_plan"].update(sha256="not-a-hash"))
    refused(world, "source_hash")


def test_missing_source_observation(world):
    mutate(world, lambda d: d["sources"]["state_inventory"].pop("observed_at"))
    refused(world, "observation_missing")


def test_missing_unresolved_hold(world):
    mutate(world, lambda d: d.update(unresolved=[r for r in d["unresolved"] if r["kind"] != "hold"]))
    refused(world, "reserved_ruling")


def test_unresolved_evidence_missing(world):
    mutate(world, lambda d: d["unresolved"][0].update(evidence=""))
    refused(world, "evidence_missing")


def test_dependency_pr_reference_must_resolve(world):
    mutate(world, lambda d: d["pr_dispositions"][1].update(dependencies=["PR #9999"]))
    refused(world, "pr_unresolved")


def test_repository_escape_is_not_a_resolving_repo_path(world):
    mutate(world, lambda d: d["pr_dispositions"][0].update(evidence="../prs.json"))
    refused(world, "path_unresolved")


def test_same_phase_and_inventory_pr_url_and_short_commit_are_valid(world):
    mutate(world, lambda d: d["pr_dispositions"][1].update(
        dependencies=["PR #3141"], evidence="https://github.com/Marsys-Technologies/Madhav/pull/3141; sha ABC1234"))
    assert run(world)[0].returncode == 0


@pytest.mark.parametrize("evidence", ["read `missing/directory`", "read `file with spaces.md`"])
def test_explicit_paths_without_extensions_or_with_spaces(world, evidence):
    mutate(world, lambda d: d["pr_dispositions"][0].update(evidence=evidence))
    refused(world, "path_unresolved")


def test_explicit_existing_path_with_spaces(world):
    (world[1] / "file with spaces.md").write_text("evidence\n")
    mutate(world, lambda d: d["pr_dispositions"][0].update(evidence="read `file with spaces.md:1`"))
    assert run(world)[0].returncode == 0


def test_known_row_id_embedded_in_dependency(world):
    mutate(world, lambda d: d["pr_dispositions"][1].update(phase=7, dependencies=["requires A5.5l readback"]))
    refused(world, "phase_order")


@pytest.mark.parametrize("name", ["prs", "state"])
def test_both_inventory_pins_are_required(world, name):
    key = "pr_inventory" if name == "prs" else "state_inventory"
    mutate(world, lambda d: d["sources"][key].pop("sha256"))
    done, report = run(world)
    assert done.returncode == 3 and report["violations"][0]["code"] == "input_digest"


@pytest.mark.parametrize("kind", ["pr", "state"])
def test_missing_entire_disposition_class_cannot_pass(world, kind):
    mutate(world, lambda d: d.pop(kind + "_dispositions"))
    refused(world, "coverage_missing")


def test_duplicate_json_member_is_unknown(world):
    world[0]["disposition"].write_text('{"item":"J-0c", "item":"J-0c"}')
    done, report = run(world)
    assert done.returncode == 3 and report["violations"][0]["code"] == "input_invalid"


def test_digest_mismatch_is_unknown_not_refusal_or_pass(world):
    paths, _ = world
    paths["prs"].write_bytes(paths["prs"].read_bytes() + b" ")
    done, report = run(world)
    assert done.returncode == 3 and report["result"] == "unknown"
    assert [v["code"] for v in report["violations"]] == ["input_digest"]


@pytest.mark.parametrize("name", ["disposition", "prs", "state"])
def test_unreadable_input_is_unknown(world, name):
    world[0][name].unlink()
    done, report = run(world)
    assert done.returncode == 3 and report["result"] == "unknown"
    assert report["violations"][0]["code"] == "input_unreadable"


def test_invalid_json_is_unknown(world):
    world[0]["disposition"].write_text("{")
    assert run(world)[0].returncode == 3


def test_real_artifact_truth_when_available():
    paths = {"disposition": REAL / "J0_DISPOSITION.json", "prs": REAL / "J0_PR_INVENTORY.json",
             "state": REAL / "J0_STATE_INVENTORY.json"}
    if not all(p.is_file() for p in paths.values()):
        pytest.skip("historical inventories unavailable offline")
    done, report = run((paths, REPO))
    assert done.returncode == 1
    # Observed independently: no class counts, plus the unexcepted phase 7 -> 8 edge.
    assert [(v["code"], v["row"]) for v in report["violations"]] == [
        ("coverage_count", "coverage.decisions"),
        ("coverage_count", "coverage.sealed_decisions"),
        ("coverage_count", "coverage.holds"),
        ("phase_order", "A5.5m"),
    ]
