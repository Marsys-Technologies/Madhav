#!/usr/bin/env python3
"""check_asset_catalogue_contract.py — the Nirmāṇa M0 catalogue-conformance guard.

Nirmāṇa autonomous campaign, WORK_QUEUE id **M0-T9**. Implements
`00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md` §6/§8 — its 28 numbered
rules C-01…C-28 — plus five campaign-extension assertions X-01…X-05 that the M0 exit
criteria (`NIRMANA_ELEVATION_PLAN_v4_0.md` §14.1) name but the contract document does
not number.

Built to the shape of `check_earned_signal.py` and `check_fact_category_pinning.py`:
bundled PASS/FAIL fixtures + `--self-test`, a disclosed-residuals JSON, `--json`, and a
declared exit-code policy. Stdlib-only in every mode except `--live`, which needs
`psycopg`.

============================================================================
THE THREE-VALUED OUTPUT, AND WHY IT IS THE POINT
============================================================================
Every rule reports exactly one of:

  pass           a detector ran, over data that exists, and found zero violations
  fail           a detector ran and found violations (they are listed)
  not_checkable  the detector exists but the column or the data it needs does not

`not_checkable` is NEVER collapsed into `pass`. This is CLAUDE.md §N.8 applied to this
script itself: a rule whose input column is absent has produced no verdict, and a
dashboard that renders "no verdict" as green is the exact defect the Nirmāṇa campaign
exists to remove. The contract document says so in its own words about C-25/C-26/C-27:

    "Rules C-25, C-26 and C-27 must never be reported as passing. They have no
     detector. Under CLAUDE.md §N.8 a rule with no detector is null, not green; a CI
     guard implementing this document emits them as `not_checkable` with the reason,
     and a dashboard that renders that as a pass is itself a defect."

Those three are hard-wired NOT_CHECKABLE here and the contract cross-check (below)
independently asserts they are.

**Partial evaluation may prove `fail`; it may never prove `pass`.** Several rules are
conjunctions where one conjunct is checkable and another is not (C-04: "target_table
NOT NULL *and* the table exists" — the NULL half needs no catalogue of tables, the
existence half does). Such a rule returns `fail` if the checkable half found
violations, and `not_checkable` otherwise. It never returns `pass` on half an answer.

============================================================================
THE CONTRACT CROSS-CHECK — why the guard cannot drift from the spec
============================================================================
The rule ids and their severities are not transcribed into this file as constants and
left to rot. At every run (including `--self-test`) the guard parses the contract
document's own §6 table and asserts:

  * every C-* id in the document has an implementation here,
  * every C-* implemented here appears in the document,
  * the severity implemented here equals the severity the document states,
  * every rule the document's §6 table marks "not checkable" is implemented as a
    hard NOT_CHECKABLE rule.

A mismatch is a guard-level ERROR (exit 3), not a rule failure: it means the spec and
the guard have diverged and neither can be trusted until a human reconciles them. The
X-* extension rules are declared here, are explicitly NOT contract rules, and are
excluded from the cross-check by construction (they carry an `origin` field naming the
plan section they come from).

============================================================================
ROW SOURCES
============================================================================
The rules run over a *snapshot* — a plain JSON document with this shape:

    {
      "_meta": {...},                 # provenance; never contains a credential
      "registry_columns": [...],      # the columns asset_registry ACTUALLY has
      "public_tables": [...] | null,  # null ⇒ table-existence conjuncts not checkable
      "assets": [ {col: value, ...} ],
      "throughput": [ {asset_id, throughput_rows, states, ...} ] | null,
      "writer_substep_truth": {asset_id: bool} | null,   # DECLARED, not authoritative
      "zero_consumer_packets": {...} | null,
      "build_run_assets": [ {asset_id, state: "complete"} ] | null,   # X-06's key:
                                     # DISTINCT asset_id with ≥1 COMPLETE run, only
      "build_run_asset_ids_all": [ asset_id, ... ] | null,   # X-07's key: the FULL
                                     # DISTINCT asset_id population from
                                     # build_run_assets, every state — deliberately a
                                     # separate, wider key from the one above
      "frozen_rungs": [...]
    }

`writer_substep_truth` is the one field in that document that is NOT trusted. C-23
derives the writer-class truth by parsing the writer classes AT RUN TIME (M0-T25;
ADHIKĀRIN D-25 part 3), because a truth read from a checked-in artifact is only as
current as the last regeneration of that artifact and will report PASS on a
divergence that appeared afterwards. The declared map is kept, ignored, and reported
on: C-23's `detail` says whether it has gone stale against the code. Bundled
self-test fixtures are the sole exception — their registries are imaginary, so their
declared map is the only truth that could exist for them, and that path is reachable
only from `--self-test`.

Three ways to obtain one:

  --self-test              bundled fixtures under asset_catalogue_fixtures/{pass,fail}/
  --snapshot <path>        a committed, dated snapshot of the live registry
  --live                   read production directly (READ-ONLY; needs psycopg +
                           DATABASE_URL from platform/.env.local, which is never
                           printed, logged or written to any output — charter P4)

CI runs the first two. `--live` is deploy/operator tooling and is deliberately NOT
wired into CI, for the same reason `msr_referential_integrity.py --live` and
`registry_parity_gate.py --live` are not: GitHub Actions has no production DB. Stated
plainly so nobody reads a green CI as a statement about the live catalogue — it is a
statement about the detector, plus a statement about the dated snapshot.

============================================================================
WHAT THIS GUARD DOES NOT DO
============================================================================
 1. It does not check that any `integrity_check_sql` is *satisfied*. §4.7 item 5 is
    explicit: "No CI guard may assert this field is satisfied — only the gate engine's
    run does that, and only against a live build." C-22 checks presence, nothing more.
 2. It does not repair anything. It reads. Every repair is a rung's stage-2 work.
 3. It does not certify. It reports observations (I16/H7).
 4. A `pass` from a rule is a statement about that rule's predicate over the snapshot
    it was given, and nothing wider.

Exit codes
  0  no BLOCKING or RUNG rule failed (RESIDUAL/ADVISORY failures may still be printed)
  1  at least one BLOCKING or RUNG rule failed
  2  bad usage / snapshot unreadable
  3  guard-level error: the guard and the contract document disagree, or a self-test
     expectation was not met
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import inspect
import json
import pathlib
import re
import sys
import tempfile
from typing import Any, Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / "00_ARCHITECTURE" / "control" / "ASSET_CATALOGUE_CONTRACT_v1_0.md"
CONTROL = REPO_ROOT / "00_ARCHITECTURE" / "control"
HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE / "asset_catalogue_fixtures"
RESIDUALS_PATH = HERE / "asset_catalogue_disclosed_residuals.json"
COWRITERS_PATH = HERE / "asset_catalogue_declared_cowriters.json"
BASELINE_SNAPSHOT = HERE / "asset_catalogue_baseline_20260823.json"
UNEARNED_LIT_FLOOR_PATH = HERE / "unearned_lit_floor.json"
LINEAGE_MANIFEST_PATH = HERE / "asset_id_lineage_manifest.json"
DECISIONS_PATH = REPO_ROOT / "00_ARCHITECTURE" / "autonomy" / "state" / "DECISIONS.jsonl"
MIGRATIONS_DIR = REPO_ROOT / "platform" / "migrations"

PASS = "pass"
FAIL = "fail"
NOT_CHECKABLE = "not_checkable"

BLOCKING = "BLOCKING"
RUNG = "RUNG"
ADVISORY = "ADVISORY"
RESIDUAL = "RESIDUAL"          # X-* only: detected and reported, never gates

EXIT_RELEVANT = (BLOCKING, RUNG)

LAYER_PREFIX = {
    "brahmagyan": "bg_", "ganita": "ga_", "bodha": "bo_",
    "kala": "ka_", "phala": "ph_", "mimamsa": "mi_",
}
LAYER_INDEX = {
    "brahmagyan": "L0", "ganita": "L1", "bodha": "L2",
    "kala": "L3", "phala": "L4", "mimamsa": "L5",
}
LAYER_NAME = {
    "brahmagyan": "Brahmagyan", "ganita": "Gaṇita", "bodha": "Bodha",
    "kala": "Kāla", "phala": "Phala", "mimamsa": "Mīmāṃsā",
}
LAYER_RUNG = {
    "brahmagyan": "R0", "ganita": "R1", "bodha": "R2",
    "kala": "R3", "phala": "R4", "mimamsa": "R5",
}
SCOPE_DOMAIN = {"global": "shared", "per_chart": "chart"}
KIND_TYPE_OK = {("data", "data"), ("artifact", "data"), ("service", "service"),
                ("source", "data")}
DATA_KINDS = ("data", "artifact")


# ─────────────────────────────────────────────────────────────────────────────
# Result plumbing
# ─────────────────────────────────────────────────────────────────────────────
class Result:
    __slots__ = ("status", "violations", "reason", "detail")

    def __init__(self, status: str, violations: list | None = None,
                 reason: str | None = None, detail: dict | None = None):
        assert status in (PASS, FAIL, NOT_CHECKABLE), status
        self.status = status
        self.violations = violations or []
        self.reason = reason
        self.detail = detail or {}

    def as_dict(self) -> dict:
        return {"status": self.status, "violation_count": len(self.violations),
                "violations": self.violations, "reason": self.reason,
                "detail": self.detail}


def verdict(violations: list, blocked: list[str] | None = None,
            detail: dict | None = None) -> Result:
    """Partial evaluation: a fail is sound on half the evidence; a pass is not."""
    blocked = [b for b in (blocked or []) if b]
    if violations:
        return Result(FAIL, violations,
                      ("; ".join(blocked) + " (rule is a conjunction; the checkable "
                       "half already found violations)") if blocked else None,
                      detail)
    if blocked:
        return Result(NOT_CHECKABLE, [], "; ".join(blocked), detail)
    return Result(PASS, [], None, detail)


class Rule:
    def __init__(self, rid: str, severity: str, statement: str,
                 fn: Callable[["Snapshot"], Result], origin: str = "contract"):
        self.id = rid
        self.severity = severity
        self.statement = statement
        self.fn = fn
        self.origin = origin


# ─────────────────────────────────────────────────────────────────────────────
# Snapshot
# ─────────────────────────────────────────────────────────────────────────────
class Snapshot:
    def __init__(self, raw: dict, synthetic: bool = False):
        self.raw = raw
        # `synthetic` is set ONLY by the bundled self-test loader. A self-test fixture
        # describes an imaginary registry whose asset_ids do not exist in this repo's
        # writer tree, so C-23's code derivation has nothing to say about it and the
        # fixture's own declared `writer_substep_truth` is the only truth there is.
        # It is deliberately NOT settable from `--snapshot` or `--live`: those two
        # modes always derive C-23's truth from the writer classes (see c23).
        self.synthetic = synthetic
        self.meta: dict = raw.get("_meta") or {}
        self.assets: list[dict] = raw.get("assets") or []
        self.columns: set[str] = set(raw.get("registry_columns") or [])
        if not self.columns and self.assets:
            self.columns = set(self.assets[0].keys())
        pt = raw.get("public_tables")
        self.public_tables: set[str] | None = set(pt) if pt is not None else None
        self.throughput: dict[str, dict] | None = None
        if raw.get("throughput") is not None:
            self.throughput = {r["asset_id"]: r for r in raw["throughput"]}
        # DECLARED truth — whatever the snapshot (or, under --live, the census FILE)
        # says the writer classes look like. Under `--snapshot`/`--live` this is NOT
        # C-23's truth source any more; it is carried so C-23 can REPORT when the
        # declared artifact has gone stale against the code. See c23.
        self.writer_truth: dict[str, bool] | None = raw.get("writer_substep_truth")
        self.zero_consumer: dict | None = raw.get("zero_consumer_packets")
        self.frozen_rungs: list[str] = raw.get("frozen_rungs") or []
        self.by_id = {a["asset_id"]: a for a in self.assets}

    def has(self, col: str) -> bool:
        return col in self.columns

    def missing(self, col: str) -> str | None:
        if self.has(col):
            return None
        return (f"column `{col}` does not exist on asset_registry in this snapshot "
                f"(migration 590 adds it) — the rule's detector exists but has no "
                f"input, so its verdict is null, not green")

    def get(self, a: dict, col: str, default=None):
        return a.get(col, default)

    def domain_of(self, a: dict) -> tuple[str | None, str]:
        """(domain, provenance). Uses the real column when present; otherwise §5.1's
        normative 1:1 derivation from `scope`, which is stated in the contract as
        total and judgment-free. The provenance is always reported."""
        if self.has("domain"):
            return a.get("domain"), "column"
        return SCOPE_DOMAIN.get(a.get("scope")), "derived_from_scope(§5.1)"

    def deps(self, a: dict) -> list[str]:
        d = a.get("depends_on")
        return list(d) if d else []


# ─────────────────────────────────────────────────────────────────────────────
# Contract §6 table parse — the anti-drift mechanism
# ─────────────────────────────────────────────────────────────────────────────
CONTRACT_ROW_RE = re.compile(
    r"^\|\s*(C-\d\d)\s*\|(.*?)\|\s*(BLOCKING|RUNG|ADVISORY)\s*\|(.*?)\|\s*$")


def parse_contract(path: pathlib.Path) -> dict:
    if not path.exists():
        raise GuardError(f"contract document not found at {path}")
    rows: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CONTRACT_ROW_RE.match(line)
        if not m:
            continue
        rid, assertion, severity, live = m.group(1), m.group(2), m.group(3), m.group(4)
        rows[rid] = {
            "assertion": assertion.strip(),
            "severity": severity,
            "live_cell": live.strip(),
            "declared_not_checkable": "not checkable" in live.lower(),
        }
    if not rows:
        raise GuardError(f"parsed 0 conformance rules out of {path} — the §6 table "
                         "shape changed; the guard refuses to run against a spec it "
                         "cannot read")
    return rows


class GuardError(Exception):
    pass


# ═════════════════════════════════════════════════════════════════════════════
# SNAPSHOT FRESHNESS — M0-T40, finding F-T36-2
# ═════════════════════════════════════════════════════════════════════════════
# WHY `--baseline` EXISTS, ESTABLISHED BEFORE IT WAS TOUCHED.
#
# It is not a mistake and it is not a shortcut. GitHub Actions has no route to the
# production database and no credential for one — see this module's header, and
# `.github/workflows/nirmana-m0-guards.yml`, which runs `--self-test` and `--baseline`
# and never `--live`. `--live` reads `DATABASE_URL` out of `platform/.env.local`, a
# file that does not exist in CI. So "switch CI to `--live`" is not a fix; it is a job
# that cannot run. `--baseline` is a deliberate accommodation to that constraint.
#
# WHAT WAS ACTUALLY BROKEN. The accommodation shipped without the one thing that makes
# it honest: a freshness detector. The dated snapshot was read, its rules were run, and
# its output was printed with no statement anywhere about how old the data was — so the
# same report reads identically whether the snapshot was taken sixty seconds ago or
# three months ago, and a reader (or a future blocking gate) cannot tell which. Measured
# at 2026-08-23T08:26Z: the shipped baseline was captured at 05:09:17Z, before migration
# 590 applied and before two certified repairs landed, and it reported C-05, C-14 and
# C-23 as BLOCKING failures when all three pass against production. It also reported
# five rules `not_checkable` for want of columns that production has had since 05:36Z.
# That is a fossil being read as a verdict, which is CLAUDE.md §N.8's defect class
# sitting inside the mechanism built to catch it.
#
# THE FIX, AND ITS HONEST SCOPE. Two detectors, both DB-free, both reported in every
# mode and ENFORCED (exit 3) in snapshot/baseline mode:
#
#   1. AGE. `_meta.read_at` against a declared maximum (`--max-age-hours`, default
#      DEFAULT_MAX_SNAPSHOT_AGE_HOURS). A snapshot with no parseable `read_at` is stale
#      by definition: an age that cannot be measured is not a young age.
#   2. SCHEMA-BEHIND. Every `ALTER TABLE asset_registry ADD COLUMN` in this repo's
#      `platform/migrations/*.sql` names a column the catalogue is supposed to have. A
#      snapshot missing one of those columns provably predates a migration that is
#      sitting in the same checkout. This is a PROOF of staleness, not an estimate.
#
#      Its honest limit, stated rather than glossed: it reads only that one statement
#      form in that one directory, so it is SUFFICIENT to prove staleness and NOT
#      COMPLETE — a snapshot it calls schema-current may still be old, which is exactly
#      what detector 1 is for. Neither detector can prove a snapshot is CURRENT; they
#      can only prove it is not. That is why the output never says "fresh", only
#      "no staleness detected", and why `--live` remains the only mode that is a
#      statement about production.
#
# WHAT THIS DELIBERATELY DOES NOT DO: it does not make anything gate that did not gate
# before in the CI sense (the workflow's `continue-on-error: true` is untouched, and no
# file under `.github/` was edited by this task), and it does not weaken any rule. It
# only stops a stale input from being reported as if it were a current one.
DEFAULT_MAX_SNAPSHOT_AGE_HOURS = 24.0

_ALTER_ADD_COLUMN_RE = re.compile(
    r"alter\s+table\s+(?:only\s+)?(?:public\.)?asset_registry\s+"
    r"add\s+column\s+(?:if\s+not\s+exists\s+)?([a-z_][a-z0-9_]*)", re.I)


def migration_declared_registry_columns() -> tuple[set[str], list[str]]:
    """Columns this repo's migrations declare on asset_registry. (set, files)."""
    cols: set[str] = set()
    files: list[str] = []
    if not MIGRATIONS_DIR.exists():
        return cols, files
    for p in sorted(MIGRATIONS_DIR.glob("*.sql")):
        flat = " ".join(p.read_text(encoding="utf-8", errors="replace").split())
        found = {m.group(1).lower() for m in _ALTER_ADD_COLUMN_RE.finditer(flat)}
        if found:
            cols |= found
            files.append(p.name)
    return cols, files


def snapshot_staleness(raw: dict, mode: str, max_age_hours: float,
                       now: _dt.datetime | None = None) -> dict:
    """Measure how old the rows the guard is about to judge actually are."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    meta = raw.get("_meta") or {}
    read_at = meta.get("read_at")
    reasons: list[str] = []
    age_hours: float | None = None

    if not read_at:
        reasons.append("the snapshot carries no `_meta.read_at`, so its age cannot be "
                       "measured — an age that cannot be measured is not a young age")
    else:
        try:
            ts = _dt.datetime.fromisoformat(str(read_at).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=_dt.timezone.utc)
            age_hours = round((now - ts).total_seconds() / 3600.0, 3)
        except ValueError:
            reasons.append(f"`_meta.read_at` ({read_at!r}) is not an ISO-8601 timestamp, "
                           f"so the snapshot's age cannot be measured")

    age_exceeded = age_hours is not None and age_hours > max_age_hours
    if age_exceeded:
        reasons.append(f"the snapshot was taken {age_hours}h ago, which exceeds the "
                       f"declared maximum of {max_age_hours}h")

    declared, mig_files = migration_declared_registry_columns()
    snap_cols = {str(c).lower() for c in (raw.get("registry_columns") or [])}
    schema_behind = sorted(declared - snap_cols) if snap_cols else []
    if schema_behind:
        reasons.append(
            f"the snapshot is missing column(s) {schema_behind} that a migration in "
            f"THIS checkout adds to asset_registry ({', '.join(mig_files)}) — the "
            f"snapshot provably predates a schema change that is already in the repo")

    return {
        "mode": mode,
        "read_at": read_at,
        "measured_at": now.isoformat(),
        "age_hours": age_hours,
        "max_age_hours": max_age_hours,
        "age_exceeded": age_exceeded,
        "migration_declared_columns": sorted(declared),
        "migration_files_scanned": mig_files,
        "schema_behind_columns": schema_behind,
        "stale": bool(reasons),
        "reasons": reasons,
        "enforced": mode != "live",
        "what_a_clean_result_means": (
            "no staleness was DETECTED. That is not a claim that the snapshot is "
            "current: neither detector can prove currency, only its absence. Only "
            "`--live` is a statement about production."),
    }


# ═════════════════════════════════════════════════════════════════════════════
# PER-RULE DISCLOSURES — M0-T40, finding F-T36-3
# ═════════════════════════════════════════════════════════════════════════════
# THE DEFECT. `asset_catalogue_disclosed_residuals.json` grew a `deferred_rule_disclosures`
# block (M0-T36) to satisfy ADHIKĀRIN D-30 part 4, which amends D-24 part 3 so the CI
# blocking flip additionally requires every DEFERRED rule to carry an itemised, dated
# disclosure. Sixteen entries were written AT THAT TIME (the file has grown since —
# for the current state read a run's own `disclosure` blocks, not this paragraph).
# NOTHING READ THEM: `disclosed_additions` is
# keyed by asset_id and read in exactly one function (`x02`), `zero_consumer_dispositions`
# in exactly one other (`x05`), and severity was a constant typed into the RULES table.
# A disclosure could therefore be written, look correct, and change no outcome — so
# D-30 part 4's precondition was satisfiable on paper and inert in fact, and the switch
# could have been flipped on a condition that was never really met.
#
# WHAT THIS MECHANISM DOES, AND THE THREE THINGS IT REFUSES TO DO.
#
#   * A disclosure NEVER turns a rule green. The rule still runs, still reports `fail`,
#     and still lists every violation, with the disclosure attached to the result. This
#     is D-12 part 4's "never silently green" and D-10 part 3's migration-number route,
#     as M0-T14 implemented it. What a disclosure can buy is that the failure does not
#     GATE — `effective_severity` becomes DISCLOSED_NON_GATING and the exit code ignores
#     it. Visible and non-gating; never invisible.
#   * A disclosure NEVER silences a rule wholesale. It must itemise what it covers, and
#     the demotion applies only while EVERY current violation of that rule is inside
#     that itemised set. One new violation the disclosure does not name and the rule
#     gates again at its declared severity, with the uncovered rows called out. The
#     backlog can be paid down, never silently grown — the same discipline
#     `migration_number_legacy_duplicates.json` is held to.
#   * A KĀRAKA CANNOT DEMOTE A GATE BY WRITING A FILE. Severity is no longer a bare
#     constant, but nor is it a free-text field: a demotion takes effect only when the
#     entry names a decision id that ACTUALLY EXISTS in `state/DECISIONS.jsonl`, was
#     authored by ADHIKĀRIN, AND ITSELF AUTHORISES THIS RULE FOR THESE IDENTITIES —
#     because catalogue-gate disposition is a charter G-power and an entry any agent
#     can type is not an authority record. That last conjunct arrived with D-61 and it
#     replaced a stated limit that had become the hole: until 2026-08-23 this comment
#     read "it verifies such a ruling EXISTS and who authored it; it cannot verify the
#     ruling says what the entry claims", and ADHIKĀRIN's own probe showed that limit
#     was not a boundary anyone could live inside — a real ruling about
#     `fleet/heartbeat.sh` demoted C-01, as did the same citation carrying an invented,
#     WIDER `covers` list. The check now reads the cited decision's own
#     `authorised_covers`, requires an entry keyed by this RULE ID, and requires the
#     shipped `covers` to be a SUBSET of it (see decision_grant /
#     apply_rule_disclosures). The honest limit that REMAINS, stated: the ledger is an
#     append-only file in this repository, so this detector is exactly as trustworthy
#     as the ledger's own integrity — it proves the warrant was written, never that it
#     was wise.
#
# CONSEQUENCE, RE-MEASURED 2026-08-23T15:21Z (M0-T56) AND DELIBERATELY NOT RESTATED AS A
# FROZEN COUNT: this block used to assert that "all sixteen shipped entries lack both
# `gating_effect` and `authorised_by` … NOT ONE BLOCKING GATE IS DEMOTED", which was
# true when M0-T14 wrote it and was falsified by M0-T49 at 14:06Z. Shipped entries now
# DO claim `gating_effect: non_gating` under an ADHIKĀRIN authority, and rules are
# demoted in fact. THE LIVE NUMBER IS THE GUARD'S OWN SUMMARY FIELD
# (`disclosed_non_gating`, plus each rule's `disclosure` block) — read it from a run,
# never from this comment, which is how the previous count came to be false. What has
# not changed: a demoted rule still FAILS, still reports every violation, and a
# violation outside `covers` brings the gate straight back. Flipping the CI job's
# blocking switch remains ADHIKĀRIN's act and is still unflipped — the
# `nirmana-m0-guards.yml` conformance job is `continue-on-error` as of this edit, and
# this task did not touch `.github/`.
DISCLOSED_NON_GATING = "DISCLOSED_NON_GATING"

# Fields every rule disclosure must carry. An incomplete disclosure is not a
# disclosure — same posture as x02()'s check and migration_number_guard.ts error E4.
REQUIRED_DISCLOSURE_FIELDS = ("rule", "owner", "deferred_to", "disclosed_via",
                              "reason", "disclosed_at", "disclosed_by")
# Additionally required the moment an entry claims a gating effect.
REQUIRED_DEMOTION_FIELDS = ("authorised_by", "covers")
VALID_GATING_EFFECTS = ("none", "non_gating")

_RULE_DISCLOSURE_DOC: dict | None = None      # test-injection point (self-test only)
_DECISION_INDEX: dict | None = None           # test-injection point (self-test only)


def decision_index(force: bool = False) -> dict:
    """{decision_id: {"agent":…, "power":…, "authorised_covers":…}} from DECISIONS.jsonl.

    `authorised_covers` IS RETAINED DELIBERATELY (D-61 part 4). Until 2026-08-23 this
    index kept only agent/power/ts and discarded the decision body, so the authority
    check downstream could authenticate the AUTHOR of a cited decision and could not,
    structurally, ask whether that decision authorises anything at all. ADHIKĀRIN
    re-ran the attack through this guard's own injection point and found the covers
    list entirely self-asserted: `authorised_by=D-1` (a real G9 ruling about
    fleet/heartbeat.sh, carrying no `authorised_covers`) demoted C-01, and so did the
    same citation carrying an INVENTED, WIDER covers list naming assets D-1 never
    mentions. Dropping the body here was what made that possible; keeping it is half
    the fix, and apply_rule_disclosures() is the other half.
    """
    global _DECISION_INDEX
    if _DECISION_INDEX is not None and not force:
        return _DECISION_INDEX
    idx: dict[str, dict] = {}
    if DECISIONS_PATH.exists():
        for line in DECISIONS_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict) and d.get("id"):
                idx[str(d["id"])] = {"agent": d.get("agent"), "power": d.get("power"),
                                     "ts": d.get("ts"),
                                     "authorised_covers": d.get("authorised_covers")}
    _DECISION_INDEX = idx
    return idx


def decision_grant(auth: dict | None, rid: str) -> tuple[set[str] | None, str]:
    """The identities decision `auth` actually authorises for rule `rid`.

    Returns (granted_identities, why_not). `granted_identities is None` means THE
    DECISION AUTHORISES NOTHING FOR THIS RULE and the caller must refuse the demotion —
    fail closed on every gap, per D-61 part 4: no `authorised_covers` field at all, no
    entry keyed by this rule id, or an entry with no `covers` list.

    Note the key is the RULE ID (`C-28`), not the disclosure entry's own key
    (`C-28_residual`): a disclosure may be filed under any key it likes, but it can
    only ever be authorised for the rule it declares.
    """
    if not isinstance(auth, dict):
        return None, "no such decision"
    ac = auth.get("authorised_covers")
    if not isinstance(ac, dict):
        return None, ("carries no `authorised_covers` field — a decision authorises a "
                      "demotion in a machine-readable field or it authorises nothing, "
                      "whatever its prose says (D-61 part 6)")
    grant = ac.get(rid)
    if not isinstance(grant, dict):
        return None, (f"carries `authorised_covers`, but no entry for {rid} — it "
                      f"authorises {sorted(ac) or 'nothing'}")
    covers = grant.get("covers")
    if not isinstance(covers, list):
        return None, f"`authorised_covers[{rid}]` carries no `covers` list"
    return {str(c) for c in covers}, ""


def load_rule_disclosures(doc: dict | None = None) -> dict[str, list[dict]]:
    """Rule-keyed disclosures, validated. Raises GuardError on a malformed entry."""
    if doc is None:
        doc = _RULE_DISCLOSURE_DOC
    if doc is None:
        doc = _load_json(RESIDUALS_PATH)
    if doc is None:
        raise GuardError(f"residuals file unreadable: {RESIDUALS_PATH.name} — the "
                         f"disclosure reader cannot report 'no disclosures' when it "
                         f"could not read the file that would carry them")
    block = doc.get("deferred_rule_disclosures") or {}
    known = {r.id for r in ALL_RULES}
    out: dict[str, list[dict]] = {}
    for key, ent in sorted(block.items()):
        if not isinstance(ent, dict):
            raise GuardError(f"rule disclosure '{key}' is not an object")
        missing = [f for f in REQUIRED_DISCLOSURE_FIELDS if not ent.get(f)]
        if missing:
            raise GuardError(
                f"rule disclosure '{key}' is missing required field(s) {missing} — an "
                f"incomplete disclosure is not a disclosure (mirrors x02 / "
                f"migration_number_guard.ts error E4)")
        rid = str(ent["rule"])
        if rid not in known:
            raise GuardError(
                f"rule disclosure '{key}' names rule '{rid}', which this guard does not "
                f"implement — a disclosure for a rule that does not exist is a typo "
                f"wearing governance clothes")
        eff = ent.get("gating_effect", "none")
        if eff not in VALID_GATING_EFFECTS:
            raise GuardError(f"rule disclosure '{key}': gating_effect must be one of "
                             f"{VALID_GATING_EFFECTS}, got {eff!r}")
        if eff == "non_gating":
            lacking = [f for f in REQUIRED_DEMOTION_FIELDS if not ent.get(f)]
            if lacking:
                raise GuardError(
                    f"rule disclosure '{key}' claims gating_effect='non_gating' but is "
                    f"missing {lacking}. A demotion needs an authority record "
                    f"(`authorised_by`: a DECISIONS.jsonl id) and an itemised `covers` "
                    f"list; without both it would silence the rule wholesale, which is "
                    f"charter H3")
            if not isinstance(ent.get("covers"), list):
                raise GuardError(f"rule disclosure '{key}': `covers` must be a list of "
                                 f"violation identities")
        out.setdefault(rid, []).append(dict(ent, _key=key))
    return out


def violation_identity(row: Any) -> str:
    """A stable identity for one violation row, for coverage comparison."""
    if isinstance(row, dict):
        for k in ("asset_id", "id", "table", "target_table"):
            if row.get(k):
                return str(row[k])
        return json.dumps(row, sort_keys=True, ensure_ascii=False)
    return str(row)


def apply_rule_disclosures(rid: str, declared_severity: str, result: dict,
                           disclosures: dict[str, list[dict]],
                           decisions: dict) -> dict:
    """Compute the effective severity FROM the disclosures. Mutates `result`."""
    entries = disclosures.get(rid) or []
    notes: list[str] = []
    covered: set[str] = set()
    demoting: list[str] = []
    effective = declared_severity

    for ent in entries:
        key = ent.get("_key", rid)
        if ent.get("gating_effect", "none") != "non_gating":
            notes.append(f"{key}: recorded, no gating effect claimed "
                         f"(gating_effect absent or 'none')")
            continue
        auth_id = str(ent.get("authorised_by"))
        auth = decisions.get(auth_id)
        if auth is None:
            notes.append(f"{key}: claims non_gating under '{auth_id}', which is NOT a "
                         f"decision id present in {DECISIONS_PATH.name} — no effect")
            continue
        if auth.get("agent") != "ADHIKARIN":
            notes.append(f"{key}: claims non_gating under '{auth_id}', authored by "
                         f"{auth.get('agent')!r} and not ADHIKĀRIN — no effect")
            continue
        # ── D-61 part 4 — THE CITED DECISION MUST ACTUALLY AUTHORISE THIS DEMOTION ──
        # Everything above authenticates the AUTHOR of a decision. It never asks
        # whether that decision authorises this rule, or bounds what the entry may
        # claim to cover. Both gaps were exploited by ADHIKĀRIN's own probe (D-61
        # part 1): a real ruling about heartbeat.sh demoted C-01, and the same
        # citation carrying an invented, WIDER `covers` list demoted it too. So the
        # grant is now read from the decision itself and the entry's `covers` must be
        # a SUBSET of it. Fail closed on every gap — an unauthorised entry buys
        # nothing and the rule gates at its declared severity.
        granted, why_not = decision_grant(auth, rid)
        if granted is None:
            notes.append(f"{key}: claims non_gating under '{auth_id}', which {why_not} "
                         f"— no effect")
            continue
        claimed = {str(c) for c in (ent.get("covers") or [])}
        outside = sorted(claimed - granted)
        if outside:
            notes.append(
                f"{key}: claims non_gating under '{auth_id}' for {len(claimed)} "
                f"identity/identities, but {len(outside)} of them are OUTSIDE what "
                f"that decision authorises for {rid} {outside[:8]} — no effect. A "
                f"`covers` list wider than its grant PRE-AUTHORISES a future violation "
                f"(D-54 part 5(a)); the subset rule is what makes that a detector "
                f"instead of an honour system")
            continue
        demoting.append(key)
        covered |= claimed

    ids = [violation_identity(v) for v in result.get("violations") or []]
    uncovered = sorted({i for i in ids if i not in covered})

    if result.get("status") == FAIL and demoting:
        if uncovered:
            notes.append(
                f"authorised disclosure(s) {demoting} apply, but {len(uncovered)} "
                f"violation(s) are OUTSIDE their itemised `covers` list "
                f"{uncovered[:8]} — the rule gates at its declared severity. A "
                f"disclosure covers what it names; a backlog may be paid down, never "
                f"silently grown")
        else:
            effective = DISCLOSED_NON_GATING
            notes.append(f"every violation is inside the itemised `covers` of "
                         f"authorised disclosure(s) {demoting} — the failure is "
                         f"REPORTED IN FULL and does not gate")

    result["declared_severity"] = declared_severity
    result["effective_severity"] = effective
    result["disclosure"] = {
        "count": len(entries),
        "keys": [e.get("_key", rid) for e in entries],
        "authorised_demoting": demoting,
        "covered_violations": sorted(covered & set(ids)),
        "uncovered_violations": uncovered if result.get("status") == FAIL else [],
        "effect": "non_gating" if effective == DISCLOSED_NON_GATING else "none",
        "notes": notes,
        "never_green": ("a disclosure never changes a rule's status; the failure and "
                        "all of its violations are reported either way"),
    }
    return result



# ─────────────────────────────────────────────────────────────────────────────
# C-01 … C-28
# ─────────────────────────────────────────────────────────────────────────────
def c01(s: Snapshot) -> Result:
    """asset_id prefix matches layer, for non-source rows.

    FOUR CLASSES KEPT APART, deliberately (M0-T1 census `prefix_conformance`):
    `unrecognised_prefix` (the id's prefix is not one of the six) and
    `layer_contradiction` (a recognised prefix that names a different layer than the
    `layer` column) are DIFFERENT defects with different repairs. C-02's NULL and
    bare-digit classes are `layer_index` metadata gaps and are NOT prefix violations —
    totalling them into one number would report 20 metadata gaps as prefix defects.
    """
    unrecognised, contradiction = [], []
    for a in s.assets:
        if a.get("asset_kind") == "source":
            continue
        aid, layer = a["asset_id"], a.get("layer")
        pre = aid[:3]
        if pre not in set(LAYER_PREFIX.values()):
            unrecognised.append({"asset_id": aid, "prefix": pre, "layer": layer,
                                 "class": "unrecognised_prefix"})
        elif pre != LAYER_PREFIX.get(layer):
            contradiction.append({"asset_id": aid, "prefix": pre, "layer": layer,
                                  "expected_prefix": LAYER_PREFIX.get(layer),
                                  "class": "layer_contradiction"})
    return verdict(unrecognised + contradiction, detail={
        "conforming": sum(1 for a in s.assets if a.get("asset_kind") != "source")
                      - len(unrecognised) - len(contradiction),
        "class_counts": {"unrecognised_prefix": len(unrecognised),
                         "layer_contradiction": len(contradiction)},
        "classes_are_not_totalled": "C-02's layer_index NULL/bare-digit gaps are a "
                                    "separate metadata class and are counted by C-02",
    })


def c02(s: Snapshot) -> Result:
    """layer_index matches ^L[0-5]$ and agrees with layer. Three classes kept apart."""
    nulls, bare, mismatch = [], [], []
    for a in s.assets:
        aid, layer, li = a["asset_id"], a.get("layer"), a.get("layer_index")
        want = LAYER_INDEX.get(layer)
        if li is None:
            nulls.append({"asset_id": aid, "layer": layer, "expected": want,
                          "class": "layer_index_null"})
        elif re.fullmatch(r"[0-5]", str(li)):
            bare.append({"asset_id": aid, "layer": layer, "layer_index": li,
                         "expected": want, "class": "layer_index_bare_digit"})
        elif not re.fullmatch(r"L[0-5]", str(li)) or li != want:
            mismatch.append({"asset_id": aid, "layer": layer, "layer_index": li,
                             "expected": want, "class": "layer_index_mismatch"})
    return verdict(nulls + bare + mismatch, detail={"class_counts": {
        "layer_index_null": len(nulls), "layer_index_bare_digit": len(bare),
        "layer_index_mismatch": len(mismatch)}})


def c03(s: Snapshot) -> Result:
    v = []
    for a in s.assets:
        want = LAYER_NAME.get(a.get("layer"))
        got = a.get("layer_name")
        if got != want:
            v.append({"asset_id": a["asset_id"], "layer": a.get("layer"),
                      "layer_name": got, "expected": want,
                      "class": "layer_name_null" if got is None
                               else "layer_name_spelling"})
    return verdict(v, detail={"class_counts": {
        "layer_name_null": sum(1 for x in v if x["class"] == "layer_name_null"),
        "layer_name_spelling": sum(1 for x in v if x["class"] == "layer_name_spelling")}})


def c04(s: Snapshot) -> Result:
    v, blocked = [], []
    if s.public_tables is None:
        blocked.append("public_tables not present in this snapshot — the "
                       "'table exists' conjunct cannot be evaluated")
    for a in s.assets:
        if a.get("asset_kind") not in DATA_KINDS:
            continue
        tt = a.get("target_table")
        if tt is None:
            v.append({"asset_id": a["asset_id"], "asset_kind": a.get("asset_kind"),
                      "target_table": None, "class": "target_table_null"})
        elif s.public_tables is not None and tt not in s.public_tables:
            v.append({"asset_id": a["asset_id"], "target_table": tt,
                      "class": "target_table_missing"})
    return verdict(v, blocked)


def c05(s: Snapshot) -> Result:
    return verdict([{"asset_id": a["asset_id"], "asset_kind": a.get("asset_kind")}
                    for a in s.assets
                    if a.get("asset_kind") in DATA_KINDS and a.get("count_sql") is None])


def c06(s: Snapshot) -> Result:
    v, prov = [], None
    for a in s.assets:
        dom, prov = s.domain_of(a)
        cs = a.get("count_sql")
        if dom == "chart" and cs is not None and "$1" not in cs:
            v.append({"asset_id": a["asset_id"], "domain": dom,
                      "domain_provenance": prov})
    return verdict(v, detail={"domain_provenance": prov})


def c07(s: Snapshot) -> Result:
    v = []
    for a in s.assets:
        if a.get("asset_kind") != "service":
            continue
        offending = {k: a.get(k) for k in
                     ("target_table", "count_sql", "target_floor", "clear_tables")
                     if a.get(k) is not None}
        if offending:
            v.append({"asset_id": a["asset_id"], "non_null_fields": sorted(offending)})
    return verdict(v)


def c08(s: Snapshot) -> Result:
    blocked = s.missing("data_disposition")
    if blocked:
        return Result(NOT_CHECKABLE, [], blocked,
                      {"retired_rows_in_snapshot":
                       [a["asset_id"] for a in s.assets
                        if a.get("catalog_status") == "RETIRED"]})
    return verdict([{"asset_id": a["asset_id"]} for a in s.assets
                    if a.get("catalog_status") == "RETIRED"
                    and a.get("data_disposition") is None])


def c09(s: Snapshot) -> Result:
    blocked = s.missing("superseded_by")
    if blocked:
        return Result(NOT_CHECKABLE, [], blocked)
    return verdict([{"asset_id": a["asset_id"], "superseded_by": a["superseded_by"]}
                    for a in s.assets
                    if a.get("superseded_by") is not None
                    and a["superseded_by"] not in s.by_id])


def c10(s: Snapshot) -> Result:
    blocked = s.missing("data_disposition")
    if blocked:
        return Result(NOT_CHECKABLE, [], blocked)
    return verdict([{"asset_id": a["asset_id"],
                     "catalog_status": a.get("catalog_status")}
                    for a in s.assets
                    if a.get("data_disposition") is not None
                    and a.get("catalog_status") != "RETIRED"])


def c11(s: Snapshot) -> Result:
    """A CURRENT asset may depend only on CURRENT (or source) assets.

    Two classes kept apart: a DRAFT/RETIRED/inactive TARGET, and a DANGLING target
    (no such row at all). C-12 owns dangling in general; this rule reports it as its
    own class rather than folding it into 'depends on DRAFT'.
    """
    v = []
    for a in s.assets:
        if a.get("catalog_status") != "CURRENT":
            continue
        for d in s.deps(a):
            b = s.by_id.get(d)
            if b is None:
                v.append({"asset_id": a["asset_id"], "dep": d,
                          "class": "dangling_edge_from_current"})
            elif b.get("catalog_status") != "CURRENT" and b.get("asset_kind") != "source":
                v.append({"asset_id": a["asset_id"], "dep": d,
                          "dep_status": b.get("catalog_status"),
                          "dep_is_active": b.get("is_active"),
                          "class": f"current_depends_on_{str(b.get('catalog_status')).lower()}"})
    return verdict(v, detail={"class_counts": _counts(v)})


def c12(s: Snapshot) -> Result:
    v = [{"asset_id": a["asset_id"], "dep": d}
         for a in s.assets for d in s.deps(a) if d not in s.by_id]
    return verdict(v)


def c13(s: Snapshot) -> Result:
    self_edges = [{"asset_id": a["asset_id"], "class": "self_edge"}
                  for a in s.assets if a["asset_id"] in s.deps(a)]
    # iterative DFS, three-colour, over declared edges that resolve
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {aid: WHITE for aid in s.by_id}
    cycles: list[dict] = []
    for root in sorted(s.by_id):
        if colour[root] != WHITE:
            continue
        stack: list[tuple[str, int]] = [(root, 0)]
        path: list[str] = []
        colour[root] = GREY
        path.append(root)
        while stack:
            node, i = stack[-1]
            ds = [d for d in s.deps(s.by_id[node]) if d in s.by_id and d != node]
            if i < len(ds):
                stack[-1] = (node, i + 1)
                nxt = ds[i]
                if colour[nxt] == GREY:
                    k = path.index(nxt)
                    cycles.append({"cycle": path[k:] + [nxt], "class": "cycle"})
                elif colour[nxt] == WHITE:
                    colour[nxt] = GREY
                    path.append(nxt)
                    stack.append((nxt, 0))
            else:
                colour[node] = BLACK
                stack.pop()
                if path and path[-1] == node:
                    path.pop()
    return verdict(self_edges + cycles,
                   detail={"class_counts": _counts(self_edges + cycles)})


def c14(s: Snapshot) -> Result:
    v = [{"asset_id": a["asset_id"], "asset_kind": a.get("asset_kind"),
          "asset_type": a.get("asset_type")}
         for a in s.assets
         if (a.get("asset_kind"), a.get("asset_type")) not in KIND_TYPE_OK]
    return verdict(v)


def c15(s: Snapshot) -> Result:
    v = [{"asset_id": a["asset_id"],
          "health_probe": a.get("health_probe") is not None,
          "provides_apis": a.get("provides_apis") is not None}
         for a in s.assets
         if a.get("asset_kind") == "service"
         and (a.get("health_probe") is None or a.get("provides_apis") is None)]
    return verdict(v)


def c16(s: Snapshot) -> Result:
    return verdict([{"asset_id": a["asset_id"], "asset_kind": a.get("asset_kind"),
                     "service_health": a.get("service_health")}
                    for a in s.assets
                    if a.get("asset_kind") != "service"
                    and a.get("service_health") is not None])


def c17(s: Snapshot) -> Result:
    """No graded health without a probe behind it (charter H4, CLAUDE.md §N.8)."""
    return verdict([{"asset_id": a["asset_id"],
                     "service_health": a.get("service_health")}
                    for a in s.assets
                    if a.get("service_health") in ("healthy", "degraded", "unhealthy")
                    and a.get("health_probe") is None])


def c18(s: Snapshot) -> Result:
    blocked = s.missing("domain")
    if blocked:
        return Result(NOT_CHECKABLE, [], blocked, {
            "would_be_derived": "§5.1 derives domain 1:1 from scope; the derivation is "
                                "total over this snapshot, but a derivation is not a "
                                "column and this rule asserts the column"})
    return verdict([{"asset_id": a["asset_id"], "scope": a.get("scope"),
                     "domain": a.get("domain"),
                     "expected": SCOPE_DOMAIN.get(a.get("scope"))}
                    for a in s.assets
                    if a.get("domain") != SCOPE_DOMAIN.get(a.get("scope"))])


def c19(s: Snapshot) -> Result:
    blocked = s.missing("rung")
    if blocked:
        return Result(NOT_CHECKABLE, [], blocked)
    return verdict([{"asset_id": a["asset_id"], "layer": a.get("layer"),
                     "rung": a.get("rung"), "expected": LAYER_RUNG.get(a.get("layer"))}
                    for a in s.assets
                    if a.get("asset_kind") != "source"
                    and a.get("rung") != LAYER_RUNG.get(a.get("layer"))])


def c20(s: Snapshot) -> Result:
    return verdict([{"asset_id": a["asset_id"], "asset_kind": a.get("asset_kind")}
                    for a in s.assets
                    if a.get("catalog_status") == "CURRENT"
                    and a.get("asset_kind") in DATA_KINDS
                    and a.get("target_floor") is None])


def c21(s: Snapshot) -> Result:
    return verdict([{"asset_id": a["asset_id"]} for a in s.assets
                    if a.get("target_floor") == 0
                    and not (a.get("volume_explanation") or "").strip()])


def c22(s: Snapshot) -> Result:
    """Frozen-rung data assets must carry an integrity_check_sql.

    NOT_CHECKABLE on two independent grounds today, and both are reported rather than
    one masking the other. The contract's own §6 cell says "0 rungs frozen, so
    vacuously 0 today" — a vacuous pass is a signal no database state could turn red,
    which §N.8 says is null, not green. So this guard reports it as null.
    """
    blocked = []
    if not s.frozen_rungs:
        blocked.append("no rung is frozen in this snapshot, so the rule's precondition "
                       "set is empty — a 'pass' here could not be falsified by any "
                       "catalogue state (§N.8: null, not green)")
    m = s.missing("rung")
    if m:
        blocked.append(m)
    if blocked:
        return Result(NOT_CHECKABLE, [], "; ".join(blocked), {
            "frozen_rungs": s.frozen_rungs,
            "assets_carrying_integrity_check_sql":
                sum(1 for a in s.assets if a.get("integrity_check_sql")),
            "assets_total": len(s.assets)})
    return verdict([{"asset_id": a["asset_id"], "rung": a.get("rung")}
                    for a in s.assets
                    if a.get("asset_kind") in DATA_KINDS
                    and a.get("rung") in s.frozen_rungs
                    and a.get("integrity_check_sql") is None])


# ─────────────────────────────────────────────────────────────────────────────
# C-23's truth source: the writer CLASSES, parsed at run time — never a file
# ─────────────────────────────────────────────────────────────────────────────
_CODE_TRUTH: tuple[dict[str, bool] | None, dict] | None = None


def code_writer_substep_truth(force: bool = False) -> tuple[dict[str, bool] | None, dict]:
    """`{asset_id: bool}` DERIVED FROM THE WRITER CLASSES AT RUN TIME.

    WHY THIS EXISTS (Nirmāṇa M0-T25). C-23 used to compare the registry against
    `00_ARCHITECTURE/control/writer_substep_census.json` — a checked-in artifact. A
    guard whose truth source is a file is only as current as the last time somebody
    regenerated that file: if the writer tree changes afterwards, the guard reports
    PASS on a divergence that really exists. That is this campaign's own defect class
    (CLAUDE.md §N.8 — a signal must be produced by a detector that measures the claim
    it asserts), and ADHIKĀRIN D-25 part 3 states the rule for exactly this column
    family: *any registry boolean that gates whether a check runs must be derived from
    code, never trusted as declared.* `has_substeps` is that boolean —
    `asset_runner.py:620` only runs the substep-plan-completeness probe when it reads
    true (D-24, §N.8 instance 4) — so its guard may not rest on a file either.

    ONE PARSER, REUSED (D-25 part 2c). The derivation is the campaign's single
    @register/AST census, `00_ARCHITECTURE/control/writer_substep_census.py` (M0-T8,
    made importable by M0-T22 for precisely this kind of reuse). No fourth parser is
    written here, and no asset id is special-cased anywhere.

    STILL STDLIB-ONLY. The census imports only `ast`, `json`, `pathlib`, `sys` and
    executes nothing it parses, so `--self-test` and `--snapshot` remain DB-free and
    dependency-free. It also satisfies D-13 by construction: nothing is imported from
    `platform/scripts/`, and the writer tree is read as text, never executed.

    Returns `(truth, provenance)`. `truth is None` means the derivation could NOT be
    performed, and C-23 then reports `not_checkable`. It NEVER falls back to the file:
    a fallback would restore the exact hazard this function removes.
    """
    global _CODE_TRUTH
    if _CODE_TRUTH is not None and not force:
        return _CODE_TRUTH

    census_py = REPO_ROOT / "00_ARCHITECTURE" / "control" / "writer_substep_census.py"
    sidecar = REPO_ROOT / "platform" / "python-sidecar"
    prov: dict[str, Any] = {
        "truth_source": "writer classes, parsed at run time (AST)",
        "parser": "00_ARCHITECTURE/control/writer_substep_census.py :: census()",
        "rule": "HEAVY := the @register'd class overrides BOTH plan_substeps AND "
                "run_substep (FROZEN contract, CLAUDE.md §N.2)",
    }

    def _null(reason: str):
        global _CODE_TRUTH
        prov["reason"] = reason
        _CODE_TRUTH = (None, prov)
        return _CODE_TRUTH

    if not census_py.exists():
        return _null(f"the writer-class census is not present at "
                     f"{census_py.relative_to(REPO_ROOT)} — C-23's truth cannot be "
                     f"derived from code, and it will NOT be read from a file instead")
    if not sidecar.exists():
        return _null(f"the writer tree {sidecar.relative_to(REPO_ROOT)} is not present "
                     f"in this checkout — nothing to derive the truth from")

    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(
            "_nirmana_writer_substep_census", census_py)
        if spec is None or spec.loader is None:
            return _null("could not load the writer-class census module")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # THE CENSUS'S OWN ROOT DERIVATION IS EXERCISED, NOT OVERRIDDEN (Nirmāṇa
        # M0-T30 / F-6). Until M0-T28 the census pinned `ROOT` to one developer's
        # absolute path, so this function re-pointed `mod.ROOT`/`mod.BASE` at
        # REPO_ROOT before calling `census()`. That workaround was correct when it
        # was written and became a MASK the moment the root was fixed: with the
        # re-point in place, mis-deriving the census root (e.g. `parents[1]`) left
        # this guard's `--self-test` reporting `579 files, 123 @register decorators`
        # and exit 0, because the guard never ran the derivation it was standing in
        # front of. A guard that cannot go red on a defect is not a detector for it
        # (charter H3/H4, CLAUDE.md §N.8, D-24 part 3). The re-point is therefore
        # gone: the census resolves its own root, and if that resolution is wrong the
        # scan comes back empty and C-23 goes not_checkable below — which the
        # code-derivation probe counts as a self-test FAILURE.
        c = mod.census(force=True)
    except Exception as e:                                   # noqa: BLE001
        return _null(f"the writer-class census raised {type(e).__name__}: {e}")

    prov.update({
        "files_scanned": c.get("files_scanned"),
        "registrations": c.get("n_registrations"),
        "distinct_asset_ids": c.get("n_distinct_asset_ids"),
        # WHERE it looked, not only WHAT it found (M0-T28 added these to the census
        # record for exactly this reason: an empty census is indistinguishable from a
        # healthy one unless the provenance says which tree was scanned).
        "scan_root": c.get("scan_root"),
        "scan_base": c.get("scan_base"),
        "base_exists": c.get("base_exists"),
    })
    # §N.8 applied to the derivation itself: every one of these means the census does
    # NOT know the writer set, so the truth is null rather than quietly short. A short
    # map would silently skip assets, and a skipped asset can never produce a
    # violation — a detector that cannot fail.
    if c.get("parse_errors"):
        return _null(f"{len(c['parse_errors'])} writer source file(s) failed to parse, "
                     f"so the census is incomplete: {c['parse_errors'][:3]}")
    if c.get("unresolved_registrations"):
        return _null(f"{len(c['unresolved_registrations'])} @register argument(s) did "
                     f"not resolve, so the writer set is not trustworthy: "
                     f"{c['unresolved_registrations'][:3]}")
    if not c.get("files_scanned") or not c.get("n_registrations"):
        return _null(f"the census scanned {c.get('files_scanned')} file(s) and found "
                     f"{c.get('n_registrations')} @register decorator(s) — an empty "
                     f"writer set cannot falsify anything, so it is null, not green")
    # …and, having exercised the derivation rather than overridden it, CHECK ITS
    # ANSWER instead of coercing it. A census that resolved a DIFFERENT checkout
    # scans a real writer tree and comes back full, so the emptiness branch above
    # cannot see it — yet C-23 would then be comparing THIS repo's registry against
    # ANOTHER tree's writer classes. `NIRMANA_REPO` is the live way to reach that
    # state (the census honours it as an override). This is a DETECTOR, not the
    # re-point returning: it makes the guard go null with the two paths named,
    # where the re-point silently made the mismatch impossible to observe.
    scanned_root = str(c.get("scan_root") or "")
    if scanned_root and pathlib.Path(scanned_root) != REPO_ROOT:
        return _null(f"the census derived its own repo root as {scanned_root!r}, which "
                     f"is not the checkout this guard is running over "
                     f"({str(REPO_ROOT)!r}) — C-23 would be comparing this registry "
                     f"against another tree's writer classes. Unset NIRMANA_REPO (or "
                     f"point it here) rather than reading this as a pass")

    truth = {aid: bool(recs[0].get("writer_truth_has_substeps"))
             for aid, recs in (c.get("writers") or {}).items() if recs}
    prov["heavy"] = sum(1 for x in truth.values() if x)
    prov["light"] = sum(1 for x in truth.values() if not x)
    _CODE_TRUTH = (truth, prov)
    return _CODE_TRUTH


def c23(s: Snapshot) -> Result:
    """has_substeps must equal the writer-class truth (plan_substeps + run_substep).

    The truth is DERIVED FROM THE WRITER CLASSES at run time, not read from the
    census file or from whatever the snapshot happened to bake in when it was taken
    (M0-T25; D-25 part 3). The only exception is a bundled self-test fixture, whose
    registry is imaginary and whose declared map is therefore the only truth that
    could exist for it — and that path is reachable only from `--self-test`, never
    from a caller-supplied `--snapshot`.
    """
    if s.synthetic:
        if not s.writer_truth:
            return Result(NOT_CHECKABLE, [], (
                "self-test fixture declares no writer_substep_truth — a synthetic "
                "registry has no writer classes to derive one from"))
        truth: dict[str, bool] = {k: bool(v) for k, v in s.writer_truth.items()}
        prov: dict[str, Any] = {"truth_source": "self-test fixture (synthetic registry)"}
    else:
        truth_or_none, prov = code_writer_substep_truth()
        if truth_or_none is None:
            return Result(NOT_CHECKABLE, [], (
                "the writer-class truth could not be derived from source: "
                + str(prov.get("reason"))
                + " — C-23 does NOT fall back to "
                  "00_ARCHITECTURE/control/writer_substep_census.json or to the "
                  "snapshot's baked-in map, because a file can be stale and a guard "
                  "that passes on a stale truth is not a detector (§N.8)"), dict(prov))
        truth = truth_or_none

    v = []
    for a in s.assets:
        t = truth.get(a["asset_id"])
        if t is None:
            continue          # no registered writer — C-23 has nothing to compare
        if bool(a.get("has_substeps")) != bool(t):
            v.append({"asset_id": a["asset_id"],
                      "registry_has_substeps": a.get("has_substeps"),
                      "writer_truth_has_substeps": t,
                      "class": "false_negative" if t else "false_positive"})

    detail: dict[str, Any] = dict(prov)
    detail.update({
        "assets_with_writer_truth": len(truth),
        "assets_without_writer_truth_skipped":
            sum(1 for a in s.assets if a["asset_id"] not in truth),
        "class_counts": _counts(v)})

    # The stale-artifact report. When a declared map is present but is NOT the truth
    # source, say so and say whether it has drifted. This is reported, not asserted:
    # C-23's claim is about the registry, and a stale census file can no longer make
    # this rule green — which is the whole point of the change.
    if not s.synthetic and s.writer_truth:
        drift = sorted(aid for aid, dv in s.writer_truth.items()
                       if aid in truth and bool(dv) != truth[aid])
        detail["declared_truth_ignored"] = (
            "a writer_substep_truth map was present (snapshot or census file) and was "
            "NOT used as the truth source")
        detail["declared_truth_stale_vs_code"] = len(drift)
        if drift:
            detail["declared_truth_stale_asset_ids"] = drift[:20]
    return verdict(v, detail=detail)


def c24(s: Snapshot) -> Result:
    v, blocked = [], []
    if s.public_tables is None:
        blocked.append("public_tables not present — the 'listed table exists' "
                       "conjunct cannot be evaluated")
    for a in s.assets:
        ct = a.get("clear_tables")
        if not ct:
            continue
        for t in ct:
            if s.public_tables is not None and t not in s.public_tables:
                v.append({"asset_id": a["asset_id"], "listed": t,
                          "class": "clear_table_missing"})
        if a.get("target_table") not in ct:
            v.append({"asset_id": a["asset_id"], "target_table": a.get("target_table"),
                      "clear_tables": ct, "class": "target_table_not_in_clear_tables"})
    return verdict(v, blocked, detail={"rows_setting_clear_tables":
                                       sum(1 for a in s.assets if a.get("clear_tables"))})


def _no_detector(rid: str, why: str) -> Callable[[Snapshot], Result]:
    def f(_s: Snapshot) -> Result:
        return Result(NOT_CHECKABLE, [], why, {"contract_rule": rid})
    return f


def c28(s: Snapshot) -> Result:
    if s.throughput is None:
        return Result(NOT_CHECKABLE, [], (
            "no asset_throughput section in this snapshot — 'has at least one "
            "successful build' cannot be evaluated"))
    v = []
    for a in s.assets:
        if a.get("asset_kind") not in DATA_KINDS:
            continue
        t = s.throughput.get(a["asset_id"])
        built = bool(t and any(st == "lit" for st in (t.get("states") or [])))
        if built and a.get("estimated_seconds") is None:
            v.append({"asset_id": a["asset_id"], "states": t.get("states")})
    return verdict(v)


def x06(s: Snapshot) -> Result:
    """D-94 (ADHIKĀRIN, F-Y) — THE ALL-ASSET-KIND UNEARNED-LIT RATCHET.

    D-42's actual question, asked directly and across EVERY asset_kind, not only
    DATA_KINDS: `asset_throughput.state='lit'` (a CLAIM a build happened) with ZERO
    completed `build_run_assets` records (the EVIDENCE a build happened) behind it.
    c28() above asks a DIFFERENT, narrower, and independently defensible question —
    whether `estimated_seconds` is set on a DATA/artifact asset that was ever marked
    `lit` — and D-94 part 4 confirms both questions are real and neither is wrong.

    THIS rule exists because D-94 found that a CORRECT asset_kind repair
    (bg_panchanga: data -> service, M0-T21, fully authorised under D-24 part 2) walked
    that asset OUT of c28()'s DATA_KINDS-scoped population without c28() itself ever
    changing — "EXIT BY RECATEGORIZATION". D-42 part 3's old protection was conditioned
    on HOW that might happen ("if c28() is ever re-pointed"); D-94 part 9 replaces it
    with an outcome condition: COVERAGE is the invariant, and any row leaving ANY
    blocking rule's population, by ANY mechanism including a correct repair, is an
    event requiring an explanation — never silence. This rule is that coverage: it
    carries NO asset_kind predicate at all, so a future category change cannot walk an
    asset out of it the way one walked bg_panchanga out of c28().

    RATCHET SHAPE — D-87's pawl, WITH D-95's correction applied from the start rather
    than discovered the hard way (D-95 found D-87's shipped pawl compared against
    HEAD^, which releases one commit after a growth; the correct reference is a
    COMMITTED, MONOTONE FLOOR). The population is compared against
    `unearned_lit_floor.json` — itemised, machine-generated, NEVER HAND-TYPED (D-67
    part 4). This rule BLOCKS ONLY ON GROWTH: a live asset_id that is unearned-lit
    today and is NOT a member of the committed floor. It does NOT, and must NEVER,
    block on the floor's own residual population — I13 forbids repairing asset build
    state while R0 is shut, so blocking on the residual would be a PERMANENT RED no
    one may clear (H3 by attrition, D-73 / D-39 part 2). The floor itself may only
    SHRINK, enforced at regeneration time
    (`--regenerate-unearned-lit-floor`), never at read time and never automatically —
    see `regenerate_unearned_lit_floor()`.

    D-84 (set-not-count) applies directly and is why `growth` below is a SET
    difference naming asset_ids, never a length comparison: a population that shrinks
    by one and regrows a DIFFERENT one stays the same SIZE and must still be caught.

    ANCHOR DECLARATION (D-103, ADHIKĀRIN, closing PARIKSAKA V-67 / F-V67-1) —
    stated explicitly per D-103 part 6, whether or not a lineage manifest exists,
    because "a floor that moves for a reason nobody wrote down is the same shape as
    the pawl defect we just spent two tasks on": THIS RULE ANCHORS ON
    `asset_registry` (via `s.assets`), NEVER on `build_run_assets` directly.
    `build_run_assets` is consulted only to ask, for an asset_id ALREADY present in
    `s.assets`, whether that id has a completed run — an asset_id that exists only in
    `build_run_assets` and not in `asset_registry` can never enter `current_ids` and
    is correctly outside this rule's population (you cannot have an unearned lit on
    an asset that does not exist).

    KNOWN-AFFECTED IDS, NAMED RATHER THAN SILENTLY ABSORBED (D-103 part 6): four
    asset_ids live in `build_run_assets` with no matching `asset_registry` row today
    (`platform/scripts/governance/asset_id_lineage_manifest.json` has the full,
    migration/live-DB-derived evidence trail for each):
      - `ga_pyjhora_engine`            — DELETED, migration 342 (no successor id)
      - `ka_gochara_v2_materialize`    — RENAMED to `ka_gochara`, migration 563
      - `chart_dashas`                 — legacy_never_registered (never a valid
                                          asset_id; likely caller confusion with
                                          `ga_dashas`'s target_table of the same name)
      - `ga_chart_service`             — legacy_never_registered (a real, live
                                          service; by design never carried in
                                          asset_registry — see the manifest and
                                          RETRIEVAL_STRATEGY_v1_0.md §5.3)
    Because this rule anchors on `asset_registry`, none of the four can ever be
    flagged BY this rule (correct — they are not assets). The risk D-103 raised is
    narrower and still real: `ka_gochara_v2_materialize`'s completed builds are
    evidence that belongs to the CURRENT id `ka_gochara`, and this rule's `ran` set
    is keyed by the literal `build_run_assets.asset_id` string, so it does not credit
    `ka_gochara` with builds recorded under its pre-rename name. This rule does NOT
    currently read the lineage manifest to resolve that — D-103 part 5 asks this to
    be considered and stated, not necessarily built in the same pass, and wiring it
    in was judged more than a small, clearly-scoped change to a function that already
    carries five rulings' worth of invariants (see the manifest's
    `not_yet_wired_for_resolution` field for the full reasoning and a scoped
    follow-up recommendation). Today this is a live gap, not a silent one: if
    `ka_gochara` is ever independently flagged unearned-lit, this doc-comment and the
    manifest are the pointer to why that reading needs rename-awareness before it is
    trusted at face value.
    """
    if s.throughput is None:
        return Result(NOT_CHECKABLE, [], (
            "no asset_throughput section in this snapshot — 'state=lit with zero "
            "completed runs' cannot be evaluated"))
    if s.raw.get("build_run_assets") is None:
        return Result(NOT_CHECKABLE, [], (
            "no build_run_assets section in this snapshot — the only table that can "
            "hold EVIDENCE a build actually ran is absent, so 'zero completed runs' "
            "cannot be evaluated"))
    floor_doc = _load_json(UNEARNED_LIT_FLOOR_PATH)
    if floor_doc is None:
        return Result(NOT_CHECKABLE, [], f"floor file unreadable: "
                                         f"{UNEARNED_LIT_FLOOR_PATH.name}")
    floor_ids = {e["asset_id"] for e in (floor_doc.get("floor") or [])}

    ran = {r["asset_id"] for r in s.raw["build_run_assets"] if r.get("state") == "complete"}
    current_ids: set[str] = set()
    for a in s.assets:
        aid = a["asset_id"]
        t = s.throughput.get(aid)
        lit = bool(t and any(st == "lit" for st in (t.get("states") or [])))
        if lit and aid not in ran:
            current_ids.add(aid)

    growth = sorted(current_ids - floor_ids)
    paid_down = sorted(floor_ids - current_ids)
    v = [{"asset_id": aid, "class": "unearned_lit_not_in_committed_floor"}
         for aid in growth]
    return verdict(v, detail={
        "current_population_ids": sorted(current_ids),
        "current_population_count": len(current_ids),
        "committed_floor_count": len(floor_ids),
        "growth": growth,
        "paid_down_since_floor": paid_down,
        "r0_intake_named_items": sorted(
            e["asset_id"] for e in (floor_doc.get("floor") or []) if e.get("r0_intake")),
        "why_not_blocking_on_the_residual_itself": (
            "I13 forbids repairing asset build state while R0 is shut (D-94 parts 6 "
            "and 7); blocking on the residual would be a permanent red, H3 by "
            "attrition (D-73 / D-39 part 2). Regenerate the floor with "
            "--regenerate-unearned-lit-floor to record real pay-down; the floor may "
            "only shrink."),
    })


REQUIRED_MANIFEST_ENTRY_FIELDS = ("asset_id", "disposition", "evidence")


def _check_manifest_entry_shape(entry: dict, vocab: set[str]) -> list[dict]:
    """D-116 (ADHIKĀRIN, F-V74-1) — per-entry shape/evidence check for ONE
    `asset_id_lineage_manifest.json` entry, TIERED by disposition class exactly as
    D-116 specifies. Returns a list of violation dicts (empty = this entry passed).

    TIER 1 — `legacy_never_registered` (the evidence is a NEGATIVE claim — "this id
    was never a valid asset_registry.asset_id" — and no cheap mechanical check
    establishes a negative): SHAPE ONLY. `disposition` must be a key of the
    manifest's OWN declared `disposition_vocabulary` (read from the manifest file,
    never hardcoded here), `evidence` must be a non-empty array, and the required
    fields must be present. An EMPTY evidence array is INCOMPLETE, not a partial
    pass — mirrors `migration_number_guard.ts`'s E4 INCOMPLETE-DISCLOSURE class, the
    in-repo precedent D-116 names.

    TIER 2 — any other disposition (`renamed`, `deleted` in the manifest's current
    vocabulary — identified by carrying a `renamed_by_migration` or
    `deleted_by_migration` citation field, D-116's own phrasing for this tier): the
    evidence IS machine-checkable and IS checked for real — the cited migration file
    must actually exist under `REPO_ROOT` AND its content must reference this
    entry's `asset_id` (a substring check over the migration's own source text). A
    migration that does not exist, or exists but never mentions the id, is the
    `manifest_entry_unverifiable_migration_citation` violation class.

    THE CHECK MUST NOT OVERCLAIM (D-116 part 4): a GREEN result for a TIER 1
    (`legacy_never_registered`) entry means only that a disposition and non-empty
    evidence were SUPPLIED — it does NOT mean the evidence was independently
    verified, because no cheap mechanical check can establish a negative. Only the
    TIER 2 (migration-citing) classes get their citation actually resolved against a
    real file on disk. Callers (x07's own doc-comment, any cockpit signal reading
    X-07) must carry this same distinction forward rather than reading X-07 green as
    "every disposition is verified."
    """
    aid = entry.get("asset_id", "<missing asset_id>")

    missing = [f for f in REQUIRED_MANIFEST_ENTRY_FIELDS if f not in entry]
    if missing:
        return [{"asset_id": aid, "class": "manifest_entry_missing_required_field",
                 "detail": f"missing required field(s): {missing}"}]

    disposition = entry["disposition"]
    if disposition not in vocab:
        return [{"asset_id": aid,
                 "class": "manifest_entry_disposition_not_in_vocabulary",
                 "detail": (f"disposition {disposition!r} is not a key of the "
                            f"manifest's own disposition_vocabulary "
                            f"{sorted(vocab)}")}]

    evidence = entry["evidence"]
    if not isinstance(evidence, list) or len(evidence) == 0:
        return [{"asset_id": aid, "class": "manifest_entry_evidence_empty",
                 "detail": ("evidence array is empty — INCOMPLETE, not a partial "
                            "pass (migration_number_guard E4 INCOMPLETE-DISCLOSURE "
                            "precedent)")}]

    if disposition == "legacy_never_registered":
        return []   # TIER 1: shape-only — no migration to check against a negative

    # TIER 2 — a migration-citing disposition: the citation must actually resolve.
    if "deleted_by_migration" in entry:
        migration_field = "deleted_by_migration"
    elif "renamed_by_migration" in entry:
        migration_field = "renamed_by_migration"
    else:
        return [{"asset_id": aid,
                 "class": "manifest_entry_unverifiable_migration_citation",
                 "detail": (f"disposition {disposition!r} is not "
                            f"legacy_never_registered but the entry carries neither "
                            f"a deleted_by_migration nor a renamed_by_migration "
                            f"citation field")}]

    migration_rel = entry[migration_field]
    migration_path = REPO_ROOT / migration_rel
    if not migration_path.is_file():
        return [{"asset_id": aid,
                 "class": "manifest_entry_unverifiable_migration_citation",
                 "detail": f"cited migration does not exist: {migration_rel}"}]

    try:
        migration_text = migration_path.read_text(encoding="utf-8")
    except OSError as e:
        return [{"asset_id": aid,
                 "class": "manifest_entry_unverifiable_migration_citation",
                 "detail": f"cited migration {migration_rel} could not be read: {e}"}]

    if aid not in migration_text:
        return [{"asset_id": aid,
                 "class": "manifest_entry_unverifiable_migration_citation",
                 "detail": (f"cited migration {migration_rel} exists but its "
                            f"content does not reference {aid!r}")}]

    return []


def x07(s: Snapshot) -> Result:
    """D-111 (ADHIKĀRIN) — LINEAGE MANIFEST COMPLETENESS, closing PARIKṢAKA V-70 /
    F-V70-2.

    D-103 authorised `asset_id_lineage_manifest.json` (M0-T75) to record the
    DETERMINED disposition of every `asset_id` that lives in `build_run_assets` but
    not `asset_registry`, and — in ADHIKĀRIN's own words at D-111 — "ordered an
    artifact and ordered nothing to read it." x06() anchors on `asset_registry` by
    design (D-103 part 6) and structurally cannot see an orphan id; no other rule
    compared the two id sets. A fifth orphan — a rename, a retirement, or an operator
    naming a table instead of a registered asset_id, each of which has ALREADY
    happened once (migration 563, migration 342, the `chart_dashas` incident) — would
    therefore appear with nothing to notice it. The only reason the first four were
    ever found was a verifier chasing an arithmetic mismatch by hand (PARIKṢAKA V-70's
    own closing observation) — luck with good habits attached, not a detector.

    THE INVARIANT IS COMPLETENESS, NOT MONOTONICITY (D-111 part 2 — read this before
    touching the rule below). Every OTHER assertion this campaign shipped today
    (the entrypoint allowlist, the X-06 unearned-lit floor) is an allowlist: amnesty
    for a defect, and amnesty may only shrink. `asset_id_lineage_manifest.json` is NOT
    an allowlist — it is a RECORD, and a record's job is to grow when a new fact
    exists to record. A rename next month SHOULD add a fifth entry. Building this rule
    as a shrink-only/frozen-population ratchet (the X-06 shape) would therefore be
    EXACTLY BACKWARDS — it would block the very future renames this manifest exists to
    document. So this is a SET EQUALITY assertion (D-84 set-not-count, third use
    today), never a subset/floor comparison:

        {ids in build_run_assets absent from asset_registry} == {manifest's ids}

    naming any difference in EITHER direction:
      - `orphan_missing_from_manifest`     — a live orphan the manifest does not
        record (a new rename/retirement/operator-error happened and nobody logged its
        disposition yet — D-111's primary failure shape).
      - `manifest_entry_not_a_live_orphan` — a manifest entry whose id is no longer
        (or never was) a live orphan — the manifest DELETED an entry while the orphan
        itself still sits in `build_run_assets` (D-111's second named failure shape;
        a one-directional "every orphan is recorded" check would miss exactly this).

    THE FAILURE MODE IS UNDETERMINED-AND-FATAL, NOT ADVISORY (D-111 part 3): a set
    mismatch here is a state the campaign cannot interpret, and per CLAUDE.md §N.8 a
    detector that cannot answer must not return the answer that looks green. This is
    why the rule is BLOCKING and reports FAIL (not NOT_CHECKABLE) the moment both id
    sets are known and disagree — including when the manifest is entirely ABSENT: a
    missing manifest file is treated as an empty enumerated set, not as "cannot
    evaluate," because "the manifest was never created" is precisely the pre-D-103
    state this rule exists to make loud instead of silent. NOT_CHECKABLE is reserved
    for genuine input absence (no `build_run_assets` evidence in the snapshot at all)
    or a manifest file that exists but fails to parse (corruption, not omission) —
    the guard cannot compute a verdict from data it does not have, but "no manifest
    was ever written" is data (an empty record), not a hole. The rule blocks until a
    human/KĀRAKA task adds or corrects a manifest entry with a DETERMINED disposition
    — derived from a migration or live evidence, never guessed, exactly as D-103
    required of the original four and as M0-T75 actually did.

    ANCHOR: the orphan population is read from `build_run_asset_ids_all` — the FULL,
    state-independent distinct `asset_id` list from `build_run_assets` (added to
    `read_live()` for this rule) — never from `s.raw["build_run_assets"]` alone,
    because that key is X-06's and is deliberately scoped to COMPLETE-state evidence
    only (X-06 only needs to know a build *succeeded*). At least one of the four known
    orphans (`ga_pyjhora_engine`: 10 rows, states {aborted, error}, ZERO complete) has
    NO complete-state row at all and would be invisible to a rule that reused X-06's
    narrower key — reusing it here would silently under-count the very population
    this rule exists to reconcile.

    PER-ENTRY SHAPE/EVIDENCE CHECK (D-116, ADHIKĀRIN, closing PARIKṢAKA V-74 /
    F-V74-1) — the set-equality assertion above makes the POPULATION complete; it
    reads nothing about any individual entry, so D-111's own "the manifest may grow"
    ruling made GROWTH the sanctioned way to clear a future failure: add an entry
    with the right `asset_id` and any content at all. `_check_manifest_entry_shape`
    (above) closes that by checking each entry, TIERED by disposition class. READ
    THIS PLAINLY, BECAUSE IT IS THE PART MOST LIKELY TO BE OVERCLAIMED: a GREEN
    result from this rule means, for a `legacy_never_registered` entry, ONLY that a
    disposition (a key of the manifest's own `disposition_vocabulary`) and a
    non-empty `evidence` array were SUPPLIED — it does NOT mean that evidence was
    independently verified, because no cheap mechanical check can establish a
    negative ("this id was never a valid asset_registry.asset_id"). For a
    migration-citing entry (`renamed`/`deleted` — identified by a
    `renamed_by_migration`/`deleted_by_migration` field), green DOES mean the cited
    migration file exists and its content references the entry's `asset_id` — a real
    evidence assertion, not a shape assertion, because that evidence is genuinely
    machine-checkable. NEVER read an X-07 PASS, in this artifact or any cockpit
    signal downstream of it, as "every disposition is verified" — for
    `legacy_never_registered` entries it means only that a disposition and evidence
    were supplied.
    """
    all_ids = s.raw.get("build_run_asset_ids_all")
    if all_ids is None:
        return Result(NOT_CHECKABLE, [], (
            "no build_run_asset_ids_all section in this snapshot — the full, "
            "state-independent build_run_assets id population this rule reconciles "
            "against the manifest cannot be computed"))
    manifest = _load_json(LINEAGE_MANIFEST_PATH)
    if manifest is None:
        if LINEAGE_MANIFEST_PATH.exists():
            return Result(NOT_CHECKABLE, [], (
                f"lineage manifest exists but is not parseable JSON: "
                f"{LINEAGE_MANIFEST_PATH.name} — corruption, not omission; the guard "
                f"cannot compute a verdict from data it cannot read"))
        manifest = {"entries": []}   # ABSENT is an empty RECORD, not a null verdict —
        # see the doc-comment above: this is the exact pre-D-103 shape the rule exists
        # to catch, and must FAIL loudly rather than go quiet for lack of a file.

    manifest_entries = manifest.get("entries") or []
    manifest_ids = {e["asset_id"] for e in manifest_entries}
    live_orphans = {aid for aid in set(all_ids) if aid not in s.by_id}

    undocumented = sorted(live_orphans - manifest_ids)
    stale = sorted(manifest_ids - live_orphans)
    v = [{"asset_id": aid, "class": "orphan_missing_from_manifest"}
         for aid in undocumented]
    v += [{"asset_id": aid, "class": "manifest_entry_not_a_live_orphan"}
          for aid in stale]

    # D-116 / F-V74-1 — per-entry shape/evidence check, TIERED by disposition class.
    # `vocab` is read from the manifest's OWN declared `disposition_vocabulary`,
    # never hardcoded here (an absent/empty vocabulary means every entry fails the
    # membership check, which is correct: an undeclared vocabulary cannot vouch for
    # any disposition).
    vocab = set((manifest.get("disposition_vocabulary") or {}).keys())
    for entry in manifest_entries:
        v += _check_manifest_entry_shape(entry, vocab)

    return verdict(v, detail={
        "live_orphan_ids": sorted(live_orphans),
        "manifest_ids": sorted(manifest_ids),
        "undocumented_orphans": undocumented,
        "stale_manifest_entries": stale,
        "disposition_vocabulary_keys": sorted(vocab),
        "class_counts": _counts(v) if v else {},
    })


def _counts(rows: list[dict]) -> dict:
    out: dict[str, int] = {}
    for r in rows:
        out[r.get("class", "unclassified")] = out.get(r.get("class", "unclassified"), 0) + 1
    return out


# ─────────────────────────────────────────────────────────────────────────────
# X-01 … X-05 — campaign extension rules (NOT contract rules)
# ─────────────────────────────────────────────────────────────────────────────
def _load_json(p: pathlib.Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def x01(s: Snapshot) -> Result:
    """Multi-producer collision on a target_table, MINUS the declared co-writers.

    The contract's de-duplication invariant is one authoritative producer per
    (target_table × generation × natural-key partition), NOT one per table (§4.9).
    Five tables have multiple active producers today and are legitimate; failing on
    them would be a guard demanding a repair the contract does not ask for. So this
    rule distinguishes a DECLARED co-writer set from an UNDECLARED collision, and
    only the undeclared kind is a violation.

    It does NOT check that each co-writer's partition is disjoint — that is C-25,
    which has no column and stays not_checkable. A pass here is 'no collision nobody
    declared', never 'the partitions are correct'.
    """
    decl = _load_json(COWRITERS_PATH)
    if decl is None:
        return Result(NOT_CHECKABLE, [], f"declared co-writer file unreadable: "
                                         f"{COWRITERS_PATH.name}")
    declared = decl.get("declared_cowriter_tables") or {}
    groups: dict[str, list[str]] = {}
    for a in s.assets:
        tt = a.get("target_table")
        if tt and a.get("is_active") is not False:
            groups.setdefault(tt, []).append(a["asset_id"])
    v, undeclared_extra = [], []
    for tt, ids in sorted(groups.items()):
        if len(ids) < 2:
            continue
        if tt not in declared:
            v.append({"target_table": tt, "producers": sorted(ids),
                      "class": "undeclared_collision"})
            continue
        known = set(declared[tt].get("producers") or [])
        new = sorted(set(ids) - known)
        if new:
            undeclared_extra.append({"target_table": tt, "new_producers": new,
                                     "declared_producers": sorted(known),
                                     "class": "new_producer_in_declared_group"})
    return verdict(v + undeclared_extra, detail={
        "declared_tables": sorted(declared),
        "multi_producer_tables_seen": sorted(t for t, i in groups.items() if len(i) > 1),
        "partition_disjointness_not_checked": "see C-25 (not_checkable — no column)"})


def x02(s: Snapshot) -> Result:
    """asset_throughput rows on inactive / RETIRED assets.

    ⚠ NON-BLOCKING BY CONSTRUCTION (severity RESIDUAL). The only such rows today
    belong to `ka_gochara_sweep`, charter P1's named unrecoverable asset. ADHIKĀRIN
    ruling D-12 part 4 routes them to R3 by name and states M0 "CLOSES WITH THIS
    CRITERION EXPLICITLY UNMET AND RECORDED AS DEFERRED-TO-R3 — never silently green".

    This guard therefore does NOT let a disclosure turn the rule green. Disclosed
    rows are reported as violations with their disclosure attached, and the rule
    reports `fail`; what the disclosure buys is that the severity is RESIDUAL, so the
    failure does not gate. Making it gate would force a later agent to touch a P1
    asset to get CI green — which is how a gate becomes a reason to break a
    prohibition.
    """
    if s.throughput is None:
        return Result(NOT_CHECKABLE, [], "no asset_throughput section in this snapshot")
    res = _load_json(RESIDUALS_PATH)
    if res is None:
        return Result(NOT_CHECKABLE, [], f"residuals file unreadable: {RESIDUALS_PATH.name}")
    disclosed = res.get("disclosed_additions") or {}
    required = ("owner", "landed_at", "disclosed_via", "reason", "deferred_to")
    for key, ent in disclosed.items():
        missing = [f for f in required if not ent.get(f)]
        if missing:
            raise GuardError(
                f"disclosed residual '{key}' is missing required field(s) "
                f"{missing} — an incomplete disclosure is not a disclosure "
                f"(mirrors migration_number_guard.ts error E4)")
    v = []
    for aid, t in sorted(s.throughput.items()):
        a = s.by_id.get(aid)
        if a is None:
            v.append({"asset_id": aid, "class": "throughput_on_unregistered_asset",
                      "throughput_rows": t.get("throughput_rows")})
            continue
        inactive = a.get("is_active") is False
        retired = a.get("catalog_status") == "RETIRED"
        if inactive or retired:
            row = {"asset_id": aid, "is_active": a.get("is_active"),
                   "catalog_status": a.get("catalog_status"),
                   "throughput_rows": t.get("throughput_rows"),
                   "states": t.get("states"),
                   "class": "throughput_on_inactive_or_retired"}
            d = disclosed.get(aid)
            row["disclosed"] = bool(d)
            if d:
                row["disclosure"] = d
            v.append(row)
    return verdict(v, detail={
        "disclosed_keys": sorted(disclosed),
        "undisclosed_count": sum(1 for x in v if not x.get("disclosed")),
        "why_non_blocking": "severity RESIDUAL per ADHIKĀRIN D-12 part 4 "
                            "(deferred to R3, never silently green)"})


def x03(s: Snapshot) -> Result:
    """An active asset with neither build coverage nor a dead flag.

    'Build coverage' = at least one asset_throughput row. The only exemptions are the
    two states that mean "this row is not expected to build at all": `is_active=false`
    / `catalog_status='RETIRED'` (it has exited service), and `asset_kind='source'`
    (ingested data the DAG reads and never builds, contract §7).

    `has_writer = false` is NOT an exemption, and the first draft of this rule wrongly
    made it one. That draft returned 0 violations over the live registry — because the
    only two assets it could ever have caught (`bg_gochara_citation_resolution`,
    `lel_events`) are precisely the two that carry `has_writer=false`. A rule that
    exempts the only population it can detect is a constant wearing a detector's
    clothes (CLAUDE.md §N.8), which is the defect this whole campaign exists to remove.
    `has_writer=false` on an ACTIVE row is the finding — the contract's §7 says it in
    as many words: "never leave a CURRENT asset that nothing can build" — so it is
    reported, as its own class, not excused.
    """
    if s.throughput is None:
        return Result(NOT_CHECKABLE, [], "no asset_throughput section in this snapshot")
    v = []
    for a in s.assets:
        aid = a["asset_id"]
        if a.get("is_active") is False or a.get("catalog_status") == "RETIRED":
            continue
        if a.get("asset_kind") == "source":
            continue
        if aid in s.throughput:
            continue
        cls = ("no_coverage_and_no_writer_registered"
               if s.has("has_writer") and a.get("has_writer") is False
               else "no_coverage_writer_registered_never_built")
        v.append({"asset_id": aid, "catalog_status": a.get("catalog_status"),
                  "asset_kind": a.get("asset_kind"),
                  "has_writer": a.get("has_writer"), "class": cls})
    return verdict(v, detail={"class_counts": _counts(v)})


def x04(s: Snapshot) -> Result:
    """Domain coherence (plan §11): a shared asset may depend only on shared assets.

    "A chart-independent writer cannot read per-chart data without silently binding
    itself to one chart." The plan states this may well fail first on the four shared
    assets above L0 and that a failure there is a registration defect resolved in the
    owning rung — not a reason to weaken the rule.

    HONEST SCOPE, because a green here is easy to over-read: this rule checks DECLARED
    `depends_on` edges only. The plan's actual suspicion — that a shared L3 service
    probe "reads per-chart data to answer 'am I healthy?'" — is about what the writer
    READS, which no registry column records. A pass here means "no shared asset
    DECLARES a chart-domain upstream", never "no shared writer touches per-chart
    data". The read-vs-declared audit is plan §11's separate declared-vs-read item and
    is not implemented by this guard.
    """
    v, prov = [], None
    for a in s.assets:
        dom, prov = s.domain_of(a)
        if dom != "shared":
            continue
        for d in s.deps(a):
            b = s.by_id.get(d)
            if b is None:
                continue          # dangling — C-12's finding, not this rule's
            bdom, _ = s.domain_of(b)
            if bdom != "shared":
                v.append({"asset_id": a["asset_id"], "layer": a.get("layer"),
                          "dep": d, "dep_domain": bdom,
                          "class": "shared_depends_on_chart"})
    return verdict(v, detail={"domain_provenance": prov,
                              "class_counts": _counts(v)})


def x05(s: Snapshot) -> Result:
    """Unresolved zero-consumer findings.

    Reads the 23 evidence packets of ZERO_CONSUMER_EVIDENCE_v1_0 / .json (M0-T7). A
    packet is RESOLVED only when an explicit, dated disposition for that asset exists
    in asset_catalogue_disclosed_residuals.json's `zero_consumer_dispositions` block,
    naming the DECISIONS.jsonl ruling that made it (disposition is charter G1 —
    ADHIKĀRIN's, never this guard's and never a KĀRAKA's). Anything else is
    unresolved, which is a `fail`, not a `not_checkable`: the packet exists, the
    detector ran, and the answer is "no ruling yet".
    """
    packets = s.zero_consumer
    if packets is None:
        ev = _load_json(CONTROL / "zero_consumer_evidence.json")
        packets = (ev or {}).get("assets")
    if packets is None:
        return Result(NOT_CHECKABLE, [], (
            "zero_consumer_evidence.json not readable and no zero_consumer_packets in "
            "the snapshot — the 23 M0-T7 packets are the input this rule reduces"))
    res = _load_json(RESIDUALS_PATH) or {}
    disp = res.get("zero_consumer_dispositions") or {}
    v = []
    for aid in sorted(packets):
        d = disp.get(aid)
        if not d:
            v.append({"asset_id": aid, "class": "no_disposition_recorded"})
        elif not d.get("decision_ref"):
            v.append({"asset_id": aid, "class": "disposition_without_decision_ref",
                      "disposition": d})
    return verdict(v, detail={"packets": len(packets),
                              "dispositions_recorded": len(disp)})


# ─────────────────────────────────────────────────────────────────────────────
# Rule table
# ─────────────────────────────────────────────────────────────────────────────
NOT_CHECKABLE_REASONS = {
    "C-25": ("no schema column exists for a natural-key partition declaration "
             "(contract §4.9, §10.3). §6 states this rule must never be reported as "
             "passing; there is no detector, so its verdict is null."),
    "C-26": ("no schema column exists for an authority pointer / protected_generations "
             "(contract §4.11, §10.3). No detector, so null — never green."),
    "C-27": ("not checkable until Track M2 produces cleaned telemetry (contract §4.8). "
             "ADVISORY, and explicitly NOT reported as green."),
}

CONTRACT_RULES: list[Rule] = [
    Rule("C-01", BLOCKING, "asset_id prefix matches layer, non-source rows", c01),
    Rule("C-02", BLOCKING, "layer_index matches ^L[0-5]$ and agrees with layer", c02),
    Rule("C-03", BLOCKING, "layer_name is the exact lexicon spelling for layer", c03),
    Rule("C-04", BLOCKING, "data/artifact ⇒ target_table NOT NULL and the table exists", c04),
    Rule("C-05", BLOCKING, "data/artifact ⇒ count_sql NOT NULL", c05),
    Rule("C-06", BLOCKING, "chart-domain count_sql contains $1", c06),
    Rule("C-07", BLOCKING, "service ⇒ target_table/count_sql/target_floor/clear_tables NULL", c07),
    Rule("C-08", BLOCKING, "RETIRED ⇒ data_disposition NOT NULL", c08),
    Rule("C-09", BLOCKING, "superseded_by resolves to an existing asset_id", c09),
    Rule("C-10", BLOCKING, "data_disposition only on RETIRED rows", c10),
    Rule("C-11", BLOCKING, "CURRENT depends only on CURRENT (or source)", c11),
    Rule("C-12", BLOCKING, "every depends_on element resolves", c12),
    Rule("C-13", BLOCKING, "depends_on graph is acyclic and self-reference-free", c13),
    Rule("C-14", BLOCKING, "asset_kind and asset_type are coherent", c14),
    Rule("C-15", BLOCKING, "service ⇒ health_probe and provides_apis NOT NULL", c15),
    Rule("C-16", BLOCKING, "non-service ⇒ service_health IS NULL", c16),
    Rule("C-17", BLOCKING, "graded service_health ⇒ health_probe NOT NULL", c17),
    Rule("C-18", BLOCKING, "domain present and derived from scope", c18),
    Rule("C-19", BLOCKING, "rung present and derived from layer", c19),
    Rule("C-20", BLOCKING, "CURRENT data/artifact ⇒ target_floor NOT NULL", c20),
    Rule("C-21", BLOCKING, "target_floor = 0 ⇒ volume_explanation NOT NULL", c21),
    Rule("C-22", RUNG, "frozen rung data/artifact ⇒ integrity_check_sql NOT NULL", c22),
    Rule("C-23", BLOCKING, "has_substeps equals the writer-class truth", c23),
    Rule("C-24", BLOCKING, "clear_tables elements exist and include target_table", c24),
    Rule("C-25", BLOCKING, "co-written target_table ⇒ every co-writer declares its partition",
         _no_detector("C-25", NOT_CHECKABLE_REASONS["C-25"])),
    Rule("C-26", BLOCKING, "generation-bearing asset declares its authority pointer",
         _no_detector("C-26", NOT_CHECKABLE_REASONS["C-26"])),
    Rule("C-27", ADVISORY, "writer_timeout_seconds set from telemetry where p95 ≥ 0.5×",
         _no_detector("C-27", NOT_CHECKABLE_REASONS["C-27"])),
    Rule("C-28", BLOCKING, "estimated_seconds NOT NULL where a successful build exists", c28),
]

EXTENSION_RULES: list[Rule] = [
    Rule("X-01", BLOCKING, "no UNDECLARED multi-producer collision on a target_table",
         x01, origin="plan §14.1 M0 exit criteria (multi-producer partitions)"),
    Rule("X-02", RESIDUAL, "no asset_throughput rows on inactive/RETIRED assets",
         x02, origin="plan §14.1 M0 exit criteria; DEFERRED-TO-R3 per D-12 part 4"),
    Rule("X-03", BLOCKING, "no active asset with neither build coverage nor a dead flag",
         x03, origin="plan §14.1 M0 exit criteria (active-without-coverage)"),
    Rule("X-04", BLOCKING, "domain coherence: a shared asset depends only on shared assets",
         x04, origin="plan §11 (CI shape guard addition)"),
    Rule("X-05", BLOCKING, "no unresolved zero-consumer finding",
         x05, origin="plan §14.1 M0 exit criteria; packets from M0-T7"),
    Rule("X-06", BLOCKING,
         "no growth in the cross-kind unearned-lit population (asset_throughput."
         "state='lit' with zero completed build_run_assets records, ALL asset_kind) "
         "beyond the committed floor",
         x06, origin="D-94 (ADHIKĀRIN, F-Y — exit by recategorization); floor-not-"
                     "HEAD^ pattern D-95"),
    Rule("X-07", BLOCKING,
         "build_run_assets orphan ids (absent from asset_registry) equal "
         "asset_id_lineage_manifest.json's enumerated set exactly, naming any "
         "difference in either direction",
         x07, origin="D-111 (ADHIKĀRIN), closing PARIKṢAKA V-70 / F-V70-2 — D-103 "
                     "built the manifest and appointed no reader"),
]

ALL_RULES = CONTRACT_RULES + EXTENSION_RULES


# ─────────────────────────────────────────────────────────────────────────────
# Cross-check
# ─────────────────────────────────────────────────────────────────────────────
def cross_check(contract_rows: dict) -> list[str]:
    problems = []
    impl = {r.id: r for r in CONTRACT_RULES}
    for rid in sorted(set(contract_rows) | set(impl)):
        doc, code = contract_rows.get(rid), impl.get(rid)
        if doc and not code:
            problems.append(f"{rid}: present in the contract §6 table, NOT implemented "
                            f"by this guard — a spec rule with no detector")
        elif code and not doc:
            problems.append(f"{rid}: implemented by this guard, ABSENT from the "
                            f"contract §6 table — the guard has invented a rule")
        else:
            if doc["severity"] != code.severity:
                problems.append(f"{rid}: severity disagreement — contract says "
                                f"{doc['severity']}, guard says {code.severity}")
            if doc["declared_not_checkable"] and code.fn.__name__ != "f":
                problems.append(
                    f"{rid}: the contract §6 table marks it not checkable, but this "
                    f"guard implements a detector for it — one of the two is wrong")
            if (not doc["declared_not_checkable"]) and code.fn.__name__ == "f":
                problems.append(
                    f"{rid}: this guard hard-wires it NOT_CHECKABLE, but the contract "
                    f"§6 table does not mark it not checkable")
    for r in EXTENSION_RULES:
        if r.id in contract_rows:
            problems.append(f"{r.id}: extension rule id collides with a contract rule id")
    return problems


# ─────────────────────────────────────────────────────────────────────────────
# Live read (READ-ONLY)  — charter P4: DATABASE_URL never printed or stored
# ─────────────────────────────────────────────────────────────────────────────
def _database_url() -> str:
    env = REPO_ROOT / "platform" / ".env.local"
    for line in env.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+)$", line)
            if m:
                return m.group(1).strip().strip("\"'")
    raise GuardError("DATABASE_URL not found in platform/.env.local")


def read_live() -> dict:
    import psycopg
    import psycopg.rows
    snap: dict[str, Any] = {"_meta": {
        "source": "live asset_registry (READ-ONLY)",
        "read_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "credential": "read from platform/.env.local; never printed, logged or stored",
    }}
    with psycopg.connect(_database_url(), row_factory=psycopg.rows.dict_row,
                         autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '60s'")
        cur.execute("SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='asset_registry' "
                    "ORDER BY ordinal_position")
        cols = [r["column_name"] for r in cur.fetchall()]
        snap["registry_columns"] = cols
        cur.execute(f"SELECT {', '.join(cols)} FROM asset_registry ORDER BY asset_id")
        snap["assets"] = [
            {k: (v.isoformat() if isinstance(v, (_dt.datetime, _dt.date)) else v)
             for k, v in r.items()} for r in cur.fetchall()]
        cur.execute("SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'")
        snap["public_tables"] = sorted(r["table_name"] for r in cur.fetchall())
        cur.execute("""SELECT asset_id, count(*) AS throughput_rows,
                              array_agg(DISTINCT state ORDER BY state) AS states,
                              sum(COALESCE(rows_written,0)) AS rows_written_total
                       FROM asset_throughput GROUP BY asset_id ORDER BY asset_id""")
        snap["throughput"] = [dict(r) for r in cur.fetchall()]
        # X-06 (D-94): the ONLY table that can hold EVIDENCE a build actually ran.
        # Distinct asset_ids with at least one COMPLETE run — the exact shape
        # c28_population_probe's synthetic fixture already uses, so a live and a
        # synthetic Snapshot agree on what this key means.
        cur.execute("""SELECT DISTINCT asset_id, 'complete' AS state
                       FROM build_run_assets WHERE state='complete'
                       ORDER BY asset_id""")
        snap["build_run_assets"] = [dict(r) for r in cur.fetchall()]
        # X-07 (D-111): the FULL, state-independent distinct asset_id population from
        # build_run_assets — deliberately a SEPARATE key from `build_run_assets`
        # above, which X-06 scopes to complete-state evidence only. At least one of
        # the four known orphans (ga_pyjhora_engine: 10 rows, states {aborted, error},
        # zero complete) would be invisible under the complete-only key; X-07 needs
        # the whole population to reconcile against the lineage manifest.
        cur.execute("SELECT DISTINCT asset_id FROM build_run_assets ORDER BY asset_id")
        snap["build_run_asset_ids_all"] = [r["asset_id"] for r in cur.fetchall()]
    # The census FILE is carried into the snapshot for provenance and for C-23's
    # stale-artifact report ONLY. Since M0-T25 it is NOT C-23's truth source: C-23
    # derives the writer-class truth from source at run time, so a census file that
    # nobody regenerated can no longer make the rule green (see c23 /
    # code_writer_substep_truth).
    wc = _load_json(CONTROL / "writer_substep_census.json")
    if wc and isinstance(wc.get("writers"), dict):
        snap["writer_substep_truth"] = {
            aid: bool(recs[0].get("writer_truth_has_substeps"))
            for aid, recs in wc["writers"].items() if recs}
    zc = _load_json(CONTROL / "zero_consumer_evidence.json")
    if zc and zc.get("assets"):
        snap["zero_consumer_packets"] = {k: True for k in zc["assets"]}
    snap["frozen_rungs"] = []
    return snap


# ─────────────────────────────────────────────────────────────────────────────
# Runner + reporting
# ─────────────────────────────────────────────────────────────────────────────
def run_rules(snap: Snapshot) -> dict:
    # Disclosures are loaded ONCE per run and validated before any rule is judged: a
    # malformed disclosure must stop the guard (exit 3), never be skipped past.
    disclosures = load_rule_disclosures()
    decisions = decision_index()
    out: dict[str, dict] = {}
    for r in ALL_RULES:
        try:
            res = r.fn(snap)
        except GuardError:
            raise
        except Exception as e:                       # noqa: BLE001
            res = Result(NOT_CHECKABLE, [], f"rule raised {type(e).__name__}: {e}")
        d = res.as_dict()
        # `severity` stays the DECLARED severity — the contract cross-check compares
        # against it, and a disclosure must never be able to rewrite what the spec says
        # this rule is. The disclosure's effect lands in `effective_severity`.
        d.update({"severity": r.severity, "statement": r.statement, "origin": r.origin})
        apply_rule_disclosures(r.id, r.severity, d, disclosures, decisions)
        out[r.id] = d
    return out


def summarise(results: dict) -> dict:
    s = {"pass": 0, "fail": 0, "not_checkable": 0,
         "blocking_failures": [], "rung_failures": [],
         "residual_failures": [], "advisory_failures": [],
         "disclosed_non_gating_failures": [],
         "not_checkable_rules": [],
         # D-30 part 4 is a condition about disclosures, so the guard reports on it
         # mechanically rather than leaving it to be asserted in prose.
         "failing_rules_with_disclosure": [],
         "failing_rules_without_disclosure": [],
         "disclosures_recorded_without_effect": []}
    for rid, r in sorted(results.items()):
        s[r["status"]] += 1
        disc = r.get("disclosure") or {}
        if r["status"] == FAIL:
            key = {BLOCKING: "blocking_failures", RUNG: "rung_failures",
                   RESIDUAL: "residual_failures", ADVISORY: "advisory_failures",
                   DISCLOSED_NON_GATING: "disclosed_non_gating_failures",
                   }[r.get("effective_severity", r["severity"])]
            s[key].append(rid)
            (s["failing_rules_with_disclosure"] if disc.get("count")
             else s["failing_rules_without_disclosure"]).append(rid)
        elif r["status"] == NOT_CHECKABLE:
            s["not_checkable_rules"].append(rid)
        if disc.get("count") and disc.get("effect") == "none":
            s["disclosures_recorded_without_effect"].append(rid)
    return s


def emit_text(results: dict, summary: dict, header: str, max_rows: int,
              staleness: dict | None = None) -> None:
    print(header)
    print("=" * len(header))
    if staleness:
        emit_staleness(staleness)
    for rid in sorted(results):
        r = results[rid]
        badge = {PASS: "PASS ", FAIL: "FAIL ", NOT_CHECKABLE: "NULL "}[r["status"]]
        print(f"  [{badge}] {rid} ({r['severity']:8s}) {r['statement']}")
        if r["status"] == FAIL:
            print(f"           violations: {r['violation_count']}")
            for row in r["violations"][:max_rows]:
                print(f"             - {json.dumps(row, ensure_ascii=False)}")
            if r["violation_count"] > max_rows:
                print(f"             … {r['violation_count'] - max_rows} more")
        if r["status"] == NOT_CHECKABLE:
            print(f"           not_checkable: {r['reason']}")
        if r["detail"].get("class_counts"):
            print(f"           classes: {r['detail']['class_counts']}")
        disc = r.get("disclosure") or {}
        if disc.get("count"):
            print(f"           disclosure: {disc['keys']} effect={disc['effect']} "
                  f"(declared {r.get('declared_severity')} -> effective "
                  f"{r.get('effective_severity')})")
            for n in disc.get("notes") or []:
                print(f"             · {n}")
    print()
    print(f"  pass={summary['pass']}  fail={summary['fail']}  "
          f"not_checkable={summary['not_checkable']}")
    print(f"  BLOCKING failures : {summary['blocking_failures'] or 'none'}")
    print(f"  RUNG failures     : {summary['rung_failures'] or 'none'}")
    print(f"  RESIDUAL failures : {summary['residual_failures'] or 'none'} "
          f"(non-gating by construction — see X-02)")
    print(f"  ADVISORY failures : {summary['advisory_failures'] or 'none'}")
    print(f"  DISCLOSED non-gating failures : "
          f"{summary['disclosed_non_gating_failures'] or 'none'} "
          f"(REPORTED IN FULL above; demoted only by an itemised disclosure whose "
          f"`covers` includes every one of their violations AND lies inside the "
          f"`authorised_covers` grant of the ADHIKĀRIN decision it cites)")
    print(f"  not_checkable     : {summary['not_checkable_rules'] or 'none'}")
    print(f"  failing rules WITHOUT a disclosure entry : "
          f"{summary['failing_rules_without_disclosure'] or 'none'}")
    print(f"  disclosures recorded but with NO gating effect : "
          f"{summary['disclosures_recorded_without_effect'] or 'none'}")
    print("  NOTE: not_checkable is NOT a pass. A rule whose input column or data "
          "does not exist has produced no verdict (CLAUDE.md §N.8).")
    print("  NOTE: a disclosure never turns a rule green. Every violation above is "
          "reported whether disclosed or not; a disclosure can only stop a failure "
          "from gating, and only over the rows it itemises.")


def emit_staleness(st: dict) -> None:
    """Print the snapshot's age. Always — a silent freshness check is not a check."""
    verdict_word = "STALE" if st["stale"] else "no staleness detected"
    print(f"  SNAPSHOT FRESHNESS [{verdict_word}] read_at={st['read_at']} "
          f"age_hours={st['age_hours']} max={st['max_age_hours']} "
          f"schema_behind={st['schema_behind_columns'] or 'none'}")
    for r in st["reasons"]:
        print(f"      · {r}")
    if not st["stale"]:
        print(f"      · {st['what_a_clean_result_means']}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────
def self_test(max_rows: int) -> int:
    contract_rows = parse_contract(CONTRACT_PATH)
    problems = cross_check(contract_rows)
    if problems:
        print("GUARD ERROR — guard and contract document disagree:")
        for p in problems:
            print("  -", p)
        return 3
    print(f"contract cross-check OK — {len(contract_rows)} rules parsed from "
          f"{CONTRACT_PATH.relative_to(REPO_ROOT)}, all implemented, severities agree, "
          f"and every rule the document marks not checkable is hard-wired "
          f"NOT_CHECKABLE here.")
    fixtures = sorted(FIXTURES.rglob("*.json"))
    if not fixtures:
        print(f"GUARD ERROR — no fixtures under {FIXTURES}")
        return 3
    failures = 0
    for fx in fixtures:
        raw = json.loads(fx.read_text(encoding="utf-8"))
        expect = raw.pop("_expect", None)
        if not expect:
            print(f"GUARD ERROR — fixture {fx.name} declares no _expect block; a "
                  f"fixture with no expectation cannot detect a partial regression")
            failures += 1
            continue
        results = run_rules(Snapshot(raw, synthetic=True))
        summary = summarise(results)
        bad = []
        for rid, want in sorted(expect.items()):
            got = results.get(rid)
            if got is None:
                bad.append(f"{rid}: expected {want}, rule not implemented")
                continue
            if isinstance(want, str):
                want = {"status": want}
            if got["status"] != want["status"]:
                bad.append(f"{rid}: expected status {want['status']}, got "
                           f"{got['status']} ({got['reason'] or ''})")
            if "violation_count" in want and got["violation_count"] != want["violation_count"]:
                bad.append(f"{rid}: expected {want['violation_count']} violations, "
                           f"got {got['violation_count']}")
        rel = fx.relative_to(FIXTURES)
        if bad:
            failures += 1
            print(f"  [FIXTURE FAIL] {rel}")
            for b in bad:
                print(f"      - {b}")
            emit_text(results, summary, f"    (full result for {rel})", max_rows)
        else:
            print(f"  [FIXTURE OK  ] {rel} — {len(expect)} expectations met "
                  f"(pass={summary['pass']} fail={summary['fail']} "
                  f"not_checkable={summary['not_checkable']})")
    failures += c23_code_derivation_probe()
    failures += rule_disclosure_probe()
    failures += c28_population_probe()
    failures += x06_ratchet_probe()
    failures += x07_manifest_completeness_probe()
    failures += snapshot_staleness_probe()

    if failures:
        print(f"\nSELF-TEST FAILED: {failures} check(s) did not behave as declared.")
        return 3
    print("\nself-test OK — every fixture behaved exactly as its _expect block declares, "
          "including every fixture built to make a rule FAIL, and C-23's code-derived "
          "truth was proved to fail on a divergence its declared map calls clean.")
    return 0


def c23_code_derivation_probe() -> int:
    """Prove C-23's NEW truth source works, and prove it CAN fail (D-24 part 3).

    The four bundled fixtures exercise C-23's COMPARISON on a synthetic registry with
    a declared truth map. They cannot exercise the thing M0-T25 changed — that the
    truth is derived from the writer classes at run time rather than read from a
    checked-in artifact. This probe does, DB-free, against this repo's real writer
    tree, and it is the fixture ADHIKĀRIN D-24 part 3 requires on every guard this
    campaign ships: an assertion is not earned until something has been shown to make
    it go red.

    Case 2 is the regression test for the defect itself: the declared map agrees with
    the registry, and the code does not. The old file-sourced C-23 called that state
    PASS. It must now FAIL.

    Returns the number of probe failures (0 = all four cases behaved).
    """
    global _CODE_TRUTH
    print("\n  C-23 code-derivation probe (the truth is parsed from the writer "
          "classes, not read from a file):")
    bad = 0
    truth, prov = code_writer_substep_truth(force=True)
    if truth is None:
        print(f"      - PROBE NOT CHECKABLE: {prov.get('reason')}")
        print("        The writer tree ships in this repository, so a derivation that "
              "cannot run means a broken checkout, not an excusable skip. Counted as "
              "a failure rather than passed over (§N.8).")
        return 1
    heavy = sorted(a for a, t in truth.items() if t)
    light = sorted(a for a, t in truth.items() if not t)
    if not heavy or not light:
        print(f"      - PROBE NOT CHECKABLE: the census found heavy={len(heavy)} "
              f"light={len(light)}; the probe needs at least one of each to build a "
              f"two-sided divergence")
        return 1
    h, l = heavy[0], light[0]
    print(f"      derived from source: {prov.get('files_scanned')} files, "
          f"{prov.get('registrations')} @register decorators, "
          f"{prov.get('heavy')} heavy / {prov.get('light')} light")
    print(f"      probe assets: heavy={h}  light={l}")

    def snap(reg_h: bool, reg_l: bool, declared: dict | None) -> dict:
        raw = {"assets": [{"asset_id": h, "has_substeps": reg_h},
                          {"asset_id": l, "has_substeps": reg_l}]}
        if declared is not None:
            raw["writer_substep_truth"] = declared
        return raw

    def check(label: str, raw: dict, want_status: str, want_n: int | None,
              want_stale: int | None = None) -> None:
        nonlocal bad
        r = c23(Snapshot(raw)).as_dict()
        ok = r["status"] == want_status and (want_n is None
                                             or r["violation_count"] == want_n)
        if want_stale is not None:
            ok = ok and r["detail"].get("declared_truth_stale_vs_code") == want_stale
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}: status={r['status']} "
              f"violations={r['violation_count']} "
              f"classes={r['detail'].get('class_counts')} "
              f"declared_stale={r['detail'].get('declared_truth_stale_vs_code')}")
        if not ok:
            bad += 1
            print(f"          expected status={want_status} violations={want_n} "
                  f"declared_stale={want_stale}")
            if r["reason"]:
                print(f"          reason: {r['reason']}")

    # 1 — registry agrees with the code: pass.
    check("registry agrees with the writer classes", snap(True, False, None),
          PASS, 0)
    # 2 — THE DEFECT. Registry has drifted BOTH ways, and the declared map agrees with
    #     the drifted registry, exactly as a census file that nobody regenerated would.
    #     File-sourced C-23 passed here. Code-sourced C-23 must fail, twice.
    check("registry drifted AND the declared map is stale in the same direction "
          "(the old guard's blind spot)",
          snap(False, True, {h: False, l: True}), FAIL, 2, want_stale=2)
    # 3 — same drift with no declared map at all: still caught.
    check("registry drifted, no declared map present", snap(False, True, None),
          FAIL, 2)
    # 4 — not_checkable is a distinct outcome from pass: with the derivation
    #     unavailable, C-23 must go null even though the registry looks clean and a
    #     declared map is sitting right there offering an answer.
    saved = _CODE_TRUTH
    try:
        _CODE_TRUTH = (None, {"reason": "probe: derivation deliberately disabled"})
        check("derivation unavailable ⇒ null, never a fallback to the declared map",
              snap(True, False, {h: True, l: False}), NOT_CHECKABLE, 0)
    finally:
        _CODE_TRUTH = saved
    return bad


def rule_disclosure_probe() -> int:
    """Prove the per-rule disclosure mechanism is real, and prove it CAN fail.

    D-24 part 3, binding on every guard this campaign ships: an assertion is not earned
    until something has been shown to make it go red. F-T36-3 was exactly the absence of
    that — sixteen disclosure entries that no code read, so no observation could ever
    have distinguished a correct disclosure from a decorative one.

    Case 2 is the mechanism working; every other case is a way it must REFUSE to work,
    and they are the reason this is not a way to silence a gate.

    CASES 8–11 ARE NEW AT M0-T56 AND CLOSE FINDING F-G (D-61). Until then this probe's
    own positive case cited `D-1` — a real ADHIKĀRIN ruling about `fleet/heartbeat.sh`
    which authorises no demotion of anything — and PASSED, because the check
    authenticated the AUTHOR of a decision and never asked whether the decision
    authorised the rule. ADHIKĀRIN reproduced that through this file's own injection
    point and found it worse: the same citation carrying an INVENTED, WIDER `covers`
    list was accepted too, so the `covers` list was entirely self-asserted. Cases 8–11
    are those probes, run here as must-refuse cases, plus the subset conjunct's own
    positive control.

    Returns the number of probe failures (0 = every case behaved).
    """
    global _RULE_DISCLOSURE_DOC
    print("\n  Rule-disclosure probe (severity is computed from the disclosure, and a "
          "disclosure can only demote what its own cited decision authorises):")
    bad = 0
    decisions = decision_index(force=True)
    adhikarin = sorted(k for k, v in decisions.items() if v.get("agent") == "ADHIKARIN")
    if not adhikarin:
        print(f"      - PROBE NOT CHECKABLE: no ADHIKĀRIN decision found in "
              f"{DECISIONS_PATH}. The ledger ships in this repository, so a probe that "
              f"cannot read one means a broken checkout, not an excusable skip (§N.8).")
        return 1

    # The positive case must cite a decision that REALLY grants C-01, for identities it
    # REALLY names — no injected authority, because the thing under test is precisely
    # whether a citation is checked against the ledger. Chosen programmatically so the
    # probe follows the ledger rather than a hardcoded id that will rot.
    real_decision = probe_asset = None
    for k in adhikarin:
        granted, _why = decision_grant(decisions.get(k), "C-01")
        if not granted:
            continue
        # …and the identity has to be one that C-01 would actually flag in the probe
        # registry below, or the "fully covering" case would be vacuous.
        cand = sorted(i for i in granted
                      if i[:3] not in set(LAYER_PREFIX.values())
                      or i[:3] != LAYER_PREFIX["ganita"])
        if cand:
            real_decision, probe_asset = k, cand[0]
            break
    if real_decision is None:
        print(f"      - PROBE NOT CHECKABLE: no ADHIKĀRIN decision in "
              f"{DECISIONS_PATH.name} carries an `authorised_covers` grant for C-01 "
              f"naming an identity C-01 would flag. Since D-61 a demotion requires "
              f"exactly that, so the mechanism's positive case cannot be built and the "
              f"probe reports a failure rather than skipping (§N.8).")
        return 1

    # A real ADHIKĀRIN ruling that authorises NOTHING — the F-G attack's warrant.
    # `D-1` by preference because that is the id ADHIKĀRIN's own probe used; any
    # `authorised_covers`-less ruling reproduces it, so the probe does not depend on
    # one line surviving in the ledger.
    bare = [k for k in adhikarin
            if not isinstance(decisions[k].get("authorised_covers"), dict)]
    bare_primary = "D-1" if "D-1" in bare else (bare[0] if bare else None)
    bare_second = next((k for k in ["D-60", *reversed(bare)]
                        if k in bare and k != bare_primary), None)

    other_agent = next((k for k, v in decisions.items()
                        if v.get("agent") and v.get("agent") != "ADHIKARIN"), None)
    print(f"      authority ledger: {len(decisions)} decisions, "
          f"{len(adhikarin)} by ADHIKĀRIN, {len(bare)} of those carrying no "
          f"`authorised_covers` at all")
    print(f"      probe cites {real_decision} (grants C-01 → {probe_asset!r}); "
          f"un-authorising controls: {bare_primary}, {bare_second}")

    def snap(extra_c01: bool = False) -> dict:
        assets = [
            {"asset_id": probe_asset, "layer": "ganita", "asset_kind": "data",
             "asset_type": "data", "count_sql": None, "catalog_status": "CURRENT",
             "is_active": True, "scope": "global", "depends_on": []},
            {"asset_id": "ga_probe_two", "layer": "ganita", "asset_kind": "data",
             "asset_type": "data", "count_sql": None, "catalog_status": "CURRENT",
             "is_active": True, "scope": "global", "depends_on": []},
        ]
        if extra_c01:
            assets.append({"asset_id": "qq_probe_three", "layer": "ganita",
                           "asset_kind": "data", "asset_type": "data",
                           "count_sql": "SELECT 1", "catalog_status": "CURRENT",
                           "is_active": True, "scope": "global", "depends_on": []})
        return {"assets": assets}

    def disclosure(**over) -> dict:
        ent = {"rule": "C-01", "owner": "probe", "deferred_to": "R5",
               "disclosed_via": f"DECISIONS.jsonl {real_decision}",
               "reason": "probe fixture", "disclosed_at": "2026-08-23",
               "disclosed_by": "self-test probe",
               "gating_effect": "non_gating", "authorised_by": real_decision,
               "covers": [probe_asset]}
        ent.update(over)
        return {"deferred_rule_disclosures": {"C-01": ent}}

    def check(label: str, doc: dict | None, raw: dict, want: dict) -> None:
        nonlocal bad
        saved = _RULE_DISCLOSURE_DOC
        globals()["_RULE_DISCLOSURE_DOC"] = doc if doc is not None else {}
        try:
            results = run_rules(Snapshot(raw))
            summary = summarise(results)
        finally:
            globals()["_RULE_DISCLOSURE_DOC"] = saved
        c01r, c05r = results["C-01"], results["C-05"]
        got = {
            "c01_status": c01r["status"],
            "c01_violations": c01r["violation_count"],
            "c01_effective": c01r["effective_severity"],
            "c01_gates": "C-01" in summary["blocking_failures"],
            "c05_gates": "C-05" in summary["blocking_failures"],
        }
        ok = all(got[k] == v for k, v in want.items())
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}")
        print(f"           got {got}")
        if not ok:
            bad += 1
            print(f"           expected {want}")
            print(f"           notes: {c01r['disclosure']['notes']}")

    REFUSED = {"c01_status": FAIL, "c01_effective": BLOCKING, "c01_gates": True,
               "c05_gates": True}

    # 1 — no disclosure at all: both rules gate. The control.
    check("no disclosure ⇒ both BLOCKING rules gate", {}, snap(),
          {"c01_status": FAIL, "c01_violations": 1, "c01_effective": BLOCKING,
           "c01_gates": True, "c05_gates": True})
    # 2 — THE MECHANISM. Authorised, itemised, fully covering: C-01 still FAILS and
    #     still reports its violation; it stops gating. C-05 is untouched — a
    #     disclosure for one rule may not silence another.
    check("authorised + itemised + fully covering + inside the cited decision's own "
          "grant ⇒ C-01 reported, non-gating; C-05 STILL GATES", disclosure(), snap(),
          {"c01_status": FAIL, "c01_violations": 1,
           "c01_effective": DISCLOSED_NON_GATING,
           "c01_gates": False, "c05_gates": True})
    # 3 — NOT A WHOLESALE SILENCER. A new violation the disclosure does not itemise
    #     brings the gate straight back at the declared severity.
    check("a violation outside `covers` ⇒ the rule gates again at BLOCKING",
          disclosure(), snap(extra_c01=True),
          {"c01_status": FAIL, "c01_violations": 2, "c01_effective": BLOCKING,
           "c01_gates": True, "c05_gates": True})
    # 4 — THE AUTHORITY DETECTOR IS REAL. A decision id nobody ever recorded buys
    #     nothing, however well-written the entry.
    check("authorised_by names a decision that does not exist ⇒ no effect",
          disclosure(authorised_by="D-NO-SUCH-RULING"), snap(), REFUSED)
    # 5 — and it checks WHO. Only ADHIKĀRIN holds the charter power; an entry citing
    #     any other agent's line is inert.
    # The real ledger is currently 100% ADHIKĀRIN, so the "who authored it" conjunct
    # has no natural counter-example there. A conjunct with no counter-example is an
    # untested conjunct, so one is INJECTED rather than skipped past (§N.8).
    global _DECISION_INDEX
    saved_idx = _DECISION_INDEX
    injected = "D-PROBE-NOT-ADHIKARIN"
    globals()["_DECISION_INDEX"] = dict(
        decisions, **{injected: {"agent": "KARAKA",
                                 "authorised_covers": {"C-01": {"covers": [probe_asset]}}}})
    try:
        check(f"authorised_by names a real but non-ADHIKĀRIN line ({injected}, "
              f"agent=KARAKA) ⇒ no effect — even carrying a perfectly-formed grant",
              disclosure(authorised_by=injected), snap(), REFUSED)
    finally:
        globals()["_DECISION_INDEX"] = saved_idx
    if other_agent:
        check(f"ledger's own non-ADHIKĀRIN line ({other_agent}) ⇒ no effect",
              disclosure(authorised_by=other_agent), snap(), REFUSED)
    # 6 — an incomplete demotion is refused loudly, not applied partially.
    saved = _RULE_DISCLOSURE_DOC
    globals()["_RULE_DISCLOSURE_DOC"] = disclosure(covers=None)
    try:
        load_rule_disclosures()
        print("      [BAD ] gating_effect='non_gating' with no `covers` was ACCEPTED")
        bad += 1
    except GuardError as e:
        print(f"      [OK  ] gating_effect='non_gating' with no `covers` ⇒ GuardError "
              f"({str(e)[:60]}…)")
    finally:
        globals()["_RULE_DISCLOSURE_DOC"] = saved

    # ── 8–11 — F-G (D-61). The three ADHIKĀRIN probes, plus the subset conjunct's own
    #    positive control. Each of 8, 9 and 10 was ACCEPTED before this task.
    print("      ── F-G (D-61): the cited decision must itself authorise the rule ──")
    if bare_primary:
        # 8 — ADHIKĀRIN's reproduction: a REAL ruling of ADHIKĀRIN's, about something
        #     else entirely, carrying no `authorised_covers` at all.
        check(f"authorised_by names a real ADHIKĀRIN ruling that authorises nothing "
              f"({bare_primary}, no `authorised_covers`) ⇒ REFUSED",
              disclosure(authorised_by=bare_primary), snap(), REFUSED)
        # 9 — the extension nobody had run: the same wrong warrant, plus an invented,
        #     WIDER covers list naming identities that are not even violating.
        check(f"…the same ruling with an INVENTED, WIDER `covers` list ⇒ REFUSED "
              f"(the list is no longer self-asserted)",
              disclosure(authorised_by=bare_primary,
                         covers=[probe_asset, "bg_reference", "ga_positions"]),
              snap(), REFUSED)
    else:
        print("      [BAD ] no ADHIKĀRIN ruling WITHOUT `authorised_covers` exists in "
              "the ledger, so F-G's own warrant cannot be reproduced here")
        bad += 1
    if bare_second:
        # 10 — ADHIKĀRIN's fourth probe: a different unrelated ruling of its own.
        check(f"a second unrelated ADHIKĀRIN ruling ({bare_second}) ⇒ REFUSED",
              disclosure(authorised_by=bare_second), snap(), REFUSED)
    # 11 — the grant exists but is for ANOTHER RULE. Fail closed on the rule key too,
    #      not only on the field's absence.
    saved_idx = _DECISION_INDEX
    wrong_rule = "D-PROBE-GRANTS-ANOTHER-RULE"
    globals()["_DECISION_INDEX"] = dict(
        decisions, **{wrong_rule: {"agent": "ADHIKARIN",
                                   "authorised_covers": {
                                       "C-04": {"covers": [probe_asset]}}}})
    try:
        check(f"ADHIKĀRIN grant exists but is keyed to another rule (C-04, not C-01) "
              f"⇒ REFUSED", disclosure(authorised_by=wrong_rule), snap(), REFUSED)
    finally:
        globals()["_DECISION_INDEX"] = saved_idx
    # 12 — POSITIVE CONTROL FOR THE SUBSET RULE, so 8–11 are not passing merely because
    #      everything now refuses. A grant WIDER than the entry still demotes: the rule
    #      is `covers ⊆ grant`, not `covers == grant`.
    saved_idx = _DECISION_INDEX
    wider = "D-PROBE-GRANT-WIDER-THAN-ENTRY"
    globals()["_DECISION_INDEX"] = dict(
        decisions, **{wider: {"agent": "ADHIKARIN",
                              "authorised_covers": {
                                  "C-01": {"covers": [probe_asset,
                                                      "zz_never_claimed"]}}}})
    try:
        check("grant is WIDER than the entry's `covers` ⇒ still demotes (subset, not "
              "equality)", disclosure(authorised_by=wider), snap(),
              {"c01_status": FAIL, "c01_violations": 1,
               "c01_effective": DISCLOSED_NON_GATING,
               "c01_gates": False, "c05_gates": True})
    finally:
        globals()["_DECISION_INDEX"] = saved_idx

    # 7 — the SHIPPED file must parse and validate. If someone hand-edits it into an
    #     invalid state, the self-test says so DB-free, before CI ever reads a snapshot.
    try:
        live_disc = load_rule_disclosures(_load_json(RESIDUALS_PATH))
        eff = sorted(r for r, es in live_disc.items()
                     if any(e.get("gating_effect") == "non_gating" for e in es))
        print(f"      [OK  ] shipped {RESIDUALS_PATH.name}: "
              f"{sum(len(v) for v in live_disc.values())} rule disclosure(s) over "
              f"{len(live_disc)} rule(s) parse and validate; "
              f"claiming a gating effect: {eff or 'none'}")
    except GuardError as e:
        print(f"      [BAD ] shipped {RESIDUALS_PATH.name} does not validate: {e}")
        bad += 1
        live_disc = {}

    # 7b — AND EVERY SHIPPED DEMOTION MUST SURVIVE THE NEW SUBSET CHECK, DB-FREE.
    #      D-61 part 5 makes this the condition on the fix: prove the shipped entries
    #      still demote after it. This states that per entry, in the guard itself, so
    #      it is a detector rather than a claim in a report. It reports the refusal
    #      reason if one ever appears; it must NEVER be answered by widening a grant.
    unauthorised = []
    for rid, ents in sorted(live_disc.items()):
        for e in ents:
            if e.get("gating_effect") != "non_gating":
                continue
            auth = decisions.get(str(e.get("authorised_by")))
            granted, why = decision_grant(auth, rid)
            if granted is None:
                unauthorised.append(f"{e.get('_key', rid)} → {e.get('authorised_by')}: "
                                    f"{why}")
                continue
            outside = sorted({str(c) for c in (e.get("covers") or [])} - granted)
            if outside:
                unauthorised.append(f"{e.get('_key', rid)} → {e.get('authorised_by')}: "
                                    f"{len(outside)} identity/identities outside the "
                                    f"grant {outside[:6]}")
    demoting_entries = sum(1 for ents in live_disc.values() for e in ents
                           if e.get("gating_effect") == "non_gating")
    if unauthorised:
        print(f"      [BAD ] {len(unauthorised)} of {demoting_entries} shipped "
              f"demotion(s) are NOT authorised by the decision they cite:")
        for u in unauthorised:
            print(f"               - {u}")
        print("               This is a FINDING to report, never a reason to widen a "
              "grant or relax the subset rule (D-61 part 5).")
        bad += 1
    else:
        print(f"      [OK  ] all {demoting_entries} shipped demotion(s) are inside the "
              f"`authorised_covers` grant of the decision they cite")
    return bad


def c28_population_probe() -> int:
    """SQ-11 / D-43 part 6 — C-28's POPULATION is pinned, and the trap is shown red.

    THE TRAP, MEASURED BY PARĪKṢAKA AT V-27 AND NOT HYPOTHETICAL. Re-point C-28 so it
    enumerates FROM `build_run_assets` — "assets with a completed run whose
    `estimated_seconds` is NULL" — and it returns **0 violations**. The BLOCKING
    failure passes, and all 32 unearned `lit` states survive untouched. It is the most
    natural-looking way to "apply D-42", which is exactly what makes it dangerous:
    nothing about the diff looks like weakening a gate, and the number it produces is
    the number everybody wants.

    WHY IT IS WRONG, IN ONE SENTENCE: the defect C-28 looks for is an asset CLAIMING a
    built state with NO run behind it, and `build_run_assets` is by construction the
    table such an asset is ABSENT from. A table that cannot contain a row for the
    defect being sought is not a population — it is a place the defect goes to hide.
    C-28 must enumerate the assets making the CLAIM (registry × `asset_throughput`) and
    join outward to find the ABSENCE.

    Doing that re-pointing to clear the gate is charter H3 (D-43 part 6). This probe is
    the detector against it, not an instance of it: nothing here changes c28.

    FOUR PARTS, following the campaign's standing mutation-proof doctrine (D-41):
      1. BEHAVIOURAL, POSITIVE — the shipped rule finds the unwitnessed asset.
      2. BEHAVIOURAL, PAIRED NEGATIVES — three assets that must NOT fire, so a rule
         that simply flagged everything would not pass part 1 by accident.
      3. BEHAVIOURAL, SEEDED DEFECT — the re-pointed rule is BUILT HERE and run over
         the same snapshot; it must return 0. That is what makes part 1 capable of
         going red, and it re-measures V-27's finding rather than citing it.
      4. STRUCTURAL — over c28's own source, because a behavioural test only reaches
         the paths its author imagined. The population loop must iterate `s.assets`,
         and the rule must carry no reference to a run table at all. Applied to the
         seeded-defect function as a paired positive, so the structural assertion is
         not vacuously satisfied by any function whatsoever.

    WHAT PART 4 DOES NOT ESTABLISH, stated rather than assumed: it is a source-text
    assertion, so it catches a re-pointing written in the obvious way and would not
    catch one that reached `build_run_assets` through an indirection, a helper in
    another module, or a renamed snapshot key. Parts 1–3 are the behavioural backstop
    for that, and they bind whatever the source looks like.

    Returns the number of probe failures (0 = every part behaved).
    """
    print("\n  C-28 population probe (SQ-11: the rule enumerates the assets CLAIMING a "
          "built state and joins OUTWARD to find absence):")
    bad = 0

    def asset(aid: str, kind: str, est) -> dict:
        return {"asset_id": aid, "layer": "brahmagyan", "asset_kind": kind,
                "asset_type": "data" if kind != "service" else "service",
                "catalog_status": "CURRENT", "is_active": True, "scope": "global",
                "estimated_seconds": est, "depends_on": []}

    # THE DEFECT: `lit`, no estimate, and no run record of any kind — V-27's Class A,
    # which is all 32 of them. The paired negatives cover the three ways an asset can
    # look similar and not be this defect.
    raw = {
        "assets": [
            asset("bg_probe_unwitnessed", "data", None),        # ← the one violation
            asset("bg_probe_witnessed", "data", 12.5),          # ran, and has an estimate
            asset("bg_probe_unlit", "data", None),              # never claimed a built state
            asset("bg_probe_service", "service", None),         # not a DATA kind (V-22)
        ],
        "throughput": [
            {"asset_id": "bg_probe_unwitnessed", "states": ["lit"]},
            {"asset_id": "bg_probe_witnessed", "states": ["lit"]},
            {"asset_id": "bg_probe_unlit", "states": ["planned"]},
            {"asset_id": "bg_probe_service", "states": ["lit"]},
        ],
        # The run table, populated exactly as production's is: it holds rows for the
        # assets that DID run, and therefore structurally cannot hold one for the
        # asset whose missing run is the defect.
        "build_run_assets": [
            {"asset_id": "bg_probe_witnessed", "state": "complete"},
            {"asset_id": "bg_probe_service", "state": "complete"},
        ],
    }
    snap = Snapshot(raw)

    def c28_repointed_at_build_run_assets(s: Snapshot) -> Result:
        """THE SEEDED DEFECT — the trap, written the way it would really be written.

        Enumerates the population FROM `build_run_assets` (assets with a completed
        run) instead of from the registry. Every line of it looks reasonable. It is
        never called by the guard; it exists so the assertion above can be shown to
        fail.
        """
        runs = s.raw.get("build_run_assets") or []
        ran = {r["asset_id"] for r in runs if r.get("state") == "complete"}
        v = []
        for aid in sorted(ran):
            a = s.by_id.get(aid)
            if not a or a.get("asset_kind") not in DATA_KINDS:
                continue
            if a.get("estimated_seconds") is None:
                v.append({"asset_id": aid})
        return verdict(v)

    # ── 1 + 2 — behavioural, both directions ────────────────────────────────────
    shipped = c28(snap).as_dict()
    got_ids = sorted(violation_identity(x) for x in shipped["violations"])
    want_ids = ["bg_probe_unwitnessed"]
    ok = shipped["status"] == FAIL and got_ids == want_ids
    print(f"      [{'OK  ' if ok else 'BAD '}] shipped C-28 over a registry claiming "
          f"4 assets built / 2 witnessed by a run: status={shipped['status']} "
          f"violations={got_ids}")
    if not ok:
        bad += 1
        print(f"           expected status={FAIL} violations={want_ids} — the "
              f"unwitnessed asset is the whole point of the rule, and the three "
              f"paired negatives (has an estimate / never lit / service kind) must "
              f"not fire")

    # ── 3 — the seeded defect must go red ───────────────────────────────────────
    trapped = c28_repointed_at_build_run_assets(snap).as_dict()
    ok = trapped["status"] == PASS and trapped["violation_count"] == 0
    print(f"      [{'OK  ' if ok else 'BAD '}] the SAME snapshot through a C-28 "
          f"re-pointed at build_run_assets: status={trapped['status']} "
          f"violations={trapped['violation_count']} — V-27's measurement reproduced; "
          f"the defect vanishes and the gate would pass")
    if not ok:
        bad += 1
        print(f"           expected status={PASS} violations=0. If this stops "
              f"holding, the fixture no longer DISCRIMINATES between the correct "
              f"population and the trap, and the assertion above is no longer earned "
              f"— rebuild the fixture, do not delete this case.")

    # ── 4 — structural, with a paired positive ──────────────────────────────────
    def structural(fn, label: str) -> list[str]:
        src = inspect.getsource(fn)
        body = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        problems = []
        if "for a in s.assets" not in body:
            problems.append(f"{label}: does not iterate `s.assets` — its population is "
                            f"not the set of assets making the claim")
        if "build_run" in body:
            problems.append(f"{label}: references `build_run*` — C-28 must not read "
                            f"the run table at all; absence is found by the assets it "
                            f"does NOT contain")
        return problems

    shipped_problems = structural(c28, "c28")
    trap_problems = structural(c28_repointed_at_build_run_assets, "the re-pointed rule")
    if shipped_problems:
        bad += 1
        print("      [BAD ] structural: c28's population has been re-pointed")
        for p in shipped_problems:
            print(f"               - {p}")
    else:
        print("      [OK  ] structural: c28 iterates `s.assets` and contains no "
              "reference to a run table")
    if trap_problems:
        print(f"      [OK  ] structural, paired positive: the same assertion applied "
              f"to the seeded defect reports {len(trap_problems)} problem(s) — so a "
              f"clean result above is a measurement, not a vacuous one")
    else:
        bad += 1
        print("      [BAD ] structural, paired positive: the assertion found NOTHING "
              "wrong with a function that is the defect by construction — the "
              "structural check is inert and proves nothing about c28")
    return bad


def snapshot_staleness_probe() -> int:
    """Prove the freshness detector is real, and prove it CAN fail (F-T36-2)."""
    print("\n  Snapshot-freshness probe (the age of the data a gate judges is itself "
          "measured, and an unmeasurable age is not a young age):")
    bad = 0
    declared, files = migration_declared_registry_columns()
    if not declared:
        print("      - PROBE NOT CHECKABLE: no `ALTER TABLE asset_registry ADD COLUMN` "
              "found under platform/migrations/. The migrations ship in this "
              "repository, so finding none means a broken checkout (§N.8).")
        return 1
    col = sorted(declared)[0]
    now = _dt.datetime.now(_dt.timezone.utc)
    fresh = (now - _dt.timedelta(minutes=5)).isoformat()
    old = (now - _dt.timedelta(hours=100)).isoformat()
    allcols = sorted(declared) + ["asset_id"]
    print(f"      migrations declare {sorted(declared)} on asset_registry "
          f"({', '.join(files)})")

    def check(label, raw, mode, want) -> None:
        nonlocal bad
        st = snapshot_staleness(raw, mode, DEFAULT_MAX_SNAPSHOT_AGE_HOURS, now=now)
        got = {k: st[k] for k in want}
        ok = got == want
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}: {got}")
        if not ok:
            bad += 1
            print(f"           expected {want}; reasons={st['reasons']}")

    check("fresh snapshot, schema current ⇒ not stale",
          {"_meta": {"read_at": fresh}, "registry_columns": allcols}, "snapshot",
          {"stale": False, "age_exceeded": False, "schema_behind_columns": []})
    check("100h old ⇒ stale on age",
          {"_meta": {"read_at": old}, "registry_columns": allcols}, "snapshot",
          {"stale": True, "age_exceeded": True})
    check(f"fresh but missing migration-declared column `{col}` ⇒ stale on schema",
          {"_meta": {"read_at": fresh},
           "registry_columns": [c for c in allcols if c != col]}, "snapshot",
          {"stale": True, "age_exceeded": False, "schema_behind_columns": [col]})
    check("no `_meta.read_at` at all ⇒ stale (an unmeasurable age is not a young age)",
          {"registry_columns": allcols}, "snapshot", {"stale": True})
    check("unparseable `_meta.read_at` ⇒ stale",
          {"_meta": {"read_at": "yesterday-ish"}, "registry_columns": allcols},
          "snapshot", {"stale": True})
    check("live mode is measured but never enforced on age",
          {"_meta": {"read_at": old}, "registry_columns": allcols}, "live",
          {"stale": True, "enforced": False})

    # The shipped baseline, reported rather than asserted: this is the fossil F-T36-2
    # named, and the self-test states its condition out loud on every CI run.
    raw = _load_json(BASELINE_SNAPSHOT)
    if raw is None:
        print(f"      [BAD ] shipped baseline {BASELINE_SNAPSHOT.name} unreadable")
        return bad + 1
    st = snapshot_staleness(raw, "snapshot", DEFAULT_MAX_SNAPSHOT_AGE_HOURS, now=now)
    print(f"      shipped baseline {BASELINE_SNAPSHOT.name}: stale={st['stale']} "
          f"age_hours={st['age_hours']} schema_behind={st['schema_behind_columns']}")
    for r in st["reasons"]:
        print(f"          · {r}")
    return bad


def x06_ratchet_probe() -> int:
    """D-94 / D-84 — X-06 blocks on GROWTH (a SET, never a count) and never on the
    committed floor's own residual, and preserves the DIFFERENTIAL that is the only
    reason bg_panchanga's gap was ever found (D-94 part 8).

    FOUR PARTS, mirroring c28_population_probe's discipline:
      1. BEHAVIOURAL, POSITIVE — an unwitnessed SERVICE-kind asset (bg_panchanga's
         shape exactly: c28() cannot see it, X-06 must) is reported as growth when it
         is absent from the floor.
      2. BEHAVIOURAL, PAIRED NEGATIVE — the SAME asset, present in the floor, must NOT
         be reported: the rule blocks on growth, never on the carried residual (I13).
      3. SET-NOT-COUNT (D-84) — a population that shrinks by one member and grows a
         DIFFERENT one is the SAME SIZE as the floor. A count-only comparison would
         pass; the shipped rule must still catch it by name.
      4. THE DIFFERENTIAL, PRESERVED AS A TEST (D-94 part 8) — c28() (DATA_KINDS-
         scoped, by `estimated_seconds`) and X-06 (all-kind, by `build_run_assets`)
         are DIFFERENT questions that happen to agree on today's live population
         (independently confirmed: all 32 measured 2026-08-23 have estimated_seconds
         NULL). This part builds a fixture where they are DESIGNED to agree exactly
         as they do live, and structurally proves X-06 carries no asset_kind
         predicate — the one property that let bg_panchanga escape c28() and must
         never be reintroduced here.

    Returns the number of probe failures (0 = every part behaved).
    """
    print("\n  X-06 ratchet probe (D-94: growth-only, set-not-count, and the "
          "differential that found bg_panchanga survives consolidation):")
    bad = 0

    def asset(aid: str, kind: str, est=None) -> dict:
        return {"asset_id": aid, "layer": "brahmagyan", "asset_kind": kind,
                "asset_type": "data" if kind != "service" else "service",
                "catalog_status": "CURRENT", "is_active": True, "scope": "global",
                "estimated_seconds": est, "depends_on": []}

    # bg_panchanga's exact shape: SERVICE kind, lit, never a completed run.
    raw = {
        "assets": [
            asset("bg_probe_service_unwitnessed", "service", None),
            asset("bg_probe_data_unwitnessed", "data", None),
            asset("bg_probe_witnessed", "data", 12.5),
        ],
        "throughput": [
            {"asset_id": "bg_probe_service_unwitnessed", "states": ["lit"]},
            {"asset_id": "bg_probe_data_unwitnessed", "states": ["lit"]},
            {"asset_id": "bg_probe_witnessed", "states": ["lit"]},
        ],
        "build_run_assets": [
            {"asset_id": "bg_probe_witnessed", "state": "complete"},
        ],
    }
    snap = Snapshot(raw)

    # D-77: NO live mutation window on the real committed floor. Every write this
    # probe makes lands in an isolated temp directory; the module-global path is
    # repointed there for the probe's duration and restored in `finally`, exactly
    # like T62/T69's sandboxing precedent — the real file at UNEARNED_LIT_FLOOR_PATH
    # is never opened for writing by this function.
    global UNEARNED_LIT_FLOOR_PATH
    real_path = UNEARNED_LIT_FLOOR_PATH
    tmpdir = tempfile.TemporaryDirectory(prefix="x06_ratchet_probe_")
    UNEARNED_LIT_FLOOR_PATH = pathlib.Path(tmpdir.name) / "unearned_lit_floor.json"

    def with_floor(floor_ids: list[str]) -> None:
        UNEARNED_LIT_FLOOR_PATH.write_text(json.dumps({
            "floor": [{"asset_id": a} for a in floor_ids]}), encoding="utf-8")

    try:
        # ── 1 — empty floor: BOTH unwitnessed assets are growth, service INCLUDED ──
        with_floor([])
        r1 = x06(snap).as_dict()
        got1 = sorted(violation_identity(x) for x in r1["violations"])
        want1 = ["bg_probe_data_unwitnessed", "bg_probe_service_unwitnessed"]
        ok = r1["status"] == FAIL and got1 == want1
        print(f"      [{'OK  ' if ok else 'BAD '}] empty floor: status={r1['status']} "
              f"growth={got1}")
        if not ok:
            bad += 1
            print(f"           expected status={FAIL} growth={want1} — X-06 must see "
                  f"the SERVICE-kind unwitnessed asset that c28() structurally cannot "
                  f"(F-Y / bg_panchanga)")

        # ── 2 — both in the floor: neither is growth; I13's residual is carried, ──
        # ── never blocked on ──────────────────────────────────────────────────────
        with_floor(["bg_probe_service_unwitnessed", "bg_probe_data_unwitnessed"])
        r2 = x06(snap).as_dict()
        ok = r2["status"] == PASS and r2["violation_count"] == 0
        print(f"      [{'OK  ' if ok else 'BAD '}] both members of the committed "
              f"floor: status={r2['status']} violations={r2['violation_count']}")
        if not ok:
            bad += 1
            print(f"           expected status={PASS} violations=0 — I13 forbids "
                  f"repairing asset build state while R0 is shut; a residual must "
                  f"never be blocking")

        # ── 3 — set-not-count (D-84): floor has ONE member, live population has a ──
        # ── DIFFERENT single member — same SIZE, must still be caught by NAME ─────
        with_floor(["bg_probe_witnessed"])   # wrong member entirely, same count (1)
        # re-point the floor to a single member that is NOT in the live population,
        # while the live population also has exactly one growth-eligible member
        # (data_unwitnessed) once the service one is excluded for this sub-check
        raw_one = dict(raw)
        raw_one["assets"] = [asset("bg_probe_data_unwitnessed", "data", None),
                             asset("bg_probe_witnessed", "data", 12.5)]
        raw_one["throughput"] = [
            {"asset_id": "bg_probe_data_unwitnessed", "states": ["lit"]},
            {"asset_id": "bg_probe_witnessed", "states": ["lit"]},
        ]
        snap_one = Snapshot(raw_one)
        r3 = x06(snap_one).as_dict()
        got3 = sorted(violation_identity(x) for x in r3["violations"])
        ok = r3["status"] == FAIL and got3 == ["bg_probe_data_unwitnessed"]
        print(f"      [{'OK  ' if ok else 'BAD '}] floor size 1, live growth-eligible "
              f"size 1, DIFFERENT member: status={r3['status']} growth={got3}")
        if not ok:
            bad += 1
            print("           a count-only comparison (len(current)==len(floor)) "
                  "would have passed this case silently — D-84 requires the SET be "
                  "reconciled, never the count")
    finally:
        UNEARNED_LIT_FLOOR_PATH = real_path
        tmpdir.cleanup()
        assert UNEARNED_LIT_FLOOR_PATH == real_path, (
            "probe must restore the real committed-floor path exactly (D-77)")

    # ── 4 — the differential, preserved as a structural test (D-94 part 8) ──────
    # c28() and X-06 ask different questions; they are DESIGNED to agree on this
    # fixture the way they are independently confirmed to agree on today's live
    # population, so the fixture re-derives the OLD unfiltered scorecard behaviour
    # (lit AND estimated_seconds IS NULL, ALL kinds — no build_run_assets involved)
    # and checks it against BOTH new pieces together.
    def independent_all_kinds_null_estimate_and_lit(s: Snapshot) -> set[str]:
        """Re-implementation of the OLD, unfiltered m0_exit_scorecard.py C-28 SQL —
        `estimated_seconds IS NULL AND EXISTS (throughput.state='lit')`, no kind
        filter — written independently of c28()/x06() so it anchors both."""
        out = set()
        for row in s.raw.get("throughput") or []:
            aid = row["asset_id"]
            a = s.by_id.get(aid)
            if a is None or a.get("estimated_seconds") is not None:
                continue
            if "lit" in (row.get("states") or []):
                out.add(aid)
        return out

    fixture4 = {
        "assets": [asset("bg_probe_service_unwitnessed", "service", None),
                   asset("bg_probe_data_unwitnessed", "data", None),
                   asset("bg_probe_witnessed", "data", 12.5)],
        "throughput": raw["throughput"],
        "build_run_assets": raw["build_run_assets"],
    }
    snap4 = Snapshot(fixture4)
    independent = independent_all_kinds_null_estimate_and_lit(snap4)
    c28_ids = {violation_identity(x) for x in c28(snap4).as_dict()["violations"]}
    non_data_kind_members = {aid for aid in independent
                             if snap4.by_id[aid].get("asset_kind") not in DATA_KINDS}
    reconstructed = c28_ids | non_data_kind_members
    ok = independent == reconstructed and independent == {
        "bg_probe_service_unwitnessed", "bg_probe_data_unwitnessed"}
    print(f"      [{'OK  ' if ok else 'BAD '}] differential preserved: old-unfiltered "
          f"independent set {sorted(independent)} == narrowed-C-28 "
          f"{sorted(c28_ids)} ∪ non-DATA_KINDS-members {sorted(non_data_kind_members)}")
    if not ok:
        bad += 1
        print("           the narrowing of C-28 to DATA_KINDS must NEVER be shipped "
              "without something else covering exactly the members it drops (D-94 "
              "part 5) — this is that invariant, re-measured, not just cited")

    # ── 4b — PARIKṢAKA F-V75-1: the check above proves (X∩D) ∪ (X∩¬D) == X, which ──
    # is TRUE BY SET ALGEBRA FOR EVERY POSSIBLE INPUT (measured by PARIKṢAKA across 64
    # fixture combinations — the conjunct failed in zero) and, worse, it never calls
    # x06() at all — it cannot detect the exact coverage-loss it claims to guard
    # against even in principle. ADD a DIRECT measurement against x06()'s own
    # population (do NOT replace the check above — it is not wrong, only
    # insufficient, per F-V75-1's own framing): call x06() on the SAME fixture and
    # assert every member c28() drops for being outside DATA_KINDS actually appears
    # in x06()'s own `current_population_ids` detail field — the real sibling rule's
    # real output, not an algebraic restatement of the input.
    r6 = x06(snap4).as_dict()
    x06_population = set(r6["detail"].get("current_population_ids") or [])
    covered = non_data_kind_members.issubset(x06_population)
    ok = r6["status"] != NOT_CHECKABLE and covered
    print(f"      [{'OK  ' if ok else 'BAD '}] x06() itself covers what c28() drops "
          f"(direct measurement, not algebra): non-DATA_KINDS members "
          f"{sorted(non_data_kind_members)} ⊆ x06(snap4) current_population_ids "
          f"{sorted(x06_population)} (x06 status={r6['status']})")
    if not ok:
        bad += 1
        print("           F-V75-1: the set-algebra check above can never fail for any "
              "input and never calls x06() — this calls x06() on the SAME fixture and "
              "reads its OWN detail field, turning 'something else covers exactly the "
              "members c28 drops' from a tautology into a measurement against the "
              "actual sibling rule")

    # Structural anchor (D-89 shape, one-sided by construction — X-06's whole point is
    # having NO asset_kind predicate; a future edit adding one recreates the exact gap
    # F-Y found and must fail this line): x06's EXECUTABLE body must not reference
    # DATA_KINDS. Parsed via AST over the body only (the docstring above names
    # DATA_KINDS in prose to explain the contrast with c28() — a substring scan over
    # raw source text would false-positive on that prose, which is not a predicate).
    fn_ast = ast.parse(inspect.getsource(x06)).body[0]
    body_stmts = fn_ast.body
    if body_stmts and isinstance(body_stmts[0], ast.Expr) and \
            isinstance(getattr(body_stmts[0], "value", None), ast.Constant) and \
            isinstance(body_stmts[0].value.value, str):
        body_stmts = body_stmts[1:]          # drop the docstring statement
    names_referenced = {n.id for node in body_stmts for n in ast.walk(node)
                        if isinstance(n, ast.Name)}
    ok = "DATA_KINDS" not in names_referenced
    print(f"      [{'OK  ' if ok else 'BAD '}] x06() executable body carries no "
          f"DATA_KINDS reference")
    if not ok:
        bad += 1
        print("           X-06 exists specifically because bg_panchanga (a SERVICE) "
              "escaped a DATA_KINDS-scoped rule by recategorization — a DATA_KINDS "
              "reference here would reintroduce that exact gap")

    return bad


def x07_manifest_completeness_probe() -> int:
    """D-111 — prove X-07 catches BOTH directions of a manifest/orphan-population
    mismatch, and prove it would have caught the REAL historical gap PARIKṢAKA found
    (V-70 / F-V70-2): a manifest that does not exist at all, with the four real
    orphans already sitting in `build_run_assets`. Mirrors `x06_ratchet_probe`'s
    discipline. D-77: no live mutation window on the real committed manifest — every
    write this probe makes lands in an isolated temp directory; the module-global
    `LINEAGE_MANIFEST_PATH` is repointed there for the probe's duration and restored
    in `finally`. The real `asset_id_lineage_manifest.json` and the real database are
    never opened for writing by this function, and its 4 real committed entries are
    never touched.

    ALSO covers D-116 / F-V74-1's per-entry shape/evidence check: the four
    pre-registered failing cases D-116 part 5 names (migration cited does not exist;
    real migration that never references the id; empty evidence array; disposition
    outside the declared vocabulary), a positive control proving the check does not
    just fail everything, and a missing-required-field case.

    Returns the number of probe failures (0 = every case behaved).
    """
    print("\n  X-07 lineage-manifest-completeness probe (D-111: set equality, both "
          "directions, and the real pre-D-103 gap reproduced):")
    bad = 0

    def registry_asset(aid: str) -> dict:
        return {"asset_id": aid, "layer": "ganita", "asset_kind": "data",
                "asset_type": "data", "catalog_status": "CURRENT", "is_active": True,
                "scope": "global", "depends_on": []}

    global LINEAGE_MANIFEST_PATH
    real_path = LINEAGE_MANIFEST_PATH
    tmpdir = tempfile.TemporaryDirectory(prefix="x07_manifest_probe_")
    LINEAGE_MANIFEST_PATH = pathlib.Path(tmpdir.name) / "asset_id_lineage_manifest.json"

    # NOTE (D-116 / F-V74-1): entries written by this helper must carry valid shape
    # — a disposition_vocabulary, a disposition that is a member of it, and a
    # non-empty evidence array — or the NEW per-entry shape check added to x07()
    # below would fail cases 2/4/5 on shape alone and mask the SET-completeness
    # behaviour this part of the probe exists to isolate. `legacy_never_registered`
    # is used as the neutral synthetic disposition: it needs no migration citation,
    # so it does not couple this SET-completeness fixture to any real migration file.
    def write_manifest(ids: list[str]) -> None:
        LINEAGE_MANIFEST_PATH.write_text(json.dumps({
            "disposition_vocabulary": {
                "legacy_never_registered": "synthetic fixture disposition"},
            "entries": [{"asset_id": a, "disposition": "legacy_never_registered",
                        "evidence": ["synthetic fixture evidence"]} for a in ids],
        }), encoding="utf-8")

    def check(label: str, raw: dict, want_status: str,
              want_undoc: list[str], want_stale: list[str]) -> None:
        nonlocal bad
        r = x07(Snapshot(raw)).as_dict()
        got_undoc = sorted(v["asset_id"] for v in r["violations"]
                           if v["class"] == "orphan_missing_from_manifest")
        got_stale = sorted(v["asset_id"] for v in r["violations"]
                           if v["class"] == "manifest_entry_not_a_live_orphan")
        ok = (r["status"] == want_status and got_undoc == sorted(want_undoc)
              and got_stale == sorted(want_stale))
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}: status={r['status']} "
              f"undocumented={got_undoc} stale={got_stale}")
        if not ok:
            bad += 1
            print(f"           expected status={want_status} "
                  f"undocumented={sorted(want_undoc)} stale={sorted(want_stale)}")
            if r["reason"]:
                print(f"           reason: {r['reason']}")

    try:
        # ── 1 — THE REAL HISTORICAL MOMENT. No manifest file at all (the state ────
        # before M0-T75/D-103 ever ran) and the four REAL orphan ids, exactly as
        # PARIKṢAKA found them by hand. This is the case the task's hard constraint
        # names explicitly: the assertion must report UNDETERMINED-AND-FATAL here,
        # not a silent pass.
        real_orphans = ["ga_pyjhora_engine", "ka_gochara_v2_materialize",
                        "chart_dashas", "ga_chart_service"]
        raw1 = {
            "assets": [registry_asset("ga_dashas"), registry_asset("ka_gochara")],
            "build_run_asset_ids_all": real_orphans + ["ga_dashas", "ka_gochara"],
        }
        assert not LINEAGE_MANIFEST_PATH.exists(), "probe must start with no manifest"
        check("no manifest file at all (pre-D-103 state) + the 4 real orphans "
              "PARIKṢAKA found by hand ⇒ UNDETERMINED-AND-FATAL, all 4 named",
              raw1, FAIL, real_orphans, [])

        # ── 2 — manifest present and complete for the 4 real orphans: matches. ────
        # (the synthetic mirror of today's real, live-DB state — see the report for
        # the actual --live confirmation, which this DB-free self-test cannot run.)
        write_manifest(real_orphans)
        check("manifest present, complete, and matches the live orphan population "
              "exactly ⇒ clean", raw1, PASS, [], [])

        # ── 3 — DIRECTION 1: a live orphan with NO manifest entry (a rename/ ──────
        # retirement/operator-error happened and nobody logged it yet).
        raw3 = dict(raw1)
        raw3["build_run_asset_ids_all"] = real_orphans + [
            "ga_dashas", "ka_gochara", "ph_new_undocumented_rename"]
        check("a 5th orphan appears with NO manifest entry ⇒ FAIL, naming only the "
              "new id (direction 1)", raw3, FAIL, ["ph_new_undocumented_rename"], [])

        # ── 4 — DIRECTION 2: a manifest entry for an id that is NO LONGER a live ──
        # orphan — the manifest was not updated when something changed (an entry
        # deleted from the manifest while the orphan itself remains is the named
        # D-111 shape; this fixture is its mirror image, an entry ADDED for an id
        # that is not/no-longer live — both are the same SET mismatch direction).
        write_manifest(real_orphans + ["mi_stale_manifest_only"])
        check("manifest carries an entry for an id that is not a live orphan ⇒ FAIL, "
              "naming only the stale entry (direction 2)", raw1, FAIL, [],
              ["mi_stale_manifest_only"])

        # ── 5 — restore the correct manifest; confirm clean, no state bled forward ─
        write_manifest(real_orphans)
        check("re-confirm clean after restoring the correct manifest", raw1, PASS, [],
              [])
    finally:
        LINEAGE_MANIFEST_PATH = real_path
        tmpdir.cleanup()
        assert LINEAGE_MANIFEST_PATH == real_path, (
            "probe must restore the real manifest path exactly (D-77)")

    # ── 5b..5g — D-116 / F-V74-1 PER-ENTRY SHAPE checks. D-105 pre-registration: ──
    # these are the FOUR failing cases D-116 part 5 names explicitly, stated before
    # the fix's own behaviour is trusted, plus a positive control (the real
    # migration-citing shape must actually PASS, not just fail everything) and one
    # missing-required-field case. Each fixture's `build_run_asset_ids_all` is set
    # to exactly the fixture's own entry ids, so the SET-completeness half of x07
    # (already proven in 1-5 above) contributes zero violations here — every
    # violation reported below is a SHAPE violation, isolated on purpose.
    tmpdir3 = tempfile.TemporaryDirectory(prefix="x07_manifest_probe_shape_")
    LINEAGE_MANIFEST_PATH = pathlib.Path(tmpdir3.name) / "asset_id_lineage_manifest.json"
    SHAPE_VOCAB = {
        "renamed": "synthetic — old id UPDATEd to a new id by a cited migration",
        "deleted": "synthetic — id DELETEd by a cited migration, no successor",
        "legacy_never_registered": "synthetic — never a valid asset_registry id",
    }

    def write_shape_manifest(entries: list[dict]) -> None:
        LINEAGE_MANIFEST_PATH.write_text(json.dumps(
            {"disposition_vocabulary": SHAPE_VOCAB, "entries": entries}),
            encoding="utf-8")

    def check_shape(label: str, entries: list[dict], want_status: str,
                    want_classes: list[str]) -> None:
        nonlocal bad
        write_shape_manifest(entries)
        raw_shape = {"assets": [],
                     "build_run_asset_ids_all": [e["asset_id"] for e in entries]}
        r = x07(Snapshot(raw_shape)).as_dict()
        got_classes = sorted(v["class"] for v in r["violations"])
        ok = r["status"] == want_status and got_classes == sorted(want_classes)
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}: status={r['status']} "
              f"classes={got_classes}")
        if not ok:
            bad += 1
            print(f"           expected status={want_status} "
                  f"classes={sorted(want_classes)}")
            if r["reason"]:
                print(f"           reason: {r['reason']}")

    try:
        # ── 5b — D-116 pre-registered case 1: migration cited does not exist ──────
        check_shape(
            "renamed entry cites a migration file that does not exist ⇒ FAIL "
            "(D-116 pre-registered case 1)",
            [{"asset_id": "ph_probe_bad_migration_path", "disposition": "renamed",
              "renamed_to": "ph_probe_new",
              "renamed_by_migration": "platform/migrations/999999_does_not_exist.sql",
              "evidence": ["synthetic"]}],
            FAIL, ["manifest_entry_unverifiable_migration_citation"])

        # ── 5c — D-116 pre-registered case 2: a REAL migration that never ─────────
        # mentions the id.
        check_shape(
            "deleted entry cites a REAL migration that never references the id ⇒ "
            "FAIL (D-116 pre-registered case 2)",
            [{"asset_id": "ph_probe_not_in_migration", "disposition": "deleted",
              "deleted_by_migration":
                  "platform/migrations/342_retire_ga_pyjhora_engine.sql",
              "evidence": ["synthetic"]}],
            FAIL, ["manifest_entry_unverifiable_migration_citation"])

        # ── 5d — D-116 pre-registered case 3: empty evidence array ⇒ INCOMPLETE, ──
        # never a partial pass (migration_number_guard E4 precedent).
        check_shape(
            "legacy_never_registered entry with an EMPTY evidence array ⇒ FAIL "
            "(D-116 pre-registered case 3)",
            [{"asset_id": "ph_probe_empty_evidence",
              "disposition": "legacy_never_registered", "evidence": []}],
            FAIL, ["manifest_entry_evidence_empty"])

        # ── 5e — D-116 pre-registered case 4: disposition outside the declared ────
        # vocabulary.
        check_shape(
            "entry with a disposition that is not a key of the manifest's own "
            "disposition_vocabulary ⇒ FAIL (D-116 pre-registered case 4)",
            [{"asset_id": "ph_probe_bad_disposition", "disposition": "guessed",
              "evidence": ["synthetic"]}],
            FAIL, ["manifest_entry_disposition_not_in_vocabulary"])

        # ── 5f — POSITIVE CONTROL, not part of D-116's four but required to prove ──
        # the check does not just fail everything: the REAL committed manifest's own
        # migration-citing shape (disposition=renamed, citing migration 563, which
        # DOES reference ka_gochara_v2_materialize — confirmed by grep, 13 hits)
        # reproduced verbatim must PASS clean.
        check_shape(
            "renamed entry citing the REAL migration 563, which DOES reference the "
            "id ⇒ clean (positive control — the check does not fail everything)",
            [{"asset_id": "ka_gochara_v2_materialize", "disposition": "renamed",
              "renamed_to": "ka_gochara",
              "renamed_by_migration":
                  "platform/migrations/563_utkarsha_w64_asset_rename.sql",
              "evidence": ["synthetic"]}],
            PASS, [])

        # ── 5g — required-field-missing (the KEY absent, not merely an empty ──────
        # value) is its own class, distinct from an empty evidence array.
        check_shape(
            "entry missing the evidence field entirely ⇒ FAIL, "
            "manifest_entry_missing_required_field",
            [{"asset_id": "ph_probe_no_evidence_field",
              "disposition": "legacy_never_registered"}],
            FAIL, ["manifest_entry_missing_required_field"])
    finally:
        LINEAGE_MANIFEST_PATH = real_path
        tmpdir3.cleanup()
        assert LINEAGE_MANIFEST_PATH == real_path, (
            "probe must restore the real manifest path exactly (D-77)")

    # ── 6 — NOT_CHECKABLE is a distinct outcome from PASS: no input, no verdict ───
    r_missing = x07(Snapshot({"assets": []})).as_dict()
    ok = r_missing["status"] == NOT_CHECKABLE
    print(f"      [{'OK  ' if ok else 'BAD '}] no build_run_asset_ids_all key in the "
          f"snapshot at all ⇒ NOT_CHECKABLE, never a silent pass: "
          f"status={r_missing['status']}")
    if not ok:
        bad += 1
        print(f"           expected status={NOT_CHECKABLE}")

    # ── 7 — a manifest file that exists but is not parseable JSON ⇒ NOT_CHECKABLE, ─
    # distinct from "absent" (case 1), which is instead treated as an empty record
    # and must FAIL. Corruption is a genuine data hole; omission is not.
    tmpdir2 = tempfile.TemporaryDirectory(prefix="x07_manifest_probe_corrupt_")
    LINEAGE_MANIFEST_PATH = pathlib.Path(tmpdir2.name) / "asset_id_lineage_manifest.json"
    try:
        LINEAGE_MANIFEST_PATH.write_text("{not valid json", encoding="utf-8")
        r_corrupt = x07(Snapshot(raw1)).as_dict()
        ok = r_corrupt["status"] == NOT_CHECKABLE
        print(f"      [{'OK  ' if ok else 'BAD '}] manifest file exists but is not "
              f"parseable JSON ⇒ NOT_CHECKABLE (never conflated with 'absent'): "
              f"status={r_corrupt['status']}")
        if not ok:
            bad += 1
            print(f"           expected status={NOT_CHECKABLE}")
    finally:
        LINEAGE_MANIFEST_PATH = real_path
        tmpdir2.cleanup()
        assert LINEAGE_MANIFEST_PATH == real_path, (
            "probe must restore the real manifest path exactly (D-77)")

    return bad


def regenerate_unearned_lit_floor() -> int:
    """MAINTENANCE ONLY. Never run automatically; never part of a CI read path.

    Measures the LIVE cross-kind unearned-lit population (asset_throughput.state=
    'lit' AND zero completed build_run_assets records, ALL asset_kind) and writes it
    as X-06's new committed floor — ITEMISED, GENERATED FROM THIS MEASUREMENT, NEVER
    HAND-TYPED (D-67 part 4).

    REFUSES to write if the measured population is not a SUBSET of the existing
    committed floor (when one already exists): the floor may only SHRINK (D-95's
    correction to D-87's pawl, applied here from the outset). If growth is ever
    genuinely authorised, D-96 governs: a new, explicitly-ruled baseline recorded as a
    dated decision, never a silent regeneration through this command.

    A first-ever run (no committed floor on disk) is a BOOTSTRAP, not growth, and is
    always permitted — there is nothing yet to have grown past.
    """
    raw = read_live()
    snap = Snapshot(raw)
    if snap.throughput is None or raw.get("build_run_assets") is None:
        print("GUARD ERROR — live snapshot missing asset_throughput or "
              "build_run_assets; refusing to regenerate the floor from partial data.",
              file=sys.stderr)
        return 3

    ran = {r["asset_id"] for r in raw["build_run_assets"] if r.get("state") == "complete"}
    current = []
    for a in snap.assets:
        aid = a["asset_id"]
        t = snap.throughput.get(aid)
        lit = bool(t and any(st == "lit" for st in (t.get("states") or [])))
        if lit and aid not in ran:
            current.append(a)
    current_ids = {a["asset_id"] for a in current}

    bootstrap = not UNEARNED_LIT_FLOOR_PATH.exists()
    old = {} if bootstrap else (_load_json(UNEARNED_LIT_FLOOR_PATH) or {})
    old_ids = {e["asset_id"] for e in (old.get("floor") or [])}
    old_r0_intake = {e["asset_id"] for e in (old.get("floor") or []) if e.get("r0_intake")}

    if not bootstrap:
        growth = sorted(current_ids - old_ids)
        if growth:
            print("GUARD ERROR — the measured population is NOT a subset of the "
                  f"committed floor; the floor may only shrink (D-95). New, "
                  f"uncommitted asset_id(s): {growth}. If this growth is real and "
                  f"authorised, it needs an explicit, dated ruling widening the floor "
                  f"(D-96 — never a silent regeneration); refusing to write.",
                  file=sys.stderr)
            return 3

    new_floor = []
    for a in sorted(current, key=lambda x: x["asset_id"]):
        aid = a["asset_id"]
        entry = {"asset_id": aid, "asset_kind": a.get("asset_kind"),
                 "estimated_seconds": a.get("estimated_seconds")}
        if aid in old_r0_intake or aid == "bg_panchanga":
            entry["r0_intake"] = True
            entry["r0_intake_note"] = (
                "D-94 parts 6-7: asset build state, R0 shut, I13 binds. Not "
                "repaired by this rule layer; carried openly until R0 opens.")
        new_floor.append(entry)

    doc = {
        "schema_version": "1.0",
        "$comment": (
            "Committed floor for X-06 (check_asset_catalogue_contract.py). ITEMISED, "
            "GENERATED FROM A LIVE MEASUREMENT, NEVER HAND-TYPED (D-67 part 4). The "
            "gate asserts the CURRENT live population is a SUBSET of this floor "
            "(growth is BLOCKING, D-84: the SET is compared, never the count); this "
            "file may only SHRINK, enforced at regeneration time by "
            "regenerate_unearned_lit_floor() — a measured population that is not a "
            "subset of the existing committed floor makes that function refuse to "
            "write, never silently widen (D-95 pattern, D-96: no exemption fields, "
            "ever). Regenerate with `python "
            "platform/scripts/governance/check_asset_catalogue_contract.py "
            "--regenerate-unearned-lit-floor` ONLY after a real repair has paid one "
            "of these down."),
        "rule_id": "X-06",
        "generated_by": "check_asset_catalogue_contract.py --regenerate-unearned-lit-floor",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "authority": "D-94 (ADHIKĀRIN, F-Y); floor-not-HEAD^ pattern D-95",
        "floor_count": len(new_floor),
        "floor": new_floor,
    }
    UNEARNED_LIT_FLOOR_PATH.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {UNEARNED_LIT_FLOOR_PATH.relative_to(REPO_ROOT)}: "
          f"{len(new_floor)} item(s) (was {len(old_ids)}); "
          f"paid down since last commit: {sorted(old_ids - current_ids) or 'none'}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--self-test", action="store_true",
                     help="Run bundled fixtures + the contract cross-check (DB-free).")
    src.add_argument("--snapshot", metavar="PATH",
                     help="Run the rules over a committed registry snapshot JSON.")
    src.add_argument("--live", action="store_true",
                     help="Run the rules over production, READ-ONLY (needs psycopg).")
    src.add_argument("--regenerate-unearned-lit-floor", action="store_true",
                     help="MAINTENANCE ONLY: measure the live X-06 population and "
                          "rewrite its committed floor (never widens it; see "
                          "regenerate_unearned_lit_floor()).")
    ap.add_argument("--baseline", action="store_true",
                    help=f"Shorthand for --snapshot {BASELINE_SNAPSHOT.name}.")
    ap.add_argument("--snapshot-out", metavar="PATH",
                    help="With --live: write the snapshot to PATH (no credential in it).")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    ap.add_argument("--max-rows", type=int, default=8,
                    help="Violation rows printed per rule in text mode (default 8).")
    ap.add_argument("--max-age-hours", type=float,
                    default=DEFAULT_MAX_SNAPSHOT_AGE_HOURS,
                    help=f"Maximum age of a --snapshot/--baseline input before the "
                         f"guard refuses to report it as a verdict (default "
                         f"{DEFAULT_MAX_SNAPSHOT_AGE_HOURS}h). Tightening it is always "
                         f"allowed; loosening it does not silence the schema-behind "
                         f"detector, which is a proof rather than a threshold.")
    args = ap.parse_args(argv)

    try:
        if args.self_test:
            return self_test(args.max_rows)

        if args.regenerate_unearned_lit_floor:
            return regenerate_unearned_lit_floor()

        if args.live:
            raw = read_live()
            if args.snapshot_out:
                pathlib.Path(args.snapshot_out).write_text(
                    json.dumps(raw, indent=1, ensure_ascii=False, default=str),
                    encoding="utf-8")
            header = "LIVE asset_registry (READ-ONLY)"
        else:
            p = pathlib.Path(args.snapshot) if args.snapshot else BASELINE_SNAPSHOT
            if not args.snapshot and not args.baseline:
                ap.error("one of --self-test / --snapshot / --live / --baseline / "
                        "--regenerate-unearned-lit-floor required")
            if not p.exists():
                print(f"snapshot not found: {p}", file=sys.stderr)
                return 2
            raw = json.loads(p.read_text(encoding="utf-8"))
            raw.pop("_expect", None)
            header = f"snapshot {p.name}"

        contract_rows = parse_contract(CONTRACT_PATH)
        problems = cross_check(contract_rows)
        if problems:
            print("GUARD ERROR — guard and contract document disagree:", file=sys.stderr)
            for pr in problems:
                print("  -", pr, file=sys.stderr)
            return 3

        mode = "live" if args.live else "snapshot"
        staleness = snapshot_staleness(raw, mode, args.max_age_hours)

        results = run_rules(Snapshot(raw))
        summary = summarise(results)
        if args.json:
            print(json.dumps({"_meta": raw.get("_meta"), "header": header,
                              "staleness": staleness,
                              "summary": summary, "rules": results},
                             indent=1, ensure_ascii=False, default=str))
        else:
            emit_text(results, summary,
                      f"Asset Catalogue Contract conformance — {header}", args.max_rows,
                      staleness=staleness)

        # THE FOSSIL GATE (F-T36-2). A stale snapshot's rule results are printed in
        # full above — suppressing them would hide data, which is the opposite defect —
        # but the guard refuses to EXIT as though they were a verdict about the
        # catalogue. Exit 3 is the existing "the guard cannot be trusted to have
        # measured what it claims" code, which is exactly this situation. `--live`
        # measures production by definition and is never failed on age.
        if staleness["stale"] and staleness["enforced"]:
            print("", file=sys.stderr)
            print("GUARD ERROR — SNAPSHOT STALE: the rules above were run over data "
                  "that is provably not the current catalogue.", file=sys.stderr)
            for r in staleness["reasons"]:
                print(f"  - {r}", file=sys.stderr)
            print("  A gate that reads a stale snapshot is not a gate: it reports "
                  "failures that may already be repaired and would report success for "
                  "a defect introduced since. Regenerate the snapshot from an "
                  "environment that HAS database access — `--live --snapshot-out "
                  f"{BASELINE_SNAPSHOT.name}` — and commit it; CI has no credential "
                  "and cannot do this for itself.", file=sys.stderr)
            return 3

        return 1 if (summary["blocking_failures"] or summary["rung_failures"]) else 0
    except GuardError as e:
        print(f"GUARD ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
