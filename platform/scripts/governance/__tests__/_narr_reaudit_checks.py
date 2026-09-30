"""_narr_reaudit_checks.py: structural (AST) checks for the E6.1 re-audit of the 13 DDL-evidence Narr declarations.

The 13 older declarations cited a column's DDL and the census ("the column is TEXT and a capability SELECTs it"), never the
writer code that builds the text. `_narr_writer_checks.py` covers writers that bind a literal parameter tuple / a dict the
same module builds; these writers bind differently:

  * a named-parameter INSERT (`%(col)s`) executed with a row dict that an EMITTER module builds (`conn.execute(_INSERT_SQL, row)`);
  * a `_make_row(..., summary=..., headline=...)` helper whose parameters become the dict's values, so the text is composed at
    every CALL site, not in the dict literal;
  * a positional INSERT fed by `rows.append((...))` tuples and `executemany(SQL, rows[i:i+N])`;
  * a record dataclass filled by an engine (`SodhanaRecord(recommendation_text=...)`) that the writer iterates.

Every helper answers from the syntax tree, offline. "Composed" means the expression string-builds from values: an f-string that
interpolates at least one value, `+`/`%` with a string operand, `.format`, `.join`. A constant (even an implicitly concatenated
multi-line one), a verbatim load, a slice or `str(x)` is not composed.
"""
from __future__ import annotations

import ast
import re


# ───────────────────────── composition classifier ─────────────────────────

def _is_str_operand(n):
    return (isinstance(n, ast.JoinedStr) or (isinstance(n, ast.Constant) and isinstance(n.value, str))
            or (isinstance(n, ast.BinOp) and (_is_str_operand(n.left) or _is_str_operand(n.right))))


def directly_composed(expr):
    """True when `expr` itself builds text (no following of names)."""
    for n in ast.walk(expr):
        if isinstance(n, ast.JoinedStr) and any(isinstance(v, ast.FormattedValue) for v in n.values):
            return True
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)) and (_is_str_operand(n.left) or _is_str_operand(n.right)):
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("format", "join"):
            return True
    return False


def parents(tree):
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            c._parent = n
    return tree


def enclosing_function(node):
    while node is not None and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        node = getattr(node, "_parent", None)
    return node


def functions_named(tree, name):
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]


def _called_name(call):
    f = call.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)


def _assignments(scope, name):
    """Values assigned to the bare name `name` inside `scope` (plain, annotated and augmented assignments)."""
    out = []
    for a in ast.walk(scope):
        if isinstance(a, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in a.targets):
            out.append(a.value)
        elif isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.target.id == name and a.value is not None:
            out.append(a.value)
    return out


def _param_index(fn, name):
    args = [a.arg for a in fn.args.posonlyargs + fn.args.args]
    return (args.index(name) if name in args else None), any(a.arg == name for a in fn.args.kwonlyargs)


def resolve_composed(tree, expr, _seen=None):
    """(problems, leaves): every terminal value `expr` can be must be composed.

    A composed expression is a leaf. A Name resolves through ALL its assignments in the enclosing function (every branch must
    compose), or, when it is a parameter, through the argument every call of that function passes. A call of a function in the
    module resolves through every `return`. An IfExp needs both branches composed; `a or b` is composed when either operand is
    (the `loaded_value or f"fallback"` default idiom: the verbatim-first shape is reported by the caller, not hidden here)."""
    _seen = _seen if _seen is not None else set()
    key = id(expr)
    if key in _seen:
        return [], []
    _seen.add(key)
    if isinstance(expr, ast.IfExp):
        pa, na = resolve_composed(tree, expr.body, _seen)
        pb, nb = resolve_composed(tree, expr.orelse, _seen)
        return pa + pb, na + nb
    if directly_composed(expr):
        return [], [expr]
    if isinstance(expr, ast.Name):
        fn = enclosing_function(expr)
        if fn is not None:
            values = _assignments(fn, expr.id)
            if values:
                probs, leaves = [], []
                for v in values:
                    p, n = resolve_composed(tree, v, _seen)
                    probs += p
                    leaves += n
                return probs, leaves
            idx, kwonly = _param_index(fn, expr.id)
            if idx is not None or kwonly:
                calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and _called_name(c) == fn.name and c is not expr]
                if not calls:
                    return [f"line {expr.lineno}: parameter {expr.id!r} of {fn.name} has no call site"], []
                probs, leaves = [], []
                for c in calls:
                    arg = next((k.value for k in c.keywords if k.arg == expr.id), None)
                    if arg is None and idx is not None:
                        off = 1 if fn.args.args and fn.args.args[0].arg in ("self", "cls") and isinstance(c.func, ast.Attribute) else 0
                        pos = idx - off
                        arg = c.args[pos] if 0 <= pos < len(c.args) else None
                    if arg is None:
                        probs.append(f"line {c.lineno}: call of {fn.name} does not pass {expr.id!r}")
                        continue
                    p, n = resolve_composed(tree, arg, _seen)
                    probs += p
                    leaves += n
                return probs, leaves
        return [f"line {expr.lineno}: name {expr.id!r} is not assigned a composed value"], []
    if isinstance(expr, ast.Call):
        fns = functions_named(tree, _called_name(expr) or "")
        if len(fns) == 1:
            probs, leaves = [], []
            rets = [r.value for r in ast.walk(fns[0]) if isinstance(r, ast.Return) and r.value is not None]
            if not rets:
                return [f"line {expr.lineno}: {fns[0].name} returns nothing"], []
            for r in rets:
                p, n = resolve_composed(tree, r, _seen)
                probs += p
                leaves += n
            return probs, leaves
    if isinstance(expr, ast.BoolOp):
        return [f"line {expr.lineno}: no operand of `or`/`and` composes text"], []
    return [f"line {getattr(expr, 'lineno', '?')}: {type(expr).__name__} is not composed text ({ast.unparse(expr)[:60]})"], []


# ───────────────────────── (1) the INSERT binds the declared column ─────────────────────────

def named_insert_problems(src, table, col, expect_statements=1):
    """The module holds exactly `expect_statements` string literal(s) `INSERT INTO table (...) VALUES (...)`; each names `col`
    in the column list and binds `%(col)s` exactly once."""
    tree = ast.parse(src)
    texts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and re.search(rf"INSERT\s+INTO\s+(?:public\.)?{re.escape(table)}\s*\(", n.value, re.I)]
    problems = []
    if len(texts) != expect_statements:
        problems.append(f"expected {expect_statements} INSERT INTO {table}, found {len(texts)}")
    for sql in texts:
        text = re.sub(r"--[^\n]*", "", sql)
        head = re.search(r"INSERT\s+INTO\s+(?:public\.)?\w+\s*\(([^)]*)\)\s*VALUES", text, re.I | re.S)
        cols = [c.strip() for c in head.group(1).split(",")] if head else []
        if col not in cols:
            problems.append(f"INSERT INTO {table} does not name column {col!r}")
        if text.count(f"%({col})s") != 1:
            problems.append(f"INSERT INTO {table} binds %({col})s {text.count(f'%({col})s')} times")
    return problems


def dict_literal_values(tree, key):
    """Value expressions of every dict literal in the module that carries the constant key."""
    return [v for d in ast.walk(tree) if isinstance(d, ast.Dict) for k, v in zip(d.keys, d.values)
            if isinstance(k, ast.Constant) and k.value == key]


def emitter_column_problems(emitter_src, col):
    """(problems, n_dict_sites, leaves): every dict literal carrying `col` holds a value that resolves to composed text."""
    tree = parents(ast.parse(emitter_src))
    values = dict_literal_values(tree, col)
    if not values:
        return [f"no dict literal carries key {col!r}"], 0, []
    problems, leaves = [], []
    for v in values:
        p, n = resolve_composed(tree, v)
        problems += p
        leaves += n
    return problems, len(values), leaves


def writer_uses_emitter_problems(writer_src, module_suffix, builders, insert_var="_INSERT_SQL"):
    """The writer imports each `builders` name from a module ending `module_suffix`, calls it, and executes
    `execute(<insert_var>, <row>)` (the row the emitter built goes to the INSERT unchanged)."""
    tree = ast.parse(writer_src)
    problems = []
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and (n.module or "").endswith(module_suffix)
                for a in n.names}
    called = {_called_name(c) for c in ast.walk(tree) if isinstance(c, ast.Call)}
    for b in builders:
        if b not in imported:
            problems.append(f"{b} is not imported from ...{module_suffix}")
        if b not in called:
            problems.append(f"{b} is never called")
    execs = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
             and c.func.attr in ("execute", "executemany") and len(c.args) >= 2
             and isinstance(c.args[0], ast.Name) and c.args[0].id == insert_var and isinstance(c.args[1], ast.Name)]
    if not execs:
        problems.append(f"no execute({insert_var}, <row>) call")
    return problems


# ───────────────────────── (2) kwargs of a record / positional tuples ─────────────────────────

def call_kwarg_values(tree, call_name, kwarg):
    return [k.value for c in ast.walk(tree) if isinstance(c, ast.Call) and _called_name(c) == call_name
            for k in c.keywords if k.arg == kwarg]


def classify_sites(tree, values):
    """([lineno of composed values], [lineno of non-composed values]) for each value expression, by resolve_composed."""
    comp, non = [], []
    for v in values:
        (non if resolve_composed(tree, v)[0] else comp).append(v.lineno)
    return sorted(comp), sorted(non)


def loop_var_from_builder_problems(src, var, builder):
    """`for <var> in <name>` where <name> is assigned from `builder(...)` in the same function."""
    tree = parents(ast.parse(src))
    loops = [n for n in ast.walk(tree) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == var
             and isinstance(n.iter, ast.Name)]
    if not loops:
        return [f"no `for {var} in <name>` loop"]
    problems = []
    for lp in loops:
        fn = enclosing_function(lp)
        if not any(isinstance(v, ast.Call) and _called_name(v) == builder for v in _assignments(fn, lp.iter.id)):
            problems.append(f"line {lp.lineno}: {lp.iter.id} is not assigned from {builder}(...)")
    return problems


def assigned_from_call_problems(src, var, builder):
    tree = parents(ast.parse(src))
    hits = [a for a in ast.walk(tree) if isinstance(a, ast.Assign) and isinstance(a.value, ast.Call)
            and _called_name(a.value) == builder
            and any(isinstance(n, ast.Name) and n.id == var for t in a.targets for n in ast.walk(t))]
    return [] if hits else [f"{var} is not assigned from {builder}(...)"]


def positional_insert_index(sql, table, col):
    """Index of `col` in `INSERT INTO table (cols)`; the VALUES expressions must be one placeholder per column."""
    text = re.sub(r"--[^\n]*", "", sql)
    m = re.search(rf"INSERT\s+INTO\s+(?:public\.)?{re.escape(table)}\s*\(([^)]*)\)\s*VALUES", text, re.I | re.S)
    if not m:
        return None
    cols = [c.strip() for c in m.group(1).split(",") if c.strip()]
    return cols.index(col) if col in cols else None


def appended_tuple_elements(src, func, list_name, index, width=None):
    """(problems, [element expression at `index`]) over every `list_name.append((...))` in function `func`; the tuples must be
    literal and star-free before `index` (and, when `width` is given, exactly as wide as the INSERT's column list)."""
    tree = parents(ast.parse(src))
    fns = functions_named(tree, func)
    if len(fns) != 1:
        return [f"function {func} not found (or ambiguous)"], []
    problems, out = [], []
    for c in ast.walk(fns[0]):
        if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "append"
                and isinstance(c.func.value, ast.Name) and c.func.value.id == list_name and len(c.args) == 1):
            t = c.args[0]
            if not isinstance(t, ast.Tuple):
                problems.append(f"line {c.lineno}: appended value is not a literal tuple")
            elif any(isinstance(e, ast.Starred) for e in t.elts[: index + 1]):
                problems.append(f"line {t.lineno}: star-arg at or before position {index}")
            elif len(t.elts) <= index:
                problems.append(f"line {t.lineno}: tuple too short for position {index}")
            elif width is not None and len(t.elts) != width:
                problems.append(f"line {t.lineno}: tuple has {len(t.elts)} elements for {width} INSERT columns")
            else:
                out.append(t.elts[index])
    if not out:
        problems.append(f"no {list_name}.append((...)) tuples in {func}")
    return problems, out


def executemany_feeds_problems(src, func, sql_var, list_name):
    """Inside `func`, `executemany(<sql_var>, <list_name>[...])` (a slice of the list the tuples were appended to)."""
    tree = ast.parse(src)
    fns = functions_named(tree, func)
    if len(fns) != 1:
        return [f"function {func} not found (or ambiguous)"]
    for c in ast.walk(fns[0]):
        if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "executemany" and len(c.args) >= 2
                and isinstance(c.args[0], ast.Name) and c.args[0].id == sql_var):
            a = c.args[1]
            root = a.value if isinstance(a, ast.Subscript) else a
            if isinstance(root, ast.Name) and root.id == list_name:
                return []
    return [f"no executemany({sql_var}, {list_name}[...]) in {func}"]


def sql_literal_assigned(src, func, name):
    tree = ast.parse(src)
    fns = functions_named(tree, func)
    if len(fns) != 1:
        return None
    vals = [v.value for v in _assignments(fns[0], name) if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    return vals[0] if len(vals) == 1 else None


def tuple_return_elements(tree, func, index):
    """[(lineno, expr)] for element `index` of every tuple `return` of function `func`."""
    parents(tree)
    fns = functions_named(tree, func)
    if len(fns) != 1:
        return []
    return [(r.value.elts[index].lineno, r.value.elts[index]) for r in ast.walk(fns[0])
            if isinstance(r, ast.Return) and isinstance(r.value, ast.Tuple) and len(r.value.elts) > index]
