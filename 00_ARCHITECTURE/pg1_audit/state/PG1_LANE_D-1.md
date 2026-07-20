---
lane: D-1
status: COMPLETE
---

# PG1 Lane D-1 — Conversation data reality

## Scope

Read-only audit (DB reads in scope for this lane) of the conversation/message
data plane referenced by `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` — sizing
whether the parts_json → canonical message_parts migration described there
is a script or a salvage operation. Queried the live `amjis` Postgres
instance via `mcp__postgres__query` (SELECT-only).

## Findings count by class

| class | count |
|---|---|
| confirmed | 1 |
| new_defect | 1 |
| unverifiable | 1 |
| informational | 1 |
| **total** | **4** |

Severity: 1 high, 2 medium, 1 low.

## Headline finding

**It's neither a script nor a salvage operation — it's a green-field schema
fix with no data to migrate yet.**

The lane brief pointed at "assumption A26" as the governing claim, but A-26
in the current doc (v0.5) is about mobile UX, not conversation data (finding
PG1-D1-0001) — the actually load-bearing assumption is **A-08** (canonical
`conversation_messages` + `message_parts` child rows) and forensic finding
**F-25e** (`parts_json` has no version discriminator, so any blob→parts
migration is "unverifiable by the document's own argument").

DB reality (PG1-D1-0002, PG1-D1-0003): the schema matches the doc's "today"
description exactly — `conversation_messages.parts_json` is an
undifferentiated `jsonb` blob with no version column, and no
`message_parts` table exists anywhere in the 251-table schema. But **every
conversation-adjacent table has zero rows** — `conversation_messages`,
`conversations`, `conversation_message_embeddings`, `conversation_branches`,
`conversation_folders`, `conversation_folder_members`,
`conversation_shares`, `project_conversations` all count 0. This is not an
empty/stale DB — the same instance holds 276,206 `chart_facts` rows, 4 built
charts, 3 profiles, and 2 real `mcp_sessions` rows spanning 2026-07-01 to
2026-07-17. The Paripraśna portal conversation-persistence path has simply
never written a row.

**Consequence for planning:** the doc's framing (shape-infer AI SDK v4 vs
v5 from existing rows, size an unmigratable residue, sequence a
shape-inferred blob migration as an appendix-scoped operation) assumes a
corpus that does not exist in this instance. There is nothing to sample,
nothing to classify, and no residue to size — the sampling/shape-inference
part of this lane's charge is **unverifiable** for lack of data, not because
the data is ambiguous. The actionable move is cheap and immediate: add a
schema-version column to `parts_json`/`metadata_json` now, before the first
real row lands, and the entire "unverifiable migration" risk in F-25e is
eliminated rather than deferred. Caveat (PG1-D1-0004): this lane had exactly
one DB connection available; if a separate production instance exists with
real conversation history, these counts must be re-verified against it
before treating F-25e as moot.

## Files

- `00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings_D-1.jsonl` (4 findings)
