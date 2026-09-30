---
artifact: D_PINS_A2_PINS_READMISSION_AUTHORITY
version: 1.0
status: PINS_READMISSION_AUTHORIZED
date: 2026-09-30
decision: D-PINS-A2
campaign: pravaha
item: A2.3
---

# D-PINS-A2 — Nirmāṇa analysis-layer pins re-admission authority (pravaha/a2-kernel-geometry merge)

## The decision, verbatim

From `/Users/Dev/pravaha/run/EVENTS.jsonl`, 2026-09-30T03:22:56+00:00, actor `steward`:

> {"kind":"decision","actor":"steward","decision":"D-PINS-A2","state":"decided","detail":"Steward, on the native's 2026-09-30 standing authority (not a reserved decision): authorise the Nirmāṇa analysis-layer pins successor admission for merging pravaha/a2-kernel-geometry (ee0dd335f) — append-only, fail-closed, identity-bound authority evidence doc, per-asset delta classification from each writer's import closure, same pattern as D-E022; no edit of prior admissions; delivery-topology check must pass on a simulated squash onto the then-current main.","ts":"2026-09-30T03:22:56+00:00"}

Recorded by the steward on the native's standing authority of 2026-09-30 (the
autonomy addendum: the campaign runs headless; the steward decides or delegates
everything not reserved to the native — a pins readmission is not a reserved
decision). Quoted verbatim; nothing paraphrased.

## Scope of the authority granted

This authority is narrow. It authorises exactly one operation: fail-closed
successor admission (`nirmana_analysis_layer_pins.py --admit-successor`) for the
ONE stale analysis layer detected on branch `pravaha/a2-kernel-geometry` after
merging `origin/main` (`469009b6a8240dd3b2f59036e4f6356327ec004f`) — merge
commit `eccd32d14` — per `MERGE_HYGIENE_12_10c_RUNBOOK.md` step 2 and the D-E022
precedent:

- **L3** (`ka_` prefix): successor over the Pravāha A2.1 kernel-geometry
  changeset delta (accepted by the A2.2 independent review, Codex closure round
  3 ACCEPT on `ee0dd335f` — `ASTRA_REVIEW_A2_KERNEL_GEOMETRY_v1_2.md` in the
  Pravāha campaign repo's `00_ARCHITECTURE/briefs/pravaha/reviews/`).

It does **not** grant a general re-pin capability, does not touch any other
layer (L0/L1/L2/L4/L5 verify clean in delivery topology on this branch), and
does not authorise membership changes (none occurred — the changed set is
digest drift on existing writers only).

## Why the pin went stale

The branch's A2.1/A2.2-reviewed edits to `services/gochara_kernel/*` (arcs,
contacts, episodes, ids) and `services/ka_gochara/service.py` moved the import
closures of four L3 writers. The committed pin still names the D-E022 successor
aggregate (`d1bf773c4d94…`, admitted at the #2731 merge); the merged tree
derives the new aggregate. Detector-correct staleness: the writer sources moved;
the receipt did not. Per ADK-0026 the receipt is re-admitted, not the detector
weakened.

## Per-asset delta classification

Computed by comparing each writer's provenance closure
(`asset_runner._writer_source_paths` + transitive local-import closure) between
`origin/main` (`469009b6a8…`) and the branch HEAD. `git diff origin/main...HEAD
-- platform/python-sidecar/services` touches ONLY `gochara_kernel/*` and
`ka_gochara/service.py` — no writer's own module was edited on this branch.

| Asset | Classification | Cause |
|---|---|---|
| `ka_gochara_v3_century_materialize` | `derived_import_change` | closure imports `gochara_kernel/*` via `gochara_v3/*`; no own-module edit |
| `ka_moorti_nirnaya` | `derived_import_change` | closure imports `gochara_kernel/*`; no own-module edit |
| `ka_sangam` | `derived_import_change` | closure imports `gochara_kernel/*` and `ka_gochara/service.py`; no own-module edit |
| `ka_vedha_gochara` | `derived_import_change` | closure imports `gochara_kernel/*`; no own-module edit |

## Authority identity

The immutable approval identity for this authority is the commit that first
introduced this document: `fa0b0a9a003624b8f39e30600e98460a60170bb2`
