#!/usr/bin/env python3
"""check_no_local_dignity_table.py — D-01b: No file-local dignity classification.

EKAVĀKYATĀ guard (F-62; B-01 class). Permanent CI enforcement that no file outside
the canonical dignity oracle defines its own dignity classification logic. The broken
instances:

  - ga_structural_writer.py:4872-4884  — 4-way if/elif (exalted/debilitated/own/neutral)
  - ga_vargas_writer.py::_compute_dignity  — file-local DIGNITY_TABLE dict

The canonical oracle: brahmagyan/dignity_oracle.py (B-01 output). This lint ensures
future code does not re-introduce shadow copies.

What it flags (Python)
----------------------
  (a) DIGNITY_TABLE pattern: a module-level dict whose variable name contains
      'dignity' AND whose values contain dict literals with 'exalt'/'debil'/'own'
      keys (the ga_vargas_writer DIGNITY_TABLE shape).

  (b) Inline if/elif chain: a function that chains
      if ... == sign:  dignity = "exalted"
      elif ...         dignity = "debilitated"
      (i.e. assigns string literals 'exalted', 'debilitated', 'own', 'neutral'
      via consecutive if/elif comparisons in the same function).

Canonical oracle paths (never flagged):
  brahmagyan/dignity_oracle.py
  pipeline/orchestrator/writers/bo_pratijna_v4_engine.py  (pre-B-01 reference impl)

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
FIXTURE_DIR = SCRIPT_DIR / "no_local_dignity_table_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "no_local_dignity_table_allowlist.json"

DEFAULT_PY_GLOBS = ["platform/python-sidecar/**/*.py"]

EXCLUDE_SUBSTRINGS = (
    "no_local_dignity_table_fixtures/",
    "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    # Canonical oracle + reference impl
    "brahmagyan/dignity_oracle.py",
    "bo_pratijna_v4_engine.py",
)

# Pattern A: module-level dict assignment whose variable name contains 'dignity'
# (case-insensitive). We match any identifier then filter by name in Python code
# to handle names like DIGNITY_TABLE (starts with DIGNITY) and local_dignity_map.
_RE_DIGNITY_TABLE_VAR = re.compile(
    r"^[ \t]*(?P<varname>[A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*[^=\n]+)?\s*=\s*\{",
    re.MULTILINE,
)
# The dict body must contain 'exalt' and 'debil' keys to be a real dignity table
_RE_DIGNITY_KEYS = re.compile(r"['\"]exalt['\"]|['\"]debil['\"]")

# Pattern B: inline if/elif chain assigning 'exalted', 'debilitated', 'own', 'neutral'
# Detect the telltale pair: dignity = "exalted" ... elif ... dignity = "debilitated"
_RE_DIGNITY_ASSIGNMENT = re.compile(
    r'dignity\s*=\s*["\'](?:exalted|debilitated|own|neutral|moolatrikona)["\']',
    re.IGNORECASE,
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


def _find_dict_end(text: str, open_brace: int) -> int:
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


def scan_python_file(text: str) -> List[tuple]:
    hits = []

    # Pattern A: DIGNITY_TABLE dict
    for m in _RE_DIGNITY_TABLE_VAR.finditer(text):
        varname = m.group("varname")
        if "dignity" not in varname.lower():
            continue
        # Grab the dict body
        try:
            brace_start = text.index("{", m.end() - 1)
        except ValueError:
            continue
        brace_end = _find_dict_end(text, brace_start)
        body = text[brace_start:brace_end]
        if not _RE_DIGNITY_KEYS.search(body):
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(body.split())[:160]
        hits.append((line, "dignity_table_dict", snippet))

    # Pattern B: function with multiple dignity string assignments (if/elif chain)
    # Find all occurrences of dignity = "exalted/debilitated/..." in the file
    assignments = list(_RE_DIGNITY_ASSIGNMENT.finditer(text))
    if len(assignments) >= 2:
        # Group by function: find function defs and check which contain >=2 assignments
        fn_re = re.compile(r"^\s*def\s+(\w+)\s*\(", re.MULTILINE)
        fn_starts = [(m.start(), m.group(1)) for m in fn_re.finditer(text)]
        for i, (fn_start, fn_name) in enumerate(fn_starts):
            fn_end = fn_starts[i + 1][0] if i + 1 < len(fn_starts) else len(text)
            fn_body = text[fn_start:fn_end]
            fn_assignments = _RE_DIGNITY_ASSIGNMENT.findall(fn_body)
            if len(fn_assignments) >= 2:
                line = text.count("\n", 0, fn_start) + 1
                snippet = f"def {fn_name}(...) contains {len(fn_assignments)} dignity assignments"
                hits.append((line, "inline_dignity_chain", snippet))

    return hits


def scan_repo(root: Path, py_globs: Sequence[str]) -> List[Violation]:
    violations = []
    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_python_file(text):
            violations.append(Violation(
                file=rel, line=line, kind=kind, snippet=snippet,
                message=(
                    f"File-local dignity classification '{kind}' detected. "
                    "Import classify_dignity() from brahmagyan.dignity_oracle instead "
                    "(B-01 oracle; no-local-dignity-table guard D-01b)."
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
        print("check_no_local_dignity_table: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2
    failures = []
    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".py":
            continue
        hits = scan_python_file(fixture.read_text(encoding="utf-8"))
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged: {hits}")
    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".py":
            continue
        hits = scan_python_file(fixture.read_text(encoding="utf-8"))
        if not hits:
            failures.append(f"FAIL-fixture '{fixture.name}' produced no violation")
    if failures:
        print("check_no_local_dignity_table: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    pass_count = sum(1 for f in pass_dir.iterdir() if f.is_file() and f.suffix == ".py")
    fail_count = sum(1 for f in fail_dir.iterdir() if f.is_file() and f.suffix == ".py")
    print(f"check_no_local_dignity_table: SELF-TEST PASS ({pass_count} pass, {fail_count} fail fixtures).")
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
    violations = scan_repo(root, DEFAULT_PY_GLOBS)
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
        print(f"check_no_local_dignity_table: {len(allowed)} allowlisted (see allowlist):")
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(f"check_no_local_dignity_table: STRICT — {len(violations)} violation(s). FAIL.", file=sys.stderr)
        return 1

    if new:
        print(f"check_no_local_dignity_table: {len(new)} NEW violation(s). FAIL.", file=sys.stderr)
        print_violations(new, prefix="  ")
        return 1

    print(f"check_no_local_dignity_table: 0 new violations ({len(allowed)} allowlisted). PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
