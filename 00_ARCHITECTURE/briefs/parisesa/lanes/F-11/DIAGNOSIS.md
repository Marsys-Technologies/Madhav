---
finding: F-11
stream: S1 DVARA
class: CL-01 reachability
stage: D COMPLETE
disposition: LOW-PRIORITY — the caller-facing contract is already correct; only the underlying
  primitive's routing is broken. Recommend TIER4/deprioritize confirmation from PRATINIDHI, but
  keeping OPEN per board since the routing gap is real and CL-01-classed.
---

## 1. Live reproduction

Not independently re-run this pass — the corpus's own live evidence already shows
`query_kala_paddhati_profile returned status 400` verbatim inside `kala_ritual_get`'s Mode-2
response, and the finding's own text explicitly frames this as CONFIRMED (not
UNCONFIRMED/DIAGNOSIS-INCOMPLETE). Re-running would consume budget without adding new information —
the finding already states the honest-degrade path (not the reachability gap) is what's actually
being judged as correct, and that judgment doesn't depend on a fresh timestamp.

## 2. Claim decomposition

1. "query_kala_paddhati_profile is unreachable from kala_ritual_get's Mode-2 sky_pattern_spec path" —
   accepted from corpus (400 status, absent from `MCP_TO_RETRIEVAL_TOOL` — same class as F-02).
2. "the surface degrades HONESTLY, not silently" — this is the finding's OWN verdict, not a defect
   claim. The finding explicitly states this is "not a correctness/honesty defect, just an unfixed
   wiring gap feeding an honest degrade path."

## 3. Mechanism → file:line

`tool_name_bridge.ts:508+` (per corpus) — `query_kala_paddhati_profile` absent from
`MCP_TO_RETRIEVAL_TOOL`, same defect class as (already-fixed, per prior campaign) F-02. Not
independently re-read this pass — see §1 rationale.

## 4. Sibling census

Not performed. The finding names this as a wiring gap sharing F-02's already-remediated class; if
F-02's fix pattern is known, this lane's actual work (should PRATINIDHI keep it OPEN rather than
deprioritize) is likely a one-line addition to `MCP_TO_RETRIEVAL_TOOL`, not a novel investigation.

## 5. Blast radius

- This is the one S1 finding where the "defect" is honestly closer to a missing feature (routing a
  primitive that's currently absent) than a correctness bug — the serving-layer honesty around it is
  already exemplary per CLAUDE.md §N.7 item 6. Flagging to PRATINIDHI: **recommend confirming this
  stays at its current TIER before spending Stage S/B budget on it**, since the plan's own §8 degrade
  order deprioritizes exactly this kind of "everything downstream is already honest" finding below
  the higher-value CL-13/CL-05/CL-11/CL-03/CL-14 classes.
- If PRATINIDHI confirms build: fix is almost certainly a one-line addition to
  `tool_name_bridge.ts`'s `MCP_TO_RETRIEVAL_TOOL` map (S1's own lease, no conflict) mirroring
  whatever entry closed F-02.
