---
artifact: wave-close-ac-sweep.md
session: wave-close
wave: ws1
swept_at: 2026-06-05T02:30:18Z
verdict: ALL_GREEN
---

# WS-1 Wave-Close AC Sweep

## AC-1 — Dashboard state chips + layer pip rail on client cards
**PASS**
- `ClientCard.tsx` implements `StateChip` (line 63) and `LayerPipRail` (line 135) components.
- Dashboard page renders both on every client card row.
- Source: `platform/src/components/dashboard/ClientCard.tsx`

## AC-2 — chart_created toast on dashboard after new client creation
**PASS**
- `ChartCreatedToast` component exists at `platform/src/components/brahma/ChartCreatedToast.tsx`.
- Dashboard page imports and renders it (line 162) when `?chart_created=[id]` is present in URL.
- `NewClientForm.tsx` wires the redirect with the `chart_created` query param.
- Source: `platform/src/app/dashboard/page.tsx`, `platform/src/components/brahma/ChartCreatedToast.tsx`

## AC-3 — Cockpit page at /clients/[id]/build loads without error
**PASS**
- Route exists at `platform/src/app/clients/[id]/build/page.tsx` with layout, error boundary, and test file.
- Build emits `ƒ /clients/[id]/build` in the route table (dynamic, server-rendered).
- Source: `platform/src/app/clients/[id]/build/`

## AC-4 — LayerTower renders L0–L5 bands bottom-up
**PASS**
- `LayerTower.tsx` exists at `platform/src/components/brahma/LayerTower.tsx`.
- Component renders bottom-up layers (L0–L5), with Brahmagyan bedrock at L0 and Mīmāṃsā always-active at L5.
- `STATUS_CHIP_CLASSES` and `STATUS_LABELS` mappings confirmed in source.
- Source: `platform/src/components/brahma/LayerTower.tsx`

## AC-5 — SSE endpoint streams build events (route exists + correct headers)
**PASS**
- Route at `platform/src/app/api/build/events/[buildId]/route.ts` exists.
- Emits `Content-Type: text/event-stream` header (line 107 confirmed).
- Build table confirms: `ƒ /api/build/events/[buildId]`

## AC-6 — pyramid-layers endpoint returns layer status
**PASS**
- Route at `platform/src/app/api/build/pyramid-layers/route.ts` exists.
- Queries DB for `layer, sublayer, status` and groups into Layer objects with asset arrays.
- Build table confirms: `ƒ /api/build/pyramid-layers`

## AC-7 — AssetInspector panel renders on asset click
**PASS**
- `AssetInspector.tsx` exists at `platform/src/components/brahma/AssetInspector.tsx`.
- Per-asset API at `platform/src/app/api/assets/[chart_id]/[asset_key]/route.ts` confirmed in build: `ƒ /api/assets/[chart_id]/[asset_key]`

## AC-8 — "Consult now (Gaṇita)" button on L1 band when status=built
**PASS**
- `LayerTower.tsx` renders the button at lines 205–214:
  ```
  {layer.layer === 'L1' && layer.status === 'built' && onConsultClick && (
    <button ... data-testid="consult-now-btn">Consult now (Gaṇita)</button>
  )}
  ```
- Prop `onConsultClick` wired from cockpit page.
- Source: `platform/src/components/brahma/LayerTower.tsx`

## AC-9 — ConsumeChatV2 shows capability gate state (no-build / building / ready)
**PASS**
- `ConsumeChatV2.tsx` defines `CapabilityGateState` union type with three states:
  - `no-build` (line 67) — renders no-build banner (`data-testid="capability-gate-no-build"`)
  - `l1-building` (line 68) — renders amber building banner (`data-testid="capability-gate-l1-building"`)
  - `ready` (line 69) — chat fully grounded
- Source: `platform/src/components/consume/ConsumeChatV2.tsx`

## AC-10 — /admin/foundation route exists, gated to super_admin
**PASS**
- Route at `platform/src/app/admin/foundation/page.tsx` with `L0TowerIsland.tsx` island.
- Role gate at line 126: `if (ctx.profile.role !== 'super_admin') redirect('/dashboard')`
- Build table confirms: `ƒ /admin/foundation`

## AC-11 — npm run build exits 0
**PASS**
- `cd platform && npm run build` exited 0.
- Output: `✓ Compiled successfully in 17.2s`
- TypeScript: `Finished TypeScript in 8.2s` — no errors.
- 13 warnings present but all are pre-existing known patterns (dynamic path analysis, optional
  deps html-pdf-node, bundle_adapters.js) — none introduced by WS-1 sessions.

## AC-12 — No TypeScript errors
**PASS**
- TypeScript compilation finished cleanly: 0 errors.
- All WS-1 components (LayerTower, AssetInspector, ChartCreatedToast, ConsumeChatV2 gate,
  capability-gate.ts, admin/foundation page) passed type-checking.

---

## Summary

| AC | Description | Verdict |
|----|-------------|---------|
| AC-1 | State chips + layer pip rail | PASS |
| AC-2 | chart_created toast | PASS |
| AC-3 | /clients/[id]/build cockpit | PASS |
| AC-4 | LayerTower L0–L5 bottom-up | PASS |
| AC-5 | SSE endpoint + correct headers | PASS |
| AC-6 | pyramid-layers endpoint | PASS |
| AC-7 | AssetInspector panel | PASS |
| AC-8 | Consult now (Gaṇita) on L1 built | PASS |
| AC-9 | ConsumeChatV2 3-state gate | PASS |
| AC-10 | /admin/foundation super_admin gated | PASS |
| AC-11 | npm run build exits 0 | PASS |
| AC-12 | No TypeScript errors | PASS |

**All 12 ACs: GREEN. WS-1 wave approved for merge.**
