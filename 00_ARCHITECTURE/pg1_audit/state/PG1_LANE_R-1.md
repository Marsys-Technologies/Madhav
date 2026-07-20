---
artifact: PG1_LANE_R-1
lane: R-1
wave: PG-1 (Paripraśna Grounding Audit)
status: CLOSED
authored_by: Claude Code (Sonnet 5), Lane R-1 agent, 2026-07-19
audit_target: 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.5)
---

# PG1 Lane R-1 — Capability Inventory + Reconciliation

## Scope

Read-only audit of the MCP capability surface referenced by
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §1.1/§8: enumerate the live MCP
tool surface, reconcile it against `CAPABILITY_MANIFEST.json` and against
`platform-mcp/src/server.ts`'s own tool-count census, identify each
capability's registration path, and render verdicts on assumptions A1, A3,
A4, A5, A6, A9, A10.

Wrote only to `00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings_R-1.jsonl`
and this state file. No writes to `platform/src/**`, `platform-mcp/src/**`,
migrations, infra, workflows, or any governance-manifest file.

## Findings count by class

| class | count |
|---|---|
| new_defect | 2 |
| stale | 1 |
| confirmed | 2 |
| partial | 1 |
| unverifiable | 5 |
| **total** | **11** |

## Headline finding (PG1-R1-0001 + PG1-R1-0002, read together)

The "113 (manifest) vs ~200 (observed live)" discrepancy that BIND_PG-1.md
framed as this lane's opening question turns out to be **two separate
errors layered on top of each other, not one drift**:

1. **`CAPABILITY_MANIFEST.json` is not an MCP capability registry at all.**
   It is a governance-artifact catalog (`canonical_id`, `path`, `version`,
   `status`, `layer`, `expose_to_chat`) generated from markdown/data assets
   — its first entry is a `.md` file. It has none of the fields an MCP tool
   descriptor needs (no `input_schema`, `archetype`, `tool_role`). Comparing
   its `entry_count: 113` against the live MCP tool surface is a category
   error. The real "one registry" the architecture doc's A-08/D-08 refer to
   is `platform/src/lib/retrieval/registry/` (the `CapabilityDescriptor`
   type), which carries **119 distinct `marsys://tool/*` URIs**.

2. **`server.ts`'s own hand-maintained census is stale by its own math.**
   Its itemized comment computes `REGISTERED_TOOL_COUNT = 120` and calls
   itself "authoritative," but four of its own cited files undercount their
   actual `server.tool()`/`regAlias()`/`globalAlias()` call sites:
   `registry_bridge.ts` (25 actual vs 20 documented), `register_p1_synthesis.ts`
   (6 vs 3), `register_p1_aliases.ts` (55 vs 45, missing an entire
   dynamically-registered alias block), and `register_p2_dasha_lord.ts`
   (1 tool imported and called at `server.ts:364` but never added to the
   running total at all). Corrected sum: 120 + 5 + 3 + 10 + 1 = **139**,
   which exactly matches the live tool count observed in this session's
   connected `mcp__marsys-jis-direct__*` tool listing.

So the true picture is: **119 distinct registry capabilities, served as 139
MCP tool names (alias layer), documented internally as 120 (stale
undercount), and audited against 113 (wrong artifact entirely).** None of
these four numbers should be treated as interchangeable in future sessions.

## A1/A3-A6/A9/A10 verdicts (brief summary — full evidence in JSONL)

- **A1** (D-17 demoted, shim generator + unwired `codegen:check`) —
  **confirmed accurate**. The strangler shim generator exists exactly as
  described (`registry_shims.ts` header self-documents "NOT WIRED IN"), and
  `codegen:check` genuinely does not appear in any of the 8
  `.github/workflows/*.yml` files.
- **A3** (three registry projections incl. `marsys_drill`) — target-state,
  confirmed unbuilt (`marsys_drill` exists only in doc prose, never in
  source; server.ts registers all 139 tools unconditionally, no
  full/compact/chat split).
- **A4** (`mutation: true` class + sidecar pull-in) — target-state,
  confirmed unbuilt (no `mutation` field in `CapabilityDescriptor`; three
  live `KEYSTONE REQUEST` sidecar tools named in server.ts comments as the
  concrete pull-in inventory).
- **A5** (`density_contract` mandatory) — confirmed still optional
  (`density_contract?:` in types.ts), matching CLAUDE.md §N.6's own
  description.
- **A6** (one planner pipeline, `PlanReceipt`) — partially checked;
  evidence of planner multiplicity exists (3-4 distinct planner-named
  files) but `PlanReceipt` itself has zero hits in source — low-confidence,
  flagged for a follow-up lane with more time budget.
- **A9** (Model plane, OpenRouter, CachePlanner) — confirmed fully unbuilt;
  zero `model_plane` files, zero `OpenRouter` references outside the
  architecture doc itself.
- **A10** (D-16 per-turn provenance stamp) — **unverifiable**, this lane's
  time budget did not extend to a migrations/schema read; handed to R-2
  (which already has confirmed DB access) as a follow-up.

## Known methodology gap (PG1-R1-0011)

"Registration path per tool" (registry-backed / sidecar / alias / direct)
could not be fully machine-derived from import-statement grepping alone —
some files' handler bodies use calling mechanisms this lane's grep patterns
didn't catch (notably `register_p1_ganita.ts`'s 9 tools). A dedicated
handler-body-resolution script is needed for a complete per-tool
registration-path census; recorded as a defect in audit methodology, not a
claim about the architecture document.
