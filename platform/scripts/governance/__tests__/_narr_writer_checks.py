"""_narr_writer_checks.py: structural (AST) checks that a declared `prose_fields` entry is really what its writer does.

A word search ("the column name appears in the file") is not a check: a writer that inserted `json.dumps({})` into the
declared column, or renamed the INSERT column, would still contain the word. These helpers answer, from the writer's
syntax tree: (1) does an INSERT statement bind the declared column, (2) is the value bound to it the output of the
named builder (tuple rows) / a dict literal that carries the declared path (named params), (3) is the leaf at the
declared JSON path composed by code (f-string, `+`, `%`, .format, .join), and (4) for a `[]` claim, do the bound
parameters of the INSERTs contain nothing but a verbatim read, a slice, a constant or json.dumps. Offline; no DB.
"""
from __future__ import annotations

import ast
import re


# ───────────────────────── small AST helpers ─────────────────────────

def _is_json_dumps(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "dumps"
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "json" and len(n.args) >= 1)


def _assign_values(tree, name):
    return [a.value for a in ast.walk(tree) if isinstance(a, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in a.targets)]


def _function(tree, name):
    fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    return fns[0] if len(fns) == 1 else None


def _called_name(call):
    if isinstance(call, ast.Call):
        f = call.func
        return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
    return None


def dict_nodes(tree, node, _seen=None):
    """Dict literals a value expression can be: itself, either branch of an IfExp, every assignment of a Name, and every
    returned dict of a function the expression calls by name."""
    _seen = _seen if _seen is not None else set()
    if id(node) in _seen:
        return []
    _seen.add(id(node))
    if isinstance(node, ast.Dict):
        return [node]
    if isinstance(node, ast.IfExp):
        return dict_nodes(tree, node.body, _seen) + dict_nodes(tree, node.orelse, _seen)
    if isinstance(node, ast.Name):
        return [d for v in _assign_values(tree, node.id) for d in dict_nodes(tree, v, _seen)]
    if isinstance(node, ast.Call):
        fn = _function(tree, _called_name(node) or "")
        if fn is not None:
            return [d for r in ast.walk(fn) if isinstance(r, ast.Return) and r.value is not None
                    for d in dict_nodes(tree, r.value, _seen)]
    return []


def dict_key_values(dicts, key):
    return [v for d in dicts for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value == key]


def _key_nodes(dicts, key):
    return [k for d in dicts for k in d.keys if isinstance(k, ast.Constant) and k.value == key]


def is_composed(tree, node, _seen=None):
    """True when the expression (following Name assignments) builds text: an f-string, `+`/`%` on strings, .format, .join."""
    _seen = _seen if _seen is not None else set()
    if id(node) in _seen:
        return False
    _seen.add(id(node))
    for n in ast.walk(node):
        if isinstance(n, ast.JoinedStr):
            return True
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("format", "join"):
            return True
        if isinstance(n, ast.Name) and any(is_composed(tree, v, _seen) for v in _assign_values(tree, n.id)):
            return True
    return False


# ───────────────────────── (1)+(2) the column is bound, and to the builder's output ─────────────────────────

def _strip_sql_comments(sql):
    return re.sub(r"--[^\n]*", "", sql)


def parse_insert(sql, table):
    """(columns, [placeholder positions]) of `INSERT INTO table (cols) VALUES (exprs)` (SQL comments ignored; each VALUES
    expression may hold several %s, e.g. a function call): columns[i] is bound from params[pos[i]] when exprs[i] holds
    exactly one %s. None when the statement is not an INSERT INTO table."""
    text = _strip_sql_comments(sql)
    m = re.search(rf"INSERT\s+INTO\s+(?:public\.)?{re.escape(table)}\s*\(([^)]*)\)\s*VALUES\s*\(", text, re.I | re.S)
    if not m:
        return None
    cols = [c.strip() for c in m.group(1).split(",") if c.strip()]
    depth, cur, exprs, i = 1, "", [], m.end()
    while i < len(text) and depth:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        if ch == "," and depth == 1:
            exprs.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    exprs.append(cur)
    counts = [e.count("%s") for e in exprs]
    if len(counts) != len(cols):
        return cols, None
    pos, acc = [], 0
    for c in counts:
        pos.append((acc, c))
        acc += c
    return cols, pos


def _parents(tree):
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            c._parent = n
    return tree


def _enclosing_function(node):
    while node is not None and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        node = getattr(node, "_parent", None)
    return node


def _sql_text(tree, arg, scope=None):
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    if isinstance(arg, ast.Name):
        for where in (scope, tree):
            if where is None:
                continue
            vals = [v for v in _assign_values(where, arg.id) if isinstance(v, ast.Constant) and isinstance(v.value, str)]
            if len(vals) == 1:
                return vals[0].value
    return None


def _appended_tuples(scope, name):
    return [c.args[0] for c in ast.walk(scope) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and c.func.attr == "append" and isinstance(c.func.value, ast.Name) and c.func.value.id == name
            and len(c.args) == 1 and isinstance(c.args[0], ast.Tuple)]


def _source_list_of(scope, name):
    """`name` is filled from a loop over another list (`for row, x in zip(rows, ...)` / `for row in rows`): that list."""
    for loop in (n for n in ast.walk(scope) if isinstance(n, ast.For)):
        tgt = {t.id for t in ast.walk(loop.target) if isinstance(t, ast.Name)}
        it = loop.iter
        if isinstance(it, ast.Call) and _called_name(it) == "zip" and it.args:
            it = it.args[0]
        if not isinstance(it, ast.Name):
            continue
        for c in ast.walk(loop):
            if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "append"
                    and isinstance(c.func.value, ast.Name) and c.func.value.id == name
                    and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id in tgt):
                return it.id
    return None


def bound_values(src, table, col, expect_statements=1):
    """(problems, [expression bound to `col`]) over every `execute/executemany(<INSERT INTO table ...>, params)` in `src`.
    The INSERT must name `col` and give it exactly one placeholder (comments in the SQL are ignored); `params` is a literal
    tuple, or a list of tuples the same function `.append`s (directly, or through a list filled from a loop over another
    such list). The expression returned is the element at the column's position in every such tuple; a star-arg at or
    before that position makes the binding unknowable and is a problem."""
    tree = _parents(ast.parse(src))
    problems, values, n = [], [], 0
    for call in (c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr in ("execute", "executemany") and len(c.args) >= 2):
        sql = _sql_text(tree, call.args[0], _enclosing_function(call))
        parsed = parse_insert(sql, table) if sql else None
        if parsed is None:
            continue
        n += 1
        cols, pos = parsed
        if col not in cols:
            problems.append(f"line {call.lineno}: INSERT INTO {table} does not name column {col!r} (columns: {cols})")
            continue
        if pos is None:
            problems.append(f"line {call.lineno}: INSERT INTO {table}: VALUES expressions do not match the column list")
            continue
        start, width = pos[cols.index(col)]
        if width != 1:
            problems.append(f"line {call.lineno}: {col} has {width} placeholders")
            continue
        params, scope = call.args[1], _enclosing_function(call)
        tuples = []
        if isinstance(params, ast.Tuple):
            tuples = [params]
        elif isinstance(params, ast.Name) and scope is not None:
            name, hops = params.id, 0
            while name and not _appended_tuples(scope, name) and hops < 3:
                name, hops = _source_list_of(scope, name), hops + 1
            tuples = _appended_tuples(scope, name) if name else []
        if not tuples:
            problems.append(f"line {call.lineno}: no literal parameter tuple feeds INSERT INTO {table}")
            continue
        for t in tuples:
            if any(isinstance(e, ast.Starred) for e in t.elts[: start + 1]):
                problems.append(f"line {t.lineno}: a star-arg at or before position {start} makes {col}'s binding unknowable")
            elif not any(isinstance(e, ast.Starred) for e in t.elts) and len(t.elts) != sum(w for _, w in pos):
                problems.append(f"line {t.lineno}: tuple has {len(t.elts)} elements for {sum(w for _, w in pos)} placeholders")
            else:
                values.append(t.elts[start])
    if n != expect_statements:
        problems.append(f"expected {expect_statements} INSERT INTO {table} execute call(s), found {n}")
    return problems, values


def tuple_bound_values(src, table, col):
    return bound_values(src, table, col)


def named_bound_values(src, table, col):
    """(problems, [value expression]) for a writer that binds `%(col)s` from dict rows: an INSERT INTO table statement text
    in `src` names `col` and binds `%(col)s`; every dict literal with key `col` contributes its value. (The SQL is checked as
    text and the dict literals by key; the flow from dict to execute goes through a helper call and is not traced.)"""
    tree = ast.parse(src)
    texts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and re.search(rf"INSERT\s+INTO\s+(?:public\.)?{re.escape(table)}\b", n.value, re.I)]
    if len(texts) != 1:
        return [f"expected exactly one INSERT INTO {table}, found {len(texts)}"], []
    sql = texts[0]
    head = re.search(r"\(([^)]*)\)\s*VALUES", sql, re.S)
    cols = [c.strip() for c in head.group(1).split(",")] if head else []
    if col not in cols:
        return [f"INSERT INTO {table} does not name column {col!r}"], []
    if f"%({col})s" not in sql:
        return [f"INSERT INTO {table} does not bind %({col})s"], []
    values = [v for d in (n for n in ast.walk(tree) if isinstance(n, ast.Dict)) for k, v in zip(d.keys, d.values)
              if isinstance(k, ast.Constant) and k.value == col]
    return ([] if values else [f"no dict row carries key {col!r}"]), values


def json_dumps_argument(expr):
    return expr.args[0] if _is_json_dumps(expr) else None


def check_tuple_json_from_builder(src, table, col, builder):
    """Every tuple bound to `col` is `json.dumps(<name assigned from builder(...)>)`; returns problems."""
    tree = ast.parse(src)
    problems, values = tuple_bound_values(src, table, col)
    for v in values:
        arg = json_dumps_argument(v)
        if arg is None or not isinstance(arg, ast.Name):
            problems.append(f"line {v.lineno}: {col} is not bound to json.dumps(<builder output>)")
        elif not any(_called_name(a) == builder for a in _assign_values(tree, arg.id)):
            problems.append(f"line {v.lineno}: {arg.id} bound to {col} is not assigned from {builder}(...)")
    return problems


def check_tuple_json_not_literal(src, table, col):
    """Every tuple bound to `col` is json.dumps(<a name or a subscript>), never a literal or constant; returns problems."""
    problems, values = tuple_bound_values(src, table, col)
    for v in values:
        arg = json_dumps_argument(v)
        if arg is None or not isinstance(arg, (ast.Name, ast.Subscript)):
            problems.append(f"line {v.lineno}: {col} is not bound to json.dumps(<computed value>)")
    return problems


# ───────────────────────── (3) the leaf at a JSON path is composed ─────────────────────────

def leaves_at_path(tree, roots, path):
    """Value nodes at `path` (tuple of keys) below the dict(s) the `roots` expressions can be."""
    current = [d for r in roots for d in dict_nodes(tree, r)]
    for i, key in enumerate(path):
        vals = dict_key_values(current, key)
        if i == len(path) - 1:
            return vals
        current = [d for v in vals for d in dict_nodes(tree, v)]
    return []


def composed_report(tree, roots, path):
    """[(lineno of the key, composed?)] for every leaf at `path`."""
    key = path[-1]
    current = [d for r in roots for d in dict_nodes(tree, r)]
    for k in path[:-1]:
        current = [d for v in dict_key_values(current, k) for d in dict_nodes(tree, v)]
    return sorted((kn.lineno, is_composed(tree, v)) for d in current
                  for kn, v in ((k, v) for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value == key))


# ───────────────────────── (4) a `[]` claim: the bound columns are only verbatim/slice/constant ─────────────────────────

_ALLOWED_PARAM_NODES = (ast.Name, ast.Constant, ast.Subscript, ast.Slice, ast.Load, ast.IfExp, ast.BoolOp, ast.Or, ast.And,
                        ast.List, ast.Tuple, ast.Dict, ast.Attribute, ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq,
                        ast.Call, ast.keyword)
_ALLOWED_CALLS = {"get", "dumps", "len"}     # d.get(...), json.dumps(...), len(...): reads/serialisation, not string building


def no_string_building_in_bound_params(src, func):
    """Inside `func`, the parameter tuple of every `cur.execute(sql, (params))` INSERT may only read values: names,
    constants, subscripts/slices, conditionals, `.get`, `json.dumps`. A `+`/`%`/f-string/.format/.join/any other call is
    string building on a bound column and is returned as a problem."""
    tree = ast.parse(src)
    fn = _function(tree, func)
    if fn is None:
        return [f"function {func} not found (or ambiguous)"]
    problems, seen = [], 0
    for call in (c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr in ("execute", "executemany")):
        if not call.args or not (isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str)
                                 and re.search(r"\bINSERT\b", call.args[0].value, re.I)):
            continue
        seen += 1
        params = call.args[1] if len(call.args) > 1 else None
        if not isinstance(params, (ast.Tuple, ast.List)):
            problems.append(f"line {call.lineno}: INSERT params are not a literal tuple")
            continue
        for node in (x for e in params.elts for x in ast.walk(e)):
            if isinstance(node, (ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context)):
                continue
            if isinstance(node, (ast.JoinedStr, ast.BinOp)):
                problems.append(f"line {node.lineno}: string building ({type(node).__name__}) on a bound column")
            elif isinstance(node, ast.Call):
                name = _called_name(node)
                if name not in _ALLOWED_CALLS:
                    problems.append(f"line {node.lineno}: call {name!r} on a bound column")
            elif not isinstance(node, _ALLOWED_PARAM_NODES):
                problems.append(f"line {node.lineno}: {type(node).__name__} on a bound column")
    if not seen:
        problems.append(f"{func} has no INSERT with parameters")
    return problems


def module_level_composition(src, name):
    """Module-level corpus literal `name`: any f-string/`+`/%/.format/.join inside it, or any module-level statement
    that mutates it after its definition. Returns problems."""
    tree = ast.parse(src)
    problems = []
    defs = [s for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign))
            and any(isinstance(t, ast.Name) and t.id == name for t in (s.targets if isinstance(s, ast.Assign) else [s.target]))]
    if len(defs) != 1:
        return [f"{name} is not defined exactly once at module level"]
    for n in ast.walk(defs[0]):
        if isinstance(n, ast.JoinedStr) or (isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod))) or (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("format", "join")):
            problems.append(f"line {n.lineno}: {name} literal builds text ({type(n).__name__})")
    for s in tree.body:
        if s is defs[0]:
            continue
        for n in ast.walk(s):
            if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Store):
                problems.append(f"line {n.lineno}: module-level statement rebinds {name}")
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == name and n.func.attr in ("append", "extend", "insert", "update", "pop", "remove")):
                problems.append(f"line {n.lineno}: module-level statement mutates {name}")
    return problems
