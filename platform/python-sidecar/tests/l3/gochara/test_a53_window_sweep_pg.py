"""A5.3 — the window sweep against the REAL applied schema (1081 + 1152–1157), on a throwaway
database (NOT_RUN skip when the server is unreachable).

One admitted P3 record (Saturn's residence in Libra, the 7th signature house of marriage from the
fixture's Aries lagna) is materialised through the real record grain, then swept. The contract
checks that matter live in the database, not in the sweep: the 1156 coverage guard, the membership
guard, the score/evidence/severity CHECKs, the half-open interval, and delete-then-insert.
"""
from __future__ import annotations

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect  # noqa: E402
import dataclasses
import uuid
from datetime import datetime, timedelta

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
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise                    # a hostile admin DSN is a configuration ERROR, never a skip
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
    """The ACTUAL 1.1.0 catalogue rows (Stream B's #2897/#2907 — flat selector as source of truth, decoded
    applicability from the shared codec), not a hand-written nested block."""
    return [dict(r) for r in ws.registry_factor_rows(path, "1.1.0")]


def _qualification_manifest(conn, store, sky_cid, kala_cid):
    """A CANDIDATE manifest whose vector selects `window_qualification/1` — these fixtures exercise the numbers-enabled
    policy's semantics; the policy is the MANIFEST's (R9-1), so the generation must have one."""
    from services.gochara_kernel import ledger as gk_ledger
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        store.ensure_bridge(kala_cid, sky_cid)
        gk_ledger.publish_candidate(conn, CHART_ID, GEN, kala_cid, {"result_policy": "window_qualification/1"},
                                    {"backend": "swieph"}, "[2025-01-01T00:00:00+00:00,2026-01-01T00:00:00+00:00)",
                                    writer_asset_id="ka_gochara_v5")


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
    _qualification_manifest(conn, store, sky_cid, kala_cid)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(store, **{**_grain_kwargs(store, sky_cid), "chart": CHART})
    assert counts["records"] == 1
    return conn


@pytest.fixture(autouse=True)
def _geometry_probe_for_every_read(monkeypatch):
    """The sweep requires the contact GEOMETRY for span members (Codex round 7 [8]). The writer's store
    always supplies a position probe; these tests do the same, matched to the grains they seed."""
    original = WindowStore.read_grain

    def read_grain(self, **kw):
        if kw.get("position_at") is None:
            kw["position_at"] = _probe_for(kw["path_id"])
        return original(self, **kw)
    monkeypatch.setattr(WindowStore, "read_grain", read_grain)


def _p3_probe(body, t):
    """Saturn is in Libra for days [10, 200) of the grain — the same fact the seeded crossings state."""
    d = (t - T0) / DAY
    return 195.0 if 10 <= d < 200 else 15.0


def _swiss_from_spans(spans, inside=195.0, outside=15.0):
    """A `calc_sidereal_lon(body, jd, ephe)` stand-in CONSISTENT with the seeded geometry: `spans` = {body: [(a, b)]}
    — inside them the body is at `inside`°, elsewhere at `outside`°. The window phase's independent geometry check
    (R8-4) probes the ephemeris just inside/outside each stored span end, so a constant stand-in cannot satisfy it."""
    from datetime import timezone

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc)
        return (inside if any(a <= t < b for a, b in spans.get(body.lower(), ())) else outside), 2
    return calc


def _sweep_and_write(conn, rows_for):
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS,
                               path_id=PATH, rule_version=VERSION, position_at=_p3_probe)
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
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon",
                        _swiss_from_spans({"saturn": [(T0 + 10 * DAY, T0 + 200 * DAY)]}))
    monkeypatch.setattr(writer_mod, "_verify_live_inputs", lambda ctx, chart_id: None)   # own test below
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-window", db_conn=grain,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    w = writer_mod.GocharaV5Writer()
    with grain.transaction():
        res = w.run_substep(ctx, SubStep(key=f"window:{CLS}:{PATH}", label="w"))
    assert res.rows_inserted == 2                                # 1 window + 1 membership row
    assert "1 window(s) (1 unqualified" in res.notes and "reproduced all 1 window(s) exactly" in res.notes
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
    _qualification_manifest(conn, store, sky_cid, kala_cid)
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
    """The SOLVER's numbers (the dynamic switch lifted — the writer never does); the schema stores them."""
    conn, cls = p2_grain
    ws_store = WindowStore(conn)
    recs = ws_store.read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                               rule_version=VERSION)
    # a bound vedha source is a STATE-valued operand: with no stated boundaries the record is unqualified (R8-6) ...
    (unq,), _ = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5, allow_dynamic=True)
    assert unq.peak_instant is None and unq.unqualified_reason == ws.STATE_BOUNDARIES_REASON
    # ... the constant source here has no state change at all: its boundaries are stated complete and empty
    import dataclasses
    recs = [dataclasses.replace(r, state_boundaries=lambda lo, hi: [], state_boundaries_complete=True) for r in recs]
    drafts, _ = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5,
                                 allow_dynamic=True)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        ws_store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                       path_id="P2", rule_version=VERSION, drafts=drafts)
    (row,) = _window_rows(conn)
    # favourable residence is evidence FOR a gain class; the against channel is evaluated (P2 assigns
    # a direction per record), and empty
    assert (row[3], row[4], row[5]) == (0.5, 0.5, 0.0)
    assert row[2] == T0 + 20 * DAY and row[6] == "favourable"


def test_a_window_grain_outside_the_planned_paths_is_refused_by_name(grain, monkeypatch):
    monkeypatch.setattr(writer_mod, "_verify_live_inputs", lambda ctx, chart_id: None)
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


def _probe_for(path):
    def p2(body, t):
        d = (t - T0) / DAY
        return 15.0 if 20 <= d < 120 else 195.0
    def p4(body, t):
        d = (t - T0) / DAY
        window = (10, 200) if body.lower() == "jupiter" else (100, 300)
        return 195.0 if window[0] <= d < window[1] else 15.0
    return {"P2": p2, "P3": _p3_probe, "P4": p4}[path]


def _drafts(conn, cls, path, rows_for):
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls,
                                        path_id=path, rule_version=VERSION, position_at=_probe_for(path))
    return ws.draft_windows(cls, recs, rows_for)[0]


def test_verifier_reproduces_the_unqualified_and_the_qualified_window(grain):
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, ws.registry_factor_rows))
    # every member unqualified: nothing numeric to reproduce, and the structural checks hold
    out0 = _verify(grain, CLS, PATH)
    assert (out0["windows"], out0["numeric_reproduced"], out0["fully_reproduced"], out0["status"]) == (1, 0, 1, "VERIFIED")
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, _declared_rows))
    out = _verify(grain, CLS, PATH, _declared_rows)
    assert (out["windows"], out["numeric_reproduced"], out["fully_reproduced"], out["status"]) == (1, 1, 1, "VERIFIED")


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
    drafts = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5,
                              allow_dynamic=True)[0]
    _write(conn, cls, "P2", drafts)
    # the solver ran (switch lifted) with a bound vedha source — but NO source of vedha overlay edges exists, so the
    # record is unqualified (`state_boundaries_incomplete`, R8-6) and the window is NULL: builder and verifier derive
    # the same thing independently, so it is fully VERIFIED — no numeric vedha window can claim verification
    assert drafts[0].peak_instant is None and drafts[0].unqualified_reason == ws.STATE_BOUNDARIES_REASON
    out = _verify(conn, cls, "P2", vedha_bound=True, dynamic_enabled=True)
    assert out["windows"] == 1 and out["unverified_dynamic"] == 0
    assert out["status"] == "VERIFIED"


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
    _qualification_manifest(conn, store, sky_cid, kala_cid)
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
    out = _verify(conn, cls, "P4", _declared_rows)
    assert (out["windows"], out["numeric_reproduced"], out["status"]) == (1, 1, "VERIFIED")


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


# ── Codex round 7 [1]: unevaluated record evidence/severity is NULL, never a placeholder 0.0 ────────────

def test_an_unevaluated_record_stores_null_evidence_and_severity_not_zero(grain):
    row = grain.execute(
        "SELECT evidence_for_occurrence, evidence_against_occurrence, severity,"
        " outcome_valence_for_native FROM public.ka_gochara_relationship_record"
        " WHERE generation = %s", (GEN,)).fetchone()
    assert row == (None, None, None, "unqualified")


# ── persisted-or-reconstructable qualification ──────────────────────────────────────────────────────

def test_the_affected_channels_and_reasons_are_reconstructable_from_the_stored_rows(grain):
    """1156 has no column for per-window reasons: the contract is that they are OBLIGATORILY reconstructable
    from the stored members and the bound factor rows by code that shares nothing with the builder."""
    from services.gochara_kernel.window_verifier import reconstruct_qualification
    recs, drafts, _, _, _ = _sweep_and_write(grain, ws.registry_factor_rows)       # today's rows: unqualified
    rebuilt = reconstruct_qualification(grain, chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                        path_id=PATH, rule_version=VERSION,
                                        factor_rows=ws.registry_factor_rows(PATH, VERSION))
    (w,) = rebuilt.values()
    assert w["affected_channels"] == ["evidence_for_occurrence"]
    assert w["reasons"] == {drafts[0].record_ids[0]: ["applicability_undeclared"]} or \
        sorted(sum(w["reasons"].values(), [])) == ["applicability_undeclared"]
    # and the qualified world reconstructs to "nothing affected"
    _sweep_and_write(grain, _declared_rows)
    rebuilt2 = reconstruct_qualification(grain, chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                         path_id=PATH, rule_version=VERSION,
                                         factor_rows=_declared_rows(PATH, VERSION))
    (w2,) = rebuilt2.values()
    assert w2["affected_channels"] == [] and w2["reasons"] == {}


# ═══ Codex round 7 [5]: no unconditional pass — UNVERIFIED is a real state; universal bounds; source geometry ═══

def _p2_dynamic_world(p2_grain, monkeypatch):
    """A function-valued (vedha) P2 window the SOLVER numbers. The R8-6 boundary rule would make a vedha record
    unqualified (no vedha-edge source exists); these tests are about the window ARITHMETIC and the unverified-dynamic
    gate, which are independent of it, so BOTH sides' state-valued-factor sets are emptied here (the boundary rule has
    its own tests in test_a53_r86_sweep.py)."""
    from services.gochara_kernel import window_verifier as wv
    monkeypatch.setattr(ws, "STATE_VALUED_FACTORS", frozenset())
    monkeypatch.setattr(wv, "_STATE_VALUED", ())
    conn, cls = p2_grain
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                                        rule_version=VERSION)
    drafts = ws.draft_windows(cls, recs, ws.registry_factor_rows, vedha=lambda r, t: 0.5,
                              allow_dynamic=True)[0]
    return conn, cls, drafts


def test_a_fabricated_evidence_for_of_123_on_a_one_root_dynamic_window_is_refused(p2_grain, monkeypatch):
    """The review's reproduction: a one-root P2 window with evidence_for=123.0 used to be accepted as
    {numeric_reproduced: 0, structural_only: 1}. Even without reproducing the number, ONE root feeding a
    channel bounds its evidence by 1 (every per-root value is ≤ 1)."""
    import dataclasses
    conn, cls, drafts = _p2_dynamic_world(p2_grain, monkeypatch)
    _write(conn, cls, "P2", [dataclasses.replace(drafts[0], evidence_for=123.0)])
    with pytest.raises(RuntimeError, match="evidence_for 123.0 is outside"):
        _verify(conn, cls, "P2", vedha_bound=True, dynamic_enabled=True)
    _write(conn, cls, "P2", [dataclasses.replace(drafts[0], evidence_against=3.0)])
    with pytest.raises(RuntimeError, match="evidence_against 3.0 is outside"):
        _verify(conn, cls, "P2", vedha_bound=True, dynamic_enabled=True)
    # under the SWITCH (what the writer runs) any number on such a window is refused outright
    with pytest.raises(RuntimeError, match="partial subtotal was stored"):
        _write(conn, cls, "P2", [dataclasses.replace(drafts[0], evidence_for=123.0)])
        _verify(conn, cls, "P2", vedha_bound=True)


def test_a_genuine_dynamic_window_is_reported_unverified_and_cannot_satisfy_the_gate(p2_grain, monkeypatch):
    from services.gochara_kernel import window_verifier as wv
    conn, cls, drafts = _p2_dynamic_world(p2_grain, monkeypatch)
    _write(conn, cls, "P2", drafts)
    out = _verify(conn, cls, "P2", vedha_bound=True, dynamic_enabled=True)
    assert out["status"] == "UNVERIFIED_DYNAMIC" and out["unverified_dynamic"] == 1
    assert out["fully_reproduced"] == 0 and len(out["unverified_windows"]) == 1
    assert wv.satisfies_gate(out) is False


def test_the_verifier_checks_the_stored_outcome_valence_against_the_evidence(grain):
    """R8-4: the outcome valence is a governed field — a window whose valence contradicts its evidence (or whose
    NULL result carries anything but `unqualified`) is refused."""
    drafts = _drafts(grain, CLS, PATH, _declared_rows)
    assert drafts[0].outcome_valence_for_native == "favourable"                 # marriage is a gain class
    _write(grain, CLS, PATH, [dataclasses.replace(drafts[0], outcome_valence_for_native="adverse")])
    with pytest.raises(RuntimeError, match="outcome valence 'adverse' != 'favourable'"):
        _verify(grain, CLS, PATH, _declared_rows)
    null_drafts = _drafts(grain, CLS, PATH, ws.registry_factor_rows)
    _write(grain, CLS, PATH, [dataclasses.replace(null_drafts[0], outcome_valence_for_native="favourable")])
    with pytest.raises(RuntimeError, match="outcome valence 'favourable' != 'unqualified'"):
        _verify(grain, CLS, PATH)


def test_an_all_against_unqualified_p2_window_is_stored_and_verified_under_the_one_policy(p2_grain):
    """The review's demonstrated builder/verifier disagreement: an all-against P2 Saturn house-8 window at the 1.0.0
    registry (vedha unbound ⇒ the member is unqualified) is written by the builder AND accepted by the verifier —
    the for objective is identically 0 (peak at the start, evidence_for 0.0); score and evidence_against are NULL."""
    conn, cls = p2_grain
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("UPDATE public.ka_gochara_relationship_record SET house_from_frame = 8"
                     " WHERE path_id = 'P2'")                    # Saturn in the 8th: ADVERSE for a gain class
    drafts = ws.draft_windows(cls, WindowStore(conn).read_grain(
        chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2", rule_version=VERSION),
        ws.registry_factor_rows)[0]
    (d,) = drafts
    assert (d.evidence_for, d.objective_value, d.score, d.evidence_against) == (0.0, 0.0, None, None)
    assert d.peak_instant == d.interval[0] and d.outcome_valence_for_native == "unqualified"
    _write(conn, cls, "P2", drafts)
    out = _verify(conn, cls, "P2")
    assert out["status"] == "VERIFIED" and out["fully_reproduced"] == 1 and out["numeric_reproduced"] == 1
    (row,) = out["windows_detail"]
    assert row["objective_value"] == 0.0 and row["unresolved"] == {"vedha_overlay_not_bound": 1}
    assert row["affected_channels"] == ["evidence_against_occurrence"]
    # the same window with a fabricated score is refused (the live member is unqualified: its product is unknown)
    _write(conn, cls, "P2", [dataclasses.replace(d, score=0.0)])
    with pytest.raises(RuntimeError, match="score 0.0 != re-derived None"):
        _verify(conn, cls, "P2")


def test_a_fully_reproduced_world_satisfies_the_gate_and_an_unqualified_one_is_fully_verified(grain):
    from services.gochara_kernel import window_verifier as wv
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, ws.registry_factor_rows))      # all unqualified
    out = _verify(grain, CLS, PATH)
    assert out["status"] == "VERIFIED" and out["fully_reproduced"] == 1 and wv.satisfies_gate(out) is True
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, _declared_rows))                # constants, reproduced
    out2 = _verify(grain, CLS, PATH, _declared_rows)
    assert out2["status"] == "VERIFIED" and out2["numeric_reproduced"] == 1 and wv.satisfies_gate(out2)


def test_the_gate_helper_never_passes_a_report_that_is_not_verified():
    from services.gochara_kernel import window_verifier as wv
    assert wv.satisfies_gate({"status": "UNVERIFIED_DYNAMIC", "unverified_windows": ["w"]}) is False
    assert wv.satisfies_gate({"status": "VERIFIED", "unverified_windows": ["w"]}) is False
    assert wv.satisfies_gate({}) is False
    assert wv.satisfies_gate({"status": "VERIFIED", "unverified_windows": []}) is True


def test_the_writer_stores_a_dynamic_window_as_named_null_and_the_verifier_reproduces_exactly_that(p2_grain, monkeypatch):
    """With a vedha source bound the member is function-valued; the writer runs under the dynamic SWITCH, so the
    stored window is entirely NULL (named reason), and the independent verifier reproduces those NULLs — a
    VERIFIED window (an exact reproduction of 'no numeric result'), never an UNVERIFIED_DYNAMIC one."""
    conn, cls = p2_grain
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", _swiss_from_spans(
        {"saturn": [(T0 + 20 * DAY, T0 + 120 * DAY)]}, inside=15.0, outside=195.0))      # Saturn in Aries
    monkeypatch.setattr(writer_mod, "_verify_live_inputs", lambda ctx, chart_id: None)
    monkeypatch.setattr(writer_mod, "VEDHA_SOURCE", lambda rec, t: 0.5)
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-dyn", db_conn=conn,
                      config={"chart_id": uuid.UUID(CHART_ID), "horizon": HORIZON}, dry_run=False)
    with conn.transaction():
        res = writer_mod.GocharaV5Writer().run_substep(
            ctx, SubStep(key=f"window:{cls}:P2", label="w"))
    (row,) = _window_rows(conn)
    assert (row[2], row[3], row[4], row[5], row[6]) == (None, None, None, None, "unqualified")
    assert "UNVERIFIED" not in res.notes and "reproduced all 1 window(s) exactly" in res.notes
    from services.gochara_kernel import window_verifier as wv
    out = _verify(conn, cls, "P2", vedha_bound=True)
    assert out["status"] == "VERIFIED" and wv.satisfies_gate(out)
    (d,) = out["windows_detail"]
    # R8-6: with no source of vedha overlay edges the member is unqualified before the dynamic switch is reached
    assert d["unqualified_reason"] == "state_boundaries_incomplete"


class _GeomConn:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=()):
        class R:
            def __init__(s, rows):
                s.rows = rows

            def fetchall(s):
                return s.rows
        return R(self.rows)


def test_member_support_is_checked_against_the_source_geometry_and_the_kind_target_form():
    from services.gochara_kernel.window_verifier import verify_member_support
    kw = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version=VERSION)
    ok = [("r1", "sign_span", "span:7", True), ("r2", "house_lord", "point:12.5", True)]
    assert verify_member_support(_GeomConn(ok), **kw) == {"members": 2}
    with pytest.raises(RuntimeError, match="not the contact span"):
        verify_member_support(_GeomConn([("r1", "sign_span", "span:7", False)]), **kw)
    for kind, target in (("sign_span", "point:12.5"), ("house_lord", "span:7"), ("star", "star:28"),
                         ("sign_span", "span:13")):
        with pytest.raises(RuntimeError, match="object kind"):
            verify_member_support(_GeomConn([("r1", kind, target, True)]), **kw)
    # P1's support is the prerequisite-restricted one (record_verifier's), not the raw contact span
    assert verify_member_support(_GeomConn([("r1", "sign_span", "span:7", False)]),
                                 **dict(kw, path_id="P1")) == {"members": 1}


def test_member_support_check_passes_on_the_real_schema(grain):
    from services.gochara_kernel.window_verifier import verify_member_support
    _write(grain, CLS, PATH, _drafts(grain, CLS, PATH, ws.registry_factor_rows))
    assert verify_member_support(grain, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH,
                                 rule_version=VERSION) == {"members": 1}


def test_a_wrong_but_in_bounds_evidence_sum_is_caught_by_the_exact_check_not_only_the_bounds(p4_grain):
    """Two roots (Jupiter, Saturn) are live at the P4 peak: evidence_for must be 2.0. Storing 1.0 is
    inside the universal bounds ([0, 2], ≥ the score 1.0) — only the exact re-derivation can refuse it."""
    import dataclasses
    conn, cls = p4_grain
    recs = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P4",
                                        rule_version=VERSION)
    good = ws.draft_windows(cls, recs, _declared_rows)[0][0]
    assert good.evidence_for == 2.0 and good.score == 1.0
    _write(conn, cls, "P4", [dataclasses.replace(good, evidence_for=1.0)])
    with pytest.raises(RuntimeError, match="evidence_for 1.0 != re-derived 2.0"):
        _verify(conn, cls, "P4", _declared_rows)


def test_the_store_asserts_boundary_completeness_only_where_it_has_a_boundary_source(p2_grain):
    """R8-6: a residence record has no state-boundary source (only a dṛṣṭi record's sign ingresses are one), so the
    store never asserts completeness for it — read back from the real schema, not stubbed."""
    conn, cls = p2_grain
    (rec,) = WindowStore(conn).read_grain(chart_id=CHART_ID, generation=GEN, event_class=cls, path_id="P2",
                                          rule_version=VERSION)
    assert rec.state_boundaries is None and rec.state_boundaries_complete is False
