---
status: OPEN
session_id: AIOPS_CP_4
phase: CP.4
phase_name: "Health badges + audit revert + accessibility + brand polish"
next_session: AIOPS_CP_5
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_4
## AIOps Phase 1, Step 4 — Polish, audit, accessibility

---

## §0 — Executor orientation

CP.4 is the polish phase. After CP.3 the system works end-to-end under
either flag state. CP.4 adds:

1. Health probe cron + visible badges on every model row everywhere.
2. Functional revert from the Recent Changes right rail.
3. Accessibility audit (WCAG 2.1 AA).
4. Brand audit (no new colors, fonts, or design primitives introduced).
5. Visual regression confirmation.

No new endpoints other than `POST /audit/[id]/revert`. No new data tables.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md §6, §13
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  platform/src/lib/components/aiops/ModelDropdown.tsx        (CP.2 deliverable)
5.  platform/src/lib/components/aiops/StackPickerCards.tsx     (CP.2 deliverable)
6.  /var/folders/.../skills/design-accessibility-review/SKILL.md
7.  /var/folders/.../skills/brand-guidelines/SKILL.md
```

(Use the `design:accessibility-review` and `brand-guidelines` skills as
reference checklists for this phase.)

---

## §2 — Scope

### may_touch
```
platform/src/lib/aiops/health/**                        # NEW: probe cron + helpers
platform/src/app/api/admin/aiops/health/route.ts        # GET + manual trigger
platform/src/app/api/admin/aiops/audit/[id]/revert/route.ts  # NEW
platform/src/lib/components/aiops/**                    # add HealthPip, RevertConfirmDialog
platform/src/app/(super-admin)/aiops/control/page.tsx   # wire revert
platform/scripts/aiops/probe_health_cron.ts             # NEW (nightly cron entry point)
CLAUDECODE_BRIEF.md
```

### must_not_touch
(Same as CP.3. Specifically: do not change any AC from CP.2 or CP.3 — those
are locked.)

---

## §3 — Work plan

### 3.1 — Health probe service

Create `platform/src/lib/aiops/health/`:

- `prober.ts` — `probeModel(modelId): Promise<HealthResult>`. Internally
  uses the existing `runProbe()` from CP.2 with a minimal payload (uses
  the `worker` call type's prompt as the universal small probe).
- `bulk.ts` — `probeAllModels(): Promise<HealthReport>` — probes every
  model present in the catalog snapshots (`llm_catalog_snapshot`) plus
  every model_id in the registry.
- Writes results to `llm_model_health` (single row per model_id; UPSERT).

### 3.2 — Health cron entry point

Create `platform/scripts/aiops/probe_health_cron.ts`:

```ts
#!/usr/bin/env node
import { probeAllModels } from '@/lib/aiops/health/bulk'

const r = await probeAllModels()
console.log(`[AIOPS-HEALTH] probed=${r.total} pass=${r.pass} fail=${r.fail}`)
process.exit(0)
```

Add an npm script: `"aiops:health": "tsx scripts/aiops/probe_health_cron.ts"`.

The actual cron registration in production happens by native via Cloud
Scheduler — outside this brief. Native is informed at the close of CP.5.

### 3.3 — Health API

`GET /api/admin/aiops/health?model_id=<optional>` — returns the health
table, filtered if `model_id` is given.

`POST /api/admin/aiops/health/probe?model_id=<id>` — manual one-off
probe trigger.

### 3.4 — HealthPip component

`platform/src/lib/components/aiops/HealthPip.tsx`:
- Small inline dot with tooltip on hover.
- Colors:
  - green: last_probe ≤ 24h ago, status=pass
  - yellow: last_probe ≤ 7d ago, status=pass
  - red: status=fail
  - gray: never probed
- Tooltip: "Last probe: <time ago>. Latency: <ms>. Cost: $<cost>."

Render HealthPip:
- In every ModelDropdown row.
- In every CallTypeRow primary + fallback display.
- On the Recent Changes right rail next to model_id entries.

### 3.5 — Revert functionality

`POST /api/admin/aiops/audit/[id]/revert` — reads the audit row, applies the
inverse operation:
- `set_stack` → set stack back to `before_value.active_stack`
- `set_routing` → set routing back to before
- `set_param` → set param back to before
- `reset_param` → re-apply the previous value
- Writes a *new* audit row with `action='revert'` and `notes='reverted audit
  id <N>'`. (Revert is itself an auditable event.)

Component `RevertConfirmDialog.tsx`:
- Modal showing "Revert this change?" with before/after values diffed.
- On confirm → POST to the revert endpoint → toast on success / failure.

### 3.6 — Accessibility audit

Run the `design:accessibility-review` skill against the Control Panel
(read its SKILL.md, then run its checks). Specifically:

1. Color contrast: every text vs background ≥ 4.5:1 for body, ≥ 3:1 for
   large text (≥18pt or ≥14pt bold).
2. Keyboard nav: every interactive element reachable via Tab; visible focus
   ring on every focused element.
3. ARIA: dropdowns have `aria-expanded`, `aria-haspopup`, `role='listbox'`;
   tab strip has `role='tablist'` + `role='tab'` + `aria-selected`.
4. Touch targets: every clickable ≥ 44×44 px.
5. Screen reader: every icon has an accessible label.

Fix every issue found. Capture the before/after report at
`00_ARCHITECTURE/aiops/CP4_A11Y_AUDIT.md`.

### 3.7 — Brand audit

Run the `brand-guidelines` skill. Confirm:

1. No new colors introduced — every color must come from existing Tailwind
   tokens or the dark theme CSS variables.
2. No new fonts — same typography stack as Observatory.
3. No new icon library — reuse whatever the Observatory uses.
4. Spacing scale consistent with Observatory.

Capture the audit at `00_ARCHITECTURE/aiops/CP4_BRAND_AUDIT.md`.

### 3.8 — Visual regression

Manual confirmation (logged in commit body): take screenshots of
- `/aiops/control` (each of 6 stacks)
- `/observatory` (unchanged from main)
- The CostConfirmDialog modal
- The TestProbeInline expanded panel
- The RevertConfirmDialog modal

Save under `00_ARCHITECTURE/aiops/CP4_SCREENSHOTS/` (gitignored after
review). Confirm visual coherence with the existing Observatory aesthetic.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CP4.1 | Health endpoints exist + tested | ≥6 endpoint cases |
| AC.CP4.2 | HealthPip renders in every ModelDropdown row | snapshot test |
| AC.CP4.3 | Health cron script runs end-to-end on dev | `npm run aiops:health` exits 0 |
| AC.CP4.4 | Revert endpoint inverts each action type | ≥5 cases (one per action) |
| AC.CP4.5 | Revert dialog opens + submits + toasts | UI test |
| AC.CP4.6 | A11Y audit report exists with 0 outstanding issues | `grep "OUTSTANDING: 0" 00_ARCHITECTURE/aiops/CP4_A11Y_AUDIT.md` |
| AC.CP4.7 | Brand audit report exists with 0 violations | `grep "VIOLATIONS: 0" 00_ARCHITECTURE/aiops/CP4_BRAND_AUDIT.md` |
| AC.CP4.8 | Color contrast automated check passes | `npx pa11y http://localhost:3000/aiops/control` exits 0 OR equivalent |
| AC.CP4.9 | `npm run typecheck` | exit 0 |
| AC.CP4.10 | `npm run lint` | exit 0 |
| AC.CP4.11 | Full test suite green | exit 0 |
| AC.CP4.12 | scope-violation grep | SCOPE_OK |

---

## §5 — Test minimums

- Health prober: ≥6 tests.
- Revert endpoint: ≥5 tests (one per action).
- HealthPip component: ≥4 tests.
- A11Y assertions in component tests: every interactive element asserts
  `aria-*` + focus ring + tab-reachable.

Total ≥ 30 new tests.

---

## §6 — Session close

Final commit `feat(aiops-CP.4): health badges + audit revert + a11y + brand polish`.
Rotate CLAUDECODE_BRIEF.md → PHASE_CP_5_BRIEF.md.

---

## §7 — BAIL OUT triggers (CP.4 specific)

- Accessibility issue cannot be fixed without changing brand tokens (e.g.,
  required contrast can't be achieved with current palette).
- Health prober reveals systemic provider failures (≥3 providers down) —
  catalog won't populate; bulk probe fails; BAIL OUT to let native fix
  provider credentials.

---

*End of PHASE_CP_4_BRIEF.md*
