PAR-F125-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform-mcp/src/tools/kala_views/upaya.ts (S4 VĀCA lease), platform-mcp/src/tools/register_p1_aliases.ts (S5 MŪLA lease, via the generic regAlias helper — also affects the
sibling bodha_domain_reading_get, not named in F-125's original claim but confirmed same-defect
in Stage-D sibling census)
Reason: F-125's B.11 orientation gate (fetchOrientationContext, registry_bridge.ts:2061) is
module-private with 15 in-file call sites — structurally unreachable from other files. S2's own,
in-lease piece of the fix is exporting fetchOrientationContext from registry_bridge.ts so it is
callable elsewhere. The actual wiring-in at kala_upaya_get and bodha_remedies_get/
bodha_domain_reading_get requires edits inside S4's and S5's files respectively.
Ask: S2 will build+ship the export (small, contained, no behavior change to existing 15
call sites). S4 and S5 each take a short spec for wiring the exported gate into their own
handlers once S2's export lands — conductor to route or confirm ordering.
Status: **CONFIRMED-ROUTED by conductor**, verified against `LEASES.json` at source (FM-09) —
`upaya.ts` piece builds at S4; `register_p1_aliases.ts` piece routes to S5, queued behind S1's
`dualOutput` toolName sweep on that file. S2 owns this lane end-to-end (spec the export + both
wiring pieces in one SPEC.md, follow through resubmission/build) rather than parking.
