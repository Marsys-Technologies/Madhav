"""
brahmagyan.l0_ontology_texts - the ontology `text` class derived from the corpus manifest
(TI-L0-13, SS Q4 / CF-09 (c)). Pure functions over an entity list; no import of l0_ontology (no cycle).

The `text` class and the corpus (`brahmagyan.l0_texts.TEXTS`, the manifest bg_texts builds the corpus
from, 15 texts) had drifted by 3 in each direction (corpus-only: bhrigu_nandi_nadi, bphs_jaimini,
nadi_navamsa_patel; ontology-only: bhrigu_samhita, jaimini_sutram, lal_kitab_text). Rules, in order:
  1. every manifest text is a text entity: `derive_missing_text_entities` adds the ones the hand-kept
     rows in l0_ontology.py lack, taking EVERY field from the manifest (name, Sanskrit title, author,
     school, and its own `source_citation` - not the BPHS placeholder);
  2. the 12 texts that already existed in both places keep their display fields VERBATIM (they stay as
     literal rows in l0_ontology.py; golden test) - no served name, synonym or description moves;
  3. an ontology-only id stays ONLY if a consumer exists (referrer census, see the wave plan):
     `jaimini_sutram` is cited as text_id by 12 yoga and 5 dasha_system catalogue rows (+ migration 465)
     and is a live classical_texts row (its chunks live under `bphs_jaimini`). `bhrigu_samhita` and
     `lal_kitab_text` have no consumer anywhere and are not corpus texts (l0_texts.py: "Dropped: lal_kitab
     ... bhrigu_samhita (no defensible edition)"), so they are no longer emitted and the writer's
     owned-class sweep removes them;
  4. `assert_text_class_matches_manifest` fails at import if the class and the manifest drift again.
This is a separate module because `asset_declarations.json` pins evidence lines in l0_ontology.py and
declares that module composes only ordinal labels; the description string built here is not narration.
"""
from __future__ import annotations

from typing import Any

TEXT_ONTOLOGY_ONLY_KEPT: frozenset[str] = frozenset({"jaimini_sutram"})


def _corpus(corpus_texts: list[dict] | None) -> list[dict]:
    if corpus_texts is not None:
        return corpus_texts
    from brahmagyan.l0_texts import TEXTS
    return TEXTS


def derive_missing_text_entities(entities: list[dict], corpus_texts: list[dict] | None = None) -> list[dict]:
    """Entities for the manifest texts that `entities` has no `text` row for (pure)."""
    have = {e["canonical_id"] for e in entities if e["entity_class"] == "text"}
    out: list[dict] = []
    for t in _corpus(corpus_texts):
        cid = t["text_id"]
        if cid in have:
            continue
        synonyms: list[str] = []
        for cand in (t["title_en"].lower(), cid.replace("_", " ")):
            if cand not in synonyms:
                synonyms.append(cand)
        out.append({
            "entity_class": "text",
            "canonical_id": cid,
            "canonical_name_en": t["title_en"],
            "canonical_name_sa": t.get("title_sa"),
            "synonyms": synonyms,
            "description": t["author"] + "; " + t["school"] + " school",
            "source_citation": t["source_citation"],
        })
    return out


def text_class_drift(entities: list[dict], corpus_texts: list[dict] | None = None) -> dict[str, Any]:
    ont = {e["canonical_id"] for e in entities if e["entity_class"] == "text"}
    corp = {t["text_id"] for t in _corpus(corpus_texts)}
    return {"corpus_only": sorted(corp - ont), "ontology_only_unkept": sorted(ont - corp - TEXT_ONTOLOGY_ONLY_KEPT)}


def assert_text_class_matches_manifest(entities: list[dict], corpus_texts: list[dict] | None = None) -> None:
    drift = text_class_drift(entities, corpus_texts)
    if drift["corpus_only"] or drift["ontology_only_unkept"]:
        raise ValueError(
            "ontology text class drifted from the corpus manifest (brahmagyan.l0_texts.TEXTS): "
            + repr(drift) + "; add the text to the manifest, or declare the ontology-only id in "
            "TEXT_ONTOLOGY_ONLY_KEPT with its consumer"
        )
