PAR-F12-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform/src/lib/retrieval/registry/layers/L1_ganita/get_dignity.ts,
platform/src/lib/retrieval/registry/layers/L1_ganita/get_avasthas.ts,
platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts
(also covers F-37's file, platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts,
same defect class, same target stream — see F-37/DIAGNOSIS.md §6, no separate NEEDS_LEASE filed
for it individually)
Reason: F-12's DIAGNOSIS.md confirms this finding's actual mechanism is NOT in any file S2 owns
(response_budget.ts, registry_bridge.ts, kala_views/{elect,story,ritual,priority,shared}.ts —
none of which contain a `total` field or a chart_facts query for these three tools). The bug is
missing `SELECT COUNT(*)` sibling queries inside three L1 Gaṇita retrieval handlers (plus one L0
reference-catalog handler for F-37). Per LEASES.json, `platform (L1_ganita/** query files)` and
`capability SQL under layers/L0_*` are both explicitly S5 MŪLA's OWNS entries. This is not a
sara-kernel/response-composition problem at all (confirmed: ekv/a-09-sara-kernel's entire diff is
response_budget.ts + registry_bridge.ts, scoped to assess_* tools — none of which are involved
here) — it is a straightforward SQL-arithmetic fix, the same shape already correctly implemented
in the SAME directory's get_condition_composite.ts (Promise.all a page query + a COUNT(*) query).
Ask: route F-12 (and F-37, same shape) to S5 MŪLA for SPEC+BUILD — S5 already owns every file
these two findings touch. No lease extension into S2 needed or requested; this is a clean
same-stream routing, not a contested file.
Status: OPEN, awaiting conductor disposition. Does not block any other S2 lane — no file overlap
with S2's OWNS list.
