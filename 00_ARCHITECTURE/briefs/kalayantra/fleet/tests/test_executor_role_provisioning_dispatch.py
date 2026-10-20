"""U-M-03 oracles: the executor kinds gochara_role_provisioning_dispatch and gochara_role_provisioning_dispatch_dryrun (fleet/role_provisioning_dispatch.py).

Sources of the rules: the one-shot workflow itself (.github/workflows/gochara-role-provisioning-oneshot.yml: its `confirm` text, its `stage` choices, its declared inputs,
`github.ref == 'refs/heads/main'`), the prime rule of the shared lease table as executor.lease_live states it (one campaign changes production at a time; fleet/window_lease_gate.py
is the same reading), and the runbook's no-credential rule (A1). A fake `gh` records its argv; a fake lease table is a local bare origin. No production, no network, no secret.

Claims, one oracle each (a single planted reversion of the named line fails it):
  P1 both kinds ship disabled with a real script (exact binding: test_executor_table.PROVISIONING_BINDINGS; refusal: its disabled-kind oracle)  (executor_ops.json `enabled`)
  P2 only stage create-roles is served                                  (plan: `args.stage != STAGE`)
  P3 only the workflow's own confirm text dispatches                    (plan: `args.confirm != CONFIRM`)
  P4 a foreign ACTIVE lease refuses, and so does an unreadable table    (plan: `verdict(...)`)
  P5 window_lease_id is required and must be ACTIVE                     (plan: `not own`; verdict's own-lease test)
  P6 the request's own lease_id must be the window_lease_id             (plan: the KY_OPERATION_REQUEST comparison)
  P7 a clean lease dispatches exactly the workflow's declared inputs on main  (main: the gh argv)
  P8 the dry run runs the lease gate and makes no gh call               (main: `args.dry_run`)
  P9 dsn_tail: `?` restored, no credential, no second @                 (dsn_tail)
  P10 no credential is read, forwarded or printed                       (gh_environment; main's prints)
  P11 a failing gh is a failed run, not a dispatch                      (main: `p.returncode`)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "role_provisioning_dispatch.py"
WORKFLOW = REPO / ".github" / "workflows" / "gochara-role-provisioning-oneshot.yml"
OPS_FILE = FLEET / "executor_ops.json"

import importlib.util
_spec = importlib.util.spec_from_file_location("ky_lease_gate_fixtures", HERE / "test_executor_window_lease_gate.py")
lg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lg)

CONFIRM = "PROVISION-GOCHARA-ROLES"
WIRE_TAIL = "@/gochara,host=/cloudsql/madhav-astrology:asia-south1:amjis-postgres"
REAL_TAIL = "@/gochara?host=/cloudsql/madhav-astrology:asia-south1:amjis-postgres"
SENTINEL = "SENTINEL-NOT-A-REAL-SECRET-4f1c"


class Fake:
    """A fake gh: records argv and the NAMES of its environment, exits `code`."""

    def __init__(self, tmp_path, code=0):
        self.argv, self.envnames = tmp_path / "gh.argv", tmp_path / "gh.envnames"
        self.path = tmp_path / "fake-gh"
        self.path.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {self.argv}\nenv | cut -d= -f1 | sort > {self.envnames}\nexit {code}\n')
        self.path.chmod(0o755)

    def calls(self):
        return self.argv.read_text().splitlines() if self.argv.exists() else None


def run(tmp_path, world, *, mode="--execute", stage="create-roles", tail=WIRE_TAIL, confirm=CONFIRM, lease="MINE", request=None, gh_code=0, extra_env=None):
    fake = Fake(tmp_path, gh_code)
    cmd = [sys.executable, "-I", str(SCRIPT), mode, "--stage", stage, "--dsn_tail", tail, "--confirm", confirm,
           "--repo", str(world.repo), "--gh", str(fake.path)] + (["--window_lease_id", lease] if lease is not None else [])
    env = {**lg._env(), **(extra_env or {})}
    if request is not None: env["KY_OPERATION_REQUEST"] = json.dumps(request)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    return p, fake


def clean_world(tmp_path):
    return lg.World(tmp_path / "w", lg.table(("MINE", 5, "ACTIVE"), ("OLD", 5, "RELEASED")))


# ── P1
@pytest.mark.parametrize("kind", ["gochara_role_provisioning_dispatch", "gochara_role_provisioning_dispatch_dryrun"])
def test_p1_the_kinds_ship_disabled_with_a_script_that_exists(kind):
    entry = json.loads(OPS_FILE.read_text())["ops"][kind]
    assert next(iter(entry)) == "enabled" and entry["enabled"] is False
    assert (REPO / entry["script"]).is_file()


# ── P2
def test_p2_only_create_roles_is_served(tmp_path):
    w = clean_world(tmp_path)
    p, fake = run(tmp_path, w, stage="sealer-password")
    assert p.returncode == 1 and "stage must be create-roles" in p.stdout and fake.calls() is None
    (tmp_path / "ok").mkdir()
    p, fake = run(tmp_path / "ok", w)
    assert p.returncode == 0 and fake.calls() is not None, p.stdout                      # control: the same world dispatches with the served stage


# ── P3
@pytest.mark.parametrize("confirm", ["", "provision-gochara-roles", CONFIRM + " "])
def test_p3_only_the_exact_confirm_text_dispatches(tmp_path, confirm):
    p, fake = run(tmp_path, clean_world(tmp_path), confirm=confirm)
    assert p.returncode == 1 and "confirm must be exactly" in p.stdout and fake.calls() is None


# ── P4
def test_p4_a_foreign_active_lease_refuses(tmp_path):
    w = lg.World(tmp_path / "w", lg.table(("MINE", 5, "ACTIVE"), ("J-3", 5, "ACTIVE")))
    p, fake = run(tmp_path, w)
    assert p.returncode == 1 and "J-3" in p.stdout and fake.calls() is None


def test_p4_an_unreadable_lease_table_refuses(tmp_path):
    p, fake = run(tmp_path, lg.World(tmp_path / "w", None))
    assert p.returncode == 1 and p.stdout.startswith("REFUSED") and fake.calls() is None


# ── P5
def test_p5_the_window_lease_is_required_and_must_be_active(tmp_path):
    p, fake = run(tmp_path, lg.World(tmp_path / "w", lg.table(("OLD", 5, "RELEASED"))), lease=None)   # no lease is held at all: only the missing name stops it
    assert p.returncode == 1 and "window_lease_id" in p.stdout and fake.calls() is None
    (tmp_path / "b").mkdir()
    p, fake = run(tmp_path / "b", lg.World(tmp_path / "b" / "w", lg.table(("OLD", 5, "RELEASED"))), lease="OLD")   # named, but RELEASED
    assert p.returncode == 1 and "OLD" in p.stdout and fake.calls() is None


# ── P6
def test_p6_the_requests_own_lease_must_be_the_window_lease(tmp_path):
    p, fake = run(tmp_path, clean_world(tmp_path), request={"lease_id": "SOMEONE-ELSE"})
    assert p.returncode == 1 and "request's own lease_id" in p.stdout and fake.calls() is None
    (tmp_path / "ok").mkdir()
    p, fake = run(tmp_path / "ok", clean_world(tmp_path / "ok"), request={"lease_id": "MINE"})
    assert p.returncode == 0 and fake.calls() is not None, p.stdout


# ── P7
def workflow_inputs():
    text = WORKFLOW.read_text()
    block = text.split("workflow_dispatch:", 1)[1].split("\npermissions:", 1)[0]
    return set(re.findall(r"^      (\w+):\s*$", block, re.M))


def test_p7_a_clean_lease_dispatches_the_workflows_declared_inputs_on_main(tmp_path):
    p, fake = run(tmp_path, clean_world(tmp_path))
    assert p.returncode == 0 and p.stdout.splitlines()[-1].startswith("DISPATCHED"), p.stdout
    argv = fake.calls()
    assert argv[:4] == ["workflow", "run", "gochara-role-provisioning-oneshot.yml", "--ref"] and argv[4] == "main"
    given = dict(a.split("=", 1) for a in argv[5:] if a != "-f")
    assert argv[5::2] == ["-f"] * len(given)
    assert given == {"stage": "create-roles", "dsn_tail": REAL_TAIL, "confirm": CONFIRM}
    assert set(given) <= workflow_inputs() == {"stage", "dsn_tail", "confirm"}              # an input the workflow does not declare would 422 the dispatch


# ── P8
def test_p8_the_dry_run_runs_the_lease_gate_and_makes_no_gh_call(tmp_path):
    p, fake = run(tmp_path, clean_world(tmp_path), mode="--dry-run")
    assert p.returncode == 0 and "DRY RUN" in p.stdout and fake.calls() is None
    (tmp_path / "f").mkdir()
    w = lg.World(tmp_path / "f" / "w", lg.table(("MINE", 5, "ACTIVE"), ("J-3", 5, "ACTIVE")))
    p, fake = run(tmp_path / "f", w, mode="--dry-run")
    assert p.returncode == 1 and "J-3" in p.stdout and fake.calls() is None                 # a dry run that passes means the live dispatch would pass the gate


# ── P9
@pytest.mark.parametrize("tail,why", [
    ("/gochara", "plain @host/db"),                                                         # must start with @
    ("@host/db,host=a@b", "plain @host/db"),                                                 # a second @ would carry credentials
    ("@host/db,password=hunter2", "credential"),
    ("@host/db,a=b,c=d", "plain @host/db"),                                                 # `,` once at most
    ("@host/db?host=x", "plain @host/db"),                                                  # `?` cannot arrive through the executor and is not accepted
])
def test_p9_a_bad_dsn_tail_is_refused(tmp_path, tail, why):
    p, fake = run(tmp_path, clean_world(tmp_path), tail=tail)
    assert p.returncode == 1 and why in p.stdout and fake.calls() is None


# ── P10
def test_p10_no_credential_is_read_forwarded_or_printed(tmp_path):
    secrets = {"DATABASE_URL": SENTINEL, "ADMIN_DATABASE_URL": SENTINEL, "DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL": SENTINEL,
               "GH_TOKEN": SENTINEL, "GOCHARA_SEALER_PASSWORD_STAGING": SENTINEL}
    p, fake = run(tmp_path, clean_world(tmp_path), extra_env=secrets)
    assert p.returncode == 0, p.stdout
    assert SENTINEL not in p.stdout + p.stderr
    assert REAL_TAIL not in p.stdout and WIRE_TAIL not in p.stdout                           # only a digest prefix of the (non-secret) tail is shown
    assert not set(secrets) & set(fake.envnames.read_text().split())                         # gh never receives them


# ── P11
def test_p11_a_failing_gh_is_a_failed_run(tmp_path):
    p, fake = run(tmp_path, clean_world(tmp_path), gh_code=1)
    assert fake.calls() is not None and p.returncode == 1 and "FAILED" in p.stdout and "DISPATCHED" not in p.stdout
