---
artifact: PURNA_ACCEPTANCE_PACKET_A_B_DIAGNOSIS
version: 1.0
status: FINDINGS_RECORDED_TWO_AUTHORITY_GATES_OPEN
date: 2026-09-29
campaign_id: madhav-purna-anvesana
phase: ACCEPTANCE_AND_LIVE_CLOSURE
governing_brief: 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_ACCEPTANCE_AND_LIVE_CLOSURE_v1_0.md
base_main_sha: 55ec5e3555a8bf2b4a3ed4f42397f03a56396b2d
candidate_validation: NOT_RUN
live_validation: NOT_RUN
campaign_completion: NOT_EARNED
---

# Packet A/B diagnosis — why the authenticated live turn fails

Read-only diagnosis plus three governed probe calls. No source, data, credential, IAM or
migration change was made. No private answer content is recorded here.

## 1. Runtime reconciliation (Packet A steps 1-2)

| Service | Serving revision | `NIRMANA_DEPLOYED_SHA` |
|---|---|---|
| `amjis-web` | `amjis-web-probe-55ec5e3555a8-36556176232-1` (100%) | `55ec5e3` = current `origin/main` |
| `amjis-mcp` | `amjis-mcp-probe-205a62618182-36388849236-1` (100%) | `205a626` (#2742 merge) |
| `amjis-sidecar` | `amjis-sidecar-probe-205a62618182-36388849236-1` (100%) | `205a626` |

- The brief's "verified web revision `1e0683e`" is superseded: web now serves `55ec5e3`, which
  contains both Purna merges (#2742, #2749) and #2752.
- `git diff 205a626 55ec5e3 -- platform-mcp` is empty, so the MCP/sidecar source is unchanged.
  The raw door's `inquiry_start` reports `deployed_revision=55ec5e3`. Acceptance config must
  pin per-door `door_expected_revisions`; this split is benign, not a defect.

## 2. Failure `36513034331` — classification

- Stream error: `PLANNER_INVALID_PLAN` (phase `plan`, ~0.7 s), raised in
  `platform/src/lib/pariprashna/pipeline/plan_stage.ts` from a planner `fault`.
- Server log: `AiConsoleError code AI_EXECUTION_FAILED` from `doStream` in the AI Console provider
  wrapper (`platform/src/lib/ai-console/providers/types.ts`), i.e. the selected provider call
  failed. `normalizeAiError` maps 401/402/403/404/429/5xx/network to specific codes, so this is
  a 400-class rejection or non-HTTP failure whose raw text is redacted by design.
- Reproduced once on the smoke path (same question, synthetic chart): same error.
- **Causality:** every planner invocation ever recorded for `probe-service-account` failed — 7 of 7
  (`ai_turn_role_invocations`, 2026-09-29 00:54Z–11:28Z, across revisions `fd4c3d4`, `952e5c3`,
  `1e0683e`, `55ec5e3`). Two planner invocations by another user on the same provider (`google`),
  same model (`gemini-2.5-flash`) and same code succeeded (09:32Z, 11:29Z). Connection metadata for
  both is identical (validated, structured-output capable). Classification: **provider /
  credential-or-entitlement for the probe account's own connection ("Production behaviour probe"),
  not Purna source and not a deploy regression.** The failure predates `1e0683e`.
- The workflow's informational `facts_consumed=0` and `citation.define=0` follow from the turn
  never reaching retrieval; they are not independent findings.
- Portal uses the probe's AI Console selection; a working provider connection for that account is
  a precondition of any Portal-door acceptance.

## 3. Chart evidence preflight (Packet B, partial)

- Managed MCP `prashna_ask` on the canonical chart `482012f1-…` ends the durable job `failed`
  with `CHART_RECOMPUTE_REQUIRED: The latest build of this chart failed.` The same refusal occurs
  on the synthetic chart `1c826d5a-…`.
- Cause: `platform/src/lib/charts/readingGate.ts` requires shared readiness `ready` for MCP
  `prashna_ask` (Paripraśna/Portal intentionally does not, per #2752). For the canonical chart
  readiness is not `ready`: the latest `build_runs` row is a failed `ga_positions` rebuild
  (`orphan-watchdog: run never dispatched`, 2026-09-19, trigger
  `l3-lane-frozen-manifest-rebuild`), and 42 active per-chart assets are non-lit — 11 `bo_*` stale, 11 `ka_*` (2 `error`, 9 `stale`),
  11 `mi_*` (8 `error`, 2 `stale`, 1 `dormant`), 9 `ph_*` stale. L1
  (`ga_*`) has no non-lit asset.
- Raw MCP `inquiry_start` on the canonical chart succeeds (lifecycle token + 13 next actions), so
  the raw door is reachable; its external synthesis step needs model credentials in the harness
  process, not yet verified.
- Not yet checked: served-generation head identity, `ga_strength` receipt, dasha binding,
  near-miss ratification, timing-obligation availability.

## 4. Local baseline

`vitest run scripts/purna` — 8 files, 68 tests, all pass on this branch.

## 5. Open authority gates (independent work otherwise continues)

1. **Probe provider credential** — Portal door cannot complete a turn. Credential operation.
2. **Canonical-chart readiness** — managed door refuses; producer rebuild/repair is not
   authorized, and the parallel L3 Kāla campaign owns `ka_*` on this chart. Alternatively a
   source-policy decision to align managed MCP with #2752 partial-chart semantics (HIGH/MED).

No candidate or live evidence exists. `campaign_completion` remains `NOT_EARNED`.
