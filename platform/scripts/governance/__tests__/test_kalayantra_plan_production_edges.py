"""Production prerequisites remain earned when a campaign-completion edge moves.

Governance oracles: CLAUDE.md §N.8 and relaunch plan v2.7 §6 STEP require
the step's own live detector; operation acceptance remains independently bound.
Exercise the committed SQL and real tracker step/completion paths without any
production connection. The in-memory ledger only supplies query result fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path
import hashlib
import sqlite3
import subprocess
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
P06_PR = 3516
P06_BRANCH = "origin/kalayantra/w4-p06"
GCW2_STEP = "gcw2_1305_1306_1308_applied"
GCW2_FILES = {
    "1305_gochara_snapshot_owns_l1_copy.sql": "b7ad2ba40ae81b29a2672c41a9f44212c67347e382dabefa153227a93da19a31",
    "1306_gochara_expected_class_census.sql": "b55e244e0e76fe783ad10e25656ecace29ead19ef7625a0668098e6529b2c574",
    "1308_gochara_near_miss_storage.sql": "bc7a220970b91d2d60b1532368e106df673f63a56d573d88acd78857e665204b",
}


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


def production_spec(plan, step=STEP):
    consumer = item(plan, "KA-3a")
    assert "J-4d-pr3018" not in consumer["depends_on"], "full campaign closure is no longer the 1235 prerequisite"
    assert step in consumer["steps"], "retain an earned production prerequisite"
    spec = consumer["step_evidence"][step]["detector"]
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


def test_plan_structure_and_remaining_ka3a_edges_are_preserved():
    plan = model()
    assert check_model(plan) == []
    assert item(plan, "KA-3a")["depends_on"] == ["J-0m", "K0a-4", "KA-1w", "KA-2"]
    ids = {row["id"] for row in plan["items"]}
    # The P06 items stay in the model; only KA-3a's strict completion edge to them is replaced.
    assert {"J-4c-pr3141", "J-4c-pr3191", "J-4c-pr3193"} <= ids
    assert any("J-4c-pr3141" in row.get("depends_on", []) for row in plan["items"] if row["id"] != "KA-3a")


# --- SR-A6-EDGES + SR-A6-GCW2: P06 #3516 becomes CODE for KA-3a (merge step + 1305/1306/1308 readback) ---

def test_ka3a_p06_edges_become_merge_step_and_production_readback_step():
    consumer = item(model(), "KA-3a")
    assert not {"J-4c-pr3141", "J-4c-pr3191", "J-4c-pr3193"} & set(consumer["depends_on"])
    assert {"p06_code_merged", GCW2_STEP} <= set(consumer["steps"])
    merged = consumer["step_evidence"]["p06_code_merged"]["detector"]
    assert (merged["type"], merged["pr"]) == ("pr_merged", P06_PR)


def gcw2_ledger(rows_present, monkeypatch, tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute("ATTACH DATABASE ':memory:' AS public")
    conn.execute("CREATE TABLE public._migrations_applied (filename TEXT, applied_at TEXT, sha256 TEXT)")
    for filename, digest in rows_present:
        conn.execute("INSERT INTO public._migrations_applied VALUES (?, '2026-10-16 16:00:00Z', ?)", (filename, digest))
    det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))
    # psql -tA hands the detector text cells, so the fixture does the same.
    monkeypatch.setattr(det, "_psql", lambda sql: [[str(cell) for cell in row] for row in conn.execute(sql).fetchall()])
    return det


FILES = list(GCW2_FILES.items())
WRONG = "0" * 64


@pytest.mark.parametrize("label,present,expected", [
    ("empty ledger", [], "pending"),
    ("only 1305", FILES[:1], "pending"),
    ("1305+1306, 1308 missing", FILES[:2], "pending"),
    ("1305+1308, 1306 missing", [FILES[0], FILES[2]], "pending"),
    ("three files, 1308 hash wrong", FILES[:2] + [(FILES[2][0], WRONG)], "pending"),
    ("1305 applied twice, others missing", [FILES[0], FILES[0]], "pending"),
    ("1383 etc. applied, none of the three", [("1383_ka_3a_vedha_candidate_intervals.sql", GCW2_FILES[FILES[0][0]])], "pending"),
    ("all three exact", FILES, "done"),
    ("all three plus unrelated rows", FILES + [("1383_ka_3a_vedha_candidate_intervals.sql", WRONG)], "done"),
])
def test_gcw2_readback_is_true_only_when_all_three_are_applied_with_file_hashes(label, present, expected, monkeypatch, tmp_path):
    spec = production_spec(model(), GCW2_STEP)
    assert spec["type"] == "db_query" and spec["expect"] == "nonempty"
    assert gcw2_ledger(present, monkeypatch, tmp_path).verify(spec).status == expected, label


def test_gcw2_readback_is_unmeasured_without_database(tmp_path):
    spec = production_spec(model(), GCW2_STEP)
    det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))
    assert det.verify(spec).status == "error"


def _p06_file_bytes(name):
    """The 1305/1306/1308 file as #3516 ships it: the merged repo copy, else the open branch."""
    merged = ROOT / "platform/migrations" / name
    if merged.is_file():
        return merged.read_bytes()
    done = subprocess.run(["git", "show", f"{P06_BRANCH}:platform/migrations/{name}"], cwd=ROOT,
                          capture_output=True, env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})
    if done.returncode != 0:
        pytest.skip(f"{name} is neither in the working tree nor on {P06_BRANCH}")
    return done.stdout


@pytest.mark.parametrize("name", sorted(GCW2_FILES))
def test_gcw2_sql_hashes_are_the_file_sha256s_of_the_p06_migrations(name):
    spec = production_spec(model(), GCW2_STEP)
    digest = hashlib.sha256(_p06_file_bytes(name)).hexdigest()
    assert GCW2_FILES[name] == digest, "plan hash must be the migration file's sha256 (SR-A6-GCW2 readback)"
    assert f"filename = '{name}' AND sha256 = '{digest}'" in spec["sql"]


@pytest.mark.parametrize("observation,expected", [("pending", 2), ("error", 2), ("done", 0)])
def test_gcw2_step_needs_live_production_measurement(observation, expected, tmp_path, monkeypatch):
    plan = model()
    spec = production_spec(plan, GCW2_STEP)
    events = tmp_path / "EVENTS.jsonl"
    evidence = tmp_path / "gcw2-readback.json"
    evidence.write_text('{"fixture":"readback evidence"}\n')
    monkeypatch.setattr(cli, "load_model", lambda: plan)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    monkeypatch.setattr(cli, "get", lambda *a, **kw: (
        {"item": "KA-3a", "step": GCW2_STEP, "spec": spec, "detector": {"status": observation}}, "live"))
    assert cli.main(["step", "KA-3a", GCW2_STEP, "--stream", "K", "--evidence", str(evidence)]) == expected
    assert events.exists() == (expected == 0)


@pytest.mark.parametrize("open_step", ["p06_code_merged", GCW2_STEP])
def test_ka3a_cannot_complete_while_a_p06_step_is_open(open_step):
    plan = model()
    # A7 D-46 drops step receipts for a code item (the PR acceptance covers them); the step gate still binds
    # every other kind, so the open-step refusal is measured on the operation kind.
    item(plan, "KA-3a")["completion_kind"] = "operation"
    events = accepted_inputs(plan, {"KA-3a"})
    assert rows(plan, events)["KA-3a"]["deps_open_strict"] == []
    for step in item(plan, "KA-3a")["steps"]:
        if step != open_step:
            events.append(dict(kind="item", item="KA-3a", actor="stream-K", state="done", step=step,
                               evidence="synthetic accepted step", ts="2026-10-16T16:01:00Z"))
    with pytest.raises(CompletionError, match="steps remain open: " + open_step):
        guarded_done_event(plan, events, "KA-3a", "stream-K", {"status": "done"}, {})
