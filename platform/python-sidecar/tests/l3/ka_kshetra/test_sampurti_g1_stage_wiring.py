"""
tests/l3/ka_kshetra/test_sampurti_g1_stage_wiring.py — SAMPURTI G1 stage-wiring
smoke tests.

These tests verify STRUCTURAL WIRING without a live DB or heavy imports.
They operate exclusively on source-file text (Path.read_text), which means:
  - no dependency on networkx / scipy / psycopg2 / etc.
  - no DB connection required
  - fast and deterministic

What is verified:
  1. Each of stages 0–3 defines the three module-level functions:
     plan_substeps, handles_substep, run_substep
  2. handles_substep routing — correct step.key patterns in each stage
  3. Plugin ORDER in writer._optional_stage_plugins:
     stage0 → stage2 → stage3 → stage1   (dependency-correct)
  4. S1-F1 fix: _route_gain_and_sign_for_lord in stage3 references
     kala_field_routes, not the non-existent kala_field_promise_routes
  5. §N.3 discipline: DELETE appears in plan_substeps, not in run_substep
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KA_KSHETRA = (
    Path(__file__).resolve().parents[3]
    / 'services' / 'ka_kshetra'
)


def _src(filename: str) -> str:
    """Return full source text of a ka_kshetra module file."""
    return (_KA_KSHETRA / filename).read_text(encoding='utf-8')


def _fn_body(src: str, fn_name: str) -> str:
    """Extract the source text of a function/method definition by name.

    Handles both top-level defs (column 0) and indented class methods.
    Captures from 'def <fn_name>(' up to the next def/class at the SAME
    indentation level or shallower, or end-of-file.
    """
    # Find the line that starts the definition (any indentation)
    header_pattern = re.compile(
        r'^([ \t]*)def ' + re.escape(fn_name) + r'\b',
        re.MULTILINE,
    )
    hm = header_pattern.search(src)
    assert hm is not None, (
        f"Function/method '{fn_name}' not found as a def in source"
    )
    indent = hm.group(1)  # leading whitespace of the def line
    start = hm.start()

    # Find the next def or class at the same (or shallower) indentation level
    # after the definition header.
    body_end_pattern = re.compile(
        r'^(?!' + re.escape(indent) + r'[ \t])(?:' + re.escape(indent) + r')(?:def |class )',
        re.MULTILINE,
    )
    # Simpler: find next line starting with ≤ len(indent) whitespace followed
    # by def/class — scan from just after the header line end.
    header_end = src.index('\n', start) + 1
    next_sibling = re.compile(
        r'^[ \t]{0,' + str(len(indent)) + r'}(?:def |class )\S',
        re.MULTILINE,
    )
    nm = next_sibling.search(src, header_end)
    end = nm.start() if nm else len(src)
    return src[start:end]


def _has_top_level_def(src: str, fn_name: str) -> bool:
    """True if src contains 'def <fn_name>(' at column 0."""
    return bool(re.search(r'^def ' + re.escape(fn_name) + r'\b', src, re.MULTILINE))


# ---------------------------------------------------------------------------
# 1. Wiring attributes present in every stage module
# ---------------------------------------------------------------------------

class TestStageModulesHaveWiringAttributes:
    """Each stage module must expose plan_substeps, handles_substep, run_substep
    at module level (top-level def, column 0)."""

    @pytest.mark.parametrize('filename,stage_label', [
        ('stage0_kinematics.py', 'stage0'),
        ('stage1_symbolization.py', 'stage1'),
        ('stage2_promise.py', 'stage2'),
        ('stage3_clocks.py', 'stage3'),
    ])
    def test_module_has_wiring(self, filename: str, stage_label: str) -> None:
        src = _src(filename)
        for fn in ('plan_substeps', 'handles_substep', 'run_substep'):
            assert _has_top_level_def(src, fn), (
                f"{filename} is missing top-level `def {fn}(` — "
                f"required by _optional_stage_plugins protocol (SAMPURTI G1)"
            )


# ---------------------------------------------------------------------------
# 2. handles_substep routing correctness (source-text pattern check)
# ---------------------------------------------------------------------------

class TestHandlesSubstepRouting:
    """Each stage's handles_substep must claim the correct key pattern and not
    claim another stage's keys.  Verified via source-text pattern inspection."""

    def test_stage0_claims_stage0_prefix(self) -> None:
        src = _fn_body(_src('stage0_kinematics.py'), 'handles_substep')
        assert "stage0:" in src, (
            "stage0.handles_substep must check for 'stage0:' prefix"
        )

    def test_stage0_does_not_claim_other_stages(self) -> None:
        src = _fn_body(_src('stage0_kinematics.py'), 'handles_substep')
        for bad in ('stage1:', 'stage2:', 'stage3:'):
            assert bad not in src, (
                f"stage0.handles_substep must NOT reference '{bad}'"
            )

    def test_stage1_claims_stage1_run(self) -> None:
        src = _fn_body(_src('stage1_symbolization.py'), 'handles_substep')
        assert 'stage1:run' in src, (
            "stage1.handles_substep must check for 'stage1:run'"
        )

    def test_stage1_does_not_claim_other_stages(self) -> None:
        src = _fn_body(_src('stage1_symbolization.py'), 'handles_substep')
        for bad in ('stage0:', 'stage2:', 'stage3:'):
            assert bad not in src, (
                f"stage1.handles_substep must NOT reference '{bad}'"
            )

    def test_stage2_claims_stage2_run(self) -> None:
        src = _fn_body(_src('stage2_promise.py'), 'handles_substep')
        assert 'stage2:run' in src, (
            "stage2.handles_substep must check for 'stage2:run'"
        )

    def test_stage2_does_not_claim_other_stages(self) -> None:
        src = _fn_body(_src('stage2_promise.py'), 'handles_substep')
        for bad in ('stage0:', 'stage1:', 'stage3:'):
            assert bad not in src, (
                f"stage2.handles_substep must NOT reference '{bad}'"
            )

    def test_stage3_claims_stage3_run(self) -> None:
        src = _fn_body(_src('stage3_clocks.py'), 'handles_substep')
        assert 'stage3:run' in src, (
            "stage3.handles_substep must check for 'stage3:run'"
        )

    def test_stage3_does_not_claim_other_stages(self) -> None:
        src = _fn_body(_src('stage3_clocks.py'), 'handles_substep')
        for bad in ('stage0:', 'stage1:', 'stage2:'):
            assert bad not in src, (
                f"stage3.handles_substep must NOT reference '{bad}'"
            )


# ---------------------------------------------------------------------------
# 3. Plugin ORDER in writer._optional_stage_plugins
# ---------------------------------------------------------------------------

class TestPluginOrder:
    """The plugin list in writer._optional_stage_plugins must be in dependency order:
    stage0 → stage2 → stage3 → stage1.

    stage1 reads BOTH stage0 output (kinematics) AND stage3 output (boundaries),
    so it MUST come last. stage3 reads stage2 output (routes), so stage2 before
    stage3. Verified by parsing the string literals in the plugins list.
    """

    def test_plugin_order_is_dependency_correct(self) -> None:
        src = _src('writer.py')
        # Extract the method body of _optional_stage_plugins
        method_body = _fn_body(src, '_optional_stage_plugins')
        # Find all 'services.ka_kshetra.stageN_*' string literals in order
        found = re.findall(
            r"['\"]services\.ka_kshetra\.(stage\d+\w+)['\"]",
            method_body,
        )
        expected = [
            'stage0_kinematics',
            'stage2_promise',
            'stage3_clocks',
            'stage1_symbolization',
        ]
        assert found == expected, (
            f"Plugin order wrong.\n"
            f"  Got:      {found}\n"
            f"  Expected: {expected}\n"
            "Dependency rationale: stage1 reads BOTH stage0 (kinematics) AND "
            "stage3 (boundaries); stage3 reads stage2 (routes). "
            "Correct order: stage0 → stage2 → stage3 → stage1."
        )


# ---------------------------------------------------------------------------
# 4. S1-F1 fix: correct table name in _route_gain_and_sign_for_lord
# ---------------------------------------------------------------------------

class TestS1F1Fix:
    """S1-F1: stage3_clocks._route_gain_and_sign_for_lord must query
    kala_field_routes, NOT the non-existent kala_field_promise_routes."""

    def test_correct_table_name_in_route_gain_query(self) -> None:
        src = _fn_body(_src('stage3_clocks.py'), '_route_gain_and_sign_for_lord')
        assert 'kala_field_promise_routes' not in src, (
            "S1-F1 regression: _route_gain_and_sign_for_lord still references "
            "kala_field_promise_routes (non-existent table). Must use kala_field_routes."
        )
        assert 'kala_field_routes' in src, (
            "S1-F1: _route_gain_and_sign_for_lord must query kala_field_routes."
        )


# ---------------------------------------------------------------------------
# 5. §N.3 — delete once in plan_substeps, never in run_substep
# ---------------------------------------------------------------------------

class TestDeleteOnce:
    """§N.3: the per-chart delete must appear in plan_substeps (via REPLACE_PRIOR_SQL
    or explicit DELETE FROM), never repeated in run_substep."""

    @staticmethod
    def _plan_has_delete(filename: str) -> bool:
        src = _fn_body(_src(filename), 'plan_substeps')
        upper = src.upper()
        return 'DELETE FROM' in upper or 'REPLACE_PRIOR_SQL' in upper

    @staticmethod
    def _run_has_delete(filename: str) -> bool:
        src = _fn_body(_src(filename), 'run_substep')
        return 'DELETE FROM' in src.upper()

    @pytest.mark.parametrize('filename,stage_label', [
        ('stage0_kinematics.py', 'stage0'),
        ('stage1_symbolization.py', 'stage1'),
        ('stage2_promise.py', 'stage2'),
        ('stage3_clocks.py', 'stage3'),
    ])
    def test_plan_substeps_has_delete(self, filename: str, stage_label: str) -> None:
        assert self._plan_has_delete(filename), (
            f"{filename}: plan_substeps must run §N.3 delete "
            "(REPLACE_PRIOR_SQL or DELETE FROM)"
        )

    @pytest.mark.parametrize('filename,stage_label', [
        ('stage0_kinematics.py', 'stage0'),
        ('stage1_symbolization.py', 'stage1'),
        ('stage2_promise.py', 'stage2'),
        ('stage3_clocks.py', 'stage3'),
    ])
    def test_run_substep_no_delete(self, filename: str, stage_label: str) -> None:
        assert not self._run_has_delete(filename), (
            f"{filename}: run_substep must NOT issue DELETE FROM "
            "(§N.3: delete runs ONCE in plan_substeps only)"
        )
