"""SR-F4-STORE-EXACT amend-1: every verifier / gate / served reader of a stored REAL column reads it EXACTLY (`::float8`), not as the driver's shortest-decimal text.

The round-1 fix (test_od1_f4_exact.py) made the window verifier's own window read exact. The ruling's amendment audited the other readers; the ones below read a REAL
the verifier compares, uses as a tolerance, or serves, and were lossy:

  reader                                              REAL column(s)                            what consumes it
  window_verifier  contact read (junction/endpoint)   ka_gochara_contact.delta_lambda           the contact accuracy `bm.accuracy_degrees` (a comparison tolerance)
  record_verifier  residence-contact read             ka_gochara_contact.delta_lambda           the same tolerance
  contact_certify  contact ledger read                ka_gochara_contact.delta_lambda           the same tolerance
  record_derivation.stored_path_records               relationship_record evidence_*/severity   the record verifier's result-policy check
  scope_response._window_qualification (batch, single) eval_window.objective_value              the served qualification entry
  serving_reader._WINDOW_COLUMNS                      eval_window score/evidence_for/_against/severity   the served window page
  near_miss_verifier stored-row read                  ka_gochara_near_miss.delta_t              `precision_problems` bound check

Oracle (one per reader). The source of truth is IEEE-754 binary32, never the code under test: the REAL the database stores for the decimal 0.1 is the binary32
0x3DCCCCCD = 13421773 · 2⁻²⁷ = 0.100000001490116119384765625, a double that is NOT 0.1; the driver's default text read of that REAL is the shortest decimal "0.1",
i.e. the double 0.1 (a different number). Each reader is run against a real disposable PostgreSQL table with REAL columns holding such a value, and must return the
binary32 widened to double. The PLANTED REVERSION — the same statement with its `::float8` removed (the reading the ruling forbids) — must read the other number, which
is what makes the exact-equality oracle able to fail. The statements under test are the production source text (`_production_sql` pulls them from the module file), not
copies; the `serving_reader` constant and the module functions are called as production calls them.

The guard that keeps this from recurring is `platform/scripts/governance/check_f4_exact_reads.py` (+ its test).
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import near_miss_verifier as nmv
from services.gochara_kernel import record_derivation as rd
from services.gochara_kernel import scope_response as sr
from services.gochara_kernel import serving_reader as srv

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX

KERNEL = Path(srv.__file__).resolve().parent
GUARD = Path(__file__).resolve().parents[4] / "scripts" / "governance" / "check_f4_exact_reads.py"

# binary32 closed forms (mantissa · 2^exp): the exact double of each stored REAL, and the double of the decimal the driver's text read yields.
EXACT = {                      # decimal -> the exact value the database holds for `x::real`
    0.1: 13421773 / 2 ** 27,   # 0x3DCCCCCD
    0.3: 10066330 / 2 ** 25,   # 0x3E99999A
    0.7: 11744051 / 2 ** 24,   # 0x3F333333
    0.9: 15099494 / 2 ** 24,   # 0x3F666666
    1.1: 9227469 / 2 ** 23,    # 0x3F8CCCCD
    2.2: 9227469 / 2 ** 22,    # 0x400CCCCD
}

CHART, GEN, CLS, PATH, VER = "c", "g", "marriage", "P3", "1.0.0"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 2, tzinfo=timezone.utc)
ID = {k: str(uuid.uuid5(uuid.NAMESPACE_DNS, k)) for k in ("contact", "record", "window", "nmobj")}

_DDL = """
CREATE TABLE public.ka_gochara_physical_object (physical_object_id int PRIMARY KEY, canonical_target text);
CREATE TABLE public.ka_gochara_contact (chart_id text, generation text, contact_id uuid, physical_object_id int, body text, relation_kind text,
  t_in timestamptz, t_out timestamptz, t_exact timestamptz, delta_lambda REAL, delta_t REAL);
CREATE TABLE public.ka_gochara_relationship_record (record_id uuid, chart_id text, generation text, event_class text, path_id text, rule_version text,
  contact_id uuid, agent text, relation text, object_role text, object_kind text, object_id int, operator_role text, provenance text, ruling_ref text,
  admission_state text, house_from_frame int, frame_kind text, frame_arg text, affected_person text, temporal_support_state text,
  temporal_support_intervals tstzrange[], evidence_for_occurrence REAL, evidence_against_occurrence REAL, severity REAL, outcome_valence_for_native text,
  coverage_partition_kind text, coverage_partition_key text);
CREATE TABLE public.ka_gochara_record_prerequisite (record_id uuid, predicate_id text, result text);
CREATE TABLE public.ka_gochara_eval_window (window_id uuid, chart_id text, generation text, event_class text, path_id text, rule_version text,
  interval tstzrange, peak_instant timestamptz, score REAL, evidence_for REAL, evidence_against REAL, outcome_valence_for_native text, severity REAL,
  null_states_used text[], objective text, objective_value REAL, qualification jsonb);
CREATE TABLE public.ka_gochara_eval_window_record (chart_id text, generation text, event_class text, path_id text, rule_version text, window_id uuid, record_id uuid);
CREATE TABLE public.kala_gochara_coverage (chart_id text, generation text, partition_kind text, partition_key text, completed_horizon tstzrange);
CREATE TABLE public.ka_gochara_near_miss (chart_id text, generation text, near_miss_object_id uuid, ordinal int, delta_t REAL);
"""

_ROWS = [
    ("INSERT INTO public.ka_gochara_physical_object VALUES (1, 'span:Aries')", ()),
    ("INSERT INTO public.ka_gochara_contact VALUES (%s,%s,%s,1,'jupiter','residence',%s,%s,%s,0.1::real,0.1::real)", (CHART, GEN, ID["contact"], T0, T1, T0)),
    ("INSERT INTO public.ka_gochara_relationship_record VALUES (%s,%s,%s,%s,%s,%s,%s,'jupiter','residence','target','kind',1,'op','prov','rule','adm',1,"
     "'natal',NULL,'self','supported',NULL,0.7::real,0.3::real,1.1::real,'unqualified','event_class',%s)", (ID["record"], CHART, GEN, CLS, PATH, VER, ID["contact"], CLS)),
    ("INSERT INTO public.ka_gochara_eval_window VALUES (%s,%s,%s,%s,%s,%s,tstzrange(%s,%s),%s,0.9::real,0.7::real,0.3::real,'unqualified',1.1::real,"
     "'{}','objective',2.2::real,'{}'::jsonb)", (ID["window"], CHART, GEN, CLS, PATH, VER, T0, T1, T0)),
    ("INSERT INTO public.ka_gochara_eval_window_record VALUES (%s,%s,%s,%s,%s,%s,%s)", (CHART, GEN, CLS, PATH, VER, ID["window"], ID["record"])),
    ("INSERT INTO public.kala_gochara_coverage VALUES (%s,%s,'event_class',%s,tstzrange(%s,%s))", (CHART, GEN, CLS, T0, T1)),
    ("INSERT INTO public.ka_gochara_near_miss VALUES (%s,%s,%s,1,0.1::real)", (CHART, GEN, ID["nmobj"])),
]


@pytest.fixture(scope="module")
def pg():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}f4xr_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
        conn.execute(_DDL)
        for sql, params in _ROWS:
            conn.execute(sql, params)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


class _TextRead:
    """The PLANTED REVERSION: the same connection, every statement with its `::float8` widening removed — the default text read of a REAL that the ruling forbids."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        sql = re.sub(r",\s*delta_t::float8 AS delta_t", "", sql)           # the near-miss reader re-selects delta_t after `*`; without it `*` carries the text read
        return self._conn.execute(sql.replace("::float8", ""), params) if params is not None else self._conn.execute(sql.replace("::float8", ""))


def _guard():
    name = "check_f4_exact_reads_for_readers"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, GUARD)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod                 # a dataclass in the module resolves its own module through sys.modules
        spec.loader.exec_module(mod)
    return sys.modules[name]


def _production_sql(module_file: str, needle: str) -> str:
    """The production statement (the whole flattened string expression) of `services/gochara_kernel/<module_file>` that contains `needle`."""
    g = _guard()
    hits = [t for _, t in g._sql_strings(ast.parse((KERNEL / module_file).read_text())) if needle in t]
    assert len(hits) == 1, (module_file, needle, len(hits))
    return hits[0]


def _first(cur):
    row = cur.fetchall()[0]
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


# each reader: conn -> the list of REAL values it returned, in a fixed order
def _r_window_verifier_contact(conn):
    sql = _production_sql("window_verifier.py", "lower(cov.completed_horizon), upper(cov.completed_horizon), c.delta_lambda")
    return [_first(conn.execute(sql, (CHART, GEN, CLS, PATH, VER)))[-1]]


def _r_record_verifier_contact(conn):
    sql = _production_sql("record_verifier.py", "c.t_in, c.t_out, c.delta_lambda")
    return [_first(conn.execute(sql, (CHART, GEN)))[-1]]


def _r_contact_certify_contact(conn):
    sql = _production_sql("contact_certify.py", "c.t_in, c.t_out, c.delta_lambda")
    return [_first(conn.execute(sql, (CHART, GEN)))[-1]]


def _r_record_derivation(conn):
    (rec,) = rd.stored_path_records(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id=PATH, rule_version=VER)
    return [rec["ev_for"], rec["ev_against"], rec["severity"]]


def _r_scope_response_batch(conn):
    return [sr._window_qualification(conn, CHART, GEN, [{"window_id": ID["window"]}], batch=True)[0]["objective_value"]]


def _r_scope_response_single(conn):
    return [sr._window_qualification(conn, CHART, GEN, [{"window_id": ID["window"]}], batch=False)[0]["objective_value"]]


def _r_serving_reader(conn):
    row = _first(conn.execute("SELECT " + srv._WINDOW_COLUMNS + " FROM public.ka_gochara_eval_window w"))
    return [row[9], row[10], row[11], row[13]]           # score, evidence_for, evidence_against, severity (the page's own column order)


def _r_near_miss_verifier(conn):
    sql = _production_sql("near_miss_verifier.py", "AS object_id")
    (row,) = nmv._rows(conn.execute(sql, (CHART, GEN, ID["nmobj"])))
    return [row["delta_t"]]


READERS = {
    "window_verifier.contact_delta_lambda": (_r_window_verifier_contact, [EXACT[0.1]]),
    "record_verifier.contact_delta_lambda": (_r_record_verifier_contact, [EXACT[0.1]]),
    "contact_certify.contact_delta_lambda": (_r_contact_certify_contact, [EXACT[0.1]]),
    "record_derivation.record_results": (_r_record_derivation, [EXACT[0.7], EXACT[0.3], EXACT[1.1]]),
    "scope_response.objective_value_batch": (_r_scope_response_batch, [EXACT[2.2]]),
    "scope_response.objective_value_single": (_r_scope_response_single, [EXACT[2.2]]),
    "serving_reader.window_page": (_r_serving_reader, [EXACT[0.9], EXACT[0.7], EXACT[0.3], EXACT[1.1]]),
    "near_miss_verifier.delta_t": (_r_near_miss_verifier, [EXACT[0.1]]),
}


def test_the_premise_a_real_is_not_its_shortest_decimal():
    """binary32 (not the code under test): each stored REAL is a different double from the decimal that prints it."""
    import struct
    for dec, exact in EXACT.items():
        assert exact != dec, dec
        assert struct.unpack(">f", bytes.fromhex(f"{struct.unpack('>I', struct.pack('>f', dec))[0]:08x}"))[0] == exact      # the hand-written closed form is the binary32
        assert float(repr(dec)) == dec != exact


@pytest.mark.parametrize("name", sorted(READERS))
def test_reader_returns_the_exact_stored_float4(pg, name):
    read, want = READERS[name]
    assert read(pg) == want, name


@pytest.mark.parametrize("name", sorted(READERS))
def test_planted_text_read_reversion_reads_the_other_number(pg, name):
    """The oracle can fail: with `::float8` removed the same reader returns the shortest decimal, which is NOT the stored number."""
    read, want = READERS[name]
    got = read(_TextRead(pg))
    shortest = [float(repr(next(d for d, e in EXACT.items() if e == w))) for w in want]
    assert got == shortest and got != want, (name, got, want)
