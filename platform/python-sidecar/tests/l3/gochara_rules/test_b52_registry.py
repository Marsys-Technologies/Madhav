"""B5.2 merge tests — cited registry content from PROMISE_NATURE_YOGA_MAP_v1_1.

§5 kāraka sets, §6 yoga→event map, §2–§3 nature/maitrī factors and the
naisargika table, §1.1/§4.11 dignity and ṣaḍbala scales, §4.2 dignity data.

Count note (flagged to the steward): the campaign instruction says "the 8
entries of §6", but §6's table carries 7 rows and 9 DISTINCT yoga_ids (the
last row names Y-SUNAPHA / Y-ANAPHA / Y-DURADHARA). The registry stores one
row per yoga_id ⇒ exactly 9 entries; the full id set is asserted verbatim.
§5 likewise assigns Jupiter AND Mercury to the education classes (śl.4–5);
the artifact is followed over the instruction's summary.
"""
from __future__ import annotations

import pytest

from services.gochara_rules.dignity import (
    DEBILITY, EXALTATION, MULATRIKONA, dignity_of,
)
from services.gochara_rules.nature import (
    NON_NODE_GRAHAS, agent_nature, mercury_affiliation, moon_paksa,
    naisargika_maitri_from_rows, naisargika_relation,
)
from services.gochara_rules.registry import (
    CLASS_BY_NAME, FACTORS, KARAKA_SETS, KARAKA_UNATTACHED, RULE_PATHS,
    YOGA_EVENT_MAP, _karaka_row, _yoga_row,
)

EXPECTED_YOGA_IDS = {
    "Y-MARRIAGE-T1", "Y-MARRIAGE-D1", "Y-MARRIAGE-DT1", "Y-MARRIAGE-COND",
    "Y-ADHI", "Y-DHANA", "Y-SUNAPHA", "Y-ANAPHA", "Y-DURADHARA",
}


# ── §5 kāraka sets ───────────────────────────────────────────────────────────
def test_karaka_marriage_venus_with_citation():
    ks = KARAKA_SETS["marriage"]
    assert ks["state"] == "computed"
    (row,) = ks["karakas"]
    assert row["karaka"] == "Venus"
    assert row["provenance"] == "verse_cited"
    assert row["citation"]["text"] == "phaladeepika"
    assert row["citation"]["locator"] == "PG49:C1"
    assert row["citation"]["sloka"] == 6


def test_karaka_sets_match_artifact():
    def karakas(cls):
        return [r["karaka"] for r in KARAKA_SETS[cls]["karakas"]]
    assert karakas("romantic_start") == ["Venus"]
    assert karakas("bereavement") == ["Sun"]
    assert karakas("parental_event") == ["Sun", "Moon"]  # father + mother
    assert karakas("childbirth") == ["Jupiter"]
    # education: Jupiter (śl.5) AND Mercury (śl.4) per the artifact
    assert karakas("education_milestone") == ["Jupiter", "Mercury"]
    assert karakas("exam_outcome") == ["Jupiter", "Mercury"]
    for cls in ("illness_acute", "chronic_onset", "surgery"):
        assert karakas(cls) == ["Saturn"]
    for cls in ("career_entry", "career_advancement", "career_change",
                "career_setback", "achievement_recognition"):
        assert karakas(cls) == ["Sun"]
    assert karakas("major_gain") == ["Venus"]
    assert karakas("major_loss") == ["Venus"]
    # Mars (brothers, PG47:C1 śl.3) recorded-but-unused
    (mars,) = KARAKA_UNATTACHED
    assert mars["karaka"] == "Mars" and mars["citation"]["locator"] == "PG47:C1"


def test_karaka_computed_empty_stays_empty():
    # a class with no cited kāraka stays computed_empty
    assert KARAKA_SETS["spiritual_turn"] == {
        "state": "computed_empty", "karakas": [],
        "source": KARAKA_SETS["marriage"]["source"]}
    # every one of the 27 classes carries one of the two tagged states
    for name in CLASS_BY_NAME:
        assert KARAKA_SETS[name]["state"] in ("computed", "computed_empty")


def test_karaka_row_without_citation_rejected():
    # mutation: a kāraka row without a citation must fail at write time
    with pytest.raises(ValueError):
        _karaka_row("Mars", None, 3, "no locator")
    with pytest.raises(ValueError):
        _karaka_row("Mars", "PG47:C1", None, "no śloka")


# ── §6 yoga→event map ────────────────────────────────────────────────────────
def test_yoga_map_entries_verse_cited_with_locators():
    assert set(YOGA_EVENT_MAP) == EXPECTED_YOGA_IDS
    # 9 distinct yoga_ids from §6's 7 table rows (see module docstring)
    assert len(YOGA_EVENT_MAP) == 9
    for row in YOGA_EVENT_MAP.values():
        assert row["provenance"] == "verse_cited"
        assert row["citation"]["locator"]
        assert row["citation"]["sloka"]
        for cls in row["event_classes"]:
            assert cls in CLASS_BY_NAME
    # Y-ADHI carries the ocr_degradation flag on the house list
    assert YOGA_EVENT_MAP["Y-ADHI"]["ocr_degradation"]
    assert YOGA_EVENT_MAP["Y-ADHI"]["citation"]["locator"] == "PG384:C1"


def test_yoga_map_excludes_orr5_synthetic_fixture():
    # the O-RR-5 fixture yoga ("7L Venus conjunct exalted Jupiter in the 9th")
    # is synthetic-only — it enters no registry row
    for row in YOGA_EVENT_MAP.values():
        assert "exalted Jupiter" not in row["definition"]
        assert "7L Venus conjunct" not in row["definition"]


def test_yoga_row_verse_cited_without_locator_rejected():
    # mutation: verse_cited with no locator fails validation
    with pytest.raises(ValueError):
        _yoga_row("Y-BOGUS", "invented yoga", ["marriage"], None, "1")
    # unknown event class is likewise rejected
    with pytest.raises(ValueError):
        _yoga_row("Y-BOGUS", "x", ["not_a_class"], "PG1:C1", "1")


# ── §3.1 naisargika maitrī table ─────────────────────────────────────────────
# Fixture snapshot of the derived table (BPHS ch.3 śl.55 [D] PG39:C1, with
# the Moon row's PG40:C1 exception) — it lived in services/gochara_rules/
# nature.py as a module constant until Pravāha C10 (2026-10-02); production
# now loads the mapping from the L0 rows of bg_graha_naisargika_friendship
# (migration 250) via naisargika_maitri_from_rows, and this snapshot is the
# test-only pin the loader output is checked against.
NAISARGIKA_MAITRI: dict[str, dict[str, frozenset[str]]] = {
    "Sun": {"friends": frozenset({"Moon", "Mars", "Jupiter"}),
            "enemies": frozenset({"Venus", "Saturn"}),
            "neutral": frozenset({"Mercury"})},
    "Moon": {"friends": frozenset({"Sun", "Mercury"}),
             "enemies": frozenset(),  # the text's own exception (PG40:C1)
             "neutral": frozenset({"Mars", "Jupiter", "Venus", "Saturn"})},
    "Mars": {"friends": frozenset({"Sun", "Moon", "Jupiter"}),
             "enemies": frozenset({"Mercury"}),
             "neutral": frozenset({"Venus", "Saturn"})},
    "Mercury": {"friends": frozenset({"Sun", "Venus"}),
                "enemies": frozenset({"Moon"}),
                "neutral": frozenset({"Mars", "Jupiter", "Saturn"})},
    "Jupiter": {"friends": frozenset({"Sun", "Moon", "Mars"}),
                "enemies": frozenset({"Mercury", "Venus"}),
                "neutral": frozenset({"Saturn"})},
    "Venus": {"friends": frozenset({"Mercury", "Saturn"}),
              "enemies": frozenset({"Sun", "Moon"}),
              "neutral": frozenset({"Mars", "Jupiter"})},
    "Saturn": {"friends": frozenset({"Mercury", "Venus"}),
               "enemies": frozenset({"Sun", "Moon", "Mars"}),
               "neutral": frozenset({"Jupiter"})},
}

# The 42 non-node rows of bg_graha_naisargika_friendship, copied verbatim
# (graha, other_graha, relation) from migration 250 — the L0 source the
# production loader reads. Stream B verified read-only (2026-10) that all 42
# non-node pairs agree with the derived snapshot above.
L0_NAISARGIKA_ROWS = [
    ("Sun", "Moon", "friend"), ("Sun", "Mars", "friend"),
    ("Sun", "Jupiter", "friend"), ("Sun", "Mercury", "neutral"),
    ("Sun", "Venus", "enemy"), ("Sun", "Saturn", "enemy"),
    ("Moon", "Sun", "friend"), ("Moon", "Mercury", "friend"),
    ("Moon", "Mars", "neutral"), ("Moon", "Jupiter", "neutral"),
    ("Moon", "Venus", "neutral"), ("Moon", "Saturn", "neutral"),
    ("Mars", "Sun", "friend"), ("Mars", "Moon", "friend"),
    ("Mars", "Jupiter", "friend"), ("Mars", "Venus", "neutral"),
    ("Mars", "Saturn", "neutral"), ("Mars", "Mercury", "enemy"),
    ("Mercury", "Sun", "friend"), ("Mercury", "Venus", "friend"),
    ("Mercury", "Mars", "neutral"), ("Mercury", "Jupiter", "neutral"),
    ("Mercury", "Saturn", "neutral"), ("Mercury", "Moon", "enemy"),
    ("Jupiter", "Sun", "friend"), ("Jupiter", "Moon", "friend"),
    ("Jupiter", "Mars", "friend"), ("Jupiter", "Saturn", "neutral"),
    ("Jupiter", "Mercury", "enemy"), ("Jupiter", "Venus", "enemy"),
    ("Venus", "Mercury", "friend"), ("Venus", "Saturn", "friend"),
    ("Venus", "Mars", "neutral"), ("Venus", "Jupiter", "neutral"),
    ("Venus", "Sun", "enemy"), ("Venus", "Moon", "enemy"),
    ("Saturn", "Mercury", "friend"), ("Saturn", "Venus", "friend"),
    ("Saturn", "Jupiter", "neutral"), ("Saturn", "Sun", "enemy"),
    ("Saturn", "Moon", "enemy"), ("Saturn", "Mars", "enemy"),
]

NAISARGIKA_TABLE = naisargika_maitri_from_rows(L0_NAISARGIKA_ROWS)


def test_loader_output_equals_snapshot_for_all_42_pairs():
    table = naisargika_maitri_from_rows(L0_NAISARGIKA_ROWS)
    assert table == NAISARGIKA_MAITRI
    # node rows in the L0 source are skipped, not loaded (§3.3)
    with_nodes = L0_NAISARGIKA_ROWS + [("Rahu", "Sun", "enemy"),
                                       ("Sun", "Rahu", "enemy")]
    assert naisargika_maitri_from_rows(with_nodes) == NAISARGIKA_MAITRI


def test_loader_db_less_literal_rows_and_refusals():
    # mapping-shaped rows (a psycopg dict-row path) load identically
    rows = [{"graha": g, "other_graha": o, "relation": r}
            for g, o, r in L0_NAISARGIKA_ROWS]
    assert naisargika_maitri_from_rows(rows) == NAISARGIKA_MAITRI
    # an unknown relation label refuses — never defaulted
    with pytest.raises(ValueError, match="unknown relation label"):
        naisargika_maitri_from_rows(
            L0_NAISARGIKA_ROWS + [("Sun", "Moon", "great_friend")])
    # a missing non-node pair refuses — never defaulted
    with pytest.raises(ValueError, match="missing 1 non-node pair"):
        naisargika_maitri_from_rows(L0_NAISARGIKA_ROWS[:-1])


def test_maitri_spot_checks():
    # Sun–Saturn enemies in BOTH directions
    assert naisargika_relation("Sun", "Saturn", NAISARGIKA_TABLE) == "enemy"
    assert naisargika_relation("Saturn", "Sun", NAISARGIKA_TABLE) == "enemy"
    # the Moon has NO enemies (the text's own exception, PG40:C1)
    assert NAISARGIKA_TABLE["Moon"]["enemies"] == frozenset()
    assert naisargika_relation("Moon", "Saturn", NAISARGIKA_TABLE) == "neutral"
    assert naisargika_relation("Moon", "Mercury", NAISARGIKA_TABLE) == "friend"
    # nodes are NOT in the table (translator's note, not registry content)
    assert naisargika_relation("Rahu", "Sun", NAISARGIKA_TABLE) is None
    assert naisargika_relation("Sun", "Rahu", NAISARGIKA_TABLE) is None
    # every row partitions the other six grahas exactly once
    grahas = set(NON_NODE_GRAHAS)
    assert set(NAISARGIKA_TABLE) == grahas
    for g, row in NAISARGIKA_TABLE.items():
        covered = row["friends"] | row["enemies"] | row["neutral"]
        assert covered == grahas - {g}


# ── §2 agent nature / pakṣa / affiliation ────────────────────────────────────
def test_agent_nature_rules():
    assert agent_nature("Sun") == "malefic"
    assert agent_nature("Jupiter") == "benefic"
    # waxing Moon benefic, waning Moon malefic (elongation operand required)
    assert moon_paksa(10.0, 100.0) == "waxing"
    assert moon_paksa(10.0, 200.0) == "waning"
    assert agent_nature("Moon", sun_lon=10.0, moon_lon=100.0) == "benefic"
    assert agent_nature("Moon", sun_lon=10.0, moon_lon=200.0) == "malefic"
    assert agent_nature("Moon") == "unqualified"
    # Mercury: malefic only if joined to a malefic
    assert mercury_affiliation(True) == "malefic"
    assert mercury_affiliation(False) == "benefic"
    assert mercury_affiliation(None) == "unqualified"


# ── §4.2 dignity data + dignity_of ───────────────────────────────────────────
def test_dignity_of_exaltation_debility():
    assert dignity_of("Sun", "Aries") == "exaltation"
    assert dignity_of("Sun", "Libra") == "debility"
    assert dignity_of("Jupiter", "Cancer") == "exaltation"
    assert dignity_of("Jupiter", "Capricorn") == "debility"
    # deep-exaltation degrees per śl.49-50
    assert EXALTATION["Mars"] == {"sign": "Capricorn", "deep_deg": 28.0}
    assert DEBILITY["Saturn"] == {"sign": "Aries", "deep_deg": 20.0}


def test_dignity_of_mulatrikona_and_own():
    assert dignity_of("Sun", "Leo", deg_in_sign=10.0) == "mulatrikona"
    assert dignity_of("Sun", "Leo", deg_in_sign=25.0) == "own"
    # Mercury's Virgo zones are cited: first 15° exaltation, next 5° MT,
    # last 10° own (śl.53, PG38:C1–C2)
    assert dignity_of("Mercury", "Virgo", deg_in_sign=10.0) == "exaltation"
    assert dignity_of("Mercury", "Virgo", deg_in_sign=17.0) == "mulatrikona"
    assert dignity_of("Mercury", "Virgo", deg_in_sign=25.0) == "own"
    # Moon's exaltation sign coincides with its MT sign (Taurus) and the MT
    # span is flagged unverified_ocr — degree-dependent ⇒ unqualified, never
    # a guessed span
    assert MULATRIKONA["Moon"]["span_state"] == "unverified_ocr"
    assert dignity_of("Moon", "Taurus", deg_in_sign=10.0) == "unqualified"
    assert dignity_of("Moon", "Taurus") == "unqualified"
    # naisargika-based tiers without a compound operand (loaded L0 table)
    assert dignity_of("Saturn", "Taurus", naisargika=NAISARGIKA_TABLE) == "friend"   # Venus rules Taurus
    assert dignity_of("Saturn", "Leo", naisargika=NAISARGIKA_TABLE) == "enemy"       # Sun rules Leo
    # without the loaded table the sign-lord tiers are unqualified, never assumed
    assert dignity_of("Saturn", "Taurus") == "unqualified"
    # compound operand unlocks the extreme tiers
    assert dignity_of("Saturn", "Taurus",
                      compound_relation="extreme_friend") == "extreme_friend"


# ── factor rows: calibration + ordering anchors ──────────────────────────────
def test_new_factors_uncalibrated_default():
    for fid in ("agent_nature", "moon_paksa", "mercury_affiliation",
                "maitri_compound", "sad_bala_summary"):
        row = FACTORS[(fid, "1.0.0")]
        assert row["calibration_status"] == "uncalibrated_default"
        assert row["range"] == [0.0, 1.0]
    assert FACTORS[("maitri_compound", "1.0.0")]["categories"] == [
        "extreme_friend", "friend", "neutral", "enemy", "extreme_enemy"]
    # virūpa ordering anchor on the dignity factor (BPHS ch.27 śl.2-4)
    anchor = FACTORS[("dignity_of_transit_sign", "1.0.0")]["ordering_anchor"]
    assert anchor["mulatrikona"] == 45 and anchor["own"] == 30
    assert anchor["extreme_friend"] == 20 and anchor["friend"] == 15
    assert anchor["neutral"] == 10 and anchor["enemy"] == 4
    assert anchor["extreme_enemy"] == 2
    # pūrṇa-bala thresholds (Phaladīpikā IV.22-24)
    th = FACTORS[("sad_bala_summary", "1.0.0")]["purna_bala_thresholds"]
    assert th == {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
                  "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}


def test_p1_soft_factors_include_nature_and_maitri():
    # spec §2.2: strength/śaḍbala and maitrī enter only as NAMED factors here
    soft = dict(RULE_PATHS[("P1", "1.0.0")]["soft_factors"])
    assert ("agent_nature", "1.0.0") in RULE_PATHS[("P1", "1.0.0")]["soft_factors"]
    assert ("maitri_compound", "1.0.0") in RULE_PATHS[("P1", "1.0.0")]["soft_factors"]
    assert ("dignity_of_transit_sign", "1.0.0") in \
        RULE_PATHS[("P1", "1.0.0")]["soft_factors"]
    assert soft  # composite refs, no bare ids
