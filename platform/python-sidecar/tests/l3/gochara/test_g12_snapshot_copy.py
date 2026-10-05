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
import re
import uuid
from collections import Counter
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


def _is_a_forbidden_live_read(exc: BaseException) -> bool:
    """The ONE kind of failure `_answers_from_the_copy` turns into a failed assertion (round 6, R4), identified explicitly, never by 'it raised':
      * PostgreSQL's UndefinedTable naming a live L1 relation (the test DROPPED chart_facts / chart_dashas, so any statement or server-side function that reads
        them fails with exactly this), or
      * migration 1305's own copy builders refusing because a consumed id is no longer in live L1 (`... a snapshot is built from existing rows`): the code went
        back to live L1 for rows the snapshot already owns.
    Everything else (a lost connection, a permission error, a TypeError, a broken fixture) is NOT evidence of a live read."""
    import psycopg
    text = str(exc)
    if isinstance(exc, psycopg.errors.UndefinedTable):
        return re.search(r'relation "(public\.)?(chart_facts|chart_dashas)" does not exist', text) is not None
    if isinstance(exc, psycopg.errors.RaiseException):
        return "a snapshot is built from existing rows" in text
    return False


def _answers_from_the_copy(fn):
    """Run `fn` with live L1 gone. ONLY the explicitly identified forbidden-live-read failure (`_is_a_forbidden_live_read`) is reported as a FAILED ASSERTION
    (pytest.fail), so that detection is an assertion the mutation harness may count. EVERY other exception PROPAGATES unchanged: the harness then classifies it
    as infrastructure (UNEXPECTED-EXCEPTION), never as a caught mutation (rounds 4 and 5 converted every exception, which laundered a lost connection into a
    'catch')."""
    try:
        return fn()
    except Exception as exc:
        if _is_a_forbidden_live_read(exc):
            pytest.fail(f"the code read live L1 (it needed rows that are gone): {type(exc).__name__}: {str(exc)[:200]}")
        raise


def _contract_codes(conn, facts_text, dashas_text, *, eligibility=True):
    """The capture contract over ONE pair of copies, judged by BOTH implementations: the database's `ka_gochara_search_copy_violations` and the independent
    Python `copy_contract_violations`. They must agree code for code (a multiset: one violation per offending element); the agreed codes are returned."""
    sql = Counter(r[0] for r in conn.execute(
        "SELECT code FROM public.ka_gochara_search_copy_violations(%s::jsonb, %s::jsonb, tstzrange(%s, %s, '[)'), %s)",
        (facts_text, dashas_text, H0, H1, eligibility)).fetchall())
    py = Counter(c for c, _ in inv_v.copy_contract_violations(json.loads(facts_text, parse_float=Decimal), json.loads(dashas_text, parse_float=Decimal),
                                                             (H0, H1), eligibility=eligibility))
    assert sql == py, f"the database and the Python checker disagree: only SQL {dict(sql - py)}, only Python {dict(py - sql)}"
    return sql


def _scope_ids(conn):
    """Every row id of the upstream scope as the database states it (canonical ayanamsha, Vimśottarī, MD/AD/PD, overlapping the horizon; every tier and build)."""
    return [str(r[0]) for r in conn.execute(
        "SELECT dasha_row_id FROM public.chart_dashas WHERE chart_id = %s AND ayanamsha_id = 'lahiri_chitrapaksha' AND system_id = 'vimshottari'"
        " AND level_n IN (1, 2, 3) AND start_iso < %s AND end_iso > %s ORDER BY dasha_row_id", (CHART_ID, H1, H0)).fetchall()]


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
    assert one["content"]["lord_path"], "the lord path is stored (identity: it is a function of the row and of its consumed ancestors)"
    # round 6, R3: the IDENTITY block holds only values of rows the snapshot consumed; the ordinal path counts siblings it never read, so it is metadata
    assert set(one["content"]) == {"lord_graha", "end_iso", "parent_level_n", "parent_start_iso", "lord_path"}
    assert set(one["metadata"]) == {"dasha_row_id", "build_id", "parent_row_id", "verification_pass_status", "engine_version", "ordinal_path"}
    assert set(s["facts"][0]["content"]) == {"fact_value_text", "fact_value_num", "fact_value_jsonb", "unit"}
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
    import psycopg
    try:
        _reinsert(conn, s, facts=lie, dashas=lie_d)
    except psycopg.errors.RaiseException as exc:
        if "ka_gochara_search_input_snapshot refused (1305)" not in str(exc):
            raise
        # identified, not laundered: 1305's own capture refusal here can only mean the database JUDGED the submitted copy instead of replacing it with its own
        pytest.fail(f"the database kept the SUBMITTED copy (and then refused it) instead of building its own: {str(exc)[:200]}")
    after = _snapshot(conn)
    assert after["facts"] == s["facts"] and after["dashas"] == s["dashas"], "the stored copy is the database's, not the submitted one"
    assert after["l1m"] == s["l1m"] and after["ddm"] == s["ddm"] and after["input"] == s["input"]


def test_a_false_identity_digest_is_refused(g12):
    _step, conn = g12
    s = _snapshot(conn)
    with pytest.raises(Exception, match=r"not the identity digests of the copy the database built from the submitted keys"):
        _reinsert(conn, s, l1="0" * 64, with_copy=False)


def test_an_incomplete_capture_is_refused_and_the_refusal_names_the_key_of_the_period_left_out(g12):
    """Codex round 1, ruling 1 + round 6, R8: a snapshot that names FEWER rows than the upstream scope (one Antardaśā left out, with the correct digest of the
    subset) is refused at capture, and the refusal NAMES the natural key, the row id, the tier and the build of the row the copy lacks. (A whole fact left out:
    test_a_whole_natal_subject_omitted_from_the_copy_is_refused_at_insert.)"""
    _step, conn = g12
    s = _snapshot(conn)
    gone = str(uuid.UUID(int=3))                                        # the Sun Antardaśā starting 2025-02-01
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, s, dasha_ids=[x for x in map(str, s["dasha_ids"]) if x != gone])
    msg = str(e.value)
    assert "period_upstream_row_not_in_copy" in msg and '"level_n":2' in msg and '"start_iso":"2025-02-01T00:00:00+00:00"' in msg, msg
    assert f"{gone} tier two_pass_verified build {base.PINNED_BUILD}" in msg and "the copy has 0 row(s), upstream has 1 row(s)" in msg, msg
    assert "required_horizon_end_uncovered (level 2" in msg and "required_parent_missing (level 3" in msg, msg     # and the copy BY ITSELF is refused too
    assert conn.execute("SELECT count(*) FROM public.ka_gochara_search_input_snapshot").fetchone()[0] == 0, "nothing was stored"


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
    # EVERY capture attempt of this suite is also a parity case: the copy the database would store is judged by the SQL contract and by the Python checker
    built = conn.execute("SELECT public.ka_gochara_search_facts_copy(%s::uuid, %s::text[])::text, public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[])::text",
                         (CHART_ID, fids, CHART_ID, dids)).fetchone()
    _contract_codes(conn, built[0], built[1])
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


def test_a_conflicting_extra_period_present_at_capture_refuses_the_snapshot_when_the_old_ids_are_resubmitted(g12):
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, parent_row_id, 'Ketu', start_iso, end_iso,"
                 " gen_random_uuid(), verification_pass_status FROM public.chart_dashas WHERE level_n = 2 LIMIT 1")
    with pytest.raises(Exception, match=r"period_row_count_differs \(.*the copy has 1 row\(s\).*upstream has 2 row\(s\)"):
        _reinsert(conn, s, with_copy=False)


def test_a_conflicting_extra_fact_present_at_capture_refuses_the_snapshot_when_the_old_ids_are_resubmitted(g12):
    """Round 6, R13 (the Codex inventory: 'no corresponding extra-fact capture case'): a second SUN row exists upstream; the builder resubmits the ten old ids. The
    copy by itself is a perfect ten-subject population, so only the comparison with the WHOLE upstream scope refuses it, by name."""
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-SUN-dup', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'longitude_sidereal', 12.0)", (CHART_ID,))
    with pytest.raises(Exception) as e:
        _reinsert(conn, s, with_copy=False)
    msg = str(e.value)
    assert "fact_row_count_differs" in msg and '"fact_subject":"SUN"' in msg and "fact-SUN-dup" in msg and "upstream has 2 row(s)" in msg, msg
    assert "required_fact_duplicate" not in msg, "the copy itself holds SUN once: it is the upstream comparison that refuses"


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


@pytest.mark.parametrize("sql,pattern", [
    ("UPDATE public.chart_dashas SET parent_row_id = NULL WHERE level_n = 3", r"required_parent_missing \(level 3"),                                        # an orphan PD
    ("UPDATE public.chart_dashas SET parent_row_id = NULL WHERE level_n = 2", r"required_parent_missing \(level 2"),                                        # an orphan AD (round 6, R13)
    ("UPDATE public.chart_dashas SET parent_row_id = dasha_row_id WHERE level_n = 2", r"required_parent_missing \(level 2"),                                # an AD that is its own parent
    ("UPDATE public.chart_dashas SET parent_row_id = (SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 1) WHERE level_n = 3", r"required_parent_missing"),  # a PD whose parent is an MD
    ("UPDATE public.chart_dashas SET end_iso = '2026-07-01' WHERE level_n = 2 AND lord_graha = 'Sun'", r"required_parent_not_containing"),                   # a child outside its parent
    ("UPDATE public.chart_dashas SET ayanamsha_id = 'lahiri_other' WHERE level_n = 1", r"required_level_missing|required_parent_missing"),                    # a parent of another ayanamsha
    ("UPDATE public.chart_dashas SET system_id = 'yogini' WHERE level_n = 1", r"required_level_missing|required_parent_missing"),                             # a parent of another system
])
def test_an_inconsistent_hierarchy_is_refused_at_capture_by_name_even_when_every_level_tiles_the_horizon(g12, sql, pattern):
    """Codex round 4, P1: every level validated INDEPENDENTLY accepted an orphan PD, a child outside its parent, a parent of another ayanamsha. The contract now includes the hierarchy."""
    _step, conn = g12
    conn.execute(sql)
    with pytest.raises(Exception, match=pattern):
        _submit_all_eligible_ids(conn, None)


@pytest.mark.parametrize("column,value", [("ayanamsha_id", "lahiri_other"), ("system_id", "yogini")])
def test_a_parent_of_another_ayanamsha_or_system_never_enters_the_copied_ancestry(g12, column, value):
    """Codex round 4, P1 (and round 5's inventory: 'checks ayanamsha only, despite the test name mentioning system'): the parent lookup of an element once checked
    only chart and row id, so a foreign-ayanamsha or foreign-system parent entered the copied ancestry (parent level/start, lord path, ordinal path)."""
    _step, conn = g12
    ad = conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso LIMIT 1").fetchone()[0]
    own = conn.execute("SELECT public.ka_gochara_search_dasha_element(%s::uuid, %s::uuid)", (CHART_ID, ad)).fetchone()[0]
    assert own["content"]["parent_level_n"] == 1 and own["content"]["lord_path"].count("/") == 1 and own["metadata"]["ordinal_path"].count(".") == 1
    conn.execute(f"UPDATE public.chart_dashas SET {column} = %s WHERE level_n = 1", (value,))
    foreign = conn.execute("SELECT public.ka_gochara_search_dasha_element(%s::uuid, %s::uuid)", (CHART_ID, ad)).fetchone()[0]
    assert foreign["content"]["parent_level_n"] is None and foreign["content"]["parent_start_iso"] is None, foreign
    assert "/" not in foreign["content"]["lord_path"] and "." not in foreign["metadata"]["ordinal_path"], foreign


@pytest.mark.parametrize("column,value", [("ayanamsha_id", "lahiri_other"), ("system_id", "yogini"), ("chart_id", "00000000-0000-0000-0000-0000000000f2")])
def test_a_child_hanging_under_a_parent_of_another_ayanamsha_system_or_chart_is_refused_while_every_level_stays_complete(g12, column, value):
    """Round 6, R13 (Codex: the round-5 cases changed the ONLY Mahādaśā to another scope, so the pre-existing missing-level check fired and nothing proved the parent
    rule). Here the in-scope Mahādaśā STAYS; a twin of it in another ayanamsha, system or CHART is added, and both Antardaśās are pointed at the twin. Every level
    still tiles the horizon; only the hierarchy refuses, and it must say `required_parent_missing`."""
    _step, conn = g12
    if column == "chart_id":
        conn.execute("INSERT INTO public.charts(id) VALUES (%s)", (value,))
    twin = conn.execute(
        f"INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
        f" verification_pass_status) SELECT gen_random_uuid(), {'%s::uuid' if column == 'chart_id' else 'chart_id'}, {'%s' if column == 'ayanamsha_id' else 'ayanamsha_id'},"
        f" {'%s' if column == 'system_id' else 'system_id'}, 1, NULL, lord_graha, start_iso, end_iso, build_id, verification_pass_status"
        " FROM public.chart_dashas WHERE level_n = 1 RETURNING dasha_row_id", (value,)).fetchone()[0]
    conn.execute("UPDATE public.chart_dashas SET parent_row_id = %s WHERE level_n = 2 AND chart_id = %s", (twin, CHART_ID))
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, None, dasha_ids=_scope_ids(conn))
    msg = str(e.value)
    assert msg.count("required_parent_missing (level 2") == 2 and "required_level_missing" not in msg and "period_out_of_scope" not in msg, msg


def test_rows_of_another_chart_cannot_be_submitted_as_this_charts_inputs(g12):
    """Foreign-chart rows: the copy is built chart-scoped, so ids of ANOTHER chart's facts and daśā rows are refused by name ('do not exist for chart')."""
    _step, conn = g12
    other = "00000000-0000-0000-0000-0000000000f1"
    conn.execute("INSERT INTO public.charts(id) VALUES (%s)", (other,))
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-OTHER-SUN', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'longitude_sidereal', 12.0)", (other,))
    s = _snapshot(conn)
    with pytest.raises(Exception, match=r"do not exist for chart"):
        _submit_all_eligible_ids(conn, s, fact_ids=s["fact_ids"][:-1] + ["fact-OTHER-SUN"])
    foreign_dasha = conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                                 " verification_pass_status) SELECT gen_random_uuid(), %s, ayanamsha_id, system_id, level_n, NULL, lord_graha, start_iso, end_iso, build_id,"
                                 " verification_pass_status FROM public.chart_dashas WHERE level_n = 1 RETURNING dasha_row_id", (other,)).fetchone()[0]
    with pytest.raises(Exception, match=r"do not exist for chart"):
        _submit_all_eligible_ids(conn, s, dasha_ids=[str(x) for x in s["dasha_ids"][:-1]] + [str(foreign_dasha)])


def test_an_ad_spanning_two_mds_is_refused_at_capture(g12):
    _step, conn = g12
    conn.execute("UPDATE public.chart_dashas SET end_iso = '2025-01-10' WHERE level_n = 1")
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 1, NULL, 'Mercury', '2025-01-10', '2026-06-01', build_id, verification_pass_status"
                 " FROM public.chart_dashas WHERE level_n = 1")
    with pytest.raises(Exception, match=r"required_parent_not_containing"):
        _submit_all_eligible_ids(conn, None)


def test_relabelling_every_ad_and_md_row_after_capture_leaves_the_gate_clean_and_staleness_soft(g12):
    """Codex round 4, P2-2: TIER IS METADATA. The required scope used to filter on the consumed tier at drift, so relabelling all AD rows closed the gate with
    `input_snapshot_required_scope / required_level_missing` while staleness said metadata-only. The test looks at EVERY violation, not only `input_snapshot_drift`."""
    _step, conn = g12
    before = _violations(conn)                                    # the stub world has its own unrelated violations (vector, bridge, verification rows): compare, do not expect empty
    conn.execute("UPDATE public.chart_dashas SET verification_pass_status = 'single' WHERE level_n IN (1, 2)")
    after = _violations(conn)
    assert after == before, set(after) ^ set(before)
    assert not [v for v in after if v[1].startswith("input_snapshot")], after
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["metadata_only_drift"] is True


def test_ancestry_is_part_of_a_moves_identity_a_same_lord_same_ordinal_period_under_other_ancestors_is_missing_and_extra():
    """Codex round 4, P2-3 (the reviewer's scenario, on the pure formatter): stored Venus AD under a Venus MD (ordinal path 1.1) and a Venus AD under a Sun MD (2.9). The first
    MD tree and the earlier ADs under the Sun MD are deleted and the surviving Venus AD starts a day later: its ordinal path becomes 1.1 and its leaf lord is Venus again, but
    its ancestry is Sun/Venus, not Venus/Venus. It must not be reported as the deleted period 'moved'."""
    import json as _j
    def el(start, ordinal, lords, lord="venus"):
        return {"key": {"ayanamsha_id": "lahiri_chitrapaksha", "system_id": "vimshottari", "level_n": 2, "start_iso": start, "kp_sublevel": ""},
                "content": {"lord_graha": lord, "end_iso": "2030-01-01T00:00:00+00:00", "parent_level_n": 1, "parent_start_iso": "2000-01-01T00:00:00+00:00",
                            "lord_path": lords},
                "metadata": {"dasha_row_id": start, "verification_pass_status": "two_pass_verified", "ordinal_path": ordinal}}
    stored = [el("2000-01-01T00:00:00+00:00", "1.1", "venus/venus"), el("2020-01-01T00:00:00+00:00", "2.9", "sun/venus")]
    live = [el("2020-01-02T00:00:00+00:00", "1.1", "sun/venus")]                          # the survivor, shifted a day, now ordinal 1.1
    changes, total = staleness._changes("[]", _j.dumps(stored), "[]", _j.dumps(live))
    assert not [c for c in changes if c["change"] == "moved"], changes
    kinds = [(c["change"]) for c in changes]
    assert kinds.count("missing_live") == 2 and kinds.count("extra_live") == 1, kinds
    # and a genuine move (same full ancestry, same ordinal) is still a move
    live2 = [el("2000-01-02T00:00:00+00:00", "1.1", "venus/venus"), stored[1]]
    changes2, _ = staleness._changes("[]", _j.dumps(stored), "[]", _j.dumps(live2))
    assert [c["change"] for c in changes2 if c["change"] == "moved"] == ["moved"]


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
    with pytest.raises(Exception, match=r"consumed fact id\(s\) fact-NOT-THERE do not exist for chart"):
        _reinsert(conn, s, fact_ids=s["fact_ids"] + ["fact-NOT-THERE"], with_copy=False)
    with pytest.raises(Exception, match=r"1 consumed daśā row id\(s\) do not exist for chart"):                  # round 6, R13: the daśā half had no test
        _reinsert(conn, s, dasha_ids=[str(x) for x in s["dasha_ids"]] + [str(uuid.UUID(int=999999))], with_copy=False)


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
    assert _answers_from_the_copy(lambda: conn.execute(q, (CHART_ID, GEN, ob)).fetchone()[0]) == before
    conn.execute("DROP TABLE public.chart_dashas CASCADE")                                   # even with live L1 GONE the function answers from the copy
    assert _answers_from_the_copy(lambda: conn.execute(q, (CHART_ID, GEN, ob)).fetchone()[0]) == before


def test_the_generation_verifies_even_when_live_L1_is_gone_entirely(g12):
    _step, conn = g12
    conn.execute("DELETE FROM public.chart_dashas")
    conn.execute("DELETE FROM public.chart_facts")
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)                         # the drift REPORT reads live L1 by design, and says so honestly
    assert rep["drifted"] is True and {"l1_facts", "dasha", "input"} <= set(rep["drifted_components"])
    assert rep["self_contained"] is True and rep["copy_consistent"] is True, "the copy itself is intact: it is upstream that is gone"
    assert {c["change"] for c in rep["changes"]} == {"missing_live"}
    conn.execute("DROP TABLE public.chart_dashas CASCADE")                                   # now ANY live read, client- or server-side, is an identified failure
    conn.execute("DROP TABLE public.chart_facts CASCADE")
    assert _answers_from_the_copy(lambda: _verify_marriage(conn))                            # the copy is all the verifier needs
    assert _answers_from_the_copy(lambda: inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN))["source"] == "snapshot_copy"


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
    assert conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'chart_facts' AND column_name = 'fact_value_num'").fetchone()[0] == "numeric"
    conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num::numeric(30,12)")       # the SAME numbers, stored with twelve trailing digits
    assert conn.execute("SELECT fact_value_num::text FROM public.chart_facts WHERE fact_subject = 'SUN'").fetchone()[0].endswith("0000")
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["components"]["l1_facts"]["same"] and not rep["drifted"], rep["changes"]
    assert not _drift_violations(conn)


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
    # round 6, R11: the stub column is NUMERIC, as production (supabase/migrations/204_chart_facts.sql), so no ALTER stands between this test and the claim
    assert conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'chart_facts' AND column_name = 'fact_value_num'").fetchone()[0] == "numeric"
    assert staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["components"]["l1_facts"]["same"]
    conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num + 0.0000000000000000001 WHERE fact_subject = 'SUN'")
    assert float(conn.execute("SELECT fact_value_num FROM public.chart_facts WHERE fact_subject = 'SUN'").fetchone()[0]) == base.CHART["natal"]["Sun"], "the same float64"
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
    with pytest.raises(Exception, match=r"required_level_missing \(level 2 has no period overlapping the horizon\)") as e:
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                         " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                         (CHART_ID, GEN, conv, vec, s["fact_ids"], keep, [], s["l1"], sub, inp))
    assert str(e.value).count("period_upstream_row_not_in_copy") == 2, "and both Antardaśā rows the copy lacks are named"


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


def _masked(violations):
    """Violations with the NAMES of tiers masked (the detail names the tier of each row it mentions; a name decides nothing)."""
    return sorted((v[0], v[1], re.sub(r"tier \S+", "tier *", v[2])) for v in violations)


def test_an_extra_upstream_row_inside_the_required_scope_is_a_violation_whatever_its_tier_and_relabelling_it_changes_nothing(g12):
    """Round 6, R2 (Codex round 5, finding 2 — and the round-5 test at this place asserted the OPPOSITE). After a valid capture an overlapping, parentless
    Antardaśā appears at a NEW natural key with tier `single`. It is a row of the required scope (canonical ayanamsha, Vimśottarī, level 2, overlapping the horizon),
    so the gate reports it — as an extra row, as an overlap and as an orphan — at tier `single`. Relabelling ONLY that row to `two_pass_verified` then changes
    nothing: no branch of the scope, of extra-row detection or of drift reads the tier."""
    _step, conn = g12
    clean = _violations(conn)
    extra = conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                         " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 2, NULL, 'Ketu', start_iso, end_iso, build_id, 'single'"
                         " FROM public.chart_dashas WHERE level_n = 1 LIMIT 1 RETURNING dasha_row_id").fetchone()[0]
    as_single = _violations(conn)
    new = [v for v in as_single if v not in clean]
    assert {v[1] for v in new} == {"input_snapshot_drift", "input_snapshot_required_scope"}, new
    assert any("required_period_overlap" in v[2] for v in new) and any("required_parent_missing (level 2" in v[2] for v in new), new
    (drift,) = [v for v in new if v[1] == "input_snapshot_drift"]
    assert "upstream_row_not_in_copy" in drift[2] and str(extra) in drift[2] and "tier single" in drift[2], drift
    rep_single = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep_single["drifted"] is True and rep_single["drifted_components"] == ["dasha", "input"]
    conn.execute("UPDATE public.chart_dashas SET verification_pass_status = 'two_pass_verified' WHERE dasha_row_id = %s", (extra,))
    as_verified = _violations(conn)
    assert _masked(as_verified) == _masked(as_single), "the tier of an upstream row decides nothing after capture"
    rep_verified = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep_verified["drifted_components"] == rep_single["drifted_components"]
    assert rep_verified["components"]["dasha"]["live"] == rep_single["components"]["dasha"]["live"], "the identity digest of the upstream scope does not see the tier"


@pytest.mark.parametrize("tier", ["single", "two_pass_verified"])
def test_an_extra_upstream_row_inside_the_required_scope_refuses_the_capture_whatever_its_tier(g12, tier):
    """Round 6, R2 at CAPTURE: the same extra row present BEFORE the snapshot is taken. The builder submits the six rows it read; the upstream scope holds seven. The
    capture is refused by name at either tier (rounds 1-5 filtered the scope on the consumed tier, so a `single` row was invisible)."""
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 2, NULL, 'Ketu', start_iso, end_iso, build_id, %s"
                 " FROM public.chart_dashas WHERE level_n = 1 LIMIT 1", (tier,))
    with pytest.raises(Exception, match=rf"period_upstream_row_not_in_copy \(.*tier {tier} build"):
        _reinsert(conn, s, with_copy=False)


def test_no_function_that_runs_after_capture_reads_a_verification_tier_and_eligibility_is_one_guarded_place():
    """Round 6, R2 as a STATIC property of migration 1305 (the class, not the example): the word `verification_pass_status` occurs in executable SQL only where a
    row's tier is COPIED into a metadata block or NAMED in a message; the upstream scope functions, the drift function and the completeness function do not
    contain it at all; and inside the contract every use of the copied tier or build is guarded by `p_eligibility` (true only at capture and for the stored copy)."""
    text = M1305.read_text()

    def body(name):
        a = text.index(f"CREATE OR REPLACE FUNCTION public.{name}(")
        return "\n".join(ln.split("--")[0] for ln in text[a:text.index("\n$$;", a)].splitlines())
    for name in ("ka_gochara_search_facts_live_population", "ka_gochara_search_dasha_live_population", "ka_gochara_search_snapshot_copy_violations",
                 "ka_gochara_search_completeness_violations", "ka_gochara_search_moon_resolved_domain", "ka_gochara_search_copy_digest",
                 "ka_gochara_search_dasha_path", "ka_gochara_search_dasha_ordinal_path", "ka_gochara_search_dasha_copy"):
        assert "verification_pass_status" not in body(name) and "two_pass_verified" not in body(name), name
    contract = body("ka_gochara_search_copy_violations")
    assert contract.count("verification_pass_status") == 1 and "AS tier" in contract            # read ONCE, from the copy's metadata block
    arms = contract.split("UNION ALL")
    guarded = [arm for arm in arms if re.search(r"\ba\.(tier|build)\b", arm)]
    assert len(guarded) == 3 and all("WHERE p_eligibility AND" in arm for arm in guarded), guarded
    assert not re.search(r"\b(d|c|p|x)\.(tier|build)\b", contract), "no structural rule may reach a tier or a build"
    assert contract.count("'two_pass_verified'") == 1
    scope_calls = re.findall(r"ka_gochara_search_copy_violations\((.*?)\)", body("ka_gochara_search_snapshot_copy_violations"))
    assert scope_calls == ["snap.consumed_fact_rows, snap.consumed_dasha_rows, hz, true", "up_f, up_d, hz, false"], scope_calls


def test_a_whole_natal_subject_omitted_from_the_copy_is_refused_at_insert(g12):
    _step, conn = g12
    s = _snapshot(conn)
    keep = [e["metadata"]["fact_id"] for e in s["facts"] if e["key"]["fact_subject"] != "SUN"]
    sub = conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_copy(%s::uuid, %s::text[]), 'content')", (CHART_ID, keep)).fetchone()[0]
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    vec = conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    conv = conn.execute("SELECT convention_id FROM public.ka_gochara_sky_convention LIMIT 1").fetchone()[0]
    inp = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])", (conv, vec, sub, s["dd"], [])).fetchone()[0]
    with pytest.raises(Exception, match=r"fact_upstream_row_not_in_copy \(.*\"fact_subject\":\"SUN\".*fact-SUN.*required_fact_missing \(subject SUN\)"):
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            conn.execute("INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                         " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
                         (CHART_ID, GEN, conv, vec, keep, s["dasha_ids"], [], sub, s["dd"], inp))


def test_the_required_scope_in_the_database_equals_the_python_read_contract():
    """The SQL literals and the Python read contract are one contract: a change to either without the other fails here."""
    from services.gochara_kernel import seal_brief
    text = M1305.read_text()
    subjects = "(" + ", ".join(f"'{x}'" for x in seal_brief.NATAL_SUBJECTS) + ")"
    assert tuple(seal_brief.NATAL_SUBJECTS) == inv_v._C_FACT_SUBJECTS
    assert f"f.ayanamsha_id = '{inv_v._C_AYANAMSHA}'" in text and f"d.ayanamsha_id = '{inv_v._C_AYANAMSHA}'" in text       # the two upstream scopes
    assert f"d.system_id = '{inv_v._C_SYSTEM}'" in text and f"d.level_n IN ({', '.join(str(x) for x in inv_v._C_LEVELS)})" in text
    assert "f.fact_subject IN " + subjects in text and "f.fact_category = 'graha_position' AND f.fact_key = 'longitude_sidereal'" in text
    # the contract over a copy
    assert f"a.ay = '{inv_v._C_AYANAMSHA}' AND a.sy = '{inv_v._C_SYSTEM}' AND a.lv IN ({', '.join(str(x) for x in inv_v._C_LEVELS)})" in text
    assert f"a.tier IS DISTINCT FROM '{inv_v._C_TIER}'" in text
    assert f"x.el #>> '{{key,ayanamsha_id}}' = '{inv_v._C_AYANAMSHA}' AND x.el #>> '{{key,fact_category}}' = '{inv_v._C_FACT_CATEGORY}' AND x.el #>> '{{key,fact_key}}' = '{inv_v._C_FACT_KEY}'" in text
    assert "x.el #>> '{key,fact_subject}' IN " + subjects in text
    assert "levels(l) AS (VALUES " + ", ".join(f"({x})" for x in inv_v._C_LEVELS) + ")" in text


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
    # round 6, R3: the renumbered sibling kept every consumed value, so its changed ordinal is a METADATA difference, not a changed identity
    assert any(c["change"] == "metadata_only" and c["fields"] == ["ordinal_path"] for c in rep["changes"] if c["kind"] == "dasha"), rep["changes"]
    assert not [c for c in rep["changes"] if c["change"] == "content_differs"], rep["changes"]


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
        _answers_from_the_copy(lambda key=key: step(key))


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


def test_the_mutation_harness_classifies_from_the_structured_report_only_an_assertion_is_a_catch():
    """Codex rounds 3-4, item 5: only an ASSERTION failure of a test's call phase is evidence of detection. A database error, a PermissionError, a TypeError, a setup error, a
    collection failure or a missing report is NOT (`FAILED ... - psycopg.OperationalError: connection lost` used to read as CAUGHT)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("mutation_check_1305", base.MIGRATIONS.parent / "scripts" / "gochara" / "mutation_check_1305.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    classify = mod.classify

    def report(*cases):
        body = "".join(cases)
        return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{body}</testsuite></testsuites>'
    ok = '<testcase classname="t" name="test_ok"/>'
    fail = lambda msg: f'<testcase classname="t" name="test_f"><failure message="{msg}">trace</failure></testcase>'
    err = lambda msg: f'<testcase classname="t" name="test_e"><error message="{msg}">trace</error></testcase>'
    assert classify(0, "40 passed", report(ok)) == "SURVIVED"
    assert classify(1, "", report(ok, fail("assert 1 == 2"))) == "CAUGHT"
    assert classify(1, "", report(fail("AssertionError: the stored copy differs"))) == "CAUGHT"
    assert classify(1, "", report(fail("Failed: DID NOT RAISE &lt;class 'Exception'&gt;"))) == "CAUGHT"
    assert classify(1, "", report(fail("psycopg.OperationalError: connection lost"))) == "UNEXPECTED-EXCEPTION"
    assert classify(1, "", report(fail("PermissionError: denied"))) == "UNEXPECTED-EXCEPTION"
    assert classify(1, "", report(fail("TypeError: unsupported operand"))) == "UNEXPECTED-EXCEPTION"
    assert classify(1, "", report(err("failed on setup with &quot;psycopg.errors.RaiseException&quot;"))) == "SETUP-ERROR"
    assert classify(2, "", report(err("collection failure"))) == "COLLECTION-FAILURE"
    assert classify(5, "no tests ran", report()) == "COLLECTION-FAILURE"
    assert classify(1, "", None).startswith("INFRASTRUCTURE")
    assert classify(1, "", "<not xml").startswith("INFRASTRUCTURE")
    # an assertion in one test and an infrastructure error in another: the assertion IS evidence
    assert classify(1, "", report(fail("psycopg.OperationalError: x"), fail("assert False"))) == "CAUGHT"


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
    assert len(functions) == 13 and all(r[2] is False for r in functions), [r[0] for r in functions]
    assert replaced == [(True, True, True)]
    assert {r[0] for r in shas} == {"ka_gochara_search_completeness_violations", "ka_gochara_search_moon_resolved_domain"}
    assert all(r[1] not in ("63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb", "707bd37ce48a3c5fbaf2de881bc7554d97bc81fc1a09a6534d36b4ec5f09cf07")
               for r in shas), "the replaced functions are NOT the 1232 bodies any more"
    assert ledger == [(1, 1, 0)]                                               # recorded; one snapshot (this test's); none without a copy


# ══ ROUND 6 ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# The steward's rulings R1-R13 (run/G12_ROUND6_RULINGS.txt). Each test below is an ATTACK that was tried on the round-6 result and kept: an incomplete, duplicated,
# inconsistent or false snapshot that must be refused by name, or a legitimate one that must be accepted.

def _insert_twin(conn, of_row, *, build=None, tier=None):
    """A second row with the SAME natural key, interval, lord and parent as `of_row`, under another row id (and, when given, another build / tier)."""
    return str(conn.execute(
        "INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
        " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso,"
        " COALESCE(%s::uuid, build_id), COALESCE(%s, verification_pass_status) FROM public.chart_dashas WHERE dasha_row_id = %s RETURNING dasha_row_id",
        (build, tier, of_row)).fetchone()[0])


OTHER_BUILD = "0b0b0b0b-0000-4000-8000-00000000000b"


# ── R1: what is validated is exactly what is stored ────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("build,tier,also", [
    (OTHER_BUILD, "single", ("period_tier_ineligible", "dasha_builds_mixed")),          # the reviewer's counterexample (Codex round 5, finding 1)
    (OTHER_BUILD, None, ("dasha_builds_mixed",)),                                       # the same substitution at the consumed tier: only build and hierarchy refuse
    (None, None, ()),                                                                   # same build AND tier (the stub has no unique index): ONLY the hierarchy refuses
])
def test_substituting_an_identical_parent_row_is_refused_by_name_because_the_stored_copy_itself_is_judged(g12, build, tier, also):
    """Round 6, R1 (THE substitution test). Valid, verified rows M -> A -> P. M2 is an identical Mahādaśā (same natural key, interval, lord) under another row id.
    The builder submits [M2, A..., P...] with correctly recomputed digests. Rounds 1-5 validated the UPSTREAM population [M, A, P] and then compared CONTENT digests,
    which exclude row ids, parent ids, build and tier: the copy [M2, A, P] was stored although A hangs under M, which the copy does not hold. Now the copy that would
    be stored is what is judged: A's parent_row_id is not the row the copy holds at A's parent's natural key."""
    _step, conn = g12
    s = _snapshot(conn)
    m = str(uuid.UUID(int=1))
    m2 = _insert_twin(conn, m, build=build, tier=tier)
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, s, dasha_ids=[m2] + [x for x in map(str, s["dasha_ids"]) if x != m])
    msg = str(e.value)
    assert msg.count("required_parent_id_mismatch (level 2") == 2 and f"hangs under row {m}" in msg, msg
    assert all(code in msg for code in also), msg
    assert "period_row_count_differs" in msg and "the copy has 1 row(s)" in msg and "upstream has 2 row(s)" in msg, msg     # and upstream holds BOTH rows at that key
    assert conn.execute("SELECT count(*) FROM public.ka_gochara_search_input_snapshot").fetchone()[0] == 0, "nothing was stored"
    # the independent Python checker refuses the very same copy, for the same reason (parity is asserted inside _submit_all_eligible_ids; this is the name)
    built = conn.execute("SELECT public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[])::text",
                         (CHART_ID, [m2] + [x for x in map(str, s["dasha_ids"]) if x != m])).fetchone()[0]
    assert "required_parent_id_mismatch" in {c for c, _ in inv_v.dasha_copy_violations(json.loads(built), (H0, H1))}


def test_a_whole_identical_build_of_another_tier_submitted_directly_is_refused_by_name_the_copys_own_tier_is_asserted(g12):
    """Round 6, R1 (THE mixed-tier direct-insert test; Fable round 5, P2-2, which the database ACCEPTED). A complete second build B exists beside the verified
    build A: the same periods, its own row ids and its own internally consistent parent ids, tier `single`. The builder bypasses the writer and submits ONLY B's
    rows with their correct digests. The content of B equals the content of A, so every content-digest comparison passes; the copy's OWN recorded tier is what
    refuses it."""
    _step, conn = g12
    s = _snapshot(conn)
    conn.execute("CREATE TEMP TABLE _b AS SELECT dasha_row_id AS old_id, gen_random_uuid() AS new_id FROM public.chart_dashas")
    conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                 " verification_pass_status) SELECT m.new_id, d.chart_id, d.ayanamsha_id, d.system_id, d.level_n, pm.new_id, d.lord_graha, d.start_iso, d.end_iso, %s::uuid,"
                 " 'single' FROM public.chart_dashas d JOIN _b m ON m.old_id = d.dasha_row_id LEFT JOIN _b pm ON pm.old_id = d.parent_row_id", (OTHER_BUILD,))
    b_ids = [str(r[0]) for r in conn.execute("SELECT new_id FROM _b").fetchall()]
    # build B by itself is a structurally perfect population with the SAME identity digest as the verified build: only eligibility tells them apart
    assert conn.execute("SELECT public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[]), 'content')",
                        (CHART_ID, b_ids)).fetchone()[0] == s["dd"]
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, s, dasha_ids=b_ids)
    msg = str(e.value)
    assert msg.count("period_tier_ineligible") >= 6 and "carries tier single, not two_pass_verified" in msg, msg
    assert "required_parent" not in msg and "dasha_builds_mixed" not in msg, "the copy is one build with a closed hierarchy: its TIER is the refusal"
    assert conn.execute("SELECT count(*) FROM public.ka_gochara_search_input_snapshot").fetchone()[0] == 0


def test_a_copy_of_two_builds_is_refused_by_name_even_when_every_row_is_verified_and_the_hierarchy_closes(g12):
    """R1, the sibling of the two above (`one build` is asserted ON THE COPY): build B is a second VERIFIED build; the builder submits A's Mahādaśā and
    Antardaśās with B's Pratyantaras re-parented under A's Antardaśās, so the hierarchy closes and every row is `two_pass_verified`. Only the copy's own builds refuse."""
    _step, conn = g12
    s = _snapshot(conn)
    pds = [str(r[0]) for r in conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 3").fetchall()]
    twins = [_insert_twin(conn, x, build=OTHER_BUILD) for x in pds]
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, s, dasha_ids=[x for x in map(str, s["dasha_ids"]) if x not in pds] + twins)
    msg = str(e.value)
    assert "dasha_builds_mixed (the copy holds rows of 2 builds" in msg and "required_parent" not in msg and "period_tier_ineligible" not in msg, msg


def test_the_trigger_judges_NEW_the_value_it_stores_and_nothing_else():
    """R1 as a STATIC property (the class): in the capture trigger the contract, the upstream comparison and the digest check all take NEW.consumed_fact_rows /
    NEW.consumed_dasha_rows as their argument — the columns that are stored — and no local variable holds a second copy that could differ from them."""
    text = M1305.read_text()
    a = text.index("CREATE OR REPLACE FUNCTION public.ka_gochara_search_input_snapshot_copy_build()")
    body = "\n".join(ln.split("--")[0] for ln in text[a:text.index("\n$$;", a)].splitlines())
    assert "INTO NEW.consumed_fact_rows, NEW.consumed_dasha_rows, upstream_facts, upstream_dashas;" in body
    assert "ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, true)" in body
    assert "ka_gochara_search_copy_difference(NEW.consumed_fact_rows, upstream_facts)" in body
    assert "ka_gochara_search_copy_difference(NEW.consumed_dasha_rows, upstream_dashas)" in body
    assert body.count("NEW.consumed_fact_rows :=") == 0 and body.count("NEW.consumed_dasha_rows :=") == 0, "assigned once, by the one live read"
    declared = body[body.index("DECLARE"):body.index("BEGIN")]
    assert "facts jsonb" not in declared.replace("upstream_facts jsonb", "") and "dashas jsonb" not in declared.replace("upstream_dashas jsonb", "")
    assert body.index("ka_gochara_search_copy_violations(NEW.") < body.index("RETURN NEW;")


# ── R9: capture sees ONE upstream snapshot ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_capture_trigger_reads_live_L1_in_exactly_one_statement_and_everything_after_it_is_pure(g12):
    """Round 6, R9 (Fable P3-3). Under READ COMMITTED a VOLATILE trigger function takes a new snapshot per statement, so rounds 1-5 (scope check, copy build and
    population digests in separate statements) could judge one L1 state and store another. Now ONE statement performs every live read of the capture (its four
    STABLE function calls run on that statement's snapshot) and every later statement of the trigger is arithmetic on jsonb values. This is asserted on the
    function AS APPLIED in the database. (A two-session interleaving test is not practical here: there is no longer a second live-reading statement to slip between,
    and PostgreSQL offers no hook to pause inside one statement; the isolation assumption is stated in the migration: the per-chart lock, READ COMMITTED or stricter.)"""
    _step, conn = g12
    src = conn.execute("SELECT prosrc FROM pg_proc WHERE proname = 'ka_gochara_search_input_snapshot_copy_build'").fetchone()[0]
    statements = [st for st in "\n".join(ln.split("--")[0] for ln in src.splitlines()).split(";") if st.strip()]
    readers = ("ka_gochara_search_facts_copy", "ka_gochara_search_dasha_copy", "ka_gochara_search_facts_live_population", "ka_gochara_search_dasha_live_population")
    live = [st for st in statements if any(r in st for r in readers) or re.search(r"\b(chart_facts|chart_dashas)\b", st)]
    assert len(live) == 1 and all(r in live[0] for r in readers), live
    vol = dict(conn.execute("SELECT proname, provolatile FROM pg_proc WHERE proname = ANY(%s)", (list(readers),)).fetchall())
    assert set(vol.values()) == {"s"}, vol                                                       # STABLE: they run on the calling statement's snapshot
    # the functions every LATER statement calls read no table at all
    for pure in ("ka_gochara_search_copy_violations", "ka_gochara_search_copy_difference", "ka_gochara_search_copy_digest"):
        body = conn.execute("SELECT prosrc FROM pg_proc WHERE proname = %s", (pure,)).fetchone()[0]
        code = "\n".join(ln.split("--")[0] for ln in body.splitlines())
        assert not re.search(r"\b(FROM|JOIN)\s+public\.\w+\s*(?!\()", code.replace("public.ka_gochara_", "fn_")), pure
        assert "chart_facts" not in code and "chart_dashas" not in code and "ka_gochara_search_input_snapshot" not in code, pure


# ── R3: identity depends only on what was consumed ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_an_upstream_period_wholly_outside_the_horizon_added_after_capture_leaves_the_gate_clean_and_is_at_most_soft(g12):
    """Round 6, R3 (Fable round 5, P2-1, executed there: ONE Mahādaśā before the horizon flipped every consumed row to HARD drift, `content_differs:
    ['ordinal_path']`). Three periods the search never read are added after capture — an earlier Mahādaśā, an earlier Antardaśā under the consumed Mahādaśā and an
    earlier Pratyantara under a consumed Antardaśā, all ending before the horizon starts. They renumber the consumed rows' siblings and change NO consumed value: the
    gate is unchanged and the report is soft (the ordinal path is metadata)."""
    _step, conn = g12
    before = _violations(conn)
    md, ad = str(uuid.UUID(int=1)), str(uuid.UUID(int=2))
    for level, parent, lord, a, b in ((1, None, "Mercury", "2007-06-01", "2024-06-01"), (2, md, "Ketu", "2024-06-01", "2024-12-01"), (3, ad, "Ketu", "2024-12-01", "2024-12-20")):
        conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                     " verification_pass_status) VALUES (gen_random_uuid(), %s, 'lahiri_chitrapaksha', 'vimshottari', %s, %s, %s, %s, %s, %s, 'two_pass_verified')",
                     (CHART_ID, level, parent, lord, a, b, base.PINNED_BUILD))
    assert _violations(conn) == before, "the gate does not move for rows the snapshot never consumed"
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["drifted_components"] == [] and rep["components"]["dasha"]["same"] and rep["components"]["input"]["same"], rep["components"]
    assert rep["metadata_only_drift"] is True and rep["metadata_drift_components"] == ["dasha_metadata"]
    assert rep["changes"] and all(c["change"] == "metadata_only" and c["fields"] == ["ordinal_path"] for c in rep["changes"]), rep["changes"]
    # ... and the generation still verifies from its copy
    assert _verify_marriage(conn) and inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN)["source"] == "snapshot_copy"
    # CONTRAST: the same kind of row INSIDE the horizon is hard, so the test above is not passing because nothing is looked at
    conn.execute("UPDATE public.chart_dashas SET end_iso = '2025-01-05' WHERE level_n = 3 AND lord_graha = 'Ketu'")
    assert _drift_violations(conn) and staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["drifted"] is True


def test_movement_naming_reads_the_ordinal_path_from_metadata_and_the_identity_digest_does_not_contain_it(g12):
    """R3: ruling 5 of the earlier rounds (a moved boundary is named by its ordinal AND lord path) still holds, with the ordinal read from the metadata block."""
    _step, conn = g12
    s = _snapshot(conn)
    assert all("ordinal_path" in e["metadata"] and "ordinal_path" not in e["content"] for e in s["dashas"])
    stripped = json.dumps([{**e, "metadata": {k: v for k, v in e["metadata"].items() if k != "ordinal_path"}} for e in s["dashas"]])
    assert conn.execute("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, 'content')", (stripped,)).fetchone()[0] == s["dd"], "identity ignores the ordinal path"
    assert conn.execute("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, 'metadata')", (stripped,)).fetchone()[0] != s["ddm"], "the metadata digest carries it"
    row = conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE level_n = 2 ORDER BY start_iso LIMIT 1").fetchone()
    conn.execute("UPDATE public.chart_dashas SET start_iso = start_iso + interval '90 seconds' WHERE dasha_row_id = %s", (row[0],))
    (moved,) = [c for c in staleness.sealed_generation_staleness(conn, CHART_ID, GEN)["changes"] if c["change"] == "moved"]
    assert moved["ordinal_path"] == "1.1" and moved["lord_path"] == "saturn/moon" and moved["start_shift_seconds"] == 90.0, moved


# ── R7: the stored copy recomputes to its stored digests ────────────────────────────────────────────────────────────────────────────────────────────────────

def _tamper(conn, sql, params=()):
    """Change the stored snapshot row behind every guard (the insert-only triggers and the check): what a detector must still notice afterwards."""
    conn.execute("SET session_replication_role = replica")            # no user trigger and no foreign-key check fires (the inventory references input_digest)
    try:
        conn.execute(sql, params)
    finally:
        conn.execute("SET session_replication_role = origin")


def _inconsistent(conn):
    return [v[2] for v in _violations(conn) if v[1] == "input_snapshot_copy_inconsistent"]


def test_a_pristine_copy_is_consistent_and_self_contained(g12):
    _step, conn = g12
    assert _inconsistent(conn) == []
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["self_contained"] is True and rep["copy_consistent"] is True and rep["copy_inconsistencies"] == [] and rep["components"]["copy"]["same"] is True


@pytest.mark.parametrize("sql,expected", [
    # (i) a VALUE inside the stored copy is changed: the copy no longer recomputes to the stored identity digest
    ("UPDATE public.ka_gochara_search_input_snapshot SET consumed_fact_rows = jsonb_set(consumed_fact_rows, '{0,content,fact_value_num}', '999')",
     ["l1_facts_digest is not the identity digest of the stored fact copy"]),
    ("UPDATE public.ka_gochara_search_input_snapshot SET consumed_dasha_rows = jsonb_set(consumed_dasha_rows, '{0,content,lord_graha}', '\"moon\"')",
     ["dasha_digest is not the identity digest of the stored daśā copy", "the stored copy violates the capture contract: lord_path_inconsistent"]),
    # (ii) only METADATA inside the stored copy is changed (a tier): the metadata digest no longer recomputes, and the copy's own tier is no longer eligible
    ("UPDATE public.ka_gochara_search_input_snapshot SET consumed_dasha_rows = jsonb_set(consumed_dasha_rows, '{0,metadata,verification_pass_status}', '\"single\"')",
     ["dasha_metadata_digest is not the metadata digest of the stored daśā copy", "the stored copy violates the capture contract: period_tier_ineligible"]),
    # (iii) a stored DIGEST is changed and the copy left alone
    ("UPDATE public.ka_gochara_search_input_snapshot SET l1_facts_metadata_digest = repeat('0', 64)", ["l1_facts_metadata_digest is not the metadata digest of the stored fact copy"]),
    ("UPDATE public.ka_gochara_search_input_snapshot SET input_digest = repeat('0', 64)", ["input_digest is not the digest of the stored convention, vector, identity digests and AV declarations"]),
    # (iv) a period is removed from the copy and EVERY digest is recomputed consistently: nothing fails to recompute, the copy itself violates the contract
    ("WITH c AS (SELECT chart_id, generation, consumed_dasha_rows - (jsonb_array_length(consumed_dasha_rows) - 1) AS j FROM public.ka_gochara_search_input_snapshot)"
     " UPDATE public.ka_gochara_search_input_snapshot s SET consumed_dasha_rows = c.j, dasha_digest = public.ka_gochara_search_copy_digest(c.j, 'content'),"
     " dasha_metadata_digest = public.ka_gochara_search_copy_digest(c.j, 'metadata'), input_digest = public.ka_gochara_search_input_digest(s.convention_id,"
     " s.input_generation_vector, s.l1_facts_digest, public.ka_gochara_search_copy_digest(c.j, 'content'), s.av_declarations) FROM c"
     " WHERE (s.chart_id, s.generation) = (c.chart_id, c.generation)",
     ["the stored copy violates the capture contract: required_horizon_end_uncovered (level 3"]),
])
def test_a_stored_copy_that_does_not_recompute_or_violates_the_contract_is_a_named_violation_and_never_self_contained(g12, sql, expected):
    """Round 6, R7 (Fable round 5, P3-1, executed there: a tampered copy read CLEAN in the gate and in staleness, `self_contained: True`). The detector reads the
    stored row only — the stored copy against the stored digests and against the capture contract — so it fires whatever upstream looks like."""
    _step, conn = g12
    _tamper(conn, sql)
    found = _inconsistent(conn)
    assert found and all(any(f.startswith(x) for f in found) for x in expected), found
    if "jsonb_array_length" in sql:
        assert not [f for f in found if "is not the" in f], f"every digest recomputes; only the contract refuses: {found}"
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["self_contained"] is False and rep["copy_consistent"] is False and rep["copy_inconsistencies"] == sorted(found)
    assert rep["drifted"] is True and "copy" in rep["drifted_components"], "an inconsistent copy cannot read as a clean generation"
    # the same detector with upstream GONE: it is a statement about the row, not about live L1
    conn.execute("DELETE FROM public.chart_dashas")
    conn.execute("DELETE FROM public.chart_facts")
    assert sorted(_inconsistent(conn)) == sorted(found)


# ── R10: the digest is a function of the multiset of lines ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_copy_digest_orders_by_the_full_line_so_conflicting_duplicates_give_one_digest_in_any_order(g12):
    """Round 6, R10 (Fable round 5, P3-4): two elements that share a key and differ in content used to be concatenated in an unspecified order (the sort was by key
    only), so the digest of a conflicting population could flip between calls."""
    import hashlib
    import itertools
    _step, conn = g12
    a = {"key": {"k": 1}, "content": {"v": 1}, "metadata": {"m": 2}}
    b = {"key": {"k": 1}, "content": {"v": 2}, "metadata": {"m": 1}}
    c = {"key": {"k": 0}, "content": {"v": 3}, "metadata": {"m": 3}}
    for block in ("content", "metadata"):
        digests = {conn.execute("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, %s)", (json.dumps(list(perm)), block)).fetchone()[0]
                   for perm in itertools.permutations([a, b, c, b])}
        assert len(digests) == 1, (block, digests)
        lines = sorted(conn.execute("SELECT public.ka_gochara_canonical_json(%s::jsonb) || '|' || public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(%s::jsonb))",
                                    (json.dumps(e["key"]), json.dumps(e[block]))).fetchone()[0].encode() for e in (a, b, c, b))
        assert digests == {hashlib.sha256(b"\n".join(lines)).hexdigest()}, "sha256 of the byte-sorted FULL lines"
    assert conn.execute("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, 'content')", (json.dumps([a, c]),)).fetchone()[0] not in digests


# ── R4: the helper converts only the identified failure ─────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_live_read_helper_converts_only_the_identified_forbidden_read_and_lets_every_other_exception_through(g12):
    """Round 6, R4 (Codex round 5, finding 3; Fable P3-5). The reviewer exercised the round-5 helper with psycopg.OperationalError, PermissionError and TypeError:
    all three became assertion-shaped failures the mutation classifier counts as CAUGHT. Each now PROPAGATES with its own type (the harness classifies a call-phase
    failure of another type as UNEXPECTED-EXCEPTION), and only a REAL live read of a dropped L1 table, or 1305's own 'a snapshot is built from existing rows', fails
    the assertion."""
    import psycopg
    _step, conn = g12

    def boom(exc):
        def fn():
            raise exc
        return fn
    for exc in (psycopg.OperationalError("connection lost"), PermissionError("denied"), TypeError("unsupported operand"), KeyError("content"),
                inv_v.Unverifiable("the snapshot's consumed facts lack ['sun']"), psycopg.errors.InsufficientPrivilege("permission denied for table chart_facts"),
                psycopg.errors.UndefinedTable('relation "public.some_other_table" does not exist'), psycopg.errors.RaiseException("an unrelated refusal")):
        with pytest.raises(type(exc)) as e:
            _answers_from_the_copy(boom(exc))
        assert e.value is exc and not isinstance(e.value, pytest.fail.Exception), type(exc).__name__
    assert _answers_from_the_copy(lambda: 7) == 7
    # the two identified forms, produced by the REAL database, are the only ones converted
    ids = _snapshot(conn)["dasha_ids"]
    _rebuild_l1_with_new_ids(conn)
    with pytest.raises(pytest.fail.Exception, match="the code read live L1"):
        _answers_from_the_copy(lambda: conn.execute("SELECT public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[])", (CHART_ID, ids)).fetchone())
    conn.execute("DROP TABLE public.chart_facts CASCADE")
    with pytest.raises(pytest.fail.Exception, match="the code read live L1"):
        _answers_from_the_copy(lambda: conn.execute("SELECT count(*) FROM public.chart_facts").fetchone())
    with pytest.raises(pytest.fail.Exception, match="the code read live L1"):                              # ... also when the read is hidden in a server-side function
        _answers_from_the_copy(lambda: conn.execute("SELECT public.ka_gochara_search_facts_live_population(%s::uuid)", (CHART_ID,)).fetchone())


def test_the_harness_classifies_what_the_helper_now_lets_through_as_infrastructure_end_to_end():
    """R4, end to end through the classifier: the junit failure message pytest writes for each propagated exception type is NOT counted as a caught mutation."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("mutation_check_1305", base.MIGRATIONS.parent / "scripts" / "gochara" / "mutation_check_1305.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def report(msg):
        return f'<?xml version="1.0"?><testsuites><testsuite name="pytest"><testcase classname="t" name="x"><failure message="{msg}">trace</failure></testcase></testsuite></testsuites>'
    for msg in ("psycopg.OperationalError: connection lost", "PermissionError: denied", "TypeError: unsupported operand", "KeyError: 'content'",
                "services.gochara_kernel.inventory_verifier.Unverifiable: x", "psycopg.errors.InsufficientPrivilege: permission denied"):
        assert mod.classify(1, "", report(msg)) == "UNEXPECTED-EXCEPTION", msg
    assert mod.classify(1, "", report("Failed: the code read live L1 (it needed rows that are gone): UndefinedTable: x")) == "CAUGHT"


# ── R6: the chronological legacy replay ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_chronological_a_generation_sealed_with_a_legacy_snapshot_then_1305_applied_replays_and_a_first_seal_is_refused(monkeypatch, tmp_path):
    """Round 6, R6 (restored; Codex round 5, finding 5: round 5 deleted this test and its substitute only manufactured a legacy-shaped row). In real order: a
    generation is SEALED under the pre-1305 schema (a legacy snapshot: ids and 1206 digests, no copy); migration 1305 is then applied on top; the sealed generation
    REPLAYS (the replay branch asks nothing of the copy), while the completeness function — the first-seal branch and the candidate gate — names the missing copy
    for that same snapshot, and a NEW snapshot can no longer be written in the legacy shape. The seal is the pre-1240 shape (no approval receipt), as in the 1240
    chronological test."""
    import psycopg
    admin, name, dsn = create_am5_database("g12chron", faithful=True, apply_1240=False)              # 1206 + 1232 + grants, no 1240, no 1305
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
        RuleRegistryStore(conn).seed()
        ephe = make_ephe(tmp_path, monkeypatch)
        w = writer_mod.GocharaV5Writer()
        for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-chron", db_conn=conn, config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe}, dry_run=False)
            with conn.transaction():
                w.run_substep(ctx, SubStep(key=k, label=k))
        assert InventoryStore(conn).snapshot_copy_available() is False, "the pre-1305 schema: the snapshot is legacy-shaped"
        from services.gochara_kernel import ledger as gk_ledger
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            gk_ledger.publish(conn, CHART_ID, GEN)
            mid = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        assert conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0] == 1
        conn.execute(M1305.read_text())                                                                # 1305 applied on top of the SEALED generation
        assert InventoryStore(conn).snapshot_copy_available() is True
        legacy = conn.execute("SELECT consumed_fact_rows IS NULL AND consumed_dasha_rows IS NULL FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
                              (CHART_ID, GEN)).fetchone()[0]
        assert legacy is True, "the sealed snapshot stays legacy-shaped (1305 is additive; nothing rewrites it)"
        with conn.transaction():                                                                       # REPLAY: same manifest, no refusal, no copy asked for
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            assert conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] == mid
        replay = conn.execute("SELECT violation FROM public.ka_gochara_search_replay_violations(%s, %s)", (CHART_ID, GEN)).fetchall()
        assert not [r for r in replay if "copy" in r[0]], replay
        # the completeness function (the FIRST-seal branch and the candidate gate) now names the missing copy for that same legacy snapshot
        found = _violations(conn)
        assert [v for v in found if v[1] == "input_snapshot_without_copy"] and not [v for v in found if v[1] == "input_snapshot_copy_inconsistent"], found
        rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
        assert rep["self_contained"] is False and rep["copy_consistent"] is None and rep["sealed"] is True
    finally:
        conn.close()
        drop_am5_database(admin, name)


# ── R13: the shapes the reviewers' inventory marks as untested ──────────────────────────────────────────────────────────────────────────────────────────────

def test_two_periods_of_a_level_that_overlap_at_DISTINCT_starts_are_refused_by_the_database_as_an_overlap_not_as_a_duplicate(g12):
    """Round 6, R13 (Codex inventory: 'Overlap at distinct starts: Python case. No isolated SQL refusal test'). The Sun Antardaśā is made to begin a week before the
    previous one ends. No natural key is shared, every level still covers the horizon, every child is still inside its parent: ONLY the overlap rule refuses."""
    _step, conn = g12
    conn.execute("UPDATE public.chart_dashas SET start_iso = '2025-01-25T00:00:00+00' WHERE dasha_row_id = %s", (str(uuid.UUID(int=3)),))
    with pytest.raises(Exception) as e:
        _submit_all_eligible_ids(conn, None)
    msg = str(e.value)
    assert "(1 violation(s)): required_period_overlap (level 2 period starting 2025-01-25 00:00:00+00 begins before the previous ends (2025-02-01 00:00:00+00))" in msg, msg


def test_vimshottari_kp_rows_are_outside_the_scope_at_capture_and_after_it(g12):
    """Round 6, R13 (Fable round 5, D: 'a vimshottari_kp row present in the table (excluded by system filter, untested)'). KP sub-lord rows live under
    system_id 'vimshottari_kp' (ga_dashas_writer). They overlap the horizon at the same levels and carry a kp_sublevel; they are neither required nor extra."""
    step, conn = g12
    kp = ("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
          " verification_pass_status, kp_sublevel) SELECT gen_random_uuid(), chart_id, ayanamsha_id, 'vimshottari_kp', level_n, NULL, lord_graha, start_iso, end_iso, build_id,"
          " verification_pass_status, %s FROM public.chart_dashas WHERE system_id = 'vimshottari'")
    conn.execute(kp, ("sub",))
    assert conn.execute("SELECT count(*) FROM public.chart_dashas WHERE system_id = 'vimshottari_kp'").fetchone()[0] == 6
    InventoryStore(conn).delete_generation_inventory(CHART_ID, GEN)
    step(writer_mod.SNAPSHOT_SUBSTEP)                                    # a fresh capture THROUGH THE WRITER with the KP rows present: accepted
    s = _snapshot(conn)
    assert len(s["dashas"]) == 6 and {e["key"]["system_id"] for e in s["dashas"]} == {"vimshottari"} and {e["key"]["kp_sublevel"] for e in s["dashas"]} == {""}
    clean = _violations(conn)
    assert not [v for v in clean if v[1].startswith("input_snapshot")], clean
    conn.execute(kp, ("sub2",))                                          # more KP rows AFTER capture: not drift, not even soft
    assert _violations(conn) == clean
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["metadata_only_drift"] is False and rep["changes"] == []
    # a KP row SUBMITTED as an input is refused by name (it is not a period of the contract)
    one = str(conn.execute("SELECT dasha_row_id FROM public.chart_dashas WHERE system_id = 'vimshottari_kp' LIMIT 1").fetchone()[0])
    with pytest.raises(Exception, match=r"period_out_of_scope \(.*vimshottari_kp"):
        _submit_all_eligible_ids(conn, s, dasha_ids=[str(x) for x in s["dasha_ids"]] + [one])


def test_a_period_wholly_outside_the_horizon_a_deeper_level_and_a_fact_of_another_subject_cannot_be_smuggled_into_the_copy(g12):
    """R1's other direction (nothing but the contract's rows is STORED): rows that exist upstream but are not part of the contract are refused when submitted."""
    _step, conn = g12
    s = _snapshot(conn)
    ids = [str(x) for x in s["dasha_ids"]]
    outside = str(conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                               " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 1, NULL, 'Mercury', '2026-06-01', '2043-06-01', build_id,"
                               " verification_pass_status FROM public.chart_dashas WHERE level_n = 1 RETURNING dasha_row_id").fetchone()[0])
    with pytest.raises(Exception, match=r"period_outside_horizon \("):
        _submit_all_eligible_ids(conn, s, dasha_ids=ids + [outside])
    deeper = str(conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                              " verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, 4, dasha_row_id, 'Mercury', start_iso, end_iso, build_id,"
                              " verification_pass_status FROM public.chart_dashas WHERE level_n = 3 ORDER BY start_iso LIMIT 1 RETURNING dasha_row_id").fetchone()[0])
    with pytest.raises(Exception, match=r"period_out_of_scope \(.*\"level_n\":4"):
        _submit_all_eligible_ids(conn, s, dasha_ids=ids + [deeper])
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-URANUS', %s, 'lahiri_chitrapaksha', 'graha_position', 'URANUS', 'longitude_sidereal', 1.0),"
                 "        ('fact-SUN-speed', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'speed', 1.0)", (CHART_ID, CHART_ID))
    for extra in ("fact-URANUS", "fact-SUN-speed"):
        with pytest.raises(Exception, match=r"fact_out_of_scope \("):
            _submit_all_eligible_ids(conn, s, fact_ids=s["fact_ids"] + [extra])
    conn.execute("UPDATE public.chart_facts SET fact_value_num = NULL WHERE fact_id = 'fact-SUN'")
    with pytest.raises(Exception, match=r"fact_value_missing \(.*required_fact_missing|fact_value_missing \("):
        _submit_all_eligible_ids(conn, s, fact_ids=s["fact_ids"])
    with pytest.raises(Exception, match=r"period_row_id_duplicate \(|required_period_duplicate \("):       # the same row id submitted twice
        _submit_all_eligible_ids(conn, s, dasha_ids=ids + [ids[0]])


# ── legitimate snapshots must NOT be refused ────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_legitimate_upstream_shapes_are_accepted_at_capture_and_stay_clean(g12):
    """The other half of the attack: try to get a LEGITIMATE snapshot refused. All of these are accepted by the database contract and by the Python checker, and
    leave the gate without a single input_snapshot violation: a first period that starts BEFORE the horizon and a last one that ends AFTER it; periods that meet
    exactly (adjacency is not an overlap); a child that ends exactly where its parent ends and one that starts exactly where its parent starts; rows of ANOTHER
    system and of ANOTHER ayanamsha, and a period wholly outside the horizon of another tier, all present upstream; and a complete L1 rebuild (new row ids, a new
    build id, the same values) followed by a FRESH capture."""
    _step, conn = g12
    s = _snapshot(conn)
    rows = {int(uuid.UUID(e["metadata"]["dasha_row_id"]).int): e for e in s["dashas"]}
    assert rows[1]["key"]["start_iso"] < "2025-01-01" and rows[1]["content"]["end_iso"] > "2025-03-01"              # the MD spans the whole horizon
    assert rows[2]["content"]["end_iso"] == rows[3]["key"]["start_iso"] == rows[5]["content"]["end_iso"]             # adjacency; a PD ending exactly with its AD
    assert rows[6]["key"]["start_iso"] == rows[3]["key"]["start_iso"]                                                # a PD starting exactly with its AD
    for system, ayanamsha, a, b, tier in (("yogini", "lahiri_chitrapaksha", "2024-06-01", "2026-06-01", "two_pass_verified"),
                                          ("vimshottari", "raman", "2024-06-01", "2026-06-01", "single"),
                                          ("vimshottari", "lahiri_chitrapaksha", "2026-06-01", "2043-06-01", "single"),
                                          ("vimshottari", "lahiri_chitrapaksha", "2007-06-01", "2024-06-01", "single")):
        conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
                     " verification_pass_status) VALUES (gen_random_uuid(), %s, %s, %s, 1, NULL, 'Mercury', %s, %s, %s, %s)", (CHART_ID, ayanamsha, system, a, b, base.PINNED_BUILD, tier))
    conn.execute("INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num)"
                 " VALUES ('fact-SUN-raman', %s, 'raman', 'graha_position', 'SUN', 'longitude_sidereal', 290.5),"
                 "        ('fact-SUN-speed', %s, 'lahiri_chitrapaksha', 'graha_position', 'SUN', 'speed', 1.0)", (CHART_ID, CHART_ID))
    _submit_all_eligible_ids(conn, s, fact_ids=s["fact_ids"], dasha_ids=_scope_ids(conn))                           # accepted (parity asserted inside)
    assert not [v for v in _violations(conn) if v[1].startswith("input_snapshot")]
    _rebuild_l1_with_new_ids(conn)
    assert not [v for v in _violations(conn) if v[1].startswith("input_snapshot")], "the rebuild is metadata-only drift for the snapshot taken before it"
    _submit_all_eligible_ids(conn, None, dasha_ids=_scope_ids(conn))                                                # a FRESH capture over the rebuilt L1: accepted
    after = _snapshot(conn)
    assert after["dd"] == s["dd"] and after["l1"] == s["l1"] and after["ddm"] != s["ddm"], "the same identity, other metadata"
    assert not [v for v in _violations(conn) if v[1].startswith("input_snapshot")]
    rep = staleness.sealed_generation_staleness(conn, CHART_ID, GEN)
    assert rep["drifted"] is False and rep["metadata_only_drift"] is False and rep["self_contained"] is True


# ── the database contract and the independent Python checker agree on EVERY shape ───────────────────────────────────────────────────────────────────────────

def _shape_cases():
    """(name, mutate(facts, dashas) -> (facts, dashas), codes that MUST be reported, eligibility). `facts` / `dashas` are deep copies of a VALID stored copy (the
    stub world's: MD 1; AD 2, 3 under it; PD 4, 5 under AD 2 and PD 6 under AD 3), indexed below by the row number in `metadata.dasha_row_id`."""
    def row(d, n):
        return next(e for e in d if int(uuid.UUID(e["metadata"]["dasha_row_id"]).int) == n)

    def fact(f, subject):
        return next(e for e in f if e["key"]["fact_subject"] == subject)

    def without(d, *ns):
        return [e for e in d if int(uuid.UUID(e["metadata"]["dasha_row_id"]).int) not in ns]

    def edit(n, block, **kw):
        def go(f, d):
            row(d, n)[block].update(kw)
            return f, d
        return go

    def clone(d, n, new_id, **key):
        e = json.loads(json.dumps(row(d, n), default=_jsonable), parse_float=Decimal)
        e["metadata"]["dasha_row_id"] = str(uuid.UUID(int=new_id))
        e["key"].update(key)
        return e
    Y = True
    return [
        ("valid", lambda f, d: (f, d), set(), Y),
        # ── facts
        ("a subject left out", lambda f, d: ([e for e in f if e["key"]["fact_subject"] != "SUN"], d), {"required_fact_missing"}, Y),
        ("a subject twice", lambda f, d: (f + [dict(fact(f, "SUN"), metadata={"fact_id": "x"})], d), {"required_fact_duplicate"}, Y),
        ("a fact of another ayanamsha instead", lambda f, d: ([dict(e, key=dict(e["key"], ayanamsha_id="raman")) if e["key"]["fact_subject"] == "MOON" else e for e in f], d),
         {"fact_out_of_scope", "required_fact_missing"}, Y),
        ("a fact of a subject outside the ten", lambda f, d: (f + [dict(fact(f, "SUN"), key=dict(fact(f, "SUN")["key"], fact_subject="URANUS"))], d), {"fact_out_of_scope"}, Y),
        ("a fact of another key", lambda f, d: (f + [dict(fact(f, "SUN"), key=dict(fact(f, "SUN")["key"], fact_key="speed"))], d), {"fact_out_of_scope"}, Y),
        ("a fact without a number", lambda f, d: ([dict(e, content=dict(e["content"], fact_value_num=None)) if e["key"]["fact_subject"] == "LAGNA" else e for e in f], d),
         {"fact_value_missing"}, Y),
        ("a fact whose number is a string", lambda f, d: ([dict(e, content=dict(e["content"], fact_value_num="12.5")) if e["key"]["fact_subject"] == "LAGNA" else e for e in f], d),
         {"fact_value_missing"}, Y),
        ("no facts", lambda f, d: ([], d), {"required_fact_missing"}, Y),
        ("a fact element without a metadata block", lambda f, d: ([{k: v for k, v in e.items() if k != "metadata"} if e["key"]["fact_subject"] == "SUN" else e for e in f], d),
         {"copy_malformed", "required_fact_missing"}, Y),
        ("the fact copy is an object, not an array", lambda f, d: ({"facts": f}, d), {"copy_malformed", "required_fact_missing"}, Y),
        ("the fact copy is null", lambda f, d: (None, d), {"copy_malformed", "required_fact_missing"}, Y),
        # ── periods: members and coverage
        ("no periods", lambda f, d: (f, []), {"required_level_missing"}, Y),
        ("the daśā copy is null", lambda f, d: (f, None), {"copy_malformed", "required_level_missing"}, Y),
        ("a period element that is a string", lambda f, d: (f, d + ["x"]), {"copy_malformed"}, Y),
        ("the whole AD level left out", lambda f, d: (f, without(d, 2, 3)), {"required_level_missing", "required_parent_missing"}, Y),
        ("the whole MD level left out", lambda f, d: (f, without(d, 1)), {"required_level_missing", "required_parent_missing"}, Y),
        ("the whole PD level left out", lambda f, d: (f, without(d, 4, 5, 6)), {"required_level_missing"}, Y),
        ("the period over the horizon start left out", lambda f, d: (f, without(d, 4)), {"required_horizon_start_uncovered"}, Y),
        ("the period over the horizon end left out", lambda f, d: (f, without(d, 6)), {"required_horizon_end_uncovered"}, Y),
        ("a period in the middle left out", lambda f, d: (f, without(d, 5)), {"required_period_gap"}, Y),
        ("a gap between two periods", edit(5, "content", end_iso="2025-01-28T00:00:00+00:00"), {"required_period_gap"}, Y),
        ("an overlap at distinct starts", edit(6, "key", start_iso="2025-01-28T00:00:00+00:00"), {"required_period_overlap"}, Y),
        ("two periods of a level share a start", lambda f, d: (f, d + [clone(d, 5, 50)]), {"required_period_duplicate"}, Y),
        ("two periods share a start and differ in kp_sublevel", lambda f, d: (f, d + [clone(d, 5, 51, kp_sublevel="sub")]), {"required_period_duplicate"}, Y),
        ("the same element twice", lambda f, d: (f, d + [row(d, 5)]), {"required_period_duplicate", "period_row_id_duplicate"}, Y),
        ("a row id carried by two different periods", lambda f, d: (f, [dict(e, metadata=dict(e["metadata"], dasha_row_id=str(uuid.UUID(int=4))))
                                                                         if int(uuid.UUID(e["metadata"]["dasha_row_id"]).int) == 5 else e for e in d]), {"period_row_id_duplicate"}, Y),
        ("a row without a row id", edit(5, "metadata", dasha_row_id=None), {"period_row_id_duplicate"}, Y),
        ("a period that ends before it starts", edit(5, "content", end_iso="2025-01-10T00:00:00+00:00"), {"period_not_positive"}, Y),
        ("a period of zero length", edit(5, "content", end_iso="2025-01-15T00:00:00+00:00"), {"period_not_positive"}, Y),
        # ── periods: scope
        ("a period of another system", edit(5, "key", system_id="yogini"), {"period_out_of_scope"}, Y),
        ("a KP period added", lambda f, d: (f, d + [clone(d, 5, 52, system_id="vimshottari_kp", kp_sublevel="sub")]), {"period_out_of_scope"}, Y),
        ("a period of another ayanamsha", edit(5, "key", ayanamsha_id="raman"), {"period_out_of_scope"}, Y),
        ("a level-4 period added", lambda f, d: (f, d + [clone(d, 5, 53, level_n=4)]), {"period_out_of_scope"}, Y),
        ("a period wholly after the horizon added", lambda f, d: (f, d + [dict(clone(d, 1, 54, start_iso="2026-06-01T00:00:00+00:00"),
                                                                              content=dict(row(d, 1)["content"], end_iso="2043-06-01T00:00:00+00:00"))]), {"period_outside_horizon"}, Y),
        ("a period ending exactly at the horizon start added", lambda f, d: (f, d + [dict(clone(d, 1, 55, start_iso="2007-06-01T00:00:00+00:00"),
                                                                                         content=dict(row(d, 1)["content"], end_iso="2025-01-01T00:00:00+00:00"))]), {"period_outside_horizon"}, Y),
        # ── hierarchy
        ("an orphan PD (no natural parent pointer)", edit(5, "content", parent_level_n=None, parent_start_iso=None), {"required_parent_missing"}, Y),
        ("an orphan AD", edit(2, "content", parent_level_n=None, parent_start_iso=None), {"required_parent_missing"}, Y),
        ("a PD pointing two levels up", edit(5, "content", parent_level_n=1, parent_start_iso="2024-06-01T00:00:00+00:00"), {"required_parent_missing"}, Y),
        ("a PD pointing at a start no AD has", edit(5, "content", parent_start_iso="2024-11-01T00:00:00+00:00"), {"required_parent_missing"}, Y),
        ("a child whose parent_row_id is another row than the one at its parent's key (the substitution)", edit(2, "metadata", parent_row_id=str(uuid.UUID(int=77))),
         {"required_parent_id_mismatch"}, Y),
        ("the parent swapped for a row of another id", edit(1, "metadata", dasha_row_id=str(uuid.UUID(int=78))), {"required_parent_id_mismatch"}, Y),
        ("a child without a parent_row_id", edit(5, "metadata", parent_row_id=None), {"required_parent_id_mismatch"}, Y),
        ("a PD under the wrong sibling AD", edit(5, "content", parent_start_iso="2025-02-01T00:00:00+00:00"), {"required_parent_id_mismatch", "required_parent_not_containing"}, Y),
        ("an AD that ends after its MD", lambda f, d: (edit(1, "content", end_iso="2025-03-15T00:00:00+00:00")(f, d)), {"required_parent_not_containing"}, Y),
        ("a child that starts before its parent", lambda f, d: (edit(5, "content", parent_start_iso="2024-12-25T00:00:00+00:00")(*edit(4, "content", parent_start_iso="2024-12-25T00:00:00+00:00")(
            *edit(2, "key", start_iso="2024-12-25T00:00:00+00:00")(f, d)))), {"required_parent_not_containing"}, Y),
        ("a child whose lord path names another ancestor", edit(5, "content", lord_path="jupiter/moon/rahu"), {"lord_path_inconsistent"}, Y),
        ("a child whose own lord is not the end of its lord path", edit(5, "content", lord_graha="mercury"), {"lord_path_inconsistent"}, Y),
        ("an MD whose lord path is not its lord", edit(1, "content", lord_path="jupiter"), {"lord_path_inconsistent"}, Y),
        ("an MD that carries a parent_row_id (a parent of another chart, ayanamsha or system: its natural fields are NULL)", edit(1, "metadata", parent_row_id=str(uuid.UUID(int=79))),
         {"root_has_parent"}, Y),
        ("an MD that carries a natural parent pointer", edit(1, "content", parent_level_n=1, parent_start_iso="2007-06-01T00:00:00+00:00"), {"root_has_parent"}, Y),
        ("an MD with a parent is refused with eligibility OFF too", edit(1, "metadata", parent_row_id=str(uuid.UUID(int=79))), {"root_has_parent"}, False),
        ("an MD whose lord changed under its children", edit(1, "content", lord_graha="jupiter", lord_path="jupiter"), {"lord_path_inconsistent"}, Y),
        # ── eligibility (the copy's own tier and build), on and OFF
        ("one period of another tier", edit(5, "metadata", verification_pass_status="single"), {"period_tier_ineligible"}, Y),
        ("a period without a tier", edit(5, "metadata", verification_pass_status=None), {"period_tier_ineligible"}, Y),
        ("every period of another tier", lambda f, d: (f, [dict(e, metadata=dict(e["metadata"], verification_pass_status="single")) for e in d]), {"period_tier_ineligible"}, Y),
        ("one period of another build", edit(5, "metadata", build_id=OTHER_BUILD), {"dasha_builds_mixed"}, Y),
        ("a period without a build", edit(5, "metadata", build_id=None), {"period_build_missing"}, Y),
        ("another tier, another build and no build — eligibility OFF (drift): nothing", lambda f, d: (f, [dict(e, metadata=dict(
            e["metadata"], verification_pass_status="single", build_id=(None if i == 0 else OTHER_BUILD if i == 1 else e["metadata"]["build_id"]))) for i, e in enumerate(d)]),
         set(), False),
        ("a structural violation is reported with eligibility OFF too", lambda f, d: (f, without(d, 5)), {"required_period_gap"}, False),
        ("the metadata that is NOT part of the contract changes: nothing", lambda f, d: (f, [dict(e, metadata=dict(e["metadata"], engine_version="x", ordinal_path="9.9.9")) for e in d]),
         set(), Y),
    ]


def test_the_database_contract_and_the_independent_python_checker_agree_on_every_shape_and_every_code_is_exercised(g12):
    """The steward's instruction for round 6: the SQL logic and the independent Python checker must agree on every case. Every shape of `_shape_cases` is run through
    BOTH (`_contract_codes` compares the two multisets of codes); the codes each shape must produce are asserted; a shape that expects nothing must produce nothing;
    and the union of codes seen is EVERY code the SQL function can emit, so no rule exists that only one side implements or that no shape reaches."""
    _step, conn = g12
    s = _snapshot(conn)
    seen: set[str] = set()
    for name, mutate, expected, eligibility in _shape_cases():
        facts = json.loads(json.dumps(s["facts"], default=_jsonable), parse_float=Decimal)
        dashas = json.loads(json.dumps(s["dashas"], default=_jsonable), parse_float=Decimal)
        f2, d2 = mutate(facts, dashas)
        codes = _contract_codes(conn, json.dumps(f2, default=_jsonable), json.dumps(d2, default=_jsonable), eligibility=eligibility)
        assert expected <= set(codes), f"{name}: expected {sorted(expected)}, got {dict(codes)}"
        if not expected:
            assert not codes, f"{name}: a legitimate shape was refused: {dict(codes)}"
        seen |= set(codes)
    text = M1305.read_text()
    a = text.index("CREATE OR REPLACE FUNCTION public.ka_gochara_search_copy_violations(")
    emitted = set(re.findall(r"SELECT '([a-z_]+)'(?:::text)?,", text[a:text.index("\n$$;", a)]))
    assert len(emitted) == 23 and emitted == seen, f"codes no shape reaches: {sorted(emitted - seen)}; codes the SQL does not state: {sorted(seen - emitted)}"


def test_the_python_checker_derives_the_upstream_scope_itself_at_capture_and_refuses_a_copy_that_is_not_that_scope(g12):
    """The writer's capture-time call (`against_live=True`): the verifier reads live chart_dashas ITSELF (every tier and build), builds the natural parent pointer
    and the lord path from the rows' own parent ids, and requires the stored copy to equal that scope row for row and field for field. Here the stored copy is
    valid and upstream then changes: each change is named."""
    _step, conn = g12
    ok = inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN, against_live=True)
    assert ok == {"consumed": 6, "pinned_overlapping": 6, "source": "snapshot_copy_and_live"}
    cases = [
        ("UPDATE public.chart_dashas SET verification_pass_status = 'single' WHERE dasha_row_id = %s", r"upstream period_tier_ineligible .*copy_row_differs_from_upstream \(.*\['tier'\]"),
        ("UPDATE public.chart_dashas SET end_iso = end_iso + interval '1 hour' WHERE dasha_row_id = %s", r"copy_row_differs_from_upstream \(.*\['en'\]"),
        ("UPDATE public.chart_dashas SET lord_graha = 'Mercury' WHERE dasha_row_id = %s", r"copy_row_differs_from_upstream \(.*\['lord', 'lpath'\]"),
        ("DELETE FROM public.chart_dashas WHERE dasha_row_id = %s", r"upstream required_period_gap .*copy_row_not_in_upstream_scope"),
    ]
    conn.execute("CREATE TABLE _bak AS SELECT * FROM public.chart_dashas")
    for sql, pattern in cases:
        conn.execute(sql, (str(uuid.UUID(int=5)),))
        with pytest.raises(inv_v.Unverifiable, match=pattern):
            inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN, against_live=True)
        assert inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN)["source"] == "snapshot_copy", "the copy alone still verifies"
        conn.execute("DELETE FROM public.chart_dashas")
        conn.execute("INSERT INTO public.chart_dashas SELECT * FROM _bak")
    _insert_twin(conn, str(uuid.UUID(int=5)), tier="single")                                     # an extra upstream row of another tier at a consumed key
    with pytest.raises(inv_v.Unverifiable, match=r"upstream required_period_duplicate .*upstream_row_not_in_copy \(.*tier single"):
        inv_v.validate_consumed_dasha_population(conn, chart_id=CHART_ID, generation=GEN, against_live=True)


def test_the_natal_chart_is_never_read_from_a_fact_copy_that_violates_the_contract(g12):
    """Fable round 5, A-2: `chart_from_copy` did not detect a duplicated subject (the last element won) and relied on the database having refused it. It is now refused
    by the Python side too, by name."""
    _step, conn = g12
    facts = _snapshot(conn)["facts"]
    assert inv_v.chart_from_copy(facts)["lagna"] == base.CHART["lagna_deg"]
    sun = next(e for e in facts if e["key"]["fact_subject"] == "SUN")
    with pytest.raises(inv_v.Unverifiable, match=r"required_fact_duplicate \(subject SUN has 2 rows"):
        inv_v.chart_from_copy(facts + [dict(sun, content=dict(sun["content"], fact_value_num=Decimal("1.0")))])
    with pytest.raises(inv_v.Unverifiable, match=r"required_fact_missing \(subject SUN\)"):
        inv_v.chart_from_copy([e for e in facts if e is not sun])
    with pytest.raises(inv_v.Unverifiable, match=r"fact_out_of_scope"):
        inv_v.chart_from_copy(facts + [dict(sun, key=dict(sun["key"], ayanamsha_id="raman"))])


@pytest.mark.parametrize("column,value", [("chart_id", "00000000-0000-0000-0000-0000000000f3"), ("system_id", "yogini"), ("ayanamsha_id", "lahiri_other"), (None, None)])
def test_a_mahadasha_hanging_under_a_parent_of_another_chart_system_or_ayanamsha_is_refused_and_a_parentless_root_is_accepted(g12, column, value):
    """Round 6 follow-up (Codex v1.5, the blocking finding). The Mahādaśā is given a parent_row_id that names an EXISTING row of another chart, system or ayanamsha.
    The ancestry joins drop that row, so the copied natural parent fields are NULL and the lord path is the row's own lord: every other rule passes, in SQL and in
    Python. A root has no parent: `root_has_parent`. Control (None): the same world with a parentless root is accepted."""
    _step, conn = g12
    s = _snapshot(conn)
    md = str(uuid.UUID(int=1))
    if column is not None:
        if column == "chart_id":
            conn.execute("INSERT INTO public.charts(id) VALUES (%s)", (value,))
        foreign = conn.execute(
            f"INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, build_id,"
            f" verification_pass_status) SELECT gen_random_uuid(), {'%s::uuid' if column == 'chart_id' else 'chart_id'}, {'%s' if column == 'ayanamsha_id' else 'ayanamsha_id'},"
            f" {'%s' if column == 'system_id' else 'system_id'}, 1, NULL, 'Mercury', '1990-01-01T00:00:00+00', '2040-01-01T00:00:00+00', build_id, verification_pass_status"
            " FROM public.chart_dashas WHERE dasha_row_id = %s RETURNING dasha_row_id", (value, md)).fetchone()[0]
        conn.execute("UPDATE public.chart_dashas SET parent_row_id = %s WHERE dasha_row_id = %s", (foreign, md))
        el = conn.execute("SELECT public.ka_gochara_search_dasha_element(%s::uuid, %s::uuid)", (CHART_ID, md)).fetchone()[0]
        assert el["content"]["parent_level_n"] is None and el["content"]["lord_path"] == "saturn" and el["metadata"]["parent_row_id"] == str(foreign)
        with pytest.raises(Exception) as e:
            _submit_all_eligible_ids(conn, s, dasha_ids=_scope_ids(conn))
        msg = str(e.value)
        assert f"(1 violation(s)): root_has_parent (level 1 period starting 2024-06-01 00:00:00+00 carries a parent (row {foreign}" in msg, msg
        assert conn.execute("SELECT count(*) FROM public.ka_gochara_search_input_snapshot").fetchone()[0] == 0
    else:
        assert conn.execute("SELECT parent_row_id FROM public.chart_dashas WHERE dasha_row_id = %s", (md,)).fetchone()[0] is None
        _submit_all_eligible_ids(conn, s, dasha_ids=_scope_ids(conn))
        assert not [v for v in _violations(conn) if v[1].startswith("input_snapshot")]
