#!/usr/bin/env python3
"""check_no_raw_token_in_narrative.py — D-01e: no raw internal token in narrative fields.

EKAVĀKYATĀ guard (F-131/F-132; A-14). Narrative text fields (_thesis, _text,
signal_headline_text, signal_text) must not embed raw internal tokens directly:

Known defect sites:
  - platform-mcp/src/tools/kala_views/now.ts:  reading.thesis interpolates
    `(window.signature_classes ?? []).join('/')` → raw 'CLASSIFY_RESIDUAL/DIGNITY/YOGA'
  - platform/python-sidecar/**/*.py: signal_headline_text built with
    f"{signal_type_id}: ..." or f"GRAHA: ..." raw templates

What it flags
-------------
Pattern A (TypeScript):
  Any line where `signature_classes` appears within the same expression as `.join('/')`.
  The slash separator produces raw enum tokens (CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM)
  that are not human-readable in a narrative field.
  SAFE: `.map(glossFn).join(...)` — classes are glossed before joining; not flagged.

Pattern B1 (Python):
  Any line where `signal_headline_text`, `signal_text`, `_thesis`, or `_narrative`
  is assigned an f-string containing `{signal_type_id}` directly.
  SAFE: assigning the result of a gloss helper function — not flagged.

Pattern B2 (Python):
  Any line where the above field names are assigned an f-string whose literal content
  starts with a raw internal-token prefix: GRAHA:, CLASSIFY_RESIDUAL, YOGA:,
  DIGNITY:, or SUBSYSTEM:.
  SAFE: f-string that starts with a human-readable graha name or label — not flagged.

False-negative boundary:
  - `.join(' / ')` (spaces around slash) is NOT flagged; rare display choice.
  - A function-call result (not an f-string) assigned to signal_headline_text is NOT flagged.
False-positive boundary:
  - `.map(glossClass).join(...)` is safe — classes are glossed first.
  - gloss-map lookups or helper-function calls assigned to narrative fields are safe.

Exit codes: 0 clean, 1 violation(s), 2 invocation error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
FIXTURE_DIR = SCRIPT_DIR / "no_raw_token_narrative_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "no_raw_token_narrative_allowlist.json"

DEFAULT_TS_GLOBS = ["platform-mcp/src/**/*.ts", "platform/src/**/*.ts"]
DEFAULT_PY_GLOBS = ["platform/python-sidecar/**/*.py"]

EXCLUDE_SUBSTRINGS = (
    "no_raw_token_narrative_fixtures/",
    "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    ".test.ts", ".spec.ts",
)

# Pattern A (TypeScript): signature_classes joined with '/' separator.
# Matches expressions where `signature_classes` precedes `.join('/')` on the same line.
# Does NOT match `.map(fn).join(...)` with a different separator.
_RE_TS_RAW_CLASSES_JOIN = re.compile(
    r"signature_classes\b[^\n]*\.join\s*\(\s*['\"][/]['\"]",
)

# Pattern B1 (Python): direct {signal_type_id} interpolation into a narrative field.
# Matches: signal_headline_text = f"{signal_type_id}: ..."
# Also:    "signal_headline_text": f"{signal_type_id}..."
_NARRATIVE_FIELDS = r"(?:signal_headline_text|signal_text|_thesis|_narrative)"
_RE_PY_TYPE_ID_IN_TEXT = re.compile(
    r"""(?:["\'])?""" + _NARRATIVE_FIELDS + r"""(?:["\'])?\s*[:=]\s*f["\'][^\n]*\{signal_type_id\}""",
)

# Pattern B2 (Python): literal raw internal-token prefix in an f-string narrative assignment.
# Matches: "signal_headline_text": f"GRAHA: ..." or signal_headline_text = f"YOGA: ..."
_RAW_TOKEN_PREFIX_RE = r"(?:GRAHA|CLASSIFY_RESIDUAL|YOGA|DIGNITY|SUBSYSTEM):"
_RE_PY_RAW_PREFIX_IN_TEXT = re.compile(
    r"""(?:["\'])?""" + _NARRATIVE_FIELDS + r"""(?:["\'])?\s*[:=]\s*f["\']""" + _RAW_TOKEN_PREFIX_RE,
)


def _excluded(rel: str) -> bool:
    return any(s in rel for s in EXCLUDE_SUBSTRINGS)


def expand_globs(root: Path, globs: Sequence[str]) -> List[Path]:
    out: set = set()
    for pattern in globs:
        for match in root.glob(pattern):
            if match.is_file():
                rel = match.relative_to(root).as_posix()
                if not _excluded(rel):
                    out.add(match)
    return sorted(out)


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    kind: str
    snippet: str
    message: str

    def key(self) -> str:
        return f"{self.file}|{self.kind}|{self.line}"


def scan_ts_file(text: str) -> List[tuple]:
    """Return list of (line_no, kind, snippet) hits for a TypeScript file."""
    hits = []
    for m in _RE_TS_RAW_CLASSES_JOIN.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(m.group().split())[:160]
        hits.append((line, "ts_raw_classes_join", snippet))
    return hits


def scan_py_file(text: str) -> List[tuple]:
    """Return list of (line_no, kind, snippet) hits for a Python file."""
    hits = []
    for m in _RE_PY_TYPE_ID_IN_TEXT.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(m.group().split())[:160]
        hits.append((line, "py_signal_type_id_in_text", snippet))
    for m in _RE_PY_RAW_PREFIX_IN_TEXT.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(m.group().split())[:160]
        hits.append((line, "py_raw_token_prefix_in_text", snippet))
    return hits


_KIND_MESSAGE = {
    "ts_raw_classes_join": (
        "signature_classes.join('/') embeds raw internal enum tokens in narrative text. "
        "Gloss classes through a display-label map before joining "
        "(A-14; no-raw-token-in-narrative guard D-01e)."
    ),
    "py_signal_type_id_in_text": (
        "f\"{signal_type_id}:...\" in narrative field embeds raw internal MSR token. "
        "Map signal_type_id through a human-readable gloss dict before interpolating "
        "(F-131; no-raw-token-in-narrative guard D-01e)."
    ),
    "py_raw_token_prefix_in_text": (
        "Raw internal-token prefix (GRAHA:/YOGA:/etc.) in f-string narrative field. "
        "Use a human-readable gloss map instead of hardcoding the raw token literal "
        "(F-132; no-raw-token-in-narrative guard D-01e)."
    ),
}


def scan_repo(root: Path, ts_globs: Sequence[str], py_globs: Sequence[str]) -> List[Violation]:
    violations = []
    for path in expand_globs(root, ts_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_ts_file(text):
            violations.append(Violation(
                file=rel, line=line, kind=kind, snippet=snippet,
                message=_KIND_MESSAGE[kind],
            ))
    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_py_file(text):
            violations.append(Violation(
                file=rel, line=line, kind=kind, snippet=snippet,
                message=_KIND_MESSAGE[kind],
            ))
    return violations


def load_allowlist(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []


def _matches_entry(v: Violation, entry: dict) -> bool:
    if entry.get("file") != v.file:
        return False
    if "line" in entry and entry["line"] is not None:
        return int(entry["line"]) == v.line
    pat = entry.get("pattern")
    if pat:
        try:
            return bool(re.search(pat, v.snippet))
        except re.error:
            return pat in v.snippet
    return False


def partition_allowlisted(violations, allowlist):
    allowed, new = [], []
    for v in violations:
        if any(_matches_entry(v, e) for e in allowlist):
            allowed.append(v)
        else:
            new.append(v)
    return allowed, new


def print_violations(violations, prefix=""):
    for v in violations:
        print(f"{prefix}[{v.kind}] {v.file}:{v.line} — {v.message}")
        print(f"{prefix}    {v.snippet}")


def run_self_test() -> int:
    pass_dir = FIXTURE_DIR / "pass"
    fail_dir = FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print("check_no_raw_token_in_narrative: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2
    failures = []
    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file():
            continue
        text = fixture.read_text(encoding="utf-8")
        if fixture.suffix == ".ts":
            hits = scan_ts_file(text)
        elif fixture.suffix == ".py":
            hits = scan_py_file(text)
        else:
            continue
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged: {hits}")
    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file():
            continue
        text = fixture.read_text(encoding="utf-8")
        if fixture.suffix == ".ts":
            hits = scan_ts_file(text)
        elif fixture.suffix == ".py":
            hits = scan_py_file(text)
        else:
            continue
        if not hits:
            failures.append(f"FAIL-fixture '{fixture.name}' produced no violation")
    if failures:
        print("check_no_raw_token_in_narrative: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    pass_count = sum(1 for f in pass_dir.iterdir() if f.is_file() and f.suffix in (".ts", ".py"))
    fail_count = sum(1 for f in fail_dir.iterdir() if f.is_file() and f.suffix in (".ts", ".py"))
    print(f"check_no_raw_token_in_narrative: SELF-TEST PASS ({pass_count} pass, {fail_count} fail fixtures).")
    return 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--root", default=str(REPO_ROOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    violations = scan_repo(root, DEFAULT_TS_GLOBS, DEFAULT_PY_GLOBS)
    allowlist = load_allowlist(ALLOWLIST_PATH)
    allowed, new = partition_allowlisted(violations, allowlist)

    if args.json:
        print(json.dumps({
            "total": len(violations), "allowlisted": len(allowed),
            "new": [v.__dict__ for v in new],
            "pass": not (args.strict and violations) and not new,
        }, indent=2))
        return 1 if (args.strict and violations) or new else 0

    if allowed:
        print(f"check_no_raw_token_in_narrative: {len(allowed)} allowlisted (see allowlist):")
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(f"check_no_raw_token_in_narrative: STRICT — {len(violations)} violation(s). FAIL.", file=sys.stderr)
        return 1

    if new:
        print(f"check_no_raw_token_in_narrative: {len(new)} NEW violation(s). FAIL.", file=sys.stderr)
        print_violations(new, prefix="  ")
        return 1

    print(f"check_no_raw_token_in_narrative: 0 new violations ({len(allowed)} allowlisted). PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
