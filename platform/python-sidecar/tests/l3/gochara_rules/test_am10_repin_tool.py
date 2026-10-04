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
        return T.full_iso(datetime.fromtimestamp(T._t(s_).timestamp() + shift_s, tz=timezone.utc))      # FULL precision (the tool measures with it)
    rows = [r("m0", 1, None, "Mercury", sh("2000-01-01T00:00:00Z"), sh("2010-01-01T00:00:00Z")),
            r("m1", 1, None, "Ketu", sh("2010-01-01T00:00:00Z"), sh("2020-01-01T00:00:00Z")),
            r("a0", 2, f"{prefix}-m0", "Mercury", sh("2000-01-01T00:00:00Z"), sh("2005-01-01T00:00:00Z")),
            r("a1", 2, f"{prefix}-m0", "Ketu", sh("2005-01-01T00:00:00Z"), sh("2010-01-01T00:00:00Z"))]
    if lord_override:
        for x in rows:
            if x["dasha_row_id"].endswith(lord_override[0]):
                x["lord_graha"] = lord_override[1]
    return rows


class _AllFalse(dict):
    """A flags stand-in for tests that mock the READER: every row is unflagged (the toy trees are nowhere near the window bounds)."""
    def __contains__(self, k): return True
    def __getitem__(self, k): return (False, False)


def real_reader(fn):
    """Marks a test that exercises the REAL reader and the REAL flags SQL (every other test mocks `read_truncation`)."""
    fn._real_reader = True
    return fn


@pytest.fixture(autouse=True)
def _flags_stub(request, monkeypatch):
    if not getattr(request.function, "_real_reader", False):
        monkeypatch.setattr(T, "read_truncation", lambda conn, chart, build: _AllFalse())


class FakeConn:
    """A connection stand-in that LOOKS like psycopg3 (has `execute`) — used where the reader itself is monkeypatched."""
    def execute(self, *a, **k):
        raise AssertionError("the reader is mocked in this test")

    def cursor(self):
        raise AssertionError("not used")


def build3(prefix, shift_s=0):
    """build() plus a level-3 (PD) row, so every level the tool expects (1–3) is present."""
    rows = build(prefix, shift_s)
    a0 = next(x for x in rows if x["dasha_row_id"].endswith("a0"))
    rows.append({"dasha_row_id": f"{prefix}-p0", "level_n": 3, "parent_row_id": a0["dasha_row_id"], "lord_graha": "Mercury",
                 "start_iso": a0["start_iso"], "end_iso": a0["end_iso"], "verification_pass_status": TIER, "build_id": prefix})
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
    assert m["only_old"] == [(2, (("Mercury", 0), ("Ketu", 0)))] and not m["only_new"]            # keyed by LORD, not by a bare index


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
    # a different lord at a reference position is a problem (its structural key — which carries the LORD — has no counterpart), not a silent re-measure
    flipped = real_build("new", 6993); flipped[0]["lord_graha"] = "Venus"
    _, probs = T.remeasure_reference_rows(old, T.index_paths(flipped))
    assert any("no counterpart" in p for p in probs)


def test_cli_refuses_the_current_pin_and_stops_without_a_forensic_report(monkeypatch, tmp_path):
    assert T.main(["--new-build-id", PERM.DASHA_READ_CONTRACT["build_id"]], conn=FakeConn()) == 2
    # the DB stand-in: no rows for the new build ⇒ the new build is absent ⇒ STOP (exit 3), nothing applied
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: {"builds": [], "non_scope": 0, "scope": 0, "throughput": {}})
    assert T.main(["--new-build-id", "11111111-1111-4111-8111-111111111111"], conn=FakeConn()) == 3          # an EMPTY read is a STOP (never 'nothing changed')


def _stub_verifier(tmp_path, build_id=None):
    d = tmp_path / "services" / "gochara_kernel"; d.mkdir(parents=True, exist_ok=True)
    (d / "inventory_verifier.py").write_text(f'"""stub of Stream A\'s verifier"""\n_C_BUILD = "{build_id or PERM.DASHA_READ_CONTRACT["build_id"]}"\n', encoding="utf-8")


def test_apply_rewrites_the_pin_the_reference_rows_and_literals_and_generates_the_refusal_test(monkeypatch, tmp_path):
    _stub_verifier(tmp_path)
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
    assert any(c.endswith("permission.py") for c in changed) and any(c.endswith("inventory_verifier.py") for c in changed) and len(changed) == 4


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


def test_a_lord_difference_at_ANY_row_is_a_REFUSED_SUBTREE_not_only_at_the_reference_rows():
    old, new = build("old"), build("new", shift_s=6993)
    new[-1]["lord_graha"] = "Rahu"                              # a non-reference row's lord changes (its sibling sequence differs)
    oi, ni = T.index_paths(old), T.index_paths(new)
    refusals = T.subtree_refusals(oi, ni)
    assert len(refusals) == 1 and refusals[0]["old"] == ["Mercury", "Ketu"] and refusals[0]["new"] == ["Mercury", "Rahu"]
    m = {**T.match(oi, ni)}
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m=m, ref_problems=[], forensic_report="f.md", flips=[])
    assert any("REFUSED SUBTREE" in x and "never best-guessed" in x for x in T.decide(**good, refused_subtrees=refusals))


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


def test_apply_formats_the_permission_literals_whole_second_while_rows_keep_full_precision(monkeypatch, tmp_path):
    maps = _apply_world(tmp_path)
    maps[0]["new"]["start_iso"] = "2013-01-14T09:13:56.750000Z"                                       # a measured full-precision instant
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    T.apply_repin(NEWB, maps, tmp_path)
    perm = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text()
    assert "2013-01-14T09:13:56Z" in perm and "09:13:56.75" not in perm                              # whole-second literal in permission.py only
    assert T.full_iso("2013-01-14T09:13:56.750000Z") == "2013-01-14T09:13:56.750000Z" and T.iso("2013-01-14T09:13:56.750000Z") == "2013-01-14T09:13:56Z"


def test_a_ruling_to_rewrite_changes_ONLY_the_ruled_line(monkeypatch, tmp_path):
    _stub_verifier(tmp_path)
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


def _notice(tmp_path, **over):
    d = {"settled_1": True, "source_message_id": "M20261004T000000-test", "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha",
         "new_build_id": "11111111-1111-4111-8111-111111111111", "expected_shift_seconds": {"1": 6993, "2": 6993, "3": 6993}, "tolerance_seconds": 2}
    d.update(over)
    p = tmp_path / "notice.json"
    import json as _j
    p.write_text(_j.dumps(d, allow_nan=True))
    return str(p)


def test_the_settled_notice_is_strict_finite_complete_and_bound_to_a_build(tmp_path):
    good = T.load_notice(_notice(tmp_path))
    assert good["tolerance_seconds"] == 2 and len(good["_sha256"]) == 64
    assert T.load_notice(_notice(tmp_path, expected_shift_seconds={"1": 6993, "2": {"start": 6992, "end": 6994}, "3": 6993}))["expected_shift_seconds"]["2"] == {"start": 6992, "end": 6994}
    assert T.load_notice(_notice(tmp_path, expected_shift_seconds={"1": 6993, "2": 6993, "3": 6993, "4": 41000}))["_ignored_levels"] == ["4"]       # a level-4 entry is TOLERATED, echoed, never compared
    bad = [dict(system_id="kalachakra"), dict(system_id=None), dict(ayanamsha_id="raman"), dict(source_message_id=""), dict(source_message_id=None), dict(settled_1=False), dict(new_build_id=None), dict(new_build_id="not-a-uuid"), dict(expected_shift_seconds={"1": 6993, "2": 6993}),                    # a level missing
           dict(expected_shift_seconds={"1": 6993, "2": 6993, "3": {"start": 1}}),          # one boundary only
           dict(expected_shift_seconds={"1": float("nan"), "2": 6993, "3": 6993}), dict(expected_shift_seconds={"1": float("inf"), "2": 6993, "3": 6993}),
           dict(expected_shift_seconds={"1": True, "2": 6993, "3": 6993}), dict(expected_shift_seconds={"1": "6993", "2": 6993, "3": 6993}),
           dict(tolerance_seconds=float("nan")), dict(tolerance_seconds=float("inf")), dict(tolerance_seconds=0.5), dict(tolerance_seconds=0), dict(tolerance_seconds=-1), dict(tolerance_seconds=True),
           dict(tolerance_seconds=None)]
    for over in bad:
        with pytest.raises(ValueError, match="notice is invalid"):
            T.load_notice(_notice(tmp_path, **over))



def test_apply_is_refused_without_the_hold_lift_and_dry_run_excludes_apply_and_writes_nothing(monkeypatch, tmp_path, capsys):
    new = "11111111-1111-4111-8111-111111111111"
    assert T.main(["--new-build-id", new, "--apply"], conn=FakeConn()) == 2
    assert "ST-SL1-HOLD" in capsys.readouterr().err
    assert T.main(["--new-build-id", new, "--apply", "--dry-run", "--settled-received", "M1"], conn=FakeConn()) == 2
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: {"builds": [], "non_scope": 0, "scope": 0, "throughput": {}})
    out = tmp_path / "evidence.md"
    assert T.main(["--new-build-id", new, "--dry-run", "--out", str(out)], conn=FakeConn()) == 3        # absent build ⇒ STOP, and …
    assert not out.exists()                                                                          # … a dry run writes no file


# ── G6: coexisting builds; capture the OLD rows BEFORE S-L1 (steward M20261002T223036-02f0) ─────────────────────────────────────────────
OLDB = PERM.DASHA_READ_CONTRACT["build_id"]
NEWB = "11111111-1111-4111-8111-111111111111"
GOODFACTS = {"builds": [NEWB], "non_scope": 45, "scope": 1, "throughput": {"ga_dashas": "lit", "ga_positions": "lit"}}


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
    p = tmp_path / "old.json"
    cap = write_old_cap(p)
    assert T.load_capture_full(str(p), CHART, OLDB) == cap and len(cap["sha256"]) == 64
    with pytest.raises(ValueError):
        T.load_capture(str(p), "another-chart", OLDB)                            # another chart
    with pytest.raises(ValueError):
        T.load_capture(str(p), CHART, NEWB)                                      # another build
    d = __import__("json").loads(p.read_text()); d["rows"][0]["lord_graha"] = "Venus"; p.write_text(__import__("json").dumps(d))
    with pytest.raises(ValueError, match="sha256"):
        T.load_capture(str(p), CHART, OLDB)                                      # altered after capture


def _rewrite(p, mutate, recompute=False):
    import json as _j
    d = _j.loads(p.read_text())
    mutate(d)
    if recompute:
        d["sha256"] = T._capture_digest(d["chart_id"], d["build_id"], d["rows"], d["natal"])             # an attacker who recomputes the checksum
    p.write_text(_j.dumps(d))


def test_an_envelope_that_claims_the_old_pin_while_every_row_carries_another_build_is_refused_even_with_a_recomputed_checksum(tmp_path):
    """R18-1 (Codex reproduced a false CLEAN): structurally valid reference rows, every row `22222222-…`, the envelope names the expected old pin."""
    p = tmp_path / "old.json"
    write_old_cap(p)
    _rewrite(p, lambda d: [r.__setitem__("build_id", "22222222-2222-4222-8222-222222222222") for r in d["rows"]], recompute=True)
    with pytest.raises(ValueError, match="foreign or mixed build"):
        T.load_capture(str(p), CHART, OLDB)
    p2 = tmp_path / "mixed.json"
    write_old_cap(p2)
    _rewrite(p2, lambda d: d["rows"][0].__setitem__("build_id", "22222222-2222-4222-8222-222222222222"), recompute=True)              # ONE foreign row among the old ones
    with pytest.raises(ValueError, match="foreign or mixed build"):
        T.load_capture(str(p2), CHART, OLDB)


def test_wrong_system_tier_or_level_in_a_capture_is_refused(tmp_path):
    for mutate, needle in ((lambda d: d["rows"][0].__setitem__("system_id", "kalachakra"), "system"), (lambda d: d["rows"][0].__setitem__("verification_pass_status", "single"), "tier"),
                           (lambda d: d["rows"][0].__setitem__("level_n", 4), "level")):
        p = tmp_path / "c.json"
        write_old_cap(p)
        _rewrite(p, mutate, recompute=True)
        with pytest.raises(ValueError, match=needle):
            T.load_capture(str(p), CHART, OLDB)


def test_the_envelope_identity_and_selection_are_bound_into_the_checksum(tmp_path):
    for mutate in (lambda d: d.__setitem__("chart_id", "another-chart"), lambda d: d.__setitem__("build_id", "22222222-2222-4222-8222-222222222222"),
                   lambda d: d["selection"].__setitem__("tier", "single"), lambda d: d["selection"].__setitem__("levels", [1, 2, 3, 4])):
        p = tmp_path / "c.json"
        write_old_cap(p)
        _rewrite(p, mutate)                                                      # the data digest is NOT recomputed: any change to identity/selection invalidates it
        with pytest.raises(ValueError):
            T.load_capture(str(p), CHART, OLDB)


def test_the_cli_compares_against_a_captured_old_file_when_the_old_rows_are_gone_and_stops_on_coexistence(monkeypatch, tmp_path, capsys):
    rows_new = T.norm_rows(ref_rows("new", 6993))
    cap = tmp_path / "old.json"
    write_old_cap(cap)
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, build_id=None, **kw: rows_new if build_id == NEWB else [])    # the old build is GONE from the DB
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: GOODFACTS)
    notice = tmp_path / "n.json"
    notice.write_text('{"settled_1": true, "source_message_id": "M1", "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha", "new_build_id": "%s", "expected_shift_seconds": {"1": 6993, "2": 6993, "3": 6993}, "tolerance_seconds": 1}' % NEWB)
    fr = tmp_path / "f.md"; fr.write_text("anchors ok")
    args = ["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", str(notice), "--forensic-report", str(fr), "--dry-run"]
    rc = T.main(args, conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 0 and "verdict: **CLEAN**" in out, out[-800:]
    # without the capture the old rows are absent ⇒ STOP with the instruction
    rc = T.main([x for x in args if x not in ("--old-rows", str(cap))], conn=FakeConn())
    err = capsys.readouterr().err
    assert rc == 3 and "--capture-old" in err and "NO rows" in err
    # coexistence of the old build ⇒ STOP even though the comparison is otherwise clean
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {OLDB: 117, NEWB: 117})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: {**GOODFACTS, "builds": [OLDB, NEWB]})
    rc = T.main(args, conn=FakeConn())
    assert rc == 3 and "exactly ONE" in capsys.readouterr().out


def test_capture_old_writes_a_file_and_refuses_when_the_pinned_build_has_no_rows(monkeypatch, tmp_path):
    rows = T.norm_rows(ref_rows("old"))
    monkeypatch.setattr(T, "read_natal", lambda conn, chart: natal_dicts())
    monkeypatch.setattr(T, "capture_census", lambda conn, chart: {"chart_dashas_build_ids": [OLDB], "partitions_non_scope": 45, "partitions_scope_cap": 1, "asset_throughput": {"ga_dashas": "lit", "ga_positions": "lit"}})
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [dict(r) for r in rows])
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)], conn=FakeConn()) == 0 and p.exists()
    got = T.load_capture(str(p), PERM.DASHA_READ_CONTRACT["chart_id"], OLDB)
    assert [{k: v for k, v in r.items() if not k.startswith("trunc_")} for r in got] == rows and all(r["trunc_start"] is False and r["trunc_end"] is False for r in got)
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    q = tmp_path / "none.json"
    assert T.main(["--capture-old", str(q)], conn=FakeConn()) == 3 and not q.exists()


def test_the_settled_1_mechanical_guard_refuses_each_condition_separately():
    assert T.preflight_problems(GOODFACTS, NEWB) == []
    assert any("(ii)" in p for p in T.preflight_problems({**GOODFACTS, "builds": [OLDB, NEWB]}, NEWB))                  # mixed builds
    assert any("(ii)" in p for p in T.preflight_problems({**GOODFACTS, "builds": []}, NEWB))                            # nothing
    assert any("(v)" in p for p in T.preflight_problems({**GOODFACTS, "builds": [OLDB]}, NEWB))                         # one build, but not the SETTLED-1 one
    assert any("(iii)" in p and "44 non-scope" in p for p in T.preflight_problems({**GOODFACTS, "non_scope": 44}, NEWB))   # a partition missing
    assert any("(iii)" in p for p in T.preflight_problems({**GOODFACTS, "scope": 0}, NEWB))                             # the scope-cap partition missing
    assert any("(iii)" in p for p in T.preflight_problems({**GOODFACTS, "non_scope": 46}, NEWB))
    for st in ("stale", "error", "building", None):
        bad = {**GOODFACTS, "throughput": {"ga_dashas": st or "lit", "ga_positions": "lit"}} if st else {**GOODFACTS, "throughput": {"ga_positions": "lit"}}
        assert any("(iv)" in p and "ga_dashas" in p for p in T.preflight_problems(bad, NEWB)), st
    assert any("(iv)" in p and "ga_positions" in p for p in T.preflight_problems({**GOODFACTS, "throughput": {"ga_dashas": "lit", "ga_positions": "stale"}}, NEWB))


def test_the_facts_fetch_is_three_read_only_selects():
    class Cur:
        def __init__(self): self.qs, self.k = [], 0
        def execute(self, q, p=None): self.qs.append(q); self.k += 1
        def fetchall(self): return [("b1",)] if self.k == 1 else [("ga_dashas", "lit"), ("ga_positions", "lit")]
        def fetchone(self): return (45, 1)
    class Conn:
        def __init__(self): self.c = Cur()
        def cursor(self): return self.c
    c = Conn()
    assert T.fetch_preflight_facts(c, "x") == {"builds": ["b1"], "non_scope": 45, "scope": 1, "throughput": {"ga_dashas": "lit", "ga_positions": "lit"}}
    assert len(c.c.qs) == 3 and all(q.lstrip().lower().startswith("select") for q in c.c.qs)
    assert not any(w in q.lower() for q in c.c.qs for w in ("update ", "delete ", "insert ", "truncate"))
    assert "scope_cap" in c.c.qs[1]


def test_the_tool_refuses_another_system_or_level_4_and_reads_only_levels_1_to_3(monkeypatch, tmp_path):
    new = "11111111-1111-4111-8111-111111111111"
    assert T.main(["--new-build-id", new, "--system", "kalachakra", "--dry-run"], conn=FakeConn()) == 2
    assert T.main(["--new-build-id", new, "--max-level", "4", "--dry-run"], conn=FakeConn()) == 2
    seen = []
    def fake(conn, chart, **kw):
        seen.append(kw.get("levels")); return []
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", fake)
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: {"builds": [], "non_scope": 0, "scope": 0, "throughput": {}})
    T.main(["--new-build-id", new, "--dry-run"], conn=FakeConn())
    T.main(["--capture-old", str(tmp_path / "c.json")], conn=FakeConn())
    assert seen and all(lv == (1, 2, 3) for lv in seen), seen                         # never level 4


# ── Fable F-R17-1/2/5/6: the REAL reader, psycopg3, an empty read, the verifier's independent pin ────────────────────────────────────────────
import uuid as _uuid
from datetime import datetime as _dt, timezone as _tz

_NS = _uuid.UUID("12345678-1234-5678-1234-567812345678")
_KEYS = ["dasha_row_id", "system_id", "level_n", "parent_row_id", "lord_graha", "start_iso", "end_iso", "build_id", "verification_pass_status"]


def _uid(prefix, name):
    return str(_uuid.uuid5(_NS, f"{prefix}-{name}"))


def _db_tuples(prefix, build_id, shift_s=0):
    """build3() as the tuples a psycopg3 cursor returns for the reader's SELECT (real uuid ids, tz-aware datetimes, the reader's column order)."""
    out = []
    for r in build3(prefix, shift_s):
        name = r["dasha_row_id"].split("-", 1)[1]
        parent = r["parent_row_id"]
        out.append((_uid(prefix, name), "vimshottari", r["level_n"], None if parent is None else _uid(prefix, parent.split("-", 1)[1]), r["lord_graha"],
                    T._t(r["start_iso"]), T._t(r["end_iso"]), build_id, TIER))
    return out


def ref_rows(prefix, shift_s=0):
    """The pinned reference rows (permission.py) as a tree: old ids are the reference ids, new ids are fresh UUIDs; instants shifted by `shift_s`."""
    refs = list(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS)
    ids = {r["row_id"]: (r["row_id"] if prefix == "old" else str(_uuid.uuid4())) for r in refs}
    return [{"dasha_row_id": ids[r["row_id"]], "level_n": {"MD": 1, "AD": 2, "PD": 3}[r["level"]], "parent_row_id": None if r["parent_row_id"] is None else ids[r["parent_row_id"]],
             "lord_graha": r["lord"], "start_iso": T.full_iso(datetime.fromtimestamp(T._t(r["start_iso"]).timestamp() + shift_s, tz=timezone.utc)),
             "end_iso": T.full_iso(datetime.fromtimestamp(T._t(r["end_iso"]).timestamp() + shift_s, tz=timezone.utc)), "verification_pass_status": TIER,
             "build_id": OLDB if prefix == "old" else NEWB, "system_id": "vimshottari"} for r in refs]


CHART = PERM.DASHA_READ_CONTRACT["chart_id"]


def natal_dicts(build="1c092ffb-72eb-4614-8422-552ca6eae985"):
    return [{"fact_id": f"fact-{s_}", "fact_subject": s_, "longitude": str(100.0 + i), "tier": "single", "build_id": build} for i, s_ in enumerate(sorted(T.NATAL_SUBJECTS))]


def old_cap(rows=None, natal=None, **meta):
    return T.build_capture(CHART, OLDB, T.norm_rows(ref_rows("old")) if rows is None else rows, natal_dicts() if natal is None else natal, meta or None)


def write_old_cap(path, rows=None, natal=None):
    cap = old_cap(rows, natal)
    assert T.validate_capture(cap, CHART, OLDB) == [], T.validate_capture(cap, CHART, OLDB)
    T.write_capture(str(path), cap)
    return cap


def ref_db_tuples(build_id):
    return [(r["dasha_row_id"], "vimshottari", r["level_n"], r["parent_row_id"], r["lord_graha"], T._t(r["start_iso"]), T._t(r["end_iso"]), build_id, TIER) for r in ref_rows("old")]


def natal_tuples(build_id=None):
    b = build_id or "1c092ffb-72eb-4614-8422-552ca6eae985"
    return [(f"fact-{s_}", s_, 100.0 + i, "single", b) for i, s_ in enumerate(sorted(T.NATAL_SUBJECTS))]


def census_answer(sql):
    """The capture census queries (`capture_census`) answered the way the pinned production state would: one build, 45 + 1 partitions, both assets lit. Returns a cursor-like or None."""
    if "FROM public.asset_throughput" in sql:
        return type("C", (), {"fetchall": lambda s_: [("ga_dashas", "lit"), ("ga_positions", "lit")]})()
    if "count(*) FILTER" in sql:
        return type("C", (), {"fetchone": lambda s_: (45, 1)})()
    if sql.strip().startswith("SELECT DISTINCT build_id::text FROM public.chart_dashas"):
        return type("C", (), {"fetchall": lambda s_: [(OLDB,)]})()
    return None


class Psycopg3Shaped:
    """Exposes ONLY psycopg3's surface (`execute()` -> cursor with fetchall()) — the REAL reader (`DD.fetch_dasha_periods_multilevel`) is NOT mocked."""
    def __init__(self, by_build, natal=True):
        self.by_build, self.sql, self.natal = by_build, [], natal

    def execute(self, sql, params=None):
        self.sql.append((sql, params))
        ans = census_answer(sql)
        if ans is not None:
            return ans
        build = params[-1] if params else None
        if "is_truncated_at_window" in sql:
            rows = [(r[0], False, False) for r in self.by_build.get(str(params[1]), [])]
        else:
            rows = (natal_tuples() if self.natal else []) if "chart_facts" in sql else self.by_build.get(str(build), [])
        class Cur:
            def fetchall(self_):
                return list(rows)
        return Cur()


class Psycopg2Shaped:
    """Exposes ONLY psycopg2's surface (`cursor()`): the reader would raise AttributeError and swallow it into []."""
    def cursor(self):
        raise AssertionError("never reached: the tool must STOP by name before reading")


@real_reader
def test_the_UNMOCKED_reader_through_a_psycopg3_shaped_connection_feeds_capture_old(tmp_path):
    conn = Psycopg3Shaped({OLDB: ref_db_tuples(OLDB)})
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)], conn=conn) == 0 and p.exists()
    full = T.load_capture_full(str(p), PERM.DASHA_READ_CONTRACT["chart_id"], OLDB)
    rows = full["rows"]
    assert sorted({r["level_n"] for r in rows}) == [1, 2, 3] and len(rows) == len(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS) and all("trunc_start" in r and "trunc_end" in r for r in rows)
    assert [n["fact_subject"] for n in full["natal"]] == sorted(T.NATAL_SUBJECTS) and all(n["tier"] == "single" for n in full["natal"])         # the ten natal rows, same capture
    assert conn.sql and any("chart_dashas" in q for q, _ in conn.sql) and any("chart_facts" in q for q, _ in conn.sql)                         # the real SELECTs ran


@real_reader
def test_a_psycopg2_shaped_connection_STOPS_by_name_not_by_no_rows(tmp_path, capsys):
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)], conn=Psycopg2Shaped()) == 3
    err = capsys.readouterr().err
    assert "not a psycopg (v3) connection" in err and "no rows" not in err.lower() and not p.exists()


@real_reader
def test_an_empty_level_is_a_STOP_that_quotes_the_readers_own_logged_reason(tmp_path, capsys):
    class Boom(Psycopg3Shaped):
        def execute(self, sql, params=None):
            raise RuntimeError("relation chart_dashas is unreachable")                 # the reader swallows this into []
    assert T.main(["--capture-old", str(tmp_path / "c.json")], conn=Boom({})) == 3
    err = capsys.readouterr().err
    assert "NO rows for level(s) ['MD', 'AD', 'PD']" in err and "relation chart_dashas is unreachable" in err
    only12 = Psycopg3Shaped({OLDB: [r for r in _db_tuples("old", OLDB) if r[2] in (1, 2)]})                 # a level missing, the others present
    assert T.main(["--capture-old", str(tmp_path / "d.json")], conn=only12) == 3
    assert "['PD']" in capsys.readouterr().err


def test_a_dasha_read_conflict_is_a_named_refusal(monkeypatch, capsys):
    def boom(conn, chart, **kw):
        raise T.DD.DashaReadConflict("two rows, one identity, different contract fields")
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", boom)
    assert T.main(["--capture-old", "/nonexistent/x.json"], conn=FakeConn()) == 3
    assert "dasha read conflict" in capsys.readouterr().err


def test_the_notice_tolerance_must_be_at_least_one_second(tmp_path):
    for tol in (0, 0.5, -1):
        with pytest.raises(ValueError, match=">= 1"):
            T.load_notice(_notice(tmp_path, tolerance_seconds=tol))
    assert T.load_notice(_notice(tmp_path, tolerance_seconds=1))["tolerance_seconds"] == 1


def test_a_missing_or_empty_forensic_report_stops_before_any_read(tmp_path, capsys):
    new = NEWB
    assert T.main(["--new-build-id", new, "--forensic-report", str(tmp_path / "nope.md"), "--dry-run"], conn=FakeConn()) == 3
    assert "FORENSIC" in capsys.readouterr().err
    empty = tmp_path / "e.md"; empty.write_text("")
    assert T.main(["--new-build-id", new, "--forensic-report", str(empty), "--dry-run"], conn=FakeConn()) == 3


def _apply_world(tmp_path, ver_line=None, with_verifier=True):
    (tmp_path / "services" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "tests" / "l3" / "gochara_rules").mkdir(parents=True)
    (tmp_path / "services" / "gochara_rules" / "permission.py").write_text(pathlib.Path(PERM.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    if with_verifier:
        d = tmp_path / "services" / "gochara_kernel"; d.mkdir(parents=True)
        (d / "inventory_verifier.py").write_text(ver_line if ver_line is not None else f'_C_BUILD = "{OLDB}"\n', encoding="utf-8")
    ref = PERM.AD_ROWS[0]
    return [{"old": ref, "new": {"dasha_row_id": "99999999-9999-4999-8999-999999999999", "start_iso": "2013-01-14T09:13:56Z", "end_iso": "2014-01-11T14:11:56Z", "lord_graha": ref["lord"]}, "key": (2, (0,))}]


def test_apply_rewrites_BOTH_pin_constants_and_the_generated_test_asserts_they_are_equal(monkeypatch, tmp_path):
    maps = _apply_world(tmp_path)
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    changed = T.apply_repin(NEWB, maps, tmp_path)
    assert (tmp_path / "services" / "gochara_kernel" / "inventory_verifier.py").read_text() == f'_C_BUILD = "{NEWB}"\n'
    assert f'"build_id": "{NEWB}"' in (tmp_path / "services" / "gochara_rules" / "permission.py").read_text()
    assert any(c.endswith("inventory_verifier.py") for c in changed)
    gen = (tmp_path / "tests" / "l3" / "gochara_rules" / f"test_am10_repin_{NEWB[:8]}.py").read_text()
    assert "inventory_verifier._C_BUILD == DASHA_READ_CONTRACT" in gen


@pytest.mark.parametrize("ver_line,with_verifier", [(None, False), (f'_C_BUILD = "{OLDB}"\n_C_BUILD = "{OLDB}"\n', True), ('_C_BUILD = "someone-else"\n', True)])
def test_apply_STOPS_writing_nothing_when_the_verifiers_pin_cannot_be_rewritten(monkeypatch, tmp_path, ver_line, with_verifier):
    maps = _apply_world(tmp_path, ver_line=ver_line, with_verifier=with_verifier)
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    perm_before = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text()
    with pytest.raises(T.VerifierPinMissing):
        T.apply_repin(NEWB, maps, tmp_path)
    assert (tmp_path / "services" / "gochara_rules" / "permission.py").read_text() == perm_before          # nothing was written
    assert not list((tmp_path / "tests" / "l3").rglob("test_am10_repin_*.py"))


# ── ONE end-to-end test against a DISPOSABLE PostgreSQL with chart_dashas-SHAPED rows: real psycopg3 connection (read-only), the real reader, the real builds / pre-flight queries ─────────
import os as _os

_PG = _os.environ.get("GOCHARA_A51_TEST_DATABASE_URL")


@pytest.mark.skipif(not _PG, reason="needs GOCHARA_A51_TEST_DATABASE_URL (a disposable PostgreSQL server; the test creates and drops its own database)")
@real_reader
def test_end_to_end_against_a_disposable_database_with_real_chart_dashas_shaped_rows(monkeypatch, tmp_path, capsys):
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    base = conninfo_to_dict(_PG)
    admin = psycopg.connect(make_conninfo(**{**base, "dbname": "postgres"}), autocommit=True)
    name = f"repin_tool_{_uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        dsn = make_conninfo(**{**base, "dbname": name})
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute("""CREATE TABLE chart_dashas (dasha_row_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL, system_id text NOT NULL,
                           level_n int NOT NULL, parent_row_id uuid, lord_graha text NOT NULL, start_iso timestamptz NOT NULL, end_iso timestamptz NOT NULL,
                           verification_pass_status text NOT NULL, is_truncated_at_window_start boolean NOT NULL DEFAULT false, is_truncated_at_window_end boolean NOT NULL DEFAULT false)""")
            c.execute("CREATE TABLE asset_throughput (chart_id uuid, asset_id text, state text)")
            chart = PERM.DASHA_READ_CONTRACT["chart_id"]
            for r in [(x["dasha_row_id"], "vimshottari", x["level_n"], x["parent_row_id"], x["lord_graha"], T._t(x["start_iso"]), T._t(x["end_iso"]), NEWB, TIER) for x in ref_rows("new", 6993)]:       # the SETTLED-1 build, reference-shaped
                c.execute("INSERT INTO chart_dashas VALUES (%s,%s,'lahiri_chitrapaksha',%s,%s,%s,%s,%s,%s,%s,%s)", (r[0], chart, r[7], r[1], r[2], r[3], r[4], r[5], r[6], r[8]))
            # every other partition of the 45 + the scope-cap, one row each, the SAME build (the complete shape the guard requires)
            for system in ("vimshottari", "vimshottari_kp", "yogini", "ashtottari", "kalachakra", "mudda", "narayana", "naisargika", "chara_karaka"):
                for ay in ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta"):
                    if (system, ay) == ("vimshottari", "lahiri_chitrapaksha"):
                        continue
                    c.execute("INSERT INTO chart_dashas VALUES (%s,%s,%s,%s,%s,1,NULL,'Sun','2000-01-01','2010-01-01','two_pass_verified')", (str(_uuid.uuid4()), chart, ay, NEWB, system))
            c.execute("INSERT INTO chart_dashas VALUES (%s,%s,'lahiri_chitrapaksha',%s,'scope_cap',1,NULL,'Sun','2000-01-01','2010-01-01','two_pass_verified')", (str(_uuid.uuid4()), chart, NEWB))
            c.execute("INSERT INTO asset_throughput VALUES (%s,'ga_dashas','lit'), (%s,'ga_positions','lit')", (chart, chart))
        cap = tmp_path / "old.json"
        write_old_cap(cap)                                                                              # the old build is GONE from the database; its rows were captured BEFORE
        notice = tmp_path / "n.json"
        notice.write_text('{"settled_1": true, "source_message_id": "M1", "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha", "new_build_id": "%s", "expected_shift_seconds": {"1": 6993, "2": 6993, "3": 6993}, "tolerance_seconds": 1}' % NEWB)
        fr = tmp_path / "f.md"; fr.write_text("the seven FORENSIC anchors hold")
        monkeypatch.setenv("DATABASE_URL", dsn)
        rc = T.main(["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", str(notice), "--forensic-report", str(fr), "--dry-run"])        # conn=None ⇒ the REAL read-only psycopg3 connect
        out = capsys.readouterr()
        assert rc == 0 and "verdict: **CLEAN**" in out.out, (out.out[-900:], out.err[-400:])
        # and the same database with the OLD build coexisting is refused by the G6 guard through the real queries
        with psycopg.connect(dsn, autocommit=True) as c:
            for r in _db_tuples("old", OLDB):
                c.execute("INSERT INTO chart_dashas VALUES (%s,%s,'lahiri_chitrapaksha',%s,%s,%s,%s,%s,%s,%s,%s)", (r[0], chart, r[7], r[1], r[2], r[3], r[4], r[5], r[6], r[8]))
        rc = T.main(["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", str(notice), "--forensic-report", str(fr), "--dry-run"])
        assert rc == 3 and "exactly ONE" in capsys.readouterr().out
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


# ── Codex R17-1 (rest) / R17-3 / R17-4 / R17-5 / R17-6 / R17-7 ────────────────────────────────────────────────────────────────────────────────
import math as _math


def _stats_for(shift):
    old, new = T.index_paths(build3("old")), T.index_paths(build3("new", shift_s=shift))
    return T.shift_stats(old, new, T.match(old, new)["matched"])


def test_a_fractional_shift_just_inside_is_accepted_and_just_outside_is_refused_at_FULL_precision(tmp_path):
    n = T.load_notice(_notice(tmp_path, tolerance_seconds=1))                      # 6993 s ± 1 s on levels 1–3
    for ok in (6993.0, 6993.9, 6992.1, 6994.0, 6992.0):
        assert T.shift_problems(_stats_for(ok), n) == [], ok
    for bad in (6994.1, 6991.9, 6994.9, 6990.0, 6993 + 1e-3 + 1):
        assert T.shift_problems(_stats_for(bad), n), bad                           # whole-second truncation used to hide these


def test_a_NaN_or_infinite_measurement_is_refused_not_passed(tmp_path):
    n = T.load_notice(_notice(tmp_path))
    nan = {lv: {side: {"min": float("nan"), "max": float("nan"), "mean": 0, "n": 1} for side in ("start", "end")} for lv in (1, 2, 3)}
    assert T.shift_problems(nan, n)
    inf = {lv: {side: {"min": float("inf"), "max": float("inf"), "mean": 0, "n": 1} for side in ("start", "end")} for lv in (1, 2, 3)}
    assert T.shift_problems(inf, n)


def test_the_two_boundaries_are_checked_separately_when_the_notice_gives_start_and_end(tmp_path):
    n = T.load_notice(_notice(tmp_path, expected_shift_seconds={"1": {"start": 6993, "end": 7500}, "2": 6993, "3": 6993}, tolerance_seconds=1))
    probs = T.shift_problems(_stats_for(6993.0), n)
    assert probs and all("MD end" in p for p in probs)                              # only the MD END boundary disagrees


def test_full_precision_is_kept_in_the_rows_and_the_capture(tmp_path):
    rows = T.norm_rows([{**r, "start_iso": T._t(r["start_iso"]).replace(microsecond=250000)} for r in ref_rows("old")])
    assert all(".250000Z" in r["start_iso"] for r in rows)
    p = tmp_path / "c.json"; write_old_cap(p, rows)
    assert T.load_capture(str(p), CHART, OLDB) == rows


def _row(i, lvl, parent, lord="Mercury"):
    return {"dasha_row_id": i, "level_n": lvl, "parent_row_id": parent, "lord_graha": lord, "start_iso": "2000-01-01T00:00:00Z", "end_iso": "2001-01-01T00:00:00Z", "verification_pass_status": TIER, "build_id": "b"}


@pytest.mark.parametrize("rows,needle", [
    ([_row("m", 1, None), _row("a", 2, "a")], "its own parent"),                                        # self-parented
    ([_row("m", 1, None), _row("a", 2, "b"), _row("b", 2, "a")], "level 2"),                            # a two-row cycle at one level: wrong parent level
    ([_row("m", 1, None), _row("a", 2, None)], "NO parent"),                                            # unreachable from any root
    ([_row("m", 1, None), _row("a", 2, "ghost")], "missing parent"),
    ([_row("m", 1, None), _row("p", 3, "m")], "expected 2"),                                            # wrong parent level
    ([_row("m", 1, "m")], "level-1 row"),                                                              # a root with a parent
    ([_row("m", 1, None), _row("m", 1, None)], "duplicate row id"),
    ([_row("m", 1, None), _row("q", 4, "m")], "outside the in-scope levels"),
])
def test_a_malformed_tree_is_reported_by_name(rows, needle):
    probs = T.tree_problems(rows, "side")
    assert any(needle in p for p in probs), probs


def test_a_well_formed_tree_has_no_problems_and_every_row_is_indexed_exactly_once():
    rows = build3("old")
    assert T.tree_problems(rows, "side") == [] and len(T.index_paths(rows)) == len(rows)


def test_codexs_two_counterexamples_now_stop(monkeypatch, tmp_path, capsys):
    """(1) three old rows vs four new rows where the extra new row is self-parented; (2) four vs four where a lord changes on a row unreachable from a root."""
    base = [("m", 1, None, "Mercury"), ("a", 2, "m", "Mercury"), ("p", 3, "a", "Mercury")]
    def tup(prefix, extra=None, shift=0, drop=()):
        rows = [(f"{prefix}-{i}", lvl, None if par is None else f"{prefix}-{par}", lord) for i, lvl, par, lord in base]
        return rows + ([extra] if extra else [])
    def make(prefix, spec, shift=0):
        out = []
        for i, lvl, par, lord in spec:
            out.append({"dasha_row_id": i, "level_n": lvl, "parent_row_id": par, "lord_graha": lord,
                        "start_iso": T.full_iso(datetime.fromtimestamp(T._t("2000-01-01T00:00:00Z").timestamp() + 100 * len(out) + shift, tz=timezone.utc)),
                        "end_iso": T.full_iso(datetime.fromtimestamp(T._t("2001-01-01T00:00:00Z").timestamp() + 100 * len(out) + shift, tz=timezone.utc)),
                        "verification_pass_status": TIER, "build_id": prefix})
        return out
    old = make("old", tup("old"))
    new_bad = make("new", tup("new", extra=("new-x", 2, "new-x", "Venus")), shift=6993)                         # (1) an extra self-parented row
    new_probs = T.tree_problems(new_bad, "new build")
    assert any("its own parent" in p for p in new_probs)
    old_unreach = make("old", tup("old", extra=("old-u", 2, None, "Mercury")))
    new_unreach = make("new", tup("new", extra=("new-u", 2, None, "Venus")), shift=6993)                        # (2) the lord of an unreachable row changed
    assert T.tree_problems(old_unreach, "old build") and T.tree_problems(new_unreach, "new build")
    # the capture of a malformed OLD tree STOPS the comparison (load_capture refuses it)
    p = tmp_path / "cap.json"
    T.write_capture(str(p), old_cap(T.norm_rows(old_unreach)))                                   # written directly (acquisition would have refused it); load must refuse it too
    with pytest.raises(ValueError, match="malformed"):
        T.load_capture(str(p), CHART, OLDB)


def test_per_level_row_totals_must_be_equal(tmp_path):
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m={"matched": [], "only_old": [], "only_new": []}, flips=[], ref_problems=[], forensic_report="f")
    assert T.decide(**good, old_totals={1: 2, 2: 2, 3: 1}, new_totals={1: 2, 2: 2, 3: 1}) == []
    assert any("per-level row totals differ" in s for s in T.decide(**good, old_totals={1: 2, 2: 2, 3: 1}, new_totals={1: 2, 2: 3, 3: 1}))
    assert any("own parent" in s for s in T.decide(**good, tree_issues=["new build: row x is its own parent"]))


def test_the_notice_must_name_the_same_build_as_the_cli_and_the_output_binds_the_notice_and_forensic_hashes(monkeypatch, tmp_path, capsys):
    rows_new = T.norm_rows(ref_rows("new", 6993))
    cap = tmp_path / "old.json"; write_old_cap(cap)
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, build_id=None, **kw: rows_new if build_id == NEWB else [])
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: GOODFACTS)
    fr = tmp_path / "f.md"; fr.write_text("anchors")
    args = lambda notice: ["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", notice, "--forensic-report", str(fr), "--dry-run"]
    rc = T.main(args(_notice(tmp_path)), conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 0 and "verdict: **CLEAN**" in out
    assert "settled notice sha256:" in out and "forensic report sha256:" in out and "EXISTS and is NON-EMPTY ONLY" in out and "NOT independent validation" in out
    rc = T.main(args(_notice(tmp_path, new_build_id="22222222-2222-4222-8222-222222222222")), conn=FakeConn())
    assert rc == 3 and "names build 22222222" in capsys.readouterr().out                    # notice != --new-build-id
    rc = T.main(args(_notice(tmp_path, new_build_id=None)), conn=FakeConn())
    assert rc == 3 and "new_build_id is required" in capsys.readouterr().err               # a notice without its build is refused outright


def test_apply_needs_only_SETTLED_received_and_says_the_production_hold_stays(monkeypatch, tmp_path, capsys):
    new = NEWB
    assert T.main(["--new-build-id", new, "--apply"], conn=FakeConn()) == 2
    assert "SETTLED-1 received" in capsys.readouterr().err
    with pytest.raises(SystemExit) as exc:
        T.main(["--new-build-id", new, "--apply", "--settled-received", "M1", "--hold-lifted", "M2"], conn=FakeConn())        # the old flag no longer exists (argparse error)
    assert exc.value.code == 2


class _Boom:
    """Any use of the connection fails the test: mode validation must happen BEFORE a connection is used."""
    def __getattr__(self, name):
        raise AssertionError(f"the connection was touched ({name}) before mode validation")


@pytest.mark.parametrize("argv", [
    ["--capture-old", "{p}", "--dry-run"],
    ["--capture-old", "{p}", "--apply"],
    ["--capture-old", "{p}", "--apply", "--dry-run", "--settled-received", "M1"],
    ["--capture-old", "{p}", "--new-build-id", NEWB],
    ["--capture-old", "{p}", "--settled-notice", "x.json"],
    ["--capture-old", "{p}", "--old-rows", "x.json"],
    ["--capture-old", "{p}", "--rulings", "x.json"],
    ["--capture-old", "{p}", "--forensic-report", "x.md"],
    ["--capture-old", "{p}", "--out", "x.md"],
    ["--capture-old", "{p}", "--settled-received", "M1"],
    ["--dry-run"],                                                                       # compare mode without --new-build-id
    ["--new-build-id", "not-a-uuid"],
    ["--new-build-id", NEWB, "--apply", "--dry-run", "--settled-received", "M1"],
    ["--new-build-id", NEWB, "--rulings", "r.json"],                                     # rulings without --apply
    ["--new-build-id", NEWB, "--apply"],                                                 # apply without the announcement
    ["--new-build-id", NEWB, "--system", "kalachakra"],
    ["--new-build-id", NEWB, "--max-level", "4"],
    ["--capture-old", "{p}", "--system", "yogini"],
])
def test_every_mode_combination_is_validated_BEFORE_any_capture_or_connection_and_writes_nothing(tmp_path, argv):
    p = tmp_path / "cap.json"
    args = [x.replace("{p}", str(p)) for x in argv]
    assert T.main(args, conn=_Boom()) == 2
    assert not p.exists() and not list(tmp_path.iterdir())                                # nothing written by any refused combination


def test_a_dry_run_writes_nothing_on_every_dispatch_path(monkeypatch, tmp_path):
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, **kw: [])
    out = tmp_path / "evidence.md"
    assert T.main(["--new-build-id", NEWB, "--dry-run", "--out", str(out)], conn=FakeConn()) == 3
    assert not out.exists() and not list(tmp_path.iterdir())


@pytest.mark.skipif(not _PG, reason="needs GOCHARA_A51_TEST_DATABASE_URL (a disposable PostgreSQL server; the test creates and drops its own database)")
@real_reader
def test_the_NORMAL_cli_capture_path_against_a_disposable_database_without_a_pre_S_L1_replacement_build(monkeypatch, tmp_path, capsys):
    """Codex R17-1 (rest): `--capture-old` through `conn=None` — the REAL psycopg3 read-only connect and the REAL reader — with NO --new-build-id and no lambda reader."""
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    base = conninfo_to_dict(_PG)
    admin = psycopg.connect(make_conninfo(**{**base, "dbname": "postgres"}), autocommit=True)
    name = f"repin_cap_{_uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        dsn = make_conninfo(**{**base, "dbname": name})
        chart = PERM.DASHA_READ_CONTRACT["chart_id"]
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute("""CREATE TABLE chart_dashas (dasha_row_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL, system_id text NOT NULL,
                           level_n int NOT NULL, parent_row_id uuid, lord_graha text NOT NULL, start_iso timestamptz NOT NULL, end_iso timestamptz NOT NULL,
                           verification_pass_status text NOT NULL, is_truncated_at_window_start boolean NOT NULL DEFAULT false, is_truncated_at_window_end boolean NOT NULL DEFAULT false)""")
            for r in ref_db_tuples(OLDB):                                                               # BEFORE S-L1: the pinned (old) build is what the database holds
                c.execute("INSERT INTO chart_dashas (dasha_row_id, chart_id, ayanamsha_id, build_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso, verification_pass_status)"
                          " VALUES (%s,%s,'lahiri_chitrapaksha',%s,%s,%s,%s,%s,%s,%s,%s)", (r[0], chart, r[7], r[1], r[2], r[3], r[4], r[5], r[6], r[8]))
            c.execute("CREATE TABLE asset_throughput (chart_id uuid, asset_id text, state text)")
            c.execute("INSERT INTO asset_throughput VALUES (%s,'ga_dashas','lit'), (%s,'ga_positions','lit')", (chart, chart))
            c.execute("""CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL, fact_category text NOT NULL,
                           fact_subject text NOT NULL, fact_key text NOT NULL, fact_value_num numeric, verification_pass_status text)""")
            for i, subj in enumerate(sorted(T.NATAL_SUBJECTS)):                                          # the ten natal rows (+ one other fact the capture must NOT take)
                c.execute("INSERT INTO chart_facts VALUES (%s,%s,'lahiri_chitrapaksha','1c092ffb-72eb-4614-8422-552ca6eae985','graha_position',%s,'longitude_sidereal',%s,'single')", (f"f-{subj}", chart, subj, 100.123456789 + i))
            c.execute("INSERT INTO chart_facts VALUES ('f-other',%s,'lahiri_chitrapaksha','1c092ffb-72eb-4614-8422-552ca6eae985','house_chalit','H1','cusp_lon',5,'single')", (chart,))
        monkeypatch.setenv("DATABASE_URL", dsn)
        cap = tmp_path / "old.json"
        assert T.main(["--capture-old", str(cap)]) == 0 and cap.exists()                                  # no conn=, no --new-build-id
        out = capsys.readouterr().out
        full = T.load_capture_full(str(cap), chart, OLDB)
        rows = full["rows"]
        assert sorted({r["level_n"] for r in rows}) == [1, 2, 3] and len(rows) == len(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS) and T.capture_problems(rows) == []
        assert [n["fact_subject"] for n in full["natal"]] == sorted(T.NATAL_SUBJECTS) and all(n["tier"] == "single" and __import__("decimal").Decimal(n["longitude"]) == __import__("decimal").Decimal("100.123456789") + i for i, n in enumerate(full["natal"]))      # exact numeric text, full precision
        # ONE repeatable-read read-only transaction: the same snapshot at the start and the end, recorded in the file; the sha256 and the elapsed time are printed
        assert full["meta"]["snapshot_start"] == full["meta"]["snapshot_end"] and full["meta"]["transaction_isolation"] == "repeatable read" and full["meta"]["transaction_read_only"] == "on"
        assert f"sha256 {full['sha256']}" in out and "connection closed; elapsed" in out and f"whole-file sha256 {T.file_sha256(str(cap))}" in out
        assert full["meta"]["census"]["chart_dashas_build_ids"] == [OLDB] and full["meta"]["census"]["asset_throughput"] == {"ga_dashas": "lit", "ga_positions": "lit"}          # from the SAME snapshot
        # NO LINGERING SESSION: the tool's connection (application_name repin_capture) is gone when main() returns
        n = admin.execute("SELECT count(*) FROM pg_stat_activity WHERE application_name = 'repin_capture'").fetchone()[0]
        assert n == 0, f"{n} lingering repin_capture session(s)"
        # the READ-ONLY helper still refuses a write
        with T.open_readonly_connection() as ro:
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                ro.execute("INSERT INTO chart_dashas SELECT * FROM chart_dashas LIMIT 1")
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


# ── pairing by STRUCTURE only (steward M20261003T003446-1f8d, -c27f; Suvarṇa): every dasha_row_id changes at S-L1; children are paired by LORD SEQUENCE; a differing child count REFUSES the subtree ──
def _uuid_rows(prefix, shift_s=0, with_pd=True, drop_ad1=False):
    rows = build3(prefix, shift_s) if with_pd else build(prefix, shift_s)
    if drop_ad1:
        rows = [r for r in rows if not r["dasha_row_id"].endswith("a1")]
    ids = {r["dasha_row_id"]: str(_uuid.uuid4()) for r in rows}                                   # EVERY id is a fresh random uuid, different on each side
    return [{**r, "dasha_row_id": ids[r["dasha_row_id"]], "parent_row_id": None if r["parent_row_id"] is None else ids[r["parent_row_id"]]} for r in rows]


def test_every_id_differs_and_the_rows_still_pair_by_structure_alone():
    old, new = _uuid_rows("old"), _uuid_rows("new", shift_s=6993)
    assert not ({r["dasha_row_id"] for r in old} & {r["dasha_row_id"] for r in new})
    oi, ni = T.index_paths(old), T.index_paths(new)
    m = T.match(oi, ni)
    assert len(m["matched"]) == len(old) and not m["only_old"] and not m["only_new"] and T.subtree_refusals(oi, ni) == []
    assert T.shift_stats(oi, ni, m["matched"])[1]["start"]["min"] == 6993.0


def test_the_reference_rows_are_found_by_structure_and_apply_rewrites_their_ids_from_the_pairing_when_every_id_differs(monkeypatch, tmp_path):
    ref_rows = list(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS)
    def tree(prefix, shift):
        out = []
        for ref in ref_rows:
            pid = ref["parent_row_id"]
            out.append({"dasha_row_id": ref["row_id"] if prefix == "old" else str(_uuid.uuid4()), "level_n": {"MD": 1, "AD": 2, "PD": 3}[ref["level"]], "parent_row_id": pid,
                        "lord_graha": ref["lord"],
                        "start_iso": T.full_iso(datetime.fromtimestamp(T._t(ref["start_iso"]).timestamp() + shift, tz=timezone.utc)),
                        "end_iso": T.full_iso(datetime.fromtimestamp(T._t(ref["end_iso"]).timestamp() + shift, tz=timezone.utc))})
        if prefix == "new":                                                                       # re-link the parents to the NEW ids (every id differs, the structure does not)
            newid = {ref["row_id"]: r["dasha_row_id"] for ref, r in zip(ref_rows, out)}
            for r, ref in zip(out, ref_rows):
                r["parent_row_id"] = None if ref["parent_row_id"] is None else newid[ref["parent_row_id"]]
        return out
    old, new = T.index_paths(tree("old", 0)), T.index_paths(tree("new", 6993))
    maps, probs = T.remeasure_reference_rows(old, new)
    assert probs == [] and len(maps) == len(ref_rows) and all(x["new"]["dasha_row_id"] != x["old"]["row_id"] for x in maps)
    _apply = _apply_world(tmp_path)
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    T.apply_repin(NEWB, maps, tmp_path)
    perm = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text()
    assert all(x["new"]["dasha_row_id"] in perm and x["old"]["row_id"] not in perm for x in maps)             # the ids were rewritten FROM THE STRUCTURAL PAIRING


def test_a_parent_whose_child_count_changes_is_REFUSED_listed_and_never_paired():
    old, new = _uuid_rows("old"), _uuid_rows("new", shift_s=6993, drop_ad1=True)                   # MD0 had two ADs, now one
    oi, ni = T.index_paths(old), T.index_paths(new)
    refusals = T.subtree_refusals(oi, ni)
    assert [(r["parent"], r["old"], r["new"]) for r in refusals] == [((("Mercury", 0),), ["Mercury", "Ketu"], ["Mercury"])]
    m = T.match(oi, ni)
    kept = [k for k in m["matched"] if not T.under_refused(k, refusals)]
    assert all(not (k[1][:1] == (("Mercury", 0),) and len(k[1]) > 1) for k in kept)                # nothing under the refused parent is paired (no best guess)
    good = dict(new_tier_ok=True, new_integrity={"orphans": [], "duplicates": 0}, m=m, flips=[], ref_problems=[], forensic_report="f.md")
    stops = T.decide(**good, refused_subtrees=refusals, old_totals=T.level_totals(old), new_totals=T.level_totals(new))
    assert any("REFUSED SUBTREE under Mercury#0" in s for s in stops) and any("per-level row totals differ" in s for s in stops)


def test_a_changed_lord_sequence_with_the_same_count_is_also_refused():
    old, new = _uuid_rows("old"), _uuid_rows("new", shift_s=6993)
    for r in new:
        if r["lord_graha"] == "Ketu" and r["level_n"] == 2:
            r["lord_graha"] = "Venus"
    assert T.subtree_refusals(T.index_paths(old), T.index_paths(new))[0]["new"] == ["Mercury", "Venus"]


# ── the pre-S-L1 CAPTURE (Suvarṇa via the steward): ONE REPEATABLE READ read-only transaction, daśā L1–3 AND the ten natal rows, file + sha256, connection closed, elapsed printed ─────────
class SpyConn:
    """psycopg3-shaped; records every statement and the lifecycle calls — proves ONE transaction (no commit), rolled back, then closed."""
    def __init__(self, natal=True):
        self.calls, self.closed, self.rolled_back, self.committed = [], 0, 0, 0
        self.natal = natal
        self.isolation_level = None
        self.read_only = None

    def execute(self, sql, params=None):
        self.calls.append(" ".join(sql.split())[:400])
        outer = self
        ans = census_answer(sql)
        if ans is not None:
            return ans
        if "pg_current_snapshot" in sql:
            return type("C", (), {"fetchone": lambda s_: ("100:200:",)})()
        if sql.strip().upper().startswith("SHOW TRANSACTION_ISOLATION"):
            return type("C", (), {"fetchone": lambda s_: ("repeatable read",)})()
        if sql.strip().upper().startswith("SHOW TRANSACTION_READ_ONLY"):
            return type("C", (), {"fetchone": lambda s_: ("on",)})()
        if "chart_facts" in sql:
            return type("C", (), {"fetchall": lambda s_: natal_tuples()})()
        if "is_truncated_at_window" in sql:
            return type("C", (), {"fetchall": lambda s_: [(r[0], False, False) for r in ref_db_tuples(OLDB)]})()
        return type("C", (), {"fetchall": lambda s_: ref_db_tuples(OLDB)})()

    def commit(self): self.committed += 1
    def rollback(self): self.rolled_back += 1
    def close(self): self.closed += 1


@real_reader
def test_the_capture_is_ONE_transaction_that_is_rolled_back_never_committed_and_the_connection_is_closed(monkeypatch, tmp_path, capsys):
    spy = SpyConn()
    monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 0
    assert spy.committed == 0 and spy.rolled_back == 1 and spy.closed == 1                        # one transaction, ended by rollback, then closed
    assert spy.calls[0].startswith("SELECT pg_current_snapshot")                                   # the very first statement opens it
    assert any("chart_dashas" in c for c in spy.calls) and any("chart_facts" in c for c in spy.calls) and any("is_truncated_at_window" in c for c in spy.calls) and spy.calls[-1].startswith("SELECT pg_current_snapshot")
    out = capsys.readouterr().out
    assert "sha256 " in out and "repeatable read read-only transaction, connection closed; elapsed" in out
    full = T.load_capture_full(str(p), PERM.DASHA_READ_CONTRACT["chart_id"], OLDB)
    assert full["meta"]["snapshot_start"] == full["meta"]["snapshot_end"] and full["meta"]["transaction_isolation"] == "repeatable read" and len(full["natal"]) == 10
    assert full["sha256"] in out and full["meta"]["elapsed_seconds"] >= 0


@real_reader
def test_a_snapshot_that_changes_during_the_capture_refuses_and_still_closes_the_connection(monkeypatch, tmp_path, capsys):
    class Moving(SpyConn):
        n = 0
        def execute(self, sql, params=None):
            if "pg_current_snapshot" in sql:
                Moving.n += 1
                return type("C", (), {"fetchone": lambda s_, n=Moving.n: (f"{n}:{n}:",)})()
            return super().execute(sql, params)
    spy = Moving()
    monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 3 and not p.exists()
    assert "NOT one transaction" in capsys.readouterr().err and spy.closed == 1 and spy.rolled_back == 1 and spy.committed == 0


@real_reader
def test_a_wrong_isolation_or_a_missing_natal_row_refuses(monkeypatch, tmp_path, capsys):
    class ReadCommitted(SpyConn):
        def execute(self, sql, params=None):
            if sql.strip().upper().startswith("SHOW TRANSACTION_ISOLATION"):
                return type("C", (), {"fetchone": lambda s_: ("read committed",)})()
            return super().execute(sql, params)
    spy = ReadCommitted(); monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    assert T.main(["--capture-old", str(tmp_path / "a.json")], conn=None) == 3 and "not repeatable read" in capsys.readouterr().err and spy.closed == 1
    spy2 = SpyConn(); monkeypatch.setattr(T, "open_capture_connection", lambda: spy2)
    monkeypatch.setattr(T, "read_natal", lambda conn, chart: (_ for _ in ()).throw(T.NatalRefused("nine rows")))
    assert T.main(["--capture-old", str(tmp_path / "b.json")]) == 3 and "nine rows" in capsys.readouterr().err and spy2.closed == 1 and not (tmp_path / "b.json").exists()


def test_the_natal_read_demands_exactly_the_ten_subjects():
    class C:
        def __init__(self, rows): self.rows = rows
        def execute(self, sql, params=None):
            return type("Cur", (), {"fetchall": lambda s_: self.rows})()
    assert len(T.read_natal(C(natal_tuples()), "c")) == 10
    with pytest.raises(T.NatalRefused):
        T.read_natal(C(natal_tuples()[:9]), "c")
    with pytest.raises(T.NatalRefused):
        T.read_natal(C(natal_tuples() + [("f", "RAH_TRUE", 1, "single", "b")]), "c")


# ── Fable F-R18-1: the writer CLIPS the first/last row of every level to the window; Codex R18-1/R18-2: capture validation at acquisition and load ─────────────────────────────────────────
def clipped_world(prefix, shift_s=0):
    """A WRITER-SHAPED tree: the ten real reference rows (shifted) plus the first and last row of every level clipped to 1950-01-01 / 2100-12-31 — flags set at levels 1–2 and NOT at level 3
    (the writer passes them only there), clipped edges do not move, every other edge shifts."""
    refs = list(PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS)
    rows = ref_rows(prefix, shift_s)
    for r in rows:
        r["trunc_start"] = r["trunc_end"] = False
    md = next(r for r in rows if r["level_n"] == 1)
    def mk(i, lvl, parent, lord, a, b, ts=False, te=False):
        return {"dasha_row_id": f"{prefix}-{i}" if prefix == "old" else str(_uuid.uuid4()), "level_n": lvl, "parent_row_id": parent, "lord_graha": lord, "start_iso": a, "end_iso": b,
                "verification_pass_status": TIER, "build_id": OLDB if prefix == "old" else NEWB, "system_id": "vimshottari", "trunc_start": ts, "trunc_end": te}
    # old ids for extras must be deterministic uuids so the new side can re-link; use uuid5 on the name
    nm = lambda i: str(_uuid.uuid5(_NS, f"{prefix}-{i}"))
    fm = mk("fm", 1, None, "Moon", T.WINDOW_START_ISO, md["start_iso"], ts=True); fm["dasha_row_id"] = nm("fm")
    lm = mk("lm", 1, None, "Venus", md["end_iso"], T.WINDOW_END_ISO, te=True); lm["dasha_row_id"] = nm("lm")
    fa = mk("fa", 2, fm["dasha_row_id"], "Moon", T.WINDOW_START_ISO, fm["end_iso"], ts=True); fa["dasha_row_id"] = nm("fa")
    la = mk("la", 2, lm["dasha_row_id"], "Venus", lm["start_iso"], T.WINDOW_END_ISO, te=True); la["dasha_row_id"] = nm("la")
    fp = mk("fp", 3, fa["dasha_row_id"], "Moon", T.WINDOW_START_ISO, fa["end_iso"]); fp["dasha_row_id"] = nm("fp")                       # level 3: clipped, NOT flagged
    lp = mk("lp", 3, la["dasha_row_id"], "Venus", la["start_iso"], T.WINDOW_END_ISO); lp["dasha_row_id"] = nm("lp")
    return rows + [fm, lm, fa, la, fp, lp]


def _flags_of(rows):
    return {r["dasha_row_id"]: (bool(r.get("trunc_start")), bool(r.get("trunc_end"))) for r in rows}


def _clip_cli(monkeypatch, tmp_path, new_rows, notice_over=None):
    old = clipped_world("old")
    cap = tmp_path / "old.json"; write_old_cap(cap, T.norm_rows([dict(r) for r in old]) if False else old)
    new_plain = [dict(r) for r in new_rows]
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, build_id=None, **kw: [{k: v for k, v in r.items() if not k.startswith("trunc_")} for r in new_plain] if build_id == NEWB else [])
    monkeypatch.setattr(T, "read_truncation", lambda conn, chart, build: _flags_of(new_plain))
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: len(new_plain)})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: GOODFACTS)
    fr = tmp_path / "f.md"; fr.write_text("anchors")
    return ["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", _notice(tmp_path, new_build_id=NEWB, **(notice_over or {})), "--forensic-report", str(fr), "--dry-run"]


@real_reader
def test_a_writer_shaped_clipped_tree_reaches_CLEAN_through_main_with_the_real_reference_rows_and_the_clipped_edges_excluded(monkeypatch, tmp_path, capsys):
    new = clipped_world("new", 6993)                      # interior +6,993 s; the clipped edges are NOT moved by the builder
    for r in new:
        if r["trunc_start"] or r["start_iso"] == T.WINDOW_START_ISO:
            r["start_iso"] = T.WINDOW_START_ISO
        if r["trunc_end"] or r["end_iso"] == T.WINDOW_END_ISO:
            r["end_iso"] = T.WINDOW_END_ISO
    # (the builder's clipped edges stay at the bounds; ref_rows shifted every reference instant, which are all interior)
    args = _clip_cli(monkeypatch, tmp_path, [r for r in new])
    # NOTE: remeasure_reference_rows is NOT monkeypatched — the ten real reference rows are found in the clipped tree by structure
    rc = T.main(args, conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 0 and "verdict: **CLEAN**" in out, out[-1200:]
    assert "window-clipped edges excluded" in out and "MD start 1 / end 1" in out and "AD start 1 / end 1" in out and "PD start 1 / end 1" in out
    assert "| MD | start | 6993" in out and "| PD | end | 6993" in out                                      # the statistics are over the UNCLIPPED edges only


@real_reader
def test_a_clip_that_exists_on_ONE_build_only_is_a_STOP_by_name(monkeypatch, tmp_path, capsys):
    new = clipped_world("new", 6993)
    for r in new:
        if r["start_iso"] == T.WINDOW_START_ISO and r["level_n"] == 1:
            r["start_iso"] = "1950-01-01T00:01:40Z"; r["trunc_start"] = False                         # the new build no longer clips the first MD
    args = _clip_cli(monkeypatch, tmp_path, new)
    rc = T.main(args, conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 3 and "window-edge status changed" in out and "MD start edge" in out


@real_reader
def test_a_flag_set_off_the_window_bound_or_a_clipped_edge_that_moved_is_a_STOP(monkeypatch, tmp_path, capsys):
    new = clipped_world("new", 6993)
    first = next(r for r in new if r["level_n"] == 1 and r["start_iso"] == T.WINDOW_START_ISO)
    first["start_iso"] = "1950-01-01T00:00:10Z"                                                       # flagged truncated, but the instant is not the bound
    args = _clip_cli(monkeypatch, tmp_path, new)
    assert T.main(args, conn=FakeConn()) == 3
    out = capsys.readouterr().out
    assert "FLAGGED truncated but its instant is not the window bound" in out or "window-edge status changed" in out


def test_a_level_with_zero_unclipped_measurements_is_a_STOP(tmp_path):
    n = T.load_notice(_notice(tmp_path))
    stats = {1: {"end": {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 1}}, 2: {"start": {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 1}, "end": {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 1}},
             3: {"start": {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 1}, "end": {"min": 6993.0, "max": 6993.0, "mean": 6993.0, "n": 1}}}
    probs = T.shift_problems(stats, n)
    assert any("MD start: ZERO unclipped measurements" in p for p in probs)


def test_an_edge_is_clipped_by_the_flag_or_by_the_window_bound_instant():
    row = {"start_iso": T.WINDOW_START_ISO, "end_iso": "2000-01-01T00:00:00Z", "trunc_start": False, "trunc_end": False}
    assert T.edge_clipped(row, "start") is True and T.edge_clipped(row, "end") is False                 # level-3 shape: clipped, unflagged
    assert T.edge_clipped({**row, "start_iso": "1951-01-01T00:00:00Z", "trunc_start": True}, "start") is True
    assert T.edge_clipped({**row, "end_iso": T.WINDOW_END_ISO}, "end") is True


# ── capture acquisition = the loader's validation; NO artifact on a malformed capture ───────────────────────────────────────────────────────────────────────────────────────
def _spy_with_rows(rows):
    class S(SpyConn):
        def execute(self, sql, params=None):
            if "is_truncated_at_window" not in sql and "chart_facts" not in sql and "pg_current_snapshot" not in sql and not sql.strip().upper().startswith("SHOW") and census_answer(sql) is None:
                return type("C", (), {"fetchall": lambda s_: rows})()
            return super().execute(sql, params)
    return S()


@real_reader
def test_a_self_parented_row_is_a_named_STOP_at_acquisition_with_NO_artifact_and_the_transaction_is_ended(monkeypatch, tmp_path, capsys):
    tuples = ref_db_tuples(OLDB)
    bad = list(tuples)
    pd = next(i for i, r in enumerate(bad) if r[2] == 3)
    bad[pd] = (*bad[pd][:3], bad[pd][0], *bad[pd][4:])                                              # a PD row that is its OWN parent
    spy = _spy_with_rows(bad)
    monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 3                                                    # through the NORMAL capture dispatch
    err = capsys.readouterr().err
    assert "its own parent" in err and "nothing written" in err and not p.exists()
    assert spy.closed == 1 and spy.rolled_back == 1 and spy.committed == 0                          # rollback + close preserved on the refusal


@real_reader
def test_a_foreign_build_or_a_missing_reference_row_is_a_named_STOP_at_acquisition(monkeypatch, tmp_path, capsys):
    foreign = [(*r[:7], "22222222-2222-4222-8222-222222222222", *r[8:]) for r in ref_db_tuples(OLDB)]
    spy = _spy_with_rows(foreign); monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 3 and "foreign or mixed build" in capsys.readouterr().err and not p.exists()
    missing = ref_db_tuples(OLDB)[1:]                                                                # the MD reference row is absent
    spy2 = _spy_with_rows(missing); monkeypatch.setattr(T, "open_capture_connection", lambda: spy2)
    assert T.main(["--capture-old", str(p)]) == 3 and not p.exists() and spy2.closed == 1


@real_reader
def test_the_capture_retains_its_provenance_and_prints_the_whole_file_checksum_separately(monkeypatch, tmp_path, capsys):
    spy = SpyConn(); monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 0
    out = capsys.readouterr().out
    full = T.load_capture_full(str(p), CHART, OLDB)
    m = full["meta"]
    assert m["tool_sha256"] == T.file_sha256(T.__file__) and "tool_commit" in m and full["selection"] == T.selection_contract()
    assert m["counts_by_level"] == {str(k): v for k, v in T.level_totals(full["rows"]).items()} and m["dasha_build_ids"] == [OLDB] and len(m["natal_build_ids"]) == 1
    assert m["census"] == {"chart_dashas_build_ids": [OLDB], "partitions_non_scope": 45, "partitions_scope_cap": 1, "asset_throughput": {"ga_dashas": "lit", "ga_positions": "lit"}}
    assert f"sha256 {full['sha256']}" in out and f"whole-file sha256 {T.file_sha256(str(p))}" in out and full["sha256"] != T.file_sha256(str(p))


# ── the W0 fallback ingestion (Fable F-R18-4) ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _w0_file(tmp_path, mutate=None):
    import json as _j
    d = {"chart_id": CHART, "build_id": OLDB, "rows": [{k: v for k, v in r.items()} for r in ref_rows("old")], "natal": natal_dicts()}
    if mutate:
        mutate(d)
    p = tmp_path / "w0.json"
    p.write_text(_j.dumps(d))
    return p, T.file_sha256(str(p))


def test_the_w0_baseline_is_imported_only_against_its_named_checksum_and_validated_like_a_capture(tmp_path, capsys):
    p, chk = _w0_file(tmp_path)
    out = tmp_path / "cap.json"
    assert T.main(["--import-w0", str(p), "--w0-checksum", chk, "--w0-capture-out", str(out)]) == 0
    full = T.load_capture_full(str(out), CHART, OLDB)
    assert full["meta"]["source"] == "w0" and full["meta"]["w0_sha256"] == chk
    out2 = tmp_path / "cap2.json"
    assert T.main(["--import-w0", str(p), "--w0-checksum", "0" * 64, "--w0-capture-out", str(out2)]) == 3 and not out2.exists()          # the checksum SETTLED-1 names must match
    bad_p, bad_chk = _w0_file(tmp_path, lambda d: d["rows"][-1].__setitem__("parent_row_id", d["rows"][-1]["dasha_row_id"]))                  # a self-parented row
    assert T.main(["--import-w0", str(bad_p), "--w0-checksum", bad_chk, "--w0-capture-out", str(out2)]) == 3 and not out2.exists()
    assert "could not later be compared" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["--import-w0", "x"], ["--import-w0", "x", "--w0-checksum", "a"], ["--import-w0", "x", "--w0-checksum", "a", "--w0-capture-out", "y", "--apply"],
                                  ["--import-w0", "x", "--w0-checksum", "a", "--w0-capture-out", "y", "--capture-old", "z"], ["--w0-checksum", "a"]])
def test_the_w0_import_mode_is_validated_before_anything_is_read(tmp_path, argv):
    assert T.main(argv, conn=_Boom()) == 2


# ── Fable F-R18-5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_two_new_instants_for_one_old_literal_stop_apply_before_writing(monkeypatch, tmp_path):
    maps = _apply_world(tmp_path)
    ref = maps[0]["old"]
    maps.append({"old": ref, "new": {**maps[0]["new"], "start_iso": "2013-02-02T02:02:02Z"}, "key": (2, (("x", 0),))})                       # the same old start maps to a SECOND new instant
    monkeypatch.setattr(T, "SIDECAR", tmp_path)
    before = (tmp_path / "services" / "gochara_rules" / "permission.py").read_text()
    with pytest.raises(T.VerifierPinMissing, match="literal conflict"):
        T.apply_repin(NEWB, maps, tmp_path)
    assert (tmp_path / "services" / "gochara_rules" / "permission.py").read_text() == before


def test_uuids_are_compared_in_one_canonical_form_and_apply_is_refused_for_another_chart(monkeypatch, tmp_path, capsys):
    assert T.canon_uuid(NEWB.upper()) == NEWB
    n = T.load_notice(_notice(tmp_path, new_build_id=NEWB.upper()))
    assert n["new_build_id"] == NEWB                                                                  # the notice's id is canonicalised
    assert T.main(["--new-build-id", NEWB, "--apply", "--settled-received", "M1", "--chart-id", "11111111-0000-4000-8000-000000000000"], conn=_Boom()) == 2
    assert "canonical chart" in capsys.readouterr().err


# ── Codex R19-2 / Fable F-R19-3 / F-R19-4 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
class AllClippedMD(SpyConn):
    """A pathological but valid-looking baseline: the sole reference MD carries BOTH window bounds (flagged at level 1), so level MD has no measurable boundary at all."""
    def execute(self, sql, params=None):
        if "is_truncated_at_window" in sql:
            return type("C", (), {"fetchall": lambda s_: [(r[0], r[2] == 1, r[2] == 1) for r in ref_db_tuples(OLDB)]})()
        if "chart_dashas" in sql and "is_truncated_at_window" not in sql and "count(*)" not in sql and "DISTINCT" not in sql and "FROM public.asset_throughput" not in sql:
            self.calls.append(" ".join(sql.split())[:400])
            rows = [(r[0], r[1], r[2], r[3], r[4], T._t(T.WINDOW_START_ISO) if r[2] == 1 else r[5], T._t(T.WINDOW_END_ISO) if r[2] == 1 else r[6], r[7], r[8]) for r in ref_db_tuples(OLDB)]
            return type("C", (), {"fetchall": lambda s_: rows})()
        return super().execute(sql, params)


@real_reader
def test_a_baseline_with_no_unclipped_boundary_at_a_level_is_refused_at_ACQUISITION_with_rollback_and_close_and_no_artifact(monkeypatch, tmp_path, capsys):
    spy = AllClippedMD()
    monkeypatch.setattr(T, "open_capture_connection", lambda: spy)
    p = tmp_path / "cap.json"
    assert T.main(["--capture-old", str(p)]) == 3 and not p.exists()                    # named exit 3, nothing written
    err = capsys.readouterr().err
    assert "level MD has NO UNCLIPPED start boundary" in err and "level MD has NO UNCLIPPED end boundary" in err
    assert spy.rolled_back == 1 and spy.closed == 1 and spy.committed == 0              # the lifecycle is preserved on the refusal


def test_coverage_counts_an_UNFLAGGED_level_3_edge_as_clipped_and_needs_only_one_unclipped_start_and_end_per_level():
    rows = clipped_world("old")
    assert T.coverage_problems(rows) == []                                              # writer-shaped: one unclipped start and end remain at every level
    # make every PD start sit on the window bound with the flag False: the instant itself must count as clipped
    pds = [r for r in rows if r["level_n"] == 3]
    for r in pds:
        r["start_iso"] = T.WINDOW_START_ISO
    assert any("level PD has NO UNCLIPPED start" in x for x in T.coverage_problems(rows))
    assert not any("level PD has NO UNCLIPPED end" in x for x in T.coverage_problems(rows))
    assert any("level AD" in x for x in T.coverage_problems([r for r in rows if r["level_n"] != 2]))        # an EMPTY level has no boundary either


def test_the_same_pathological_baseline_is_refused_at_LOAD_and_at_W0_import_without_an_artifact(tmp_path, capsys):
    def clip_md(d):
        for r in d["rows"]:
            if r["level_n"] == 1:
                r["start_iso"], r["end_iso"], r["trunc_start"], r["trunc_end"] = T.WINDOW_START_ISO, T.WINDOW_END_ISO, True, True
    p, chk = _w0_file(tmp_path, clip_md)
    out = tmp_path / "cap.json"
    assert T.main(["--import-w0", str(p), "--w0-checksum", chk, "--w0-capture-out", str(out)]) == 3 and not out.exists()
    assert "level MD has NO UNCLIPPED" in capsys.readouterr().err
    rows = ref_rows("old")
    for r in rows:
        r["trunc_start"] = r["trunc_end"] = False
        if r["level_n"] == 1:
            r["start_iso"], r["end_iso"], r["trunc_start"], r["trunc_end"] = T.WINDOW_START_ISO, T.WINDOW_END_ISO, True, True
    cap = T.build_capture(CHART, OLDB, rows, natal_dicts())
    f = tmp_path / "hand.json"
    import json as _j
    f.write_text(_j.dumps(cap))
    with pytest.raises(ValueError, match="level MD has NO UNCLIPPED"):
        T.load_capture_full(str(f), CHART, OLDB)                                         # a hand-built file with a CORRECT checksum is still refused at load


def test_a_W0_file_in_the_DOCUMENTED_shape_imports(tmp_path, capsys):
    """Only the documented keys; instants with an offset; the database spelling of the flags; level-4 rows present; natal `value` instead of `longitude`; no system / tier / build on the rows."""
    def documented(d):
        keep = ("dasha_row_id", "level_n", "parent_row_id", "lord_graha", "start_iso", "end_iso")
        d["rows"] = [{**{k: r[k] for k in keep}, "is_truncated_at_window_start": False, "is_truncated_at_window_end": False} for r in d["rows"]]
        d["rows"][0]["start_iso"] = d["rows"][0]["start_iso"].replace("Z", "+00:00")                       # an explicit offset is as good as Z
        d["rows"].append({"dasha_row_id": str(_uuid.uuid4()), "level_n": 4, "parent_row_id": d["rows"][-1]["dasha_row_id"], "lord_graha": "Venus",
                          "start_iso": "2013-11-21T04:44:19Z", "end_iso": "2013-11-22T04:44:19Z"})
        d["natal"] = [{"fact_id": n["fact_id"], "fact_subject": n["fact_subject"], "value": n["longitude"], "verification_pass_status": n["tier"], "build_id": n["build_id"]} for n in d["natal"]]
    p, chk = _w0_file(tmp_path, documented)
    out = tmp_path / "cap.json"
    assert T.main(["--import-w0", str(p), "--w0-checksum", chk, "--w0-capture-out", str(out)]) == 0
    text = capsys.readouterr().out
    assert "dropped 1 row(s) at level 4" in text and "filled / aliased" in text and "system_id on 10 row(s)" in text and "natal longitude (from value) on 10 row(s)" in text
    full = T.load_capture_full(str(out), CHART, OLDB)
    assert len(full["rows"]) == 10 and all(r["system_id"] == "vimshottari" and r["verification_pass_status"] == TIER and r["build_id"] == OLDB for r in full["rows"])
    # a PRESENT wrong value is still refused (the fill is only for what is absent)
    def wrong(d):
        documented(d)
        d["rows"][1]["system_id"] = "kalachakra"
    p2, chk2 = _w0_file(tmp_path, wrong)
    assert T.main(["--import-w0", str(p2), "--w0-checksum", chk2, "--w0-capture-out", str(tmp_path / "x.json")]) == 3 and not (tmp_path / "x.json").exists()


def test_an_instant_string_without_an_offset_is_REFUSED_by_name_on_any_machine_timezone(monkeypatch, tmp_path, capsys):
    import time as _time
    old_tz = _os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Asia/Kolkata")
    _time.tzset()
    try:
        assert T._t("2010-08-18T15:50:23Z") == datetime(2010, 8, 18, 15, 50, 23, tzinfo=timezone.utc)
        assert T._t("2010-08-18T21:20:23+05:30") == datetime(2010, 8, 18, 15, 50, 23, tzinfo=timezone.utc)     # an explicit offset is honoured
        with pytest.raises(ValueError, match="instant without an offset"):
            T._t("2010-08-18T15:50:23")                                                                           # NEVER read as machine-local time (IST would give 10:20:23Z)
        assert T._t(datetime(2010, 8, 18, 15, 50, 23)) == datetime(2010, 8, 18, 15, 50, 23, tzinfo=timezone.utc)  # a naive datetime OBJECT is UTC by convention
        def naive(d):
            d["rows"][0]["start_iso"] = "2010-08-18T15:50:23"
        p, chk = _w0_file(tmp_path, naive)
        out = tmp_path / "cap.json"
        assert T.main(["--import-w0", str(p), "--w0-checksum", chk, "--w0-capture-out", str(out)]) == 3 and not out.exists()
        assert "instant without an offset" in capsys.readouterr().err
    finally:
        if old_tz is None:
            _os.environ.pop("TZ", None)
        _time.tzset()


# ── declared post-S-L1 shape (steward ST-REPIN-PARTITION-SHAPE) ─────────────────────────────────────────────────────────────────────────────────────────────

OTHERB = "33333333-3333-4333-8333-333333333333"


def _shape(**over):
    d = {"expected_partitions_non_scope": 47, "expected_partitions_scope_cap": 1, "expected_dasha_build_ids": [NEWB, OTHERB]}
    d.update(over)
    return d


def test_the_notice_may_declare_the_post_s_l1_shape_all_or_none_and_strictly(tmp_path):
    assert T.load_notice(_notice(tmp_path))["_declared_shape"] is None                                             # no declaration ⇒ only the default is ever accepted
    got = T.load_notice(_notice(tmp_path, new_build_id=NEWB, **_shape()))["_declared_shape"]
    assert got == {"non_scope": 47, "scope": 1, "build_ids": sorted([NEWB, OTHERB])}
    bad = [dict(expected_partitions_non_scope=47),                                                                  # partial declarations are refused
           dict(expected_partitions_non_scope=47, expected_partitions_scope_cap=1),
           dict(expected_dasha_build_ids=[NEWB]),
           _shape(expected_partitions_non_scope=-1), _shape(expected_partitions_non_scope=True), _shape(expected_partitions_non_scope=47.0), _shape(expected_partitions_scope_cap="1"),
           _shape(expected_dasha_build_ids=[]), _shape(expected_dasha_build_ids="x"), _shape(expected_dasha_build_ids=[NEWB, "not-a-uuid"]),
           _shape(expected_dasha_build_ids=[NEWB, NEWB]),                                                          # a repeated build id
           _shape(expected_dasha_build_ids=[OTHERB])]                                                              # the SETTLED-1 build must be one of them
    for over in bad:
        with pytest.raises(ValueError, match="notice is invalid"):
            T.load_notice(_notice(tmp_path, new_build_id=NEWB, **over))


def test_the_guard_accepts_the_default_or_exactly_the_declared_shape_and_nothing_else():
    declared = {"non_scope": 47, "scope": 1, "build_ids": sorted([NEWB, OTHERB])}
    # no declaration: unchanged (the default only)
    assert T.preflight_problems(GOODFACTS, NEWB) == []
    assert any("(iii)" in p for p in T.preflight_problems({**GOODFACTS, "non_scope": 47}, NEWB))
    assert any("(ii)" in p for p in T.preflight_problems({**GOODFACTS, "builds": [NEWB, OTHERB]}, NEWB))
    # with a declaration: the declared shape passes ...
    assert T.preflight_problems({**GOODFACTS, "non_scope": 47, "builds": [NEWB, OTHERB]}, NEWB, declared=declared) == []
    assert T.preflight_problems({**GOODFACTS, "non_scope": 47, "builds": [OTHERB, NEWB]}, NEWB, declared=declared) == []        # order is irrelevant
    # ... the default still passes ...
    assert T.preflight_problems(GOODFACTS, NEWB, declared=declared) == []
    # ... and everything that is NEITHER is refused, each condition separately
    assert any("(iii)" in p and "declared 47 + 1" in p for p in T.preflight_problems({**GOODFACTS, "non_scope": 46}, NEWB, declared=declared))
    assert any("(iii)" in p for p in T.preflight_problems({**GOODFACTS, "non_scope": 47, "scope": 0}, NEWB, declared=declared))
    assert any("(ii)" in p and "declared set" in p for p in T.preflight_problems({**GOODFACTS, "builds": [NEWB, OLDB]}, NEWB, declared=declared))   # an UNdeclared extra build

    assert any("(v)" in p for p in T.preflight_problems({**GOODFACTS, "builds": [OTHERB]}, NEWB, declared=declared))                # the declared extra ALONE is one build that is not the SETTLED-1 build
    assert any("(ii)" in p for p in T.preflight_problems({**GOODFACTS, "builds": []}, NEWB, declared=declared))
    for st in ("stale", None):
        bad = {**GOODFACTS, "throughput": {"ga_dashas": st or "lit", "ga_positions": "lit"}} if st else {**GOODFACTS, "throughput": {"ga_positions": "lit"}}
        assert any("(iv)" in p for p in T.preflight_problems({**bad, "non_scope": 47, "builds": [NEWB, OTHERB]}, NEWB, declared=declared))       # (iv) is never relaxed


def test_the_cli_records_the_default_and_the_declared_shape_and_never_relaxes_the_vimshottari_single_build_check(monkeypatch, tmp_path, capsys):
    rows_new = T.norm_rows(ref_rows("new", 6993))
    cap = tmp_path / "old.json"; write_old_cap(cap)
    monkeypatch.setattr(T.DD, "fetch_dasha_periods_multilevel", lambda conn, chart, build_id=None, **kw: rows_new if build_id == NEWB else [])
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117})
    fr = tmp_path / "f.md"; fr.write_text("anchors")
    notice_args = lambda **over: ["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", _notice(tmp_path, new_build_id=NEWB, **over), "--forensic-report", str(fr), "--dry-run"]
    facts47 = {**GOODFACTS, "non_scope": 47, "builds": [NEWB, OTHERB]}
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: facts47)
    # declared + observed == declared ⇒ CLEAN, and the evidence names the default, the declaration and the match
    rc = T.main(notice_args(**_shape()), conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 0 and "verdict: **CLEAN**" in out, out[-900:]
    assert "chart_dashas shape: observed 47 non-scope + 1 scope-cap" in out and "(matches: declared)" in out and "default 45 + 1" in out and f"declared 47 non-scope + 1 scope-cap, builds {sorted([NEWB, OTHERB])}" in out
    # the SAME observation WITHOUT a declaration ⇒ STOP, and the evidence says no shape was declared
    rc = T.main(notice_args(), conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 3 and "(iii)" in out and "no shape declared in the notice" in out and "(matches: NONE)" in out
    # a declaration that the observation does NOT equal ⇒ STOP
    rc = T.main(notice_args(**_shape(expected_partitions_non_scope=48)), conn=FakeConn())
    assert rc == 3 and "declared 48 + 1" in capsys.readouterr().out
    # the Vimśottarī (Lahiri, levels 1–3) single-build check is NEVER relaxed by a declaration: two such builds ⇒ STOP even when the declared shape matches
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117, OTHERB: 117})
    rc = T.main(notice_args(**_shape()), conn=FakeConn())
    assert rc == 3 and "exactly ONE" in capsys.readouterr().out
    # default observation, default behaviour: the recorded evidence says it matched the default
    monkeypatch.setattr(T, "fetch_vimshottari_builds", lambda conn, chart: {NEWB: 117})
    monkeypatch.setattr(T, "fetch_preflight_facts", lambda conn, chart: GOODFACTS)
    rc = T.main(["--new-build-id", NEWB, "--old-rows", str(cap), "--settled-notice", _notice(tmp_path, new_build_id=NEWB), "--forensic-report", str(fr), "--dry-run"], conn=FakeConn())
    out = capsys.readouterr().out
    assert rc == 0 and "(matches: default)" in out and "no shape declared in the notice" in out
