"""
test_ga_dashas_f_a12_dignity_vocab.py — F-A12 (L1 W3): ga_dashas' own persisted
lord_natal_dignity_d1 disagreed with get_dashas.ts's serve-time authority
(chart_facts.graha_dignity_per_varga) for the exact same natal fact — both sides
ultimately compute from brahmagyan.dignity_oracle.classify_dignity, but
_load_natal_context_inner routed chart_divisionals' Title-cased oracle output
through ga_condition_writer's _DIVISIONAL_DIGNITY_NORMALIZE, a map that exists
for a DIFFERENT consumer (avastha_deeptaadi_from_dignity_and_state's own
"*_sign" vocabulary) — producing "enemy_sign"/"neutral_sign" instead of the bare
"enemy"/"neutral" chart_facts.graha_dignity_per_varga actually stores.

NO DB required — fakes exactly the three sequential cursor.execute()/fetchall()
calls _load_natal_context_inner makes, in order.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as mod  # noqa: E402


class _FakeCursor:
    def __init__(self, query_results):
        self._results = list(query_results)
        self._current: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._current = self._results.pop(0) if self._results else []
        return self

    def fetchall(self):
        return self._current


class _FakeConn:
    def __init__(self, query_results):
        self._query_results = query_results

    def cursor(self, row_factory=None):
        return _FakeCursor(self._query_results)


def _run(divisional_rows):
    """Drive _load_natal_context_inner with graha_position + shadbala empty,
    and the given (graha, dignity_text) rows for the chart_divisionals query."""
    conn = _FakeConn([
        [],                 # 1st execute: chart_facts graha_position (sign/nakshatra/house_d1)
        divisional_rows,    # 2nd execute: chart_divisionals varga_dignity D1
        [],                 # 3rd execute: chart_facts graha_shadbala_total
    ])
    ctx: dict[str, dict] = {}
    mod._load_natal_context_inner(conn, "chart-x", "lahiri_chitrapaksha", {}, ctx)
    return ctx


def test_neutral_maps_to_bare_neutral_not_neutral_sign():
    """The live regression this fix closes: D1 Sun on the canonical chart is
    Title-cased 'Neutral' in chart_divisionals (once ga_vargas rebuilds with its
    oracle-delegating dignity code) — must become plain 'neutral', matching
    chart_facts.graha_dignity_per_varga exactly, not the deeptaadi-vocabulary
    'neutral_sign' the old _DIVISIONAL_DIGNITY_NORMALIZE route produced."""
    ctx = _run([("Sun", "Neutral")])
    assert ctx["Sun"]["dignity_d1"] == "neutral"


def test_enemy_maps_to_bare_enemy_not_enemy_sign():
    """Same regression on the currently-live (pre-rebuild) stale chart_divisionals
    value for Sun ('Enemy', a leftover of the old pre-oracle-refactor writer) —
    this fix's output is honest about what chart_divisionals says today, even
    though ga_vargas rebuilding will change the input to one of the oracle's own
    five tiers. Either way the "*_sign" suffix must never appear."""
    ctx = _run([("Sun", "Enemy")])
    assert ctx["Sun"]["dignity_d1"] == "enemy"


def test_all_five_oracle_tiers_round_trip_case_insensitively():
    """classify_dignity's five canonical tiers, Title-cased as chart_divisionals
    stores them, must each survive as the bare lowercase tier name — no tier is
    silently dropped or renamed by the fix."""
    ctx = _run([
        ("Sun", "Exalted"), ("Moon", "Debilitated"), ("Mars", "Moolatrikona"),
        ("Mercury", "Own"), ("Jupiter", "Neutral"),
    ])
    assert ctx["Sun"]["dignity_d1"] == "exalted"
    assert ctx["Moon"]["dignity_d1"] == "debilitated"
    assert ctx["Mars"]["dignity_d1"] == "moolatrikona"
    assert ctx["Mercury"]["dignity_d1"] == "own"
    assert ctx["Jupiter"]["dignity_d1"] == "neutral"


def test_none_dignity_stays_none():
    """A graha with no chart_divisionals row at all must stay None, never a
    fabricated default (§N.4 floors-aspirational / no-fabrication discipline)."""
    ctx = _run([])
    assert ctx == {}


def test_matches_ga_structural_oracle_output_directly():
    """Cross-check against the actual shared oracle both ga_vargas and
    ga_structural delegate to: classify_dignity('Sun', 'Capricorn', <D1 degree>)
    returns 'neutral' on the canonical chart's real Sun position (measured live
    against chart_facts: longitude_sidereal=291.9626, Capricorn starts at 270,
    so degree_in_sign=21.9626) — this fix's output must equal that bare string,
    not a suffixed variant of it."""
    from brahmagyan.dignity_oracle import classify_dignity
    oracle_value = classify_dignity("Sun", "Capricorn", 21.9626)
    assert oracle_value == "neutral"
    ctx = _run([("Sun", oracle_value.capitalize())])
    assert ctx["Sun"]["dignity_d1"] == oracle_value
