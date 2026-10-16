"""Offline J8 preparation: fixtures are observations, never campaign acceptance.

Breaks caught: dropped J-0 rows, proposal-as-completion, lost dependencies,
nonterminal/partial tracker exports, log drift, and corrupted archive bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "platform/scripts/governance/pravaha_close.py"
PRAVAHA = ROOT / "00_ARCHITECTURE/control/pravaha/plan_model.json"
CAMPAIGN = ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json"


def put(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cli(*args):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)],
                          text=True, capture_output=True, timeout=15,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def assert_ok(result):
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def world(tmp_path):
    disposition = put(tmp_path / "disposition.json", {
        "artifact": "J0_DISPOSITION", "item": "J-0c",
        "pr_dispositions": [{"pr": 2817, "proposal": "keep", "owner": "J-4b", "phase": 7},
                            {"pr": 2952, "proposal": "not-applicable", "owner": "J-3c", "phase": 5}],
        "state_dispositions": [{"id": "B6.3", "proposal": "keep", "owner": "J-8", "phase": 12},
                               {"id": "J3", "proposal": "keep", "owner": "J-8", "phase": 12}],
    })
    return tmp_path, disposition


def prepare(world):
    tmp, disposition = world
    out = tmp / "prepared"
    result = cli("prepare", "--disposition", disposition, "--campaign-model", CAMPAIGN,
                 "--pravaha-model", PRAVAHA, "--out-dir", out)
    assert_ok(result)
    return out


def row_args(world, out):
    return ["--rows", out / "close_rows.template.json", "--disposition", world[1],
            "--campaign-model", CAMPAIGN, "--pravaha-model", PRAVAHA]


def fill_rows(out):
    p = out / "close_rows.template.json"
    data = read(p)
    for row in data["rows"]:
        row.update(final_state="done", evidence="reviewed evidence: fixture only")
    put(p, data)
    return data


def test_prepare_reports_every_j0_row_without_promoting_proposals(world):
    out = prepare(world)
    report = (out / "PRAVAHA_CLOSE_REPORT_DRAFT_v1_0.md").read_text()
    assert "status: DRAFT" in report
    for key in ["pr:2817", "pr:2952", "state:B6.3", "state:J3"]:
        assert f"| {key} |" in report
    data = read(out / "close_rows.template.json")
    assert [row["key"] for row in data["rows"]] == ["pr:2817", "pr:2952", "state:B6.3", "state:J3"]
    assert all(row["final_state"] is None and row["evidence"] is None for row in data["rows"])
    assert data["status"] == "TEMPLATE_NOT_EVIDENCE"
    assert not (out / "PRAVAHA_CLOSE_REPORT_v1_0.md").exists()
    assert not (out / "J8A_PRAVAHA_FINAL.json").exists()


def test_templates_retain_each_current_and_original_dependency(world):
    out = prepare(world)
    expected = {
        "J-8": ["J-8a", "V-J6", "J-8-b63", "J-8-j3"],
        "J-8a": ["J-0", "V-J6"],
        "J-8-b63": ["J-0m", "J-8a", "V-J6", "J-7a-a62", "J-7-a63", "J-7-b61", "J-7b-b62"],
        "J-8-j3": ["J-0m", "J-8a", "V-J6", "J-8-b63"],
    }
    for item, deps in expected.items():
        data = read(out / f"{item}.template.json")
        assert data["depends_on"] == deps
        assert data["landing_phase"] == 12
        assert data["artifact_sha256"] is None
        assert data["independent_acceptance"] is None
        assert data["status"] == "TEMPLATE_NOT_EVIDENCE"
        assert set(data["prerequisite_evidence"]) == set(deps)
        assert all(proof == {"path": None, "sha256": None, "independent_acceptance": None}
                   for proof in data["prerequisite_evidence"].values())
    b63 = read(out / "J-8-b63.template.json")
    assert b63["inherited"] == {"item": "B6.3", "depends_on": ["A6.2", "A6.3", "B6.1", "B6.2"]}
    assert b63["required_evidence"] == ["close_report", "CURRENT_STATE", "SESSION_LOG", "validated_SESSION_CLOSE"]
    assert read(out / "J-8-j3.template.json")["inherited"] == {"item": "J3", "depends_on": ["B6.3"]}


def test_source_model_losing_original_dependency_is_refused_before_writes(world):
    tmp, disposition = world
    model = read(PRAVAHA)
    next(row for row in model["items"] if row["id"] == "B6.3")["depends_on"].remove("A6.3")
    bad = put(tmp / "bad-model.json", model)
    out = tmp / "refused"
    result = cli("prepare", "--disposition", disposition, "--campaign-model", CAMPAIGN,
                 "--pravaha-model", bad, "--out-dir", out)
    assert result.returncode == 1
    assert "lineage" in result.stdout
    assert not out.exists()


def test_unfilled_template_fails_local_row_check(world):
    out = prepare(world)
    result = cli("check-rows", *row_args(world, out))
    assert result.returncode == 1
    assert "final state" in result.stdout


def test_complete_rows_render_evidence_but_remain_draft(world):
    out = prepare(world)
    data = fill_rows(out)
    data["rows"][1].update(final_state="not_applicable", reason="integration exhibit only",
                           decision="fixture decision Q17")
    put(out / "close_rows.template.json", data)
    result = cli("check-rows", *row_args(world, out))
    assert_ok(result)
    observed = json.loads(result.stdout)
    assert observed["local_rows_complete"] is True
    assert observed["independent_acceptance"] is None
    rendered = cli("render", *row_args(world, out))
    assert_ok(rendered)
    assert "status: DRAFT" in rendered.stdout
    assert "not_applicable" in rendered.stdout
    assert "integration exhibit only" in rendered.stdout
    assert "fixture decision Q17" in rendered.stdout
    assert "reviewed evidence: fixture only" in rendered.stdout


@pytest.mark.parametrize("mutation,fragment", [
    ("missing", "coverage"), ("extra", "coverage"), ("duplicate", "duplicate"),
    ("blank_evidence", "evidence"), ("na_without_reason", "reason"),
    ("superseded_without_decision", "decision"), ("parked", "final state"),
    ("changed_proposal", "proposal"), ("bad_source_pin", "SHA-256"),
])
def test_local_row_check_rejects_missing_or_unearned_dispositions(world, mutation, fragment):
    out = prepare(world)
    data = fill_rows(out)
    if mutation == "missing":
        data["rows"].pop()
    elif mutation == "extra":
        data["rows"].append({**data["rows"][0], "key": "state:invented"})
    elif mutation == "duplicate":
        data["rows"].append(data["rows"][0])
    elif mutation == "blank_evidence":
        data["rows"][0]["evidence"] = " \n"
    elif mutation == "na_without_reason":
        data["rows"][0].update(final_state="not_applicable", decision="fixture decision")
    elif mutation == "superseded_without_decision":
        data["rows"][0].update(final_state="superseded", reason="replaced")
    elif mutation == "parked":
        data["rows"][0]["final_state"] = "parked"
    elif mutation == "changed_proposal":
        data["rows"][0]["proposal"] = "salvage"
    else:
        data["sources"]["disposition_sha256"] = "0" * 64
    put(out / "close_rows.template.json", data)
    result = cli("check-rows", *row_args(world, out))
    assert result.returncode == 1
    assert fragment in result.stdout


def tracker_fixture(tmp):
    model = {"items": [
        {"id": "A6.2", "depends_on": []}, {"id": "A6.3", "depends_on": []},
        {"id": "B6.1", "depends_on": []}, {"id": "B6.2", "depends_on": []},
        {"id": "B6.3", "depends_on": ["A6.2", "A6.3", "B6.1", "B6.2"]},
        {"id": "J3", "depends_on": ["B6.3"], "done_by": "join"},
    ]}
    rows = [{**row, "status": "done", "deps_open": [], "evidence": "fixture measured evidence"}
            for row in model["items"]]
    event = {"kind": "item", "item": "B6.3", "state": "done", "actor": "stream-B",
             "ts": "2026-10-16T00:00:00+00:00", "evidence": "fixture measured evidence"}
    events = tmp / "EVENTS.source.jsonl"
    events.write_bytes((json.dumps(event) + "\n").encode())
    snapshot = {"tracks": [{"id": "B", "items": rows}], "health": {
        "event_log": {"exists": True, "events": 1, "malformed": 0},
        "last_event_at": event["ts"], "model_error": None, "detector_errors": [], "tick_errors": []}}
    return put(tmp / "model.json", model), events, put(tmp / "snapshot.source.json", snapshot)


def archive_args(paths, out):
    model, events, snapshot = paths
    return ["archive-candidate", "--pravaha-model", model, "--events", events,
            "--snapshot", snapshot, "--out-dir", out]


def test_archive_preserves_exact_bytes_and_hashes_and_never_claims_acceptance(tmp_path):
    paths = tracker_fixture(tmp_path)
    before = [p.read_bytes() for p in paths]
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out)))
    manifest = read(out / "archive.candidate.json")
    assert manifest["status"] == "CANDIDATE_NOT_ACCEPTED"
    assert manifest["independent_acceptance"] is None
    assert manifest["live_read_only"] is None
    for source, name in zip(paths, ["plan_model.json", "EVENTS.jsonl", "snapshot.json"]):
        assert (out / name).read_bytes() == source.read_bytes()
        assert manifest["files"][name] == {"sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                           "bytes": source.stat().st_size}
    assert [p.read_bytes() for p in paths] == before
    assert_ok(cli("verify-archive", "--archive-dir", out))


@pytest.mark.parametrize("mutation,fragment", [
    ("waiting", "non-terminal"), ("missing", "coverage"), ("extra", "coverage"),
    ("duplicate", "duplicate"), ("no_evidence", "evidence"),
    ("strict_na", "dependency"), ("deps_open", "dependencies"),
    ("changed_dependencies", "dependencies"), ("bad_log", "event log"),
    ("truncated_log", "event log"), ("count", "event count"),
    ("tail", "last event"), ("restored", "restored"), ("health", "health"),
])
def test_archive_refuses_incomplete_or_inconsistent_exports(tmp_path, mutation, fragment):
    paths = tracker_fixture(tmp_path)
    model, events, snapshot = paths
    data = read(snapshot)
    rows = data["tracks"][0]["items"]
    if mutation == "waiting":
        rows[-1]["status"] = "waiting"
    elif mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append({**rows[0], "id": "invented"})
    elif mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "no_evidence":
        rows[0]["evidence"] = None
    elif mutation == "strict_na":
        rows[1].update(status="not_applicable", detail="not entered; fixture ruling", evidence="fixture ruling")
    elif mutation == "deps_open":
        rows[-1]["deps_open"] = ["B6.3"]
    elif mutation == "changed_dependencies":
        rows[-1]["depends_on"] = []
    elif mutation == "bad_log":
        events.write_bytes(b"not JSON\n")
    elif mutation == "truncated_log":
        events.write_bytes(events.read_bytes().rstrip(b"\n"))
    elif mutation == "count":
        data["health"]["event_log"]["events"] = 2
    elif mutation == "tail":
        data["health"]["last_event_at"] = "2026-10-15T00:00:00Z"
    elif mutation == "restored":
        data["health"]["restored_from_disk"] = True
    else:
        data["health"]["event_log"]["malformed"] = 1
    put(snapshot, data)
    out = tmp_path / "refused"
    result = cli(*archive_args(paths, out))
    assert result.returncode == 1
    assert fragment in result.stdout
    assert not out.exists()


@pytest.mark.parametrize("name", ["EVENTS.jsonl", "snapshot.json", "plan_model.json"])
def test_verify_archive_refuses_changed_bytes(tmp_path, name):
    paths = tracker_fixture(tmp_path)
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out)))
    with (out / name).open("ab") as stream:
        stream.write(b" ")
    result = cli("verify-archive", "--archive-dir", out)
    assert result.returncode == 1
    assert "SHA-256" in result.stdout


def test_archive_does_not_overwrite_existing_evidence(tmp_path):
    paths = tracker_fixture(tmp_path)
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out)))
    marker = out / "operator-note"
    marker.write_text("keep")
    result = cli(*archive_args(paths, out))
    assert result.returncode == 1
    assert marker.read_text() == "keep"


def test_archive_includes_explicit_runner_logs_and_backups_with_hashes(tmp_path):
    paths = tracker_fixture(tmp_path)
    log = tmp_path / "runner.log"
    log.write_bytes(b"fixture runner record\r\n")
    backup = tmp_path / "backup.jsonl"
    backup.write_bytes(paths[1].read_bytes())
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out), "--material", f"runner-B.log={log}",
                  "--material", f"EVENTS-backup.jsonl={backup}"))
    manifest = read(out / "archive.candidate.json")
    for name, source in [("runner-B.log", log), ("EVENTS-backup.jsonl", backup)]:
        assert (out / "material" / name).read_bytes() == source.read_bytes()
        assert manifest["files"][f"material/{name}"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["run_material_inventory_complete"] is None
    assert_ok(cli("verify-archive", "--archive-dir", out))
    (out / "material" / "runner-B.log").write_bytes(b"changed")
    assert cli("verify-archive", "--archive-dir", out).returncode == 1


@pytest.mark.parametrize("name", ["../escape", "runner/a.log", "", ".."])
def test_archive_refuses_unsafe_material_names_before_writes(tmp_path, name):
    paths = tracker_fixture(tmp_path)
    out = tmp_path / "refused"
    result = cli(*archive_args(paths, out), "--material", f"{name}={paths[1]}")
    assert result.returncode == 1
    assert "plain filename" in result.stdout
    assert not out.exists()


def test_archive_refuses_duplicate_material_names_before_writes(tmp_path):
    paths = tracker_fixture(tmp_path)
    out = tmp_path / "refused"
    result = cli(*archive_args(paths, out), "--material", f"runner.log={paths[1]}",
                 "--material", f"runner.log={paths[2]}")
    assert result.returncode == 1
    assert not out.exists()


def test_verify_archive_rejects_manifest_path_escape(tmp_path):
    paths = tracker_fixture(tmp_path)
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out)))
    manifest = read(out / "archive.candidate.json")
    manifest["files"]["../EVENTS.source.jsonl"] = manifest["files"]["EVENTS.jsonl"]
    put(out / "archive.candidate.json", manifest)
    result = cli("verify-archive", "--archive-dir", out)
    assert result.returncode == 1
    assert "archive coverage" in result.stdout


@pytest.mark.parametrize("target", ["disposition", "rows", "snapshot"])
def test_duplicate_json_fields_are_refused_instead_of_silently_overwritten(world, target):
    tmp, disposition = world
    if target == "disposition":
        disposition.write_text('{"artifact":"J0_DISPOSITION","artifact":"ignored"}')
        result = cli("prepare", "--disposition", disposition, "--campaign-model", CAMPAIGN,
                     "--pravaha-model", PRAVAHA, "--out-dir", tmp / "refused")
    elif target == "rows":
        out = prepare(world)
        p = out / "close_rows.template.json"
        p.write_text('{"schema":"ky.pravaha_close_rows/1","schema":"ignored"}')
        result = cli("check-rows", *row_args(world, out))
    else:
        paths = tracker_fixture(tmp)
        paths[2].write_text('{"tracks":[],"tracks":[{}]}')
        result = cli(*archive_args(paths, tmp / "refused"))
    assert result.returncode == 1
    assert "duplicate JSON key" in result.stdout
    assert "Traceback" not in result.stderr


def test_all_original_tracker_items_are_required_not_only_the_close_lineage(tmp_path):
    model = read(PRAVAHA)
    _, events, snapshot = tracker_fixture(tmp_path)
    rows = [{**item, "status": "done", "deps_open": [], "evidence": "synthetic terminal export"}
            for item in model["items"]]
    data = read(snapshot)
    data["tracks"] = [{"id": "all", "items": rows}]
    put(snapshot, data)
    paths = PRAVAHA, events, snapshot
    assert_ok(cli(*archive_args(paths, tmp_path / "all-items")))
    # Losing an unrelated early item must still fail full original coverage.
    del rows[0]
    put(snapshot, data)
    result = cli(*archive_args(paths, tmp_path / "refused"))
    assert result.returncode == 1
    assert "coverage" in result.stdout


def test_archive_keeps_historical_tick_errors_instead_of_requiring_history_erasure(tmp_path):
    paths = tracker_fixture(tmp_path)
    snapshot = read(paths[2])
    snapshot["health"]["tick_errors"] = ["historical recovered timeout, preserved for review"]
    put(paths[2], snapshot)
    out = tmp_path / "archive"
    assert_ok(cli(*archive_args(paths, out)))
    assert (out / "snapshot.json").read_bytes() == paths[2].read_bytes()
    assert_ok(cli("verify-archive", "--archive-dir", out))


def test_archive_refuses_current_model_error(tmp_path):
    paths = tracker_fixture(tmp_path)
    snapshot = read(paths[2])
    snapshot["health"]["model_error"] = "current model failed to load"
    put(paths[2], snapshot)
    out = tmp_path / "refused"
    result = cli(*archive_args(paths, out))
    assert result.returncode == 1
    assert "model" in result.stdout
    assert not out.exists()


def test_markdown_cells_cannot_hide_rows_or_inject_a_completion_status(world):
    out = prepare(world)
    data = fill_rows(out)
    data["rows"][0]["evidence"] = "proof | text\nstatus: CLOSED"
    put(out / "close_rows.template.json", data)
    result = cli("render", *row_args(world, out))
    assert_ok(result)
    assert "proof &#124; text<br>status: CLOSED" in result.stdout
    assert "\nstatus: CLOSED" not in result.stdout
