"""
test_domain_vocabulary_census.py — SHABDA-SHUDDHI · Lane L8 Detectors

CI vocabulary-census gate: scans all Python writers and services for hardcoded
legacy/synonym domain string literals that have been emitted (or can be emitted)
as domain column values into the database.

Two deliverables in this file:
  1. Census gate (Deliverable 2): flags files using legacy domain terms as dict keys
     in domain-classifying maps — the defect class that caused migration-386's DB
     CHECK to be a superset of the canonical 13-domain vocabulary.
  2. Empty-evidence lint (Deliverable 3, §N.8 P2 pattern): flags hardcoded
     verdict/status/grade assignments that have no backing computation (the
     bo_pratijna 'denied'-on-empty and mi_adhilepa 'clean'-always defect classes).

WHAT IS A "VIOLATION" FOR THE CENSUS GATE
------------------------------------------
A violation is a Python source file that contains a known legacy domain term
(from DOMAIN_SYNONYMS keys) where that term is used as a **dict key** in a
domain-classifying mapping that routes domain column values — i.e. the file will
emit the legacy string into a DB domain column rather than resolving it through
canonical_domain() / DOMAIN_SYNONYMS first.

WHAT IS NOT A VIOLATION
-----------------------
- The domain_vocabulary.py module itself (defines the synonyms — obviously allowed)
- Test files (this file, test_domain_vocabulary.py, __tests__/ directories)
- String literals that appear only as dict *values* in a synonym mapping
  (e.g. 'financial': 'wealth' — 'wealth' is canonical, not a violation)
- Strings used purely as keyword-search terms / NLP hints (bg_text_index.py,
  bo_drishti.py domain keyword lists) — these never enter a DB domain column
- String literals in SQL / event_class names that are not DB domain columns
  (e.g. event_class='marriage' in gochara_grammar — 'marriage' is an event_class
  identifier, not a domain column value)
- import statements

HIGH-SEVERITY VIOLATIONS (domain emitted directly to DB domain column)
----------------------------------------------------------------------
These files use 'finance' or 'spiritual' as the key in a dict that is then
iterated to produce domain column values written to DB tables:
  - ka_bhavishya_lekha.py: _DOMAINS list + _DOMAIN_KEYWORDS dict
  - ka_yojaka.py: _SIGNAL_DOMAIN_KEYWORDS dict
  - mi_sambandha.py: _PRIOR_PROPENSITIES dict
  - services/ph_rectification/engine.py: domain→houses mapping
  - services/ph_nimitta/engine.py: _SUBSYSTEM_DOMAIN mapping (synonym-style)
  - services/ph_sankrama.py / ph_phaladesa.py: _ANCHOR_TO_PHALADESA_DOMAIN mappings
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_REPO = _SIDECAR.parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.domain_vocabulary import DOMAIN_SYNONYMS  # noqa: E402

# ── Paths to scan ─────────────────────────────────────────────────────────────

_WRITERS_DIR = _SIDECAR / "pipeline" / "orchestrator" / "writers"
_SERVICES_DIR = _SIDECAR / "services"

# ── Known-safe exclusions ──────────────────────────────────────────────────────

# Files whose legacy-term usage is purely as NLP keyword-search terms (never
# emitted as DB domain column values) or as synonym-resolution dict values
# (the right side of a mapping, where the legacy term IS the key being looked up).
# Each entry is a (stem pattern, reason) pair — path.name must match the stem.
_SAFE_FILE_STEMS: frozenset[str] = frozenset({
    # The vocabulary module itself — defines synonyms, obviously allowed
    "domain_vocabulary.py",
    # NLP text-index keyword sets — these strings go into FTS queries, not domain cols
    "bg_text_index.py",
    # bo_drishti: 'marriage' is used as a human-readable category label in a
    # pattern-matching config dict, not as a DB domain column value
    "bo_drishti.py",
})

# Test files are always excluded
_TEST_FILE_PATTERNS: tuple[str, ...] = (
    "test_",
    "__tests__",
)

# ── Legacy terms that are DICT KEYS (domain emitters) ─────────────────────────
#
# These are the DOMAIN_SYNONYMS keys that can appear as dict keys in legacy
# domain-classifying maps, causing the legacy term to flow into a DB domain column.
# We focus on the highest-severity subset that actually appears in the codebase:

# Tier 1: terms that appear as dict keys emitting DB domain column values
_DICT_KEY_DOMAIN_EMITTERS: frozenset[str] = frozenset({
    'finance',
    'spiritual',
    'financial',
    'psychological',
    'psychology',
    'relationships',
    'progeny_children',
    'residential',
    'moksha',
    'dharma',
    'money',
    'spouse',
    'creativity',
    'intellect',
    'property',
    'foreign',
})

# ── Patterns that indicate "domain-classifying map" vs "NLP keyword list" ─────
#
# A string that appears only as an element in a list of keyword strings (like
# ['dhana', 'second', 'eleventh', 'wealth', ...]) is NOT a domain emitter.
# A string that appears as a dict key where that dict is iterated to produce
# domain values IS a domain emitter.
#
# We detect two forms of the defect class:
#
# Form 1 — dict key with non-string value (domain-classifier map):
#   'legacy_term': [...]   — key maps to keyword list
#   'legacy_term': (n, m)  — key maps to tuple (house numbers, etc.)
#   "legacy_term": {...}   — key maps to sub-dict of channel propensities
#
# INTENTIONALLY NOT flagged by Form 1:
#   'legacy_term': 'canonical_term'  — resolution map (value is a quoted string → safe)
#
# The distinguishing lookahead: the character after ':' must be [, (, {, or a digit.
# A quoted string value starts with ' or " — resolution maps are excluded.

_DICT_KEY_PATTERN = re.compile(
    r"""(?:^|\s|,|\{)\s*['"]("""
    + "|".join(re.escape(t) for t in sorted(_DICT_KEY_DOMAIN_EMITTERS))
    + r""")['"]\s*:\s*(?=[(\[{0-9])""",
    re.MULTILINE,
)

# Form 2 — tuple-first-element pattern in list-of-tuples domain classifiers:
#   ('finance', ['dhana', ...])  — from ka_bhavishya_lekha _DOMAIN_KEYWORDS
#   ('spiritual', ['dharma', ...])
# These are equivalent to dict keys but spelled as tuple elements.

_TUPLE_DOMAIN_PATTERN = re.compile(
    r"""\(\s*['"]("""
    + "|".join(re.escape(t) for t in sorted(_DICT_KEY_DOMAIN_EMITTERS))
    + r""")['"]\s*,\s*\[""",
    re.MULTILINE,
)

# Form 3 — variable assignment to a flat list containing legacy domain terms:
#   _DOMAINS = ['career', 'health', 'relationship', 'finance', 'spiritual', ...]
# This only fires when the entire list is assigned to a name ending in DOMAINS
# (uppercase convention), not on keyword-value lists inside dicts.
_FLAT_LIST_DOMAIN_PATTERN = re.compile(
    r"""_DOMAINS\s*=\s*\[(?=[^\]]*?['"](career|health|wealth)['"]).{0,400}?['"]("""
    + "|".join(re.escape(t) for t in sorted(_DICT_KEY_DOMAIN_EMITTERS))
    + r""")['"]\s*[,\]]""",
    re.DOTALL,
)


def _is_excluded(path: pathlib.Path) -> bool:
    """True if this file should be skipped by the census gate."""
    name = path.name
    if name in _SAFE_FILE_STEMS:
        return True
    for pat in _TEST_FILE_PATTERNS:
        if pat in name or pat in str(path):
            return True
    # Skip __pycache__ and .pyc
    if '__pycache__' in str(path) or name.endswith('.pyc'):
        return True
    return False


def _collect_py_files() -> list[pathlib.Path]:
    """Collect all Python writer + service files to scan."""
    files = []
    for d in (_WRITERS_DIR, _SERVICES_DIR):
        if d.is_dir():
            for p in d.rglob("*.py"):
                if not _is_excluded(p):
                    files.append(p)
    return files


def _strip_non_code(source: str) -> str:
    """Remove docstrings and comments so we only match in executable code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source  # can't parse — return raw (conservative)

    # Collect line ranges covered by string constants (docstrings)
    docstring_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                # multi-line string: mark all its lines as docstring
                end = getattr(node.value, 'end_lineno', node.value.lineno)
                for ln in range(node.value.lineno, end + 1):
                    docstring_lines.add(ln)

    # Strip single-line comments and docstring lines
    lines = []
    for i, line in enumerate(source.splitlines(), start=1):
        if i in docstring_lines:
            lines.append("")
            continue
        stripped = line.lstrip()
        if stripped.startswith('#'):
            lines.append("")
            continue
        # Inline comment: drop from first unquoted '#'
        cleaned = re.sub(r'(?<![\'"\\])#.*$', '', line)
        lines.append(cleaned)
    return "\n".join(lines)


def _find_violations_in_file(path: pathlib.Path) -> list[tuple[str, str, int]]:
    """Return list of (legacy_term, match_snippet, approx_line) violations."""
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return []

    code = _strip_non_code(source)
    violations = []
    seen: set[int] = set()  # dedup by line number to avoid double-reporting

    for pat in (_DICT_KEY_PATTERN, _TUPLE_DOMAIN_PATTERN, _FLAT_LIST_DOMAIN_PATTERN):
        for m in pat.finditer(code):
            line_no = code[:m.start()].count('\n') + 1
            if line_no in seen:
                continue
            seen.add(line_no)
            # Extract the legacy term: group(1) for DICT/TUPLE, group(2) for FLAT_LIST
            if pat is _FLAT_LIST_DOMAIN_PATTERN:
                term = m.group(2)
            else:
                term = m.group(1)
            snippet = m.group(0).strip()[:80]
            violations.append((term, snippet, line_no))

    return violations


# ═══════════════════════════════════════════════════════════════════════════════
# DELIVERABLE 2: CI vocabulary-census gate
# ═══════════════════════════════════════════════════════════════════════════════


def test_census_gate_known_violations_are_detected():
    """FAILING-FIRST: Confirms the scanner correctly identifies known violations.

    The files listed in _KNOWN_VIOLATIONS are confirmed legacy-domain emitters —
    they use 'finance' or 'spiritual' as dict keys whose values flow into DB domain
    columns. This test asserts the scanner finds them, so if someone migrates one of
    these files and forgets to remove it from the list, this test catches the drift
    (a violation in the other direction).
    """
    # Files confirmed to still have violations on this branch.
    # Remove an entry when the file is migrated (the zero-violations gate will catch
    # any regression — this dict is for "confirm scanner detects the known cases").
    # Previously included: ka_bhavishya_lekha.py (fixed by L5 lane), ka_yojaka.py (fixed).
    _KNOWN_VIOLATIONS = {
        "mi_sambandha.py": {"finance"},
    }

    all_files = _collect_py_files()
    file_by_name = {p.name: p for p in all_files}

    for filename, expected_terms in _KNOWN_VIOLATIONS.items():
        p = file_by_name.get(filename)
        if p is None:
            pytest.skip(f"{filename} not found in scan paths — may have been migrated")
        violations = _find_violations_in_file(p)
        found_terms = {v[0] for v in violations}
        missing = expected_terms - found_terms
        assert not missing, (
            f"{filename}: scanner did not detect expected legacy terms {sorted(missing)}. "
            f"If the file was migrated, remove it from _KNOWN_VIOLATIONS."
        )


def test_census_gate_zero_legacy_domain_literals():
    """GATE: zero legacy domain literals outside of synonym definitions.

    This is the CI gate that prevents future vocabulary regression. It PASSES only
    when no file outside the safe-list uses a legacy domain term as a dict key in a
    domain-classifying map. When this test fails, the failure message lists each
    file, the legacy term found, and the approximate line number so the fix is
    unambiguous.

    CURRENT STATE: This test is expected to FAIL on the un-migrated codebase (the
    known violations listed in test_census_gate_known_violations_are_detected above).
    It will pass once those files are migrated to use canonical_domain() instead of
    raw legacy strings. The test is committed in its failing state as the CI gate
    that makes those migrations mandatory.
    """
    files = _collect_py_files()
    violations_by_file: dict[str, list[tuple[str, str, int]]] = {}

    for path in sorted(files):
        viols = _find_violations_in_file(path)
        if viols:
            rel = str(path.relative_to(_SIDECAR))
            violations_by_file[rel] = viols

    if violations_by_file:
        lines = ["Legacy domain literals found (migrate to canonical_domain()):"]
        for fname, viols in sorted(violations_by_file.items()):
            for term, snippet, lineno in viols:
                lines.append(f"  {fname}:{lineno}: {term!r} — {snippet!r}")
        pytest.fail("\n".join(lines))


def test_census_gate_safe_exclusions_do_not_fire():
    """Excluded files do not appear in the census scan output.

    _collect_py_files() applies exclusions before scanning. This test confirms that
    the files in _SAFE_FILE_STEMS are absent from the collected set, so they never
    reach _find_violations_in_file at all.
    """
    collected = {p.name for p in _collect_py_files()}
    for safe_name in _SAFE_FILE_STEMS:
        assert safe_name not in collected, (
            f"{safe_name} is in _SAFE_FILE_STEMS but was NOT excluded from scan — "
            f"_is_excluded() logic needs updating."
        )
    # Also confirm the test file itself is excluded
    assert "test_domain_vocabulary_census.py" not in collected
    assert "test_domain_vocabulary.py" not in collected


def test_census_scanner_finds_py_files():
    """Sanity: scanner finds at least the known writers in the expected directories."""
    files = _collect_py_files()
    names = {p.name for p in files}
    assert "ka_bhavishya_lekha.py" in names, "ka_bhavishya_lekha.py not found in scan"
    assert "ka_yojaka.py" in names, "ka_yojaka.py not found in scan"
    assert "mi_sambandha.py" in names, "mi_sambandha.py not found in scan"
    # test files themselves must be excluded
    assert "test_domain_vocabulary_census.py" not in names, (
        "test file should be excluded from scan"
    )
    assert "test_domain_vocabulary.py" not in names, (
        "test file should be excluded from scan"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DELIVERABLE 3: Empty-evidence lint for the P2 pattern (§N.8)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Detects code that produces a verdict/status/grade from empty evidence without
# honestly labeling it as such. Three concrete pattern classes:
#
#   P2a: status = 'denied' (or similar) when evidence lists are empty
#        (the bo_pratijna defect: grade=0.0 < 2.0 → 'denied' even with zero signals)
#   P2b: leakage = "clean" hardcoded without a detector (mi_adhilepa defect)
#   P2c: = "light" hardcoded in intensity/severity fields
#
# Approach: grep for specific literal patterns. For P2a we look for the combination
# of _grade_to_status-style functions where 'denied' is returned without any guard
# for empty inputs. For P2b/P2c we look for unconditional literal assignments.

_P2B_CLEAN_PATTERN = re.compile(
    # Matches: leakage = "clean"  BUT NOT:  leakage = "clean" if <condition> else <other>
    # The negative lookahead (?!\s+if) excludes the ternary form, which has a real detector.
    r"""(?<!\w)leakage\s*=\s*["']clean["'](?!\s+if)""",
    re.MULTILINE,
)

_P2C_LIGHT_PATTERN = re.compile(
    r"""(?:intensity|severity|magnitude)\s*=\s*["']light["']""",
    re.MULTILINE,
)

# P2a: 'denied' assigned in a function that does NOT guard for empty supporting list.
# We detect: return "denied" or return 'denied' inside any function body.
_P2A_DENIED_RETURN = re.compile(
    r"""return\s+["']denied["']""",
    re.MULTILINE,
)

# We also look for:  status = 'denied'  as a direct assignment (not a comparison)
_P2A_DENIED_ASSIGN = re.compile(
    r"""(?<!\w)(?:status|state)\s*=\s*["']denied["']""",
    re.MULTILINE,
)


def _scan_p2_patterns(
    path: pathlib.Path,
) -> dict[str, list[tuple[str, int]]]:
    """Return {pattern_class: [(snippet, lineno), ...]} for P2 patterns found."""
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return {}

    code = _strip_non_code(source)
    results: dict[str, list[tuple[str, int]]] = {}

    for label, pat in [
        ("P2a_denied_return", _P2A_DENIED_RETURN),
        ("P2a_denied_assign", _P2A_DENIED_ASSIGN),
        ("P2b_leakage_clean", _P2B_CLEAN_PATTERN),
        ("P2c_light_literal", _P2C_LIGHT_PATTERN),
    ]:
        hits = []
        for m in pat.finditer(code):
            lineno = code[:m.start()].count('\n') + 1
            hits.append((m.group(0).strip(), lineno))
        if hits:
            results[label] = hits
    return results


def test_p2_known_instances_are_detected():
    """FAILING-FIRST: The scanner finds the documented P2 defect instances.

    These are the instances documented in the SHABDA-SHUDDHI campaign brief.
    When they are fixed, remove the corresponding entry.
    """
    # Files confirmed to still have P2 instances on this branch.
    # Previously included: mi_adhilepa.py (P2b — fixed by L5 lane: leakage = None now).
    _KNOWN_P2_INSTANCES = {
        "bo_pratijna.py": "P2a_denied_return",   # _grade_to_status returns 'denied'
    }

    all_files = _collect_py_files()
    file_by_name = {p.name: p for p in all_files}

    for filename, expected_class in _KNOWN_P2_INSTANCES.items():
        p = file_by_name.get(filename)
        if p is None:
            pytest.skip(f"{filename} not found — may have been fixed and deleted")
        found = _scan_p2_patterns(p)
        assert expected_class in found, (
            f"{filename}: expected P2 pattern class {expected_class!r} not detected. "
            f"If the defect was fixed, remove it from _KNOWN_P2_INSTANCES."
        )


def test_p2_empty_evidence_lint_zero_violations():
    """GATE: zero P2 (empty-evidence) pattern violations in writers + services.

    §N.8 Earned-Signal Principle: every status/grade/PASS must be computed by a
    detector that measures the specific claim it asserts.

    This test FAILS on the un-migrated codebase (bo_pratijna 'denied' on empty
    evidence; mi_adhilepa unconditional leakage = "clean"). It will pass once:
      - bo_pratijna._grade_to_status guards empty supporting + contradicting lists
        and returns 'inconclusive' or similar rather than 'denied'.
      - mi_adhilepa._overlay_row's leakage is computed from a real detector.

    IMPORTANT: 'denied' is a legitimate status when evidence DOES exist and the
    grade is below threshold. The defect is only when supporting_ids AND
    contradicting_ids are both empty, making grade=0.0 which is always < _DENIED_CEIL.
    The lint flags ALL 'denied' returns as requiring review; human judgement is
    needed to confirm whether the guard exists.
    """
    files = _collect_py_files()
    violations_by_file: dict[str, dict[str, list[tuple[str, int]]]] = {}

    for path in sorted(files):
        found = _scan_p2_patterns(path)
        if found:
            rel = str(path.relative_to(_SIDECAR))
            violations_by_file[rel] = found

    if violations_by_file:
        lines = [
            "P2 pattern (empty-evidence verdict) violations found (§N.8):",
            "  Verify each site has a real detector behind its status/grade/leakage.",
        ]
        for fname, patterns in sorted(violations_by_file.items()):
            for pclass, hits in sorted(patterns.items()):
                for snippet, lineno in hits:
                    lines.append(f"  {fname}:{lineno} [{pclass}]: {snippet!r}")
        pytest.fail("\n".join(lines))


def test_p2_scanner_finds_writers():
    """Sanity: scanner finds known writers in the scan paths."""
    files = _collect_py_files()
    names = {p.name for p in files}
    assert "bo_pratijna.py" in names
    assert "mi_adhilepa.py" in names
