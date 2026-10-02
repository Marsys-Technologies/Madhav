"""A5.3 — AM-14 Moon-resolved period-role domain (Codex round 6 R2; Stream B's migration 1232, PR #2909).

Moon exclusion follows the RESOLVED concrete transiting agent, per role obligation. A Moon-resolved
portion of a `period_lord:*` interval is ACCOUNTED as `excluded_moon_tier` — neither a missing search
interval nor a completed geometry search — when the applied schema can account it, and stays an
honest `missing_inputs` when it cannot (the schema is read, never assumed). The independent verifier
derives the same ledger. The integration tests apply Stream B's 1232 on top of 1206 on a throwaway
database and let ITS completeness function judge this writer's output; they skip when the migration
file is not available (it is read from the repo, or from PR #2909's branch until it merges).
"""
from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import targets
from services.gochara_kernel.inventory_store import InventoryStore
from services.gochara_kernel.rule_registry import RuleRegistryStore

from . import test_a53_inventory as base
from .test_a53_am5_writer import make_ephe
from .test_a53_inventory import (CHART, CHART_ID, DASHA, H0, H1, SEALED, create_am5_database,
                                 drop_am5_database)

GEN = writer_mod.GENERATION
MIGRATION_1232 = "1232_gochara_search_moon_scope_domain.sql"
PR_REF = "origin/pravaha/b6-am14-moon-domain-1232"


def _sql_1232() -> str | None:
    here = base.MIGRATIONS / MIGRATION_1232
    if here.exists():
        return here.read_text()
    out = subprocess.run(["git", "show", f"{PR_REF}:platform/migrations/{MIGRATION_1232}"],
                         capture_output=True, text=True, cwd=str(base.MIGRATIONS))
    return out.stdout if out.returncode == 0 and out.stdout.strip() else None


# ── the planner (pure) ───────────────────────────────────────────────────────────────────────────────

def _row(i, level, lord, a, b):
    return inv.DashaRow(str(uuid.UUID(int=i)), level, lord, a, b)


#: a Jupiter Mahādaśā with a MOON Antardaśā inside the horizon, and a Sun pratyantara inside it
MOON_BHUKTI = [
    _row(1, 1, "jupiter", base._dt(2024, 6, 1), base._dt(2026, 6, 1)),
    _row(2, 2, "moon", base._dt(2024, 12, 1), base._dt(2025, 2, 1)),
    _row(3, 2, "saturn", base._dt(2025, 2, 1), base._dt(2025, 4, 1)),
    _row(4, 3, "sun", base._dt(2024, 12, 20), base._dt(2025, 1, 15)),
    _row(5, 3, "moon", base._dt(2025, 1, 15), base._dt(2025, 2, 1)),
    _row(6, 3, "mars", base._dt(2025, 2, 1), base._dt(2025, 4, 1)),
]


def _plan(cap, rows=MOON_BHUKTI, cls="marriage"):
    return inv.plan_class_inventory(
        event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=SEALED, capability=cap,
        path_exclusions={"P5": base.P5_EXCL}, dasha_rows=rows)


def _states_by_role(plan):
    by_ob = {o.ob_id: o.agent for o in plan.obligations}
    out: dict[str, set] = {}
    for v in plan.intervals:
        if by_ob[v.ob_id].startswith("period_lord:"):
            out.setdefault(by_ob[v.ob_id], set()).add(v.state)
    return out


def test_with_the_domain_accounting_only_the_moon_resolved_role_portion_is_excluded():
    plan = _plan(inv.SearchCapability(True, True, True, moon_scope_domain=True))
    roles = _states_by_role(plan)
    # the Moon Antardaśā excludes ONLY the `ad` obligation's Moon portion; the Jupiter MD lord's
    # delivery during the Moon bhukti is still searched
    assert roles["period_lord:md"] == {inv.STATE_COMPLETE}
    assert inv.STATE_EXCLUDED_MOON in roles["period_lord:ad"]
    assert inv.STATE_EXCLUDED_MOON in roles["period_lord:pd"]
    moon_pieces = [v for v in plan.intervals if v.state == inv.STATE_EXCLUDED_MOON]
    assert moon_pieces and all(v.detail["resolved_agent"] == "moon" for v in moon_pieces)
    assert all(v.detail["tier"] == "moon_resolved_domain (AM-14)" for v in moon_pieces)


def test_the_excluded_portions_are_exactly_the_moon_rows_clipped_to_the_horizon():
    plan = _plan(inv.SearchCapability(True, True, True, moon_scope_domain=True))
    by_ob = {o.ob_id: o.agent for o in plan.obligations}
    ad = sorted((v.start, v.end) for v in plan.intervals
                if v.state == inv.STATE_EXCLUDED_MOON and by_ob[v.ob_id] == "period_lord:ad")
    assert set(ad) == {(H0, base._dt(2025, 2, 1))}                      # Moon AD [2024-12-01, 2025-02-01) ∩ horizon
    pd = sorted((v.start, v.end) for v in plan.intervals
                if v.state == inv.STATE_EXCLUDED_MOON and by_ob[v.ob_id] == "period_lord:pd")
    assert set(pd) == {(base._dt(2025, 1, 15), base._dt(2025, 2, 1))}   # Moon PD, clipped


def test_without_the_domain_accounting_the_same_portion_stays_an_honest_missing_input():
    plan = _plan(inv.SearchCapability(True, True, True, moon_scope_domain=False))
    assert not any(v.state == inv.STATE_EXCLUDED_MOON for v in plan.intervals)
    moon = [v for v in plan.intervals if v.detail and v.detail.get("resolved_agent") == "moon"]
    assert moon and all(v.state == inv.STATE_MISSING and v.detail["tier"] == "moon_on_demand (AM-4)"
                        for v in moon)


def test_the_exclusion_follows_the_transiting_agent_not_the_natal_moon():
    """Moon-agent EDGES are not stored (AM-4), but the Moon as a natal TARGET and the Moon frame of
    other agents are untouched: some class still has obligations aimed at the natal Moon's point, and
    none of them is a Moon-agent obligation."""
    moon_point = targets.point_target(CHART["natal"]["Moon"])
    aimed, moon_agent = 0, 0
    for cls in ("marriage", "career_change", "major_gain", "childbirth", "relocation"):
        for o in _plan(inv.SearchCapability(True, True, True, moon_scope_domain=True), cls=cls).obligations:
            aimed += o.target == moon_point
            moon_agent += o.agent == "moon"
    assert aimed > 0 and moon_agent == 0


# ── the vector carries the scope ─────────────────────────────────────────────────────────────────────

def test_the_input_vector_states_the_stored_scope():
    assert iv.STORED_SCOPE == "stored_non_moon"


# ── against the REAL schema, judged by Stream B's 1232 ────────────────────────────────────────────────

@pytest.fixture(params=[False, True], ids=["1206_only", "with_1232"])
def moon_run(request, monkeypatch, tmp_path):
    import psycopg
    sql = None
    if request.param:
        sql = _sql_1232()
        if sql is None:
            pytest.skip("migration 1232 (PR #2909) is not available here")
    admin, name, dsn = create_am5_database("moon")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        if sql is not None:
            with conn.transaction():
                conn.execute(sql)
        # the AD 'venus' [2024-12-01, 2025-02-01) is the Moon's Antardaśā in this chart
        conn.execute("UPDATE public.chart_dashas SET lord_graha = 'Moon'"
                     " WHERE dasha_row_id = %s", (str(uuid.UUID(int=2)),))
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
        RuleRegistryStore(conn).seed()
        ephe = make_ephe(tmp_path)
        w = writer_mod.GocharaV5Writer()

        def step(key):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-moon", db_conn=conn,
                              config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe},
                              dry_run=False)
            with conn.transaction():
                return w.run_substep(ctx, SubStep(key=key, label=key))
        yield step, conn, request.param
    finally:
        conn.close()
        drop_am5_database(admin, name)


def _violations(conn):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        return conn.execute(
            "SELECT event_class, violation FROM"
            " public.ka_gochara_search_completeness_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()


def _chain(step):
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP,
              "inventory:marriage", "coverage:marriage"):
        step(k)


def _ad_states(conn):
    return {r[0] for r in conn.execute(
        "SELECT v.state FROM public.ka_gochara_search_interval v JOIN public.ka_gochara_search_obligation o"
        " ON (o.chart_id,o.generation,o.event_class,o.ob_id) = (v.chart_id,v.generation,v.event_class,v.ob_id)"
        " WHERE o.agent = 'period_lord:ad' AND v.event_class = 'marriage' AND v.generation = %s",
        (GEN,)).fetchall()}


def test_the_writer_stores_the_moon_portion_as_the_schema_can_account_it(moon_run):
    step, conn, has_1232 = moon_run
    _chain(step)
    assert InventoryStore(conn).moon_scope_available() is has_1232      # READ from the applied schema
    states = _ad_states(conn)
    assert ("excluded_moon_tier" in states) is has_1232
    assert ("missing_inputs" in states) is (not has_1232)
    # the Jupiter-equivalent MD lord (Saturn here) is never touched by a Moon bhukti
    assert {r[0] for r in conn.execute(
        "SELECT v.state FROM public.ka_gochara_search_interval v JOIN public.ka_gochara_search_obligation o"
        " ON (o.chart_id,o.generation,o.event_class,o.ob_id) = (v.chart_id,v.generation,v.event_class,v.ob_id)"
        " WHERE o.agent = 'period_lord:md' AND v.event_class = 'marriage'").fetchall()} == {"searched_complete"}


def test_the_independent_verifier_derives_the_same_ledger_either_way(moon_run):
    """The ledger digest is re-derived from the pinned daśā rows by code that shares nothing with the
    planner; it must equal the stored one with and without the domain accounting. (The class-level
    verify substep still refuses P2 — its independent derivation is a separate open item — so the
    ledger derivation is called directly on the stored obligations.)"""
    from services.gochara_kernel import inventory_verifier as ver
    step, conn, has_1232 = moon_run
    _chain(step)
    obs = [r[0] for r in conn.execute(
        "SELECT canonical_bytes FROM public.ka_gochara_search_obligation WHERE event_class = 'marriage'"
        " AND generation = %s ORDER BY canonical_bytes", (GEN,)).fetchall()]
    cap = {"position_probe": True, "arc_index": True, "aspect_span_solver": True,
           "moon_scope_domain": has_1232}
    stored = conn.execute("SELECT ledger_digest FROM public.ka_gochara_search_inventory"
                          " WHERE event_class = 'marriage' AND generation = %s", (GEN,)).fetchone()[0]
    assert ver.rederive_ledger_digest(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                                      obligations=obs, capability=cap) == stored
    # told the WRONG fact about the schema, it disagrees — the check has teeth
    wrong = dict(cap, moon_scope_domain=not has_1232)
    assert ver.rederive_ledger_digest(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                                      obligations=obs, capability=wrong) != stored


def test_stream_bs_completeness_function_judges_the_writers_output(moon_run):
    step, conn, has_1232 = moon_run
    _chain(step)
    names = {v for _, v in _violations(conn)}
    if has_1232:
        # the Moon-resolved portion is accounted: no missing input, no unaccounted/extra domain, scope stated
        assert not names & {"missing_inputs_present", "moon_domain_missing", "moon_domain_extra",
                            "stored_scope_missing", "moon_exclusion_on_non_period_obligation"}
    else:
        assert "missing_inputs_present" in names                         # 1206 alone: the class cannot seal


def test_with_1232_a_builder_that_does_not_account_the_domain_is_caught(moon_run, monkeypatch):
    step, conn, has_1232 = moon_run
    if not has_1232:
        pytest.skip("needs 1232")
    monkeypatch.setattr(InventoryStore, "moon_scope_available", lambda self: False)
    _chain(step)
    names = {v for _, v in _violations(conn)}
    assert {"missing_inputs_present", "moon_domain_missing"} <= names    # the unperformed search is not hidden
