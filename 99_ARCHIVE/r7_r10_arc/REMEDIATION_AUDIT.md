---
artifact: REMEDIATION_AUDIT.md
version: 1.0
status: COMPLETE
produced_during: chat-v2/r9-integration-remediation
produced_on: 2026-05-20
---

# R9 Integration Gap Remediation Audit

## Methodology

Read STREAM_R9_COMPLETE.md and FINAL_MERGE_TRAIN_REPORT.md for claimed state,
then verified each claim against the actual files on disk (main branch as of 2026-05-20).

---

## R9-S1 — Projects Abstraction

### API Layer
- `platform/src/app/api/projects/route.ts` — **EXISTS** (GET list + POST create)
- `platform/src/app/api/projects/[id]/route.ts` — **EXISTS** (GET detail + PATCH + DELETE)
- Migrations 110 applied in production (confirmed by operator close-out, S174)

### UI Components
- `platform/src/components/sidebar/ProjectsSection.tsx` — **EXISTS**
- `platform/src/components/sidebar/ProjectBadge.tsx` — **EXISTS**
- `platform/src/components/modals/NewProjectModal.tsx` — **EXISTS**

### Mounting
- `ConversationSidebarV2.tsx` imports `ProjectsSection` and `NewProjectModal` (lines 32–33)
  and renders `<ProjectsSection ...>` when `showProjects=true` (lines 509–521)
- `ConsumeChatV2.tsx` passes:
  ```tsx
  showProjects={process.env.NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS === 'true'}
  ```
  to `ConversationSidebarV2` (line 1609)

### **Gap Identified: `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS` not in build pipeline**

The client-side `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS` env var is absent from:
- `.github/workflows/deploy.yml` → `build-args` section (where NEXT_PUBLIC_ Firebase vars ARE listed)
- `platform/.env.local` (local dev)

Next.js bakes `NEXT_PUBLIC_*` vars at `next build` time into the client bundle. The server-side
`MARSYS_FLAG_R9_PROJECTS=true` that was set via `gcloud run services update` post-deploy does NOT
reach client components. So `showProjects` evaluates `false` in production and locally.

**Status: EXISTS-BUT-NOT-MOUNTED** (env var gap in deploy pipeline)

### Fix
Add `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS=true` to:
1. `deploy.yml` `build-args` block
2. `platform/.env.local`

---

## R9-S3 — Persona Library

### API Layer
- `platform/src/app/api/personas/route.ts` — **EXISTS** (GET list + POST create)
- `platform/src/app/api/personas/[id]/route.ts` — **EXISTS** (PATCH + DELETE)
- `platform/src/app/settings/personas/page.tsx` — **EXISTS** (verified working on production)
- Migration 111 applied in production (confirmed by operator close-out, S174)
- `/api/chat/consume/route.ts` reads `body.persona_id` (line 172–173) and calls
  `getPersonaForSynthesis` when `MARSYS_FLAG_R9_PERSONAS=true` (line 812–820) — **EXISTS**

### UI Components
- `platform/src/components/chat/ModelStylePicker.tsx` — **EXISTS** with full persona code:
  - Imports `usePersonas` hook (line 19)
  - Accepts `activePersonaId?: string | null` and `onPersonaChange?: (id: string | null) => void` props (lines 60–63)
  - Renders persona `DropdownMenuGroup` when `showPersonas && onPersonaChange` (line 96)
- `platform/src/hooks/usePersonas.ts` — **EXISTS**

### **Gap Identified: Persona props not threaded from context to picker**

`V2BottomBar` (the sub-component in ConsumeChatV2.tsx that renders `ModelStylePicker`) reads
from `V2PrefsCtx` (line 1314–1315), but:

1. `V2PrefsCtxValue` interface does NOT include `activePersonaId` or `setActivePersonaId`
2. `ModelStylePicker` is called WITHOUT `activePersonaId` or `onPersonaChange` props (lines 1322–1327)
3. Because `onPersonaChange` is undefined, the persona section NEVER renders
   (ModelStylePicker guards with `{showPersonas && onPersonaChange && ...}`)
4. The `runtime.body()` function (line 1815–1835) does NOT include `persona_id`
   in the payload, so synthesis never receives a persona even if the picker were wired

**Status: EXISTS-BUT-NOT-MOUNTED** (props not threaded through context and runtime body)

### Fix
Three-point fix in `ConsumeChatV2.tsx`:
1. Add `activePersonaId: string | null` + `setActivePersonaId` to `V2PrefsCtxValue`
2. Add `useState<string | null>(null)` for persona in the main render function
3. Include in `prefsCtxValue` and thread to `ModelStylePicker` in `V2BottomBar`
4. Add `...(activePersonaIdRef.current ? { persona_id: activePersonaIdRef.current } : {})` to runtime body

---

## R9-S4 — Inline Tool Flow Timeline

### API Layer
- `platform/src/app/api/audit/[query_id]/trace/route.ts` — **EXISTS**
  (reads `query_trace_steps` filtered by `query_id`, auth-gated to super_admin)

### UI Component
- `platform/src/components/chat/InlineToolFlow.tsx` — **EXISTS**
  - Fetches `/api/audit/${queryId}/trace` on expand
  - Caches per queryId with `useRef<Map>`
  - Props: `{ queryId: string | null; isAdmin: boolean }`
  - Guards on `FLAG_ON || !isAdmin || !queryId` (line 69)
  - `FLAG_ON = process.env.NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW === 'true'`

### Mounting
- `platform/src/components/chat/AssistantMessage.tsx` — **CORRECTLY MOUNTED**
  - Imports `InlineToolFlow` (line 12)
  - Derives `queryId = (meta.query_id ?? meta.queryId) as string | undefined` (line 92)
  - Derives `isAdmin = tier === 'super_admin' || tier === 'acharya_reviewer'` (line 93)
  - Renders `<InlineToolFlow queryId={queryId ?? null} isAdmin={isAdmin} />` (line 218)

### **Gap Identified: `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW` not in build pipeline**

Same pattern as R9-S1. `FLAG_ON` evaluates `false` because the var is not baked into
the Next.js client bundle at build time. The server-side flag flip had no effect on the
client bundle — `InlineToolFlow` renders `null` for all users.

**Status: EXISTS-BUT-NOT-MOUNTED** (env var gap in deploy pipeline)

### Fix
Add `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW=true` to:
1. `deploy.yml` `build-args` block
2. `platform/.env.local`

---

## Hard Halt Assessment

No backend APIs are missing. All three features have shipped backend code. The gaps are:
- **R9-S3**: Code gap — props not threaded (fixable in this session)
- **R9-S1, R9-S4**: Deploy pipeline gap — NEXT_PUBLIC_ vars missing from `build-args` (fixable in this session)

**No hard halt triggered.**

---

## Feedback Candidate

> Autonomous stream completion claims must include "is NEXT_PUBLIC_ build-arg set in deploy.yml?"
> as a verifiable AC for any feature that uses `process.env.NEXT_PUBLIC_*` in client components,
> not just "does the file exist" or "does the server-side flag exist."
>
> Additionally: "is the prop being passed from the context/parent component?" must be a verifiable
> AC for any component that conditionally renders based on an optional prop.
