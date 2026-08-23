PAR-F46-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform-mcp/src/tools/register_p1_ganita.ts, platform-mcp/src/tools/register_p1_synthesis.ts
Reason: F-46's cleanest fix (per DIAGNOSIS.md §3) is a one-line call-site swap at each file's
`dualOutput` (`applyAutoBudgetToEnvelope` → `finalizeMcpBudget`), not a change to
response_budget.ts's exported functions themselves (both already exist and do the right thing;
only the caller's choice of which to call is wrong). These two files are S1 DVĀRA's
"tool registration files" / "dualOutput/pointer helpers" lease per LEASES.json, not S2's.
register_p1_synthesis.ts additionally carries S5's pre-existing ordered-handoff claim (§2.1,
CL-03 predicate fixes) — a third stream with a plausible claim on this one file.
Ask: either (a) a one-time narrow lease extension to S2 for this specific two-line change
(cleanest — no dualOutput redesign, just which function it calls), or (b) S2 hands this spec to
S1 to build once written, sequenced after S5's CL-03 work per the existing §2.1 ordering.
Status: **CONFIRMED-ROUTED by conductor**, verified against `LEASES.json` at source (FM-09) —
`register_p1_ganita.ts` piece builds at S1 (their existing `*register*.ts` lease);
`register_p1_synthesis.ts` piece follows that file's own ordered-handoff chain (currently S5,
later S4). S2 owns this lane end-to-end (spec both pieces in one SPEC.md, follow through
resubmission/build) rather than parking. Not blocking F-44 (same file, response_budget.ts side
only, no lease conflict) or the rest of S2's lanes.
