PAR-F45-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform-mcp/src/tools/register_p1_aliases.ts (S5 MŪLA lease, ordered-handoff-owed from
S1 first), platform-mcp/src/tools/register_p1_synthesis.ts (S5 MŪLA lease, ordered-handoff-
pending to S4), platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts (S5
MŪLA lease), platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts (S5
MŪLA lease), platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts (S5 MŪLA
lease)
Reason: F-45's DIAGNOSIS.md traces all five named tools (bodha_signals_get,
synth_chart_brief_get, kala_priority_ranking_get, kala_windows_get, bodha_remedies_get) to stale
narrative-count fields computed BEFORE a generic budget trimmer shrinks their sibling array. Five
of the six files carrying these call sites are explicitly S5 MŪLA's per LEASES.json (the sixth,
response_budget.ts, IS S2's HOT file — see below). The primary fix (stop computing/baking the
count before the trim point, or route it through the correct pattern) lives at each call site,
not in S2's generic trim machinery.
Genuine partial S2 angle (not a full claim): response_budget.ts's finalizeMcpBudget/
applyResponseBudget have no concept of a scalar "companion count field" that describes a
sibling array and needs re-deriving after a trim — teaching the trimmer this convention (e.g. an
optional companionCountField on TrimmableSection) would be a legitimate, in-lease S2
contribution that the five call sites could then opt into. This is NOT an extension of
ekv/a-09-sara-kernel (confirmed: that branch's response_budget.ts diff is additive new code in a
different region, :641-830, SaraKernel/assembleSaraContent for assess_* tools only) — it would be
fresh work against origin/main.
Ask: (a) route the five call-site fixes to S5 MŪLA (four files) — S5 already owns all of them;
(b) S2 independently considers, at SPEC stage, whether adding a companionCountField convention to
response_budget.ts is worth building as a shared recurrence guard, coordinated with but not
gating S5's five call-site fixes (they can each be fixed locally without waiting on this).
Status: OPEN, awaiting conductor disposition. The optional response_budget.ts angle (b) can
proceed independently within S2's own lease if the conductor/S2 lead judges it worthwhile;
routing (a) is the blocking ask for the actual finding closure.
