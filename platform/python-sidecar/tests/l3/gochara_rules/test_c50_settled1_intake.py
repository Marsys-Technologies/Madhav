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
from datetime import datetime, timedelta, timezone

import pytest

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
OLD_BUILD = PERM.DASHA_READ_CONTRACT["build_id"]
NEW_BUILD = "11111111-1111-4111-8111-111111111111"
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


def test_a_build_id_other_than_the_notice_stops(good, capsys):
    old, new = good
    assert C.main(_args(old, new, build="33333333-3333-4333-8333-333333333333")) == 1
    assert "STOP capture-new" in capsys.readouterr().out


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
