"""
L5 reference-resolution ledger -- TESTS-FIRST for the design in
00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_REFERENCE_RESOLUTION_LEDGER_DESIGN_v1_0.md

Context (SS ruling N-99).  `mimamsa_predictions` rows are a frozen calibration
record; 135 of the 139 rows on the canonical chart cite phala_anchors that no
longer exist.  Those rows are NEVER deleted or rewritten.  The gap is recorded in a
COMPUTED side ledger (`mimamsa_reference_resolution`), written by an L5-side asset,
and read by a reported-not-blocking detector.

This file holds, and is the ONLY place that holds (no production module exists yet):

  1. REFERENCE_PURE_FUNCTION -- `resolve_references` and its helpers.  It is the
     executable specification of the design doc's section 5 resolution rules.  When the
     implementation PR lands it moves to `brahmagyan/mimamsa/reference_resolution.py`
     and the strict-xfail parity hold at the bottom of this file flips (XPASS strict ->
     failure) and must be converted into a real parity test in the same PR.
  2. Table-driven scenarios (resolved / superseded / vanished, the 135/4 production
     shape, chart isolation, precedence, ambiguity, case-folding).
  3. Contract properties: idempotence, order independence, no mutation of inputs, no
     aliasing of outputs, one row per prediction, DDL-CHECK-equivalent row invariants.
  4. MUTATION PROOFS: the same contract suite is run against source-level mutants of the
     reference function and of the static SQL checker; every mutant must be killed.
  5. A STATIC SQL CHECK over every ```sql block in the design doc: the design may never
     emit DELETE / UPDATE / INSERT / TRUNCATE / ALTER / DROP / GRANT / FK / trigger
     against `mimamsa_predictions`, and the ledger DDL carries no reference to it or to
     `phala_anchors` at all (a computed side table must never reference-block, cascade
     into, or modify the frozen record).
  6. Strict-xfail HOLDS for the pieces that do not exist yet (production module, writer
     registration, migration file -- matched by file CONTENT so the real filename flips it).
  7. REAL-POSTGRES layer (section 7): the doc's SQL is executed on a throwaway cluster that
     reproduces the production power structure (schema public owned by a schema-owner role,
     `amjis_app` with USAGE only).  It proves the DDL needs the protected window, drives the
     CHECK matrix exhaustively against the Python twin, kills mutated DDL, runs the writer /
     detector / reader / registry SQL, and asserts the reader's stale predicate equals D1's.
     Skips (with a reason) when no PostgreSQL binaries are found; L5_LEDGER_REQUIRE_PG=1 turns
     that skip into a failure.

No production module is imported.  Sections 1-6 are pure functions; section 7 starts its own
loopback-only throwaway Postgres and touches nothing else.
"""
from __future__ import annotations

import collections
import copy
import glob
import hashlib
import inspect
import json
import os
import random
import re
import shutil
import socket
import subprocess
import tempfile
import textwrap
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import pytest

# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC = (
    _REPO_ROOT
    / "00_ARCHITECTURE/briefs/suvarna/layers/L5"
    / "L5_REFERENCE_RESOLUTION_LEDGER_DESIGN_v1_0.md"
)
LEAK_GUARD_TS = _REPO_ROOT / "platform/src/lib/pariprashna/no_leakage/calibration_leak_guard.ts"
MIGRATIONS_DIR = _REPO_ROOT / "platform/migrations"
SUPABASE_MIGRATIONS_DIR = _REPO_ROOT / "platform/supabase/migrations"

LEDGER_TABLE = "mimamsa_reference_resolution"
FROZEN_TABLE = "mimamsa_predictions"

# ===========================================================================
# 1. REFERENCE_PURE_FUNCTION  (test-file only; mirrors design doc section 5)
# ===========================================================================

STATUS_RESOLVED = "resolved"
STATUS_SUPERSEDED = "superseded"
STATUS_VANISHED = "vanished"
STATUSES = (STATUS_RESOLVED, STATUS_SUPERSEDED, STATUS_VANISHED)

BASIS_ID_REFERENCED = "id_match_referenced"
BASIS_ID_FREEZE = "id_match_freeze"
BASIS_CLAIM_UNIQUE = "claim_key_unique"
BASIS_CLAIM_AMBIGUOUS = "claim_key_ambiguous"
BASIS_NO_MATCH = "no_match"

# status -> permitted bases.  The DDL CHECK in the design doc encodes exactly this.
STATUS_BASES: dict[str, frozenset[str]] = {
    STATUS_RESOLVED: frozenset({BASIS_ID_REFERENCED, BASIS_ID_FREEZE}),
    STATUS_SUPERSEDED: frozenset({BASIS_CLAIM_UNIQUE}),
    STATUS_VANISHED: frozenset({BASIS_CLAIM_AMBIGUOUS, BASIS_NO_MATCH}),
}

FREEZE_SRC_CITATION = "citation_ref"
FREEZE_SRC_SUFFIX = "prediction_id_suffix"
FREEZE_SRC_REFERENCED = "source_pramana_id"
FREEZE_SOURCES = (FREEZE_SRC_CITATION, FREEZE_SRC_SUFFIX, FREEZE_SRC_REFERENCED)

RESOLVER_VERSION = "mi_nirdesa_ref_v1.0"
PREDICTION_ID_PREFIX = "pred_"  # mi_bhavisya.py: prediction_id = f"pred_{anchor_id}"

# The ONLY inputs the resolver may take.  No outcome, no brier, no lifecycle, no
# calibration: resolution is a function of (prediction reference + anchor table) alone.
RESOLVER_PREDICTION_FIELDS = frozenset(
    {
        "chart_id",
        "prediction_id",
        "source_pramana_id",
        "citation_anchor_id",
        "domain",
        "window_start",
        "window_end",
        "falsifier_jsonb",
        "frozen_bundle_hash",
    }
)
RESOLVER_ANCHOR_FIELDS = frozenset(
    {"chart_id", "anchor_id", "domain", "window_start", "window_end", "falsifier"}
)


def _norm_id(value: Any) -> str:
    return "" if value is None else str(value).strip().lower()


def canonical_falsifier(value: Any) -> Any:
    """Mirror mi_bhavisya.py's falsifier projection (anchor text -> falsifier_jsonb).

    NULL / empty -> {} ; text -> json.loads(text) if it parses else {"raw": text}.
    """
    if value is None or value == "":
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return {"raw": value}
    return value


def _fals_key(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def prediction_claim_key(p: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(p["domain"]),
        str(p["window_start"]),
        str(p["window_end"]),
        _fals_key(p["falsifier_jsonb"]),
    )


def anchor_claim_key(a: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(a["domain"]),
        str(a["window_start"]),
        str(a["window_end"]),
        _fals_key(canonical_falsifier(a.get("falsifier"))),
    )


def freeze_anchor_id(
    prediction_id: Any, citation_anchor_id: Any, source_pramana_id: Any
) -> tuple[str, str]:
    """The anchor id the prediction was FROZEN against, and where that came from.

    Preference order (design doc 5.1): the manifestation-set citation (untouched by migration
    680 but NOT durable: mi_bhavisya deletes every manifestation set on rebuild) -> the
    `pred_<anchor_id>` suffix of prediction_id (durable: it is the primary key) -> the live
    reference column as a last resort (then the two ids are the same by construction and
    `reference_rewritten_since_freeze` is necessarily false).
    """
    cit = _norm_id(citation_anchor_id)
    if cit:
        return cit, FREEZE_SRC_CITATION
    pid = str(prediction_id or "")
    if pid.startswith(PREDICTION_ID_PREFIX) and len(pid) > len(PREDICTION_ID_PREFIX):
        return pid[len(PREDICTION_ID_PREFIX):].strip().lower(), FREEZE_SRC_SUFFIX
    return _norm_id(source_pramana_id), FREEZE_SRC_REFERENCED


def _pred_sort_key(p: Mapping[str, Any]) -> tuple[str, str]:
    return (str(p["chart_id"]), str(p["prediction_id"]))


def resolve_references(
    predictions: Iterable[Mapping[str, Any]],
    anchors: Iterable[Mapping[str, Any]],
    *,
    resolver_version: str = RESOLVER_VERSION,
) -> list[dict[str, Any]]:
    """Resolve every prediction's anchor reference against the CURRENT anchor table.

    Pure: no I/O, no clock, no randomness, inputs never mutated, output never aliases
    input.  Anchors only ever match predictions of the SAME chart.
    """
    preds = list(predictions)
    anch = list(anchors)

    seen_keys: set[tuple[str, str]] = set()
    for p in preds:
        k = _pred_sort_key(p)
        if k in seen_keys:
            raise ValueError(f"duplicate prediction key {k!r}")
        seen_keys.add(k)

    by_chart_ids: dict[str, dict[str, str]] = {}
    by_chart_claim: dict[str, dict[tuple[str, str, str, str], set[str]]] = {}
    for a in anch:
        chart = str(a["chart_id"])
        aid = _norm_id(a["anchor_id"])
        by_chart_ids.setdefault(chart, {})[aid] = aid
        by_chart_claim.setdefault(chart, {}).setdefault(anchor_claim_key(a), set()).add(aid)

    out: list[dict[str, Any]] = []
    ordered = sorted(preds, key=_pred_sort_key)
    for p in ordered:
        chart = str(p["chart_id"])
        ids = by_chart_ids.get(chart, {})
        ref = _norm_id(p.get("source_pramana_id"))
        frz, frz_src = freeze_anchor_id(
            p.get("prediction_id"), p.get("citation_anchor_id"), p.get("source_pramana_id")
        )
        key = prediction_claim_key(p)
        cand = sorted(by_chart_claim.get(chart, {}).get(key, set()))

        resolved_anchor_id: str | None
        if ref and ref in ids:
            status, basis, resolved_anchor_id = STATUS_RESOLVED, BASIS_ID_REFERENCED, ids[ref]
        elif frz and frz in ids:
            status, basis, resolved_anchor_id = STATUS_RESOLVED, BASIS_ID_FREEZE, ids[frz]
        elif len(cand) == 1:
            status, basis, resolved_anchor_id = STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, cand[0]
        elif len(cand) > 1:
            status, basis, resolved_anchor_id = STATUS_VANISHED, BASIS_CLAIM_AMBIGUOUS, None
        else:
            status, basis, resolved_anchor_id = STATUS_VANISHED, BASIS_NO_MATCH, None

        row = {
            "chart_id": chart,
            "prediction_id": str(p["prediction_id"]),
            "anchor_id_at_freeze": frz,
            "freeze_id_source": frz_src,
            "anchor_id_referenced": ref,
            "reference_rewritten_since_freeze": ref != frz,
            "resolution_status": status,
            "resolution_basis": basis,
            "resolved_anchor_id": resolved_anchor_id,
            "candidate_count": len(cand),
            "current_anchor_count": len(ids),
            "claim_key": {
                "domain": key[0],
                "window_start": key[1],
                "window_end": key[2],
                "falsifier_sha256": hashlib.sha256(key[3].encode("utf-8")).hexdigest(),
            },
            "prediction_frozen_bundle_hash": str(p.get("frozen_bundle_hash") or ""),
            "resolver_version": resolver_version,
        }
        out.append(row)
    return out


def summarize(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Counts per status (all three keys always present, zeros included) + total."""
    counts = {s: 0 for s in STATUSES}
    total = 0
    for r in rows:
        counts[r["resolution_status"]] += 1
        total += 1
    counts["total"] = total
    return counts


DDL_CONSTRAINTS = ("status_chk", "freeze_src_chk", "counts_chk", "matrix_chk")


def ddl_check_violations(row: Mapping[str, Any]) -> list[str]:
    """Python twin of EXACTLY the four DDL CHECK constraints (design doc section 3).

    Returns the suffixes of the violated constraints (mimamsa_reference_resolution_<name>).
    Cross-validated against a real Postgres in section 7: the database must accept a row
    iff this returns [].
    """
    st, bs = row["resolution_status"], row["resolution_basis"]
    rid, n, cur = row["resolved_anchor_id"], row["candidate_count"], row["current_anchor_count"]
    v: list[str] = []
    if st not in STATUSES:
        v.append("status_chk")
    if row["freeze_id_source"] not in FREEZE_SOURCES:
        v.append("freeze_src_chk")
    if not (n >= 0 and cur >= 0):
        v.append("counts_chk")
    matrix = (
        (st == STATUS_RESOLVED and bs in STATUS_BASES[STATUS_RESOLVED] and rid is not None)
        or (st == STATUS_SUPERSEDED and bs == BASIS_CLAIM_UNIQUE and rid is not None and n == 1)
        or (st == STATUS_VANISHED and bs == BASIS_NO_MATCH and rid is None and n == 0)
        or (st == STATUS_VANISHED and bs == BASIS_CLAIM_AMBIGUOUS and rid is None and n >= 2)
    )
    if not matrix:
        v.append("matrix_chk")
    return v


def row_invariant_violations(row: Mapping[str, Any]) -> list[str]:
    """DDL CHECKs (via `ddl_check_violations`) plus two Python-only semantic invariants."""
    v: list[str] = list(ddl_check_violations(row))
    if v:
        return v
    if not row["anchor_id_at_freeze"] and row["freeze_id_source"] != FREEZE_SRC_REFERENCED:
        v.append("empty freeze id with non-fallback source")
    if row["resolution_status"] == STATUS_VANISHED and row["current_anchor_count"] == 0 \
            and row["candidate_count"] != 0:
        v.append("candidates cannot exist when the chart has no current anchors")
    return v


# ===========================================================================
# Scenario builders
# ===========================================================================

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _u(n: int) -> str:
    """Deterministic fake UUID text."""
    return str(uuid.UUID(int=n))


def pred(
    n: int,
    *,
    chart: str = CANON,
    referenced: str | None = None,
    freeze: str | None = None,
    citation: str | None = None,
    domain: str = "career",
    ws: date = date(2026, 8, 12),
    we: date = date(2026, 11, 10),
    falsifier: str = "REFUTED if no career event by 2026-11-10",
) -> dict[str, Any]:
    """A prediction row as the writer would read it.

    `freeze` is the anchor id the prediction was frozen against (prediction_id suffix);
    `referenced` is what source_pramana_id holds NOW (== freeze unless migration 680
    rewrote it).
    """
    frz = freeze if freeze is not None else _u(1000 + n)
    ref = referenced if referenced is not None else frz
    return {
        "chart_id": chart,
        "prediction_id": f"pred_{frz}",
        "source_pramana_id": ref,
        "citation_anchor_id": citation if citation is not None else frz,
        "domain": domain,
        "window_start": ws,
        "window_end": we,
        "falsifier_jsonb": canonical_falsifier(falsifier),
        "frozen_bundle_hash": hashlib.sha256(f"{chart}|{frz}".encode()).hexdigest()[:32],
    }


def anch(
    anchor_id: str,
    *,
    chart: str = CANON,
    domain: str = "career",
    ws: date = date(2026, 8, 12),
    we: date = date(2026, 11, 10),
    falsifier: str | None = "REFUTED if no career event by 2026-11-10",
) -> dict[str, Any]:
    return {
        "chart_id": chart,
        "anchor_id": anchor_id,
        "domain": domain,
        "window_start": ws,
        "window_end": we,
        "falsifier": falsifier,
    }


def production_shape(
    n_resolved: int = 4, n_vanished_remapped: int = 131, n_vanished_unremapped: int = 4
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The 135/4 shape measured on the canonical chart (design doc section 2).

    * 4 predictions whose (680-rewritten) reference still resolves,
    * 131 whose reference was rewritten by migration 680 to a deterministic id that no
      longer exists,
    * 4 never rewritten (680 collision pairs) whose random id no longer exists.
    Current anchors: only the 4 resolved ones.  Vanished windows differ from every
    current anchor's window, so no claim key can match (superseded = 0).
    """
    preds: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []
    k = 0
    for i in range(n_resolved):
        k += 1
        new_id = _u(5000 + i)
        preds.append(pred(k, freeze=_u(2000 + i), referenced=new_id,
                          domain=("career", "health", "relationship", "character")[i % 4]))
        anchors.append(anch(new_id, domain=("career", "health", "relationship", "character")[i % 4]))
    for i in range(n_vanished_remapped):
        k += 1
        preds.append(pred(k, freeze=_u(3000 + i), referenced=_u(6000 + i),
                          domain="transition", ws=date(2027, 1, 1), we=date(2030, 1, 1),
                          falsifier=f"gone-{i}"))
    for i in range(n_vanished_unremapped):
        k += 1
        preds.append(pred(k, freeze=_u(4000 + i), domain="character",
                          ws=date(2027, 10, 20), we=date(2030, 4, 3), falsifier=f"gone-u-{i}"))
    return preds, anchors


# ---------------------------------------------------------------------------
# Table-driven scenarios.  expected: {prediction_id: (status, basis, resolved_anchor_id|None)}
# ---------------------------------------------------------------------------

A1, A2, A3 = _u(1), _u(2), _u(3)


def _scenarios() -> list[tuple[str, list, list, dict[str, tuple[str, str, str | None]]]]:
    sc: list[tuple[str, list, list, dict]] = []

    p = pred(1, freeze=_u(10), referenced=A1)
    sc.append(("resolved_by_referenced_id", [p], [anch(A1)],
               {p["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, A1)}))

    p = pred(2, freeze=A2, referenced=_u(11))
    sc.append(("resolved_by_freeze_id_when_reference_rewritten_away", [p], [anch(A2)],
               {p["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_FREEZE, A2)}))

    p = pred(3, freeze=_u(12), referenced=_u(13))
    sc.append(("superseded_unique_claim_key", [p], [anch(A3)],
               {p["prediction_id"]: (STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, A3)}))

    p = pred(4, freeze=_u(14), referenced=_u(15))
    sc.append(("vanished_ambiguous_two_candidates", [p], [anch(A1), anch(A2)],
               {p["prediction_id"]: (STATUS_VANISHED, BASIS_CLAIM_AMBIGUOUS, None)}))

    p = pred(5, freeze=_u(16), referenced=_u(17))
    sc.append(("vanished_no_anchors_at_all", [p], [],
               {p["prediction_id"]: (STATUS_VANISHED, BASIS_NO_MATCH, None)}))

    for label, kw in (
        ("domain", {"domain": "wealth"}),
        ("window_start", {"ws": date(2026, 8, 13)}),
        ("window_end", {"we": date(2026, 11, 11)}),
        ("falsifier", {"falsifier": "REFUTED if no career event by 2099-01-01"}),
    ):
        p = pred(6, freeze=_u(18), referenced=_u(19))
        sc.append((f"vanished_claim_key_differs_in_{label}", [p], [anch(A1, **kw)],
                   {p["prediction_id"]: (STATUS_VANISHED, BASIS_NO_MATCH, None)}))

    p = pred(7, freeze=_u(20), referenced=A1)
    sc.append(("chart_isolation_same_anchor_id_other_chart_does_not_resolve", [p],
               [anch(A1, chart=OTHER)],
               {p["prediction_id"]: (STATUS_VANISHED, BASIS_NO_MATCH, None)}))

    p = pred(8, freeze=_u(21), referenced=_u(22))
    sc.append(("chart_isolation_same_claim_key_other_chart_is_not_superseded", [p],
               [anch(A1, chart=OTHER)],
               {p["prediction_id"]: (STATUS_VANISHED, BASIS_NO_MATCH, None)}))

    # id match beats claim-key match (both available)
    p = pred(9, freeze=_u(23), referenced=A1)
    sc.append(("precedence_id_match_beats_claim_key", [p], [anch(A1), anch(A2)],
               {p["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, A1)}))

    # referenced beats freeze when both resolve
    p = pred(10, freeze=A2, referenced=A1)
    sc.append(("precedence_referenced_beats_freeze", [p], [anch(A1), anch(A2)],
               {p["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, A1)}))

    hexid = "abcdef12-3456-7890-abcd-ef1234567890"  # letters, so .upper() is not a no-op
    p = pred(11, freeze=_u(24), referenced=hexid.upper())
    sc.append(("uuid_case_folding", [p], [anch(hexid)],
               {p["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, hexid)}))

    # falsifier stored as parsed JSON on both sides still matches
    jf = '{"deny": "x", "n": 1}'
    p = pred(12, freeze=_u(25), referenced=_u(26), falsifier=jf)
    sc.append(("superseded_json_falsifier_canonicalised", [p],
               [anch(A3, falsifier='{"n": 1,  "deny": "x"}')],
               {p["prediction_id"]: (STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, A3)}))

    # NULL anchor falsifier == {} falsifier
    p = pred(13, freeze=_u(27), referenced=_u(28), falsifier="")
    sc.append(("superseded_null_falsifier_matches_empty", [p], [anch(A3, falsifier=None)],
               {p["prediction_id"]: (STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, A3)}))

    # two predictions, one anchor: many-to-one supersession is recorded, not forbidden
    pa, pb = pred(14, freeze=_u(29), referenced=_u(30)), pred(15, freeze=_u(31), referenced=_u(32))
    sc.append(("many_predictions_one_superseding_anchor", [pa, pb], [anch(A3)],
               {pa["prediction_id"]: (STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, A3),
                pb["prediction_id"]: (STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, A3)}))

    # mixed batch across two charts
    pc = pred(16, chart=CANON, freeze=_u(33), referenced=A1)
    po = pred(17, chart=OTHER, freeze=_u(34), referenced=A2)
    pv = pred(18, chart=OTHER, freeze=_u(35), referenced=_u(36), domain="wealth")
    sc.append(("mixed_two_charts", [pc, po, pv], [anch(A1), anch(A2, chart=OTHER)],
               {pc["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, A1),
                po["prediction_id"]: (STATUS_RESOLVED, BASIS_ID_REFERENCED, A2),
                pv["prediction_id"]: (STATUS_VANISHED, BASIS_NO_MATCH, None)}))

    sc.append(("empty_inputs", [], [], {}))
    return sc


SCENARIOS = _scenarios()
SCENARIO_IDS = [s[0] for s in SCENARIOS]

ResolverFn = Callable[..., list]


def _check_scenario(fn: ResolverFn, name: str, preds: list, anchors: list, expected: dict) -> None:
    rows = fn(copy.deepcopy(preds), copy.deepcopy(anchors))
    got = {r["prediction_id"]: (r["resolution_status"], r["resolution_basis"],
                                r["resolved_anchor_id"]) for r in rows}
    assert len(rows) == len(preds), f"{name}: one ledger row per prediction (got {len(rows)})"
    assert got == expected, f"{name}: {got} != {expected}"
    for r in rows:
        bad = row_invariant_violations(r)
        assert not bad, f"{name}: invariant violations {bad}"


def _check_production_shape(fn: ResolverFn) -> None:
    preds, anchors = production_shape()
    assert len(preds) == 139 and len(anchors) == 4
    rows = fn(copy.deepcopy(preds), copy.deepcopy(anchors))
    s = summarize(rows)
    assert s == {STATUS_RESOLVED: 4, STATUS_SUPERSEDED: 0, STATUS_VANISHED: 135, "total": 139}, s
    assert {r["resolution_basis"] for r in rows if r["resolution_status"] == STATUS_VANISHED} == {
        BASIS_NO_MATCH
    }
    assert all(r["current_anchor_count"] == 4 for r in rows)
    assert all(r["candidate_count"] == 0 for r in rows if r["resolution_status"] == STATUS_VANISHED)
    # 680 rewrote the reference column on 135 of 139 rows (131 vanished + 4 resolved)
    assert sum(1 for r in rows if r["reference_rewritten_since_freeze"]) == 135
    for r in rows:
        assert not row_invariant_violations(r)


def _check_idempotent_and_order_independent(fn: ResolverFn) -> None:
    preds, anchors = production_shape(4, 12, 4)
    a = fn(copy.deepcopy(preds), copy.deepcopy(anchors))
    b = fn(copy.deepcopy(preds), copy.deepcopy(anchors))
    assert a == b, "same inputs, same output (no clock / randomness)"
    rng = random.Random(20261003)
    p2, a2 = copy.deepcopy(preds), copy.deepcopy(anchors)
    rng.shuffle(p2)
    rng.shuffle(a2)
    assert fn(p2, a2) == a, "input order must not change the output"
    # feeding the resolver its own output's facts again changes nothing (fixed point)
    assert fn(copy.deepcopy(preds), copy.deepcopy(anchors)) == a


def _container_ids(obj: Any) -> set[int]:
    """id() of every dict / list / set reachable from obj (aliasing detector)."""
    seen: set[int] = set()
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, (dict, list, set, tuple)):
            if isinstance(cur, (dict, list, set)):
                seen.add(id(cur))
            children = cur.values() if isinstance(cur, dict) else cur
            stack.extend(children)
    return seen


def _check_no_mutation_no_aliasing(fn: ResolverFn) -> None:
    preds, anchors = production_shape(3, 6, 2)
    preds.reverse()  # deliberately unsorted: an in-place sort would be visible
    p0, a0 = copy.deepcopy(preds), copy.deepcopy(anchors)
    rows = fn(preds, anchors)
    assert preds == p0, "predictions input was mutated (content or order)"
    assert anchors == a0, "anchors input was mutated"
    in_ids = _container_ids(preds) | _container_ids(anchors)
    assert not (in_ids & _container_ids(rows)), "output shares a mutable container with the input"
    rows[0]["claim_key"]["domain"] = "TAMPERED"
    rows[0]["resolution_status"] = "TAMPERED"
    assert preds == p0 and anchors == a0, "output aliases input"
    # iterables (generators) are accepted and consumed once
    gen_rows = fn((p for p in copy.deepcopy(p0)), (a for a in copy.deepcopy(a0)))
    assert len(gen_rows) == len(p0)


def _check_rewritten_flag(fn: ResolverFn) -> None:
    """reference_rewritten_since_freeze == (live reference differs from the freeze id).

    Includes the BLANK reference: a blanked reference column is a rewrite too (review LOW-5).
    """
    f = _u(77)
    same = pred(1, freeze=f, referenced=f)
    diff = pred(2, freeze=_u(78), referenced=_u(79))
    blank = pred(3, freeze=_u(80), referenced="")
    g = _u(82)
    blank_resolvable = pred(4, freeze=g, referenced="")
    fallback = {**pred(5, freeze=_u(81)), "prediction_id": "weird", "citation_anchor_id": None}
    rows = {r["prediction_id"]: r for r in fn(
        copy.deepcopy([same, diff, blank, blank_resolvable, fallback]),
        copy.deepcopy([anch(f), anch(g)]),
    )}
    assert rows[same["prediction_id"]]["reference_rewritten_since_freeze"] is False
    assert rows[diff["prediction_id"]]["reference_rewritten_since_freeze"] is True
    assert rows[blank["prediction_id"]]["reference_rewritten_since_freeze"] is True
    assert rows[blank["prediction_id"]]["resolution_status"] == STATUS_VANISHED
    br = rows[blank_resolvable["prediction_id"]]
    assert br["reference_rewritten_since_freeze"] is True
    assert (br["resolution_status"], br["resolution_basis"]) == (STATUS_RESOLVED, BASIS_ID_FREEZE)
    fb = rows["weird"]
    assert fb["freeze_id_source"] == FREEZE_SRC_REFERENCED
    assert fb["reference_rewritten_since_freeze"] is False


def _check_duplicate_rejected(fn: ResolverFn) -> None:
    p = pred(1)
    with pytest.raises(ValueError):
        fn([p, copy.deepcopy(p)], [])


def _check_randomised_invariants(fn: ResolverFn) -> None:
    """Seeded fuzz: every output row satisfies the DDL-twin invariants and coverage."""
    rng = random.Random(1984)
    domains = ["career", "health", "wealth"]
    for trial in range(200):
        n_anchor = rng.randint(0, 6)
        anchors = [
            anch(_u(7000 + i), chart=rng.choice([CANON, OTHER]), domain=rng.choice(domains),
                 we=date(2026, 11, rng.randint(1, 3)), falsifier=rng.choice(["a", "b", None]))
            for i in range(n_anchor)
        ]
        preds = []
        for j in range(rng.randint(0, 8)):
            kind = rng.random()
            freeze = _u(8000 + trial * 10 + j)
            ref = rng.choice(anchors)["anchor_id"] if anchors and kind < 0.3 else freeze
            preds.append(pred(trial * 10 + j, chart=rng.choice([CANON, OTHER]), freeze=freeze,
                              referenced=ref, domain=rng.choice(domains),
                              we=date(2026, 11, rng.randint(1, 3)),
                              falsifier=rng.choice(["a", "b", ""])))
        rows = fn(copy.deepcopy(preds), copy.deepcopy(anchors))
        assert len(rows) == len(preds)
        assert {(r["chart_id"], r["prediction_id"]) for r in rows} == {
            (p["chart_id"], p["prediction_id"]) for p in preds}
        for r in rows:
            assert not row_invariant_violations(r), (trial, r)
            if r["resolved_anchor_id"] is not None:  # a resolved anchor must exist IN-CHART
                assert any(_norm_id(a["anchor_id"]) == r["resolved_anchor_id"]
                           and str(a["chart_id"]) == r["chart_id"] for a in anchors), (trial, r)


def contract_checks(fn: ResolverFn) -> None:
    """The whole contract.  Raises AssertionError on the first violation."""
    for name, preds, anchors, expected in SCENARIOS:
        _check_scenario(fn, name, preds, anchors, expected)
    _check_production_shape(fn)
    _check_idempotent_and_order_independent(fn)
    _check_no_mutation_no_aliasing(fn)
    _check_rewritten_flag(fn)
    try:
        _check_duplicate_rejected(fn)
    except pytest.fail.Exception as exc:  # DID NOT RAISE -> a contract violation
        raise AssertionError(str(exc)) from exc
    _check_randomised_invariants(fn)


# ===========================================================================
# 2-3. Tests on the reference function
# ===========================================================================


@pytest.mark.parametrize("name,preds,anchors,expected", SCENARIOS, ids=SCENARIO_IDS)
def test_scenario(name, preds, anchors, expected):
    _check_scenario(resolve_references, name, preds, anchors, expected)


def test_production_shape_135_vanished_4_resolved():
    _check_production_shape(resolve_references)


def test_idempotent_and_order_independent():
    _check_idempotent_and_order_independent(resolve_references)


def test_inputs_not_mutated_outputs_not_aliased():
    _check_no_mutation_no_aliasing(resolve_references)


def test_rewritten_flag_means_reference_differs_from_freeze_id():
    _check_rewritten_flag(resolve_references)


def test_duplicate_prediction_key_is_rejected():
    _check_duplicate_rejected(resolve_references)


def test_randomised_row_invariants():
    _check_randomised_invariants(resolve_references)


def test_summarize_always_reports_all_three_statuses():
    assert summarize([]) == {STATUS_RESOLVED: 0, STATUS_SUPERSEDED: 0, STATUS_VANISHED: 0, "total": 0}
    rows = resolve_references(*production_shape(1, 2, 0))
    assert summarize(rows) == {STATUS_RESOLVED: 1, STATUS_SUPERSEDED: 0, STATUS_VANISHED: 2, "total": 3}


@pytest.mark.parametrize(
    "prediction_id,citation,referenced,expected",
    [
        ("pred_AAA", "CCC", "RRR", ("ccc", FREEZE_SRC_CITATION)),
        ("pred_AAA", None, "RRR", ("aaa", FREEZE_SRC_SUFFIX)),
        ("pred_AAA", "", "RRR", ("aaa", FREEZE_SRC_SUFFIX)),
        ("weird", None, "RRR", ("rrr", FREEZE_SRC_REFERENCED)),
        ("pred_", None, "RRR", ("rrr", FREEZE_SRC_REFERENCED)),
    ],
)
def test_freeze_anchor_id_provenance(prediction_id, citation, referenced, expected):
    assert freeze_anchor_id(prediction_id, citation, referenced) == expected


def test_falsifier_projection_mirrors_the_freezing_writer():
    # text that is not JSON -> {"raw": text}  (the shape of all 195 production rows)
    assert canonical_falsifier("REFUTED if x") == {"raw": "REFUTED if x"}
    assert canonical_falsifier("{'deny': 1}") == {"raw": "{'deny': 1}"}  # python-repr, not JSON
    assert canonical_falsifier('{"a": 1}') == {"a": 1}
    assert canonical_falsifier(None) == {} and canonical_falsifier("") == {}


def test_resolver_inputs_carry_no_outcome_or_calibration_fields():
    """Leak-guard stance: resolution is a function of reference + anchor columns only."""
    forbidden = re.compile(r"outcome|brier|calibrat|lifecycle|confirm|denied|posterior|reliab", re.I)
    for field in RESOLVER_PREDICTION_FIELDS | RESOLVER_ANCHOR_FIELDS:
        assert not forbidden.search(field), field
    src = inspect.getsource(resolve_references)
    for token in ("lifecycle_status", "outcome", "brier", "life_events", "calibration"):
        assert token not in src, f"resolver source must not touch {token!r}"
    # signature: two positional iterables + resolver_version, nothing else
    params = list(inspect.signature(resolve_references).parameters)
    assert params == ["predictions", "anchors", "resolver_version"]


def test_proposed_served_field_names_do_not_trip_the_calibration_leak_guard():
    """Design doc section 8 serves these keys; none may match CALIBRATION_LEAK_KEYS."""
    ts = LEAK_GUARD_TS.read_text(encoding="utf-8")
    block = ts.split("CALIBRATION_LEAK_KEYS", 1)[1].split("\n]", 1)[0]
    patterns = [m.group(1) for m in re.finditer(r"^\s*/(.+)/i,\s*(?://.*)?$", block, re.M)]
    assert len(patterns) >= 6, "failed to parse the guard's key list -- parser needs updating"
    served_keys = [
        "reference_resolution", "resolution_status", "resolution_basis", "resolved_anchor_id",
        "anchor_id_at_freeze", "reference_gap", "reference_gap_summary", "ledgered", "unledgered",
        "stale_ledger_rows", "dangling_anchor_references_present", "reference_rewritten_since_freeze",
    ]
    for key in served_keys:
        for pat in patterns:
            assert not re.search(pat, key, re.I), f"{key!r} matches leak key /{pat}/"


# ===========================================================================
# 4a. MUTATION PROOFS -- source-level mutants of the resolver
# ===========================================================================


def _build_mutant(patches: dict[str, tuple[str, str]]) -> ResolverFn:
    """Re-compile the resolver (and helpers) with textual patches; each patch must hit."""
    ns: dict[str, Any] = dict(globals())
    funcs = {
        "resolve_references": resolve_references,
        "anchor_claim_key": anchor_claim_key,
        "prediction_claim_key": prediction_claim_key,
        "freeze_anchor_id": freeze_anchor_id,
        "_norm_id": _norm_id,
    }
    for fname, func in funcs.items():
        src = textwrap.dedent(inspect.getsource(func))
        if fname in patches:
            old, new = patches[fname]
            assert old in src, f"mutation target {old!r} not found in {fname} (mutant would be a no-op)"
            src = src.replace(old, new, 1)
        exec(compile(src, f"<mutant:{fname}>", "exec"), ns)
    return ns["resolve_references"]


MUTANTS: dict[str, dict[str, tuple[str, str]]] = {
    "ids_not_chart_scoped": {
        "resolve_references": (
            "ids = by_chart_ids.get(chart, {})",
            "ids = {k: k for d in by_chart_ids.values() for k in d}",
        )
    },
    "claim_key_not_chart_scoped": {
        "resolve_references": (
            "cand = sorted(by_chart_claim.get(chart, {}).get(key, set()))",
            "cand = sorted(set().union(*[m.get(key, set()) for m in by_chart_claim.values()]))",
        )
    },
    "ambiguous_treated_as_superseded": {
        "resolve_references": ("elif len(cand) == 1:", "elif len(cand) >= 1:")
    },
    "ambiguity_resolved_by_picking_first": {
        "resolve_references": (
            "elif len(cand) > 1:\n            status, basis, resolved_anchor_id = STATUS_VANISHED, BASIS_CLAIM_AMBIGUOUS, None",
            "elif len(cand) > 1:\n            status, basis, resolved_anchor_id = STATUS_SUPERSEDED, BASIS_CLAIM_UNIQUE, cand[0]",
        )
    },
    "id_match_case_sensitive": {
        "_norm_id": ('return "" if value is None else str(value).strip().lower()',
                     'return "" if value is None else str(value).strip()')
    },
    "claim_key_ignores_window": {
        "prediction_claim_key": ("str(p[\"window_start\"]),\n        str(p[\"window_end\"]),",
                                 "'', '',"),
        "anchor_claim_key": ("str(a[\"window_start\"]),\n        str(a[\"window_end\"]),",
                             "'', '',"),
    },
    "claim_key_ignores_falsifier": {
        "prediction_claim_key": ("_fals_key(p[\"falsifier_jsonb\"]),", "'',"),
        "anchor_claim_key": ("_fals_key(canonical_falsifier(a.get(\"falsifier\"))),", "'',"),
    },
    "claim_key_ignores_domain": {
        "prediction_claim_key": ("str(p[\"domain\"]),", "'',"),
        "anchor_claim_key": ("str(a[\"domain\"]),", "'',"),
    },
    "freeze_id_never_consulted": {
        "resolve_references": ("elif frz and frz in ids:", "elif False:")
    },
    "freeze_beats_referenced": {
        "resolve_references": (
            "if ref and ref in ids:",
            "if ref and ref in ids and not (frz in ids and frz != ref):",
        )
    },
    "drops_vanished_rows": {
        "resolve_references": (
            "out.append(row)",
            "out.append(row) if row['resolution_status'] != 'vanished' else None",
        )
    },
    "sorts_caller_list_in_place": {
        "resolve_references": (
            "ordered = sorted(preds, key=_pred_sort_key)",
            "ordered = preds\n    preds.sort(key=_pred_sort_key)\n    if isinstance(predictions, list): predictions.sort(key=_pred_sort_key)",
        )
    },
    "writes_into_caller_prediction_dict": {
        "resolve_references": (
            "key = prediction_claim_key(p)",
            "p['_seen'] = True\n        key = prediction_claim_key(p)",
        )
    },
    "output_aliases_input_falsifier": {
        "resolve_references": (
            '"prediction_frozen_bundle_hash": str(p.get("frozen_bundle_hash") or ""),',
            '"prediction_frozen_bundle_hash": str(p.get("frozen_bundle_hash") or ""), "_alias": p,',
        )
    },
    "nondeterministic_output": {
        "resolve_references": (
            '"resolver_version": resolver_version,',
            '"resolver_version": resolver_version + uuid.uuid4().hex,',
        )
    },
    "duplicate_prediction_not_rejected": {
        "resolve_references": ('raise ValueError(f"duplicate prediction key {k!r}")', "pass")
    },
    "rewritten_flag_ignores_blank_reference": {
        "resolve_references": (
            '"reference_rewritten_since_freeze": ref != frz,',
            '"reference_rewritten_since_freeze": bool(ref and frz and ref != frz),',
        )
    },
    "candidate_count_lies": {
        "resolve_references": ('"candidate_count": len(cand),', '"candidate_count": 0,')
    },
    "vanished_keeps_stale_resolved_id": {
        "resolve_references": (
            "status, basis, resolved_anchor_id = STATUS_VANISHED, BASIS_NO_MATCH, None",
            "status, basis, resolved_anchor_id = STATUS_VANISHED, BASIS_NO_MATCH, ref",
        )
    },
}


def test_unmutated_reference_passes_the_whole_contract():
    contract_checks(resolve_references)


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_mutant_is_killed_by_the_contract(mutant):
    fn = _build_mutant(MUTANTS[mutant])
    with pytest.raises((AssertionError, KeyError, TypeError, ValueError)):
        contract_checks(fn)


# ===========================================================================
# 5. STATIC SQL CHECK over the design doc
# ===========================================================================

_FENCE = re.compile(r"^```sql[ \t]*([\w\-]*)[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
DDL_KIND, WRITER_KINDS, READ_KINDS = "ddl", ("writer",), ("detector", "reader", "evidence")
REGISTRY_KIND = "registry"
ASSET_ID = "mi_nirdesa"


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def sql_blocks(doc_text: str) -> list[tuple[str, str]]:
    """[(kind, comment-stripped sql)] for every ```sql <kind> fence in the doc."""
    return [(m.group(1) or "untagged", _strip_sql_comments(m.group(2))) for m in _FENCE.finditer(doc_text)]


def _statements(sql: str) -> list[str]:
    # split on ';' that is not inside a quoted literal (quoted literals hold no ';' in this doc)
    return [s.strip() for s in sql.split(";") if s.strip()]


_FROZEN = r"(?:public\.)?" + FROZEN_TABLE + r"\b"
_FROZEN_WRITE_PATTERNS = [
    rf"\bdelete\s+from\s+(?:only\s+)?{_FROZEN}",
    rf"\bupdate\s+(?:only\s+)?{_FROZEN}",
    rf"\binsert\s+into\s+{_FROZEN}",
    rf"\btruncate\s+(?:table\s+)?(?:only\s+)?{_FROZEN}",
    rf"\balter\s+table\s+(?:only\s+|if\s+exists\s+)*{_FROZEN}",
    rf"\bdrop\s+(?:table|trigger|policy|index|constraint)\b[^;]*{_FROZEN}",
    rf"\bcreate\s+(?:or\s+replace\s+)?(?:constraint\s+)?trigger\b[^;]*\bon\s+{_FROZEN}",
    rf"\bcreate\s+policy\b[^;]*\bon\s+{_FROZEN}",
    rf"\bmerge\s+into\s+{_FROZEN}",
    rf"\bcopy\s+{_FROZEN}\s+from\b",
    rf"\b(?:grant|revoke)\b[^;]*\bon\s+(?:table\s+)?{_FROZEN}",
    rf"\breferences\s+{_FROZEN}",
    rf"\bfor\s+(?:no\s+key\s+)?update\b[^;]*\b{FROZEN_TABLE}\b",
]
_FORBIDDEN_IN_DDL = [
    r"\breferences\b",          # no FK to anything: neither mimamsa_predictions nor phala_anchors
    r"\bforeign\s+key\b",
    r"\bon\s+delete\b",
    r"\bon\s+update\s+cascade\b",
    r"\bcreate\s+(?:or\s+replace\s+)?(?:constraint\s+)?trigger\b",
    r"\binherits\b",
]
_DML_OR_DDL = re.compile(
    r"\b(insert|update|delete|truncate|alter|drop|create|grant|revoke|merge|copy|call|do)\b", re.I
)


def sql_violations(doc_text: str) -> list[str]:
    """Every rule the design's SQL must obey.  Empty list == compliant."""
    v: list[str] = []
    blocks = sql_blocks(doc_text)
    kinds = {k for k, _ in blocks}
    for needed in (DDL_KIND, "writer", "detector", REGISTRY_KIND):
        if needed not in kinds:
            v.append(f"design doc has no ```sql {needed} block")
    for kind, sql in blocks:
        low = sql.lower()
        for pat in _FROZEN_WRITE_PATTERNS:
            if re.search(pat, low, re.S):
                v.append(f"[{kind}] touches {FROZEN_TABLE} destructively/structurally: /{pat}/")
        if kind == DDL_KIND:
            for pat in _FORBIDDEN_IN_DDL:
                if re.search(pat, low):
                    v.append(f"[ddl] forbidden construct /{pat}/ (ledger must not link to other tables)")
            for m in re.finditer(r"\bphala_anchors\b", low):
                v.append("[ddl] mentions phala_anchors (ledger DDL must not couple to the L4 table)")
                break
            for st in _statements(sql):
                if re.match(r"\s*(create|alter|grant|revoke|comment|drop)\b", st, re.I) and (
                    LEDGER_TABLE not in st.lower() and "idx_mimamsa_reference_resolution" not in st.lower()
                ):
                    v.append(f"[ddl] statement not about {LEDGER_TABLE}: {st[:70]!r}")
        elif kind in WRITER_KINDS:
            for st in _statements(sql):
                s = st.lower()
                if re.match(r"\s*delete\b", s):
                    if not re.match(rf"\s*delete\s+from\s+{LEDGER_TABLE}\s+where\s+chart_id\s*=", s):
                        v.append(f"[writer] DELETE must be 'DELETE FROM {LEDGER_TABLE} WHERE chart_id = ...': {st[:70]!r}")
                elif re.match(r"\s*insert\b", s):
                    if not re.match(rf"\s*insert\s+into\s+{LEDGER_TABLE}\b", s):
                        v.append(f"[writer] INSERT must target the ledger only: {st[:70]!r}")
                elif re.match(r"\s*(select|with)\b", s):
                    pass
                else:
                    v.append(f"[writer] unexpected statement: {st[:70]!r}")
        elif kind in READ_KINDS:
            for st in _statements(sql):
                if not re.match(r"\s*(select|with)\b", st, re.I) or _DML_OR_DDL.search(
                    re.sub(r"'[^']*'", "''", st)  # ignore words inside string literals
                ):
                    v.append(f"[{kind}] read-only block contains non-SELECT content: {st[:70]!r}")
        elif kind == REGISTRY_KIND:
            for st in _statements(sql):
                s_ = st.lower()
                if re.match(r"\s*insert\s+into\s+asset_registry\b", s_):
                    if f"'{ASSET_ID}'" not in s_.split("values", 1)[-1][:60]:
                        v.append(f"[registry] INSERT must be the {ASSET_ID} row: {st[:70]!r}")
                elif re.match(r"\s*update\s+asset_registry\b", s_):
                    if not re.search(rf"where\s+asset_id\s*=\s*'{ASSET_ID}'", s_):
                        v.append(f"[registry] UPDATE must be scoped to asset_id = '{ASSET_ID}': {st[:70]!r}")
                else:
                    v.append(f"[registry] only INSERT/UPDATE asset_registry for {ASSET_ID}: {st[:70]!r}")
        else:
            v.append(f"unknown sql block kind {kind!r}")
    return v


def _doc_text() -> str:
    assert DESIGN_DOC.is_file(), f"design doc missing: {DESIGN_DOC}"
    return DESIGN_DOC.read_text(encoding="utf-8")


def test_design_doc_sql_never_modifies_or_links_the_frozen_record():
    assert sql_violations(_doc_text()) == []


def test_design_doc_ddl_encodes_the_status_basis_matrix():
    ddl = " ".join(sql for k, sql in sql_blocks(_doc_text()) if k == DDL_KIND).lower()
    for token in STATUSES + tuple(b for bs in STATUS_BASES.values() for b in bs) + FREEZE_SOURCES:
        assert f"'{token}'" in ddl, f"DDL CHECK must mention {token!r}"
    assert "primary key (chart_id, prediction_id)" in re.sub(r"\s+", " ", ddl)
    for col in ("anchor_id_at_freeze", "resolution_status", "prediction_id", "resolved_anchor_id",
                "candidate_count", "claim_key", "prediction_frozen_bundle_hash", "resolver_version"):
        assert col in ddl, col


def test_design_doc_frontmatter_and_sections():
    text = _doc_text()
    assert text.startswith("---\n")
    fm = text.split("---\n", 2)[1]
    for key in ("artifact:", "version:", "status:", "changelog:"):
        assert key in fm, f"frontmatter missing {key}"
    for heading in (
        "## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.", "## 8.", "## 9.", "## 10.", "## 11.",
    ):
        assert re.search(rf"^{re.escape(heading)}", text, re.M), f"missing section {heading}"
    assert "needs number from SS" in text


def _repo_count_sql_placeholder_styles() -> collections.Counter:
    styles: collections.Counter = collections.Counter()
    pat = re.compile(r"count_sql[^;]{0,400}?chart_id\s*=\s*(\$1|:chart_id|%s|\$\{[A-Za-z_]+\})", re.S)
    for d in (MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR):
        for f in sorted(d.glob("*.sql")):
            try:
                txt = f.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in pat.finditer(txt):
                styles[m.group(1)] += 1
    return styles


def _integrity_block(doc_text: str) -> str:
    blocks = [sql for k, sql in sql_blocks(doc_text) if k == "detector" and "asset integrity" in sql.lower()]
    raw = [m.group(2) for m in _FENCE.finditer(doc_text)
           if m.group(1) == "detector" and "-- asset integrity" in m.group(2)]
    assert len(raw) == 1, "expected exactly one asset-integrity detector block"
    return _strip_sql_comments(raw[0])


def _norm_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip().rstrip(";").strip()


def registry_violations(doc_text: str) -> list[str]:
    """count_sql convention + integrity_check_sql identity for the registry block."""
    v: list[str] = []
    reg = [sql for k, sql in sql_blocks(doc_text) if k == REGISTRY_KIND]
    if len(reg) != 1:
        return [f"expected exactly one registry block, found {len(reg)}"]
    m = re.search(
        r"'SELECT count\(\*\) FROM mimamsa_reference_resolution WHERE chart_id = ([^']+)'", reg[0])
    if not m:
        v.append("registry block has no chart-scoped count_sql on the ledger table")
    elif m.group(1) != "$1":
        v.append(f"count_sql binds the chart as {m.group(1)!r}; the registry convention is '$1'")
    lit = re.search(r"\$integrity\$(.*?)\$integrity\$", reg[0], re.S)
    if not lit:
        v.append("registry block has no $integrity$ literal")
    elif _norm_sql(lit.group(1)) != _norm_sql(_integrity_block(doc_text)):
        v.append("registry integrity_check_sql differs from the section 7.2 block")
    for kind, sql in sql_blocks(doc_text):
        if ":chart_id" in sql:
            v.append(f"[{kind}] uses the ':chart_id' placeholder")
    return v


def test_count_sql_placeholder_matches_the_repo_registry_convention():
    styles = _repo_count_sql_placeholder_styles()
    assert styles.get("$1", 0) >= 20, f"could not establish the repo convention: {dict(styles)}"
    assert set(styles) == {"$1"}, f"mixed count_sql placeholder styles in migrations: {dict(styles)}"
    assert registry_violations(_doc_text()) == []


@pytest.mark.parametrize("name,mut", [
    ("colon_placeholder", lambda t: t.replace("WHERE chart_id = $1'", "WHERE chart_id = :chart_id'", 1)),
    ("percent_placeholder", lambda t: t.replace("WHERE chart_id = $1'", "WHERE chart_id = %s'", 1)),
    ("integrity_literal_drifts", lambda t: t.replace("btrim(prediction_frozen_bundle_hash) = ''", "btrim(prediction_frozen_bundle_hash) = 'x'", 1)),
])
def test_registry_checker_kills_mutant(name, mut):
    text = _doc_text()
    mutated = mut(text)
    assert mutated != text, f"{name}: mutation was a no-op"
    assert registry_violations(mutated), name


# ---- mutation proofs for the static checker ------------------------------------------------

_SQL_MUTANTS: dict[str, Callable[[str], str]] = {
    "extra_delete_on_frozen": lambda t: t + "\n```sql writer\nDELETE FROM mimamsa_predictions WHERE chart_id = %s;\n```\n",
    "extra_update_on_frozen": lambda t: t + "\n```sql writer\nUPDATE mimamsa_predictions SET source_pramana_id = 'x';\n```\n",
    "extra_insert_on_frozen": lambda t: t + "\n```sql writer\nINSERT INTO public.mimamsa_predictions (chart_id) VALUES (%s);\n```\n",
    "truncate_frozen": lambda t: t + "\n```sql writer\nTRUNCATE TABLE mimamsa_predictions;\n```\n",
    "alter_frozen": lambda t: t + "\n```sql ddl\nALTER TABLE mimamsa_predictions ADD COLUMN x int;\n```\n",
    "drop_frozen": lambda t: t + "\n```sql ddl\nDROP TABLE mimamsa_predictions;\n```\n",
    "trigger_on_frozen": lambda t: t + "\n```sql ddl\nCREATE TRIGGER t AFTER INSERT ON mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION f();\n```\n",
    "grant_on_frozen": lambda t: t + "\n```sql ddl\nGRANT DELETE ON mimamsa_predictions TO data_plane_builder;\n```\n",
    "policy_on_frozen": lambda t: t + "\n```sql ddl\nCREATE POLICY p ON mimamsa_predictions USING (true);\n```\n",
    "fk_to_frozen_in_ledger_ddl": lambda t: t.replace(
        "PRIMARY KEY (chart_id, prediction_id)",
        "PRIMARY KEY (chart_id, prediction_id),\n  FOREIGN KEY (chart_id, prediction_id) REFERENCES mimamsa_predictions (chart_id, prediction_id)", 1),
    "fk_to_anchor_table_in_ledger_ddl": lambda t: re.sub(
        r"resolved_anchor_id\s+uuid,",
        "resolved_anchor_id uuid REFERENCES phala_anchors (anchor_id) ON DELETE CASCADE,", t, count=1),
    "ledger_writer_deletes_unscoped": lambda t: t.replace(
        f"DELETE FROM {LEDGER_TABLE} WHERE chart_id = %s", f"DELETE FROM {LEDGER_TABLE}", 1),
    "detector_gains_dml": lambda t: t + "\n```sql detector\nSELECT 1; DELETE FROM mimamsa_reference_resolution;\n```\n",
    "reader_gains_cte_delete": lambda t: t + "\n```sql reader\nWITH d AS (DELETE FROM mimamsa_predictions RETURNING 1) SELECT * FROM d;\n```\n",
    "registry_block_updates_another_asset": lambda t: t + "\n```sql registry\nUPDATE asset_registry SET is_active = false WHERE asset_id = 'ph_nimitta';\n```\n",
    "registry_block_deletes_registry_rows": lambda t: t + "\n```sql registry\nDELETE FROM asset_registry WHERE asset_id = 'mi_nirdesa';\n```\n",
    "registry_block_unscoped_update": lambda t: t + "\n```sql registry\nUPDATE asset_registry SET natural_key_partition = 'x';\n```\n",
    "select_for_update_on_frozen": lambda t: t + "\n```sql detector\nSELECT * FROM mimamsa_predictions FOR UPDATE;\n```\n",
}


@pytest.mark.parametrize("mutant", sorted(_SQL_MUTANTS))
def test_sql_checker_kills_mutant(mutant):
    text = _doc_text()
    mutated = _SQL_MUTANTS[mutant](text)
    assert mutated != text, f"mutation {mutant} was a no-op against the doc"
    assert sql_violations(mutated), f"static SQL checker failed to flag mutant {mutant}"


def test_sql_checker_ignores_comments_that_merely_mention_the_frozen_table():
    benign = (
        "```sql ddl\n-- never DELETE FROM mimamsa_predictions here\n"
        "CREATE TABLE IF NOT EXISTS mimamsa_reference_resolution (chart_id uuid);\n```\n"
        "```sql writer\nDELETE FROM mimamsa_reference_resolution WHERE chart_id = %s;\n```\n"
        "```sql detector\nSELECT 1; /* UPDATE mimamsa_predictions */\n```\n"
        "```sql registry\nUPDATE asset_registry SET is_active = true WHERE asset_id = 'mi_nirdesa';\n```\n"
    )
    assert sql_violations(benign) == []


# ===========================================================================
# 6. HOLDS -- strict xfail: these flip to XPASS (= failure) the moment the real thing
#    lands, forcing whoever lands it to replace the hold with a real test.
# ===========================================================================


@pytest.mark.xfail(strict=True, reason="HOLD: production resolver module not written yet "
                                       "(brahmagyan/mimamsa/reference_resolution.py, design doc 6.2)")
def test_hold_production_module_matches_reference_on_every_scenario():
    from brahmagyan.mimamsa import reference_resolution as prod  # noqa: PLC0415

    for name, preds, anchors, expected in SCENARIOS:
        _check_scenario(prod.resolve_references, name, preds, anchors, expected)
        assert prod.resolve_references(copy.deepcopy(preds), copy.deepcopy(anchors)) == \
            resolve_references(copy.deepcopy(preds), copy.deepcopy(anchors))


@pytest.mark.xfail(strict=True, reason="HOLD: writer for the proposed asset mi_nirdesa is not registered yet "
                                       "(design doc 6.1)")
def test_hold_writer_registered_under_the_frozen_orchestrator_contract():
    from pipeline.orchestrator.writers import WriterBase, discover_all, get_writer  # noqa: PLC0415

    discover_all()
    cls = get_writer("mi_nirdesa")
    assert cls is not None and issubclass(cls, WriterBase)
    src = inspect.getsource(cls)
    assert ".commit(" not in src and ".close(" not in src, "writer must never commit/close ctx.db_conn"
    assert "asset_throughput" not in src, "orchestrator is the sole build-state writer"
    for pat in _FROZEN_WRITE_PATTERNS:
        assert not re.search(pat, src.lower(), re.S), pat


def _migration_files_creating_ledger() -> list[Path]:
    pat = re.compile(r"create\s+table\s+(if\s+not\s+exists\s+)?(public\.)?" + LEDGER_TABLE + r"\b", re.I)
    out: list[Path] = []
    for d in (MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR):
        for f in sorted(d.glob("*.sql")):
            try:
                if pat.search(_strip_sql_comments(f.read_text(encoding="utf-8"))):
                    out.append(f)
            except OSError:
                continue
    return out


@pytest.mark.xfail(strict=True, reason="HOLD: ledger-table migration (1264, protected public-schema window) not "
                                       "authored yet (design doc 4.1, 10); matched by file CONTENT so the real "
                                       "filename flips it")
def test_hold_ledger_migration_exists_and_matches_the_design_ddl():
    files = _migration_files_creating_ledger()
    assert files, "no migration creating mimamsa_reference_resolution"
    body = _strip_sql_comments(files[0].read_text(encoding="utf-8")).lower()
    assert not re.search(r"\breferences\b|\bon\s+delete\b|create\s+trigger", body)
    for pat in _FROZEN_WRITE_PATTERNS:
        assert not re.search(pat, body, re.S), pat
    protected = (_REPO_ROOT / "platform/scripts/migrate.ts").read_text(encoding="utf-8")
    assert files[0].name in protected, "1264 must be listed in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS (design doc 4.1)"


# ===========================================================================
# 7. REAL-POSTGRES LAYER
# ===========================================================================
# A throwaway cluster started by the fixture itself: loopback TCP on a free port, NO unix
# socket, temporary data directory, stopped by the recorded postmaster PID.  Nothing but this
# process's own cluster is ever started, stopped or touched.

NOLOGIN_ROLES = (
    "data_plane_schema_owner", "retrieval_census_ro", "role_web_serve", "role_jobs", "role_sidecar",
    "nirmana_evidence_ingress_writer", "suvarna_reader", "role_orchestrator", "role_ledger_write",
    "data_plane_builder",
)
LOGIN_ROLE = "amjis_app"

# Copied from production (information_schema / pg_get_constraintdef, read-only, 2026-10-03).
REGISTRY_STUB_DDL = """
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, layer text NOT NULL, sort_order integer NOT NULL,
  sanskrit_name text NOT NULL, english_name text NOT NULL, english_description text NOT NULL,
  storage_type text NOT NULL, target_table text, count_sql text, size_sql text, target_floor integer,
  expected_volume_formula text, expected_volume_inputs jsonb, volume_explanation text,
  depends_on text[] DEFAULT ARRAY[]::text[], scope text NOT NULL, is_active boolean DEFAULT true,
  estimated_seconds integer, created_at timestamptz DEFAULT now(), clear_tables text[],
  asset_type text NOT NULL DEFAULT 'data', layer_name text, layer_index text, provides_apis jsonb,
  health_probe jsonb, catalog_status text NOT NULL DEFAULT 'DRAFT',
  rebuild_on_probe_fail boolean NOT NULL DEFAULT false, integrity_check_sql text,
  has_substeps boolean NOT NULL DEFAULT false, asset_kind text NOT NULL DEFAULT 'data',
  service_health text, last_invoked_at timestamptz, last_selftest_at timestamptz, selftest_detail jsonb,
  has_writer boolean NOT NULL DEFAULT false, writer_timeout_seconds integer NOT NULL DEFAULT 600,
  domain text, rung text, superseded_by text REFERENCES asset_registry (asset_id),
  data_disposition text, natural_key_partition text, dead_flag boolean,
  CONSTRAINT asset_registry_asset_kind_check CHECK (asset_kind = ANY (ARRAY['data','service','artifact'])),
  CONSTRAINT asset_registry_asset_type_check CHECK (asset_type = ANY (ARRAY['data','service'])),
  CONSTRAINT asset_registry_catalog_status_check CHECK (catalog_status = ANY (ARRAY['CURRENT','DRAFT','RETIRED'])),
  CONSTRAINT asset_registry_domain_check CHECK (domain IS NULL OR domain = ANY (ARRAY['shared','chart'])),
  CONSTRAINT asset_registry_layer_check CHECK (layer = ANY (ARRAY['brahmagyan','ganita','bodha','kala','phala','mimamsa'])),
  CONSTRAINT asset_registry_natural_key_partition_needs_table CHECK (natural_key_partition IS NULL OR target_table IS NOT NULL),
  CONSTRAINT asset_registry_natural_key_partition_nonblank CHECK (natural_key_partition IS NULL OR btrim(natural_key_partition) <> ''),
  CONSTRAINT asset_registry_rung_check CHECK (rung IS NULL OR rung = ANY (ARRAY['R0','R1','R2','R3','R4','R5'])),
  CONSTRAINT asset_registry_scope_check CHECK (scope = ANY (ARRAY['global','per_chart'])),
  CONSTRAINT asset_registry_storage_type_check CHECK (storage_type = ANY (ARRAY['postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only','service']))
);
"""

SOURCE_STUB_DDL = """
CREATE TABLE charts (id uuid PRIMARY KEY);
CREATE TABLE phala_anchors (anchor_id uuid PRIMARY KEY, chart_id uuid NOT NULL, domain text,
  window_start date, window_end date, falsifier text);
CREATE TABLE mimamsa_predictions (
  chart_id uuid NOT NULL, prediction_id text NOT NULL, source_pramana_id text NOT NULL,
  outcome_claim text NOT NULL DEFAULT 'x', domain text NOT NULL, observation_window daterange NOT NULL,
  eval_date date NOT NULL DEFAULT '2030-01-01', confidence_band numrange NOT NULL DEFAULT '[0.4,0.7)',
  magnitude_expected text NOT NULL DEFAULT 'm', falsifier_jsonb jsonb NOT NULL, base_rate numeric,
  emitted_at timestamptz NOT NULL DEFAULT now(), lifecycle_status text NOT NULL DEFAULT 'pending',
  driving_signals jsonb NOT NULL DEFAULT '[]', frozen_bundle_hash text NOT NULL,
  bundle_formula_version text NOT NULL DEFAULT 'v', chart_context_stale_at timestamptz,
  PRIMARY KEY (chart_id, prediction_id));
CREATE TABLE mimamsa_manifestation_sets (chart_id uuid NOT NULL, prediction_id text NOT NULL,
  channel_id text NOT NULL, citation_ref jsonb NOT NULL, PRIMARY KEY (chart_id, prediction_id, channel_id));
CREATE FUNCTION app_chart_context() RETURNS uuid LANGUAGE sql AS $$ SELECT NULL::uuid $$;
"""


def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    w = shutil.which("initdb")
    if w:
        cands.append(Path(w).resolve().parent)
    for pat in ("/usr/lib/postgresql/*/bin", "/opt/homebrew/opt/postgresql@*/bin", "/opt/homebrew/bin",
                "/usr/local/opt/postgresql@*/bin", "/usr/local/bin"):
        cands.extend(Path(d) for d in sorted(glob.glob(pat), reverse=True))
    for d in cands:
        if all((d / b).exists() for b in ("initdb", "pg_ctl", "postgres")):
            return d
    return None


class _Pg:
    def __init__(self, bindir: Path, datadir: Path, port: int, pid: int):
        self.bindir, self.datadir, self.port, self.pid = bindir, datadir, port, pid

    def connect(self, dbname: str = "postgres", user: str = "postgres", autocommit: bool = True):
        import psycopg  # noqa: PLC0415

        return psycopg.connect(host="127.0.0.1", port=self.port, user=user, dbname=dbname,
                               autocommit=autocommit, connect_timeout=10)


@pytest.fixture(scope="module")
def pg():
    pytest.importorskip("psycopg")
    bindir = _find_pg_bin()
    if bindir is None:
        if os.environ.get("L5_LEDGER_REQUIRE_PG") == "1":
            pytest.fail("L5_LEDGER_REQUIRE_PG=1 but no PostgreSQL binaries (initdb/pg_ctl/postgres) found")
        pytest.skip("no PostgreSQL binaries found (initdb/pg_ctl/postgres); real-Postgres layer skipped")
    datadir = Path(tempfile.mkdtemp(prefix="l5led_pg_"))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    log = datadir / "server.log"
    try:
        subprocess.run([str(bindir / "initdb"), "-D", str(datadir / "d"), "-U", "postgres", "-A", "trust",
                        "-E", "UTF8", "--no-locale"], check=True, capture_output=True)
        subprocess.run([str(bindir / "pg_ctl"), "-D", str(datadir / "d"), "-l", str(log), "-w", "-t", "60",
                        "-o", f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories='' "
                              f"-c fsync=off -c synchronous_commit=off", "start"],
                       check=True, capture_output=True)
        pid = int((datadir / "d" / "postmaster.pid").read_text().splitlines()[0])
    except (subprocess.CalledProcessError, OSError) as exc:
        shutil.rmtree(datadir, ignore_errors=True)
        detail = (getattr(exc, "stderr", b"") or b"").decode("utf-8", "replace")[-300:]
        if os.environ.get("L5_LEDGER_REQUIRE_PG") == "1":
            pytest.fail(f"could not start a throwaway PostgreSQL: {exc!r} {detail}")
        pytest.skip(f"could not start a throwaway PostgreSQL ({exc!r}); real-Postgres layer skipped")
    h = _Pg(bindir, datadir, port, pid)
    try:
        yield h
    finally:
        subprocess.run([str(bindir / "pg_ctl"), "-D", str(datadir / "d"), "-m", "fast", "-w", "-t", "60", "stop"],
                       capture_output=True)
        for _ in range(100):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        shutil.rmtree(datadir, ignore_errors=True)


_DB_COUNTER = [0]


def _ddl_blocks() -> list[str]:
    return [sql for k, sql in sql_blocks(_doc_text()) if k == DDL_KIND]


def _provision_db(h: _Pg, *, window_and_ddl: bool, stubs: bool = True) -> str:
    """A fresh database shaped like production: schema public owned by data_plane_schema_owner,
    `amjis_app` (LOGIN, NOINHERIT, not superuser) holding USAGE only; source tables owned by amjis_app."""
    admin = h.connect()
    if not admin.execute("SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app'").fetchone():
        for r in NOLOGIN_ROLES:
            admin.execute(f"CREATE ROLE {r} NOLOGIN")
        admin.execute(f"CREATE ROLE {LOGIN_ROLE} LOGIN NOINHERIT")
    _DB_COUNTER[0] += 1
    name = f"l5led_{_DB_COUNTER[0]}"
    admin.execute(f"CREATE DATABASE {name}")
    admin.close()
    c = h.connect(name)
    c.execute("DROP SCHEMA public CASCADE")
    c.execute("CREATE SCHEMA public AUTHORIZATION data_plane_schema_owner")
    c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, role_web_serve, role_jobs, role_sidecar, "
              "suvarna_reader, role_orchestrator, data_plane_builder")
    if stubs:
        c.execute(SOURCE_STUB_DDL)
        c.execute(REGISTRY_STUB_DDL)
        for t in ("charts", "phala_anchors", "mimamsa_predictions", "mimamsa_manifestation_sets",
                  "asset_registry"):
            c.execute(f"ALTER TABLE {t} OWNER TO amjis_app")
    c.close()
    if window_and_ddl:
        _open_window(h, name)
        a = h.connect(name, user=LOGIN_ROLE)
        for blk in _ddl_blocks():
            a.execute(blk)
        a.close()
        _close_window(h, name)
    return name


def _open_window(h: _Pg, db: str) -> None:
    c = h.connect(db)
    c.execute("GRANT CREATE ON SCHEMA public TO amjis_app")
    c.close()


def _close_window(h: _Pg, db: str) -> None:
    c = h.connect(db)
    c.execute("REVOKE CREATE ON SCHEMA public FROM amjis_app")
    c.close()


@pytest.fixture(scope="module")
def ledger_db(pg):
    return _provision_db(pg, window_and_ddl=True)


def test_pg_routine_role_cannot_create_the_ledger_table_without_the_protected_window(pg):
    import psycopg  # noqa: PLC0415

    db = _provision_db(pg, window_and_ddl=False)
    c = pg.connect(db)
    assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
    assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'USAGE')").fetchone()[0] is True
    c.close()
    a = pg.connect(db, user=LOGIN_ROLE)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="permission denied for schema public"):
        a.execute(_ddl_blocks()[0])
    # re-running as the (future) owner does not help either: IF NOT EXISTS still needs CREATE only when absent,
    # so assert the table really is absent and nothing half-applied
    assert a.execute("SELECT to_regclass('public.mimamsa_reference_resolution')").fetchone()[0] is None


def test_pg_ddl_applies_inside_the_window_idempotently_and_closes_it(pg, ledger_db):
    h = pg
    c = h.connect(ledger_db)
    owner = c.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname = 'mimamsa_reference_resolution'").fetchone()[0]
    assert owner == "amjis_app"
    assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
    acl = c.execute("SELECT relacl::text FROM pg_class WHERE relname = 'mimamsa_reference_resolution'").fetchone()[0]
    for expect in ("role_orchestrator=arwd/amjis_app", "data_plane_builder=ard/amjis_app",
                   "suvarna_reader=r/amjis_app", "role_web_serve=r/amjis_app", "role_sidecar=r/amjis_app",
                   "role_jobs=r/amjis_app", "retrieval_census_ro=r/amjis_app",
                   "nirmana_evidence_ingress_writer=r/amjis_app"):
        assert expect in acl, (expect, acl)
    assert "role_ledger_write" not in acl
    pols = {r[0] for r in c.execute("SELECT polname FROM pg_policy WHERE polrelid = 'mimamsa_reference_resolution'::regclass")}
    assert pols == {"mimamsa_reference_resolution_g1c_chart_context", "mimamsa_reference_resolution_g1c_unscoped"}
    # nothing links the ledger to the frozen / anchor tables, and nothing was added to them
    assert c.execute("""SELECT count(*) FROM pg_constraint
                         WHERE contype = 'f' AND (conrelid = 'mimamsa_reference_resolution'::regclass
                            OR confrelid IN ('mimamsa_predictions'::regclass, 'phala_anchors'::regclass))""").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN "
                     "('mimamsa_predictions'::regclass, 'phala_anchors'::regclass)").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM pg_policy WHERE polrelid IN "
                     "('mimamsa_predictions'::regclass, 'phala_anchors'::regclass)").fetchone()[0] == 0
    c.close()
    # idempotent: a second pass inside a fresh window succeeds
    _open_window(h, ledger_db)
    a = h.connect(ledger_db, user=LOGIN_ROLE)
    for blk in _ddl_blocks():
        a.execute(blk)
    a.close()
    _close_window(h, ledger_db)


_LEDGER_COLS = ("chart_id, prediction_id, anchor_id_at_freeze, freeze_id_source, anchor_id_referenced, "
                "reference_rewritten_since_freeze, resolution_status, resolution_basis, resolved_anchor_id, "
                "candidate_count, current_anchor_count, claim_key, prediction_frozen_bundle_hash, "
                "resolver_version, build_id, resolved_at")
_GRID_RID = (None, "00000000-0000-0000-0000-0000000000aa")
_GRID_STATUS = STATUSES + ("bogus",)
_GRID_BASIS = tuple(b for bs in STATUS_BASES.values() for b in sorted(bs)) + ("bogus",)
_GRID_CAND = (-1, 0, 1, 2, 3)
_GRID_CUR = (-1, 0, 4)
_GRID_SRC = FREEZE_SOURCES + ("bogus",)


def cross_validate_check_matrix(conn, table: str = LEDGER_TABLE) -> list[str]:
    """Drive the exhaustive grid through INSERT; return every disagreement with the Python twin."""
    import psycopg  # noqa: PLC0415

    mismatches: list[str] = []
    i = 0
    for st in _GRID_STATUS:
        for bs in _GRID_BASIS:
            for rid in _GRID_RID:
                for n in _GRID_CAND:
                    for cur in _GRID_CUR:
                        for src in _GRID_SRC:
                            i += 1
                            row = {"resolution_status": st, "resolution_basis": bs, "resolved_anchor_id": rid,
                                   "candidate_count": n, "current_anchor_count": cur, "freeze_id_source": src}
                            twin = ddl_check_violations(row)
                            try:
                                conn.execute(
                                    f"INSERT INTO {table} ({_LEDGER_COLS}) VALUES "
                                    f"('{CANON}', %s, 'a', %s, 'a', false, %s, %s, %s, %s, %s, '{{}}', 'h', 'v', 'b', now())",
                                    (f"g{i}", src, st, bs, rid, n, cur))
                                db_ok, db_constraint = True, None
                            except psycopg.errors.CheckViolation as exc:
                                db_ok, db_constraint = False, (exc.diag.constraint_name or "").replace(f"{table}_", "")
                            if db_ok != (not twin):
                                mismatches.append(f"{row}: db_accepts={db_ok} twin_violations={twin}")
                            elif not db_ok and db_constraint not in twin:
                                mismatches.append(f"{row}: db rejected on {db_constraint} but twin says {twin}")
    return mismatches


def test_pg_check_matrix_agrees_with_the_python_twin_on_an_exhaustive_grid(ledger_db, pg):
    c = pg.connect(ledger_db, user=LOGIN_ROLE)
    try:
        assert cross_validate_check_matrix(c) == []
        # sanity: both outcomes were actually exercised
        accepted = c.execute(f"SELECT count(*) FROM {LEDGER_TABLE}").fetchone()[0]
        assert 0 < accepted < (len(_GRID_STATUS) * len(_GRID_BASIS) * len(_GRID_RID) * len(_GRID_CAND)
                                * len(_GRID_CUR) * len(_GRID_SRC))
        c.execute(f"DELETE FROM {LEDGER_TABLE}")
    finally:
        c.close()


def _ddl_mutants(ddl0: str) -> dict[str, str]:
    """Textual mutants of the CREATE TABLE block's CHECK matrix (each must change the text)."""
    def sub(pattern: str, repl: str) -> str:
        out, n = re.subn(pattern, repl, ddl0, count=1, flags=re.S)
        assert n == 1, f"DDL mutation target not found: {pattern!r}"
        return out

    return {
        "superseded_candidates_loosened": sub(r"(claim_key_unique'\s+AND resolved_anchor_id IS NOT NULL AND )candidate_count = 1", r"\1candidate_count >= 0"),
        "no_match_requires_non_null_anchor": sub(r"(resolution_basis = 'no_match'\s+AND )resolved_anchor_id IS NULL", r"\1resolved_anchor_id IS NOT NULL"),
        "ambiguous_threshold_loosened": sub(r"candidate_count >= 2", "candidate_count >= 0"),
        "resolved_no_longer_needs_anchor": sub(r"(\('id_match_referenced', 'id_match_freeze'\))\s+AND resolved_anchor_id IS NOT NULL\)", r"\1)"),
        "status_list_loses_superseded": sub(r"IN \('resolved', 'superseded', 'vanished'\)", "IN ('resolved', 'vanished')"),
        "freeze_source_list_loses_one": sub(r"'prediction_id_suffix', 'source_pramana_id'\)", "'prediction_id_suffix')"),
        "counts_check_drops_current_anchor": sub(r"CHECK \(candidate_count >= 0 AND current_anchor_count >= 0\)", "CHECK (candidate_count >= 0)"),
        "resolved_branch_admits_vanished": sub(r"\(resolution_status = 'resolved'\s+AND resolution_basis IN", "(resolution_status IN ('resolved', 'vanished') AND resolution_basis IN"),
        "no_match_admits_a_resolving_basis": sub(r"resolution_basis = 'no_match'", "resolution_basis IN ('no_match', 'id_match_referenced')"),
        "superseded_branch_dropped": sub(r"OR \(resolution_status = 'superseded'\s+AND resolution_basis = 'claim_key_unique'\s+AND resolved_anchor_id IS NOT NULL AND candidate_count = 1\)", ""),
    }


def test_pg_ddl_mutants_are_caught_by_the_cross_validation(pg):
    ddl0 = _ddl_blocks()[0]
    mutants = _ddl_mutants(ddl0)
    assert len(mutants) >= 10
    survivors = []
    for name, mutated in mutants.items():
        assert mutated != ddl0, name
        db = _provision_db(pg, window_and_ddl=False, stubs=False)
        c = pg.connect(db)  # superuser: this test is about CHECK semantics, not privileges
        c.execute(mutated)
        mism = cross_validate_check_matrix(c)
        c.close()
        if not mism:
            survivors.append(name)
    assert survivors == [], f"DDL mutants that cross-validation failed to catch: {survivors}"


def _load_production_shape(conn) -> tuple[list, list]:
    from psycopg.types.json import Jsonb  # noqa: PLC0415

    preds, anchors = production_shape()
    other_p = [pred(900 + i, chart=OTHER, freeze=_u(9000 + i), referenced=_u(9500 + i)) for i in range(3)]
    other_a = [anch(_u(9500 + i), chart=OTHER) for i in range(3)]
    for ch in (CANON, OTHER):
        conn.execute("INSERT INTO charts VALUES (%s) ON CONFLICT DO NOTHING", (ch,))
    for p_ in preds + other_p:
        conn.execute(
            "INSERT INTO mimamsa_predictions (chart_id, prediction_id, source_pramana_id, domain, "
            "observation_window, falsifier_jsonb, frozen_bundle_hash) VALUES (%s,%s,%s,%s,daterange(%s,%s),%s,%s)",
            (p_["chart_id"], p_["prediction_id"], p_["source_pramana_id"], p_["domain"], p_["window_start"],
             p_["window_end"], Jsonb(p_["falsifier_jsonb"]), p_["frozen_bundle_hash"]))
        conn.execute("INSERT INTO mimamsa_manifestation_sets VALUES (%s,%s,'ch_x',%s)",
                     (p_["chart_id"], p_["prediction_id"], Jsonb({"anchor_id": p_["citation_anchor_id"]})))
    for a_ in anchors + other_a:
        conn.execute("INSERT INTO phala_anchors VALUES (%s,%s,%s,%s,%s,%s)",
                     (a_["anchor_id"], a_["chart_id"], a_["domain"], a_["window_start"], a_["window_end"], a_["falsifier"]))
    return preds + other_p, anchors + other_a


def _blocks_by_kind() -> dict[str, list[str]]:
    out: dict[str, list[str]] = collections.defaultdict(list)
    for k, sql in sql_blocks(_doc_text()):
        out[k].append(sql)
    return out


def _run_writer(conn, chart: str) -> dict[str, int]:
    import psycopg  # noqa: PLC0415
    from psycopg.types.json import Jsonb  # noqa: PLC0415

    sel_p, sel_a, delete, insert = _statements(_blocks_by_kind()["writer"][0])
    conn.row_factory = psycopg.rows.dict_row
    pr = conn.execute(sel_p, (chart,)).fetchall()
    an = conn.execute(sel_a, (chart,)).fetchall()
    conn.row_factory = psycopg.rows.tuple_row
    rows = resolve_references(pr, an)
    conn.execute(delete, (chart,))
    for r in rows:
        conn.execute(insert, (r["chart_id"], r["prediction_id"], r["anchor_id_at_freeze"], r["freeze_id_source"],
                              r["anchor_id_referenced"], r["reference_rewritten_since_freeze"], r["resolution_status"],
                              r["resolution_basis"], r["resolved_anchor_id"], r["candidate_count"],
                              r["current_anchor_count"], Jsonb(r["claim_key"]), r["prediction_frozen_bundle_hash"],
                              RESOLVER_VERSION, "build-1", "2026-10-03T00:00:00Z"))
    return summarize(rows)


def _d1(conn) -> dict[str, dict[str, int]]:
    import psycopg  # noqa: PLC0415

    d1 = _statements(_blocks_by_kind()["detector"][0])[0]
    conn.row_factory = psycopg.rows.dict_row
    rows = conn.execute(d1).fetchall()
    conn.row_factory = psycopg.rows.tuple_row
    return {str(r["chart_id"]): dict(r) for r in rows}


def _reader_stats(conn, chart: str) -> tuple[dict[str, int], int]:
    """(summary row, number of per-row ledger_stale = true) from the doc's reader SQL."""
    import psycopg  # noqa: PLC0415

    per_row, summary = _statements(_blocks_by_kind()["reader"][0])
    conn.row_factory = psycopg.rows.dict_row
    rows = conn.execute(per_row, (chart,)).fetchall()
    summ = dict(conn.execute(summary, (chart,)).fetchone())
    conn.row_factory = psycopg.rows.tuple_row
    return summ, sum(1 for r in rows if r["ledger_stale"] is True)


def test_pg_writer_detector_reader_registry_end_to_end(pg):
    db = _provision_db(pg, window_and_ddl=True)
    kinds = _blocks_by_kind()
    conn = pg.connect(db, user=LOGIN_ROLE, autocommit=False)
    _load_production_shape(conn)
    conn.commit()
    digest_sql = kinds["evidence"][0]
    digest_before = conn.execute(digest_sql).fetchall()

    assert _run_writer(conn, CANON) == {STATUS_RESOLVED: 4, STATUS_SUPERSEDED: 0, STATUS_VANISHED: 135, "total": 139}
    assert _run_writer(conn, OTHER)["total"] == 3
    assert _run_writer(conn, CANON)[STATUS_VANISHED] == 135  # idempotent rerun replaces, never accretes
    conn.commit()
    assert conn.execute(f"SELECT count(*) FROM {LEDGER_TABLE}").fetchone()[0] == 142

    # D1 on the clean ledger; summary reader agrees with D1; nothing stale/unledgered/orphaned
    d1 = _d1(conn)[CANON]
    assert (d1["predictions"], d1["resolved"], d1["superseded"], d1["vanished"]) == (139, 4, 0, 135)
    assert (d1["unledgered"], d1["orphan_ledger_rows"], d1["stale_ledger_rows"]) == (0, 0, 0)
    summ, stale_rows = _reader_stats(conn, CANON)
    assert (summ["total_matching"], summ["ledgered"], summ["unledgered"], summ["resolved"], summ["superseded"],
            summ["vanished"], summ["vanished_ambiguous"], summ["reference_rewritten"],
            summ["stale_ledger_rows"], stale_rows) == (139, 139, 0, 4, 0, 135, 0, 135, 0, 0)

    # D2 / D3 / asset-integrity / per-row reader
    det = kinds["detector"]
    _d1_sql, d2, d3 = _statements(det[0])
    assert len(conn.execute(d2, (CANON,)).fetchall()) == 135
    d3rows = {str(r[0]): r[1:] for r in conn.execute(d3).fetchall()}
    assert d3rows[CANON] == (139, 4, 135) and d3rows[OTHER] == (3, 3, 0)
    assert conn.execute(det[1]).fetchone()[0] is True

    # D1 must be able to read false: each perturbation moves exactly its counter, and the reader's
    # stale predicate AGREES with D1 (MED-4: one definition of "stale").
    vanished_ref = conn.execute(
        "SELECT source_pramana_id FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id IN "
        "(SELECT prediction_id FROM mimamsa_reference_resolution WHERE chart_id = %s AND resolution_status = 'vanished') "
        "ORDER BY prediction_id LIMIT 1", (CANON, CANON)).fetchone()[0]
    first_pred = conn.execute("SELECT min(prediction_id) FROM mimamsa_predictions WHERE chart_id = %s", (CANON,)).fetchone()[0]
    perturbations = {
        "ledger row deleted": (f"DELETE FROM {LEDGER_TABLE} WHERE chart_id = '{CANON}' AND prediction_id = '{first_pred}'", "unledgered"),
        "vanished anchor id reappears": (f"INSERT INTO phala_anchors VALUES ('{vanished_ref}', '{CANON}', 'x', NULL, NULL, NULL)", "stale_ledger_rows"),
        "prediction replaced (hash)": (f"UPDATE mimamsa_predictions SET frozen_bundle_hash = 'zzz' WHERE chart_id = '{CANON}' AND prediction_id = '{first_pred}'", "stale_ledger_rows"),
        "prediction deleted": (f"DELETE FROM mimamsa_predictions WHERE chart_id = '{CANON}' AND prediction_id = '{first_pred}'", "orphan_ledger_rows"),
        "resolved anchor disappears": (f"DELETE FROM phala_anchors WHERE chart_id = '{CANON}' AND anchor_id = (SELECT resolved_anchor_id FROM {LEDGER_TABLE} WHERE chart_id = '{CANON}' AND resolution_status = 'resolved' ORDER BY prediction_id LIMIT 1)", "stale_ledger_rows"),
    }
    for label, (sql, counter) in perturbations.items():
        try:
            conn.execute(sql)
            moved = _d1(conn)[CANON]
            assert moved[counter] == 1, (label, moved)
            others = {"unledgered", "orphan_ledger_rows", "stale_ledger_rows"} - {counter}
            assert all(moved[o] == 0 for o in others), (label, moved)
            summ, stale_rows = _reader_stats(conn, CANON)
            assert summ["stale_ledger_rows"] == moved["stale_ledger_rows"] == stale_rows, (label, summ, moved, stale_rows)
            assert summ["unledgered"] == moved["unledgered"], label
        finally:
            conn.rollback()

    # the frozen-set digest is untouched by writer + detectors (the ledger never modifies the frozen table)
    assert conn.execute(digest_sql).fetchall() == digest_before
    conn.close()

    # registry block: runs as the ROUTINE role with NO window (DML on an amjis_app-owned table), is
    # idempotent, and its count_sql runs with a bound $1
    c2 = pg.connect(db, user=LOGIN_ROLE)
    assert c2.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
    for _ in range(2):
        for st in _statements(kinds["registry"][0]):
            c2.execute(st)
    row = c2.execute("SELECT count_sql, depends_on, scope, natural_key_partition, integrity_check_sql, has_writer "
                     "FROM asset_registry WHERE asset_id = 'mi_nirdesa'").fetchone()
    assert row[1] == ["mi_bhavisya", "ph_nimitta"] and row[2] == "per_chart" and row[5] is True
    assert c2.execute("SELECT count(*) FROM asset_registry").fetchone()[0] == 1
    c2.execute(f"PREPARE cnt AS {row[0]}")
    assert c2.execute(f"EXECUTE cnt('{CANON}')").fetchone()[0] == 139
    assert _norm_sql(row[4]) == _norm_sql(_integrity_block(_doc_text()))
    assert c2.execute(row[4]).fetchone()[0] is True
    c2.close()
