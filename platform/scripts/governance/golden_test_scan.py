"""Static verification of a DECLARED golden-value test for an asset's narration builder (Narr.fidelity_test).

E5.7 Worker E (SS N-150 R7). CLAUDE.md N.7 item 5: "verified fact != verified prose": a narration layer that assembles a sentence
from facts needs a test that asserts the BUILT sentence against an independently stated expected value. Test names alone prove
nothing, so the asset DECLARES `fidelity_tests: [{test: "<repo path>::<test name>", covers: [<prose entries>]}]` and this module
verifies each by reading the test's source (ast, nothing is run):

  1. the file exists among the discovered sidecar tests and the named test function exists in it, not skipped / xfailed;
  2. it calls the builder (a name imported from a module the declaration's evidence cites);
  3. it contains a golden assertion: an EQUALITY (`assert a == b`, `assertEqual(a, b)` and the assertDictEqual / assertListEqual /
     assertTupleEqual / assertMultiLineEqual forms) in which one side is derived from the builder call (the call itself, a name
     assigned from it, or a subscript / attribute / method result of those: forward data-flow in the test function) and the OTHER
     side is a LITERAL (str / number / container of literals, a module-level constant bound to one, or a pytest.mark.parametrize
     value that is one) that contains NO builder-derived name and NO builder call, and that carries prose (a string of at least
     MIN_WORDS words and MIN_CHARS characters);
  4. every entry in `covers` is referenced (its leaf: the column, or the last key of a JSON path) inside the golden assertion or the
     assignments that define the names it uses.

`isinstance`, `len(x) > 0`, `assert x`, `in` / startswith containment, `assert built == build(...)` (expected produced by the
builder), and a literal that is only a label are NOT golden. PASS needs every declared prose entry covered by a verified test.
The expected literal's sha256 and the assertion line are echoed so a reader can see WHICH sentence is pinned.
"""
from __future__ import annotations

import ast
import hashlib
import re

MIN_WORDS = 2
POISON_MIN = 10          # a recorder class is 'pre-seeded' when it shares a run of this many characters with an expected string, whatever way the sentence was split or reached
MIN_CHARS = 10
_EQ_CALLS = ("assertEqual", "assertEquals", "assertDictEqual", "assertListEqual", "assertTupleEqual", "assertMultiLineEqual", "assert_equal")
_GENERIC_LEAVES = ("statement", "reason", "text", "summary", "description", "note")


def _split_ref(ref: str):
    """('path.py', ['Class', 'test_name']) from 'path.py::Class::test_name' / 'path.py::test_name'."""
    parts = ref.split("::")
    return parts[0], parts[1:]


def _prose_bearing(node) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            t = " ".join(n.value.split())
            if len(t) >= MIN_CHARS and len(t.split(" ")) >= MIN_WORDS:
                return True
    return False


def _names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _picked_keys(node, is_builder_call=None):
    """The names a compared operand uses to PICK a value out of the built output, EXACTLY: a constant subscript key (`row["k"]`, a chain `row["a"][0]["k"]`), the first constant argument of `.get("k")` /
    `.pop("k")`, an attribute name (`row.k`) and a plain name (`k = build(...)`). Not call keyword names (an INPUT of the builder), not sentence text, and never a token of a longer name
    (a variable `citation` does not cover `citation_human`). The arguments of a BUILDER call are its INPUTS, so the walk does not enter them: `build_narration(citation_human)["note"]` picks `note`."""
    out = set()

    def walk(n):
        if is_builder_call is not None and isinstance(n, ast.Call) and is_builder_call(n):
            walk(n.func)                                  # the callee only (`mod.build`): never `Call.args` / `Call.keywords`
            return
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            out.add(n.slice.value)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("get", "pop") and n.args \
                and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            out.add(n.args[0].value)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Name):
            out.add(n.id)
        for c in ast.iter_child_nodes(n):
            walk(c)

    walk(node)
    return out


def _dict_values_by_key(node, depth=0):
    """{key: [value nodes]} of every constant-keyed dict display inside the literal `node`, at any depth."""
    out = {}
    if depth > 6:
        return out
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.setdefault(k.value, []).append(v)
            out_sub = _dict_values_by_key(v, depth + 1)
            for kk, vv in out_sub.items():
                out.setdefault(kk, []).extend(vv)
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for e in node.elts:
            for kk, vv in _dict_values_by_key(e, depth + 1).items():
                out.setdefault(kk, []).extend(vv)
    return out


def _target_names(assign):
    return {x.id for t in assign.targets for x in ast.walk(t) if isinstance(x, ast.Name)}


_UNK = object()
_CMP = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b, ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b, ast.Is: lambda a, b: a is b, ast.IsNot: lambda a, b: a is not b, ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}


def _const_eval(node, depth=0):
    """The Python value of a CONSTANT expression (literals, containers of literals, `not`, `and` / `or`, comparisons, unary minus), else _UNK."""
    if depth > 8:
        return _UNK
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        vals = [_const_eval(e, depth + 1) for e in node.elts]
        if any(v is _UNK for v in vals):
            return _UNK
        return tuple(vals) if not isinstance(node, ast.Set) else frozenset(vals)
    if isinstance(node, ast.Dict):
        return {} if not node.keys else _UNK
    if isinstance(node, ast.UnaryOp):
        v = _const_eval(node.operand, depth + 1)
        if v is _UNK:
            return _UNK
        try:
            return (not v) if isinstance(node.op, ast.Not) else (-v) if isinstance(node.op, ast.USub) else (+v) if isinstance(node.op, ast.UAdd) else _UNK
        except Exception:
            return _UNK
    if isinstance(node, ast.BoolOp):
        vals = [_const_eval(e, depth + 1) for e in node.values]
        if any(v is _UNK for v in vals):
            return _UNK
        if isinstance(node.op, ast.And):
            for v in vals:
                if not v:
                    return v
            return vals[-1]
        for v in vals:
            if v:
                return v
        return vals[-1]
    if isinstance(node, ast.Compare):
        left = _const_eval(node.left, depth + 1)
        res = True
        for op, c in zip(node.ops, node.comparators):
            right = _const_eval(c, depth + 1)
            fn = _CMP.get(type(op))
            if left is _UNK or right is _UNK or fn is None:
                return _UNK
            try:
                res = res and fn(left, right)
            except Exception:
                return _UNK
            left = right
        return res
    return _UNK


def _const_truth(test):
    """True / False for a constant test (`if False:`, `if 0:`, `if not True:`, `if 0 == 1:`, `if 1 and 0:`), None otherwise."""
    v = _const_eval(test)
    return None if v is _UNK else bool(v)


_SWALLOW = ("AssertionError", "Exception", "BaseException")


def _exc_names(t) -> list:
    """The final names of an exception expression: `AssertionError`, `builtins.AssertionError`, `(ValueError, builtins.AssertionError)`."""
    if t is None:
        return []
    out = []
    for x in ast.walk(t):
        if isinstance(x, ast.Name):
            out.append(x.id)
        elif isinstance(x, ast.Attribute):
            out.append(x.attr)
    return out


def _swallows(handler) -> bool:
    t = handler.type
    names = _exc_names(t) if t is not None else ["BaseException"]
    return any(n in _SWALLOW for n in names) and not any(isinstance(x, ast.Raise) for x in ast.walk(handler))


def _expects_failure(w) -> bool:
    for it in w.items:
        c = it.context_expr
        if isinstance(c, ast.Call):
            nm = c.func.attr if isinstance(c.func, ast.Attribute) else c.func.id if isinstance(c.func, ast.Name) else ""
            if nm in ("raises", "assertRaises", "assertRaisesRegex", "warns", "assertWarns", "expectedFailure"):
                return True
            if nm == "suppress" and any(n in _SWALLOW for a in c.args for n in _exc_names(a)):
                return True                               # contextlib.suppress(AssertionError): an assertion failure inside is swallowed
    return False


_TERMINATORS = ("skip", "skipTest", "fail", "exit", "_exit", "importorskip")


def _terminates(body) -> bool:
    """The statement list ends every path it takes in a return / raise / continue / break or a skip / fail call (`self.skipTest(...)`, `pytest.skip(...)`)."""
    for st in body:
        if isinstance(st, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
            return True
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
            f = st.value.func
            nm = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
            if nm in _TERMINATORS:
                return True
        if isinstance(st, ast.If):
            t = _const_truth(st.test)
            if (t is True and _terminates(st.body)) or (t is False and _terminates(st.orelse)) or (t is None and _terminates(st.body) and _terminates(st.orelse)):
                return True
    return False


def _empty_iter(it) -> bool:
    """A `for` over a constant empty iterable (`[]`, `()`, `{}`, `""`, `range(0)`): its body never runs."""
    if isinstance(it, ast.Call) and isinstance(it.func, ast.Name) and it.func.id == "range" and it.args:
        vals = [_const_eval(a) for a in it.args]
        if all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
            return len(range(*vals)) == 0
        return False
    v = _const_eval(it)
    return v is not _UNK and hasattr(v, "__len__") and len(v) == 0


def reachable(body):
    """The statements of `body` that RUN: recursing through if / for / while / with / try, but not into nested function or class definitions, not into a branch a constant test excludes, not
    after a return / raise / continue / break, not into a `with pytest.raises(...)` body (an assertion there is expected to fail) and not into a `try` body whose handler swallows AssertionError."""
    for st in body:
        yield st
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(st, ast.If):
            t = _const_truth(st.test)
            if t is not False:
                yield from reachable(st.body)
            if t is not True:
                yield from reachable(st.orelse)
        elif isinstance(st, (ast.For, ast.AsyncFor)):
            if not _empty_iter(st.iter):
                yield from reachable(st.body)
            yield from reachable(st.orelse)
        elif isinstance(st, ast.While):
            if _const_truth(st.test) is not False:
                yield from reachable(st.body)
            yield from reachable(st.orelse)
        elif isinstance(st, (ast.With, ast.AsyncWith)):
            if not _expects_failure(st):
                yield from reachable(st.body)
        elif isinstance(st, ast.Try):
            if not any(_swallows(h) for h in st.handlers):
                yield from reachable(st.body)
            for h in st.handlers:
                yield from reachable(h.body)
            yield from reachable(st.orelse)
            yield from reachable(st.finalbody)
        if _terminates([st]):
            break                                         # nothing after a return / raise / skip, nor after an `if True:` / both-branch exit


_COMPOUND_BODY = ("body", "orelse", "finalbody", "handlers", "cases")


def _own_nodes(st):
    """Every ast node of statement `st` itself: all of a simple statement, only the header expressions of a compound one."""
    if not isinstance(st, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        yield from ast.walk(st)
        return
    if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    for name, val in ast.iter_fields(st):
        if name in _COMPOUND_BODY:
            continue
        for v in (val if isinstance(val, list) else [val]):
            if isinstance(v, ast.AST):
                yield from ast.walk(v)


_PATCHERS = ("setattr", "patch", "object", "setitem", "multiple", "dict")


def _patches_builder(fn, called_names) -> str | None:
    """A reason when the test replaces the builder it claims to test (monkeypatch.setattr / mock.patch / patch.object / `mod.builder = ...`): the expected literal could then be what the stub returns."""
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            nm = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id if isinstance(n.func, ast.Name) else ""
            if nm in _PATCHERS:
                for a in list(n.args) + [k.value for k in n.keywords]:
                    for c in ast.walk(a):
                        if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value.rsplit(".", 1)[-1] in called_names:
                            return f"line {n.lineno}: the test patches the builder `{c.value.rsplit('.', 1)[-1]}` it calls"
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and t.attr in called_names:
                    return f"line {n.lineno}: the test assigns over the builder `{t.attr}` it calls"
    for d in fn.decorator_list:
        for c in ast.walk(d):
            if isinstance(c, ast.Constant) and isinstance(c.value, str) and "." in c.value and c.value.rsplit(".", 1)[-1] in called_names \
                    and ast.unparse(d).startswith(("patch", "mock.patch", "unittest.mock.patch")):
                return f"line {d.lineno}: the test is decorated with a patch of the builder `{c.value.rsplit('.', 1)[-1]}`"
    return None


def _parametrized(fn) -> dict:
    """{param name: [value nodes]} from literal @pytest.mark.parametrize decorators; a param with any non-literal value is omitted."""
    out = {}
    for d in fn.decorator_list:
        if not (isinstance(d, ast.Call) and ast.unparse(d.func).endswith("parametrize") and len(d.args) >= 2):
            continue
        names_node, vals = d.args[0], d.args[1]
        if isinstance(names_node, ast.Constant) and isinstance(names_node.value, str):
            names = [x.strip() for x in names_node.value.split(",") if x.strip()]
        elif isinstance(names_node, (ast.List, ast.Tuple)) and all(isinstance(e, ast.Constant) for e in names_node.elts):
            names = [e.value for e in names_node.elts]
        else:
            continue
        if not isinstance(vals, (ast.List, ast.Tuple)):
            continue
        cols = {n: [] for n in names}
        ok = True
        for v in vals.elts:
            if len(names) == 1:
                cols[names[0]].append(v)
            elif isinstance(v, (ast.Tuple, ast.List)) and len(v.elts) == len(names):
                for n, e in zip(names, v.elts):
                    cols[n].append(e)
            else:
                ok = False
        if ok:
            out.update(cols)
    return out


def _flat_concat(n):
    """The text of a `+` concatenation of string constants; None when any part is not one."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        a, b = _flat_concat(n.left), _flat_concat(n.right)
        return None if a is None or b is None else a + b
    return None


class _Fn:
    def __init__(self, fn, tree, bound, dotted, calls_module, mods):
        self.fn, self.tree, self.bound = fn, tree, bound
        self.dotted, self.calls_module, self.mods = dotted, calls_module, mods
        self.module_consts = {}
        for st in getattr(tree, "body", []):
            if isinstance(st, ast.Assign):
                for t in st.targets:
                    if isinstance(t, ast.Name):
                        self.module_consts.setdefault(t.id, []).append(st.value)
        self.params = _parametrized(fn)
        self.stmts = list(reachable(fn.body))
        self.nodes = [n for st in self.stmts for n in _own_nodes(st)]
        self.rec_line = 0
        self.recorders = self._recorders()      # {name: class}: a test-built recorder object (a fake connection) the builder was handed and that the test never wrote to
        self.tainted = set()                    # the names tainted at the END of the function (the fallback view)
        self.taint_at: dict = {}                # id(statement) -> the names tainted just BEFORE it runs (flow-sensitive: a rebinding to a non-builder value clears the taint)
        self.over_at: dict = {}                 # id(statement) -> {(name, key)} of builder-output keys overwritten by a non-builder value just before it
        self._cur = None
        self._taint()

    def builder_call(self, n) -> bool:
        if isinstance(n, ast.Call):
            d = self.dotted(n.func, self.bound) if isinstance(n.func, (ast.Name, ast.Attribute)) else None
            return bool(d) and any(self.calls_module(d, m) for m in self.mods)
        return False

    def at(self, stmt):
        """Evaluate `derived` / `literal` / `expected_nodes` / `defining_assigns` against the names tainted just before `stmt` (None = the end of the function)."""
        self._cur = self.taint_at.get(id(stmt)) if stmt is not None else None

    @property
    def cur(self):
        return self._cur if self._cur is not None else self.tainted

    def overwritten(self, stmt) -> set:
        return {k for (_n, k) in self.over_at.get(id(stmt), ())}

    def _recorders(self) -> dict:
        """The objects a builder may RECORD its output into, narrowly: a name passed bare to a builder call (or built into a name that is: `ctx = ContextSpec(db_conn=conn)`) whose single binding in
        the test is a NO-ARGUMENT constructor call of a class defined in the test module (a fake connection), and that the test never writes to (no `name.attr = ...`, `+=`, setattr). Only an
        attribute read off such a name AFTER the first builder call counts as derived from the builder (`conn.inserted[0]`); `SimpleNamespace(citation_human=S)`, a fake pre-seeded with the sentence
        (see `poisoned`) and `conn.citation_human = S` do not qualify. A subscript of a test-built fixture never does."""
        calls = [n for n in self.nodes if self.builder_call(n)]
        if not calls:
            return {}
        self.rec_line = min(getattr(c, "lineno", 0) for c in calls)
        passed = set()
        for c in calls:
            for a in list(c.args) + [k.value for k in c.keywords]:
                if isinstance(a, ast.Name):
                    passed.add(a.id)
        passed -= set(self.params)
        binds: dict = {}
        for st in self.stmts:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                binds.setdefault(st.targets[0].id, []).append(st.value)
        classes = {c.name: c for c in getattr(self.tree, "body", []) if isinstance(c, ast.ClassDef)}

        def ctor(name):
            b = binds.get(name, [])
            if len(b) == 1 and isinstance(b[0], ast.Call) and not b[0].args and not b[0].keywords and isinstance(b[0].func, ast.Name) and b[0].func.id in classes:
                return classes[b[0].func.id]
            return None
        rec = {}
        for n in passed:
            if ctor(n) is not None:
                rec[n] = ctor(n)
                continue
            b = binds.get(n, [])
            if len(b) == 1 and isinstance(b[0], ast.Call):
                for a in list(b[0].args) + [k.value for k in b[0].keywords]:
                    if isinstance(a, ast.Name) and ctor(a.id) is not None:
                        rec[a.id] = ctor(a.id)
        written = self._written_roots(set(rec), classes)
        return {k: v for k, v in rec.items() if k not in written}

    @staticmethod
    def _root(n):
        """The Name at the root of an attribute / subscript / call-receiver chain (`conn.inserted[0].x` -> conn), else None."""
        while isinstance(n, (ast.Attribute, ast.Subscript, ast.Call)):
            n = n.value if isinstance(n, (ast.Attribute, ast.Subscript)) else n.func
        return n.id if isinstance(n, ast.Name) else None

    def _written_roots(self, names: set, classes: dict) -> set:
        """The recorder names the test could have SEEDED with the expected sentence: any Store / Del of an attribute or item whose receiver chain is rooted at the name (`conn.x = ..`, `conn.x[i] = ..`,
        `conn.inserted[:] = ..`, `del conn.x[0]`), any method call on a chain rooted at it BEFORE the first builder call (`conn.inserted.append(..)`, `conn.add_row(..)`), `setattr` / `delattr` /
        `vars(...)` / `__dict__` on it, and a call BEFORE the builder call that hands it to a helper defined in the test module (the helper may seed it). The builder call itself and imported
        constructors (`ContextSpec(db_conn=conn)`) are not writes."""
        written = set()
        helpers = {n.name for n in getattr(self.tree, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        for n in ast.walk(self.fn):
            if isinstance(n, (ast.Attribute, ast.Subscript)) and isinstance(n.ctx, (ast.Store, ast.Del)):
                r = self._root(n)
                if r in names:
                    written.add(r)
            if isinstance(n, ast.Attribute) and n.attr == "__dict__":
                r = self._root(n)
                if r in names:
                    written.add(r)
            if isinstance(n, ast.Call):
                fn_name = n.func.id if isinstance(n.func, ast.Name) else None
                if fn_name in ("setattr", "delattr", "vars") and n.args:
                    r = self._root(n.args[0])
                    if r in names:
                        written.add(r)
                if self.builder_call(n):
                    continue
                before = getattr(n, "lineno", 0) < self.rec_line
                if isinstance(n.func, ast.Attribute) and before:
                    r = self._root(n.func)
                    if r in names:
                        written.add(r)
                if before and fn_name in helpers:
                    for a in list(n.args) + [k.value for k in n.keywords]:
                        r = self._root(a)
                        if r in names:
                            written.add(r)
        return written

    @staticmethod
    def _strings(node):
        """Every string a node states: each string constant, and each constant concatenation / f-string constant text (`"Sun is exalted " + "in Aries by rule"`)."""
        out = []
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                out.append(n.value)
            elif isinstance(n, ast.JoinedStr):
                out.append("".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str)))
            elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                flat = _flat_concat(n)
                if flat is not None:
                    out.append(flat)
        return out

    def _class_strings(self, cls) -> list:
        """The strings a recorder class holds or can reach: its own constants and concatenations, the module constants and the module-level functions its body names (transitively, depth 3)."""
        funcs = {n.name: n for n in getattr(self.tree, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        seen, todo, out = set(), [(cls, 0)], []
        while todo:
            node, d = todo.pop()
            if id(node) in seen:
                continue
            seen.add(id(node))
            out += self._strings(node)
            for n in ast.walk(node):
                if isinstance(n, ast.Name) and n.id in self.module_consts:
                    for v in self.module_consts[n.id]:
                        out += self._strings(v)
                elif isinstance(n, ast.Name) and n.id in funcs and d < 3:
                    todo.append((funcs[n.id], d + 1))
        return out

    def poisoned(self, exps) -> bool:
        """A recorder class that itself holds (a fragment of) the expected sentence: a fake pre-seeded with it would hand the sentence back. Every string the class holds or reaches, alone and joined
        (with and without a space), is compared with every expected string: ONE shared run of POISON_MIN (10) characters is a pre-seed, however the sentence was split."""
        want = [x for e in exps for x in self._strings(e) if len(x) >= POISON_MIN]
        if not want:
            return False
        for cls in self.recorders.values():
            have = self._class_strings(cls)
            blobs = have + ["".join(have), " ".join(have)]
            for w in want:
                wins = {w[i:i + POISON_MIN] for i in range(len(w) - POISON_MIN + 1) if re.search(r"\w \w", w[i:i + POISON_MIN])}      # a sentence-like run: two words around a space (an identifier or key name shared with the fake's SQL is not the sentence)
                if any(win in b for b in blobs for win in wins):
                    return True
        return False

    def derived(self, node, taint=None) -> bool:
        taint = self.cur if taint is None else taint
        for n in ast.walk(node):
            if self.builder_call(n) or (isinstance(n, ast.Name) and n.id in taint):
                return True
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in self.recorders and getattr(n, "lineno", 0) > self.rec_line:
                return True
        return False

    def _taint(self):
        """One forward pass over the reachable statements in source order. A name is tainted from a statement that binds it to a builder-derived value until the next statement that binds it to a
        value that is NOT builder-derived (`out = build(...)` then `out = {"citation_human": "<s>"}` leaves the assertion comparing the literal with itself). A key of the output overwritten by
        a non-builder value (`out["k"] = "<s>"`) is recorded the same way. Branches are read in source order, the last binding winning (conservative: it can only withdraw a golden verdict)."""
        cur, over = set(), set()
        for n in self.stmts:
            self.taint_at[id(n)] = frozenset(cur)
            self.over_at[id(n)] = frozenset(over)
            if isinstance(n, (ast.With, ast.AsyncWith)):
                for it in n.items:
                    if it.optional_vars is not None and self.derived(it.context_expr, cur):
                        cur |= _names(it.optional_vars)
                continue
            tgt, val = None, None
            if isinstance(n, ast.Assign):
                tgt, val = n.targets, n.value
            elif isinstance(n, ast.AnnAssign) and n.value is not None:
                tgt, val = [n.target], n.value
            elif isinstance(n, (ast.For, ast.AsyncFor)):
                tgt, val = [n.target], n.iter
            elif isinstance(n, ast.AugAssign):
                if self.derived(n.value, cur):
                    cur |= _names(n.target)
                continue
            if tgt is None:
                continue
            d = self.derived(val, cur)
            for t in tgt:
                if isinstance(t, (ast.Name, ast.Tuple, ast.List, ast.Starred)):
                    bound = {x.id for x in ast.walk(t) if isinstance(x, ast.Name)}
                    if d:
                        cur |= bound
                        over = {(a, k) for (a, k) in over if a not in bound}
                    else:
                        cur -= bound
                        over = {(a, k) for (a, k) in over if a not in bound}
                elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str):
                    if d:
                        over.discard((t.value.id, t.slice.value))
                    else:
                        over.add((t.value.id, t.slice.value))
                elif d:
                    cur |= _names(t)
        self.tainted = cur

    def literal(self, node, depth=0) -> bool:
        """The node states a value independent of the builder: literal constants and containers, a module constant or a parametrize value bound to such."""
        if depth > 4:
            return False
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, ast.JoinedStr):
            return all(isinstance(v, ast.Constant) for v in node.values)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return self.literal(node.operand, depth + 1)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.literal(node.left, depth + 1) and self.literal(node.right, depth + 1)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(self.literal(e, depth + 1) for e in node.elts)
        if isinstance(node, ast.Dict):
            return all(k is not None and self.literal(k, depth + 1) and self.literal(v, depth + 1) for k, v in zip(node.keys, node.values))
        if isinstance(node, ast.Name):
            if node.id in self.cur:
                return False
            if node.id in self.params:
                return all(self.literal(v, depth + 1) for v in self.params[node.id])
            vals = self.module_consts.get(node.id)
            if vals is not None and len(vals) == 1:
                return self.literal(vals[0], depth + 1)
        return False

    def expected_nodes(self, node):
        """The literal node(s) an expected side stands for (a parametrize name expands to its values)."""
        if isinstance(node, ast.Name) and node.id in self.params and node.id not in self.cur:
            return list(self.params[node.id])
        if isinstance(node, ast.Name) and node.id not in self.cur and len(self.module_consts.get(node.id, [])) == 1:
            return [self.module_consts[node.id][0]]
        return [node]

    def equalities(self):
        """[(lhs, rhs, node)] for every equality inside a REACHABLE assert statement or assertEqual-style call statement."""
        out = []
        for st in self.stmts:
            if isinstance(st, ast.Assert):
                t = st.test
                cands = t.values if isinstance(t, ast.BoolOp) and isinstance(t.op, ast.And) else [t]
                for c in cands:
                    if isinstance(c, ast.Compare) and len(c.ops) == 1 and isinstance(c.ops[0], ast.Eq):
                        out.append((c.left, c.comparators[0], st))
            elif isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
                n = st.value
                nm = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id if isinstance(n.func, ast.Name) else None
                if nm in _EQ_CALLS and len(n.args) >= 2:
                    out.append((n.args[0], n.args[1], st))
        return out

    def defining_assigns(self, node):
        used = _names(node) & self.cur
        return [n for n in self.stmts if isinstance(n, ast.Assign) and any(_names(t) & used for t in n.targets) and self.derived(n.value, self.taint_at.get(id(n), self.tainted))]

    def called_builder_names(self):
        out = set()
        for n in self.nodes:
            if self.builder_call(n):
                d = self.dotted(n.func, self.bound)
                out.add(d.rsplit(".", 1)[-1])
        return out


def verify_test(fn_rec, tree, mods, dotted, calls_module):
    """(golden dict | None, reason) for one test function record (`node`, `bound` keys present). The golden dict carries `keys`: {key: line} for every key a verified golden equality
    COVERS: the key the actual side picks out exactly (subscript / `.get` / attribute / name) beside a prose-bearing literal, or a key of a literal expected dict whose OWN value is prose."""
    f = _Fn(fn_rec["node"], tree, fn_rec["bound"], dotted, calls_module, mods)
    if fn_rec.get("skipped"):
        return None, "the test is skipped / xfailed"
    names = f.called_builder_names()
    if not names:
        return None, "the test does not (reachably) call the builder module(s) " + ", ".join(mods)
    patched = _patches_builder(fn_rec["node"], names)
    if patched:
        return None, patched
    last = "no reachable equality assertion found"
    first, keys = None, {}
    for lhs, rhs, node in f.equalities():
        f.at(node)                                           # taint as of THIS assertion (flow-sensitive)
        for actual, exp in ((lhs, rhs), (rhs, lhs)):
            if not f.derived(actual):
                continue
            if f.derived(exp):
                last = f"line {node.lineno}: the expected side is produced by the builder (not independent)"
                continue
            exps = f.expected_nodes(exp)
            if not exps or not all(f.literal(e) for e in exps):
                last = f"line {node.lineno}: the expected side is not a literal"
                continue
            if not any(_prose_bearing(e) for e in exps):
                last = f"line {node.lineno}: the expected literal carries no sentence (a string of >= {MIN_WORDS} words and >= {MIN_CHARS} characters)"
                continue
            if f.poisoned(exps):
                last = f"line {node.lineno}: a test-built fake the builder is handed holds the expected sentence itself (a pre-seeded recorder)"
                continue
            picked = _picked_keys(actual, f.builder_call)
            for x in f.defining_assigns(node):
                picked |= _target_names(x)                 # `citation_human = build(...)` names the column; the assigned call's own arguments do not
                picked |= _picked_keys(x.value, f.builder_call)            # `reasons = [out["reason"], ...]`: a key that picks the value out of the built output in the assignment that defines a compared name
            picked -= f.overwritten(node)                  # a key the test itself overwrote with a literal before asserting it is not the builder's
            by_key = {}
            for e in exps:
                for k, vs in _dict_values_by_key(e).items():
                    by_key.setdefault(k, []).extend(vs)
            for k, vs in by_key.items():
                if any(_prose_bearing(v) for v in vs):
                    keys.setdefault(k, node.lineno)         # the dict key's OWN value is the sentence
            if not by_key:
                for k in picked:
                    keys.setdefault(k, node.lineno)         # a scalar sentence compared with the value picked out by key k
            if first is None:
                dump = "|".join(sorted(ast.dump(e) for e in exps))
                first = dict(line=node.lineno, expected_sha256=hashlib.sha256(dump.encode("utf-8")).hexdigest())
    if first is None:
        return None, last
    return dict(first, keys=keys), "golden assertion"


def scan(entries, declared, mods, tests, test_facts, dotted, calls_module, leaf_of_entry, root_rel):
    """Narr.fidelity_test over the declared `fidelity_tests`.

    entries: the declared prose entries; declared: list of {test, covers}; mods: builder modules; tests: [(Path, text)]; test_facts: the census's `_test_facts`
    (extended records with `node`, `bound`, `qual`); leaf_of_entry(entry) -> leaf; root_rel(path) -> repo-relative posix path.
    Returns dict(v, tests=[...], covered=[...], measured, golden?)."""
    results, covered = [], set()
    by_rel = {}
    for p, text in tests:
        by_rel[root_rel(p)] = (p, text)
    for d in declared:
        path, rest = _split_ref(d["test"])
        got = by_rel.get(path)
        row = dict(test=d["test"], covers=list(d["covers"]))
        if got is None:
            row.update(ok=False, reason=f"the file {path} is not among the discovered sidecar test files")
            results.append(row)
            continue
        p, text = got
        facts = test_facts(p, text)
        if not facts:
            row.update(ok=False, reason="the test file does not parse")
            results.append(row)
            continue
        funcs, mod_skip = facts
        want = rest[-1] if rest else ""
        cls = rest[-2] if len(rest) >= 2 else None
        cand = [f for f in funcs if f["name"] == want and (cls is None or f.get("cls") == cls)]
        if not cand:
            row.update(ok=False, reason=f"no test function {d['test'].split('::', 1)[1]} in {path}")
            results.append(row)
            continue
        if mod_skip:
            row.update(ok=False, reason="the test module is skipped")
            results.append(row)
            continue
        rec = cand[-1]                                       # pytest runs the LAST of two definitions with one name
        g, why = verify_test(rec, ast.parse(text), mods, dotted, calls_module)
        if g is None:
            row.update(ok=False, reason=why)
            results.append(row)
            continue
        ok_cov, bad_cov = [], []
        for e in d["covers"]:
            lf = leaf_of_entry(e)
            (ok_cov if lf in g["keys"] else bad_cov).append(e)
        covered |= set(ok_cov)
        row.update(ok=not bad_cov, reason=("golden assertion verified" if not bad_cov else
                                           f"golden assertion verified but the entry/entries {', '.join(bad_cov)} are not referenced in it"),
                   line=g["line"], expected_sha256=g["expected_sha256"], covers_verified=ok_cov,
                   file_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
        results.append(row)
    unc = [e for e in entries if e not in covered]
    v = "PASS" if not unc and all(r.get("ok") for r in results) else "PARTIAL"
    rows = [dict(r) for r in results]
    verified = [r for r in rows if r.get("covers_verified")]
    measured = (f"{len(verified)} declared golden-value test(s) verified (the built output asserted equal to an independent literal sentence): covers {', '.join(sorted(covered)) or 'nothing'}"
                + (f"; NOT covered by a verified golden test: {', '.join(unc)}" if unc else "")
                + ("; unverified declared test(s): " + "; ".join(f"{r['test']} ({r['reason']})" for r in rows if not r.get("ok"))
                   if any(not r.get("ok") for r in rows) else ""))
    out = dict(v=v, covered=sorted(covered), golden_tests=rows, measured=measured)
    if v == "PASS":
        out["golden"] = dict(verified=True, entries=list(entries), builder_modules=list(mods),
                             tests=[dict(test=r["test"], line=r["line"], expected_sha256=r["expected_sha256"], file_sha256=r["file_sha256"],
                                         covers=r["covers_verified"]) for r in verified])
    return out
