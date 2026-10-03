"""ci_changes.py: classify a pull request as DOCS-ONLY or not, so ci.yml can skip its heavy jobs for a change that cannot affect them.

  python3 ci_changes.py --event pull_request --base HEAD^1 --head HEAD     prints `docs_only=true|false` (always exit 0)
  python3 ci_changes.py --files a.md b/c.py                                 classify a given file list (tests)
  python3 ci_changes.py --list-pinned                                       print the pinned set computed from this checkout

FAIL-CLOSED: `docs_only=true` is printed ONLY for a pull_request event with a non-empty changed-file list in which EVERY file (old and new
name of a rename, deleted files included: `--no-renames`) is a documentation file. An error, an empty list, an unreadable diff, a push /
merge_group / workflow_dispatch event all print `docs_only=false`, so every job runs (post-merge runs on main and the merge queue always
run everything).

A DOCS file is a `*.md` / `*.txt` (extension compared case-insensitively) that lives under `00_ARCHITECTURE/` or `99_ARCHIVE/` and is NOT:
under `.github/`, `00_ARCHITECTURE/control/`, `00_ARCHITECTURE/autonomy/`, a tests / fixtures / migrations / node_modules directory (any case);
a file some TEST READS (the pinned set: every md/txt a test file names, COMPUTED AT CLASSIFY TIME by `scan_pinned()` over the checked-out tree, so
there is no committed list to go stale or to conflict on, and a test the change itself adds is already counted). A scan that errors, cannot read
a tracked test file, or finds nothing at all is not credible: the set becomes the wildcard and nothing is docs-only. Everything else never
skips: code, data, config and workflow files; markdown beside code (platform/, services/); the canonical corpora (025_HOLISTIC_SYNTHESIS/,
01_FACTS_LAYER/, ...) that the unit tests parse; root files. Names are compared exactly as git reports them (`-z`): no stripping.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC_EXT = (".md", ".txt")
DOC_ROOTS = ("00_ARCHITECTURE/", "99_ARCHIVE/")
DENY_PREFIX = (".github/", "00_ARCHITECTURE/control/", "00_ARCHITECTURE/autonomy/")
DENY_DIRS = ("__tests__", "tests", "test", "fixtures", "migrations", "node_modules")
TEST_FILE = re.compile(r"(^|/)(__tests__|tests?|fixtures)/|(^|/)test_[^/]*\.py$|_test\.py$|\.(test|spec)\.(ts|tsx|js|jsx|mjs)$")
DOC_TOKEN = re.compile(r"[A-Za-z0-9_./\-]+\.(?:md|txt)\b", re.I)


def _pinned() -> frozenset[str]:
    """The pinned set for THIS checkout, computed now. Fail closed: any error, or an empty result (a real tree always has tests that name documents,
    so an empty scan means the scan did not see the tests), is the wildcard: nothing is provably unpinned."""
    try:
        pins = frozenset(scan_pinned(strict=True))
    except Exception:                                    # noqa: BLE001 - fail closed on anything unexpected
        return frozenset({"*"})
    return pins if pins else frozenset({"*"})


def is_doc(path: str, pinned: frozenset[str] | None = None) -> bool:
    raw = path
    if not raw or raw != raw.strip() or "\\" in raw or raw.startswith("/") or any(seg in ("", ".", "..") for seg in raw.split("/")):
        return False                                     # git never reports these: anything odd is not a docs file
    low = raw.lower()
    if not low.endswith(DOC_EXT) or not raw.startswith(DOC_ROOTS):
        return False
    if any(raw.startswith(d) for d in DENY_PREFIX) or any(seg.lower() in DENY_DIRS for seg in raw.split("/")[:-1]):
        return False
    pins = _pinned() if pinned is None else pinned
    return "*" not in pins and raw not in pins


def docs_only(files: list[str], pinned: frozenset[str] | None = None) -> bool:
    pins = _pinned() if pinned is None else pinned
    return bool(files) and all(is_doc(f, pins) for f in files)


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(HERE.parents[2]), "ls-files", "-z"], capture_output=True, check=True, timeout=120).stdout
    return [f for f in out.decode("utf-8", "surrogateescape").split("\0") if f]


def scan_pinned(root: Path | None = None, files: list[str] | None = None, strict: bool = False) -> list[str]:
    """Every md/txt DOCS-eligible file that a test file names: by a path-suffix match when the token has a directory part, by basename otherwise.
    `strict`: a tracked test file that cannot be read raises (an unread test could hide a pinned document) instead of being skipped."""
    root = root or HERE.parents[2]
    files = tracked_files() if files is None else files
    eligible = [f for f in files if f.lower().endswith(DOC_EXT) and f.startswith(DOC_ROOTS)]
    by_base: dict[str, list[str]] = {}
    for f in eligible:
        by_base.setdefault(posixpath.basename(f).lower(), []).append(f)
    tokens: set[str] = set()
    for f in files:
        if not TEST_FILE.search(f) or not f.lower().endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".json", ".yml", ".yaml")):
            continue
        try:
            text = (root / f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            if strict:
                raise
            continue
        tokens.update(t.strip("./") if t.startswith("./") else t for t in DOC_TOKEN.findall(text))
    pinned: set[str] = set()
    for t in tokens:
        tl = t.lower()
        if "/" in t:
            pinned.update(f for f in eligible if f.lower() == tl or f.lower().endswith("/" + tl))
        else:
            pinned.update(by_base.get(tl, ()))
    return sorted(pinned)


def changed_files(base: str, head: str) -> list[str] | None:
    try:
        out = subprocess.run(["git", "diff", "--name-only", "--no-renames", "-z", base, head], capture_output=True, timeout=120, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return [f for f in out.decode("utf-8", "surrogateescape").split("\0") if f]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--event", default="pull_request")
    ap.add_argument("--base", default="HEAD^1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--list-pinned", action="store_true")
    a = ap.parse_args(argv)
    if a.list_pinned:
        pins = _pinned()
        print("\n".join(sorted(pins)))
        return 0 if "*" not in pins else 1
    try:
        if a.files is not None:
            res = docs_only(a.files)
        elif a.event != "pull_request":
            res = False
        else:
            files = changed_files(a.base, a.head)
            res = files is not None and docs_only(files)
    except Exception:                                    # noqa: BLE001 - fail closed: anything unexpected means "run everything"
        res = False
    print(f"docs_only={'true' if res else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
