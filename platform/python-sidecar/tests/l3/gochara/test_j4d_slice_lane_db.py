"""J-4d by slice (SR-BOLD-03) end to end on the local disposable cluster: the writer's real substeps, the real stored columns, the real golden format.

One clone of the a55 template builds three classes under the MEASURING rules WITH THE PRE-FIX EDGE DERIVATION (`prefix_edge_derivation`: what the real
measuring build ran) and is exported as a golden bundle (what J-3c's capture is for the real run). A second clone builds the same three classes under the
FINAL rules through `build_slice` with the current (fixed) solver, and `verdict` compares the two: equality of every field except the point-contact edges,
the independent-root tolerance proof, the solver isolation proof, STRICT certification with 0 invented / 0 anomaly, and the peak-windows row. A third clone
re-derives the golden's cells with the fixed solver (`j4d_rederive_golden`, SR-EDGES-PROOF c) and the final slice must equal that byte for byte. The
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
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import near_miss as nm
from services.gochara_kernel import rule_registry as rr

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
        # SR-OD1 V1: the doctrine rows (P1/P3/P4@1.3.0, P2@1.1.0) change every scored cell under the final rules, leaving no
        # "unchanged" cell for this equality-with-the-golden scenario; it runs on the pre-doctrine final profile (ND-H / ND-P2 /
        # parental suppression only), exactly like kala_db/test_j4d_slice_qualification.py. The TRIAL gates the doctrine rows.
        patch.setattr(rr, "FINAL_SELECTED_PATH_REFS", rr.SELECTED_PATH_REFS)
        patch.setattr(rr, "FINAL_ONLY_PATH_REFS", rr.ND_H_PATH_REFS)
        yield


@pytest.fixture(scope="module")
def measuring_dir(_lane_guard_is_proven_elsewhere, template, tmp_path_factory):                                          # noqa: F811
    """The measuring build of the slice classes, exported in the J-3 golden format; yields the bundle directory."""
    world = _World(template)
    try:
        with q.prefix_edge_derivation():                  # the old golden is what the pre-fix derivation stored
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


_REAL_BUILD = q.build_slice                  # the CLI test replaces q.build_slice with _narrowed_build
NARROW = dict(head=("rules", "manifest", "snapshot"), kinds=("inventory", "coverage", "record"), paths=PATHS)


def _narrowed_build(conn, **kw):
    """`build_slice` narrowed to what the stubbed-L1 world can run. That world cannot run the `verify:<class>` substeps (where the writer certifies), so the
    writer's own strict call (`certify_contact_geometry` under POLICY_RAISE with a graze sink, as the near-miss layer passes) is made here, through the
    build observer, and merged into what the build observed."""
    got = _REAL_BUILD(conn, **kw, **NARROW)
    with q.observe_build() as seen:
        for cls in SLICE:
            cc.certify_contact_geometry(conn, chart_id=kw["chart_id"], generation="5.0", event_class=cls, position_at=q.swiss_position_at(kw["ephe_path"]),
                                        graze_sink=[], sink_policy=cc.POLICY_RAISE)
    got["observed"]["certification_policies"] += seen["certification_policies"]
    return got


def _build(world):
    return _narrowed_build(world.conn, chart_id=CHART_ID, horizon=SHORT, classes=SLICE, ephe_path=EPHE_PATH)


def _proofs(world, golden, build):
    """Everything `qualify` measures beyond the equality proof, on the built lane database."""
    sliced = q.read_slice(world.conn, chart_id=CHART_ID, classes=SLICE)
    measured = q.measure_certification(world.conn, chart_id=CHART_ID, classes=SLICE, ephe_path=EPHE_PATH)
    return sliced, dict(
        tolerance=q.tolerance_proof(sliced, golden["horizon"], ephe_path=EPHE_PATH),
        isolation=q.solver_isolation_proof(golden, SLICE, golden["horizon"], ephe_path=EPHE_PATH),
        certification=q.certification_proof(build["observed"], measured),
        peak_windows=q.peak_windows_row(world.conn, chart_id=CHART_ID, classes=SLICE, observed=build["observed"]))


def _verdict(world, golden, receipt, **extra):
    choice = q.choose_slice(classes=SLICE)
    build = _build(world)
    sliced, proofs = _proofs(world, golden, build)
    return q.verdict(choice=choice, golden=golden, build=build, sliced=sliced, p06b=q.p06b_complete(receipt), **proofs, **extra)


def test_the_final_rules_slice_is_qualified_against_the_measuring_golden(final_world, measuring, receipt):
    got = _verdict(final_world, measuring, receipt)
    assert got["build"]["defects"] == [] and got["build"]["substeps_run"] > 0
    assert got["verdict"] == q.QUALIFIED, got["reasons"]
    compared = {(c["event_class"], c["path_id"]) for c in got["equality"]["cells"]}
    assert ("marriage", "P3") in compared and ("bereavement", "P2") in compared and ("bereavement", "P3") not in compared
    assert sum(c["golden_records"] for c in got["equality"]["cells"]) > 0                       # the equality proof compared real rows
    assert got["equality"]["point_contacts_edge_exempt"] > 0                                    # ... including point contacts whose edges the fix moved
    assert got["tolerance"]["edges_judged"] > 0 and got["solver_isolation"]["passed"] and got["solver_isolation"]["edges_fixed_vs_prefix"]["moved"] > 0
    assert got["certification"]["passed"] and got["certification"]["policy"] == "raise" and (got["certification"]["invented"], got["certification"]["anomaly"]) == (0, 0)
    assert got["peak_windows"]["passed"] and got["peak_windows"]["admitted"] is False           # all_null_candidate/1 is the default: no peak is admitted
    assert got["edge_moves"]["moved"] > 0                                                       # before / after: the fix really moved edges in this world


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
    build = {"steps": [{"step": "x", "rows": 1}], "defects": [], "observed": {"certification_policies": ["raise"], "maximise_earliest_calls": 0}}
    sliced, proofs = _proofs(final_world, measuring, build)
    got = q.verdict(choice=q.choose_slice(classes=SLICE), golden=measuring, build=build, sliced=sliced, p06b=q.p06b_complete(receipt), **proofs)
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert got["reasons"] == ["equality_records_differ: marriage/P3"]


def test_the_command_line_writes_the_verdict_once_and_exits_zero_when_qualified(final_world, measuring_dir, receipt, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(q, "build_slice", _narrowed_build)
    out = tmp_path / "verdict.json"
    argv = ["qualify", "--classes", ",".join(SLICE), "--golden", str(measuring_dir), "--dsn", final_world.dsn, "--ephe-path", EPHE_PATH,
            "--p06b-receipt", str(receipt), "--output", str(out)]
    assert q.main(argv) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["verdict"] == q.QUALIFIED and written["classes"] == sorted(SLICE) and written["independent_acceptance"] is None
    assert q.main(argv) == 2 and "REFUSED" in capsys.readouterr().err                  # reviewed evidence is never replaced


# ── SR-EDGES-PROOF (c): the golden re-derived locally with the fixed solver ───────────────────────────────────────────

from scripts.kala_gochara_cutover import j4d_rederive_golden as rg                              # noqa: E402


@pytest.fixture()
def rederive_world(template, measuring):                                                      # noqa: F811
    world = _World(template)
    try:
        yield world
    finally:
        world.close()


def _rederive(world, golden, solver):
    return rg.rederive(world.conn, golden, SLICE, ephe_path=EPHE_PATH, solver=solver, **NARROW)


def test_the_prefix_re_derivation_reproduces_the_old_golden_byte_for_byte(rederive_world, measuring):
    """The control: the old derivation, re-run from the golden's own inputs, IS the golden (edges included). Without this a re-derivation proves nothing."""
    got = _rederive(rederive_world, measuring, "prefix")
    assert got["build"]["defects"] == [] and got["equality_with_old_golden"]["passed"], got["equality_with_old_golden"]["problems"]
    assert got["equality_with_old_golden"]["strict_edges"] and got["equality_with_old_golden"]["all_cells"]
    assert got["equality_with_old_golden"]["contacts_compared"] > 0 and got["equality_with_old_golden"]["point_contacts_edge_exempt"] == 0


def test_the_fixed_re_derivation_differs_from_the_old_golden_only_in_the_edges_and_the_final_slice_equals_it_byte_for_byte(rederive_world, final_world, measuring,
                                                                                                                      receipt, tmp_path):
    derived = _rederive(rederive_world, measuring, "fixed")
    vs_old = derived["equality_with_old_golden"]
    assert derived["build"]["defects"] == [] and vs_old["passed"], vs_old["problems"]
    assert not vs_old["strict_edges"] and vs_old["point_contacts_edge_exempt"] > 0 and vs_old["all_cells"]
    strict_vs_old = q.equality_proof(measuring, {"records": derived["bundle"]["records.jsonl"], "windows": derived["bundle"]["windows.jsonl"],
                                                 "contacts": derived["bundle"]["contacts.jsonl"]}, SLICE, strict_edges=True, all_cells=True)
    assert not strict_vs_old["passed"]                       # the fix moved edges: a byte-for-byte comparison with the OLD golden must fail (the detector reads false)
    mc.write_bundle(tmp_path / "rederived", derived["bundle"])
    got = _verdict(final_world, measuring, receipt, rederived=q.load_golden(tmp_path / "rederived"))
    assert got["verdict"] == q.QUALIFIED, got["reasons"]
    assert got["rederived_equality"]["passed"] and got["rederived_equality"]["strict_edges"] and got["rederived_equality"]["contacts_compared"] > 0


def test_a_planted_difference_in_the_re_derived_golden_fails_the_final_slice(rederive_world, final_world, measuring, receipt, tmp_path):
    derived = _rederive(rederive_world, measuring, "fixed")
    bundle = derived["bundle"]
    by_id = {c["contact_id"]: c for c in bundle["contacts.jsonl"]}
    compared = [by_id[q._contact_id_of(r)] for r in bundle["records.jsonl"] if q.cell_expectation(*q._cell(r))["kind"] == "same"
                and q._contact_id_of(r) in by_id and by_id[q._contact_id_of(r)]["canonical_target"].startswith("point:")]
    assert compared, "no point contact in an unchanged cell to plant the difference in"
    compared[0]["t_in"] = "2000-01-01T00:00:00+00:00"       # one edge a different instant, in a cell the equality proof compares: only a byte-for-byte comparison can see it
    got = _verdict(final_world, measuring, receipt, rederived={"records": bundle["records.jsonl"], "windows": bundle["windows.jsonl"],
                                                              "contacts": bundle["contacts.jsonl"]})
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert any(r.startswith("rederived_equality_") for r in got["reasons"])


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
