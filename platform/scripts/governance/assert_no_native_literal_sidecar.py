#!/usr/bin/env python3
"""assert_no_native_literal_sidecar.py -- native-data ratchet for python-sidecar route/service code.

SS N-384 (PR-S6). Sibling of assert_no_native_literal.sh (which guards platform/src/lib/retrieval);
this one guards ``platform/python-sidecar/{routers,services,brahmagyan}/**/*.py``: the code that
SERVES requests. A route or service must never carry one person's identity, birth details or chart
id as a value it can hand out or fall back on.

WHAT IT FLAGS  (AST, not text: only string/number constants that are CODE; docstrings, comments and
bare string statements are documentation and are not counted)

  NAME          a string constant containing a name token of the native (case-insensitive)
  BIRTHDATE     a string constant containing the native's birth date, or a date(...)-style call whose
                first three arguments are that date as integers
  BIRTHTIME     a string constant containing the native's birth clock time
  COORD         the native's birth latitude/longitude (either 4-decimal pair used in the code base)
                as a number, or inside a string. The 2-decimal city coordinates used as a PLACE
                default for panchang/muhurta are not birth data and are not flagged.
  CHART_DEFAULT the canonical chart UUID used as a DEFAULT: a function/lambda parameter default, a
                class-body field value (pydantic / dataclass), the argument of Field/Query/Body/Path
                (or ``default=``), the fallback argument of os.environ.get / os.getenv, or the value
                of a module-level ``*CHART_ID*`` constant. The same UUID as an explicit request value
                or an expected value in a test is NOT flagged (tests are out of scope anyway).

SCOPE  routers/, services/, brahmagyan/ under platform/python-sidecar, except tests (tests/,
       __tests__/, test_*.py, *_test.py, conftest.py), fixtures/, migrations/, __pycache__. ga_writers,
       pipeline/orchestrator/writers and migrations live outside these roots or are excluded: they are
       governed by their own rules.

ALLOWLIST  native_literal_sidecar_allowlist.json: an explicit entry per file with ``max_hits`` and a
           ``reason``. It is a RATCHET: a file with more hits than ``max_hits``, a file with hits and
           no entry, and a STALE entry (file gone, no hits left, or ``max_hits`` above the real count)
           all fail. Paying a file down means lowering its number; deleting the last hit means deleting
           its entry.

Exit codes: 0 clean, 1 violation(s), 2 invocation error.

  python3 platform/scripts/governance/assert_no_native_literal_sidecar.py            # repo scan
  python3 platform/scripts/governance/assert_no_native_literal_sidecar.py --self-test
  python3 platform/scripts/governance/assert_no_native_literal_sidecar.py --list      # hits per file

Note on this file's own literals: the patterns below are assembled from fragments on purpose, so this
guard does not itself contain the strings it forbids (a plain grep for them stays meaningful).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
ALLOWLIST_PATH = SCRIPT_DIR / "native_literal_sidecar_allowlist.json"

SCAN_ROOTS = (
    "platform/python-sidecar/routers",
    "platform/python-sidecar/services",
    "platform/python-sidecar/brahmagyan",
)
EXCLUDED_DIR_NAMES = frozenset({
    "tests", "__tests__", "fixtures", "migrations", "__pycache__", "ga_writers",
})
EXCLUDED_FILE_RE = re.compile(r"(^test_.*\.py$)|(.*_test\.py$)|(^conftest\.py$)")

# ---- the forbidden values, assembled from fragments (see module docstring) --------------------------
_NAME_TOKENS = ("abhi" + "sek", "moh" + "anty")
_BIRTH_DATE = "1984" + "-02-05"
_BIRTH_YMD = (1984, 2, 5)
_BIRTH_TIME = re.compile(r"(?<![\d:])10" + ":" + r"43(?![\d])")
_COORDS = ("20." + "2735", "85." + "8334", "20." + "2961", "85." + "8245")   # the two 4-decimal birth-coordinate pairs in use
_CHART_UUID = "482012f1" + "-710e-4a25-994a-93821f5871aa"

_DEFAULTISH_CALLS = frozenset({"Field", "PydanticField", "Query", "Body", "Path", "Header", "Form", "Depends"})
_ENV_CALLS = frozenset({"get", "getenv"})
_CHART_ID_NAME = re.compile(r"CHART_ID", re.IGNORECASE)


@dataclass(frozen=True)
class Hit:
    kind: str
    line: int
    snippet: str


# ------------------------------------------------------------------------------------------------ scan


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """ids of Constant nodes that are bare string statements (docstrings and stray doc strings)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            ids.add(id(node.value))
    return ids


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def _is_uuid_const(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.strip().lower() == _CHART_UUID
    )


def _default_positions(tree: ast.AST) -> list[ast.AST]:
    """Expression nodes that sit in a 'default value' position."""
    out: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            out.extend(d for d in a.defaults if d is not None)
            out.extend(d for d in a.kw_defaults if d is not None)
        elif isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                    out.append(stmt.value)
                elif isinstance(stmt, ast.Assign):
                    out.append(stmt.value)
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in _DEFAULTISH_CALLS:
                out.extend(node.args[:1])
                out.extend(k.value for k in node.keywords if k.arg in ("default", None))
            elif name in _ENV_CALLS and len(node.args) >= 2:
                out.append(node.args[1])
                out.extend(k.value for k in node.keywords if k.arg == "default")
    # module-level *CHART_ID* constants
    if isinstance(tree, ast.Module):
        for stmt in tree.body:
            targets: list[ast.expr] = []
            if isinstance(stmt, ast.Assign):
                targets, value = list(stmt.targets), stmt.value
            elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                targets, value = [stmt.target], stmt.value
            else:
                continue
            if any(isinstance(t, ast.Name) and _CHART_ID_NAME.search(t.id) for t in targets):
                out.append(value)
    return out


def _contains_uuid(node: ast.AST) -> list[ast.Constant]:
    return [n for n in ast.walk(node) if _is_uuid_const(n)]  # type: ignore[misc]


def scan_source(text: str) -> list[Hit]:
    """All hits in one module's source. Raises SyntaxError on an unparsable file."""
    tree = ast.parse(text)
    docs = _docstring_node_ids(tree)
    hits: list[Hit] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) not in docs:
            v = node.value
            if isinstance(v, str):
                low = v.lower()
                if any(t in low for t in _NAME_TOKENS):
                    hits.append(Hit("NAME", node.lineno, _short(v)))
                if _BIRTH_DATE in v:
                    hits.append(Hit("BIRTHDATE", node.lineno, _short(v)))
                if _BIRTH_TIME.search(v):
                    hits.append(Hit("BIRTHTIME", node.lineno, _short(v)))
                if any(c in v for c in _COORDS):
                    hits.append(Hit("COORD", node.lineno, _short(v)))
            elif isinstance(v, float) and any(float(c) == v for c in _COORDS):
                hits.append(Hit("COORD", node.lineno, repr(v)))
        elif isinstance(node, ast.Call):
            ints = [a.value for a in node.args[:3] if isinstance(a, ast.Constant) and isinstance(a.value, int)]
            if len(node.args) >= 3 and tuple(ints) == _BIRTH_YMD:
                hits.append(Hit("BIRTHDATE", node.lineno, f"{_call_name(node)}(date as integers)"))

    seen: set[int] = set()
    for pos in _default_positions(tree):
        for c in _contains_uuid(pos):
            if id(c) not in seen:
                seen.add(id(c))
                hits.append(Hit("CHART_DEFAULT", c.lineno, "canonical chart id used as a default"))

    hits.sort(key=lambda h: (h.line, h.kind))
    return hits


def _short(s: str) -> str:
    s = " ".join(s.split())
    return s if len(s) <= 60 else s[:57] + "..."


def in_scope(rel: Path) -> bool:
    parts = rel.parts
    if any(p in EXCLUDED_DIR_NAMES for p in parts[:-1]):
        return False
    return not EXCLUDED_FILE_RE.match(rel.name) and rel.suffix == ".py"


def scan_repo(repo_root: Path, roots: Sequence[str] = SCAN_ROOTS) -> tuple[dict[str, list[Hit]], list[str]]:
    """({repo-relative path: hits (only files with hits)}, [unparsable files])."""
    result: dict[str, list[Hit]] = {}
    unparsable: list[str] = []
    for root in roots:
        base = repo_root / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if not in_scope(path.relative_to(base)):
                continue
            rel = path.relative_to(repo_root).as_posix()
            try:
                hits = scan_source(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, ValueError):
                unparsable.append(rel)
                continue
            if hits:
                result[rel] = hits
    return result, unparsable


# ------------------------------------------------------------------------------------------ allowlist


def load_allowlist(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    out: dict[str, dict] = {}
    for e in entries:
        f = e.get("file")
        if not f or not isinstance(e.get("max_hits"), int) or not str(e.get("reason", "")).strip():
            raise ValueError(f"allowlist entry needs file, integer max_hits and a non-empty reason: {e!r}")
        if f in out:
            raise ValueError(f"duplicate allowlist entry for {f}")
        out[f] = e
    return out


def evaluate(
    hits_by_file: dict[str, list[Hit]],
    allowlist: dict[str, dict],
    existing_files: Iterable[str],
    unparsable: Sequence[str] = (),
) -> list[str]:
    """Problems (empty = pass). `existing_files` = every in-scope file that exists (stale check)."""
    existing = set(existing_files)
    problems: list[str] = []
    for f in unparsable:
        problems.append(f"{f}: could not be parsed, so it could not be checked (fix the file or the scanner)")
    for f, hits in sorted(hits_by_file.items()):
        entry = allowlist.get(f)
        kinds = sorted({h.kind for h in hits})
        if entry is None:
            first = hits[0]
            problems.append(
                f"{f}: {len(hits)} native-data hit(s) [{', '.join(kinds)}], not allowlisted "
                f"(first: line {first.line} {first.kind} {first.snippet!r}). Remove the literal "
                f"(read the requested chart's data instead); see platform/scripts/governance/"
                f"assert_no_native_literal_sidecar.py"
            )
        elif len(hits) > entry["max_hits"]:
            problems.append(
                f"{f}: {len(hits)} hit(s) > allowed {entry['max_hits']} (new native-data literal added; "
                f"the allowlist is a ratchet, it can only shrink)"
            )
    for f, entry in sorted(allowlist.items()):
        if f not in existing:
            problems.append(f"{f}: STALE allowlist entry, the file no longer exists/in scope; delete the entry")
        elif f not in hits_by_file:
            problems.append(f"{f}: STALE allowlist entry, no native-data hit left; delete the entry")
        elif len(hits_by_file[f]) < entry["max_hits"]:
            problems.append(
                f"{f}: STALE allowlist count, {len(hits_by_file[f])} hit(s) left but max_hits is "
                f"{entry['max_hits']}; lower it to {len(hits_by_file[f])}"
            )
    return problems


def in_scope_files(repo_root: Path, roots: Sequence[str] = SCAN_ROOTS) -> list[str]:
    out = []
    for root in roots:
        base = repo_root / root
        if base.is_dir():
            out.extend(
                p.relative_to(repo_root).as_posix()
                for p in sorted(base.rglob("*.py")) if in_scope(p.relative_to(base))
            )
    return out


def run(repo_root: Path, allowlist_path: Path, roots: Sequence[str] = SCAN_ROOTS) -> tuple[list[str], dict[str, list[Hit]]]:
    hits, unparsable = scan_repo(repo_root, roots)
    allow = load_allowlist(allowlist_path)
    return evaluate(hits, allow, in_scope_files(repo_root, roots), unparsable), hits


# ----------------------------------------------------------------------------------------- self-test

_OFFENDER = '''
import os
from datetime import date
from fastapi import Query
from pydantic import BaseModel, Field

"""stray doc string naming {name} is documentation, not a hit"""

PROFILE = {{"name": "{name} {surname}"}}                       # NAME
BORN = "{bdate}"                                                # BIRTHDATE
BORN_CALL = date(1984, 2, 5)                                    # BIRTHDATE (integers)
CLOCK = "born at {btime} IST"                                   # BIRTHTIME
LAT = {lat}                                                     # COORD (number)
LON_TXT = "lon={lon}"                                           # COORD (in a string)
NATIVE_CHART_ID = "{cid}"                                       # CHART_DEFAULT (module constant)
ENV_ID = os.environ.get("X", "{cid}")                           # CHART_DEFAULT (env fallback)


def route(chart_id: str = "{cid}"):                             # CHART_DEFAULT (param default)
    return chart_id


def route2(chart_id: str = Query("{cid}")):                     # CHART_DEFAULT (Query default)
    return chart_id


class Req(BaseModel):
    chart_id: str = Field(default="{cid}")                      # CHART_DEFAULT (Field default)
    other: str = "{cid}"                                        # CHART_DEFAULT (class-body value)
'''.format(
    name=_NAME_TOKENS[0].title(), surname=_NAME_TOKENS[1].title(), bdate=_BIRTH_DATE, btime="10" + ":" + "43",
    lat=_COORDS[0], lon=_COORDS[1], cid=_CHART_UUID,
)
_OFFENDER_EXPECTED = {"NAME": 1, "BIRTHDATE": 2, "BIRTHTIME": 1, "COORD": 2, "CHART_DEFAULT": 6}

_CLEAN = '''
"""Module doc: the {name} chart was born {bdate}; this is documentation, not data."""
import os
from fastapi import Query
from pydantic import BaseModel, Field

# a comment naming {name} and {cid} is not code
DEFAULT_LOCATION = (20.27, 85.84)                # a place default, not the birth coordinate pair
SOME_TIME = "10:44"
RECORD = {{"chart_id": "{cid}"}}                  # an explicit value, not a default
SUPPLIED = {{"x": [("{cid}", 1)]}}


def route(chart_id: str, other: str = "generic"):
    """Doc string that mentions {cid}."""
    return call_with(chart_id="{cid}")           # an explicit argument


def call_with(**kw):
    return kw


def route2(chart_id: str = Query(...)):
    return chart_id


class Req(BaseModel):
    chart_id: str = Field(...)
    note: str = "x"
'''.format(name=_NAME_TOKENS[0].title(), bdate=_BIRTH_DATE, cid=_CHART_UUID)


def self_test() -> list[str]:
    """Prove the detector can read false AND true; returns failures (empty = the guard works)."""
    fails: list[str] = []

    # 1. the offender produces exactly the expected hits per kind
    got: dict[str, int] = {}
    for h in scan_source(_OFFENDER):
        got[h.kind] = got.get(h.kind, 0) + 1
    if got != _OFFENDER_EXPECTED:
        fails.append(f"offender fixture: expected {_OFFENDER_EXPECTED}, got {got}")

    # 2. the clean file produces none
    clean = scan_source(_CLEAN)
    if clean:
        fails.append(f"clean fixture produced hits: {[(h.kind, h.line) for h in clean]}")

    # 3. allowlist evaluation: not allowlisted / exact / too many / stale (gone, no hits, count too high)
    off = scan_source(_OFFENDER)
    n = len(off)
    files = ["a.py", "b.py"]
    cases: list[tuple[str, dict, dict, list[str], bool]] = [
        ("offender, no entry fails", {"a.py": off}, {}, files, True),
        ("exact entry passes", {"a.py": off}, {"a.py": {"max_hits": n, "reason": "r"}}, files, False),
        ("extra hit above entry fails", {"a.py": off}, {"a.py": {"max_hits": n - 1, "reason": "r"}}, files, True),
        ("stale entry (no hits) fails", {}, {"a.py": {"max_hits": 1, "reason": "r"}}, files, True),
        ("stale entry (file gone) fails", {}, {"gone.py": {"max_hits": 1, "reason": "r"}}, files, True),
        ("stale count (too high) fails", {"a.py": off}, {"a.py": {"max_hits": n + 3, "reason": "r"}}, files, True),
        ("clean repo passes", {}, {}, files, False),
    ]
    for label, hb, allow, ex, should_fail in cases:
        failed = bool(evaluate(hb, allow, ex))
        if failed != should_fail:
            fails.append(f"allowlist logic: {label}: expected {'fail' if should_fail else 'pass'}")

    # 4. scope: tests / fixtures / writers / kala-free paths excluded, ordinary modules included
    for rel, want in (
        ("routers/x.py", True), ("brahmagyan/phala/y.py", True), ("services/s/t.py", True),
        ("services/s/tests/test_a.py", False), ("brahmagyan/__tests__/a.py", False),
        ("routers/test_x.py", False), ("routers/x_test.py", False), ("routers/conftest.py", False),
        ("services/s/fixtures/f.py", False), ("brahmagyan/migrations/m.py", False),
    ):
        if in_scope(Path(rel)) != want:
            fails.append(f"scope: {rel} should be {'in' if want else 'out of'} scope")
    return fails


# ------------------------------------------------------------------------------------------------ main


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true", help="prove the detector on bundled fixtures")
    ap.add_argument("--list", action="store_true", help="print the hit count per file and exit 0")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    ap.add_argument("--allowlist", type=Path, default=ALLOWLIST_PATH)
    args = ap.parse_args(argv)

    if args.self_test:
        fails = self_test()
        if fails:
            print("assert_no_native_literal_sidecar --self-test FAILED:", file=sys.stderr)
            for f in fails:
                print(f"  - {f}", file=sys.stderr)
            return 1
        print("assert_no_native_literal_sidecar --self-test: PASS (offender flagged, clean file clean, "
              "allowlist ratchet + stale checks, scope)")
        return 0

    if not args.repo_root.is_dir():
        print(f"repo root not found: {args.repo_root}", file=sys.stderr)
        return 2
    try:
        problems, hits = run(args.repo_root, args.allowlist)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"assert_no_native_literal_sidecar: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for f, hs in sorted(hits.items()):
            print(f"{len(hs):4d}  {f}  [{', '.join(sorted({h.kind for h in hs}))}]")
        return 0

    total = sum(len(h) for h in hits.values())
    if problems:
        print("NATIVE-LITERAL (sidecar) GATE FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"assert_no_native_literal_sidecar: PASS ({total} allowlisted hit(s) in {len(hits)} file(s); "
          f"no new native-data literal in routers/services/brahmagyan)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
