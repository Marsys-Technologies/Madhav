---
artifact: CO7_NATIVE_ACCEPTANCE.md
version: 1.0
status: OPEN
authored_at: 2026-05-14
session_id: AIOPS_CO_7
phase: Phase 3 — Consume UI Overhaul (CO.0 → CO.7)
reviewer: Abhisek Mohanty (native)
---

# CO.7 Native Acceptance — AIOps Phase 3

Pre-merge checklist for the native reviewer. 12 items.

---

## §1 — Setup

```bash
# Ensure you are on the feature branch
git checkout feature/aiops-phase-3-consume-ui

# Start dev server with flag ON
CONSUME_UI_V2_ENABLED=true npm run dev

# For flag-OFF comparison
CONSUME_UI_V2_ENABLED=false npm run dev
```

---

## §2 — Checklist

### Core bug fixes

- [ ] **Bug 3.3 — Reasoning slot placement**
  Visit `/consume`. Submit a query to a reasoning model (Gemini 2.5 Pro or
  DeepSeek R1). Confirm the reasoning slot appears immediately at submission —
  not after the stream finishes. No layout jump (CLS) when reasoning text
  arrives.

- [ ] **Bug 3.1 — Input panel cleanup + per-message metadata**
  After a completed response, the input panel above the composer does NOT show
  the model name (e.g. "Gemini 2.5 Pro"). Instead, a compact badge appears
  below the assistant message showing model + latency. Click the badge to
  expand token counts.

- [ ] **Bug 3.2 — Sidebar hover-expand + click-to-pin**
  On desktop (≥ 640px):
  - Sidebar starts collapsed (icon-only strip, `w-14`).
  - Hover the left edge → sidebar expands to `w-64` with conversation list.
  - Click the pin button (📌) → sidebar stays expanded even when mouse leaves.
  - Click pin again → sidebar collapses back.
  - Refresh page → pin state persists (localStorage).

- [ ] **Bug 3.4 — Reasoning slot absent for non-reasoning models**
  Submit a query via NIM stack (Nemotron or another non-reasoning model).
  Confirm the reasoning slot does NOT appear at all. Only appears for models
  with `reasoning_via: 'native'` or `'markers'`.

### Visual + behavioral

- [ ] **CLS < 0.05**
  In Chrome DevTools → Performance → record a submit + response cycle.
  Confirm CLS metric < 0.05 in the "Experience" section. (Or use Lighthouse:
  `Cmd+Shift+P → "Generate Lighthouse report"` on `/consume`.)

- [ ] **Mobile viewport (375×667)**
  Chrome DevTools → Toggle device toolbar → iPhone SE / 375×667:
  - Sidebar collapses to overlay mode (not visible by default, hamburger toggle shows).
  - Composer is sticky at the bottom of the viewport.
  - No horizontal scroll bar.
  - Reasoning slot collapses to one-line summary; tap to expand.

- [ ] **Keyboard shortcuts**
  From `/consume` with focus NOT in the composer:
  - `Cmd+K` (Mac) / `Ctrl+K` (Windows): focus jumps to composer textarea.
  - `Esc`: collapses any expanded panels; focus returns to composer.
  - `Cmd+/` / `Ctrl+/`: shortcuts help overlay appears.
  - `Cmd+Enter` / `Ctrl+Enter` from within the textarea: submits the form.

- [ ] **Mid-stream "Stop generating"**
  Submit a long-running reasoning query. While the response is streaming:
  - A "Stop generating" button is visible near the message.
  - Clicking it cancels the stream (partial output frozen).
  - A "Regenerate" button appears for re-submission.

### Parity + regression

- [ ] **Flag-off equivalence**
  Start dev server with `CONSUME_UI_V2_ENABLED=false`. Confirm `/consume`
  renders the legacy components (StreamingAnswer, LiveReasoningCard) and
  behavior is identical to the pre-Phase-3 baseline.

### Audit sign-off

- [ ] **A11y audit (CO.6)**
  Read `00_ARCHITECTURE/aiops/phase_3/CO6_A11Y_AUDIT.md`.
  Confirm `OUTSTANDING: 0`. Sign off that the two documented deferrals
  (touch target + supplemental text contrast) are acceptable for this release.

- [ ] **Visual audit (CO.5)**
  Read `00_ARCHITECTURE/aiops/phase_3/CO5_VISUAL_AUDIT.md`.
  Confirm typography ≤ 6 sizes, motion tiers consolidated, no hardcoded
  brand colors remaining.

### Post-merge monitoring

- [ ] **Observatory cost + latency — 1-hour window**
  After merge + deploy, confirm no /consume regressions in Cloud Run metrics
  or Observatory dashboard for 1 hour. Expected: latency unchanged (no server
  work added); cost unchanged (same models, same token budgets).

---

## §3 — Sign-off

When all 12 items are checked:

1. Merge `feature/aiops-phase-3-consume-ui` → `main`.
2. Monitor Cloud Run for 48 hours.
3. Schedule flag-removal PRs for 2 weeks post-merge:
   - Remove `CONSUME_UI_V2_ENABLED` from `feature_flags.ts` + `deploy.yml`.
   - Delete legacy flag-OFF code paths in `ConsumeChat.tsx`.
   - Archive `LiveReasoningCard.tsx` (or delete; already carries "LEGACY" comment).

---

## §4 — Rollback

If a production defect is found after merge + deploy:

```bash
# Remove flag via gcloud — no code revert needed
gcloud run services update amjis-web \
  --region asia-south1 \
  --remove-env-vars CONSUME_UI_V2_ENABLED
```

This immediately reverts to the legacy path. No redeploy needed.

---

*End of CO7_NATIVE_ACCEPTANCE.md v1.0*
*AIOps Phase 3 — 8 sub-phases, CO.0 → CO.7.*
