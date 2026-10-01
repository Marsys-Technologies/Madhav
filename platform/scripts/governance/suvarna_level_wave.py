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
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "suvarna.e5_9.transitive_footprint/2"
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
            lines.append(f"  {title} (0 found in the edges supplied; not a clean reading while INCOMPLETE)")

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


def expected_confirmation(digest: str, n_assets: int) -> str:
    """`--confirm` token: the existing `<SUBJECT>_FROZEN_REBUILD` convention with the subject bound to the manifest, so a
    token from one dry run can not confirm a different manifest (a registry change moves the digest and the token)."""
    return f"{n_assets}ASSETS_{digest[:12].upper()}_FROZEN_REBUILD"


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
               footprint: bool = False, on_commit=None, meta: Mapping[str, Any] | None = None) -> dict:
    """One transaction: advisory lock, active-run refusal, registry-row re-read and compare, external dependencies
    lit+fresh, INSERT build_runs + build_run_assets, then ROLLBACK (dry run) or COMMIT (only with the exact token).

    The re-read happens in THIS transaction, after the manifest was built from an earlier, separate read, so a registry
    change in between is visible (a repeated read inside one SERIALIZABLE snapshot could not show it).
    `on_commit(receipt)` is called the instant the COMMIT succeeds, before anything else can fail, so the caller always
    knows a run exists. `meta` is merged into the receipt (the deployed job sha is printed on every receipt)."""
    plan = [a for wave in manifest["waves"] for a in wave]
    token = expected_confirmation(digest, len(plan))
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


def _footprint_report(conn, rows_now: Sequence[Mapping[str, Any]]) -> dict:
    """E5.9 footprint of the wave's write tables (registry target_table); the loaders run SELECTs only."""
    edges = fk_edges_from_catalog(conn)
    tables = tables_from_catalog(conn)
    writes = sorted({r["target_table"] for r in rows_now if r.get("target_table")})
    if not writes:
        return {"status": "NO_TARGET_TABLES", "detail": "no asset in the set declares a target_table"}
    fp = transitive_footprint(writes, edges, known_tables=tables)
    return {"footprint": fp, "impact_lines": impact_statement_footprint_section(fp)}


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


def dispatch_run_with_timeout(*, run_id: str, project: str, region: str, job: str, run_command=subprocess.run,
                              timeout: float = GCLOUD_TIMEOUT_SECONDS) -> str:
    """The same `gcloud run jobs execute ... --async` command dispatch_frozen_rebuild.dispatch_run issues, with a timeout, no
    stdin and no prompts. After a timeout the execution may or may not have started: the caller terminalises the planned run
    (the runner refuses a run that is not planned/running), so a late start can not build anything."""
    try:
        result = run_command(
            ["gcloud", "run", "jobs", "execute", job, f"--project={project}", f"--region={region}",
             f"--args=--run-id,{run_id}", "--async", "--format=value(metadata.name)"],
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
    if args.job_sha_file:
        recheck_job_sha(args.repo, pinned_job_sha=pinned, job_sha_file=args.job_sha_file, git=git)
    meta = {"deployed_job_sha": pinned, "inventory_sha": binding["inventory_sha"]}

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
    token_full = expected_confirmation(plan["manifest_digest"], len(plan["plan"]))
    summary = {
        "schema": LEVEL_WAVE_SCHEMA, "never_executed_note": NEVER_EXECUTED_NOTE, "chart_id": args.chart_id, **meta,
        "job_sha_binding": binding["binding"], "family_ref": ref_status,
        "family_enforcement": "name_patterns_and_family_set" if family["state"] == "present" else "name_patterns_only",
        "live_dry_run_note": "the LIVE dry run is mandatory before the first --commit; the waves above are the live waves for "
                             "this registry, any README list is indicative",
        "asset_count": len(plan["plan"]), "waves": plan["waves"], "manifest_digest": plan["manifest_digest"],
        "confirm_token_single_run": token_full,
        "per_wave": [{"wave": w["wave"], "assets": w["assets"], "manifest_digest": w["manifest_digest"],
                      "confirm_token": expected_confirmation(w["manifest_digest"], len(w["assets"]))}
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
        send = dispatch or (lambda run_id: dispatch_run_with_timeout(run_id=run_id, project=args.project, region=args.region, job=args.job))

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
                             confirm=expected_confirmation(target["manifest_digest"], len(tgt)) if args.commit else None,
                             commit=args.commit, footprint=args.with_footprint, on_commit=on_commit(0), meta=meta)
        summary["insert"] = receipt
        summary["committed"] = receipt["committed"]
        if args.commit and send_or_terminalise(receipt) is not None:
            summary["dispatch_error"] = receipt["dispatch_error"]
            summary["terminalise_warning"] = receipt["terminalise_warning"]
            _emit(out, "summary", **summary)
            return EXIT_DISPATCH_FAILED
        if args.commit:
            summary["execution_name"] = receipt.get("execution_name")
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
                             confirm=expected_confirmation(w["manifest_digest"], len(w["assets"])),
                             commit=True, footprint=False, on_commit=on_commit(i), meta=meta)
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
