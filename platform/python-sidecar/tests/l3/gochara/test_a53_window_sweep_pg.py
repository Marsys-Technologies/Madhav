"""A5.3 — the window sweep against the REAL applied schema (1081 + 1152–1157), on a throwaway
database (NOT_RUN skip when the server is unreachable).

One admitted P3 record (Saturn's residence in Libra, the 7th signature house of marriage from the
fixture's Aries lagna) is materialised through the real record grain, then swept. The contract
checks that matter live in the database, not in the sweep: the 1156 coverage guard, the membership
guard, the score/evidence/severity CHECKs, the half-open interval, and delete-then-insert.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.rule_registry import RuleRegistryStore
from services.gochara_kernel.window_store import WindowStore

from .test_a53_record_store import (ADMIN_DSN, CHART, CHART_ID, DAY, DB_PREFIX, HORIZON,  # noqa: F401
                                    MIGRATION_CHAIN, MIGRATIONS, T0, _coverage_kwargs,
                                    _grain_kwargs, _seed_saturn_crossings, _sky_convention_id)

GEN = "5.0"
CLS, PATH, VERSION = "marriage", "P3", "1.0.0"


@pytest.fixture()
def pg():
    """A FRESH database per test (the windows these tests write must not leak between them): the
    gochara-5 chain applied verbatim, dropped afterwards; refuses to drop what it did not create."""
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}win_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
            cur.execute("CREATE TABLE public._migrations_applied"
                        " (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
            for fname in MIGRATION_CHAIN:
                cur.execute((MIGRATIONS / fname).read_text())
                cur.execute("INSERT INTO public._migrations_applied(filename) VALUES (%s)", (fname,))
            cur.execute("INSERT INTO public.charts(id) VALUES (%s)", (CHART_ID,))
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _declared_rows(path, version):
    """The real factor rows + the applicability block the 1.1.0 row declares (spans ⇒ step)."""
    rows = []
    for row in ws.registry_factor_rows(path, version):
        row = dict(row)
        if row["factor_id"] == "activity_kernel":
            row["applicability"] = {
                "span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
                         "inside": 1.0, "outside": 0.0},
                "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                            "function": "linear", "orb_deg": None}}
        elif row["factor_id"] == "graduated_drishti":
            row["applicability"] = {"relations": ["aspect"]}
        rows.append(row)
    return rows


@pytest.fixture()
def grain(pg):
    """Registry sealed, coverage written, one admitted P3 record materialised."""
    conn = pg
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_saturn_crossings(conn, sky_cid)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(store, **{**_grain_kwargs(store, sky_cid), "chart": CHART})
    assert counts["records"] == 1
    return conn


def _sweep_and_write(conn, rows_for):
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                               path_id=PATH, rule_version=VERSION)
    drafts, excluded = ws.draft_windows(CLS, recs, rows_for)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = ws_store.replace_grain_windows(
            chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH,
            rule_version=VERSION, drafts=drafts)
        verified = ws_store.verify_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                         path_id=PATH, rule_version=VERSION)
    return recs, drafts, excluded, counts, verified


def _window_rows(conn):
    return conn.execute(
        "SELECT lower(interval), upper(interval), peak_instant, score, evidence_for,"
        " evidence_against, outcome_valence_for_native, severity, null_states_used,"
        " coverage_partition_key FROM public.ka_gochara_eval_window ORDER BY 1").fetchall()


def test_the_materialised_record_is_admitted_and_scored(grain):
    (rec,) = WindowStore(grain).read_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                           path_id=PATH, rule_version=VERSION)
    assert (rec.admission_state, rec.operator_role, rec.relation) == ("admitted", "scored", "residence")
    assert rec.supports == ((T0 + 10 * DAY, T0 + 200 * DAY),)


def test_todays_registry_stores_an_honest_unqualified_window(grain):
    recs, drafts, excluded, counts, verified = _sweep_and_write(grain, ws.registry_factor_rows)
    assert counts == {"windows": 1, "memberships": 1, "replaced": 0} and verified == {"windows": 1}
    (row,) = _window_rows(grain)
    lo, hi, peak, score, ev_for, ev_against, valence, severity, null_states, key = row
    assert (lo, hi) == (T0 + 10 * DAY, T0 + 200 * DAY)           # the whole connected union
    assert (peak, score, ev_for, ev_against, severity) == (None, None, None, None, None)
    assert valence == "unqualified" and list(null_states) == ["unqualified"] and key == CLS


def test_a_declared_applicability_row_qualifies_the_same_record_with_no_code_change(grain):
    _sweep_and_write(grain, _declared_rows)
    (row,) = _window_rows(grain)
    lo, hi, peak, score, ev_for, ev_against, valence, severity, null_states, _ = row
    assert (lo, hi) == (T0 + 10 * DAY, T0 + 200 * DAY)
    assert peak == T0 + 10 * DAY and lo <= peak < hi            # earliest instant of the plateau max
    assert (score, ev_for, ev_against) == (1.0, 1.0, 0.0)
    assert severity is None                                      # named null, never 0
    assert valence == "favourable"                               # marriage is a gain class
    assert list(null_states) == []


def test_a_rerun_replaces_the_grain_never_accretes(grain):
    _sweep_and_write(grain, ws.registry_factor_rows)
    _, _, _, counts, _ = _sweep_and_write(grain, _declared_rows)
    assert counts == {"windows": 1, "memberships": 1, "replaced": 1}
    assert len(_window_rows(grain)) == 1
    assert grain.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] == 1


def test_the_independent_sql_union_check_catches_a_missing_window(grain):
    _sweep_and_write(grain, _declared_rows)
    with grain.transaction():
        grain.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        grain.execute("DELETE FROM public.ka_gochara_eval_window")
        with pytest.raises(RuntimeError, match="window verification failed"):
            WindowStore(grain).verify_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                            path_id=PATH, rule_version=VERSION)


def test_a_not_admitted_record_never_forms_a_window(grain):
    with grain.transaction():
        grain.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        grain.execute(
            "UPDATE public.ka_gochara_record_prerequisite SET result = 'false'")
        grain.execute(
            "UPDATE public.ka_gochara_relationship_record SET admission_state = 'not_admitted'")
    _, drafts, excluded, counts, _ = _sweep_and_write(grain, _declared_rows)
    assert drafts == [] and excluded["not_admitted"] == 1
    assert counts == {"windows": 0, "memberships": 0, "replaced": 0}


# ── through the writer's own substep ─────────────────────────────────────────

def test_the_writer_window_substep_runs_on_the_runners_native_types(grain, monkeypatch):
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-window", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    w = writer_mod.GocharaV5Writer()
    with grain.transaction():
        res = w.run_substep(ctx, SubStep(key=f"window:{CLS}:{PATH}", label="w"))
    assert res.rows_inserted == 2                                # 1 window + 1 membership row
    assert "1 window(s) (1 unqualified" in res.notes and "independent SQL union + semantic re-derivation passed" in res.notes
    (row,) = _window_rows(grain)
    assert row[3] is None and row[6] == "unqualified"
    # the dry run solves and writes nothing
    dry = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-dry", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=True)
    assert w.run_substep(dry, SubStep(key=f"window:{CLS}:{PATH}", label="w")).rows_inserted == 0


def _seed_crossings(conn, sky_cid, body, levels_days):
    """Sign-ingress sky events for `body` at (level°, day) pairs, under the real substrate convention."""
    from services.gochara_kernel.substrate import (SkyEventStore, assign_occurrence_ordinals,
                                                   physical_object_id)
    store = SkyEventStore(conn)
    for level, day in levels_days:
        poid = physical_object_id(body=body.lower(), relation_kind="sign_ingress",
                                  canonical_target=f"point:{level!r}", convention_id=sky_cid)
        store.insert_physical_object(poid)
        (contact,) = assign_occurrence_ordinals(physical_object_id=poid, t_exact_list=[T0 + day * DAY])
        store.insert_event(contact, event_kind="sign_ingress", longitude=level,
                           solver_method="swiss_refined", delta_lambda=2.0 / 3600.0, delta_t=1e-9,
                           precision_regime="swiss_bisect_tol_1e-9d", coverage={"truncated": False})


@pytest.fixture()
def p2_grain(pg):
    """P2 / career_advancement (a native gain class): Saturn in Aries is the 3rd from the natal Moon
    (Aquarius) — inside Saturn's cited favourable set, so the record is ADMITTED. Aries residence
    [day 20, day 120)."""
    from services.gochara_kernel import evaluator as ev
    from services.gochara_kernel.rule_registry import RuleRegistryStore as _R
    conn = pg
    _R(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_crossings(conn, sky_cid, "Saturn", ((0.0, 20), (30.0, 120)))
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    cls = "career_advancement"
    edges = [e for e in ev.enumerate_edges(cls, "P2", CHART)
             if e.transit and e.agent == "saturn" and e.relation == "residence"
             and e.obj.canonical_target == "span:1"]
    assert len(edges) == 1

    def probe(body, t):
        d = (t - T0) / DAY
        return 15.0 if 20 <= d < 120 else 195.0

    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **{**_coverage_kwargs(store, kala_cid, sky_cid),
                                          "event_class": cls,
                                          "class_edges": ev.enumerate_edges(cls, "P2", CHART),
                                          "position_at": probe})
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2", edges=edges,
            horizon=HORIZON, position_at=probe, house_for=writer_mod._house_resolver(CHART),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"], chart=CHART)
    assert counts["records"] == 1
    return conn, cls


def test_p2_record_is_admitted_with_its_direction_and_the_window_is_unqualified_until_vedha_is_bound(p2_grain):
    conn, cls = p2_grain
    ws_store = WindowStore(conn)
    (rec,) = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                                 rule_version=VERSION)
    assert (rec.admission_state, rec.house_from_frame, rec.agent) == ("admitted", 3, "saturn")
    assert ws.p2_direction(rec.agent, rec.house_from_frame) == "favourable"
    drafts, _ = ws.draft_windows(cls, [rec], ws.registry_factor_rows)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        ws_store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                       path_id="P2", rule_version=VERSION, drafts=drafts)
        ws_store.verify_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                              rule_version=VERSION)
    (row,) = _window_rows(conn)
    assert (row[0], row[1]) == (T0 + 20 * DAY, T0 + 120 * DAY)
    assert row[3] is None and row[6] == "unqualified"
    assert list(row[8]) == ["unqualified"]


def test_p2_with_a_bound_vedha_source_stores_both_channels_in_the_real_schema(p2_grain):
    conn, cls = p2_grain
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                               rule_version=VERSION)
    drafts, _ = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        ws_store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                       path_id="P2", rule_version=VERSION, drafts=drafts)
    (row,) = _window_rows(conn)
    # favourable residence is evidence FOR a gain class; the against channel is evaluated (P2 assigns
    # a direction per record), and empty
    assert (row[3], row[4], row[5]) == (0.5, 0.5, 0.0)
    assert row[2] == T0 + 20 * DAY and row[6] == "favourable"


def test_a_window_grain_outside_the_planned_paths_is_refused_by_name(grain):
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-x", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    with grain.transaction():
        res = writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=f"window:{CLS}:P5", label="w"))
    assert res.rows_inserted == 0 and "unknown window grain" in res.notes


# ── the independent semantic verifier ────────────────────────────────────────────────────────────────

def _write(conn, cls, path, drafts):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        WindowStore(conn).replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                                path_id=path, rule_version=VERSION, drafts=drafts)


def _verify(conn, cls, path, rows_for=ws.registry_factor_rows, **kw):
    from services.gochara_kernel.window_verifier import verify_window_semantics
    return verify_window_semantics(conn, chart_id=CHART_ID, generation=GEN, event_class=cls,
                                   path_id=path, rule_version=VERSION,
                                   factor_rows=rows_for(path, VERSION), **kw)


def _drafts(conn, cls, path, rows_for):
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                        path_id=path, rule_version=VERSION)
    return ws.draft_windows(cls, recs, rows_for)[0]


def test_verifier_reproduces_the_unqualified_and_the_qualified_window(grain):
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, ws.registry_factor_rows))
    # every member unqualified: nothing numeric to reproduce, and the structural checks hold
    assert _verify(grain, CLS, PATH) == {"windows": 1, "numeric_reproduced": 0, "structural_only": 1}
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, _declared_rows))
    out = _verify(grain, CLS, PATH, _declared_rows)
    assert out == {"windows": 1, "numeric_reproduced": 1, "structural_only": 0}


def test_verifier_refuses_a_wrong_score_a_wrong_peak_and_a_wrong_evidence_sum(grain):
    import dataclasses
    good = _drafts(grain, CLS, PATH, _declared_rows)
    for bad in (dataclasses.replace(good[0], score=0.5),
                dataclasses.replace(good[0], peak_instant=good[0].peak_instant + 7 * DAY),
                dataclasses.replace(good[0], evidence_for=2.0),
                dataclasses.replace(good[0], evidence_against=None),
                dataclasses.replace(good[0], severity=0.0)):
        _write(grain, CLS, PATH, [bad])
        with pytest.raises(RuntimeError, match="window semantic verification failed"):
            _verify(grain, CLS, PATH, _declared_rows)


def test_verifier_refuses_a_null_state_disclosure_the_records_do_not_support(grain):
    import dataclasses
    # one admitted qualified record: claiming 'unqualified' member(s) in the disclosure is a lie ...
    good = _drafts(grain, CLS, PATH, _declared_rows)
    _write(grain, CLS, PATH, [dataclasses.replace(good[0], null_states_used=["unqualified"])])
    with pytest.raises(RuntimeError, match="null_states_used"):
        _verify(grain, CLS, PATH, _declared_rows)
    # ... and under today's rows (every member unqualified) hiding it is too
    bad = dataclasses.replace(_drafts(grain, CLS, PATH, ws.registry_factor_rows)[0], null_states_used=[])
    _write(grain, CLS, PATH, [bad])
    with pytest.raises(RuntimeError, match="null_states_used"):
        _verify(grain, CLS, PATH)


def test_verifier_checks_the_p2_channels_from_the_cited_sets(p2_grain):
    conn, cls = p2_grain
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                        path_id="P2", rule_version=VERSION)
    drafts = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5)[0]
    _write(conn, cls, "P2", drafts)
    # the sweep ran with a bound vedha source; tell the verifier the same fact
    out = _verify(conn, cls, "P2", vedha_bound=True)
    assert out["windows"] == 1 and out["structural_only"] == 1      # vedha value is a function: not claimed


# ── P4 on the real schema: the window is the INTERSECTION; members extend past it ─────────────────────

@pytest.fixture()
def p4_grain(pg):
    """P4 / marriage: Jupiter in Libra [day 10, day 200) and Saturn in Libra [day 100, day 300) — the
    7th signature house from the Aries lagna. Both records are ADMITTED (each overlaps the other)."""
    from services.gochara_kernel import evaluator as ev
    from services.gochara_kernel.rule_registry import RuleRegistryStore as _R
    conn = pg
    _R(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_crossings(conn, sky_cid, "Jupiter", ((180.0, 10), (210.0, 200)))
        _seed_crossings(conn, sky_cid, "Saturn", ((180.0, 100), (210.0, 300)))
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    cls = "marriage"
    edges = [e for e in ev.enumerate_edges(cls, "P4", CHART)
             if e.transit and e.relation == "residence" and e.obj.canonical_target == "span:7"]
    assert {e.agent for e in edges} == {"jupiter", "saturn"}

    def probe(body, t):
        d = (t - T0) / DAY
        window = (10, 200) if body.lower() == "jupiter" else (100, 300)
        return 195.0 if window[0] <= d < window[1] else 15.0

    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **{**_coverage_kwargs(store, kala_cid, sky_cid),
                                          "event_class": cls,
                                          "class_edges": ev.enumerate_edges(cls, "P4", CHART),
                                          "position_at": probe})
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P4", edges=edges,
            horizon=HORIZON, position_at=probe, house_for=writer_mod._house_resolver(CHART),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"], chart=CHART)
    assert counts["records"] == 2
    return conn, cls


def test_p4_window_is_the_joint_support_and_members_extend_past_it(p4_grain):
    conn, cls = p4_grain
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P4",
                               rule_version=VERSION)
    assert {r.admission_state for r in recs} == {"admitted"}
    drafts, _ = ws.draft_windows(cls, recs, _declared_rows)
    _write(conn, cls, "P4", drafts)
    (row,) = _window_rows(conn)
    assert (row[0], row[1]) == (T0 + 100 * DAY, T0 + 200 * DAY)          # NOT the raw union [10, 300)
    assert (row[2], row[3]) == (T0 + 100 * DAY, 1.0)
    members = conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0]
    assert members == 2                                                     # both extend past the window
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        assert WindowStore(conn).verify_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                              path_id="P4", rule_version=VERSION) == {"windows": 1}
    assert _verify(conn, cls, "P4", _declared_rows) == {"windows": 1, "numeric_reproduced": 1,
                                                        "structural_only": 0}


def test_p4_sql_check_refuses_a_window_built_on_the_raw_union(p4_grain):
    import dataclasses
    conn, cls = p4_grain
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                        path_id="P4", rule_version=VERSION)
    good = ws.draft_windows(cls, recs, _declared_rows)[0][0]
    wrong = dataclasses.replace(good, interval=(T0 + 10 * DAY, T0 + 300 * DAY),
                                peak_instant=T0 + 10 * DAY)
    with pytest.raises(RuntimeError, match="SQL connected components"):
        _write(conn, cls, "P4", [wrong])
        _verify_store(conn, cls, "P4")


def _verify_store(conn, cls, path):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        WindowStore(conn).verify_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                       path_id=path, rule_version=VERSION)


def test_membership_is_overlap_a_dropped_overlapping_member_is_caught(p4_grain):
    conn, cls = p4_grain
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                        path_id="P4", rule_version=VERSION)
    _write(conn, cls, "P4", ws.draft_windows(cls, recs, _declared_rows)[0])
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("DELETE FROM public.ka_gochara_eval_window_record WHERE record_id ="
                     " (SELECT record_id FROM public.ka_gochara_eval_window_record LIMIT 1)")
    with pytest.raises(RuntimeError, match="not members"):
        _verify_store(conn, cls, "P4")


def test_verifier_refuses_a_partial_subtotal_stored_on_an_unqualified_window(grain):
    """R1: today's rows leave the only (for-channel) member unqualified, so the objective is
    unqualified — a stored score/peak/evidence_for would be a partial subtotal passed off as complete."""
    import dataclasses
    good = _drafts(grain, CLS, PATH, ws.registry_factor_rows)[0]
    assert good.score is None
    bad = dataclasses.replace(good, score=1.0, peak_instant=good.interval[0], evidence_for=1.0,
                              evidence_against=0.0)
    _write(grain, CLS, PATH, [bad])
    with pytest.raises(RuntimeError, match="partial subtotal"):
        _verify(grain, CLS, PATH)
