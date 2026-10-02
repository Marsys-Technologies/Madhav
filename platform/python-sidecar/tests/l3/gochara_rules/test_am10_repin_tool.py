"""AM-10 re-pin tool — pure functions + the CLI over an in-memory DB stand-in. The tool is loaded from its file;
every assertion runs its production code (no rule re-implemented here)."""
import importlib.util
import pathlib
import sys
from datetime import datetime, timezone

import pytest

_P = pathlib.Path(__file__).resolve().parents[3] / "scripts" / "gochara" / "repin_dasha_contract.py"
_spec = importlib.util.spec_from_file_location("repin_dasha_contract_t", _P)
T = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = T
_spec.loader.exec_module(T)

PERM = T.PERM
TIER = PERM.DASHA_READ_CONTRACT["tier"]


def build(prefix, shift_s=0, lord_override=None):
    """A tiny two-MD tree: MD0 [2000..2010) → AD0 [2000..2005), AD1 [2005..2010); MD1 [2010..2020)."""
    def r(i, lvl, parent, lord, a, b):
        return {"dasha_row_id": f"{prefix}-{i}", "level_n": lvl, "parent_row_id": parent, "lord_graha": lord,
                "start_iso": a, "end_iso": b, "verification_pass_status": TIER, "build_id": prefix}
    def sh(s_):
        return T.iso(datetime.fromtimestamp(T._t(s_).timestamp() + shift_s, tz=timezone.utc))
    rows = [r("m0", 1, None, "Mercury", sh("2000-01-01T00:00:00Z"), sh("2010-01-01T00:00:00Z")),
            r("m1", 1, None, "Ketu", sh("2010-01-01T00:00:00Z"), sh("2020-01-01T00:00:00Z")),
            r("a0", 2, f"{prefix}-m0", "Mercury", sh("2000-01-01T00:00:00Z"), sh("2005-01-01T00:00:00Z")),
            r("a1", 2, f"{prefix}-m0", "Ketu", sh("2005-01-01T00:00:00Z"), sh("2010-01-01T00:00:00Z"))]
    if lord_override:
        for x in rows:
            if x["dasha_row_id"].endswith(lord_override[0]):
                x["lord_graha"] = lord_override[1]
    return rows


def test_paths_match_by_level_parent_index_across_builds_with_different_ids():
    old, new = T.index_paths(build("old")), T.index_paths(build("new", shift_s=6993))
    m = T.match(old, new)
    assert not m["only_old"] and not m["only_new"] and len(m["matched"]) == 4
    st = T.shift_stats(old, new, m["matched"])
    assert st[1]["start"] == {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 2}
    assert st[2]["end"]["n"] == 2


def test_a_count_difference_is_reported_not_hidden():
    o, n = build("old"), build("new")
    n = [x for x in n if not x["dasha_row_id"].endswith("a1")]
    m = T.match(T.index_paths(o), T.index_paths(n))
    assert m["only_old"] == [(2, (0, 1))] and not m["only_new"]


def test_lord_flip_at_an_instant_is_detected_and_a_shift_inside_a_period_is_not():
    old, new = build("old"), build("new", shift_s=6993)
    inside = ["2003-06-01T00:00:00Z", "2012-01-01T00:00:00Z"]
    assert T.lord_flips(old, new, inside) == []
    edge = ["2005-01-01T00:00:10Z"]          # old: AD Ketu already running; new boundary shifted +6993 s ⇒ still Mercury
    flips = T.lord_flips(old, new, edge)
    assert flips and flips[0]["old"]["AD"] == "Ketu" and flips[0]["new"]["AD"] == "Mercury"


def test_integrity_finds_orphans_and_duplicates():
    rows = build("new")
    rows.append({**rows[2], "dasha_row_id": "new-a0dup"})                           # same level/parent/start/lord
    rows.append({**rows[2], "dasha_row_id": "new-orph", "parent_row_id": "ghost", "start_iso": "2001-01-01T00:00:00Z"})
    i = T.integrity(rows)
    assert i["duplicates"] == 1 and i["orphans"] == ["new-orph"]


def test_decide_lists_every_stop_and_is_clean_only_with_all_evidence():
    m_ok = {"matched": [1], "only_old": [], "only_new": []}
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m=m_ok, flips=[], ref_problems=[], forensic_report="f.md")
    assert T.decide(**good) == []
    assert any("FORENSIC" in s for s in T.decide(**{**good, "forensic_report": None}))
    assert any("lord flip" in s for s in T.decide(**{**good, "flips": [{"instant": "x"}]}))
    assert any("two_pass_verified" in s for s in T.decide(**{**good, "new_tier_ok": False}))
    assert any("row-count" in s for s in T.decide(**{**good, "m": {"matched": [], "only_old": [(1, (0,))], "only_new": []}}))
    assert any("orphaned" in s for s in T.decide(**{**good, "new_integrity": {"orphans": ["o"], "duplicates": 0}}))


def test_reference_rows_are_remeasured_from_the_new_build_by_position():
    # use the REAL pinned reference rows as the old build, shifted +6993 s with fresh ids, all paths preserved
    def real_build(prefix, shift):
        rows = []
        for ref in PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS:
            rows.append({"dasha_row_id": ref["row_id"] if prefix == "old" else f"new-{ref['row_id']}", "level_n": {"MD": 1, "AD": 2, "PD": 3}[ref["level"]],
                         "parent_row_id": None if ref["parent_row_id"] is None else (ref["parent_row_id"] if prefix == "old" else f"new-{ref['parent_row_id']}"),
                         "lord_graha": ref["lord"],
                         "start_iso": T.iso(datetime.fromtimestamp(T._t(ref["start_iso"]).timestamp() + shift, tz=timezone.utc)),
                         "end_iso": T.iso(datetime.fromtimestamp(T._t(ref["end_iso"]).timestamp() + shift, tz=timezone.utc))})
        return rows
    old, new = T.index_paths(real_build("old", 0)), T.index_paths(real_build("new", 6993))
    maps, problems = T.remeasure_reference_rows(old, new)
    assert problems == [] and len(maps) == len(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS)
    assert all(x["new"]["dasha_row_id"].startswith("new-") for x in maps)
    # a lord flip at a reference position is a problem, not a silent re-measure
    flipped = real_build("new", 6993); flipped[0]["lord_graha"] = "Venus"
    _, probs = T.remeasure_reference_rows(old, T.index_paths(flipped))
    assert any("LORD FLIP" in p for p in probs)


def test_cli_refuses_the_current_pin_and_stops_without_a_forensic_report(monkeypatch, tmp_path):
    assert T.main(["--new-build-id", PERM.DASHA_READ_CONTRACT["build_id"]], conn=object()) == 2
    # the DB stand-in: no rows for the new build ⇒ the new build is absent ⇒ STOP (exit 3), nothing applied
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    out = tmp_path / "evidence.md"
    assert T.main(["--new-build-id", "11111111-1111-4111-8111-111111111111", "--out", str(out)], conn=object()) == 3
    assert "STOP" in out.read_text()


def test_apply_rewrites_the_pin_the_reference_rows_and_literals_and_generates_the_refusal_test(monkeypatch, tmp_path):
    # a scratch copy of the files --apply may touch
    perm_src = pathlib.Path(PERM.__file__)
    (tmp_path / "services" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "tests" / "l3" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "services" / "gochara_rules" / "permission.py").write_text(perm_src.read_text(encoding="utf-8"), encoding="utf-8")
    ref = PERM.AD_ROWS[0]
    lit = tmp_path / "tests" / "l3" / "gochara_rules" / "test_literal.py"
    lit.write_text(f'ROW = "{ref["row_id"]}"\nT = "{ref["start_iso"]}"\nB = "{PERM.DASHA_READ_CONTRACT["build_id"]}"\nOTHER = "2099-01-01T00:00:00Z"\n', encoding="utf-8")
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    new_id = "22222222-2222-4222-8222-222222222222"
    maps = [{"old": ref, "new": {"dasha_row_id": "99999999-9999-4999-8999-999999999999", "start_iso": "2013-01-14T09:13:56Z",
                                 "end_iso": "2014-01-11T14:11:56Z", "lord_graha": ref["lord"]}, "key": (2, (0,))}]
    changed = T.apply_repin(new_id, maps, tmp_path)
    p = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text(encoding="utf-8")
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    assert f'"build_id": "{new_id}"' in p and f'"build_id": "{old_id}"' not in p     # (the old id may survive in the module docstring as history)
    assert "99999999-9999-4999-8999-999999999999" in p and ref["row_id"] not in p
    text = lit.read_text(encoding="utf-8")
    assert "99999999-9999-4999-8999-999999999999" in text and "2013-01-14T09:13:56Z" in text and new_id in text
    assert "OTHER = \"2099-01-01T00:00:00Z\"" in text                        # unrelated literals untouched
    gen = tmp_path / "tests" / "l3" / "gochara_rules" / "test_am10_repin_22222222.py"
    assert gen.exists() and PERM.DASHA_READ_CONTRACT["build_id"] in gen.read_text(encoding="utf-8") and "DashaReadConflict" in gen.read_text(encoding="utf-8")
    assert any(c.endswith("permission.py") for c in changed) and len(changed) == 3
