"""bg_rules: a match whose consequence has no word character is not a rule (census run A, Narr.agree: 8 stored rules read blank).

`_extract_result_clause` returns "" when the trigger word ends the chunk (the sentence continues in the next chunk) and a run of punctuation or dashes
when the clause is only OCR debris. Before the fix such a match scored 0.8 and was stored with prediction.result == "" or "——". The two REAL chunks
below (saravali PG83:C1 ends with "...the native will be"; brihat_samhita PG960:C1 is an index page whose clause is a dash run) are the live cases;
their former rule ids are pinned so the test says exactly which rules are gone. No database: extract_rules_from_chunk is a pure generator.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from brahmagyan import l0_rules
from brahmagyan.l0_rules import extract_rules_from_chunk

_FIX = Path(__file__).resolve().parent / "fixtures" / "bg_rules_empty_result"
VALID = {"saravali", "brihat_samhita", "bphs"}

# rule ids that census run A found stored with a blank/dash-only result (live sutravali_rules, 2026-10-11)
GONE_FROM_SARAVALI = {"1e821404-30d3-5136-a5bc-e1e845671363"}
GONE_FROM_BRIHAT_SAMHITA = {"c5505bf1-2f7d-5c97-af48-5503113ab74c"}


def _load(name: str) -> dict:
    return json.loads((_FIX / name).read_text())


def _rules(chunk: dict) -> list[dict]:
    return list(extract_rules_from_chunk(chunk, VALID))


def _result(rule: dict) -> str:
    p = rule["prediction_jsonb"]
    return (json.loads(p) if isinstance(p, str) else p)["result"]


def _chunk(text: str, verse_ref: str = "1.1") -> dict:
    return {"id": str(uuid.uuid4()), "text_id": "bphs", "verse_ref": verse_ref, "content_en": text}


def test_real_chunk_ending_mid_sentence_yields_no_empty_rule():
    rules = _rules(_load("saravali_pg83_c1.json"))
    assert rules, "the chunk still carries real rules"
    ids = {str(r["rule_id"]) for r in rules}
    assert not (ids & GONE_FROM_SARAVALI)
    assert all(re.search(r"\w", _result(r)) for r in rules)


def test_real_index_page_with_dash_run_yields_no_dash_only_rule():
    rules = _rules(_load("brihat_samhita_pg960_c1.json"))
    ids = {str(r["rule_id"]) for r in rules}
    assert not (ids & GONE_FROM_BRIHAT_SAMHITA)
    assert all(re.search(r"\w", _result(r)) for r in rules)


def test_trigger_word_as_last_token_yields_nothing():
    assert _rules(_chunk("Jupiter in the fifth house gives")) == []


def test_punctuation_only_result_yields_nothing():
    assert _rules(_chunk("Saturn in the 7th house gives. ")) == []


def test_a_real_consequence_is_still_kept():
    rules = _rules(_chunk("Jupiter in the seventh house gives wealth and learning to the native."))
    assert len(rules) >= 1
    assert all(re.search(r"\w", _result(r)) for r in rules)
    assert any("wealth" in _result(r) for r in rules)


def test_the_guard_is_in_the_shared_generator_not_one_pattern():
    src = Path(l0_rules.__file__).read_text()
    assert 'if not re.search(r"\\w", str(prediction.get("result") or "")):' in src
