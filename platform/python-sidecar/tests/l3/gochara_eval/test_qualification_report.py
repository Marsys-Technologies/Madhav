"""Hash-bound report assembly, independent scorer declarations, no acceptance."""
from __future__ import annotations

import hashlib
import json

import pytest

from services.gochara_eval import qualification_report as report

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def pin(tmp_path, name, doc):
    p = tmp_path / name
    p.write_text(json.dumps(doc))
    return {"path": name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def manifest(tmp_path):
    result = {"protocol": "EVALUATION_PROTOCOL_v2_3", "generation": "5.0",
              "input_adapter": {"status": "PASS"}, "mode": "MEASUREMENT",
              "t_cover": {"hits": 31, "total": 47, "pass": False},
              "t_rank": {"status": "RANK-UNPROVEN", "eligible": 0, "floor": 17},
              "mechanism_attribution": {"P1": {"hits": 2, "eids": ["a", "b"]}},
              "path_ablations": {"P1": {"delta_hits": -2}}}
    ext = pin(tmp_path, "extract5.json", {"chart_id": CHART, "generation": "5.0", "rows": []})
    result["extract_sha256"] = {"measured": ext["sha256"], "declared_pin": ext["sha256"], "match": True}
    result["freeze"] = {"status": "VERIFIED"}
    return {"schema": "ky.qualification_inputs/1", "chart_id": CHART, "generation_authors": ["builder-a", "builder-b"],
            "sources": {"5.0": {**pin(tmp_path, "score5.json", result), "scorer_id": "independent-scorer", "extract": ext}}}


def test_all_generations_endpoints_diagnostics_and_dependencies_visible(tmp_path):
    doc = manifest(tmp_path)
    before = json.loads(json.dumps(doc))
    result = report.assemble(doc, tmp_path)
    assert result["build_state"] == "built_waiting_on_gate"
    assert result["chart_id"] == CHART
    assert set(result["generations"]) == {"3.0", "4.1", "5.0"}
    assert result["generations"]["5.0"]["endpoints"]["t_cover"]["status"] == "fail"
    assert result["generations"]["5.0"]["endpoints"]["t_rank"]["status"] == "insufficient_evidence"
    assert result["generations"]["5.0"]["source_result"]["t_cover"]["hits"] == 31
    assert result["generations"]["4.1"]["endpoints"]["t_cover"]["measured"] is None
    assert result["generations"]["5.0"]["mechanism_attribution"]["measured"] == {"P1": {"hits": 2, "eids": ["a", "b"]}}
    assert result["generations"]["5.0"]["path_ablations"]["measured"] == {"P1": {"delta_hits": -2}}
    assert result["generations"]["3.0"]["path_ablations"]["status"] == "insufficient_evidence"
    assert result["generations"]["5.0"]["path_ablations"]["status"] == "insufficient_evidence"
    assert result["generations"]["5.0"]["path_ablations"]["missing_paths"] == ["P2", "P3", "P4", "P5", "P6"]
    assert all(g["status"] in ("not_evaluable", "insufficient_evidence") for g in result["engineering_diagnostics"].values())
    assert result["pending_prerequisites"] == ["J-4f", "A5.6", "B5.3", "B4.3", "B4.4", "independent_seal_verification", "independent_acceptance"]
    assert result["sources"]["5.0"]["sha256"] == doc["sources"]["5.0"]["sha256"]
    assert doc == before
    assert "flip_eligible" not in result and "verdict" not in result
    md = report.render_markdown(result)
    assert "built, waiting on gate" in md and "31" in md and "insufficient_evidence" in md
    assert "single chart" in md and "not used for calibration" in md


@pytest.mark.parametrize("scorer", ["builder-a", "builder-b", "", None, " BUILDER-A "])
def test_generation_authors_cannot_score_held_out_items(tmp_path, scorer):
    doc = manifest(tmp_path)
    doc["sources"]["5.0"]["scorer_id"] = scorer
    with pytest.raises(ValueError, match="independent scorer"):
        report.assemble(doc, tmp_path)


def test_hash_mismatch_refuses_report(tmp_path):
    doc = manifest(tmp_path)
    (tmp_path / "score5.json").write_text('{}')
    with pytest.raises(ValueError, match="sha256"):
        report.assemble(doc, tmp_path)


@pytest.mark.parametrize("bad", ["authors", "source_generation", "protocol", "input", "mode", "freeze", "path"])
def test_malformed_or_rejected_source_cannot_be_reported_as_measurement(tmp_path, bad):
    doc = manifest(tmp_path)
    if bad == "authors":
        doc["generation_authors"] = []
    elif bad == "path":
        doc["sources"]["5.0"]["path"] = "https://invalid.example/score.json"
    else:
        p = tmp_path / "score5.json"
        src = json.loads(p.read_text())
        key, val = {"source_generation": ("generation", "4.1"), "protocol": ("protocol", "v1"),
                    "input": ("input_adapter", {"status": "INPUT_REJECTED"}), "mode": ("mode", "BASELINE_DRY_RUN"), "freeze": ("freeze", {"status": "REFUSED"})}[bad]
        src[key] = val
        doc["sources"]["5.0"].update(pin(tmp_path, p.name, src))
    with pytest.raises(ValueError):
        report.assemble(doc, tmp_path)


def test_cli_builds_reviewable_artifacts_with_absent_measurements(tmp_path):
    mp = tmp_path / "input.json"
    mp.write_text(json.dumps({"schema": "ky.qualification_inputs/1", "chart_id": CHART,
                              "generation_authors": ["builder"], "sources": {}}))
    out, md = tmp_path / "report.json", tmp_path / "report.md"
    assert report.main(["--inputs", str(mp), "--output", str(out), "--markdown", str(md)]) == 0
    doc = json.loads(out.read_text())
    assert all(v["status"] == "insufficient_evidence"
               for g in doc["generations"].values() for v in g["endpoints"].values())
    assert md.exists()


def test_diagnostic_extract_is_hash_and_identity_bound(tmp_path):
    doc = manifest(tmp_path)
    extract = {"chart_id": CHART, "generation": "5.0", "rows": [
        {"event_class": "marriage", "ws": "2010-01-01", "we": "2010-01-02", "pk": "2010-01-01",
         "si": 1, "outcome_valence_for_native": "adverse"}]}
    doc["diagnostic_extract"] = pin(tmp_path, "diag.json", extract)
    result = report.assemble(doc, tmp_path)
    assert result["engineering_diagnostics"]["valence"]["measured"] == {"adverse": 1}
    extract["generation"] = "4.1"
    doc["diagnostic_extract"] = pin(tmp_path, "diag.json", extract)
    with pytest.raises(ValueError, match="identity"):
        report.assemble(doc, tmp_path)


def test_source_extract_must_match_chart_and_measured_digest(tmp_path):
    doc = manifest(tmp_path)
    ent = doc["sources"]["5.0"]
    ent["extract"] = pin(tmp_path, "extract5.json", {"chart_id": "00000000-0000-0000-0000-000000000000", "generation": "5.0", "rows": []})
    src = json.loads((tmp_path / "score5.json").read_text())
    src["extract_sha256"] = {"measured": ent["extract"]["sha256"], "declared_pin": ent["extract"]["sha256"], "match": True}
    ent.update(pin(tmp_path, "score5.json", src))
    with pytest.raises(ValueError, match="identity|extract"):
        report.assemble(doc, tmp_path)


def test_cli_refuses_to_overwrite_input(tmp_path):
    mp = tmp_path / "input.json"
    mp.write_text(json.dumps(manifest(tmp_path)))
    before = mp.read_bytes()
    assert report.main(["--inputs", str(mp), "--output", str(mp)]) == 2
    assert mp.read_bytes() == before


def test_score_extract_digest_is_not_merely_an_asserted_match_flag(tmp_path):
    doc = manifest(tmp_path)
    src = json.loads((tmp_path / "score5.json").read_text())
    src["extract_sha256"]["measured"] = "0" * 64
    doc["sources"]["5.0"].update(pin(tmp_path, "score5.json", src))
    with pytest.raises(ValueError, match="digest"):
        report.assemble(doc, tmp_path)


def test_coverage_source_is_hash_and_identity_bound(tmp_path):
    doc = manifest(tmp_path)
    cov = {"chart_id": CHART, "generation": "5.0", "cells": []}
    doc["coverage_cells"] = pin(tmp_path, "coverage.json", cov)
    assert report.assemble(doc, tmp_path)["engineering_diagnostics"]["coverage"]["status"] == "insufficient_evidence"
    cov["chart_id"] = "00000000-0000-0000-0000-000000000000"
    doc["coverage_cells"] = pin(tmp_path, "coverage.json", cov)
    with pytest.raises(ValueError, match="identity"):
        report.assemble(doc, tmp_path)


def test_portable_3_0_baseline_is_transcribed_without_changing_any_figure(tmp_path):
    import shutil
    from pathlib import Path
    source = Path(__file__).parent / "fixtures/candidate_3_0"
    score_name, extract_name = "rerun_result_v2_3.json", "baseline_3_0_extract_v1_0.json"
    for name in (score_name, extract_name):
        shutil.copyfile(source / name, tmp_path / name)
    def existing(name):
        return {"path": name, "sha256": hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()}
    doc = {"schema": "ky.qualification_inputs/1", "chart_id": CHART, "generation_authors": ["synthetic-builder"],
           "sources": {"3.0": {**existing(score_name), "scorer_id": "historical-stream-b",
                                 "extract": existing(extract_name)}}}
    original = json.loads((tmp_path / score_name).read_text())
    result = report.assemble(doc, tmp_path)
    base = result["generations"]["3.0"]
    assert base["source_result"] == original
    assert base["endpoints"]["t_cover"]["measured"]["hits"] == 32
    assert base["endpoints"]["t_cover"]["status"] == "pass"
    assert base["endpoints"]["t_time"]["measured"]["capped_median_days"] == 182
    assert base["endpoints"]["t_time"]["status"] == "fail"
    assert base["endpoints"]["t_rank"]["status"] == "not_evaluable"
    assert base["endpoints"]["t_rank"]["measured"]["status"] == "VOID"
    assert base["endpoints"]["t_fp"]["status"] == "fail"
    assert base["endpoints"]["t_honesty"]["status"] == "insufficient_evidence"
    assert result["generations"]["5.0"]["source_result"] is None
