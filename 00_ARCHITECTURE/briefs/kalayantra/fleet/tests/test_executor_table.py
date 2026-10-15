"""KV3-B-EXECUTOR-TABLE (relaunch plan v2.7 §2, §5, §6 EXECUTE, §14 B-1): the executor table and the executor's git handle.

What this proves, and what it deliberately does not touch:
  · the table: every `enabled_by` is a plan-model item; exactly four kinds are enabled; every field equals the table at the
    plan pin except the enumerated K9-23 / Wave 4 preparation edits and `_doc`; the five P10 entries are present and disabled; `enabled` is the first
    key of each entry; each of the five model detector patterns (read from the model, not retyped) misses the table and
    hits a copy with that one entry flipped;
  · the authority boundary: executor.py differs from the plan-pin revision in `GIT` and exact approved receipt/capability additions only, and the listed
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
PINNED_EXECUTOR_SHA256 = "8b9a164f52b307514d7b42f87019070689b1533f624b871a2e1d113408ebdcf7"
DEFAULT_SOURCE_REPO = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
SH_GIT_OLD = 'GIT="$KY_ROOT/wt/campaign"'
SH_GIT_NEW = 'GIT="${KY_SOURCE_REPO:-' + DEFAULT_SOURCE_REPO + '}"'
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"

ENABLED_KINDS = {"readback_sql", "migration_readback", "local_schema_seed", "finalize"}
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


def detector_pattern(item_id):
    det = model_items()[item_id]["detector"]
    assert det["type"] == "file_contains", f"{item_id}: detector is {det['type']}"
    assert det["path"].endswith("/" + OPS_REL), f"{item_id}: detector reads {det['path']}"
    return re.compile(det["pattern"])


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


def test_enabled_set_is_exactly_the_four_kinds():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    assert {k for k, e in ops.items() if enabled_state(k, e)} == ENABLED_KINDS


def test_enabled_is_the_first_key_of_every_entry():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for kind, entry in ops.items():
        assert next(iter(entry)) == "enabled", f"{kind}: first key is {next(iter(entry))}"


def test_p10_entries_present_and_disabled():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    for item, kind in P10.items():
        assert kind in ops, f"{kind} is missing"
        assert enabled_state(kind, ops[kind]) is False, f"{kind} must be disabled"
        assert ops[kind]["enabled_by"] == item


def test_table_equals_the_pin_except_reviewed_k9_and_w4_preparation_edits():
    base = load_ops(base_text(OPS_REL))
    now = load_ops(OPS_FILE.read_text())
    assert set(now) == set(base) and set(now["ops"]) == set(base["ops"]), "the set of kinds or top-level keys changed"
    assert list(now["ops"]) == list(base["ops"]), "the order of kinds changed"
    expected = json.loads(json.dumps(base["ops"]))
    for kind in K9_KINDS:
        assert expected[kind]["enabled_by"] == "K9-3", f"{kind}: the pin no longer says K9-3 — test premise broken"
        expected[kind]["enabled_by"] = "K9-23"
        assert "TO_BE_SET_BY_K9-3" in expected[kind]["script"]
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
    expected["measuring_dispatch"]["also_needs"] = ["gcloud"]
    expected["verification_job"]["needs"] = "gcloud"
    expected["measuring_dispatch"]["staging_dry_run"] = {
        "enabled": False, "needs": "builder", "script": "platform/scripts/dispatch_v5_small_test_job.py",
        "fixed_args": ["--i-am-steward", "--after-settled-1", "--dry-run", "--run", "all_classes_full", "--classes", "all"],
        "allowed_args": [], "scope": "staging rollback only; no remote launch attestation; child allocation and phase enablement required"}
    for kind, phase in [("measuring_dispatch", "J-3a"), ("century_dispatch", "J-4d"),
                        ("verification_job", "phase 10 after P06b"), ("publish_head", "J-6m"), ("rollback_head", "J-6r")]:
        expected[kind]["prepared_dry_run"] = {
            "enabled": False, "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/operation_dryrun.py",
            "fixed_args": ["--dry-run", "--kind", kind], "allowed_args": expected[kind]["allowed_args"], "enable_at": phase,
            "attestation": "PREPARATION_ONLY; dry_run_passed=false; allocate a real child before binding or enablement"}
    for kind, entry in now["ops"].items():
        assert set(entry) == set(expected[kind]), f"{kind}: key set changed"
        assert next(iter(entry)) == "enabled", f"{kind}: enabled must remain first"
        for key in entry:
            assert entry[key] == expected[kind][key], f"{kind}.{key}: {entry[key]!r} != {expected[kind][key]!r}"
    # the only top-level difference allowed is `_doc`
    assert {k: v for k, v in now.items() if k != "_doc"} == {k: v for k, v in base.items() if k != "_doc"} | {"ops": now["ops"]}


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
def test_model_detector_misses_the_table_and_hits_one_flipped_entry(item, kind):
    pattern = detector_pattern(item)
    text = OPS_FILE.read_text()
    assert not pattern.search(text), f"{item}'s detector already matches the table"
    flipped = flip(text, kind)
    assert pattern.search(flipped), f"{item}'s detector does not read the flipped {kind} entry"
    for other_item, other_kind in P10.items():
        if other_item != item:
            assert not detector_pattern(other_item).search(flipped), f"flipping {kind} also trips {other_item}"


def test_detector_state_unreadable_is_a_failure():
    # a table whose entry state the helper cannot read must fail, not pass
    with pytest.raises(AssertionError):
        enabled_state("x", {"enabled": "true"})
    with pytest.raises(AssertionError):
        enabled_state("x", {"needs": "none"})
    with pytest.raises(KeyError):
        detector_pattern("NO-SUCH-ITEM")


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


# Exact approved Wave 4 additions only. Any other mutation, including a changed
# admission gate or receipt parser, still fails the pinned boundary detector.
W4_FUNCTION_HASHES = {'receipt': '32faf16f6fc5600bb667b730c3792ebe7797df5c333e32b498c840263d0349cd', 'validate': '6a497e463815ff701c5ea67a8f20b009c32594d176d074167e88f631da5a4915'}


# Exact K9-23 additions: a distinct verifier capability and one-connection injection.
K9_FUNCTION_HASHES = {'capabilities': '5ebe1c302e6b797c2af0da3bb72b7a9aadca4b40663645396aab217a27b9b675', 'execute': '40eb38466820b546f985f223e520161fa8fee4c6c2f48fcd8d4c440965126648'}


def normalize_wave4(base_src, work_src):
    base_seg, work_seg = _segments(base_src), _segments(work_src)
    for name, digest in (W4_FUNCTION_HASHES | K9_FUNCTION_HASHES).items():
        segment = work_seg.get(name, "")
        if hashlib.sha256(segment.encode()).hexdigest() == digest:
            work_src = work_src.replace(segment, base_seg[name], 1)
    return work_src


def boundary_violations(base_src, work_src):
    """Why `work_src` is not the pinned executor.py plus a changed GIT assignment (empty list = boundary holds)."""
    work_src = normalize_wave4(base_src, work_src)
    problems = []
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
    """A copy of the table text with `kind` enabled and `fields` set — the only way an entry is ever enabled in these tests."""
    ops = json.loads(flip(text, kind))
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


@pytest.mark.parametrize("kind", ["smalltest_dispatch", "verification_job", "century_dispatch", "publish_head", "rollback_head",
                                  "measuring_dispatch", "layer_verify", "orchestrator_rebuild", "backup_snapshot"])
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
