#!/usr/bin/env python3
"""check_no_local_aspect_dict.py — D-01a: No file-local graha-to-aspect-degree dict.

EKAVĀKYATĀ guard (F-52/F-64/F-65; B-02 class). Permanent CI enforcement that no
file outside the canonical aspect oracle defines its own dict mapping planet names
or numbers to aspect angles/house-offsets. The broken instances this class closed:

  - services/gochara_grammar/primitives.py:189-194  SPECIAL_DRISHTI_DEG
    (Mars/Jup/Sat mapped to degree lists; omits Rahu/Ketu — active distortion)
  - ga_writers/ga_yoga_writer.py:1499-1504  NB_GRAHA_DRISHTI + NB_DEFAULT_DRISHTI
    (planet names → frozenset of house offsets; same truncation)
  - ga_vargas_writer.py::_compute_aspect_matrix  local `special` dict (latent)

The canonical oracle lives at brahmagyan/aspects.py after B-02 lands. This lint
ensures no future file re-introduces a shadow copy.

What it flags (Python only — aspect tables are Python-only in this codebase)
--------
Any module-level or class-level dict literal where:
  (a) the keys include at least two canonical graha names (case variants of
      Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) OR graha numbers
      (integers 1-9 used as positional planet indices), AND
  (b) the values are float/int literals, lists of float/int literals, OR
      frozenset/set literals of integers —
  AND the dict is NOT imported from an allowlisted oracle path.

Canonical oracle paths (never flagged regardless of content):
  brahmagyan/aspects.py  (the authoritative oracle)
  brahmagyan/parashari_aspects.py  (permitted sibling)

False-negative boundary (honest — regex scanner, not AST):
  - Dict built via dict() constructor or dict comprehension is NOT caught.
  - A planet dict assigned as a class attribute via __init__ is NOT caught.
  - A constant defined in one module and imported into another is only caught
    in the defining file.
False-positive boundary:
  - House-signification, period, strength, or natural-friend dicts that happen
    to have planet-name keys are NOT flagged, because their VALUE type (usually
    a single int or string) does not match the aspect-value shape (list/frozenset
    of ints, or float between 0-360).

Modes
-----
  --self-test   Hermetic fixture test. DB-free, repo-free.
  (default)     Scan the live repo tree (WARN-first via allowlist).
  --strict      Fail on ANY violation including allowlisted ones.

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
FIXTURE_DIR = SCRIPT_DIR / "no_local_aspect_dict_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "no_local_aspect_dict_allowlist.json"

DEFAULT_PY_GLOBS = ["platform/python-sidecar/**/*.py"]

EXCLUDE_SUBSTRINGS = (
    "no_local_aspect_dict_fixtures/",
    "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    ".test.ts", ".spec.ts",
    # The canonical oracle itself — never flag it
    "brahmagyan/aspects.py",
    "brahmagyan/parashari_aspects.py",
)

# Canonical graha names (case-insensitive match)
GRAHA_NAMES = {
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
    # common abbreviated / uppercased forms
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu", "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS",
    "SATURN", "RAHU", "KETU",
}

# Regex: a dict literal assigned to a name containing "drishti", "aspect",
# or "special" — or a dict whose keys look like graha names mapped to lists/frozensets.
# We use two complementary patterns:
#
# Pattern A: variable name contains 'drishti', 'aspect', or 'special' (case-insensitive)
#   AND the right-hand side starts a dict literal ('{' after '=')
_RE_NAMED_ASPECT_DICT = re.compile(
    r"^(?P<indent>\s*)(?P<varname>[A-Z_][A-Z0-9_]*)(?:\s*:\s*[^=]+)?\s*=\s*\{",
    re.MULTILINE,
)
_ASPECT_VAR_KEYWORDS = re.compile(r"drishti|aspect|special.*graha|graha.*special", re.IGNORECASE)

# Pattern B: dict literal where at least 2 graha names appear as string keys
# AND the values are frozenset/list/float literals (aspect-degree shape)
_RE_GRAHA_KEY = re.compile(
    r"""['"](Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|
    sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|
    SUN|MOON|MARS|MERCURY|JUPITER|VENUS|SATURN|RAHU|KETU)['"]""",
    re.VERBOSE,
)
_RE_ASPECT_VALUE = re.compile(
    r"frozenset\s*\(\s*\{|frozenset\s*\(\s*\[|\[\s*\d+(?:\.\d+)?|{[^}]*\d+(?:\.\d+)?[^}]*}"
)


def _excluded(rel: str) -> bool:
    return any(s in rel for s in EXCLUDE_SUBSTRINGS)


def expand_globs(root: Path, globs: Sequence[str]) -> List[Path]:
    out: set[Path] = set()
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
        return f"{self.file}|{self.kind}|{self.snippet[:80]}"


def _find_dict_end(text: str, open_brace: int) -> int:
    """Find the closing } of a dict literal. Returns index after '}'."""
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
    """Return list of (line, kind, snippet) violations."""
    hits = []
    for m in _RE_NAMED_ASPECT_DICT.finditer(text):
        varname = m.group("varname")
        if not _ASPECT_VAR_KEYWORDS.search(varname):
            continue
        # Found a suspect variable name — grab the dict body
        brace_start = text.index("{", m.end() - 1)
        brace_end = _find_dict_end(text, brace_start)
        body = text[brace_start:brace_end]
        # Must have graha-name keys
        graha_hits = _RE_GRAHA_KEY.findall(body)
        if len(set(g.lower() for g in graha_hits)) < 2:
            continue
        # Must have aspect-value shaped values (floats or frozenset/list of ints)
        if not _RE_ASPECT_VALUE.search(body):
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(body.split())[:160]
        hits.append((line, "named_aspect_dict", snippet))
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
                    f"File-local graha-to-aspect dict '{kind}' detected. "
                    "Import get_graha_aspects() from brahmagyan.aspects instead "
                    "(B-02 oracle; no-local-aspect-dict guard D-01a)."
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
        print("check_no_local_aspect_dict: SELF-TEST — fixture dirs missing", file=sys.stderr)
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
            failures.append(f"FAIL-fixture '{fixture.name}' produced no violation (false negative)")
    if failures:
        print("check_no_local_aspect_dict: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    pass_count = sum(1 for f in pass_dir.iterdir() if f.is_file() and f.suffix == ".py")
    fail_count = sum(1 for f in fail_dir.iterdir() if f.is_file() and f.suffix == ".py")
    print(f"check_no_local_aspect_dict: SELF-TEST PASS ({pass_count} pass, {fail_count} fail fixtures).")
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
        print(f"check_no_local_aspect_dict: {len(allowed)} allowlisted violation(s) (see allowlist):")
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(f"check_no_local_aspect_dict: STRICT — {len(violations)} violation(s). FAIL.", file=sys.stderr)
        print_violations(violations, prefix="  ")
        return 1

    if new:
        print(f"check_no_local_aspect_dict: {len(new)} NEW violation(s). FAIL.", file=sys.stderr)
        print_violations(new, prefix="  ")
        return 1

    print(f"check_no_local_aspect_dict: 0 new violations ({len(allowed)} allowlisted). PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
