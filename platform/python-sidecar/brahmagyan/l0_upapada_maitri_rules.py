"""
brahmagyan.l0_upapada_maitri_rules — L0 Brahmagyan: hand-curated classical rule
corpus for D-2 Lane V-6 (Doctrine completions).

Three rule sets authored here, each a small, versioned, citable table (never a
narrative-string "as per tradition" claim — CLAUDE.md B.3 derivation-ledger
mandate). Every rule carries a deterministic `rule_id` (UUID5, same scheme as
`l0_rules.py`'s extracted corpus: `UUID5(NAMESPACE_URL, "text_id|verse_ref|slug")`)
so ga_structural_writer.py's `citation_ref` fields can point at a stable,
resolvable id rather than a bare string.

1. UPAPADA_RULES (CR-101) — BPHS-tradition Upapada Lagna (UL = Arudha of the
   12th house, A12) placement rules used for marriage-quality/timing reading.
   Source: BPHS ch.30 (Yogas from UL) as commonly transmitted via the Jaimini
   Upapada doctrine (UL is the "Arudha of the Bhava that is the 2nd-from-11th",
   which reduces to A12 — Sanjay Rath, "Jaimini Sutras", and KN Rao's Arudha
   Lagna treatment both cite this reduction explicitly). Rules below encode
   the placement-of-UL-lord + benefic/malefic-association tests widely
   reproduced across BPHS commentaries under this chapter heading.

2. MAITRI_RULE (CR-105) — the pañcadhā-maitrī (5-fold compound-friendship)
   compounding rule. BPHS ch.4 gives the NATURAL (naisargika) friendship
   table (already coded as `NATURAL_PLANET_RELATIONS` in
   `ga_structural_writer.py`); this file supplies the TEMPORAL (tatkalika)
   rule (planets in 2nd/3rd/4th/10th/11th/12th houses from one another =
   temporal friends; 1st/5th/6th/7th/8th/9th = temporal enemies — BPHS ch.4
   v.19-20) and the 5-way compounding table (natural+temporal → Adhi Mitra /
   Mitra / Sama / Shatru / Adhi Shatru — BPHS ch.4 v.21-22).

3. KENDRADHIPATI_RULE (ledger row 49) — the kendrādhipati-doṣa PROPOSED
   ruling. Recorded here as PROPOSED (not binding) pending conductor DR-n
   record; see the citation_human field on each row for the exact classical
   ground and the PROPOSED flag carried into chart_facts.

ZERO LLM — hand-curated from cited classical chapters, deterministic ids.
"""
from __future__ import annotations

import uuid

_NS = uuid.NAMESPACE_URL


def _rule_id(text_id: str, verse_ref: str, slug: str) -> str:
    return str(uuid.uuid5(_NS, f"{text_id}|{verse_ref}|{slug}"))


# ── 1. Upapada Lagna (UL = A12) placement rules — BPHS ch.30 tradition ──────
# Each rule: {rule_id, slug, condition, verdict, citation_human}
# `condition` values are evaluated by ga_structural_writer._build_upapada_rows
# against the UL's own house-from-UL classification of its dispositor and any
# graha conjunct/aspecting UL — this table supplies ONLY the citable rule
# text + verdict, never a re-derivation of the placement itself (B.1).
UPAPADA_RULES: list[dict[str, str]] = [
    {
        "rule_id": _rule_id("bphs", "ch.30", "ul_lord_kendra_trikona_from_ul"),
        "slug": "ul_lord_kendra_trikona_from_ul",
        "condition": "ul_lord_house_from_ul in (1,4,5,7,9,10)",
        "verdict": "auspicious_marriage_indication",
        "citation_human": (
            "BPHS ch.30 (Upapada Yogas): the lord of Upapada Lagna posited in a "
            "kendra or trikona counted from UL itself indicates a stable, "
            "auspicious marital significance for the pada."
        ),
    },
    {
        "rule_id": _rule_id("bphs", "ch.30", "ul_lord_dusthana_from_ul"),
        "slug": "ul_lord_dusthana_from_ul",
        "condition": "ul_lord_house_from_ul in (6,8,12)",
        "verdict": "afflicted_marriage_indication",
        "citation_human": (
            "BPHS ch.30 (Upapada Yogas): the lord of Upapada Lagna posited in a "
            "dusthana (6/8/12) counted from UL itself indicates affliction to "
            "the marital significance of the pada — read together with any "
            "benefic mitigation before use as a standalone verdict."
        ),
    },
    {
        "rule_id": _rule_id("bphs", "ch.30", "natural_benefic_conjunct_ul"),
        "slug": "natural_benefic_conjunct_ul",
        "condition": "any_natural_benefic_conjunct_ul",
        "verdict": "benefic_association_strengthens_pada",
        "citation_human": (
            "BPHS ch.30 tradition: a natural benefic (Jupiter/Venus/waxing "
            "Moon/unafflicted Mercury) conjunct Upapada Lagna strengthens the "
            "pada's auspicious signification."
        ),
    },
    {
        "rule_id": _rule_id("bphs", "ch.30", "natural_malefic_conjunct_ul"),
        "slug": "natural_malefic_conjunct_ul",
        "condition": "any_natural_malefic_conjunct_ul",
        "verdict": "malefic_association_afflicts_pada",
        "citation_human": (
            "BPHS ch.30 tradition: a natural malefic (Sun/Mars/Saturn/Rahu/"
            "Ketu) conjunct Upapada Lagna afflicts the pada's signification — "
            "the classical remedy-reading is to weigh this against the UL "
            "lord's own placement (see ul_lord_kendra_trikona_from_ul /"
            "ul_lord_dusthana_from_ul) rather than reading either test alone."
        ),
    },
]

# ── 2. Pañcadhā-maitrī temporal friendship + compound table — BPHS ch.4 ────
# Temporal (tatkalika) rule (BPHS ch.4 v.19-20): from one planet to another,
# counted in houses (1-indexed, 1=same sign):
#   houses {2,3,4,10,11,12} from the source planet's sign -> temporal friend
#   houses {1,5,6,7,8,9}   from the source planet's sign -> temporal enemy
TEMPORAL_FRIEND_HOUSES: frozenset[int] = frozenset({2, 3, 4, 10, 11, 12})
TEMPORAL_ENEMY_HOUSES: frozenset[int] = frozenset({1, 5, 6, 7, 8, 9})

MAITRI_TEMPORAL_RULE_ID = _rule_id("bphs", "ch.4.19-20", "tatkalika_maitri")
MAITRI_TEMPORAL_CITATION_HUMAN = (
    "BPHS ch.4 v.19-20 (Tatkālika/temporal friendship): counted from the "
    "source graha's own sign to the target graha's sign, houses 2/3/4/10/11/12 "
    "= temporal friend; houses 1/5/6/7/8/9 = temporal enemy."
)

# 5-fold compound table (BPHS ch.4 v.21-22): combine the NATURAL relation
# (friend/neutral/enemy, from NATURAL_PLANET_RELATIONS in ga_structural_writer)
# with the TEMPORAL relation (friend/enemy) computed above.
#   natural friend + temporal friend  -> Adhi Mitra   (great friend)
#   natural friend + temporal enemy   -> Sama          (neutral — one up one down)
#   natural neutral + temporal friend -> Mitra         (friend)
#   natural neutral + temporal enemy  -> Shatru        (enemy)
#   natural enemy + temporal friend   -> Sama          (neutral — one up one down)
#   natural enemy + temporal enemy    -> Adhi Shatru   (great enemy)
MAITRI_COMPOUND_TABLE: dict[tuple[str, str], str] = {
    ("friend", "friend"): "adhi_mitra",
    ("friend", "enemy"): "sama",
    ("neutral", "friend"): "mitra",
    ("neutral", "enemy"): "shatru",
    ("enemy", "friend"): "sama",
    ("enemy", "enemy"): "adhi_shatru",
}
MAITRI_COMPOUND_RULE_ID = _rule_id("bphs", "ch.4.21-22", "panchadha_maitri_compound")
MAITRI_COMPOUND_CITATION_HUMAN = (
    "BPHS ch.4 v.21-22 (Pañcadhā Maitrī): natural × temporal relation compounds "
    "to one of 5 grades — Adhi Mitra (great friend), Mitra (friend), Sama "
    "(neutral), Shatru (enemy), Adhi Shatru (great enemy)."
)

# ── 3. Kendrādhipati-doṣa — PROPOSED ruling (NOT binding; see final report) ─
# Classical ground (Phaladeepika ch.2 v.7-8; BPHS ch.7's kendrādhipatya
# discussion of Mercury/Jupiter/Venus/Moon as lords of ONLY kendra houses):
# a natural benefic (Jupiter, Venus, Mercury, waxing-tending Moon) that rules
# a kendra house (4th/7th/10th — NOT the lagna/1st, which is both kendra and
# trikona and is textually exempted) and rules NO trikona house (1/5/9)
# ACQUIRES kendrādhipatya-doṣa: it behaves as if functionally neutral-to-mild-
# malefic rather than a pure benefic. A natural malefic that rules ONLY a
# kendra (and no trikona) is UNAFFECTED by this doctrine (kendrādhipatya-doṣa
# is a benefic-only affliction per the cited texts — a malefic kendra lord's
# functional standing is governed by the separate kendradhipatya-immunity
# rule already present in `_get_functional_class_dynamic`, not duplicated
# here). PROPOSED per protocol §4.1/§4.3 — Adjudicator-doctrine sign-off is
# required before this ruling is binding; see the V-6 close report.
KENDRADHIPATI_RULE_ID = _rule_id("phaladeepika", "ch.2.7-8", "kendradhipati_dosha_benefic_only")
KENDRADHIPATI_CITATION_HUMAN = (
    "PROPOSED (Phaladeepika ch.2 v.7-8; BPHS ch.7 kendrādhipatya discussion): "
    "a natural benefic (Jupiter/Venus/Mercury/Moon) that rules a kendra house "
    "(4/7/10 — 1st exempted as also-trikona) and no trikona house (1/5/9) "
    "carries kendrādhipati-doṣa (functional demotion toward neutral/mild-"
    "malefic). Natural malefics are unaffected by this specific doctrine. "
    "PROPOSED, not binding — pending conductor DR-n record."
)

NATURAL_BENEFICS_FOR_KENDRADHIPATI: frozenset[str] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
KENDRA_HOUSES_NON_LAGNA: frozenset[int] = frozenset({4, 7, 10})
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
