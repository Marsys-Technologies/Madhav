"""J-4d by slice (SR-BOLD-03): the qualification verdict, its class choice and its two proofs, with no database.

Every oracle plants ONE defect (or one omission) in an otherwise QUALIFIED run and requires the verdict to flip to FULL_BUILD_REQUIRED
for that defect's named reason. The golden is a real bundle in the J-3 capture format (measuring_capture.write_bundle / verify_bundle).
Doctrine behind the cells: ND-H-20261005 (the eight classes run P1/P3/P4 at 1.2.0), ND-P2-20261005 rule 3 (bereavement P3/P4), ND-H
item 5 (parental P2 emits no row under the final rules); every other cell keeps the measuring 1.0.0 selection (rule_registry.py).
"""
from __future__ import annotations

import copy
import json
from contextlib import contextmanager

import pytest

from scripts.kala_gochara_cutover import j4d_slice_qualify as q
from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import rule_registry as rr

SLICE = ["business_launch", "marriage", "parental_event"]
HORIZON = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
RECEIPT = ('{"head":"' + "a" * 40 + '","item":"P06b","merged_on_main":true,"mutation_verified":true,'
           '"review_job":"X-20261018T000000Z-test","step":"ephemeris_verifier_stage","verdict":"MET"}\n')
SPAN = [["2025-01-10T00:00:00+00:00", "2025-02-20T00:00:00+00:00"]]


def raw(event_class, path, version="1.0.0", *, contact=None, supports=SPAN):
    return dict(record_id=f"{event_class}-{path}-{version}", chart_id="c", generation="5.0", event_class=event_class, affected_person="native",
                frame_kind="lagna", frame_arg=None, agent="saturn", relation="residence", object_id="obj", object_role="signature_house",
                contact_id=contact or f"contact-{event_class}-{path}", path_id=path, rule_version=version, prerequisites=[["p", version]],
                source_text=None, period_anchor_lord=None, period_anchor_level=None, admission_state="admitted", operator_role="scored",
                temporal_support_intervals=supports)


def contact_row(contact_id, *, t_out="2025-02-20T00:00:00+00:00"):
    return {"contact_id": contact_id, "body": "saturn", "relation_kind": "residence", "canonical_target": "span:7",
            "t_in": "2025-01-10T00:00:00+00:00", "t_out": t_out, "t_exact": None, "delta_lambda": 0.0001}


def window_row(event_class, path, version="1.0.0", hi="2025-02-20T00:00:00+00:00"):
    return {"event_class": event_class, "path_id": path, "rule_version": version, "lo": "2025-01-10T00:00:00+00:00", "hi": hi}


def measuring_rows():
    """What the measuring build stored for the slice classes: every cell at 1.0.0."""
    records = [raw(c, p) for c in SLICE for p in ("P1", "P2", "P3", "P4")]
    contacts = [contact_row(r["contact_id"]) for r in records]
    windows = [window_row(c, p) for c in SLICE for p in ("P1", "P2", "P3", "P4")]
    return records, contacts, windows


def final_rows():
    """What a correct final-rules slice stores: unchanged cells equal to the golden, changed cells at their final version,
    the suppressed cell (parental P2) empty."""
    records, contacts, windows = [], [], []
    for cls in SLICE:
        for path in ("P1", "P2", "P3", "P4"):
            expect = q.cell_expectation(cls, path)
            if expect["kind"] == "suppressed":
                continue
            version = expect["final_version"]
            contact = f"contact-{cls}-{path}" if expect["kind"] == "same" else f"contact-{cls}-{path}-{version}"
            records.append(raw(cls, path, version, contact=contact))
            contacts.append(contact_row(contact))
            windows.append(window_row(cls, path, version))
    return records, contacts, windows


@pytest.fixture()
def golden(tmp_path):
    records, contacts, windows = measuring_rows()
    bundle = mc.make_bundle(binding={"chart_id": "c", "generation": "5.0", "run_id": "run", "manifest_id": "m", "source_commit": "b" * 40},
                            contacts=contacts, records=records, windows=windows, horizon_basis={"schema": "x/1"}, stretch_sink=[],
                            informational={"horizon": HORIZON, "input_vector": {}})
    mc.write_bundle(tmp_path / "golden", bundle)
    return q.load_golden(tmp_path / "golden")


@pytest.fixture()
def receipt(tmp_path):
    path = tmp_path / "P06b.ephemeris_verifier_stage.json"
    path.write_text(RECEIPT, encoding="utf-8")
    return path


def sliced_state(records=None, contacts=None, windows=None):
    fr, fc, fw = final_rows()
    return {"records": [mc.golden_record(r) for r in (fr if records is None else records)],
            "contacts": [mc._plain(c) for c in (fc if contacts is None else contacts)],
            "windows": [mc._plain(w) for w in (fw if windows is None else windows)]}


def run_verdict(golden, receipt, sliced=None, *, build=None, p06b=None):
    return q.verdict(choice={"classes": SLICE, "heaviest": "marriage", "source": "explicit", "costs": None}, golden=golden,
                     build=build or {"steps": [{"step": "x", "rows": 1}], "defects": []}, sliced=sliced or sliced_state(),
                     p06b=q.p06b_complete(receipt) if p06b is None else p06b)


# ── the cell doctrine ────────────────────────────────────────────────────────────────────────────────────────────

def test_cells_follow_nd_h_nd_p2_and_the_parental_suppression():
    assert q.cell_expectation("business_launch", "P1") == {"kind": "final", "measuring_version": "1.0.0", "final_version": "1.2.0"}
    assert q.cell_expectation("business_launch", "P2")["kind"] == "same"
    assert [q.cell_expectation("bereavement", p)["kind"] for p in ("P1", "P2", "P3", "P4")] == ["same", "same", "final", "final"]
    assert q.cell_expectation("parental_event", "P2")["kind"] == "suppressed"
    assert all(q.cell_expectation("marriage", p)["kind"] == "same" for p in ("P1", "P2", "P3", "P4"))
    assert q.is_unchanged_class("marriage") and not q.is_unchanged_class("business_launch")


# ── class choice ─────────────────────────────────────────────────────────────────────────────────────────────────

def timings(by_class_substep):
    return {"timings": {"run_seconds": 1, "asset_seconds": 1, "by_phase": {"records": 1}, "by_class_substep": by_class_substep}}


def test_the_heaviest_class_is_the_per_class_sum_not_the_single_longest_substep():
    doc = timings({**{f"marriage:record:P{i}": 50 for i in range(1, 5)}, "surgery:record": 120, "relocation:verify": 10})
    assert q.class_costs(doc)["marriage"] == 200
    assert q.choose_slice(timings=doc)["heaviest"] == "marriage"          # a longest-single-substep rule would name surgery


def test_the_costliest_three_are_chosen_and_a_report_draft_is_read_like_the_observations():
    doc = timings({"marriage:record": 90, "surgery:record": 80, "relocation:record": 70, "separation:record": 60})
    draft = {"numbers": {"1": {"data": doc["timings"]}}}
    for source in (doc, draft):
        got = q.choose_slice(timings=source)
        assert got["classes"] == ["marriage", "relocation", "surgery"] and got["heaviest"] == "marriage" and got["source"] == "timings"


def test_a_slice_of_only_changed_classes_gets_the_costliest_unchanged_class_instead_of_its_third():
    doc = timings({"business_launch:record": 90, "spiritual_turn:record": 80, "foreign_settlement:record": 70, "marriage:record": 60, "surgery:record": 50})
    got = q.choose_slice(timings=doc)
    assert got["classes"] == ["business_launch", "marriage", "spiritual_turn"]      # heaviest kept; marriage replaces the third pick


def test_explicit_classes_are_three_distinct_scored_classes_and_hold_the_heaviest_when_timings_exist():
    assert q.choose_slice(classes=SLICE)["classes"] == SLICE
    for bad in (SLICE[:2], SLICE + ["surgery"], ["marriage", "marriage", "surgery"], ["marriage", "surgery", "not_a_class"]):
        with pytest.raises(q.SliceRefused):
            q.choose_slice(classes=bad)
    doc = timings({"surgery:record": 90, "marriage:record": 5})
    with pytest.raises(q.SliceRefused, match="slice_misses_heaviest_class"):
        q.choose_slice(timings=doc, classes=SLICE)
    with pytest.raises(q.SliceRefused):
        q.choose_slice()


@pytest.mark.parametrize("doc", [{}, {"timings": {"by_class_substep": {}}}, timings({"nothing_named": 1}), timings({"marriage:record": -1})])
def test_unreadable_timings_are_refused_not_guessed(doc):
    with pytest.raises(q.SliceRefused):
        q.class_costs(doc)


# ── the golden ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_tampered_golden_is_refused_before_any_comparison(tmp_path, golden):
    (tmp_path / "golden" / "records.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(mc.CaptureRefused, match="golden_digest_mismatch"):
        q.load_golden(tmp_path / "golden")


# ── the verdict ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_correct_final_slice_with_p06b_complete_is_qualified(golden, receipt):
    got = run_verdict(golden, receipt)
    assert got["verdict"] == q.QUALIFIED and got["reasons"] == []
    assert got["equality"]["passed"] and got["noninterference"]["passed"] and got["independent_acceptance"] is None
    compared = {(c["event_class"], c["path_id"]) for c in got["equality"]["cells"]}
    assert ("marriage", "P3") in compared and ("business_launch", "P2") in compared and ("business_launch", "P1") not in compared
    assert got["cannot_establish"]


def test_a_planted_support_shift_in_one_slice_class_fails_equality_and_flips_the_verdict(golden, receipt):
    records, _, _ = final_rows()
    planted = copy.deepcopy(records)
    victim = next(r for r in planted if r["event_class"] == "marriage" and r["path_id"] == "P3")
    victim["temporal_support_intervals"] = [["2025-01-10T00:00:01+00:00", "2025-02-20T00:00:00+00:00"]]
    got = run_verdict(golden, receipt, sliced_state(records=planted))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == ["equality_records_differ: marriage/P3"]
    assert got["equality"]["passed"] is False and got["noninterference"]["passed"]


def test_a_planted_window_end_shift_fails_equality(golden, receipt):
    _, _, windows = final_rows()
    planted = copy.deepcopy(windows)
    next(w for w in planted if w["event_class"] == "business_launch" and w["path_id"] == "P2")["hi"] = "2025-02-21T00:00:00+00:00"
    got = run_verdict(golden, receipt, sliced_state(windows=planted))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == ["equality_windows_differ: business_launch/P2"]


def test_a_planted_contact_difference_fails_equality(golden, receipt):
    _, contacts, _ = final_rows()
    planted = copy.deepcopy(contacts)
    next(c for c in planted if c["contact_id"] == "contact-marriage-P1")["t_out"] = "2025-02-21T00:00:00+00:00"
    got = run_verdict(golden, receipt, sliced_state(contacts=planted))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == ["equality_contact_differs: contact-marriage-P1"]


def test_a_changed_cell_is_allowed_to_differ_from_the_golden_but_not_to_keep_the_measuring_version(golden, receipt):
    records, _, _ = final_rows()
    leaked = copy.deepcopy(records)
    victim = next(r for r in leaked if r["event_class"] == "business_launch" and r["path_id"] == "P3")
    victim["rule_version"] = "1.0.0"
    got = run_verdict(golden, receipt, sliced_state(records=leaked))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert got["reasons"] == ["noninterference_wrong_rule_version: business_launch/P3 carries 1.0.0, final is 1.2.0"]
    assert got["equality"]["passed"]          # the changed cell is not an equality cell


def test_a_row_in_the_suppressed_parental_p2_cell_fails_noninterference(golden, receipt):
    records, contacts, _ = final_rows()
    got = run_verdict(golden, receipt, sliced_state(records=records + [raw("parental_event", "P2")], contacts=contacts + [contact_row("contact-parental_event-P2")]))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert "noninterference_suppressed_cell_not_empty: parental_event/P2 (1 rows)" in got["reasons"]


def test_a_record_of_a_class_outside_the_slice_fails_noninterference(golden, receipt):
    records, _, _ = final_rows()
    got = run_verdict(golden, receipt, sliced_state(records=records + [raw("surgery", "P1")]))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and "noninterference_class_outside_slice: ['surgery']" in got["reasons"]


def test_a_proof_that_compared_nothing_is_not_green(golden, receipt):
    got = run_verdict(golden, receipt, sliced_state(records=[], contacts=[], windows=[]))
    assert got["verdict"] == q.FULL_BUILD_REQUIRED
    assert "equality_records_differ: marriage/P1" in got["reasons"]
    empty = {"records": [], "windows": [], "contacts": []}
    assert any(p.startswith("equality_vacuous") for p in q.equality_proof({**golden, "records": [], "windows": [], "contacts": []}, empty, SLICE)["problems"])


def test_the_default_profile_detector_reads_false_inside_the_final_context_and_noninterference_reports_it():
    assert q.default_profile_intact() is True
    with rr.rule_profile(final_rules=True):
        assert q.default_profile_intact() is False
    assert q.noninterference_proof({"records": []}, SLICE, default_profile_intact=False)["problems"] == ["noninterference_default_profile_changed"]


@pytest.mark.parametrize("text,reason", [(None, "p06b_receipt_missing"), ("{}\n", "p06b_receipt_malformed"),
                                         (RECEIPT.replace('"verdict":"MET"', '"verdict":"UNMET"'), "p06b_receipt_malformed"),
                                         (RECEIPT.replace('"mutation_verified":true', '"mutation_verified":false'), "p06b_receipt_malformed")])
def test_p06b_incomplete_means_full_build(golden, tmp_path, text, reason):
    path = tmp_path / "missing.json"
    if text is not None:
        path.write_text(text, encoding="utf-8")
    got = run_verdict(golden, path)
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == [reason] and got["p06b"] == {"complete": False, "reason": reason}


def test_any_build_defect_means_full_build(golden, receipt):
    defect = {"step": "record:marriage:P3", "defect": "substep_raised", "detail": "ValueError: boom"}
    got = run_verdict(golden, receipt, build={"steps": [], "defects": [defect]})
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == ["build_defect: record:marriage:P3: substep_raised: ValueError: boom"]
    empty = run_verdict(golden, receipt, build={"steps": [], "defects": []})
    assert empty["verdict"] == q.FULL_BUILD_REQUIRED and "build_empty: no substep ran" in empty["reasons"]


# ── the build driver and the lane guard ──────────────────────────────────────────────────────────────────────────

class _Conn:
    def __init__(self, name="ky_lane_x", addr="127.0.0.1/32", port=55433):
        self.row = (name, addr, port)

    def execute(self, sql, params=None):
        outer = self

        class _Cur:
            def fetchone(self):
                return outer.row
        return _Cur()

    @contextmanager
    def transaction(self):
        yield


@pytest.mark.parametrize("row", [("postgres", "127.0.0.1/32", 55433), ("ky_lane_x", "10.0.0.4/32", 55433), ("ky_lane_x", "127.0.0.1/32", 5433),
                                 ("ky_lane_x", "34.1.2.3/32", 55433)])
def test_only_the_local_lane_cluster_is_accepted(row):
    with pytest.raises(q.SliceRefused):
        q.require_lane(_Conn(*row))
    q.require_lane(_Conn())
    q.require_lane(_Conn("a53t_j4d_1234abcd", None))


class _Result:
    def __init__(self, notes=""):
        self.rows_inserted, self.notes = 1, notes


def _stub_writer(monkeypatch, behaviour):
    from pipeline.orchestrator.writers import SubStep, ka_gochara_v5 as writer_mod
    seen = []

    class Writer:
        def plan_substeps(self, ctx):
            assert ctx.config["gochara_v5_final_rules"] is True
            return [SubStep(key=k, label=k) for k in ("rules", "convention", "manifest", "snapshot", "inventory:marriage", "record:marriage:P1",
                                                      "record:surgery:P1", "verify:marriage")]

        def run_substep(self, ctx, step):
            seen.append(step.key)
            return behaviour(step.key)
    monkeypatch.setattr(writer_mod, "GocharaV5Writer", Writer)
    return seen


def test_the_build_runs_only_the_slice_classes_and_the_class_less_head_under_the_final_rules(monkeypatch):
    seen = _stub_writer(monkeypatch, lambda key: _Result())
    got = q.build_slice(_Conn(), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x")
    assert got["defects"] == [] and seen == ["rules", "convention", "manifest", "snapshot", "inventory:marriage", "record:marriage:P1", "verify:marriage"]


def test_a_raised_substep_stops_the_build_and_is_a_named_defect(monkeypatch):
    def behave(key):
        if key == "inventory:marriage":
            raise RuntimeError("boom")
        return _Result()
    seen = _stub_writer(monkeypatch, behave)
    got = q.build_slice(_Conn(), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x")
    assert got["defects"] == [{"step": "inventory:marriage", "defect": "substep_raised", "detail": "RuntimeError: boom"}]
    assert seen[-1] == "inventory:marriage"


def test_an_unverified_outcome_is_a_defect_even_though_nothing_raised(monkeypatch):
    _stub_writer(monkeypatch, lambda key: _Result("class marriage UNVERIFIED: tier unavailable" if key.startswith("verify:") else ""))
    got = q.build_slice(_Conn(), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x")
    assert [d["defect"] for d in got["defects"]] == ["unverified"] and got["defects"][0]["step"] == "verify:marriage"


def test_the_build_refuses_a_database_that_is_not_the_lane_before_any_substep(monkeypatch):
    seen = _stub_writer(monkeypatch, lambda key: _Result())
    with pytest.raises(q.SliceRefused):
        q.build_slice(_Conn("production", "127.0.0.1/32", 5433), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x")
    assert seen == []


class _LaneWithoutNearMissStorage:
    """A lane connection whose catalog never gains the near-miss tables, whatever is executed (the migration 'did not take')."""

    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append(sql)
        outer = self

        class _Cur:
            def fetchone(self):
                return ("ky_lane_x", "127.0.0.1/32", 55433) if "current_database" in sql else (False,)
        return _Cur()

    @contextmanager
    def transaction(self):
        yield


def test_the_near_miss_layer_is_applied_from_the_real_migration_and_a_lane_where_it_does_not_take_is_refused():
    """J-4d pre-run F2: the layer must be PROVEN present (the writer's own presence test) after the migration, or the harness refuses by name."""
    conn = _LaneWithoutNearMissStorage()
    with pytest.raises(q.SliceRefused, match="near_miss_layer_not_applied"):
        q.ensure_near_miss_layer(conn)
    assert any("ka_gochara_near_miss_search" in sql and "CREATE TABLE" in sql.upper() for sql in conn.executed)       # the real 1308 file was run
    assert q.NEAR_MISS_MIGRATION.name == "1308_gochara_near_miss_storage.sql" and q.NEAR_MISS_MIGRATION.exists()


# ── command line ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_choose_prints_the_slice_and_a_bad_slice_exits_2(capsys, tmp_path):
    path = tmp_path / "obs.json"
    path.write_text(json.dumps(timings({"marriage:record": 9, "surgery:record": 8, "relocation:record": 7})), encoding="utf-8")
    assert q.main(["choose", "--timings", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["classes"] == ["marriage", "relocation", "surgery"]
    assert q.main(["choose", "--classes", "marriage,surgery"]) == 2
    assert "REFUSED: slice_not_three_distinct_classes" in capsys.readouterr().err
