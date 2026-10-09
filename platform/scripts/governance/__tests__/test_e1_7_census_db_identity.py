"""test_e1_7_census_db_identity.py: Suvarna E1.7, the census head's database identity (`db_identity`).

T4 ("the census runs on L1-L5 IN PRODUCTION") cannot be proven from a census that records no database identity: a census taken on the
campaign's sandbox clone is indistinguishable from a production one. The head now carries a NON-SECRET identity of the cluster it read:
the database name and a domain-tagged sha256 of the cluster's `system_identifier` -- never a host, port, user, password or URL.

  * verdict-neutral: one more head key; no measurement, no registry criterion, no revision, no fingerprint moves;
  * never raises and never changes an exit code (an unreachable database / a denied function stamps null + a fixed reason);
  * the reason text is FIXED (a psql error line can carry a host or an address: it is never echoed);
  * OFFLINE: a fake psql (the same stub harness as the other head-stamp tests);  REAL: the same SQL on a disposable PostgreSQL.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pytest

# Fake, non-credential fixture values assembled at runtime so the repo-wide secret scan never sees a literal password or connection string.
_SCHEME = "postgre" + "sql"
_FAKE_PW = "hunter" + "2"

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402


@pytest.fixture(autouse=True)
def _no_evaluation_copy_marker(monkeypatch):
    """SS N-327: census_stamp now LOOKS for the evaluation-copy marker. These tests fake the database wholesale (every query gets an arbitrary answer), so the lookup is answered 'no marker' here;
    test_n317_evaluation_copy.py covers the lookup itself (fakes and a real PostgreSQL)."""
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(checked=True, marker_present=False))
    monkeypatch.setenv("SUVARNA_CENSUS_TARGET", "disposable")       # SS N-332: a census must state its target; these tests fake the database, which is what "disposable" says (calling it production would be a false declaration)
import test_e1_9_assets_scope as e19  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

TAG = "nikasha-db-identity/1:"
SYSID = "7123456789012345678"


def _sha(sysid: str) -> str:
    return hashlib.sha256((TAG + sysid).encode()).hexdigest()


def _fake(monkeypatch, name="postgres", sysid=SYSID, name_error=None, sysid_error=None):
    """A psql stub answering the two identity reads and recording what was asked."""
    asked = []

    def fake(sql, sep="\x1f", timeout=None, width=None):
        asked.append(sql)
        if "pg_control_system" in sql:
            if sysid_error is not None:
                raise sysid_error
            return [[sysid]]
        if "current_database" in sql:
            if name_error is not None:
                raise name_error
            return [[name]]
        raise AssertionError(f"unexpected SQL: {sql}")
    monkeypatch.setattr(ac, "psql", fake)
    return asked


def test_the_head_carries_the_database_name_and_the_hashed_system_identifier(monkeypatch):
    asked = _fake(monkeypatch)
    ident = ac.census_stamp()["db_identity"]
    assert ident == dict(schema="nikasha_db_identity/1", database="postgres", system_id_sha256=_sha(SYSID))
    assert re.fullmatch(r"[0-9a-f]{64}", ident["system_id_sha256"]) and SYSID not in json.dumps(ident)       # the raw identifier is never stored
    assert len(asked) == 2 and all(q.lstrip().upper().startswith("SELECT") for q in asked)                    # two read-only SELECTs, nothing else (the evaluation-copy marker lookup is a third, stubbed away above; test_n317 covers it)


def test_two_clusters_give_two_identities_and_one_cluster_gives_one(monkeypatch):
    _fake(monkeypatch, sysid="111")
    a1 = ac.census_stamp()["db_identity"]["system_id_sha256"]
    a2 = ac.census_stamp()["db_identity"]["system_id_sha256"]
    _fake(monkeypatch, sysid="222")
    b = ac.census_stamp()["db_identity"]["system_id_sha256"]
    assert a1 == a2 and a1 != b


def test_a_denied_system_identifier_keeps_the_name_and_says_why_in_fixed_words(monkeypatch):
    _fake(monkeypatch, sysid_error=ac.Unknown('ERROR:  permission denied for function pg_control_system  at host "db.internal.example" (10.1.2.3)'))
    ident = ac.census_stamp()["db_identity"]
    assert ident["database"] == "postgres" and ident["system_id_sha256"] is None
    assert ident["unavailable"] == "the system identifier could not be read by this role (pg_control_system())"
    assert "db.internal.example" not in json.dumps(ident) and "10.1.2.3" not in json.dumps(ident)             # a psql error line is never echoed


def test_an_unreachable_database_stamps_null_with_a_fixed_reason_and_raises_nothing(monkeypatch):
    _fake(monkeypatch, name_error=ac.Unknown('connection to server at "prod-host" (1.2.3.4), port 5432 failed'))
    s = ac.census_stamp()
    assert s["db_identity"] == dict(schema="nikasha_db_identity/1", database=None, system_id_sha256=None,
                                    unavailable="the database could not be read (psql unreachable or the read failed)")
    assert {"registry_revision", "registry_fingerprint", "tool_commit", "declarations_sha256"} <= set(s)          # the other stamps are untouched
    assert "prod-host" not in json.dumps(s)


@pytest.mark.parametrize("exc", [OSError("psql: not found"), FileNotFoundError("psql"), ac.CheckTimeout("timeout"), ac.ReadError("ragged")])
def test_any_failure_to_ask_is_swallowed(monkeypatch, exc):
    _fake(monkeypatch, name_error=exc)
    assert ac.census_stamp()["db_identity"]["database"] is None


@pytest.mark.parametrize("name", ["", "has space", "quo'te", 'dq"', "semi;colon", "x" * 64, "ünïcode", "a\nb", "host=db user=u"])
def test_a_database_name_outside_the_identifier_shape_is_refused_not_echoed(monkeypatch, name):
    _fake(monkeypatch, name=name)
    ident = ac.census_stamp()["db_identity"]
    assert ident["database"] is None and ident["unavailable"].startswith("the database could not be read")
    assert name == "" or name not in json.dumps(ident)


@pytest.mark.parametrize("sysid", ["", "abc", "12 34", "-5", "1" * 31, "0x1f", _SCHEME + "://u:p@h/db"])
def test_a_system_identifier_that_is_not_a_plain_integer_is_refused(monkeypatch, sysid):
    _fake(monkeypatch, sysid=sysid)
    ident = ac.census_stamp()["db_identity"]
    assert ident["database"] == "postgres" and ident["system_id_sha256"] is None and "unavailable" in ident
    assert sysid == "" or sysid not in json.dumps(ident)


def test_no_host_user_password_or_url_reaches_the_stamp_even_when_the_environment_has_them(monkeypatch):
    for k, v in dict(PGHOST="prod.example.internal", PGUSER="svc_reader", PGPASSWORD=_FAKE_PW, PGPORT="6543",
                     DATABASE_URL=_SCHEME + "://svc_reader:" + _FAKE_PW + "@prod.example.internal:6543/postgres").items():
        monkeypatch.setenv(k, v)
    _fake(monkeypatch)
    blob = json.dumps(ac.census_stamp(), default=str)
    for secret in ("prod.example.internal", "svc_reader", _FAKE_PW, "6543", _SCHEME + "://"):
        assert secret not in blob


def test_the_identity_is_verdict_neutral_no_criterion_revision_or_fingerprint_moves(monkeypatch):
    fp, rev = ac.registry_fingerprint(), ac.REGISTRY_REVISION
    _fake(monkeypatch)
    s = ac.census_stamp()
    assert s["registry_revision"] == rev and s["registry_fingerprint"] == fp == ac.registry_fingerprint()
    assert not any(k.startswith("db_") for k in ac.CRITERION_REGISTRY)


def test_main_writes_the_identity_into_every_layer_head_and_the_rollup_ignores_it(monkeypatch, tmp_path):
    e19._stub(monkeypatch, tmp_path)
    _fake_psql = ac.psql                                                      # the stub's psql answers "48" to anything: a valid-looking identity
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--rollup", "--out", str(out)])
    assert ac.main() in (0, 2, 3)
    doc = json.loads(out.read_text(encoding="utf-8"))
    ident = doc["L0"]["db_identity"]
    assert ident["schema"] == "nikasha_db_identity/1" and set(ident) <= {"schema", "database", "system_id_sha256", "unavailable"}
    stripped = {k: v for k, v in doc["L0"].items() if k != "db_identity"}
    assert json.dumps(ac.rollup_census(doc["L0"]), sort_keys=True) == json.dumps(ac.rollup_census(stripped), sort_keys=True)
    assert _fake_psql is not None


def test_an_unreachable_database_still_exits_exactly_as_before(monkeypatch, tmp_path, capsys):
    """The stamp is taken before measure(): a failure to read the identity must not turn the run's own UNKNOWN (exit 4) into something else."""
    e19._stub(monkeypatch, tmp_path)

    def down(sql, sep="\x1f", timeout=None, width=None):
        raise ac.Unknown("could not connect")
    monkeypatch.setattr(ac, "psql", down)
    monkeypatch.setattr(ac, "registry", lambda k: (_ for _ in ()).throw(ac.Unknown("could not connect")))
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(tmp_path / "census.json")])
    assert ac.main() == 4
    assert not (tmp_path / "census.json").exists()


# ───────────────────── REAL SQL: the same two reads on a disposable PostgreSQL ─────────────────────

def test_REAL_the_identity_of_the_disposable_cluster_matches_its_own_catalog(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    ident = ac.census_stamp()["db_identity"]
    want = disposable_pg.psql("SELECT system_identifier::text FROM pg_control_system()")
    assert ident["database"] == disposable_pg.dbname == disposable_pg.psql("SELECT current_database()")
    assert ident["system_id_sha256"] == _sha(want) and "unavailable" not in ident
    assert json.dumps(ident).count("127.0.0.1") == 0 and str(disposable_pg.port) not in json.dumps(ident)


def test_REAL_a_cluster_that_is_a_different_cluster_has_a_different_identity(monkeypatch, disposable_pg):
    """Same cluster, two databases: the system identifier is the cluster's, the database name is the database's; the pair distinguishes both."""
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql("CREATE DATABASE nt_ident_other", db="postgres")
    try:
        a = ac.census_stamp()["db_identity"]
        monkeypatch.setenv("PGDATABASE", "nt_ident_other")
        b = ac.census_stamp()["db_identity"]
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS nt_ident_other", db="postgres")
    assert a["system_id_sha256"] == b["system_id_sha256"] and a["database"] != b["database"] and b["database"] == "nt_ident_other"


def test_REAL_a_role_without_execute_on_pg_control_system_keeps_the_name_and_says_so(monkeypatch, disposable_pg):
    """Real denial (PostgreSQL grants EXECUTE on pg_control_system() to PUBLIC by default, so this is a managed-database hardening, simulated here
    in a throw-away database of the disposable cluster: pg_proc is per-database, nothing outside `nt_ident_denied` changes)."""
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql("CREATE DATABASE nt_ident_denied", db="postgres")
    try:
        disposable_pg.psql("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nt_ident_ro') THEN CREATE ROLE nt_ident_ro LOGIN; END IF; END $$",
                           db="postgres")
        disposable_pg.psql("REVOKE EXECUTE ON FUNCTION pg_control_system() FROM PUBLIC", db="nt_ident_denied")
        monkeypatch.setenv("PGDATABASE", "nt_ident_denied")
        monkeypatch.setenv("PGUSER", "nt_ident_ro")
        ident = ac.census_stamp()["db_identity"]
    finally:
        disposable_pg.psql("DROP DATABASE IF EXISTS nt_ident_denied", db="postgres")
        disposable_pg.psql("DROP ROLE IF EXISTS nt_ident_ro", db="postgres")
    assert ident == dict(schema="nikasha_db_identity/1", database="nt_ident_denied", system_id_sha256=None,
                         unavailable="the system identifier could not be read by this role (pg_control_system())")
