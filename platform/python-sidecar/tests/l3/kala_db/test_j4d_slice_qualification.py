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


PASSING = {"passed": True, "problems": []}


def run_verdict(golden, receipt, sliced=None, *, build=None, p06b=None, **sections):
    """The proofs this module does not exercise (tolerance, solver isolation, certification, peak windows) are supplied as PASSING stubs so each test here
    plants exactly one defect; their own oracles are in tests/l3/gochara/test_j4d_edge_proofs.py and below."""
    sections = {"tolerance": PASSING, "isolation": PASSING, "certification": PASSING, "peak_windows": PASSING, **sections}
    return q.verdict(choice={"classes": SLICE, "heaviest": "marriage", "source": "explicit", "costs": None}, golden=golden,
                     build=build or {"steps": [{"step": "x", "rows": 1}], "defects": []}, sliced=sliced or sliced_state(),
                     p06b=q.p06b_complete(receipt) if p06b is None else p06b, **sections)


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


# ═══ SR-EDGES-PROOF (a): the equality proof compares every field EXCEPT the minted point-contact edges ═══════════════
#
# The reference for the cells below is the record store itself: a point-contact record's support is `(occ.t_in, occ.t_out)` clipped by the record's periods
# (record_store.py `raw_support = (occ.t_in, occ.t_out)`), a window's interval is the union of its records' supports, and a contact's identity is
# `body|relation|target|convention|ordinal` hashed (substrate.py header: ordinals are assigned over the t_exact-ordered crossing set, ids never hash a time).
# So when the fixed solver moves `t_in` / `t_out`, the support and window endpoints that ARE those edges move with them and nothing else may.
# The targets are SYNTHETIC ray levels; no chart's natal point is used.

from datetime import datetime, timedelta, timezone

T_IN0, T_OUT0 = datetime(2025, 1, 10, tzinfo=timezone.utc), datetime(2025, 2, 20, tzinfo=timezone.utc)
CUT_A, CUT_B = "2025-01-25T00:00:00+00:00", "2025-02-01T00:00:00+00:00"        # dasha-style cuts inside the contact: NOT contact edges
MARRIAGE = ["marriage"]


def _iso(t):
    return t.isoformat()


def point_contact(contact_id, *, shift=0, t_exact="2025-01-30T12:00:00+00:00", delta=0.000278, target="point:123.456"):
    return {"contact_id": contact_id, "body": "jupiter", "relation_kind": "aspect", "canonical_target": target,
            "t_in": _iso(T_IN0 + timedelta(seconds=shift)), "t_out": _iso(T_OUT0 - timedelta(seconds=shift)), "t_exact": t_exact, "delta_lambda": delta}


def point_state(*, shift=0, contact_ids=None, cut_shift=0, window_hi_shift=0, t_exacts=None):
    """marriage P1..P4, one record per path over its own point contact (or the given ids, all in P1 for the count / ordinal oracles); `shift` seconds
    moves each contact's t_in / t_out and the support / window endpoints that are those edges."""
    ids = contact_ids or {path: f"pt-marriage-{path}" for path in ("P1", "P2", "P3", "P4")}
    records, contacts, windows = [], [], []
    for n, (path, contact_id) in enumerate(ids.items() if isinstance(ids, dict) else [("P1", i) for i in ids]):
        contact = point_contact(contact_id, shift=shift, t_exact=(t_exacts or {}).get(contact_id, "2025-01-30T12:00:00+00:00"),
                                target=f"point:{100 + n}.5" if contact_ids is None else "point:123.456")        # one physical object per path; the occurrence oracles share one
        contacts.append(contact)
        cut_a = (datetime.fromisoformat(CUT_A) + timedelta(seconds=cut_shift)).isoformat()
        records.append(raw("marriage", path, contact=contact_id,
                           supports=[[contact["t_in"], cut_a], [CUT_B, contact["t_out"]]]))
    for path in sorted({r["path_id"] for r in records}):
        windows.append({"event_class": "marriage", "path_id": path, "rule_version": "1.0.0",
                        "lo": _iso(T_IN0 + timedelta(seconds=shift)), "hi": _iso(T_OUT0 - timedelta(seconds=shift) + timedelta(seconds=window_hi_shift))})
    return {"records": [mc.golden_record(r) for r in records], "contacts": [mc._plain(c) for c in contacts], "windows": [mc._plain(w) for w in windows]}


def test_moved_point_edges_and_the_endpoints_that_are_those_edges_do_not_fail_equality_but_nothing_else_may_move():
    golden, moved = point_state(), point_state(shift=90)
    got = q.equality_proof(golden, moved, MARRIAGE)
    assert got["passed"], got["problems"]
    assert got["point_contacts_edge_exempt"] == 4 and got["contacts_compared"] == 4
    assert q.edge_moves({c["contact_id"]: c for c in golden["contacts"]}, {c["contact_id"]: c for c in moved["contacts"]}) == \
        {"edges": 8, "moved": 8, "median_seconds": 90.0, "max_seconds": 90.0}
    # the control: with the edge exemption reverted (the old byte-for-byte comparison, also the re-derived-golden comparison) the very same slice fails
    strict = q.equality_proof(golden, moved, MARRIAGE, strict_edges=True)
    assert not strict["passed"] and "equality_contact_differs: pt-marriage-P1" in strict["problems"] and "equality_records_differ: marriage/P1" in strict["problems"]


def test_the_re_derived_comparison_is_byte_for_byte_edges_included():
    assert q.equality_proof(point_state(shift=90), point_state(shift=90), MARRIAGE, strict_edges=True)["passed"]


@pytest.mark.parametrize("planted,expect", [
    (dict(t_exacts={"pt-marriage-P3": "2025-01-30T12:00:01+00:00"}), ["equality_t_exact_differs: pt-marriage-P3"]),          # t_exact must stay bit-identical
    (dict(cut_shift=1), ["equality_records_differ: marriage/P1", "equality_records_differ: marriage/P2", "equality_records_differ: marriage/P3",
                         "equality_records_differ: marriage/P4"]),                                          # a support endpoint that is NOT an edge (a period cut) stays exact
    (dict(window_hi_shift=1), ["equality_windows_differ: marriage/P1", "equality_windows_differ: marriage/P2", "equality_windows_differ: marriage/P3",
                               "equality_windows_differ: marriage/P4"]),                                    # a window end that is NOT a contact edge stays exact
])
def test_one_planted_non_edge_difference_fails_equality_under_moved_edges(planted, expect):
    got = q.equality_proof(point_state(), point_state(shift=90, **planted), MARRIAGE)
    assert not got["passed"] and got["problems"] == expect


def test_a_changed_delta_lambda_or_target_is_not_an_edge_and_fails_equality():
    golden, other = point_state(), point_state(shift=90)
    other["contacts"][1]["delta_lambda"] = 0.0005
    assert q.equality_proof(golden, other, MARRIAGE)["problems"] == ["equality_contact_differs: pt-marriage-P2"]


def test_a_different_contact_id_in_a_record_fails_equality_by_id():
    golden, other = point_state(), point_state(shift=90)
    renamed = copy.deepcopy(other)
    renamed["contacts"][0]["contact_id"] = "pt-marriage-P1-renamed"
    key = json.loads(renamed["records"][0]["gkey"])
    key["contact_id"] = "pt-marriage-P1-renamed"
    renamed["records"][0]["gkey"] = mc.canonical(key)
    got = q.equality_proof(golden, renamed, MARRIAGE)
    assert "equality_records_differ: marriage/P1" in got["problems"] and "equality_contact_missing_in_slice: pt-marriage-P1" in got["problems"]


def test_a_dropped_occurrence_fails_the_per_obligation_count():
    both = ["pt-a", "pt-b"]
    golden = point_state(contact_ids=both, t_exacts={"pt-a": "2025-01-20T00:00:00+00:00", "pt-b": "2025-02-10T00:00:00+00:00"})
    slice_ = point_state(contact_ids=["pt-a"], t_exacts={"pt-a": "2025-01-20T00:00:00+00:00"})
    problems = q.equality_proof(golden, slice_, MARRIAGE)["problems"]
    assert any(p.startswith("equality_contact_count_differs") and p.endswith("(2 vs 1)") for p in problems)


def test_occurrence_ids_out_of_t_exact_order_fail_the_ordinal_sequence():
    first, second = "2025-01-20T00:00:00+00:00", "2025-02-10T00:00:00+00:00"
    golden = point_state(contact_ids=["pt-a", "pt-b"], t_exacts={"pt-a": first, "pt-b": second})
    swapped = point_state(contact_ids=["pt-a", "pt-b"], t_exacts={"pt-a": second, "pt-b": first})
    problems = q.equality_proof(golden, swapped, MARRIAGE)["problems"]
    assert any(p.startswith("equality_ordinals_differ") for p in problems) and "equality_t_exact_differs: pt-a" in problems


def test_a_span_contact_keeps_its_ingress_edges_bit_for_bit(golden, receipt):
    """Residence / span contacts take their edges from the sign-ingress substrate, which the edge fix does not touch: moving one is NOT exempt."""
    _, contacts, _ = final_rows()
    planted = copy.deepcopy(contacts)
    next(c for c in planted if c["contact_id"] == "contact-marriage-P1")["t_in"] = "2025-01-10T00:00:01+00:00"
    got = run_verdict(golden, receipt, sliced_state(contacts=planted))
    assert got["reasons"] == ["equality_contact_differs: contact-marriage-P1"]


# ── the verdict requires every proof ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", ["tolerance", "solver_isolation", "certification", "peak_windows"])
def test_a_proof_that_was_not_run_is_a_reason_not_a_pass(golden, receipt, name):
    key = {"solver_isolation": "isolation"}.get(name, name)
    sections = {"tolerance": PASSING, "isolation": PASSING, "certification": PASSING, "peak_windows": PASSING, key: None}
    got = q.verdict(choice={"classes": SLICE, "heaviest": None, "source": "explicit", "costs": None}, golden=golden,
                    build={"steps": [{"step": "x", "rows": 1}], "defects": []}, sliced=sliced_state(), p06b=q.p06b_complete(receipt), **sections)
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == [f"{name}_proof_not_run"]


@pytest.mark.parametrize("section", ["tolerance", "isolation", "certification", "peak_windows"])
def test_a_failing_proof_section_flips_the_verdict_with_its_own_reason(golden, receipt, section):
    got = run_verdict(golden, receipt, **{section: {"passed": False, "problems": [f"{section}_planted"]}})
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == [f"{section}_planted"]


def test_a_re_derived_golden_must_equal_the_slice_byte_for_byte_when_supplied(golden, receipt):
    ok = run_verdict(golden, receipt, rederived={**golden, "records": golden["records"], "windows": golden["windows"], "contacts": golden["contacts"]})
    assert ok["verdict"] == q.QUALIFIED and ok["rederived_equality"]["passed"] and ok["rederived_equality"]["strict_edges"]
    off = copy.deepcopy(golden)
    next(c for c in off["contacts"] if c["contact_id"] == "contact-marriage-P1")["t_out"] = "2025-02-20T00:00:01+00:00"
    got = run_verdict(golden, receipt, rederived=off)
    assert got["verdict"] == q.FULL_BUILD_REQUIRED and got["reasons"] == ["rederived_equality_contact_differs: contact-marriage-P1"]
    assert not any("re-derived" in line for line in ok["cannot_establish"]) and any("re-derived" in line for line in run_verdict(golden, receipt)["cannot_establish"])


# ── the ruled slice (SR-EDGES-PROOF) ────────────────────────────────────────────────────────────────────────────────

def test_the_ruled_slice_is_chronic_onset_illness_acute_major_loss_and_bereavement_with_something_to_compare():
    got = q.choose_slice(ruled=True)
    assert got["classes"] == ["bereavement", "chronic_onset", "illness_acute", "major_loss"] and got["source"] == "SR-EDGES-PROOF"
    assert any(q.cell_expectation(c, p)["kind"] == "same" for c in got["classes"] for p in ("P1", "P2", "P3", "P4"))       # the equality proof is not vacuous
    surgery = q.choose_slice(ruled=True, classes=["bereavement", "chronic_onset", "surgery", "major_loss"])
    assert "surgery" in surgery["classes"]
    heavy = q.choose_slice(ruled=True, timings=timings({"marriage:record": 99, "surgery:record": 1}))
    assert heavy["heaviest"] == "marriage" and "marriage" not in heavy["classes"]          # the ruling names the classes; timing does not override it
    with pytest.raises(q.SliceRefused):
        q.choose_slice(ruled=True, classes=["marriage", "surgery"])


def test_the_command_line_names_the_ruled_slice(capsys):
    assert q.main(["choose", "--ruled-slice"]) == 0
    assert json.loads(capsys.readouterr().out)["classes"] == list(q.RULED_SLICE_CLASSES)


# ── certification under the STRICT policy: 0 invented / 0 anomaly (D-CLOUD C-7 / C-11) ───────────────────────────────

from services.gochara_kernel import contact_certify as cc

CLEAN = {"per_class": {"chronic_onset": {"stretches": 5, "invented": 0, "anomaly": 0, "by_kind": {"contact": 5}}}, "unavailable": {}}


def test_certification_is_strict_and_counts_zero_invented_zero_anomaly():
    got = q.certification_proof({"certification_policies": [cc.POLICY_RAISE, cc.POLICY_RAISE]}, CLEAN)
    assert got["passed"] and got["policy"] == cc.POLICY_RAISE and got["invented"] == 0 and got["anomaly"] == 0 and got["certification_calls"] == 2


@pytest.mark.parametrize("observed,measured,problem", [
    ({"certification_policies": [cc.POLICY_RAISE, cc.POLICY_SINK_ALL]}, CLEAN, "certification_not_strict: observed policies ['raise', 'sink_all']"),
    ({"certification_policies": []}, CLEAN, "certification_not_observed: the build made no certification call"),
    ({"certification_policies": [cc.POLICY_RAISE]}, None, "certification_not_measured: no independent collect-all pass over the built slice"),
    ({"certification_policies": [cc.POLICY_RAISE]}, {"per_class": {"x": {"stretches": 3, "invented": 1, "anomaly": 0, "by_kind": {}}}, "unavailable": {}}, "certification_invented: 1"),
    ({"certification_policies": [cc.POLICY_RAISE]}, {"per_class": {"x": {"stretches": 3, "invented": 0, "anomaly": 2, "by_kind": {}}}, "unavailable": {}}, "certification_anomaly: 2"),
    ({"certification_policies": [cc.POLICY_RAISE]}, {"per_class": {}, "unavailable": {"x": "Unverifiable: no inventory"}},
     "certification_class_unavailable: x: Unverifiable: no inventory"),
    ({"certification_policies": [cc.POLICY_RAISE]}, {"per_class": {}, "unavailable": {}}, "certification_vacuous: no class was certified"),
])
def test_each_certification_claim_reads_false_when_its_one_condition_is_planted(observed, measured, problem):
    got = q.certification_proof(observed, measured)
    assert not got["passed"] and got["problems"] == [problem]


def test_the_build_observer_records_the_policy_at_the_call_and_restores_the_module(monkeypatch):
    from services.gochara_kernel import window_sweep as ws
    calls = []
    monkeypatch.setattr(cc, "certify_contact_geometry", lambda *a, **k: calls.append(k) or {"obligations_certified": 0})
    monkeypatch.setattr(ws, "maximise_earliest", lambda *a, **k: None)
    stubbed = (cc.certify_contact_geometry, ws.maximise_earliest)
    with q.observe_build() as seen:
        cc.certify_contact_geometry(None, sink_policy=cc.POLICY_SINK_ALL)
        cc.certify_contact_geometry(None)                                                 # the default is the strict policy
        ws.maximise_earliest(None, None, None)
    assert seen == {"certification_policies": [cc.POLICY_SINK_ALL, cc.POLICY_RAISE], "maximise_earliest_calls": 1}
    assert (cc.certify_contact_geometry, ws.maximise_earliest) == stubbed and len(calls) == 2


def test_count_certification_reads_the_certifier_kinds():
    got = q.count_certification([{"kind": "contact"}, {"kind": "invented"}, {"kind": "anomaly"}, {"kind": "anomaly"}, {"kind": "near_miss"}])
    assert (got["stretches"], got["invented"], got["anomaly"]) == (5, 1, 2)


# ── the peak-windows row (SR-A53-NARROW 4) ──────────────────────────────────────────────────────────────────────────

class _PeakConn:
    def __init__(self, policy, with_peak, windows=7):
        self.policy, self.with_peak, self.windows = policy, with_peak, windows

    def execute(self, sql, params=None):
        outer = self

        class _Cur:
            def fetchone(self):
                if "input_generation_vector" in sql:
                    return None if outer.policy is None else (outer.policy,)
                return (outer.with_peak,) if "peak_instant IS NOT NULL" in sql else (outer.windows,)
        return _Cur()


QUALIFICATION, ALL_NULL = "window_qualification/1", "all_null_candidate/1"


def _row(policy, with_peak, edges):
    return q.peak_windows_row(_PeakConn(policy, with_peak), chart_id="c", classes=["marriage"], observed={"maximise_earliest_calls": edges})


def test_peak_windows_and_maximise_earliest_edges_must_both_be_positive_where_the_policy_admits_peaks():
    ok = _row(QUALIFICATION, 4, 9)
    assert ok["passed"] and ok["admitted"] and ok["windows_with_peak_fields_set"] == 4 and ok["maximise_earliest_edges"] == 9
    assert _row(QUALIFICATION, 0, 9)["problems"][0].startswith("peak_windows_zero")             # 0 is a defect, not a pass
    assert _row(QUALIFICATION, 4, 0)["problems"][0].startswith("maximise_earliest_edges_zero")


def test_under_the_all_null_policy_no_peak_is_admitted_and_one_that_appears_is_a_defect():
    quiet = _row(ALL_NULL, 0, 0)
    assert quiet["passed"] and quiet["admitted"] is False and quiet["result_policy"] == ALL_NULL        # reported, not asserted green as a peak measurement
    assert _row(ALL_NULL, 2, 0)["problems"] == [f"peak_present_under_{ALL_NULL}: 2 window(s) carry a peak field"]


def test_an_unreadable_policy_is_a_named_problem_not_a_guess():
    got = _row(None, 0, 0)
    assert not got["passed"] and got["result_policy"] is None and got["problems"][0].startswith("peak_policy_unreadable")
