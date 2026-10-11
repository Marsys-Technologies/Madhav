"""B-0c: the surrogate decision schema, the veto handler and the surrogate card agree on one record."""
import json
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
