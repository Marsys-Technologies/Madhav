---
brief_id: EXEC_BRIEF_PHASE_11A_INVESTIGATION
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_11A_INVESTIGATION_v1_0.md and execute it."
phase: 11A.investigate
phase_name: Phase 11A — Diagnose Legacy-UI Render at /clients/[clientId]/consume
risk_classification: LOW (read-only investigation)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_11A_v1_0.md (COMPLETE)]
estimated_streams: 5
output_artifact: platform/scripts/cutover/stage1_diagnosis.md
---

# EXEC_BRIEF — Phase 11A Investigation — Why Is Legacy UI Rendering?

## Mission

Native reports that visiting `http://localhost:3001/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume` after Phase 11A's flag flip is rendering the **legacy UI**, not the new pipeline UI (no `<StreamingAnswer />`, no `<CitationChip />`, no `<DisclosureTierBadge />`). Either the flag default flip didn't propagate to runtime, or the per-client consume page surface was missed in Phase 5's UI integration.

This brief is a **read-only diagnostic pass**. The output is a single markdown report that identifies the root cause and proposes — but does NOT execute — the remediation. A separate follow-up brief will execute the fix once native has reviewed the diagnosis.

## Scope

**`may_touch`:**
- `platform/scripts/cutover/stage1_diagnosis.md` (new — the report this brief produces)

**`must_not_touch`:**
- Every other file in the repo. This is read-only investigation.
- No code changes. No test changes. No config changes. No env changes. No restarts.
- If during investigation a fix becomes obvious (e.g., a one-line missing prop pass-through), DO NOT apply it. Document it in the report and let native decide.

## Investigation streams (5 total, sequential)

### Stream A — Environment audit

Determine what feature flag values are actually evaluated when the dev server renders a consume page.

1. Open `platform/src/lib/config/feature_flags.ts`. Read the current default for `NEW_QUERY_PIPELINE_ENABLED` and `AUDIT_ENABLED`. Confirm both defaults are `true` post-Phase-11A.
2. Identify the **exact environment variable names** the file reads from `process.env`. Common patterns are `NEW_QUERY_PIPELINE_ENABLED`, `MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED`, `NEXT_PUBLIC_NEW_QUERY_PIPELINE_ENABLED`, etc. Note them exactly.
3. Check `platform/.env.local` (if it exists). If the file exists, list every line that mentions any of the two flags. If a line sets either flag to `false`, note it — that's the smoking gun for Cause #1.
4. Check `platform/.env`, `platform/.env.development`, and any other `.env*` files in `platform/`. Same audit.
5. Check root-level `.env*` files at `/Users/Dev/Vibe-Coding/Apps/Madhav/` (one level above platform/). If anything mentions the flags, note it.
6. **Do NOT modify any env file.**

Stream A output: a section in the diagnosis report titled "Environment Audit" listing what env vars are read by code, what env files set them, and what value would resolve at runtime.

### Stream B — Consume page surface map

Find every page route under `platform/src/app/` that renders a Consume-tab UI.

1. Run `find platform/src/app -name "page.tsx" -path "*consume*"` to enumerate consume page files.
2. Also check for layout files that might wrap consume routes: `find platform/src/app -name "layout.tsx" -path "*consume*"` and `find platform/src/app -name "layout.tsx" -path "*clients*"`.
3. For each page file found, capture: full path, line count, top of file (first 30 lines for imports + types), the JSX it renders, and which client/server boundary it sits on (does it have `"use client"` at the top?).
4. Specifically verify these two are present and read each one:
   - `platform/src/app/consume/page.tsx` (root consume — Phase 5 explicitly named this)
   - `platform/src/app/clients/[clientId]/consume/page.tsx` (per-client consume — the URL native is on)
5. If there are MORE than these two consume pages, note all of them.

Stream B output: a section "Consume Page Surface Map" listing every consume page route in the app with its file path and a one-paragraph description of what it does.

### Stream C — Render tree audit

For each consume page found in Stream B, trace the prop chain from server-side flag fetch all the way to `ConsumeChat`'s rendering decision.

1. For each consume page, answer:
   a. Does the page import `getFeatureFlag` (or equivalent helper) from `lib/config/feature_flags.ts`?
   b. Does the page server-side-fetch `NEW_QUERY_PIPELINE_ENABLED` and `AUDIT_ENABLED`?
   c. Does it pass `pipelineEnabled` (or equivalent prop) to `<ConsumeChat />`?
   d. What is the exact prop name used? (Phase 5's brief said `pipelineEnabled` + `audienceTier`. Phase 11A may have renamed.)
2. Open `platform/src/components/consume/ConsumeChat.tsx`. Identify:
   a. What prop(s) does it accept that gate the new vs legacy UI?
   b. Where in the component is the conditional render that picks new vs legacy? Quote the conditional.
   c. What does each branch render? (Specifically: does the truthy branch use `<StreamingAnswer />` from `consume/StreamingAnswer.tsx`?)
3. Trace through `<StreamingAnswer />` and `<AnswerView />` to confirm they import `<CitationChip />` from `components/citations/` and `<DisclosureTierBadge />` from `components/disclosure/`.
4. **Critical check**: if any consume page in Stream B does NOT pass the prop down OR uses a different prop name than what `ConsumeChat` reads, that page renders the legacy UI regardless of env state. This is Cause #3.

Stream C output: a section "Render Tree Audit" with a per-consume-page table showing: page path / fetches flag? / passes prop? / prop name / ConsumeChat receives prop? / branch taken at runtime.

### Stream D — API route audit

Determine which API endpoint the per-client consume page actually hits when a query is submitted.

1. Open `ConsumeChat.tsx`. Find the `fetch(...)` or `useChat(...)` call that submits queries. Note the exact URL it posts to.
2. Check whether the URL is `/api/chat/consume` (new pipeline route per Phase 4 + Phase 7 corrections) or `/api/consume` (legacy) or something else entirely.
3. Open the route file at the URL `ConsumeChat` posts to. Confirm:
   a. Does the route check `NEW_QUERY_PIPELINE_ENABLED` and branch to legacy vs new?
   b. If yes, what's the legacy branch's handler? Does it call `consume-tools.ts`?
   c. Is the new pipeline branch the orchestrator strategy switch (Phase 7's `createOrchestrator`)?
4. If `ConsumeChat` posts to a route that doesn't exist OR points to a third route that wasn't part of any Phase brief, note this as a finding.

Stream D output: a section "API Route Audit" with the URL, the route file path, and the conditional logic at the top of the route handler.

### Stream E — Diagnosis & recommendation

Synthesize Streams A-D into a root cause statement.

The investigation must end with one of these conclusions (or a nuanced combination):

- **Cause #1 (env override winning):** `.env.local` or another env file is explicitly setting one of the master flags to `false`, overriding the new code default. Fix scope: edit env file (one line), restart dev server.
- **Cause #2 (build cache stale):** The code defaults are correct, env files are clean, but `.next/` cache is stale and serving old compiled output. Fix scope: nuke `.next/` and restart.
- **Cause #3 (per-client page missed):** The root `/consume` page was integrated by Phase 5 but `/clients/[clientId]/consume/page.tsx` was either missed entirely or doesn't pass the `pipelineEnabled` prop down. Fix scope: small follow-up brief that updates the per-client consume page in parallel with the root.
- **Cause #4 (ConsumeChat branch logic):** Both pages pass the prop correctly, but `ConsumeChat`'s conditional render logic is wrong (e.g., inverted boolean, prop name typo). Fix scope: small edit in `ConsumeChat.tsx`.
- **Cause #5 (API route bypass):** UI is correctly switching components but submitting queries to the legacy API endpoint, so behavior looks legacy even if the components are new. Fix scope: route URL update in `ConsumeChat`.
- **Cause #6 (other):** Investigation surfaced something none of the above describes. Document it.

Stream E output: a section "Root Cause" stating which cause(s) the evidence supports, with citations back to specific findings in earlier streams. Then a "Recommended Remediation" section that proposes a follow-up brief scope (file paths to touch, expected effort, risk classification) — **without executing the fix**.

## Output artifact

The investigation produces ONE file:

`platform/scripts/cutover/stage1_diagnosis.md`

with these sections, in order:

1. Summary (3-5 sentences: what was investigated, what was found, what to do next)
2. Environment Audit (Stream A findings)
3. Consume Page Surface Map (Stream B findings)
4. Render Tree Audit (Stream C findings — table format)
5. API Route Audit (Stream D findings)
6. Root Cause (Stream E synthesis)
7. Recommended Remediation (a proposed follow-up brief outline, NOT the fix itself)

The file lives in `platform/scripts/cutover/` alongside `stage1_smoke.ts` for clean grouping.

## Critical constraints

- **Read-only.** Zero file modifications anywhere in the repo except the new diagnosis file.
- **No fixes.** Even if a one-line fix is obvious, document it in the recommendation section and stop.
- **No restarts.** Do not run `npm run dev`, do not nuke `.next/`, do not modify env files.
- **No `npm` commands** that would mutate state. `npm test` (read-only check) is fine. `npm install`, `npm run build`, etc. are forbidden.
- **Be specific.** "The page might fetch the flag" is not useful. "Line 14 of `app/clients/[clientId]/consume/page.tsx` calls `getFeatureFlag('NEW_QUERY_PIPELINE_ENABLED')` and passes the result as the `pipelineEnabled` prop on line 32; ConsumeChat reads it correctly at line 47" — that's useful.
- **Cite line numbers.** Every finding in the report should reference a file path and a line number range.

## Done criteria

1. Stream A: environment audit complete; report names every env file, every flag-related line, and the runtime-resolved value.
2. Stream B: every consume page route enumerated; root + per-client confirmed present (or absence noted).
3. Stream C: render tree traced from each consume page to ConsumeChat to leaf components; prop chain documented.
4. Stream D: API endpoint identified; route handler conditional documented.
5. Stream E: root cause stated; recommended remediation proposed; no fix applied.
6. `platform/scripts/cutover/stage1_diagnosis.md` exists, has all 7 sections, and is internally consistent (Stream E references findings from A-D).
7. Native reads the report and decides next step (likely a small follow-up fix brief).

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_11A_INVESTIGATION_v1_0.md and execute it.

After Sonnet completes, the diagnosis report at `platform/scripts/cutover/stage1_diagnosis.md` tells you what's actually broken. You then decide whether to fix it inline or author a follow-up brief.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when the diagnosis file exists and is internally consistent
