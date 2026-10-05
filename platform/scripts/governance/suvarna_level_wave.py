#!/usr/bin/env python3
"""suvarna_level_wave.py -- Suvarna Track E level-wave tooling.

SECTIONS (each item owns one section; add yours below the marker, do not edit another item's section)
  1. E5.9  transitive write/delete footprint from the pg_constraint closure   (pure: no CLI, no database of its own)
  2. E5.3  multi-asset level-wave dispatcher, its refusals, stop hook and wall-time report
           (CLI; the database is reached only through an injected connection factory; see README_level_wave.md)

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
  refusing         edges that REFUSE the delete immediately: RESTRICT, non-deferrable NO ACTION, and SET NULL
                   on a NOT NULL column -- the blockers
  refusing_deferrable
                   NO ACTION edges declared DEFERRABLE: they may pass at commit, so they are flagged apart,
                   but they stay in has_blockers (the catalog cannot show the data or the SET CONSTRAINTS)
  unknown_tables   write tables the edge list / catalog table list does not know: NOT "no footprint"
  dangling_after_rewrite
                   references that survive a rewrite in tables with NO foreign key are not computable from
                   pg_constraint; the field is always `unknown_not_in_catalog` and never an empty clean reading
  inherited_partition_edges
                   FK rows cloned onto partitions (conparentid <> 0), each tied to its root constraint
  limitations      what this reading cannot see (always present; see LIMITATIONS)

Earned-signal rule (CLAUDE.md section N.8): a footprint that cannot be wrong must not read as clean. An empty
edge list, or a write table outside the edge list's universe, yields `fk_closure_status: INCOMPLETE` with the
tables in `unknown_tables`. `COMPLETE` means ONLY "the foreign-key closure over the edges supplied is computed";
it says nothing about references that carry no foreign key (see dangling_after_rewrite).

Inputs
  edges        list of dicts: child_table, parent_table, on_delete, columns, child_columns_not_null, and
               optionally constraint, on_update, deferrable, deferred, inherited_from ({table, constraint} of
               the parent constraint a partition clone was cloned from), child_is_partition, parent_is_partition.
               on_delete is a name (CASCADE, SET NULL, SET DEFAULT, NO ACTION, RESTRICT) or the pg_constraint
               code letter (c, n, d, a, r); an unknown value raises. Tables are schema-qualified; a bare name
               means public.<name>. A missing `deferrable` reads as False (immediate: the conservative side).
  known_tables optional catalog table list (tables_from_catalog). With it, a table with no FK edges is a
               computed zero (`no_fk_edges_tables`); without it, the universe is the tables the edges mention
               and an FK-free write table is reported unknown (the catalog was not asked about it). An EMPTY
               edge list is INCOMPLETE either way: a populated plane with no foreign keys is implausible and the
               absence is not established.

Semantics (stricter reading when in doubt)
  * CASCADE closure is a breadth-first walk from the write set, level by level in sorted order, so the path
    reported for each table is the shortest one and ties break deterministically; cycles and self-references
    terminate (each table is reached once).
  * A table in the write set is not listed as a cascade side effect (the writers already own it), but its own
    children are still traversed from it.
  * SET NULL does not propagate: a nulled row is not a deleted row, so its own children are untouched.
  * NO ACTION / RESTRICT are listed as refusing even when the child is also cascade-deleted in the same
    statement (`child_also_deleted: true` says so); NO ACTION can pass when the referencing rows are gone by
    commit, and the catalog cannot show the data, so the caller decides with the flag in hand.
  * Partitions: a FK on a partitioned table is cloned onto every partition. A child-side clone (same referenced
    table as its root edge, resolved through conparentid) is COLLAPSED into the root edge so the closure and the
    counts do not double-count; a referenced-side clone (it points at a partition) is KEPT, because a write set
    may name a partition directly, and its path hops and entries carry `inherited` / `inherited_edge_in_path`.
    Every inherited row is listed in `inherited_partition_edges` (collapsed or kept), never silently dropped.
  * Output is sorted everywhere and has no timestamps: json.dumps(sort_keys=True) is byte-reproducible.

The loaders take an already-open DB-API connection and pass ONLY this module's two fixed SQL constants to
_run_select. assert_select_only is a guard on those constants (a regression tripwire if someone edits them), NOT a
general SQL sandbox: its keyword blocklist is not exhaustive and it must never be handed caller-supplied SQL
(_run_select stays private and the public loaders take no SQL). Read-only-ness is to be enforced by the
connection itself (a read-only role such as suvarna_reader, or a READ ONLY transaction): the loaders never issue
SET / BEGIN / COMMIT / ROLLBACK and never commit, roll back or close the caller's connection.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
import operator
import os
import re
import string
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "suvarna.e5_9.transitive_footprint/3"   # /3: has_blockers is bool | "unknown" in the dispatcher report (_footprint_report)
DEFAULT_SCHEMA = "public"

CASCADE = "CASCADE"
SET_NULL = "SET NULL"
SET_DEFAULT = "SET DEFAULT"
NO_ACTION = "NO ACTION"
RESTRICT = "RESTRICT"

# pg_constraint.confdeltype / confupdtype
_ACTION_CODES = {"a": NO_ACTION, "r": RESTRICT, "c": CASCADE, "n": SET_NULL, "d": SET_DEFAULT}
_ACTION_NAMES = {v: v for v in _ACTION_CODES.values()}

LIMITATIONS = (
    "FK edges only: triggers, rules, row-level security and application-side deletes are not in pg_constraint "
    "(e.g. the assert_l2_msr_delete_safe guard is not part of this closure)",
    "pg_constraint.confdelsetcols (PG15+ ON DELETE SET NULL (col, ...)) is not read, the server version being "
    "unknown: a column-list SET NULL is treated as nulling every FK column, so it can be over-reported as "
    "SET_NULL_ON_NOT_NULL (the safe direction)",
    "no row data is read: refusing edges are potential blockers (NO ACTION may pass at commit when the "
    "referencing rows are also removed), and SET DEFAULT may or may not satisfy its FK",
    "references that carry no foreign key are invisible to the catalog (see dangling_after_rewrite)",
    "partition clones are collapsed onto the root edge only when the root constraint is present in the edge list "
    "and references the same table; anything unresolved is kept and flagged in inherited_partition_edges",
)

# ---------------------------------------------------------------------------------------------
# Read-only catalog loaders
# ---------------------------------------------------------------------------------------------

FK_EDGE_COLUMNS = ("constraint", "child_table", "parent_table", "confdeltype", "confupdtype",
                   "child_columns", "child_columns_not_null", "deferrable", "deferred",
                   "inherited_from_table", "inherited_from_constraint", "child_is_partition",
                   "parent_is_partition")

# One row per foreign-key constraint. child_columns keeps constraint column order; child_columns_not_null is the
# subset of those columns declared NOT NULL (a SET NULL action on one of them cannot succeed). A constraint
# cloned onto a partition has conparentid <> 0; inherited_from_* names the constraint it was cloned from.
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
              ORDER BY k.ord) AS child_columns_not_null,
       con.condeferrable AS "deferrable",
       con.condeferred AS "deferred",
       rcn.nspname || '.' || rcc.relname AS inherited_from_table,
       rc.conname::text AS inherited_from_constraint,
       cc.relispartition AS child_is_partition,
       pc.relispartition AS parent_is_partition
  FROM pg_constraint con
  JOIN pg_class cc ON cc.oid = con.conrelid
  JOIN pg_namespace cn ON cn.oid = cc.relnamespace
  JOIN pg_class pc ON pc.oid = con.confrelid
  JOIN pg_namespace pn ON pn.oid = pc.relnamespace
  LEFT JOIN pg_constraint rc ON rc.oid = con.conparentid AND con.conparentid <> 0
  LEFT JOIN pg_class rcc ON rcc.oid = rc.conrelid
  LEFT JOIN pg_namespace rcn ON rcn.oid = rcc.relnamespace
 WHERE con.contype = 'f'
 ORDER BY child_table, parent_table, con.conname
"""

# Every ordinary / partitioned user table outside the system, toast and temp schemas (the catalog universe).
# A regex, not LIKE, so no backslash escape is needed.
TABLES_SQL = """
SELECT n.nspname || '.' || c.relname AS table_name
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE c.relkind IN ('r', 'p')
   AND n.nspname NOT IN ('pg_catalog', 'information_schema')
   AND n.nspname !~ '^pg_(toast|temp_)'
 ORDER BY 1
"""

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|INTO|COPY|CALL|DO|EXECUTE|MERGE|VACUUM|"
    r"REINDEX|CLUSTER|REFRESH|COMMENT|LOCK|SET|RESET|BEGIN|COMMIT|ROLLBACK|NEXTVAL|SETVAL|SET_CONFIG|"
    r"PG_TERMINATE_BACKEND|PG_CANCEL_BACKEND|PG_SLEEP\w*|PG_NOTIFY|PG_RELOAD_CONF|PG_ROTATE_LOGFILE|"
    r"PG_ADVISORY\w*|LO_IMPORT|LO_EXPORT|LO_UNLINK|DBLINK\w*)\b"
    r"|\bFOR\s+(UPDATE|SHARE|NO\s+KEY|KEY\s+SHARE)\b",
    re.IGNORECASE)

_DOLLAR_TAG = re.compile(r"\$((?:[^\W\d])\w*)?\$")


def _is_ident_char(ch: str) -> bool:
    return ch.isalnum() or ch in "_$" or ord(ch) > 127


def _lex_code(sql: str) -> str:
    """One left-to-right pass: the statement text with every literal and comment consumed in lexer order.

    String literals (with '' escapes; E'..' strings with backslash escapes), "quoted identifiers", $tag$
    dollar-quoted strings, -- line comments and nested /* */ comments are each replaced by a placeholder, so a
    comment opener inside a string (or a quote inside a comment) can never hide a statement separator.
    Unterminated constructs raise. A backslash inside a plain string raises (its meaning depends on
    standard_conforming_strings, so the lexer cannot know where the string ends).
    """
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif c == "/" and sql.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if sql.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif sql.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated block comment")
            out.append(" ")
        elif c == "'":
            escape = i > 0 and sql[i - 1] in "eE" and (i < 2 or not _is_ident_char(sql[i - 2]))
            i += 1
            closed = False
            while i < n:
                ch = sql[i]
                if ch == "\\":
                    if not escape:
                        raise ValueError("backslash inside a plain string literal is not allowed")
                    i += 2
                    continue
                if ch == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                raise ValueError("unterminated string literal")
            out.append("''")
        elif c == '"':
            i += 1
            closed = False
            while i < n:
                if sql[i] == '"':
                    if i + 1 < n and sql[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                raise ValueError("unterminated quoted identifier")
            out.append('""')
        elif c == "$" and not (i > 0 and _is_ident_char(sql[i - 1])):
            m = _DOLLAR_TAG.match(sql, i)
            if m is None:
                out.append(c)
                i += 1
            else:
                end = sql.find(m.group(0), m.end())
                if end < 0:
                    raise ValueError("unterminated dollar-quoted string")
                i = end + len(m.group(0))
                out.append("''")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def assert_select_only(sql: str) -> None:
    """Raise ValueError unless `sql` lexes to exactly one plain SELECT statement.

    SCOPE: a tripwire on this module's two fixed SQL constants, NOT a general sandbox. The keyword blocklist is
    not exhaustive; never pass caller-supplied SQL through it. Read-only must also be enforced by the connection
    (a read-only role or READ ONLY transaction).

    The statement is first lexed in one left-to-right pass (_lex_code), so a separator is recognised wherever
    the lexer says it is, regardless of comment openers or quotes inside literals. After that: no separator
    except one trailing ';', the statement must start with SELECT (WITH-queries are rejected: a data-modifying
    CTE hides a write behind a SELECT), and no write / DDL / session-state construct may appear.
    """
    if not isinstance(sql, str):
        raise ValueError("statement must be a string")
    s = _lex_code(sql).strip()
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


def _parse_pg_array_text(text: str) -> list[str]:
    """Parse PostgreSQL array text ('{a,"b,c","d\\"e"}'): quoted elements may hold commas, quotes, backslashes."""
    t = text.strip()
    if len(t) < 2 or t[0] != "{" or t[-1] != "}":
        raise ValueError(f"not a PostgreSQL array literal: {text!r}")
    inner, n, i = t[1:-1], len(t) - 2, 0
    items: list[str] = []
    while i < n:
        if inner[i] == '"':
            i += 1
            buf: list[str] = []
            while i < n and inner[i] != '"':
                if inner[i] == "\\" and i + 1 < n:
                    buf.append(inner[i + 1])
                    i += 2
                else:
                    buf.append(inner[i])
                    i += 1
            if i >= n:
                raise ValueError(f"unterminated quoted element in array literal: {text!r}")
            i += 1
            items.append("".join(buf))
        else:
            j = inner.find(",", i)
            j = n if j < 0 else j
            tok = inner[i:j].strip()
            if not tok or tok.upper() == "NULL":
                raise ValueError(f"empty or NULL element in array literal: {text!r}")
            items.append(tok)
            i = j
        if i < n:
            if inner[i] != ",":
                raise ValueError(f"malformed array literal: {text!r}")
            i += 1
            if i >= n:
                raise ValueError(f"trailing comma in array literal: {text!r}")
    return items


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):  # a driver that hands arrays back as PostgreSQL array text
        return _parse_pg_array_text(value)
    return [str(x) for x in value]


def _run_select(conn: Any, sql: str) -> list[Any]:
    """PRIVATE. Runs one of this module's fixed SQL constants; never exposed with caller-supplied SQL."""
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
    or closed, and no SET is issued. Zero rows returns [] -- transitive_footprint then reports INCOMPLETE.
    """
    edges = []
    for row in _run_select(conn, FK_EDGES_SQL):
        if hasattr(row, "keys"):
            rec = {k: row[k] for k in FK_EDGE_COLUMNS}
        else:
            if len(row) != len(FK_EDGE_COLUMNS):
                raise ValueError(f"catalog row has {len(row)} columns, expected {len(FK_EDGE_COLUMNS)}")
            rec = dict(zip(FK_EDGE_COLUMNS, row))
        src_table = rec["inherited_from_table"]
        edges.append({
            "constraint": rec["constraint"],
            "child_table": rec["child_table"],
            "parent_table": rec["parent_table"],
            "on_delete": _norm_action(rec["confdeltype"], "confdeltype"),
            "on_update": _norm_action(rec["confupdtype"], "confupdtype"),
            "columns": _as_list(rec["child_columns"]),
            "child_columns_not_null": _as_list(rec["child_columns_not_null"]),
            "deferrable": bool(rec["deferrable"]),
            "deferred": bool(rec["deferred"]),
            "inherited_from": (None if src_table is None else
                               {"table": src_table, "constraint": rec["inherited_from_constraint"]}),
            "child_is_partition": bool(rec["child_is_partition"]),
            "parent_is_partition": bool(rec["parent_is_partition"]),
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
    src = e.get("inherited_from")
    if src is not None:
        if "table" not in src or "constraint" not in src:
            raise ValueError(f"inherited_from needs table and constraint: {src!r}")
        src = {"table": _norm_table(src["table"]), "constraint": str(src["constraint"])}
    return {
        "child_table": _norm_table(e["child_table"]),
        "parent_table": _norm_table(e["parent_table"]),
        "on_delete": _norm_action(e["on_delete"]),
        "constraint": str(e.get("constraint") or ""),
        "columns": [str(c) for c in (e.get("columns") or [])],
        "child_columns_not_null": [str(c) for c in (e.get("child_columns_not_null") or [])],
        "deferrable": bool(e.get("deferrable", False)),
        "deferred": bool(e.get("deferred", False)),
        "inherited_from": src,
    }


def _edge_key(e: dict) -> tuple:
    src = e["inherited_from"]
    return (e["parent_table"], e["child_table"], e["constraint"], tuple(e["columns"]), e["on_delete"],
            tuple(e["child_columns_not_null"]), e["deferrable"], e["deferred"],
            (src["table"], src["constraint"]) if src else ("", ""))


def _hop(e: dict) -> dict:
    return {"from": e["parent_table"], "to": e["child_table"], "constraint": e["constraint"],
            "columns": list(e["columns"]), "on_delete": e["on_delete"],
            "inherited": e["inherited_from"] is not None}


def _sort_key(entry: dict) -> tuple:
    return (entry["table"], entry.get("constraint", ""), tuple(entry.get("columns", ())))


def _resolve_root(e: dict, by_key: dict) -> dict | None:
    """The un-inherited root edge of a partition clone, or None when the chain cannot be resolved."""
    cur, seen = e, set()
    while cur["inherited_from"] is not None:
        k = (cur["inherited_from"]["table"], cur["inherited_from"]["constraint"])
        if k in seen:
            return None
        seen.add(k)
        cur = by_key.get(k)
        if cur is None:
            return None
    return cur


def _collapse_partition_clones(edge_list: list[dict]) -> tuple[list[dict], list[dict]]:
    """(edges kept for the closure, inherited_partition_edges report). See the module docstring."""
    by_key = {(e["child_table"], e["constraint"]): e for e in edge_list}
    kept, report = [], []
    for e in edge_list:
        if e["inherited_from"] is None:
            kept.append(e)
            continue
        root = _resolve_root(e, by_key)
        collapsed = root is not None and root["parent_table"] == e["parent_table"]
        report.append({
            "child_table": e["child_table"], "parent_table": e["parent_table"], "constraint": e["constraint"],
            "collapsed": collapsed,
            "root": None if root is None else {"child_table": root["child_table"],
                                               "parent_table": root["parent_table"],
                                               "constraint": root["constraint"]},
        })
        if not collapsed:
            kept.append(e)
    report.sort(key=lambda r: (r["child_table"], r["parent_table"], r["constraint"]))
    return kept, report


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
    all_edges = [uniq[k] for k in sorted(uniq)]
    # universe and inbound-FK facts come from every edge, before any partition clone is collapsed away
    edge_universe = {e["parent_table"] for e in all_edges} | {e["child_table"] for e in all_edges}
    parents_with_inbound = {e["parent_table"] for e in all_edges}
    edge_list, inherited_report = _collapse_partition_clones(all_edges)
    out_edges: dict[str, list[dict]] = {}
    for e in edge_list:
        out_edges.setdefault(e["parent_table"], []).append(e)

    known = None if known_tables is None else {_norm_table(t) for t in known_tables}
    universe = edge_universe if known is None else (edge_universe | known)

    unknown, no_fk, incomplete = [], [], []
    for t in write:
        if all_edges and t in universe:
            if t not in edge_universe:
                no_fk.append(t)
            continue
        if not all_edges:
            reason = "no FK edges in the catalog, so the absence of this table's edges is not established"
        elif known is None:
            reason = "not in the edge list's universe (no FK edge names it; no catalog table list was supplied)"
        else:
            reason = "not in the catalog table list and no FK edge names it"
        unknown.append({"table": t, "reason": reason})
    if not all_edges:
        incomplete.append("no FK edges in catalog; implausible for a populated plane, verify catalog access")
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

    def inherited_in(path: Sequence[Mapping[str, Any]]) -> bool:
        return any(h["inherited"] for h in path)

    delete_cascades = [{"table": t, "depth": len(p), "path": p, "inherited_edge_in_path": inherited_in(p)}
                       for t, p in reached.items() if t not in write_set]

    # --- non-cascading actions out of every table whose rows are deleted (write set + cascade closure) ---
    set_null, set_default, refusing, refusing_deferrable = [], [], [], []
    for parent in sorted(reached):
        for e in out_edges.get(parent, ()):
            act = e["on_delete"]
            if act == CASCADE:
                continue
            path = reached[parent] + [_hop(e)]
            base = {"table": e["child_table"], "parent_table": parent, "constraint": e["constraint"],
                    "columns": list(e["columns"]), "depth": len(path), "path": path,
                    "child_in_write_set": e["child_table"] in write_set,
                    "child_also_deleted": e["child_table"] in reached,
                    "inherited_edge_in_path": inherited_in(path),
                    "deferrable": e["deferrable"], "deferred": e["deferred"]}
            if act in (SET_NULL, SET_DEFAULT):
                nn = [c for c in e["columns"] if c in set(e["child_columns_not_null"])]
                entry = {k: v for k, v in base.items() if k not in ("deferrable", "deferred")}
                entry.update(not_null_columns=nn, violates_not_null=bool(nn) and act == SET_NULL)
                (set_null if act == SET_NULL else set_default).append(entry)
                if entry["violates_not_null"]:
                    refusing.append(_refusal("SET_NULL_ON_NOT_NULL", base, deferrable=False))
            elif act == NO_ACTION and e["deferrable"]:
                refusing_deferrable.append(_refusal(NO_ACTION, base, deferrable=True))
            else:  # RESTRICT (never deferrable) / immediate NO ACTION
                refusing.append(_refusal(act, base, deferrable=False))

    delete_cascades.sort(key=lambda x: x["table"])
    for lst in (set_null, set_default):
        lst.sort(key=_sort_key)
    for lst in (refusing, refusing_deferrable):
        lst.sort(key=lambda r: (r["child_table"], r["constraint"], tuple(r["columns"]), r["kind"]))

    no_inbound = [t for t in write if t in universe and t not in parents_with_inbound]
    known_refs = []
    for r in known_non_fk_references or ():
        for k in ("referencing_table", "column", "referenced_table"):
            if k not in r:
                raise ValueError(f"known_non_fk_references entry is missing {k!r}: {r!r}")
        referenced, referencing = _norm_table(r["referenced_table"]), _norm_table(r["referencing_table"])
        if referenced in write_set:
            known_refs.append({"referencing_table": referencing, "column": str(r["column"]),
                               "referenced_table": referenced})
    known_refs.sort(key=lambda r: (r["referencing_table"], r["column"], r["referenced_table"]))

    via_inherited = sum(1 for lst in (delete_cascades, set_null, set_default, refusing, refusing_deferrable)
                        for x in lst if x["inherited_edge_in_path"])
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
        "refusing_deferrable": refusing_deferrable,
        "has_blockers": bool(refusing or refusing_deferrable),
        "has_immediate_blockers": bool(refusing),
        "inherited_partition_edges": inherited_report,
        "dangling_after_rewrite": {
            "status": "unknown_not_in_catalog",
            "note": ("references that survive a delete-then-insert in tables with no foreign key are not "
                     "computable from pg_constraint; measure after the wave "
                     "(msr_dangling_signal_refs.py, msr_referential_integrity.py)"),
            "write_tables_with_no_inbound_fk": no_inbound,
            "known_non_fk_references": known_refs,
        },
        "limitations": list(LIMITATIONS),
        "counts": {
            "write_tables": len(write), "delete_cascades": len(delete_cascades), "set_null": len(set_null),
            "set_default": len(set_default), "refusing": len(refusing),
            "refusing_deferrable": len(refusing_deferrable), "unknown_tables": len(unknown),
            "no_fk_edges_tables": len(no_fk), "edges_considered": len(edge_list),
            "inherited_partition_edges_collapsed": sum(1 for r in inherited_report if r["collapsed"]),
            "inherited_partition_edges_kept": sum(1 for r in inherited_report if not r["collapsed"]),
            "entries_via_inherited_edges": via_inherited,
        },
    }


def _refusal(kind: str, base: dict, *, deferrable: bool) -> dict:
    return {"kind": kind, "child_table": base["table"], "parent_table": base["parent_table"],
            "constraint": base["constraint"], "columns": list(base["columns"]), "path": base["path"],
            "child_in_write_set": base["child_in_write_set"], "child_also_deleted": base["child_also_deleted"],
            "deferrable": deferrable, "deferred": base["deferred"] if deferrable else False,
            "inherited_edge_in_path": base["inherited_edge_in_path"]}


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
    # a PARTIAL footprint scope (footprint_scope, set by _footprint_report) is never a clean "0 found"
    complete = fp["fk_closure_status"] == "COMPLETE" and fp.get("footprint_scope", "complete") != "partial"
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
    n_inh = c["inherited_partition_edges_collapsed"] + c["inherited_partition_edges_kept"]
    if n_inh:
        lines.append(f"  Partition-inherited FK rows: {n_inh} ({c['inherited_partition_edges_collapsed']} collapsed "
                     f"into their root edge, {c['inherited_partition_edges_kept']} kept and flagged)")

    def section(title: str, entries: Sequence[Mapping[str, Any]], line_fn, zero_text: str) -> None:
        if entries:
            lines.append(f"  {title} ({len(entries)}):")
            lines.extend(line_fn(e) for e in entries)
        elif complete:
            lines.append(f"  {title} (0): {zero_text} (computed over {n_edges} catalog FK edge(s))")
        else:
            lines.append(f"  {title} (0 found in the edges supplied; not a clean reading while INCOMPLETE or PARTIAL)")

    inh = lambda e: "  [via partition-inherited FK]" if e["inherited_edge_in_path"] else ""  # noqa: E731
    section("CASCADE deletes", fp["delete_cascades"],
            lambda e: f"    - {e['table']}  depth {e['depth']}: {_render_path(e['path'])}{inh(e)}",
            "none beyond the write set")
    section("SET NULL", fp["set_null"],
            lambda e: (f"    - {e['table']}.{','.join(e['columns'])}  depth {e['depth']}: {_render_path(e['path'])}"
                       + ("  ** NOT NULL column: the delete would be refused" if e["violates_not_null"] else "")
                       + ("  (rows also deleted by cascade)" if e["child_also_deleted"] else "") + inh(e)),
            "none")
    section("SET DEFAULT", fp["set_default"],
            lambda e: (f"    - {e['table']}.{','.join(e['columns'])}  depth {e['depth']}: {_render_path(e['path'])}"
                       "  (default must satisfy the FK or the delete fails)" + inh(e)),
            "none")
    section("REFUSING edges (immediate blockers)", fp["refusing"],
            lambda e: (f"    - {e['kind']}: {e['child_table']}.{','.join(e['columns'])} -> {e['parent_table']}: "
                       f"{_render_path(e['path'])}"
                       + ("  (child also cascade-deleted; NO ACTION may pass at commit)"
                          if e["child_also_deleted"] else "") + inh(e)),
            "none")
    section("REFUSING edges, DEFERRABLE NO ACTION (may pass at commit; still counted as blockers)",
            fp["refusing_deferrable"],
            lambda e: (f"    - {e['kind']}: {e['child_table']}.{','.join(e['columns'])} -> {e['parent_table']}: "
                       f"{_render_path(e['path'])}" + ("  (initially deferred)" if e["deferred"] else "") + inh(e)),
            "none")
    d = fp["dangling_after_rewrite"]
    lines.append(f"  Dangling references after rewrite: UNKNOWN ({d['status']}) -- {d['note']}")
    if d["write_tables_with_no_inbound_fk"]:
        lines.append("    write tables with no inbound FK (any referencing rows are invisible to the catalog): "
                     + ", ".join(d["write_tables_with_no_inbound_fk"]))
    for r in d["known_non_fk_references"]:
        lines.append(f"    known non-FK reference: {r['referencing_table']}.{r['column']} -> {r['referenced_table']}")
    lines.append("  Limitations of this reading:")
    lines += [f"    - {x}" for x in fp["limitations"]]
    return lines


# ================================================================================================
# SECTION 2 -- E5.3 level-wave dispatcher (multi-asset manifest builder, refusals, stop hook, wall-time report)
# ================================================================================================
# Builds ONE frozen run manifest (`nirmana-run-manifest/v1`) for an explicit asset list, the same way
# platform/scripts/dispatch_frozen_rebuild.py does for one asset: same canonical-JSON digest, same registry-row and
# nirmana-writer-digests.json inputs, same INSERT shape. What is new: WAVES derived from depends_on, the refusals
# below, a stop hook between waves, and a per-asset wall-time report.
#
# STATUS: NEVER EXECUTED IN PRODUCTION above 17 assets / 1 wave (the largest run on record, 2026-09-04, L0). A
# 23-asset or multi-wave run has never run. See platform/scripts/governance/README_level_wave.md. Exec Suvarna runs it;
# the tests below use fakes and fixtures only.
#
# WHAT THE RUNNER DOES (read, not touched: pipeline/orchestrator/runner.py, asset_runner.py -- FROZEN):
#   * validate_frozen_run_manifest: digest, version, chart, scope/scope_target/action == the build_runs row,
#     flatten(waves) == plan exactly, one asset entry per plan id in plan order, 64-hex expected_code_digest.
#   * _verify_sidecar_code_matches_manifest: expected_code_digest == the DEPLOYED job image's writer hash (image skew).
#   * _verify_registry_still_matches_manifest: scope, sorted depends_on, natural_key_partition, has_cowriters.
#   * asset_runner.deps_unsatisfied (DEP-ASSERT): every DECLARED dependency lit AND fresh (service deps: lit only).
#   * scheduling comes from each asset's depends_on in the manifest, NOT from wave boundaries. One run executes every
#     wave; the runner has NO hook between waves.
# THEREFORE the stop hook is implemented here, outside the runner, as `--mode wave-by-wave`: one run per wave, each
# manifest holding only that wave (the earlier waves are then ordinary out-of-set dependencies, which DEP-ASSERT and
# this script require to be lit+fresh), with an operator pause between runs. `--mode single-run` submits one manifest
# with all waves and has no pause: a documented limitation, not a bug.

MANIFEST_VERSION = "nirmana-run-manifest/v1"
TRIGGERED_BY = "suvarna-e5-3-level-wave"
LEVEL_WAVE_SCHEMA = "suvarna.e5_3.level_wave/1"
NEVER_EXECUTED_NOTE = (
    "NEVER EXECUTED IN PRODUCTION above 17 assets / 1 wave. A multi-wave or 23-asset manifest has never run; the "
    "runner supports N assets and waves structurally (read, not executed). Dry-run first, read the receipt."
)
REPO_ROOT = Path(__file__).resolve().parents[3]
WRITER_DIGESTS_REL = "platform/src/generated/nirmana-writer-digests.json"
FAMILY_FILE_REL = "00_ARCHITECTURE/control/FAMILY_ASSETS.json"
FAMILY_LIST_KEYS = ("family_gochara", "family_sangam", "family_kshetra",
                    "family_readers_L3", "family_readers_L4", "family_readers_L5")
# The Pravaha gochara family by NAME, enforced even when FAMILY_ASSETS.json is absent or unreadable.
FAMILY_NAME_PATTERN = re.compile(r"^(ka_gochara|ka_vedha_gochara|gochara_|bg_gochara_|kala_gochara_)")
TERMINAL_RUN_STATES = ("completed", "stopped", "failed")
_HEX64 = re.compile(r"[0-9a-f]{64}")

# Exit codes (documented in --help and the README): 0 ok / dry run done, 1 DATABASE_URL missing, 2 bad input or internal
# inconsistency (nothing dispatched), 3 dispatch failed after the run was committed (planned run terminalised, or a
# chart-blocking WARNING is printed), 4 a gate refused, 5 wave-by-wave campaign stopped (refusal, operator, run or asset
# not complete), 6 unexpected exception or database error (the JSON summary lists every run committed so far).
EXIT_NO_DATABASE_URL = 1
EXIT_BAD_INPUT = 2
EXIT_DISPATCH_FAILED = 3
REFUSAL_EXIT_CODE = 4
EXIT_CAMPAIGN_STOPPED = 5
EXIT_UNEXPECTED = 6
EXIT_INTERRUPTED = 7        # SIGINT / SIGTERM: the summary lists every run committed so far and the BLOCKS-chart warning


class LevelWaveError(Exception):
    """Bad input or an internal inconsistency; nothing was dispatched."""


class CommitOutcomeUnknown(Exception):
    """The connection failed during COMMIT: the run may or may not exist. Never reported as "no run was committed"."""

    def __init__(self, run_id: str, chart_id: str, cause: BaseException):
        self.run_id, self.chart_id = run_id, chart_id
        self.detail = (f"COMMIT outcome unknown for run {run_id} (chart {chart_id}): the connection failed during COMMIT "
                       f"({type(cause).__name__}: {cause}). Run the ACTIVE_RUN check before any relaunch: a planned/running "
                       f"run for the chart means it committed (find it by run_id), none means it did not.")
        super().__init__(self.detail)


class LevelWaveRefusal(LevelWaveError):
    """A gate refused. `.refusals` is a list of {code, ...} dicts; nothing was inserted or dispatched."""

    def __init__(self, refusals: Sequence[Mapping[str, Any]]):
        self.refusals = [dict(r) for r in refusals]
        super().__init__("; ".join(f"{r['code']}: {r.get('detail', '')}" for r in self.refusals))


def canonical_json(value: object) -> str:
    """Same bytes as dispatch_frozen_rebuild._canonical_json and runner._canonical_manifest_digest."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------
# Scope: explicit asset list
# ---------------------------------------------------------------------------------------------

def parse_asset_scope(values: Sequence[str]) -> list[str]:
    """`--assets` forms (comma list, repeated flag, `@file`) with asset_census.parse_assets_arg semantics: empty,
    duplicate, malformed or miscased ids are errors, never silently normalised. Order is the caller's."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import asset_census  # noqa: PLC0415  (heavy module; imported only when a scope is parsed)
    try:
        return asset_census.parse_assets_arg(list(values))
    except asset_census.ScopeError as exc:
        raise LevelWaveError(f"asset scope refused: {exc}") from exc


# ---------------------------------------------------------------------------------------------
# Family refusals (Pravaha gochara family; never fail open)
# ---------------------------------------------------------------------------------------------

GIT_TIMEOUT_SECONDS = 30
GCLOUD_TIMEOUT_SECONDS = 120


def _git(repo: str, args: Sequence[str]) -> subprocess.CompletedProcess:
    """git in `repo`: never prompts (GIT_TERMINAL_PROMPT=0, stdin closed) and never hangs (timeout). A timeout reads as a
    failed command (rc 124), which every caller already treats as a refusal or as `unverified`."""
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False,
                              timeout=GIT_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(list(args), 124, "", f"git {args[0]} timed out after {GIT_TIMEOUT_SECONDS}s")


def load_family_info(repo: str, ref: str = "origin/main", *, git=_git) -> dict:
    """Read FAMILY_ASSETS.json at `ref` (committed content, never the working tree).

    Returns {"state": "absent"} when the ref is readable and the file is not in it, or
    {"state": "present", "family_set": frozenset, "families": {name: frozenset}}.
    Raises LevelWaveRefusal(FAMILY_FILE_UNREADABLE) for everything else: an unreadable ref, a failing `git show`,
    invalid JSON, a missing or mistyped key, or a family_set that is not the union of the six lists.
    """
    def unreadable(why: str) -> LevelWaveRefusal:
        return LevelWaveRefusal([{"code": "FAMILY_FILE_UNREADABLE", "detail": f"{FAMILY_FILE_REL} at {ref}: {why}"}])

    head = git(repo, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if head.returncode != 0:
        raise unreadable(f"ref not resolvable ({(head.stderr or '').strip()[:200]})")
    listed = git(repo, ["ls-tree", "--name-only", ref, "--", FAMILY_FILE_REL])
    if listed.returncode != 0:
        raise unreadable(f"git ls-tree failed ({(listed.stderr or '').strip()[:200]})")
    if not (listed.stdout or "").strip():
        return {"state": "absent"}
    shown = git(repo, ["show", f"{ref}:{FAMILY_FILE_REL}"])
    if shown.returncode != 0:
        raise unreadable(f"git show failed ({(shown.stderr or '').strip()[:200]})")
    try:
        doc = json.loads(shown.stdout)
    except (TypeError, ValueError) as exc:
        raise unreadable(f"not valid JSON ({exc})") from exc
    if not isinstance(doc, dict):
        raise unreadable("top level is not an object")
    lists: dict[str, frozenset] = {}
    for key in (*FAMILY_LIST_KEYS, "family_set"):
        val = doc.get(key)
        if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
            raise unreadable(f"{key!r} is missing or not a list of asset ids")
        lists[key] = frozenset(val)
    union = frozenset().union(*(lists[k] for k in FAMILY_LIST_KEYS))
    if union != lists["family_set"]:
        raise unreadable("family_set is not the union of the six family lists")
    return {"state": "present", "family_set": lists["family_set"],
            "families": {k: lists[k] for k in FAMILY_LIST_KEYS}}


def family_refusals(assets: Sequence[str], family: Mapping[str, Any], *, committing: bool) -> list[dict]:
    """Every family problem in the request, all reported together. Empty list = clear."""
    req = set(assets)
    out: list[dict] = []
    for a in sorted(req):
        if FAMILY_NAME_PATTERN.match(a):
            out.append({"code": "FAMILY_ASSET", "asset": a, "via": "name_pattern",
                        "detail": f"{a} matches the Pravaha gochara family name pattern (ka_gochara*, ka_vedha_gochara*, gochara_*, bg_gochara_*, kala_gochara_*)"})
    state = family.get("state")
    if state == "present":
        for a in sorted(req & family["family_set"]):
            if not FAMILY_NAME_PATTERN.match(a):
                out.append({"code": "FAMILY_ASSET", "asset": a, "via": "family_set",
                            "detail": f"{a} is in FAMILY_ASSETS.json family_set"})
        for name, members in sorted(family["families"].items()):
            have, missing = req & members, members - req
            if have and missing:
                out.append({"code": "SPLITS_FAMILY", "family": name, "requested": sorted(have),
                            "missing": sorted(missing),
                            "detail": f"{name}: asks for {sorted(have)} without {sorted(missing)}"})
    elif state == "absent":
        if committing:
            out.append({"code": "FAMILY_FILE_MISSING",
                        "detail": f"{FAMILY_FILE_REL} is not on the family ref: a real dispatch needs it; only the "
                                  "name-pattern check could run"})
    else:
        raise LevelWaveError(f"unknown family state {state!r}")
    return out


# ---------------------------------------------------------------------------------------------
# Waves: longest path inside the requested set
# ---------------------------------------------------------------------------------------------

def _effective_inset_deps(members: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    """For each member, the IN-SET assets it must come after: its direct in-set dependencies plus every in-set ancestor
    reached THROUGH out-of-set assets (A depends on E outside the set, E depends on B inside it => A after B).
    The walk looks through out-of-set assets only; an in-set asset is a stop (its own ordering is its own). A path
    that leads back to the member itself is kept as a self-edge so it is reported as a cycle."""
    inset = set(members)
    out: dict[str, list[str]] = {}
    for a in sorted(inset):
        found: set[str] = set()
        seen: set[str] = set()
        stack = list(depends_on.get(a) or ())
        while stack:
            d = stack.pop()
            if d == a:
                found.add(a)
            elif d in inset:
                found.add(d)
            elif d not in seen:
                seen.add(d)
                stack.extend(depends_on.get(d) or ())
        out[a] = sorted(found)
    return out


def derive_waves(assets: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> list[list[str]]:
    """wave(a) = 0 if a has no ordering dependency inside the requested set, else 1 + max(wave(d)) over them (the longest
    path). Ordering dependencies are the direct in-set dependencies PLUS in-set ancestors reached through out-of-set
    assets, when `depends_on` carries the out-of-set assets' own dependencies (read_dependency_closure supplies them).
    Dependencies outside the set otherwise do not move an asset (they must already be lit+fresh:
    check_external_dependencies). Ids inside a wave are sorted, so the plan (flattened waves) is deterministic.
    A cycle (self-dependency or a loop through out-of-set assets included) raises. Input order is irrelevant."""
    members = sorted(set(assets))
    if len(members) != len(list(assets)):
        raise LevelWaveError("asset list has duplicates")
    inside = _effective_inset_deps(members, depends_on)
    wave: dict[str, int] = {}
    remaining = set(members)
    while remaining:
        ready = sorted(a for a in remaining if all(d in wave for d in inside[a]))
        if not ready:
            raise LevelWaveError("dependency cycle inside the requested set: " + ", ".join(sorted(remaining)))
        for a in ready:
            wave[a] = 1 + max((wave[d] for d in inside[a]), default=-1)
        remaining -= set(ready)
    out: list[list[str]] = [[] for _ in range(max(wave.values()) + 1)]
    for a in members:
        out[wave[a]].append(a)
    return out


def at_risk_intermediates(assets: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> list[dict]:
    """Out-of-set assets E that an in-set asset A depends on (directly or through other outside assets) and that themselves
    depend on an in-set asset B. Rebuilding B can make E's receipt stale, and A's DEPENDENCY_NOT_READY at its own wave then
    follows: the operator sees the risk in the dry run, before the live run. Needs the out-of-set rows in `depends_on`."""
    inset = set(assets)
    memo: dict[str, set[str]] = {}

    def below(e: str, stack: frozenset = frozenset()) -> set[str]:
        if e in memo:
            return memo[e]
        found: set[str] = set()
        for d in depends_on.get(e) or ():
            if d in inset:
                found.add(d)
            elif d not in stack and d != e:
                found |= below(d, stack | {e})
        memo[e] = found
        return found

    needed_by: dict[str, set[str]] = {}
    for a in sorted(inset):
        seen: set[str] = set()
        todo = [d for d in (depends_on.get(a) or ()) if d not in inset]
        while todo:
            e = todo.pop()
            if e in seen:
                continue
            seen.add(e)
            needed_by.setdefault(e, set()).add(a)
            todo.extend(d for d in (depends_on.get(e) or ()) if d not in inset)
    return [{"asset": e, "depends_on_in_set": sorted(below(e)), "needed_by": sorted(by)}
            for e, by in sorted(needed_by.items()) if below(e)]


def external_dependencies(assets: Sequence[str], depends_on: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    """{asset: sorted declared dependencies that are NOT in the requested set} (only assets that have any)."""
    inset = set(assets)
    out = {}
    for a in sorted(inset):
        ext = sorted({d for d in (depends_on.get(a) or ()) if d not in inset})
        if ext:
            out[a] = ext
    return out


# ---------------------------------------------------------------------------------------------
# Registry rows, manifest, digests
# ---------------------------------------------------------------------------------------------

CANDIDATES_SQL = """
SELECT ar.asset_id, ar.layer, ar.scope, ar.asset_kind, ar.is_active, ar.has_writer,
       ar.target_table, ar.writer_timeout_seconds, ar.estimated_seconds,
       COALESCE(ar.depends_on, '{}') AS depends_on,
       ar.natural_key_partition,
       EXISTS (
         SELECT 1 FROM asset_registry peer
          WHERE peer.target_table = ar.target_table
            AND ar.target_table IS NOT NULL
            AND peer.asset_id <> ar.asset_id
            AND peer.is_active = true AND peer.has_writer = true
       ) AS has_cowriters
  FROM asset_registry ar
 WHERE ar.asset_id = ANY(%s)
 ORDER BY ar.asset_id
"""

DEPS_SQL = """
SELECT dep.asset_id, reg.asset_kind, t.state, f.freshness_state
FROM unnest(%s::text[]) AS dep(asset_id)
LEFT JOIN asset_registry reg ON reg.asset_id = dep.asset_id
LEFT JOIN LATERAL (
    SELECT state FROM asset_throughput at
    WHERE at.asset_id = dep.asset_id
      AND (at.chart_id IS NOT DISTINCT FROM %s OR at.chart_id IS NULL)
    ORDER BY (at.chart_id IS NOT DISTINCT FROM %s) DESC, at.last_built_at DESC NULLS LAST
    LIMIT 1
) t ON true
LEFT JOIN LATERAL (
    SELECT freshness_state FROM asset_freshness af
    WHERE af.asset_id = dep.asset_id
      AND (af.chart_id IS NOT DISTINCT FROM %s OR af.chart_id IS NULL)
    ORDER BY (af.chart_id IS NOT DISTINCT FROM %s) DESC, af.observed_at DESC
    LIMIT 1
) f ON true
"""

# ---------------------------------------------------------------------------------------------
# DEPS_SQL parity with the FROZEN runner (asset_runner.deps_unsatisfied)
# ---------------------------------------------------------------------------------------------
# DEPS_SQL is a COPY of the dependency query the runner's DEP-ASSERT executes (asset_runner.py is FROZEN and is only read,
# as text, here; its path is ASSET_RUNNER_REL, defined with the force-marker constants below). The dispatcher's pre-check
# (check_external_dependencies) is only as good as that copy: if the runner's query changes and this one does not, the
# pre-check approves what the runner then refuses (or the reverse). The parity check extracts the runner's statement by a
# deterministic parse (ast) of the file text at a given git ref and compares it with DEPS_SQL modulo whitespace. Extraction
# that finds nothing, or more than one candidate, RAISES: a check that cannot read its subject is a failure, never a pass
# and never a skip.

RUNNER_DEPS_FUNCTION = "deps_unsatisfied"
_RUNNER_SQL_START = re.compile(r"\A\s*SELECT\s+dep\.asset_id\b")


class RunnerSqlExtractionError(LevelWaveError):
    """The runner's dependency SQL could not be extracted (or read) unambiguously: parity is UNVERIFIED, not true."""


def collapse_sql_whitespace(sql: str) -> str:
    """Every run of whitespace -> one space, ends trimmed. The only normalisation the parity check applies."""
    return " ".join(sql.split())


def extract_runner_deps_sql(text: str) -> str:
    """The dependency statement inside `def deps_unsatisfied` of the runner source `text`, exactly as written.

    The candidate is a plain (non-f) string literal in that function that starts with `SELECT dep.asset_id` and ends with
    `) f ON true`. Raises RunnerSqlExtractionError for: unparseable text, the function missing or defined more than once,
    and zero or several candidates (an f-string or a `+`-built statement is not a candidate, so it raises rather than
    matching a fragment)."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError) as exc:
        raise RunnerSqlExtractionError(f"runner source is not parseable: {exc}") from exc
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == RUNNER_DEPS_FUNCTION]
    if len(fns) != 1:
        raise RunnerSqlExtractionError(f"expected exactly one def {RUNNER_DEPS_FUNCTION}, found {len(fns)}")
    inside_fstring = {id(v) for n in ast.walk(fns[0]) if isinstance(n, ast.JoinedStr) for v in n.values}
    found = []
    for n in ast.walk(fns[0]):
        if (isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in inside_fstring
                and _RUNNER_SQL_START.match(n.value) and collapse_sql_whitespace(n.value).endswith(") f ON true")):
            found.append(n.value)
    if len(found) != 1:
        raise RunnerSqlExtractionError(
            f"expected exactly one dependency SQL literal in {RUNNER_DEPS_FUNCTION}, found {len(found)}")
    return found[0]


def deps_sql_matches_runner(runner_text: str, deps_sql: str | None = None) -> bool:
    """True iff DEPS_SQL (or `deps_sql`) equals the runner's statement modulo whitespace. Raises if it cannot be extracted."""
    return collapse_sql_whitespace(DEPS_SQL if deps_sql is None else deps_sql) == \
        collapse_sql_whitespace(extract_runner_deps_sql(runner_text))


def runner_text_at_ref(repo: str | Path, ref: str = "HEAD", *, git=_git) -> str:
    """asset_runner.py as COMMITTED at `ref` (`git show`; local objects only, no network). Raises
    RunnerSqlExtractionError when git cannot produce it."""
    shown = git(str(repo), ["show", f"{ref}:{ASSET_RUNNER_REL}"])
    if shown.returncode != 0:
        raise RunnerSqlExtractionError(
            f"git show {ref}:{ASSET_RUNNER_REL} failed ({(shown.stderr or '').strip()[:200]})")
    if not (shown.stdout or "").strip():
        raise RunnerSqlExtractionError(f"{ASSET_RUNNER_REL} at {ref} is empty")
    return shown.stdout


def registry_row_digest(row: Mapping[str, Any]) -> str:
    """Digest of every registry field this dispatch depends on (manifest fields plus buildability). Unordered
    depends_on, matching the runner's own unordered comparison. A change between the build and the insert moves it."""
    return hashlib.sha256(canonical_json({
        "asset_id": row["asset_id"], "layer": row.get("layer"), "scope": row["scope"],
        "asset_kind": row.get("asset_kind"), "depends_on": sorted(row.get("depends_on") or []),
        "natural_key_partition": row.get("natural_key_partition"), "has_cowriters": bool(row.get("has_cowriters")),
        "is_active": bool(row.get("is_active")), "has_writer": bool(row.get("has_writer")),
    }).encode("utf-8")).hexdigest()


def load_local_writer_digests(repo: str | Path = REPO_ROOT) -> dict[str, str]:
    path = Path(repo) / WRITER_DIGESTS_REL
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LevelWaveError(f"writer digest inventory unreadable at {path}: {exc}") from exc
    writers = inventory.get("writers")
    if not isinstance(writers, dict):
        raise LevelWaveError("writer digest inventory has no `writers` object")
    return writers


def load_deployed_writer_digests(*, repo: str | Path, sha: str | None = None, file: str | Path | None = None,
                                 git=_git) -> dict[str, str]:
    """The DEPLOYED job image's writer digests, from exactly one source: the committed inventory at the job's sha
    (`git show <sha>:...`, the sha read by the operator from the running job) or a file holding that inventory.
    No source, an unreadable one, or one without a `writers` object refuses: image skew can not be ruled out."""
    if (sha is None) == (file is None):
        raise LevelWaveRefusal([{"code": "DEPLOYED_DIGESTS_UNAVAILABLE",
                                 "detail": "exactly one of --deployed-sha / --deployed-digests-file is required"}])
    try:
        if sha is not None:
            shown = git(str(repo), ["show", f"{sha}:{WRITER_DIGESTS_REL}"])
            if shown.returncode != 0:
                raise ValueError((shown.stderr or "git show failed").strip()[:200])
            text = shown.stdout
        else:
            text = Path(file).read_text(encoding="utf-8")
        writers = json.loads(text).get("writers")
        if not isinstance(writers, dict):
            raise ValueError("no `writers` object")
    except (OSError, ValueError, AttributeError) as exc:
        raise LevelWaveRefusal([{"code": "DEPLOYED_DIGESTS_UNAVAILABLE",
                                 "detail": f"deployed image digests unreadable: {exc}"}]) from exc
    return writers


def resolve_commit(repo: str, ref: str, *, git=_git, code: str = "JOB_SHA_UNRESOLVABLE") -> str:
    """The full 40-hex commit `ref` names in `repo`, or a refusal."""
    cp = git(str(repo), ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    full = (cp.stdout or "").strip()
    if cp.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", full):
        raise LevelWaveRefusal([{"code": code, "detail": f"{ref!r} does not resolve to a commit in {repo}"}])
    return full


def read_job_sha_file(path: str | Path) -> str:
    """The live deployed JOB image sha an operator tool (Exec's LC-1 gate) keeps in a file. The file must hold exactly one
    40-hex commit sha (a trailing newline is fine): anything else, empty included, refuses (fail closed)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise LevelWaveRefusal([{"code": "JOB_SHA_FILE_UNREADABLE", "detail": f"{path}: {exc}"}]) from exc
    sha = text.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or len(text.strip().splitlines()) != 1:
        raise LevelWaveRefusal([{"code": "JOB_SHA_FILE_UNREADABLE",
                                 "detail": f"{path} must hold exactly one 40-hex commit sha, got {text.strip()[:60]!r}"}])
    return sha


def check_job_sha_binding(repo: str, *, inventory_sha: str, job_sha: str, git=_git) -> dict:
    """The operator-supplied LIVE deployed job image sha must be the same commit as the one whose committed inventory
    supplied the deployed digests. (Trap 103: use the image / DEPLOY_SHA, never a deploy run's head_sha, which can
    disagree with it.) Returns {"inventory_sha", "deployed_job_sha"} resolved to 40-hex, or refuses."""
    inv = resolve_commit(repo, inventory_sha, git=git, code="JOB_SHA_UNRESOLVABLE")
    job = resolve_commit(repo, job_sha, git=git, code="JOB_SHA_UNRESOLVABLE")
    if inv != job:
        raise LevelWaveRefusal([{"code": "JOB_SHA_MISMATCH", "inventory_sha": inv, "deployed_job_sha": job,
                                 "detail": f"the inventory used for the digests is {inv}, the deployed job image is {job}: "
                                           "the digests are not the deployed image's"}])
    return {"inventory_sha": inv, "deployed_job_sha": job}


def recheck_job_sha(repo: str, *, pinned_job_sha: str, job_sha_file: str | Path, git=_git) -> None:
    """Re-read the job-sha file and refuse unless it still names the pinned commit (a redeploy mid-campaign)."""
    now = resolve_commit(repo, read_job_sha_file(job_sha_file), git=git)
    if now != pinned_job_sha:
        raise LevelWaveRefusal([{"code": "JOB_SHA_CHANGED", "pinned": pinned_job_sha, "now": now,
                                 "detail": f"the deployed job image changed from {pinned_job_sha} to {now} during the campaign"}])


def family_ref_status(repo: str, ref: str, *, git=_git) -> dict:
    """The sha of the family ref read, and whether it is the remote's tip (`git ls-remote`, read-only, time-limited). Every
    output line is parsed: the one for refs/heads/<branch> must be present and a 40-hex sha. For a ref that is not
    `<remote>/<branch>`, or when the remote can not be asked or answers unexpectedly, freshness is not_a_remote_ref /
    unverified."""
    sha = resolve_commit(repo, ref, git=git, code="FAMILY_FILE_UNREADABLE")
    m = re.fullmatch(r"([A-Za-z0-9_.-]+)/(.+)", ref)
    if not m:
        return {"ref": ref, "sha": sha, "freshness": "not_a_remote_ref"}
    want = f"refs/heads/{m.group(2)}"
    cp = git(str(repo), ["ls-remote", m.group(1), want])
    if cp.returncode != 0:
        return {"ref": ref, "sha": sha, "freshness": "unverified",
                "detail": f"git ls-remote {m.group(1)} failed ({(cp.stderr or '').strip()[:160]})"}
    tips = set()
    for line in (cp.stdout or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == want and re.fullmatch(r"[0-9a-f]{40}", parts[0]):
            tips.add(parts[0])
    if len(tips) != 1:
        return {"ref": ref, "sha": sha, "freshness": "unverified",
                "detail": f"git ls-remote {m.group(1)} returned {len(tips)} distinct tips for {want}"}
    remote = next(iter(tips))
    return {"ref": ref, "sha": sha, "remote_sha": remote, "freshness": "fresh" if remote == sha else "stale"}


def family_ref_refusals(status: Mapping[str, Any], *, committing: bool) -> list[dict]:
    if status["freshness"] == "stale":
        return [{"code": "FAMILY_REF_STALE", "detail": f"{status['ref']} is {status['sha']} but the remote tip is "
                 f"{status['remote_sha']}: `git fetch` first, so the family file read is current"}]
    if committing and status["freshness"] != "fresh":
        return [{"code": "FAMILY_REF_UNVERIFIED", "detail": f"a real dispatch needs the family ref verified fresh against the "
                 f"remote; {status['ref']} is {status['freshness']}"}]
    return []


def check_image_skew(assets: Sequence[str], local: Mapping[str, str], deployed: Mapping[str, str]) -> None:
    """Refuse unless every asset has a valid local digest equal to the deployed image's (R2, checked before the
    runner can refuse the whole run). A missing digest on either side refuses; it is never skipped."""
    bad = []
    for a in assets:
        mine, theirs = local.get(a), deployed.get(a)
        if not isinstance(mine, str) or not _HEX64.fullmatch(mine):
            bad.append({"code": "CODE_DIGEST_UNAVAILABLE", "asset": a,
                        "detail": f"no valid writer digest for {a} in the checkout's inventory"})
        elif theirs is None:
            bad.append({"code": "IMAGE_SKEW", "asset": a, "detail": f"{a} has no digest in the deployed image's inventory"})
        elif mine != theirs:
            bad.append({"code": "IMAGE_SKEW", "asset": a, "checkout": mine, "deployed": theirs,
                        "detail": f"{a}: checkout digest differs from the deployed image's"})
    if bad:
        raise LevelWaveRefusal(bad)


def accept_candidates(assets: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> dict[str, dict]:
    """Registry rows keyed by asset id; refuses (all at once) any requested asset that is missing, inactive, has no
    writer, is a service, or appears twice."""
    by_id: dict[str, dict] = {}
    bad = []
    for r in rows:
        if r["asset_id"] in by_id:
            bad.append({"code": "REGISTRY_ROW_INVALID", "asset": r["asset_id"], "detail": "duplicate registry rows"})
        by_id[r["asset_id"]] = dict(r)
    for a in assets:
        r = by_id.get(a)
        if r is None:
            bad.append({"code": "REGISTRY_ROW_INVALID", "asset": a, "detail": f"no registry row for {a}"})
        elif not (r.get("is_active") is True and r.get("has_writer") is True):
            bad.append({"code": "REGISTRY_ROW_INVALID", "asset": a, "detail": f"{a} is not an active writer asset"})
        elif r.get("asset_kind") == "service":
            bad.append({"code": "REGISTRY_ROW_INVALID", "asset": a, "detail": f"{a} is a service asset (nothing to build)"})
        elif r.get("scope") != "per_chart":
            bad.append({"code": "NON_PER_CHART_SCOPE", "asset": a,
                        "detail": f"{a} has scope {r.get('scope')!r}: a chart-scoped level wave builds per_chart assets only "
                                  "(global assets rebuild for every chart; they are not this tool's)"})
    if bad:
        raise LevelWaveRefusal(bad)
    return by_id


def build_level_manifest(*, chart_id: str, plan_waves: Sequence[Sequence[str]], rows: Mapping[str, Mapping[str, Any]],
                         writer_digests: Mapping[str, str]) -> tuple[dict[str, Any], str]:
    """The `nirmana-run-manifest/v1` for `plan_waves`, byte-identical in shape to dispatch_frozen_rebuild.build_manifest
    (a one-asset, one-wave input yields the same manifest and digest)."""
    plan = [a for wave in plan_waves for a in wave]
    if not plan or any(not wave for wave in plan_waves) or len(set(plan)) != len(plan):
        raise LevelWaveError("waves must be non-empty, non-empty each, and free of duplicates")
    assets = []
    for a in plan:
        row = rows[a]
        digest = writer_digests.get(a)
        if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
            raise LevelWaveError(f"writer digest missing or invalid for {a}")
        assets.append({
            "asset_id": a, "scope": row["scope"], "depends_on": list(row.get("depends_on") or []),
            "natural_key_partition": row.get("natural_key_partition"),
            "has_cowriters": bool(row.get("has_cowriters")), "expected_code_digest": digest,
        })
    manifest: dict[str, Any] = {
        "version": MANIFEST_VERSION, "chart_id": chart_id, "scope": "asset_set", "scope_target": ",".join(plan),
        "action": "rebuild", "waves": [list(w) for w in plan_waves], "assets": assets,
    }
    return manifest, manifest_digest(manifest)


FORCE_ENV_VAR = "NIRMANA_FORCE_EXECUTE"


def expected_confirmation(digest: str, n_assets: int, force_execute: bool = False) -> str:
    """`--confirm` token: the existing `<SUBJECT>_FROZEN_REBUILD` convention with the subject bound to the manifest, so a
    token from one dry run can not confirm a different manifest (a registry change moves the digest and the token). A
    forced dispatch has a DIFFERENT token (`..._FORCE_FROZEN_REBUILD`): a token confirmed for a normal run can not authorise
    a force, and the reverse."""
    return f"{n_assets}ASSETS_{digest[:12].upper()}_{'FORCE_' if force_execute else ''}FROZEN_REBUILD"


def force_refusals(assets: Sequence[str], family: Mapping[str, Any]) -> list[dict]:
    """`--force-execute` bypasses the runner's delta-skip for EVERY asset of the run, so it is allowed for exactly one asset,
    and never for a family asset (name pattern or FAMILY_ASSETS.json family_set), even when it is the only asset."""
    out: list[dict] = []
    if len(assets) != 1:
        out.append({"code": "FORCE_MULTI_ASSET", "detail": f"--force-execute is for a single-asset plan; {len(assets)} assets "
                    "requested (force would bypass the delta-skip for every asset of the run)"})
    members = family.get("family_set") if family.get("state") == "present" else frozenset()
    for a in sorted(assets):
        if FAMILY_NAME_PATTERN.match(a) or a in (members or frozenset()):
            out.append({"code": "FORCE_FAMILY_ASSET", "asset": a,
                        "detail": f"--force-execute is refused for family asset {a}"})
    return out


RUNNER_REL = "platform/python-sidecar/pipeline/orchestrator/runner.py"
ASSET_RUNNER_REL = "platform/python-sidecar/pipeline/orchestrator/asset_runner.py"
# What a deployed image must contain for NIRMANA_FORCE_EXECUTE to do anything (O-wave WP-2): the runner reads the variable,
# and the asset runner's delta-skip gate is conditioned on `not force`.
_FORCE_MARKERS = ((RUNNER_REL, re.compile(r"NIRMANA_FORCE_EXECUTE"), "reads NIRMANA_FORCE_EXECUTE"),
                  (ASSET_RUNNER_REL, re.compile(r"has_cowriters is not None and not force"),
                   "gates the delta-skip on `not force`"))


def check_image_supports_force(repo: str, job_sha: str, *, git=_git) -> None:
    """`--force-execute` is only meaningful if the DEPLOYED job image honours it. An image built before the O-wave WP-2 commit
    accepts the gcloud override and silently delta-skips. Read the runner sources at the pinned job sha and refuse
    (FORCE_NOT_SUPPORTED_BY_IMAGE) unless both markers are present; an unreadable file refuses too."""
    problems = []
    for rel, pat, what in _FORCE_MARKERS:
        cp = git(str(repo), ["show", f"{job_sha}:{rel}"])
        if cp.returncode != 0:
            problems.append(f"{rel} at {job_sha} is unreadable ({(cp.stderr or '').strip()[:120]})")
        elif not pat.search(cp.stdout or ""):
            problems.append(f"{rel} at {job_sha} does not contain code that {what}")
    if problems:
        raise LevelWaveRefusal([{"code": "FORCE_NOT_SUPPORTED_BY_IMAGE", "job_sha": job_sha, "problems": problems,
                                 "detail": "the deployed job image does not honour NIRMANA_FORCE_EXECUTE (it would accept the "
                                           "override and delta-skip): " + "; ".join(problems)}])


# ---------------------------------------------------------------------------------------------
# Plan (read phase) and dispatch (insert phase)
# ---------------------------------------------------------------------------------------------

def check_external_dependencies(cur, chart_id: str, ext: Mapping[str, Sequence[str]]) -> None:
    """Every declared dependency OUTSIDE the set must be lit (throughput) and fresh (latest receipt), the same test
    asset_runner.deps_unsatisfied applies (service deps need only be service_ok). Refuses with every offender."""
    wanted = sorted({d for deps in ext.values() for d in deps})
    if not wanted:
        return
    cur.execute(DEPS_SQL, (wanted, chart_id, chart_id, chart_id, chart_id))
    seen = {}
    for d in cur.fetchall():
        seen[d["asset_id"]] = d
    bad = []
    for dep in wanted:
        d = seen.get(dep)
        state = d["state"] if d else None
        freshness = d["freshness_state"] if d else None
        if state not in ("lit", "service_ok"):
            why = f"{dep}({state or 'absent'})"
        elif d and d.get("asset_kind") == "service":
            continue
        elif freshness != "fresh":
            why = f"{dep}(receipt:{freshness or 'absent'})"
        else:
            continue
        needed_by = sorted(a for a, deps in ext.items() if dep in deps)
        bad.append({"code": "DEPENDENCY_NOT_READY", "dependency": dep, "needed_by": needed_by,
                    "detail": f"declared dependency {why} is not lit+fresh; needed by {', '.join(needed_by)}"})
    if bad:
        raise LevelWaveRefusal(bad)


def check_registry_unchanged(built: Mapping[str, str], rows_now: Sequence[Mapping[str, Any]]) -> None:
    """Refuse when any asset's registry-row digest now differs from the one the manifest was built from."""
    now = {r["asset_id"]: registry_row_digest(r) for r in rows_now}
    bad = []
    for a, digest in sorted(built.items()):
        if a not in now:
            bad.append({"code": "REGISTRY_ROW_CHANGED", "asset": a, "detail": f"{a} no longer has a registry row"})
        elif now[a] != digest:
            bad.append({"code": "REGISTRY_ROW_CHANGED", "asset": a,
                        "detail": f"asset_registry row for {a} changed since the manifest was built"})
    if bad:
        raise LevelWaveRefusal(bad)


def make_plan(*, chart_id: str, assets: Sequence[str], rows: Sequence[Mapping[str, Any]],
              writer_digests: Mapping[str, str], deployed_digests: Mapping[str, str],
              outside_deps: Mapping[str, Sequence[str]] | None = None) -> dict:
    """Pure: from registry rows to the waves, per-wave manifests and the single-run manifest. Raises on image skew.
    `outside_deps` = {out-of-set asset: its depends_on} (read_dependency_closure) so ordering sees through them."""
    by_id = accept_candidates(assets, rows)
    check_image_skew(assets, writer_digests, deployed_digests)
    deps = {a: by_id[a].get("depends_on") or [] for a in assets}
    waves = derive_waves(assets, {**dict(outside_deps or {}), **deps})
    manifest, digest = build_level_manifest(chart_id=chart_id, plan_waves=waves, rows=by_id, writer_digests=writer_digests)
    per_wave = []
    for i, wave in enumerate(waves):
        wm, wd = build_level_manifest(chart_id=chart_id, plan_waves=[wave], rows=by_id, writer_digests=writer_digests)
        per_wave.append({"wave": i, "assets": list(wave), "manifest": wm, "manifest_digest": wd})
    return {
        "chart_id": chart_id, "waves": waves, "plan": [a for w in waves for a in w],
        "manifest": manifest, "manifest_digest": digest, "per_wave": per_wave,
        "row_digests": {a: registry_row_digest(by_id[a]) for a in assets},
        "external_dependencies": external_dependencies(assets, deps),
        "rows": by_id,
    }


def estimate_runtime(waves: Sequence[Sequence[str]], rows: Mapping[str, Mapping[str, Any]]) -> dict:
    """Runtime bounds from the registry; None where nothing was ever measured (never an invented number).

    parallel_upper_bound_seconds: sum over waves of the largest writer_timeout_seconds in the wave (assets in a wave run
    in parallel, up to the runner's concurrency cap); serial_upper_bound_seconds: the sum of all timeouts.
    measured_seconds: sum over waves of the largest estimated_seconds, only when every asset has one."""
    def col(a, k):
        v = rows[a].get(k)
        return v if isinstance(v, (int, float)) and v > 0 else None
    par, ser, est, measured = 0, 0, 0, True
    unknown_timeout = []
    for wave in waves:
        t = [col(a, "writer_timeout_seconds") for a in wave]
        unknown_timeout += [a for a, x in zip(wave, t) if x is None]
        par += max((x for x in t if x is not None), default=0)
        ser += sum(x for x in t if x is not None)
        e = [col(a, "estimated_seconds") for a in wave]
        if any(x is None for x in e):
            measured = False
        else:
            est += max(e)
    return {"parallel_upper_bound_seconds": par, "serial_upper_bound_seconds": ser,
            "measured_seconds": est if measured else None, "assets_without_timeout": sorted(unknown_timeout),
            "note": "upper bounds are writer timeouts, not predictions; measured_seconds is None unless every asset "
                    "has a registry estimated_seconds"}


def _lock_key(chart_id: str) -> str:
    return f"suvarna-level-wave:{chart_id}"


def insert_run(connect, *, chart_id: str, manifest: Mapping[str, Any], digest: str, row_digests: Mapping[str, str],
               external: Mapping[str, Sequence[str]], confirm: str | None, commit: bool,
               footprint: bool = False, on_commit=None, meta: Mapping[str, Any] | None = None,
               force_execute: bool = False) -> dict:
    """One transaction: advisory lock, active-run refusal, registry-row re-read and compare, external dependencies
    lit+fresh, INSERT build_runs + build_run_assets, then ROLLBACK (dry run) or COMMIT (only with the exact token).

    The re-read happens in THIS transaction, after the manifest was built from an earlier, separate read, so a registry
    change in between is visible (a repeated read inside one SERIALIZABLE snapshot could not show it).
    `on_commit(receipt)` is called the instant the COMMIT succeeds, before anything else can fail, so the caller always
    knows a run exists. `meta` is merged into the receipt (the deployed job sha is printed on every receipt)."""
    plan = [a for wave in manifest["waves"] for a in wave]
    token = expected_confirmation(digest, len(plan), force_execute)
    if commit and confirm != token:
        raise LevelWaveRefusal([{"code": "CONFIRM_TOKEN_MISMATCH",
                                 "detail": f"--commit requires --confirm {token}", "expected": token}])
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (_lock_key(chart_id),))
        cur.execute("""SELECT id, chart_id, state FROM build_runs
                        WHERE chart_id=%s AND state IN ('planned','running','paused')""", (chart_id,))
        active = cur.fetchall()
        if active:
            raise LevelWaveRefusal([{"code": "ACTIVE_RUN", "detail": f"active build run(s) exist for this chart: {active}"}])
        cur.execute(CANDIDATES_SQL, (plan,))
        rows_now = [dict(r) for r in cur.fetchall()]
        check_registry_unchanged(row_digests, rows_now)
        check_external_dependencies(cur, chart_id, external)
        footprint_report = _footprint_report(conn, rows_now) if footprint else None
        run_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO build_runs
              (id, chart_id, scope, scope_target, action, state, plan,
               plan_manifest, plan_manifest_digest, triggered_by)
            VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                    %s::jsonb, %s, %s)
            """,
            (run_id, chart_id, manifest["scope_target"], json.dumps(plan), json.dumps(manifest), digest, TRIGGERED_BY),
        )
        for position, asset_id in enumerate(plan):
            cur.execute(
                """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                   VALUES (%s, %s, %s, 'queued')""",
                (run_id, asset_id, position),
            )
        receipt = {"run_id": run_id, "chart_id": chart_id, "assets": plan, "waves": manifest["waves"],
                   "manifest_digest": digest, "committed": bool(commit), "confirm_token": token}
        receipt.update(dict(meta or {}))
        if footprint_report is not None:
            receipt["footprint"] = footprint_report
        if commit:
            try:
                conn.commit()
            except Exception as exc:  # noqa: BLE001 -- the outcome of a failed COMMIT is unknown, never "not committed"
                raise CommitOutcomeUnknown(run_id, chart_id, exc) from exc
            if on_commit is not None:
                on_commit(receipt)
        else:
            conn.rollback()
        return receipt
    except CommitOutcomeUnknown:
        raise
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------------------------
# Footprint scope: which writes the registry target_table does NOT show (static, read-only, indicative)
# ---------------------------------------------------------------------------------------------
# asset_registry carries ONE target_table per asset, but a writer may write several tables, and a writer may declare none.
# The write set _footprint_report feeds transitive_footprint is therefore only what the registry shows. This scan reads the
# writer SOURCE TEXT (ast.parse only: nothing is imported or executed, no database) and finds INSERT INTO / DELETE FROM /
# UPDATE .. SET / TRUNCATE / COPY .. FROM targets in its string literals (docstrings excluded). Forms it resolves: a
# literal name, a module/class string constant ({TABLE}), a table passed as a literal argument to a parametric helper
# (ga_writers/_idempotency.clear_table_for_chart), and the tables a known idempotency helper (replace_prior_*) writes. A
# thin adapter that lists `source_paths = [...]` (never mutated) is followed one level into those files. Every table of a
# TRUNCATE a, b list and every write of a multi-statement / CTE literal is captured; a read (USING, FROM, SELECT) is not a
# write. Anything else -- a table named by a runtime value or a dotted/attribute name, SQL handed to execute() that this file
# does not show (an imported constant, a call result, a subscript, bytes, __doc__), a literal that ends in a write verb with
# no target, copy_from & co, exec/eval, runtime rebinding, `import *`, a literal over 64 KB, a writer that shows no write
# statement at all (it delegates, or it is read-only: the two are not distinguishable here), an unreadable or unparseable
# file, a missing writer file -- goes to assets_not_scanned with a named reason. The scan is
# INDICATIVE: it can both over-report (a table named in a string that is not run) and under-report (SQL loaded from a file,
# a delegate in another module), which is why any non-empty list makes the footprint scope "partial", never "complete".

WRITERS_REL = "platform/python-sidecar/pipeline/orchestrator/writers"
WRITE_SCAN_HELPER_MODULES = ("platform/python-sidecar/ga_writers/_idempotency.py",
                             "platform/python-sidecar/bodha_writers/_idempotency.py")
FOOTPRINT_SCAN_LABEL = "indicative_static_scan"
_ASSET_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")

_PH_OPEN, _PH_CLOSE = "\x01", "\x02"
# a quoted identifier is one whole "..." token (a quoted name with spaces/odd characters is then refused by _add_target
# instead of being half-read); a placeholder is \x01expr\x02. Literal text never carries \x01/\x02 (see _clean_literal).
_NAME_PART = r'(?:"[^"\x01\x02]+"|[A-Za-z_][\w$]*|\x01[^\x02]*\x02)'
# the lookahead refuses a name that continues ("public.{T}_x", "{A}{B}"): a partly-resolvable name is not guessed
_TBL = rf"{_NAME_PART}(?:\s*\.\s*{_NAME_PART})?(?![\w$\"&\x01]|\s*\.)"
# INSERT / DELETE / UPDATE / COPY name ONE written table (a read after it -- DELETE .. USING b, UPDATE .. FROM b,
# INSERT .. SELECT FROM b -- is not a write, and finditer keeps every statement / CTE write in one literal). TRUNCATE takes a
# comma list and is parsed separately (_WriteScan._scan_truncate).
_WRITE_VERBS = (
    ("INSERT", re.compile(rf"\bINSERT\s+INTO\s+(?:ONLY\s+)?(?P<t>{_TBL})", re.IGNORECASE)),
    ("DELETE", re.compile(rf"\bDELETE\s+FROM\s+(?:ONLY\s+)?(?P<t>{_TBL})", re.IGNORECASE)),
    ("UPDATE", re.compile(rf"\bUPDATE\s+(?:ONLY\s+)?(?P<t>{_TBL})(?:\s*\*)?\s+(?:(?:AS\s+)?[A-Za-z_]\w*\s+)?SET\b", re.IGNORECASE)),
    ("COPY", re.compile(rf"\bCOPY\s+(?P<t>{_TBL})\s*(?:\((?:[^()\x01]|\x01[^\x02]*\x02){{0,4000}}\)\s*)?FROM\b", re.IGNORECASE)),
)
_TRUNCATE_HEAD = re.compile(r"\bTRUNCATE(?:\s+TABLE\b)?(?=\s)\s*", re.IGNORECASE)
_TRUNCATE_ITEM = re.compile(rf"(?:ONLY\s+)?(?P<t>{_TBL})\s*(?:\*\s*)?", re.IGNORECASE)
# A verb whose target is not a recognisable name ("INSERT INTO %s", "DELETE FROM {}") cannot be resolved: not scanned.
_VERB_ANY = re.compile(r"\b(?:INSERT\s+INTO|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)\s+(?P<rest>\S+)", re.IGNORECASE)
_SQL_WORDS = {"select", "set", "values", "only", "table", "from", "where", "default", "using"}
# a literal that ENDS in a write verb has no target token: the target is joined on at runtime (" ".join([verb, tbl]), verb + tbl)
_TRAILING_STRONG_VERB = re.compile(r"\b(?:INSERT\s+INTO|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)\s*\Z", re.IGNORECASE)
_TRAILING_WEAK_VERB = re.compile(r"\b(?:UPDATE|COPY)\s+\Z", re.IGNORECASE)   # needs a trailing space: a bare "UPDATE" is a label
_UPDATE_WORD = re.compile(r"\bUPDATE\b", re.IGNORECASE)
_COPY_WORD = re.compile(r"\bCOPY\b", re.IGNORECASE)
_SET_WORD = re.compile(r"\bSET\b", re.IGNORECASE)
_TO_WORD = re.compile(r"\bTO\b", re.IGNORECASE)
_NAME_AFTER_VERB = re.compile(r'\s+(?:ONLY\s+)?(?P<n>[A-Za-z_"\x01])', re.IGNORECASE)
# `UPDATE a`, `UPDATE ONLY a t`, `COPY a (x, y)` that END the text: the SET / FROM tail is joined on at runtime
_UNFINISHED_TAIL = re.compile(
    rf"\s+(?:ONLY\s+)?{_NAME_PART}(?:\s*\.\s*{_NAME_PART})?(?:\s*\*)?(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?"
    rf"(?:\s*\((?:[^()\x01]|\x01[^\x02]*\x02){{0,4000}}\))?(?:\s*\x01[^\x02]*\x02)*\s*\Z", re.IGNORECASE)
# a savepoint statement: the whole statement is the verb and an identifier (a placeholder may sit inside the identifier)
_TXN_CONTROL = re.compile(r"\s*(?:SAVEPOINT|RELEASE(?:\s+SAVEPOINT)?|ROLLBACK\s+TO(?:\s+SAVEPOINT)?)\s+"
                          r"(?:[A-Za-z0-9_]|\x01[^\x02]*\x02)+\s*\Z", re.IGNORECASE)
_COMMENT_NEAR = re.compile(r"/\*|--")
_PLAIN_QUOTED = re.compile(r'"[a-z_][a-z0-9_]*"')
# a statement whose VERB is a runtime value / a name: `{V} FROM a`, `{V} {T} SET x`, `{V} INTO a`, `{V} TABLE a`
_STMT_START_PH = re.compile(r"(?:\A|;)\s*(?P<ph>\x01[^\x02]*\x02|\{[^}]*\}|%s)(?P<rest>[^;]*)")
_SQL_WORD_IN_REST = re.compile(r"\b(?:FROM|INTO|TABLE|SET|VALUES|SELECT)\b")
_PLACEHOLDER_BODY = re.compile(r"\x01[^\x02]*\x02")
_PLACEHOLDER_CAPTURE = re.compile(r"\x01([^\x02]*)\x02")
_SECOND_PLACEHOLDER = re.compile(r"\s+\x01(?P<expr>[^\x02]*)\x02")
_SQL_WORD_ONLY = re.compile(r"\s*(?:ONLY\s+)?(?:FROM|INTO|TABLE|SET|VALUES|SELECT)\s*\Z", re.IGNORECASE)
_BARE_VERB = re.compile(r"\s*(?:INSERT(?:\s+INTO)?|DELETE(?:\s+FROM)?|UPDATE|TRUNCATE(?:\s+TABLE)?|COPY|MERGE(?:\s+INTO)?|CREATE|"
                        r"DROP|ALTER|SELECT|WITH|REFRESH)\s*\Z", re.IGNORECASE)
_FROM_WORD = re.compile(r"\bFROM\b", re.IGNORECASE)
_NOT_A_STATEMENT_UPDATE_PREV = {"for", "do", "on", "key", "of", "before", "after", "or", "instead"}
_SELECT_INTO_WORDS = re.compile(r"\(|\)|;|\b(?:SELECT|INTO|INSERT|FROM|UPDATE|DELETE)\b", re.IGNORECASE)
# a literal this long is not scanned at all (it bounds regex work, and no real statement is this long): not scanned
MAX_SQL_LITERAL_CHARS = 64 * 1024


def _select_into(text: str) -> bool:
    """`SELECT ... INTO <name>` (a table-creating form): an INTO at the same parenthesis depth as a SELECT, with no
    FROM/INSERT/UPDATE/DELETE at that depth in between -- a FROM inside `EXTRACT(year FROM d)` is one level deeper and does not
    disarm it. One linear pass over parentheses and keywords (the earlier regex rescanned to the end from every SELECT)."""
    armed: list[bool] = [False]
    for m in _SELECT_INTO_WORDS.finditer(text):
        w = m.group().upper()
        if w == "(":
            armed.append(False)
        elif w == ")":
            if len(armed) > 1:
                armed.pop()
        elif w == ";":
            armed = [False]
        elif w == "SELECT":
            armed[-1] = True
        elif w == "INTO":
            if armed[-1]:
                return True
        else:
            armed[-1] = False
    return False


_SQL_LEXEME = re.compile(r"\x01[^\x02]*\x02|'|\"|\$(?:(?!\d)\w+)?\$|/\*|--")
_NAKED_LEXEME = re.compile(r"/\*|--")
_BLOCK_EDGE = re.compile(r"/\*|\*/")
_LINE_END = re.compile(r"[\r\n]")


def _skip_quoted(text: str, start: int, quote: str, backslash: bool) -> int:
    """Index just past the quoted run that opens at `start` (`\\x` is an escape in an E'' string);
    an unterminated run reaches the end of the text."""
    i, n = start + 1, len(text)
    while i < n:
        c = text[i]
        if backslash and c == "\\":
            i += 2
            continue
        if c == quote:
            return i + 1                                          # a doubled quote ('') is one close + one open: same pairing
        i += 1
    return n


def _is_ident_part(ch: str) -> bool:
    """A character that can continue an SQL identifier: letters, digits, `_`, `$`, and any non-ASCII character."""
    return ch.isalnum() or ch in "_$" or ord(ch) > 127


def _strip_sql_comments(text: str, quote_aware: bool = True) -> str:
    """The text with `/* ... */` (nested) and `-- ...` comments replaced by one space each: the server reads a comment as
    whitespace, so `INSERT /* c */ INTO a` is `INSERT INTO a`. With `quote_aware` a comment marker inside a '...' / E'...' /
    "..." / $tag$...$tag$ run is text, not a comment (`SELECT '--'; DELETE FROM t` keeps its DELETE) and a \\x01..\\x02
    placeholder is opaque; a `$` that continues an identifier (`a$b$`) does not open a dollar quote. An unterminated quote keeps
    the rest of the text as is; an unterminated block comment drops the rest. Without it (`quote_aware=False`) every comment
    marker is a comment wherever it sits -- the over-stripping reading, used as one more variant so that a statement whose keywords
    are split by a comment INSIDE a string / dollar body (`DO $$ BEGIN DELETE /*x*/ FROM t; END $$`) is still seen. One linear
    pass either way."""
    out: list[str] = []
    pos, n = 0, len(text)
    lexeme = _SQL_LEXEME if quote_aware else _NAKED_LEXEME
    while pos < n:
        m = lexeme.search(text, pos)
        if m is None:
            break
        tok, start = m.group(), m.start()
        out.append(text[pos:start])
        if tok[0] == "\x01":
            out.append(tok)
            pos = m.end()
        elif tok == "'" or tok == '"':
            escape = tok == "'" and start > 0 and text[start - 1] in "Ee" and (start < 2 or not _is_ident_part(text[start - 2]))
            end = _skip_quoted(text, start, tok, escape)
            out.append(text[start:end])
            pos = end
        elif tok[0] == "$":
            if start > 0 and _is_ident_part(text[start - 1]):
                out.append("$")                                    # `a$b$`: part of an identifier, not a dollar quote
                pos = start + 1
                continue
            close = text.find(tok, m.end())
            end = n if close < 0 else close + len(tok)
            out.append(text[start:end])
            pos = end
        elif tok == "--":
            out.append(" ")
            e = _LINE_END.search(text, m.end())
            pos = n if e is None else e.start()
        else:                                                      # "/*": a (nested) block comment
            out.append(" ")
            depth, pos = 1, m.end()
            while depth and pos < n:
                e = _BLOCK_EDGE.search(text, pos)
                if e is None:
                    pos = n
                    break
                depth += 1 if e.group() == "/*" else -1
                pos = e.end()
    out.append(text[pos:])
    return "".join(out)


# Write forms this scan does NOT analyse. Seeing one in a (non-docstring) string literal means the writer touches tables the
# scan cannot name, so the writer goes to assets_not_scanned instead of reading as a clean single-table writer.
_TRIPWIRES = (
    ("MERGE INTO", re.compile(r"\bMERGE\s+INTO\b", re.IGNORECASE).search),
    ("REFRESH MATERIALIZED VIEW", re.compile(r"\bREFRESH\s+MATERIALIZED\s+VIEW\b", re.IGNORECASE).search),
    ("CREATE TABLE", re.compile(r"\bCREATE\s+(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMP|TEMPORARY)\s+|UNLOGGED\s+)?TABLE\b", re.IGNORECASE).search),
    ("SELECT ... INTO", _select_into),
    ("ALTER TABLE", re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE).search),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE).search),
    ("DROP SCHEMA", re.compile(r"\bDROP\s+SCHEMA\b", re.IGNORECASE).search),
)
_SQL_COMPOSITION_ATTRS = {"SQL", "Identifier", "Composed", "Literal", "Placeholder"}
# calls whose argument 0 (or sql= / query= / ...) is SQL text; execute_values / execute_batch take it as argument 1
_EXECUTE_ATTRS = {"execute", "executemany", "executescript", "copy", "copy_expert", "fetch", "fetchrow", "fetchval",
                  "fetchmany", "prepare", "exec_driver_sql", "run"}
_SQL_SECOND_ARG_FUNCS = {"execute_values", "execute_batch"}                          # psycopg2.extras.f(cur, SQL, ...)
_SQL_KEYWORDS = {"query", "sql", "statement", "operation", "stmt", "command", "text", "sql_text", "sql_query"}
_COPY_API_ATTRS = {"copy_from", "copy_to", "copy_records_to_table", "copy_to_table"}  # write / move a table with no SQL text
_DB_EXEC_NAMES = (_EXECUTE_ATTRS - {"copy", "run"}) | _COPY_API_ATTRS | {"copy_from_table", "copy_from_query"}
_CONTAINER_MUTATORS = {"append", "extend", "insert", "update", "add", "setdefault", "appendleft", "extendleft",
                       "__setitem__", "__iadd__", "__ior__"}                      # their arguments become elements
_CONTAINER_BULK_MUTATORS = {"extend", "update", "extendleft", "__iadd__", "__ior__"}   # the argument is a container of elements
_HARMLESS_MUTATORS = {"pop", "popitem", "remove", "clear", "sort", "reverse", "discard", "popleft", "__delitem__"}  # add nothing
_CONTAINER_CALLS = {"list", "dict", "set", "frozenset", "sorted", "reversed", "zip", "enumerate", "map", "filter",
                    "defaultdict", "OrderedDict", "deque", "Counter", "bytearray"}
_CONTAINER_READ_METHODS = {"get", "copy", "keys", "values", "items"}      # read a container: clean iff the container (and the key) is
_PURE_CONSUMERS = {"len", "sorted", "list", "tuple", "set", "frozenset", "enumerate", "zip", "reversed", "iter", "any", "all",
                   "min", "max", "str", "repr", "dict", "bool", "next"}
_ITER_WRAPPERS = {"enumerate", "sorted", "reversed", "list", "tuple", "set", "frozenset", "iter", "zip"}
# builtins whose result is a number / bool (no SQL text can pass through) and builtins whose result carries their arguments' text
_NUMERIC_FUNCS = {"len", "int", "float", "bool", "abs", "round", "ord", "hash", "id", "any", "all", "isinstance",
                  "issubclass", "callable", "range", "chr", "divmod", "pow", "bin", "hex", "oct"}
_TEXT_FUNCS = {"str", "repr", "ascii", "format", "sorted", "list", "tuple", "set", "frozenset", "min", "max", "reversed",
               "enumerate", "zip", "iter", "dict", "text", "dedent", "cleandoc"}
_DYNAMIC_CODE_FUNCS = {"exec", "eval", "compile"}
_GLOBALS_FUNCS = {"globals", "locals", "vars"}
_STR_METHODS = {"join", "split", "rsplit", "splitlines", "partition", "rpartition", "format", "format_map", "strip", "lstrip", "rstrip", "lower", "upper", "casefold", "title", "capitalize",
                "replace", "encode", "decode", "removeprefix", "removesuffix", "expandtabs", "zfill", "ljust", "rjust", "center"}
_FILE_READ_ATTRS = {"read", "read_text", "read_bytes", "readlines"}
_SQL_FILE_LITERAL = re.compile(r"\A\s*[\w./~-]+\.sql\s*\Z")
_BYTES_WRITE_FORM = re.compile(r"\b(?:INSERT\s+INTO|DELETE\s+FROM|TRUNCATE|UPDATE\s+\S+\s+SET|COPY\s+\S+\s+FROM|MERGE\s+INTO|"
                               r"REFRESH\s+MATERIALIZED|CREATE\s+(?:\w+\s+)?TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE)

# What the scan cannot see by construction (printed with the impact statement; a `complete` scope is a statement about the
# scan, not about production).
WRITE_SCAN_LIMITATIONS = (
    "stored functions / procedures that write (SELECT fn(...), CALL proc(...)) are not resolved to the tables they write",
    "a writer that imports another module and calls it to write is only followed through its declared source_paths and the "
    "known idempotency helpers; a writer that also writes tables itself and delegates the rest reads as scanned",
    "triggers, rules, RLS and ON DELETE/UPDATE cascades are not writes the scan sees (the FK closure covers cascades)",
    "SQL built from runtime values, composed with psycopg sql.SQL/Identifier, or read from a file is reported as not scanned",
    "the default is CLOSED: the SQL handed to an execute-like call (execute/executemany/copy/copy_expert/execute_values/fetch/"
    "fetchrow/fetchval/prepare/exec_driver_sql/...) reads as scanned only when it is provably made of this file's own literals "
    "(a literal; an f-string/concatenation/format/join of such; a name every binding of which is such; a parameter whose in-file "
    "call sites all pass such; a loop variable over such a container; a class attribute assigned once in its class body; a local "
    "function that returns only such). An imported name or module attribute (imported_sql_constant), a call result, a subscript "
    "of something unprovable, an unbound name or attribute, a parameter with no / an unprovable call site, *args/**kwargs, a "
    "bytes literal, a dunder attribute (fn.__doc__), an execute method aliased or passed on (ex = cur.execute, partial, map) is "
    "reported as not scanned; so are copy_from/copy_to/copy_to_table/copy_records_to_table calls, exec/eval/compile, setattr, "
    "writes or aliases through globals()/locals()/vars()/sys.modules, `from x import *`, getattr(...)(...) of an execute/copy "
    "attribute, and a literal that ends in a write verb with no target (the table is joined on at runtime)",
    "an UPDATE / COPY whose SET / FROM tail or target is a placeholder or a runtime value is reported as not scanned; so is a "
    "statement whose verb comes from a name holding a bare verb (V = 'DELETE'; f'{V} FROM a'), or whose first token is a name "
    "followed by SQL words or by a name holding a SQL keyword (f'{V} {F} a'); SQL comments are whitespace and a comment marker "
    "inside a quoted run is text (the stripper is quote-aware); verbs are matched on the raw and on the comment-free text and "
    "all three readings are kept (the union: every table and every not-scanned reason of any), a third strips every comment marker "
    "wherever it sits, so a keyword split by a comment inside a string or a $$ body is still read; `$` inside an identifier (a$b$) "
    "does not open a dollar quote and a dollar tag may be non-ASCII",
    "a template of this file's own constants is READ as the statement it runs: `'%s %s t' % (V, F)`, `'{} {} t'.format(V, F)`, "
    "`f'{V}ETE FROM t'`, `'DELETE FROM'.strip() + ' t'`, `'DELETE FROM x'.replace('x', 't')`, `v, f = 'DELETE', 'FROM'` are "
    "rendered with the constants written out and scanned",
    "a name is policed as a possible mutable container UNLESS it is provably an immutable str/bytes/number/bool/None or a tuple "
    "of such (a call result, subscript, attribute, setdefault/get/pop, a loop over a container of lists ... is not): it is provable "
    "only while every use of it is a read (iteration, subscript "
    "load, .items()/.values()/.keys()/.get()/.copy(), len, in, str.join, a pure builtin, a mutator or item store on the bare "
    "name): aliasing it, passing it to a call, binding a method of it, mutating it through an attribute receiver (self.L.append), "
    "returning, yielding or storing it is container_escapes; a container (or a tuple) that holds another mutable container is not "
    "provable",
    "a class attribute is provable only on a plain class (undecorated, no bases but object, no metaclass, no subclass in the "
    "file, never constructed with arguments, its name never rebound, no __dict__ / __setattr__ / __getattribute__ use, no "
    "3-argument type(...) call, no `self.X = ...`, methods not called through the class with an explicit self) when it is an "
    "unannotated top-level `X = ...` assigned exactly once in the class body; dataclass / NamedTuple / Enum fields, subclass "
    "overrides, `+=`, `if`/`try` rebinding are not provable",
    "dispatch by string is not scanned (dynamic_dispatch): getattr with a runtime name, with a name that is a local def / class or "
    "a SQL-running method, or whose result is called; ANY use of globals()/locals()/vars() or __builtins__; gc.get_objects(); sys.modules, "
    "__import__, importlib, builtins, __main__, frames (_getframe, currentframe, f_globals), operator.methodcaller/attrgetter, "
    "__getattribute__; an imported or other foreign decorator on a function whose result or arguments the SQL depends on makes "
    "it unprovable",
    "a dotted or attribute name ({cfg.T}, {self.T}) is never read as a table constant; a quoted name that is not a plain "
    "lowercase identifier is not read; a SQL literal over 64 KB is not scanned; a file whose provenance resolution exceeds its "
    "work cap (60,000 steps) is not scanned (resolver_work_cap); a source_paths list that is mutated or aliased (append/+=/"
    "extend/item assignment/setattr/getattr/unpacking) is not followed",
    "SQL assembled from separately bound fragments (a list of keyword strings joined elsewhere, a verb in one name and its "
    "target in another) is not reassembled, except that a name holding a bare verb, or SQL words / a SQL-keyword name after a leading name, flag the statement: only literals, "
    "f-strings, + concatenation and a literal-separator ''.join([...]) of a list literal are rendered",
    "documented, not detected: VACUUM FULL / CLUSTER (rewrite a table, write no rows), COPY ... TO with a runtime target (an "
    "export), a class instance of another module that is called instead of this file's class (an imported delegate), `__dict__` on "
    "an instance (only matters for class attributes, which it already disables), SQL held by an in-file class attribute that a "
    "name-collision elsewhere makes unknowable",
)


def _norm_written_table(raw: str) -> str:
    """'public.x' / x / "x" / public."x" -> 'public.x'. Same normalisation as the registry side."""
    return _norm_table(raw.replace('"', "").strip().lower())


def _is_str(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _clean_literal(value: str) -> str:
    """Literal text never carries the placeholder control characters (a literal \\x01 must not read as an expression)."""
    return value.replace(_PH_OPEN, " ").replace(_PH_CLOSE, " ")


def _render_sql_node(node: ast.AST) -> str | None:
    """The text of a string-building expression with every non-literal part as a \\x01expr\\x02 placeholder; None if the
    node is not string-building at all (a plain str constant is handled by the caller)."""
    if _is_str(node):
        return _clean_literal(node.value)
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if _is_str(v):
                out.append(_clean_literal(v.value))
            elif isinstance(v, ast.FormattedValue):
                out.append(f"{_PH_OPEN}{ast.unparse(v.value)}{_PH_CLOSE}")
        return "".join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _render_sql_node(node.left), _render_sql_node(node.right)
        if left is None and right is None:
            return None
        return (left if left is not None else f"{_PH_OPEN}{ast.unparse(node.left)}{_PH_CLOSE}") + \
               (right if right is not None else f"{_PH_OPEN}{ast.unparse(node.right)}{_PH_CLOSE}")
    pf = _render_percent_or_format(node)
    if pf is not None:
        return pf
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join"
            and _is_str(node.func.value) and len(node.args) == 1 and not node.keywords
            and isinstance(node.args[0], (ast.List, ast.Tuple))
            and not any(isinstance(e, ast.Starred) for e in node.args[0].elts)):
        parts = []
        for e in node.args[0].elts:
            r = _render_sql_node(e)
            parts.append(r if r is not None else f"{_PH_OPEN}{ast.unparse(e)}{_PH_CLOSE}")
        return _clean_literal(node.func.value.value).join(parts)
    return None


_PERCENT_CONV = re.compile(r"%[sdir%]")


def _render_arg(node: ast.AST) -> str:
    r = _render_sql_node(node)
    return r if r is not None else f"{_PH_OPEN}{ast.unparse(node)}{_PH_CLOSE}"


def _render_percent_or_format(node: ast.AST) -> str | None:
    """`'%s %s hidden' % (V, F)` and `'{} {} hidden'.format(V, F)` / `'{a}'.format(a=V)`: the template with each argument in
    place (a literal as its text, anything else as a placeholder), so the statement the server runs can be read. Only the plain
    forms are supported: %s %r %d %i %% and {} {0} {name} without a spec, conversion, attribute or index."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and _is_str(node.left):
        tmpl = _clean_literal(node.left.value)
        right = node.right
        if isinstance(right, ast.Dict) or isinstance(right, ast.Starred):
            return None
        args = list(right.elts) if isinstance(right, ast.Tuple) else [right]
        if any(isinstance(a, ast.Starred) for a in args):
            return None
        convs = _PERCENT_CONV.findall(tmpl)
        if "%" in _PERCENT_CONV.sub("", tmpl) or sum(1 for c in convs if c != "%%") != len(args):
            return None
        it = iter(args)
        return _PERCENT_CONV.sub(lambda m: "%" if m.group() == "%%" else _render_arg(next(it)), tmpl)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format"
            and _is_str(node.func.value) and not any(isinstance(a, ast.Starred) for a in node.args)
            and not any(k.arg is None for k in node.keywords)):
        try:
            fields = list(string.Formatter().parse(_clean_literal(node.func.value.value)))
        except ValueError:
            return None
        kw = {k.arg: k.value for k in node.keywords}
        out, auto = [], 0
        for lit, name, spec, conv in fields:
            out.append(lit)
            if name is None:
                continue
            if spec or conv or "." in name or "[" in name:
                return None
            if name == "":
                name, auto = str(auto), auto + 1
            arg = node.args[int(name)] if name.isdigit() and int(name) < len(node.args) else kw.get(name)
            if arg is None:
                return None
            out.append(_render_arg(arg))
        return "".join(out)
    return None


def _string_const_value(node: ast.AST) -> str | None:
    return node.value if _is_str(node) else None


def _reads_a_file(node: ast.AST) -> bool:
    """True if the expression contains open(...) or a .read()/.read_text()/.read_bytes()/.readlines() call."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == "open") or (isinstance(f, ast.Attribute) and f.attr in _FILE_READ_ATTRS):
                return True
    return False


def _root_name(node: ast.AST) -> str | None:
    """The Name at the root of an attribute/subscript/call chain (a.b[c].d -> a), else None."""
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


_SQL_COMPOSITION_REASON = "write_form_not_analysed: sql.SQL / sql.Identifier composition"


def _is_sql_composition(func: ast.AST) -> bool:
    return (isinstance(func, ast.Attribute) and func.attr in _SQL_COMPOSITION_ATTRS and isinstance(func.value, ast.Name)
            and func.value.id == "sql") or (isinstance(func, ast.Name) and func.id in {"Identifier", "SQL", "Composed"})


def _is_container_value(node: ast.AST) -> bool:
    """An expression that evaluates to a MUTABLE container (list / dict / set, a comprehension, a copy or a combination of
    one): a name bound to it can be aliased and mutated from anywhere, so its uses are policed (`container_escapes`)."""
    if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
        return True
    if isinstance(node, ast.Call):
        f = node.func
        return (isinstance(f, ast.Name) and f.id in _CONTAINER_CALLS) or (
            isinstance(f, ast.Attribute) and f.attr in ("copy", "split", "splitlines", "keys", "values", "items", "fromkeys"))
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult, ast.BitOr)):
        return _is_container_value(node.left) or _is_container_value(node.right)
    if isinstance(node, ast.IfExp):
        return _is_container_value(node.body) or _is_container_value(node.orelse)
    if isinstance(node, ast.BoolOp):
        return any(_is_container_value(v) for v in node.values)
    return False


def _holds_mutable(node: ast.AST, depth: int = 0) -> bool:
    """`node` evaluates to a mutable container, or to something that CARRIES one at any depth: a tuple of (a tuple of ...) a list, a starred element that unpacks a container
    holding one, either branch of an `if`/`or`, either side of `+` / `*` (tuple concatenation). The nested-container refusal used to look ONE level down (`_is_container_value` on a
    direct element), so `[('a', ['b'])]` read as flat: an alias of the inner list (`inner = Q[0][1]`) mutated it with nothing tying the mutation to `Q`. Closed list: a name, call
    or subscript is not looked through (its own bindings are policed where it is bound); past depth 24 the answer is yes (fail closed)."""
    if depth > 24:
        return True
    if _is_container_value(node):
        return True
    d = depth + 1
    if isinstance(node, ast.Tuple):
        return any(_holds_mutable(e, d) for e in node.elts)
    if isinstance(node, ast.Starred):
        return _holds_mutable(node.value, d) or _has_nested_container(node.value, d)
    if isinstance(node, ast.IfExp):
        return _holds_mutable(node.body, d) or _holds_mutable(node.orelse, d)
    if isinstance(node, ast.BoolOp):
        return any(_holds_mutable(v, d) for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult)):
        return _holds_mutable(node.left, d) or _holds_mutable(node.right, d)
    return False


def _has_nested_container(node: ast.AST, depth: int = 0) -> bool:
    """A container literal / comprehension holding another mutable container as an element or value, at ANY depth through tuples and the other carriers `_holds_mutable` lists (a
    tuple that holds one included: the tuple cannot change but the list inside it can)."""
    if depth > 24:
        return True
    d = depth + 1
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return any(_holds_mutable(e, d) for e in node.elts)
    if isinstance(node, ast.Dict):
        return any(v is not None and _holds_mutable(v, d) for v in node.values)
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return _holds_mutable(node.elt, d)
    if isinstance(node, ast.DictComp):
        return _holds_mutable(node.value, d)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult, ast.BitOr)):      # [['a']] * 2, [['a']] + [['b']], {...} | {...}
        return _has_nested_container(node.left, d) or _has_nested_container(node.right, d)
    if isinstance(node, ast.IfExp):
        return _has_nested_container(node.body, d) or _has_nested_container(node.orelse, d)
    if isinstance(node, ast.BoolOp):
        return any(_has_nested_container(v, d) for v in node.values)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("list", "dict", "set", "frozenset", "tuple"):
        # the constructor copies its argument's elements / takes keyword values: list([['a']]), dict(k=['a']), dict([('k', ['a'])])
        return any(_has_nested_container(a, d) for a in node.args) or any(_holds_mutable(k.value, d) for k in node.keywords)      # an ARGUMENT is copied: its elements matter, not that it is a container
    return False


def _mentions_modules(node: ast.AST) -> bool:
    """`sys.modules[...]` (or any `.modules` attribute) somewhere in the chain: a way to reach another module's namespace."""
    return any(isinstance(n, ast.Attribute) and n.attr == "modules" for n in ast.walk(node))


def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    return {id(c): p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}


def _is_globals_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _GLOBALS_FUNCS


class _Budget(Exception):
    """The provenance evaluation visited more bindings than the cap allows: the statement is not scanned."""


class _NotConst(Exception):
    """An operand of the expression is not a constant (a parameter, a loop variable, an unknown call, a name with a non-assignment binding): the constant evaluator does not judge it."""


class _Unsupported(Exception):
    """Every operand is a constant but the operation cannot be evaluated (an unsupported operator or method, a size cap, a runtime error): the expression is NOT SCANNED."""


class _ConstSet(set):
    """A set value of the constant evaluator. Membership and length are fine; ITERATING it is not: the order of a set of strings changes with the interpreter's hash seed, so a
    text assembled from one (`''.join({'DEL', 'ETE FROM t'})`) has no single reading and is NOT SCANNED."""

    def __iter__(self):
        raise _Unsupported("the iteration order of a set is not deterministic")


class _Pieces:
    """A container the file BUILDS UP (`Q = []; Q.append(x)`, `D = {}; D['k'] = x`): its elements are known, their order and count are not. Indexing it yields any element (each is
    a candidate statement, and is scanned); ITERATING it (a join, a comprehension, `list(Q)`) has no single reading and is NOT SCANNED."""

    def __init__(self, items: list) -> None:
        self.items = items

    def __iter__(self):
        raise _Unsupported("the elements of a container built up by mutation have no fixed order or count")

    def __len__(self):
        raise _NotConst("the length of a container built up by mutation is a number, not a text")


_CV_MAX_VALUES = 32          # distinct constant values one expression may take (a name with several constant bindings): past it the expression is not judged here
_CV_MAX_COMBOS = 512         # candidate combinations tried for one operation
_CV_MAX_ITEMS = 4096         # elements of an evaluated container / iteration
_CV_STR_METHODS = {"join", "split", "rsplit", "splitlines", "partition", "rpartition", "format", "format_map", "strip", "lstrip", "rstrip", "lower", "upper", "casefold", "title",
                   "capitalize", "swapcase", "replace", "removeprefix", "removesuffix", "expandtabs", "zfill", "ljust", "rjust", "center", "encode", "translate", "count", "find",
                   "rfind", "index", "rindex", "startswith", "endswith", "isalpha", "isdigit", "isalnum", "isspace", "isupper", "islower"}
_CV_BYTES_METHODS = {"decode", "join", "replace", "strip", "lstrip", "rstrip", "lower", "upper", "split", "hex"}
_CV_DICT_METHODS = {"get", "keys", "values", "items", "copy"}
_CV_SEQ_METHODS = {"index", "count", "copy"}
_CV_BUILTINS = {"chr": chr, "ord": ord, "str": str, "repr": repr, "ascii": ascii, "int": int, "float": float, "bool": bool, "len": len, "list": list, "tuple": tuple, "set": set,
                "frozenset": frozenset, "dict": dict, "sorted": sorted, "reversed": lambda x: list(reversed(x)), "min": min, "max": max, "sum": sum, "range": lambda *a: list(range(*a)),
                "abs": abs, "any": any, "all": all, "zip": lambda *a: list(zip(*a)), "enumerate": lambda x, *a: list(enumerate(x, *a)), "bytes": bytes, "format": format}
def _cv_raw_items(v) -> list:
    """The elements of a set / frozenset in its arbitrary internal order (callers must not let that order reach a text)."""
    return list(frozenset.__iter__(v)) if type(v) is frozenset else list(set.__iter__(v))


def _cv_order_free(fn):
    """A builtin whose RESULT does not depend on the iteration order of a set argument (sorted / min / max / len / any / all / sum): the set is read through the plain `set` iterator."""
    return lambda *a, **k: fn(*[_cv_raw_items(x) if isinstance(x, (set, frozenset)) else x for x in a], **k)


for _n in ("sorted", "min", "max", "len", "any", "all", "sum"):
    _CV_BUILTINS[_n] = _cv_order_free(_CV_BUILTINS[_n])
_CV_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv, ast.Div: operator.truediv,
              ast.BitOr: operator.or_, ast.BitAnd: operator.and_, ast.BitXor: operator.xor, ast.LShift: operator.lshift, ast.RShift: operator.rshift, ast.Pow: operator.pow,
              ast.MatMult: operator.matmul}
_CV_CMPOPS = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Is: operator.is_,
              ast.IsNot: operator.is_not, ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}


class _WriteScan:
    """What one parsed module shows: resolved write tables, unresolved reasons, parametric functions, helper calls.

    The SQL text handed to an execute-like call is judged by a CLOSED allow-list (`_clean_expr`): it is `clean` only when it
    is positively recognised as made of literals of THIS file -- a literal, an f-string / `+` / format / join of clean parts, a
    name every binding of which is clean, a parameter whose in-file call sites all pass clean values, a loop variable over a
    clean literal container, a class attribute assigned once in the same class body. Anything else is not scanned."""

    MAX_RESOLVER_STEPS = 60_000          # bindings + expression nodes visited per file: past it the file is NOT scanned

    def __init__(self, tree: ast.Module, const_tree: ast.Module | None = None) -> None:
        self.tables: set[str] = set()
        self.unresolved: list[str] = []
        self.consts: dict[str, set[str]] = {}
        self.bindings: dict[str, list[tuple]] = {}          # name -> every binding (scope-blind, whole module)
        self.attr_bindings: dict[str, list[tuple]] = {}     # attribute name -> every `obj.attr = ...` binding in the module
        self.class_nodes: dict[str, list[ast.ClassDef]] = {}  # class name -> every ClassDef of that name
        self.base_names: set[str] = set()                   # names used as a base class anywhere in the module
        self.container_ids: set[str] = set()                # names / attributes bound to a mutable container (list/dict/set)
        self.refs_by_ident: dict[str, list[ast.AST]] = {}   # name / attribute -> every Load reference
        self.uses_dunder_dict = False
        self.uses_type_call = False
        self.aug_ops: dict[int, type] = {}                  # id(rhs node of an augmented assignment) -> its operator class
        self.aug_names: set[str] = set()                    # names that are the target of an augmented assignment (`s += x`): their value is not any one binding's
        self._cv_names: dict[str, object] = {}              # constant-evaluator cache: name -> its candidate values (or the exception it raised)
        self._cv_stack: set[str] = set()
        self._cv_nodes: dict[int, object] = {}              # constant-evaluator cache: expression node -> verdict
        self._cv_scanned: set[str] = set()                  # evaluated texts already scanned
        self.explicit_self_calls: set[tuple[str, str]] = set()   # (Class, method) called as Class.method(...)
        self._info_cache: dict[tuple, object] = {}
        self._parents: dict[int, ast.AST] | None = None
        self._const_tree: ast.Module | None = None
        self.local_classes: set[str] = set()
        self.func_defs: dict[str, list[ast.AST]] = {}       # def name -> every FunctionDef of that name
        self.method_ids: set[int] = set()                   # ids of FunctionDef nodes that sit directly in a class body
        self.imported: set[str] = set()                     # names bound by `import x` / `from x import y`
        self.exec_aliases: dict[str, str] = {}              # `from m import execute_values as ev` -> {"ev": "execute_values"}
        self.params: set[str] = set()
        self.local_defs: set[str] = set()                   # def / class names
        self.defined: set[str] = set()
        self.param_funcs: dict[str, list[tuple[str, int]]] = {}   # function -> [(param name, positional index)]
        self.method_param_funcs: set[str] = set()           # param_funcs entries whose index already excludes self/cls
        self.classmethod_funcs: set[str] = set()
        self.calls: list[ast.Call] = []                     # the calls of the scanned tree
        self.calls_by_callee: dict[str, list[ast.Call]] = {}      # callee name (Name id or Attribute attr) -> calls, whole module
        self.callee_ids: set[int] = set()
        self.value_refs: set[str] = set()                   # names / attributes referenced other than as the callee of a call
        self.node_class: dict[int, str | None] = {}         # Attribute node -> enclosing class
        self._memo: dict[tuple, str | None] = {}
        self._stack: set[tuple] = set()
        self._cycle_hit = False
        self._steps = 0
        # scanning ONE function of a helper module (const_tree given): its own parameters are filled by the caller, which is
        # where the table-parameter machinery (param_funcs / resolve_param_calls) resolves them
        self._entry_funcs = {id(n) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))} \
            if const_tree is not None else set()
        self._const_tree = const_tree if const_tree is not None else tree
        self._collect_constants(self._const_tree)
        self._index(self._const_tree)
        self._walk(tree, [])
        self._tripwire_calls(tree)

    # ---- bindings -------------------------------------------------------------------------------------------------

    def _bind(self, name: str, value: str | None) -> None:
        self.consts.setdefault(name, set()).add(value if value is not None else "\x00non-literal")

    def _bind_target(self, target: ast.AST, value: str | None = None) -> None:
        """Record every name a binding target introduces. A plain `NAME = "literal"` keeps its literal; every other form
        (tuple unpacking, attribute assignment, loop variable, ...) binds the name to an UNKNOWN value."""
        if isinstance(target, ast.Name):
            self._bind(target.id, value)
        elif isinstance(target, ast.Attribute):
            self._bind(target.attr, None)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                self._bind_target(e, None)
        elif isinstance(target, ast.Starred):
            self._bind_target(target.value, None)

    def _bind_target_value(self, target: ast.AST, value: ast.AST) -> None:
        """`a, b = 'x', 'y'` binds each name to its own literal (a constant), any other unpacking binds unknown values."""
        if (isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)) and len(target.elts) == len(value.elts)
                and not any(isinstance(e, ast.Starred) for e in list(target.elts) + list(value.elts))):
            for te, ve in zip(target.elts, value.elts):
                self._bind_target_value(te, ve)
        else:
            self._bind_target(target, _string_const_value(value))

    def _add(self, name: str, binding: tuple) -> None:
        self.bindings.setdefault(name, []).append(binding)

    def _bind_value(self, target: ast.AST, value: ast.AST) -> None:
        """`target = value`: elementwise for a literal tuple/list unpack of the same length, otherwise every name gets the
        whole value as an iterable it was drawn from."""
        if isinstance(target, ast.Name):
            self._add(target.id, ("expr", value))
            if _is_container_value(value):
                self.container_ids.add(target.id)
        elif isinstance(target, ast.Attribute):
            self.attr_bindings.setdefault(target.attr, []).append(("expr", value))
        elif isinstance(target, ast.Subscript):
            root = _root_name(target.value)
            if root:
                self._add(root, ("elem", value))
                self._add(root, ("subkey", target.slice))
        elif isinstance(target, (ast.Tuple, ast.List)):
            if (isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts)
                    and not any(isinstance(e, ast.Starred) for e in list(value.elts) + list(target.elts))):
                for t, v in zip(target.elts, value.elts):
                    self._bind_value(t, v)
            else:
                for t in target.elts:
                    self._bind_iter_target(t, value)
        elif isinstance(target, ast.Starred):
            self._bind_iter_target(target.value, value)

    def _bind_iter_target(self, target: ast.AST, iter_node: ast.AST, tag: str = "iter") -> None:
        if isinstance(target, ast.Name):
            self._add(target.id, (tag, iter_node))
        elif isinstance(target, ast.Attribute):
            self.attr_bindings.setdefault(target.attr, []).append((tag, iter_node))
        elif isinstance(target, ast.Subscript):
            root = _root_name(target.value)
            if root:
                self._add(root, (tag, iter_node))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                self._bind_iter_target(e, iter_node, "iter_values" if tag == "iter_values" else "iter")
        elif isinstance(target, ast.Starred):
            # `first, *rest = SRC`: `rest` is a fresh LIST (mutable, aliasable) whose elements are drawn from SRC. Tag "star" cleans like "iter" (the elements) but is NEVER an
            # immutable value (E6.1 follow-up: a starred target used to read as immutable because its elements are, so `alias = rest; alias.append(x)` went unpoliced)
            self._bind_iter_target(target.value, iter_node, "star")

    def _bind_unknown(self, target: ast.AST, why: str) -> None:
        if isinstance(target, ast.Name):
            self._add(target.id, ("unknown", why))
        elif isinstance(target, ast.Attribute):
            self.attr_bindings.setdefault(target.attr, []).append(("unknown", why))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                self._bind_unknown(e, why)
        elif isinstance(target, ast.Starred):
            self._bind_unknown(target.value, why)
        elif isinstance(target, ast.Subscript):
            root = _root_name(target.value)
            if root:
                self._add(root, ("unknown", why))

    def _collect_constants(self, tree: ast.Module) -> None:
        """name -> the set of values it is bound to ANYWHERE in the module (scope-blind on purpose: a name is a usable
        constant only if every binding of it is the same string literal). Any other binding of the name -- loop target,
        with/except/match target, comprehension target, augmented or walrus assignment, function parameter, import alias,
        global/nonlocal, def/class name, del, tuple unpacking, attribute assignment -- makes it unresolved. Also records every
        binding with what it was bound to (`self.bindings`) for the closed allow-list in `_clean_expr`."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    self._bind_target_value(t, node.value)
                    self._bind_value(t, node.value)
            elif isinstance(node, ast.AnnAssign):
                if node.value is not None:
                    self._bind_target(node.target, _string_const_value(node.value) if isinstance(node.target, ast.Name) else None)
                    self._bind_value(node.target, node.value)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    self.aug_names.add(node.target.id)
                    self.aug_ops[id(node.value)] = type(node.op)
                self._bind_target(node.target, None)
                self._bind_value(node.target, node.value)
            elif isinstance(node, ast.NamedExpr):
                self._bind_target(node.target, None)
                self._bind_value(node.target, node.value)
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                self._bind_target(node.target, None)
                it = node.iter
                if (isinstance(node.target, (ast.Tuple, ast.List)) and len(node.target.elts) == 2
                        and not any(isinstance(e, ast.Starred) for e in node.target.elts)
                        and isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute) and it.func.attr == "items" and not it.args):
                    self._bind_iter_target(node.target.elts[0], it.func.value, "iter_keys")      # `for k, v in X.items()`
                    self._bind_iter_target(node.target.elts[1], it.func.value, "iter_values")
                else:
                    self._bind_iter_target(node.target, node.iter)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        self._bind_target(item.optional_vars, None)
                        self._bind_unknown(item.optional_vars, "bound by a with statement")
            elif isinstance(node, ast.ExceptHandler):
                if node.name:
                    self._bind(node.name, None)
                    self._add(node.name, ("unknown", "bound by an except clause"))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                a = node.args
                positional = list(a.posonlyargs) + list(a.args)
                defaults = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
                for i, arg in enumerate(positional):
                    self._bind(arg.arg, None)
                    self.params.add(arg.arg)
                    self._add(arg.arg, ("param", node, i, arg.arg, defaults[i]) if not isinstance(node, ast.Lambda)
                              else ("unknown", "a lambda parameter"))
                for arg, d in zip(a.kwonlyargs, a.kw_defaults):
                    self._bind(arg.arg, None)
                    self.params.add(arg.arg)
                    self._add(arg.arg, ("param", node, None, arg.arg, d) if not isinstance(node, ast.Lambda)
                              else ("unknown", "a lambda parameter"))
                for arg in (a.vararg, a.kwarg):
                    if arg is not None:
                        self._bind(arg.arg, None)
                        self.params.add(arg.arg)
                        self._add(arg.arg, ("unknown", "a *args / **kwargs parameter"))
                if not isinstance(node, ast.Lambda):
                    self._bind(node.name, None)
                    self.local_defs.add(node.name)
                    self._add(node.name, ("def", node.name))
                    self.func_defs.setdefault(node.name, []).append(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for al in node.names:
                    bound = al.asname or al.name.split(".")[0]
                    self._bind(bound, None)
                    self.imported.add(bound)
                    self._add(bound, ("import", bound))
                    if isinstance(node, ast.ImportFrom) and al.asname and al.name in _SQL_SECOND_ARG_FUNCS:
                        self.exec_aliases[al.asname] = al.name
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                for n in node.names:
                    self._bind(n, None)
                    self._add(n, ("unknown", "declared global / nonlocal"))
            elif isinstance(node, ast.ClassDef):
                self._bind(node.name, None)
                self.local_defs.add(node.name)
                self.local_classes.add(node.name)
                self._add(node.name, ("def", node.name))
                self.class_nodes.setdefault(node.name, []).append(node)
                for b in node.bases:
                    base = b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else None
                    if base:
                        self.base_names.add(base)
                for stmt in node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.method_ids.add(id(stmt))
            elif isinstance(node, ast.Delete):
                for t in node.targets:
                    self._bind_target(t, None)
                    self._bind_unknown(t, "deleted")
            elif isinstance(node, ast.MatchAs) and node.name:
                self._bind(node.name, None)
                self._add(node.name, ("unknown", "bound by a match pattern"))
            elif isinstance(node, ast.MatchStar) and node.name:
                self._bind(node.name, None)
                self._add(node.name, ("unknown", "bound by a match pattern"))
            elif isinstance(node, ast.MatchMapping) and node.rest:
                self._bind(node.rest, None)
                self._add(node.rest, ("unknown", "bound by a match pattern"))
            elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
                self._bind_target(node.name, None)
                self._bind_unknown(node.name, "a type alias")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _CONTAINER_MUTATORS:
                root = _root_name(node.func.value)
                if root:                                      # X.append(v) adds the element v; X.update(C) adds C's elements
                    tag = "econt" if node.func.attr in _CONTAINER_BULK_MUTATORS else "elem"
                    for a in node.args:
                        self._add(root, (tag, a.value if isinstance(a, ast.Starred) else a))
                    for k in node.keywords:
                        self._add(root, ("elem", k.value))

    def _index(self, tree: ast.Module) -> None:
        """Whole-module indexes the provenance check needs: the enclosing class of each attribute reference, every call by
        callee name, and every name/attribute used as a value rather than called (an alias, a partial(), a map())."""
        todo: list[tuple[ast.AST, str | None]] = [(tree, None)]
        while todo:
            node, cls = todo.pop()
            if isinstance(node, ast.ClassDef):
                cls = node.name
            if isinstance(node, ast.Attribute):
                self.node_class[id(node)] = cls
            if isinstance(node, ast.Call):
                f = node.func
                self.callee_ids.add(id(f))
                if isinstance(f, ast.Name) and f.id == "type" and len(node.args) >= 3:
                    self.uses_type_call = True
                if isinstance(f, ast.Name):
                    self.calls_by_callee.setdefault(f.id, []).append(node)
                elif isinstance(f, ast.Attribute):
                    self.calls_by_callee.setdefault(f.attr, []).append(node)
            for child in ast.iter_child_nodes(node):
                todo.append((child, cls))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.refs_by_ident.setdefault(node.id, []).append(node)
                if id(node) not in self.callee_ids:
                    self.value_refs.add(node.id)
            elif isinstance(node, ast.Attribute):
                if node.attr in ("__dict__", "__setattr__", "__getattribute__", "__delattr__"):
                    self.uses_dunder_dict = True
                if isinstance(node.value, ast.Name):
                    self.explicit_self_calls.add((node.value.id, node.attr))
                if isinstance(node.ctx, ast.Load):
                    self.refs_by_ident.setdefault(node.attr, []).append(node)
                    if id(node) not in self.callee_ids:
                        self.value_refs.add(node.attr)

    def _resolve_const(self, expr: str) -> str | None:
        """A plain identifier -> its single string value, else None. A dotted / attribute expression ('cfg.T', 'self.T') is
        NEVER a table constant: resolving it by its last segment would read `{cfg.T}` as an unrelated local T."""
        name = expr.strip() if re.fullmatch(r"[A-Za-z_]\w*", expr.strip()) else None
        vals = self.consts.get(name or "")
        if vals and len(vals) == 1:
            (only,) = vals
            return None if only == "\x00non-literal" else only
        return None

    def _is_method(self, fn: ast.AST) -> bool:
        """A def in a class body whose first parameter is self/cls (and is not a staticmethod): its positional arguments are
        shifted by one at an `obj.method(...)` call."""
        if id(fn) not in self.method_ids or not fn.args.args and not fn.args.posonlyargs:
            return False
        first = (list(fn.args.posonlyargs) + list(fn.args.args))[0].arg
        static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in fn.decorator_list)
        return first in ("self", "cls") and not static

    @staticmethod
    def _is_classmethod(fn: ast.AST) -> bool:
        return any(isinstance(d, ast.Name) and d.id == "classmethod" for d in fn.decorator_list)

    @staticmethod
    def _foreign_decorator(fn: ast.AST) -> bool:
        """A decorator other than staticmethod / classmethod / property may wrap the function and change what it returns or
        which arguments reach it (an imported decorator is code this file does not show)."""
        return any(not (isinstance(d, ast.Name) and d.id in ("staticmethod", "classmethod", "property")) for d in fn.decorator_list)

    def _arg_shift(self, func: ast.AST, call: ast.Call) -> int:
        """How many parameters of `func` the call site does not pass: 1 for `obj.method(...)` and for a classmethod called
        through its class (cls is bound); 0 for `Cls.method(instance, ...)`, a staticmethod, a plain function."""
        if not self._is_method(func) or not isinstance(call.func, ast.Attribute):
            return 0
        on_class = isinstance(call.func.value, ast.Name) and call.func.value.id in self.local_classes
        return 0 if (on_class and not self._is_classmethod(func)) else 1

    # ---- the closed allow-list: is this expression made only of this file's own literals? -------------------------------

    def _memoised(self, key: tuple, compute) -> str | None:
        """compute() once per key. A key met again while it is being computed is a cycle: assumed clean (a cycle adds no
        new source), and any result that leaned on that assumption is not cached (a problem found is always definitive)."""
        if key in self._memo:
            return self._memo[key]
        if key in self._stack:
            self._cycle_hit = True
            return None
        self._stack.add(key)
        saved, self._cycle_hit = self._cycle_hit, False
        try:
            result = compute()
        finally:
            self._stack.discard(key)
        hit = self._cycle_hit
        self._cycle_hit = saved or hit
        if result is not None or not hit:
            self._memo[key] = result
        return result

    @property
    def work_steps(self) -> int:
        """Read-only view of the work counter `_step` increments (bindings + expression nodes visited so far). The deterministic cost
        measure the tests bound (steps per source line, steps against MAX_RESOLVER_STEPS) instead of a wall-clock budget."""
        return self._steps

    def _step(self) -> None:
        """One unit of provenance work; the cap makes a hostile file cost bounded time and fall back to NOT scanned."""
        self._steps += 1
        if self._steps > self.MAX_RESOLVER_STEPS:
            raise _Budget(f"more than {self.MAX_RESOLVER_STEPS} bindings / expressions examined in this file")

    # ---- the constant evaluator: expressions built only from constants are READ, never passed ------------------------------

    def _cv_uniq(self, vals: list) -> list:
        out, seen = [], set()
        for v in vals:
            k = (type(v).__name__, repr(v))
            if k not in seen:
                seen.add(k)
                out.append(v)
                if len(out) > _CV_MAX_VALUES:
                    raise _NotConst("too many distinct constant values")
        return out

    @staticmethod
    def _cv_check(v: object) -> object:
        if isinstance(v, (str, bytes, bytearray)) and len(v) > MAX_SQL_LITERAL_CHARS:
            raise _NotConst("value longer than the literal cap")           # a statement that long is `sql_literal_too_long` where it is scanned; not this evaluator's to judge
        if isinstance(v, (list, tuple, set, frozenset, dict)) and len(v) > _CV_MAX_ITEMS:
            raise _NotConst("container larger than the evaluation cap")
        if isinstance(v, (set, frozenset)) and not isinstance(v, _ConstSet):
            return _ConstSet(_cv_raw_items(v))
        return v

    def _cv_map(self, fn, *lists: list) -> list:
        """fn applied to every combination of the operands' candidate values (a bounded product); a runtime error of the operation is _Unsupported."""
        n = 1
        for lst in lists:
            n *= max(len(lst), 1)
        if n > _CV_MAX_COMBOS:
            raise _NotConst("too many candidate combinations")
        out = []
        for combo in itertools.product(*lists):
            try:
                r = fn(*combo)
            except (_Budget, _NotConst, _Unsupported):
                raise
            except Exception as exc:                                  # noqa: BLE001 -- an operation that fails at run time on these constants yields no statement: not judged here
                raise _NotConst(f"{type(exc).__name__}") from None
            out.append(self._cv_check(r))
        return self._cv_uniq(out)

    @staticmethod
    def _cv_one(cands: list) -> object:
        if len(cands) != 1:
            raise _NotConst("several candidate values")
        return cands[0]

    def _name_cvals(self, name: str, depth: int) -> list:
        """A name whose EVERY binding is a plain assignment of a constant expression: the candidate values of those bindings (a name assigned in several places is each of them,
        the file's scope-blind reading). An augmented-assignment target, a parameter, loop variable, import, def, item store or mutator call is not a constant."""
        if name in self._cv_names:
            hit = self._cv_names[name]
            if isinstance(hit, Exception):
                raise hit
            return hit
        bound = self.bindings.get(name)
        if not bound or name in self._cv_stack:
            raise _NotConst(name)
        self._cv_stack.add(name)
        try:
            res = self._cv_name_value(name, sorted(bound, key=lambda b: (getattr(b[1], "lineno", 0), getattr(b[1], "col_offset", 0)) if isinstance(b[1], ast.AST) else (0, 0)), depth)
        except (_NotConst, _Unsupported) as exc:
            self._cv_names[name] = exc
            raise
        finally:
            self._cv_stack.discard(name)
        self._cv_names[name] = res
        return res

    def _cv_name_value(self, name: str, bound: list, depth: int) -> list:
        """The candidate values of a name from ALL its bindings in source order. A plain assignment is one candidate; `s += x` / `s = s + x` (also in a loop) extends the text built so far
        by the piece (every cumulative arrangement is a candidate, and a loop variable's pieces are also taken all together in order); a loop variable over a constant container is
        any of its elements; a container built up by `.append` / item stores is a `_Pieces` (indexable, never iterable). Anything else is not a constant."""
        container_tags = ("elem", "econt", "subkey")
        if any(b[0] in container_tags for b in bound):
            items: list = []
            for b in bound:
                if b[0] == "expr":
                    for v in self._cvals(b[1], {}, depth):
                        if isinstance(v, dict):
                            items.extend(v.values()); items.extend(v.keys())
                        elif isinstance(v, (list, tuple, str)):
                            items.extend(v)
                        elif isinstance(v, (set, frozenset)):
                            items.extend(_cv_raw_items(v))
                        else:
                            raise _NotConst(name)
                elif b[0] in container_tags:
                    for v in self._cvals(b[1], {}, depth):
                        if b[0] == "econt" and isinstance(v, (list, tuple, set, frozenset)):
                            items.extend(_cv_raw_items(v) if isinstance(v, (set, frozenset)) else v)
                        else:
                            items.append(v)
                else:
                    raise _NotConst(name)
            return [_Pieces(self._cv_uniq(items))]
        vals: list = []
        cur: list = []                                                # the candidates of the text built so far (since the last plain assignment)
        pieces_n = 0
        for b in bound:
            tag = b[0]
            if tag == "iter":                                         # a loop variable / unpack target over a constant container: any of its elements
                for it in self._cvals(b[1], {}, depth):
                    try:
                        vals.extend(_cv_raw_items(it) if isinstance(it, (set, frozenset)) else list(it))
                    except (TypeError, _Unsupported):
                        raise _NotConst(name) from None
                continue
            if tag != "expr":
                raise _NotConst(name)
            node = b[1]
            if isinstance(node, ast.Constant) and id(node) not in self.aug_ops:     # a literal binding costs nothing to read (thousands of `q = 'SELECT 1'` stay linear)
                vals.append(node.value)
                cur = [node.value]
                continue
            self._step()
            aug_op = self.aug_ops.get(id(node))
            selfref = aug_op is None and any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node))
            if aug_op is None and not selfref:
                cur = self._cvals(node, {}, depth)
                vals.extend(cur)
                continue
            if aug_op is not None and aug_op is not ast.Add:
                raise _Unsupported(f"{name} is updated with an augmented operator that is not `+=`")
            pieces_n += 1
            if pieces_n > 64:
                raise _Unsupported(f"{name} is assembled from more than 64 pieces")
            pieces = self._cvals(node, {name: ""} if selfref else {}, depth)
            # a piece drawn from a loop variable: the loop appends ALL its elements in order, so that text is a candidate too
            if isinstance(node, ast.Name) or selfref:
                for n in ast.walk(node):
                    if isinstance(n, ast.Name) and n.id != name and n.id in self.bindings and any(x[0] == "iter" for x in self.bindings[n.id]):
                        try:
                            for it in self._cv_name_iter_sources(n.id, depth):
                                pieces = pieces + ["".join(it)]
                        except TypeError:
                            pass
            mode = "append" if aug_op is not None else "both"                   # `s += x` appends; `s = s + x` appends; `s = x + s` prepends; any other self-reference: either
            if selfref and isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Name) and node.left.id == name:
                    mode = "append"
                elif isinstance(node.right, ast.Name) and node.right.id == name:
                    mode = "prepend"
            new_cur = []
            for base in (cur or [""]):
                for piece in pieces:
                    try:
                        if mode in ("append", "both"):
                            new_cur.append(base + piece)
                        if mode in ("prepend", "both"):
                            new_cur.append(piece + base)
                    except TypeError:
                        raise _NotConst(name) from None
            cur = self._cv_uniq(new_cur)
            vals.extend(cur)
        if not vals:
            raise _NotConst(name)
        return self._cv_uniq(vals)

    def _cv_name_iter_sources(self, name: str, depth: int) -> list:
        """For a loop variable: each constant iterable it ranges over, as an ordered list of its elements."""
        out = []
        for b in self.bindings.get(name, []):
            if b[0] == "iter":
                for it in self._cvals(b[1], {}, depth):
                    if isinstance(it, (set, frozenset)):
                        raise _Unsupported("loop over a set")
                    out.append(list(it))
        return out

    def _cvals(self, node: ast.AST | None, env: dict, depth: int = 0) -> list:
        """The candidate values of `node` when it is built ONLY from constants, constant-bound names and comprehension variables, through any operator, subscript, container,
        comprehension, conditional or call of a closed list of pure builtins / str, bytes, dict and sequence methods; _NotConst when some operand is not a constant;
        _Unsupported when every operand is but the operation cannot be evaluated. No import, no call of anything this file defines, nothing executed but those pure operations."""
        if node is None:
            return [None]
        if isinstance(node, ast.Constant):
            return [node.value]
        if isinstance(node, ast.Name):
            if node.id in env:
                return [env[node.id]]
            if node.id in self._cv_names:                             # a cached name costs nothing
                return self._name_cvals(node.id, depth)
        self._step()
        if depth > 150:
            raise _Unsupported("nesting too deep")
        d = depth + 1
        if isinstance(node, ast.Name):
            return self._name_cvals(node.id, d)
        if isinstance(node, ast.JoinedStr):
            return self._cv_map(lambda *xs: "".join(xs), *[self._cvals(v, env, d) for v in node.values])
        if isinstance(node, ast.FormattedValue):
            conv = node.conversion

            def fmt(x, spec):
                x = str(x) if conv == 115 else repr(x) if conv == 114 else ascii(x) if conv == 97 else x
                return format(x, spec)
            return self._cv_map(fmt, self._cvals(node.value, env, d), self._cvals(node.format_spec, env, d) if node.format_spec is not None else [""])
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            stars = [isinstance(e, ast.Starred) for e in node.elts]
            parts = [self._cvals(e.value if st else e, env, d) for e, st in zip(node.elts, stars)]
            make = tuple if isinstance(node, ast.Tuple) else list if isinstance(node, ast.List) else set

            def build(*xs):
                items = []
                for x, st in zip(xs, stars):
                    items.extend(x) if st else items.append(x)
                return make(items)
            return self._cv_map(build, *parts)
        if isinstance(node, ast.Dict):
            unpack = [k is None for k in node.keys]
            ks = [self._cvals(k, env, d) if k is not None else [None] for k in node.keys]
            vs = [self._cvals(v, env, d) for v in node.values]

            def build_dict(*xs):
                n = len(ks)
                out: dict = {}
                for u, k, v in zip(unpack, xs[:n], xs[n:]):
                    out.update(v) if u else out.__setitem__(k, v)
                return out
            return self._cv_map(build_dict, *ks, *vs)
        if isinstance(node, ast.UnaryOp):
            fn = {ast.Not: operator.not_, ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Invert: operator.invert}[type(node.op)]
            return self._cv_map(fn, self._cvals(node.operand, env, d))
        if isinstance(node, ast.BinOp):
            op = type(node.op)
            fn = _CV_BINOPS.get(op)
            left, right = self._cvals(node.left, env, d), self._cvals(node.right, env, d)
            if fn is None:
                raise _Unsupported("operator")

            def binop(a, b):
                if op is ast.Mult:
                    for seq, n in ((a, b), (b, a)):
                        if isinstance(seq, (str, bytes, list, tuple)) and isinstance(n, int) and len(seq) * max(n, 0) > MAX_SQL_LITERAL_CHARS:
                            raise _NotConst("repetition larger than the literal cap")
                if op in (ast.Pow, ast.LShift) and isinstance(b, int) and (abs(b) > 64 or (isinstance(a, int) and abs(a) > (1 << 64))):
                    raise _NotConst("exponent too large")
                return fn(a, b)
            return self._cv_map(binop, left, right)
        if isinstance(node, ast.BoolOp):
            is_and = isinstance(node.op, ast.And)

            def go(i: int) -> list:
                vals = self._cvals(node.values[i], env, d)
                if i == len(node.values) - 1:
                    return vals
                out: list = []
                for v in vals:
                    out.extend([v] if (not v if is_and else v) else go(i + 1))
                return self._cv_uniq(out)
            return go(0)
        if isinstance(node, ast.Compare):
            ops = [_CV_CMPOPS.get(type(o)) for o in node.ops]
            if any(o is None for o in ops):
                raise _Unsupported("comparison")
            parts = [self._cvals(node.left, env, d)] + [self._cvals(c, env, d) for c in node.comparators]

            def chain(*xs):
                return all(o(a, b) for o, a, b in zip(ops, xs, xs[1:]))
            return self._cv_map(chain, *parts)
        if isinstance(node, ast.IfExp):
            out: list = []
            for t in self._cvals(node.test, env, d):
                out.extend(self._cvals(node.body if t else node.orelse, env, d))
            return self._cv_uniq(out)
        if isinstance(node, ast.Slice):
            return self._cv_map(slice, self._cvals(node.lower, env, d), self._cvals(node.upper, env, d), self._cvals(node.step, env, d))
        if isinstance(node, ast.Subscript):
            vals = self._cvals(node.value, env, d)
            out = [x for v in vals if isinstance(v, _Pieces) for x in v.items]          # a container built up by mutation: any element it can hold
            plain = [v for v in vals if not isinstance(v, _Pieces)]
            if plain:
                out.extend(self._cv_map(operator.getitem, plain, self._cvals(node.slice, env, d)))
            return self._cv_uniq(out)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            return self._cv_comp(node, env, d)
        if isinstance(node, ast.Call):
            return self._cv_call(node, env, d)
        raise _NotConst(type(node).__name__)

    def _cv_comp(self, node: ast.AST, env: dict, d: int) -> list:
        gens = node.generators
        if any(g.is_async for g in gens):
            raise _Unsupported("async comprehension")

        def bind(target: ast.AST, item: object, e: dict) -> None:
            if isinstance(target, ast.Name):
                e[target.id] = item
            elif isinstance(target, (ast.Tuple, ast.List)):
                items = list(item)
                if len(items) != len(target.elts) or any(isinstance(t, ast.Starred) for t in target.elts):
                    raise _Unsupported("unpacking")
                for t, i in zip(target.elts, items):
                    bind(t, i, e)
            else:
                raise _Unsupported("comprehension target")

        def run(i: int, e: dict, out: list, firsts: list | None) -> None:
            if i == len(gens):
                if isinstance(node, ast.DictComp):
                    out.append((self._cv_one(self._cvals(node.key, e, d)), self._cv_one(self._cvals(node.value, e, d))))
                else:
                    out.append(self._cv_one(self._cvals(node.elt, e, d)))
                return
            it = self._cv_one(self._cvals(gens[i].iter, e, d)) if firsts is None else firsts
            try:
                seq = list(itertools.islice(iter(it), _CV_MAX_ITEMS + 1))
            except TypeError:
                raise _Unsupported("iteration") from None
            if len(seq) > _CV_MAX_ITEMS:
                raise _Unsupported("iteration larger than the evaluation cap")
            for item in seq:
                self._step()
                e2 = dict(e)
                bind(gens[i].target, item, e2)
                if all(self._cv_one(self._cvals(c, e2, d)) for c in gens[i].ifs):
                    run(i + 1, e2, out, None)

        results = []
        for first in self._cvals(gens[0].iter, env, d):             # the outermost iterable may be any of its candidate values
            out: list = []
            run(0, dict(env), out, first)
            try:
                results.append(dict(out) if isinstance(node, ast.DictComp) else set(out) if isinstance(node, ast.SetComp) else out)
            except TypeError:
                raise _Unsupported("unhashable element") from None
        return self._cv_uniq([self._cv_check(r) for r in results])

    def _cv_call(self, node: ast.Call, env: dict, d: int) -> list:
        f = node.func
        if isinstance(f, ast.Attribute):
            if isinstance(f.value, ast.Name) and f.value.id in ("str", "bytes") and f.value.id not in env and f.value.id not in self.bindings and f.value.id not in self.defined:
                cls = str if f.value.id == "str" else bytes
                allowed = _CV_STR_METHODS if cls is str else _CV_BYTES_METHODS
                recvs = [cls]
                static = True
            else:
                recvs = self._cvals(f.value, env, d)
                allowed, static = None, False
            attr = f.attr
        elif isinstance(f, ast.Name):
            if f.id in env or f.id in self.bindings or f.id in self.defined or f.id not in _CV_BUILTINS:
                raise _NotConst(f.id)
            recvs, attr, allowed, static = [None], None, None, False
        else:
            raise _NotConst("call")
        stars = [isinstance(a, ast.Starred) for a in node.args]
        argc = [self._cvals(a.value if st else a, env, d) for a, st in zip(node.args, stars)]
        kws = [k.arg for k in node.keywords]
        kwc = [self._cvals(k.value, env, d) for k in node.keywords]
        if any(k is None for k in kws):
            raise _Unsupported("keyword unpacking")
        n = len(argc)

        def call(recv, *xs):
            args, i = [], 0
            for x, st in zip(xs[:n], stars):
                args.extend(x) if st else args.append(x)
            kwargs = dict(zip(kws, xs[n:]))
            if attr is None:
                return _CV_BUILTINS[f.id](*args, **kwargs)
            if static:
                if attr not in allowed:
                    raise _Unsupported(f"method {attr}")
                return getattr(recv, attr)(*args, **kwargs)
            ok = (_CV_STR_METHODS if isinstance(recv, str) else _CV_BYTES_METHODS if isinstance(recv, bytes) else _CV_DICT_METHODS if isinstance(recv, dict)
                  else _CV_SEQ_METHODS if isinstance(recv, (list, tuple)) else ())
            if attr not in ok:
                raise _Unsupported(f"method {attr}")
            res = getattr(recv, attr)(*args, **kwargs)
            return list(res) if isinstance(res, (type({}.keys()), type({}.values()), type({}.items()))) else res
        return self._cv_map(call, recvs, *argc, *kwc)

    def _const_text_verdict(self, node: ast.AST) -> str | None:
        """For an expression built only from constants: when it evaluates to text, that text (every candidate) is SCANNED as the statement it runs, and the expression is clean;
        when it is constant-only but cannot be evaluated, it is NOT SCANNED (a reach, never clean). None when the expression is not constant-only or does not evaluate to text
        (the existing handling applies). Cached per node. (E6.1 follow-up: this replaces an operator allow-list that a wrapper or a named constant walked around.)"""
        key = id(node)
        if key in self._cv_nodes:
            return self._cv_nodes[key]
        verdict: str | None = None
        try:
            vals = self._cvals(node, {})
        except _NotConst:
            vals = None
        except _Unsupported as exc:
            verdict = f"write_form_not_analysed: a constant-only template whose text this scan cannot read: {ast.unparse(node)[:60]} ({exc})"
            vals = None
        if vals is not None and vals and all(isinstance(v, str) for v in vals):
            for text in vals:
                if text not in self._cv_scanned:
                    self._cv_scanned.add(text)
                    self._scan_text(text, [])
            verdict = ""                                              # "" = evaluated, scanned and clean
        self._cv_nodes[key] = verdict
        return verdict

    def _clean_expr(self, node: ast.AST | None) -> str | None:
        """None if `node` is provably built only from this file's literals, else the reason it is not."""
        if node is None:
            return None
        self._step()
        if isinstance(node, (ast.BinOp, ast.Subscript, ast.Call, ast.IfExp, ast.BoolOp, ast.Name)):
            verdict = self._const_text_verdict(node)
            if verdict:
                return verdict                                        # constant-only but unevaluable: NOT SCANNED
            # ("" = constant-only text that evaluated: its text has been SCANNED as the statement it runs; the closed allow-list below still judges the expression as before,
            #  so the evaluator only ever ADDS tables and reasons, it never makes an expression cleaner than the allow-list found it)
        unp = lambda: ast.unparse(node)[:60]  # noqa: E731
        if isinstance(node, ast.Constant):
            return "bytes_sql_literal: SQL passed as bytes is not analysed" if isinstance(node.value, (bytes, bytearray)) else None
        if isinstance(node, ast.JoinedStr):
            for v in node.values:
                if isinstance(v, ast.FormattedValue):
                    p = self._clean_expr(v.value) or self._clean_expr(v.format_spec)
                    if p:
                        return p
            return None
        if isinstance(node, ast.BinOp):
            return self._clean_expr(node.left) or self._clean_expr(node.right)
        if isinstance(node, ast.UnaryOp):
            return self._clean_expr(node.operand)
        if isinstance(node, ast.BoolOp):
            return next((p for p in (self._clean_expr(v) for v in node.values) if p), None)
        if isinstance(node, ast.Compare):
            return None                                           # a bool: no SQL text
        if isinstance(node, ast.IfExp):
            return self._clean_expr(node.body) or self._clean_expr(node.orelse)
        if isinstance(node, ast.Name):
            return self._clean_name(node.id)
        if isinstance(node, ast.Attribute):
            return self._clean_attribute(node)
        if isinstance(node, ast.Subscript):
            p = self._clean_expr(node.value)
            if p is None:
                return None                                       # a whole container of clean values, any index
            return p if p.startswith(("imported_sql_constant", "container_escapes")) else f"sql_from_subscript: {unp()} ({p})"
        if isinstance(node, ast.Call):
            return self._clean_call(node)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return next((p for p in (self._clean_expr(e) for e in node.elts) if p), None)
        if isinstance(node, ast.Dict):
            return next((p for p in (self._clean_expr(e) for e in list(node.keys) + list(node.values) if e is not None) if p), None)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self._clean_expr(node.elt)
        if isinstance(node, ast.DictComp):
            return self._clean_expr(node.key) or self._clean_expr(node.value)
        if isinstance(node, (ast.Starred, ast.Await, ast.NamedExpr)):
            return self._clean_expr(node.value)
        if isinstance(node, ast.Slice):
            return None
        return f"unresolved_sql_expression: {type(node).__name__}"

    # ---- mutable containers: provable only while every use of the name is a read -----------------------------------------

    def _parent_of(self, node: ast.AST) -> ast.AST | None:
        if self._parents is None:
            self._parents = _parent_map(self._const_tree)
        return self._parents.get(id(node))

    def _container_problem(self, ident: str) -> str | None:
        """A name / attribute bound to a mutable container is provable only if EVERY use of it is a read: iteration, a
        subscript load, `.items()/.values()/.keys()/.get()/.copy()`, `len`, `in`, `str.join(...)`, a pure builtin, a mutator
        call or item store on the BARE name (those are tracked as bindings). Aliasing it, passing it on, binding a method of
        it, mutating it through an attribute receiver (`self.L.append`), returning, yielding or storing it elsewhere hides a
        mutation from this scan. A container that holds another mutable container is not provable at all."""
        return self._memoised(("c", ident), lambda: self._container_problem_uncached(ident))

    def _container_problem_uncached(self, ident: str) -> str | None:
        for b in self.bindings.get(ident, []) + self.attr_bindings.get(ident, []):
            if (b[0] in ("expr", "econt") and _has_nested_container(b[1])) or (b[0] in ("elem", "subkey") and _holds_mutable(b[1])):
                return f"container_escapes: {ident} holds another mutable container (an inner alias can mutate it)"
        for ref in self.refs_by_ident.get(ident, []):
            self._step()
            how = self._use_problem(ref, 0)
            if how:
                return f"container_escapes: {ident} is {how}"
        return None

    def _use_problem(self, ref: ast.AST, depth: int) -> str | None:
        """None if this reference of a container is a read; else how it escapes."""
        par = self._parent_of(ref)
        bare = isinstance(ref, ast.Name)
        if par is None or depth > 6:
            return "used in a position this scan cannot read"
        if isinstance(par, (ast.For, ast.AsyncFor, ast.comprehension)):
            return None                                           # iteration (a Load can only be the iterable or a condition)
        if isinstance(par, ast.Subscript) and par.value is ref:
            if isinstance(par.ctx, (ast.Store, ast.Del)) and not bare:
                return "mutated through an attribute receiver (item assignment)"
            return None                                           # NAME[k] load, or a tracked item store / delete on the bare name
        if isinstance(par, ast.Subscript):
            return "used as a subscript key"
        if isinstance(par, ast.Attribute) and par.value is ref:
            gp = self._parent_of(par)
            if not (isinstance(gp, ast.Call) and gp.func is par):
                return f"bound as a method / read as an attribute (.{par.attr})"
            if par.attr in ("items", "values", "keys", "copy", "get"):
                return self._derived_problem(gp, depth + 1, par.attr == "get")
            if par.attr == "join" or par.attr in _STR_METHODS:
                return None
            if par.attr in _CONTAINER_MUTATORS:
                return None if bare else f"mutated through an attribute receiver (.{par.attr})"
            if par.attr in _HARMLESS_MUTATORS:
                return None
            return f"used as the receiver of .{par.attr}()"
        if isinstance(par, ast.Call):
            f = par.func
            if ref in par.args or any(k.value is ref for k in par.keywords):
                if (isinstance(f, ast.Attribute) and f.attr in _EXECUTE_ATTRS | _SQL_SECOND_ARG_FUNCS) or (
                        isinstance(f, ast.Name) and (f.id in _SQL_SECOND_ARG_FUNCS or f.id in self.exec_aliases)):
                    return None                                   # handed to the database as SQL text / parameters: a read
                if isinstance(f, ast.Name) and f.id in _PURE_CONSUMERS and ref in par.args:
                    return self._derived_problem(par, depth + 1, False)
                if isinstance(f, ast.Attribute) and f.attr == "join" and ref in par.args:
                    return None
                if (isinstance(f, ast.Attribute) and f.attr in _CONTAINER_MUTATORS and isinstance(f.value, ast.Name)
                        and f.value.id not in _CONTAINER_CALLS and f.value.id not in self.imported and f.value.id in self.bindings):
                    return None                                   # d.update(OTHER) / l.extend(OTHER): OTHER's elements are bound to the bare receiver
                                                                  # (not `list.append(OTHER, x)`: there OTHER is the receiver)
                return "passed as an argument to a call"
            return "called"
        if isinstance(par, ast.Compare):
            return None
        if isinstance(par, (ast.If, ast.While, ast.IfExp)):
            return None if par.test is ref else "returned from a conditional expression"
        if isinstance(par, ast.Assert) or (isinstance(par, ast.UnaryOp) and isinstance(par.op, ast.Not)):
            return None
        if isinstance(par, ast.FormattedValue):
            return None
        if isinstance(par, ast.Starred):
            gp = self._parent_of(par)
            return None if isinstance(gp, (ast.List, ast.Tuple, ast.Set)) else "unpacked into a call"
        if isinstance(par, ast.Dict):
            return None if any(k is None and v is ref for k, v in zip(par.keys, par.values)) else "stored as a dict value"
        if isinstance(par, (ast.Assign, ast.AnnAssign)) and par.value is ref:
            targets = par.targets if isinstance(par, ast.Assign) else [par.target]
            if all(isinstance(t, (ast.Tuple, ast.List)) for t in targets):
                return None                                       # a, b = NAME: unpacking copies the elements out
            return "aliased (bound to another name / attribute)"
        if isinstance(par, ast.BinOp):
            return self._derived_problem(par, depth + 1, False)
        if isinstance(par, ast.Return):
            return "returned"
        if isinstance(par, (ast.Yield, ast.YieldFrom, ast.Await)):
            return "yielded"
        if isinstance(par, (ast.List, ast.Tuple, ast.Set)):
            return "stored inside another container"
        if isinstance(par, ast.keyword):
            return "passed as a keyword argument"
        return f"used in a {type(par).__name__} this scan does not read"

    def _derived_problem(self, node: ast.AST, depth: int, element: bool) -> str | None:
        """`node` was derived from a container (a view, an iterator, a copy, an element): none of those can mutate the original
        (elements are not containers: a container that holds one is refused up front), and a derived container bound to a name
        is policed on that name. Nothing to check here."""
        return None

    # ---- provably immutable values: not policed as possible containers ------------------------------------------------

    _NON_STR_RESULT_METHODS = {"split", "rsplit", "splitlines", "partition", "rpartition"}

    def _name_immutable(self, name: str) -> bool:
        """True iff EVERY binding of the name is provably an immutable value (str / bytes / number / bool / None, or a tuple /
        frozenset of such, recursively). Any other name may be a mutable container that arrived by a call, a subscript, an
        attribute, `setdefault`/`get`/`pop`, a loop over a container of lists ... and its uses are then policed."""
        return self._memoised_bool(("im", name), lambda: self._name_immutable_uncached(name))

    def _memoised_bool(self, key: tuple, compute) -> bool:
        r = self._memoised(key, lambda: None if compute() else "x")
        return r is None

    def _name_immutable_uncached(self, name: str) -> bool:
        bound = self.bindings.get(name)
        if not bound:
            return False
        for b in bound:
            self._step()
            tag = b[0]
            if tag == "expr":
                ok = self._immutable_expr(b[1])
            elif tag in ("iter", "iter_values"):
                ok = self._elements_immutable(b[1])
            elif tag == "iter_keys":
                ok = self._keys_immutable(b[1])
            elif tag == "param":
                ok = self._param_problem(name, *b[1:], check=lambda a: None if self._immutable_expr(a) else "mutable") is None
            else:
                ok = False
            if not ok:
                return False
        return True

    def _immutable_expr(self, node: ast.AST | None, depth: int = 0) -> bool:
        if node is None:
            return True
        self._step()
        if depth > 40:
            return False
        d = depth + 1
        if isinstance(node, ast.Constant):
            return not isinstance(node.value, (bytearray,))
        if isinstance(node, (ast.JoinedStr, ast.Compare)):
            return True
        if isinstance(node, ast.UnaryOp):
            return self._immutable_expr(node.operand, d)
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Mod):
                return self._immutable_expr(node.left, d)
            return self._immutable_expr(node.left, d) and self._immutable_expr(node.right, d)
        if isinstance(node, ast.BoolOp):
            return all(self._immutable_expr(v, d) for v in node.values)
        if isinstance(node, ast.IfExp):
            return self._immutable_expr(node.body, d) and self._immutable_expr(node.orelse, d)
        if isinstance(node, ast.Name):
            return self._name_immutable(node.id)
        if isinstance(node, ast.Tuple):
            return all(self._elements_immutable(e.value, d) if isinstance(e, ast.Starred) else self._immutable_expr(e, d) for e in node.elts)
        if isinstance(node, ast.Subscript):
            return self._immutable_expr(node.value, d)           # an element of a tuple of immutables / a character of a str
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and (node.value.id in ("self", "cls") or node.value.id in self.local_classes):
                cls = self.node_class.get(id(node)) if node.value.id in ("self", "cls") else node.value.id
                value, why = self._class_attr_value(cls, node.attr) if cls else (None, "no class")
                return why is None and self._immutable_expr(value, d)
            return False
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                if f.id in self.func_defs:
                    return self._memoised_bool(("fi", f.id), lambda: self._returns_immutable(f.id))
                if f.id in _NUMERIC_FUNCS or f.id in ("str", "repr", "ascii", "format", "text", "dedent", "cleandoc"):
                    return True
                if f.id in ("tuple", "frozenset") and len(node.args) == 1:
                    return self._elements_immutable(node.args[0], d)
                return False
            if isinstance(f, ast.Attribute):
                if (f.attr in self.func_defs and isinstance(f.value, ast.Name) and (f.value.id in ("self", "cls") or f.value.id in self.local_classes)):
                    return self._memoised_bool(("fi", f.attr), lambda: self._returns_immutable(f.attr))
                if f.attr in _STR_METHODS and f.attr not in self._NON_STR_RESULT_METHODS:
                    return f.attr == "join" or self._immutable_expr(f.value, d)
                if f.attr in ("text", "dedent", "cleandoc"):
                    return True
            return False
        return False

    def _returns_immutable(self, name: str) -> bool:
        for fn in self.func_defs.get(name, []):
            if self._foreign_decorator(fn):
                return False
            rets, todo = [], list(fn.body)
            while todo:
                n = todo.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(n, (ast.Yield, ast.YieldFrom)):
                    return False
                if isinstance(n, ast.Return):
                    rets.append(n.value)
                todo.extend(ast.iter_child_nodes(n))
            if not rets or not all(self._immutable_expr(r) for r in rets):
                return False
        return True

    def _elements_immutable(self, node: ast.AST | None, depth: int = 0) -> bool:
        """Every element a container expression yields is immutable (so iterating it hands out only strings / numbers / ...)."""
        if node is None:
            return True
        self._step()
        if depth > 40:
            return False
        d = depth + 1
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return all(self._elements_immutable(e.value, d) if isinstance(e, ast.Starred) else self._immutable_expr(e, d) for e in node.elts)
        if isinstance(node, ast.Dict):
            return all(self._immutable_expr(e, d) if e is not None else True for e in list(node.keys) + list(node.values))
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self._immutable_expr(node.elt, d)
        if isinstance(node, ast.DictComp):
            return self._immutable_expr(node.key, d) and self._immutable_expr(node.value, d)
        if isinstance(node, ast.Name):
            return self._memoised_bool(("ei", node.id), lambda: self._name_elements_immutable(node.id))
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult, ast.BitOr)):
            return self._elements_immutable(node.left, d) and self._elements_immutable(node.right, d)
        if isinstance(node, (ast.IfExp,)):
            return self._elements_immutable(node.body, d) and self._elements_immutable(node.orelse, d)
        if isinstance(node, ast.BoolOp):
            return all(self._elements_immutable(v, d) for v in node.values)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return self._elements_immutable(node.value, d)
        if isinstance(node, ast.Constant):
            return True                                           # iterating a str yields characters
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and (node.value.id in ("self", "cls") or node.value.id in self.local_classes):
            cls = self.node_class.get(id(node)) if node.value.id in ("self", "cls") else node.value.id
            value, why = self._class_attr_value(cls, node.attr) if cls else (None, "no class")
            return why is None and self._elements_immutable(value, d)
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                if f.id in self.func_defs:
                    return self._memoised_bool(("fe", f.id), lambda: self._returns_elements_immutable(f.id))
                if f.id in ("sorted", "list", "tuple", "set", "frozenset", "reversed", "iter", "enumerate", "zip", "min", "max"):
                    return all(self._elements_immutable(a, d) for a in node.args)
                if f.id == "range":
                    return True
                return False
            if isinstance(f, ast.Attribute):
                if f.attr in ("items", "values", "keys", "copy") and not node.args:
                    return self._elements_immutable(f.value, d)
                if f.attr in _STR_METHODS:
                    return True
            return False
        return False

    def _keys_immutable(self, node: ast.AST) -> bool:
        """The KEYS of a mapping are immutable (its values may be anything): `for k, v in X.items()` binds k to a key."""
        if isinstance(node, ast.Dict):
            return all(self._immutable_expr(k) for k in node.keys if k is not None)
        if isinstance(node, ast.Name):
            def compute() -> bool:
                bound = self.bindings.get(node.id)
                if not bound:
                    return False
                for b in bound:
                    self._step()
                    if b[0] == "elem":
                        continue                                  # `X[k] = v`: v is a value; k is its own "subkey" binding
                    if b[0] == "expr":
                        ok = self._keys_immutable(b[1]) if isinstance(b[1], ast.Dict) else self._elements_immutable(b[1])
                    elif b[0] == "subkey":
                        ok = self._immutable_expr(b[1])
                    elif b[0] == "econt":
                        ok = self._keys_immutable(b[1])
                    else:
                        ok = False
                    if not ok:
                        return False
                return True
            return self._memoised_bool(("ki", node.id), compute)
        return self._elements_immutable(node)

    def _returns_elements_immutable(self, name: str) -> bool:
        for fn in self.func_defs.get(name, []):
            if self._foreign_decorator(fn):
                return False
            rets, todo = [], list(fn.body)
            while todo:
                n = todo.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(n, (ast.Yield, ast.YieldFrom)):
                    return False
                if isinstance(n, ast.Return):
                    rets.append(n.value)
                todo.extend(ast.iter_child_nodes(n))
            if not rets or not all(self._elements_immutable(r) for r in rets):
                return False
        return True

    def _name_elements_immutable(self, name: str) -> bool:
        bound = self.bindings.get(name)
        if not bound:
            return False
        for b in bound:
            self._step()
            tag = b[0]
            if tag == "expr":
                ok = self._elements_immutable(b[1]) or self._immutable_expr(b[1])
            elif tag == "elem" or tag == "subkey":
                ok = self._immutable_expr(b[1])
            elif tag == "econt":
                ok = self._elements_immutable(b[1])
            elif tag == "param":
                ok = self._param_problem(name, *b[1:], check=lambda a: None if self._elements_immutable(a) else "mutable") is None
            else:
                ok = False
            if not ok:
                return False
        return True

    def _clean_name(self, name: str) -> str | None:
        return self._memoised(("n", name), lambda: self._name_problem(name))

    def _name_problem(self, name: str) -> str | None:
        bound = self.bindings.get(name)
        if not bound:
            return f"unresolved_sql_name: {name} is not bound in this module"
        for b in bound:
            self._step()
            p = self._binding_problem(name, b)
            if p:
                return p
        if not self._name_immutable(name):
            return self._container_problem(name)                   # a possible container: every use of it must be a read
        return None

    def _binding_problem(self, name: str, b: tuple) -> str | None:
        tag = b[0]
        if tag in ("expr", "elem", "econt"):
            return self._clean_expr(b[1])
        if tag in ("iter", "star"):
            return self._clean_iter(b[1])
        if tag == "iter_values":
            return self._clean_expr(b[1])
        if tag == "iter_keys":
            return self._clean_keys(b[1])
        if tag == "subkey":
            return self._clean_expr(b[1])
        if tag == "import":
            return f"imported_sql_constant: {name}"
        if tag == "param":
            return self._param_problem(name, *b[1:])
        if tag == "def":
            return f"unresolved_sql_name: {name} is bound to a function or class"
        return f"unresolved_sql_name: {name} is {b[1]}"

    def _clean_keys(self, node: ast.AST) -> str | None:
        """The KEYS of a mapping are clean iff its literal keys and every `X[k] = v` key are; values may be anything (the
        position-aware half of `for k, v in X.items()`)."""
        if isinstance(node, ast.Dict):
            return next((p for p in (self._clean_expr(k) for k in node.keys if k is not None) if p), None)
        if not isinstance(node, ast.Name):
            return self._clean_expr(node)

        def compute() -> str | None:
            bound = self.bindings.get(node.id)
            if not bound:
                return f"unresolved_sql_name: {node.id} is not bound in this module"
            for b in bound:
                self._step()
                if b[0] == "elem":
                    continue                                      # `X[k] = v`: v is a value, k is covered by its "subkey"
                p = self._clean_keys(b[1]) if (b[0] == "expr" and isinstance(b[1], ast.Dict)) else self._binding_problem(node.id, b)
                if p:
                    return p
            return None
        return self._memoised(("k", node.id), compute)

    def _clean_iter(self, node: ast.AST) -> str | None:
        """Elements drawn from `node` (a loop / comprehension / unpacking source) are clean iff the container is."""
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr in ("items", "values", "keys", "copy") and not node.args:
                return self._clean_expr(f.value)
            if isinstance(f, ast.Name) and f.id == "range":
                return None
            if isinstance(f, ast.Name) and f.id in _ITER_WRAPPERS:
                return next((p for p in (self._clean_iter(a) for a in node.args) if p), None)
        return self._clean_expr(node)

    def _param_problem(self, name: str, func: ast.AST, idx: int | None, pname: str, default: ast.AST | None,
                       check=None) -> str | None:
        """A parameter is clean iff every call site of its function in THIS file passes a clean value (a missing argument
        falls back to the default, which must itself be clean); no call site, an aliased function, or a *args/**kwargs call
        => not clean."""
        method = self._is_method(func)
        if (method and idx == 0) or id(func) in self._entry_funcs:
            return None                                           # self / cls, or a helper's own parameter
        if func.name in self.value_refs:
            return f"unresolved_sql_parameter: {name} of {func.name}() -- the function is used as a value (alias / partial / map)"
        if self._foreign_decorator(func):
            return f"unresolved_sql_parameter: {name} of {func.name}() -- the function is decorated (the decorator can rewrite its arguments)"
        sites = self.calls_by_callee.get(func.name)
        if not sites:
            return f"unresolved_sql_parameter: {name} of {func.name}() has no call site in this file"
        for call in sites:
            if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
                return f"unresolved_sql_arguments: {func.name}() is called with *args / **kwargs"
            arg = None
            if idx is not None:
                pos = idx - self._arg_shift(func, call)
                if 0 <= pos < len(call.args):
                    arg = call.args[pos]
            if arg is None:
                arg = next((k.value for k in call.keywords if k.arg == pname), None)
            if arg is None:
                arg = default
                if arg is None:
                    return f"unresolved_sql_parameter: {name} of {func.name}() is not passed at a call site and has no default"
            p = (check or self._clean_expr)(arg)
            if p:
                return p
        return None

    def _clean_attribute(self, node: ast.Attribute) -> str | None:
        unp = ast.unparse(node)[:60]
        if node.attr.startswith("__") and node.attr.endswith("__"):
            return f"sql_from_dunder_attribute: {unp}"
        root = _root_name(node)
        if root in self.imported:
            return f"imported_sql_constant: {unp}"
        base = node.value
        cls = None
        if isinstance(base, ast.Name):
            if base.id in ("self", "cls"):
                cls = self.node_class.get(id(node))
            elif base.id in self.local_classes:
                cls = base.id
        if cls is None:
            return f"unresolved_sql_attribute: {unp} is not self. / cls. / a class of this file"
        value, why = self._class_attr_value(cls, node.attr)
        if why:
            return f"unresolved_sql_attribute: {unp} -- {why}"
        p = self._memoised(("a", cls, node.attr), lambda: self._clean_expr(value))
        if p is None and not self._immutable_expr(value):
            p = self._container_problem(node.attr)
        return p

    def _class_attr_value(self, cls: str, attr: str) -> tuple[ast.AST | None, str | None]:
        """The value of `cls.attr` when it is provably THE value: an unannotated `attr = <expr>` assigned exactly once, at the top
        level of the class body, of a plain class (undecorated, no bases but `object`, no metaclass, no local subclass, never
        instantiated with arguments, its name never rebound), in a file with no `__dict__` / attribute-hook (`__setattr__`,
        `__getattribute__`) use and no 3-argument `type(...)` call, with no instance assignment `self.attr = ...`. Anything that
        could override it -- a dataclass / NamedTuple field default, a subclass override, an `if`/`try` or `+=` rebinding,
        `self.__dict__[...]`, a constructor argument, `A = type('A', (), {...})`, `A = imported` -- is not provable."""
        info = self._class_info(cls)
        if info[0]:
            return None, info[0]
        _, tops, stores = info
        if self.attr_bindings.get(attr):
            return None, f"{attr} is also assigned through an attribute (self.{attr} = ... / obj.{attr} = ...)"
        top, store = tops.get(attr, []), stores.get(attr, [])
        if len(top) != 1 or len(store) != 1:
            return None, f"{attr} is not an unannotated top-level `{attr} = ...` assigned exactly once in the body of class {cls}"
        return top[0].value, None

    def _class_info(self, cls: str) -> tuple:
        """(reason | None, top-level plain assignments by name, every binding by name) of a class, computed ONCE per class: the
        class body is walked a single time (every node charged to the work cap) and every per-attribute lookup is a dict hit."""
        return self._cached(("ci", cls), lambda: self._class_info_uncached(cls))

    def _cached(self, key: tuple, compute):
        if key not in self._info_cache:
            self._info_cache[key] = compute()
        return self._info_cache[key]

    def _class_info_uncached(self, cls: str) -> tuple:
        nodes = self.class_nodes.get(cls, [])
        none = ({}, {})
        if len(nodes) != 1:
            return (f"class {cls} is not defined exactly once in this file", *none)
        cn = nodes[0]
        if len(self.bindings.get(cls, [])) != 1 or any(b[0] != "def" for b in self.bindings.get(cls, [])):
            return (f"the name {cls} is rebound in this file (`{cls} = ...`, an import, a parameter, a loop variable): it may not be this class", *none)
        if cn.decorator_list:
            return (f"class {cls} is decorated (a dataclass-style decorator can override a class attribute)", *none)
        if cn.keywords or any(not (isinstance(b, ast.Name) and b.id == "object") for b in cn.bases):
            return (f"class {cls} has base classes / a metaclass (NamedTuple, Enum, dataclass bases, parents)", *none)
        if cls in self.base_names:
            return (f"class {cls} has a subclass in this file that can override its attributes", *none)
        if self.uses_dunder_dict:
            return ("this file uses __dict__ / an attribute hook (__setattr__, __getattribute__, ...), which can rebind a class or instance attribute", *none)
        if self.uses_type_call:
            return ("this file calls type(name, bases, namespace), which can build a subclass or a replacement class", *none)
        for call in self.calls_by_callee.get(cls, []):
            self._step()
            if call.args or call.keywords:
                return (f"class {cls} is instantiated with arguments", *none)
        for fn in cn.body:
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._step()
                if fn.name in ("__getattribute__", "__setattr__", "__delattr__", "__init_subclass__", "__set_name__"):
                    return (f"class {cls} defines {fn.name}, which can change what an attribute lookup returns", *none)
                if self._is_method(fn) and not self._is_classmethod(fn) and (cls, fn.name) in self.explicit_self_calls:
                    return (f"{cls}.{fn.name}() is called through the class with an explicit self (any object can stand in)", *none)
        tops: dict[str, list[ast.Assign]] = {}
        stores: dict[str, list[ast.AST]] = {}
        for st in cn.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                tops.setdefault(st.targets[0].id, []).append(st)
        todo: list[ast.AST] = list(cn.body)
        while todo:
            n = todo.pop()
            self._step()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                stores.setdefault(n.name, []).append(n)
                continue
            if isinstance(n, ast.Lambda):
                continue
            if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                stores.setdefault(n.id, []).append(n)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    stores.setdefault(a.asname or a.name.split(".")[0], []).append(n)
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                for name in n.names:
                    stores.setdefault(name, []).append(n)
            todo.extend(ast.iter_child_nodes(n))
        return (None, tops, stores)

    def _clean_call(self, node: ast.Call) -> str | None:
        f = node.func
        unp = ast.unparse(node)[:60]
        if _is_sql_composition(f):
            return _SQL_COMPOSITION_REASON
        # a function defined in this file: clean iff everything it returns is (its parameters are judged at their call sites)
        local = None
        if isinstance(f, ast.Name) and f.id in self.func_defs:
            local = f.id
            if any(b[0] != "def" for b in self.bindings.get(f.id, [])):
                return f"sql_from_call_result: {unp} (the name is also bound to something else)"
        elif (isinstance(f, ast.Attribute) and f.attr in self.func_defs and isinstance(f.value, ast.Name)
              and (f.value.id in ("self", "cls") or f.value.id in self.local_classes)):
            local = f.attr
        if local is not None:
            if any(self._foreign_decorator(fn) for fn in self.func_defs.get(local, [])):
                return f"sql_from_call_result: {unp} (the function is decorated: the decorator can rewrite its result)"
            return self._memoised(("f", local), lambda: self._returns_problem(local))
        if isinstance(f, ast.Attribute) and (f.attr in _STR_METHODS or f.attr in _CONTAINER_READ_METHODS):
            parts = [f.value, *node.args, *(k.value for k in node.keywords)]
            return next((p for p in (self._clean_expr(x) for x in parts) if p), None)
        text_wrapper = (isinstance(f, ast.Name) and f.id in _TEXT_FUNCS) or (
            isinstance(f, ast.Attribute) and f.attr in ("text", "dedent", "cleandoc") and _root_name(f) in self.imported)
        if isinstance(f, ast.Name) and f.id in _NUMERIC_FUNCS:
            return None                                           # len(x) / int(x) / ...: a number, no SQL text
        if text_wrapper:                                          # str(x) / dedent(x) / text(x): carries its arguments' text
            return next((p for p in (self._clean_expr(x) for x in [*node.args, *(k.value for k in node.keywords)]) if p), None)
        return f"sql_from_call_result: {unp}"

    def _returns_problem(self, name: str) -> str | None:
        for fn in self.func_defs.get(name, []):
            rets: list[ast.AST | None] = []
            todo = list(fn.body)
            while todo:
                n = todo.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(n, (ast.Yield, ast.YieldFrom)):
                    return f"sql_from_call_result: {name}() is a generator"
                if isinstance(n, ast.Return):
                    rets.append(n.value)
                todo.extend(ast.iter_child_nodes(n))
            if not rets:
                return f"sql_from_call_result: {name}() returns nothing"
            for r in rets:
                self._step()
                p = self._clean_expr(r)
                if p:
                    return p
        return None

    # ---- literal scan -----------------------------------------------------------------------------------------------

    def _walk(self, node: ast.AST, fn_stack: list[ast.AST]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.defined.add(node.name)
            fn_stack = fn_stack + [node]
        if isinstance(node, ast.Call):
            self.calls.append(node)
            joined = _render_sql_node(node)                    # '' .join([...]) of a list literal; children are walked too
            if joined is not None:
                self._scan_text(joined, fn_stack)
            if isinstance(node.func, ast.Attribute) and node.func.attr in self._STR_EVAL_METHODS:
                evaluated = self._eval_const(node, 0)           # 'DELETE FROM xx'.replace('xx', 'hidden'): the text that runs
                if evaluated is not None and evaluated != joined:
                    self._scan_text(evaluated, fn_stack)
        if isinstance(node, ast.Expr) and _is_str(node.value):
            return                                              # docstring / bare prose string: not SQL
        if isinstance(node, ast.Constant) and isinstance(node.value, (bytes, bytearray)):
            self._scan_bytes(bytes(node.value))
        if isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            text = _render_sql_node(node)
            if text is not None:
                self._scan_text(text, fn_stack)
                if isinstance(node, ast.JoinedStr) or (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
                    return                                      # its pieces are already part of `text`
        for child in ast.iter_child_nodes(node):
            self._walk(child, fn_stack)

    def _scan_bytes(self, data: bytes) -> None:
        """SQL held as bytes is not analysed: a bytes literal that carries a write form is reported, not read."""
        if len(data) > MAX_SQL_LITERAL_CHARS:
            self.unresolved.append(f"sql_literal_too_long: bytes literal of {len(data)} bytes (limit {MAX_SQL_LITERAL_CHARS})")
        elif _BYTES_WRITE_FORM.search(data.decode("latin-1")):
            self.unresolved.append("bytes_sql_literal: a write form in a bytes literal is not analysed")

    # ---- execute()-argument and exotic-form checks -------------------------------------------------------------------

    def _check_execute_call(self, call: ast.Call, file_sql_names: set[str]) -> None:
        f = call.func
        idx = None
        name = None
        if isinstance(f, ast.Attribute):
            name = f.attr
            if f.attr in _SQL_SECOND_ARG_FUNCS:
                idx = 1
            elif f.attr in _EXECUTE_ATTRS:
                idx = 0
            if idx is not None and f.attr in ("copy", "run") and _root_name(f) in self.imported:
                return                                            # copy.copy(x) / shutil.copy(a, b) / subprocess.run([...])
        elif isinstance(f, ast.Name):
            name = self.exec_aliases.get(f.id, f.id)
            if name in _SQL_SECOND_ARG_FUNCS:
                idx = 1
        if idx is None:
            return
        if any(isinstance(a, ast.Starred) for a in call.args[:idx + 1]) or any(k.arg is None for k in call.keywords):
            self.unresolved.append(f"unresolved_sql_arguments: {name}() is called with *args / **kwargs")
            return
        nodes = []
        if len(call.args) > idx:
            nodes.append(call.args[idx])
        nodes += [k.value for k in call.keywords if k.arg in _SQL_KEYWORDS]
        if not nodes:
            if (call.args or call.keywords) and name not in ("copy", "fetchmany", "run"):
                self.unresolved.append(f"unresolved_sql_arguments: no SQL argument of {name}() could be identified")
            return
        for arg in nodes:
            if _reads_a_file(arg) or (isinstance(arg, ast.Name) and arg.id in file_sql_names):
                self.unresolved.append("write_form_not_analysed: SQL read from a file feeds execute()")
                return
            rendered = _render_sql_node(arg)
            if rendered is not None and _TXN_CONTROL.match(rendered):
                continue                                          # SAVEPOINT / RELEASE / ROLLBACK TO <identifier>: writes no table
            try:
                problem = self._clean_expr(arg)
            except _Budget as exc:
                problem = f"resolver_work_cap: {exc}"
            if problem:
                self.unresolved.append(problem)
                return

    def _tripwire_calls(self, tree: ast.Module) -> None:
        """Forms that name tables only at runtime or outside this file: psycopg sql composition, SQL read from a file, SQL
        that is not provably this file's own literals reaching execute(), copy APIs with no SQL text, exec/eval, runtime
        rebinding."""
        file_sql_names: set[str] = set()
        parents: dict[int, ast.AST] | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _reads_a_file(node.value):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        file_sql_names.add(t.id)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and _SQL_FILE_LITERAL.match(node.value):
                self.unresolved.append(f"write_form_not_analysed: sql file reference {node.value.strip()[:60]!r}")
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] in ("importlib", "builtins", "__main__") and node.level == 0:
                    self.unresolved.append("dynamic_dispatch: importlib / builtins / __main__ reach modules and namespaces by name")
                if any(a.name == "*" for a in node.names):
                    self.unresolved.append(f"dynamic_binding: from {'.' * node.level}{node.module or ''} import *")
                for a in node.names:
                    if a.name in _DB_EXEC_NAMES:
                        self.unresolved.append(f"execute_function_imported: {a.name} is imported, its call shape is not analysed")
            elif isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)) and (
                    _is_globals_call(node.value) or _mentions_modules(node.value)):
                self.unresolved.append("runtime_rebinding: item assignment on globals()/locals()/vars()/sys.modules")
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)) and _mentions_modules(node.value):
                self.unresolved.append("runtime_rebinding: attribute assignment on sys.modules[...]")
            elif isinstance(node, ast.Attribute) and node.attr == "modules" and isinstance(node.value, ast.Name) and node.value.id == "sys":
                self.unresolved.append("dynamic_dispatch: sys.modules reaches another module's namespace")
            elif isinstance(node, ast.Name) and node.id == "__builtins__":
                self.unresolved.append("dynamic_dispatch: __builtins__ reaches the builtin namespace by name")
            elif isinstance(node, ast.Attribute) and node.attr in ("get_objects", "get_referrers", "get_referents"):
                self.unresolved.append(f"dynamic_dispatch: .{node.attr}() finds live objects without naming them")
            elif isinstance(node, ast.Attribute) and node.attr in ("f_globals", "f_locals", "__getattribute__"):
                self.unresolved.append(f"dynamic_dispatch: .{node.attr} reaches a namespace by name")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and id(node) not in self.callee_ids \
                    and node.id in ("globals", "locals", "vars", "getattr", "__import__", "setattr"):
                self.unresolved.append(f"dynamic_dispatch: {node.id} is aliased / passed on as a value")
            elif isinstance(node, ast.Import) and any(a.name.split(".")[0] in ("importlib", "builtins", "__main__") for a in node.names):
                self.unresolved.append("dynamic_dispatch: importlib / builtins / __main__ reach modules and namespaces by name")
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and id(node) not in self.callee_ids and (
                    node.attr in _EXECUTE_ATTRS or node.attr in _SQL_SECOND_ARG_FUNCS or node.attr in _COPY_API_ATTRS):
                if not (node.attr in ("copy", "run") and _root_name(node) in self.imported):
                    self.unresolved.append(f"execute_method_used_as_value: .{node.attr} is aliased / passed on, its calls are not analysed")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and id(node) not in self.callee_ids and (
                    node.id in _SQL_SECOND_ARG_FUNCS or node.id in self.exec_aliases):
                self.unresolved.append(f"execute_method_used_as_value: {node.id} is aliased / passed on, its calls are not analysed")
            elif isinstance(node, (ast.Call,)) and _is_globals_call(node):
                parents = parents if parents is not None else _parent_map(tree)
                par = parents.get(id(node))
                ok = (isinstance(par, ast.Subscript) and isinstance(par.ctx, ast.Load)) or isinstance(par, (ast.keyword, ast.Starred, ast.Compare)) \
                    or (isinstance(par, ast.Attribute) and par.attr in ("get", "keys", "values", "items", "copy", "__contains__", "__getitem__")) \
                    or (isinstance(par, ast.Dict))
                if not ok:
                    self.unresolved.append("runtime_rebinding: the globals()/locals()/vars() dict is aliased or passed on")
        for call in self.calls:
            f = call.func
            if _is_sql_composition(f):
                self.unresolved.append(_SQL_COMPOSITION_REASON)
            if isinstance(f, ast.Name) and f.id in _DYNAMIC_CODE_FUNCS:
                self.unresolved.append(f"dynamic_code: {f.id}() builds code at runtime")
            if isinstance(f, ast.Name) and f.id == "setattr":
                self.unresolved.append("runtime_rebinding: setattr() can rebind a SQL constant or a method at runtime")
            if isinstance(f, ast.Attribute) and f.attr in _COPY_API_ATTRS:
                self.unresolved.append(f"copy_api_without_sql_text: {f.attr}() writes a table with no SQL text to scan")
            # getattr(x, name): an attribute chosen at runtime. A 3-argument read of a literal attribute (a default is given) is
            # a plain read; a non-literal name, a literal that names a local def/class or a SQL-running method, or any getattr
            # result that is called straight away is a dispatch by string
            if isinstance(f, ast.Name) and f.id == "getattr" and len(call.args) >= 2:
                a = call.args[1]
                par = self._parent_of(call)
                held = par.targets[0].id if (isinstance(par, ast.Assign) and len(par.targets) == 1
                                             and isinstance(par.targets[0], ast.Name) and par.value is call) else None
                runtime_name_read = (not _is_str(a) and len(call.args) >= 3 and held is not None
                                     and held not in self.calls_by_callee)
                if (id(call) in self.callee_ids or (not _is_str(a) and not runtime_name_read)
                        or (_is_str(a) and (a.value in self.func_defs or a.value in self.local_classes
                                            or a.value in _EXECUTE_ATTRS | _COPY_API_ATTRS | _SQL_SECOND_ARG_FUNCS))):
                    self.unresolved.append("dynamic_dispatch: getattr(...) picks an attribute / method by name at runtime")
            if isinstance(f, ast.Name) and f.id in ("__import__", "import_module"):
                self.unresolved.append("dynamic_dispatch: __import__() loads a module chosen at runtime")
            if isinstance(f, ast.Attribute) and f.attr in ("import_module", "methodcaller", "attrgetter", "__getattribute__", "_getframe", "currentframe"):
                self.unresolved.append(f"dynamic_attribute_call: .{f.attr}() reaches an attribute / module / frame by name")
            if _is_globals_call(call):
                self.unresolved.append("dynamic_dispatch: globals()/locals()/vars() reach module attributes (containers, functions, classes) by name")
                par = self._parent_of(call)
                gp = self._parent_of(par) if par is not None else None
                if (isinstance(par, ast.Subscript) and isinstance(par.ctx, ast.Load) and id(par) in self.callee_ids) or (
                        isinstance(par, ast.Attribute) and par.attr == "get" and isinstance(gp, ast.Call) and id(gp) in self.callee_ids):
                    self.unresolved.append("dynamic_dispatch: a function is looked up by name in globals()/locals()/vars() and called")
            self._check_execute_call(call, file_sql_names)

    # ---- statement text ---------------------------------------------------------------------------------------------

    def _scan_text(self, text: str, fn_stack: list[ast.AST]) -> None:
        if len(text) > MAX_SQL_LITERAL_CHARS:
            self.unresolved.append(f"sql_literal_too_long: {len(text)} characters (limit {MAX_SQL_LITERAL_CHARS}); not scanned")
            return
        # SQL comments are whitespace to the server (`INSERT /* c */ INTO a`, `TRUNCATE a -- c\n, b`). Three readings of the
        # text are scanned and UNIONED -- every table and every not-scanned reason of any of them -- so that nothing can hide a
        # verb: the raw text; the quote-aware comment-free text (a marker inside '...' / $$...$$ is text); and the text with
        # every marker stripped wherever it sits (a statement whose keywords are split by a comment INSIDE a string or a dollar
        # body, `DO $$ BEGIN DELETE /*x*/ FROM t; END $$`). A statement whose comment sits inside its verb may therefore be
        # over-reported, never under-reported.
        variants = [text]
        if "/*" in text or "--" in text:
            for quote_aware in (True, False):
                v = _strip_sql_comments(text, quote_aware)
                if v not in variants:
                    variants.append(v)
        for i, v in enumerate(variants):
            self._scan_variant(v, fn_stack, raw=(i == 0 and len(variants) > 1))
            if _PH_OPEN in v:
                inlined = self._inline_consts(v)
                if inlined != v and len(inlined) <= MAX_SQL_LITERAL_CHARS:
                    # the same statement with every placeholder that is provably a constant written out: `V = 'DEL'; f'{V}ETE
                    # FROM t'`, `'%s %s t' % (V, F)`, `'DELETE FROM'.strip() + ' t'` are read as the statement they run
                    self._scan_variant(inlined, fn_stack)

    def _inline_consts(self, text: str) -> str:
        cache: dict[str, str | None] = {}

        def sub(m: re.Match) -> str:
            expr = m.group(1)
            if expr not in cache:
                try:
                    tree = ast.parse(expr.strip(), mode="eval")
                    cache[expr] = self._eval_const(tree.body, 0)
                except (SyntaxError, ValueError, RecursionError):
                    cache[expr] = None
            value = cache[expr]
            return _clean_literal(value) if value is not None else m.group(0)
        return _PLACEHOLDER_CAPTURE.sub(sub, text)

    _STR_EVAL_METHODS = {"strip", "lstrip", "rstrip", "lower", "upper", "title", "capitalize", "casefold", "swapcase", "replace",
                         "format", "removeprefix", "removesuffix", "zfill", "ljust", "rjust", "center", "expandtabs", "join"}

    def _eval_const(self, node: ast.AST, depth: int) -> str | None:
        """The string an expression of this file's own literals evaluates to (str methods run on literals only, no import, no
        call of anything else), else None. Used only to READ the statement a template builds."""
        if depth > 12:
            return None
        if _is_str(node):
            return node.value
        if isinstance(node, ast.Name):
            return self._resolve_const(node.id)
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if _is_str(v):
                    parts.append(v.value)
                elif isinstance(v, ast.FormattedValue) and v.format_spec is None and v.conversion == -1:
                    r = self._eval_const(v.value, depth + 1)
                    if r is None:
                        return None
                    parts.append(r)
                else:
                    return None
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = self._eval_const(node.left, depth + 1), self._eval_const(node.right, depth + 1)
            return left + right if left is not None and right is not None else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and _is_str(node.left):
            rhs = node.right
            items = list(rhs.elts) if isinstance(rhs, ast.Tuple) else [rhs]
            vals = [self._eval_const(i, depth + 1) for i in items]
            if any(v is None for v in vals):
                return None
            try:
                return node.left.value % tuple(vals)
            except (TypeError, ValueError):
                return None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in self._STR_EVAL_METHODS:
            recv = self._eval_const(node.func.value, depth + 1)
            if recv is None or any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
                return None
            try:
                if node.func.attr == "join":
                    seq = node.args[0] if len(node.args) == 1 else None
                    if not isinstance(seq, (ast.List, ast.Tuple)):
                        return None
                    vals = [self._eval_const(e, depth + 1) for e in seq.elts]
                    return None if any(v is None for v in vals) else recv.join(vals)
                def arg_value(a: ast.AST):
                    v = self._eval_const(a, depth + 1)
                    return v if v is not None else (a.value if isinstance(a, ast.Constant) and isinstance(a.value, (int, str)) else None)
                args = [arg_value(a) for a in node.args]
                kwargs = {k.arg: arg_value(k.value) for k in node.keywords}
                if any(a is None for a in args) or any(v is None for v in kwargs.values()):
                    return None
                out = getattr(str, node.func.attr)(recv, *args, **kwargs)
                return out if isinstance(out, str) and len(out) <= MAX_SQL_LITERAL_CHARS else None
            except (TypeError, ValueError, KeyError, IndexError):
                return None
        return None

    def _scan_variant(self, text: str, fn_stack: list[ast.AST], raw: bool = False) -> None:
        """One pass over `text`. `raw` is the pass over the text WITH its comments: a verb whose very next token is a comment
        opener (`INSERT INTO /* c */ a`, `TRUNCATE /* c */ a`) is deferred to the comment-free pass instead of being reported
        unparseable twice; everything else found in either pass is kept."""
        for label, hit in _TRIPWIRES:
            if hit(text):
                self.unresolved.append(f"write_form_not_analysed: {label}")
        for m in _STMT_START_PH.finditer(text):
            ph, rest = m.group("ph"), m.group("rest")
            const = self._resolve_const(ph[1:-1]) if ph.startswith(_PH_OPEN) else None
            second = _SECOND_PLACEHOLDER.match(rest)
            second_const = self._resolve_const(second.group("expr")) if second else None
            # the verb of the statement is a name: its value is a bare verb (`V = 'DELETE'; f'{V} FROM a'`), or SQL words
            # follow the placeholder, or a SQL keyword held in a second name follows (`f'{V} {F} a'`). A name that holds a
            # whole statement (`P + ' ' + Q`) and prose (`f'{a} {b} house'`) are not a hidden verb.
            if (const is not None and _BARE_VERB.match(const)) or (
                    (const is None or _BARE_VERB.match(const)) and (
                        _SQL_WORD_IN_REST.search(_PLACEHOLDER_BODY.sub(" ", rest)) or (second_const is not None and _SQL_WORD_ONLY.match(second_const)))):
                self.unresolved.append("unparseable_write_target: a statement starts with a name / runtime value (its verb is not in this text)")
        verb_starts: set[int] = set()
        matched_spans: list[tuple[int, int]] = []
        for verb, rx in _WRITE_VERBS:
            for m in rx.finditer(text):
                verb_starts.add(m.start())
                matched_spans.append(m.span("t"))
                self._add_target(m.group("t"), verb, fn_stack)
        for head in _TRUNCATE_HEAD.finditer(text):
            self._scan_truncate(text, head, matched_spans, fn_stack, raw)
        matched_starts = {a for a, _ in matched_spans}            # a set: a list scan per verb is quadratic on hostile input
        for m in _VERB_ANY.finditer(text):
            if m.start("rest") not in matched_starts and m.group("rest").lower().strip('"') not in _SQL_WORDS:
                if raw and m.group("rest").startswith(("/*", "--")):
                    continue
                self.unresolved.append(f"unparseable_write_target: {m.group(0)[:60]!r}")
        self._scan_unmatched_verbs(text, verb_starts, raw)

    def _scan_truncate(self, text: str, head: re.Match, matched_spans: list[tuple[int, int]], fn_stack: list[ast.AST],
                       raw: bool = False) -> None:
        """TRUNCATE [TABLE] [ONLY] a [*] [, [ONLY] b [*] ...] [RESTART|CONTINUE IDENTITY] [CASCADE|RESTRICT]: every table in the
        comma list is written; a list item that is not a recognisable name makes the statement unresolved."""
        pos = head.end()
        while True:
            m = _TRUNCATE_ITEM.match(text, pos)
            if m is None or m.group("t").lower().strip('"') in _SQL_WORDS:
                if raw and text.startswith(("/*", "--"), pos):
                    return
                self.unresolved.append(f"unparseable_write_target: {text[head.start():head.start() + 60]!r}")
                return
            matched_spans.append(m.span("t"))
            self._add_target(m.group("t"), "TRUNCATE", fn_stack)
            pos = m.end()
            if text[pos:pos + 1] != ",":
                return
            pos += 1
            while pos < len(text) and text[pos].isspace():
                pos += 1

    def _scan_unmatched_verbs(self, text: str, verb_starts: set[int], raw: bool = False) -> None:
        """A write verb the verb regexes did not resolve to a target: a literal that ends in the verb (the table is joined on
        at runtime), an UPDATE / COPY followed by a name or placeholder with no SET / FROM|TO behind it (the tail is joined
        on at runtime), an UPDATE ... SET / COPY ... FROM whose target is not a recognisable name."""
        if _TRAILING_STRONG_VERB.search(text):
            self.unresolved.append("trailing_write_verb_without_target: a literal ends in a write verb (the table is joined on at runtime)")
        m = _TRAILING_WEAK_VERB.search(text)
        if m:
            prev = text[max(0, m.start() - 30):m.start()].split()[-1:]
            if not (prev and prev[0].lower() in _NOT_A_STATEMENT_UPDATE_PREV):
                self.unresolved.append("trailing_write_verb_without_target: a literal ends in a write verb (the table is joined on at runtime)")
        last_set = max((x.start() for x in _SET_WORD.finditer(text)), default=-1)
        last_from = max((x.start() for x in _FROM_WORD.finditer(text)), default=-1)
        last_to = max((x.start() for x in _TO_WORD.finditer(text)), default=-1)
        for m in _UPDATE_WORD.finditer(text):
            prev = text[max(0, m.start() - 30):m.start()].split()[-1:]
            if m.start() in verb_starts or (prev and prev[0].lower() in _NOT_A_STATEMENT_UPDATE_PREV):
                continue
            if raw and _COMMENT_NEAR.search(text, m.end(), m.end() + 200):
                continue                                          # a comment splits the statement: the comment-free pass reads it
            tail = _NAME_AFTER_VERB.match(text, m.end())
            # SET behind it but the target is not a name; or no SET at all and either a placeholder follows the verb or the
            # text ends right after a name (the tail is runtime). A Title-case "Update x ..." is prose
            if last_set > m.end() or (tail and (tail.group("n") == _PH_OPEN or (m.group() in ("UPDATE", "update")
                                                                                and _UNFINISHED_TAIL.match(text, m.end())))):
                self.unresolved.append(f"unparseable_write_target: {text[m.start():m.start() + 60]!r}")
        for m in _COPY_WORD.finditer(text):
            if m.start() in verb_starts:
                continue
            if text[m.end():m.end() + 200].lstrip()[:1] == "(":
                continue                                        # COPY (SELECT ...) TO: an export, a read
            if raw and _COMMENT_NEAR.search(text, m.end(), m.end() + 200):
                continue
            tail = _NAME_AFTER_VERB.match(text, m.end())
            if last_from > m.end() or (tail and last_to <= m.end() and (tail.group("n") == _PH_OPEN or (
                    m.group() == "COPY" and _UNFINISHED_TAIL.match(text, m.end())))):
                self.unresolved.append(f"unparseable_write_target: {text[m.start():m.start() + 60]!r}")

    def _add_target(self, token: str, verb: str, fn_stack: list[ast.AST]) -> None:
        if verb != "TRUNCATE" and token.lower().strip('"') in _SQL_WORDS:
            return
        parts = re.findall(rf"{_NAME_PART}", token)
        resolved = []
        for part in parts:
            if part.startswith(_PH_OPEN):
                expr = part[1:-1]
                value = self._resolve_const(expr)
                if value is None:
                    fn = fn_stack[-1] if fn_stack else None
                    params = [a.arg for a in fn.args.args] if fn is not None else []
                    if fn is not None and expr in params and len(parts) == 1:
                        idx = params.index(expr)
                        if self._is_method(fn):
                            if idx == 0:
                                self.unresolved.append(f"unresolved_table_expression: {expr}")
                                return
                            idx -= 1
                            self.method_param_funcs.add(fn.name)
                            if self._is_classmethod(fn):
                                self.classmethod_funcs.add(fn.name)
                        self.param_funcs.setdefault(fn.name, []).append((expr, idx))
                        return
                    self.unresolved.append(f"unresolved_table_expression: {expr}")
                    return
                resolved.append(value)
            elif part.startswith('"'):
                if not _PLAIN_QUOTED.fullmatch(part):             # "a.b", "Foo", "my table": quoted names keep case and dots
                    self.unresolved.append(f"unresolved_table_expression: {token[:60]!r} (a quoted name that is not a plain lowercase identifier)")
                    return
                resolved.append(part.strip('"'))
            else:
                resolved.append(part)
        name = ".".join(resolved)
        if not re.fullmatch(r"[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?", name):
            self.unresolved.append(f"unresolved_table_expression: {token[:60]!r}")
            return
        self.tables.add(_norm_written_table(name))

    def resolve_param_calls(self, helper_params: Mapping[str, Sequence[tuple[str, int]]] | None = None) -> None:
        """Fill the tables of parametric functions from their call sites; a parametric function nothing calls, or one that is
        aliased / passed on as a value, is unresolved."""
        merged: dict[str, list[tuple[str, int]]] = {k: list(v) for k, v in (helper_params or {}).items()}
        for k, v in self.param_funcs.items():
            merged.setdefault(k, []).extend(v)
        called: set[str] = set()
        for fname in merged:
            if fname in self.value_refs:
                self.unresolved.append(f"unresolved_table_argument: {fname}() is used as a value (alias / partial / map)")
        for call in self.calls:
            fname = call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None
            if fname not in merged:
                continue
            called.add(fname)
            for pname, idx in merged[fname]:
                if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
                    self.unresolved.append(f"unresolved_table_argument: {fname}(*args / **kwargs)")
                    continue
                if (fname in self.method_param_funcs and fname not in self.classmethod_funcs and isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Name) and call.func.value.id in self.local_classes):
                    idx += 1                                      # Class.method(instance, ...): the instance is an argument
                arg = call.args[idx] if idx < len(call.args) else next((k.value for k in call.keywords if k.arg == pname), None)
                value = None
                if arg is not None:
                    value = _string_const_value(arg) or (self._resolve_const(ast.unparse(arg)) if isinstance(arg, ast.Name) else None)
                if value is None or not re.fullmatch(r"[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?", value):
                    self.unresolved.append(f"unresolved_table_argument: {fname}({pname}=...)")
                else:
                    self.tables.add(_norm_written_table(value))
        for k in self.param_funcs:
            if k not in called:
                self.unresolved.append(f"parametric_table_helper_never_called_with_a_literal: {k}")


def _parse_python(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError, RecursionError, MemoryError):
        return None


def helper_write_effects(repo: Path) -> dict[str, dict]:
    """For each function in the idempotency helper modules: the tables it writes, its table-parameter positions, or why
    it cannot be resolved. A name defined in two helper modules with different effects is marked unresolved."""
    out: dict[str, dict] = {}
    for rel in WRITE_SCAN_HELPER_MODULES:
        tree = _parse_python(repo / rel)
        if tree is None:
            continue
        for fn in tree.body:
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            try:
                sc = _WriteScan(ast.Module(body=[fn], type_ignores=[]), const_tree=tree)
            except RecursionError:
                out[fn.name] = {"tables": set(), "params": [], "unresolved": f"helper_too_deeply_nested: {fn.name}"}
                continue
            entry = {"tables": set(sc.tables), "params": list(sc.param_funcs.get(fn.name, [])),
                     "unresolved": sc.unresolved[0] if sc.unresolved else None}
            if not (entry["tables"] or entry["params"] or entry["unresolved"]):
                continue
            if fn.name in out and out[fn.name] != entry:
                entry = {"tables": set(), "params": [], "unresolved": f"helper_defined_twice_with_different_effects: {fn.name}"}
            out[fn.name] = entry
    return out


def _is_source_paths(node: ast.AST) -> bool:
    """`source_paths` as a bare name or as an attribute (`cls.source_paths`, `self.source_paths`)."""
    return (isinstance(node, ast.Name) and node.id == "source_paths") or (isinstance(node, ast.Attribute) and node.attr == "source_paths")


_SOURCE_PATHS_READERS = {"len", "list", "tuple", "sorted", "set", "frozenset", "iter", "enumerate"}


def _contains_source_paths(target: ast.AST) -> bool:
    if _is_source_paths(target):
        return True
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_contains_source_paths(e) for e in target.elts)
    if isinstance(target, ast.Starred):
        return _contains_source_paths(target.value)
    return False


def _source_paths_literal(tree: ast.Module) -> tuple[list[str], str | None]:
    """The string items of a `source_paths = [...]` (or tuple) assignment; nothing else is evaluated. The second value is a
    reason when an assignment is not a plain list/tuple of string literals, or when the list is touched in any way other than
    being read for its length / iterated: a mutation (`.append`, `+=`, item assignment, setattr, walrus, del, tuple-unpack
    assignment, getattr(..., 'source_paths')) or an alias (`x = source_paths`, `list.append(source_paths, ...)`) means the
    list the writer really runs with is not the literal, so it cannot be followed."""
    paths: list[str] = []
    mutated = (paths, "source_paths_mutated_at_runtime")
    parents: dict[int, ast.AST] | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, (ast.Tuple, ast.List, ast.Starred)) and _contains_source_paths(t) for t in targets):
                return mutated
            if any(_is_source_paths(t) for t in targets):
                v = node.value
                if not isinstance(v, (ast.List, ast.Tuple)) or not all(_is_str(e) for e in v.elts):
                    return paths, "source_paths_not_a_literal_list_of_strings"
                paths += [e.value for e in v.elts]
        elif isinstance(node, ast.AugAssign) and _is_source_paths(node.target):
            return mutated
        elif isinstance(node, ast.NamedExpr) and _is_source_paths(node.target):
            return mutated
        elif isinstance(node, ast.Delete) and any(_contains_source_paths(t) for t in node.targets):
            return mutated
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)) and _contains_source_paths(node.target):
            return mutated
        elif isinstance(node, ast.Constant) and node.value == "source_paths":
            return mutated                                           # setattr / getattr / vars()[...] by name
        elif _is_source_paths(node) and isinstance(getattr(node, "ctx", None), ast.Load):
            parents = parents if parents is not None else _parent_map(tree)
            par = parents.get(id(node))
            ok = ((isinstance(par, ast.Call) and isinstance(par.func, ast.Name) and par.func.id in _SOURCE_PATHS_READERS
                   and node in par.args)
                  or (isinstance(par, (ast.For, ast.AsyncFor, ast.comprehension)) and par.iter is node)
                  or isinstance(par, ast.Compare)
                  or (isinstance(par, ast.Subscript) and par.value is node and isinstance(par.ctx, ast.Load)))
            if not ok:
                return mutated
    return paths, None


def scan_writer_tables(asset_id: str, repo: str | Path, helpers: Mapping[str, dict] | None = None) -> dict:
    """Static, read-only scan of one writer. Returns {"tables": [...], "files": [...]} or {"not_scanned": reason}."""
    repo = Path(repo).resolve()
    if not _ASSET_ID_RE.match(asset_id):
        return {"not_scanned": "asset_id_is_not_a_plain_identifier"}
    writer = repo / WRITERS_REL / f"{asset_id}.py"
    if not writer.is_file():
        return {"not_scanned": "writer_file_not_found"}
    tree = _parse_python(writer)
    if tree is None:
        return {"not_scanned": "writer_file_unparseable"}
    files = [writer]
    source_paths, bad = _source_paths_literal(tree)
    if bad:
        return {"not_scanned": bad}
    for rel in source_paths:
        if not rel.endswith(".py"):
            return {"not_scanned": f"source_path_not_python: {rel}"}
        cand = (repo / rel).resolve()
        try:
            cand.relative_to(repo)
        except ValueError:
            return {"not_scanned": f"source_path_outside_repo: {rel}"}
        if cand != writer.resolve():
            files.append(cand)
    helpers = helper_write_effects(repo) if helpers is None else helpers
    tables: set[str] = set()
    scanned: list[str] = []
    for f in files:
        t = tree if f == writer else _parse_python(f)
        if t is None:
            return {"not_scanned": f"source_file_unreadable_or_unparseable: {f.name}"}
        try:
            sc = _WriteScan(t)
            sc.resolve_param_calls({k: v["params"] for k, v in helpers.items() if v["params"]})
        except RecursionError:
            return {"not_scanned": f"source_file_too_deeply_nested: {f.name}"}
        for call in sc.calls:
            fname = call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None
            if fname in helpers and fname not in sc.defined:
                sc.tables |= helpers[fname]["tables"]
                if helpers[fname]["unresolved"]:
                    sc.unresolved.append(f"helper_write_unresolved: {fname}: {helpers[fname]['unresolved']}")
        if sc.unresolved:
            return {"not_scanned": sc.unresolved[0]}
        tables |= sc.tables
        scanned.append(f.relative_to(repo).as_posix() if f.resolve().is_relative_to(repo) else str(f))
    if not tables:
        return {"not_scanned": "no_write_statement_found (delegates to another module, or read-only: not distinguishable)"}
    return {"tables": sorted(tables), "files": scanned}


def footprint_scope(rows_now: Sequence[Mapping[str, Any]], writes: Sequence[str], repo: str | Path) -> dict:
    """assets_without_target_table / assets_whose_writer_writes_other_tables / assets_not_scanned, and the scope they imply.

    An empty row set is never "complete": nothing was examined."""
    write_set = {_norm_table(w) for w in writes}
    helpers = helper_write_effects(Path(repo))
    without, others, not_scanned = [], [], []
    for r in sorted({x["asset_id"]: x for x in rows_now}.values(), key=lambda x: x["asset_id"]):
        asset_id = r["asset_id"]
        own = _norm_table(r["target_table"]) if r.get("target_table") else None
        if own is None:
            without.append(asset_id)
        try:
            res = scan_writer_tables(asset_id, repo, helpers)
        except Exception as exc:  # noqa: BLE001 -- a scan that cannot run is "not scanned", never a crash and never clean
            res = {"not_scanned": f"scan_error: {type(exc).__name__}"}
        if "not_scanned" in res:
            not_scanned.append({"asset_id": asset_id, "reason": res["not_scanned"]})
            continue
        extra = sorted(t for t in res["tables"] if t != own)
        uncovered = sorted(t for t in extra if t not in write_set)
        if uncovered:
            others.append({"asset_id": asset_id, "registry_target_table": own, "extra_tables": uncovered,
                           "extra_tables_already_in_write_set": sorted(set(extra) - set(uncovered)),
                           "source": FOOTPRINT_SCAN_LABEL, "files": res["files"]})
    reasons = [name for name, hit in (("no_assets_in_set", not rows_now),
                                      ("assets_without_target_table", without),
                                      ("writer_writes_other_tables", others),
                                      ("writer_not_scanned", not_scanned)) if hit]
    return {"footprint_scope": "partial" if reasons else "complete",
            "partial_reasons": reasons,
            "assets_without_target_table": without,
            "assets_whose_writer_writes_other_tables": others,
            "assets_not_scanned": not_scanned,
            "writer_scan": FOOTPRINT_SCAN_LABEL}


def impact_statement_scope_lines(scope: Mapping[str, Any]) -> list[str]:
    """The footprint scope and the three lists, for the impact statement. A partial scope is stated, never implied; a
    complete one is labelled as complete only per the static scan."""
    partial = scope["footprint_scope"] == "partial"
    label = "PARTIAL" if partial else "COMPLETE_PER_STATIC_SCAN"
    lines = [f"  Footprint scope: {label} (writer scan is {scope.get('writer_scan', FOOTPRINT_SCAN_LABEL)}; "
             "the registry shows one target_table per asset)"]
    if partial:
        lines.append("  ! PARTIAL: the write set above is only what asset_registry.target_table shows and the FK closure "
                     "can see -- has_blockers is UNKNOWN, not false; the items below are NOT in the footprint. "
                     f"Reasons: {', '.join(scope.get('partial_reasons', [])) or 'unspecified'}.")
    else:
        lines.append("  (indicative: every writer was statically scanned and showed no table beyond its registry target; "
                     "the scan cannot see stored functions, runtime-built SQL or delegates -- see the limitations below)")
    closure = scope.get("fk_closure_status")
    if closure is not None and closure != "COMPLETE":
        lines.append(f"  ! FK closure is {closure}: the catalog could not confirm the FK edges of the write set.")
    if scope["assets_without_target_table"]:
        lines.append(f"  Assets without a target_table ({len(scope['assets_without_target_table'])}): "
                     + ", ".join(scope["assets_without_target_table"]))
    others = scope["assets_whose_writer_writes_other_tables"]
    if others:
        lines.append(f"  Assets whose writer writes other tables, indicative ({len(others)}):")
        lines += [f"    - {o['asset_id']}: {', '.join(o['extra_tables'])}" for o in others]
    ns = scope["assets_not_scanned"]
    if ns:
        lines.append(f"  Assets not scanned ({len(ns)}):")
        lines += [f"    - {o['asset_id']}: {o['reason']}" for o in ns]
    lines.append("  Limitations of the writer scan:")
    lines += [f"    - {x}" for x in WRITE_SCAN_LIMITATIONS]
    return lines


def _footprint_report(conn, rows_now: Sequence[Mapping[str, Any]], *, repo: str | Path = REPO_ROOT) -> dict:
    """E5.9 footprint of the wave's write tables (registry target_table); the loaders run SELECTs only.

    footprint_scope is "complete" only when every asset has a target_table AND its writer was scanned AND showed no table
    beyond it AND the FK closure over the write set is COMPLETE; otherwise "partial", and has_blockers is reported as
    "unknown" (never false) with the value computed over the known part kept as has_blockers_known_subset."""
    edges = fk_edges_from_catalog(conn)
    tables = tables_from_catalog(conn)
    writes = sorted({r["target_table"] for r in rows_now if r.get("target_table")})
    scope = footprint_scope(rows_now, writes, repo)
    if not writes:
        scope["fk_closure_status"] = "NOT_COMPUTED"
        return {"status": "NO_TARGET_TABLES", "detail": "no asset in the set declares a target_table",
                "has_blockers": "unknown", "has_blockers_known_subset": None, "fk_closure_status": "NOT_COMPUTED",
                **scope, "impact_lines": impact_statement_scope_lines(scope)}
    fp = dict(transitive_footprint(writes, edges, known_tables=tables))
    scope["fk_closure_status"] = fp["fk_closure_status"]
    if fp["fk_closure_status"] != "COMPLETE":
        scope["footprint_scope"] = "partial"
        scope["partial_reasons"] = [*scope["partial_reasons"], "fk_closure_incomplete"]
        scope["fk_closure_incomplete_reasons"] = list(fp["incomplete_reasons"])
    partial = scope["footprint_scope"] == "partial"
    known_subset = fp["has_blockers"]
    fp.update(scope)
    if partial:
        fp["has_blockers_known_subset"] = fp["has_blockers"]
        fp["has_blockers"] = "unknown"
        fp["has_immediate_blockers_known_subset"] = fp["has_immediate_blockers"]
        fp["has_immediate_blockers"] = "unknown"
    lines = impact_statement_footprint_section(fp)
    lines += impact_statement_scope_lines(scope)
    return {"footprint": fp, "impact_lines": lines, "has_blockers": fp["has_blockers"],
            "has_blockers_known_subset": known_subset, **scope}


def read_rows(connect, assets: Sequence[str]) -> list[dict]:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(CANDIDATES_SQL, (list(assets),))
        rows = [dict(r) for r in cur.fetchall()]
        conn.rollback()
        return rows
    finally:
        conn.close()


CLOSURE_SQL = """
SELECT ar.asset_id, COALESCE(ar.depends_on, '{}') AS depends_on
  FROM asset_registry ar
 WHERE ar.asset_id = ANY(%s)
 ORDER BY ar.asset_id
"""


def read_dependency_closure(connect, assets: Sequence[str], rows: Sequence[Mapping[str, Any]], *, max_rounds: int = 12) -> dict:
    """{out-of-set asset: its declared depends_on} for the upstream closure of the requested set, so the wave derivation
    can see ordering paths that run through assets outside the set. Read-only; ids the registry does not know map to []."""
    inset = set(assets)
    frontier = sorted({d for r in rows for d in (r.get("depends_on") or [])} - inset)
    outside: dict[str, list[str]] = {}
    conn = connect()
    try:
        cur = conn.cursor()
        rounds = 0
        while frontier:
            rounds += 1
            if rounds > max_rounds:
                raise LevelWaveError("dependency closure did not converge (cycle outside the set?)")
            cur.execute(CLOSURE_SQL, (frontier,))
            got = {r["asset_id"]: list(r["depends_on"] or []) for r in cur.fetchall()}
            for d in frontier:
                outside[d] = got.get(d, [])
            frontier = sorted({d for deps in got.values() for d in deps} - inset - set(outside))
        conn.rollback()
    finally:
        conn.close()
    return outside


def _load_frozen_dispatcher():
    """dispatch_frozen_rebuild.py (stdlib at import time), loaded by path so its gcloud dispatch and terminalise
    helpers are reused as they are, not copied. Loaded BEFORE any insert so a load failure can not strand a run."""
    path = Path(__file__).resolve().parents[1] / "dispatch_frozen_rebuild.py"
    spec = importlib.util.spec_from_file_location("dispatch_frozen_rebuild", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------------------------
# Stop hook (between waves) and wave-by-wave driver
# ---------------------------------------------------------------------------------------------

STALE_HOOK_GLOBS = ("after-wave-*.continue", "after-wave-*.stop", "after-wave-*.pending.json")


def continue_token(next_wave: int, run_id: str, report: Mapping[str, Any] | None = None) -> str:
    """The operator's continue token, bound to the run that just finished: its run_id (a fresh uuid per insert) and the
    ended_at of its assets, which exist only once the wave has ended. It can not be computed from a dry-run summary or
    from the manifest, so a token written in advance is wrong."""
    ended = sorted(str(a.get("ended_at")) for a in (report or {}).get("assets", []))
    nonce = hashlib.sha256(canonical_json({"run_id": run_id, "ended_at": ended}).encode("utf-8")).hexdigest()[:12].upper()
    return f"CONTINUE_WAVE_{next_wave}_{nonce}"


def stale_hook_files(pause_dir: str | Path) -> list[str]:
    root = Path(pause_dir)
    if not root.is_dir():
        return []
    return sorted({p.name for g in STALE_HOOK_GLOBS for p in root.glob(g)})


def check_pause_dir_clean(pause_dir: str | Path) -> None:
    """Refuse (do not delete) when the pause directory already holds hook files: a leftover .continue or .stop could
    release or stop a wave without the operator having seen it finish."""
    stale = stale_hook_files(pause_dir)
    if stale:
        raise LevelWaveRefusal([{"code": "STALE_HOOK_FILES", "files": stale, "pause_dir": str(pause_dir),
                                 "detail": f"{pause_dir} already holds {stale}. Nothing was deleted: remove them yourself "
                                           "(or use a fresh --pause-dir) and relaunch."}])


def _write_private(path: Path, text: str) -> None:
    """Write `text` to `path` with mode 0600 from the first byte."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(path, 0o600)


def file_stop_hook(pause_dir: str | Path, *, poll_seconds: float = 5.0, timeout_seconds: float = 6 * 3600.0,
                   settle_attempts: int = 5, settle_seconds: float = 1.0, sleep=time.sleep, monotonic=time.monotonic):
    """A hook(wave_done, summary, next_info) -> bool. It first REFUSES if this wave's .continue / .stop already exist
    (stale, or written before the wave finished); then writes <dir>/after-wave-<k>.pending.json (mode 0600, in a 0700
    directory: what finished, the wall times, the next wave and its run-bound token) and waits for
    <dir>/after-wave-<k>.continue whose text is exactly next_info["continue_token"]. A .continue that exists but does not
    (yet) hold the token (empty, half-written) is re-read `settle_attempts` times, `settle_seconds` apart, before it counts
    as a wrong token; .stop, a wrong token or the timeout all STOP (False). Nothing continues by default."""
    root = Path(pause_dir)

    def hook(wave_done: int, summary: Mapping[str, Any], next_info: Mapping[str, Any]) -> bool:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(root, 0o700)
        stem = root / f"after-wave-{wave_done}"
        pre = [p.name for p in (stem.with_suffix(".continue"), stem.with_suffix(".stop")) if p.exists()]
        if pre:
            raise LevelWaveRefusal([{"code": "STALE_HOOK_FILES", "files": pre, "pause_dir": str(root),
                                     "detail": f"{pre} existed before wave {wave_done} was reported finished: refused. "
                                               "Remove them and relaunch; the campaign stops here."}])
        token = next_info["continue_token"]
        _write_private(stem.with_suffix(".pending.json"), json.dumps(
            {"wave_done": wave_done, "summary": summary, "next": dict(next_info), "continue_token": token,
             "to_continue": f"write the token into {stem.with_suffix('.continue')}",
             "to_stop": f"create {stem.with_suffix('.stop')}"}, sort_keys=True, default=str, indent=1))
        deadline = monotonic() + timeout_seconds
        while True:
            if stem.with_suffix(".stop").exists():
                return False
            go = stem.with_suffix(".continue")
            if go.exists():
                for attempt in range(settle_attempts):
                    if stem.with_suffix(".stop").exists():
                        return False
                    if go.read_text(encoding="utf-8").strip() == token:
                        return True
                    if attempt + 1 < settle_attempts:
                        sleep(settle_seconds)
                return False
            if monotonic() >= deadline:
                return False
            sleep(poll_seconds)
    return hook


def wait_for_terminal_run(connect, run_id: str, *, poll_seconds: float, timeout_seconds: float,
                          sleep=time.sleep, monotonic=time.monotonic) -> dict:
    """Poll build_runs until completed/stopped/failed. A timeout returns state 'timeout' (the run is left alone)."""
    deadline = monotonic() + timeout_seconds
    while True:
        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT state, last_error FROM build_runs WHERE id=%s", (run_id,))
            row = cur.fetchone()
            conn.rollback()
        finally:
            conn.close()
        state = row["state"] if row else "missing"
        if state in TERMINAL_RUN_STATES or state == "missing":
            return {"state": state, "last_error": (row or {}).get("last_error")}
        if monotonic() >= deadline:
            return {"state": "timeout", "last_error": None}
        sleep(poll_seconds)


# asset_throughput.state values that mean "finished successfully": exactly the success states of the runner's own allowlist
# (runner._SUCCESS_OUTCOMES minus the build_run_assets literal 'complete'). Anything else, 'incomplete' included, is a failure.
GOOD_THROUGHPUT_STATES = frozenset({"lit", "mature", "dormant", "service_ok"})


def _not_built_reason(row: Mapping[str, Any] | None, declared_skip: bool) -> str | None:
    """Why an asset of a finished wave does not count as built, or None when it does."""
    if row is None:
        return "no build_run_assets row was reported for this asset"
    if row.get("state") != "complete":
        return f"build_run_assets.state is {row.get('state')!r}, not 'complete'"
    tp = row.get("throughput_state")
    if tp not in GOOD_THROUGHPUT_STATES:
        return (f"asset_throughput.state is {tp!r} (the runner marks build_run_assets 'complete' even for an incomplete "
                f"build); accepted: {sorted(GOOD_THROUGHPUT_STATES)}")
    disposition = row.get("disposition")
    if disposition == "skip_no_delta":
        return None if declared_skip else "skip_no_delta (nothing was rebuilt) and the asset is not in --declared-skips"
    if disposition != "build":
        return f"disposition is {disposition!r}, not 'build'"
    return None


def run_wave_by_wave(plan: Mapping[str, Any], *, dispatch_wave, wait_terminal, wave_report, hook,
                     declared_skips: Iterable[str] = (), emit=None) -> dict:
    """Drive the waves one run at a time. `dispatch_wave(i)` inserts+dispatches wave i (it re-checks dependencies lit+fresh
    in its own transaction, so wave i+1 only starts once wave i's assets are lit+fresh), `wait_terminal(run_id)` blocks,
    `wave_report(run_id)` returns the wall-time report, `hook(done, summary, next)` is the operator pause.
    Stops at the first wave whose run is not `completed`, whose dispatch refuses or errors, whose assets are not all
    `complete` by the strict test in _not_built_reason, or whose hook says stop. A no-delta skip (disposition
    'skip_no_delta') is NOT success unless the asset is in `declared_skips`; every skipped asset is reported either way. Any exception (a database error included) stops the campaign with STOPPED_ERROR and the
    run id, never an escaped traceback. `emit(event, **fields)` is called at every dispatch and wave end."""
    emit = emit or (lambda event, **fields: None)
    declared = set(declared_skips)
    results: list[dict] = []
    per_wave = plan["per_wave"]

    def stop(status: str) -> dict:
        return {"status": status, "waves": results}

    for i, wave in enumerate(per_wave):
        entry: dict[str, Any] = {"wave": i, "assets": wave["assets"]}
        results.append(entry)
        try:
            receipt = dispatch_wave(i)
        except LevelWaveRefusal as exc:
            entry.update(status="REFUSED", refusals=exc.refusals)
            emit("wave_refused", wave=i, refusals=exc.refusals)
            return stop("STOPPED_REFUSED")
        except CommitOutcomeUnknown as exc:
            entry.update(status="ERROR", error=exc.detail, commit_outcome_unknown=True, run_id=exc.run_id)
            emit("wave_error", wave=i, run_id=exc.run_id, error=exc.detail, stage="commit", commit_outcome_unknown=True)
            return stop("STOPPED_ERROR")
        except Exception as exc:  # noqa: BLE001 -- a database error must still end in a JSON summary
            entry.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")
            emit("wave_error", wave=i, error=entry["error"], stage="dispatch")
            return stop("STOPPED_ERROR")
        run_id = receipt["run_id"]
        entry["run_id"] = run_id
        emit("wave_dispatched", wave=i, run_id=run_id, execution_name=receipt.get("execution_name"),
             manifest_digest=receipt.get("manifest_digest"))
        try:
            terminal = wait_terminal(run_id)
            report = wave_report(run_id)
        except Exception as exc:  # noqa: BLE001
            entry.update(status="ERROR", error=f"{type(exc).__name__}: {exc}",
                         note=f"run {run_id} is committed and may still be running: find it by run_id")
            emit("wave_error", wave=i, run_id=run_id, error=entry["error"], stage="wait_or_report")
            return stop("STOPPED_ERROR")
        entry.update(run_state=terminal["state"], last_error=terminal.get("last_error"), wall_time=report)
        emit("wave_ended", wave=i, run_id=run_id, run_state=terminal["state"], last_error=terminal.get("last_error"),
             unmeasured=report.get("unmeasured"), run_wall_seconds=report.get("run_wall_seconds"))
        if terminal["state"] != "completed":
            entry["status"] = "RUN_NOT_COMPLETED"
            return stop("STOPPED_RUN_NOT_COMPLETED")
        # An asset of the wave counts as built only when ALL of these hold, read from the database after the run:
        #   build_run_assets.state == 'complete' (the runner writes that literal for every terminal outcome, the
        #     'incomplete' of SATYA-DIPA included -- so it proves nothing alone);
        #   asset_throughput.state in GOOD_THROUGHPUT_STATES (what the writer path actually computed; none/NULL fails:
        #     every asset here is writer-backed);
        #   disposition == 'build', or 'skip_no_delta' for an asset named in `declared_skips` (a no-delta skip rebuilt
        #     nothing; any other disposition -- withheld, deferred, blocked, dormant -- is not a build).
        # A missing report row, or no report at all, fails every asset. The reason is recorded per asset.
        got = {a["asset_id"]: a for a in report.get("assets", [])}
        skipped = sorted(a for a in wave["assets"] if (got.get(a) or {}).get("disposition") == "skip_no_delta")
        if skipped:
            entry["assets_skipped"] = skipped
        reasons = {a: why for a in wave["assets"] if (why := _not_built_reason(got.get(a), a in declared))}
        if reasons:
            entry["status"] = "ASSETS_NOT_COMPLETE"
            entry["assets_not_complete"] = sorted(reasons)
            entry["not_complete_reasons"] = {a: reasons[a] for a in sorted(reasons)}
            emit("wave_assets_not_complete", wave=i, run_id=run_id, reasons=entry["not_complete_reasons"])
            return stop("STOPPED_ASSETS_NOT_COMPLETE")
        entry["status"] = "COMPLETED"
        if i + 1 < len(per_wave):
            nxt = per_wave[i + 1]
            info = {"wave": i + 1, "assets": nxt["assets"], "manifest_digest": nxt["manifest_digest"],
                    "after_run_id": run_id, "continue_token": continue_token(i + 1, run_id, report)}
            try:
                ok = hook(i, report, info)
            except LevelWaveRefusal as exc:
                entry.update(hook="REFUSED", refusals=exc.refusals)
                emit("hook_refused", wave=i, refusals=exc.refusals)
                return stop("STOPPED_HOOK_REFUSED")
            except Exception as exc:  # noqa: BLE001
                entry.update(hook="ERROR", error=f"{type(exc).__name__}: {exc}")
                emit("wave_error", wave=i, run_id=run_id, error=entry["error"], stage="hook")
                return stop("STOPPED_ERROR")
            if not ok:
                entry["hook"] = "STOP"
                emit("hook_stop", wave=i)
                return stop("STOPPED_BY_OPERATOR")
            entry["hook"] = "CONTINUE"
            emit("hook_continue", wave=i, next_wave=i + 1)
    return stop("ALL_WAVES_COMPLETED")


# ---------------------------------------------------------------------------------------------
# Per-asset wall-time report (after a run)
# ---------------------------------------------------------------------------------------------

RUN_ASSETS_SQL = """
SELECT bra.asset_id, bra.position, bra.state, bra.disposition, bra.started_at, bra.ended_at, bra.error,
       t.state AS throughput_state, t.last_built_at
  FROM build_run_assets bra
  JOIN build_runs br ON br.id = bra.run_id
  LEFT JOIN LATERAL (
        SELECT state, last_built_at FROM asset_throughput at
         WHERE at.asset_id = bra.asset_id AND (at.chart_id IS NOT DISTINCT FROM br.chart_id OR at.chart_id IS NULL)
         ORDER BY (at.chart_id IS NOT DISTINCT FROM br.chart_id) DESC, at.last_built_at DESC NULLS LAST
         LIMIT 1) t ON true
 WHERE bra.run_id = %s
 ORDER BY bra.position
"""


def _as_dt(v):
    if v is None or isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def asset_wall_time_report(rows: Sequence[Mapping[str, Any]], waves: Sequence[Sequence[str]] | None = None) -> dict:
    """Per-asset wall time from build_run_assets (started_at/ended_at) plus the asset_throughput state, with per-wave and
    whole-run spans. An asset with a missing or inverted timestamp is `unmeasured` (wall_seconds None), never 0."""
    wave_of = {a: i for i, w in enumerate(waves or ()) for a in w}
    assets, unmeasured = [], []
    for r in sorted(rows, key=lambda x: (x.get("position") is None, x.get("position"), x["asset_id"])):
        s, e = _as_dt(r.get("started_at")), _as_dt(r.get("ended_at"))
        wall = (e - s).total_seconds() if s is not None and e is not None and e >= s else None
        entry = {"asset_id": r["asset_id"], "position": r.get("position"), "wave": wave_of.get(r["asset_id"]),
                 "state": r.get("state"), "disposition": r.get("disposition"), "started_at": s.isoformat() if s else None,
                 "ended_at": e.isoformat() if e else None, "wall_seconds": wall, "error": r.get("error"),
                 "throughput_state": r.get("throughput_state")}
        assets.append(entry)
        if wall is None:
            unmeasured.append(r["asset_id"])
    per_wave = {}
    for i, w in enumerate(waves or ()):
        span = [(_as_dt(r.get("started_at")), _as_dt(r.get("ended_at"))) for r in rows if r["asset_id"] in set(w)]
        starts = [s for s, _ in span if s]
        ends = [e for _, e in span if e]
        full = len(starts) == len(w) and len(ends) == len(w)
        per_wave[str(i)] = {"assets": len(w), "wall_seconds": (max(ends) - min(starts)).total_seconds() if full else None}
    starts = [_as_dt(r.get("started_at")) for r in rows if r.get("started_at")]
    ends = [_as_dt(r.get("ended_at")) for r in rows if r.get("ended_at")]
    measured = [a["wall_seconds"] for a in assets if a["wall_seconds"] is not None]
    return {
        "schema": LEVEL_WAVE_SCHEMA + "/wall_time",
        "assets": assets, "unmeasured": sorted(unmeasured), "per_wave": per_wave,
        "run_wall_seconds": (max(ends) - min(starts)).total_seconds() if starts and ends and len(starts) == len(rows) == len(ends) else None,
        "sum_asset_seconds": sum(measured) if measured else None,
        "slowest": [a["asset_id"] for a in sorted((a for a in assets if a["wall_seconds"] is not None),
                                                  key=lambda a: (-a["wall_seconds"], a["asset_id"]))[:5]],
    }


def read_wall_time_report(connect, run_id: str, waves: Sequence[Sequence[str]] | None = None) -> dict:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(RUN_ASSETS_SQL, (run_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.rollback()
    finally:
        conn.close()
    if not rows:
        raise LevelWaveError(f"no build_run_assets rows for run {run_id}")
    return asset_wall_time_report(rows, waves)


def forced_effect(connect, run_id: str) -> dict:
    """Did a forced run actually force? Read the run's state and each asset's disposition once: `build` means the writer ran,
    `skip_no_delta` means the delta-skip was NOT bypassed. forced_effective is True / False, or None when the run has not ended
    or the reading is incomplete (never a guess). A False carries a warning."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT state, last_error FROM build_runs WHERE id=%s", (run_id,))
        run = cur.fetchone()
        cur.execute(RUN_ASSETS_SQL, (run_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.rollback()
    finally:
        conn.close()
    state = run["state"] if run else "missing"
    dispositions = {r["asset_id"]: r.get("disposition") for r in rows}
    out: dict[str, Any] = {"run_id": run_id, "run_state": state, "dispositions": dispositions, "forced_effective": None,
                           "warning": None}
    if state not in TERMINAL_RUN_STATES:
        out["note"] = f"run is {state!r}: the disposition is not verified (it can still change)"
    elif not rows:
        out["note"] = "no build_run_assets rows: not verified"
    elif any(d == "skip_no_delta" for d in dispositions.values()):
        skipped = sorted(a for a, d in dispositions.items() if d == "skip_no_delta")
        out["forced_effective"] = False
        out["warning"] = (f"FORCE DID NOT TAKE EFFECT: {skipped} ended skip_no_delta although --force-execute was set "
                          "(the deployed image or job env did not honour NIRMANA_FORCE_EXECUTE)")
    elif all(d == "build" for d in dispositions.values()):
        out["forced_effective"] = True
    else:
        out["note"] = f"dispositions {sorted(set(map(str, dispositions.values())))} are not all 'build': not verified"
    return out


# ---------------------------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------------------------

HELP_EPILOG = (
    "WARNING: " + NEVER_EXECUTED_NOTE + "\n\n"
    "The LIVE dry run (INSERT then ROLLBACK, run by the operator session against the real database) is MANDATORY before the "
    "first --commit: it prints the LIVE wave list. Any wave list in the README is indicative only.\n\n"
    "Default is a DRY RUN. --commit needs --confirm <token> (printed by the dry run, bound to the manifest digest), --mode, "
    "--deployed-sha AND --deployed-job-sha (the live deployed job image sha read at launch; it must be the same commit as the "
    "inventory the digests come from), and FAMILY_ASSETS.json on a fresh origin/main. single-run submits all waves in ONE run "
    "(the runner has no hook between waves); wave-by-wave submits one run per wave and pauses for the operator between waves "
    "(--pause-dir, --job-sha-file re-read before every wave). Refuses: image skew, a job sha mismatch, any dependency outside "
    "the set not lit+fresh (whole plan), a registry row changed since the manifest was built, any Pravaha gochara-family asset, "
    "a split family, an unreadable or stale family file, a non-per_chart asset, an active run on the chart, stale hook files.\n\n"
    "--force-execute (OFF by default) dispatches with NIRMANA_FORCE_EXECUTE=1: it bypasses the runner's delta-skip for EVERY "
    "asset of the run, so it is allowed for ONE asset only, never a family asset, and needs --commit with its own force-bound "
    "--confirm token (a dry run previews the token). The deployed image must contain the force read or it is refused "
    "(FORCE_NOT_SUPPORTED_BY_IMAGE); single-run does not verify the effect unless --verify-forced.\n\n"
    "Output is JSON lines, flushed per event; the last line is the summary. Exit codes: 0 ok / dry run done; 1 DATABASE_URL "
    "missing; 2 bad input; 3 dispatch failed after commit (see the warning in the summary); 4 a gate refused; 5 wave-by-wave "
    "campaign stopped; 6 unexpected exception or database error (the summary lists every run committed so far; a COMMIT "
    "that failed mid-way is reported as outcome unknown); 7 interrupted (SIGINT/SIGTERM; the summary lists the runs committed "
    "so far and the chart-blocking warning)."
)


def _psycopg_connect_factory(database_url: str):
    def connect():
        import psycopg  # noqa: PLC0415
        import psycopg.rows  # noqa: PLC0415
        conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
        conn.autocommit = False
        conn.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
        return conn
    return connect


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="suvarna_level_wave.py", description="Multi-asset level-wave manifest builder and dispatcher "
                                "(E5.3). Reads DATABASE_URL from the environment; never reads credential files.",
                                epilog=HELP_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chart-id", required=True)
    p.add_argument("--assets", action="append", required=True, metavar="LIST|@FILE",
                   help="explicit asset ids: comma list, repeated flag, or @file (asset_census.parse_assets_arg semantics)")
    p.add_argument("--mode", choices=("single-run", "wave-by-wave"), help="required with --commit")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--deployed-sha", help="commit whose committed writer digests are taken as the deployed image's")
    g.add_argument("--deployed-digests-file", help="a nirmana-writer-digests.json copied from the deployed image "
                   "(dry run only: its provenance can not be bound to a job sha)")
    p.add_argument("--deployed-job-sha", help="the LIVE deployed job image sha (DEPLOY_SHA / image, never a deploy run's "
                   "head_sha), read by the operator at launch; must equal --deployed-sha")
    p.add_argument("--job-sha-file", help="a file the operator's gate keeps holding exactly the live deployed job sha (40 hex); "
                   "validated at launch and re-read before every wave (required for wave-by-wave --commit)")
    p.add_argument("--force-execute", action="store_true", help="OFF by default. Dispatch with NIRMANA_FORCE_EXECUTE=1 (gcloud "
                   "--update-env-vars): bypasses the runner's delta-skip for EVERY asset of the run, so a single asset only, "
                   "never a family asset; needs --commit and its own force-bound --confirm token (a dry run previews it)")
    p.add_argument("--verify-forced", action="store_true", help="single-run with --force-execute: after dispatch wait for the run "
                   "to end and report forced_effective (build vs skip_no_delta), warning if it skipped; wave-by-wave always verifies")
    p.add_argument("--declared-skips", default="", help="comma list of assets whose no-delta skip (disposition skip_no_delta) counts as success")
    p.add_argument("--repo", default=str(REPO_ROOT))
    p.add_argument("--family-ref", default="origin/main")
    p.add_argument("--commit", action="store_true", help="commit the run(s); omission is a rollback-only dry run")
    p.add_argument("--confirm", help="required with --commit: the token the dry run printed")
    p.add_argument("--with-footprint", action="store_true", help="include the E5.9 transitive footprint (catalog SELECTs only)")
    p.add_argument("--pause-dir", help="wave-by-wave: directory for the stop-hook files (must hold none already)")
    p.add_argument("--poll-seconds", type=float, default=15.0)
    p.add_argument("--wave-timeout-seconds", type=float, default=4 * 3600.0)
    p.add_argument("--hook-timeout-seconds", type=float, default=6 * 3600.0)
    p.add_argument("--project", default="madhav-astrology")
    p.add_argument("--region", default="asia-south1")
    p.add_argument("--job", default="brahma-build-pipeline-job")
    return p


def _emit(out, event: str, **fields) -> None:
    out.write(json.dumps({"schema": LEVEL_WAVE_SCHEMA, "event": event, **fields}, sort_keys=True, default=str) + "\n")
    flush = getattr(out, "flush", None)
    if flush is not None:
        flush()


def precheck_external(connect, chart_id: str, external: Mapping[str, Sequence[str]]) -> None:
    """Read-only check of the WHOLE plan's outside dependencies (every wave), before anything is inserted."""
    conn = connect()
    try:
        check_external_dependencies(conn.cursor(), chart_id, external)
        conn.rollback()
    finally:
        conn.close()


def dispatch_command(*, run_id: str, project: str, region: str, job: str, force_execute: bool = False) -> list[str]:
    """The `gcloud run jobs execute` command. With force_execute it adds the per-execution env override
    `--update-env-vars=NIRMANA_FORCE_EXECUTE=1` (a flag `gcloud run jobs execute` accepts next to --args: it merges the pair into
    the job's environment for this one execution). The runner reads that variable per run (runner.py execute_run) and bypasses
    the delta-skip for every asset of the run; there is no manifest field for it."""
    cmd = ["gcloud", "run", "jobs", "execute", job, f"--project={project}", f"--region={region}",
           f"--args=--run-id,{run_id}"]
    if force_execute:
        cmd.append(f"--update-env-vars={FORCE_ENV_VAR}=1")
    return cmd + ["--async", "--format=value(metadata.name)"]


def dispatch_run_with_timeout(*, run_id: str, project: str, region: str, job: str, run_command=None,
                              timeout: float = GCLOUD_TIMEOUT_SECONDS, force_execute: bool = False,
                              authorised: bool = False) -> str:
    """The same `gcloud run jobs execute ... --async` command dispatch_frozen_rebuild.dispatch_run issues, with a timeout, no
    stdin and no prompts. After a timeout the execution may or may not have started: the caller terminalises the planned run
    (the runner refuses a run that is not planned/running), so a late start can not build anything.

    The runner is resolved by injection, never bound at import time: `run_command` is used when given (tests, other tools). With
    none given the REAL process runner (`subprocess.run`, looked up at CALL time) is used only when `authorised=True`, which only
    the explicit `--commit` + matching confirm-token path in `main` sets; any other call refuses before a process can start."""
    if run_command is None:
        if not authorised:
            raise RuntimeError("dispatch refused: no runner injected and the call is not the authorised --commit path")
        run_command = subprocess.run
    try:
        result = run_command(
            dispatch_command(run_id=run_id, project=project, region=region, job=job, force_execute=force_execute),
            capture_output=True, check=False, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
            env={**os.environ, "CLOUDSDK_CORE_DISABLE_PROMPTS": "1"})
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gcloud timed out after {timeout}s: dispatch outcome unknown") from exc
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "unknown gcloud error").strip()[:1000])
    execution = result.stdout.strip()
    if not execution:
        raise RuntimeError("gcloud returned no execution name")
    return execution


def _terminalise(connect, run_id: str, error: str, frozen=None) -> None:
    """Take a planned-but-undispatched run out of the active set (dispatch_frozen_rebuild's own statement)."""
    frozen = frozen or _load_frozen_dispatcher()
    conn = connect()
    try:
        frozen.terminalize_dispatch_failure(conn.cursor(), run_id=run_id, error=error)
        conn.commit()
    finally:
        conn.close()


def _terminalise_or_warn(connect, run_id: str, chart_id: str, error: str, frozen) -> str | None:
    """Terminalise; if that fails, return the chart-blocking warning instead of raising (the run id must be reported)."""
    try:
        _terminalise(connect, run_id, error, frozen)
        return None
    except Exception as exc:  # noqa: BLE001
        return (f"run {run_id} is COMMITTED in state 'planned' and BLOCKS chart {chart_id} until it is terminalised "
                f"(terminalise failed: {type(exc).__name__}: {exc}). Terminalise it by hand: "
                f"UPDATE build_runs SET state='failed', ended_at=NOW(), last_error='dispatch failed' WHERE id='{run_id}' "
                "AND state='planned'; and abort its queued build_run_assets rows.")


def _safe_wall_time_report(connect, run_id: str, waves) -> dict:
    """The wall-time report, or an empty one carrying the error (the wave driver then stops: no reading is not a pass)."""
    try:
        return read_wall_time_report(connect, run_id, waves)
    except LevelWaveError as exc:
        return {"assets": [], "error": str(exc)}


def _interrupt_warning(committed: Sequence[Mapping[str, Any]], chart_id: str) -> str:
    if not committed:
        return "interrupted before any COMMIT was reported: no run id is known (if the interrupt hit during a COMMIT, run the ACTIVE_RUN check)"
    ids = ", ".join(r["run_id"] for r in committed)
    return (f"interrupted after COMMIT: run(s) {ids} exist. One not yet dispatched is committed in state 'planned' and BLOCKS "
            f"chart {chart_id} until it is dispatched or terminalised; one already dispatched may be running. Find each by "
            "run_id before any relaunch.")


def run_cli(args: argparse.Namespace, *, connect, git=_git, out=None, sleep=time.sleep, monotonic=time.monotonic,
            dispatch=None, hook=None) -> int:
    """The whole command, with every outside contact injected (database, git, gcloud, the operator hook). Output is JSON
    lines flushed per event; the last line is the summary (or the refusal / error)."""
    out = out or sys.stdout
    committed: list[dict] = []        # every run committed so far: found by run_id if anything later fails
    try:
        return _run_cli(args, connect=connect, git=git, out=out, sleep=sleep, monotonic=monotonic, dispatch=dispatch,
                        hook=hook, committed=committed)
    except LevelWaveRefusal as exc:
        _emit(out, "refused", refused=True, refusals=exc.refusals, committed_runs=committed,
              never_executed_note=NEVER_EXECUTED_NOTE)
        return REFUSAL_EXIT_CODE
    except LevelWaveError as exc:
        _emit(out, "error", error=str(exc), committed_runs=committed)
        return EXIT_BAD_INPUT
    except CommitOutcomeUnknown as exc:
        _emit(out, "error", unexpected=True, commit_outcome_unknown=True, run_id=exc.run_id, chart_id=exc.chart_id,
              error=exc.detail, committed_runs=committed, warning=exc.detail)
        return EXIT_UNEXPECTED
    except KeyboardInterrupt:
        _emit(out, "interrupted", interrupted=True, committed_runs=committed,
              warning=_interrupt_warning(committed, args.chart_id))
        return EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 -- never an escaped traceback: the operator must see the run ids
        _emit(out, "error", unexpected=True, error=f"{type(exc).__name__}: {exc}", committed_runs=committed,
              warning=("runs listed in committed_runs exist and may be planned/running: find them by run_id before any "
                       "relaunch" if committed else "no run was committed"))
        return EXIT_UNEXPECTED


def _run_cli(args, *, connect, git, out, sleep, monotonic, dispatch, hook, committed) -> int:
    emit = lambda event, **f: _emit(out, event, **f)  # noqa: E731
    assets = parse_asset_scope(args.assets)
    ref_status = family_ref_status(args.repo, args.family_ref, git=git)
    family = load_family_info(args.repo, args.family_ref, git=git)
    refusals = family_ref_refusals(ref_status, committing=args.commit) + family_refusals(assets, family, committing=args.commit)
    if args.force_execute:
        refusals += force_refusals(assets, family)
        declared = {x for x in (args.declared_skips or "").split(",") if x}
        if declared & set(assets):
            refusals.append({"code": "FORCE_WITH_DECLARED_SKIP", "assets": sorted(declared & set(assets)),
                             "detail": "--force-execute with --declared-skips naming the same asset is contradictory: a forced run "
                                       "that ends skip_no_delta means force failed, never success"})
    if refusals:
        raise LevelWaveRefusal(refusals)
    if args.commit and not args.mode:
        raise LevelWaveError("--commit requires --mode single-run|wave-by-wave")
    wave_by_wave = args.mode == "wave-by-wave"
    if wave_by_wave and args.commit and not (args.pause_dir or hook):
        raise LevelWaveError("--mode wave-by-wave --commit requires --pause-dir (the stop hook)")
    if wave_by_wave and args.commit and not args.job_sha_file:
        raise LevelWaveError("--mode wave-by-wave --commit requires --job-sha-file (re-read before every wave)")
    if wave_by_wave and args.commit and args.pause_dir:
        check_pause_dir_clean(args.pause_dir)

    # The live deployed job sha: asserted by the operator, bound to the inventory the digests come from.
    if not args.deployed_job_sha:
        raise LevelWaveRefusal([{"code": "DEPLOYED_JOB_SHA_REQUIRED",
                                 "detail": "--deployed-job-sha (the live deployed job image sha read at launch) is required"}])
    if args.deployed_sha:
        binding = check_job_sha_binding(args.repo, inventory_sha=args.deployed_sha, job_sha=args.deployed_job_sha, git=git)
        binding["binding"] = "verified"
    else:
        if args.commit:
            raise LevelWaveRefusal([{"code": "DEPLOYED_BINDING_UNVERIFIED",
                                     "detail": "a digests file has no provenance a job sha can be checked against: use "
                                               "--deployed-sha for a real dispatch"}])
        binding = {"inventory_sha": None, "deployed_job_sha": resolve_commit(args.repo, args.deployed_job_sha, git=git),
                   "binding": "unverified_file_source"}
    pinned = binding["deployed_job_sha"]
    if args.force_execute:
        check_image_supports_force(args.repo, pinned, git=git)     # the image must honour the flag, or force is a no-op
    if args.job_sha_file:
        recheck_job_sha(args.repo, pinned_job_sha=pinned, job_sha_file=args.job_sha_file, git=git)
    force = bool(args.force_execute)
    meta = {"deployed_job_sha": pinned, "inventory_sha": binding["inventory_sha"], "force_execute": force}

    local = load_local_writer_digests(args.repo)
    deployed = load_deployed_writer_digests(repo=args.repo, sha=args.deployed_sha, file=args.deployed_digests_file, git=git)
    frozen = _load_frozen_dispatcher() if args.commit else None      # before any insert: a load failure strands nothing
    rows = read_rows(connect, assets)
    outside = read_dependency_closure(connect, assets, rows)
    plan = make_plan(chart_id=args.chart_id, assets=assets, rows=rows, writer_digests=local, deployed_digests=deployed,
                     outside_deps={k: v for k, v in outside.items()})
    if wave_by_wave:
        precheck_external(connect, args.chart_id, plan["external_dependencies"])      # every wave's outside dependencies
    estimate = estimate_runtime(plan["waves"], plan["rows"])
    token_full = expected_confirmation(plan["manifest_digest"], len(plan["plan"]), force)
    summary = {
        "schema": LEVEL_WAVE_SCHEMA, "never_executed_note": NEVER_EXECUTED_NOTE, "chart_id": args.chart_id, **meta,
        "job_sha_binding": binding["binding"], "family_ref": ref_status, "force_execute": force,
        "family_enforcement": "name_patterns_and_family_set" if family["state"] == "present" else "name_patterns_only",
        "live_dry_run_note": "the LIVE dry run is mandatory before the first --commit; the waves above are the live waves for "
                             "this registry, any README list is indicative",
        "asset_count": len(plan["plan"]), "waves": plan["waves"], "manifest_digest": plan["manifest_digest"],
        "confirm_token_single_run": token_full,
        "per_wave": [{"wave": w["wave"], "assets": w["assets"], "manifest_digest": w["manifest_digest"],
                      "confirm_token": expected_confirmation(w["manifest_digest"], len(w["assets"]), force)}
                     for w in plan["per_wave"]],
        "external_dependencies": plan["external_dependencies"], "runtime_estimate": estimate, "committed": False,
        "out_of_set_intermediates_at_risk": at_risk_intermediates(assets, {**outside, **{a: plan["rows"][a].get("depends_on") or [] for a in assets}}),
        "committed_runs": committed,
    }
    if args.commit and args.confirm != token_full:
        raise LevelWaveRefusal([{"code": "CONFIRM_TOKEN_MISMATCH", "expected": token_full,
                                 "detail": f"--commit requires --confirm {token_full} (the full-plan token the dry run printed)"}])

    def on_commit(wave_index):
        def cb(receipt):
            rec = {"run_id": receipt["run_id"], "wave": wave_index, "assets": receipt["assets"],
                   "manifest_digest": receipt["manifest_digest"], "chart_id": receipt["chart_id"], **meta}
            committed.append(rec)
            emit("run_committed", **rec)
        return cb

    send = None
    if args.commit:
        # only reached under args.commit with the matching confirm token (CONFIRM_TOKEN_MISMATCH above refuses otherwise)
        send = dispatch or (lambda run_id: dispatch_run_with_timeout(run_id=run_id, project=args.project, region=args.region, job=args.job,
                                                                           force_execute=force, authorised=True))

    def send_or_terminalise(receipt) -> str | None:
        """Dispatch a committed run; on failure terminalise it (or return the chart-blocking warning). Returns the warning
        text on failure, None on success (execution_name is set on the receipt)."""
        try:
            receipt["execution_name"] = send(receipt["run_id"])
            emit("run_dispatched", run_id=receipt["run_id"], execution_name=receipt["execution_name"], **meta)
            return None
        except Exception as exc:  # noqa: BLE001
            warn = _terminalise_or_warn(connect, receipt["run_id"], args.chart_id, f"dispatch failed: {exc}", frozen)
            receipt["dispatch_error"] = str(exc)
            receipt["terminalise_warning"] = warn
            emit("dispatch_failed", run_id=receipt["run_id"], error=str(exc), warning=warn, **meta)
            return warn or "terminalised"

    if not args.commit or not wave_by_wave:
        # Dry run (either mode) or a single-run commit. A wave-by-wave dry run exercises wave 0 only (the whole plan's
        # outside dependencies were already checked above).
        target = plan["per_wave"][0] if wave_by_wave else {
            "assets": plan["plan"], "manifest": plan["manifest"], "manifest_digest": plan["manifest_digest"]}
        tgt = target["assets"]
        ext = external_dependencies(tgt, {a: plan["rows"][a].get("depends_on") or [] for a in tgt})
        receipt = insert_run(connect, chart_id=args.chart_id, manifest=target["manifest"], digest=target["manifest_digest"],
                             row_digests={a: plan["row_digests"][a] for a in tgt}, external=ext,
                             confirm=expected_confirmation(target["manifest_digest"], len(tgt), force) if args.commit else None,
                             commit=args.commit, footprint=args.with_footprint, on_commit=on_commit(0), meta=meta,
                             force_execute=force)
        summary["insert"] = receipt
        summary["committed"] = receipt["committed"]
        if args.commit and send_or_terminalise(receipt) is not None:
            summary["dispatch_error"] = receipt["dispatch_error"]
            summary["terminalise_warning"] = receipt["terminalise_warning"]
            _emit(out, "summary", **summary)
            return EXIT_DISPATCH_FAILED
        if args.commit:
            summary["execution_name"] = receipt.get("execution_name")
        if args.commit and force:
            if args.verify_forced:
                end = wait_for_terminal_run(connect, receipt["run_id"], poll_seconds=args.poll_seconds,
                                            timeout_seconds=args.wave_timeout_seconds, sleep=sleep, monotonic=monotonic)
                eff = forced_effect(connect, receipt["run_id"])
                eff["wait"] = end["state"]
                summary["forced_effect"] = eff
                summary["forced_effective"] = eff["forced_effective"]
                emit("forced_effect", **eff)
                if eff["warning"]:
                    summary["warning"] = eff["warning"]
            else:
                summary["forced_effective"] = "not_verified"
                summary["forced_note"] = ("single-run reads nothing back: the disposition (build vs skip_no_delta) is NOT verified; "
                                          "use --verify-forced or read build_run_assets.disposition for this run")
        _emit(out, "summary", **summary)
        return 0

    the_hook = hook or file_stop_hook(args.pause_dir, poll_seconds=args.poll_seconds, timeout_seconds=args.hook_timeout_seconds,
                                      sleep=sleep, monotonic=monotonic)

    def dispatch_wave(i):
        recheck_job_sha(args.repo, pinned_job_sha=pinned, job_sha_file=args.job_sha_file, git=git)   # before EVERY wave
        w = plan["per_wave"][i]
        ext = external_dependencies(w["assets"], {a: plan["rows"][a].get("depends_on") or [] for a in w["assets"]})
        receipt = insert_run(connect, chart_id=args.chart_id, manifest=w["manifest"], digest=w["manifest_digest"],
                             row_digests={a: plan["row_digests"][a] for a in w["assets"]}, external=ext,
                             confirm=expected_confirmation(w["manifest_digest"], len(w["assets"]), force),
                             commit=True, footprint=False, on_commit=on_commit(i), meta=meta, force_execute=force)
        failure = send_or_terminalise(receipt)
        if failure is not None:
            raise LevelWaveRefusal([{"code": "DISPATCH_FAILED", "run_id": receipt["run_id"],
                                     "detail": receipt["dispatch_error"], "terminalise_warning": receipt["terminalise_warning"]}])
        return receipt

    result = run_wave_by_wave(
        plan, dispatch_wave=dispatch_wave,
        wait_terminal=lambda rid: wait_for_terminal_run(connect, rid, poll_seconds=args.poll_seconds,
                                                        timeout_seconds=args.wave_timeout_seconds, sleep=sleep, monotonic=monotonic),
        wave_report=lambda rid: _safe_wall_time_report(connect, rid, plan["waves"]),
        hook=the_hook, emit=emit,
        declared_skips=[x for x in (args.declared_skips or "").split(",") if x])
    summary["wave_by_wave"] = result
    summary["committed"] = bool(committed)
    if force:
        # every wave asset reached disposition 'build' (a skip_no_delta stops the campaign), or the campaign did not finish
        summary["forced_effective"] = True if result["status"] == "ALL_WAVES_COMPLETED" else "not_verified"
    _emit(out, "summary", **summary)
    if result["status"] == "ALL_WAVES_COMPLETED":
        return 0
    last_refusals = (result["waves"][-1].get("refusals") or []) if result["waves"] else []
    if result["status"] == "STOPPED_REFUSED" and any(r.get("code") == "DISPATCH_FAILED" for r in last_refusals):
        return EXIT_DISPATCH_FAILED          # documented: dispatch failed after the run was committed (3), like single-run
    return EXIT_UNEXPECTED if result["status"] == "STOPPED_ERROR" else EXIT_CAMPAIGN_STOPPED


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return EXIT_NO_DATABASE_URL
    def _term(signum, frame):  # noqa: ARG001
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    return run_cli(args, connect=_psycopg_connect_factory(database_url))


if __name__ == "__main__":
    raise SystemExit(main())
