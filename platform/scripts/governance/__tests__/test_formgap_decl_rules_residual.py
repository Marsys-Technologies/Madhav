"""test_formgap_decl_rules_residual.py: bg_rules stays UNDECLARED, and why (SS N-210).

bg_rules writes `sutravali_rules` by deterministic regex extraction over the `classical_text_chunks` corpus (brahmagyan/l0_rules.py seed_rules, extracted_by python_regex_v2). The rows are therefore a
function of a corpus that lives in the database only: no committed file holds the verses the extractor reads, so a sentence column of the output cannot be pinned (curated_corpus), closed (a vocabulary)
or transcribed (a seed) by any form the engine has. The one detector that would measure the claim "this table is what the extractor produces from the corpus" is a REPRODUCIBILITY detector (re-run the
extractor over the corpus and compare the rows), which needs the whole corpus text read through the census role and the 27 extraction patterns run over it on every census: it was not built in the
review-fix pass. Until it is, the honest declaration is the residual: prose_fields stays null, every Narr / Null cell reads NO_DETECTOR, and nothing here lets a PASS or an N/A through.
Residual (named): bg_rules is derived from a DB-only corpus; the reproducibility detector is pending.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

DECLS = ac.load_asset_declarations()
RESIDUAL = "bg_rules is derived from a DB-only corpus; the reproducibility detector is pending"


def test_bg_rules_is_undeclared_so_no_form_can_release_it():
    e = DECLS["bg_rules"]
    assert e["prose_fields"] is None and "prose_none" not in e and "curated_corpus" not in e and "static_read" not in e.get("prose_none", {})
    assert e["carriage"]["nature"] == "unverified_transcription"           # the D1 carriage is the existing honest statement about these rows


def test_bg_rules_reads_no_detector_on_all_six_never_na_or_pass():
    got = ac.prose_checks("bg_rules", DECLS["bg_rules"], dict(table="sutravali_rules", own={}, tests=[], vocabulary=set(), counts=None, paths=[], written=None))
    assert sorted(got) == sorted(ac.NARR_CHECKS + ac.NULL_CHECKS)
    assert all(v["v"] == ac.NO_DET and "undeclared" in v["measured"] for v in got.values()), {c: v["v"] for c, v in got.items()}


def test_the_extractor_reads_only_database_text_so_a_pin_has_nothing_to_pin_against():
    src = (ac.ROOT / "platform/python-sidecar/brahmagyan/l0_rules.py").read_text(encoding="utf-8")
    assert "classical_text_chunks" in src and "python_regex_v2" in src
    seed = (ac.ROOT / "platform/python-sidecar/pipeline/orchestrator/writers/bg_rules.py").read_text(encoding="utf-8")
    assert "deterministic regex extraction" in seed and "classical_text_chunks" in seed
