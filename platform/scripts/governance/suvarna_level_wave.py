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

import json
import re
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
# SECTION 2 -- E5.3 level-wave dispatcher (RESERVED: written by item E5.3, not by E5.9)
# ================================================================================================
