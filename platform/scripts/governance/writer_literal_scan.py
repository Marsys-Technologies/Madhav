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
                        writes.append(dict(table=t, column=c, piece=pc, start=st))
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
                out.append(f"{self.where(n)} the key name used as a value ({type(par).__name__})")
            elif word.search(n.value) and not _SQLISH.match(n.value) and not isinstance(par, ast.Expr):
                out.append(f"{self.where(n)} the key name inside a non-SQL string")
        return out

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
                            and not isinstance(t.slice, (ast.Slice,)) and not isinstance(t.slice, ast.Constant):
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
                    if isinstance(val, str) and self.ph(val):
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
                    if isinstance(v, (ast.List, ast.Tuple, ast.Set)):
                        for e in v.elts:
                            self.expr(e, acc, depth + 1, seen, role)
                    elif isinstance(v, ast.Dict):
                        for e in v.values:
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
                    acc.problem("literal_fallback", where, f"SQL fallback literal {t!r} in the SELECT / FROM source of the write (`{re.sub(r'[ \n]+', ' ', whole[m.start():m.start() + 70])}`)")
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
        acc.problem("constant_write", where, f"the SQL writes a concatenation of literals: {re.sub(r'[ \n]+', ' ', p)[:60]!r}")
        return False
    acc.unres(f"{where} the SQL writes `{re.sub(r'[ \n]+', ' ', p)[:70]}`, a value taken from another column / table / expression the scan does not read")
    return False


def _execute_bindings(scope: _Scope, unit, line: int):
    """[(call, sql_arg_index)]: execute-like calls whose SQL argument is the string node on `line` of `unit` (inline, or a Name assigned that node)."""
    out = []
    names = set()
    for n in scope.nodes:
        if isinstance(n, ast.Assign) and scope.unit_of.get(id(n)) is unit and _is_string_node(n.value) and n.value.lineno == line:
            names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    for c in scope.calls:
        nm = c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else None
        if nm not in _EXEC_NAMES:
            continue
        for i, a in enumerate(c.args[:3]):
            if (_is_string_node(a) and a.lineno == line and scope.unit_of.get(id(c)) is unit) or (isinstance(a, ast.Name) and a.id in names):
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
                    stmts.append((u, text, ln))
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
                            exprs = _positional_exprs(scope, c, si, pos, nm in ("executemany", "execute_values", "execute_batch"), acc)
                            for x in exprs or []:
                                acc.sources += 1
                                an.expr(x, acc)
        if path is not None:
            leaf = [k for k in path if k != "[*]"][-1]
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
