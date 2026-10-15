"""test_dens_not_served.py — SS N-211 (E2 / E3 ii / E7) as hardened by the N-212 review (H1, H2, M4, M5): the CHECKED N/A form of Dens.served, `dens_not_served`.

A declaration releases NOTHING by itself (earned-signal rule, CLAUDE.md N.8): the record is checked against the capability scan and the registry.
  none       no served SELECT of the table exists, the scan was clean, and the non-label code occurrences of the asset's tokens ARE the declared `reaches`   -> N/A
  reads      as none, and the served selects are EXACTLY the declared internal reads (same count)                                                          -> N/A
  owned_by   a table two assets share, the sibling owns the same target table AND the same rows, declares nothing itself                                      -> N/A
A contradicting served select reads FAIL (forged / stale), anything the scan cannot attribute reads NO_DETECTOR, an unsound declaration NO_DETECTOR, and a hand-built N/A record
without the verified block is refused by the rollup. The probe tests below put a REAL select of the table into the code in every form the review named: the declared asset must never
read N/A.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_not_served.py -v
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402

tree = dr.tree                                   # the synthetic-source-tree fixture (re-exported for pytest)
EV = "platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:163"       # a real file that names bg_sky_calendar
AID = "bg_sky_calendar"
WHY = "no served capability reads this table: the asset is dormant and its only mention is a description"
NONE = dict(why=WHY, evidence=EV, reaches=[])
CLEAN = dict(scanned=True, outside=[], outside_named=[], unparsed=[], served_at=[], reach_at=[], reach_dynamic=[])


def _rec(entry_dn=None, cap=None, table="t_x", **kw):
    dn = dict(NONE) if entry_dn is None else entry_dn
    kw.setdefault("table_shared", False)
    return ac.dens_not_served_record(AID, dict(dens_not_served=dn), table, dict(CLEAN, **(cap or {})), **kw)


def _rollup(rec):
    return ac.rollup_asset("L0", {"Dens.served": rec})["Dens"]


# ───────────────────────────── none ─────────────────────────────

def test_none_with_a_clean_scan_reads_na_and_the_rollup_releases_it():
    d = _rec()
    assert d["v"] == ac.NA and d["cause"] == "dens-not-served" and d["dens_not_served"]["kind"] == "none" and d["dens_not_served"]["reach_checked"] is True, d
    assert _rollup(d)["v"] == ac.NA


def test_a_comment_only_mention_outside_the_roots_is_the_one_tolerated_shape():
    d = _rec(cap=dict(outside_named=["platform/src/lib/x.ts (a comment names it)"]))
    assert d["v"] == ac.NA, d


def test_mutation_the_same_declaration_reads_fail_once_a_served_select_exists():
    assert _rec()["v"] == ac.NA
    forged = _rec(cap=dict(served_at=[("platform/src/lib/q.ts", 7, 8)], reach_at=[("platform/src/lib/q.ts", 7, "cccccccc")]))
    assert forged["v"] == ac.FAIL and "q.ts" in forged["measured"] and "forged or stale" in forged["measured"], forged
    assert _rollup(forged)["v"] == ac.FAIL


def test_none_on_a_shared_table_is_refused():
    d = _rec(table_shared=True)
    assert d["v"] == ac.NO_DET and "shared" in d["measured"] and "owned_by" in d["measured"], d


# ───────────────────────────── H1 (2): the declared reaches ─────────────────────────────

def test_a_newly_reaching_occurrence_flips_the_cell_to_no_detector():
    declared = dict(NONE, reaches=["platform-mcp/src/lib/a.ts:10#aaaaaaaa"])
    assert _rec(declared, cap=dict(reach_at=[("platform-mcp/src/lib/a.ts", 10, "aaaaaaaa")]))["v"] == ac.NA
    new = _rec(declared, cap=dict(reach_at=[("platform-mcp/src/lib/a.ts", 10, "aaaaaaaa"), ("platform-mcp/src/tools/b.ts", 3, "bbbbbbbb")]))
    assert new["v"] == ac.NO_DET and "not declared" in new["measured"] and "b.ts:3" in new["measured"], new
    gone = _rec(declared, cap=dict(reach_at=[]))
    assert gone["v"] == ac.NO_DET and "declared but gone" in gone["measured"], gone
    moved = _rec(declared, cap=dict(reach_at=[("platform-mcp/src/lib/a.ts", 11, "aaaaaaaa")]))
    assert moved["v"] == ac.NO_DET, moved


def test_a_reaching_module_that_selects_from_a_run_time_table_name_cannot_be_ruled_out():
    declared = dict(NONE, reaches=["platform-mcp/src/lib/a.ts:10#aaaaaaaa"])
    d = _rec(declared, cap=dict(reach_at=[("platform-mcp/src/lib/a.ts", 10, "aaaaaaaa")], reach_dynamic=["platform-mcp/src/lib/a.ts"]))
    assert d["v"] == ac.NO_DET and "run-time table name" in d["measured"], d


def test_reaches_is_required_for_none_and_reads_and_forbidden_for_owned_by():
    bad = ac.dens_not_served_problem(dict(dens_not_served=dict(why=WHY, evidence=EV)), AID)
    assert bad and "reaches is required" in bad, bad
    bad = ac.dens_not_served_problem(dict(dens_not_served=dict(why=WHY, evidence=EV, owned_by="bg_y", reaches=[])), AID)
    assert bad and "belongs to the none / reads forms" in bad, bad
    assert ac.dens_not_served_problem(dict(dens_not_served=dict(why=WHY, evidence=EV, owned_by="bg_y")), AID) is None


# ───────────────────────────── H1 (1)(3)(4)(5): the probes ─────────────────────────────
# A REAL read of the table, put into the code in each form the review named, scanned with the STRICT probe a dens_not_served declaration is checked with. The asset declares `reaches: []`:
# none of these may read N/A.

def _probe(tree, src, *, where="tools", name="p.ts", outside_name=None, outside_src=None, strict=True):
    if src is not None:
        tree.write(getattr(tree, where) if isinstance(where, str) else where, name, src)
    if outside_src is not None:
        out = tree.outside / (outside_name or "o.ts")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(outside_src, encoding="utf-8")
    cap = dr._REAL_SCAN(tree.roots, ["t_x", AID], shared=set(), columns={}, outside_roots=(str(tree.outside),) if outside_src is not None else (),
                        outside_exclude=ac.DENS_STRICT_EXCLUDE if strict else None, table_tokens=["t_x"])
    return cap, _rec(cap=cap)


NOT_NA = "never N/A"


@pytest.mark.parametrize("form,src", [
    ("plain select", "export const t = { run: () => query(`SELECT id FROM t_x WHERE a = $1`) }\n"),
    ("comma join", "export const t = { run: () => query(`SELECT * FROM other o, t_x x WHERE o.id = x.id`) }\n"),
    ("array-joined select", "export const t = { run: () => query(['SELECT id', 'FROM t_x', 'WHERE a = $1'].join(' ')) }\n"),
    ("TABLE shorthand", "export const t = { run: () => query('TABLE t_x') }\n"),
    ("concatenated select", "const T = 't_x'\nexport const t = { run: () => query('SELECT id FROM ' + T) }\n"),
    ("concatenated select with an inline name", "export const t = { run: () => query('SELECT id FROM ' + 't_x' + ' WHERE a = 1') }\n"),
    ("bare table name in a call", "export const t = { run: () => repo.fetchAll('t_x') }\n"),
    ("query-builder .from()", "export const t = { run: () => db.from('t_x').select('id') }\n"),
])
def test_probe_a_real_read_of_the_table_in_the_serving_roots_never_reads_na(tree, form, src):
    cap, d = _probe(tree, src)
    assert d["v"] in (ac.FAIL, ac.NO_DET) and d["v"] != ac.NA, (form, d)
    assert _rollup(d)["v"] != ac.NA, form


@pytest.mark.parametrize("name", ["p.mjs", "p.cjs", "p.js"])
def test_probe_a_select_in_a_javascript_module_is_scanned(tree, name):
    cap, d = _probe(tree, "export const t = { run: () => query(`SELECT id FROM t_x`) }\n", name=name)
    assert cap["served"] == 1 and d["v"] == ac.FAIL, (name, d)


def test_probe_the_test_files_are_still_not_a_served_surface(tree):
    cap, d = _probe(tree, "query(`SELECT id FROM t_x`)\n", name="p.test.mjs")
    assert cap["served"] == 0 and d["v"] == ac.NA, d


def test_probe_a_dynamic_from_behind_an_allowlist_cannot_be_ruled_out(tree):
    src = "const ALLOWED = ['t_x', 'other']\nexport const t = { run: (n) => query(`SELECT id FROM ${n}`) }\n"
    cap, d = _probe(tree, src)
    assert cap["reach_dynamic"] and d["v"] == ac.NO_DET, (cap["reach_dynamic"], d)


def test_probe_a_real_select_in_registry_knowledge_is_seen_by_the_strict_probe_only(tree):
    src = "export const probe = () => query(`SELECT id FROM t_x`)\n"
    cap, d = _probe(tree, None, outside_name="retrieval/registry/knowledge/p.ts", outside_src=src)
    assert cap["outside"] and d["v"] == ac.NO_DET and "outside the scanned serving roots" in d["measured"], (cap, d)
    lax = dr._REAL_SCAN(tree.roots, ["t_x", AID], shared=set(), columns={}, outside_roots=(str(tree.outside),))
    assert lax["outside"] == []                    # the base scan's carve-out hid it: the reason the strict probe exists


def test_probe_an_outside_file_with_a_run_time_from_and_the_token_is_named(tree):
    src = "const T = 't_x'\nexport const f = (n) => query(`SELECT id FROM ${n}`)\n"
    cap, d = _probe(tree, None, outside_name="lib/o.ts", outside_src=src)
    assert any("run-time table name" in x for x in cap["outside_named"]) and d["v"] == ac.NO_DET, (cap, d)


def test_probe_an_outside_file_passing_the_table_name_to_a_call_is_named(tree):
    cap, d = _probe(tree, None, outside_name="lib/o.ts", outside_src="export const f = () => db.from('t_x').select('id')\n")
    assert any("passed to a call" in x for x in cap["outside_named"]) and d["v"] == ac.NO_DET, (cap, d)


def test_probe_a_comment_only_mention_outside_the_roots_stays_na(tree):
    cap, d = _probe(tree, None, outside_name="lib/o.ts", outside_src="// t_x is read by the sidecar, not here\nexport const f = 1\n")
    assert d["v"] == ac.NA, (cap, d)


# ───────────────────────────── reads ─────────────────────────────

P = "platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts"
READS = dict(why="the only served select is an internal lookup used inside another computation", evidence=EV, reads=[f"{P}:10"], reaches=[f"{P}:10#eeeeeeee"])


def test_the_matcher_accepts_exact_reads_and_fails_every_other_set():
    ok = _rec(READS, cap=dict(served_at=[(P, 9, 12)], reach_at=[(P, 10, "eeeeeeee")]))
    assert ok["v"] == ac.NA and ok["dens_not_served"]["n_served"] == 1 and _rollup(ok)["v"] == ac.NA, ok
    extra = _rec(READS, cap=dict(served_at=[(P, 9, 12), (P, 40, 41)], reach_at=[(P, 10, "eeeeeeee"), (P, 40, "ffffffff")]))
    assert extra["v"] == ac.FAIL and "not declared" in extra["measured"], extra
    gone = _rec(READS, cap=dict(served_at=[], reach_at=[]))
    assert gone["v"] == ac.FAIL and "not served selects" in gone["measured"], gone
    moved = _rec(READS, cap=dict(served_at=[(P, 20, 22)], reach_at=[(P, 10, "eeeeeeee")]))
    assert moved["v"] == ac.FAIL, moved
    other = _rec(READS, cap=dict(served_at=[("platform/src/other.ts", 9, 12)], reach_at=[(P, 10, "eeeeeeee")]))
    assert other["v"] == ac.FAIL, other


def test_m5_two_served_selects_in_the_range_of_one_declared_read_fail():
    """Both selects lie inside the declared read's line range, so neither is 'undeclared': the COUNT differs (2 found, 1 declared)."""
    d = _rec(READS, cap=dict(served_at=[(P, 8, 12), (P, 9, 13)], reach_at=[(P, 10, "eeeeeeee")]))
    assert d["v"] == ac.FAIL and "2 served select(s) were found for 1 declared" in d["measured"], d


def test_reads_with_a_new_reaching_occurrence_elsewhere_reads_no_detector():
    d = _rec(READS, cap=dict(served_at=[(P, 9, 12)], reach_at=[(P, 10, "eeeeeeee"), ("platform-mcp/src/tools/z.ts", 5, "dddddddd")]))
    assert d["v"] == ac.NO_DET and "z.ts:5" in d["measured"], d


# ───────────────────────────── owned_by (H2) ─────────────────────────────

def _own(owner="bg_y", why="the table is shared and the sibling asset owns its Dens cell"):
    return dict(why=why, evidence=EV, owned_by=owner)


def _owned(entry=None, **kw):
    kw = dict(dict(table_shared=True, owner_row=dict(target_table="t_x"), count_sql="SELECT count(*) FROM t_x", owner_count_sql="SELECT count(*) FROM t_x"), **kw)
    return ac.dens_not_served_record(AID, dict(dens_not_served=entry or _own()), "t_x", dict(CLEAN), **kw)


def test_owned_by_a_sibling_with_the_same_rows_reads_na():
    d = _owned()
    assert d["v"] == ac.NA and d["cause"] == "dens-owned-by-sibling" and d["dens_not_served"]["same_rows"] is True, d
    assert _rollup(d)["v"] == ac.NA


def test_h2_different_row_predicates_are_refused():
    d = _owned(owner_count_sql="SELECT count(*) FROM t_x WHERE fact_kind = 'lifetime_count'")
    assert d["v"] == ac.NO_DET and "fewer rows" in d["measured"], d
    d = _owned(count_sql="SELECT count(*) FROM t_x WHERE fact_kind <> 'lifetime_count'", owner_count_sql="SELECT count(*) FROM t_x WHERE fact_kind = 'lifetime_count'")
    assert d["v"] == ac.NO_DET and "fewer rows" in d["measured"], d
    assert _rollup(d)["v"] != ac.NA


def test_review2_the_owner_must_cover_the_sibling_rows_exactly_not_a_count_of_populated_rows():
    """Finding 4 (and 5): `IS NULL` is not `IS NOT NULL`, `a IS NOT NULL` is not `b IS NOT NULL`, the FROM / JOIN clause is compared, and the OWNER's predicates must be a SUBSET of the
    sibling's. bg_text_index (embedding / topic_tag IS NOT NULL) therefore does NOT cover bg_texts (all rows): the pair is refused, no special case."""
    idx = "SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL"
    allr = "SELECT count(*) FROM classical_text_chunks"
    assert ac.count_sql_same_rows(allr, allr) is None
    assert ac.count_sql_same_rows(idx, idx) is None
    assert ac.count_sql_same_rows(allr, idx) is None                                    # an owner that reads ALL rows covers the sibling's tagged subset
    bad = ac.count_sql_same_rows(idx, allr)                                              # an owner that reads the tagged subset does not cover all rows
    assert bad and "fewer rows" in bad, bad
    assert ac.count_sql_same_rows("SELECT 1 FROM t WHERE a IS NULL", "SELECT 1 FROM t WHERE a IS NOT NULL")
    assert ac.count_sql_same_rows("SELECT 1 FROM t WHERE a IS NOT NULL", "SELECT 1 FROM t WHERE b IS NOT NULL")
    assert ac.count_sql_same_rows("SELECT 1 FROM t JOIN u ON u.id = t.id", "SELECT 1 FROM t")
    d = _owned(count_sql=allr, owner_count_sql=idx)
    assert d["v"] == ac.NO_DET and "fewer rows" in d["measured"], d


def test_h2_an_unavailable_count_sql_cannot_be_compared():
    d = _owned(count_sql=None)
    assert d["v"] == ac.NO_DET and "cannot be compared" in d["measured"], d


@pytest.mark.parametrize("kw,frag", [
    (dict(owner_row=None), "not an active asset"),
    (dict(owner_row=dict(target_table="t_other")), "owns"),
    (dict(table_shared=False), "is not shared"),
    (dict(owner_entry=dict(dens_not_served=dict(NONE))), "no chain"),
])
def test_owned_by_refusals(kw, frag):
    d = _owned(**kw)
    assert d["v"] == ac.NO_DET and frag in d["measured"], d


@pytest.mark.parametrize("mut", [lambda b: b.update(owner_table="other"), lambda b: b.update(owner_declares_na=True), lambda b: b.update(table_shared=False),
                                 lambda b: b.update(owned_by=""), lambda b: b.update(same_rows=False)])
def test_an_owner_block_must_carry_the_sibling_facts(mut):
    bad = copy.deepcopy(_owned())
    mut(bad["dens_not_served"])
    assert _rollup(bad)["v"] == ac.NO_DET


# ───────────────────────────── M4: services ─────────────────────────────

def test_m4_an_asset_with_no_table_must_be_a_declared_service():
    d = ac.dens_not_served_record(AID, dict(dens_not_served=dict(NONE)), None, dict(CLEAN), table_shared=False, asset_kind="data")
    assert d["v"] == ac.NO_DET and "declared service" in d["measured"], d
    d = ac.dens_not_served_record(AID, dict(dens_not_served=dict(NONE)), None, dict(CLEAN), table_shared=False, asset_kind="service")
    assert d["v"] == ac.NO_DET and "declared service" in d["measured"], d               # a service without a declared service_probe
    ok = ac.dens_not_served_record(AID, dict(dens_not_served=dict(NONE), service_probe=dict(probe_type="x")), None, dict(CLEAN), table_shared=False, asset_kind="service")
    assert ok["v"] == ac.NA, ok


# ───────────────────────────── soundness and the rollup ─────────────────────────────

@pytest.mark.parametrize("mut,frag", [
    (lambda d: d.update(evidence="unverified: i looked at it"), "unverified"),
    (lambda d: d.update(evidence="platform/scripts/governance/asset_census.py:1"), "mentions neither"),
    (lambda d: d.update(evidence="platform/nope/missing.ts:3"), "existing repo-relative file"),
    (lambda d: d.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py"), "must name a line"),
    (lambda d: d.update(why="tbd"), "why"),
    (lambda d: d.update(owned_by="bg_y", reads=["platform/src/a.ts:1"]), "one form only"),
    (lambda d: d.update(reads=[]), "reads must be"),
    (lambda d: d.update(owned_by=AID, reaches=None) or d.pop("reaches"), "names the asset itself"),
    (lambda d: d.update(extra="x"), "unknown field"),
    (lambda d: d.update(reaches=["not a path"]), "reaches is required"),
])
def test_an_unsound_declaration_is_refused_by_the_validator_and_reads_no_detector(mut, frag):
    d = dict(NONE)
    mut(d)
    bad = ac.dens_not_served_problem(dict(dens_not_served=d), AID)
    assert bad and frag in bad, bad
    with pytest.raises(ac.DeclarationsError):
        ac.validate_dens_not_served_declaration("assets['x']", dict(dens_not_served=d), AID)
    rec = ac.dens_not_served_record(AID, dict(dens_not_served=d), "t_x", dict(CLEAN), table_shared=False)
    assert rec["v"] == ac.NO_DET and "refused" in rec["measured"], rec


def test_an_undeclared_asset_is_untouched():
    assert ac.dens_not_served_record(AID, dict(kind="data"), "t_x", dict(scanned=True), table_shared=False) is None
    assert ac.dens_not_served_problem(dict(kind="data"), AID) is None


def test_a_hand_built_na_without_the_verified_block_is_not_honoured_by_the_rollup():
    assert _rollup(ac._na("declared, trust me", "dens-not-served"))["v"] == ac.NO_DET
    assert _rollup(ac._na("declared, trust me", "dens-owned-by-sibling"))["v"] == ac.NO_DET


@pytest.mark.parametrize("mut", [
    lambda b: b.update(checked=False),
    lambda b: b.update(outside=["platform/src/x.ts"]),
    lambda b: b.update(unparsed=["platform/src/x.ts"]),
    lambda b: b.update(outside_named=["platform/src/x.ts (holds the table and selects FROM a run-time table name)"]),
    lambda b: b.update(reach_checked=False),
    lambda b: b.pop("reaches"),
    lambda b: b.update(served_selects=["platform/src/x.ts:3"]),                      # kind none but a served select recorded
    lambda b: b.update(kind="reads"),                                                 # reads with no declared reads
])
def test_a_block_that_contradicts_its_own_claim_is_not_honoured(mut):
    good = _rec()
    assert _rollup(good)["v"] == ac.NA
    bad = copy.deepcopy(good)
    mut(bad["dens_not_served"])
    assert _rollup(bad)["v"] == ac.NO_DET


def test_a_reads_block_must_balance_served_selects_against_declared_reads():
    good = _rec(READS, cap=dict(served_at=[(P, 9, 12)], reach_at=[(P, 10, "eeeeeeee")]))
    assert _rollup(good)["v"] == ac.NA
    for k, v in (("n_served", 2), ("unmatched_served", ["x:1"]), ("unmatched_declared", ["y:2"]), ("served_selects", [])):
        bad = copy.deepcopy(good)
        bad["dens_not_served"][k] = v
        assert _rollup(bad)["v"] == ac.NO_DET, k
