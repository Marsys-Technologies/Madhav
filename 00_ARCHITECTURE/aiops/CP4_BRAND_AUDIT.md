---
artifact: CP4_BRAND_AUDIT
phase: CP.4
status: CLOSED
audited_at: 2026-05-13
---

# CP.4 Brand Audit

## Components audited
- `HealthPip.tsx`
- `RevertConfirmDialog.tsx`
- `AuditRail.tsx` (revert button addition)
- `ModelDropdown.tsx` (HealthPip wiring)
- `probe_health_cron.ts` (no UI)

## Findings and resolutions

**No violations found.**

## Confirmed-pass items

### Colors
- HealthPip uses inline style with dynamic hex values `#ef4444` (red-500), `#22c55e` (green-500), `#eab308` (yellow-500), `#6b7280` (gray-500) — all are Tailwind palette equivalents. Inline style required for runtime `boxShadow` with alpha. Observatory precedent: `#ef4444` used in `observatory/charts/utils.ts`.
- All other color usage is via Tailwind semantic tokens (`text-foreground`, `text-muted-foreground`, `bg-card`, `bg-muted`, `border-border`, `text-red-400`, `bg-red-500/10`) — identical to Observatory and existing AIOps components.

### Typography
- No new font families introduced. Monospace (`font-mono`) and sans (`font-sans` default) match Observatory pattern.

### Icons / symbols
- `↩` (U+21A9 LEFTWARDS ARROW WITH HOOK) — consistent with Unicode symbol approach used elsewhere (↻ in ModelDropdown, ✏ in StackBreakdownCards).
- No icon library imports added.

### Spacing / sizing
- All sizing uses Tailwind scale tokens (px, py, gap, rounded) — no arbitrary values outside existing project patterns.

## VIOLATIONS: 0
