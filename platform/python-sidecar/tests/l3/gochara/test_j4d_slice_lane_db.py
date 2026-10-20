"""J-4d by slice (SR-BOLD-03) end to end on the local disposable cluster: the writer's real substeps, the real stored columns, the real golden format.

One clone of the a55 template builds three classes under the MEASURING rules and is exported as a golden bundle (what J-3c's capture is for the
real run). A second clone builds the same three classes under the FINAL rules through `build_slice`, and `verdict` compares the two. The
planted defect is made in the stored rows of one slice class, so it is the stored columns and the golden comparison that must catch it.
Classes: marriage (every cell unchanged by the final rules), bereavement (ND-P2-20261005 rule 3: P3 at 1.2.0 with rows under both rule sets; P2
unchanged) and parental_event (ND-H item 5: P2 emits no row under the final rules; P3 at 1.2.0). Paths P2 and P3 only: P1 cannot pass on the
stubbed L1 (see test_a55_replace_chain.py) and P4 yields nothing there, so the substeps are narrowed with build_slice's `head`/`kinds`/`paths`.
"""
from __future__ import annotations

import json
import re

import pytest

from scripts.kala_gochara_cutover import j4d_slice_qualify as q
from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import near_miss as nm

from .conftest import EPHE_PATH
from .test_a53_inventory import CHART_ID
from .test_a55_replace_chain import SHORT, _World, template  # noqa: F401
from .test_d1_near_miss_storage import KEY, NEAR, template_off  # noqa: F401

SLICE = ["bereavement", "marriage", "parental_event"]
PATHS = ("P2", "P3")
RECEIPT = ('{"head":"' + "a" * 40 + '","item":"P06b","merged_on_main":true,"mutation_verified":true,'
           '"review_job":"X-20261018T000000Z-test","step":"ephemeris_verifier_stage","verdict":"MET"}\n')


@pytest.fixture(scope="module", autouse=True)
def _lane_guard_is_proven_elsewhere():
    """The lane guard is exercised against fake connections in kala_db/test_j4d_slice_qualification.py; a CI service container is not
    the 127.0.0.1:55433 lane (its address is a bridge IP), so here it only insists on a disposable database name. Module-scoped: the
    module-scoped `measuring_dir` build calls `read_slice` before any function-scoped patch would be in place."""
    def disposable_only(conn):
        assert re.fullmatch(r"a53t_[a-z0-9_]+", conn.execute("SELECT current_database()").fetchone()[0])
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(q, "require_lane", disposable_only)
        yield


@pytest.fixture(scope="module")
def measuring_dir(_lane_guard_is_proven_elsewhere, template, tmp_path_factory):                                          # noqa: F811
    """The measuring build of the slice classes, exported in the J-3 golden format; yields the bundle directory."""
    world = _World(template)
    try:
        world.build(SHORT, classes=tuple(SLICE), paths=PATHS)
        rows = q.read_slice(world.conn, chart_id=CHART_ID, classes=SLICE)
        raw = mc._rows(world.conn, "SELECT r.*, COALESCE((SELECT jsonb_agg(jsonb_build_array(p.predicate_id, p.predicate_rule_version) ORDER BY p.ordinal)"
                       " FROM public.ka_gochara_record_prerequisite p WHERE p.record_id = r.record_id AND p.chart_id = r.chart_id"
                       " AND p.generation = r.generation), '[]'::jsonb) AS prerequisites FROM public.ka_gochara_relationship_record r"
                       " WHERE r.generation = '5.0'", ())
        assert raw, "the measuring build stored nothing: the scenario would prove nothing"
        bundle = mc.make_bundle(
            binding={"chart_id": CHART_ID, "generation": "5.0", "run_id": "run", "manifest_id": "m", "source_commit": "c" * 40},
            contacts=rows["contacts"], records=raw, windows=rows["windows"], horizon_basis={"schema": "x/1"}, stretch_sink=[],
            informational={"horizon": [SHORT[0].isoformat(), SHORT[1].isoformat()], "input_vector": {}})
        directory = tmp_path_factory.mktemp("j4d_golden") / "golden"
        mc.write_bundle(directory, bundle)
        yield directory
    finally:
        world.close()


@pytest.fixture(scope="module")
def measuring(measuring_dir):
    return q.load_golden(measuring_dir)


@pytest.fixture()
def final_world(template, measuring):                                                   # noqa: F811
    world = _World(template)
    try:
        yield world
    finally:
        world.close()


@pytest.fixture()
def receipt(tmp_path):
    path = tmp_path / "P06b.ephemeris_verifier_stage.json"
    path.write_text(RECEIPT, encoding="utf-8")
    return path


NARROW = dict(head=("rules", "manifest", "snapshot"), kinds=("inventory", "coverage", "record"), paths=PATHS)


def _build(world):
    return q.build_slice(world.conn, chart_id=CHART_ID, horizon=SHORT, classes=SLICE, ephe_path=EPHE_PATH, **NARROW)


def _verdict(world, golden, receipt):
    choice = q.choose_slice(classes=SLICE)
    return q.verdict(choice=choice, golden=golden, build=_build(world), sliced=q.read_slice(world.conn, chart_id=CHART_ID, classes=SLICE),
                     p06b=q.p06b_complete(receipt))


def test_the_final_rules_slice_is_qualified_against_the_measuring_golden(final_world, measuring, receipt):
    got = _verdict(final_world, measuring, receipt)
    assert got["build"]["defects"] == [] and got["build"]["substeps_run"] > 0
    assert got["verdict"] == q.QUALIFIED, got["reasons"]
    compared = {(c["event_class"], c["path_id"]) for c in got["equality"]["cells"]}
    assert ("marriage", "P3") in compared and ("bereavement", "P2") in compared and ("bereavement", "P3") not in compared
    assert sum(c["golden_records"] for c in got["equality"]["cells"]) > 0                       # the equality proof compared real rows


def test_the_final_rules_really_ran_the_changed_cell_at_the_final_version(final_world, measuring, receipt):
    """Without this the equality above could be a golden compared with the measuring rules again, or a changed/suppressed cell with nothing in it."""
    _verdict(final_world, measuring, receipt)
    final = {tuple(r) for r in final_world.conn.execute(
        "SELECT event_class, path_id, rule_version FROM public.ka_gochara_relationship_record WHERE generation = '5.0'").fetchall()}
    golden = {(json.loads(r["gkey"])["event_class"], json.loads(r["gkey"])["path_id"], json.loads(r["gkey"])["rule_version"]) for r in measuring["records"]}
    assert {v for _c, _p, v in golden} == {"1.0.0"}
    assert ("bereavement", "P3", "1.0.0") in golden and ("bereavement", "P3", "1.2.0") in final          # ND-P2-20261005 rule 3: P3 moved to 1.2.0
    assert ("bereavement", "P3", "1.0.0") not in final and ("bereavement", "P2", "1.0.0") in golden and ("bereavement", "P2", "1.0.0") in final
    assert ("parental_event", "P2", "1.0.0") in golden and not any(c == "parental_event" and p == "P2" for c, p, _v in final)   # ND-H item 5
    assert ("marriage", "P3", "1.0.0") in final and ("marriage", "P3", "1.0.0") in golden                     # an unchanged cell holds real rows


def test_a_planted_defect_in_one_slice_class_fails_the_proof_and_flips_the_verdict(final_world, measuring, receipt):
    assert _verdict(final_world, measuring, receipt)["verdict"] == q.QUALIFIED
    victim = final_world.conn.execute(
        "SELECT record_id FROM public.ka_gochara_relationship_record WHERE generation = '5.0' AND event_class = 'marriage' AND path_id = 'P3'"
        " ORDER BY record_id LIMIT 1").fetchone()
    assert victim is not None, "no marriage/P3 record to plant the defect in"
    final_world.conn.execute(          # one support starts one second late: nothing else about the record changes
        "UPDATE public.ka_gochara_relationship_record SET temporal_support_intervals = ARRAY(SELECT tstzrange(lower(s) + interval '1 second', upper(s))"
        " FROM unnest(temporal_support_intervals) WITH ORDINALITY AS u(s, n) ORDER BY n) WHERE record_id = %s", victim)
    got = q.verdict(choice=q.choose_slice(classes=SLICE), golden=measuring, build={"steps": [{"step": "x", "rows": 1}], "defects": []},
                    sliced=q.read_slice(final_world.conn, chart_id=CHART_ID, classes=SLICE), p06b=q.p06b_complete(receipt))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert got["reasons"] == ["equality_records_differ: marriage/P3"]


def test_the_command_line_writes_the_verdict_once_and_exits_zero_when_qualified(final_world, measuring_dir, receipt, tmp_path, monkeypatch, capsys):
    narrowed = q.build_slice
    monkeypatch.setattr(q, "build_slice", lambda conn, **kw: narrowed(conn, **kw, **NARROW))
    out = tmp_path / "verdict.json"
    argv = ["qualify", "--classes", ",".join(SLICE), "--golden", str(measuring_dir), "--dsn", final_world.dsn, "--ephe-path", EPHE_PATH,
            "--p06b-receipt", str(receipt), "--output", str(out)]
    assert q.main(argv) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["verdict"] == q.QUALIFIED and written["classes"] == sorted(SLICE) and written["independent_acceptance"] is None
    assert q.main(argv) == 2 and "REFUSED" in capsys.readouterr().err                  # reviewed evidence is never replaced


def test_a_lane_without_the_near_miss_storage_is_made_faithful_so_a_class_with_a_near_miss_verifies(template_off):   # noqa: F811
    """J-4d pre-run F2. On a lane that lacks migration 1308 the writer takes its pre-ND-P2 path (nowhere to keep a near-miss), so `verify:<class>` refuses
    every rootless positive-clearance stretch with "expected contact [...) is not in the ledger" - 10 of them for psychological_arc, all on the natal
    Moon point, none paired with an "invented" line. The stand-in chart has the same shape (Jupiter's 2003-12-15 loop to 2004-01-23 never reaches the
    aspect ray to point:265.39; test_d1_near_miss_storage pins the refusal on the OFF layer). `build_slice` must put the storage in first
    (the final candidate has it, ND-P2 rule 2) - the strict policy is not relaxed - and the near-miss is then stored, one unscored interval."""
    world = _World(template_off)
    try:
        assert not nm.NearMissStore(world.conn).layer_present()
        got = q.build_slice(world.conn, chart_id=CHART_ID, horizon=NEAR, classes=["marriage"], ephe_path=EPHE_PATH,
                            head=("rules", "manifest", "snapshot"), kinds=("inventory", "coverage", "record", "window", "verify"))
        assert got["defects"] == [], got["defects"]
        assert got["near_miss_layer"] == "applied" and "verify:marriage" in [s["step"] for s in got["steps"]]
        stored = world.conn.execute(
            "SELECT o.body, o.relation_kind, o.canonical_target, n.standing, n.score FROM public.ka_gochara_near_miss n"
            " JOIN public.ka_gochara_near_miss_object o USING (near_miss_object_id) WHERE n.generation = '5.0'").fetchall()
        assert [tuple(r) for r in stored] == [(*KEY, "near_miss", None)]
        assert q.ensure_near_miss_layer(world.conn) == "present"                              # idempotent: a lane that has it is left alone
    finally:
        world.close()
