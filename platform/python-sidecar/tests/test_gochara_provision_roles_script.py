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
MIGRATOR_PW = "Zm4rk3rMigratorPw"    # the same marker discipline for the protected data_plane_migrator route (stage grant-l1-reads)
DSN = ADMIN_URL = MIGRATOR_URL = SUDSN = ""         # set by the `cluster` fixture


def _admin():
    """A SUPERUSER connection, for assertions only (the script never uses it)."""
    guard.assert_disposable_dsn(SUDSN)
    c = psycopg.connect(SUDSN, autocommit=True, connect_timeout=3)
    guard.assert_connected_to(c)
    return c


@pytest.fixture(scope="module")
def cluster(tmp_path_factory):
    global DSN, ADMIN_URL, MIGRATOR_URL, SUDSN
    data = tmp_path_factory.mktemp("pgscram") / "data"
    pwfile = tmp_path_factory.mktemp("pgpw") / "pw"
    pwfile.write_text("testsuperpw")
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    subprocess.run([str(BIN / "initdb"), "-D", str(data), "-U", "postgres", "-A", "scram-sha-256", f"--pwfile={pwfile}", "-E", "UTF8"], check=True, capture_output=True, env=env)
    subprocess.run([str(BIN / "pg_ctl"), "-D", str(data), "-o", f"-p {port} -c unix_socket_directories= -c listen_addresses=127.0.0.1", "-l", str(data.parent / "log"), "-w", "start"],
                   check=True, capture_output=True, env=env)
    SUDSN = f"postgresql://postgres:testsuperpw@127.0.0.1:{port}/postgres"
    ADMIN_URL = f"postgresql://pgadmin:{ADMIN_PW}@127.0.0.1:{port}/postgres"
    MIGRATOR_URL = f"postgresql://data_plane_migrator:{MIGRATOR_PW}@127.0.0.1:{port}/postgres"
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


def run(world, stage="create-roles", *, url=None, tail=TAIL, extra=None, psql=None, migrator=None):
    """`migrator`: the protected data_plane_migrator URL (workflow env MIGRATOR_DATABASE_URL). Default: supplied for stage grant-l1-reads only (as the workflow does for that stage's run
    step — the env block is the same for every stage, so the other stages' tests also pass it; "" omits it)."""
    mig = MIGRATOR_URL if migrator is None else migrator
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("PG")}, "STAGE": stage, "ADMIN_DATABASE_URL": url or ADMIN_URL, "GCLOUD_BIN": world["gcloud"], "PSQL_BIN": psql or PSQL,
           "DSN_TAIL": tail, "GCLOUD_PROJECT": "madhav-astrology", **({"MIGRATOR_DATABASE_URL": mig} if mig else {}), **(extra or {})}
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


# ── J-4b-a55j (A6 D-40, SR-GRANTS-MINIMAL / SR-A55J-A55M-RESCOPE): the L1 read grants and the sealer credential, both inside this one-shot ─────────────
# Sources: migration 1378 header lines 53-57 ("NOT HERE, ON PURPOSE": both principals need SELECT on chart_facts and chart_dashas, nothing else, provisioned before the first
# verification run); the runbook's "L1 read ACLs" section; SR-GRANTS-MINIMAL (the one-shot workflow generates the sealer credential straight into Secret Manager, never printed).
L1_TABLES = ("chart_facts", "chart_dashas")
PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


OWNERS = ("data_plane_schema_owner", "data_plane_l1_owner")
GOCHARA = ("gochara_verifier", "gochara_sealer")


@pytest.fixture()
def l1(world):
    """The PRODUCTION TOPOLOGY after the data-plane cutover (STEP1_DIAG §2; platform/scripts/data-plane-ownership-preflight.ts:215-322,358-361): schema public is owned by the NOLOGIN
    data_plane_schema_owner with PUBLIC revoked, the L1 tables by the NOLOGIN data_plane_l1_owner, and data_plane_migrator (NOINHERIT, USAGE on public and SELECT on the L1 tables, as the
    cutover's fixed lists give it) is a MEMBER of both owner roles. The script's ownership admin (`pgadmin`, the Cloud SQL `postgres` stand-in) owns nothing and belongs to no owner
    role. A third L1 table must stay untouched. The original schema owner and PUBLIC USAGE are restored afterwards."""
    with _admin() as c:
        owner = c.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'").fetchone()[0]
        for o in OWNERS:
            c.execute(f"CREATE ROLE {o} NOLOGIN NOINHERIT")
        c.execute(f"CREATE ROLE data_plane_migrator LOGIN NOINHERIT PASSWORD '{MIGRATOR_PW}'")
        c.execute("GRANT data_plane_schema_owner, data_plane_l1_owner TO data_plane_migrator")
        c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
        c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        c.execute("GRANT USAGE ON SCHEMA public TO data_plane_migrator")
        c.execute("GRANT USAGE, CREATE ON SCHEMA public TO data_plane_l1_owner")          # preflight.ts:304,310: the L1 owner enters (and creates in) public — the schema owner needs no more
        for t in (*L1_TABLES, "chart_divisionals"):
            c.execute(f"DROP TABLE IF EXISTS public.{t}")
            c.execute(f"CREATE TABLE public.{t} (id int)")
            c.execute(f"ALTER TABLE public.{t} OWNER TO data_plane_l1_owner")
            c.execute(f"GRANT SELECT ON public.{t} TO data_plane_migrator")
    yield
    with _admin() as c:
        for t in (*L1_TABLES, "chart_divisionals"):
            c.execute(f"DROP TABLE IF EXISTS public.{t}")
        c.execute(f"ALTER SCHEMA public OWNER TO {owner}")                  # first: revoking from the OWNER would strip the owner's own entries
        for r in (*GOCHARA, *OWNERS, "data_plane_migrator", "other_member"):   # a role holding a schema privilege cannot be dropped
            c.execute(f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{r}') THEN REVOKE ALL ON SCHEMA public FROM {r}; END IF; END $$")
        c.execute(f"GRANT ALL ON SCHEMA public TO {owner}")
        c.execute("GRANT USAGE ON SCHEMA public TO PUBLIC")
        c.execute("DROP ROLE IF EXISTS other_member")
        c.execute("DROP ROLE data_plane_migrator")
        for o in OWNERS:
            c.execute(f"DROP ROLE {o}")


def held(role_name, table):
    with _admin() as c:
        return {p for p in PRIVS if c.execute("SELECT has_table_privilege(%s, %s, %s)", (role_name, f"public.{table}", p)).fetchone()[0]}


def grant_option(role_name, table):
    with _admin() as c:
        return any(c.execute("SELECT has_table_privilege(%s, %s, %s)", (role_name, f"public.{table}", f"{p} WITH GRANT OPTION")).fetchone()[0] for p in PRIVS)


def schema_priv(role_name, priv):
    with _admin() as c:
        return c.execute("SELECT has_schema_privilege(%s, 'public', %s)", (role_name, priv)).fetchone()[0]


def nothing_granted():
    assert all(held(r, t) == set() for r in GOCHARA for t in L1_TABLES), "an L1 grant was committed"
    assert all(schema_priv(r, "USAGE") is False for r in GOCHARA), "a schema grant was committed"


def test_the_ownership_admin_login_cannot_grant_on_public_or_the_l1_tables_in_the_production_topology(world, l1):  # claim F1/F3 (STEP1_DIAG §2-3: why the old route was REFUSED)
    """The topology oracle itself: the ownership admin owns nothing and is in no owner role, so PostgreSQL gives it neither the schema nor the table GRANT (PostgreSQL docs, GRANT: only the
    owner, a member of the owner, or a holder of the grant option can grant). Grants to a Gochara role were never possible over ADMIN_DATABASE_URL — and then `public` is not even enterable."""
    import psycopg as pg
    assert run(world).returncode == 0
    assert schema_priv("pgadmin", "USAGE") is False and held("pgadmin", "chart_facts") == set()
    with psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3) as a:
        with pytest.raises(pg.errors.InsufficientPrivilege):
            a.execute("GRANT SELECT ON public.chart_facts TO gochara_verifier")
        with pytest.raises(pg.errors.InsufficientPrivilege):
            a.execute("GRANT USAGE ON SCHEMA public TO gochara_verifier")
        with pytest.raises(pg.errors.InsufficientPrivilege):
            a.execute("SELECT to_regclass('public.chart_facts')")                  # the probe whose failure the old stage misreported as "does not exist"


def test_grant_l1_reads_gives_both_principals_select_on_exactly_the_two_l1_tables_and_nothing_else(world, l1):  # claim G1 (1378 header lines 53-57) — over the migrator route, as the owners
    assert run(world).returncode == 0
    r = run(world, "grant-l1-reads")
    assert r.returncode == 0, r.stdout + r.stderr
    for who in GOCHARA:
        for t in L1_TABLES:
            assert held(who, t) == {"SELECT"}, (who, t)           # read only: no write, no REFERENCES/TRIGGER
            assert grant_option(who, t) is False, (who, t)        # and no right to pass it on
        assert held(who, "chart_divisionals") == set(), who       # a third L1 table is not widened
    assert verbs(world) == ["add", "list"]                         # this stage touches no secret


def test_the_grants_are_recorded_as_issued_by_the_owning_roles_not_by_the_migrator(world, l1):  # claim G5 (SR-STEP1-MIGRATOR-SETROLE: SET LOCAL ROLE to the owners; the deploy gate reads these ACLs)
    assert run(world).returncode == 0
    assert run(world, "grant-l1-reads").returncode == 0
    with _admin() as c:
        tbl = c.execute("SELECT DISTINCT pg_get_userbyid(a.grantor), r.rolname FROM pg_class cl CROSS JOIN LATERAL aclexplode(cl.relacl) a JOIN pg_roles r ON r.oid=a.grantee"
                        " WHERE cl.relname IN ('chart_facts','chart_dashas') AND r.rolname = ANY(%s)", (list(GOCHARA),)).fetchall()
        sch = c.execute("SELECT DISTINCT pg_get_userbyid(a.grantor), r.rolname FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a JOIN pg_roles r ON r.oid=a.grantee"
                        " WHERE n.nspname='public' AND r.rolname = ANY(%s)", (list(GOCHARA),)).fetchall()
    assert sorted(tbl) == [("data_plane_l1_owner", "gochara_sealer"), ("data_plane_l1_owner", "gochara_verifier")], tbl
    assert sorted(sch) == [("data_plane_schema_owner", "gochara_sealer"), ("data_plane_schema_owner", "gochara_verifier")], sch


def test_grant_l1_reads_without_the_migrator_route_refuses_and_changes_nothing(world, l1):  # claim G6 (the ownership-admin route is not accepted for this stage)
    assert run(world).returncode == 0
    r = run(world, "grant-l1-reads", migrator="")
    assert r.returncode != 0 and "MIGRATOR_DATABASE_URL" in r.stderr, r.stdout + r.stderr
    nothing_granted()
    # ...and the admin URL offered AS the migrator route is refused by the identity guard, before any change
    r = run(world, "grant-l1-reads", migrator=ADMIN_URL)
    assert r.returncode == 2 and "data_plane_migrator" in r.stderr, r.stdout + r.stderr
    nothing_granted()


def test_grant_l1_reads_refuses_any_login_that_is_not_exactly_the_migrator_even_with_owner_membership(world, l1):  # claim G7 (identity guard, exit 2)
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("CREATE ROLE other_member LOGIN PASSWORD 'testotherpw'")
        c.execute("GRANT data_plane_schema_owner, data_plane_l1_owner TO other_member")
    port = re.search(r":(\d+)/", ADMIN_URL).group(1)
    r = run(world, "grant-l1-reads", migrator=f"postgresql://other_member:testotherpw@127.0.0.1:{port}/postgres")
    assert r.returncode == 2 and "session_user 'other_member'" in r.stderr, r.stdout + r.stderr
    nothing_granted()


@pytest.mark.parametrize("owner_role", OWNERS)
def test_grant_l1_reads_refuses_a_migrator_that_is_not_a_member_of_both_owner_roles_and_commits_nothing(world, l1, owner_role):  # claim G8 (SET ROLE to either owner needs membership)
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute(f"REVOKE {owner_role} FROM data_plane_migrator")
    r = run(world, "grant-l1-reads")
    assert r.returncode == 2 and "member of data_plane_schema_owner and data_plane_l1_owner" in r.stderr, r.stdout + r.stderr
    nothing_granted()


def test_a_migrator_that_cannot_enter_schema_public_is_refused_with_the_accurate_reason_not_does_not_exist(world, l1):  # claim F4 (honest message)
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("REVOKE USAGE ON SCHEMA public FROM data_plane_migrator")
    r = run(world, "grant-l1-reads")
    assert r.returncode != 0 and "cannot enter schema public (no USAGE)" in r.stderr, r.stdout + r.stderr
    assert "does not exist" not in r.stderr                       # a permission failure is never reported as a missing relation
    nothing_granted()


def test_the_migrator_password_is_in_no_psql_argument_list_and_no_output(world, l1):  # claim G9 (the secret stays in the environment, as for the admin URL)
    shim, log = _argv_logger(world, "psql_argv_logger_migrator")
    assert run(world).returncode == 0
    r = run(world, "grant-l1-reads", psql=str(shim))
    assert r.returncode == 0, r.stdout + r.stderr
    argv = log.read_text()
    assert argv.strip() and MIGRATOR_PW not in argv and "postgresql://" not in argv and "data_plane_migrator:" not in argv, argv[:400]
    assert MIGRATOR_PW not in visible(r)


def test_the_migrator_route_is_never_used_by_any_other_stage(world, l1):  # claim G10 ("this stage and only this stage": create-roles still runs as the ownership admin)
    bad = MIGRATOR_URL.replace(MIGRATOR_PW, "wrong-password")      # present in the environment (the workflow passes it to every stage) but unusable: a stage that connected with it would fail
    r = run(world, migrator=bad)
    assert r.returncode == 0, r.stdout + r.stderr
    with _admin() as c:
        assert c.execute("SELECT count(*) FROM pg_roles WHERE rolname=ANY(%s)", (list(GOCHARA),)).fetchone()[0] == 2


def test_grant_l1_reads_is_idempotent(world, l1):  # claim G4
    assert run(world).returncode == 0
    assert run(world, "grant-l1-reads").returncode == 0
    again = run(world, "grant-l1-reads")
    assert again.returncode == 0, again.stdout + again.stderr
    assert held("gochara_sealer", "chart_facts") == {"SELECT"}


def test_grant_l1_reads_refuses_when_a_principal_is_absent_and_changes_nothing(world, l1):  # claim G2
    r = run(world, "grant-l1-reads")                               # create-roles has not run: neither role exists
    assert r.returncode == 3 and "does not exist" in r.stderr, r.stdout + r.stderr
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("DROP ROLE gochara_sealer")
    r = run(world, "grant-l1-reads")
    assert r.returncode == 3 and "gochara_sealer does not exist" in r.stderr, r.stdout + r.stderr
    assert held("gochara_verifier", "chart_facts") == set()        # nothing was granted to the one that does exist


def test_grant_l1_reads_refuses_a_wider_pre_existing_acl_and_commits_nothing(world, l1):  # claim G3 (the grant is atomic with its closure check)
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("GRANT INSERT ON public.chart_dashas TO gochara_verifier")      # something already made the verifier able to write L1
    r = run(world, "grant-l1-reads")
    assert r.returncode != 0 and "postcondition" in r.stderr, r.stdout + r.stderr
    assert held("gochara_verifier", "chart_dashas") == {"INSERT"}  # unchanged: the SELECT grant rolled back with the failed check
    assert held("gochara_sealer", "chart_facts") == set()


def test_grant_l1_reads_gives_both_principals_exactly_usage_on_schema_public_so_the_l1_select_is_usable(world, l1):  # claim U1 (C-04)
    assert run(world).returncode == 0
    for who in ("gochara_verifier", "gochara_sealer"):
        assert schema_priv(who, "USAGE") is False, who            # the measured production state; without it the next assertions would be vacuous
    with _admin() as c:
        c.execute("CREATE ROLE canary_nsp NOLOGIN")
    try:
        r = run(world, "grant-l1-reads")
        assert r.returncode == 0, r.stdout + r.stderr
        assert run(world, "grant-l1-reads").returncode == 0       # idempotent
        for who in ("gochara_verifier", "gochara_sealer"):
            assert schema_priv(who, "USAGE") is True, who
            assert schema_priv(who, "CREATE") is False, who       # USAGE only: no object creation in public
            assert schema_priv(who, "USAGE WITH GRANT OPTION") is False and schema_priv(who, "CREATE WITH GRANT OPTION") is False, who
            with _admin() as c, c.transaction():                  # the point of the grant: the table SELECT is now usable as the principal
                c.execute(f"SET LOCAL ROLE {who}")
                assert c.execute("SELECT count(*) FROM public.chart_facts").fetchone()[0] == 0
        assert schema_priv("canary_nsp", "USAGE") is False        # nobody else was widened
    finally:
        with _admin() as c:
            c.execute("DROP ROLE canary_nsp")


def test_without_the_schema_grant_the_l1_select_is_unusable_in_the_hardened_database(world, l1):  # claim U1 (the defect C-04 closes: SELECT without USAGE)
    import psycopg as pg
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("GRANT SELECT ON public.chart_facts TO gochara_verifier")      # what the stage did before C-04
    with _admin() as c:
        with pytest.raises(pg.errors.InsufficientPrivilege, match="schema public"), c.transaction():
            c.execute("SET LOCAL ROLE gochara_verifier")
            c.execute("SELECT count(*) FROM public.chart_facts")


def test_grant_l1_reads_refuses_a_principal_that_can_create_in_public_and_commits_nothing(world, l1):  # claim U2 (USAGE only, atomic with the closure check)
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("GRANT CREATE ON SCHEMA public TO gochara_verifier")
    r = run(world, "grant-l1-reads")
    assert r.returncode != 0 and "postcondition" in r.stderr, r.stdout + r.stderr
    assert schema_priv("gochara_sealer", "USAGE") is False        # the whole transaction rolled back, the sealer included
    assert held("gochara_sealer", "chart_facts") == set() and held("gochara_verifier", "chart_facts") == set()


def sealer_secret_name(world):
    return (world["tmp"] / "gcloud_argv.txt").read_text()


def test_sealer_credential_writes_the_sealer_dsn_to_secret_manager_and_the_role_authenticates_with_it(world):  # claim C1 (SR-GRANTS-MINIMAL)
    import psycopg as pg
    assert run(world).returncode == 0
    (world["tmp"] / "gcloud_argv.txt").unlink()
    tail = "@127.0.0.1:5432/amjis"
    r = run(world, "sealer-credential", tail=tail)
    assert r.returncode == 0, r.stdout + r.stderr
    dsn = world["capture"].read_text()
    m = re.fullmatch(r"postgresql://gochara_sealer:([0-9a-f]{96})" + re.escape(tail), dsn)
    assert m, "the secret must be exactly the sealer DSN"
    argv = sealer_secret_name(world)
    assert "secrets versions add gochara-sealer-db-url" in argv and "--data-file=-" in argv and m.group(1) not in argv
    assert m.group(1) not in visible(r)                           # the password is in the secret input and nowhere a log shows
    assert "sealer password set" in r.stdout
    with _login("gochara_sealer", m.group(1)) as c:               # activation is observable
        assert c.execute("SELECT current_user").fetchone()[0] == "gochara_sealer"
    with _admin() as c:
        assert c.execute("SELECT shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='gochara_sealer'").fetchone()[0] == "gochara-provision:sealer-password-set"
    assert verbs(world) == ["add", "list", "add", "list"]          # create-roles' pair, then this stage's pair: never `access`, never `destroy` on success


def test_sealer_credential_refuses_unless_the_sealer_is_recorded_password_null_and_writes_no_secret(world):  # claim C4 + C5
    assert run(world, "sealer-credential", tail="@127.0.0.1:5432/amjis").returncode == 3          # roles absent
    assert run(world).returncode == 0
    before = verbs(world)
    assert run(world, "sealer-credential", tail="@127.0.0.1:5432/amjis").returncode == 0
    first = world["capture"].read_text()
    again = run(world, "sealer-credential", tail="@127.0.0.1:5432/amjis")
    assert again.returncode == 3 and "password-SET" in again.stderr, again.stdout + again.stderr   # a second run never rotates behind the first
    assert world["capture"].read_text() == first and verbs(world) == before + ["add", "list"]
    for bad in ("@user:pass@host/db", "no-at-sign", "@/db?x=1;drop"):
        assert run(world, "sealer-credential", tail=bad).returncode == 2, bad


def test_a_failed_sealer_credential_activation_destroys_the_secret_version_resets_the_password_and_verifies_both(world):  # claim C3
    assert run(world).returncode == 0
    with _admin() as c:
        c.execute("GRANT cloudsqlsuperuser TO gochara_sealer")        # the activation's postcondition fails
        before = role(c, "gochara_sealer")
    r = run(world, "sealer-credential", tail="@127.0.0.1:5432/amjis")
    assert r.returncode == 5 and "compensated and VERIFIED" in r.stderr and "destroyed secret version 7" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert role(c, "gochara_sealer") == before and role(c, "gochara_sealer")[8] is True      # password NULL again, attributes as before
    destroyed = (world["tmp"] / "gcloud_destroy.txt").read_text()
    assert "--secret gochara-sealer-db-url" in destroyed          # the SEALER secret, not the verifier's, is the one rolled back
    pw = re.search(r"gochara_sealer:([0-9a-f]{96})", world["capture"].read_text()).group(1)
    assert pw not in visible(r)


def test_an_unobservable_sealer_credential_is_compensated(world):  # claim C6
    assert run(world).returncode == 0
    shim = world["tmp"] / "psql_login_always_fails"
    shim.write_text(f'#!/usr/bin/env bash\n[ "${{PGUSER:-}}" = "gochara_sealer" ] && exit 2\nexec "{PSQL}" "$@"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = run(world, "sealer-credential", tail="@127.0.0.1:5432/amjis", psql=str(shim))
    assert r.returncode == 5 and "cannot authenticate after activation" in r.stderr and "compensated and VERIFIED" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert role(c, "gochara_sealer")[8] is True
    assert "--secret gochara-sealer-db-url" in (world["tmp"] / "gcloud_destroy.txt").read_text()


# ── O-W56-C (M-W56-4): stage layer-verifier-credential — the KĀLA-YANTRA executor's whole-layer verifier login ─────────────────────────────────────
# Sources: kala-provision-verifier-role.sh (verifier_principal is created NOLOGIN, NOINHERIT, no password; grant-usage gives USAGE on public only), migrations 1330/1334/1390 (its only
# grants: the receipt INSERT on kala_layer_verification and column reads), services/kala_core/publication.py:86 (verification refuses unless current_user = verifier_principal),
# fleet/executor.env.example.sh ("a separate verifier_principal login"). The sealer-credential claims C1-C6 above are the pattern; each claim below has one oracle.
LV = "verifier_principal"
LV_TAIL = "@127.0.0.1:5432/amjis"
LV_SECRET = "kala-layer-verifier-db-url"


@pytest.fixture()
def lv(world):
    """verifier_principal exactly as kala-provision-verifier-role.sh leaves it (created over the admin connection: NOLOGIN, NOINHERIT) plus the one table it inserts into."""
    def build():
        with _admin() as c:
            c.execute(f"DROP OWNED BY {LV}") if c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (LV,)).fetchone() else None
            c.execute(f"DROP ROLE IF EXISTS {LV}")
            c.execute("DROP TABLE IF EXISTS public.kala_layer_verification, public.lv_other_table")
            c.execute("CREATE TABLE public.kala_layer_verification (chart_id uuid, generation text, result text)")
            c.execute("CREATE TABLE public.lv_other_table (id int)")
        with psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3) as a:        # the creator is the ownership admin, as in production
            a.execute(f"CREATE ROLE {LV} NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION")
        with _admin() as c:
            c.execute(f"GRANT INSERT ON public.kala_layer_verification TO {LV}")
            c.execute(f"GRANT SELECT (chart_id, generation) ON public.kala_layer_verification TO {LV}")
    build()
    yield world
    with _admin() as c:
        c.execute(f"DROP OWNED BY {LV}") if c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (LV,)).fetchone() else None
        c.execute(f"DROP ROLE IF EXISTS {LV}")
        c.execute("DROP TABLE IF EXISTS public.kala_layer_verification, public.lv_other_table")
        c.execute("GRANT USAGE ON SCHEMA public TO PUBLIC")


def lv_state(c):
    return c.execute("SELECT rolcanlogin, rolconnlimit, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolinherit, rolpassword IS NULL"
                     " FROM pg_authid WHERE rolname = %s", (LV,)).fetchone()


NOLOGIN_AS_CREATED = (False, -1, False, False, False, False, False, False, True)


def lv_run(world, **kw):
    return run(world, "layer-verifier-credential", tail=kw.pop("tail", LV_TAIL), **kw)


def test_lv_credential_writes_the_dsn_to_secret_manager_and_the_role_authenticates_as_itself_with_exactly_the_least_privilege_set(lv):  # claim V1
    r = lv_run(lv)
    assert r.returncode == 0, r.stdout + r.stderr
    dsn = lv["capture"].read_text()
    m = re.fullmatch(r"postgresql://verifier_principal:([0-9a-f]{96})" + re.escape(LV_TAIL), dsn)
    assert m, "the secret must be exactly the layer-verifier DSN"
    argv = (lv["tmp"] / "gcloud_argv.txt").read_text()
    assert f"secrets versions add {LV_SECRET}" in argv and "--data-file=-" in argv and m.group(1) not in argv
    assert m.group(1) not in visible(r)                                  # the password is in the secret input and nowhere a log shows
    with _login(LV, m.group(1)) as c:                                    # activation is observable AS verifier_principal (publication.py:86)
        assert c.execute("SELECT current_user").fetchone()[0] == LV
    with _admin() as c:
        st = lv_state(c)
        assert st == (True, 4, False, False, False, False, False, False, False), st            # login, limit 4, nothing elevated, a password set
        assert c.execute("SELECT pg_has_role(%s, 'cloudsqlsuperuser', 'MEMBER')", (LV,)).fetchone()[0] is False
        assert c.execute("SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname=%s)", (LV,)).fetchone()[0] == 0
    assert verbs(lv) == ["add", "list"]                                  # never `access`, never `destroy` on success
    assert "secret_version: 1\tenabled" in r.stdout and "member_of_cloudsqlsuperuser=f" in r.stdout


def test_lv_credential_changes_no_grant(lv):  # claim V2 (the stage grants nothing: the ownership/ACL deploy gates have nothing new to admit)
    def acl(c):
        return (c.execute("SELECT relname, relacl::text FROM pg_class WHERE relnamespace='public'::regnamespace AND relname IN ('kala_layer_verification','lv_other_table') ORDER BY 1").fetchall(),
                c.execute("SELECT nspacl::text FROM pg_namespace WHERE nspname='public'").fetchone())
    with _admin() as c:
        before = acl(c)
    assert lv_run(lv).returncode == 0
    with _admin() as c:
        assert acl(c) == before


def test_lv_credential_refuses_unless_the_role_is_the_nologin_role_as_created_and_writes_no_secret(lv):  # claim V3
    with _admin() as c:
        c.execute(f"DROP OWNED BY {LV}; DROP ROLE {LV}")
    r = lv_run(lv)
    assert r.returncode == 3 and "does not exist" in r.stderr and verbs(lv) == [], r.stdout + r.stderr          # role absent
    lv_world = lv
    with psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=3) as a:
        a.execute(f"CREATE ROLE {LV} NOLOGIN NOINHERIT")
    assert lv_run(lv_world).returncode == 0
    first = lv_world["capture"].read_text()
    again = lv_run(lv_world)                                                                                    # already a login role: never rotates behind the first run
    assert again.returncode == 3 and "not the NOLOGIN role" in again.stderr, again.stdout + again.stderr
    assert lv_world["capture"].read_text() == first and verbs(lv_world) == ["add", "list"]


def test_lv_credential_refuses_a_changed_connection_limit_and_writes_no_secret(lv):  # claim V3b (the compensation restores -1, so any other pre-state is refused rather than overwritten)
    with _admin() as c:
        c.execute(f"ALTER ROLE {LV} CONNECTION LIMIT 9")
    r = lv_run(lv)
    assert r.returncode == 3 and "not the NOLOGIN role" in r.stderr and verbs(lv) == [], r.stdout + r.stderr


@pytest.mark.parametrize("tail", ["@user:pass@127.0.0.1:5432/amjis", "no-at-sign", "@/amjis?host=/cloudsql/p:r:i", "@10.9.9.9:5432/amjis", "@localhost:5432/amjis",
                                  "@127.0.0.1:5432/amjis?sslmode=disable", "@127.0.0.1/amjis", "@127.0.0.1:5432/"])
def test_lv_credential_accepts_only_the_executors_loopback_tail(lv, tail):  # claim V4 (the executor reaches the database through a local proxy; the verifier's Cloud Run socket form is not it)
    r = lv_run(lv, tail=tail)
    assert r.returncode == 2 and verbs(lv) == [], (tail, r.stdout, r.stderr)
    with _admin() as c:
        assert lv_state(c) == NOLOGIN_AS_CREATED


@pytest.mark.parametrize("plant", [
    "GRANT UPDATE ON public.kala_layer_verification TO verifier_principal",                       # a write beyond the single receipt INSERT
    "GRANT DELETE ON public.kala_layer_verification TO verifier_principal",
    "GRANT INSERT ON public.lv_other_table TO verifier_principal",                                # the INSERT is for kala_layer_verification only
    "GRANT SELECT ON public.lv_other_table TO verifier_principal WITH GRANT OPTION",
    "GRANT CREATE ON SCHEMA public TO verifier_principal",
    "GRANT cloudsqlsuperuser TO verifier_principal",
    "ALTER TABLE public.lv_other_table OWNER TO verifier_principal",
    "REVOKE USAGE ON SCHEMA public FROM PUBLIC",                                                  # the role has no USAGE on public (grant-usage not run): every read it needs would fail
], ids=["update", "delete", "insert-other", "grant-option", "create-schema", "superuser-edge", "owns-a-table", "no-usage"])
def test_lv_credential_postconditions_refuse_anything_beyond_the_receipt_insert_and_commit_nothing(lv, plant):  # claim V5 (one planted drift per postcondition clause; nothing committed, compensation verified)
    with _admin() as c:
        c.execute(plant)
    r = lv_run(lv)
    assert r.returncode == 5 and "compensated and VERIFIED" in r.stderr and "destroyed secret version 7" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert lv_state(c) == NOLOGIN_AS_CREATED, "the activation must have committed nothing"
    pw = re.search(r"verifier_principal:([0-9a-f]{96})", lv["capture"].read_text()).group(1)
    assert pw not in visible(r)
    assert f"--secret {LV_SECRET}" in (lv["tmp"] / "gcloud_destroy.txt").read_text()


def test_lv_credential_tolerates_the_creator_admin_membership_postgres_16_records_but_refuses_any_other_member(lv):  # claim V6
    with _admin() as c:
        c.execute(f"GRANT {LV} TO pgadmin WITH ADMIN OPTION, INHERIT FALSE, SET FALSE") if c.execute("SHOW server_version_num").fetchone()[0] >= "160000" else c.execute(f"GRANT {LV} TO pgadmin WITH ADMIN OPTION")
    r = lv_run(lv)
    assert r.returncode == 0, r.stdout + r.stderr                                                       # the creating admin's own administration right is not an escalation
    with _admin() as c:
        c.execute("ALTER ROLE verifier_principal NOLOGIN PASSWORD NULL CONNECTION LIMIT -1")
        c.execute("DROP ROLE IF EXISTS lv_stranger")
        c.execute("CREATE ROLE lv_stranger NOLOGIN")
        c.execute(f"GRANT {LV} TO lv_stranger")                                                         # someone who could SET ROLE to it
    try:
        r = lv_run(lv)
        assert r.returncode == 5 and "compensated and VERIFIED" in r.stderr, r.stdout + r.stderr
        with _admin() as c:
            assert lv_state(c) == NOLOGIN_AS_CREATED
    finally:
        with _admin() as c:
            c.execute("DROP ROLE IF EXISTS lv_stranger")


def test_lv_credential_compensates_an_activation_that_cannot_be_observed_as_itself(lv):  # claim V7
    shim = lv["tmp"] / "psql_lv_login_fails"
    shim.write_text(f'#!/usr/bin/env bash\n[ "${{PGUSER:-}}" = "{LV}" ] && [ -n "${{PGPASSWORD:-}}" ] && exit 2\nexec "{PSQL}" "$@"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = lv_run(lv, psql=str(shim))
    assert r.returncode == 5 and "cannot authenticate as itself after activation" in r.stderr and "compensated and VERIFIED" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert lv_state(c) == NOLOGIN_AS_CREATED
    assert f"--secret {LV_SECRET}" in (lv["tmp"] / "gcloud_destroy.txt").read_text()


def test_lv_credential_unverifiable_compensation_exits_70_and_keeps_the_secret_version(lv):  # claim V8 (the version is the only record of a possibly-live credential)
    shim = lv["tmp"] / "psql_lv_compensation_fails"
    flag = lv["tmp"] / "lv_activated.flag"
    shim.write_text(f'''#!/usr/bin/env bash
prev=""; for a in "$@"; do if [ "$prev" = "-f" ] && [ "$a" = "-" ]; then stmt="$(cat)"; printf '%s' "$stmt" | "{PSQL}" "$@" || exit $?; touch "{flag}"; exit 0; fi; prev="$a"; done
if [ -f "{flag}" ]; then for a in "$@"; do case "$a" in *"NOLOGIN PASSWORD NULL"*) exit 1;; esac; done; fi
[ -f "{flag}" ] && [ "${{PGUSER:-}}" = "{LV}" ] && exit 2
exec "{PSQL}" "$@"
''')
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    r = lv_run(lv, psql=str(shim))
    assert r.returncode == 70 and "ROLLBACK INCOMPLETE — THE LAYER VERIFIER MAY BE ACTIVE" in r.stderr and "NOT destroyed" in r.stderr, r.stdout + r.stderr
    assert not (lv["tmp"] / "gcloud_destroy.txt").exists()


def test_lv_credential_a_secret_store_failure_changes_nothing_in_the_database(lv):  # claim V9 (secret store FIRST: a failed write leaves the role exactly as it was)
    r = lv_run(lv, extra={"GCLOUD_PERMS": "list,destroy"})
    assert r.returncode == 5 and "nothing was changed in the database" in r.stderr, r.stdout + r.stderr
    with _admin() as c:
        assert lv_state(c) == NOLOGIN_AS_CREATED
