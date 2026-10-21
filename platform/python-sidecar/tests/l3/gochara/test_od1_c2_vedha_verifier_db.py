"""SR-OD1 C2 — the verifier's OWN SQL (`vedha_verifier._RECORDS_SQL`, `_RESIDENCE_SQL`, `_PAIRS_SQL`) against a throwaway database.

The recording-connection tests (`test_od1_c2_vedha_verifier.py`) cannot execute SQL, so what only SQL does is checked here on stand-in
tables carrying the real column names (the full A5 migration chain is not needed to read them):

  C2-S1 a contact stored with no end (`coverage.truncated`) is closed at the completed horizon of THE EVENT CLASS being verified — another
        class's horizon is not used (revert: the horizon join drops the partition_key filter ⇒ the other class's later horizon closes it);
  C2-S2 only RESIDENCE contacts in a numbered sign of the listed bodies are read; only ADMITTED SCORED records of the grain are derived
        (revert: the relation filter is dropped ⇒ a conjunction contact at a sign-like target would count).

Skipped (NOT_RUN) when the disposable server is unreachable; a hostile admin DSN is an error, never a skip.
"""
from __future__ import annotations

import json
import pathlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX

from services.gochara_kernel import vedha_verifier as vv

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "gochara_rules" / "fixtures" / "l0_vedha_rows_2026_10_02.json"
PAIR_ROWS = [tuple(r) for r in json.loads(FIXTURE.read_text())]
T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
CHART, GEN, CLS, OTHER = str(uuid.uuid4()), "5.0", "marriage", "career"
D = lambda day: T0 + timedelta(days=day)           # noqa: E731

DDL = """
CREATE TABLE public.bg_transit_rules (graha text, primary_house int, vedha_house int, classical_citation text, rule_type text);
CREATE TABLE public.ka_gochara_physical_object (physical_object_id uuid PRIMARY KEY, body text, relation_kind text, canonical_target text);
CREATE TABLE public.ka_gochara_contact (chart_id uuid, generation text, contact_id uuid, physical_object_id uuid, body text,
  relation_kind text, t_in timestamptz, t_out timestamptz);
CREATE TABLE public.kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text, completed_horizon tstzrange);
CREATE TABLE public.ka_gochara_relationship_record (record_id uuid, chart_id uuid, generation text, event_class text, path_id text,
  rule_version text, agent text, house_from_frame int, object_id uuid, temporal_support_intervals tstzmultirange,
  admission_state text, operator_role text);
"""


@pytest.fixture()
def db():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}c2v_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
        conn.execute(DDL)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _object(conn, body, relation, target):
    oid = str(uuid.uuid4())
    conn.execute("INSERT INTO public.ka_gochara_physical_object VALUES (%s, %s, %s, %s)", (oid, body, relation, target))
    return oid


def _contact(conn, body, relation, target, t_in, t_out):
    conn.execute("INSERT INTO public.ka_gochara_contact VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                 (CHART, GEN, str(uuid.uuid4()), _object(conn, body, relation, target), body, relation, t_in, t_out))


def _horizon(conn, cls, lo, hi):
    conn.execute("INSERT INTO public.kala_gochara_coverage VALUES (%s, %s, 'event_class', %s, tstzrange(%s, %s, '[)'))",
                 (CHART, GEN, cls, lo, hi))


def _record(conn, agent, house, sign, lo, hi, *, admission="admitted", role="scored"):
    conn.execute("INSERT INTO public.ka_gochara_relationship_record VALUES (%s, %s, %s, %s, 'P2', '1.0.0', %s, %s, %s,"
                 " ('{[' || %s::text || ',' || %s::text || ')}')::tstzmultirange, %s, %s)",
                 (str(uuid.uuid4()), CHART, GEN, CLS, agent, house, _object(conn, agent, "residence", f"span:{sign}"),
                  lo.isoformat(), hi.isoformat(), admission, role))


def _world(conn):
    for row in PAIR_ROWS:
        conn.execute("INSERT INTO public.bg_transit_rules VALUES (%s, %s, %s, %s, %s)", row)
    _record(conn, "sun", 3, 1, D(10), D(40))                                         # the Sun in the 3rd (Aries) from an Aquarius Moon
    _record(conn, "sun", 6, 4, D(10), D(40), admission="not_admitted")               # not an admitted record: never derived
    _record(conn, "sun", 6, 4, D(10), D(40), role="testimony")                       # not a scored record: never derived
    for b in ("sun", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"):
        _contact(conn, b, "residence", "span:2", D(-5), D(400))
    _contact(conn, "mars", "residence", "span:2", D(-5), D(20))
    _contact(conn, "mars", "residence", "span:7", D(20), None)                        # Mars in Libra, stored with no end (truncated)
    _contact(conn, "mercury", "conjunction", "point:200", D(0), D(400))              # not a residence contact: never read
    _horizon(conn, CLS, D(-5), D(30))
    _horizon(conn, OTHER, D(-5), D(500))


def test_c2_s1_a_truncated_contact_is_closed_at_the_horizon_of_the_class_being_verified(db):
    _world(db)
    ov = vv.derive_overlay(db, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0", moon_sign=11)
    r = ov(next(iter(ov._records)))
    assert r.value_at(D(25)) == 0.0                                                   # Mars [20, horizon 30) in the vedha house
    assert r.value_at(D(35)) is None and r.unknown_reason_at(D(35)) == "obstructor_residence_unknown"   # beyond CLS's horizon: unknown
    assert ov.summary()["open_contacts_without_horizon"] == 0


def test_c2_s2_only_admitted_scored_records_and_residence_contacts_are_read(db):
    _world(db)
    ov = vv.derive_overlay(db, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0", moon_sign=11)
    assert ov.summary()["records"] == 1
    # with no horizon row for the class the open contact cannot be closed: it is left out and counted
    db.execute("DELETE FROM public.kala_gochara_coverage WHERE partition_key = %s", (CLS,))
    ov = vv.derive_overlay(db, chart_id=CHART, generation=GEN, event_class=CLS, path_id="P2", rule_version="1.0.0", moon_sign=11)
    assert ov.summary()["open_contacts_without_horizon"] == 1
