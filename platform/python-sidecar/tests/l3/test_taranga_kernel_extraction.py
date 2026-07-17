"""
tests/l3/test_taranga_kernel_extraction.py — wave/D-3/T-3 shared-kernel
extraction regression guard.

Covers:
  1. services.taranga_kernel.kernel's harmonic_mean / GRAHA_DOMAINS /
     month_range reproduce ka_taranga.py's former inline
     `_harmonic_mean` / `_GRAHA_DOMAINS` / `_month_range` bit-for-bit
     (they are the SAME code, re-homed — this is the byte-identical
     regression guard the D-3/T-3 brief asks for).
  2. ka_taranga.py no longer DEFINES its own copies — it imports them from
     the kernel (so there is exactly one implementation, not two that could
     drift).
  3. combine_activation reproduces the exact per-scope combination expression
     ka_taranga.py's `run()` computes inline (harmonic-mean-when-promise-
     present / arithmetic-mean-otherwise).
  4. compute_activation_curve / ChartStaticSubstrate — the new shared,
     point-in-time interface — produce numbers consistent with what
     ka_taranga.py's full monthly sweep would produce for the same
     synthetic inputs, and require chart_id (CR-87 shape: no live signal
     currently defaults chart context — a fresh substrate with an empty
     chart_id must raise, not run with a blank identity).
"""
from __future__ import annotations

import ast
import os
import sys
from datetime import date
from pathlib import Path

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.taranga_kernel.kernel import (
    GRAHA_DOMAINS,
    ActivationPoint,
    ChartStaticSubstrate,
    combine_activation,
    compute_activation_curve,
    dasha_lord_at,
    harmonic_mean,
    month_range,
)

_WRITER_PATH = Path(_SIDECAR) / "pipeline" / "orchestrator" / "writers" / "ka_taranga.py"

# ── Pre-extraction reference implementations (literal copies of what
#    ka_taranga.py used to define at module level, BEFORE this lane's
#    extraction — captured here as historical fixtures, not re-imported from
#    the writer, so this test independently proves the extraction preserved
#    behavior rather than just re-checking the same code against itself). ──


def _old_harmonic_mean(values: list[float]) -> float:
    pos = [v for v in values if v > 0]
    if not pos:
        return 0.0
    if len(pos) == 1:
        return pos[0]
    return len(pos) / sum(1.0 / v for v in pos)


_OLD_GRAHA_DOMAINS: dict[str, list[str]] = {
    "Sun":     ["dharma", "career"],
    "Moon":    ["mind", "relationship", "health"],
    "Mars":    ["career", "property", "health"],
    "Mercury": ["education", "commerce", "wealth"],
    "Jupiter": ["dharma", "wealth", "children", "education"],
    "Venus":   ["relationship", "wealth", "creativity"],
    "Saturn":  ["karma", "career", "longevity", "health"],
    "Rahu":    ["karma", "foreign", "technology"],
    "Ketu":    ["moksha", "spirituality"],
}


def _old_month_range(start: date, end: date):
    cur = date(start.year, start.month, 1)
    while cur <= end:
        yield cur
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)


class TestHarmonicMeanByteIdentical:
    @pytest.mark.parametrize("values", [
        [1.0, 1.0, 1.0],
        [0.5, 0.8, 0.1],
        [0.0, 0.5, 1.0],
        [1.0],
        [],
        [0.15, 0.0, 0.0],
        [0.9, 0.4, 0.72],
    ])
    def test_matches_pre_extraction_reference(self, values):
        assert harmonic_mean(values) == _old_harmonic_mean(values)


class TestGrahaDomainsByteIdentical:
    def test_matches_pre_extraction_reference(self):
        assert GRAHA_DOMAINS == _OLD_GRAHA_DOMAINS

    def test_all_nine_classical_grahas_present(self):
        assert set(GRAHA_DOMAINS.keys()) == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
        }


class TestMonthRangeByteIdentical:
    def test_matches_pre_extraction_reference(self):
        start, end = date(2023, 11, 15), date(2024, 3, 1)
        assert list(month_range(start, end)) == list(_old_month_range(start, end))

    def test_single_month(self):
        assert list(month_range(date(2020, 6, 1), date(2020, 6, 1))) == [date(2020, 6, 1)]


class TestWriterNoLongerDefinesOwnCopies:
    """The writer must import these from the kernel, not redefine them —
    otherwise the extraction is cosmetic and the two copies can drift."""

    def test_writer_has_no_local_harmonic_mean_def(self):
        tree = ast.parse(_WRITER_PATH.read_text())
        fn_names = {
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "_harmonic_mean" not in fn_names, (
            "ka_taranga.py must import _harmonic_mean from "
            "services.taranga_kernel.kernel, not define its own copy"
        )
        assert "_month_range" not in fn_names, (
            "ka_taranga.py must import _month_range from "
            "services.taranga_kernel.kernel, not define its own copy"
        )

    def test_writer_has_no_local_graha_domains_assignment(self):
        tree = ast.parse(_WRITER_PATH.read_text())
        assigned_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        assigned_names.add(tgt.id)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assigned_names.add(node.target.id)
        assert "_GRAHA_DOMAINS" not in assigned_names, (
            "ka_taranga.py must import _GRAHA_DOMAINS from "
            "services.taranga_kernel.kernel (as GRAHA_DOMAINS), not define "
            "its own module-level dict literal"
        )

    def test_writer_imports_from_taranga_kernel(self):
        src = _WRITER_PATH.read_text()
        assert "from services.taranga_kernel.kernel import" in src


class TestCombineActivationMatchesInlineFormula:
    """Reproduces ka_taranga.py's per-scope inline expression:
        act = harmonic_mean([d, t, p]) if p > 0 else (d + t) / 2.0
    """

    @pytest.mark.parametrize("d,t,p", [
        (1.0, 0.8, 0.6),
        (0.15, 0.0, 0.0),
        (0.15, 0.5, 0.0),
        (1.0, 1.0, 1.0),
        (0.1, 0.3, 0.9),
    ])
    def test_matches_inline_expression(self, d, t, p):
        expected = _old_harmonic_mean([d, t, p]) if p > 0 else (d + t) / 2.0
        assert combine_activation(d, t, p) == expected


class TestComputeActivationCurve:
    """The new shared, point-in-time interface — proves it reproduces the
    writer's per-month domain-scope arithmetic for synthetic inputs, and
    enforces the CR-87 required-chart_id shape."""

    def _substrate(self) -> ChartStaticSubstrate:
        return ChartStaticSubstrate(
            chart_id="482012f1-710e-4a25-994a-93821f5871aa",
            dasha_periods=[
                {"lord_graha": "Mercury", "ds": date(2020, 1, 1), "de": date(2023, 1, 1)},
                {"lord_graha": "Venus", "ds": date(2023, 1, 1), "de": date(2030, 1, 1)},
            ],
            transit_windows=[
                {"domain": "wealth", "window_start": date(2021, 1, 1),
                 "window_end": date(2021, 12, 1), "convergence_score": 0.4},
                {"domain": "wealth", "window_start": date(2021, 1, 1),
                 "window_end": date(2021, 12, 1), "convergence_score": 0.6},
            ],
            promise_by_domain={"wealth": 0.7},
        )

    def test_domain_scope_reproduces_writer_arithmetic(self):
        substrate = self._substrate()
        t = date(2021, 5, 3)
        points = compute_activation_curve(substrate, t, "domain", "wealth")
        assert len(points) == 1
        p = points[0]

        # Reproduce the writer's own per-month logic by hand:
        lord = dasha_lord_at(substrate, date(2021, 5, 1))
        assert lord == "Mercury"
        lord_domains = set(GRAHA_DOMAINS.get(lord, []))
        d_contrib = 1.0 if "wealth" in lord_domains else 0.15
        t_vals = [0.4, 0.6]
        t_contrib = sum(t_vals) / len(t_vals)
        p_contrib = 0.7
        expected_act = _old_harmonic_mean([d_contrib, t_contrib, p_contrib])

        assert p.activation == pytest.approx(round(min(1.0, max(0.0, expected_act)), 6))
        assert p.components["dasha_lord"] == "Mercury"
        assert p.components["chart_id"] == substrate.chart_id

    def test_range_yields_one_point_per_month(self):
        substrate = self._substrate()
        points = compute_activation_curve(
            substrate, (date(2021, 1, 1), date(2021, 3, 1)), "domain", "wealth",
        )
        assert [p.t for p in points] == [date(2021, 1, 1), date(2021, 2, 1), date(2021, 3, 1)]

    def test_event_class_scope_uses_max_not_mean(self):
        substrate = self._substrate()
        points = compute_activation_curve(substrate, date(2021, 5, 1), "event_class", "ec-1")
        # No promise_by_event_class entry -> p_contrib = 0.0, so combine_activation
        # falls to arithmetic mean of (d_contrib, t_contrib); t_contrib must be
        # the MAX across domain lists for event_class scope (0.6), not the mean (0.5).
        d_contrib = 1.0  # Mercury's domains overlap themselves -> tautologically 1.0
        t_contrib = 0.6
        expected = (d_contrib + t_contrib) / 2.0
        assert points[0].activation == pytest.approx(round(expected, 6))

    def test_unsupported_resolution_raises_not_silently_approximates(self):
        substrate = self._substrate()
        with pytest.raises(NotImplementedError):
            compute_activation_curve(substrate, date(2021, 1, 1), "domain", "wealth", resolution="daily")

    def test_unknown_scope_kind_raises(self):
        substrate = self._substrate()
        with pytest.raises(ValueError):
            compute_activation_curve(substrate, date(2021, 1, 1), "not_a_scope", "wealth")


class TestChartStaticSubstrateCR87Shape:
    """CR-87 (must_not_touch guard for this lane): chart context must be a
    REQUIRED parameter — never a default — on every new function/current."""

    def test_empty_chart_id_raises(self):
        with pytest.raises(ValueError):
            ChartStaticSubstrate(chart_id="", dasha_periods=[])

    def test_chart_id_is_a_required_positional_field(self):
        import inspect
        sig = inspect.signature(ChartStaticSubstrate.__init__)
        chart_id_param = sig.parameters["chart_id"]
        assert chart_id_param.default is inspect.Parameter.empty, (
            "ChartStaticSubstrate.chart_id must have no default (CR-87)"
        )

    def test_two_different_chart_ids_produce_independently_tagged_points(self):
        sub_a = ChartStaticSubstrate(chart_id="482012f1-710e-4a25-994a-93821f5871aa",
                                      dasha_periods=[{"lord_graha": "Sun", "ds": date(2020, 1, 1), "de": date(2021, 1, 1)}])
        sub_b = ChartStaticSubstrate(chart_id="1c826d5a-41cb-4450-b4dc-59d440e5f75a",
                                      dasha_periods=[{"lord_graha": "Sun", "ds": date(2020, 1, 1), "de": date(2021, 1, 1)}])
        pt_a = compute_activation_curve(sub_a, date(2020, 6, 1), "domain", "career")[0]
        pt_b = compute_activation_curve(sub_b, date(2020, 6, 1), "domain", "career")[0]
        assert pt_a.components["chart_id"] != pt_b.components["chart_id"]
