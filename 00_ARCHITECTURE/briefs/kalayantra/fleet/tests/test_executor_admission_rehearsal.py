"""SW2 (PLAN_A10_1 §8; A10.1 addition 1): the admission rehearsal harness (fleet/admission_rehearsal.py) judges request templates with the REAL validators on an isolated fixture.

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8: a verdict comes from a detector that can read false). Every claim has
  · an oracle that passes on the real sources: the clean base template is ADMITTED and the single planted defect is REFUSED with the NAMED reason as the primary reason, and
  · ONE planted reversion of the validator that owns the claim, which makes the harness FLAG it (`VALIDATOR_ADMITS`): a validator that admits the bad case does not go unnoticed.
The fixture is a throwaway repository holding the repository's own executor.py, head_operation.py, executor_ops.json, readback_sql.sh and scoped-backup script (each reversion is a one-line
edit of the fixture's copy, anchor unique), a stand-in overlay generator (the real one needs the sidecar and an ephemeris; it runs in the report, not here) and a parent commit to stand for a stale pin.
  S1 isolation: nothing outside the sandbox is read or written; a sandbox in the live KY_ROOT, in the repository or in an unmarked non-empty folder is refused
  S2 the clean templates are ADMITTED (the base of every control), and a set rendered at an older pin shows `stale_pin` until it is repinned
  S3 stale pin refused                         reversion: the pin gate admits a pin that is not main
  S4 missing / unknown scope refused           reversion: the scope gate takes a request without a scope / a scope the script does not offer
  S5 absent overlay refused                    reversion: the executor's overlay step ignores a generator that exits non-zero
  S6 disabled kind refused                     reversion: the executor ignores `enabled`
  S7 missing completion refused                reversion: the executor's dry_run_check admits without a receipt / the head policy does not require the dry-run receipt
  S8 wrong reviewed_commit refused             reversion: the executor's merge-base test is dropped / the acceptance's reviewed_commit is not compared
  S9 sql_sha256 mismatch refused               reversion: readback_sql.sh does not compare the digest
  S10 requester not allowed refused            reversion: the executor ignores `requesters`
  S11 the completion publishers are wired      reversion: the executor's main loop stops calling publish_head_completions
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
sys.path.insert(0, str(FLEET))
import admission_rehearsal as ar  # noqa: E402

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
needs_driver = pytest.mark.skipif(not HAS_PSYCOPG, reason="readback_sql.sh imports psycopg before it checks the digest: the interpreter running the tests has none")
SCRIPTS = ("backup_v5_small_test_job.py", "v5_small_test_shared.py", "backup_v5_small_test_scope.json", "backup_v5_century_scope.json",
           "backup_v5_verification_seal_scope.json", "backup_v5_w5w6_union_scope.json")
GENERATOR = '''import hashlib, json, pathlib, sys
SIDECAR = pathlib.Path(__file__).resolve().parents[2]
OUTPUT = SIDECAR.parent / "src/generated/nirmana-writer-digests.json"
doc = {"writers": {"ka_gochara_v5": hashlib.sha256((SIDECAR / "writer.txt").read_bytes()).hexdigest()}}
text = json.dumps(doc, indent=2, sort_keys=True) + "\\n"
if "--check" in sys.argv:
    sys.exit(0 if OUTPUT.read_text() == text else 1)
OUTPUT.write_text(text)
'''
RUN_ID = "11111111-2222-4333-8444-555555555555"
CHART = ar.CANONICAL_CHART


def fixture_git(path, *args):
    p = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, env=ar.clean_env(), timeout=120)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def patched(text, edits):
    for old, new in edits:
        assert text.count(old) == 1, f"reversion anchor not unique: {old!r}"        # a bad anchor is never a failed oracle
        text = text.replace(old, new)
    return text


class Fixture:
    """A source repository whose `origin/main` is the second of two commits, with `patches` {repo-relative path: [(old, new)]} applied to the copied sources."""

    def __init__(self, tmp, patches=None, disable=("http_probe",)):
        patches = patches or {}
        self.repo = tmp / "src"
        self.repo.mkdir(parents=True)
        fixture_git(self.repo, "init", "-q", "-b", "main")
        files = {ar.EXEC_REL: (REPO / ar.EXEC_REL).read_text(), ar.HEAD_REL: (REPO / ar.HEAD_REL).read_text(), ar.READBACK_REL: (REPO / ar.READBACK_REL).read_text()}
        ops = json.loads((REPO / ar.OPS_REL).read_text())
        for kind in disable: ops["ops"][kind]["enabled"] = False       # the oracle for a disabled kind must not depend on which kinds the branch under test has enabled
        files[ar.OPS_REL] = json.dumps(ops, indent=1)
        for name in SCRIPTS: files[f"{ar.SCRIPTS_REL}/{name}"] = (REPO / ar.SCRIPTS_REL / name).read_text()
        files[ar.SIDECAR_REL + "/writer.txt"] = "writer v1\n"
        files[ar.SIDECAR_REL + "/pipeline/__init__.py"] = ""
        files[ar.SIDECAR_REL + "/pipeline/orchestrator/__init__.py"] = ""
        files[ar.OVERLAY_MODULE_REL] = GENERATOR
        files[ar.GENERATED_REL + "/nirmana-writer-digests.json"] = "{}\n"
        files[ar.SIDECAR_REL + "/services/kala_core/publication_admission.py"] = "# the rebuild kinds' script (a pin target; never run here)\n"
        for rel, edits in patches.items(): files[rel] = patched(files[rel], edits)
        for rel, text in files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text)
        fixture_git(self.repo, "add", "-A")
        fixture_git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        self.base = fixture_git(self.repo, "rev-parse", "HEAD")
        (self.repo / "CHANGELOG.txt").write_text("a later main\n")
        fixture_git(self.repo, "add", "-A")
        fixture_git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "main moves")
        self.main = fixture_git(self.repo, "rev-parse", "HEAD")
        fixture_git(self.repo, "update-ref", "refs/remotes/origin/main", self.main)
        self.tmp = tmp
        self.staged = tmp / "staged"
        self.sql = tmp / "sql"
        self.write_templates()

    def write_templates(self):
        """Templates shaped like the pre-stage set (tokens, source_binding), staged at the OLD pin so an unrepinned run shows `stale_pin`."""
        self.staged.mkdir()
        self.sql.mkdir()
        (self.sql / "w6-j6-state.sql.tpl").write_text("SELECT 1 AS one\n")
        pin = self.base
        common = {"requested_by": "adhikarin", "reviewed_commit": pin, "kyd": "REHEARSAL"}
        sb = lambda: {"reviewed_commit": pin, "script_sha256": "0" * 64}
        prod = {"chart_id": CHART, "lease_id": "@FIRE:lease_id@", "expires_at": "@FIRE:expires_at@"}
        T = {
            "A-readback": dict(common, kind="readback_sql", item_id="J-6", operation_id="rh.state", idempotency_key="rh.state", args={"sql_file": "run/ops/sql/w6-j6-state.sql", "sql-sha256": "@RENDER:sql@"},
                               sql_sha256="@RENDER:sql@", source_binding=sb()),
            "B-image": dict(common, kind="cloudrun_job_readback", item_id="K9-4a", operation_id="rh.image", idempotency_key="rh.image", args={}),
            "C-rebuild-dryrun": dict(common, kind="orchestrator_rebuild_dryrun", item_id="K9-4a", operation_id="rh.rebuild-dry", idempotency_key="rh.rebuild-dry", chart_id=CHART,
                                     args={"assets": "ka_a,ka_b", "run-id": RUN_ID}, source_binding=sb()),
            "D-rebuild": dict(common, kind="orchestrator_rebuild", item_id="K9-4a", operation_id="rh.rebuild", idempotency_key="rh.rebuild", args={"assets": "ka_a,ka_b", "run-id": RUN_ID},
                              dryrun_receipt="@FIRE:accepted_dryrun_receipt@", source_binding=sb(), **prod),
            "E-publish-dryrun": dict(common, kind="publish_head_dryrun", item_id="J-6", operation_id="rh.publish-dry", idempotency_key="rh.publish-dry", chart_id=CHART,
                                     args={"expected-head-sha256": "@SEAL:expected_head_sha256@", "generation": "5.0", "manifest-id": "@SEAL:manifest_id@"},
                                     decision_event_sha256="@SEAL:decision_event_sha256@", head_change="@SEAL:head_change@", preflight_receipt="@FIRE:preflight_receipt@"),
            "F-publish": dict(common, kind="publish_head", item_id="J-6", operation_id="rh.publish", idempotency_key="rh.publish",
                              args={"expected-head-sha256": "@SEAL:expected_head_sha256@", "generation": "5.0", "manifest-id": "@SEAL:manifest_id@"},
                              decision_event_sha256="@SEAL:decision_event_sha256@", head_change="@SEAL:head_change@", preflight_receipt="@FIRE:preflight_receipt@",
                              dry_run_receipt="@FIRE:dry_run_receipt@", scope_hash_receipts="@FIRE:scope_hash_receipts@", backup_label="@FIRE:backup_label@",
                              backup_capture_sha256="@FIRE:backup_capture_sha256@", **prod),
            "G-backup": dict(common, kind="backup_snapshot", item_id="J-6", operation_id="rh.backup", idempotency_key="rh.backup", args={"label": "@FIRE:backup_label@", "scope": ar.WINDOW_SCOPE}, **prod),
            "H-probe": dict(common, kind="http_probe", item_id="J-6", operation_id="rh.probe", idempotency_key="rh.probe", args={"probe": "mcp_health"}),
        }
        for name, t in T.items(): (self.staged / f"{name}.json").write_text(json.dumps(t, indent=1))

    def rehearsal(self, sub="sb", **kw):
        kw.setdefault("python", sys.executable)
        return ar.Rehearsal(self.tmp / sub, self.repo, self.main, **kw)


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


def run_control(fx, name, patches=None, sub="sb", **kw):
    """The named control on a fixture whose sources carry `patches`; returns the control row."""
    f = fx if patches is None else Fixture(fx.tmp / "rev", patches)
    ar.OVERLAY_CACHE.clear()
    ar.SCRIPT_CACHE.clear()
    rows = f.rehearsal(sub, **kw).controls(f.staged, f.sql, repin=True, only={name})
    assert len(rows) == 1, rows
    return rows[0]


def assert_refused(row, code):
    assert row["status"] == "REFUSED" and row["ok"] is True and row["code"] == code, row
    assert row["base_admitted"] is True, row


def assert_flagged(row, status="VALIDATOR_ADMITS"):
    """The reverted validator no longer refuses by itself: either nothing refuses (`VALIDATOR_ADMITS`) or another gate catches it for a different reason (`WRONG_REASON`, executor_alone ADMITTED)."""
    assert row["status"] == status and row["ok"] is False, row
    assert ar.flags({"controls": [row], "wiring": []}), "a validator that admits the planted defect must raise a flag"


# ---- S1 isolation ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s1_the_sandbox_is_refused_where_it_could_touch_live_state(fx, tmp_path):
    for bad in (ar.LIVE_KY_ROOT / "run" / "ops" / "rehearsal-sandbox", REPO / "rehearsal-sandbox", fx.repo / "inside"):
        with pytest.raises(ar.Refused):
            ar.Rehearsal(bad, fx.repo, fx.main, python=sys.executable)
        assert not bad.exists(), f"refusal must precede any write: {bad}"
    stranger = tmp_path / "a-folder-with-work-in-it"
    stranger.mkdir()
    (stranger / "work.txt").write_text("keep me\n")
    with pytest.raises(ar.Refused, match="not a rehearsal sandbox"):
        ar.Rehearsal(stranger, fx.repo, fx.main, python=sys.executable)
    assert (stranger / "work.txt").read_text() == "keep me\n"


def test_s1_every_executor_path_and_the_git_handle_are_inside_the_sandbox(fx):
    rh = fx.rehearsal()
    rh.assert_isolated()
    for name in ("KY_ROOT", "OPS", "REQ", "REC", "DONE", "ACC", "INFLIGHT", "FENCE", "SEEN", "PACK_ALLOWLIST"):
        assert ar.inside(Path(getattr(rh.ex, name)), rh.sandbox) and not ar.inside(Path(getattr(rh.ex, name)), ar.LIVE_KY_ROOT), name
    assert Path(rh.ex.GIT).resolve() == rh.git_dir.resolve()
    assert rh.executor_sha256 == ar.sha256((REPO / ar.EXEC_REL).read_bytes()), "the executor judged is main's own bytes"


# ---- S2 clean templates admitted; a stale set shows its pins --------------------------------------------------------------------------------------------------------------------------
def test_s2_the_clean_templates_are_admitted_and_an_old_pin_is_visible_until_repinned(fx):
    ar.OVERLAY_CACHE.clear()
    stale = fx.rehearsal("stale").run_set(fx.staged, fx.sql, repin=False)
    assert {r["template"]: r["verdict"]["code"] for r in stale}["A-readback.json"] == "stale_pin"
    assert not any(r["verdict"]["admitted"] for r in stale), "every template was staged at the old pin"
    rows = {r["template"]: r["verdict"] for r in fx.rehearsal("fresh").run_set(fx.staged, fx.sql, repin=True)}
    assert {k: v["code"] for k, v in rows.items() if not v["admitted"]} == {"H-probe.json": "kind_disabled"}, rows      # only the kind main has disabled; the dry runs, writes and abort-free chain are admitted
    assert rows["F-publish.json"]["admitted"] and rows["D-rebuild.json"]["admitted"] and rows["G-backup.json"]["admitted"], rows


# ---- S3 stale pin ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s3_a_pin_older_than_main_is_refused_although_the_executor_alone_admits_it(fx):
    row = run_control(fx, "stale_pin")
    assert_refused(row, "stale_pin")
    assert row["executor_alone"] == "ADMITTED", "the executor admits any ancestor of main: the pin gate is what refuses (documented in the report)"


def test_s3_reversion_a_pin_gate_that_admits_a_stale_pin_is_flagged(fx, monkeypatch):
    monkeypatch.setattr(ar.Rehearsal, "pin_problem", lambda self, req: None)
    assert_flagged(run_control(fx, "stale_pin"))


# ---- S4 scope -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s4_a_backup_without_its_scope_and_one_with_a_scope_the_script_does_not_offer_are_refused(fx):
    assert_refused(run_control(fx, "scope_missing"), "scope_missing")
    assert_refused(run_control(fx, "scope_unknown", sub="sb2"), "scope_unknown")


def test_s4_reversion_a_scope_gate_that_takes_a_request_without_a_scope_is_flagged(fx, monkeypatch):
    original = ar.Rehearsal.scope_problem
    monkeypatch.setattr(ar.Rehearsal, "scope_problem", lambda self, req: None if not (req.get("args") or {}).get("scope") else original(self, req))
    assert_flagged(run_control(fx, "scope_missing"))


def test_s4_reversion_a_scope_gate_that_takes_a_scope_the_script_does_not_offer_is_flagged(fx, monkeypatch):
    original = ar.Rehearsal.scope_problem
    monkeypatch.setattr(ar.Rehearsal, "scope_problem", lambda self, req: None if str((req.get("args") or {}).get("scope", "")).endswith("_typo") else original(self, req))
    assert_flagged(run_control(fx, "scope_unknown"))


# ---- S5 overlay -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s5_a_production_tree_without_a_buildable_overlay_is_refused(fx):
    assert_refused(run_control(fx, "overlay_absent"), "overlay_absent")


def test_s5_reversion_an_executor_that_ignores_a_failing_overlay_generator_is_flagged(fx):
    assert_flagged(run_control(fx, "overlay_absent", patches={ar.EXEC_REL: [("            if p.returncode: return None, f\"writer-digest {step} exited", "            if False: return None, f\"writer-digest {step} exited")]}))


# ---- S6 disabled kind -----------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s6_a_kind_main_has_disabled_is_refused_and_is_admitted_once_enabled(fx):
    assert_refused(run_control(fx, "kind_disabled"), "kind_disabled")


def test_s6_reversion_an_executor_that_ignores_enabled_is_flagged(fx):
    assert_flagged(run_control(fx, "kind_disabled", patches={ar.EXEC_REL: [("    if not op.get(\"enabled\"): return f\"kind {req['kind']} is not enabled", "    if False: return f\"kind {req['kind']} is not enabled")]}))


# ---- S7 completion --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s7_a_production_write_without_the_completion_of_its_dry_run_is_refused(fx):
    assert_refused(run_control(fx, "completion_missing_rebuild"), "completion_missing")
    assert_refused(run_control(fx, "completion_missing_flip", sub="sb2"), "completion_missing")


def test_s7_reversion_an_executor_that_admits_a_rebuild_without_its_dry_run_receipt_is_flagged(fx):
    assert_flagged(run_control(fx, "completion_missing_rebuild", patches={ar.EXEC_REL: [("    if kind in NO_DRYRUN_KINDS: return None, None", "    if True: return None, None")]}))


def test_s7_reversion_a_head_policy_that_does_not_require_the_dry_run_receipt_is_flagged(fx):
    assert_flagged(run_control(fx, "completion_missing_flip", patches={ar.HEAD_REL: [("        if not req['kind'].endswith('_dryrun'):\n            if not req.get('dry_run_receipt'):", "        if False:\n            if not req.get('dry_run_receipt'):")]}))


# ---- S8 reviewed_commit ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s8_a_reviewed_commit_main_does_not_contain_and_an_acceptance_for_another_commit_are_refused(fx):
    assert_refused(run_control(fx, "reviewed_commit_not_on_main"), "reviewed_commit_not_on_main")
    assert_refused(run_control(fx, "reviewed_commit_mismatch", sub="sb2"), "reviewed_commit_mismatch")


def test_s8_reversion_an_executor_that_drops_the_merge_test_of_a_dry_run_is_flagged(fx):
    anchor = ("        if not SHA.match(rc): return \"reviewed_commit required for a dry-run operation\"\n"
              "        if git(\"merge-base\", \"--is-ancestor\", rc, \"origin/main\").returncode != 0: return \"reviewed_commit is not merged to main\"")
    row = run_control(fx, "reviewed_commit_not_on_main", patches={ar.EXEC_REL: [(anchor, anchor.split("\n")[0])]})
    assert row["executor_alone"] == "ADMITTED", "the executor, reverted, admits a commit main does not contain"
    assert_flagged(row, "WRONG_REASON")      # only the pin gate still stops it, and for another reason: the harness says so


def test_s8_reversion_an_executor_that_does_not_compare_the_acceptances_commit_is_flagged(fx):
    assert_flagged(run_control(fx, "reviewed_commit_mismatch", patches={ar.EXEC_REL: [("    if a.get(\"reviewed_commit\") != rc: return \"the acceptance receipt names a different reviewed_commit\"\n", "")]}))


# ---- S9 sql digest --------------------------------------------------------------------------------------------------------------------------------------------------------------------
@needs_driver
def test_s9_a_readback_citing_the_wrong_sql_digest_is_refused_by_the_script_itself(fx):
    row = run_control(fx, "sql_sha256_mismatch")
    assert_refused(row, "sql_sha256_mismatch")
    assert row["executor_alone"] == "ADMITTED", "the executor never reads the SQL file: main's readback script is the detector"


@needs_driver
def test_s9_reversion_a_readback_script_that_does_not_compare_the_digest_is_flagged(fx):
    assert_flagged(run_control(fx, "sql_sha256_mismatch", patches={ar.READBACK_REL: [("    if expected_digest and hashlib.sha256(sql_bytes).hexdigest() != expected_digest:", "    if False:")]}))


# ---- S10 requester --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s10_a_lane_the_kind_does_not_list_is_refused(fx):
    assert_refused(run_control(fx, "requester_not_allowed"), "requester_not_allowed")


def test_s10_reversion_an_executor_that_ignores_requesters_is_flagged(fx):
    assert_flagged(run_control(fx, "requester_not_allowed", patches={ar.EXEC_REL: [("    if req[\"requested_by\"] not in op.get(\"requesters\", [\"adhikarin\"]): return f\"requested_by", "    if False: return f\"requested_by")]}))


# ---- S11 completion publishers ------------------------------------------------------------------------------------------------------------------------------------------------------
def test_s11_the_completion_publishers_are_defined_and_called_from_the_main_loop(fx):
    assert fx.rehearsal().wiring() == [{"publisher": p, "defined": True, "called_from_main": True, "ok": True} for p in ar.COMPLETION_PUBLISHERS]


def test_s11_reversion_an_executor_that_stops_calling_the_head_publisher_is_flagged(fx):
    f = Fixture(fx.tmp / "rev", {ar.EXEC_REL: [("        publish_head_completions()            # M-W56-16", "        pass            # M-W56-16")]})
    report = {"controls": [], "wiring": f.rehearsal().wiring()}
    assert [w["ok"] for w in report["wiring"]] == [False, True]
    assert ar.flags(report) == ["completion publisher publish_head_completions: defined=True called_from_main=False"]


# ---- the report -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_the_command_line_exits_1_with_a_flag_when_a_validator_admits_the_defect(fx, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ar.Rehearsal, "pin_problem", lambda self, req: None)
    ar.OVERLAY_CACHE.clear()
    rc = ar.main(["--sandbox", str(tmp_path / "cli"), "--staged", str(fx.staged), "--sql", str(fx.sql), "--repo", str(fx.repo), "--main-ref", fx.main, "--python", sys.executable,
                  "--out", str(tmp_path / "out")])
    report = json.loads((tmp_path / "out" / "REHEARSAL.json").read_text())
    assert rc == 1 and any(f.startswith("stale_pin: VALIDATOR_ADMITS") for f in report["flags"]), report["flags"]
    assert "VALIDATOR_ADMITS" in (tmp_path / "out" / "REHEARSAL.md").read_text()
