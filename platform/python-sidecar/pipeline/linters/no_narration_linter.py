"""
INF8-S1: No-Narration Enforcement Linter — standalone module.

Scans rendered markdown or fact_value_text for forbidden narrative verbs that
violate the M4 no-narration principle.  Raises NoNarrationViolationError with
the line number and offending phrase on the first violation found.

Forbidden verbs (INF8 / M4 decision):
  indicates, suggests, implies, means that, denotes, reveals, shows,
  demonstrates, points to, signifies, represents, symbolizes

Usage:
    from pipeline.linters.no_narration_linter import lint, lint_rows, NoNarrationViolationError

    lint("Sun in Capricorn [FORENSIC §3.1]")  # OK — raises nothing
    lint("This indicates a strong career.")    # raises NoNarrationViolationError

[BUILD-ORCH-INF8-S1] INF8-S1
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence

# ── Forbidden verb patterns ───────────────────────────────────────────────────

FORBIDDEN_VERBS: list[str] = [
    r'\bindicates?\b',
    r'\bsuggests?\b',
    r'\bimplies?\b',
    r'\bmeans?\s+that\b',
    r'\bdenotes?\b',
    r'\breveals?\b',
    r'\bshows?\b',
    r'\bdemonstrates?\b',
    r'\bpoints?\s+to\b',
    r'\bsignifies?\b',
    r'\brepresents?\b',
    r'\bsymbolizes?\b',
]

_PATTERN: re.Pattern[str] = re.compile(
    '|'.join(FORBIDDEN_VERBS),
    re.IGNORECASE,
)

# ── Error type ────────────────────────────────────────────────────────────────


@dataclass
class Violation:
    line_number: int
    line_text: str
    offending_phrase: str


class NoNarrationViolationError(Exception):
    """Raised when a no-narration violation is detected.

    Attributes:
        violations: All violations found (first match per line, first line only
                    in strict mode).
        source_hint: Optional label identifying the source being linted.
    """

    violations: list[Violation]
    source_hint: Optional[str]

    def __init__(
        self,
        violations: list[Violation],
        source_hint: Optional[str] = None,
    ) -> None:
        self.violations = violations
        self.source_hint = source_hint
        first = violations[0]
        label = f" in {source_hint!r}" if source_hint else ""
        super().__init__(
            f"No-narration violation{label} "
            f"at line {first.line_number}: "
            f"'{first.offending_phrase}' "
            f"— remove narrative interpretation verbs from fact text."
        )


# ── Public API ────────────────────────────────────────────────────────────────


def lint(
    text: str,
    source_hint: Optional[str] = None,
    *,
    strict: bool = True,
) -> None:
    """Scan *text* for forbidden narrative verbs.

    Args:
        text:        The text to scan (rendered markdown or fact_value_text).
        source_hint: Optional label for the error message (e.g. section name).
        strict:      When True (default), raise on the first violation found.
                     When False, collect all violations and raise once at end.

    Raises:
        NoNarrationViolationError: On any violation.
    """
    violations = _scan(text)
    if violations:
        if strict:
            raise NoNarrationViolationError([violations[0]], source_hint)
        else:
            raise NoNarrationViolationError(violations, source_hint)


def lint_rows(
    rows: Sequence[dict],
    text_field: str = 'fact_value_text',
    id_field: str = 'fact_id',
) -> list[tuple[str, Violation]]:
    """Scan a list of chart_facts-style row dicts.

    Returns a list of (row_id, Violation) pairs for every row that fails.
    Does NOT raise — caller decides how to handle bulk violations.
    """
    failures: list[tuple[str, Violation]] = []
    for row in rows:
        text = row.get(text_field) or ''
        if not text:
            continue
        violations = _scan(text)
        if violations:
            row_id = str(row.get(id_field, 'unknown'))
            failures.append((row_id, violations[0]))
    return failures


def check(text: str) -> list[Violation]:
    """Non-raising version — returns all violations or empty list."""
    return _scan(text)


# ── Internals ─────────────────────────────────────────────────────────────────


def _scan(text: str) -> list[Violation]:
    violations: list[Violation] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        m = _PATTERN.search(line)
        if m:
            violations.append(
                Violation(
                    line_number=line_no,
                    line_text=line,
                    offending_phrase=m.group(0),
                )
            )
    return violations
