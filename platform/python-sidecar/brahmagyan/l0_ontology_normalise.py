"""
brahmagyan.l0_ontology_normalise - the ONE normalisation rule of the ontology (SS Q4 / CF-09 (b), TI-L0-11)
and the pure helpers built on it: two-tier resolution, the ambiguous-alias list, the vocabulary release.

bg_ontology is the identity authority; the rule lives with its writer module (`brahmagyan.l0_ontology`
delegates here) and consumers - bg_remedies source ids, ephemeris_daily.body, resolve_entity - resolve
THROUGH it; no stored id is rewritten. Everything takes the entity list as a parameter (pure; no import
of l0_ontology, so no cycle). It is a separate module because `asset_declarations.json` pins evidence lines
in `l0_ontology.py` and declares that module composes no text: this code builds strings (a fold, a digest
label) and none of it is narration.

The rule: Unicode NFKD, combining marks removed (diacritic fold), case-fold, strip, then every run of
whitespace / hyphens becomes one underscore.
    'BPHS' -> 'bphs'   'Jupiter' -> 'jupiter'   'Sūrya' -> 'surya'   'Purva Bhadrapada' -> 'purva_bhadrapada'
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

NORMALISATION_VERSION = "nfkd+fold+casefold+underscore-v1"


def normalise_term(term: str) -> str:
    folded = "".join(c for c in unicodedata.normalize("NFKD", term) if not unicodedata.combining(c))
    return re.sub(r"[\s\-]+", "_", folded.casefold().strip())


def entity_names(entity: dict) -> list[str]:
    return [n for n in (entity["canonical_id"], entity["canonical_name_en"],
                        entity.get("canonical_name_sa") or "", *entity["synonyms"]) if n]


def legacy_term(term: str) -> str:
    """The pre-centralisation rule applied to the LOOKUP term (lower, space -> _, hyphen -> _)."""
    return term.lower().replace(" ", "_").replace("-", "_")


def legacy_keys(entity: dict) -> set[str]:
    """The strings the pre-centralisation `resolve` compared a term against, field by field:
    canonical_id verbatim; name_en / name_sa lower-cased with spaces -> '_'; synonyms merely
    lower-cased (a synonym containing a space therefore never matched a lookup term, which
    always has its spaces replaced). Kept ONLY as the first precedence tier of `resolve`, so
    every term that resolved before resolves to the same entity; folding diacritics can
    otherwise hand a term to an EARLIER entity ('jaimini sutram' -> the school 'jaimini',
    whose synonym 'Jaimini Sūtram' folds to it) instead of the text 'jaimini_sutram'."""
    keys = {entity["canonical_id"],
            entity["canonical_name_en"].lower().replace(" ", "_"),
            (entity.get("canonical_name_sa") or "").lower().replace(" ", "_")}
    keys |= {s.lower() for s in entity["synonyms"]}
    keys.discard("")
    return keys


def build_indexes(entities: list[dict]) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    legacy: dict[str, list[int]] = {}
    folded: dict[str, list[int]] = {}
    for pos, entity in enumerate(entities):
        for key in legacy_keys(entity):
            legacy.setdefault(key, []).append(pos)
        for key in {normalise_term(n) for n in entity_names(entity)}:
            folded.setdefault(key, []).append(pos)
    return legacy, folded


def resolve_two_tier(entities: list[dict], term: str, entity_class: str | None = None) -> dict | None:
    legacy, folded = build_indexes(entities)
    for index, key in ((legacy, legacy_term(term)), (folded, normalise_term(term))):
        for pos in index.get(key, []):
            if entity_class is None or entities[pos]["entity_class"] == entity_class:
                return entities[pos]
    return None


def ambiguous_aliases(entities: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """normalised alias -> sorted [(entity_class, canonical_id), ...] for every alias that names
    MORE THAN ONE (class, id) in the vocabulary. The declared ambiguous-alias list: a consumer must
    pass an entity_class for these, never rely on the first match."""
    out: dict[str, list[tuple[str, str]]] = {}
    for key, positions in build_indexes(entities)[1].items():
        owners = sorted({(entities[p]["entity_class"], entities[p]["canonical_id"]) for p in positions})
        if len(owners) > 1:
            out[key] = owners
    return dict(sorted(out.items()))


def vocabulary_release(entities: list[dict], owned_classes: frozenset[str]) -> dict[str, Any]:
    """Content identity of the vocabulary bg_ontology OWNS (co-writer classes yoga / dosha /
    dasha_system are excluded: their rows come from sibling writers, so including them would make
    this asset's release depend on a writer it does not own). Deterministic; additive metadata -
    storing it is a separate, numbered migration (see the wave plan)."""
    rows = sorted(
        ([e["entity_class"], e["canonical_id"], e["canonical_name_en"], e.get("canonical_name_sa"),
          list(e["synonyms"]), e.get("description"), e["source_citation"]]
         for e in entities if e["entity_class"] in owned_classes),
        key=lambda r: (r[0], r[1]),
    )
    digest = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"release_id": "bg_ontology-" + digest[:12], "content_sha256": digest, "owned_rows": len(rows),
            "normalisation": NORMALISATION_VERSION}
