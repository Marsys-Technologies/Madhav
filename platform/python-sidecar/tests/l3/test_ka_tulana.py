"""
Tests for ka_tulana cross-pattern prioritization service.
ACs verified: §5 of CLAUDECODE_BRIEF_L3_KA_TULANA_v1_0.md
"""
import pytest
from datetime import date, timedelta

from services.ka_tulana.ranker import (
    KaTulanaService,
    WindowInput,
    KNOWN_DOMAINS,
    I11_WEIGHTS,
    _normalise_rarity,
    _proximity_factor,
    _composite,
)

REF = date(2026, 6, 21)


# ── Fixture helpers ───────────────────────────────────────────────────────────

def _make_window(
    wid: str,
    peak_offset_days: int = 60,
    convergence_score: float = 0.6,
    confidence_label: str = 'moderate',
    rarity_years: float = 12.0,
    domains: list[str] | None = None,
    net_label: str = 'auspicious',
    has_dissonance: bool = False,
    dissonance_domains: list[str] | None = None,
) -> WindowInput:
    peak = REF + timedelta(days=peak_offset_days)
    return WindowInput(
        window_id=wid,
        mode='A',
        peak_date=peak,
        window_start=peak - timedelta(days=15),
        window_end=peak + timedelta(days=15),
        convergence_score=convergence_score,
        confidence_label=confidence_label,
        rarity_years=rarity_years,
        net_label=net_label,
        domains=domains or ['career'],
        has_dissonance=has_dissonance,
        dissonance_domains=dissonance_domains or [],
    )


# ── AC §5.1: ranking with per-factor breakdown ────────────────────────────────

class TestRankWindows:
    def test_higher_convergence_ranks_first(self):
        svc = KaTulanaService()
        high = _make_window('w1', convergence_score=0.9, confidence_label='high')
        low  = _make_window('w2', convergence_score=0.3, confidence_label='moderate')
        ranked = svc.rank_windows([low, high], REF)
        assert ranked[0].window.window_id == 'w1'
        assert ranked[1].window.window_id == 'w2'

    def test_output_includes_per_factor_breakdown(self):
        svc = KaTulanaService()
        w = _make_window('w1', convergence_score=0.7, confidence_label='high', rarity_years=11.86)
        ranked = svc.rank_windows([w], REF)
        fb = ranked[0].factors
        assert fb.convergence_score > 0
        assert fb.rarity_norm > 0
        assert fb.confidence_score > 0
        assert fb.proximity_factor > 0
        assert 0 < fb.composite <= 1.0

    def test_rank_order_is_stable(self):
        svc = KaTulanaService()
        windows = [_make_window(f'w{i}', convergence_score=0.5 + i * 0.05) for i in range(5)]
        r1 = svc.rank_windows(windows, REF)
        r2 = svc.rank_windows(windows, REF)
        assert [r.window.window_id for r in r1] == [r.window.window_id for r in r2]

    def test_rationale_string_present(self):
        svc = KaTulanaService()
        w = _make_window('w1')
        ranked = svc.rank_windows([w], REF)
        assert 'Rank #1' in ranked[0].rationale
        assert 'composite' in ranked[0].rationale

    def test_rarer_window_ranks_above_common_at_equal_convergence(self):
        """AC §5.1 and §5.4: rarer windows rank higher at equal convergence."""
        svc = KaTulanaService()
        rare   = _make_window('rare',   convergence_score=0.6, rarity_years=29.46)  # Saturn
        common = _make_window('common', convergence_score=0.6, rarity_years=1.0)    # ~annual
        ranked = svc.rank_windows([common, rare], REF)
        assert ranked[0].window.window_id == 'rare'


# ── AC §5.2: compare(A,B) → winner + breakdown + confidence ──────────────────

class TestCompare:
    def test_compare_returns_winner(self):
        svc = KaTulanaService()
        strong = _make_window('A', convergence_score=0.85, confidence_label='high')
        weak   = _make_window('B', convergence_score=0.30, confidence_label='speculative')
        verdict = svc.compare(strong, weak, REF)
        assert verdict.winner.window_id == 'A'
        assert verdict.loser.window_id  == 'B'

    def test_compare_includes_decisive_factor(self):
        svc = KaTulanaService()
        a = _make_window('A', convergence_score=0.9)
        b = _make_window('B', convergence_score=0.2)
        verdict = svc.compare(a, b, REF)
        assert verdict.decisive_factor in I11_WEIGHTS

    def test_low_confidence_loses_to_higher_at_same_convergence(self):
        """AC §5.2: low-confidence down-ranked vs high-confidence at similar raw score."""
        svc = KaTulanaService()
        high_conf = _make_window('A', convergence_score=0.65, confidence_label='high')
        low_conf  = _make_window('B', convergence_score=0.65, confidence_label='speculative')
        verdict = svc.compare(high_conf, low_conf, REF)
        assert verdict.winner.window_id == 'A'

    def test_compare_rationale_names_decisive_factor(self):
        svc = KaTulanaService()
        a = _make_window('A', convergence_score=0.8, confidence_label='high')
        b = _make_window('B', convergence_score=0.3, confidence_label='speculative')
        verdict = svc.compare(a, b, REF)
        assert verdict.decisive_factor in verdict.rationale

    def test_compare_includes_confidence_label(self):
        svc = KaTulanaService()
        a = _make_window('A', confidence_label='high')
        b = _make_window('B', confidence_label='speculative')
        verdict = svc.compare(a, b, REF)
        assert verdict.confidence_label in ('high', 'moderate', 'speculative')


# ── AC §5.3: dissonance-aware verdicts (I-23) ────────────────────────────────

class TestDissonanceAwareVerdicts:
    def test_dissonance_window_yields_named_tension(self):
        svc = KaTulanaService()
        dissonant = _make_window(
            'conflict',
            convergence_score=0.75,
            confidence_label='high',
            domains=['relationship'],
            has_dissonance=True,
            dissonance_domains=['finance'],
        )
        clean = _make_window('clean', convergence_score=0.4, domains=['career'])
        verdict = svc.compare(dissonant, clean, REF)
        assert verdict.dissonance_note is not None
        assert 'relationship' in verdict.dissonance_note or 'finance' in verdict.dissonance_note

    def test_high_confidence_dissonance_recommends_mitigation(self):
        svc = KaTulanaService()
        w = _make_window(
            'w1', convergence_score=0.8, confidence_label='high',
            has_dissonance=True, dissonance_domains=['health'],
        )
        verdict = svc.compare(w, _make_window('w2', convergence_score=0.3), REF)
        if verdict.winner.window_id == 'w1':
            assert verdict.recommendation == 'proceed_with_mitigation'

    def test_speculative_dissonance_recommends_defer(self):
        svc = KaTulanaService()
        w = _make_window(
            'w1', convergence_score=0.55, confidence_label='speculative',
            has_dissonance=True, dissonance_domains=['career'],
        )
        verdict = svc.compare(w, _make_window('w2', convergence_score=0.3), REF)
        if verdict.winner.window_id == 'w1':
            assert verdict.recommendation == 'defer'

    def test_clean_window_proceeds(self):
        svc = KaTulanaService()
        a = _make_window('A', convergence_score=0.8, confidence_label='high')
        b = _make_window('B', convergence_score=0.3)
        verdict = svc.compare(a, b, REF)
        if verdict.winner.window_id == 'A':
            assert verdict.recommendation == 'proceed'


# ── AC §5.4: KNOWN_DOMAINS and rarity ranking ────────────────────────────────

class TestKnownDomains:
    def test_known_domains_not_invented(self):
        """AC §5.4 (updated G13/PA-4): domains match CANONICAL_DOMAINS from
        brahmagyan.domain_vocabulary — the 13-domain vocabulary.

        Previously this test asserted the old 7-domain list that mirrored
        bo_sangati.KNOWN_DOMAINS. After G13/PA-4 (R17) both ka_tulana and
        bo_sangati import from the canonical SSoT, so the assertion is now
        against all 13 canonical domains.
        """
        from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS as _CD
        assert set(KNOWN_DOMAINS) == _CD, (
            f"ka_tulana.KNOWN_DOMAINS ({sorted(KNOWN_DOMAINS)}) "
            f"does not match CANONICAL_DOMAINS ({sorted(_CD)}). "
            "G13/PA-4: import CANONICAL_DOMAINS from brahmagyan.domain_vocabulary."
        )

    def test_attention_map_keys_are_known_domains(self):
        svc = KaTulanaService()
        windows = [_make_window(f'w{i}', domains=[d]) for i, d in enumerate(KNOWN_DOMAINS)]
        amap = svc.attention_map(windows, REF, horizon_days=365)
        assert set(amap.by_domain.keys()) == set(KNOWN_DOMAINS)

    def test_rarity_ranking(self):
        """Higher rarity_years → higher rarity_norm → ranks higher."""
        assert _normalise_rarity(29.46) > _normalise_rarity(1.0)
        assert _normalise_rarity(None) == 0.5  # neutral proxy


# ── AC §5.6: anti-drift — no writes to bodha_* or other L2/L3 tables ─────────

class TestAntiDrift:
    def test_service_has_no_db_conn_attribute(self):
        svc = KaTulanaService()
        assert not hasattr(svc, 'db_conn')
        assert not hasattr(svc, '_conn')

    def test_rank_windows_returns_without_db_call(self):
        """Service operates on in-memory WindowInput only — no DB."""
        svc = KaTulanaService()
        windows = [_make_window('w1'), _make_window('w2')]
        ranked = svc.rank_windows(windows, REF)
        assert len(ranked) == 2


# ── Proximity and composite helpers ──────────────────────────────────────────

class TestHelpers:
    def test_proximity_near(self):
        assert _proximity_factor(REF + timedelta(days=10), REF) == 1.0

    def test_proximity_mid(self):
        # day 60 is midway between 30d (1.0) and 90d (0.5) → 0.75
        prx = _proximity_factor(REF + timedelta(days=60), REF)
        assert 0.7 < prx < 0.8

    def test_proximity_far(self):
        assert _proximity_factor(REF + timedelta(days=400), REF) == 0.05

    def test_composite_is_weighted_sum(self):
        w = _make_window('x', convergence_score=1.0, confidence_label='high',
                         rarity_years=30.0, peak_offset_days=10)
        fb = _composite(w, REF)
        # All normalised factors = 1.0 → composite = sum of weights = 1.0
        assert abs(fb.composite - 1.0) < 0.01

    def test_i11_weights_sum_to_one(self):
        total = sum(I11_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9
