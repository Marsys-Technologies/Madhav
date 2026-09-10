"""F-62 — the moolatrikona dignity tier must survive the whole read path.

Finding
-------
`chart_facts.graha_dignity_per_varga` / `fact_key='dignity_state'` never emitted
'moolatrikona' anywhere in the native chart's data — confirmed chart-wide, every
varga, every graha, zero rows — collapsing a classically-distinct dignity tier
into plain 'own'. Concrete instance: natal Jupiter at 9.787° Sagittarius (D1,
lahiri_chitrapaksha) is squarely inside Jupiter's moolatrikona band (Sagittarius
0°–10°; own-only applies 10°–30°) yet `D1_JUP.dignity_state` is served as 'own'.

This is not cosmetic. Moolatrikona and own carry DIFFERENT classical point values
in Saptavargaja / Sthana Bala (45 vs 30 shashtiamsa, BPHS Ch.27), so any strength
derived from `dignity_state` systematically under-scores every graha whose natal
degree falls in its own moolatrikona band.

Two distinct layers, and this file tests the second
---------------------------------------------------
1. WRITE path — `brahmagyan.dignity_oracle.classify_dignity` gained the
   degree-gated moolatrikona tier, and `ga_structural_writer` (the writer of
   `graha_dignity_per_varga`) and `ga_vargas_writer` both call it. Covered by
   `brahmagyan/__tests__/test_dignity_oracle.py`; re-anchored here on the exact
   live reproducer degrees so the Jupiter case is pinned in F-62's own file too.

2. READ path — the defect this file exists for. The instant the oracle became
   able to EMIT 'moolatrikona', four downstream consumer maps could not SPELL
   it: three keyed on "mooltrikona" (no 'a') and one enumerated only a four-value
   scale. The result was worse than the original collapse: a moolatrikona graha
   missed every lookup and fell to a *neutral* default — scoring BELOW the plain
   'own' it used to score, in the exact tier classical Sthana Bala ranks highest
   after exaltation.

The roster test below is the detector CLAUDE.md §N.8 demands: it enumerates every
consumer of the emitted vocabulary and asserts each one covers the FULL set, so a
future tier added to `DIGNITY_STATES` cannot land while a consumer silently
defaults it away. It is written to fail if the fix is reverted — not merely to
pass alongside it.

Degree-range provenance
-----------------------
No range is asserted from memory here. Every expected value is read out of
`brahmagyan.l0_dignity_reference.DIGNITY_REFERENCE` — this codebase's own
single-source classical reference (cited BPHS Ch.3, seeded to the
`bg_dignity_reference` table by migration 250) — so this file cannot drift from
the reference it is testing against, and cannot invent a range the reference
does not carry.
"""
from __future__ import annotations

import pytest

from brahmagyan.dignity_oracle import (
    DIGNITY_STATES,
    LEGACY_MOOLATRIKONA_ALIASES,
    classify_dignity,
)
from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE


_BY_GRAHA = {row["graha"]: row for row in DIGNITY_REFERENCE}


# ── §1 The live reproducer ────────────────────────────────────────────────────

# Jupiter's D1 degree_in_sign on the canonical chart
# (482012f1-710e-4a25-994a-93821f5871aa), read from production chart_facts, per
# ayanamsha. All five place Jupiter in Sagittarius; only the degree differs, and
# the moolatrikona/own boundary at 10° falls BETWEEN them — so the correct answer
# is genuinely ayanamsha-dependent, and a test that pinned only Lahiri would miss
# that the same graha is legitimately 'own' under Raman.
_JUPITER_D1_DEGREE_BY_AYANAMSHA = {
    "lahiri_chitrapaksha":       9.78749702318149,
    "krishnamurti":              9.88434935651233,
    "true_chitra":               9.80303795826677,
    "raman":                    11.2337983565124,
    "surya_siddhanta_classical": 12.7495298162099,
}

_JUPITER_D1_EXPECTED = {
    "lahiri_chitrapaksha":       "moolatrikona",
    "krishnamurti":              "moolatrikona",
    "true_chitra":               "moolatrikona",
    "raman":                     "own",
    "surya_siddhanta_classical": "own",
}


def test_jupiter_9_79_sagittarius_is_moolatrikona_not_own():
    """The exact F-62 reproducer: natal Jupiter, D1, lahiri_chitrapaksha."""
    assert classify_dignity("Jupiter", "Sagittarius", 9.79) == "moolatrikona"


@pytest.mark.parametrize("ayanamsha", sorted(_JUPITER_D1_DEGREE_BY_AYANAMSHA))
def test_jupiter_d1_dignity_per_ayanamsha(ayanamsha: str):
    """Live per-ayanamsha degrees straddle the 10° moolatrikona boundary.

    Production served 'own' for ALL FIVE. Three of the five are wrong.
    """
    degree = _JUPITER_D1_DEGREE_BY_AYANAMSHA[ayanamsha]
    assert classify_dignity("Jupiter", "Sagittarius", degree) == _JUPITER_D1_EXPECTED[ayanamsha]


def test_jupiter_moolatrikona_band_matches_the_l0_reference():
    """The band asserted above is the codebase's own reference, not a memory."""
    jup = _BY_GRAHA["Jupiter"]
    assert jup["moolatrikona_sign"] == "Sagittarius"
    assert jup["moolatrikona_from"] == 0
    assert jup["moolatrikona_to"] == 10
    assert "BPHS" in jup["classical_citation"]


# ── §2 Every graha's own band, driven from the L0 reference ───────────────────

def _grahas_with_a_moolatrikona_band() -> list[str]:
    return [
        row["graha"] for row in DIGNITY_REFERENCE
        if row["moolatrikona_sign"] is not None
    ]


@pytest.mark.parametrize("graha", _grahas_with_a_moolatrikona_band())
def test_moolatrikona_band_is_reachable_and_bounded(graha: str):
    """Inside the band → moolatrikona; just past its upper edge → own.

    Skips the two grahas whose exaltation sign IS their moolatrikona sign (Moon /
    Taurus, Mercury / Virgo). For those, `classify_dignity` checks exaltation by
    SIGN ONLY, before the degree-gated moolatrikona check, so 'moolatrikona' is
    unreachable at any degree — a KNOWN, DOCUMENTED gap reserved for a classical-
    doctrine ruling (see the module docstring in `brahmagyan/dignity_oracle.py`),
    NOT something this repair decides unilaterally. §3 below pins the gap's
    current behaviour so a future ruling has to change a test to change the
    answer.
    """
    row = _BY_GRAHA[graha]
    if row["moolatrikona_sign"] == row["exaltation_sign"]:
        pytest.skip(f"{graha}: MT sign == exaltation sign — see §3 known-gap tests")

    sign = row["moolatrikona_sign"]
    lo, hi = float(row["moolatrikona_from"]), float(row["moolatrikona_to"])

    # Inside the band, at both edges of the half-open interval [lo, hi).
    assert classify_dignity(graha, sign, lo) == "moolatrikona"
    assert classify_dignity(graha, sign, (lo + hi) / 2.0) == "moolatrikona"
    assert classify_dignity(graha, sign, hi - 0.01) == "moolatrikona"

    # At and past the upper edge, it is own — the band is a real gate, not a
    # whole-sign label.
    assert classify_dignity(graha, sign, hi) == "own"
    if hi < 29.0:
        assert classify_dignity(graha, sign, hi + 1.0) == "own"


def test_the_own_sign_that_is_not_the_moolatrikona_sign_is_never_moolatrikona():
    """A graha's SECOND own sign carries no moolatrikona band at any degree."""
    assert classify_dignity("Jupiter", "Pisces", 5.0) == "own"     # MT is Sagittarius
    assert classify_dignity("Mars", "Scorpio", 5.0) == "own"       # MT is Aries
    assert classify_dignity("Venus", "Taurus", 5.0) == "own"       # MT is Libra
    assert classify_dignity("Saturn", "Capricorn", 5.0) == "own"   # MT is Aquarius


# ── §3 The known gap, pinned rather than silently tolerated ───────────────────

@pytest.mark.parametrize("graha,sign", [("Moon", "Taurus"), ("Mercury", "Virgo")])
def test_known_gap_exaltation_sign_shadows_moolatrikona(graha: str, sign: str):
    """DOCUMENTED GAP, deliberately NOT repaired by F-62.

    For Moon and Mercury the exaltation sign coincides with the moolatrikona
    sign, and `classify_dignity` checks exaltation by sign only — so these two
    grahas return 'exalted' throughout, and 'moolatrikona' is unreachable for
    them at every degree.

    The L0 reference's own numbers show the tension is real and intentional on
    the data side: Moon's MT band starts at 4° — immediately after its 3°
    exaltation degree — and Mercury's at 16°, immediately after its 15°. The
    ranges were authored NOT to overlap. Whether the classifier should therefore
    degree-gate exaltation too is a genuine classical-doctrine question (the
    mainstream Parashari reading treats exaltation as a whole-sign state with
    the exaltation degree as the deep/paramocca point used for Uchcha Bala),
    and it is reserved for a PRATINIDHI ruling — not decided inside a
    vocabulary repair.

    This test pins CURRENT behaviour so the gap is visible and any future ruling
    must change a test to change the answer, rather than the behaviour drifting
    unnoticed in either direction.
    """
    row = _BY_GRAHA[graha]
    assert row["moolatrikona_sign"] == row["exaltation_sign"] == sign
    assert row["moolatrikona_from"] > row["exaltation_degree"], (
        "the L0 reference authored these bands as non-overlapping"
    )
    inside_the_mt_band = float(row["moolatrikona_from"]) + 1.0
    assert classify_dignity(graha, sign, inside_the_mt_band) == "exalted"


# ── §4 The read-path detector (the F-62 defect proper) ────────────────────────

def test_dignity_states_is_the_full_emittable_vocabulary():
    """DIGNITY_STATES must equal what classify_dignity can actually return.

    Guards the roster test below: if the constant drifted from the classifier,
    every "covers the full vocabulary" assertion would be vacuously weaker than
    it claims to be.
    """
    probes = [
        ("Jupiter", "Cancer", 5.0),         # exalted
        ("Jupiter", "Capricorn", 5.0),      # debilitated
        ("Jupiter", "Sagittarius", 5.0),    # moolatrikona
        ("Jupiter", "Sagittarius", 20.0),   # own
        ("Jupiter", "Aries", 5.0),          # neutral
    ]
    assert {classify_dignity(*p) for p in probes} == set(DIGNITY_STATES)
    assert "moolatrikona" in DIGNITY_STATES
    assert not (DIGNITY_STATES & LEGACY_MOOLATRIKONA_ALIASES), (
        "a legacy misspelling must never become part of the emitted vocabulary"
    )


def _consumer_maps() -> list[tuple[str, dict]]:
    """Every map that keys a score/tier off an EMITTED dignity_state value.

    Each of these is fed, directly or transitively, from
    `chart_facts.graha_dignity_per_varga` / `fact_key='dignity_state'`. Maps fed
    from PyJHora's separate `dignity_status` vocabulary (which uses 'own_sign'
    and never emits a moolatrikona tier) are deliberately NOT listed — they are
    a different vocabulary on a different path, out of F-62's scope.
    """
    from bodha_writers.formulas import DIGNITY_SCORE as FML_DIGNITY_SCORE
    from ga_writers.ga_condition_writer import DIGNITY_SCORES as GA_CONDITION_SCORES
    from pipeline.orchestrator.writers import bo_laksana

    return [
        ("bodha_writers.formulas.DIGNITY_SCORE", FML_DIGNITY_SCORE),
        ("bo_laksana._DIGNITY_SCORE", bo_laksana._DIGNITY_SCORE),
        ("bo_laksana._DIGNITY_STRENGTH_TIER", bo_laksana._DIGNITY_STRENGTH_TIER),
        ("ga_condition_writer.DIGNITY_SCORES", GA_CONDITION_SCORES),
    ]


@pytest.mark.parametrize("name,mapping", _consumer_maps(), ids=lambda v: v if isinstance(v, str) else "")
def test_consumer_map_can_spell_moolatrikona(name: str, mapping: dict):
    """The core F-62 regression test.

    Fails on the pre-fix code: three of these four maps carried only
    "mooltrikona".
    """
    assert "moolatrikona" in mapping, (
        f"{name} cannot spell the emitted 'moolatrikona' dignity_state — a "
        f"moolatrikona graha will miss this lookup and take the caller's "
        f"default. Keys present: {sorted(mapping)}"
    )


def test_moolatrikona_outranks_own_in_every_score_map():
    """Classical ordering, enforced numerically: MT > own (45 vs 30, BPHS Ch.27).

    A map that merely CONTAINS the key but scores it at or below 'own' would
    satisfy the spelling test above while still erasing the tier's meaning.
    """
    from bodha_writers.formulas import DIGNITY_SCORE as FML_DIGNITY_SCORE
    from ga_writers.ga_condition_writer import DIGNITY_SCORES as GA_CONDITION_SCORES
    from pipeline.orchestrator.writers import bo_laksana

    for name, mapping in [
        ("bodha_writers.formulas.DIGNITY_SCORE", FML_DIGNITY_SCORE),
        ("bo_laksana._DIGNITY_SCORE", bo_laksana._DIGNITY_SCORE),
        ("ga_condition_writer.DIGNITY_SCORES", GA_CONDITION_SCORES),
    ]:
        own_key = "own" if "own" in mapping else "own_sign"
        assert mapping["moolatrikona"] > mapping[own_key], (
            f"{name}: moolatrikona must outrank {own_key} — BPHS Ch.27 "
            f"Saptavargaja scores them 45 vs 30 shashtiamsa"
        )
        assert mapping["moolatrikona"] <= mapping["exalted"], (
            f"{name}: moolatrikona must not outrank exalted"
        )


def test_moolatrikona_scores_above_neutral_not_at_it():
    """The specific pre-fix symptom: MT silently took the neutral default.

    `bo_laksana` looks its dignity score up with a 0.50 default; before the fix
    'moolatrikona' hit that default, landing the strongest own-sign tier at the
    neutral score and BELOW plain 'own' (0.85).
    """
    from bodha_writers.formulas import DIGNITY_SCORE as FML_DIGNITY_SCORE

    got = FML_DIGNITY_SCORE.get("moolatrikona", 0.50)
    assert got != 0.50, "moolatrikona is still falling through to the neutral default"
    assert got > FML_DIGNITY_SCORE["own"]


def test_bo_laksana_dignity_tier_ranks_moolatrikona_with_own():
    """`_dignity_tier` returned 0 (neutral) for moolatrikona before the fix.

    That fed the D1→D9 cross-check, so a genuine own-sign-strongest D1
    placement read as neutral and could produce a spurious navamsha
    promotion/demotion verdict.
    """
    from pipeline.orchestrator.writers.bo_laksana import _dignity_tier

    assert _dignity_tier("moolatrikona") >= _dignity_tier("own")
    assert _dignity_tier("moolatrikona") > _dignity_tier("neutral")
    assert _dignity_tier("MOOLATRIKONA") > 0, "lookup is case-normalised"


def test_bo_laksana_infers_moolatrikona_as_benefic():
    """`_infer_valence` substring-matched only "mooltrikona".

    "moolatrikona" is not a substring of "mooltrikona" (nor the reverse), so the
    emitted spelling matched no benefic substring at all.
    """
    from pipeline.orchestrator.writers.bo_laksana import _infer_valence

    assert _infer_valence("graha_dignity_per_varga", "moolatrikona") == "benefic"


def test_ga_vichara_counts_moolatrikona_as_a_positive_ratification_vote():
    """`dignity_direction` matched only ('exalted', 'own') and abstained on MT."""
    from ga_writers.ga_vichara_writer import dignity_direction

    assert dignity_direction("moolatrikona") == "positive"
    assert dignity_direction("exalted") == "positive"
    assert dignity_direction("own") == "positive"
    assert dignity_direction("debilitated") == "negative"
    assert dignity_direction("neutral") is None
    assert dignity_direction(None) is None


def test_every_emitted_state_has_a_direction_or_a_deliberate_abstention():
    """No emitted dignity_state may be an unhandled surprise to the read path."""
    from ga_writers.ga_vichara_writer import dignity_direction

    directions = {state: dignity_direction(state) for state in DIGNITY_STATES}
    assert directions == {
        "exalted": "positive",
        "moolatrikona": "positive",
        "own": "positive",
        "debilitated": "negative",
        "neutral": None,
    }


# ── §5 Saptavargaja: the 45-vs-30 point split that motivates all of the above ─

def test_saptavargaja_scores_moolatrikona_at_45_and_own_at_30():
    """The downstream Sthana Bala consumer already carries the classical split.

    Verified rather than assumed: F-62's brief flagged this as a possible SECOND
    defect. It is not one — `ga_vargas_writer._build_saptavargaja_rows` already
    scores moolatrikona at 45.0 and own at 30.0, already gates moolatrikona on
    the real natal degree via the oracle, and already restricts the tier to
    varga_n == 1 (Uchcha/exaltation being a separate Sthana Bala sub-component,
    matching PyJHora's own dcf == 1 guard). This test pins that so the split
    cannot silently regress.
    """
    import inspect

    from ga_writers import ga_vargas_writer

    src = inspect.getsource(ga_vargas_writer._build_saptavargaja_rows)
    assert "saptavargaja_score = 45.0" in src
    assert 'relation_label = "Moolatrikona"' in src
    assert "saptavargaja_score = 30.0" in src
    assert 'classify_dignity(' in src, (
        "the moolatrikona branch must be gated on the shared oracle, not a "
        "writer-local degree table (CLAUDE.md §N.7 item 3)"
    )


def test_ga_vargas_compute_dignity_returns_title_case_moolatrikona():
    """`_compute_dignity` Title-cases the oracle result for its callers."""
    from ga_writers.ga_vargas_writer import SIGN_NAMES, _compute_dignity

    sag = SIGN_NAMES.index("Sagittarius")
    assert _compute_dignity("Jupiter", sag, 9.79) == "Moolatrikona"
    assert _compute_dignity("Jupiter", sag, 15.0) == "Own"
