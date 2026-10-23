"""SR-GEOMETRY-PIN-ONCE helpers: pure functions, no database, no network. They take paths so a planted reversion is applied to a COPY of the real file.

Two detectors live here, both able to read false (CLAUDE.md §N.8):
  * `geometry_digest_of(root)` / `refusals_for(root, entry)` - the geometry implementation digest recomputed from the bytes under `root` with the production recipe
    (`input_vector_verifier.module_digests`: sha256 of the source text per module, canonical JSON, sha256), compared module by module with the changelog entry. Any
    byte that is not in the entry refuses and NAMES the module (T20: "any further geometry change refuses").
  * `attribute(...)` - the row-level verdict of the controlled leave-one-out builds: every differing row is a pin-consumer row (only digest/manifest columns differ) or belongs
    to exactly one approved cause that can reach its table; anything else is `unattributed`, `double` or `out_of_reach`, and the verdict is REFUSED.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

KERNEL = "services.gochara_kernel."
MODULES_REL = "services/gochara_kernel"


def _sha256_text(path: Path) -> str:
    # production reads the source with `open(origin, encoding="utf-8").read()` (universal newlines), then hashes the utf-8 bytes
    with open(path, encoding="utf-8") as fh:
        return hashlib.sha256(fh.read().encode("utf-8")).hexdigest()


def geometry_module_names(input_vector_py: Path) -> list[str]:
    """The names in `IMPLEMENTATION_MODULES["geometry"]`, parsed from the source of input_vector.py (an AST read, so it also works on a copy)."""
    tree = ast.parse(Path(input_vector_py).read_text(encoding="utf-8"))
    prefix = None
    for node in ast.walk(tree):                                      # `_K, _R = "services.gochara_kernel.", "services.gochara_rules."`
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            for t, v in zip(node.targets[0].elts, node.value.elts):
                if isinstance(t, ast.Name) and t.id == "_K" and isinstance(v, ast.Constant):
                    prefix = v.value
    if prefix is None:
        raise ValueError("the kernel module prefix _K was not found")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "IMPLEMENTATION_MODULES" for t in node.targets):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value == "geometry":
                    gen = v.args[0]                                   # tuple(_K + m for m in ( ... ))
                    return [prefix + e.value for e in gen.generators[0].iter.elts]
    raise ValueError("IMPLEMENTATION_MODULES['geometry'] not found")


def geometry_digests_of(root: Path) -> tuple[str, dict[str, str]]:
    """(stage digest, {module: sha256}) for the geometry stage of the tree whose python-sidecar directory is `root`."""
    root = Path(root)
    names = geometry_module_names(root / MODULES_REL / "input_vector.py")
    per = {n: _sha256_text(root / (n.replace(".", "/") + ".py")) for n in names}
    stage = hashlib.sha256(json.dumps(per, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    return stage, per


def geometry_digest_of(root: Path) -> str:
    return geometry_digests_of(root)[0]


def refusals_for(root: Path, entry: dict) -> list[str]:
    """Empty when the bytes under `root` are exactly the changelog `entry`'s `after`; otherwise one line per module that differs, naming it."""
    stage, per = geometry_digests_of(root)
    out = []
    want = {KERNEL + name: m["after_sha256"] for name, m in entry["modules"].items()}
    if sorted(per) != sorted(want):
        out.append(f"the geometry module LIST changed: {sorted(set(per) ^ set(want))}")
    for name in sorted(set(per) & set(want)):
        if per[name] != want[name]:
            out.append(f"REFUSE: geometry module {name.removeprefix(KERNEL)} changed after the pin of {entry['id']} (a further geometry change needs a new ruling and a new entry)")
    if not out and stage != entry["geometry_after"]:
        out.append("REFUSE: the geometry digest differs from the entry's geometry_after although every module matches (the entry is inconsistent)")
    return out


def ownership_problems(entry: dict, geometry_names: list[str], approved: set[str], shared: dict[str, set[str]]) -> list[str]:
    """The changelog's claims about WHO moved WHICH module, checked against the entry's own before/after bytes (empty list = consistent).

    * the entry's module list is the real `IMPLEMENTATION_MODULES['geometry']` list; * the causes are exactly the approved ones;
    * every module whose bytes changed is owned by a cause, and by two only where `shared` says so (each in its own hunk); * a cause owns only modules that changed;
    * a module no cause names did not change.
    """
    problems = []
    if sorted(entry["modules"]) != sorted(geometry_names):
        problems.append(f"module list differs from IMPLEMENTATION_MODULES['geometry']: {sorted(set(entry['modules']) ^ set(geometry_names))}")
    ids = [c["id"] for c in entry["causes"]]
    if set(ids) != set(approved) or len(ids) != len(set(ids)):
        problems.append(f"causes {sorted(ids)} are not exactly the approved {sorted(approved)} (missing {sorted(set(approved) - set(ids))})")
    owners: dict[str, list[str]] = {}
    for c in entry["causes"]:
        for m in c["modules"]:
            owners.setdefault(m, []).append(c["id"])
    for name, m in entry["modules"].items():
        changed = m["before_sha256"] != m["after_sha256"]
        who = sorted(owners.get(name, []))
        if changed and not who:
            problems.append(f"module {name} changed and no cause owns it")
        if changed and len(who) > 1 and set(who) != shared.get(name, set()):
            problems.append(f"module {name} is owned by {who} but only {sorted(shared.get(name, set()))} may share it")
        if not changed and who:
            problems.append(f"module {name} did not change but is owned by {who}")
        if bool(m.get("changed")) != changed:
            problems.append(f"module {name}: the recorded `changed` flag disagrees with its before/after bytes")
    for name in owners:
        if name not in entry["modules"]:
            problems.append(f"a cause owns {name}, which is not a geometry module")
    return problems


def golden_geometry_literal(golden_py: Path) -> str:
    """The string in `assert got["implementation"]["geometry"] == "<64 hex>"` of the golden test, found by AST (never by a regex over the comments)."""
    tree = ast.parse(Path(golden_py).read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and isinstance(node.comparators[0], ast.Constant):
            left = node.left                                           # got["implementation"]["geometry"]
            if (isinstance(left, ast.Subscript) and isinstance(left.slice, ast.Constant) and left.slice.value == "geometry"
                    and isinstance(left.value, ast.Subscript) and isinstance(left.value.slice, ast.Constant) and left.value.slice.value == "implementation"):
                found.append(node.comparators[0].value)
    if len(found) != 1:
        raise ValueError(f"expected exactly one geometry literal in the golden, found {len(found)}")
    return found[0]


def reason_literals(path: Path, spellings: tuple[str, ...]) -> list[str]:
    """The reason spellings that appear as string-literal VALUES in the module at `path` (AST; an `__all__` entry or an identifier is not a literal value)."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    return sorted({n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in spellings})


def attribute(delta_rows, cause_sets: dict[str, set], consumer_allowed: dict[str, set], reach: dict[str, set]) -> dict:
    """The verdict rule of the single geometry re-derivation.

    delta_rows       : iterable of (table, key, columns) - every row of Delta(head, all-causes-off); `columns` = the differing column names ('*' for an added/removed row)
    cause_sets       : {cause: {(table, key)}} - the rows of Delta(head, head-without-that-cause)
    consumer_allowed : {table: {column}} - the digest/manifest columns of a table whose rows follow ANY pin move (counted, never attributed to one cause)
    reach            : {cause: {table}} - the tables the cause's code path can write

    Returns {"status", "attributed": {cause: [(table, key)]}, "pin_consumers": {table: n}, "unattributed", "double", "out_of_reach"}.
    A row is a pin consumer only when ALL its differing columns are allowed ones; a consumer-table row that differs elsewhere is a geometry row and needs a cause.
    """
    attributed = {c: [] for c in cause_sets}
    pin: dict[str, int] = {}
    unattributed, double, out_of_reach = [], [], []
    for table, key, cols in delta_rows:
        cols = set(cols)
        if table in consumer_allowed and "*" not in cols and cols <= set(consumer_allowed[table]):
            pin[table] = pin.get(table, 0) + 1
            continue
        owners = [c for c, rows in cause_sets.items() if (table, key) in rows]
        if not owners:
            unattributed.append((table, key, sorted(cols)))
        elif len(owners) > 1:
            double.append((table, key, owners))
        else:
            attributed[owners[0]].append((table, key))
    for cause, rows in cause_sets.items():
        for table, key in sorted(rows, key=str):
            if table not in reach.get(cause, set()) and not (table in consumer_allowed):
                out_of_reach.append((cause, table, key))
    status = "REFUSED" if (unattributed or double or out_of_reach) else "ATTRIBUTED"
    return {"status": status, "attributed": attributed, "pin_consumers": pin, "unattributed": unattributed, "double": double, "out_of_reach": out_of_reach}
