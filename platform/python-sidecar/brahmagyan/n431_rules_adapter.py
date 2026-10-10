"""brahmagyan.n431_rules_adapter: the pinned ADAPTER the census (SS N-431) runs in its parser sandbox to re-derive `sutravali_rules` (bg_rules).

The sandbox calls `run_chunk(item)` once per source chunk with ONE JSON dict `{"chunk": {id, text_id, verse_ref, content_en, ...}, "valid_text_ids": [text_id, ...]}` and serialises
the return value. This function is the glue between that contract and the real parser `l0_rules.extract_rules_from_chunk(chunk, valid_text_ids, ...)` (a generator), and it does
exactly what `l0_rules.seed_rules` does to the generator's output BEFORE a row reaches the table, so that the rows returned here are comparable to the stored ones:

  seed_rules (the writer)                                                    run_chunk (this adapter)
  chunk dict {id, text_id, verse_ref, content_en} from classical_text_chunks   the same four keys of item["chunk"] (any other key is dropped; a missing one raises)
  valid_text_ids = {DISTINCT text_id of classical_text_chunks}                 set(item["valid_text_ids"]) (the census reads the same DISTINCT list)
  extract_rules_from_chunk(chunk, valid_text_ids, <two optional counters>)     the same call, counters left at their defaults (they only count, they never change a row)
  row.pop("_quality"); skip the row when quality < QUALITY_THRESHOLD_LIVE      the same threshold (the l0_rules constant, not a copy) applied here; "_quality" is not returned
  FK nulling of yoga_canonical_id / dasha_system_id against the catalog tables NOT here (this module has no database): the census applies it from the declaration (`null_unless_in`)
  INSERT ... ON CONFLICT (rule_id) DO NOTHING (first chunk in order wins)      NOT here: the census applies it (`duplicate_policy: first_wins`) over the writer's chunk order
  created_at = now()                                                           not returned; the census ignores the column (`ignore_columns: [created_at]`)

The rows returned carry exactly the stored columns the parser produces: rule_id, text_id, verse_ref, antecedent_jsonb, predicate_jsonb, prediction_jsonb (JSON TEXT, as the parser yields
them; the table holds jsonb, so the census declares them `json_columns` and compares parsed JSON), confidence, quality_score (numbers), extracted_by, extraction_pass_log (JSON text),
yoga_canonical_id, dasha_system_id (text or None), transit_marker (bool). Because the threshold is applied here, the declaration carries no `keep_when`.

Pure and deterministic: no database, network, clock, randomness or file access (the parser's uuid5 ids, regexes and its import-time read of l0_semantic_release_v1.json are the whole of it).
This file is part of the code whose behaviour is certified, so it is pinned (sha256) in the declaration together with l0_rules.py and its import closure.
"""
from __future__ import annotations

from brahmagyan.l0_rules import QUALITY_THRESHOLD_LIVE, extract_rules_from_chunk

# The keys seed_rules hands the parser for each chunk (its SELECT list). Nothing else of the chunk row reaches the parser.
CHUNK_KEYS = ("id", "text_id", "verse_ref", "content_en")


def run_chunk(item):
    chunk = {k: item["chunk"][k] for k in CHUNK_KEYS}
    valid_text_ids = set(item["valid_text_ids"])
    rows = []
    for row in extract_rules_from_chunk(chunk, valid_text_ids):
        quality = row["_quality"]
        if quality < QUALITY_THRESHOLD_LIVE:
            continue
        rows.append({k: v for k, v in row.items() if k != "_quality"})
    return rows
