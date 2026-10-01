"""test_e5_6_rehearsal_guard.py — E5.6 phase 1: the rehearsal URL guard.

The rehearsal cluster is the only database the E5.6/E5.7 tooling may touch. Everything that hands a
connection URL to psql / migrate.ts / the orchestrator goes through
`platform/scripts/governance/rehearsal/rehearsal_guard.py::check_rehearsal_url` first
(apply_schema.sh and replay_schema.py both do). Pure unit tests: no database, no network.

Cases: non-local hosts, wrong ports, production-like hostnames, empty URLs, libpq overrides that
could redirect a connection (host=, hostaddr=, port=, service=), embedded passwords, multi-host
URLs, wrong databases. The mutation test proves the case table has teeth: with the guard disabled
(always "ok") the same table FAILS.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e5_6_rehearsal_guard.py -v
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import types

import pytest

REHEARSAL_DIR = pathlib.Path(__file__).resolve().parent.parent / "rehearsal"
sys.path.insert(0, str(REHEARSAL_DIR))

import rehearsal_guard  # noqa: E402

GOOD = "postgresql://Dev@127.0.0.1:55432/rehearsal"

ACCEPTED = [
    GOOD,
    "postgres://Dev@localhost:55432/rehearsal",
    "postgresql://localhost:55432/rehearsal",
    "postgresql://Dev@LOCALHOST:55432/rehearsal",
    "postgresql://Dev@127.0.0.1:55432/rehearsal_f3proof",
    "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=e5_6",
]

REFUSED = {
    # empty / malformed
    "empty string": "",
    "whitespace": "   ",
    "none": None,
    "not a url": "rehearsal",
    "non-postgres scheme": "mysql://Dev@127.0.0.1:55432/rehearsal",
    "unparseable port": "postgresql://Dev@127.0.0.1:abc/rehearsal",
    # non-local hosts
    "public dns host": "postgresql://Dev@db.example.com:55432/rehearsal",
    "private ip": "postgresql://Dev@10.0.0.5:55432/rehearsal",
    "bind-all address": "postgresql://Dev@0.0.0.0:55432/rehearsal",
    "ipv6 loopback": "postgresql://Dev@[::1]:55432/rehearsal",
    "localhost prefix trick": "postgresql://Dev@localhost.evil.com:55432/rehearsal",
    "userinfo trick": "postgresql://localhost@evil.com:55432/rehearsal",
    "fragment trick": "postgresql://evil.com:55432/rehearsal#@localhost",
    "no host (unix socket default)": "postgresql:///rehearsal",
    "multi host": "postgresql://localhost:55432,evil.com:55432/rehearsal",
    # wrong ports
    "default pg port": "postgresql://Dev@127.0.0.1:5432/rehearsal",
    "neighbour port": "postgresql://Dev@127.0.0.1:55433/rehearsal",
    "port missing": "postgresql://Dev@127.0.0.1/rehearsal",
    "cloud sql proxy port": "postgresql://Dev@127.0.0.1:5433/rehearsal",
    # production-like names
    "cloud sql host": "postgresql://amjis_app@amjis-postgres.asia-south1.cloudsql.example:55432/rehearsal",
    "cloud sql connection name": "postgresql://amjis_app@madhav-astrology:asia-south1:amjis-postgres/rehearsal",
    "supabase host": "postgresql://postgres@db.abcdefgh.supabase.co:55432/rehearsal",
    "prod in hostname": "postgresql://Dev@prod-db.internal:55432/rehearsal",
    "prod marker with a local host": "postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=prod",
    "production database name": "postgresql://Dev@127.0.0.1:55432/madhav_production",
    # libpq overrides that redirect the connection
    "host override": "postgresql://Dev@127.0.0.1:55432/rehearsal?host=db.example.com",
    "hostaddr override": "postgresql://Dev@127.0.0.1:55432/rehearsal?hostaddr=10.1.1.1",
    "port override": "postgresql://Dev@127.0.0.1:55432/rehearsal?port=5432",
    "service override": "postgresql://Dev@127.0.0.1:55432/rehearsal?service=other",
    "unix socket override": "postgresql://Dev@127.0.0.1:55432/rehearsal?host=/tmp/other-sock",
    # credentials / wrong database
    "password present": "postgresql://Dev:s3cret@127.0.0.1:55432/rehearsal",
    "wrong database": "postgresql://Dev@127.0.0.1:55432/postgres",
    "empty database": "postgresql://Dev@127.0.0.1:55432/",
    "database name only a prefix match": "postgresql://Dev@127.0.0.1:55432/rehearsalx",
}


def run_cases(check) -> list[str]:
    """Return a description of every case `check` gets wrong (empty list = all correct)."""
    wrong = []
    for url in ACCEPTED:
        ok, why = check(url)
        if not ok:
            wrong.append(f"should ACCEPT {url!r} but refused: {why}")
    for label, url in REFUSED.items():
        ok, _ = check(url)
        if ok:
            wrong.append(f"should REFUSE [{label}] {url!r} but accepted")
    return wrong


def test_guard_accepts_only_the_rehearsal_cluster_and_refuses_everything_else():
    assert run_cases(rehearsal_guard.check_rehearsal_url) == []


@pytest.mark.parametrize("label,url", sorted(REFUSED.items()))
def test_each_refusal_case(label, url):
    ok, reason = rehearsal_guard.check_rehearsal_url(url)
    assert ok is False, f"[{label}] {url!r} was accepted"
    assert reason  # a refusal always says why


@pytest.mark.parametrize("url", ACCEPTED)
def test_each_accepted_case(url):
    assert rehearsal_guard.check_rehearsal_url(url) == (True, "ok")


def test_rehearsal_port_constant_is_55432():
    assert rehearsal_guard.REHEARSAL_PORT == 55432


def test_cli_exit_codes_and_normalised_output():
    script = REHEARSAL_DIR / "rehearsal_guard.py"
    ok = subprocess.run([sys.executable, str(script), GOOD], capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stdout.strip() == GOOD
    for url in ("", "postgresql://Dev@db.example.com:5432/rehearsal"):
        bad = subprocess.run([sys.executable, str(script), url], capture_output=True, text=True)
        assert bad.returncode == 2 and bad.stderr.startswith("REFUSED:")
    nothing = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert nothing.returncode == 2  # no argument at all = empty URL = refused


@pytest.mark.parametrize("url", ["", "postgresql://Dev@10.0.0.5:55432/rehearsal",
                                 "postgresql://Dev@127.0.0.1:5432/rehearsal",
                                 "postgresql://amjis_app@amjis-postgres.cloudsql.example:55432/rehearsal"])
@pytest.mark.parametrize("command", ["replay", "verify", "migrate"])
def test_apply_schema_refuses_before_running_anything(command, url, tmp_path):
    """apply_schema.sh judges an explicit --url (even an empty one) with the guard FIRST: it must exit
    non-zero, say so, and never reach the server-identity step.

    SAFETY: the PostgreSQL binary directory is replaced by a stub `psql` that only records that it was
    called and fails. So even if the guard were broken/disabled, this test can never open a connection
    to the host in the URL; it instead FAILS on the 'psql was never invoked' assertion."""
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    marker = tmp_path / "psql_was_called"
    stub = stub_bin / "psql"
    stub.write_text(f"#!/bin/sh\ntouch {marker}\nexit 1\n")
    stub.chmod(0o755)
    script = REHEARSAL_DIR / "apply_schema.sh"
    r = subprocess.run(["bash", str(script), command, "--url", url], capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "REHEARSAL_PG_BIN": str(stub_bin)})
    assert not marker.exists(), "psql was invoked: the guard did not stop the URL before any process saw it"
    assert r.returncode != 0
    assert "refused" in r.stderr.lower()
    assert "server verified" not in r.stdout


def test_mutation_guard_disabled_is_detected():
    """MUTATION: the guard is replaced by one that accepts everything. The same case table must then
    FAIL — proving the table above has teeth and the real guard is what is making it pass."""
    source = (REHEARSAL_DIR / "rehearsal_guard.py").read_text(encoding="utf8")
    mutated = types.ModuleType("rehearsal_guard_mutant")
    exec(compile(source + '\ncheck_rehearsal_url = lambda url: (True, "ok")\n', "mutant", "exec"), mutated.__dict__)
    wrong = run_cases(mutated.check_rehearsal_url)
    assert len(wrong) == len(REFUSED), "every refusal case must be caught by the table when the guard is off"
    assert all(w.startswith("should REFUSE") for w in wrong)
