"""SR-OD1 C1 — the provider's OWN SQL (`vedha_source._RESIDENCE_SQL`) against a throwaway database.

The recording connection of `test_od1_c1_vedha_provider.py` cannot execute SQL, so what only SQL does is checked here on stand-in tables
carrying the real column names (the full A5 migration chain is not needed to read them):

  C1-S1 a residence contact stored without an end (`coverage.truncated`) is closed at the completed horizon of THE EVENT CLASS being
        built — another class's horizon is not used (revert: the horizon join drops the partition_key filter ⇒ the other class's later
        horizon closes it and the unknown stretch reads as an obstruction-free 1.0);
  C1-S2 only RESIDENCE contacts of the listed bodies (the nodes included, the Moon never) are read, whatever else the ledger holds
        (revert: the relation filter is dropped ⇒ a conjunction contact at a sign-like target would count as a residence).

Skipped (NOT_RUN) when the disposable server is unreachable; a hostile admin DSN is an error, never a skip.
"""
from __future__ import annotations

import uuid

import pytest

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX
from .test_od1_c1_vedha_provider import CHART, CLS, D, GEN, PAIR_ROWS, SUN, VREF
from services.gochara_kernel import vedha_source as vs

OTHER = "career"

DDL = """
CREATE TABLE public.bg_transit_rules (graha text, primary_house int, vedha_house int, classical_citation text, rule_type text);
CREATE TABLE public.ka_gochara_physical_object (physical_object_id uuid PRIMARY KEY, body text, relation_kind text, canonical_target text);
CREATE TABLE public.ka_gochara_contact (chart_id uuid, generation text, contact_id uuid, physical_object_id uuid, body text,
  relation_kind text, t_in timestamptz, t_out timestamptz);
CREATE TABLE public.kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text, completed_horizon tstzrange);
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
    name = f"{DB_PREFIX}c1v_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
        conn.execute(DDL)
        for row in PAIR_ROWS:
            conn.execute("INSERT INTO public.bg_transit_rules VALUES (%s, %s, %s, %s, %s)", row)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _contact(conn, body, relation, target, t_in, t_out):
    oid = str(uuid.uuid4())
    conn.execute("INSERT INTO public.ka_gochara_physical_object VALUES (%s, %s, %s, %s)", (oid, body, relation, target))
    conn.execute("INSERT INTO public.ka_gochara_contact VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                 (CHART, GEN, str(uuid.uuid4()), oid, body, relation, t_in, t_out))


def _horizon(conn, cls, lo, hi):
    conn.execute("INSERT INTO public.kala_gochara_coverage VALUES (%s, %s, 'event_class', %s, tstzrange(%s, %s, '[)'))",
                 (CHART, GEN, cls, lo, hi))


def _world(conn):
    for b in ("sun", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"):
        _contact(conn, b, "residence", "span:2", D(-5), D(400))
    _contact(conn, "mars", "residence", "span:2", D(-5), D(20))
    _contact(conn, "mars", "residence", "span:7", D(20), None)                  # Mars in Libra (the Sun's vedha house), stored with no end
    _contact(conn, "mercury", "conjunction", "point:200", D(0), D(400))        # not a residence contact: never read
    _contact(conn, "moon", "residence", "span:7", D(0), D(400))                # the Moon is never an obstructor source
    _horizon(conn, CLS, D(-5), D(30))
    _horizon(conn, OTHER, D(-5), D(500))


def test_c1_s1_an_open_contact_is_closed_at_the_horizon_of_the_class_being_built(db):
    _world(db)
    rec = SUN()
    ov = vs.SOURCE.for_grain(db, chart_id=CHART, generation=GEN, event_class=CLS, records=[rec]).overlay(rec, VREF)
    assert ov.value_at(D(25)) == 0.0                                            # Mars [20, horizon 30) sits in the vedha house
    assert ov.value_at(D(35)) is None and ov.unknown_reason_at(D(35)) == "obstructor_residence_unknown"   # beyond CLS's horizon: unknown
    other = vs.SOURCE.for_grain(db, chart_id=CHART, generation=GEN, event_class=OTHER, records=[rec])
    assert other.overlay(rec, VREF).value_at(D(35)) == 0.0                      # the other class's own, later horizon closes it for THAT class only


def test_c1_s2_only_residence_contacts_of_the_obstructor_bodies_are_read(db):
    _world(db)
    rec = SUN()
    prov = vs.SOURCE.for_grain(db, chart_id=CHART, generation=GEN, event_class=CLS, records=[rec])
    ov = prov.overlay(rec, VREF)
    assert [(s.t_in, s.state) for s in ov.segments][0] == (D(10), "inactive")  # the Moon in Libra and the Mercury conjunction obstruct nothing
    # with no horizon row for the class the open contact cannot be closed: it is left out and counted — a gap, not inactivity
    db.execute("DELETE FROM public.kala_gochara_coverage WHERE partition_key = %s", (CLS,))
    prov = vs.SOURCE.for_grain(db, chart_id=CHART, generation=GEN, event_class=CLS, records=[rec])
    ov = prov.overlay(rec, VREF)
    assert prov.summary()["open_contacts_without_horizon"] == 1 and ov.value_at(D(25)) is None
