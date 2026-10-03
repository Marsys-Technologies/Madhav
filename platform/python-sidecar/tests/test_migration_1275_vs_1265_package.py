"""
Migration 1275 against the REAL 1265 frozen-row guard SQL (PR #3033 head 06e668944, vendored md5-pinned in fixtures/) on a production-mirrored
PostgreSQL: roles with production attributes, charts with row-level security ON (no FORCE), the four L5 tables as read live, the repo objects beside
the guards, the consent tables. 1275 is applied as amjis_app (no CREATE on schema public); the 1265 SQL is applied as amjis_app inside the grant/revoke
window, as its executor does. Both orders are run. The 29 tables of 1275 = the world's 4 L5 tables + 25 generic per-chart tables + the pool table.

Acceptance (SS N-108): ONE fixture in which (a) a direct DELETE on a guarded row is refused for every role, owner and superuser included, and a decoy
trigger cannot spoof the chart-deletion allowance, (b) deleting a throwaway chart removes ALL its rows in all 29 tables including the four guarded ones,
the other charts untouched, (c) 1275 refuses to apply when charts has FORCE ROW LEVEL SECURITY.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("l5_world_vendored", _HERE / "fixtures" / "l5_frozen_guard_world_vendored.py")
W = importlib.util.module_from_spec(_spec)
sys.modules["l5_world_vendored"] = W
_spec.loader.exec_module(W)
pg_cluster = W.pg_cluster  # the module-scoped fixture

_REPO = Path(__file__).resolve().parents[3]
M1275 = (_REPO / "platform" / "migrations" / "1275_chart_delete_reaches_phala_and_mimamsa_per_chart_tables.sql").read_text()
GUARD_SQL_MD5 = "d598ac283738769e5dee35411e190afd"

_ts = importlib.util.spec_from_file_location("t1275_tables", _HERE / "test_migration_1275_chart_delete_per_chart_tables.py")
T = importlib.util.module_from_spec(_ts)
sys.modules["t1275_tables"] = T
_ts.loader.exec_module(T)
TABLES = T.TABLES
WORLD_TABLES = {"mimamsa_predictions", "mimamsa_manifestation_sets", "brahma_prospective_ledger", "brahma_mimamsa_prediction_ledger"}
GUARDED = sorted(WORLD_TABLES)
GENERIC = [t for t in TABLES if t not in WORLD_TABLES]
CHART_A, CHART_B, CHART_C = W.CHART_A, W.CHART_B, W.CHART_C


def test_vendored_1265_sql_is_the_pinned_head():
    assert hashlib.md5(W.FORWARD.read_text(encoding="utf8").encode()).hexdigest() == GUARD_SQL_MD5
    assert "l5_frozen_chart_cascade_authorizes" in W.FORWARD.read_text(encoding="utf8")
    assert "SECURITY DEFINER" in W.FORWARD.read_text(encoding="utf8")


def _extend_world(w):
    """Add what 1275 needs beyond the 1265 world: build_run_assets, the 25 other per-chart tables, the pool table with its NO ACTION link; rows for the 3 charts."""
    with w.connect("postgres", autocommit=True) as c:
        c.execute("CREATE TABLE public.build_run_assets (run_id uuid NOT NULL REFERENCES public.build_runs(id), asset_id text NOT NULL)")
        for t in GENERIC:
            if t == "mimamsa_pool_contributions":
                continue
            c.execute(f"CREATE TABLE public.{t} (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, payload text)")
            c.execute(f"CREATE INDEX {t}_chart_idx ON public.{t} (chart_id)")
        c.execute("CREATE TABLE public.mimamsa_pool_contributions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL REFERENCES public.charts(id), payload text)")
        c.execute("CREATE INDEX mimamsa_pool_contributions_chart_idx ON public.mimamsa_pool_contributions (chart_id)")
        for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
            c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
        for (sq,) in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'").fetchall():
            c.execute(f'ALTER SEQUENCE public."{sq}" OWNER TO amjis_app')
        for chart in (CHART_A, CHART_B, CHART_C):
            for t in GENERIC + ["mimamsa_pool_contributions"]:
                for _ in range(2):
                    c.execute(f"INSERT INTO public.{t} (chart_id, payload) VALUES (%s, 'x')", (chart,))


def _guard_world(pg, order: str):
    w = W.make_world(pg, builder_guard=False)
    _extend_world(w)
    if order == "1265_first":
        w.apply_sql(W.FORWARD.read_text(encoding="utf8"))
        w.apply_sql(M1275, window=False)
    else:
        w.apply_sql(M1275, window=False)
        w.apply_sql(W.FORWARD.read_text(encoding="utf8"))
    return w


def _counts(w, chart):
    return {t: w.query(f"SELECT count(*) FROM public.{t} WHERE chart_id = %s", (chart,))[0][0] for t in TABLES}


def _route_delete(w, chart, role="amjis_app"):
    """The statements of platform/src/app/api/charts/[id]/route.ts:87-107 that touch this fixture: build_runs of the chart, then the charts row."""
    conn = w.connect(role)
    try:
        conn.execute("DELETE FROM public.build_run_assets WHERE run_id IN (SELECT id FROM public.build_runs WHERE chart_id = %s)", (chart,))
        conn.execute("DELETE FROM public.build_runs WHERE chart_id = %s", (chart,))
        conn.execute("DELETE FROM public.charts WHERE id = %s", (chart,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


ORDERS = ["1265_first", "1275_first"]


@pytest.mark.parametrize("order", ORDERS)
def test_both_orders_apply_and_the_links_and_guards_are_in_place(pg_cluster, order):
    w = _guard_world(pg_cluster, order)
    try:
        fks = dict(w.query("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='f' AND connamespace='public'::regnamespace AND confrelid='public.charts'::regclass"))
        for t in TABLES:
            assert fks[f"{t}_chart_id_fkey"] == "FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE", t
        trg = {r[0] for r in w.query("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")}
        assert any(t.startswith("mimamsa_predictions_frozen_row_guard") for t in trg), trg
        assert w.query("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'public.charts'::regclass") == [(True, False)]
    finally:
        W.drop_world(pg_cluster, w)


@pytest.mark.parametrize("order", ORDERS)
def test_ONE_FIXTURE_direct_delete_refused_for_every_role_then_chart_delete_removes_every_row_in_all_29_tables_of_that_chart_only(pg_cluster, order):
    w = _guard_world(pg_cluster, order)
    try:
        before = {c: _counts(w, c) for c in (CHART_A, CHART_B, CHART_C)}
        assert all(v > 0 for k, v in before[CHART_A].items()), before[CHART_A]
        # (a) a direct DELETE on each guarded table is refused for the owner, a superuser and the builder role; TRUNCATE too
        for t in GUARDED:
            for role in ("amjis_app", "postgres", "data_plane_builder", "role_orchestrator"):
                with pytest.raises(Exception) as ei:
                    w.exec(f"DELETE FROM public.{t} WHERE chart_id = %s", (CHART_A,), role=role)
                msg = str(ei.value)
                assert ("frozen" in msg or "permission denied" in msg or "cannot be deleted" in msg or "refused" in msg), (t, role, msg)
            with pytest.raises(Exception):
                w.exec(f"TRUNCATE public.{t}", role="postgres")
        assert _counts(w, CHART_A) == before[CHART_A], "a refused direct delete changed something"
        # (b) the chart delete
        _route_delete(w, CHART_A)
        assert _counts(w, CHART_A) == {t: 0 for t in TABLES}, {t: n for t, n in _counts(w, CHART_A).items() if n}
        assert _counts(w, CHART_B) == before[CHART_B] and _counts(w, CHART_C) == before[CHART_C]
        # and afterwards a direct delete on another chart's guarded row is still refused
        for t in GUARDED:
            with pytest.raises(Exception):
                w.exec(f"DELETE FROM public.{t} WHERE chart_id = %s", (CHART_B,), role="amjis_app")
        assert _counts(w, CHART_B) == before[CHART_B]
    finally:
        W.drop_world(pg_cluster, w)


@pytest.mark.parametrize("order", ORDERS)
def test_chart_delete_by_the_superuser_and_a_rolled_back_chart_delete(pg_cluster, order):
    w = _guard_world(pg_cluster, order)
    try:
        before = _counts(w, CHART_B)
        conn = w.connect("amjis_app")
        conn.execute("DELETE FROM public.build_runs WHERE chart_id = %s", (CHART_B,))
        conn.execute("DELETE FROM public.charts WHERE id = %s", (CHART_B,))
        assert conn.execute("SELECT count(*) FROM public.mimamsa_predictions WHERE chart_id = %s", (CHART_B,)).fetchone()[0] == 0
        conn.rollback()
        conn.close()
        assert _counts(w, CHART_B) == before
        w.exec("DELETE FROM public.build_runs WHERE chart_id = %s", (CHART_B,), role="postgres")
        w.exec("DELETE FROM public.charts WHERE id = %s", (CHART_B,), role="postgres")
        assert _counts(w, CHART_B) == {t: 0 for t in TABLES}
    finally:
        W.drop_world(pg_cluster, w)


@pytest.mark.parametrize("order", ORDERS)
def test_a_decoy_trigger_cannot_spoof_the_chart_deletion_allowance_with_charts_rls_on(pg_cluster, order):
    w = _guard_world(pg_cluster, order)
    try:
        w.exec("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'spoofer') THEN CREATE ROLE spoofer LOGIN; END IF; END $$", role="postgres")
        w.exec("GRANT USAGE ON SCHEMA public TO spoofer", role="postgres")
        w.exec("GRANT SELECT, DELETE ON public.mimamsa_predictions, public.brahma_prospective_ledger, public.brahma_mimamsa_prediction_ledger, public.mimamsa_manifestation_sets TO spoofer", role="postgres")
        w.exec("CREATE SCHEMA atk AUTHORIZATION spoofer", role="postgres")
        w.exec("CREATE TABLE atk.decoy (id int)", role="spoofer")
        w.exec("CREATE FUNCTION atk.fire() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN "
               "DELETE FROM public.mimamsa_predictions WHERE chart_id = '%s'; DELETE FROM public.brahma_prospective_ledger WHERE chart_id = '%s'; "
               "DELETE FROM public.brahma_mimamsa_prediction_ledger WHERE chart_id = '%s'; DELETE FROM public.mimamsa_manifestation_sets WHERE chart_id = '%s'; "
               "RETURN NEW; END $f$" % (CHART_A, CHART_A, CHART_A, CHART_A), role="spoofer")
        w.exec("CREATE TRIGGER decoy_fire AFTER INSERT ON atk.decoy FOR EACH ROW EXECUTE FUNCTION atk.fire()", role="spoofer")
        before = _counts(w, CHART_A)
        with pytest.raises(Exception) as ei:
            w.exec("INSERT INTO atk.decoy VALUES (1)", role="spoofer")
        assert "frozen" in str(ei.value) or "cannot be deleted" in str(ei.value) or "refused" in str(ei.value), str(ei.value)
        assert _counts(w, CHART_A) == before
    finally:
        W.drop_world(pg_cluster, w)


def test_1275_refuses_with_FORCE_ROW_LEVEL_SECURITY_on_charts_against_the_real_world(pg_cluster):
    w = W.make_world(pg_cluster, builder_guard=False)
    try:
        _extend_world(w)
        w.exec("ALTER TABLE public.charts FORCE ROW LEVEL SECURITY", role="amjis_app")
        with pytest.raises(Exception) as ei:
            w.apply_sql(M1275, window=False)
        assert "FORCE ROW LEVEL SECURITY" in str(ei.value) and "1265" in str(ei.value), str(ei.value)
    finally:
        W.drop_world(pg_cluster, w)


def test_the_pool_table_row_goes_with_its_chart_and_the_relinked_constraint_cascades(pg_cluster):
    w = _guard_world(pg_cluster, "1265_first")
    try:
        assert w.query("SELECT confdeltype::text FROM pg_constraint WHERE conname = 'mimamsa_pool_contributions_chart_id_fkey'") == [("c",)]
        _route_delete(w, CHART_C)
        assert w.query("SELECT count(*) FROM public.mimamsa_pool_contributions WHERE chart_id = %s", (CHART_C,)) == [(0,)]
        assert w.query("SELECT count(*) FROM public.mimamsa_pool_contributions WHERE chart_id = %s", (CHART_A,)) == [(2,)]
    finally:
        W.drop_world(pg_cluster, w)
