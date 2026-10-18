"""KV3-B-EXECUTOR-TABLE (relaunch plan v2.7 §2, §5, §6 EXECUTE, §14 B-1): the executor table and the executor's git handle.

What this proves, and what it deliberately does not touch:
  · the table: every `enabled_by` is a plan-model item; four bootstrap and six J-1a kinds are enabled; every field equals the table at the
    plan pin except the enumerated K9-23 / Wave 4 / #3607 measuring preparation edits and `_doc`; P10 entries are present, with only J-1a enabled; `enabled` is the first
    key of each entry; the five model completion detectors retain main's reviewed definitions rather than treating table enablement as acceptance;
  · the authority boundary: executor.py differs from the plan-pin revision in `GIT` and exact approved receipt/capability and evidence-bound safety additions only, and the listed
    functions and constants are byte-identical;
  · the negative cases run through the real `validate` on a temporary KY_ROOT, with KY_SOURCE_REPO a temporary repository
    whose origin is a local path — never the campaign checkout, never the network, never the running executor.

An entry whose state the test cannot read is a failure, not a pass."""
import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import datetime as dt
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
OPS_FILE = FLEET / "executor_ops.json"
EXECUTOR_PY = FLEET / "executor.py"
EXECUTOR_SH = FLEET / "executor.sh"
MODEL = REPO / "00_ARCHITECTURE" / "control" / "kalayantra" / "plan_model.json"
OPS_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
PY_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py"
SH_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor.sh"
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"

PLAN_PIN = "e709f60d7fcd4559227a25a4d5d83d6431c396b6"
MODEL_PIN = "cf9831bceff36abd5a50e95328b83d16a4c1ce24"  # final J-4p/main integration target
PINNED_EXECUTOR_SHA256 = "8b9a164f52b307514d7b42f87019070689b1533f624b871a2e1d113408ebdcf7"
DEFAULT_SOURCE_REPO = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
SH_GIT_OLD = 'GIT="$KY_ROOT/wt/campaign"'
SH_GIT_NEW = 'GIT="${KY_SOURCE_REPO:-' + DEFAULT_SOURCE_REPO + '}"'
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"

P01_BINDINGS = {
    "backup_snapshot": {"needs": "owner", "script": "platform/scripts/backup_v5_small_test_job.py",
                        "fixed_args": ["--operation", "snapshot", "--execute"], "allowed_args": ["label", "scope"]},
    "backup_restore_verify": {"needs": "owner", "script": "platform/scripts/backup_v5_small_test_job.py",
                              "fixed_args": ["--operation", "restore-verify", "--execute"], "allowed_args": ["label", "scope"]},
    "smalltest_dispatch_dryrun": {"script": "platform/scripts/dispatch_v5_small_test_job.py",
                                 "fixed_args": ["--i-am-steward", "--after-settled-1", "--dry-run"]},
    "smalltest_dispatch": {"script": "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py",
                          "fixed_args": []},
    "smalltest_teardown_dryrun": {"script": "platform/scripts/teardown_v5_small_test_job.py",
                                 "fixed_args": ["--dry-run"], "allowed_args": []},
    "smalltest_teardown": {"script": "platform/scripts/teardown_v5_small_test_job.py",
                          "fixed_args": ["--execute", "--i-am-steward"], "allowed_args": []},
}
W4_KINDS = set(P01_BINDINGS)
# #3607 (f847ba24d) bound the four measuring kinds exactly, disabled; J-3a enables them with those same bindings, in their A8 form
# (§3.8 dry runs are production:false, §3.11 the remote launch carries remote_async, §5 required_rows retired).
MEASURING_BINDINGS = {
    "measuring_dispatch": {
        "enabled": True, "needs": "builder", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/measuring_launch.py",
        "fixed_args": [], "allowed_args": ["run", "classes"], "production": True, "remote_async": True, "enabled_by": "J-3c",
        "also_needs": ["gcloud"],
    },
    "measuring_dispatch_dryrun": {
        "enabled": True, "needs": "builder", "script": "platform/scripts/dispatch_v5_measuring_job.py",
        "fixed_args": ["--i-am-steward", "--after-settled-1", "--dry-run"], "allowed_args": ["run", "classes"],
        "production": False, "enabled_by": "J-3c",
    },
    "measuring_teardown_dryrun": {
        "enabled": True, "needs": "owner", "script": "platform/scripts/teardown_v5_small_test_job.py",
        "fixed_args": ["--dry-run"], "allowed_args": [], "production": False, "enabled_by": "J-3d",
    },
    "measuring_teardown": {
        "enabled": True, "needs": "owner", "script": "platform/scripts/teardown_v5_small_test_job.py",
        "fixed_args": ["--execute", "--i-am-steward"], "allowed_args": [], "production": True, "enabled_by": "J-3d",
    },
}
# A8 §3.11: the kinds whose work continues remotely after the child returns — the only ones that take the production fence.
REMOTE_ASYNC_KINDS = {"smalltest_dispatch", "measuring_dispatch", "century_dispatch", "verification_job"}
# J-2a M6/M7: the one added read-only kind (fleet/CLOUDRUN_READBACK_v1_0.md). Exact binding, not permission for any other op.
CLOUDRUN_READBACK = {
    "enabled": True, "needs": "gcloud", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/cloudrun_readback.py",
    "fixed_args": [], "allowed_args": ["execution", "logs"], "requesters": ["adhikarin", "v1", "v2"], "production": False,
    "timeout_s": 600, "enabled_by": "J-2a",
}
# A7 D-44: `read_only` marks the kinds the executor accepts mechanically; `quiescence_check` is the one added read-only kind (session readback).
READ_ONLY_KINDS = ("readback_sql", "migration_readback", "cloudrun_job_readback", "quiescence_check")
QUIESCENCE_CHECK = {
    "enabled": True, "needs": "pgenv", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/quiescence_sessions.sh",
    "fixed_args": [], "allowed_args": ["operation", "execution_readback"], "requesters": ["adhikarin", "v1", "v2", "sutradhara"],
    "production": False, "read_only": True, "timeout_s": 300, "enabled_by": "B-1",
}
# SR-J3-REAPER-PAUSE (enabled_by J-3c): the five governed Cloud Scheduler kinds plus SR-J3-CANCEL-NULL's measuring_cancel, appended after every earlier kind. Exact bindings; the flag is the only
# enablement edit (flip `enabled` here and in the table together to hold them back).
SCHEDULER_SCRIPT = "00_ARCHITECTURE/briefs/kalayantra/fleet/scheduler_reaper.py"
SCHEDULER_BINDINGS = {
    "scheduler_readback": {"enabled": True, "needs": "gcloud", "script": SCHEDULER_SCRIPT, "fixed_args": ["--action", "readback"], "allowed_args": ["job"],
                           "requesters": ["adhikarin", "v1", "v2"], "production": False, "read_only": True, "timeout_s": 600, "enabled_by": "J-3c"},
    "scheduler_pause_dryrun": {"enabled": True, "needs": "gcloud", "script": SCHEDULER_SCRIPT, "fixed_args": ["--action", "pause", "--dry-run"],
                               "allowed_args": ["job", "resume-by"], "production": False, "timeout_s": 300, "enabled_by": "J-3c"},
    "scheduler_pause": {"enabled": True, "needs": "gcloud", "script": SCHEDULER_SCRIPT, "fixed_args": ["--action", "pause"],
                        "allowed_args": ["job", "resume-by"], "production": True, "timeout_s": 600, "enabled_by": "J-3c"},
    "scheduler_resume_dryrun": {"enabled": True, "needs": "gcloud", "script": SCHEDULER_SCRIPT, "fixed_args": ["--action", "resume", "--dry-run"],
                                "allowed_args": ["job"], "production": False, "timeout_s": 300, "enabled_by": "J-3c"},
    "scheduler_resume": {"enabled": True, "needs": "gcloud", "script": SCHEDULER_SCRIPT, "fixed_args": ["--action", "resume"],
                         "allowed_args": ["job"], "production": True, "timeout_s": 600, "enabled_by": "J-3c"},
    "measuring_cancel_dryrun": {"enabled": True, "needs": "gcloud", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/measuring_cancel.py", "fixed_args": ["--dry-run"],
                               "allowed_args": ["execution"], "production": False, "timeout_s": 300, "enabled_by": "J-3c"},
    "measuring_cancel": {"enabled": True, "needs": "gcloud", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/measuring_cancel.py", "fixed_args": [],   # SR-J3-CANCEL-NULL
                         "allowed_args": ["execution"], "production": True, "timeout_s": 900, "enabled_by": "J-3c"},
}
ENABLED_KINDS = {"readback_sql", "migration_readback", "cloudrun_job_readback", "quiescence_check", "local_schema_seed", "finalize"} | set(P01_BINDINGS) | set(MEASURING_BINDINGS) | set(SCHEDULER_BINDINGS)   # J-3a: the four measuring kinds; J-3c: the seven scheduler/cancel kinds
K9_KINDS = ["orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify", "layer_publish", "layer_rollback"]
P10 = {"J-1a": "smalltest_dispatch", "J-4b": "verification_job", "J-4d": "century_dispatch",
       "J-6m": "publish_head", "J-6r": "rollback_head"}
BOUNDARY_FUNCTIONS = ["validate", "execute", "run_one", "main", "lease_live", "request_digest", "fence_quiescent",
                      "refresh_refusal_reason", "handover_from_main", "refresh_from_main_or_fail_closed",
                      "capabilities", "run_group"]
BOUNDARY_CONSTANTS = ["CHILD_ENV_ALLOW", "SAFE_ID", "SAFE_ARG", "SHA", "MAX_TIMEOUT", "CANONICAL_CHART"]
A8_REMOVED_CONSTANTS = ["APPROVAL_MAX_AGE_S"]   # A8 §4: the 3-hour acceptance age cap is gone; normalize_wave4 restores the pin's line so the rest compares


def git_show(rev_path):
    p = subprocess.run(["git", "-C", str(REPO), "show", rev_path], capture_output=True)
    assert p.returncode == 0, f"cannot read {rev_path}: {p.stderr.decode()[-300:]}"
    return p.stdout


def base_text(rel):
    return git_show(f"{PLAN_PIN}:{rel}").decode()


def load_ops(text):
    return json.loads(text)


def enabled_state(kind, entry):
    """True/False only; anything else is a test failure, never a silent pass."""
    assert isinstance(entry, dict) and "enabled" in entry, f"{kind}: no readable `enabled`"
    assert entry["enabled"] is True or entry["enabled"] is False, f"{kind}: `enabled` is not a boolean"
    return entry["enabled"]


def model_items():
    return {i["id"]: i for i in json.loads(MODEL.read_text())["items"]}


def detector_definition(item_id):
    return model_items()[item_id]["detector"]


def flip(text, kind):
    """The table text with ONE entry's `enabled` set true."""
    out, n = re.subn(r'("' + re.escape(kind) + r'"\s*:\s*\{\s*"enabled"\s*:\s*)false', r"\1true", text)
    assert n == 1, f"{kind}: expected one disabled entry to flip, found {n}"
    return out


# ───────────────────────────── the table ─────────────────────────────

def test_every_enabled_by_is_a_model_item():
    ids = set(model_items())
    ops = load_ops(OPS_FILE.read_text())["ops"]
    bad = {k: e.get("enabled_by") for k, e in ops.items() if e.get("enabled_by") not in ids}
    assert not bad, f"enabled_by names an id that is not in the plan model: {bad}"


def test_enabled_set_is_exactly_bootstrap_cloudrun_readback_and_six_p01_kinds():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    assert {k for k, e in ops.items() if enabled_state(k, e)} == ENABLED_KINDS


def test_enabled_is_the_first_key_of_every_entry():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for kind, entry in ops.items():
        assert next(iter(entry)) == "enabled", f"{kind}: first key is {next(iter(entry))}"


def test_p10_entries_present_with_only_j1a_enabled():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for item, kind in P10.items():
        assert kind in ops, f"{kind} is missing"
        assert enabled_state(kind, ops[kind]) is (item == "J-1a"), f"{kind} has unexpected enablement"
        assert ops[kind]["enabled_by"] == item


def test_table_equals_the_pin_except_reviewed_k9_and_w4_preparation_edits():
    assert_table_matches_pin(load_ops(OPS_FILE.read_text()))


def assert_table_matches_pin(now):
    base = load_ops(base_text(OPS_REL))
    expected_order = list(base["ops"])
    pos = expected_order.index("measuring_dispatch") + 1
    expected_order[pos:pos] = ["measuring_dispatch_dryrun", "measuring_teardown_dryrun", "measuring_teardown"]
    expected_order.insert(expected_order.index("migration_readback") + 1, "cloudrun_job_readback")
    expected_order.insert(expected_order.index("cloudrun_job_readback") + 1, "quiescence_check")
    expected_order += list(SCHEDULER_BINDINGS)                      # SR-J3-REAPER-PAUSE: appended last
    assert set(now) == set(base) and set(now["ops"]) == set(expected_order), "the set of kinds or top-level keys changed"
    assert list(now["ops"]) == expected_order, "the order of kinds changed"
    expected = json.loads(json.dumps(base["ops"]))
    for kind in K9_KINDS:
        assert expected[kind]["enabled_by"] == "K9-3", f"{kind}: the pin no longer says K9-3 — test premise broken"
        expected[kind]["enabled_by"] = "K9-23"
        assert "TO_BE_SET_BY_K9-3" in expected[kind]["script"]
        expected[kind]["script"] = expected[kind]["script"].replace("TO_BE_SET_BY_K9-3", "TO_BE_SET_BY_K9-23", 1)
    expected["smalltest_dispatch"]["script"] = "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py"
    expected["smalltest_dispatch"]["also_needs"] = ["gcloud"]
    expected["smalltest_dispatch_dryrun"]["fixed_args"] = ["--i-am-steward", "--after-settled-1", "--dry-run"]
    expected["verification_job"]["needs"] = "gcloud"
    expected.update(json.loads(json.dumps(MEASURING_BINDINGS)))
    expected["cloudrun_job_readback"] = json.loads(json.dumps(CLOUDRUN_READBACK))
    expected["quiescence_check"] = json.loads(json.dumps(QUIESCENCE_CHECK))
    expected.update(json.loads(json.dumps(SCHEDULER_BINDINGS)))
    for kind in READ_ONLY_KINDS[:3]:
        expected[kind]["read_only"] = True
    for kind, phase in [("measuring_dispatch", "J-3a"), ("century_dispatch", "J-4d"),
                        ("verification_job", "phase 10 after P06b"), ("publish_head", "J-6m"), ("rollback_head", "J-6r")]:
        expected[kind]["prepared_dry_run"] = {
            "enabled": False, "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/operation_dryrun.py",
            "fixed_args": ["--dry-run", "--kind", kind], "allowed_args": expected[kind]["allowed_args"], "enable_at": phase,
            "attestation": "PREPARATION_ONLY; dry_run_passed=false; allocate a real child before binding or enablement"}
    for kind, binding in P01_BINDINGS.items():
        expected[kind].update(enabled=True, **binding)
    for kind in W4_KINDS | {"readback_sql"}:
        key = "lane_readback" if kind == "readback_sql" else "lane_dry_run"
        expected[kind][key] = {"script": "00_ARCHITECTURE/briefs/kalayantra/fleet/lane_smalltest.py", "needs": "none"}
    for kind, entry in expected.items():          # A8 (§3.8, §3.11, §5): required_rows retired; dry runs production:false; remote kinds flagged
        entry.pop("required_rows", None)
        if kind.endswith("_dryrun"): entry["production"] = False
        if kind in REMOTE_ASYNC_KINDS: entry["remote_async"] = True
    for kind, entry in now["ops"].items():
        assert set(entry) == set(expected[kind]), f"{kind}: key set changed"
        assert next(iter(entry)) == "enabled", f"{kind}: enabled must remain first"
        for key in entry:
            assert entry[key] == expected[kind][key], f"{kind}.{key}: {entry[key]!r} != {expected[kind][key]!r}"
    # the only top-level difference allowed is `_doc`
    assert {k: v for k, v in now.items() if k != "_doc"} == {k: v for k, v in base.items() if k != "_doc"} | {"ops": now["ops"]}


def test_table_pin_refuses_an_extra_kind():
    now = load_ops(OPS_FILE.read_text())
    assert_table_matches_pin(now)
    now["ops"]["measuring_unreviewed"] = dict(MEASURING_BINDINGS["measuring_dispatch_dryrun"])
    with pytest.raises(AssertionError, match="set of kinds"):
        assert_table_matches_pin(now)


@pytest.mark.parametrize("kind", MEASURING_BINDINGS)
@pytest.mark.parametrize("field,value", [
    ("enabled", False), ("script", "platform/scripts/unreviewed.py"),
    ("fixed_args", ["--execute"]), ("allowed_args", ["unreviewed"]),
])
def test_table_pin_refuses_unreviewed_measuring_changes(kind, field, value):
    now = load_ops(OPS_FILE.read_text())
    assert_table_matches_pin(now)
    now["ops"][kind][field] = value
    with pytest.raises(AssertionError, match=re.escape(f"{kind}.{field}")):
        assert_table_matches_pin(now)


def test_k9_placeholders_name_k9_23_and_none_is_filled():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for kind in K9_KINDS:
        assert ops[kind]["enabled_by"] == "K9-23"
        assert ops[kind]["script"].startswith("TO_BE_SET_BY_K9-23"), kind
        assert "K9-3" not in ops[kind]["script"].replace("K9-23", ""), kind
    assert ops["local_schema_seed"]["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/local_db.sh"
    assert ops["local_schema_seed"]["fixed_args"] == ["seed"]


def test_doc_states_what_it_serves_and_assumes_no_enablement_path():
    doc = load_ops(OPS_FILE.read_text())["_doc"]
    assert "`enabled_by` names the item an entry serves" in doc
    assert "campaign builders never edit this file" in doc
    assert "open: enablement path" in doc
    assert "FORMAT RULE: `enabled` is the FIRST key of every entry" in doc
    for stale in ("landed by the plan-model item", "set by the item that enables the entry"):
        assert stale not in doc, f"_doc still says: {stale}"


@pytest.mark.parametrize("item,kind", sorted(P10.items()))
def test_model_completion_detector_preserves_main_authority(item, kind):
    # Final main replaced the old enablement regex with earned code/operation
    # completion detectors. Preserve those definitions while P01 enables bindings.
    main_model = json.loads(git_show(f"{MODEL_PIN}:00_ARCHITECTURE/control/kalayantra/plan_model.json"))
    main_item = next(i for i in main_model["items"] if i["id"] == item)
    detector = detector_definition(item)
    assert detector == main_item["detector"]
    assert not detector.get("path", "").endswith("/" + OPS_REL)
    assert enabled_state(kind, load_ops(OPS_FILE.read_text())["ops"][kind]) is (item == "J-1a")


def test_detector_state_unreadable_is_a_failure():
    # a table whose entry state the helper cannot read must fail, not pass
    with pytest.raises(AssertionError):
        enabled_state("x", {"enabled": "true"})
    with pytest.raises(AssertionError):
        enabled_state("x", {"needs": "none"})
    with pytest.raises(KeyError):
        detector_definition("NO-SUCH-ITEM")


# ───────────────────────────── the authority boundary ─────────────────────────────

def _strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
    return tree


def _is_git_assign(node):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "GIT")


def _segments(src):
    tree = ast.parse(src)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out[node.name] = ast.get_source_segment(src, node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = ast.get_source_segment(src, node)
    return out


# OWNER-MINIMAL-PROTECTION-NOW (mechanical acceptance of a production write): validate, signer_acceptance_problem, canonical_sha, mechanical_exempt, pack_fill_check,
# dry_run_check, mechanical_problem, mechanical_pre_acceptance and the PACK_* / SIGNED_ONLY_KINDS / NO_DRYRUN_KINDS / DRYRUN_IDENTITY_FIELDS / HEX64 constants are pinned the same way.
# A7 D-44 (mechanical acceptance): fence_quiescent / execute / run_one edits and the session_marker, write_new_json, measured_identity,
# mechanical_* and accepted_cloudrun_execution additions are pinned the same way.
# Exact Wave 4 safety-fix, #3607 (f847ba24d) measuring and J-1a lane additions, including the
# local_schema_seed scratch lifecycle (#3627) and the D-33 generated-overlay hand-off (#3672, d62eb02d4:
# overlay_proofs, apply_generated_overlay and their call sites in receipt/execute/execute_lane), and the J-3c blocker fix (2026-10-18: the measuring dry-run rollback proof is parsed from the child's stdout alone), as made structural by SR-EXECUTOR-FRAMING
# (child_stderrs and its call sites in execute/execute_lane/run_one/receipt/scheduler_backstop_fire: stdout and stderr are stored separately, never joined) and the Amendment A8 executor changes
# (validate, validate_lane, execute_lane, execute, main, request_digest, refresh_from_main_or_fail_closed, remote_async and the two
# module constants UNBOUND_REQUEST_FIELDS / REMOTE_ASYNC_KINDS). Each hash is of the merged executor.py segment; every other mutation,
# including weakening these functions, fails the boundary pin.
W4_FUNCTION_HASHES = {'fence_quiescent': '4e5ee3a3318f4d556f2f54061bad3227ec25c8fd1a19a09defc7de5afd96b416', 'receipt': '5c4b2183fb4f529ead0ab61dcd21dd997c281feaa7edd38adf68a35e5682e784', 'smalltest_policy': '7eeb58f3824919057e9a5845a816340981db7358ecace5ff130ac57f26efea58', 'smalltest_policy_problem': '5b0eba5031bde1fd947b380b210363d875a54e7c90a48fbff5231048faf3ccc7', 'validate': '5c46c4ba8dab9baf7fd412ad0ecae19d3c61e344d41aeec487fed96e5b6a7c3a', 'lane_selected': '16c586e33156c646f6411e46738929625f6e8d8533157fef16a9428fdb2f843d', 'lane_target_settings': 'aa4899d9eeea3ee66b6c85bdcd122108b2b67863009f9132ec750b12eb9a22a9', 'validate_lane': '88bf9fe8db575678fc093c7ca3f65238a650a085d0c530334553f6a3cf86058c', 'lane_qualification': 'bdfdb3a7f981c88dbbb79ebe4fca31745598a676a3ed330d655794786ff4ae50', 'lane_child_env': 'cb2e88d98cb481152a14b361f84403fd0861d771fb127bfeadd3df53f1ee9d34', 'execute_lane': '55ec56f43c66590db415dbc5141b889fe226392e2dd81bcc14568d9147a9d925', 'receipt_lane': 'c93ccb7e594b3080c2b8d78ee32e95e245217784a57ebb141088fc9e3ca53f05', 'execute': 'c121e7e9ab5598343d0d74b60e7d3029c064643ffc510b49e9f086235d72a2b0', 'main': 'f8298c2d910211eb27ba8ec419d542ef13566a2f816a56c60a2f9c549381f4c5', 'child_stderrs': '2701c3a828806e2e6653b398609becae1dbf40043a5d1efe6d4335c7abbe902a', 'overlay_proofs': '3fe0d184de37b9f83a74d4db2544f1db75997e4a875602f8f3cd3974b14e1b53', 'apply_generated_overlay': 'effe0b423c3c0328c4b3da9e2694097c022125fc5cb81ff59420a6cf54cf19c3', 'run_one': 'f30360721639b59cd9371c10aec7fc2251e2aef8acebdf20d78a0e856894adbb', 'session_marker': '21216adbf560807fffed590211a11235484167a5dbd762a18aed9c59cdd5ab09', 'write_new_json': 'b69919f6644041481108595fa11fe896bf8ede6de391adca233a28ea8a6c3e26', 'measured_identity': 'f47bc85d6d3516158ea1ef399d8e28a74674318d4842f9596da43c26a5f49222', 'mechanical_post_acceptance': '383b0a42ec72e3ed3d840f9693ecb288d4e7a431f285553601a244fffd55ed0e', 'accepted_cloudrun_execution': '5a87517fae4a7febf1eb0479e56b70bf90673e4569a00f74897ba2e298f5ae7d', 'mechanical_quiescence': 'c893b95cb448bebbb2899238059139e431d842dca307c4dc71bdc5e8526e260c', 'mechanical_acceptance': 'c9e263a19704a100a4583ad84cf6126d4bdff10c312aad7cd964606fae12a806', 'request_digest': '972ee7e7f9d665377108a9ab233c45db04b3e8a9a31825dc7560ce05b08406b6', 'refresh_from_main_or_fail_closed': 'c177789a8289a212e5690d1a70b87a34e36c34df052c1687e5cd3965f78eb18c', 'remote_async': '053f72a12ac1629af29731e3f5ab77bcecfde2c1fb01e56c256640a886755b98', 'UNBOUND_REQUEST_FIELDS': 'e3c09d66976b1be9186502bceb7b318a1416f93cd640bdbc4ad852e437b17a12', 'REMOTE_ASYNC_KINDS': '3896625f1c5786170001c8b85ac4e5b0dde89fe249de020d76920b0ad5ef1155', 'SCHEDULER_JOB': 'eb099f996955c70fd6bd1aa6a50fc7dfc195b7c3e78594751dd226d9b862faf4', 'SCHEDULER_PROJECT': 'e63bc56c1f7ff7c1cabcbbfe7af3a48b3aaeec1aa4c7e090144cd0167d62afa5', 'SCHEDULER_REGION': 'c0267426fb76794ab995158ddec9e3fc8127772b137618e9019892344acb0b80', 'SCHEDULER_SCRIPT': 'f479c65ab5597d6fca611a5804d02dcaa87d5c3e099dffa466f948cab610f083', 'SCHEDULER_ACTION': 'bcce7bd9f31fbe10c8fa722a2bd609416107b280bf4e26550633dc8cf0561a00', 'SCHEDULER_STATES': 'b57629e1c41abd330b2da37f27865473060e2a104d0d28b287d74b97b36a731d', 'SCHEDULER_UTC': 'd463e745920163c76c1dea9659a8eeef2aed71da4bd059a8588f1fddb69596b4', 'SCHEDULER_BACKSTOP': '5336986b52b9342f36bebb292599e0faffefdfba49d95329afda5452904df188', 'lease_expiry': '23f2b14757ee303848c7f77c3d39e066dcf872a6122855707ac7d9401a1aa0c4', 'scheduler_policy_problem': '12630309cd268eeb090355a5844ae4d462f472b11e9da75f02495d896fe0a94f', 'scheduler_proof': '8ef650eaa9c0e78ee080de1862aecf52c378ca5f6e72012600064c4f28d41428', 'scheduler_write': '53a2d469ef44b3a9805794d9c889e4b14fbf6c97e07f94800d172d499888389b', 'scheduler_backstop_records': 'db053014456aaa26df639582cdbb728c9d213545f0221fd1c6a9b917fae5e552', 'arm_scheduler_backstop': '0e7a39078a9870914c142643be9be49bf1081ebc7be2c8ee2415c3de95b7bd29', 'scheduler_backstop_satisfy': '201c57f603bb483f38add84b058d28ae28340aae3a2d46fe4f721b9918d74081', 'scheduler_backstop_fire': '8dc3f584770fdd06d363cf20be284661aead0a589cf9832e8ded2db18b7126ae', 'scheduler_backstop_tick': 'c6fcad69671e482c5460eda18f0d07f53699c39195802f9c0cd431b1a11fe4b8', 'measuring_cancel_problem': '635e5e5b1fc83e143a793eb4c2b54e5fc200593b8f275b653cf577f231c8df42', 'measuring_cancel_proof': '19b48179419b7864b6640bedbc19cfbee601b2bd263030d26d18b69ff6930765', 'canonical_sha': 'f8f23ad6c9162e9444540ddfdf1046ac31db16f1807ec27cb0fc1d6482a4d0ba', 'mechanical_exempt': '802a819301de8a5ad283a693cc87931548cfbd9ea93f1cad2187f0aeb3f1de0a', 'pack_fill_check': '084a2d76b85ad35339ee50e820747e0d8617e04d1b4da9a87701c0f17c8d73c3', 'dry_run_check': 'ba4c756c73f67f3500f30d73733573882a59032af7399835d062c0eaa8f82269', 'mechanical_problem': 'b1b2e07fce11b99da96af74d59f1b2112d686a65f6980a4bafd0ad812873fe88', 'mechanical_pre_acceptance': '4c566fb91b17c63ddabdd5b7859640daaef57110ed114f054272718f5e4c2090', 'signer_acceptance_problem': '81b018c05f10e2355e7bfe2168ae2db625e13a124f18dbf5482b13f9dd23afea', 'PACK_ALLOWLIST': '895b42a1a543f823c50bf4504f68c969ca317324d1583716b09393883a845a56', 'SIGNED_ONLY_KINDS': '73a9f5fa12f897b89e6a3bb7ca126826f67b812bef4fd55d25c2c2343db815a5', 'NO_DRYRUN_KINDS': '1831c60b886d47185af1542e9be21cf4c330d3495ca9259471a37d2991d903f7', 'PACK_NEVER_FILLED': 'ae15e6db6c6772e98a7fa57994ec23c3607af03c3d81b7fc38e7dc7ee5913786', 'DRYRUN_IDENTITY_FIELDS': 'b81fe525fa8a151e2183e0f1065255b9bb0b47d43c4c7f45b80fa7397d79c528', 'HEX64': 'f4b9a1efc5cff4c648c87e337ff1353507e3ba55ceb7c9b11d9ae6f3f3bcd638'}


def _module_docstring(src):
    node = ast.parse(src).body[0]
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return ast.get_source_segment(src, node)
    return None


def normalize_wave4(base_src, work_src):
    base_seg, work_seg = _segments(base_src), _segments(work_src)
    for name, digest in W4_FUNCTION_HASHES.items():
        segment = work_seg.get(name, "")
        if hashlib.sha256(segment.encode()).hexdigest() == digest:
            if name in base_seg:
                work_src = work_src.replace(segment, base_seg[name], 1)
            elif segment.startswith("def "):
                work_src = work_src.replace(segment + "\n\n\n", "", 1)
            else:                                        # an added module constant: its whole line goes, trailing comment included
                work_src = re.sub(r"^" + re.escape(name) + r" = [^\n]*\n", "", work_src, count=1, flags=re.M)
    for name in A8_REMOVED_CONSTANTS:                    # a removed constant: the pin's exact line returns in front of the line that followed it
        following = re.search(r"^" + re.escape(name) + r" = [^\n]*\n([^\n]*\n)", base_src, re.M)
        if following and not re.search(r"^" + re.escape(name) + r" = ", work_src, re.M):
            work_src = work_src.replace(following.group(1), following.group(0), 1)
    base_doc, work_doc = _module_docstring(base_src), _module_docstring(work_src)
    if base_doc and work_doc and work_doc != base_doc:   # prose only: the AST comparison strips it, the line diff must not trip on it
        work_src = work_src.replace(work_doc, base_doc, 1)
    return work_src


def boundary_violations(base_src, work_src):
    """Why `work_src` is not the pinned executor.py plus a changed GIT assignment (empty list = boundary holds)."""
    base_segments, raw_segments = _segments(base_src), _segments(work_src)
    problems = [f"{name} safety helper missing or changed" for name, digest in W4_FUNCTION_HASHES.items()
                if name not in base_segments and hashlib.sha256(raw_segments.get(name, "").encode()).hexdigest() != digest]
    work_src = normalize_wave4(base_src, work_src)
    base_tree, work_tree = ast.parse(base_src), ast.parse(work_src)
    base_git = [n for n in base_tree.body if _is_git_assign(n)]
    work_git = [n for n in work_tree.body if _is_git_assign(n)]
    if len(base_git) != 1 or len(work_git) != 1:
        problems.append("GIT must be assigned exactly once at module level")
    base_tree.body = [n for n in base_tree.body if not _is_git_assign(n)]
    work_tree.body = [n for n in work_tree.body if not _is_git_assign(n)]
    if ast.dump(_strip_docstrings(base_tree)) != ast.dump(_strip_docstrings(work_tree)):
        problems.append("a code line other than the GIT assignment changed")
    base_seg, work_seg = _segments(base_src), _segments(work_src)
    for name in BOUNDARY_FUNCTIONS + BOUNDARY_CONSTANTS:
        if name not in base_seg:
            problems.append(f"{name} missing from the pin — test premise broken")
        elif hashlib.sha256((base_seg[name] or "").encode()).hexdigest() != hashlib.sha256((work_seg.get(name) or "").encode()).hexdigest():
            problems.append(f"{name} is not byte-identical to the pin")
    return problems


def test_pinned_executor_has_the_pinned_sha256():
    assert hashlib.sha256(git_show(f"{PLAN_PIN}:{PY_REL}")).hexdigest() == PINNED_EXECUTOR_SHA256


def test_executor_py_changes_are_only_git_and_exact_reviewed_w4_functions():
    assert boundary_violations(base_text(PY_REL), EXECUTOR_PY.read_text()) == []


def test_executor_py_remaining_line_diff_is_the_git_line_only():
    import difflib
    base_src = base_text(PY_REL)
    base, work = base_src.splitlines(), normalize_wave4(base_src, EXECUTOR_PY.read_text()).splitlines()
    changed = [l for l in difflib.unified_diff(base, work, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    for line in changed:
        body = line[1:].strip()
        assert body.startswith("GIT = ") or body.startswith("#"), f"unexpected changed line: {line}"
    assert any(l.startswith("+GIT = ") for l in changed), "the GIT assignment did not change"


@pytest.mark.parametrize("old,new", [
    ("MAX_TIMEOUT = 6 * 3600", "MAX_TIMEOUT = 7 * 3600"),
    ('if not issued <= current < expires: return "approval expired or not yet valid"', 'if not issued <= current: return "approval expired or not yet valid"'),
    ('return op.get("remote_async") is True or kind in REMOTE_ASYNC_KINDS', 'return op.get("remote_async") is True'),
    ('if kind.endswith("_teardown"): required.append("backup_taken")', 'pass'),
    ('if k not in UNBOUND_REQUEST_FIELDS and not k.endswith("_expires_at")', 'if k not in UNBOUND_REQUEST_FIELDS'),
    ('"HOME", "PATH", "LANG"', '"HOME", "PATH", "LANG", "KY_BUILDER_DATABASE_URL"'),
    ('return f"kind {req[\'kind\']} is not enabled', 'return f"kind {req[\'kind\']} is disabled'),
    ('if not caps.get(op["needs"], False): return f"capability_missing: {op[\'needs\']}"', 'pass'),
    ("def now() -> str: return dt.datetime.now(dt.timezone.utc).isoformat(timespec=\"seconds\")",
     "def now() -> str: return dt.datetime.now().isoformat(timespec=\"seconds\")"),
    ('    return subprocess.run(["git", "-C", str(GIT), *args], capture_output=True, text=True, timeout=timeout)',
     '    return subprocess.run(["git", "-C", str(GIT), *args], capture_output=True, text=True, timeout=timeout + 1)'),
])
def test_boundary_test_fails_when_another_code_line_changes(old, new):
    work = EXECUTOR_PY.read_text()
    assert work.count(old) == 1, f"mutation anchor not unique in executor.py: {old!r}"
    problems = boundary_violations(base_text(PY_REL), work.replace(old, new))
    assert problems, "the boundary test accepted a changed code line"


@pytest.mark.parametrize("name", ["smalltest_policy", "smalltest_policy_problem", "remote_async"])
def test_boundary_refuses_removal_of_a_new_safety_helper(name):
    work = EXECUTOR_PY.read_text()
    segment = _segments(work)[name]
    assert boundary_violations(base_text(PY_REL), work.replace(segment, "", 1))


@pytest.mark.parametrize("name,old,new", [
    ("receipt", 'proof.get("rollback_confirmed") is True', 'proof.get("rollback_confirmed") is False'),
    ("fence_quiescent", '"ky.measuring_completion/1"', '"ky.smalltest_completion/1"'),
    ("smalltest_policy_problem", '"measuring_request_problem"', '"smalltest_request_problem"'),
])
def test_boundary_refuses_changes_to_reviewed_measuring_functions(name, old, new):
    work = EXECUTOR_PY.read_text()
    base = base_text(PY_REL)
    assert boundary_violations(base, work) == []
    segment = _segments(work)[name]
    assert segment.count(old) == 1
    assert boundary_violations(base, work.replace(segment, segment.replace(old, new), 1))


def test_boundary_test_fails_when_a_second_statement_hides_on_the_git_line():
    work = EXECUTOR_PY.read_text()
    m = re.search(r"^GIT = .*$", work, re.M)
    assert m
    mutated = work.replace(m.group(0), m.group(0).split("#")[0].rstrip() + "; MAX_TIMEOUT = 1", 1)
    assert boundary_violations(base_text(PY_REL), mutated)


def _load_executor(tmp_path, source_repo=None):
    saved = {k: os.environ.get(k) for k in ("KY_ROOT", "KY_SOURCE_REPO")}
    os.environ["KY_ROOT"] = str(tmp_path / "ky")
    if source_repo is None:
        os.environ.pop("KY_SOURCE_REPO", None)
    else:
        os.environ["KY_SOURCE_REPO"] = str(source_repo)
    try:
        spec = importlib.util.spec_from_file_location(f"ky_executor_table_{abs(hash((str(tmp_path), str(source_repo))))}", EXECUTOR_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_git_handle_is_the_environment_selected_source_repo(tmp_path):
    chosen = tmp_path / "some-repo"
    mod = _load_executor(tmp_path, chosen)
    assert mod.GIT == chosen and isinstance(mod.GIT, Path)
    assert mod.KY_ROOT == tmp_path / "ky"
    default = _load_executor(tmp_path, None)
    assert str(default.GIT) == DEFAULT_SOURCE_REPO
    assert default.KY_ROOT == tmp_path / "ky" and "wt" not in default.GIT.parts[-2:]


def test_executor_sh_differs_from_the_pin_only_in_the_git_assignment():
    base, work = base_text(SH_REL), EXECUTOR_SH.read_text()
    assert work.count(SH_GIT_NEW) == 1 and SH_GIT_OLD not in work
    assert work.replace(SH_GIT_NEW, SH_GIT_OLD, 1) == base
    assert subprocess.run(["bash", "-n", str(EXECUTOR_SH)], capture_output=True).returncode == 0


# ───────────────────────────── negative cases through validate ─────────────────────────────

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
ALL_CAPS = {"builder": True, "owner": True, "pgenv": True, "gcloud": True, "none": True}
# 2026-10-17 incident: an inherited GIT_DIR beats `-C`, so `git init --bare` re-initialised the SHARED repository. A fixture's git must only see what it made.
REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                      "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")


def _git_env():
    return {**{k: v for k, v in os.environ.items() if k not in REPO_LOCATING_VARS}, **GIT_ENV}


def _git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=_git_env())
    assert p.returncode == 0, f"git {args}: {p.stderr[-300:]}"
    return p.stdout.strip()


def _lease_table(lease_id):
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    expiry = (dt.datetime.now(ist) + dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    return ("# fixture\n\n## 1. Leases\n\n| lease | a | b | c | expires | state |\n|---|---|---|---|---|---|\n"
            f"| {lease_id} | x | y | z | {expiry} | ACTIVE |\n\n## 2. Other\n")


class World:
    """A temporary repository whose origin is a local bare repo: origin/main carries a table, origin/campaign-coordination a lease."""

    def __init__(self, tmp_path, monkeypatch, table_text, lease_id="lease-1"):
        for k, v in GIT_ENV.items():
            monkeypatch.setenv(k, v)
        for k in REPO_LOCATING_VARS:  # the executor under test runs git from this environment too
            monkeypatch.delenv(k, raising=False)
        self.root = tmp_path / "ky"
        self.origin = tmp_path / "origin.git"
        self.repo = tmp_path / "source-repo"
        self.lease_id = lease_id
        _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(self.origin))
        _git(tmp_path, "init", "-q", "-b", "main", str(self.repo))
        _git(self.repo, "remote", "add", "origin", str(self.origin))
        (self.repo / OPS_REL).parent.mkdir(parents=True)
        (self.repo / OPS_REL).write_text(table_text)
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "table")
        self.reviewed = _git(self.repo, "rev-parse", "HEAD")
        _git(self.repo, "push", "-q", "origin", "main")
        _git(self.repo, "checkout", "-q", "-b", "campaign-coordination")
        (self.repo / COORD_REL).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / COORD_REL).write_text(_lease_table(lease_id))
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "lease")
        _git(self.repo, "push", "-q", "origin", "campaign-coordination")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "fetch", "-q", "origin")
        self.mod = _load_executor(tmp_path, self.repo)
        self.mod.ACC.mkdir(parents=True, exist_ok=True)

    def table(self):
        table = self.mod.load_table()
        assert table is not None, "origin/main of the temporary repository is unreadable"
        return table

    def production_request(self, kind, **over):
        req = {"operation_id": "op-1", "kind": kind, "item_id": "X", "idempotency_key": "key-1", "requested_by": "adhikarin",
               "kyd": "kyd-1", "args": {}, "chart_id": CANONICAL_CHART, "lease_id": self.lease_id,
               "reviewed_commit": self.reviewed,
               "expires_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(timespec="seconds")}
        req.update(over)
        return req

    def accept(self, req, **over):
        acc = {"result": "ACCEPTED", "operation_id": req["operation_id"], "by": "v1", "reviewed_commit": req["reviewed_commit"],
               "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "request_sha256": self.mod.request_digest(req),
               "rows": {}, "checks": {"backup_taken": True, "restore_verified": True, "dry_run_passed": True}}
        acc.update(over)
        path = self.mod.ACC / f"{req['operation_id']}.json"
        path.write_text(json.dumps(acc))
        return {**req, "acceptance_receipt": str(path)}


def simple_request(kind, by="adhikarin", **over):
    req = {"operation_id": "op-s", "kind": kind, "item_id": "X", "idempotency_key": "key-s", "requested_by": by, "kyd": "kyd-1", "args": {}}
    req.update(over)
    return req


def copy_with(text, kind, **fields):
    """An independent fixture table with `kind` enabled and `fields` set."""
    ops = json.loads(text)
    ops["ops"][kind]["enabled"] = True
    ops["ops"][kind].update(fields)
    return json.dumps(ops)


def _linked_worktree_victim(tmp_path):
    """A throwaway repository with one linked worktree: (repository, the linked worktree's gitdir), as in the 2026-10-17 incident."""
    victim = tmp_path / "victim"
    _git(tmp_path, "init", "-q", "-b", "main", str(victim))
    _git(victim, "commit", "-q", "--allow-empty", "-m", "x")
    _git(victim, "worktree", "add", "-q", str(tmp_path / "linked"), "-b", "linked")
    assert _git(victim, "config", "--bool", "core.bare") == "false"
    return victim, next((victim / ".git" / "worktrees").iterdir())


def _core_bare(victim):
    return subprocess.run(["git", "--git-dir", str(victim / ".git"), "config", "--bool", "core.bare"], capture_output=True, text=True, env=_git_env()).stdout.strip()


def test_world_fixture_leaves_a_repository_named_by_an_inherited_git_dir_untouched(tmp_path, monkeypatch):
    """The 2026-10-17 incident, on a throwaway repository: GIT_DIR names a LINKED WORKTREE's gitdir and the fixture's plain `git init` re-initialised the whole repository as bare
    (core.bare=true in the common config). The fixture must leave that repository's core.bare alone."""
    victim, linked_gitdir = _linked_worktree_victim(tmp_path)
    scratch = tmp_path / "w"
    scratch.mkdir()
    monkeypatch.setenv("GIT_DIR", str(linked_gitdir))
    try:
        w = World(scratch, monkeypatch, OPS_FILE.read_text())
    finally:  # judged first even when building the fixture failed half-way: that is what a re-initialised victim looks like
        assert _core_bare(victim) == "false", "the fixture's git re-initialised the repository named by the inherited GIT_DIR (core.bare=%s)" % _core_bare(victim)
    assert w.reviewed and (w.origin / "HEAD").is_file()  # the fixture still built its own repositories


def test_fleet_conftest_drops_git_dir_before_any_fixture_inherits_it(tmp_path):
    """A pytest process started with GIT_DIR exported: the fleet conftest must keep a fixture's plain `git init` off that repository (throwaway repository only)."""
    victim, linked_gitdir = _linked_worktree_victim(tmp_path)
    run = tmp_path / "run"
    run.mkdir()
    (run / "conftest.py").write_text((FLEET / "tests" / "conftest.py").read_text())
    (run / "test_x.py").write_text('import subprocess\n\ndef test_init(tmp_path):\n    subprocess.run(["git", "init", "-q", str(tmp_path / "repo")], check=True, capture_output=True)\n')
    env = {**_git_env(), "GIT_DIR": str(linked_gitdir)}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(run / "test_x.py")], capture_output=True, text=True, env=env, cwd=run)
    assert r.returncode == 0, r.stdout + r.stderr
    assert _core_bare(victim) == "false"


def test_validate_reads_the_real_table_through_the_selected_repository(tmp_path, monkeypatch):
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    assert str(w.mod.GIT) == str(w.repo)
    table = w.table()
    assert {k for k, e in table.items() if enabled_state(k, e)} == ENABLED_KINDS
    # positive controls: the enabled kinds are admitted for their requesters, so the refusals below are not vacuous
    assert w.mod.validate(simple_request("readback_sql", "v1", args={"sql_file": "a.sql"}), table, ALL_CAPS) is None
    assert w.mod.validate(simple_request("finalize", "sutradhara"), table, ALL_CAPS) is None


@pytest.mark.parametrize("kind", ["verification_job", "century_dispatch", "publish_head", "rollback_head", *K9_KINDS])
def test_request_for_a_disabled_kind_is_not_enabled(tmp_path, monkeypatch, kind):
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    why = w.mod.validate(w.production_request(kind), w.table(), ALL_CAPS)
    assert why is not None and "not enabled" in why, why


@pytest.mark.parametrize("kind", K9_KINDS)
def test_entry_enabled_in_a_copy_with_a_placeholder_script_is_refused(tmp_path, monkeypatch, kind):
    text = OPS_FILE.read_text()
    w = World(tmp_path, monkeypatch, copy_with(text, kind))
    table = w.table()
    assert enabled_state(kind, table[kind]) is True and "TO_BE_SET" in table[kind]["script"]
    assert w.mod.validate(w.production_request(kind), table, ALL_CAPS) == "operation script not yet reviewed/landed"


def test_requester_outside_the_entrys_requesters_is_refused(tmp_path, monkeypatch):
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    table = w.table()
    for kind, by in (("readback_sql", "sutradhara-x"), ("readback_sql", "v3"), ("local_schema_seed", "adhikarin"),
                     ("local_schema_seed", "v1"), ("finalize", "adhikarin"), ("finalize", "v2")):
        why = w.mod.validate(simple_request(kind, by), table, ALL_CAPS)
        assert why is not None and "may not request" in why, (kind, by, why)
    assert w.mod.validate(simple_request("local_schema_seed", "sutradhara"), table, ALL_CAPS) is None


def test_entry_without_requesters_accepts_adhikarin_alone(tmp_path, monkeypatch):
    text = OPS_FILE.read_text()
    kind = "backup_snapshot"
    w = World(tmp_path, monkeypatch, copy_with(text, kind, script="platform/scripts/fixture_backup.sh"))
    table = w.table()
    assert "requesters" not in table[kind]
    for by in ("v1", "sutradhara", "kimi"):
        why = w.mod.validate(w.production_request(kind, requested_by=by), table, ALL_CAPS)
        assert why is not None and "may not request" in why, (by, why)


def _production_world(tmp_path, monkeypatch):
    text = OPS_FILE.read_text()
    # a copy in which a production kind is enabled with a real-looking script; the repository's own table is never changed
    w = World(tmp_path, monkeypatch, copy_with(text, "backup_snapshot", script="platform/scripts/fixture_backup.sh"))
    return w, w.table()


def test_production_request_with_a_bound_acceptance_is_admitted_control(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    req = w.accept(w.production_request("backup_snapshot"))
    assert w.mod.validate(req, table, ALL_CAPS) is None, "control failed — the refusals below would be vacuous"


def test_production_request_without_an_acceptance_is_refused(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    req = w.production_request("backup_snapshot")
    assert "pre-acceptance receipt missing" in w.mod.validate(req, table, ALL_CAPS)
    outside = tmp_path / "elsewhere.json"
    outside.write_text("{}")
    assert "pre-acceptance receipt missing" in w.mod.validate({**req, "acceptance_receipt": str(outside)}, table, ALL_CAPS)


def test_production_acceptance_not_bound_to_the_request_digest_is_refused(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    base = w.production_request("backup_snapshot")
    wrong_digest = w.accept(base, request_sha256="0" * 64)
    assert w.mod.validate(wrong_digest, table, ALL_CAPS) == "approval does not bind the complete request"
    # accepted for one request, then the request changes: the approval no longer binds it
    accepted = w.accept(base)
    assert w.mod.validate({**accepted, "args": {"label": "other"}}, table, ALL_CAPS) is not None
    assert w.mod.validate({**accepted, "kyd": "another-kyd"}, table, ALL_CAPS) == "approval does not bind the complete request"


@pytest.mark.parametrize("by", ["v5", "adhikarin", "sutradhara", "", None])
def test_production_acceptance_by_a_non_verifier_lane_is_refused(tmp_path, monkeypatch, by):
    w, table = _production_world(tmp_path, monkeypatch)
    req = w.accept(w.production_request("backup_snapshot"), by=by)
    why = w.mod.validate(req, table, ALL_CAPS)
    assert why is not None and "verifier lane" in why, why


@pytest.mark.parametrize("by", ["v1", "v2", "v3", "v4"])
def test_production_acceptance_by_each_verifier_lane_is_admitted(tmp_path, monkeypatch, by):
    w, table = _production_world(tmp_path, monkeypatch)
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot"), by=by), table, ALL_CAPS) is None


def test_production_acceptance_other_refusals(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=4)).isoformat(timespec="seconds")
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot"), ts=old), table, ALL_CAPS) is None   # A8 §4: no age cap
    future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat(timespec="seconds")
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot"), ts=future), table, ALL_CAPS) == "approval expired or not yet valid"
    lapsed = w.production_request("backup_snapshot", expires_at=(dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)).isoformat(timespec="seconds"))
    assert w.mod.validate(w.accept(lapsed), table, ALL_CAPS) == "approval expired or not yet valid"
    assert "different reviewed_commit" in w.mod.validate(w.accept(w.production_request("backup_snapshot"), reviewed_commit="a" * 40), table, ALL_CAPS)
    other = w.production_request("backup_snapshot", chart_id="362f9f17-0000-0000-0000-000000000000")
    assert w.mod.validate(w.accept(other), table, ALL_CAPS) == "chart_id is not the canonical chart"
    stale_lease = w.production_request("backup_snapshot", lease_id="lease-2")
    assert "lease is not the single unexpired ACTIVE row" in w.mod.validate(w.accept(stale_lease), table, ALL_CAPS)


def test_enabled_set_is_exactly_bootstrap_plus_wave4():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    assert {k for k, e in ops.items() if enabled_state(k, e)} == ENABLED_KINDS


def test_p10_entries_present_and_disabled():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for item, kind in {item: kind for item, kind in P10.items() if item != "J-1a"}.items():
        assert kind in ops, f"{kind} is missing"
        assert enabled_state(kind, ops[kind]) is False, f"{kind} must be disabled"
        assert ops[kind]["enabled_by"] == item


@pytest.mark.parametrize("item,kind", sorted({item: kind for item, kind in P10.items() if item != "J-1a"}.items()))
def test_future_table_enablement_and_typed_model_detectors_stay_separate(item, kind):
    # The reconciled model uses packet/rehearsal evidence, not enabled-string
    # completion. Preserve the legacy first-key format without inventing a detector.
    det = model_items()[item]["detector"]
    assert det["type"] in {"pr_merged", "branch_merged", "file_exists"}
    assert det.get("pr") or det.get("ref") or det.get("path")
    pattern = re.compile(r'"' + re.escape(kind) + r'"\s*:\s*\{\s*"enabled"\s*:\s*true')
    text = OPS_FILE.read_text()
    assert not pattern.search(text)
    assert pattern.search(flip(text, kind))


# Local schema seed scratch belongs to the executor, never to its caller.
@pytest.mark.parametrize("needs,connection", [
    ("pgenv", None), ("none", None), ("builder", "fixture-builder"), ("owner", "fixture-owner"),
])
@pytest.mark.parametrize("exit_code", [0, 23])
def test_seed_child_gets_owned_scratch_without_expanding_env(tmp_path, monkeypatch, needs, connection, exit_code):
    import sys
    mod = _load_executor(tmp_path)
    for directory in (mod.TMP, mod.EXEC):
        directory.mkdir(parents=True)
    # Entirely synthetic parent environment: no actual connection is read or sent.
    parent_env = {"HOME": str(tmp_path), "PATH": os.defpath, "LANG": "C", "TZ": "UTC", "TMPDIR": str(tmp_path),
                  "KY_SCRATCH": "caller-scratch-must-not-be-inherited", "DATABASE_URL": "fixture-unrelated",
                  "KY_BUILDER_DATABASE_URL": "fixture-builder", "KY_OWNER_DATABASE_URL": "fixture-owner",
                  "UNLISTED": "must-not-leak", "JOB_SCRATCH": "must-not-leak"}
    monkeypatch.setattr(mod.os, "environ", parent_env)
    monkeypatch.setattr(mod, "PY", sys.executable)
    op = dict(load_ops(OPS_FILE.read_text())["ops"]["local_schema_seed"], script="fixture_seed.py", needs=needs)
    source = f"""import json, os, pathlib, sys
value = os.environ.get("KY_SCRATCH", "")
scratch = pathlib.Path(value)
assert value and scratch.is_absolute() and scratch.is_dir(), "absolute existing KY_SCRATCH required"
assert sys.argv[1:] == ["seed"]
assert os.environ.get("DATABASE_URL") == {connection!r}
assert not any(key in os.environ for key in ("KY_BUILDER_DATABASE_URL", "KY_OWNER_DATABASE_URL", "UNLISTED", "JOB_SCRATCH"))
assert os.environ["HOME"] == {str(tmp_path)!r} and os.environ["LANG"] == "C" and os.environ["TZ"] == "UTC"
assert os.environ["TMPDIR"] == {str(tmp_path)!r}
(scratch / "nested").mkdir()
(scratch / "nested" / "seed.log").write_text("fixture")
print(json.dumps({{"scratch": value}}))
sys.exit({exit_code})
"""
    def git_show(*args):
        assert args == ("show", "origin/main:fixture_seed.py")
        return subprocess.CompletedProcess(args, 0, source, "")
    monkeypatch.setattr(mod, "git", git_show)
    req = simple_request("local_schema_seed", "sutradhara", operation_id="seed-fixture")
    rc, output = mod.execute(req, op)
    assert rc == exit_code, output
    scratch = Path(json.loads(output)["scratch"])
    assert scratch.parent == mod.EXEC.resolve()
    assert not scratch.exists(), "operation scratch survived child completion"
    assert not list(mod.EXEC.iterdir()) and not list(mod.TMP.iterdir())
    assert parent_env["KY_SCRATCH"] == "caller-scratch-must-not-be-inherited"


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("fixture", 1), OSError("fixture spawn failure")])
def test_seed_scratch_is_removed_when_execution_raises(tmp_path, monkeypatch, failure):
    mod = _load_executor(tmp_path)
    for directory in (mod.TMP, mod.EXEC):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod.os, "environ", {})
    monkeypatch.setattr(mod, "git", lambda *args: subprocess.CompletedProcess(args, 0, "fixture", ""))
    observed = []
    def fail_child(argv, cwd, env, timeout):
        scratch = Path(env["KY_SCRATCH"])
        assert scratch.is_absolute() and scratch.is_dir()
        (scratch / "partial.log").write_text("fixture")
        observed.append(scratch)
        raise failure
    monkeypatch.setattr(mod, "run_group", fail_child)
    with pytest.raises(type(failure)):
        mod.execute(simple_request("local_schema_seed", "sutradhara"),
                    load_ops(OPS_FILE.read_text())["ops"]["local_schema_seed"])
    assert len(observed) == 1 and not observed[0].exists()
    assert not list(mod.EXEC.iterdir()) and not list(mod.TMP.iterdir())


def test_nonseed_child_does_not_inherit_caller_scratch_or_connections(tmp_path, monkeypatch):
    import sys
    mod = _load_executor(tmp_path)
    for directory in (mod.TMP, mod.EXEC):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod.os, "environ", {"TMPDIR": str(tmp_path), "KY_SCRATCH": "caller-scratch", "DATABASE_URL": "fixture-unrelated",
                                           "KY_BUILDER_DATABASE_URL": "fixture-builder", "KY_OWNER_DATABASE_URL": "fixture-owner"})
    monkeypatch.setattr(mod, "PY", sys.executable)
    source = "import os; assert not any(k in os.environ for k in ('KY_SCRATCH', 'DATABASE_URL', 'KY_BUILDER_DATABASE_URL', 'KY_OWNER_DATABASE_URL'))"
    monkeypatch.setattr(mod, "git", lambda *args: subprocess.CompletedProcess(args, 0, source, ""))
    rc, output = mod.execute(simple_request("finalize", "sutradhara"),
                             {"script": "fixture.py", "needs": "none", "production": False})
    assert rc == 0, output
    assert not list(mod.EXEC.iterdir()) and not list(mod.TMP.iterdir())
