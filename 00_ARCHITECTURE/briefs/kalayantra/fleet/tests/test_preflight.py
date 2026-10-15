"""KV3-B-PREFLIGHT: preflight.sh v3 (plan v2.7 §5 "Preflight v3", §14 B-1/B-2; KU-01 `preflight-v3`).

Hermetic. A temporary KY_ROOT, KY_RUN, KY_FLEET and campaign checkout hold fakes for `ky`, `local_db.sh`,
`kyqualify.py`, `claude`, `curl`, `npm` and the campaign venv's python; no tracker, docker, model, database or network
is ever reached, nothing is written under /Users/Dev/kalayantra, and the real launchctl is never called. Each fake
appends to one call log, so a test can show exactly what preflight asked for and in what order.

Every check is shown to flip: each one fails alone (exit 1, `FAIL <name>`, no receipt, an earlier receipt gone) while
the other checks still report ok (root CLAUDE.md §N.8: a signal nothing could turn false is null).
"""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
PREFLIGHT = FLEET / "preflight.sh"
LAUNCH_CHECKS = ["secrets", "claude", "smoke", "dependencies", "tracker", "audit", "slots"]
SESSION_GRAMMAR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
SECRET_VALUE = "s3cr3t-value-DO-NOT-PRINT"
ROLES = {"bootstrap-builder": "claude-opus-5-5", "surrogate": "claude-opus-5-5"}
PINNED = {"sepl_18.se1": b"planets", "semo_18.se1": b"moon", "seas_18.se1": b"asteroids"}
SEED_FILES = {"schema_sha256": "prod_schema.sql", "ledger_sha256": "migrations_applied_data.sql",
              "registry_sha256": "asset_registry_data.sql"}
FINDINGS = [("CLAIM_NO_VERDICT", "claim:12"), ("VERDICT_ORPHAN", "verdict:7")]
AUDIT_OUT = ("audit since kickoff\n"
             "FAIL CLAIM_NO_VERDICT claim:12: claim has no verdict\n"
             "FAIL VERDICT_ORPHAN verdict:7: verdict names no claim\n"
             "AUDIT FAIL: 2 findings\n")


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else Path(data).read_bytes()).hexdigest()


def write_exec(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


FAKE_KY = """#!/bin/bash
echo "ky KY_STREAM=${KY_STREAM-} $*" >> "$CALL_LOG"
echo "receipt_present=$([ -e "$KY_RUN/LAUNCH_RECEIPT.json" ] && echo yes || echo no)" >> "$CALL_LOG"
[ -f "$CTL/audit_stdout" ] && cat "$CTL/audit_stdout"
exit "$(cat "$CTL/audit_exit" 2>/dev/null || echo 0)"
"""

FAKE_LOCAL_DB = """#!/bin/bash
echo "local_db $*" >> "$CALL_LOG"
echo "receipt_present=$([ -e "$KY_RUN/LAUNCH_RECEIPT.json" ] && echo yes || echo no)" >> "$CALL_LOG"
cmd="$1"; shift
fail="$(cat "$CTL/localdb_fail" 2>/dev/null)"
[ "$fail" = "$cmd" ] && { echo "boom $cmd" >&2; exit 1; }
[ "$fail" = "hang_$cmd" ] && sleep 30
h() { cat "$CTL/seed_$1"; }   # hashes of the seed files, taken once by the rig (spawning shasum per test is slow)
case "$cmd" in
  slots) if [ -f "$CTL/slots" ]; then cat "$CTL/slots"; else printf 'b1\\nb2\\nv1\\n'; fi
         exit "$(cat "$CTL/slots_exit" 2>/dev/null || echo 0)" ;;
  up) exit 0 ;;
  db) slot="$1"; sess="$3"; mkdir -p "$KY_RUN/local_db"
      result="$(cat "$CTL/db_result" 2>/dev/null || echo READY)"
      rsess="$(cat "$CTL/db_session" 2>/dev/null || echo "$sess")"
      s="$(cat "$CTL/db_seed_schema" 2>/dev/null || h schema)"
      printf '{"schema":"ky.slot_db/1","slot":"%s","database":"ky_%s","result":"%s","session_id":"%s","seed":{"schema_sha256":"%s","ledger_sha256":"%s","registry_sha256":"%s"}}\\n' \\
        "$slot" "$slot" "$result" "$rsess" "$s" "$(h ledger)" "$(h registry)" > "$KY_RUN/local_db/$slot.json"
      exit 0 ;;
  check) exit 0 ;;
  close) [ -f "$CTL/close_keep" ] || rm -f "$KY_RUN"/local_db/*.json
         echo "close session=$2 dropped=1 container=removed"
         exit "$(cat "$CTL/close_exit" 2>/dev/null || echo 0)" ;;
esac
exit 64
"""

FAKE_KYQUALIFY = """import json, os, sys
open(os.environ["CALL_LOG"], "a").write("kyqualify " + " ".join(sys.argv[1:]) + "\\n")
ctl = os.environ["CTL"]
bad = open(ctl + "/qual_fail").read().split() if os.path.exists(ctl + "/qual_fail") else []
cfg = sys.argv[sys.argv.index("--config") + 1]
sys.exit(1 if json.load(open(cfg))["role"] in bad else 0)
"""

FAKE_CLAUDE = """#!/bin/bash
echo "claude $*" >> "$CALL_LOG"
echo "receipt_present=$([ -e "$KY_RUN/LAUNCH_RECEIPT.json" ] && echo yes || echo no)" >> "$CALL_LOG"
[ -f "$CTL/claude_hang" ] && sleep 30
[ -f "$CTL/claude_exit" ] && exit "$(cat "$CTL/claude_exit")"
if [ -f "$CTL/claude_version" ]; then cat "$CTL/claude_version"; else echo "2.1.296 (Claude Code)"; fi
"""

FAKE_CURL = """#!/bin/bash
echo "curl $*" >> "$CALL_LOG"
out=""; prev=""
for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done
case "$*" in
  */api/health*) [ -f "$CTL/curl_exit" ] && exit "$(cat "$CTL/curl_exit")"
                 cat "$CTL/health.json"; exit 0 ;;
esac
[ -n "$out" ] || exit 22
src="$CTL/download/$(basename "$out" | sed -e 's/^\\.//' -e 's/\\.tmp.*$//')"
[ -f "$src" ] || exit 22
cp "$src" "$out"
"""

FAKE_NPM = """#!/bin/bash
echo "npm $* (cwd=$PWD)" >> "$CALL_LOG"
[ "$1" = ci ] && mkdir -p node_modules
exit 0
"""

FAKE_VENV_PYTHON = """#!/bin/bash
echo "venv_python $*" >> "$CALL_LOG"
[ "$*" = "-c import pytest, psycopg, swisseph" ] || exit 3
exit "$(cat "$CTL/venv_exit" 2>/dev/null || echo 0)"
"""


class Rig:
    """A complete, passing launch environment under tmp_path; tests break one thing at a time."""

    def __init__(self, tmp_path, base=None):
        """base: a prebuilt tree to copy (building the git fixture per test is slow); None builds from scratch."""
        t = self.tmp = tmp_path if base is None else tmp_path / "w"
        assert not str(t).startswith("/Users/Dev/kalayantra"), "the test rig must never sit in the live root"
        if base is not None:
            shutil.copytree(base, t, symlinks=True)
        self.root, self.src = t / "kyroot", t / "campaign"
        self.run, self.fleet = self.root / "run", self.root / "fleet_live"
        self.ephe, self.scratch = self.root / "ephe", t / "scratch"
        self.ctl, self.bin, self.log = t / "ctl", t / "fakebin", t / "calls.log"
        self.receipt = self.run / "LAUNCH_RECEIPT.json"
        self.recon, self.review = self.run / "AUDIT_RECONCILIATION.json", self.run / "AUDIT_RECONCILIATION.review.json"
        if base is None:
            for d in (self.run / "QUALIFICATIONS", self.run / "schema", self.ephe, self.scratch, self.ctl,
                      self.ctl / "download", t / "tmp"):
                d.mkdir(parents=True, exist_ok=True)
            self.log.write_text("")
            write_exec(self.root / "bin" / "ky", FAKE_KY)
            write_exec(self.fleet / "local_db.sh", FAKE_LOCAL_DB)
            (self.fleet / "kyqualify.py").write_text(FAKE_KYQUALIFY)
            write_exec(self.bin / "claude", FAKE_CLAUDE)
            write_exec(self.bin / "curl", FAKE_CURL)
            write_exec(self.bin / "npm", FAKE_NPM)
            write_exec(self.root / "venv" / "bin" / "python", FAKE_VENV_PYTHON)
            for role, model in ROLES.items():
                (self.fleet / "templates").mkdir(parents=True, exist_ok=True)
                (self.fleet / "templates" / f"LAUNCH_CONFIG.{role}.json").write_text(json.dumps({"role": role, "model": model}))
                (self.run / "QUALIFICATIONS" / f"{role}-{model}.json").write_text(json.dumps({"verdict": "PASS", "role": role}))
            for name in SEED_FILES.values():
                (self.run / "schema" / name).write_text(f"-- {name}\nselect 1;\n")
            for name, body in PINNED.items():
                (self.ephe / name).write_bytes(body)
                (self.ctl / "download" / name).write_bytes(body)
            side = self.src / "platform/python-sidecar/services/gochara_kernel"
            side.mkdir(parents=True)
            (side / "ephemeris_pins.py").write_text(
                "PINNED_SE1_SHA256: dict[str, str] = {\n" + "".join(f'    "{n}": "{sha(b)}",\n' for n, b in PINNED.items()) + "}\n")
            (self.src / "platform/node_modules").mkdir()
            (self.src / "platform-mcp/node_modules").mkdir(parents=True)
            (self.src / "00_ARCHITECTURE/control/kalayantra").mkdir(parents=True)
            (self.src / "00_ARCHITECTURE/control/kalayantra/plan_model.json").write_text('{"model": 1}')
            self.git("init", "-q")
            self.git("add", "-A")
            self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "fixture")
            (self.ctl / "health.json").write_text('{"ok": true}')
            for key, fname in (("schema", "prod_schema.sql"), ("ledger", "migrations_applied_data.sql"), ("registry", "asset_registry_data.sql")):
                (self.ctl / f"seed_{key}").write_text(sha(self.run / "schema" / fname))
        self.env = {"PATH": f"{self.bin}:/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(t), "TMPDIR": str(t / "tmp"),
                    "KY_ROOT": str(self.root), "KY_RUN": str(self.run), "KY_FLEET": str(self.fleet),
                    "KY_SCRATCH": str(self.scratch), "KY_SOURCE_REPO": str(self.src), "SE_EPHE_PATH": str(self.ephe),
                    "CLAUDE_BIN": str(self.bin / "claude"), "KY_CURL": str(self.bin / "curl"),
                    "PRAVAHA_URL": "http://127.0.0.1:8767", "CTL": str(self.ctl), "CALL_LOG": str(self.log),
                    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.src), *args], check=True, capture_output=True, text=True).stdout.strip()

    def ctl_set(self, name, text):
        (self.ctl / name).write_text(text)

    def set_audit(self, stdout, code):
        self.ctl_set("audit_stdout", stdout)
        self.ctl_set("audit_exit", str(code))

    def write_recon(self, pairs=FINDINGS, disposition="superseded by the install", authority="D-RETIRE-3", **raw):
        rec = {"schema": "ky.audit_reconciliation/1",
               "entries": [{"code": c, "ref": r, "disposition": disposition, "authority": authority} for c, r in pairs]}
        rec.update(raw)
        self.recon.write_text(json.dumps(rec, indent=1))
        return sha(self.recon)

    def write_review(self, digest, **over):
        rev = {"verdict": "ACCEPTED", "inputs": digest, "reviewer_session_id": "REV-1", "author_session_id": "PLAN-1"}
        rev.update(over)
        self.review.write_text(json.dumps(rev, indent=1))

    def accept_reconciliation(self, pairs=FINDINGS):
        self.set_audit(AUDIT_OUT, 1)
        self.write_review(self.write_recon(pairs))

    def run_pf(self, *args, extra_env=None, drop=()):
        env = {k: v for k, v in self.env.items() if k not in drop}
        env.update(extra_env or {})
        return subprocess.run(["bash", str(PREFLIGHT), *args], env=env, capture_output=True, text=True,
                              timeout=120, cwd=str(self.tmp))

    def launch(self, **kw):
        return self.run_pf("launch", **kw)

    def calls(self, prefix=None):
        lines = [x for x in self.log.read_text().splitlines() if not x.startswith("receipt_present=")]
        return [x for x in lines if prefix is None or x.startswith(prefix)]

    def receipt_json(self):
        return json.loads(self.receipt.read_text())


@pytest.fixture(scope="session")
def base_tree(tmp_path_factory):
    return Rig(tmp_path_factory.mktemp("base")).tmp


@pytest.fixture
def rig(tmp_path, base_tree):
    return Rig(tmp_path, base_tree)


def check_lines(out):
    found = []
    for line in out.splitlines():
        m = re.match(r"^(ok|FAIL) ([a-z]+)(?:: (.*))?$", line)
        if m:
            found.append((m.group(1), m.group(2), m.group(3)))
    return found


def statuses(res):
    return {name: status for status, name, _ in check_lines(res.stdout)}


def assert_fails_alone(rig, res, name, stale=True):
    assert res.returncode == 1, (res.stdout, res.stderr)
    st = statuses(res)
    assert st.get(name) == "FAIL", res.stdout
    assert [n for _, n, _ in check_lines(res.stdout)] == LAUNCH_CHECKS, res.stdout
    assert {n: s for n, s in st.items() if n != name} == {n: "ok" for n in LAUNCH_CHECKS if n != name}, res.stdout
    assert not rig.receipt.exists()
    assert not list(rig.run.glob(".LAUNCH_RECEIPT*")), "no partial receipt may remain"
    assert SECRET_VALUE not in res.stdout + res.stderr


# ── the whole path ───────────────────────────────────────────────────────────────────────────────────────────────

def test_all_ok_exit_0_and_receipt(rig):
    rig.receipt.write_text("stale")
    res = rig.launch()
    assert res.returncode == 0, (res.stdout, res.stderr)
    assert [(s, n) for s, n, _ in check_lines(res.stdout)] == [("ok", n) for n in LAUNCH_CHECKS], res.stdout
    text = rig.receipt.read_text()
    assert text.startswith('{\n "schema": "ky.launch_receipt/3"'), "JSON indent 1"
    assert '"mode": "launch"' in text
    r = json.loads(text)
    assert r["schema"] == "ky.launch_receipt/3" and r["mode"] == "launch"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", r["ts"])
    assert r["checks"] == [f"ok:{n}" for n in LAUNCH_CHECKS]
    assert r["slots"] == ["b1", "b2", "v1"]
    proof = r["slot_proof"]
    assert proof["slot"] == "b1" and proof["closed"] is True and SESSION_GRAMMAR.fullmatch(proof["session"])
    assert proof["seed"] == {k: sha(rig.run / "schema" / v) for k, v in SEED_FILES.items()}
    assert r["claude"] == {"path": str(rig.bin / "claude"), "version": "2.1.296", "sha256": sha(rig.bin / "claude")}
    quals = sorted(r["qualifications"], key=lambda q: q["role"])
    assert [(q["role"], q["model"]) for q in quals] == sorted(ROLES.items())
    for q in quals:
        assert q["receipt_sha256"] == sha(rig.run / "QUALIFICATIONS" / f"{q['role']}-{q['model']}.json")
        assert q["config_sha256"] == sha(rig.fleet / "templates" / f"LAUNCH_CONFIG.{q['role']}.json")
    assert r["audit"] == {"exit": 0, "findings": [], "reconciliation_sha256": None, "review_sha256": None}
    assert r["campaign_head"] == rig.git("rev-parse", "HEAD")
    assert r["model_sha256"] == sha(rig.src / "00_ARCHITECTURE/control/kalayantra/plan_model.json")
    assert r["preflight_sha256"] == sha(PREFLIGHT)
    assert not list(rig.run.glob(".LAUNCH_RECEIPT*"))


def test_local_db_log_is_exactly_the_slot_proof_for_one_slot_and_session(rig):
    assert rig.launch().returncode == 0
    calls = rig.calls("local_db ")
    session = calls[1].split()[-1]
    assert SESSION_GRAMMAR.fullmatch(session) and ":" not in session and session.startswith("PREFLIGHT-")
    assert calls == ["local_db slots", f"local_db up --session {session}", f"local_db db b1 --session {session}",
                     "local_db check b1", f"local_db close --session {session}"]
    assert rig.receipt_json()["slot_proof"]["session"] == session


def test_claude_smoke_is_the_version_check_and_the_qualification_check_only(rig):
    assert rig.launch().returncode == 0
    assert rig.calls("claude ") == ["claude --version"]
    qcalls = sorted(rig.calls("kyqualify "))
    assert qcalls == sorted(
        f"kyqualify check {rig.run}/QUALIFICATIONS/{role}-{model}.json --config {rig.fleet}/templates/LAUNCH_CONFIG.{role}.json"
        f" --require-context launchd --verify-evidence" for role, model in ROLES.items())
    assert rig.calls("ky KY_STREAM") == ["ky KY_STREAM=S audit --since kickoff"]
    assert not [c for c in rig.calls() if "kalayantra_fleet.sh" in c or c.endswith(" smoke")], "no fleet smoke"


def test_receipt_removed_before_the_first_check_runs(rig):
    rig.receipt.write_text("stale")
    assert rig.launch().returncode == 0
    seen = [x for x in rig.log.read_text().splitlines() if x.startswith("receipt_present=")]
    assert seen and set(seen) == {"receipt_present=no"}


def test_stale_receipt_is_removed_when_the_first_check_fails(rig):
    rig.receipt.write_text("stale")
    res = rig.launch(extra_env={"PGPASSWORD": SECRET_VALUE})
    assert res.returncode == 1 and not rig.receipt.exists()


def test_preflight_never_writes_the_reconciliation_or_its_review(rig):
    rig.accept_reconciliation()
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (rig.recon, rig.review)}
    assert rig.launch().returncode == 0
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before} == before


def test_no_old_topology_or_direct_database_calls_in_the_script():
    text = PREFLIGHT.read_text().lower()
    for banned in ("kalayantra_fleet.sh", "/wt/", "docker", "psql"):
        assert banned not in text, banned
    assert "python3" in text


# ── usage ────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("args", [(), ("deploy",), ("launch", "extra"), ("",)])
def test_usage_exit_64_leaves_everything_alone(rig, args):
    rig.receipt.write_text("keep")
    res = rig.run_pf(*args)
    assert res.returncode == 64
    assert rig.receipt.read_text() == "keep" and rig.calls() == []


@pytest.mark.parametrize("name", ["KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SOURCE_REPO", "SE_EPHE_PATH"])
def test_relative_path_setting_is_a_usage_error(rig, name):
    res = rig.launch(extra_env={name: "relative/path"})
    assert res.returncode == 64 and rig.calls() == []


# ── secrets ──────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("var", ["DATABASE_URL", "KY_BUILDER_DATABASE_URL", "AB_DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY"])
def test_secret_name_set_fails_and_value_is_never_printed(rig, var):
    rig.receipt.write_text("stale")
    res = rig.launch(extra_env={var: SECRET_VALUE})
    assert_fails_alone(rig, res, "secrets")
    assert var in res.stdout
    assert SECRET_VALUE not in res.stdout + res.stderr + rig.log.read_text()


def test_empty_secret_variable_still_counts_as_set(rig):
    res = rig.launch(extra_env={"PGPASSWORD": ""})
    assert_fails_alone(rig, res, "secrets")


def test_secrets_never_reach_the_children(rig):
    rig.launch(extra_env={"DATABASE_URL": SECRET_VALUE})
    assert SECRET_VALUE not in rig.log.read_text()
    # a probe that would show the value if a child inherited it
    write_exec(rig.bin / "claude", '#!/bin/bash\necho "claude $*" >> "$CALL_LOG"\necho "db=${DATABASE_URL-unset}" >> "$CALL_LOG"\necho "2.1.296"\n')
    rig.launch(extra_env={"DATABASE_URL": SECRET_VALUE})
    assert "db=unset" in rig.log.read_text() and SECRET_VALUE not in rig.log.read_text()


def test_similarly_named_variables_are_not_credentials(rig):
    res = rig.launch(extra_env={"DATABASE_URL_NOTE": "x", "MY_DATABASE": "x", "ANTHROPIC_API_KEYS": "x"})
    assert res.returncode == 0, res.stdout


# ── claude ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_claude_not_executable_fails(rig):
    (rig.bin / "claude").chmod(0o644)
    assert_fails_alone(rig, rig.launch(), "claude")


def test_claude_missing_fails(rig):
    (rig.bin / "claude").unlink()
    assert_fails_alone(rig, rig.launch(), "claude")


def test_claude_relative_path_fails(rig):
    assert_fails_alone(rig, rig.launch(extra_env={"CLAUDE_BIN": "claude"}), "claude")


@pytest.mark.parametrize("version", ["2.1.295 (Claude Code)", "2.1.239", "1.9.999", "2.0.400", "garbage", ""])
def test_claude_below_2_1_296_or_unparseable_fails(rig, version):
    rig.ctl_set("claude_version", version)
    res = rig.launch()
    assert_fails_alone(rig, res, "claude")


@pytest.mark.parametrize("version", ["2.1.296 (Claude Code)", "2.1.300", "2.2.0", "2.10.0", "3.0.0 (Claude Code)"])
def test_claude_at_or_above_2_1_296_passes_by_numeric_comparison(rig, version):
    rig.ctl_set("claude_version", version)
    res = rig.launch()
    assert res.returncode == 0, res.stdout
    assert rig.receipt_json()["claude"]["version"] == version.split()[0]


def test_claude_version_command_failing_fails(rig):
    rig.ctl_set("claude_exit", "3")
    assert_fails_alone(rig, rig.launch(), "claude")


def test_a_hung_command_is_a_failure_not_a_wait(rig):
    rig.ctl_set("claude_hang", "1")
    res = rig.launch(extra_env={"KY_PREFLIGHT_TIMEOUT": "2"})
    assert_fails_alone(rig, res, "claude")


# ── smoke (Claude only) ──────────────────────────────────────────────────────────────────────────────────────────

def test_smoke_missing_qualification_receipt_fails(rig):
    (rig.run / "QUALIFICATIONS" / "surrogate-claude-opus-5-5.json").unlink()
    res = rig.launch()
    assert_fails_alone(rig, res, "smoke")
    assert "surrogate" in res.stdout


def test_smoke_check_nonzero_fails_and_names_the_role(rig):
    rig.ctl_set("qual_fail", "bootstrap-builder")
    res = rig.launch()
    assert_fails_alone(rig, res, "smoke")
    assert "bootstrap-builder" in res.stdout


def test_smoke_every_config_is_checked_even_after_one_fails(rig):
    rig.ctl_set("qual_fail", "bootstrap-builder")
    rig.launch()
    assert len(rig.calls("kyqualify ")) == len(ROLES)


def test_smoke_no_launch_configuration_at_all_fails(rig):
    for p in (rig.fleet / "templates").glob("LAUNCH_CONFIG.*.json"):
        p.unlink()
    assert_fails_alone(rig, rig.launch(), "smoke")


def test_smoke_a_new_configuration_without_a_receipt_fails(rig):
    (rig.fleet / "templates" / "LAUNCH_CONFIG.extra.json").write_text(json.dumps({"role": "extra", "model": "claude-opus-5-5"}))
    assert_fails_alone(rig, rig.launch(), "smoke")


@pytest.mark.parametrize("config", [{"role": "../x", "model": "m"}, {"role": "r", "model": "a/b"}, {"model": "m"}, {"role": "r"},
                                    {"role": "", "model": "m"}, [1]])
def test_smoke_unusable_config_identity_fails(rig, config):
    (rig.fleet / "templates" / "LAUNCH_CONFIG.bad.json").write_text(json.dumps(config))
    assert_fails_alone(rig, rig.launch(), "smoke")


def test_smoke_config_that_is_not_json_fails(rig):
    (rig.fleet / "templates" / "LAUNCH_CONFIG.bad.json").write_text("{nope")
    assert_fails_alone(rig, rig.launch(), "smoke")


def test_smoke_missing_kyqualify_cannot_run_so_fails(rig):
    (rig.fleet / "kyqualify.py").unlink()
    assert_fails_alone(rig, rig.launch(), "smoke")


def test_smoke_receipt_changed_during_the_check_refuses_the_receipt(rig):
    (rig.fleet / "kyqualify.py").write_text(FAKE_KYQUALIFY.replace(
        "sys.exit(", "if sys.argv[2].endswith('/surrogate-claude-opus-5-5.json'): open(sys.argv[2], 'a').write(' ')\nsys.exit(", 1))
    res = rig.launch()
    assert res.returncode == 1 and not rig.receipt.exists()
    assert "FAIL receipt:" in res.stdout and "changed while preflight ran" in res.stdout


# ── dependencies ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_dependencies_checkout_not_a_git_work_tree_fails(rig):
    shutil.rmtree(rig.src / ".git")
    assert_fails_alone(rig, rig.launch(), "dependencies")


def test_dependencies_venv_import_failure_fails(rig):
    rig.ctl_set("venv_exit", "1")
    assert_fails_alone(rig, rig.launch(), "dependencies")
    assert rig.calls("venv_python ") == ["venv_python -c import pytest, psycopg, swisseph"]


def test_dependencies_venv_missing_fails(rig):
    (rig.root / "venv" / "bin" / "python").unlink()
    assert_fails_alone(rig, rig.launch(), "dependencies")


@pytest.mark.parametrize("rel", ["platform/node_modules", "platform-mcp/node_modules"])
def test_dependencies_node_modules_missing_fails_and_launch_repairs_nothing(rig, rel):
    shutil.rmtree(rig.src / rel)
    assert_fails_alone(rig, rig.launch(), "dependencies")
    assert rig.calls("npm ") == [] and not (rig.src / rel).exists()


@pytest.mark.parametrize("name", sorted(PINNED))
def test_dependencies_ephemeris_hash_mismatch_fails(rig, name):
    (rig.ephe / name).write_bytes(b"tampered")
    res = rig.launch()
    assert_fails_alone(rig, res, "dependencies")
    assert name in res.stdout
    assert (rig.ephe / name).read_bytes() == b"tampered"
    assert not [c for c in rig.calls("curl ") if "-o" in c], "launch repairs nothing"


@pytest.mark.parametrize("name", sorted(PINNED))
def test_dependencies_ephemeris_missing_fails_and_launch_downloads_nothing(rig, name):
    (rig.ephe / name).unlink()
    assert_fails_alone(rig, rig.launch(), "dependencies")
    assert not (rig.ephe / name).exists()
    assert not [c for c in rig.calls("curl ") if "-o" in c]


def test_dependencies_pins_file_missing_or_without_the_pin_fails(rig):
    pins = rig.src / "platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py"
    text = pins.read_text()
    pins.write_text(text.replace('"seas_18.se1"', '"other.se1"'))
    assert_fails_alone(rig, rig.launch(), "dependencies")
    pins.unlink()
    assert_fails_alone(rig, rig.launch(), "dependencies")


# ── tracker ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_tracker_asked_at_the_configured_url(rig):
    assert rig.launch(extra_env={"PRAVAHA_URL": "http://127.0.0.1:9999/"}).returncode == 0
    assert rig.calls("curl ")[0].endswith("http://127.0.0.1:9999/api/health")


@pytest.mark.parametrize("body", ['{"ok": false}', '{"ok": "true"}', '{"ok": 1}', '{}', 'not json', '',
                                  '{"ok": true, "model_error": "model refused"}', '[true]'])
def test_tracker_health_not_ok_fails(rig, body):
    rig.ctl_set("health.json", body)
    assert_fails_alone(rig, rig.launch(), "tracker")


@pytest.mark.parametrize("body", ['{"ok": true}', '{"ok": true, "model_error": null}', '{"ok": true, "model_error": ""}',
                                  '{"ok": true, "extra": {"a": 1}}'])
def test_tracker_ok_true_without_model_error_passes(rig, body):
    rig.ctl_set("health.json", body)
    assert rig.launch().returncode == 0


def test_tracker_unreachable_fails(rig):
    rig.ctl_set("curl_exit", "7")
    assert_fails_alone(rig, rig.launch(), "tracker")


@pytest.mark.parametrize("curl", ["curl", "/nonexistent/curl"])
def test_tracker_curl_that_cannot_run_fails(rig, curl):
    assert_fails_alone(rig, rig.launch(extra_env={"KY_CURL": curl}), "tracker")


# ── audit (KU-01, rulings P17) ───────────────────────────────────────────────────────────────────────────────────

def test_audit_exit_1_with_exact_accepted_reconciliation_passes_and_findings_reach_the_receipt(rig):
    rig.accept_reconciliation()
    res = rig.launch()
    assert res.returncode == 0, res.stdout
    for code, ref in FINDINGS:
        assert f"FAIL {code} {ref}:" in res.stdout, "every finding line is echoed"
    assert [(s, n) for s, n, _ in check_lines(res.stdout)] == [("ok", n) for n in LAUNCH_CHECKS]
    audit = rig.receipt_json()["audit"]
    assert audit == {"exit": 1, "findings": [{"code": c, "ref": r} for c, r in FINDINGS],
                     "reconciliation_sha256": sha(rig.recon), "review_sha256": sha(rig.review)}


def test_audit_finding_without_a_reconciliation_entry_fails(rig):
    rig.accept_reconciliation(FINDINGS[:1])
    res = rig.launch()
    assert_fails_alone(rig, res, "audit")
    assert "VERDICT_ORPHAN" in res.stdout


def test_audit_entry_without_a_finding_fails(rig):
    rig.accept_reconciliation(FINDINGS + [("OLD_CODE", "claim:99")])
    res = rig.launch()
    assert_fails_alone(rig, res, "audit")
    assert "OLD_CODE" in res.stdout


def test_audit_same_code_different_ref_is_a_different_finding(rig):
    rig.accept_reconciliation([("CLAIM_NO_VERDICT", "claim:13"), FINDINGS[1]])
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_no_reconciliation_record_fails(rig):
    rig.set_audit(AUDIT_OUT, 1)
    assert_fails_alone(rig, rig.launch(), "audit")


@pytest.mark.parametrize("field", ["disposition", "authority"])
@pytest.mark.parametrize("value", ["", "   ", None, 5])
def test_audit_empty_disposition_or_authority_fails(rig, field, value):
    rig.set_audit(AUDIT_OUT, 1)
    rig.write_recon()
    rec = json.loads(rig.recon.read_text())
    rec["entries"][0][field] = value
    rig.recon.write_text(json.dumps(rec))
    rig.write_review(sha(rig.recon))
    assert_fails_alone(rig, rig.launch(), "audit")


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(schema="ky.audit_reconciliation/2"),
    lambda r: r.pop("schema"),
    lambda r: r.update(entries="x"),
    lambda r: r.update(entries=[1]),
    lambda r: r["entries"].append(dict(r["entries"][0])),
    lambda r: r["entries"][0].pop("ref"),
])
def test_audit_malformed_or_duplicated_record_fails(rig, mutate):
    rig.set_audit(AUDIT_OUT, 1)
    rig.write_recon()
    rec = json.loads(rig.recon.read_text())
    mutate(rec)
    rig.recon.write_text(json.dumps(rec))
    rig.write_review(sha(rig.recon))
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_record_not_json_fails(rig):
    rig.set_audit(AUDIT_OUT, 1)
    rig.recon.write_text("{nope")
    rig.write_review(sha(rig.recon))
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_record_without_a_review_fails(rig):
    rig.set_audit(AUDIT_OUT, 1)
    rig.write_recon()
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_record_not_accepted_at_its_current_digest_fails(rig):
    rig.accept_reconciliation()
    rec = json.loads(rig.recon.read_text())
    rec["entries"][0]["disposition"] = "edited after the review"
    rig.recon.write_text(json.dumps(rec))
    res = rig.launch()
    assert_fails_alone(rig, res, "audit")
    assert "digest" in res.stdout


@pytest.mark.parametrize("over", [
    {"verdict": "REJECTED"}, {"verdict": "accepted"}, {"verdict": None}, {"inputs": "0" * 64}, {"inputs": None},
    {"inputs": ["x"]}, {"reviewer_session_id": "PLAN-1"}, {"reviewer_session_id": ""}, {"author_session_id": ""},
    {"reviewer_session_id": None},
])
def test_audit_review_not_independent_or_not_accepted_fails(rig, over):
    rig.set_audit(AUDIT_OUT, 1)
    digest = rig.write_recon()
    rig.write_review(digest, **over)
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_review_missing_a_session_field_fails(rig):
    rig.set_audit(AUDIT_OUT, 1)
    digest = rig.write_recon()
    rig.review.write_text(json.dumps({"verdict": "ACCEPTED", "inputs": digest, "reviewer_session_id": "REV-1"}))
    assert_fails_alone(rig, rig.launch(), "audit")


@pytest.mark.parametrize("code", [2, 3, 78, 127, 130])
def test_audit_unavailable_exit_fails(rig, code):
    rig.accept_reconciliation()
    rig.set_audit(AUDIT_OUT, code)
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_count_line_must_equal_lines_parsed(rig):
    rig.accept_reconciliation()
    rig.set_audit(AUDIT_OUT.replace("2 findings", "3 findings"), 1)
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_count_line_missing_fails(rig):
    rig.accept_reconciliation()
    rig.set_audit(AUDIT_OUT.replace("AUDIT FAIL: 2 findings\n", ""), 1)
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_unparseable_fail_line_fails(rig):
    rig.accept_reconciliation()
    rig.set_audit(AUDIT_OUT.replace("AUDIT FAIL: 2", "FAIL malformed line\nAUDIT FAIL: 2"), 1)
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_exit_1_with_no_findings_is_unknown_so_fails(rig):
    rig.set_audit("AUDIT FAIL: 0 findings\n", 1)
    rig.write_review(rig.write_recon([]))
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_missing_ky_cannot_run_so_fails(rig):
    (rig.root / "bin" / "ky").unlink()
    assert_fails_alone(rig, rig.launch(), "audit")


def test_audit_exit_0_needs_no_reconciliation_and_ignores_a_stale_one(rig):
    rig.write_recon([("GONE", "x:1")])
    res = rig.launch()
    assert res.returncode == 0
    assert rig.receipt_json()["audit"]["reconciliation_sha256"] is None


def test_audit_finding_line_echo_cannot_be_mistaken_for_a_check_line(rig):
    rig.set_audit(AUDIT_OUT.replace("claim has no verdict", "x\nok slots"), 1)
    rig.write_review(rig.write_recon())
    res = rig.launch()
    assert [n for _, n, _ in check_lines(res.stdout)].count("slots") == 1


# ── slots (P16) ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_slots_command_failing_fails_and_nothing_else_is_called(rig):
    rig.ctl_set("slots_exit", "1")
    assert_fails_alone(rig, rig.launch(), "slots")
    assert rig.calls("local_db ") == ["local_db slots"]


@pytest.mark.parametrize("listing", ["b1\nb2\n", "v1\nv2\n", "", "b1\nv1\nbogus\n", "b1\n\nv1\n", "x1\ny1\n"])
def test_slots_need_one_b_and_one_v_and_nothing_else(rig, listing):
    rig.ctl_set("slots", listing)
    assert_fails_alone(rig, rig.launch(), "slots")
    assert rig.calls("local_db ") == ["local_db slots"]


def test_slots_proof_uses_the_first_slot_listed(rig):
    rig.ctl_set("slots", "v2\nb3\nb1\nv1\n")
    assert rig.launch().returncode == 0
    assert rig.calls("local_db ")[2].startswith("local_db db v2 --session ")
    assert rig.receipt_json()["slots"] == ["v2", "b3", "b1", "v1"]


@pytest.mark.parametrize("step,expected", [
    ("up", ["slots", "up", "close"]),
    ("db", ["slots", "up", "db", "close"]),
    ("check", ["slots", "up", "db", "check", "close"]),
])
def test_slots_failing_step_is_named_and_close_is_still_attempted(rig, step, expected):
    rig.ctl_set("localdb_fail", step)
    res = rig.launch()
    assert_fails_alone(rig, res, "slots")
    assert step in [x for x in res.stdout.splitlines() if x.startswith("FAIL slots")][0]
    assert [c.split()[1] for c in rig.calls("local_db ")] == expected
    sessions = {c.split()[-1] for c in rig.calls("local_db ") if "--session" in c}
    assert len(sessions) == 1


def test_slots_hung_step_fails_and_close_is_still_attempted(rig):
    rig.ctl_set("localdb_fail", "hang_db")
    res = rig.launch(extra_env={"KY_PREFLIGHT_TIMEOUT": "2"})
    assert_fails_alone(rig, res, "slots")
    assert [c.split()[1] for c in rig.calls("local_db ")] == ["slots", "up", "db", "close"]


@pytest.mark.parametrize("result", ["FAILED", "STALE", ""])
def test_slots_receipt_not_ready_fails(rig, result):
    rig.ctl_set("db_result", result)
    res = rig.launch()
    assert_fails_alone(rig, res, "slots")
    assert rig.calls("local_db ")[-1].startswith("local_db close --session ")


def test_slots_receipt_for_another_session_fails(rig):
    rig.ctl_set("db_session", "SOMEONE-ELSE")
    assert_fails_alone(rig, rig.launch(), "slots")


@pytest.mark.parametrize("key", ["db_seed_schema"])
def test_slots_seed_hash_unequal_fails(rig, key):
    rig.ctl_set(key, "0" * 64)
    res = rig.launch()
    assert_fails_alone(rig, res, "slots")
    assert rig.calls("local_db ")[-1].startswith("local_db close --session ")


@pytest.mark.parametrize("name", sorted(SEED_FILES.values()))
def test_slots_a_seed_file_changed_after_the_receipt_is_unequal(rig, name):
    # the receipt hashes were taken from the files; changing the file under the fake after db but before the comparison
    (rig.fleet / "local_db.sh").write_text(FAKE_LOCAL_DB.replace(
        '  check) exit 0 ;;', f'  check) echo tamper >> "$KY_RUN/schema/{name}"; exit 0 ;;'))
    assert_fails_alone(rig, rig.launch(), "slots")


def test_slots_seed_file_empty_or_missing_fails(rig):
    (rig.run / "schema" / "asset_registry_data.sql").unlink()
    assert_fails_alone(rig, rig.launch(), "slots")


def test_slots_close_failure_fails(rig):
    rig.ctl_set("close_exit", "1")
    res = rig.launch()
    assert_fails_alone(rig, res, "slots")
    assert "close" in [x for x in res.stdout.splitlines() if x.startswith("FAIL slots")][0]


def test_slots_removal_unproven_when_the_receipt_survives_close(rig):
    rig.ctl_set("close_keep", "1")
    assert_fails_alone(rig, rig.launch(), "slots")


def test_slots_missing_local_db_cannot_run_so_fails(rig):
    (rig.fleet / "local_db.sh").unlink()
    assert_fails_alone(rig, rig.launch(), "slots")


def test_slots_interrupted_run_still_closes_its_session(rig):
    # the fake `up` sends SIGTERM to preflight itself (its grandparent: fake <- bounded helper <- preflight)
    write_exec(rig.fleet / "local_db.sh", FAKE_LOCAL_DB.replace(
        "  up) exit 0 ;;",
        '  up) pp="$(ps -o ppid= -p $PPID | tr -d " ")"; kill -TERM "$pp"; sleep 1; exit 0 ;;'))
    res = rig.launch()
    assert res.returncode == 143, (res.stdout, res.stderr)
    assert [c.split()[1] for c in rig.calls("local_db ")] == ["slots", "up", "close"]
    assert not rig.receipt.exists()


# ── bootstrap ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_bootstrap_ok_writes_no_receipt_and_runs_none_of_the_launch_checks(rig):
    res = rig.run_pf("bootstrap")
    assert res.returncode == 0, (res.stdout, res.stderr)
    assert [(s, n) for s, n, _ in check_lines(res.stdout)] == [("ok", "dependencies")]
    assert not rig.receipt.exists()
    assert rig.calls() == ["venv_python -c import pytest, psycopg, swisseph"]


def test_bootstrap_leaves_an_existing_receipt_alone(rig):
    rig.receipt.write_text("keep")
    assert rig.run_pf("bootstrap").returncode == 0
    assert rig.receipt.read_text() == "keep"


def test_bootstrap_downloads_a_missing_ephemeris_file_and_verifies_it(rig):
    (rig.ephe / "semo_18.se1").unlink()
    res = rig.run_pf("bootstrap")
    assert res.returncode == 0, res.stdout
    assert (rig.ephe / "semo_18.se1").read_bytes() == PINNED["semo_18.se1"]
    assert any("madhav-ephemeris/se1/semo_18.se1" in c for c in rig.calls("curl "))
    assert not list(rig.ephe.glob(".*tmp*")) and not list(rig.ephe.glob("*.tmp*"))


def test_bootstrap_replaces_a_wrong_ephemeris_file_only_with_a_verified_one(rig):
    (rig.ephe / "sepl_18.se1").write_bytes(b"corrupt")
    assert rig.run_pf("bootstrap").returncode == 0
    assert (rig.ephe / "sepl_18.se1").read_bytes() == PINNED["sepl_18.se1"]


def test_bootstrap_download_with_the_wrong_hash_fails_and_installs_nothing(rig):
    (rig.ephe / "semo_18.se1").unlink()
    (rig.ctl / "download" / "semo_18.se1").write_bytes(b"not the pinned bytes")
    res = rig.run_pf("bootstrap")
    assert res.returncode == 1 and statuses(res) == {"dependencies": "FAIL"}
    assert not (rig.ephe / "semo_18.se1").exists() and not list(rig.ephe.glob("*tmp*"))


def test_bootstrap_download_failing_fails(rig):
    (rig.ephe / "semo_18.se1").unlink()
    (rig.ctl / "download" / "semo_18.se1").unlink()
    res = rig.run_pf("bootstrap")
    assert res.returncode == 1 and statuses(res) == {"dependencies": "FAIL"}


@pytest.mark.parametrize("rel", ["platform", "platform-mcp"])
def test_bootstrap_repairs_missing_node_modules_with_npm_ci(rig, rel):
    shutil.rmtree(rig.src / rel / "node_modules")
    res = rig.run_pf("bootstrap")
    assert res.returncode == 0, res.stdout
    [call] = rig.calls("npm ")
    assert call.startswith("npm ci (cwd=") and call.endswith(rel + ")")
    assert (rig.src / rel / "node_modules").is_dir()


def test_bootstrap_missing_venv_is_created_and_still_fails_without_the_imports(rig):
    shutil.rmtree(rig.root / "venv")
    for r in ("requirements.txt", "requirements-ci.txt"):
        (rig.src / "platform/python-sidecar").mkdir(parents=True, exist_ok=True)
        (rig.src / "platform/python-sidecar" / r).write_text("")
    res = rig.run_pf("bootstrap")
    assert (rig.root / "venv" / "bin" / "python").exists(), res.stdout
    assert res.returncode == 1 and statuses(res) == {"dependencies": "FAIL"}, "the imports are not installed: never ok"


def test_bootstrap_checkout_not_a_git_work_tree_fails(rig):
    shutil.rmtree(rig.src / ".git")
    res = rig.run_pf("bootstrap")
    assert res.returncode == 1 and statuses(res) == {"dependencies": "FAIL"}
    assert rig.calls("npm ") == []


def test_bootstrap_has_no_smoke_no_model_no_audit_no_slots(rig):
    rig.run_pf("bootstrap")
    assert not [c for c in rig.calls() if c.split()[0] in ("claude", "ky", "kyqualify", "local_db")]


def qualification_readers():
    """Load the real embedded helpers without invoking either entrypoint."""
    install = FLEET / "install.sh"
    program = install.read_text().split("\n: <<'KYINSTALL_PY'\n", 1)[1].rsplit("\nKYINSTALL_PY\n", 1)[0]
    program = program.rsplit("\nsys.exit(main(sys.argv[1:]))", 1)[0]
    installer = {"__file__": str(install)}
    exec(compile(program, str(install), "exec"), installer)
    program = PREFLIGHT.read_text().split("PYSRC <<'PYEOF'\n", 1)[1].split("\nPYEOF", 1)[0]
    preflight = {"__name__": "preflight_helpers"}
    exec(compile(program, str(PREFLIGHT), "exec"), preflight)
    return installer, preflight


def install_bound_templates(rig):
    sys.path.insert(0, str(FLEET))
    import kymanifest
    bound, deferred = kymanifest.read_component_list(str(FLEET.parents[3]))
    templates = rig.fleet / "templates"
    shutil.rmtree(templates)
    templates.mkdir()
    for rel in bound:
        if "/templates/LAUNCH_CONFIG." in rel:
            (templates / Path(rel).name).write_bytes((FLEET.parents[3] / rel).read_bytes())
    return sorted(templates.glob("LAUNCH_CONFIG.*.json")), deferred


def test_smoke_naming_matches_installer_and_manifest_for_every_installed_template(rig, capsys):
    # Dropping a variant suffix binds the wrong receipt even when the plain role is PASS.
    configs, deferred = install_bound_templates(rig)
    installer, preflight = qualification_readers()
    import kymanifest
    for cfg in configs:
        doc = json.loads(cfg.read_text())
        tag = installer["qualification_tag"](str(cfg), doc)
        (rig.run / "QUALIFICATIONS" / f'{tag}-{doc["model"]}.json').write_text('{}')
    out = rig.tmp / "smoke-plan.json"
    preflight["cmd_smoke_plan"](str(rig.fleet), str(rig.run), str(out))
    entries = json.loads(out.read_text())
    assert len(entries) == len(configs) == 20
    assert "ERR\t" not in capsys.readouterr().out
    for entry in entries:
        cfg = Path(entry["config"])
        doc = json.loads(cfg.read_text())
        tag = installer["qualification_tag"](str(cfg), doc)
        assert Path(entry["receipt"]).name == f'{tag}-{doc["model"]}.json'
        argv = ["--mcp-config", doc["mcp_config"]] if doc.get("mcp_config") else []
        selected = kymanifest.launch_config_of(dict(doc, binds={"env_names": doc["env_names"], "argv": argv}))
        assert Path(selected).name == cfg.name
    receipts = {Path(e["receipt"]).name for e in entries}
    assert {"build-tests-claude-opus-5-5.json", "build-tests-gpt-6.1-sol.json",
            "rework-tests-claude-opus-5-5.json", "verify-tests-gpt-6.1-sol.json"} <= receipts
    assert not ({Path(rel).name for rel in deferred} & {Path(e["config"]).name for e in entries})


@pytest.mark.parametrize("tests", [None, "platform/tests/first.py\nplatform/tests/second.py"])
def test_smoke_checks_bound_variants_with_installer_identity_and_evidence(rig, tests):
    # Missing KY_* identity used to make resolve_env refuse; TESTS has a harness default.
    configs, _ = install_bound_templates(rig)
    installer, _ = qualification_readers()
    for cfg in configs:
        doc = json.loads(cfg.read_text())
        tag = installer["qualification_tag"](str(cfg), doc)
        (rig.run / "QUALIFICATIONS" / f'{tag}-{doc["model"]}.json').write_text(
            json.dumps({"config_sha256": sha(cfg)}))
    # Replace the unconditional fake exit with the strict boundary checks.
    strict = FAKE_KYQUALIFY.replace('sys.exit(1 if json.load(open(cfg))["role"] in bad else 0)', f'''
import hashlib
sys.path.insert(0, {str(FLEET)!r})
import kyqualify
doc = json.load(open(cfg))
resolved, errors = kyqualify.resolve_env(doc, dict(os.environ, HOME="/h", USER="u"))
if "TESTS" in doc["env_names"]:
    assert resolved["TESTS"] == {tests if tests is not None else '00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyqualify.py'!r}
expected = {installer["QUALIFICATION_JOB_ENV"]!r}.get(doc["role"], {{}})
assert all(os.environ.get(k) == v for k, v in expected.items()), expected
assert not errors, errors
assert "--verify-evidence" in sys.argv
receipt = json.load(open(sys.argv[2]))
assert receipt["config_sha256"] == hashlib.sha256(open(cfg, "rb").read()).hexdigest()
sys.exit(0)
''')
    (rig.fleet / "kyqualify.py").write_text(strict)
    env = {"KY_STREAM": "wrong", "KY_LANE": "wrong", "KY_CONTROLLER_ID": "wrong"}
    if tests is not None:
        env["TESTS"] = tests
    result = rig.launch(extra_env=env)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert len(rig.receipt_json()["qualifications"]) == 20
    assert len(rig.calls("kyqualify")) == 20
