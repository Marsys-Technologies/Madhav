"""
test_nakshatra_vocabulary_normaliser.py -- SS N-548 (one canonical nakshatra spelling, narrow shape).

  1. The canonical family and its authority: `brahmagyan.l0_nakshatra.NAKSHATRAS_ENRICHED[i].name_en`,
     the table `bg_nakshatra` seeds (Mrigasira / Moola / Dhanishtha), agreed by the L0 ontology.
  2. ONE normaliser: every registered spelling (canonical, lexicon alt_names / IAST, ontology synonyms,
     the three legacy L1 spellings) resolves; anything else RAISES -- never a silent default.
  3. STATIC: every nakshatra name any touched writer can EMIT is one of the canonical 27, while the
     untouched modules (`pyjhora_adapter._names`, `pipeline.transit_search`,
     `services.ka_graha_sancara.engine`) keep their own literals and map 1:1 onto the lexicon.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

SIDECAR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIDECAR))

from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED  # noqa: E402
from brahmagyan.l0_ontology import NAK_DATA  # noqa: E402
from brahmagyan.nakshatra_vocabulary import _fold  # noqa: E402  (the fold the module itself uses)
from brahmagyan.nakshatra_vocabulary import (  # noqa: E402
    AMBIGUOUS_BARE_TOKENS,
    CANONICAL_NAKSHATRA_NAMES,
    LEGACY_L1_SPELLINGS,
    NAKSHATRA_SYNONYMS,
    SUPPRESSED_AMBIGUOUS_ALIASES,
    AmbiguousNakshatraError,
    UnknownNakshatraError,
    canonical_nakshatra,
    nakshatra_index,
    nakshatra_number,
    normalize_nakshatra,
)

CANON = list(CANONICAL_NAKSHATRA_NAMES)
NAK_DEG = 360.0 / 27.0


# ═══════════════════════════════════════════ 1. canonical family + authority ═══════════════════════════════════════════

def test_canonical_names_are_the_bg_nakshatra_seed_name_en_in_nakshatra_order():
    rows = sorted((r for r in NAKSHATRAS_ENRICHED if 1 <= r["nakshatra_id"] <= 27), key=lambda r: r["nakshatra_id"])
    assert CANON == [r["name_en"] for r in rows] and len(CANON) == len(set(CANON)) == 27
    assert (CANON[4], CANON[18], CANON[22]) == ("Mrigasira", "Moola", "Dhanishtha")
    abhijit = [r for r in NAKSHATRAS_ENRICHED if r["nakshatra_id"] == 28]
    assert abhijit and abhijit[0]["name_en"] == "Abhijit" and "Abhijit" not in CANON


def test_bg_nakshatra_seeds_exactly_this_table():
    """`bg_nakshatra` delegates to `l0_nakshatra.seed_nakshatra()`, whose INSERT writes each
    NAKSHATRAS_ENRICHED row's `name_en` into `reference_nakshatra.name_en`."""
    writer = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bg_nakshatra.py").read_text(encoding="utf-8")
    assert "from brahmagyan.l0_nakshatra import seed_nakshatra" in writer
    seed = (SIDECAR / "brahmagyan" / "l0_nakshatra.py").read_text(encoding="utf-8")
    i = seed.index("INSERT INTO reference_nakshatra (")
    cols = [c.strip() for c in seed[seed.index("(", i) + 1: seed.index(")", i)].replace("\n", " ").split(",")]
    assert cols[:4] == ["nakshatra_id", "name_sa_iast", "name_sa_devanagari", "name_en"]
    assert "NAKSHATRAS_ENRICHED" in seed[seed.index("def seed_nakshatra"):]


def test_ontology_canonical_name_en_agrees_with_the_lexicon():
    assert [name_en for _nid, name_en, _sa, _syn in NAK_DATA] == CANON


# ═══════════════════════════════════════════ 2. the one normaliser ═══════════════════════════════════════════

@pytest.mark.parametrize("spelling,canon,n", [
    ("Mrigashira", "Mrigasira", 5), ("Mula", "Moola", 19), ("Dhanishta", "Dhanishtha", 23),      # the L1 adapter's spellings
    ("Mrigasira", "Mrigasira", 5), ("Moola", "Moola", 19), ("Dhanishtha", "Dhanishtha", 23),      # canonical
    ("PurvaPhalguni", "Purva Phalguni", 11), ("purva_bhadrapada", "Purva Bhadrapada", 25),        # space-less / underscore
    (" DHANISHTA ", "Dhanishtha", 23), ("Mṛgaśirā", "Mrigasira", 5),                              # case / padding / IAST
    ("Shravishtha", "Dhanishtha", 23), ("Makayiram", "Mrigasira", 5), ("Moolam", "Moola", 19),     # lexicon alt_names
    ("mrigsira", "Mrigasira", 5), ("mool", "Moola", 19),                                            # ontology synonyms
])
def test_registered_spellings_resolve_to_the_canonical_name_and_number(spelling, canon, n):
    assert normalize_nakshatra(spelling) == canon and nakshatra_index(spelling) == n
    assert canonical_nakshatra(spelling) == canon and nakshatra_number(spelling) == n


def test_every_lexicon_alias_and_every_ontology_synonym_resolves_except_the_suppressed_bare_tokens():
    suppressed = set(SUPPRESSED_AMBIGUOUS_ALIASES)
    for row in NAKSHATRAS_ENRICHED:
        if not 1 <= row["nakshatra_id"] <= 27:
            continue
        assert normalize_nakshatra(row["name_sa_iast"]) == row["name_en"]
        for alt in row["alt_names"]:
            if alt in suppressed:
                with pytest.raises(AmbiguousNakshatraError):
                    normalize_nakshatra(alt)
            else:
                assert normalize_nakshatra(alt) == row["name_en"], alt
    for _nid, name_en, name_sa, synonyms in NAK_DATA:
        assert normalize_nakshatra(name_sa) == name_en
        for syn in synonyms:
            if syn in suppressed:
                with pytest.raises(AmbiguousNakshatraError):
                    normalize_nakshatra(syn)
            else:
                assert normalize_nakshatra(syn) == name_en, syn


# ── SS N-561: ambiguous bare names ──────────────────────────────────────────────────────────────────────────────────────

EXPECTED_AMBIGUOUS = {"purva", "uttara", "poorva", "phalguni", "ashadha", "asadha", "bhadrapada", "bhadra"}


def test_the_ambiguity_set_is_computed_from_the_l0_sources_and_pinned():
    assert {"purva", "uttara"} <= AMBIGUOUS_BARE_TOKENS
    assert AMBIGUOUS_BARE_TOKENS == EXPECTED_AMBIGUOUS, sorted(AMBIGUOUS_BARE_TOKENS ^ EXPECTED_AMBIGUOUS)
    # independently re-derived: every word of every registered spelling owned by two or more nakshatras
    owners: dict[str, set[str]] = {}
    for row in NAKSHATRAS_ENRICHED:
        if 1 <= row["nakshatra_id"] <= 27:
            for sp in [row["name_en"], row["name_sa_iast"], *row["alt_names"]]:
                for w in sp.replace("_", " ").replace("-", " ").split():
                    owners.setdefault(_fold(w), set()).add(row["name_en"])
    for _nid, name_en, name_sa, synonyms in NAK_DATA:
        for sp in [name_sa, *synonyms]:
            for w in sp.replace("_", " ").replace("-", " ").split():
                owners.setdefault(_fold(w), set()).add(name_en)
    assert {t for t, cs in owners.items() if len(cs) > 1} == AMBIGUOUS_BARE_TOKENS


@pytest.mark.parametrize("bare", ["Purva", "Uttara", "uttara", "Poorva", "Phalguni", "Ashadha", "Asadha", "Bhadrapada", "Bhadra",
                                  " PURVA ", "purva_", "Uttara-", "Phalgunī"])
def test_an_ambiguous_bare_token_raises_a_distinct_error_and_never_resolves(bare):
    with pytest.raises(AmbiguousNakshatraError) as exc:
        normalize_nakshatra(bare)
    assert isinstance(exc.value, UnknownNakshatraError) and isinstance(exc.value, ValueError)
    with pytest.raises(AmbiguousNakshatraError):
        nakshatra_index(bare)
    assert canonical_nakshatra(bare) is None and nakshatra_number(bare) is None


@pytest.mark.parametrize("token", sorted(EXPECTED_AMBIGUOUS))
def test_every_token_of_the_ambiguity_set_raises(token):
    with pytest.raises(AmbiguousNakshatraError):
        normalize_nakshatra(token)
    assert token not in NAKSHATRA_SYNONYMS


def test_the_full_names_that_contain_an_ambiguous_token_still_resolve():
    assert normalize_nakshatra("Purva Phalguni") == "Purva Phalguni" and nakshatra_index("Uttara Ashadha") == 21
    assert normalize_nakshatra("Purva Bhadra") == "Purva Bhadrapada" and normalize_nakshatra("UttaraBhadrapada") == "Uttara Bhadrapada"
    assert normalize_nakshatra("Pubba") == "Purva Phalguni" and normalize_nakshatra("Uthiram") == "Uttara Phalguni"   # the unambiguous alt_names of 11 / 12


def test_the_suppressed_registrations_are_exactly_the_bare_purva_uttara_and_are_reported_for_the_lexicon_owner():
    assert dict(SUPPRESSED_AMBIGUOUS_ALIASES) == {
        "Purva": ("Purva Phalguni", "lexicon alt_names"),
        "Uttara": ("Uttara Phalguni", "lexicon alt_names"),
        "uttara": ("Uttara Phalguni", "ontology synonym"),
    }


def test_no_alias_in_the_resolved_map_is_shared_by_two_nakshatras():
    """Independently of the module's own build: fold every registered spelling of every source and check each key has ONE owner."""
    owners: dict[str, set[str]] = {}
    for row in NAKSHATRAS_ENRICHED:
        if 1 <= row["nakshatra_id"] <= 27:
            for sp in [row["name_en"], row["name_sa_iast"], *row["alt_names"]]:
                owners.setdefault(_fold(sp), set()).add(row["name_en"])
    for _nid, name_en, name_sa, synonyms in NAK_DATA:
        for sp in [name_sa, *synonyms]:
            owners.setdefault(_fold(sp), set()).add(name_en)
    shared = {k: sorted(v) for k, v in owners.items() if len(v) > 1}
    assert shared == {}, shared
    for key, canon in NAKSHATRA_SYNONYMS.items():
        assert owners[key] == {canon}, key
        assert key not in AMBIGUOUS_BARE_TOKENS


def test_the_three_legacy_l1_spellings_are_registered_aliases_of_the_lexicon_or_ontology():
    registered = {a.casefold() for r in NAKSHATRAS_ENRICHED for a in r["alt_names"]}
    registered |= {s.casefold() for _i, _e, sa, syns in NAK_DATA for s in [sa, *syns]}
    assert LEGACY_L1_SPELLINGS == {"Mrigashira": "Mrigasira", "Mula": "Moola", "Dhanishta": "Dhanishtha"}
    for legacy, canon in LEGACY_L1_SPELLINGS.items():
        assert legacy.casefold() in registered, legacy
        assert normalize_nakshatra(legacy) == canon


@pytest.mark.parametrize("bad", ["Abhijit", "Vega nakshatra", "NotANakshatra", "", "   ", "Mulaa", "Moolaa", "Nak19", "Dhanisht"])
def test_an_unregistered_name_raises_and_never_defaults(bad):
    with pytest.raises(UnknownNakshatraError) as exc:
        normalize_nakshatra(bad)
    assert isinstance(exc.value, ValueError)
    with pytest.raises(UnknownNakshatraError):
        nakshatra_index(bad)
    assert canonical_nakshatra(bad) is None and nakshatra_number(bad) is None


def test_a_non_string_is_a_type_error_for_the_raising_forms_and_none_for_the_optional_forms():
    for bad in (None, 5, 19.0, ["Moola"]):
        with pytest.raises(TypeError):
            normalize_nakshatra(bad)
        with pytest.raises(TypeError):
            nakshatra_index(bad)
        assert canonical_nakshatra(bad) is None and nakshatra_number(bad) is None


def test_the_alias_map_is_unambiguous_total_and_read_only():
    assert set(NAKSHATRA_SYNONYMS.values()) == set(CANON)
    assert len(NAKSHATRA_SYNONYMS) >= 27 + len(LEGACY_L1_SPELLINGS)
    with pytest.raises(TypeError):
        NAKSHATRA_SYNONYMS["x"] = "Ashwini"  # type: ignore[index]


# ═══════════════════════════════════════════ 3. STATIC: what the touched writers can EMIT ═══════════════════════════════════════════

def test_the_adapter_is_unchanged_and_ga_positions_folds_every_adapter_name_onto_the_lexicon():
    from pyjhora_adapter._names import NAKSHATRA_NAMES, nakshatra_name

    adapter = [n for n in NAKSHATRA_NAMES if n]
    assert len(adapter) == 27 and (adapter[4], adapter[18], adapter[22]) == ("Mrigashira", "Mula", "Dhanishta")  # byte-identical (SS N-548)
    assert [normalize_nakshatra(n) for n in adapter] == CANON
    assert [normalize_nakshatra(nakshatra_name(i)) for i in range(1, 28)] == CANON


def test_ga_dashas_moon_nakshatra_name_is_canonical_for_every_longitude():
    from ga_writers.ga_dashas_writer import _get_moon_nakshatra_lord

    for n in range(1, 28):
        idx, name, _lord = _get_moon_nakshatra_lord((n - 1) * NAK_DEG + 1.0)
        assert (idx, name) == (n, CANON[n - 1])
    assert _get_moon_nakshatra_lord(18 * NAK_DEG + 1.0)[1] == "Moola"       # fails on base: "Mula"
    assert _get_moon_nakshatra_lord(4 * NAK_DEG + 1.0)[1] == "Mrigasira"    # fails on base: "Mrigashira"


def test_panchang_engine_names_fold_onto_the_lexicon_and_ga_panchangas_table_is_the_lexicon():
    from panchang_engine.shastra_tables import NAKSHATRA_NAMES as PE
    from ga_writers import ga_panchanga_writer as gp

    assert len(PE) == 27 and [normalize_nakshatra(n) for n in PE] == CANON
    assert PE[4] == "Mrigashira"  # the engine's own spelling; ga_panchanga normalises it at emission
    assert list(gp.NAKSHATRA_NAMES) == CANON


def test_every_touched_writers_own_name_table_is_the_lexicon_in_order():
    from ga_writers import ga_sensitive_writer as gs5
    from ga_writers import ga_structural_writer as gstr
    from bodha_writers import nakshatra_semantic_emitter as nse
    from services.ka_sangam import engine as sangam
    from services.kala_permission import permission as perm

    for table in (gs5.NAKSHATRAS, gstr.NAKSHATRA_NAMES_27, nse.NAKSHATRA_ORDER,
                  sangam._NAKSHATRAS_ORDERED, perm.NAKSHATRA_NAMES_27):
        assert list(table) == CANON


def test_the_untouched_kala_literals_map_one_to_one_onto_the_lexicon():
    from pipeline.transit_search import NAKSHATRAS as TS
    from services.ka_graha_sancara.engine import NAKSHATRAS as GS
    from services.gochara_rules.ashtakavarga import NAKSHATRAS as AV

    assert (TS[4], TS[18], TS[22]) == ("Mrigashira", "Moola", "Dhanishta")      # byte-identical (SS N-548)
    assert (GS[4], GS[18], GS[22]) == ("Mrigashira", "Mula", "Dhanishta")
    assert (AV[4], AV[18], AV[22]) == ("Mrigashira", "Mula", "Dhanishta")       # byte-identical (SS N-593; Kala's post-round change)
    for literal in (TS, GS, AV):
        assert [normalize_nakshatra(n) for n in literal] == CANON
        assert [nakshatra_index(n) for n in literal] == list(range(1, 28))


_TOUCHED_NAME_READERS = [
    "ga_writers/ga_positions_writer.py", "ga_writers/ga_dashas_writer.py", "ga_writers/ga_panchanga_writer.py",
    "ga_writers/ga_sensitive_writer.py", "ga_writers/ga_sensitive_degree_writer.py", "ga_writers/ga_structural_writer.py",
    "ga_writers/ga_medical_writer.py", "bodha_writers/nakshatra_semantic_emitter.py",
    "pipeline/orchestrator/writers/ka_sangam.py", "pipeline/orchestrator/writers/ph_muhurta.py",
    "services/ka_sangam/engine.py", "services/kala_permission/permission.py",
]   # gochara_rules/ashtakavarga.py and p6.py are out of this round (SS N-593: byte-identical to main)


@pytest.mark.parametrize("rel", _TOUCHED_NAME_READERS)
def test_no_touched_module_keeps_a_raw_index_or_defaulting_lookup_by_nakshatra_name(rel):
    src = (SIDECAR / rel).read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert not re.search(r"NAKSHATRA[A-Za-z_0-9]*\.index\(", code), f"{rel}: raw .index(name) on a nakshatra table"
    assert not re.search(r"NAKSHATRA[A-Za-z_0-9]*\.get\([^()]*,\s*0\)", code), f"{rel}: .get(name, 0) silent-Ashwini default"
    assert not re.search(r"_NAKSHATRA_(ORDINALS|ID_1INDEXED)\b", code), f"{rel}: a hand-typed ordinal table"
