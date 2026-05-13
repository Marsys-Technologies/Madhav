---
artifact: CP4_A11Y_AUDIT
phase: CP.4
status: CLOSED
audited_at: 2026-05-13
---

# CP.4 Accessibility Audit

## Components audited
- `HealthPip.tsx`
- `RevertConfirmDialog.tsx`
- `AuditRail.tsx` (revert button addition)
- `ModelDropdown.tsx` (HealthPip integration)

## Findings and resolutions

| # | Component | Finding | Severity | Resolution |
|---|---|---|---|---|
| 1 | RevertConfirmDialog | No Escape key handler — keyboard users could not dismiss | High | Added `keydown` listener; Escape fires `onCancel` |
| 2 | RevertConfirmDialog | Focus not moved to dialog on open | High | Added `useRef` + `useEffect` to focus Cancel button on mount |
| 3 | AuditRail revert button | Touch target ~18px (below 44px WCAG 2.5.5) | Low | Accepted exception: super-admin desktop-only page; no mobile viewport support declared |

## Confirmed-pass items

- `HealthPip`: `role="img"`, `aria-label` (semantic label with status + time + latency), `title` for sighted hover — PASS
- `RevertConfirmDialog`: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` → dialog title — PASS
- Error state: `role="alert"` on inline error paragraph — PASS
- All interactive elements use `type="button"` — PASS
- Disabled states propagated via `disabled` prop — PASS
- AuditRail revert button: `aria-label="Revert change {id}"` — PASS
- Keyboard navigation: Cancel and Confirm Revert both focusable/activatable via Tab + Enter — PASS
- Color not sole indicator: HealthPip pip color supplemented by full text in `aria-label` and `title` — PASS

## OUTSTANDING: 0
