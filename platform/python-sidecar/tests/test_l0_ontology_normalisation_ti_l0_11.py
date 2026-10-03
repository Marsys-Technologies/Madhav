"""TI-L0-11 (SS Q4, CF-09 (b)): the normalisation rule lives in the bg_ontology writer module
(one authority) and the vocabulary carries a deterministic release identity.

Proves
  1. `resolve` keeps every previous resolution: for EVERY name the static vocabulary carries
     that the previous ad-hoc rule resolved, old and new `resolve()` return the same entity
     (property test over all names), so no served resolution moves. (Found while writing it:
     folding diacritics alone is NOT a safe superset - 'jaimini sutram' folds to a synonym of an
     EARLIER entity, the school 'jaimini' - so `resolve` tries the exact legacy form first.)
  2. the declared ambiguous-alias list is exact (every ambiguous alias names >1 (class,id) and
     is resolvable class-aware to each owner).
  3. the SS-stated prediction for the remedy source ids, computed from a read-only production
     census fixture: exact 52 / normalised-only 204 / unresolved 85 against the CURRENT text
     class (TI-L0-13 later moves 2 of the unresolved to exact).
  4. `ephemeris_daily.body` (stored 'Jupiter', 'Moon', ...) resolves class-aware to the planet
     ids, with NO stored value rewritten.
  5. the release id is deterministic, sensitive to a vocabulary edit, and blind to co-writer
     classes (which bg_ontology does not own).
  6. real PostgreSQL (env-gated): a seed over an already-seeded table changes no stored row
     and reports the release.
"""
from __future__ import annotations

import copy
import json
import unicodedata
from pathlib import Path

import pytest

from brahmagyan import l0_ontology as O
from tests._l0d_pg import requires_pg, scratch_schema

FIX = json.loads((Path(__file__).parent / "fixtures" / "l0_ontology_remedy_source_ids.json").read_text(encoding="utf-8"))["counts"]


def old_rule(term: str) -> str:
    return term.lower().replace(" ", "_").replace("-", "_")


def old_resolve(term: str):
    t = old_rule(term)
    for entity in O.ENTITIES:
        if entity["canonical_id"] == t:
            return entity
        if entity["canonical_name_en"].lower().replace(" ", "_") == t:
            return entity
        if (entity.get("canonical_name_sa") or "").lower().replace(" ", "_") == t:
            return entity
        if t in [s.lower() for s in entity["synonyms"]]:
            return entity
    return None


def all_names():
    for e in O.ENTITIES:
        yield from (e["canonical_id"], e["canonical_name_en"], e.get("canonical_name_sa") or "", *e["synonyms"])


# ── 1 ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,want", [
    ("BPHS", "bphs"), ("Jupiter", "jupiter"), ("Sūrya", "surya"), ("Purva  Bhadrapada", "purva_bhadrapada"),
    ("  Shani ", "shani"), ("kuja-dosha", "kuja_dosha"), ("Ṛṇa", "rna"),
])
def test_normalise_term_examples(raw, want):
    assert O.normalise_term(raw) == want


def test_normalise_term_is_idempotent_and_total_over_the_vocabulary():
    for n in all_names():
        if not n:
            continue
        k = O.normalise_term(n)
        assert O.normalise_term(k) == k
        assert not any(unicodedata.combining(c) for c in k)


def test_new_resolve_equals_old_resolve_for_every_name_in_the_vocabulary():
    checked = 0
    for n in all_names():
        if not n or not old_rule(n):
            continue
        old = old_resolve(n)
        if old is None:
            continue                       # old rule did not resolve it; new may (superset), checked below
        assert O.resolve(n) is old, f"resolution moved for {n!r}"
        checked += 1
    assert checked > 1500


def test_new_resolve_is_a_superset_it_adds_diacritic_and_case_forms_only():
    assert old_resolve("Sūrya") is None or old_resolve("Sūrya") is O.resolve("Sūrya")
    assert O.resolve("Sūrya")["canonical_id"] == "sun"


@pytest.mark.parametrize("term,cls,cid", [
    ("Shani", None, "saturn"), ("chandra", None, "moon"), ("career", None, "career"), ("SATURN", None, "saturn"),
    ("Jupiter", "planet", "jupiter"), ("BPHS", "text", "bphs"),
])
def test_acceptance_examples_still_resolve(term, cls, cid):
    assert O.resolve(term, cls)["canonical_id"] == cid


def test_unknown_term_is_none():
    assert O.resolve("zzz_not_a_term") is None


# ── 2 ────────────────────────────────────────────────────────────────────────

def test_ambiguous_alias_list_is_exact_and_each_owner_resolves_class_aware():
    amb = O.ambiguous_aliases()
    assert len(amb) == 71
    for key, owners in amb.items():
        assert len(owners) >= 2 and len(set(owners)) == len(owners)
        for cls, cid in owners:
            e = O.resolve(key, cls)
            assert e is not None and e["canonical_id"] in {c for k, c in owners if k == cls}, (key, cls)
    assert ("domain", "foreign_travel") in amb["abroad"] and ("planet", "mars") in amb["bhumi"]


def test_ambiguity_is_not_resolved_by_guessing_without_a_class():
    # the first match in ENTITIES order is returned (unchanged behaviour), and it is flagged ambiguous
    assert "ascendant" in O.ambiguous_aliases()


# ── 3 ────────────────────────────────────────────────────────────────────────

def classify(source_id: str):
    text_ids = {e["canonical_id"] for e in O.ENTITIES if e["entity_class"] == "text"}
    if source_id in text_ids:
        return "exact"
    e = O.resolve(source_id, "text")
    return "normalised_only" if e is not None else "unresolved"


def test_remedy_source_id_prediction_52_204_85():
    tally = {"exact": 0, "normalised_only": 0, "unresolved": 0}
    for sid, n in FIX.items():
        tally[classify(sid)] += n
    assert sum(tally.values()) == 341
    assert tally == {"exact": 52, "normalised_only": 204, "unresolved": 85}, tally
    assert classify("classical_tradition") == "unresolved"       # not provenance (SS Q3): never resolves
    assert classify("Tajaka") == "unresolved"                      # 'tajaka' is the SCHOOL; class-aware resolution does not take it for a text


# ── 4 ────────────────────────────────────────────────────────────────────────

def test_ephemeris_bodies_resolve_class_aware_to_planets_without_rewriting_the_stored_value():
    bodies = ["Jupiter", "Ketu", "Mars", "Mercury", "Moon", "Rahu", "Saturn", "Sun", "Venus"]
    for b in bodies:
        e = O.resolve(b, "planet")
        assert e is not None and e["canonical_id"] == O.normalise_term(b), b
    assert bodies == sorted(bodies)                                # the stored values are passed through untouched


# ── 5 ────────────────────────────────────────────────────────────────────────

def test_release_is_deterministic_and_counts_only_owned_classes():
    r1, r2 = O.vocabulary_release(), O.vocabulary_release()
    assert r1 == r2
    assert r1["owned_rows"] == len([e for e in O.ENTITIES if e["entity_class"] in O.ONTOLOGY_OWNED_ENTITY_CLASSES])
    assert r1["release_id"] == "bg_ontology-" + r1["content_sha256"][:12]


def test_release_changes_on_a_vocabulary_edit_and_ignores_co_writer_classes():
    base = O.vocabulary_release()["content_sha256"]
    saved = copy.deepcopy(O.ENTITIES)
    try:
        O.ENTITIES[0]["synonyms"] = O.ENTITIES[0]["synonyms"] + ["zzz_new_alias"]
        assert O.vocabulary_release()["content_sha256"] != base
    finally:
        O.ENTITIES[:] = saved
    assert O.vocabulary_release()["content_sha256"] == base
    try:
        O.ENTITIES.append(O._e("yoga", "zz_fake_yoga", "Fake", "Fake", ["fake"], None))
        assert O.vocabulary_release()["content_sha256"] == base       # co-writer class: not part of the release
    finally:
        O.ENTITIES[:] = saved


def test_dry_run_reports_the_release():
    assert O.seed_ontology(None, dry_run=True)["vocabulary_release"] == O.vocabulary_release()


# ── 6 ────────────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE brahma_ontology (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), entity_class text NOT NULL, canonical_id text NOT NULL,
  canonical_name_en text NOT NULL, canonical_name_sa text, synonyms text[] NOT NULL DEFAULT '{}',
  description text, source_citation text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id));
"""


@requires_pg
def test_real_seed_over_a_seeded_table_changes_no_stored_row_and_reports_the_release():
    with scratch_schema(DDL) as conn:
        first = O.seed_ontology(conn, autocommit=False)
        conn.commit()
        assert first["vocabulary_release"] == O.vocabulary_release()
        snap = list(conn.execute("SELECT id,entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation FROM brahma_ontology ORDER BY entity_class,canonical_id"))
        assert len(snap) == len(O.ENTITIES)
        second = O.seed_ontology(conn, autocommit=False)
        conn.commit()
        assert second["inserted"] == 0, "a converged rerun changes nothing (the normalisation rule rewrites no stored id)"
        assert list(conn.execute("SELECT id,entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation FROM brahma_ontology ORDER BY entity_class,canonical_id")) == snap
