---
name: §M.16 EXEC BRIEF — Kill ConsumeChatLegacy + flag cutover (workstream close)
canonical_id: CHAT_V2_M_16_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored: 2026-05-18
governing_plan: 00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md §8.3 (workstream close §M.16)
governing_decision: Option C fast-cutover compromise (operator decision 2026-05-18). Originally §M.16 was scheduled after F.4 reflip + 7-day clean watch; accelerated to fire immediately after R6.5 + R6.6 merge.
branch: chore/chat-v2-m16/kill-legacy-flag-cutover
base: main (POST R6.6 merge)
pr_title: "chore(chat-v2/m16): kill ConsumeChatLegacy + flag cutover (workstream close)"
estimated_loc: ~-850 net (delete 817-LoC legacy file + remove flag plumbing across ~10 sites)
estimated_files: ~8 (1 delete + 7 edits)
may_touch:
  - platform/src/components/consume/ConsumeChatLegacy.tsx (DELETE 817 LoC)
  - platform/src/components/consume/ConsumeChat.tsx (simplify wrapper to re-export V2)
  - platform/src/components/consume/ConsumeChatV2.tsx (move ConsumeChatProps type from removed Legacy file)
  - platform/src/lib/config/feature_flags.ts (remove CHAT_V2_ENABLED from union + DEFAULT_FLAGS)
  - .github/workflows/deploy.yml (remove MARSYS_FLAG_CHAT_V2_ENABLED env override)
  - platform/src/app/clients/[id]/consume/page.tsx (remove chatV2Enabled prop + flag lookup)
  - platform/src/app/clients/[id]/consume/[conversationId]/page.tsx (remove chatV2Enabled prop + flag lookup)
  - platform/src/app/api/chat/consume/route.ts (remove chatV2Enabled conditional pendingStreamWriter — always use V2 path)
  - platform/src/components/consume/__tests__/lifecycle.test.tsx (remove ConsumeChatLegacy assertions)
  - platform/src/components/consume/__tests__/ConsumeChat.lel.test.tsx (review — likely also needs update)
must_not_touch:
  - V2 implementation code (useDataParts, EmptyState, ConversationSidebarV2, V2Message, etc. — all stay as-is)
  - sidebar/layout/composer/action-bar (R6.1-R6.6 already shipped)
  - any other flag in feature_flags.ts
  - the chat-v2-smoke workflow (R6-SMOKE-PATCH is still informational)
depends_on: R6.5 AND R6.6 merged to main + operator F.3 visual sign-off
operator_responsibilities:
  - F.3 visual walkthrough at dev server BEFORE merging this PR (verify V2 functions correctly end-to-end)
  - Post-merge gcloud env-var removal (CANNOT be automated by the PR — see §3.5)
  - Post-deploy production smoke (operator-driven login + send message + verify response)
---

# §1 Mission

Close the Chat V2 Big Bang workstream. Move every user from `ConsumeChatLegacy` to `ConsumeChatV2`. Remove the flag, remove the legacy file, simplify the wrapper, update deployment config.

This brief was originally scheduled as Round 6 plan §8.3 §M.16, gated on R6.1-R6.6 merge + F.4 reflip + 7-day clean watch (Option A in the operator's 2026-05-18 decision matrix). The operator chose **Option C fast-cutover compromise**: ship R6.5 + R6.6 (the two visual blockers), then §M.16 immediately. R6.2 (citation footnotes) and R6.3 (citation enrichment) ship as fix-forwards after cutover.

What ships in production after §M.16:
- Every user on V2.
- Flag `MARSYS_FLAG_CHAT_V2_ENABLED` does not exist (in code or in Cloud Run env).
- `ConsumeChatLegacy.tsx` does not exist.
- `ConsumeChat.tsx` is a trivial re-export of V2.
- 5/9 smoke gate tests GREEN (B1, O1, L1, L2, L3 from R6.x); 2 still RED (B2/B3, B4/B5 — R6.2 and R6.3 are post-cutover fix-forwards); B6 GREEN (R6.6); N1 GREEN.
- Known production-visible regressions vs legacy:
  - Raw `SIG.MSR.NNN` markers in answer text + citation chips in footer (B2/B3) — content-ugly but functional
  - Empty citation snippets when chip clicked (B4/B5) — citation panel less useful until R6.3 fix-forward lands

Acceptable trade-off per Option C: ship the cleaner repo + faster cutover, fix-forward the citation polish over the following ~3 days.

# §2 Scope

8 files. One delete, seven edits. Net LoC: approximately -850.

| File | Action | Notes |
|---|---|---|
| `platform/src/components/consume/ConsumeChatLegacy.tsx` | DELETE | 817-line file. All exports removed. |
| `platform/src/components/consume/ConsumeChat.tsx` | Simplify | Drop `chatV2Enabled` prop + flag conditional + Legacy import. Just re-export V2. |
| `platform/src/components/consume/ConsumeChatV2.tsx` | Move type | Define `ConsumeChatProps` here (currently imported from Legacy at line 40). Update `import type` to local declaration. |
| `platform/src/lib/config/feature_flags.ts` | Remove flag | Drop `CHAT_V2_ENABLED` from `FeatureFlag` union (line ~84) + from `DEFAULT_FLAGS` (line ~110ish). |
| `.github/workflows/deploy.yml` | Remove env | Line 78 `MARSYS_FLAG_CHAT_V2_ENABLED=false` deleted. |
| `platform/src/app/clients/[id]/consume/page.tsx` | Remove prop | Line 44 (`configService.getFlag('CHAT_V2_ENABLED')`) + line 64 (`chatV2Enabled={...}`) — drop both. |
| `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` | Remove prop | Lines 57 + 79 — same pattern. |
| `platform/src/app/api/chat/consume/route.ts` | Remove conditional | Lines 368-369 `chatV2Enabled` conditional `pendingStreamWriter` — always use V2 path. |
| `platform/src/components/consume/__tests__/lifecycle.test.tsx` | Remove assertions | Lines ~292-346: tests checking for ConsumeChatLegacy.tsx existence + chatV2Enabled prop forwarding. Remove those test blocks; legacy file is deliberately gone. |
| `platform/src/components/consume/__tests__/ConsumeChat.lel.test.tsx` | Review | Likely contains flag-on / flag-off assertions. Remove flag-off branch tests; keep V2-only behavior tests. |

# §3 Implementation specification

## §3.1 — `platform/src/components/consume/ConsumeChatV2.tsx` (move type first)

Currently line 40: `import type { ConsumeChatProps } from './ConsumeChatLegacy'`

Replace with a local declaration. The `ConsumeChatProps` interface lives in `ConsumeChatLegacy.tsx` today. Locate it (grep `export interface ConsumeChatProps` or `export type ConsumeChatProps` in `ConsumeChatLegacy.tsx`) and copy the verbatim definition into `ConsumeChatV2.tsx` BEFORE the `ConsumeChatV2` export.

**Before:**
```ts
import type { ConsumeChatProps } from './ConsumeChatLegacy'
```

**After (illustrative — actual shape determined by current Legacy export):**
```ts
export interface ConsumeChatProps {
  chartId: string
  chartName: string
  chartMeta?: string
  costVisibilityEnabled?: boolean
  audienceTier?: AudienceTier
  reports?: Report[]
}
```

Re-export from ConsumeChatV2 so external imports (`from '@/components/consume/ConsumeChat'`) still resolve via `ConsumeChat.tsx`'s re-export.

This MUST be the first edit. The other deletions break if `ConsumeChatProps` has no home.

## §3.2 — `platform/src/components/consume/ConsumeChat.tsx` (simplify wrapper)

**Current** (verbatim from main):

```tsx
/**
 * ConsumeChat — thin flag switch between legacy and V2 paths.
 *
 * Flag-off (MARSYS_FLAG_CHAT_V2_ENABLED=false, default):
 *   renders ConsumeChatLegacy — byte-identical to pre-α7 production behavior.
 *
 * Flag-on:
 *   renders ConsumeChatV2 — assistant-ui Thread shell (β phase populates full UX).
 *
 * All consumers import from this file; neither Legacy nor V2 is imported directly.
 */

import { ConsumeChatLegacy, type ConsumeChatProps } from './ConsumeChatLegacy'
import { ConsumeChatV2 } from './ConsumeChatV2'

export type { ConsumeChatProps }

interface SwitchProps extends ConsumeChatProps {
  /** Wire MARSYS_FLAG_CHAT_V2_ENABLED here (read by server pages via configService). */
  chatV2Enabled?: boolean
}

export function ConsumeChat({ chatV2Enabled, ...props }: SwitchProps) {
  if (chatV2Enabled) {
    return <ConsumeChatV2 {...props} />
  }
  return <ConsumeChatLegacy {...props} />
}
```

**Target:**

```tsx
/**
 * ConsumeChat — thin re-export of the V2 chat shell.
 *
 * Pre-§M.16 (closed 2026-05-18) this file was a flag-gated switch between
 * ConsumeChatLegacy and ConsumeChatV2. Post-cutover, V2 is the only path;
 * the legacy file is deleted; the flag MARSYS_FLAG_CHAT_V2_ENABLED is removed
 * from feature_flags.ts and from the Cloud Run env.
 */

export { ConsumeChatV2 as ConsumeChat, type ConsumeChatProps } from './ConsumeChatV2'
```

That's the entire file. ~10 LoC instead of ~30. The `SwitchProps` interface and `chatV2Enabled` plumbing are deleted.

## §3.3 — Delete `ConsumeChatLegacy.tsx`

```bash
git rm platform/src/components/consume/ConsumeChatLegacy.tsx
```

817 LoC gone. After this, `git grep ConsumeChatLegacy platform/src` should show only the now-stale references in tests + the §3.1 import we just removed. Those are the next sites to clean.

## §3.4 — `platform/src/lib/config/feature_flags.ts` (remove flag)

Two edits in this file.

**Edit 1: Remove from `FeatureFlag` union (line ~84):**

Find:
```ts
  // Chat V2 — assistant-ui big-bang (α7+). Default OFF; flip after phase α exit gate.
  // Env: MARSYS_FLAG_CHAT_V2_ENABLED.
  | 'CHAT_V2_ENABLED'
```

Delete those three lines.

**Edit 2: Remove from `DEFAULT_FLAGS` record:**

Find the `DEFAULT_FLAGS: Record<FeatureFlag, boolean>` block (line ~104 onwards). Delete the line:

```ts
  CHAT_V2_ENABLED: false,
```

If `configService.getFlag('CHAT_V2_ENABLED')` is called anywhere, that's a compile error post-edit — the executor's `tsc --noEmit` step catches it. Fix those call sites per §3.6.

## §3.5 — `.github/workflows/deploy.yml` (remove env override)

Current line 78 (or nearby):
```yaml
            MARSYS_FLAG_CHAT_V2_ENABLED=false
```

Delete that line entirely. The deploy step will no longer set the env var.

**CRITICAL — operator post-merge step.** Per the deploy-cloudrun-env-merge memory note: removing a line from `env_vars:` in `deploy.yml` does NOT remove the var from the running Cloud Run service — it merges, not replaces. The operator must explicitly run:

```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --remove-env-vars MARSYS_FLAG_CHAT_V2_ENABLED
```

after the deploy completes. Document this in the PR description as a post-merge operator action. WITHOUT this step, the Cloud Run env continues to define `MARSYS_FLAG_CHAT_V2_ENABLED=false` (the previous value), and even though `configService.getFlag` no longer reads it (because the flag is gone), residual env-var pollution is the kind of thing future debugging falls over.

## §3.6 — Remove `chatV2Enabled` plumbing across server pages + route

Three sites, identical pattern.

**`platform/src/app/clients/[id]/consume/page.tsx`** lines 44 + 64:

Remove:
```ts
const chatV2Enabled = configService.getFlag('CHAT_V2_ENABLED')
```
and:
```tsx
chatV2Enabled={chatV2Enabled}
```

**`platform/src/app/clients/[id]/consume/[conversationId]/page.tsx`** lines 57 + 79: same removal.

**`platform/src/app/api/chat/consume/route.ts`** lines 368-369:

Find:
```ts
const chatV2Enabled = configService.getFlag('CHAT_V2_ENABLED')
const pendingStreamWriter = chatV2Enabled
  ? <V2 path>
  : <Legacy path>
```

Replace with the V2 path unconditionally. The Legacy path code (whatever follows the `:`) is dead and gets deleted.

## §3.7 — Update tests

**`platform/src/components/consume/__tests__/lifecycle.test.tsx`** has at least three blocks referencing legacy:

- Lines ~292-307: assertions that `ConsumeChatLegacy.tsx` exists as a file
- Lines ~316-340: assertions that flag-off path renders LiveReasoningCard
- Line 346: `expect(src).toContain('chatV2Enabled')` checking the switch wrapper

All three blocks should be deleted. The lifecycle test now asserts V2-only behavior.

**`platform/src/components/consume/__tests__/ConsumeChat.lel.test.tsx`** — review file. If it tests flag-on/flag-off render branches, remove flag-off cases. Keep only V2 behavior. If after edits the file becomes trivial, evaluate whether to delete it entirely (operator judgement; default to keeping the file with V2-only tests for regression coverage).

## §3.8 — Final grep proof

After all edits:

```bash
grep -rn "ConsumeChatLegacy\|chatV2Enabled\|CHAT_V2_ENABLED\|MARSYS_FLAG_CHAT_V2_ENABLED" \
  platform/src .github/workflows 2>&1
```

Expected: **zero hits**. Any remaining reference is a leak — fix it before opening the PR.

# §4 Acceptance criteria

- [ ] `platform/src/components/consume/ConsumeChatLegacy.tsx` does not exist.
- [ ] `platform/src/components/consume/ConsumeChat.tsx` is reduced to ~10 LoC (re-export only).
- [ ] `platform/src/components/consume/ConsumeChatV2.tsx` declares `ConsumeChatProps` locally and exports it.
- [ ] `platform/src/lib/config/feature_flags.ts`: `CHAT_V2_ENABLED` removed from `FeatureFlag` union AND from `DEFAULT_FLAGS`.
- [ ] `.github/workflows/deploy.yml`: `MARSYS_FLAG_CHAT_V2_ENABLED` line removed.
- [ ] `grep -rn "ConsumeChatLegacy\|chatV2Enabled\|CHAT_V2_ENABLED\|MARSYS_FLAG_CHAT_V2_ENABLED" platform/src .github/workflows` returns zero hits.
- [ ] `cd platform && npx tsc --noEmit` exits 0.
- [ ] `cd platform && npx eslint src/components/consume src/app/clients src/app/api/chat src/lib/config` exits 0.
- [ ] `cd platform && npm test` exits 0. Lifecycle + ConsumeChat.lel tests updated for V2-only behavior.
- [ ] PR description includes the post-merge `gcloud run services update --remove-env-vars MARSYS_FLAG_CHAT_V2_ENABLED` step that the operator must run.
- [ ] **Operator F.3 visual sign-off** before merge: end-to-end conversation through V2 in dev server (or staging), confirms no critical regression beyond the known B2/B3/B4/B5 citation polish issues.

# §5 Verification commands

```bash
cd platform

# Confirm Legacy file is gone
test ! -f src/components/consume/ConsumeChatLegacy.tsx && echo "Legacy deleted" || echo "FIX: Legacy still exists"

# Confirm zero leak
grep -rn "ConsumeChatLegacy\|chatV2Enabled\|CHAT_V2_ENABLED\|MARSYS_FLAG_CHAT_V2_ENABLED" \
  src .github/workflows 2>&1 | head -10
# Expected: no output

# Compile + lint + test
npx tsc --noEmit
npx eslint src/components/consume src/app/clients src/app/api/chat src/lib/config
npm test

# Smoke spec (operator-side with cookie)
# Expected: 5+1=6 GREEN (B1, O1, L1, L2, L3, B6, N1); 2 RED (B2/B3, B4/B5)
# Wait — N1 is reports library; if R6.6 merged before this, B6 also GREEN.
# Total post-§M.16: 7/9 GREEN (B1, O1, L1, L2, L3, B6, N1) + 2 RED (B2/B3, B4/B5)
npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts \
  --project=chromium --reporter=list

# Local dev server full walkthrough
npm run dev &
DEV_PID=$!
sleep 5
# Operator: open http://localhost:3000/clients/<dev-chart>/consume
# Operator: send a real query (with a real Gemini/DeepSeek key in local .env)
# Operator: verify the full flow — stage stepper, tool cards, answer, citations,
#   stop button, regenerate, copy, details drawer
# Operator: walk through every R6.x-fixed surface
kill $DEV_PID
```

# §6 Hard constraints

- DO NOT branch before BOTH R6.5 AND R6.6 are merged to main.
- DO NOT skip the post-merge `gcloud run services update --remove-env-vars` step — env-var residue persists otherwise.
- DO NOT remove or modify any other feature flag in feature_flags.ts.
- DO NOT modify R6-SMOKE spec or workflow — those stay informational until R7.
- DO NOT modify V2 implementation files (useDataParts, EmptyState, ConversationSidebarV2, V2Message, etc.) — they're already correct.
- DO NOT keep ConsumeChatLegacy.tsx around "just in case." This brief deletes it. Rollback path is `git revert`.

# §7 Risks + mitigations

| Risk | Mitigation |
|---|---|
| Production regression after cutover (some V2 path doesn't work for a real user) | Operator F.3 sign-off in §4 is the gate. Rollback is `git revert <merge-sha>` + redeploy. ~10-minute recovery time. |
| Cloud Run env var `MARSYS_FLAG_CHAT_V2_ENABLED=false` persists despite workflow removal | §3.5 calls this out explicitly. Operator MUST run the `gcloud --remove-env-vars` command post-deploy. After that, no env override exists. |
| A non-grepped reference to `chatV2Enabled` or `CHAT_V2_ENABLED` exists in a `.env*` file, README, or doc | §3.8 grep includes `.github/workflows` but not docs. Expand the grep to include `**/*.md README.md` if executor wants belt-and-suspenders. If found, drop those references. |
| Test file deletion breaks a snapshot or unrelated test | `npm test` catches it; update or remove accordingly. |
| `ConsumeChatProps` type definition has subtle field differences between Legacy's export and what V2 currently consumes | Audit during §3.1: read the Legacy export, read the V2 destructure (`function ConsumeChatV2({ chartId, chartName, chartMeta, costVisibilityEnabled, audienceTier, reports = [] }: ConsumeChatProps)` at ~line 1234), confirm every field. If Legacy had extras V2 doesn't use, decide: include them (forward-compat) or drop (cleanup). Default to dropping unused fields. |
| `route.ts` line 368-369 conditional `pendingStreamWriter` had behavior the V2 path doesn't replicate | Read the conditional carefully BEFORE deleting. If the Legacy branch did something the V2 branch doesn't (e.g., a different writer for legacy SSE format), evaluate whether that behavior is still needed. Most likely it's pure flag-switch with no real branching. Document in the PR description. |
| §M.17 (CLAUDE.md §E mark workstream CLOSED + memory file rotation) is a separate follow-up | Out of scope for this PR. File as a Cowork housekeeping task post-merge. |

# §8 PR description template

```
## What this PR does

Closes the Chat V2 Big Bang workstream (§M.16 from Round 6 plan §8.3). Every user moves to ConsumeChatV2 unconditionally. The flag, the wrapper switch, and the legacy file are all removed.

Per Option C fast-cutover compromise (operator decision 2026-05-18), this PR fires after R6.5 + R6.6 land (the two visual blockers). R6.2 + R6.3 (citation polish) ship as post-cutover fix-forwards.

## Files touched

- DELETE `platform/src/components/consume/ConsumeChatLegacy.tsx` (817 LoC)
- MOD `platform/src/components/consume/ConsumeChat.tsx` (simplify to re-export of V2)
- MOD `platform/src/components/consume/ConsumeChatV2.tsx` (move ConsumeChatProps type from removed Legacy file)
- MOD `platform/src/lib/config/feature_flags.ts` (remove CHAT_V2_ENABLED from union + DEFAULT_FLAGS)
- MOD `.github/workflows/deploy.yml` (remove MARSYS_FLAG_CHAT_V2_ENABLED env override)
- MOD `platform/src/app/clients/[id]/consume/page.tsx` (remove chatV2Enabled plumbing)
- MOD `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` (same)
- MOD `platform/src/app/api/chat/consume/route.ts` (remove conditional pendingStreamWriter)
- MOD `platform/src/components/consume/__tests__/lifecycle.test.tsx` (remove legacy assertions)
- MOD `platform/src/components/consume/__tests__/ConsumeChat.lel.test.tsx` (review + V2-only tests)

Net LoC: approximately -850.

## ⚠ Post-merge operator action REQUIRED

The Cloud Run env-vars merge with new deploys; removing a line from `deploy.yml` does NOT remove the var from the running service. After this PR merges + the deploy completes, the operator MUST run:

```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --remove-env-vars MARSYS_FLAG_CHAT_V2_ENABLED
```

Without this step, the Cloud Run service continues to define `MARSYS_FLAG_CHAT_V2_ENABLED=false` (the previous value). The flag is gone from code so this doesn't break anything, but it leaves env-var residue that future debugging falls over.

## Known regressions vs legacy that ship to users

Per Option C fast-cutover trade-off, these ship as post-cutover fix-forwards:

- **B2/B3** raw `SIG.MSR.NNN` markers in answer text + citation chips in footer. Citations work, just visually clumsy. R6.2 fixes.
- **B4/B5** empty citation snippets when chip clicked. Citation panel useful but less informative. R6.3 fixes.

All other Round 6 P0 bugs (B1, O1, L1, L2, L3, B6) are already fixed in main.

## R6-SMOKE delta

| Test | After §M.16 |
|---|---|
| B1, O1 | GREEN (R6.1) |
| L1, L2 | GREEN (R6.4) |
| L3 | GREEN (R6.5) |
| B6 | GREEN (R6.6) |
| N1 | GREEN |
| B2/B3 | RED (R6.2 follow-up) |
| B4/B5 | RED (R6.3 follow-up) |

Green count: 7/9.

## Refs

- `00_ARCHITECTURE/chat_v2_briefs/round6/M.16-kill-legacy-flag-cutover.md` (this PR's brief)
- `00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md` §8.3
- Operator decision 2026-05-18 (Option C fast-cutover compromise)
```

# §9 Post-merge — operator runbook

1. Wait for GitHub Actions deploy workflow to complete (typically 5-8 minutes after merge).
2. Confirm the new Cloud Run revision is healthy: `gcloud run revisions list --service=amjis-web --region=asia-south1 --limit=3`
3. **Remove the residual env var** (CRITICAL):
   ```bash
   gcloud run services update amjis-web \
     --region asia-south1 \
     --remove-env-vars MARSYS_FLAG_CHAT_V2_ENABLED
   ```
4. Confirm removal: `gcloud run services describe amjis-web --region asia-south1 --format yaml | grep MARSYS_FLAG_CHAT_V2_ENABLED` → no output.
5. Open production URL, log in, send a test query, verify V2 renders correctly.
6. File the §M.17 follow-up (Cowork housekeeping): update `CLAUDE.md §E` to mark Chat V2 Big Bang workstream CLOSED; rotate `memory/project_chat_v2_workstream.md` to a historical-record state.
7. Author R6.2 + R6.3 fix-forward briefs (citation polish).

# §10 Changelog

- **v1.0 (2026-05-18, READY_FOR_EXECUTION)** — Initial authoring. Workstream-close brief: kill ConsumeChatLegacy (817 LoC delete), simplify wrapper, remove flag from feature_flags.ts + deploy.yml + Cloud Run env. Operator F.3 sign-off + post-merge gcloud env-var removal are mandatory steps. Known regressions B2/B3 + B4/B5 explicitly ship to users as post-cutover fix-forwards per Option C compromise.
