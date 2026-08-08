"""
fact_identity_parser.py — the ONE deterministic parser for graha/house/varga/
sign identity smuggled inside `chart_facts.fact_subject` / `.fact_key` text
(ADHIṢṬHĀNA Campaign A, Lane A5; MASTER_PLAN_v1_0.md §3 Lane A5).

`chart_facts` (migration `204_chart_facts.sql`) has no structured varga/house
columns — every consumer that wants "what's in house 7" or "Venus's D9 sign"
has been hand-rolling its own fragile substring parsing against a swamp of
at least six house encodings, three varga separators, and two planet-naming
systems (see SIDDHANTA_STATE.md DB10 for a documented substring-collision
defect from exactly this class of ad-hoc parsing). This module replaces all
of that with one parser, with per-rule provenance, whose output populates
the derived `chart_fact_identity` table (migration TBD).

R19 (`chart_facts` stays sealed): this module only READS `fact_subject` /
`fact_key` strings; it never touches `chart_facts` itself. The derived index
built from this parser's output is fully rebuildable from `chart_facts`
alone at any time.

Design — two-phase parse + merge (see A5_COVERAGE_REPORT for the empirical
justification, drawn from a live reconnaissance pass over all three
canonical charts before a single regex was written, per the lane's TDD
mandate):

  Phase 1 — parse `fact_subject` alone against an ordered list of shape
  rules (most specific / highest-arity first, so e.g. a varga+house+pair
  shape is never mis-claimed by a plainer varga+house rule).

  Phase 2 — parse `fact_key` alone against a SMALL, deliberately narrow set
  of rules: fact_key is the identity carrier only in the handful of writer
  conventions where a bare varga code (`D9`, `D_ALL`) or a bare house code
  (`house_7`) was placed in the key column instead of the subject column
  (see `ga_condition_writer.py` ~1079/1104/1127/1310/1334 for the varga-as-
  bare-fact_key convention). Everything else in fact_key — grade labels,
  matrix coordinates like `h8_offset7` or `from_sign_4_offset_12`, secondary
  relational references like `aspected_by_SUN` — is deliberately NOT
  absorbed into identity dimensions here; see the module docstring's "Scope
  boundary" section below for why, and the coverage report for the specific
  named shapes this leaves out.

  Phase 3 — merge: if `fact_subject` alone already yields a full compound
  shape (e.g. `graha_in_varga`), the key is not consulted further (it is
  almost always a plain attribute name like `grade` or `dignity_state` in
  that case). If `fact_subject` yields only a partial identity (a bare
  graha, or a recognized-but-dimensionless special-point/token, or nothing
  at all), Phase 2's key-derived dimension is merged in.

Scope boundary (read before extending this module):
  This parser extracts graha/house/varga/sign identity — the four
  dimensions the ADHIṢṬHĀNA A5 lane was chartered to structure. It
  deliberately does NOT attempt to decode every secondary relational
  token embedded in a fact_key (`aspected_by_SUN`, `conjunct_RAH_MEAN`,
  `opposed_argala_D1`, `on_Virgo`, `h8_offset7`, `from_sign_N_offset_M`)
  into extra columns. Those are matrix/relation COORDINATES layered on top
  of a row whose primary identity is already captured from fact_subject;
  absorbing every one of them would multiply this module's rule count
  across a long, ad-hoc tail without changing what a consumer needs for the
  lane's target queries ("occupants of house 7", "Venus's D9 sign", "7th
  lord and its house"). This is a disclosed, named limitation — see the
  coverage report — not a silent gap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

from brahmagyan.graha_vocabulary import norm_graha

# ── Canonical vocabularies ───────────────────────────────────────────────

# System-A graha subject codes (Lane A2 SSoT output). LAGNA is included
# because it appears as a bare fact_subject; MC (midheaven) likewise
# appears in hyphen-compound subjects (see migration 551's synonym for
# canonical_id='midheaven').
SYSTEM_A_GRAHAS = frozenset({
    "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT",
    "RAH_MEAN", "KET_MEAN", "LAGNA", "MC",
})

# Local, narrowly-scoped alias layer used ONLY for recognizing compound
# subject tokens before handing them to `norm_graha()` for canonicalization.
# `graha_vocabulary._GRAHA_ALIASES` is the frozen Lane A2 SSoT and is not
# modified here (per CLAUDE.md do-not: never fork/shadow an SSoT) — this is
# strictly a pre-normalization step for two tokens observed in live compound
# subjects (`ASC-MAR`, `MC-KET`) that `norm_graha` does not itself resolve
# (ASC/MC are not planetary grahas in `_GRAHA_ALIASES`; MC has no alias at
# all and ASC is the live data's short form of the Ascendant/Lagna, which
# `brahma_ontology` migration 551 already treats as a synonym of
# canonical_id='ascendant' i.e. LAGNA).
_LOCAL_COMPOUND_ALIASES = {"ASC": "LAGNA", "MC": "MC"}


def _canon_graha_token(tok: str) -> str | None:
    """Resolve one compound-subject token to a system-A graha code, or None
    if the token is not a recognized graha/lagna/mc token at all."""
    tok_u = tok.upper()
    if tok_u in _LOCAL_COMPOUND_ALIASES:
        tok_u = _LOCAL_COMPOUND_ALIASES[tok_u]
    if tok_u == "MC":
        return "MC"
    code = norm_graha(tok_u)
    return code if code in SYSTEM_A_GRAHAS else None


# Sign names in canonical zodiac order (rashi 1..12) — used both for the
# `D#_<SignName>` Title-case compound shape and for bare sign-name subjects
# (`aspect_jaimini`'s Rasi-drishti matrix uses bare sign names, not house
# numbers, for both fact_subject and fact_key — signs are ascendant-
# independent, houses are not; the two must never be conflated).
SIGN_NAMES_IN_ORDER = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_NAME_TO_NUM = {name: i + 1 for i, name in enumerate(SIGN_NAMES_IN_ORDER)}
SIGN_NAME_TO_NUM_UPPER = {name.upper(): n for name, n in SIGN_NAME_TO_NUM.items()}

# The 30-varga computational set (`ga_vargas_writer.py` ALL_30_VARGAS =
# PARASHARI_16 + SUPPLEMENTARY_11 + NADI_3; A6_VARGAS_SPEC_v1_0.md §1).
# Mirrored here (not imported) because `ga_vargas_writer.py` pulls in the
# full pyjhora_adapter/DB-writer dependency chain, which this lightweight,
# widely-importable parser module must not carry. Drift is prevented by
# `tests/test_fact_identity_parser.py::test_all_30_vargas_matches_writer`,
# which imports the real writer constant and asserts byte-for-byte equality
# — a real detector, not an unverified claim (CLAUDE.md §N.7 item 3 / §N.8).
PARASHARI_16 = (1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)
SUPPLEMENTARY_11 = (5, 6, 8, 11, 14, 15, 21, 32, 33, 50, 54)
NADI_3 = (108, 150, 2700)
ALL_30_VARGAS = frozenset(PARASHARI_16 + SUPPLEMENTARY_11 + NADI_3)

# Underscore-compound graha tokens (varga_graha / varga_graha_graha shapes)
# use ONLY the system-A codes (confirmed against live data — no short-code
# variants observed in this position). Sorted longest-first so the regex
# alternation prefers RAH_MEAN/KET_MEAN over any shorter accidental prefix.
_UNDERSCORE_GRAHA_TOKENS = sorted(
    (g for g in SYSTEM_A_GRAHAS if g not in ("LAGNA", "MC")),
    key=len, reverse=True,
)
_UNDERSCORE_GRAHA_ALT = "|".join(_UNDERSCORE_GRAHA_TOKENS)

# Hyphen-compound tokens additionally admit the short RAH/KET forms and
# ASC/MC (all observed live: `MAR-RAH`, `MOON-KET`, `ASC-VEN`, `MC-MAR`).
_HYPHEN_GRAHA_TOKENS = sorted(
    set(_UNDERSCORE_GRAHA_TOKENS) | {"RAH", "KET", "ASC", "MC"},
    key=len, reverse=True,
)
_HYPHEN_GRAHA_ALT = "|".join(_HYPHEN_GRAHA_TOKENS)

_SIGN_NAME_ALT = "|".join(SIGN_NAMES_IN_ORDER)

# 2-letter graha shorthand (SU/MO/MA/ME/JU/VE/SA/RA/KE) — a THIRD planet-
# naming system observed only in the `ARUDHA_<code>` shape (graha-keyed
# Jaimini arudha padas, e.g. `ARUDHA_JU` = the arudha computed with Jupiter
# as reference graha — distinct from `ARUDHA_A<n>`/`BHAVA_ARUDHA_A<n>`,
# which are HOUSE-keyed bhava arudhas). All 9 codes already resolve via
# `graha_vocabulary._GRAHA_ALIASES` (SU/MO/MA/ME/JU/VE/SA/RA/KE), so no new
# alias table is introduced here — this is purely the regex alternation.
_TWO_LETTER_GRAHA_TOKENS = ("SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE")
_TWO_LETTER_GRAHA_ALT = "|".join(_TWO_LETTER_GRAHA_TOKENS)

# Life-domain / karyatva words observed as both `D#_<word>` compound
# subjects (`karaka_bhava_concordance`) and bare `<word>` subjects
# (`karakatva_strength_per_significance`, `karaka_house_lord_overlap_flag`)
# across all three canonical charts. These are classical house-signification
# labels, NOT a house number themselves (the varga_domain_word subject rule
# already declines to reverse-map them to a house — see that rule's
# docstring) — kept as an explicit set (not a bare `[a-z_]+` catch-all) so
# an actually-unrecognized lowercase token still surfaces as a real gap
# instead of being silently swallowed.
KNOWN_DOMAIN_WORDS = frozenset({
    "artha", "authority", "body", "career", "children", "courage",
    "creativity", "dharma", "education", "enemies", "foreign_travel",
    "gains", "happiness", "inner_strength", "intelligence", "kama",
    "liberation", "lineage", "longevity", "losses", "luck", "moksha",
    "mother", "obstacles", "self", "siblings", "spiritual_merit", "spouse",
    "travel", "wealth",
})

# Special-point / role / index tokens that ARE recognized (a human auditing
# an "unparsed" bucket should never see these as unexplained) but do NOT
# themselves carry graha/house/varga/sign identity in fact_subject/fact_key
# text — the dimension they relate to (which graha occupies MANDI, which
# house KAKSHYA_3 falls in) lives in the fact's VALUE columns, not smuggled
# in the key/subject strings this parser exists to clean up. Enumerated
# from the live Step-1 reconnaissance inventory (see coverage report), not
# guessed.
KNOWN_SPECIAL_POINTS = frozenset({
    "MANDI", "MRITYU_SPHUTA", "BRAHMA_POINT", "VISHNU_POINT", "SHIVA_POINT",
    "YOGI_POINT", "AVAYOGI_POINT", "DHUMA", "VYATIPATA", "PARIVESHA",
    "INDRACHAPA", "UPAKETU", "CHART", "SARVA",
    # Upagraha / sensitive-point family (aprakasha_position, saturn_derived_
    # point, sun_derived_upagraha) — each a single fixed sensitive point per
    # chart; no graha/house/varga/sign digit embedded in the name itself.
    "DHWAJA", "KANDANGA", "PATALA", "PIDAA", "VIGHNI",
    "GULIKA_LAHIRI", "MAANDI", "YAMAGANDA_SPHUTA", "GULIKA", "GULIKA_HINDU",
    "ARTHA_PRAHARA", "KALA_SUN", "MRITYU_SUN", "YAMAGHANTAKA", "KALA",
    # Special-lagna family (special_lagna) — each its own named lagna
    # variant, not a bhava/varga-indexed shape.
    "BHAVA_LAGNA", "GHATI_LAGNA", "HORA_LAGNA", "INDU_LAGNA", "SREE_LAGNA",
    "VARNADA_LAGNA", "VIGHATI_LAGNA", "UPAPADA_LAGNA",
    # Bhrigu/esoteric sphuta points (esoteric_point_* categories) — fixed
    # named points, no embedded digit.
    "BHAVA_ARUDHA_UPA", "BHRIGU_BINDU", "PRANAPADA_SPHUTA", "BEEJA_SPHUTA",
    "KSHETRA_SPHUTA", "TRIKONA_DASHA_SPHUTA",
    "SRI_YANTRA_LAGNA", "SRI_YANTRA_MOON", "SRI_YANTRA_SUN",
    # Saptarishi/Maharsi sphuta points (maharsi_specific_point) — 7 fixed
    # sage-attributed points.
    "AGASTYA_SPHUTA", "ATRI_SPHUTA", "BHARADWAJA_SPHUTA", "GAUTAMA_SPHUTA",
    "KASHYAPA_SPHUTA", "VASISHTHA_SPHUTA", "VISHWAMITRA_SPHUTA",
    # Nakshatra-pada sensitive points (nakshatra_pada_sensitive).
    "AK_PADA", "LAGNA_PADA", "MOON_PADA", "SUN_PADA",
    # Yogi/Avayogi/Dhuma-adjacent sensitive-point family.
    "AVAYOGI", "YOGI", "YOGI_GRAHA", "SAHAYOGI", "DUPLICATE_YOGI",
    # KP ruling-planets-natal labels (kp_ruling_planets_natal) — role
    # labels ("ascendant lord", "day lord", ...), the actual graha is the
    # fact VALUE, not the subject text.
    "RP_ASC_LORD", "RP_ASC_SUB_LORD", "RP_DAY_LORD",
    "RP_MOON_SIGN_LORD", "RP_MOON_STAR_LORD",
    # Panchaka classification labels (panchanga_panchaka_classification).
    "PANCHAKA_AGNI", "PANCHAKA_CHORA", "PANCHAKA_MRITYU", "PANCHAKA_RAJA",
    "PANCHAKA_ROGA", "PANCHAKA_OVERALL",
    # Misc single-instance labels.
    "KARAKAMSA", "TAJIK_VARGOTTAMA", "TRIRAASHIPATHI", "YOGA_UNKNOWN",
    # Lal Kitab arudha/index labels — instance-numbered but the number is a
    # Lal-Kitab-internal ordinal (only 1..3 ever observed, a fixed 3-item
    # scheme), NOT verified as a lagna-relative bhava number; the real
    # house number for these rows lives in fact_key='house' as a VALUE, not
    # smuggled in this text. Populating house_num from the ordinal here
    # would be an unverified guess (CLAUDE.md B.10) so it is deliberately
    # withheld.
    "LAL_KITAB_ARUDHA_1", "LAL_KITAB_ARUDHA_2", "LAL_KITAB_ARUDHA_3",
    # Dagdha Rashi variant index (esoteric_point_yogi_system) — 1/2 are two
    # alternate calculation methods for the day's combust sign, not a sign
    # number themselves; same B.10 reasoning as above.
    "DAGDHA_RASHI_1", "DAGDHA_RASHI_2",
})
KNOWN_KARAKA_ROLES = frozenset({
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
    "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA", "STRIKARAKA",
})
# Classical yoga-name / dosha-name labels (yoga_label, dosha_label
# categories) — catalog labels, not graha/house/varga identity.
KNOWN_YOGA_DOSHA_LABELS = frozenset({
    "yuga_nabhasa", "gola", "kedara", "sasa", "shoola", "vasi", "anapha",
    "kemadruma", "manglik",
})
# Ayurdaya (longevity) calculation-method labels (ayurdaya category).
KNOWN_AYURDAYA_LABELS = frozenset({"AMSAYU", "NISARGAYU", "PINDAYU"})
# Reference/lookup-table row keys: these enumerate a FIXED classification
# table (all 27 nakshatras for tara-bala, all 12 signs in transliterated
# Sanskrit for chandra-bala) attached per-chart for convenience — they are
# not the native's own graha/sign placement, so are not sign/nakshatra
# identity for THIS chart. Matched by prefix, not a fixed set (27+12 close
# variants; a prefix check is more honest than transcribing all of them).
_REFERENCE_TABLE_PREFIXES = ("TRANSIT_NAK_", "TRANSIT_SIGN_")


@dataclass(frozen=True)
class IdentityMatch:
    entity_kind: str
    parse_rule: str
    graha_code: str | None = None
    graha_code_secondary: str | None = None
    house_num: int | None = None
    house_num_secondary: int | None = None
    varga_id: str | None = None
    sign_num: int | None = None


# ── fact_subject rules (ordered: most specific first) ───────────────────
# Each rule is (name, compiled_regex, handler(match) -> IdentityMatch|None).

def _r_varga_house_pair(m: re.Match) -> IdentityMatch:
    n, h1, h2 = m.group(1), int(m.group(2)), int(m.group(3))
    return IdentityMatch(
        entity_kind="varga_house_pair", parse_rule="varga_house_pair",
        varga_id=f"D{n}", house_num=h1, house_num_secondary=h2,
    )


def _r_varga_sign_numeric(m: re.Match) -> IdentityMatch:
    n, s = m.group(1), int(m.group(2))
    return IdentityMatch(
        entity_kind="varga_sign", parse_rule="varga_sign_numeric",
        varga_id=f"D{n}", sign_num=s,
    )


def _r_varga_sign_name(m: re.Match) -> IdentityMatch:
    n, sign = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="varga_sign", parse_rule="varga_sign_name",
        varga_id=f"D{n}", sign_num=SIGN_NAME_TO_NUM[sign],
    )


def _r_varga_house(m: re.Match) -> IdentityMatch:
    n, h = m.group(1), int(m.group(2))
    return IdentityMatch(
        entity_kind="varga_house", parse_rule="varga_house_long",
        varga_id=f"D{n}", house_num=h,
    )


def _r_varga_house_short(m: re.Match) -> IdentityMatch:
    n, h = m.group(1), int(m.group(2))
    return IdentityMatch(
        entity_kind="varga_house", parse_rule="varga_house_short",
        varga_id=f"D{n}", house_num=h,
    )


def _r_varga_graha_pair(m: re.Match) -> IdentityMatch:
    n, g1, g2 = m.group(1), m.group(2), m.group(3)
    return IdentityMatch(
        entity_kind="varga_graha_pair", parse_rule="varga_graha_pair",
        varga_id=f"D{n}", graha_code=g1, graha_code_secondary=g2,
    )


def _r_varga_graha(m: re.Match) -> IdentityMatch:
    n, g = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="graha_in_varga", parse_rule="varga_graha_underscore",
        varga_id=f"D{n}", graha_code=g,
    )


def _r_varga_graha_dot(m: re.Match) -> IdentityMatch:
    # Precedent shape from `ga_vargas_writer.py` (~line 916, `f"{vid}.{subject}"`)
    # — NOT observed in any live row across all three canonical charts as of
    # this lane's reconnaissance (see coverage report), but supported for
    # forward-compatibility per the master-plan lead, at zero extra cost.
    n, g = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="graha_in_varga", parse_rule="varga_graha_dot",
        varga_id=f"D{n}", graha_code=g,
    )


def _r_varga_chart(m: re.Match) -> IdentityMatch:
    n = m.group(1)
    return IdentityMatch(
        entity_kind="varga", parse_rule="varga_chart_subject",
        varga_id=f"D{n}",
    )


def _r_varga_domain(m: re.Match) -> IdentityMatch:
    # `D#_<lowercase_domain_word>` (e.g. `D10_wealth`) — the domain word is
    # a life-signification label (karyatva), not a graha/house/sign; kept
    # only as varga identity. Deliberately does NOT attempt to reverse-map
    # the domain word to a house number — that is a classical inference
    # (which house governs "wealth" in this varga's own lagna framing),
    # not a textual extraction, and belongs to a future interpretive layer
    # (B.1/B.10: no fabricated computation at the Index layer).
    n = m.group(1)
    return IdentityMatch(
        entity_kind="varga_domain", parse_rule="varga_domain_word",
        varga_id=f"D{n}",
    )


def _r_hyphen_house(m: re.Match) -> IdentityMatch:
    prefix, h = m.group(1), int(m.group(2))
    graha = _canon_graha_token(prefix)
    if graha:
        return IdentityMatch(
            entity_kind="graha_in_house", parse_rule="hyphen_graha_house",
            graha_code=graha, house_num=h,
        )
    if prefix.upper() == "SARVA":
        return IdentityMatch(
            entity_kind="house", parse_rule="hyphen_sarva_house",
            house_num=h,
        )
    # Unrecognized prefix (none observed live) — still house-bearing.
    return IdentityMatch(
        entity_kind="house", parse_rule="hyphen_unknown_prefix_house",
        house_num=h,
    )


def _r_hyphen_sign(m: re.Match) -> IdentityMatch:
    prefix, s = m.group(1), int(m.group(2))
    graha = _canon_graha_token(prefix)
    if graha:
        return IdentityMatch(
            entity_kind="graha_in_sign", parse_rule="hyphen_graha_sign",
            graha_code=graha, sign_num=s,
        )
    if prefix.upper() == "SARVA":
        return IdentityMatch(
            entity_kind="sign", parse_rule="hyphen_sarva_sign",
            sign_num=s,
        )
    return IdentityMatch(
        entity_kind="sign", parse_rule="hyphen_unknown_prefix_sign",
        sign_num=s,
    )


def _r_hyphen_graha_pair(m: re.Match) -> IdentityMatch | None:
    left, right = m.group(1), m.group(2)
    g1, g2 = _canon_graha_token(left), _canon_graha_token(right)
    if g1 is None or g2 is None:
        return None
    return IdentityMatch(
        entity_kind="graha_pair", parse_rule="hyphen_graha_pair",
        graha_code=g1, graha_code_secondary=g2,
    )


def _r_graha_in_house_underscore(m: re.Match) -> IdentityMatch:
    g, h = m.group(1), int(m.group(2))
    return IdentityMatch(
        entity_kind="graha_in_house", parse_rule="graha_in_house_underscore",
        graha_code=g, house_num=h,
    )


def _r_bare_house(m: re.Match) -> IdentityMatch:
    return IdentityMatch(
        entity_kind="house", parse_rule="bare_house_subject",
        house_num=int(m.group(1)),
    )


def _r_bare_bhava(m: re.Match) -> IdentityMatch:
    return IdentityMatch(
        entity_kind="house", parse_rule="bare_bhava_subject",
        house_num=int(m.group(1)),
    )


def _r_bare_cusp(m: re.Match) -> IdentityMatch:
    return IdentityMatch(
        entity_kind="house", parse_rule="bare_cusp_subject",
        house_num=int(m.group(1)),
    )


def _r_bhava_arudha(m: re.Match) -> IdentityMatch:
    raw = m.group(1)
    h = 1 if raw == "L" else int(raw)
    return IdentityMatch(
        entity_kind="arudha_pada", parse_rule="bhava_arudha_a_n",
        house_num=h,
    )


def _r_arudha_pada(m: re.Match) -> IdentityMatch:
    raw = m.group(1)
    h = 1 if raw == "L" else int(raw)
    return IdentityMatch(
        entity_kind="arudha_pada", parse_rule="arudha_a_n",
        house_num=h,
    )


def _r_swamsa_house(m: re.Match) -> IdentityMatch:
    return IdentityMatch(
        entity_kind="swamsa_house", parse_rule="swamsa_house_n",
        house_num=int(m.group(1)),
    )


def _r_bare_sign_name(m: re.Match) -> IdentityMatch:
    return IdentityMatch(
        entity_kind="sign", parse_rule="bare_sign_name_subject",
        sign_num=SIGN_NAME_TO_NUM[m.group(0)],
    )


def _r_varga_graha_to_graha(m: re.Match) -> IdentityMatch:
    # Significator-path shape: `D<n>_<GRAHA>_to_<GRAHA>` (category
    # `significator_path`) — the shortest-argala-path graph edge between
    # two grahas within one varga.
    n, g1, g2 = m.group(1), m.group(2), m.group(3)
    return IdentityMatch(
        entity_kind="varga_graha_pair", parse_rule="varga_graha_to_graha",
        varga_id=f"D{n}", graha_code=g1, graha_code_secondary=g2,
    )


def _r_maitri_graha_pair(m: re.Match) -> IdentityMatch:
    # Panchadha Maitri (five-fold planetary friendship) subject shape:
    # `MAITRI_<GRAHA>_<GRAHA>`.
    g1, g2 = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="graha_pair", parse_rule="maitri_graha_pair",
        graha_code=g1, graha_code_secondary=g2,
    )


def _r_pakka_ghar_graha(m: re.Match) -> IdentityMatch:
    # Lal Kitab "permanent house" per graha: `PAKKA_GHAR_<GRAHA>`.
    return IdentityMatch(
        entity_kind="graha", parse_rule="pakka_ghar_graha",
        graha_code=m.group(1),
    )


def _r_arudha_graha_2letter(m: re.Match) -> IdentityMatch:
    # Graha-keyed Jaimini arudha pada: `ARUDHA_<2-letter code>` (e.g.
    # `ARUDHA_JU` = arudha with Jupiter as reference graha) — distinct
    # from the house-keyed `ARUDHA_A<n>` shape handled by `arudha_a_n`.
    graha = _canon_graha_token(m.group(1))
    return IdentityMatch(
        entity_kind="graha_arudha_pada", parse_rule="arudha_graha_2letter",
        graha_code=graha,
    )


def _r_bare_graha_pair_underscore(m: re.Match) -> IdentityMatch:
    g1, g2 = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="graha_pair", parse_rule="bare_graha_pair_underscore",
        graha_code=g1, graha_code_secondary=g2,
    )


def _r_graha_v_graha(m: re.Match) -> IdentityMatch:
    # `<GRAHA>_v_<GRAHA>` — graha_yuddha (planetary war) / combustion_
    # relationship subject shape (e.g. `VEN_v_MAR`, `SUN_v_MER`).
    g1, g2 = m.group(1), m.group(2)
    return IdentityMatch(
        entity_kind="graha_pair", parse_rule="graha_v_graha",
        graha_code=g1, graha_code_secondary=g2,
    )


def _r_bare_domain_word(m: re.Match) -> IdentityMatch | None:
    word = m.group(0)
    if word not in KNOWN_DOMAIN_WORDS:
        return None
    return IdentityMatch(entity_kind="domain", parse_rule="bare_domain_word")


# Ordered rule table. First match wins.
_SUBJECT_RULES: list[tuple[str, re.Pattern, "callable"]] = [
    ("varga_house_pair", re.compile(r"^D(\d{1,4})_HOUSE_0*(\d{1,2})_to_HOUSE_0*(\d{1,2})$"), _r_varga_house_pair),
    ("varga_graha_to_graha", re.compile(rf"^D(\d{{1,4}})_({_UNDERSCORE_GRAHA_ALT})_to_({_UNDERSCORE_GRAHA_ALT})$"), _r_varga_graha_to_graha),
    ("varga_sign_numeric", re.compile(r"^D(\d{1,4})_SIGN_0*(\d{1,2})$"), _r_varga_sign_numeric),
    ("varga_sign_name", re.compile(rf"^D(\d{{1,4}})_({_SIGN_NAME_ALT})$"), _r_varga_sign_name),
    ("varga_house_long", re.compile(r"^D(\d{1,4})_HOUSE_0*(\d{1,2})$"), _r_varga_house),
    ("varga_house_short", re.compile(r"^D(\d{1,4})_H0*(\d{1,2})$"), _r_varga_house_short),
    ("varga_graha_pair", re.compile(rf"^D(\d{{1,4}})_({_UNDERSCORE_GRAHA_ALT})_({_UNDERSCORE_GRAHA_ALT})$"), _r_varga_graha_pair),
    ("varga_graha_underscore", re.compile(rf"^D(\d{{1,4}})_({_UNDERSCORE_GRAHA_ALT})$"), _r_varga_graha),
    ("varga_graha_dot", re.compile(rf"^D(\d{{1,4}})\.({_UNDERSCORE_GRAHA_ALT})$"), _r_varga_graha_dot),
    ("varga_chart_subject", re.compile(r"^D(\d{1,4})_CHART$"), _r_varga_chart),
    ("bhava_arudha_a_n", re.compile(r"^BHAVA_ARUDHA_A(L|\d{1,2})$"), _r_bhava_arudha),
    ("arudha_a_n", re.compile(r"^ARUDHA_A(L|\d{1,2})$"), _r_arudha_pada),
    ("arudha_graha_2letter", re.compile(rf"^ARUDHA_({_TWO_LETTER_GRAHA_ALT})$"), _r_arudha_graha_2letter),
    ("swamsa_house_n", re.compile(r"^SWAMSA_HOUSE_0*(\d{1,2})$"), _r_swamsa_house),
    ("maitri_graha_pair", re.compile(rf"^MAITRI_({_UNDERSCORE_GRAHA_ALT})_({_UNDERSCORE_GRAHA_ALT})$"), _r_maitri_graha_pair),
    ("pakka_ghar_graha", re.compile(rf"^PAKKA_GHAR_({_UNDERSCORE_GRAHA_ALT})$"), _r_pakka_ghar_graha),
    ("hyphen_house", re.compile(r"^([A-Z_]+)-HOUSE_0*(\d{1,2})$"), _r_hyphen_house),
    ("hyphen_sign", re.compile(r"^([A-Z_]+)-SIGN_0*(\d{1,2})$"), _r_hyphen_sign),
    ("hyphen_graha_pair", re.compile(rf"^({_HYPHEN_GRAHA_ALT})-({_HYPHEN_GRAHA_ALT})$"), _r_hyphen_graha_pair),
    ("graha_in_house_underscore", re.compile(rf"^({_UNDERSCORE_GRAHA_ALT})_IN_HOUSE_0*(\d{{1,2}})$"), _r_graha_in_house_underscore),
    ("bare_graha_pair_underscore", re.compile(rf"^({_UNDERSCORE_GRAHA_ALT})_({_UNDERSCORE_GRAHA_ALT})$"), _r_bare_graha_pair_underscore),
    ("graha_v_graha", re.compile(rf"^({_UNDERSCORE_GRAHA_ALT})_v_({_UNDERSCORE_GRAHA_ALT})$"), _r_graha_v_graha),
    ("bare_house_subject", re.compile(r"^HOUSE_0*(\d{1,2})$"), _r_bare_house),
    ("bare_bhava_subject", re.compile(r"^BHAVA_0*(\d{1,2})$"), _r_bare_bhava),
    ("bare_cusp_subject", re.compile(r"^CUSP_0*(\d{1,2})$"), _r_bare_cusp),
    ("bare_sign_name_subject", re.compile(rf"^({_SIGN_NAME_ALT})$"), _r_bare_sign_name),
    # varga_domain is intentionally last among the D#_* rules: it is the
    # broadest D#_<word> catch-all and must not shadow the more specific
    # numeric/graha/sign/house shapes above.
    ("varga_domain_word", re.compile(r"^D(\d{1,4})_[a-z_]+$"), _r_varga_domain),
    # Bare lowercase domain word (no D#/varga prefix) — last: the broadest,
    # most permissive shape, gated by set-membership in the handler so an
    # unrecognized lowercase token still falls through as a real gap.
    ("bare_domain_word", re.compile(r"^[a-z_]+$"), _r_bare_domain_word),
]


def _parse_subject(fact_subject: str) -> IdentityMatch | None:
    for _name, pattern, handler in _SUBJECT_RULES:
        m = pattern.match(fact_subject)
        if m:
            result = handler(m)
            if result is not None:
                return result
    # Bare graha subject (SUN, MOON, ..., RAH_MEAN, KET_MEAN, LAGNA, MC).
    # Checked after the compound rules (a bare-graha regex would also
    # accidentally be a substring of nothing here since we require a full
    # match, but ordering keeps intent explicit: compounds are more
    # specific than atoms).
    if re.match(r"^[A-Z_]+$", fact_subject):
        graha = _canon_graha_token(fact_subject)
        if graha:
            return IdentityMatch(entity_kind="graha", parse_rule="bare_graha_subject", graha_code=graha)
    return None


# ── fact_key rules (narrow: identity-carrying keys only) ────────────────

_KEY_VARGA_RE = re.compile(r"^D(\d{1,4})$")
_KEY_HOUSE_RE = re.compile(r"^house_0*(\d{1,2})$")


def _parse_key_identity(fact_key: str) -> tuple[str, IdentityMatch] | tuple[None, None]:
    """Returns (dimension, partial IdentityMatch) for the narrow set of
    fact_key shapes that themselves carry varga/house identity, or
    (None, None) if fact_key is not one of those (the overwhelming common
    case — plain attribute names like 'grade', 'dignity_state', or matrix
    coordinates like 'h8_offset7' are NOT identity carriers; see module
    docstring's Scope boundary)."""
    if fact_key == "D_ALL":
        # Explicit floor marker — "all vargas", not a specific varga. Must
        # NOT be parsed as a literal varga id (see ga_condition_writer.py
        # ~1128 and the lane brief's explicit warning about this shape).
        return "varga_floor_all", None
    m = _KEY_VARGA_RE.match(fact_key)
    if m and int(m.group(1)) in ALL_30_VARGAS:
        return "varga", IdentityMatch(entity_kind="_partial_", parse_rule="bare_varga_key", varga_id=f"D{m.group(1)}")
    m = _KEY_HOUSE_RE.match(fact_key)
    if m:
        return "house", IdentityMatch(entity_kind="_partial_", parse_rule="bare_house_key", house_num=int(m.group(1)))
    return None, None


# ── Public API ────────────────────────────────────────────────────────

def parse_fact_identity(
    fact_subject: str | None, fact_key: str | None, fact_category: str | None = None,
) -> IdentityMatch | None:
    """The single entry point. Returns an IdentityMatch (with a
    `parse_rule` provenance string) if any graha/house/varga/sign identity
    dimension could be extracted from `fact_subject`/`fact_key`, else None.

    `fact_category` is currently unused by any rule (every rule so far is
    decidable from subject+key alone) but is accepted so a future rule that
    genuinely needs it (disambiguating two categories that reuse the same
    subject/key shape for different meanings) doesn't require a signature
    change at every call site.
    """
    if not fact_subject:
        return None
    fact_subject = fact_subject.strip()
    fact_key = (fact_key or "").strip()

    subj_match = _parse_subject(fact_subject)
    key_dim, key_partial = _parse_key_identity(fact_key) if fact_key else (None, None)

    if subj_match is not None:
        # Subject already yields a compound/rich shape -> key is not a
        # second identity carrier for these (it's almost always a plain
        # attribute name in that case); but a subject that resolved to a
        # BARE graha can still be enriched by a key-carried varga/house.
        if subj_match.entity_kind == "graha" and key_dim in ("varga", "house"):
            if key_dim == "varga":
                return replace(
                    subj_match, entity_kind="graha_in_varga",
                    parse_rule=f"{subj_match.parse_rule}+{key_partial.parse_rule}",
                    varga_id=key_partial.varga_id,
                )
            return replace(
                subj_match, entity_kind="graha_in_house",
                parse_rule=f"{subj_match.parse_rule}+{key_partial.parse_rule}",
                house_num=key_partial.house_num,
            )
        if subj_match.entity_kind == "graha" and key_dim == "varga_floor_all":
            # D_ALL: explicitly no specific varga — record the floor
            # explanation in parse_rule but do not fabricate a varga_id.
            return replace(subj_match, parse_rule=f"{subj_match.parse_rule}+d_all_floor_key")
        return subj_match

    # Subject alone didn't resolve to any dimension (it may still be a
    # recognized-but-dimensionless special-point/karaka/saham token, or a
    # genuinely unrecognized string) — key-derived identity, if any, still
    # counts as a real parse of this row.
    if key_dim == "varga":
        return IdentityMatch(entity_kind="varga", parse_rule=key_partial.parse_rule, varga_id=key_partial.varga_id)
    if key_dim == "house":
        return IdentityMatch(entity_kind="house", parse_rule=key_partial.parse_rule, house_num=key_partial.house_num)

    return None


_OPEN_ENDED_CATALOG_LABEL_CATEGORIES = frozenset({"yoga_label", "dosha_label"})


def classify_unparsed_subject(fact_subject: str, fact_category: str | None = None) -> str | None:
    """For a subject that `parse_fact_identity` could not resolve to any
    dimension, return a short classification label if it is a RECOGNIZED,
    genuinely identity-free token (special point / karaka role / saham /
    ashtakavarga or tajik degree-index / sade-sati cycle label), else None
    (meaning: a real candidate for the coverage report's gap list).

    `fact_category` is consulted for the two open-ended classical-label
    catalogs (`yoga_label`, `dosha_label`): these categories' subject is,
    BY THE CATEGORY'S OWN DEFINITION, always a yoga/dosha name (e.g.
    'malavya', 'daridra') drawn from an open-ended classical catalog that
    keeps growing (new yoga/dosha detectors landing over time) — enumerating
    every current member as a fixed set (as this module does for the
    genuinely-closed special-point/karaka-role lists above) would silently
    go stale the next time a new yoga/dosha label is added. Gating on the
    category is the honest, non-enumerable-set equivalent of the same
    "recognized token, no graha/house/varga digit in the text" reasoning.
    """
    if fact_category in _OPEN_ENDED_CATALOG_LABEL_CATEGORIES:
        return f"{fact_category}_catalog_label"
    if fact_subject in KNOWN_SPECIAL_POINTS:
        return "special_point_or_aggregate_marker"
    if fact_subject in KNOWN_KARAKA_ROLES:
        return "jaimini_karaka_role_label"
    if fact_subject in KNOWN_YOGA_DOSHA_LABELS:
        return "yoga_or_dosha_catalog_label"
    if fact_subject in KNOWN_AYURDAYA_LABELS:
        return "ayurdaya_method_label"
    if fact_subject.startswith("SAHAM_"):
        return "saham_arabic_part_label"
    if fact_subject.startswith(_REFERENCE_TABLE_PREFIXES):
        return "fixed_reference_lookup_table_row_not_natal_placement"
    if fact_subject.endswith("_BIRTH") or fact_subject.endswith("_BIRTH_DAY"):
        return "panchanga_constant_label"
    if re.match(r"^KAKSHYA_\d{1,2}$", fact_subject):
        return "ashtakavarga_kakshya_index_not_house"
    if re.match(r"^HADDA_\d{1,3}$", fact_subject):
        return "tajik_hadda_degree_term_index_not_house"
    if re.match(r"^CYCLE_\d{1,2}(\.(JANMA|ANUMUKHA|VISHAKHA)(\.(Q\d|RETRO_\d{1,2}))?)?$", fact_subject):
        return "sade_sati_cycle_phase_label_moon_relative_not_lagna_house"
    if re.match(r"^DHAIYA_\d{1,2}H_\d{1,3}$", fact_subject):
        return "dhaiya_subperiod_label_moon_relative_not_lagna_house"
    if re.match(r"^BHRIGU_CHAKRA_\d{1,2}$", fact_subject):
        return "bhrigu_nadi_chakra_index_not_house"
    if re.match(r"^[A-Z][a-z]*( [A-Z][a-z]*)*$", fact_subject) and fact_subject not in SIGN_NAME_TO_NUM:
        # A Title-Case word or space-separated two-word name that is not
        # one of the 12 rashi names — observed live as a bare nakshatra
        # name, both single-word ('Vishakha') and two-word compound
        # nakshatra names ('Purva Bhadrapada' — the native's own birth
        # Moon nakshatra, FORENSIC anchor #2). Nakshatra identity is a
        # genuine fifth dimension outside this lane's chartered
        # graha/house/varga/sign scope (MASTER_PLAN_v1_0.md §3 Lane A5) —
        # named honestly here rather than silently absorbed.
        return "nakshatra_name_fifth_dimension_out_of_scope"
    return None  # unrecognized token — real gap candidate
