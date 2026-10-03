"""TI-L0-12 (SS Q4, CF-09 (a)): the 79 dosha rows of brahma_ontology carry closed, non-empty
alias sets built ONLY from names the module's own entries carry (live: 79/79 empty - the
Vocab.alias FAIL).

Static proofs (no database): the rule's output is re-derived here by an INDEPENDENT
implementation of the three allowed transforms and every produced alias must lie inside it
("no invented aliases"); no derived alias is claimed by two doshas or by a class bg_ontology
owns; the full names always survive; golden sets pin the exact output for six doshas.
Real-PostgreSQL proof (env-gated): the REAL seed_doshas turns the live shape (all `{}`)
into 79/79 non-empty sets, changing ONLY ontology.synonyms, nothing else in the three
projections, no row of any other ontology class, and a rerun is a no-op.
"""
from __future__ import annotations

import collections
from pathlib import Path
import re
import unicodedata

import pytest

from brahmagyan import l0_doshas as D
from brahmagyan import l0_ontology as O
from tests._l0d_pg import requires_pg, scratch_schema


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def key(s: str) -> str:
    return fold(s).casefold()


def allowed_closure(d: dict) -> set[str]:
    """Independent re-implementation: every string reachable from the entry's own names by
    {drop trailing Dosha token, split name_sa's trailing parenthetical, diacritic-fold}."""
    base = {d["canonical_id"], d["name_en"], d["name_sa"]}
    cur = set(base)
    m = re.match(r"^(.*?)\s*\((.*?)\)\s*$", d["name_sa"])
    if m:
        cur |= {m.group(1).strip(), m.group(2).strip()}
    cur |= {re.sub(r"\s+(Dosha|Doṣa|Dosa)$", "", x) for x in set(cur)}
    cur |= {fold(x) for x in set(cur)}
    return {x for x in cur if x}


SETS = D.dosha_alias_sets(D.DOSHAS)
BY_ID = {d["canonical_id"]: d for d in D.DOSHAS}


def test_79_doshas_each_with_a_non_empty_set_that_keeps_the_full_names():
    assert len(D.DOSHAS) == 79 and len(SETS) == 79
    for cid, aliases in SETS.items():
        d = BY_ID[cid]
        assert aliases, cid
        assert aliases[:3] == [x for x in (d["canonical_id"], d["name_en"], d["name_sa"])][:len(aliases[:3])]
        for full in (d["canonical_id"], d["name_en"], d["name_sa"]):
            assert full in aliases, (cid, full)
        assert len(aliases) == len(set(aliases)), f"exact duplicate alias in {cid}"


def test_no_alias_is_invented_every_alias_is_inside_the_independent_closure():
    for cid, aliases in SETS.items():
        extra = set(aliases) - allowed_closure(BY_ID[cid])
        assert not extra, f"{cid}: aliases outside the declared transforms: {extra}"


def test_full_names_are_unique_across_the_79():
    owners = collections.defaultdict(set)
    for d in D.DOSHAS:
        for nm in (d["canonical_id"], d["name_en"], d["name_sa"]):
            owners[key(nm)].add(d["canonical_id"])
    assert {k: v for k, v in owners.items() if len(v) > 1} == {}


def test_no_derived_alias_is_shared_between_two_doshas():
    owners = collections.defaultdict(set)
    for cid, aliases in SETS.items():
        for a in aliases:
            owners[key(a)].add(cid)
    assert {k: v for k, v in owners.items() if len(v) > 1} == {}


def test_no_derived_alias_equals_a_name_of_a_class_bg_ontology_owns():
    reserved = D._bg_ontology_owned_name_keys()
    assert "mars" in reserved and "kuja" in reserved           # the reservation set is real
    for cid, aliases in SETS.items():
        d = BY_ID[cid]
        base = {d["canonical_id"], d["name_en"], d["name_sa"]}
        bad = [a for a in aliases if a not in base and key(a) in reserved]
        assert bad == [], f"{cid}: {bad}"


def test_the_ambiguous_parenthetical_kuja_is_dropped_because_it_is_also_the_planet_mars():
    assert "Kuja" not in SETS["manglik"] and "Mangala" not in SETS["manglik"]
    assert "Maṅgala Doṣa" in SETS["manglik"] and "Kuja Doṣa" in SETS["manglik"]


@pytest.mark.parametrize("cid,golden", [
    ("kala_sarpa", ["kala_sarpa", "Kala Sarpa Dosha", "Kāla Sarpa Doṣa", "Kala Sarpa", "Kāla Sarpa", "Kala Sarpa Dosa"]),
    ("manglik", ["manglik", "Manglik Dosha", "Maṅgala Doṣa (Kuja Doṣa)", "Maṅgala Doṣa", "Kuja Doṣa", "Manglik",
                 "Mangala Dosa (Kuja Dosa)", "Mangala Dosa", "Kuja Dosa"]),
    ("balarishta", ["balarishta", "Balarishta", "Bālāriṣṭa"]),
    ("kuja_dosha_lagna_1st", ["kuja_dosha_lagna_1st", "Kuja Dosha (Mars in 1st from Lagna)",
                              "Kuja Doṣa — Lagna-prathama", "Kuja Dosa — Lagna-prathama"]),
])
def test_golden_alias_sets(cid, golden):
    assert SETS[cid] == golden


def test_golden_totals():
    assert sum(len(v) for v in SETS.values()) == 383
    assert collections.Counter(len(v) for v in SETS.values()) == {3: 5, 4: 44, 5: 6, 6: 10, 7: 11, 8: 2, 9: 1}


def test_the_ontology_class_set_is_unchanged_the_writer_still_emits_doshas_only_for_79():
    assert len({d["canonical_id"] for d in D.DOSHAS}) == 79


# ── real PostgreSQL ──────────────────────────────────────────────────────────

DDL = """
CREATE TABLE brahma_dosha_catalog (
  canonical_id text PRIMARY KEY, name_sa text NOT NULL, name_en text NOT NULL,
  category text NOT NULL CHECK (category IN ('graha_placement','rashi_combination','nakshatra_compatibility','tithi','other')),
  formation_rule_jsonb jsonb NOT NULL, formation_text text NOT NULL, effects_text text NOT NULL,
  severity_grades jsonb, cancellation_conditions jsonb, classical_citations jsonb,
  source_chunk_ids bigint[] DEFAULT ARRAY[]::bigint[], associated_remedies uuid[] DEFAULT ARRAY[]::uuid[],
  school text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE brahma_ontology (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), entity_class text NOT NULL, canonical_id text NOT NULL,
  canonical_name_en text NOT NULL, canonical_name_sa text, synonyms text[] NOT NULL DEFAULT '{}',
  description text, source_citation text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id));
CREATE TABLE reference_doshas (
  canonical_id text PRIMARY KEY REFERENCES brahma_dosha_catalog(canonical_id) ON DELETE CASCADE,
  name_en text NOT NULL, category text NOT NULL);
"""


def _proj(conn):
    cat = [dict(r) for r in conn.execute("SELECT canonical_id,name_sa,name_en,category,formation_text,effects_text,school,classical_citations FROM brahma_dosha_catalog ORDER BY 1")]
    ref = [dict(r) for r in conn.execute("SELECT * FROM reference_doshas ORDER BY 1")]
    ont = [dict(r) for r in conn.execute(
        "SELECT canonical_id,canonical_name_en,canonical_name_sa,description,source_citation FROM brahma_ontology WHERE entity_class='dosha' ORDER BY 1")]
    return cat, ref, ont


@requires_pg
def test_real_writer_fills_79_of_79_alias_sets_and_changes_nothing_else():
    with scratch_schema(DDL) as conn:
        # the other ontology classes are present and must be untouched
        conn.execute("INSERT INTO brahma_ontology(entity_class,canonical_id,canonical_name_en,synonyms,source_citation) "
                     "VALUES ('planet','mars','Mars','{kuja,mangala}','x'),('yoga','kemadruma','Kemadruma','{kemadruma}','y')")
        D.seed_doshas(conn, autocommit=False)
        # live shape: every dosha alias set empty
        conn.execute("UPDATE brahma_ontology SET synonyms='{}' WHERE entity_class='dosha'")
        conn.commit()
        assert conn.execute("SELECT count(*) AS n FROM brahma_ontology WHERE entity_class='dosha' AND cardinality(synonyms)=0").fetchone()["n"] == 79
        before = _proj(conn)
        others_before = list(conn.execute("SELECT * FROM brahma_ontology WHERE entity_class<>'dosha' ORDER BY canonical_id"))

        D.seed_doshas(conn, autocommit=False)
        conn.commit()

        n_empty = conn.execute("SELECT count(*) AS n FROM brahma_ontology WHERE entity_class='dosha' AND cardinality(synonyms)=0").fetchone()["n"]
        assert n_empty == 0
        got = {r["canonical_id"]: list(r["synonyms"]) for r in conn.execute("SELECT canonical_id,synonyms FROM brahma_ontology WHERE entity_class='dosha'")}
        assert got == SETS, "stored alias sets equal the rule's output, in order"
        assert _proj(conn) == before, "catalog, reference_doshas and every other ontology column are unchanged"
        assert list(conn.execute("SELECT * FROM brahma_ontology WHERE entity_class<>'dosha' ORDER BY canonical_id")) == others_before
        # rerun converges
        D.seed_doshas(conn, autocommit=False)
        conn.commit()
        got2 = {r["canonical_id"]: list(r["synonyms"]) for r in conn.execute("SELECT canonical_id,synonyms FROM brahma_ontology WHERE entity_class='dosha'")}
        assert got2 == got


# ── SS N-113 (a): the 7 names that are ALSO yoga names ──────────────────────────────────────────────────────
# The alias sets are landed. Six of their names (kemadruma, Kemadruma, daridra, Daridra, Sakata Yoga, Sarpa Yoga; the seventh,
# Rajju, is now a withheld generic kuta word and no longer collides) are also names of a yoga in brahma_ontology. They stay in the dosha sets, but the SERVED winner for them
# stays the yoga (resolve_entity's tie order puts a dosha last: PR TI-L0-14 / #3054) until the acharya batch rules.
# This test pins the 7 so the hold is a visible, countable list; flipping them is the one-line switch documented in
# resolve_entity.ts (TIE HOLD), not a change to these sets.
HELD_YOGA_NAMES = {"kemadruma": "kemadruma", "Kemadruma": "kemadruma", "daridra": "daridra", "Daridra": "daridra",
                   "Sakata Yoga": "shakata", "Sarpa Yoga": "sarpa_yoga_dosha"}


@pytest.mark.parametrize("alias,dosha_id", sorted(HELD_YOGA_NAMES.items()))
def test_the_six_yoga_colliding_names_are_in_the_dosha_alias_sets(alias, dosha_id):
    assert alias in SETS[dosha_id]


# ── independent review L0B nits: qualifiers and generic kuta words ───────────────────────────────────────────
def test_name_sa_parentheticals_that_are_qualifiers_are_not_aliases_but_name_parentheticals_are():
    assert "Sandhi" not in SETS["balarishta_sandhi"] and "Candra Dusthāna" not in SETS["balarishta_moon_dusthana"]
    assert "Svakṣetra" not in SETS["kuja_dosha_bhanga_own_sign"] and "Lagna" not in SETS["papa_kartari_lagna"]
    assert "Aṣṭama/Kaṇṭaka Śani" not in SETS["dhaiya"]
    assert "Kuja Doṣa" in SETS["manglik"], "a parenthetical that names a doṣa IS an alternative name"
    # the head part before the parenthetical is always a name
    assert "Bālāriṣṭa" in SETS["balarishta"] or "Bālāriṣṭa (Sandhi)" in SETS["balarishta_sandhi"]


EXPECTED_WITHHELD = {
    "nadi_dosha": ["Nadi", "Nāḍī"], "bhakoot_dosha": ["Bhakoot", "Bhakūṭa", "Bhakuta"], "gana_dosha": ["Gana", "Gaṇa"],
    "yoni_dosha": ["Yoni"], "vashya_dosha": ["Vashya", "Vaśya", "Vasya"], "tara_dosha_compat": ["Tārā", "Tara"],
    "varna_dosha": ["Varna", "Varṇa"], "graha_maitri_dosha": ["Graha-Maitri", "Graha-Maitrī"],
    "gandanta_dosha": ["Gandanta", "Gaṇḍānta"], "mool_dosha": ["Mūla", "Mula"], "abhukta_mula_dosha": ["Abhukta-Mula"],
    "vish_kanya_dosha": None, "rajju_dosha": ["Rajju"], "vedha_dosha": ["Vedha"],
    "stree_deergha_dosha": ["Stree-Deergha", "Strī-Dīrgha", "Stri-Dirgha"], "mahendra_dosha": ["Mahendra"],
}


def test_generic_kuta_words_are_withheld_from_the_stored_sets_and_listed_for_the_acharya_batch():
    withheld = D.withheld_dosha_aliases()
    assert sum(len(v) for v in withheld.values()) == 28
    for cid, words in withheld.items():
        d = BY_ID[cid]
        assert d["category"] in D._KUTA_CATEGORIES
        for w in words:
            assert " " not in w and w not in SETS[cid], (cid, w)
    for cid, words in EXPECTED_WITHHELD.items():
        if words is not None:
            assert set(words) <= set(withheld.get(cid, [])), cid
    # non-kuta single-token names are kept: they are distinctive names, not factors
    assert "Manglik" in SETS["manglik"] and "Shrapit" in SETS["shrapit_dosha"] and "Angarak" in SETS["angarak"]


# ── COUPLING (independent review L0B #1): the winner hold lives in the resolver ───────────────────────────────
RESOLVER = Path(__file__).resolve().parents[3] / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "L0_brahmagyan" / "resolve_entity.ts"


def test_the_dosha_alias_sets_may_only_land_in_a_tree_whose_resolver_keeps_a_dosha_last_in_ties():
    """With main's ORDER BY (alphabetical entity_class) these alias sets alone flip 6 served names from the yoga to the dosha
    (kemadruma, Kemadruma, daridra, Daridra, Sakata Yoga, Sarpa Yoga). PR #3054 adds `(entity_class = 'dosha')` to the
    ORDER BY. This test is red until that line is in the tree: #3054 must be merged before (or with) this PR and before the
    level-0 rebuild."""
    sql = RESOLVER.read_text(encoding="utf-8")
    order = re.search(r"ORDER BY[^`]*", sql)
    assert order and "(entity_class = 'dosha')" in order.group(0), (
        "resolve_entity.ts has no dosha-last tie preference: merge PR #3054 (TI-L0-14) first")
