"""
P5c (GOCHARA_DESIGN_SPECS_v1_4 §2.2, sealed FABLE #19 / T0-10) — kakṣyā
donor-key qualification.

The fruit of a kakṣyā crossing is delivered in the cell owned by the
mark-DONOR (Phaladīpikā XXIII, PG301; division order Saturn, Jupiter, Mars,
Sun, Venus, Mercury, Moon, Lagna — 8 cells of 3°45′ each per sign). The
qualifying mark is the cell-lord's contribution to the transiting graha's
BAV in the transited sign, joined on ga_strength_writer.py's actual key
scheme '{GRAHA}-CONTRIBUTOR_{DONOR}-SIGN_{N}'
(ashtakavarga_bindu_contributor) — NOT the transiting graha's own
sign-level BAV count (the N-22/N-13 interim key).

Covered here:
  (a) cell -> lord mapping for known cells;
  (b) the donor join resolves the writer-scheme contributor key;
  (c) absent contributor data yields the honest 'unavailable' state, never
      a fabricated 0/1;
  (d) mutation: the old interim key (transiting graha's own sign marks)
      produces a DIFFERENT qualification on the same fixture — asserting
      the difference so the wrong key fails.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.gochara_grammar import primitives as P
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_v3 import engine as engine_module
from services.gochara_v3.context import (
    BinduContributorRow, BinduSignRow, ClassContext, KakshyaBoundaryRow,
    _fetch_bindu_contributor_rows,
)
from services.gochara_v3.engine import (
    _compute_activity_v3, _kakshya_cell_crossing_from_context,
)

_BASE_JD = 2461042.0


# ── (a) cell -> lord mapping ─────────────────────────────────────────────────

class TestKakshyaCellLordMapping:
    """Cell width 3°45′ (3.75° = 30/8, the grid ga_strength_writer writes);
    lords in division order from Saturn, cell 0 = 0°00′–3°45′."""

    @pytest.mark.parametrize("deg,expected_index", [
        (0.0, 0),       # 0°00′ -> cell 0
        (3.74, 0),
        (3.75, 1),      # 3°45′ -> cell 1
        (7.5, 2),       # 7°30′ -> cell 2
        (11.25, 3),     # 11°15′ -> cell 3
        (15.0, 4),      # 15°00′ -> cell 4
        (18.75, 5),     # 18°45′ -> cell 5
        (22.5, 6),      # 22°30′ -> cell 6
        (26.25, 7),     # 26°15′ -> cell 7
        (29.999, 7),
        (33.0, 0),      # absolute longitude accepted: 3° into Taurus
    ])
    def test_index_for_degree(self, deg, expected_index):
        assert P.kakshya_index_for_degree_in_sign(deg) == expected_index

    def test_lord_order(self):
        assert [P.kakshya_lord_for_index(i) for i in range(8)] == [
            "Saturn", "Jupiter", "Mars", "Sun",
            "Venus", "Mercury", "Moon", "Lagna",
        ]

    def test_out_of_range_is_none_never_guessed(self):
        assert P.kakshya_lord_for_index(-1) is None
        assert P.kakshya_lord_for_index(8) is None

    def test_crossing_detail_carries_donor_lord(self):
        """kakshya_cell_crossing emits the crossed cell's lord in detail."""
        target = ResonanceTarget(
            chart_id="c", event_class="marriage", target_type="bhava",
            target_ref="7", weight=1.0, target_sign="Aries",
            uncited_extension=True,
        )
        ev = MagicMock()
        ev.event_jd = _BASE_JD + 1.0
        ev.event_datetime_ist = "2026-01-01T12:00:00+05:30"
        with patch(
            "services.gochara_grammar.primitives.find_aspect_events",
            return_value=[ev],
        ):
            sentences = P.kakshya_cell_crossing(
                MagicMock(), "c", target, _BASE_JD, _BASE_JD + 30.0,
                conn=None, planets=["Jupiter"],
            )
        assert len(sentences) == 8  # equal-eighths fallback (no conn)
        assert [s.detail["kakshya_lord"] for s in sentences] == [
            "Saturn", "Jupiter", "Mars", "Sun",
            "Venus", "Mercury", "Moon", "Lagna",
        ]


# ── (b) donor join on the writer's key scheme ────────────────────────────────

class TestDonorJoin:
    def _conn(self, rows):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = rows
        return conn

    def test_resolves_contributor_key(self):
        conn = self._conn([(1.0,)])  # fact_value_num
        detail = P.kakshya_donor_bindu_detail(conn, "chart-1", "Jupiter", 1, 0)
        assert detail["kakshya_lord"] == "Saturn"
        assert detail["donor_row_key"] == "JUP-CONTRIBUTOR_SAT-SIGN_1"
        assert detail["donor_bindu_state"] == "resolved"
        assert detail["donor_bindu"] == 1
        # The read hit the writer's category/subject/key scheme verbatim.
        sql, params = conn.execute.call_args[0][0], conn.execute.call_args[0][1]
        assert "ashtakavarga_bindu_contributor" in sql
        assert params == ["chart-1", "JUP-CONTRIBUTOR_SAT-SIGN_1"]

    def test_lagna_donor_key(self):
        conn = self._conn([(0.0,)])
        detail = P.kakshya_donor_bindu_detail(conn, "chart-1", "Saturn", 12, 7)
        assert detail["kakshya_lord"] == "Lagna"
        assert detail["donor_row_key"] == "SAT-CONTRIBUTOR_LAGNA-SIGN_12"
        assert detail["donor_bindu"] == 0
        assert detail["donor_bindu_state"] == "resolved"


# ── (c) absent contributor data -> honest 'unavailable' ─────────────────────

class TestDonorUnavailable:
    def test_no_rows(self):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = []
        detail = P.kakshya_donor_bindu_detail(conn, "chart-1", "Jupiter", 1, 0)
        assert detail["donor_bindu_state"] == "unavailable"
        assert detail["donor_bindu"] is None
        assert detail["donor_bindu"] not in (0, 1)

    def test_none_conn(self):
        detail = P.kakshya_donor_bindu_detail(None, "chart-1", "Jupiter", 1, 0)
        assert detail["donor_bindu_state"] == "unavailable"
        assert detail["donor_bindu"] is None

    def test_null_value_is_unavailable_not_zero(self):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = [(None,)]
        detail = P.kakshya_donor_bindu_detail(conn, "chart-1", "Jupiter", 1, 0)
        assert detail["donor_bindu_state"] == "unavailable"
        assert detail["donor_bindu"] is None

    def test_read_failure_is_unavailable(self):
        conn = MagicMock()
        conn.execute.side_effect = RuntimeError("relation missing")
        detail = P.kakshya_donor_bindu_detail(conn, "chart-1", "Jupiter", 1, 0)
        assert detail["donor_bindu_state"] == "unavailable"
        assert detail["donor_bindu"] is None


# ── context fetch parses the writer's subject scheme ─────────────────────────

class TestContributorContextFetch:
    def test_parse_and_degrade(self):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = [
            ("JUP-CONTRIBUTOR_SAT-SIGN_1", 1.0),
            ("JUP-CONTRIBUTOR_LAGNA-SIGN_1", 0.0),
            ("SAT-CONTRIBUTOR_JUP-SIGN_12", 1.0),
            ("malformed-subject", 5.0),
            ("JUP-CONTRIBUTOR_SAT-SIGN_x", 5.0),
        ]
        rows = _fetch_bindu_contributor_rows(conn, "chart-1")
        by_key = {(r.graha, r.contributor, r.sign_number): r.bindus for r in rows}
        assert by_key == {
            ("JUP", "SAT", 1): 1.0,
            ("JUP", "LAGNA", 1): 0.0,
            ("SAT", "JUP", 12): 1.0,
        }

    def test_none_conn(self):
        assert _fetch_bindu_contributor_rows(None, "chart-1") == []


# ── (d) mutation: donor key != old sign-grain key on the same fixture ────────

_L1_ROWS = (
    KakshyaBoundaryRow(planet="Jupiter", kakshya_index=0, start_deg=10.0, end_deg=20.0),
    KakshyaBoundaryRow(planet="Jupiter", kakshya_index=1, start_deg=20.0, end_deg=30.0),
)


def _make_context(**overrides) -> ClassContext:
    defaults = {
        "chart_id": "test-chart-id",
        "event_class": "marriage",
        "resonance_targets": (),
        "promise": 0.5,
        "promise_detail": {},
        "dasha_periods": (),
        "relevant_grahas": frozenset(),
        "relevant_signs": frozenset(),
        "temporal_shape": "point",
        "valence": "neutral",
        "is_adverse": False,
        "beta_e": 1.0,
        "weight_by_target_ref": {},
        "natal_facts": None,
        "av_gate_rows": (),
        "av_gate_fetch_error": None,
        "sade_sati_phases": (),
        "vedha_rows": (),
        "malefic_scale": (),
        "kakshya_boundaries": (),
        "moorti_rows": (),
        "bindu_sign_rows": (),
        "bindu_contributor_rows": (),
    }
    defaults.update(overrides)
    return ClassContext(**defaults)


def _target(sign: str = "Aries") -> ResonanceTarget:
    return ResonanceTarget(
        chart_id="test-chart-id",
        event_class="marriage",
        target_type="bhava",
        target_ref="7",
        weight=1.0,
        target_sign=sign,
        uncited_extension=True,
    )


def _crossings(ctx: ClassContext, planet: str = "Jupiter"):
    ev = MagicMock()
    ev.event_jd = _BASE_JD + 1.0
    ev.event_datetime_ist = "2026-01-01T12:00:00+05:30"
    with patch(
        "services.gochara_v3.engine.find_aspect_events",
        return_value=[ev],
    ):
        return _kakshya_cell_crossing_from_context(
            MagicMock(), ctx, _target(), _BASE_JD, _BASE_JD + 30.0,
            planets=[planet],
        )


@pytest.fixture
def flag_on(monkeypatch):
    monkeypatch.setattr(engine_module, "_KAKSHYA_BINDU_INTERIM_ENABLED", True)


class TestDonorKeyEngineWiring:
    """Flag on, donor matrix present: qualification is by the cell-lord's
    contribution, at kakṣyā grain — and it DIFFERS from the old key."""

    def test_donor_key_overrides_sign_key(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            # OLD KEY: Jupiter's own sign-1 BAV count = 4 -> would qualify
            # BOTH crossings at sign grain.
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=4.0),),
            # DONOR KEY: cell 0's lord Saturn donates 0; cell 1's lord
            # Jupiter donates 1.
            bindu_contributor_rows=(
                BinduContributorRow(graha="JUP", contributor="SAT", sign_number=1, bindus=0.0),
                BinduContributorRow(graha="JUP", contributor="JUP", sign_number=1, bindus=1.0),
            ),
        )
        sentences = _crossings(ctx)
        assert len(sentences) == 2
        cell0, cell1 = sentences

        # Cell 0 (Saturn's kakṣyā): donor withheld the mark -> unqualified,
        # where the old sign key would have qualified it.
        assert cell0.detail["kakshya_lord"] == "Saturn"
        assert cell0.detail["donor_bindu"] == 0
        assert cell0.detail["donor_bindu_state"] == "resolved"
        assert cell0.detail["donor_row_key"] == "JUP-CONTRIBUTOR_SAT-SIGN_1"
        assert cell0.detail["completeness_state"] == "unqualified"
        assert cell0.detail["failure_detail"]["error_class"] == "donor_mark_zero"
        assert cell0.detail["failure_detail"]["row_identity"] == (
            "test-chart-id:JUP-CONTRIBUTOR_SAT-SIGN_1"
        )

        # Cell 1 (Jupiter's kakṣyā): donor gave the mark -> qualified at the
        # KAKSHYA grain, not the sign grain.
        assert cell1.detail["kakshya_lord"] == "Jupiter"
        assert cell1.detail["donor_bindu"] == 1
        assert cell1.detail["completeness_state"] == "applied"
        assert cell1.detail["qualification_grain"] == "kakshya"
        assert cell1.detail["bindu_source"] == "chart_facts.ashtakavarga_bindu_contributor"

        # Mutation assertion: the two keys produce different activity on this
        # fixture. Donor key: only cell 1 active -> noisy-OR(0.5) = 0.5.
        # Old sign key would qualify both -> noisy-OR(0.5, 0.5) = 0.75.
        activity, detail, _ = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == pytest.approx(0.5)
        assert detail["sentence_count_active"] == 1
        assert activity != pytest.approx(0.75)  # the old key's answer

    def test_old_key_would_qualify_both(self, flag_on):
        """Control: without contributor rows the sign-grain interim qualifies
        both crossings — proving the fixture discriminates the keys."""
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=4.0),),
        )
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "applied"
            assert s.detail["qualification_grain"] == "sign"
        activity, _, _ = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == pytest.approx(0.75)


class TestDonorUnavailableFallback:
    """Flag on, contributor matrix absent (production state): the sign-grain
    interim applies, labelled as the coarser qualification, with the donor
    operand honestly 'unavailable' — never a fabricated 0/1."""

    def test_unavailable_falls_back_to_sign_grain(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=4.0),),
            bindu_contributor_rows=(),  # matrix not built
        )
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "applied"
            assert s.detail["qualification_grain"] == "sign"  # labelled coarser P5a
            assert s.detail["donor_bindu_state"] == "unavailable"
            assert s.detail["donor_bindu"] is None
            assert s.detail["donor_bindu"] not in (0, 1)
            assert s.detail["kakshya_lord"] in (
                "Saturn", "Jupiter", "Mars", "Sun",
                "Venus", "Mercury", "Moon", "Lagna",
            )

    def test_unavailable_does_not_fabricate_zero_marks(self, flag_on):
        """No contributor rows + no sign rows -> unqualified via the sign
        interim, donor still unavailable (NOT a donor-mark-zero verdict)."""
        ctx = _make_context(kakshya_boundaries=_L1_ROWS)
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "unqualified"
            assert s.detail["failure_detail"]["error_class"] == "bindu_unresolvable"
            assert s.detail["donor_bindu_state"] == "unavailable"
            assert s.detail["donor_bindu"] is None


class TestFlagOffUnchanged:
    def test_flag_off_has_no_donor_keys(self):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_contributor_rows=(
                BinduContributorRow(graha="JUP", contributor="SAT", sign_number=1, bindus=1.0),
            ),
        )
        sentences = _crossings(ctx)
        for s in sentences:
            assert set(s.detail) == {"boundary_deg", "kakshya_index", "source"}
