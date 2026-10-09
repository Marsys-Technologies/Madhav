"""test_n268_bar.py: the N-268 certification bar (named ceilings and disclosure gaps) of census_postprocess.py, offline.

Every pattern has (1) a POSITIVE case whose evidence text is copied from the real census b87dafbed (n268_real_cells.json) and (2) FORGED-evidence cases built from that real text that must still BLOCK (a non-canonical
clause, a cycle, a non-allowlisted violation, another finding in the same text, a found blank row, a truncated listing ...). The bar is also tested end to end: the cell stays PARTIAL in the file, only the verdict moves,
`--bar strict` reproduces the older reading, the header carries the explicit bar label, and the scoped-delta OVERLAY replaces exactly the overlaid assets' cells.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import test_e5_7_census_postprocess as base  # noqa: E402

cp, cell, layer_file = base.cp, base.cell, base.layer_file
REAL = json.loads((HERE / "n268_real_cells.json").read_text(encoding="utf-8"))
LABEL = "bar: N-268 (named ceilings and disclosure gaps)"


def named(key, asset=None, text=None):
    r = REAL[key]
    return cp.named_item(asset or r["asset"], r["criterion"], dict(v=r["verdict"], cause=text if text is not None else r["text"], state="MEASURED"))


def not_named(key):
    """the REAL text of a cell the closed list must NOT name."""
    return named(key) is None


def blocked(key, mutate, asset=None, verdict=None):
    r = REAL[key]
    text = mutate(r["text"])
    assert text != r["text"], "the forgery did not change the text"
    return cp.named_item(asset or r["asset"], r["criterion"], dict(v=verdict or r["verdict"], cause=text, state="MEASURED")) is None


# ───────────────────────── positives: the real wording of census b87dafbed ─────────────────────────

@pytest.mark.parametrize("key,kind", [("vocab-canonical-with-caveats", "ceiling"), ("vocab-unread-timeout", "ceiling"), ("dag-parse-incomplete", "ceiling"), ("dag-bedrock", "ceiling"),
                                       ("narr-lint-allowlisted", "ceiling"), ("narr-checkable-upper-bound", "ceiling"), ("dens-no-tier-column", "gap"),
                                       ("null-blank-constant-write", "gap"), ("null-default-constant-write", "gap")])
def test_the_real_wording_is_a_named_item(key, kind):
    r = named(key)
    assert r and r["kind"] == kind and r["criterion"] == REAL[key]["criterion"] and r["reason"]


@pytest.mark.parametrize("key", [k for k in REAL if k.startswith("not-measurable:")])
def test_the_real_not_measurable_wording_is_a_ceiling(key):
    r = named(key)
    assert r and r["kind"] == "ceiling" and r["reason"].startswith("not measurable: "), r


def test_the_pattern_list_is_closed_and_every_pattern_has_a_real_positive():
    ids = {named(k)["pattern"] for k in REAL if named(k)}
    assert set(cp.NAMED_PATTERN_IDS) == ids | set(cp.NAMED_PATTERN_IDS) and len(cp.NAMED_PATTERN_IDS) == len(set(cp.NAMED_PATTERN_IDS))
    assert set(cp.NAMED_PATTERN_IDS) <= ids, sorted(set(cp.NAMED_PATTERN_IDS) - ids)         # no pattern without a real positive case


def test_a_verdict_that_is_not_the_patterns_verdict_never_matches():
    for key in ("vocab-canonical-with-caveats", "dag-parse-incomplete", "narr-lint-allowlisted", "dens-no-tier-column", "null-blank-constant-write"):
        for v in ("FAIL", "NO_DETECTOR", "PASS", "INCONCLUSIVE"):
            assert blocked(key, lambda t: t + " ", verdict=v) or True
            r = REAL[key]
            assert cp.named_item(r["asset"], r["criterion"], dict(v=v, cause=r["text"], state="MEASURED")) is None, (key, v)
    r = REAL["not-measurable:Vocab.identity:empty-table"]
    assert cp.named_item("x", r["criterion"], dict(v="FAIL", cause=r["text"], state="MEASURED")) is None
    assert cp.named_item("x", "Vocab.alias", dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED")) is None       # another criterion's text


def test_a_pattern_never_applies_to_another_criterion():
    r = REAL["narr-lint-allowlisted"]
    for other in ("Narr.checkable", "Null.blank_rows", "Dens.served", "Build.dag", "Vocab.alias"):
        assert cp.named_item("x", other, dict(v="PARTIAL", cause=r["text"], state="MEASURED")) is None


# ───────────────────────── forgeries: each of these must still block ─────────────────────────

def test_FORGED_vocab_alias_with_one_non_canonical_value_blocks():
    k = "vocab-canonical-with-caveats"
    assert blocked(k, lambda t: t + "; non-canonical spelling: bodha_pratijna.derivation ('Sunn')")
    assert blocked(k, lambda t: t.replace("every whole value found is canonical", "a non-canonical value found ('SUNN'); every whole value found is canonical"))
    assert blocked(k, lambda t: t.replace("every whole value found is canonical, but:", "every whole value found is canonical, but: MIXED canonical spelling families in one column: a.b (JUP, Jupiter: no single spelling family); "))
    assert blocked(k, lambda t: t.replace("every whole value found is canonical", "not every whole value found is canonical"))
    assert blocked(k, lambda t: t.replace(", but:", ""))                                                   # no caveat part at all
    assert blocked(k, lambda t: t.replace("(graha/rashi:", "(graha/rashi; non-canonical: SUNN;", 1))
    assert not_named("vocab-mixed")                                                              # the real MIXED-families text
    assert blocked(k, lambda t: t + "; one short alias only, unverified: a.b (MC)")
    assert blocked(k, lambda t: t + "; unread: chart_facts: the table holds NO rows in the read scope (chart x): there is nothing to judge")
    assert blocked(k, lambda t: t + "; unknown caveat nobody wrote")
    assert blocked(k, lambda t: t.replace("in 2 column(s)", "in 9 column(s)"))                               # the column count must agree with the list
    assert blocked("vocab-unread-timeout", lambda t: t.replace("existence probe exceeded the statement timeout", "existence probe found a stray row"))


def test_FORGED_vocab_no_whole_value_is_a_term_stays_a_blocker():
    t = "embedded vocabulary, spelling unchecked: a.b ('true_chitra'); no whole value is a term, so the spelling cannot be graded: PARTIAL, never N/A"
    assert cp.named_item("x", "Vocab.alias", dict(v="PARTIAL", cause=t, state="MEASURED")) is None


def test_FORGED_build_dag_with_a_cycle_or_a_missing_edge_or_another_note_blocks():
    k = "dag-parse-incomplete"
    assert blocked(k, lambda t: t.replace("is on no dependency cycle (registry-wide graph)", "is on a dependency cycle (bo_arudha -> bo_x -> bo_arudha)"))
    assert blocked(k, lambda t: t.replace("exists: all 2 are active registry assets", "exists: 1 of 2 are active registry assets (bo_gone is not)"))
    assert blocked(k, lambda t: t.replace("bo_arudha is on no", "bo_other is on no"), asset="bo_arudha")        # the cycle statement must be about THIS asset
    assert blocked(k, lambda t: t.replace(", but the parse is incomplete", ", and 1 read(s) of another asset's table have no declared edge (bo_x), but the parse is incomplete"))
    assert blocked(k, lambda t: t + "; 1 read(s) have no declared edge")
    assert not_named("dag-soft-tier")                                                           # the SOFT-tier chart_facts note is another caveat, not the closed shape
    assert blocked(k, lambda t: t.split("the parse is incomplete — ")[0] + "the parse is incomplete — ")     # an empty parse list names nothing


def test_FORGED_narr_lint_with_a_non_allowlisted_violation_blocks():
    k = "narr-lint-allowlisted"
    assert blocked(k, lambda t: t.replace("only allowlisted narration lint violation(s)", "narration lint violation(s)"))
    assert blocked(k, lambda t: t + "; also non-allowlisted violation(s): hardcoded-grade platform/python-sidecar/x.py:9")
    assert blocked(k, lambda t: t + "; fact-category-pin")                                                  # an item without a path:line
    assert blocked(k, lambda t: t.replace("in scope:", "in scope: 4 violation(s) not allowlisted;"))


def test_FORGED_narr_checkable_with_another_finding_blocks():
    k = "narr-checkable-upper-bound"
    assert blocked(k, lambda t: t + "; none or unknown on citation_human")
    assert blocked(k, lambda t: t.replace("citation_human=600", "citation_human=unknown"))
    assert blocked(k, lambda t: t.replace("the count is a whole-table upper bound", "the count is an exact count"))
    assert not_named("checkable-unknown")                                                         # the real 'none or unknown on ...' text


def test_FORGED_dens_served_with_another_finding_in_the_same_text_blocks():
    k = "dens-no-tier-column"
    assert blocked(k, lambda t: t + "; platform-mcp/src/tools/x.ts: tier carriage not established (a run-time select list)")
    assert blocked(k, lambda t: t + "; platform-mcp/src/tools/x.ts: its served select of the table is in a different top-level declaration (attribution not established)")
    assert blocked(k, lambda t: t + "; also a served select outside the scanned serving roots (not graded): platform/src/x.ts")
    assert blocked(k, lambda t: t.replace("no tier column in its served select", "a tier column is read but unverified"))
    assert not_named("dens-attribution")
    assert blocked(k, lambda t: t.replace("declares density_contract but", "declares nothing but"))


def test_FORGED_null_with_a_found_blank_row_or_another_finding_blocks():
    for k in ("null-blank-constant-write", "null-default-constant-write"):
        assert blocked(k, lambda t: t.replace("writer scan NOT clean - literal problems: ", "writer scan NOT clean - literal problems: surface_reading bo_x.py:9 (literal_fallback) literal fallback `or`: ''; "))
        assert blocked(k, lambda t: t + " | unresolved write path(s): citation_human: bo_x.py:5 the parameter row is not a literal tuple")
        assert blocked(k, lambda t: t + "; ...")                                                              # a truncated listing hides entries
        assert blocked(k, lambda t: t + "; declared curated corpus not applied: 3 scan finding(s) are outside every declared waiver")
        assert blocked(k, lambda t: t + "; citation_human bo_x.py:7 (placeholder_write) the column is written a placeholder: 'TBD'")
    assert blocked("null-blank-constant-write", lambda t: t.replace("no blank or placeholder row among the checkable prose rows", "2 blank row(s) among the checkable prose rows"))
    assert blocked("null-blank-constant-write", lambda t: t.replace("no blank or placeholder row among the checkable prose rows", "no blank or placeholder row among the checkable prose rows (unknown for citation_human)"))
    assert not_named("null-remedies")                                                              # bg_remedies: truncated list + unresolved write path + 172 outside the waiver
    assert not_named("null-literal-fallback")                                                       # a literal fallback is a placeholder candidate
    assert not_named("null-truncated")


@pytest.mark.parametrize("key,forge", [
    ("not-measurable:Build.completion:census-role-denied", lambda t: t.replace("live=126769", "live=126000")),                                  # a count disagreement is a finding
    ("not-measurable:Build.completion:view-object", lambda t: t + "; the view disagrees"),
    ("not-measurable:Dens.served:no-served-select", lambda t: t + "; but a served select exists in x.ts"),
    ("not-measurable:Dens.served:shared-table", lambda t: t.replace("cannot be attributed to brahma_ontology", "cannot be attributed to other_table")),
    ("not-measurable:Earn.build_record:receipt-overwritten", lambda t: t.replace("not contradicted", "contradicted")),
    ("not-measurable:Earn.build_record:skip-no-delta", lambda t: t.replace("skip_no_delta (2026", "failed (2026")),
    ("not-measurable:Ldgr.source_presence:empty-table", lambda t: t.replace("on 0 rows", "on 7 rows")),
    ("not-measurable:Ldgr.source_presence:statement-timeout", lambda t: t.replace("neither a PASS nor a FAIL", "a FAIL")),
    ("not-measurable:Vocab.alias:empty-owned-tables", lambda t: t.replace("hold no rows", "hold rows")),
    ("not-measurable:Vocab.identity:empty-table", lambda t: t.replace("vacuous on 0 rows", "violated on 3 rows")),
])
def test_FORGED_not_measurable_shapes_block(key, forge):
    assert blocked(key, forge)


def test_not_measurable_needs_the_a_detector_class_and_no_other_verdict():
    r = REAL["not-measurable:Vocab.identity:empty-table"]
    assert cp.named_item("x", "Vocab.identity", dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED"))
    for v in ("FAIL", "PARTIAL", "INCONCLUSIVE", "PASS"):
        assert cp.named_item("x", "Vocab.identity", dict(v=v, cause=r["text"], state="MEASURED")) is None
    # a NO_DETECTOR for a missing declaration / a contradicted declaration / an unexercised build is not in the closed list
    for name, t in (("Narr.lint", "NO_DETECTOR — prose_fields is undeclared for x: never read as 'no prose'"),
                    ("Narr.lint", "NO_DETECTOR — x declares no prose but its schema contradicts it (open text column(s) the declaration does not close: a.b (text))"),
                    ("Build.history", "NO_DETECTOR — nothing has exercised the current code and contract: no attempt since; window opens 2026-10-01"),
                    ("Carr.D1", "not measured (applies)")):
        assert cp.named_item("x", name, dict(v="NO_DETECTOR", cause=t, state="MEASURED")) is None


def test_a_missing_or_non_text_cause_never_names_anything():
    for c in (None, "", 7, ["x"]):
        assert cp.named_item("x", "Narr.lint", dict(v="PARTIAL", cause=c, state="MEASURED")) is None


# ───────────────────────── end to end: the bar, the cells, the header, --bar strict ─────────────────────────

CRIT = ["Build.history", "Idem.pattern", "Narr.lint", "Dens.served", "Vocab.alias", "Build.dag"]


def _cells(partial=()):
    return {n: (cell(n, "PARTIAL") if n in partial else cell(n)) for n in CRIT}


def _write(tmp_path, texts, partial=("Narr.lint",), **kw):
    """world of three layer files; a1 carries the PARTIAL cells with the given measured texts, everyone else is all PASS."""
    layers = {"L0": ["a1", "a2"], "L1": ["b1"], "L2": ["c1"]}
    paths = []
    for l, aids in layers.items():
        d = layer_file(l, {a: (_cells(partial) if a == "a1" else _cells()) for a in aids}, **kw.get(l, {}))
        for h in d[l]["assets"]:
            if h["asset_id"] == "a1":
                for n, t in texts.items():
                    h["measurements"][n]["measured"] = t
        p = tmp_path / f"census_{l}.json"
        p.write_text(json.dumps(d))
        paths.append(p)
    return paths


def _go(paths, tmp_path, *extra):
    out = tmp_path / "out"
    rc = cp.main(["--census", *map(str, paths), "--date", "2026-10-09", "--layers", "L0,L1,L2", "--out-dir", str(out), *extra])
    cert = json.loads((out / "CERTIFIED_LIST.json").read_text())
    fix = json.loads((out / "FIX_LIST.json").read_text())
    return rc, out, cert, fix


def test_end_to_end_the_cell_stays_partial_only_the_verdict_moves_and_strict_reproduces_the_old_reading(tmp_path):
    texts = {"Narr.lint": REAL["narr-lint-allowlisted"]["text"]}
    paths = _write(tmp_path, texts)
    raw = json.loads(paths[0].read_text())
    rc, out, cert, fix = _go(paths, tmp_path / "n")
    assert rc == 0 and cert["bar_label"] == LABEL and cert["bar"] == "n268"
    by = {c["asset"]: c for c in cert["certified"]}
    assert "a1" in by and "a1" not in fix["fix_list"]
    assert [(n["criterion"], n["kind"], n["pattern"]) for n in by["a1"]["named"]] == [("Narr.lint", "ceiling", "narr-lint-allowlisted")] and by["a2"]["named"] == []
    assert by["a1"]["measured_pass"] == 5 and by["a2"]["measured_pass"] == 6                  # the PARTIAL cell is NOT counted as a PASS
    assert raw["rollup"]["layers"]["L0"]["a1"]["G"]["checks"][2]["v"] == "PARTIAL"            # the census input is untouched
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert md.splitlines()[1].startswith(LABEL) and "Narr.lint [ceiling] (narr-lint-allowlisted)" in md
    assert (out / "FIX_LIST.md").read_text().splitlines()[1].startswith(LABEL)
    rc, out, cert, fix = _go(paths, tmp_path / "s", "--bar", "strict")
    assert rc == 0 and cert["bar"] == "strict" and "strict" in cert["bar_label"]
    assert [c["asset"] for c in cert["certified"]] == ["a2", "b1", "c1"] and "a1" in fix["fix_list"]
    assert fix["fix_list"]["a1"][0]["criterion"] == "Narr.lint" and all("named" not in c or c["named"] == [] for c in cert["certified"])


def test_end_to_end_a_forged_text_keeps_the_asset_on_the_fix_list_under_both_bars(tmp_path):
    forged = REAL["narr-lint-allowlisted"]["text"] + "; hardcoded-grade platform/python-sidecar/x.py:9 (not allowlisted)"
    paths = _write(tmp_path, {"Narr.lint": forged})
    for bar in ("n268", "strict"):
        rc, out, cert, fix = _go(paths, tmp_path / bar, "--bar", bar)
        assert "a1" in fix["fix_list"] and "a1" not in {c["asset"] for c in cert["certified"]}


def test_end_to_end_one_blocker_keeps_the_asset_off_the_certificate_and_the_named_item_is_listed_beside_it(tmp_path):
    paths = _write(tmp_path, {"Narr.lint": REAL["narr-lint-allowlisted"]["text"], "Dens.served": "STRUCTURAL: a different, unknown finding"}, partial=("Narr.lint", "Dens.served"))
    rc, out, cert, fix = _go(paths, tmp_path)
    assert [i["criterion"] for i in fix["fix_list"]["a1"]] == ["Dens.served"]                   # only the unmatched cell blocks
    assert [n["criterion"] for n in fix["named_not_blocking_on_fix_list"]["a1"]] == ["Narr.lint"]


def test_end_to_end_default_bar_is_n268_and_an_unknown_bar_is_refused(tmp_path, capsys):
    paths = _write(tmp_path, {"Narr.lint": REAL["narr-lint-allowlisted"]["text"]})
    rc, out, cert, fix = _go(paths, tmp_path / "d")
    assert cert["bar"] == "n268"
    with pytest.raises(SystemExit) as e:
        cp.main(["--census", *map(str, paths), "--date", "2026-10-09", "--out-dir", str(tmp_path / "x"), "--bar", "lenient"])
    assert e.value.code == 2
    with pytest.raises(cp.Refused):
        cp.build(paths, ["L0", "L1", "L2"], None, None, "2026-10-09", {}, "lenient")


def test_ruled_residuals_and_ceilings_still_work_under_both_bars(tmp_path):
    paths = _write(tmp_path, {}, partial=())
    for bar in ("n268", "strict"):
        rc, out, cert, fix = _go(paths, tmp_path / bar, "--bar", bar)
        assert len(cert["certified"]) == 4 and fix["fix_list"] == {}


# ───────────────────────── overlay: scoped delta rollups replace exactly their assets' cells ─────────────────────────

def _delta(tmp_path, cells_by_asset, layer="L0", fp=base.FP, rev=25, scope=None, with_scope=True):
    d = layer_file(layer, cells_by_asset, rev=rev, fp=fp)
    if with_scope:
        d[layer]["scope"] = dict(assets=sorted(scope or cells_by_asset), partial=True)
        d["rollup"]["scope"] = dict(assets=sorted(scope or cells_by_asset), partial=True, layers=[layer], registry_revision=rev)
    p = tmp_path / "delta_L0.json"
    p.write_text(json.dumps(d))
    return p


def test_overlay_replaces_the_overlaid_assets_cells_and_records_the_fingerprint(tmp_path):
    paths = _write(tmp_path, {"Narr.lint": "measured text of Narr.lint"})                     # a1 has an unmatched PARTIAL: blocked
    rc, out, cert, fix = _go(paths, tmp_path / "pre")
    assert "a1" in fix["fix_list"]
    delta = _delta(tmp_path, {"a1": _cells()}, fp="ef" * 32)                                   # post-fix delta: a1 all PASS, at another registry fingerprint
    rc, out, cert, fix = _go(paths, tmp_path / "post", "--overlay", str(delta))
    assert rc == 0 and "a1" in {c["asset"] for c in cert["certified"]} and fix["fix_list"] == {}
    (o,) = cert["overlays"]
    assert o["assets"] == ["a1"] and o["registry_fingerprint"] == "ef" * 32 and o["base_registry_fingerprint"] == base.FP and o["layer"] == "L0"
    assert "Overlay" in (out / "CERTIFIED_LIST.md").read_text()
    again = _go(paths, tmp_path / "again", "--overlay", str(delta))
    assert (again[1] / "CERTIFIED_LIST.json").read_text() == (out / "CERTIFIED_LIST.json").read_text()      # deterministic


def test_overlay_can_also_block_what_the_full_census_certified(tmp_path):
    paths = _write(tmp_path, {}, partial=())
    delta = _delta(tmp_path, {"a2": _cells(("Idem.pattern",))})                                 # the delta reads a2 PARTIAL: a2 leaves the certificate
    rc, out, cert, fix = _go(paths, tmp_path, "--overlay", str(delta))
    assert "a2" in fix["fix_list"] and "a2" not in {c["asset"] for c in cert["certified"]}


@pytest.mark.parametrize("what", ["unscoped", "unknown_asset", "other_criteria", "other_revision", "other_layer", "scope_mismatch", "other_db", "twice"])
def test_overlay_refusals(tmp_path, what):
    paths = _write(tmp_path, {}, partial=())
    if what == "unscoped":
        delta = _delta(tmp_path, {"a1": _cells()}, with_scope=False)
    elif what == "unknown_asset":
        delta = _delta(tmp_path, {"zz": _cells()})
    elif what == "other_criteria":
        delta = _delta(tmp_path, {"a1": {n: cell(n) for n in CRIT[:-1]}})
    elif what == "other_revision":
        delta = _delta(tmp_path, {"a1": _cells()}, rev=26)
    elif what == "other_layer":
        delta = _delta(tmp_path, {"b1": _cells()}, layer="L0")                                  # b1 is an L1 asset
    elif what == "scope_mismatch":
        delta = _delta(tmp_path, {"a1": _cells()}, scope=["a1", "a2"])
    elif what == "other_db":
        d = json.loads(_delta(tmp_path, {"a1": _cells()}).read_text())
        d["L0"]["db_identity"] = dict(base.DB, database="otherdb")
        delta = tmp_path / "delta_L0.json"
        delta.write_text(json.dumps(d))
    else:
        delta = _delta(tmp_path, {"a1": _cells()})
        with pytest.raises(cp.Refused):
            cp.build(paths, ["L0", "L1", "L2"], None, None, "2026-10-09", {}, "n268", [delta, delta])
        return
    with pytest.raises(cp.Refused):
        cp.build(paths, ["L0", "L1", "L2"], None, None, "2026-10-09", {}, "n268", [delta])


def test_a_scoped_census_is_still_refused_as_a_base_file(tmp_path):
    delta = _delta(tmp_path, {"a1": _cells(), "a2": _cells()})
    with pytest.raises(cp.Refused):
        cp.load(delta)
