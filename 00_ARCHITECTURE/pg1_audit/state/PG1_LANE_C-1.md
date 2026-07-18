---
lane: C-1
status: verifying
implementer_model: claude-sonnet-5
verifier_model: opus
attempts: 1
---

## Scope

Chat/conversation-layer forensic verification of
`00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` (v0.5), §16.1
(Streaming and render) and §16.6 (Capabilities that do not exist today),
cross-read against §6.6 (the instrument must be able to ask) and §1.1's
A-11 through A-25 design-conclusion rows. Read-only: verified file:line
citations in `platform/src/app/api/chat/consult/route.ts`,
`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`,
`platform/src/components/consume/ConsumeChatV2.tsx`,
`platform/src/lib/synthesis/citation_check.ts`, and searched
`platform/tests/**`, `platform/migrations/**`, `platform/src/lib/mcp/**`,
`platform/src/lib/canary/**` for the substrate A-14/A-19/A-20 assume is
absent or present.

## Findings summary

12 findings emitted, all with non-empty evidence (file:line + quote).

- `confirmed`: 10 (PG1-C1-0001 through 0010)
- `partial`: 1 (PG1-C1-0011 — NO-LEAKAGE arm substrate only partially located)
- `new_defect`: 1 (PG1-C1-0012 — stale self-referential line-range comment in run_adapter_dispatch.ts)
- `stale`: 0
- `unverifiable`: 0

Total: 12.

**Headline finding:** every checked §16.1/§16.6 file:line citation this lane
sampled (the two-outcome planner at consult/route.ts:445-453, the
audience_tier stamp at :459, the raw-injection sites at :407-414/:436-444,
and citation_check.ts's PRESCRIPTIVE_CLASSES at :91/:129-135) is **byte-exact
correct** — the 2026-07-19 re-verification sweep claimed in the doc's own
"Verification standing" banner holds up under independent spot-check. The
one genuinely new item is PG1-C1-0012: `run_adapter_dispatch.ts:357`'s
comment claims parity with `route.ts:1373-1475`, but `consult/route.ts` is
only 1030 lines — that cited range does not exist in the current tree,
making the "adapter path mirrors the legacy onFinish gate" claim
unverifiable and a candidate F-25h for Z-1's append-only §16.1 table.
Secondary finding of note: A-11/§12.2 undercounts scope — the chat client
runs through `@assistant-ui/react-ai-sdk`'s `useChatRuntime` wrapper, not
bare AI SDK `useChat`, so the transport replacement's blast radius is one
layer deeper than stated (PG1-C1-0004).

## Evidence log

All 12 rows in `pg1_findings_C-1.jsonl`, IDs PG1-C1-0001 through
PG1-C1-0012. Each carries `evidence[].file` + `.line` + `.quote` sourced
directly from the working tree (git branch `pg1/wave`), not from the
architecture doc itself.

## Receipt

```json
{"lane":"C-1","verifier_model":"opus","diff_reviewed":"pending",
 "findings":{"emitted":12,"schema_valid":12,"evidence_complete":12},
 "assertions":{"script":"scripts/validate_findings.py","green":[],"red":[]},
 "scope_warden":"pass","verdict":"PENDING_REVIEW","diagnosis":""}
```
