"""Act 2b step 1 — the machine-side secret-staging unit (Codex R12-5): every failure is tested at the OUTERMOST boundary (the exit status a caller sees), with a `gh` shim that records
argv and stdin and fails on request. No database needed."""
from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "gochara-sealer-stage-secrets.sh"
TAIL = "@/amjis?host=/cloudsql/p:r:i"


@pytest.fixture()
def env(tmp_path):
    log = tmp_path / "gh_calls.txt"
    stdin_dir = tmp_path / "stdin"
    stdin_dir.mkdir()
    gh = tmp_path / "gh"
    gh.write_text(f'''#!/usr/bin/env bash
echo "$*" >> "{log}"
name=""; for a in "$@"; do case "$a" in GOCHARA_*) name="$a";; esac; done
case "$1 $2" in
  "secret set") cat > "{stdin_dir}/$name"; case ",${{GH_FAIL:-}}," in *",set:$name,"*) exit 1;; esac ;;
  "secret delete") case ",${{GH_FAIL:-}}," in *",delete:$name,"*) exit 1;; esac; rm -f "{stdin_dir}/$name" ;;
  *) echo "unexpected gh call: $*" >&2; exit 9 ;;
esac
''')
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    ossl = tmp_path / "openssl"
    ossl.write_text('#!/usr/bin/env bash\nif [ "${OPENSSL_FAIL:-}" = 1 ]; then exit 1; fi\nif [ "${OPENSSL_SHORT:-}" = 1 ]; then echo abcd; exit 0; fi\nexec openssl "$@"\n')
    ossl.chmod(ossl.stat().st_mode | stat.S_IEXEC)
    return {"tmp": tmp_path, "gh": str(gh), "openssl": str(ossl), "log": log, "stdin": stdin_dir}


def run(env, **extra):
    e = {**os.environ, "DSN_TAIL": TAIL, "GH_BIN": env["gh"], "OPENSSL_BIN": env["openssl"], **extra}
    return subprocess.run(["bash", str(SCRIPT)], env=e, capture_output=True, text=True, timeout=60)


def calls(env):
    return env["log"].read_text().strip().splitlines() if env["log"].exists() else []


def test_success_writes_the_dsn_to_gochara_seal_and_the_password_alone_to_the_staging_environment_from_one_variable(env):
    r = run(env)
    assert r.returncode == 0, r.stdout + r.stderr
    a = (env["stdin"] / "GOCHARA_SEALER_DB_URL").read_text()
    b = (env["stdin"] / "GOCHARA_SEALER_PASSWORD_STAGING").read_text()
    m = re.fullmatch(r"postgresql://gochara_sealer:([0-9a-f]{96})" + re.escape(TAIL), a)
    assert m and m.group(1) == b, "(a) is the DSN carrying the SAME password as (b)"
    assert [c.split()[:2] + [c.split()[2]] for c in calls(env)] == [["secret", "set", "GOCHARA_SEALER_DB_URL"], ["secret", "set", "GOCHARA_SEALER_PASSWORD_STAGING"]]
    assert "--env gochara-seal" in calls(env)[0] and "--env data-plane-production-cutover" in calls(env)[1]
    assert "--body" not in " ".join(calls(env)) and "body-file" not in " ".join(calls(env))         # stdin only
    assert b not in r.stdout + r.stderr and b not in " ".join(calls(env))                          # the password is in no argv and no output


@pytest.mark.parametrize("extra,code,needle", [
    ({"OPENSSL_FAIL": "1"}, 11, "password generation"),
    ({"OPENSSL_SHORT": "1"}, 11, "password length"),
])
def test_a_password_failure_exits_11_and_writes_nothing(env, extra, code, needle):
    r = run(env, **extra)
    assert r.returncode == code and needle in r.stderr and "do NOT proceed to step 2" in r.stderr, r.stdout + r.stderr
    assert calls(env) == []


def test_a_failed_lasting_secret_write_exits_12_removes_it_and_tells_the_caller_to_stop(env):
    r = run(env, GH_FAIL="set:GOCHARA_SEALER_DB_URL")
    assert r.returncode == 12 and "do NOT proceed to step 2" in r.stderr, r.stdout + r.stderr
    assert any("secret delete GOCHARA_SEALER_DB_URL" in c for c in calls(env))                      # removal attempted: the write's outcome may be ambiguous
    assert not any("PASSWORD_STAGING" in c for c in calls(env))                                      # (b) was never attempted


def test_a_failed_staging_write_exits_13_and_removes_both(env):
    r = run(env, GH_FAIL="set:GOCHARA_SEALER_PASSWORD_STAGING")
    assert r.returncode == 13 and "rolled back: deleted GOCHARA_SEALER_DB_URL" in r.stderr and "rolled back: deleted GOCHARA_SEALER_PASSWORD_STAGING" in r.stderr, r.stdout + r.stderr
    assert not (env["stdin"] / "GOCHARA_SEALER_DB_URL").exists()                                     # (a) is gone again


@pytest.mark.parametrize("fail", ["set:GOCHARA_SEALER_PASSWORD_STAGING,delete:GOCHARA_SEALER_DB_URL", "set:GOCHARA_SEALER_DB_URL,delete:GOCHARA_SEALER_DB_URL",
                                  "set:GOCHARA_SEALER_PASSWORD_STAGING,delete:GOCHARA_SEALER_PASSWORD_STAGING"])
def test_a_failed_rollback_exits_14_and_names_what_may_remain(env, fail):
    r = run(env, GH_FAIL=fail)
    assert r.returncode == 14 and "ROLLBACK INCOMPLETE" in r.stderr and "by hand" in r.stderr, r.stdout + r.stderr


def test_bad_input_exits_2(env):
    for tail in ("@user:pass@host/db", "no-at-sign", "@/db;drop"):
        r = run(env, DSN_TAIL=tail)
        assert r.returncode == 2, (tail, r.stderr)
    assert calls(env) == []


def test_the_caller_idiom_stops_on_every_failure_at_the_outermost_boundary(env):
    """The runbook invokes the unit as `bash script || { …; exit 1; }`: reproduce THAT outermost wrapper for each failure and require the wrapper's own status to be non-zero
    (Codex R12-5 reproduced a wrapper that returned 0 after a failed write)."""
    wrapper = 'bash "$SCRIPT" || { echo "STOP: act 2b step 1 failed" >&2; exit 1; }; echo CONTINUED'
    for extra in ({"OPENSSL_FAIL": "1"}, {"GH_FAIL": "set:GOCHARA_SEALER_DB_URL"}, {"GH_FAIL": "set:GOCHARA_SEALER_PASSWORD_STAGING"},
                  {"GH_FAIL": "set:GOCHARA_SEALER_PASSWORD_STAGING,delete:GOCHARA_SEALER_DB_URL"}):
        e = {**os.environ, "DSN_TAIL": TAIL, "GH_BIN": env["gh"], "OPENSSL_BIN": env["openssl"], "SCRIPT": str(SCRIPT), **extra}
        r = subprocess.run(["bash", "-c", wrapper], env=e, capture_output=True, text=True, timeout=60)
        assert r.returncode == 1 and "CONTINUED" not in r.stdout, (extra, r.returncode, r.stdout, r.stderr)
