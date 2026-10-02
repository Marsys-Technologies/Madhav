"""A5.3 — the COMPLETE builder write flow as the RESTRICTED builder (Codex round 9, R9-4).

The role suite built as SUPERUSER, so it could not see that 1240's new window CHECK helper
(`ka_gochara_window_qualification_ok`) lacked a builder EXECUTE grant: with PUBLIC EXECUTE revoked (production's
bootstrap) a table INSERT grant alone does not let the restricted builder insert a window. This suite runs the whole
build — convention, manifest, snapshot, inventory, coverage, sky events, records, windows — as `data_plane_builder`
on the faithful mirror, after the real builder-grant migrations (1216 tables, 1220 functions, 1234 window
tables/functions) and 1240, and proves that REMOVING the helper grant makes the flow fail on exactly that function.
The builder stays at zero privileges on the verification table throughout.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import window_gate as wg

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t, _world
from .test_a53_window_verification_gate import CLS, SPANS, _materialise

UTC = timezone.utc
HELPER = "public.ka_gochara_window_qualification_ok(jsonb)"
# the L1 / L0 stubs the writer READS: in production the builder reaches the real tables through other migrations
# (1217, 1225, ...); the stubs are granted explicitly so this suite isolates the gochara grants
STUBS = ("charts", "chart_facts", "chart_dashas", "bg_transit_rules", "_migrations_applied")


@pytest.fixture()
def rworld(monkeypatch, tmp_path):
    yield from _world(monkeypatch, tmp_path, faithful=True)


@pytest.fixture(autouse=True)
def _consistent_sky(rworld, monkeypatch):
    SPANS.clear()

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=UTC)
        return (195.0 if any(a <= t < b for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)
    # 1206's completeness trigger belongs to its own suite; this one is about the builder's write privileges
    rworld.conn.execute("ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER"
                        " ka_gochara_generation_seal_z_search_complete")


@contextmanager
def as_builder(conn):
    conn.execute("SET ROLE data_plane_builder")
    try:
        yield
    finally:
        conn.execute("RESET ROLE")


def _prepare(w):
    w.set_periods([(2, _t(1, 1), _t(2, 1))])             # the L1 stub rows, set up as the fixture owner
    for table in STUBS:
        w.conn.execute(f"GRANT SELECT ON public.{table} TO data_plane_builder")
    SPANS["saturn"] = [(_t(1, 10), _t(2, 20))]


def _builder_flow(w):
    """Everything the builder writes, as the builder: manifest/snapshot/inventory/coverage, sky events, records,
    windows (the window phase also runs the in-build verification, which only REPORTS for an unprivileged session)."""
    with as_builder(w.conn):
        w.boot()
        w.seed("saturn", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
        counts = _materialise(w, "P3", {"saturn": (_t(1, 10), _t(2, 20))})
        out = {p: w.step(f"window:{CLS}:{p}") for p in ("P1", "P2", "P3", "P4")}      # the BUILDER's steps only
    return counts, out


def test_the_restricted_builder_can_run_the_complete_write_flow(rworld):
    w = rworld
    _prepare(w)
    counts, out = _builder_flow(w)
    assert counts["records"] == 1
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window").fetchone()[0] >= 1
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] >= 1
    assert all("verification_pending_verifier_principal" in r.notes for r in out.values()), [r.notes for r in out.values()]
    # and it held nothing on the verification table the whole time
    with as_builder(w.conn):
        for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert w.conn.execute("SELECT has_table_privilege(current_user,"
                                  " 'public.ka_gochara_eval_window_verification', %s)", (privilege,)).fetchone()[0] is False
        assert wg.can_write_verification(w.conn) is False


def test_the_builder_holds_execute_on_the_check_helper_and_nothing_else_new(rworld):
    w = rworld
    held = {r[0] for r in w.conn.execute(
        "SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
        " WHERE n.nspname = 'public' AND p.proname LIKE 'ka_gochara%%'"
        " AND has_function_privilege('data_plane_builder', p.oid, 'EXECUTE')").fetchall()}
    assert "ka_gochara_window_qualification_ok(jsonb)" in held
    # the verification-side machinery is NOT the builder's (digests, gate, replay, seal helpers)
    for name in ("ka_gochara_eval_window_content_digest", "ka_gochara_eval_window_expected_digest",
                 "ka_gochara_window_verification_violations", "ka_gochara_candidate_gate_violations",
                 "ka_gochara_f4_token"):
        assert not any(h.startswith(name + "(") for h in held), name


def test_mutation_removing_the_helper_grant_makes_the_builder_flow_fail_on_exactly_that_function(rworld):
    import psycopg
    w = rworld
    _prepare(w)
    w.conn.execute(f"REVOKE EXECUTE ON FUNCTION {HELPER} FROM data_plane_builder")
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="ka_gochara_window_qualification_ok"):
        _builder_flow(w)
