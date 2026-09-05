"""
NIRMĀṆA L3-W3 finding M4 (§N.5, §N.7 items 2/3/6) — ka_avadhi's lord-condition refs.

THE DEFECT. `_FETCH_FACT_REFS_SQL` returned zero rows for every lord on every chart, so
`lord_condition_fact_refs` was `[]` on **100.00%** of `kala_avadhi` rows and was served as an
empty array with no flag — which reads as "this lord has no notable condition" rather than
"this query never matched anything". Three independent mismatches against L1, all measured:

  1. `chart_dashas.lord_graha` is Title-case ('Jupiter'); `chart_facts.fact_subject` is the
     canonical 3-letter code ('JUP', 'RAH_MEAN', 'KET_MEAN'). Neither 'Jupiter' NOR 'JUPITER'
     matched — so an upper() would not have fixed it either.
  2. No `fact_category` pin (§N.7 item 2).
  3. Five of the seven `fact_key` values did not exist under `graha_position` at all.

Measured after the fix, live: 8 refs for each of the 9 grahas, up from 0.

These tests fail against the pre-fix query.
"""
from __future__ import annotations

import re

import pytest

from brahmagyan.graha_vocabulary import norm_graha
from pipeline.orchestrator.writers.ka_avadhi import _FETCH_FACT_REFS_SQL

# The real key vocabulary under fact_category='graha_position', measured live.
REAL_KEYS = {
    "sign", "nakshatra", "nakshatra_lord", "sign_lord",
    "house_d1", "pada", "longitude_sidereal", "combustion_state", "retrograde_flag",
}
# The five the query used to ask for, none of which exist under that category.
PHANTOM_KEYS = {"dispositor", "D9_sign", "karaka_role", "longitude", "dignity_score"}


def _quoted_literals(sql: str) -> set[str]:
    return set(re.findall(r"'([^']*)'", sql))


def test_query_pins_the_fact_category() -> None:
    """Selecting on fact_key alone is the §N.7 item-2 defect class."""
    assert "fact_category" in _FETCH_FACT_REFS_SQL
    assert "'graha_position'" in _FETCH_FACT_REFS_SQL


def test_query_asks_only_for_keys_that_exist() -> None:
    asked = _quoted_literals(_FETCH_FACT_REFS_SQL)
    phantoms_still_asked = asked & PHANTOM_KEYS
    assert not phantoms_still_asked, (
        f"query asks for fact_key values that do not exist under graha_position: "
        f"{sorted(phantoms_still_asked)}"
    )
    # And it must still ask for something real, or the fix would be a silent narrowing to nothing.
    assert asked & REAL_KEYS, "query asks for no real graha_position fact_key at all"


def test_query_orders_totally_so_its_limit_is_deterministic() -> None:
    """§N.7 item 2: a LIMIT without a total ORDER BY picks arbitrarily."""
    assert "ORDER BY" in _FETCH_FACT_REFS_SQL
    assert "LIMIT" in _FETCH_FACT_REFS_SQL
    assert _FETCH_FACT_REFS_SQL.index("ORDER BY") < _FETCH_FACT_REFS_SQL.index("LIMIT")


@pytest.mark.parametrize(
    ("dasha_lord", "expected_subject"),
    [
        ("Sun", "SUN"), ("Moon", "MOON"), ("Mars", "MAR"), ("Mercury", "MER"),
        ("Jupiter", "JUP"), ("Venus", "VEN"), ("Saturn", "SAT"),
        ("Rahu", "RAH_MEAN"), ("Ketu", "KET_MEAN"),
    ],
)
def test_every_dasha_lord_normalises_to_a_real_chart_facts_subject(
    dasha_lord: str, expected_subject: str
) -> None:
    """
    The bridge the writer was missing. Note Rahu/Ketu especially: they map to RAH_MEAN/KET_MEAN,
    so no case transformation of the Title-case name could ever have reached them — which is why
    this had to go through the L0 SSoT rather than an upper() or a local dict (§N.7 item 3).
    """
    assert norm_graha(dasha_lord) == expected_subject
