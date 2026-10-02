"""A5.3 — P1 prerequisite-restricted SUPPORT, re-derived independently (Codex round 7 [3]).

A P1 transit record's admitted support is its contact span (clipped to the horizon) restricted to the
periods the agent RUNS, keeping disjoint pieces. The builder cuts the span by CALLING Stream B's
`period_running_at`; `record_verifier.verify_p1_support` derives the same thing from the snapshot-bound
daśā rows with Postgres multirange arithmetic. Cases (the review's): a period that begins/ends inside a
contact, licensed pieces separated by a gap, an ingress before the horizon, retrograde re-crossings; an
agent with no L1 rows stays unrestricted with an explicit `unknown`.

Everything runs on the real applied schema (1081 + 1152–1157 + 1206) with the L1 tables stubbed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.dasha_read import make_period_rows_for
from services.gochara_kernel.record_verifier import verify_p1_support
from services.gochara_kernel.rule_registry import RuleRegistryStore
from services.gochara_kernel.substrate import SkyEventStore, assign_occurrence_ordinals, physical_object_id

from .test_a53_am5_writer import make_ephe
from .test_a53_inventory import CHART, CHART_ID, H0, H1, create_am5_database, drop_am5_database

UTC = timezone.utc
GEN = writer_mod.GENERATION
P1_PREREQS = [["period_running_at", "1.0.0"], ["natal_bhava_relationship", "1.0.0"],
              ["transit_relation", "1.0.0"]]


def _t(m, d):
    return datetime(2025, m, d, tzinfo=UTC)


def _lagna_house(edge, sign):
    signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
             "capricorn", "aquarius", "pisces"]
    return (signs.index(sign.lower()) - int(CHART["lagna_deg"] // 30)) % 12 + 1


@pytest.fixture()
def world(monkeypatch, tmp_path):
    """A fresh AM-5 database with the registry, convention, manifest, snapshot and ONE class inventory +
    coverage written, so a P1 grain can be materialised and verified. `daśā(rows)` rewrites the stubbed
    L1 daśā rows BEFORE the snapshot (the snapshot binds whatever is there)."""
    yield from _world(monkeypatch, tmp_path, faithful=False)


def _world(monkeypatch, tmp_path, faithful):
    import psycopg
    admin, name, dsn = create_am5_database("p1s", faithful=faithful)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    RuleRegistryStore(conn).seed()
    ephe = make_ephe(tmp_path, monkeypatch)
    w = writer_mod.GocharaV5Writer()

    def step(key):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-p1", db_conn=conn,
                          config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe},
                          dry_run=False)
        with conn.transaction():
            return w.run_substep(ctx, SubStep(key=key, label=key))

    def set_periods(venus):
        """Make Venus run exactly `venus` = [(level, start, end)]; the stub's other level-2/3 rows are removed
        (their gaps become honest `missing_inputs` ledger intervals; overlapping rows would be refused)."""
        conn.execute("DELETE FROM public.chart_dashas WHERE level_n IN (2, 3)")
        for i, (lvl, a, b) in enumerate(venus):
            conn.execute(
                "INSERT INTO public.chart_dashas(dasha_row_id, chart_id, ayanamsha_id, system_id, level_n,"
                " parent_row_id, lord_graha, start_iso, end_iso, build_id, verification_pass_status)"
                " VALUES (%s,%s,'lahiri_chitrapaksha','vimshottari',%s,NULL,'Venus',%s,%s,%s,'two_pass_verified')",
                (str(uuid.UUID(int=900 + i)), CHART_ID, lvl, a, b, base_build()))

    def set_lord_periods(rows):
        """rows = [(lord, level, start, end)]: replace ALL level-2/3 rows by exactly these (any lord)."""
        conn.execute("DELETE FROM public.chart_dashas WHERE level_n IN (2, 3)")
        for i, (lord, lvl, a, b) in enumerate(rows):
            conn.execute(
                "INSERT INTO public.chart_dashas(dasha_row_id, chart_id, ayanamsha_id, system_id, level_n,"
                " parent_row_id, lord_graha, start_iso, end_iso, build_id, verification_pass_status)"
                " VALUES (%s,%s,'lahiri_chitrapaksha','vimshottari',%s,NULL,%s,%s,%s,%s,'two_pass_verified')",
                (str(uuid.UUID(int=900 + i)), CHART_ID, lvl, lord.title(), a, b, base_build()))

    def boot():
        for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP,
                  "inventory:marriage", "coverage:marriage"):
            step(k)

    def seed_crossings(body, events):
        """events: [(level_deg, instant)] sign_ingress sky events for `body`."""
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            store = SkyEventStore(conn)
            sky = store.register_convention()
            by_level: dict[float, list] = {}
            for level, at in events:
                by_level.setdefault(level, []).append(at)
            for level, times in by_level.items():
                poid = physical_object_id(body=body, relation_kind="sign_ingress",
                                          canonical_target=f"point:{level!r}", convention_id=sky)
                store.insert_physical_object(poid)
                # ONE call per object: the occurrence ordinals count the repeated crossings 1, 2, 3 ...
                for contact, at in zip(assign_occurrence_ordinals(physical_object_id=poid,
                                                                  t_exact_list=sorted(times)), sorted(times)):
                    store.insert_event(contact, event_kind="sign_ingress", longitude=level,
                                       solver_method="swiss_refined", delta_lambda=2.0 / 3600.0, delta_t=1e-9,
                                       precision_regime="swiss_bisect_tol_1e-9d", coverage={"truncated": False})
            return sky

    def grain(agent, in_sign, house_for=_lagna_house, anchor=None, anchors=None):
        """Materialise the P1 `agent` Libra-residence grain read under `anchor` = (lord, level) — default: the
        agent's own AD; `in_sign(t)` says when the body is IN Libra."""
        wanted = list(anchors) if anchors else [anchor or (agent, "ad")]      # ONE call: the grain is rebuilt whole
        edges = [e for e in ev.enumerate_edges("marriage", "P1", CHART)
                 if e.transit and e.relation == "residence" and e.agent == agent
                 and e.obj.canonical_target == "span:7"
                 and (e.period_anchor_lord, e.period_anchor_level) in wanted]
        assert len(edges) == len(wanted)
        rows_for, _ = make_period_rows_for(conn, CHART_ID)
        store = rs.RecordStore(conn)
        sky = SkyEventStore(conn).register_convention()
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            return rs.materialise_record_grain(
                store, chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id="P1",
                edges=edges, horizon=(H0, H1),
                position_at=lambda body, t: 195.0 if in_sign(t) else 15.0, house_for=house_for,
                sky_convention_id=sky, source_fact_ids=["fact-1"], prerequisites=P1_PREREQS,
                chart=CHART, dasha_rows_for=rows_for)

    class W:
        pass
    wd = W()
    wd.conn, wd.step, wd.set_periods, wd.boot, wd.seed, wd.grain = conn, step, set_periods, boot, seed_crossings, grain
    wd.set_lord_periods = set_lord_periods
    try:
        yield wd
    finally:
        conn.close()
        drop_am5_database(admin, name)


def base_build():
    from .test_a53_inventory import PINNED_BUILD
    return PINNED_BUILD


def _supports(conn):
    return [[(r.lower, r.upper) for r in row[0]] for row in conn.execute(
        "SELECT temporal_support_intervals FROM public.ka_gochara_relationship_record"
        " WHERE path_id = 'P1' ORDER BY (SELECT lower(x) FROM unnest(temporal_support_intervals) x LIMIT 1) NULLS LAST,"
        " record_id").fetchall()]


def _results(conn):
    return sorted(r[0] for r in conn.execute(
        "SELECT p.result FROM public.ka_gochara_record_prerequisite p JOIN public.ka_gochara_relationship_record r"
        " ON r.record_id = p.record_id WHERE r.path_id = 'P1' AND p.predicate_id = 'period_running_at'").fetchall())


def test_a_period_ending_inside_a_contact_restricts_the_support_to_the_period(world):
    w = world
    w.set_periods([(2, _t(1, 1), _t(2, 1))])                      # Venus runs [01-01, 02-01)
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20))
    assert _supports(w.conn) == [[(_t(1, 10), _t(2, 1))]] and _results(w.conn) == ["true"]
    assert verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage") == {
        "records": 1, "restricted": 1}


def test_licensed_pieces_separated_by_a_gap_stay_disjoint_never_bridged(world):
    w = world
    w.set_periods([(2, _t(1, 1), _t(1, 12)), (2, _t(1, 18), _t(2, 1))])
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(1, 25))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(1, 25))
    assert _supports(w.conn) == [[(_t(1, 10), _t(1, 12)), (_t(1, 18), _t(1, 25))]]
    verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_a_contact_that_never_meets_a_running_period_is_computed_empty_and_false(world):
    w = world
    w.set_periods([(2, _t(2, 10), _t(2, 25))])
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(1, 25))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(1, 25))
    assert _supports(w.conn) == [[]] and _results(w.conn) == ["false"]
    assert w.conn.execute("SELECT temporal_support_state FROM public.ka_gochara_relationship_record"
                          " WHERE path_id = 'P1'").fetchone()[0] == "computed_empty"
    verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_an_ingress_before_the_horizon_is_clipped_then_restricted(world):
    w = world
    w.set_periods([(2, _t(1, 5), _t(1, 20))])                     # Venus runs [01-05, 01-20); horizon starts 01-01
    w.boot()
    dec = datetime(2024, 12, 15, tzinfo=UTC)                       # the ingress precedes the horizon
    w.seed("venus", [(180.0, dec), (210.0, _t(2, 10))])
    w.grain("venus", lambda t: dec <= t < _t(2, 10))
    assert _supports(w.conn) == [[(_t(1, 5), _t(1, 20))]]
    verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_retrograde_re_crossings_are_separate_contacts_each_restricted_on_its_own(world):
    w = world
    w.set_periods([(2, _t(1, 1), _t(2, 1))])
    w.boot()
    # enters Libra 01-10, retrogrades out 01-20, re-enters 01-25, leaves 02-20
    w.seed("venus", [(180.0, _t(1, 10)), (180.0, _t(1, 20)), (180.0, _t(1, 25)), (210.0, _t(2, 20))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(1, 20) or _t(1, 25) <= t < _t(2, 20))
    assert _supports(w.conn) == [[(_t(1, 10), _t(1, 20))], [(_t(1, 25), _t(2, 1))]]
    assert _results(w.conn) == ["true", "true"]
    verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_an_agent_with_no_daśā_rows_is_unrestricted_with_an_explicit_unknown(world):
    w = world
    w.set_periods([])                                              # Venus has NO rows
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(1, 25))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(1, 25))
    assert _supports(w.conn) == [[(_t(1, 10), _t(1, 25))]] and _results(w.conn) == ["unknown"]
    assert verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN,
                             event_class="marriage") == {"records": 1, "restricted": 0}


def test_the_verifier_refuses_a_support_that_admits_a_period_gap_or_discards_a_valid_portion(world):
    w = world
    w.set_periods([(2, _t(1, 1), _t(1, 12)), (2, _t(1, 18), _t(2, 1))])
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(1, 25))])
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(1, 25))
    # the pinned periods change AFTER the build (a wider Venus period would have admitted the gap ...)
    w.conn.execute("UPDATE public.chart_dashas SET end_iso = %s WHERE dasha_row_id = %s",
                   (_t(1, 18), str(uuid.UUID(int=900))))
    with pytest.raises(RuntimeError, match="P1 support verification failed"):
        verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")
    # ... and a narrower one would have discarded a valid portion
    w.conn.execute("UPDATE public.chart_dashas SET end_iso = %s WHERE dasha_row_id = %s",
                   (_t(1, 12), str(uuid.UUID(int=900))))
    w.conn.execute("UPDATE public.chart_dashas SET start_iso = %s WHERE dasha_row_id = %s",
                   (_t(1, 22), str(uuid.UUID(int=901))))
    with pytest.raises(RuntimeError, match="P1 support verification failed"):
        verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


class _RowsConn:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=()):
        class R:
            def __init__(s, rows):
                s.rows = rows

            def fetchall(s):
                return s.rows

            def fetchone(s):                                  # the schema probe: the 1233 anchor columns exist
                return (2,)
        return R(self.rows)


def test_the_stored_prerequisite_result_is_checked_against_the_support_it_implies():
    """(record_id, stored, expected, equal, expected_empty, result, has_rows): support equal in every row
    here, so ONLY the result check can speak."""
    ok = ("r1", "{[a,b)}", "{[a,b)}", True, False, "true", True)
    verify_p1_support(_RowsConn([ok]), chart_id=CHART_ID, generation=GEN, event_class="marriage")
    for bad in (("r1", "{[a,b)}", "{[a,b)}", True, False, "false", True),        # support non-empty but 'false'
                ("r2", "{}", "{}", True, True, "true", True),                      # empty support but 'true'
                ("r3", "{[a,b)}", "{[a,b)}", True, False, "true", False),          # no rows must be 'unknown'
                ("r4", "{[a,b)}", "{[a,b)}", True, False, None, True)):            # an unevaluated NULL result
        with pytest.raises(RuntimeError, match="period_running_at stored"):
            verify_p1_support(_RowsConn([bad]), chart_id=CHART_ID, generation=GEN, event_class="marriage")
