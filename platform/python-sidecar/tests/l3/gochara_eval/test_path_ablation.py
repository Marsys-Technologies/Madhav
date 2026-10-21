"""J-5q: the six per-path ablation runs of a governed generation (FIXTURE tests; no stored chart value is read, and nothing here is a measurement).

The protocol (v2.3 §10) makes per-path ablations a mandatory NON-GATING disclosure and names no procedure; the procedure implemented is
leave-one-path-out over the stored windows (path_ablation.py, (I) INTERPRETATION). Oracles are therefore the protocol's own endpoint definitions on
a hand-checkable fixture: removing the only window that contains a held-out event must drop T-cover by exactly that event (§6.1), and removing
a window that holds no held-out event must change no endpoint.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from services.gochara_eval import dump_extract as dx
from services.gochara_eval import path_ablation as pa
from services.gochara_eval import qualification_report as report
from services.gochara_eval import load_registry
from services.gochara_eval.candidate import load_candidate_extract_bytes, score_candidate
from services.gochara_eval.candidate_score import run
from services.gochara_eval.controls import CONTROLS_SEED, draw_controls
from services.gochara_eval.freeze import sha256_file

from .conftest import synth_registry, write_json
from .test_freeze_and_dump import CHART_ID, INPUT_FILES, OUT
from .test_governed_5_0 import governed_stage1

WHY = "dynamic_objective_solver_guarantee_not_available"


def row(cls, path, ws, we, pk, si, valence="favourable", reason=None):
    return {"event_class": cls, "ws": ws, "we": we, "pk": pk, "si": si, "outcome_valence_for_native": valence, "path_id": path, "null_reason": reason}


# FIXTURE rows against the synthetic registry (held-out: career_advancement exact 2010-05-20; relocation, year 2015). P5 and P6 built nothing.
ROWS = [
    row("career_advancement", "P3", "2010-04-01", "2010-07-01", "2010-05-20", 0.9),
    row("relocation", "P4", "2015-03-01", "2015-04-01", "2015-03-10", 0.5),
    row("relocation", "P1", "2015-09-01", "2015-10-01", None, None, "unqualified", WHY),
    row("marriage", "P2", "2012-01-01", "2012-02-01", "2012-01-09", 0.4),
]


def extract_bytes(rows=ROWS) -> bytes:
    return dx.render("5.0", "2026-10-21", copy.deepcopy(rows), chart_id=CHART_ID)


@pytest.fixture()
def registry(tmp_path):
    return load_registry(write_json(tmp_path / "registry.json", synth_registry()))


def hits(rec):
    return rec["figures"]["t_cover"]["hits"]


class TestLeaveOnePathOut:
    def test_removing_the_only_window_that_contains_a_held_out_event_drops_t_cover_by_exactly_that_event(self, registry):
        out = pa.run_ablations(registry, extract_bytes())
        assert out["base"]["figures"]["t_cover"]["hits"] == 2
        p3 = out["paths"]["P3"]
        assert p3["status"] == "MEASURED" and p3["rows_removed"] == 1 and p3["rows_remaining"] == 3
        assert hits(p3) == 1 and p3["delta_vs_full"]["t_cover"]["hits"] == -1
        # the exact-date event is no longer hit, so T-time reads the cap for it: the capped median moves from the 10-day-or-less error to the cap
        assert p3["delta_vs_full"]["t_time"]["median_hi"] > 0

    def test_removing_a_path_that_holds_no_held_out_event_leaves_the_event_endpoints_alone_and_moves_only_the_false_positive_burden(self, registry):
        """The marriage window holds no held-out event: T-cover, T-time, T-rank and T-honesty read the events and cannot move. T-FP (§6.4) counts every
        admitted day of a class against its budget, so it MAY move — here the class's burden falls out of the gain band, and the record says so."""
        p2 = pa.run_ablations(registry, extract_bytes())["paths"]["P2"]
        assert p2["status"] == "MEASURED" and p2["rows_removed"] == 1
        d = p2["delta_vs_full"]
        assert d["t_cover"]["hits"] == 0 and d["t_time"]["median_hi"] == 0
        assert all(v["changed"] is False for ep in ("t_cover", "t_time", "t_rank", "t_honesty") for k, v in d[ep].items() if k in ("pass", "status"))
        assert d["t_fp_overall"]["pass"] == {"full": False, "ablated": True, "changed": True}

    def test_removing_the_path_that_built_the_unknown_competitor_removes_the_unknown(self, registry):
        """SI addendum §4: an unknown-si window is a competitor with an unknown rank. Removing P1's unknown window leaves none."""
        out = pa.run_ablations(registry, extract_bytes())
        assert out["paths"]["P1"]["unknown_competitors"]["unknown_rows"] == 0
        assert out["paths"]["P3"]["unknown_competitors"]["unknown_rows"] == 1

    def test_a_path_that_built_nothing_is_not_ablated_and_carries_no_delta(self, registry):
        """A removed-nothing run would show delta 0 and read as 'the path does not matter' — it has no figures and says why."""
        out = pa.run_ablations(registry, extract_bytes())
        for path in ("P5", "P6"):
            rec = out["paths"][path]
            assert rec["status"] == "path_absent_from_extract" and rec["rows_removed"] == 0
            assert rec["figures"] is None and rec["delta_vs_full"] is None and rec["extract_sha256"] is None
            assert "path_absent_from_extract" in rec["null_reason"]
        assert set(out["paths"]) == set(pa.PATHS)

    def test_the_baseline_must_reproduce_the_recorded_measurement(self, registry):
        raw = extract_bytes()
        recorded = score_candidate(registry, load_candidate_extract_bytes(raw))
        assert pa.run_ablations(registry, raw, recorded_result=recorded)["base"]["reproduces_recorded_result"] is True
        tampered = copy.deepcopy(recorded)
        tampered["t_cover"]["hits"] += 1
        assert pa.run_ablations(registry, raw, recorded_result=tampered)["base"]["reproduces_recorded_result"] is False
        assert pa.run_ablations(registry, raw)["base"]["reproduces_recorded_result"] is None          # not supplied: unknown, not true

    def test_each_ablated_extract_is_written_and_hash_recorded(self, registry, tmp_path):
        out = pa.run_ablations(registry, extract_bytes(), out_dir=tmp_path)
        for path, rec in out["paths"].items():
            f = tmp_path / f"ablated_extract_{path}.json"
            if rec["status"] == "MEASURED":
                blob = f.read_bytes()
                assert hashlib.sha256(blob).hexdigest() == rec["extract_sha256"]
                doc = json.loads(blob)
                assert all(r["path_id"] != path for r in doc["rows"]) and doc["ablation"]["removed_path"] == path and doc["row_count"] == len(doc["rows"])
            else:
                assert not f.exists()

    def test_the_result_is_a_non_gating_diagnostic_that_states_its_limits(self, registry):
        out = pa.run_ablations(registry, extract_bytes())
        assert out["non_gating"] is True and out["mode"] == "leave_one_path_out" and "never a gate" in out["limits"]

    @pytest.mark.parametrize("doc_edit, needle", [
        (lambda d: d.update(predicate="kala_gochara_windows where chart_id='x' and generation='4.1'"), "not a ka_gochara_eval_window extract"),
        (lambda d: [r.pop("path_id") for r in d["rows"]], "without `path_id`")])
    def test_an_extract_that_does_not_record_the_building_path_is_refused(self, registry, doc_edit, needle):
        doc = json.loads(extract_bytes())
        doc_edit(doc)
        with pytest.raises(pa.AblationRefused, match=needle):
            pa.run_ablations(registry, json.dumps(doc).encode())


# ── the command ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def measured(tmp_path, rows=ROWS, budget=None):
    """FIXTURE: a verified MEASUREMENT of the fixture extract (the base result an ablation run must reproduce)."""
    reg = write_json(tmp_path / INPUT_FILES["event_registry"], synth_registry())
    ex = tmp_path / OUT
    ex.write_bytes(extract_bytes(rows))
    ctl = write_json(tmp_path / INPUT_FILES["random_controls"], {"seed": CONTROLS_SEED, "controls": [
        {k: v for k, v in c.items() if not k.startswith("_")}
        for c in draw_controls(load_registry(reg), load_candidate_extract_bytes(ex.read_bytes()))]})
    doc, s1 = governed_stage1(tmp_path, cohort={"held_out": 2, "timing_usable": 1, "year_grain": 1, "exact_cohort": 1, "interval_grain": 0,
                                                "chart_id": CHART_ID})
    if budget is not None:                                           # a frozen budget that is NOT the module default
        doc["tolerances_and_conversions"]["enumeration_budget"] = budget
        write_json(s1, doc)
    s2 = write_json(tmp_path / "FREEZE_STAGE2_t.json", {"run_id": "t", "stage1_sha256": sha256_file(s1), "extracts": {ex.name: {"sha256": sha256_file(ex)}}})
    base = tmp_path / "base.json"
    extra = [] if budget is None else ["--budget", str(budget)]
    assert run(["--registry", str(reg), "--extract", str(ex), "--controls", str(ctl), "--stage1", str(s1), "--stage2", str(s2), "--output", str(base), *extra]) == 0
    return reg, ex, ctl, s1, s2, base


def argv(tmp_path, reg, ex, s1, s2, base, out):
    return ["--registry", str(reg), "--extract", str(ex), "--stage1", str(s1), "--stage2", str(s2), "--base-result", str(base),
            "--out-dir", str(tmp_path / "abl"), "--output", str(out)]


def test_the_command_runs_under_the_verified_freeze_and_its_baseline_reproduces_the_measurement(tmp_path):
    reg, ex, ctl, s1, s2, base = measured(tmp_path, budget=12345)
    out = tmp_path / "ablations.json"
    assert pa.main([*argv(tmp_path, reg, ex, s1, s2, base, out), "--budget", "12345"]) == 0
    doc = json.loads(out.read_text())
    assert doc["schema"] == "ky.path_ablations/1" and doc["chart_id"] == CHART_ID and doc["generation"] == "5.0"
    assert doc["base"]["reproduces_recorded_result"] is True and doc["base"]["extract_sha256"] == sha256_file(ex)
    assert doc["enumeration_budget"] == 12345                                    # the FROZEN budget, not a default of this module
    assert doc["paths"]["P3"]["delta_vs_full"]["t_cover"]["hits"] == -1


def test_the_command_refuses_without_a_verified_freeze_a_foreign_base_result_or_an_edited_extract(tmp_path, capsys):
    reg, ex, ctl, s1, s2, base = measured(tmp_path)
    out = tmp_path / "ablations.json"
    # a base result that is not a verified MEASUREMENT
    refused = json.loads(base.read_text())
    refused["mode"] = "BASELINE_DRY_RUN"
    bad = write_json(tmp_path / "bad_base.json", refused)
    assert pa.main(argv(tmp_path, reg, ex, s1, s2, bad, out)) == 1 and "not a verified MEASUREMENT" in capsys.readouterr().err
    # a base result of another extract
    other = json.loads(base.read_text())
    other["extract_sha256"]["measured"] = "0" * 64
    assert pa.main(argv(tmp_path, reg, ex, s1, s2, write_json(tmp_path / "other_base.json", other), out)) == 1
    assert "did not score this extract" in capsys.readouterr().err
    # an extract edited after the Stage-2 seal
    ex.write_text(ex.read_text() + " ")
    assert pa.main(argv(tmp_path, reg, ex, s1, s2, base, out)) == 1 and "differs from the sealed" in capsys.readouterr().err
    assert not out.exists()


# ── the report carries the ablations only for the extract they ablated ────────────────────────────────────────────────────────────

def _bundle(tmp_path, ablation_doc):
    reg, ex, ctl, s1, s2, base = measured(tmp_path)
    ab = tmp_path / "ablations.json"
    assert pa.main(argv(tmp_path, reg, ex, s1, s2, base, ab)) == 0
    if ablation_doc is not None:
        doc = json.loads(ab.read_text())
        ablation_doc(doc)                                  # edits in place
        ab.write_text(json.dumps(doc))

    def pin(p):
        return {"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    res = json.loads(base.read_text())
    res["extract_sha256"]["declared_pin"] = res["extract_sha256"]["measured"]            # the report requires the scorer's declared pin == measured == the file
    base.write_text(json.dumps(res))
    return {"schema": "ky.qualification_inputs/1", "chart_id": CHART_ID, "generation_authors": ["builder-a"],
            "sources": {"5.0": {**pin(base), "scorer_id": "independent-scorer", "extract": pin(ex), "path_ablations": pin(ab)}}}


def test_the_report_discloses_all_six_paths_from_the_pinned_ablations(tmp_path):
    out = report.assemble(_bundle(tmp_path, None), tmp_path)
    dis = out["generations"]["5.0"]["path_ablations"]
    assert dis["missing_paths"] == [] and dis["status"] == "pass"
    assert dis["measured"]["P3"]["status"] == "MEASURED" and dis["measured"]["P5"]["status"] == "path_absent_from_extract"
    assert dis["run"]["mode"] == "leave_one_path_out" and dis["run"]["non_gating"] is True
    assert out["generations"]["3.0"]["path_ablations"]["missing_paths"] == list(pa.PATHS)      # no ablation file for 3.0: all six still listed missing


@pytest.mark.parametrize("edit, needle", [
    (lambda d: d["base"].update(extract_sha256="0" * 64), "did not ablate this source's extract"),
    (lambda d: d.update(generation="4.1"), "identity or schema mismatch"),
    (lambda d: d.update(chart_id="11111111-1111-4111-8111-111111111111"), "identity or schema mismatch"),
    (lambda d: d.update(schema="other/1"), "identity or schema mismatch"),
    (lambda d: d.pop("paths"), "no per-path records")])
def test_the_report_refuses_ablations_of_another_extract_generation_or_shape(tmp_path, edit, needle):
    with pytest.raises(ValueError, match=needle):
        report.assemble(_bundle(tmp_path, edit), tmp_path)


def test_a_path_with_no_record_stays_listed_as_missing(tmp_path):
    out = report.assemble(_bundle(tmp_path, lambda d: d["paths"].pop("P2")), tmp_path)
    dis = out["generations"]["5.0"]["path_ablations"]
    assert dis["missing_paths"] == ["P2"] and dis["status"] == "insufficient_evidence"
