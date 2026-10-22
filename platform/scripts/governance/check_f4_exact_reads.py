#!/usr/bin/env python3
"""check_f4_exact_reads.py — SR-F4-STORE-EXACT amend-1 guard: a REAL column is read as float8, never as the driver's default text.

The defect class. PostgreSQL stores `REAL` (float4). The driver's default read of a REAL is the SHORTEST DECIMAL that round-trips the float4 (1.9420573 for the stored
1.94205725…), a double that can sit up to half a float4 spacing away from the number the database holds. A verifier that compares such a read against an independent
re-derivation inside a one-half-spacing tolerance (`window_solver_check._f4_tol`) stacks a second half-spacing on the builder's own rounding and reads a correct store
as a disagreement (PRETR-early D-C: three `property_acquisition` P3 windows). `col::float8` is an exact widening; it loosens nothing.

What it flags. In every non-test Python source under the roots below, each SQL string (a literal, an implicit/`+` concatenation or an f-string) that touches a
`ka_gochara_*` table with REAL columns (`REAL_COLUMNS`) and whose SELECT LIST reads such a column without `::float8` / `::double precision` / `float4send(`.
A column used only as a NULL test (`score IS NOT NULL`) or only in WHERE/ON/GROUP/ORDER is not a value read and is not flagged. A `*` / `alias.*` select-list is flagged
unless every REAL column of the touched tables is re-selected as `col::float8 AS col` after it. A bare select-list FRAGMENT constant (`"w.score, w.severity, …"`
that a query assembles) is checked the same way.

Whole-row JSON reads (`to_jsonb(t)`) are the registry digest's PREIMAGE (compared for byte equality with the database's own digest, and pinned by seals); they are not value reads
and are not flagged.

Exemptions are NAMED, each with the reason it is not a lossy verifier compare (`EXEMPT`); an exemption that no longer matches anything FAILS the run (a stale
exemption is a signal with no detector behind it — root CLAUDE.md §N.8). The set of REAL columns itself is re-derived from the applied migrations by the test
(`declared_real_columns`), so a new REAL column cannot be added without the guard learning of it.

Usage:  python platform/scripts/governance/check_f4_exact_reads.py [--repo-root DIR]      exit 0 = clean, 1 = violations
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# table -> its REAL (float4) columns. Re-derived from the migrations by `declared_real_columns` in the test.
REAL_COLUMNS: dict[str, frozenset[str]] = {
    "ka_gochara_eval_window": frozenset({"score", "evidence_for", "evidence_against", "severity", "objective_value"}),
    "ka_gochara_relationship_record": frozenset({"evidence_for_occurrence", "evidence_against_occurrence", "severity"}),
    "ka_gochara_contact": frozenset({"delta_lambda", "delta_t"}),
    "ka_gochara_sky_event": frozenset({"delta_lambda", "delta_t"}),
    "ka_gochara_near_miss": frozenset({"delta_t"}),
    "ka_gochara_factor": frozenset({"range_lower", "range_upper"}),
}

# directories (relative to the repo root) whose non-test Python is scanned.
ROOTS = (
    "platform/python-sidecar/services",
    "platform/python-sidecar/scripts",
    "platform/python-sidecar/pipeline",
    "platform/scripts",
)

# (path suffix, needle that must occur in the SQL, why this read is not a lossy verifier compare). A match exempts the whole statement.
EXEMPT: tuple[tuple[str, str, str], ...] = (
    ("services/gochara_kernel/window_gate.py", "r.evidence_for_occurrence::text",
     "digest PREIMAGE, byte-equal to migration 1240 `ka_gochara_eval_window_inputs_digest`, which prints the REAL as the database's own text (an injective encoding of the "
     "float4, compared only for equality with that digest; the migration is applied and cannot be edited)"),
    ("services/gochara_kernel/window_gate.py", "c.delta_lambda::text",
     "digest PREIMAGE of the contact fields, byte-equal to migration 1240's `ka_gochara_eval_window_inputs_digest` (same reason)"),
    ("services/gochara_kernel/measuring_capture.py", "SELECT r.*",
     "golden CAPTURE: `golden_record` keeps only the natural-key / support fields; no record REAL value enters the pinned golden bundle"),
    ("scripts/kala_gochara_cutover/j4d_slice_qualify.py", "SELECT r.*",
     "slice CAPTURE (same as the measuring capture): no record REAL value enters the pinned golden"),
    ("services/gochara_kernel/measuring_capture.py", "c.delta_lambda",
     "golden CAPTURE: contact rows (delta_lambda as the driver reads it) are hashed into the pinned golden bundle; casting would change pinned bytes (goldens are not re-pinned)"),
    ("scripts/kala_gochara_cutover/j4d_slice_qualify.py", "c.delta_lambda",
     "slice CAPTURE in the golden's own canonical form (measuring_capture): the same pinned bytes as the measuring capture"),
    ("services/gochara_kernel/record_store.py", "t_in, t_out, t_exact, solver_method, delta_lambda, delta_t, precision_regime, coverage",
     "BUILDER write-then-read-back: compared by `_contact_row_diffs` after BOTH sides are rounded to float32 (`_as_float4`), which maps the shortest decimal back to the stored float4"),
    ("services/gochara_kernel/record_store.py", "FROM public.ka_gochara_sky_event",
     "BUILDER input: the sign-ingress crossings the builder reads to build its own contacts; no verifier compares it (ruling: the builder is unchanged)"),
    ("services/gochara_kernel/substrate.py", "FROM public.ka_gochara_sky_event",
     "BUILDER substrate store: reads back the sky events it wrote; no verifier compares it (ruling: the builder is unchanged)"),
    ("services/gochara_eval/dump_extract.py", "w.evidence_for AS si",
     "the Stage-1 freeze records this EXACT extract command (SI addendum v1.3 §5); it feeds the qualification report's ordering, not a verifier tolerance"),
)

_TABLE_RE = re.compile(r"\b(" + "|".join(REAL_COLUMNS) + r")\b")
_CAST_OK = re.compile(r"\s*::\s*(float8|double\s+precision)\b", re.I)
_NULL_TEST = re.compile(r"\s*IS\s+(NOT\s+)?NULL\b", re.I)
_SELECT_RE = re.compile(r"\bSELECT\b", re.I)
_FROM_RE = re.compile(r"\bFROM\b", re.I)
_FRAGMENT_RE = re.compile(r"^[\s\w.,:()'\"]+$")


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    column: str
    reason: str
    sql: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.reason} ({self.column}) in: {' '.join(self.sql.split())[:160]}"


def declared_real_columns(migrations_dir: Path) -> dict[str, frozenset[str]]:
    """The (ka_gochara_* table -> REAL columns) the migrations declare: `col REAL` lines of a CREATE TABLE, and `ADD COLUMN col REAL` of an ALTER TABLE."""
    found: dict[str, set[str]] = {}
    for f in sorted(Path(migrations_dir).glob("*.sql")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "ka_gochara_" not in text:
            continue
        table = None
        for raw in text.splitlines():
            line = raw.split("--", 1)[0]
            m = re.search(r"\b(?:CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?|ALTER\s+TABLE(?:\s+ONLY)?(?:\s+IF\s+EXISTS)?)\s+(?:public\.)?(\w+)", line, re.I)
            if m:
                table = m.group(1)
            c = re.match(r"\s*(?:ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?)?(\w+)\s+(?:REAL|FLOAT4)\b", line, re.I)
            if c and table and table.startswith("ka_gochara_") and c.group(1).upper() not in ("ADD", "ALTER", "CREATE"):
                found.setdefault(table, set()).add(c.group(1))
    return {t: frozenset(v) for t, v in found.items()}


def _flatten(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _flatten(node.left), _flatten(node.right)
        if a is None and b is None:
            return None
        return (a if a is not None else " ") + (b if b is not None else " ")
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else " " for v in node.values)
    return None


def _sql_strings(tree: ast.AST):
    """(line, text) of every maximal string expression that is not a docstring / bare expression statement."""
    inner: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            inner.update((id(n.left), id(n.right)))
        elif isinstance(n, ast.JoinedStr):
            inner.update(id(v) for v in n.values)
        elif isinstance(n, ast.Expr):
            inner.add(id(n.value))
    for n in ast.walk(tree):
        if id(n) in inner:
            continue
        text = _flatten(n)
        if text is not None:
            yield n.lineno, text


def _mask_literals(sql: str) -> str:
    """Blank the contents of '...' string literals (keeps offsets), so `-> 'score'` or a quoted word is never read as a column."""
    return re.sub(r"'(?:[^']|'')*'", lambda m: "'" + " " * (len(m.group(0)) - 2) + "'", sql)


def _select_lists(sql: str) -> list[tuple[str, str]]:
    """(select list, the rest of that SELECT's own scope) for every SELECT in `sql`: the list runs from SELECT to the FROM at the same paren depth, the scope from there to
    the closing paren that ends the SELECT (or the end of the string)."""
    masked = _mask_literals(sql)
    depth_at = []
    d = 0
    for ch in masked:
        if ch == "(":
            d += 1
        depth_at.append(d)
        if ch == ")":
            d -= 1
    out = []
    for m in _SELECT_RE.finditer(masked):
        start, depth = m.end(), depth_at[m.start()]
        end = len(masked)
        for f in _FROM_RE.finditer(masked, start):
            if depth_at[f.start()] == depth:
                end = f.start()
                break
        # a closing paren below the SELECT's depth ends the list too (a SELECT with no FROM inside a subquery)
        for i in range(start, end):
            if depth_at[i] < depth:
                end = i
                break
        scope_end = next((i for i in range(end, len(masked)) if depth_at[i] < depth), len(masked))
        out.append((masked[start:end], masked[end:scope_end]))
    return out


_STAR_ITEM = re.compile(r"^\s*(?:DISTINCT\s+)?(?:\w+\.)?\*\s*$", re.I)


def _items(lst: str) -> list[str]:
    """The select-list split at its top-level commas."""
    items, depth, cur = [], 0, []
    for ch in lst:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            items.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    items.append("".join(cur))
    return items


def _is_value_read(lst: str, col: str, m: re.Match) -> bool:
    before = lst[:m.start()]
    after = lst[m.end():]
    if re.search(r"\bAS\s+$", before, re.I):           # an output alias, not a column read
        return False
    if re.search(r"float4send\s*\(\s*(?:\w+\.)?$", before, re.I):
        return False
    if _CAST_OK.match(after):
        return False
    if _NULL_TEST.match(after):
        return False
    return True


def _violations_in_list(lst: str, scope: str, cols: frozenset[str], tables: set[str]):
    for col in sorted(cols):
        for m in re.finditer(r"(?<![\w])(?:\w+\.)?" + re.escape(col) + r"\b(?!\s*\()", lst):
            if _is_value_read(lst, col, m):
                yield col, "REAL column read without ::float8"
    from_tables = {m.group(1) for m in _TABLE_RE.finditer(scope)} or (tables if not scope else set())
    if from_tables and any(_STAR_ITEM.match(item) for item in _items(lst)):
        star_cols = frozenset().union(*(REAL_COLUMNS[t] for t in from_tables))
        missing = sorted(c for c in star_cols if not re.search(r"\b" + re.escape(c) + r"\s*::\s*(?:float8|double\s+precision)\s+AS\s+" + re.escape(c) + r"\b", lst, re.I))
        if missing:
            yield "*", f"star select-list reads REAL column(s) {', '.join(missing)} as text (re-select each as `col::float8 AS col`)"


def check_python_source(src: str, relpath: str, *, exempt=EXEMPT) -> tuple[list[Violation], set[int]]:
    """(violations, indexes into `exempt` that matched something) for one source file."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], set()
    file_tables = {t for t in REAL_COLUMNS if re.search(r"\b" + t + r"\b", src)}
    out: list[Violation] = []
    used: set[int] = set()
    for line, text in _sql_strings(tree):
        tables = {m.group(1) for m in _TABLE_RE.finditer(text)}
        if _SELECT_RE.search(text) and _FROM_RE.search(text):
            if not tables:
                continue
            lists = _select_lists(text)
        elif file_tables and _FRAGMENT_RE.match(text) and "," in text and re.search(r"\b\w+\.\w+", text) and not re.search(r"\b(WHERE|JOIN|ORDER|GROUP)\b", text, re.I):
            tables, lists = set(file_tables), [(_mask_literals(text), "")]      # a select-list fragment a query assembles
        else:
            continue
        cols = frozenset().union(*(REAL_COLUMNS[t] for t in tables))
        found = [(c, why) for lst, scope in lists for c, why in _violations_in_list(lst, scope, cols, tables)]
        if not found:
            continue
        hit = [i for i, (suffix, needle, _why) in enumerate(exempt) if relpath.endswith(suffix) and needle in text]
        if hit:
            used.update(hit)
            continue
        out.extend(Violation(relpath, line, c, why, text) for c, why in found)
    return out, used


def scan_tree(repo_root: Path, *, exempt=EXEMPT) -> tuple[list[Violation], list[str]]:
    """(violations, stale exemptions) over the scanned roots of `repo_root`."""
    violations: list[Violation] = []
    used: set[int] = set()
    for root in ROOTS:
        base = Path(repo_root) / root
        for p in sorted(base.rglob("*.py")) if base.is_dir() else []:
            rel = p.relative_to(repo_root).as_posix()
            parts = set(rel.split("/"))
            if parts & {"tests", "__tests__", "__pycache__"} or p.name.startswith(("test_", "conftest")):
                continue
            v, u = check_python_source(p.read_text(encoding="utf-8", errors="replace"), rel, exempt=exempt)
            violations.extend(v)
            used.update(u)
    stale = [f"{suffix} / {needle!r}" for i, (suffix, needle, _why) in enumerate(exempt) if i not in used]
    return violations, stale


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args(argv)
    violations, stale = scan_tree(Path(args.repo_root))
    for v in violations:
        print(f"F4-LOSSY-READ {v}")
    for s in stale:
        print(f"F4-STALE-EXEMPTION {s}")
    if violations or stale:
        print(f"check_f4_exact_reads: {len(violations)} lossy REAL read(s), {len(stale)} stale exemption(s)")
        return 1
    print("check_f4_exact_reads: every REAL read on the gochara paths is ::float8 (or a named exemption)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
