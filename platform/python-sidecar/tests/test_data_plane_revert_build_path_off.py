"""Data-plane surgical revert (N-165, route A), piece 1: the build path is OFF in code.

What is pinned here
-------------------
1. Both wrappers' bypass is ON by default: the ONE explicit switch
   ``ga_writers.data_plane_contracts.data_plane_build_path_enabled()`` returns False, so the L1 and
   L2 wrappers hand every call straight to the original writer -- no cursor, no SQL, no
   ``l2_generation=`` note -- even on a real psycopg connection (the production shape; the
   connection class no longer decides). Flipping the switch to True restores the previous
   behaviour (the contract machinery is dormant, not deleted).
2. The L1 ``authorize_l1_chart_facts_delete`` receipt call and the L2 ``assert_l2_msr_delete_safe``
   call (both of which raise outside an admitted data-plane context) are not made; the L2
   dependency check runs instead as read-only SQL against the live tables, and the MSR child
   scope reads the live table, not a ``pg_temp`` shadow that is never created.
3. The six writers that relied on the guard trigger to fill ``bodha_msr_signals.producer_asset_id``
   set it themselves, to the value the guard set (``v_asset``, i.e. the writer's own asset id).
4. ``bo_samskara`` and ``bo_pramana_mapa`` no longer read data-plane history; the
   ``context_generation`` detector is gone.
5. No writer reads any ``l1_/l2_data_plane_*`` object, and the identity helpers the writers
   import (``stable_uuid`` & co.) are untouched.

The DB-backed parts use ``tests/pg_disposable.py`` (a throw-away local cluster, never a project
database) and skip loudly when no Postgres binaries exist.
"""
from __future__ import annotations

import pathlib
import re
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import bodha_writers.data_plane_contracts as l2c  # noqa: E402
import ga_writers.data_plane_contracts as l1c  # noqa: E402
import ga_writers.data_plane_runtime as l1rt  # noqa: E402
from bodha_writers import _idempotency as l2idem  # noqa: E402
from ga_writers import _idempotency as l1idem  # noqa: E402
from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, pg, q, requires_pg  # noqa: E402,F401

SIDECAR = pathlib.Path(__file__).resolve().parents[1]
WRITERS = SIDECAR / "pipeline" / "orchestrator" / "writers"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


# --------------------------------------------------------------------------- doubles

class _NoSqlConn:
    """Any attempt to touch the database is a test failure."""

    def __init__(self, module: str = "psycopg", **flags):
        self.__class__ = type("Connection", (_NoSqlConn,), {"__module__": module})
        for key, value in flags.items():
            setattr(self, key, value)

    def cursor(self, *a, **k):  # pragma: no cover - failure path
        raise AssertionError("wrapper touched the database with the build path off")

    def execute(self, *a, **k):  # pragma: no cover - failure path
        raise AssertionError("wrapper touched the database with the build path off")


def _psycopg_conn():
    """A connection whose class module is ``psycopg`` -- the production shape the wrapper keys on."""
    return _NoSqlConn("psycopg")


def _l1_double():
    return _NoSqlConn("tests", _l1_contract_test_double=True)


def _l2_double():
    return _NoSqlConn("tests", _l2_contract_test_double=True)


# --------------------------------------------------------------------------- 1. bypass is on

def test_the_single_build_path_switch_defaults_off():
    assert l1c.DATA_PLANE_BUILD_PATH_ENABLED is False
    assert l1c.data_plane_build_path_enabled() is False
    # one place only: the L2 module re-uses the same function object, it defines no second switch
    assert l2c.data_plane_build_path_enabled is l1c.data_plane_build_path_enabled
    assert l2idem.data_plane_build_path_enabled is l1c.data_plane_build_path_enabled
    assert l1idem.data_plane_build_path_enabled is l1c.data_plane_build_path_enabled
    assert l1rt.data_plane_build_path_enabled is l1c.data_plane_build_path_enabled
    assert not hasattr(l2c, "L2_DATA_PLANE_BUILD_PATH_ENABLED")
    assert not hasattr(l1c, "L1_DATA_PLANE_BUILD_PATH_ENABLED")


@pytest.mark.parametrize("make_conn", [_psycopg_conn, _l1_double])
def test_l1_wrapper_runs_original_writer_untouched(make_conn):
    from pipeline.orchestrator.writers import ContextSpec, WriterResult

    @l1rt.l1_producer_contract
    class _Probe:
        asset_id = "ga_positions"
        has_substeps = False
        calls = 0

        def run(self, ctx):
            type(self).calls += 1
            return WriterResult(asset_id=self.asset_id, rows_inserted=9)

    ctx = ContextSpec(
        asset_id="ga_positions", build_id="11111111-1111-4111-8111-111111111111",
        db_conn=make_conn(), config={"chart_id": CHART},
    )
    # the connection class alone would have switched the slow path on; only the switch holds it off
    assert l1rt._contract_sql_enabled(ctx.db_conn) is True
    result = _Probe().run(ctx)
    assert (result.rows_inserted, _Probe.calls) == (9, 1)


@pytest.mark.parametrize("make_conn", [_psycopg_conn, _l2_double])
def test_l2_wrapper_runs_original_writer_untouched(make_conn):
    seen = []

    @l2c.l2_producer("bo_laksana")
    class _Probe:
        def run(self, ctx):
            seen.append(ctx.config["chart_id"])
            return SimpleNamespace(rows_inserted=3, rows_updated=0, rows_skipped=0, notes=None)

    import uuid
    chart_uuid = uuid.UUID(CHART)
    ctx = SimpleNamespace(
        dry_run=False, db_conn=make_conn(), build_id="b1",
        config={"chart_id": chart_uuid},
    )
    assert l2c._contract_sql_enabled(ctx.db_conn) is True  # connection-class test alone says "go"
    result = _Probe().run(ctx)
    assert result.rows_inserted == 3
    assert result.notes is None, "no l2_generation= suffix is appended on the direct path"
    assert not hasattr(result, "_l2_partition_key")
    # the existing UUID -> str normalisation still runs before the bypass
    assert seen == [CHART]


def test_real_l1_writer_boundary_issues_no_sql_by_default(monkeypatch):
    from ga_writers import ga_positions_writer
    from pipeline.orchestrator.writers import ContextSpec, discover_all, list_writers

    discover_all()
    monkeypatch.setattr(ga_positions_writer, "build_ga_positions",
                        lambda **kwargs: {"total_chart_facts_rows": 9})
    ctx = ContextSpec(
        asset_id="ga_positions", build_id="11111111-1111-4111-8111-111111111111",
        db_conn=_psycopg_conn(),
        config={"chart_id": CHART, "birth_params": {"datetime_iso": "2000-01-01T12:00:00"}},
    )
    assert list_writers()["ga_positions"]().run(ctx).rows_inserted == 9


def test_contract_machinery_is_dormant_not_deleted(monkeypatch):
    """Switch on -> the wrappers' SQL path is reachable again (and only then)."""
    monkeypatch.setattr(l1c, "DATA_PLANE_BUILD_PATH_ENABLED", True)
    assert l1rt._contract_sql_enabled(_l1_double()) is True
    assert l1rt._contract_sql_enabled(_psycopg_conn()) is True
    assert l2c._contract_sql_enabled(_l2_double()) is True
    assert l2c._contract_sql_enabled(_psycopg_conn()) is True
    assert l2c._contract_sql_enabled(object()) is False  # non-psycopg, non-double stays ignored


def test_every_registered_writer_still_carries_its_wrapper_marker():
    """The decorators stay applied (flag-gated, not removed), so the switch is a one-line revert."""
    from pipeline.orchestrator.writers import discover_all, list_writers

    discover_all()
    writers = list_writers()
    # ga_fact_identity (migration 1334) derives an index from the 19 producers' chart_facts; it is not a data-plane producer and carries no marker.
    l1 = [a for a in writers if a.startswith("ga_") and a != "ga_fact_identity"]
    l2 = [a for a in writers if a.startswith("bo_") and a in l2c.CURRENT_WRITERS]
    assert len(l1) == 19 and len(l2) == 23
    assert all(writers[a].__l1_data_plane_contract__ is True for a in l1)


# --------------------------------------------------------------------------- 2. idempotency

class _L1RecordingConn:
    def __init__(self):
        self.sql: list[str] = []

    def execute(self, sql, params=None):
        self.sql.append(" ".join(sql.split()))
        return SimpleNamespace(rowcount=0)


def test_l1_delete_receipt_is_not_requested_with_build_path_off():
    conn = _L1RecordingConn()
    rows = [{"chart_id": CHART, "ayanamsha_id": "lahiri", "fact_category": "c1"}]
    l1idem.replace_prior_chart_facts(conn, rows)
    assert len(conn.sql) == 1 and conn.sql[0].startswith("DELETE FROM chart_facts")
    assert not any("authorize_l1_chart_facts_delete" in s for s in conn.sql)


def test_l1_delete_receipt_is_requested_with_build_path_on(monkeypatch):
    monkeypatch.setattr(l1c, "DATA_PLANE_BUILD_PATH_ENABLED", True)
    conn = _L1RecordingConn()
    l1idem.replace_prior_chart_facts(
        conn, [{"chart_id": CHART, "ayanamsha_id": "lahiri", "fact_category": "c1"}])
    assert conn.sql[0].startswith("SELECT public.authorize_l1_chart_facts_delete(")
    assert conn.sql[1].startswith("DELETE FROM chart_facts")


class _L2RecordingConn:
    """An L2 contract double: records SQL text (composed SQL rendered), answers the FK catalogue."""

    _l2_contract_test_double = True

    def __init__(self, fks=(), dependents=()):
        self.sql: list[str] = []
        self._fks = list(fks)
        self._dependents = set(dependents)

    def execute(self, sql, params=None):
        text = sql if isinstance(sql, str) else sql.as_string(None)
        text = " ".join(text.split())
        self.sql.append(text)
        if "FROM pg_constraint" in text:
            return SimpleNamespace(fetchall=lambda: list(self._fks), rowcount=0)
        if text.startswith("SELECT EXISTS"):
            table = re.search(r'FROM "public"\."(\w+)"', text).group(1)
            hit = table in self._dependents
            return SimpleNamespace(fetchone=lambda: (hit,), rowcount=0)
        return SimpleNamespace(rowcount=0)


def _msr_rows():
    return [{"chart_id": CHART, "ayanamsha_id": "lahiri", "signal_type_id": "st1"}]


def test_l2_msr_replace_uses_live_table_and_inline_check_with_build_path_off():
    conn = _L2RecordingConn(fks=[
        ("public", "bodha_signal_embeddings", "signal_id", 1, "signal_id"),
        ("public", "bodha_contradictions", "signal_a_id", 1, "signal_id"),
        ("public", "kala_future", "signal_id", 1, "signal_id"),
    ])
    l2idem.replace_prior_msr_signals(conn, _msr_rows())
    joined = "\n".join(conn.sql)
    assert "assert_l2_msr_delete_safe" not in joined
    assert "pg_temp" not in joined
    assert "SELECT signal_id FROM public.bodha_msr_signals" in joined
    # own-layer children are skipped; the one foreign-layer FK is checked, read-only
    exists = [s for s in conn.sql if s.startswith("SELECT EXISTS")]
    assert len(exists) == 1 and '"public"."kala_future"' in exists[0]
    assert not any("FOR UPDATE" in s for s in conn.sql)


def test_l2_msr_replace_is_blocked_by_a_dependent_row_in_scope():
    conn = _L2RecordingConn(
        fks=[("public", "kala_future", "signal_id", 1, "signal_id")],
        dependents={"kala_future"},
    )
    with pytest.raises(l2idem.MsrReplacementBlocked, match="kala_future"):
        l2idem.replace_prior_msr_signals(conn, _msr_rows())
    assert not any(s.startswith("DELETE") for s in conn.sql), "nothing is deleted once blocked"


def test_l2_msr_replace_rejects_an_unsupported_composite_foreign_key():
    conn = _L2RecordingConn(fks=[("public", "odd", "signal_id", 2, "signal_id")])
    with pytest.raises(l2idem.MsrReplacementBlocked, match="unsupported"):
        l2idem.replace_prior_msr_for_chart(conn, CHART, "lahiri", ["arudha"])


def test_l2_msr_replace_for_chart_uses_live_scope_table():
    conn = _L2RecordingConn()
    l2idem.replace_prior_msr_for_chart(conn, CHART, "lahiri", ["arudha"])
    joined = "\n".join(conn.sql)
    assert "pg_temp" not in joined and "assert_l2_msr_delete_safe" not in joined
    assert "SELECT signal_id FROM public.bodha_msr_signals" in joined


def test_l2_msr_replace_with_build_path_on_is_the_previous_behaviour(monkeypatch):
    monkeypatch.setattr(l1c, "DATA_PLANE_BUILD_PATH_ENABLED", True)
    conn = _L2RecordingConn()
    l2idem.replace_prior_msr_signals(conn, _msr_rows())
    joined = "\n".join(conn.sql)
    assert "assert_l2_msr_delete_safe" in joined
    assert "SELECT signal_id FROM pg_temp.bodha_msr_signals" in joined


def test_l2_inline_check_ignores_non_psycopg_non_double_connections():
    class _Plain:
        def execute(self, *a, **k):  # pragma: no cover - failure path
            raise AssertionError("plain unit doubles must stay out of the dependency check")

    l2idem._assert_msr_delete_safe(_Plain(), chart_id=CHART)


@requires_pg
def test_l2_inline_check_against_a_real_catalogue(pg):
    """The FK discovery and the scope filters, executed for real on a disposable Postgres."""
    import psycopg

    db = new_db(pg)
    ddl = """
    CREATE TABLE public.bodha_msr_signals (
      signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
      signal_type_id text NOT NULL, signal_type_class text NOT NULL);
    CREATE TABLE public.bodha_signal_embeddings (
      id serial PRIMARY KEY, signal_id uuid REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE);
    CREATE TABLE public.bodha_contradictions (
      id serial PRIMARY KEY, signal_a_id uuid REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE);
    CREATE TABLE public.kala_future (
      id serial PRIMARY KEY, signal_id uuid REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE);
    """
    assert psql(pg, db, ddl).returncode == 0
    s_in = "00000000-0000-4000-8000-000000000001"
    s_out = "00000000-0000-4000-8000-000000000002"
    assert psql(pg, db, f"""
      INSERT INTO public.bodha_msr_signals VALUES
        ('{s_in}', '{CHART}', 'lahiri', 'st1', 'cls'),
        ('{s_out}', '{CHART}', 'lahiri', 'st2', 'other');
      INSERT INTO public.bodha_signal_embeddings(signal_id) VALUES ('{s_in}');
      INSERT INTO public.bodha_contradictions(signal_a_id) VALUES ('{s_in}');
    """).returncode == 0

    with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db, autocommit=True) as conn:
        check = l2idem._assert_msr_delete_safe
        # own-layer children only: replaceable
        check(conn, chart_id=CHART, ayanamsha_ids=["lahiri"], signal_type_ids=["st1"])
        # a foreign-layer dependent on the OTHER signal does not block st1's replacement ...
        conn.execute("INSERT INTO public.kala_future(signal_id) VALUES (%s)", [s_out])
        check(conn, chart_id=CHART, ayanamsha_ids=["lahiri"], signal_type_ids=["st1"])
        # ... but blocks any scope that covers it (by type, by class, and unscoped)
        for kwargs in ({"signal_type_ids": ["st2"]}, {"signal_type_classes": ["other"]}, {}):
            with pytest.raises(l2idem.MsrReplacementBlocked, match="kala_future"):
                check(conn, chart_id=CHART, ayanamsha_ids=["lahiri"], **kwargs)
        # another chart is never in scope
        check(conn, chart_id="00000000-0000-4000-8000-0000000000ff", signal_type_ids=["st2"])


# --------------------------------------------------------------------------- 3. producer_asset_id

SIX = ("bo_laksana", "bo_arudha", "bo_special_lagna", "bo_sudarshana",
       "bo_vargottama_dhana", "bo_nakshatra_semantic")


def _insert_sql(asset: str) -> str:
    import importlib
    module = importlib.import_module(f"pipeline.orchestrator.writers.{asset}")
    return module._INSERT_SQL


def _columns_and_values(sql: str) -> tuple[list[str], list[str]]:
    code = re.sub(r"--[^\n]*", "", sql)
    cols = re.search(r"INSERT INTO public\.bodha_msr_signals\s*\((.*?)\)\s*VALUES", code, re.S).group(1)
    vals = re.search(r"VALUES\s*\((.*)\)\s*ON CONFLICT", code, re.S).group(1)
    split = lambda s: [p.strip() for p in re.split(r",(?![^(]*\))", s) if p.strip()]  # noqa: E731
    return split(cols), split(vals)


@pytest.mark.parametrize("asset", SIX)
def test_writer_sets_producer_asset_id_to_its_own_asset_id(asset):
    columns, values = _columns_and_values(_insert_sql(asset))
    assert len(columns) == len(values), "every column has exactly one value"
    assert columns.count("producer_asset_id") == 1
    assert values[columns.index("producer_asset_id")] == f"'{asset}'"
    # the literal is the writer's own registered asset id (what the guard trigger set: v_asset)
    import importlib
    module = importlib.import_module(f"pipeline.orchestrator.writers.{asset}")
    declared = {cls.asset_id for cls in vars(module).values()
                if isinstance(cls, type) and getattr(cls, "asset_id", None) == asset}
    assert declared == {asset}


def test_the_six_ids_are_exactly_the_ids_the_producer_check_constraint_admits():
    migration = (SIDECAR.parent / "supabase" / "migrations"
                 / "1036_data_plane_l2_producer_generations.sql").read_text()
    block = re.search(r"CHECK \(producer_asset_id IN \((.*?)\)\)", migration, re.S).group(1)
    admitted = set(re.findall(r"'(bo_\w+)'", block))
    assert admitted == set(SIX)


def test_no_other_writer_inserts_msr_rows():
    """bo_laksana_rerank only UPDATEs (the guard never filled a producer for it)."""
    inserters = sorted(
        p.stem for p in WRITERS.glob("bo_*.py")
        if re.search(r"INSERT\s+INTO\s+(public\.)?bodha_msr_signals", p.read_text())
    )
    assert inserters == sorted(SIX)


@requires_pg
@pytest.mark.parametrize("asset", SIX)
def test_the_writers_own_insert_statement_stores_its_producer_asset_id(pg, asset):
    """Run each writer's REAL _INSERT_SQL against a table with the production NOT NULL + CHECK."""
    import json
    import psycopg

    sql = _insert_sql(asset)
    columns, values = _columns_and_values(sql)
    names = [c for c in columns]
    db = new_db(pg)
    col_defs = ", ".join(f"{c} text" for c in names if c != "producer_asset_id")
    ddl = f"""
    CREATE TABLE public.bodha_msr_signals ({col_defs},
      producer_asset_id text NOT NULL
        CHECK (producer_asset_id IN ({", ".join(f"'{a}'" for a in SIX)})));
    CREATE UNIQUE INDEX ON public.bodha_msr_signals
      (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb);
    """
    assert psql(pg, db, ddl).returncode == 0
    params = {n: "x" for n in re.findall(r"%\((\w+)\)s", sql)}
    for name in params:
        if name.endswith("_jsonb") or name in ("classical_sources_jsonb",):
            params[name] = json.dumps({})
    params["chart_id"] = CHART
    with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db, autocommit=True) as conn:
        # the statement must run unchanged by any trigger: a plain table, no data-plane objects
        conn.execute(sql, params)
        (stored,) = conn.execute("SELECT producer_asset_id FROM public.bodha_msr_signals").fetchone()
    assert stored == asset


# --------------------------------------------------------------------------- 4. snapshot readers

def _fetch_existing():
    import importlib
    return importlib.import_module("pipeline.orchestrator.writers.bo_samskara")._fetch_existing_embeddings


def test_bo_samskara_reads_the_live_embedding_table_for_the_bound_chart():
    seen = {}

    class _Conn:
        def execute(self, sql, params=None):
            seen["sql"], seen["params"] = " ".join(sql.split()), params
            rows = [("s1", "sum", "[0.1,0.2]", "m", "v")]
            return SimpleNamespace(fetchall=lambda: rows)

    out = _fetch_existing()(_Conn(), CHART, "lahiri")
    assert "FROM public.bodha_signal_embeddings" in seen["sql"]
    assert "chart_id = %s AND ayanamsha_id = %s" in seen["sql"]
    assert "embedding_vec::text" in seen["sql"]
    assert "data_plane" not in seen["sql"]
    assert seen["params"] == [CHART, "lahiri"]
    assert out == {"s1": {"signal_id": "s1", "embedding_input_summary": "sum", "embedding_vec": "[0.1,0.2]",
                          "embedding_model": "m", "embedding_model_version": "v"}}


def test_bo_pramana_mapa_has_no_snapshot_reader_and_no_context_generation_detector(monkeypatch):
    import importlib
    mod = importlib.import_module("pipeline.orchestrator.writers.bo_pramana_mapa")
    assert not hasattr(mod, "_CONTEXT_GENERATION_SQL")
    source = (WRITERS / "bo_pramana_mapa.py").read_text()
    assert "l2_data_plane_row_snapshots" not in source
    assert "l2_data_plane_generation_heads" not in source
    assert "data_plane_l2_producer_generations" not in source
    monkeypatch.setattr(mod, "_count_one", lambda *_a, **_k: 0)
    result = mod.detect_l2_contract_integrity(object(), CHART)
    assert sorted(result) == ["discovery_grounding", "ledger_independence_and_duplicate_root",
                              "no_pre_answer", "signed_relation_and_cancellation"]
    assert all(entry["pass"] is True for entry in result.values())


def test_no_writer_reads_or_writes_data_plane_history():
    offenders = []
    for path in sorted(WRITERS.glob("*.py")) + sorted((SIDECAR / "ga_writers").glob("*.py")) \
            + sorted((SIDECAR / "bodha_writers").glob("*.py")):
        if path.name in ("data_plane_contracts.py", "data_plane_runtime.py",
                         "data_plane_resource_config_slice.py", "data_plane_resource_mechanism_slice.py"):
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]
            if re.search(r"\bl[12]_data_plane_\w+|data_plane_l[12]_producer|_data_plane_generation", code) \
                    and "authorize_l1_chart_facts_delete" not in code \
                    and "assert_l2_msr_delete_safe" not in code:
                offenders.append(f"{path.relative_to(SIDECAR)}:{number}")
    assert offenders == []


def test_row_identity_helpers_are_still_wired_into_the_writers():
    """Pravaha constraint: stable ids, build_id, parent_row_id are assigned by the writers, as before."""
    expect = {
        SIDECAR / "ga_writers" / "ga_dashas_writer.py": ("stable_uuid", "stabilize_hierarchical_uuids"),
        SIDECAR / "ga_writers" / "ga_condition_writer.py": ("stable_fact_id",),
        SIDECAR / "ga_writers" / "ga_tajaka_writer.py": ("stable_uuid",),
        SIDECAR / "pipeline" / "orchestrator" / "writers" / "bo_samskara.py": ("stable_semantic_uuid",),
    }
    for path, names in expect.items():
        text = path.read_text()
        for name in names:
            assert re.search(rf"\b{name}\(", text), f"{path.name} no longer calls {name}"
    dashas = (SIDECAR / "ga_writers" / "ga_dashas_writer.py").read_text()
    assert "parent_row_id" in dashas and "build_id" in dashas
