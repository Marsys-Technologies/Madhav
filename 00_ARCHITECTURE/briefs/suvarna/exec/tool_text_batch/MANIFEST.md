---
artifact: TOOL_TEXT_BATCH_MANIFEST
version: 1.0
status: DRAFT_RED_BY_DESIGN
date: 2026-10-02
branch: suvarna/land/TI-tool-text-batch-001
base: suvarna/land/TI-formula-pins-001 (PR #2866 head)
changelog:
  - "1.0 (2026-10-02): first issue. Lists the pin-moving tool-text commits split out of PR #2866, what each changes and which pins/baselines each moves. Pins are NOT regenerated here: SS takes this branch to the Purna session for one coordinated re-baseline."
---

# Tool-text batch: commits that move Purna / Pariprashna pins

PR #2866 (formula pins) is GREEN and mergeable without these commits. This branch carries the ONLY
commits of that lane that move a pin, so SS can assemble the coordinated re-baseline. **This branch is
red by design: do not regenerate the pins on it** (no `capability_knowledge.snapshot.json`, no
`BEYOND_ACARYA_ACCEPTANCE_v13.json`, nothing under `platform/tests/pariprashna/**`).

Other tool-text commits already in PR #2866 (`chart_facts_query`, `get_karakas`, `get_sensitive_points`
served fields and notes) change no description, input_schema or `source_refs`, and were verified to move
no pin (knowledge snapshot hash unchanged; `beyond_acarya_acceptance`, `route_golden_stream`,
`synthesis_guidance_consult`, `nirmana-l0-analysis-receipts` all green on the PR head).

## Commits on this branch (on top of the PR head)

| # | Commit subject | What it changes | Pins / baselines it moves |
|---|---|---|---|
| 1 | `tool-text: refresh source-query availability probes and source_refs anchors for the three formula-pin readers` | Only `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts` (10 lines in, 10 out, line-neutral): the zero-row probe SQL for `get_karakas` (+`fact_subject`, +`formula_id`, total ORDER BY), `get_sensitive_points` (total ORDER BY) and `chart_facts_query` (+`formula_id`, handler ORDER BY) now mirror the handlers; `source_refs` anchors re-aimed (`get_karakas.ts:104-126`, `get_sensitive_points.ts:90-127`, `register_d7_channel.ts:972-1013` and `1133-1259`). | see below |
| 2 | `lint: allowlist entry for the get_karakas availability probe (pairs with the probe tool-text commit)` | `platform/scripts/governance/fact_category_pin_allowlist.json`: the `get_karakas` probe used to be matched by the `get_tara_chandra_bala` pattern through an identical snippet prefix; it needs its own entry once its projection changes. **Must travel with commit 1.** | none (lint config) |
| 3 | `chore: regenerate capability_estate_census` | `platform/src/generated/capability_estate_census.json` source hashes only (the census hashes `source_query_availability.ts`). Not a Purna pin. | none |

## Pins and baselines moved by commit 1

Measured on this branch (generator run to a scratch file and reverted; nothing committed):

| Pin / baseline | Before | After | Status on this branch |
|---|---|---|---|
| `platform/src/generated/capability_knowledge.snapshot.json` `content_hash` | `sha256:6c1aefca7601a9b7204471e0a3ccc03fe8ffa31819e5800b0d5e36fe83e156a8` | `sha256:65cc365fa3cf6ee5db906d826d7a1029dd6c91bfb0e63173e2a7eeb7ddd1ffc4` | stale; `npm run codegen:capability-knowledge:check` fails |
| same snapshot, `producer_contract_fingerprint` | `sha256:a68b6466f7c05ad9f904c99226480754d28b1c7b551850b5ccc7430a683031cf` | unchanged | no move |
| `capability_content_hash` in `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v13.json` (derives from the snapshot `content_hash`) | `sha256:6c1aefca…` | would become `sha256:65cc365f…` on re-baseline | `beyond_acarya_acceptance.test.ts` itself stays green (it compares committed artifacts, not the live hash) but the committed value is then out of step with the live snapshot |
| `platform/tests/pariprashna/route_ports/baseline/branch-deep-dive.json` | route output equals baseline | route fails with `CAPABILITY_KNOWLEDGE_STALE` before streaming | `route_golden_stream.test.ts` > `branch-deep-dive (from route-branch)` RED |
| `platform/tests/pariprashna/route_ports/baseline/branch-completeness-receipt.json` | same | same | `route_golden_stream.test.ts` > `branch-completeness-receipt (from route-branch)` RED |
| `platform/src/app/api/chat/__tests__/synthesis_guidance_consult.test.ts` (V3-E-024) | 200 | 500 (`CAPABILITY_KNOWLEDGE_STALE` in `consult/route.ts`) | RED |
| `platform/src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` | green | green | no move |

Root cause of all three reds: any change to a descriptor's `source_refs` / availability SQL changes the
knowledge snapshot `content_hash`, and the pariprashna / consult routes refuse a stale snapshot. No
description or input_schema is touched.

## To land (SS / Purna session)

1. Merge PR #2866 first (green on its own).
2. On top of it, take this branch's commits 1 + 2 together, then re-baseline in ONE pass:
   `npm run codegen:capability-knowledge -- --generated-at=<reviewed ISO>`, update
   `capability_content_hash` in `BEYOND_ACARYA_ACCEPTANCE_v13.json`, regenerate the two route_ports baselines,
   then re-run the four tests above.
3. Regenerate `capability_estate_census.json` last (commit 3 is only a convenience for this branch).

Also queued for this batch by the coordinator (not authored in this lane): the argala `get_argala.ts` text and
the ayurdaya `source_refs` line.
