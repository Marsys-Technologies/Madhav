#!/usr/bin/env python3
"""Asset census — the `measured` half of the delta ledger, for a whole layer in one read-only pass.

WHY THIS EXISTS. The five L0 pilot briefs were measured by hand: a query for the alias census, a grep
for the writer contract, an arithmetic check for grid completeness, a count per asset's own count_sql.
Every one of those is scriptable, and hand-measuring 129 assets is how a campaign stalls. This script
measures; the brief renders what it measured; the author judges. That turns the remaining work from
authoring into reviewing, which is the only way a 129-asset ladder finishes.

WHAT IT MEASURES, per asset, against the tier-4 template's nine gates:

  Build.registered      exactly one @register('<asset_id>') and the registry agrees it has a writer
  Build.contract        WriterBase; run XOR plan_substeps+run_substep; never commits/closes ctx.db_conn;
                        never WRITES asset_throughput (a docstring promising not to is not a violation)
  Build.target          target_table declared, or the asset is a declared service (PASS by declaration) / multi-table
  Build.dag             every depends_on id is an active registry asset (every layer); the asset is on no dependency
                        cycle; the declared edges match what the
                        writer's SQL reads (reads-match, T4:275)
  Build.count_integrity count_sql present and integrity_check_sql present — each able to fail
  Build.completion      the build record agrees with the live count (rows_written=0 against a populated
                        table is a status with no measurement behind it)
  Earn.build_record     rows_per_second / last_built_at present — is the build instrumented at all
  Ldgr.source_presence  for a reference layer: the rows carry a citation column and it is populated
  Idem.pattern          the writer's idempotency pattern matches the layer convention (§N.3)
  Vocab.alias           per entity class, alias-set coverage (where the table has a synonyms column)
  Vocab.identity        uniqueness under the table's OWN DECLARED KEY, read from pg_constraint — never
                        an assumed key (native decision 16: the detector tests the declared key)
  Dens.served           which capability modules reference the target table; do they declare a
                        density_contract
  Complete.depth        per-column population census over the primary target table: columns fully
                        populated, columns NEVER populated
  Complete.width        the declared universe, if one exists — and it almost never does, so the honest
                        output is `universe_undeclared`, which is itself the first gap
  Cost.baseline         rows_written / rows_per_second / last_built_at

WHAT IT DOES NOT MEASURE, and says so rather than guessing: carriage detectors (D1/D2/D3 are per-asset
semantics) and width universes that are not declared anywhere. Those come out as `NOT_GENERIC` — a prompt
for the brief author, never a pass. Reachability at field level (`Reach.fields`, R23) is MEASURED — width
and depth over every capability module's SQL — but REPORTED, not graded: it stays `NOT_GENERIC`, so it
never opens or closes a gap.

FAIL-CLOSED. No database, no psql, or an unreadable registry exits 4 UNKNOWN and reports nothing clean.
An unreachable instrument is not a passing result (CLAUDE.md §N.8).

READ-ONLY. Catalog and content SELECTs only. `--emit-gaps` is the one write, and it appends to
00_ARCHITECTURE/control/asset_gaps.jsonl with deterministic ids (`<asset>-<criterion>`), skipping any id
already present, so re-running is idempotent and never disturbs a hand-written row.

Usage:
  asset_census.py --layer L0                 measure and print; writes the census JSON
  asset_census.py --layer L0 --emit-gaps     also append ledger rows for failures
  asset_census.py --layer all                every layer
  asset_census.py --layer L2 --assets bo_a,bo_b [--emit-gaps] [--rollup]
                                             E1.9: measure (and emit for) ONLY those assets — comma list, repeated flag
                                             or @file; validated against the layer's active registry. The output is
                                             labelled SCOPED (`scope: {assets, partial: true}` in the file, layer and
                                             rollup headers), goes to asset_census_scoped.json unless --out names
                                             another file (never the full census file), and is refused by anything that
                                             needs the whole population (`require_full_census` / `load_full_census`).
  asset_census.py --layer L0 --rollup        also write the nine-gate cells per asset (key `rollup`) and the
                                             non-nine gates as information (`rollup_excluded`) into the census JSON
Exit: 0 clean · 2 failures measured · 3 only NOT_GENERIC/undeclared items · 4 unknown · 5 script error, or
      --rollup failed (census still written, without it; the measured exit is named on stderr, never lost).
      6 bad --assets scope (empty / duplicate / miscased / unknown / wrong layer / retired id, or --out naming the
      full census file) — nothing measured, nothing written.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import collections
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            .stdout.strip() or ".")
# R57/P3: ledger directory is overridable so a sandbox --emit-gaps run never touches the
# production ledgers (NIKASHA_CONTROL_DIR; ported from harness/asset_census_closing.py).
CTRL = Path(os.environ.get("NIKASHA_CONTROL_DIR", str(ROOT / "00_ARCHITECTURE" / "control")))
SIDECAR = ROOT / "platform" / "python-sidecar"
WRITERS = SIDECAR / "pipeline" / "orchestrator" / "writers"

LAYERS = {
    "L0": dict(prefix="bg_", name="Brahmagyan", registry_layer="brahmagyan", scoring="fidelity",
               caps="platform/src/lib/retrieval/registry/layers/L0_brahmagyan", idem="upsert"),
    "L1": dict(prefix="ga_", name="Ganita", registry_layer="ganita", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L1_ganita", idem="delete_then_insert"),
    "L2": dict(prefix="bo_", name="Bodha", registry_layer="bodha", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L2_bodha", idem="delete_then_insert"),
    "L3": dict(prefix="ka_", name="Kala", registry_layer="kala", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L3_kala", idem="delete_then_insert"),
    "L4": dict(prefix="ph_", name="Phala", registry_layer="phala", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L4_phala", idem="delete_then_insert"),
    "L5": dict(prefix="mi_", name="Mimamsa", registry_layer="mimamsa", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L5_mimamsa", idem="delete_then_insert"),
}

PASS, FAIL, PARTIAL, NO_DET, NA, NOT_GENERIC = "PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "N/A", "NOT_GENERIC"
# R41: a per-check exception (timeout, missing relation, malformed key) degrades to ERRORED for
# THAT check/asset — never in FAILING (never opens a gap the detector itself couldn't measure)
# nor in CLOSABLE (never closes one either); an existing open gap is left exactly as it was,
# because "the detector broke" and "the defect is fixed" are different facts.
ERRORED = "ERRORED"

# ─────────────────────────── R78/R79/D4: the declarative criterion registry ───────────────────────────
# D4 ruling (nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md §D4, adopted 2026-09-27): "obligation
# identity comes first; the id is derived from it." A gap row is identified by (asset, scope,
# criterion), where `criterion` is an entry in this declarative registry — replacing the criterion
# strings that used to be built inline as bare `m["Gate.check"] = ...` assignments through
# `measure()` with nothing anywhere naming them as a closed, registered set. Each entry carries:
#   gate          — one of the nine gates (§4 of ASSET_ELEVATION_TEMPLATE_v2_0.md)
#   check         — the specific claim within that gate; the criterion string is always
#                   f"{gate}.{check}" — the census's own pre-existing id form, unchanged
#   applicability — one line: when this criterion applies
#   detector      — "asset_census.py:measure()" for every criterion the census itself auto-measures
#                   on every run, or the literal string "NONE" for a criterion that exists so a
#                   hand-written gap row has somewhere registered to point at, but that nothing in
#                   this script currently measures automatically (D4: "a registered criterion with
#                   detector: NONE yields NO_DETECTOR rows on every run ... which is the visible
#                   'detector wanted' state" — never registering a bare, undetected claim; the
#                   NONE binding IS the honest, visible form of "wanted, not yet built").
#   revision      — an integer, bumped whenever a criterion's applicability or detector binding
#                   changes in a way that would make an old measurement under the same string
#                   mean something different (not bumped by this registry's initial authoring).
#
# R78 does not change what measure() computes — every criterion below with detector="asset_census.py:measure()"
# is exactly the string that function already assigns into `m[...]`; this registry is the census
# READING itself as a closed set (D4 finding #5: "no declarative criterion list exists ... a
# NO_DETECTOR row for a declared, unbound criterion is the honest form, not a forbidden one").
#
# A specific proof is a distinct criterion from its generic placeholder (D4: `Carr.D1` ≠
# `Carr.detector`; `Completeness.depth.dasha_link` ≠ `Complete.depth`; `Earn.service_state` ≠
# `Earn.build_record`) and is never merged by family alias at runtime — the four family aliases
# named in R79/D4 (`Vocab.rule1.alias`→`Vocab.alias`, `Dens.density_contract`→`Dens.served`,
# `Carr.D1|D2|D3`→`Carr.detector`, `Completeness.*`→`Complete.*`) are one-time crosswalk entries
# consumed only by the R81 migration script, and are NOT registered here as runtime equivalences.
#
# E6.1 (Track E brief §8) adds three EXPLICIT applicability keys to every entry (None where a key
# does not restrict; an entry without one is a test failure, never a default):
#   layers        — tuple of layer keys where the criterion is defined. All six today: every criterion
#                   the census emits has verdicts wherever it is measured, and narrowing would drop
#                   committed verdicts (a later, deliberate `layers` narrowing is a registry revision).
#   columns_any   — column-pattern applicability: applies only when the asset's target table has at
#                   least one of these exact column names. Ldgr.source_presence shares
#                   CITATION_COLUMNS with measure(), so the rule and the detector cannot drift.
#   asset_kinds   — applies only when asset_kind is in the tuple (Earn.service_state's own text).
# See criterion_applicability() for how these are evaluated: an absent fact is UNKNOWN, never N/A.
ALL_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")
ALIAS_COLUMN = "synonyms"   # the alias-bearing column: read by the Vocab.alias registry entry AND alias_census()
CITATION_COLUMNS = ("source_citation", "source_text_id", "classical_citation", "classical_citations", "citation_ref")
CRITERION_REGISTRY: dict[str, dict] = {
    # ── auto-measured every run (detector = this module's own measure()) ──
    "Build.registered":      dict(gate="Build", check="registered",       applicability="always (writer-backed or not — a false has_writer is itself the failure)", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.contract":        dict(gate="Build", check="contract",         applicability="has_writer=true",       detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.target":          dict(gate="Build", check="target",          applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),
    "Build.dag":             dict(gate="Build", check="dag",              applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),
    "Build.count_integrity": dict(gate="Build", check="count_integrity", applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.completion":      dict(gate="Build", check="completion",       applicability="a count_sql or view target exists", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),  # R99 bumped: a writer-backed empty table under target_floor=0 now reads PARTIAL, not the R52-era blanket PASS
    "Build.exercised":       dict(gate="Build", check="exercised",        applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.history":         dict(gate="Build", check="history",          applicability="has been exercised at least once", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.dep_liveness":     dict(gate="Build", check="dep_liveness",     applicability="declares at least one depends_on", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Idem.pattern":          dict(gate="Idem",  check="pattern",          applicability="has_writer=true",       detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),
    "Earn.build_record":     dict(gate="Earn",  check="build_record",     applicability="has a build/attempt record to grade", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    # NOTE: "Cost", "Count", "Complete" and "Reach" are not among the nine gates in
    # ASSET_ELEVATION_TEMPLATE_v2_0.md §4 (Ldgr/Idem/Earn/Null/Vocab/Carr/Narr/Dens/Build) — they
    # are pre-existing census criteria this registry catalogs as-is (T5_LEDGER_DRIFT.md already
    # lists Cost.baseline and Complete.depth among the ledger's census criteria). R78 is scoped to
    # registering what exists, not to reconciling the gate taxonomy against T4, which is out of
    # this row's scope and left as an out-of-scope finding in the wave report.
    "Cost.baseline":         dict(gate="Cost",  check="baseline",         applicability="has a build/attempt record to grade", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Count.floor":           dict(gate="Count", check="floor",            applicability="declares target_floor and a count_sql", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Complete.depth":        dict(gate="Complete", check="depth",         applicability="target_table exists in production", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Complete.width":        dict(gate="Complete", check="width",         applicability="always (declaring a universe is the first width gap where none exists)", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Vocab.identity":        dict(gate="Vocab", check="identity",         applicability="a declared key exists and the table is non-empty", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Vocab.alias":           dict(gate="Vocab", check="alias",            applicability="the table declares an alias-bearing class census", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=(ALIAS_COLUMN,), asset_kinds=None, revision=1),
    "Ldgr.source_presence":  dict(gate="Ldgr",  check="source_presence",  applicability="the target table carries a recognised citation column (R60: singular classical_citation included)", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=CITATION_COLUMNS, asset_kinds=None, revision=2),
    "Dens.served":           dict(gate="Dens",  check="served",           applicability="reaches a served capability module; PASS (structural) needs ONE capability entry (the object literal that declares density_contract) whose own served read of the asset's table selects a tier column; a sibling entry, a sub-select, an INSERT...SELECT or a UNION branch does not count", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=4),  # E6.1(d): was file-level 'declares density_contract anywhere' (rev 1)
    "Narr.agree":            dict(gate="Narr",  check="agree",            applicability="prose_fields declared non-empty (null = undeclared: NO_DETECTOR; [] = declared no prose: measured N/A candidate, cause no-prose, undecided)", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),  # E6 (c): the declaration and the table's columns agree
    "Narr.checkable":        dict(gate="Narr",  check="checkable",        applicability="prose_fields declared non-empty; zero checkable rows is INCONCLUSIVE, never PASS", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Narr.fidelity_test":    dict(gate="Narr",  check="fidelity_test",    applicability="prose_fields declared non-empty; structural test discovery (N.7 item 5); never PASS", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Narr.lint":             dict(gate="Narr",  check="lint",             applicability="prose_fields declared non-empty; the fact-category-pin and raw-token narration lints over the writer scope", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Null.schema_default":   dict(gate="Null",  check="schema_default",   applicability="prose_fields declared non-empty; a non-NULL DEFAULT on a declared prose column; never PASS alone", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Null.blank_rows":       dict(gate="Null",  check="blank_rows",       applicability="prose_fields declared non-empty; blank or placeholder rows standing in for NULL; never PASS alone", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Carr.detector":         dict(gate="Carr",  check="detector",         applicability="always (the generic 'some carriage detector exists' reading)", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Reach.fields":          dict(gate="Reach", check="fields",           applicability="a served capability module selects specific columns", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    # ── registered, hand-observed only (detector NONE — D4 finding #5's honest, visible form) ──
    # These are the specific criteria R81's migration re-keys the 11 T5_LEDGER_DRIFT.md §A pairs
    # onto, each strictly MORE SPECIFIC than the generic auto-measured placeholder it sits beside
    # (Carr.D1/D2/D3 vs Carr.detector; Completeness.depth.dasha_link vs Complete.depth;
    # Earn.service_state vs Earn.build_record) — registered so a hand row has somewhere to point,
    # never auto-measured because no in-repo detector exists for the specific claim yet.
    "Carr.D1":                       dict(gate="Carr", check="D1", applicability="the asset restates a value from a cited source (source correspondence)", detector="NONE", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Carr.D2":                       dict(gate="Carr", check="D2", applicability="the asset carries two independent witnesses of the same fact", detector="NONE", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Carr.D3":                       dict(gate="Carr", check="D3", applicability="the asset computes a value that a second method could re-derive", detector="NONE", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Completeness.depth.dasha_link": dict(gate="Completeness", check="depth.dasha_link", applicability="the table declares a dasha_system_id column", detector="NONE", layers=ALL_LAYERS, columns_any=("dasha_system_id",), asset_kinds=None, revision=1),
    "Earn.service_state":            dict(gate="Earn", check="service_state", applicability="asset_kind='service' (no target_table; asset_throughput's rows_written signal cannot distinguish healthy-and-idle from broken)", detector="NONE", layers=ALL_LAYERS, columns_any=None, asset_kinds=("service",), revision=1),
}


def registered_criterion(crit: str) -> dict | None:
    """R78/R79: the one lookup every criterion string in this script (or a hand gap row) resolves
    through. Returns the registry entry, or None if `crit` is not a registered criterion at all —
    the D4 rule that "hand-written gap rows use a registered criterion; if the gap has none, the
    author registers one line first" is enforced by callers treating None as a hard stop, not by
    this function inventing a default entry."""
    return CRITERION_REGISTRY.get(crit)


def gap_id_for(asset_id: str, crit: str, scope: str | None = None) -> str:
    """R79 (re-scoped per D4): the deterministic id derivation — `<asset>-<Gate>.<check>`, the
    census's pre-existing form (criterion strings are already "Gate.check"), with a scope suffix
    appended where the gap is chart-scoped. Deliberately does NOT resolve family aliases (R79 is
    re-scoped, not withdrawn: aliasing happens once, by hand, in the R81 migration script — never
    here, and never at runtime)."""
    base = f"{asset_id}-{crit}"
    return f"{base}@{scope}" if scope else base


def lookup_criterion(asset: str, scope: str | None, crit: str) -> tuple[str, dict] | None:
    """R79 (re-scoped per D4): deterministic lookup on (asset, scope, registered criterion) — no
    substance-key aliasing, no family merge. Returns (gap_id, registry_entry) or None when `crit`
    is not registered. Two criteria that happen to describe related substance (e.g. `Carr.D1` and
    `Carr.detector`) are two distinct lookups here, by design (D4 review finding #2: "a specific
    proof is a distinct criterion from its generic placeholder ... and is never merged by family
    alias")."""
    entry = registered_criterion(crit)
    if entry is None:
        return None
    return gap_id_for(asset, crit, scope), entry


# ─────────────────────────── E6.1/E6.2: applicability, rollup, registry revision ───────────────────────────
# The nine gates of plan §2.1. Only these are rolled up into gate cells (9 x 127). Criteria of any other
# gate name (Cost, Count, Complete, Reach, Completeness) are reported by rollup_excluded(), never dropped.
CELL_GATES = ("Ldgr", "Idem", "Earn", "Null", "Vocab", "Carr", "Narr", "Dens", "Build")
# Worst first. N/A is not in the order: it is a cell value only when EVERY check is N/A by declared rule.
ROLLUP_ORDER = ("FAIL", "ERRORED", "NO_DETECTOR", "PARTIAL", "PASS")

# Declared N/A rules: rule id -> decision id (plan §2.1: "every rule cites its decision id"; N/A is computed,
# never typed). Rule ids are "<criterion>#columns_any", "<criterion>#asset_kinds" (a supplied fact disproves the
# pattern) and "<criterion>#measured:<cause>" (the census itself measured N/A, and the inspector named the CAUSE:
# N-22 ruling principle 2). The uncaused "<criterion>#measured" form is RETIRED: one id per criterion released
# every measured N/A of that criterion, whatever condition produced it. EMPTY on purpose: per-gate applicability
# rules are N-22 (Strategic Suvarna), not yet approved. Until a rule id is declared here, an N/A reads NO_DETECTOR.
NA_RULE_DECISIONS: dict[str, str] = {}

# The causes the inspector may emit on a measured N/A, per criterion. A slug names the CODE CONDITION that produced
# the N/A (what `measure()` or a helper actually tested), never a semantic the code does not establish; the table
# with each condition and reason text is E6.1/cause_table.md. `cause` is emitted only on N/A records.
NA_CAUSES: dict[str, tuple[str, ...]] = {
    "Build.registered": ("no-writer-registry-agrees",),
    "Build.contract": ("no-writer-registry-agrees",),
    "Idem.pattern": ("no-writer-registry-agrees",),
    "Build.target": ("service-no-target-table", "no-writer-no-target-table"),
    "Build.count_integrity": ("no-writer-no-count-sql",),
    "Build.completion": ("no-writer-no-count-sql", "service-no-target-table-no-count-sql"),
    "Count.floor": ("target-floor-zero",),
    "Dens.served": ("no-served-surface",),
    "Carr.D1": ("no-carriage",), "Carr.D2": ("no-carriage",), "Carr.D3": ("no-carriage",),
    "Build.exercised": ("never-run-no-writer", "never-executed-no-writer"),
    "Build.history": ("never-run",),
    "Build.dep_liveness": ("no-declared-dependencies",),
    "Narr.agree": ("no-prose",), "Narr.checkable": ("no-prose",), "Narr.fidelity_test": ("no-prose",), "Narr.lint": ("no-prose",),
    "Null.schema_default": ("no-prose-declared",), "Null.blank_rows": ("no-prose-declared",),
    "Earn.build_record": ("never-attempted", "healthy-non-execution", "no-registered-writer",
                         "before-completion-write"),
}
_CAUSE_SLUG = re.compile(r"[a-z0-9][a-z0-9_-]*")


def _na(measured: str, cause: str) -> dict:
    """A measured N/A record: the ONLY record shape that carries a `cause` (the rollup reads it)."""
    return dict(v=NA, measured=measured, cause=cause)

def validate_na_rule_decisions() -> None:
    """Every declared N/A rule id must be a rule id this module can actually issue, else ValueError naming ALL the
    offenders (a typo'd or retired id otherwise sits inert: it reads as 'declared' in review and releases nothing).
    Well-formed ids: `<crit>#measured:<cause>` with `cause` a slug registered for `crit` in NA_CAUSES (the retired
    uncaused `<crit>#measured` is NOT well-formed), and the fact-disproved applicability forms
    `<crit>#columns_any` / `<crit>#asset_kinds` for a registered criterion whose registry entry has that pattern
    (`criterion_applicability` issues exactly these). Each decision must be a non-blank str (plan §2.1: every rule
    cites its decision id). Called by rollup_asset (every cell) and emit_gaps (every ledger write)."""
    bad = []
    for rid, decision in NA_RULE_DECISIONS.items():
        ok = False
        if isinstance(rid, str) and isinstance(decision, str) and decision.strip():
            crit, sep, rule = rid.partition("#")
            if sep and rule.startswith("measured:"):
                cause = rule[len("measured:"):]
                ok = bool(_CAUSE_SLUG.fullmatch(cause)) and cause in NA_CAUSES.get(crit, ())
            elif sep and rule in ("columns_any", "asset_kinds"):
                ok = crit in CRITERION_REGISTRY and CRITERION_REGISTRY[crit][rule] is not None
        if not ok:
            bad.append(rid)
    if bad:
        raise ValueError(f"NA_RULE_DECISIONS holds {len(bad)} id(s) that are not a rule id this inspector can issue "
                         f"(need <crit>#measured:<registered cause> or <crit>#columns_any/#asset_kinds for a "
                         f"criterion with that pattern, each with a non-blank decision id): {bad!r}")


# Registry revision: hand-bumped integer; registry_fingerprint() is the content hash a pin test binds to it, so the
# revision cannot silently lag the content. Every gate cell carries both.
REGISTRY_REVISION = 7     # 7: E6 item (f): NA_CAUSES gains Carr.D1/D2/D3:no-carriage (N-22 principle 7, provisional until J1; SS strict definition: no DAG dependents AND no served-surface reach). The criterion registry is unchanged; the fingerprint moves because NA_CAUSES is fingerprinted content. No rule declared (NA_RULE_DECISIONS stays empty) and no asset declares terminal_by_construction, so no census cell changes. 6: E6 items (g)+(h): Build.target rev 2 (a declared service with no target_table, declared `service` by BOTH the registry and the declarations file, reads PASS by declaration, T4:274); Build.dag rev 2 (THREE clauses, each stated in the verdict text: every depends_on id is an active registry asset in ANY layer, the asset is on no dependency cycle, and reads-match — the writer's SQL reads against the declared edges, T4:275, aligned with pipeline/orchestrator/dag_edge_guard.py (SS 2026-10-01: L0 bedrock reads are exempt as `bedrock_exempt`, PROVISIONAL pending the J1 review; chart_facts is satisfied by any producer in the declared transitive closure); an undeclared read is a FAIL naming the missing edge, or a back-read when the edge would close a cycle; an incomplete parse is PARTIAL/NO_DETECTOR); Idem.pattern rev 2 (relative imports resolve against the importing package: ONE resolver for Idem.pattern and the reads scan — verdicts identical on the 127 saved writers, three notes changed: ka_dasha_kala, ka_gochara, ka_muhurta_seva). 5: E6 packet (c): Narr.agree/checkable/fidelity_test/lint and Null.schema_default/blank_rows registered; NA_CAUSES gains no-prose / no-prose-declared. 4: Dens.served rev 4 (contract AND a tier column in the served select; structural; cause no-served-surface). 3: NA_CAUSES gains Earn.build_record:no-registered-writer (E6 review fix 2). 2: N/A rule ids are cause-keyed (<criterion>#measured:<cause>); NA_CAUSES joins the content


def registry_fingerprint() -> str:
    """sha256 over the canonical JSON of everything that decides a cell: the registry, the declared N/A
    rules, the N/A causes the inspector may emit, and the cell-gate list."""
    import hashlib
    blob = json.dumps(dict(registry=CRITERION_REGISTRY, na_rules=NA_RULE_DECISIONS, na_causes=NA_CAUSES,
                           cell_gates=list(CELL_GATES), rollup_order=list(ROLLUP_ORDER)),
                      sort_keys=True, default=list, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def criterion_applicability(crit: str, layer: str, facts: dict | None = None) -> dict:
    """E6.1: is registered criterion `crit` applicable to an asset of `layer`, given the asset `facts` the
    caller SUPPLIED (`columns`: the target table's column names; `asset_kind`)?

    States: OUT_OF_LAYER (layer not declared; not part of that layer's gate), NOT_APPLICABLE (a supplied
    fact contradicts a declared pattern; carries the `rule_id` an N/A would need), UNKNOWN (the fact the
    pattern needs was not supplied — absence is never NOT_APPLICABLE), APPLIES. NOT_APPLICABLE dominates
    UNKNOWN: one disproving fact is definitive whatever the other says. Raises KeyError for an
    unregistered criterion."""
    e = CRITERION_REGISTRY[crit]
    if layer not in LAYERS:
        raise KeyError(f"unknown layer {layer!r}; expected one of {sorted(LAYERS)}")
    if layer not in e["layers"]:
        return dict(state="OUT_OF_LAYER", rule_id=None, reason=f"{crit} is not defined for {layer}")
    facts = facts or {}
    unknown = []
    for key, fact_key, label in (("columns_any", "columns", "target-table columns"),
                                 ("asset_kinds", "asset_kind", "asset_kind")):
        pattern = e[key]
        if pattern is None:
            continue
        have = facts.get(fact_key)
        if key == "columns_any":
            # evidence only when a list/tuple/set of str; an EMPTY collection counts only when the caller
            # asserts columns_known is exactly True ("the table is known and has zero columns")
            usable = (isinstance(have, (list, tuple, set)) and all(isinstance(c, str) for c in have)
                      and (bool(have) or facts.get("columns_known") is True))
        else:
            usable = isinstance(have, str) and bool(have)
        if not usable:
            unknown.append(f"{label} not supplied" if have is None else f"{label} unusable ({have!r})")
            continue
        ok = (any(c in pattern for c in have) if key == "columns_any" else have in pattern)
        if not ok:
            return dict(state="NOT_APPLICABLE", rule_id=f"{crit}#{key}",
                        reason=f"{label} {list(have) if key == 'columns_any' else have!r} match none of {list(pattern)}")
    if unknown:
        return dict(state="UNKNOWN", rule_id=None, reason="; ".join(unknown) + " — applicability undecidable")
    return dict(state="APPLIES", rule_id=None, reason="applies")


def rollup_verdicts(verdicts) -> str:
    """E6.2: worst of FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS. All N/A -> N/A. No checks ->
    NO_DETECTOR (a gate with no checks measures nothing). A verdict outside PASS/FAIL/PARTIAL/NO_DETECTOR/
    ERRORED/N/A (NOT_GENERIC included) raises ValueError: an ungradable value is never silently ranked.
    Any iterable is accepted (materialised first, so a generator is not drained by validation); a bare str
    raises TypeError (it would otherwise be iterated character by character)."""
    if isinstance(verdicts, (str, bytes)):
        raise TypeError("rollup_verdicts takes an iterable of verdicts, not a bare string")
    verdicts = list(verdicts)
    for v in verdicts:
        if v not in ROLLUP_ORDER and v != NA:
            raise ValueError(f"verdict {v!r} is outside the rollup vocabulary {list(ROLLUP_ORDER) + [NA]}")
    if not verdicts:
        return NO_DET
    graded = [v for v in verdicts if v != NA]
    if not graded:
        return NA
    return min(graded, key=ROLLUP_ORDER.index)


def _check_contribution(crit: str, layer: str, meas: dict | None, facts: dict | None) -> dict | None:
    """One criterion's contribution to its gate cell, or None when it is out of layer and unmeasured."""
    e = CRITERION_REGISTRY[crit]
    ap = criterion_applicability(crit, layer, facts)
    if meas is not None:
        if ap["state"] == "OUT_OF_LAYER":
            raise ValueError(f"{crit} was measured on {layer} but the registry declares layers {list(e['layers'])}")
        v = meas["v"]
        if v not in ROLLUP_ORDER and v != NA:
            raise ValueError(f"{crit}: measured verdict {v!r} is outside the rollup vocabulary")
        if v == NA:
            cause = meas.get("cause")
            if not (isinstance(cause, str) and _CAUSE_SLUG.fullmatch(cause)):
                # N-22 principle 2: an N/A whose inspector named no usable cause cannot be keyed to any rule.
                # Reported (reason + the cause as found), never honoured — not even by an `every id declared` set.
                return dict(criterion=crit, v=NO_DET, state="MEASURED",
                            reason=f"N/A without a declared cause (cause={cause!r}): the inspector named no usable "
                                   "cause, so no rule can release it")
            rid = f"{crit}#measured:{cause}"
            if cause not in NA_CAUSES.get(crit, ()):
                return dict(criterion=crit, v=NO_DET, state="MEASURED", rule_id=rid, cause=cause,
                            reason=f"measured N/A with cause {cause!r}, which is not a registered cause of {crit}: "
                                   "never honoured")
            if rid in NA_RULE_DECISIONS:
                return dict(criterion=crit, v=NA, state="MEASURED", rule_id=rid, cause=cause,
                            decision=NA_RULE_DECISIONS[rid], reason="measured N/A under a declared rule")
            return dict(criterion=crit, v=NO_DET, state="MEASURED", rule_id=rid, cause=cause,
                        reason="measured N/A but N/A rule undecided (N-22): an undeclared N/A is not N/A")
        if v == PASS and e["detector"] == "NONE":
            return dict(criterion=crit, v=NO_DET, state="MEASURED",
                        reason="detector NONE never reaches PASS")
        # E6 packet (c): the rollup does not trust a record's own verdict where the claim cannot be established
        # (INCONCLUSIVE is a state: nothing was measured), and the two capped checks cannot read PASS (SS: Null "never
        # PASS alone"; Narr.fidelity_test structural only)
        infl = bool(meas.get("inconclusive"))
        if infl and v in (PASS, PARTIAL):
            return dict(criterion=crit, v=NO_DET, state="MEASURED", inconclusive=True,
                        reason="INCONCLUSIVE record: nothing was established, so it cannot read PASS or PARTIAL")
        if v == PASS and (crit.startswith("Null.") or crit == "Narr.fidelity_test"):
            return dict(criterion=crit, v=PARTIAL, state="MEASURED",
                        reason=f"{crit} is capped at PARTIAL (Null: never PASS alone; fidelity_test: structural only)")
        basis = meas.get("basis")
        if basis is not None and basis != "declaration":      # case-exact: 'Declaration' is not 'declaration'
            return dict(criterion=crit, v=NO_DET, state="MEASURED",
                        reason=f"unrecognised basis {basis!r} (the only defined basis is 'declaration', case-exact): "
                               "the verdict is not honoured")
        if v == PASS and basis == "declaration":
            return dict(criterion=crit, v=v, state="MEASURED", basis="declaration",
                        reason="PASS by declaration, not measured: no measurement stands behind this verdict")
        if v == FAIL and meas.get("transitive_only") is True:
            return dict(criterion=crit, v=v, state="MEASURED",
                        reason="measured; transitive_only: every missing edge is already reachable through a declared "
                               "dependency (ordering holds, the edge is undeclared)", **(dict(inconclusive=True) if infl else {}))
        return dict(criterion=crit, v=v, state="MEASURED", reason="measured", **(dict(inconclusive=True) if infl else {}))
    st = ap["state"]
    if st == "OUT_OF_LAYER":
        return None
    if st == "NOT_APPLICABLE":
        rid = ap["rule_id"]
        if rid in NA_RULE_DECISIONS:
            return dict(criterion=crit, v=NA, state=st, rule_id=rid, decision=NA_RULE_DECISIONS[rid], reason=ap["reason"])
        return dict(criterion=crit, v=NO_DET, state=st, rule_id=rid,
                    reason=f"N/A rule undecided (N-22): {ap['reason']}")
    return dict(criterion=crit, v=NO_DET, state=st, reason=f"not measured ({ap['reason']})")


def rollup_asset(layer: str, measurements: dict, facts: dict | None = None) -> dict:
    """E6.2: the nine gate cells for one asset. `measurements` is the census's per-asset
    `measurements` dict; `facts` optionally supplies `columns` and `asset_kind`. A registered criterion
    with no measurement still counts (NO_DETECTOR) unless it is out of layer or an N/A rule declared in
    NA_RULE_DECISIONS disproves it — absence is never N/A. Raises KeyError for a layer or measured
    criterion not registered, ValueError for a measurement outside its declared layers or verdict set."""
    if layer not in LAYERS:
        raise KeyError(f"unknown layer {layer!r}")
    for crit in measurements:
        if crit not in CRITERION_REGISTRY:
            raise KeyError(f"measured criterion {crit!r} is not in CRITERION_REGISTRY")
    validate_na_rule_decisions()
    fp = registry_fingerprint()
    cells = {}
    for gate in CELL_GATES:
        checks = []
        for crit, e in CRITERION_REGISTRY.items():
            if e["gate"] != gate:
                continue
            c = _check_contribution(crit, layer, measurements.get(crit), facts)
            if c is not None:
                checks.append(c)
        cells[gate] = dict(gate=gate, v=rollup_verdicts([c["v"] for c in checks]), checks=checks,
                           registry_revision=REGISTRY_REVISION, registry_fingerprint=fp)
        declared = [c["criterion"] for c in checks if c.get("basis") == "declaration"]
        if declared:                  # a cell that rests on a declaration says so (key absent otherwise: no other cell changes)
            cells[gate]["declared_checks"] = declared
    return cells


def rollup_excluded(layer: str, measurements: dict) -> dict:
    """Measured criteria whose gate is not one of the nine cell gates: reported here, never silently
    dropped (their owner decision is a campaign question, not a rollup choice)."""
    return {c: mv["v"] for c, mv in measurements.items()
            if c in CRITERION_REGISTRY and CRITERION_REGISTRY[c]["gate"] not in CELL_GATES}


def rollup_census(census_layer: dict, facts_by_asset: dict | None = None) -> dict:
    """E6.2 over one measured layer (`measure()` output): asset_id -> nine gate cells. Read-only."""
    layer = census_layer.get("layer")
    if layer is None:
        layer = census_layer["assets"][0]["layer"]
    return {a["asset_id"]: rollup_asset(layer, a["measurements"], (facts_by_asset or {}).get(a["asset_id"]))
            for a in census_layer["assets"]}


# E6.1 packet 2a: the per-asset FACTS the rollup's applicability rules read, emitted by measure() and turned into
# the `facts` mapping by facts_for_asset(). "Could not be established" (no target table, table absent from the
# catalog, no column rows for an existing relation, blank asset_kind) is None, i.e. JSON null: an empty list never
# stands for unknown, and no string marker exists that could be read as a value (and a disproving one at that).


def _target_columns_fact(tbl: str | None, cat: dict):
    """The target table's column names as a sorted list, or None (unknown). Known only when the table is in the
    catalog's `exists` AND the catalog returned column rows for it (a materialized view is in `exists` but
    information_schema lists none: incomplete introspection is unknown, not 'zero columns')."""
    if not tbl or tbl not in cat.get("exists", ()):
        return None
    cols = cat.get("cols", {}).get(tbl)
    if not isinstance(cols, list) or not cols or not all(isinstance(c, str) and c for c in cols):
        return None
    return sorted(cols)


# E6.1 declarations packet: the per-asset DECLARED facts (N-22 ruling; SS decisions 2026-09-30). ONE versioned
# repository file, reviewed in PRs, read here; no migration, the registry CHECK is untouched. A declaration is a FACT
# and only a fact: nothing in this block makes a gate N/A, changes a criterion, or changes a verdict (rules key on
# causes, a later packet). An asset absent from the file, and a null field, are UNKNOWN: never a value.

DECLARATIONS_PATH = Path(__file__).resolve().parent / "asset_declarations.json"
DECLARED_KINDS = ("data", "service", "view", "static", "rider", "probe", "user_data")   # `multi-table` is a measured fact, not a kind
# `dag_dependents` is deliberately NOT a declared carriage field: who depends on an asset is MEASURED (the census
# blocking_radius), and a declared copy of a measurement is circular (every value was derived from it) and can only
# ever be wrong-or-redundant; it already was wrong for bg_gochara_arcs, whose real reader ka_gochara has no registry
# depends_on edge (a registry defect, recorded in the evidence file, not a declaration). Nothing overrides the radius.
CARRIAGE_FIELDS = ("served_surface",)
_DECL_ENTRY_KEYS = ("kind", "carriage", "prose_fields", "terminal_by_construction", "cross_asset_writes",
                    "read_evidence", "read_table", "read_kind", "evidence", "evidence_kind")
_DECL_EVIDENCE_KEYS = ("kind", "carriage", "prose_fields", "cross_asset_writes")
# prose_fields entries (SS ruling 2026-10-01; CLAUDE.md N.7 concerns GENERATED prose): a column name, or a JSON path into
# a JSONB column, `column.$.seg(.seg)*` where a seg is an identifier key, optionally followed by ONE `[*]` (every element
# of the array at that key; grammar 1.6.0). No index numbers, no `[*][*]`, no `[*]` on the column itself, no quoting.
# Used with fullmatch.
PROSE_IDENT_MAX = 128          # a column name / JSON key longer than this is not an identifier anyone declared on purpose
_PROSE_COLUMN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PROSE_PATH_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\.\$((?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[\*\])?)+)")
PROSE_WILDCARD = "[*]"         # the path-tuple token for an array-element segment (not a valid identifier: no key collides)
# evidence.prose_fields must cite writer code as `path.ext:LINE` (py/ts/tsx; never .sql, never a test path) and carries
# `evidence_kind: "writer"`; a declaration that cites the column's DDL migration instead is marked `evidence_kind: "ddl"` (it then
# needs a `NNN_name.sql` token, no line). An unmarked (null) kind gets the same cite checks as "writer".
EVIDENCE_PATH_LINE_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\[\]@-]*\.(?:py|ts|tsx):[1-9][0-9]*")
_EVIDENCE_SQL_LINE_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\[\]@-]*\.sql:[1-9][0-9]*")
_EVIDENCE_ANY_CITE_RE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./\[\]@-]*\.(?:py|ts|tsx)):[1-9][0-9]*")
_EVIDENCE_TEST_PATH_RE = re.compile(r"(^|/)(__tests__|tests?|fixtures)/|(^|/)test_[^/]*$|_test\.py$|\.(test|spec)\.tsx?$")
EVIDENCE_KINDS = ("ddl", "writer")
_DDL_EVIDENCE_RE = re.compile(r"[0-9]+_[A-Za-z0-9_]+\.sql")


def _blank_text(s) -> bool:
    """True for a string with no visible character: empty, whitespace, control, or invisible format/separator code points
    (zero-width space/joiner, BOM, word joiner, no-break and other Unicode spaces), which str.strip() alone does not remove."""
    return all(unicodedata.category(ch)[0] in ("Z", "C") for ch in s)


_CROSS_WRITE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*")   # table.column; used with fullmatch
# `served_surface: true` needs a real read: `read_evidence` is a repo-relative `path:line` (1-based) and `read_table` the
# identifier that line reads FROM/JOINs (a test opens the file and checks the line); neither may exist otherwise.
# Served TypeScript only (platform/src or platform-mcp/src, .ts/.tsx; no Python, no scripts); components are never
# '.'/'..' (checked in validate_declarations) and never match _READ_EVIDENCE_EXCLUDED_RE.
_READ_EVIDENCE_RE = re.compile(r"(?:platform|platform-mcp)/src/[A-Za-z0-9_.\[\]@-]+(?:/[A-Za-z0-9_.\[\]@-]+)*\.tsx?:[1-9][0-9]*")
# paths that can never be a served read: tests/specs/mocks/e2e/fixtures/generated, the availability probe, the
# api/mcp/db/query table allow-list (a component match anywhere, with or without a leading directory)
_READ_EVIDENCE_EXCLUDED_RE = re.compile(
    r"(?:(?:^|/)(?:__tests__|__mocks__|tests?|e2e|fixtures|generated)/|\.(?:test|spec)\.[A-Za-z]+:?|"
    r"source_query_availability|(?:^|/)mcp/db/query/)")
READ_KINDS = ("coverage", "projection", "table_map")   # None = a row-level SQL read (the default); see declared_facts
_READ_TABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class DeclarationsError(ValueError):
    """The declarations file (or a document handed to validate_declarations) is malformed."""


def parse_prose_field(entry):
    """One `prose_fields` entry -> (column, path): `"narrative"` -> ("narrative", None);
    `"narrative.$.headline"` -> ("narrative", ("headline",)) (the JSON path of a composed string inside a JSONB column,
    which is what a Narr detector reads); `"d.$.a[*].b"` -> ("d", ("a", "[*]", "b")) (`[*]` = every element of the array
    at `a`, carried as the token "[*]"). Raises DeclarationsError on anything else (a blank, a non-string, a table
    prefix, `col.$` with no key, an index number, `[*][*]`, `[*]` on the column itself, a column that does not look like
    a column name)."""
    if isinstance(entry, str):
        if _PROSE_COLUMN_RE.fullmatch(entry):
            if len(entry) <= PROSE_IDENT_MAX:
                return entry, None
        else:
            m = _PROSE_PATH_RE.fullmatch(entry)
            if m:
                path = []
                for seg in m.group(2).split(".")[1:]:
                    wild = seg.endswith(PROSE_WILDCARD)
                    path.append(seg[:-len(PROSE_WILDCARD)] if wild else seg)
                    if wild:
                        path.append(PROSE_WILDCARD)
                path = tuple(path)
                if len(m.group(1)) <= PROSE_IDENT_MAX and all(len(k) <= PROSE_IDENT_MAX for k in path):
                    return m.group(1), path
    raise DeclarationsError(f"prose_fields entry {entry!r} must be a column name or 'column.$.key(.key)*' "
                            f"(a JSON path into a JSONB column; keys are plain identifiers, each optionally followed by one [*])")


def _registry_id_set(registry_ids):
    if registry_ids is None:
        return None
    if not isinstance(registry_ids, (list, tuple, set, frozenset)) or not all(isinstance(i, str) for i in registry_ids):
        raise DeclarationsError("registry_ids must be a list/tuple/set of asset-id strings (a bare string or other "
                                "iterable would silently change what `in` means)")
    return set(registry_ids)


def _decl_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise DeclarationsError(f"duplicate key {k!r} in the declarations file")
        seen[k] = v
    return seen


def validate_declarations(doc, registry_ids=None) -> dict:
    """Validate a declarations document and return its `assets` mapping (asset_id -> entry). Raises
    DeclarationsError naming the offending asset/field. `registry_ids` (an iterable of asset ids), when given, is the
    census registry set: a declared asset id outside it is an error (a typo must not become a silent UNKNOWN); it
    must be a list/tuple/set of strings, anything else is a DeclarationsError."""
    if not isinstance(doc, dict):
        raise DeclarationsError("declarations document must be a JSON object")
    if not isinstance(doc.get("version"), str) or not doc["version"].strip():
        raise DeclarationsError("`version` must be a non-empty string")
    if doc.get("kind_enum") != list(DECLARED_KINDS):
        raise DeclarationsError(f"`kind_enum` must be exactly {list(DECLARED_KINDS)}, got {doc.get('kind_enum')!r}")
    assets = doc.get("assets")
    if not isinstance(assets, dict):
        raise DeclarationsError("`assets` must be an object mapping asset_id to a declaration")
    known = _registry_id_set(registry_ids)
    for aid, e in assets.items():
        where = f"assets[{aid!r}]"
        if not isinstance(aid, str) or not aid.strip():
            raise DeclarationsError(f"{where}: asset id must be a non-empty string")
        if known is not None and aid not in known:
            raise DeclarationsError(f"{where}: asset id is not in the census registry set")
        if not isinstance(e, dict):
            raise DeclarationsError(f"{where}: must be an object")
        extra = sorted(set(e) - set(_DECL_ENTRY_KEYS))
        if extra:
            raise DeclarationsError(f"{where}: unknown field(s) {extra}")
        k = e.get("kind")
        if k is not None and (not isinstance(k, str) or k not in DECLARED_KINDS):
            raise DeclarationsError(f"{where}.kind {k!r} is not one of {list(DECLARED_KINDS)} (or null = unknown)")
        car = e.get("carriage")
        if car is not None:
            if not isinstance(car, dict):
                raise DeclarationsError(f"{where}.carriage must be an object or null")
            bad = sorted(set(car) - set(CARRIAGE_FIELDS))
            if bad:
                raise DeclarationsError(f"{where}.carriage: unknown field(s) {bad}")
            for f, v in car.items():
                if v is not None and not isinstance(v, bool):
                    raise DeclarationsError(f"{where}.carriage.{f} must be true, false or null, got {v!r}")
        pf = e.get("prose_fields")
        if pf is not None:
            # null = undeclared; [] = declared "this writer composes no prose" (a positive claim); both need evidence
            if not isinstance(pf, list):
                raise DeclarationsError(f"{where}.prose_fields must be null or a list of column names / "
                                        f"'column.$.key' JSON paths ([] = declared: composes no prose)")
            parsed = []
            for c in pf:
                try:
                    parsed.append(parse_prose_field(c))
                except DeclarationsError as exc:
                    raise DeclarationsError(f"{where}.prose_fields: {exc}") from exc
            # distinct, and no entry covers another: a duplicate, a column and a path of it, or a path and its sub-path
            # (case-insensitively; one column's sibling paths, or equal keys under two columns, are fine)
            for i, (col, path) in enumerate(parsed):
                for j in range(i + 1, len(parsed)):
                    col2, path2 = parsed[j]
                    if col.lower() != col2.lower():
                        continue
                    short, long_ = sorted((path or (), path2 or ()), key=len)
                    if tuple(x.lower() for x in long_[:len(short)]) == tuple(x.lower() for x in short):
                        raise DeclarationsError(f"{where}.prose_fields: {pf[i]!r} and {pf[j]!r} overlap (equal, or one "
                                                f"column/path already covers the other)")
            evp = (e.get("evidence") or {}).get("prose_fields") if isinstance(e.get("evidence"), dict) else None
            if not (isinstance(evp, str) and not _blank_text(evp)):
                raise DeclarationsError(f"{where}.prose_fields is declared (even []), so evidence.prose_fields must "
                                        f"carry a non-blank pointer (the writer code read, file:line)")
            ek = e.get("evidence_kind")
            if ek is not None and ek not in EVIDENCE_KINDS:
                raise DeclarationsError(f"{where}.evidence_kind must be null or one of {list(EVIDENCE_KINDS)}")
            if ek in (None, "writer"):
                cites = _EVIDENCE_ANY_CITE_RE.findall(evp)
                if not cites:
                    raise DeclarationsError(f"{where}.evidence.prose_fields must cite writer code as 'path.py:LINE' "
                                            f"(py/ts/tsx); DDL-only evidence needs evidence_kind 'ddl'")
                if _EVIDENCE_SQL_LINE_RE.search(evp):
                    raise DeclarationsError(f"{where}.evidence.prose_fields: a .sql:LINE cite is not writer code")
                if any(_EVIDENCE_TEST_PATH_RE.search(c) for c in cites):
                    raise DeclarationsError(f"{where}.evidence.prose_fields: a test/fixture path is not writer code")
            else:
                if not pf:
                    raise DeclarationsError(f"{where}: an empty prose_fields ([]) is a claim about writer code, not DDL evidence")
                if not _DDL_EVIDENCE_RE.search(evp):
                    raise DeclarationsError(f"{where}: evidence_kind 'ddl' needs the migration file (NNN_name.sql) in evidence.prose_fields")
        else:
            ev_orphan = e.get("evidence")
            if isinstance(ev_orphan, dict) and ev_orphan.get("prose_fields") is not None:
                raise DeclarationsError(f"{where}.evidence.prose_fields is set but prose_fields is null (undeclared): "
                                        f"an orphan pointer would read as evidence for a claim nobody made")
            if e.get("evidence_kind") is not None:
                raise DeclarationsError(f"{where}.evidence_kind is set but prose_fields is null (undeclared)")
        tbc = e.get("terminal_by_construction")
        if tbc is not None:
            if not isinstance(tbc, str) or _blank_text(tbc) or tbc != tbc.strip():
                raise DeclarationsError(f"{where}.terminal_by_construction must be null or a non-blank pointer string "
                                        f"(why the asset has no downstream consumer BY CONSTRUCTION)")
            if isinstance(car, dict) and car.get("served_surface") is True:
                raise DeclarationsError(f"{where}: terminal_by_construction contradicts carriage.served_surface true")
        re_ = e.get("read_evidence")
        rt = e.get("read_table")
        served_true = isinstance(car, dict) and car.get("served_surface") is True
        if re_ is not None and not (isinstance(re_, str) and _READ_EVIDENCE_RE.fullmatch(re_)
                                    and not {".", ".."} & set(re_.rsplit(":", 1)[0].split("/"))):
            raise DeclarationsError(f"{where}.read_evidence must be null or 'platform/src/...ts:LINE' / "
                                    f"'platform-mcp/src/...ts:LINE' (served TypeScript, no test/mock/generated/allow-list path)")
        if isinstance(re_, str) and _READ_EVIDENCE_EXCLUDED_RE.search(re_):
            raise DeclarationsError(f"{where}.read_evidence {re_!r} is a test/mock/generated/allow-list path, not a served read")
        rk = e.get("read_kind")
        if rk is not None and (not isinstance(rk, str) or rk not in READ_KINDS):
            raise DeclarationsError(f"{where}.read_kind must be null (row-level read) or one of {list(READ_KINDS)}")
        if rt is not None and not (isinstance(rt, str) and _READ_TABLE_RE.fullmatch(rt)):
            raise DeclarationsError(f"{where}.read_table must be null or a table identifier")
        if served_true and (re_ is None or rt is None):
            raise DeclarationsError(f"{where}: carriage.served_surface true requires read_evidence ('path:line' of a real "
                                    f"non-test read of the asset's table) and read_table; without a real read it is null")
        if not served_true and (re_ is not None or rt is not None or rk is not None):
            raise DeclarationsError(f"{where}: read_evidence/read_table/read_kind are only for carriage.served_surface true")
        cw = e.get("cross_asset_writes")
        if cw is not None:
            if (not isinstance(cw, list) or not all(isinstance(c, str) and _CROSS_WRITE_RE.fullmatch(c) for c in cw)
                    or len({c.lower() for c in cw}) != len(cw)):
                raise DeclarationsError(f"{where}.cross_asset_writes must be null or a list of distinct (case-insensitively) "
                                        f"'table.column' strings ([] = declared: writes nothing outside its own table)")
            ev0 = e.get("evidence")
            if not (isinstance(ev0, dict) and isinstance(ev0.get("cross_asset_writes"), str) and ev0["cross_asset_writes"].strip()):
                raise DeclarationsError(f"{where}.cross_asset_writes is declared (even []), so evidence.cross_asset_writes "
                                        f"must carry a non-blank pointer")
        ev = e.get("evidence")
        if ev is not None:
            if (not isinstance(ev, dict) or set(ev) - set(_DECL_EVIDENCE_KEYS)
                    or not all(v is None or isinstance(v, str) for v in ev.values())):
                raise DeclarationsError(f"{where}.evidence must be null or an object of pointer strings keyed "
                                        f"by {list(_DECL_EVIDENCE_KEYS)}")
    return assets


def load_asset_declarations(path=None, registry_ids=None) -> dict:
    """Pure reader: asset_id -> entry (`kind`, `carriage`, `prose_fields`, `evidence`). Reads only `path`
    (default DECLARATIONS_PATH). Raises DeclarationsError on a missing, unreadable, undecodable, non-JSON,
    pathologically nested, duplicate-keyed or malformed file. An asset absent from the result is UNKNOWN; so is any null field of an entry."""
    p = Path(path) if path is not None else DECLARATIONS_PATH
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:     # ValueError: UnicodeDecodeError, an embedded NUL in the path
        raise DeclarationsError(f"cannot read the declarations file {p}: {exc}") from exc
    try:
        doc = json.loads(text, object_pairs_hook=_decl_pairs)
    except json.JSONDecodeError as exc:
        raise DeclarationsError(f"declarations file {p} is not valid JSON: {exc}") from exc
    except RecursionError as exc:
        raise DeclarationsError(f"declarations file {p} is nested too deeply to parse (recursion limit)") from exc
    except ValueError as exc:                # e.g. an integer literal over the int-parsing digit limit
        raise DeclarationsError(f"declarations file {p} cannot be parsed: {exc}") from exc
    return validate_declarations(doc, registry_ids)


def declared_facts(declarations, asset_id, registry_kind=None, measured_dependents=None, measured_served=None) -> dict:
    """The DECLARED facts for one asset, as separate keys that never replace a measured one:
    `declared_kind`; `declared_carriage` (only the known `served_surface` boolean); `declared_carries_downstream`;
    `declared_prose_fields` (a list; `[]` = declared "composes no prose", a positive claim, present as an empty list; null = undeclared, key left out; entries are a column or a `column.$.key` JSON path, see parse_prose_field); `declared_read_evidence` / `declared_read_table` (the `path:line` of the real read that
    backs a declared served_surface true) and `declared_read_kind` (only when that read is not row-level:
    `coverage` = a facet/DISTINCT coverage lookup, `projection` = a column served on request, `table_map` = a
    dynamic `FROM ${table}` fed by a map); `declared_terminal_by_construction` (the pointer string); `declared_cross_asset_writes`
    (a list of 'table.column'; [] = declared writes-nothing-outside-its-own-table, null = unknown, key omitted); and
    `declaration_disagreements`: every place a declaration contradicts a measured or registry fact, reported and
    never resolved. Absent asset / null field -> key left out (UNKNOWN).

    `declared_carries_downstream` is NEVER derived from negatives (a negative scan or a zero measured count is not
    proof, CLAUDE.md N.8 / N.7.6): True only from a positive `served_surface: true`; False ONLY when the file carries
    the separate positive `terminal_by_construction` pointer; otherwise omitted (unknown). A future `write-nothing`
    cause must key on `declared_cross_asset_writes == []`, never on kind `service` alone (mi_abhilekha is a service
    that UPDATEs mimamsa_predictions.lifecycle_status).

    Measured inputs (each optional; a disagreement is reported only where the measurement is available):
    `registry_kind` (only 'service' and 'data' are compared: `artifact` maps to the declaration file per asset),
    `measured_dependents` (the census blocking_radius.direct; the only word on DAG dependents), `measured_served`
    (the Dens.served verdict: a declared served_surface False against PASS/FAIL/PARTIAL, or True against N/A, is reported)."""
    facts: dict = {}
    e = (declarations or {}).get(asset_id)
    if not isinstance(e, dict):
        return facts
    disagree = []
    kind = e.get("kind")
    if isinstance(kind, str) and kind in DECLARED_KINDS:
        facts["declared_kind"] = kind
        if registry_kind in ("service", "data") and kind != registry_kind:
            disagree.append(dict(field="kind", declared=kind, registry=registry_kind))
    car = e.get("carriage")
    served = None
    if isinstance(car, dict):
        known = {f: car[f] for f in CARRIAGE_FIELDS if isinstance(car.get(f), bool)}
        if known:
            facts["declared_carriage"] = known
            served = known.get("served_surface")
    if served is True:
        facts["declared_carries_downstream"] = True
    if isinstance(measured_served, str):
        if served is False and measured_served in (PASS, FAIL, PARTIAL):
            disagree.append(dict(field="carriage.served_surface", declared=False, measured=measured_served))
        elif served is True and measured_served == NA:
            disagree.append(dict(field="carriage.served_surface", declared=True, measured=measured_served))
    tbc = e.get("terminal_by_construction")
    if isinstance(tbc, str) and not _blank_text(tbc):
        facts["declared_terminal_by_construction"] = tbc
        if served is not True:
            facts["declared_carries_downstream"] = False
        if isinstance(measured_dependents, int) and not isinstance(measured_dependents, bool) and measured_dependents > 0:
            disagree.append(dict(field="terminal_by_construction", declared=tbc, measured_dependents=measured_dependents))
    pf = e.get("prose_fields")
    if isinstance(pf, list):
        facts["declared_prose_fields"] = list(pf)
    cw = e.get("cross_asset_writes")
    if isinstance(cw, list):
        facts["declared_cross_asset_writes"] = list(cw)
    rev, rtab = e.get("read_evidence"), e.get("read_table")
    if isinstance(rev, str) and rev.strip() and isinstance(rtab, str) and rtab.strip():
        facts["declared_read_evidence"] = rev
        facts["declared_read_table"] = rtab
        if isinstance(e.get("read_kind"), str) and e["read_kind"] in READ_KINDS:
            facts["declared_read_kind"] = e["read_kind"]
    if disagree:
        facts["declaration_disagreements"] = disagree
    return facts


def facts_for_asset(asset_record, declarations=None) -> dict:
    """The `facts` mapping `rollup_asset` expects (`columns`, `asset_kind`; plus `count_sql_declared` for the
    conditions that will read it), from one measured asset record. A fact that is absent (a record from before
    packet 2a), None (unknown), empty, or of the wrong type is LEFT OUT, so its applicability stays
    UNKNOWN. `columns_known` is never set: an emitted list cannot assert 'the table is known and has zero columns'.

    `declarations` (the mapping load_asset_declarations returns; default None = none supplied, the mapping is then
    exactly what it was before the declarations packet) MERGES the declared facts under their own `declared_*`
    keys (see declared_facts). The measured `asset_kind` is never overwritten: a declared kind that disagrees with
    the registry's 'service'/'data' is listed under `declaration_disagreements`, not silently preferred. No
    criterion reads a declared_* key, so no cell changes."""
    facts: dict = {}
    if not isinstance(asset_record, dict):
        return facts
    cols = asset_record.get("target_columns")
    if isinstance(cols, list) and cols and all(isinstance(c, str) and c.strip() for c in cols):
        facts["columns"] = [c.strip() for c in cols]   # stripped like measure() strips: a blank name is unknown
    kind = asset_record.get("asset_kind")
    if isinstance(kind, str) and kind.strip():
        facts["asset_kind"] = kind.strip()
    declared = asset_record.get("count_sql_declared")
    if isinstance(declared, bool):
        facts["count_sql_declared"] = declared
    if declarations:
        br = asset_record.get("blocking_radius")
        direct = br.get("direct") if isinstance(br, dict) else None
        ms = asset_record.get("measurements")
        ds = ms.get("Dens.served") if isinstance(ms, dict) else None
        served = ds.get("v") if isinstance(ds, dict) else None
        aid = asset_record.get("asset_id")
        if isinstance(aid, str):
            facts.update(declared_facts(declarations, aid, facts.get("asset_kind"), direct, served))
    return facts


def build_rollup_output(census_by_layer: dict, declarations: dict | None = None) -> dict:
    """The `--rollup` payload for {layer: measure() output}: the nine gate cells per asset (computed from each
    asset's emitted facts) and, as information, the measured criteria of the non-nine gates. Read-only; the
    census dicts are not modified (emit_gaps never sees this)."""
    layers, excluded = {}, {}
    scopes = {k: census_scope(c) for k, c in census_by_layer.items()}
    scoped = [k for k, v in scopes.items() if v is not None]
    if scoped and len(scoped) != len(census_by_layer):
        raise ScopeError(f"layer(s) {', '.join(scoped)} are scoped and the rest are full: one rollup cannot be both")
    if declarations is None:
        # the id check needs the whole registry set, never a partial run — and a scoped run is a partial run even
        # when it reaches every layer (E1.9)
        full = set(census_by_layer) == set(ALL_LAYERS) and not scoped
        ids = [a["asset_id"] for c in census_by_layer.values() for a in c["assets"]] if full else None
        declarations = load_asset_declarations(registry_ids=ids)
    for k, c in census_by_layer.items():
        layers[k] = rollup_census(c, {a["asset_id"]: facts_for_asset(a, declarations) for a in c["assets"]})
        excluded[k] = {a["asset_id"]: rollup_excluded(c["layer"], a["measurements"]) for a in c["assets"]}
    head = dict(registry_revision=REGISTRY_REVISION, registry_fingerprint=registry_fingerprint())
    if scoped:   # E1.9: the rollup header says it is partial, next to the registry revision it was computed under
        head["scope"] = dict(assets=sorted(x for v in scopes.values() for x in v["assets"]), partial=True,
                             layers=list(scoped), registry_revision=REGISTRY_REVISION)
    return dict(rollup=dict(**head, layers=layers),
                rollup_excluded=excluded)


# ─────────────────────────── E6 item (f): Carr `no-carriage` on D1, D2, D3 ───────────────────────────
# N-22 ruling principle 7 (provisional until the J1 review): "where no D-check fits because the asset carries nothing
# downstream by construction (a declared fact), that is check-level N/A by cause `no-carriage`. Where a check should
# fit but none exists, it is NO_DETECTOR (T4:329)." SS strict definition (2026-09-30): the asset has NO DAG dependents
# AND does not reach a served surface; being served IS downstream carriage. The cause is a CANDIDATE only: it releases
# nothing until NA_RULE_DECISIONS declares `Carr.D<n>#measured:no-carriage` (empty today, and no asset declares
# `terminal_by_construction` today, so no census cell changes). An absence is never the evidence (CLAUDE.md N.8): zero
# measured dependents and a null served_surface are NOT proof of anything; only the positive declared pointer is.
CARR_D_CHECKS = ("Carr.D1", "Carr.D2", "Carr.D3")
_CARR_NEVER = "never read as no-carriage"


def _count(v):
    """A measured non-negative integer count, else None (a bool, float, str or negative is not a measurement)."""
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def grade_carr_no_carriage(record_facts) -> dict:
    """The Carr.D1/D2/D3 `no-carriage` reading of one asset, from `record_facts` (pure; no I/O):
      declared_terminal_by_construction  the positive declared pointer (a str with at least one visible character), else undeclared
      declared_carriage                  {'served_surface': bool | None}  (absent/None = unknown; any other form is malformed)
      blocking_radius                    the census radius {'direct': int, 'transitive': int} (absent/None/malformed = unmeasured)
      measured_served                    the Dens.served verdict of this census run
    N/A (cause `no-carriage`, a CANDIDATE) ONLY when ALL hold: the pointer is declared; measured direct AND transitive
    dependents are both 0; `served_surface` is None or False (true contradicts; a non-bool is malformed); and the
    measured Dens.served verdict is EXACTLY 'N/A' (the only verdict meaning "scanned, no reference"). Every other
    Dens.served value (NO_DETECTOR, ERRORED, absent, a case variant) means "possibly served" (the scan did not run, a module
    names the table but no served select was found, comment-only, outside the scanned roots, unparsed, shared-only), which
    is not evidence of no carriage: NO_DETECTOR. A declaration that a measured fact contradicts is NO_DETECTOR with a
    `declaration_disagreements` entry (reported, never resolved); an unmeasured radius or no declaration is NO_DETECTOR.
    `served_surface` None does not block: the declared pointer is then the evidence, and the verdict text says so.

    LIMIT (N-22 principle 3): no detector exists that still catches a mis-declared terminal asset. D1-D3 are detector NONE,
    and the contradiction checks here are blind to undeclared edges: the blocking radius counts only DECLARED depends_on
    edges, so it under-reports an undeclared reader (bg_gochara_arcs is read by ka_gochara.py:412 with no depends_on edge;
    an L0 reader never adds an edge because Build.dag exempts bedrock reads; 14 of the 40 zero-dependent assets are L0),
    and to Dens scanner gaps. The `no-carriage` N/A RULE must stay UNDECLARED (NA_RULE_DECISIONS empty) until an
    inverse-readers detector exists: one that scans the registered writers' reads, bedrock included, for readers of the
    asset's tables, and gates the candidate on none found."""
    f = record_facts if isinstance(record_facts, dict) else {}
    tbc = f.get("declared_terminal_by_construction")
    if not (isinstance(tbc, str) and not _blank_text(tbc)):
        return dict(v=NO_DET, measured=f"NO_DETECTOR — no terminal_by_construction declared: carriage is unknown, {_CARR_NEVER}")
    car = f.get("declared_carriage")
    if car is not None and not isinstance(car, dict):
        return dict(v=NO_DET, measured=f"NO_DETECTOR — the declared carriage is malformed ({car!r}: not an object); the "
                                       f"declared pointer ({tbc!r}) cannot be relied on, {_CARR_NEVER}")
    served = car.get("served_surface") if isinstance(car, dict) else None
    if served is not None and not isinstance(served, bool):
        return dict(v=NO_DET, measured=f"NO_DETECTOR — carriage.served_surface is malformed ({served!r}: only null, true or "
                                       f"false are forms); the declared pointer ({tbc!r}) cannot be relied on, {_CARR_NEVER}")
    br = f.get("blocking_radius")
    direct = _count(br.get("direct")) if isinstance(br, dict) else None
    trans = _count(br.get("transitive")) if isinstance(br, dict) else None
    ms = f.get("measured_served")
    bad = []
    if served is True:
        bad.append(dict(field="carriage.served_surface", declared=True, terminal_by_construction=tbc))
    if direct is not None and trans is not None and (direct > 0 or trans > 0):
        bad.append(dict(field="terminal_by_construction", declared=tbc,
                        measured_dependents=dict(direct=direct, transitive=trans)))
    if ms in (PASS, FAIL, PARTIAL):
        bad.append(dict(field="terminal_by_construction", declared=tbc, measured_served=ms))
    if bad:
        what = []
        if served is True:
            what.append("carriage.served_surface is declared true (reaches a served surface)")
        if direct is not None and trans is not None and (direct > 0 or trans > 0):
            what.append(f"measured dependents are direct {direct}, transitive {trans}")
        if ms in (PASS, FAIL, PARTIAL):
            what.append(f"Dens.served measured {ms} (a served read was found)")
        return dict(v=NO_DET, declaration_disagreements=bad,
                    measured=f"NO_DETECTOR — the declared terminal_by_construction pointer ({tbc!r}) is contradicted: "
                             f"{'; '.join(what)}; {_CARR_NEVER}")
    if direct is None or trans is None:
        return dict(v=NO_DET, measured=f"NO_DETECTOR — dependents unmeasured (the blocking radius is absent or not a count); "
                                       f"the declared pointer ({tbc!r}) cannot be checked against the DAG, {_CARR_NEVER}")
    if not (isinstance(ms, str) and ms == NA):
        return dict(v=NO_DET, measured=f"NO_DETECTOR — Dens.served is {ms!r}, not 'N/A' (scanned, no reference): the asset is "
                                       f"possibly served (scan not run, a served select not found or not attributable), so the "
                                       f"declared pointer ({tbc!r}) is not corroborated; {_CARR_NEVER}")
    sv = ("served_surface declared false" if served is False else
          "served_surface not declared (null: the declared pointer is the evidence)")
    return _na(f"declared terminal_by_construction ({tbc!r}); measured dependents direct {direct}, transitive {trans}; "
               f"Dens.served N/A (scanned, no reference); {sv}; the declared pointer is the evidence (a candidate, not a "
               "rule: released only by a declared rule, which must stay undeclared until an inverse-readers detector exists)",
               "no-carriage")


def carr_checks(record_facts) -> dict:
    """measure()'s Carr.D1/D2/D3 records for one asset: {} unless the asset DECLARES a terminal_by_construction pointer
    (an undeclared asset emits nothing, so its cell reads the rollup's own `not measured` NO_DETECTOR exactly as before;
    an explicit NO_DETECTOR record per check would change every cell's check text for no new information). A declared
    asset gets one independent record per check (the same grading: the declared fact covers D1, D2 and D3 alike)."""
    f = record_facts if isinstance(record_facts, dict) else {}
    tbc = f.get("declared_terminal_by_construction")
    if not (isinstance(tbc, str) and not _blank_text(tbc)):
        return {}
    r = grade_carr_no_carriage(f)
    return {c: dict(r, **({"declaration_disagreements": list(r["declaration_disagreements"])}
                          if "declaration_disagreements" in r else {})) for c in CARR_D_CHECKS}


# ─────────────────────────── E6 packet (c): the Null and Narr checks ───────────────────────────
# Design: /Users/Dev/suvarna-evidence/E6.1/packet_c_design.md. Each check is a pure grader over inputs the census
# reads (declarations, catalog, writer code, tests on disk); measure() calls `prose_checks`, so the saved-census
# harness and the unit tests run exactly what measure() runs. INCONCLUSIVE is a measured STATE (`inconclusive: true`
# on a NO_DETECTOR record), never a verdict and never a PASS. Null can never read PASS ("never PASS alone", Track E E6.1).
PROSE_JSON_TYPES = ("json", "jsonb")
_EMPTY_JSON_DEFAULT = re.compile(r"\s*'\s*(?:\{\s*\}|\[\s*\])\s*'\s*(?:::\s*jsonb?)?\s*", re.I)



def _json_entry(entry: str) -> bool:
    return parse_prose_field(entry)[1] is not None


def grade_narr_agree_tables(entries, own) -> dict:
    """Narr.agree over every table the asset owns (`own`: table -> (columns | None, types | None)): a declared prose
    entry must resolve to a column of at least one owned table (a multi-table asset keeps its narration column in a
    table other than the registry's target_table). FAIL: a column found in no owned table while every owned table's
    columns are known, or a JSON-path entry whose column is typed non-JSON everywhere it is found. PASS: all resolve
    (JSON types verified). PARTIAL: names resolve but a JSON-path column's type was not read. NO_DETECTOR: no owned
    table, or a missing column could sit in a table whose columns are unknown (never 'zero columns')."""
    if not own:
        return dict(v=NO_DET, measured="NO_DETECTOR — no target table to read the declared prose columns against")
    known = {t: set(c) for t, (c, _ty) in own.items() if isinstance(c, (list, tuple, set)) and c}
    unknown = sorted(t for t in own if t not in known)
    names = ", ".join(own)
    parsed = [(e, *parse_prose_field(e)) for e in entries]
    missing = [e for e, col, _ in parsed if not any(col in cs for cs in known.values())]
    if missing:
        if unknown:
            return dict(v=NO_DET, measured=f"NO_DETECTOR — {', '.join(missing)} not found in the known columns of {names}, and "
                                           f"the columns of {', '.join(unknown)} are unknown (never 'zero columns')")
        return dict(v=FAIL, measured=f"declared prose column(s) not among the columns of {names}: {', '.join(missing)}")
    wrong, unread = [], []
    for e, col, path in parsed:
        if path is None:
            continue
        kinds = [(own[t][1] or {}).get(col) for t in known if col in known[t]]
        if any(k and k.lower() in PROSE_JSON_TYPES for k in kinds):
            continue
        if any(k is None for k in kinds):
            unread.append(col)
        else:
            wrong.append(f"{col} ({', '.join(sorted(set(kinds)))})")
    if wrong:
        return dict(v=FAIL, measured=f"JSON-path entries on non-JSON column(s) of {names}: {', '.join(wrong)}")
    if unread:
        return dict(v=PARTIAL, measured=f"every declared column exists in {names}; the type of JSON-path column(s) "
                                        f"{', '.join(sorted(set(unread)))} was not read")
    return dict(v=PASS, measured=f"all {len(parsed)} declared prose entr{'y' if len(parsed) == 1 else 'ies'} resolve to "
                                 f"column(s) of {names} (names, and JSON types for path entries; the writer binding is "
                                 "the declaration tests' claim, not read here)")


def grade_narr_agree(entries, table, columns, types) -> dict:
    """Single-table form of grade_narr_agree_tables (table, its columns, its column types)."""
    return grade_narr_agree_tables(entries, {table: (columns, types)} if table else {})


def _holders(col, own):
    """The owned tables whose KNOWN columns include `col`."""
    return [t for t, v in own.items() if isinstance(v[0], (list, tuple, set)) and v[0] and col in v[0]]


def grade_null_schema_default_tables(entries, own) -> dict:
    """Null.schema_default over the asset's owned tables (`own`: table -> (columns, types, defaults)): each declared
    entry is read against the default of the owned table(s) that HOLD its column (a same-named column elsewhere is not
    read). FAIL names a non-NULL default (an empty JSON container on a path-only column is structure, not a stand-in).
    PARTIAL (never PASS) when none; NO_DETECTOR when an entry's column is held by no owned table or its table's
    defaults were not read."""
    parsed = [parse_prose_field(e) for e in entries]
    hit, unread = [], []
    for col in sorted({c for c, _ in parsed}):
        held = _holders(col, own)
        if not held:
            unread.append(f"{col} (no owned table holds it)")
            continue
        for t in held:
            dflts = own[t][2] if len(own[t]) > 2 else None
            if not isinstance(dflts, dict):
                unread.append(f"{col} (defaults of {t} not read)")
                continue
            d = dflts.get(col)
            if d in (None, ""):
                continue
            if all(path is not None for c2, path in parsed if c2 == col) and _EMPTY_JSON_DEFAULT.fullmatch(d):
                continue
            hit.append(f"{t}.{col} DEFAULT {d}")
    if hit:
        return dict(v=FAIL, measured="declared prose column(s) carry a non-NULL schema default: " + "; ".join(hit))
    if unread:
        return dict(v=NO_DET, measured="NO_DETECTOR — the column default could not be read for: " + "; ".join(unread))
    cols = sorted({c for c, _ in parsed})
    return dict(v=PARTIAL, measured=f"no schema default on the declared prose column(s) {', '.join(cols)}; writer "
                                    "literal fallbacks and constant columns are not measured here, so this is never PASS")


def grade_null_schema_default(entries, columns, defaults) -> dict:
    """Single-table form of grade_null_schema_default_tables (the target table's columns and defaults)."""
    if not isinstance(columns, (list, tuple, set)) or not columns or not isinstance(defaults, dict):
        return dict(v=NO_DET, measured="NO_DETECTOR — the target table's columns or column defaults were not read")
    return grade_null_schema_default_tables(entries, {"(table)": (list(columns), None, defaults)})


# Placeholder literals that stand in for NULL in prose (closed, lowercase; compared trimmed and lowercased).
PROSE_PLACEHOLDERS = ("", "n/a", "na", "none", "null", "unknown", "tbd", "-", "--", "undefined", "nan")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SCOPE_COUNT = re.compile(r"\s*select\s+count\(\s*(?:\*|1)\s*\)(?:\s+as\s+\w+)?\s+from\s+(?:public\.)?(\w+)"
                          r"(\s+where\s+.+?)?\s*;?\s*", re.I | re.S)
_SCOPE_BANNED = re.compile(r"\b(?:select|join|group|having|union|limit|order|intersect|except)\b|;", re.I)


def _count_scope_tail(count_sql: str, table: str):
    """The ` WHERE ...` tail (or "") of a registry count_sql that is a plain `SELECT count(*) FROM <table> [WHERE ...]`
    over `table`; None for any other shape (join, group, union, subselect, constant, another table): the asset's
    own rows cannot then be scoped from it."""
    q = re.sub(r"--[^\n]*", "", count_sql or "")
    m = _SCOPE_COUNT.fullmatch(q)
    if not m or m.group(1).lower() != (table or "").lower():
        return None
    tail = (m.group(2) or "").strip()
    if tail and _SCOPE_BANNED.search(tail):
        return None
    return " " + tail if tail else ""


def _in_list() -> str:
    return ", ".join("'" + p + "'" for p in PROSE_PLACEHOLDERS)


# whitespace class for "blank": the POSIX space class (space, tab, LF, VT, FF, CR) plus NBSP, zero-width space,
# U+2000-200A (en/em/thin... spaces) and the BOM; the same class text is valid in a PostgreSQL ARE and in Python re
_WS = r"[\s\u00A0\u200B\u2000-\u200A\uFEFF]"
_WS_TRIM_PY = f"^{_WS}+|{_WS}+$"
_WS_TRIM = f"'{_WS_TRIM_PY}', '', 'g'"


def prose_row_counts_sql(table: str, entries, where_tail: str, types=None) -> str:
    """One read-only count query: per declared entry, `count(*) FILTER` rows whose text is checkable (non-NULL, a TEXT
    value, not blank, not a placeholder) and rows holding a blank/placeholder string instead of NULL. A plain column
    reads `"c"::text` (a json/jsonb column must hold a JSON string, an array column is never text: `types` = column ->
    data_type); a JSON path `("c"::jsonb #>> '{k,k}')` only where the leaf is a JSON string; an array path (`[*]`) an
    EXISTS over jsonb_path_query. Trimming covers space, tab, CR and LF. Identifiers come from parse_prose_field
    (regex-validated): ValueError otherwise."""
    if not _IDENT.fullmatch(table or "") or not entries:
        raise ValueError("prose_row_counts_sql needs a table identifier and at least one declared entry")
    items = []
    for e in entries:
        col, path = parse_prose_field(e)
        if path and PROSE_WILDCARD in path:
            jp = "$"
            for seg in path:
                jp += "[*]" if seg == PROSE_WILDCARD else f'."{seg}"'
            src = (f"EXISTS (SELECT 1 FROM jsonb_path_query(\"{col}\"::jsonb, '{jp}') AS e(x) WHERE jsonb_typeof(x) = 'string' "
                   f"AND lower(regexp_replace(x #>> '{{}}', {_WS_TRIM})) ")
            checkable, blank = src + f"NOT IN ({_in_list()}))", src + f"IN ({_in_list()}))"
        else:
            ty = ((types or {}).get(col) or "").lower()
            if path is not None:
                keys = ",".join(path)
                v = f"(\"{col}\"::jsonb #>> '{{{keys}}}')"
                guard = f"jsonb_typeof(\"{col}\"::jsonb #> '{{{keys}}}') = 'string' AND "
            elif ty in ("json", "jsonb"):
                v, guard = f'("{col}"::jsonb #>> \'{{}}\')', f'jsonb_typeof("{col}"::jsonb) = \'string\' AND '
            elif ty == "array" or ty.endswith("[]") or ty.startswith("_"):
                v, guard = f'"{col}"::text', "FALSE AND "
            else:
                v, guard = f'"{col}"::text', ""
            tr = f"lower(regexp_replace({v}, {_WS_TRIM}))"
            checkable = ("(FALSE)" if guard == "FALSE AND " else f"{guard}{v} IS NOT NULL AND {tr} NOT IN ({_in_list()})")
            blank = ("(FALSE)" if guard == "FALSE AND " else f"{guard}{v} IS NOT NULL AND {tr} IN ({_in_list()})")
        items += [f"count(*) FILTER (WHERE {checkable})::text", f"count(*) FILTER (WHERE {blank})::text"]
    return f"SELECT {', '.join(items)} FROM {table}{where_tail}"


def prose_row_counts(table: str, entries, where_tail: str, types=None) -> dict:
    """entry -> dict(checkable=int, blank=int), from one read-only query. A malformed answer raises Unknown."""
    row = (psql(prose_row_counts_sql(table, entries, where_tail, types)) or [[]])[0]
    if len(row) != 2 * len(entries):
        raise Unknown(f"prose row-count query answered {len(row)} value(s) for {len(entries)} declared entr(ies)")
    try:
        return {e: dict(checkable=int(row[2 * i]), blank=int(row[2 * i + 1])) for i, e in enumerate(entries)}
    except ValueError as exc:
        raise Unknown(f"prose row-count query returned a non-integer: {exc}") from exc


UPPER_BOUND = "whole-table upper bound"


def grade_narr_checkable(entries, counts) -> dict:
    """Narr.checkable (SS 2026-10-01): rows actually CHECKABLE per declared entry (`counts[entry]` = dict(checkable,
    blank, scope), or None = unknown for that entry). PASS: every entry has >= 1 checkable row in a chart-scoped (or
    chart-free) count; PARTIAL: some have none / are unknown, or the count is a whole-table upper bound (the scope is
    named). Zero everywhere, unknown everywhere, or no row data: INCONCLUSIVE (NO_DETECTOR + inconclusive), never PASS."""
    if not isinstance(counts, dict):
        return dict(v=NO_DET, inconclusive=True, measured="INCONCLUSIVE: no row data was read for the declared prose "
                                                          "entries (scope unsupported or not measured); no PASS is possible")
    n = {e: (None if counts.get(e) is None else int(counts[e].get("checkable", 0))) for e in entries}
    scopes = sorted({counts[e]["scope"] for e in entries if counts.get(e) and counts[e].get("scope")})
    extra = dict(scope="; ".join(scopes)) if scopes else {}
    text = ", ".join(f"{e}={'unknown' if k is None else k}" for e, k in n.items())
    if not any(n.values()):
        return dict(v=NO_DET, inconclusive=True, checkable=n, **extra,
                    measured=f"INCONCLUSIVE: 0 checkable rows on every declared entry ({text})")
    bad = [e for e, k in n.items() if not k]
    if bad:
        return dict(v=PARTIAL, checkable=n, **extra,
                    measured=f"checkable rows per declared entry: {text}; none or unknown on {', '.join(bad)}")
    if UPPER_BOUND in scopes:
        return dict(v=PARTIAL, checkable=n, **extra, measured=f"checkable rows per declared entry: {text}; the count is a "
                    f"{UPPER_BOUND} (count_sql unparseable, unshared table that carries chart_id): rows of other charts may count")
    return dict(v=PASS, checkable=n, **extra, measured=f"checkable rows per declared entry: {text} ({'; '.join(scopes) or 'scope n/a'})")


def grade_null_blank_rows(entries, counts) -> dict:
    """Null.blank_rows: declared prose rows holding a blank string or a placeholder literal instead of NULL. FAIL on
    any. PARTIAL (never PASS) when none in >= 1 checkable row; INCONCLUSIVE without row data or checkable rows."""
    if isinstance(counts, dict):
        bad = {e: (None if counts.get(e) is None else int(counts[e].get("blank", 0))) for e in entries}
        ub = {e for e in entries if (counts.get(e) or {}).get("scope") == UPPER_BOUND}
        hit = [f"{e}={k}" for e, k in bad.items() if k and e not in ub]
        hit_ub = [f"{e}={k}" for e, k in bad.items() if k and e in ub]
        if hit:
            return dict(v=FAIL, blank=bad, measured="blank or placeholder rows standing in for NULL in declared prose "
                                                    "column(s): " + ", ".join(hit)
                        + (f" (not counted: {', '.join(hit_ub)} in a {UPPER_BOUND})" if hit_ub else ""))
        if hit_ub:
            return dict(v=PARTIAL, blank=bad, measured=f"blank or placeholder rows ({', '.join(hit_ub)}) in a {UPPER_BOUND}: "
                        "they may belong to other charts, so this chart is not failed on them; chart-scope the count to decide")
        if any((counts.get(e) or {}).get("checkable", 0) for e in entries):
            unk = [e for e, k in bad.items() if k is None]
            return dict(v=PARTIAL, blank=bad, measured="no blank or placeholder row among the checkable prose rows"
                        + (f" (unknown for {', '.join(unk)})" if unk else "") + "; schema defaults are read by "
                        "Null.schema_default and writer literal fallbacks and constant columns are not measured, so "
                        "this is never PASS")
    return dict(v=NO_DET, inconclusive=True,
                measured="INCONCLUSIVE: no checkable prose rows were read for the declared entries")


_SIDECAR_PREFIX = "platform/python-sidecar/"
_TEST_FACTS: dict = {}


def python_tests(sidecar=None) -> list:
    """Every `test_*.py` under a `tests/` or `__tests__/` directory of the python sidecar, as (Path, text)."""
    root = Path(sidecar) if sidecar is not None else SIDECAR
    out = []
    for f in sorted(root.rglob("test_*.py")):
        if {"tests", "__tests__"} & set(f.relative_to(root).parts[:-1]):
            try:
                out.append((f, f.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                continue
    return out


def _cited_modules(evidence) -> list:
    """The dotted sidecar modules the declaration's evidence cites (`platform/python-sidecar/x/y.py:LINE`)."""
    out = []
    for c in _EVIDENCE_ANY_CITE_RE.findall(evidence or ""):
        if c.startswith(_SIDECAR_PREFIX) and c.endswith(".py"):
            d = c[len(_SIDECAR_PREFIX):-3].replace("/", ".")
            d = d[:-len(".__init__")] if d.endswith(".__init__") else d
            if d not in out:
                out.append(d)
    return out


def _dotted(node, bound):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Call):
        return None
    if not isinstance(node, ast.Name) or node.id not in bound:
        return None
    return ".".join([bound[node.id]] + parts[::-1])


_GENERIC_LEAVES = ("statement", "reason", "text", "summary", "description", "note")


_SKIP_WORD = re.compile(r"\b(?:skip\w*|xfail)\b", re.I)


def _skips(node, aliases=()) -> bool:
    """A skip/xfail decorator (`pytest.mark.skip[if]`, `unittest.skip*`, `xfail`), directly or through an alias name
    (`sk = pytest.mark.skip` ... `@sk`)."""
    for d in getattr(node, "decorator_list", []):
        u = ast.unparse(d)
        if _SKIP_WORD.search(u) or any(re.search(rf"\b{re.escape(a)}\b", u) for a in aliases):
            return True
    return False


def _path_loaded(node, loaders):
    """`loader('x.py')` where `loader` is a module-level helper that loads a module from a file path
    (spec_from_file_location): the token `<file>:x`, which a cited module of the same stem matches."""
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in loaders and node.args
            and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
            and node.args[0].value.endswith(".py")):
        return "<file>:" + node.args[0].value[:-3].replace("/", ".").split(".")[-1]
    return None


def _import_module_arg(node, bound):
    """`importlib.import_module('x')` / `import_module('x')` / an alias of it (`from importlib import import_module as im`):
    the dotted module string, else None."""
    if not (isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)):
        return None
    f = node.func
    name = _dotted(f, bound) if isinstance(f, (ast.Name, ast.Attribute)) else None
    if ast.unparse(f).endswith("import_module") or (name or "").endswith("import_module"):
        return node.args[0].value
    return None


def _test_facts(path: Path, text: str):
    """(functions, module_skipped) for a test file — cached; None if unparseable. One record per `test*` function:
    the dotted names it CALLS, whether it has a real assert, the leaf names it references (`leaves`; `assert_leaves`
    = those inside asserts / assert-call arguments) and whether it is skipped (decorator, class decorator, a
    `pytest.skip(` call, or a module `pytestmark` skip)."""
    key = (str(path), text)
    if key in _TEST_FACTS:
        return _TEST_FACTS[key]
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        _TEST_FACTS[key] = None
        return None
    try:
        pkg = list(path.relative_to(SIDECAR).parts[:-1])
    except ValueError:
        pkg = []
    bound: dict = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.asname:
                    bound[a.asname] = a.name
                else:
                    bound[a.name.split(".")[0]] = a.name.split(".")[0]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg[:len(pkg) - (n.level - 1)] if n.level - 1 <= len(pkg) else []
                mod = ".".join(base + ([n.module] if n.module else []))
            else:
                mod = n.module or ""
            for a in n.names:
                bound[a.asname or a.name] = f"{mod}.{a.name}" if mod else a.name
    # a helper that RETURNS an imported module/name (`def _mod(): from x import m; return m`) binds `w = _mod()`;
    # `w = importlib.import_module('x')` binds w to x
    rets = {}
    loaders = {f.name for f in tree.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
               and any(isinstance(c, ast.Call) and ast.unparse(c.func).endswith("spec_from_file_location") for c in ast.walk(f))}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for r in ast.walk(fn):
                if isinstance(r, (ast.Return, ast.Yield)) and r.value is not None:
                    d = (_dotted(r.value, bound) if isinstance(r.value, (ast.Name, ast.Attribute))
                         else _import_module_arg(r.value, bound) or _path_loaded(r.value, loaders))
                    if d:
                        rets[fn.name] = d
                        if any("fixture" in ast.unparse(dd) for dd in fn.decorator_list):
                            bound[fn.name] = d          # a test parameter named like the fixture is that module
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            f = n.value.func
            tgt = [t.id for t in n.targets if isinstance(t, ast.Name)]
            if isinstance(f, ast.Name) and f.id in rets:
                for t in tgt:
                    bound[t] = rets[f.id]
            elif _import_module_arg(n.value, bound) or _path_loaded(n.value, loaders):
                for t in tgt:
                    bound[t] = _import_module_arg(n.value, bound) or _path_loaded(n.value, loaders)
    aliases = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) and _SKIP_WORD.search(ast.unparse(n.value))
               for t in n.targets if isinstance(t, ast.Name) and t.id != "pytestmark"}
    mod_skip = any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in n.targets)
                   and _SKIP_WORD.search(ast.unparse(n.value)) for n in tree.body)
    cls_skip = {id(c): _skips(k, aliases) for k in ast.walk(tree) if isinstance(k, ast.ClassDef)
                for c in k.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def leaves_of(root, acc):
        for n in ast.walk(root):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                acc.add(n.value)
            elif isinstance(n, ast.Attribute):
                acc.add(n.attr)
            elif isinstance(n, ast.Name):
                acc.add(n.id)
            elif isinstance(n, ast.keyword) and n.arg:
                acc.add(n.arg)
    def facts_of(fn):
        calls, leaves, aleaves, asserts, called = set(), set(), set(), False, set()
        skipped = _skips(fn, aliases) or cls_skip.get(id(fn), False)
        leaves_of(fn, leaves)
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                d = _dotted(n.func, bound)
                if d:
                    calls.add(d)
                if isinstance(n.func, ast.Name):
                    called.add(n.func.id)
                nm = ast.unparse(n.func)
                if nm in ("pytest.skip", "skip", "pytest.xfail", "xfail"):
                    skipped = True
                if isinstance(n.func, ast.Attribute) and (n.func.attr.startswith("assert") or n.func.attr == "raises"):
                    asserts = True
                    for x in list(n.args) + [k.value for k in n.keywords]:
                        leaves_of(x, aleaves)
            elif isinstance(n, ast.Assert):
                if not (isinstance(n.test, ast.Constant) and n.test.value):      # `assert True` / `assert 1` prove nothing
                    asserts = True
                    leaves_of(n.test, aleaves)
        return dict(name=fn.name, calls=calls, asserts=asserts, leaves=leaves, assert_leaves=aleaves, skipped=skipped,
                    called=called)
    helpers = {n.name: facts_of(n) for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("test")}
    funcs = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) or not fn.name.startswith("test"):
            continue
        f = facts_of(fn)
        for h in f["called"]:                       # ONE level of module-level helper: its calls, asserts and leaves
            if h in helpers:
                f["calls"] |= helpers[h]["calls"]
                f["leaves"] |= helpers[h]["leaves"]
                f["asserts"] = f["asserts"] or helpers[h]["asserts"]
        funcs.append(f)
    _TEST_FACTS[key] = (funcs, mod_skip)
    return _TEST_FACTS[key]


def _calls_module(call: str, mod: str) -> bool:
    """A dotted call lies in `mod`, or in a module loaded from a file path whose stem is mod's last component."""
    if call == mod or call.startswith(mod + "."):
        return True
    return call.startswith("<file>:") and call[len("<file>:"):].split(".")[0] == mod.rsplit(".", 1)[-1]


def _leaf_in(leaf: str, names) -> bool:
    """A declared leaf is referenced when a name contains it (`citation_human` in `_citation_human_position`) or is one of
    its underscore tokens of length >= 5 (`reason` for `verdict_reason`)."""
    toks = {t for t in leaf.split("_") if len(t) >= 5}
    return any(leaf in n or n in toks for n in names)


def narr_fidelity_scan(entries, evidence, tests) -> dict:
    """Narr.fidelity_test (CLAUDE.md N.7 item 5): a test exists that exercises the narration builder. Builder modules
    = the .py files the declaration's evidence cites. A test QUALIFIES when it calls a name imported from a builder
    module and contains an assert; it COVERS an entry when it also references the entry's leaf (column or last key).
    FAIL: no qualifying test. PARTIAL: >= 1 qualifying test. PASS is NOT reachable (SS decision: structural coverage
    does not prove a test grades the sentence). NO_DETECTOR: no readable builder module cited."""
    mods = _cited_modules(evidence)
    if not mods:
        return dict(v=NO_DET, measured="NO_DETECTOR — the declaration's evidence cites no readable sidecar writer module "
                                       "to look for tests of")
    leaves = {e: (lambda c, p: [k for k in (p or ()) if k != PROSE_WILDCARD][-1] if p else c)(*parse_prose_field(e))
              for e in entries}
    spec = [e for e, lf in leaves.items() if lf not in _GENERIC_LEAVES]
    spec_leaves = {leaves[e] for e in spec}
    qual, covered = [], set()
    for path, text in tests:
        f = _test_facts(Path(path), text)
        if not f or f[1]:                                  # unparseable, or the module is skipped
            continue
        for fn in f[0]:
            if fn["skipped"] or not fn["asserts"] or not any(_calls_module(c, m) for c in fn["calls"] for m in mods):
                continue
            qual.append(Path(path).name)
            beside = any(_leaf_in(lf, fn["leaves"]) for lf in spec_leaves)
            covered |= {e for e, lf in leaves.items()
                        if (_leaf_in(lf, fn["leaves"]) if lf not in _GENERIC_LEAVES
                            else (lf in fn["assert_leaves"] or (lf in fn["leaves"] and beside)))}
    if not qual:
        return dict(v=FAIL, covered=[], tests=[], measured=f"no (unskipped) test function calls the builder module(s) "
                    f"{', '.join(mods)} and asserts in the same function — N.7 item 5 (a fidelity test for the narration) "
                    "has no evidence in the repo")
    cov = [e for e in entries if e in covered]
    unc = [e for e in entries if e not in covered]
    names = sorted(set(qual))
    if not cov:
        return dict(v=PARTIAL, covered=[], tests=names, measured=f"{len(names)} test file(s) call the builder and assert "
                    f"({', '.join(names[:4])}): tests call the builder but none names a declared field (direct or indirect); "
                    f"declared: {', '.join(entries)}; structural only, never PASS")
    return dict(v=PARTIAL, covered=cov, tests=names, measured=(
        f"structural only: {len(names)} test file(s) call the builder and assert in the same test function "
        f"({', '.join(names[:4])}{'…' if len(names) > 4 else ''}); declared field(s) referenced: {', '.join(cov)}"
        + (f"; no qualifying test names: {', '.join(unc)}" if unc else "")
        + "; whether the assertion grades the sentence is not read, so this never reads PASS"))


_LINTS: dict = {}


def _lint_module(name: str):
    """A sibling governance lint, loaded by path once (registered in sys.modules: its dataclasses need it)."""
    if name not in _LINTS:
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"_census_{name}", Path(__file__).resolve().parent / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _LINTS[name] = mod
    return _LINTS[name]


def _flat_str(node):
    """The text of a string expression made of constants, f-string constant parts and `+` concatenation; None otherwise."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else " " for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _flat_str(node.left), _flat_str(node.right)
        return None if a is None or b is None else a + b
    return None


def _fact_category_surface(text: str) -> bool:
    """Real code that SELECTs chart_facts by fact_category: a non-docstring string expression (constant, f-string,
    `+` concatenation) holding SELECT, chart_facts and fact_category. A comment, a docstring or two unrelated strings
    each mentioning one word are not a surface. Raises SyntaxError for unparseable source."""
    tree = ast.parse(text)
    docs = _docstring_ids(tree)
    for n in ast.walk(tree):
        if id(n) in docs or not isinstance(n, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            continue
        t = _flat_str(n)
        if t and re.search(r"\bSELECT\b", t, re.I) and "chart_facts" in t and "fact_category" in t:
            return True
    return False


def _raw_token_surface(col: str) -> bool:
    """A column the raw-token lint's narrative-field pattern covers: signal_headline_text, signal_text, *_thesis, *_narrative."""
    return col in ("signal_headline_text", "signal_text") or col.endswith(("_thesis", "_narrative"))


def narr_lint_scan(paths, columns=()) -> dict:
    """Narr.lint: the existing narration lints (check_fact_category_pinning: the D1 class, N.7 item 2;
    check_no_raw_token_in_narrative) over the writer's resolved scope files, with their own allowlists. FAIL: a
    non-allowlisted violation (file:line). PARTIAL: only allowlisted ones (named; CI accepts them, the census does not
    call them clean). PASS needs a lint SURFACE that applied: fact_category selection of chart_facts in the scope
    (fact-category-pin) and/or a declared column the raw-token lint's field pattern covers (raw-token); with neither,
    the lints say nothing about this asset: NO_DETECTOR 'not applicable' (a clean scan of code a lint cannot see is
    not a pass). `applied` names the surfaces. NO_DETECTOR: no file in scope. ERRORED: unreadable file/lint."""
    paths = [Path(p) for p in paths]
    if not paths:
        return dict(v=NO_DET, applied=[], measured="NO_DETECTOR — no writer file in scope to run the narration lints over")
    try:
        fcp, rt = _lint_module("check_fact_category_pinning"), _lint_module("check_no_raw_token_in_narrative")
        allow_f, allow_r = fcp.load_allowlist(fcp.ALLOWLIST_PATH), rt.load_allowlist(rt.ALLOWLIST_PATH)
        new, old = [], []
        fact_surface = False
        for p in paths:
            text = p.read_text(encoding="utf-8")
            fact_surface = fact_surface or _fact_category_surface(text)
            try:
                rel = p.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                rel = str(p)
            vf = [fcp.Violation(rel, ln, "python", "sql_select", sn, "") for ln, sn in fcp.scan_python_text(text)]
            vr = [rt.Violation(rel, ln, kind, sn, "") for ln, kind, sn in rt.scan_py_file(text)]
            for tag, vs, allow, mod in (("fact-category-pin", vf, allow_f, fcp), ("raw-token", vr, allow_r, rt)):
                a, n = mod.partition_allowlisted(vs, allow)
                old += [f"{tag} {v.file}:{v.line}" for v in a]
                new += [f"{tag} {v.file}:{v.line}" for v in n]
    except (OSError, ValueError, AttributeError, SyntaxError, ImportError) as exc:
        return dict(v=ERRORED, measured=f"check errored: narration lint could not run ({type(exc).__name__}: {exc})")
    applied = (["fact-category-pin"] if fact_surface else []) + (["raw-token"] if any(_raw_token_surface(c) for c in columns) else [])
    if new:
        return dict(v=FAIL, applied=applied, measured="narration lint violation(s) in the writer scope: " + "; ".join(new))
    if old:
        return dict(v=PARTIAL, applied=applied, measured="only allowlisted narration lint violation(s) in scope: " + "; ".join(old))
    if not applied:
        return dict(v=NO_DET, applied=[], measured=f"NO_DETECTOR — the narration lints are not applicable to this asset: no "
                    f"chart_facts fact_category selection in its {len(paths)}-file writer scope and no declared column the "
                    "raw-token lint covers; a clean scan of code they cannot see is not a pass")
    return dict(v=PASS, applied=applied, measured=f"{len(paths)} writer scope file(s) clean under the {' and '.join(applied)} "
                                                  "narration lint(s) that applied (their own allowlists applied)")


_QQ = r"(?:ONLY\s+)?(?:public\.)?\"?"
_INSERT_COLS = re.compile(r"INSERT\s+INTO\s+" + _QQ + r"([A-Za-z_][A-Za-z_0-9]*)\"?\s*(\([^)]*\))?", re.I)
_UPDATE_SET = re.compile(r"\bUPDATE\s+" + _QQ + r"([A-Za-z_][A-Za-z_0-9]*)\"?\s+SET\s+(.*?)(?=\bWHERE\b|\bFROM\b|\bRETURNING\b|\Z)",
                         re.I | re.S)


def written_columns(units, tables):
    """table -> the columns the writer's resolved scope INSERTs (column list) or UPDATEs (SET targets) on `tables`.
    None when a write to one of them cannot be read (no column list, an unresolved `{?}` name): never a guess."""
    tset = {t.lower() for t in tables if t}
    out: dict = {}
    for u in units:
        for node in u["nodes"]:
            for text, _ln in _sql_texts(dict(u, nodes=[node])):
                for m in _INSERT_COLS.finditer(text):
                    if m.group(1).lower() not in tset:
                        continue
                    if not m.group(2) or "{?}" in m.group(2):
                        return None
                    out.setdefault(m.group(1).lower(), set()).update(
                        c.strip().strip('"') for c in m.group(2)[1:-1].split(",") if c.strip())
                for m in _UPDATE_SET.finditer(text):
                    if m.group(1).lower() not in tset:
                        continue
                    if "{?}" in m.group(2):
                        return None
                    for a in _split_top(m.group(2)):
                        if "=" in a:
                            out.setdefault(m.group(1).lower(), set()).add(a.split("=", 1)[0].strip().strip('"'))
    return out


def prose_vocabulary(declarations) -> set:
    """The columns some asset's declaration lists as prose (the file's own narration-column vocabulary)."""
    return {parse_prose_field(e)[0] for d in (declarations or {}).values() if isinstance(d, dict)
            for e in (d.get("prose_fields") or [])}


def prose_reverse_leg(written, vocabulary) -> list:
    """`[]`-declared asset: the `table.column` writes that hit a column the declarations treat as narration elsewhere
    (principle 8: such a column present while prose_fields is empty reads FAIL). Write-column names only: it does not
    prove 'composes no string' (the AST proofs in test_e6_1_declarations.py do, per asset)."""
    return sorted(f"{t}.{c}" for t, cols in (written or {}).items() for c in cols if c in vocabulary)


NARR_CHECKS = ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint")
NULL_CHECKS = ("Null.schema_default", "Null.blank_rows")


def _own3(ctx: dict) -> dict:
    """ctx -> {table: (columns, types, defaults)}: the owned tables when supplied (a 2-tuple has unread defaults),
    else the single target table with ctx's columns/types/defaults."""
    if ctx.get("own") is not None:
        return {t: (v[0], v[1], v[2] if len(v) > 2 else None) for t, v in ctx["own"].items()}
    return {ctx["table"]: (ctx.get("columns"), ctx.get("types"), ctx.get("defaults"))} if ctx.get("table") else {}


def prose_checks(aid: str, decl, ctx: dict) -> dict:
    """The six Narr/Null records for one asset, from its declaration entry (`prose_fields`, `evidence`) and `ctx`:
    table, columns, types, defaults, counts (None = not read), paths (writer scope files), tests, vocabulary, written
    (None = the writer's writes could not be read). null prose_fields = undeclared: every check NO_DETECTOR, never
    'no prose'. [] = positive declaration: measured N/A candidates (causes no-prose / no-prose-declared; no rule is
    declared, so the rollup reads them NO_DETECTOR) unless a write hits a column the file treats as narration (agree
    FAIL, the rest NO_DETECTOR) or the writes are unreadable (NO_DETECTOR)."""
    allc = NARR_CHECKS + NULL_CHECKS
    pf = decl.get("prose_fields") if isinstance(decl, dict) else None
    if pf is None:
        return {c: dict(v=NO_DET, measured=f"NO_DETECTOR — prose_fields is undeclared for {aid}: never read as 'no prose'")
                for c in allc}
    if not pf:
        if ctx.get("written") is None:
            return {c: dict(v=NO_DET, measured=f"NO_DETECTOR — {aid} declares prose_fields [] but its writes could not be "
                                               "read, so the declaration cannot be checked") for c in allc}
        hits = prose_reverse_leg(ctx["written"], ctx.get("vocabulary") or set())
        if hits:
            out = {c: dict(v=NO_DET, measured=f"NO_DETECTOR — {aid} declares prose_fields [] but Narr.agree failed") for c in allc}
            out["Narr.agree"] = dict(v=FAIL, measured=f"prose_fields is [] but the writer writes column(s) the declarations "
                                                      f"treat as narration: {', '.join(hits)}")
            return out
        why = ("prose_fields [] declared and no write to a column the declarations treat as narration (write-column "
               "names only; the composed-string proof is the declaration tests')")
        return {c: _na(why, "no-prose" if c.startswith("Narr.") else "no-prose-declared") for c in allc}
    ev = (decl.get("evidence") or {}).get("prose_fields") if isinstance(decl.get("evidence"), dict) else None
    out = {}
    for crit, fn in (
            ("Narr.agree", lambda: grade_narr_agree_tables(pf, {t: (v[0], v[1]) for t, v in _own3(ctx).items()})),
            ("Narr.checkable", lambda: grade_narr_checkable(pf, ctx.get("counts"))),
            ("Narr.fidelity_test", lambda: narr_fidelity_scan(pf, ev, ctx.get("tests") or ())),
            ("Narr.lint", lambda: narr_lint_scan(ctx.get("paths") or (), [parse_prose_field(e)[0] for e in pf])),
            ("Null.schema_default", lambda: grade_null_schema_default_tables(pf, _own3(ctx))),
            ("Null.blank_rows", lambda: grade_null_blank_rows(pf, ctx.get("counts")))):
        try:
            out[crit] = fn()
        except (Unknown, DeclarationsError) as exc:      # R41: one check's failure degrades only that check
            out[crit] = dict(v=ERRORED, measured=f"check errored: {exc}")
    if out.get("Narr.agree", {}).get("v") == PASS and ctx.get("written") is None:
        out["Narr.agree"] = dict(v=PARTIAL, measured=out["Narr.agree"]["measured"] + "; reverse leg unavailable: the writer's "
                                 "writes could not be read, so a prose-vocabulary column it writes without declaring is unchecked")
    if out.get("Narr.agree", {}).get("v") == PASS and ctx.get("written") is not None:
        # two-way: a column the declarations treat as narration that this writer writes but does not declare
        declared_cols = {parse_prose_field(e)[0] for e in pf}
        und = [h for h in prose_reverse_leg(ctx["written"], ctx.get("vocabulary") or set()) if h.split(".", 1)[1] not in declared_cols]
        if und:
            out["Narr.agree"] = dict(v=PARTIAL, measured=out["Narr.agree"]["measured"] + "; but the writer also writes "
                                     f"prose-vocabulary column(s) it does not declare (undeclared): {', '.join(und)}")
    return out


# R40: the psql subprocess timeout was hardcoded at 180s, which is shorter than a full-table
# duplicate scan on the estate's largest table (kala_field, 10.3M rows) can take — making the L3
# and `--layer all` census unrunnable on production. Configurable via env so an operator pointed
# at a much larger table than the ones this script was calibrated against can raise it without a
# code change.
PSQL_TIMEOUT_SECONDS = int(os.environ.get("NIKASHA_CENSUS_TIMEOUT_SECONDS", "180"))

# R231 (A_REVIEW2 G4): 78 of 86 L1–L5 `count_sql` are chart-scoped (`WHERE chart_id = $1`). Run
# standalone they cannot bind `$1`, so F2 correctly graded them ERRORED — and `Build.completion` was
# unmeasured above L0. The census now binds ONE chart scope, exactly as the engine does
# (`asset_runner._data_rows_present`: `count_sql.replace("$1", %s)` with the chart id as a quoted
# literal), and reads that chart's own build record. The canonical chart (CLAUDE.md §B) is the
# default; `362f9f17-…` is a dead phantom and is refused.
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_ID = os.environ.get("NIKASHA_CENSUS_CHART_ID", CANONICAL_CHART_ID).strip()
_PHANTOM_CHART_PREFIX = "362f9f17"
_PARAM_1 = re.compile(r"\$1(?!\d)")
_ANY_PARAM = re.compile(r"\$\d+")


def _view_count_sql(view: str, cols: list[str]) -> str:
    """R46: the census's count of a view target — its rows for the bound chart when the view carries
    `chart_id` (bound like any `$1` count), else the whole view."""
    return f"SELECT count(*) FROM {view}" + (" WHERE chart_id = $1" if "chart_id" in cols else "")


def _chart_scoped(count_sql: str) -> bool:
    return bool(_PARAM_1.search(count_sql or ""))


def _count_tables(count_sql: str) -> list[str]:
    """R42: the relations a count_sql reads (FROM / JOIN targets, in order, de-duplicated). One
    table is a plain count; several is a multi-table count (a sum or a join) whose total must be
    compared like-for-like and never presented as the target table's own rows; NONE is a constant
    (`SELECT 0 AS count`, bo_samvada) — a figure that cannot vary is not a measurement."""
    q = re.sub(r"--[^\n]*", "", count_sql or "")
    out: list[str] = []
    for t in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_.]*)", q, re.I):
        t = t.split(".")[-1].lower()
        if t not in out:
            out.append(t)
    return out


# R42: the build-record states that mean "a build completed and wrote these rows". `stale` is a
# completed build whose upstream has since moved (R45 grades staleness, W2-2); `error`,
# `incomplete`, `dormant` and `building` are not completions, so their rows_written — whatever it
# equals — is not a completed build agreeing with the live data.
COMPLETED_STATES = ("lit", "stale")


def _bind_chart(q: str, chart_id: str) -> str:
    """Bind `$1` to the chart scope as a quoted literal (the engine's own binding). Raises `Unknown`
    for a phantom chart id, a malformed one, or a `count_sql` with any OTHER unbound parameter —
    a query that cannot be bound is not measured, and never silently run half-bound."""
    if _PARAM_1.search(q):
        if chart_id.startswith(_PHANTOM_CHART_PREFIX):
            raise Unknown(f"refusing chart scope {chart_id}: the 362f9f17-… chart id is a dead phantom")
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", chart_id):
            raise Unknown(f"chart scope {chart_id!r} is not a uuid")
    bound = _PARAM_1.sub(f"'{chart_id}'", q)
    left = sorted(set(_ANY_PARAM.findall(bound)))
    if left:
        raise Unknown(f"count_sql has unbound parameter(s) {', '.join(left)} — only $1 (chart scope) is bindable")
    return bound


class Unknown(Exception):
    """The instrument could not run. Never reported as clean."""


class CheckTimeout(Unknown):
    """R223 (A_REVIEW2 G3): the client-side psql timeout fired. Production's `statement_timeout`
    (30 min) is far above the census's client timeout (180 s), so a real timeout arrives as
    `subprocess.TimeoutExpired` — which is not an `Unknown`, escaped every per-check guard, and
    ended the whole run with exit 5. It is converted here, at the one place every query passes
    through, so a timed-out check degrades to ERRORED exactly like any other failed query (and a
    timed-out layer-wide read still aborts the layer, fail-closed, naming the read)."""


def psql(sql: str, sep: str = "\x1f", timeout: int | None = None) -> list[list[str]]:
    env = dict(os.environ)
    env.setdefault("PGCONNECT_TIMEOUT", "10")
    limit = timeout if timeout is not None else PSQL_TIMEOUT_SECONDS
    try:
        p = subprocess.run(["psql", "-tAX", "-F", sep, "-v", "ON_ERROR_STOP=1", "-c", sql],
                           capture_output=True, text=True, env=env, timeout=limit)
    except subprocess.TimeoutExpired as exc:
        raise CheckTimeout(f"client-side timeout after {limit}s (psql killed): "
                           f"{' '.join(sql.split())[:120]}") from exc
    if p.returncode != 0:
        raise Unknown((p.stderr.strip().splitlines() or ["psql failed"])[0])
    return [ln.split(sep) for ln in p.stdout.strip().split("\n") if ln.strip()]


def scalar(sql: str) -> str | None:
    r = psql(sql)
    return r[0][0] if r and r[0] else None


# ─────────────────────────── code-side scans ───────────────────────────

def _writer_files() -> list[Path]:
    """Writer modules only. `__init__.py` is the FRAMEWORK — it defines @register and documents what a
    writer must not do, so scanning it as a writer reports the framework's own docstring as a violation.
    The first run did exactly that."""
    if not WRITERS.is_dir():
        raise Unknown(f"writers directory not found: {WRITERS}")
    return [f for f in sorted(WRITERS.glob("*.py")) if f.name != "__init__.py"]


_PARSED: dict[tuple[str, str], ast.AST] = {}


def _parse(f: Path):
    """R20: cached per (path, content) — delegation-following reads the same seeder/helper modules for
    many assets; a changed file re-parses (the key is its text, not its mtime)."""
    text = f.read_text(encoding="utf-8", errors="replace")
    key = (str(f), text)
    if key not in _PARSED:
        try:
            _PARSED[key] = ast.parse(text, filename=str(f))
        except SyntaxError as exc:
            raise Unknown(f"{f.name}: unparseable ({exc})") from exc
    return _PARSED[key]


def _register_id(dec: ast.expr, consts: dict[str, str] | None = None) -> str | None:
    """@register('<asset_id>') as a real decorator — via the AST, so a docstring that MENTIONS
    `@register('bg_x')` is not mistaken for one. The regex version made that mistake twice.

    R43 (handverify L4/L5): `@register(ASSET_ID)` — a module-level string constant — is resolved
    through `consts` (the module's own top-level `NAME = '<str>'` assignments). An unresolvable name
    is not guessed: it returns None, exactly like any other decorator."""
    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "register" and dec.args:
        a = dec.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return a.value
        if isinstance(a, ast.Name) and consts and a.id in consts:
            return consts[a.id]
    return None


def _module_constants(tree: ast.AST) -> dict[str, str]:
    """R43: a module's top-level string constants (`ASSET_ID = "mi_bhara"`, annotated or not). A name
    assigned more than once, or to anything but one string literal, is dropped — never guessed."""
    seen: dict[str, list] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for tg in node.targets:
                if isinstance(tg, ast.Name):
                    seen.setdefault(tg.id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            seen.setdefault(node.target.id, []).append(node.value)
    return {k: v[0].value for k, v in seen.items()
            if len(v) == 1 and isinstance(v[0], ast.Constant) and isinstance(v[0].value, str)}


def _writer_path(name: str) -> Path:
    """R43: a writer-scan name is relative to writers/ (a module, or `<pkg>/<module>.py`) or, for a
    module reached through a writers/ shim's import, relative to the python sidecar root."""
    p = WRITERS / name
    return p if p.exists() else SIDECAR / name


def _first_party_imports(tree: ast.AST, here: Path) -> list[Path]:
    """R43: the first-party modules a writers/ module imports (`from services.ka_tulana.writer import
    KaTulanaWriter`, relative imports inside a package). The engine discovers writers by importing
    each writers/ module, and that import runs the imported modules' `@register` decorators — the ten
    L3 shims register this way. Only modules that exist under the sidecar are returned."""
    out: list[Path] = []
    for n in ast.walk(tree):
        mods = []
        if isinstance(n, ast.ImportFrom):
            base = SIDECAR if not n.level else here.parents[n.level - 1]
            mods.append((base, n.module or ""))
        elif isinstance(n, ast.Import):
            mods += [(SIDECAR, a.name) for a in n.names]
        for base, mod in mods:
            parts = [x for x in mod.split(".") if x]
            if not parts:
                continue
            for cand in (base.joinpath(*parts).with_suffix(".py"), base.joinpath(*parts, "__init__.py")):
                if cand.is_file() and cand not in out:
                    out.append(cand)
                    break
    return out


def _code_strings(node: ast.AST) -> list[str]:
    """String constants that are NOT docstrings — SQL, not prose."""
    docs = set()
    for n in ast.walk(node):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


def _writer_modules() -> list[tuple[str, Path]]:
    """R43: every module the engine's writer discovery executes, as (scan name, path):
    writers/*.py (the framework `__init__.py` excluded), each package directory's modules
    (`ph_rectification/__init__.py`; test directories and caches skipped), and — one level deep —
    the first-party modules those import (`services/ka_tulana/writer.py`). De-duplicated by path:
    a module imported by two shims runs its decorators once."""
    mods: list[tuple[str, Path]] = []
    seen: set[Path] = set()

    def add(name: str, path: Path) -> None:
        rp = path.resolve()
        if rp not in seen:
            seen.add(rp)
            mods.append((name, path))
    for f in _writer_files():
        add(f.name, f)
    for d in sorted(x for x in WRITERS.iterdir() if x.is_dir() and (x / "__init__.py").is_file()
                    and x.name not in ("tests", "__tests__", "__pycache__")):
        for f in sorted(d.glob("*.py")):
            add(f"{d.name}/{f.name}", f)
    for _name, f in list(mods):
        for g in _first_party_imports(_parse(f), f.parent):
            if WRITERS in g.parents and g.parent == WRITERS:
                continue                                    # a writers/ module: already listed
            if g.name == "__init__.py" and g.parent == WRITERS:
                continue                                    # the framework itself
            try:
                add(str(g.relative_to(SIDECAR)), g)
            except ValueError:
                continue
    return mods


def registered_ids(prefix: str) -> dict[str, list[str]]:
    """asset_id -> writer file(s), from real decorators on real classes (R43: literal ids, resolved
    module constants, package writers and shim-imported modules)."""
    out: dict[str, list[str]] = {}
    for name, f in _writer_modules():
        tree = _parse(f)
        consts = _module_constants(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    rid = _register_id(dec, consts)
                    if rid and rid.startswith(prefix) and name not in out.setdefault(rid, []):
                        out[rid].append(name)
    return out


def _writer_class(f: Path, asset_id: str) -> ast.ClassDef | None:
    tree = _parse(f)
    consts = _module_constants(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(_register_id(d, consts) == asset_id for d in node.decorator_list):
            return node
    return None


def contract_scan(asset_id: str, files: list[str]) -> tuple[str, list[str]]:
    """Frozen-contract conformance, per registered CLASS rather than per file.

    Calibrated after the first run's false positives: the ONLY hard failures are (a) no WriterBase
    subclass, (b) neither entry point, (c) a real `ctx.db_conn.commit()/close()` CALL, (d) a real SQL
    string that writes `asset_throughput`. Declaring both entry points is a note, not a failure —
    `WriterBase` may define `run()` as the template method that dispatches substeps, and calling that a
    violation would fail a conformant heavy writer."""
    notes: list[str] = []
    if not files:
        # R222 / N2: nothing was scanned — never N/A here. `_measure_contract` decides whether the
        # registry makes this genuinely not-applicable (has_writer=false) or an unmeasured writer.
        return NO_DET, ["no writer file recognised — nothing scanned"]
    found = False
    for name in files:
        f = _writer_path(name)
        cls = _writer_class(f, asset_id)
        if cls is None:
            continue
        found = True
        bases = {b.id for b in cls.bases if isinstance(b, ast.Name)} | \
                {b.attr for b in cls.bases if isinstance(b, ast.Attribute)}
        if "WriterBase" not in bases:
            notes.append(f"{name}: {cls.name} does not subclass WriterBase (bases: {sorted(bases) or 'none'})")
        methods = {m.name for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        heavy = {"plan_substeps", "run_substep"} <= methods
        if not heavy and "run" not in methods:
            notes.append(f"{name}: {cls.name} has neither run(ctx) nor plan_substeps+run_substep")
        if heavy and "run" in methods:
            notes.append(f"{name}: {cls.name} declares both entry points (note, not a violation)")
        for n in ast.walk(cls):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in ("commit", "close") and isinstance(n.func.value, ast.Attribute) \
                    and n.func.value.attr == "db_conn":
                notes.append(f"{name}: {cls.name} calls ctx.db_conn.{n.func.attr}() — the orchestrator owns the transaction")
        for sql in _code_strings(cls):
            if "asset_throughput" in sql and re.search(r"\b(INSERT|UPDATE|DELETE)\b", sql, re.I):
                notes.append(f"{name}: {cls.name} writes asset_throughput — the orchestrator is the sole build-state writer")
    if not found:
        return FAIL, [f"no class decorated @register('{asset_id}') found in {', '.join(files)}"]
    hard = [n for n in notes if "note, not a violation" not in n]
    return (PASS if not hard else FAIL), (notes or ["conformant"])


def _docstring_ids(tree: ast.AST) -> set[int]:
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    return docs


def _module_sequences(tree: ast.AST) -> dict[str, list[str]]:
    """C-KSHETRA: a module's top-level list/tuple literals of table names (`_OWNED_TABLES = (('kala_field',
    None), …)`, annotated or not) -> the first string of each element. Assigned twice -> dropped."""
    seen: dict[str, list] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for tg in node.targets:
                if isinstance(tg, ast.Name):
                    seen.setdefault(tg.id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            seen.setdefault(node.target.id, []).append(node.value)
    return {k: out for k, v in seen.items() if len(v) == 1 and (out := _literal_names(v[0]))}


def _literal_names(node: ast.AST) -> list[str]:
    """The table names a literal list/tuple enumerates: each string element, or each tuple element's first
    string. Anything else yields nothing (never guessed)."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    out = []
    for e in node.elts:
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            out.append(e.value)
        elif isinstance(e, ast.Tuple) and e.elts and isinstance(e.elts[0], ast.Constant) \
                and isinstance(e.elts[0].value, str):
            out.append(e.elts[0].value)
    return out


def _call_name(c: ast.AST) -> str | None:
    if isinstance(c, ast.Call):
        f = c.func
        return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
    return None


# ─────────── R20 (W2-3): follow writer delegation into the seeder ───────────

# R20: how many cross-module hops `idem_scan` follows from the registered writer class. Hop 1 is the
# module the writer calls into (a seeder `brahmagyan/l0_*.seed_*`, a shared helper
# `bodha_writers/_idempotency.replace_prior_*`, or the adapter target `ga_writers/ga_*_writer.build_*`);
# hop 2 is what THAT calls (the L1 adapters' own `ga_writers/_idempotency.replace_prior_*`). Beyond the
# limit nothing is guessed: a replacement found only deeper reads PARTIAL naming the chain.
IDEM_DELEGATION_HOPS = 2
# The orchestrator framework (@register, WriterBase, WriterResult, SubStep) is never a delegation target.
_FRAMEWORK_MODULES = ("pipeline/orchestrator/__init__.py", "pipeline/orchestrator/writers/__init__.py")
_WRITE_TEXT = re.compile(r"DELETE\s+FROM|TRUNCATE|INSERT\s+INTO|ON\s+CONFLICT|CREATE\s+OR\s+REPLACE", re.I)
_Q = r"(?:ONLY\s+)?(?:public\.)?\"?"
_SQL_DELETE = re.compile(r"DELETE\s+FROM\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*|\{\?\})?", re.I)
_SQL_TRUNCATE = re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?" + _Q + r"([A-Za-z_][A-Za-z_0-9]*|\{\?\})?", re.I)
_SQL_INSERT = re.compile(r"INSERT\s+INTO\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*|\{\?\})?", re.I)
_SQL_UPDATE = re.compile(r"\bUPDATE\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*)\s+SET\b", re.I)
_SQL_VIEW = re.compile(r"CREATE\s+OR\s+REPLACE\s+(?:MATERIALIZED\s+)?VIEW\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*)", re.I)
_ON_CONFLICT = re.compile(r"ON\s+CONFLICT", re.I)
# C-KSHETRA's output-existence probe, widened by R241 to the count form, now CAPTURING the probed table:
# a probe is an OUTPUT probe only when it reads one of the asset's own tables (or a table the scan cannot
# name) — mi_jivanaghatana's `count_chart_lel_events` counts its UPSTREAM life events and is no hold.
_PROBE_SQL = re.compile(r"SELECT\s+(?:EXISTS\s*\(\s*SELECT\s+1\s+FROM\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*|\{\?\})"
                        r"|(?:1|count\(\s*\*\s*\))\s+FROM\s+" + _Q + r"([A-Za-z_][A-Za-z_0-9]*|\{\?\})\s+WHERE\s+chart_id)", re.I)



def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(WRITERS))
    except ValueError:
        try:
            return str(p.relative_to(SIDECAR))
        except ValueError:
            return p.name


def _import_map(tree: ast.AST, here: Path) -> dict[str, tuple[Path, str | None]]:
    """R20: every first-party name a module imports — module-level or inside a function (the L1 adapters
    import their builder inside run()) — as local name -> (module file, imported attribute), or
    (module file, None) when the name IS a module (`from services.mi_bhara import db`). Only files that
    exist under the python sidecar; third-party imports resolve to nothing.

    `here` is the DIRECTORY of the importing module; a relative import resolves against the importing module's own package
    (`here` for level 1, its parent for level 2, ...). ONE resolver serves Idem.pattern and the Build.dag reads scan: the
    earlier base (`here.parents[level - 1]`) sat one directory too high, so package re-exports were silently skipped."""
    out: dict[str, tuple[Path, str | None]] = {}

    def mod_file(base: Path, parts: list[str]) -> Path | None:
        for cand in (base.joinpath(*parts).with_suffix(".py") if parts else None,
                     base.joinpath(*parts, "__init__.py")):
            if cand is not None and cand.is_file():
                return cand
        return None

    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            if not n.level:
                base = SIDECAR
            else:
                base = here if n.level == 1 else here.parents[n.level - 2]
            parts = [x for x in (n.module or "").split(".") if x]
            for a in n.names:
                sub = mod_file(base, parts + [a.name])
                if sub is not None:
                    out.setdefault(a.asname or a.name, (sub, None))
                    continue
                f = mod_file(base, parts)
                if f is not None:
                    out.setdefault(a.asname or a.name, (f, a.name))
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.asname:
                    f = mod_file(SIDECAR, a.name.split("."))
                    if f is not None:
                        out.setdefault(a.asname, (f, None))
    return {k: v for k, v in out.items() if not _is_framework(v[0])}


def _is_framework(p: Path) -> bool:
    """The orchestrator itself (asset_runner, runner, …) and the writer framework are never a writer's
    delegate: a `@l2_producer` wrapper importing the runner must not pull the engine into the scope."""
    r = _rel(p)
    return any(r.endswith(m) for m in _FRAMEWORK_MODULES) or r == "__init__.py" or \
        (r.startswith("pipeline/orchestrator/") and not r.startswith("pipeline/orchestrator/writers/"))


def _top_defs(tree: ast.AST) -> dict[str, ast.AST]:
    """A module's top-level functions, classes and assigned names (the SQL constants live there:
    `_INSERT_SQL = \"\"\"INSERT INTO …\"\"\"`), by name — looking through top-level if/try blocks."""
    out: dict[str, ast.AST] = {}

    def walk(body):
        for s in body:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.setdefault(s.name, s)
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name):
                        out.setdefault(t.id, s)
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None:
                out.setdefault(s.target.id, s)
            elif isinstance(s, (ast.If, ast.Try)):
                walk(s.body)
                walk(getattr(s, "orelse", []))
                for h in getattr(s, "handlers", []):
                    walk(h.body)
    walk(getattr(tree, "body", []))
    return out


def _closure(roots: list[ast.AST], defs: dict[str, ast.AST]) -> list[ast.AST]:
    """R20: the roots plus every top-level definition of the SAME module they reference by name,
    transitively — a module-level helper or SQL constant the writer class uses is part of the writer."""
    out, seen, todo = [], set(), list(roots)
    while todo:
        n = todo.pop()
        if id(n) in seen:
            continue
        seen.add(id(n))
        out.append(n)
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id in defs:
                todo.append(defs[x.id])
    return out


def _external_refs(nodes: list[ast.AST], imports: dict) -> list[tuple[Path, str]]:
    """The first-party definitions these nodes reference in OTHER modules: an imported name used
    (`seed_rules(...)`, a decorator `@l2_producer(...)`) or a module attribute (`db.insert_skill_row`)."""
    out: list[tuple[Path, str]] = []
    for n in nodes:
        for x in ast.walk(n):
            ref = None
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in imports \
                    and imports[x.value.id][1] is None:
                ref = (imports[x.value.id][0], x.attr)
            elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id in imports \
                    and imports[x.id][1] is not None:
                ref = imports[x.id]
            if ref and ref not in out:
                out.append(ref)
    return out


def _resolve_def(path: Path, name: str) -> tuple[Path, ast.AST, ast.AST] | None:
    """`name` defined in `path`, following package re-exports (`from .x import name`, at most 3)."""
    for _ in range(4):
        tree = _parse(path)
        d = _top_defs(tree).get(name)
        if d is not None and not isinstance(d, (ast.Assign, ast.AnnAssign)):
            return path, tree, d
        nxt = _import_map(tree, path.parent).get(name)
        if not nxt or nxt[1] is None:
            return None
        path, name = nxt
    return None


def _delegation_scope(asset_id: str, files: list[str], hops: int | None = None) -> tuple[list[dict], list[str]]:
    """R20: the code a rebuild of `asset_id` runs, as far as it can be read statically — the registered
    writer CLASS (not its whole module: bo_laksana.py registers two assets, and bo_laksana_rerank must
    not inherit bo_laksana's replacement) plus the same-module definitions it references, then each
    first-party definition that code references in another module, up to `hops` modules away.
    Returns (units, beyond): a unit is dict(rel, tree, nodes, hop, via); `beyond` names each chain the
    hop limit cut whose target module holds write SQL (a module with no DELETE/INSERT/ON CONFLICT text
    cannot hold the replacement, so cutting it loses nothing and is not reported)."""
    hops = IDEM_DELEGATION_HOPS if hops is None else hops
    units: list[dict] = []
    beyond: list[str] = []
    seen: set[tuple[str, str]] = set()
    queue: list[tuple[Path, ast.AST, list[ast.AST], int, str]] = []
    for name in files:
        p = _writer_path(name)
        tree = _parse(p)
        cls = _writer_class(p, asset_id)
        queue.append((p, tree, [cls] if cls is not None else [tree], 0, _rel(p)))
    while queue:
        p, tree, roots, hop, via = queue.pop(0)
        nodes = _closure(roots, _top_defs(tree))
        units.append(dict(rel=_rel(p), path=p, tree=tree, nodes=nodes, hop=hop, via=via))
        for tp, attr in _external_refs(nodes, _import_map(tree, p.parent)):
            r = _resolve_def(tp, attr)
            if r is None:
                continue
            dp, dtree, dnode = r
            key = (str(dp.resolve()), attr)
            if key in seen:
                continue
            seen.add(key)
            chain = f"{via} → {_rel(dp)}:{attr}"
            if hop + 1 > hops:
                if _WRITE_TEXT.search(dp.read_text(encoding="utf-8", errors="replace")):
                    beyond.append(chain)
                continue
            queue.append((dp, dtree, [dnode], hop + 1, chain))
    return units, beyond


_TREE_INFO: dict[int, tuple] = {}


def _sql_texts(unit: dict):
    """(text, line, is_dynamic) for every SQL-bearing string in a unit's nodes — docstrings excluded;
    an f-string's `{X}` resolved to a module constant or the enclosing `for` sequence (one text per
    resolved name), else kept as the marker `{?}`; string concatenation (`a + b`) read as one text."""
    tree = unit["tree"]
    if id(tree) not in _TREE_INFO:                     # once per parsed module, not once per node
        _TREE_INFO[id(tree)] = (tree, _docstring_ids(tree), _module_constants(tree), _module_sequences(tree))
    _, docs, consts, seqs = _TREE_INFO[id(tree)]
    out: list[tuple[str, int]] = []
    done: set[int] = set()

    def parts_of(n, loops) -> list[str] | None:
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return [n.value]
        if isinstance(n, ast.JoinedStr):
            texts = [""]
            for v in n.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    texts = [t + v.value for t in texts]
                elif isinstance(v, ast.FormattedValue):
                    e = v.value
                    names = (loops.get(e.id) or ([consts[e.id]] if e.id in consts else None)) \
                        if isinstance(e, ast.Name) else None
                    texts = [t + x for t in texts for x in (names or ["{?}"])]
            return texts
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            a, b = parts_of(n.left, loops), parts_of(n.right, loops)
            if a is not None and b is not None:
                return [x + y for x in a for y in b]
        return None

    def visit(n, loops):
        if isinstance(n, (ast.For, ast.AsyncFor)):
            it = n.iter
            names = _literal_names(it) or (seqs.get(it.id, []) if isinstance(it, ast.Name) else [])
            tg = n.target.elts[0] if isinstance(n.target, ast.Tuple) and n.target.elts else n.target
            if names and isinstance(tg, ast.Name):
                loops = dict(loops, **{tg.id: names})
        if id(n) not in done and id(n) not in docs and isinstance(n, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            texts = parts_of(n, loops)
            if texts is not None:
                for x in ast.walk(n):
                    done.add(id(x))
                out.extend((t, getattr(n, "lineno", 0)) for t in texts)
                return
        for c in ast.iter_child_nodes(n):
            visit(c, loops)
    for node in unit["nodes"]:
        visit(node, {})
    return out


def _write_facts(units: list[dict]) -> dict[str, list[tuple[str, str, int, str]]]:
    """R20: what the resolved scope WRITES, by statement kind: `replace` (DELETE / TRUNCATE / CREATE OR
    REPLACE VIEW), `upsert` (INSERT … ON CONFLICT), `insert` (plain INSERT), `update`, each as
    (table, file, line, delegation chain — '' in the writer itself); and `dynamic` — a DELETE/TRUNCATE/INSERT whose table the scan cannot name. An
    INSERT and an ON CONFLICT split across two strings of ONE function count as an upsert, never as a
    plain insert (the split must not manufacture an "accretes" FAIL)."""
    facts = {k: [] for k in ("replace", "upsert", "insert", "update", "dynamic")}
    for u in units:
        for node in u["nodes"]:
            texts = _sql_texts(dict(u, nodes=[node]))
            fns = sorted(((f.lineno, f.end_lineno) for f in ast.walk(node)
                          if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))), key=lambda r: r[1] - r[0])

            def owner(ln):
                return next((r for r in fns if r[0] <= ln <= r[1]), None)
            orphan = {owner(ln) for t, ln in texts if _ON_CONFLICT.search(t) and not _SQL_INSERT.search(t)}
            for t, ln in texts:
                where = (u["rel"], ln, u["via"] if u["hop"] else "")
                for rx in (_SQL_DELETE, _SQL_TRUNCATE, _SQL_VIEW):
                    for m in rx.finditer(t):
                        tb = m.group(1)
                        facts["dynamic" if not tb or tb == "{?}" else "replace"].append(
                            ("?" if not tb or tb == "{?}" else tb.lower(), *where))
                for m in _SQL_INSERT.finditer(t):
                    tb = m.group(1)
                    if not tb or tb == "{?}":
                        facts["dynamic"].append(("?", *where))
                    else:
                        k = "upsert" if (_ON_CONFLICT.search(t) or owner(ln) in orphan) else "insert"
                        facts[k].append((tb.lower(), *where))
                for m in _SQL_UPDATE.finditer(t):
                    facts["update"].append((m.group(1).lower(), *where))
    return {k: sorted(set(v), key=lambda x: (x[1], x[2], x[0])) for k, v in facts.items()}


_FETCH_CALLS = ("fetchone", "fetchall", "fetchval", "scalar")
# R241: a probe whose predicate pins the CURRENT build (`… AND build_id_uuid = %s`) asks whether this build
# already wrote the rows — a substep-resume check (ga_vargas `_check_already_written`); a rebuild carries a
# new build id and is never held by it. Only a probe of the chart's output as such is a hold.
_BUILD_SCOPED = re.compile(r"\bbuild_id\w*\s*=", re.I)


def _probe_polarity(t: ast.AST, probes: set[str], probed: dict[str, str]) -> tuple[str, str] | None:
    """R20/R241: is an `if` test the POPULATED or the EMPTY reading of an output-existence probe?
    Returns ('populated'|'empty', probe name) or None. Recognised: the probe call itself (also inside a
    walrus or `bool(...)`), a name bound to its result, `x is not None` / `x is None`, `x > 0`,
    `x >= 1`, `x != 0` / `x == 0`, `0 < x`, and `not <any of these>` (polarity inverted)."""
    if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not):
        r = _probe_polarity(t.operand, probes, probed)
        return (("empty" if r[0] == "populated" else "populated"), r[1]) if r else None
    if isinstance(t, (ast.NamedExpr, ast.Subscript, ast.Await)):         # `(n := probe())`, `row[0]`, `await p()`
        return _probe_polarity(t.value, probes, probed)
    if isinstance(t, ast.Call) and _call_name(t) == "bool" and t.args:
        return _probe_polarity(t.args[0], probes, probed)
    if isinstance(t, ast.Call) and _call_name(t) in probes:
        return "populated", _call_name(t)
    if isinstance(t, ast.Name) and t.id in probed:
        return "populated", probed[t.id]
    if isinstance(t, ast.Compare) and len(t.ops) == 1:
        left, op, right = t.left, t.ops[0], t.comparators[0]
        if isinstance(left, ast.Constant) and isinstance(right, ast.Name):          # 0 < x  ->  x > 0
            left, right = right, left
            op = {ast.Lt: ast.Gt(), ast.LtE: ast.GtE(), ast.Gt: ast.Lt(), ast.GtE: ast.LtE()}.get(type(op), op)
        base = _probe_polarity(left, probes, probed)
        if base is None or not isinstance(right, ast.Constant):
            return None
        v, name = right.value, base[1]
        if v is None and isinstance(op, ast.IsNot):
            return "populated", name
        if v is None and isinstance(op, ast.Is):
            return "empty", name
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if (isinstance(op, ast.Gt) and v == 0) or (isinstance(op, ast.GtE) and v == 1) \
                    or (isinstance(op, ast.NotEq) and v == 0):
                return "populated", name
            if isinstance(op, ast.Eq) and v == 0:
                return "empty", name
    return None


def _refusal_guard(units: list[dict], tset=frozenset()) -> tuple[str, int, str, str] | None:
    """C-KSHETRA, generalised by R20/R241 to the whole resolved scope: a rebuild that is HELD when the
    chart's output already exists is not an idempotent replacement, whatever DELETE sits behind the hold.
    Across every function the writer's rebuild reaches (the writer class and its delegates — not merely
    one file), find an `if` on the POPULATED reading of an output-existence probe (a function or block
    whose SQL is `SELECT EXISTS (SELECT 1 FROM …`, `SELECT 1 FROM <t> WHERE chart_id …` or
    `SELECT count(*) FROM <t> WHERE chart_id …`) READING ONE OF THE ASSET'S OWN TABLES (`tset`, or a
    table the scan cannot name) whose populated branch RAISES, RETURNS, CONTINUEs or BREAKs with a delete
    reachable only past it (after the `if`, or in its empty branch) — or whose only delete sits in the
    empty branch (a skip with no raise). A probe of an UPSTREAM table is no hold (mi_jivanaghatana raises
    when its input life_events exist but it built nothing — the opposite of a refusal), nor is a probe
    pinned to the current build (`_BUILD_SCOPED`, a resume check). Returns (file,
    line, 'raise X' | 'return' | 'continue' | 'break' | 'the delete runs only in the output-empty branch',
    probe) or None."""
    funcs, seen = [], set()
    for u in units:
        for n in u["nodes"]:
            for f in ast.walk(n):
                if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and id(f) not in seen:
                    seen.add(id(f))
                    funcs.append((u, f))
    def probes_own(u, f) -> bool:
        for t, _ in _sql_texts(dict(u, nodes=[f])):
            for m in _PROBE_SQL.finditer(t):
                tb = (m.group(1) or m.group(2) or "").lower()
                if _BUILD_SCOPED.search(t[m.end():]):
                    continue            # "did THIS build already write it" — a resume check, not a hold
                if tb in tset or tb == "{?}":
                    return True
        return False
    own_probe = {id(f): probes_own(u, f) for u, f in funcs}
    probes = {f.name for _, f in funcs if own_probe[id(f)]}
    deleters = {f.name for _, f in funcs if any(_SQL_DELETE.search(s) or _SQL_TRUNCATE.search(s)
                                                 for s in _code_strings(f))}
    grew = True
    while grew:                                            # a function that calls a deleter deletes
        before = len(deleters)
        deleters |= {f.name for _, f in funcs if any(_call_name(c) in deleters for c in ast.walk(f))}
        grew = len(deleters) > before
    def deletes(nodes) -> bool:
        return any(_call_name(c) in deleters for c in nodes) or \
            any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                and (_SQL_DELETE.search(c.value) or _SQL_TRUNCATE.search(c.value)) for c in nodes)

    def probed_names(f) -> dict[str, str]:
        inline, probed = own_probe[id(f)], {}
        for a in ast.walk(f):
            if isinstance(a, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                val = a.value
                while isinstance(val, (ast.Subscript, ast.Await)) or (
                        isinstance(val, ast.Call) and _call_name(val) in ("bool", "int", "len") and val.args):
                    val = val.value if not isinstance(val, ast.Call) else val.args[0]   # `bool(probe())`
                tgts = a.targets if isinstance(a, ast.Assign) else [a.target]
                if _call_name(val) in probes or (inline and _call_name(val) in _FETCH_CALLS):
                    src = _call_name(val) if _call_name(val) in probes else f"{f.name} (inline)"
                    probed.update({t.id: src for t in tgts if isinstance(t, ast.Name)})
        return probed

    def populated_ifs(f):
        probed = probed_names(f)
        for node in ast.walk(f):
            if isinstance(node, ast.If):
                pol = _probe_polarity(node.test, probes, probed)
                if pol is not None:
                    held, path = (node.body, node.orelse) if pol[0] == "populated" else (node.orelse, node.body)
                    yield node, pol, held, path

    def raise_name(stop) -> str:
        exc = stop.exc
        return "raise " + (_call_name(exc) or (exc.id if isinstance(exc, ast.Name) else "an exception"))

    # R241 (follow-up): a GUARD HELPER — a function that raises on the populated reading and deletes nothing
    # itself (`_assert_empty`) — holds the rebuild for any caller that deletes after calling it (a call
    # inside a `try` is not counted: the caller may catch it). Resolved to a fixpoint over the scope.
    raisers: dict[str, tuple[str, str]] = {}
    for _u, f in funcs:
        for _node, pol, held, _path in populated_ifs(f):
            stop = next((x for x in held if isinstance(x, ast.Raise)), None)
            if stop is not None and f.name not in raisers:
                raisers[f.name] = (raise_name(stop), pol[1])

    def untried_calls(f):
        tried = {id(c) for t in ast.walk(f) if isinstance(t, ast.Try) and t.handlers
                 for s in t.body for c in ast.walk(s)}
        return [c for c in ast.walk(f) if isinstance(c, ast.Call) and id(c) not in tried]
    grew = True
    while grew:
        grew = False
        for _u, f in funcs:
            if f.name in raisers:
                continue
            hit = next((c for c in untried_calls(f) if _call_name(c) in raisers), None)
            if hit is not None:
                raisers[f.name] = raisers[_call_name(hit)]
                grew = True

    for u, f in funcs:
        for node, pol, held, path in populated_ifs(f):
            stop = next((s for s in held if isinstance(s, (ast.Raise, ast.Return, ast.Continue, ast.Break))), None)
            after = [c for c in ast.walk(f) if getattr(c, "lineno", 0) > node.end_lineno]
            on_path = [c for s in path for c in ast.walk(s)]
            if stop is not None and deletes(on_path + after):
                what = raise_name(stop) if isinstance(stop, ast.Raise) else type(stop).__name__.lower()
                return u["rel"], stop.lineno, what, pol[1]          # return / continue / break / raise X
            # R241: a hold that neither raises nor returns — the delete sits ONLY in the empty branch, and
            # nothing in the populated branch or after the `if` deletes: a populated chart is skipped.
            if stop is None and deletes(on_path) and not deletes([c for s in held for c in ast.walk(s)] + after):
                return u["rel"], node.lineno, "the delete runs only in the output-empty branch", pol[1]
        for c in untried_calls(f):
            name = _call_name(c)
            if name in raisers and name != f.name and \
                    deletes([x for x in ast.walk(f) if getattr(x, "lineno", 0) > getattr(c, "end_lineno", c.lineno)]):
                what, probe = raisers[name]
                return u["rel"], c.lineno, f"{what} in the guard helper {name}", probe
    return None


_UO_SCOPE_COLS = ("chart_id", "ayanamsha_id", "build_id", "asset_id", "run_id")
_UO_SET = re.compile(r"\bSET\b(.*?)(?=\bWHERE\b|\bFROM\b|\bRETURNING\b|\Z)", re.I | re.S)
_UO_WHERE = re.compile(r"\bWHERE\b(.*?)(?=\bRETURNING\b|\Z)", re.I | re.S)
_UO_ARRAY_ACC = re.compile(r"\b(?:array_(?:append|cat|prepend)|concat|jsonb_insert)\s*\(", re.I)
_UO_KEYED = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(?:%s|%\(\w+\)s|\$\d+|ANY\s*\()", re.I)


_UO_JSON_DELETE = r"(?:''|ARRAY\s*\[[^\]]*\]|(?:%s|%\(\w+\)s)\s*::\s*text(?:\[\])?)"


def _split_top_br(s: str) -> list:
    """_split_top that also keeps `[...]` (array constructors) whole."""
    parts, depth, cur = [], 0, []
    for ch in s:
        depth += ch in "(["
        depth -= ch in ")]"
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    return parts + ["".join(cur)]


def _uo_assignments(set_text: str):
    """(column, expression) pairs of a SET clause; a tuple form `(a, b) = (x, y)` / `= ROW(x, y)` is paired by
    position (an unpairable right side is attributed whole to each column)."""
    for a in _split_top_br(set_text):
        if "=" not in a:
            continue
        lhs, rhs = (x.strip() for x in a.split("=", 1))
        if lhs.startswith("(") and lhs.endswith(")"):
            cols = [c.strip().strip('"') for c in lhs[1:-1].split(",")]
            r = rhs[3:].strip() if rhs.upper().startswith("ROW") else rhs
            exprs = _split_top(r[1:-1]) if r.startswith("(") and r.endswith(")") else None
            if exprs and len(exprs) == len(cols):
                yield from zip(cols, (x.strip() for x in exprs))
            else:
                yield from ((c, rhs) for c in cols)
        else:
            yield lhs.strip('"'), rhs


def _uo_shapes(w) -> list:
    """The row-set predicate shapes of an UPDATE's WHERE text (None = no WHERE)."""
    found = []
    if w is None:
        return ["no-predicate"]
    if re.search(r"\bIS\s+DISTINCT\s+FROM\b", w, re.I):
        found.append("guarded")
    if re.search(r"\bIS\s+(?:NOT\s+)?NULL\b", w, re.I):
        found.append("state-conditional")
    lhs = [c.lower() for c in _UO_KEYED.findall(w)]
    if any(c not in _UO_SCOPE_COLS for c in lhs):
        found.append("keyed")
    if any(c in _UO_SCOPE_COLS for c in lhs) or re.search(r"\b(?:" + "|".join(_UO_SCOPE_COLS) + r")\b", w, re.I):
        found.append("scope")
    return found or ["other-predicate"]


def _update_only_reading(units, tset) -> dict:
    """Idem.pattern's update-only sub-reading (N-22 ruling 6; SS: Idem stays ONE gate, update-only is not N/A): each
    own-table UPDATE is read for (a) an ACCUMULATING assignment (`SET c = c + x`, `c * x`, array_append/cat/prepend
    of c: a second rebuild changes the row again; named update-only:accumulating-assignment) and (b) its row-set
    predicate shape: keyed, scope (chart/ayanamsha/build/asset), state-conditional (IS [NOT] NULL), guarded (IS DISTINCT
    FROM), none, other. Whether a rebuild re-derives EVERY row is not provable statically (PASS needs the E5.5
    semantic-fingerprint comparison on the E5.6 rehearsal database), so the reading never PASSes."""
    acc, concat, shapes, recs = [], [], {}, []
    for u in units:
        for node in u["nodes"]:
            for text, ln in _sql_texts(dict(u, nodes=[node])):
                m = _SQL_UPDATE.search(text)
                if not m or m.group(1).lower() not in tset:
                    continue
                flat = re.sub(r"'(?:[^']|'')*'", "''", re.sub(r"--[^\n]*", "", text))
                where = _UO_WHERE.search(flat)
                cite_ = f"{m.group(1).lower()} ({u['rel']}:{ln}{' via ' + u['via'] if u['hop'] else ''})"
                st = _UO_SET.search(flat)
                fns = sorted(((f.lineno, f.end_lineno) for f in ast.walk(node)
                              if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))), key=lambda r: r[1] - r[0])
                fn = next((r for r in fns if r[0] <= ln <= r[1]), None)
                shapes_here = _uo_shapes(where.group(1) if where else None)
                ifs = [(i.lineno, i.end_lineno) for i in ast.walk(node) if isinstance(i, ast.If)]
                # a reset excuses an accumulation only when UNCONDITIONAL (not inside an `if`) and chart-wide (no keyed,
                # state-conditional, guarded or other predicate)
                excuses = (not any(a0 <= ln <= b0 for a0, b0 in ifs)
                           and not set(shapes_here) & {"keyed", "state-conditional", "guarded", "other-predicate"})
                for col, expr in (_uo_assignments(st.group(1)) if st else []):
                    if not re.fullmatch(r"[A-Za-z_]\w*", col):
                        continue
                    if not re.search(rf"\b{re.escape(col)}\b", expr):
                        recs.append(dict(kind="reset", table=m.group(1).lower(), col=col, line=ln, fn=fn, u=u["rel"], ok=excuses))
                    elif re.fullmatch(rf"\s*{re.escape(col)}\s*-\s*{_UO_JSON_DELETE}\s*", expr, re.I):
                        continue                                # jsonb key delete: idempotent
                    elif re.search(r"[+\-*/]", re.sub(r"%\(\w+\)s|::\w+", "", expr)) or _UO_ARRAY_ACC.search(expr):
                        recs.append(dict(kind="acc", table=m.group(1).lower(), col=col, line=ln, fn=fn, u=u["rel"],
                                         text=f"{col} = {expr[:60]} in {cite_}"))
                    elif "||" in expr:
                        concat.append(f"{col} in {cite_}")
                found = shapes_here
                for f in found:
                    shapes.setdefault(f, []).append(cite_)
    # an accumulation is excused only by a reset of the SAME column of the SAME table earlier in the SAME function
    for r in recs:
        if r["kind"] == "acc" and not any(x["kind"] == "reset" and x["ok"] and x["table"] == r["table"] and x["col"] == r["col"]
                                          and x["u"] == r["u"] and r["fn"] is not None and x["fn"] == r["fn"]
                                          and x["line"] < r["line"] for x in recs):
            acc.append(r["text"])
    return dict(accumulating=acc, concat=concat, shapes=shapes)


def _update_only_text(rd: dict) -> str:
    slugs = [f"update-only:{k}-row-set-unproven" for k in ("keyed", "scope", "state-conditional", "guarded", "no-predicate",
                                                          "other-predicate") if k in rd["shapes"]]
    if rd["concat"]:
        slugs.append("update-only:self-referencing-concat-type-unread (" + "; ".join(rd["concat"]) + ")")
    return (" ".join(slugs) + "; no row is added, but whether a rebuild re-derives every row is not proven statically: "
            "PASS needs the E5.5 semantic-fingerprint comparison across a rebuild on the E5.6 rehearsal database, "
            "which this scan does not run")


def idem_scan(asset_id: str, files: list[str], convention: str, targets=()) -> tuple[str, list[str]]:
    """§N.3, over real SQL strings (docstrings excluded), measured on the code a rebuild RUNS.

    C-KSHETRA (W2-2 gate review §4.1): the PASS is a claim that a REBUILD REPLACES the asset's own rows —
    (a) a counted DELETE must NAME one of the asset's own tables (`targets`: target_table ∪ count_sql
    tables), and (b) a rebuild held when the output is populated reads FAIL with the hold's location.

    R20 (W2-3): the scan now follows the writer's DELEGATION (`_delegation_scope`): from the registered
    class — not its whole module — through the same-module helpers and SQL constants it uses, into the
    seeder / shared helper / adapter target it calls, up to IDEM_DELEGATION_HOPS modules away. The same
    two rules apply to everything reached. Upsert layers (L0) PASS on an `INSERT … ON CONFLICT` into the
    asset's OWN table (no longer on `ON CONFLICT` text anywhere), or on a delete-then-insert of it — a
    full replacement, no accretion. A FAIL needs a measured defect on a fully-read scope: a hold, an
    own-table INSERT with no replacement (accretes), or an own-table upsert where §N.3 requires
    delete-then-insert. Everything else is PARTIAL with the reason named — a chain the hop limit cut, a
    table the scan cannot name, a registry/writer table mismatch (R240), in-place UPDATEs only, or no
    own-table write at all — never "likely delegates"."""
    if not files:
        return NO_DET, ["no writer file recognised — nothing scanned"]   # R222 / N2, as contract_scan
    units, beyond = _delegation_scope(asset_id, files)
    facts = _write_facts(units)
    tset = {t.lower() for t in targets if t}

    def cite(rows) -> str:
        return ", ".join(dict.fromkeys(f"{t} ({rel}:{ln}{f' via {via}' if via else ''})" for t, rel, ln, via in rows))

    guard = _refusal_guard(units, tset)          # R241: across the whole resolved scope, not one file
    if guard:
        rel, ln, what, probe = guard
        u = next((x for x in units if x["rel"] == rel), None)
        hop = f", reached via {u['via']}" if u and u["hop"] else ""
        return FAIL, [f"rebuild refused when target is populated: {rel}:{ln} ({what} after the output-existence "
                      f"probe {probe}{hop}) — the delete-then-insert path runs only on an output-empty chart, so a "
                      "rebuild of a populated chart does not replace (§N.3 'rebuild replaces' not met)"]
    own = {k: [x for x in facts[k] if x[0] in tset] for k in ("replace", "upsert", "insert", "update")}
    unresolved = bool(beyond or facts["dynamic"])
    # R20 (follow-up): the PASS is per TABLE, not per asset — a multi-table writer that replaces one of its
    # tables and plain-INSERTs into another it never replaces still accretes the second on every rebuild.
    covered = {x[0] for x in own["replace"] + own["upsert"]}
    unreplaced = [x for x in own["insert"] if x[0] not in covered]
    if unreplaced and covered:
        what = (f"the rebuild replaces {sorted(covered)} but plain-INSERTs into {sorted({x[0] for x in unreplaced})} "
                f"with no delete or upsert of it: {cite(unreplaced)}")
        if not unresolved:
            return FAIL, [f"{what} — that table accretes (or collides) on every rebuild"]
        return PARTIAL, [f"{what}; the scope is not fully read (a cut delegation chain or an unnamed table may "
                         f"hold its replacement) [resolved scope: {', '.join(dict.fromkeys(u['rel'] for u in units))}]"]
    if convention == "upsert":
        if own["upsert"]:
            return PASS, [f"INSERT … ON CONFLICT into the asset's own table(s) (upsert): {cite(own['upsert'])}"]
        if own["replace"]:
            return PASS, [f"the asset's own table(s) replaced by delete-then-insert: {cite(own['replace'])} — a full "
                          "replacement, not the L0 upsert convention, and no accretion"]
    elif own["replace"]:
        return PASS, [f"DELETE FROM the asset's own table(s) (delete-then-insert): {cite(own['replace'])}"]
    if not unresolved:
        if convention != "upsert" and own["upsert"]:
            return FAIL, [f"upsert into the asset's own table(s) with no delete of them anywhere in the resolved scope: "
                          f"{cite(own['upsert'])} — §N.3 requires delete-then-insert for this layer; rows a rebuild no "
                          "longer produces survive it"]
        if own["insert"] and not own["upsert"]:
            return FAIL, [f"plain INSERT into the asset's own table(s) with no delete or upsert of them anywhere in the "
                          f"resolved scope: {cite(own['insert'])} — a rebuild accretes (or collides) rather than replaces"]
    reasons = []
    other = sorted({x[0] for x in facts["replace"] + facts["upsert"]} - tset)
    mismatch = sorted({(o, t) for t in other for o in tset if t.startswith(o + "_") or o.startswith(t + "_")})
    if mismatch:
        reasons.append("registry/writer table mismatch (R240, a registry-data finding — not closable by the "
                       "detector): " + "; ".join(f"the registry declares {o}, the writer replaces {t}" for o, t in mismatch))
    if beyond:
        reasons.append(f"delegation deeper than {IDEM_DELEGATION_HOPS} hop(s), not followed: {'; '.join(beyond)}")
    if facts["dynamic"]:
        reasons.append("a DELETE/INSERT whose table the scan cannot name: "
                       + ", ".join(f"{x[1]}:{x[2]}" for x in facts["dynamic"]))
    if own["upsert"]:
        reasons.append(f"upsert into the asset's own table(s) and no delete of them found: {cite(own['upsert'])}")
    if own["insert"]:
        reasons.append(f"plain INSERT into the asset's own table(s) and no replacement found: {cite(own['insert'])}")
    if own["update"] and not (own["upsert"] or own["insert"]):
        rd = _update_only_reading(units, tset)
        if rd["accumulating"]:
            what = "update-only:accumulating-assignment: " + "; ".join(rd["accumulating"])
            if not unresolved:
                return FAIL, [f"the asset's own table(s) are only UPDATEd in place: {cite(own['update'])} — {what} — a second "
                              "rebuild changes the rows again (not idempotent)"]
            reasons.append(f"the asset's own table(s) are only UPDATEd in place: {cite(own['update'])} — {what} (the scope "
                           "is not fully read, so this is PARTIAL, not FAIL)")
        else:
            reasons.append(f"the asset's own table(s) are only UPDATEd in place: {cite(own['update'])} — "
                           f"{_update_only_text(rd)}")
    if other and not mismatch:
        reasons.append(f"it replaces only other tables: {', '.join(other)}")
    if not any(own.values()):
        reasons.append(f"no write to the asset's own table(s) {sorted(tset) or '(none declared)'} anywhere in the "
                       "resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a "
                       "write's absence")
    scope = ", ".join(dict.fromkeys(u["rel"] for u in units))
    return PARTIAL, ["; ".join(reasons) + f" [resolved scope: {scope}]"]


def _ts_code(src: str, blank_strings: bool = False) -> str:
    """R51: TypeScript source with its comments removed (`// …` and `/* … */`, JSDoc included), string
    and template literals respected — a `//` inside `'http://…'` or a backticked SQL string is code,
    not a comment. Newlines inside removed comments are kept so positions stay line-true. With
    `blank_strings`, literal CONTENTS are blanked too (the quotes stay). Limit, disclosed: a regex
    literal containing a quote or `//` is not recognised as a regex (no such literal is needed by the
    capability modules' table references or declarations)."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c, nx = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and nx == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * src.count("\n", i, j) or " ")
            i = j
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            body = src[i + 1:min(j, n)]
            out.append(c + (re.sub(r"[^\n]", " ", body) if blank_strings else body) + (c if j < n else ""))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


# `density_contract: <object or identifier>`: a key whose value is `undefined` / `null` / `false` / `true` declares
# nothing (R232 carried: a declaration needs a real value, not just the key).
_DENSITY_DECL = re.compile(r"\bdensity_contract\s*\??\s*:\s*(?!(?:undefined|null|false|true)\b)(?=[{A-Za-z_$(\[])")

# E6.1 (d) / N-22 ruling principle 4: the Dens scanner. A tier column is STRUCTURAL vocabulary: `tier`, any `<x>_tier`
# (signature_tier, efficacy_tier, ...) and the L1 verification tier `verification_pass_status` — a column NAME, never a
# value check. `confidence*` columns are deliberately not in it (open question to the lead, DESIGN_DENS.md Q1).
DENS_TIER_COLUMN = re.compile(r"^(?:tier|\w+_tier|verification_pass_status)$", re.I)
TIER_YES, TIER_NO, TIER_UNKNOWN = "tier", "no-tier", "unknown"


def _ts_mask(src: str, blank_strings: bool = False) -> str:
    """`_ts_code`'s comment discipline with POSITIONS KEPT: same length as `src`; every comment character becomes a
    space (newlines stay); with `blank_strings`, literal contents too. Offsets found in the mask are offsets in `src`,
    which `_ts_code` (it deletes comment text) cannot give — needed to say WHICH top-level declaration a token, a
    `density_contract:` and a SELECT literal sit in."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c, nx = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out[i:j] = " " * (j - i)
            i = j
        elif c == "/" and nx == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out[i:j] = [ch if ch == "\n" else " " for ch in src[i:j]]
            i = j
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            if blank_strings:
                out[i + 1:min(j, n)] = [ch if ch == "\n" else " " for ch in src[i + 1:min(j, n)]]
            i = j + 1
        else:
            i += 1
    return "".join(out)[:n]


def _ts_literal_spans(src: str) -> list[tuple[int, str]]:
    """`_ts_literals` with each literal's start offset in `src` (comments skipped, strings respected)."""
    out, i, n = [], 0, len(src)
    while i < n:
        c, nx = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and nx == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append((i + 1, src[i + 1:min(j, n)]))
            i = j + 1
        else:
            i += 1
    return out


def _ts_desynced(src: str) -> bool:
    """Did the string/comment scanner lose sync with the file? True when a quoted string is never closed, or a `'` / `"`
    string spans a raw newline (neither is legal TypeScript; both are what a stray quote — an apostrophe in JSX text
    (`<p>don't</p>`), a quote inside a regex literal — does to every literal after it). Everything `_ts_mask`,
    `_ts_literal_spans` and `_ts_decl_starts` report for such a file is unreliable, so the outside probe never reads
    "no served select" from it. Limit, disclosed: two stray quotes re-sync by accident and are not detected (a `.tsx`
    file is never trusted for that reason — it is always read textually)."""
    i, n = 0, len(src)
    while i < n:
        c, nx = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and nx == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                if c != "`" and src[j] == "\n":
                    return True
                j += 2 if src[j] == "\\" else 1
            if j >= n:
                return True
            i = j + 1
        else:
            i += 1
    return False


_DYN_FROM = re.compile(r"\b(?:FROM|JOIN)\s+(?:ONLY\s+)?(?:\"?[A-Za-z_]\w*\"?\.)?\"?\$\{|\b(?:FROM|JOIN)\s+(?:ONLY\s+)?(?:[\w\"]+\.)?%(?:\d+\$)?[IsL]", re.I)
# a literal that ENDS in `FROM` / `JOIN` / `FROM <partial name>` and has its table name joined on in code
_DYN_FROM_TAIL = re.compile(r"\b(?:FROM|JOIN)\b(?:\s+(?:ONLY\s+)?[\w.\"]*)?\s*$", re.I)
_DYN_JOINED = re.compile(r"(?:\s|/\*.*?\*/|//[^\n]*\n)*(?:\+|,|\.concat\s*\()", re.S)


def _dynamic_from(txt: str, spans: list[tuple[int, str]]) -> bool:
    """Does any literal name its table at run time: `FROM ${T}` (also `"${T}"`, `"public"."${T}"`, `public.${T}`, JOIN,
    ONLY), a `format(… FROM %I …)` placeholder, or a literal ending in `FROM`/`JOIN`/`FROM t_` that has a name joined
    on with `+`, `.concat(` or an array `,` (a comment between is skipped)?"""
    for pos, c in spans:
        if _DYN_FROM.search(c):
            return True
        if _DYN_FROM_TAIL.search(c) and _DYN_JOINED.match(txt[pos + len(c) + 1:pos + len(c) + 200]):
            return True
    return False


_DECL_LINE = re.compile(r"^(?:import\b|export\b|(?:async\s+)?function\b|(?:const|let|var|class|interface|type|enum)\b)", re.M)


def _ts_decl_starts(mask: str) -> list[int]:
    """Offsets where a TOP-LEVEL declaration begins (the unit this scan calls a capability): the point at which a
    bracket nest returns to depth 0, a `;` at depth 0, and a line that starts a declaration keyword at depth 0.
    `mask` has comments and string contents blanked, so a brace in either never counts. Limit, disclosed: a regex
    literal holding a bracket is not recognised."""
    starts, depth = {0}, 0
    at_decl = {m.start() for m in _DECL_LINE.finditer(mask)}
    for i, ch in enumerate(mask):
        if depth == 0 and i in at_decl:
            starts.add(i)
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth = max(depth - 1, 0)
            if depth == 0:
                starts.add(i + 1)
        elif ch == ";" and depth == 0:
            starts.add(i + 1)
    return sorted(starts)


_DENS_RAW: dict[tuple, frozenset] = {}
_DENS_FACTS: dict[tuple, dict] = {}


def _dens_words(f: Path) -> tuple[tuple, frozenset]:
    """Every `\\w+` word of the file's RAW text (comments included) — a cheap pre-filter: a token that is not a word
    here is in no comment and no code, so the expensive parse below never runs for the file."""
    st = f.stat()
    key = (str(f), st.st_mtime_ns, st.st_size)
    if key not in _DENS_RAW:
        _DENS_RAW[key] = frozenset(re.findall(r"\w+", f.read_text(encoding="utf-8", errors="replace")))
    return key, _DENS_RAW[key]


def _enclosing_object(blank: str, pos: int) -> tuple[int, int]:
    """`(start, end)` of the innermost `{ ... }` around `pos` in the comment- and string-blanked text — the object
    literal a `density_contract:` key sits directly in: the capability ENTRY it declares the contract for. No enclosing
    brace: the whole text."""
    depth, i = 0, pos - 1
    while i >= 0:
        ch = blank[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            if depth == 0:
                break
            depth -= 1
        i -= 1
    else:
        return 0, len(blank)
    depth = 0
    for j in range(i, len(blank)):
        if blank[j] == "{":
            depth += 1
        elif blank[j] == "}":
            depth -= 1
            if depth == 0:
                return i, j + 1
    return i, len(blank)


def _dens_module(f: Path, key: tuple) -> dict:
    """The file parsed once: comment-masked text (strings kept: the SQL lives in them), the declaration starts, the
    offsets of `density_contract:` DECLARATIONS (R232: comments stripped, strings blanked), and the string literals
    with their offsets."""
    if key not in _DENS_FACTS:
        txt = f.read_text(encoding="utf-8", errors="replace")
        blank = _ts_mask(txt, blank_strings=True)
        spans = _ts_literal_spans(txt)
        _DENS_FACTS[key] = dict(
            cmask=_ts_mask(txt),
            starts=_ts_decl_starts(blank),
            contracts=[m.start() for m in _DENSITY_DECL.finditer(blank)],
            contract_objs=[(m.start(), *_enclosing_object(blank, m.start())) for m in _DENSITY_DECL.finditer(blank)],
            spans=spans,
            desynced=_ts_desynced(txt),
            dynamic_from=_dynamic_from(txt, spans),
        )
    return _DENS_FACTS[key]


def _decl_of(mod: dict, pos: int) -> int:
    return bisect.bisect_right(mod["starts"], pos)


_WORD_SELECT = re.compile(r"\bSELECT\b", re.I)
_NOT_A_READ_PREFIX = re.compile(r"\b(?:INSERT|CREATE|MERGE|COPY|UNION|INTERSECT|EXCEPT)\b", re.I)


_SQL_TOKEN = re.compile(r"'(?:[^']|'')*'|/\*.*?\*/|--[^\n]*", re.S)


def _sql_flat(sql: str, strings: bool = True) -> str:
    """`sql` with its SQL comments (`/* … */`, `-- …`) — and, with `strings`, its `'…'` literals — blanked to spaces,
    positions kept: a paren or a keyword inside a comment or a string is not SQL structure."""
    def blank(m):
        t = m.group(0)
        return t if (t[0] == "'" and not strings) else re.sub(r"[^\n]", " ", t)
    return _SQL_TOKEN.sub(blank, sql)


# the read side of a write / a set operation, matched strictly (SQL syntax, not prose) when the evidence is only the
# PREVIOUS literal of a concatenation
_NOT_A_READ_STRICT = re.compile(
    r"\b(?:INSERT\s+INTO|MERGE\s+INTO|CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP\w*\s+|MATERIALIZED\s+|UNLOGGED\s+)?(?:TABLE|VIEW)"
    r"|COPY\s+\S+|UNION(?:\s+ALL)?|INTERSECT|EXCEPT)\b", re.I)


def _owner_select(head: str):
    """The SELECT that owns a FROM sitting at the end of `head`: the last whole-word SELECT after which the
    parentheses balance (a SELECT inside an earlier `( … )` belongs to that sub-query, not to this FROM). Comments and
    string literals are blanked first: a `)` in either is not a paren."""
    flat = _sql_flat(head)
    for m in reversed(list(_WORD_SELECT.finditer(flat))):
        depth = 0
        for ch in flat[m.end():]:
            depth += (ch == "(") - (ch == ")")
            if depth < 0:
                break
        if depth == 0:
            return m
    return None


def _is_served_read(head: str, sel_start: int, before: str = "") -> bool:
    """Is the SELECT at `sel_start` of `head` a served READ — not a `( SELECT …` sub-query (WHERE .. IN, EXISTS, a CTE
    body) and not the read side of an INSERT / CREATE … AS / MERGE / COPY, nor a UNION / INTERSECT / EXCEPT branch
    (its column names come from the first branch)? SQL comments are blanked before the test. When the SELECT opens its
    literal (`'… IN (' + 'SELECT …'`), its context is the end of the PREVIOUS literal (`before`): a `(`, or a write /
    set-operation prefix, there makes it not-a-read. The context is judged on what is visible; a caller that cannot
    see it (a SELECT reached through a helper, a variable) is not seen at all — disclosed limit."""
    pre = _sql_flat(head[:sel_start], strings=False).rsplit(";", 1)[-1]
    if not pre.strip() and before:
        b = _sql_flat(before, strings=False).rsplit(";", 1)[-1]
        return not b.rstrip().endswith("(") and not _NOT_A_READ_STRICT.search(b)
    return not pre.rstrip().endswith("(") and not _NOT_A_READ_PREFIX.search(pre)


def _served_selects(table: str, lits: list[str], strict: bool = False):
    """`(i, match, alias, select_list)` for every `FROM|JOIN <table>` in literal `i` that sits under a SELECT list
    (R23's reader, factored so the Dens scan and `field_reach` read a served select identically). A FROM counts only
    with a SELECT in front of it — in the same literal or, for `'SELECT a, b ' + 'FROM t'`, the literal before (prose
    that says "from <table>" is not a query). `SELECT` is a whole word (`is_selected` is not one).
    `strict` (the Dens scan): the FROM's OWN select is found by paren balance, and when it is not a served read
    (`_is_served_read`) `select_list` is None — the select is counted as served but its list credits no tier column."""
    rx = re.compile(r"\b(?:FROM|JOIN)\s+(?:ONLY\s+)?(?:public\.)?\"?" + re.escape(table) +
                    r"\b\"?(?:\s+(?:AS\s+)?([A-Za-z_][A-Za-z_0-9]*))?", re.I)
    for i, lit in enumerate(lits):
        for m in rx.finditer(lit):
            alias = m.group(1) if m.group(1) and m.group(1).lower() not in _ALIAS_STOP else None
            head = lit[:m.start()]
            k = _owner_select(head) if strict else next(iter(reversed(list(_WORD_SELECT.finditer(head)))), None)
            if k is not None:
                sel = head[k.end():]
                ok = _is_served_read(head, k.start(), lits[i - 1] if i else "")
            elif strict and _WORD_SELECT.search(head):
                continue                                   # a SELECT exists but none owns this FROM (EXTRACT(.. FROM t))
            else:
                prev = lits[i - 1] if i else ""
                k2 = _owner_select(prev) if strict else next(iter(reversed(list(_WORD_SELECT.finditer(prev)))), None)
                if k2 is None or re.search(r"\bFROM\b", _sql_flat(prev[k2.start():]), re.I):
                    continue
                sel = prev[k2.end():]
                ok = _is_served_read(prev, k2.start(), lits[i - 2] if i > 1 else "")
            yield i, m, alias, (sel if (ok or not strict) else None)


_SEL_CAST = re.compile(r"::\s*[A-Za-z_][\w.]*(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?(?:\[\])*")
_SEL_ALIAS = re.compile(r"\s+AS\s+(?:\"[^\"]*\"|\w+)\s*$", re.I)
_SEL_PLAIN_ITEM = re.compile(r"(?:DISTINCT\s+)?(?:\"?([A-Za-z_]\w*)\"?\s*\.\s*)?\"?([A-Za-z_]\w*)\"?", re.I)


def _plain_item(item: str) -> tuple[str | None, str] | None:
    """`(qualifier, name)` when a select item IS a column reference — `col`, `q.col`, `"col"`, with an optional `::cast`
    and `AS alias` — else None (a function call, CASE, arithmetic, a sub-select, `*`: never a column by itself)."""
    it = _SEL_ALIAS.sub("", _SEL_CAST.sub("", item.strip())).strip()
    m = _SEL_PLAIN_ITEM.fullmatch(it)
    return (m.group(1), m.group(2)) if m else None


def _flatten_select(clean: str) -> str:
    """The select text as a list of top-level items: a top-level `FROM` (the scanner's text can carry one — a
    sub-select's truncated list, a driving table) and an unmatched `)` (the cut-off `(SELECT …` opener) become item
    separators, so each clause is read as its own item and an item is never glued to its FROM clause."""
    out, depth, i = [], 0, 0
    while i < len(clean):
        ch = clean[i]
        m = re.match(r"FROM\b", clean[i:], re.I) if (ch in "Ff" and (i == 0 or not re.match(r"\w", clean[i - 1]))) else None
        if m and depth == 0:
            out.append(" , ")
            i += 4
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                out.append(" , ")
                i += 1
                continue
            depth -= 1
        out.append(ch)
        i += 1
    return "".join(out)


def _select_tier(sel: str, alias: str | None, table: str, cols: list[str] | None) -> tuple[str, list[str]]:
    """Does this served select list carry a tier column? `(TIER_YES|TIER_NO|TIER_UNKNOWN, tier columns)`.
    A tier column is carried only when a select ITEM is the column itself (`_plain_item`): `count(DISTINCT tier)`,
    `count(*) FILTER (WHERE tier = …)`, `lower(tier)`, `CASE … END AS tier` carry none. With the table's columns known
    (catalog) the item's name must also be one of them and `*` / `<alias>.*` expands to every column; with them
    unknown only a tier NAME counts (unqualified, or qualified by this table/alias) and `*` / a `${...}` run-time list
    stay UNKNOWN — never read as a tier column and never as proof of its absence.
    ATTRIBUTION LIMIT, disclosed: the scanner hands over the text after the LAST `SELECT` before the asset's `FROM` /
    `JOIN`. A `(SELECT …)` in the list, or any `FROM` in it (a sub-select's truncated list, or a driving table the
    asset is only JOINed to), means an UNQUALIFIED name cannot be attributed to the asset's table: UNKNOWN, never YES.
    A name qualified by the asset's own table/alias still counts.
    DELIBERATE OVER-BLOCKING, kept: a `(SELECT …)` scalar sub-select anywhere in the list makes the whole list UNKNOWN
    (PARTIAL at best, never PASS) even when a tier column is also qualified by the asset's alias — PASS is the closable
    direction (§N.8), so the ambiguity is resolved against it."""
    dynamic = "${" in sel
    clean = re.sub(r"'[^']*'", "''", sel)
    if re.search(r"\(\s*SELECT\b", clean, re.I):
        return TIER_UNKNOWN, []
    has_from = bool(re.search(r"\bFROM\b", clean, re.I))
    mine = {x.lower() for x in (alias, table) if x}
    lower = {c.lower() for c in cols} if cols else set()
    got: set[str] = set()
    star = unattributed = False
    for item in _split_top(_flatten_select(clean)):
        it = item.strip()
        if re.fullmatch(r"(?:DISTINCT\s+)?\*", it, re.I) or any(re.fullmatch(rf"{re.escape(m)}\.\*", it, re.I) for m in mine):
            star = True
            got.update(c for c in lower if DENS_TIER_COLUMN.match(c))
            continue
        pi = _plain_item(it)
        if not pi:
            continue
        q, name = pi
        if not DENS_TIER_COLUMN.match(name) or (cols and name.lower() not in lower):
            continue
        if q:
            if q.lower() in mine:
                got.add(name.lower())
        elif has_from:
            unattributed = True
        else:
            got.add(name.lower())
    if got:
        return TIER_YES, sorted(got)
    if unattributed:
        return TIER_UNKNOWN, []
    return (TIER_UNKNOWN if ((star and not cols) or dynamic) else TIER_NO), []


def _name(rel: Path, root: str, first: bool) -> str:
    return rel.as_posix() if first else f"{root}/{rel.as_posix()}"


def capability_scan(caps_dirs, tables: list[str], shared=(), columns: dict | None = None, outside_roots=()) -> dict:
    """E6.1 (d): the Dens scanner, repaired (N-22 ruling principle 4). Structural: it reads source, not behaviour.

    SCOPE. `caps_dirs` (one path or several; `measure()` passes `CAPS_ROOTS`, R23's serving roots) are read
    RECURSIVELY — every layer directory, the files at the layers root, both MCP roots — for every token in `tables`
    (target table, asset id, every `count_sql` table). A missing root is `scanned=False` (R222 / N3), never an N/A.
    `outside_roots` (the wider source trees) are probed ONLY so that an asset with a served select outside the serving
    roots is never read N/A: they grade nothing (no density contract lives there). The probe honours R51 (§N.8): a
    served select read in code is `outside`; otherwise the file is `outside_named` — and so also blocks N/A — when
    (a) only a COMMENT names a token, (b) the file is `.tsx` or the string scanner ends desynchronised on it (an
    apostrophe in JSX text, a quote in a regex literal: `_ts_desynced`) and ANY text names a token, or (c) it holds a
    token in code and selects `FROM ${...}` (a run-time table name). Limits, disclosed: a run-time table name built
    in a file that never names the asset or its table, and two stray quotes that re-sync the scanner by accident in a
    `.ts` file, are not seen; a names-map in a cleanly parsed `.ts` file (no select, no comment) does not block N/A.

    ATTRIBUTION. A token in `shared` (a table another asset also declares) never attributes a module to THIS asset:
    `chart_facts` would make every reader serve every asset. Attribution is per capability (a top-level declaration):
    a `density_contract:` counts for the asset only in a declaration that references it, and only a tier column in a
    served `SELECT ... FROM <the asset's table>` INSIDE THE SAME capability entry (the object literal holding the
    `density_contract:` key, whose value must be a real object/identifier) makes it dense; a sibling entry's select, a
    sub-select, an INSERT...SELECT or a UNION branch credits nothing. A serving-root file that names the asset but on
    which the string scanner loses sync (`_ts_desynced`) is returned in `unparsed` and grades NO_DETECTOR (never FAIL,
    never N/A; a PASS/PARTIAL earned in a clean file stands).

    Returns `modules` (by code, attributing tokens), `density` (capabilities that are dense), `dense`, `declared`
    (modules whose referencing capability declares the contract, with why the tier half is missing), `tier_only`,
    `served` (how many served selects of the asset's tables), `shared_only`, `comment_only` (R51: a comment names it,
    no code does), `outside`, `outside_named`."""
    dirs = [caps_dirs] if isinstance(caps_dirs, str) else list(caps_dirs)
    for d in dirs:
        if not (ROOT / d).is_dir():
            # R222 / N3: `scanned=False` — "no module references the table" was never established.
            return dict(modules=[], density=0, note=f"no capability directory at {d}", scanned=False)
    shared = set(shared or ())
    columns = columns or {}
    toks = [t for t in dict.fromkeys(tables) if t and t not in shared]
    sh = [t for t in dict.fromkeys(tables) if t and t in shared]
    hits, dense, declared, tier_only, shared_only, mentions, elsewhere = [], [], [], [], [], [], []
    unparsed: list[str] = []
    served = 0
    seen: set[str] = set()
    for i, root in enumerate(dirs):
        base = ROOT / root
        for f in sorted(base.rglob("*.ts")):
            if f.name.endswith(".test.ts") or "__tests__" in f.parts:
                continue
            seen.add(str(f))
            name = _name(f.relative_to(base), root, i == 0)
            key, words = _dens_words(f)
            code_toks = [t for t in toks if t in words]
            code_sh = [t for t in sh if t in words]
            if not code_toks and not code_sh:
                continue
            mod = _dens_module(f, key)
            if mod["desynced"] and code_toks:
                # the string scanner lost sync on this file: what it reports (literals, comment blanking, declaration
                # boundaries, the contract) is unreliable, so it neither attributes the asset nor proves it unserved.
                # NO_DETECTOR for the asset (never FAIL, never N/A, never PASS from this file).
                unparsed.append(name)
                continue
            has = lambda t: re.search(r"\b" + re.escape(t) + r"\b", mod["cmask"])      # noqa: E731  (code, strings kept)
            ref_toks = [t for t in code_toks if has(t)]                                # R51: code, not a comment
            if not ref_toks:
                if any(has(t) for t in code_sh):
                    shared_only.append(name)
                elif code_toks:
                    mentions.append(name)                                              # R51: named in a comment only
                continue
            hits.append(name)
            refs = {_decl_of(mod, m.start()) for t in ref_toks for m in re.finditer(r"\b" + re.escape(t) + r"\b", mod["cmask"])}
            # a capability ENTRY that declares the contract: the object literal holding the `density_contract:` key, in a
            # top-level declaration that references the asset
            cobjs = [o for o in mod["contract_objs"] if _decl_of(mod, o[0]) in refs]
            contract_decls = {_decl_of(mod, o[0]) for o in cobjs}
            lits = [c for _p, c in mod["spans"]]
            sels: list[tuple[int, int, str, list[str]]] = []                           # (declaration, offset, tier state, columns)
            # a select of a SHARED table counts only inside a capability that names THIS asset (by its id or by a table
            # only it declares): the asset id discriminates what the shared table cannot
            for t in ref_toks + [x for x in code_sh if has(x)]:
                for li, m, alias, sel in _served_selects(t, lits, strict=True):
                    pos = mod["spans"][li][0]
                    d = _decl_of(mod, pos)
                    if d in refs:
                        st = (_select_tier(sel, alias, t, columns.get(t.lower()) or columns.get(t))
                              if sel is not None else (TIER_UNKNOWN, []))           # not the served read: credits nothing
                        sels.append((d, pos, st[0], st[1]))
                        served += 1
            tier_decls = {d for d, _p, st, _c in sels if st == TIER_YES}
            inside = lambda o: [(st, cs) for _d, p, st, cs in sels if o[1] <= p < o[2]]    # noqa: E731
            dense_cols = sorted({c for o in cobjs for st, cs in inside(o) if st == TIER_YES for c in cs})
            if dense_cols:
                # PASS: the contract and the tier select belong to the SAME capability entry (the contract's own object)
                dense.append((name, dense_cols))
            else:
                # a contract counts for the asset only in a capability entry that also SERVES it (a served select of its
                # table inside the object that declares the contract) — a declaration that merely names the asset's id,
                # or a sibling entry's select, is not its serving capability
                why = set()
                for o in cobjs:
                    sts = {st for st, _c in inside(o)}
                    if sts:
                        why.add("tier carriage not established (a run-time select list, a sub-select / INSERT…SELECT / "
                                "UNION branch, or SELECT * with unknown columns)" if TIER_UNKNOWN in sts
                                else "no tier column in its served select")
                    elif any(sd == _decl_of(mod, o[0]) for sd, *_r in sels):
                        why.add("its served select of the table is in the same top-level declaration but a different "
                                "capability entry, not the object that declares the contract (attribution not established)")
                    elif sels:
                        why.add("its served select of the table is in a different top-level declaration of the module "
                                "(contract/select attribution not established)")
                if why:
                    declared.append((name, sorted(why)))
                else:
                    if tier_decls:
                        tier_only.append(name)
                    if sels and mod["contracts"]:
                        elsewhere.append(name)       # the module declares a contract, but not in a capability that serves it
    outside: list[str] = []
    outside_named: list[str] = []
    for root in outside_roots or ():
        base = ROOT / root
        if not base.is_dir():
            return dict(modules=[], density=0, note=f"no source directory at {root}", scanned=False)
        for ext in ("*.ts", "*.tsx"):
            for f in sorted(base.rglob(ext)):
                if str(f) in seen or DENS_OUTSIDE_EXCLUDE.search(str(f)):
                    continue
                seen.add(str(f))
                key, words = _dens_words(f)
                present = [t for t in toks if t in words]
                if not present:
                    continue
                mod = _dens_module(f, key)
                rel = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else str(f)
                lits = [c for _p, c in mod["spans"]]
                if any(next(_served_selects(t, lits), None) for t in present):
                    outside.append(rel)
                    continue
                # No served select was read. That is a finding only for a file the scanner read RELIABLY (R51 / §N.8):
                if ext == "*.tsx" or mod["desynced"]:
                    # JSX text / a stray quote desynchronises the string scanner, so a select it missed is not evidence
                    # of none: ANY textual reference (code or comment) keeps the asset off the closable N/A
                    outside_named.append(f"{rel} (unparsed file — JSX, a nested template literal or a regex desynced the scanner: the asset is named in its text)")
                elif any(not re.search(r"\b" + re.escape(t) + r"\b", mod["cmask"]) for t in present):
                    outside_named.append(f"{rel} (a comment names it)")                          # R51: alone or beside code
                elif mod["dynamic_from"]:
                    outside_named.append(f"{rel} (holds the table and selects FROM a run-time table name)")
    return dict(modules=hits, density=len(dense), note="", scanned=True, comment_only=mentions, dense=dense,
                declared=declared, tier_only=tier_only, served=served, shared_only=shared_only, outside=outside, outside_named=outside_named, unparsed=unparsed, elsewhere=elsewhere,
                shared_tokens=sh, tokens=toks, roots=dirs)


def _few(xs, n: int = 6) -> str:
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" (+{len(xs) - n} more)" if len(xs) > n else "")


def _grade_dens(cap: dict, label: str) -> dict:
    """`Dens.served` from a `capability_scan` result. STRUCTURAL throughout: the contract is a declared property and the
    tier column a name in a served select — neither is a check that the served rows are in fact layered.
    PASS only when a capability that references the asset declares the contract AND a served select of its table in that
    same capability carries a tier column. See `capability_scan` for the attribution rule."""
    if cap.get("scanned") is not True:
        # R222 / N3 (A_REVIEW2 G2): a root was not scanned (missing), so "no module serves this table" was never
        # established. It read the closable N/A — one live ledger-copy run closed all 24 open L0 Dens.served gaps
        # with the dir pointed elsewhere.
        return dict(v=NO_DET, measured=f"NO_DETECTOR — {cap.get('note') or 'capability scan did not run'}; "
                                       "the served surface was never scanned")
    mods = cap.get("modules") or []
    outside = cap.get("outside") or []
    reach = f"{len(mods)} module(s) reach it by code: {_few(mods)}"
    tail = (f"; also a served select outside the scanned serving roots (not graded): {_few(outside, 3)}"
            if outside and mods else "")
    if mods and cap.get("density"):
        d = cap.get("dense") or []
        return dict(v=PASS, measured=(f"STRUCTURAL: {reach}; {cap['density']} capability(ies) declare density_contract AND "
                                      f"select a tier column from it ({_few(sorted({c for _n, cs in d for c in cs}))}) "
                                      f"in: {_few(n for n, _c in d)}" + tail))
    if mods and cap.get("declared"):
        det = "; ".join(f"{n}: {', '.join(w)}" for n, w in cap["declared"][:4])
        return dict(v=PARTIAL, measured=(f"STRUCTURAL: {reach}; a referencing capability declares density_contract but "
                                         f"{det}" + tail))
    if cap.get("unparsed"):
        # a serving-root file that names the asset could not be read reliably: what it serves, and whether it declares the
        # contract, is unknown — so neither FAIL (no contract anywhere) nor N/A (not served) was established
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — {len(cap['unparsed'])} serving-root file(s) naming {label} lose the "
                                        f"string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a "
                                        f"quote desynced it): {_few(cap['unparsed'], 4)}; its served "
                                        "select and density_contract cannot be read — never FAIL, never the closable N/A"))
    if mods and cap.get("served"):
        extra = ((f"; a tier column is selected without a contract in: {_few(cap['tier_only'])}" if cap.get("tier_only") else "")
                 + (f"; a density_contract is declared in {_few(cap['elsewhere'], 3)}, but not in a capability that serves it"
                    if cap.get("elsewhere") else ""))
        return dict(v=FAIL, measured=(f"STRUCTURAL: {reach}; {cap['served']} served select(s) of its table; no referencing "
                                      f"capability that serves it declares density_contract{extra}" + tail))
    if mods:
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — {reach}, but no served `SELECT ... FROM` its table was found "
                                        f"(no served select): whether it is served cannot be told by code"
                                        + tail))
    if outside:
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — no module in the serving roots references {label}, but a served "
                                        f"select of it sits outside the scanned serving roots: {_few(outside, 4)} — the "
                                        "served surface cannot be graded by this scan (never the closable N/A)"))
    if cap.get("outside_named"):
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — no module in the serving roots references {label}, but it is "
                                        f"named outside the scanned serving roots where a served select cannot be ruled "
                                        f"out (R51): {_few(cap['outside_named'], 4)} — never the closable N/A"))
    if cap.get("shared_only"):
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — only a table other assets share ({_few(cap.get('shared_tokens') or [])}) "
                                        f"is referenced, by {len(cap['shared_only'])} module(s): {_few(cap['shared_only'], 3)}; "
                                        f"the served surface cannot be attributed to {label} by code (never the closable N/A)"))
    if cap.get("comment_only"):
        # R51 + §N.8: no module's CODE references the table, but comments do — the asset is named as served (e.g.
        # "already-served-elsewhere bg_dignity_reference", served by the generic MCP DB route). "Not served" was never
        # established, so never the closable N/A.
        return dict(v=NO_DET, measured=(f"NO_DETECTOR — no capability module's code references {label}; named in comments "
                                        f"only in: {', '.join(cap['comment_only'])} — the served surface cannot be "
                                        "attributed by code (never the closable N/A)"))
    return _na(f"STRUCTURAL: 0 module(s) reference it by code in the {len(cap.get('roots') or [])} "
               "serving root(s) scanned, and no served select of it exists in the wider source "
               "scanned; declaring density_contract: 0", "no-served-surface")


# ─────────── R23 (W2-3): field-level reachability over capability modules ───────────

# Every layer's capability modules: a field is dark only if NO retrieval capability, of any layer, reads it
# (an L4 capability reads chart_facts as readily as an L1 one). Tests and `__tests__` are not capabilities.
CAPS_ROOT = "platform/src/lib/retrieval/registry/layers"
# W2-3 C3 (gate review §5): the MCP server is a second serving plane. Its tools
# (`platform-mcp/src/tools/**`) run SQL directly, and so do the `platform-mcp/src/lib/**` modules those
# tools import (`lib/kala_envelope.ts`, imported by five `tools/kala_views/*` tools, reads
# kala_field_skill). The registry layers alone called ga_prashna_judgment "dark" while
# `tools/register_p1_synthesis.ts` serves it. Every root is scanned; a missing one leaves R23 unmeasured.
CAPS_ROOTS = (CAPS_ROOT, "platform-mcp/src/tools", "platform-mcp/src/lib")
DENS_OUTSIDE_ROOTS = ("platform/src", "platform-mcp/src")
# `retrieval/registry/knowledge/` holds read-only availability PROBES that mirror a handler's own source query (already read in
# CAPS_ROOTS) and the catalogue metadata naming every asset; it serves no rows, so it is not a served surface.
DENS_OUTSIDE_EXCLUDE = re.compile(r"\.test\.tsx?$|\.d\.ts$|__tests__|/generated/|node_modules|/retrieval/registry/knowledge/")
_SQL_STOP = re.compile(r"\b(?:ORDER\s+BY|GROUP\s+BY|LIMIT|OFFSET|UNION|RETURNING|FROM|WINDOW|HAVING)\b|;", re.I)
_ALIAS_STOP = {"where", "join", "left", "right", "inner", "outer", "full", "cross", "on", "order", "group", "limit",
               "offset", "union", "as", "using", "natural", "lateral", "window", "having", "returning", "for"}


def _ts_literals(src: str) -> list[str]:
    """R23: the CONTENTS of a TypeScript module's string and template literals, in order — comments skipped
    (the same scanner discipline as `_ts_code`, R51: `//` inside a string is not a comment)."""
    out, i, n = [], 0, len(src)
    while i < n:
        c, nx = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and nx == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i + 1:min(j, n)])
            i = j + 1
        else:
            i += 1
    return out


_CAPS_LITERALS: dict[tuple, list[str]] = {}


def capability_sql(caps_root: str | None = None) -> dict[str, list[str]]:
    """R23: serving module -> its SQL-bearing literals (a FROM or JOIN in them). With no `caps_root`, every
    serving root in `CAPS_ROOTS` (C3): registry-layer modules keyed by their path under the registry root
    (unchanged), every other root's modules keyed `<root>/<path>`. With `caps_root`, that one root, keyed by
    the path under it. A missing directory raises `Unknown`: "no capability reads it" is never inferred from a
    scan that did not run (R222 / N3's rule, at field grain)."""
    if caps_root is None:
        out: dict[str, list[str]] = {}
        for i, root in enumerate(CAPS_ROOTS):
            out.update(capability_sql(root) if i == 0 else
                       {f"{root}/{k}": v for k, v in capability_sql(root).items()})
        return out
    d = ROOT / caps_root
    if not d.is_dir():
        raise Unknown(f"no capability directory at {caps_root}")
    out: dict[str, list[str]] = {}
    for f in sorted(d.rglob("*.ts")):
        if f.name.endswith(".test.ts") or "__tests__" in f.parts:
            continue
        st = f.stat()
        key = (str(f), st.st_mtime_ns, st.st_size)          # re-read only a module that changed
        if key not in _CAPS_LITERALS:
            # C3: SELECT-only literals are kept too — `\`SELECT a, b \` + \`FROM t \`` puts the select list in
            # the literal BEFORE the FROM, and `field_reach` reads it from there; dropping it here made the
            # concatenated form read as zero columns / no query at all.
            _CAPS_LITERALS[key] = [x for x in _ts_literals(f.read_text(encoding="utf-8", errors="replace"))
                                   if re.search(r"\b(?:FROM|JOIN|SELECT)\b", x, re.I)]
        lits = _CAPS_LITERALS[key]
        if lits:
            out[str(f.relative_to(d))] = lits
    return out


def _split_top(s: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    return parts + ["".join(cur)]


def _selected_columns(sel: str, cols: list[str], alias: str | None, table: str) -> set[str]:
    """The table's columns a SELECT list reads: `*` / `<alias>.*` -> every column; `<alias>.col` or a bare
    `col` (also inside an expression, `coalesce(col, …)`, `jsonb_build_object('k', col)`) -> that column;
    `<other_alias>.col` -> not this table's. String literal contents never count."""
    lower = {c.lower() for c in cols}
    mine = {x for x in (alias, table) if x}
    got: set[str] = set()
    sel = re.sub(r"'[^']*'", "''", sel)
    for item in _split_top(sel):
        it = item.strip()
        if it == "*" or re.fullmatch(r"(?:DISTINCT\s+)?\*", it, re.I) or \
                any(re.fullmatch(rf"{re.escape(m)}\.\*", it, re.I) for m in mine):
            return set(lower)
        for q, name in re.findall(r"(?:\b([A-Za-z_][A-Za-z_0-9]*)\s*\.\s*)?\b([A-Za-z_][A-Za-z_0-9]*)\b", it):
            if name.lower() in lower and (not q or q.lower() in {m.lower() for m in mine}):
                got.add(name.lower())
    return got


def _literal_pins(where: str, cols: list[str]) -> dict[str, set[str]] | None:
    """Row-level: the literal equality / IN pins a query's predicate puts on the table's own columns
    (`fact_category = 'dasha'`, `varga IN ('D9','D10')`). Parameters (`= $2`) pin nothing — the caller may
    ask for any value. An OR anywhere makes the predicate unanalysable here: None (read as unpinned, so
    depth stays an UPPER bound, never an invented narrowing)."""
    if re.search(r"\bOR\b", where, re.I):
        return None
    lower = {c.lower() for c in cols}
    pins: dict[str, set[str]] = {}
    for c, v in re.findall(r"(?:\b\w+\.)?\b(\w+)\s*=\s*'([^']*)'", where):
        if c.lower() in lower:
            pins.setdefault(c.lower(), set()).add(v)
    for c, vs in re.findall(r"(?:\b\w+\.)?\b(\w+)\s+IN\s*\(\s*('[^)]*')\s*\)", where, re.I):
        if c.lower() in lower:
            pins.setdefault(c.lower(), set()).update(re.findall(r"'([^']*)'", vs))
    return pins


def field_reach(table: str, cols: list[str], sql_by_module: dict[str, list[str]]) -> dict:
    """R23: which of `table`'s columns any capability module's SQL selects (width), and whether its
    queries pin rows by literal values (depth). Static and syntactic: see `_selected_columns` /
    `_literal_pins`; SQL a capability reaches through an imported helper is not followed. A FROM counts
    only with a SELECT in front of it (prose that says "from <table>" is not a query); a `${…}` select
    list is recorded in `dynamic_select` (its columns are unknown — width becomes a lower bound)."""
    exposed: set[str] = set()
    modules, pinned, unpinned, dynamic = [], [], False, []
    for mod, lits in sql_by_module.items():
        hit = False
        for i, m, alias, sel in _served_selects(table, lits):
            lit = lits[i]
            hit = True
            if "${" in sel:                               # `SELECT ${cols}`: the list is built at run time
                dynamic.append(mod)
            exposed |= _selected_columns(sel, cols, alias, table)
            # a keyword read as the alias (`FROM t WHERE …`) belongs to the tail, not the alias
            tail = lit[m.end() if alias or not m.group(1) else m.start(1):]
            w = re.search(r"\bWHERE\b", tail, re.I)
            where = ""
            if w:
                where = tail[w.end():]
                stop = _SQL_STOP.search(where)
                where = where[:stop.start()] if stop else where
            p = _literal_pins(where, cols)
            if p:
                pinned.append(p)
            else:
                unpinned = True
        if hit:
            modules.append(mod)
    return dict(modules=modules, exposed=exposed, pinned=pinned, unpinned=unpinned,
                dynamic_select=sorted(set(dynamic)))


def _pin_predicate(pins: list[dict[str, set[str]]]) -> str:
    def lit(v):
        return "'" + v.replace("'", "''") + "'"
    return " OR ".join("(" + " AND ".join(f"{c}::text IN ({', '.join(lit(v) for v in sorted(vs))})"
                                          for c, vs in sorted(p.items())) + ")" for p in pins)


def _grade_reach(tbl: str, cols: list[str], dc: dict, caps: dict | None, caps_note: str | None,
                 chart_id: str) -> tuple[dict, dict | None]:
    """R23: `Reach.fields` for an asset's target table — REPORTED, NOT GRADED (verdict stays NOT_GENERIC:
    a static SQL parse is a proxy for exposure, and a grading threshold is a decision above the census).
    Width = built columns some capability selects / built columns, where "built" is the depth census's
    populated columns (every column when depth did not measure rows — said so). Depth = the fraction of the
    table's rows (the bound chart's, when it has chart_id) some capability query can return: 1.0 when any
    query reads it with no literal row pin (an upper bound), else the rows matching the union of the pins,
    counted read-only; 0.0 when no capability reads the table at all."""
    if caps is None:
        return dict(v=NOT_GENERIC, measured=f"field reachability unmeasured: {caps_note}"), None
    fr = field_reach(tbl, cols, caps)
    never = set(c.lower() for c in dc.get("never", [])) if dc.get("rows") else set()
    built = [c.lower() for c in cols if c.lower() not in never]
    basis_b = "populated columns (depth census)" if dc.get("rows") else "all columns (depth census measured no rows)"
    exp = sorted(set(built) & fr["exposed"])
    dark = sorted(set(built) - fr["exposed"])
    width = (len(exp) / len(built)) if built else None
    if not fr["modules"]:
        depth, dbasis = 0.0, "no capability module reads this table"
    elif fr["unpinned"]:
        depth, dbasis = 1.0, "a capability query reads it with no literal row pin (upper bound)"
    else:
        scoped = " WHERE chart_id = '" + chart_id + "'" if "chart_id" in [c.lower() for c in cols] else ""
        try:
            hitn, total = psql(f"SELECT (count(*) FILTER (WHERE {_pin_predicate(fr['pinned'])}))::text, count(*)::text "
                               f"FROM {tbl}{scoped}")[0]
            depth = (int(hitn) / int(total)) if int(total) else None
            dbasis = (f"{hitn}/{total} rows{' of chart ' + chart_id[:8] if scoped else ''} match the capability "
                      f"queries' literal pins {_pin_predicate(fr['pinned'])[:160]}")
        except Unknown as exc:
            depth, dbasis = None, f"unmeasured: the pin count errored ({exc})"
    reach = dict(table=tbl, modules=fr["modules"], columns_built=len(built), built_basis=basis_b,
                 exposed=exp, dark=dark, width=(round(width, 4) if width is not None else None),
                 width_is_lower_bound=bool(fr["dynamic_select"]), dynamic_select=fr["dynamic_select"],
                 depth=(round(depth, 4) if depth is not None else None), depth_basis=dbasis)
    wtxt = (("≥ " if fr["dynamic_select"] else "") + f"{len(exp)}/{len(built)} built column(s) ({width:.1%})"
            + (f", a lower bound: {', '.join(fr['dynamic_select'])} select(s) a run-time column list"
               if fr["dynamic_select"] else "")) if width is not None else "no built column"
    dtxt = f"{depth:.1%}" if depth is not None else "unmeasured"
    return dict(v=NOT_GENERIC, measured=(f"reported, not graded — width {wtxt} selected by {len(fr['modules'])} "
                                         f"capability module(s); dark: {dark[:12]}{' …' if len(dark) > 12 else ''}; "
                                         f"depth {dtxt} ({dbasis})")), reach


def local_map_candidates(prefix: str) -> int:
    """Rule 6 candidates: literal graha-name sets in the layer's own python package."""
    pkg = ROOT / "platform" / "python-sidecar" / "brahmagyan"
    if not pkg.is_dir():
        return -1
    n = 0
    for f in pkg.rglob("*.py"):
        txt = f.read_text(encoding="utf-8", errors="replace")
        if re.search(r"['\"]Sun['\"]\s*[,:]", txt) and re.search(r"['\"]Venus['\"]", txt):
            n += 1
    return n


# ─────────────────────────── database reads ───────────────────────────

def registry(layer_key: str) -> tuple[dict[str, dict], dict]:
    """Read via json_agg, NOT line-oriented output.

    `count_sql` and `integrity_check_sql` contain newlines, so a row-per-line read splits one asset
    across several lines and invents assets whose ids are fragments of SQL. That bug produced 52 assets
    from 40 on this script's first run — the same defect class the layer template warns about, an
    instrument whose population was never stated. One JSON document has no such ambiguity.

    R220: `asset_registry` for this prefix has more rows than the ACTIVE population the census
    should measure — 129 total vs 127 active registry-wide (2 retired L3 rows, measured 2026-09-27).
    `is_active AND NOT dead_flag` is the register's own phrasing, but `dead_flag` is NULL (not
    false) on every row today, and `NOT NULL` is NULL in SQL — so that exact expression silently
    matches ZERO rows, not 127. The honest form is `is_active AND NOT coalesce(dead_flag, false)`.
    Excluded (inactive) rows are named here, not silently dropped — `measure()` states the
    population figure in its own output rather than letting 129 and 127 quietly disagree.

    R224 (A_REVIEW2 G5): the population is scoped by `asset_registry.layer`, NOT by the asset-id
    prefix. The prefix is a naming convention, not the registry's own statement of which layer an
    asset belongs to: `lel_events` (layer='mimamsa', no `mi_` prefix) was silently outside every
    layer's census — 126 measured where the tracker counts 127. `layer` is what the registry
    declares; the prefix still names the layer's writers and capability modules, nothing more."""
    cfg = LAYERS[layer_key]
    scope = f"layer = '{cfg['registry_layer']}'"
    total = int(scalar(f"SELECT count(*)::text FROM asset_registry WHERE {scope}") or 0)
    excluded = [dict(asset_id=r[0], is_active=(r[1] == "t"), catalog_status=r[2])
                for r in psql("SELECT asset_id, is_active::text, coalesce(catalog_status,'') "
                              f"FROM asset_registry WHERE {scope} "
                              "AND NOT (is_active AND NOT coalesce(dead_flag,false)) ORDER BY asset_id")]
    blob = scalar(
        "SELECT coalesce(json_agg(json_build_object("
        "'asset_id',asset_id,'has_writer',coalesce(has_writer,false),'target_table',target_table,"
        "'count_sql',coalesce(count_sql,''),'has_integrity',(integrity_check_sql IS NOT NULL),"
        "'depends_on',coalesce(to_json(depends_on),'[]'::json),'target_floor',target_floor,"
        "'catalog_status',coalesce(catalog_status,''),'asset_kind',coalesce(asset_kind,''))"
        " ORDER BY asset_id)::text,'[]') "
        f"FROM asset_registry WHERE {scope} "
        "AND is_active AND NOT coalesce(dead_flag,false)")
    rows = json.loads(blob or "[]")
    out = {}
    for r in rows:
        out[r["asset_id"]] = dict(
            asset_id=r["asset_id"], has_writer=bool(r["has_writer"]),
            target_table=r["target_table"] or None, count_sql=r["count_sql"] or "",
            has_integrity=bool(r["has_integrity"]), depends_on=list(r["depends_on"] or []),
            target_floor=(str(r["target_floor"]) if r["target_floor"] is not None else None),
            catalog_status=r["catalog_status"], asset_kind=r["asset_kind"])
    if not out:
        # F7 (A_REVIEW.md): before R220 this raised on zero rows; R220 narrowed it to zero REGISTRY
        # rows, so a population filter that matched nothing (the `NOT dead_flag` NULL trap, M9)
        # measured zero assets and exited 0 — a clean-looking census of nothing. An empty active
        # population is never a clean result: it is UNKNOWN (exit 4), with both figures stated.
        raise Unknown(f"zero active {cfg['prefix']}* rows (layer='{cfg['registry_layer']}') in asset_registry "
                      f"({total} registry row(s) for this layer) — an empty population is not a clean census; "
                      "check the population filter")
    population = dict(registry_total=total, active=len(out), excluded_inactive=excluded)
    return out, population


def live_counts(reg: dict, chart_id: str | None = None,
                view_counts: dict[str, str] | None = None) -> tuple[dict[str, int | None], dict[str, str]]:
    """Each asset's OWN count_sql — the cockpit instrument, not a table count.

    F2 (A_REVIEW.md, Lane A gate REJECT): a `count_sql` that RAISES (statement timeout, missing
    relation) must be distinguishable from an asset that simply HAS no `count_sql` at all — both
    used to collapse to `out[aid] = None`, and `measure()` then wrote `Build.completion = N/A "no
    count_sql"` for a query that in fact errored. N/A is CLOSABLE; a live demonstration
    (bg_ephemeris) closed the gap on a query that never returned a clean answer. Returns
    `(counts, errored)`: `errored[aid]` is set only when that asset's own `count_sql` was
    non-empty and its query raised `Unknown` — never for a genuinely absent `count_sql`.

    R231: a chart-scoped `count_sql` (`$1`) is bound to `chart_id` (default `CHART_ID`, the
    canonical chart) before it runs; one that cannot be bound is recorded in `errored` with the
    reason, never run and never read as absent."""
    chart_id = CHART_ID if chart_id is None else chart_id
    out: dict[str, int | None] = {}
    errored: dict[str, str] = {}
    parts, ids, bound = [], [], {}
    for aid, r in reg.items():
        q = " ".join(re.sub(r"--[^\n]*", "", r["count_sql"]).replace("\n", " ").rstrip(" ;").split())
        if view_counts and aid in view_counts:
            q = view_counts[aid]       # R46: the census's own count of the view (see _view_count_sql)
        if not q:
            out[aid] = None
            if r["count_sql"].strip():                     # R222: comments only is not "no count_sql"
                errored[aid] = "count_sql is empty once its comments are stripped — nothing to run"
            continue
        try:
            q = _bind_chart(q, chart_id)
        except Unknown as exc:
            out[aid] = None
            errored[aid] = str(exc)
            continue
        bound[aid] = q
        parts.append(f"SELECT '{aid}' a,({q})::text n")
        ids.append(aid)
    if not parts:
        return out, errored
    def _take(aid: str, v: str | None) -> None:
        # R222 / N1 (A_REVIEW2 G2): a count_sql that RAN but returned NULL or a non-integer used to
        # map to `None` with no error recorded — indistinguishable from an asset with no count_sql,
        # so measure() read the closable N/A "no count_sql" (false text; one live ledger-copy run
        # closed bg_ontology's gap on `SELECT NULL::bigint`). It is recorded as errored, with what
        # the query actually returned.
        if v is not None and v.strip().lstrip("-").isdigit():
            out[aid] = int(v)
        else:
            out[aid] = None
            errored[aid] = (f"count_sql returned {'NULL' if not (v or '').strip() else repr(v)}, "
                            "not an integer count")

    try:
        for a, n in psql(" UNION ALL ".join(parts)):
            _take(a, n)
    except Unknown:
        for aid in ids:                                    # one bad count_sql must not blind the rest
            q = bound[aid]
            try:
                _take(aid, scalar(f"SELECT ({q})::text"))
            except Unknown as exc:
                out[aid] = None
                errored[aid] = str(exc)
    return out, errored


def _asset_scope(prefix: str, ids=None, col: str = "asset_id") -> str:
    """R224: the per-layer reads select the MEASURED population (`ids`, from `registry()`, scoped by
    `asset_registry.layer`), not the id prefix — so an active asset outside the prefix convention
    (`lel_events`) gets its build record and history read like any other. `ids=None` keeps the
    prefix form for callers that have no population in hand."""
    if ids is None:
        return f"{col} LIKE '{prefix}%'"
    lit = ", ".join("'" + str(i).replace("'", "''") + "'" for i in ids)
    return f"{col} IN ({lit})" if lit else "FALSE"


def throughput(prefix: str, ids=None, with_duration: bool = False) -> dict[str, dict[str, dict]]:
    """asset_id -> {chart_id ('' for a global row) -> build record}.

    R231: `asset_throughput` holds one row per (chart_id, asset_id). The pre-R231 read keyed a dict
    by asset_id alone, so whichever chart's row came last silently became "the" build record — a
    count bound to one chart compared against another chart's rows_written. Rows are now kept per
    chart and `_build_record()` picks the one matching the count's own scope.

    R44 (handverify L1/L2/L4/L5): the record must be the LATEST row for its (asset, chart), chosen on
    a stated key — never "whichever row the unordered read returned last". The read had no ORDER BY
    and a second row for the same key silently overwrote the first. Uniqueness per (chart, asset) is
    today enforced only by two partial unique indexes (`asset_throughput_per_chart_idx`,
    `asset_throughput_global_idx`) that this script never checks, so the selection is made here,
    independent of row order: the greatest (last_built_at, last_measured_at), NULLs lowest. Two rows
    that tie on that key are not silently resolved — the record is marked `ambiguous` and
    Build.completion reads ERRORED (the latest cannot be determined; nothing opens or closes)."""
    rows = psql("SELECT asset_id, coalesce(state,''), coalesce(rows_written::text,''), "
                "coalesce(round(rows_per_second)::text,''), coalesce(last_built_at::date::text,''), "
                "coalesce(chart_id::text,''), "
                "coalesce(extract(epoch FROM last_built_at)::text,''), "
                "coalesce(extract(epoch FROM last_measured_at)::text,''), "
                # D6 item 2: the duration column is named ONLY when the instrument (migration 1094)
                # was feature-detected present — never a query that fails on its absence.
                + ("coalesce(duration_seconds::text,'') " if with_duration else "'' ")
                + f"FROM asset_throughput WHERE {_asset_scope(prefix, ids)} "
                "ORDER BY asset_id, chart_id, last_built_at DESC NULLS LAST, last_measured_at DESC NULLS LAST")
    out: dict[str, dict[str, dict]] = {}
    for r in ((x + [""] * 9)[:9] for x in rows):
        rec = dict(state=r[1], rows_written=r[2], rps=r[3], last_built=r[4], n_rows=1, ambiguous=False,
                   _key=(_epoch(r[6]), _epoch(r[7])), built_epoch=r[6],
                   duration=(float(r[8]) if r[8].strip() else None))
        cur = out.setdefault(r[0], {}).get(r[5])
        if cur is None:
            out[r[0]][r[5]] = rec
            continue
        n = cur["n_rows"] + 1
        if rec["_key"] > cur["_key"]:
            rec.update(n_rows=n, ambiguous=False)
            out[r[0]][r[5]] = rec
        else:
            cur["n_rows"] = n
            if rec["_key"] == cur["_key"]:
                cur["ambiguous"] = True
    return out


def _epoch(v: str) -> float:
    """An `extract(epoch …)` text as a sort key; NULL (empty) sorts lowest."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("-inf")


def _build_record(rows_by_chart: dict, chart_scoped: bool, chart_id: str) -> tuple[dict, str]:
    """R231: the build record that matches the live count's scope, and a label naming it.
    Chart-scoped count -> that chart's row; global count -> the global (chart_id NULL) row, else the
    bound chart's row (a global table built per chart), said so in the label."""
    short = chart_id[:8]
    if chart_scoped:
        return rows_by_chart.get(chart_id, {}), f"chart {short}"
    if "" in rows_by_chart:
        return rows_by_chart[""], "global"
    return rows_by_chart.get(chart_id, {}), f"chart {short} (global count_sql; no global build row)"


def catalog(tables: list[str]) -> dict:
    """One round trip each for existence, columns and declared keys — not one per asset.

    The first run made roughly 240 psql invocations for 40 assets and took minutes; each pays process
    start plus connection. Three batched reads replace them."""
    t = [x for x in {x for x in tables if x}]
    if not t:
        return dict(exists=set(), cols={}, keys={})
    lit = ", ".join("'" + x.replace("'", "''") + "'" for x in t)
    exists = {r[0] for r in psql(f"SELECT table_name FROM information_schema.tables "
                                 f"WHERE table_schema='public' AND table_name IN ({lit})")}
    cols: dict[str, list[str]] = {}
    for tn, cn in psql("SELECT table_name, column_name FROM information_schema.columns "
                       f"WHERE table_schema='public' AND table_name IN ({lit}) "
                       "ORDER BY table_name, ordinal_position"):
        cols.setdefault(tn, []).append(cn)
    keys: dict[str, list[list[str]]] = {}
    for tn, defn in psql("SELECT c.relname, pg_get_constraintdef(x.oid) FROM pg_constraint x "
                         "JOIN pg_class c ON c.oid=x.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                         f"WHERE n.nspname='public' AND x.contype IN ('u','p') AND c.relname IN ({lit})"):
        m = re.search(r"\((.*?)\)", defn)
        if m:
            keys.setdefault(tn, []).append([c.strip().strip('"') for c in m.group(1).split(",")])
    # R46: which targets are VIEWS (or materialized views) — a view is counted by the view itself.
    views = {r[0] for r in psql("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                                f"WHERE n.nspname='public' AND c.relkind IN ('v','m') AND c.relname IN ({lit})")}
    # E6 packet (c): column data types and non-NULL defaults (Narr.agree / Null.schema_default). `cols` is unchanged;
    # a failed read leaves them None (unknown), it never aborts the layer.
    types: dict | None = {}
    defaults: dict | None = {}
    try:
        for tn, cn, dt_, dflt in psql("SELECT table_name, column_name, data_type, coalesce(replace(column_default, E'\\n', ' '), '') "
                                      f"FROM information_schema.columns WHERE table_schema='public' AND table_name IN ({lit}) "
                                      "ORDER BY table_name, ordinal_position"):
            types.setdefault(tn, {})[cn] = dt_
            if dflt:
                defaults.setdefault(tn, {})[cn] = dflt
    except Unknown:
        types = defaults = None
    return dict(exists=exists | views, cols=cols, keys=keys, views=views, types=types, defaults=defaults)


def build_history(prefix: str, ids=None) -> dict:
    """What the orchestrator ACTUALLY did, from build_runs / build_run_assets.

    The static checks say an asset *should* be dispatchable. Only this says whether it ever was, and what
    happened. Native context (2026-09-26): a global build skips L0 and walks L1->L5, so an L0 asset is
    only ever exercised by a layer- or asset-scope run — measured here rather than assumed.

    C1 (W2-1_REVIEW §2 A8): a `build_run_assets` ROW is not an EXECUTION. The engine inserts every
    planned asset as `queued` and sets `started_at` only where an attempt is started in state
    'building': `asset_runner.py:1403` (the orchestrator's 'building' transition) and
    `run_heavy_writer_standalone.py:137` (the standalone heavy-writer runner, same meaning). "Executed"
    below therefore means STARTED — dispatched past the building flip — which includes skip_no_delta,
    probe-green and pre-writer-error attempts, not only writer runs. Rows that never reach it keep
    `started_at` NULL whatever their final state: `queued` leftovers in finished runs, `aborted` rows
    the runner's preflight/guardian terminalised straight from `queued` (runner.py
    `_terminalize_preflight_failure`), and `error` rows written by `_mark_asset_blocked` ("BLOCKED: …
    The asset is NOT executed"). Measured 2026-09-27: queued 1 465 (0 started), aborted 649 (8
    started), error 1 515 (319 started), complete 3 133 (3 133 started). So the executed set is
    `started_at IS NOT NULL`, not a list of states — a state list ({complete, error, aborted}) would
    count 1 837 never-started rows as runs. `executed` counts those rows; `runs` stays the raw row
    count and is reported beside it.

    R233 (F-C4, W2-1 C4): `error` is free text and Python tracebacks carry newlines. `psql()` splits
    its output on newlines, so a raw `left(a.error,200)` split ONE row into several: the row's
    started flag landed on a fragment line (executed undercounted — ph_sodhana 39 against 41 started)
    and traceback fragments became phantom per-asset keys. The error text is flattened in SQL before
    it reaches the line-oriented read: newline, carriage return and the field separator (chr(31))
    become spaces, THEN it is truncated — so one attempt is always exactly one line."""
    per: dict[str, dict] = {}
    rows = psql("SELECT a.asset_id, r.scope, a.state, coalesce(a.disposition,''), "
                "coalesce(r.created_at::date::text,''), "
                "coalesce(left(translate(a.error, E'\\n\\r' || chr(31), '   '),200),''), "
                "(a.started_at IS NOT NULL)::text "
                "FROM build_run_assets a JOIN build_runs r ON r.id=a.run_id "
                f"WHERE {_asset_scope(prefix, ids, 'a.asset_id')} "
                # R49: a TOTAL order — (asset_id, run_id) is build_run_assets' primary key, so rows of
                # runs created at the same instant (12 such pairs live, 2026-09-27) no longer come back
                # in an arbitrary order; "last" below is the latest attempt, deterministically.
                "ORDER BY a.asset_id, r.created_at, a.run_id")
    # R50 (L1 handverify: ga_dashas "108 run(s)" against 107 rows): every attempt must parse into
    # EXACTLY the seven selected fields. The read used to pad a short line (`(x + [""] * 7)[:7]`) and
    # count it as a run under whatever its first field held — so a split error fragment whose last
    # line was an asset id would add a phantom run to that REAL asset. R233 removed the known source
    # of split lines; a line of the wrong shape now fails the read (fail-closed), never counted.
    bad = [x for x in rows if len(x) != 7]
    if bad:
        raise Unknown(f"build_history: {len(bad)} line(s) did not parse into the 7 selected fields "
                      f"(first: {bad[0][:3]!r}) — the attempt tallies would be wrong; not counted")
    for aid, scope, state, disp, when, err, started in rows:
        d = per.setdefault(aid, dict(runs=0, error=0, aborted=0, complete=0, queued=0, skipped=0,
                                     blocked=0, scopes=set(), last_state="", last_when="",
                                     last_disposition="", sample_error="", sample_blocked="",
                                     executed=0, executed_scopes=set(), last_executed_when="",
                                     states={}))
        d["runs"] += 1
        d[state] = d.get(state, 0) + 1
        d["states"][state] = d["states"].get(state, 0) + 1
        if started in ("t", "true"):
            d["executed"] += 1
            d["executed_scopes"].add(scope)
            d["last_executed_when"] = when
        if disp == "skip_no_delta":
            d["skipped"] += 1
        # Packet B1: 'blocked_dependency' (migration 1095) marks a row whose writer never
        # ran because an upstream dependency failed/was blocked in the SAME run — a
        # cascade CONSEQUENCE, not its own root cause. Tracked separately from the plain
        # `error` tally so grading below can count "one cause, N blocked" instead of
        # grading a chart FAIL/PARTIAL purely from downstream cascade noise
        # (B1_before_20260926T173931Z.json §4 — asset_census was the worst offender:
        # it already read `disposition` for skip_no_delta but never checked this value).
        if state == "error" and disp == "blocked_dependency":
            d["blocked"] += 1
            if err and not d["sample_blocked"]:
                d["sample_blocked"] = err
        d["scopes"].add(scope)
        d["last_state"], d["last_when"], d["last_disposition"] = state, when, disp
        if state == "error" and disp != "blocked_dependency" and err:
            # R49 (L3 handverify ka_avadhi, ka_kshetra): the quoted error is the LATEST one, dated —
            # the read is in ascending attempt order, so each later error replaces the earlier. It
            # used to keep the FIRST error ever recorded ("not d['sample_error']"), so a FAIL reading
            # "most recent run error" quoted a months-old error the asset had long since moved past.
            d["sample_error"], d["sample_error_when"] = err, when
    glob = int(scalar("SELECT count(*)::text FROM build_runs WHERE scope='global'") or 0)
    glob_l0 = int(scalar("SELECT count(*)::text FROM build_runs r JOIN build_run_assets a ON a.run_id=r.id "
                         f"WHERE r.scope='global' AND {_asset_scope(prefix, ids, 'a.asset_id')}") or 0)
    # R45: the chart-agnostic `lit` set (asset_ids lit on ANY chart) that Build.dep_liveness read is
    # gone — liveness is now read per dependency at the census's chart scope (`_grade_dep_liveness`).
    return dict(per=per, global_runs=glob, global_with_layer=glob_l0)


def _cascade_skip_note(rec_state: str, h: dict | None) -> str:
    """Suvarna Track I-3: when an asset's `asset_throughput` record reads 'error' only because the frozen
    runner's `_mark_asset_blocked` wrote a cascade skip there (it records `state='error'` for a consumer
    whose upstream did not complete), say so in Build.completion's measured text. The verdict is NOT
    changed here — a skipped consumer genuinely has no completed build record — only mis-attribution is
    removed: the test for "cascade" is the structural `disposition='blocked_dependency'` on the latest
    build_run_assets attempt (build_history's last_*), never the BLOCKED message text. Empty for a
    genuine error, a non-'error' record, or no history. Note: build_history is not chart-scoped, so this
    reads the latest attempt on any chart, said so in the note."""
    if rec_state != "error" or not h:
        return ""
    if h.get("last_state") == "error" and h.get("last_disposition") == "blocked_dependency":
        return ("; the throughput 'error' may be a cascade skip, not this asset's own failure: its latest recorded "
                f"build_run_assets attempt ({h.get('last_when') or 'undated'}, any chart) is blocked_dependency — an "
                "upstream did not complete, so the writer never ran on that attempt")
    return ""


def latest_attempts(ids) -> tuple[dict[str, dict[str, dict]], float | None]:
    """D6 item 2 (R55, with R44/R45/R49): the latest STARTED build_run_assets attempt per
    (asset, run chart) — `{asset_id: {chart_id: attempt}}` — plus the start of the disposition era.

    Measurement identity is (asset, chart scope, latest attempt). "Attempt" means STARTED (C1: a
    `queued` leftover or an unstarted BLOCKED/aborted row never executed). Order is total:
    (created_at, run_id) — run_id completes the primary key (R49). Each attempt carries
    `ended_epoch` (the link to the build record, below), `created_epoch`, and `receipt`: whether an
    `asset_provenance_receipts` row names this run as its build_id — the probe-green evidence (the
    engine's `_mark_probe_green` writes `complete` with NO disposition and persists a receipt with
    build_id = run_id; it never writes a `probe_green` disposition, wave-1 F11).

    `era` is the epoch of the first attempt the engine marked `disposition='build'` (2026-09-04 live).
    From then on every writer completion records 'build'; BEFORE it, completions carried no
    disposition at all, so "complete + no disposition + a receipt" there may be a real writer build
    whose receipt survived (2 such latest attempts live, 2026-09-27) — never a probe-green."""
    if not ids:
        return {}, None
    lit = ", ".join("'" + str(i).replace("'", "''") + "'" for i in ids)
    rows = psql("SELECT DISTINCT ON (a.asset_id, r.chart_id) a.asset_id, r.chart_id::text, a.run_id::text, "
                "a.state, coalesce(a.disposition,''), coalesce(extract(epoch FROM a.ended_at)::text,''), "
                "extract(epoch FROM r.created_at)::text, r.created_at::date::text, "
                "(EXISTS (SELECT 1 FROM asset_provenance_receipts p WHERE p.build_id = a.run_id "
                "AND p.asset_id = a.asset_id))::text "
                "FROM build_run_assets a JOIN build_runs r ON r.id = a.run_id "
                f"WHERE a.started_at IS NOT NULL AND a.asset_id IN ({lit}) "
                "ORDER BY a.asset_id, r.chart_id, r.created_at DESC, a.run_id DESC")
    out: dict[str, dict[str, dict]] = {}
    for r in ((x + [""] * 9)[:9] for x in rows):
        out.setdefault(r[0], {})[r[1]] = dict(run_id=r[2], state=r[3], disposition=r[4], ended_epoch=r[5],
                                              created_epoch=_epoch(r[6]), when=r[7],
                                              receipt=(r[8] in ("t", "true")))
    era = scalar("SELECT extract(epoch FROM min(r.created_at))::text FROM build_run_assets a "
                 "JOIN build_runs r ON r.id = a.run_id WHERE a.disposition = 'build'")
    return out, (_epoch(era) if era else None)


def _grade_build_history(h: dict) -> dict:
    """Grade one asset's Build.history verdict from its build_history() per-asset dict `h`.

    Extracted as its own pure function (Packet B1) so this grading arithmetic is
    unit-testable directly against a hand-built `h`, without mocking psql/scalar for
    the whole measure() pipeline.

    Packet B1: a cascade-blocked row (disposition='blocked_dependency', migration 1095)
    is a CONSEQUENCE, never its own cause — it must not by itself grade a chart
    FAIL/PARTIAL. Before this fix, asset_census already read `disposition` (for
    skip_no_delta) but never checked this value at all — a chart whose every build
    blemish was downstream cascade from someone else's failure was graded exactly as
    if it had real defects of its own (B1_before_20260926T173931Z.json §4, the packet's
    most consequential surface: a governance signal, not just a UI cosmetic).

    `genuine_error` excludes blocked rows from the count this grading acts on;
    `last_run_was_blocked_only` excludes a purely-cascade most-recent-run from the
    "most recent run failed" FAIL trigger specifically. `h['blocked']` is still
    surfaced in every branch's `measured` text — never silently dropped (§N.6: count
    it, don't hide it; a chart with genuinely zero non-cascade defects grades PASS,
    not NA, so the blocked count doesn't vanish from the report).
    """
    genuine_error = h["error"] - h["blocked"]
    bad = genuine_error + h["aborted"]
    # R49: the quoted error is dated — it is the latest non-cascade error, not necessarily the last
    # run's (the last run may have completed, or ended with no error text).
    se = (f"latest error ({h['sample_error_when']}): {h['sample_error']}"
          if h.get("sample_error_when") and h.get("sample_error") else h.get("sample_error", ""))
    last_run_was_blocked_only = (
        h["last_state"] == "error" and h["last_disposition"] == "blocked_dependency"
    )
    if h["last_state"] in ("error", "aborted") and not last_run_was_blocked_only:
        return dict(v=FAIL, measured=f"most recent run {h['last_state']} ({h['last_when']}); {genuine_error} error(s), {h['aborted']} abort(s), {h['blocked']} blocked_dependency (cascade, not counted as failure). {se}")
    if bad:
        return dict(v=PARTIAL, measured=f"latest run complete, but {genuine_error} error(s) and {h['aborted']} abort(s) on record ({h['blocked']} additional blocked_dependency row(s) excluded as cascade-only). {se}")
    if h["blocked"]:
        # C-4 (review B1_review_20260926T182200Z.md, §N.8): PASS must require at
        # least one EARNED completion, not merely "zero genuine errors". Without
        # this guard, an asset that has NEVER once completed a build — every
        # attempt cascade-blocked, none of them its own fault — would grade PASS
        # from an all-cascade history alone: a green signal with no detector
        # behind the claim "this asset builds successfully" (the exact §N.8
        # defect class). Measured against live production at review time: 0 of
        # 124 assets currently hit this branch (6 FAIL->FAIL, 7 FAIL->PARTIAL, 89
        # PARTIAL->PARTIAL, 22 PASS->PASS, zero flips to PASS) — latent, not live,
        # but the path exists and would fire the moment a new asset is added
        # downstream of a chronically-failing root.
        if h["complete"] == 0:
            return dict(v=PARTIAL, measured=f"0 complete — this asset has NEVER once finished a build; {h['blocked']} blocked_dependency row(s) were all downstream cascade ({h['sample_blocked']}), not a defect of this asset, but a history with zero completions cannot grade PASS on the strength of 'no genuine error' alone; {h['skipped']} skip_no_delta")
        return dict(v=PASS, measured=f"{h['complete']} complete, no genuine error or abort; {h['blocked']} blocked_dependency row(s) were all downstream cascade from an upstream failure, not a defect of this asset ({h['sample_blocked']}); {h['skipped']} skip_no_delta (healthy)")
    if h["complete"] == 0:
        # C1 (W2-1_REVIEW §2 A3/A8): zero completions and zero errors/aborts means no attempt ever
        # reached an outcome (e.g. only `queued` rows left in finished runs). "No error" there is the
        # absence of a measurement, not a clean history — PASS would close a gap on nothing, and the
        # delegating N/A would too. NO_DETECTOR (non-closable, opens a gap) with the reason; the
        # missing execution itself is Build.exercised's FAIL.
        return dict(v=NO_DET, measured=f"NO_DETECTOR — 0 complete and no error or abort across {h['runs']} "
                                       f"build_run_assets row(s) (states: {h.get('states') or 'n/a'}): no "
                                       "attempt reached an outcome to grade")
    return dict(v=PASS, measured=f"{h['complete']} complete, no error or abort; {h['skipped']} skip_no_delta (healthy)")


def duration_instrument_present() -> bool | None:
    """D6 item 1 (feature detection): does `asset_throughput.duration_seconds` exist yet
    (migration 1094)? Returns None (not False) when the check itself cannot run — that is
    "instrument unreachable", a distinct NO_DETECTOR reason from "instrument absent".

    F11 (A_REVIEW.md, tested against the engine at 8edba0533): schema-qualified exactly as the
    engine's own `_duration_columns_present` is (gate review R-7 there) — a same-named table in
    another schema must never make the instrument read as present in `public`."""
    try:
        return (scalar("SELECT (EXISTS(SELECT 1 FROM information_schema.columns "
                       "WHERE table_schema='public' AND table_name='asset_throughput' "
                       "AND column_name='duration_seconds'))::text")
               or "f") in ("t", "true")
    except Unknown:
        return None


def _grade_earn_cost(attempt: dict | None, instrument_present: bool | None, baseline: dict | None,
                      attempt_linkage_wired: bool = False) -> tuple[dict, dict]:
    """D6 (DECISIONS_RECOMMENDATIONS_v2_0.md D6, R55 re-specified): grade `Earn.build_record` and
    `Cost.baseline` — two SEPARATE measurements, neither certifying the whole Earn gate, Cost not
    one of the nine gates at all (tier 4 §1's build-cost baseline only).

    Extracted as a pure function (same discipline as `_grade_build_history`, Packet B1) so every
    branch is unit-testable against a hand-built `attempt`/`baseline`, without a live
    `asset_throughput.duration_seconds` column to test against — which does not exist in this
    environment (migration 1094 not applied, confirmed 2026-09-27 in both production and the
    nikasha_sandbox proof DB) or in production, so this function is EXERCISED here only through
    its own test suite.

    F1 (Lane A gate review, `nikasha_test/wave1/A_REVIEW.md`): `measure()` does NOT query
    `build_run_assets` for a real attempt today — that wiring is R42–R56, a separate lane this
    packet stops short of (§A-4). So `measure()` always calls this with `attempt=None` AND
    `attempt_linkage_wired=False`, regardless of whether the instrument (migration 1094) is
    present. This is deliberately NOT the same claim as "genuinely never attempted": the fixed
    call site's earlier docstring said this "will grade for real the moment migration 1094 lands,
    without any further code change" — that was false. Grading for real needs the attempt query
    (R42–R56) to land too; until then, an instrument-present-but-unwired run must read
    `NO_DETECTOR — attempt linkage not wired`, not the closable `N/A "never attempted"` a genuine
    no-attempt-row case would use — the latter would falsely CLOSE every `Earn.build_record` gap
    for every asset that was in fact built, the instant the column exists.

    R225 (A_REVIEW2 G1): `attempt_linkage_wired` DEFAULTS TO False — the safe value. With the old
    default (True) a call site that merely omitted the argument would read `attempt=None` as
    "confirmed never attempted" and grade the closable N/A the moment migration 1094 lands. Only a
    caller that has genuinely queried build_run_assets may pass True.

    `attempt` is the latest build_run_assets row for (asset, chart scope), or None if the asset
    has never been attempted (only a meaningful "None" when `attempt_linkage_wired` is True — see
    above). Expected keys: `state` ("complete"/"error"/"aborted"/"queued"),
    `disposition` ("skip_no_delta"/"probe_green"/"" ), `reached_completion_write` (bool — did
    execution get far enough that a duration WOULD have been recorded if the instrument were
    working), `duration_seconds` (float/None), `rows_written` (int/None), `is_legacy_telemetry`
    (bool — this attempt's writer is on the pre-1094 `_telemetry` path R34 left as a residual; the
    ONLY currently-known cause of a completion write with no duration. Unclassified so far:
    engine-side, migration-1094-dependent; no such marker exists in this environment either).
    `has_writer` — no registered writer at all (a legacy health-probe service) grades N/A, but under its own
    cause `no-registered-writer`: only a skip/probe DISPOSITION earns `healthy-non-execution`.

    `baseline`, when not None, is the most recent MEASURED completion on record for this asset at
    this scope: `{"rate": float, "attempt_id": str, "age_days": int}` — provenance, not just a number.
    """
    if instrument_present is None:
        reason = "instrument unreachable"
    elif not instrument_present:
        reason = "instrument absent (migration 1094)"
    else:
        reason = None

    if reason is not None:
        nd = dict(v=NO_DET, measured=f"NO_DETECTOR — {reason}, scoped to this run")
        return dict(nd), dict(nd)

    # From here, the instrument genuinely exists — grade Earn.build_record for the latest attempt.
    if attempt is None and not attempt_linkage_wired:
        # F1: the instrument exists but this call site never queried build_run_assets for an
        # attempt at all — `attempt=None` here means "unknown", never "confirmed absent". Reading
        # N/A would close a gap on a fact this run never actually measured.
        nd = dict(v=NO_DET, measured="NO_DETECTOR — attempt linkage not wired")
        return dict(nd), dict(nd)
    if attempt is None:
        earn = _na("never attempted — see Build.exercised", "never-attempted")
    elif attempt.get("disposition") in ("skip_no_delta", "probe_green"):
        # "healthy non-execution" is the DISPOSITION's claim (the engine skipped / probed green): only that
        # disposition earns the slug. A no-writer asset whose attempt failed is not "healthy".
        earn = _na(f"healthy non-execution ({attempt['disposition']}) — no build was due", "healthy-non-execution")
    elif not attempt.get("has_writer", True):
        earn = _na(f"no registered writer (attempt {attempt.get('state', '?')}) — no build record applies",
                   "no-registered-writer")
    elif not attempt.get("reached_completion_write", False):
        earn = _na(f"attempt {attempt.get('state','?')} before completion; see Build.history", "before-completion-write")
    elif attempt.get("duration_seconds") is not None:
        dur = attempt["duration_seconds"]
        rw = attempt.get("rows_written") or 0
        rate = (rw / dur) if dur else 0.0
        earn = dict(v=PASS, measured=f"completion write with duration={dur}s, rows_written={rw}, rate={rate} "
                                     "(a measured rate of 0.0 is a real measurement, not suppressed)")
    elif attempt.get("is_legacy_telemetry"):
        earn = dict(v=FAIL, measured="completion write reached with no duration — the legacy _telemetry "
                                     "path (R34's residual)")
    else:
        earn = dict(v=NO_DET, measured="NO_DETECTOR — unclassified NULL (completion write with no duration "
                                       "and no identified cause)")

    # Cost.baseline: independent of the latest attempt's own outcome — a healthy skip/failure
    # neither erases a prior sanctioned baseline nor creates one.
    if baseline is not None:
        cost = dict(v=PASS, measured=f"sanctioned baseline: rate={baseline['rate']} "
                                     f"(attempt {baseline['attempt_id']}, {baseline['age_days']}d old)")
    else:
        cost = dict(v=FAIL, measured="no sanctioned baseline build on record")
    return earn, cost


def _attempt_timing(by_chart: dict | None, rec: dict, rec_scope: str, chart_id: str,
                    instrument_present: bool | None, has_writer: bool, era: float | None,
                    today: dt.date | None = None) -> tuple[dict, dict]:
    """D6 item 2 — the attempt adapter: Earn.build_record / Cost.baseline attributed to the latest
    STARTED attempt at the build record's scope, then graded by the unchanged D6 classifier
    (`_grade_earn_cost`, attempt linkage genuinely wired).

    `by_chart` is `latest_attempts()` for this asset (None when the attempt read itself failed).
    Scope: a global build record (chart_id NULL) is written by a run on ANY chart, so its attempt is
    the latest across run charts; any other record is the bound chart's, so its attempt is that
    chart's latest. The link between an attempt and the build record's duration is the engine's own:
    the completion write sets `asset_throughput.last_built_at = NOW()` and `build_run_assets.ended_at
    = NOW()` with `disposition='build'` in ONE transaction, so the two are equal — true for all 64
    latest 'build' attempts live (2026-09-27). A duration counts for an attempt only if the attempt
    is 'build' AND that equality holds (skip, probe-green, error and start all refresh
    `last_built_at` without touching the duration — D6 finding 3).

    Nothing here can PASS or N/A while the instrument is absent: `_grade_earn_cost` grades
    NO_DETECTOR first. The linked attempt's identity is appended to that NO_DETECTOR as evidence."""
    atts = by_chart or {}
    if rec_scope == "global":
        att = max(atts.values(), key=lambda a: (a["created_epoch"], a["run_id"])) if atts else None
        where = "any chart (global build record)"
    else:
        att, where = atts.get(chart_id), f"chart {chart_id[:8]}"
    ident = (f"latest attempt at {where}: run {att['run_id'][:8]} {att['state']}/"
             f"{att['disposition'] or 'no disposition'} ({att['when']})" if att else f"no started attempt at {where}")
    if by_chart is None:
        ident = "the attempt read failed"

    if instrument_present is not True:
        earn, cost = _grade_earn_cost(attempt=None, instrument_present=instrument_present, baseline=None,
                                      attempt_linkage_wired=True)
        return (dict(earn, measured=f"{earn['measured']}; {ident}"),
                dict(cost, measured=f"{cost['measured']}; {ident}"))
    if by_chart is None:
        nd = dict(v=NO_DET, measured="NO_DETECTOR — the build_run_assets attempt read failed; no attempt to link")
        return dict(nd), dict(nd)
    if att is None:
        if atts:
            nd = dict(v=NO_DET, measured=f"NO_DETECTOR — {ident} ({len(atts)} run chart(s) with attempts elsewhere): "
                                         "nothing to time for this scope")
            return dict(nd), dict(nd)
        return _grade_earn_cost(attempt=None, instrument_present=True, baseline=None, attempt_linkage_wired=True)

    disp, state = att["disposition"], att["state"]
    linked = (state == "complete" and disp == "build" and bool(att["ended_epoch"])
              and att["ended_epoch"] == rec.get("built_epoch"))

    def _nd(why: str) -> tuple[dict, dict]:
        nd = dict(v=NO_DET, measured=f"NO_DETECTOR — {ident}: {why}")
        return dict(nd), dict(nd)

    if state == "complete":
        if disp == "build" and not linked:
            return _nd("a completion write, but the build record's last_built_at is not this attempt's completion "
                       "(a later write touched it); its duration cannot be attributed")
        if not disp:
            if not (att["receipt"] and era is not None and att["created_epoch"] >= era):
                return _nd("complete with no disposition and not derivable as probe-green ("
                           + ("no probe receipt names this run" if not att["receipt"] else
                              "it predates the disposition era, so a surviving receipt may be a writer build's")
                           + ") — unclassified")
            disp = "probe_green"                            # derived: complete + no disposition + receipt
        elif disp not in ("build", "skip_no_delta"):
            return _nd(f"complete with an unrecognised disposition '{disp}' — unclassified")
    elif state in ("error", "aborted"):
        if disp in ("build", "skip_no_delta", "probe_green"):
            return _nd(f"state '{state}' with disposition '{disp}' is inconsistent — unclassified")
    else:
        return _nd(f"attempt in state '{state}', no outcome to grade")

    dur = rec.get("duration") if linked else None
    rw = int(rec["rows_written"]) if str(rec.get("rows_written", "")).strip().lstrip("-").isdigit() else 0
    attempt = dict(state=state, disposition=disp, reached_completion_write=(disp == "build"),
                   duration_seconds=dur, rows_written=rw, is_legacy_telemetry=False, has_writer=has_writer)
    baseline = None
    if linked and dur is not None:
        age = ((today or dt.date.today()) - dt.date.fromisoformat(att["when"])).days if att["when"] else 0
        baseline = dict(rate=(rw / dur) if dur else 0.0, attempt_id=att["run_id"][:8], age_days=age)
    earn, cost = _grade_earn_cost(attempt=attempt, instrument_present=True, baseline=baseline,
                                  attempt_linkage_wired=True)
    if baseline is None and rec.get("duration") is not None:
        # D6 item 4: a healthy skip neither erases a prior baseline nor creates one — but a duration
        # this adapter cannot attribute to a completion attempt has no provenance, so it is not a
        # "sanctioned" baseline either, and "none on record" would be false. Unmeasured, said so.
        cost = dict(v=NO_DET, measured=f"NO_DETECTOR — a duration is on record ({rec['duration']}s) but is not "
                                       f"attributable to a completion attempt ({ident})")
    return (dict(earn, measured=f"{earn['measured']}; {ident}"), dict(cost, measured=f"{cost['measured']}; {ident}"))


def declared_keys(table: str) -> list[list[str]]:
    rows = psql("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                f"WHERE conrelid='{table}'::regclass AND contype IN ('u','p')")
    keys = []
    for (d,) in ((r[0],) for r in rows):
        m = re.search(r"\((.*?)\)", d)
        if m:
            keys.append([c.strip().strip('"') for c in m.group(1).split(",")])
    return keys


def table_exists(t: str) -> bool:
    return (scalar(f"SELECT (to_regclass('public.{t}') IS NOT NULL)::text") or "f") in ("t", "true")


def depth_census(table: str, cols: list[str]) -> dict:
    if not cols:
        return dict(columns=0, note="no columns")
    total = int(scalar(f"SELECT count(*)::text FROM {table}") or 0)
    if total == 0:
        return dict(columns=len(cols), rows=0, full=[], never=[], note="table empty")
    sel = ", ".join(f"count({c})::text" for c in cols)
    vals = psql(f"SELECT {sel} FROM {table}")[0]
    full = [c for c, v in zip(cols, vals) if int(v) == total]
    never = [c for c, v in zip(cols, vals) if int(v) == 0]
    return dict(columns=len(cols), rows=total, full=full, never=never, note="")


def alias_census(table: str, cols: list[str]) -> dict | None:
    names = set(cols)
    if ALIAS_COLUMN not in names:
        return None
    grp = "entity_class" if "entity_class" in names else "'(all)'"
    rows = psql(f"SELECT {grp}::text, count(*)::text, "
                f"count(*) FILTER (WHERE {ALIAS_COLUMN} IS NULL OR cardinality({ALIAS_COLUMN})=0)::text "
                f"FROM {table} GROUP BY 1 ORDER BY 1")
    return {r[0]: dict(rows=int(r[1]), no_alias=int(r[2])) for r in rows}


def _no_writer_scanned(aid: str, has_writer: bool, check: str) -> dict:
    """R222 / N2 (A_REVIEW2 G2): no writer file was recognised for this asset. That is a genuine
    N/A only when the registry agrees there is no writer. With `has_writer=true` the writer exists
    but its `@register` was not recognised (e.g. `@register(ASSET_ID)`, R43), so the scan never ran:
    NO_DETECTOR, never the closable N/A (one live ledger-copy run closed bg_reference-Idem.pattern
    on exactly this; live today on L3/L4/L5, where 13 writer-backed assets are unrecognised)."""
    if not has_writer:
        return _na("no writer, and the registry agrees (has_writer=false) — nothing to scan", "no-writer-registry-agrees")
    return dict(v=NO_DET, measured=f"NO_DETECTOR — registry says has_writer=true but no @register('{aid}') "
                                   f"was recognised in writers/; {check} was never scanned (see Build.registered)")


def _measure_contract(aid: str, files: list[str], has_writer: bool) -> dict:
    """R41 fault isolation for Build.contract, extracted as its own pure-ish function (F3,
    A_REVIEW.md: the inline try/except could only be proven by grepping measure()'s source text,
    which survives a mutation that makes the guard re-raise instead of catching. Extracting it
    lets a test call it directly with `contract_scan` monkeypatched to raise, and assert the
    RETURN VALUE is ERRORED — a mutation that removes or breaks the try/except now fails that
    assertion instead of surviving on source text alone)."""
    if not files:
        return _no_writer_scanned(aid, has_writer, "the contract")
    try:
        v, notes = contract_scan(aid, files)
        return dict(v=v, measured="; ".join(notes) or "conformant")
    except Unknown as exc:
        return dict(v=ERRORED, measured=f"check errored: {exc}")


def _measure_idem(aid: str, files: list[str], convention: str, has_writer: bool, targets=()) -> dict:
    """R41 fault isolation for Idem.pattern — same discipline as `_measure_contract`. `targets`
    (C-KSHETRA): the asset's own tables — target_table ∪ count_sql tables — a counted DELETE must name."""
    if not files:
        return _no_writer_scanned(aid, has_writer, "the idempotency pattern")
    try:
        v, notes = idem_scan(aid, files, convention, targets)
        return dict(v=v, measured="; ".join(notes))
    except Unknown as exc:
        return dict(v=ERRORED, measured=f"check errored: {exc}")


def target_owners() -> dict[str, list[str]]:
    """R53: table -> the active assets (registry-wide, every layer) that declare it as target_table."""
    out: dict[str, list[str]] = {}
    for t, aid in psql("SELECT target_table, asset_id FROM asset_registry WHERE target_table IS NOT NULL "
                       "AND is_active AND NOT coalesce(dead_flag,false) ORDER BY 1, 2"):
        out.setdefault(t, []).append(aid)
    return out


def dependency_graph() -> dict[str, list[str]]:
    """R21: every ACTIVE asset's declared `depends_on`, registry-wide (all six layers), in one read —
    the blocking radius crosses layers (an L0 table blocks L1–L5 builders)."""
    blob = scalar("SELECT coalesce(json_object_agg(asset_id, coalesce(to_json(depends_on), '[]'::json))::text, '{}') "
                  "FROM asset_registry WHERE is_active AND NOT coalesce(dead_flag,false)")
    return {k: [str(d) for d in (v or [])] for k, v in json.loads(blob or "{}").items()}


def blocking_radius(graph: dict[str, list[str]]) -> dict[str, dict]:
    """R21 (triage BT05; register row R21). THE METRIC, per active asset A:

      transitive      the number of DISTINCT active assets (every layer) that depend on A through
                      `asset_registry.depends_on`, directly or through any chain — what a failing A can
                      block. Edges come only from active assets and point only at active assets (a
                      dependency on an inactive/unknown id is no edge); a cycle counts each member once
                      and never A itself.
      direct          those that declare A in their own `depends_on`.
      severity_weight 1 + transitive — the multiplier a Build gap carries: an isolated leaf weighs 1.

    A leaf and a root with the same Build verdict are the same defect with different costs; this is the
    figure that orders their repair."""
    rev: dict[str, set[str]] = {a: set() for a in graph}
    for a, deps in graph.items():
        for d in deps:
            if d in rev and d != a:
                rev[d].add(a)
    out = {}
    for a in graph:
        seen: set[str] = set()
        todo = list(rev[a])
        while todo:
            x = todo.pop()
            if x == a or x in seen:
                continue
            seen.add(x)
            todo.extend(rev[x])
        out[a] = dict(transitive=len(seen), direct=len(rev[a]), severity_weight=1 + len(seen))
    return out


# ─────────── E6 item (h): Build.dag reads-match (T4:275, check 4) ───────────
#
# T4:275: "the declared edges match what the asset actually reads". Until this block Build.dag tested RESOLVABILITY
# only (every depends_on id exists). This reads what the writer's code SELECTs — FROM / JOIN relations of every SQL
# string in the registered class's delegation scope — and compares it with the asset's DECLARED depends_on edges.
#
#   * A read of a table another asset PRODUCES (registry target_table or a table its count_sql names) with no DIRECT
#     depends_on edge to a producer is a FAIL that names the missing edge and the file:line that reads it. A shared
#     table (several producers) is covered by an edge to any one of them. An edge that is only transitively present
#     (ordering still holds through the intermediate asset) is named in the FAIL text, but it is still a missing edge:
#     T4:275 asks for the DECLARED edges to match.
#   * "Reads nothing undeclared" is a PASS only when the parse is demonstrably complete (`reads_scan()['incomplete']`
#     empty): every SQL string parsed, no table named dynamically, every execute() argument traced to a literal, no SQL
#     one hop past the scan limit. Otherwise NO_DETECTOR — never a PASS by the absence of a parse (CLAUDE.md N.8).
#   * Static SQL only. A read through a database view or function is not followed (a view over an asset's table is a
#     read of a relation no asset produces, so it is invisible to the ownership map); the PASS text says so.

# SS ruling 2026-10-01 (alignment with pipeline/orchestrator/dag_edge_guard.py, whose lists this module IMPORTS, never copies):
#   * L0 BEDROCK reads (table names with the guard's _UNGATED_PREFIXES bg_/reference_/brahma_/sutravali_/classical_, _UNGATED_EXACT
#     ephemeris_daily, _EXTERNAL_TABLES life_event*) need no declared edge: not a missing-edge FAIL, recorded as `bedrock_exempt`
#     in the record. THIS IS A PROVISIONAL INTERPRETATION OF T4 (check 4), to be confirmed at the J1 review.
#   * chart_facts (_SHARED_SOFT_TABLES, a polymorphic read whose producer cannot be named) is satisfied by ANY producer in the
#     asset's declared transitive closure (the guard's SOFT tier), recorded as `soft_satisfied`; no producer in the closure
#     keeps the FAIL.
#   * DEVIATION FROM THE GUARD (stricter, earned-signal-conservative, CLAUDE.md N.8): the guard exempts by table NAME alone. Here
#     a table is exempt only when it has a bedrock NAME AND every producer that owns it in the registry is an L0 asset (bg_*); a
#     bedrock-named table with any non-L0 owner (a brahma_* table owned by bo_x, a mixed bg_/bo_ owner set) is an ordinary read
#     needing an edge and its finding carries `bedrock_name_non_l0_owner`.
#   * `soft_satisfied` limit: satisfied by ANY chart_facts producer in the declared closure; fact_category is NOT matched
#     (record: fact_category_matched=False), so it does not prove the READ category is produced upstream.
#   * The guard counts only per_chart producers: global NON-prefixed L0 tables (vidhi_floor_items, vidhi_intent_floors,
#     vidhi_primitives) would FAIL here if a writer read them (they match no ungated prefix and no per_chart owner rule); none does today.
#   * Transitive invariant: for every other table the guard asks for a producer in the transitive closure; this check still
#     asks for a DIRECT edge (SS: transitive-only findings stay FAIL with `transitive_only`; Track I migration 1202 adds them).
# Recorded limits and review notes (E6 review of b24e580cc; counts at table level, 2026-10-01):
#   * Counts are quoted as: "N table-level findings = M distinct (asset, producer-set) pairs, of which B are back-reads; K of the
#     M-B missing-edge pairs are transitive (a back-read pair cannot be transitive); J assets have only transitive findings".
#     A pair can carry several tables; a shared table's producer set is one pair. (Saved censuses: 68 findings = 65 pairs,
#     3 back-read pairs; 41 of 62 missing-edge pairs transitive; 16 assets only-transitive.)
#   * One-directional: an OVER-declared edge (declared, never read) is never flagged (ka_tulana declares 3 edges, reads
#     nothing, and reads PASS). The check asks "is every read declared", not "is every edge read".
#   * Co-owner exemption: another asset registered on the SAME writer class (bg_transit_engine / bg_transit_rules) is not
#     a producer the asset must depend on.
#   * chart_facts remedy ambiguity: chart_facts has ten producing ga_* assets, so a missing edge to it reads "needs
#     ga_ayurdaya | ... (10 assets)"; any ONE edge satisfies the read. A fact_category ownership map could name the right
#     producer; this check does not.
#   * The reconstructed registry edges used offline (seed + migrations 913/1084/730/676, inactive dropped) were verified by
#     the reviewer against the live registry, read-only: md5 of the sorted depends_on of the 127 active rows =
#     045e811d55d6825cf7c7f1fda329bdc4, identical to the reconstruction.
READS_DELEGATION_HOPS = 3            # the code a rebuild runs, as far as it can be read statically; a frontier check one hop past
_EXEC_METHODS = frozenset({"execute", "executemany", "fetch", "fetchrow", "fetchval", "mogrify", "copy_expert", "query"})
# a call that is not an execute-type METHOD but takes SQL all the same (pandas `read_sql`, a `exec_sql` helper, `execute_values`):
# when NONE of its arguments is traced to literal SQL the parse is incomplete — the SQL it runs is not in the text.
_SQL_LIKE_CALLEE = re.compile(r"^(?:read_sql\w*|exec(?:ute)?(?:_\w+)?|run_sql\w*|run_query\w*|raw_sql)$", re.I)
_SQL_CTX = re.compile(r"\b(?:SELECT|UPDATE|DELETE|INSERT|WITH|MERGE)\b", re.I)
_FROM_JOIN = re.compile(r"\b(FROM|JOIN|USING)\b", re.I)
_SQL_IDENT = r'(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_$]*)'
_SQL_QNAME = re.compile(_SQL_IDENT + r"(?:\s*\.\s*" + _SQL_IDENT + r")*")
_SQL_ITEM_END = frozenset({
    "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "NATURAL", "ON", "USING", "GROUP", "ORDER", "LIMIT",
    "OFFSET", "UNION", "INTERSECT", "EXCEPT", "HAVING", "WINDOW", "FOR", "RETURNING", "SET", "FETCH", "TABLESAMPLE",
    "WITH", "SELECT", "VALUES", "AS", "LATERAL", "OUTER", "WHEN", "THEN", "ELSE", "END", "AND", "OR", "NOT", "IN"})
# ONE left-to-right pass, so whichever starts first wins: a `--` inside a string literal is not a comment, and an
# apostrophe inside a comment does not open a string.
_SQL_MASK = re.compile(r"'(?:[^']|'')*'|/\*.*?\*/|--[^\n]*", re.S)
_SQL_CTE = re.compile(r"(?:\bWITH\b(?:\s+RECURSIVE)?|,)\s*(" + _SQL_IDENT + r")\s*(?:\([^()]*\))?\s+AS\s+"
                      r"(?:NOT\s+)?(?:MATERIALIZED\s*)?\(", re.I)
# a FROM that is not a relation clause: EXTRACT(field FROM x), SUBSTRING/OVERLAY/POSITION(a FROM b), TRIM([BOTH] [c] FROM x),
# and the comparison `IS [NOT] DISTINCT FROM`. The surrounding call is kept; only the keyword is dropped.
_SQL_FROM_NOT_RELATION = [
    re.compile(r"\bEXTRACT\s*\(\s*[A-Za-z_]+\s+FROM\b", re.I),
    re.compile(r"\b(?:SUBSTRING|OVERLAY|POSITION)\s*\((?:[^()]|\([^()]*\))*?\s+(?:FROM|IN)\b", re.I),
    re.compile(r"\bTRIM\s*\(\s*(?:(?:BOTH|LEADING|TRAILING)\s+)?(?:(?:[\w.]+|'')\s+)?FROM\b", re.I),
]
_SQL_IS_DISTINCT = re.compile(r"\bIS\s+(?:NOT\s+)?DISTINCT\s+FROM\b", re.I)
_SQL_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.I)


def _sql_clean(text: str) -> str:
    """The SQL with comments and string literals blanked, and every `FROM` that does not open a relation clause
    (EXTRACT / SUBSTRING / TRIM / IS DISTINCT FROM / DELETE FROM — a write target) neutralised."""
    t = _SQL_MASK.sub(lambda m: "''" if m.group(0)[0] == "'" else " ", text)
    for rx in _SQL_FROM_NOT_RELATION:
        t = rx.sub(lambda m: re.sub(r"(?:FROM|IN)$", "_", m.group(0), flags=re.I), t)
    t = _SQL_IS_DISTINCT.sub(" <> ", t)
    return _SQL_DELETE_FROM.sub("DELETE _ ", t)


def _skip_parens(t: str, i: int) -> int:
    """`t[i] == '('`: the index just past its matching ')' (end of text when unbalanced)."""
    depth = 0
    while i < len(t):
        if t[i] == "(":
            depth += 1
        elif t[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return i


def _take_relation(t: str, i: int, ctes: frozenset) -> tuple[str, str, int]:
    """One relation item at `t[i:]`: (kind, name, next index). kind: `table` | `skip` (a subquery, VALUES, function,
    CTE, foreign schema, or a token that is not a relation) | `dynamic` (the table name is not in the text)."""
    n = len(t)
    while i < n and t[i].isspace():
        i += 1
    if i >= n:
        return "dynamic", "end of the string", i
    if t[i] in "{%$:" or t.startswith("{?}", i):
        j = i
        while j < n and not t[j].isspace() and t[j] not in ",)":
            j += 1
        return "dynamic", t[i:j] or t[i], j
    while True:                                                   # LATERAL / ONLY prefixes
        m = re.match(r"(?:LATERAL|ONLY)\b\s*", t[i:], re.I)
        if not m:
            break
        i += m.end()
    if i < n and t[i] == "(":
        return "skip", "", _skip_parens(t, i)
    m = _SQL_QNAME.match(t, i)
    if not m:
        j = i
        while j < n and not t[j].isspace() and t[j] not in ",)":
            j += 1
        return "skip", "", max(j, i + 1)
    j = m.end()
    if j < n and t[j] in "{%$":                                   # `bg_{suffix}` / `t_%s`: a name assembled outside the string
        k = j
        while k < n and not t[k].isspace() and t[k] not in ",)":
            k += 1
        return "dynamic", t[i:k], k
    k = j
    while k < n and t[k].isspace():
        k += 1
    if k < n and t[k] == "(":                                     # a function call
        return "skip", "", _skip_parens(t, k)
    parts = [p.strip().strip('"') for p in re.split(r"\s*\.\s*", m.group(0))]
    name = parts[-1].lower()
    if len(parts) >= 2 and parts[-2].lower() != "public":        # pg_temp / information_schema / pg_catalog: not an asset table
        return "skip", "", j
    if name in ctes or name.upper() in _SQL_ITEM_END:
        return "skip", "", j
    return "table", name, j


def _skip_alias(t: str, i: int) -> int:
    """Past an optional `[AS] alias [(col, ...)]` after a relation item."""
    n = len(t)
    j = i
    while j < n and t[j].isspace():
        j += 1
    m = re.match(r"AS\b\s*", t[j:], re.I)
    had_as = bool(m)
    if m:
        j += m.end()
    m = re.match(_SQL_IDENT, t[j:])
    if m and (had_as or m.group(0).upper() not in _SQL_ITEM_END):
        j += m.end()
        k = j
        while k < n and t[k].isspace():
            k += 1
        if k < n and t[k] == "(":
            j = _skip_parens(t, k)
    return j


_SQL_TAIL_TOKEN = re.compile(r"\b(?:WHERE|GROUP|ORDER|LIMIT|UNION|INTERSECT|EXCEPT|HAVING|WINDOW|OFFSET|FETCH|RETURNING|JOIN|INNER|"
                             r"LEFT|RIGHT|FULL|CROSS|NATURAL)\b|[;,()\[\]]", re.I)


def _next_list_comma(t: str, i: int) -> int:
    """Index of the comma that continues a FROM list after a JOIN's ON/USING condition (`a JOIN b ON x, c`), or -1:
    the first depth-0 comma before the next clause keyword, JOIN, ';' or an unbalanced ')'."""
    depth = 0
    for m in _SQL_TAIL_TOKEN.finditer(t, i):
        tok = m.group(0)
        if tok in "([":
            depth += 1
        elif tok in ")]":
            if depth == 0:
                return -1
            depth -= 1
        elif depth == 0:
            return m.start() if tok == "," else -1
    return -1


def sql_relations(text: str) -> tuple[list[str], list[str]]:
    """The relations a SQL text READS, as (tables, dynamic): FROM / JOIN targets in order, de-duplicated, lower-cased,
    `public.` stripped. Not reads: CTE names, functions, subqueries and VALUES lists (their inner FROM/JOIN is read on
    its own), tables of any schema but `public`, the target of `DELETE FROM`, and the FROM of EXTRACT / SUBSTRING / TRIM
    / `IS DISTINCT FROM`. A relation after USING IS a read only inside a DELETE / MERGE statement (`DELETE FROM x USING y`, `MERGE ... USING y`);
    `JOIN b USING (id)` is a column list, and `ALTER ... TYPE x USING c::int` / `EXECUTE stmt USING p` are not relation clauses. `dynamic` names every relation position whose table name is not in the text (`{?}` — an
    f-string placeholder `_sql_texts` could not resolve — `%s`, `{x}`, a name cut off at the end of the string) and every
    placeholder that follows a relation where a JOIN could sit: a dynamic position is never guessed, it makes the
    caller's parse incomplete. Comma lists (`FROM a, b`, also after a JOIN's ON condition) are followed."""
    t = _sql_clean(text)
    ctes = frozenset(re.sub(r'^"|"$', "", m.group(1)).lower() for m in _SQL_CTE.finditer(t))
    tables: list[str] = []
    dynamic: list[str] = []
    for m in _FROM_JOIN.finditer(t):
        i = m.end()
        if m.group(1).upper() == "USING":
            j = i
            while j < len(t) and t[j].isspace():
                j += 1
            if j < len(t) and t[j] == "(":        # `JOIN b USING (id)`: a column list; `MERGE ... USING (SELECT ..)`: its inner FROM is read on its own
                continue
            if not re.search(r"\b(?:DELETE|MERGE)\b", t[t.rfind(";", 0, m.start()) + 1:m.start()], re.I):
                continue                          # `ALTER ... TYPE x USING c::int`, `EXECUTE stmt USING p`: not a relation clause
        while True:
            kind, name, i = _take_relation(t, i, ctes)
            if kind == "table" and name not in tables:
                tables.append(name)
            elif kind == "dynamic":
                dynamic.append(name)
            i = _skip_alias(t, i)
            j = i
            while j < len(t) and t[j].isspace():
                j += 1
            if j < len(t) and t[j] == ",":
                i = j + 1
                continue
            if m.group(1).upper() == "JOIN":
                c = _next_list_comma(t, i)
                if c >= 0:
                    i = c + 1
                    continue
            if j < len(t) and t[j] in "{%":
                dynamic.append(f"a placeholder {t[j:j + 6].split()[0]!r} follows the relation and may expand to a JOIN or another relation")
            break
    return tables, dynamic


def _walk_ctx(root: ast.AST, fn=None, cls=None):
    """(node, enclosing FunctionDef or None, enclosing ClassDef or None) for every node under `root`."""
    if isinstance(root, (ast.FunctionDef, ast.AsyncFunctionDef)):
        fn = root
    elif isinstance(root, ast.ClassDef):
        cls = root
    yield root, fn, cls
    for c in ast.iter_child_nodes(root):
        yield from _walk_ctx(c, fn, cls)


def _lit_str(n: ast.AST) -> bool:
    """A string expression whose literal parts `_sql_texts` reads: a str constant, an f-string, `a + b`, `a % b`, a
    conditional of those, or a `.format()/.strip()/…` of one. What such an expression hides (a placeholder) is caught
    where it sits at a FROM/JOIN position (`dynamic`)."""
    if isinstance(n, ast.Constant):
        return isinstance(n.value, str)
    if isinstance(n, ast.JoinedStr):
        return True
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
        return _lit_str(n.left) and (isinstance(n.op, ast.Mod) or _lit_str(n.right))
    if isinstance(n, ast.IfExp):
        return _lit_str(n.body) and _lit_str(n.orelse)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in (
            "format", "strip", "lstrip", "rstrip", "replace", "dedent", "join"):
        return _lit_str(n.func.value)
    return False


def _callers(name: str, sites: list) -> list:
    return [s for s in sites if s["callee"] == name]


def _sql_arg_traced(a: ast.AST, fn, cls, unit, sites: list, depth: int = 0, seen=None) -> bool:
    """Is the SQL argument of an execute-type call traced to literal SQL text? A literal expression, a Name whose every
    assignment in the function is one (or a module-level literal), a `self.X` whose class assigns a literal X, or a
    parameter of the enclosing function whose every in-scope caller passes a traced argument (at least one caller)."""
    if _lit_str(a):
        return True
    seen = seen or set()
    if isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) and a.value.id in ("self", "cls") and cls is not None:
        vals = [s.value for s in cls.body if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == a.attr for t in s.targets)]
        vals += [s.value for s in cls.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.target.id == a.attr and s.value is not None]
        return bool(vals) and all(_lit_str(v) for v in vals)
    if not isinstance(a, ast.Name):
        return False
    local = []
    if fn is not None:
        for x in ast.walk(fn):
            if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == a.id for t in x.targets):
                local.append(x.value)
            elif isinstance(x, ast.AnnAssign) and isinstance(x.target, ast.Name) and x.target.id == a.id and x.value is not None:
                local.append(x.value)
            elif isinstance(x, ast.AugAssign) and isinstance(x.target, ast.Name) and x.target.id == a.id:
                local.append(x.value)
    if local:
        return all(_lit_str(v) for v in local)
    top = _top_defs(unit["tree"]).get(a.id)
    if isinstance(top, ast.Assign) and _lit_str(top.value):
        return True
    imported = _import_map(unit["tree"], unit["path"].parent).get(a.id)
    if imported is not None and imported[1] is not None:         # `from .sql import READ_SQL`: the constant is read as a unit
        got = _resolve_assign(imported[0], imported[1])
        if got is not None and isinstance(got[2], ast.Assign) and _lit_str(got[2].value):
            return True
    if fn is None or depth >= 3:
        return False
    args = fn.args
    pos = [p.arg for p in args.posonlyargs + args.args]
    kwonly = [p.arg for p in args.kwonlyargs]
    if a.id not in pos and a.id not in kwonly:
        return False
    key = (id(fn), a.id)
    if key in seen:
        return False
    seen = seen | {key}
    calls = _callers(fn.name, sites)
    if not calls:
        return False
    is_method = bool(pos) and pos[0] in ("self", "cls")
    for s in calls:
        call = s["call"]
        arg = None
        if a.id in pos:
            idx = pos.index(a.id) - (1 if is_method and isinstance(call.func, ast.Attribute) else 0)
            if 0 <= idx < len(call.args):
                arg = call.args[idx]
        if arg is None:
            arg = next((k.value for k in call.keywords if k.arg == a.id), None)
        if arg is None or not _sql_arg_traced(arg, s["fn"], s["cls"], s["unit"], sites, depth + 1, seen):
            return False
    return True


def _resolve_assign(path: Path, name: str):
    """A module-level `NAME = <expr>` (an imported SQL constant) that `_resolve_def` deliberately skips: (path, tree,
    assign node) following package re-exports, or None."""
    for _ in range(4):
        tree = _parse(path)
        d = _top_defs(tree).get(name)
        if isinstance(d, (ast.Assign, ast.AnnAssign)):
            return path, tree, d
        nxt = _import_map(tree, path.parent).get(name)
        if not nxt or nxt[1] is None:
            return None
        path, name = nxt
    return None


def _third_party_binding(path: Path, name: str) -> bool:
    """Is `name` bound in the module at `path` by an import that does NOT resolve to first-party code (a re-exported
    third-party module such as `from jhora.panchanga import drik`)? Following first-party re-exports, at most 3."""
    for _ in range(4):
        tree = _parse(path)
        bound = None
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and any((a.asname or a.name) == name for a in n.names):
                bound = n
            elif isinstance(n, ast.Import) and any((a.asname or a.name.split(".")[0]) == name for a in n.names):
                bound = n
        if bound is None:
            return False
        nxt = _import_map(tree, path.parent).get(name)
        if not nxt:
            return True
        if nxt[1] is None:
            return False
        path, name = nxt
    return False


def _constant_units(units: list[dict], hops: int) -> tuple[list[dict], list[str]]:
    """Imported module-level constants the scope uses (`from .sql import READ_SQL`): `_delegation_scope` follows
    definitions only, so their SQL would be missed silently. Returns (pseudo-units holding the assignment, reasons) — a
    used first-party name that resolves to neither a definition nor an assignment is a reason (not silently skipped)."""
    out, why, seen = [], [], set()
    for u in units:
        for tp, attr in _external_refs(u["nodes"], _import_map(u["tree"], u["path"].parent)):
            if _resolve_def(tp, attr) is not None:
                continue
            a = _resolve_assign(tp, attr)
            if a is None and _third_party_binding(tp, attr):
                continue            # a shim that re-exports a third-party module (`pyjhora_adapter/_jhora.py`): no SQL of ours behind it
            if a is None:
                why.append(f"{u['rel']}: the imported name {attr!r} (from {_rel(tp)}) is neither a definition nor a constant "
                           "this scan can read, so SQL behind it is not resolvable")
                continue
            ap, atree, anode = a
            if (str(ap.resolve()), attr) in seen:
                continue
            seen.add((str(ap.resolve()), attr))
            if u["hop"] + 1 > hops:
                if any(_SQL_CTX.search(t) and _FROM_JOIN.search(t)
                       for t, _ln in _sql_texts(dict(rel=_rel(ap), path=ap, tree=atree, nodes=[anode], hop=u["hop"] + 1, via=""))):
                    why.append(f"{_rel(ap)}: the constant {attr!r} holds SQL that reads a relation {u['hop'] + 1} hop(s) from the "
                               f"writer ({u['via']}), one past the scan limit of {hops} hop(s)")
                continue
            out.append(dict(rel=_rel(ap), path=ap, tree=atree, nodes=[anode], hop=u["hop"] + 1,
                            via=f"{u['via']} → {_rel(ap)}:{attr}"))
    return out, why


def _scope_sites(units: list[dict]) -> list[dict]:
    sites = []
    for u in units:
        for node in u["nodes"]:
            for x, fn, cls in _walk_ctx(node):
                if isinstance(x, ast.Call):
                    f = x.func
                    callee = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                    sites.append(dict(call=x, callee=callee, fn=fn, cls=cls, unit=u))
    return sites


def reads_scan(asset_id: str, files: list[str], hops: int | None = None) -> dict:
    """What the writer of `asset_id` READS (static SQL), and whether that parse is complete.

    Returns dict(reads={table: [(file, line, chain)]}, incomplete=[reason, ...], units=int, sql_strings=int, hops=int,
    co_registered=[other asset ids registered on the same writer class]).
    `reads` is every FROM / JOIN relation of every SQL string (an execute-type call's text, f-strings and `a + b`
    resolved by `_sql_texts`) in the registered class's delegation scope, `hops` modules deep (the same scope
    machinery as Idem.pattern; docstrings are not SQL). `incomplete` lists every reason the parse may be missing a
    read, each with file:line: a registered class not found (the whole module would be in scope), a table named
    dynamically, an execute-type call whose SQL argument is not traced to a literal, and SQL that reads a relation
    one hop past the scan limit. Empty `incomplete` = every SQL string in scope was parsed and every relation named."""
    hops = READS_DELEGATION_HOPS if hops is None else hops
    units, _beyond = _delegation_scope(asset_id, files, hops=hops)
    extra_units, unresolved = _constant_units(units, hops)
    units = units + extra_units
    reads: dict[str, list[tuple[str, int, str]]] = {}
    incomplete: list[str] = list(unresolved)
    n_sql = 0
    co_registered: set[str] = set()                  # other assets registered on the SAME writer class (bg_transit_engine / bg_transit_rules)
    for name in files:
        cls = _writer_class(_writer_path(name), asset_id)
        if cls is None:
            incomplete.append(f"{name}: no class registered for {asset_id} found, so the whole module would be in scope")
            continue
        consts = _module_constants(_parse(_writer_path(name)))
        co_registered |= {rid for d in cls.decorator_list if (rid := _register_id(d, consts))} - {asset_id}
    for u in units:
        for text, line in _sql_texts(u):
            if not (_SQL_CTX.search(text) and _FROM_JOIN.search(text)):
                continue
            n_sql += 1
            tables, dynamic = sql_relations(text)
            for t in tables:
                loc = (u["rel"], line, u["via"] if u["hop"] else "")
                if loc not in reads.setdefault(t, []):
                    reads[t].append(loc)
            for d in dynamic:
                incomplete.append(f"{u['rel']}:{line}: a table is named dynamically ({d!r}), so the read is not resolvable")
    sites = _scope_sites(units)
    for s in sites:
        c = s["call"]
        if isinstance(c.func, ast.Attribute) and c.func.attr in _EXEC_METHODS and c.args \
                and not _sql_arg_traced(c.args[0], s["fn"], s["cls"], s["unit"], sites):
            incomplete.append(f"{s['unit']['rel']}:{c.lineno}: {c.func.attr}() is given SQL that is not traced to a "
                              f"literal ({ast.unparse(c.args[0])[:40]!r}), so what it reads is not resolvable")
        elif isinstance(c.func, (ast.Attribute, ast.Name)) and c.args:
            callee = c.func.attr if isinstance(c.func, ast.Attribute) else c.func.id
            if callee not in _EXEC_METHODS and _SQL_LIKE_CALLEE.match(callee) and not any(
                    _sql_arg_traced(a, s["fn"], s["cls"], s["unit"], sites) for a in list(c.args) + [k.value for k in c.keywords]):
                incomplete.append(f"{s['unit']['rel']}:{c.lineno}: {callee}() takes SQL and none of its arguments is traced "
                                  "to a literal, so what it reads is not resolvable")
    frontier, _ = _delegation_scope(asset_id, files, hops=hops + 1)
    for u in frontier:
        if u["hop"] == hops + 1 and any(_SQL_CTX.search(t) and _FROM_JOIN.search(t) for t, _ln in _sql_texts(u)):
            incomplete.append(f"{u['rel']}: holds SQL that reads a relation {hops + 1} hop(s) from the writer ({u['via']}), "
                              f"one past the scan limit of {hops} hop(s)")
    return dict(reads=reads, incomplete=sorted(set(incomplete)), units=len(units), sql_strings=n_sql, hops=hops,
                co_registered=sorted(co_registered))


def build_table_owners(rows) -> dict[str, list[str]]:
    """table -> the active WRITER-BACKED assets that PRODUCE it: each row is (asset_id, target_table, count_sql[,
    has_writer=True]); a table is produced by an asset when it is its target_table or one of the relations its
    count_sql names (a multi-table asset declares its produced tables there; a partition writer such as ga_strength
    declares chart_facts there). An asset with no writer (a user_data table such as lel_events, a static table) produces
    nothing a build waits for: a depends_on edge to it could never reach `lit` (T4 check 9, a permanent DEP-ASSERT
    trap), so a read of its table is never a missing edge."""
    out: dict[str, set[str]] = {}
    for row in rows:
        aid, target, count_sql = row[0], row[1], row[2]
        if len(row) > 3 and not row[3]:
            continue
        for t in ([target] if target else []) + _count_tables(count_sql or ""):
            out.setdefault(t.lower(), set()).add(aid)
    return {t: sorted(a) for t, a in sorted(out.items())}


def produced_table_owners() -> dict[str, list[str]]:
    """Registry-wide (every layer) table -> producing active writer-backed assets, in one JSON read (count_sql holds
    newlines, so a line-oriented read would split rows). Raises Unknown when the registry cannot be read."""
    blob = scalar("SELECT coalesce(json_agg(json_build_object('a',asset_id,'t',target_table,'c',coalesce(count_sql,''),"
                  "'w',coalesce(has_writer,false)) ORDER BY asset_id)::text,'[]') FROM asset_registry "
                  "WHERE is_active AND NOT coalesce(dead_flag,false)")
    return build_table_owners((r["a"], r["t"], r["c"], r["w"]) for r in json.loads(blob or "[]"))


_DAG_GUARD: list = []
_DAG_GUARD_PATH = Path(__file__).resolve().parents[2] / "python-sidecar" / "pipeline" / "orchestrator" / "dag_edge_guard.py"


def _dag_guard():
    """The repo's own `pipeline/orchestrator/dag_edge_guard.py`, loaded by file path (it imports nothing heavy at module
    level: its DB import is deferred). Its exemption lists are the SINGLE source for which tables a read of which needs no
    declared edge — this module never keeps a second list. Raises Unknown when the guard cannot be loaded."""
    if not _DAG_GUARD:
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location("dag_edge_guard_for_census", _DAG_GUARD_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for need in ("_UNGATED_PREFIXES", "_UNGATED_EXACT", "_EXTERNAL_TABLES", "_SHARED_SOFT_TABLES"):
                getattr(mod, need)
        except Exception as exc:
            raise Unknown(f"dag_edge_guard could not be loaded from {_DAG_GUARD_PATH}: {type(exc).__name__}: {exc}") from exc
        _DAG_GUARD.append(mod)
    return _DAG_GUARD[0]


def _is_bedrock(table: str) -> bool:
    """dag_edge_guard's rule (`_UNGATED_PREFIXES` / `_UNGATED_EXACT` / `_EXTERNAL_TABLES`, pipeline/orchestrator/
    dag_edge_guard.py:86-89): always-present L0 bedrock (bg_, reference_, brahma_, sutravali_, classical_, ephemeris_daily)
    and external ingest tables are never gated."""
    guard = _dag_guard()
    t = table.lower()
    return t.startswith(tuple(guard._UNGATED_PREFIXES)) or t in guard._UNGATED_EXACT or t in guard._EXTERNAL_TABLES


def _ancestors(graph: dict[str, list[str]] | None, start: str) -> set[str]:
    out, todo = set(), [start]
    while todo:
        for d in (graph or {}).get(todo.pop(), []):
            if d not in out:
                out.add(d)
                todo.append(d)
    return out


def _dep_path(graph: dict[str, list[str]], start: str, goal: str) -> list[str] | None:
    """The shortest depends_on chain `start -> ... -> goal` (at least one edge, so `start == goal` finds a cycle through
    `start`), or None. Computed from the registry graph handed in, never assumed."""
    prev: dict[str, str] = {}
    todo = []
    for d in graph.get(start, []):
        if d not in prev:
            prev[d] = start
            todo.append(d)
    while todo:
        x = todo.pop(0)
        if x == goal:
            path = [goal]
            while True:
                path.append(prev[path[-1]])
                if path[-1] == start:
                    return path[::-1]
        for d in graph.get(x, []):
            if d not in prev:
                prev[d] = x
                todo.append(d)
    return None


def _reads_clause(aid: str, r: dict, files: list[str], owners_fn, g) -> tuple[str, str, dict]:
    """The reads-match clause of Build.dag (T4:275): (verdict, text, extra record keys). `g` is the registry-wide
    depends_on graph with this asset's own edges applied, or None when it could not be read.

    A read of another writer-backed asset's table with no DIRECT declared edge is a finding. Two kinds:
      missing_edge  declaring `aid -> producer` is possible: the graph stays acyclic (a shared table is satisfied by an
                    edge to ANY one producer, and only the producers that stay acyclic are named);
      back_read     every producer of the table already depends on `aid` (directly or through a chain): the code reads a
                    DOWNSTREAM asset's product, an edge would close a cycle, so it is NOT a missing edge. The cycle test
                    is computed from the graph plus the candidate edge (`_dep_path`), never listed by name.
    Both keep the verdict FAIL (the evidence stays visible). `transitive_only` marks a FAIL whose every missing edge is
    already reachable through a declared dependency (ordering holds, the edge is undeclared) — SS decides later whether
    that stays a FAIL; the default is FAIL.
    Findings are counted at table level (one per (asset, table) with a producer set); a distinct (asset, producer-set)
    pair can carry several tables.

    An incomplete parse with no undeclared read reads PARTIAL when at least one read resolved and every resolved read is
    covered (the Idem.pattern precedent: a scan that cannot see everything says so), NO_DETECTOR when nothing resolved.
    DEFAULT PENDING SS."""
    deps = list(r["depends_on"])
    if not files:
        if not r["has_writer"] and not deps:
            return PASS, ("no writer (registry has_writer=false and no @register found) and no declared edge — no build code "
                          "reads anything, so there is nothing to match"), {}
        if not r["has_writer"]:
            return NO_DET, (f"not established: no writer code to scan (registry has_writer=false) but {len(deps)} declared "
                            "edge(s) — they cannot be compared with reads"), {}
        return NO_DET, ("not established: the registry says has_writer=true and no @register file was found "
                        "(see Build.registered)"), {}
    try:
        scan = reads_scan(aid, files)
    except Exception as exc:
        return ERRORED, f"check errored: reads-match scan failed: {type(exc).__name__}: {exc}", {}
    own = set(filter(None, [r["target_table"]])) | set(_count_tables(r["count_sql"]))
    owners: dict[str, list[str]] = {}
    if scan["reads"]:
        try:
            owners = owners_fn()
        except Unknown as exc:
            return ERRORED, (f"check errored: table ownership unreadable, so what the writer reads cannot be attributed to "
                             f"assets: {exc}"), {}
    try:
        guard = _dag_guard() if scan["reads"] else None
    except Unknown as exc:
        return ERRORED, f"check errored: {exc}", {}
    anc = {d: _ancestors(g, d) for d in deps} if g is not None else {}
    closure = set(deps).union(*anc.values()) if g is not None else None
    findings, covered, exempt, soft = [], 0, [], []
    for t, locs in sorted(scan["reads"].items()):
        prod = [a for a in owners.get(t, []) if a != aid]
        if not prod or aid in owners.get(t, []) or t in own or any(p in scan["co_registered"] for p in prod):
            continue                  # nobody produces it / its own table / produced by another asset of the SAME writer class
        if any(p in deps for p in prod):
            covered += 1
            continue
        f, ln, via = sorted(locs)[0]  # the first location in file order
        bedrock_name = _is_bedrock(t)
        non_l0 = bedrock_name and not all(o.startswith(LAYERS["L0"]["prefix"]) for o in owners.get(t, []))
        if bedrock_name and not non_l0:
            # SS ruling 2026-10-01 (PROVISIONAL interpretation of T4, to be confirmed at the J1 review): a read of an L0 bedrock
            # table needs no declared edge. STRICTER THAN dag_edge_guard, which exempts by table NAME alone: here the table must
            # have a bedrock NAME (the guard's lists) AND every producer that owns it must be an L0 asset (bg_*) — a
            # `brahma_*` table owned by an L2+ asset is an ordinary read (earned-signal-conservative, CLAUDE.md N.8).
            # Kept visible as `bedrock_exempt`, never dropped.
            exempt.append(dict(asset=aid, needs=" | ".join(prod), table=t, file=f, line=ln, via=via, kind="bedrock_exempt"))
            continue
        if t in guard._SHARED_SOFT_TABLES and closure is not None and any(p in closure for p in prod):
            # dag_edge_guard's SOFT tier: a polymorphic multi-producer table (chart_facts) is satisfied by ANY producer in the
            # declared TRANSITIVE closure; with none in the closure at all it stays a finding (below).
            soft.append(dict(asset=aid, needs=" | ".join(prod), table=t, file=f, line=ln, via=sorted(p for p in prod if p in closure),
                             kind="soft_satisfied", fact_category_matched=False))
            continue
        chains = {p: _dep_path(g, p, aid) for p in prod} if g is not None else {}
        viable = [p for p in prod if chains.get(p) is None]
        if g is not None and not viable:
            findings.append(dict(asset=aid, needs=" | ".join(prod), table=t, file=f, line=ln, via=via, transitive_via=[],
                                 kind="back_read", cycle_path=chains[prod[0]], cycle_tested=True))
        else:
            need = viable if g is not None else prod
            findings.append(dict(asset=aid, needs=" | ".join(need), table=t, file=f, line=ln, via=via,
                                 transitive_via=sorted(d for d in deps if any(p in anc.get(d, ()) for p in need)),
                                 kind="missing_edge", cycle_tested=g is not None))
    for fd in findings:
        if _is_bedrock(fd["table"]) and not all(o.startswith(LAYERS["L0"]["prefix"]) for o in owners.get(fd["table"], [])):
            fd["bedrock_name_non_l0_owner"] = True
    if findings:
        parts = []
        for fd in findings:
            at = f"{fd['file']}:{fd['line']}" + (f", via {fd['via']}" if fd["via"] else "")
            if fd["kind"] == "back_read":
                parts.append(f"back-read: {aid} reads {fd['table']} ({at}), the product of {fd['needs']}, which already depends on "
                             f"{aid} (chain {' -> '.join(fd['cycle_path'])}); an edge {aid} -> {fd['needs']} would create a cycle")
            else:
                s = f"missing depends_on edge: {aid} -> {fd['needs']} (reads {fd['table']} at {at}"
                s += (f"; the producer is reachable transitively via {', '.join(fd['transitive_via'])}, so ordering holds but the "
                      "edge is undeclared") if fd["transitive_via"] else ""
                s += "; the cycle test did not run: the registry dependency graph was unreadable, so this could be a back-read" \
                    if not fd["cycle_tested"] else ""
                s += "; bedrock-named table with a non-L0 owner: not exempt (stricter than dag_edge_guard, which exempts by name alone)" \
                    if fd.get("bedrock_name_non_l0_owner") else ""
                parts.append(s + ")")
        extra_ev = {k: v for k, v in (("bedrock_exempt", exempt), ("soft_satisfied", soft)) if v}
        miss = [fd for fd in findings if fd["kind"] == "missing_edge"]
        # transitive_only is claimed only when no back-read is present for the asset: a back-read must stay visible in the
        # rollup reason (a mix of a back-read and all-transitive missing edges is NOT "transitive only")
        only_t = bool(miss) and len(miss) == len(findings) and all(fd["transitive_via"] for fd in miss)
        return FAIL, "FAIL — " + "; ".join(parts), dict(missing_edges=findings, transitive_only=only_t, **extra_ev)
    extra_ev = {k: v for k, v in (("bedrock_exempt", exempt), ("soft_satisfied", soft)) if v}
    satisfied = covered + len(exempt) + len(soft)
    note = ""
    if exempt:
        note += (f"; {len(exempt)} read(s) of bedrock-named table(s) owned only by L0 assets ({', '.join(e['table'] for e in exempt)}) "
                 "need no declared edge (dag_edge_guard exemption list; stricter than the guard, which exempts by table name alone; "
                 "provisional interpretation of T4, to be confirmed at the J1 review)")
    if soft:
        note += (f"; {len(soft)} chart_facts read(s) satisfied by a producer in the declared transitive closure "
                 f"({', '.join(sorted({v for sf in soft for v in sf['via']}))}; dag_edge_guard SOFT tier): satisfied by ANY chart_facts "
                 "producer in the declared closure; fact_category is not matched, so this does not prove the READ category is "
                 "produced upstream")
    if scan["incomplete"]:
        why = "; ".join(scan["incomplete"][:3]) + (f"; +{len(scan['incomplete']) - 3} more" if len(scan["incomplete"]) > 3 else "")
        if satisfied:
            return PARTIAL, (f"{satisfied} resolved read(s) of other assets' tables are covered by declared edges or exempt (see below), "
                             f"but the parse is incomplete — {why}{note}"), extra_ev
        return NO_DET, (f"not established: the parse is incomplete — {why}. Nothing resolved to compare, so the claim has no "
                        "detector (never a PASS by absence of a parse)"), {}
    return PASS, (f"{covered} read(s) of other assets' tables, every one covered by a declared edge{note}; static scan of "
                  f"{scan['units']} code unit(s), {scan['sql_strings']} SQL string(s), hops<={scan['hops']}, every relation "
                  "named; reads through views and DB functions are not followed"), extra_ev


def _measure_dag(aid: str, r: dict, files: list[str], known: set[str], prefix: str, owners_fn, graph) -> dict:
    """Build.dag (T4:275, check 4: "every depends_on entry exists; no cycle; the declared edges match what the asset
    actually reads"), three clauses, each stated in the verdict text:

      exists       every depends_on id is an ACTIVE registry asset, in EVERY layer. When the registry-wide graph could not
                   be read only ids with this layer's prefix can be checked against the layer registry; the others are
                   NO_DETECTOR for this clause ("not checked"), never a silent PASS.
      cycle        the asset is on no dependency cycle in the registry graph (the cycle is reported); NO_DETECTOR when the
                   graph could not be read.
      reads-match  see `_reads_clause`.

    The verdict is the worst of the three (FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS). `owners_fn()` is the lazily read
    registry-wide ownership map (raises Unknown when unreadable); `graph` the registry-wide depends_on map or None."""
    deps = list(r["depends_on"])
    g = None if graph is None else {**graph, aid: deps}
    if g is not None:
        unknown, unverifiable = [d for d in deps if d not in set(g) | known], []
    else:
        unknown = [d for d in deps if d.startswith(prefix) and d not in known]
        unverifiable = [d for d in deps if not d.startswith(prefix)]
    if unknown:
        ev, et = FAIL, f"depends_on references unknown or inactive assets: {unknown}"
    elif unverifiable:
        ev, et = NO_DET, (f"cross-layer id(s) {unverifiable} not checked: the registry-wide dependency read was unavailable")
    else:
        ev, et = PASS, (f"all {len(deps)} are active registry assets (every layer)" if deps else "no declared edge to resolve")
    if g is None:
        cv, ct = NO_DET, "not measured: the registry-wide dependency read was unavailable"
    else:
        cyc = _dep_path(g, aid, aid)
        cv, ct = (FAIL, f"{' -> '.join(cyc)} (a dependency cycle)") if cyc else (PASS, f"{aid} is on no dependency cycle (registry-wide graph)")
    rv, rt, extra = _reads_clause(aid, r, files, owners_fn, g)
    v = rollup_verdicts([ev, cv, rv])
    return dict(v=v, measured=f"{len(deps)} declared edge(s); exists: {et}; cycle: {ct}; reads-match: {rt}", **extra)


def _declared_kind(declarations, asset_id: str):
    """The kind the asset-declarations file declares for `asset_id`, or None (absent asset / null / unknown kind)."""
    e = (declarations or {}).get(asset_id)
    k = e.get("kind") if isinstance(e, dict) else None
    return k if isinstance(k, str) and k in DECLARED_KINDS else None


def _measure_target(r: dict, owners, declared_kind) -> dict:
    """Build.target (T4:274: "a `target_table` set, or service / multi-table declared explicitly").

    E6 item (g): an asset with NO target_table that BOTH the registry (`asset_kind`) and the asset-declarations file
    declare `service` reads PASS BY DECLARATION. Nothing measures that verdict — no code path tests the declaration,
    so this branch cannot read false (CLAUDE.md N.8); the text and the record's `basis` say so. Where the file and
    the registry disagree the registry fact decides and the reading is the one it always was (cause-keyed N/A);
    `multi-table` is not a kind, it is the measured count_sql table set (`_grade_target_less`)."""
    if r["target_table"]:
        return dict(v=PASS, measured=f"target_table={r['target_table']}")
    if r["asset_kind"] == "service" or not r["has_writer"]:
        if r["asset_kind"] == "service" and declared_kind == "service":
            return dict(v=PASS, basis="declaration",
                        measured="PASS by declaration (T4:274): no target_table, and both the registry (asset_kind='service') and "
                                 "the asset-declarations file (kind: service) declare a service; no measurement stands behind "
                                 "this verdict — nothing tests the declaration, so this branch has no fail path (CLAUDE.md N.8)")
        return _na(f"no target_table; asset_kind='{r['asset_kind']}', has_writer={r['has_writer']}",
                   "service-no-target-table" if r["asset_kind"] == "service" else "no-writer-no-target-table")
    try:
        # R242 (W2-2 OS-B): the registry-wide read happens only when absent (the caller caches it).
        return _grade_target_less(r, owners)
    except Unknown as exc:
        return dict(v=ERRORED, measured=f"check errored: {exc}")


def _grade_target_less(r: dict, owners) -> dict:
    """R53 (T1 plant build_target_null; W2-1 OS-1/#18): Build.target for a writer-backed data/artifact
    asset with NO target_table. The FAIL branch used to be dead — `asset_kind` is NOT NULL
    CHECK(data|service|artifact), so "no target_table" always read the closable N/A.

    The engine never clears or counts by target_table: its produced-table rule is target_table ∪ the
    tables its count_sql names (`dag_edge_guard._producer_tables`), and target_table otherwise feeds
    cowriter-peer detection. So, from the count_sql (`owners()` is called only when needed):
      ≥2 tables                      → PASS: a multi-table asset, its produced tables declared
                                        (bg_prashna_rules: 5 tables);
      1 table, another asset's target → PASS: a partition writer into that asset's table
                                        (ga_strength, ga_structural → chart_facts, 7 declaring assets);
      1 table nobody declares         → FAIL: the declaration is missing (the plant's exact shape);
      no table                        → FAIL: nothing to aim at."""
    ct = _count_tables(r["count_sql"])
    if len(ct) >= 2:
        return dict(v=PASS, measured=f"no single target_table: a multi-table asset whose count_sql declares the "
                                     f"{len(ct)} tables it produces ({', '.join(ct)}) — the engine's produced-table rule")
    if len(ct) == 1:
        own = [a for a in owners().get(ct[0], []) if a != r["asset_id"]]
        if own:
            return dict(v=PASS, measured=f"no target_table: writes a partition of {ct[0]}, the declared target of "
                                         f"{', '.join(own)} (count_sql counts its share)")
        return dict(v=FAIL, measured=f"target_table not declared: count_sql counts {ct[0]}, which no active asset "
                                     "declares as its target — the declaration is missing")
    return dict(v=FAIL, measured="has a writer and neither a target_table nor a count_sql naming a table — the "
                                 "orchestrator's clear/count steps have nothing to aim at")


def _grade_dep_liveness(deps: list[str], deprec: dict, chart_id: str) -> dict:
    """R45 (L2 handverify; W2-1_REVIEW C2): Build.dep_liveness at the census's CHART SCOPE.

    The claim is "every declared dependency is live for the chart this census measures". It used to
    read a chart-agnostic set — an asset_id `lit` on ANY chart counted — so 10 assets read PASS while a
    dependency was `stale` on the canonical chart and lit only on 1c826d5a. A dependency's record is
    its row for `chart_id`, else its global (chart_id NULL) row — no asset carries both (live,
    2026-09-27). Per dependency: `lit` → live; `stale` (a completed build whose upstream has since
    moved) → stale; no record at this scope, or any other state (error, dormant, incomplete,
    building) → not live; an R44-ambiguous record → undetermined. Verdict: any not live → FAIL;
    else any undetermined → ERRORED (never closable); else any stale → PARTIAL; else PASS, naming
    the scope measured."""
    short = chart_id[:8]
    live, stale, dead, undet = [], [], [], []
    for d in deps:
        by = deprec.get(d, {})
        rec, where = ((by[chart_id], f"chart {short}") if chart_id in by
                      else (by[""], "global") if "" in by else (None, ""))
        if rec is None:
            others = sorted({x.get("state", "?") for c, x in by.items() if c})
            dead.append(f"{d} (no build record on chart {short} or global"
                        + (f"; exists only on {len(by)} other chart(s), state(s) {others})" if by else ")"))
        elif rec.get("ambiguous"):
            undet.append(f"{d} ({where}: {rec.get('n_rows')} tied rows)")
        elif rec.get("state") == "lit":
            live.append(d)
        elif rec.get("state") == "stale":
            stale.append(f"{d} (stale, {where})")
        else:
            dead.append(f"{d} ({rec.get('state') or 'no state'}, {where})")
    head = f"{len(live)}/{len(deps)} declared dependencies lit at chart {short} (or global)"
    if dead:
        return dict(v=FAIL, measured=f"{head}; not live: {dead}" + (f"; stale: {stale}" if stale else "")
                                     + " — a DEP-ASSERT trap if no writer can light them")
    if undet:
        return dict(v=ERRORED, measured=f"check errored: {head}; undetermined (R44 tie): {undet}")
    if stale:
        return dict(v=PARTIAL, measured=f"{head}; stale: {stale} — built, but an upstream has moved since")
    return dict(v=PASS, measured=head)


def _grade_count_floor(r: dict, live: int | None, error: str | None, ctables: list[str]) -> dict | None:
    """Count.floor for one asset: the live count against the registry's declared `target_floor`.
    Returns None only when the criterion does not apply (see the branches).

    R56 (T1 differential): on the 57 L1/L2/L4/L5 assets whose count_sql is parameterised (`$1`) or
    multi-table, Count.floor was SILENTLY ABSENT — `live is None` (an unbound `$1`) skipped the
    criterion without a word, while the differential found real breaches it never reported
    (ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510, sandbox). With R231
    binding the chart the count is measured; and when a count_sql exists but could not be measured
    the criterion now reads ERRORED with the reason — never absent. A multi-table total is compared
    as a total (the engine compares its writer's multi-table rows_written with the same floor)."""
    floor = r["target_floor"]
    if floor is None:
        return None                     # nothing declared: there is no floor claim to measure
    # R48 (L3 handverify: 20/23 L3 assets declare target_floor, yet Count.floor was absent from the
    # whole L3 census): every asset that DECLARES a floor gets a verdict, whatever else is missing.
    floor = floor.strip()
    if floor == "0":
        # A floor of zero cannot be breached — `live >= 0` is true of every count, so PASS would be
        # a detector that cannot read false (§N.8). The registry's declaration is what applies.
        return _na("target_floor=0: the registry declares zero rows complete — "
                   f"there is no floor to breach (live={'unmeasured' if live is None else live})", "target-floor-zero")
    if not floor.isdigit():
        return dict(v=NO_DET, measured=f"NO_DETECTOR — target_floor {floor!r} is not a whole number of rows")
    if not r["count_sql"].strip():
        return dict(v=NO_DET, measured=f"NO_DETECTOR — target_floor={floor} is declared but no count_sql is "
                                       "registered to measure it")
    if error is not None or live is None:
        return dict(v=ERRORED, measured=f"check errored: {error or 'count_sql produced no value'} — "
                                        f"floor={floor} not measured")
    if not ctables:
        return dict(v=NO_DET, measured=f"NO_DETECTOR — count_sql reads no table (a constant {live}); "
                                       f"floor={floor} cannot be measured against it")
    d = live - int(floor)
    what = "count_sql total" if (len(ctables) > 1 or r["target_table"] not in ctables) else "live"
    return dict(v=(FAIL if d < 0 else PASS), measured=f"{what}={live}, floor={floor}, delta={d:+d}")


# The closed verdict set a registered carriage detector may return (the ledgers' own vocabulary,
# asset_elevation_tracker.VERDICTS). NOT_GENERIC / ERRORED are census-internal and never a detector's.
DETECTOR_VERDICTS = (PASS, FAIL, PARTIAL, NO_DET, NA)


def _run_carriage_detector(aid: str) -> dict:
    """P3/R57 item (d): a per-asset carriage detector registered at <CTRL>/detectors/<asset>_D<1|2|3>.py
    IS the detector — run it and adopt its verdict instead of the blanket NO_DETECTOR.

    F8 (A_REVIEW.md): the port adopted the last stdout line's `verdict` without checking the
    process's return code or the verdict's vocabulary, so a detector that crashed AFTER printing
    `{"verdict": "PASS", …}` — or printed a verdict outside the closed set — was adopted as its
    verdict, and a PASS closes a gap. A non-zero exit, an unparseable last line, or a verdict outside
    DETECTOR_VERDICTS now reads NO_DETECTOR with the exact reason: a detector that did not complete
    cleanly has measured nothing."""
    det_dir = CTRL / "detectors"
    det = None
    if det_dir.is_dir():
        for n in (1, 2, 3):
            p = det_dir / f"{aid}_D{n}.py"
            if p.exists():
                det = p
                break
    if det is None:
        return dict(v=NO_DET, measured="no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics")
    try:
        pr = subprocess.run([sys.executable, str(det)], capture_output=True, text=True,
                            env=os.environ, timeout=120)
    except Exception as exc:  # a registered detector that cannot run is not a pass
        return dict(v=NO_DET, measured=f"{det.name} failed to run: {exc}")
    if pr.returncode != 0:
        tail = (pr.stderr.strip().splitlines() or ["no stderr"])[-1]
        return dict(v=NO_DET, measured=f"{det.name} exited {pr.returncode} ({tail}) — output of a failed "
                                       "detector is not a verdict")
    try:
        out = json.loads(pr.stdout.strip().splitlines()[-1])
        verdict, measured = out["verdict"], out["measured"]
    except Exception as exc:
        return dict(v=NO_DET, measured=f"{det.name} produced no parseable verdict line: {type(exc).__name__}: {exc}")
    if verdict not in DETECTOR_VERDICTS:
        return dict(v=NO_DET, measured=f"{det.name} returned verdict {verdict!r}, outside the closed set "
                                       f"{list(DETECTOR_VERDICTS)}")
    return dict(v=verdict, measured=f"{det.name}: {measured}")


# ─────────────────────────── the census ───────────────────────────

def _layer_read(name: str, fn, *args):
    """F12 (A_REVIEW.md): name the layer-wide read that failed, so the UNKNOWN says which one."""
    try:
        return fn(*args)
    except Unknown as exc:
        raise Unknown(f"layer-wide read '{name}' failed: {exc}") from exc


def _measure_prose(aid, decl, r, files, cat, ctables, shared, ptests, vocab) -> dict:
    """measure()'s glue for the six Narr/Null checks: gathers the inputs (catalog columns/types/defaults, the asset's
    row counts from its own count_sql scope, the writer scope, tests) and calls prose_checks. Fault-isolated (R41)."""
    tbl = r["target_table"]
    pf = decl.get("prose_fields") if isinstance(decl, dict) else None
    own = {}
    for t in dict.fromkeys([x for x in [tbl] + list(ctables) if x]):
        own[t] = (_target_columns_fact(t, cat),
                  (cat.get("types") or {}).get(t) if cat.get("types") is not None else None,
                  (cat.get("defaults") or {}).get(t, {}) if cat.get("defaults") is not None else None)
    # the asset's own tables: the registry target plus every table its count_sql reads (a multi-table asset keeps its
    # narration column outside the target_table); a table the catalog lacks is unknown, never 'zero columns'
    ctx = dict(table=tbl, own=own, tests=ptests, vocabulary=vocab, counts=None, paths=[], written=None)
    if files and pf is not None:
        try:
            units, _beyond = _delegation_scope(aid, files)
            ctx["paths"] = [u["path"] for u in units]
            ctx["written"] = written_columns(units, [tbl] + list(ctables))
        except Unknown:
            pass
    errored = {}
    if pf:
        # each entry is counted in the owned table that HOLDS its column; an entry no owned table holds, or a table
        # whose scope cannot be established (shared + unparseable count_sql), is unknown for that entry
        counts: dict = {e: None for e in pf}
        groups: dict = {}
        for e in pf:
            held = _holders(parse_prose_field(e)[0], own)
            if held and held[0] in cat["exists"]:
                groups.setdefault(held[0], []).append(e)
        try:
            for t, es in groups.items():
                tail = _count_scope_tail(r["count_sql"], t)
                if tail is not None:
                    # chart-scoped only when the predicate BINDS chart_id to the census chart (`chart_id = $1`, no OR); a
                    # parseable count_sql without it on a table that carries chart_id counts every chart: an upper bound
                    if re.search(r"\bchart_id\s*=\s*\$1(?!\d)", tail) and not re.search(r"\bOR\b", tail, re.I):
                        scope = "chart-scoped by count_sql"
                    elif "chart_id" in (own[t][0] or ()):
                        scope = UPPER_BOUND
                    else:
                        scope = "count_sql predicate (not chart-scoped)"
                elif t in shared:
                    continue
                else:
                    tail = ""
                    scope = (UPPER_BOUND if "chart_id" in (own[t][0] or ()) else "whole-table (table has no chart_id column)")
                got = prose_row_counts(t, es, _bind_chart(tail, CHART_ID), own[t][1])
                for e in es:
                    counts[e] = dict(got[e], scope=scope)
            ctx["counts"] = counts if any(v is not None for v in counts.values()) else None
        except Unknown as exc:
            errored = {c: dict(v=ERRORED, measured=f"check errored: {exc}") for c in ("Narr.checkable", "Null.blank_rows")}
    out = prose_checks(aid, decl, ctx)
    out.update(errored)
    return out


# ─────────────────────────── E1.9: `--assets` scope ───────────────────────────
# A level wave measures and emits ONLY its assets. A scoped census is a PARTIAL census: it is labelled
# (`scope: {assets: [...], partial: true}`) in every header it writes and anything that expects the whole
# population refuses it (`require_full_census`). An unscoped run writes no `scope` key at all, so its output is
# byte-identical to what it was before this flag existed.
EXIT_SCOPE = 6
_ASSET_ID = re.compile(r"[a-z][a-z0-9_]*")


class ScopeError(Exception):
    """A scope that cannot be honoured exactly (unknown / wrong-layer / empty / duplicate / malformed id), or a scoped
    census handed to something that needs the whole population. Never degraded to 'measure everything'."""


def parse_assets_arg(values) -> list[str]:
    """The `--assets` forms: a comma list, a repeated flag, or `@file` (ids separated by commas and/or newlines;
    blank lines and `#` comments ignored). Entries are whitespace-trimmed; ids are NOT case-normalized (a miscased id
    is a typo, reported as one); an empty list, an empty entry, a duplicate or whitespace inside an id is an error."""
    if not values:
        raise ScopeError("--assets was given no value: an empty scope is not 'everything' (omit the flag for a full run)")
    out: list[str] = []
    for raw in values:
        if raw.strip().startswith("@"):
            path = raw.strip()[1:]
            try:
                text = Path(path).read_text(encoding="utf-8-sig")      # a UTF-8 BOM is accepted
            except UnicodeDecodeError as exc:
                raise ScopeError(f"--assets @{path}: not valid UTF-8 text (a UTF-16 or binary file?) — save the list "
                                 "as UTF-8, one id per line or comma-separated") from exc
            except (OSError, ValueError) as exc:
                raise ScopeError(f"--assets @{path}: cannot read the file ({exc.__class__.__name__})") from exc
            entries = []
            for ln in text.splitlines():
                ln = ln.split("#", 1)[0]
                entries += [e for e in (x.strip() for x in ln.split(",")) if e]
            if not entries:
                raise ScopeError(f"--assets @{path}: the file names no asset")
            if any(e.startswith("@") for e in entries):
                raise ScopeError(f"--assets @{path}: nested @file references are not supported")
        else:
            entries = [x.strip() for x in raw.split(",")]
            if any(not e for e in entries):
                raise ScopeError(f"--assets {raw!r}: empty entry (blank value or stray comma)")
        out += entries
    for e in out:
        if re.search(r"\s", e):
            raise ScopeError(f"--assets: whitespace inside the id {e!r} (separate ids with commas)")
        if not _ASSET_ID.fullmatch(e):
            hint = f" — ids are lowercase (did you mean {e.lower()!r}?)" if e != e.lower() and _ASSET_ID.fullmatch(e.lower()) else ""
            raise ScopeError(f"--assets: malformed asset id {e!r}{hint}")
    dup = sorted(e for e, n in collections.Counter(out).items() if n > 1)
    if dup:
        raise ScopeError(f"--assets: duplicate id(s): {', '.join(dup)}")
    return out


def validate_scope(ids: list[str], layer_keys: list[str]) -> dict[str, list[str]]:
    """Every id must be an ACTIVE registry asset of one of `layer_keys`. Returns {layer: sorted ids}. Reports every bad
    id at once: unknown (in no registry), wrong layer (a registry asset of a layer not selected) or retired/inactive."""
    if not ids:
        raise ScopeError("empty scope")
    by_layer: dict[str, list[str]] = {}
    retired: dict[str, str] = {}
    active: dict[str, str] = {}
    for k in layer_keys:
        reg, pop = _layer_read("registry", registry, k)
        for aid in reg:
            active.setdefault(aid, k)
        for x in pop.get("excluded_inactive", ()):
            retired.setdefault(x["asset_id"] if isinstance(x, dict) else str(x), k)
    problems = []
    for aid in ids:
        if aid in active:
            by_layer.setdefault(active[aid], []).append(aid)
            continue
        if aid in retired:
            problems.append(f"{aid}: retired/inactive in {retired[aid]} (the census measures the active population only)")
            continue
        other = None
        for k in ALL_LAYERS:
            if k in layer_keys:
                continue
            try:
                if aid in registry(k)[0]:
                    other = k
                    break
            except Unknown:
                continue
        problems.append(f"{aid}: belongs to {other}, not in the selected layer(s) {', '.join(layer_keys)}" if other
                        else f"{aid}: unknown asset (not in the registry of {', '.join(layer_keys)})")
    if problems:
        raise ScopeError("; ".join(problems))
    return {k: sorted(v) for k, v in by_layer.items()}


def _is_full_census_path(target, full_out) -> bool:
    """Is `target` the full census file by ANY route: the same path, a case variant (case-insensitive filesystems), a
    hardlink or a symlink? An existing target is compared by inode (`os.path.samefile`); a not-yet-existing one by its
    resolved, normcased, case-folded path (conservative: on a case-sensitive filesystem a case variant is refused too)."""
    t, f = Path(target), Path(full_out)
    try:
        if t.exists() and f.exists() and os.path.samefile(t, f):
            return True
    except OSError:
        pass
    norm = lambda p: os.path.normcase(str(p.resolve())).casefold()      # noqa: E731
    return norm(t) == norm(f)


def _write_atomic(path, text: str) -> None:
    """Write `text` to `path` via a temp file in the same directory and `os.replace` — readers and concurrent writers
    see the old file or the whole new one, never a torn one. The temp file is removed on any failure."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".asset_census_", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        um = os.umask(0)
        os.umask(um)
        os.chmod(tmp, 0o666 & ~um)          # mkstemp's 0600 is not the mode a plain write_text would have given the file
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def census_scope(obj) -> dict | None:
    """The scope label of a layer census, or None (a full census carries none). Fail-closed on a malformed label."""
    if not isinstance(obj, dict) or "scope" not in obj:
        return None
    sc = obj["scope"]
    if not (isinstance(sc, dict) and sc.get("partial") is True and isinstance(sc.get("assets"), list)
            and sc["assets"] and all(isinstance(x, str) and x for x in sc["assets"])):
        raise ScopeError(f"malformed census scope label {sc!r}: expected {{assets: [non-empty ids], partial: true}}")
    return sc


def require_full_census(obj, who: str) -> None:
    """Refuse a SCOPED census (a layer census, a census file, or a file's rollup) — for anything that needs all assets."""
    labels = [("census", obj)]
    if isinstance(obj, dict):
        labels += [(k, v) for k, v in obj.items() if isinstance(v, dict) and k != "scope"]
        if isinstance(obj.get("rollup"), dict):
            labels.append(("rollup", obj["rollup"]))
    for where, o in labels:
        if census_scope(o) is not None:
            raise ScopeError(f"{who}: refuses a SCOPED census ({where} carries scope.partial=true) — it needs the full "
                             "population; re-run without --assets")
        n, pop = (o.get("n_assets"), o.get("population_active")) if isinstance(o, dict) else (None, None)
        if isinstance(n, int) and isinstance(pop, int) and not isinstance(n, bool) and n < pop:
            raise ScopeError(f"{who}: refuses a census whose n_assets ({n}) is below the layer's population_active ({pop}) "
                             f"({where}): a partial census with its scope label stripped — it needs the full population")


def load_full_census(path) -> dict:
    """Read a census JSON for a consumer that expects every asset; a scoped file is refused."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    require_full_census(obj, f"census file {path}")
    return obj


def measure(layer_key: str, assets=None) -> dict:
    """Measure one layer — or, with `assets` (E1.9), ONLY those assets of it.

    SCOPE (E1.9). `assets` is validated against the layer's active registry BEFORE anything is measured (ScopeError:
    empty, duplicate, miscased, unknown or not in this layer). The per-asset reads (live counts, build record, build
    history, latest attempts, dependency records, catalog) are made for the selected assets only; the checks that read
    the WHOLE layer (Build.dag's known ids, the shared-table set, the blocking radius, the layer facts) still read the
    whole registry, so a scoped asset measures to exactly what it measures to in a full run. The result carries
    `scope={assets, partial: true}`; a full run carries no `scope` key.

    R41 SCOPE LIMIT (F12, A_REVIEW.md — disclosed, not fixed). R41 isolates PER-ASSET checks: one
    asset's failing check degrades only that criterion to ERRORED. The LAYER-WIDE reads below —
    `registry`, `catalog`, `registered_ids` (the writer scan), `throughput`, `build_history` — are
    not isolated: any of them raising `Unknown` still aborts the whole layer (exit 4, nothing reported
    clean), and under `--layer all` it also stops every layer after it, with no census file written.
    That is fail-closed, never a false PASS, but it is a whole-layer blind spot, not a degraded one.
    (`live_counts` isolates per asset itself — F2; `duration_instrument_present` degrades to
    `instrument unreachable` — D6 item 1.)"""
    cfg = LAYERS[layer_key]
    reg_all, population = _layer_read("registry", registry, layer_key)
    reg, assets_sel = reg_all, None                       # E1.9: `assets_sel` is the scope label (None: a full run)
    if assets is not None:
        sel = list(assets)
        if not sel or len(set(sel)) != len(sel) or any(not isinstance(x, str) or not _ASSET_ID.fullmatch(x) for x in sel):
            raise ScopeError(f"layer {layer_key}: the scope must be a non-empty list of distinct lowercase asset ids, got {sel!r}")
        missing = sorted(set(sel) - set(reg_all))
        if missing:
            raise ScopeError(f"layer {layer_key}: not active registry assets of this layer: {', '.join(missing)}")
        reg = {aid: r for aid, r in reg_all.items() if aid in set(sel)}     # registry order, like a full run
        assets_sel = sorted(sel)
    cat = _layer_read("catalog", catalog, [r["target_table"] for r in reg.values()]
                      + [t for r in reg.values() for t in _count_tables(r["count_sql"])])
    regd = _layer_read("registered_ids", registered_ids, cfg["prefix"])
    # R46 (L2 handverify): a view asset whose registry count_sql is a constant (bo_samvada: `SELECT 0`
    # over vw_chart_digest, which returns 15 rows) is counted by the VIEW — chart-scoped where the view
    # carries chart_id — instead of reading the constant as its live rows.
    view_counts = {aid: _view_count_sql(r["target_table"], cat["cols"].get(r["target_table"], []))
                   for aid, r in reg.items()
                   if r["target_table"] in cat.get("views", set()) and not _count_tables(r["count_sql"])}
    counts, count_errors = _layer_read("live_counts", live_counts, reg, CHART_ID, view_counts)
    ids = sorted(reg)                                      # R224: the layer's measured population
    # D6 item 1: feature-detected ONCE per layer run, not per asset — the instrument either
    # exists or it doesn't; a per-asset re-check would just be the same answer 40 times over.
    # (Detected before the build-record read, which names `duration_seconds` only when present.)
    instrument_present = duration_instrument_present()
    thru = _layer_read("throughput", throughput, cfg["prefix"], ids, instrument_present is True)
    hist = _layer_read("build_history", build_history, cfg["prefix"], ids)
    # D6 item 2: the latest started attempt per (asset, run chart). Fault-isolated like live_counts:
    # a failed read leaves Earn/Cost unlinked (NO_DETECTOR), it never aborts the layer.
    try:
        attempts, era = latest_attempts(ids)
    except Unknown:
        attempts, era = None, None
    # R45: every declared dependency's build record (cross-layer ones included), latest per
    # (asset, chart) by R44's rule — read only when some asset declares a dependency.
    dep_ids = sorted({d for r in reg.values() for d in r["depends_on"]})
    deprec = _layer_read("dependency_records", throughput, "", dep_ids) if dep_ids else {}
    lmaps = local_map_candidates(cfg["prefix"]) if layer_key == "L0" else -1
    # R21: the blocking radius, registry-wide. Fault-isolated: an unreadable graph leaves every asset's
    # radius UNMEASURED (None, with the reason) — never 0, which would read as "an isolated leaf".
    try:
        dep_graph = dependency_graph()
        radius, radius_note = blocking_radius(dep_graph), None
    except Unknown as exc:
        dep_graph = None
        radius, radius_note = {}, f"unmeasured: the dependency read failed ({exc})"
    # E6 item (g): the asset-declarations file's kinds (a declared service satisfies Build.target by declaration).
    # An unreadable file leaves every declared kind UNKNOWN: Build.target then reads exactly as before.
    try:
        declarations = load_asset_declarations()
    except DeclarationsError:
        declarations = None
    # R23: every capability module's SQL, read once per layer run.
    try:
        caps_sql, caps_note = capability_sql(), None
    except Unknown as exc:
        caps_sql, caps_note = None, str(exc)

    known = set(reg_all)
    # E6.1 (d): a table (target or count_sql) that MORE THAN ONE active asset of this layer declares is shared.
    # Disclosed limit: only this layer's registry is read here; every share in the estate today sits inside one layer.
    _decl: dict[str, set[str]] = {}
    for _aid, _r in reg_all.items():
        for _t in ([_r["target_table"]] if _r["target_table"] else []) + _count_tables(_r["count_sql"]):
            _decl.setdefault(_t, set()).add(_aid)
    dens_shared = frozenset(t for t, who in _decl.items() if len(who) > 1)
    owners: dict = {}                                     # R53: read lazily, at most once per layer
    try:                                                   # E6 packet (c): read once per layer run
        prose_decls = load_asset_declarations()
        prose_vocab = prose_vocabulary(prose_decls)
    except DeclarationsError as exc:
        prose_decls, prose_vocab = exc, set()
    prose_tests = None
    produced: dict = {}                                   # E6 (h): registry-wide table -> producers, lazily, once per layer

    def produced_owners():
        if "map" not in produced:                         # an unreadable map raises and is NOT cached as empty
            produced["map"] = produced_table_owners()
        return produced["map"]
    assets = []
    for aid, r in reg.items():
        m: dict[str, dict] = {}
        files = regd.get(aid, [])

        # Build.registered
        if len(files) == 1 and r["has_writer"]:
            m["Build.registered"] = dict(v=PASS, measured=f"@register in {files[0]}; registry agrees")
        elif len(files) == 1 and not r["has_writer"]:
            m["Build.registered"] = dict(v=FAIL, measured=f"@register in {files[0]} but registry says has_writer=false")
        elif len(files) > 1:
            m["Build.registered"] = dict(v=FAIL, measured=f"registered in {len(files)} files: {', '.join(files)}")
        elif r["has_writer"]:
            m["Build.registered"] = dict(v=FAIL, measured="registry says has_writer=true and no @register found")
        else:
            m["Build.registered"] = _na("no writer, and the registry agrees (service or static)", "no-writer-registry-agrees")

        # R41: a per-check exception must degrade THAT check to ERRORED, never abort the layer.
        m["Build.contract"] = _measure_contract(aid, files, r["has_writer"])
        m["Idem.pattern"] = _measure_idem(aid, files, cfg["idem"], r["has_writer"],
                                          [r["target_table"]] + _count_tables(r["count_sql"]))

        # Build.target
        m["Build.target"] = _measure_target(
            r, lambda: owners["map"] if "map" in owners else owners.setdefault("map", target_owners()),
            _declared_kind(declarations, aid))

        # Build.dag: resolvability, and (E6 item h, T4:275) the declared edges against what the writer reads
        m["Build.dag"] = _measure_dag(aid, r, files, known, cfg["prefix"], produced_owners, dep_graph)

        ok_ci = bool(r["count_sql"]) and r["has_integrity"]
        ci_text = f"count_sql={'yes' if r['count_sql'] else 'no'}, integrity_check_sql={'yes' if r['has_integrity'] else 'no'}"
        if ok_ci:
            m["Build.count_integrity"] = dict(v=PASS, measured=ci_text)
        elif not r["has_writer"] and not r["count_sql"]:
            m["Build.count_integrity"] = _na(ci_text, "no-writer-no-count-sql")
        else:
            m["Build.count_integrity"] = dict(v=PARTIAL, measured=ci_text)

        live = counts.get(aid)
        is_view = aid in view_counts                                       # R46
        ctables = [r["target_table"]] if is_view else _count_tables(r["count_sql"])
        multi = len(ctables) > 1 or (bool(ctables) and r["target_table"] not in ctables)
        # R42: say what the live figure IS. On a multi-table asset it is the count_sql total across
        # every table it reads — compared like-for-like with rows_written (the writer's own total
        # across the same tables, e.g. mi_kula.py:302 `len(_FAMILIES) + len(_CONTROLS)`) — and never
        # presented as the target table's own rows (that figure is appended below, as context).
        basis = (f"counted by the census from the view {r['target_table']} "
                 f"({'chart-scoped' if _chart_scoped(view_counts[aid]) else 'whole view'}); the registry "
                 f"count_sql is a constant ({' '.join(r['count_sql'].split())})" if is_view
                 else f"count_sql total over {len(ctables)} table(s): {', '.join(ctables)}" if multi
                 else "count_sql over the target table")
        t, rec_scope = _build_record(thru.get(aid, {}),
                                     _chart_scoped(view_counts[aid] if is_view else r["count_sql"]), CHART_ID)
        if t.get("n_rows", 1) > 1 and not t.get("ambiguous"):
            rec_scope += f"; latest of {t['n_rows']} rows, last_built {t.get('last_built') or 'NULL'}"   # R44
        rw = t.get("rows_written", "")
        if aid in count_errors:
            # F2 (A_REVIEW.md): a count_sql that RAISED must never read N/A "no count_sql" — that
            # reading is CLOSABLE and a live demonstration (bg_ephemeris) closed the gap on a query
            # that in fact errored. D4 case 1 ("never on an errored check") requires ERRORED here.
            m["Build.completion"] = dict(v=ERRORED, measured=f"check errored: {count_errors[aid]}")
        elif live is None and r["count_sql"].strip():
            # R222 / N1: a count_sql exists but produced no value that live_counts recorded. Never
            # "no count_sql" — that text would be false, and N/A would close a gap.
            m["Build.completion"] = dict(v=ERRORED, measured="check errored: count_sql produced no value")
        elif live is None:
            if not r["has_writer"] or (r["asset_kind"] == "service" and not r["target_table"]):
                m["Build.completion"] = _na(
                    f"no count_sql and nothing to count: has_writer={r['has_writer']}, "
                    f"asset_kind='{r['asset_kind']}', no target_table; build state='{t.get('state','-')}'",
                    "no-writer-no-count-sql" if not r["has_writer"] else "service-no-target-table-no-count-sql")
            else:
                m["Build.completion"] = dict(
                    v=NO_DET, measured="NO_DETECTOR — no count_sql registered for a writer-backed asset with "
                                       f"asset_kind='{r['asset_kind']}'; completion cannot be measured")
        elif is_view:
            # R46: the view is now counted — but a view has no written rows: the writer creates or
            # preserves the view object (bo_samvada: rows_written=1 "the VIEW itself counts as 1
            # object", WriterResult rows_inserted=0), so rows_written<->live consistency is not
            # measurable. Emptiness still is: a view serving no rows for this chart FAILs unless the
            # registry declares zero rows complete. Never PASS on a comparison that cannot be made.
            if live == 0 and (r["target_floor"] or "").strip() != "0":
                m["Build.completion"] = dict(v=FAIL, measured=f"empty: live=0 ({basis}; {rec_scope}) and the registry "
                                                             "does not declare zero rows complete")
            else:
                m["Build.completion"] = dict(v=NO_DET, measured=f"NO_DETECTOR — view: live={live} ({basis}; {rec_scope}); "
                                                               f"build record rows_written={rw or 'none'} counts the "
                                                               "view object, not rows — completion consistency is not "
                                                               "measurable for a view")
        elif not ctables:
            # R42: a count_sql that reads no relation is a constant — it cannot disagree with anything.
            m["Build.completion"] = dict(v=NO_DET, measured=f"NO_DETECTOR — count_sql reads no table (a constant "
                                                           f"{live}); completion cannot be measured")
        elif live == 0 and (r["target_floor"] or "").strip() != "0":
            # R52 (T1 plant build_completion_truncate): NON-EMPTINESS, measured on its own and first.
            # The check used to be only a rows_written<->live consistency test, so emptying a table
            # whose build record said rows_written=0 made the two AGREE and flipped FAIL -> PASS:
            # destroying data made the asset look healthy. An empty result is a completion only
            # where the registry itself declares zero rows complete (target_floor=0 — the engine's
            # own rule, asset_runner.py `zero_rows_is_complete`); everywhere else it FAILs,
            # whatever the build record says.
            m["Build.completion"] = dict(v=FAIL, measured=f"empty: live=0 ({basis}; {rec_scope}) and the registry "
                                                         f"does not declare zero rows complete (target_floor="
                                                         f"{r['target_floor'] if r['target_floor'] is not None else 'none'}); "
                                                         f"build record rows_written={rw or 'none'}")
        elif t.get("ambiguous"):
            # R44: several build rows for this (asset, chart) tie on (last_built_at, last_measured_at),
            # so which one is the latest is undetermined. Comparing against an arbitrary one would be
            # a verdict on a row nobody chose — ERRORED (neither opens nor closes a gap).
            m["Build.completion"] = dict(v=ERRORED, measured=f"check errored: {t.get('n_rows')} asset_throughput "
                                                             f"rows for this asset ({rec_scope}) tie on "
                                                             "(last_built_at, last_measured_at) — the latest "
                                                             "build record cannot be determined")
        elif rw == "":
            m["Build.completion"] = dict(v=FAIL, measured=f"live={live} and no build record at all ({rec_scope})")
        elif t.get("state") not in COMPLETED_STATES:
            m["Build.completion"] = dict(v=FAIL, measured=f"build record state='{t.get('state')}' is not a completed "
                                                         f"build (rows_written={rw}, live={live}, {rec_scope}) — see "
                                                         "Build.history"
                                                         + _cascade_skip_note(t.get("state"), hist["per"].get(aid)))
        elif int(rw) == 0 and live > 0:
            m["Build.completion"] = dict(v=FAIL, measured=f"build record says rows_written=0 against live={live} ({rec_scope})")
        elif int(rw) != live:
            # R42: the pre-fix final branch read PASS for ANY rows_written > 0 — it never compared
            # (mi_kula's "15 vs 11 scored PASS" was that branch; 15 vs anything would have passed).
            m["Build.completion"] = dict(v=FAIL, measured=f"build record rows_written={rw} disagrees with "
                                                         f"live={live} ({basis}; {rec_scope})")
        elif live == 0 and r["has_writer"]:
            # R99: the uncovered third case (ga_prashna: 51 runs, 0 rows, 0 modules). target_floor=0
            # alone is not "the layer plan declares this asset empty by design" — it is frequently
            # just an unset floor, and R52's fix (below) built its PASS path for a genuinely
            # design-empty asset (bg_sarvatobhadra_grid: has_writer=false, no writer ever attempted).
            # A WRITER-BACKED data asset that has actually run and still produced zero rows is
            # indistinguishable from a writer that has never worked — PASS here would silently
            # launder that ambiguity through the same branch. has_writer is the one existing
            # registry signal honest enough to distinguish the two without inventing a new
            # "empty by design" field nothing populates yet; a writer-backed asset gets PARTIAL —
            # not FAIL (R52's fix must not regress: an empty table under a declared target_floor=0
            # must not read as a new defect beyond what the emptiness itself already is), not PASS
            # (nothing here confirms the emptiness is intended, only that a floor was set to 0).
            m["Build.completion"] = dict(
                v=PARTIAL,
                measured=f"rows_written={rw} = live=0 ({basis}; {rec_scope}); target_floor=0 declares zero "
                         "rows complete, but this is a writer-backed data asset (has_writer=true) with no "
                         "layer-plan claim that the emptiness is by design — indistinguishable from a "
                         "writer that has never produced a row")
        else:
            # Consistency (R42), reached for live == 0 only under the target_floor=0 declaration (R52)
            # AND (R99) has_writer=false — no writer at all, the one signal honest enough to read as
            # "empty by design" without inventing a field the registry does not carry.
            m["Build.completion"] = dict(v=PASS, measured=f"rows_written={rw} = live={live} ({basis}; {rec_scope})"
                                         + ("; zero rows declared complete by target_floor=0 (has_writer=false "
                                            "— no writer at all, the signal honest enough to read as by-design)"
                                            if live == 0 else ""))

        # D6 item 2 (W2-2): Earn/Cost are attributed to the latest STARTED build_run_assets attempt at
        # the build record's scope (`_attempt_timing`), and only then graded by the D6 classifier —
        # the attempt linkage wave 1 left unwired (F1; `attempt_linkage_wired=False` until now). With
        # the instrument absent (migration 1094 not applied — production today) both still read
        # NO_DETECTOR "instrument absent", now naming the attempt they would be linked to.
        m["Earn.build_record"], m["Cost.baseline"] = _attempt_timing(
            None if attempts is None else attempts.get(aid, {}), t, rec_scope.split(";")[0], CHART_ID,
            instrument_present, r["has_writer"], era)

        cf = _grade_count_floor(r, live, count_errors.get(aid), ctables)
        if cf is not None:
            m["Count.floor"] = cf

        tbl = r["target_table"]
        reach = None
        dc = {}
        if tbl and tbl in cat["exists"]:
            # R41: each of these four checks queries the target table independently (one of them,
            # on the estate's largest tables, is exactly R40's kala_field timeout case) — a single
            # slow/failing query must degrade only its OWN criterion, never blind the other three.
            try:
                dc = depth_census(tbl, cat["cols"].get(tbl, []))
                if dc.get("note") or not dc.get("rows"):
                    # R222 / N5 (A_REVIEW2 G2): an empty table (or one with no readable columns) has
                    # no column population to measure. It read PASS ("never populated: []" is
                    # vacuously empty), so truncating a table closed its open depth gap.
                    # Non-emptiness is Build.completion's / Count.floor's claim, not depth's.
                    m["Complete.depth"] = dict(v=NO_DET, measured=f"NO_DETECTOR — {dc.get('note') or 'no rows'} "
                                               f"({dc.get('rows', 0)} rows, {dc.get('columns', 0)} cols): column "
                                               "population cannot be measured on no rows")
                else:
                    m["Complete.depth"] = dict(v=(PASS if not dc.get("never") else PARTIAL),
                                               measured=(f"{dc.get('rows',0)} rows, {dc['columns']} cols; "
                                                         f"fully populated {len(dc.get('full',[]))}; NEVER populated "
                                                         f"{dc.get('never',[])}"))
            except Unknown as exc:
                dc = {}
                m["Complete.depth"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            if multi and isinstance(dc.get("rows"), int) and m["Build.completion"]["v"] in (PASS, FAIL):
                # R42: the target table's own rows, stated as context — never the compared figure.
                m["Build.completion"]["measured"] += (f"; target_table {tbl} alone: {dc['rows']} row(s), "
                                                      "whole table — context, not the compared figure")

            keys = cat["keys"].get(tbl, [])
            if keys:
                k = keys[0] if len(keys[0]) > 1 or keys[0][0] != "id" else (keys[1] if len(keys) > 1 else keys[0])
                kd = ", ".join(k)
                try:
                    # R40: `count(*) - count(DISTINCT (cols))` requires a full sort/hash of every row
                    # to materialise BOTH counts and does not scale to the estate's largest table
                    # (kala_field, 10.3M rows; ground truth measured by hand: duplicates = 0 in 47s
                    # against the naive form's >180s). An EXISTS/HAVING duplicate-group probe can
                    # stop at the first violation instead of counting the whole table when one
                    # exists, and never needs the second full DISTINCT pass either way.
                    has_dup = (scalar(f"SELECT EXISTS(SELECT 1 FROM {tbl} GROUP BY {kd} "
                                      "HAVING count(*) > 1)::text") or "f") in ("t", "true")
                    # F9 (A_REVIEW.md): R40's EXISTS probe decides the verdict but dropped the figure
                    # the ledger `_schema` requires ("measured: <figure …>"). The figure is restored —
                    # "N duplicate(s)" means rows beyond the first per key, the same quantity the
                    # pre-R40 `count(*) - count(DISTINCT key)` reported — but it is counted ONLY when
                    # the probe found a duplicate, so the clean case (kala_field) keeps R40's cost. A
                    # count that errors keeps the probe's FAIL and says the figure is missing.
                    if not has_dup:
                        figure = "0 duplicate(s)"
                    else:
                        try:
                            dup_groups, dup_rows = psql(
                                "SELECT count(*)::text, coalesce(sum(n - 1), 0)::text FROM "
                                f"(SELECT count(*) AS n FROM {tbl} GROUP BY {kd} HAVING count(*) > 1) d")[0]
                            figure = f"{dup_rows} duplicate(s) in {dup_groups} duplicate group(s)"
                        except Unknown as exc:
                            figure = f"duplicate group(s) exist; the count errored ({exc})"
                    m["Vocab.identity"] = dict(v=(FAIL if has_dup else PASS),
                                               measured=f"declared key ({kd}): {figure}")
                    if not has_dup:
                        # R222 / N5, same class: "0 duplicates" on a table with NO rows is vacuous —
                        # truncating a table would close its open identity gap. Row count from the
                        # depth census when it ran; otherwise one EXISTS probe.
                        nrows = dc.get("rows")
                        if nrows is None:
                            nrows = 1 if (scalar(f"SELECT EXISTS(SELECT 1 FROM {tbl})::text") or "f") \
                                in ("t", "true") else 0
                        if nrows == 0:
                            m["Vocab.identity"] = dict(v=NO_DET, measured=f"NO_DETECTOR — table empty: uniqueness "
                                                                          f"under ({kd}) is vacuous on 0 rows")
                except Unknown as exc:
                    m["Vocab.identity"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            try:
                ac = alias_census(tbl, cat["cols"].get(tbl, []))
                if ac:
                    bad = {k: v for k, v in ac.items() if v["no_alias"]}
                    # R54 (T1 plant vocab_alias): the verdict saturates — one empty alias set FAILs as
                    # hard as all of them (79/741 -> 741/741 empty moved nothing at verdict level). The
                    # measured fraction is stated in the evidence and carried as `severity` (0.0-1.0,
                    # rows lacking an alias set / rows), so a worsening is visible below the verdict.
                    rows_t = sum(v["rows"] for v in ac.values())
                    empty_t = sum(v["no_alias"] for v in ac.values())
                    frac = (empty_t / rows_t) if rows_t else 0.0
                    m["Vocab.alias"] = dict(v=(PASS if not bad else FAIL),
                                            measured=(f"{len(ac)} class(es); {empty_t}/{rows_t} row(s) lack an alias set "
                                                      f"({frac:.1%}); empty alias sets: "
                                                      + (", ".join(f"{k} {v['no_alias']}/{v['rows']}" for k, v in bad.items()) or "none")),
                                            severity=round(frac, 4))
            except Unknown as exc:
                m["Vocab.alias"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            # R23: field-level reachability of the target table (reported, not graded).
            m["Reach.fields"], reach = _grade_reach(tbl, cat["cols"].get(tbl, []), dc, caps_sql, caps_note, CHART_ID)

            tcols = set(cat["cols"].get(tbl, []))
            # R60: the singular `classical_citation` (as opposed to the plural `classical_citations`)
            # was missing from this list — bg_nakshatra_medical and at least a dozen other L0 tables
            # (bg_avastha_schemes, bg_combustion_orbs, bg_dignity_reference, bg_graha_dik,
            # bg_graha_naisargika_friendship, bg_medical_mappings, bg_motion_state_thresholds,
            # bg_prashna_* x5, bg_shashtiamsha_deities, bg_sign_medical, bg_transit_av_gates,
            # bg_transit_moorti — measured 2026-09-28 via information_schema) carry it and got no
            # Ldgr.source_presence check at all, despite a populated citation column.
            cit = [c for c in CITATION_COLUMNS if c in tcols]
            if cit and dc.get("rows"):
                col = cit[0]
                try:
                    n = scalar(f"SELECT count(*)::text FROM {tbl} WHERE {col} IS NOT NULL")
                    m["Ldgr.source_presence"] = dict(v=(PASS if int(n) == dc["rows"] else PARTIAL),
                                                     measured=f"{col} populated on {n}/{dc['rows']} rows")
                except Unknown as exc:
                    m["Ldgr.source_presence"] = dict(v=ERRORED, measured=f"check errored: {exc}")
        elif tbl:
            m["Complete.depth"] = dict(v=FAIL, measured=f"target_table '{tbl}' does not exist in production")

        # E6.1 (d): every token the asset is served under — target table, asset id, every count_sql table — over every
        # serving root (R23's CAPS_ROOTS, recursive) plus the wider source probe. A table another active asset of this
        # layer also declares is SHARED: it names the table, not this asset, so it never attributes a module.
        dtoks = list(dict.fromkeys([t for t in ([tbl] if tbl else []) + list(ctables) + [aid] if t]))
        cap = capability_scan(CAPS_ROOTS, dtoks, shared=dens_shared, columns=cat["cols"],
                              outside_roots=DENS_OUTSIDE_ROOTS)
        m["Dens.served"] = _grade_dens(cap, tbl or aid)

        # E6 packet (c): the Null and Narr checks (declarations file + catalog + writer scope + tests; fault-isolated)
        if isinstance(prose_decls, DeclarationsError):
            for _c in NARR_CHECKS + NULL_CHECKS:
                m[_c] = dict(v=ERRORED, measured=f"check errored: the declarations file is unreadable ({prose_decls})")
        else:
            try:
                if prose_tests is None and (prose_decls.get(aid) or {}).get("prose_fields"):
                    prose_tests = python_tests()
                m.update(_measure_prose(aid, prose_decls.get(aid), r, files, cat, ctables, dens_shared, prose_tests or (),
                                        prose_vocab))
            except (Unknown, DeclarationsError) as exc:
                for _c in NARR_CHECKS + NULL_CHECKS:
                    m[_c] = dict(v=ERRORED, measured=f"check errored: {exc}")

        h = hist["per"].get(aid)
        if not h:
            if r["has_writer"]:
                m["Build.exercised"] = dict(
                    v=FAIL, measured="registered with a writer and the orchestrator has NEVER run it "
                                     "(no build_run_assets row)")
            else:
                m["Build.exercised"] = _na("never run, and it has no writer — consistent", "never-run-no-writer")
            m["Build.history"] = _na("never run; check 7 owns this", "never-run")
        elif not h.get("executed", 0):
            # C1 (W2-1_REVIEW §2 A8): rows exist but none was ever STARTED (queued leftovers, aborted or
            # BLOCKED before start) — the orchestrator never executed this asset. Not a PASS; the
            # history is still graded (its own zero-completion guard keeps it non-closable).
            if r["has_writer"]:
                m["Build.exercised"] = dict(
                    v=FAIL, measured=f"registered with a writer and the orchestrator has NEVER executed it: "
                                     f"{h['runs']} build_run_assets row(s), none ever started "
                                     f"(states: {h.get('states') or 'n/a'})")
            else:
                m["Build.exercised"] = _na(f"never executed ({h['runs']} unstarted row(s)), and it has no "
                                           "writer — consistent", "never-executed-no-writer")
            m["Build.history"] = _grade_build_history(h)
        else:
            m["Build.exercised"] = dict(
                v=PASS, measured=f"{h['executed']} executed run(s) of {h['runs']} build_run_assets row(s), "
                                 f"scope(s): {', '.join(sorted(h['executed_scopes']))}, last executed "
                                 f"{h['last_executed_when']}")
            m["Build.history"] = _grade_build_history(h)

        m["Build.dep_liveness"] = (_grade_dep_liveness(r["depends_on"], deprec, CHART_ID) if r["depends_on"]
                                   else _na("no declared dependencies", "no-declared-dependencies"))

        m["Complete.width"] = dict(v=NOT_GENERIC, measured="no declared universe for this asset — declaring one is the first width gap")
        m["Carr.detector"] = _run_carriage_detector(aid)
        # E6 item (f): Carr.D1-D3 `no-carriage` candidates, only for an asset that DECLARES terminal_by_construction
        m.update(carr_checks(dict(declared_facts(declarations, aid), blocking_radius=radius.get(aid),
                                  measured_served=m["Dens.served"]["v"])))
        if "Reach.fields" not in m:
            m["Reach.fields"] = dict(v=NOT_GENERIC, measured=("no target table in production to census at field level"
                                                              if tbl else "no target_table declared: no table to census "
                                                                          "at field level"))

        br = radius.get(aid)
        assets.append(dict(asset_id=aid, layer=layer_key, scoring=cfg["scoring"], live_rows=live,
                           reach=reach,
                           blocking_radius=(dict(br, basis="active assets depending on it, transitively, every layer")
                                            if br else dict(transitive=None, direct=None, severity_weight=None,
                                                            basis=radius_note or "unmeasured: not in the active "
                                                                                 "dependency graph")),
                           live_rows_basis=(basis if live is not None else None), count_sql_tables=ctables,
                           target_table=tbl, has_writer=r["has_writer"], writer_files=files,
                           catalog_status=r["catalog_status"],
                           # E6.1 packet 2a: applicability FACTS for the rollup (additive; no measurement reads them)
                           target_columns=_target_columns_fact(tbl, cat),
                           asset_kind=(r["asset_kind"].strip() if isinstance(r["asset_kind"], str) and r["asset_kind"].strip()
                                       else None),
                           # DECLARED, not runnable/meaningful: a true value (even `SELECT 0`, the R46 trap) is no
                           # evidence for Count.floor or Build.completion; it says only that count_sql is non-blank.
                           count_sql_declared=bool((r["count_sql"] or "").strip()),
                           measurements=m))

    extra = sorted(set(regd) - known)
    never = [a["asset_id"] for a in assets if a["measurements"]["Build.exercised"]["v"] == FAIL]
    # R15/R29 (hand_row_provenance.py): `generated` below IS the census_run_id a hand-written gap/
    # opportunity/disposition row is required to carry — no second identifier is invented. Everything
    # MEASURABLE belongs to this function; a hand row records only its judgement plus which run of
    # THIS output it was judged against.
    return dict(generated=dt.datetime.now().astimezone().isoformat(timespec="seconds"), layer=layer_key,
                layer_name=cfg["name"], scoring=cfg["scoring"], n_assets=len(assets),
                # R220: the population this census measured, stated explicitly — `n_assets` above IS
                # the active population (`registry()` already excludes inactive/dead rows), but the
                # gap between it and the layer's raw registry row count must never be silent.
                population_active=population["active"], population_registry_total=population["registry_total"],
                population_excluded_inactive=population["excluded_inactive"],
                # R231: the chart every `$1` count_sql was bound to, and how many were.
                chart_scope=CHART_ID,
                chart_scoped_count_sql=sum(1 for r in reg_all.values() if _chart_scoped(r["count_sql"])),
                # E1.9/F4: a scoped run's build history covers the scoped ids only, so its layer-wide run counts would
                # describe the scope, not the layer — omitted there (the unscoped key order and values are unchanged).
                **({} if assets_sel is not None else dict(global_runs=hist["global_runs"],
                                                          global_runs_touching_layer=hist["global_with_layer"])),
                never_exercised_with_writer=never,
                registered_ids=len(regd), registry_has_writer=sum(1 for r in reg_all.values() if r["has_writer"]),
                phantom_registered=extra, local_map_candidates=lmaps, assets=assets,
                **({} if assets_sel is None else dict(scope=dict(assets=assets_sel, partial=True))))


# D4 ruling (DECISIONS_RECOMMENDATIONS_v2_0.md): the verdict a check can return keeps growing
# (NOT_GENERIC today; R41's per-check fault isolation adds an "errored" state; an unmeasured
# criterion is silently absent from `measurements` and never reaches this function at all). A
# gap closes on an EXPLICIT allowlist, never on "whatever isn't in the failing tuple" — the sandbox
# port's own defect (D4 finding #6): closing on "any other verdict" would close on NOT_GENERIC too.
CLOSABLE = (PASS, NA)
FAILING = (FAIL, PARTIAL, NO_DET)
# A gap row's own state vocabulary (asset_gaps.jsonl `_schema`): OPEN and IN_PROGRESS are both
# live/unresolved (D4: "an IN_PROGRESS row transitions on PASS" exactly like an OPEN one); CLOSED
# is resolved; anything else (WITHDRAWN, or a state string this script has never written) is left
# alone rather than re-opened by inference.
LIVE_GAP_STATES = ("OPEN", "IN_PROGRESS")


def _na_released(crit: str, rec: dict) -> bool:
    """May this measured record CLOSE a gap? True only for a verdict PASS, or for an N/A whose cause is a
    registered cause of `crit` (NA_CAUSES) AND whose rule id `<crit>#measured:<cause>` is declared in
    NA_RULE_DECISIONS — the same release the rollup applies (`_check_contribution`). Any other N/A (no cause, a
    malformed or unregistered cause, a registered cause no rule declares) is what the rollup reads NO_DETECTOR,
    and closing a ledger row on it would record a closure the cell itself refuses (CLAUDE.md §N.8)."""
    v = rec.get("v")
    if v == PASS:
        return True
    if v != NA:
        return False
    cause = rec.get("cause")
    if not (isinstance(cause, str) and _CAUSE_SLUG.fullmatch(cause)):
        return False
    return cause in NA_CAUSES.get(crit, ()) and f"{crit}#measured:{cause}" in NA_RULE_DECISIONS


def _emit_scope(census: dict, assets) -> frozenset | None:
    """The set of asset ids emit_gaps may write rows for, or None (every asset of the census: an unscoped run).
    Raises ScopeError — before the ledger is touched — on a malformed label, a census that contradicts its own
    label, an empty / duplicate / non-string `assets`, or an `assets` entry the census did not measure."""
    label = census_scope(census)
    present = {a["asset_id"] for a in census["assets"]}
    scope = None
    if label is not None:
        scope = frozenset(label["assets"])
        stray = sorted(present - scope)
        if stray:
            raise ScopeError(f"the census is labelled scoped to {sorted(scope)} but holds measurements for "
                             f"{', '.join(stray)}: refusing to emit (nothing written)")
    if assets is not None:
        want = list(assets)
        if not want or len(set(want)) != len(want) or any(not isinstance(x, str) or not x for x in want):
            raise ScopeError(f"emit scope must be a non-empty list of distinct asset ids, got {want!r}")
        unmeasured = sorted(set(want) - present)
        if unmeasured:
            raise ScopeError(f"emit scope names asset(s) this census did not measure: {', '.join(unmeasured)}")
        scope = frozenset(want) if scope is None else scope & frozenset(want)
    return scope


def emit_gaps(census: dict, assets=None) -> tuple[int, int, int, int]:
    """Append-only ledger with deterministic ids (`<asset>-<criterion>`), closing by measurement.

    D4 ruling (R57 amended), each an acceptance case with its own test in
    __tests__/test_a2_emit_gaps_closure.py:

    - CLOSED only on `PASS` or an explicitly justified `N/A` — never on `NOT_GENERIC`, `UNKNOWN`,
      an errored check, or an unmeasured criterion (i.e. anything outside CLOSABLE is a no-op,
      not an implicit close). "Explicitly justified" is `_na_released`: a registered cause AND a declared
      `<crit>#measured:<cause>` rule. Any other N/A is treated exactly like the rollup's NO_DETECTOR: it
      does not close, it opens (or keeps open) a NO_DETECTOR-type gap whose `what` names why it was not released.
    - check failing (FAIL/PARTIAL/NO_DETECTOR), no row with this gap_id yet     -> append OPEN
    - check failing, latest row OPEN or IN_PROGRESS                            -> skip (already open)
    - check failing, latest row CLOSED                                        -> append OPEN
      ("RE-OPENED by measurement" — the defect regressed; a loop that only counts up is not a loop)
    - check failing, latest row WITHDRAWN (or any other terminal state this script never wrote)
      -> nothing to do; WITHDRAWN is a terminal, human decision (F4, A_REVIEW.md) and is "left
      alone rather than re-opened by inference" exactly as documented below — the code used to
      contradict this comment by re-opening WITHDRAWN rows too.
    - check closable (PASS/N-A) now, latest row OPEN or IN_PROGRESS            -> append CLOSED
      (closure BY MEASUREMENT: the same detector now passes; the row quotes the new measured value)
    - check closable, latest row CLOSED or no row                             -> nothing to do
    - a row carrying `superseded_by` (R80) is a dead identity — never touched, never resurrected,
      regardless of what the census currently measures for that gap_id, and regardless of any
      LATER row for the same gap_id that omits the flag (F5, A_REVIEW.md): once superseded, always
      superseded — the flag is checked across the id's whole history, not only its latest row.
    - hand `change`/`owner`/`gate` are CARRIED FORWARD from the prior row onto every transition
      row (CLOSED or RE-OPENED); only a gap_id's very first OPEN row uses the census's own
      defaults, because there is no prior hand annotation yet to carry.
    Rows whose gap_id is not a deterministic `<asset>-<criterion>` id (hand-written rows with no
    detector binding, R58) are never touched by this function at all — no census criterion will
    ever produce that gap_id, so `latest` simply never matches them.

    LIMIT (F12, A_REVIEW.md item 4 — disclosed, not detected): "latest" means last in FILE order,
    not by `ts`. For one append-only file that is the truth. A git merge of two branches that both
    appended to the ledger concatenates their rows in merge order, so a stale CLOSED can land after a
    newer OPEN for the same gap_id and be read as current. Neither this function nor the tracker
    detects that; re-running the census after such a merge re-measures and appends the correct
    transition.

    SCOPE (E1.9). A census carrying `scope` (a scoped measure()), and/or `assets=[...]`, restricts the emit to those
    assets: no row of any other asset is read for a decision, appended, closed, withdrawn or reopened, and the file
    is only ever APPENDED to, so every pre-existing row stays byte-identical and in order. The scope is checked
    before the ledger is opened: a census whose assets contradict its own scope label, an `assets` entry the census
    never measured, an empty list or a malformed label raises ScopeError and writes nothing.
    """
    scope = _emit_scope(census, assets)
    validate_na_rule_decisions()
    path = CTRL / "asset_gaps.jsonl"
    latest: dict[str, dict] = {}
    # F5 (A_REVIEW.md, non-blocking correction): `superseded_by` must be a PERMANENT flag on the
    # identity, not just a property of whichever row happens to be latest. Checking only
    # `latest.get(gid)` meant a superseded id could be resurrected the instant any later row
    # (hand-written or otherwise) omitted the flag — demonstrated: an early superseded_by row
    # followed by a later plain row re-opened/re-closed the "dead" id. `ever_superseded` is set
    # once any row for a gid ever carried the flag, and stays set regardless of what follows.
    ever_superseded: set[str] = set()
    if path.exists():
        for ln in path.read_text(encoding="utf-8").split("\n"):
            if ln.strip():
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if r.get("gap_id"):
                    latest[r["gap_id"]] = r  # append-only: last row for an id wins
                    if r.get("superseded_by"):
                        ever_superseded.add(r["gap_id"])
    ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    added = skipped = closed = reopened = 0
    with path.open("a", encoding="utf-8") as f:
        for a in census["assets"]:
            if scope is not None and a["asset_id"] not in scope:
                continue  # E1.9: an asset outside the scope is never decided about, never written
            for crit, res in a["measurements"].items():
                v = res["v"]
                if v not in FAILING and v not in CLOSABLE:
                    continue  # NOT_GENERIC / UNKNOWN / errored / anything future: never a transition
                if v == NA and not _na_released(crit, res):
                    # §N.8: the ledger records closure, so it may not honour an N/A the rollup refuses.
                    res = dict(res, measured=f"NO_DETECTOR — measured N/A not released by a declared rule "
                                             f"(cause={res.get('cause')!r}): {res['measured']}")
                    v = NO_DET
                gid = f"{a['asset_id']}-{crit}"
                prior = latest.get(gid)
                if gid in ever_superseded:
                    continue  # a superseded id is never resurrected, whatever is measured now,
                              # and whatever any LATER row (with no superseded_by of its own) says
                prior_state = (prior or {}).get("state", "OPEN").upper()
                # Carry hand metadata forward; only the very first OPEN row for a gid has none
                # to carry, so it alone falls back to the census's own defaults.
                change = prior.get("change", "") if prior else ""
                owner = prior.get("owner", "asset_census") if prior else "asset_census"
                gate = prior.get("gate", "this asset's certification") if prior else "this asset's certification"
                # R21: a Build gap carries its asset's blocking radius as its severity — measured by this
                # census run, never carried from a prior row (the DAG moves) and never invented (an
                # unmeasured radius is null with its reason, not 0).
                sev = {}
                if crit.startswith("Build.") and isinstance(a.get("blocking_radius"), dict):
                    br = a["blocking_radius"]
                    sev = dict(blocking_radius=br.get("transitive"), severity_weight=br.get("severity_weight"))
                    if br.get("transitive") is None:
                        sev["blocking_radius_note"] = br.get("basis", "unmeasured")
                if v in FAILING:
                    if prior is None:
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"measured: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="OPEN", ts=ts, **sev), ensure_ascii=False) + "\n")
                        added += 1
                    elif prior_state in LIVE_GAP_STATES:
                        skipped += 1
                    elif prior_state == "CLOSED":  # regression re-opens
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"RE-OPENED by measurement: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="OPEN", ts=ts, **sev), ensure_ascii=False) + "\n")
                        reopened += 1
                    else:
                        # F4 (A_REVIEW.md): WITHDRAWN (or any other terminal state this script
                        # never assigned) is a human, out-of-band decision — left alone rather than
                        # re-opened by inference, matching this function's own documented contract.
                        skipped += 1
                else:  # v in CLOSABLE
                    if prior is not None and prior_state in LIVE_GAP_STATES:
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"CLOSED by measurement: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="CLOSED", ts=ts, **sev), ensure_ascii=False) + "\n")
                        closed += 1
                    # else: no prior, or prior already CLOSED/terminal — nothing to do (idempotent)
    return added, skipped, closed, reopened


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="L0")
    ap.add_argument("--emit-gaps", action="store_true")
    ap.add_argument("--rollup", action="store_true",
                    help="also write the nine-gate cells per asset (key `rollup`) and the non-nine gates as "
                         "information (key `rollup_excluded`) into --out; --emit-gaps neither reads nor changes it")
    ap.add_argument("--assets", action="append", default=None, metavar="ID[,ID...]|@FILE",
                    help="E1.9: measure (and, with --emit-gaps, emit for) ONLY these assets — a comma list, a repeated "
                         "flag, or @file. Every id must be an active registry asset of the selected layer(s). The census "
                         "is labelled SCOPED/partial (`scope`), is written to asset_census_scoped.json unless --out names "
                         "another file, and never replaces the full census file. Exit 6 on a bad scope; nothing is written.")
    ap.add_argument("--out", default=None, help="default: <control>/asset_census.json (scoped: asset_census_scoped.json)")
    a = ap.parse_args()
    keys = list(LAYERS) if a.layer.lower() == "all" else [k.strip().upper() for k in a.layer.split(",")]
    for k in keys:
        if k not in LAYERS:
            sys.exit(f"unknown layer {k}; expected one of {list(LAYERS)} or 'all'")

    full_out = CTRL / "asset_census.json"
    by_layer = None
    if a.assets is not None:
        try:
            by_layer = validate_scope(parse_assets_arg(a.assets), keys)
        except ScopeError as exc:
            print(f"asset_census: scope error — {exc}", file=sys.stderr)
            return EXIT_SCOPE
        except Unknown as exc:
            print(f"asset_census: UNKNOWN — cannot validate --assets against the registry: {exc}")
            return 4
        keys = [k for k in keys if k in by_layer]
    out_path = a.out if a.out is not None else str(CTRL / "asset_census_scoped.json" if by_layer is not None else full_out)
    if by_layer is not None and _is_full_census_path(out_path, full_out):
        print(f"asset_census: scope error — the scoped output path {out_path} is the full census file (same file, "
              "case variant, hardlink or symlink): a scoped (partial) census never replaces the full census — name "
              "another --out", file=sys.stderr)
        return EXIT_SCOPE

    out, worst = {}, 0
    for k in keys:
        try:
            c = measure(k) if by_layer is None else measure(k, assets=by_layer[k])
        except ScopeError as exc:
            print(f"asset_census: scope error — {exc}", file=sys.stderr)
            return EXIT_SCOPE
        except Unknown as exc:
            print(f"asset_census: UNKNOWN — layer {k}: {exc}")
            print("  Nothing is reported clean: an unreachable instrument is not a passing result.")
            print("  R41 isolates per-asset checks only; a failed layer-wide read leaves this whole layer "
                  f"unmeasured{' and stops every layer after it (no census file written)' if len(keys) > 1 else ''}.")
            return 4
        out[k] = c
        if by_layer is not None:
            print(f"{k} SCOPED RUN — partial census, not a layer census: {c['n_assets']} of "
                  f"{c['population_active']} active assets ({', '.join(c['scope']['assets'])})")
        fails = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] == FAIL)
        parts = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] in (PARTIAL, NO_DET))
        errored = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] == ERRORED)
        print(f"{k} {c['layer_name']} ({c['scoring']}): {c['n_assets']} assets · "
              f"{c['registered_ids']} registered ids vs {c['registry_has_writer']} has_writer=true")
        if c["population_registry_total"] != c["population_active"]:
            print(f"  population: {c['population_active']} active of {c['population_registry_total']} registry "
                  f"rows for this layer — excluded (inactive/dead): "
                  f"{', '.join(x['asset_id'] for x in c['population_excluded_inactive'])}")
        if c.get("chart_scoped_count_sql"):
            print(f"  chart scope: {c['chart_scoped_count_sql']} chart-scoped count_sql bound to chart {c['chart_scope']}")
        if "global_runs" in c:   # absent in a scoped census (F4): never stated about the layer from scoped-only data
            print(f"  build scope: {c['global_runs']} global run(s), of which {c['global_runs_touching_layer']} "
                  f"touched this layer" + ("  ← the global path never exercises it" if c['global_runs_touching_layer'] == 0 else ""))
        if c["never_exercised_with_writer"]:
            print(f"  !! registered with a writer and NEVER run by the orchestrator: {c['never_exercised_with_writer']}")
        if c["phantom_registered"]:
            print(f"  !! registered but absent from the registry: {c['phantom_registered']}")
        print(f"  FAIL {fails} · PARTIAL/NO_DETECTOR {parts} · ERRORED {errored} · assets measured {c['n_assets']}")
        if errored:
            print(f"  !! {errored} check(s) errored (R41: degraded, not layer-aborting) — "
                  "never counted as PASS; see each asset's measurements for the exception")
        by = {}
        for x in c["assets"]:
            for crit, r in x["measurements"].items():
                if r["v"] == FAIL:
                    by.setdefault(crit, []).append(x["asset_id"])
        for crit in sorted(by):
            n = by[crit]
            print(f"    FAIL {crit}: {len(n)} — {', '.join(n[:6])}{'…' if len(n) > 6 else ''}")
        worst = max(worst, 2 if fails else (3 if (parts or errored) else 0))
        if a.emit_gaps:
            added, skipped, closed, reopened = emit_gaps(c)
            print(f"  ledger: {added} row(s) appended, {skipped} already present, "
                  f"{closed} closed by measurement, {reopened} re-opened")

    rollup_error = None
    if a.rollup:
        # computed AFTER measuring and emit_gaps, from the finished census; never fed to emit_gaps. A rollup
        # failure must not lose the measurements: they are written without a `rollup` key and the run exits 5
        # (overriding any measured worst of 2/3; the stderr message names the measured exit).
        try:
            out = {**out, **build_rollup_output(out)}
        except Exception as exc:  # noqa: BLE001
            rollup_error = f"{type(exc).__name__}: {exc}"
            print(f"asset_census: rollup failed — {rollup_error} (census written without a rollup; measured exit "
                  f"{worst} overridden by 5)", file=sys.stderr)
    if by_layer is not None:    # E1.9: the file header says it is partial, before any layer is read
        out = {"scope": dict(assets=sorted(x for k in keys for x in by_layer[k]), partial=True, layers=list(keys)), **out}
    text = json.dumps(out, indent=1, default=str) + "\n"
    if by_layer is not None:
        _write_atomic(out_path, text)       # E1.9: a scoped file is never torn by a crash or a concurrent scoped run
    else:
        Path(out_path).write_text(text, encoding="utf-8")
    print(f"census written: {os.path.relpath(out_path, ROOT)}" + (" (SCOPED: partial census)" if by_layer is not None else ""))
    if rollup_error:
        return 5
    return worst


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"asset_census: script error — {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
