#!/usr/bin/env python3
"""check_node_series_pin.py: the reader-pin lint for the `ephemeris_daily` node series, with a RATCHET.

WHY (SS N-68/N-69; DESIGN_L0_MEAN_NODE_SERIES_v1_0.md section 7; CLAUDE.md section N.7 item 2, same discipline as
`check_fact_category_pinning.py`). `ephemeris_daily` stores the TRUE node for Rahu/Ketu today (node_mode = 'true'; the seven
other bodies carry node_mode NULL). L0 is about to gain a second, MEAN, row set beside it. Every reader that can return
Rahu/Ketu rows and does not say WHICH series it means would, the day the second set exists, silently read both (a duplicate
date per node body, last-row-wins, UNIONed retrograde days, ...). This lint makes "which series" a property that is checked,
not remembered.

WHAT IT FLAGS. Every SQL READ of `ephemeris_daily` (a SELECT statement with `FROM|JOIN [public.]ephemeris_daily`) in
  * python  : platform/python-sidecar/**/*.py, platform/scripts/**/*.py
  * ts/tsx  : platform/src/**, platform-mcp/src/**, platform/scripts/**
  * sql     : platform/scripts/**/*.sql, platform/migrations/**/*.sql, platform/supabase/migrations/**/*.sql (a NEW view/function/
              integrity check over the table is a reader too; already-applied files are in the baseline, never edited)
that can return Rahu/Ketu rows and carries NONE of:
  (a) the node-series pin: `NODE_SERIES_PREDICATE` (services/w2g/node_series.py) in the statement, or an explicit `node_mode`
      predicate (`node_mode = ...`, `IN`, `IS [NOT] NULL`, `COALESCE(node_mode, ...)`, `... = node_mode`);
  (b) a documented exemption comment `node-agnostic: <reason>` (`#`, `--` or `//`) inside the statement or on the three lines
      above it; the reason must be at least 12 characters and must NOT name Rahu or Ketu (an exemption is for readers that
      provably never see them);
  (c) a statement that provably cannot return a node row: `LIMIT 0`, a literal `body = 'X'` / `body IN ('X', ...)` whose values
      are all non-node (and no non-literal body constraint beside it), or `body NOT IN ('Rahu', 'Ketu')`.
Writers (INSERT/UPDATE/DELETE FROM) are not reads and are not flagged.

RATCHET (the baseline can only shrink). `node_series_pin_baseline.json` lists today's unpinned readers as
(file, anchor, count) entries, anchor = the enclosing function/class or the assigned constant name (stable across line moves
and reformatting). Default mode FAILS on:
  R1 NEW      an unpinned reader that is not in the baseline, or more unpinned readers under one (file, anchor) than its count;
  R2 STALE    a baseline entry whose count exceeds the unpinned readers actually found: the reader was pinned (or removed), so
              the entry must shrink or go, and its key moves to `retired`;
  R3 RETIRED  an unpinned reader under a (file, anchor) in `retired`: a pinned reader may never come back;
  R4 CEILING  the baseline total differs from RATCHET_CEILING_TOTAL below. Raising it is a deliberate, reviewed code edit
              (NEVER do it to make CI pass); after a fix it must be lowered to the new total, so the ratchet can never sit
              above what the baseline holds;
  R5 SHAPE    an entry without a written `note`, a duplicate key, an entry both live and retired.
`--against <git ref>` additionally fails if the baseline has any key, or any count, that the ref's baseline does not (so a
PR cannot grow it even by editing the baseline and the ceiling together); skipped with a stated reason when the ref is absent
(a shallow CI checkout).

Honest scope (a regex/lexer scanner, not dataflow): it reads literals, merging adjacent ones and `+` concatenations; it is blind
to SQL assembled through variables across statements, ORM builders, and to callers of a shared helper (they are covered through
the helper's own SQL, e.g. ka_graha_sancara.engine._read_from_bg_ephemeris). Pinning is judged per statement, not per sub-select.

Modes: --self-test (bundled fixtures, hermetic); (default) repo scan + ratchet; --json; --emit-baseline (prints a draft for the
initial rollout or a shrink; a human reviews it); --against <ref>.
Exit codes: 0 clean; 1 violation / self-test fail; 2 invocation or config error.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
FIXTURE_DIR = SCRIPT_DIR / "node_series_pin_fixtures"
BASELINE_PATH = SCRIPT_DIR / "node_series_pin_baseline.json"
BASELINE_REL = "platform/scripts/governance/node_series_pin_baseline.json"

# NEVER raise this to make CI pass. It must equal the baseline's total; a fix lowers both.
RATCHET_CEILING_TOTAL = 29  # must equal the baseline total; see node_series_pin_baseline.json

SCAN_GLOBS: Dict[str, List[str]] = {
    "py": ["platform/python-sidecar/**/*.py", "platform/scripts/**/*.py"],
    "ts": ["platform/src/**/*.ts", "platform/src/**/*.tsx", "platform-mcp/src/**/*.ts", "platform/scripts/**/*.ts"],
    "sql": ["platform/scripts/**/*.sql", "platform/migrations/**/*.sql", "platform/supabase/migrations/**/*.sql"],
}
EXCLUDE_SUBSTRINGS = (
    "node_series_pin_fixtures/", "check_node_series_pin.py", "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    "/_archive/", "/.clone/", "/dist/", "/.venv/", ".test.ts", ".test.tsx", ".spec.ts", "/conftest.py",
)
NODE_BODIES = ("Rahu", "Ketu")

READ_RE = re.compile(r"\b(?:FROM|JOIN)\s+(?:ONLY\s+)?(?:public\.)?\"?ephemeris_daily\b", re.I)
# a file-level constant naming the table (`TABLE = "ephemeris_daily"`) used as `FROM {TABLE}` / `FROM ${TABLE}`
ALIAS_DEF_RE = re.compile(r"^[ \t]*(?:export[ \t]+)?(?:const[ \t]+|let[ \t]+)?([A-Za-z_]\w*)[ \t]*(?::[^=\n]+)?=[ \t]*[\"'`]ephemeris_daily[\"'`][ \t]*;?[ \t]*$", re.M)


def read_re_for(text: str) -> "re.Pattern[str]":
    names = sorted(set(ALIAS_DEF_RE.findall(text)))
    if not names:
        return READ_RE
    alt = "|".join(re.escape(n) for n in names)
    return re.compile(r"\b(?:FROM|JOIN)\s+(?:ONLY\s+)?(?:(?:public\.)?\"?ephemeris_daily\b|\$?\{(?:\w+\.)*(?:" + alt + r")\})", re.I)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+$", re.I)
SELECT_RE = re.compile(r"\bSELECT\b", re.I)
PIN_TOKEN_RE = re.compile(r"\bNODE_SERIES_PREDICATE\b")
PIN_PRED_RES = [
    re.compile(r"\bnode_mode\s*(?:=|<>|!=|<|>)", re.I),
    re.compile(r"\bnode_mode\s+(?:NOT\s+)?(?:IN|IS|LIKE|BETWEEN)\b", re.I),
    re.compile(r"\bCOALESCE\s*\(\s*(?:\w+\.)?node_mode\b", re.I),
    re.compile(r"(?:=|<>|!=)\s*(?:\w+\.)?node_mode\b", re.I),
    # the series are separated, not merged: GROUP BY / PARTITION BY a list that carries node_mode
    re.compile(r"\b(?:GROUP\s+BY|PARTITION\s+BY)\b[^;)]*?\bnode_mode\b", re.I),
]
MARKER_RE = re.compile(r"node-agnostic:\s*([^\n\r]*)", re.I)
LIMIT0_RE = re.compile(r"\bLIMIT\s+0\b", re.I)
BODY_EQ_RE = re.compile(r"\b(?:\w+\.)?body\s*=\s*'([^']*)'", re.I)
BODY_IN_RE = re.compile(r"\b(?:\w+\.)?body\s+IN\s*\(([^)]*)\)", re.I)
BODY_NOT_IN_RE = re.compile(r"\b(?:\w+\.)?body\s+NOT\s+IN\s*\(([^)]*)\)", re.I)
BODY_ANY_RE = re.compile(r"\b(?:\w+\.)?body\s*(?:=\s*ANY\b|=\s*%|=\s*\$|=\s*:|=\s*\?|IN\s*\(\s*(?:%|\$|:|\?))", re.I)
STR_LIT_RE = re.compile(r"'([^']*)'")


@dataclass(frozen=True)
class Site:
    file: str       # repo-relative POSIX path
    line: int       # 1-indexed line of the FROM/JOIN
    anchor: str     # enclosing function/class or assigned constant
    snippet: str    # normalized statement head
    pinned: bool
    reason: str     # why it is pinned/exempt, or why it is not

    @property
    def key(self) -> str:
        return f"{self.file}::{self.anchor}"


# ------------------------------------------------------------------------------------------- lexer
Literal = Tuple[int, int, str, str]   # start offset, end offset (exclusive), text, kind


def _lex_literals(text: str, lang: str) -> List[Literal]:
    """String literals of python (`#` comments, ''' and \"\"\") or ts (// and /* */ comments, backtick templates).
    Adjacent literals (only whitespace/comments between them, python implicit concatenation) and `+`-joined literals merge."""
    out: List[Literal] = []
    i, n = 0, len(text)

    def skip_string(j: int) -> int:
        q = text[j]
        if lang == "py" and text.startswith(q * 3, j):
            end = text.find(q * 3, j + 3)
            while end != -1 and text[end - 1] == "\\" and text[end - 2] != "\\":
                end = text.find(q * 3, end + 1)
            return n if end == -1 else end + 3
        k = j + 1
        while k < n:
            c = text[k]
            if c == "\\":
                k += 2
                continue
            if q == "`" and c == "$" and text.startswith("${", k):
                k = skip_braces(k + 2)
                continue
            if c == q:
                return k + 1
            if c == "\n" and q != "`":
                return k
            k += 1
        return n

    def skip_braces(j: int) -> int:
        depth = 1
        while j < n and depth:
            c = text[j]
            if c in "'\"`":
                j = skip_string(j)
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        return j

    while i < n:
        c = text[i]
        if lang == "py" and c == "#":
            i = text.find("\n", i)
            i = n if i == -1 else i
            continue
        if lang == "ts" and c == "/" and text.startswith("//", i):
            i = text.find("\n", i)
            i = n if i == -1 else i
            continue
        if lang == "ts" and c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c in "'\"" or (c == "`" and lang == "ts"):
            j = skip_string(i)
            out.append((i, j, text[i:j], "str"))
            i = j
            continue
        i += 1
    # merge adjacent / '+'-joined literals
    merged: List[Literal] = []
    for lit in out:
        if merged:
            ps, pe, pt, _ = merged[-1]
            gap = text[pe:lit[0]]
            gap_nc = re.sub(r"#[^\n]*" if lang == "py" else r"//[^\n]*|/\*.*?\*/", "", gap, flags=re.S)
            if (lang == "py" and re.fullmatch(r"\s*[rbfuRBFU]{0,2}", gap_nc)) or \
               (lang == "ts" and "+" in gap_nc and re.fullmatch(r"[\s+]*", gap_nc)):
                merged[-1] = (ps, lit[1], text[ps:lit[1]], "str")
                continue
        merged.append(lit)
    return merged


def _is_docstring(text: str, start: int) -> bool:
    """A python literal standing alone as a statement right after a def/class/if line or at the top of the file."""
    k = start - 1
    while k >= 0 and text[k] in " \t":
        k -= 1
    line_start = k < 0 or text[k] == "\n"
    if not line_start:
        return False
    while k >= 0 and text[k] in " \t\r\n":
        k -= 1
    return k < 0 or text[k] == ":"


def _statements(lit_text: str) -> List[Tuple[int, str]]:
    """Split a literal into statements on ';' (offset of each statement within the literal)."""
    out, pos = [], 0
    for part in lit_text.split(";"):
        out.append((pos, part))
        pos += len(part) + 1
    return out


# ------------------------------------------------------------------------------------------- classification
def _body_literals(stmt: str) -> Optional[bool]:
    """True: provably non-node by literal body constraint; False: not provable; None: no body constraint at all."""
    if BODY_NOT_IN_RE.search(stmt):
        vals = [v for m in BODY_NOT_IN_RE.finditer(stmt) for v in STR_LIT_RE.findall(m.group(1))]
        if set(NODE_BODIES) <= {v for v in vals}:
            return True
    lits: List[str] = []
    any_constraint = False
    for m in BODY_EQ_RE.finditer(stmt):
        any_constraint = True
        lits.append(m.group(1))
    for m in BODY_IN_RE.finditer(stmt):
        if BODY_NOT_IN_RE.search(stmt[max(0, m.start() - 8):m.end()]):
            continue
        any_constraint = True
        lits.extend(STR_LIT_RE.findall(m.group(1)))
    if BODY_ANY_RE.search(stmt):
        return False
    if not any_constraint:
        return None
    return not any(v in NODE_BODIES for v in lits)


def classify(stmt: str, context_above: str) -> Tuple[bool, str]:
    """(pinned_or_exempt, reason) for one statement that reads ephemeris_daily."""
    if PIN_TOKEN_RE.search(stmt):
        return True, "NODE_SERIES_PREDICATE"
    if any(r.search(stmt) for r in PIN_PRED_RES):
        return True, "explicit node_mode predicate"
    for m in MARKER_RE.finditer(stmt + "\n" + context_above):
        reason = m.group(1).strip().rstrip("\"'`)*/ ").strip()
        if len(reason) >= 12 and not re.search(r"\b(Rahu|Ketu)\b", reason, re.I):
            return True, "node-agnostic marker"
        return False, f"invalid node-agnostic marker ({'names Rahu/Ketu' if re.search(r'Rahu|Ketu', reason, re.I) else 'reason shorter than 12 characters'})"
    if LIMIT0_RE.search(stmt):
        return True, "LIMIT 0 (returns no row)"
    bl = _body_literals(stmt)
    if bl is True:
        return True, "literal non-node body filter"
    return False, "no node_mode pin, marker or non-node body filter"


def _anchor_py(lines: List[str], lineno0: int) -> str:
    cur = lines[lineno0]
    m = re.match(r"\s*(\w+)\s*(?::[^=]+)?=\s*(?:\(\s*)?[rbfuRBFU]{0,2}(?:\"|')", cur) or re.match(r"\s*(\w+)\s*=\s*\(", cur)
    if m:
        return m.group(1)
    indent = len(cur) - len(cur.lstrip())
    names: List[str] = []
    for k in range(lineno0, -1, -1):
        ln = lines[k]
        if not ln.strip():
            continue
        ind = len(ln) - len(ln.lstrip())
        mm = re.match(r"\s*(?:async\s+def|def|class)\s+(\w+)", ln)
        if mm and ind < indent:
            names.append(mm.group(1))
            indent = ind
            if ind == 0:
                break
    return ".".join(reversed(names)) if names else "<module>"


def _anchor_ts(lines: List[str], lineno0: int) -> str:
    cur = lines[lineno0]
    m = re.match(r"\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=", cur) or re.match(r"\s*(\w+)\s*:\s*[`'\"]", cur)
    if m:
        return m.group(1)
    indent = len(cur) - len(cur.lstrip())
    names: List[str] = []
    for k in range(lineno0, -1, -1):
        ln = lines[k]
        if not ln.strip():
            continue
        ind = len(ln) - len(ln.lstrip())
        mm = (re.match(r"\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)", ln)
              or re.match(r"\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=", ln)
              or re.match(r"\s*(?:(?:public|private|protected|static|async)\s+)*(\w+)\s*\([^)]*\)\s*(?::[^{=]+)?\{\s*$", ln))
        if mm and ind < indent and mm.group(1) not in ("if", "for", "while", "switch", "catch", "return"):
            names.append(mm.group(1))
            indent = ind
            if ind == 0:
                break
    return ".".join(reversed(names)) if names else "<module>"


def scan_text(text: str, rel: str, lang: str) -> List[Site]:
    """All reads of ephemeris_daily in `text` (lang: py | ts | sql), each classified."""
    read_re = read_re_for(text)
    lines = text.split("\n")
    line_starts = [0]
    for ln in lines:
        line_starts.append(line_starts[-1] + len(ln) + 1)

    def lineno_of(off: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= off:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    sites: List[Site] = []

    def handle(block: str, block_off: int, doc: bool, anchor_fn):
        for soff, stmt in _statements(block):
            code_view = re.sub(r"--[^\n]*", lambda mm: " " * len(mm.group(0)), stmt) if lang == "sql" else stmt
            if doc or not SELECT_RE.search(code_view):
                continue
            for m in read_re.finditer(code_view):
                if DELETE_FROM_RE.search(code_view[max(0, m.start() - 12):m.start()]):
                    continue
                abs_off = block_off + soff + m.start()
                ln = lineno_of(abs_off)
                above = "\n".join(lines[max(0, lineno_of(block_off + soff) - 4):lineno_of(block_off + soff) - 1])
                pinned, reason = classify(code_view, above + "\n" + stmt if lang == "sql" else above)
                snippet = re.sub(r"\s+", " ", code_view.strip())[:110]
                anchor = "sql:" + " ".join(snippet.split(" ")[:7]) if lang == "sql" else anchor_fn(lineno_of(block_off + soff) - 1)
                sites.append(Site(rel, ln, anchor, snippet, pinned, reason))
                break  # one site per statement: pinning is judged per statement

    if lang == "sql":
        # SQL comments are statements' neighbours, not literals: keep them (markers live there)
        handle(text, 0, False, lambda l0: f"sql@{l0 + 1}")
        return sites
    anchor_fn = (lambda l0: _anchor_py(lines, l0)) if lang == "py" else (lambda l0: _anchor_ts(lines, l0))
    for start, end, lit, _ in _lex_literals(text, lang):
        if not read_re.search(lit):
            continue
        handle(lit, start, lang == "py" and _is_docstring(text, start), anchor_fn)
    return sites


# ------------------------------------------------------------------------------------------- repo scan
def _excluded(rel: str) -> bool:
    low = "/" + rel
    base = rel.rsplit("/", 1)[-1]
    return any(s in low for s in EXCLUDE_SUBSTRINGS) or (base.startswith("test_") and base.endswith(".py"))


def scan_repo(root: Path) -> List[Site]:
    out: List[Site] = []
    seen = set()
    for lang, globs in SCAN_GLOBS.items():
        for g in globs:
            for p in sorted(root.glob(g)):
                if not p.is_file():
                    continue
                rel = p.relative_to(root).as_posix()
                if rel in seen or _excluded(rel):
                    continue
                seen.add(rel)
                try:
                    text = p.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if "ephemeris_daily" not in text:
                    continue
                out.extend(scan_text(text, rel, lang))
    return out


def unpinned(sites: Sequence[Site]) -> List[Site]:
    return [s for s in sites if not s.pinned]


# ------------------------------------------------------------------------------------------- baseline + ratchet
def load_baseline(path: Path = BASELINE_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def baseline_counts(b: dict) -> Dict[str, int]:
    return {f"{e['file']}::{e['anchor']}": int(e["count"]) for e in b.get("entries", [])}


def ratchet(sites: Sequence[Site], baseline: dict, ceiling: int) -> List[str]:
    """Violations of R1-R5 as human-readable strings (empty = clean)."""
    errs: List[str] = []
    entries = baseline.get("entries", [])
    keys = [f"{e.get('file')}::{e.get('anchor')}" for e in entries]
    for k, c in Counter(keys).items():
        if c > 1:
            errs.append(f"R5 SHAPE: duplicate baseline key {k}")
    for e in entries:
        if not str(e.get("note", "")).strip():
            errs.append(f"R5 SHAPE: baseline entry {e.get('file')}::{e.get('anchor')} has no written note")
        if not isinstance(e.get("count"), int) or e["count"] < 1:
            errs.append(f"R5 SHAPE: baseline entry {e.get('file')}::{e.get('anchor')} needs an integer count >= 1")
    retired = {f"{r['file']}::{r['anchor']}" for r in baseline.get("retired", [])}
    for k in set(keys) & retired:
        errs.append(f"R5 SHAPE: {k} is both a live baseline entry and retired")
    base = baseline_counts(baseline)
    found = Counter(s.key for s in unpinned(sites))
    for k, c in sorted(found.items()):
        if k in retired:
            lines = ", ".join(str(s.line) for s in unpinned(sites) if s.key == k)
            errs.append(f"R3 RETIRED: {k} was pinned and retired from the baseline but reads ephemeris_daily unpinned again (line {lines})")
        elif c > base.get(k, 0):
            lines = ", ".join(str(s.line) for s in unpinned(sites) if s.key == k)
            what = "NEW unpinned reader" if k not in base else f"{c} unpinned readers (baseline allows {base[k]})"
            errs.append(f"R1 NEW: {k}: {what} (line {lines}); pin it with NODE_SERIES_PREDICATE / a node_mode predicate or a "
                        f"`node-agnostic:` comment. Do NOT add it to the baseline.")
    for k, c in sorted(base.items()):
        if found.get(k, 0) < c:
            errs.append(f"R2 STALE: {k}: baseline says {c}, found {found.get(k, 0)}; the reader is pinned or gone: shrink/remove the "
                        f"entry, record the key under `retired`, and lower RATCHET_CEILING_TOTAL")
    total = sum(base.values())
    if total != ceiling:
        errs.append(f"R4 CEILING: baseline total {total} != RATCHET_CEILING_TOTAL {ceiling} (the ceiling must equal the baseline; "
                    f"never raise it to make CI pass)")
    return errs


def against_ref(baseline: dict, ref: str, root: Path = REPO_ROOT) -> Tuple[List[str], str]:
    """Errors if `baseline` has a key or a count the ref's baseline lacks. Returns (errors, note); note explains a skip."""
    r = subprocess.run(["git", "show", f"{ref}:{BASELINE_REL}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return [], f"skipped: no {BASELINE_REL} at {ref} ({r.stderr.strip()[:80] or 'git unavailable'})"
    old = baseline_counts(json.loads(r.stdout))
    errs = []
    for k, c in baseline_counts(baseline).items():
        if k not in old:
            errs.append(f"GROWN: baseline key {k} is not in {ref}'s baseline")
        elif c > old[k]:
            errs.append(f"GROWN: baseline count for {k} rose {old[k]} -> {c} versus {ref}")
    return errs, f"compared with {ref}"


def emit_baseline(sites: Sequence[Site]) -> dict:
    grouped: "OrderedDict[str, dict]" = OrderedDict()
    for s in unpinned(sites):
        e = grouped.setdefault(s.key, {"file": s.file, "anchor": s.anchor, "count": 0, "lines_at_rollout": [], "note": ""})
        e["count"] += 1
        e["lines_at_rollout"].append(s.line)
    return {"entries": list(grouped.values()), "retired": []}


# ------------------------------------------------------------------------------------------- self-test
def run_self_test() -> int:
    ok = True
    for lang, ext in (("py", ".py"), ("ts", ".ts"), ("sql", ".sql")):
        for kind, want_unpinned in (("pass", False), ("fail", True)):
            d = FIXTURE_DIR / kind
            for p in sorted(d.glob(f"*{ext}")):
                found = unpinned(scan_text(p.read_text(encoding="utf-8"), p.name, lang))
                good = bool(found) if want_unpinned else not found
                if not good:
                    ok = False
                    print(f"SELF-TEST FAIL: {kind}/{p.name}: expected {'a flagged unpinned read' if want_unpinned else 'no unpinned read'}, "
                          f"got {[(s.line, s.reason) for s in found] or 'none'}")
    # fixtures must exist for every language and every verdict (a missing fixture is a blind scanner)
    for kind in ("pass", "fail"):
        for ext in (".py", ".ts", ".sql"):
            if not list((FIXTURE_DIR / kind).glob(f"*{ext}")):
                ok = False
                print(f"SELF-TEST FAIL: no {kind} fixture for {ext}")
    # ratchet self-test on a synthetic baseline
    s1 = Site("a.py", 1, "f", "x", False, "r")
    cases = [
        ("clean", [s1], {"entries": [{"file": "a.py", "anchor": "f", "count": 1, "note": "n"}], "retired": []}, 1, True),
        ("new reader", [s1, Site("b.py", 1, "g", "x", False, "r")],
         {"entries": [{"file": "a.py", "anchor": "f", "count": 1, "note": "n"}], "retired": []}, 1, False),
        ("stale entry", [], {"entries": [{"file": "a.py", "anchor": "f", "count": 1, "note": "n"}], "retired": []}, 1, False),
        ("retired comes back", [s1], {"entries": [], "retired": [{"file": "a.py", "anchor": "f"}]}, 0, False),
        ("ceiling raised", [s1], {"entries": [{"file": "a.py", "anchor": "f", "count": 1, "note": "n"}], "retired": []}, 2, False),
        ("no note", [s1], {"entries": [{"file": "a.py", "anchor": "f", "count": 1, "note": ""}], "retired": []}, 1, False),
    ]
    for name, sites, base, ceil, want_clean in cases:
        errs = ratchet(sites, base, ceil)
        if bool(errs) == want_clean:
            ok = False
            print(f"SELF-TEST FAIL: ratchet case '{name}': expected {'clean' if want_clean else 'a violation'}, got {errs or 'clean'}")
    print("self-test: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------- CLI
def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="reader-pin lint for the ephemeris_daily node series, with a ratchet")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-baseline", action="store_true", help="print a draft baseline (initial rollout or a shrink; review by hand)")
    ap.add_argument("--against", metavar="GIT_REF", help="also fail if the baseline grew relative to this ref")
    ap.add_argument("--root", default=str(REPO_ROOT))
    ap.add_argument("--baseline", default=str(BASELINE_PATH))
    args = ap.parse_args(argv)
    if args.self_test:
        return run_self_test()
    root = Path(args.root)
    sites = scan_repo(root)
    if args.emit_baseline:
        print(json.dumps(emit_baseline(sites), indent=2))
        return 0
    try:
        baseline = load_baseline(Path(args.baseline))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CONFIG ERROR: cannot read baseline: {exc}", file=sys.stderr)
        return 2
    errs = ratchet(sites, baseline, RATCHET_CEILING_TOTAL)
    note = ""
    if args.against:
        e2, note = against_ref(baseline, args.against, root)
        errs += e2
    pinned = [s for s in sites if s.pinned]
    if args.json:
        print(json.dumps({"reads": len(sites), "pinned_or_exempt": len(pinned), "unpinned": len(unpinned(sites)),
                          "baseline_total": sum(baseline_counts(baseline).values()), "errors": errs, "against": note}, indent=2))
    else:
        print(f"ephemeris_daily reads: {len(sites)} (pinned/exempt {len(pinned)}, unpinned {len(unpinned(sites))}; "
              f"baseline {sum(baseline_counts(baseline).values())}){' [' + note + ']' if note else ''}")
        for e in errs:
            print("  " + e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
