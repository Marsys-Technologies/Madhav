"""Behavioural tests of platform/scripts/gochara-provision-roles.sh against a DISPOSABLE, CLOUD-SQL-SHAPED PostgreSQL (the native's ruling #1, option A).

The script runs for real; only `gcloud` is a recording shim (so the test can prove WHAT is written to Secret Manager, under WHICH permission model, and that the password never
appears anywhere else). Each module run creates its OWN throwaway cluster (initdb in a temp directory, scram-sha-256 authentication on every line of pg_hba, loopback only,
removed afterwards) shaped like Cloud SQL where it matters (Fable F-R12-3): the script's admin role is NOT a superuser (`CREATEROLE CREATEDB`, a member of a stand-in
`cloudsqlsuperuser`), so **pg_authid is unreadable to it** — the password-state logic must work without it — and passwords are really checked (a role with PASSWORD NULL cannot
authenticate). A separate superuser connection is used only to ASSERT. Needs the PostgreSQL binaries (initdb, pg_ctl, psql); set GOCHARA_PROVISION_TEST_PGBIN to their directory
(default: next to `psql` on PATH). Never touches any other server.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

from . import _disposable_guard as guard

psycopg = pytest.importorskip("psycopg")

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "gochara-provision-roles.sh"
BIN = Path(os.environ.get("GOCHARA_PROVISION_TEST_PGBIN") or (os.path.dirname(shutil.which("psql") or "")))
PSQL = str(BIN / "psql") if (BIN / "psql").exists() else None
pytestmark = pytest.mark.skipif(not (BIN / "initdb").exists() or not (BIN / "pg_ctl").exists() or not PSQL,
                                reason="NOT_RUN: PostgreSQL binaries (initdb, pg_ctl, psql) not found — set GOCHARA_PROVISION_TEST_PGBIN")
TAIL = "@/amjis?host=/cloudsql/p:r:i"
ADMIN_PW = "Zm4rk3rAdminPw"          # also the argv/output marker: it must appear in NO psql argument list and NO output
DSN = ADMIN_URL = SUDSN = ""         # set by the `cluster` fixture


def _admin():
    """A SUPERUSER connection, for assertions only (the script never uses it)."""
    guard.assert_disposable_dsn(SUDSN)
    c = psycopg.connect(SUDSN, autocommit=True, connect_timeout=3)
    guard.assert_connected_to(c)
    return c


@pytest.fixture(scope="module")
def cluster(tmp_path_factory):
    global DSN, ADMIN_URL, SUDSN
    data = tmp_path_factory.mktemp("pgscram") / "data"
    sock = Path(tempfile.mkdtemp(prefix="b6pg"))
    pwfile = tmp_path_factory.mktemp("pgpw") / "pw"
    pwfile.write_text("testsuperpw")
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    subprocess.run([str(BIN / "initdb"), "-D", str(data), "-U", "postgres", "-A", "scram-sha-256", f"--pwfile={pwfile}", "-E", "UTF8"], check=True, capture_output=True, env=env)
    subprocess.run([str(BIN / "pg_ctl"), "-D", str(data), "-o", f"-p {port} -k {sock} -c listen_addresses=127.0.0.1", "-l", str(data.parent / "log"), "-w", "start"],
                   check=True, capture_output=True, env=env)
    SUDSN = f"postgresql://postgres:testsuperpw@127.0.0.1:{port}/postgres"
    ADMIN_URL = f"postgresql://pgadmin:{ADMIN_PW}@127.0.0.1:{port}/postgres"
    DSN = ADMIN_URL
    try:
        with _admin() as c:
            c.execute("CREATE ROLE cloudsqlsuperuser NOLOGIN")
            c.execute(f"CREATE ROLE pgadmin LOGIN CREATEROLE CREATEDB PASSWORD '{ADMIN_PW}' IN ROLE cloudsqlsuperuser")
        # the Cloud SQL shape: the script's admin role cannot read pg_authid
        with psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3) as a:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                a.execute("SELECT rolpassword FROM pg_authid LIMIT 1")
        yield {"port": port}
    finally:
        subprocess.run([str(BIN / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "stop"], capture_output=True, env=env)
        shutil.rmtree(sock, ignore_errors=True)


@pytest.fixture()
def world(tmp_path, cluster):
    with _admin() as c:
        for r in ("gochara_verifier", "gochara_sealer"):
            c.execute(f"DROP ROLE IF EXISTS {r}")
        c.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cloudsqlsuperuser') THEN CREATE ROLE cloudsqlsuperuser NOLOGIN; END IF; END $$")
    capture = tmp_path / "secret_stdin.txt"
    shim = tmp_path / "gcloud"
    # the shim ENFORCES a permission model (GCLOUD_PERMS, default = roles/secretmanager.secretVersionManager's three verbs the script uses) and records every verb it is asked to run
    shim.write_text(f'''#!/usr/bin/env bash
verb=""; case "$*" in *"secrets versions add"*) verb=add;; *"secrets versions destroy"*) verb=destroy;; *"secrets versions list"*) verb=list;; *"secrets versions access"*) verb=access;; esac
echo "$verb" >> "{tmp_path}/gcloud_verbs.txt"
[ -n "$verb" ] || {{ echo "unexpected gcloud call: $*" >&2; exit 9; }}
case ",${{GCLOUD_PERMS:-add,list,destroy}}," in *",$verb,"*) ;; *) echo "PERMISSION_DENIED: $verb (the shim models the declared IAM roles)" >&2; exit 1 ;; esac
case "$verb" in
  add) cat > "{capture}" ; echo "$*" >> "{tmp_path}/gcloud_argv.txt"; echo "projects/1/secrets/gochara-verifier-db-url/versions/7" ;;
  destroy) echo "$*" >> "{tmp_path}/gcloud_destroy.txt" ;;
  list) printf '1\\tenabled\\n' ;;
esac
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    yield {"tmp": tmp_path, "capture": capture, "gcloud": str(shim)}
    with _admin() as c:
        for r in ("gochara_verifier", "gochara_sealer"):
            c.execute(f"DROP ROLE IF EXISTS {r}")


def run(world, stage="create-roles", *, url=None, tail=TAIL, extra=None, psql=None):
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("PG")}, "STAGE": stage, "ADMIN_DATABASE_URL": url or ADMIN_URL, "GCLOUD_BIN": world["gcloud"], "PSQL_BIN": psql or PSQL,
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
    assert "member_of_cloudsqlsuperuser=f" in facts and "secret_version: 1\tenabled" in facts
    assert "sealer_recorded_state=gochara-provision:sealer-password-null" in facts and "sealer_authentication_with_a_random_password=refused" in facts
    assert "sealer_rolpassword_is_null" not in facts and "pg_authid" not in facts                     # the state is recorded + probed, never read from pg_authid
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


@pytest.mark.parametrize("url", [
    "postgresql://postgres:x@10.9.9.9:5432/postgres",
    "postgresql://postgres:x@127.0.0.1:5432,db.prod.example.com:5432/postgres",             # multi-host: libpq can fail over to the second
    "postgresql://postgres:x@db.prod.example.com:5432,127.0.0.1:5432/postgres",
    "postgresql://postgres:x@127.0.0.1:5432/postgres?host=db.prod.example.com",             # query-string overrides
    "postgresql://postgres:x@127.0.0.1:5432/postgres?hostaddr=10.9.9.9",
    "postgresql://postgres:x@127.0.0.1:5432/postgres?service=prod",
    "postgresql:///postgres?host=db.prod.example.com",
    "postgresql://postgres:x@localhost.evil.example.com:5432/postgres",                      # a host that merely STARTS with a loopback name
    "host=127.0.0.1 dbname=postgres",                                                         # not a URL
])
def test_refuses_every_non_loopback_or_redirectable_admin_connection_without_calling_psql(world, url):
    calls = world["tmp"] / "psql_calls.txt"
    shim = world["tmp"] / "psql_recorder"
    shim.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\nexit 1\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, url=url, psql=str(shim))
    assert r.returncode == 2 and ("loopback" in r.stderr or "postgres:// URL" in r.stderr), (url, r.stdout, r.stderr)
    assert not calls.exists(), "the script must refuse BEFORE it connects anywhere"


@pytest.mark.parametrize("var", ["PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_refuses_an_environment_override_of_the_connection(world, var):
    r = run(world, extra={var: "db.prod.example.com"})
    assert r.returncode == 2 and var in r.stderr


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
        with _admin() as c:                                        # ...and this run's roles were ROLLED BACK (nothing half-done is left)
            assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0
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
    assert again.returncode == 3 and "recorded state is password-SET" in again.stderr
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


def test_a_secret_store_failure_rolls_the_roles_back_and_no_password_was_ever_set(world):
    """The secret write happens BEFORE the role password: if it fails, the role never had a password and this run's roles are dropped."""
    broken = world["tmp"] / "gcloud_broken"
    broken.write_text("#!/usr/bin/env bash\nexit 1\n")
    broken.chmod(broken.stat().st_mode | stat.S_IEXEC)
    r = run(world, extra={"GCLOUD_BIN": str(broken)})
    assert r.returncode == 5 and "Secret Manager failed" in r.stderr and "dropped role gochara_verifier" in r.stderr, r.stderr
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0


def test_an_alter_role_failure_destroys_the_new_secret_version_drops_the_roles_and_never_shows_the_password(world):
    """A server error can QUOTE the failing statement (and so the password). The shim fails every ALTER ROLE and prints the statement on stderr, as a server
    syntax error would: the script must discard that stderr, destroy the version it just wrote, drop both roles and leak nothing."""
    shim = world["tmp"] / "psql_alter_shim"
    shim.write_text(f'''#!/usr/bin/env bash
prev=""; for a in "$@"; do if [ "$prev" = "-f" ] && [ "$a" = "-" ]; then stmt="$(cat)"; echo "ERROR: syntax error near LINE 1: $stmt" >&2; exit 1; fi; prev="$a"; done
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, psql=str(shim))
    assert r.returncode == 5 and "ALTER ROLE PASSWORD failed" in r.stderr, r.stdout + r.stderr
    secret = world["capture"].read_text()
    pw = re.search(r"gochara_verifier:([0-9a-f]{96})@", secret).group(1)
    assert pw not in visible(r)
    assert "versions/7" in (world["tmp"] / "gcloud_destroy.txt").read_text() or " 7 " in (world["tmp"] / "gcloud_destroy.txt").read_text()
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0


def test_a_role_that_ends_up_in_cloudsqlsuperuser_fails_the_act_before_any_secret_is_written_and_is_rolled_back(world):
    """What `gcloud sql users create` would have done: a shim makes the new verifier a member of cloudsqlsuperuser right after it is created; the
    post-check must REFUSE (exit 4) before the password is generated or any secret written, and this run's roles are dropped."""
    shim = world["tmp"] / "psql_member_shim"
    shim.write_text(f'''#!/usr/bin/env bash
"{PSQL}" "$@" || exit $?
for a in "$@"; do case "$a" in *"CREATE ROLE gochara_verifier LOGIN"*) "{PSQL}" "{SUDSN}" -X -q -c "GRANT cloudsqlsuperuser TO gochara_verifier" >/dev/null;; esac; done
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, psql=str(shim))
    assert r.returncode == 4 and "member of cloudsqlsuperuser" in r.stderr, r.stdout + r.stderr
    assert not world["capture"].exists()
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0



# ── round 12 (R12-3/4/5): the permission model, the admin secret out of argv, sealer activation made transactional and compensated ───────────────

def verbs(world):
    f = world["tmp"] / "gcloud_verbs.txt"
    return f.read_text().split() if f.exists() else []


def test_the_script_asks_secret_manager_for_exactly_add_and_list_on_success_and_never_for_access(world):
    """Permission model (act 11: roles/secretmanager.secretVersionManager on the verifier secret ONLY): the success path uses `versions add` and `versions list`, and the payload is
    never read — no `versions access`."""
    r = run(world)
    assert r.returncode == 0, r.stdout + r.stderr
    assert verbs(world) == ["add", "list"], verbs(world)


def test_under_the_version_adder_only_model_the_run_fails_and_reports_that_it_cannot_destroy_the_version(world):
    """The model Codex tested (R12-3): `secretVersionAdder` alone lets the script ADD but neither LIST nor DESTROY. The run must fail, drop its roles and say — loudly, exit 70 — that the
    version could not be destroyed (which is why the runbook grants secretVersionManager instead)."""
    r = run(world, extra={"GCLOUD_PERMS": "add"})
    assert r.returncode == 70, r.stdout + r.stderr
    assert "listing the secret versions failed" in r.stderr and "ROLLBACK INCOMPLETE: destroy secret version 7" in r.stderr
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer')").fetchone()[0] == 0
    assert verbs(world) == ["add", "list", "destroy"]


def _argv_logger(world, name="psql_argv_logger"):
    log = world["tmp"] / f"{name}.log"
    shim = world["tmp"] / name
    shim.write_text(f'''#!/usr/bin/env bash
echo "$*" >> "{log}"
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    return shim, log


def test_the_admin_connection_is_never_in_any_psql_argument_list(world):
    """R12-3: `ADMIN_DATABASE_URL` used to be passed positionally to psql. Now the connection comes from the process environment (PG*) — a password marker in the URL appears in no argv,
    no output, and psql still connects."""
    shim, log = _argv_logger(world)
    marker = ADMIN_PW
    url = ADMIN_URL
    assert marker in url
    r = run(world, url=url, psql=str(shim))
    assert r.returncode == 0, r.stdout + r.stderr
    argv = log.read_text()
    assert argv.strip() and marker not in argv and "postgresql://" not in argv and "127.0.0.1" not in argv, argv[:400]
    assert marker not in visible(r)


def _sealer_world(world, *, nologin=False):
    """create-roles done (both roles PASSWORD NULL); returns nothing."""
    shim = None
    if nologin:
        shim = world["tmp"] / "psql_fallback_shim"
        shim.write_text(f'''#!/usr/bin/env bash
for a in "$@"; do case "$a" in *"CREATE ROLE gochara_sealer LOGIN"*) exit 1;; esac; done
exec "{PSQL}" "$@"
''')
        shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, psql=str(shim) if shim else None)
    assert r.returncode == 0, r.stdout + r.stderr
    return shim


@pytest.mark.parametrize("nologin", [False, True], ids=["login_sealer", "nologin_fallback_sealer"])
def test_a_failed_activation_postcondition_commits_nothing_and_the_compensation_is_verified(world, nologin):
    """R12-4: activation and its postconditions are ONE transaction. Make the postcondition fail (the sealer is in cloudsqlsuperuser): nothing is committed, the compensation runs anyway and is
    VERIFIED (password NULL; NOLOGIN restored if it was NOLOGIN), the exit is non-zero and the recovery message says the secrets are recovery material."""
    shim = _sealer_world(world, nologin=nologin)
    with _admin() as c:
        c.execute("GRANT cloudsqlsuperuser TO gochara_sealer")
        before = role(c, "gochara_sealer")
    staged = "ab" * 40
    r = run(world, "sealer-password", psql=str(shim) if shim else None, extra={"SEALER_PASSWORD_STAGING": staged})
    assert r.returncode == 5 and "compensated and VERIFIED" in r.stderr and "recovery material" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        after = role(c, "gochara_sealer")
    assert after == before and after[8] is True, (before, after)           # password still NULL, login attribute exactly as before
    assert staged not in visible(r)


def test_a_failure_after_the_activation_committed_is_compensated_and_verified(world):
    """R12-4: the first read-only fact query AFTER the commit fails (what Codex injected): exit non-zero AND the password is reset to NULL and the reset verified — never a silent active credential."""
    _sealer_world(world)
    shim = world["tmp"] / "psql_post_commit_failure"
    flag = world["tmp"] / "activated.flag"
    shim.write_text(f'''#!/usr/bin/env bash
prev=""; for a in "$@"; do if [ "$prev" = "-f" ] && [ "$a" = "-" ]; then stmt="$(cat)"; printf '%s' "$stmt" | "{PSQL}" "$@" || exit $?; case "$stmt" in *"LOGIN PASSWORD"*) touch "{flag}";; esac; exit 0; fi; prev="$a"; done
if [ -f "{flag}" ]; then for a in "$@"; do case "$a" in *"rolname, rolcanlogin"*) exit 31;; esac; done; fi
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    staged = "cd" * 40
    r = run(world, "sealer-password", psql=str(shim), extra={"SEALER_PASSWORD_STAGING": staged})
    assert r.returncode != 0 and flag.exists(), r.stdout + r.stderr          # the activation DID commit...
    assert "compensated and VERIFIED" in r.stderr, r.stderr                   # ...and was compensated
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is True                           # rolpassword IS NULL again
    assert staged not in visible(r)


def test_an_unverifiable_compensation_exits_70_and_says_the_sealer_may_be_active(world):
    _sealer_world(world)
    shim = world["tmp"] / "psql_compensation_fails"
    flag = world["tmp"] / "activated2.flag"
    shim.write_text(f'''#!/usr/bin/env bash
prev=""; for a in "$@"; do if [ "$prev" = "-f" ] && [ "$a" = "-" ]; then stmt="$(cat)"; printf '%s' "$stmt" | "{PSQL}" "$@" || exit $?; touch "{flag}"; exit 0; fi; prev="$a"; done
if [ -f "{flag}" ]; then for a in "$@"; do case "$a" in *"rolname, rolcanlogin"*) exit 31;; *"PASSWORD NULL"*) exit 1;; esac; done; fi
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, "sealer-password", psql=str(shim), extra={"SEALER_PASSWORD_STAGING": "ef" * 40})
    assert r.returncode == 70 and "ROLLBACK INCOMPLETE — THE SEALER MAY BE ACTIVE" in r.stderr and "BEFORE deleting any secret" in r.stderr, r.stdout + r.stderr


def test_a_cancelled_run_is_compensated(world):
    """R12-4/R12-3: the runner CANCELS a run by signalling its process group. A SIGTERM while the activation is in flight must still run the compensation (the EXIT trap)."""
    import signal
    import time
    _sealer_world(world)
    shim = world["tmp"] / "psql_hangs_in_activation"
    started = world["tmp"] / "in_flight.flag"
    shim.write_text(f'''#!/usr/bin/env bash
prev=""; for a in "$@"; do if [ "$prev" = "-f" ] && [ "$a" = "-" ]; then cat > /dev/null; touch "{started}"; sleep 60; exit 0; fi; prev="$a"; done
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("PG")}, "STAGE": "sealer-password", "ADMIN_DATABASE_URL": ADMIN_URL, "GCLOUD_BIN": world["gcloud"],
           "PSQL_BIN": str(shim), "SEALER_PASSWORD_STAGING": "12" * 40}
    p = subprocess.Popen(["bash", str(SCRIPT)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    for _ in range(100):
        if started.exists():
            break
        time.sleep(0.1)
    assert started.exists(), "the activation never started"
    os.killpg(p.pid, signal.SIGTERM)                       # what the runner does on cancel: the whole process group
    out, err = p.communicate(timeout=60)
    assert p.returncode == 143 and "compensated and VERIFIED" in err, (p.returncode, out, err)
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is True


def test_the_preexisting_password_check_still_refuses_to_overwrite(world):
    _sealer_world(world)
    assert run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": "ab" * 40}).returncode == 0
    again = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": "cd" * 40})
    assert again.returncode == 3 and "recorded state is password-SET" in again.stderr


# ── Fable F-R12-3: the password state without pg_authid (the admin role of this mirror cannot read it, as on Cloud SQL) ─────────────────────────────

def _login(user, password):
    import psycopg as pg
    port = SUDSN.rsplit(":", 1)[1].split("/")[0]
    return pg.connect(f"host=127.0.0.1 port={port} dbname=postgres user={user} password={password}", connect_timeout=3)


def test_the_sealer_really_cannot_authenticate_until_activation_and_can_afterwards_with_the_admin_unable_to_read_pg_authid(world):
    """The whole point of the mirror: scram is enforced and the admin cannot read pg_authid, yet create-roles and sealer-password complete — the state is recorded (a role comment)
    and PROBED (authentication), never read from pg_authid."""
    import psycopg as pg
    assert run(world).returncode == 0
    for pw in ("anything", ""):                                               # PASSWORD NULL: no password authenticates
        with pytest.raises(pg.OperationalError):
            _login("gochara_sealer", pw)
    staged = "ab" * 40
    r = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": staged})
    assert r.returncode == 0, r.stdout + r.stderr
    with _login("gochara_sealer", staged) as c:                               # activation is OBSERVABLE
        assert c.execute("SELECT current_user").fetchone()[0] == "gochara_sealer"
    with pytest.raises(pg.OperationalError):
        _login("gochara_sealer", "cd" * 40)
    with _admin() as c:
        assert c.execute("SELECT shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='gochara_sealer'").fetchone()[0] == "gochara-provision:sealer-password-set"


def test_a_sealer_with_no_recorded_password_null_state_is_refused_not_activated(world):
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("COMMENT ON ROLE gochara_sealer IS NULL")                  # its state is now UNKNOWN (not created by this one-shot, or tampered with)
    r = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": "ab" * 40})
    assert r.returncode == 3 and "no recorded password-null state" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is True                          # untouched


def test_a_sealer_that_already_authenticates_with_the_staged_password_is_refused(world):
    assert run(world).returncode == 0
    staged = "ef" * 40
    with _admin() as c:
        c.execute(f"ALTER ROLE gochara_sealer PASSWORD '{staged}'")           # something else set it, but the recorded marker still says password-null
    r = run(world, "sealer-password", extra={"SEALER_PASSWORD_STAGING": staged})
    assert r.returncode == 3 and "already authenticates" in r.stderr, r.stdout + r.stderr


def test_an_activation_that_cannot_be_observed_is_compensated_and_verified(world):
    """If the sealer cannot authenticate AFTER the commit (the probe fails), the run fails and compensates."""
    assert run(world).returncode == 0
    shim = world["tmp"] / "psql_login_always_fails"
    shim.write_text(f'#!/usr/bin/env bash\n[ "${{PGUSER:-}}" = "gochara_sealer" ] && exit 2\nexec "{PSQL}" "$@"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, "sealer-password", psql=str(shim), extra={"SEALER_PASSWORD_STAGING": "12" * 40})
    assert r.returncode == 5 and "cannot authenticate after activation" in r.stderr and "compensated and VERIFIED" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is True
        assert c.execute("SELECT shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='gochara_sealer'").fetchone()[0] == "gochara-provision:sealer-password-null"
