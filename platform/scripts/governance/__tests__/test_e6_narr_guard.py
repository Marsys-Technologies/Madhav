"""test_e6_narr_guard.py: NARR-GUARD (REGISTRY_REVISION 16, declarations 1.12.0; strategist ruling N-94).

The ruling: bg_phaladeepika_latta declares `prose_fields: []` under the established rule R03 (Narr measures GENERATED prose; the latta generates none: its effect and affliction strings are
hand-normalised restatements of passage clauses). The claim a Narr check would measure (each stored string faithfully restates its passage clause) already has a real detector, Carr.D1.
So the N/A stays COUPLED to D1: a new optional per-asset declaration `prose_coupling: {to: 'carriage_d1', columns, why, evidence}` that

  * the validator refuses unless prose_fields is exactly [], the asset declares a transcription carriage that applies D1 with a spec, the why cites carriage transcription and Carr.D1, the
    evidence is a real repo file:line, and EVERY listed column is covered by the D1 spec (the covered set is derived from the spec, never trusted from the declaration);
  * the measure-time glue re-checks with the table's columns and types (refusal = the four Narr checks NO_DETECTOR, the disagreement reported);
  * the rollup honours only while the asset's own Carr.D1 EFFECTIVE contribution reads PASS and the D1 record shows a per-row result for every coupled column (else Narr NO_DETECTOR 'Narr N/A
    rests on Carr.D1 PASS (coupled): Carr.D1 reads X'); the gap ledger, the certificate writer (test_e6_narr_guard_writer.py) and the E6.3 reader (here, Part 6) read the same function.

Part 1 the committed entry and the validator. Part 2 the measure-time glue (offline). Part 3 the rollup guard (offline, real D1 records on the committed fixture). Part 4 REAL detectors on a
disposable Postgres: PASS, every mutation, and the cell diff across ALL 40 L0 assets of the saved census. Part 5 nothing moves for an asset that does not declare it (six saved censuses).
Part 6 the E6.3 reader. Part 7 the pin."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import carriage_d1 as d1  # noqa: E402
import test_e6_decl_latta as dl  # noqa: E402
import test_e6_decl_latta_null as ln  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_e6_s1_elevation_reader as rd  # noqa: E402
from test_e6_s1_elevation_reader import real_registry  # noqa: E402,F401  (its autouse fixture: the reader tests' real registry)
from _e6_3_fixtures import RUN_ID, World, cert, disp, sha  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

AID = dl.AID
PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
DECL, ENTRY, CAR, SPEC, ROWS, CHUNKS = dl.DECL, dl.ENTRY, dl.CAR, dl.SPEC, dl.ROWS, dl.CHUNKS
PC = ENTRY["prose_coupling"]
COLS, TYPES, CAT, R = dl.COLS, ln.TYPES, ln.CAT, ln.R
NARR = list(ac.NARR_CHECKS)
SAVED = dl.SAVED
FACTS = {"declared_prose_coupling": {"to": PC["to"], "columns": list(PC["columns"]), "covered": {"effect_description": "effect", "affliction_condition": "affliction_condition"}}}
FILES = ["bg_phaladeepika_vedha.py"]
BATCH2_EMPTY = ["bg_transit_engine", "bg_kp_sublord_division"]      # L0-WAVE batch 2: [] with no carriage, so no coupling
EXISTING_EMPTY = ["bg_doshas", "bg_ontology", "bg_yogas", "bo_laksana_rerank"]    # the four assets that declared prose_fields [] before this lane
CONVERTED = ["bg_doshas", "bg_ontology", "bg_yogas", "bo_laksana_rerank"]      # E5.7 fills + final: converted to a checked prose_none (no grandfather table remains), so a saved unchecked N/A no longer releases their Narr cell
ROOT = ac.ROOT
RESIDUAL_PROSE_NONE = ["bg_class_lifetime_counts", "bg_class_priors", "bg_formula_constants", "bg_ghatana", "bg_gochara_citation_resolution", "bg_kota_chakra_rings", "bg_medical_mappings", "bg_nakshatra_medical", "bg_parihara_rules", "bg_prashna_rules", "bg_sign_medical", "bg_texts", "bg_vidhi_floors", "bg_vidhi_primitives"]      # residual declaration batch (POST-#3176 item 1); bg_dasha_systems, bg_nakshatra and bg_reference left it in the SS audit of 2026-10-06 (their prose_none could not be shown true)


def _doc(mutate, aid=AID):
    d = copy.deepcopy(DECL)
    mutate(d["assets"][aid])
    return d


def _refused(mutate, match, aid=AID):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(mutate, aid))


def _line(ptr):
    rel, n = ptr.rsplit(":", 1)
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()[int(n) - 1]


# ───────────────────────── Part 1: the committed entry ─────────────────────────

def test_the_file_is_1_12_0_and_the_latta_declares_prose_fields_empty_with_a_coupling():
    assert DECL["version"] == _decl_version.CURRENT and ac.validate_declarations(DECL)
    assert ENTRY["prose_fields"] == [] and ENTRY["evidence_kind"] == "writer"
    ev = ENTRY["evidence"]["prose_fields"]
    cites = ac._EVIDENCE_ANY_CITE_RE.findall(ev)
    assert cites == ["platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py"] * 3 and not ac._EVIDENCE_TEST_PATH_RE.search(ev)
    assert [int(x) for x in re.findall(r"vedha\.py:([0-9]+)", ev)] == [122, 86, 181]
    assert "LATTA_ROWS" in _line("platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:122") and "AFFLICTION_CONDITION" in _line("platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:86")
    assert "INSERT INTO bg_phaladeepika_latta" in _line("platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:181") and "N-94" in ev and "Carr.D1" in ev


def test_the_coupling_is_what_the_strategist_ruled_and_only_the_latta_declares_one():
    assert list(PC) == list(ac.PROSE_COUPLING_DECL_FIELDS) == ["to", "columns", "why", "evidence"]
    assert DECL["prose_coupling_declaration_fields"] == list(ac.PROSE_COUPLING_DECL_FIELDS)
    assert PC["to"] == "carriage_d1" and PC["columns"] == ["effect_description", "affliction_condition"]
    assert "transcription" in PC["why"] and "Carr.D1" in PC["why"] and "N-94" in PC["why"] and "OCR English" in PC["why"] and "sourced_ocr_unverified" in PC["why"]
    _mor = next(i for i, l in enumerate((ROOT / "platform/scripts/governance/carriage_d1.py").read_text(encoding="utf-8").splitlines(), 1) if l.startswith("def match_ordinal_row"))
    assert PC["evidence"] == f"platform/scripts/governance/carriage_d1.py:{_mor}" and "def match_ordinal_row" in _line(PC["evidence"])        # the pointer follows the function, wherever it moves
    assert [a for a, e in DECL["assets"].items() if "prose_coupling" in e] == [AID]
    assert sorted(a for a, e in DECL["assets"].items() if e.get("prose_fields") == []) == sorted(EXISTING_EMPTY + BATCH2_EMPTY + [AID, "bg_ephemeris", "bg_gochara_arcs", *RESIDUAL_PROSE_NONE, "bo_samvada", "bo_drishti"])    # + bo_samvada, bo_drishti: checked prose_none (E5.7 L2 fill)
    for a in EXISTING_EMPTY + BATCH2_EMPTY:                                              # the four earlier [] assets declare no coupling: inert
        assert "prose_coupling" not in DECL["assets"][a] and DECL["assets"][a]["prose_fields"] == []
    d = DECL["description"].split("Version 1.12.0", 1)[1]
    assert "bg_phaladeepika_latta's entry ONLY" in d and "no other asset or structure changed" in d and "N-94" in d and "prose_coupling_declaration_fields" in d
    assert ac.prose_coupling_problem(ENTRY) is None
    for word in ("verbatim", "accurate", "exact"):                       # the latta tests pin this vocabulary out of the entry and the description
        assert word not in json.dumps(ENTRY).lower().replace('"mode": "exactly"', "") and word not in d.lower()


def test_the_covered_columns_are_derived_from_the_spec_not_declared():
    assert d1.prose_coverage(SPEC) == {"effect_description": "effect", "affliction_condition": "affliction_condition"}
    assert "verse_ref" not in d1.prose_coverage(SPEC)                      # an `equals` constant is not prose coverage
    assert not {"graha", "count_from_graha", "direction"} & set(d1.prose_coverage(SPEC))      # claim fields are not either
    assert "covered" not in PC and set(PC) == {"to", "columns", "why", "evidence"}


@pytest.mark.parametrize("mutate, match", [
    (lambda e: e["prose_coupling"].__setitem__("to", "carriage_d2"), "`to` must be 'carriage_d1'"),
    (lambda e: e["prose_coupling"].__setitem__("to", None), "`to` must be"),
    (lambda e: e["prose_coupling"].__setitem__("extra", "x"), "unknown field"),
    (lambda e: e["prose_coupling"].__setitem__("columns", []), "non-empty list"),
    (lambda e: e["prose_coupling"].__setitem__("columns", "effect_description"), "non-empty list"),
    (lambda e: e["prose_coupling"].__setitem__("columns", ["effect_description", "effect_description"]), "distinct"),
    (lambda e: e["prose_coupling"].__setitem__("columns", ["effect description"]), "identifiers"),
    (lambda e: e["prose_coupling"].__setitem__("columns", [f"c{i}" for i in range(17)]), "at most 16"),
    (lambda e: e.__setitem__("prose_fields", ["effect_description"]), "only qualifies a declared prose_fields \\[\\]"),
    (lambda e: e.update(prose_fields=None, evidence_kind=None, evidence=dict(e["evidence"], prose_fields=None)), "only qualifies a declared prose_fields \\[\\]"),
    (lambda e: e["carriage"].__setitem__("spec", None), "declares no `spec`"),
    (lambda e: e["prose_coupling"].__setitem__("why", "effect_description and affliction_condition restate the passage clauses, which Carr.D1 checks"), "transcription and Carr.D1"),
    (lambda e: e["prose_coupling"].__setitem__("why", "effect_description and affliction_condition are transcription of the stored OCR English passage text"), "transcription and Carr.D1"),
    (lambda e: e["prose_coupling"].__setitem__("why", ""), "prose_coupling.why"),
    (lambda e: e["prose_coupling"].__setitem__("why", "short"), "prose_coupling.why"),
    (lambda e: e["prose_coupling"].__setitem__("why", "TBD transcription of the passage rests on Carr.D1 later"), "placeholder"),
    (lambda e: e["prose_coupling"].__setitem__("why", " " + e["prose_coupling"]["why"]), "prose_coupling.why"),
    (lambda e: e["prose_coupling"].__setitem__("evidence", "TBD"), "prose_coupling.evidence"),
    (lambda e: e["prose_coupling"].__setitem__("evidence", ""), "prose_coupling.evidence"),
    (lambda e: e["prose_coupling"].__setitem__("evidence", "platform/scripts/governance/no_such_file.py:1"), "prose_coupling.evidence"),
    (lambda e: e["prose_coupling"].__setitem__("evidence", "platform/scripts/governance/carriage_d1.py:99999"), "line 99999"),
    (lambda e: e["prose_coupling"].__setitem__("evidence", "unverified:strategist ruling N-94 recorded in the run decisions log"), "may not be `unverified:`"),
])
def test_a_malformed_or_unsound_coupling_is_refused(mutate, match):
    _refused(mutate, match)


# ── the guard keys on the D1 spec: each mutation of the spec leaves a coupled column uncovered ──

def test_MUTATION_dropping_affliction_condition_from_the_d1_spec_refuses_the_coupling():
    _refused(lambda e: e["carriage"]["spec"].__setitem__("extra_fields", [x for x in e["carriage"]["spec"]["extra_fields"] if x["column"] != "affliction_condition"]),
             "column 'affliction_condition' is not covered by the D1 spec")


def test_MUTATION_dropping_the_effect_mapping_or_the_clauses_refuses_the_coupling():
    _refused(lambda e: (e["carriage"]["spec"].pop("non_claim_columns"), e["carriage"]["spec"]["fields"].__setitem__("effect", "source_citation")),     # C1-1: source_citation is a declared non-claim; drop it so the mutation reaches the coupling check
             "column 'effect_description' is not covered by the D1 spec")
    with pytest.raises(ac.DeclarationsError, match="effect_clauses"):                    # the D1 spec cannot even be valid without its clauses
        ac.validate_declarations(_doc(lambda e: e["carriage"]["spec"].pop("effect_clauses")))


def test_a_column_that_is_only_a_claim_field_a_constant_or_absent_from_the_spec_is_not_covered():
    _refused(lambda e: e["prose_coupling"].__setitem__("columns", ["effect_description", "graha"]), "claim field")
    _refused(lambda e: e["prose_coupling"].__setitem__("columns", ["effect_description", "verse_ref"]), "checked only against a constant")
    _refused(lambda e: e["prose_coupling"].__setitem__("columns", ["effect_description", "source_citation"]), "never 'source_citation'")
    _refused(lambda e: e["prose_coupling"].__setitem__("columns", ["effect_description", "no_such_column"]), "never 'no_such_column'")
    ef = {"column": "affliction_condition", "kind": "equals", "value": "If, when thus counting"}
    _refused(lambda e: e["carriage"]["spec"].__setitem__("extra_fields", [ef] + [x for x in e["carriage"]["spec"]["extra_fields"] if x["column"] != "affliction_condition"]),
             "checked only against a constant")


def test_a_coupling_needs_the_d1_transcription_carriage_it_rests_on():
    pc = copy.deepcopy(PC)
    for aid in EXISTING_EMPTY:                                             # no carriage declaration at all
        d = copy.deepcopy(DECL)
        d["assets"][aid]["prose_coupling"] = pc
        with pytest.raises(ac.DeclarationsError, match="transcription' that applies 'D1'"):
            ac.validate_declarations(d)
    judged = dict(nature="ratified_judgment", ruling="N-9", why="a ratified judgment seed, not a transcription of a passage", evidence="platform/scripts/governance/carriage_d1.py:1")
    _refused(lambda e: e.update(carriage=judged, vocab_alias=None, ldgr_source=None, null_convention=None), "transcription' that applies 'D1'")
    comp = dict(nature="computation", applies="D3", why="a computation re-derived by D3", evidence="platform/scripts/governance/carriage_d1.py:1")
    _refused(lambda e: e.update(carriage=comp, vocab_alias=None, ldgr_source=None, null_convention=None), "transcription' that applies 'D1'")
    deriv = dict(nature="derivation", applies="D3", why="a derivation re-derived by D3", evidence="platform/scripts/governance/carriage_d1.py:1")
    _refused(lambda e: e.update(carriage=deriv, vocab_alias=None, ldgr_source=None, null_convention=None), "transcription' that applies 'D1'")


# ───────────────────────── Part 2: the measure-time glue (offline) ─────────────────────────

def _ctx(types=TYPES, cols=COLS, written=None):
    return dict(table=AID, own={AID: (cols, types, {})}, tests=(), vocabulary=set(), counts=None, paths=[], written={AID: set(COLS)} if written is None else written)


def test_inert_until_declared_the_four_earlier_empty_assets_read_exactly_as_before():
    assert all(ac.load_asset_declarations()[a].get("prose_none") is not None for a in CONVERTED)
    for a in CONVERTED:                                                                       # no grandfather: stripped of its checked prose_none, a bare [] reads NO_DETECTOR on all six
        ent = {k: v for k, v in ac.load_asset_declarations()[a].items() if k != "prose_none"}
        out = ac.prose_checks(a, ent, dict(table="t", own={"t": (["a"], {"a": "text"}, {})}, tests=(), vocabulary=set(), counts=None, paths=[], written={"t": {"a"}}))
        assert all(out[c]["v"] == NO_DET and "prose_none" in out[c]["measured"] and "cause" not in out[c] for c in NARR + list(ac.NULL_CHECKS)), a
    undeclared = ac.prose_checks(AID, dict(ENTRY, prose_fields=None, prose_coupling=None), _ctx())
    assert all(undeclared[c]["v"] == NO_DET and "undeclared" in undeclared[c]["measured"] for c in NARR)


def test_a_coupled_asset_reads_the_na_candidate_with_its_block_and_names_what_it_does_not_claim():
    out = ac.prose_checks(AID, ENTRY, _ctx())
    for c in NARR:
        assert out[c]["v"] == NA and out[c]["cause"] == "no-prose"
        b = out[c]["prose_coupling"]
        assert b == dict(to="carriage_d1", columns=["effect_description", "affliction_condition"],
                         covered={"effect_description": "effect", "affliction_condition": "affliction_condition"}, unclassified_text_columns=["source_citation", "table_version"])
        assert "rests on Carr.D1 PASS (coupled)" in out[c]["measured"] and "source_citation, table_version" in out[c]["measured"]
    assert all(out[c]["v"] == NA and out[c]["cause"] == "no-prose-declared" and "prose_coupling" not in out[c] for c in ac.NULL_CHECKS)


def test_an_unsound_coupling_that_slipped_past_the_validator_reads_no_detector_never_na_at_measure_time():
    bad = copy.deepcopy(ENTRY)
    bad["carriage"]["spec"]["extra_fields"] = [x for x in bad["carriage"]["spec"]["extra_fields"] if x["column"] != "affliction_condition"]
    out = ac.prose_checks(AID, bad, _ctx())
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert out[c]["v"] == NO_DET and "coupling is refused" in out[c]["measured"] and "affliction_condition" in out[c]["measured"]
    assert all("prose_coupling" not in out[c] for c in out)


def test_a_coupled_column_that_is_absent_from_the_table_or_not_text_is_refused_at_measure_time():
    out = ac.prose_checks(AID, ENTRY, _ctx(cols=[c for c in COLS if c != "affliction_condition"]))
    assert all(out[c]["v"] == NO_DET and "not columns of the asset's table" in out[c]["measured"] for c in NARR)
    out = ac.prose_checks(AID, ENTRY, _ctx(types=dict(TYPES, affliction_condition="integer")))
    assert all(out[c]["v"] == NO_DET and "not text columns" in out[c]["measured"] and "affliction_condition" in out[c]["measured"] for c in NARR)
    out = ac.prose_checks(AID, ENTRY, _ctx(types=dict(TYPES, effect_description="jsonb")))
    assert all(out[c]["v"] == NO_DET for c in NARR)
    assert all(ac.prose_checks(AID, ENTRY, _ctx(types=dict(TYPES, effect_description=t)))[NARR[0]]["v"] == NA for t in ("text", "character varying", "citext"))


def test_the_old_guards_still_come_first_unreadable_writes_and_a_narration_vocabulary_hit():
    assert all(v["v"] == NO_DET and "could not be read" in v["measured"] for v in ac.prose_checks(AID, ENTRY, _ctx(written={})).values())
    ctx = dict(_ctx(), vocabulary={"graha"})                 # some other asset declares a column this writer writes (and does not couple) as prose: the reverse leg still FAILs
    out = ac.prose_checks(AID, ENTRY, ctx)
    assert out["Narr.agree"]["v"] == FAIL and "prose_coupling" not in out["Narr.agree"]
    # E5.7 (SS 2026-10-06 (2)): the reverse leg is scoped PER ASSET, so another asset declaring the same column NAME as narration in ITS OWN table
    # (bg_vedha_malefic_scale.effect_description) does not turn this asset's coupled N/A into a FAIL ...
    out2 = ac.prose_checks(AID, ENTRY, dict(_ctx(), vocabulary={"effect_description": {"bg_vedha_malefic_scale"}, "affliction_condition": {"bg_vedha_malefic_scale"}}))
    assert all(out2[c]["v"] == NA for c in NARR)
    # ... but a declaration by an asset that shares THIS table (or by an asset whose tables are unknown: the wildcard) is still a hit
    shared = ac.prose_checks(AID, ENTRY, dict(_ctx(), vocabulary={"effect_description": {AID}}))
    assert shared["Narr.agree"]["v"] == FAIL and f"{AID}.effect_description" in shared["Narr.agree"]["measured"]
    assert ac.prose_checks(AID, ENTRY, dict(_ctx(), vocabulary={"effect_description": {None}}))["Narr.agree"]["v"] == FAIL
    # ... and a write into the declaring asset's own table is a hit (the table.column scoping the exclusion form shares)
    other = dict(_ctx(), vocabulary={"effect_description": {"some_other_table"}}, written={"some_other_table": {"effect_description"}})
    assert ac.prose_checks(AID, ENTRY, other)["Narr.agree"]["v"] == FAIL


def test_declared_facts_carry_the_coupling_only_for_the_asset_that_declares_it():
    decl = ac.load_asset_declarations()
    assert ac.declared_facts(decl, AID)["declared_prose_coupling"] == dict(to="carriage_d1", columns=["effect_description", "affliction_condition"], covered={"effect_description": "effect", "affliction_condition": "affliction_condition"})
    for a in EXISTING_EMPTY + ["bg_phaladeepika_latta_none"]:
        assert "declared_prose_coupling" not in ac.declared_facts(decl, a)


# ───────────────────────── Part 3: the rollup guard (offline; real D1 records on the committed fixture) ─────────────────────────

def _d1(rows=None, spec=None, state="sourced_ocr_unverified", chunks=None):
    return d1.d1_measure(spec or SPEC, state, chunks or CHUNKS, copy.deepcopy(rows if rows is not None else ROWS), AID)


def _ms(d1rec, coupled=True, entry=ENTRY):
    m = ac.prose_checks(AID, entry, _ctx())
    if not coupled:
        m = {k: {kk: vv for kk, vv in v.items() if kk != "prose_coupling"} for k, v in m.items()}
    out = {c: m[c] for c in NARR}
    if d1rec is not None:
        out["Carr.D1"] = d1rec
    out["Carr.D2"] = ac._na("x", "not-the-declared-carriage")
    out["Carr.D3"] = ac._na("x", "not-the-declared-carriage")
    return out


def _narr(ms, facts=None):
    cell = ac.rollup_asset("L0", ms, facts)["Narr"]
    return cell, {c["criterion"]: c for c in cell["checks"]}


def test_d1_pass_releases_all_four_narr_checks_to_na_under_the_declared_rules():
    cell, chk = _narr(_ms(_d1()), FACTS)
    assert cell["v"] == NA and all(chk[c]["v"] == NA and chk[c]["rule_id"] == f"{c}#measured:no-prose" for c in NARR)
    cell, _ = _narr(_ms(_d1()))                                             # no facts: the record's own block is enough
    assert cell["v"] == NA


def _one_word_off():
    rows = copy.deepcopy(ROWS)
    [r.update(effect_description=r["effect_description"].replace("Quarrel", "Quarrels")) for r in rows if r["graha"] == "Venus"]
    return rows


@pytest.mark.parametrize("name, rec, reads", [
    ("PARTIAL: one effect word altered", lambda: _d1(rows=_one_word_off()), "PARTIAL"),
    ("PARTIAL: a row missing", lambda: _d1(rows=[r for r in ROWS if r["graha"] != "Sun"]), "PARTIAL"),
    ("PARTIAL: one affliction word altered", lambda: _d1(rows=[dict(r, affliction_condition=r["affliction_condition"].replace("sickness", "sickly")) if r["graha"] == "Moon" else r for r in ROWS]), "PARTIAL"),
    ("NO_DETECTOR: unsourced citation_state", lambda: _d1(state="unsourced"), "NO_DETECTOR"),
    ("NO_DETECTOR: refuted citation_state", lambda: _d1(state="refuted"), "NO_DETECTOR"),
    ("NO_DETECTOR: a chunk is missing", lambda: _d1(chunks={k: v for k, v in CHUNKS.items() if k.endswith("0338_c01")}), "NO_DETECTOR"),
    ("FAIL: a forged FAIL record", lambda: dict(_d1(), v=FAIL), "FAIL"),
    ("ERRORED", lambda: dict(v=ERRORED, measured="check errored: x", citation_state="sourced_ocr_unverified"), "ERRORED"),
    ("a bare PASS with no verified passage evidence", lambda: dict(v=PASS, measured="x", citation_state="sourced_ocr_unverified"), "NO_DETECTOR"),
    ("the D1 record absent", lambda: None, "not measured"),
])
def test_MUTATION_a_d1_that_is_not_pass_makes_narr_no_detector_never_na(name, rec, reads):
    cell, chk = _narr(_ms(rec()), FACTS)
    assert cell["v"] == NO_DET, name
    for c in NARR:
        assert chk[c]["v"] == NO_DET and f"Narr N/A rests on Carr.D1 PASS (coupled): Carr.D1 reads {reads}" in chk[c]["reason"], (name, chk[c]["reason"])
    cell, _ = _narr(_ms(rec()))                                             # the record's own block alone is enough to refuse
    assert cell["v"] == NO_DET


def test_the_exact_refusal_text_for_a_partial_d1():
    _, chk = _narr(_ms(_d1(rows=_one_word_off())), FACTS)
    assert chk["Narr.agree"]["reason"] == "Narr N/A rests on Carr.D1 PASS (coupled): Carr.D1 reads PARTIAL"
    _, chk = _narr(_ms(dict(v=PASS, measured="x", citation_state="sourced_ocr_unverified")), FACTS)
    assert chk["Narr.lint"]["reason"].startswith("Narr N/A rests on Carr.D1 PASS (coupled): Carr.D1 reads NO_DETECTOR (the D1 record says PASS: D1 PASS without verified passage evidence")


def test_a_record_that_dropped_its_own_block_cannot_slip_through_when_the_declaration_says_coupled():
    ms = _ms(_d1(rows=_one_word_off()), coupled=False)
    assert _narr(ms, {})[0]["v"] == NO_DET                                      # (N-150: a plain N/A is released only for an enumerated legacy asset) no coupling facts and no block: indistinguishable from an undeclared asset (the facts are what bind it)
    cell, chk = _narr(ms, FACTS)
    assert cell["v"] == NO_DET and "carries no well-formed prose_coupling block" in chk["Narr.agree"]["reason"]
    ms = _ms(_d1(), coupled=False)
    assert _narr(ms, FACTS)[0]["v"] == NO_DET                                # even with a PASS D1: the record must carry what it rests on


@pytest.mark.parametrize("tamper", [
    lambda b: b.__setitem__("to", "carriage_d2"), lambda b: b.__setitem__("columns", []), lambda b: b.__setitem__("covered", {}),
    lambda b: b.__setitem__("covered", {"effect_description": "effect"}), lambda b: b.__setitem__("columns", ["effect_description"]),
    lambda b: b.__setitem__("columns", ["affliction_condition", "effect_description"]),
])
def test_a_tampered_block_is_not_honoured(tamper):
    ms = _ms(_d1())
    for c in NARR:
        tamper(ms[c]["prose_coupling"])
    assert _narr(ms, FACTS)[0]["v"] == NO_DET


def test_a_block_naming_another_detector_is_not_honoured_even_with_no_declared_facts_to_compare_with():
    ms = _ms(_d1(rows=_one_word_off()))
    for c in NARR:
        ms[c]["prose_coupling"]["to"] = "carriage_d2"
    assert _narr(ms)[0]["v"] == NO_DET and "no well-formed prose_coupling block" in _narr(ms)[1]["Narr.agree"]["reason"]


def test_MUTATION_a_d1_that_never_graded_affliction_condition_cannot_back_the_na_even_when_it_reads_pass():
    """Drop affliction_condition from the D1 spec and run D1 anyway: the effect column still matches, D1 reads PASS, and the Narr record (built from the full declaration) still names the column.
    The D1 record has no per-row result for it, so the rollup refuses: the measured coverage does not depend on any declaration."""
    spec = copy.deepcopy(SPEC)
    spec["extra_fields"] = [x for x in spec["extra_fields"] if x["column"] != "affliction_condition"]
    rec = _d1(spec=spec)
    assert rec["v"] == PASS and "affliction_condition" not in rec["d1"]["rows"][0]["result"]
    cell, chk = _narr(_ms(rec), FACTS)
    assert cell["v"] == NO_DET
    assert "no passing per-row result for the coupled column 'affliction_condition'" in chk["Narr.agree"]["reason"] and "Carr.D1 did not measure that column" in chk["Narr.agree"]["reason"]
    spec = copy.deepcopy(SPEC)                                               # the effect column remapped: its per-row result key is gone too
    spec["fields"] = dict(spec["fields"], effect="source_citation")
    rows = [dict(r, source_citation=r["effect_description"]) for r in ROWS]
    rec = _d1(spec=spec, rows=rows)
    assert _narr(_ms(rec), FACTS)[0]["v"] in (NO_DET, NA)                     # (the covered key for effect_description is `effect`; a remap is caught at validation, test above)


def test_a_failing_per_row_value_for_a_coupled_column_in_a_pass_record_is_refused():
    rec = _d1()
    rec["d1"]["rows"][3]["result"]["affliction_condition"] = False             # a forged record: PASS verdict, a row that did not match
    assert _narr(_ms(rec), FACTS)[0]["v"] == NO_DET
    rec = _d1()
    rec["d1"]["rows"] = []
    assert _narr(_ms(rec), FACTS)[0]["v"] == NO_DET


def test_null_ok_on_the_reserved_empty_effect_rows_is_what_a_pass_carries():
    rec = _d1()
    res = {r["row"]: r["result"] for r in rec["d1"]["rows"]}
    assert res["Mars"]["effect"] == "NULL-ok" and res["Saturn"]["effect"] == "NULL-ok" and res["Sun"]["effect"] is True and all(r["affliction_condition"] is True for r in res.values())
    assert _narr(_ms(rec), FACTS)[0]["v"] == NA


def test_the_four_earlier_empty_assets_have_no_unchecked_release_and_no_d1_at_all():
    for a in CONVERTED:
        ent = {k: v for k, v in ac.load_asset_declarations()[a].items() if k != "prose_none"}
        m = ac.prose_checks(a, ent, dict(table="t", own={"t": (["a"], {"a": "text"}, {})}, tests=(), vocabulary=set(), counts=None, paths=[], written={"t": {"a"}}))
        ms = {c: m[c] for c in NARR}
        cell = ac.rollup_asset("L0", ms, ac.declared_facts(ac.load_asset_declarations(), a))["Narr"]
        assert cell["v"] == NO_DET and "d1" not in ms, a


def test_the_gap_ledger_releases_a_coupled_na_only_where_the_rollup_does():
    ok, bad = _ms(_d1()), _ms(_d1(rows=_one_word_off()))
    assert ac._na_released("Narr.agree", ok["Narr.agree"], ok, "L0") is True
    assert ac._na_released("Narr.agree", bad["Narr.agree"], bad, "L0") is False
    assert ac._na_released("Narr.agree", ok["Narr.agree"]) is False           # coupled and no context to read Carr.D1: not released
    plain = dict(v=NA, measured="m", cause="no-prose")
    assert ac._na_released("Narr.agree", plain) is False and ac._na_released("Narr.agree", plain, facts={"declared_prose_bare_legacy": True}) is False          # an uncoupled unchecked N/A: no grandfather, never released


def _open_row(crit):
    return dict(asset=AID, gap_id=f"{AID}-{crit}", kind="gap", criterion=crit, what="w", change="", detector="d", owner="asset_census", gate="this asset's certification", state="OPEN", ts="t0")


def _emit(monkeypatch, tmp_path, ms):
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    (tmp_path / "asset_gaps.jsonl").write_text("".join(json.dumps(_open_row(c)) + "\n" for c in NARR), encoding="utf-8")
    census = dict(layer="L0", assets=[dict(asset_id=AID, layer="L0", measurements=ms)])
    out = ac.emit_gaps(census)
    rows = [json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return out, {r["criterion"]: r["state"] for r in rows}


def test_the_gap_ledger_closes_the_four_narr_rows_on_a_coupled_na_only_while_carr_d1_passes(monkeypatch, tmp_path):
    (added, skipped, closed, reopened), states = _emit(monkeypatch, tmp_path / "ok", _ms(_d1()))
    assert closed == 4 and set(states.values()) == {"CLOSED"}
    (added, skipped, closed, reopened), states = _emit(monkeypatch, tmp_path / "bad", _ms(_d1(rows=_one_word_off())))
    assert closed == 0 and set(states.values()) == {"OPEN"}                    # a closure the rollup refuses is never recorded (N.8)


def test_the_narr_guard_never_touches_a_non_narr_criterion_or_a_non_na_record():
    ms = _ms(_d1(rows=_one_word_off()))
    assert ac.narr_coupling_problem("Carr.D1", "L0", ms["Carr.D1"], FACTS, ms) is None
    assert ac.narr_coupling_problem("Null.blank_rows", "L0", dict(v=PASS), FACTS, ms) is None
    assert ac.narr_coupling_problem("Narr.agree", "L0", None, FACTS, ms) is None
    assert ac.narr_coupling_problem("Narr.agree", "L0", dict(v=FAIL, measured="x"), None, ms) is None


# ───────────────────────── review F1-F5 (adversarial review of #2998) ─────────────────────────

def _strip(e=ENTRY):
    return {k: v for k, v in e.items() if k != "prose_coupling"}


def test_F1_deleting_the_prose_coupling_block_is_refused_by_validation_and_names_the_missing_coupling():
    with pytest.raises(ac.DeclarationsError, match="prose_coupling is missing.*needs a `prose_coupling` to carriage_d1"):
        ac.validate_declarations(_doc(lambda e: e.pop("prose_coupling")))
    assert ac.prose_empty_d1_problem(_strip()) and ac.prose_empty_d1_problem(ENTRY) is None
    for nature, applies in (("computation", "D3"), ("derivation", "D2")):               # only a D1 transcription carriage triggers it
        assert ac.prose_empty_d1_problem(dict(prose_fields=[], carriage=dict(nature=nature, applies=applies))) is None
    assert ac.prose_empty_d1_problem(dict(prose_fields=[])) is None and ac.prose_empty_d1_problem(dict(prose_fields=None, carriage=ENTRY["carriage"])) is None


def test_F1_the_four_earlier_empty_assets_are_not_touched_by_the_new_refusal():
    decl = ac.load_asset_declarations()
    for a in EXISTING_EMPTY:
        assert decl[a]["prose_fields"] == [] and (not isinstance(decl[a].get("carriage"), dict) or decl[a]["carriage"].get("nature") in (None, *ac.CEILING_NATURES)), a        # N-156: a declared ceiling is not a D1 transcription carriage
        assert ac.prose_empty_d1_problem(decl[a]) is None and "declared_prose_coupling_missing" not in ac.declared_facts(decl, a), a


def test_F1_at_measure_time_a_stripped_entry_reads_no_detector_never_na():
    out = ac.prose_checks(AID, _strip(), _ctx())
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert out[c]["v"] == NO_DET and "needs a `prose_coupling` to carriage_d1" in out[c]["measured"], c


def test_F1_the_rollup_refuses_a_plain_narr_na_when_the_declaration_is_empty_prose_on_d1_without_its_coupling():
    facts = ac.declared_facts({AID: _strip()}, AID)
    assert facts["declared_prose_coupling_missing"] is True and "declared_prose_coupling" not in facts
    plain = {c: ac._na("prose_fields [] declared", "no-prose") for c in NARR}
    cell = ac.rollup_asset("L0", plain, facts)["Narr"]
    assert cell["v"] == NO_DET and all("no prose_coupling" in c["reason"] for c in cell["checks"] if c["criterion"] in NARR)
    assert ac.rollup_asset("L0", plain, {"declared_prose_fields": []})["Narr"]["v"] == NO_DET                          # no grandfather: a plain N/A with no coupling and no checked block is no release


def test_F2_the_gap_ledger_does_not_close_a_narr_row_for_a_hand_stripped_block_with_a_partial_d1(monkeypatch, tmp_path):
    ms = _ms(_d1(rows=_one_word_off()), coupled=False)                          # the record dropped its block, D1 PARTIAL: the rollup reads NO_DETECTOR with the declared facts
    (added, skipped, closed, reopened), states = _emit(monkeypatch, tmp_path, ms)
    assert closed == 0 and set(states.values()) == {"OPEN"}
    ms = _ms(_d1(), coupled=False)                                                # even with a PASS D1 the record must carry what it rests on
    (added, skipped, closed, reopened), states = _emit(monkeypatch, tmp_path / "pass", ms)
    assert closed == 0 and set(states.values()) == {"OPEN"}
    ok = _emit(monkeypatch, tmp_path / "ok", _ms(_d1()))
    assert ok[0][2] == 4 and set(ok[1].values()) == {"CLOSED"}


def test_F3_a_forged_covered_map_is_not_honoured_the_declared_spec_coverage_decides():
    ms = _ms(_d1())
    assert _narr(ms, FACTS)[0]["v"] == NA
    forged = {"effect_description": "effect", "affliction_condition": "effect"}      # points the second column at a result key that is True on every row
    for c in NARR:
        ms[c]["prose_coupling"]["covered"] = dict(forged)
    cell, chk = _narr(ms, FACTS)
    assert cell["v"] == NO_DET and "does not match the declared coupling and the D1 spec's own coverage" in chk["Narr.agree"]["reason"]
    no_cov = dict(FACTS["declared_prose_coupling"])
    no_cov.pop("covered")
    assert _narr(_ms(_d1()), {"declared_prose_coupling": no_cov})[0]["v"] == NO_DET   # a declared fact without its coverage cannot vouch


def test_F3_declared_facts_derive_the_coverage_from_the_spec():
    decl = ac.load_asset_declarations()
    assert ac.declared_facts(decl, AID)["declared_prose_coupling"]["covered"] == {"effect_description": "effect", "affliction_condition": "affliction_condition"}
    e = copy.deepcopy(ENTRY)
    e["carriage"]["spec"]["extra_fields"] = [x for x in e["carriage"]["spec"]["extra_fields"] if x["column"] != "affliction_condition"]
    assert ac.declared_facts({AID: e}, AID)["declared_prose_coupling"]["covered"] is None


@pytest.mark.parametrize("name", ["effect", "count", "direction"])
def test_F4_an_extra_field_named_like_a_matcher_result_key_is_refused(name):
    ef = {"column": name, "kind": "equals", "value": "x"}
    with pytest.raises(ac.DeclarationsError, match="collides with a result key"):
        ac.validate_declarations(_doc(lambda e: e["carriage"]["spec"]["extra_fields"].append(ef)))
    spec = copy.deepcopy(SPEC)
    spec["extra_fields"].append(dict(ef, kind="passage_text"))
    with pytest.raises(d1.SpecError):
        d1.prose_coverage(spec)
    assert "collides" in (ac.prose_coupling_problem(dict(ENTRY, carriage=dict(CAR, spec=spec))) or "")


def test_F5_a_d1_evaluation_error_is_not_swallowed_into_a_pass():
    ms = _ms(_d1())
    ms["Carr.D1"] = dict(ms["Carr.D1"], v="BOGUS")
    bad = ac.narr_coupling_problem("Narr.agree", "L0", ms["Narr.agree"], FACTS, ms)
    assert bad and "Carr.D1 cannot be evaluated" in bad
    assert ac.narr_coupling_problem("Narr.agree", "NOPE", ms["Narr.agree"], FACTS, _ms(_d1())) is not None


def test_F5_a_malformed_block_is_refused_not_a_crash():
    for mut in (lambda b: b.__setitem__("columns", []), lambda b: b.pop("covered"), lambda b: b.__setitem__("columns", "effect_description"),
                lambda b: b.__setitem__("covered", ["effect"]), lambda b: b.__setitem__("covered", {"effect_description": 1, "affliction_condition": None}),
                lambda b: b.__setitem__("columns", [["x"]]), lambda b: b.clear()):
        ms = _ms(_d1())
        for c in NARR:
            mut(ms[c]["prose_coupling"])
        assert ac.narr_coupling_problem("Narr.agree", "L0", ms["Narr.agree"], FACTS, ms) is not None
        assert _narr(ms, FACTS)[0]["v"] == NO_DET and _narr(ms)[0]["v"] == NO_DET


# ───────────────────────── Part 4: REAL detectors on a disposable Postgres ─────────────────────────

def _per_asset_vocabulary(decls):
    """The production reading (measure() hands prose_checks the PER-ASSET vocabulary): bg_vedha_malefic_scale's effect_description is narration in ITS table only; an asset whose tables are not
    given here is a wildcard (never weaker than the global reading)."""
    return ac.prose_vocabulary(decls, {"bg_vedha_malefic_scale": {"bg_vedha_malefic_scale"}})


def _real(monkeypatch, pg, extra=(), entry=None):
    """Carr.D1 (the declared carriage check) and the Narr/Null records, by the REAL glue on the 8 corpus rows (+ SQL `extra` applied after the rows)."""
    s3._real(monkeypatch, pg, dl._setup() + list(extra))
    ent = entry or ENTRY
    m = {}
    m.update(ac.carriage_declared_checks(AID, ent["carriage"], AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[]))
    m.update(ac._measure_prose(AID, ent, R, FILES, CAT, [], set(), (), _per_asset_vocabulary(ac.load_asset_declarations())))
    return m


def _cell(m, facts=FACTS):
    cell = ac.rollup_asset("L0", {k: v for k, v in m.items() if k.startswith(("Narr.", "Carr."))}, facts)["Narr"]
    return cell, {c["criterion"]: c for c in cell["checks"]}


def test_REAL_the_eight_corpus_rows_pass_d1_and_the_four_narr_checks_read_na(monkeypatch, disposable_pg):
    m = _real(monkeypatch, disposable_pg)
    assert m["Carr.D1"]["v"] == PASS and m["Carr.D1"]["citation_state"] == "sourced_ocr_unverified"
    for c in NARR:
        assert m[c]["v"] == NA and m[c]["prose_coupling"]["columns"] == ["effect_description", "affliction_condition"]
    assert m["Narr.agree"]["prose_coupling"]["unclassified_text_columns"] == ["source_citation", "table_version"]
    cell, chk = _cell(m)
    assert cell["v"] == NA and all(chk[c]["v"] == NA for c in NARR)
    assert ac.rollup_asset("L0", m, FACTS)["Carr"]["v"] == PASS


def test_REAL_the_effect_and_affliction_columns_each_have_a_per_row_result_from_the_real_d1_run(monkeypatch, disposable_pg):
    rows = _real(monkeypatch, disposable_pg)["Carr.D1"]["d1"]["rows"]
    assert len(rows) == 8 and all(r["result"]["affliction_condition"] is True and r["result"]["effect"] in (True, "NULL-ok") for r in rows)


@pytest.mark.parametrize("sql, label", [
    ("UPDATE bg_phaladeepika_latta SET effect_description = 'Quarrels.' WHERE graha = 'Venus'", "one effect word altered"),
    ("UPDATE bg_phaladeepika_latta SET effect_description = NULL WHERE graha = 'Sun'", "a stored effect removed"),
    ("UPDATE bg_phaladeepika_latta SET effect_description = 'Misery.' WHERE graha = 'Mars'", "a reserved-empty effect populated"),
    ("UPDATE bg_phaladeepika_latta SET affliction_condition = replace(affliction_condition, 'sickness', 'sickly') WHERE graha = 'Moon'", "one affliction word altered"),
    ("UPDATE bg_phaladeepika_latta SET affliction_condition = 'If, when thus counting, the natal star is the Latta star there is sickness.' WHERE graha = 'Rahu'", "an affliction paraphrase"),
    ("DELETE FROM bg_phaladeepika_latta WHERE graha = 'Saturn'", "a row missing"),
    ("UPDATE bg_phaladeepika_latta SET count_from_graha = 21 WHERE graha = 'Moon'", "a count altered"),
])
def test_REAL_MUTATION_a_d1_defect_makes_narr_no_detector_not_na(monkeypatch, disposable_pg, sql, label):
    m = _real(monkeypatch, disposable_pg, [sql + ";"])
    assert m["Carr.D1"]["v"] == PARTIAL, label
    cell, chk = _cell(m)
    assert cell["v"] == NO_DET, label
    assert all(chk[c]["reason"] == "Narr N/A rests on Carr.D1 PASS (coupled): Carr.D1 reads PARTIAL" for c in NARR), label
    assert all(m[c]["v"] == NA for c in NARR)                                  # the MEASUREMENT is still the N/A candidate: the rollup is what refuses


def test_REAL_MUTATION_an_unsourced_or_refuted_citation_state_is_not_na(monkeypatch, disposable_pg):
    for state in ("unsourced", "refuted"):
        ent = copy.deepcopy(ENTRY)
        ent["carriage"]["citation_state"] = state
        m = _real(monkeypatch, disposable_pg, entry=ent)
        assert m["Carr.D1"]["v"] == NO_DET
        cell, chk = _cell(m)
        assert cell["v"] == NO_DET and "Carr.D1 reads NO_DETECTOR" in chk["Narr.agree"]["reason"], state


def test_REAL_MUTATION_dropping_affliction_condition_from_the_d1_spec_is_not_na_in_either_path(monkeypatch, disposable_pg):
    ent = copy.deepcopy(ENTRY)
    ent["carriage"]["spec"]["extra_fields"] = [x for x in ent["carriage"]["spec"]["extra_fields"] if x["column"] != "affliction_condition"]
    with pytest.raises(ac.DeclarationsError, match="affliction_condition' is not covered"):      # (1) the declaration is refused outright
        ac.validate_declarations(_doc(lambda e: e.__setitem__("carriage", ent["carriage"])))
    m = _real(monkeypatch, disposable_pg, entry=ent)                           # (2) bypassing the validator: the measure-time glue refuses
    assert all(m[c]["v"] == NO_DET and "coupling is refused" in m[c]["measured"] for c in NARR)
    assert _cell(m)[0]["v"] == NO_DET
    full = _real(monkeypatch, disposable_pg)                                    # (3) the full Narr record over a D1 that never graded the column (the stale-record forgery)
    stale = dict(full, **{"Carr.D1": ac.carriage_declared_checks(AID, ent["carriage"], AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[])["Carr.D1"]})
    # C1-1: the column ledger now also names the dropped column (affliction_condition is a text column nothing matches), so D1 itself reads PARTIAL; the Narr guard still refuses
    assert stale["Carr.D1"]["v"] == PARTIAL and stale["Carr.D1"]["d1"]["column_ledger"]["uncovered"] == ["affliction_condition"] and _cell(stale)[0]["v"] == NO_DET
    ent2 = copy.deepcopy(ent)                                                       # the original forgery: declare the column a non-claim so D1 PASSes without ever grading it
    ent2["carriage"]["spec"]["non_claim_columns"] = ent2["carriage"]["spec"]["non_claim_columns"] + [dict(
        column="affliction_condition", why="affliction_condition is declared a non-claim here only to reproduce the forgery", evidence="platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:86")]
    stale2 = dict(full, **{"Carr.D1": ac.carriage_declared_checks(AID, ent2["carriage"], AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[])["Carr.D1"]})
    assert stale2["Carr.D1"]["v"] == PASS and _cell(stale2)[0]["v"] == NO_DET


def test_REAL_MUTATION_dropping_the_effect_mapping_is_not_na(monkeypatch, disposable_pg):
    ent = copy.deepcopy(ENTRY)
    ent["carriage"]["spec"].pop("non_claim_columns")                              # C1-1: source_citation is a declared non-claim; drop it so the mutation reaches the coupling check
    ent["carriage"]["spec"]["fields"]["effect"] = "source_citation"
    with pytest.raises(ac.DeclarationsError, match="effect_description' is not covered"):
        ac.validate_declarations(_doc(lambda e: e.__setitem__("carriage", ent["carriage"])))
    m = _real(monkeypatch, disposable_pg, entry=ent)
    assert all(m[c]["v"] == NO_DET and "coupling is refused" in m[c]["measured"] for c in NARR) and _cell(m)[0]["v"] == NO_DET


def test_REAL_the_four_narr_checks_and_only_they_depend_on_the_coupling(monkeypatch, disposable_pg):
    m = _real(monkeypatch, disposable_pg)
    broken = _real(monkeypatch, disposable_pg, ["UPDATE bg_phaladeepika_latta SET effect_description = 'Quarrels.' WHERE graha = 'Venus';"])
    for k in ("Null.schema_default", "Null.blank_rows"):                        # Null is the S1 lane's: it neither reads nor feeds the coupling
        assert m[k]["v"] == NA or m[k]["v"] == PASS
    assert ac.rollup_asset("L0", m, FACTS)["Carr"]["v"] == PASS and ac.rollup_asset("L0", broken, FACTS)["Carr"]["v"] == PARTIAL


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_REAL_cell_diff_across_all_40_l0_assets_only_the_latta_narr_checks_move(monkeypatch, disposable_pg):
    """BEFORE = the saved L0 measurements with the latta measured as it reads on #2995's declarations (prose_fields null; the three declared carriage / vocab / ldgr blocks; the Null convention)
    and AFTER = the same with the latta's Narr records measured under THIS declaration (prose_fields [] + prose_coupling). Every other asset's measurements are the saved ones in both."""
    assets = json.loads((SAVED / "census_L0.json").read_text(encoding="utf-8"))["L0"]["assets"]
    decl_after = ac.load_asset_declarations()
    before_ent = copy.deepcopy(ENTRY)
    before_ent.update(prose_fields=None, evidence_kind=None)
    before_ent["evidence"] = dict(before_ent["evidence"], prose_fields=None)
    before_ent.pop("prose_coupling")
    vocab = _per_asset_vocabulary(decl_after)
    s3._real(monkeypatch, disposable_pg, dl._setup())
    three = {}
    three.update(ac.carriage_declared_checks(AID, ENTRY["carriage"], AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[]))
    three.update(ac.vocab_alias_declared_check(AID, ENTRY["vocab_alias"], AID, COLS))
    three.update(ac.ldgr_source_declared_check(AID, ENTRY["ldgr_source"], AID, COLS, [["table_version", "graha"]]))
    mb = ac._measure_prose(AID, before_ent, R, FILES, CAT, [], set(), (), vocab)
    ma = ac._measure_prose(AID, ENTRY, R, FILES, CAT, [], set(), (), vocab)
    assert all(mb[c]["v"] == NO_DET for c in NARR) and all(ma[c]["v"] == NA for c in NARR)
    before, after, saved_cells = {}, {}, json.loads((SAVED / "census_L0.json").read_text(encoding="utf-8"))["rollup"]["layers"]["L0"]
    for a in assets:
        aid, base = a["asset_id"], dict(a["measurements"])
        facts = ac.facts_for_asset(a, decl_after)
        if aid == AID:
            base = {k: v for k, v in base.items() if k not in ("Ldgr.source_presence", "Vocab.alias") + ac.NARR_CHECKS + ac.NULL_CHECKS}
            base.update(three)
            b, n = dict(base, **{k: mb[k] for k in NARR + list(ac.NULL_CHECKS)}), dict(base, **{k: ma[k] for k in NARR + list(ac.NULL_CHECKS)})
        else:
            b = n = base
        before[aid], after[aid] = ac.rollup_asset("L0", b, facts), ac.rollup_asset("L0", n, facts)
        if aid != AID and aid in CONVERTED:
            assert {g: c["v"] for g, c in after[aid].items() if g != "Narr"} == {g: c["v"] for g, c in saved_cells[aid].items() if g != "Narr"} and after[aid]["Narr"]["v"] == NO_DET, aid    # E5.7: a saved unchecked N/A is not a release for a converted asset
        elif aid != AID:
            assert {g: c["v"] for g, c in after[aid].items()} == {g: c["v"] for g, c in saved_cells[aid].items()}, aid          # the saved census verdicts, untouched
    assert len(before) == len(after) == 40
    cells = [(aid, g, before[aid][g]["v"], after[aid][g]["v"]) for aid in before for g in before[aid] if before[aid][g]["v"] != after[aid][g]["v"]]
    assert cells == [(AID, "Narr", NO_DET, NA)]
    checks = [(aid, g, c0["criterion"], c0["v"], c1["v"]) for aid in before for g in before[aid]
              for c0, c1 in zip(before[aid][g]["checks"], after[aid][g]["checks"]) if c0["v"] != c1["v"] or c0.get("reason") != c1.get("reason")]
    assert sorted(checks) == sorted((AID, "Narr", c, NO_DET, NA) for c in NARR)
    l0_empty = [a for a in EXISTING_EMPTY if a in before]                      # bg_doshas, bg_ontology, bg_yogas (bo_laksana_rerank is an L2 asset: see the next test)
    assert l0_empty == ["bg_doshas", "bg_ontology", "bg_yogas"] and {a: after[a]["Narr"]["v"] for a in l0_empty} == {a: NO_DET for a in l0_empty}     # converted to prose_none: the saved unchecked N/A is no longer honoured until re-measured
    assert all(before[a]["Narr"] == after[a]["Narr"] for a in l0_empty)
    assert all(before[a] == after[a] for a in before if a != AID)
    assert {g: c["v"] for g, c in after[AID].items() if g != "Narr"} == {g: c["v"] for g, c in before[AID].items() if g != "Narr"}


# ───────────────────────── Part 5: nothing moves for an asset that does not declare it ─────────────────────────

@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_on_the_six_saved_censuses_no_cell_moves_zero_of_1143():
    decl = ac.load_asset_declarations()
    moved, n = [], 0
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved = d["rollup"]["layers"][L]
        now = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        for aid, cells in now.items():
            for g, c in cells.items():
                n += 1
                if c["v"] != saved[aid][g]["v"]:
                    moved.append((aid, g, saved[aid][g]["v"], c["v"]))
    assert n == 1143 and sorted(moved) == [(a, "Narr", NA, NO_DET) for a in CONVERTED]      # E5.7: the three converted assets read NO_DETECTOR on a saved census until re-measured with the checked prose_none


@pytest.mark.skipif(not (SAVED / "census_L2.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_bo_laksana_rerank_reads_no_detector_on_a_saved_census_until_remeasured_and_carries_no_coupling():
    d = json.loads((SAVED / "census_L2.json").read_text(encoding="utf-8"))
    a = [x for x in d["L2"]["assets"] if x["asset_id"] == "bo_laksana_rerank"][0]
    decl = ac.load_asset_declarations()
    cells = ac.rollup_asset("L2", a["measurements"], ac.facts_for_asset(a, decl))
    assert cells["Narr"]["v"] == NO_DET and d["rollup"]["layers"]["L2"]["bo_laksana_rerank"]["Narr"]["v"] == NA      # converted to a checked prose_none: the saved unchecked N/A is no longer a release
    assert "prose_coupling" not in decl["bo_laksana_rerank"] and not any("prose_coupling" in a["measurements"][c] for c in NARR)


def test_a_coupling_declared_on_a_hypothetical_second_asset_is_inert_for_every_other_asset():
    """The guard keys on the record's block or the declared facts: an asset with neither (every asset but one) is untouched whatever its D1 reads."""
    ms = {c: ac._na("x", "no-prose") for c in NARR}
    ms["Carr.D1"] = dict(v=FAIL, measured="x")
    assert ac.rollup_asset("L0", ms, {})["Narr"]["v"] == NO_DET                                                # no grandfather: an unchecked plain N/A is no release whatever D1 reads
    assert ac.rollup_asset("L0", ms, {"declared_prose_fields": []})["Narr"]["v"] == NO_DET


# ───────────────────────── Part 6: the E6.3 reader refuses a coupled Narr N/A whose Carr.D1 is not PASS ─────────────────────────

T = rd.T
NCRIT = "Narr.agree"
RID = f"{NCRIT}#measured:no-prose"
CFILE = rd.CFILE


def _census_with(ms, asset=AID):
    return rd.census_obj(ms, asset=asset, layer="L0")


def nworld(tmp_path, ms, *, entry=ENTRY, census_src=None, text=None, crits=(NCRIT,), extra_files=None, asset=AID):
    pathlib_tmp = pathlib.Path(tmp_path)
    pathlib_tmp.mkdir(parents=True, exist_ok=True)
    w = World(tmp_path, census=census_src or rd.CENSUS_TEXT)
    ent = {k: entry.get(k) for k in ("prose_fields", "prose_coupling", "carriage") if entry.get(k) is not None}
    w.declarations_text = json.dumps({"version": "1.0.0", "assets": {asset: ent}}, indent=2) + "\n"
    body = text if text is not None else json.dumps(_census_with(ms, asset=asset))
    w.raw[CFILE] = body
    w.raw["platform/scripts/governance/carriage_d1.py"] = (HERE.parent / "carriage_d1.py").read_text(encoding="utf-8")
    for k, v in (extra_files or {}).items():
        w.raw[k] = v
    digest = sha(body.encode("utf-8"))
    for c in crits:
        e = ac.CRITERION_REGISTRY[c]
        r = f"{c}#measured:no-prose"
        w.certs.append(cert(asset, c, "N/A", detector=e["detector"], layer="L0", revision=e["revision"], gate="Narr",
                            na=dict(rule_id=r, decision_id=ac.NA_RULE_DECISIONS[r], basis="measured_cause", cause="no-prose", facts=None),
                            evidence=dict(census_run_id=RUN_ID, census_file=CFILE, census_sha256=digest),
                            declarations_sha256=sha(w.declarations_text.encode())))
    w.disps.append(disp(asset, "keep"))
    w.commit()
    return w


def satisfied_narr(w, crits=(NCRIT,), asset=AID):
    state, _d, _g, _p = T._e63_load(w.last, str(w.repo))
    return [T._e63_satisfies(state.by_key[f"{asset}|gate|{c}"][-1], state, False) for c in crits]


def _full(d1rec):
    return _ms(d1rec)


def test_the_reader_counts_a_coupled_narr_na_only_while_the_census_at_the_ref_reads_carr_d1_pass(tmp_path):
    assert satisfied_narr(nworld(tmp_path / "ok", _full(_d1()))) == [True]
    assert satisfied_narr(nworld(tmp_path / "partial", _full(_d1(rows=_one_word_off())))) == [False]
    assert satisfied_narr(nworld(tmp_path / "unsourced", _full(_d1(state="unsourced")))) == [False]
    assert satisfied_narr(nworld(tmp_path / "refuted", _full(_d1(state="refuted")))) == [False]
    assert satisfied_narr(nworld(tmp_path / "absent", _full(None))) == [False]
    assert satisfied_narr(nworld(tmp_path / "bare", _full(dict(v=PASS, measured="x", citation_state="sourced_ocr_unverified")))) == [False]
    assert satisfied_narr(nworld(tmp_path / "forged_fail", _full(dict(_d1(), v=FAIL)))) == [False]


def test_the_reader_refuses_a_stripped_block_a_missing_census_and_a_d1_that_never_graded_the_column(tmp_path):
    stripped = _ms(_d1(), coupled=False)
    assert satisfied_narr(nworld(tmp_path / "stripped", stripped)) == [False]
    spec = copy.deepcopy(SPEC)
    spec["extra_fields"] = [x for x in spec["extra_fields"] if x["column"] != "affliction_condition"]
    assert satisfied_narr(nworld(tmp_path / "ungraded", _full(_d1(spec=spec)))) == [False]
    w = nworld(tmp_path / "nocensus", _full(_d1()), text=json.dumps(_census_with(_full(_d1()))))
    w.raw[CFILE] = None                                                       # the census file the certificate cites is not at the ref
    w.commit()
    assert satisfied_narr(w) == [False]
    wrong = nworld(tmp_path / "revision", _full(_d1()), text=json.dumps(rd.census_obj(_full(_d1()), asset=AID, layer="L0", revision=ac.REGISTRY_REVISION - 1)))
    assert satisfied_narr(wrong) == [False]
    badfp = nworld(tmp_path / "fingerprint", _full(_d1()), text=json.dumps(rd.census_obj(_full(_d1()), asset=AID, layer="L0", fingerprint="0" * 64)))
    assert satisfied_narr(badfp) == [False]


def test_the_reader_fails_closed_on_a_ref_whose_census_has_no_guard_and_leaves_an_uncoupled_declaration_alone(tmp_path):
    old = rd.CENSUS_TEXT.replace("def narr_coupling_problem(", "def _renamed_narr_coupling_problem(")
    assert satisfied_narr(nworld(tmp_path / "noguard", _full(_d1()), census_src=old)) == [False]
    inert = rd.CENSUS_TEXT.replace('    blk = meas.get("prose_coupling")\n    fcp = facts.get', '    return None\n    blk = meas.get("prose_coupling")\n    fcp = facts.get')
    assert inert != rd.CENSUS_TEXT
    assert satisfied_narr(nworld(tmp_path / "inert_guard", _full(_d1(rows=_one_word_off())), census_src=inert)) == [False]       # a ref census whose guard never refuses: the reader's own D1 PASS requirement holds
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}               # a [] declaration with NO carriage check (bg_yogas shape): the declared rule alone decides, exactly as before
    nocar = {"prose_fields": [], "evidence": ENTRY["evidence"]}
    # the stand-in is an asset that is NOT in PROSE_COUPLING_REQUIRED (bg_yogas): since the required-coupling pin the latta's own id with this entry is the double deletion, tested below
    assert "bg_yogas" not in ac.PROSE_COUPLING_REQUIRED
    assert satisfied_narr(nworld(tmp_path / "nocarriage", plain, entry=nocar, asset="bg_yogas"), asset="bg_yogas") == [True]
    assert satisfied_narr(nworld(tmp_path / "nocarriage_nocensus", plain, entry=nocar, text="{}", asset="bg_yogas"), asset="bg_yogas") == [True]


def test_F1_the_reader_refuses_a_ref_declaration_that_is_empty_prose_on_a_d1_carriage_without_its_coupling(tmp_path):
    """Delete the prose_coupling block, keep prose_fields [] and the D1 carriage: the declaration at the ref is refused (with a census that records a plain N/A, with the full
    record and a D1 PASS, and with no census at all): never counted."""
    stripped = {k: v for k, v in ENTRY.items() if k != "prose_coupling"}
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}
    assert satisfied_narr(nworld(tmp_path / "plain", plain, entry=stripped)) == [False]
    assert satisfied_narr(nworld(tmp_path / "pass", _full(_d1()), entry=stripped)) == [False]
    assert satisfied_narr(nworld(tmp_path / "nocensus", plain, entry=stripped, text="{}")) == [False]
    assert satisfied_narr(nworld(tmp_path / "coupled", _full(_d1()))) == [True]            # the committed (coupled) entry still counts


def test_F5_a_driver_error_at_the_ref_fails_closed(tmp_path):
    boom = rd.CENSUS_TEXT.replace('    blk = meas.get("prose_coupling")\n    fcp = facts.get', '    raise RuntimeError("boom")\n    blk = meas.get("prose_coupling")\n    fcp = facts.get')
    assert boom != rd.CENSUS_TEXT
    assert satisfied_narr(nworld(tmp_path / "boom", _full(_d1()), census_src=boom)) == [False]


def test_F5_the_reader_cache_is_keyed_by_the_request_two_criteria_of_one_ref_do_not_share_an_answer(tmp_path):
    ms = _full(_d1())
    ms["Narr.lint"] = dict(v=NO_DET, measured="NO_DETECTOR - this record is not an N/A")             # same ref, same census, same asset: only the criterion differs
    ms["Narr.lint"].pop("prose_coupling", None)
    w = nworld(tmp_path / "two", ms, crits=("Narr.agree", "Narr.lint"))
    assert satisfied_narr(w, ("Narr.agree", "Narr.lint")) == [True, False]
    T._E63_NARR_CACHE.clear()
    assert satisfied_narr(w, ("Narr.lint", "Narr.agree")) == [False, True]


def test_the_reader_holds_no_copy_of_the_rule():
    src = (HERE.parents[3] / "00_ARCHITECTURE" / "control" / "asset_elevation_tracker.py").read_text(encoding="utf-8")
    block = src.split("_E63_NARR_DRIVER = ", 1)[1].split("def _e63_parse_certs", 1)[0]
    assert "narr_coupling_problem" in block and "rollup_asset" in block                    # it asks the ref's own census: the rollup (which holds the rule)
    code = "\n".join(l for l in block.splitlines() if not l.lstrip().startswith("#"))
    for copy_of_the_rule in ("_check_contribution(", "prose_coverage", "d1_evidence_problem", '["result"]', '"rows"', "NULL-ok", "per-row"):
        assert copy_of_the_rule not in code, copy_of_the_rule


# ───────────────────────── Part 7: the pin ─────────────────────────

def test_the_registry_revision_and_the_four_narr_criteria_carry_the_new_declared_form():
    import test_e6_1_p1_registry_rollup as p1
    assert 16 in p1.PINNED_FINGERPRINTS and ac.REGISTRY_REVISION == max(p1.PINNED_FINGERPRINTS)     # the NARR-GUARD pin (16) is stacked under later pins
    for c in NARR:
        e = ac.CRITERION_REGISTRY[c]
        assert e["revision"] == (6 if c in ("Narr.lint", "Narr.agree") else 5) and "prose_coupling to carriage_d1" in e["applicability"] and "NARR-GUARD" in e["applicability"], c
    assert ac.NA_CAUSES["Narr.agree"] == ("no-prose", "no-table-no-prose") and all(f"{c}#measured:no-prose" in ac.NA_RULE_DECISIONS for c in NARR)
    head, tail = pathlib.Path(ac.__file__).read_text(encoding="utf-8").split(f"REGISTRY_REVISION = {ac.REGISTRY_REVISION}", 1)
    note = tail.split("\n", 1)[0]
    assert note[:200].lstrip(" #").startswith(f"{ac.REGISTRY_REVISION} (provisional): ") and "16 (provisional): NARR-GUARD" in head     # the leading note is the current revision's; the 16 note is carried


@pytest.mark.parametrize("bad", [["effect"], {"a": 1}, 7, None])
def test_a_non_string_extra_field_column_is_a_spec_error_never_an_unhashable_crash(bad):
    """Re-review L1: `ef.get("column") in RESULT_KEYS` raised TypeError for a list/dict column (it was a SpecError before the collision check)."""
    spec = json.loads(json.dumps(SPEC))
    spec["extra_fields"] = list(spec.get("extra_fields", [])) + [{"column": bad, "kind": "passage_text"}]
    with pytest.raises(d1.SpecError):
        d1.validate_spec(spec, "x")
