---
status: OPEN
session_id: AIOPS_CP_0
phase: CP.0
phase_name: "Branch + IA shell + stub routes"
next_session: AIOPS_CP_1
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_0
## AIOps Phase 1, Step 0 — Branch + IA shell + stub routes

---

## §0 — Executor orientation

You are executing CP.0 of AIOps Phase 1 (Control Panel). This is the first
of six sequential phases. Master plan: `00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md`.
Execution rules: `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md` — read
in full before starting.

**This phase is plumbing.** It establishes the branch, the route shell, the
empty stub pages, and the directory structure. No DB, no real UI yet — that
lands in CP.1 and CP.2.

**Execution vehicle:** new branch `feature/aiops-control-panel` cut from `main`.

---

## §1 — Mandatory reads (in order)

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  platform/src/lib/models/registry.ts  (STACK_ROUTING, CallType, ModelStack)
5.  platform/src/app/(super-admin)/observatory/page.tsx  (existing Observatory shell for reference)
6.  platform/src/app/api/admin/observatory/_guard.ts  (auth pattern to mirror)
```

---

## §2 — Scope

### may_touch
```
platform/src/app/(super-admin)/aiops/**
platform/src/app/observatory/**            # only to add a redirect alias
platform/src/lib/aiops/**                  # create the directory + index.ts
platform/src/lib/components/aiops/**       # create the directory + AuthGate copy
00_ARCHITECTURE/aiops/**                   # update if needed
CLAUDECODE_BRIEF.md                        # rotate at close
```

### must_not_touch
```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
platform/src/lib/models/**                 # CP.1 territory
platform/src/lib/components/observatory/** # untouched in CP.0
platform/src/app/api/admin/observatory/**
00_ARCHITECTURE/MACRO_PLAN_v2_0.md
00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md
```

---

## §3 — Work plan

Execute in order.

### 3.1 — Branch creation

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main
git pull --ff-only
git checkout -b feature/aiops-control-panel
```

Confirm branch:
```bash
git branch --show-current   # expect: feature/aiops-control-panel
```

### 3.2 — Route shell

Create the AIOps shell. The shell is a thin wrapper that hosts two tabs:
`/aiops/control` and `/aiops/observatory`. The existing Observatory page
remains reachable at `/observatory` (alias kept for bookmark compatibility).

Files to create:

- `platform/src/app/(super-admin)/aiops/layout.tsx`
  Layout component with a top tab strip (Control Panel | Observatory) and
  the existing super-admin auth gate. Tab strip is built from the existing
  `AuthGate` + a new `<AiopsTabs />` component.

- `platform/src/app/(super-admin)/aiops/page.tsx`
  Default redirect to `/aiops/control`.

- `platform/src/app/(super-admin)/aiops/control/page.tsx`
  Stub: renders a single heading "AIOps Control Panel — CP.0 stub" and a
  paragraph "Configuration UI lands in CP.2." Use the same dark-theme
  wrapper components as the Observatory page.

- `platform/src/app/(super-admin)/aiops/observatory/page.tsx`
  Re-exports the existing Observatory page (default-export the same
  component as `platform/src/app/(super-admin)/observatory/page.tsx`).
  This makes `/aiops/observatory` and `/observatory` render identically.

### 3.3 — Component scaffold

Create:

- `platform/src/lib/components/aiops/AuthGate.tsx`
  Copy of `platform/src/lib/components/observatory/AuthGate.tsx`, renamed.
  Same super-admin check.

- `platform/src/lib/components/aiops/AiopsTabs.tsx`
  Two-tab horizontal strip. Tabs: "Control Panel" (link to `/aiops/control`)
  and "Observatory" (link to `/aiops/observatory`). Active-tab state derived
  from pathname.

- `platform/src/lib/components/aiops/index.ts`
  Barrel exporting both.

### 3.4 — Service scaffold

Create:

- `platform/src/lib/aiops/index.ts` — empty barrel for CP.1 imports.
- `platform/src/lib/aiops/types.ts` — declare the placeholder types that CP.1
  will populate:
  ```ts
  export type {} from '../models/registry'  // re-export anchor; expanded in CP.1
  ```

### 3.5 — Smoke test

```bash
cd platform
npm run typecheck   # must pass
npm run lint        # must pass
npm run dev         # spin up; visit http://localhost:3000/aiops in a browser

# Manual visual check (logged at session-close as a note):
#   /aiops               redirects to /aiops/control
#   /aiops/control       renders "AIOps Control Panel — CP.0 stub"
#   /aiops/observatory   renders the existing Observatory
#   /observatory         renders the existing Observatory (unchanged)
```

The dev server confirmation is a courtesy — automated ACs below cover the
contract.

---

## §4 — Acceptance criteria

| AC | Check command | Pass condition |
|---|---|---|
| AC.CP0.1 | `git branch --show-current` | Output is `feature/aiops-control-panel` |
| AC.CP0.2 | `test -f platform/src/app/(super-admin)/aiops/layout.tsx` | exit 0 |
| AC.CP0.3 | `test -f platform/src/app/(super-admin)/aiops/page.tsx` | exit 0 |
| AC.CP0.4 | `test -f platform/src/app/(super-admin)/aiops/control/page.tsx` | exit 0 |
| AC.CP0.5 | `test -f platform/src/app/(super-admin)/aiops/observatory/page.tsx` | exit 0 |
| AC.CP0.6 | `test -f platform/src/lib/components/aiops/AuthGate.tsx` | exit 0 |
| AC.CP0.7 | `test -f platform/src/lib/components/aiops/AiopsTabs.tsx` | exit 0 |
| AC.CP0.8 | `test -f platform/src/lib/aiops/index.ts` | exit 0 |
| AC.CP0.9 | `cd platform && npm run typecheck` | exit 0 |
| AC.CP0.10 | `cd platform && npm run lint` | exit 0 |
| AC.CP0.11 | `cd platform && npm run test -- --run` | exit 0 (no regressions) |
| AC.CP0.12 | scope-violation grep (see §5) | no violations |

---

## §5 — Scope-violation grep

Before the final commit, run:
```bash
git diff --name-only main \
  | grep -vE '^(platform/src/app/\(super-admin\)/aiops/|platform/src/lib/(aiops|components/aiops)/|platform/src/app/observatory/|00_ARCHITECTURE/aiops/|CLAUDECODE_BRIEF\.md$)' \
  || echo "SCOPE_OK"
```

Expected output: `SCOPE_OK`. Any other output is a violation — abort the
commit, BAIL OUT per R6.

---

## §6 — Session close

After all ACs pass:

1. Stage all changes:
   ```bash
   git add platform/src/app/\(super-admin\)/aiops/ \
           platform/src/lib/aiops/ \
           platform/src/lib/components/aiops/ \
           platform/src/app/observatory/ \
           00_ARCHITECTURE/aiops/
   ```

2. Rotate `CLAUDECODE_BRIEF.md`:
   ```bash
   cp 00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_1_BRIEF.md CLAUDECODE_BRIEF.md
   git add CLAUDECODE_BRIEF.md
   ```

3. Commit:
   ```bash
   git commit -m "feat(aiops-CP.0): branch + IA shell + stub routes

   - new branch feature/aiops-control-panel cut from main
   - new shell at /aiops with two child routes (/aiops/control, /aiops/observatory)
   - /observatory preserved as alias (existing Observatory unchanged)
   - new component dir platform/src/lib/components/aiops/ (AuthGate, AiopsTabs)
   - new service dir platform/src/lib/aiops/ (index + types stubs)
   - CLAUDECODE_BRIEF rotated to AIOPS_CP_1

   AC summary: 12/12 PASS, 0 DEFERRED, 0 FAIL"
   ```

4. Report:
   ```
   [AIOPS-CLOSE] phase=CP.0 status=CLOSED next_phase=CP.1
   ```

---

## §7 — BAIL OUT triggers (CP.0 specific)

- `git checkout -b` fails because the branch already exists with divergent commits.
- Existing Observatory page has been moved/renamed — the alias setup needs different paths.
- `npm run typecheck` or `npm run lint` fails on the new stubs.

In any of these cases, follow R6 (write BAIL_OUT block, halt, exit non-zero).

---

*End of PHASE_CP_0_BRIEF.md*
