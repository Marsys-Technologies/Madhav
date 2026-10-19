"""W2-M-08 oracles: every protected-window dispatcher refuses while a foreign production lease is ACTIVE.

Source of the rule: the prime rule of the shared lease table, as executor.lease_live states it ("the ONE unexpired ACTIVE row ... one campaign deploys or builds at a
time", executor.py:255-274). Each oracle uses a fake lease table: a local bare origin whose campaign-coordination branch carries the table. No production, no network.

Claims, one oracle each (a single planted reversion of the named line fails it):
  C1 a foreign ACTIVE unexpired lease -> refuse            (window_lease_gate.verdict: `if foreign`)
  C2 no ACTIVE lease -> dispatch                           (verdict: the final OK)
  C3 the window's own lease only -> dispatch               (verdict: `foreign = [... != own_lease]`)
  C4 an unreadable table -> refuse (fail closed)           (read_table / verdict: `table_text is None`)
  C5 an expired or non-ACTIVE row is not a lease           (active_leases: the expiry and ACTIVE tests)
  C6 the reading is executor.lease_live's reading          (parity over the same fixtures)
  C7 kala_window_auto.sh asks the gate before `gh workflow run`
  C8 deploy.yml's protected job runs the gate before any credential step
"""
import datetime as dt
import importlib.util
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
GATE_PY = FLEET / "window_lease_gate.py"
AUTO_SH = FLEET / "ops_guard" / "kala_window_auto.sh"
EXECUTOR_PY = FLEET / "executor.py"
DEPLOY_YML = REPO / ".github" / "workflows" / "deploy.yml"
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"

REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                      "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _env():
    return {**{k: v for k, v in os.environ.items() if k not in REPO_LOCATING_VARS}, **GIT_ENV}


def _git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=_env())
    assert p.returncode == 0, f"git {args}: {p.stderr[-300:]}"
    return p.stdout.strip()


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load(GATE_PY, "ky_window_lease_gate_under_test")


def _expiry(hours):
    return (dt.datetime.now(IST) + dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")


def table(*rows):
    """A lease table in the real shape (six cells; §1 then §2). A row is (lease_id, hours_to_expiry, state)."""
    body = "".join(f"| {lease} | camp | scope | start | {_expiry(hours)} | {state} |\n" for lease, hours, state in rows)
    return ("# fixture\n\n## 1. Leases\n\n| lease | campaign | scope | start | expires | state |\n|---|---|---|---|---|---|\n"
            + body + "\n## 2. Other\n\n| not | a | lease | row | x | ACTIVE |\n")


def _garble(text):
    return re.sub(r"\d{4}-\d\d-\d\d \d\d:\d\d", "someday", text)


class World:
    """A repository whose origin is a local bare repo; origin/campaign-coordination carries `text` (None: the branch does not exist)."""

    def __init__(self, tmp_path, text):
        self.origin, self.repo = tmp_path / "origin.git", tmp_path / "checkout"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True, env=_env())
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True, env=_env())
        _git(self.repo, "remote", "add", "origin", str(self.origin))
        (self.repo / "README").write_text("x")
        _git(self.repo, "add", "-A"); _git(self.repo, "commit", "-q", "-m", "main"); _git(self.repo, "push", "-q", "origin", "main")
        if text is not None:
            _git(self.repo, "checkout", "-q", "-b", "campaign-coordination")
            (self.repo / COORD_REL).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / COORD_REL).write_text(text)
            _git(self.repo, "add", "-A"); _git(self.repo, "commit", "-q", "-m", "lease"); _git(self.repo, "push", "-q", "origin", "campaign-coordination")
            _git(self.repo, "checkout", "-q", "main")

    def run_gate(self, own=None):
        cmd = [sys.executable, "-I", str(GATE_PY), "--repo", str(self.repo)] + (["--own-lease", own] if own is not None else [])
        p = subprocess.run(cmd, capture_output=True, text=True, env=_env(), timeout=60)
        return p.returncode, p.stdout.strip()


def test_c1_foreign_active_lease_refuses(tmp_path):
    rc, out = World(tmp_path, table(("J-3", 5, "ACTIVE"))).run_gate()
    assert rc == 1 and "J-3" in out
    rc, out = World(tmp_path / "b", table(("MINE", 5, "ACTIVE"), ("J-3", 5, "**ACTIVE**"))).run_gate(own="MINE")   # own does not excuse a second, foreign lease
    assert rc == 1 and "J-3" in out and "MINE" not in out.split(":", 1)[1]


def test_c2_no_active_lease_dispatches(tmp_path):
    rc, out = World(tmp_path, table(("L-1", 5, "RELEASED"), ("L-2", -3, "ACTIVE"))).run_gate()
    assert rc == 0 and out.startswith("OK")


def test_c3_own_lease_alone_dispatches(tmp_path):
    rc, out = World(tmp_path, table(("MINE", 5, "ACTIVE"), ("OLD", 5, "RELEASED"))).run_gate(own="MINE")
    assert rc == 0 and out.startswith("OK")


@pytest.mark.parametrize("why", ["no_branch", "no_section_1", "bad_expiry", "unsafe_own", "no_repo"])
def test_c4_unreadable_table_refuses(tmp_path, why):
    own = None
    if why == "no_branch":
        world = World(tmp_path, None)
    elif why == "no_section_1":
        world = World(tmp_path, "# fixture\n\nno leases section here\n")
    elif why == "bad_expiry":
        world = World(tmp_path, _garble(table(("J-3", 5, "ACTIVE"))))
    elif why == "unsafe_own":
        world, own = World(tmp_path, table(("J-3", 5, "ACTIVE"))), "x;rm -rf /"
    else:
        world = World(tmp_path, table())
        world.repo = tmp_path / "does-not-exist"
    rc, out = world.run_gate(own=own)
    assert rc == 1 and out.startswith("REFUSED")


def test_c4_an_own_lease_that_is_not_active_refuses(tmp_path):
    rc, out = World(tmp_path, table(("OTHER-RELEASED", 5, "RELEASED"))).run_gate(own="MINE")
    assert rc == 1 and "MINE" in out


def test_c5_expired_and_non_active_rows_are_not_leases():
    now = dt.datetime.now(dt.timezone.utc)
    assert gate.active_leases(table(("A", -1, "ACTIVE"), ("B", 5, "RELEASED"), ("C", 5, "ACTIVE (paused)"), ("D", 5, "ACTIVE-PAUSED")), now) == ["C"]
    assert gate.active_leases(table(("A", 2, "ACTIVE")), now + dt.timedelta(hours=3)) == []   # the expiry is measured against `now`


FIXTURES = {
    "one_live": table(("L-A", 4, "ACTIVE")),
    "two_live": table(("L-A", 4, "ACTIVE"), ("L-B", 4, "ACTIVE")),
    "expired": table(("L-A", -4, "ACTIVE")),
    "released": table(("L-A", 4, "RELEASED")),
    "starred": table(("**L-A**", 4, "**ACTIVE** (owner)")),
    "bad_expiry": _garble(table(("L-A", 4, "ACTIVE"))),
    "no_section": "nothing here",
}


@pytest.mark.parametrize("name", sorted(FIXTURES))
@pytest.mark.parametrize("own", ["L-A", "L-B", "L-Z"])
def test_c6_reads_the_table_exactly_as_executor_lease_live(tmp_path, monkeypatch, name, own):
    """For every fixture, the gate with own=X dispatches iff executor.lease_live(X) (X is the one live lease) - the same table, the same rules."""
    world = World(tmp_path, FIXTURES[name])
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)
    for k in REPO_LOCATING_VARS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky")); monkeypatch.setenv("KY_SOURCE_REPO", str(world.repo))
    ex = _load(EXECUTOR_PY, f"ky_executor_for_gate_{name}_{own}")
    rc, out = world.run_gate(own=own)
    assert (rc == 0) == ex.lease_live(own), (name, own, out)


def _fake_bin(tmp_path):
    """A `gh` that records dispatches and a `sleep` that ends the dispatcher loop at its first pause."""
    b = tmp_path / "bin"; b.mkdir()
    (b / "gh").write_text('#!/bin/bash\ncase "$*" in\n  "run list --commit"*) echo "completed/success";;\n  "workflow run"*) echo "$*" >> "$KY_TEST_GH_LOG";;\nesac\nexit 0\n')
    (b / "sleep").write_text("#!/bin/bash\nkill -TERM $PPID\nexit 0\n")
    for f in b.iterdir():
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return b


def _run_auto(tmp_path, lease_text, own=None, keep_gate=True):
    world = World(tmp_path / "w", lease_text)
    guard = tmp_path / "guard"; guard.mkdir()
    (guard / "kala_window_select.py").write_text("import sys\nprint('1381_fixture.sql')\ndef derived(r): return ['1381_fixture.sql']\n")
    (guard / "kala_window_decide.py").write_text("print('go')\n")
    if keep_gate:
        (guard / "window_lease_gate.py").write_bytes(GATE_PY.read_bytes())
    gh_log = tmp_path / "gh.log"
    env = {**_env(), "PATH": f"{_fake_bin(tmp_path)}:{os.environ['PATH']}", "KY_REPO": str(world.repo), "KY_KWA_GUARD": str(guard),
           "KY_KWA_STATE": str(tmp_path / "state.json"), "KY_TEST_GH_LOG": str(gh_log)}
    if own is not None:
        env["KY_KWA_OWN_LEASE"] = own
    p = subprocess.run(["bash", str(AUTO_SH)], capture_output=True, text=True, env=env, timeout=60)
    return p, gh_log.read_text() if gh_log.exists() else ""


def test_c7_auto_dispatcher_dispatches_with_no_lease(tmp_path):
    p, dispatched = _run_auto(tmp_path, table(("L-1", 5, "RELEASED")))
    assert "workflow run deploy.yml --ref main -f kala_schema_migration=true" in dispatched, p.stdout + p.stderr


def test_c7_auto_dispatcher_holds_while_a_foreign_lease_is_active(tmp_path):
    p, dispatched = _run_auto(tmp_path, table(("J-3", 5, "ACTIVE")))
    assert dispatched == "" and "HOLD lease gate" in p.stdout and "J-3" in p.stdout, p.stdout + p.stderr


def test_c7_auto_dispatcher_dispatches_under_its_own_lease(tmp_path):
    p, dispatched = _run_auto(tmp_path, table(("MINE", 5, "ACTIVE")), own="MINE")
    assert "kala_schema_migration=true" in dispatched, p.stdout + p.stderr


def test_c7_auto_dispatcher_names_its_own_lease_to_the_deploy_gate(tmp_path):
    """B-1: deploy.yml re-runs the gate with --own-lease "$WINDOW_LEASE_ID"; a dispatch that omits window_lease_id makes its own lease foreign there."""
    p, dispatched = _run_auto(tmp_path / "a", table(("MINE", 5, "ACTIVE")), own="MINE")
    assert "-f window_lease_id=MINE" in dispatched, p.stdout + p.stderr
    # The deploy-side check, fed exactly what was dispatched, passes; the same run without the input is refused.
    world = World(tmp_path / "b", table(("MINE", 5, "ACTIVE")))
    sent = re.search(r"window_lease_id=(\S+)", dispatched).group(1)
    assert world.run_gate(own=sent)[0] == 0
    assert world.run_gate(own="")[0] != 0
    # With no own lease the dispatcher sends no window_lease_id (unchanged behaviour).
    p, dispatched = _run_auto(tmp_path / "c", table(("L-1", 5, "RELEASED")))
    assert "window_lease_id" not in dispatched, p.stdout + p.stderr


def test_c7_auto_dispatcher_holds_when_the_table_is_unreadable_or_the_gate_is_missing(tmp_path):
    p, dispatched = _run_auto(tmp_path / "a", None)   # no campaign-coordination branch
    assert dispatched == "" and "HOLD lease gate" in p.stdout, p.stdout + p.stderr
    p, dispatched = _run_auto(tmp_path / "b", table(), keep_gate=False)   # a gate that cannot run is not a pass
    assert dispatched == "" and "HOLD lease gate" in p.stdout, p.stdout + p.stderr


def _job(text):
    m = re.search(r"^  jataka-protected-migrations:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n)", text, re.S | re.M)
    assert m, "jataka-protected-migrations job not found"
    return m.group(1)


def test_c8_protected_job_runs_the_gate_before_any_credential_step():
    job = _job(DEPLOY_YML.read_text())
    ran = re.search(r'^        run: python3 00_ARCHITECTURE/briefs/kalayantra/fleet/window_lease_gate\.py --repo \. --own-lease "\$WINDOW_LEASE_ID"$', job, re.M)
    assert ran, "the protected job never runs window_lease_gate.py"
    gate_at = ran.start()
    assert job.find("WINDOW_LEASE_ID: ${{ inputs.window_lease_id }}") > 0
    for first_credential_use in ("google-github-actions/auth", "Start Cloud SQL Auth Proxy", "secrets.PROD_DATABASE_URL", "secrets.DATA_PLANE_MIGRATOR_DATABASE_URL"):
        assert 0 < gate_at < job.find(first_credential_use), f"the lease gate must run before {first_credential_use}"
    assert "window_lease_id:" in DEPLOY_YML.read_text().split("jobs:", 1)[0]
