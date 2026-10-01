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
  Build.target          target_table declared, or the asset is a declared service / multi-table
  Build.dag             every depends_on entry exists; no cycle inside the layer
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
  asset_census.py --layer L0 --rollup        also write the nine-gate cells per asset (key `rollup`) and the
                                             non-nine gates as information (`rollup_excluded`) into the census JSON
Exit: 0 clean · 2 failures measured · 3 only NOT_GENERIC/undeclared items · 4 unknown · 5 script error, or
      --rollup failed (census still written, without it; the measured exit is named on stderr, never lost).
"""

from __future__ import annotations

import argparse
import ast
import bisect
import datetime as dt
import json
import os
import re
import subprocess
import sys
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
    "Build.target":          dict(gate="Build", check="target",          applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.dag":             dict(gate="Build", check="dag",              applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.count_integrity": dict(gate="Build", check="count_integrity", applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.completion":      dict(gate="Build", check="completion",       applicability="a count_sql or view target exists", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2),  # R99 bumped: a writer-backed empty table under target_floor=0 now reads PARTIAL, not the R52-era blanket PASS
    "Build.exercised":       dict(gate="Build", check="exercised",        applicability="always",                detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.history":         dict(gate="Build", check="history",          applicability="has been exercised at least once", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Build.dep_liveness":     dict(gate="Build", check="dep_liveness",     applicability="declares at least one depends_on", detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
    "Idem.pattern":          dict(gate="Idem",  check="pattern",          applicability="has_writer=true",       detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),
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
    "Build.exercised": ("never-run-no-writer", "never-executed-no-writer"),
    "Build.history": ("never-run",),
    "Build.dep_liveness": ("no-declared-dependencies",),
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
REGISTRY_REVISION = 4     # 4: Dens.served rev 4 (contract AND a tier column in the served select; structural; cause no-served-surface). 3: NA_CAUSES gains Earn.build_record:no-registered-writer (E6 review fix 2). 2: N/A rule ids are cause-keyed (<criterion>#measured:<cause>); NA_CAUSES joins the content


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
        return dict(criterion=crit, v=v, state="MEASURED", reason="measured")
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
            if not isinstance(tbc, str) or not tbc.strip() or tbc != tbc.strip():
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
    if isinstance(tbc, str) and tbc.strip():
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
    if declarations is None:
        full = set(census_by_layer) == set(ALL_LAYERS)   # the id check needs the whole registry set, never a partial run
        ids = [a["asset_id"] for c in census_by_layer.values() for a in c["assets"]] if full else None
        declarations = load_asset_declarations(registry_ids=ids)
    for k, c in census_by_layer.items():
        layers[k] = rollup_census(c, {a["asset_id"]: facts_for_asset(a, declarations) for a in c["assets"]})
        excluded[k] = {a["asset_id"]: rollup_excluded(c["layer"], a["measurements"]) for a in c["assets"]}
    return dict(rollup=dict(registry_revision=REGISTRY_REVISION, registry_fingerprint=registry_fingerprint(),
                            layers=layers),
                rollup_excluded=excluded)


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
    exist under the python sidecar; third-party imports resolve to nothing."""
    out: dict[str, tuple[Path, str | None]] = {}

    def mod_file(base: Path, parts: list[str]) -> Path | None:
        for cand in (base.joinpath(*parts).with_suffix(".py") if parts else None,
                     base.joinpath(*parts, "__init__.py")):
            if cand is not None and cand.is_file():
                return cand
        return None

    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            base = SIDECAR if not n.level else here.parents[n.level - 1]
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
        reasons.append(f"the asset's own table(s) are only UPDATEd in place: {cite(own['update'])} — no row is added, "
                       "but whether a rebuild re-derives every row is not measured")
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
    return dict(exists=exists | views, cols=cols, keys=keys, views=views)


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


def measure(layer_key: str) -> dict:
    """Measure one layer.

    R41 SCOPE LIMIT (F12, A_REVIEW.md — disclosed, not fixed). R41 isolates PER-ASSET checks: one
    asset's failing check degrades only that criterion to ERRORED. The LAYER-WIDE reads below —
    `registry`, `catalog`, `registered_ids` (the writer scan), `throughput`, `build_history` — are
    not isolated: any of them raising `Unknown` still aborts the whole layer (exit 4, nothing reported
    clean), and under `--layer all` it also stops every layer after it, with no census file written.
    That is fail-closed, never a false PASS, but it is a whole-layer blind spot, not a degraded one.
    (`live_counts` isolates per asset itself — F2; `duration_instrument_present` degrades to
    `instrument unreachable` — D6 item 1.)"""
    cfg = LAYERS[layer_key]
    reg, population = _layer_read("registry", registry, layer_key)
    cat = _layer_read("catalog", catalog, [r["target_table"] for r in reg.values()])
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
        radius, radius_note = blocking_radius(dependency_graph()), None
    except Unknown as exc:
        radius, radius_note = {}, f"unmeasured: the dependency read failed ({exc})"
    # R23: every capability module's SQL, read once per layer run.
    try:
        caps_sql, caps_note = capability_sql(), None
    except Unknown as exc:
        caps_sql, caps_note = None, str(exc)

    known = set(reg)
    # E6.1 (d): a table (target or count_sql) that MORE THAN ONE active asset of this layer declares is shared.
    # Disclosed limit: only this layer's registry is read here; every share in the estate today sits inside one layer.
    _decl: dict[str, set[str]] = {}
    for _aid, _r in reg.items():
        for _t in ([_r["target_table"]] if _r["target_table"] else []) + _count_tables(_r["count_sql"]):
            _decl.setdefault(_t, set()).add(_aid)
    dens_shared = frozenset(t for t, who in _decl.items() if len(who) > 1)
    owners: dict = {}                                     # R53: read lazily, at most once per layer
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
        if r["target_table"]:
            m["Build.target"] = dict(v=PASS, measured=f"target_table={r['target_table']}")
        elif r["asset_kind"] == "service" or not r["has_writer"]:
            m["Build.target"] = _na(f"no target_table; asset_kind='{r['asset_kind']}', has_writer={r['has_writer']}",
                                    "service-no-target-table" if r["asset_kind"] == "service" else "no-writer-no-target-table")
        else:
            try:
                # R242 (W2-2 OS-B): `owners.setdefault("map", target_owners())` evaluated its argument —
                # the registry-wide read — on EVERY call, whatever the cache held. Read it only when absent.
                m["Build.target"] = _grade_target_less(
                    r, lambda: owners["map"] if "map" in owners else owners.setdefault("map", target_owners()))
            except Unknown as exc:
                m["Build.target"] = dict(v=ERRORED, measured=f"check errored: {exc}")

        missing = [d for d in r["depends_on"] if d not in known and not d.startswith(cfg["prefix"]) is False]
        unknown_deps = [d for d in r["depends_on"] if d.startswith(cfg["prefix"]) and d not in known]
        m["Build.dag"] = dict(v=(FAIL if unknown_deps else PASS),
                              measured=(f"depends_on references unknown {cfg['prefix']}* assets: {unknown_deps}"
                                        if unknown_deps else f"{len(r['depends_on'])} edge(s), all resolvable"))

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
                                                         "Build.history")
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
                chart_scoped_count_sql=sum(1 for r in reg.values() if _chart_scoped(r["count_sql"])),
                global_runs=hist["global_runs"], global_runs_touching_layer=hist["global_with_layer"],
                never_exercised_with_writer=never,
                registered_ids=len(regd), registry_has_writer=sum(1 for r in reg.values() if r["has_writer"]),
                phantom_registered=extra, local_map_candidates=lmaps, assets=assets)


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


def emit_gaps(census: dict) -> tuple[int, int, int, int]:
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
    """
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
    ap.add_argument("--out", default=str(CTRL / "asset_census.json"))
    a = ap.parse_args()
    keys = list(LAYERS) if a.layer.lower() == "all" else [k.strip().upper() for k in a.layer.split(",")]
    for k in keys:
        if k not in LAYERS:
            sys.exit(f"unknown layer {k}; expected one of {list(LAYERS)} or 'all'")

    out, worst = {}, 0
    for k in keys:
        try:
            c = measure(k)
        except Unknown as exc:
            print(f"asset_census: UNKNOWN — layer {k}: {exc}")
            print("  Nothing is reported clean: an unreachable instrument is not a passing result.")
            print("  R41 isolates per-asset checks only; a failed layer-wide read leaves this whole layer "
                  f"unmeasured{' and stops every layer after it (no census file written)' if len(keys) > 1 else ''}.")
            return 4
        out[k] = c
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
    Path(a.out).write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"census written: {os.path.relpath(a.out, ROOT)}")
    if rollup_error:
        return 5
    return worst


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"asset_census: script error — {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
