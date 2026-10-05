"""P1-EXCLUSION-FIX (steward P1-EMPTY-CLASS ruling, adopted): an EXCLUDED H-dependent path is verified by its EXCLUSION (nothing minted),
never by an expected population and never by emptiness.

THE DEFECT (Codex on PR 3142; Stream B ruling): eight of the 26 scored classes have signature houses H = UNKNOWN (GOCHARA_DESIGN_SPECS_v1_4
section 2.2, S:307-312). Under the standing ruling ST-H-UNKNOWN-20261002 their H-dependent paths P1, P3 and P4 are carried as `excluded` /
`inputs_unavailable` and the class seals `searched_scoped`; P1 mints nothing (`evaluator.enumerate_p1_edges` returns [] for H unknown). The
verification JOB already honoured that (it checks P1 only for classes whose P1 pin is INCLUDED), but the WRITER's in-build self-check called
`verify_p1_anchors`, which starts from the class-independent expected contact set and demands every contact and its anchored records: it failed at
`record:<class>:P1` of the first class of any full or all-classes build (`achievement_recognition` sorts first), even with real L1.

THE FIX: `verify_p1_anchors` (and a new job stage) verify the EXCLUSION for a class in the verifier's OWN `_UNKNOWN_H` table: zero relationship
records and zero windows in P1/P3/P4, any one is a failure by name. The acceptance is keyed on the ruling, never on the ledger being empty.

Tests (mutation-checked): each of the eight completes `record:<class>:P1` .. `verify:<class>` through the WRITER with nothing minted; a planted record
fails by name; a KNOWN-H class with an empty P1 ledger STILL fails; the two class lists are equal and are the eight; the all-classes slice's first class
completes; the verification job needs NO new stage (R11-1 already refuses any output in an excluded grain) and still checks P1 for a known-H class."""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import evaluator as gk_evaluator
from services.gochara_kernel import inventory_verifier as inv_v
from services.gochara_kernel import record_verifier as rv
from services.gochara_kernel.knots import calc_sidereal_lon

from .conftest import EPHE_PATH
from .test_a55_replace_chain import CHART_ID, FULLL, GEN, _World, template  # noqa: F401

EIGHT = ("achievement_recognition", "business_launch", "financial_deception", "foreign_settlement", "parental_event",
         "property_acquisition", "psychological_arc", "spiritual_turn")
RULING = "ST-H-UNKNOWN-20261002"
_JD_UNIX_EPOCH = 2440587.5


def _position_at(body, t):
    lon, _flag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + _JD_UNIX_EPOCH, EPHE_PATH)
    return lon


def _class_chain(w, cls, horizon=FULLL):
    """The writer's OWN per-class substeps in plan order: inventory, coverage, every record grain, every window grain, verify."""
    w.step(f"inventory:{cls}", horizon)
    w.step(f"coverage:{cls}", horizon)
    for p in writer_mod.RECORD_PATHS:
        w.step(f"record:{cls}:{p}", horizon)
    for p in writer_mod.WINDOW_PATHS:
        w.step(f"window:{cls}:{p}", horizon)
    w.step(f"verify:{cls}", horizon)


def _count(w, table, cls, paths=("P1", "P3", "P4")):
    return w.conn.execute(f"SELECT count(*) FROM public.{table} WHERE generation = %s AND event_class = %s AND path_id = ANY(%s)",
                          (GEN, cls, list(paths))).fetchone()[0]


# ── no database: the two lists, the ruling, the scope of the fix ────────────────────────────────────────────────────────

def test_the_builder_list_and_the_verifier_list_of_unknown_h_classes_are_equal_and_are_the_eight():
    builder = {c for c, k in gk_evaluator.ROW_MEMBERSHIP.items() if k == "unknown"}
    assert builder == set(EIGHT), sorted(builder ^ set(EIGHT))
    assert set(inv_v._UNKNOWN_H) == set(EIGHT), sorted(set(inv_v._UNKNOWN_H) ^ set(EIGHT))     # the verifier's OWN literal, not imported from the builder
    assert set(EIGHT) <= set(writer_mod.SCORED_CLASSES) and len(writer_mod.SCORED_CLASSES) == 26
    known = [c for c in writer_mod.SCORED_CLASSES if c not in EIGHT]
    assert len(known) == 18 and not (set(known) & set(inv_v._UNKNOWN_H))
    assert inv_v._H_DEPENDENT == ("p1", "p3", "p4") and rv.H_UNKNOWN_PATHS == ("P1", "P3", "P4")


def test_the_verifiers_ruling_literal_is_the_one_the_writer_hands_the_inventory_verifier():
    assert rv.H_UNKNOWN_RULING == RULING == writer_mod.VERIFIER_H_UNKNOWN_RULING["ruling_ref"]
    assert writer_mod.VERIFIER_H_UNKNOWN_RULING["basis"] == f"ruling:{RULING}"


def test_the_exclusion_check_refuses_to_be_used_for_a_known_h_class_so_it_cannot_excuse_an_omission():
    with pytest.raises(ValueError, match="not an H-unknown class"):
        rv.verify_h_unknown_exclusion(object(), chart_id=CHART_ID, generation=GEN, event_class="marriage")
    with pytest.raises(ValueError, match="not H-dependent paths"):
        rv.verify_h_unknown_exclusion(object(), chart_id=CHART_ID, generation=GEN, event_class=EIGHT[0], paths=("P2",))


class _Conn:
    """Answers the exclusion query with canned counts; records that no geometry or other table is read."""

    def __init__(self, records=None, windows=None):
        self.records, self.windows, self.sql = records or [], windows or [], []

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        self.sql.append(flat)
        rows = self.records if "ka_gochara_relationship_record" in flat else self.windows if "ka_gochara_eval_window" in flat else []

        class _R:
            def fetchall(self_inner):
                return list(rows)
        return _R()


def test_p1_anchors_for_an_unknown_h_class_verifies_the_exclusion_and_needs_no_geometry():
    conn = _Conn()
    out = rv.verify_p1_anchors(conn, chart_id=CHART_ID, generation=GEN, event_class=EIGHT[0], position_at=None)    # no ephemeris needed
    assert out["excluded"] == RULING and out["contacts"] == 0 and out["paths"] == ["P1"]
    assert len(conn.sql) == 2 and all("path_id = ANY" in s for s in conn.sql)


def test_a_p1_record_for_an_unknown_h_class_fails_by_name_in_the_anchor_verifier():
    with pytest.raises(RuntimeError, match=rf"P1 exclusion verification failed {EIGHT[3]}.*EXCLUDED.*{RULING}.*P1: 2 relationship records"):
        rv.verify_p1_anchors(_Conn(records=[("P1", 2)]), chart_id=CHART_ID, generation=GEN, event_class=EIGHT[3], position_at=None)


@pytest.mark.parametrize("records,windows,named", [
    ([("P3", 1)], [], "P3: 1 relationship records"), ([("P4", 4)], [], "P4: 4 relationship records"),
    ([], [("P1", 1)], "P1: 1 windows"), ([], [("P3", 2)], "P3: 2 windows"), ([("P1", 1)], [("P1", 1)], "P1: 1 relationship records, 1 windows")])
def test_the_job_level_exclusion_check_names_any_minted_p1_p3_p4_record_or_window(records, windows, named):
    with pytest.raises(RuntimeError, match=named):
        rv.verify_h_unknown_exclusion(_Conn(records=records, windows=windows), chart_id=CHART_ID, generation=GEN, event_class=EIGHT[1])


# ── the real writer on the real migration chain ─────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def world(template):
    w = _World(template)
    try:
        w.step(writer_mod.MANIFEST_SUBSTEP, FULLL)
        w.step(writer_mod.SNAPSHOT_SUBSTEP, FULLL)
        yield w
    finally:
        w.close()


@pytest.mark.parametrize("cls", EIGHT)
def test_each_of_the_eight_completes_its_whole_class_chain_through_the_writer_with_nothing_minted_in_p1_p3_p4(world, cls):
    """Before the fix this raised at `record:<class>:P1` ('P1 anchor verification failed ... not in the ledger') for every one of them."""
    _class_chain(world, cls)
    assert _count(world, "ka_gochara_relationship_record", cls) == 0 and _count(world, "ka_gochara_eval_window", cls) == 0
    out = rv.verify_p1_anchors(world.conn, chart_id=CHART_ID, generation=GEN, event_class=cls, position_at=_position_at)
    assert out["excluded"] == RULING and out["contacts"] == 0
    # the independent inventory verification of the class (the verify:<class> substep above) already agreed the P1/P3/P4 pins are excluded under the ruling
    pins = {r[0]: (r[1], r[2]) for r in world.conn.execute(
        "SELECT path_id, disposition, exclusion_reason FROM public.ka_gochara_search_path_pin WHERE generation = %s AND event_class = %s",
        (GEN, cls)).fetchall()}
    assert {p for p, (d, _r) in pins.items() if d == "excluded"} >= {"P1", "P3", "P4"}, pins


def test_the_first_class_of_an_all_classes_plan_completes(template):
    """The all-classes slice used to die at its FIRST class: the plan runs classes in sorted order and `achievement_recognition` sorts first."""
    w = _World(template)
    try:
        assert writer_mod.SCORED_CLASSES[0] == "achievement_recognition"
        w.step(writer_mod.MANIFEST_SUBSTEP, FULLL)
        w.step(writer_mod.SNAPSHOT_SUBSTEP, FULLL)
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=w.conn, dry_run=True,
                          config={"chart_id": CHART_ID, "horizon": FULLL, "ephe_path": EPHE_PATH})
        plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(ctx)]
        first = [k for k in plan[plan.index(f"inventory:{writer_mod.SCORED_CLASSES[0]}"):]
                 if k.endswith(writer_mod.SCORED_CLASSES[0]) or f":{writer_mod.SCORED_CLASSES[0]}:" in k]
        assert first[0] == "inventory:achievement_recognition" and first[-1] == "verify:achievement_recognition" and len(first) == 2 + len(writer_mod.RECORD_PATHS) + len(writer_mod.WINDOW_PATHS) + 1
        for key in first:                                              # every substep of the first class, in plan order, through the writer
            w.step(key, FULLL)
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_search_inventory WHERE generation = %s AND event_class = %s AND finalized_at IS NOT NULL",
                              (GEN, "achievement_recognition")).fetchone()[0] == 1
    finally:
        w.close()


def _plant(w, cls, path_id, source_class="marriage", source_path="P3"):
    """Copy one real record of a KNOWN-H class into `cls` under `path_id` (superuser, replica role: triggers are not what is observed)."""
    cols = [r[0] for r in w.conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_relationship_record'"
        " ORDER BY ordinal_position").fetchall()]
    sel = ", ".join("gen_random_uuid()" if c == "record_id" else "%s" if c == "event_class" else "%s" if c == "path_id" else c for c in cols)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        n = w.conn.execute(
            f"INSERT INTO public.ka_gochara_relationship_record ({', '.join(cols)}) SELECT {sel} FROM public.ka_gochara_relationship_record"
            " WHERE generation = %s AND event_class = %s AND path_id = %s LIMIT 1",
            [x for c in cols for x in ((cls,) if c == "event_class" else (path_id,) if c == "path_id" else ())] + [GEN, source_class, source_path]).rowcount
    assert n == 1, "no source record to plant (the stub world minted none)"


def test_a_planted_p3_record_for_an_unknown_h_class_fails_the_exclusion_check_by_name(world):
    _class_chain(world, "marriage", FULLL)                          # known-H class: its P3 records are minted normally on this world
    _class_chain(world, EIGHT[0])
    _plant(world, EIGHT[0], "P3")
    with pytest.raises(RuntimeError, match=rf"exclusion verification failed {EIGHT[0]}.*{RULING}.*P3: 1 relationship records"):
        rv.verify_h_unknown_exclusion(world.conn, chart_id=CHART_ID, generation=GEN, event_class=EIGHT[0])
    with pytest.raises(RuntimeError, match=rf"exclusion verification failed {EIGHT[0]}"):
        rv.verify_h_unknown_exclusion(world.conn, chart_id=CHART_ID, generation=GEN, event_class=EIGHT[0], paths=("P3",))
    # P1 alone is still clean: the anchor verifier checks ONLY P1
    assert rv.verify_p1_anchors(world.conn, chart_id=CHART_ID, generation=GEN, event_class=EIGHT[0], position_at=_position_at)["excluded"] == RULING


def test_a_known_h_class_with_an_empty_p1_ledger_STILL_fails_the_anchor_verifier(world):
    """The guard is NOT weakened: for a known-H class the expected contact set is never empty over a real horizon, so an empty P1 ledger is the
    zero-output case R9-2 (iii) exists to catch. Acceptance is keyed on the ruling, not on emptiness."""
    world.step("inventory:marriage", FULLL)
    world.step("coverage:marriage", FULLL)                          # no record:marriage:P1: the P1 ledger of a known-H class is empty
    assert _count(world, "ka_gochara_relationship_record", "marriage", ("P1",)) == 0
    with pytest.raises(RuntimeError, match=r"P1 anchor verification failed marriage.*not in the ledger"):
        rv.verify_p1_anchors(world.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", position_at=_position_at)


def test_the_writers_own_p1_grain_calls_the_anchor_verifier_for_every_class_and_the_verifier_decides(world, monkeypatch):
    """The WRITER is unchanged: its in-build P1 grain still calls `verify_p1_anchors` for every class; the verifier now decides. For a known-H class
    the call certifies the expected contact set (contacts > 0, no exclusion marker); for an unknown-H class it returns the exclusion marker."""
    seen = []
    real = writer_mod.verify_p1_anchors

    def spy(conn, **kw):
        out = real(conn, **kw)
        seen.append((kw["event_class"], out))
        return out
    monkeypatch.setattr(writer_mod, "verify_p1_anchors", spy)
    for cls in ("marriage", EIGHT[0]):
        world.step(f"inventory:{cls}", FULLL)
        world.step(f"coverage:{cls}", FULLL)
        world.step(f"record:{cls}:P1", FULLL)
    got = dict(seen)
    assert set(got) == {"marriage", EIGHT[0]}
    assert got["marriage"]["contacts"] > 0 and "excluded" not in got["marriage"]
    assert got[EIGHT[0]] == {"contacts": 0, "excluded": RULING, "paths": ["P1"], "records": 0, "windows": 0}


# ── the verification JOB: it ALREADY verifies the exclusion (R11-1), and still checks P1 for a known-H class ──────────────

def _verify(w, cls, **over):
    from services.gochara_kernel import verification_job as vj
    store = writer_mod.RuleRegistryStore(w.conn)
    kw = dict(chart_id=CHART_ID, generation=GEN, event_class=cls, position_at=_position_at,
              configured_selection=writer_mod.gk_rule_registry.selected_versions_for(cls), path_rulings=writer_mod.VERIFIER_PATH_RULINGS,
              h_unknown=writer_mod.VERIFIER_H_UNKNOWN_RULING, moon_scope_domain=False, factor_rows_for=store.bound_factor_rows,
              drishti_bound=False, vedha_bound=False, persist=False)
    kw.update(over)
    return vj.verify_class(w.conn, **kw)


def test_the_job_passes_an_unknown_h_class_without_a_p1_population_stage_and_still_runs_it_for_a_known_one(world):
    """The job's P1 stage keys on the class's INCLUDED P1 pin: for an unknown-H class (P1 excluded) it is skipped, for a known-H class it runs."""
    _class_chain(world, EIGHT[0])
    out = _verify(world, EIGHT[0])
    assert out.get("status") != "UNVERIFIED" and "p1" not in out, out
    _class_chain(world, "marriage")
    known = _verify(world, "marriage")
    assert "p1" in known and known["p1"]["anchors"]["contacts"] > 0, known


@pytest.mark.parametrize("path_id,source_path", [("P1", "P1"), ("P3", "P3")])
def test_the_job_already_refuses_a_record_minted_in_an_excluded_grain_so_the_exclusion_is_verified_there_too(world, path_id, source_path):
    """Confirmed for the P1-EXCLUSION-FIX assignment ('add the same positive exclusion check at the job if none exists'): one EXISTS. R11-1
    (`window_gate.generation_output_problems`, called first in `_verify_class`) refuses ANY relationship record, window or membership link in a (class, path,
    version) the inventory does not INCLUDE — and P1/P3/P4 of an unknown-H class are excluded — before anything is verified. So no job stage is added."""
    from services.gochara_kernel import verification_job as vj
    _class_chain(world, "marriage")
    _class_chain(world, EIGHT[0])
    _plant(world, EIGHT[0], path_id, source_path=source_path)
    with pytest.raises(vj.VerificationDisagrees, match=rf"generation_output.*record\(s\) in {EIGHT[0]}/{path_id}@.*a grain this generation's inventory does not include"):
        _verify(world, EIGHT[0])
