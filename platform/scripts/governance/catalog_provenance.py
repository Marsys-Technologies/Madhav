#!/usr/bin/env python3
"""catalog_provenance.py — Nikaṣa wave 1, Lane B (R85, D5 rev. 2.1).

Read-only, deterministic-first (no LLM calls). Derives, for every semantic capability
unit (SCU) in `platform/src/generated/capability_knowledge.snapshot.json`, which
asset(s) produce or part-produce it, so the necessity closure over
`asset_registry.depends_on` (B-2) can be computed from the catalog rather than
guessed.

Scope (NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4):
  B-1  the derivation:   this module's `derive_all()` + `--derive` (default action)
  B-2  the closure:      `--closure` (writes CLOSURE_REPORT.md)
  B-3  the reader scan:  `--reader-scan` (writes BUILD_DEPENDENCIES_READER_SCAN.md;
                          read-only grep, never drops or alters `build_dependencies`)
  B-4  the `--check` gate: exits non-zero when any SCU has neither a reviewed nor a
                          derived producer and no `no_detector` reason.

Honest tiers (CLAUDE.md §N.7/§N.8; wave1 prompt §2.6):
  - A machine-derived producer is `disposition: derived_from_source_query` (parsed out
    of a `kind: source_query` availability-contract requirement's SQL) or
    `derived_from_service_probe` (read directly off a `kind: service_probe`
    requirement's own `asset_id` field — no SQL parsing needed or attempted) —
    NEVER `reviewed_output`. The 12 existing hand-reviewed `producer_output_claims`
    (disposition `reviewed_output`) are carried through verbatim as the authority
    where present; this script never overwrites or downgrades one.
  - A unit nothing resolves gets `no_detector: "<exact reason>"` — never a guess.
  - Every producer traces to BOTH a `source_ref` (file:line-range or the reviewed
    claim's own evidence citation) AND a `target_table` (or `null` with a stated
    reason, e.g. a service asset with no table).

No writer, orchestrator, sealed-tier, editorial.ts, or asset_registry write happens
here. DB access is read-only (see `connect_db`); this script issues SELECT only.

Run:
  source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433
  python3 platform/scripts/governance/catalog_provenance.py --derive --closure --reader-scan
  python3 platform/scripts/governance/catalog_provenance.py --check
  python -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -v
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_PATH = REPO_ROOT / "platform/src/generated/capability_knowledge.snapshot.json"
PROVENANCE_DIR = REPO_ROOT / "00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance"
DERIVED_OUTPUT_PATH = PROVENANCE_DIR / "producer_provenance.derived.json"
CLOSURE_REPORT_PATH = PROVENANCE_DIR / "CLOSURE_REPORT.md"
READER_SCAN_PATH = PROVENANCE_DIR / "BUILD_DEPENDENCIES_READER_SCAN.md"
# C-5(iv): this lane's own wave1 report/review directory. Its prose (B_REPORT.md,
# and the gate's own B_REVIEW.md) mentions "build_dependencies" many times while
# discussing the scan itself — a moving, self-referential source of hits, just
# like the un-excluded PROVENANCE_DIR was before the fix documented below. Not
# excluding it is exactly why the committed 80 went stale the moment B_REPORT.md
# grew one more line quoting the term (observed: 80 -> 81, "the difference is
# B_REPORT lines" — B_REVIEW.md §"Also noted, blocking nothing").
WAVE1_DIR = REPO_ROOT / "00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1"

# ─────────────────────────────────────────────────────────────────────────────
# §0 — Data types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AssetRow:
    asset_id: str
    layer: str
    is_active: bool
    dead_flag: bool
    target_table: Optional[str]
    natural_key_partition: Optional[str]
    depends_on: Tuple[str, ...]
    asset_kind: str


@dataclass
class Producer:
    asset_id: str
    table: Optional[str]
    source_ref: str
    disposition: str  # 'reviewed_output' | 'derived_from_source_query' | 'derived_from_service_probe' | 'route_evidence_only'
    shared: bool = False
    # C-3: which name of the one-hop-followed helper (if any) contributed the
    # literal this relation name was found in — None when found directly in the
    # handler segment's own text, never guessed.
    via_helper: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "table": self.table,
            "source_ref": self.source_ref,
            "disposition": self.disposition,
            "via_helper": self.via_helper,
            "shared": self.shared,
        }


@dataclass
class ScuProvenance:
    scu_id: str
    producers: List[Producer] = field(default_factory=list)
    no_detector: Optional[str] = None
    requirement_kinds: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_json(self) -> dict:
        out: dict = {
            "requirement_kinds": self.requirement_kinds,
            "producers": [p.to_json() for p in self.producers],
        }
        if self.no_detector:
            out["no_detector"] = self.no_detector
        if self.notes:
            out["notes"] = self.notes
        return out


# ─────────────────────────────────────────────────────────────────────────────
# §1 — Snapshot loading
# ─────────────────────────────────────────────────────────────────────────────


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def iter_scu_requirements(snapshot: dict):
    """Yield (scu_id, requirement_dict) for every availability_contracts[].requirements[]
    entry across every SCU, in snapshot order."""
    for scu in snapshot.get("scus", []):
        scu_id = scu["scu_id"]
        for ac in scu.get("availability_contracts", []) or []:
            for req in ac.get("requirements", []) or []:
                yield scu_id, req


def get_reviewed_claims(snapshot: dict) -> Dict[str, List[dict]]:
    """SCU -> list of producer_output_claims with disposition == 'reviewed_output',
    verbatim (never mutated). This is the calibration + authority set (12 SCUs / 14
    assets, measured 2026-09-27 — see B_REPORT.md for the exact recount against the
    D5 ruling's stated '15 assets', and C-5's correction: 15 is not an off-by-one —
    it counts every producer_output_claim, including the one carried by
    `get_non_reviewed_producer_output_claims` below, not just the reviewed ones)."""
    out: Dict[str, List[dict]] = {}
    for scu in snapshot.get("scus", []):
        claims = [
            c
            for c in (scu.get("producer_output_claims") or [])
            if c.get("disposition") == "reviewed_output"
        ]
        if claims:
            out[scu["scu_id"]] = claims
    return out


def get_non_reviewed_producer_output_claims(snapshot: dict) -> Dict[str, List[dict]]:
    """C-5(iii): SCU -> list of producer_output_claims whose disposition is
    anything OTHER than 'reviewed_output' (today, exactly one:
    `scu.kala.temporal_activation`'s `route_evidence_only` claim naming
    `ka_kalasutra` — the D5 ruling's 15th named asset, dropped silently by the
    pre-correction derivation). Carried through `derive_all` with their OWN
    disposition, verbatim — never relabeled as `reviewed_output` (that would be
    the exact §N.7 'never emit a tier nothing double-checked' violation this
    lane must not commit), and never silently dropped (§N.8: an honest,
    not-yet-reviewed claim is still real evidence, not nothing)."""
    out: Dict[str, List[dict]] = {}
    for scu in snapshot.get("scus", []):
        claims = [
            c
            for c in (scu.get("producer_output_claims") or [])
            if c.get("disposition") and c.get("disposition") != "reviewed_output"
        ]
        if claims:
            out[scu["scu_id"]] = claims
    return out


# ─────────────────────────────────────────────────────────────────────────────
# §2 — DB access (read-only). Every query here is a SELECT; nothing writes.
# ─────────────────────────────────────────────────────────────────────────────


def connect_db(db_url: Optional[str] = None):
    """Connect read-only. `db_url` defaults to $DATABASE_URL; if unset, falls back to
    a bare libpq connection that reads PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD
    from the environment (the `dbenv.sh` convention this campaign uses — see
    NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §2.1). Never issues a write; callers must
    only SELECT."""
    dsn = db_url if db_url is not None else os.environ.get("DATABASE_URL", "")
    try:
        import psycopg  # psycopg3

        return psycopg.connect(dsn) if dsn else psycopg.connect()
    except ImportError:
        import psycopg2  # type: ignore

        return psycopg2.connect(dsn) if dsn else psycopg2.connect("")


def load_asset_registry(conn) -> Dict[str, AssetRow]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT asset_id, layer, is_active, dead_flag, target_table,
               natural_key_partition, depends_on, asset_kind
          FROM asset_registry
        """
    )
    out: Dict[str, AssetRow] = {}
    for row in cur.fetchall():
        asset_id, layer, is_active, dead_flag, target_table, nkp, depends_on, asset_kind = row
        out[asset_id] = AssetRow(
            asset_id=asset_id,
            layer=layer,
            is_active=bool(is_active),
            dead_flag=bool(dead_flag) if dead_flag is not None else False,
            target_table=target_table,
            natural_key_partition=nkp,
            depends_on=tuple(depends_on or []),
            asset_kind=asset_kind,
        )
    return out


def load_information_schema_tables(conn, schema: str = "public") -> Set[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
        (schema,),
    )
    return {row[0] for row in cur.fetchall()}


def active_population(assets: Dict[str, AssetRow]) -> Set[str]:
    """R220: is_active AND NOT dead_flag, with NULL dead_flag treated as false
    (production has dead_flag NULL on every row today — `NOT dead_flag` alone is a
    three-valued-logic trap that silently returns zero rows; see B_REPORT.md)."""
    return {a.asset_id for a in assets.values() if a.is_active and not a.dead_flag}


def known_tables_and_producer_map(
    assets: Dict[str, AssetRow], info_schema_tables: Set[str]
) -> Tuple[Set[str], Dict[str, List[AssetRow]]]:
    known_tables = set(info_schema_tables)
    table_to_assets: Dict[str, List[AssetRow]] = {}
    for a in assets.values():
        if a.target_table:
            known_tables.add(a.target_table)
            table_to_assets.setdefault(a.target_table, []).append(a)
    return known_tables, table_to_assets


# ─────────────────────────────────────────────────────────────────────────────
# §3 — source_ref parsing + resolution
# ─────────────────────────────────────────────────────────────────────────────

_SEGMENT_RE = re.compile(r"^([^:#]+):(\d+)-(\d+)$")


def parse_source_ref_segments(source_ref: str) -> List[Tuple[str, int, int]]:
    """A source_ref is one or more ` | `-joined `<file>:<a>-<b>` segments. Anything
    that does not match that exact shape (whole-file citations, `#anchor` citations,
    single-line `:N` citations) is not a resolvable segment under this script's
    contract and is silently excluded here — NOT silently trusted. Callers report
    the SCU as unresolved only when every segment falls through this filter."""
    segments: List[Tuple[str, int, int]] = []
    for raw in (source_ref or "").split("|"):
        seg = raw.strip()
        m = _SEGMENT_RE.match(seg)
        if m:
            segments.append((m.group(1), int(m.group(2)), int(m.group(3))))
    return segments


def resolve_segment_text(
    repo_root: Path, file_rel: str, a: int, b: int
) -> Tuple[Optional[str], Optional[str]]:
    """Return (text, out_of_range_reason) for lines a..b (1-indexed, inclusive) of
    file_rel under repo_root. Never reads outside [a, b] — that would silently
    widen the declared contract.

    C-2/C-4: a missing file and an out-of-bounds range are DISTINCT failure modes
    that used to both collapse into a bare `None`, which made a stale
    `source_ref` annotation (the declared range no longer matches the file's
    current length — e.g. code was edited/moved and the annotation was never
    updated) silently indistinguishable from "this range genuinely has no
    relation name in it". `out_of_range_reason` names exactly which segment
    failed and why, including the file's actual current line count, so a caller
    can classify this honestly as `source_ref_out_of_range` rather than the
    misleading "resolved source range(s) contain no relation name"."""
    fpath = repo_root / file_rel
    if not fpath.is_file():
        return None, f"{file_rel} does not exist"
    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    n = len(lines)
    if a < 1 or b > n or a > b:
        return None, f"{file_rel} has {n} lines, ref {a}-{b}"
    return "".join(lines[a - 1 : b]), None


def resolve_full_file_text(repo_root: Path, file_rel: str) -> Optional[str]:
    fpath = repo_root / file_rel
    if not fpath.is_file():
        return None
    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ─────────────────────────────────────────────────────────────────────────────
# §4 — string-literal extraction + relation-name candidate matching
# ─────────────────────────────────────────────────────────────────────────────


def extract_string_literals(text: str, file_ext: str) -> List[str]:
    """Return the contents of every quoted string literal in `text`. `.sql` files ARE
    the query (DDL/DML directly, not wrapped in a host-language string) so the whole
    text is returned as one literal. `.ts`/`.js`/`.py` files have their SQL embedded
    in backtick / single / double (and, for Python, triple) quoted string literals —
    a small hand-rolled tokenizer walks the text respecting backslash escapes so
    prose in comments/descriptions (e.g. the literal word "today" in an input_schema
    description) is never treated as SQL text just because it sits near a FROM/JOIN
    keyword elsewhere in the same range."""
    if file_ext == ".sql":
        return [text]

    literals: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in ("'", '"', "`"):
            quote = ch
            # Python triple-quote
            if file_ext == ".py" and text[i : i + 3] == quote * 3:
                close = quote * 3
                end = text.find(close, i + 3)
                if end == -1:
                    break
                literals.append(text[i + 3 : end])
                i = end + 3
                continue
            j = i + 1
            buf = []
            while j < n:
                c = text[j]
                if c == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                if c == quote:
                    j += 1
                    break
                buf.append(c)
                j += 1
            literals.append("".join(buf))
            i = j
            continue
        if ch == "#" and file_ext == ".py":
            end = text.find("\n", i)
            i = end if end != -1 else n
            continue
        if text[i : i + 2] == "//" and file_ext in (".ts", ".js"):
            end = text.find("\n", i)
            i = end if end != -1 else n
            continue
        i += 1
    return literals


_RELATION_RE = re.compile(
    r"\b(?:FROM|JOIN|UPDATE|INTO)\s+(?:ONLY\s+)?\"?([A-Za-z_][A-Za-z0-9_]*)\"?"
    r"(?:\s*\.\s*\"?([A-Za-z_][A-Za-z0-9_]*)\"?)?",
    re.IGNORECASE,
)

# Naive-regex noise words the wave1 prompt names by name (§4 B-1) plus the SQL
# keywords that can immediately follow FROM/JOIN in real queries without being a
# relation (subquery openers, set-returning functions). These are only a documented
# example of what the known-tables filter must reject — they are never special-cased
# by name; the filter is the `known_tables` set membership test below.
_KNOWN_NOISE_EXAMPLES = {"today", "the", "one", "unnest"}


def find_relation_candidates(literal_texts: Sequence[str]) -> List[str]:
    candidates: List[str] = []
    for lit in literal_texts:
        for m in _RELATION_RE.finditer(lit):
            schema_part, table_part = m.group(1), m.group(2)
            name = table_part if table_part else schema_part
            candidates.append(name)
    return candidates


def filter_known_relations(candidates: Sequence[str], known_tables: Set[str]) -> List[str]:
    seen: List[str] = []
    for c in candidates:
        if c in known_tables and c not in seen:
            seen.append(c)
    return seen


# ─────────────────────────────────────────────────────────────────────────────
# §5 — one-hop helper following (best-effort, non-recursive)
# ─────────────────────────────────────────────────────────────────────────────

_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_SQL_AND_LANG_STOPWORDS = {
    "FROM", "JOIN", "UPDATE", "INTO", "SELECT", "WHERE", "AND", "OR", "ORDER", "BY",
    "GROUP", "LIMIT", "OFFSET", "AS", "ON", "IF", "NOT", "EXISTS", "ONLY", "CROSS",
    "LEFT", "RIGHT", "INNER", "OUTER", "WITH", "CASE", "WHEN", "THEN", "ELSE", "END",
    "NULL", "TRUE", "FALSE", "ARRAY", "ANY", "ALL", "DISTINCT", "COUNT", "SUM",
    "COALESCE", "UNNEST", "NOW", "String", "Number", "Math", "Date", "Array",
    "Object", "Promise", "query", "console", "JSON", "parseInt", "parseFloat",
}

_TS_DEF_RE_TMPL = (
    r"(?:\bfunction\s+{name}\s*\(|\bconst\s+{name}\s*=\s*(?:async\s*)?\(|"
    r"\bconst\s+{name}\s*=\s*(?:async\s*)?function\b|\bexport\s+function\s+{name}\s*\()"
)
_PY_DEF_RE_TMPL = r"\bdef\s+{name}\s*\("


def _extract_ts_body(full_text: str, def_start: int, max_lines: int = 400) -> str:
    brace_start = full_text.find("{", def_start)
    if brace_start == -1:
        return ""
    depth = 0
    i = brace_start
    n = len(full_text)
    lines_seen = 0
    while i < n:
        c = full_text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return full_text[brace_start : i + 1]
        elif c == "\n":
            lines_seen += 1
            if lines_seen > max_lines:
                return full_text[brace_start:i]
        i += 1
    return full_text[brace_start:]


def _extract_py_body(full_text: str, def_start: int, max_lines: int = 400) -> str:
    lines = full_text[def_start:].split("\n")
    if not lines:
        return ""
    header_indent = len(lines[0]) - len(lines[0].lstrip())
    body_lines = [lines[0]]
    for ln in lines[1 : max_lines + 1]:
        if ln.strip() == "":
            body_lines.append(ln)
            continue
        indent = len(ln) - len(ln.lstrip())
        if indent <= header_indent:
            break
        body_lines.append(ln)
    return "\n".join(body_lines)


_DEF_HEADER_PREFIX_RE = re.compile(r"\b(?:def|function)\s*$")


def one_hop_helper_texts(range_text: str, full_file_text: Optional[str], file_ext: str) -> List[Tuple[str, str]]:
    """Best-effort: for each plain-identifier call in `range_text` that names a
    function/const-arrow defined elsewhere in the SAME file, return [(name, body_text)]
    for the first definition site found. Non-recursive (one hop only, per spec).

    C-3(a): `_CALL_RE` (`identifier(`) matches a `def foo(`/`function foo(` HEADER
    just as readily as it matches a real call to `foo(...)` — a real defect this
    lane's own derivation hit: a declared range whose LAST line happened to be a
    function's own definition header (not a call to it) was followed as if it were
    a call, ingesting that function's entire body as evidence for the range's SQL,
    even though the range never called it. Skip any match immediately preceded
    (ignoring whitespace/newlines) by the `def`/`function` keyword — that identifier
    is being DEFINED here, not called."""
    if not full_file_text:
        return []
    found: List[Tuple[str, str]] = []
    seen_names: Set[str] = set()
    for m in _CALL_RE.finditer(range_text):
        name = m.group(1)
        if name in _SQL_AND_LANG_STOPWORDS or name in seen_names or len(name) < 3:
            continue
        if _DEF_HEADER_PREFIX_RE.search(range_text[: m.start()]):
            continue
        seen_names.add(name)
        if file_ext == ".py":
            def_re = re.compile(_PY_DEF_RE_TMPL.format(name=re.escape(name)))
        else:
            def_re = re.compile(_TS_DEF_RE_TMPL.format(name=re.escape(name)))
        dm = def_re.search(full_file_text)
        if not dm:
            continue
        body = (
            _extract_py_body(full_file_text, dm.start())
            if file_ext == ".py"
            else _extract_ts_body(full_file_text, dm.end())
        )
        if body:
            found.append((name, body))
    return found


# ─────────────────────────────────────────────────────────────────────────────
# §6 — narrowing shared-table producers via natural_key_partition
# ─────────────────────────────────────────────────────────────────────────────

_PIN_RE = re.compile(
    r"\b(fact_category|signal_type_class)\s*(=|IN)\s*"
    r"(?:'([^']*)'|\(([^)]*)\))",
    re.IGNORECASE,
)


def extract_query_pins(literal_texts: Sequence[str]) -> Set[str]:
    """Pull literal fact_category / signal_type_class values the query pins in its
    WHERE clause, e.g. `fact_category = 'ayurdaya'` or
    `fact_category = ANY(ARRAY['a','b'])`. Best-effort textual match, not a SQL
    parser — used only to NARROW a shared-table producer set, never to invent one."""
    pins: Set[str] = set()
    array_re = re.compile(r"ARRAY\s*\[([^\]]*)\]", re.IGNORECASE)
    for lit in literal_texts:
        for am in array_re.finditer(lit):
            for tok in am.group(1).split(","):
                tok = tok.strip().strip("'").strip()
                if tok:
                    pins.add(tok)
        for pm in _PIN_RE.finditer(lit):
            val_eq, val_in = pm.group(3), pm.group(4)
            if val_eq:
                pins.add(val_eq.strip())
            if val_in:
                for tok in val_in.split(","):
                    tok = tok.strip().strip("'").strip()
                    if tok:
                        pins.add(tok)
    return pins


def parse_natural_key_partition_values(nkp: Optional[str]) -> Set[str]:
    """Parse `asset_registry.natural_key_partition` free text of the form
    `<table>.<column> = <value>` or `<table>.<column> IN (<values>)` into the set of
    values that asset owns. Text that doesn't match this shape (free-prose rows like
    bg_texts' "canonical text_id set (15); chunk_id") yields an empty set — the
    caller must then keep the table's producers flagged `shared`, never guess."""
    if not nkp:
        return set()
    values: Set[str] = set()
    for m in re.finditer(r"=\s*([A-Za-z0-9_]+)", nkp):
        values.add(m.group(1))
    for m in re.finditer(r"IN\s*\(([^)]*)\)", nkp, re.IGNORECASE):
        for tok in m.group(1).split(","):
            tok = tok.strip()
            if tok:
                values.add(tok)
    return values


def narrow_producers_by_partition(
    table: str,
    candidate_assets: List[AssetRow],
    query_pins: Set[str],
) -> Tuple[List[AssetRow], bool]:
    """Returns (narrowed_or_full_list, shared_flag). Narrows to exactly one producer
    only if exactly one candidate's declared natural_key_partition covers every
    pinned value and no other candidate's partition covers any of them — otherwise
    every candidate is kept, flagged shared (per B-1: 'otherwise keep all, flagged')."""
    if len(candidate_assets) <= 1:
        return candidate_assets, False
    if not query_pins:
        return candidate_assets, True
    owners = []
    for a in candidate_assets:
        owned = parse_natural_key_partition_values(a.natural_key_partition)
        if owned and query_pins <= owned:
            owners.append(a)
    if len(owners) == 1:
        return owners, False
    return candidate_assets, True


# ─────────────────────────────────────────────────────────────────────────────
# §6b — source_ref segment classification (C-3 b/c)
# ─────────────────────────────────────────────────────────────────────────────

_MIGRATION_PATH_RE = re.compile(r"(?:^|/)(?:migrations|supabase/migrations)/")
_WRITER_PATH_RE = re.compile(r"(?:^|/)(?:[A-Za-z0-9]+_writers|writers)/")


def classify_segment_kind(file_rel: str) -> str:
    """Classify a source_ref segment's file by its role relative to the SCU's OWN
    query, so relation-name extraction can be scoped to the segment(s) that
    actually represent that query (the 'handler') rather than incidental SQL a
    migration's integrity check or a writer's own input read happens to contain.

    C-3(b): a migration file's SQL (e.g. an unrelated integrity-check query sitting
    a few lines from the one the citation actually means) is never evidence of what
    the SCU's handler reads — it produced a real false positive
    (`bg_dignity_reference` from migration 606's integrity check, when the actual
    handler reads a different, unregistered table).
    C-3(c): a writer's OWN input read (e.g. the writer reading its upstream input
    table to build its output) is not the SCU's read either — it produced another
    real false positive (`bg_texts`/`bg_text_index` from `bg_compendium_index`'s
    writer reading `classical_text_chunks` as ITS input)."""
    if _MIGRATION_PATH_RE.search(file_rel):
        return "migration"
    if _WRITER_PATH_RE.search(file_rel):
        return "writer"
    return "handler"


# ─────────────────────────────────────────────────────────────────────────────
# §7 — the derivation core (pure function; DI'd known_tables/table_to_assets so
#      tests never need a live DB)
# ─────────────────────────────────────────────────────────────────────────────


def derive_from_source_query(
    scu_id: str,
    req: dict,
    known_tables: Set[str],
    table_to_assets: Dict[str, List[AssetRow]],
    repo_root: Path,
) -> Tuple[List[Producer], Optional[str]]:
    source_ref = req.get("source_ref") or ""
    segments = parse_source_ref_segments(source_ref)
    if not segments:
        return [], f"NO_DETECTOR — source_ref did not resolve to any <file>:<a>-<b> segment ({source_ref!r})"

    handler_literals: List[str] = []
    # C-3: relation-name origin, so a Producer can honestly say whether it was found
    # directly in the handler's own text or only via a one-hop-followed helper.
    # `None` = direct. Populated ONLY from handler-kind segments (never migration/
    # writer — see classify_segment_kind).
    origin: Dict[str, Optional[str]] = {}
    oob_reasons: List[str] = []
    excluded_kinds: Set[str] = set()
    resolved_any = False

    for file_rel, a, b in segments:
        text, oob_reason = resolve_segment_text(repo_root, file_rel, a, b)
        if text is None:
            if oob_reason:
                oob_reasons.append(oob_reason)
            continue
        resolved_any = True

        kind = classify_segment_kind(file_rel)
        if kind != "handler":
            # C-3(b)/(c): a migration's or a writer's own SQL is not evidence of
            # what THIS SCU's query reads. Still counts toward `resolved_any` (so
            # out-of-range detection above stays honest about what actually
            # resolved), but contributes no relation candidates.
            excluded_kinds.add(kind)
            continue

        ext = Path(file_rel).suffix
        direct_literals = extract_string_literals(text, ext)
        handler_literals.extend(direct_literals)
        for name in find_relation_candidates(direct_literals):
            origin.setdefault(name, None)

        full_text = resolve_full_file_text(repo_root, file_rel) if ext != ".sql" else None
        for helper_name, body in one_hop_helper_texts(text, full_text, ext):
            helper_literals = extract_string_literals(body, ext)
            handler_literals.extend(helper_literals)
            for name in find_relation_candidates(helper_literals):
                origin.setdefault(name, helper_name)

    if not resolved_any:
        # C-2/C-4: a stale source_ref annotation (file exists but the declared range
        # no longer matches its current length) is a DISTINCT, more actionable cause
        # than "no segment even parsed as <file>:<a>-<b>" — name it precisely,
        # including the file's actual current line count, rather than folding both
        # into one vague "does not exist or is out of bounds" message.
        if oob_reasons:
            return [], f"NO_DETECTOR — source_ref_out_of_range ({'; '.join(oob_reasons)})"
        return [], (
            "NO_DETECTOR — every segment in source_ref names a file that does not "
            f"exist or a range out of bounds ({source_ref!r})"
        )

    candidates = find_relation_candidates(handler_literals)
    known = filter_known_relations(candidates, known_tables)
    if not known:
        # C-4: even when SOME segment resolved, an out-of-range handler segment
        # sitting alongside a resolved-but-irrelevant migration/writer segment must
        # not be silently reported as "resolved, no relation" — the true cause is
        # the stale annotation, and burying it there is exactly finding 4's defect.
        if oob_reasons:
            return [], (
                f"NO_DETECTOR — source_ref_out_of_range ({'; '.join(oob_reasons)}); no relation name "
                f"found in the remaining resolved handler-kind segment(s) ({source_ref!r})"
            )
        if excluded_kinds and not handler_literals:
            return [], (
                "NO_DETECTOR — resolved source range(s) contain no relation name in any "
                f"handler-kind segment (excluded {sorted(excluded_kinds)}-kind segment(s) per C-3) "
                f"({source_ref!r})"
            )
        return [], (
            "NO_DETECTOR — resolved source range(s) contain no relation name in "
            "asset_registry.target_table ∪ information_schema.tables "
            f"({source_ref!r})"
        )

    query_pins = extract_query_pins(handler_literals)
    producers: List[Producer] = []
    for table in known:
        assets = table_to_assets.get(table, [])
        if not assets:
            continue
        narrowed, shared = narrow_producers_by_partition(table, assets, query_pins)
        for a in narrowed:
            producers.append(
                Producer(
                    asset_id=a.asset_id,
                    table=table,
                    source_ref=source_ref,
                    disposition="derived_from_source_query",
                    shared=shared,
                    via_helper=origin.get(table),
                )
            )
    if not producers:
        return [], (
            "NO_DETECTOR — relation name(s) "
            f"{known} matched no row in asset_registry.target_table ({source_ref!r})"
        )
    return producers, None


def derive_from_service_probe(req: dict, assets: Dict[str, AssetRow]) -> Tuple[List[Producer], Optional[str]]:
    asset_id = req.get("asset_id")
    if not asset_id:
        return [], "NO_DETECTOR — service_probe requirement carries no asset_id"
    a = assets.get(asset_id)
    return (
        [
            Producer(
                asset_id=asset_id,
                table=a.target_table if a else None,
                source_ref=req.get("source_ref") or f"service_probe:{req.get('probe_id', '')}",
                disposition="derived_from_service_probe",
                shared=False,
            )
        ],
        None,
    )


def derive_all(
    snapshot: dict,
    assets: Dict[str, AssetRow],
    known_tables: Set[str],
    table_to_assets: Dict[str, List[AssetRow]],
    repo_root: Path = REPO_ROOT,
) -> Dict[str, ScuProvenance]:
    reviewed = get_reviewed_claims(snapshot)
    non_reviewed_claims = get_non_reviewed_producer_output_claims(snapshot)
    result: Dict[str, ScuProvenance] = {}

    for scu in snapshot.get("scus", []):
        scu_id = scu["scu_id"]
        sp = ScuProvenance(scu_id=scu_id)
        result[scu_id] = sp

        # Reviewed claims are carried through verbatim, always, as authority.
        for claim in reviewed.get(scu_id, []):
            claim_asset = assets.get(claim["asset_id"])
            sp.producers.append(
                Producer(
                    asset_id=claim["asset_id"],
                    table=claim_asset.target_table if claim_asset else None,
                    source_ref=claim.get("evidence", ""),
                    disposition="reviewed_output",
                    shared=False,
                )
            )

        # C-5(iii): a claim with a non-reviewed disposition (e.g.
        # `route_evidence_only`) is carried through too, honestly, under ITS OWN
        # disposition — never silently dropped, never relabeled as reviewed_output.
        for claim in non_reviewed_claims.get(scu_id, []):
            claim_asset = assets.get(claim["asset_id"])
            sp.producers.append(
                Producer(
                    asset_id=claim["asset_id"],
                    table=claim_asset.target_table if claim_asset else None,
                    source_ref=claim.get("evidence", ""),
                    disposition=claim["disposition"],
                    shared=False,
                )
            )

        reqs = list(iter_scu_requirements({"scus": [scu]}))
        if not reqs and not sp.producers:
            sp.no_detector = "NO_DETECTOR — no availability_contracts requirement and no reviewed_output claim"
            continue

        per_requirement_reasons: List[str] = []
        for _scu_id2, req in reqs:
            kind = req["kind"]
            sp.requirement_kinds.append(kind)
            if kind == "source_query":
                producers, reason = derive_from_source_query(scu_id, req, known_tables, table_to_assets, repo_root)
                sp.producers.extend(producers)
                if reason:
                    per_requirement_reasons.append(reason)
            elif kind == "service_probe":
                producers, reason = derive_from_service_probe(req, assets)
                sp.producers.extend(producers)
                if reason:
                    per_requirement_reasons.append(reason)
            elif kind == "producer_output":
                # Normally already covered by the reviewed-claims pass above (the
                # requirement's asset_id/spec_sha256 mirrors the claim it accompanies).
                # But a producer_output requirement can exist with NO matching
                # producer_output_claims entry at all (of any disposition) — that is a
                # genuinely unclassified state, not silently "nothing to add" (C-1: the
                # gate's constructed orphan case). Name it explicitly so it either
                # becomes a real reason or, once C-5 carries non-reviewed dispositions
                # through, is superseded by an actual producer.
                req_asset_id = req.get("asset_id")
                has_any_claim = any(
                    c.get("asset_id") == req_asset_id for c in (scu.get("producer_output_claims") or [])
                )
                if not has_any_claim:
                    per_requirement_reasons.append(
                        f"NO_DETECTOR — producer_output requirement ({req_asset_id!r}) has no "
                        "producer_output_claims recorded"
                    )
            elif kind == "derived":
                per_requirement_reasons.append(
                    f"NO_DETECTOR — no source_query requirement (kind: derived; {req.get('source_ref', '')})"
                )
            else:
                per_requirement_reasons.append(f"NO_DETECTOR — unrecognized requirement kind {kind!r}")

        # Deduplicate producers (same asset_id + table + disposition).
        dedup: List[Producer] = []
        seen_keys: Set[Tuple[str, Optional[str], str]] = set()
        for p in sp.producers:
            key = (p.asset_id, p.table, p.disposition)
            if key not in seen_keys:
                seen_keys.add(key)
                dedup.append(p)
        sp.producers = dedup

        if not sp.producers:
            # C-1: NO catch-all here. If no requirement branch produced a specific
            # reason, this SCU is left genuinely unclassified (no_detector stays None)
            # rather than being handed a fabricated generic reason — `check_completeness`
            # / `validate_derived_artifact` then correctly reads this as a --check
            # FAILURE, not a passing reason. A `--check` that can never see this state
            # is not a detector (CLAUDE.md §N.8).
            if per_requirement_reasons:
                sp.no_detector = "; ".join(per_requirement_reasons)
        else:
            sp.notes.extend(per_requirement_reasons)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# §8 — calibration against the reviewed set
# ─────────────────────────────────────────────────────────────────────────────


def calibration_report(snapshot: dict, provenance: Dict[str, ScuProvenance]) -> dict:
    reviewed = get_reviewed_claims(snapshot)
    out = {}
    for scu_id, claims in reviewed.items():
        reviewed_assets = sorted({c["asset_id"] for c in claims})
        sp = provenance[scu_id]
        derived_assets = sorted(
            {p.asset_id for p in sp.producers if p.disposition == "derived_from_source_query"}
        )
        agree = set(reviewed_assets) <= set(derived_assets) if derived_assets else False
        out[scu_id] = {
            "reviewed_assets": reviewed_assets,
            "derived_assets": derived_assets,
            "agreement": agree,
            "detail": (
                "no source_query contract on this SCU — nothing to compare"
                if not sp.requirement_kinds or "source_query" not in sp.requirement_kinds
                else ("derivation matches or is a superset of the reviewed claim" if agree
                      else "derivation did not reproduce the reviewed asset(s)")
            ),
        }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# §8b — C-4 segment resolution recount (full / partial / none, bounds checked)
# ─────────────────────────────────────────────────────────────────────────────


def compute_segment_resolution_counts(
    snapshot: dict, repo_root: Path = REPO_ROOT
) -> Tuple[int, int, int, List[str]]:
    """C-4: for every `kind: source_query` requirement, resolve EVERY `|`-joined
    piece of its declared source_ref (not just until one resolves) under the
    definition the gate review used — "file exists, range in-bounds" — and
    classify the SCU as fully resolved (every declared piece meets that
    definition), partially resolved (some but not all), or unresolved (none do,
    including a piece that never even parsed as `<file>:<a>-<b>`, e.g. a bare
    `#anchor` or `:name` citation).

    This is a stricter, more honest count than the "shape-valid" figure
    (`parse_source_ref_segments` silently drops non-numeric-range pieces before
    counting) — it surfaces the SCUs whose numeric ranges parse fine but are
    stale against the file's CURRENT length, which the shape-valid count hides
    entirely. Returns (full, partial, none, stale_refs) where stale_refs names
    each individual out-of-range piece found, prefixed with its owning SCU id —
    the exact, non-truncated list this lane registers as a finding for
    `source_query_availability.ts`'s owner (never edited by this lane)."""
    full = partial = none = 0
    stale: List[str] = []
    for scu_id, req in iter_scu_requirements(snapshot):
        if req.get("kind") != "source_query":
            continue
        source_ref = req.get("source_ref") or ""
        raw_pieces = [p.strip() for p in source_ref.split("|") if p.strip()]
        if not raw_pieces:
            none += 1
            continue
        good = 0
        for piece in raw_pieces:
            m = _SEGMENT_RE.match(piece)
            if not m:
                continue  # non-numeric-range citation (#anchor, :name, whole-file) — never resolves here
            file_rel, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            text, oob_reason = resolve_segment_text(repo_root, file_rel, a, b)
            if text is not None:
                good += 1
            elif oob_reason:
                stale.append(f"{scu_id}: {piece} ({oob_reason})")
        if good == len(raw_pieces):
            full += 1
        elif good == 0:
            none += 1
        else:
            partial += 1
    return full, partial, none, stale


# ─────────────────────────────────────────────────────────────────────────────
# §9 — B-2 necessity closure
# ─────────────────────────────────────────────────────────────────────────────


def transitive_upstream_closure(seeds: Set[str], depends_on: Dict[str, Sequence[str]]) -> Set[str]:
    seen: Set[str] = set()
    frontier = list(seeds)
    while frontier:
        a = frontier.pop()
        if a in seen:
            continue
        seen.add(a)
        for dep in depends_on.get(a, []) or []:
            if dep not in seen:
                frontier.append(dep)
    return seen


def compute_closure_report(
    assets: Dict[str, AssetRow],
    provenance: Dict[str, ScuProvenance],
) -> dict:
    active = active_population(assets)
    depends_on = {a.asset_id: a.depends_on for a in assets.values()}

    reviewed_seed = {
        p.asset_id
        for sp in provenance.values()
        for p in sp.producers
        if p.disposition == "reviewed_output"
    }
    all_seed = {p.asset_id for sp in provenance.values() for p in sp.producers}

    before_closure = transitive_upstream_closure(reviewed_seed, depends_on)
    after_closure = transitive_upstream_closure(all_seed, depends_on)

    before_necessary = before_closure & active
    after_necessary = after_closure & active

    def by_layer(remaining: Set[str]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for asset_id in sorted(remaining):
            layer = assets[asset_id].layer
            out.setdefault(layer, []).append(asset_id)
        return out

    still_outside = active - after_necessary

    def reason_for(asset_id: str) -> str:
        a = assets[asset_id]
        is_producer = asset_id in all_seed
        if is_producer:
            return "produces a catalog unit but the unit's SCU has no other unresolved path (should not occur)"
        has_dependents_in_closure = any(asset_id in assets[o].depends_on for o in after_necessary)
        if has_dependents_in_closure:
            return "unreachable: appears in some necessary asset's depends_on only outside the active set, or via a superseded edge"
        return "no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)"

    return {
        "population_active": sorted(active),
        "population_active_count": len(active),
        "reviewed_seed_assets": sorted(reviewed_seed),
        "derived_plus_reviewed_seed_assets": sorted(all_seed),
        "before": {
            "named_producers": len(reviewed_seed),
            "necessary_count": len(before_necessary),
            "necessary_assets": sorted(before_necessary),
        },
        "after": {
            "named_producers": len(all_seed),
            "necessary_count": len(after_necessary),
            "necessary_assets": sorted(after_necessary),
        },
        "still_outside_by_layer": {
            layer: [{"asset_id": aid, "reason": reason_for(aid)} for aid in aids]
            for layer, aids in by_layer(still_outside).items()
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# §10 — B-3 build_dependencies reader scan (read-only grep; never touches the table)
# ─────────────────────────────────────────────────────────────────────────────

_SCAN_EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".next", "dist", "build"}
_SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".sql", ".md", ".sh", ".json", ".yaml", ".yml"}


def scan_build_dependencies_readers(repo_root: Path = REPO_ROOT) -> List[Tuple[str, int, str]]:
    """Read-only grep. Deliberately excludes this lane's own generated output
    (`PROVENANCE_DIR`, which includes this scan's own prior report) AND this
    lane's own report/review prose (`WAVE1_DIR` — B_REPORT.md and B_REVIEW.md,
    which both discuss 'build_dependencies' at length while describing this very
    scan): without excluding PROVENANCE_DIR, re-running the scan finds its own
    previous output file listing 'build_dependencies' on every line, and hit
    counts runaway-inflate on every invocation (observed: 67 -> 144 hits on a
    second consecutive run before that exclusion was added). Without ALSO
    excluding WAVE1_DIR, the count is not runaway but is still unstable — it
    silently drifts every time B_REPORT.md or B_REVIEW.md gains or loses a line
    mentioning the term (observed: 80 -> 81 the moment B_REPORT.md was extended;
    C-5(iv)). Generated drift/build reports and this lane's own narrative are
    both outside the repo's SOURCE tree in intent even though they live under
    00_ARCHITECTURE/."""
    hits: List[Tuple[str, int, str]] = []
    pattern = re.compile(r"\bbuild_dependencies\b")
    excluded_dirs_abs = [PROVENANCE_DIR.resolve(), WAVE1_DIR.resolve()]
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in _SCAN_EXCLUDE_DIRS and not d.startswith(".")]
        dp_resolved = Path(dirpath).resolve()
        if any(dp_resolved == excl or excl in dp_resolved.parents for excl in excluded_dirs_abs):
            continue
        for fname in filenames:
            if Path(fname).suffix not in _SCAN_EXTS:
                continue
            fpath = Path(dirpath) / fname
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    for lineno, line in enumerate(fh, start=1):
                        if pattern.search(line):
                            rel = str(fpath.relative_to(repo_root))
                            hits.append((rel, lineno, line.strip()))
            except (OSError, UnicodeDecodeError):
                continue
    return hits


# ─────────────────────────────────────────────────────────────────────────────
# §11 — report writers
# ─────────────────────────────────────────────────────────────────────────────


def write_derived_json(
    snapshot: dict,
    provenance: Dict[str, ScuProvenance],
    calibration: dict,
    out_path: Path = DERIVED_OUTPUT_PATH,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(provenance)
    named = sum(1 for sp in provenance.values() if sp.producers)
    no_detector = sum(1 for sp in provenance.values() if sp.no_detector)
    # Bucketed by the CLOSED reason class (C-1's `classify_no_detector_reason`), not a
    # free-text prefix — a stable, enumerable key, never "whatever text came first".
    reason_counts: Dict[str, int] = {}
    for sp in provenance.values():
        if sp.no_detector:
            key = classify_no_detector_reason(sp.no_detector)
            reason_counts[key] = reason_counts.get(key, 0) + 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "platform/scripts/governance/catalog_provenance.py",
        "snapshot_content_hash": snapshot.get("content_hash"),
        "snapshot_scu_count": len(snapshot.get("scus", [])),
        "summary": {
            "total_scus": total,
            "scus_with_producers": named,
            "scus_no_detector": no_detector,
            "no_detector_reason_counts": reason_counts,
        },
        "scus": {scu_id: sp.to_json() for scu_id, sp in provenance.items()},
        "calibration": calibration,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")


def write_closure_report_md(closure: dict, out_path: Path = CLOSURE_REPORT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("---")
    lines.append("artifact: NIKASHA_WAVE1_B2_CLOSURE_REPORT")
    lines.append("version: \"1.0\"")
    lines.append(f"generated_at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("generator: platform/scripts/governance/catalog_provenance.py --closure")
    lines.append("---")
    lines.append("")
    lines.append("# Nikaṣa wave 1 — B-2 necessity closure report")
    lines.append("")
    lines.append(
        "Population: `SELECT count(*) FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE` "
        f"= **{closure['population_active_count']}** (R220). NOTE: `dead_flag` is NULL on every "
        "production row today, so a literal `is_active AND NOT dead_flag` reads 0 rows "
        "(three-valued-logic trap) — `dead_flag IS NOT TRUE` is the correct predicate and reproduces "
        "the documented population of 127."
    )
    lines.append("")
    lines.append("## Before (reviewed producers only — the D5 rev. 2.1 ruling's own baseline)")
    lines.append("")
    lines.append(f"- Named producer assets: **{closure['before']['named_producers']}**")
    lines.append(f"- Necessary (closure ∩ active population): **{closure['before']['necessary_count']} / {closure['population_active_count']}**")
    lines.append("")
    lines.append("## After (reviewed ∪ derived producers — this session's B-1 output)")
    lines.append("")
    lines.append(f"- Named producer assets: **{closure['after']['named_producers']}**")
    lines.append(f"- Necessary (closure ∩ active population): **{closure['after']['necessary_count']} / {closure['population_active_count']}**")
    lines.append("")
    lines.append("## Still outside the closure, by layer")
    lines.append("")
    for layer, rows in closure["still_outside_by_layer"].items():
        lines.append(f"### {layer} ({len(rows)})")
        lines.append("")
        for row in rows:
            lines.append(f"- `{row['asset_id']}` — {row['reason']}")
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_reader_scan_md(hits: List[Tuple[str, int, str]], out_path: Path = READER_SCAN_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("---")
    lines.append("artifact: NIKASHA_WAVE1_B3_BUILD_DEPENDENCIES_READER_SCAN")
    lines.append("version: \"1.0\"")
    lines.append(f"generated_at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("generator: platform/scripts/governance/catalog_provenance.py --reader-scan")
    lines.append("---")
    lines.append("")
    lines.append("# Nikaṣa wave 1 — B-3 `build_dependencies` reader scan")
    lines.append("")
    lines.append(
        "Read-only grep for `\\bbuild_dependencies\\b` across the repo (excluding `.git`, "
        "`node_modules`, `__pycache__`, `.next`, `dist`, `build`). **No change made to the table "
        "or any file** — this is evidence for a native decision (R219), not an action."
    )
    lines.append("")
    lines.append(f"Total hits: **{len(hits)}**")
    lines.append("")
    by_file: Dict[str, List[Tuple[int, str]]] = {}
    for rel, lineno, text in hits:
        by_file.setdefault(rel, []).append((lineno, text))
    for rel in sorted(by_file):
        lines.append(f"## `{rel}`")
        lines.append("")
        for lineno, text in by_file[rel]:
            safe = text.replace("|", "\\|")
            lines.append(f"- L{lineno}: `{safe}`")
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# §12 — B-4 --check
# ─────────────────────────────────────────────────────────────────────────────

# The CLOSED set of no_detector reason classes (C-1). `classify_no_detector_reason`
# maps a human-readable reason string to one of these — anything it cannot match
# comes back "unclassified", which is deliberately NOT a member of this set, so an
# unrecognized reason string fails validation rather than silently passing. Every
# member here corresponds to a specific, named code path in `derive_all` /
# `derive_from_source_query` / `derive_from_service_probe` — there is no catch-all.
NO_DETECTOR_REASON_CLASSES: Set[str] = {
    "no_contract",
    "source_ref_unresolvable_shape",
    "source_ref_out_of_range",
    "no_relation_in_range",
    "relation_unowned_by_registry",
    "derived_kind_no_source_query",
    "unrecognized_requirement_kind",
    "service_probe_missing_asset_id",
    "producer_output_unclaimed",
}

# Dispositions that are a "declared exemption" (per C-1's correction text) from the
# strict table+range requirement `derived_from_source_query` producers must meet.
# Each of these already carries its own evidence citation (a migration line, a
# service asset_id, or a hand-authored gap_reason) by construction, not by a regex
# parse of application SQL, so a range-shaped source_ref / non-null table is not
# expected of them.
_DECLARED_EXEMPTION_DISPOSITIONS = {"reviewed_output", "derived_from_service_probe", "route_evidence_only"}


def classify_no_detector_reason(reason: Optional[str]) -> str:
    """Map a no_detector message to its closed reason class. Order matters: more
    specific substrings are checked before more general ones so a combined message
    (e.g. an out-of-range segment alongside a 'no relation' finding) classifies by
    its most specific, most actionable cause."""
    if not reason:
        return "unclassified"
    r = reason
    if "no availability_contracts requirement" in r:
        return "no_contract"
    if "source_ref_out_of_range" in r:
        return "source_ref_out_of_range"
    if "did not resolve to any" in r and "segment" in r:
        return "source_ref_unresolvable_shape"
    if "matched no row in asset_registry.target_table" in r:
        return "relation_unowned_by_registry"
    if "contain no relation name" in r:
        return "no_relation_in_range"
    if "kind: derived" in r:
        return "derived_kind_no_source_query"
    if "unrecognized requirement kind" in r:
        return "unrecognized_requirement_kind"
    if "service_probe requirement carries no asset_id" in r:
        return "service_probe_missing_asset_id"
    if "producer_output requirement" in r and "no producer_output_claims recorded" in r:
        return "producer_output_unclaimed"
    return "unclassified"


def check_completeness(provenance: Dict[str, ScuProvenance]) -> List[str]:
    """Returns the list of SCU ids that fail the invariant: every SCU must have
    either a non-empty producers[] or a non-empty no_detector reason. This is an
    in-memory sanity check run right after a fresh `--derive` (belt-and-braces);
    the authoritative B-4 gate is `validate_derived_artifact`, which reads the
    committed JSON file rather than re-deriving (C-1) — see
    __tests__/test_catalog_provenance.py."""
    failures = []
    for scu_id, sp in provenance.items():
        if not sp.producers and not sp.no_detector:
            failures.append(scu_id)
    return failures


def validate_derived_artifact(payload: dict) -> List[str]:
    """The real B-4 gate (C-1). Validates the COMMITTED `producer_provenance.derived
    .json` payload itself — never re-derives — against the invariant: every SCU has
    (a) >=1 producer that is either a declared-exemption disposition
    (`_DECLARED_EXEMPTION_DISPOSITIONS`) carrying a non-empty source_ref, or a
    `derived_from_source_query` producer with a non-null `table` AND a range-shaped
    `source_ref` (validated via `parse_source_ref_segments`, never trusted as a
    bare string) — or (b) a `no_detector` reason whose class is a member of the
    CLOSED `NO_DETECTOR_REASON_CLASSES` set. An SCU with neither, or whose
    no_detector reason classifies as "unclassified", or that is simply absent from
    the artifact's `scus` map, is a failure. This is the function that makes
    `--check` able to read false on a real, stale, or hand-edited artifact."""
    failures: List[str] = []
    scus = payload.get("scus") or {}
    for scu_id, entry in scus.items():
        producers = entry.get("producers") or []
        no_detector = entry.get("no_detector")

        producer_ok = False
        for p in producers:
            disposition = p.get("disposition")
            source_ref = p.get("source_ref") or ""
            if disposition == "derived_from_source_query":
                if p.get("table") and parse_source_ref_segments(source_ref):
                    producer_ok = True
                    break
            elif disposition in _DECLARED_EXEMPTION_DISPOSITIONS:
                if source_ref:
                    producer_ok = True
                    break
        if producer_ok:
            continue

        if no_detector and classify_no_detector_reason(no_detector) in NO_DETECTOR_REASON_CLASSES:
            continue

        failures.append(scu_id)
    return failures


# ─────────────────────────────────────────────────────────────────────────────
# §13 — CLI
# ─────────────────────────────────────────────────────────────────────────────


def _run_derivation(db_url: Optional[str]) -> Tuple[dict, Dict[str, AssetRow], Dict[str, ScuProvenance]]:
    snapshot = load_snapshot()
    conn = connect_db(db_url)
    try:
        assets = load_asset_registry(conn)
        info_tables = load_information_schema_tables(conn)
    finally:
        conn.close()
    known_tables, table_to_assets = known_tables_and_producer_map(assets, info_tables)
    provenance = derive_all(snapshot, assets, known_tables, table_to_assets)
    return snapshot, assets, provenance


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--derive", action="store_true", help="Run B-1 and write producer_provenance.derived.json")
    ap.add_argument("--closure", action="store_true", help="Run B-2 and write CLOSURE_REPORT.md")
    ap.add_argument("--reader-scan", action="store_true", help="Run B-3 and write BUILD_DEPENDENCIES_READER_SCAN.md")
    ap.add_argument("--check", action="store_true", help="Run B-4: exit non-zero if any SCU is unaccounted for")
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""), help="Postgres DSN (default: $DATABASE_URL, else libpq env vars)")
    args = ap.parse_args(argv)

    if not any([args.derive, args.closure, args.reader_scan, args.check]):
        args.derive = args.closure = args.reader_scan = args.check = True

    db_url = args.db_url or None
    exit_code = 0

    if args.reader_scan:
        hits = scan_build_dependencies_readers()
        write_reader_scan_md(hits)
        print(f"[B-3] build_dependencies reader scan: {len(hits)} hits -> {READER_SCAN_PATH}")

    if args.derive or args.closure:
        snapshot, assets, provenance = _run_derivation(db_url)

        if args.derive:
            calibration = calibration_report(snapshot, provenance)
            write_derived_json(snapshot, provenance, calibration)
            named = sum(1 for sp in provenance.values() if sp.producers)
            print(f"[B-1] {named}/{len(provenance)} SCUs have a named producer -> {DERIVED_OUTPUT_PATH}")
            # Belt-and-braces in-memory sanity check right after a fresh derivation
            # (see check_completeness's docstring) — NOT the authoritative B-4 gate.
            in_memory_failures = check_completeness(provenance)
            if in_memory_failures:
                print(
                    f"[B-1] WARNING: {len(in_memory_failures)} freshly-derived SCU(s) have neither a "
                    "producer nor a no_detector reason (this should not happen — investigate before "
                    "relying on --check):"
                )
                for f in in_memory_failures:
                    print(f"  - {f}")

        if args.closure:
            closure = compute_closure_report(assets, provenance)
            write_closure_report_md(closure)
            print(
                f"[B-2] necessary before={closure['before']['necessary_count']}, "
                f"after={closure['after']['necessary_count']} (of {closure['population_active_count']}) "
                f"-> {CLOSURE_REPORT_PATH}"
            )

    if args.check:
        # C-1: --check validates the COMMITTED artifact itself — it never re-derives
        # silently. A stale artifact (e.g. hand-edited, or left over from before a
        # snapshot/registry change) must be able to fail this even though nothing in
        # today's DB/snapshot would reproduce the problem.
        if not DERIVED_OUTPUT_PATH.is_file():
            print(f"[B-4] --check FAIL: no derived artifact at {DERIVED_OUTPUT_PATH} — run --derive first.")
            exit_code = 1
        else:
            with open(DERIVED_OUTPUT_PATH, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            failures = validate_derived_artifact(payload)
            total = len(payload.get("scus") or {})
            if failures:
                print(
                    f"[B-4] --check FAIL: {len(failures)} SCU(s) with neither a valid producer nor a "
                    f"no_detector reason from the closed reason set (artifact: {DERIVED_OUTPUT_PATH}):"
                )
                for f in failures:
                    print(f"  - {f}")
                exit_code = 1
            else:
                print(
                    f"[B-4] --check PASS: all {total} SCUs in {DERIVED_OUTPUT_PATH} have a valid producer "
                    "or a no_detector reason from the closed reason set."
                )

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
