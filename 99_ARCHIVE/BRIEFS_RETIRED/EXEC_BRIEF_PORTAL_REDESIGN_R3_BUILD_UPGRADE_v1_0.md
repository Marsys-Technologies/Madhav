---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE_v1_0.md and execute it."
phase: Portal Redesign R3
phase_name: Build mode upgrade — three-pane cockpit (per-client)
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: MEDIUM
parallelizable_with: [R7]
must_complete_before: [R7 close]                     # R3 should close before R7 closes so R7 polishes R3's surface
depends_on: [R0, R2]                                 # R0 for AppShell; R2 because Continue-building CTA originates in R2's Build Room
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R3_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R3 — Build mode upgrade

## Mission

The per-client Build mode (`/clients/{id}/build`) is currently a v1 chat: basic `<Input>` + bubble list with a small `<PyramidStatusPanel>`. The Consume tab is a v3 mature shell with `ChatShell`, `ConversationSidebar`, `AdaptiveMessageList`, `Composer`, `StreamingMarkdown`, `CommandPalette`, `ShareButton`, branches, model picker, command palette. R3 closes that gap.

Two parts:

1. **Replace the BuildChat shell** with the same shell Consume uses — `ChatShell` + `ConversationSidebar` + `AdaptiveMessageList` + `Composer` + `StreamingMarkdown` riding on the same hook stack (`useChatSession`, `useBranches`, `useFeedback`, `useChatPreferences`). Build chat finally gets streaming, branches, command palette, model picker, and share.

2. **Compose the right pane** as a stack of already-built widgets — `JourneyStrip` for layer progress, `BriefPanel` for current intent, `InsightCards` for recently-built artifacts, a compact `MirrorPairsTable` summary, the existing `PyramidStatusPanel` collapsed by default. All these components exist in `platform/src/components/build/`; R3 composes them, doesn't author them.

R3 has internal sub-phase decomposition per VISION §4.3.3:

- **R3a** — Hook-compatibility audit (the gate item from VISION §4.3.1 G2). Independent investigation; produces a written audit naming whether `useChatSession` / `useBranches` / `useFeedback` accept the build endpoint as-is or need an adapter. If adapter exceeds 80 lines, R3 splits — R3b becomes its own session.
- **R3b** — UI swap and right-pane composition.

Zero schema changes, zero migrations, zero sidecar changes, zero auth changes.

## Pre-flight gate

Halt with a clear actionable message if any fail.

1. R0 closed; AppShell + ZoneRoot exist on `main`.
2. R2 closed; Chart Profile page renders; the Build Room's "Continue building" CTA links into `/clients/{id}/build` and is the origin of every entry into Build mode post-R2.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_R2_REPORT_v1_0.md` exists with `status: COMPLETE`.
4. R3 row in TRACKER §3 reflects authored or earlier.
5. Vision `status: CURRENT`.
6. Working tree clean. Branch `redesign/r3-build-upgrade`.

## Scope declaration

```yaml
may_touch:
  # The chat shell swap
  - platform/src/components/build/BuildChat.tsx                      # REPLACE — composes ChatShell now
  - platform/src/app/clients/[id]/build/page.tsx                     # narrow edits — props for new shell
  - platform/src/app/clients/[id]/build/layout.tsx                   # add ZoneRoot zone if needed (likely vellum)
  - platform/src/app/api/chat/build/route.ts  # BOUNDED — 3 changes only: toUIMessageStreamResponse, conversation persistence, conversationId in metadata

  # Right-pane composition (NEW orchestrator)
  - platform/src/components/build/BuildRightPane.tsx                 # NEW — composes JourneyStrip + BriefPanel + InsightCards + MirrorPairsTable + PyramidStatusPanel

  # Hook adapter (only if R3a determines it's needed)
  - platform/src/hooks/useBuildChatAdapter.ts                        # CONDITIONAL — only if /api/chat/build needs adaptation

  # Audit deliverable
  - 00_ARCHITECTURE/PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0.md     # NEW — R3a output

  # Tests
  - tests/components/BuildChat.test.tsx                              # NEW or rewritten
  - tests/components/BuildRightPane.test.tsx                         # NEW
  - tests/e2e/portal/build-mode.spec.ts                              # NEW

must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/lib/db/types.ts
  - platform/src/lib/firebase/
  - platform/src/app/api/chat/consume/**  # Consume route untouched  # NOTE: /api/chat/build/route.ts is in may_touch above — bounded changes only
  - platform/src/components/chat/**                                  # ChatShell, Composer, etc. — REUSE only, don't modify
  - platform/src/components/consume/**                               # R4 territory; R3 reuses but doesn't modify
  - platform/src/components/profile/**                               # R2 territory
  - platform/src/components/dashboard/**                             # R1 territory
  - platform/src/components/build/JourneyStrip.tsx                   # REUSE only
  - platform/src/components/build/BriefPanel.tsx                     # REUSE only
  - platform/src/components/build/InsightCards.tsx                   # REUSE only
  - platform/src/components/build/MirrorPairsTable.tsx               # REUSE only
  - platform/src/components/build/PyramidStatusPanel.tsx             # REUSE only
  - platform/src/components/shared/AppShell.tsx                      # R0 scope
  - platform/src/lib/strategies/single_model_strategy.ts             # synthesis untouched
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
```

If a discovery during execution forces a touch outside `may_touch`, halt and emit a `scope_expansion_request` block per `GOVERNANCE_INTEGRITY_PROTOCOL §F`.

## §1 — R3a: Hook-compatibility audit (gate item)

This is the FIRST task of R3, before any code change. Independent investigation; produces a written audit at `00_ARCHITECTURE/PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0.md`.

### §1.1 What the audit answers

Three concrete yes/no questions:

1. **Can `useChatSession` accept `/api/chat/build` as its endpoint?** Compare the request shape `useChatSession` sends against `/api/chat/build`'s request handler (`platform/src/app/api/chat/build/route.ts`). If shapes match: yes. If not: name the specific fields that differ.

2. **Can `useBranches` work with the build conversation model?** `useBranches` was authored for Consume. Verify it doesn't assume Consume-specific conversation metadata (e.g., audience tier, panel mode) that build conversations don't have.

3. **Can `useFeedback` work with the build response stream?** Verify `useFeedback`'s assumed message structure matches what `/api/chat/build` returns.

### §1.4 Scope amendment note

During R3a review it was determined that `/api/chat/build/route.ts` requires three bounded, format-level changes (not contract redesign) to enable `toUIMessageStreamResponse` streaming compatible with `@ai-sdk/react`'s `useChat`. A grep of the codebase confirmed that `BuildChat.tsx` is the sole consumer of this route. The changes are: (1) switch `toTextStreamResponse` → `toUIMessageStreamResponse`, (2) add first-turn conversation persistence (mirroring the existing Consume route pattern), (3) echo `conversationId` in the message metadata on the first turn. No request-shape change is visible to any other caller. This scope expansion was approved during R3a review — the route is now listed in `may_touch` above.

### §1.2 Audit outcome — three possible verdicts

**Verdict A — Direct compatibility.** All three hooks accept the build endpoint as-is. R3b proceeds with no adapter. R3 ships in this session.

**Verdict B — Thin adapter (≤ 80 lines).** A small adapter at `platform/src/hooks/useBuildChatAdapter.ts` translates between the build endpoint and the hook stack. R3b proceeds in this session with the adapter.

**Verdict C — Substantial adapter (> 80 lines) or contract gap.** The audit names the specific gap. R3 SPLITS — this session closes with the audit committed and a follow-up R3b brief authored. R3b becomes its own session.

### §1.3 Audit document structure

```markdown
---
artifact_id: PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT
version: 1.0
status: COMPLETE
authored_at: <ISO>
verdict: A | B | C
---

# R3a Hook-Compatibility Audit

## Question 1: useChatSession + /api/chat/build
[response shape comparison; verdict]

## Question 2: useBranches + build conversation model
[metadata comparison; verdict]

## Question 3: useFeedback + build response stream
[message structure comparison; verdict]

## Synthesis verdict
[A | B | C — with rationale]

## Adapter spec (if verdict B)
[exact adapter signature and translation rules]

## Split rationale (if verdict C)
[why a separate R3b session is needed; what it should do]
```

## §2 — R3b: BuildChat shell swap

Conditional on Verdict A or B. If Verdict C, this section is the input to a separate R3b brief.

### §2.1 New BuildChat composition

`platform/src/components/build/BuildChat.tsx` replaces its current `<Input>` + bubble list with:

```tsx
<ChatShell>
  <ConversationSidebar conversations={...} />
  <main>
    <AdaptiveMessageList messages={...} />
    <Composer onSend={handleSend} model={selectedModel} />
  </main>
  <BuildRightPane chartId={chartId} />
</ChatShell>
```

The shell is the same one Consume uses. The chat hooks (`useChatSession`, `useBranches`, `useFeedback`) are wired to the build endpoint per the audit's verdict. Streaming markdown, command palette, model picker, share — all inherited.

### §2.2 BuildRightPane composition

`platform/src/components/build/BuildRightPane.tsx` (NEW) is a vertical stack:

```tsx
<aside>
  <JourneyStrip layers={...} />          {/* R3 just composes; R0 already had this */}
  <BriefPanel currentIntent={...} />
  <InsightCards recent={...} />
  <MirrorPairsTable summary />
  <Collapsible>
    <PyramidStatusPanel detail={...} />
  </Collapsible>
</aside>
```

All five components already exist. R3 composes them. No styling tweaks beyond the wrapper.

### §2.3 The build page

`platform/src/app/clients/[id]/build/page.tsx` server component:

1. Resolves user/profile/chart per existing pattern.
2. Loads conversation history (existing helper).
3. Loads pyramid layers (existing helper).
4. Loads recent insights (may need new query — kept minimal).
5. Renders `<BuildChat chartId conversation history layers insights />`.

Wraps in `<ZoneRoot zone="vellum">` (Build is vellum, unlike Consume's ink).

### §2.4 What goes away

The current `BuildChat.tsx` (v1) is replaced wholesale. The custom `<Input>` + bubble list disappears. The standalone `<PyramidStatusPanel>` rendering moves into `<BuildRightPane>` as a collapsible.

## §3 — Tests

### §3.1 Unit tests

- `tests/components/BuildChat.test.tsx`: rewrite. Asserts `<ChatShell>` renders, `<ConversationSidebar>` renders, `<AdaptiveMessageList>` renders, `<Composer>` is interactive, `<BuildRightPane>` renders.
- `tests/components/BuildRightPane.test.tsx`: NEW. Asserts all five widgets render in order; collapsible PyramidStatusPanel works.

### §3.2 E2E

- `tests/e2e/portal/build-mode.spec.ts`: super_admin opens `/clients/{id}/build`; sees three-pane layout; sends a message; verifies streaming response renders; opens command palette via `Cmd+K`; switches model via picker.

### §3.3 Existing tests

All Consume tests, all chat shell tests, all build widget tests must continue to pass. Capture pre/post test count.

### §3.4 Governance scripts

`mirror_enforcer.py`, `drift_detector.py`, `schema_validator.py` exit 0.

## §4 — Closure report

`00_ARCHITECTURE/PORTAL_REDESIGN_R3_REPORT_v1_0.md` with `status: COMPLETE`. Document:

1. Audit verdict (A/B/C) and the audit's reasoning.
2. Adapter line count (if verdict B).
3. Did R3 ship in one session or split into R3a + R3b?
4. Test baseline preserved.
5. Any deferred polish items (these become R7 follow-ups).

Update TRACKER §3 R3 row to `status: closed` with session_id, closed_at, follow_ups.

## §5 — R7 coordination note

R7 is parallelizable with R3 per VISION's R7+R3 split decision. If R7 is in flight in another worktree while R3 is running:

- R7 polishes the surfaces R3 hasn't yet replaced (Roster, Chart Profile, Consume, Timeline, Cockpit) — those are stable.
- R7 explicitly defers Build mode polish to R7's `follow_ups` block; R3's closure adds those polish items as a small follow-up commit on `redesign/r3-build-upgrade` before its PR opens.
- The two PRs land in the order: R3 first (so R7 has the new BuildChat to verify against in its tests), then R7's polish commit, then R7 PR.

If R3 produces verdict C and splits, R7 still proceeds — R7 simply leaves Build mode alone in its current state.

## §6 — Out of scope

- Do NOT modify `/api/chat/build`'s API contract — only the client-side consumer.
- Do NOT modify Consume's chat shell.
- Do NOT add new build-side widgets — compose the existing ones.
- Do NOT add streaming logic to the build endpoint if it isn't there — that's a separate platform brief.
- Do NOT introduce DB migrations.
- Do NOT touch the parked trace-fix or platform-hygiene workstreams.

## §7 — One-line summary

Bring the per-client Build chat to feature parity with Consume by composing the existing chat shell + the existing build widgets — no new components, no API change.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE_v1_0.md (AUTHORED, 2026-04-30).*
