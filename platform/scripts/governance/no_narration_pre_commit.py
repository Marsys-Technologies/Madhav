#!/usr/bin/env python3
"""
INF8-S2: No-narration pre-commit hook.

Scans staged files for no-narration violations:
  - Python files: scans any string literals assigned to fact_value_text
  - Markdown files: scans full content
  - JSON files: scans any "fact_value_text" field values

Usage (pre-commit framework — add to .pre-commit-config.yaml):
    - id: no-narration
      name: No-narration linter
      entry: python platform/scripts/governance/no_narration_pre_commit.py
      language: python
      types: [python, markdown]

Usage (standalone — run manually or in CI against a directory):
    python platform/scripts/governance/no_narration_pre_commit.py [paths...]

Exit code 0 = clean, 1 = violations found.

[BUILD-ORCH-INF8-S2] INF8-S2
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# Resolve paths relative to this script's location so it works from any CWD
_SCRIPT_DIR = Path(__file__).parent.resolve()
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent

# ── No-narration pattern (mirrors no_narration_linter.py) ────────────────────

_FORBIDDEN = re.compile(
    r'\bindicates?\b|\bsuggests?\b|\bimplies?\b|\bmeans?\s+that\b'
    r'|\bdenotes?\b|\breveals?\b|\bshows?\b|\bdemonstrates?\b'
    r'|\bpoints?\s+to\b|\bsignifies?\b|\brepresents?\b|\bsymbolizes?\b',
    re.IGNORECASE,
)

# ── File scanners ─────────────────────────────────────────────────────────────


def scan_markdown(path: Path) -> list[tuple[int, str]]:
    """Return (line_no, phrase) for each violation in a markdown file."""
    violations: list[tuple[int, str]] = []
    for line_no, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        m = _FORBIDDEN.search(line)
        if m:
            violations.append((line_no, m.group(0)))
    return violations


def scan_python(path: Path) -> list[tuple[int, str]]:
    """Scan Python string literals for fact_value_text assignments."""
    violations: list[tuple[int, str]] = []
    text = path.read_text(encoding='utf-8', errors='replace')
    # Look for fact_value_text = "..." or fact_value_text: "..." patterns
    in_value = False
    for line_no, line in enumerate(text.splitlines(), 1):
        if 'fact_value_text' in line and '=' in line or 'fact_value_text' in line and ':' in line:
            in_value = True
        if in_value:
            m = _FORBIDDEN.search(line)
            if m:
                violations.append((line_no, m.group(0)))
            # Reset after the value line (simple heuristic)
            if in_value and (line.strip().endswith(',') or line.strip().endswith('"') or line.strip().endswith("'")):
                in_value = False
    return violations


def scan_json(path: Path) -> list[tuple[int, str]]:
    """Scan JSON files for fact_value_text field violations."""
    violations: list[tuple[int, str]] = []
    try:
        data = json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except json.JSONDecodeError:
        return []

    def walk(obj: object, depth: int = 0) -> None:
        if depth > 20:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'fact_value_text' and isinstance(v, str):
                    m = _FORBIDDEN.search(v)
                    if m:
                        violations.append((0, m.group(0)))
                walk(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, depth + 1)

    walk(data)
    return violations


# ── Staged files discovery ────────────────────────────────────────────────────


def get_staged_files() -> list[Path]:
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(_REPO_ROOT),
        )
        return [_REPO_ROOT / f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []


# ── Main ──────────────────────────────────────────────────────────────────────


def main(paths: list[Path] | None = None) -> int:
    """Scan paths (or staged files if paths is None). Returns exit code."""
    targets = paths if paths is not None else get_staged_files()

    total_violations = 0
    for p in targets:
        if not p.is_file():
            continue
        # Skip test files — they intentionally contain violation strings as fixtures
        if any(part in ('__tests__', 'tests', 'test') for part in p.parts):
            continue
        if p.name.startswith('test_') or p.name.endswith('_test.py'):
            continue
        suffix = p.suffix.lower()
        violations: list[tuple[int, str]] = []

        if suffix == '.md':
            violations = scan_markdown(p)
        elif suffix == '.py':
            violations = scan_python(p)
        elif suffix == '.json':
            violations = scan_json(p)
        else:
            continue

        for line_no, phrase in violations:
            loc = f'{p}:{line_no}' if line_no else str(p)
            print(f'[no-narration] VIOLATION in {loc}: \'{phrase}\'', file=sys.stderr)
            total_violations += 1

    if total_violations:
        print(
            f'\n[no-narration] {total_violations} violation(s) found. '
            'Remove narrative interpretation verbs from fact_value_text fields.',
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == '__main__':
    explicit_paths = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    sys.exit(main(explicit_paths))
