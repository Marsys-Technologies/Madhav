"""C50 — SETTLED-1 intake checker: synthetic captures for every STOP.

The captures are built with the re-pin tool's own `build_capture` and validated by its own
`validate_capture` (the checker reuses both — no rule re-implemented here): each fixture is a
minimal valid capture = the ten permission.py reference rows (ids, lords, parents, instants)
plus one non-reference AD row, the ten natal subjects, and the build/tier/system contract.
"""
import importlib.util
import json
import pathlib
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import dasha_read

_HERE = pathlib.Path(__file__).resolve()
_P = _HERE.parents[3] / "scripts" / "gochara" / "repin_dasha_contract.py"
_spec = importlib.util.spec_from_file_location("repin_dasha_contract_c50", _P)
R = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = R
_spec.loader.exec_module(R)

_C = _HERE.parents[3] / "scripts" / "gochara" / "settled1_intake_check.py"
_spec2 = importlib.util.spec_from_file_location("settled1_intake_check_c50", _C)
C = importlib.util.module_from_spec(_spec2)
sys.modules[_spec2.name] = C
_spec2.loader.exec_module(C)

PERM = R.PERM
TIER = PERM.DASHA_READ_CONTRACT["tier"]
CHART = PERM.DASHA_READ_CONTRACT["chart_id"]
OLD_BUILD = getattr(PERM, "REFERENCE_DASHA_BUILD_ID", None) or PERM.DASHA_READ_CONTRACT["build_id"]
NEW_BUILD = "ca17639b-f3cf-42c7-9866-0a61f3855802"
EXTRA_AD_ID = "22222222-2222-4222-8222-222222222222"
LEVEL_OF = {"MD": 1, "AD": 2, "PD": 3}


def _shift(iso, seconds):
    t = datetime.fromtimestamp(R._t(iso).timestamp() + seconds, tz=timezone.utc)
    return R.full_iso(t)


def _rows(build_id, shift_s=0, extra_lord="Venus", drop_extra=False):
    rows = []
    for ref in PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS:
        rows.append({"dasha_row_id": ref["row_id"], "level_n": LEVEL_OF[ref["level"]],
                     "parent_row_id": ref["parent_row_id"], "lord_graha": ref["lord"],
                     "start_iso": _shift(ref["start_iso"], shift_s),
                     "end_iso": _shift(ref["end_iso"], shift_s),
                     "verification_pass_status": TIER, "system_id": "vimshottari",
                     "build_id": build_id})
    if not drop_extra:
        # a non-reference AD under the same MD (between Ketu and Moon): its lord can flip
        # without tripping the capture-time reference check, so R1 itself is exercised
        md = PERM.MD_ROWS[0]
        rows.append({"dasha_row_id": EXTRA_AD_ID, "level_n": 2,
                     "parent_row_id": md["row_id"], "lord_graha": extra_lord,
                     "start_iso": _shift("2015-01-01T00:00:00Z", shift_s),
                     "end_iso": _shift("2016-01-01T00:00:00Z", shift_s),
                     "verification_pass_status": TIER, "system_id": "vimshottari",
                     "build_id": build_id})
    return rows


def _natal(fact_prefix="fact"):
    return [{"fact_id": f"{fact_prefix}-{s}", "fact_subject": s, "longitude": "123.456",
             "tier": "single", "build_id": OLD_BUILD} for s in R.NATAL_SUBJECTS]


def _capture(tmp_path, name, build_id, rows, natal):
    d = R.build_capture(CHART, build_id, rows, natal)
    p = tmp_path / name
    p.write_text(json.dumps(d, indent=1, sort_keys=True), encoding="utf-8")
    return str(p)


@pytest.fixture()
def good(tmp_path):
    old = _capture(tmp_path, "old.json", OLD_BUILD, _rows(OLD_BUILD), _natal())
    new = _capture(tmp_path, "new.json", NEW_BUILD, _rows(NEW_BUILD, shift_s=6993), _natal())
    return old, new


def _args(old, new, shifts=("1=6993", "2=6993", "3=6993"), tol="5", build=NEW_BUILD):
    out = ["--old", old, "--new", new, "--new-build-id", build, "--tolerance", tol]
    for s in shifts:
        out += ["--expected-shift", s]
    return out


def test_happy_path_every_rule_passes(good, capsys):
    old, new = good
    assert C.main(_args(old, new)) == 0
    out = capsys.readouterr().out
    for rule in ("capture-old", "capture-new", "R5-build-id", "R1-lords-counts",
                 "R2-shift", "R3-level4-allowed", "R4-natal-fact-ids"):
        assert f"PASS {rule}" in out, rule


def test_a_lord_flip_at_a_non_reference_row_stops_R1(good, tmp_path, capsys):
    old, _ = good
    new = _capture(tmp_path, "new2.json", NEW_BUILD,
                   _rows(NEW_BUILD, shift_s=6993, extra_lord="Saturn"), _natal())
    assert C.main(_args(old, new)) == 1
    assert "STOP R1-lords-counts" in capsys.readouterr().out


def test_a_row_count_difference_stops_R1(good, tmp_path, capsys):
    old, _ = good
    new = _capture(tmp_path, "new3.json", NEW_BUILD,
                   _rows(NEW_BUILD, shift_s=6993, drop_extra=True), _natal())
    assert C.main(_args(old, new)) == 1
    assert "STOP R1-lords-counts" in capsys.readouterr().out


def test_an_out_of_tolerance_shift_stops_R2(good, tmp_path, capsys):
    old, _ = good
    new = _capture(tmp_path, "new4.json", NEW_BUILD, _rows(NEW_BUILD, shift_s=7200), _natal())
    assert C.main(_args(old, new)) == 1
    assert "STOP R2-shift" in capsys.readouterr().out


def test_a_shift_the_notice_does_not_expect_stops_R2(good, capsys):
    old, new = good
    assert C.main(_args(old, new, shifts=("1=3600", "2=6993", "3=6993"))) == 1
    assert "STOP R2-shift" in capsys.readouterr().out


def test_a_changed_natal_fact_id_stops_R4(good, tmp_path, capsys):
    old, _ = good
    new = _capture(tmp_path, "new5.json", NEW_BUILD, _rows(NEW_BUILD, shift_s=6993),
                   _natal(fact_prefix="other"))
    assert C.main(_args(old, new)) == 1
    assert "STOP R4-natal-fact-ids" in capsys.readouterr().out


@pytest.mark.parametrize("mutation", ["swap_subject_ids", "duplicate_ids"])
def test_R4_preserves_each_subjects_fact_id_and_requires_ten_distinct_ids(good, tmp_path, capsys, mutation):
    old, new = good
    old_d = json.loads(pathlib.Path(old).read_text())
    new_d = json.loads(pathlib.Path(new).read_text())
    if mutation == "swap_subject_ids":
        a, b = new_d["natal"][:2]
        a["fact_id"], b["fact_id"] = b["fact_id"], a["fact_id"]
    else:
        # Even an unchanged one-id set cannot substantiate "all ten" facts.
        for d in (old_d, new_d):
            for n in d["natal"]:
                n["fact_id"] = "same-id-for-every-subject"
        old = _capture(tmp_path, "duplicate-old.json", OLD_BUILD, old_d["rows"], old_d["natal"])
    new = _capture(tmp_path, "mutated-new.json", NEW_BUILD, new_d["rows"], new_d["natal"])
    assert C.main(_args(old, new)) == 1
    assert "STOP R4-natal-fact-ids" in capsys.readouterr().out


def test_a_build_id_other_than_the_notice_stops(good, capsys):
    old, new = good
    assert C.main(_args(old, new, build="33333333-3333-4333-8333-333333333333")) == 1
    assert "STOP settlement-authority" in capsys.readouterr().out


def test_a_tampered_capture_stops(good, capsys):
    old, new = good
    d = json.loads(pathlib.Path(new).read_text())
    d["rows"][0]["lord_graha"] = "Jupiter"           # a reference row: validation names it
    d["sha256"] = R._capture_digest(d["chart_id"], d["build_id"], d["rows"], d["natal"])
    pathlib.Path(new).write_text(json.dumps(d, indent=1, sort_keys=True))
    assert C.main(_args(old, new)) == 1
    assert "STOP capture-new" in capsys.readouterr().out


def test_a_level4_shift_is_echoed_never_compared(good, capsys):
    old, new = good
    assert C.main(_args(old, new, shifts=("1=6993", "2=6993", "3=6993", "4=41000"))) == 0
    out = capsys.readouterr().out
    assert "PASS R3-level4-allowed" in out and "41000" in out and "never compared" in out


def test_usage_refusals(good):
    old, new = good
    assert C.main(_args(old, new, shifts=("1=6993", "2=6993"))) == 2          # level 3 missing
    assert C.main(_args(old, new, tol="0")) == 2                              # below the tool's floor
    assert C.main(_args(old, new, build="not-a-uuid")) == 2
    assert C.main(_args(old, new, shifts=("1=abc", "2=6993", "3=6993"))) == 2


def test_a_missing_capture_file_stops(tmp_path, capsys):
    assert C.main(_args(str(tmp_path / "no-old.json"), str(tmp_path / "no-new.json"))) == 1
    assert "STOP capture-load" in capsys.readouterr().out


@pytest.mark.parametrize("build,shift", [
    ("11111111-1111-4111-8111-111111111111", 6993),
    (OLD_BUILD, 0),
])
def test_consistent_unrelated_or_legacy_capture_cannot_supply_settlement_authority(
        good, tmp_path, capsys, build, shift):
    old, _ = good
    new = _capture(tmp_path, "unsettled.json", build, _rows(build, shift_s=shift), _natal())
    args = _args(old, new, build=build, shifts=tuple(f"{lv}={shift}" for lv in (1, 2, 3)))
    assert C.main(args) == 1
    out = capsys.readouterr().out
    assert "STOP settlement-authority" in out
    assert "PASS R5-build-id" not in out and "every rule PASS" not in out


@pytest.mark.parametrize("fault", ["missing", "malformed", "conflicting_build", "conflicting_chart"])
def test_absent_or_unusable_governed_settlement_stops(good, tmp_path, capsys, monkeypatch, fault):
    path = tmp_path / "settlement.json"
    if fault != "missing":
        record = json.loads(dasha_read.SETTLEMENT_PATH.read_text())
        if fault == "malformed":
            path.write_text("{invalid")
        else:
            record["run_id" if fault == "conflicting_build" else "chart_id"] = (
                "33333333-3333-4333-8333-333333333333")
            path.write_text(json.dumps(record))
    monkeypatch.setattr(dasha_read, "SETTLEMENT_PATH", path, raising=False)
    assert C.main(_args(*good)) == 1
    out = capsys.readouterr().out
    assert "STOP settlement-authority" in out
    assert "PASS R5-build-id" not in out and "every rule PASS" not in out


def test_missing_j4p_loader_stops_without_a_fallback(good, capsys, monkeypatch):
    monkeypatch.delattr(dasha_read, "load_dasha_settlement", raising=False)
    assert C.main(_args(*good)) == 1
    assert "STOP settlement-authority" in capsys.readouterr().out


def test_capture_build_must_match_the_governed_build_even_when_cli_matches(good, tmp_path, capsys):
    old, _ = good
    foreign = "11111111-1111-4111-8111-111111111111"
    new = _capture(tmp_path, "foreign.json", foreign, _rows(foreign, shift_s=6993), _natal())
    assert C.main(_args(old, new)) == 1
    out = capsys.readouterr().out
    assert "STOP capture-new" in out and "PASS R5-build-id" not in out


def test_matching_cli_and_captures_for_an_unsettled_chart_stop(good, tmp_path, capsys):
    chart = "33333333-3333-4333-8333-333333333333"
    paths = []
    for name, original in zip(("foreign-old.json", "foreign-new.json"), good):
        d = json.loads(pathlib.Path(original).read_text())
        d = R.build_capture(chart, d["build_id"], d["rows"], d["natal"])
        path = tmp_path / name
        path.write_text(json.dumps(d))
        paths.append(str(path))
    assert C.main(_args(*paths) + ["--chart-id", chart]) == 1
    assert "STOP settlement-authority" in capsys.readouterr().out


def _window_edge_rows(side, clipped_on):
    old_rows, new_rows = _rows(OLD_BUILD), _rows(NEW_BUILD, shift_s=6993)
    # A separate root avoids changing any reference row or its descendants.
    extra = {"dasha_row_id": "33333333-3333-4333-8333-333333333333", "level_n": 1,
             "parent_row_id": None, "lord_graha": "Sun", "verification_pass_status": TIER,
             "system_id": "vimshottari", "build_id": OLD_BUILD,
             "start_iso": R.WINDOW_START_ISO if side == "start" else "2080-01-01T00:00:00Z",
             "end_iso": "2000-01-01T00:00:00Z" if side == "start" else R.WINDOW_END_ISO}
    edge = f"{side}_iso"
    if clipped_on == "new":
        extra[edge] = _shift(extra[edge], -6993)
    newer = {**extra, "build_id": NEW_BUILD,
             "start_iso": _shift(extra["start_iso"], 6993), "end_iso": _shift(extra["end_iso"], 6993)}
    if clipped_on == "both":
        newer[edge] = extra[edge]
    old_rows.append(extra)
    new_rows.append(newer)
    return old_rows, new_rows


@pytest.mark.parametrize("side", ["start", "end"])
@pytest.mark.parametrize("clipped_on", ["old", "new"])
def test_one_sided_window_clipping_stops_R2(tmp_path, capsys, side, clipped_on):
    old_rows, new_rows = _window_edge_rows(side, clipped_on)
    old = _capture(tmp_path, "clipped-old.json", OLD_BUILD, old_rows, _natal())
    new = _capture(tmp_path, "clipped-new.json", NEW_BUILD, new_rows, _natal())
    # Both acquisition checks pass: only the cross-build edge report detects this.
    assert not R.validate_capture(json.loads(pathlib.Path(old).read_text()), CHART, OLD_BUILD)
    assert not R.validate_capture(json.loads(pathlib.Path(new).read_text()), CHART, NEW_BUILD)
    assert C.main(_args(old, new)) == 1
    out = capsys.readouterr().out
    assert "STOP R2-shift" in out and "window-edge status changed" in out
    assert "PASS R2-shift" not in out and "every rule PASS" not in out


@pytest.mark.parametrize("side", ["start", "end"])
def test_both_clipped_unchanged_edges_are_excluded_and_pass(tmp_path, capsys, side):
    old_rows, new_rows = _window_edge_rows(side, "both")
    old = _capture(tmp_path, "clipped-old.json", OLD_BUILD, old_rows, _natal())
    new = _capture(tmp_path, "clipped-new.json", NEW_BUILD, new_rows, _natal())
    assert C.main(_args(old, new)) == 0
    assert "PASS R2-shift" in capsys.readouterr().out


def _reinsert_ids(rows):
    ids = {r["dasha_row_id"]: str(uuid.uuid5(uuid.NAMESPACE_URL, "review-new:" + r["dasha_row_id"]))
           for r in rows}
    return [{**r, "dasha_row_id": ids[r["dasha_row_id"]], "parent_row_id": ids.get(r["parent_row_id"])}
            for r in reversed(rows)]


def test_rebuilt_capture_with_every_row_id_changed_passes_by_structure(good, tmp_path, capsys):
    old, _ = good
    new = _capture(tmp_path, "reinserted.json", NEW_BUILD,
                   _reinsert_ids(_rows(NEW_BUILD, shift_s=6993)), _natal())
    assert C.main(_args(old, new)) == 0
    out = capsys.readouterr().out
    assert "11 rows matched by path" in out and "every rule PASS" in out


@pytest.mark.parametrize("mutation,diagnostic", [
    ("lord", "no counterpart"),
    ("parent_path", "no counterpart"),
    ("orphan", "missing parent"),
])
def test_changed_ids_do_not_hide_a_reference_lord_or_structure_mutation(
        tmp_path, capsys, mutation, diagnostic):
    old_rows, new_rows = _window_edge_rows("start", "both")
    new_rows = _reinsert_ids(new_rows)
    row = next(r for r in new_rows if r["level_n"] == 2 and r["lord_graha"] == "Ketu")
    if mutation == "lord":
        row["lord_graha"] = "Jupiter"
    elif mutation == "parent_path":
        row["parent_row_id"] = next(r["dasha_row_id"] for r in new_rows
                                    if r["level_n"] == 1 and r["lord_graha"] == "Sun")
    else:
        row["parent_row_id"] = "44444444-4444-4444-8444-444444444444"
    old = _capture(tmp_path, "old.json", OLD_BUILD, old_rows, _natal())
    new = _capture(tmp_path, "mutated-new.json", NEW_BUILD, new_rows, _natal())
    assert C.main(_args(old, new)) == 1
    out = capsys.readouterr().out
    assert "STOP capture-new" in out and diagnostic in out
    assert "every rule PASS" not in out


def test_old_capture_still_requires_the_historical_reference_ids(good, tmp_path, capsys):
    _, new = good
    old = _capture(tmp_path, "unproven-old.json", OLD_BUILD, _reinsert_ids(_rows(OLD_BUILD)), _natal())
    assert C.main(_args(old, new)) == 1
    out = capsys.readouterr().out
    assert "STOP capture-old" in out and "NOT in the capture" in out


@pytest.mark.parametrize("fault,diagnostic", [
    ("chart", "capture is for chart"),
    ("envelope_build", "capture envelope names build"),
    ("selection", "selection contract"),
    ("checksum", "sha256"),
    ("row_build", "foreign or mixed build"),
    ("system", "is system"),
    ("tier", "is tier"),
    ("counts", "recorded per-level counts"),
    ("duplicate", "duplicate row id"),
    ("truncation", "flagged truncated"),
    ("coverage", "UNCLIPPED"),
])
def test_rebuilt_capture_retains_its_own_validation(good, tmp_path, capsys, fault, diagnostic):
    old, _ = good
    rows = _reinsert_ids(_rows(NEW_BUILD, shift_s=6993))
    if fault == "row_build":
        rows[0]["build_id"] = OLD_BUILD
    elif fault == "system":
        rows[0]["system_id"] = "ashtottari"
    elif fault == "tier":
        rows[0]["verification_pass_status"] = "single"
    elif fault == "duplicate":
        rows.append(dict(rows[0]))
    elif fault == "truncation":
        rows[0]["trunc_start"] = True
    elif fault == "coverage":
        next(r for r in rows if r["level_n"] == 1)["start_iso"] = R.WINDOW_START_ISO
    d = R.build_capture(CHART, NEW_BUILD, rows, _natal())
    if fault == "chart":
        d["chart_id"] = "33333333-3333-4333-8333-333333333333"
    elif fault == "envelope_build":
        d["build_id"] = OLD_BUILD
    elif fault == "selection":
        d["selection"]["system_id"] = "ashtottari"
    elif fault == "checksum":
        d["sha256"] = "0" * 64
    elif fault == "counts":
        d["meta"]["counts_by_level"]["1"] = 999
    path = tmp_path / "invalid-new.json"
    path.write_text(json.dumps(d))
    assert C.main(_args(old, str(path))) == 1
    out = capsys.readouterr().out
    assert "STOP capture-new" in out and diagnostic in out


def test_old_acquisition_uses_j4ps_historical_reference_export(good, capsys, monkeypatch):
    # J-4p removes the runtime build from DASHA_READ_CONTRACT. Its historical
    # reference export, not the current settlement, governs the old acquisition.
    monkeypatch.setattr(PERM, "REFERENCE_DASHA_BUILD_ID", OLD_BUILD, raising=False)
    monkeypatch.delitem(PERM.DASHA_READ_CONTRACT, "build_id", raising=False)
    assert C.main(_args(*good)) == 0
    assert "every rule PASS" in capsys.readouterr().out
