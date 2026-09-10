#!/usr/bin/env python3
"""check_dualoutput_requires_toolname.py — D-01d: dualOutput must carry a toolName.

EKAVĀKYATĀ guard (F-43; A-09 class). Every file-local `function dualOutput` definition
must NOT use `'unknown_tool'` as the toolName default. The broken instance:

  - platform-mcp/src/tools/register_p1_aliases.ts:188
    function dualOutput(data: unknown, toolName = 'unknown_tool') {...}
    — any call site that omits toolName inherits 'unknown_tool', making
    recover_via pointers in MCP error objects useless (~19 downstream call sites).

A-09's fix is to either: (a) give each file's dualOutput a real tool-name default, or
(b) migrate to the shared kalaBudgetedDualOutput / envelope pattern, which always
threads toolName explicitly.

What it flags (TypeScript)
--------------------------
  (a) DEFINITION defect: `function dualOutput(...)` whose parameter list contains
      `toolName = 'unknown_tool'` — the literal string 'unknown_tool' as a default.

  (b) CALL-SITE defect (contextual): in any file where the local dualOutput
      definition has `'unknown_tool'` default, a bare `dualOutput(data)` call
      with exactly ONE argument — because that call inherits the broken default.

False-negative boundary:
  - A `dualOutput` call with 2 args where the second is a variable (not a literal)
    is NOT flagged even if the variable happens to be undefined. The lint trusts
    that explicit 2-arg calls intend to supply a real tool name.
  - `kalaBudgetedDualOutput(content, TOOL_NAME)` calls are never flagged.
False-positive boundary:
  - `function dualOutput(..., toolName = 'kala_now_get')` is SAFE (real name).
  - `dualOutput(data, TOOL_NAME)` is SAFE (explicit second arg).

Exit codes: 0 clean, 1 violation(s), 2 invocation error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Set

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
FIXTURE_DIR = SCRIPT_DIR / "dualoutput_toolname_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "dualoutput_toolname_allowlist.json"

DEFAULT_TS_GLOBS = ["platform-mcp/src/**/*.ts"]

EXCLUDE_SUBSTRINGS = (
    "dualoutput_toolname_fixtures/",
    "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    ".test.ts", ".spec.ts",
    # shared.ts exports kalaBudgetedDualOutput — the canonical replacement, never flag
    "kala_views/shared.ts",
)

# Pattern A: function definition with 'unknown_tool' default
_RE_DUAL_DEF_BAD = re.compile(
    r"function\s+dualOutput\s*\([^)]*toolName\s*=\s*'unknown_tool'[^)]*\)",
    re.MULTILINE,
)

# Pattern B: bare dualOutput call with exactly one argument
# Matches: dualOutput(expr) where expr does not contain a top-level comma
# (i.e. only 1 argument). We use a bracket-counting approach.
_RE_DUAL_CALL = re.compile(r"\bdualOutput\s*\(")


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


def _extract_args(text: str, open_paren_idx: int) -> tuple:
    """Return (arg_text, index_after_closing_paren) using bracket counting."""
    depth = 0
    i = open_paren_idx
    start = i + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    return text[start:], n


def _count_top_level_args(arg_text: str) -> int:
    """Count comma-separated top-level arguments (ignoring commas inside brackets)."""
    depth = 0
    count = 1
    for c in arg_text:
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            count += 1
    return count if arg_text.strip() else 0


def scan_ts_file(text: str) -> List[tuple]:
    hits = []
    has_bad_def = bool(_RE_DUAL_DEF_BAD.search(text))

    # Pattern A: bad definition
    for m in _RE_DUAL_DEF_BAD.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(m.group().split())[:160]
        hits.append((line, "bad_default_def", snippet))

    # Pattern B: bare 1-arg calls (only in files that have the bad definition)
    if has_bad_def:
        for m in _RE_DUAL_CALL.finditer(text):
            open_idx = m.end() - 1
            arg_text, _ = _extract_args(text, open_idx)
            n_args = _count_top_level_args(arg_text)
            if n_args == 1:
                line = text.count("\n", 0, m.start()) + 1
                snippet = f"dualOutput({arg_text.strip()[:80]})"
                hits.append((line, "bare_call_no_toolname", snippet))

    return hits


def scan_repo(root: Path, ts_globs: Sequence[str]) -> List[Violation]:
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
                message=(
                    f"dualOutput toolName defect '{kind}': "
                    "'unknown_tool' default makes recover_via pointers useless. "
                    "Give dualOutput a real tool-name default or use kalaBudgetedDualOutput "
                    "(A-09; dualOutput-requires-toolName guard D-01d)."
                ),
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
        print("check_dualoutput_requires_toolname: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2
    failures = []
    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".ts":
            continue
        hits = scan_ts_file(fixture.read_text(encoding="utf-8"))
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged: {hits}")
    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".ts":
            continue
        hits = scan_ts_file(fixture.read_text(encoding="utf-8"))
        if not hits:
            failures.append(f"FAIL-fixture '{fixture.name}' produced no violation")
    if failures:
        print("check_dualoutput_requires_toolname: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    pass_count = sum(1 for f in pass_dir.iterdir() if f.is_file() and f.suffix == ".ts")
    fail_count = sum(1 for f in fail_dir.iterdir() if f.is_file() and f.suffix == ".ts")
    print(f"check_dualoutput_requires_toolname: SELF-TEST PASS ({pass_count} pass, {fail_count} fail fixtures).")
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
    violations = scan_repo(root, DEFAULT_TS_GLOBS)
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
        print(f"check_dualoutput_requires_toolname: {len(allowed)} allowlisted (see allowlist):")
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(f"check_dualoutput_requires_toolname: STRICT — {len(violations)} violation(s). FAIL.", file=sys.stderr)
        return 1

    if new:
        print(f"check_dualoutput_requires_toolname: {len(new)} NEW violation(s). FAIL.", file=sys.stderr)
        print_violations(new, prefix="  ")
        return 1

    print(f"check_dualoutput_requires_toolname: 0 new violations ({len(allowed)} allowlisted). PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
