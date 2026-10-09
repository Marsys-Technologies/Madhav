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

@pytest.mark.parametrize("key,kind", [("vocab-canonical-with-caveats", "ceiling"), ("vocab-unread-timeout", "ceiling"), ("vocab-embedded-only", "ceiling"), ("vocab-embedded-only-multi", "ceiling"),
                                       ("vocab-embedded-only-unread", "ceiling"), ("vocab-embedded-only-timeout", "ceiling"), ("dag-parse-incomplete", "ceiling"), ("dag-bedrock", "ceiling"),
                                       ("narr-lint-allowlisted", "ceiling"), ("narr-checkable-upper-bound", "ceiling"), ("dens-no-tier-column", "gap"),
                                       ("null-blank-constant-write", "gap"), ("null-default-constant-write", "gap"),
                                       ("null-unresolved-blank", "gap"), ("null-unresolved-default", "gap"), ("null-unresolved-default-yantra", "gap"), ("dens-attribution", "gap"), ("dens-attr-doshas", "gap"),
                                       ("dens-attr-dignity", "gap"), ("dens-attr-vastu", "gap"), ("dens-attr-transit", "gap"), ("checkable-unknown", "ceiling"), ("checkable-unknown-upaya", "ceiling"),
                                       ("checkable-unknown-grounding", "ceiling"), ("checkable-unknown-vichara", "ceiling")])
def test_the_real_wording_is_a_named_item(key, kind):
    r = named(key)
    assert r and r["kind"] == kind and r["criterion"] == REAL[key]["criterion"] and r["reason"]


@pytest.mark.parametrize("key", [k for k in REAL if k.startswith("not-measurable:")])
def test_the_real_not_measurable_wording_is_a_ceiling(key):
    r = named(key)
    assert r and r["kind"] == "ceiling" and r["reason"].startswith("not measurable: "), r


def test_the_pattern_list_is_closed_and_every_pattern_has_a_real_positive():
    ids = {named(k)["pattern"] for k in REAL if named(k)} | {"empty-by-design:ga_prashna"}          # the empty-by-design pattern needs the asset's cells: tested below
    assert set(cp.NAMED_PATTERN_IDS) == ids | set(cp.NAMED_PATTERN_IDS) and len(cp.NAMED_PATTERN_IDS) == len(set(cp.NAMED_PATTERN_IDS))
    assert set(cp.NAMED_PATTERN_IDS) <= ids, sorted(set(cp.NAMED_PATTERN_IDS) - ids)         # no pattern without a real positive case


def test_a_verdict_that_is_not_the_patterns_verdict_never_matches():
    for key in ("vocab-canonical-with-caveats", "dag-parse-incomplete", "narr-lint-allowlisted", "dens-no-tier-column", "null-blank-constant-write"):
        for v in ("FAIL", "NO_DETECTOR", "PASS", "INCONCLUSIVE"):
            assert blocked(key, lambda t: t + " ", verdict=v) or True
            r = REAL[key]
            assert cp.named_item(r["asset"], r["criterion"], dict(v=v, cause=r["text"], state="MEASURED")) is None, (key, v)
    r = REAL["not-measurable:Dens.served:no-served-select"]
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
    assert named("checkable-unknown")["pattern"] == "narr-checkable-unknown-or-empty"                       # N-276: unknown / empty entries only


def test_FORGED_dens_served_with_another_finding_in_the_same_text_blocks():
    k = "dens-no-tier-column"
    assert blocked(k, lambda t: t + "; platform-mcp/src/tools/x.ts: tier carriage not established (a run-time select list)")
    assert blocked(k, lambda t: t + "; platform-mcp/src/tools/x.ts: its served select of the table is in a different top-level declaration (attribution not established)")
    assert blocked(k, lambda t: t + "; also a served select outside the scanned serving roots (not graded): platform/src/x.ts")
    assert blocked(k, lambda t: t.replace("no tier column in its served select", "a tier column is read but unverified"))
    assert not_named("dens-outside-roots") and not_named("dens-outside-roots-yogas")
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
    ("not-measurable:Ldgr.source_presence:statement-timeout", lambda t: t.replace("neither a PASS nor a FAIL", "a FAIL")),
])
def test_FORGED_not_measurable_shapes_block(key, forge):
    assert blocked(key, forge)


def test_not_measurable_needs_the_a_detector_class_and_no_other_verdict():
    r = REAL["not-measurable:Dens.served:no-served-select"]
    assert cp.named_item("x", "Dens.served", dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED"))
    for v in ("FAIL", "PARTIAL", "INCONCLUSIVE", "PASS"):
        assert cp.named_item("x", "Dens.served", dict(v=v, cause=r["text"], state="MEASURED")) is None
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


# ───────────────────────── N-271 (a): Vocab.alias EMBEDDED-ONLY ─────────────────────────

def test_FORGED_embedded_only_with_a_whole_value_or_another_family_or_finding_blocks():
    k = "vocab-embedded-only"
    assert blocked(k, lambda t: t.replace("; no whole value is a term", "; non-canonical spelling: a.b ('Sunn'); no whole value is a term"))
    assert blocked(k, lambda t: t.replace("no whole value is a term, so the spelling cannot be graded: PARTIAL, never N/A", "every whole value found is canonical"))
    assert blocked(k, lambda t: "vocabulary values found by value in 1 column(s): a.b (graha: Sun); " + t)                   # a whole value exists: the other pattern's territory, and not this shape
    assert blocked(k, lambda t: t + "; MIXED canonical spelling families in one column: a.b (JUP, Jupiter: no single spelling family)")
    assert blocked(k, lambda t: t + "; one short alias only, unverified: a.b (MC)")
    assert blocked(k, lambda t: t.replace("; no whole value is a term, so the spelling cannot be graded: PARTIAL, never N/A", ""))         # no sentinel: the claim 'no whole value' is absent
    assert blocked(k, lambda t: t + "; an unknown remark")
    assert blocked("vocab-embedded-only-multi", lambda t: t + "; unread: chart_facts: the table holds NO rows in the read scope")
    assert blocked("vocab-embedded-only-unread", lambda t: t.replace("leaf cap 5000 reached", "a stray row was found"))
    assert blocked("vocab-embedded-only-timeout", lambda t: t.replace("the existence probe exceeded the statement timeout", "the existence probe found a stray row"))


def test_embedded_only_pattern_does_not_touch_the_canonical_pattern_or_other_criteria():
    r = REAL["vocab-embedded-only"]
    assert cp.m_vocab("x", r["text"]) is None and cp.m_vocab_embedded_only("x", REAL["vocab-canonical-with-caveats"]["text"]) is None
    assert cp.named_item("x", "Null.blank_rows", dict(v="PARTIAL", cause=r["text"], state="MEASURED")) is None
    assert cp.named_item("x", "Vocab.alias", dict(v="FAIL", cause=r["text"], state="MEASURED")) is None


# ───────────────────────── N-271 (b): empty by design, a CLOSED per-asset list, verified from the cells ─────────────────────────

def _prashna_cells(**over):
    cells = {"Build.history": dict(v="PASS", cause=REAL["prashna-history"]["text"], state="MEASURED"),
             "Build.completion": dict(v="PASS", cause=REAL["prashna-completion"]["text"], state="MEASURED")}
    cells.update(over)
    return cells


EMPTY = ("empty:Vocab.alias", "empty:Vocab.identity", "empty:Ldgr.source_presence")


def _empty(aid, key, cells):
    r = REAL[key]
    return cp.named_item(aid, r["criterion"], dict(v=r["verdict"], cause=r["text"], state="MEASURED"), cells)


def test_the_closed_list_is_exactly_ga_prashna_and_names_its_input():
    assert set(cp.EMPTY_BY_DESIGN) == {"ga_prashna"} and cp.EMPTY_BY_DESIGN["ga_prashna"]["input_table"] == "prashna_charts"


@pytest.mark.parametrize("key", EMPTY)
def test_empty_cells_of_ga_prashna_are_named_empty_by_design_when_the_cells_verify_it(key):
    r = _empty("ga_prashna", key, _prashna_cells())
    assert r and r["pattern"] == "empty-by-design:ga_prashna" and r["reason"].startswith("empty by design: prashna questions") and "recorded: none" in r["reason"]


@pytest.mark.parametrize("key", EMPTY)
def test_FORGED_empty_cells_block_without_the_asset_cells_or_for_any_other_asset(key):
    assert _empty("ga_prashna", key, None) is None and _empty("ga_prashna", key, {}) is None            # the census evidence of the asset must be supplied
    assert _empty("bg_sarvatobhadra_grid", key, _prashna_cells()) is None                              # not in the closed list
    assert _empty("some_other_asset", key, _prashna_cells()) is None
    assert cp.named_item("ga_prashna", REAL[key]["criterion"], dict(v="NO_DETECTOR", cause=REAL[key]["text"], state="MEASURED")) is None      # the generic 'empty table = not measurable' route is gone


@pytest.mark.parametrize("mutate", [
    lambda h, c: (dict(h, v="PARTIAL"), c),                                                                                          # no PASS history
    lambda h, c: (dict(h, v="NO_DETECTOR", cause="NO_DETECTOR — nothing has exercised the current code and contract: no attempt since"), c),
    lambda h, c: (dict(h, cause=h["cause"].replace("1 complete, no error or abort", "0 complete, no error or abort")), c),             # no complete attempt in the window
    lambda h, c: (h, dict(c, cause=c["cause"].replace("verified: chart 482012f1 has no row in prashna_charts.chart_id", "verified: chart 482012f1 has 3 row(s) in prashna_charts.chart_id"))),   # the input is NOT empty
    lambda h, c: (h, dict(c, cause=c["cause"].replace("has no row in prashna_charts.chart_id", "has no row in some_other_table.chart_id"))),     # another input
    lambda h, c: (h, dict(c, cause=c["cause"].replace("rows_written=0 = live=0", "rows_written=5 = live=5"))),                      # rows were written
    lambda h, c: (h, dict(c, cause=c["cause"].replace("the declared integrity_check_sql holds", "the declared integrity_check_sql FAILS"))),
    lambda h, c: (h, dict(c, cause=c["cause"].replace("zero rows by declared convention (zero_row_convention, N-149), ", ""))),         # no declared convention
    lambda h, c: (h, dict(c, v="PARTIAL")),
    lambda h, c: (h, None),
])
def test_FORGED_emptiness_not_shown_legitimate_blocks(mutate):
    cells = _prashna_cells()
    h, c = mutate(cells["Build.history"], cells["Build.completion"])
    cells = {"Build.history": h, "Build.completion": c}
    if c is None:
        del cells["Build.completion"]
    for key in EMPTY:
        assert _empty("ga_prashna", key, cells) is None, key


def test_end_to_end_ga_prashna_is_certified_empty_by_design_only_with_its_evidence(tmp_path):
    def build_world(hist, comp):
        crit = ["Build.history", "Build.completion", "Vocab.alias"]
        layers = {"L0": ["a2"], "L1": ["ga_prashna"], "L2": ["c1"]}
        paths = []
        for l, aids in layers.items():
            d = layer_file(l, {a: {n: cell(n, "NO_DETECTOR" if (a == "ga_prashna" and n == "Vocab.alias") else "PASS") for n in crit} for a in aids})
            for h in d[l]["assets"]:
                if h["asset_id"] == "ga_prashna":
                    h["measurements"]["Build.history"]["measured"] = hist
                    h["measurements"]["Build.completion"]["measured"] = comp
                    h["measurements"]["Vocab.alias"]["measured"] = REAL["empty:Vocab.alias"]["text"]
            p = tmp_path / f"census_{l}.json"
            p.write_text(json.dumps(d))
            paths.append(p)
        return paths
    ok = _go(build_world(REAL["prashna-history"]["text"], REAL["prashna-completion"]["text"]), tmp_path / "ok")
    by = {c["asset"]: c for c in ok[2]["certified"]}
    assert "ga_prashna" in by and by["ga_prashna"]["empty_by_design"][0].startswith("certified, empty by design: prashna questions")
    assert "certified, empty by design" in (ok[1] / "CERTIFIED_LIST.md").read_text()
    bad = _go(build_world(REAL["prashna-history"]["text"], REAL["prashna-completion"]["text"].replace("has no row in", "has 4 row(s) in")), tmp_path / "bad")
    assert "ga_prashna" in bad[3]["fix_list"] and "ga_prashna" not in {c["asset"] for c in bad[2]["certified"]}
    strict = _go(build_world(REAL["prashna-history"]["text"], REAL["prashna-completion"]["text"]), tmp_path / "st", "--bar", "strict")
    assert "ga_prashna" in strict[3]["fix_list"]


# ───────────────────────── N-271 (d): every blocker classified ─────────────────────────

@pytest.mark.parametrize("crit,verdict,text,cls", [
    ("Vocab.alias", "FAIL", "non-canonical spelling(s) of a graha term found", cp.GENUINE),
    ("Vocab.alias", "PARTIAL", "x; MIXED canonical spelling families in one column: a.b (JUP, Jupiter: no single spelling family)", cp.GENUINE),
    ("Null.blank_rows", "PARTIAL", "... literal problems: surface_reading bo_x.py:9 (literal_fallback) literal fallback `or`: ''", cp.GENUINE),
    ("Narr.lint", "NO_DETECTOR", "NO_DETECTOR — x declares no prose but its schema contradicts it (open text column(s))", cp.GENUINE),
    ("Narr.lint", "NO_DETECTOR", "NO_DETECTOR — prose_fields is undeclared for x: never read as 'no prose'", cp.MISSING_DECL),
    ("Carr.D1", "NO_DETECTOR", "not measured (applies)", cp.MISSING_DECL),
    ("Ldgr.source_presence", "NO_DETECTOR", "not measured (target-table columns not supplied — applicability undecidable)", cp.MISSING_DECL),
    ("Dens.served", "PARTIAL", "x: tier carriage not established (a run-time select list)", cp.STRUCTURAL),
    ("Narr.checkable", "NO_DETECTOR", "INCONCLUSIVE: no row data was read", cp.STRUCTURAL),
    ("Null.schema_default", "PARTIAL", "writer scan NOT clean - unresolved write path(s): x", cp.STRUCTURAL),
    ("Build.history", "NO_DETECTOR", "NO_DETECTOR — nothing has exercised the current code and contract", cp.STRUCTURAL),
])
def test_blocker_classification_rules(crit, verdict, text, cls):
    assert cp.classify_blocker(crit, verdict, text)[0] == cls


def test_an_unknown_blocker_is_shown_unclassified_never_dropped():
    assert cp.classify_blocker("Weird.criterion", "PARTIAL", "something new")[0] == "UNCLASSIFIED"


def test_end_to_end_blockers_by_class_files_cover_every_fix_list_item(tmp_path):
    paths = _write(tmp_path, {"Narr.lint": "measured text of Narr.lint", "Dens.served": "STRUCTURAL: 1 module(s) reach it by code: x.ts; a referencing capability declares density_contract but x.ts: tier carriage not established"},
                   partial=("Narr.lint", "Dens.served"))
    rc, out, cert, fix = _go(paths, tmp_path)
    b = json.loads((out / "BLOCKERS_BY_CLASS.json").read_text())
    assert (out / "BLOCKERS_BY_CLASS.md").read_text().startswith("# BLOCKERS_BY_CLASS") and b["bar_label"] == LABEL
    assert sum(b["blockers"].values()) == sum(len(v) for v in fix["fix_list"].values()) and set(b["per_asset"]) == set(fix["fix_list"])
    assert b["blockers"]["UNCLASSIFIED"] == 1 and b["blockers"]["STRUCTURAL"] == 1                      # the unknown Narr.lint text stays visible as UNCLASSIFIED
    assert b["assets"] == 1


# ───────────────────────── N-276: four more closed patterns (real census text; forged variants must block) ─────────────────────────

def test_n276_every_new_pattern_has_a_real_positive():
    got = {named(k)["pattern"] for k in REAL if named(k)}
    for pid in ("null-blank-unresolved-write-path", "null-default-unresolved-write-path", "dens-not-attributable", "narr-checkable-unknown-or-empty"):
        assert pid in got, pid
    for c in cp.PROSE_FAMILY:
        r = REAL["budget:" + c]
        i = cp.named_item(r["asset"], c, dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED"))
        assert i and i["pattern"] == f"walk-budget:{c}" and i["reason"].startswith("not measurable: walk budget") and i["kind"] == "ceiling"
    assert set(cp.NAMED_PATTERN_IDS) >= {f"walk-budget:{c}" for c in cp.PROSE_FAMILY}


@pytest.mark.parametrize("key", ["null-unresolved-blank", "null-unresolved-default", "null-unresolved-default-yantra"])
def test_FORGED_null_unresolved_with_a_listed_literal_or_another_finding_blocks(key):
    marker = "writer scan NOT clean - unresolved write path(s): "
    assert blocked(key, lambda t: t.replace(marker, "writer scan NOT clean - literal problems: surface_reading bo_x.py:9 (literal_fallback) literal fallback `or`: ''; ... | unresolved write path(s): "))
    assert blocked(key, lambda t: t.replace(marker, "writer scan NOT clean - literal problems: citation_human bo_x.py:9 (constant_write) the column is written a literal: 'x' | unresolved write path(s): "))
    assert blocked(key, lambda t: t + "; citation_human bo_x.py:7 (placeholder_write) the column is written a placeholder: 'TBD'")
    assert blocked(key, lambda t: t + "; declared curated corpus not applied: 3 scan finding(s) are outside every declared waiver")
    assert blocked(key, lambda t: t + "; an unknown remark without a path")
    assert blocked(key, lambda t: t.replace("and the scan is not clean", "and the scan is clean"))
    assert blocked(key, lambda t: t.replace("writer scan NOT clean", "writer scan found a blank row"))
    assert blocked(key, lambda t: t.replace("(E5.7)", "(E9.9)"))


def test_null_unresolved_truncated_listing_is_allowed_only_without_a_literal_and_a_found_blank_blocks():
    r = REAL["null-unresolved-blank"]
    ok = r["text"] + "; ..."
    assert cp.named_item(r["asset"], r["criterion"], dict(v="PARTIAL", cause=ok, state="MEASURED"))
    assert blocked("null-unresolved-blank", lambda t: t.replace("no blank or placeholder row among the checkable prose rows", "2 blank row(s) among the checkable prose rows"))
    assert blocked("null-unresolved-blank", lambda t: t.replace("no blank or placeholder row among the checkable prose rows", "no blank or placeholder row among the checkable prose rows (unknown for citation_human)"))
    assert not_named("null-remedies")                                      # bg_remedies: literals listed AND unresolved: stays a blocker
    assert not_named("null-literal-fallback") and not_named("null-truncated")


@pytest.mark.parametrize("key", ["dens-attribution", "dens-attr-doshas", "dens-attr-dignity", "dens-attr-vastu", "dens-attr-transit"])
def test_FORGED_dens_attribution_with_any_other_finding_blocks(key):
    assert blocked(key, lambda t: t + "; also a served select outside the scanned serving roots (not graded): platform/src/lib/x.ts")
    assert blocked(key, lambda t: t + "; platform-mcp/src/tools/x.ts: tier carriage not established")                                 # truncated clause = not the known wording
    assert blocked(key, lambda t: t + "; platform-mcp/src/tools/x.ts: a tier column is read but unverified")
    assert blocked(key, lambda t: t + ". uniform_authority declared: PASS WITHHELD (SS N-212 M3)")
    assert blocked(key, lambda t: t.replace("declares density_contract but", "declares nothing but"))
    assert blocked(key, lambda t: t + "; platform/src/x.py: no tier column in its served select")                                       # not a .ts path


def test_dens_real_texts_with_extra_findings_stay_blocked():
    for k in ("dens-outside-roots", "dens-outside-roots-yogas"):
        assert not_named(k)
    r = REAL["dens-attr-vastu"]
    only_k1 = "; ".join(r["text"].split("; ")[:2])                                                                 # a single 'no tier column' item keeps the OLD pattern, not the new one
    got = cp.named_item(r["asset"], r["criterion"], dict(v="PARTIAL", cause=only_k1, state="MEASURED"))
    assert got and got["pattern"] == "dens-no-tier-column"


@pytest.mark.parametrize("key", ["checkable-unknown", "checkable-unknown-upaya", "checkable-unknown-grounding", "checkable-unknown-vichara"])
def test_FORGED_checkable_unknown_with_an_unlisted_or_extra_name_or_finding_blocks(key):
    assert blocked(key, lambda t: t + ", zzz_entry")                                                              # names an entry that is not declared
    assert blocked(key, lambda t: t.rsplit("; none or unknown on", 1)[0])                                    # the unknown entries are not stated
    assert blocked(key, lambda t: t + "; none or unknown on nothing_declared")
    assert blocked(key, lambda t: t + "; a blank row was found")
    assert blocked(key, lambda t: t.replace("checkable rows per declared entry", "checkable rows"))
    assert blocked(key, lambda t: t.replace("; none or unknown on", "; the count is exact; none or unknown on"))


def test_checkable_unknown_names_must_equal_the_empty_entries():
    t = "checkable rows per declared entry: a=5, b=0, c=unknown; none or unknown on b"
    assert cp.m_checkable_unknown("x", t) is None                                                           # c is unknown but unlisted
    assert cp.m_checkable_unknown("x", "checkable rows per declared entry: a=5, b=0; none or unknown on a, b") is None
    assert cp.m_checkable_unknown("x", "checkable rows per declared entry: a=5, b=0, c=unknown; none or unknown on b, c")
    assert cp.m_checkable_unknown("x", "checkable rows per declared entry: a=5, b=3; none or unknown on b") is None


@pytest.mark.parametrize("crit", cp.PROSE_FAMILY)
def test_FORGED_walk_budget_other_reasons_or_other_assets_or_other_criteria_do_not_match(crit):
    r = REAL["budget:" + crit]
    ck = lambda text, v="NO_DETECTOR": dict(v=v, cause=text, state="MEASURED")
    assert cp.named_item("bo_other", crit, ck(r["text"])) is None                                          # the text names bo_drishti: another asset is not covered
    assert cp.named_item(r["asset"], crit, ck(r["text"].replace("unread: budget: the walk of", "unread: statement timeout: the walk of"))) is None
    assert cp.named_item(r["asset"], crit, ck(r["text"].replace("without reaching the end of the table", "after finding a stray row"))) is None
    assert cp.named_item(r["asset"], crit, ck(r["text"] + "; chart_dashas.citation_ref (templated): the bounded read exceeded the statement timeout")) is None
    assert cp.named_item(r["asset"], crit, ck(r["text"], "FAIL")) is None and cp.named_item(r["asset"], crit, ck(r["text"], "PARTIAL")) is None
    assert cp.named_item(r["asset"], "Vocab.alias", ck(r["text"])) is None                                  # not a prose-family criterion
    t = REAL["timeout:Narr.lint"]
    assert cp.named_item(t["asset"], "Narr.lint", ck(t["text"])) is None                                    # ga_dashas: statement timeout is NOT covered


def test_build_history_nd_is_not_named_for_any_asset_n276_item_5_withdrawn():
    r = REAL["history-nd"]
    for aid in ("bo_laksana", "ga_vichara", "bg_gochara_arcs", "other"):
        assert cp.named_item(aid, "Build.history", dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED")) is None


def test_build_history_nd_blocker_reasons_for_the_three_assets():
    t = REAL["history-nd"]["text"]
    for aid in ("bo_laksana", "ga_vichara"):
        assert cp.classify_blocker("Build.history", "NO_DETECTOR", t, aid) == (cp.STRUCTURAL, "excluded from tonight's rebuild (embedding wipe / date-stamped output)")
    assert cp.classify_blocker("Build.history", "NO_DETECTOR", t, "bg_gochara_arcs") == (cp.STRUCTURAL, "owned by Kāla")
    cls, why = cp.classify_blocker("Build.history", "NO_DETECTOR", t, "some_other_asset")
    assert cls == cp.STRUCTURAL and why != "owned by Kāla" and "tonight" not in why                          # the override is per asset, never generic
    assert cp.classify_blocker("Build.history", "NO_DETECTOR", "something else", "bo_laksana")[1] != "excluded from tonight's rebuild (embedding wipe / date-stamped output)"


# ───────────────────────── N-285: constant-write literals must be HONEST ABSENCE STATEMENTS (one quoted literal per item) ─────────────────────────

ABSENT_OK = ["no classical_sources_jsonb citations for this signal", "L1 ayurdaya.maraka_grahas fact not found for this chart/ayanamsha - cannot compute a verdict without it (never guessed).",
             "no sutravali_rules antecedent (full or per-component) matched this firing's constituent_planets/constituent_houses", "value not available", "none recorded", "not recorded for this chart",
             "INR market pricing requires an external source not present in the classical-text corpus"]
PLACEHOLDERS = ["TBD", "N/A", "Unknown", "Default description", "Moderate influence", "see doctrine", "Sun in the 7th: strong", "no data; Mars exalted", "", "   ",
                "casino for sale", "we know for sure", "nobody matched", "not found for this chart; Mars exalted", "no entry for this chart. TBD", "unknown: not found for this chart",
                "CDLM chart summary aggregated from bodha_cdlm_cells by bo_sangati", "Mutual aspect (paraspara drishti): two grahas casting drishti on one another, reinforcing their combined influence"]


@pytest.mark.parametrize("lit", ABSENT_OK)
def test_honest_absence_statements_are_accepted(lit):
    assert cp.honest_absence_problem(lit) is None


@pytest.mark.parametrize("lit", PLACEHOLDERS)
def test_FORGED_placeholders_values_and_vocabulary_terms_are_not_honest_absence(lit):
    assert cp.honest_absence_problem(lit) is not None, lit


def _const_text(items, crit="blank"):
    body = "; ".join(f"{col} {path} (constant_write) the column is written a literal: {lit}" for col, path, lit in items)
    pre = ("no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, "
           "so the writer source is scanned for them (E5.7) and the scan is not clean; writer scan NOT clean - literal problems: ")
    return pre + body


def _named_blank(text):
    return cp.named_item("x", "Null.blank_rows", dict(v="PARTIAL", cause=text, state="MEASURED"))


def test_constant_write_names_each_literal_and_path_line_on_the_reason():
    t = _const_text([("a.$.r", "w/a.py:12", "'no classical_sources_jsonb citations for this signal'"), ("a.$.r", "w/a.py:90", '"x fact not found for this chart (never guessed)."')])
    r = _named_blank(t)
    assert r and r["pattern"] == "null-blank-constant-write"
    assert "honest absence statement: no classical_sources_jsonb citations for this signal (w/a.py:12)" in r["reason"] and "(w/a.py:90)" in r["reason"]
    for k in ("null-blank-constant-write", "null-default-constant-write", "null-const-grounding", "null-const-grounding-default"):
        got = named(k)
        assert got and "honest absence statement:" in got["reason"] and ".py:" in got["reason"], k


def test_FORGED_constant_write_with_a_placeholder_or_value_literal_blocks():
    for lit in PLACEHOLDERS:
        t = _const_text([("a", "w/a.py:1", repr(lit))])
        assert _named_blank(t) is None, lit
    t = _const_text([("a", "w/a.py:1", "'no classical_sources_jsonb citations for this signal'"), ("a", "w/a.py:2", "'Moderate influence'")])
    assert _named_blank(t) is None                                                         # one placeholder among honest ones blocks the cell


def test_FORGED_constant_write_item_must_be_exactly_one_quoted_literal():
    ok = "'no classical_sources_jsonb citations for this signal'"
    for tail in (" or 'TBD'", ".", " + 'x'", " # note", "\n", " extra words", ", 'second'", " if x else 'Unknown'"):
        assert _named_blank(_const_text([("a", "w/a.py:1", ok + tail)])) is None, repr(tail)
    assert _named_blank(_const_text([("a", "w/a.py:1", ok)]))
    assert _named_blank(_const_text([("a", "w/a.py:1", "no classical_sources_jsonb citations for this signal")])) is None      # not quoted
    assert _named_blank(_const_text([("a", "w/a.py:1", "'unterminated")])) is None


def test_real_cdlm_and_motifs_constant_write_no_longer_certify():
    for k in ("null-const-cdlm", "null-const-motifs"):
        assert not_named(k), k                                                                # provenance labels / descriptions that read like content


# the four wording fixes ---------------------------------------------------------------------------------------------------------------------

def test_dens_attr_reason_lists_the_clause_kind_per_file():
    r = named("dens-attr-doshas")
    assert "no tier column in the served select (known absence)" in r["reason"] and "tier carriage not established: run-time select list (static-reading limit)" in r["reason"]
    assert ".ts:" in r["reason"] and r["reason"].startswith("served; per file:")
    r2 = named("dens-attr-dignity")
    assert "attribution not established: select in a different top-level declaration" in r2["reason"] and "different capability entry" in r2["reason"]


def test_checkable_unknown_reason_says_unknown_or_zero():
    r = named("checkable-unknown")
    assert "unknown or zero for domain_verdict_map_jsonb" in r["reason"] and "no rows to check there" not in r["reason"]


def test_walk_budget_reason_says_no_verdict_reached():
    r = REAL["budget:Narr.lint"]
    got = cp.named_item(r["asset"], "Narr.lint", dict(v="NO_DETECTOR", cause=r["text"], state="MEASURED"))
    assert "no verdict reached" in got["reason"] and "no defect found" not in got["reason"]


@pytest.mark.parametrize("key", ["not-measurable:Dens.served:no-served-select", "not-measurable:Dens.served:shared-table"])
def test_FORGED_module_path_lists_are_anchored(key):
    assert named(key)
    r = REAL[key]
    first = r["text"].split("code: ", 1)[1] if "code: " in r["text"] else r["text"].split("module(s): ", 1)[1]
    mod = first.split(",")[0].split(";")[0].split(" ")[0]
    for bad in (mod + ",", mod + ".", mod + "\n", mod + " extra", mod + " , x"):
        assert blocked(key, lambda t, bad=bad: t.replace(mod, bad, 1)), bad


def test_unresolved_reason_counts_listed_paths_and_the_plus_more_note():
    r = named("null-unresolved-blank")                                                       # bo_samskara: one listed path, '+2 more' inside its note
    assert "1 listed write path(s) (+2 more not listed)" in r["reason"]
    r2 = named("null-unresolved-default-yantra")
    assert "1 listed write path(s) (instrument limit)" in r2["reason"] and "more not listed" not in r2["reason"]


def test_a_listed_non_absence_constant_literal_is_a_genuine_blocker():
    for k in ("null-const-cdlm", "null-const-motifs", "null-remedies", "null-truncated"):
        r = REAL[k]
        assert cp.classify_blocker(r["criterion"], r["verdict"], r["text"], r["asset"])[0] == cp.GENUINE, k
    r = REAL["null-unresolved-blank"]
    assert cp.classify_blocker(r["criterion"], r["verdict"], r["text"], r["asset"])[0] == cp.STRUCTURAL              # an unresolved path alone stays an instrument limit


# ───────────────────────── re-review: a literal must be ONE absence clause; transliterations and homoglyphs fail closed ─────────────────────────

REAL_ABSENCE = [
    "no sutravali_rules antecedent (full or per-component) matched this firing's constituent_planets/constituent_houses",
    "no classical_sources_jsonb citations for this signal",
    "INR market pricing requires an external, time-varying market-price source not present in the classical-text corpus this system computes from — B.10 forbids inventing a figure. "
    "See cost_tier for the qualitative (free/low/medium/high) classification, which IS corpus-derived.",
    "L1 ayurdaya.maraka_grahas fact not found for this chart/ayanamsha — cannot compute a maraka verdict without it (never guessed).",
]


@pytest.mark.parametrize("lit", REAL_ABSENCE)
def test_the_four_real_absence_literals_still_pass_the_single_clause_rule(lit):
    assert cp.honest_absence_problem(lit) is None


MIXED = ["The chart is auspicious and strong. Not found for this chart.", "Wealth yoga present; no data for it", "Wealth yoga present. No entry for this chart.",
         "not found for this chart, but auspicious", "not found for this chart, the 7th house is strong", "Strong results; not found for this chart",
         "not found for this chart. Chart is strong", "not found for this chart; Mars exalted", "not found for this chart. See doctrine. Excellent career"]
TRANSLIT = ["Surya fact not found for this chart", "Mangal fact not found for this chart", "Shani value not found for this chart", "Meena entry not found for this chart",
            "Kumbha fact not found", "Guru fact not found for this chart", "Budha fact not found", "Chandra data not found for this chart", "surya fact not found for this chart",
            "SURYA fact not found for this chart", "no mangala data for this chart", "not found for this chart, mangal strong"]
HOMOGLYPH = ["Mаrs fact not found for this chart", "not found for this chart сhart", "fact not found for this chart मंगल", "οne fact not found",
             "fact not found for this chаrt"]


@pytest.mark.parametrize("lit", MIXED)
def test_FORGED_content_mixed_with_an_absence_marker_blocks(lit):
    assert cp.honest_absence_problem(lit) is not None, lit


@pytest.mark.parametrize("lit", TRANSLIT)
def test_FORGED_transliterated_and_alternate_names_block(lit):
    assert cp.honest_absence_problem(lit) is not None, lit


@pytest.mark.parametrize("lit", HOMOGLYPH)
def test_FORGED_homoglyphs_and_non_ascii_letters_block(lit):
    assert "non-ASCII letter" in (cp.honest_absence_problem(lit) or ""), lit


def test_fullwidth_latin_is_nfkc_normalised_before_the_checks():
    assert cp.honest_absence_problem("Ｍａｒｓ fact not found for this chart") is not None            # fullwidth 'Mars' normalises to the vocabulary term and blocks
    assert cp.honest_absence_problem("ｎｏ classical_sources_jsonb citations for this signal") is None        # fullwidth 'no' normalises to a plain absence clause


def test_constant_write_items_with_mixed_or_transliterated_literals_block_end_to_end():
    for lit in MIXED + TRANSLIT + HOMOGLYPH:
        assert _named_blank(_const_text([("a", "w/a.py:1", repr(lit))])) is None, lit
    for lit in REAL_ABSENCE:
        assert _named_blank(_const_text([("a", "w/a.py:1", repr(lit))])), lit
