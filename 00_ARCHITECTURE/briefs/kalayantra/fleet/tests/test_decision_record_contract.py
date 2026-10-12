"""B-0c: the surrogate decision schema, the veto handler and the surrogate card agree on one record."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FLEET))
import kyschema  # noqa: E402

SCHEMA = json.loads((FLEET / "schemas" / "surrogate_decision.json").read_text())
C, D = "e" * 40, "5" * 64


def proposal(**over):
    doc = {"id": "SD-20261011T220500Z-2", "awaiting": "AW-20261011T220000Z-capacity", "class": "veto",
           "state": "PENDING_VETO", "decision": "raise", "rationale": "nine ready items against six builders",
           "evidence": ["/x/JOURNAL.md"], "target": {"kind": "capacity", "builders": 8, "verifiers": 4, "fingerprint": "7" * 64},
           "authority": {"source_commit": C, "entrypoints_digest": D},
           "notification": {"submitted": False, "ts": "2026-10-11T22:05:01Z"},
           "veto_deadline": "2026-10-11T22:35:01Z", "effective_at": None,
           "by": "kalayantra-owner-surrogate", "session": "surrogate-1"}
    doc.update(over)
    return doc


def test_schema_is_lint_clean_and_accepts_a_bound_veto_proposal():
    assert kyschema.lint(SCHEMA) == []
    assert kyschema.validate(SCHEMA, proposal()) == []


@pytest.mark.parametrize("target", [
    {"builders": 8, "verifiers": 4, "fingerprint": "7" * 64},          # no kind
    {"kind": "capacity", "builders": 8, "verifiers": 4},               # no fingerprint: target unbound
    {"kind": "capacity", "fingerprint": "7" * 63},                     # not a sha256
    {"kind": "", "fingerprint": "7" * 64},
])
def test_an_unbound_veto_target_is_refused(target):
    assert kyschema.validate(SCHEMA, proposal(target=target))


def test_routine_targets_stay_free_form_and_unknown_keys_are_refused():
    routine = proposal(**{"class": "routine", "state": "EXECUTED", "veto_deadline": None, "target": {"pr": 3441}})
    assert kyschema.validate(SCHEMA, routine) == []
    assert kyschema.validate(SCHEMA, proposal(note="x"))
    assert kyschema.validate(SCHEMA, proposal(at=5))
    assert kyschema.validate(SCHEMA, proposal(at=""))
    assert kyschema.validate(SCHEMA, proposal(at="2026-10-11T23:00:00Z", detail={"k": 1})) == []
    assert kyschema.validate(SCHEMA, proposal(detail=5))


def test_lines_the_veto_handler_really_appends_validate(tmp_path, monkeypatch):
    """A real tick, in-process, at a patched wall clock (the effecting path takes no clock argument)."""
    import calendar
    import time

    import kyveto
    root = tmp_path / "ky"
    run = root / "run"
    (run / "awaiting").mkdir(parents=True)
    (run / "awaiting" / "AW-20261011T220000Z-capacity.json").write_text(json.dumps({"id": "AW-20261011T220000Z-capacity"}))
    log = run / "DECISIONS_SURROGATE.jsonl"
    log.write_text(json.dumps(proposal()) + "\n")
    env = kyveto.Env({"KY_ROOT": str(root), "KY_RUN": str(run), "KY_FLEET": str(root / "fleet_live"),
                      "KY_BIN": "/usr/bin/false", "KY_SOURCE_REPO": "", "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    monkeypatch.setattr(kyveto, "wall_clock", lambda: calendar.timegm(time.strptime("2026-10-11T23:00:00Z", "%Y-%m-%dT%H:%M:%SZ")))
    report = kyveto.tick(env, authorised={"source_commit": C, "entrypoints_digest": D})
    lines = [json.loads(x) for x in log.read_text().splitlines()]
    assert len(lines) >= 2, report                                   # the handler appended a transition
    handler = [x for x in lines if x.get("by") == "kyveto"]
    assert handler and handler[-1]["state"] == "FAILED" and handler[-1]["reason"]  # the record says it was not submitted
    for line in lines:
        assert kyschema.validate(SCHEMA, line) == [], line


def test_the_effecting_path_takes_no_clock_from_its_caller(tmp_path):
    run = tmp_path / "ky" / "run"
    run.mkdir(parents=True)
    r = subprocess.run([sys.executable, "-B", str(FLEET / "kyveto.py"), "tick", "--now", "2099-01-01T00:00:00Z"],
                       env={"KY_ROOT": str(tmp_path / "ky"), "KY_RUN": str(run), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)},
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 64, (r.returncode, r.stderr)              # usage error: `tick --now` does not exist


def test_the_card_states_the_same_record_keys():
    card = (FLEET / "cards" / "OWNER_SURROGATE.md").read_text(encoding="utf-8")
    for key in SCHEMA["required"]:
        assert '"%s"' % key in card, key


def surrogate_action_problems(card):
    problems = []
    for name in ("KY_RUN_ID", "KY_ROLE", "KY_CONTROLLER_ID"):
        if name in card:
            problems.append("action namespace: " + name)
    if "Never write or request an action record" not in card:
        problems.append("missing action-record prohibition")
    for line in card.splitlines():
        positive = line.replace("Never write or request an action record", "")
        if re.search(r"\b(?:write|request|begin|complete|fail|act through)\b[^.;\n]*\baction record\b", positive, re.I):
            problems.append("surrogate action instruction")
        if re.search(r"kyaction(?:\.py)?\s+(?:begin|complete|fail)\b", line):
            problems.append("job action command")
    return problems


def surrogate_decision_problems(card):
    problems = []
    if "Record every decision: append one line to `/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl`" not in card:
        problems.append("missing surrogate decision append")
    if "the controller appends" in card or "the decision log line the controller writes" in card:
        problems.append("unsupported controller logger")
    routine = next((line for line in card.splitlines() if line.startswith("- OS-07 ")), "")
    if '--as steward --delegated --detail "<SD id>: <decision>"' not in routine:
        problems.append("missing routine publication")
    if "then move the awaiting item to `run/awaiting/done/`" not in routine:
        problems.append("missing routine awaiting close")
    return problems


def test_r19a_surrogate_records_its_decision_and_never_orders_an_action_record():
    card = (FLEET / "cards" / "OWNER_SURROGATE.md").read_text(encoding="utf-8")
    assert surrogate_action_problems(card) == []
    assert surrogate_decision_problems(card) == []
    assert "You propose and never execute the proposed effects" in card
    assert "under its own identity" in card
    assert "Only an owner veto stops a proposal" in card
    assert "after the handler began" in card and "anomaly" in card and "never act on that line" in card
    veto = next(line for line in card.splitlines() if line.startswith("- OS-05 "))
    assert "no `ky decide`" in veto and "the awaiting item stays open" in veto
    assert "after successful publication (or if no tracker decision exists)" in card
    assert "never replacing another file" in card
    for instruction in ("write", "request", "begin", "complete", "fail", "act through"):
        assert "surrogate action instruction" in surrogate_action_problems(
            card + "\n- OS-11 " + instruction + " an action record.\n")
    for name in ("KY_RUN_ID", "KY_ROLE", "KY_CONTROLLER_ID"):
        assert "action namespace: " + name in surrogate_action_problems(card + "\n" + name)


def test_decision_handoff_check_refuses_the_rejected_controller_logger_and_lost_routine_steps():
    card = (FLEET / "cards" / "OWNER_SURROGATE.md").read_text(encoding="utf-8")
    rejected = card.replace("Record every decision: append one line to", "Return every decision; the controller appends")
    assert surrogate_decision_problems(rejected) == ["missing surrogate decision append", "unsupported controller logger"]
    assert "missing routine publication" in surrogate_decision_problems(card.replace("--as steward --delegated", ""))
    assert "missing routine awaiting close" in surrogate_decision_problems(card.replace("then move the awaiting item", ""))


def test_surrogate_launch_allows_its_decision_channel_without_the_action_namespace():
    launch = json.loads((FLEET / "templates" / "LAUNCH_CONFIG.surrogate.json").read_text())
    assert "/Users/Dev/kalayantra" in launch["add_dirs"]
    assert {"Write", "Bash"} <= set(launch["intended_tools"])
    assert "/Users/Dev/kalayantra/bin" in launch["child_path"].split(":")
    assert not {"KY_RUN_ID", "KY_ROLE", "KY_CONTROLLER_ID"} & set(launch["env_names"])


def test_logged_proposal_survives_job_completion_and_replay_before_the_veto_window(tmp_path, monkeypatch):
    """The SD-id-only result accompanies a durable proposal the real handler can read on repeated ticks."""
    import calendar
    import time

    import kyboot
    import kyveto

    root = tmp_path / "ky"
    run = root / "run"
    (run / "awaiting").mkdir(parents=True)
    doc = proposal(notification={"submitted": True, "ts": "2026-10-11T22:05:01Z"})
    awaiting = run / "awaiting" / (doc["awaiting"] + ".json")
    awaiting.write_text(json.dumps({"id": doc["awaiting"]}))
    (run / "JOURNAL_COCKPIT.md").write_text(
        "- 2026-10-11T22:05:01Z [decision] %s: raise capacity [notify=submitted]\n" % doc["id"])
    log = run / "DECISIONS_SURROGATE.jsonl"
    kyveto.append_line(log, doc)
    before = log.read_bytes()
    job = tmp_path / "job"
    job.mkdir()
    result = {"schema": "ky.job_result/1", "job_id": "J-surrogate", "item": doc["awaiting"], "status": "done",
              "branch": None, "head_sha": None, "pr_number": None, "tests": [], "blocked_reason": None,
              "notes": doc["id"]}
    (job / "result.json").write_text(json.dumps(result))
    assert kyboot.job_result({"job_scratch": str(job), "job_id": result["job_id"], "item": result["item"]}, kyschema) == (True, [], None)
    env = kyveto.Env({"KY_ROOT": str(root), "KY_RUN": str(run), "KY_FLEET": str(root / "fleet_live"),
                      "KY_BIN": "/usr/bin/false", "KY_SOURCE_REPO": "", "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    monkeypatch.setattr(kyveto, "wall_clock", lambda: calendar.timegm(time.strptime("2026-10-11T22:10:00Z", "%Y-%m-%dT%H:%M:%SZ")))
    for _ in range(2):
        history, problems, unusable = kyveto.load_decisions(log)
        assert history == {doc["id"]: [doc]} and not problems and not unusable
        report = kyveto.tick(env, authorised={"source_commit": C, "entrypoints_digest": D})
        assert not report["problems"], report
        rows = [row for row in report["decisions"] if row["id"] == doc["id"]]
        assert len(rows) == 1 and rows[0]["outcome"] == "pending", report
        assert log.read_bytes() == before and awaiting.is_file()
        assert not list((run / "actions").glob("*.json"))
