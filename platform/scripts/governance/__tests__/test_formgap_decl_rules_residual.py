"""test_formgap_decl_rules_residual.py: bg_rules declares its writer-composed description as prose BESIDE corpus_derived (SS N-455 / N-457), and what that does and does not release.

bg_rules writes `sutravali_rules` by deterministic regex extraction over the `classical_text_chunks` corpus (brahmagyan/l0_rules.py seed_rules, extracted_by python_regex_v2). Every string leaf of the rows is
a slice of the verse, a copied identifier or a fixed label EXCEPT `predicate_jsonb.description`, which each of the 27 extractors composes by f-string from the matched tokens (SS N-455). That column is the
asset's prose and is declared (`prose_fields`), BESIDE the `corpus_derived` reproducibility form (mode 2, SS N-457): a corpus_derived PASS releases Narr.agree and Narr.checkable ONLY; Narr.fidelity_test is
earned by the declared golden tests, Narr.lint by `lint_none`, Null.* by the writer scan and the live row counts. N-210's earlier residual (undeclared, every cell NO_DETECTOR) is superseded.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

DECLS = ac.load_asset_declarations()
PROSE = "predicate_jsonb.$.description"
L0 = "platform/python-sidecar/brahmagyan/l0_rules.py"


def test_bg_rules_declares_the_composed_description_as_prose_beside_corpus_derived_and_no_other_form():
    e = DECLS["bg_rules"]
    assert e["prose_fields"] == [PROSE] and e["evidence_kind"] == "writer"
    assert e["corpus_derived"] is not None and ac.corpus_derived_mode(e) == 2 and ac.corpus_derived_applies(e) and ac.corpus_derived_problem(e) is None
    assert "prose_none" not in e and "curated_corpus" not in e and "writer_constant_phrases" not in e and "static_read" not in e.get("prose_none", {})
    assert e["carriage"]["nature"] == "unverified_transcription"           # the D1 carriage is the existing honest statement about these rows
    assert ac.lint_none_problem(e) is None and "verbatim" not in e["lint_none"]["why"] and "verbatim" not in e["corpus_derived"]["why"]


def test_the_corpus_derived_pins_are_exactly_the_committed_manifest():
    man = json.loads((HERE.parent / "pins/bg_rules_parser_pins_v1.json").read_text(encoding="utf-8"))["pinned_files"]
    assert DECLS["bg_rules"]["corpus_derived"]["parser"]["pinned_files"] == [dict(path=p["path"], sha256=p["sha256"]) for p in man] and len(man) == 6


def test_every_cite_of_the_prose_evidence_is_a_line_of_the_writer_that_holds_what_the_text_says():
    ev = DECLS["bg_rules"]["evidence"]["prose_fields"]
    lines = (ac.ROOT / L0).read_text(encoding="utf-8").split("\n")
    import re
    cites = sorted({int(n) for n in re.findall(re.escape(L0) + r":(\d+)", ev)})
    assert len(cites) >= 10 and cites[-1] <= len(lines)
    for needle, what in (("def _graha_label", "_graha_label"), ('"description": f"{_graha_label(planet)} in house {house}"', "planet_in_house"), ('target_desc = "target unresolved"', "target unresolved"),
                         ('"house or sign unresolved"', "house or sign unresolved"), ('json.dumps(result["predicate"])', "json.dumps"), ("INSERT INTO sutravali_rules (", "INSERT")):
        hit = [i + 1 for i, ln in enumerate(lines) if needle in ln]
        assert len(hit) == 1 and hit[0] in cites, (what, hit)


def test_with_no_live_read_and_no_test_world_nothing_reads_pass_or_na():
    got = ac.prose_checks("bg_rules", DECLS["bg_rules"], dict(table="sutravali_rules", own={}, tests=[], vocabulary=set(), counts=None, paths=[], written=None))
    assert sorted(got) == sorted(ac.NARR_CHECKS + ac.NULL_CHECKS)
    assert all(v["v"] not in (ac.PASS, ac.NA) for v in got.values()), {c: v["v"] for c, v in got.items()}


def test_the_declared_golden_tests_are_verified_from_the_real_test_source():
    """Narr.fidelity_test is earned through the normal fidelity_tests machinery (golden_test_scan): both declared tests call an extractor directly and assert its description equal to a literal sentence."""
    e = DECLS["bg_rules"]
    assert e["fidelity_tests"] and all(d["covers"] == [PROSE] for d in e["fidelity_tests"])
    r = ac.narr_fidelity_scan(e["prose_fields"], e["evidence"]["prose_fields"], ac.python_tests(), e["fidelity_tests"], ac.ROOT)
    assert r["v"] == ac.PASS, r["measured"]


def test_the_extractor_reads_only_database_text_so_a_pin_has_nothing_to_pin_against():
    src = (ac.ROOT / "platform/python-sidecar/brahmagyan/l0_rules.py").read_text(encoding="utf-8")
    assert "classical_text_chunks" in src and "python_regex_v2" in src
    seed = (ac.ROOT / "platform/python-sidecar/pipeline/orchestrator/writers/bg_rules.py").read_text(encoding="utf-8")
    assert "deterministic regex extraction" in seed and "classical_text_chunks" in seed
