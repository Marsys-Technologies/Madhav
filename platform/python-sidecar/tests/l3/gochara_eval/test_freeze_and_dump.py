"""Two-stage freeze refusal, the extract-generation command and the candidate scoring CLI (services/gochara_eval)."""
from __future__ import annotations

import copy
import datetime as dt
import decimal
import hashlib
import json
from pathlib import Path

import pytest

from services.gochara_eval import dump_extract as dx
from services.gochara_eval.candidate_score import run
from services.gochara_eval.freeze import (FROZEN_CODE_FILES, REQUIRED_CONSUMED_BODIES, THRESHOLD_KEYS, FreezeRefused, bind_dump_run,
                                          bind_scoring_run, code_hashes, ephemeris_coverage_problems, required_ephemeris_files,
                                          require_stage1, require_stage2, sha256_file, stage1_problems)

from .conftest import (CAMPAIGN_MEASUREMENT, EXTRACT_3_0, EXTRACT_3_0_PIN, REGISTRY_V2_3, needs_campaign, synth_registry,
                       write_json)

COMMIT = "a" * 40
SIDECAR = Path(__file__).resolve().parents[3]


SHA = "ab" * 32
GOOD_EPH = {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": SHA, "platform": "Linux-x86_64",
            "files": {"sepl_18.se1": SHA, "semo_18.se1": SHA}, "probe_digest": SHA}
ORB_RULING = "M-1 fallback no-box x 5.0 deg (unratified)"
INPUT_FILES = {                                            # identifier -> file name (every mandatory input identity)
    "event_registry": "event_registry_v2_3.json", "random_controls": "random_controls_v1_3.json",
    "baseline_3_0_extract": "baseline_3_0_extract_v1_0.json", "scorer_3_0": "rerun_3_0_v2_3_scorer.py",
    "recorded_result_3_0": "rerun_result_v2_3.json", "recorded_per_event_3_0": "rerun_per_event_v2_3.json",
    "evaluation_protocol": "EVALUATION_PROTOCOL_v2_3.md", "si_addendum": "EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_4.md",
    "bounds_model": "unknown_competitor_bounds_model.py", "design_specs": "GOCHARA_DESIGN_SPECS_v1_4.md",
    "test_oracles": "GOCHARA_TEST_ORACLES_v1_4.json", "amendments_draft": "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md",
}
OUT = "baseline_4_1_extract_v1_0.json"


def make_stage1(tmp_path, generation="4.1", cohort=None):
    """A SUBSTANTIVE, valid Stage-1 freeze: every mandatory field typed and non-empty, every mandatory input present on disk."""
    inputs = {}
    for ident, fname in INPUT_FILES.items():
        f = tmp_path / fname
        if not f.exists():
            f.write_text(f"frozen input {ident}")
        inputs[ident] = {"path": fname, "sha256": sha256_file(f)}
    args = {"generation": generation, "stage1": "FREEZE_STAGE1_t.json", "pinned_at": "2026-10-05", "out": OUT}
    doc = {"artifact": "FREEZE_STAGE1", "run_id": "t", "generation": generation, "status": "FROZEN",
           "amendments_draft": {"version": "0.22"}, "addendum": {"artifact": "EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING", "version": "1.4"},
           "registries_selected": {"event_registry": "v2_3", "governed_registry_rows": "n/a (legacy-kernel generation)"},
           "orb_state": {"text": "the 4.x chain's own activity orb as declared in its manifest (unratified)",
                         "manifest_location": "kala_gochara_publication.input_generation_vector"},
           "conventions": {"si_mapping": "raw_intensity as stored", "utc_to_ist": "(ts at time zone 'Asia/Kolkata')::date",
                           "merge_implementation": "candidate.merge_candidates", "stored_value_precision": "double via Decimal",
                           "tie_tolerance": 1e-9, "tie_grouping": "adjacent-gap", "candidate_set": "protocol 4.6",
                           "horizon": {"scored": "1998-01-01 -> 2026-04-17", "extract_assertion": "1998-01-01 <= w < 2026-04-18"}},
           "ephemeris_requirement": {
               "id": "S1-REQ-EPHEMERIS", "consumed_bodies": list(REQUIRED_CONSUMED_BODIES),
               "horizon": {"start": "1997-12-31", "end": "2026-04-19"},
               "manifest_readback": {"generation": generation, "manifest_status": "candidate", "orb_max_deg": 5.0,
                                     "orb_ruling": ORB_RULING, "ephemeris": GOOD_EPH, "ephemeris_problems": []}},
           "code": {"adapter_commit": COMMIT, "scorer_commit": COMMIT, "files": code_hashes(SIDECAR)},
           "extract_generation_args": args, "extract_generation_command": dx.CANONICAL_COMMAND.format(**args),
           "extract_environment": "read-only role; READ ONLY transaction",
           "cohort": cohort or {"held_out": 47, "timing_usable": 32, "year_grain": 15, "exact_cohort": 5, "interval_grain": 4,
                                "chart_id": "482012f1-710e-4a25-994a-93821f5871aa"},
           "controls": {"file": INPUT_FILES["random_controls"], "seed": 482012, "experiment": "rolling spans", "rule": "re-drawn"},
           "thresholds": {k: f"threshold text for {k}" for k in THRESHOLD_KEYS},
           "tolerances_and_conversions": {"tie_tolerance": 1e-9, "percentile": "100*(avg_rank-1)/N", "timezone": "IST",
                                          "enumeration_budget": 400000, "budget_exceeded": "unqualified, full range"},
           "av_donor_rows": {"behaviour": "donor_resolved", "comparability": "a run made before these rows exist is a DIFFERENT candidate; never compared as one",
                             "per_ayanamsha": {"lahiri_chitrapaksha": {"row_count": 672, "digest": SHA},
                                               "raman": {"row_count": 672, "digest": SHA[::-1]}}},
           "coverage_manifest": "UNVERIFIABLE (determined)", "rerun_policy": "deterministic; no change after inspection",
           "inputs": inputs}
    return doc, write_json(tmp_path / "FREEZE_STAGE1_t.json", doc)


def conn_for(doc):
    """A fake read-only connection whose live manifest and live donor-row identity equal the frozen ones."""
    rb = doc["ephemeris_requirement"]["manifest_readback"]
    av = [(a, e["row_count"], e["digest"]) for a, e in doc["av_donor_rows"]["per_ayanamsha"].items()]
    return FakeConn(ROWS, manifest=[(rb["manifest_status"], rb["orb_max_deg"], rb["orb_ruling"], rb["ephemeris"])], av=av)


class TestStage1:
    def test_a_complete_freeze_verifies(self, tmp_path):
        doc, p = make_stage1(tmp_path)
        assert require_stage1(p, tmp_path, dx.CANONICAL_COMMAND)["run_id"] == "t"

    def test_missing_file_is_refused(self, tmp_path):
        with pytest.raises(FreezeRefused, match="does not exist"):
            require_stage1(tmp_path / "nope.json", tmp_path, dx.CANONICAL_COMMAND)

    def test_placeholder_anywhere_is_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        for path in (("code", "adapter_commit"), ("code", "scorer_commit"), ("amendments_draft", "sha256")):
            d = copy.deepcopy(doc)
            d[path[0]][path[1]] = "<<FILL_AT_MERGE>>"
            assert any("placeholder" in p for p in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))

    def test_commit_must_be_40_hex(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        doc["code"]["adapter_commit"] = "abc123"
        assert any("40-hex" in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_input_hash_mismatch_is_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        (tmp_path / INPUT_FILES["event_registry"]).write_text("changed after the freeze")
        assert any("sha256 mismatch" in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_missing_input_file_is_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        (tmp_path / INPUT_FILES["bounds_model"]).unlink()
        assert any("not found" in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_running_code_must_equal_frozen_code(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        doc["code"]["files"]["services/gochara_eval/candidate.py"] = "1" * 64
        assert any("code hash mismatch for services/gochara_eval/candidate.py" in p
                   for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_every_frozen_code_file_exists_and_is_listed(self):
        have = code_hashes(SIDECAR)
        assert set(have) == set(FROZEN_CODE_FILES)

    def test_tolerance_must_be_the_protocols(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        doc["conventions"]["tie_tolerance"] = 1e-6
        assert any("tie_tolerance" in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_status_must_be_frozen_and_command_canonical(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        doc["status"] = "DRAFT"
        doc["extract_generation_command"] = "psql -c 'select 1'"
        probs = stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND)
        assert any("'FROZEN'" in p for p in probs) and any("canonical command" in p for p in probs)

    def test_the_ephemeris_requirement_is_a_real_component_not_a_flag(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        P = lambda d: stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND)       # noqa: E731
        d = copy.deepcopy(doc)
        d["ephemeris_requirement"]["manifest_readback"]["ephemeris"]["files"] = {}
        assert any("files is empty" in p for p in P(d))                          # re-derived: the claimed [] problems list is not trusted
        d = copy.deepcopy(doc)
        d["ephemeris_requirement"]["manifest_readback"]["ephemeris"]["backend"] = "moshier"
        assert any("not 'swieph'" in p for p in P(d))
        d = copy.deepcopy(doc)
        d["ephemeris_requirement"]["manifest_readback"] = "not read yet"
        assert any("manifest_readback is missing" in p for p in P(d))
        d = copy.deepcopy(doc)
        del d["ephemeris_requirement"]
        assert any("ephemeris_requirement is missing" in p for p in P(d))

    def test_the_moon_and_every_consumed_body_must_be_covered_by_the_opened_files(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        P = lambda d: stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND)       # noqa: E731
        d = copy.deepcopy(doc)
        del d["ephemeris_requirement"]["manifest_readback"]["ephemeris"]["files"]["semo_18.se1"]     # no lunar file
        assert any("lacks ['semo_18.se1']" in p for p in P(d))
        d = copy.deepcopy(doc)
        d["ephemeris_requirement"]["consumed_bodies"] = [b for b in REQUIRED_CONSUMED_BODIES if b != "Moon"]
        assert any("omits ['Moon']" in p for p in P(d))
        d = copy.deepcopy(doc)
        d["ephemeris_requirement"]["horizon"] = {"start": "1997-12-31", "end": "2400-01-02"}      # runs into the next 600-year block
        assert any("sepl_24.se1" in p for p in P(d))
        assert required_ephemeris_files(["Moon", "Sun"], 1998, 2026) == {"sepl_18.se1", "semo_18.se1"}
        assert required_ephemeris_files(["Sun"], 1790, 1810) == {"sepl_12.se1", "sepl_18.se1"}

    def test_an_empty_but_well_keyed_freeze_is_refused(self, tmp_path):
        """Codex R9-8: every key present, status FROZEN, correct code hashes, canonical command — inputs {} and nulls — returned []."""
        doc, _ = make_stage1(tmp_path)
        hollow = {k: doc[k] for k in ("artifact", "run_id", "generation", "status", "code", "extract_generation_args",
                                      "extract_generation_command")}
        hollow.update({"amendments_draft": {}, "addendum": {}, "registries_selected": {}, "orb_state": {}, "conventions": {"tie_tolerance": 1e-9},
                       "ephemeris_requirement": None, "cohort": {}, "controls": {}, "thresholds": {}, "rerun_policy": "none",
                       "inputs": {}, "tolerances_and_conversions": {}, "extract_environment": "", "coverage_manifest": ""})
        probs = stage1_problems(hollow, tmp_path, dx.CANONICAL_COMMAND)
        assert probs, "an empty freeze must not validate"
        for needle in ("inputs.event_registry", "inputs.random_controls", "ephemeris_requirement is missing", "cohort.held_out",
                       "thresholds.t_cover", "conventions.si_mapping"):
            assert any(needle in x for x in probs), needle
        stub = copy.deepcopy(hollow)
        stub["ephemeris_requirement"] = {"manifest_readback": {"ephemeris_problems": []}}                 # the review's second case
        assert any("no `ephemeris` component" in x for x in stage1_problems(stub, tmp_path, dx.CANONICAL_COMMAND))

    def test_every_mandatory_input_identity_is_required_and_unknown_ones_are_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        for ident in INPUT_FILES:
            d = copy.deepcopy(doc)
            del d["inputs"][ident]
            assert any(f"inputs.{ident} needs a path and a sha256" in x for x in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))
        d = copy.deepcopy(doc)
        d["inputs"]["whatever"] = d["inputs"]["event_registry"]
        assert any("not a known input identifier" in x for x in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))

    def test_typed_fields(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        for path, bad, needle in [(("cohort", "held_out"), "47", "cohort.held_out"), (("cohort", "chart_id"), "x", "cohort.chart_id"),
                                  (("controls", "seed"), "482012", "controls.seed"), (("generation",), "5.0", "measurable candidate"),
                                  (("tolerances_and_conversions", "enumeration_budget"), 0, "enumeration_budget"),
                                  (("extract_generation_args", "pinned_at"), "tomorrow", "ISO date")]:
            d = copy.deepcopy(doc)
            tgt = d
            for k in path[:-1]:
                tgt = tgt[k]
            tgt[path[-1]] = bad
            assert any(needle in x for x in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND)), path

    def test_missing_required_fields_are_listed(self, tmp_path):
        assert any("cohort is missing" in p for p in stage1_problems({"status": "FROZEN"}, tmp_path, dx.CANONICAL_COMMAND))


class TestStage2:
    def seal(self, tmp_path, s1p, extract, **over):
        doc = {"artifact": "FREEZE_STAGE2", "run_id": "t", "stage1_sha256": sha256_file(s1p),
               "extracts": {extract.name: {"sha256": sha256_file(extract), "row_count": 1}}}
        doc.update(over)
        return write_json(tmp_path / "FREEZE_STAGE2_t.json", doc)

    def test_ok_then_every_refusal(self, tmp_path):
        s1, s1p = make_stage1(tmp_path)
        ex = write_json(tmp_path / "baseline_4_1_extract_v1_0.json", {"rows": []})
        require_stage2(self.seal(tmp_path, s1p, ex), s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="does not exist"):
            require_stage2(tmp_path / "missing.json", s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="no record for extract"):
            require_stage2(self.seal(tmp_path, s1p, ex, extracts={}), s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="differs from the sealed"):
            require_stage2(self.seal(tmp_path, s1p, ex, extracts={ex.name: {"sha256": "0" * 64}}), s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="THIS Stage-1"):
            require_stage2(self.seal(tmp_path, s1p, ex, stage1_sha256="0" * 64), s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="run_id"):
            require_stage2(self.seal(tmp_path, s1p, ex, run_id="other"), s1p, s1, ex)
        with pytest.raises(FreezeRefused, match="placeholder"):
            require_stage2(self.seal(tmp_path, s1p, ex, note="<<TBD>>"), s1p, s1, ex)

    def test_an_extract_edited_after_the_seal_is_refused(self, tmp_path):
        s1, s1p = make_stage1(tmp_path)
        ex = write_json(tmp_path / "baseline_4_1_extract_v1_0.json", {"rows": []})
        s2 = self.seal(tmp_path, s1p, ex)
        ex.write_text(json.dumps({"rows": [{"x": 1}]}))
        with pytest.raises(FreezeRefused, match="differs from the sealed"):
            require_stage2(s2, s1p, s1, ex)


class FakeCursor:
    def __init__(self, conn): self.conn = conn
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=()): self.conn.executed.append((sql, params)); self.last = sql
    def fetchone(self):
        if "sign_mismatch" in self.last:
            return self.conn.sign
        if "input_generation_vector" in self.last or "kala_gochara_coverage" in self.last:
            return None
        return (self.conn.outside,)
    def fetchall(self):
        if "ashtakavarga_bindu_contributor" in self.last:
            return self.conn.av
        if "kala_gochara_coverage" in self.last:
            return self.conn.coverage
        return self.conn.manifest if "input_generation_vector" in self.last else self.conn.rows


class FakeConn:
    def __init__(self, rows, outside=0, sign=(0, 0), manifest=None, coverage=None, av=None):
        self.rows, self.outside, self.executed, self.read_only, self.closed = rows, outside, [], False, False
        self.sign, self.manifest, self.coverage, self.av = sign, manifest or [], coverage or [], av or []
    def cursor(self): return FakeCursor(self)
    def rollback(self): pass
    def close(self): self.closed = True


D = dt.date
ROWS = [("marriage", D(2010, 1, 1), D(2010, 2, 1), D(2010, 1, 10), decimal.Decimal("0.50"), "gain", False, None, "interval"),
        ("marriage", D(2010, 1, 1), D(2010, 3, 1), D(2010, 1, 20), decimal.Decimal("0.70"), "gain", False, "x", "interval")]


class TestAvDonorRows:
    """The donor-row identity is a NAMED frozen input: which behaviour of the '4.1' chain the run uses, with the live rows reconciled before any window row is read."""

    def test_the_freeze_without_the_block_is_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        d = copy.deepcopy(doc); del d["av_donor_rows"]
        assert any("av_donor_rows is missing" in p for p in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))

    @pytest.mark.parametrize("mut,needle", [
        (lambda a: a.update(behaviour="whatever"), "is not one of"),
        (lambda a: a["per_ayanamsha"]["lahiri_chitrapaksha"].update(row_count=0, digest=None), "has no donor rows"),
        (lambda a: a.update(behaviour="sign_grain_interim"), "donor rows EXIST"),
        (lambda a: a["per_ayanamsha"]["raman"].update(digest=None), "no sha256 digest"),
        (lambda a: a["per_ayanamsha"]["raman"].update(row_count=0), "digest must be null"),
        (lambda a: a["per_ayanamsha"].pop("lahiri_chitrapaksha"), "lacks the candidate's own ayanamsha"),
        (lambda a: a.update(per_ayanamsha={}), "missing or empty"),
        (lambda a: a.update(comparability=""), "comparability"),
        (lambda a: a["per_ayanamsha"]["raman"].update(row_count="672"), "not a non-negative integer")])
    def test_each_inconsistency_is_named(self, tmp_path, mut, needle):
        doc, _ = make_stage1(tmp_path)
        d = copy.deepcopy(doc); mut(d["av_donor_rows"])
        assert any(needle in p for p in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND)), stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND)

    def test_the_interim_behaviour_with_no_rows_is_a_valid_freeze_and_a_different_candidate(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        d = copy.deepcopy(doc)
        d["av_donor_rows"] = {"behaviour": "sign_grain_interim", "comparability": "different candidate from any donor-resolved run",
                              "per_ayanamsha": {"lahiri_chitrapaksha": {"row_count": 0, "digest": None}}}
        assert stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND) == []

    def test_the_read_back_reports_count_and_digest_per_ayanamsha(self):
        out = dx.read_av_donor_identity(FakeConn(ROWS, av=[("lahiri_chitrapaksha", 672, SHA), ("raman", 0, None)]))
        assert out["per_ayanamsha"] == {"lahiri_chitrapaksha": {"row_count": 672, "digest": SHA}, "raman": {"row_count": 0, "digest": None}}


class TestEphemerisComponent:
    def test_the_am16_component_passes(self):
        assert dx.ephemeris_component_problems(GOOD_EPH) == []

    def test_a_manifest_without_the_component_is_not_an_identity(self):
        assert any("predates AM-16" in p for p in dx.ephemeris_component_problems(None))

    @pytest.mark.parametrize("mut,needle", [
        ({"files": {}}, "files is empty"), ({"files": {"sepl_18.se1": "short"}}, "no sha256"),
        ({"files": {"ephemeris.bin": SHA}}, "not a Swiss ephemeris"), ({"backend": "moshier"}, "not 'swieph'"),
        ({"swe_version": ""}, "swe_version is empty"), ({"library_sha256": "abc"}, "library_sha256 is not a sha256"),
        ({"probe_digest": None}, "probe_digest is not a sha256"), ({"platform": ""}, "platform is empty"),
        ({"runtime": {"swisseph_sha256": SHA}}, "outside the AM-16 definition")])
    def test_each_defect_is_named(self, mut, needle):
        assert any(needle in p for p in dx.ephemeris_component_problems({**GOOD_EPH, **mut}))

    def test_every_missing_key_is_named(self):
        for k in dx.EPHEMERIS_KEYS:
            c = {kk: v for kk, v in GOOD_EPH.items() if kk != k}
            assert any(f"lacks key {k!r}" in p for p in dx.ephemeris_component_problems(c))

    def test_the_manifest_read_back_carries_the_verdict(self):
        ok = dx.read_manifest_orb(FakeConn(ROWS, manifest=[("candidate", 5.0, "r", GOOD_EPH)]), "4.1")
        assert ok["ephemeris_problems"] == [] and ok["ephemeris"] == GOOD_EPH
        old = dx.read_manifest_orb(FakeConn(ROWS, manifest=[("candidate", 5.0, "r", None)]), "4.1")
        assert old["ephemeris_problems"] and old["ephemeris"] is None


class TestDump:
    def test_sql_is_a_single_read_only_select_with_a_total_order(self):
        assert dx.SQL_DUMP.lstrip().upper().startswith("SELECT")
        order = dx.SQL_DUMP.split("ORDER BY")[1]
        for col in ("event_class", "ws", "we", "pk", "si", "valence", "adv", "resolution", "temporal_shape"):
            assert col in order
        for bad in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "GRANT"):
            assert bad not in (dx.SQL_DUMP + dx.SQL_HORIZON).upper()

    def test_rows_are_rendered_deterministically_in_the_pinned_layout(self):
        conn = FakeConn(ROWS)
        rows = dx.dump_rows(conn, "4.1", horizon_check=True)
        assert conn.read_only is True
        assert rows[0] == {"event_class": "marriage", "ws": "2010-01-01", "we": "2010-02-01", "pk": "2010-01-10", "si": 0.5,
                           "valence": "gain", "adv": False, "resolution": None, "temporal_shape": "interval"}
        a, b = dx.render("4.1", "2026-10-05", rows), dx.render("4.1", "2026-10-05", rows)
        assert a == b and not a.endswith(b"\n") and a.startswith(b'{\n "artifact": "baseline_4_1_extract"')
        assert json.loads(a)["row_count"] == 2 and json.loads(a)["predicate"].endswith("generation='4.1'")

    def test_si_is_the_unsigned_raw_intensity_and_the_two_columns_must_reconcile(self):
        assert "raw_intensity AS si" in dx.SQL_DUMP and "signed_intensity AS si" not in dx.SQL_DUMP
        with pytest.raises(RuntimeError, match=r"2 rows with \|signed_intensity\| != raw_intensity"):
            dx.dump_rows(FakeConn(ROWS, sign=(2, 0)), "4.1", horizon_check=True)
        with pytest.raises(RuntimeError, match="1 rows with raw_intensity < 0"):
            dx.dump_rows(FakeConn(ROWS, sign=(0, 1)), "3.0", horizon_check=False)      # the check runs for the baseline too

    def test_manifest_orb_read_touches_no_window_row(self, capsys):
        conn = FakeConn(ROWS, manifest=[("candidate", 5.0, "M-1 fallback no-box x 5.0 deg (unratified)", GOOD_EPH)])
        rc = dx.main(["--generation", "4.1", "--read-manifest-orb"], conn_factory=lambda: conn)
        out = json.loads(capsys.readouterr().out)
        assert rc == 0 and out["orb_max_deg"] == 5.0 and out["orb_ruling"].endswith("(unratified)")
        assert all("kala_gochara_windows" not in sql for sql, _ in conn.executed)
        assert out["ephemeris_problems"] == []
        assert dx.main(["--generation", "5.0", "--read-manifest-orb"], conn_factory=lambda: conn) == 2
        with pytest.raises(RuntimeError, match="exactly one manifest"):
            dx.read_manifest_orb(FakeConn(ROWS, manifest=[]), "4.1")

    def test_coverage_summary_is_disclosure_only_and_says_per_class_year_cells_are_not_derivable(self, capsys):
        cov = [("body_target", 24, 24, 0, 300, 290, 10, ["jupiter", "ketu", "mars", "mercury", "rahu", "saturn", "sun", "venus"])]
        conn = FakeConn(ROWS, coverage=cov)
        assert dx.main(["--generation", "4.1", "--read-coverage-summary"], conn_factory=lambda: conn) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["partition_kinds"]["body_target"]["partitions"] == 24 and out["event_class_partitions"] == 0
        assert out["per_class_year_cells_derivable"] is False
        assert all("kala_gochara_windows" not in sql for sql, _ in conn.executed)
        assert "event_class" not in dx.SQL_COVERAGE_SUMMARY.split("WHERE")[1]          # no class mapping is invented here

    def test_horizon_violation_stops(self):
        with pytest.raises(RuntimeError, match="outside the scored horizon"):
            dx.dump_rows(FakeConn(ROWS, outside=3), "4.1", horizon_check=True)

    def test_refuses_without_a_freeze_and_for_governed_generations(self, tmp_path, capsys):
        out = tmp_path / "o.json"
        base = ["--pinned-at", "2026-10-05", "--out", str(out)]
        assert dx.main(["--generation", "4.1", *base], conn_factory=lambda: FakeConn(ROWS)) == 2
        assert dx.main(["--generation", "5.0", "--stage1", "x", *base], conn_factory=lambda: FakeConn(ROWS)) == 2
        assert "eval-window reader" in capsys.readouterr().err
        assert not out.exists()

    def test_refuses_while_the_freeze_has_placeholders(self, tmp_path, capsys):
        doc, p = make_stage1(tmp_path)
        doc["code"]["adapter_commit"] = "<<FILL_AT_MERGE>>"
        write_json(p, doc)
        out = tmp_path / "o.json"
        created = []
        rc = dx.main(["--generation", "4.1", "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", str(out)],
                     conn_factory=lambda: created.append(1) or FakeConn(ROWS))
        assert rc == 2 and not out.exists() and created == []          # never even connected
        assert "placeholder" in capsys.readouterr().err

    def test_a_verified_freeze_dumps_and_closes(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        doc, p = make_stage1(tmp_path)
        conn = conn_for(doc)
        rc = dx.main(["--generation", "4.1", "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", OUT],
                     conn_factory=lambda: conn)
        assert rc == 0 and conn.closed and json.loads((tmp_path / OUT).read_text())["row_count"] == 2

    @pytest.mark.parametrize("flag,value", [("--pinned-at", "2026-10-06"), ("--out", "elsewhere.json")])
    def test_the_actual_invocation_must_be_the_frozen_command(self, tmp_path, monkeypatch, capsys, flag, value):
        monkeypatch.chdir(tmp_path)
        doc, p = make_stage1(tmp_path)
        argv = {"--generation": "4.1", "--stage1": str(p), "--pinned-at": "2026-10-05", "--out": OUT, flag: value}
        created = []
        rc = dx.main([x for kv in argv.items() for x in kv], conn_factory=lambda: created.append(1) or conn_for(doc))
        assert rc == 2 and created == [] and "does not match the frozen command" in capsys.readouterr().err
        assert not (tmp_path / "elsewhere.json").exists()

    def test_a_manifest_that_changed_since_the_freeze_is_refused_before_any_window_row_is_read(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        doc, p = make_stage1(tmp_path)
        rb = doc["ephemeris_requirement"]["manifest_readback"]
        other = {**GOOD_EPH, "library_sha256": "cd" * 32}
        conn = FakeConn(ROWS, manifest=[(rb["manifest_status"], rb["orb_max_deg"], rb["orb_ruling"], other)])
        rc = dx.main(["--generation", "4.1", "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=lambda: conn)
        assert rc == 2 and "live manifest differs" in capsys.readouterr().err
        assert not (tmp_path / OUT).exists() and all("kala_gochara_windows" not in sql for sql, _ in conn.executed)

    def test_donor_rows_that_appeared_after_the_freeze_make_a_different_candidate_and_are_refused(self, tmp_path, monkeypatch, capsys):
        """The freeze said 'sign_grain_interim' (no donor rows); the live database now HAS them (or the digest moved): the run is refused before any window row is read."""
        monkeypatch.chdir(tmp_path)
        doc, p = make_stage1(tmp_path)
        rb = doc["ephemeris_requirement"]["manifest_readback"]
        moved = [("lahiri_chitrapaksha", 672, "cd" * 32), ("raman", 672, SHA[::-1])]
        conn = FakeConn(ROWS, manifest=[(rb["manifest_status"], rb["orb_max_deg"], rb["orb_ruling"], rb["ephemeris"])], av=moved)
        rc = dx.main(["--generation", "4.1", "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=lambda: conn)
        assert rc == 2 and "ashtakavarga_bindu_contributor rows differ from the frozen" in capsys.readouterr().err
        assert not (tmp_path / OUT).exists() and all("kala_gochara_windows" not in sql for sql, _ in conn.executed)

    def test_the_cli_reads_back_the_donor_row_identity(self, capsys):
        conn = FakeConn(ROWS, av=[("lahiri_chitrapaksha", 672, SHA)])
        assert dx.main(["--generation", "4.1", "--read-av-donor-rows"], conn_factory=lambda: conn) == 0
        assert json.loads(capsys.readouterr().out)["per_ayanamsha"]["lahiri_chitrapaksha"] == {"row_count": 672, "digest": SHA}

    def test_bind_dump_run_names_each_mismatch(self, tmp_path):
        doc, _ = make_stage1(tmp_path)
        assert bind_dump_run(doc, generation="4.1", stage1="x/FREEZE_STAGE1_t.json", pinned_at="2026-10-05", out=OUT) == []
        assert len(bind_dump_run(doc, generation="5.0", stage1="x/other.json", pinned_at=None, out=None)) == 4

    def test_requalify_3_0_reports_the_byte_comparison(self, tmp_path):
        out = tmp_path / "o.json"
        rc = dx.main(["--generation", "3.0", "--pinned-at", "2026-09-29", "--out", str(out), "--requalify-3-0", "0" * 64],
                     conn_factory=lambda: FakeConn(ROWS))
        assert rc == 1
        want = hashlib.sha256(out.read_bytes()).hexdigest()
        assert dx.main(["--generation", "3.0", "--pinned-at", "2026-09-29", "--out", str(out), "--requalify-3-0", want],
                       conn_factory=lambda: FakeConn(ROWS)) == 0
        assert dx.main(["--generation", "4.1", "--pinned-at", "x", "--out", str(out), "--requalify-3-0", want],
                       conn_factory=lambda: FakeConn(ROWS)) == 2

    def test_requalify_compares_the_row_multiset_when_the_pinned_order_was_database_defined(self, tmp_path):
        pinned = tmp_path / "pinned.json"
        rows = dx.dump_rows(FakeConn(ROWS), "3.0", horizon_check=False)
        pinned.write_bytes(dx.render("3.0", "2026-09-29", list(reversed(rows))))      # same rows, other order
        out = tmp_path / "o.json"
        argv = ["--generation", "3.0", "--pinned-at", "2026-09-29", "--out", str(out), "--requalify-3-0",
                hashlib.sha256(pinned.read_bytes()).hexdigest(), "--compare-to", str(pinned)]
        assert dx.main(argv, conn_factory=lambda: FakeConn(ROWS)) == 0           # rows identical -> ok although bytes differ
        pinned.write_bytes(dx.render("3.0", "2026-09-29", rows[:1]))             # a row missing -> fail
        assert dx.main(argv, conn_factory=lambda: FakeConn(ROWS)) == 1

    @needs_campaign
    def test_the_layout_reproduces_the_pinned_3_0_file_byte_for_byte(self):
        doc = json.loads(EXTRACT_3_0.read_bytes())
        blob = dx.render("3.0", doc["pinned_at"], doc["rows"])
        assert hashlib.sha256(blob).hexdigest() == EXTRACT_3_0_PIN


class TestCli:
    def reg_ext(self, tmp_path, predicate="kala_gochara_windows where chart_id='x' and generation='3.0'"):
        reg = write_json(tmp_path / "reg.json", synth_registry())
        rows = [{"event_class": "career_advancement", "ws": "2010-04-01", "we": "2010-07-01", "pk": "2010-05-20", "si": 0.9,
                 "valence": "gain", "adv": False, "resolution": None, "temporal_shape": "interval"},
                {"event_class": "relocation", "ws": "2015-03-01", "we": "2015-04-01", "pk": "2015-03-10", "si": None,
                 "valence": "gain", "adv": False, "resolution": None, "temporal_shape": "interval"}]
        ex = write_json(tmp_path / "e.json", {"predicate": predicate, "rows": rows})
        return reg, ex

    def test_measurement_without_both_stages_is_refused_and_writes_a_refusal(self, tmp_path):
        reg, ex = self.reg_ext(tmp_path, "kala_gochara_windows ... generation='4.1'")
        out = tmp_path / "r.json"
        assert run(["--registry", str(reg), "--extract", str(ex), "--output", str(out)]) == 1
        assert json.loads(out.read_text())["mode"] == "REFUSED"

    def test_dry_run_refuses_a_candidate_extract(self, tmp_path):
        for gen in ("4.1", "5.0"):
            reg, ex = self.reg_ext(tmp_path, f"kala_gochara_windows where generation='{gen}'")
            out = tmp_path / f"r{gen}.json"
            assert run(["--registry", str(reg), "--extract", str(ex), "--output", str(out), "--baseline-dry-run",
                        "--declared-pin", "0" * 64]) == 1
            r = json.loads(out.read_text())
            assert r["mode"] == "REFUSED" and "t_cover" not in r            # the candidate was never scored

    def test_dry_run_needs_the_pin_and_scores_a_baseline_with_unknowns_reported(self, tmp_path):
        reg, ex = self.reg_ext(tmp_path)
        out = tmp_path / "r.json"
        assert run(["--registry", str(reg), "--extract", str(ex), "--output", str(out), "--baseline-dry-run"]) == 1
        pin = sha256_file(ex)
        assert run(["--registry", str(reg), "--extract", str(ex), "--output", str(out), "--baseline-dry-run",
                    "--declared-pin", pin]) == 0
        r = json.loads(out.read_text())
        assert r["mode"] == "BASELINE_DRY_RUN" and r["generation"] == "3.0" and r["extract_sha256"]["match"] is True
        assert r["unknown_competitors"]["unknown_rows"] == 1 and r["t_cover"]["hits"] == 2

    def frozen_run(self, tmp_path, predicate="kala_gochara_windows ... generation='4.1'"):
        """A measurement whose registry, controls and extract ARE the frozen ones (synthetic registry: 2 held-out events)."""
        from services.gochara_eval import load_registry
        from services.gochara_eval.candidate import load_candidate_extract
        from services.gochara_eval.controls import CONTROLS_SEED, draw_controls
        reg0, ex0 = self.reg_ext(tmp_path, predicate)
        reg = tmp_path / INPUT_FILES["event_registry"]
        reg.write_bytes(reg0.read_bytes())
        ex = tmp_path / OUT
        ex.write_bytes(ex0.read_bytes())
        from services.gochara_eval.extract import load_extract
        ctl_doc = {"seed": CONTROLS_SEED, "controls": [{k: v for k, v in c.items() if not k.startswith("_")}
                                                       for c in draw_controls(load_registry(reg), load_candidate_extract(ex))]}
        ctl = write_json(tmp_path / INPUT_FILES["random_controls"], ctl_doc)
        doc, s1p = make_stage1(tmp_path, cohort={"held_out": 2, "timing_usable": 1, "year_grain": 1, "exact_cohort": 1,
                                                 "interval_grain": 0, "chart_id": "482012f1-710e-4a25-994a-93821f5871aa"})
        s2 = write_json(tmp_path / "FREEZE_STAGE2_t.json", {"run_id": "t", "stage1_sha256": sha256_file(s1p),
                        "extracts": {ex.name: {"sha256": sha256_file(ex)}}})
        argv = ["--registry", str(reg), "--extract", str(ex), "--controls", str(ctl), "--stage1", str(s1p), "--stage2", str(s2)]
        return doc, argv, ex

    def test_full_measurement_path_with_both_stages(self, tmp_path):
        doc, argv, ex = self.frozen_run(tmp_path)
        out = tmp_path / "r.json"
        assert run([*argv, "--output", str(out)]) == 0
        r = json.loads(out.read_text())
        assert r["mode"] == "MEASUREMENT" and r["generation"] == "4.1" and r["freeze"]["status"] == "VERIFIED"
        ex.write_text(ex.read_text() + " ")                                # edited after the seal -> refused, nothing scored
        assert run([*argv, "--output", str(out)]) == 1
        assert "t_cover" not in json.loads(out.read_text())

    def test_the_run_is_bound_to_the_frozen_registry_controls_generation_and_budget(self, tmp_path):
        doc, argv, ex = self.frozen_run(tmp_path)
        out = tmp_path / "r.json"
        # a different registry file (same name, other bytes) is not the frozen one
        reg = Path(argv[1])
        original = reg.read_bytes()
        reg.write_text(json.dumps({**json.loads(original), "version": "tampered"}))
        assert run([*argv, "--output", str(out)]) == 1
        assert "event_registry" in json.dumps(json.loads(out.read_text())["freeze"]["problems"])
        reg.write_bytes(original)
        # no controls supplied
        argv2 = [a for i, a in enumerate(argv) if a != "--controls" and (i == 0 or argv[i - 1] != "--controls")]
        assert run([*argv2, "--output", str(out)]) == 1
        assert "random_controls" in json.dumps(json.loads(out.read_text())["freeze"]["problems"])
        # a budget other than the frozen one
        assert run([*argv, "--budget", "7", "--output", str(out)]) == 1
        assert "enumeration budget" in json.dumps(json.loads(out.read_text())["freeze"]["problems"])
        assert run([*argv, "--budget", "400000", "--output", str(out)]) == 0

    def test_bind_scoring_run_catches_generation_cohort_and_extract_name(self, tmp_path):
        doc, argv, ex = self.frozen_run(tmp_path)
        reg, ctl = Path(argv[1]), Path(argv[5])
        base = dict(registry_path=reg, controls_path=ctl, extract_path=ex, extract_header_predicate="kala ... generation='4.1'",
                    registry_held_out=2, budget=None)
        assert bind_scoring_run(doc, tmp_path, **base) == []
        assert any("does not name generation" in x for x in bind_scoring_run(doc, tmp_path, **{**base, "extract_header_predicate": "generation='3.0'"}))
        assert any("held-out events" in x for x in bind_scoring_run(doc, tmp_path, **{**base, "registry_held_out": 47}))
        other = tmp_path / "other_extract.json"
        other.write_bytes(ex.read_bytes())
        assert any("not the frozen output" in x for x in bind_scoring_run(doc, tmp_path, **{**base, "extract_path": other}))

    @needs_campaign
    def test_dry_run_on_the_real_3_0_extract_reproduces_the_recorded_numbers(self, tmp_path):
        out = tmp_path / "r.json"
        assert run(["--registry", str(REGISTRY_V2_3), "--extract", str(EXTRACT_3_0), "--controls",
                    str(CAMPAIGN_MEASUREMENT / "random_controls_v1_3.json"), "--output", str(out), "--baseline-dry-run",
                    "--declared-pin", EXTRACT_3_0_PIN]) == 0
        r = json.loads(out.read_text())
        rec = json.loads((CAMPAIGN_MEASUREMENT / "rerun_result_v2_3.json").read_text())
        assert (r["t_cover"]["hits"], r["t_time"]["capped_median_days"], r["t_rank"]["status"]) == (32, 182, "VOID")
        assert r["random_controls"]["total_hits"] == rec["random_controls"]["total_hits"] == 638
        assert r["t_fp"] == rec["t_fp"] and r["t_fp_gain"] == rec["t_fp_gain"] and r["degeneracy"] == rec["degeneracy"]
