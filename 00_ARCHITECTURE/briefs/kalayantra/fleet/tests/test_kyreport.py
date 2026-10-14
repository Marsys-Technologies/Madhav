"""KV3-B-KYREPORT: kyreport.py reports what was measured and says `unknown` for everything else (plan v2.7 §13).

Every test runs the script from a temporary fleet directory against a temporary KY_RUN, with a fake `gh`, a fake
`launchctl` / `claude` that only record that they were called (they never are), and a HOME that holds nothing.
The only processes signalled are the `sleep` children a test started itself.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
REPO = FLEET.parents[3]
TRACKER = REPO / "platform" / "scripts" / "governance"
sys.path.insert(0, str(FLEET))
import kyaction  # noqa: E402
import kyreport  # noqa: E402

CLASSES = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
GREEN = ("HEALTHY", "PASS", "DONE", "READY_TO_START", "verified", "PROGRESS", "submitted")
HEAD_A = "a" * 40
T0 = "2026-10-12T08:00:00+00:00"

FAKE_RECORDER = """#!/bin/sh
echo "$0 $*" >> "%s"
exit 0
"""

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys
here = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(here, "gh_calls.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
try:
    fx = json.load(open(os.path.join(here, "gh.json")))
except OSError:
    sys.stderr.write("gh: not signed in\n"); sys.exit(4)
a = sys.argv[1:]
if len(a) != 2 or a[0] != "api" or a[1] not in fx:
    sys.stderr.write("gh: HTTP 404\n"); sys.exit(1)
print(json.dumps(fx[a[1]]))
'''

SHIM = '''#!/usr/bin/env python3
"""the real %(name)s.py, imported once per process (python3 -B compiles the copy again every time)"""
import sys
sys.path.insert(0, %(fleet)r)
import %(name)s as real
main = real.main
if __name__ == "__main__":
    sys.exit(main())
'''

FAKE_KYLOOP = r'''#!/usr/bin/env python3
"""the real kyloop.py for `admin show|child`; a fixture for the two qualification questions"""
import json, os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, %r)
import kyloop as real


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) == 3 and a[0] == "admin" and a[1] in ("expected-qualification", "launch-config"):
        try:
            fx = json.load(open(os.path.join(here, "qualification.json")))
        except OSError:
            sys.stderr.write("no launch configuration\n")
            return 1
        if a[1] == "launch-config":
            print(json.dumps({"role": a[2], "model": "m"}))
        else:
            print(json.dumps({"role": a[2], "receipt_path": fx["receipt_path"]}))
        return 0
    return real.main(a)


if __name__ == "__main__":
    sys.exit(main())
''' % str(FLEET)

FAKE_KYQUALIFY = r'''#!/usr/bin/env python3
import json, os, sys
here = os.path.dirname(os.path.realpath(__file__))
fx = json.load(open(os.path.join(here, "qualification.json")))
a = sys.argv[1:]
with open(os.path.join(here, "kyqualify_calls.jsonl"), "a") as f:
    f.write(json.dumps({"argv": a, "config": json.load(open(a[a.index("--config") + 1]))}) + "\n")
if fx["mode"] == "crash":
    sys.exit(2)
ok = fx["mode"] == "pass"
print(json.dumps({"check": "PASS" if ok else "REFUSED", "reasons": [] if ok else ["evidence_hash_mismatch"],
                  "receipt": a[1], "context": "launchd"}))
sys.exit(0 if ok else 1)
'''

FAKE_KYVETO = r'''#!/usr/bin/env python3
import json, os, sys
here = os.path.dirname(os.path.realpath(__file__))


def main(argv=None):
    fx = json.load(open(os.path.join(here, "veto_status.json")))
    print(json.dumps(fx["report"]))
    return fx["rc"]


if __name__ == "__main__":
    sys.exit(main())
'''

FAKE_BASELINE = r'''#!/usr/bin/env python3
"""fixture: the adapter face of token_baseline.py (--json OUT; keys sources, grand_total, by_role, top_sessions)"""
import json, sys
ROWS = %s
a = sys.argv[1:]
rows = [dict(r, total=r["input"] + r["output"] + r["cache_creation"] + r["cache_read"]) for r in ROWS]
grand = {k: sum(r[k] for r in rows) for k in ("input", "output", "cache_creation", "cache_read", "total")}
with open(a[a.index("--json") + 1], "w") as f:
    json.dump({"sources": {"claude_files": len(rows)}, "grand_total": grand, "by_role": [], "top_sessions": rows}, f)
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, text, mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode:
        path.chmod(mode)
    return path


def write_json(path, obj):
    return write(path, json.dumps(obj, indent=1) + "\n")


def tree(root):
    """every file under root with its content hash: what `nothing is written` is compared on"""
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in sorted(Path(root).rglob("*")) if p.is_file()}


def lstart(pid):
    ident = kyaction.ps_identity(pid)
    assert ident, "ps could not name pid %s" % pid
    return ident[1]


class World:
    def __init__(self, tmp, monkeypatch):
        self.tmp = tmp
        self.monkeypatch = monkeypatch
        self.root = tmp / "kalayantra"
        self.run = self.root / "run"
        self.run.mkdir(parents=True)
        self.fleet = tmp / "fleet"
        self.fleet.mkdir()
        for name in ("kyreport.py", "kyaction.py"):
            shutil.copy(FLEET / name, self.fleet / name)
        for name in ("kyloop", "kyveto"):
            write(self.fleet / (name + ".py"), SHIM % {"name": name, "fleet": str(FLEET)})
        self.bin = tmp / "bin"
        self.calls = tmp / "launch_calls.log"
        for name in ("launchctl", "claude", "codex"):
            write(self.bin / name, FAKE_RECORDER % self.calls, 0o755)
        write(self.bin / "gh", FAKE_GH, 0o755)
        (tmp / "home").mkdir()
        (tmp / "tmp").mkdir()
        self.env = {"PATH": "%s:/usr/bin:/bin" % self.bin, "HOME": str(tmp / "home"), "TMPDIR": str(tmp / "tmp"),
                    "KY_ROOT": str(self.root), "KY_RUN": str(self.run), "KY_TRACKER_LIVE": str(TRACKER),
                    "KY_GH": str(self.bin / "gh"), "LANG": "en_US.UTF-8"}

    def cli(self, *args, env=None):
        r = subprocess.run([sys.executable, "-B", str(self.fleet / "kyreport.py")] + [str(a) for a in args],
                           capture_output=True, text=True, env=dict(self.env, **(env or {})), timeout=120,
                           stdin=subprocess.DEVNULL)
        return r

    def report(self, *args, env=None):
        """the status report, made in this process by the module's own report() on the temporary fleet"""
        opts = dict(zip(args[::2], [str(a) for a in args[1::2]]))
        assert set(opts) <= {"--events", "--model"}
        with self.monkeypatch.context() as m:
            for key, value in dict(self.env, **(env or {})).items():
                m.setenv(key, value)
            m.setattr(kyreport, "FLEET", self.fleet)
            out = kyreport.report(self.run, opts.get("--events") or str(self.run / "EVENTS.jsonl"),
                                  opts.get("--model"), os.environ["KY_TRACKER_LIVE"])
        return json.loads(json.dumps(out))

    def cli_report(self, *args):
        r = self.cli(*args)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)

    # ---- fixtures
    def job(self, job_id, **fields):
        doc = {"schema": "ky.job/1", "job_id": job_id, "item": "KV3-X", "kind": "BUILD", "role": "builder",
               "phase": "ended", "provider_session_id": "sess-" + job_id, "result_event": None}
        doc.update(fields)
        doc = {k: v for k, v in doc.items() if v != "ABSENT"}
        write_json(self.run / "jobs" / job_id / "state.json", doc)

    def install_receipt(self, mode="final"):
        return write_json(self.run / "INSTALL_RECEIPT.json", {"schema": "ky.install_receipt/1", "mode": mode})

    def loop(self, name="planner", **fields):
        self.install_receipt()
        doc = {"enabled": True,
               "controller": {"controller_id": "CTL-test", "pid": os.getpid(), "pgid": os.getpgid(0),
                              "process_start": lstart(os.getpid()), "started_at": kyaction.utc()},
               "bundle": {"receipt_sha256": kyaction.sha_file(self.run / "INSTALL_RECEIPT.json")},
               "expected_child": None, "waiting": "no_eligible_work", "last_iteration_at": kyaction.utc(),
               "no_progress_count": 0}
        doc.update(fields)
        write_json(self.run / "loops" / (name + ".json"), doc)

    def baseline_repo(self, rows):
        """a git repository whose HEAD commit holds the fake baseline script → (repo, commit, path, blob sha256)"""
        repo = self.tmp / "source"
        path = "scripts/token_economy/token_baseline.py"
        text = FAKE_BASELINE % json.dumps(rows)
        write(repo / path, text)
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
               "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        subprocess.run(git + ["add", "-A"], check=True, capture_output=True)
        subprocess.run(git + ["commit", "-q", "-m", "baseline"], check=True, capture_output=True)
        commit = subprocess.run(git + ["rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        return repo, commit, path, sha(text.encode("utf-8"))

    def review_receipt(self, commit, path, digest, **over):
        doc = {"verdict": "ACCEPTED", "reviewer_session_id": "sess-reviewer", "author_session_id": "sess-author",
               "source_commit": commit, "inputs": {path: digest}}
        doc.update(over)
        return write_json(self.tmp / "review_receipt.json", doc)

    def import_baseline(self, rows, parent_includes_children=None):
        repo, commit, path, digest = self.baseline_repo(rows)
        receipt = self.review_receipt(commit, path, digest)
        dest = self.tmp / "installed" / "token_baseline.py"
        r = self.cli("baseline-import", "--repo", repo, "--commit", commit, "--path", path,
                     "--review-receipt", receipt, "--dest", dest)
        assert r.returncode == 0, r.stderr
        if parent_includes_children is not None:     # the proof is another job's; here the receipt is the fixture
            doc = json.loads((self.run / "BASELINE_RECEIPT.json").read_text())
            doc["parent_includes_children"] = parent_includes_children
            write_json(self.run / "BASELINE_RECEIPT.json", doc)
        return dest


@pytest.fixture
def w(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch)


def usage(i, cc, cr, o):
    return dict(zip(CLASSES, (i, cc, cr, o)))


def result_event(session, i=10, cc=20, cr=30, o=40):
    return {"type": "result", "subtype": "success", "session_id": session, "usage": usage(i, cc, cr, o)}


def row(session, i=1, o=2, cc=3, cr=4):
    return {"key": "claude:" + session, "input": i, "output": o, "cache_creation": cc, "cache_read": cr}


def values(node, path="report"):
    """every (path, value) of a node that carries `value` — figures and signals alike"""
    if isinstance(node, dict):
        if "value" in node:
            yield path, node["value"]
        for k, v in node.items():
            yield from values(v, "%s.%s" % (path, k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from values(v, "%s[%d]" % (path, i))


def leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from leaves(v)
    else:
        yield value


MODEL = {"campaign": "t", "control_plane": {"guarded_completion": True}, "streams": [], "phases": [],
         "tracks": [{"id": "T", "title": "t"}],
         "decisions": [{"id": "D-1", "title": "d", "needed_by": "A"}],
         "items": [{"id": "A", "title": "a", "track": "T"},
                   {"id": "B", "title": "b", "track": "T"},
                   {"id": "C", "title": "c", "track": "T"},
                   {"id": "DEC", "title": "d", "track": "T", "done_by": "decision", "decision": "D-1"},
                   {"id": "J", "title": "j", "track": "T", "done_by": "join", "depends_on": ["A", "DEC"]}]}
EVENTS = [{"kind": "item", "item": "A", "state": "done", "guarded": True, "ts": T0, "actor": "steward"},
          {"kind": "item", "item": "B", "state": "done", "ts": "2026-10-12T08:01:00+00:00", "actor": "A"},
          {"kind": "decision", "decision": "D-1", "state": "decided", "ts": "2026-10-12T08:02:00+00:00",
           "actor": "native"},
          {"kind": "verdict", "item": "A", "result": "ACCEPTED", "head": HEAD_A, "phase": "pre_merge",
           "ts": "2026-10-12T08:03:00+00:00", "actor": "reviewer"},
          {"kind": "verdict", "item": "B", "result": "REJECTED", "head": "b" * 40, "phase": "pre_merge",
           "ts": "2026-10-12T08:04:00+00:00", "actor": "reviewer"}]


def events_text(events=EVENTS):
    return "".join(json.dumps(e) + "\n" for e in events)


# ───────────────────────────── the command line ─────────────────────────────

def test_usage_errors_exit_64(w):
    for args in (["--nope"], ["--events"], ["approval"], ["baseline-import", "--repo", "x"], ["status", "extra"]):
        r = w.cli(*args)
        assert r.returncode == 64, (args, r.stdout, r.stderr)
        assert r.stdout == ""


def test_missing_run_directory_exits_66(w):
    r = w.cli(env={"KY_RUN": str(w.tmp / "absent")})
    assert r.returncode == 66 and r.stdout == ""
    r = w.cli("baseline-import", "--repo", "x", "--commit", HEAD_A, "--path", "p", "--review-receipt", "v",
              "--dest", str(w.tmp / "d"), env={"KY_RUN": str(w.tmp / "absent")})
    assert r.returncode == 66


def test_empty_run_reads_unknown_never_a_number_or_green_and_starts_nothing(w):
    before = tree(w.tmp)
    rep = w.cli_report()
    assert tree(w.tmp) == before                              # it writes nothing
    assert not list(w.tmp.rglob("__pycache__"))
    assert not w.calls.exists()                               # it launches and admits nothing
    assert rep["schema"] == "ky.report/1" and rep["mode"] == "status"
    assert rep["savings"] == "cannot_be_estimated" and rep["throughput"] == "cannot_be_estimated"
    seen = dict(values(rep))
    assert len(seen) >= 20
    for path, value in seen.items():
        for leaf in leaves(value):
            assert not isinstance(leaf, (int, float)), "%s reads as a number: %r" % (path, value)
            assert leaf not in GREEN, "%s reads green: %r" % (path, value)
    for key in ("guarded_completed", "decision_completions", "joins", "accepted_heads", "weighted_progress"):
        assert rep["completions"][key]["value"] == "unknown" and rep["completions"][key]["why"]
    assert rep["tokens"]["total"]["value"] == "unknown"
    assert rep["jobs"]["count"]["value"] == "unknown"
    assert "kygate.sh" in rep["helpers_unavailable"]


def test_today_is_the_status_report(w):
    w.job("J-1", result_event=result_event("sess-J-1"))
    a, b, c = w.cli_report(), w.cli_report("--today"), w.report()
    for rep in (a, b, c):
        rep.pop("generated_at")
    assert a == b == c and a["tokens"]["total"]["partial"]["total"] == 100


# ───────────────────────────── completions ─────────────────────────────

def test_completions_are_reported_separately_with_denominator_and_boundary(w):
    text = events_text()
    write(w.run / "EVENTS.jsonl", text + '{"kind": "item", "item": "C", "sta')      # an unfinished last line
    model = write_json(w.tmp / "model.json", MODEL)
    c = w.report("--model", model)["completions"]
    assert c["guarded_completed"]["value"] == ["A"] and c["guarded_completed"]["count"] == 1
    assert c["guarded_completed"]["denominator"] == {"scope": "items completed by guarded event", "count": 3}
    assert c["decision_completions"]["value"] == ["DEC"] and c["decision_completions"]["denominator"]["count"] == 1
    assert c["joins"]["value"] == ["J"] and c["joins"]["denominator"]["count"] == 1
    assert c["accepted_heads"]["value"] == [HEAD_A] and c["accepted_heads"]["denominator"]["count"] == 2
    assert c["weighted_progress"]["value"] == 60.0 and c["weighted_progress"]["denominator"]["count"] == 5
    assert c["rejection_rate"]["value"] == 0.5 and c["rejection_rate"]["denominator"]["count"] == 2
    for key in c:
        assert c[key]["observed"] == {"events_path": str(w.run / "EVENTS.jsonl"), "events_lines": 5,
                                      "prefix_sha256": sha(text.encode()), "from": T0,
                                      "to": "2026-10-12T08:04:00+00:00"}


def test_events_argument_selects_the_log(w):
    other = write(w.tmp / "other.jsonl", events_text(EVENTS[:1]))
    model = write_json(w.tmp / "model.json", MODEL)
    c = w.report("--events", other, "--model", model)["completions"]
    assert c["guarded_completed"]["value"] == ["A"] and c["joins"]["value"] == []
    assert c["joins"]["observed"]["events_lines"] == 1


def test_an_acceptance_revoked_at_the_same_head_is_not_an_accepted_head(w):
    later = dict(EVENTS[3], result="REJECTED", ts="2026-10-12T08:05:00+00:00")
    write(w.run / "EVENTS.jsonl", events_text(EVENTS + [later]))
    c = w.report("--model", write_json(w.tmp / "model.json", MODEL))["completions"]
    assert c["accepted_heads"]["value"] == []


@pytest.mark.parametrize("case", ["no_model", "no_events", "malformed_line", "unguarded_model", "no_tracker"])
def test_completions_unknown_when_a_source_is_missing(w, case):
    write(w.run / "EVENTS.jsonl", events_text())
    model = write_json(w.tmp / "model.json", MODEL)
    args, env = ["--model", model], {}
    if case == "no_model":
        args = []
    elif case == "no_events":
        (w.run / "EVENTS.jsonl").unlink()
    elif case == "malformed_line":
        write(w.run / "EVENTS.jsonl", events_text() + "not json\n")
    elif case == "unguarded_model":
        args = ["--model", write_json(w.tmp / "model.json", dict(MODEL, control_plane={}))]
    else:
        env = {"KY_TRACKER_LIVE": str(w.tmp / "no_tracker")}
    c = w.report(*args, env=env)["completions"]
    assert c["guarded_completed"]["value"] == "unknown" and c["guarded_completed"]["why"]
    assert "count" not in c["guarded_completed"]
    if case != "unguarded_model":
        for key in ("decision_completions", "joins", "weighted_progress"):
            assert c[key]["value"] == "unknown", key
    for key in ("accepted_heads", "rejection_rate"):           # these two need the event log only
        assert (c[key]["value"] == "unknown") == (case in ("no_events", "malformed_line")), key


# ───────────────────────────── jobs ─────────────────────────────

def test_jobs_a_missing_field_is_unknown(w):
    w.job("J-1", result_event=result_event("sess-J-1"), outcome="done", failure_fp=None, attempt=1)
    w.job("J-2", role="ABSENT", phase="ABSENT", outcome="failed", failure_fp="fp-1", attempt=2)
    w.job("J-3", outcome="failed", failure_fp="fp-1", attempt=3)
    write(w.run / "jobs" / "J-4" / "state.json", "{broken")
    jobs = w.report()["jobs"]
    assert jobs["count"]["value"] == 4
    rows = {r["job_dir"]: r for r in jobs["rows"]}
    assert rows["J-2"]["role"] == "unknown" and rows["J-2"]["phase"] == "unknown"
    assert rows["J-1"]["role"] == "builder" and rows["J-1"]["result_event"] == "present"
    assert rows["J-3"]["result_event"] == "unknown"
    assert rows["J-4"]["job_id"] == "unknown" and rows["J-4"]["state"].startswith("unreadable")
    assert jobs["by_phase"]["value"] == {"ended": 2, "unknown": 2}
    assert jobs["failure_fingerprints"]["value"] == "unknown"          # one record cannot be read
    (w.run / "jobs" / "J-4" / "state.json").unlink()
    (w.run / "jobs" / "J-4").rmdir()
    jobs = w.report()["jobs"]
    assert jobs["failure_fingerprints"]["value"] == {"fp-1": {"jobs": 2, "max_attempt": 3}}
    assert jobs["count"]["denominator"] == {"scope": "job state records under %s" % (w.run / "jobs"), "count": 3}


# ───────────────────────────── tokens: the seven §13 fixtures ─────────────────────────────

def test_tokens_no_verified_baseline_total_is_unknown_never_zero(w):
    w.job("J-1", result_event=result_event("sess-J-1"))
    t = w.report()["tokens"]
    assert t["baseline"]["value"] == "unknown" and "BASELINE_RECEIPT.json" in t["baseline"]["why"]
    assert t["total"]["value"] == "unknown" and t["total"]["value"] != 0
    assert t["total"]["partial"] == dict(usage(10, 20, 30, 40), total=100)       # what was measured, labelled
    assert t["by_role"]["value"] == "unknown" and t["per_guarded_completion"]["value"] == "unknown"
    assert t["classes"] == list(CLASSES)


def test_tokens_normal_completion_with_a_verified_baseline(w):
    w.import_baseline([])
    w.job("J-1", result_event=result_event("sess-J-1"))
    w.job("J-2", role="reviewer", kind="REVIEW", result_event=result_event("sess-J-2", 1, 1, 1, 1))
    w.job("J-3", phase="prepared", provider_session_id=None)             # never launched: owns no session
    t = w.report()["tokens"]
    assert t["baseline"]["value"] == "verified_installed"
    assert t["total"]["value"] == dict(usage(11, 21, 31, 41), total=104)
    assert t["total"]["denominator"] == {"scope": "provider sessions owned by a job or a role state", "count": 2}
    assert t["by_role"]["value"] == {"builder": dict(usage(10, 20, 30, 40), total=100),
                                     "reviewer": dict(usage(1, 1, 1, 1), total=4)}
    assert set(t["by_kind"]["value"]) == {"BUILD", "REVIEW"}
    assert t["not_started_jobs"] == ["J-3"]


def test_tokens_a_duplicated_result_event_counts_once(w):
    w.import_baseline([])
    ev = result_event("sess-dup")
    w.job("J-1", provider_session_id="sess-dup", result_event=ev)
    w.job("J-2", provider_session_id="sess-dup", result_event=dict(ev))          # the same session, identical payload
    t = w.report()["tokens"]
    assert t["total"]["value"] == dict(usage(10, 20, 30, 40), total=100)
    assert t["total"]["denominator"]["count"] == 1
    assert [s["duplicates_dropped"] for s in t["sessions"]] == [1]


def test_tokens_two_different_results_for_one_session_are_not_added(w):
    w.import_baseline([])
    w.job("J-1", provider_session_id="sess-dup", result_event=result_event("sess-dup"))
    w.job("J-2", provider_session_id="sess-dup", result_event=result_event("sess-dup", 99, 0, 0, 0))
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and "sess-dup" in json.dumps(t["uncovered"])


def test_tokens_a_killed_job_makes_the_total_unknown_and_the_rest_partial(w):
    w.import_baseline([row("someone-else")])
    w.job("J-1", result_event=result_event("sess-J-1"))
    w.job("J-2", outcome="interrupted", result_event=None)                # killed: no result event
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown"
    assert t["total"]["partial"] == dict(usage(10, 20, 30, 40), total=100)
    assert [u["session"] for u in t["uncovered"]] == ["sess-J-2"]
    assert t["by_kind"]["value"] == "unknown" and t["by_kind"]["partial"]["BUILD"]["total"] == 100


def test_tokens_a_killed_job_is_counted_only_from_the_verified_baseline(w):
    dest = w.import_baseline([row("sess-J-2", i=1, o=2, cc=3, cr=4)])
    w.job("J-1", result_event=result_event("sess-J-1"))
    w.job("J-2", outcome="interrupted", result_event=None)
    before = tree(w.tmp)
    t = w.report()["tokens"]
    assert tree(w.tmp) == before
    assert t["total"]["value"] == dict(usage(11, 23, 34, 42), total=110)
    assert {s["session"]: s["source"] for s in t["sessions"]} == {"sess-J-1": "result_event", "sess-J-2": "baseline"}
    dest.chmod(0o644)
    dest.write_text(dest.read_text() + "# edited after the review\n")    # the installed file is not the reviewed blob
    t = w.report()["tokens"]
    assert t["baseline"]["value"] == "unknown" and "sha256" in t["baseline"]["why"]
    assert t["total"]["value"] == "unknown"


def test_tokens_children_are_added_only_when_the_parent_is_proven_not_to_include_them(w):
    w.job("J-1", result_event=result_event("sess-J-1"))
    w.job("J-1c", parent_session_id="sess-J-1", result_event=result_event("sess-J-1c", 1, 1, 1, 1))
    w.import_baseline([])
    t = w.report()["tokens"]                                              # an import records null: not proven
    assert t["total"]["value"] == "unknown"
    assert t["uncovered"][0]["session"] == "sess-J-1c" and "parent_includes_children" in t["uncovered"][0]["why"]
    receipt = json.loads((w.run / "BASELINE_RECEIPT.json").read_text())
    write_json(w.run / "BASELINE_RECEIPT.json", dict(receipt, parent_includes_children=False))
    assert w.report()["tokens"]["total"]["value"] == dict(usage(11, 21, 31, 41), total=104)
    write_json(w.run / "BASELINE_RECEIPT.json", dict(receipt, parent_includes_children=True))
    t = w.report()["tokens"]
    assert t["total"]["value"] == dict(usage(10, 20, 30, 40), total=100)
    assert [s["session"] for s in t["sessions"] if s["source"] == "included_in_parent"] == ["sess-J-1c"]
    write_json(w.run / "BASELINE_RECEIPT.json", dict(receipt, parent_includes_children="false"))
    assert w.report()["tokens"]["total"]["value"] == "unknown"


def test_tokens_an_orphan_child_is_uncovered_even_when_parents_include_children(w):
    w.import_baseline([], parent_includes_children=True)
    w.job("J-1", result_event=result_event("sess-J-1"))
    w.job("J-1c", parent_session_id="sess-nobody", result_event=result_event("sess-J-1c", 1000, 1000, 1000, 1000))
    t = w.report()["tokens"]                                              # its parent is counted nowhere here
    assert t["total"]["value"] == "unknown" and t["total"]["partial"] == dict(usage(10, 20, 30, 40), total=100)
    assert [u["session"] for u in t["uncovered"]] == ["sess-J-1c"] and "sess-nobody" in t["uncovered"][0]["why"]
    assert [s["source"] for s in t["sessions"]] == ["result_event", None]
    # the parent named by its job: counted → left out as inside it; a job nobody recorded → uncovered
    w.job("J-1c", parent_job_id="J-1", result_event=result_event("sess-J-1c", 1000, 1000, 1000, 1000))
    t = w.report()["tokens"]
    assert t["total"]["value"] == dict(usage(10, 20, 30, 40), total=100) and t["uncovered"] == []
    assert [s["source"] for s in t["sessions"]] == ["result_event", "included_in_parent"]
    w.job("J-1c", parent_job_id="J-nobody", result_event=result_event("sess-J-1c"))
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and [u["session"] for u in t["uncovered"]] == ["sess-J-1c"]
    # the two parent fields disagree
    w.job("J-1c", parent_job_id="J-1", parent_session_id="sess-other", result_event=result_event("sess-J-1c"))
    assert w.report()["tokens"]["total"]["value"] == "unknown"
    # the parent is recorded but its own usage is not counted (a killed job the baseline does not cover)
    w.job("J-1", result_event=None)
    w.job("J-1c", parent_session_id="sess-J-1", result_event=result_event("sess-J-1c"))
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and "partial" not in t["total"]
    assert sorted(u["session"] for u in t["uncovered"]) == ["sess-J-1", "sess-J-1c"]


def test_tokens_only_an_uncounted_child_with_a_guarded_completion_reads_unknown(w):
    w.import_baseline([], parent_includes_children=True)
    w.job("J-1c", parent_session_id="sess-gone", result_event=result_event("sess-J-1c", 1000, 1000, 1000, 1000))
    write(w.run / "EVENTS.jsonl", events_text())
    model = write_json(w.tmp / "model.json", MODEL)
    t = w.report("--model", model)["tokens"]
    assert t["total"]["value"] == "unknown" and t["total"]["why"] and "partial" not in t["total"]
    assert t["by_role"]["value"] == "unknown" and t["by_kind"]["value"] == "unknown"
    assert t["per_guarded_completion"]["value"] == "unknown"
    assert t["per_guarded_completion"]["denominator"]["count"] == 1
    assert w.cli_report("--model", model)["tokens"]["total"]["value"] == "unknown"     # a report, not a traceback


def test_tokens_interactive_planner_and_conductor_sessions(w):
    w.import_baseline([row("sess-planner"), row("sess-conductor", i=10, o=10, cc=10, cr=10)])
    write_json(w.run / "PLANNER_STATE.json", {"schema": "ky.role_state/1", "role": "planner", "active": {},
                                             "session_id": "sess-planner"})
    write_json(w.run / "CONDUCTOR_STATE.json", {"schema": "ky.role_state/1", "role": "conductor", "active": {},
                                               "session": {"session_id": "sess-conductor"}})
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and "KV3-B-KYDJOBS" in t["total"]["why"]   # whose jobs ran is not known
    assert t["total"]["partial"]["total"] == 50
    (w.run / "jobs").mkdir()                                              # job state is recorded: there are no jobs
    t = w.report()["tokens"]
    assert t["total"]["value"] == dict(usage(11, 13, 14, 12), total=50)
    assert t["by_role"]["value"]["planner"]["total"] == 10 and t["by_kind"]["value"]["interactive"]["total"] == 50
    # two identities in one role state: nobody owns the session
    write_json(w.run / "PLANNER_STATE.json", {"session_id": "sess-planner", "session": {"session_id": "sess-other"}})
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown"
    assert t["uncovered"][0]["owner"] == "role_state:planner" and "2 session identities" in t["uncovered"][0]["why"]
    # none
    write_json(w.run / "PLANNER_STATE.json", {"schema": "ky.role_state/1", "active": {}})
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and "0 session identities" in t["uncovered"][0]["why"]


def test_tokens_bootstrap_jobs(w):
    w.import_baseline([])
    w.job("J-b", kind="bootstrap", role="bootstrap", item="KV3-B-KYREPORT", result_event=result_event("sess-J-b"))
    t = w.report()["tokens"]
    assert t["by_kind"]["value"] == {"bootstrap": dict(usage(10, 20, 30, 40), total=100)}
    assert t["by_role"]["value"] == {"bootstrap": dict(usage(10, 20, 30, 40), total=100)}


@pytest.mark.parametrize("case", ["no_session_id", "unreadable_state", "usage_incomplete", "no_sessions",
                                  "baseline_fails", "bool_usage"])
def test_tokens_missing_records_are_unknown(w, case):
    w.import_baseline([])
    if case != "no_sessions":
        w.job("J-1", result_event=result_event("sess-J-1"))
    if case == "no_session_id":
        w.job("J-2", phase="live", provider_session_id=None)
    elif case == "unreadable_state":
        write(w.run / "jobs" / "J-2" / "state.json", "[]")
    elif case == "usage_incomplete":
        ev = result_event("sess-J-2")
        del ev["usage"]["output_tokens"]
        w.job("J-2", result_event=ev)
    elif case == "bool_usage":
        ev = result_event("sess-J-2")
        ev["usage"]["output_tokens"] = True
        w.job("J-2", result_event=ev)
    elif case == "baseline_fails":
        w.job("J-2", result_event=None)
        dest = w.tmp / "installed" / "token_baseline.py"
        text = "import sys\nsys.exit(3)\n"
        dest.chmod(0o644)
        dest.write_text(text)
        receipt = json.loads((w.run / "BASELINE_RECEIPT.json").read_text())
        write_json(w.run / "BASELINE_RECEIPT.json", dict(receipt, sha256=sha(text.encode())))
    t = w.report()["tokens"]
    assert t["total"]["value"] == "unknown" and t["total"]["why"]
    assert t["per_guarded_completion"]["value"] == "unknown"
    if case != "no_sessions":
        assert t["total"]["partial"]["total"] == 100


def test_tokens_per_guarded_completion(w):
    w.import_baseline([])
    w.job("J-1", result_event=result_event("sess-J-1"))
    write(w.run / "EVENTS.jsonl", events_text())
    t = w.report("--model", write_json(w.tmp / "model.json", MODEL))["tokens"]
    assert t["per_guarded_completion"]["value"] == dict(usage(10, 20, 30, 40), total=100)
    assert t["per_guarded_completion"]["denominator"] == {"scope": "distinct guarded-completed item ids", "count": 1}


# ───────────────────────────── baseline import ─────────────────────────────

def test_baseline_import_installs_the_reviewed_blob_under_one_action_record(w):
    repo, commit, path, digest = w.baseline_repo([row("s")])
    receipt = w.review_receipt(commit, path, digest)
    write(repo / path, "print('work tree, not the reviewed blob')\n")     # the work tree is never what is installed
    dest = w.tmp / "installed" / "token_baseline.py"
    r = w.cli("baseline-import", "--repo", repo, "--commit", commit, "--path", path, "--review-receipt", receipt,
              "--dest", dest)
    assert r.returncode == 0, r.stderr
    assert sha(dest.read_bytes()) == digest
    got = json.loads((w.run / "BASELINE_RECEIPT.json").read_text())
    assert got == {"schema": "ky.baseline_receipt/1", "source_commit": commit, "path": path, "sha256": digest,
                   "review_receipt_sha256": sha(receipt.read_bytes()), "installed_path": str(dest),
                   "parent_includes_children": None}
    records = [json.loads(p.read_text()) for p in (w.run / "actions").glob("*.json")]
    assert len(records) == 1 and records[0]["state"] == "DONE" and records[0]["kind"] == "baseline_import"
    assert records[0]["result"]["sha256"] == digest
    after = tree(w.tmp)
    again = w.cli("baseline-import", "--repo", repo, "--commit", commit, "--path", path, "--review-receipt",
                  receipt, "--dest", dest)
    assert again.returncode == 0 and tree(w.tmp) == after                 # the same import again changes nothing


@pytest.mark.parametrize("case", ["work_tree_file", "work_tree_path", "symbolic_commit", "unaccepted",
                                  "self_review", "no_reviewer", "other_commit", "other_digest", "no_receipt",
                                  "relative_dest", "dest_differs", "unknown_commit"])
def test_baseline_import_refusals_write_nothing(w, case):
    repo, commit, path, digest = w.baseline_repo([row("s")])
    dest = w.tmp / "installed" / "token_baseline.py"
    over, args = {}, {"--repo": repo, "--commit": commit, "--path": path, "--dest": dest}
    if case == "work_tree_file":              # a file that exists only in the work tree: not in the object store
        path2 = "scripts/token_economy/local_only.py"
        write(repo / path2, "print(1)\n")
        args["--path"] = path2
        over = {"inputs": {path2: sha(b"print(1)\n")}}
    elif case == "work_tree_path":            # an absolute path to the file on disk
        args["--path"] = str(repo / path)
        over = {"inputs": {str(repo / path): digest}}
    elif case == "symbolic_commit":           # HEAD moves: only an exact commit id is a source head
        args["--commit"] = "HEAD"
        over = {"source_commit": "HEAD"}
    elif case == "unaccepted":
        over = {"verdict": "PROCEED-WITH-FIXES"}
    elif case == "self_review":
        over = {"reviewer_session_id": "sess-author"}
    elif case == "no_reviewer":
        over = {"reviewer_session_id": None}
    elif case == "other_commit":
        over = {"source_commit": "c" * 40}
    elif case == "other_digest":              # the receipt reviewed other bytes (e.g. the edited work-tree file)
        over = {"inputs": {path: sha(b"something else")}}
    elif case == "relative_dest":
        args["--dest"] = "installed/token_baseline.py"
    elif case == "dest_differs":
        write(dest, "an installed file this import did not write\n")
    elif case == "unknown_commit":
        args["--commit"] = "d" * 40
        over = {"source_commit": "d" * 40}
    receipt = w.review_receipt(commit, path, digest, **over)
    args["--review-receipt"] = w.tmp / "absent.json" if case == "no_receipt" else receipt
    before = tree(w.tmp)
    r = w.cli("baseline-import", *[x for kv in args.items() for x in kv])
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert "REFUSED" in r.stderr and r.stdout == ""
    assert tree(w.tmp) == before
    assert not (w.run / "BASELINE_RECEIPT.json").exists() and not (w.run / "actions").exists()
    assert w.report()["tokens"]["baseline"]["value"] == "unknown"


# ───────────────────────────── signals: loop healthy ─────────────────────────────

def health(w, loop="planner"):
    return w.report()["signals"]["loop_healthy"][loop]


def test_a_waiting_loop_without_a_child_is_healthy_and_nothing_is_started(w):
    w.loop()
    before = tree(w.tmp)
    h = health(w)
    assert h["value"] == "HEALTHY", h
    assert h["child"] == "none" and h["waiting"] == "no_eligible_work"
    assert tree(w.tmp) == before and not w.calls.exists()


def test_a_loop_with_its_expected_child_alive_is_healthy(w):
    child = subprocess.Popen(["/bin/sleep", "120"], start_new_session=True)
    try:
        w.loop(expected_child={"run_id": "R-1", "pid": child.pid, "pgid": child.pid,
                               "process_start": lstart(child.pid)},
               waiting=None, last_iteration_at="2026-10-12T00:00:00Z")    # a child run is not a missed iteration
        h = health(w)
        assert h["value"] == "HEALTHY" and h["child"] == "alive", h
    finally:
        child.kill()                                                     # the test's own child, by handle
        child.wait()
    h = health(w)
    assert h["value"] == "UNHEALTHY" and "expected child" in " ".join(h["why"])


def test_a_loaded_job_without_a_verified_controller_identity_is_not_healthy(w):
    write(w.root / "LaunchAgents" / "in.marsys.kalayantra.planner.plist", "<plist/>")     # loaded says nothing
    w.loop(controller=None)
    assert health(w)["value"] == "UNHEALTHY" and "controller" in " ".join(health(w)["why"])
    gone = subprocess.Popen(["/usr/bin/true"])
    start = lstart(os.getpid())
    gone.wait()
    w.loop(controller={"controller_id": "CTL-dead", "pid": gone.pid, "process_start": start})
    h = health(w)
    assert h["value"] == "UNHEALTHY" and "controller" in " ".join(h["why"])
    w.loop(controller={"controller_id": "CTL-x", "pid": os.getpid(), "process_start": None})   # cannot be compared
    assert health(w)["value"] == "unknown"


@pytest.mark.parametrize("case", ["bundle", "no_receipt", "stale", "no_waiting", "unreconciled_child", "future"])
def test_loop_unhealthy_cases(w, case):
    w.loop()
    path = w.run / "loops" / "planner.json"
    doc = json.loads(path.read_text())
    if case == "bundle":
        write_json(w.run / "INSTALL_RECEIPT.json", {"mode": "final", "changed": True})
    elif case == "no_receipt":
        (w.run / "INSTALL_RECEIPT.json").unlink()
    elif case == "stale":
        doc["last_iteration_at"] = kyaction.utc(time.time() - 121)
    elif case == "future":
        doc["last_iteration_at"] = kyaction.utc(time.time() + 3600)
    elif case == "no_waiting":
        doc["waiting"] = None
    elif case == "unreconciled_child":
        write_json(w.run / "locks" / "planner" / "owner.json", {"child": "pending"})
    write_json(path, doc)
    h = health(w)
    assert h["value"] == "UNHEALTHY" and h["why"], h


def test_a_stopped_loop_reports_stopped(w):
    w.loop()
    write(w.run / "STOP_planner", "")
    assert health(w)["value"] == "STOPPED"
    (w.run / "STOP_planner").unlink()
    assert health(w)["value"] == "HEALTHY"
    w.loop(enabled=False)
    assert health(w)["value"] == "STOPPED"


def test_loop_health_unknown_without_a_readable_loop_state(w):
    assert health(w)["value"] == "unknown"
    write(w.run / "loops" / "planner.json", "{broken")
    assert health(w)["value"] == "unknown"
    w.loop("veto", waiting="idle")
    assert health(w, "veto")["value"] == "HEALTHY" and health(w, "conductor")["value"] == "unknown"


# ───────────────────────────── signals: loop making progress ─────────────────────────────

def test_loop_progress_is_the_judged_run_not_a_timestamp(w):
    def progress():
        return w.report()["signals"]["loop_progress"]["planner"]
    w.loop(no_progress_count=0, last_run_id="RUN-1")
    assert progress()["value"] == "unknown"                    # zero is also the default: it proves nothing
    write_json(w.run / "loops" / "planner" / "RUN-1.json", {"run_id": "RUN-1", "progressed": True,
                                                           "accepted": ["x"], "dependency_changed": False})
    assert progress()["value"] == "PROGRESS"
    write_json(w.run / "loops" / "planner" / "RUN-1.json", {"run_id": "RUN-1", "progressed": False})
    assert progress()["value"] == "unknown"
    w.loop(no_progress_count=2, last_run_id="RUN-1")
    p = progress()
    assert p["value"] == "NO_PROGRESS" and p["no_progress_count"] == 2
    w.loop(no_progress_count="2")
    assert progress()["value"] == "unknown"


# ───────────────────────────── signals: probe PASS ─────────────────────────────

def probe_world(w, mode):
    write(w.fleet / "kyloop.py", FAKE_KYLOOP)
    write(w.fleet / "kyqualify.py", FAKE_KYQUALIFY)
    write_json(w.fleet / "qualification.json", {"mode": mode, "receipt_path": str(w.run / "QUALIFICATION.json")})


def test_probe_pass_is_the_qualification_check(w):
    probe_world(w, "pass")
    p = w.report()["signals"]["probe_pass"]
    assert p["planner"]["value"] == "PASS" and p["conductor"]["value"] == "PASS"
    calls = [json.loads(x) for x in (w.fleet / "kyqualify_calls.jsonl").read_text().splitlines()]
    assert len(calls) == 2
    for call in calls:
        a = call["argv"]
        assert a[:2] == ["check", str(w.run / "QUALIFICATION.json")]
        assert a[a.index("--require-context") + 1] == "launchd" and "--verify-evidence" in a
    assert {c["config"]["role"] for c in calls} == {"planner", "conductor"}
    assert list((w.tmp / "tmp").iterdir()) == []                # the configuration handed over is removed again


@pytest.mark.parametrize("mode,want", [("refused", "REFUSED"), ("crash", "unknown")])
def test_probe_not_pass(w, mode, want):
    probe_world(w, mode)
    p = w.report()["signals"]["probe_pass"]["planner"]
    assert p["value"] == want and p["why"]


def test_probe_unknown_without_a_launch_configuration(w):
    assert w.report()["signals"]["probe_pass"]["planner"]["value"] == "unknown"


# ───────────────────────────── signals: surrogate decision, veto expired, owner notified ─────────────────────────────

def veto_world(w, decisions, rc=0):
    write(w.fleet / "kyveto.py", FAKE_KYVETO)
    write_json(w.fleet / "veto_status.json", {"rc": rc, "report": {"schema": "ky.veto_status/1",
                                                                  "decisions": decisions, "attention": rc == 3}})


def test_surrogate_decision_is_its_state_and_veto_expiry_is_the_handlers(w):
    veto_world(w, [
        {"id": "SD-1", "state": "EXECUTED", "notification_submitted": True, "made_effective_by_handler": True},
        {"id": "SD-2", "state": "PENDING_VETO", "notification_submitted": True, "made_effective_by_handler": False,
         "seconds_remaining": 600},
        {"id": "SD-3", "state": "PENDING_VETO", "notification_submitted": True, "made_effective_by_handler": False,
         "seconds_remaining": 0},
        {"id": "SD-4", "state": "VETOED", "notification_submitted": False, "made_effective_by_handler": False},
        {"id": "SD-5", "state": "EFFECTIVE", "notification_submitted": True, "made_effective_by_handler": False,
         "anomaly": "log_claims_effective_without_action_record"}], rc=3)
    write(w.run / "JOURNAL_COCKPIT.md",
          "- 2026-10-12T08:00:00Z [decision] SD-1: go [notify=submitted]\n"
          "- 2026-10-12T08:00:01Z [decision] SD-2: go [notify=failed]\n"
          "- 2026-10-12T08:00:02Z [decision] SD-3: SD-5: go [notify=submitted]\n"
          "a line saying SD-5: was sent [notify=submitted]\n")
    s = w.report()["signals"]
    assert s["surrogate_decision"]["value"] == {"SD-1": "EXECUTED", "SD-2": "PENDING_VETO", "SD-3": "PENDING_VETO",
                                               "SD-4": "VETOED", "SD-5": "unknown"}
    assert s["veto_expired"]["value"] == {"SD-1": "expired", "SD-2": "not_expired", "SD-3": "unknown",
                                         "SD-4": "not_expired", "SD-5": "unknown"}
    assert s["owner_notified"]["value"] == {"SD-1": "submitted", "SD-2": "not_submitted", "SD-3": "submitted",
                                           "SD-4": "not_submitted", "SD-5": "not_submitted"}
    assert s["owner_notified"]["read_by_owner"] == "unknown"


def test_surrogate_signals_unknown_when_the_handler_cannot_answer(w):
    veto_world(w, [], rc=66)
    s = w.report()["signals"]
    for key in ("surrogate_decision", "veto_expired", "owner_notified"):
        assert s[key]["value"] == "unknown" and s[key]["why"]


def test_the_real_veto_handler_with_no_decision_reads_as_an_empty_measured_set(w):
    s = w.report()["signals"]
    assert s["surrogate_decision"]["value"] == {} and s["surrogate_decision"]["denominator"]["count"] == 0


# ───────────────────────────── signals: WAVE_B_DONE and READY_TO_START ─────────────────────────────

def test_wave_b_done_is_the_bound_marker_never_its_existence(w):
    def done():
        return w.report()["signals"]["WAVE_B_DONE"]
    assert done()["value"] == "NOT_DERIVED"
    receipt = w.install_receipt("final")
    versions = write_json(w.run / "VERSIONS.json", {"components": {}})
    write_json(w.run / "WAVE_B_DONE", {"schema": "ky.wave_b_done/1", "final_receipt_sha256": sha(receipt.read_bytes()),
                                       "versions_sha256": sha(versions.read_bytes())})
    assert done()["value"] == "DONE"
    write_json(w.run / "VERSIONS.json", {"components": {"changed": 1}})
    assert done()["value"] == "UNVERIFIED"
    write_json(w.run / "VERSIONS.json", {"components": {}})
    assert done()["value"] == "DONE"
    w.install_receipt("bootstrap")                              # the receipt the marker bound is no longer there
    assert done()["value"] == "UNVERIFIED"
    write_json(w.run / "WAVE_B_DONE", {"final_receipt_sha256": kyaction.sha_file(w.run / "INSTALL_RECEIPT.json"),
                                       "versions_sha256": sha(versions.read_bytes())})
    assert done()["value"] == "UNVERIFIED"                      # bound, but to a receipt that is not final
    write(w.run / "WAVE_B_DONE", "")                            # a file's existence
    assert done()["value"] == "UNVERIFIED"


def gate(w, first, rc):
    write(w.fleet / "kygate.sh", '#!/bin/bash\necho "$*" >> "%s"\nprintf "%s\\nreason=x: y\\n"\nexit %d\n'
          % (w.tmp / "gate_calls.log", first, rc), 0o755)


def test_ready_to_start_is_the_gate_rerun(w):
    def ready():
        return w.report()["signals"]["READY_TO_START"]
    assert ready()["value"] == "unknown"                        # KV3-B-KYGATE is not installed
    gate(w, "READY_TO_START", 0)
    assert ready()["value"] == "READY_TO_START"
    assert set((w.tmp / "gate_calls.log").read_text().split("\n")) == {"--pre-resume", ""}
    gate(w, "WAIT", 75)
    r = ready()
    assert r["value"] == "WAIT" and r["reasons"] == ["x: y"]
    gate(w, "READY_TO_START", 75)                               # the line and the exit code disagree
    assert ready()["value"] == "unknown"
    gate(w, "OPEN", 0)                                          # not what --pre-resume says
    assert ready()["value"] == "unknown"
    gate(w, "WAIT", 1)
    assert ready()["value"] == "unknown"


# ───────────────────────────── signals: platform approval ─────────────────────────────

EXPECT = {"repository": "marsys/madhav", "run_id": 123, "run_attempt": 1, "environment": "production",
          "source_sha": HEAD_A, "required_approver": "owner"}
RUN = {"id": 123, "run_attempt": 1, "head_sha": HEAD_A, "status": "in_progress", "conclusion": None,
       "repository": {"full_name": "marsys/madhav"}}
APPROVAL = {"state": "approved", "user": {"login": "owner"}, "environments": [{"name": "production"}]}


def gh(w, run=RUN, attempt=RUN, approvals=(APPROVAL,)):
    base = "repos/marsys/madhav/actions/runs/123"
    fx = {}
    if run is not None:
        fx[base] = run
    if attempt is not None:
        fx[base + "/attempts/1"] = attempt
    if approvals is not None:
        fx[base + "/approvals"] = list(approvals)
    write_json(w.bin / "gh.json", fx)


def approval(w, expect=EXPECT, env=None):
    r = w.cli("approval", "--expect", write_json(w.tmp / "expect.json", expect), env=env)
    return r.returncode, (json.loads(r.stdout) if r.stdout else None)


def test_platform_approval_verified_by_bound_readback(w):
    gh(w)
    rc, out = approval(w)
    assert rc == 0 and out["value"] == "verified" and out["external_dependency"] == "satisfied"
    assert out["workflow_completion"]["value"] == "in_progress"         # approval is not completion
    assert out["operation_acceptance"]["value"] == "unknown"            # … and neither is acceptance
    calls = [json.loads(x) for x in (w.bin / "gh_calls.jsonl").read_text().splitlines()]
    assert all(c[0] == "api" and c[1].startswith("repos/marsys/madhav/actions/runs/123") for c in calls)
    gh(w, run=dict(RUN, status="completed", conclusion="success"),
       attempt=dict(RUN, status="completed", conclusion="success"))
    rc, out = approval(w)
    assert rc == 0 and out["workflow_completion"]["value"] == "success"


def test_an_owners_report_without_readback_is_approval_reported_unverified(w):
    reported = dict(EXPECT, owner_report="approved it at 08:10, Abhisek")
    rc, out = approval(w, reported)                                      # gh cannot answer at all
    assert rc == 1 and out["value"] == "approval_reported_unverified"
    assert out["external_dependency"] == "kept" and out["workflow_completion"]["value"] == "unknown"
    gh(w, approvals=[])                                                  # gh answers: no approval on record
    rc, out = approval(w, reported)
    assert rc == 1 and out["value"] == "approval_reported_unverified"
    rc, out = approval(w, reported, env={"KY_GH": str(w.tmp / "no-gh")})
    assert rc == 1 and out["value"] == "approval_reported_unverified"
    rc, out = approval(w)                                                # nothing reported, nothing read back
    assert rc == 1 and out["value"] == "not_verified"
    gh(w)
    rc, out = approval(w, reported)                                      # the report plus the readback
    assert rc == 0 and out["value"] == "verified"


@pytest.mark.parametrize("case", ["sha", "approver", "environment", "attempt_id", "repository", "newer_attempt",
                                  "rejected", "pending_state", "later_attempt", "no_approvals_endpoint", "garbage"])
def test_platform_approval_not_verified(w, case):
    run, attempt, approvals, expect = dict(RUN), dict(RUN), [dict(APPROVAL)], dict(EXPECT)
    if case == "sha":
        attempt["head_sha"] = "b" * 40
    elif case == "approver":
        approvals[0]["user"] = {"login": "someone-else"}
    elif case == "environment":
        approvals[0]["environments"] = [{"name": "staging"}]
    elif case == "attempt_id":
        attempt["id"] = 999
    elif case == "repository":
        attempt["repository"] = {"full_name": "fork/madhav"}
    elif case == "newer_attempt":
        run["run_attempt"] = 2
    elif case == "rejected":
        approvals.append(dict(APPROVAL, state="rejected"))
    elif case == "pending_state":
        approvals[0]["state"] = "pending"
    elif case == "later_attempt":             # the approvals readback is per run: it cannot be bound to attempt 2
        expect["run_attempt"] = 2
        run["run_attempt"] = attempt["run_attempt"] = 2
    elif case == "no_approvals_endpoint":
        approvals = None
    gh(w, run, attempt, approvals)
    if case == "later_attempt":
        fx = json.loads((w.bin / "gh.json").read_text())
        fx["repos/marsys/madhav/actions/runs/123/attempts/2"] = attempt
        write_json(w.bin / "gh.json", fx)
    if case == "garbage":
        write(w.bin / "gh", "#!/bin/sh\necho not-json\n", 0o755)
    rc, out = approval(w, expect)
    assert rc == 1 and out["value"] in ("not_verified", "unknown") and out["why"], out
    assert out["value"] == ("unknown" if case in ("no_approvals_endpoint", "garbage") else "not_verified")
    assert out["external_dependency"] == "kept"


@pytest.mark.parametrize("bad", [{"run_id": "123"}, {"source_sha": "abc"}, {"repository": "nope"},
                                 {"run_attempt": 0}, {"required_approver": ""}, {"environment": None},
                                 {"run_id": True}])
def test_approval_expectation_must_be_complete(w, bad):
    gh(w)
    r = w.cli("approval", "--expect", write_json(w.tmp / "expect.json", dict(EXPECT, **bad)))
    assert r.returncode == 64 and r.stdout == ""


def test_the_status_report_never_claims_an_approval(w):
    gh(w)
    p = w.report()["signals"]["platform_approval"]
    assert p["value"] == "unknown" and "approval --expect" in p["why"]
    assert not (w.bin / "gh_calls.jsonl").exists()              # the status report does not reach GitHub
