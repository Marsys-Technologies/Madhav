"""Behavioural tests of platform/scripts/gochara-provision-roles.sh against a DISPOSABLE PostgreSQL (the native's ruling #1, option A).

The script runs for real; only `gcloud` is a recording shim (so the test can prove WHAT is written to Secret Manager and that the
password never appears anywhere else). The roles are cluster-level, so this suite runs ONLY against a cluster named explicitly by
GOCHARA_PROVISION_TEST_ADMIN_DSN (a loopback superuser DSN of a throwaway cluster — never a shared one): it drops and re-creates
`gochara_verifier`, `gochara_sealer` and a stand-in `cloudsqlsuperuser` there. Without the variable every test is skipped.
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytest

psycopg = pytest.importorskip("psycopg")

DSN = os.environ.get("GOCHARA_PROVISION_TEST_ADMIN_DSN", "")
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "gochara-provision-roles.sh"
PSQL = os.environ.get("GOCHARA_PROVISION_TEST_PSQL") or shutil.which("psql")
pytestmark = pytest.mark.skipif(not DSN or not PSQL, reason="NOT_RUN: set GOCHARA_PROVISION_TEST_ADMIN_DSN (a throwaway loopback cluster) and have psql")
TAIL = "@/amjis?host=/cloudsql/p:r:i"


def _admin():
    host = urlparse(DSN).hostname
    assert host in ("127.0.0.1", "localhost"), "refusing a non-loopback cluster"
    return psycopg.connect(DSN, autocommit=True, connect_timeout=3)


@pytest.fixture()
def world(tmp_path):
    with _admin() as c:
        for r in ("gochara_verifier", "gochara_sealer"):
            c.execute(f"DROP ROLE IF EXISTS {r}")
        c.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cloudsqlsuperuser') THEN CREATE ROLE cloudsqlsuperuser NOLOGIN; END IF; END $$")
    capture = tmp_path / "secret_stdin.txt"
    shim = tmp_path / "gcloud"
    shim.write_text(f'''#!/usr/bin/env bash
case "$*" in
  *"secrets versions add"*) cat > "{capture}" ; echo "$*" >> "{tmp_path}/gcloud_argv.txt" ;;
  *"secrets versions list"*) printf '1\\tenabled\\n' ;;
  *) echo "unexpected gcloud call: $*" >&2; exit 9 ;;
esac
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    yield {"tmp": tmp_path, "capture": capture, "gcloud": str(shim)}
    with _admin() as c:
        for r in ("gochara_verifier", "gochara_sealer"):
            c.execute(f"DROP ROLE IF EXISTS {r}")


def run(world, stage="create-roles", *, url=None, tail=TAIL, extra=None, psql=None):
    env = {**os.environ, "STAGE": stage, "ADMIN_DATABASE_URL": url or DSN, "GCLOUD_BIN": world["gcloud"], "PSQL_BIN": psql or PSQL,
           "DSN_TAIL": tail, "GCLOUD_PROJECT": "madhav-astrology", **(extra or {})}
    return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=120)


def visible(out) -> str:
    """Everything the workflow log would show: the runner CONSUMES `::add-mask::` lines (it masks the value), so they are not shown."""
    return "\n".join(l for l in (out.stdout + "\n" + out.stderr).splitlines() if not l.startswith("::add-mask::"))


def role(c, name):
    return c.execute("SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolinherit, rolconnlimit, rolpassword IS NULL"
                     " FROM pg_authid WHERE rolname = %s", (name,)).fetchone()


def test_create_roles_makes_both_roles_least_privileged_with_no_superuser_membership_and_writes_only_the_verifier_secret(world):
    out = run(world)
    assert out.returncode == 0, out.stdout + out.stderr
    with _admin() as c:
        v, s = role(c, "gochara_verifier"), role(c, "gochara_sealer")
        assert v[:8] == (True, False, False, False, False, False, False, 4) and v[8] is False, v          # login, nothing elevated, a password set
        assert s[:8] == (True, False, False, False, False, False, False, 2) and s[8] is True, s           # sealer: LOGIN but PASSWORD NULL — cannot authenticate
        for r in ("gochara_verifier", "gochara_sealer"):
            assert c.execute("SELECT pg_has_role(%s, 'cloudsqlsuperuser', 'MEMBER')", (r,)).fetchone()[0] is False
            assert c.execute("SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname=%s)"
                             " OR roleid = (SELECT oid FROM pg_roles WHERE rolname=%s)", (r, r)).fetchone()[0] == 0
    dsn = world["capture"].read_text()
    m = re.fullmatch(r"postgresql://gochara_verifier:([0-9a-f]{96})" + re.escape(TAIL), dsn)
    assert m, "the secret must be exactly the verifier DSN"
    # the password is in the secret store input and NOWHERE else a log could show
    assert m.group(1) not in visible(out)
    assert "gcloud sql users" not in out.stdout + out.stderr
    argv = (world["tmp"] / "gcloud_argv.txt").read_text()
    assert "secrets versions add gochara-verifier-db-url" in argv and "--data-file=-" in argv and m.group(1) not in argv
    facts = out.stdout
    assert "member_of_cloudsqlsuperuser=f" in facts and "sealer_rolpassword_is_null=t" in facts and "secret_version: 1\tenabled" in facts
    assert "created gochara_sealer: LOGIN PASSWORD NULL" in facts


def test_a_second_run_refuses_and_changes_nothing(world):
    assert run(world).returncode == 0
    before = world["capture"].read_text()
    with _admin() as c:
        snap = (role(c, "gochara_verifier"), role(c, "gochara_sealer"))
    again = run(world)
    assert again.returncode == 3 and "already exists" in again.stderr, again.stdout + again.stderr
    assert world["capture"].read_text() == before
    with _admin() as c:
        assert (role(c, "gochara_verifier"), role(c, "gochara_sealer")) == snap


def test_refuses_a_non_loopback_admin_connection_and_a_dsn_tail_that_carries_credentials(world):
    r = run(world, url="postgresql://postgres:x@10.9.9.9:5432/postgres")
    assert r.returncode == 2 and "loopback" in r.stderr
    for bad in ("@user:pass@host/db", "no-at-sign", "@/db?x=1;drop"):
        r = run(world, tail=bad)
        assert r.returncode == 2, (bad, r.stdout, r.stderr)
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0


def test_refuses_to_certify_membership_on_a_server_without_cloudsqlsuperuser(world):
    """Not Cloud SQL: the membership post-check cannot run, so the act is reported as failed (roles were created: the runbook's rollback applies)."""
    with _admin() as c:
        c.execute("DROP ROLE cloudsqlsuperuser")
    try:
        r = run(world)
        assert r.returncode == 4 and "cloudsqlsuperuser is absent" in r.stderr
        assert not world["capture"].exists()                       # no secret was written
    finally:
        with _admin() as c:
            c.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cloudsqlsuperuser') THEN CREATE ROLE cloudsqlsuperuser NOLOGIN; END IF; END $$")


def test_sealer_password_stage_sets_it_once_and_never_shows_it(world):
    assert run(world).returncode == 0
    staged = "ab" * 40
    r = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": staged})
    assert r.returncode == 0, r.stdout + r.stderr
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is False                # a password is now set
    assert staged not in visible(r)
    again = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": "cd" * 40})
    assert again.returncode == 3 and "already has a password" in again.stderr
    for bad in ("short", "zz" * 40):
        assert run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": bad}).returncode in (2, 3)


def test_the_nologin_fallback_when_password_null_is_not_accepted_then_2b_enables_login(world):
    """A psql shim rejects ONLY the sealer's `LOGIN ... PASSWORD NULL` creation; the script falls back to NOLOGIN (the role still exists) and act 2b makes it LOGIN."""
    shim = world["tmp"] / "psql_shim"
    shim.write_text(f'''#!/usr/bin/env bash
for a in "$@"; do case "$a" in *"CREATE ROLE gochara_sealer LOGIN"*) exit 1;; esac; done
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, psql=str(shim))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "created gochara_sealer: NOLOGIN (fallback" in r.stdout
    with _admin() as c:
        assert role(c, "gochara_sealer")[0] is False
    staged = "ef" * 40
    assert run(world, "sealer-password", psql=str(shim), extra={"SEALER_PASSWORD_STAGING": staged}).returncode == 0
    with _admin() as c:
        s = role(c, "gochara_sealer")
        assert s[0] is True and s[8] is False


def test_the_secret_write_happens_before_the_role_password_is_set(world):
    """If Secret Manager fails the role must still have NO password (never an unknown password nobody holds)."""
    broken = world["tmp"] / "gcloud_broken"
    broken.write_text("#!/usr/bin/env bash\nexit 1\n")
    broken.chmod(broken.stat().st_mode | stat.S_IEXEC)
    r = run(world, extra={"GCLOUD_BIN": str(broken)})
    assert r.returncode == 5 and "Secret Manager failed" in r.stderr
    with _admin() as c:
        assert role(c, "gochara_verifier")[8] is True               # still PASSWORD NULL


def test_a_role_that_ends_up_in_cloudsqlsuperuser_fails_the_act_before_any_secret_is_written(world):
    """What `gcloud sql users create` would have done: a shim makes the new verifier a member of cloudsqlsuperuser right after it is created; the
    post-check must REFUSE (exit 4) before the password is generated or any secret written."""
    shim = world["tmp"] / "psql_member_shim"
    shim.write_text(f'''#!/usr/bin/env bash
"{PSQL}" "$@" || exit $?
for a in "$@"; do case "$a" in *"CREATE ROLE gochara_verifier LOGIN"*) "{PSQL}" "{DSN}" -X -q -c "GRANT cloudsqlsuperuser TO gochara_verifier" >/dev/null;; esac; done
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, psql=str(shim))
    assert r.returncode == 4 and "member of cloudsqlsuperuser" in r.stderr, r.stdout + r.stderr
    assert not world["capture"].exists()
