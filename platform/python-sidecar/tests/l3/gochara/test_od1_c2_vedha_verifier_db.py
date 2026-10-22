"""SR-OD1 C2 — the verifier's OWN SQL (`vedha_verifier._RECORDS_SQL`, `_CONVENTION_SQL`, `_PAIRS_SQL`) against a throwaway database.

The recording-connection tests (`test_od1_c2_vedha_verifier.py`) cannot execute SQL, so what only SQL does is checked here on stand-in
tables carrying the real column names (the full A5 migration chain is not needed to read them):

  C2-S1 the sky convention the verifier reproduces is THE GENERATION'S OWN row for THE EVENT CLASS being verified — another class' convention
        is not used, a class with none is refused, and a convention the verifier cannot reproduce (the true node) is refused, never replaced
        (revert: the convention join drops the partition_key filter ⇒ two rows ⇒ refused for the class that has one);
  C2-S2 only ADMITTED SCORED records of the grain are derived (revert: the admission / role filter is dropped ⇒ three records are derived);
  C2-S3 no stored contact is read for the obstructors' residence (the table is absent from the fixture: reading it would fail the statement).

The residence itself is derived from the real ephemeris (`SE_EPHE_PATH`): see `test_od1_vedha_residence.py`.
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
CREATE TABLE public.ka_gochara_sky_convention (convention_id text PRIMARY KEY, ayanamsha text, node_convention text);
CREATE TABLE public.ka_gochara_convention_bridge (kala_convention_id text PRIMARY KEY, sky_convention_id text);
CREATE TABLE public.kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text, completed_horizon tstzrange,
  convention_id text);
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
    conn.execute("INSERT INTO public.ka_gochara_sky_convention VALUES ('sky-mean', 'lahiri_chitrapaksha', 'mean')")
    conn.execute("INSERT INTO public.ka_gochara_sky_convention VALUES ('sky-true', 'lahiri_chitrapaksha', 'true')")
    conn.execute("INSERT INTO public.ka_gochara_convention_bridge VALUES ('mean', 'sky-mean'), ('true', 'sky-true')")
    conn.execute("INSERT INTO public.kala_gochara_coverage VALUES (%s, %s, 'event_class', %s, tstzrange(%s, %s), 'mean')", (CHART, GEN, CLS, D(-5), D(400)))
    conn.execute("INSERT INTO public.kala_gochara_coverage VALUES (%s, %s, 'event_class', %s, tstzrange(%s, %s), 'true')", (CHART, GEN, OTHER, D(-5), D(400)))


def _derive(conn, cls):
    return vv.derive_overlay(conn, chart_id=CHART, generation=GEN, event_class=cls, path_id="P2", rule_version="1.0.0", moon_sign=11)


def test_c2_s1_the_convention_is_the_generations_own_for_the_class_being_verified(db):
    _world(db)
    ov = _derive(db, CLS)
    assert ov.summary()["convention"] == {"ayanamsha": "lahiri_chitrapaksha", "node_convention": "mean"}
    assert ov.summary()["residence_source"] == vv.RESIDENCE_SOURCE
    db.execute("UPDATE public.ka_gochara_relationship_record SET event_class = %s", (OTHER,))
    with pytest.raises(vv.VedhaDerivationError, match="pinned sky convention"):      # the other class was built on the TRUE node: no switch, no substitution
        _derive(db, OTHER)
    db.execute("UPDATE public.ka_gochara_relationship_record SET event_class = 'unbuilt'")
    with pytest.raises(vv.VedhaDerivationError, match="not readable"):
        _derive(db, "unbuilt")


def test_c2_s2_only_admitted_scored_records_are_derived_and_no_contact_is_read(db):
    _world(db)
    ov = _derive(db, CLS)
    assert ov.summary()["records"] == 1
    r = ov(next(iter(ov._records)))
    assert r.applicable and r.complete and r.segments           # derived from the real sky; no `ka_gochara_contact` table even exists here
