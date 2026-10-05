"""Deploy gate (platform/scripts/data-plane-ownership-status.ts) across the three trigger states.

PIECE 2 of the data-plane revert DISABLES the 81 guard/capture triggers (ALTER TABLE ... DISABLE
TRIGGER) and leaves their 81 attestation rows untouched; rollback is ENABLE TRIGGER. The gate has
to read GREEN with every trigger enabled, with every trigger disabled, and after the re-enable,
while still refusing a missing, renamed, re-typed, re-pointed or re-defined trigger.

This test takes the three trigger statements (capture count, shape, surface-vs-attestation) out of
the REAL gate source, runs them on a disposable Postgres against a miniature of the protected
schema (same trigger names, same ``tgtype`` 31 / 21, same function names, attestation rows taken
exactly the way migrations 1035/1036 take them), and asserts the verdict in each state.

The TypeScript-side count comparison (``Number(l1) !== L1_ACTIVE_TABLES.length - 1`` ...) is
mirrored here as ``expected_capture_counts``; a static check ties the mirror to the source text.
"""
from __future__ import annotations

import pathlib
import re
import sys
import warnings

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, pg, q, requires_pg  # noqa: E402,F401

GATE = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "data-plane-ownership-status.ts"
SRC = GATE.read_text(encoding="utf-8")

if not HAVE_PG:
    warnings.warn(f"{pathlib.Path(__file__).name}: DB-backed gate tests SKIPPED, not passed: {PG_SKIP_REASON}",
                  UserWarning, stacklevel=1)

L1_TABLES = ("chart_facts", "chart_dashas", "chart_divisionals")      # chart_dashas: guard only
L2_TABLES = ("bodha_msr_signals", "bodha_cgm_nodes")


def _sql_after(marker: str) -> str:
    start = SRC.index(marker)
    first = SRC.index("`", start) + 1
    return SRC[first:SRC.index("`", first)]


CAPTURE_SQL = _sql_after("const triggers = await pool.query")
SHAPE_SQL = _sql_after("const triggerShape = await pool.query")
SURFACE_SQL = _sql_after("const triggerSurface = await pool.query")


def _lit(tables) -> str:
    return "ARRAY[" + ",".join(f"'{t}'" for t in tables) + "]::text[]"


def _bind(sql: str, *arrays) -> str:
    for i, arr in enumerate(arrays, 1):
        sql = sql.replace(f"${i}", _lit(arr))
    assert "$" not in sql
    return sql


SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS pgcrypto;
{"".join(f"CREATE TABLE public.{t} (id int, chart_id uuid);" for t in L1_TABLES + L2_TABLES)}
CREATE FUNCTION public.l1_data_plane_guard_active_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
CREATE FUNCTION public.l1_data_plane_capture_row() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
CREATE FUNCTION public.l2_data_plane_guard_active_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
CREATE FUNCTION public.l2_data_plane_capture_row() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
{"".join(f'''
CREATE TRIGGER l1_data_plane_mutation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.{t}
  FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_guard_active_mutation();''' for t in L1_TABLES)}
{"".join(f'''
CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON public.{t}
  FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row();''' for t in L1_TABLES if t != "chart_dashas")}
{"".join(f'''
CREATE TRIGGER l2_data_plane_mutation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.{t}
  FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_guard_active_mutation();
CREATE TRIGGER l2_data_plane_capture AFTER INSERT OR UPDATE ON public.{t}
  FOR EACH ROW EXECUTE FUNCTION public.l2_data_plane_capture_row();''' for t in L2_TABLES)}
CREATE TABLE public.l1_data_plane_trigger_attestations (
  table_name text NOT NULL, trigger_name text NOT NULL, trigger_type smallint NOT NULL, enabled "char" NOT NULL,
  function_oid oid NOT NULL, function_signature text NOT NULL, definition_digest text NOT NULL,
  PRIMARY KEY(table_name, trigger_name));
CREATE TABLE public.l2_data_plane_trigger_attestations (LIKE public.l1_data_plane_trigger_attestations INCLUDING ALL);
"""

# the attestation rows, taken exactly as migrations 1035 / 1036 take them (enabled state recorded as installed: 'O')
ATTEST = """
INSERT INTO public.{layer}_data_plane_trigger_attestations
SELECT c.relname,t.tgname,t.tgtype,t.tgenabled,t.tgfoid,t.tgfoid::regprocedure::text,
       encode(digest(pg_get_triggerdef(t.oid, true), 'sha256'), 'hex')
FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname = ANY({tables});
"""


def expected_capture_counts() -> tuple[int, int]:
    """Mirror of the TS comparison: L1 = all L1 tables but chart_dashas, L2 = every L2 table."""
    return len(L1_TABLES) - 1, len(L2_TABLES)


def verdicts(port: int, db: str) -> dict[str, bool]:
    """True = the gate would pass this statement. Same statements, same parameters as the gate."""
    l1_capture = [t for t in L1_TABLES if t != "chart_dashas"]
    row = q(port, db, _bind(CAPTURE_SQL, l1_capture, L2_TABLES)).split("|")
    counts_ok = (int(row[0]), int(row[1])) == expected_capture_counts()
    shape_unsafe = q(port, db, _bind(SHAPE_SQL, L1_TABLES + L2_TABLES)) == "t"
    surface_unsafe = q(port, db, _bind(SURFACE_SQL, L1_TABLES + L2_TABLES)) == "t"
    return {"capture_count": counts_ok, "shape": not shape_unsafe, "surface": not surface_unsafe}


def _all(v: dict[str, bool]) -> bool:
    return all(v.values())


@pytest.fixture()
def gate_db(pg):
    db = new_db(pg)
    r = psql(pg, db, SCHEMA)
    assert r.returncode == 0, r.stderr
    assert psql(pg, db, ATTEST.format(layer="l1", tables=_lit(L1_TABLES))).returncode == 0
    assert psql(pg, db, ATTEST.format(layer="l2", tables=_lit(L2_TABLES))).returncode == 0
    return pg, db


def _set_all(port, db, verb: str):
    for t in L1_TABLES + L2_TABLES:
        assert psql(port, db, f"ALTER TABLE public.{t} {verb} TRIGGER USER;").returncode == 0


# --------------------------------------------------------------------------- static

def test_gate_still_checks_every_trigger_dimension_by_name():
    """No check was weakened to ride out the disabled state: name, tgtype, function, digest, count all stay."""
    assert "t.tgname='l1_data_plane_capture'" in CAPTURE_SQL and "t.tgname='l2_data_plane_capture'" in CAPTURE_SQL
    assert "t.tgtype<>31" in SHAPE_SQL and "t.tgtype<>21" in SHAPE_SQL
    for fn in ("l1_data_plane_guard_active_mutation", "l1_data_plane_capture_row",
               "l2_data_plane_guard_active_mutation", "l2_data_plane_capture_row"):
        assert f"public.{fn}()'::regprocedure" in SHAPE_SQL
    assert "cardinality($1::text[])" in SHAPE_SQL
    for dim in ("a.table_name=e.table_name", "a.trigger_name=e.trigger_name", "a.trigger_type=e.trigger_type",
                "a.function_oid=e.function_oid", "a.function_signature=e.function_signature",
                "a.definition_digest=e.definition_digest"):
        assert dim in SURFACE_SQL
    assert "WHERE a.table_name IS NULL OR e.table_name IS NULL" in SURFACE_SQL
    # the ONLY accepted deviation is: same trigger, attested enabled, now 'D'
    assert "(a.enabled=e.enabled OR (a.enabled='D' AND e.enabled IN ('O','A')))" in SURFACE_SQL
    assert "t.tgenabled IN ('O','A','D')" in CAPTURE_SQL
    assert "'R'" not in CAPTURE_SQL and "'R'" not in SURFACE_SQL
    assert "Number(triggers.rows[0]?.l1) !== L1_ACTIVE_TABLES.length - 1" in SRC
    assert "Number(triggers.rows[0]?.l2) !== L2_ACTIVE_TABLES.length" in SRC


# --------------------------------------------------------------------------- the three states

@requires_pg
def test_gate_is_green_enabled_then_disabled_then_re_enabled(gate_db):
    port, db = gate_db
    assert _all(verdicts(port, db)), "baseline: all triggers enabled as attested"
    _set_all(port, db, "DISABLE")
    assert q(port, db, "SELECT count(DISTINCT tgenabled) || tgenabled FROM pg_trigger "
                       "WHERE NOT tgisinternal GROUP BY tgenabled") == "1D"
    assert _all(verdicts(port, db)), "all triggers disabled ('D'): attestation rows unchanged"
    _set_all(port, db, "ENABLE")
    assert _all(verdicts(port, db)), "after rollback (ENABLE TRIGGER)"
    assert q(port, db, "SELECT string_agg(DISTINCT enabled::text, ',') FROM public.l1_data_plane_trigger_attestations") == "O"


@requires_pg
def test_gate_accepts_a_mixed_state_where_each_trigger_is_as_attested_or_disabled(gate_db):
    port, db = gate_db
    assert psql(port, db, "ALTER TABLE public.chart_facts DISABLE TRIGGER l1_data_plane_capture;").returncode == 0
    assert _all(verdicts(port, db))


# --------------------------------------------------------------------------- still fails closed

@requires_pg
@pytest.mark.parametrize("state", ["enabled", "disabled"])
@pytest.mark.parametrize("breakage,failing", [
    ("DROP TRIGGER l1_data_plane_capture ON public.chart_facts;", {"capture_count", "surface"}),
    ("DROP TRIGGER l2_data_plane_mutation_guard ON public.bodha_msr_signals;", {"shape", "surface"}),
    ("ALTER TRIGGER l2_data_plane_capture ON public.bodha_cgm_nodes RENAME TO l2_data_plane_capture_x;",
     {"capture_count", "surface"}),
    ("ALTER TABLE public.chart_facts DISABLE TRIGGER l1_data_plane_capture; "
     "ALTER TABLE public.chart_facts ENABLE REPLICA TRIGGER l1_data_plane_capture;", {"capture_count", "surface"}),
    ("DROP TRIGGER l1_data_plane_capture ON public.chart_facts; "
     "CREATE TRIGGER l1_data_plane_capture AFTER INSERT ON public.chart_facts "
     "FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row();", {"shape", "surface"}),
    ("DROP TRIGGER l1_data_plane_capture ON public.chart_facts; "
     "CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON public.chart_facts "
     "FOR EACH ROW WHEN (NEW.id > 0) EXECUTE FUNCTION public.l1_data_plane_capture_row();", {"surface"}),
    ("CREATE TRIGGER extra_unattested AFTER INSERT ON public.chart_facts "
     "FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_capture_row();", {"surface"}),
    ("DELETE FROM public.l2_data_plane_trigger_attestations WHERE table_name='bodha_msr_signals' "
     "AND trigger_name='l2_data_plane_capture';", {"surface"}),
])
def test_gate_still_refuses_drift_in_either_state(gate_db, state, breakage, failing):
    port, db = gate_db
    if state == "disabled":
        _set_all(port, db, "DISABLE")
    r = psql(port, db, breakage)
    assert r.returncode == 0, r.stderr
    got = verdicts(port, db)
    assert {name for name, ok in got.items() if not ok} >= failing, got
    assert not _all(got)


@requires_pg
def test_a_disabled_trigger_must_have_been_attested_enabled(gate_db):
    """'D' is accepted only for a trigger attested as enabled; an attested-'D' row does not launder drift."""
    port, db = gate_db
    assert psql(port, db, "UPDATE public.l1_data_plane_trigger_attestations SET enabled='R' "
                          "WHERE table_name='chart_facts' AND trigger_name='l1_data_plane_capture';").returncode == 0
    _set_all(port, db, "DISABLE")
    assert not verdicts(port, db)["surface"]
