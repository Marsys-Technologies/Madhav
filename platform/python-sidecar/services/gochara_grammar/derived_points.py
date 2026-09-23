"""
gochara_grammar.derived_points — M-6 derived transit targets (Phaladīpikā
Adh. XVII), pure sign-grain arithmetic shared by the resonance writer
(`services.ka_gochara_resonance.writer`) and the read-side resolver
(`services.gochara_intensity.enrichment`) so the two sides can never drift
(the codebase's drift-guarded-literal-copy pattern is replaced here by a
single importable source; both consumers are outside the I2-frozen
`gochara_grammar` engine surface, and this module is ADDITIVE — it changes
no existing behaviour).

Ruling basis (GOCHARA_RULING_SHEET_v2_0 §1 M-6; remainder brief §4.4):

  * Gulika/Māndi-derived points are admitted as transit targets ONLY for the
    classes the chapter names — death/māraka and acute illness
    (`bereavement`, `illness_acute`) — never as a general target.
  * The sign-distance target (Phaladīpikā XVII.26, served chunk `PG220:C1`
    śl.26, translation verified against the corpus source OCR
    in.ernet.dli.2015.92117):
        "Ascertain how far Mandi is removed from the lord of the 8th house.
         When Saturn in his transit arrives at a Rasi so far removed from
         Mandi, death may happen."
  * The Yamakaṇṭaka-difference rāśi spans (`PG214:C1` śl.6–8, `PG217:C1`
    śl.14, same OCR verification):
        śl.6   lagna-lord − Yamakaṇṭaka        → Jupiter transit → native's death
        śl.7   Sun − Yamakaṇṭaka               → Jupiter transit → father's death
        śl.7   Yamakaṇṭaka − Māndi             → Saturn transit  → father's death
        śl.8   5th-star-lord − Yamakaṇṭaka     → Jupiter transit → son's death
        śl.14  lagna-lord − Yamakaṇṭaka        → Jupiter in the indicated
                                                 navāṃśa → death (same formula
                                                 as śl.6's first clause; one
                                                 row cites both chunks).

Declared-coarser discipline (F-20, same as sign-level BAV interim):
  * The verses' "figures" carry degree precision, but the honestly served
    operands are sign-grain, so the DIFFERENCE is computed at sign grain and
    the emitted target is the indicated rāśi's whole-sign span. The verses'
    navāṃśa refinement is named here and in WP1_CONTRACTS §2.2 item 10 but
    is NOT emitted: a 3°20′ span cannot be honestly anchored from sign-grain
    operands. Never fabricate a midpoint point.
  * The trikona positions the verses also admit ("or their Trikona
    position") are NOT emitted as separate rows in v1 — the ruling's own
    paraphrase scopes admission to "the resulting rāśi/navāṃśa". Recorded
    here, deferred.
"""
from __future__ import annotations

SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Vimśottari nakṣatra-lord cycle (nakṣatra 1 = Aśvinī = Ketu). Standard
# served doctrine (production vimshottari daśā is built on the same table).
VIMSHOTTARI_NAKSHATRA_LORDS: tuple[str, ...] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
)

# The two event classes M-6 scopes every derived point to.
M6_EVENT_CLASSES: tuple[str, ...] = ("bereavement", "illness_acute")

MANDI_DISTANCE_REF = "mandi_sign_distance_from_8L"
MANDI_DISTANCE_CITATION = "PG220:C1 śl.26"
MANDI_DISTANCE_AGENT = "Saturn"

# The four Yamakaṇṭaka-difference formulas. `minuend`/`subtrahend` are operand
# roles the caller resolves to sign numbers:
#   lagna_lord       — lord of the lagna sign (L0 reference_signs)
#   Sun              — the Sun's own sign
#   yamakantaka      — L1 sensitive_point_gulika_mandi[YAMAKANTAKA].sign
#   mandi            — L1 sensitive_point_gulika_mandi[MANDI].sign
#   fifth_star_lord  — Vimśottari lord of the 5th nakṣatra from the natal
#                      Moon nakṣatra (natal counts as 1), resolved to its sign
YAMAKANTAKA_FORMULAS: tuple[dict, ...] = (
    {
        "ref": "lagna_lord_minus_yamakantaka",
        "minuend": "lagna_lord",
        "subtrahend": "yamakantaka",
        "agent": "Jupiter",
        "event": "native_death",
        "citation": "PG214:C1 śl.6; PG217:C1 śl.14",
    },
    {
        "ref": "sun_minus_yamakantaka",
        "minuend": "Sun",
        "subtrahend": "yamakantaka",
        "agent": "Jupiter",
        "event": "father_death",
        "citation": "PG214:C1 śl.7",
    },
    {
        "ref": "yamakantaka_minus_mandi",
        "minuend": "yamakantaka",
        "subtrahend": "mandi",
        "agent": "Saturn",
        "event": "father_death",
        "citation": "PG214:C1 śl.7",
    },
    {
        "ref": "panchama_tara_lord_minus_yamakantaka",
        "minuend": "fifth_star_lord",
        "subtrahend": "yamakantaka",
        "agent": "Jupiter",
        "event": "son_death",
        "citation": "PG214:C1 śl.8",
    },
)


def sign_num_of(sign_name: str) -> int | None:
    """1-based sign number (Aries=1 … Pisces=12); None for an unknown name."""
    try:
        return SIGNS.index(sign_name) + 1
    except ValueError:
        return None


def sign_name_of(sign_num: int) -> str:
    """Sign name for a 1-based sign number."""
    return SIGNS[(int(sign_num) - 1) % 12]


def difference_sign_num(minuend_sign_num: int, subtrahend_sign_num: int) -> int:
    """Rāśi indicated by 'subtract the figures of B from those of A' at sign
    grain: (A − B) mod 12, with 0 read as 12 (Pisces). Whole-sign subtraction
    matches the classical figures subtraction when degrees are dropped:
    A.00 − B.00 ≡ (A−B) mod 12 signs from Aries."""
    d = (int(minuend_sign_num) - int(subtrahend_sign_num)) % 12
    return d if d != 0 else 12


def mandi_distance_target_sign_num(eighth_lord_sign_num: int, mandi_sign_num: int) -> int:
    """Phaladīpikā XVII.26: N = forward zodiacal distance from the 8th lord's
    sign to Māndi's sign (0 when they tenant the same sign); the target is the
    sign N removed from Māndi in the same forward direction. N=0 therefore
    yields Māndi's own sign — the literal reading of 'a Rasi so far removed
    from Mandi'."""
    n = (int(mandi_sign_num) - int(eighth_lord_sign_num)) % 12
    return (int(mandi_sign_num) - 1 + n) % 12 + 1


def nakshatra_lord(nakshatra_id: int) -> str:
    """Vimśottari lord of nakṣatra `nakshatra_id` (1-based, Aśvinī=1)."""
    return VIMSHOTTARI_NAKSHATRA_LORDS[(int(nakshatra_id) - 1) % 9]


def fifth_star_lord(natal_moon_nakshatra_id: int) -> str:
    """'The planet ruling the 5th star reckoned from the natal one'
    (PG214:C1 śl.8): the natal nakṣatra counts as the 1st, so the 5th is
    natal+4; lord per the Vimśottari table."""
    fifth = (int(natal_moon_nakshatra_id) - 1 + 4) % 27 + 1
    return nakshatra_lord(fifth)
