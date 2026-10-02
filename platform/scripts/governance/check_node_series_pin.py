#!/usr/bin/env python3
"""check_node_series_pin.py: the reader-pin lint for the `ephemeris_daily` node series, with a RATCHET.

WHY (SS N-68/N-69; DESIGN_L0_MEAN_NODE_SERIES_v1_0.md section 7; CLAUDE.md section N.7 item 2, same discipline as
`check_fact_category_pinning.py`). `ephemeris_daily` stores the TRUE node for Rahu/Ketu today (node_mode = 'true'; the seven
other bodies carry node_mode NULL). L0 is about to gain a second, MEAN, row set beside it. Every reader that can return
Rahu/Ketu rows and does not say WHICH series it means would, the day the second set exists, silently read both. This lint makes
"which series" a property that is checked, not remembered.

THIS LINT IS A RATCHET AND AN AID, NOT THE PROOF. A text lint cannot be made sound against query builders and string assembly (see
KNOWN BLIND SPOTS). It is FAIL-CLOSED: a read counts as pinned only when the lint can POSITIVELY show it.

WHAT IT SCANS. Every SQL statement that READS `ephemeris_daily` (a relation after FROM / JOIN / comma-join, or after USING in a
DELETE, or after FROM in an UPDATE; `"ephemeris_daily"`, `"public"."ephemeris_daily"`, `l0.ephemeris_daily`, `${schema}.ephemeris_daily`
and a file-level constant naming the table all count) in python / ts / tsx / js / mjs / cjs / sh string literals, sql files and the
migration directories, under platform/python-sidecar, platform/src, platform-mcp/src, platform/scripts, scripts, evals, infra, and
the migrations. Writers (INSERT INTO / UPDATE / DELETE FROM the table itself) are not reads; comments and docstrings are not reads.
Each SELECT branch is judged on its own: a UNION needs the proof in EVERY branch.

PINNED means ONE of (a)-(c), shown POSITIVELY on THAT read:
  (a) the shared helper: the bare `{NODE_SERIES_PREDICATE}` interpolation (services/w2g/node_series.py) as a top-level conjunct of
      that SELECT's own WHERE, or of the ON of that table's join;
  (b) a literal `node_mode` predicate (`node_mode = ...`, `IN`, `IS [NOT] NULL`, `COALESCE(node_mode, ..) = ..`, `.. = node_mode`) as
      a top-level conjunct of that SELECT's own WHERE (or ON bound to that table), on THIS table (qualified by its alias when the
      statement has more than one relation); a conjunct may be an OR whose every disjunct is such a predicate or a non-node body test;
  (c) a literal non-node body list with NO interpolation as such a conjunct: `body = 'Sun'`, `body IN ('Sun','Moon')`, or
      `body NOT IN ('Rahu','Ketu')`.
EVERYTHING ELSE is UNPINNED: comments never satisfy a pin (`--`, `/* */`, `#`, `//`); a predicate on another table; a variable or
interpolated body filter (`body IN ({ph})`, `body = '{b}'`, `%s`, `$1`, `:name`); a conditional pin (`${c ? "AND node_mode = 'true'" : ""}`,
`{NODE_SERIES_PREDICATE if x else 'TRUE'}`); a node_mode mention outside the WHERE / ON (SELECT list, SET, GROUP BY); a pin in a
neighbouring SELECT or CTE. `LIMIT 0` and counts are not special: they need an exemption marker or a baseline entry.

EXEMPTION MARKER (explicit, closed reason codes, scoped to the ONE statement it is attached to):
    node-agnostic: <reason_code>: <what it is, 12+ characters, not naming Rahu or Ketu>
  non_node_bodies_literal   the read is restricted to non-node bodies by a literal list the lint cannot see in the WHERE (e.g. the list
                            is passed in as a parameter from a literal constant of non-node bodies);
  count_only_table_level    a table-level count/aggregate (floor/volume checks, registry count_sql descriptors) that returns no node value;
  schema_introspection      a probe that never returns rows (LIMIT 0 availability probes, existence checks);
  legacy_dead_code          a statement that cannot run against the current schema (legacy column names) and is never reached.
  Placement: a `--` / `/* */` comment INSIDE the statement; or (python/ts/sh) a `#` / `//` comment on the line of the literal or in the
  comment block directly above it (no blank line; one opener line such as `c.execute(` may sit between). A marker above a function
  never reaches the next function's read. An unknown code, a short text, or text naming Rahu/Ketu is an INVALID marker (unpinned).

RATCHET (the baseline can only shrink). `node_series_pin_baseline.json` lists today's unpinned readers as (file, anchor, count)
entries; anchor = the ENCLOSING def (class.def, nested closures dotted; TS: the enclosing function/method/arrow const) and, for a
module- or class-level constant only, the assigned name; `count` plays the role of an ordinal within one enclosing def (a second
read in the same def raises the count). Default mode FAILS on:
  R1 NEW      an unpinned reader not in the baseline, or more unpinned readers under one (file, anchor) than its count;
  R2 STALE    a baseline count above the unpinned readers found: shrink the count to what is found (and, when none is left, remove the
              entry and record the key under `retired`);
  R3 RETIRED  an unpinned reader under a (file, anchor) in `retired`: a pinned reader may never come back;
  R4 CEILING  the baseline total differs from RATCHET_CEILING_TOTAL below (never raise it to make CI pass; lower it after a fix);
  R5 SHAPE    an entry without a written `note` and `owner`, a duplicate key, an entry both live and retired.
GROWTH GUARD (`--against <ref>`, run for real in CI by the governance pytest step): the baseline total, any (file, anchor) count, a new
key and RATCHET_CEILING_TOTAL may not exceed the merge-base's (or, on a shallow CI checkout, the fetched ref's), UNLESS the baseline
carries a NEW top-level `ceiling_raise_approved: "<reason>"` (different from the ref's): the explicit, reviewable marker; the test prints it.

KNOWN BLIND SPOTS (documented, not modelled; fixtures marked xfail in the tests): Supabase `.from("ephemeris_daily")`, SQLAlchemy
`Table(...)`, `sql.Identifier(...)`, `.format("ephemeris_daily")`; python `+` concatenation and `" ".join([...])` of SQL pieces; a table name or a
whole statement imported from another file; SQL assembled across statements or variables; heredoc SQL in shell scripts; HTTP callers
of the L0 routes (covered through the route's own SQL). The one table-name-argument form seen in the repo, `count("ephemeris_daily")`,
is matched narrowly (functions count / row_count / table_count).

Modes: --self-test; (default) repo scan + ratchet; --json; --emit-baseline (draft, review by hand); --against <git ref>.
Exit codes: 0 clean; 1 violation / self-test fail; 2 invocation or config error.
"""
from __future__ import annotations

import argparse
import json
import os
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
SCRIPT_REL = "platform/scripts/governance/check_node_series_pin.py"

# NEVER raise this to make CI pass. It must equal the baseline's total; a fix lowers both.
RATCHET_CEILING_TOTAL = 32  # must equal the baseline total (rev 2; rev 1 was 32); see node_series_pin_baseline.json

TABLE = "ephemeris_daily"
_TS_EXT = ("ts", "tsx", "js", "mjs", "cjs")
SCAN_GLOBS: Dict[str, List[str]] = {
    "py": [f"{r}/**/*.{e}" for r in ("platform/python-sidecar", "platform/scripts", "scripts", "evals", "infra") for e in ("py", "sh")],
    "ts": [f"{r}/**/*.{e}" for r in ("platform/src", "platform-mcp/src", "platform/scripts", "scripts", "evals", "infra") for e in _TS_EXT],
    "sql": [f"{r}/**/*.sql" for r in ("platform/scripts", "platform/migrations", "platform/supabase/migrations", "scripts", "evals", "infra")],
}
EXCLUDE_SUBSTRINGS = (
    "node_series_pin_fixtures/", "check_node_series_pin.py", "/__tests__/", "/tests/", "/node_modules/", "/generated/",
    "/_archive/", "/.clone/", "/dist/", "/.venv/", "/.next/", ".test.ts", ".test.tsx", ".test.js", ".spec.ts", "/conftest.py",
)
NODE_BODIES = ("rahu", "ketu")
MARKER_CODES = ("non_node_bodies_literal", "count_only_table_level", "schema_introspection", "legacy_dead_code")
MARKER_RE = re.compile(r"node-agnostic:[ \t]*([A-Za-z_]+)[ \t]*:?[ \t]*([^\n\r]*)", re.I)
ALIAS_DEF_RE = re.compile(
    r"^[ \t]*(?:export[ \t]+)?(?:const[ \t]+|let[ \t]+)?([A-Za-z_]\w*)[ \t]*(?::[^=\n]+)?=[ \t]*[\"'`](?:\w+\.)?ephemeris_daily[\"'`][ \t]*;?[ \t]*$",
    re.M)
TABLE_ARG_CALL_RE = re.compile(r"\b(?:count|row_count|table_count)\(\s*[\"'](?:\w+\.)?ephemeris_daily[\"']")


@dataclass(frozen=True)
class Site:
    file: str       # repo-relative POSIX path
    line: int       # 1-indexed line of the FROM/JOIN
    anchor: str     # enclosing def (class.def) / TS function / constant name
    snippet: str    # normalized statement head
    pinned: bool
    reason: str     # why it is pinned/exempt, or why it is not

    @property
    def key(self) -> str:
        return f"{self.file}::{self.anchor}"


# ------------------------------------------------------------------------------------------- SQL tokenizer + block parser
@dataclass(frozen=True)
class Tok:
    type: str       # word | str | qid | param | num | op
    text: str
    up: str         # upper-case text for words, raw text otherwise
    pos: int


_TOKEN_RE = re.compile(
    r"(?P<ws>\s+)|(?P<lc>--[^\n]*)|(?P<bc>/\*.*?\*/)|(?P<str>'(?:[^']|'')*')|(?P<qid>\"(?:[^\"]|\"\")*\")"
    r"|(?P<param>%\([A-Za-z_]\w*\)s|%s|\$\d+|(?<!:):[A-Za-z_]\w*|\?)|(?P<word>[A-Za-z_][A-Za-z0-9_$]*)|(?P<num>\d+(?:\.\d+)?)|(?P<op>.)",
    re.S)
_INTERP = "__INTERP__"
_COMP = r"(?:=|< >|! =|< =|> =|<|>|IN|IS|NOT IN|LIKE)"


def _tokenize(text: str):
    toks: List[Tok] = []
    comments: List[Tuple[int, str]] = []
    for m in _TOKEN_RE.finditer(text):
        k = m.lastgroup
        if k == "ws":
            continue
        if k in ("lc", "bc"):
            comments.append((m.start(), m.group()))
            continue
        s = m.group()
        toks.append(Tok(k, s, s.upper() if k == "word" else s, m.start()))
    return toks, comments


def _unq(t: Tok) -> str:
    return t.text[1:-1].replace('""', '"') if t.type == "qid" else t.text


@dataclass
class Rel:
    name: str
    alias: str
    on: List[Tuple[Tok, int]]
    tok: Tok


@dataclass
class Block:
    kind: str
    rels: List[Rel]
    reads: List[Rel]
    where: List[Tuple[Tok, int]]


def _find_blocks(toks: List[Tok]) -> List[Block]:
    n = len(toks)
    depth = [0] * n
    d = 0
    for i, t in enumerate(toks):
        if t.type == "op" and t.text == ")":
            d -= 1
        depth[i] = d
        if t.type == "op" and t.text == "(":
            d += 1
    match: Dict[int, int] = {}
    st: List[int] = []
    for i, t in enumerate(toks):
        if t.type == "op" and t.text == "(":
            st.append(i)
        elif t.type == "op" and t.text == ")" and st:
            match[st.pop()] = i
    sub = {o for o in match if o + 1 < n and toks[o + 1].type == "word" and toks[o + 1].up in ("SELECT", "WITH", "VALUES")}
    blocks: List[Block] = []
    for i, t in enumerate(toks):
        if t.type != "word":
            continue
        kind = None
        if t.up == "SELECT":
            kind = "SELECT"
        elif t.up in ("UPDATE", "DELETE") and (i == 0 or toks[i - 1].text == ")"):
            kind = t.up
        if kind is None:
            continue
        end = n
        for k in range(i + 1, n):
            if depth[k] < depth[i]:
                end = k
                break
            if depth[k] == depth[i] and toks[k].type == "word":
                if toks[k].up in ("UNION", "INTERSECT", "EXCEPT"):
                    end = k
                    break
                if toks[k].up == "ON" and k + 1 < n and toks[k + 1].up == "CONFLICT":
                    end = k
                    break
        clauses: Dict[str, List[int]] = {c: [] for c in ("select", "target", "delfrom", "set", "from", "where", "group", "limit", "other")}
        clause = "select" if kind == "SELECT" else "target"
        k = i + 1
        while k < end:
            if k in sub and match[k] < end:
                k = match[k] + 1
                continue
            tk = toks[k]
            if depth[k] == depth[i] and tk.type == "word":
                u = tk.up
                if u == "FROM" and not (k > 0 and toks[k - 1].up == "DISTINCT"):
                    clause = "delfrom" if (kind == "DELETE" and clause == "target") else "from"
                    k += 1
                    continue
                if u == "USING" and kind == "DELETE" and clause == "delfrom":
                    clause = "from"
                    k += 1
                    continue
                if u == "WHERE":
                    clause = "where"
                    k += 1
                    continue
                if u == "GROUP":
                    clause = "group"
                    k += 1
                    continue
                if u in ("HAVING", "ORDER", "OFFSET", "WINDOW", "FETCH", "FOR", "RETURNING"):
                    clause = "other"
                    k += 1
                    continue
                if u == "LIMIT":
                    clause = "limit"
                    k += 1
                    continue
                if u == "SET" and kind == "UPDATE" and clause == "target":
                    clause = "set"
                    k += 1
                    continue
            clauses[clause].append(k)
            k += 1
        # parse the FROM clause into relation items at the block's own depth
        items: List[Dict] = [{"rel": [], "on": []}]
        mode = "rel"
        for k in clauses["from"]:
            tk = toks[k]
            if depth[k] == depth[i] and tk.type == "word":
                if tk.up == "JOIN":
                    items.append({"rel": [], "on": []})
                    mode = "rel"
                    continue
                if tk.up in ("INNER", "LEFT", "RIGHT", "FULL", "CROSS", "NATURAL", "OUTER") and not (k + 1 < n and toks[k + 1].text == "("):
                    continue
                if tk.up == "ON":
                    mode = "on"
                    continue
                if tk.up == "USING":
                    mode = "using"
                    continue
            if depth[k] == depth[i] and tk.type == "op" and tk.text == ",":
                items.append({"rel": [], "on": []})
                mode = "rel"
                continue
            if mode == "rel":
                items[-1]["rel"].append(tk)
            elif mode == "on":
                items[-1]["on"].append((tk, depth[k]))
        rels: List[Rel] = []
        for it in items:
            r = [x for x in it["rel"] if not (x.type == "word" and x.up in ("ONLY", "LATERAL"))]
            if not r or r[0].text == "(":
                continue
            comps: List[str] = []
            j = 0
            while j < len(r) and r[j].type in ("word", "qid"):
                comps.append(_unq(r[j]))
                if j + 1 < len(r) and r[j + 1].text == ".":
                    j += 2
                    continue
                j += 1
                break
            if not comps:
                continue
            alias = ""
            if j < len(r) and r[j].type == "word" and r[j].up == "AS":
                j += 1
            if j < len(r) and r[j].type in ("word", "qid") and r[j].up not in ("TABLESAMPLE",):
                alias = _unq(r[j])
            rels.append(Rel(comps[-1].lower(), (alias or comps[-1]).lower(), it["on"], r[0]))
        where = [(toks[k], depth[k]) for k in clauses["where"]]
        blocks.append(Block(kind, rels, [r for r in rels if r.name == TABLE], where))
    return blocks


def _strip_parens(seq):
    while len(seq) >= 2 and seq[0][0].text == "(" and seq[0][0].type == "op":
        close = None
        for j in range(1, len(seq)):
            if seq[j][0].text == ")" and seq[j][0].type == "op" and seq[j][1] == seq[0][1]:
                close = j
                break
        if close == len(seq) - 1:
            seq = seq[1:-1]
        else:
            break
    return seq


def _split_top(seq, word: str):
    if not seq:
        return [seq]
    base = min(d for _, d in seq)
    parts, cur, between = [], [], False
    for tk, d in seq:
        if d == base and tk.type == "word":
            if tk.up == "BETWEEN":
                between = True
            elif tk.up == "AND" and between:
                between = False
            elif tk.up == word:
                parts.append(cur)
                cur = []
                continue
        cur.append((tk, d))
    parts.append(cur)
    return parts


def _qual_ok(toks: List[Tok], idx: int, rel: Rel, single: bool) -> bool:
    if idx >= 2 and toks[idx - 1].text == ".":
        return _unq(toks[idx - 2]).lower() in (rel.alias, TABLE)
    return single


def _flat(toks: List[Tok]) -> str:
    out = []
    for t in toks:
        if t.type == "str":
            out.append("'S'")
        elif t.type == "param":
            out.append("?")
        elif t.type == "num":
            out.append("N")
        elif t.type == "qid":
            out.append(_unq(t).upper())
        else:
            out.append(t.up)
    return " ".join(out)


def _is_lit_str(t: Tok) -> bool:
    return t.type == "str" and _INTERP not in t.text


def _atom_safe(seq, rel: Rel, single: bool) -> Optional[str]:
    toks = [t for t, _ in seq]
    if not toks:
        return None
    if len(toks) == 1 and toks[0].type == "word" and toks[0].up == "NODE_SERIES_PREDICATE":
        return "NODE_SERIES_PREDICATE"
    flat = _flat(toks)
    # node_mode predicates (literal predicate text on THIS table)
    for pat in (r"(?:\w+ \. )?NODE_MODE %s .*" % _COMP,
                r"COALESCE \( (?:\w+ \. )?NODE_MODE , .* \) %s .*" % _COMP,
                r".* (?:=|< >|! =) (?:\w+ \. )?NODE_MODE"):
        m = re.fullmatch(pat, flat)
        if m:
            idx = next((i for i, t in enumerate(toks) if t.type in ("word", "qid") and _unq(t).upper() == "NODE_MODE"), None)
            if idx is not None and _qual_ok(toks, idx, rel, single):
                return "node_mode predicate"
    # literal body tests
    for i, t in enumerate(toks):
        if t.type in ("word", "qid") and _unq(t).upper() == "BODY" and i in (0, 2):
            if i == 2 and not _qual_ok(toks, i, rel, single):
                return None
            rest = toks[i + 1:]
            vals: Optional[List[str]] = None
            neg = False
            if len(rest) == 2 and rest[0].text == "=" and _is_lit_str(rest[1]):
                vals = [rest[1].text[1:-1]]
            else:
                r2 = rest
                if len(r2) >= 2 and r2[0].up == "NOT" and r2[1].up == "IN":
                    neg, r2 = True, r2[2:]
                elif len(r2) >= 1 and r2[0].up == "IN":
                    r2 = r2[1:]
                else:
                    r2 = None
                if r2 and r2[0].text == "(" and r2[-1].text == ")":
                    inner = r2[1:-1]
                    if inner and all((j % 2 == 0 and _is_lit_str(x)) or (j % 2 == 1 and x.text == ",") for j, x in enumerate(inner)) and len(inner) % 2 == 1:
                        vals = [x.text[1:-1] for j, x in enumerate(inner) if j % 2 == 0]
            if vals is not None:
                low = {v.lower() for v in vals}
                if neg:
                    if set(NODE_BODIES) <= low:
                        return "literal non-node body list"
                elif not (low & set(NODE_BODIES)):
                    return "literal non-node body list"
            return None
    return None


def _safe_seq(seq, rel: Rel, single: bool) -> Optional[str]:
    seq = _strip_parens(seq)
    if not seq:
        return None
    ors = _split_top(seq, "OR")
    if len(ors) > 1:
        rs = [_safe_seq(p, rel, single) for p in ors]
        return rs[0] if all(rs) else None
    ands = _split_top(seq, "AND")
    if len(ands) > 1:
        for p in ands:
            r = _safe_seq(p, rel, single)
            if r:
                return r
        return None
    return _atom_safe(seq, rel, single)


def _pin_reason(block: Block, rel: Rel) -> Optional[str]:
    single = len(block.rels) == 1
    for seq in (block.where, rel.on):
        if seq:
            r = _safe_seq(seq, rel, single)
            if r:
                return r
    return None


def _valid_marker(comment_texts: Sequence[str]) -> Tuple[Optional[bool], str]:
    """(True, code) when a valid marker is found; (False, why) when a marker exists but is invalid; (None, '') when none."""
    bad = None
    for c in comment_texts:
        m = MARKER_RE.search(c)
        if not m:
            continue
        code, txt = m.group(1).lower(), m.group(2).strip().rstrip("*/ ").strip()
        if code not in MARKER_CODES:
            bad = f"invalid node-agnostic marker (unknown reason code '{code}'; allowed: {', '.join(MARKER_CODES)})"
        elif len(txt) < 12:
            bad = "invalid node-agnostic marker (text shorter than 12 characters)"
        elif re.search(r"\b(rahu|ketu)\b", txt, re.I):
            bad = "invalid node-agnostic marker (text names Rahu/Ketu)"
        else:
            return True, code
    return (False, bad) if bad else (None, "")


@dataclass
class RawSite:
    pos: int
    snippet: str
    pinned: bool
    reason: str


def _analyze(text: str, extra_comments: Sequence[str] = ()) -> List[RawSite]:
    """Every read of ephemeris_daily in one SQL text (statements split on ';' outside quotes and comments)."""
    toks, comments = _tokenize(text)
    stmts: List[Tuple[List[Tok], int, int]] = []
    cur: List[Tok] = []
    start = 0
    for t in toks:
        if t.type == "op" and t.text == ";":
            stmts.append((cur, start, t.pos))
            cur, start = [], t.pos + 1
        else:
            cur.append(t)
    stmts.append((cur, start, len(text)))
    out: List[RawSite] = []
    first = True
    for stoks, s0, s1 in stmts:
        if not stoks:
            continue
        blocks = [b for b in _find_blocks(stoks) if b.reads]
        if blocks:
            ctext = [c for p, c in comments if s0 <= p < s1] + (list(extra_comments) if first else [])
            mk, why = _valid_marker(ctext)
            head = re.sub(r"\s+", " ", text[stoks[0].pos:stoks[min(len(stoks), 12) - 1].pos + 8]).strip()
            for b in blocks:
                for rel in b.reads:
                    if mk:
                        pinned, reason = True, f"node-agnostic marker ({why})"
                    else:
                        r = _pin_reason(b, rel)
                        pinned, reason = (True, r) if r else (False, why if mk is False else "no positive node-series pin on this read")
                    out.append(RawSite(rel.tok.pos, head[:110], pinned, reason))
        first = False
    return out


# ------------------------------------------------------------------------------------------- literal lexer (py / ts)
@dataclass
class Lit:
    start: int
    end: int
    content: str
    segs: List[Tuple[int, int]]     # (offset in normalized content, source start)
    last_end: int


def _lex(text: str, lang: str):
    """String literals (python: ' \" ''' \"\"\" and # comments; ts: ' \" ` and // /* */ comments) merged when adjacent (python implicit
    concatenation, TS `+`), plus the comments seen outside literals as (pos, text)."""
    pieces: List[Tuple[int, int]] = []
    comments: List[Tuple[int, str]] = []
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
            e = text.find("\n", i)
            e = n if e == -1 else e
            comments.append((i, text[i:e]))
            i = e
            continue
        if lang == "ts" and c == "/" and text.startswith("//", i):
            e = text.find("\n", i)
            e = n if e == -1 else e
            comments.append((i, text[i:e]))
            i = e
            continue
        if lang == "ts" and c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            comments.append((i, text[i:j]))
            i = j
            continue
        if c in "'\"" or (c == "`" and lang == "ts"):
            j = skip_string(i)
            pieces.append((i, j))
            i = j
            continue
        i += 1
    groups: List[List[Tuple[int, int]]] = []
    for pc in pieces:
        if groups:
            pe = groups[-1][-1][1]
            gap = text[pe:pc[0]]
            gap_nc = re.sub(r"#[^\n]*" if lang == "py" else r"//[^\n]*|/\*.*?\*/", "", gap, flags=re.S)
            if (lang == "py" and re.fullmatch(r"\s*[rbfuRBFU]{0,2}", gap_nc)) or \
               (lang == "ts" and "+" in gap_nc and re.fullmatch(r"[\s+]*", gap_nc)):
                groups[-1].append(pc)
                continue
        groups.append([pc])
    return groups, comments


def _piece_content(text: str, s: int, e: int, lang: str) -> str:
    raw = text[s:e]
    q = raw[0]
    d = 3 if (lang == "py" and raw.startswith(q * 3) and len(raw) >= 6) else 1
    body = raw[d:-d] if len(raw) >= 2 * d and raw.endswith(q * d) else raw[d:]
    return re.sub(r"\\[nrt]", " ", body)


def _braced(s: str, i: int) -> int:
    depth, j = 1, i
    while j < len(s) and depth:
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
        j += 1
    return j


def _normalize(content: str, aliases: Sequence[str]) -> str:
    """Interpolations: the bare NODE_SERIES_PREDICATE and a table-name constant keep their meaning; anything else becomes __INTERP__."""
    out, i, n = [], 0, len(content)
    while i < n:
        c = content[i]
        if c == "{" or (c == "$" and content.startswith("${", i)):
            j0 = i + (2 if c == "$" else 1)
            j = _braced(content, j0)
            inner = content[j0:j - 1].strip()
            last = inner.rsplit(".", 1)[-1]
            if re.fullmatch(r"(?:\w+\.)*NODE_SERIES_PREDICATE", inner):
                out.append(" NODE_SERIES_PREDICATE ")
            elif re.fullmatch(r"(?:\w+\.)*\w+", inner) and last in aliases:
                out.append(TABLE)
            else:
                out.append(_INTERP)
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


# ------------------------------------------------------------------------------------------- anchors
def _indent(s: str) -> int:
    return len(s) - len(s.lstrip())


def _enclosing(lines: List[str], line0: int, lang: str) -> Tuple[str, bool]:
    """(dotted enclosing def chain or '<module>', found_def)."""
    cur = lines[line0] if line0 < len(lines) else ""
    indent = _indent(cur)
    names: List[str] = []
    skipping_cont = False
    for k in range(min(line0, len(lines) - 1), -1, -1):
        ln = lines[k]
        if not ln.strip():
            continue
        ind = _indent(ln)
        if lang == "py":
            if ind < indent:
                m = re.match(r"\s*(?:async\s+def|def|class)\s+(\w+)", ln)
                if m:
                    names.append(m.group(1))
                    indent = ind
                    if ind == 0:
                        break
                elif ln.lstrip()[0] in ")]}":
                    # a multi-line signature closing line: keep walking to its def at the same indent
                    for k2 in range(k - 1, -1, -1):
                        l2 = lines[k2]
                        if l2.strip() and _indent(l2) <= ind and re.match(r"\s*(?:async\s+def|def|class)\s+(\w+)", l2):
                            names.append(re.match(r"\s*(?:async\s+def|def|class)\s+(\w+)", l2).group(1))
                            indent = _indent(l2)
                            break
                    if indent == 0:
                        break
        else:
            if ind < indent:
                mm = (re.match(r"\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)", ln)
                      or re.match(r"\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*(?::[^=]+)?=>|\w+\s*=>)", ln)
                      or re.match(r"\s*(?:(?:public|private|protected|static|async)\s+)*(\w+)\s*\([^)]*\)\s*(?::[^{=]+)?\{\s*$", ln)
                      or re.match(r"\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", ln))
                if mm and mm.group(1) not in ("if", "for", "while", "switch", "catch", "return"):
                    names.append(mm.group(1))
                    indent = ind
                    if ind == 0:
                        break
    return (".".join(reversed(names)), True) if names else ("<module>", False)


def _assign_name(lines: List[str], line0: int) -> Optional[str]:
    for k in (line0, line0 - 1):
        if 0 <= k < len(lines):
            m = re.match(r"\s*(?:export\s+)?(?:const\s+|let\s+|var\s+)?(\w+)\s*(?::[^=]+)?=\s*(?:\(\s*)?(?:[rbfuRBFU]{0,2}[\"'`]|$)", lines[k])
            if m:
                return m.group(1)
    return None


def _anchor(lines: List[str], line0: int, lang: str) -> str:
    enc, found = _enclosing(lines, line0, lang)
    if not found:
        nm = _assign_name(lines, line0)
        return f"<module>.{nm}" if nm else "<module>"
    return enc


def _comments_for(lines: List[str], comments_by_line: Dict[int, List[str]], first0: int, last0: int, lang: str) -> List[str]:
    """Code comments attached to the literal on lines first0..last0: on those lines, and the comment-only block directly above."""
    out: List[str] = []
    for ln in range(first0, last0 + 1):
        out += comments_by_line.get(ln, [])
    k = first0 - 1
    opener_used = False
    while k >= 0:
        s = lines[k].strip()
        if not s:
            break
        only_comment = s.startswith("#") if lang == "py" else s.startswith(("//", "/*", "*"))
        if only_comment:
            out += comments_by_line.get(k, [s])
            k -= 1
            continue
        if not opener_used and s.endswith(("(", "[", ",", "=", "+", "{")):
            opener_used = True
            out += comments_by_line.get(k, [])
            k -= 1
            continue
        break
    return out


def _is_docstring(text: str, start: int, end: int) -> bool:
    """A python literal that is a def/class docstring or the module docstring (standalone statement)."""
    k = start - 1
    while k >= 0 and text[k] in " \t":
        k -= 1
    if not (k < 0 or text[k] == "\n"):
        return False
    j = end
    while j < len(text) and text[j] in " \t":
        j += 1
    if j < len(text) and text[j] not in "\r\n#":
        return False
    lines = text[:start].split("\n")
    li = len(lines) - 1                                  # index of the literal's line
    cur_ind = len(lines[li]) - len(lines[li].lstrip())
    code = [(i, l) for i, l in enumerate(lines[:li]) if l.strip() and not l.strip().startswith("#")]
    if not code:
        return True                                      # module docstring
    for i, l in reversed(code):
        if _indent(l) < cur_ind:
            if re.match(r"\s*(?:async\s+def|def|class)\s+\w+", l):
                return l.rstrip().endswith(":")
            if l.lstrip()[0] in ")]}" and l.rstrip().endswith(":"):
                for i2, l2 in reversed([c for c in code if c[0] < i]):
                    if _indent(l2) <= _indent(l) and re.match(r"\s*(?:async\s+def|def|class)\s+\w+", l2):
                        return True
            return False
        break
    return False


# ------------------------------------------------------------------------------------------- scanning
def scan_text(text: str, rel: str, lang: str) -> List[Site]:
    """All reads of ephemeris_daily in `text` (lang: py | ts | sql), each classified."""
    lines = text.split("\n")
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln) + 1)

    def lineno(off: int) -> int:
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= off:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    sites: List[Site] = []
    if lang == "sql":
        for rs in _analyze(text):
            ln = lineno(rs.pos)
            sites.append(Site(rel, ln, "sql:" + " ".join(rs.snippet.split(" ")[:7]), rs.snippet, rs.pinned, rs.reason))
        return sites
    aliases = sorted(set(ALIAS_DEF_RE.findall(text)))
    groups, comments = _lex(text, lang)
    comments_by_line: Dict[int, List[str]] = {}
    for p, c in comments:
        comments_by_line.setdefault(lineno(p) - 1, []).append(c)
    for g in groups:
        pcs = [_normalize(_piece_content(text, s, e, lang), aliases) for s, e in g]
        content = "".join(pcs)
        if TABLE not in content:
            continue
        if lang == "py" and len(g) == 1 and _is_docstring(text, g[0][0], g[0][1]):
            continue
        first0, last0 = lineno(g[0][0]) - 1, lineno(g[-1][1] - 1) - 1
        extra = _comments_for(lines, comments_by_line, first0, last0, lang)
        anchor = _anchor(lines, first0, lang)
        offs, acc = [], 0
        for (s, _e), pc in zip(g, pcs):
            offs.append((acc, s))
            acc += len(pc)
        for rs in _analyze(content, extra):
            seg = max((o for o in offs if o[0] <= rs.pos), key=lambda o: o[0])
            ln = lineno(seg[1]) + content.count("\n", seg[0], rs.pos)
            sites.append(Site(rel, ln, anchor, rs.snippet, rs.pinned, rs.reason))
    for m in TABLE_ARG_CALL_RE.finditer(text):
        ln0 = lineno(m.start()) - 1
        extra = _comments_for(lines, comments_by_line, ln0, ln0, lang)
        mk, why = _valid_marker(extra)
        sites.append(Site(rel, ln0 + 1, _anchor(lines, ln0, lang), m.group(0)[:110], bool(mk),
                          f"node-agnostic marker ({why})" if mk else (why if mk is False else "table name passed to a count helper: no SQL visible to pin")))
    return sorted(sites, key=lambda s: s.line)


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
                if TABLE not in text:
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
        k = f"{e.get('file')}::{e.get('anchor')}"
        if not str(e.get("note", "")).strip() or not str(e.get("owner", "")).strip():
            errs.append(f"R5 SHAPE: baseline entry {k} needs a written note and a named owner")
        if not isinstance(e.get("count"), int) or e["count"] < 1:
            errs.append(f"R5 SHAPE: baseline entry {k} needs an integer count >= 1")
    retired = {f"{r['file']}::{r['anchor']}" for r in baseline.get("retired", [])}
    for k in set(keys) & retired:
        errs.append(f"R5 SHAPE: {k} is both a live baseline entry and retired")
    base = baseline_counts(baseline)
    found = Counter(s.key for s in unpinned(sites))
    for k, c in sorted(found.items()):
        lines = ", ".join(str(s.line) for s in unpinned(sites) if s.key == k)
        if k in retired:
            errs.append(f"R3 RETIRED: {k} was pinned and retired from the baseline but reads ephemeris_daily unpinned again (line {lines})")
        elif c > base.get(k, 0):
            what = "NEW unpinned reader" if k not in base else f"{c} unpinned readers (baseline allows {base[k]})"
            errs.append(f"R1 NEW: {k}: {what} (line {lines}); pin it (NODE_SERIES_PREDICATE or a literal node_mode predicate in its WHERE) or add a "
                        f"`node-agnostic: <reason_code>: <text>` marker. Do NOT add it to the baseline.")
    for k, c in sorted(base.items()):
        n = found.get(k, 0)
        if n < c:
            if n == 0:
                errs.append(f"R2 STALE: {k}: baseline says {c}, found 0; the reader is pinned or gone: remove the entry, record the key under "
                            f"`retired`, and lower RATCHET_CEILING_TOTAL")
            else:
                errs.append(f"R2 STALE: {k}: baseline says {c}, found {n}; lower the entry's count to {n} and lower RATCHET_CEILING_TOTAL "
                            f"(do not retire a key that still has a reader)")
    total = sum(base.values())
    if total != ceiling:
        errs.append(f"R4 CEILING: baseline total {total} != RATCHET_CEILING_TOTAL {ceiling} (the ceiling must equal the baseline; "
                    f"never raise it to make CI pass)")
    return errs


def _git(args: List[str], root: Path):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def ensure_ref(ref: str, root: Path = REPO_ROOT, fetch: bool = False) -> bool:
    """True when `ref` resolves; with fetch=True try `git fetch --depth=1 origin <branch>` first (a shallow CI checkout)."""
    if fetch:
        branch = ref.split("/", 1)[1] if ref.startswith("origin/") else ref
        _git(["fetch", "--no-tags", "--depth=1", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"], root)
    return _git(["rev-parse", "--verify", "-q", ref + "^{commit}"], root).returncode == 0


def _ceiling_from_script(src: str) -> Optional[int]:
    m = re.search(r"^RATCHET_CEILING_TOTAL\s*=\s*(\d+)", src, re.M)
    return int(m.group(1)) if m else None


def against_ref(baseline: dict, ref: str, root: Path = REPO_ROOT, ceiling: Optional[int] = None) -> Tuple[List[str], str]:
    """Growth guard. Errors if the baseline grew (a key, a count, the total, the ceiling) versus the merge-base with `ref`
    (or `ref` itself when no merge-base is available, a shallow checkout), unless the baseline carries a NEW `ceiling_raise_approved`.
    Returns (errors, note); note explains a skip (ref absent / baseline absent at the ref)."""
    if not ensure_ref(ref, root):
        return [], f"skipped: ref {ref} not available"
    mb = _git(["merge-base", "HEAD", ref], root)
    base_ref = mb.stdout.strip() if mb.returncode == 0 and mb.stdout.strip() else ref
    r = _git(["show", f"{base_ref}:{BASELINE_REL}"], root)
    if r.returncode != 0:
        return [], f"initial introduction: no {BASELINE_REL} at {base_ref[:12]}"
    old_b = json.loads(r.stdout)
    old = baseline_counts(old_b)
    grown: List[str] = []
    for k, c in baseline_counts(baseline).items():
        if k not in old:
            grown.append(f"GROWN: baseline key {k} is not in {base_ref[:12]}'s baseline")
        elif c > old[k]:
            grown.append(f"GROWN: baseline count for {k} rose {old[k]} -> {c} versus {base_ref[:12]}")
    if sum(baseline_counts(baseline).values()) > sum(old.values()):
        grown.append(f"GROWN: baseline total {sum(old.values())} -> {sum(baseline_counts(baseline).values())}")
    if ceiling is not None:
        rs = _git(["show", f"{base_ref}:{SCRIPT_REL}"], root)
        oc = _ceiling_from_script(rs.stdout) if rs.returncode == 0 else None
        if oc is not None and ceiling > oc:
            grown.append(f"GROWN: RATCHET_CEILING_TOTAL {oc} -> {ceiling}")
    if grown:
        appr = str(baseline.get("ceiling_raise_approved", "")).strip()
        if appr and appr != str(old_b.get("ceiling_raise_approved", "")).strip():
            print(f"CEILING_RAISE_APPROVED: {appr}")
            return [], f"compared with {base_ref[:12]}: growth APPROVED ({'; '.join(grown)})"
        grown.append("no new top-level `ceiling_raise_approved: <reason>` in the baseline: a new reader may not enter the baseline "
                     "(pin it instead); an approved raise needs that explicit, reviewed marker")
    return grown, f"compared with {base_ref[:12]}"


def growth_guard(baseline: dict, ceiling: int, root: Path = REPO_ROOT, ref: str = "origin/main",
                 in_ci: Optional[bool] = None) -> Tuple[List[str], str]:
    """The growth guard as CI runs it: under CI (GITHUB_ACTIONS=true) the base is FETCHED here (`git fetch --depth=1 origin main`) and a base that
    cannot be fetched is a FAILURE, never a skip; outside CI an absent ref is a stated skip."""
    if in_ci is None:
        in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if not ensure_ref(ref, root, fetch=in_ci):
        if in_ci:
            return [f"GROWTH GUARD CANNOT RUN: {ref} could not be fetched under CI; the ratchet cannot be verified against the base "
                    f"(fix the checkout/fetch, do not skip)"], "base unavailable under CI"
        return [], f"skipped: {ref} not available locally"
    return against_ref(baseline, ref, root, ceiling)


def emit_baseline(sites: Sequence[Site]) -> dict:
    grouped: "OrderedDict[str, dict]" = OrderedDict()
    for s in unpinned(sites):
        e = grouped.setdefault(s.key, {"file": s.file, "anchor": s.anchor, "count": 0, "lines_at_rollout": [], "owner": "", "note": ""})
        e["count"] += 1
        e["lines_at_rollout"].append(s.line)
    return {"entries": list(grouped.values()), "retired": []}


# ------------------------------------------------------------------------------------------- self-test
def run_self_test() -> int:
    ok = True
    for lang, ext in (("py", ".py"), ("ts", ".ts"), ("sql", ".sql")):
        for kind, want_unpinned in (("pass", False), ("fail", True)):
            for p in sorted((FIXTURE_DIR / kind).glob(f"*{ext}")):
                found = unpinned(scan_text(p.read_text(encoding="utf-8"), p.name, lang))
                good = bool(found) if want_unpinned else not found
                if not good:
                    ok = False
                    print(f"SELF-TEST FAIL: {kind}/{p.name}: expected {'a flagged unpinned read' if want_unpinned else 'no unpinned read'}, "
                          f"got {[(s.line, s.reason) for s in found] or 'none'}")
    for kind in ("pass", "fail"):
        for ext in (".py", ".ts", ".sql"):
            if not list((FIXTURE_DIR / kind).glob(f"*{ext}")):
                ok = False
                print(f"SELF-TEST FAIL: no {kind} fixture for {ext}")
    s1 = Site("a.py", 1, "f", "x", False, "r")
    ent = {"file": "a.py", "anchor": "f", "count": 1, "note": "n", "owner": "o"}
    cases = [   # (name, sites, baseline, ceiling, expected rule prefix or None for clean)
        ("clean", [s1], {"entries": [ent], "retired": []}, 1, None),
        ("new reader", [s1, Site("b.py", 1, "g", "x", False, "r")], {"entries": [ent], "retired": []}, 1, "R1"),
        ("stale entry", [], {"entries": [ent], "retired": []}, 1, "R2"),
        ("partial shrink not lowered", [s1], {"entries": [dict(ent, count=2)], "retired": []}, 2, "R2"),
        ("retired comes back", [s1], {"entries": [], "retired": [{"file": "a.py", "anchor": "f"}]}, 0, "R3"),
        ("ceiling raised", [s1], {"entries": [ent], "retired": []}, 2, "R4"),
        ("no note", [s1], {"entries": [dict(ent, note="")], "retired": []}, 1, "R5"),
        ("no owner", [s1], {"entries": [dict(ent, owner="")], "retired": []}, 1, "R5"),
    ]
    for name, sites, base, ceil, prefix in cases:
        errs = ratchet(sites, base, ceil)
        good = (not errs) if prefix is None else any(e.startswith(prefix) for e in errs)
        if not good:
            ok = False
            print(f"SELF-TEST FAIL: ratchet case '{name}': expected {prefix or 'clean'}, got {errs or 'clean'}")
    print("self-test: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------- CLI
def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="reader-pin lint for the ephemeris_daily node series, with a ratchet")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-baseline", action="store_true", help="print a draft baseline (initial rollout or a shrink; review by hand)")
    ap.add_argument("--against", metavar="GIT_REF", help="also fail if the baseline grew relative to this ref (merge-base)")
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
        e2, note = against_ref(baseline, args.against, root, RATCHET_CEILING_TOTAL)
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
