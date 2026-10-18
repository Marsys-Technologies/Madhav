"""A7 D-46: a code/artifact item is IMPLEMENTED once merged + accepted + deployed; open gates only defer ACTIVATION.

One oracle per distinct claim (owner decision D-OWNER-TESTS-20261016). The source for every claim is the owner direction
D-46 (/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl): code/artifact items close with `activation_pending=<gate>`,
operation/decision/verdict items keep strict ordered completion (SR-A4-01), the headline is implemented/total with
activated/total beside it, and close needs both.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import subprocess

import pytest

from pravaha_tracker import d46_sweep
from pravaha_tracker.audit import audit
from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.state import build_snapshot

NOW = dt.datetime(2026, 10, 17, tzinfo=dt.timezone.utc)
HEAD, MERGE, DEPLOYED = "a" * 40, "b" * 40, "c" * 40


def model_with(*items, declared=False):
    cp = {"guarded_completion": True, "verdict_stream": "V"}
    if declared:
        cp["declarations"] = {"reviewer_rule": {"v_exact_head_then_deploy_containment": "x"}}
    return {"campaign": "fixture", "control_plane": cp, "streams": [], "decisions": [],
            "tracks": [{"id": "K", "title": "K"}],
            "items": [{"track": "K", "owner": "K", "title": i["id"], "depends_on": [],
                       "detector": {"type": "branch_merged", "ref": "origin/x"}, **i} for i in items]}


def code_events():
    ts = NOW.isoformat()
    return [{"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "review",
             "detail": f"PR #7 @ {HEAD}", "ts": ts},
            {"kind": "verdict", "actor": "stream-V:v1", "item": "K-C", "head": HEAD, "phase": "pre_merge",
             "result": "ACCEPTED", "detail": "diff and item tests", "ts": ts}]


def code_proof(deploy=True):
    proof = {"type": "code", "reviewed_head": HEAD,
             "pr": {"number": 7, "headRefOid": HEAD, "mergeCommit": {"oid": MERGE}, "state": "MERGED"}}
    if deploy:
        proof["deploy"] = {"deployed_sha": DEPLOYED, "run_id": 4242, "contains_merge": True}
    return proof


def complete(model, events, item, proof, actor="stream-K:k1"):
    return guarded_done_event(model, events, item, actor, {"status": "done"}, proof)


def rows_of(model, events):
    snap = build_snapshot(model, events, {}, {}, {}, now=NOW)
    return snap, {r["id"]: r for t in snap["tracks"] for r in t["items"]}


# ---- claim 1: a code item with an open dependency is implemented, with the gate and evidence recorded ---------------

def test_code_item_with_open_dependency_completes_and_records_activation_pending():
    model = model_with({"id": "K-C", "depends_on": ["K-GATE"], "steps": []}, {"id": "K-GATE"})
    event = complete(model, code_events(), "K-C", code_proof())
    assert event["guarded"] is True and event["state"] == "done"
    assert event["activation_pending"] == ["K-GATE"]
    assert event["merged_pr"] == 7 and event["deploy_run_id"] == 4242
    assert event["acceptance_ref"]["head"] == HEAD and event["acceptance_ref"]["actor"] == "stream-V:v1"


# ---- claim 2: code items drop the separate step receipts; artifact items keep their steps -----------------------------

def test_code_item_needs_no_step_receipt_but_artifact_item_still_does():
    model = model_with({"id": "K-C", "steps": ["tests"]}, {"id": "K-A", "steps": ["written"]})
    assert complete(model, code_events(), "K-C", code_proof())["state"] == "done"
    with pytest.raises(CompletionError, match="steps remain open: written"):
        complete(model, [], "K-A", {"type": "artifact", "artifact_digest": "d" * 64})


# ---- claim 3: SR-A4-01 stays for every other kind -------------------------------------------------------------------

def test_operation_item_keeps_strict_ordered_completion():
    model = model_with({"id": "K-OP", "depends_on": ["K-GATE"], "completion_kind": "operation"}, {"id": "K-GATE"},
                       declared=True)
    with pytest.raises(CompletionError, match="dependencies remain open: K-GATE"):
        complete(model, [], "K-OP", {"type": "operation"})


# ---- claim 4: only the dependency rule is relaxed — merge, acceptance and deploy are still required -----------------

def test_open_dependency_does_not_excuse_missing_deploy_or_acceptance():
    model = model_with({"id": "K-C", "depends_on": ["K-GATE"]}, {"id": "K-GATE"})
    with pytest.raises(CompletionError, match="deployment"):
        complete(model, code_events(), "K-C", code_proof(deploy=False))
    with pytest.raises(CompletionError, match="verdict"):
        complete(model, code_events()[:1], "K-C", code_proof())


# ---- claim 5: a gate must be a plan item; an id the plan does not know is not a deferrable gate ---------------------

def test_unknown_dependency_is_not_deferred():
    model = model_with({"id": "K-C", "depends_on": ["NOT-IN-PLAN"]})
    with pytest.raises(CompletionError, match="unknown to the plan: NOT-IN-PLAN"):
        complete(model, code_events(), "K-C", code_proof())


# ---- claim 6: headline implemented/total + activated/total; close needs both ----------------------------------------

def test_headline_counts_implemented_and_activated_and_close_needs_both():
    model = model_with({"id": "K-C", "depends_on": ["K-GATE"]}, {"id": "K-GATE"})
    done_c = {**complete(model, code_events(), "K-C", code_proof()), "ts": NOW.isoformat()}
    snap, rows = rows_of(model, [*code_events(), done_c])
    assert rows["K-C"]["status"] == "done" and rows["K-C"]["activation_pending"] == ["K-GATE"]
    o = snap["overall"]
    assert (o["implemented"], o["activated"], o["activation_pending"], o["total"]) == (1, 0, 1, 2)
    assert o["close_ready"] is False
    gate = {"kind": "item", "actor": "stream-K:k1", "item": "K-GATE", "state": "done", "guarded": True,
            "evidence": "gate closed", "ts": NOW.isoformat()}
    snap, rows = rows_of(model, [*code_events(), done_c, gate])
    o = snap["overall"]
    assert rows["K-C"]["activation_pending"] == []
    assert (o["implemented"], o["activated"], o["activation_pending"]) == (2, 2, 0)
    assert o["close_ready"] is True


# ---- claim 7: the audit accepts a recorded deferral and still flags an unrecorded or non-D-46 one -------------------

def _audit_codes(model, events):
    return [f["code"] for f in audit(model, events, "/nonexistent-run-root", since=NOW - dt.timedelta(hours=1), now=NOW)]


def test_audit_requires_the_deferred_gate_to_be_recorded():
    model = model_with({"id": "K-C", "depends_on": ["K-GATE"]}, {"id": "K-GATE"})
    done = {**complete(model, code_events(), "K-C", code_proof()), "ts": NOW.isoformat()}
    log = [*code_events(), done]
    assert "unmet_dependency" not in _audit_codes(model, log)
    assert "activation_pending_unrecorded" not in _audit_codes(model, log)
    assert "activation_pending_unrecorded" in _audit_codes(model, [*code_events(), {**done, "activation_pending": []}])
    op = model_with({"id": "K-OP", "depends_on": ["K-GATE"], "completion_kind": "operation"}, {"id": "K-GATE"},
                    declared=True)
    op_done = {"kind": "item", "actor": "stream-K:k1", "item": "K-OP", "state": "done", "guarded": True,
               "evidence": "x", "completion": {"type": "operation"}, "ts": NOW.isoformat()}
    assert "unmet_dependency" in _audit_codes(op, [op_done])


# ---- claim 8: the sweep decides from git and the evidence file, lists what is missing, writes nothing in dry-run -----

def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True, env=env).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "commit", "-q", "--allow-empty", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    git(root, "commit", "-q", "--allow-empty", "-m", "feature (#7)")
    merge = git(root, "rev-parse", "HEAD")
    git(root, "commit", "-q", "--allow-empty", "-m", "later")
    return {"path": root, "base": base, "merge": merge, "tip": git(root, "rev-parse", "HEAD")}


def evidence_for(repo, *, deploy_head=None, accepted=True):
    ev = {"schema": d46_sweep.SCHEMA, "observed_at": NOW.isoformat(), "main_sha": repo["tip"],
          "prs": [{"number": 7, "state": "MERGED", "headRefOid": HEAD, "mergeCommit": {"oid": repo["merge"]},
                   "item": "K-C"}],
          "acceptances": [{"item": "K-C", "criterion": "v2", "result": "ACCEPTED", "actor": "stream-V:v1",
                           "ts": NOW.isoformat(), "ref": "review-job-1", "pr": 7, "head": HEAD}] if accepted else [],
          "deploys": [{"run_id": 99, "head_sha": deploy_head or repo["tip"], "conclusion": "success",
                       "event": "workflow_run", "branch": "main", "created_at": NOW.isoformat()}],
          "detectors": {"K-C": {"status": "done", "detail": "merged"}}}
    return ev


def sweep_model():
    return model_with({"id": "K-C", "depends_on": ["K-GATE"], "completion_kind": "code",
                       "reviewer_rule": "v_exact_head_then_deploy_containment"}, {"id": "K-GATE"}, declared=True)


def report(reports, item):
    return next(r for r in reports if r["item"] == item)


def test_sweep_lists_closable_items_with_evidence_and_holds_the_rest(repo):
    r = report(d46_sweep.classify(sweep_model(), [], evidence_for(repo), str(repo["path"])), "K-C")
    assert r["status"] == "would_close" and r["activation_pending"] == ["K-GATE"]
    assert r["evidence"]["merged_pr"] == 7 and r["evidence"]["deploy_run_id"] == 99
    assert r["evidence"]["merge_commit"] == repo["merge"] and r["evidence"]["acceptance_ref"]["ref"] == "review-job-1"
    # the only deploy predates the merge: git, not the file, says it does not contain it
    r = report(d46_sweep.classify(sweep_model(), [], evidence_for(repo, deploy_head=repo["base"]),
                                  str(repo["path"])), "K-C")
    assert r["status"] == "not_closable"
    assert r["missing"] == ["no successful main deploy contains the merge commit"]
    r = report(d46_sweep.classify(sweep_model(), [], evidence_for(repo, accepted=False), str(repo["path"])), "K-C")
    assert r["status"] == "not_closable" and "acceptance" in r["missing"][0]


def test_sweep_closes_a_data_writing_item_without_a_post_deploy_acceptance_apply_included(repo, tmp_path):
    """A8 §4 / SR-POSTDEPLOY-RETIRED: the sweep asks a migration item for the same evidence as any code item."""
    model = sweep_model()
    model["items"][0]["brief"] = {"migration": "1401_x.sql"}
    r = report(d46_sweep.classify(model, [], evidence_for(repo), str(repo["path"])), "K-C")
    assert r["status"] == "would_close" and r["missing"] == []
    events_path = tmp_path / "EVENTS.jsonl"
    events_path.write_text("")
    results = d46_sweep.apply(model, evidence_for(repo), str(repo["path"]), str(events_path),
                              lambda iid: {"status": "done", "detail": "merged"})
    assert results[0]["closed"] is True


def test_sweep_dry_run_writes_nothing_and_apply_closes_through_the_guard(repo, tmp_path, capsys):
    model_path, events_path, evidence_path = tmp_path / "model.json", tmp_path / "EVENTS.jsonl", tmp_path / "ev.json"
    model_path.write_text(json.dumps(sweep_model()))
    events_path.write_text("")
    evidence_path.write_text(json.dumps(evidence_for(repo)))
    args = ["--model", str(model_path), "--events", str(events_path), "--evidence", str(evidence_path),
            "--repo", str(repo["path"])]
    assert d46_sweep.main(args) == 0
    assert "CLOSE  K-C [code] pr=7 deploy_run=99 activation_pending=['K-GATE']" in capsys.readouterr().out
    assert events_path.read_text() == ""
    assert d46_sweep.main([*args, "--apply"]) == 0
    log = [json.loads(line) for line in events_path.read_text().splitlines()]
    closed = [e for e in log if e.get("state") == "done"]
    assert len(closed) == 1 and closed[0]["item"] == "K-C" and closed[0]["activation_pending"] == ["K-GATE"]
    assert closed[0]["merged_pr"] == 7 and closed[0]["deploy_run_id"] == 99
    assert _audit_codes(sweep_model(), log) == []
    assert d46_sweep.main([*args, "--apply"]) == 0   # idempotent: already_done is not swept again
    assert len([e for e in events_path.read_text().splitlines() if '"state":"done"' in e]) == 1


# ---- claim 9: the dashboard shows implemented/total and activated/total -------------------------------------------

def test_dashboard_renders_implemented_and_activated_chips():
    from test_built_waiting_on_gate import CLIENT_PROBE
    model = model_with({"id": "K-C", "depends_on": ["K-GATE"]}, {"id": "K-GATE"})
    done_c = {**complete(model, code_events(), "K-C", code_proof()), "ts": NOW.isoformat()}
    snap, rows = rows_of(model, [*code_events(), done_c])
    app = Path(__file__).resolve().parents[1] / "static" / "app.js"
    out = subprocess.run(["node", "-e", CLIENT_PROBE, str(app)], input=json.dumps([snap]), text=True,
                         capture_output=True, check=True)
    shown = json.loads(out.stdout)[0]
    assert "Render error" not in shown["foot"]
    assert "<b>1/2</b>implemented" in shown["counts"] and "<b>0/2</b>activated" in shown["counts"]
    assert "implemented, activation pending: K-GATE" in shown["plan"]


# ---- review round 1 (PR #3691): B1-B4, one oracle each ------------------------------------------------------------
# Source: owner direction D-46 — merged + accepted + contained in a successful main deploy for EVERY code item; strict
# kinds keep SR-A4-01 behind an upstream that is implemented but not activated; activated means the gates are closed.

_RULES = {"v_exact_head_then_deploy_containment": "x", "v_exact_head_then_post_deploy_at_merge_commit": "x",
          "v_pre_acceptance_then_receipt_readback_digest": "x"}
_CODE = {"completion_kind": "code", "reviewer_rule": "v_exact_head_then_deploy_containment"}


def _declared(*items):
    m = model_with(*items)
    m["control_plane"]["declarations"] = {"reviewer_rule": _RULES}
    return m


def _stamped(event):
    return {**event, "ts": NOW.isoformat()}


def _code_log(model, item, head=HEAD):
    ts = NOW.isoformat()
    return [{"kind": "item", "actor": "stream-K:k1", "item": item, "state": "review", "detail": f"PR #7 @ {head}",
             "ts": ts},
            {"kind": "verdict", "actor": "stream-V:v1", "item": item, "head": head, "phase": "pre_merge",
             "result": "ACCEPTED", "detail": "ok", "ts": ts}]


def _proof(head=HEAD):
    return {**code_proof(), "reviewed_head": head, "pr": {**code_proof()["pr"], "headRefOid": head}}


def test_B1_data_writing_code_item_needs_a_measured_deploy_containment():
    model = _declared({"id": "K-M", "completion_kind": "code", "depends_on": ["K-GATE"],
                       "reviewer_rule": "v_exact_head_then_post_deploy_at_merge_commit",
                       "brief": {"migration": "123_x.sql"}}, {"id": "K-GATE"})
    log = _code_log(model, "K-M") + [{"kind": "verdict", "actor": "stream-V:v1", "item": "K-M", "head": MERGE,
                                      "phase": "post_deploy", "result": "ACCEPTED", "detail": "ok",
                                      "ts": NOW.isoformat()}]
    with pytest.raises(CompletionError, match="no successful deployment"):
        complete(model, log, "K-M", code_proof(deploy=False))
    event = complete(model, log, "K-M", code_proof())
    assert event["deploy_run_id"] == 4242 and event["activation_pending"] == ["K-GATE"]


def _chain(*kinds):
    """K-GATE (open) <- K-C (code, implemented, gate pending) <- one dependant per kind in `kinds`."""
    first = {"id": "K-C", "depends_on": ["K-GATE"], **_CODE}
    rest = [{"id": f"K-{i}", "depends_on": ["K-C"], **extra} for i, extra in enumerate(kinds)]
    model = _declared({"id": "K-GATE"}, first, *rest)
    log = _code_log(model, "K-C")
    log.append(_stamped(complete(model, log, "K-C", code_proof())))
    return model, log


def test_B2_strict_dependant_waits_for_an_implemented_but_not_activated_upstream():
    digest = "d" * 64
    model, log = _chain({"completion_kind": "operation", "reviewer_rule": "v_pre_acceptance_then_receipt_readback_digest"})
    log.append({"kind": "verdict", "actor": "stream-V:v1", "item": "K-0", "artifact_digest": digest,
                "phase": "artifact", "result": "ACCEPTED", "detail": "ok", "ts": NOW.isoformat()})
    proof = {"type": "operation", "artifact_digest": digest, "operation_id": "op1",
             "receipt": {"operation_id": "op1", "item_id": "K-0", "status": "COMPLETED"}}
    with pytest.raises(CompletionError, match="dependencies remain open: K-C"):
        complete(model, log, "K-0", proof)
    # a code dependant of the same upstream is still allowed to close (D-46 relaxation is for code/artifact only)
    model, log = _chain(_CODE)
    h2 = "e" * 40
    log += _code_log(model, "K-0", h2)
    assert complete(model, log, "K-0", _proof(h2))["activation_pending"] == ["K-GATE"]


def test_B3_activation_is_transitive_so_the_activated_count_does_not_overstate():
    model, log = _chain(_CODE)
    h2 = "e" * 40
    log += _code_log(model, "K-0", h2)
    event = complete(model, log, "K-0", _proof(h2))
    assert event["activation_pending"] == ["K-GATE"]          # the upstream's open gate, not just its own deps
    log.append(_stamped(event))
    snap, rows = rows_of(model, log)
    assert snap["overall"]["implemented"] == 2 and snap["overall"]["activated"] == 0, snap["overall"]
    assert rows["K-0"]["activation_pending"] == ["K-GATE"] and rows["K-C"]["activation_pending"] == ["K-GATE"]
    assert snap["overall"]["close_ready"] is False


def test_B4_a_refused_apply_leaves_the_event_log_untouched(repo, tmp_path):
    ev = evidence_for(repo)
    ev["detectors"] = {}                                       # measured live by --apply: the detector is down
    events_path = tmp_path / "EVENTS.jsonl"
    events_path.write_text("")
    results = d46_sweep.apply(sweep_model(), ev, str(repo["path"]), str(events_path),
                              lambda iid: {"status": "unknown", "detail": "down"})
    assert results and results[0]["closed"] is False
    assert events_path.read_text() == ""


def _tracker(known: dict):
    """A stand-in tracker answering GET /api/verify?id=<item> from `known`, 404 for any item it does not know."""
    import http.server
    import threading
    from urllib.parse import parse_qs, urlparse

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):    # noqa: N802
            iid = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
            body, code = (json.dumps({"item": iid, "detector": known[iid]}), 200) if iid in known else ("not found", 404)
            self.send_response(code)
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_B5_apply_measures_the_detector_on_the_tracker_it_is_pointed_at_and_names_it_when_it_cannot(
        repo, tmp_path, monkeypatch, capsys):
    """2026-10-17: run with the module default (the Pravāha tracker, which does not know KĀLA-YANTRA items) every
    candidate was refused with a bare "declared detector has not passed". `--url` selects the tracker; a tracker that
    cannot answer is named in the refusal."""
    from pravaha_tracker import cli
    other, other_url = _tracker({})
    live, live_url = _tracker({"K-C": {"status": "done", "detail": "merged", "source": "detector:branch_merged"}})
    monkeypatch.setattr(cli, "URL", other_url)    # what an unconfigured `python -m pravaha_tracker.d46_sweep` gets
    ev = evidence_for(repo)
    ev["detectors"] = {}
    model_path, events_path, evidence_path = tmp_path / "model.json", tmp_path / "EVENTS.jsonl", tmp_path / "ev.json"
    model_path.write_text(json.dumps(sweep_model()))
    events_path.write_text("")
    evidence_path.write_text(json.dumps(ev))
    args = ["--model", str(model_path), "--events", str(events_path), "--evidence", str(evidence_path),
            "--repo", str(repo["path"]), "--apply"]
    try:
        assert d46_sweep.main(args) == 3
        refusal = capsys.readouterr().out
        assert "REFUSED K-C" in refusal and f"at {other_url}" in refusal and "'unknown'" in refusal
        assert events_path.read_text() == ""
        assert d46_sweep.main([*args, "--url", live_url]) == 0
        assert [json.loads(x)["item"] for x in events_path.read_text().splitlines() if '"state":"done"' in x] == ["K-C"]
    finally:
        other.shutdown()
        live.shutdown()
