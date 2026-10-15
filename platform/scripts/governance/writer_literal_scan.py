"""Static scan of a writer's source for the WRITE PATHS to declared prose columns (Null.schema_default / Null.blank_rows).

E5.7 Worker E (SS N-150 R7: a certificate PASS on Null.* needs a real PASS path). The census caps every Null PASS at PARTIAL
because "writer literal fallbacks and constant columns are not measured". This module measures them, from SOURCE ONLY (it reads
nothing from a database): for each declared prose entry it finds every statement in the writer's resolved scope that writes
the column (INSERT column list, UPDATE / ON CONFLICT DO UPDATE SET), follows the VALUE written back to its source expression
(a named parameter %(k)s -> every assignment to the key k in the scope; a positional %s -> the element of the literal parameter
tuple at the bound execute call; an SQL expression -> the expression itself) and classifies each source expression:

  * a literal fallback: `x or 'N/A'`, `d.get(k, 'none')`, `getattr(o, a, '-')`, `x if x else 'unknown'`, SQL `COALESCE(x, 'n/a')`;
  * a constant write: the column is written a string / number literal (a constant column);
  * unresolved: a source the scan cannot follow (dynamic SQL, `INSERT` without a column list, a parameter with no caller in the
    scope, a callee outside the scope, dynamic row construction that could supply the key). Never read as clean.

`v` is PASS only when EVERY entry has at least one found write path, no problem and nothing unresolved; PARTIAL otherwise
(naming each problem and each unresolved path); NO_DETECTOR when there is no writer source to scan. It never FAILs: a static
scan's finding is evidence for a human, not a verdict on the data (the data-level FAIL stays with Null.schema_default /
Null.blank_rows themselves). The placeholder vocabulary is the census's own (`is_placeholder` is injected: the Python port of
`_ldgr_lacking_text`, so there is ONE definition of "placeholder").

Pure functions over ast units; the census passes `units` (from `_delegation_scope`) and `sql_texts` (its own `_sql_texts`).
"""
from __future__ import annotations

import ast
import re

MAX_DEPTH = 7
_PASS_ROLE = frozenset({"str", "repr", "strip", "lstrip", "rstrip", "lower", "upper", "title", "capitalize", "casefold", "encode", "decode", "replace",
                        "removeprefix", "removesuffix", "translate", "normalize", "copy", "deepcopy"})
_SQLISH = re.compile(r"\s*(?:INSERT|UPDATE|SELECT|WITH|CREATE|ALTER|DELETE|COMMENT|COPY|DROP|SET|SAVEPOINT)\b", re.I)
_ENTRY_POINTS = frozenset({"run", "run_substep", "plan_substeps"})
_BUILTIN_PURE = frozenset({
    "str", "repr", "int", "float", "round", "len", "sorted", "list", "tuple", "set", "frozenset", "sum", "min", "max", "abs", "bool",
    "dumps", "loads", "isoformat", "strftime", "format", "join", "strip", "lstrip", "rstrip", "lower", "upper", "title", "capitalize",
    "casefold", "replace", "split", "splitlines", "encode", "decode", "ljust", "rjust", "center", "zfill", "removeprefix",
    "removesuffix", "translate", "format_map", "partition", "rpartition", "startswith", "endswith", "count", "index", "find",
    "fetchone", "fetchall", "fetchmany", "fetchval", "scalar", "execute", "cursor", "keys", "values", "items", "copy", "deepcopy",
    "enumerate", "zip", "dict", "range", "reversed", "any", "all", "isinstance", "type", "id", "hash", "digest", "hexdigest", "sha256", "md5",
    "uuid4", "now", "utcnow", "today", "time", "monotonic", "perf_counter", "append", "extend", "get_json", "normalize", "sub", "match",
    "search", "findall", "capitalize", "swapcase", "isdigit", "isalpha", "isupper", "islower", "chr", "ord", "ascii", "bytes",
    "bytearray", "memoryview", "decimal", "Decimal", "date", "datetime", "timedelta", "float_", "math", "sqrt", "floor", "ceil", "log",
})
_DEFAULT_ARG_METHODS = {"get": 1, "pop": 1, "setdefault": 1, "next": 1, "getattr": 2, "coalesce": 1, "nvl": 1, "ifnull": 1, "get_or": 1, "or_default": 1,
                        "dict_get": 1, "getenv": 1}
_SQL_FALLBACK_FN = re.compile(r"\b(?:COALESCE|NULLIF|IFNULL|NVL|CASE)\b", re.I)
_SQL_PURE_LITERAL = re.compile(r"\s*(?:E)?'(?:[^']|'')*'\s*(?:::\s*[A-Za-z_][\w ]*(?:\[\])?)?\s*", re.I)
_SQL_NUM_LITERAL = re.compile(r"\s*-?\d+(?:\.\d+)?\s*(?:::\s*[A-Za-z_][\w ]*)?\s*")
_SQL_STR_LITERAL = re.compile(r"'((?:[^']|'')*)'")
_PH_NAMED = re.compile(r"%\((\w+)\)s")
_PH_ANY = re.compile(r"%\((\w+)\)s|(?<!%)%s")
_PIECE_PH = re.compile(r"\s*(?:%\((\w+)\)s|%s)\s*(?:::\s*[A-Za-z_][\w ]*(?:\[\])?)?\s*")
_INSERT = re.compile(r"\bINSERT\s+INTO\s+(?:ONLY\s+)?(?:public\.)?\"?([A-Za-z_][A-Za-z_0-9]*|\{\?\})\"?", re.I)
_UPDATE = re.compile(r"\bUPDATE\s+(?:ONLY\s+)?(?:public\.)?\"?([A-Za-z_][A-Za-z_0-9]*|\{\?\})\"?(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?\s+SET\b", re.I)
_COPY = re.compile(r"\bCOPY\s+(?:public\.)?\"?([A-Za-z_][A-Za-z_0-9]*|\{\?\})\"?", re.I)
_DO_UPDATE = re.compile(r"\bDO\s+UPDATE\s+SET\b", re.I)
_EXEC_NAMES = ("execute", "executemany", "execute_values", "execute_batch")


def blank_sql_comments(s: str) -> str:
    """`s` with every SQL comment (`-- ...` to end of line, `/* ... */`) replaced by spaces of the same length, so offsets and line positions are unchanged. A comment is never read as SQL:
    an apostrophe in prose (`the writer's own value`) opens a string that swallows the rest of a column list, and a comma or `%s` in a comment shifts a split. Quote aware: a `--` or `/*`
    inside a single-quoted string (`''` is an escaped quote; in an E'...' string a backslash escapes the next character, so `E'it\\'s -- text'` is one string), a double-quoted identifier or a
    dollar-quoted string (`$$ ... $$`, `$tag$ ... $tag$`) is text, not a comment."""
    out, j, n = [], 0, len(s)
    while j < n:
        ch = s[j]
        if ch == "'" or ch == '"':
            escape = ch == "'" and j > 0 and s[j - 1] in "Ee" and (j < 2 or not (s[j - 2].isalnum() or s[j - 2] == "_"))      # an E'...' string: backslash escapes
            k = j + 1
            while k < n:
                if escape and s[k] == "\\":
                    k += 2
                    continue
                if s[k] == ch:
                    if k + 1 < n and s[k + 1] == ch:
                        k += 2
                        continue
                    break
                k += 1
            out.append(s[j:k + 1])
            j = k + 1
        elif ch == "$":
            m = _DOLLAR_TAG.match(s, j)
            if m is not None and (j == 0 or not (s[j - 1].isalnum() or s[j - 1] == "_")):
                tag = m.group(0)
                k = s.find(tag, m.end())
                end = n if k < 0 else k + len(tag)
                prev = re.search(r"([A-Za-z_]+)\s*$", s[:j])
                if prev is not None and prev.group(1).upper() in ("DO", "AS"):
                    # a CODE body (`DO $$ ... $$`, `CREATE FUNCTION ... AS $$ ... $$`), the same test blank_sql_literals uses: its comments are comments (a commented statement is no statement)
                    out.append(tag + blank_sql_comments(s[m.end():end - len(tag) if k >= 0 else end]) + (tag if k >= 0 else ""))
                else:
                    out.append(s[j:end])                   # a dollar-quoted STRING is text: a `--` or `/*` inside it is not a comment
                j = end
            else:
                out.append(ch)
                j += 1
        elif ch == "-" and s.startswith("--", j):
            k = s.find("\n", j)
            k = n if k < 0 else k
            out.append(" " * (k - j))
            j = k
        elif ch == "/" and s.startswith("/*", j):
            depth, k = 1, j + 2                              # PostgreSQL block comments NEST: `/* a /* b */ still a comment */`
            while k < n and depth:
                if s.startswith("/*", k):
                    depth += 1
                    k += 2
                elif s.startswith("*/", k):
                    depth -= 1
                    k += 2
                else:
                    k += 1
            out.append("".join(c if c == "\n" else " " for c in s[j:k]))
            j = k
        else:
            out.append(ch)
            j += 1
    return "".join(out)


_DOLLAR_TAG = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$")


def blank_sql_literals(s: str) -> str:
    """`s` with the CONTENT of every single-quoted string literal (`''` escapes honoured) and dollar-quoted STRING (`$$...$$`, `$tag$...$tag$`) replaced by spaces of the same length (newlines kept),
    so a statement keyword that only appears INSIDE text (`SELECT 'INSERT INTO t'`, `SELECT $$CREATE TABLE t$$`, `RAISE NOTICE 'CREATE TABLE t'`) is not read as a statement. A dollar-quoted body that is CODE
    (it follows `DO` or `AS`: a DO block, a function body) keeps its statements, with its own string literals blanked: the declared migrations 630 / 631 UPDATE their table inside DO blocks. Call it AFTER `blank_sql_comments`
    (a comment marker inside a string is text; an apostrophe inside a comment must already be gone). Double-quoted identifiers are kept as they are. An unterminated literal is blanked to the end."""
    out, j, n = [], 0, len(s)
    while j < n:
        ch = s[j]
        if ch == '"':
            k = s.find('"', j + 1)
            k = n - 1 if k < 0 else k
            out.append(s[j:k + 1])
            j = k + 1
        elif ch == "'":
            escape = j > 0 and s[j - 1] in "Ee" and (j < 2 or not (s[j - 2].isalnum() or s[j - 2] == "_"))      # an E'...' string: a backslash escapes the next character
            k = j + 1
            while k < n:
                if escape and s[k] == "\\":
                    k += 2
                    continue
                if s[k] == "'":
                    if k + 1 < n and s[k + 1] == "'":
                        k += 2
                        continue
                    break
                k += 1
            body = s[j + 1:k]
            out.append("'" + "".join(c if c == "\n" else " " for c in body) + ("'" if k < n else ""))
            j = k + 1
        elif ch == "$":
            m = _DOLLAR_TAG.match(s, j)
            if m is not None and (j == 0 or not (s[j - 1].isalnum() or s[j - 1] == "_")):
                tag = m.group(0)
                k = s.find(tag, m.end())
                end = n if k < 0 else k + len(tag)
                body = s[m.end():end - len(tag) if k >= 0 else end]
                prev = re.search(r"([A-Za-z_]+)\s*$", s[:j])
                if prev is not None and prev.group(1).upper() in ("DO", "AS"):
                    # a CODE body (`DO $$ ... $$`, `CREATE FUNCTION ... AS $$ ... $$`): its statements are statements, but a string literal INSIDE it is still text
                    out.append(tag + blank_sql_literals(body) + (tag if k >= 0 else ""))
                else:
                    out.append(tag + "".join(c if c == "\n" else " " for c in body) + (tag if k >= 0 else ""))      # a dollar-quoted STRING: all text
                j = end
            else:
                out.append(ch)
                j += 1
        else:
            out.append(ch)
            j += 1
    return "".join(out)


def _balanced(s: str, i: int):
    """(inner, end) of the parenthesised group opening at s[i] == '(' (quote aware), or None when unbalanced."""
    depth, j, q = 0, i, False
    while j < len(s):
        ch = s[j]
        if q:
            if ch == "'":
                if j + 1 < len(s) and s[j + 1] == "'":
                    j += 1
                else:
                    q = False
        elif ch == "'":
            q = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j
        j += 1
    return None


def _split_top(s: str, base: int = 0):
    """[(piece, absolute_start)] split at depth-0 commas (parentheses and single quotes respected; '' is an escaped quote)."""
    out, depth, q, start, j = [], 0, False, 0, 0
    while j < len(s):
        ch = s[j]
        if q:
            if ch == "'":
                if j + 1 < len(s) and s[j + 1] == "'":
                    j += 1
                else:
                    q = False
        elif ch == "'":
            q = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append((s[start:j], base + start))
            start = j + 1
        j += 1
    out.append((s[start:], base + start))
    return out


def _top_keyword(s: str, words):
    """The index of the first depth-0 occurrence of one of `words` (whole word, case-insensitive) in s, else -1."""
    depth, q = 0, False
    up = s.upper()
    j = 0
    while j < len(s):
        ch = s[j]
        if q:
            if ch == "'":
                if j + 1 < len(s) and s[j + 1] == "'":
                    j += 1
                else:
                    q = False
        elif ch == "'":
            q = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and (j == 0 or not (s[j - 1].isalnum() or s[j - 1] == "_")):
            for w in words:
                if up.startswith(w, j) and (j + len(w) >= len(s) or not (s[j + len(w)].isalnum() or s[j + len(w)] == "_")):
                    return j
        j += 1
    return -1


def sql_writes(text: str, tables):
    """The column writes one statement text makes into `tables` (lower-case names): a list of dicts
    dict(table, column, piece, start) (`piece` = the SQL expression written, `start` its offset in `text`), plus `issues`
    (statements writing a named table the scan cannot read the columns of: no column list, a dynamic table / column list, COPY)."""
    writes, issues = [], []
    tset = {t.lower() for t in tables}
    for m in _COPY.finditer(text):
        t = m.group(1).lower()
        if t == "{?}" or t in tset:
            issues.append(f"COPY into {t}: the values written are not in the statement text")
    for m in _INSERT.finditer(text):
        t = m.group(1).lower()
        if t == "{?}":
            issues.append("INSERT into a table the scan cannot name (dynamic SQL)")
            continue
        if t not in tset:
            continue
        i = m.end()
        while i < len(text) and text[i].isspace():
            i += 1
        cols = None
        if i < len(text) and text[i] == "(":
            g = _balanced(text, i)
            if g is None:
                issues.append(f"INSERT into {t}: unbalanced column list")
                continue
            inner, end = g
            if "{?}" in inner:
                issues.append(f"INSERT into {t}: a dynamic column list the scan cannot read")
                continue
            cols = [c.strip().strip('"').lower() for c in inner.split(",")]
            i = end + 1
        else:
            issues.append(f"INSERT into {t} has no column list: the column of each value is its position in the table, not in the statement")
            continue
        rest = text[i:]
        stripped = rest.lstrip()
        off = i + (len(rest) - len(stripped))
        up = stripped.upper()
        if up.startswith("VALUES"):
            j = off + len("VALUES")
            pos = j
            any_group = False
            while True:
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                if pos < len(text) and text[pos] == "(":
                    g = _balanced(text, pos)
                    if g is None:
                        issues.append(f"INSERT into {t}: unbalanced VALUES group")
                        break
                    inner, end = g
                    pieces = _split_top(inner, pos + 1)
                    if len(pieces) != len(cols):
                        issues.append(f"INSERT into {t}: {len(cols)} column(s) but {len(pieces)} value(s) in a VALUES group")
                        break
                    for c, (pc, st) in zip(cols, pieces):
                        writes.append(dict(table=t, column=c, piece=pc, start=st, cols=list(cols)))
                    any_group = True
                    pos = end + 1
                    while pos < len(text) and text[pos].isspace():
                        pos += 1
                    if pos < len(text) and text[pos] == ",":
                        pos += 1
                        continue
                    break
                break
            if not any_group:
                issues.append(f"INSERT into {t}: VALUES without a parenthesised group (a bulk-values template such as execute_values): the per-column values are not in the statement")
        elif up.startswith("SELECT") or up.startswith("WITH") or up.startswith("("):
            body = stripped
            sel = body[len("SELECT"):] if up.startswith("SELECT") else None
            if sel is None:
                issues.append(f"INSERT into {t}: a WITH / parenthesised source the scan cannot position-map")
            else:
                k = _top_keyword(sel, ("FROM", "ON CONFLICT", "RETURNING"))
                sel_list = sel if k < 0 else sel[:k]
                pieces = _split_top(sel_list, off + len("SELECT"))
                if len(pieces) != len(cols):
                    issues.append(f"INSERT into {t}: {len(cols)} column(s) but {len(pieces)} select-list item(s)")
                else:
                    for c, (pc, st) in zip(cols, pieces):
                        writes.append(dict(table=t, column=c, piece=re.sub(r"^\s*DISTINCT\s+", "", pc, flags=re.I), start=st, select=True))
        else:
            issues.append(f"INSERT into {t}: an INSERT form the scan does not read (DEFAULT VALUES / other)")
        # ON CONFLICT ... DO UPDATE SET c = expr
        for dm in _DO_UPDATE.finditer(text, i):
            tail = text[dm.end():]
            k = _top_keyword(tail, ("WHERE", "RETURNING"))
            seg = tail if k < 0 else tail[:k]
            for pc, st in _split_top(seg, dm.end()):
                if "=" in pc:
                    lhs, rhs = pc.split("=", 1)
                    writes.append(dict(table=t, column=lhs.strip().strip('"').lower(), piece=rhs, start=st + len(lhs) + 1, update=True))
    for m in _UPDATE.finditer(text):
        t = m.group(1).lower()
        if t == "{?}":
            issues.append("UPDATE of a table the scan cannot name (dynamic SQL)")
            continue
        if t not in tset:
            continue
        tail = text[m.end():]
        k = _top_keyword(tail, ("WHERE", "FROM", "RETURNING"))
        seg = tail if k < 0 else tail[:k]
        if "{?}" in seg:
            issues.append(f"UPDATE {t}: a dynamic SET list the scan cannot read")
            continue
        for pc, st in _split_top(seg, m.end()):
            if "=" in pc:
                lhs, rhs = pc.split("=", 1)
                writes.append(dict(table=t, column=lhs.strip().strip('"').lower(), piece=rhs, start=st + len(lhs) + 1, update=True))
    return writes, issues


def _placeholders(text: str, start: int, end: int):
    """[(named key | None, positional index | None)] for the placeholders in text[start:end]; the positional index counts every %s / %(k)s before."""
    out = []
    for m in _PH_ANY.finditer(text):
        if m.start() >= start and m.end() <= end:
            idx = len(_PH_ANY.findall(text[:m.start()]))
            out.append((m.group(1), None if m.group(1) else idx))
    return out


def _is_string_node(n):
    return isinstance(n, (ast.Constant, ast.JoinedStr, ast.BinOp)) and getattr(n, "lineno", None) is not None


def _flat(n):
    """The text of a string made only of constants (and `+` / implicit concatenation); None otherwise (an f-string with a formatted value is None)."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.JoinedStr):
        if all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in n.values):
            return "".join(v.value for v in n.values)
        return None
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        a, b = _flat(n.left), _flat(n.right)
        return None if a is None or b is None else a + b
    return None


class _Scope:
    """Index over every ast node of the writer's resolved scope: parents, functions by name, assignments, call sites."""

    def __init__(self, units):
        self.units = units
        self.parent: dict[int, ast.AST] = {}
        self.unit_of: dict[int, dict] = {}
        self.funcs: dict[str, list] = {}
        self.calls: list = []
        self.nodes: list = []
        seen = set()
        for u in units:
            for root in u["nodes"]:
                for n in ast.walk(root):
                    if id(n) in seen:
                        continue
                    seen.add(id(n))
                    self.nodes.append(n)
                    self.unit_of[id(n)] = u
                    for c in ast.iter_child_nodes(n):
                        self.parent.setdefault(id(c), n)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.funcs.setdefault(n.name, []).append(n)
                    elif isinstance(n, ast.Call):
                        self.calls.append(n)
        self.attr_assigns: dict[str, list] = {}          # `self.X = v` / `cls.X = v` / `Obj.X = v`, and class-level `X = v`, by attribute name
        for n in self.nodes:
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Attribute):
                        self.attr_assigns.setdefault(t.attr, []).append(n.value)
            elif isinstance(n, ast.ClassDef):
                for st in n.body:
                    if isinstance(st, ast.Assign):
                        for t in st.targets:
                            if isinstance(t, ast.Name):
                                self.attr_assigns.setdefault(t.id, []).append(st.value)
                    elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.value is not None:
                        self.attr_assigns.setdefault(st.target.id, []).append(st.value)
        self.module_assigns: dict[str, list] = {}
        for u in units:
            for st in getattr(u["tree"], "body", []):
                if isinstance(st, ast.Assign):
                    for t in st.targets:
                        if isinstance(t, ast.Name):
                            self.module_assigns.setdefault(t.id, []).append(st.value)
                elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.value is not None:
                    self.module_assigns.setdefault(st.target.id, []).append(st.value)

    def where(self, n) -> str:
        u = self.unit_of.get(id(n))
        return f"{u['rel'] if u else '?'}:{getattr(n, 'lineno', 0)}"

    def enclosing(self, n):
        p = self.parent.get(id(n))
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            p = self.parent.get(id(p))
        return p

    def fn_nodes(self, fn):
        """Nodes of `fn` excluding nested function bodies."""
        out, todo = [], list(ast.iter_child_nodes(fn))
        while todo:
            n = todo.pop()
            out.append(n)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            todo.extend(ast.iter_child_nodes(n))
        return out

    # ---- opaque row construction -------------------------------------------------------------------------------
    def enumerated(self, k: str, rels=None):
        """Places where the key NAME `k` is used as a value that could drive a run-time key (a member of a literal list / tuple / set, a call argument, a plain assignment or return value, a word inside a
        non-SQL string such as a comma-separated column list). A key written only as a dict-display key, a subscript key, a comparison operand or inside SQL statements cannot be reached by a
        dynamically built key, so the dynamic-construction check (`opaque`) only matters when this list is non-empty. (A key assembled at run time from string fragments is not detected.)"""
        out = []
        word = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(k) + r"(?![A-Za-z0-9_])")
        for n in self.nodes:
            if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
                continue
            if rels is not None and (self.unit_of.get(id(n)) or {}).get("rel") not in rels:
                continue
            par = self.parent.get(id(n))
            if n.value == k:
                if isinstance(par, ast.Dict) and any(kk is n for kk in par.keys):
                    continue
                if isinstance(par, ast.Subscript) and par.slice is n:
                    continue
                if isinstance(par, (ast.Compare, ast.Expr)):
                    continue
                if (isinstance(par, ast.Call) and par.args and par.args[0] is n and isinstance(par.func, ast.Attribute) and par.func.attr in ("get", "pop")
                        and len(par.args) <= 2 and not par.keywords):
                    continue                                              # FORM-GAP: `row.get("k", "")` / `row.pop("k")` READ the key; they cannot make a run-time key appear in a row
                if isinstance(par, (ast.List, ast.Tuple, ast.Set)) and self._member_list_inert(par):
                    continue                                              # FORM-GAP: a literal column list that is only counted, joined into SQL text and used as a READ index
                out.append(f"{self.where(n)} the key name used as a value ({type(par).__name__})")
            elif word.search(n.value) and not _SQLISH.match(n.value) and not isinstance(par, ast.Expr):
                out.append(f"{self.where(n)} the key name inside a non-SQL string")
        return out

    # ---- FORM-GAP (detector limits #3218): a literal list of column names that can drive no run-time key ----
    _TEXT_ONLY_CALLEES = frozenset({"str", "repr", "len", "print", "format", "ascii"})

    def _loop_var_inert(self, loop, target_names) -> bool:
        """True when, inside the loop `loop`, every use of each loop variable only READS (an index `r[c]`, a comparison, text formatting): none of them is a store key, a dict-display key, or an argument to anything
        that could build a key."""
        body = list(loop.body) + list(getattr(loop, "orelse", []))
        for st in body:
            for n in ast.walk(st):
                if not (isinstance(n, ast.Name) and n.id in target_names):
                    continue
                if not isinstance(n.ctx, ast.Load):
                    return False
                par = self.parent.get(id(n))
                ok = ((isinstance(par, ast.Subscript) and par.slice is n and isinstance(par.ctx, ast.Load))
                      or isinstance(par, ast.Compare)
                      or isinstance(par, ast.FormattedValue)
                      or (isinstance(par, ast.Call) and any(a is n for a in par.args) and isinstance(par.func, ast.Name) and par.func.id in self._TEXT_ONLY_CALLEES)
                      or (isinstance(par, ast.Call) and any(a is n for a in par.args) and isinstance(par.func, ast.Attribute) and par.func.attr == "format"))
                if not ok:
                    return False
        return True

    def _member_list_inert(self, container) -> bool:
        """The literal list / tuple / set `container` is assigned to ONE name `L` (`_COLUMNS = [...]`) and every use of `L` in the scope is inert: `len(L)`, `", ".join(L)` (SQL text), or `for c in L:` whose loop
        variable only READS (`_loop_var_inert`). Any other use (passed on, zipped, unpacked, stored, iterated into a store) leaves the list a possible key source."""
        par = self.parent.get(id(container))
        if not (isinstance(par, ast.Assign) and len(par.targets) == 1 and isinstance(par.targets[0], ast.Name) and par.value is container):
            return False
        name = par.targets[0].id
        uses = [n for n in self.nodes if isinstance(n, ast.Name) and n.id == name and n is not par.targets[0]]
        if not uses or any(not isinstance(n.ctx, ast.Load) for n in uses):
            return False
        if sum(1 for n in self.nodes if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)) != 1:
            return False
        for n in uses:
            p = self.parent.get(id(n))
            if isinstance(p, ast.Call) and any(a is n for a in p.args) and isinstance(p.func, ast.Name) and p.func.id == "len":
                continue
            if (isinstance(p, ast.Call) and len(p.args) == 1 and p.args[0] is n and isinstance(p.func, ast.Attribute) and p.func.attr == "join"
                    and isinstance(p.func.value, ast.Constant) and isinstance(p.func.value.value, str)):
                continue
            if isinstance(p, (ast.For, ast.AsyncFor)) and p.iter is n:
                tn = {x.id for x in ast.walk(p.target) if isinstance(x, ast.Name)}
                if tn and self._loop_var_inert(p, tn):
                    continue
            return False
        return True


    def opaque(self, rels=None, key=None):
        """Constructs after which a dict key can come from somewhere the key-source search cannot see. `rels`: only constructs in these source files (the files that hold a source of the key or the statement): a
        dynamic construction in an unrelated helper module cannot be this row's key."""
        out = []
        if key is not None and not self.enumerated(key, rels):
            return out
        for n in self.nodes:
            if rels is not None and (self.unit_of.get(id(n)) or {}).get("rel") not in rels:
                continue
            if isinstance(n, ast.Dict) and any(k is None for k in n.keys):
                out.append(f"{self.where(n)} a dict display with a ** unpack")
            elif isinstance(n, ast.Dict) and any(k is not None and not (isinstance(k, ast.Constant) and isinstance(k.value, str)) for k in n.keys):
                out.append(f"{self.where(n)} a dict display with a non-literal key")
            elif isinstance(n, ast.DictComp):
                out.append(f"{self.where(n)} a dict comprehension")
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Subscript) and not (isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str)) \
                            and not isinstance(t.slice, (ast.Slice,)) and not isinstance(t.slice, ast.Constant) \
                            and not (isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "len"):
                        out.append(f"{self.where(n)} a subscript store with a non-literal key")
            elif isinstance(n, ast.Call):
                nm = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else None
                if nm == "dict" and (any(k.arg is None for k in n.keywords) or any(not isinstance(a, (ast.Name, ast.Dict)) for a in n.args)):
                    out.append(f"{self.where(n)} dict() built from a non-literal / unpacked mapping")
                elif nm == "update" and any(not isinstance(a, ast.Dict) for a in n.args):
                    out.append(f"{self.where(n)} .update() with a non-literal mapping")
                elif nm == "setattr":
                    out.append(f"{self.where(n)} setattr")
        return out

    def key_sources(self, k: str):
        """Every expression the scope assigns to the string key `k`: dict display entries, `x["k"] = e`, `dict(k=e)`, `.update(k=e)`, `.setdefault("k", e)`."""
        out = []
        for n in self.nodes:
            if isinstance(n, ast.Dict):
                for key, val in zip(n.keys, n.values):
                    if isinstance(key, ast.Constant) and key.value == k:
                        out.append(val)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value == k:
                        out.append(n.value)
            elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Subscript) and isinstance(n.target.slice, ast.Constant) and n.target.slice.value == k:
                out.append(n.value)
            elif isinstance(n, ast.Call):
                nm = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else None
                if nm in ("dict", "update"):
                    out += [kw.value for kw in n.keywords if kw.arg == k]
                if nm == "setdefault" and len(n.args) >= 2 and isinstance(n.args[0], ast.Constant) and n.args[0].value == k:
                    out.append(n.args[1])
        return out


class _Acc:
    def __init__(self):
        self.problems: list[dict] = []
        self.unresolved: list[str] = []
        self.sources = 0

    def problem(self, kind, where, text):
        d = dict(kind=kind, where=where, text=text)
        if d not in self.problems:
            self.problems.append(d)

    def unres(self, why):
        if why not in self.unresolved:
            self.unresolved.append(why)


class _PartAcc:
    """The accumulator used while following a FRAGMENT of a composed value (an f-string field, a `+` operand, a join argument): a placeholder-vocabulary fallback inside it is a real problem (the
    sentence reads `Graha: unknown`), but what the fragment is made of is not the column's value, so an unresolved fragment source is not a gap and a constant fragment is not a constant write."""

    def __init__(self, acc):
        self.acc = acc
        self.sources = 0

    @property
    def problems(self):
        return self.acc.problems

    def problem(self, kind, where, text):
        if kind == "literal_fallback":
            self.acc.problem(kind, where, text)

    def unres(self, why):
        if why.startswith("source chain deeper"):
            self.acc.unres(why)


class _Analyzer:
    def __init__(self, scope: _Scope, is_placeholder):
        self.s = scope
        self.ph = is_placeholder
        self.opaque = None

    def literal(self, v, n, acc, how):
        if isinstance(v, str):
            kind = "literal_fallback" if self.ph(v) else "constant_write"
            acc.problem(kind, self.s.where(n), f"{how}: {v!r}")
        elif v is None:
            return
        else:
            acc.problem("constant_write", self.s.where(n), f"{how}: {v!r}")

    def flag(self, v, n, acc, how, role):
        """A literal that stands in for a missing value: in the VALUE role any literal fallback / constant; in a fragment only a placeholder-vocabulary one."""
        if role == "value":
            self.literal(v, n, acc, how)
        elif isinstance(v, str) and self.ph(v):
            acc.problem("literal_fallback", self.s.where(n), f"{how}: {v!r}")

    _TERMINATORS = (".", "!", "?", "...", "\u2026")

    def _terminator_suffix(self, ifexp, lit, other) -> bool:
        """SS 2026-10-05 R-b, closed: the literal is a sentence TERMINATOR ('.', '!', '?', an ellipsis), it is the else/then branch of a conditional whose OTHER branch is also a plain string
        literal, and that conditional is the LAST operand of a `+` chain (the right operand of the chain's outermost Add, itself not an operand of another Add). Anything else (`x if x else "-"`,
        `"?"`/`"..."` beside a computed value, a conditional inside an f-string, in the middle of a chain, or a whole value) stays a finding."""
        if lit.value not in self._TERMINATORS or not (isinstance(other, ast.Constant) and isinstance(other.value, str)):
            return False
        par = self.s.parent.get(id(ifexp))
        if not (isinstance(par, ast.BinOp) and isinstance(par.op, ast.Add) and par.right is ifexp):
            return False
        top = self.s.parent.get(id(par))
        if isinstance(top, ast.BinOp) and isinstance(top.op, ast.Add):
            return False
        flat = _flat(par.left) if isinstance(par.left, (ast.Constant, ast.JoinedStr, ast.BinOp)) else None
        if flat is not None and not any(ch.isalnum() for ch in flat):
            return False                                  # `"" + ("." if m else "!")`: nothing precedes the terminator, the value IS a lone punctuation literal
        return True

    @staticmethod
    def _missing_test(test) -> bool:
        """The test of a conditional expression asks whether a value is missing / empty: `x`, `not x`, `x is None`, `x is not None`, `x == None`, `len(x) == 0`, `not x.y`, `x[...]`, `bool(x)`."""
        t = test
        while isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not):
            t = t.operand
        if isinstance(t, (ast.Name, ast.Attribute, ast.Subscript)):
            return True
        if isinstance(t, ast.Call):
            nm = t.func.id if isinstance(t.func, ast.Name) else t.func.attr if isinstance(t.func, ast.Attribute) else None
            return nm in ("bool", "len", "any", "all", "isinstance") and nm != "isinstance"
        if isinstance(t, ast.Compare) and len(t.ops) == 1:
            r = t.comparators[0]
            if isinstance(r, ast.Constant) and (r.value is None or r.value in (0, "", False)):
                return True
            if isinstance(t.left, ast.Call) and isinstance(t.left.func, ast.Name) and t.left.func.id == "len":
                return True
        return isinstance(t, ast.BoolOp) and all(_Analyzer._missing_test(v) for v in t.values)

    def expr(self, n, acc, depth=0, seen=None, role="value"):
        """role 'value': the expression IS the written value (a bare literal is a constant write). role 'part': a fragment of a composed value (a bare literal is a template piece)."""
        if role == "part" and not isinstance(acc, _PartAcc):
            acc = _PartAcc(acc)                      # a fragment: only a placeholder-vocabulary fallback inside it is a finding
        seen = seen if seen is not None else set()
        if depth > MAX_DEPTH:
            acc.unres(f"{self.s.where(n)} source chain deeper than {MAX_DEPTH} steps")
            return
        key = (id(n), role)
        if key in seen:
            return
        seen = seen | {key}
        if isinstance(n, ast.Constant):
            if role == "value":
                self.literal(n.value, n, acc, "the column is written a literal")
            return
        if isinstance(n, ast.JoinedStr):
            flat = _flat(n)
            if flat is not None:
                if role == "value":
                    self.literal(flat, n, acc, "the column is written a literal")
                return
            fvs = [v for v in n.values if isinstance(v, ast.FormattedValue)]
            bare = len(fvs) == 1 and all(isinstance(v, ast.FormattedValue) or (isinstance(v, ast.Constant) and not str(v.value).strip()) for v in n.values)
            for v in fvs:
                self.expr(v.value, acc, depth + 1, seen, role if bare else "part")    # f"{x or 'N/A'}" IS the value `x or 'N/A'`
            return
        if isinstance(n, ast.BinOp):
            if isinstance(n.op, (ast.Add, ast.Mod)):
                flat = _flat(n)
                if flat is not None:
                    if role == "value":
                        self.literal(flat, n, acc, "the column is written a literal")
                    return
                for side in (n.left, n.right):
                    self.expr(side, acc, depth + 1, seen, "part")
                return
            self.expr(n.left, acc, depth + 1, seen, "part")
            self.expr(n.right, acc, depth + 1, seen, "part")
            return
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.Or):
                for i, v in enumerate(n.values):
                    if i > 0 and isinstance(v, ast.Constant) and v.value is not None:
                        self.flag(v.value, v, acc, "literal fallback `or`", role)
                    elif i > 0 and isinstance(v, ast.JoinedStr) and _flat(v) is not None:
                        self.flag(_flat(v), v, acc, "literal fallback `or`", role)
                    else:
                        self.expr(v, acc, depth + 1, seen, role)
            else:
                for v in n.values:
                    self.expr(v, acc, depth + 1, seen, "part")
            return
        if isinstance(n, ast.IfExp):
            missing = self._missing_test(n.test)
            for br, other in ((n.body, n.orelse), (n.orelse, n.body)):
                lit = br if isinstance(br, ast.Constant) and br.value is not None else (br if isinstance(br, ast.JoinedStr) and _flat(br) is not None else None)
                if lit is not None:
                    val = lit.value if isinstance(lit, ast.Constant) else _flat(lit)
                    other_lit = isinstance(other, ast.Constant) or (isinstance(other, ast.JoinedStr) and _flat(other) is not None)
                    if role == "part" and isinstance(lit, ast.Constant) and self._terminator_suffix(n, lit, other):
                        pass                             # SS 2026-10-05 R-b: a lone punctuation literal that TERMINATES a composed sentence (`"...winner X" + ("; methods diverge." if m else ".")`) is not a fallback
                    elif isinstance(val, str) and self.ph(val):
                        acc.problem("literal_fallback", self.s.where(lit), f"placeholder literal in a conditional expression: {val!r}")
                    elif missing and not other_lit and isinstance(val, str):
                        # a literal returned when a value is missing / empty, the other branch being a computed value: a default sentence standing in for the sentence the value would have made
                        acc.problem("literal_fallback", self.s.where(lit), f"literal default for a missing / empty value (`{ast.unparse(n.test)[:60]}`): {val!r}")
                    elif role == "value" and not other_lit:
                        pass
                    elif role == "value" and other_lit:
                        pass                             # an enumerated choice between two labels: not a default for a missing value
                else:
                    self.expr(br, acc, depth + 1, seen, role)
            return
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
            for e in n.elts:
                self.expr(e, acc, depth + 1, seen, role)
            return
        if isinstance(n, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
            self.expr(n.elt, acc, depth + 1, seen, "part")
            return
        if isinstance(n, ast.Dict):
            return                                   # a JSON / jsonb container: its nested keys are the path entries' business
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            k = n.slice.value                         # `row["citation_human"]`: the row was built somewhere in the scope: follow EVERY assignment to that key
            if ("key", k) in seen:
                return
            seen = seen | {("key", k)}
            srcs = self.s.key_sources(k)
            if not srcs:
                acc.unres(f"{self.s.where(n)} row key {k!r}: no assignment to it in the scanned scope (the row may be read from the database or built elsewhere)")
                return
            op = self.s.opaque({(self.s.unit_of.get(id(n)) or {}).get("rel")} | {(self.s.unit_of.get(id(x)) or {}).get("rel") for x in srcs}, k)
            if op:
                acc.unres(f"{self.s.where(n)} row key {k!r}: dynamic row construction in the files that build it could also supply it ({op[0]})")
            for x in srcs:
                self.expr(x, acc, depth + 1, seen, role)
            return
        if isinstance(n, ast.Attribute):
            base = n.value
            const_like = n.attr.isupper() or (isinstance(base, ast.Name) and base.id in ("self", "cls"))
            if not const_like:
                return                               # data read from an object / row (`row.citation`): not a literal
            if ("attr", n.attr) in seen:
                return
            seen = seen | {("attr", n.attr)}
            vals = self.s.attr_assigns.get(n.attr) or (self.s.module_assigns.get(n.attr) if n.attr.isupper() else None)
            if not vals:
                acc.unres(f"{self.s.where(n)} `{ast.unparse(n)[:40]}` is a constant / instance attribute with no assignment in the scanned scope (its value is not read)")
                return
            for v in vals:
                self.expr(v, acc, depth + 1, seen, role)
            return
        if isinstance(n, ast.Subscript):
            base = n.value
            if isinstance(base, ast.Name) and base.id in self.s.module_assigns and self.s.enclosing(n) is not None and not self._local_name(n, base.id):
                for v in self.s.module_assigns[base.id]:
                    dv = self._dict_display_values(v)
                    if isinstance(v, (ast.List, ast.Tuple, ast.Set)):
                        for e in v.elts:
                            self.expr(e, acc, depth + 1, seen, role)
                    elif dv is not None:
                        for e in dv:
                            self.expr(e, acc, depth + 1, seen, role)
                    else:
                        self.expr(v, acc, depth + 1, seen, role)
                return
            return                                   # data read from a row / object: not a literal
        if isinstance(n, ast.Starred):
            self.expr(n.value, acc, depth + 1, seen, role)
            return
        if isinstance(n, ast.Name):
            self.name(n, acc, depth, seen, role)
            return
        if isinstance(n, ast.Call):
            self.call(n, acc, depth, seen, role)
            return
        if isinstance(n, ast.Await):
            self.expr(n.value, acc, depth + 1, seen, role)
            return
        acc.unres(f"{self.s.where(n)} an expression of kind {type(n).__name__} the scan does not follow")

    @staticmethod
    def _dict_display_values(v):
        """The value nodes of a dict display `{...}` or a `dict(a=..., b=...)` / `dict({...}, k=...)` call; None when `v` is neither (a `**` unpack's value is read too)."""
        if isinstance(v, ast.Dict):
            return list(v.values)
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "dict":
            out = [kw.value for kw in v.keywords]
            for a in v.args:
                if isinstance(a, ast.Dict):
                    out.extend(a.values)
                elif isinstance(a, ast.Call):
                    out.extend(_Analyzer._dict_display_values(a) or [])
            return out
        return None

    def _module_dict_values(self, recv, at) -> list:
        """The values of a module-level dict constant named by `recv` (a bare Name that is not a local of the enclosing function), for `DEFS.get(k)`."""
        if not isinstance(recv, ast.Name) or recv.id not in self.s.module_assigns or self.s.enclosing(at) is None or self._local_name(at, recv.id):
            return []
        out = []
        for v in self.s.module_assigns[recv.id]:
            out.extend(self._dict_display_values(v) or [])
        return out

    def _local_name(self, n, name: str) -> bool:
        """`name` is a local variable or parameter of the function enclosing `n` (so it is not the module constant of that name)."""
        fn = self.s.enclosing(n)
        if fn is None or isinstance(fn, ast.Lambda):
            return False
        a = fn.args
        if name in [x.arg for x in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs)]:
            return True
        return any(isinstance(r, ast.Name) and isinstance(r.ctx, ast.Store) and r.id == name for r in self.s.fn_nodes(fn))

    def call(self, n: ast.Call, acc, depth, seen, role):
        f = n.func
        nm = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
        if nm in _DEFAULT_ARG_METHODS:
            pos = _DEFAULT_ARG_METHODS[nm]
            cands = [a for i, a in enumerate(n.args) if i >= pos] + [kw.value for kw in n.keywords if kw.arg in ("default", "fallback")]
            if nm in ("coalesce", "nvl", "ifnull"):
                cands = list(n.args[1:]) or cands
            for a in cands:
                v = a.value if isinstance(a, ast.Constant) else (_flat(a) if isinstance(a, ast.JoinedStr) else None)
                if isinstance(a, ast.Constant) and a.value is not None:
                    self.flag(a.value, a, acc, f"literal default of `{nm}(...)`", role)
                elif isinstance(v, str):
                    self.flag(v, a, acc, f"literal default of `{nm}(...)`", role)
                elif isinstance(a, (ast.Name, ast.Attribute)):
                    # a default that is a NAME / ATTRIBUTE (`d.get('k', MISSING)` with MISSING = 'unknown'): follow it like any other value the column may be written
                    self.expr(a, acc, depth + 1, seen, role)
            if isinstance(f, ast.Attribute) and nm in ("get", "pop", "setdefault"):
                # the RECEIVER may itself be a module-level dict display / `dict(...)` call: its values are what the lookup returns
                for v in self._module_dict_values(f.value, n):
                    self.expr(v, acc, depth + 1, seen, role)
            for a in list(n.args[:pos]) + ([f.value] if isinstance(f, ast.Attribute) else []):
                if isinstance(a, ast.Constant):
                    continue
                self.expr(a, acc, depth + 1, seen, "part")
            if nm in ("get", "pop", "setdefault", "getenv", "next", "getattr", "dict_get"):
                return
        local = self.s.funcs.get(nm) if nm else None
        if local and not (isinstance(f, ast.Attribute) and nm in _BUILTIN_PURE and nm not in self.s.funcs):
            for fn in local[:3]:
                self.returns(fn, acc, depth + 1, seen, role)
            return
        if nm in _BUILTIN_PURE or nm in ("get", "pop", "setdefault", "getenv", "next", "getattr"):
            thru = role if nm in _PASS_ROLE else "part"
            if isinstance(f, ast.Attribute):
                self.expr(f.value, acc, depth + 1, seen, thru)
            for i, a in enumerate(n.args):
                self.expr(a, acc, depth + 1, seen, thru if (i == 0 and isinstance(f, ast.Name)) else "part")
            for kw in n.keywords:
                self.expr(kw.value, acc, depth + 1, seen, "part")
            return
        acc.unres(f"{self.s.where(n)} call to `{ast.unparse(f)[:50]}`, defined outside the scanned scope (its return value is not read)")

    def returns(self, fn, acc, depth, seen, role):
        got = False
        for r in self.s.fn_nodes(fn):
            if isinstance(r, ast.Return) and r.value is not None:
                got = True
                self.expr(r.value, acc, depth, seen, role)
            elif isinstance(r, (ast.Yield, ast.YieldFrom)) and r.value is not None:
                got = True
                self.expr(r.value, acc, depth, seen, role)
        if not got:
            return

    def name(self, n: ast.Name, acc, depth, seen, role):
        fn = self.s.enclosing(n)
        bound = False
        if fn is not None and not isinstance(fn, ast.Lambda):
            args = fn.args
            params = [a.arg for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)]
            if args.vararg:
                params.append(args.vararg.arg)
            if args.kwarg:
                params.append(args.kwarg.arg)
            for r in self.s.fn_nodes(fn):
                if isinstance(r, ast.Assign):
                    for t in r.targets:
                        if isinstance(t, ast.Name) and t.id == n.id:
                            bound = True
                            self.expr(r.value, acc, depth + 1, seen, role)
                        elif isinstance(t, (ast.Tuple, ast.List)):
                            for i, e in enumerate(t.elts):
                                if isinstance(e, ast.Name) and e.id == n.id:
                                    bound = True
                                    self.unpack(r.value, i, len(t.elts), acc, depth + 1, seen, role)
                elif isinstance(r, ast.AnnAssign) and isinstance(r.target, ast.Name) and r.target.id == n.id and r.value is not None:
                    bound = True
                    self.expr(r.value, acc, depth + 1, seen, role)
                elif isinstance(r, ast.AugAssign) and isinstance(r.target, ast.Name) and r.target.id == n.id:
                    bound = True
                    self.expr(r.value, acc, depth + 1, seen, "part")
                elif isinstance(r, (ast.For, ast.AsyncFor)):
                    tg = [t.id for t in ast.walk(r.target) if isinstance(t, ast.Name)]
                    if n.id in tg:
                        bound = True
                        it = r.iter
                        if isinstance(it, (ast.List, ast.Tuple, ast.Set)) and isinstance(r.target, ast.Name):
                            for e in it.elts:
                                self.expr(e, acc, depth + 1, seen, role)
                elif isinstance(r, ast.comprehension):
                    if any(isinstance(t, ast.Name) and t.id == n.id for t in ast.walk(r.target)):
                        bound = True
                elif isinstance(r, ast.With):
                    for it in r.items:
                        if it.optional_vars is not None and any(isinstance(t, ast.Name) and t.id == n.id for t in ast.walk(it.optional_vars)):
                            bound = True
                elif isinstance(r, ast.NamedExpr) and isinstance(r.target, ast.Name) and r.target.id == n.id:
                    bound = True
                    self.expr(r.value, acc, depth + 1, seen, role)
            if bound:
                return
            if n.id in params:
                self.param(fn, n.id, acc, depth, seen, role)
                return
        if n.id in self.s.module_assigns:
            for v in self.s.module_assigns[n.id]:
                self.expr(v, acc, depth + 1, seen, role)
            return
        if n.id in ("None", "True", "False"):
            return
        acc.unres(f"{self.s.where(n)} the name `{n.id}` is bound outside the scanned scope (an import or a global it does not read)")

    def unpack(self, value, i, n, acc, depth, seen, role):
        if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == n and not any(isinstance(e, ast.Starred) for e in value.elts):
            self.expr(value.elts[i], acc, depth, seen, role)
            return
        if isinstance(value, ast.Call):
            nm = value.func.id if isinstance(value.func, ast.Name) else value.func.attr if isinstance(value.func, ast.Attribute) else None
            for fn in (self.s.funcs.get(nm) or [])[:3]:
                for r in self.s.fn_nodes(fn):
                    if isinstance(r, ast.Return) and isinstance(r.value, (ast.Tuple, ast.List)) and len(r.value.elts) == n:
                        self.expr(r.value.elts[i], acc, depth, seen, role)
                    elif isinstance(r, ast.Return) and r.value is not None and not isinstance(r.value, (ast.Tuple, ast.List)):
                        self.expr(r.value, acc, depth, seen, role)
            if nm in self.s.funcs:
                return
        return                                       # unpacked from data (a row, a zip, a call outside the scope): not a literal

    def param(self, fn, pname, acc, depth, seen, role):
        args = fn.args
        pos = list(args.posonlyargs) + list(args.args)
        names = [a.arg for a in pos]
        idx = names.index(pname) if pname in names else None
        if pname in ("self", "cls") and idx == 0:
            return
        dflt = None
        if idx is not None:
            nd = len(args.defaults)
            if idx >= len(pos) - nd:
                dflt = args.defaults[idx - (len(pos) - nd)]
        else:
            kwn = [a.arg for a in args.kwonlyargs]
            if pname in kwn:
                d = args.kw_defaults[kwn.index(pname)]
                dflt = d
        if dflt is not None:
            self.expr(dflt, acc, depth + 1, seen, role)
        called = False
        is_method = bool(names) and names[0] in ("self", "cls")
        for c in self.s.calls:
            cn = c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else None
            if cn != fn.name:
                continue
            arg = None
            for kw in c.keywords:
                if kw.arg == pname:
                    arg = kw.value
            if arg is None and idx is not None:
                k = idx - (1 if is_method and isinstance(c.func, ast.Attribute) else 0)
                if 0 <= k < len(c.args) and not any(isinstance(a, ast.Starred) for a in c.args[:k + 1]):
                    arg = c.args[k]
            if arg is None:
                if any(isinstance(a, ast.Starred) for a in c.args) or any(kw.arg is None for kw in c.keywords):
                    acc.unres(f"{self.s.where(c)} call of `{fn.name}` with */** arguments: the value of `{pname}` is not read")
                    called = True
                continue
            called = True
            self.expr(arg, acc, depth + 1, seen, role)
        if not called and dflt is None and fn.name in _ENTRY_POINTS:
            return                                   # a writer entry point: its parameters are the framework's (ctx, substep), not a value this writer chose
        if not called and dflt is None:
            acc.unres(f"{self.s.where(fn)} parameter `{pname}` of `{fn.name}` has no caller in the scanned scope")


_SQL_VALUE_FREE = re.compile(r"\s*(?:now\(\)|current_timestamp|current_date|statement_timestamp\(\)|clock_timestamp\(\)|transaction_timestamp\(\)|gen_random_uuid\(\)|uuid_generate_v4\(\))\s*(?:::\s*[A-Za-z_][\w ]*)?\s*", re.I)


def _piece_problems(piece: str, where: str, is_placeholder, acc: _Acc, *, column: str = "", whole: str | None = None) -> bool:
    """The SQL expression written for the column. Returns True when the value is FOLLOWED elsewhere (it carries a bind placeholder). Pure literal / numeric literal -> constant (or placeholder) write;
    a quoted literal beside COALESCE / NULLIF / CASE -> literal fallback; NULL / DEFAULT / a clock or uuid function / `EXCLUDED.<same column>` need nothing. ANYTHING ELSE with no bind placeholder
    (`s.x`, `col || 'x'`, a sub-select) takes its value from the database, which the scan does not read: UNRESOLVED. `whole` (the full statement text of a SELECT-sourced write: INSERT ... SELECT,
    UPDATE ... FROM, a sub-select in the piece) is also searched for a placeholder-vocabulary literal inside a fallback function anywhere in the statement."""
    p = piece.strip()
    if whole is not None:
        for m in re.finditer(r"\b(?:COALESCE|NULLIF|IFNULL|NVL)\s*\(", whole, re.I):
            g = _balanced(whole, m.end() - 1)
            seg = g[0] if g else whole[m.end():m.end() + 200]
            for lit in _SQL_STR_LITERAL.finditer(seg):
                t = lit.group(1).replace("''", "'")
                if is_placeholder(t):
                    flat = re.sub(r'[ \n]+', ' ', whole[m.start():m.start() + 70])        # (a local: Python 3.11 allows neither a backslash nor the string's own quote inside an f-string expression)
                    acc.problem("literal_fallback", where, f"SQL fallback literal {t!r} in the SELECT / FROM source of the write (`{flat}`)")
        for m in re.finditer(r"\bCASE\b.*?\bEND\b", whole, re.I | re.S):
            for lit in _SQL_STR_LITERAL.finditer(m.group(0)):
                t = lit.group(1).replace("''", "'")
                if is_placeholder(t):
                    acc.problem("literal_fallback", where, f"SQL CASE literal {t!r} in the SELECT / FROM source of the write")
    if re.fullmatch(r"NULL(?:\s*::\s*[A-Za-z_][\w ]*)?", p, re.I) or re.fullmatch(r"DEFAULT", p, re.I):
        return False
    if _SQL_PURE_LITERAL.fullmatch(p):
        txt = _SQL_STR_LITERAL.search(p).group(1).replace("''", "'")
        acc.problem("literal_fallback" if is_placeholder(txt) else "constant_write", where, f"the SQL writes the literal {txt!r}")
        return
    if _SQL_NUM_LITERAL.fullmatch(p):
        acc.problem("constant_write", where, f"the SQL writes the number literal {p!r}")
        return
    lits = [m.group(1).replace("''", "'") for m in _SQL_STR_LITERAL.finditer(p)]
    if lits and _SQL_FALLBACK_FN.search(p):
        flat_p = re.sub(r"\s+", " ", p)
        for t in lits:
            acc.problem("literal_fallback", where, f"SQL fallback literal {t!r} in `{flat_p[:70]}`")
    if _PH_ANY.search(p):
        return True
    if _SQL_VALUE_FREE.fullmatch(p) or (column and re.fullmatch(r"\s*EXCLUDED\s*\.\s*\"?" + re.escape(column) + r"\"?\s*", p, re.I)):
        return False
    if lits and not re.search(r"[A-Za-z_]\w*\s*(?:\.|\()", re.sub(r"'(?:[^']|'')*'", "''", p)) and not re.sub(r"'(?:[^']|'')*'|\|\||\s|::\w+", "", p):
        flat = re.sub(r'[ \n]+', ' ', p)[:60]
        acc.problem("constant_write", where, f"the SQL writes a concatenation of literals: {flat!r}")
        return False
    flat = re.sub(r'[ \n]+', ' ', p)[:70]
    acc.unres(f"{where} the SQL writes `{flat}`, a value taken from another column / table / expression the scan does not read")
    return False


def _execute_bindings(scope: _Scope, unit, line: int):
    """[(call, sql_arg_index)]: execute-like calls whose SQL argument is the string node on `line` of `unit` (inline, or a Name assigned that node)."""
    out = []
    names: dict[str, set] = {}                    # name -> the enclosing functions that assign the statement text to it (None = module level)
    for n in scope.nodes:
        if isinstance(n, ast.Assign) and scope.unit_of.get(id(n)) is unit and _is_string_node(n.value) and n.value.lineno == line:
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.setdefault(t.id, set()).add(id(scope.enclosing(n)) if scope.enclosing(n) is not None else None)
    for c in scope.calls:
        nm = c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else None
        if nm not in _EXEC_NAMES:
            continue
        for i, a in enumerate(c.args[:3]):
            if (_is_string_node(a) and a.lineno == line and scope.unit_of.get(id(c)) is unit):
                out.append((c, i))
            elif isinstance(a, ast.Name) and a.id in names:
                # the SAME variable name in ANOTHER function (`sql` is everyone's name for a statement) is not this statement: the call must be in the
                # function that assigned the text, or the text must be a module-level constant
                fn = scope.enclosing(c)
                if None in names[a.id] or (fn is not None and id(fn) in names[a.id]):
                    out.append((c, i))
    return out


_MUTATORS = frozenset({"append", "extend", "insert", "add", "update", "setdefault", "__iadd__", "appendleft", "extendleft", "remove", "pop", "clear", "sort", "reverse"})


def _mutated(scope: _Scope, fn, name: str) -> bool:
    """True when `name` is changed inside `fn` after its assignment: `.append/.extend/...(...)`, `name += ...`, `name[i] = ...`, `del name[i]`, or a second plain assignment."""
    plain = 0
    for r in (scope.fn_nodes(fn) if fn is not None else []):
        if isinstance(r, ast.Call) and isinstance(r.func, ast.Attribute) and r.func.attr in _MUTATORS and isinstance(r.func.value, ast.Name) and r.func.value.id == name:
            return True
        if isinstance(r, ast.AugAssign) and isinstance(r.target, ast.Name) and r.target.id == name:
            return True
        if isinstance(r, ast.Assign):
            for t in r.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == name:
                    return True
                if isinstance(t, ast.Name) and t.id == name:
                    plain += 1
        if isinstance(r, ast.Delete) and any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == name for t in r.targets):
            return True
    return plain > 1


# ───────────── FORM-GAP (SS N-191, detector limits #3218): rows returned by a helper as the elements of a tuple-unpacking assignment ─────────────
# `chapter_rows, topic_rows = _build_desired_rows(...)` then `cur.executemany(SQL, chapter_rows)`: the rows are built in the helper, each list from `[]` by `.append((<tuple display>))` and returned in a
# tuple. The scan follows exactly that shape (and refuses anything else with the old reason): ONE tuple-unpacking assignment of the name, ONE resolvable helper whose every `return` is a tuple with a
# Name at that position, the Name initialised once to `[]`, changed only by `.append(<tuple display>)`, and never handed to another callable that could change it. Anything else is unresolved.
_PURE_LIST_CONSUMERS = frozenset({"len", "sorted", "list", "tuple", "enumerate", "sum", "any", "all", "min", "max", "reversed", "iter", "bool", "set", "frozenset", "zip"})


def _appended_tuples(scope: _Scope, fn, name: str):
    """The tuple displays the function appends to the list `name`, or None when the list is not built exactly that way (see above)."""
    inits, out = 0, []
    for n in scope.fn_nodes(fn):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            if len(n.targets) == 1 and isinstance(n.value, ast.List) and not n.value.elts:
                inits += 1
            else:
                return None
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name:
            if isinstance(n.value, ast.List) and not n.value.elts:
                inits += 1
            else:
                return None
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) and n.target.id == name:
            return None
        elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)) and any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(n.target)):
            return None                                                   # the name is rebound by a loop target
        elif isinstance(n, ast.Delete) and any(isinstance(x, ast.Name) and x.id == name for t in n.targets for x in ast.walk(t)):
            return None
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == name:
                if f.attr == "append" and len(n.args) == 1 and not n.keywords and isinstance(n.args[0], ast.Tuple):
                    out.append(n.args[0])
                else:
                    return None                                           # extend / insert / pop / remove / sort ... : the set of rows is not the appended tuples
            else:
                for a in list(n.args) + [k.value for k in n.keywords]:
                    if isinstance(a, ast.Name) and a.id == name and not (isinstance(f, ast.Name) and f.id in _PURE_LIST_CONSUMERS):
                        return None                                       # handed to a callable that could change it
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == name:
                    return None
    if inits != 1 or not out:
        return None
    return out


def _unpacked_rows_from_helper(scope: _Scope, fn, pname: str):
    """The tuple displays of the rows list `pname`, when `pname` is one element of ONE tuple-unpacking assignment `a, b = helper(...)` in `fn` (see the block comment above). None otherwise."""
    found = []
    for r in scope.fn_nodes(fn):
        if isinstance(r, ast.Assign):
            for t in r.targets:
                if isinstance(t, (ast.Tuple, ast.List)) and any(isinstance(e, ast.Name) and e.id == pname for e in t.elts):
                    found.append((r, t))
    if len(found) != 1:
        return None
    r, t = found[0]
    if len(r.targets) != 1 or any(isinstance(e, ast.Starred) for e in t.elts) or not (isinstance(r.value, ast.Call) and isinstance(r.value.func, ast.Name)):
        return None
    names = [e.id if isinstance(e, ast.Name) else None for e in t.elts]
    if names.count(pname) != 1 or _mutated(scope, fn, pname):
        return None
    idx = names.index(pname)
    defs = scope.funcs.get(r.value.func.id, [])
    if len(defs) != 1:
        return None
    callee = defs[0]
    returned, any_return = set(), False
    for n in scope.fn_nodes(callee):
        if isinstance(n, ast.Return):
            any_return = True
            v = n.value
            if not (isinstance(v, ast.Tuple) and len(v.elts) == len(t.elts) and isinstance(v.elts[idx], ast.Name)):
                return None
            returned.add(v.elts[idx].id)
        elif isinstance(n, (ast.Yield, ast.YieldFrom)):
            return None
    if not any_return:
        return None
    tuples = []
    for nm in sorted(returned):
        got = _appended_tuples(scope, callee, nm)
        if got is None:
            return None
        tuples += got
    return tuples



def _positional_exprs(scope: _Scope, call: ast.Call, sql_i: int, idx: int, many: bool, acc: _Acc):
    """The expressions bound to positional placeholder `idx` at an execute-like call, or None (unresolved reason recorded)."""
    params = None
    if len(call.args) > sql_i + 1:
        params = call.args[sql_i + 1]
    for kw in call.keywords:
        if kw.arg in ("params", "vars", "argslist", "rows", "seq_of_parameters"):
            params = kw.value
    if params is None:
        acc.unres(f"{scope.where(call)} the execute call carries no parameters for placeholder {idx}")
        return None
    if isinstance(params, ast.Name):
        fn = scope.enclosing(call)
        vals = []
        for r in (scope.fn_nodes(fn) if fn is not None else []):
            if isinstance(r, ast.Assign) and any(isinstance(t, ast.Name) and t.id == params.id for t in r.targets):
                vals.append(r.value)
        if len(vals) == 1:
            pname = params.id
            params = vals[0]
            if _mutated(scope, fn, pname):
                acc.unres(f"{scope.where(call)} the parameter rows are the name `{pname}`, which the function also mutates (append / extend / insert / += / item store): the literal it was assigned is not the complete row set")
                return None
        else:
            tuples = _unpacked_rows_from_helper(scope, fn, params.id) if not vals else None          # FORM-GAP: `a, b = helper(...)` whose helper appends tuple displays to the lists it returns
            if tuples:
                params = ast.List(elts=tuples, ctx=ast.Load())
            else:
                acc.unres(f"{scope.where(call)} the parameters are the name `{params.id}` ({len(vals)} assignment(s) in the function): positional values not read")
                return None
    rows = [params] if not many else None
    if many:
        if isinstance(params, (ast.List, ast.Tuple)) and params.elts:
            rows = list(params.elts)
        elif isinstance(params, (ast.List, ast.Tuple)):
            acc.unres(f"{scope.where(call)} executemany over an EMPTY literal sequence: the rows written are not in the source")
            return None
        else:
            acc.unres(f"{scope.where(call)} executemany over a sequence the scan cannot enumerate ({type(params).__name__}): the per-row values are not read")
            return None
    out = []
    for r in rows:
        if isinstance(r, (ast.Tuple, ast.List)) and not any(isinstance(e, ast.Starred) for e in r.elts) and idx < len(r.elts):
            out.append(r.elts[idx])
        else:
            acc.unres(f"{scope.where(call)} the parameter row is not a literal tuple/list the scan can index ({type(r).__name__})")
            return None
    return out


_LOOP_WRAPPERS = frozenset({"str", "int", "float"})          # one-argument wrappers that keep the row's value (json.dumps is checked by attribute below)
_LOOP_ESCAPES = (ast.Continue, ast.Break, ast.Return, ast.Raise, ast.Yield, ast.YieldFrom, ast.Await, ast.NamedExpr)


def _loop_wrapper_ok(call: ast.AST, v: str) -> bool:
    """`v = f(v)` where f is json.dumps / str / int / float (one argument, no keywords but json.dumps' own formatting ones): a transformation of the SAME value that cannot invent a
    placeholder. Any other wrapper (`_fill(v)`, `v or ...`, `coalesce(v)`) can, so it is not accepted without analysing it."""
    if not (isinstance(call, ast.Call) and len(call.args) == 1 and isinstance(call.args[0], ast.Name) and call.args[0].id == v):
        return False
    f = call.func
    if isinstance(f, ast.Name):
        return f.id in _LOOP_WRAPPERS and not call.keywords
    if not (isinstance(f, ast.Attribute) and f.attr == "dumps" and isinstance(f.value, ast.Name) and f.value.id == "json"):
        return False
    for k in call.keywords:
        if k.arg == "default":
            if not (isinstance(k.value, ast.Name) and k.value.id == "str"):          # a `default=` hook can return any text (`lambda o: "N/A"`, `_ph`): only `str` is the value itself
                return False
        elif k.arg in ("ensure_ascii", "sort_keys", "indent", "separators"):
            if not isinstance(k.value, (ast.Constant, ast.Tuple)) or (isinstance(k.value, ast.Tuple) and not all(isinstance(e, ast.Constant) for e in k.value.elts)):
                return False
        else:
            return False
    return True


def _rebinders(fn, name: str, own_args=None):
    """The first node of `fn` (nested functions included) that BINDS `name` by a form other than the plain assignment / loop target the closed shape allows: a `with ... as`, an `except ... as`,
    an import (`import a as name`, `from m import name`), a match capture (`case name`, `*name`, `**name`), a `del name`, a `global` / `nonlocal` declaration, a def / class named so, a
    comprehension target, a lambda / def parameter, or a walrus. Returns the node or None."""
    for n in ast.walk(fn):
        if isinstance(n, ast.With) or isinstance(n, ast.AsyncWith):
            if any(it.optional_vars is not None and any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(it.optional_vars)) for it in n.items):
                return n
        elif isinstance(n, ast.ExceptHandler) and n.name == name:
            return n
        elif isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name.split(".")[0]) == name for a in n.names):
            return n
        elif isinstance(n, ast.MatchAs) and n.name == name or isinstance(n, ast.MatchStar) and n.name == name or isinstance(n, ast.MatchMapping) and n.rest == name:
            return n
        elif isinstance(n, ast.Delete) and any(isinstance(x, ast.Name) and x.id == name for t in n.targets for x in ast.walk(t)):
            return n
        elif isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names:
            return n
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name:
            return n
        elif isinstance(n, ast.comprehension) and any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(n.target)):
            return n
        elif isinstance(n, ast.arguments) and n is not own_args and any(a.arg == name for a in n.posonlyargs + n.args + n.kwonlyargs + [x for x in (n.vararg, n.kwarg) if x is not None]):
            return n
        elif isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name) and n.target.id == name:
            return n
    return None


def _module_list_mutation(scope, name: str):
    """A description of the first place the scanned scope changes the module-level list `name` other than its one literal assignment: an item or slice store, `del name[i]`, an augmented
    assignment, an assignment to the bare name inside a function (a `global` rebind), or a mutating method call (`name.append(...)`). None when there is none."""
    for n in scope.nodes:
        targets = []
        if isinstance(n, ast.Assign):
            targets = n.targets
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            targets = [n.target]
        elif isinstance(n, ast.Delete):
            targets = n.targets
        for t in targets:
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == name:
                return f"an item store or delete at {scope.where(n)}"
            if isinstance(t, ast.Name) and t.id == name and (isinstance(n, (ast.AugAssign, ast.Delete)) or scope.enclosing(n) is not None):
                return f"a rebinding at {scope.where(n)}"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == name and n.func.attr in _MUTATORS:
            return f".{n.func.attr}() at {scope.where(n)}"
    return None


_DYNAMIC_NAMESPACE = frozenset({"globals", "locals", "vars", "eval", "exec"})


def _pure_list_read(par, n) -> bool:
    """`len(name)` or `'<constant>'.join(name)`: the two read-only uses a statement's column list has (placeholder count, column text), which cannot change the list."""
    if not (isinstance(par, ast.Call) and len(par.args) == 1 and par.args[0] is n and not par.keywords):
        return False
    f = par.func
    return (isinstance(f, ast.Name) and f.id == "len") or (isinstance(f, ast.Attribute) and f.attr == "join" and isinstance(f.value, ast.Constant) and isinstance(f.value.value, str))


def _list_escape(scope, name: str):
    """Why the module-level list `name` may be changed where the scan cannot see it, else None. Any reference to `name` other than the single literal assignment, `for <x> in name` iterations, `len(name)` and `'<sep>'.join(name)`
    is an alias / argument (`c = name; c.reverse()`, `operator.setitem(name, ...)`, `sorted(name)`) and is refused; so is any use of the dynamic namespace (`globals()`, `locals()`, `vars()`,
    `eval`, `exec`, a module's `__dict__`) anywhere in the scanned code, which can rebind or mutate the list by its NAME STRING."""
    for n in scope.nodes:
        if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Load):
            par = scope.parent.get(id(n))
            if not ((isinstance(par, (ast.For, ast.AsyncFor)) and par.iter is n) or _pure_list_read(par, n)):
                return f"is referenced other than as a `for` iterable, `len(...)` or `'<sep>'.join(...)` (line {getattr(n, 'lineno', 0)}): an alias or argument could change it"
        elif isinstance(n, ast.Name) and n.id in _DYNAMIC_NAMESPACE and isinstance(n.ctx, ast.Load):
            return f"cannot be shown unchanged: the scanned code uses `{n.id}` (line {getattr(n, 'lineno', 0)}), which can rebind a module name from a string"
        elif isinstance(n, ast.Attribute) and n.attr == "__dict__" and any(isinstance(x, ast.Name) and x.id == "__name__" or isinstance(x, ast.Attribute) and x.attr == "modules" for x in ast.walk(n.value)):
            return f"cannot be shown unchanged: the scanned code reads the module's `__dict__` (line {getattr(n, 'lineno', 0)})"
    return None


def _column_loop_key(scope: _Scope, call: ast.Call, sql_i: int, pos: int, column: str, cols: list):
    """The row key a positional parameter reads when the parameters are a list FILLED IN A COLUMN LOOP (ga_tajaka's `_insert_rows`):

        vals = []
        for c in _COLUMNS:            # a module-level list of string constants, the statement's own column list
            v = r[c]                  # exactly one read of the row by the loop variable
            if c in (...): v = json.dumps(v)   # optional wrappers: v = json.dumps / str / int / float (v), the same value
            vals.append(v)            # the only mutation, once, at the loop's top level

        conn.execute(sql, vals)

    Returns (key, None) = the position `pos` is column `column` of the loop list and its value is the row's `column` entry (so the writes to it are the key sources of `column`, exactly as
    for a named `%(column)s` parameter), or (None, why) when ANY part of the shape differs: nothing is guessed. The list must not ESCAPE the shape: `vals` is referenced exactly three times in
    the function body and its nested functions (the assignment, the append, the execute argument), so no alias, helper call, `del vals[i]` or item store can change it; the loop has no
    continue / break / return / raise / yield / await / walrus and no `else`, so no iteration is skipped or ended early; the loop variable and the value name are assigned only as shown. Pure."""
    params = call.args[sql_i + 1] if len(call.args) > sql_i + 1 else next((kw.value for kw in call.keywords if kw.arg in ("params", "vars")), None)
    if not isinstance(params, ast.Name):
        return None, "the parameters are not a plain name"
    fn = scope.enclosing(call)
    if fn is None:
        return None, "no enclosing function"
    nodes = scope.fn_nodes(fn)
    refs = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == params.id]
    if len(refs) != 3:
        return None, f"`{params.id}` is referenced {len(refs)} times in the function (the shape has exactly three: its assignment, its append and the execute argument)"
    assigns = [n for n in nodes if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == params.id for t in n.targets)]
    if len(assigns) != 1 or not (isinstance(assigns[0].value, ast.List) and not assigns[0].value.elts) or len(assigns[0].targets) != 1:
        return None, f"`{params.id}` is not assigned exactly once to an empty list"
    apps = [n for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == params.id]
    if len(apps) != 1 or apps[0].func.attr != "append" or len(apps[0].args) != 1 or apps[0].keywords or not isinstance(apps[0].args[0], ast.Name):
        return None, f"`{params.id}` is mutated other than by one `.append(<name>)`"
    app = apps[0]
    v = app.args[0].id
    stmt = scope.parent.get(id(app))                       # the Expr statement
    loop = scope.parent.get(id(stmt))
    if not (isinstance(stmt, ast.Expr) and isinstance(loop, ast.For) and stmt in loop.body):
        return None, "the append is not a top-level statement of a `for` loop"
    if loop.orelse:
        return None, "the loop has an `else` clause"
    if not (isinstance(loop.target, ast.Name) and isinstance(loop.iter, ast.Name)):
        return None, "the loop is not `for <name> in <name>`"
    body_nodes = [n for st in loop.body for n in ast.walk(st)]
    esc = next((n for n in body_nodes if isinstance(n, _LOOP_ESCAPES)), None)
    if esc is not None:
        return None, f"the loop body has a {type(esc).__name__} (line {getattr(esc, 'lineno', 0)}): an iteration could be skipped or the loop ended early"
    cvar, lst = loop.target.id, loop.iter.id
    for nm in (params.id, cvar, app.args[0].id):
        bad = _rebinders(fn, nm)
        if bad is not None:
            return None, f"`{nm}` is re-bound by a {type(bad).__name__} (line {getattr(bad, 'lineno', 0)}): the shape allows only its plain assignment / loop target"
    vals = scope.module_assigns.get(lst, [])
    if len(vals) != 1 or not (isinstance(vals[0], (ast.List, ast.Tuple)) and vals[0].elts and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in vals[0].elts)):
        return None, f"the loop list `{lst}` is not a module-level literal list of strings (assigned once)"
    bad = _module_list_mutation(scope, lst)
    if bad is not None:
        return None, f"the module list `{lst}` is changed outside its literal ({bad})"
    bad = _list_escape(scope, lst)
    if bad is not None:
        return None, f"the module list `{lst}` {bad}"
    names = [e.value for e in vals[0].elts]
    if [c.lower() for c in names] != [c.lower() for c in cols]:
        return None, f"the loop list `{lst}` is not the statement's column list"
    if pos >= len(names) or names[pos].lower() != column.lower():
        return None, f"position {pos} of `{lst}` is not column {column!r}"
    if any(isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For)) and any(isinstance(t, ast.Name) and t.id == cvar for t in ast.walk(n.target if isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.For)) else ast.Tuple(elts=n.targets, ctx=ast.Store())))
           for n in body_nodes):
        return None, f"the loop variable `{cvar}` is assigned inside the loop"
    v_assigns = sorted([n for n in body_nodes if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == v for t in ast.walk(ast.Tuple(elts=n.targets, ctx=ast.Store())))],
                       key=lambda n: (n.lineno, n.col_offset))
    top_first = [n for n in loop.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == v for t in n.targets)]
    if not v_assigns or not top_first or v_assigns[0] is not top_first[0] or any(isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.For)) and any(isinstance(t, ast.Name) and t.id == v for t in ast.walk(n.target)) for n in body_nodes):
        return None, f"`{v}` is not assigned first at the top of the loop body (or is augmented / re-bound by a loop in it)"
    first = top_first[0]
    src = first.value
    if not (len(first.targets) == 1 and isinstance(src, ast.Subscript) and isinstance(src.value, ast.Name) and isinstance(src.slice, ast.Name) and src.slice.id == cvar):
        return None, f"`{v}` is not read as `<row>[{cvar}]`"
    # the row name must be the target of an ENCLOSING `for <row> in ...` loop of the same function (not a parameter, a module constant, `rows[c]` or `_DEFAULTS[c]`), and nothing in the
    # function may rebind it or call a method on it (`r.update(...)`, `r = defaultdict(...)`)
    row = src.value.id
    outer, up = None, scope.parent.get(id(loop))
    while up is not None and up is not fn:
        if isinstance(up, ast.For) and isinstance(up.target, ast.Name) and up.target.id == row:
            outer = up
            break
        up = scope.parent.get(id(up))
    if outer is None:
        return None, f"the row name `{row}` is not the target of an enclosing `for {row} in ...` loop"
    # the rows iterated must be the function's own PARAMETER, untouched: `for r in _ext(rows)` or `rows = map(_fill, rows)` could hand the loop rows this scan never saw
    if not isinstance(outer.iter, ast.Name):
        return None, f"the enclosing loop iterates a {type(outer.iter).__name__}, not a plain parameter name (a call or expression could substitute the rows)"
    rows_name = outer.iter.id
    fa = fn.args
    if rows_name not in [x.arg for x in fa.posonlyargs + fa.args + fa.kwonlyargs]:
        return None, f"the enclosing loop iterates `{rows_name}`, which is not a parameter of the function"
    for n in ast.walk(fn):
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and any(isinstance(x, ast.Name) and x.id == rows_name for t in ([n.target] if not isinstance(n, ast.Assign) else n.targets) for x in ast.walk(t)):
            return None, f"the parameter `{rows_name}` is assigned inside the function (line {n.lineno})"
        if isinstance(n, ast.For) and any(isinstance(x, ast.Name) and x.id == rows_name for x in ast.walk(n.target)):
            return None, f"the parameter `{rows_name}` is a loop target (line {n.lineno})"
    bad = _rebinders(fn, rows_name, own_args=fn.args)
    if bad is not None:
        return None, f"the parameter `{rows_name}` is re-bound by a {type(bad).__name__} (line {getattr(bad, 'lineno', 0)})"
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == rows_name and n.func.attr in _MUTATORS:
            return None, f"the rows `{rows_name}` are mutated by .{n.func.attr}() (line {n.lineno})"
    bad = _rebinders(fn, row)
    if bad is not None:
        return None, f"the row name `{row}` is re-bound by a {type(bad).__name__} (line {getattr(bad, 'lineno', 0)})"
    for n in ast.walk(fn):
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and any(isinstance(x, ast.Name) and x.id == row for t in ([n.target] if not isinstance(n, ast.Assign) else n.targets) for x in ast.walk(t)):
            return None, f"the row name `{row}` is assigned inside the function (line {n.lineno})"
        if isinstance(n, ast.For) and n is not outer and any(isinstance(x, ast.Name) and x.id == row for x in ast.walk(n.target)):
            return None, f"the row name `{row}` is also the target of another loop (line {n.lineno})"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == row:
            return None, f"a method is called on the row `{row}` (line {n.lineno}): the row could be changed"
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            hit = next((x.id for arg in list(n.args) + [k.value for k in n.keywords] for x in ast.walk(arg) if isinstance(x, ast.Name) and x.id in (row, rows_name)), None)
            if hit is not None:
                return None, f"`{hit}` is an argument of a call (line {n.lineno}, e.g. `operator.setitem({hit}, ...)`): the row could be changed"
    for a in v_assigns[1:]:
        if len(a.targets) != 1 or not _loop_wrapper_ok(a.value, v):
            return None, f"`{v}` is re-assigned to something other than json.dumps / str / int / float of itself (line {a.lineno})"
    return column, None


def scan(units, entries, holders, *, is_placeholder, sql_texts, parse_entry, beyond=()):
    """Scan the writer scope `units` for every write to the declared prose `entries` (strings as in prose_fields).

    holders: {column: [owned table that holds it]}; sql_texts: the census's `_sql_texts`; parse_entry: its `parse_prose_field`.
    Returns dict(v, entries={entry: {writes: [...], problems, unresolved}}, problems, unresolved, files, write_paths)."""
    files = sorted({u["rel"] for u in units})
    if not units:
        return dict(v="NO_DETECTOR", entries={}, problems=[], unresolved=[], files=[], write_paths=[],
                    measured="NO_DETECTOR - no writer source in scope to scan for literal fallbacks and constant columns")
    scope = _Scope(units)
    an = _Analyzer(scope, is_placeholder)
    tables = sorted({t for ts in holders.values() for t in ts})
    stmts, seen_st = [], set()
    for u in units:
        for node in u["nodes"]:
            for text, ln in sql_texts(dict(u, nodes=[node])):
                if (u["rel"], ln, text) not in seen_st:
                    seen_st.add((u["rel"], ln, text))
                    stmts.append((u, blank_sql_comments(text), ln))          # comments are not SQL: blanked in place (same offsets)
    all_issues = []
    site: dict[tuple, list] = {}
    for u, text, ln in stmts:
        writes, issues = sql_writes(text, tables)
        for w in writes:
            site.setdefault((w["table"], w["column"]), []).append((u, text, ln, w))
        for i in issues:
            all_issues.append(f"{u['rel']}:{ln} {i}")
    per_entry, write_paths = {}, []
    tot_problems, tot_unres = [], []
    for e in entries:
        col, path = parse_entry(e)
        acc = _Acc()
        found = 0
        for t in holders.get(col, []):
            for (u, text, ln, w) in site.get((t.lower(), col.lower()), []):
                found += 1
                where = f"{u['rel']}:{ln}"
                write_paths.append(dict(entry=e, table=t, column=col, where=where, update=bool(w.get("update"))))
                select_sourced = bool(w.get("select")) or bool(re.search(r"\bSELECT\b", w["piece"], re.I)) or (w.get("update") and bool(re.search(r"\bFROM\b", text[w["start"]:], re.I)))
                if path is None:
                    _piece_problems(w["piece"], where, is_placeholder, acc, column=col, whole=text if select_sourced else None)
                phs = _placeholders(text, w["start"], w["start"] + len(w["piece"]))
                if path is not None:
                    pass                                      # the nested value is the leaf key's business (below)
                for named, pos in phs:
                    if path is not None:
                        continue
                    if named:
                        srcs = scope.key_sources(named)
                        if not srcs:
                            acc.unres(f"{where} named parameter %({named})s: no assignment to the key {named!r} in the scanned scope (the row may be read from the database or built elsewhere)")
                        else:
                            opaque = scope.opaque({u["rel"]} | {(scope.unit_of.get(id(x)) or {}).get("rel") for x in srcs}, named)
                            if opaque:
                                acc.unres(f"{where} named parameter %({named})s: dynamic row construction in the files that build it could also supply the key ({opaque[0]}" + (f"; +{len(opaque) - 1} more" if len(opaque) > 1 else "") + ")")
                            for s in srcs:
                                acc.sources += 1
                                an.expr(s, acc)
                    else:
                        binds = _execute_bindings(scope, u, ln)
                        if not binds:
                            acc.unres(f"{where} positional parameter {pos}: no execute call bound to this statement in the scanned scope")
                        for c, si in binds:
                            nm = c.func.id if isinstance(c.func, ast.Name) else c.func.attr
                            loop_key, why = (None, None)
                            if nm not in ("executemany", "execute_values", "execute_batch") and w.get("cols"):
                                loop_key, why = _column_loop_key(scope, c, si, pos, col, w["cols"])
                            if loop_key is not None:
                                # parameters filled in a column loop: the value of this column is the row's entry of the same name (as a named parameter)
                                srcs = scope.key_sources(loop_key)
                                if not srcs:
                                    acc.unres(f"{where} column-loop parameter {pos}: no assignment to the row key {loop_key!r} in the scanned scope")
                                else:
                                    opaque = scope.opaque({u["rel"]} | {(scope.unit_of.get(id(x)) or {}).get("rel") for x in srcs}, loop_key)
                                    if opaque:
                                        acc.unres(f"{where} column-loop parameter {pos}: dynamic row construction in the files that build it could also supply the key ({opaque[0]})")
                                    for sx in srcs:
                                        acc.sources += 1
                                        an.expr(sx, acc)
                                continue
                            exprs = _positional_exprs(scope, c, si, pos, nm in ("executemany", "execute_values", "execute_batch"), acc)
                            for x in exprs or []:
                                acc.sources += 1
                                an.expr(x, acc)
        if path is not None:
            # a wildcard segment ([*] array elements, * object members) is not a key of the writer's dict: the leaf is the last real key (SS N-448/N-450)
            keys = [k for k in path if k not in ("[*]", "*")]
            if not keys:
                acc.unres(f"JSON path entry {e}: every member value of the column is declared, so there is no nested key to trace to a write")
            else:
                leaf = keys[-1]
                srcs = scope.key_sources(leaf)
                opaque = scope.opaque({(scope.unit_of.get(id(x)) or {}).get("rel") for x in srcs}, leaf)
                if not srcs:
                    acc.unres(f"JSON path entry {e}: no assignment to the nested key {leaf!r} in the scanned scope")
                elif opaque:
                    acc.unres(f"JSON path entry {e}: dynamic row construction in scope could also supply the nested key ({opaque[0]})")
                for s in srcs:
                    acc.sources += 1
                    an.expr(s, acc)
        if found == 0:
            acc.unres(f"no statement in the scanned scope writes the column {col!r} of {', '.join(holders.get(col, [])) or 'its table'} (INSERT column list / UPDATE SET)")
        per_entry[e] = dict(writes=found, sources=acc.sources, problems=acc.problems, unresolved=acc.unresolved)
        tot_problems += [dict(p, entry=e) for p in acc.problems]
        tot_unres += [f"{e}: {u_}" for u_ in acc.unresolved]
    for i in all_issues:
        tot_unres.append(f"scope: {i}")
    for b in beyond:
        tot_unres.append(f"scope: delegation chain cut at the hop limit ({b}) holds write SQL the scan did not read")
    v = "PASS" if not tot_problems and not tot_unres else "PARTIAL"
    names = ", ".join(entries)
    if v == "PASS":
        measured = (f"writer scan CLEAN: {sum(p['writes'] for p in per_entry.values())} write path(s) to the declared prose column(s) {names} in {len(files)} source file(s); "
                    f"{sum(p['sources'] for p in per_entry.values())} source expression(s) followed, no literal fallback, no constant write, nothing unresolved")
    else:
        bits = []
        if tot_problems:
            bits.append("literal problems: " + "; ".join(f"{p['entry']} {p['where']} ({p['kind']}) {p['text']}" for p in tot_problems[:4]) + ("; ..." if len(tot_problems) > 4 else ""))
        if tot_unres:
            bits.append("unresolved write path(s): " + "; ".join(tot_unres[:3]) + ("; ..." if len(tot_unres) > 3 else ""))
        measured = "writer scan NOT clean - " + " | ".join(bits)
    return dict(v=v, entries=per_entry, problems=tot_problems, unresolved=tot_unres, files=files, write_paths=write_paths, measured=measured)
