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

Each test calls ONE extractor directly (``mod._pN_extract(mod._PN.search(text), text)``)
with a fixed input and pins the exact description string. Input texts use
alias spellings (Guru, Surya, Chandra, ...) so the canonicalisation path is
exercised, not just the English names.
"""
from __future__ import annotations

import pytest

from brahmagyan import l0_rules as mod

# ── one pinned description per extractor (direct calls) ─────────────────────


def test_p1_planet_in_house_description():
    text = 'Guru in the fifth house gives wealth.'
    m = mod._P1.search(text)
    assert m is not None, "golden input no longer matches _P1"
    row = mod._p1_extract(m, text)
    assert row["predicate"]["description"] == 'Jupiter in house 5'


def test_p2_planet_in_sign_description():
    text = 'Surya in Aries gives courage.'
    m = mod._P2.search(text)
    assert m is not None, "golden input no longer matches _P2"
    row = mod._p2_extract(m, text)
    assert row["predicate"]["description"] == 'Sun in sign Aries'


def test_p3_lord_placement_description():
    text = 'The lord of the second in the tenth house gives fame.'
    m = mod._P3.search(text)
    assert m is not None, "golden input no longer matches _P3"
    row = mod._p3_extract(m, text)
    assert row["predicate"]["description"] == 'lord of 2 in house 10'


def test_p4_conjunction_description():
    text = 'Chandra with Mangal gives courage.'
    m = mod._P4.search(text)
    assert m is not None, "golden input no longer matches _P4"
    row = mod._p4_extract(m, text)
    assert row["predicate"]["description"] == 'Moon conjunct Mars'


def test_p5_aspect_description():
    text = 'Shani aspects Venus and gives delay.'
    m = mod._P5.search(text)
    assert m is not None, "golden input no longer matches _P5"
    row = mod._p5_extract(m, text)
    assert row["predicate"]["description"] == 'Saturn aspects Venus'


def test_p6_dignity_placement_description():
    text = 'Shukra in exaltation gives luxury.'
    m = mod._P6.search(text)
    assert m is not None, "golden input no longer matches _P6"
    row = mod._p6_extract(m, text)
    assert row["predicate"]["description"] == 'Venus in exaltation'


def test_p7_dasha_rule_description():
    text = 'During Budha dasha period the native gives gains.'
    m = mod._P7.search(text)
    assert m is not None, "golden input no longer matches _P7"
    row = mod._p7_extract(m, text)
    assert row["predicate"]["description"] == 'Mercury mahadasha period'


def test_p8_transit_rule_description():
    text = 'When Guru transits Aries gives gains.'
    m = mod._P8.search(text)
    assert m is not None, "golden input no longer matches _P8"
    row = mod._p8_extract(m, text)
    assert row["predicate"]["description"] == 'Jupiter transits'


def test_p9_house_from_reference_description():
    text = 'Mars in the fourth from Surya gives heat.'
    m = mod._P9.search(text)
    assert m is not None, "golden input no longer matches _P9"
    row = mod._p9_extract(m, text)
    assert row["predicate"]["description"] == 'Mars in 4th from Sun'


def test_p10_benefic_malefic_aspect_description():
    text = 'Malefic aspects Saturn gives pain.'
    m = mod._P10.search(text)
    assert m is not None, "golden input no longer matches _P10"
    row = mod._p10_extract(m, text)
    assert row["predicate"]["description"] == 'malefic aspects'


def test_p11_kartari_description():
    text = 'Chandra hemmed between malefics gives sorrow.'
    m = mod._P11.search(text)
    assert m is not None, "golden input no longer matches _P11"
    row = mod._p11_extract(m, text)
    assert row["predicate"]["description"] == 'Moon in kartari'


def test_p12_retrograde_description():
    text = 'Budha retrograde gives delay.'
    m = mod._P12.search(text)
    assert m is not None, "golden input no longer matches _P12"
    row = mod._p12_extract(m, text)
    assert row["predicate"]["description"] == 'Mercury retrograde'


def test_p13_combustion_description():
    text = 'Shukra combust gives loss.'
    m = mod._P13.search(text)
    assert m is not None, "golden input no longer matches _P13"
    row = mod._p13_extract(m, text)
    assert row["predicate"]["description"] == 'Venus combust'


def test_p14_planet_in_house_direct_description():
    text = 'Shani placed in the seventh house gives delay.'
    m = mod._P14.search(text)
    assert m is not None, "golden input no longer matches _P14"
    row = mod._p14_extract(m, text)
    assert row["predicate"]["description"] == 'Saturn in house 7 (direct)'


def test_p15_conditional_if_description():
    text = 'If the Chandra is in Aries, one will be bold.'
    m = mod._P15.search(text)
    assert m is not None, "golden input no longer matches _P15"
    row = mod._p15_extract(m, text)
    assert row["predicate"]["description"] == 'if Moon in sign Aries'


def test_p16_aspected_by_description():
    text = 'Chandra aspected by Mangal, one will win.'
    m = mod._P16.search(text)
    assert m is not None, "golden input no longer matches _P16"
    row = mod._p16_extract(m, text)
    assert row["predicate"]["description"] == 'Moon aspected by Mars'


def test_p17_conditional_should_description():
    text = 'Should the Surya be in Leo, one will rule.'
    m = mod._P17.search(text)
    assert m is not None, "golden input no longer matches _P17"
    row = mod._p17_extract(m, text)
    assert row["predicate"]["description"] == 'should Sun be in sign Leo'


def test_p18_dual_planet_in_house_description():
    text = 'Surya and Budha in the tenth house gives fame.'
    m = mod._P18.search(text)
    assert m is not None, "golden input no longer matches _P18"
    row = mod._p18_extract(m, text)
    assert row["predicate"]["description"] == 'Sun and Mercury in house 10'


def test_p19_planet_in_sign_aspected_description():
    text = 'Chandra in Aries in aspect to Mangal gives courage.'
    m = mod._P19.search(text)
    assert m is not None, "golden input no longer matches _P19"
    row = mod._p19_extract(m, text)
    assert row["predicate"]["description"] == 'Moon in Aries aspected by Mars'


def test_p20_strength_state_description():
    text = 'Strong Guru gives wealth.'
    m = mod._P20.search(text)
    assert m is not None, "golden input no longer matches _P20"
    row = mod._p20_extract(m, text)
    assert row["predicate"]["description"] == 'strong Jupiter'


def test_p21_conditional_when_description():
    text = 'When Mangal is in the fifth house, he will become odious.'
    m = mod._P21.search(text)
    assert m is not None, "golden input no longer matches _P21"
    row = mod._p21_extract(m, text)
    assert row["predicate"]["description"] == 'when Mars in house 5'


def test_p22_person_born_will_description():
    text = 'Guru be in the seventh house, the person born will be sceptical.'
    m = mod._P22.search(text)
    assert m is not None, "golden input no longer matches _P22"
    row = mod._p22_extract(m, text)
    assert row["predicate"]["description"] == 'Jupiter in house 7 — person born will'


def test_p23_planet_in_bhava_description():
    text = 'Shukra in the fifth bhava gives joy.'
    m = mod._P23.search(text)
    assert m is not None, "golden input no longer matches _P23"
    row = mod._p23_extract(m, text)
    assert row["predicate"]["description"] == 'Venus in 5th bhava'


def test_p24_when_planet_in_sign_description():
    text = 'When the Chandra occupies Taurus the person born will rise.'
    m = mod._P24.search(text)
    assert m is not None, "golden input no longer matches _P24"
    row = mod._p24_extract(m, text)
    assert row["predicate"]["description"] == 'when Moon occupies Taurus'


def test_p25_nadi_planet_pair_in_sign_description():
    text = 'Surya and Chandra in Aries gives power.'
    m = mod._P25.search(text)
    assert m is not None, "golden input no longer matches _P25"
    row = mod._p25_extract(m, text)
    assert row["predicate"]["description"] == 'Nadi: Sun and Moon in sign 1'


def test_p26_nadi_navamsa_placement_description():
    text = 'In the Navamsa Guru occupies Sagittarius.'
    m = mod._P26.search(text)
    assert m is not None, "golden input no longer matches _P26"
    row = mod._p26_extract(m, text)
    assert row["predicate"]["description"] == 'Nadi Navamsa: Jupiter in sign 9 (D9)'


def test_p27_nadi_triple_conjunction_in_sign_description():
    text = 'Surya, Chandra, Mangal and Shukra in Cancer gives power.'
    m = mod._P27.search(text)
    assert m is not None, "golden input no longer matches _P27"
    row = mod._p27_extract(m, text)
    assert row["predicate"]["description"] == 'Nadi triple: Sun+Moon+Mars in sign 4'


def test_golden_covers_all_27_extractors():
    assert len(mod.PATTERNS) == 27
    assert [p[0] for p in mod.PATTERNS] == ['planet_in_house', 'planet_in_sign', 'lord_placement', 'conjunction', 'aspect', 'dignity_placement', 'dasha_rule', 'transit_rule', 'house_from_reference', 'benefic_malefic_aspect', 'kartari', 'retrograde', 'combustion', 'planet_in_house_direct', 'conditional_if', 'aspected_by', 'conditional_should', 'dual_planet_in_house', 'planet_in_sign_aspected', 'strength_state', 'conditional_when', 'person_born_will', 'planet_in_bhava', 'when_planet_in_sign', 'nadi_planet_pair_in_sign', 'nadi_navamsa_placement', 'nadi_triple_conjunction_in_sign']
    for i, (_, rx, fn) in enumerate(mod.PATTERNS, 1):
        assert rx is getattr(mod, f"_P{i}") and fn is getattr(mod, f"_p{i}_extract")


# ── unresolved-value cases: explicit absence, never a value-shaped word ─────


def test_p21_vague_house_or_sign_is_explicit_not_bhava():
    text = "When Mars is in that bhava, he will become odious."
    row = mod._p21_extract(mod._P21.search(text), text)
    assert row["predicate"]["description"] == "when Mars in house or sign unresolved"
    # the antecedent still carries no location, as before
    assert row["antecedent"] == [{"planet": "mars", "relation": "occupies"}]


def test_p21_vague_same_sign_reference_is_explicit():
    text = "If Guru is in the same sign, one will prosper."
    row = mod._p21_extract(mod._P21.search(text), text)
    assert row["predicate"]["description"] == "when Jupiter in house or sign unresolved"


def test_p21_resolved_sign_is_still_stated():
    text = "When Shani is in Capricorn, he will be grave."
    row = mod._p21_extract(mod._P21.search(text), text)
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
    text = "Guru aspects the seventh house and gives marriage."
    row = mod._p5_extract(mod._P5.search(text), text)
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
    text = "Mars in the fourth from Lagna gives heat."
    row = mod._p9_extract(mod._P9.search(text), text)
    assert row["predicate"]["description"] == "Mars in 4th from Lagna"
    text = "Mars in the fourth from the ascendant gives heat."
    row = mod._p9_extract(mod._P9.search(text), text)
    assert row["predicate"]["description"] == "Mars in 4th from Lagna"


def test_antecedent_keys_and_rule_identity_are_unchanged():
    """Only the description text changed: antecedent planet keys stay the
    lower-case canonical names, so content-hash rule ids are not re-keyed."""
    text = "Guru in the fifth house gives wealth."
    row = mod._p1_extract(mod._P1.search(text), text)
    assert row["antecedent"] == [{"planet": "jupiter", "house": 5, "relation": "occupies"}]
    text = "Mars in the fourth from Surya gives heat."
    row = mod._p9_extract(mod._P9.search(text), text)
    assert row["antecedent"][0]["reference"] == "surya"
    text = "Surya, Chandra, Mangal and Shukra in Cancer gives power."
    row = mod._p27_extract(mod._P27.search(text), text)
    assert [a["planet"] for a in row["antecedent"]] == ["sun", "moon", "mars"]
