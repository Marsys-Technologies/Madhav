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
        ephe = make_ephe(tmp_path, monkeypatch)
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


# ═══ Codex round 7 [2]: the consumed daśā population, and the mandatory scope response ══════════════════

from services.gochara_kernel import inventory_verifier as ver                    # noqa: E402
from services.gochara_kernel import scope_response as sr                         # noqa: E402

UTCZ = base.UTC


def _row(i, level, lord, a, b, *, build=base.PINNED_BUILD, system="vimshottari",
         ayan="lahiri_chitrapaksha", tier="two_pass_verified", parent=None):
    return {"dasha_row_id": str(uuid.UUID(int=i)), "level_n": level, "parent_row_id": parent,
            "lord_graha": lord, "start_iso": a, "end_iso": b, "build_id": build, "system_id": system,
            "ayanamsha_id": ayan, "verification_pass_status": tier}


A, B = base._dt(2024, 6, 1), base._dt(2026, 6, 1)
POP = [_row(1, 1, "Jupiter", A, B), _row(2, 2, "Moon", base._dt(2024, 12, 1), base._dt(2025, 2, 1)),
       _row(3, 2, "Saturn", base._dt(2025, 2, 1), base._dt(2025, 4, 1))]


def _check(consumed, pinned=POP, ids=None, chart=CHART_ID, horizon=(H0, H1)):
    return ver.check_dasha_population(consumed, pinned, chart_id=chart, horizon=horizon,
                                      consumed_ids=ids or [r["dasha_row_id"] for r in consumed])


def test_the_pinned_population_passes():
    assert _check(POP) == []


def test_a_wrong_build_moon_row_is_refused_not_made_authoritative_by_hashing_it():
    evil = _row(9, 2, "Moon", base._dt(2025, 1, 1), base._dt(2025, 3, 1), build="00000000-0000-4000-8000-000000000bad")
    out = _check(POP + [evil])
    assert any("frozen" in p for p in out)


def test_a_wrong_system_or_ayanamsha_or_tier_moon_row_is_refused():
    for kw, needle in (({"system": "yogini"}, "ayanāṃśa/system"), ({"ayan": "raman"}, "ayanāṃśa/system"),
                       ({"tier": "single_pass"}, "tier")):
        evil = _row(9, 2, "Moon", base._dt(2025, 1, 1), base._dt(2025, 3, 1), **kw)
        assert any(needle in p for p in _check(POP + [evil])), kw


def test_an_extra_row_outside_the_horizon_and_an_omitted_pinned_row_are_refused():
    outside = _row(8, 2, "Moon", base._dt(2023, 1, 1), base._dt(2023, 6, 1))
    assert any("extra" in p for p in _check(POP + [outside], pinned=POP + [outside]))
    assert any("omitted" in p for p in _check(POP[:2], pinned=POP))                 # row 3 not consumed


def test_a_consumed_id_that_resolves_to_no_row_and_a_non_madhav_level_are_refused():
    assert any("resolves to no row" in p for p in _check(POP, ids=[r["dasha_row_id"] for r in POP] + [str(uuid.UUID(int=77))]))
    lvl4 = _row(9, 4, "Moon", base._dt(2025, 1, 1), base._dt(2025, 1, 5))
    assert any("not MD/AD/PD" in p for p in _check(POP + [lvl4]))


def test_conflicting_pinned_rows_and_several_builds_on_a_non_canonical_chart_are_refused():
    twin = _row(10, 2, "Moon", base._dt(2024, 12, 1), base._dt(2025, 1, 15))        # same (level, parent, start)
    assert any("conflicting" in p for p in _check(POP, pinned=POP + [twin]))
    other_chart = "11111111-1111-4111-8111-111111111111"
    mixed = [dict(POP[0]), dict(POP[1], build_id="b2")]
    assert any("several builds" in p for p in _check(mixed, pinned=mixed, chart=other_chart))


def test_the_real_chain_validates_the_population_it_consumed(moon_run):
    step, conn, has_1232 = moon_run
    _chain(step)
    out = ver.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN)
    assert out["consumed"] >= 1


def test_a_snapshot_over_a_wrong_build_moon_row_fails_the_verifiers_ledger_derivation(moon_run):
    """The adversary at the SQL level: after the build, a wrong-build Moon row appears in the pinned
    population's place (the build of a consumed row is changed). The verifier must refuse to derive."""
    step, conn, has_1232 = moon_run
    _chain(step)
    conn.execute("UPDATE public.chart_dashas SET build_id = '00000000-0000-4000-8000-000000000bad'"
                 " WHERE dasha_row_id = %s", (str(uuid.UUID(int=2)),))
    with pytest.raises(RuntimeError, match="violates the §4.0 read contract"):
        ver.rederive_ledger_digest(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                                   obligations=[], capability={"position_probe": True, "arc_index": True})


# ── the mandatory response constructor ───────────────────────────────────────────────────────────────

def test_positive_and_no_window_responses_both_carry_the_bound_scope(moon_run):
    step, conn, has_1232 = moon_run
    _chain(step)
    pos = sr.coverage_response(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                               windows=[{"interval": "x"}])
    none = sr.coverage_response(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", windows=[])
    for r in (pos, none):
        # R8-5: the scope is carried; completeness is NOT claimed from it (this manifest is an unpublished candidate)
        assert r["stored_scope"] == "stored_non_moon" and r["completeness"] == "not_published"
        assert "Moon" in r["scope_statement"] and r["on_demand_answered"] == []
    assert pos["window_count"] == 1 and none["window_count"] == 0


def test_the_scope_is_unchanged_after_an_on_demand_query_and_the_answer_is_listed(moon_run):
    step, conn, has_1232 = moon_run
    _chain(step)
    before = sr.coverage_response(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", windows=[])
    kala = conn.execute("SELECT convention_id FROM public.kala_gochara_coverage WHERE generation = %s"
                        " AND partition_kind = 'event_class' LIMIT 1", (GEN,)).fetchone()[0]
    from services.gochara_kernel.record_store import RecordStore
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        RecordStore(conn).write_moon_coverage(
            chart_id=CHART_ID, generation=GEN, partition_key="moon:interval:2025-01-05/2025-01-06",
            convention_id=kala, horizon=(base._dt(2025, 1, 5), base._dt(2025, 1, 6)), resolution=1.0,
            relations_searched=["residence"], targets_requested=1, targets_resolved=1,
            state_counts={"resolved": 1, "unavailable": 0, "unqualified": 0}, unavailable_inputs={},
            unsearched_reason=None, build_id="b-od")
    after = sr.coverage_response(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", windows=[])
    assert before["stored_scope"] == after["stored_scope"] == "stored_non_moon"
    assert after["on_demand_answered"] == ["moon:interval:2025-01-05/2025-01-06"] and before["on_demand_answered"] == []


def test_a_manifest_without_the_scope_refuses_an_unqualified_completeness_claim(moon_run, monkeypatch):
    step, conn, has_1232 = moon_run
    real = iv.build_input_vector
    monkeypatch.setattr(iv, "build_input_vector", lambda *a, **k: {x: y for x, y in real(*a, **k).items()
                                                                  if x != "stored_scope"})
    monkeypatch.setattr(writer_mod.gk_input_vector, "build_input_vector", iv.build_input_vector)
    step(writer_mod.CONVENTION_SUBSTEP)
    step(writer_mod.MANIFEST_SUBSTEP)
    for windows in ([{"interval": "x"}], []):
        r = sr.coverage_response(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", windows=windows)
        assert r["completeness"] == "refused" and r["refusal"] == "stored_scope_missing"
        assert r["stored_scope"] is None and "scope_statement" not in r
    with pytest.raises(sr.ScopeMissing):
        sr.bound_stored_scope(conn, CHART_ID, GEN)


def test_a_generation_with_no_manifest_and_an_unknown_scope_are_refused(moon_run):
    step, conn, has_1232 = moon_run
    assert sr.coverage_response(conn, chart_id=CHART_ID, generation="9.9", event_class="marriage",
                                windows=[])["completeness"] == "refused"
