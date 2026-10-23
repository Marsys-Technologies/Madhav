"""J-5q: the governed generation '5.0' reaches the scorer — extract, freeze, measurement (FIXTURE tests; no stored chart value is read).

Every row below is a FIXTURE built in the test (marked FIXTURE): none is a window of the native's chart, and no figure here is a measurement of a
generation. Oracles cite their source: SI addendum v1.5 §1 (`si := evidence_for` for 5.x) and §3 (a NULL is not zero; it stays an explicit null that
remains in the candidate set); protocol v2.3 §1 (scored horizon 1998-01-01..2026-04-17), §3 (IST calendar days); `window_sweep.draft_windows`
(`window_qualification/1`: an unqualified window stores no number, and says why); migration 1156 (`outcome_valence_for_native` enum).
"""
from __future__ import annotations

import copy
import datetime as dt
import json

import pytest

from services.gochara_eval import dump_extract as dx
from services.gochara_eval.candidate import NO_REASON_STORED, load_candidate_extract_bytes
from services.gochara_eval.candidate_score import run
from services.gochara_eval.freeze import require_stage1, sha256_file, stage1_problems

from .conftest import synth_registry, write_json
from .test_freeze_and_dump import (CHART_ID, GOOD_EPH, INPUT_FILES, OUT, SHA, FakeConn, FakeCursor, make_stage1)

D = dt.date
POLICY = "window_qualification/1"
REASON = "dynamic_objective_solver_guarantee_not_available"
# FIXTURE rows in the order the SQL returns them: (event_class, ws, we, pk, si, outcome_valence_for_native, path_id, null_reason)
GOV_ROWS = [
    ("career_advancement", D(2010, 4, 1), D(2010, 7, 1), D(2010, 5, 20), 0.9, "favourable", "P3", None),
    ("relocation", D(2015, 3, 1), D(2015, 4, 1), None, None, "unqualified", "P4", REASON),
    ("relocation", D(2015, 5, 1), D(2015, 5, 9), None, None, "unqualified", "P1", None),
]
MANIFEST = ("candidate", POLICY, GOOD_EPH, {"admission_digest": SHA, "activity": {"jupiter": 1}}, SHA[::-1],
            {"geometry": SHA, "evaluation": SHA[::-1], "window": SHA})


class GovCursor(FakeCursor):
    def fetchone(self):
        if "COUNT(*) FROM public.ka_gochara_eval_window" in self.last:
            return (self.conn.total,)
        return super().fetchone()

    def fetchall(self):
        if "FROM public.ka_gochara_eval_window" in self.last:
            return self.conn.gov_rows
        return super().fetchall()


class GovConn(FakeConn):
    def __init__(self, rows=GOV_ROWS, total=None, manifest=(MANIFEST,)):
        super().__init__([], manifest=list(manifest))
        self.gov_rows, self.total = list(rows), len(rows) + 2 if total is None else total

    def cursor(self):
        return GovCursor(self)


def ro(conn):
    dx.configure_read_only_snapshot(conn)
    return conn


def governed_stage1(tmp_path, **override):
    """A SUBSTANTIVE governed Stage-1 freeze: the 4.x chain's blocks (donor rows, daśā plurality, orb state) are absent by design."""
    doc, _ = make_stage1(tmp_path, generation="5.0")
    for k in ("av_donor_rows", "dasha_plurality_tier_policy", "orb_state"):
        doc.pop(k)
    status, policy, eph, orb, registry_digest, impl = MANIFEST
    doc["ephemeris_requirement"]["manifest_readback"] = {
        "generation": "5.0", "manifest_status": status, "result_policy": policy, "ephemeris": eph, "orb_policy": orb,
        "registry_digest": registry_digest, "implementation": impl, "ephemeris_problems": []}
    doc["registries_selected"]["governed_registry_rows"] = "ka_gochara_rule_path (sealed rule versions)"
    doc.update(override)
    return doc, write_json(tmp_path / "FREEZE_STAGE1_t.json", doc)


# ── the extract: stored columns -> the adapter's row ─────────────────────────────────────────────────────────────────────────────

class TestGovernedExtract:
    def test_the_sql_is_one_read_only_select_scoped_to_one_chart_with_a_total_order(self):
        text = " ".join(dx.SQL_GOVERNED_DUMP.upper().split())
        assert text.startswith("SELECT") and ";" not in text
        for verb in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "CREATE", "DROP", "GRANT", "LOCK", "COPY"):
            assert f" {verb} " not in f" {text} "
        assert "W.CHART_ID = %S AND W.GENERATION = %S" in text
        order = [c.strip() for c in dx.SQL_GOVERNED_DUMP.split("ORDER BY")[1].split(",")]
        assert order == dx.GOVERNED_COLUMNS          # every selected column, in the selected order: a TOTAL order (the file hash is stable)

    def test_si_is_evidence_for_and_a_null_stays_null_with_its_stored_reason(self):
        """SI addendum §1/§3: `si := evidence_for`; a NULL is an explicit null, never 0, and the row keeps the window's stored reason."""
        rows, extra = dx.dump_governed(ro(GovConn()), "5.0", chart_id=CHART_ID)
        assert [r["si"] for r in rows] == [0.9, None, None] and [r["pk"] for r in rows] == ["2010-05-20", None, None]
        assert rows[1]["null_reason"] == REASON and rows[2]["null_reason"] is None
        assert [r["outcome_valence_for_native"] for r in rows] == ["favourable", "unqualified", "unqualified"]    # the governed enum, never gain/loss
        assert extra["null_census"]["si_null"] == 2 and extra["null_census"]["si_null_without_reason"] == 1
        assert extra["null_census"]["si_null_reasons"] == {REASON: 1}
        assert extra["windows_stored"] == 5 and extra["windows_outside_scored_horizon_excluded"] == 2

    def test_the_rendered_extract_loads_in_the_candidate_adapter_and_the_unknowns_keep_their_reasons(self):
        rows, extra = dx.dump_governed(ro(GovConn()), "5.0", chart_id=CHART_ID)
        blob = dx.render("5.0", "2026-10-21", rows, chart_id=CHART_ID, extra=extra)
        head = json.loads(blob)
        assert head["columns"] == dx.GOVERNED_COLUMNS and head["predicate"] == f"ka_gochara_eval_window where chart_id='{CHART_ID}' and generation='5.0'"
        cext = load_candidate_extract_bytes(blob)
        assert cext.unknown_rows == 2 and cext.row_count == 3
        assert cext.null_reasons == {REASON: 1, NO_REASON_STORED: 1}         # a row with no stored reason is counted apart, not given one
        assert cext.valence_domain == {"favourable": 1, "unqualified": 2}
        # the two unknown relocation windows (Apr 1 and May 1..9) stay in the candidate set as unqualified representatives
        assert sorted((w.ws, w.si, w.pk) for w in cext.merged["relocation"]) == [(D(2015, 3, 1), None, None), (D(2015, 5, 1), None, None)]

    def test_the_4x_layout_is_untouched(self):
        """The 4.x header carries no governed key, so the pinned layouts (and their hashes) do not move."""
        head = json.loads(dx.render("4.1", "2026-10-05", [], chart_id=CHART_ID))
        assert head["columns"] == dx.COLUMNS and "null_census" not in head and head["predicate"].startswith("kala_gochara_windows")


# ── the freeze ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestGovernedFreeze:
    def test_a_governed_freeze_verifies_without_the_4x_blocks(self, tmp_path):
        doc, p = governed_stage1(tmp_path)
        assert require_stage1(p, tmp_path, dx.CANONICAL_COMMAND)["generation"] == "5.0"

    @pytest.mark.parametrize("mut, needle", [
        (lambda rb: rb.update(result_policy="made_up/9"), "result_policy"),
        (lambda rb: rb.pop("result_policy"), "result_policy"),
        (lambda rb: rb.update(registry_digest="short"), "registry_digest"),
        (lambda rb: rb.update(implementation={}), "implementation"),
        (lambda rb: rb.update(implementation={"geometry": "nothex"}), "implementation"),
        (lambda rb: rb.update(orb_policy={}), "orb_policy"),
        (lambda rb: rb.update(manifest_status=""), "manifest_status"),
        (lambda rb: rb.update(ephemeris={**GOOD_EPH, "backend": "moshier"}), "backend"),
    ])
    def test_each_governed_manifest_defect_is_named(self, tmp_path, mut, needle):
        doc, _ = governed_stage1(tmp_path)
        mut(doc["ephemeris_requirement"]["manifest_readback"])
        assert any(needle in p for p in stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND))

    def test_a_4_1_freeze_still_needs_the_4x_blocks_and_a_governed_readback_is_not_a_4_1_readback(self, tmp_path):
        doc, _ = make_stage1(tmp_path)                                    # generation 4.1
        governed, _ = governed_stage1(tmp_path)
        doc["ephemeris_requirement"]["manifest_readback"] = governed["ephemeris_requirement"]["manifest_readback"]
        problems = stage1_problems(doc, tmp_path, dx.CANONICAL_COMMAND)
        assert any("orb_max_deg" in p for p in problems)
        for k in ("av_donor_rows", "orb_state"):
            d = copy.deepcopy(doc)
            d.pop(k)
            assert any(k in p for p in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))
        d = copy.deepcopy(doc)
        d.pop("dasha_plurality_tier_policy")
        assert any("dasha_plurality_tier_policy" in p for p in stage1_problems(d, tmp_path, dx.CANONICAL_COMMAND))


# ── the extract command, end to end on a fake read-only connection ─────────────────────────────────────────────────────────────

class TestGovernedDumpCommand:
    argv = ["--chart-id", CHART_ID, "--generation", "5.0"]

    def test_a_verified_governed_freeze_dumps_the_scored_horizon_and_reads_no_4x_table(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        doc, p = governed_stage1(tmp_path)
        conn = GovConn()
        rc = dx.main([*self.argv, "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=lambda: conn)
        assert rc == 0 and conn.closed
        out = json.loads((tmp_path / OUT).read_text())
        assert out["row_count"] == 3 and out["columns"] == dx.GOVERNED_COLUMNS and out["result_policy"] == POLICY
        assert out["windows_outside_scored_horizon_excluded"] == 2 and out["scored_horizon"] == ["1998-01-01", "2026-04-18"]
        touched = " ".join(sql for sql, _ in conn.executed)
        for table in ("kala_gochara_windows", "chart_dashas", "chart_facts"):
            assert table not in touched

    @pytest.mark.parametrize("field, live", [
        ("result_policy", "all_null_candidate/1"), ("registry_digest", "ab" * 32), ("implementation", {"geometry": "cd" * 32}),
        ("orb_policy", {"activity": {}}), ("manifest_status", "sealed"), ("ephemeris", {**GOOD_EPH, "library_sha256": "cd" * 32})])
    def test_a_manifest_that_changed_since_the_freeze_is_refused_before_any_window_row_is_read(self, tmp_path, monkeypatch, capsys, field, live):
        monkeypatch.chdir(tmp_path)
        doc, p = governed_stage1(tmp_path)
        keys = ("manifest_status", "result_policy", "ephemeris", "orb_policy", "registry_digest", "implementation")
        changed = tuple(live if k == field else v for k, v in zip(keys, MANIFEST))
        conn = GovConn(manifest=(changed,))
        rc = dx.main([*self.argv, "--stage1", str(p), "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=lambda: conn)
        err = capsys.readouterr().err
        assert rc == 2 and "live manifest differs" in err and field in err
        assert not (tmp_path / OUT).exists() and all("ka_gochara_eval_window" not in sql for sql, _ in conn.executed)

    def test_the_4x_only_readbacks_are_refused_for_a_governed_generation(self, capsys):
        for flag in ("--read-av-donor-rows", "--read-dasha-tiers"):
            assert dx.main([*self.argv, flag], conn_factory=lambda: GovConn()) == 2
            assert "4.x chain" in capsys.readouterr().err

    def test_the_manifest_and_coverage_readbacks_work_for_a_governed_generation(self, capsys):
        conn = GovConn()
        assert dx.main([*self.argv, "--read-manifest-orb"], conn_factory=lambda: conn) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["result_policy"] == POLICY and out["ephemeris_problems"] == [] and "orb_max_deg" not in out
        conn = FakeConn([], coverage=[("event_class", 26, 26, 0, 26, 26, 0, ["marriage"])])
        assert dx.main([*self.argv, "--read-coverage-summary"], conn_factory=lambda: conn) == 0
        assert json.loads(capsys.readouterr().out)["per_class_year_cells_derivable"] is True


# ── the measurement: both stages, the frozen registry, a governed extract ────────────────────────────────────────────────────

def test_the_candidate_scorer_measures_a_governed_extract_under_a_verified_governed_freeze(tmp_path):
    """FIXTURE measurement (synthetic registry of 2 held-out events): generation '5.0' is a measurable candidate, the unknown windows are not
    dropped or zero-filled, and the result says why each unknown is unknown."""
    from services.gochara_eval import load_registry
    from services.gochara_eval.controls import CONTROLS_SEED, draw_controls

    reg = tmp_path / INPUT_FILES["event_registry"]
    write_json(reg, synth_registry())
    rows, extra = dx.dump_governed(ro(GovConn()), "5.0", chart_id=CHART_ID)
    ex = tmp_path / OUT
    ex.write_bytes(dx.render("5.0", "2026-10-05", rows, chart_id=CHART_ID, extra=extra))
    ctl_doc = {"seed": CONTROLS_SEED, "controls": [{k: v for k, v in c.items() if not k.startswith("_")}
                                                   for c in draw_controls(load_registry(reg), load_candidate_extract_bytes(ex.read_bytes()))]}
    ctl = write_json(tmp_path / INPUT_FILES["random_controls"], ctl_doc)
    doc, s1p = governed_stage1(tmp_path, cohort={"held_out": 2, "timing_usable": 1, "year_grain": 1, "exact_cohort": 1, "interval_grain": 0,
                                                 "chart_id": CHART_ID})
    s2 = write_json(tmp_path / "FREEZE_STAGE2_t.json", {"run_id": "t", "stage1_sha256": sha256_file(s1p),
                                                        "extracts": {ex.name: {"sha256": sha256_file(ex)}}})
    out = tmp_path / "r.json"
    assert run(["--registry", str(reg), "--extract", str(ex), "--controls", str(ctl), "--stage1", str(s1p), "--stage2", str(s2),
                "--output", str(out)]) == 0
    r = json.loads(out.read_text())
    assert r["mode"] == "MEASUREMENT" and r["generation"] == "5.0" and r["freeze"]["status"] == "VERIFIED"
    assert r["input_adapter"]["unknown_si_rows"] == 2 and r["input_adapter"]["raw_valence_domain"] == {"favourable": 1, "unqualified": 2}
    assert r["unknown_competitors"]["unknown_row_reasons"] == {REASON: 1, NO_REASON_STORED: 1}
    # the freeze names generation 5.0: an extract whose header names another generation is not the frozen one
    other = tmp_path / "other.json"
    other.write_bytes(dx.render("4.1", "2026-10-05", [], chart_id=CHART_ID))
    assert run(["--registry", str(reg), "--extract", str(other), "--controls", str(ctl), "--stage1", str(s1p), "--stage2", str(s2),
                "--output", str(out)]) == 1
