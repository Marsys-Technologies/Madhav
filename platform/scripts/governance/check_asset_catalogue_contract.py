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
import datetime as _dt
import json
import pathlib
import re
import sys
from typing import Any, Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / "00_ARCHITECTURE" / "control" / "ASSET_CATALOGUE_CONTRACT_v1_0.md"
CONTROL = REPO_ROOT / "00_ARCHITECTURE" / "control"
HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE / "asset_catalogue_fixtures"
RESIDUALS_PATH = HERE / "asset_catalogue_disclosed_residuals.json"
COWRITERS_PATH = HERE / "asset_catalogue_declared_cowriters.json"
BASELINE_SNAPSHOT = HERE / "asset_catalogue_baseline_20260823.json"

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
    out: dict[str, dict] = {}
    for r in ALL_RULES:
        try:
            res = r.fn(snap)
        except GuardError:
            raise
        except Exception as e:                       # noqa: BLE001
            res = Result(NOT_CHECKABLE, [], f"rule raised {type(e).__name__}: {e}")
        d = res.as_dict()
        d.update({"severity": r.severity, "statement": r.statement, "origin": r.origin})
        out[r.id] = d
    return out


def summarise(results: dict) -> dict:
    s = {"pass": 0, "fail": 0, "not_checkable": 0,
         "blocking_failures": [], "rung_failures": [],
         "residual_failures": [], "advisory_failures": [],
         "not_checkable_rules": []}
    for rid, r in results.items():
        s[r["status"]] += 1
        if r["status"] == FAIL:
            key = {BLOCKING: "blocking_failures", RUNG: "rung_failures",
                   RESIDUAL: "residual_failures", ADVISORY: "advisory_failures"}[r["severity"]]
            s[key].append(rid)
        elif r["status"] == NOT_CHECKABLE:
            s["not_checkable_rules"].append(rid)
    return s


def emit_text(results: dict, summary: dict, header: str, max_rows: int) -> None:
    print(header)
    print("=" * len(header))
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
    print()
    print(f"  pass={summary['pass']}  fail={summary['fail']}  "
          f"not_checkable={summary['not_checkable']}")
    print(f"  BLOCKING failures : {summary['blocking_failures'] or 'none'}")
    print(f"  RUNG failures     : {summary['rung_failures'] or 'none'}")
    print(f"  RESIDUAL failures : {summary['residual_failures'] or 'none'} "
          f"(non-gating by construction — see X-02)")
    print(f"  ADVISORY failures : {summary['advisory_failures'] or 'none'}")
    print(f"  not_checkable     : {summary['not_checkable_rules'] or 'none'}")
    print("  NOTE: not_checkable is NOT a pass. A rule whose input column or data "
          "does not exist has produced no verdict (CLAUDE.md §N.8).")


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
    ap.add_argument("--baseline", action="store_true",
                    help=f"Shorthand for --snapshot {BASELINE_SNAPSHOT.name}.")
    ap.add_argument("--snapshot-out", metavar="PATH",
                    help="With --live: write the snapshot to PATH (no credential in it).")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    ap.add_argument("--max-rows", type=int, default=8,
                    help="Violation rows printed per rule in text mode (default 8).")
    args = ap.parse_args(argv)

    try:
        if args.self_test:
            return self_test(args.max_rows)

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
                ap.error("one of --self-test / --snapshot / --live / --baseline required")
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

        results = run_rules(Snapshot(raw))
        summary = summarise(results)
        if args.json:
            print(json.dumps({"_meta": raw.get("_meta"), "header": header,
                              "summary": summary, "rules": results},
                             indent=1, ensure_ascii=False, default=str))
        else:
            emit_text(results, summary,
                      f"Asset Catalogue Contract conformance — {header}", args.max_rows)
        return 1 if (summary["blocking_failures"] or summary["rung_failures"]) else 0
    except GuardError as e:
        print(f"GUARD ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
