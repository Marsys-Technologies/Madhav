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
from services.gochara_eval.freeze import (FROZEN_CODE_FILES, FreezeRefused, code_hashes, require_stage1, require_stage2,
                                          sha256_file, stage1_problems)

from .conftest import (CAMPAIGN_MEASUREMENT, EXTRACT_3_0, EXTRACT_3_0_PIN, REGISTRY_V2_3, needs_campaign, synth_registry,
                       write_json)

COMMIT = "a" * 40
SIDECAR = Path(__file__).resolve().parents[3]


def make_stage1(tmp_path, generation="4.1", inputs=None):
    inp = tmp_path / "in.txt"
    inp.write_text("frozen input")
    args = {"generation": generation, "stage1": "FREEZE_STAGE1_t.json", "pinned_at": "2026-10-05",
            "out": "baseline_4_1_extract_v1_0.json"}
    doc = {"artifact": "FREEZE_STAGE1", "run_id": "t", "generation": generation, "status": "FROZEN",
           "amendments_draft": {"version": "0.21", "sha256": "0" * 64}, "addendum": {"sha256": "0" * 64},
           "registries_selected": {}, "orb_state": "unqualified points",
           "conventions": {"tie_tolerance": 1e-9}, "code": {"adapter_commit": COMMIT, "scorer_commit": COMMIT,
                                                            "files": code_hashes(SIDECAR)},
           "extract_generation_args": args, "extract_generation_command": dx.CANONICAL_COMMAND.format(**args),
           "cohort": {}, "controls": {}, "thresholds": {}, "rerun_policy": "none",
           "inputs": inputs if inputs is not None else {"in": {"path": "in.txt", "sha256": sha256_file(inp)}}}
    return doc, write_json(tmp_path / "FREEZE_STAGE1_t.json", doc)


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
        (tmp_path / "in.txt").write_text("changed after the freeze")
        assert any("sha256 mismatch" in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_missing_input_file_is_refused(self, tmp_path):
        doc, _ = make_stage1(tmp_path, inputs={"gone": {"path": "gone.txt", "sha256": "0" * 64}})
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

    def test_missing_required_fields_are_listed(self, tmp_path):
        assert any("missing required field 'cohort'" in p
                   for p in stage1_problems({"status": "FROZEN"}, tmp_path, dx.CANONICAL_COMMAND))


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
    def fetchone(self): return (self.conn.outside,)
    def fetchall(self): return self.conn.rows


class FakeConn:
    def __init__(self, rows, outside=0):
        self.rows, self.outside, self.executed, self.read_only, self.closed = rows, outside, [], False, False
    def cursor(self): return FakeCursor(self)
    def rollback(self): pass
    def close(self): self.closed = True


D = dt.date
ROWS = [("marriage", D(2010, 1, 1), D(2010, 2, 1), D(2010, 1, 10), decimal.Decimal("0.50"), "gain", False, None, "interval"),
        ("marriage", D(2010, 1, 1), D(2010, 3, 1), D(2010, 1, 20), decimal.Decimal("0.70"), "gain", False, "x", "interval")]


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

    def test_a_verified_freeze_dumps_and_closes(self, tmp_path):
        doc, p = make_stage1(tmp_path)
        out = tmp_path / "o.json"
        conn = FakeConn(ROWS)
        rc = dx.main(["--generation", "4.1", "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", str(out)],
                     conn_factory=lambda: conn)
        assert rc == 0 and conn.closed and json.loads(out.read_text())["row_count"] == 2

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

    def test_full_measurement_path_with_both_stages(self, tmp_path):
        reg, ex = self.reg_ext(tmp_path, "kala_gochara_windows ... generation='4.1'")
        ex4 = tmp_path / "baseline_4_1_extract_v1_0.json"
        ex4.write_bytes(ex.read_bytes())
        s1, s1p = make_stage1(tmp_path)
        s2 = write_json(tmp_path / "FREEZE_STAGE2_t.json", {"run_id": "t", "stage1_sha256": sha256_file(s1p),
                        "extracts": {ex4.name: {"sha256": sha256_file(ex4)}}})
        out = tmp_path / "r.json"
        assert run(["--registry", str(reg), "--extract", str(ex4), "--output", str(out), "--stage1", str(s1p),
                    "--stage2", str(s2)]) == 0
        r = json.loads(out.read_text())
        assert r["mode"] == "MEASUREMENT" and r["generation"] == "4.1" and r["freeze"]["status"] == "VERIFIED"
        ex4.write_text(ex4.read_text() + " ")                                # edited after the seal -> refused, nothing scored
        assert run(["--registry", str(reg), "--extract", str(ex4), "--output", str(out), "--stage1", str(s1p),
                    "--stage2", str(s2)]) == 1
        assert "t_cover" not in json.loads(out.read_text())

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
