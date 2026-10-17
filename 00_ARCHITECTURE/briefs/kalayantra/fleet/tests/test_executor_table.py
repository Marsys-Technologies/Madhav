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
TABLE_PIN = "cc9f509b480461880be80b225ff44b084995b3d7"  # reviewed Wave 4/measuring preparation
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
# #3607 (f847ba24d): exact disabled bindings, not permission to enable measuring.
MEASURING_BINDINGS = {
    "measuring_dispatch": {
        "enabled": False, "needs": "builder", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/measuring_launch.py",
        "fixed_args": [], "allowed_args": ["run", "classes"], "production": True, "enabled_by": "J-3c",
        "required_rows": ["2", "3", "7", "9", "11"], "also_needs": ["gcloud"],
    },
    "measuring_dispatch_dryrun": {
        "enabled": False, "needs": "builder", "script": "platform/scripts/dispatch_v5_measuring_job.py",
        "fixed_args": ["--i-am-steward", "--after-settled-1", "--dry-run"], "allowed_args": ["run", "classes"],
        "production": True, "enabled_by": "J-3c", "required_rows": ["2", "3", "7", "9", "11"],
    },
    "measuring_teardown_dryrun": {
        "enabled": False, "needs": "owner", "script": "platform/scripts/teardown_v5_small_test_job.py",
        "fixed_args": ["--dry-run"], "allowed_args": [], "production": True, "enabled_by": "J-3d",
        "required_rows": ["2", "3", "7", "9", "11"],
    },
    "measuring_teardown": {
        "enabled": False, "needs": "owner", "script": "platform/scripts/teardown_v5_small_test_job.py",
        "fixed_args": ["--execute", "--i-am-steward"], "allowed_args": [], "production": True, "enabled_by": "J-3d",
        "required_rows": ["2", "3", "7", "9", "11"],
    },
}
ENABLED_KINDS = {"readback_sql", "migration_readback", "local_schema_seed", "finalize"} | set(P01_BINDINGS)
K9_KINDS = ["orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify", "layer_publish", "layer_rollback"]
P10 = {"J-1a": "smalltest_dispatch", "J-4b": "verification_job", "J-4d": "century_dispatch",
       "J-6m": "publish_head", "J-6r": "rollback_head"}
BOUNDARY_FUNCTIONS = ["validate", "execute", "run_one", "main", "lease_live", "request_digest", "fence_quiescent",
                      "refresh_refusal_reason", "handover_from_main", "refresh_from_main_or_fail_closed",
                      "capabilities", "run_group"]
BOUNDARY_CONSTANTS = ["CHILD_ENV_ALLOW", "SAFE_ID", "SAFE_ARG", "SHA", "APPROVAL_MAX_AGE_S", "MAX_TIMEOUT",
                      "CANONICAL_CHART"]


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


def test_enabled_set_is_exactly_bootstrap_and_six_p01_kinds():
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
    assert set(now) == set(base) and set(now["ops"]) == set(expected_order), "the set of kinds or top-level keys changed"
    assert list(now["ops"]) == expected_order, "the order of kinds changed"
    expected = json.loads(json.dumps(base["ops"]))
    for kind in K9_KINDS:
        assert expected[kind]["enabled_by"] == "K9-3", f"{kind}: the pin no longer says K9-3 — test premise broken"
        expected[kind]["enabled_by"] = "K9-23"
        assert "TO_BE_SET_BY_K9-3" in expected[kind]["script"]
        # K9-23 binds the five still-disabled operations to the publication module (the only K9-23 edit).
        expected[kind]["script"] = "platform/python-sidecar/services/kala_core/publication.py"
        expected[kind]["cwd"] = "platform/python-sidecar"
        expected[kind]["python_module"] = "services.kala_core.publication"
        expected[kind]["fixed_args"] = [{"orchestrator_rebuild_dryrun": "rebuild-dryrun",
            "orchestrator_rebuild": "rebuild", "layer_verify": "verify", "layer_publish": "publish",
            "layer_rollback": "rollback"}[kind]]
    expected["layer_verify"]["needs"] = "layer_verifier"
    expected["layer_verify"]["allowed_args"] = ["run-id", "generation", "independently-derived-digest"]
    expected["smalltest_dispatch"]["script"] = "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py"
    expected["smalltest_dispatch"]["also_needs"] = ["gcloud"]
    expected["smalltest_dispatch_dryrun"]["fixed_args"] = ["--i-am-steward", "--after-settled-1", "--dry-run"]
    expected["verification_job"]["needs"] = "gcloud"
    expected.update(json.loads(json.dumps(MEASURING_BINDINGS)))
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
    ("enabled", True), ("script", "platform/scripts/unreviewed.py"),
    ("fixed_args", ["--execute"]), ("allowed_args", ["unreviewed"]),
])
def test_table_pin_refuses_unreviewed_measuring_changes(kind, field, value):
    now = load_ops(OPS_FILE.read_text())
    assert_table_matches_pin(now)
    now["ops"][kind][field] = value
    with pytest.raises(AssertionError, match=re.escape(f"{kind}.{field}")):
        assert_table_matches_pin(now)


def test_k9_prebuilt_bindings_name_k9_23_and_remain_disabled():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for kind in K9_KINDS:
        assert ops[kind]["enabled_by"] == "K9-23"
        assert ops[kind]["script"] == "platform/python-sidecar/services/kala_core/publication.py", kind
        assert ops[kind]["enabled"] is False
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


# Exact Wave 4 safety-fix, #3607 (f847ba24d) measuring and J-1a lane additions, including the
# local_schema_seed scratch lifecycle (#3627) and the D-33 generated-overlay hand-off (#3672). Each hash is of the merged executor.py function; every
# other mutation, including weakening these functions, fails the boundary pin.
W4_FUNCTION_HASHES = {'fence_quiescent': 'd66b9b39b33b7718e19186bc7dec95f6f87a6ab55daa748a71149247f3e2d5a1', 'receipt': 'fe01726e959f02fe1d6d7bba32f72e573f06bb23f901de62334e9f6e1e28aff1', 'smalltest_policy': '7eeb58f3824919057e9a5845a816340981db7358ecace5ff130ac57f26efea58', 'smalltest_policy_problem': '5b0eba5031bde1fd947b380b210363d875a54e7c90a48fbff5231048faf3ccc7', 'validate': 'd07de5f9602ed84043d87f36ed89ceb0c5b535e372150919d2c0250132dea5d1', 'lane_selected': '16c586e33156c646f6411e46738929625f6e8d8533157fef16a9428fdb2f843d', 'lane_target_settings': 'aa4899d9eeea3ee66b6c85bdcd122108b2b67863009f9132ec750b12eb9a22a9', 'validate_lane': 'b1b3c09684a5b2833004e7f99d59aa5500962245b48cc8f42c2bea030afbb8d3', 'lane_qualification': 'bdfdb3a7f981c88dbbb79ebe4fca31745598a676a3ed330d655794786ff4ae50', 'lane_child_env': 'cb2e88d98cb481152a14b361f84403fd0861d771fb127bfeadd3df53f1ee9d34', 'execute_lane': 'd445545193c558f4d1acc522b7f616382a74998b04f4c941b0628e12a190642c', 'receipt_lane': 'c93ccb7e594b3080c2b8d78ee32e95e245217784a57ebb141088fc9e3ca53f05', 'execute': '5ed6d1cafe35bff8e83710ee563abad95a433be437ef7970655c7f2a1e7af779', 'main': '8bcabbe56032a38b747ab5a3e117cd3d68c130ee1a4153604a02fb84af6ee510', 'overlay_proofs': '3fe0d184de37b9f83a74d4db2544f1db75997e4a875602f8f3cd3974b14e1b53', 'apply_generated_overlay': 'effe0b423c3c0328c4b3da9e2694097c022125fc5cb81ff59420a6cf54cf19c3'}


# Exact K9-23 additions: a distinct verifier capability and one-connection injection (`execute` = main's reviewed function plus the K9-23 branch).
K9_FUNCTION_HASHES = {'capabilities': '5ebe1c302e6b797c2af0da3bb72b7a9aadca4b40663645396aab217a27b9b675', 'execute': '867c1e7c4e9a7659c9ab2cd691a791e986effb28c48435e708767ac51dce4617'}


def normalize_wave4(base_src, work_src):
    base_seg, work_seg = _segments(base_src), _segments(work_src)
    for name, digest in (W4_FUNCTION_HASHES | K9_FUNCTION_HASHES).items():
        segment = work_seg.get(name, "")
        if hashlib.sha256(segment.encode()).hexdigest() == digest:
            if name in base_seg:
                work_src = work_src.replace(segment, base_seg[name], 1)
            else:
                work_src = work_src.replace(segment + "\n\n\n", "", 1)
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
    ('APPROVAL_MAX_AGE_S = 3 * 3600', 'APPROVAL_MAX_AGE_S = 30 * 3600'),
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


@pytest.mark.parametrize("name", ["smalltest_policy", "smalltest_policy_problem"])
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
ALL_CAPS = {"layer_verifier": True, "builder": True, "owner": True, "pgenv": True, "gcloud": True, "none": True}


def _git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env={**os.environ, **GIT_ENV})
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


def test_validate_reads_the_real_table_through_the_selected_repository(tmp_path, monkeypatch):
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    assert str(w.mod.GIT) == str(w.repo)
    table = w.table()
    assert {k for k, e in table.items() if enabled_state(k, e)} == ENABLED_KINDS
    # positive controls: the enabled kinds are admitted for their requesters, so the refusals below are not vacuous
    assert w.mod.validate(simple_request("readback_sql", "v1", args={"sql_file": "a.sql"}), table, ALL_CAPS) is None
    assert w.mod.validate(simple_request("finalize", "sutradhara"), table, ALL_CAPS) is None


@pytest.mark.parametrize("kind", ["verification_job", "century_dispatch", "publish_head", "rollback_head",
                                  "measuring_dispatch", *K9_KINDS])
def test_request_for_a_disabled_kind_is_not_enabled(tmp_path, monkeypatch, kind):
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    why = w.mod.validate(w.production_request(kind), w.table(), ALL_CAPS)
    assert why is not None and "not enabled" in why, why


@pytest.mark.parametrize("kind", K9_KINDS)
def test_entry_enabled_in_a_copy_with_a_placeholder_script_is_refused(tmp_path, monkeypatch, kind):
    text = OPS_FILE.read_text()
    w = World(tmp_path, monkeypatch, copy_with(text, kind, script="TO_BE_SET_BY_FIXTURE"))
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
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot"), ts=old), table, ALL_CAPS) == "approval expired or not yet valid"
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
