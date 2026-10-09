#!/usr/bin/env python3
"""check_no_new_ayanamsha_literal_lists.py -- ONE_AYANAMSHA Phase 1 (SS N-309/N-311).

Production Python must take "which ayanamshas does this chart build" from
`brahmagyan.ayanamsha_scope.ayanamshas_for_chart`, not from its own literal list of the five ids.
This guard finds every list / tuple / set / dict literal that holds at least THREE of the five canonical
ayanamsha ids as string constants (dict: as keys) in production Python under platform/python-sidecar and compares the set
of files with a shrinking ALLOWLIST (no_new_ayanamsha_literal_lists_allowlist.json):

* a file with such a literal that is NOT in the allowlist  -> violation (a NEW local list);
* an allowlisted file that no longer has one              -> violation (remove it from the allowlist: the
  list only ever shrinks, and reaches empty when the rollout is finished).

Excluded: tests, __tests__, fixtures, the helper itself. `--write-allowlist` rewrites the allowlist from the tree
(used once, then edited down by each rollout batch). Exit codes: 0 clean, 1 violations, 2 invocation error.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
ALLOWLIST_PATH = SCRIPT_DIR / "no_new_ayanamsha_literal_lists_allowlist.json"

FIVE = frozenset({"lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"})
MIN_HITS = 3
EXCLUDE_PARTS = ("tests", "__tests__", "fixtures", "node_modules", "__pycache__", ".venv")
HELPER = "brahmagyan/ayanamsha_scope.py"


def _is_excluded(rel: str) -> bool:
    parts = rel.split("/")
    return rel == HELPER or any(p in EXCLUDE_PARTS for p in parts) or parts[-1].startswith("test_")


def _literal_hits(node: ast.AST) -> int:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        elts = node.elts
    elif isinstance(node, ast.Dict):
        elts = [k for k in node.keys if k is not None]
    else:
        return 0
    return len({e.value for e in elts if isinstance(e, ast.Constant) and isinstance(e.value, str)} & FIVE)


def literal_lines(source: str) -> list[int]:
    """Line numbers of literals holding >= MIN_HITS of the five ids."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    return sorted(n.lineno for n in ast.walk(tree) if _literal_hits(n) >= MIN_HITS)


def scan(root: Path = SIDECAR) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if _is_excluded(rel):
            continue
        lines = literal_lines(p.read_text(encoding="utf-8", errors="replace"))
        if lines:
            out[rel] = lines
    return out


def load_allowlist(path: Path = ALLOWLIST_PATH) -> list[str]:
    return list(json.loads(path.read_text(encoding="utf-8")).get("files", []))


def check(found: dict[str, list[int]], allow: list[str]) -> list[str]:
    problems = []
    for f in sorted(set(found) - set(allow)):
        problems.append(f"NEW local ayanamsha list in {f} (line {found[f][0]}): use "
                        f"brahmagyan.ayanamsha_scope.ayanamshas_for_chart")
    for f in sorted(set(allow) - set(found)):
        problems.append(f"{f} is allowlisted but no longer has a literal list: remove it from the allowlist")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write-allowlist", action="store_true")
    ap.add_argument("--root", default=str(SIDECAR))
    ap.add_argument("--allowlist", default=str(ALLOWLIST_PATH))
    a = ap.parse_args(argv)
    root, allow_path = Path(a.root), Path(a.allowlist)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    found = scan(root)
    if a.write_allowlist:
        allow_path.write_text(json.dumps(
            {"comment": "ONE_AYANAMSHA Phase 1: files that still carry their own literal list of the five "
                        "ayanamsha ids. Each rollout batch removes the files it migrates; empty = done.",
             "files": sorted(found)}, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {len(found)} file(s) to {allow_path}")
        return 0
    problems = check(found, load_allowlist(allow_path))
    for p in problems:
        print(p)
    print(f"check_no_new_ayanamsha_literal_lists: {len(problems)} problem(s), {len(found)} file(s) with a literal list")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
