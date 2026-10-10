"""
test_l0_rules_descriptions_golden.py -- golden pins for the composed
``predicate_jsonb.description`` of every bg_rules extractor (27 patterns).

Why (SS N-457, CLAUDE.md N.7.6 "an honest null beats an invented judgment"):

  * A description must never carry a placeholder word that reads like a real
    value. Two stand-ins existed: P21 wrote "bhava" when the house/sign was
    vague ("that bhava"), and P5 wrote "subject" when the aspect target was
    unresolved. Unresolved values are now stated explicitly.
  * Graha tokens in descriptions use the canonical L1 Title spelling
    (``Jupiter``), routed through brahmagyan.graha_vocabulary. The rule's
    antecedent keys (lower-case canonical planet names) and therefore the
    content-hash ``rule_id`` are NOT touched by this.

Each test drives the registered regex + extractor from ``l0_rules.PATTERNS``
with a fixed input and pins the exact description string. Input texts use
alias spellings (Guru, Surya, Chandra, ...) so the canonicalisation path is
exercised, not just the English names.
"""
from __future__ import annotations

import pytest

from brahmagyan import l0_rules as mod

_BY_NAME = {name: (rx, fn) for name, rx, fn in mod.PATTERNS}

# (pattern name, input text, exact pinned description)
GOLDEN: list[tuple[str, str, str]] = [
    ("planet_in_house", "Guru in the fifth house gives wealth.", "Jupiter in house 5"),
    ("planet_in_sign", "Surya in Aries gives courage.", "Sun in sign Aries"),
    ("lord_placement", "The lord of the second in the tenth house gives fame.", "lord of 2 in house 10"),
    ("conjunction", "Chandra with Mangal gives courage.", "Moon conjunct Mars"),
    ("aspect", "Shani aspects Venus and gives delay.", "Saturn aspects Venus"),
    ("dignity_placement", "Shukra in exaltation gives luxury.", "Venus in exaltation"),
    ("dasha_rule", "During Budha dasha period the native gives gains.", "Mercury mahadasha period"),
    ("transit_rule", "When Guru transits Aries gives gains.", "Jupiter transits"),
    ("house_from_reference", "Mars in the fourth from Surya gives heat.", "Mars in 4th from Sun"),
    ("benefic_malefic_aspect", "Malefic aspects Saturn gives pain.", "malefic aspects"),
    ("kartari", "Chandra hemmed between malefics gives sorrow.", "Moon in kartari"),
    ("retrograde", "Budha retrograde gives delay.", "Mercury retrograde"),
    ("combustion", "Shukra combust gives loss.", "Venus combust"),
    ("planet_in_house_direct", "Shani placed in the seventh house gives delay.", "Saturn in house 7 (direct)"),
    ("conditional_if", "If the Chandra is in Aries, one will be bold.", "if Moon in sign Aries"),
    ("aspected_by", "Chandra aspected by Mangal, one will win.", "Moon aspected by Mars"),
    ("conditional_should", "Should the Surya be in Leo, one will rule.", "should Sun be in sign Leo"),
    ("dual_planet_in_house", "Surya and Budha in the tenth house gives fame.", "Sun and Mercury in house 10"),
    ("planet_in_sign_aspected", "Chandra in Aries in aspect to Mangal gives courage.", "Moon in Aries aspected by Mars"),
    ("strength_state", "Strong Guru gives wealth.", "strong Jupiter"),
    ("conditional_when", "When Mangal is in the fifth house, he will become odious.", "when Mars in house 5"),
    ("person_born_will", "Guru be in the seventh house, the person born will be sceptical.", "Jupiter in house 7 — person born will"),
    ("planet_in_bhava", "Shukra in the fifth bhava gives joy.", "Venus in 5th bhava"),
    ("when_planet_in_sign", "When the Chandra occupies Taurus the person born will rise.", "when Moon occupies Taurus"),
    ("nadi_planet_pair_in_sign", "Surya and Chandra in Aries gives power.", "Nadi: Sun and Moon in sign 1"),
    ("nadi_navamsa_placement", "In the Navamsa Guru occupies Sagittarius.", "Nadi Navamsa: Jupiter in sign 9 (D9)"),
    ("nadi_triple_conjunction_in_sign", "Surya, Chandra, Mangal and Shukra in Cancer gives power.", "Nadi triple: Sun+Moon+Mars in sign 4"),
]


def _describe(name: str, text: str) -> dict:
    rx, fn = _BY_NAME[name]
    m = rx.search(text)
    assert m is not None, f"{name}: golden input no longer matches the pattern"
    row = fn(m, text)
    assert row is not None, f"{name}: extractor rejected the golden input"
    return row


def test_golden_covers_all_27_extractors():
    assert len(mod.PATTERNS) == 27
    assert [g[0] for g in GOLDEN] == [p[0] for p in mod.PATTERNS]


@pytest.mark.parametrize("name,text,expected", GOLDEN, ids=[g[0] for g in GOLDEN])
def test_description_golden(name, text, expected):
    assert _describe(name, text)["predicate"]["description"] == expected


# ── unresolved-value cases: explicit absence, never a value-shaped word ─────


def test_p21_vague_house_or_sign_is_explicit_not_bhava():
    row = _describe("conditional_when", "When Mars is in that bhava, he will become odious.")
    assert row["predicate"]["description"] == "when Mars in house or sign unresolved"
    # the antecedent still carries no location, as before
    assert row["antecedent"] == [{"planet": "mars", "relation": "occupies"}]


def test_p21_vague_same_sign_reference_is_explicit():
    row = _describe("conditional_when", "If Guru is in the same sign, one will prosper.")
    assert row["predicate"]["description"] == "when Jupiter in house or sign unresolved"


def test_p21_resolved_sign_is_still_stated():
    row = _describe("conditional_when", "When Shani is in Capricorn, he will be grave.")
    assert row["predicate"]["description"] == "when Saturn in sign Capricorn"


class _StubMatch:
    """Minimal re.Match stand-in so an extractor can be fed groups the regex
    itself never produces (an unresolvable aspect target)."""

    def __init__(self, groups: dict[int, str | None], whole: str = "stub"):
        self._groups = groups
        self._whole = whole

    def group(self, i: int = 0):
        return self._whole if i == 0 else self._groups.get(i)

    def end(self) -> int:
        return len(self._whole)


def test_p5_unresolved_target_is_explicit_not_subject():
    m = _StubMatch({1: "Shani", 2: None, 3: None})
    row = mod._p5_extract(m, "Shani aspects x gives y")
    assert row["predicate"]["description"] == "Saturn aspects target unresolved"
    assert row["antecedent"] == [{"planet": "saturn", "relation": "aspects"}]


def test_p5_unparseable_house_token_is_unresolved_not_subject():
    m = _StubMatch({1: "Shani", 2: None, 3: "zeroth"})
    row = mod._p5_extract(m, "Shani aspects zeroth house gives y")
    assert row["predicate"]["description"] == "Saturn aspects target unresolved"


def test_p5_house_target_is_still_stated():
    row = _describe("aspect", "Guru aspects the seventh house and gives marriage.")
    assert row["predicate"]["description"] == "Jupiter aspects house 7"


# ── graha spelling: canonical Title, unrecognised stays unchanged ───────────


@pytest.mark.parametrize(
    "token,label",
    [
        ("jupiter", "Jupiter"), ("guru", "Jupiter"), ("Shani", "Saturn"),
        ("surya", "Sun"), ("mangal", "Mars"), ("rahu", "Rahu"),
        ("lagna", "Lagna"), ("ascendant", "Lagna"),
    ],
)
def test_graha_label_recognised(token, label):
    assert mod._graha_label(token) == label


@pytest.mark.parametrize("token", ["xyzzy", "the house", "lorem ipsum", ""])
def test_graha_label_unrecognised_unchanged_never_title_cased(token):
    assert mod._graha_label(token) == token


def test_p9_lagna_reference_is_canonical():
    row = _describe("house_from_reference", "Mars in the fourth from Lagna gives heat.")
    assert row["predicate"]["description"] == "Mars in 4th from Lagna"
    row = _describe("house_from_reference", "Mars in the fourth from the ascendant gives heat.")
    assert row["predicate"]["description"] == "Mars in 4th from Lagna"


def test_antecedent_keys_and_rule_identity_are_unchanged():
    """Only the description text changed: antecedent planet keys stay the
    lower-case canonical names, so content-hash rule ids are not re-keyed."""
    row = _describe("planet_in_house", "Guru in the fifth house gives wealth.")
    assert row["antecedent"] == [{"planet": "jupiter", "house": 5, "relation": "occupies"}]
    row = _describe("house_from_reference", "Mars in the fourth from Surya gives heat.")
    assert row["antecedent"][0]["reference"] == "surya"
    row = _describe("nadi_triple_conjunction_in_sign", "Surya, Chandra, Mangal and Shukra in Cancer gives power.")
    assert [a["planet"] for a in row["antecedent"]] == ["sun", "moon", "mars"]
