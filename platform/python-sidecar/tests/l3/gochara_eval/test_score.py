"""Full scoring-pass tests: CLI result shape, rejection exits, '3.0' replay."""
from __future__ import annotations

import json

import pytest

from services.gochara_eval.score import main, run_scoring_pass

from .conftest import (CONTROLS_V1_3, EXTRACT_3_0, EXTRACT_3_0_PIN,
                       REGISTRY_V2_3, needs_campaign)
from services.gochara_eval import measure_sha256


class TestCliRejections:
    def test_hash_mismatch_writes_result_and_exits_1(self, tmp_path,
                                                     synth_registry_path,
                                                     synth_extract_path):
        out = tmp_path / "result.json"
        rc = main(["--registry", str(synth_registry_path),
                   "--extract", str(synth_extract_path),
                   "--output", str(out),
                   "--declared-pin", "0" * 64])
        assert rc == 1
        result = json.loads(out.read_text())
        assert result["input_adapter"]["status"] == "INPUT_REJECTED"
        assert "sha256" in result["input_adapter"]["reason"]

    def test_clean_run_writes_result(self, tmp_path, synth_registry_path,
                                     synth_extract_path):
        out = tmp_path / "result.json"
        rc = main(["--registry", str(synth_registry_path),
                   "--extract", str(synth_extract_path),
                   "--output", str(out)])
        assert rc == 0
        result = json.loads(out.read_text())
        for key in ("t_cover", "t_time", "t_rank", "t_fp", "t_fp_gain",
                    "t_fp_overall", "t_honesty", "degeneracy", "per_event",
                    "input_adapter", "extract_sha256", "source_reconciliation",
                    "dedup_table"):
            assert key in result
        # synth fixture: both held-out events hit
        assert result["t_cover"]["hits"] == 2
        assert result["t_cover"]["total"] == 2


@needs_campaign
class TestReplay30:
    """The harness must reproduce rerun_result_v2_3.json's figures exactly."""

    def test_figures_match_rerun_result_v2_3(self, tmp_path):
        out = tmp_path / "result.json"
        result = run_scoring_pass(REGISTRY_V2_3, EXTRACT_3_0, CONTROLS_V1_3,
                                  out, declared_pin=EXTRACT_3_0_PIN,
                                  generation="3.0")
        assert result["t_cover"]["hits"] == 32
        assert result["t_cover"]["total"] == 47
        assert result["t_cover"]["pass"] is True
        assert len(result["t_cover"]["misses"]) == 15
        tt = result["t_time"]
        assert tt["capped_median_days"] == 182 and tt["misses"] == 2
        assert tt["uncapped_hits"] == [["EVT.1998.02.16.01", 686],
                                       ["EVT.2007.06.10.01", 998],
                                       ["EVT.2026.03.20.01", 333]]
        tr = result["t_rank"]
        assert tr["status"] == "VOID" and tr["eligible"] == 0
        assert tr["timing_usable"] == 32 and tr["floor"] == 17
        assert "median_percentile" not in tr
        assert result["t_fp_overall"]["pass"] is False
        assert result["t_honesty"]["status"] == "UNVERIFIABLE"
        assert result["t_honesty"]["pass"] is False
        rc = result["random_controls"]
        assert rc["status"] == "REPRODUCED"
        assert rc["total_hits"] == 638 and rc["total_draws"] == 940
        assert result["extract_sha256"] == {
            "declared_pin": EXTRACT_3_0_PIN, "measured": EXTRACT_3_0_PIN,
            "match": True}
        assert measure_sha256(EXTRACT_3_0.read_bytes()) == EXTRACT_3_0_PIN

    def test_top_level_fields_match_reference(self, tmp_path):
        out = tmp_path / "result.json"
        result = run_scoring_pass(REGISTRY_V2_3, EXTRACT_3_0, CONTROLS_V1_3,
                                  out, declared_pin=EXTRACT_3_0_PIN)
        ref_path = REGISTRY_V2_3.parent / "rerun_result_v2_3.json"
        if not ref_path.exists():
            pytest.skip("reference result file not present")
        ref = json.loads(ref_path.read_text())
        for key in ("t_cover", "t_time", "t_rank", "t_fp", "t_fp_gain",
                    "t_fp_overall", "degeneracy", "per_event", "dedup_table",
                    "extract_sha256"):
            assert result[key] == ref[key], f"field {key} diverges"
