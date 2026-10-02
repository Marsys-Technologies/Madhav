"""AM-10 re-pin tool — pure functions + the CLI over an in-memory DB stand-in. The tool is loaded from its file;
every assertion runs its production code (no rule re-implemented here)."""
import importlib.util
import pathlib
import sys
from datetime import datetime, timedelta, timezone

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
    assert any("lord flip" in s for s in T.decide(**{**good, "flips": [{"key": (2, (0,)), "old": "Ketu", "new": "Venus"}]}))
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
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {})
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
    # (e) a test literal equal to an old boundary is NOT rewritten automatically: apply STOPS before writing ANYTHING until the ruling classifies it
    perm_before = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text(encoding="utf-8")
    with pytest.raises(T.NeedsRuling) as nr:
        T.apply_repin(new_id, maps, tmp_path)
    assert any("test_literal.py:2" in u for u in nr.value.unclassified)
    assert (tmp_path / "services" / "gochara_rules" / "permission.py").read_text(encoding="utf-8") == perm_before     # nothing written
    assert not list((tmp_path / "tests" / "l3" / "gochara_rules").glob("test_am10_repin_*.py"))
    rel = "tests/l3/gochara_rules/test_literal.py"
    review: list[str] = []
    changed = T.apply_repin(new_id, maps, tmp_path, rulings={"keep": [f"{rel}:2"]}, review=review)
    p = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text(encoding="utf-8")
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    assert f'"build_id": "{new_id}"' in p and f'"build_id": "{old_id}"' not in p     # (the old id may survive in the module docstring as history)
    assert "99999999-9999-4999-8999-999999999999" in p and ref["row_id"] not in p
    assert "2013-01-14T09:13:56Z" in p and ref["start_iso"] not in p       # permission.py: the reference rows' instants ARE rewritten (single pass)
    text = lit.read_text(encoding="utf-8")
    assert "99999999-9999-4999-8999-999999999999" in text and new_id in text
    # D8: an old BOUNDARY INSTANT in a test is NOT rewritten (it may be an event date that merely equals a boundary) — it is listed for a human
    assert f'T = "{ref["start_iso"]}"' in text and "2013-01-14T09:13:56Z" not in text
    assert any("test_literal.py:2" in r and ref["start_iso"] in r and "2013-01-14T09:13:56Z" in r and "[keep]" in r for r in review)
    assert "OTHER = \"2099-01-01T00:00:00Z\"" in text                        # unrelated literals untouched
    gen = tmp_path / "tests" / "l3" / "gochara_rules" / "test_am10_repin_22222222.py"
    assert gen.exists() and PERM.DASHA_READ_CONTRACT["build_id"] in gen.read_text(encoding="utf-8") and "DashaReadConflict" in gen.read_text(encoding="utf-8")
    assert any(c.endswith("permission.py") for c in changed) and len(changed) == 3


# ── Moshier → Swiss (≈ 1.94 h boundary shift; steward M20261002T222913-35c5, D7/D8) ─────────────────────────────────────────────────
def test_a_uniform_boundary_shift_with_every_lord_kept_is_CLEAN_and_the_moved_edges_are_only_boundary_sensitive():
    old, new = build("old"), build("new", shift_s=6993)         # +6993 s ≈ 1.94 h on every edge
    oi, ni = T.index_paths(old), T.index_paths(new)
    m = T.match(oi, ni)
    assert T.path_lord_flips(oi, ni, m["matched"]) == []        # lords hold at EVERY matched (level, path)
    edge = ["2005-01-01T00:00:10Z"]
    sens = T.lord_flips(old, new, edge)                          # the lord AT the old edge instant differs …
    assert sens and sens[0]["old"]["AD"] == "Ketu" and sens[0]["new"]["AD"] == "Mercury"
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m=m, ref_problems=[], forensic_report="f.md")
    assert T.decide(**good, flips=T.path_lord_flips(oi, ni, m["matched"])) == []   # … but a moved boundary is NOT a STOP


def test_a_lord_difference_at_ANY_matched_row_is_a_STOP_not_only_at_the_reference_rows():
    old, new = build("old"), build("new", shift_s=6993)
    new[-1]["lord_graha"] = "Rahu"                              # a non-reference row's lord changes
    oi, ni = T.index_paths(old), T.index_paths(new)
    m = T.match(oi, ni)
    flips = T.path_lord_flips(oi, ni, m["matched"])
    assert len(flips) == 1 and flips[0]["new"] == "Rahu"
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m=m, ref_problems=[], forensic_report="f.md")
    assert any("lord flip" in x for x in T.decide(**good, flips=flips))


def test_oracle_instants_carry_each_pinned_edge_plus_and_minus_one_second():
    inst = set(T.oracle_instants())
    r = PERM.MD_ROWS[0]
    for edge in (r["start_iso"], r["end_iso"]):
        base = T._t(edge)
        for d in (-1, 0, 1):
            assert T.iso(base + timedelta(seconds=d)) in inst


def test_rewrite_is_ONE_pass_a_new_value_equal_to_a_later_old_value_is_not_replaced_twice():
    mapping = {"2010-08-18T15:50:23Z": "2010-08-18T17:46:56Z", "2010-08-18T17:46:56Z": "2010-08-18T19:43:29Z"}
    assert T.rewrite_once("a 2010-08-18T15:50:23Z b 2010-08-18T17:46:56Z", mapping) == "a 2010-08-18T17:46:56Z b 2010-08-18T19:43:29Z"
    assert T.rewrite_once("untouched", {}) == "untouched"


def test_a_non_whole_second_new_instant_is_refused_by_apply(monkeypatch, tmp_path):
    (tmp_path / "services" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "tests" / "l3").mkdir(parents=True)
    (tmp_path / "services" / "gochara_rules" / "permission.py").write_text(pathlib.Path(PERM.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    ref = PERM.AD_ROWS[0]
    bad = [{"old": ref, "new": {"dasha_row_id": "99999999-9999-4999-8999-999999999999", "start_iso": "2013-01-14T09:13:56.5Z", "end_iso": "2014-01-11T14:11:56Z", "lord_graha": ref["lord"]}, "key": (2, (0,))}]
    with pytest.raises(AssertionError, match="whole-second"):
        T.apply_repin("22222222-2222-4222-8222-222222222222", bad, tmp_path)


def test_a_ruling_to_rewrite_changes_ONLY_the_ruled_line(monkeypatch, tmp_path):
    (tmp_path / "services" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "tests" / "l3" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "services" / "gochara_rules" / "permission.py").write_text(pathlib.Path(PERM.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    ref = PERM.AD_ROWS[0]
    lit = tmp_path / "tests" / "l3" / "gochara_rules" / "test_two.py"
    lit.write_text(f'A = "{ref["start_iso"]}"   # a boundary\nB = "{ref["start_iso"]}"   # an EVENT date that merely equals it\n', encoding="utf-8")
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    maps = [{"old": ref, "new": {"dasha_row_id": "99999999-9999-4999-8999-999999999999", "start_iso": "2013-01-14T09:13:56Z", "end_iso": "2014-01-11T14:11:56Z", "lord_graha": ref["lord"]}, "key": (2, (0,))}]
    rel = "tests/l3/gochara_rules/test_two.py"
    T.apply_repin("22222222-2222-4222-8222-222222222222", maps, tmp_path, rulings={"rewrite": [f"{rel}:1"], "keep": [f"{rel}:2"]})
    a, b = lit.read_text(encoding="utf-8").splitlines()[:2]
    assert "2013-01-14T09:13:56Z" in a and ref["start_iso"] in b


def test_the_measured_shift_must_match_the_settled_notice_within_its_stated_tolerance():
    old, new = T.index_paths(build("old")), T.index_paths(build("new", shift_s=6993))
    stats = T.shift_stats(old, new, T.match(old, new)["matched"])
    ok = {"settled_1": True, "expected_shift_seconds": {"1": 6993, "2": 6993}, "tolerance_seconds": 2}
    assert T.shift_problems(stats, ok) == []
    assert T.shift_problems(stats, {**ok, "expected_shift_seconds": {"1": 6993, "2": 3600}})            # level 2 shifted by 6993 s, the notice expects 3600 s ⇒ refuse
    assert any("not measured" in p for p in T.shift_problems(stats, {**ok, "expected_shift_seconds": {"1": 6993, "2": 6993, "3": 6993}}))
    assert any("states no expected shift" in p for p in T.shift_problems(stats, {**ok, "expected_shift_seconds": {"1": 6993}}))
    assert any("no --settled-notice" in p for p in T.shift_problems(stats, None))
    assert T.shift_problems(stats, {**ok, "expected_shift_seconds": {"1": {"start": 6993, "end": 6993}, "2": 6993}}) == []
    assert T.shift_problems(stats, {**ok, "tolerance_seconds": 0}) == []                                      # exact is allowed when the data is exact
    assert T.shift_problems(stats, {**ok, "expected_shift_seconds": {"1": 6990, "2": 6993}, "tolerance_seconds": 2})   # 3 s off with ±2 ⇒ refuse


def test_the_settled_notice_must_state_its_tolerance_and_settle_1(tmp_path):
    good = tmp_path / "n.json"
    good.write_text('{"settled_1": true, "expected_shift_seconds": {"1": 6993}, "tolerance_seconds": 2}', encoding="utf-8")
    assert T.load_notice(str(good))["tolerance_seconds"] == 2
    for bad in ('{"settled_1": true, "expected_shift_seconds": {"1": 6993}}', '{"settled_1": false, "expected_shift_seconds": {}, "tolerance_seconds": 1}',
                '{"settled_1": true, "expected_shift_seconds": {"1": 1}, "tolerance_seconds": true}', '{"settled_1": true, "expected_shift_seconds": {"1": 1}, "tolerance_seconds": -1}'):
        p = tmp_path / "b.json"; p.write_text(bad, encoding="utf-8")
        with pytest.raises(ValueError):
            T.load_notice(str(p))


def test_apply_is_refused_without_the_hold_lift_and_dry_run_excludes_apply_and_writes_nothing(monkeypatch, tmp_path, capsys):
    new = "11111111-1111-4111-8111-111111111111"
    assert T.main(["--new-build-id", new, "--apply"], conn=object()) == 2
    assert "ST-SL1-HOLD" in capsys.readouterr().err
    assert T.main(["--new-build-id", new, "--apply", "--dry-run", "--hold-lifted", "M1"], conn=object()) == 2
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {})
    out = tmp_path / "evidence.md"
    assert T.main(["--new-build-id", new, "--dry-run", "--out", str(out)], conn=object()) == 3        # absent build ⇒ STOP, and …
    assert not out.exists()                                                                          # … a dry run writes no file


# ── G6: coexisting builds; capture the OLD rows BEFORE S-L1 (steward M20261002T223036-02f0) ─────────────────────────────────────────────
OLDB = PERM.DASHA_READ_CONTRACT["build_id"]
NEWB = "11111111-1111-4111-8111-111111111111"


def test_exactly_one_vimshottari_build_and_it_is_the_settled_one():
    assert T.build_problems({NEWB: 117}, NEWB) == []
    assert any("exactly ONE" in p for p in T.build_problems({OLDB: 117, NEWB: 117}, NEWB))          # coexistence — the silent-old-read risk
    assert T.build_problems({OLDB: 117}, NEWB)                                                       # only the OLD build present
    assert T.build_problems({}, NEWB)                                                                # nothing at all


def test_the_fetch_of_builds_is_a_read_only_group_by_over_lahiri_levels_1_to_3():
    class Cur:
        def execute(self, q, p): self.q, self.p = q, p
        def fetchall(self): return [(NEWB, 117)]
    class Conn:
        def __init__(self): self.c = Cur()
        def cursor(self): return self.c
    c = Conn()
    assert T.fetch_vimshottari_builds(c, "chart-x") == {NEWB: 117}
    q = c.c.q.lower()
    assert q.startswith("select") and "group by" in q and "level_n in (1, 2, 3)" in q and "system_id = 'vimshottari'" in q and not any(w in q for w in ("update", "delete", "insert"))
    assert c.c.p == ("chart-x", "lahiri_chitrapaksha")


def test_capture_and_load_round_trip_and_refuse_a_wrong_or_altered_file(tmp_path):
    rows = T.norm_rows(build("old"))
    p = tmp_path / "old.json"
    digest = T.write_capture(str(p), "c1", OLDB, rows)
    assert T.load_capture(str(p), "c1", OLDB) == rows and len(digest) == 64
    with pytest.raises(ValueError):
        T.load_capture(str(p), "c2", OLDB)                                       # another chart
    with pytest.raises(ValueError):
        T.load_capture(str(p), "c1", NEWB)                                       # another build
    d = __import__("json").loads(p.read_text()); d["rows"][0]["lord_graha"] = "Venus"; p.write_text(__import__("json").dumps(d))
    with pytest.raises(ValueError):
        T.load_capture(str(p), "c1", OLDB)                                       # altered after capture


def test_the_cli_compares_against_a_captured_old_file_when_the_old_rows_are_gone_and_stops_on_coexistence(monkeypatch, tmp_path, capsys):
    rows_old = T.norm_rows(build("old"))
    rows_new = T.norm_rows(build("new", shift_s=6993))
    cap = tmp_path / "old.json"
    T.write_capture(str(cap), PERM.DASHA_READ_CONTRACT["chart_id"], OLDB, rows_old)
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, build_id=None, **kw: rows_new if build_id == NEWB else [])    # the old build is GONE from the DB
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117})
    monkeypatch.setattr(T, "remeasure_reference_rows", lambda old, new: ([], []))      # the reference rows are covered by their own test; this fixture is not the pinned data
    notice = tmp_path / "n.json"
    notice.write_text('{"settled_1": true, "new_build_id": "%s", "expected_shift_seconds": {"1": 6993, "2": 6993}, "tolerance_seconds": 1}' % NEWB)
    fr = tmp_path / "f.md"; fr.write_text("anchors ok")
    args = ["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", str(notice), "--forensic-report", str(fr), "--dry-run"]
    rc = T.main(args, conn=object())
    out = capsys.readouterr().out
    assert rc == 0 and "verdict: **CLEAN**" in out, out[-800:]
    # without the capture the old rows are absent ⇒ STOP with the instruction
    rc = T.main([x for x in args if x not in ("--old-rows", str(cap))], conn=object())
    assert rc == 3 and "--capture-old" in capsys.readouterr().out
    # coexistence of the old build ⇒ STOP even though the comparison is otherwise clean
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {OLDB: 117, NEWB: 117})
    rc = T.main(args, conn=object())
    assert rc == 3 and "exactly ONE" in capsys.readouterr().out


def test_capture_old_writes_a_file_and_refuses_when_the_pinned_build_has_no_rows(monkeypatch, tmp_path):
    rows = T.norm_rows(build("old"))
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: rows)
    p = tmp_path / "cap.json"
    assert T.main(["--new-build-id", NEWB, "--capture-old", str(p)], conn=object()) == 0 and p.exists()
    assert T.load_capture(str(p), PERM.DASHA_READ_CONTRACT["chart_id"], OLDB) == rows
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    q = tmp_path / "none.json"
    assert T.main(["--new-build-id", NEWB, "--capture-old", str(q)], conn=object()) == 3 and not q.exists()
