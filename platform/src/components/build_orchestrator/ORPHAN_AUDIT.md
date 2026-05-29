# Orphan Audit — H-01

Session: H-01 (Delete BuildChat + scaffold ConstellationCanvas)
Date: 2026-05-29
Branch: feature/build-orch/stream-h

## Files Examined

### DELETED

| File | Reason |
|------|--------|
| `platform/src/components/build/BuildChat.tsx` | Replaced by ConstellationCanvas. Was the old chat-shell UI for the /build route. No longer imported after page.tsx rewrite. |
| `platform/src/app/clients/[id]/build/BuildActionPanel.tsx` | Old SSE-based build trigger panel. Replaced by ConstellationCanvas architecture (SSE consumer moves to H-09). |
| `platform/src/app/clients/[id]/build/__tests__/BuildActionPanel.test.tsx` | Test exclusively for deleted BuildActionPanel. Orphaned; deleted with its subject. |

### MODIFIED (importers cleaned)

| File | Change |
|------|--------|
| `platform/src/app/clients/[id]/build/page.tsx` | Removed `BuildChat` import + usage; replaced with `ConstellationCanvas`. Removed DB queries now unnecessary (layers, chart name, conversations, fetchBuildState). Access guard retained. |
| `platform/src/app/clients/[id]/build/[conversationId]/page.tsx` | Removed `BuildChat` import + usage; replaced with redirect to `/clients/[id]/build`. TODO comment for H-09 SSE deep-link wiring. |
| `platform/src/app/clients/__tests__/chart_pages.test.tsx` | Updated `vi.mock('@/components/build/BuildChat')` → `vi.mock('@/components/build_orchestrator/ConstellationCanvas')`; updated assertion from `build-chat-mock` → `constellation-canvas`. |

### KEPT (untouched — not orphaned)

| File | Reason |
|------|--------|
| `platform/src/components/build/BuildRightPane.tsx` | Still potentially useful; not exclusively referenced by BuildChat only. Stream H will determine if it is reused or retired. |
| `platform/src/components/build/PhaseGrid.tsx` | Used by BuildRightPane or other build components. |
| `platform/src/components/build/BriefPanel.tsx` | Used by BuildRightPane. |
| `platform/src/components/build/InsightCards.tsx` | Used by BuildRightPane. |
| `platform/src/components/build/MirrorPairsTable.tsx` | Used by BuildRightPane. |
| `platform/src/components/build/PyramidStatusPanel.tsx` | Referenced by build components. |
| `platform/src/components/build/JourneyStrip.tsx` | Referenced in chart_pages.test.tsx mock — active. |
| `platform/src/components/build/ActivityFeed.tsx` | Build cockpit component — active. |
| `platform/src/components/build/CockpitGrid.tsx` | Build cockpit component — active. |
| `platform/src/components/build/SessionTimeline.tsx` | Build cockpit component — active. |
| `platform/src/components/build/SessionTable.tsx` | Build cockpit component — active. |
| `platform/src/components/build/RegistryTable.tsx` | Build cockpit component — active. |
| `platform/src/components/build/RegistryGrouped.tsx` | Build cockpit component — active. |
| `platform/src/components/build/PlanTree.tsx` | Build cockpit component — active. |
| `platform/src/components/build/colors.ts` | Shared color constants for build components. |
| `platform/src/components/build/StatusPill.tsx` | Shared build component. |
| `platform/src/components/build/ProgressBar.tsx` | Shared build component. |
| `platform/src/components/build/HealthSparkline.tsx` | Shared build component. |
| `platform/src/components/build/HealthTrend.tsx` | Shared build component. |
| `platform/src/components/build/CorpusDensityHero.tsx` | Build cockpit component. |
| `platform/src/components/build/BuildHeader.tsx` | Build cockpit component. |
| `platform/src/components/build/BuildVelocityStrip.tsx` | Build cockpit component. |
| `platform/src/components/build/DetailSidePanel.tsx` | Build cockpit component. |
| `platform/src/components/build/SessionDetail.tsx` | Build cockpit component. |
| `platform/src/components/build/FilterableActivityFeed.tsx` | Build cockpit component. |
| `platform/src/components/build/InterventionFrequency.tsx` | Build cockpit component. |
| `platform/src/components/build/InterventionList.tsx` | Build cockpit component. |
| `platform/src/components/build/FreshnessIndicator.tsx` | Build cockpit component. |
| `platform/src/components/build/RefreshButton.tsx` | Build cockpit component. |
| `platform/src/components/build/AcCriteriaList.tsx` | Build cockpit component. |
| `platform/src/components/build/ScriptVerdictBadge.tsx` | Build cockpit component. |
| `platform/src/components/build/ActiveChartsWidget.tsx` | Build cockpit component. |
| `platform/src/components/build/charts/SessionsBar.tsx` | Build chart sub-component. |
| `platform/src/components/build/charts/CadenceArea.tsx` | Build chart sub-component. |
| `platform/src/components/build/charts/OnOffPlanDonut.tsx` | Build chart sub-component. |
| `platform/src/components/build/charts/TrendLine.tsx` | Build chart sub-component. |
| `platform/src/app/clients/[id]/build/layout.tsx` | Build page layout — active. |
| `platform/src/app/clients/[id]/build/error.tsx` | Build page error boundary — active. |

## Scope Compliance

- MUST NOT TOUCH: `platform/python-sidecar/**`, `platform/migrations/**`, streams A/B/C/D/E/G1-G4/I/J` — NONE TOUCHED.
- All changes confined to: `platform/src/components/build/BuildChat.tsx` (deleted), `platform/src/app/clients/[id]/build/BuildActionPanel.tsx` (deleted), `platform/src/app/clients/[id]/build/__tests__/BuildActionPanel.test.tsx` (deleted), `platform/src/app/clients/[id]/build/page.tsx` (modified), `platform/src/app/clients/[id]/build/[conversationId]/page.tsx` (modified), `platform/src/app/clients/__tests__/chart_pages.test.tsx` (mock updated), `platform/src/components/build_orchestrator/` (new directory + scaffold files).
