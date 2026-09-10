#!/usr/bin/env python3
"""check_no_local_ayanamsha_map.py — D-01c: No file-local ayanamsha alias map.

EKAVĀKYATĀ guard (F-59; A-15 class). Permanent CI enforcement that no TypeScript
file outside the canonical helper defines its own ayanamsha alias translation map.
The broken instance:

  - platform-mcp/src/tools/register_p1_aliases.ts:39-43
    const AYANAMSHA_ALIAS: Record<string, string> = {
      lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', ...
      true_chitra: 'lahiri_chitrapaksha',
    }
    function na(id?: string): string { ... }
    This silently rewrites 'true_chitra' -> 'lahiri_chitrapaksha', hiding the
    true_chitra dataset. A-15 wires resolveChartFactsAyanamsha at all 11 sites.

What it flags (TypeScript)
--------------------------
Any .ts file that defines a local const of type Record<string, string> (or equivalent
inline object literal) whose variable name contains 'AYANAMSHA' or 'ayanamsha'
AND whose values contain known ayanamsha identifier substrings
('chitrapaksha', 'lahiri', 'krishnamurti', 'raman', 'surya_siddhanta', 'invariant').

Canonical helper (never flagged):
  platform-mcp/src/tools/register_p1_aliases.ts resolveChartFactsAyanamsha import
  (the import line itself is SAFE — only the local definition is flagged)
  platform/src/lib/retrieval/chart_facts_helpers.ts  (the helper definition)

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
FIXTURE_DIR = SCRIPT_DIR / "no_local_ayanamsha_map_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "no_local_ayanamsha_map_allowlist.json"

DEFAULT_TS_GLOBS = ["platform-mcp/src/**/*.ts", "platform/src/**/*.ts"]

EXCLUDE_SUBSTRINGS = (
    "no_local_ayanamsha_map_fixtures/",
    "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    ".test.ts", ".spec.ts",
    # The canonical helper definition — never flag it
    "chart_facts_helpers.ts",
    # The test/fixture files
    "resolveChartFactsAyanamsha",
)

KNOWN_AYANAMSHA_VALUES = re.compile(
    r"chitrapaksha|lahiri|krishnamurti|raman|surya_siddhanta|invariant",
    re.IGNORECASE,
)

# Pattern: const/let/var <identifier> = { ... } where name contains 'ayanamsha'.
# Match any identifier and filter by name in code (handles AYANAMSHA_ALIAS which
# starts with the keyword itself, no prefix required).
_RE_AYANAMSHA_CONST = re.compile(
    r"(?:const|let|var)\s+(?P<varname>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*(?::\s*Record\s*<[^>]*>|:\s*\{[^}]*\})?\s*=\s*\{",
    re.MULTILINE,
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


def _find_obj_end(text: str, open_brace: int) -> int:
    depth = 0
    i = open_brace
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def scan_ts_file(text: str) -> List[tuple]:
    hits = []
    for m in _RE_AYANAMSHA_CONST.finditer(text):
        varname = m.group("varname")
        if "ayanamsha" not in varname.lower():
            continue
        try:
            brace_start = text.index("{", m.end() - 1)
        except ValueError:
            continue
        brace_end = _find_obj_end(text, brace_start)
        body = text[brace_start:brace_end]
        if not KNOWN_AYANAMSHA_VALUES.search(body):
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(body.split())[:160]
        hits.append((line, "local_ayanamsha_alias", snippet))
    return hits


def scan_repo(root: Path, ts_globs: Sequence[str]) -> List[Violation]:
    violations = []
    for path in expand_globs(root, ts_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Skip if file imports resolveChartFactsAyanamsha (it's the fix, not the problem)
        # but still flag if it ALSO defines a local alias map
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_ts_file(text):
            violations.append(Violation(
                file=rel, line=line, kind=kind, snippet=snippet,
                message=(
                    f"File-local ayanamsha alias map '{varname if (varname := kind) else kind}' detected "
                    "in a TS file. Use resolveChartFactsAyanamsha() from the shared helper instead "
                    "(A-15; no-local-ayanamsha-map guard D-01c)."
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
        print("check_no_local_ayanamsha_map: SELF-TEST — fixture dirs missing", file=sys.stderr)
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
        print("check_no_local_ayanamsha_map: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    pass_count = sum(1 for f in pass_dir.iterdir() if f.is_file() and f.suffix == ".ts")
    fail_count = sum(1 for f in fail_dir.iterdir() if f.is_file() and f.suffix == ".ts")
    print(f"check_no_local_ayanamsha_map: SELF-TEST PASS ({pass_count} pass, {fail_count} fail fixtures).")
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
        print(f"check_no_local_ayanamsha_map: {len(allowed)} allowlisted (see allowlist):")
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(f"check_no_local_ayanamsha_map: STRICT — {len(violations)} violation(s). FAIL.", file=sys.stderr)
        return 1

    if new:
        print(f"check_no_local_ayanamsha_map: {len(new)} NEW violation(s). FAIL.", file=sys.stderr)
        print_violations(new, prefix="  ")
        return 1

    print(f"check_no_local_ayanamsha_map: 0 new violations ({len(allowed)} allowlisted). PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
