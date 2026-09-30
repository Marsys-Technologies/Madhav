"""Controls reproduction tests (protocol §7) and oracle-file tests (§11.1)."""
from __future__ import annotations

import json

import pytest

from services.gochara_eval import (CONTROLS_SEED, ControlsMismatch,
                                   OracleFileError, draw_controls, load_oracles,
                                   verify_controls_file)
from services.gochara_eval.oracles import oracle_execution_registry

from .conftest import (CONTROLS_V1_3, EXTRACT_3_0, ORACLES_V1_4, REGISTRY_V2_3,
                       needs_campaign, write_json)
from services.gochara_eval import load_extract, load_registry


def _mini_inputs(tmp_path):
    events = [
        {"eid": "E1", "tier": "held_out_timing", "obs_type": "point",
         "grain": "exact", "date": "2010-05-20", "class": "surgery"},
        {"eid": "E2", "tier": "held_out_year", "obs_type": "point",
         "grain": "year", "date": "2015", "class": "relocation"},
    ]
    counts = {"logged_events": 2, "dev": 0, "held_out": 2,
              "held_out_timing": 1, "held_out_year": 1, "excluded": 0,
              "annotation_rows": 0, "exact_cohort": 1, "month_grain": 0,
              "interval_grain": 0, "t_rank_floor": 1}
    reg_path = write_json(tmp_path / "reg.json",
                          {"artifact": "EVENT_REGISTRY", "version": "t",
                           "horizon": {"start": "1998-01-01",
                                       "end": "2026-04-17", "H_days": 10334},
                           "conventions": {"counts": counts}, "events": events})
    rows = [{"event_class": "surgery", "ws": "2010-05-01", "we": "2010-06-01",
             "pk": "2010-05-20", "si": 0.9, "valence": "loss"}]
    ext_path = write_json(tmp_path / "ext.json", {"rows": rows})
    return load_registry(reg_path), load_extract(ext_path)


class TestControlsSynthetic:
    def test_roundtrip_reproduces(self, tmp_path):
        reg, ext = _mini_inputs(tmp_path)
        drawn = draw_controls(reg, ext)
        doc = {"seed": CONTROLS_SEED,
               "controls": [{k: c[k] for k in
                             ("eid", "cls", "span_days", "control_hits", "dates")}
                            for c in drawn]}
        path = write_json(tmp_path / "ctrl.json", doc)
        out = verify_controls_file(path, reg, ext)
        assert out["status"] == "REPRODUCED"
        assert out["total_draws"] == 40  # 20 draws × 2 events

    def test_mutated_copy_fails(self, tmp_path):
        reg, ext = _mini_inputs(tmp_path)
        drawn = draw_controls(reg, ext)
        doc = {"seed": CONTROLS_SEED,
               "controls": [{k: c[k] for k in
                             ("eid", "cls", "span_days", "control_hits", "dates")}
                            for c in drawn]}
        path = write_json(tmp_path / "ctrl.json", doc)
        raw = bytearray(path.read_bytes())
        # flip one digit inside the first drawn date (one-byte mutation)
        first_date = drawn[0]["dates"][0].encode()
        i = raw.index(first_date) + len(first_date) - 1
        raw[i:i + 1] = b"9" if raw[i:i + 1] != b"9" else b"8"
        mutated = tmp_path / "ctrl_mut.json"
        mutated.write_bytes(bytes(raw))
        with pytest.raises(ControlsMismatch):
            verify_controls_file(mutated, reg, ext)

    def test_wrong_seed_fails(self, tmp_path):
        reg, ext = _mini_inputs(tmp_path)
        path = write_json(tmp_path / "ctrl.json", {"seed": 1, "controls": []})
        with pytest.raises(ControlsMismatch, match="seed"):
            verify_controls_file(path, reg, ext)


@needs_campaign
class TestControlsReal:
    def test_v1_3_controls_reproduce_byte_for_byte(self):
        reg = load_registry(REGISTRY_V2_3)
        ext = load_extract(EXTRACT_3_0)
        out = verify_controls_file(CONTROLS_V1_3, reg, ext)
        assert out["status"] == "REPRODUCED"
        assert out["total_hits"] == 638 and out["total_draws"] == 940

    def test_mutated_real_controls_fail(self, tmp_path):
        raw = bytearray(CONTROLS_V1_3.read_bytes())
        i = raw.index(b"control_hits") + len(b"control_hits") + 3
        raw[i:i + 1] = b"9" if raw[i:i + 1] != b"9" else b"8"
        mutated = tmp_path / "ctrl_mut.json"
        mutated.write_bytes(bytes(raw))
        reg = load_registry(REGISTRY_V2_3)
        ext = load_extract(EXTRACT_3_0)
        with pytest.raises(ControlsMismatch):
            verify_controls_file(mutated, reg, ext)


def _oracle(oid, kind="literal"):
    return {"id": oid, "guards": "§x", "defects": ["#1"], "given": "g",
            "when": "w", "then": "t", "mutation_that_must_fail": "m",
            "fixture_kind": kind}


class TestOracles:
    def test_valid_file(self, tmp_path):
        doc = {"version": "t", "oracle_count": 2,
               "oracles": [_oracle("O-A-1"), _oracle("O-B-1",
                                                     "executable_at_A5.5")]}
        reg = load_oracles(write_json(tmp_path / "o.json", doc))
        assert reg.oracle_count == 2
        assert reg.split == {"literal": 1, "executable_at_A5.5": 1}
        sites = oracle_execution_registry(write_json(tmp_path / "o2.json", doc))
        assert sites == {"O-A-1": "gochara_rules_pytest",
                         "O-B-1": "a5_5_rehearsal"}

    def test_count_rule_mismatch_rejected(self, tmp_path):
        doc = {"version": "t", "oracle_count": 57,
               "oracles": [_oracle(f"O-{i}") for i in range(56)]}
        with pytest.raises(OracleFileError, match="count rule"):
            load_oracles(write_json(tmp_path / "o.json", doc))

    def test_unknown_fixture_kind_rejected(self, tmp_path):
        doc = {"version": "t", "oracle_count": 1,
               "oracles": [_oracle("O-X", "constrained_generator")]}
        with pytest.raises(OracleFileError, match="fixture_kind"):
            load_oracles(write_json(tmp_path / "o.json", doc))

    def test_status_registry(self, tmp_path):
        doc = {"version": "t", "oracle_count": 1, "oracles": [_oracle("O-A-1")]}
        reg = load_oracles(write_json(tmp_path / "o.json", doc))
        assert reg.records["O-A-1"].status == "REGISTERED"
        reg.record_status("O-A-1", "PASS")
        assert reg.as_dict()["oracles"]["O-A-1"]["status"] == "PASS"
        with pytest.raises(OracleFileError):
            reg.record_status("O-UNKNOWN", "PASS")


@needs_campaign
class TestOraclesReal:
    def test_v1_4_validates_57(self):
        reg = load_oracles(ORACLES_V1_4)
        assert reg.oracle_count == 57
        assert reg.split == {"literal": 21, "executable_at_A5.5": 36}

    def test_v1_4_mutated_to_56_fails(self, tmp_path):
        doc = json.loads(ORACLES_V1_4.read_text())
        doc["oracles"] = doc["oracles"][:-1]  # drop one -> 56 vs header 57
        with pytest.raises(OracleFileError, match="count rule"):
            load_oracles(write_json(tmp_path / "o56.json", doc))
