"""test_dens_not_served.py — SS N-211 (E2 / E3 ii / E7): the CHECKED N/A form of Dens.served, `dens_not_served`.

A declaration releases NOTHING by itself (earned-signal rule, CLAUDE.md N.8): measure() checks it against the capability scan and the registry.
  none       no served SELECT of the table exists (scan clean)                      -> N/A (cause dens-not-served)
  reads      the served selects are EXACTLY the declared internal reads             -> N/A (cause dens-not-served)
  owned_by   a table two assets share; the sibling owns it and declares nothing      -> N/A (cause dens-owned-by-sibling)
A served select that contradicts `none` / `reads` reads FAIL (a forged or stale declaration), an unsound declaration or one the scan cannot check reads NO_DETECTOR,
and a hand-built N/A record without the verified block is not honoured by the rollup. Mutation tests: the same declaration flips to FAIL when a served select is added.

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
import test_w2_1_earned_verdicts as w1  # noqa: E402

tree = dr.tree                                   # the synthetic-source-tree fixture (re-exported for pytest)
EV = "platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:163"       # a real file that names bg_sky_calendar
AID = "bg_sky_calendar"
WHY = "no served capability reads this table: the asset is dormant and its only mention is a description"
NONE = dict(why=WHY, evidence=EV)
SELECT_SRC = "export const cap = {\n  id: 'bg_sky_calendar',\n  run: async () => query(`SELECT id FROM t_x WHERE a = $1`),\n}\n"
LABEL_SRC = "export const note = {\n  provenance: { tables: ['t_x'] },\n}\n"


def _measure(monkeypatch, tree, src, dns, *, extra_reg=None, extra_decls=None, reg_table="t_x", outside_src=None):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    if outside_src is not None:
        tree.write("outside", "o.ts", outside_src)
    decls = {AID: dict(kind="data", **({"dens_not_served": dns} if dns is not None else {}))}
    decls.update(extra_decls or {})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: copy.deepcopy(decls))
    reg = {AID: w1._reg_row(AID, reg_table)}
    reg.update(extra_reg or {})
    c = dr._measure(monkeypatch, tree, reg, {"t_x": (["id", "a"], [])}, outside=outside_src is not None)
    return c


def _cell(c, aid=AID):
    return dr._dens(c, aid)


def _rollup(rec):
    return ac.rollup_asset("L0", {"Dens.served": rec})["Dens"]


# ───────────────────────────── none ─────────────────────────────

def test_none_with_no_served_select_reads_na_and_the_rollup_releases_it(tree, monkeypatch):
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, dict(NONE)))
    assert d["v"] == ac.NA and d["cause"] == "dens-not-served" and d["dens_not_served"]["kind"] == "none", d
    assert _rollup(d)["v"] == ac.NA


def test_mutation_the_same_declaration_reads_fail_once_a_served_select_exists(tree, monkeypatch):
    """The earned-signal test: the declaration is identical; only the code changed."""
    ok = _cell(_measure(monkeypatch, tree, LABEL_SRC, dict(NONE)))
    forged = _cell(_measure(monkeypatch, tree, SELECT_SRC, dict(NONE)))
    assert ok["v"] == ac.NA and forged["v"] == ac.FAIL, (ok, forged)
    assert "q.ts" in forged["measured"] and "forged or stale" in forged["measured"], forged
    assert _rollup(forged)["v"] == ac.FAIL


def test_none_on_a_shared_table_is_refused(tree, monkeypatch):
    other = {"bg_y": w1._reg_row("bg_y", "t_x")}
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, dict(NONE), extra_reg=other))
    assert d["v"] == ac.NO_DET and "shared" in d["measured"] and "owned_by" in d["measured"], d


def test_a_served_select_outside_the_serving_roots_cannot_be_checked(tree, monkeypatch):
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, dict(NONE), outside_src="export const o = () => query(`SELECT id FROM t_x`)\n"))
    assert d["v"] == ac.NO_DET and "outside the scanned serving roots" in d["measured"], d


# ───────────────────────────── reads ─────────────────────────────

def test_the_matcher_accepts_exact_reads_and_fails_every_other_set():
    base = dict(scanned=True, outside=[], unparsed=[])
    p = "platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts"     # a real, existing file (evidence is not read here)
    entry = dict(dens_not_served=dict(why="the only served select is an internal lookup used inside another computation", evidence=EV, reads=[f"{p}:10"]))
    ok = ac.dens_not_served_record(AID, entry, "t_x", dict(base, served_at=[(p, 9, 12)]), table_shared=False)
    assert ok["v"] == ac.NA and ok["dens_not_served"]["n_served"] == 1 and _rollup(ok)["v"] == ac.NA, ok
    extra = ac.dens_not_served_record(AID, entry, "t_x", dict(base, served_at=[(p, 9, 12), (p, 40, 41)]), table_shared=False)
    assert extra["v"] == ac.FAIL and "not declared" in extra["measured"], extra
    gone = ac.dens_not_served_record(AID, entry, "t_x", dict(base, served_at=[]), table_shared=False)
    assert gone["v"] == ac.FAIL and "not served selects" in gone["measured"], gone
    moved = ac.dens_not_served_record(AID, entry, "t_x", dict(base, served_at=[(p, 20, 22)]), table_shared=False)
    assert moved["v"] == ac.FAIL, moved                       # the declared line is no longer inside the select
    other = ac.dens_not_served_record(AID, entry, "t_x", dict(base, served_at=[("platform/src/other.ts", 9, 12)]), table_shared=False)
    assert other["v"] == ac.FAIL, other


# ───────────────────────────── owned_by ─────────────────────────────

def _own(owner="bg_y", why="the table is shared and the sibling asset owns its Dens cell"):
    return dict(why=why, evidence=EV, owned_by=owner)


def test_owned_by_a_sibling_that_owns_the_same_shared_table_reads_na(tree, monkeypatch):
    sib = {"bg_y": w1._reg_row("bg_y", "t_x")}
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, _own(), extra_reg=sib))
    assert d["v"] == ac.NA and d["cause"] == "dens-owned-by-sibling" and d["dens_not_served"]["owned_by"] == "bg_y", d
    assert _rollup(d)["v"] == ac.NA


@pytest.mark.parametrize("reg,decls,frag", [
    ({}, None, "not an active asset"),                                                          # the owner does not exist
    ({"bg_y": w1._reg_row("bg_y", "t_other")}, None, "is not shared"),                          # the table is not shared
])
def test_owned_by_refusals(tree, monkeypatch, reg, decls, frag):
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, _own(), extra_reg=reg, extra_decls=decls))
    assert d["v"] == ac.NO_DET and frag in d["measured"], d


def test_owned_by_an_owner_that_itself_declares_dens_not_served_is_refused(tree, monkeypatch):
    sib = {"bg_y": w1._reg_row("bg_y", "t_x")}
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, _own(), extra_reg=sib, extra_decls={"bg_y": dict(kind="data", dens_not_served=dict(NONE, evidence=EV))}))
    assert d["v"] == ac.NO_DET and "no chain" in d["measured"], d


def test_owned_by_a_sibling_with_a_different_target_table_is_refused(tree, monkeypatch):
    sib = {"bg_y": w1._reg_row("bg_y", "t_y")}
    d = _cell(_measure(monkeypatch, tree, LABEL_SRC, _own(), extra_reg=sib))
    assert d["v"] == ac.NO_DET, d


# ───────────────────────────── soundness and the rollup ─────────────────────────────

@pytest.mark.parametrize("mut,frag", [
    (lambda d: d.update(evidence="unverified: i looked at it"), "unverified"),
    (lambda d: d.update(evidence="platform/scripts/governance/asset_census.py:1"), "mentions neither"),
    (lambda d: d.update(evidence="platform/nope/missing.ts:3"), "existing repo-relative file"),
    (lambda d: d.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py"), "must name a line"),
    (lambda d: d.update(why="tbd"), "why"),
    (lambda d: d.update(owned_by="bg_y", reads=["platform/src/a.ts:1"]), "one form only"),
    (lambda d: d.update(reads=[]), "reads must be"),
    (lambda d: d.update(owned_by=AID), "names the asset itself"),
    (lambda d: d.update(extra="x"), "unknown field"),
])
def test_an_unsound_declaration_is_refused_by_the_validator_and_reads_no_detector(tree, monkeypatch, mut, frag):
    d = dict(NONE)
    mut(d)
    bad = ac.dens_not_served_problem(dict(dens_not_served=d), AID)
    assert bad and frag in bad, bad
    with pytest.raises(ac.DeclarationsError):
        ac.validate_dens_not_served_declaration("assets['x']", dict(dens_not_served=d), AID)
    rec = ac.dens_not_served_record(AID, dict(dens_not_served=d), "t_x", dict(scanned=True, outside=[], unparsed=[], served_at=[]), table_shared=False)
    assert rec["v"] == ac.NO_DET and "refused" in rec["measured"], rec


def test_an_undeclared_asset_is_untouched():
    assert ac.dens_not_served_record(AID, dict(kind="data"), "t_x", dict(scanned=True), table_shared=False) is None
    assert ac.dens_not_served_problem(dict(kind="data"), AID) is None


def test_a_hand_built_na_without_the_verified_block_is_not_honoured_by_the_rollup():
    forged = ac._na("declared, trust me", "dens-not-served")
    assert _rollup(forged)["v"] == ac.NO_DET
    owner = ac._na("declared, trust me", "dens-owned-by-sibling")
    assert _rollup(owner)["v"] == ac.NO_DET


@pytest.mark.parametrize("mut", [
    lambda b: b.update(checked=False),
    lambda b: b.update(outside=["platform/src/x.ts"]),
    lambda b: b.update(unparsed=["platform/src/x.ts"]),
    lambda b: b.update(served_selects=["platform/src/x.ts:3"]),                      # kind none but a served select recorded
    lambda b: b.update(kind="reads"),                                                 # reads with no declared reads
])
def test_a_block_that_contradicts_its_own_claim_is_not_honoured(tree, monkeypatch, mut):
    good = _cell(_measure(monkeypatch, tree, LABEL_SRC, dict(NONE)))
    assert _rollup(good)["v"] == ac.NA
    bad = copy.deepcopy(good)
    mut(bad["dens_not_served"])
    assert _rollup(bad)["v"] == ac.NO_DET


def test_an_owner_block_must_carry_the_sibling_facts(tree, monkeypatch):
    sib = {"bg_y": w1._reg_row("bg_y", "t_x")}
    good = _cell(_measure(monkeypatch, tree, LABEL_SRC, _own(), extra_reg=sib))
    for k, v in (("owner_table", "other"), ("owner_declares_na", True), ("table_shared", False), ("owned_by", "")):
        bad = copy.deepcopy(good)
        bad["dens_not_served"][k] = v
        assert _rollup(bad)["v"] == ac.NO_DET, k


def test_a_measured_na_is_not_overridden_by_the_declaration(tree, monkeypatch):
    """No reference anywhere reads N/A (no-served-surface) already; the declaration changes nothing."""
    d = _cell(_measure(monkeypatch, tree, "export const unrelated = 1\n", dict(NONE)))
    assert d["v"] == ac.NA and d["cause"] == "no-served-surface", d
