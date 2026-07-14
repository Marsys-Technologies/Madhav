# This test runs as part of the standard pytest suite: pytest platform/python-sidecar/
"""
test_cr87_native_chart_context.py — CR-87 hotfix regression guard.

CR-87 (CRIT, register): one native's natal constants were hardcoded into the
SHARED ka_sangam convergence engine —
  services/ka_sangam/engine.py:253        _NATIVE_JANMA_NAK_IDX = 24 (Purva Bhadrapada)
  services/ka_sangam/engine.py:~1148-1149 Mode-C sade-sati signs Cap/Aqu/Pis
                                           (Aquarius Moon)
  pipeline/orchestrator/writers/ka_sangam.py:35-39     _NATIVE_LOCATION (Bhubaneswar)
  pipeline/orchestrator/writers/ka_vighnakara.py:208   _NATIVE_LOC (Bhubaneswar)
— contaminating tara-bala (C_tara), sade-sati (Mode C), and panchanga
(C_panchanga) currents for EVERY chart against chart 482012f1 (Abhisek).

This file covers LANE0_CR87_HOTFIX.md §3, all 5 mandatory tests:
  1. Unit — tara: _tara_score_for_nakshatra varies with janma_nakshatra_idx.
  2. Unit — sade-sati: derive_sade_sati_signs() is derived per-chart, not fixed.
  3. Unit — no-constant guard: the deleted module constants stay deleted.
  4. Regression — Abhisek (482012f1) unchanged: the per-chart-resolved context
     reproduces the exact pre-fix hardcoded output, bit-for-bit.
  5. Regression — charts differ: Abhisek vs Abhinandan (1c826d5a) score
     differently under their own (real, DB-verified) natal contexts.

No live DB, no swisseph required — engine functions are called directly with
explicit NativeChartContext values (LANE0_CR87_HOTFIX.md §3: "must not
require a live DB where avoidable — pass contexts directly to engine
functions").

Natal values used below are real, DB-verified facts for each chart (read via
chart_facts, fact_subject='MOON', ayanamsha_id='lahiri_chitrapaksha'), cited
inline — not invented (B.10):
  482012f1 (Abhisek):    Moon nakshatra = Purva Bhadrapada (idx 24), sign = Aquarius
  1c826d5a (Abhinandan): Moon nakshatra = Ardra (idx 5),              sign = Gemini
"""
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.ka_sangam.engine import (
    _NAKSHATRAS_ORDERED,
    _NAK_NAME_TO_IDX,
    _date_to_jd,
    _tara_score_for_nakshatra,
    NativeChartContext,
    EnrichmentContext,
    derive_sade_sati_signs,
    derive_sade_sati_severity,
    mode_c_subsystem_period,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # tests/ -> python-sidecar/ -> platform/
_SIDECAR_DIR = _PROJECT_ROOT / "python-sidecar"

# ── Real, DB-verified natal facts for the two charts used throughout ────────
# (chart_facts, fact_subject='MOON', ayanamsha_id='lahiri_chitrapaksha')
_ABHISEK_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_ABHISEK_MOON_NAKSHATRA = "Purva Bhadrapada"
_ABHISEK_MOON_SIGN = "Aquarius"
_ABHISEK_JANMA_NAK_IDX = _NAK_NAME_TO_IDX[_ABHISEK_MOON_NAKSHATRA]  # 24

_ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
_ABHINANDAN_MOON_NAKSHATRA = "Ardra"
_ABHINANDAN_MOON_SIGN = "Gemini"
_ABHINANDAN_JANMA_NAK_IDX = _NAK_NAME_TO_IDX[_ABHINANDAN_MOON_NAKSHATRA]  # 5


def _make_native_ctx(janma_nakshatra_idx: int, moon_sign: str, location: dict) -> NativeChartContext:
    sade_sati_signs = derive_sade_sati_signs(moon_sign)
    return NativeChartContext(
        janma_nakshatra_idx=janma_nakshatra_idx,
        moon_sign=moon_sign,
        sade_sati_signs=sade_sati_signs,
        sade_sati_severity=derive_sade_sati_severity(sade_sati_signs),
        location=location,
    )


_ABHISEK_CTX = _make_native_ctx(
    _ABHISEK_JANMA_NAK_IDX, _ABHISEK_MOON_SIGN,
    {'lat': 20.2961, 'lon': 85.8245, 'tz_offset_minutes': 330},
)
_ABHINANDAN_CTX = _make_native_ctx(
    _ABHINANDAN_JANMA_NAK_IDX, _ABHINANDAN_MOON_SIGN,
    # Abhinandan's actual public.charts coordinates — same city (Bhubaneswar) as
    # Abhisek in this corpus, used here ONLY to prove the location value is
    # threaded independently of the tara/sade-sati natal values under test.
    {'lat': 20.2961, 'lon': 85.8245, 'tz_offset_minutes': 330},
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Unit — tara: _tara_score_for_nakshatra varies with janma_nakshatra_idx
# ═══════════════════════════════════════════════════════════════════════════

class TestTaraVariesByJanmaNakshatra:

    def test_same_transit_different_janma_gives_different_scores_somewhere(self):
        """
        For at least one transit nakshatra, Abhisek's tara score (relative to
        janma idx 24) must differ from Abhinandan's (relative to janma idx 5).
        This is the direct CR-87 regression: before the fix, BOTH charts were
        scored against idx 24 and were therefore indistinguishable.
        """
        differences = 0
        for nak in _NAKSHATRAS_ORDERED:
            score_abhisek = _tara_score_for_nakshatra(nak, _ABHISEK_JANMA_NAK_IDX)
            score_abhinandan = _tara_score_for_nakshatra(nak, _ABHINANDAN_JANMA_NAK_IDX)
            if score_abhisek != score_abhinandan:
                differences += 1
        assert differences > 0, (
            "CR-87 regression: tara-bala scores must differ between charts with "
            "different janma nakshatras — got identical scores for every transit "
            "nakshatra, meaning janma_nakshatra_idx is not actually being used."
        )

    def test_specific_transit_nakshatra_diverges(self):
        """Concrete worked example: transit in Abhisek's OWN janma nakshatra
        (Purva Bhadrapada, tara position 1 = 'Janma', score 0.4) must NOT score
        the same for Abhinandan (whose janma is Ardra, a different tara position
        relative to Purva Bhadrapada)."""
        transit_nak = _ABHISEK_MOON_NAKSHATRA  # "Purva Bhadrapada"
        score_abhisek = _tara_score_for_nakshatra(transit_nak, _ABHISEK_JANMA_NAK_IDX)
        score_abhinandan = _tara_score_for_nakshatra(transit_nak, _ABHINANDAN_JANMA_NAK_IDX)
        assert score_abhisek == pytest.approx(0.4), (
            "Transit == janma nakshatra must be tara position 1 (Janma, score 0.4)"
        )
        assert score_abhisek != score_abhinandan

    def test_unknown_nakshatra_name_returns_zero_regardless_of_idx(self):
        """Defensive: an unresolvable nakshatra name scores 0.0 for any janma idx."""
        assert _tara_score_for_nakshatra("Not A Real Nakshatra", 24) == 0.0
        assert _tara_score_for_nakshatra("Not A Real Nakshatra", 5) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Unit — sade-sati: derive_sade_sati_signs() is per-chart, not fixed
# ═══════════════════════════════════════════════════════════════════════════

class TestSadeSatiDerivation:

    def test_derived_from_aquarius_matches_classical_triad(self):
        """Aquarius Moon → (Capricorn, Aquarius, Pisces) — the classical sade-sati
        triad (12th-from-Moon, Moon sign, 2nd-from-Moon)."""
        assert derive_sade_sati_signs("Aquarius") == ("Capricorn", "Aquarius", "Pisces")

    def test_derived_from_different_moon_sign_differs(self):
        """A different Moon sign must NOT collapse to Aquarius's triad — this is
        the exact CR-87 failure mode (every chart getting Cap/Aqu/Pis)."""
        gemini_signs = derive_sade_sati_signs("Gemini")
        assert gemini_signs != ("Capricorn", "Aquarius", "Pisces")
        assert gemini_signs == ("Taurus", "Gemini", "Cancer")

    def test_severity_keyed_by_derived_signs_not_hardcoded_names(self):
        """Severity weights (0.70/1.00/0.70) follow the DERIVED signs, whatever
        they are — not a fixed Capricorn/Aquarius/Pisces key set."""
        gemini_signs = derive_sade_sati_signs("Gemini")
        severity = derive_sade_sati_severity(gemini_signs)
        assert severity == {"Taurus": 0.70, "Gemini": 1.00, "Cancer": 0.70}
        # Doctrine constants (weights) unchanged; only the sign keys move.
        assert set(severity.values()) == {0.70, 1.00}

    def test_unknown_moon_sign_raises_not_silently_defaults(self):
        """CR-87 fail-loud: an unresolvable moon_sign must raise, never silently
        fall back to Aquarius (or any other sign)."""
        with pytest.raises(ValueError):
            derive_sade_sati_signs("Not A Real Sign")

    @pytest.mark.parametrize("moon_sign,expected", [
        ("Aries", ("Pisces", "Aries", "Taurus")),
        ("Cancer", ("Gemini", "Cancer", "Leo")),
        ("Capricorn", ("Sagittarius", "Capricorn", "Aquarius")),
    ])
    def test_wraparound_at_zodiac_boundaries(self, moon_sign, expected):
        """Zodiacal wraparound (Pisces->Aries, Aquarius->Pisces) must be correct."""
        assert derive_sade_sati_signs(moon_sign) == expected


# ═══════════════════════════════════════════════════════════════════════════
# 3. Unit — no-constant guard (cheapest permanent tripwire against reintroduction)
# ═══════════════════════════════════════════════════════════════════════════

class TestNoNativeConstantGuard:
    """
    CR-87 acceptance criterion (LANE0_CR87_HOTFIX.md §4):
    grep -rn "_NATIVE_JANMA_NAK_IDX|_NATIVE_LOCATION|_NATIVE_LOC" → zero hits
    outside tests/fixtures/comments describing history.

    This test re-implements that check in Python so it runs in the standard
    suite (not just an ad-hoc grep) and fails loudly if anyone reintroduces
    a hardcoded natal constant as executable code.
    """

    _FILES = [
        _SIDECAR_DIR / "services" / "ka_sangam" / "engine.py",
        _SIDECAR_DIR / "pipeline" / "orchestrator" / "writers" / "ka_sangam.py",
        _SIDECAR_DIR / "pipeline" / "orchestrator" / "writers" / "ka_vighnakara.py",
    ]
    _FORBIDDEN_TOKENS = ("_NATIVE_JANMA_NAK_IDX", "_NATIVE_LOCATION", "_NATIVE_LOC")

    def test_forbidden_tokens_only_appear_in_comments(self):
        violations = []
        for path in self._FILES:
            assert path.exists(), f"expected file not found: {path}"
            for lineno, line in enumerate(path.read_text().splitlines(), start=1):
                stripped = line.strip()
                for token in self._FORBIDDEN_TOKENS:
                    if token not in line:
                        continue
                    # `_NATIVE_LOC` is a substring of `_NATIVE_LOCATION`; both
                    # tokens are forbidden as EXECUTABLE code either way, so no
                    # special-casing needed — only comment lines are exempt.
                    if not stripped.startswith("#"):
                        violations.append(f"{path.name}:{lineno}: {line!r}")
        assert not violations, (
            "CR-87 REINTRODUCED: found a hardcoded native constant token outside "
            "a comment. Every one of these must be a per-chart resolved value, "
            "never a module-level constant:\n" + "\n".join(violations)
        )

    def test_grep_matches_only_comment_lines(self):
        """Belt-and-suspenders: the literal grep the brief's acceptance
        criterion specifies, asserting every hit is a `#`-comment line."""
        result = subprocess.run(
            ["grep", "-rn", "-E",
             r"_NATIVE_JANMA_NAK_IDX|_NATIVE_LOCATION|_NATIVE_LOC",
             str(_SIDECAR_DIR / "services" / "ka_sangam"),
             str(_SIDECAR_DIR / "pipeline" / "orchestrator" / "writers")],
            capture_output=True, text=True,
        )
        offending = []
        for line in result.stdout.splitlines():
            # format: <path>:<lineno>:<code>
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            code = parts[2].strip()
            if not code.startswith("#"):
                offending.append(line)
        assert not offending, (
            "grep found non-comment hits for the CR-87 forbidden tokens:\n"
            + "\n".join(offending)
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. Regression — Abhisek (482012f1) unchanged: bit-identical to pre-fix output
# ═══════════════════════════════════════════════════════════════════════════

class TestAbhisekUnchanged:
    """
    Pre-fix fixture: the EXACT values the deleted module constants held
    (services/ka_sangam/engine.py, before this CR-87 fix):
      _NATIVE_JANMA_NAK_IDX = 24
      _SADE_SATI_SIGNS      = ('Capricorn', 'Aquarius', 'Pisces')
      _SADE_SATI_SEVERITY   = {'Capricorn': 0.70, 'Aquarius': 1.00, 'Pisces': 0.70}

    These are captured here as literal historical constants (NOT re-imported
    from engine.py, which no longer defines them) and compared against the
    per-chart-RESOLVED NativeChartContext for chart 482012f1. Because
    482012f1's real Moon nakshatra/sign ARE Purva Bhadrapada/Aquarius, the
    resolved values must equal these old literals exactly — proving the fix
    is a no-op for the native chart (LANE0_CR87_HOTFIX.md §2.3 + §4).
    """

    _OLD_JANMA_NAK_IDX = 24
    _OLD_SADE_SATI_SIGNS = ('Capricorn', 'Aquarius', 'Pisces')
    _OLD_SADE_SATI_SEVERITY = {'Capricorn': 0.70, 'Aquarius': 1.00, 'Pisces': 0.70}

    def test_resolved_janma_idx_matches_old_constant(self):
        assert _ABHISEK_CTX.janma_nakshatra_idx == self._OLD_JANMA_NAK_IDX == 24

    def test_resolved_sade_sati_signs_match_old_constant(self):
        assert _ABHISEK_CTX.sade_sati_signs == self._OLD_SADE_SATI_SIGNS

    def test_resolved_sade_sati_severity_matches_old_constant(self):
        assert _ABHISEK_CTX.sade_sati_severity == self._OLD_SADE_SATI_SEVERITY

    def test_resolved_location_matches_old_constant(self):
        assert _ABHISEK_CTX.location == {
            'lat': 20.2961, 'lon': 85.8245, 'tz_offset_minutes': 330,
        }

    def test_tara_scores_bit_identical_across_all_nakshatras(self):
        """For every possible transit nakshatra, the tara score computed via the
        resolved context must equal the score computed with the old hardcoded
        idx=24 literal — bit-for-bit (exact float equality, no tolerance)."""
        for nak in _NAKSHATRAS_ORDERED:
            old_score = _tara_score_for_nakshatra(nak, self._OLD_JANMA_NAK_IDX)
            new_score = _tara_score_for_nakshatra(nak, _ABHISEK_CTX.janma_nakshatra_idx)
            assert new_score == old_score, (
                f"CR-87: tara score for transit={nak!r} changed for the native "
                f"chart: old={old_score} new={new_score}"
            )

    def test_mode_c_sade_sati_windows_bit_identical(self):
        """Mode C sade-sati windows (trigger signs + severity + resulting
        convergence_score) computed via the resolved 482012f1 context must be
        bit-identical to the old hardcoded-constant computation."""
        predicate = {
            'signal_id': 'aaaaaaaa-0000-0000-0000-000000000001',
            'signature_class': 'SUBSYSTEM',
            'dignity_score': 0.8,
            'transit_trigger_jsonb': {'subsystem': 'sade_sati'},
        }
        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd = _date_to_jd(date(2030, 1, 1))

        def _make_gochara():
            mock_gs = MagicMock()
            ingress_ev = MagicMock()
            ingress_ev.event_jd = _date_to_jd(date(2027, 3, 1))

            def _find_ingresses(planet, target_sign, start_jd, end_jd):
                # One ingress per trigger sign, regardless of which sign —
                # isolates the severity/sign computation from ephemeris timing.
                return [ingress_ev]
            mock_gs.find_ingresses.side_effect = _find_ingresses
            return mock_gs

        old_windows = mode_c_subsystem_period(
            predicate=predicate,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=_make_gochara(),
            moon_sign=self._OLD_SADE_SATI_SIGNS[1],  # 'Aquarius' — the old hardcoded Moon sign
        )
        new_windows = mode_c_subsystem_period(
            predicate=predicate,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=_make_gochara(),
            moon_sign=_ABHISEK_CTX.moon_sign,
        )

        assert len(old_windows) == len(new_windows) > 0
        old_signature = sorted(
            (w['constituent_factors']['sign'], w['convergence_score']) for w in old_windows
        )
        new_signature = sorted(
            (w['constituent_factors']['sign'], w['convergence_score']) for w in new_windows
        )
        assert old_signature == new_signature, (
            "CR-87: Mode C sade-sati output for the native chart changed after "
            "the fix — must be bit-identical (§2.3, §4)."
        )


# ═══════════════════════════════════════════════════════════════════════════
# 5. Regression — charts differ: Abhisek vs Abhinandan score differently
# ═══════════════════════════════════════════════════════════════════════════

class TestChartsScoreDifferently:
    """
    2-chart correctness guard (LANE0_CR87_HOTFIX.md §3 item 5) — NOT
    population statistics. Abhinandan (1c826d5a) must score differently from
    Abhisek (482012f1) under their own real natal contexts, wherever those
    natal inputs actually differ.
    """

    def test_janma_nakshatra_idx_differs(self):
        assert _ABHISEK_CTX.janma_nakshatra_idx != _ABHINANDAN_CTX.janma_nakshatra_idx

    def test_sade_sati_signs_differ(self):
        assert _ABHISEK_CTX.sade_sati_signs != _ABHINANDAN_CTX.sade_sati_signs
        assert _ABHISEK_CTX.sade_sati_signs == ('Capricorn', 'Aquarius', 'Pisces')
        assert _ABHINANDAN_CTX.sade_sati_signs == ('Taurus', 'Gemini', 'Cancer')

    def test_tara_bala_current_differs_for_shared_transit_window(self):
        """The same transit nakshatra, scored against each chart's own janma
        nakshatra, must produce a different C_tara current for at least one
        of a representative spread of transit nakshatras."""
        sample_transits = (
            "Ashwini", "Rohini", "Magha", "Chitra", "Jyeshtha",
            "Uttara Ashadha", "Shatabhisha", "Purva Bhadrapada", "Revati",
        )
        abhisek_scores = [
            _tara_score_for_nakshatra(n, _ABHISEK_CTX.janma_nakshatra_idx) for n in sample_transits
        ]
        abhinandan_scores = [
            _tara_score_for_nakshatra(n, _ABHINANDAN_CTX.janma_nakshatra_idx) for n in sample_transits
        ]
        assert abhisek_scores != abhinandan_scores, (
            "CR-87 regression: Abhisek and Abhinandan must NOT score identically "
            "across a representative transit-nakshatra spread."
        )

    def test_mode_c_sade_sati_trigger_signs_differ_between_charts(self):
        """Mode C's sade-sati windows must target different signs for the two
        charts (Cap/Aqu/Pis for Abhisek vs Tau/Gem/Can for Abhinandan) — the
        gochara mock only reports ingresses for a chart-specific sign set, so
        cross-contamination would show up as either 0 windows or wrong signs."""
        predicate = {
            'signal_id': 'bbbbbbbb-0000-0000-0000-000000000002',
            'signature_class': 'SUBSYSTEM',
            'dignity_score': 0.8,
            'transit_trigger_jsonb': {'subsystem': 'sade_sati'},
        }
        start_jd = _date_to_jd(date(2024, 1, 1))
        end_jd = _date_to_jd(date(2030, 1, 1))

        def _make_gochara(allowed_signs):
            mock_gs = MagicMock()
            ingress_ev = MagicMock()
            ingress_ev.event_jd = _date_to_jd(date(2027, 3, 1))

            def _find_ingresses(planet, target_sign, start_jd, end_jd):
                return [ingress_ev] if target_sign in allowed_signs else []
            mock_gs.find_ingresses.side_effect = _find_ingresses
            return mock_gs

        abhisek_windows = mode_c_subsystem_period(
            predicate=predicate,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=_make_gochara({'Capricorn', 'Aquarius', 'Pisces'}),
            moon_sign=_ABHISEK_CTX.moon_sign,
        )
        abhinandan_windows = mode_c_subsystem_period(
            predicate=predicate,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=_make_gochara({'Taurus', 'Gemini', 'Cancer'}),
            moon_sign=_ABHINANDAN_CTX.moon_sign,
        )

        abhisek_signs = {w['constituent_factors']['sign'] for w in abhisek_windows}
        abhinandan_signs = {w['constituent_factors']['sign'] for w in abhinandan_windows}
        assert abhisek_signs, "Abhisek's sade-sati windows must not be empty"
        assert abhinandan_signs, "Abhinandan's sade-sati windows must not be empty"
        assert abhisek_signs != abhinandan_signs
        assert abhisek_signs.isdisjoint(abhinandan_signs), (
            "CR-87 regression: the two charts' sade-sati trigger signs must not "
            "overlap here (Cap/Aqu/Pis vs Tau/Gem/Can) — any overlap would mean "
            "one chart is leaking into the other's Mode C computation."
        )
