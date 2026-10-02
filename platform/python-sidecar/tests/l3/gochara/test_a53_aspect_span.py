"""A5.3 — aspect-to-span (the aspect point's ingress into a house span), steward
M20261002T000907-c058 (b).

`materialise.aspect_spans` derives each occurrence from the body's residence spans over the
aspect SOURCE signs. The derivation is checked against an INDEPENDENT oracle: a synthetic body
with a known longitude curve (direct motion, a retrograde loop that crosses one boundary three
times, a second revolution), whose aspected intervals are found by DENSE SAMPLING of
`floor(((λ(t) + angle) mod 360) / 30)` — no crossings, no residence spans, no shared code beyond the
pinned angle table. The solver's span boundaries must equal the oracle's within the sampling step.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel.convention import SPECIAL_DRISHTI_DEG
from services.gochara_kernel.materialise import (BoundaryCrossing, aspect_source_signs,
                                                 aspect_spans, residence_spans)
from services.gochara_rules.frames import SIGNS

UTC = timezone.utc
D0 = datetime(2025, 1, 1, tzinfo=UTC)


def _dt(day: float) -> datetime:
    return D0 + timedelta(days=day)


# ── the synthetic body: piecewise-linear longitude, exactly solvable ─────────

#: (start_day, longitude_at_start, rate_deg_per_day) — direct, a retrograde loop back across 180°,
#: direct again (180° is crossed THREE times: forward, back, forward), then a long direct run that
#: makes a whole second revolution through the zodiac.
SEGMENTS = [
    (0.0, 150.0, 0.5),       # Virgo -> crosses 180 (Libra boundary) forward
    (100.0, 200.0, -0.4),    # retrograde: back across 180 into Virgo
    (160.0, 176.0, 0.5),     # direct again: crosses 180 a third time
    (400.0, 276.0, 0.8),     # fast direct run through the rest of the zodiac and round again
]
END_DAY = 1000.0


def lam(day: float) -> float:
    seg = [s for s in SEGMENTS if s[0] <= day][-1]
    return (seg[1] + seg[2] * (day - seg[0])) % 360.0


def _crossings() -> list[BoundaryCrossing]:
    """EXACT sign-boundary crossings of the piecewise-linear curve (analytic, not sampled)."""
    out = []
    bounds = [s[0] for s in SEGMENTS] + [END_DAY]
    for (a, lon0, rate), b in zip(SEGMENTS, bounds[1:]):
        if rate == 0:
            continue
        lon_a, lon_b = lon0, lon0 + rate * (b - a)
        lo, hi = min(lon_a, lon_b), max(lon_a, lon_b)
        k = int(lo // 30.0) + (1 if lo % 30.0 else 0) if rate > 0 else int(lo // 30.0) + 1
        k0, k1 = int(lo // 30.0), int(hi // 30.0)
        for n in range(k0, k1 + 1):
            level = 30.0 * n
            if lo < level <= hi if rate > 0 else lo <= level < hi:
                t = a + (level - lon0) / rate
                if a <= t < b:
                    out.append(BoundaryCrossing(t=_dt(t), level_deg=level % 360.0))
    return sorted(out, key=lambda c: c.t)


def _position_at(t: datetime) -> float:
    return lam((t - D0).total_seconds() / 86400.0)


def _oracle(body: str, target_idx: int, h0: float, h1: float, step=0.005):
    """Maximal runs of days in [h0, h1) at which some aspect point lies in sign `target_idx`."""
    angles = SPECIAL_DRISHTI_DEG[body]
    runs, start, prev = [], None, None
    n = int(round((h1 - h0) / step))
    for i in range(n):
        d = h0 + i * step
        hit = any(int(((lam(d) + a) % 360.0) // 30.0) == target_idx for a in angles)
        if hit and start is None:
            start = d
        if not hit and start is not None:
            runs.append((start, d))
            start = None
        prev = d
    if start is not None:
        runs.append((start, h1))
    return runs


def _solver(body: str, target_idx: int, h0: float, h1: float):
    spans = residence_spans(_crossings(), horizon=(_dt(h0), _dt(h1)), position_at=_position_at)
    return aspect_spans(spans, body=body, target_sign=SIGNS[target_idx])


def _days(t: datetime) -> float:
    return (t - D0).total_seconds() / 86400.0


# ── the source-sign table (hand-derived from BPHS ch.26's angles) ────────────

@pytest.mark.parametrize("body,target,expected", [
    ("Mars", 6, {0, 3, 11}),          # Libra: Mars 7th from Aries, 4th from Cancer, 8th from Pisces
    ("Jupiter", 6, {0, 2, 10}),       # 7th from Aries, 5th from Gemini, 9th from Aquarius
    ("Saturn", 6, {0, 4, 9}),         # 7th from Aries, 3rd from Leo, 10th from Capricorn
    ("Sun", 6, {0}), ("Moon", 6, {0}), ("Mercury", 6, {0}), ("Venus", 6, {0}),
    ("Rahu", 6, set()), ("Ketu", 6, set()),      # N-14: nodes cast no dṛṣṭi
    ("Mars", 0, {9, 6, 5}),           # Aries: wraps the zodiac
])
def test_aspect_source_signs(body, target, expected):
    assert aspect_source_signs(body, target) == frozenset(expected)


# ── the independent oracle ───────────────────────────────────────────────────

@pytest.mark.parametrize("body", ["Mars", "Jupiter", "Saturn", "Sun"])
@pytest.mark.parametrize("target", range(12))
def test_solver_spans_equal_the_dense_sampling_oracle(body, target):
    """Every body x every target sign over the whole synthetic history — direct motion, the
    retrograde loop (a boundary crossed three times), and a second revolution."""
    h0, h1 = 0.0, END_DAY - 1.0
    got = [(_days(s.t_in), _days(s.t_out) if s.t_out is not None else h1)
           for s in _solver(body, target, h0, h1)]
    want = _oracle(body, target, h0, h1)
    assert len(got) == len(want), (body, target, got, want)
    for (g0, g1), (w0, w1) in zip(got, want):
        assert g0 == pytest.approx(w0, abs=0.01) and g1 == pytest.approx(w1, abs=0.01), (body, target)


def test_a_boundary_crossed_three_times_yields_two_separate_aspect_occurrences():
    """Sun aspects ONLY the 7th: Aries (idx 0) is aspected from Libra (idx 6). The curve is in Libra
    over [60, 150) (forward past 180°), is carried back out by the retrograde loop at day 150, and
    re-enters at day 168 for [168, 228): the SAME boundary crossed three times -> TWO occurrences."""
    spans = _solver("Sun", 0, 0.0, 300.0)
    runs = [(_days(s_.t_in), _days(s_.t_out)) for s_ in spans]
    assert len(runs) == 2
    assert runs[0] == pytest.approx((60.0, 150.0), abs=1e-6)
    assert runs[1] == pytest.approx((168.0, 228.0), abs=1e-6)
    assert all(s_.sign == "Aries" and s_.t_exact == s_.t_in for s_ in spans)   # labelled with the TARGET


def test_adjacent_source_signs_merge_into_one_continuous_occurrence():
    """Mars aspects Aries (idx 0) from Virgo (idx 5, 210°), Libra (idx 6, 180°) and Capricorn (idx 9,
    90°). The curve starts in Virgo, passes Virgo -> Libra at day 60, is carried back into Virgo at day
    150 by the retrograde loop and into Libra again at day 168, leaving Libra at day 228: it never
    leaves the SOURCE signs in [0, 228) although the Virgo/Libra boundary is crossed three times ->
    ONE continuous occurrence (union within an agent), truncated at the history's start."""
    spans = _solver("Mars", 0, 0.0, 300.0)
    first = spans[0]
    assert first.t_in == _dt(0.0) and first.t_exact is None and first.truncated   # N3: starts mid-run
    assert _days(first.t_out) == pytest.approx(228.0, abs=1e-6)
    assert not [s_ for s_ in spans[1:] if s_.t_in < first.t_out]                    # no overlap/split


# ── horizon / domain edges ───────────────────────────────────────────────────

def test_truncation_flags_follow_the_history_edges():
    """A run that begins at the history's start has no exact ingress (t_exact None, truncated); a run
    cut off by the history's end has no egress (t_out None, truncated); interior runs are exact on
    both sides."""
    spans = _solver("Mars", 0, 0.0, 300.0)
    assert spans[0].t_exact is None and spans[0].truncated
    ended = _solver("Sun", 0, 0.0, 200.0)               # Libra residence [168, ...) is cut at day 200
    assert ended[-1].t_out is None and ended[-1].truncated and ended[-1].t_exact is not None
    interior = _solver("Sun", 0, 0.0, 300.0)
    assert all(not s_.truncated and s_.t_exact is not None and s_.t_out is not None for s_ in interior)


# ── the enumerator's aspect-to-span edges go through the same machinery ──────

def test_every_p3_aspect_on_span_edge_has_a_nonempty_source_set_for_non_nodes():
    chart = {"natal": {"Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
                       "Jupiter": 148.87, "Venus": 265.39, "Saturn": 356.74,
                       "Rahu": 21.34, "Ketu": 201.34}, "lagna_deg": 12.43}
    edges = [e for e in ev.enumerate_edges("marriage", "P3", chart)
             if e.transit and e.relation == "aspect" and e.obj.canonical_target.startswith("span:")]
    assert edges and not [e for e in edges if e.agent in ("rahu", "ketu", "moon")]
    from services.gochara_kernel import targets
    for e in edges:
        idx = targets.span_sign_index(e.obj.canonical_target) - 1
        assert aspect_source_signs(e.agent, idx), e


# ── through the record phase (fake store): ordinals, horizon clipping, half-open membership ──────

from .test_a53_record_store import (CHART, DAY, FakeStore, SKY_CID, T0,  # noqa: E402
                                    _crossing, _house_from_lagna, _run)

LEO_MID, OUT_MID = 135.0, 165.0           # Leo is a Saturn aspect source for Libra (60° -> 2 signs)


def _saturn_libra_aspect_edge():
    edges = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
             if e.transit and e.agent == "saturn" and e.relation == "aspect"
             and e.obj.canonical_target == "span:7"]
    assert len(edges) == 1
    return edges[0]


def _leo_probe(ranges):
    def position_at(body, t):
        d = (t - T0) / DAY
        return LEO_MID if any(a <= d < b for a, b in ranges) else OUT_MID
    return position_at


def _contacts(store):
    return [kw for k, kw in store.calls if k == "insert_contact"]


def test_the_record_phase_materialises_an_aspect_to_span_edge_from_the_residence_spans():
    """Saturn aspects Libra from Leo: it is in Leo over [10, 200) -> one occurrence, ordinal 1,
    exact ingress at day 10 — written through the SAME span->contact->record flow as residence."""
    store = FakeStore({"saturn": [_crossing(10, 120.0), _crossing(200, 150.0)]})
    counts = _run(store, [_saturn_libra_aspect_edge()], position_at=_leo_probe([(10, 200)]))
    assert counts["contacts"] == 1 and counts["records"] == 1 and counts["aspect_span_deferred"] == 0
    (c,) = _contacts(store)
    assert c["contact"].occurrence_ordinal == 1
    assert c["poid"].relation_kind == "aspect" and c["poid"].canonical_target == "span:7"
    assert c["span"].t_exact == T0 + 10 * DAY and c["span"].t_out == T0 + 200 * DAY


def test_a_retrograde_re_entry_into_a_source_sign_is_a_second_occurrence_with_the_next_ordinal():
    store = FakeStore({"saturn": [_crossing(10, 120.0), _crossing(100, 120.0),
                                  _crossing(160, 120.0), _crossing(300, 150.0)]})
    counts = _run(store, [_saturn_libra_aspect_edge()],
                  position_at=_leo_probe([(10, 100), (160, 300)]))
    assert counts["contacts"] == 2 and counts["records"] == 2
    got = [(c["contact"].occurrence_ordinal, c["span"].t_in, c["span"].t_out) for c in _contacts(store)]
    assert got == [(1, T0 + 10 * DAY, T0 + 100 * DAY), (2, T0 + 160 * DAY, T0 + 300 * DAY)]


def test_an_occurrence_overlapping_a_narrower_horizon_is_clipped_and_keeps_its_full_domain_ordinal():
    """Horizon [day 50, day 150) inside Leo's [10, 200): the stored contact is CLIPPED to the horizon
    (F7/C7: its support must lie inside the class partition) — t_exact NULL, a truncated span (N3);
    identity is untouched: ordinal 1 of the full-domain set."""
    store = FakeStore({"saturn": [_crossing(10, 120.0), _crossing(200, 150.0)]})
    counts = _run(store, [_saturn_libra_aspect_edge()], horizon=(T0 + 50 * DAY, T0 + 150 * DAY),
                  position_at=_leo_probe([(10, 200)]))
    assert counts["contacts"] == 1 and counts["truncated_contacts"] == 1
    (c,) = _contacts(store)
    assert c["contact"].occurrence_ordinal == 1
    assert c["span"].t_in == T0 + 50 * DAY and c["span"].t_exact is None and c["span"].t_out is None


def test_horizon_membership_is_half_open_start_inclusive_end_exclusive():
    """Occurrence [10, 200). Horizon [200, ...) does not overlap it (the egress IS the exclusive
    start); horizon [..., 10) does not either; horizon [10, 11) keeps the exact ingress (h0 inside)."""
    store = FakeStore({"saturn": [_crossing(10, 120.0), _crossing(200, 150.0)]})
    for horizon, expected in (((T0 + 200 * DAY, T0 + 300 * DAY), 0),
                              ((T0, T0 + 10 * DAY), 0),
                              ((T0 + 10 * DAY, T0 + 11 * DAY), 1)):
        store.calls.clear()
        counts = _run(store, [_saturn_libra_aspect_edge()], horizon=horizon,
                      position_at=_leo_probe([(10, 200)]))
        assert counts["contacts"] == expected, horizon
    (c,) = _contacts(store)
    assert c["span"].t_exact == T0 + 10 * DAY                  # the horizon start itself is inside


def test_without_the_position_probe_nothing_is_minted_and_the_deferral_is_counted():
    store = FakeStore({"saturn": [_crossing(10, 120.0), _crossing(200, 150.0)]})
    counts = _run(store, [_saturn_libra_aspect_edge()], position_at=None)
    assert counts["contacts"] == 0 and counts["aspect_span_deferred"] == 1


# ── the INDEPENDENT verifier re-derives the same spans (sampling + bisection, no crossings) ────────

from services.gochara_kernel import inventory_verifier as ver  # noqa: E402


def _probe(body, t):
    return lam((t - D0).total_seconds() / 86400.0)


@pytest.mark.parametrize("body,target", [("Mars", 0), ("Saturn", 6), ("Jupiter", 4), ("Sun", 0), ("Mars", 11)])
def test_the_verifiers_sampling_derivation_equals_the_builders_residence_derivation(body, target):
    """Two readings of the same doctrine that share no code: (1) residence spans over the aspect source
    signs, merged; (2) `rederive_aspect_span_runs` — sample the aspect points, bisect each change.
    Compared over the whole synthetic history (a retrograde loop and a second revolution included)."""
    h0, h1 = 0.0, END_DAY - 1.0
    builder = [(_days(s_.t_in), _days(s_.t_out) if s_.t_out is not None else h1)
               for s_ in _solver(body, target, h0, h1)]
    sampled = [(_days(a), _days(b)) for a, b in ver.rederive_aspect_span_runs(
        _probe, body=body, target_sign_index=target, lo=_dt(h0), hi=_dt(h1))]
    assert len(builder) == len(sampled), (body, target, builder, sampled)
    for (b0, b1), (v0, v1) in zip(builder, sampled):
        assert b0 == pytest.approx(v0, abs=2e-5) and b1 == pytest.approx(v1, abs=2e-5)


# R10-6: the fixed-tolerance `verify_aspect_span_contacts` comparison (3 s / 6 h) is REMOVED — the derived-tolerance, union-of-contacts
# certification (`contact_certify`, tests/l3/gochara/test_a53_r10_boundary_contract.py) covers aspect-to-span contacts.
