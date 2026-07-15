"""test_d1_5b_b5_completions.py — Lane B-5 (D-1.5b) small L1 completions.

Covers the four independent L1 fact completions:
  1. CR-17  Karakamsha  — AK's D9 (navamsa) sign (regression lock: already emitted
            by ga_sensitive_writer._build_karakamsa_rows).
  2. CR-18  Shadbala required_rupa + ratio per graha (ga_strength_writer).
  3. CR-58  D2 hora-class (surya_hora/chandra_hora) + D2-house (ga_vargas_writer).
  4. CR-46  ph_nimitta anchor dedup — anchor_count reflects POST-dedup count.

All pure-function tests — no DB, no integration marker.
"""
from __future__ import annotations

import sys
import pathlib
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


# ── Item 1: CR-17 Karakamsha (AK's D9 sign) ───────────────────────────────────
class TestKarakamshaAKD9Sign:
    def test_emits_ak_d9_sign_and_atmakaraka(self):
        from ga_writers.ga_sensitive_writer import (
            _build_karakamsa_rows, _d9_sign, SIGNS,
        )
        # Construct longitudes so the Atmakaraka (highest degree-in-sign among the
        # 7 classical grahas) is unambiguously Jupiter at 28.5° into its sign.
        all_longs = {
            "SUN": 300.0 + 10.0,   # 10° in sign
            "MOON": 330.0 + 5.0,   # 5°
            "MAR": 90.0 + 12.0,    # 12°
            "MER": 300.0 + 3.0,    # 3°
            "JUP": 120.0 + 28.5,   # 28.5°  ← highest deg-in-sign → AK
            "VEN": 300.0 + 20.0,   # 20°
            "SAT": 210.0 + 15.0,   # 15°
            "LAGNA": 0.0 + 12.43,
        }
        rows = _build_karakamsa_rows(all_longs, "chart-x", "lahiri_chitrapaksha",
                                     "build-x", "eng/1.0")
        by_key = {r["fact_key"]: r for r in rows}

        assert by_key["atmakaraka_graha"]["fact_value_text"] == "Jupiter"
        # Karakamsa = D9 sign of the AK's longitude.
        expected_d9 = _d9_sign(all_longs["JUP"])
        assert expected_d9 in SIGNS
        assert by_key["sign"]["fact_value_text"] == expected_d9
        # every row is the KARAKAMSA subject under the karakamsa_position category
        assert all(r["fact_category"] == "karakamsa_position" for r in rows)
        assert all(r["fact_subject"] == "KARAKAMSA" for r in rows)


# ── Item 2: CR-18 Shadbala required_rupa + ratio ──────────────────────────────
class TestShadbalaRequiredRupaAndRatio:
    def _rows(self):
        from ga_writers.ga_strength_writer import _build_shadbala_rows
        shadbala = {
            g: {"sthana": 1.0, "dig": 1.0, "kala": 1.0, "cheshta": 1.0,
                "naisargika": 1.0, "drik": 1.0, "total": total}
            for g, total in [
                ("Sun", 7.5), ("Moon", 6.0), ("Mars", 2.5), ("Mercury", 7.0),
                ("Jupiter", 6.5), ("Venus", 5.5), ("Saturn", 5.0),
            ]
        }
        empty = {g: {} for g in shadbala}
        return _build_shadbala_rows(
            shadbala, empty, empty, "chart-x", "build-x",
            "lahiri_chitrapaksha", "2026-07-15T00:00:00Z", "eng/1.0",
            "two_pass_verified",
        )

    def test_required_rupa_present_per_graha(self):
        rows = self._rows()
        req = {r["fact_subject"]: r for r in rows
               if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa"}
        # BPHS minimums (verified against SHADBALA_REQUIRED constant)
        assert req["SUN"]["fact_value_num"] == 5.0
        assert req["MOON"]["fact_value_num"] == 6.0
        assert req["MER"]["fact_value_num"] == 7.0
        assert req["JUP"]["fact_value_num"] == 6.5
        assert req["VEN"]["fact_value_num"] == 5.5

    def test_ratio_is_achieved_over_required(self):
        rows = self._rows()
        ratio = {r["fact_subject"]: r for r in rows
                 if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "ratio"}
        # Sun: 7.5 / 5.0 = 1.5 (above minimum)
        assert abs(ratio["SUN"]["fact_value_num"] - 1.5) < 1e-9
        # Mars: 2.5 / 5.0 = 0.5 (below minimum)
        assert abs(ratio["MAR"]["fact_value_num"] - 0.5) < 1e-9
        # Mercury: 7.0 / 7.0 = 1.0 (exactly at minimum)
        assert abs(ratio["MER"]["fact_value_num"] - 1.0) < 1e-9
        # ratio is ayanamsha-dependent (keyed to live ayanamsha, not INVARIANT)
        assert ratio["SUN"]["ayanamsha_id"] == "lahiri_chitrapaksha"

    def test_ratio_emitted_for_all_seven_grahas(self):
        rows = self._rows()
        ratio_subjects = {r["fact_subject"] for r in rows
                          if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "ratio"}
        assert ratio_subjects == {"SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"}


# ── Item 3: CR-58 D2 hora-class + D2-house ────────────────────────────────────
class TestD2HoraClass:
    def _varga_data(self):
        # D2 sign indices per _compute_d2_hora: Leo=4 (surya), Cancer=3 (chandra).
        # Lagna in Leo (surya_hora) → house counting anchored at Leo.
        return {
            "Lagna":   {"sign_idx": 4, "degree_in_sign": 12.0},  # Leo  → house 1
            "Sun":     {"sign_idx": 4, "degree_in_sign": 10.0},  # Leo  → house 1
            "Moon":    {"sign_idx": 3, "degree_in_sign": 5.0},   # Cancer → house 12
            "Venus":   {"sign_idx": 3, "degree_in_sign": 20.0},  # Cancer → house 12
            "Saturn":  {"sign_idx": 3, "degree_in_sign": 15.0},  # Cancer → house 12
            "Mars":    {"sign_idx": 4, "degree_in_sign": 2.0},
            "Mercury": {"sign_idx": 3, "degree_in_sign": 8.0},
            "Jupiter": {"sign_idx": 4, "degree_in_sign": 25.0},
            "Rahu":    {"sign_idx": 4, "degree_in_sign": 1.0},
            "Ketu":    {"sign_idx": 3, "degree_in_sign": 1.0},
        }

    def _rows(self):
        from ga_writers.ga_vargas_writer import _build_d2_hora_rows
        return _build_d2_hora_rows(
            "chart-x", "lahiri_chitrapaksha", "build-x", "D2",
            self._varga_data(), "2026-07-15T00:00:00Z",
        )

    def test_hora_class_surya_vs_chandra(self):
        rows = self._rows()
        hc = {r["fact_subject"]: r["fact_value_text"]
              for r in rows if r["fact_key"] == "hora_class"}
        assert hc["D2.SUN"] == "surya_hora"   # Leo
        assert hc["D2.MOON"] == "chandra_hora"  # Cancer
        assert hc["D2.VEN"] == "chandra_hora"
        assert hc["D2.SAT"] == "chandra_hora"

    def test_d2_house_from_hora_lagna(self):
        rows = self._rows()
        house = {r["fact_subject"]: r["fact_value_num"]
                 for r in rows if r["fact_key"] == "hora_d2_house"}
        # Lagna in Leo → Leo is house 1; Cancer is 12th from Leo (the audit specimen:
        # "both wealth lords are in the passive hora, in the 12th of the wealth chart").
        assert house["D2.LAGNA"] == 1
        assert house["D2.SUN"] == 1
        assert house["D2.MOON"] == 12
        assert house["D2.VEN"] == 12  # 2L wealth-lord specimen
        assert house["D2.SAT"] == 12  # 11L wealth-lord specimen

    def test_category_and_verification(self):
        rows = self._rows()
        assert rows, "expected hora rows"
        assert all(r["fact_category"] == "varga_hora_class" for r in rows)
        # chart_divisionals CHECK constraint (migration 210) allows this value
        assert all(r["verification_pass_status"] == "classical_match" for r in rows)


# ── Item 4: CR-46 ph_nimitta anchor dedup ─────────────────────────────────────
class TestPhNimittaAnchorDedup:
    def _anchor(self, discovery_id: str):
        from services.ph_nimitta.engine import AnchorRecord
        # Byte-identical content across the fingerprint fields, differing ONLY by
        # discovery_id — the exact observed bug shape (98 dupes of 2 real anchors).
        return AnchorRecord(
            anchor_source="discovery",
            discovery_id=discovery_id,
            event_type="career_discovery_event",
            direction="positive",
            domain="career",
            horizon_tier="near",
            window_start=date(2026, 7, 8),
            peak_date=date(2026, 8, 22),
            window_end=date(2026, 10, 6),
            magnitude="moderate",
            confidence_low=0.30,
            confidence_high=0.35,
            posterior=0.322,
            falsifier="no career discovery event by 2026-10-06",
        )

    def test_collapses_duplicate_anchors(self):
        from pipeline.orchestrator.writers.ph_nimitta import _dedup_anchors
        anchors = [self._anchor(f"disc-{i}") for i in range(100)]
        deduped, removed = _dedup_anchors(anchors)
        assert len(deduped) == 1
        assert removed == 99

    def test_preserves_genuinely_distinct_anchors(self):
        from services.ph_nimitta.engine import AnchorRecord
        from pipeline.orchestrator.writers.ph_nimitta import _dedup_anchors
        a = self._anchor("disc-1")
        b = self._anchor("disc-2")
        b.falsifier = "a genuinely different falsifier"  # distinct content
        c = self._anchor("disc-3")
        c.window_end = date(2027, 1, 1)  # distinct window
        deduped, removed = _dedup_anchors([a, b, c])
        assert len(deduped) == 3
        assert removed == 0

    def test_first_seen_order_preserved(self):
        from pipeline.orchestrator.writers.ph_nimitta import _dedup_anchors
        first = self._anchor("disc-HIGH-RANK")
        dup = self._anchor("disc-LOW-RANK")
        deduped, removed = _dedup_anchors([first, dup])
        assert len(deduped) == 1
        # the higher-ranked (first-passed) anchor is the one retained
        assert deduped[0].discovery_id == "disc-HIGH-RANK"
        assert removed == 1
