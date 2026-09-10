"""test_d08_pointer_integrity.py — D-08 TDD red-light gate for Stream A.

These tests are INTENTIONALLY FAILING until Stream A lands the following fixes:
  A-09: replace dualOutput 'unknown_tool' default in register_p1_aliases.ts
         (all bare dualOutput(data) calls must supply a real toolName as second arg)
  A-14: gloss signature_classes in kala_views/now.ts
         (signature_classes.join('/') → WINDOW_CLASS_GLOSS map)
  A-15: wire resolveChartFactsAyanamsha at all 11 alias sites
         (AYANAMSHA_ALIAS local maps → resolveChartFactsAyanamsha import)

When all tests here are green, D-08 is complete.

Finding cross-reference:
  F-43  → dualOutput unknown_tool default + bare call sites
  F-09/17/18 → drill pointer recover_via integrity (instrument = real tool name)
  F-123 → recover_via.instrument set in every alias tool's error path
  F-131/132 → raw token in narrative (signature_classes.join + signal_type_id)
  F-59  → AYANAMSHA_ALIAS local map (true_chitra → lahiri silent rewrite)

EKV-D08-TESTS-POSTED 2026-08-16
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTER_P1_ALIASES = REPO_ROOT / "platform-mcp/src/tools/register_p1_aliases.ts"
KALA_NOW = REPO_ROOT / "platform-mcp/src/tools/kala_views/now.ts"

_AYANAMSHA_FILES = [
    "platform-mcp/src/tools/kala_views/ahead.ts",
    "platform-mcp/src/tools/kala_views/explain.ts",
    "platform-mcp/src/tools/kala_views/now.ts",
    "platform-mcp/src/tools/kala_views/priority.ts",
    "platform-mcp/src/tools/register_p1_aliases.ts",
    "platform-mcp/src/tools/register_p1_ganita.ts",
    "platform-mcp/src/tools/register_p2_dasha_lord.ts",
    "platform-mcp/src/tools/registry_bridge.ts",
]

# ── F-43: dualOutput toolName integrity (register_p1_aliases.ts) ─────────────

class TestF43DualOutputToolName:
    """A-09 gate: dualOutput in register_p1_aliases.ts must carry a real toolName."""

    def test_no_unknown_tool_default_definition(self):
        """FAILS until A-09: register_p1_aliases.ts must not define dualOutput with
        toolName='unknown_tool' as a default parameter.

        The broken definition at line 188 makes recover_via.instrument equal to the
        literal placeholder 'unknown_tool' on every auto-trimmed response from any
        of the ~25 handlers that call dualOutput(data) without a second argument.
        A-09 must either (a) set a real default or (b) migrate to kalaBudgetedDualOutput.
        """
        assert REGISTER_P1_ALIASES.exists(), f"File not found: {REGISTER_P1_ALIASES}"
        text = REGISTER_P1_ALIASES.read_text(encoding="utf-8")
        assert "toolName = 'unknown_tool'" not in text, (
            "register_p1_aliases.ts still has function dualOutput(data, toolName='unknown_tool'). "
            "F-43 / A-09: give dualOutput a real tool-name default or migrate all call sites to "
            "kalaBudgetedDualOutput(content, TOOL_NAME). "
            "This broken default makes recover_via.instrument = 'unknown_tool' on every trimmed "
            "response, so a caller trying to page a trimmed result has no honest tool name."
        )

    def test_no_bare_single_arg_dual_output_calls(self):
        """FAILS until A-09: every dualOutput call in register_p1_aliases.ts must
        supply the toolName as an explicit second argument.

        A bare dualOutput(data) call without a second arg silently inherits the
        'unknown_tool' default (F-43). A-09 fixes the broken default so that bare
        calls either disappear (replaced by kalaBudgetedDualOutput) or each explicitly
        names its tool.
        """
        assert REGISTER_P1_ALIASES.exists(), f"File not found: {REGISTER_P1_ALIASES}"
        text = REGISTER_P1_ALIASES.read_text(encoding="utf-8")

        # Find all dualOutput( invocations; count arguments by bracket depth.
        # Same comment-line guard as test_recover_via_instrument_not_unknown_tool_in_error_paths
        # below — a `//` comment illustrating the banned pattern (e.g. "do NOT call bare
        # dualOutput(data)") is not itself a call site and must not be scanned as one.
        bare_calls = []
        for m in re.finditer(r"\bdualOutput\s*\(", text):
            if text[max(0, text.rfind("\n", 0, m.start())):m.start()].strip().startswith("//"):
                continue
            open_idx = m.end() - 1
            depth = 0
            i = open_idx
            start = i + 1
            while i < len(text):
                c = text[i]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            arg_text = text[start:i]
            # Count top-level commas → number of arguments
            d = 0
            n_args = 1
            for c in arg_text:
                if c in "([{":
                    d += 1
                elif c in ")]}":
                    d -= 1
                elif c == "," and d == 0:
                    n_args += 1
            n_args = n_args if arg_text.strip() else 0
            if n_args == 1:
                line_no = text.count("\n", 0, m.start()) + 1
                bare_calls.append((line_no, arg_text.strip()[:60]))

        assert not bare_calls, (
            f"register_p1_aliases.ts has {len(bare_calls)} bare dualOutput(data) call(s) "
            "with only 1 argument — each inherits the 'unknown_tool' default (F-43 / A-09). "
            "First few: " + ", ".join(f"line {ln}: dualOutput({s})" for ln, s in bare_calls[:5])
        )

    def test_recover_via_instrument_not_unknown_tool_in_error_paths(self):
        """FAILS until A-09: no alias handler in register_p1_aliases.ts should surface
        'unknown_tool' as recover_via.instrument in its error or trimmed responses.

        When dualOutput is called without a toolName arg, the response_budget system
        sets recover_via.instrument = 'unknown_tool' in drill_pointers. This test checks
        that the string 'unknown_tool' no longer appears in dualOutput call contexts.
        """
        assert REGISTER_P1_ALIASES.exists(), f"File not found: {REGISTER_P1_ALIASES}"
        text = REGISTER_P1_ALIASES.read_text(encoding="utf-8")

        # After A-09 lands, 'unknown_tool' appears ONLY in comments (historical) — not in
        # executable positions like default parameter values or string literals in call args.
        # A simple heuristic: check for the default parameter pattern.
        bad_pattern = re.compile(r"toolName\s*=\s*'unknown_tool'")
        matches = list(bad_pattern.finditer(text))
        non_comment_matches = [
            m for m in matches
            if not text[max(0, text.rfind("\n", 0, m.start())):m.start()].strip().startswith("//")
        ]
        assert not non_comment_matches, (
            f"Found {len(non_comment_matches)} executable toolName='unknown_tool' assignment(s) in "
            "register_p1_aliases.ts — these produce recover_via.instrument='unknown_tool' in all "
            "drill_pointers emitted by the ~25 alias handlers sharing this dualOutput function (F-43/A-09)."
        )


# ── F-59: AYANAMSHA_ALIAS local map (true_chitra silent rewrite) ─────────────

class TestF59AyanamshaAliasMap:
    """A-15 gate: no file-local AYANAMSHA_ALIAS map may survive after A-15 lands."""

    @pytest.mark.parametrize("rel_path", _AYANAMSHA_FILES)
    def test_no_local_ayanamsha_alias_const(self, rel_path: str):
        """FAILS until A-15: the listed file must not define a local ayanamsha alias
        Record<string, string>. Use resolveChartFactsAyanamsha() instead.

        The local maps silently rewrite 'true_chitra' → 'lahiri_chitrapaksha', hiding
        the true_chitra dataset from every tool that uses them (F-59 / A-15).
        """
        path = REPO_ROOT / rel_path
        if not path.exists():
            pytest.skip(f"File not found (may have been moved by A-15): {path}")
        text = path.read_text(encoding="utf-8")

        # Look for const/let/var with 'ayanamsha' in name followed by = {
        local_map = re.search(
            r"(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*Record\s*<[^>]*>)?\s*=\s*\{",
            text,
        )
        ayanamsha_defs = [
            m for m in re.finditer(
                r"(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*Record\s*<[^>]*>)?\s*=\s*\{",
                text,
            )
            if "ayanamsha" in m.group(1).lower()
        ]
        # Check body for known ayanamsha values
        surviving = []
        for m in ayanamsha_defs:
            try:
                brace = text.index("{", m.end() - 1)
            except ValueError:
                continue
            depth = 0
            i = brace
            while i < len(text):
                c = text[i]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            body = text[brace : i + 1]
            if re.search(r"chitrapaksha|lahiri|krishnamurti|raman|surya_siddhanta", body, re.IGNORECASE):
                surviving.append(m.group(1))

        assert not surviving, (
            f"{rel_path} still defines local ayanamsha alias map(s): {surviving}. "
            "F-59 / A-15: replace with import of resolveChartFactsAyanamsha() from the shared helper. "
            "The local maps silently rewrite 'true_chitra' → 'lahiri_chitrapaksha', "
            "causing every kala_*/phala_* tool to serve the wrong dataset for true_chitra requests."
        )


# ── F-131/132: raw internal token in narrative (signature_classes.join) ──────

class TestF131F132RawTokenInNarrative:
    """A-14 gate: kala_views/now.ts must not join signature_classes with '/' in thesis."""

    def test_no_signature_classes_join_slash_in_now(self):
        """FAILS until A-14: kala_views/now.ts must not use signature_classes.join('/')
        in reading.thesis or any other narrative field.

        The raw join produces 'CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM' — internal
        enum labels that are not human-readable narrative (F-132 / A-14).
        Fix: map classes through a WINDOW_CLASS_GLOSS display-label map first.
        """
        assert KALA_NOW.exists(), f"File not found: {KALA_NOW}"
        text = KALA_NOW.read_text(encoding="utf-8")

        raw_join_re = re.compile(r"signature_classes\b[^\n]*\.join\s*\(\s*['\"][/]['\"]")
        matches = list(raw_join_re.finditer(text))
        assert not matches, (
            f"kala_views/now.ts still has {len(matches)} signature_classes.join('/') site(s) — "
            "these embed raw enum tokens (CLASSIFY_RESIDUAL/DIGNITY/YOGA) in reading.thesis (F-132/A-14). "
            "Replace with: (top?.signature_classes ?? []).map(c => WINDOW_CLASS_GLOSS[c] ?? c).join(' + ')"
        )
