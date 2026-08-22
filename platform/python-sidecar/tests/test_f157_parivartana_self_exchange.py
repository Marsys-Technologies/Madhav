"""F-157 — parivartana emitted for same-graha "exchanges" (svakshetra misfire).

Finding
-------
`ga_structural_writer.py::_build_varga_relationship_rows`'s parivartana
(mutual-exchange) loop had no `lord1 != g1` guard. For a graha sitting in its
OWN sign, `lord1 == g1` (e.g. Jupiter in Sagittarius: sign1="Sagittarius",
lord1=SIGN_LORDS["Sagittarius"]="Jupiter"), which makes the `sign_lord1 in
OWN_SIGNS.get(g1, [])` test trivially true against itself. The `_seen_parivartana`
dedup set does not catch this — it only suppresses the redundant A->B / B->A
double-hit of a REAL exchange, and a self-pair only ever hits once. The result
was a fabricated `chart_facts` row: fact_category='parivartana_per_varga',
fact_subject='D1_JUPITER_JUPITER', fact_value_text=
'Jupiter_in_Sagittarius_Jupiter_in_Sagittarius' — asserting a mutual exchange
between Jupiter and itself.

Classically this placement is svakshetra (own-sign), a well-defined and
entirely different dignity state from parivartana (mutual exchange), which by
definition requires TWO DIFFERENT grahas each occupying the sign the other
rules. `graha_dignity_per_varga` already correctly tags such a graha 'own' (or
'moolatrikona' — see F-62) elsewhere; this writer's parivartana enumeration
must never also claim it as an exchange.

The fix
-------
One guard, `if lord1 == g1: continue`, placed BEFORE the `OWN_SIGNS` test (see
`ga_structural_writer.py` around line 5086-5096, immediately after `lord1` is
resolved and validated non-None/classical).

Not affected (do not chase this elsewhere)
-------------------------------------------
`bo_laksana.py` consumes `parivartana_per_varga` at L2 and fans out to
career/wealth/relationship domains — an L2 rebuild must follow the L1
`ga_structural` rebuild once the GA-3 queue entry runs (see the F-157 GA-3
packet). `bo_cgm_motifs.py`'s `mutual_reception` check (lines ~277-296) is
NOT affected: it iterates `graha_ids[i+1:]`, which structurally excludes
self-pairs (`a_id != b_id` by construction of the index-offset loop) — no
guard was ever needed there.

Materialization note
---------------------
The buggy rows are already materialized in `chart_facts` (built before this
fix). This test only proves the WRITER no longer fabricates new self-pair
rows; it does not retroactively correct already-stored rows — that requires
the separately-authored (not executed by this PR) GA-3 regeneration of
`ga_structural` -> `bo_laksana` for affected charts.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_structural_writer as sut
from test_ga8_writer import (
    MOCK_CHART_OUTPUT,
    CHART_ID,
    BUILD_ID,
    AY_ID,
    ENG_VER,
    COMPUTED_AT,
)

# X_in_S_X_in_S — the exact shape a self-paired parivartana's fact_value_text
# takes: the same graha name appears as both halves of the "A_in_SignA_B_in_SignB"
# template (SignA and SignB happen to be equal too, but the graha-name repeat
# alone is diagnostic and is what this regex pins).
_SELF_PAIR_VALUE_TEXT_RE = re.compile(r"^([A-Za-z]+)_in_\w+_\1_in_\w+$")


def _parivartana_rows(chart_output, varga_state=None):
    vs = varga_state if varga_state is not None else sut._extract_chart_state(chart_output)
    rows = sut._build_varga_relationship_rows(
        "D1", vs, chart_output, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
    )
    return [r for r in rows if r["fact_category"] == "parivartana_per_varga"]


def _repeated_graha_token(fact_subject: str) -> bool:
    """fact_subject is 'D1_<SORTED_TOKEN_A>_<SORTED_TOKEN_B>' (varga_prefix +
    pair_key). A self-pair collapses both tokens to the same subject code."""
    body = fact_subject.split("_", 1)[1] if fact_subject.startswith("D1_") else fact_subject
    parts = body.split("_")
    # PLANET_TO_SUBJECT values are single tokens (e.g. "JUP", "VEN") — a
    # genuine two-planet pair_key is "A_B" (2 tokens, distinct). A self-pair
    # is "A_A".
    if len(parts) == 2:
        return parts[0] == parts[1]
    return False


class TestF157OwnSignNotParivartana:
    """MOCK_CHART_OUTPUT already carries Jupiter in Sagittarius (own_sign) —
    this is the live reproducer, not a synthetic edge case."""

    def test_jupiter_in_sagittarius_emits_no_self_pair_parivartana(self):
        assert MOCK_CHART_OUTPUT is not None
        jupiter = next(g for g in MOCK_CHART_OUTPUT["grahas"] if g["name"] == "Jupiter")
        assert jupiter["sign"] == "Sagittarius"
        assert sut.SIGN_LORDS["Sagittarius"] == "Jupiter"  # confirms lord1 == g1 precondition

        rows = _parivartana_rows(MOCK_CHART_OUTPUT)

        for r in rows:
            assert not _repeated_graha_token(r["fact_subject"]), (
                f"self-paired parivartana row emitted: fact_subject={r['fact_subject']!r}"
            )
            value_text = r.get("fact_value_text") or ""
            assert not _SELF_PAIR_VALUE_TEXT_RE.match(value_text), (
                f"self-paired parivartana row emitted: fact_value_text={value_text!r}"
            )
            # No row should even mention Jupiter/Jupiter as both halves of the pair.
            assert r["fact_value_jsonb"]["planet_a"] != r["fact_value_jsonb"]["planet_b"], (
                f"parivartana row with planet_a == planet_b: {r}"
            )

    def test_no_parivartana_row_at_all_for_a_solitary_own_sign_placement(self):
        """Stronger form of the assertion above: with ONLY Jupiter placed (no
        other graha whose lord is Jupiter and who Jupiter's own sign hosts),
        there must be ZERO parivartana_per_varga rows — not merely zero
        self-paired ones."""
        chart_output = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9,
                 "longitude": 265.0, "retrograde": False, "dignity_status": "own_sign"},
            ],
        }
        rows = _parivartana_rows(chart_output)
        assert rows == []


class TestF157GenuineExchangeStillFires:
    """Positive control — Mars in Taurus / Venus in Aries is a textbook
    parivartana (each planet sits in the sign the other rules)."""

    def test_mars_venus_exchange_still_emits_one_correctly_paired_row(self):
        chart_output = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Mars", "sign": "Taurus", "sign_id": 2, "house": 2,
                 "longitude": 45.0, "retrograde": False, "dignity_status": "neutral"},
                {"name": "Venus", "sign": "Aries", "sign_id": 1, "house": 1,
                 "longitude": 10.0, "retrograde": False, "dignity_status": "neutral"},
            ],
        }
        assert sut.SIGN_LORDS["Taurus"] == "Venus"
        assert sut.SIGN_LORDS["Aries"] == "Mars"

        rows = _parivartana_rows(chart_output)

        assert len(rows) == 1, f"expected exactly one parivartana row, got {len(rows)}: {rows}"
        row = rows[0]
        assert row["fact_category"] == "parivartana_per_varga"
        assert row["fact_key"] == "mutual_exchange"
        # pair_key = "_".join(sorted([MAR, VEN]))
        assert row["fact_subject"] == "D1_MAR_VEN"
        assert not _repeated_graha_token(row["fact_subject"])
        assert {row["fact_value_jsonb"]["planet_a"], row["fact_value_jsonb"]["planet_b"]} == {"Mars", "Venus"}
        assert row["fact_value_jsonb"]["planet_a"] != row["fact_value_jsonb"]["planet_b"]

    def test_both_own_sign_and_genuine_exchange_together(self):
        """Realistic mixed chart: Jupiter sits in its own sign (Sagittarius,
        no exchange) WHILE Mars/Venus genuinely exchange elsewhere. The fix
        must suppress only the former."""
        chart_output = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9,
                 "longitude": 265.0, "retrograde": False, "dignity_status": "own_sign"},
                {"name": "Mars", "sign": "Taurus", "sign_id": 2, "house": 2,
                 "longitude": 45.0, "retrograde": False, "dignity_status": "neutral"},
                {"name": "Venus", "sign": "Aries", "sign_id": 1, "house": 1,
                 "longitude": 10.0, "retrograde": False, "dignity_status": "neutral"},
            ],
        }
        rows = _parivartana_rows(chart_output)
        assert len(rows) == 1
        assert rows[0]["fact_subject"] == "D1_MAR_VEN"


class TestF157MutationCheck:
    """Documents the mutation-check performed manually during development:
    reverting the `lord1 == g1` guard (restoring the pre-fix code) makes
    `test_jupiter_in_sagittarius_emits_no_self_pair_parivartana` and
    `test_no_parivartana_row_at_all_for_a_solitary_own_sign_placement` fail,
    because the unguarded loop then emits fact_subject='D1_JUP_JUP' /
    fact_value_text='Jupiter_in_Sagittarius_Jupiter_in_Sagittarius' for the
    solitary-Jupiter fixture. This class re-derives that expectation directly
    against the CURRENT (guarded) source so the fixture itself stays honest
    about what the bug looked like, without needing to actually revert the
    guard in CI."""

    def test_solitary_own_sign_placement_would_self_pair_without_the_guard(self):
        g1 = "Jupiter"
        sign1 = "Sagittarius"
        lord1 = sut.SIGN_LORDS.get(sign1)
        assert lord1 == g1  # the exact precondition the guard exists to intercept
        sign_lord1 = sign1  # lord1 == g1 => get_sign(lord1) == get_sign(g1) == sign1
        assert sign_lord1 in sut.OWN_SIGNS.get(g1, [])  # would-be-trivially-true OWN_SIGNS test
        # i.e., absent the guard, s1 == s2 == "JUP", pair_key == "JUP_JUP",
        # value_text == "Jupiter_in_Sagittarius_Jupiter_in_Sagittarius" — exactly
        # the shape _SELF_PAIR_VALUE_TEXT_RE and _repeated_graha_token detect.
        would_be_value_text = f"{g1}_in_{sign1}_{lord1}_in_{sign_lord1}"
        assert _SELF_PAIR_VALUE_TEXT_RE.match(would_be_value_text)
