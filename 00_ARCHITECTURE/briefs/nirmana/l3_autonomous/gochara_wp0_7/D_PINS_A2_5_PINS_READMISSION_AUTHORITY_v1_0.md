---
artifact: D_PINS_A2_5_PINS_READMISSION_AUTHORITY
version: 1.0
status: PINS_READMISSION_AUTHORIZED
date: 2026-10-01
decision: D-PINS-A2.5
campaign: pravaha
item: A2.5
---

# D-PINS-A2.5 — Nirmāṇa analysis-layer pins re-admission authority (PR #2799, pravaha/a25-v41-candidate-writer)

## The decision, verbatim

From `/Users/Dev/pravaha/run/EVENTS.jsonl`, 2026-10-01T06:46:16+00:00, actor `steward`, message
M20261001T064616-8eed — the decision record:

> {"kind":"message","actor":"steward","to":"A","msg_id":"M20261001T064616-8eed","ref":"A2.5","detail":"D-PINS-A2.5 DECIDED: admit in THIS PR, per the standing rule (a PR that moves an L3 writer set/digest carries its own admission; D-PINS-A5.4 precedent): one L3 successor over main's current protected baseline adding ka_gochara_v4_41_candidate (classification: new writer; plus any other digest the PR moves, classified from content-hashed closures), pins JSON + census + generator authorization entry only; delivery-topology squash-sim residual lines must be byte-identical to main's. Fast-forward push, CI green, then report the new head — I dispatch the Codex review on that head (your packet v1.1 is good; append a §6 'pins admission' with the successor id). Do not queue.","ts":"2026-10-01T06:46:16+00:00"}

Recorded by the steward on the native's standing authority of 2026-09-30 (the
autonomy addendum: the campaign runs headless; the steward decides or delegates
everything not reserved to the native — a pins readmission is not a reserved
decision). Quoted verbatim; nothing paraphrased.

## Scope of the authority granted

This authority is narrow. It authorises exactly one operation: fail-closed
successor admission (`nirmana_analysis_layer_pins.py --admit-successor`) for the
ONE stale analysis layer detected on branch `pravaha/a25-v41-candidate-writer`
(PR #2799) after merging `origin/main` (`088d7dc5e`, Pravāha B5.5), per
`MERGE_HYGIENE_12_10c_RUNBOOK.md` step 2 and the D-PINS-A2 / D-PINS-A5.4
precedents:

- **L3** (`ka_` prefix): successor over the Pravāha A2.5 changeset delta, on top
  of main's protected baseline generation `l3:4f4a1993c6ad:1ddd6f117934` (the
  D-PINS-A5.4 r7 successor, delivered to main by the #2769 merge and now main's
  active L3 pin). The protected baseline entry is **not** rewritten: the
  committed `nirmana-analysis-layer-pins.json` on this branch is byte-identical
  to `origin/main`'s, and the admission archives that generation whole with its
  writer snapshot reconstructed from the protected baseline commit as its
  historical snapshot.

It does not grant a general re-pin capability, does not touch any other layer
(L0/L1/L2/L4/L5 verify clean in delivery topology on this branch), and is
limited to the ONE membership change the PR carries: the new candidate writer
`ka_gochara_v4_41_candidate`.

## Why the pin went stale

The branch adds the new L3 writer `ka_gochara_v4_41_candidate`
(`pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py`, Pravāha A2.5):
the derived writer inventory carries 23 `ka_` writers against the pinned 22.
The content-hashed-closure delta of the merged tree against `origin/main` is
exactly `{ka_gochara_v4_41_candidate}` — no other writer's digest moves
(verified: per-writer digest maps of `HEAD` vs `origin/main`, L3 and non-L3).
Classification: `approved_intentional_change` (a new own module shipped
intentionally under steward decision M20260930T195042-a4a0, Option A; the
steward's D-PINS-A2.5 wording "new writer" names this category).

## Authority identity

The immutable approval identity of this authority is the commit that first
introduced this document: `2292ee6b0cebceedc6fdaa80f0fd428e04231c65`.
