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
    return bound_values_tree(_parents(ast.parse(src)), table, col, expect_statements)


def bound_values_tree(tree, table, col, expect_statements=1):
    """bound_values over an already parsed tree (with parent links)."""
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


# ───────────────────────── (3b) `key[*]` array-element leaves (grammar 1.6.0) ─────────────────────────

def dataclass_fields(tree, cls):
    """Field names of class `cls` in declaration order (annotated class-body names); None when `cls` is not defined once."""
    defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls]
    if len(defs) != 1:
        return None
    return [s.target.id for s in defs[0].body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]


def constructor_values(tree, cls, field):
    """[(lineno, expression)] bound to `field` in every call `cls(...)` in `tree`: the keyword of that name, else the
    positional argument at the field's declaration index. A call that does not bind the field (a default, a star-arg
    before its index) contributes (lineno, None) so the caller cannot mistake silence for a value."""
    fields = dataclass_fields(tree, cls)
    if fields is None or field not in fields:
        return []
    idx, out = fields.index(field), []
    for c in (n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == cls):
        kw = [k.value for k in c.keywords if k.arg == field]
        if kw:
            out.append((c.lineno, kw[0]))
        elif idx < len(c.args) and not any(isinstance(a, ast.Starred) for a in c.args[: idx + 1]):
            out.append((c.lineno, c.args[idx]))
        else:
            out.append((c.lineno, None))
    return sorted(out, key=lambda t: t[0])


def list_element_dicts(tree, expr, scope=None, _seen=None):
    """Dict literals that can be ELEMENTS of the list `expr` denotes: a list literal's dict elements, a comprehension's
    element, every assignment of a Name (inside `scope` when given, else `tree`) and every `name.append(<dict>)` on it."""
    _seen = _seen if _seen is not None else set()
    if id(expr) in _seen:
        return []
    _seen.add(id(expr))
    out = []
    if isinstance(expr, ast.List):
        for e in expr.elts:
            out += [e] if isinstance(e, ast.Dict) else []
    elif isinstance(expr, (ast.ListComp, ast.GeneratorExp)):
        out += [expr.elt] if isinstance(expr.elt, ast.Dict) else []
    elif isinstance(expr, ast.Name):
        where = scope if scope is not None else tree
        for v in _assign_values(where, expr.id):
            out += list_element_dicts(tree, v, scope, _seen)
        for c in ast.walk(where):
            if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "append"
                    and isinstance(c.func.value, ast.Name) and c.func.value.id == expr.id
                    and len(c.args) == 1 and isinstance(c.args[0], ast.Dict)):
                out.append(c.args[0])
    return out


def terminal_strings(tree, exprs, attr_classes):
    """[(lineno, composed?)] for the string expressions `exprs` can end up as. An attribute read `x.attr` whose `attr` is a
    field of a dataclass named in `attr_classes` ({attr: class}) is followed to every constructor call of that class and
    reports the expression bound there; a None (unbound) constructor argument is a problem marker (lineno, None)."""
    out = []
    for e in exprs:
        if isinstance(e, ast.Attribute) and e.attr in attr_classes:
            for ln, v in constructor_values(tree, attr_classes[e.attr], e.attr):
                out.append((ln if v is None else v.lineno, None if v is None else is_composed(tree, v)))
        else:
            out.append((e.lineno, is_composed(tree, e)))
    return sorted(set(out), key=lambda t: (t[0], str(t[1])))


def composed_keys(tree, dicts):
    """Keys whose value expression, in any of the dict literals, builds text (f-string, `+`/`%`, .format, .join)."""
    return {k.value for d in dicts for k, v in zip(d.keys, d.values)
            if isinstance(k, ast.Constant) and isinstance(k.value, str) and is_composed(tree, v)}


# ───────────────────────── (3c) inventory of every text-building expression (for `[]` claims over provenance text) ─────────────────────────

def composed_inventory(node, kinds=("fstr", "binop", "format", "join")):
    """[(lineno, kind, unparsed source)] of every text-building expression under `node`: f-string (`fstr`, a format-spec
    sub-f-string is not counted), `+`/`%` (`binop`), `.format(...)` (`format`), `.join(...)` (`join`). Sorted by line."""
    specs = {id(v.format_spec) for v in ast.walk(node) if isinstance(v, ast.FormattedValue) and v.format_spec is not None}
    out = []
    for n in ast.walk(node):
        kind = None
        if isinstance(n, ast.JoinedStr) and id(n) not in specs:
            kind = "fstr"
        elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
            kind = "binop"
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("format", "join"):
            kind = n.func.attr
        if kind in kinds:
            out.append((n.lineno, kind, ast.unparse(n)))
    return sorted(out, key=lambda t: (t[0], t[1], t[2]))


def fstring_interpolations(node):
    """[(unparsed expression, has format spec or conversion)] for each `{...}` of an f-string node: a `{x:.2f}` / `{x!r}`
    shapes a value (a number, a repr); a bare name is a pointer/identifier read."""
    return [(ast.unparse(v.value), v.format_spec is not None or v.conversion != -1)
            for v in node.values if isinstance(v, ast.FormattedValue)]


# ───────────────────────── (3d) census of every site that sets a `citation_human` value ─────────────────────────

CITATION_PARAMS = ("citation_human", "citation", "cite", "chum", "human")


def _text_composed(node):
    return any(isinstance(x, ast.JoinedStr) or (isinstance(x, ast.BinOp) and isinstance(x.op, (ast.Add, ast.Mod)))
               or (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr in ("format", "join"))
               for x in ast.walk(node))


def citation_sites(tree):
    """[(lineno, how, kind, unparsed)] for every place the module sets a citation_human value. `how`: `dict` (a dict literal
    key "citation_human"), `kw` (a keyword argument citation_human=), `arg` (the argument bound to a citation-named parameter
    of a function defined in the module: citation_human / citation / cite / chum / human), `var` (an assignment to such a
    name). `kind`: `composed` (the value, or a name it is assigned from in the module, builds text: f-string, `+`, `%`,
    .format, .join, or a call to a module function that does), `const` (a string constant or a name assigned only constants),
    `passthrough` (a parameter forwarded as is: counted where the caller binds it), `other` (a read, a subscript, a call to
    something that is not a module function). Pure syntax: the caller decides which composed sites state a value."""
    fdefs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assigns = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    assigns.setdefault(tg.id, []).append(n.value)
    helpers = {}
    for f in fdefs.values():
        for i, a in enumerate(f.args.args):
            if a.arg in CITATION_PARAMS:
                helpers.setdefault(f.name, []).append((a.arg, i))
        for a in f.args.kwonlyargs:
            if a.arg in CITATION_PARAMS:
                helpers.setdefault(f.name, []).append((a.arg, None))

    def params_of(node):
        while node is not None and not isinstance(node, ast.FunctionDef):
            node = getattr(node, "_parent", None)
        return {a.arg for a in node.args.args + node.args.kwonlyargs} if node is not None else set()

    def classify(v):
        if _text_composed(v):
            return "composed"
        if isinstance(v, ast.Constant):
            return "const"
        if isinstance(v, ast.Name):
            if v.id in params_of(v):
                return "passthrough"
            vals = assigns.get(v.id, [])
            if any(_text_composed(x) for x in vals):
                return "composed"
            return "const" if vals and all(isinstance(x, ast.Constant) for x in vals) else "other"
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in fdefs:
            return "composed" if _text_composed(fdefs[v.func.id]) else "other"
        return "other"

    def is_key(k):
        """a constant key spelled citation_human in any case, or a name every assignment of which is such a constant"""
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            return k.value.lower() == "citation_human"
        if isinstance(k, ast.Name):
            vals = assigns.get(k.id, [])
            return bool(vals) and all(isinstance(x, ast.Constant) and isinstance(x.value, str) and x.value.lower() == "citation_human"
                                      for x in vals)
        return False

    _parents(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if k is not None and is_key(k):
                    out.append((v.lineno, "dict", classify(v), ast.unparse(v)))
        elif isinstance(n, ast.keyword) and n.arg == "citation_human":
            out.append((n.value.lineno, "kw", classify(n.value), ast.unparse(n.value)))
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id in ("citation_human", "chum", "chuman", "l1_citation_human"):
                    out.append((n.lineno, "var", classify(n.value), ast.unparse(n.value)))
                if isinstance(tg, ast.Subscript) and is_key(tg.slice):
                    out.append((n.value.lineno, "subkey", classify(n.value), ast.unparse(n.value)))
                if isinstance(tg, ast.Attribute) and tg.attr.lower() == "citation_human":
                    out.append((n.value.lineno, "attr", classify(n.value), ast.unparse(n.value)))
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "setdefault"
              and len(n.args) >= 2 and is_key(n.args[0])):
            out.append((n.args[1].lineno, "setdefault", classify(n.args[1]), ast.unparse(n.args[1])))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in helpers:
            for pname, idx in helpers[n.func.id]:
                v = next((k.value for k in n.keywords if k.arg == pname), None)
                if v is None and idx is not None and idx < len(n.args):
                    v = n.args[idx]
                if v is not None:
                    out.append((v.lineno, "arg", classify(v), ast.unparse(v)))
    for _, table in citation_inserts(tree):          # a literal parameter tuple of an INSERT that names the column: positional
        if table != "<columns>":
            for v in bound_values_tree(tree, table, "citation_human", expect_statements=-1)[1]:
                out.append((v.lineno, "tuple", classify(v), ast.unparse(v)))
    return sorted(set(out), key=lambda t: (t[0], t[1], t[3]))


def site_interpolations(tree, kind="composed"):
    """Sorted set of the `{...}` expressions interpolated by the citation sites of `kind`. A site that is a bare Name is
    followed to the f-strings it is assigned from in the module; a site that calls a module function is followed to the
    f-strings of that function."""
    fdefs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    out = set()

    def grab(node):
        for x in ast.walk(node):
            if isinstance(x, ast.JoinedStr):
                out.update(e for e, _ in fstring_interpolations(x))

    for _, _, k, u in citation_sites(tree):
        if k != kind:
            continue
        node = ast.parse(u, mode="eval").body
        grab(node)
        if isinstance(node, ast.Name):
            for v in _assign_values(tree, node.id):
                grab(v)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in fdefs:
            grab(fdefs[node.func.id])
    return sorted(out)


DATUM_KEYS = frozenset({"fact_value_text", "fact_value_num", "fact_value_jsonb", "configuration_jsonb", "fact_value"})


_DATUM_INDEX = {}


def _datum_index(tree):
    """Per-tree index (built once): name -> value expressions it is bound from (assignments, loop and comprehension
    iterables, caller-bound arguments of a parameter), and module function name -> def."""
    idx = _DATUM_INDEX.get(id(tree))
    if idx is not None and idx[0] is tree:
        return idx[1], idx[2]
    binds, fdefs = {}, {}
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            fdefs[n.name] = n
        if isinstance(n, ast.Assign):
            for tt in n.targets:
                for t in ast.walk(tt):
                    if isinstance(t, ast.Name):
                        binds.setdefault(t.id, []).append(n.value)
        elif isinstance(n, (ast.For, ast.comprehension)):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name):
                    binds.setdefault(t.id, []).append(n.iter)
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in fdefs:
            f = fdefs[c.func.id]
            params = [p.arg for p in f.args.args + f.args.kwonlyargs]
            for i, p in enumerate(params):
                v = next((k.value for k in c.keywords if k.arg == p), None)
                if v is None and i < len(c.args) and not isinstance(c.args[i], ast.Starred):
                    v = c.args[i]
                if v is not None:
                    binds.setdefault(p, []).append(v)
    _DATUM_INDEX[id(tree)] = (tree, binds, fdefs)
    return binds, fdefs


def reads_datum(tree, node, _seen=None):
    """True when the value of expression `node` depends on a fact DATUM (a read of fact_value_text / fact_value_num /
    fact_value_jsonb / configuration_jsonb): a string constant naming one anywhere in the expression, in a value a name it
    uses is bound from (assignment, loop iterable, the argument a caller binds to a parameter), or in the body of a module
    function it calls. A constant, a fixed-list ordinal or an identity key (fact_subject, a graha code) does not. It follows
    the data dependence, not the variable name, so `name` cannot hide a computed status."""
    binds, fdefs = _datum_index(tree)
    if _seen is None:                      # top-level search: nodes already fully explored with no datum found are not re-walked
        neg = _DATUM_NEG.setdefault(id(tree), set())
        seen = set()
        found = _reads_datum(tree, node, seen, binds, fdefs, neg)
        if not found:
            neg |= seen
        return found
    return _reads_datum(tree, node, _seen, binds, fdefs, set())


_DATUM_NEG = {}


def _reads_datum(tree, node, _seen, binds, fdefs, neg):
    if id(node) in _seen or id(node) in neg:
        return False
    _seen.add(id(node))
    for x in ast.walk(node):
        if isinstance(x, ast.Constant) and isinstance(x.value, str) and x.value in DATUM_KEYS:
            return True
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id in fdefs:
            if _reads_datum(tree, fdefs[x.func.id], _seen, binds, fdefs, neg):
                return True
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
            if any(_reads_datum(tree, v, _seen, binds, fdefs, neg) for v in binds.get(x.id, [])):
                return True
    return False


def interpolation_datum_flags(tree, kind="composed"):
    """{interpolated expression: reads_datum} over every citation site of `kind` (names followed as in site_interpolations)."""
    fdefs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    out = {}

    def grab(node):
        for x in ast.walk(node):
            if isinstance(x, ast.JoinedStr):
                for v in x.values:
                    if isinstance(v, ast.FormattedValue):
                        out[ast.unparse(v.value)] = out.get(ast.unparse(v.value), False) or reads_datum(tree, v.value)

    for _, _, k, u in citation_sites(tree):
        if k != kind:
            continue
        node = ast.parse(u, mode="eval").body
        grab(node)
        if isinstance(node, ast.Name):
            for v in _assign_values(tree, node.id):
                grab(v)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in fdefs:
            grab(fdefs[node.func.id])
    return out


_INSERT_COLS_RE = re.compile(r"INSERT\s+INTO\s+(?:public\.)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)", re.I | re.S)


def citation_inserts(tree):
    """[(lineno, table)] of every string (constant, or the constant parts of an f-string) in the module holding an
    `INSERT INTO table (cols)` whose column list names citation_human, plus [(lineno, "<columns>")] for every list/tuple
    constant of column names that holds citation_human (a writer that builds its INSERT from a column list)."""
    out = []
    for n in ast.walk(tree):
        text = None
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            text = n.value
        elif isinstance(n, ast.JoinedStr):
            text = "".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
        if text:
            for m in _INSERT_COLS_RE.finditer(_strip_sql_comments(text)):
                if "citation_human" in m.group(2):
                    out.append((n.lineno, m.group(1)))
        if isinstance(n, (ast.List, ast.Tuple)) and n.elts and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.elts) \
                and any(e.value == "citation_human" for e in n.elts):
            out.append((n.lineno, "<columns>"))
    return sorted(set(out))


# ───────────────────────── (4) a `[]` claim: the bound columns are only verbatim/slice/constant ─────────────────────────

_ALLOWED_PARAM_NODES = (ast.Name, ast.Constant, ast.Subscript, ast.Slice, ast.Load, ast.IfExp, ast.BoolOp, ast.Or, ast.And,
                        ast.List, ast.Tuple, ast.Dict, ast.Attribute, ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq,
                        ast.Call, ast.keyword)
_ALLOWED_CALLS = {"get", "dumps", "len"}     # d.get(...), json.dumps(...), len(...): reads/serialisation, not string building


def _insert_sql_text(node):
    """The SQL text of an `execute` first argument when it is a string constant or an f-string (its constant parts)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    return None


def no_string_building_in_bound_params(src, func, extra_calls=()):
    """Inside `func`, the parameter tuple of every `cur.execute(sql, (params))` INSERT may only read values: names,
    constants, subscripts/slices, conditionals, `.get`, `json.dumps`. A `+`/`%`/f-string/.format/.join/any other call is
    string building on a bound column and is returned as a problem. `extra_calls` names helper functions (defined in the
    same module, inventoried separately by the caller) whose call is allowed on a bound column."""
    tree = ast.parse(src)
    fn = _function(tree, func)
    if fn is None:
        return [f"function {func} not found (or ambiguous)"]
    problems, seen = [], 0
    for call in (c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr in ("execute", "executemany")):
        sql = _insert_sql_text(call.args[0]) if call.args else None
        if not (sql and re.search(r"\bINSERT\b", sql, re.I)):
            continue
        seen += 1
        params = call.args[1] if len(call.args) > 1 else None
        if not isinstance(params, (ast.Tuple, ast.List)):
            problems.append(f"line {call.lineno}: INSERT params are not a literal tuple")
            continue
        for node in (x for e in params.elts for x in ast.walk(e)):
            if isinstance(node, (ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context)):
                continue
            if isinstance(node, ast.JoinedStr):
                problems.append(f"line {getattr(node, "lineno", call.lineno)}: string building (f-string) on a bound column")
            elif isinstance(node, ast.Call):
                name = _called_name(node)
                if name not in _ALLOWED_CALLS and name not in extra_calls:
                    problems.append(f"line {getattr(node, "lineno", call.lineno)}: call {name!r} on a bound column")
            elif not isinstance(node, _ALLOWED_PARAM_NODES):
                problems.append(f"line {getattr(node, "lineno", call.lineno)}: {type(node).__name__} on a bound column")
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
