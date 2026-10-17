"""Production prerequisites remain earned when a campaign-completion edge moves.

Governance oracles: CLAUDE.md §N.8 and relaunch plan v2.7 §6 STEP require
the step's own live detector; operation acceptance remains independently bound.
Exercise the committed SQL and real tracker step/completion paths without any
production connection. The in-memory ledger only supplies query result fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform/scripts/governance"))
from pravaha_tracker import cli  # noqa: E402
from pravaha_tracker.completion import CompletionError, guarded_done_event  # noqa: E402
from pravaha_tracker.detectors import Config, Detectors  # noqa: E402
from pravaha_tracker.server import check_model  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402

MIGRATION = "1235_ka_gochara_staged_candidate_evidence_function.sql"
SHA256 = "930902f6af470d3a6cdfd1b707ea23e6e365ad8c464004b9ed2a924194353682"
STEP = "gcw_1235_production_applied"


def model():
    return json.loads((ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text())


def item(plan, iid):
    return next(row for row in plan["items"] if row["id"] == iid)


def accepted_inputs(plan, pending):
    """Already-guarded synthetic inputs; never write to the campaign event log."""
    events = []
    for row in plan["items"]:
        iid = row["id"]
        if iid in pending:
            continue
        if row.get("done_by") == "decision":
            events.append(dict(kind="decision", decision=iid, actor="steward",
                               state="decided", outcome="approved", ts="2026-10-16T15:00:00Z"))
        else:
            events.append(dict(kind="item", item=iid, actor="steward", state="done",
                               guarded=True, evidence="synthetic accepted input", ts="2026-10-16T15:00:00Z"))
    return events


def rows(plan, events):
    view = build_snapshot(plan, events, {}, {}, {})
    return {row["id"]: row for track in view["tracks"] for row in track["items"]}


def code_acceptance(iid, *, post_deploy):
    """(review + verdict events, proof) of a merged, deployed, independently accepted code item (A7 D-46)."""
    head, merge = "a" * 40, "b" * 40
    verdict = dict(kind="verdict", actor="stream-V", item=iid, result="ACCEPTED")
    events = [dict(kind="item", item=iid, actor="stream-K", state="review", detail=f"PR #9999 @ {head}",
                   ts="2026-10-16T15:01:30Z"),
              dict(verdict, head=head, phase="pre_merge", ts="2026-10-16T15:02:00Z")]
    if post_deploy:
        events.append(dict(verdict, head=merge, phase="post_deploy", ts="2026-10-16T15:03:00Z"))
    proof = dict(type="code", reviewed_head=head,
                 pr=dict(number=9999, state="MERGED", headRefOid=head, mergeCommit={"oid": merge}),
                 deploy=dict(deployed_sha="c" * 40, run_id=1, contains_merge=True))
    return events, proof


def production_spec(plan):
    consumer = item(plan, "KA-3a")
    assert "J-4d-pr3018" not in consumer["depends_on"], "full campaign closure is no longer the 1235 prerequisite"
    assert STEP in consumer["steps"], "retain an earned production prerequisite"
    spec = consumer["step_evidence"][STEP]["detector"]
    assert spec["type"] == "db_query", "file presence cannot measure production migration application"
    assert spec["expect"] == "nonempty"
    return spec


@pytest.mark.parametrize("filename,digest,expected", [
    (None, None, "pending"),
    (MIGRATION, "0" * 64, "pending"),
    ("1383_ka_3a_vedha_candidate_intervals.sql", SHA256, "pending"),
    (MIGRATION, SHA256, "done"),
])
def test_ka3a_production_precondition_measures_exact_ledger_row(filename, digest, expected, monkeypatch, tmp_path):
    spec = production_spec(model())
    with sqlite3.connect(":memory:") as conn:
        conn.execute("ATTACH DATABASE ':memory:' AS public")
        conn.execute("CREATE TABLE public._migrations_applied (filename TEXT, applied_at TEXT, sha256 TEXT)")
        if filename:
            conn.execute("INSERT INTO public._migrations_applied VALUES (?, '2026-10-16 14:25:18Z', ?)",
                         (filename, digest))
        det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))
        monkeypatch.setattr(det, "_psql", lambda sql: conn.execute(sql).fetchall())
        assert det.verify(spec).status == expected


def test_ka3a_production_precondition_is_unmeasured_without_database(tmp_path):
    spec = production_spec(model())
    det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))
    assert det.verify(spec).status == "error"


@pytest.mark.parametrize("observation,expected", [("pending", 2), ("error", 2), ("done", 0)])
def test_ka3a_step_needs_live_production_measurement(observation, expected, tmp_path, monkeypatch):
    plan = model()
    spec = production_spec(plan)
    events = tmp_path / "EVENTS.jsonl"
    evidence = tmp_path / "migration-readback.json"
    evidence.write_text('{"fixture":"readback evidence"}\n')
    monkeypatch.setattr(cli, "load_model", lambda: plan)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    monkeypatch.setattr(cli, "get", lambda *a, **kw: (
        {"item": "KA-3a", "step": STEP, "spec": spec, "detector": {"status": observation}}, "live"))
    assert cli.main(["step", "KA-3a", STEP, "--stream", "K", "--evidence", str(evidence)]) == expected
    assert events.exists() == (expected == 0)


def test_operation_item_cannot_replace_bound_receipt_with_live_query(tmp_path, monkeypatch, capsys):
    plan = model()
    spec = production_spec(plan)
    item(plan, "KA-3a")["completion_kind"] = "operation"
    events = tmp_path / "EVENTS.jsonl"
    evidence = tmp_path / "unbound.json"
    evidence.write_text('{}\n')
    monkeypatch.setattr(cli, "load_model", lambda: plan)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    monkeypatch.setattr(cli, "get", lambda *a, **kw: (
        {"item": "KA-3a", "step": STEP, "spec": spec, "detector": {"status": "done"}}, "live"))
    assert cli.main(["step", "KA-3a", STEP, "--stream", "K", "--evidence", str(evidence)]) == 2
    assert "canonical file_contains acceptance receipt" in capsys.readouterr().err
    assert not events.exists()


def test_ka3a_d46_implements_without_step_receipts_but_keeps_post_deploy_verdict():
    """A7 D-46: a code item drops separate step receipts (the PR acceptance covers them) and its open upstream
    becomes `activation_pending` (KA-3a's only production wait was that step, so none is left); the production protection that remains is the independent post-deploy verdict
    (amendment §5: KA-3a declares a migration), which no step receipt or deploy replaces."""
    plan = model()
    production_spec(plan)
    events = accepted_inputs(plan, {"KA-3a", "J-4d-pr3018"})
    assert rows(plan, events)["KA-3a"]["deps_open_strict"] == []
    accepted, proof = code_acceptance("KA-3a", post_deploy=True)
    done = guarded_done_event(plan, events + accepted, "KA-3a", "stream-K", {"status": "done"}, proof)
    assert STEP in item(plan, "KA-3a")["steps"] and not any(ev.get("step") for ev in events)
    assert done["activation_pending"] == []
    missing, proof = code_acceptance("KA-3a", post_deploy=False)
    with pytest.raises(CompletionError, match="independent post-deploy verdict at merge commit is missing"):
        guarded_done_event(plan, events + missing, "KA-3a", "stream-K", {"status": "done"}, proof)


def test_k32_d46_implements_with_sealed_production_output_pending_but_operation_kind_still_waits():
    """K3-2 keeps depends_on J-5s. D-46: as a code item it closes implemented with J-5s `activation_pending`;
    SR-A4-01 strict ordered completion still binds every non-code/artifact kind, which refuses while J-5s is open."""
    plan = model()
    consumer = item(plan, "K3-2")
    assert consumer["depends_on"] == ["J-5s", "K3-1"]
    assert consumer["steps"] == ["certification_mapping"]
    events = accepted_inputs(plan, {"K3-2", "J-5s"})
    assert rows(plan, events)["K3-2"]["deps_open_strict"] == ["J-5s"]
    accepted, proof = code_acceptance("K3-2", post_deploy=False)
    done = guarded_done_event(plan, events + accepted, "K3-2", "stream-K", {"status": "done"}, proof)
    assert done["activation_pending"] == ["J-5s"]
    consumer["completion_kind"] = "operation"
    with pytest.raises(CompletionError, match="dependencies remain open: J-5s"):
        guarded_done_event(plan, events, "K3-2", "stream-K", {"status": "done"}, {})


def test_plan_structure_and_unrelated_p06_edges_are_preserved():
    plan = model()
    assert check_model(plan) == []
    assert item(plan, "KA-3a")["depends_on"] == [
        "J-0m", "K0a-4", "KA-1w", "KA-2", "J-4c-pr3141", "J-4c-pr3191", "J-4c-pr3193"]
