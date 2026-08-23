PAR-F28-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform/src/lib/retrieval/registry/tool_name_bridge.ts (S1 DVĀRA lease — root cause),
platform-mcp/src/tools/register_p1_aliases.ts (S5 MŪLA lease — schema/registration, no
budget_kb override param), platform/src/lib/retrieval/registry/layers/L5_mimamsa/
query_calibration.ts (S3 SATYA lease — possible alternate fix site: handler could pre-shape its
own response as `{results: [...]}`, the escape hatch tool_name_bridge.ts's toToolBundleResults
already recognizes, instead of a flat multi-array object).
Reason: F-28's DIAGNOSIS.md (§3, §6) traces the truncation to three layers. The truncation lever
itself (response_budget.ts:447-454, MAX_STRING_CHARS=120, S2's own HOT file) is confirmed WORKING
AS DESIGNED — a genuine last resort that correctly fires once every other trim option is
exhausted. It is not the defect. The real defect is upstream: tool_name_bridge.ts:237-262's
`toToolBundleResults()` — "the ONLY place the ToolBundle <-> ToolResult shape conversion lives"
per its own doc-comment — collapses ANY object-shaped ToolResult.content (the standard,
documented shape per registry/types.ts:533, used by all 172 capability handler files, zero of
which pre-shape as {results:[...]}) into a single opaque JSON string before autoDetectTrimmableSections
(response_budget.ts) ever gets a chance to see the real array structure inside it. By the time
the response reaches S2's response_budget.ts, the four separate arrays
(verdict_distribution/reliability_curve/multipliers/qa_results — 4/6/9/168 rows respectively,
live-confirmed via DB) are already gone, flattened into one string. There is no fix S2 can make
inside response_budget.ts alone that closes this gap — the structural information is destroyed
one layer upstream, in a file S2 does not own.
Separately, register_p1_aliases.ts:1844-1857 (mimamsa_calibration_get's own MCP-facing schema)
exposes no budget_kb/response_format override parameter at all (live-confirmed via the tool's
actual JSONSchema) — even if tool_name_bridge.ts's collapse were fixed to preserve structure, a
caller still has no lever to request more than the 40KB default ceiling for a genuinely large
result set like this one (168 QA rows alone).
Ask: this needs either (a) a spec that S1 builds against tool_name_bridge.ts's
toToolBundleResults (narrowly scoped to the "Single ToolResult, object content" branch, to avoid
destabilizing S1's own in-flight lanes on the same file — see LEASES.json's note that
tool_name_bridge.ts is already a multi-lane hotspot via F-09/F-123 routing), with S5 building a
short companion change to register_p1_aliases.ts's mimamsa_calibration_get schema/dualOutput call
if a budget_kb param is the chosen lever, and optionally S3 evaluating whether
query_calibration.ts should pre-shape its own response instead (the escape-hatch route, which
would avoid touching tool_name_bridge.ts entirely) — or (b) S2 writes the full SPEC (this
diagnosis already has the mechanism, sibling census, and file:line detail SPEC stage needs) and
hands it to S1 as the primary builder, with S5's/S3's pieces as named dependencies in that SPEC,
per the plan's own rule that specs travel even when leases don't.
Status: **CONFIRMED-ROUTED by conductor** (option (b) taken) — build routes to S1 against
`tool_name_bridge.ts`. Verified against `LEASES.json` at source (FM-09), not just the relay.
`SPEC.md` now written in this lane dir. S2 owns this lane end-to-end going forward (through
resubmission on any INCOMPLETE-RETURN, through confirming S1's build once it lands) rather than
parking after Stage S, per the updated stream process.
Not blocking any other S2 lane — response_budget.ts itself needs no change for F-28.
