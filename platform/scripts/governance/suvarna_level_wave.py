#!/usr/bin/env python3
"""suvarna_level_wave.py -- Suvarna Track E level-wave tooling (pure module, no CLI, no database of its own).

SECTIONS (each item owns one section; add yours below the marker, do not edit another item's section)
  1. E5.9  transitive write/delete footprint from the pg_constraint closure        (this file, below)
  2. E5.3  level-wave dispatcher and its gates                                      (RESERVED -- not written)

================================================================================================
SECTION 1 -- E5.9 transitive write/delete footprint (N-32; Astra F13)
================================================================================================
A wave's writers delete-then-insert into a set of tables (the WRITE SET). The real blast radius is larger: a
DELETE in a write table fires every foreign key that points at it. This section computes, from the foreign-key
edge list in pg_constraint, what a wave's deletes do beyond the writers' own tables:

  delete_cascades  tables whose rows are DELETED by the ON DELETE CASCADE closure, with the full path
  set_null         tables whose referencing columns are NULLED by ON DELETE SET NULL, with column, NOT NULL
                   flag and path (a NOT NULL column makes the delete fail: it is also listed in `refusing`)
  set_default      tables whose referencing columns are reset by ON DELETE SET DEFAULT
  refusing         edges that would REFUSE the delete (NO ACTION / RESTRICT, or SET NULL on a NOT NULL
                   column): the blockers
  unknown_tables   write tables the edge list / catalog table list does not know: NOT "no footprint"
  dangling_after_rewrite
                   references that survive a rewrite in tables with NO foreign key are not computable from
                   pg_constraint; the field is always `unknown_not_in_catalog` and never an empty clean reading

Earned-signal rule (CLAUDE.md section N.8): a footprint that cannot be wrong must not read as clean. An empty
edge list, or a write table outside the edge list's universe, yields `fk_closure_status: INCOMPLETE` with the
tables in `unknown_tables`. `COMPLETE` means ONLY "the foreign-key closure over the edges supplied is computed";
it says nothing about references that carry no foreign key (see dangling_after_rewrite).

Inputs
  edges        list of dicts: child_table, parent_table, on_delete, columns, child_columns_not_null,
               and optionally constraint, on_update. on_delete is a name (CASCADE, SET NULL, SET DEFAULT,
               NO ACTION, RESTRICT) or the pg_constraint code letter (c, n, d, a, r). An unknown value raises.
               Tables are schema-qualified; a bare name means public.<name>.
  known_tables optional catalog table list (tables_from_catalog). With it, a table with no FK edges is a
               computed zero (`no_fk_edges_tables`); without it, the universe is the tables the edges mention
               and an FK-free write table is reported unknown (the catalog was not asked about it).

Semantics (stricter reading when in doubt)
  * CASCADE closure is a breadth-first walk from the write set, level by level in sorted order, so the path
    reported for each table is the shortest one and ties break deterministically; cycles and self-references
    terminate (each table is reached once).
  * A table in the write set is not listed as a cascade side effect (the writers already own it).
  * SET NULL does not propagate: a nulled row is not a deleted row, so its own children are untouched.
  * NO ACTION / RESTRICT are listed as refusing even when the child is also cascade-deleted in the same
    statement (`child_also_deleted: true` says so); NO ACTION can be deferred and pass, and the catalog cannot
    show the data, so the caller decides with the flag in hand.
  * Output is sorted everywhere and has no timestamps: json.dumps(sort_keys=True) is byte-reproducible.

The loaders take an already-open DB-API connection, run only SELECTs on pg_catalog (assert_select_only guards
this by construction), and never commit, roll back or close the connection.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "suvarna.e5_9.transitive_footprint/1"
DEFAULT_SCHEMA = "public"

CASCADE = "CASCADE"
SET_NULL = "SET NULL"
SET_DEFAULT = "SET DEFAULT"
NO_ACTION = "NO ACTION"
RESTRICT = "RESTRICT"

# pg_constraint.confdeltype / confupdtype
_ACTION_CODES = {"a": NO_ACTION, "r": RESTRICT, "c": CASCADE, "n": SET_NULL, "d": SET_DEFAULT}
_ACTION_NAMES = {v: v for v in _ACTION_CODES.values()}

# ---------------------------------------------------------------------------------------------
# Read-only catalog loaders
# ---------------------------------------------------------------------------------------------

FK_EDGE_COLUMNS = ("constraint", "child_table", "parent_table", "confdeltype", "confupdtype",
                   "child_columns", "child_columns_not_null")

# One row per foreign-key constraint. child_columns keeps constraint column order; child_columns_not_null is the
# subset of those columns declared NOT NULL (a SET NULL action on one of them cannot succeed).
FK_EDGES_SQL = """
SELECT con.conname::text AS "constraint",
       cn.nspname || '.' || cc.relname AS child_table,
       pn.nspname || '.' || pc.relname AS parent_table,
       con.confdeltype::text AS confdeltype,
       con.confupdtype::text AS confupdtype,
       ARRAY(SELECT a.attname::text
               FROM unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
               JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum
              ORDER BY k.ord) AS child_columns,
       ARRAY(SELECT a.attname::text
               FROM unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
               JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum
              WHERE a.attnotnull
              ORDER BY k.ord) AS child_columns_not_null
  FROM pg_constraint con
  JOIN pg_class cc ON cc.oid = con.conrelid
  JOIN pg_namespace cn ON cn.oid = cc.relnamespace
  JOIN pg_class pc ON pc.oid = con.confrelid
  JOIN pg_namespace pn ON pn.oid = pc.relnamespace
 WHERE con.contype = 'f'
 ORDER BY child_table, parent_table, con.conname
"""

# Every ordinary / partitioned table outside the system schemas (the catalog universe).
TABLES_SQL = """
SELECT n.nspname || '.' || c.relname AS table_name
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE c.relkind IN ('r', 'p')
   AND n.nspname NOT IN ('pg_catalog', 'information_schema')
   AND n.nspname NOT LIKE 'pg\\_toast%'
 ORDER BY 1
"""

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|INTO|COPY|CALL|DO|EXECUTE|MERGE|VACUUM|"
    r"REINDEX|CLUSTER|REFRESH|COMMENT|LOCK|SET|RESET|BEGIN|COMMIT|ROLLBACK|NEXTVAL|SETVAL|SET_CONFIG|"
    r"PG_TERMINATE_BACKEND|PG_CANCEL_BACKEND|LO_IMPORT|LO_EXPORT|LO_UNLINK|DBLINK\w*)\b"
    r"|\bFOR\s+(UPDATE|SHARE|NO\s+KEY|KEY\s+SHARE)\b",
    re.IGNORECASE)


def assert_select_only(sql: str) -> None:
    """Raise ValueError unless `sql` is exactly one plain SELECT statement (by construction, not by trust).

    Comments and string / quoted-identifier literals are stripped first, so a keyword inside a literal is data.
    WITH-queries are rejected too: a data-modifying CTE hides a write behind a SELECT.
    """
    if not isinstance(sql, str):
        raise ValueError("statement must be a string")
    s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    s = re.sub(r"--[^\n]*", " ", s)
    s = re.sub(r"'(?:[^']|'')*'", "''", s)
    s = re.sub(r'"(?:[^"]|"")*"', '""', s)
    s = s.strip()
    if s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        raise ValueError("empty statement")
    if ";" in s:
        raise ValueError("multiple statements are not allowed")
    if not re.match(r"SELECT\b", s, re.IGNORECASE):
        raise ValueError("only a SELECT statement may be run against the catalog")
    bad = _FORBIDDEN.search(s)
    if bad:
        raise ValueError(f"statement contains a non-read-only construct: {bad.group(0)!r}")


def _norm_action(value: Any, what: str = "on_delete") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{what}: expected a string, got {value!r}")
    v = value.strip()
    if v in _ACTION_CODES:
        return _ACTION_CODES[v]
    name = v.upper().replace("_", " ")
    if name in _ACTION_NAMES:
        return name
    raise ValueError(f"{what}: unknown referential action {value!r}")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):  # a driver that hands arrays back as '{a,b}'
        inner = value.strip().strip("{}")
        return [x.strip('"') for x in inner.split(",") if x]
    return [str(x) for x in value]


def _run_select(conn: Any, sql: str) -> list[Any]:
    assert_select_only(sql)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return list(cur.fetchall())
    finally:
        close = getattr(cur, "close", None)
        if close is not None:
            close()


def fk_edges_from_catalog(conn: Any) -> list[dict]:
    """Foreign-key edges from pg_constraint over an already-open DB-API connection (SELECT only).

    Rows may be tuples (column order FK_EDGE_COLUMNS) or mappings. The connection is not committed, rolled back
    or closed. Zero rows returns [] -- transitive_footprint then reports INCOMPLETE rather than a clean zero.
    """
    edges = []
    for row in _run_select(conn, FK_EDGES_SQL):
        rec = {k: row[k] for k in FK_EDGE_COLUMNS} if hasattr(row, "keys") else dict(zip(FK_EDGE_COLUMNS, row))
        edges.append({
            "constraint": rec["constraint"],
            "child_table": rec["child_table"],
            "parent_table": rec["parent_table"],
            "on_delete": _norm_action(rec["confdeltype"], "confdeltype"),
            "on_update": _norm_action(rec["confupdtype"], "confupdtype"),
            "columns": _as_list(rec["child_columns"]),
            "child_columns_not_null": _as_list(rec["child_columns_not_null"]),
        })
    return edges


def tables_from_catalog(conn: Any) -> list[str]:
    """Schema-qualified names of every ordinary / partitioned user table (SELECT only), sorted and unique."""
    names = set()
    for row in _run_select(conn, TABLES_SQL):
        names.add(row["table_name"] if hasattr(row, "keys") else row[0])
    return sorted(names)


# ---------------------------------------------------------------------------------------------
# Footprint (pure)
# ---------------------------------------------------------------------------------------------

def _norm_table(name: Any) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"table name must be a non-empty string, got {name!r}")
    n = name.strip()
    return n if "." in n else f"{DEFAULT_SCHEMA}.{n}"


def _norm_edge(e: Mapping[str, Any]) -> dict:
    for k in ("child_table", "parent_table", "on_delete"):
        if k not in e:
            raise ValueError(f"edge is missing {k!r}: {e!r}")
    return {
        "child_table": _norm_table(e["child_table"]),
        "parent_table": _norm_table(e["parent_table"]),
        "on_delete": _norm_action(e["on_delete"]),
        "constraint": str(e.get("constraint") or ""),
        "columns": [str(c) for c in (e.get("columns") or [])],
        "child_columns_not_null": [str(c) for c in (e.get("child_columns_not_null") or [])],
    }


def _edge_key(e: dict) -> tuple:
    return (e["parent_table"], e["child_table"], e["constraint"], tuple(e["columns"]), e["on_delete"],
            tuple(e["child_columns_not_null"]))


def _hop(e: dict) -> dict:
    return {"from": e["parent_table"], "to": e["child_table"], "constraint": e["constraint"],
            "columns": list(e["columns"]), "on_delete": e["on_delete"]}


def _sort_key(entry: dict) -> tuple:
    return (entry["table"], entry.get("constraint", ""), tuple(entry.get("columns", ())))


def transitive_footprint(write_tables: Iterable[str], edges: Iterable[Mapping[str, Any]], *,
                         known_tables: Iterable[str] | None = None,
                         known_non_fk_references: Iterable[Mapping[str, Any]] | None = None) -> dict:
    """The transitive write/delete footprint of deleting from `write_tables`. See the module docstring."""
    write = sorted({_norm_table(t) for t in write_tables})
    if not write:
        raise ValueError("write set is empty: a wave with no write tables has no footprint to compute")
    write_set = set(write)

    uniq = {}
    for raw in edges:
        e = _norm_edge(raw)
        uniq[_edge_key(e)] = e
    edge_list = [uniq[k] for k in sorted(uniq)]
    out_edges: dict[str, list[dict]] = {}
    for e in edge_list:
        out_edges.setdefault(e["parent_table"], []).append(e)
    edge_universe = {e["parent_table"] for e in edge_list} | {e["child_table"] for e in edge_list}
    parents_with_inbound = {e["parent_table"] for e in edge_list}

    known = None if known_tables is None else {_norm_table(t) for t in known_tables}
    universe = edge_universe if known is None else (edge_universe | known)

    unknown, no_fk, incomplete = [], [], []
    for t in write:
        if t in universe:
            if t not in edge_universe:
                no_fk.append(t)
            continue
        if known is None:
            reason = "not in the edge list's universe (no FK edge names it; no catalog table list was supplied)"
        else:
            reason = "not in the catalog table list and no FK edge names it"
        unknown.append({"table": t, "reason": reason})
    if not edge_list and known is None:
        incomplete.append("edge list is empty: no foreign-key edges were supplied, so nothing about the "
                          "footprint is known (not a clean zero)")
    for u in unknown:
        incomplete.append(f"{u['table']}: {u['reason']}")

    # --- CASCADE closure: breadth-first, level by level in sorted order (shortest path, stable ties) ---
    reached: dict[str, list[dict]] = {t: [] for t in write}
    frontier = list(write)
    while frontier:
        nxt = []
        for node in sorted(frontier):
            for e in out_edges.get(node, ()):
                if e["on_delete"] == CASCADE and e["child_table"] not in reached:
                    reached[e["child_table"]] = reached[node] + [_hop(e)]
                    nxt.append(e["child_table"])
        frontier = nxt

    delete_cascades = [{"table": t, "depth": len(p), "path": p} for t, p in reached.items() if t not in write_set]

    # --- non-cascading actions out of every table whose rows are deleted (write set + cascade closure) ---
    set_null, set_default, refusing = [], [], []
    for parent in sorted(reached):
        for e in out_edges.get(parent, ()):
            act = e["on_delete"]
            if act == CASCADE:
                continue
            path = reached[parent] + [_hop(e)]
            base = {"table": e["child_table"], "parent_table": parent, "constraint": e["constraint"],
                    "columns": list(e["columns"]), "depth": len(path), "path": path,
                    "child_in_write_set": e["child_table"] in write_set,
                    "child_also_deleted": e["child_table"] in reached}
            if act in (SET_NULL, SET_DEFAULT):
                nn = [c for c in e["columns"] if c in set(e["child_columns_not_null"])]
                entry = dict(base, not_null_columns=nn, violates_not_null=bool(nn) and act == SET_NULL)
                (set_null if act == SET_NULL else set_default).append(entry)
                if entry["violates_not_null"]:
                    refusing.append(_refusal("SET_NULL_ON_NOT_NULL", base))
            else:  # NO ACTION / RESTRICT
                refusing.append(_refusal(act, base))

    delete_cascades.sort(key=lambda x: x["table"])
    for lst in (set_null, set_default):
        lst.sort(key=_sort_key)
    refusing.sort(key=lambda r: (r["child_table"], r["constraint"], tuple(r["columns"]), r["kind"]))

    no_inbound = [t for t in write if t in universe and t not in parents_with_inbound]
    known_refs = []
    for r in known_non_fk_references or ():
        referenced, referencing = _norm_table(r["referenced_table"]), _norm_table(r["referencing_table"])
        if referenced in write_set:
            known_refs.append({"referencing_table": referencing, "column": str(r["column"]),
                               "referenced_table": referenced})
    known_refs.sort(key=lambda r: (r["referencing_table"], r["column"], r["referenced_table"]))

    return {
        "schema": SCHEMA,
        "write_tables": write,
        "universe": {"source": "edges_only" if known is None else "catalog_table_list",
                     "edge_tables": len(edge_universe), "tables": len(universe)},
        "fk_closure_status": "INCOMPLETE" if incomplete else "COMPLETE",
        "incomplete_reasons": incomplete,
        "unknown_tables": unknown,
        "no_fk_edges_tables": no_fk,
        "delete_cascades": delete_cascades,
        "set_null": set_null,
        "set_default": set_default,
        "refusing": refusing,
        "has_blockers": bool(refusing),
        "dangling_after_rewrite": {
            "status": "unknown_not_in_catalog",
            "note": ("references that survive a delete-then-insert in tables with no foreign key are not "
                     "computable from pg_constraint; measure after the wave "
                     "(msr_dangling_signal_refs.py, msr_referential_integrity.py)"),
            "write_tables_with_no_inbound_fk": no_inbound,
            "known_non_fk_references": known_refs,
        },
        "counts": {
            "write_tables": len(write), "delete_cascades": len(delete_cascades), "set_null": len(set_null),
            "set_default": len(set_default), "refusing": len(refusing), "unknown_tables": len(unknown),
            "no_fk_edges_tables": len(no_fk), "edges_considered": len(edge_list),
        },
    }


def _refusal(kind: str, base: dict) -> dict:
    return {"kind": kind, "child_table": base["table"], "parent_table": base["parent_table"],
            "constraint": base["constraint"], "columns": list(base["columns"]), "path": base["path"],
            "child_in_write_set": base["child_in_write_set"], "child_also_deleted": base["child_also_deleted"]}


def footprint_to_json(footprint: Mapping[str, Any]) -> str:
    """Byte-reproducible JSON of a footprint."""
    return json.dumps(footprint, sort_keys=True)


# ---------------------------------------------------------------------------------------------
# Impact-statement section
# ---------------------------------------------------------------------------------------------

def _render_path(path: Sequence[Mapping[str, Any]]) -> str:
    if not path:
        return ""
    s = path[0]["from"]
    for h in path:
        s += f" -[{h['on_delete']} {','.join(h['columns'])}]-> {h['to']}"
    return s


def impact_statement_footprint_section(footprint: Mapping[str, Any]) -> list[str]:
    """Human-readable lines an impact statement embeds. Unknown and incomplete readings are stated loudly."""
    fp = footprint
    c = fp["counts"]
    complete = fp["fk_closure_status"] == "COMPLETE"
    n_edges = c["edges_considered"]
    lines = [
        "Transitive write/delete footprint (pg_constraint closure, E5.9)",
        f"  write set ({c['write_tables']}): {', '.join(fp['write_tables'])}",
        f"  FK closure: {fp['fk_closure_status']} over {n_edges} catalog FK edge(s)"
        f" [universe: {fp['universe']['source']}]",
    ]
    for r in fp["incomplete_reasons"]:
        lines.append(f"  ! INCOMPLETE: {r}")
    if fp["unknown_tables"]:
        lines.append(f"  UNKNOWN tables ({c['unknown_tables']}) -- footprint NOT computed for these, "
                     "this is not a clean reading:")
        lines += [f"    - {u['table']}: {u['reason']}" for u in fp["unknown_tables"]]
    if fp["no_fk_edges_tables"]:
        lines.append(f"  Confirmed no FK edges ({c['no_fk_edges_tables']}): {', '.join(fp['no_fk_edges_tables'])}")

    def section(title: str, entries: Sequence[Mapping[str, Any]], line_fn, zero_text: str) -> None:
        if entries:
            lines.append(f"  {title} ({len(entries)}):")
            lines.extend(line_fn(e) for e in entries)
        elif complete:
            lines.append(f"  {title} (0): {zero_text} (computed over {n_edges} catalog FK edge(s))")
        else:
            lines.append(f"  {title} (0 found in the edges supplied; not a clean reading while INCOMPLETE)")

    section("CASCADE deletes", fp["delete_cascades"],
            lambda e: f"    - {e['table']}  depth {e['depth']}: {_render_path(e['path'])}",
            "none beyond the write set")
    section("SET NULL", fp["set_null"],
            lambda e: (f"    - {e['table']}.{','.join(e['columns'])}  depth {e['depth']}: {_render_path(e['path'])}"
                       + ("  ** NOT NULL column: the delete would be refused" if e["violates_not_null"] else "")
                       + ("  (rows also deleted by cascade)" if e["child_also_deleted"] else "")),
            "none")
    section("SET DEFAULT", fp["set_default"],
            lambda e: (f"    - {e['table']}.{','.join(e['columns'])}  depth {e['depth']}: {_render_path(e['path'])}"
                       "  (default must satisfy the FK or the delete fails)"),
            "none")
    section("REFUSING edges (blockers)", fp["refusing"],
            lambda e: (f"    - {e['kind']}: {e['child_table']}.{','.join(e['columns'])} -> {e['parent_table']}: "
                       f"{_render_path(e['path'])}"
                       + ("  (child also cascade-deleted; NO ACTION may pass at commit)"
                          if e["child_also_deleted"] else "")),
            "none")
    d = fp["dangling_after_rewrite"]
    lines.append(f"  Dangling references after rewrite: UNKNOWN ({d['status']}) -- {d['note']}")
    if d["write_tables_with_no_inbound_fk"]:
        lines.append("    write tables with no inbound FK (any referencing rows are invisible to the catalog): "
                     + ", ".join(d["write_tables_with_no_inbound_fk"]))
    for r in d["known_non_fk_references"]:
        lines.append(f"    known non-FK reference: {r['referencing_table']}.{r['column']} -> {r['referenced_table']}")
    return lines


# ================================================================================================
# SECTION 2 -- E5.3 level-wave dispatcher (RESERVED: written by item E5.3, not by E5.9)
# ================================================================================================
