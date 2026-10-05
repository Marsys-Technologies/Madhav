"""G12 route 1 — the search-input snapshot OWNS a COPY of the L1 rows it consumed (migration 1305; steward G12-ROUTE1; design note
decisions/G12_ROUTE1_SNAPSHOT_DESIGN_v1_0.md; Codex round 1 rulings in reviews/ASTRA_REVIEW_G12_SNAPSHOT_COPY_v1_0.md).

THE DEFECT THIS CLOSES: 1206's snapshot pointed at its L1 inputs by id and digested whole rows (row ids, build ids, parent ids included). After ANY later
`ga_dashas` / `ga_positions` rebuild (new `dasha_row_id`s, a new build id, an engine bump) a SEALED generation read every consumed row as MISSING or
changed: completeness reported `input_snapshot_drift` forever, the verification job could not re-derive, and a sealed generation cannot be repaired.

Real migration chain on a disposable database (1206, 1232, 1240, 1305); the L1 tables are the stubs of the A5.3 suites with the production columns.
Shown: the snapshot stores a copy PRODUCED BY THE DATABASE (a submitted copy is overwritten, a false digest is refused), proved the COMPLETE live
population at capture (a missing, extra or conflicting row refuses by name); an L1 rebuild with NEW row ids and a NEW build id and the SAME values is
METADATA-only drift (completeness clean, staleness soft, the verifier and the ledger re-derivation still pass, the Moon domain unchanged); a changed VALUE,
a missing row or an EXTRA conflicting row is HARD drift in both directions; a moved boundary is NAMED by its ORDINAL path (a repeated lord in another
cycle is not mistaken for it); numbers are compared exactly in PostgreSQL (and normalised inside jsonb); after the snapshot substep NO live L1 read
happens in the writer or kernel (instrumented and grepped); a first seal on a legacy snapshot is refused; 1305 refuses to apply after G8's 1306."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_verifier as inv_v
from services.gochara_kernel import staleness
from services.gochara_kernel.inventory_store import InventoryStore
from services.gochara_kernel.rule_registry import RuleRegistryStore

from . import test_a53_inventory as base
from .test_a53_am5_writer import make_ephe
from .test_a53_inventory import CHART_ID, H0, H1, create_am5_database, drop_am5_database

GEN = writer_mod.GENERATION
M1305 = base.MIGRATIONS / "1305_gochara_snapshot_owns_l1_copy.sql"


@pytest.fixture(params=[True], ids=["with_1305"])
def g12(request, monkeypatch, tmp_path):
    import psycopg
    admin, name, dsn = create_am5_database("g12", apply_1305=True)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
        RuleRegistryStore(conn).seed()
        # the AD stub row 2 is the Moon's Antardaśā in this chart (as in the AM-14 suite), so the Moon-resolved domain is non-empty
        conn.execute("UPDATE public.chart_dashas SET lord_graha = 'Moon' WHERE dasha_row_id = %s", (str(uuid.UUID(int=2)),))
        ephe = make_ephe(tmp_path, monkeypatch)
        w = writer_mod.GocharaV5Writer()

        def step(key):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-g12", db_conn=conn,
                              config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe}, dry_run=False)
            with conn.transaction():
                return w.run_substep(ctx, SubStep(key=key, label=key))
        for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, "inventory:marriage", "coverage:marriage"):
            step(k)
        yield step, conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


def _snapshot(conn):
    cur = conn.execute("SELECT consumed_fact_ids, consumed_dasha_row_ids, l1_facts_digest, dasha_digest, input_digest, consumed_fact_rows::text,"
                       " consumed_dasha_rows::text, l1_facts_metadata_digest, dasha_metadata_digest"
                       " FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    row = cur.fetchone()
    keys = ("fact_ids", "dasha_ids", "l1", "dd", "input", "facts", "dashas", "l1m", "ddm")
    d = dict(zip(keys, row))
    d["facts"], d["dashas"] = json.loads(d["facts"], parse_float=Decimal), json.loads(d["dashas"], parse_float=Decimal)
    return d


def _digest(conn, column, block):
    """The digest the DATABASE computes over a stored copy (the column), never over a Python re-serialisation (a Decimal would become a string)."""
    return conn.execute(f"SELECT public.ka_gochara_search_copy_digest({column}, %s) FROM public.ka_gochara_search_input_snapshot"
                        " WHERE chart_id = %s AND generation = %s", (block, CHART_ID, GEN)).fetchone()[0]


def _violations(conn):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        return conn.execute("SELECT event_class, violation, detail FROM public.ka_gochara_search_completeness_violations(%s::uuid, %s)",
                            (CHART_ID, GEN)).fetchall()


def _drift_violations(conn):
    return [v for v in _violations(conn) if v[1] == "input_snapshot_drift"]


def _rebuild_l1_with_new_ids(conn):
    """What a ga_dashas / ga_positions rebuild does to the rows: every dasha_row_id and parent_row_id re-issued, a NEW build id, a NEW engine version
    and a different created time — the VALUES are identical."""
    new_build = str(uuid.uuid4())
    conn.execute("CREATE TEMP TABLE _idmap AS SELECT dasha_row_id AS old_id, gen_random_uuid() AS new_id FROM public.chart_dashas")
    with conn.transaction():
        conn.execute("ALTER TABLE public.chart_dashas DISABLE TRIGGER ALL")
        conn.execute("UPDATE public.chart_dashas d SET parent_row_id = m.new_id FROM _idmap m WHERE d.parent_row_id = m.old_id")
        conn.execute("UPDATE public.chart_dashas d SET dasha_row_id = m.new_id, build_id = %s, engine_version = 'ga_dashas@v2', computed_at = now() + interval '1 day'"
                     " FROM _idmap m WHERE d.dasha_row_id = m.old_id", (new_build,))
        conn.execute("ALTER TABLE public.chart_dashas ENABLE TRIGGER ALL")
    conn.execute("UPDATE public.chart_facts SET build_id = %s, engine_version = 'ga_positions@v2', created_at = now() + interval '1 day'", (new_build,))
    return new_build


# ── the copy ────────────────────────────────────────────────────────────────────────────────────────

def test_the_snapshot_stores_a_copy_and_its_digests_recompute_from_it(g12):
    _step, conn = g12
    s = _snapshot(conn)
    assert len(s["facts"]) == len(s["fact_ids"]) == 10 and len(s["dashas"]) == len(s["dasha_ids"]) and len(s["dashas"]) > 0
    assert s["l1"] == _digest(conn, "consumed_fact_rows", "content") and s["dd"] == _digest(conn, "consumed_dasha_rows", "content")
    assert s["l1m"] == _digest(conn, "consumed_fact_rows", "metadata") and s["ddm"] == _digest(conn, "consumed_dasha_rows", "metadata")
    assert len({s["l1"], s["l1m"]}) == 2, "the identity and the metadata digests differ (different blocks)"
    one = s["dashas"][0]
    assert set(one) == {"key", "content", "metadata"} and "dasha_row_id" in one["metadata"] and "dasha_row_id" not in json.dumps(one["content"])
    assert set(one["key"]) == {"ayanamsha_id", "system_id", "level_n", "start_iso", "kp_sublevel"}
    assert one["content"]["lord_path"], "the ordinal lord path is stored"
    fact = s["facts"][0]
    assert "build_id" in fact["metadata"] and "build_id" not in fact["content"]
    # no interval of the inventory carries a regenerated row id any more: a natural pointer instead
    detail = conn.execute("SELECT detail::text FROM public.ka_gochara_search_interval WHERE detail IS NOT NULL LIMIT 1").fetchone()[0]
    assert "dasha_row_id" not in detail


def _reinsert(conn, s, *, facts=None, dashas=None, l1=None, fact_ids=None, dasha_ids=None, with_copy=True):
    """Delete the snapshot (the candidate replacement path) and insert it again as the BUILDER does: the keys and the identity digests, and — only when asked —
    a SUBMITTED copy (which the database must ignore). 1206's own guard then recomputes input_digest from the digests as given."""
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                       (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    cols = ("chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids, consumed_dasha_row_ids, av_declarations, l1_facts_digest,"
            " dasha_digest, input_digest")
    vals = [CHART_ID, GEN, conv, vec, fact_ids if fact_ids is not None else s["fact_ids"], dasha_ids if dasha_ids is not None else s["dasha_ids"], [],
            l1 or s["l1"], s["dd"], s["input"]]
    marks = "%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s"
    if with_copy:
        cols += ", consumed_fact_rows, consumed_dasha_rows, l1_facts_metadata_digest, dasha_metadata_digest"
        marks += ",%s::jsonb,%s::jsonb,%s,%s"
        vals += [json.dumps(facts if facts is not None else s["facts"], default=_jsonable), json.dumps(dashas if dashas is not None else s["dashas"], default=_jsonable),
                 "f" * 64, "f" * 64]
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute(f"INSERT INTO public.ka_gochara_search_input_snapshot ({cols}) VALUES ({marks})", vals)


def _jsonable(o):
    if isinstance(o, Decimal):
        return float(o)                      # a JSON number again (a Decimal must not become a string)
    raise TypeError(type(o))


def test_the_copy_is_produced_by_the_database_a_submitted_false_copy_is_overwritten(g12):
    """Codex round 1, ruling 2: matching digests prove consistency, not authenticity. The builder holds INSERT, so it submits only KEYS; whatever copy (and
    metadata digests) it submits is OVERWRITTEN by the copy the database builds from the live rows in the insert transaction."""
    _step, conn = g12
    s = _snapshot(conn)
    lie = json.loads(json.dumps(s["facts"], default=_jsonable))
    lie[0]["content"]["fact_value_num"] = 999.0
    lie[0]["metadata"]["verification_pass_status"] = "two_pass_verified"                  # a false tier, with every hash 'consistent' (f*64 is ignored too)
    lie_d = json.loads(json.dumps(s["dashas"], default=_jsonable))
    lie_d[0]["content"]["lord_graha"] = "moon"
    _reinsert(conn, s, facts=lie, dashas=lie_d)
    after = _snapshot(conn)
    assert after["facts"] == s["facts"] and after["dashas"] == s["dashas"], "the stored copy is the database's, not the submitted one"
    assert after["l1m"] == s["l1m"] and after["ddm"] == s["ddm"] and after["input"] == s["input"]


def test_a_false_identity_digest_is_refused(g12):
    _step, conn = g12
    s = _snapshot(conn)
    with pytest.raises(Exception, match=r"not the identity digests of the live rows the submitted keys name"):
        _reinsert(conn, s, l1="0" * 64, with_copy=False)


def test_an_incomplete_capture_is_refused_by_name_a_period_left_out_and_a_fact_left_out(g12):
    """Codex round 1, ruling 1: a snapshot that names FEWER rows than the live population (an overlapping period omitted) is refused at capture."""
    _step, conn = g12
    s = _snapshot(conn)
    # the builder submits keys of a subset of the daśā rows but the digest of exactly that subset (so the digest check passes): the population check refuses
    keep = s["dasha_ids"][:-1]
    sub = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[]), 'content')",
                       (CHART_ID, keep)).fetchone()[0]
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    inp = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])", (conv, vec, s["l1"], sub, [])).fetchone()[0]
    with pytest.raises(Exception, match=r"consumed daśā rows are not the COMPLETE live population"):
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                         " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                         (CHART_ID, GEN, conv, vec, s["fact_ids"], keep, [], s["l1"], sub, inp))


def _submit_all_eligible_ids(conn, s, *, fact_ids=None, dasha_ids=None):
    """What a builder does that wants the snapshot ACCEPTED: submit EVERY eligible id now in L1 (both duplicates included) with the digests of exactly that set, so the
    copy and the required population agree (the only thing that can refuse it is the CONTRACT on L1 itself)."""
    fids = fact_ids if fact_ids is not None else [r[0] for r in conn.execute(
        "SELECT fact_id FROM public.chart_facts WHERE chart_id = %s AND ayanamsha_id = 'lahiri_chitrapaksha' AND fact_category = 'graha_position'"
        " AND fact_key = 'longitude_sidereal' AND fact_value_num IS NOT NULL ORDER BY fact_id", (CHART_ID,)).fetchall()]
    dids = dasha_ids if dasha_ids is not None else [str(r[0]) for r in conn.execute(
        "SELECT dasha_row_id FROM public.chart_dashas WHERE chart_id = %s AND system_id = 'vimshottari' AND level_n IN (1,2,3)"
        " AND verification_pass_status = 'two_pass_verified' ORDER BY dasha_row_id", (CHART_ID,)).fetchall()]
    l1 = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_copy(%s::uuid, %s::text[]), 'content')", (CHART_ID, fids)).fetchone()[0]
    dd = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[]), 'content')", (CHART_ID, dids)).fetchone()[0]
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    inp = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])", (conv, vec, l1, dd, [])).fetchone()[0]
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                     " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                     (CHART_ID, GEN, conv, vec, fids, dids, [], l1, dd, inp))


def test_both_duplicate_natural_key_rows_submitted_together_are_refused_by_the_contract_not_accepted_as_a_consistent_population(g12):
    """Codex round 3, P1-2: two SUN facts / two eligible AD rows of different builds share a natural key. The builder submits BOTH ids with the digest of both, so the copy
    equals the 'required population'; only a uniqueness predicate on L1 itself refuses it."""
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso,"
                 " gen_random_uuid(), verification_pass_status FROM public.chart_dashas WHERE level_n = 2 LIMIT 1")
    with pytest.raises(Exception, match=r"required_period_duplicate"):
        _submit_all_eligible_ids(conn, s)
    conn.execute("DELETE FROM public.chart_dashas WHERE build_id NOT IN (SELECT build_id FROM public.chart_dashas WHERE level_n = 1)")
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-SUN-dup', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'longitude_sidereal', 12.0)", (CHART_ID,))
    with pytest.raises(Exception, match=r"required_fact_duplicate"):
        _submit_all_eligible_ids(conn, s)


def test_a_conflicting_extra_period_or_fact_present_at_capture_refuses_the_snapshot_when_the_old_ids_are_resubmitted(g12):
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, parent_row_id, 'Ketu', start_iso, end_iso,"
                 " gen_random_uuid(), verification_pass_status FROM public.chart_dashas WHERE level_n = 2 LIMIT 1")
    with pytest.raises(Exception, match=r"required_period_duplicate|required_period_overlap"):
        _reinsert(conn, s, with_copy=False)


def test_an_l1_that_lacks_a_required_level_a_subject_or_the_horizon_edges_is_refused_at_capture_by_name(g12):
    """Codex round 3, P1-1: the required-population functions only filtered existing rows, so an L1 WITHOUT AD rows (or without SUN, or with a period missing at a horizon
    edge) was accepted when the builder submitted what was there. The contract now asserts required MEMBERS and COVERAGE."""
    step, conn = g12
    conn.execute("CREATE TABLE _dasha_bak AS SELECT * FROM public.chart_dashas")
    conn.execute("CREATE TABLE _facts_bak AS SELECT * FROM public.chart_facts")

    def restore():
        conn.execute("DELETE FROM public.chart_dashas")
        conn.execute("INSERT INTO public.chart_dashas SELECT * FROM _dasha_bak")
        conn.execute("DELETE FROM public.chart_facts")
        conn.execute("INSERT INTO public.chart_facts SELECT * FROM _facts_bak")

    cases = [
        ("DELETE FROM public.chart_dashas WHERE level_n = 2", r"required_level_missing \(level 2"),
        ("DELETE FROM public.chart_dashas WHERE system_id = 'vimshottari'", r"required_level_missing \(level 1"),
        ("DELETE FROM public.chart_facts WHERE fact_subject = 'SUN'", r"required_fact_missing \(subject SUN"),
        # a missing period at the horizon START edge (level 3: the period covering the horizon start is removed)
        ("DELETE FROM public.chart_dashas WHERE level_n = 3 AND start_iso = (SELECT min(start_iso) FROM public.chart_dashas WHERE level_n = 3)", r"required_horizon_start_uncovered|required_period_gap"),
        # a missing period at the horizon END edge
        ("DELETE FROM public.chart_dashas WHERE level_n = 3 AND end_iso = (SELECT max(end_iso) FROM public.chart_dashas WHERE level_n = 3)", r"required_horizon_end_uncovered"),
    ]
    for sql, pattern in cases:
        conn.execute(sql)
        with pytest.raises(Exception, match=pattern):
            _submit_all_eligible_ids(conn, None)                         # the DATABASE contract, whatever the builder (or the writer's own read) would do
        restore()
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    step(writer_mod.SNAPSHOT_SUBSTEP)                                    # the restored L1 is accepted again
    assert not _drift_violations(conn)


def test_a_gap_inside_a_level_is_refused_at_capture(g12):
    _step, conn = g12
    conn.execute("DELETE FROM public.chart_dashas WHERE level_n = 3 AND lord_graha = 'Rahu'")             # the middle PD: a gap inside level 3
    with pytest.raises(Exception, match=r"required_period_gap"):
        _submit_all_eligible_ids(conn, None)


def test_a_drifted_l1_reports_a_lost_required_member_by_name_beside_the_hard_drift(g12):
    _step, conn = g12
    conn.execute("DELETE FROM public.chart_facts WHERE fact_subject = 'SUN'")                           # an upstream rebuild lost the SUN fact after the capture
    found = [v for v in _violations(conn) if v[1] == "input_snapshot_required_scope" and "required_fact_missing" in v[2]]
    assert found, _violations(conn)
    assert _drift_violations(conn), "and the identity digest of the live population no longer matches"


def test_a_second_build_of_another_tier_present_at_capture_refuses_the_snapshot_by_name(g12):
    """The trigger compares rows of the consumed TIER only; a chart whose Vimśottarī rows of ANY tier come from more than one build (a mixed L1 state) is refused
    at capture by the daśā read, by name, before a copy is taken."""
    step, conn = g12
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso,"
                 " gen_random_uuid(), 'single' FROM public.chart_dashas WHERE level_n = 1 LIMIT 1")
    with pytest.raises(Exception, match=r"dasha_builds_mixed"):
        step(writer_mod.SNAPSHOT_SUBSTEP)


def test_a_snapshot_whose_keys_name_a_missing_row_is_refused_by_name(g12):
    _step, conn = g12
    s = _snapshot(conn)
    with pytest.raises(Exception, match=r"do not exist for chart"):
        _reinsert(conn, s, fact_ids=s["fact_ids"] + ["fact-NOT-THERE"], with_copy=False)


def test_a_snapshot_without_keys_is_refused(g12):
    _step, conn = g12
    s = _snapshot(conn)
    with pytest.raises(Exception, match=r"KEYS the database builds the copy from|null value"):
        _reinsert(conn, s, fact_ids=None, with_copy=False) if False else _reinsert_nulls(conn, s)


def _reinsert_nulls(conn, s):
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, av_declarations, l1_facts_digest,"
                     " dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s)", (CHART_ID, GEN, conv, vec, [], s["l1"], s["dd"], s["input"]))


# ── an L1 rebuild with NEW ids and a NEW build id: METADATA-only drift, the generation stays verifiable ────────────────────────────────

def _verify_marriage(conn):
    """The independent re-derivation the verification job runs (the inventory digest from the snapshot's natal COPY, then the ledger digest from the
    snapshot's daśā COPY), compared with the stored header — exactly the writer's verify phase, minus the geometry."""
    inv = InventoryStore(conn)
    sealed = inv.sealed_rule_paths()
    stored_sel = inv_v.stored_selection(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")
    res = inv_v.rederive_inventory_digest(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", sealed_paths=sealed,
                                          path_exclusions=writer_mod.VERIFIER_PATH_RULINGS, h_unknown_exclusion=writer_mod.VERIFIER_H_UNKNOWN_RULING,
                                          selected_versions=stored_sel or None)
    led = inv_v.rederive_ledger_digest(conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", obligations=res["obligations"],
                                       capability={"position_probe": True, "arc_index": True, "aspect_span_solver": True,
                                                   "moon_scope_domain": inv.moon_scope_available()})
    hdr = conn.execute("SELECT inventory_digest, ledger_digest FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s"
                       " AND event_class = 'marriage'", (CHART_ID, GEN)).fetchone()
    return res["digest"] == hdr[0] and led == hdr[1]


def test_rebuilding_L1_with_new_row_ids_and_a_new_build_id_is_metadata_only_drift_and_the_generation_still_verifies(g12):
    _step, conn = g12
    inv = InventoryStore(conn)
    before_rows = inv.consumed_dasha_rows(CHART_ID, GEN)
    assert _verify_marriage(conn) and not _drift_violations(conn)
    fresh = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert fresh["self_contained"] and not fresh["drifted"] and not fresh["metadata_drift_components"] and fresh["changes"] == []

    _rebuild_l1_with_new_ids(conn)
    # the old ids no longer exist anywhere in L1
    old_ids = _snapshot(conn)["dasha_ids"]
    assert conn.execute("SELECT count(*) FROM public.chart_dashas WHERE dasha_row_id = ANY(%s::uuid[])", (old_ids,)).fetchone()[0] == 0

    assert _drift_violations(conn) == [], "completeness must not report drift for an id / build / engine re-issue"
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["drifted_components"] == [], rep["components"]
    assert rep["metadata_only_drift"] is True and set(rep["metadata_drift_components"]) == {"l1_metadata", "dasha_metadata"}
    assert rep["components"]["l1_facts"]["same"] and rep["components"]["dasha"]["same"] and rep["components"]["input"]["same"]
    assert {c["change"] for c in rep["changes"]} == {"metadata_only"}
    # the generation is still VERIFIABLE from its own copy: the daśā rows, the natal chart, the population contract, the ledger digest
    assert inv.consumed_dasha_rows(CHART_ID, GEN) == before_rows
    assert _verify_marriage(conn)
    assert inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN)["source"] == "snapshot_copy"
    assert inv_v.read_chart_snapshot(conn, CHART_ID, GEN)["lagna"] == base.CHART["lagna_deg"]


def test_the_moon_resolved_domain_is_unchanged_by_an_L1_rebuild_it_reads_the_snapshots_copy(g12):
    _step, conn = g12
    ob = conn.execute("SELECT ob_id FROM public.ka_gochara_search_obligation WHERE chart_id = %s AND generation = %s AND agent ~ '^period_lord:'"
                      " LIMIT 1", (CHART_ID, GEN)).fetchone()[0]
    q = "SELECT public.ka_gochara_search_moon_resolved_domain(%s::uuid, %s, 'marriage', %s::uuid)::text"
    # make the Moon the lord of one stored period BEFORE the snapshot is taken is not possible here (it is built); compare before / after instead
    ob = conn.execute("SELECT ob_id FROM public.ka_gochara_search_obligation WHERE chart_id = %s AND generation = %s AND agent = 'period_lord:ad' LIMIT 1",
                      (CHART_ID, GEN)).fetchone()[0]
    before = conn.execute(q, (CHART_ID, GEN, ob)).fetchone()[0]
    assert before != "{}", "setup: the Moon Antardaśā puts a non-empty Moon-resolved domain under the AD obligation"
    _rebuild_l1_with_new_ids(conn)
    assert conn.execute(q, (CHART_ID, GEN, ob)).fetchone()[0] == before
    conn.execute("DELETE FROM public.chart_dashas")                                          # even with live L1 EMPTY the function answers from the copy
    assert conn.execute(q, (CHART_ID, GEN, ob)).fetchone()[0] == before


def test_the_generation_verifies_even_when_live_L1_is_gone_entirely(g12):
    _step, conn = g12
    conn.execute("DELETE FROM public.chart_dashas")
    conn.execute("DELETE FROM public.chart_facts")
    assert _verify_marriage(conn)                                                            # the copy is all the verifier needs
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is True and {"l1_facts", "dasha", "input"} <= set(rep["drifted_components"])       # ... and drift is REPORTED as hard, honestly
    assert {c["change"] for c in rep["changes"]} == {"missing_live"}


# ── a changed VALUE is HARD drift; a moved boundary is NAMED ────────────────────────────────────────────────────────────────────────

def test_a_changed_dasha_end_is_hard_drift_in_completeness_and_staleness(g12):
    _step, conn = g12
    conn.execute("UPDATE public.chart_dashas SET end_iso = end_iso + interval '1 hour' WHERE dasha_row_id ="
                 " (SELECT dasha_row_id FROM public.chart_dashas ORDER BY level_n DESC, start_iso LIMIT 1)")
    drift = _drift_violations(conn)
    assert len(drift) == 1 and "dasha rows no longer match" in drift[0][2] and "a value changed" in drift[0][2]
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] and rep["drifted_components"] == ["dasha", "input"]
    (change,) = [c for c in rep["changes"] if c["change"] != "metadata_only"]
    assert change["change"] == "content_differs" and change["fields"] == ["end_iso"]


def test_a_changed_natal_longitude_is_hard_drift(g12):
    _step, conn = g12
    conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num + 0.5 WHERE fact_subject = 'SUN'")
    drift = _drift_violations(conn)
    assert len(drift) == 1 and "fact rows no longer match" in drift[0][2]
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] and "l1_facts" in rep["drifted_components"]
    assert any(c["kind"] == "fact" and c["change"] == "content_differs" and c["fields"] == ["fact_value_num"] for c in rep["changes"])


def test_a_trailing_scale_difference_in_a_numeric_is_not_a_value_change(g12):
    """A rebuild that stores the same number with a different trailing scale (12.5 vs 12.50) must not read as a changed value (the digest trims scale)."""
    _step, conn = g12
    conn.execute("ALTER TABLE public.chart_facts ALTER COLUMN fact_value_num TYPE numeric(30,12) USING fact_value_num::numeric(30,12)")
    # the snapshot was taken on the double stub; recompute the live view under a wider scale: the SAME numbers
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["components"]["l1_facts"]["same"], rep["changes"]


def test_a_moved_boundary_is_named_by_its_ordinal_lord_path_not_reported_as_a_missing_row(g12):
    _step, conn = g12
    row = conn.execute("SELECT dasha_row_id, start_iso FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso LIMIT 1").fetchone()
    conn.execute("UPDATE public.chart_dashas SET start_iso = start_iso + interval '6992 seconds' WHERE dasha_row_id = %s", (row[0],))
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] and "dasha" in rep["drifted_components"]
    moved = [c for c in rep["changes"] if c["change"] == "moved"]
    assert len(moved) == 1 and moved[0]["start_shift_seconds"] == 6992.0 and moved[0]["lord_path"]


# ── the migration itself ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_numbers_are_compared_exactly_in_postgresql_a_difference_a_float_cannot_carry_is_hard_drift(g12):
    """Codex round 1, finding 4: 12.5 and 12.5000000000000000001 are the SAME float64. The digest is computed in PostgreSQL over the exact numeric, so
    the difference is a value change; the same number with a different trailing scale (12.5 vs 12.50) is not."""
    _step, conn = g12
    conn.execute("ALTER TABLE public.chart_facts ALTER COLUMN fact_value_num TYPE numeric(38,22) USING fact_value_num::numeric(38,22)")
    assert staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["components"]["l1_facts"]["same"]
    conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num + 0.0000000000000000001 WHERE fact_subject = 'SUN'")
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert not rep["components"]["l1_facts"]["same"] and "l1_facts" in rep["drifted_components"]


def test_numbers_inside_nested_jsonb_are_normalised_in_the_database(g12):
    _step, conn = g12
    out = conn.execute("SELECT public.ka_gochara_search_normalize_numbers('{\"a\": [1.50, {\"b\": 2.000}], \"c\": 12.5000, \"d\": \"1.50\", \"e\": null}'::jsonb)::text").fetchone()[0]
    assert json.loads(out) == {"a": [1.5, {"b": 2}], "c": 12.5, "d": "1.50", "e": None} and "1.50," not in out and '"b": 2}' in out


def test_after_the_snapshot_substep_no_substep_reads_live_L1(g12):
    """Codex round 1, ruling 3: ONE capture. With live L1 gone entirely, the inventory and coverage substeps still run and write the same rows."""
    step, conn = g12
    q = "SELECT count(*), md5(string_agg(ob_id::text || search_range::text || state, '|' ORDER BY ob_id::text, search_range::text)) FROM public.ka_gochara_search_interval"
    before = conn.execute(q).fetchone()
    conn.execute("DROP TABLE public.chart_dashas CASCADE")
    conn.execute("DROP TABLE public.chart_facts CASCADE")
    step("inventory:marriage")
    step("coverage:marriage")
    after = conn.execute(q).fetchone()
    assert after == before and after[0] > 0, "the same intervals, from the copy alone"


def test_only_the_capture_the_independent_verifier_and_the_legacy_branches_read_live_L1():
    """The grep half of ruling 3: every SQL reference to the live L1 tables in the writer and kernel sits in a file that is the capture, the verifier's own
    independent derivation, the legacy (no copy) branch, or the seal brief's report. A new reader anywhere else fails here until it is named."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[3]
    allowed = {"chart_context.py", "dasha_read.py", "inventory_store.py", "inventory_verifier.py", "record_verifier.py", "seal_brief.py", "verification_job.py",
               "staleness.py", "record_store.py"}
    files = list((root / "services" / "gochara_kernel").glob("*.py")) + [root / "pipeline" / "orchestrator" / "writers" / "ka_gochara_v5.py"]
    pat = re.compile(r"\b(FROM|JOIN)\s+(public\.)?(chart_facts|chart_dashas)\b")        # SQL is upper-case in this code; prose comments are not
    offenders = sorted(f.name for f in files if f.name not in allowed and pat.search(f.read_text()))
    assert offenders == [], f"live L1 read outside the named capture/verifier/legacy files: {offenders}"
    # and the writer itself never reads them
    writer_src = (root / "pipeline" / "orchestrator" / "writers" / "ka_gochara_v5.py").read_text()
    assert not pat.search(writer_src)
    # Codex round 2, P2-6: a SQL-text grep cannot see a live read hidden in a helper. The writer's LIVE helpers are called exactly once each, inside the snapshot
    # substep (the capture); a new call anywhere else (a later substep re-reading live L1) fails here, and the instrumented drop-the-tables test above runs the
    # computational substeps.
    import ast
    tree = ast.parse(writer_src)
    live_helpers = {"fetch_chart_context", "load_pinned_vimshottari", "make_period_rows_for", "read_chart"}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in live_helpers]
    snap = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == "step.key == SNAPSHOT_SUBSTEP")
    inside = {id(c) for c in ast.walk(snap) if isinstance(c, ast.Call)}
    outside = [(getattr(c.func, "id", getattr(c.func, "attr", "")), c.lineno) for c in calls if id(c) not in inside]
    assert not outside, f"live-L1 helpers called outside the snapshot substep: {outside}"
    assert len(calls) == 2, [(getattr(c.func, "id", getattr(c.func, "attr", "")), c.lineno) for c in calls]


def test_a_first_seal_on_a_legacy_snapshot_is_refused_and_a_replay_of_a_sealed_generation_is_not(monkeypatch, tmp_path):
    import psycopg
    from services.gochara_kernel import seal_brief
    admin, name, dsn = create_am5_database("g12legacyseal")                       # 1206 only: a legacy snapshot
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
        RuleRegistryStore(conn).seed()
        ephe = make_ephe(tmp_path, monkeypatch)
        w = writer_mod.GocharaV5Writer()
        for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-legacyseal", db_conn=conn,
                              config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe}, dry_run=False)
            with conn.transaction():
                w.run_substep(ctx, SubStep(key=k, label=k))
        with pytest.raises(seal_brief.BriefRefused) as e:
            seal_brief._build_payload(conn, CHART_ID, GEN)
        assert e.value.args[0] == "snapshot_without_copy" or "snapshot_without_copy" in repr(e.value)
    finally:
        conn.close()
        drop_am5_database(admin, name)


# ── round 2 (Codex): the REQUIRED population is a contract in the database; natural-key facts; tier-only drift is soft; honest moves; first seal; exact numbers ───────

def test_a_whole_level_omitted_from_the_copy_is_refused_at_insert_the_required_scope_is_not_derived_from_the_submitted_ids(g12):
    """Codex round 2, P1: omit EVERY AD row (keep the MD and PD rows, with their correct digest). The old trigger derived (system, level) from the copy, so no level-2
    selector remained and nothing was compared. The required scope is a database contract (Vimśottarī MD, AD, PD over the bound horizon)."""
    _step, conn = g12
    s = _snapshot(conn)
    assert {e["key"]["level_n"] for e in s["dashas"]} == {1, 2, 3}, "the stub world carries all three levels"
    keep = [e["metadata"]["dasha_row_id"] for e in s["dashas"] if e["key"]["level_n"] != 2]
    sub = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[]), 'content')", (CHART_ID, keep)).fetchone()[0]
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    inp = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])", (conv, vec, s["l1"], sub, [])).fetchone()[0]
    with pytest.raises(Exception, match=r"consumed daśā rows are not the COMPLETE live population"):
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                         " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                         (CHART_ID, GEN, conv, vec, s["fact_ids"], keep, [], s["l1"], sub, inp))


def test_periods_of_different_levels_that_start_together_are_distinct_keys_and_a_pristine_snapshot_shows_no_drift(g12):
    """MD, AD and PD routinely START at the same instant (the first AD of an MD begins with it). The natural key is (ayanamsha, system, LEVEL, start, kp): a live view
    that matched by start alone would return the sibling of another level too and a pristine generation would read as drifted."""
    step, conn = g12
    conn.execute("UPDATE public.chart_dashas SET start_iso = (SELECT start_iso FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso LIMIT 1)"
                 " WHERE dasha_row_id = (SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 3 ORDER BY start_iso LIMIT 1)")
    shared = conn.execute("SELECT count(*) FROM (SELECT start_iso FROM public.chart_dashas GROUP BY 1 HAVING count(DISTINCT level_n) > 1) x").fetchone()[0]
    assert shared >= 1, "the arranged world has two levels starting at one instant"
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    step(writer_mod.SNAPSHOT_SUBSTEP)                                   # a fresh capture over the arranged L1
    assert not _drift_violations(conn)
    assert staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["drifted"] is False


def test_a_leftover_of_another_tier_at_the_start_of_a_consumed_row_of_a_different_level_is_not_drift(g12):
    """A non-consumed, non-eligible row (tier 'single') of ANOTHER level that happens to start where a consumed row starts is neither consumed nor in the required scope:
    the key match includes the level, so it must not enter the live view."""
    _step, conn = g12
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 2, NULL, 'Ketu', start_iso, end_iso, build_id, 'single'"
                 " FROM public.chart_dashas WHERE level_n = 1 LIMIT 1")
    assert not _drift_violations(conn)
    assert staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["drifted"] is False


def test_a_whole_natal_subject_omitted_from_the_copy_is_refused_at_insert(g12):
    _step, conn = g12
    s = _snapshot(conn)
    keep = [e["metadata"]["fact_id"] for e in s["facts"] if e["key"]["fact_subject"] != "SUN"]
    sub = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_copy(%s::uuid, %s::text[]), 'content')", (CHART_ID, keep)).fetchone()[0]
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    inp = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])", (conv, vec, sub, s["dd"], [])).fetchone()[0]
    with pytest.raises(Exception, match=r"consumed fact rows are not the COMPLETE live population"):
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                         " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                         (CHART_ID, GEN, conv, vec, keep, s["dasha_ids"], [], sub, s["dd"], inp))


def test_the_required_scope_in_the_database_equals_the_python_read_contract():
    """The SQL literals and the Python read contract are one contract: a change to either without the other fails here."""
    from services.gochara_kernel import seal_brief
    text = M1305.read_text()
    assert f"f.ayanamsha_id = '{inv_v._C_AYANAMSHA}'" in text and f"d.ayanamsha_id = '{inv_v._C_AYANAMSHA}'" in text
    assert f"d.system_id = '{inv_v._C_SYSTEM}'" in text and f"d.verification_pass_status = '{inv_v._C_TIER}'" in text
    assert f"d.level_n IN ({', '.join(str(x) for x in inv_v._C_LEVELS)})" in text
    assert "f.fact_subject IN (" + ", ".join(f"'{x}'" for x in seal_brief.NATAL_SUBJECTS) + ")" in text
    assert "f.fact_category = 'graha_position' AND f.fact_key = 'longitude_sidereal'" in text


def test_re_issued_fact_ids_with_the_same_values_are_metadata_only_drift_facts_are_keyed_by_natural_key(g12):
    """A deterministic-row-id ga_positions rebuild re-issues every fact_id: the identity (natural key + content) is unchanged, so this is soft, and the report names it
    as a metadata change, never as a missing row plus an extra row."""
    _step, conn = g12
    conn.execute("UPDATE public.chart_facts SET fact_id = 'reissued-' || fact_id, build_id = gen_random_uuid()")
    assert not _drift_violations(conn)
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["metadata_only_drift"] is True and "l1_metadata" in rep["metadata_drift_components"]
    assert {c["change"] for c in rep["changes"] if c["kind"] == "fact"} == {"metadata_only"}
    assert all("fact_id" in c["fields"] for c in rep["changes"] if c["kind"] == "fact")


def test_an_added_conflicting_fact_is_reported_not_a_crash(g12):
    """Codex round 2, P2-3: the formatter used to read start_iso of every new key, including facts (KeyError)."""
    _step, conn = g12
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-SUN-dup', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'longitude_sidereal', 12.0)", (CHART_ID,))
    assert _drift_violations(conn)
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] and "l1_facts" in rep["drifted_components"]
    kinds = {(c["kind"], c["change"]) for c in rep["changes"]}
    assert ("fact", "extra_live") in kinds, kinds


def test_a_tier_only_change_of_a_consumed_dasha_row_is_soft_not_hard_drift(g12):
    """Codex round 2, P2-4: the live view used to be selected by the copied TIER, so a relabelled row vanished from it and the content digest changed."""
    _step, conn = g12
    conn.execute("UPDATE public.chart_dashas SET verification_pass_status = 'single' WHERE level_n = 2")
    assert not _drift_violations(conn), "a tier relabel is metadata, the completeness gate must stay quiet"
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["metadata_only_drift"] is True and "dasha_metadata" in rep["metadata_drift_components"]
    assert all(c["change"] == "metadata_only" and "verification_pass_status" in c["fields"] for c in rep["changes"] if c["kind"] == "dasha")


def test_deleting_an_earlier_sibling_is_a_missing_row_and_a_changed_ordinal_never_a_move(g12):
    """Codex round 2, P2-5: two stored sibling periods A (ordinal 1) and B (ordinal 2); delete A: B becomes ordinal 1. The report must not say A 'moved' to B's start."""
    _step, conn = g12
    ads = conn.execute("SELECT dasha_row_id, parent_row_id, start_iso FROM public.chart_dashas WHERE level_n = 2 ORDER BY parent_row_id, start_iso").fetchall()
    first = ads[0]
    sibs = [r for r in ads if r[1] == first[1]]
    assert len(sibs) >= 2, "the stub world carries at least two ADs under one MD"
    conn.execute("ALTER TABLE public.chart_dashas DISABLE TRIGGER ALL")
    conn.execute("DELETE FROM public.chart_dashas WHERE dasha_row_id = %s OR parent_row_id = %s", (first[0], first[0]))
    conn.execute("ALTER TABLE public.chart_dashas ENABLE TRIGGER ALL")
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"]
    assert not [c for c in rep["changes"] if c["change"] == "moved"], rep["changes"]
    missing = [c for c in rep["changes"] if c["kind"] == "dasha" and c["change"] == "missing_live"]
    assert any(c["key"]["level_n"] == 2 for c in missing)
    assert any(c["change"] == "content_differs" and "ordinal_path" in c["fields"] for c in rep["changes"] if c["kind"] == "dasha")


def test_a_deletion_together_with_a_boundary_change_is_missing_and_extra_never_a_move(g12):
    """Codex round 3, P2-3: stored AD A (venus, ordinal 1) and B (sun, ordinal 2) under one MD. Delete A and shift B's start by a day: B becomes ordinal 1 and is unmatched by
    natural key. The report used to say 'A moved to B's start' (same ordinal, level, system) — a different lord is a different period."""
    _step, conn = g12
    ads = conn.execute("SELECT dasha_row_id, lord_graha, start_iso FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso").fetchall()
    assert len(ads) >= 2 and ads[0][1].lower() != ads[1][1].lower()
    conn.execute("ALTER TABLE public.chart_dashas DISABLE TRIGGER ALL")
    conn.execute("DELETE FROM public.chart_dashas WHERE dasha_row_id = %s OR parent_row_id = %s", (ads[0][0], ads[0][0]))
    conn.execute("UPDATE public.chart_dashas SET start_iso = start_iso + interval '1 day' WHERE dasha_row_id = %s", (ads[1][0],))
    conn.execute("ALTER TABLE public.chart_dashas ENABLE TRIGGER ALL")
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"]
    assert not [c for c in rep["changes"] if c["change"] == "moved"], rep["changes"]
    kinds = {(c["kind"], c["change"]) for c in rep["changes"]}
    assert ("dasha", "missing_live") in kinds and ("dasha", "extra_live") in kinds, kinds


def test_a_boundary_that_really_moved_is_still_named_a_move_when_the_lord_and_ordinal_agree(g12):
    _step, conn = g12
    row = conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso LIMIT 1").fetchone()
    conn.execute("UPDATE public.chart_dashas SET start_iso = start_iso + interval '6992 seconds' WHERE dasha_row_id = %s", (row[0],))
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    moved = [c for c in rep["changes"] if c["change"] == "moved"]
    assert len(moved) == 1 and moved[0]["start_shift_seconds"] == 6992


def test_every_runnable_substep_after_the_snapshot_runs_with_live_L1_gone_not_only_inventory_and_coverage(g12):
    """Codex round 2, P2-6: the single-capture guard must exercise the COMPUTATIONAL substeps, not a hand-picked pair. Every substep the writer plans for the marriage
    class after the snapshot that this stub world can run (inventory, coverage, the four record phases, the P1 and P2 window geometry; the P3/P4 window geometry and
    the generation verify need a real sky — the control run without the drop fails there too, on member geometry) is run with chart_facts and chart_dashas DROPPED:
    any read of live L1 anywhere in the writer or kernel call graph fails with 'relation does not exist'. The verifier half is test_the_generation_verifies_even_when_
    live_L1_is_gone_entirely."""
    step, conn = g12
    w = writer_mod.GocharaV5Writer()
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-g12-plan", db_conn=conn, config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": None}, dry_run=False)
    planned = [x.key for x in w.plan_substeps(ctx)]
    after = planned[planned.index(writer_mod.SNAPSHOT_SUBSTEP) + 1:]
    runnable = [k for k in after if ":marriage" in k and k not in ("window:marriage:P3", "window:marriage:P4", "verify:marriage")]
    assert runnable == ["inventory:marriage", "coverage:marriage", "record:marriage:P1", "record:marriage:P2", "record:marriage:P3", "record:marriage:P4",
                        "window:marriage:P1", "window:marriage:P2"], runnable
    conn.execute("DROP TABLE public.chart_dashas CASCADE")
    conn.execute("DROP TABLE public.chart_facts CASCADE")
    for key in runnable:
        step(key)


def test_a_decimal_that_a_float_cannot_carry_is_refused_exactly_not_context_rounded():
    """Codex round 2, P2-8: `exact.normalize()` rounds to the decimal context's 28 digits, so 12.50000000000000000000000000001 compared equal to 12.5."""
    from decimal import Decimal
    from services.gochara_kernel import targets
    tiny = Decimal("12.50000000000000000000000000001")
    with pytest.raises(ValueError, match="not exactly representable"):
        targets.assert_float64_exact(tiny)
    with pytest.raises(inv_v.Unverifiable, match="not exactly representable"):
        inv_v._exact_float(tiny, "SUN")
    assert targets.assert_float64_exact(Decimal("12.50")) == 12.5 and inv_v._exact_float(Decimal("12.50"), "SUN") == 12.5


def test_a_first_seal_on_a_legacy_snapshot_is_refused_by_the_database_gate_and_replay_is_untouched(g12):
    """Codex round 2, P2-2: the SQL first-seal branch (which calls the completeness function) must itself refuse a legacy-shaped snapshot; the REPLAY branch
    (ka_gochara_search_replay_violations) is a different function and is untouched."""
    _step, conn = g12
    assert not [v for v in _violations(conn) if v[1] == "input_snapshot_without_copy"], "a snapshot WITH a copy is not refused"
    conn.execute("ALTER TABLE public.ka_gochara_search_input_snapshot DROP CONSTRAINT kgsis_l1_copy_ck")
    conn.execute("ALTER TABLE public.ka_gochara_search_input_snapshot DISABLE TRIGGER USER")
    conn.execute("UPDATE public.ka_gochara_search_input_snapshot SET consumed_fact_rows = NULL, consumed_dasha_rows = NULL, l1_facts_metadata_digest = NULL,"
                 " dasha_metadata_digest = NULL WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    violations = _violations(conn)
    assert [v for v in violations if v[1] == "input_snapshot_without_copy"], violations
    replay = conn.execute("SELECT violation FROM public.ka_gochara_search_replay_violations(%s, %s)", (CHART_ID, GEN)).fetchall()
    assert not [r for r in replay if "without_copy" in r[0]], "replay never asks for the copy"
    # the REAL first-seal attempt (publish, then the sealing function whose BEFORE INSERT trigger runs the completeness function): refused, and the refusal names the
    # missing copy among the violations of this partial stub world
    from services.gochara_kernel import ledger as gk_ledger
    with pytest.raises(Exception, match=r"input_snapshot_without_copy"):
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            gk_ledger.publish(conn, CHART_ID, GEN)
            conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))


def test_the_python_population_checker_asserts_the_required_members_and_coverage_for_a_copy_bearing_snapshot():
    """Codex round 3, P1-1: the pure checker returned [] for an MD-only, an empty-system and a horizon-gap population. With the contract on (a snapshot that has a copy)
    each is a named violation; a legacy snapshot (contract off) keeps its 1206-era behaviour."""
    from datetime import datetime, timezone
    def row(i, level, a, b, lord="saturn"):
        return {"dasha_row_id": f"id{i}", "level_n": level, "parent_row_id": None, "lord_graha": lord, "start_iso": datetime(*a, tzinfo=timezone.utc),
                "end_iso": datetime(*b, tzinfo=timezone.utc), "build_id": "b", "system_id": inv_v._C_SYSTEM, "ayanamsha_id": inv_v._C_AYANAMSHA,
                "verification_pass_status": inv_v._C_TIER}
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 3, 1, tzinfo=timezone.utc)
    full = [row(1, 1, (2024, 6, 1), (2026, 6, 1)), row(2, 2, (2024, 12, 1), (2025, 4, 1)), row(3, 3, (2024, 12, 20), (2025, 3, 20))]
    def check(rows, contract=True):
        return inv_v.check_dasha_population(rows, rows, chart_id="c", horizon=(lo, hi), consumed_ids=[r["dasha_row_id"] for r in rows], pin_build=False, require_contract=contract)
    assert check(full) == []
    assert any("required level 2" in v for v in check([full[0], full[2]])), "an MD+PD-only population"
    assert any("required level" in v for v in check([])), "an empty population"
    assert any("gap" in v for v in check([full[0], row(2, 2, (2024, 12, 1), (2025, 1, 20)), row(5, 2, (2025, 2, 1), (2025, 4, 1)), full[2]])), "a gap inside a level"
    assert any("after the horizon start" in v for v in check([full[0], row(2, 2, (2025, 1, 10), (2025, 4, 1)), full[2]])), "a missing period at the start edge"
    assert any("before the horizon end" in v for v in check([full[0], row(2, 2, (2024, 12, 1), (2025, 2, 10)), full[2]])), "a missing period at the end edge"
    assert any("overlaps" in v for v in check(full + [row(6, 2, (2025, 2, 1), (2025, 5, 1))])), "an overlap"
    assert check([full[0]], contract=False) == [], "the legacy path keeps its behaviour"


def test_the_mutation_harness_distinguishes_a_caught_mutation_from_collection_setup_and_infrastructure_failures():
    """Codex round 3, item 5: the harness counted every non-zero pytest exit as CAUGHT, so a collection failure or an unavailable database made a surviving mutation look
    detected. Only an assertion failure of a test that ran is evidence of detection."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("mutation_check_1305", base.MIGRATIONS.parent / "scripts" / "gochara" / "mutation_check_1305.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    classify = mod.classify
    assert classify(0, "40 passed in 3s") == "SURVIVED"
    assert classify(1, "FAILED tests/x.py::test_a - AssertionError\n1 failed, 39 passed") == "CAUGHT"
    assert classify(1, "ERROR tests/x.py::test_a - psycopg.OperationalError\n1 error") == "SETUP-ERROR"
    assert classify(2, "ERROR collecting tests/x.py\n!!! Interrupted: 1 error during collection") == "COLLECTION-FAILURE"
    assert classify(5, "no tests ran in 0.01s") == "COLLECTION-FAILURE"
    assert classify(4, "usage: pytest ...") == "INFRASTRUCTURE(exit 4)"


def test_1305_refuses_to_apply_after_g8s_1306_would_have_replaced_the_completeness_function():
    """Both migrations replace ka_gochara_search_completeness_violations in full: applying 1305 AFTER 1306 would silently revert G8's census."""
    import psycopg
    admin, name, dsn = create_am5_database("g12gate", faithful=True)            # 1206 + 1232 + 1240, no 1305
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        fn = conn.execute("SELECT pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure)").fetchone()[0]
        conn.execute(fn.replace("BEGIN", "BEGIN\n  -- expected_class_list_missing (stand-in for G8's 1306 block)", 1))
        with pytest.raises(Exception, match="g8_1306_applied_first"):
            with conn.transaction():
                conn.execute(M1305.read_text())
    finally:
        conn.close()
        drop_am5_database(admin, name)


def test_1305_refuses_a_second_application_and_a_schema_without_1232():
    import psycopg
    admin, name, dsn = create_am5_database("g12twice", apply_1305=True)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        with pytest.raises(Exception, match="migration_1305_already_applied"):
            with conn.transaction():
                conn.execute(M1305.read_text())
    finally:
        conn.close()
        drop_am5_database(admin, name)
    admin, name, dsn = create_am5_database("g12no1232")                          # 1206 only: no Moon-domain function
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        with pytest.raises(Exception, match="migration_1232_not_applied"):
            with conn.transaction():
                conn.execute(M1305.read_text())
    finally:
        conn.close()
        drop_am5_database(admin, name)


def test_the_replaced_completeness_function_is_the_1232_body_with_exactly_one_block_changed():
    """A static proof, in the 1232 tradition: take 1232's function, substitute the 1305 drift block, compare with 1305's function."""
    import re
    m1232 = (base.MIGRATIONS / "1232_gochara_search_moon_scope_domain.sql").read_text()
    m1305 = M1305.read_text()

    def fn(text):
        a = text.index("CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations(p_chart uuid, p_generation text)")
        return text[a:text.index("$$;", text.index("RETURN QUERY SELECT * FROM public.ka_gochara_search_moon_scope_violations", a)) + 3]
    f1232, f1305 = fn(m1232), fn(m1305)
    a, b = f1305.index("    IF snap.consumed_fact_rows IS NULL OR"), f1305.index("    FOREACH e IN ARRAY snap.av_declarations LOOP")
    legacy_then = f1305[a:b]
    old_block = f1232[f1232.index("    live_l1 := public.ka_gochara_search_l1_facts_digest"):f1232.index("    FOREACH e IN ARRAY snap.av_declarations LOOP")]
    assert f1232.replace(old_block, legacy_then) == f1305, "1305's completeness function differs from 1232's in more than the drift block"
    # and the legacy branch contains the 1232 block's statements unchanged (modulo indentation)
    norm = lambda t: re.sub(r"\s+", " ", t).strip()
    assert norm(old_block) in norm(legacy_then)


# ── the legacy path (no 1305) is unchanged ─────────────────────────────────────────────────────────────────────────────────────────

def test_without_1305_the_writer_builds_the_legacy_snapshot_and_the_note_says_so(monkeypatch, tmp_path):
    import psycopg
    admin, name, dsn = create_am5_database("g12legacy")                          # 1206 only
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
        RuleRegistryStore(conn).seed()
        ephe = make_ephe(tmp_path, monkeypatch)
        w = writer_mod.GocharaV5Writer()
        notes = {}
        for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-legacy", db_conn=conn,
                              config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe}, dry_run=False)
            with conn.transaction():
                notes[k] = w.run_substep(ctx, SubStep(key=k, label=k)).notes
        assert "LEGACY snapshot (migration 1305 is NOT applied)" in notes[writer_mod.SNAPSHOT_SUBSTEP]
        assert InventoryStore(conn).snapshot_copy_available() is False
        rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
        assert rep["self_contained"] is False and rep["drifted"] is False
        conn.execute("UPDATE public.chart_dashas SET end_iso = end_iso + interval '1 hour' WHERE level_n = 1")
        assert staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["drifted"] is True        # legacy: every component is hard
    finally:
        conn.close()
        drop_am5_database(admin, name)


def test_with_1305_the_snapshot_note_says_self_contained(g12):
    step, conn = g12
    assert InventoryStore(conn).snapshot_copy_available() is True
    assert "SELF-CONTAINED: the snapshot owns a COPY of the consumed L1 rows" in step(writer_mod.SNAPSHOT_SUBSTEP).notes


def test_the_gate_pins_are_the_shas_a_fresh_1206_1232_chain_produces_and_production_has():
    """The sha256 values 1305's gate pins (read read-only from production 2026-10-05) are what a fresh 1206+1232 chain gives, so the gate accepts the real
    schema and the migration applies on it (the `faithful` DB is exactly 1206+1232+1240 and 1305 applies cleanly on top in the other tests)."""
    import hashlib
    import psycopg
    admin, name, dsn = create_am5_database("g12sha", faithful=True)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        got = {fn.split("(")[0]: hashlib.sha256(conn.execute(f"SELECT pg_get_functiondef('public.{fn}'::regprocedure)").fetchone()[0].encode()).hexdigest()
               for fn in ("ka_gochara_search_completeness_violations(uuid,text)", "ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)")}
    finally:
        conn.close()
        drop_am5_database(admin, name)
    assert got == {"ka_gochara_search_completeness_violations": "63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb",
                   "ka_gochara_search_moon_resolved_domain": "707bd37ce48a3c5fbaf2de881bc7554d97bc81fc1a09a6534d36b4ec5f09cf07"}
    text = M1305.read_text()
    assert all(v in text for v in got.values())


def test_a_changed_1232_function_blocks_1305_by_name():
    import psycopg
    admin, name, dsn = create_am5_database("g12chg", faithful=True)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        fn = conn.execute("SELECT pg_get_functiondef('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)'::regprocedure)").fetchone()[0]
        conn.execute(fn.replace("SELECT COALESCE(", "SELECT COALESCE( /* edited by hand */ ", 1))
        with pytest.raises(Exception, match="moon_domain_function_is_not_the_1232_body"):
            with conn.transaction():
                conn.execute(M1305.read_text())
    finally:
        conn.close()
        drop_am5_database(admin, name)


# ── the production readback ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_readback_sql_runs_read_only_and_reports_what_the_post_apply_check_expects(g12):
    _step, conn = g12
    text = (base.MIGRATIONS.parent / "scripts" / "gochara" / "readback_1305_snapshot_copy.sql").read_text()
    code_only = "\n".join(x for x in text.splitlines() if not x.strip().startswith("--"))
    results = []
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        for statement in [x for x in code_only.split(";") if x.strip()]:
            sql = statement.strip()
            if sql.upper() in ("BEGIN READ ONLY", "COMMIT"):
                continue
            results.append(conn.execute(sql).fetchall())
    columns, check, trigger, functions, replaced, grants, shas, ledger = results
    assert [r[0] for r in columns] == ["consumed_dasha_rows", "consumed_fact_rows", "dasha_metadata_digest", "l1_facts_metadata_digest"]
    assert check == [("kgsis_l1_copy_ck", False)]                              # NOT VALID: governs new rows, scans no old one
    assert len(trigger) == 1 and trigger[0][1] == "O" and trigger[0][2] is True and trigger[0][3] is True
    assert len(functions) == 12 and all(r[2] is False for r in functions)
    assert replaced == [(True, True, True)]
    assert {r[0] for r in shas} == {"ka_gochara_search_completeness_violations", "ka_gochara_search_moon_resolved_domain"}
    assert all(r[1] not in ("63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb", "707bd37ce48a3c5fbaf2de881bc7554d97bc81fc1a09a6534d36b4ec5f09cf07")
               for r in shas), "the replaced functions are NOT the 1232 bodies any more"
    assert ledger == [(1, 1, 0)]                                               # recorded; one snapshot (this test's); none without a copy
