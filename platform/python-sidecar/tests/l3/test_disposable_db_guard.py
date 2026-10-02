"""C24 — one test per DSN form for the ONE shared disposable-database guard
(tests/l3/_disposable_db_guard.py, steward M20261002T154223-e3e1): the
legitimate loopback forms are ACCEPTED and every dangerous form is REFUSED —
URI multi-host (libpq failover past the first host, the Suvarṇa finding),
keyword/value DSNs, host=/hostaddr= in the query string, pg_service, libpq
environment overrides (PGHOST / PGHOSTADDR / PGSERVICE / PGSERVICEFILE), and a
wrong dbname. All string-level tests are pure (no connection). The
post-connect check runs only when the C7 CI Postgres DSN is present.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _disposable_db_guard import (  # noqa: E402
    RefusedError,
    assert_disposable_connection,
    validate_disposable_dsn,
)

DB = "c7_builder_role_test"
C7_DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")
EMPTY_ENV: dict = {}


def _accept(dsn, name=DB, env=EMPTY_ENV):
    return validate_disposable_dsn(dsn, name, env=env)


def _refuse(dsn, name=DB, env=EMPTY_ENV):
    with pytest.raises(RefusedError):
        validate_disposable_dsn(dsn, name, env=env)


# ── acceptance: the legitimate forms ─────────────────────────────────────────

def test_uri_single_loopback_host_accepted():
    info = _accept(f"postgresql://u:p@localhost:5432/{DB}")
    assert info["dbname"] == DB and info["host"] == "localhost"


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "[::1]", "localhost"])
def test_every_loopback_spelling_accepted(host):
    _accept(f"postgresql://u:p@{host}:5432/{DB}")


def test_keyword_value_dsn_accepted():
    _accept(f"host=localhost port=5432 dbname={DB} user=u")


@pytest.mark.parametrize("key", ["dbname", "host", "hostaddr", "service"])
def test_query_string_target_options_refused(key):
    """Suvarṇa F1: target-deciding options are refused outright in a URI query
    string — even a LOOPBACK value (no `?hostaddr=127.0.0.1` loophole)."""
    value = "127.0.0.1" if key == "hostaddr" else "anything"
    _refuse(f"postgresql://u:p@localhost/{DB}?{key}={value}", name=None)


def test_query_string_dbname_attack_refused():
    """F1: postgresql://u@localhost/x_test?dbname=madhav would connect to
    `madhav` while a path-only name check reads `x_test`."""
    _refuse("postgresql://u@localhost/x_test?dbname=madhav", name=None)


def test_keyword_dbname_attack_visible_in_effective_conninfo():
    """F1: 'host=localhost dbname=madhav application_name=test' passes a
    string/path 'test' check — but the helper's returned conninfo exposes the
    EFFECTIVE dbname, which is what callers assert their name rule on."""
    info = _accept("host=localhost dbname=madhav application_name=test", name=None)
    assert info["dbname"] == "madhav"
    assert "test" not in info["dbname"].lower()  # the caller's rule must fail


def test_expected_dbname_none_is_host_discipline_only():
    # the wp10 fixture's form: any dbname, loopback everywhere
    _accept("postgresql://postgres:postgres@localhost:5432/postgres", name=None)


# ── refusal: every dangerous form ────────────────────────────────────────────

def test_uri_multi_host_refused():
    """The Suvarṇa finding: urlparse().hostname sees only the FIRST host; libpq
    can fail over to the second. Refused on the comma in the netloc."""
    _refuse(f"postgresql://u:p@localhost:5432,db.prod.example.com:5432/{DB}")


def test_keyword_value_multi_host_refused():
    _refuse(f"host=localhost,db.prod.example.com dbname={DB}")


def test_query_string_host_override_refused():
    _refuse(f"postgresql://u:p@localhost:5432/{DB}?host=db.prod.example.com")


def test_query_string_non_loopback_hostaddr_refused():
    _refuse(f"postgresql://u:p@localhost/{DB}?hostaddr=10.0.0.5")


def test_query_string_loopback_hostaddr_refused_too():
    # folded into test_query_string_target_options_refused (F1) — kept as an
    # explicit pin of the behavioural change from the first C24 draft.
    _refuse(f"postgresql://u:p@localhost/{DB}?hostaddr=127.0.0.1")


def test_remote_single_host_refused():
    _refuse(f"postgresql://u:p@db.prod.example.com:5432/{DB}")


def test_pg_service_in_dsn_refused():
    _refuse(f"service=myservice dbname={DB}")


@pytest.mark.parametrize("var", ["PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_libpq_environment_override_refused(var):
    _refuse(f"postgresql://u:p@localhost:5432/{DB}", env={var: "anything"})


def test_empty_environment_override_treated_as_unset():
    _accept(f"postgresql://u:p@localhost:5432/{DB}", env={"PGHOST": "  "})


def test_wrong_dbname_refused():
    _refuse("postgresql://u:p@localhost:5432/production")


def test_unparseable_dsn_refused():
    _refuse("not a dsn at all :::")


# ── post-connect proof (needs the CI Postgres / a local disposable) ──────────

class _FakeConn:
    """Post-connect proof without a server: execute() returns a canned row."""

    def __init__(self, dbname, server_addr):
        self._row = (dbname, server_addr)

    def execute(self, _sql):
        return self

    def fetchone(self):
        return self._row


GHA = {"GITHUB_ACTIONS": "true"}
NOT_GHA: dict = {}


@pytest.mark.parametrize("addr", [None, "127.0.0.1/32", "::1/128"])
@pytest.mark.parametrize("env", [GHA, NOT_GHA])
def test_post_connect_accepts_unix_and_loopback_everywhere(addr, env):
    assert_disposable_connection(_FakeConn(DB, addr), DB, env=env)


@pytest.mark.parametrize("addr", ["172.18.0.2/32", "10.0.0.5/8", "192.168.1.10/24", "::ffff:10.0.0.1/128"])
def test_post_connect_accepts_rfc1918_only_in_github_actions(addr):
    # 172.18.0.2 is the GitHub Actions service-container bridge address — the
    # legitimate CI shape, accepted only there. ::ffff:10.0.0.1 unwraps to the
    # RFC 1918 10.0.0.1 (F2) — private, so likewise accepted only in CI.
    assert_disposable_connection(_FakeConn(DB, addr), DB, env=GHA)
    with pytest.raises(RefusedError):
        assert_disposable_connection(_FakeConn(DB, addr), DB, env=NOT_GHA)
    with pytest.raises(RefusedError):
        assert_disposable_connection(
            _FakeConn(DB, addr), DB, env={"GITHUB_ACTIONS": "false"})
    with pytest.raises(RefusedError):
        assert_disposable_connection(
            _FakeConn(DB, addr), DB, env={"GITHUB_ACTIONS": "1"})


@pytest.mark.parametrize("env", [GHA, NOT_GHA])
@pytest.mark.parametrize("addr", [
    "8.8.8.8/32",                 # public
    "1.1.1.1/32",                 # public
    "2606:4700:4700::1111/128",   # public v6
    "::ffff:8.8.8.8/128",         # v4-mapped PUBLIC — is_private on py<3.13 (F2)
    "169.254.1.1/16",             # link-local — outside the explicit RFC 1918 set
    "fd00::1/128",                # ULA — outside the explicit set
    "0.0.0.0/32",                 # unspecified — outside the explicit set
    "192.0.2.1/24",               # TEST-NET-1 documentation range — not RFC 1918
])
def test_post_connect_refuses_everything_else_everywhere(addr, env):
    with pytest.raises(RefusedError):
        assert_disposable_connection(_FakeConn(DB, addr), DB, env=env)


def test_post_connect_refuses_the_wrong_database():
    with pytest.raises(RefusedError):
        assert_disposable_connection(_FakeConn("production", None), DB)


@pytest.mark.skipif(not C7_DSN, reason="C7_BUILDER_ROLE_TEST_DATABASE_URL not set")
def test_post_connect_check_on_the_real_disposable():
    psycopg = pytest.importorskip("psycopg")
    validate_disposable_dsn(C7_DSN, DB)
    with psycopg.connect(C7_DSN) as conn:
        assert_disposable_connection(conn, DB)  # must not raise
        with pytest.raises(RefusedError):
            assert_disposable_connection(conn, "some_other_database")


# ── Suvarṇa GuardHarness lists, lifted (steward M20261002T180436-f0e1) ────────
# The DSN forms and server addresses below are lifted from Suvarṇa's read-only
# reviewer harnesses (/Users/Dev/suvarna-evidence/GuardHarness/ — never run,
# never copied; synthetic data only) and asserted against the CORRECTED rules
# (F1: URI query-string target options refused outright, effective dbname from
# conninfo; F2: explicit RFC 1918 CI set, v4-mapped unwrap). Where our expected
# outcome differs from the harness's own apparent expectation the case label is
# marked [DIFF] and the difference is listed in the PR body. DSN validation is
# CI-independent (GITHUB_ACTIONS only affects the post-connect address rule), so
# each form carries its expectation for the db-pinned mode AND for
# expected_dbname=None (host-discipline-only, the wp10 form).

# (label, dsn, env, expected_when_db_pinned, expected_when_dbname_None)
_HARNESS_DSN_CASES = [
    ("ok localhost URI", f"postgresql://u:p@localhost:5432/{DB}", {}, True, True),
    ("ok postgres:// scheme 127.0.0.1", f"postgres://u@127.0.0.1:55433/{DB}", {}, True, True),
    ("ok [::1] URI", f"postgresql://u@[::1]:5432/{DB}", {}, True, True),
    ("ok kv host=localhost", f"host=localhost port=5432 dbname={DB} user=u", {}, True, True),
    ("[DIFF] kv unix socket dir", f"host=/private/tmp/rvp dbname={DB} user=u", {}, False, False),
    ("[DIFF] unix socket URI ?host=", f"postgresql:///{DB}?host=/private/tmp/rvp", {}, False, False),
    ("[DIFF] 127.0.0.2 (loopback /8)", f"postgresql://u@127.0.0.2:5432/{DB}", {}, False, False),
    ("ok no-host URI (socket/env default)", f"postgresql:///{DB}", {}, True, True),
    ("ok no-host kv", f"dbname={DB}", {}, True, True),
    ("remote host", f"postgresql://u:p@db.prod.example.com:5432/{DB}", {}, False, False),
    ("10.x host", f"postgresql://u:p@10.0.0.5:5432/{DB}", {}, False, False),
    ("localhost.example.com", f"postgresql://u:p@localhost.example.com:5432/{DB}", {}, False, False),
    ("multi-host w/ ports local,remote", f"postgresql://u:p@localhost:5432,db.prod.example.com:5432/{DB}", {}, False, False),
    ("multi-host no ports local,remote", f"postgresql://u:p@localhost,db.prod.example.com/{DB}", {}, False, False),
    ("multi-host local,10.x", f"postgresql://u:p@localhost:5432,10.1.2.3:5432/{DB}", {}, False, False),
    ("multi-host bad first", f"postgresql://u:p@db.prod.example.com:5432,localhost:5432/{DB}", {}, False, False),
    ("[DIFF] multi-host URI both loopback", f"postgresql://u:p@localhost:5432,127.0.0.1:5433/{DB}", {}, False, False),
    ("multi-host bad 2nd position of 3", f"postgresql://u@localhost,127.0.0.1,evil.example.com/{DB}", {}, False, False),
    ("kv host=localhost,remote", f"host=localhost,db.prod.example.com dbname={DB}", {}, False, False),
    ("kv host=a,b both loopback", f"host=localhost,127.0.0.1 dbname={DB}", {}, True, True),
    ("kv hostaddr remote", f"host=localhost hostaddr=10.1.2.3 dbname={DB}", {}, False, False),
    ("kv hostaddr loopback", f"host=localhost hostaddr=127.0.0.1 dbname={DB}", {}, True, True),
    ("kv socket path with comma", "host=/tmp/a,b dbname=" + DB, {}, False, False),
    ("kv socket path,remote", f"host=/tmp/sock,evil.example.com dbname={DB}", {}, False, False),
    ("query ?hostaddr remote", f"postgresql://u@localhost:5432/{DB}?hostaddr=203.0.113.9", {}, False, False),
    ("[DIFF] query ?hostaddr loopback", f"postgresql://u@localhost:5432/{DB}?hostaddr=127.0.0.1", {}, False, False),
    ("query ?host=remote", f"postgresql://u@localhost:5432/{DB}?host=db.prod.example.com", {}, False, False),
    ("query ?host=remote no netloc host", f"postgresql:///{DB}?host=db.prod.example.com", {}, False, False),
    ("query ?dbname override", f"postgresql://u@localhost:5432/{DB}?dbname=madhav", {}, False, False),
    ("[DIFF] query ?dbname=same", f"postgresql://u@localhost:5432/{DB}?dbname={DB}", {}, False, False),
    ("query ?service=", f"postgresql://u@localhost:5432/{DB}?service=prod", {}, False, False),
    ("query ?sslmode=require", f"postgresql://u@localhost:5432/{DB}?sslmode=require", {}, True, True),
    ("query ?application_name", f"postgresql://u@localhost:5432/{DB}?application_name=x", {}, True, True),
    ("query ?options=-c", f"postgresql://u@localhost:5432/{DB}?options=-csearch_path%3Dx", {}, True, True),
    ("query ?target_session_attrs", f"postgresql://u@localhost:5432/{DB}?target_session_attrs=any", {}, True, True),
    ("kv service=prod", f"host=localhost service=prod dbname={DB}", {}, False, False),
    ("kv sslmode=require", f"host=localhost dbname={DB} sslmode=require", {}, True, True),
    ("wrong db madhav", "postgresql://u@localhost:5432/madhav", {}, False, True),
    ("wrong db postgres", "postgresql://u@localhost:5432/postgres", {}, False, True),
    ("db suffix (test2)", f"postgresql://u@localhost:5432/{DB}2", {}, False, True),
    ("db uppercase", f"postgresql://u@localhost:5432/{DB.upper()}", {}, False, True),
    ("db empty path", "postgresql://u@localhost:5432", {}, False, True),
    ("db empty path trailing slash", "postgresql://u@localhost:5432/", {}, False, True),
    ("[DIFF] host uppercase LOCALHOST", f"postgresql://u@LOCALHOST:5432/{DB}", {}, False, False),
    ("[DIFF] host trailing dot localhost.", f"postgresql://u@localhost.:5432/{DB}", {}, False, False),
    ("URL-encoded host %6Cocalhost", f"postgresql://u@%6Cocalhost:5432/{DB}", {}, True, True),
    ("URL-encoded remote host", f"postgresql://u@db%2Eprod%2Eexample%2Ecom:5432/{DB}", {}, False, False),
    ("URL-encoded comma %2C in host", f"postgresql://u@localhost%2Cdb.prod.example.com/{DB}", {}, False, False),
    ("userinfo trick user=localhost@remote", f"postgresql://localhost:5432@db.prod.example.com/{DB}", {}, False, False),
    ("userinfo with @ in password", f"postgresql://u:p%40ss@localhost:5432/{DB}", {}, True, True),
    ("[DIFF] userinfo with comma pw", f"postgresql://u:a,b@localhost:5432/{DB}", {}, False, False),
    ("IPv6 non-loopback [2001:db8::1]", f"postgresql://u@[2001:db8::1]:5432/{DB}", {}, False, False),
    ("[DIFF] IPv6 ::ffff:127.0.0.1", f"postgresql://u@[::ffff:127.0.0.1]:5432/{DB}", {}, False, False),
    ("[DIFF] IPv6 0:0:0:0:0:0:0:1", f"postgresql://u@[0:0:0:0:0:0:0:1]:5432/{DB}", {}, False, False),
    ("0.0.0.0 host", f"postgresql://u@0.0.0.0:5432/{DB}", {}, False, False),
    ("trailing whitespace", f"postgresql://u@localhost:5432/{DB} ", {}, False, False),
    ("trailing newline", f"postgresql://u@localhost:5432/{DB}\n", {}, False, False),
    ("trailing tab", f"postgresql://u@localhost:5432/{DB}\t", {}, False, False),
    ("leading whitespace", f" postgresql://u@localhost:5432/{DB}", {}, False, False),
    ("uppercase scheme POSTGRESQL://", f"POSTGRESQL://u@localhost:5432/{DB}", {}, False, False),
    ("mysql scheme", f"mysql://u@localhost:5432/{DB}", {}, False, False),
    ("empty dsn", "", {}, False, True),
    ("garbage dsn", "not a dsn %%%", {}, False, False),
    ("kv extra host= dup", f"host=localhost host=evil.example.com dbname={DB}", {}, False, False),
    ("kv quoted host", f"host='db.prod.example.com' dbname={DB}", {}, False, False),
    ("[DIFF] kv host=''", f"host='' dbname={DB}", {}, False, False),
    ("kv fallback_application_name", f"host=localhost dbname={DB} fallback_application_name=x", {}, True, True),
    ("kv passfile / sslrootcert", f"host=localhost dbname={DB} passfile=/tmp/x", {}, True, True),
    # env cases (the env dict is what validate_disposable_dsn checks against)
    ("ENV PGHOST remote, DSN names localhost", f"postgresql://u@localhost:5432/{DB}", {"PGHOST": "db.prod.example.com"}, False, False),
    ("ENV PGHOST remote, DSN has NO host", f"postgresql:///{DB}", {"PGHOST": "db.prod.example.com"}, False, False),
    ("ENV PGHOST remote, kv no host", f"dbname={DB}", {"PGHOST": "db.prod.example.com"}, False, False),
    ("[DIFF] ENV PGHOST=localhost", f"postgresql://u@localhost:5432/{DB}", {"PGHOST": "localhost"}, False, False),
    ("[DIFF] ENV PGHOST=/socket", f"postgresql://u@localhost:5432/{DB}", {"PGHOST": "/private/tmp/rvp"}, False, False),
    ("ENV PGHOSTADDR remote, DSN localhost", f"postgresql://u@localhost:5432/{DB}", {"PGHOSTADDR": "203.0.113.9"}, False, False),
    ("[DIFF] ENV PGHOSTADDR=127.0.0.1", f"postgresql://u@localhost:5432/{DB}", {"PGHOSTADDR": "127.0.0.1"}, False, False),
    ("ENV PGSERVICE=x", f"postgresql://u@localhost:5432/{DB}", {"PGSERVICE": "prod"}, False, False),
    ("ENV PGSERVICEFILE=x", f"postgresql://u@localhost:5432/{DB}", {"PGSERVICEFILE": "/tmp/svc"}, False, False),
    ("ENV PGHOST empty string", f"postgresql://u@localhost:5432/{DB}", {"PGHOST": ""}, True, True),
    ("ENV PGHOST whitespace", f"postgresql://u@localhost:5432/{DB}", {"PGHOST": " "}, True, True),
]


@pytest.mark.parametrize(
    "label,dsn,env,pinned,none",
    _HARNESS_DSN_CASES,
    ids=[c[0] for c in _HARNESS_DSN_CASES],
)
def test_harness_dsn_forms(label, dsn, env, pinned, none):
    for expected, name in ((pinned, DB), (none, None)):
        if expected:
            validate_disposable_dsn(dsn, name, env=env)
        else:
            with pytest.raises(RefusedError):
                validate_disposable_dsn(dsn, name, env=env)


def test_harness_env_pgdatabase_and_pgport(monkeypatch):
    """PGDATABASE / PGPORT are not in the guard's refused-env list: libpq's
    explicit-DSN-beats-env precedence makes them safe — an explicit dbname in
    the DSN wins over PGDATABASE, and the port never decides identity."""
    monkeypatch.setenv("PGDATABASE", "madhav")
    # DSN carries the db explicitly — the DSN wins over PGDATABASE: ACCEPT.
    info = validate_disposable_dsn(f"postgresql://u@localhost:5432/{DB}", DB, env={})
    assert info["dbname"] == DB
    # DSN carries no db and PGDATABASE points elsewhere: the pinned mode must
    # REFUSE (the effective dbname is not the disposable one)…
    with pytest.raises(RefusedError):
        validate_disposable_dsn("postgresql://u@localhost:5432", DB, env={})
    # …while host-discipline-only mode accepts (loopback host; the fixture
    # creates its own database anyway).
    validate_disposable_dsn("postgresql://u@localhost:5432", None, env={})
    monkeypatch.setenv("PGDATABASE", DB)
    validate_disposable_dsn(f"postgresql://u@localhost:5432/{DB}", DB, env={})
    monkeypatch.setenv("PGPORT", "1")
    validate_disposable_dsn(f"postgresql://u@localhost/{DB}", DB, env={})


# The 21 post_harness.py server addresses, under F2 (explicit RFC 1918 CI set,
# v4-mapped unwrap): (address, accepted_locally, accepted_in_github_actions)
_HARNESS_SERVER_ADDRS = [
    (None, True, True),
    ("127.0.0.1/32", True, True),
    ("127.5.5.5/32", True, True),               # loopback is a /8
    ("::1/128", True, True),
    ("::ffff:127.0.0.1/128", True, True),       # unwraps to 127.0.0.1
    ("10.0.0.5/32", False, True),               # RFC 1918 — CI only
    ("172.18.0.2/32", False, True),             # the CI service-container bridge
    ("172.32.0.1/32", False, False),            # outside 172.16.0.0/12
    ("192.168.1.5/32", False, True),            # RFC 1918 — CI only
    ("169.254.1.1/32", False, False),           # link-local — outside the set
    ("fe80::1/128", False, False),              # v6 link-local
    ("fd00::1/128", False, False),              # ULA
    ("100.64.0.1/32", False, False),            # CGNAT — outside the set
    ("0.0.0.0/32", False, False),               # unspecified
    ("::/128", False, False),                   # unspecified v6
    ("8.8.8.8/32", False, False),               # public
    ("2001:db8::1/128", False, False),          # documentation range
    ("203.0.113.9/32", False, False),           # TEST-NET-3
    ("198.18.0.1/32", False, False),            # benchmarking range
    ("::ffff:10.0.0.1/128", False, True),       # unwraps to RFC 1918 — CI only
    ("garbage", False, False),                  # unparseable inet — clean refusal
]


@pytest.mark.parametrize(
    "addr,local,gha",
    _HARNESS_SERVER_ADDRS,
    ids=[str(c[0]) for c in _HARNESS_SERVER_ADDRS],
)
def test_harness_server_addresses(addr, local, gha):
    for expected, env in ((local, NOT_GHA), (gha, GHA)):
        if expected:
            assert_disposable_connection(_FakeConn(DB, addr), DB, env=env)
        else:
            with pytest.raises(RefusedError):
                assert_disposable_connection(_FakeConn(DB, addr), DB, env=env)
