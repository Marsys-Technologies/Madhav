# WS-1 S1 — Dashboard + CRUD + State-Aware Build Entry — CC Prompt

> **Paste this entire block into your Claude Code chat in Google Antigravity IDE AFTER Step 0 closes.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS1_DRIVABLE_PORTAL_v1_0.md` (§4.3)
> Reads with: `00_ARCHITECTURE/BRAHMA_BUILD_UX_SPEC_v1_0.md` §2, §3, §4, §8, §11–§13
> Branch: `feature/ws1-drivable-portal` (continuing from Step 0)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code in Google Antigravity IDE. Step 0 closed — migrations 118/124/125/126/127 applied, build orchestrator schema complete. S1 extends the existing serve shells (`ClientRoster`, `ClientCard`, `NewClientForm`, dashboard page) into a fully account-shaped surface with full CRUD per `BRAHMA_BUILD_UX_SPEC §2–§4 + §8 + §13`.

**Single commit on `feature/ws1-drivable-portal`.** All UI strings use the Brahma lexicon (Sanskrit + English; never L0–L5). All edits extend the existing design system (theme tokens, type scale, spacing); no new visual tokens.

## Step 1 — Read the existing serve shells

Before any edit, read each file end to end so the extensions integrate cleanly. Use the Read tool:

```bash
# Locate each
find platform/src -name 'NewClientForm.*' -o -name 'ClientRoster.*' -o -name 'ClientCard.*' -o -name 'BuildsInProgressCard.*' 2>/dev/null \
  | grep -v node_modules | tee /tmp/ws1_s1_existing.txt

# Find the dashboard page
find platform/src/app -name 'page.tsx' -path '*dashboard*' 2>/dev/null

# Find the existing build state queries (used by ClientCard badge if any)
grep -rEn "pyramid_layers|build_state|buildState" platform/src/lib platform/src/hooks \
  --include='*.ts' --include='*.tsx' 2>/dev/null | head -20
```

Read every file in `/tmp/ws1_s1_existing.txt` plus the dashboard page. Identify:
- Existing layout/grid pattern in `ClientRoster`.
- `ClientCard`'s current line structure (name / date / state / actions).
- `NewClientForm`'s field list + validation; the ayanamsha selector slot.
- Build-state derivation pattern (likely query on `pyramid_layers` or `builds.status`).

Write `/tmp/ws1_s1_existing_map.md` capturing the integration points.

## Step 2 — Build-state derivation (the data hook S1 needs)

S1's state chip + layer pip rail both read a derived build-state per chart. Centralize the derivation in a hook so `ClientCard` (S1) and the cockpit (S2) share one source of truth.

Create `platform/src/hooks/useChartBuildState.ts` (or refine the existing equivalent if found in Step 1):

```typescript
// Derives state per spec §13 from builds + pyramid_layers
// Returns: {
//   overall: 'not-built' | 'building' | 'built' | 'attention' | 'failed'
//   currentLayer: 'brahmagyan' | 'ganita' | 'bodha' | 'kala' | 'phala' | 'mimamsa' | null
//   currentLayerPercent: 0..100
//   layerPips: Array<{ layer, state: 'dim' | 'building' | 'amber' | 'lit' }>
//   shortfallNotes: Array<{ layer, expected, actual }>  // for amber
// }
```

Schema reads:
- `SELECT status, current_step, error_summary FROM builds WHERE chart_id = $1 ORDER BY started_at DESC LIMIT 1`
- `SELECT layer, sublayer, status, expected_rows, actual_rows FROM pyramid_layers WHERE chart_id = $1`
- Map `pyramid_layers.layer` values to Brahma external names per the lexicon (no L0–L5 leaks into the return type).

Brahma lexicon mapping helper (export from `lib/brahma/lexicon.ts`):

```typescript
export const BRAHMA_LEXICON: Record<'brahmagyan'|'ganita'|'bodha'|'kala'|'phala'|'mimamsa', { sanskrit: string; english: string }> = {
  brahmagyan: { sanskrit: 'Brahmagyan', english: 'Foundation' },
  ganita:     { sanskrit: 'Gaṇita',      english: 'Chart Facts' },
  bodha:      { sanskrit: 'Bodha',       english: 'Chart Intelligence' },
  kala:       { sanskrit: 'Kāla',        english: 'Temporal' },
  phala:      { sanskrit: 'Phala',       english: 'Prediction' },
  mimamsa:    { sanskrit: 'Mīmāṃsā',     english: 'Learning' },
} as const;
```

Type the lexicon so any future consumer is forced through this map; no string-typed layer names elsewhere.

## Step 3 — `ClientCard` extension

Per spec §2 "Account card":

- **Line 1:** chart name + state chip. State chip variants:
  - `Not built` (neutral)
  - `Building — {Sanskrit Layer} · {N}%` (amber, animated dot)
  - `Built · all verified` (teal check)
  - `Attention — {Sanskrit Layer} thin` (amber)
  - `Failed — {Sanskrit Layer}` (red)
- **Line 2:** birth date · birth place (unchanged).
- **Line 3:** new — 6-segment layer pip rail. Each pip = one layer, filled per `useChartBuildState().layerPips`. Brahmagyan is always filled (bedrock); the others fill as the build progresses.
- **Health dot** (existing) → reflect the worst non-green gate.
- **Row actions (kebab):** `Open · Build/Resume · Consult · Edit · Delete`. Show condensed when card is narrow.

Grantee view (read-only): show only `Open · Consult`. Read `authorizeChartAccess` result to decide.

Accessibility:
- `aria-label` on the state chip: `"{chart name}: {state text}"`.
- Pip rail uses an `aria-label="Build progress: {N} of 6 layers complete"`.
- Kebab menu keyboard-navigable.

## Step 4 — `NewClientForm` extension — ayanamsha-set selector

Per spec §3:

- Add an `ayanamsha-set selector` field after the existing birth fields. The 5 canonical ayanamshas (Lahiri, Raman, Krishnamurti, Yukteshwar, Fagan-Bradley — pull the exact list from L0 reference or the existing engine config; do NOT hardcode without verification).
- Default: all 5 selected. Min 1.
- Inline copy: "Ayanamsha sets the zodiac reference. More selections = a richer, cross-checked build, and a larger chart."
- Primary action label: change from "Build now" (if existing) → **"Create chart"**. Creation never auto-builds.
- On submit: persist → return to dashboard with a toast "Chart created. Build it now?" plus a **Build** affordance deep-linking to `/clients/[id]/build` (state = fresh).

## Step 5 — New edit page at `/clients/[id]/edit`

Per spec §4:

```bash
# Create the route directory
mkdir -p platform/src/app/clients/\[id\]/edit
# Create the page
```

Create `platform/src/app/clients/[id]/edit/page.tsx`:

- Reuse the `NewClientForm` component, hydrated from the chart's current data.
- Persistent banner at the top: **"Editing birth details will rebuild this entire chart (Gaṇita → Mīmāṃsā) from scratch."**
- Submit handler: detect whether any birth-affecting field changed (name/notes-only changes do NOT rebuild). If birth-affecting field changed, show D1 confirm (Step 7).
- After confirm: persist the edit → trigger a full auto-cascade rebuild via the existing build trigger API → route to `/clients/[id]/build` in `building` state.
- Ayanamsha-set changes: rebuild only the added/removed ayanamsha branches if the build orchestrator supports per-ayanamsha rebuild; else a full rebuild. Match the existing dispatcher capability — don't promise per-ayanamsha if it isn't there.

## Step 6 — Delete dialog (hard wipeout, no soft-delete)

Per spec §2 + §8 D2:

Add a `DeleteChartDialog` component (or extend an existing dialog). Behavior:
- Title: **"Delete {chart name} permanently?"**
- Body: "This immediately and irreversibly wipes the chart and all its data. There is no recovery."
- Confirmation gate: require typing the chart name exactly to enable the Delete button (or hold-to-confirm for 2 seconds).
- Delete button uses the danger style from the existing theme.
- On confirm: call a new server action / API endpoint `DELETE /api/charts/[id]` that:
  - Verifies the caller is owner or super_admin.
  - Deletes the chart row AND all per-chart data: every `brahmagyan_*` (if per-chart-scoped — most are global, so skip), `ganita_*`, `bodha_*`, `kala_*`, `phala_*`, `mimamsa_*` rows WHERE chart_id = $1, plus `builds`, `build_steps`, `build_events`, `pyramid_layers`, `conversation_branches`, `conversations` for the chart.
  - Plus any chart-scoped GCS objects (out of WS-1 scope — leave a TODO for WS-0E GCS purge to sweep periodically).
  - Returns success; client removes the card from the roster.

The delete query is destructive; per the durable rule, it lives in ONE place behind a typed function that takes a chart_id, runs in a transaction, and is unit-tested against a seeded chart. Do NOT scatter delete SQL across the codebase.

## Step 7 — Confirm dialogs

Per spec §8:

- **D1 — Edit-rebuild confirm:** title "Rebuild {chart}?"; body "Editing birth details rebuilds the entire chart from scratch (Gaṇita → Mīmāṃsā). Current results will be replaced." Buttons: [Cancel] [Rebuild]. Primary is deliberate, not default-focused (Escape cancels; Enter does not auto-confirm).
- **D2 — Delete confirm:** already specified in Step 6.
- **D3 — Cancel build confirm:** (used in S2; deferred). Specified in spec §8 for reference.

Add D1 + D2 as separate components in `platform/src/lib/components/dialogs/` (or extend an existing dialog dir).

## Step 8 — Dashboard wiring

- Each `ClientCard` `Open` action → routes to `/clients/[id]/consult` (or `/clients/[id]/build` if not yet built; the state-aware Build entry per spec §5.1).
- `Build/Resume` action → routes to `/clients/[id]/build` (S2's cockpit, which lands fully in WS-1 S2 — for now, just route there; an empty cockpit page lands in S2).
- `Edit` action → routes to `/clients/[id]/edit` (Step 5).
- `Delete` action → opens D2.

For now, **the build page can be a placeholder** that says "Cockpit coming in WS-1 S2 — for now, build from the API." That keeps the route wired so the dashboard works end-to-end while S2 fills the cockpit.

## Step 9 — AC verification

```bash
cd platform
npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head
# Expected: 0 new errors

npm run build 2>&1 | tail -10
# AC-11: must succeed (Step 0.5's Turbopack fix should already be applied if it was needed)

cd ..
```

**Lexicon AC (AC-1):**
```bash
grep -rEn "\b(L0|L1|L2|L2\.5|L3|L4|L5)\b" \
  platform/src/app/dashboard platform/src/app/clients \
  platform/src/lib/components/ClientRoster.tsx \
  platform/src/lib/components/ClientCard.tsx \
  platform/src/lib/components/NewClientForm.tsx \
  platform/src/lib/components/dialogs/ \
  --include='*.tsx' --include='*.ts' 2>/dev/null \
  | grep -vE "(^//|/\*|\* |Pro|ProDAG)" \
  | head -20
# Expected: zero hits (or only Pro/super-admin guarded blocks)
```

**Smoke (manual / curl):**
- Visit `/dashboard` (curl + read HTML; assert no `L0`/`L1` strings, assert Brahma lexicon present)
- Visit `/clients/test-stub-id/edit` (curl; expect 200 or 404 depending on auth — not 500)
- POST a delete to `/api/charts/test-stub-id` with no auth → expect 401/403, not 500

## Step 10 — Commit + push

```bash
git add -A
git status

git commit -m "feat(ws1-s1): dashboard + CRUD + state-aware build entry

WS-1 S1: extends the existing serve shells into the account-management
shape per BRAHMA_BUILD_UX_SPEC §2–§4 + §8.

Changes:
- ClientCard: state chip (Brahma-lexicon labels) + 6-segment layer pip rail + Open/Resume/Consult/Edit/Delete actions
- NewClientForm: ayanamsha-set selector (5 canonical, default-all, min-1) + 'Create chart' primary action
- New /clients/[id]/edit page with persistent rebuild-warning banner + D1 confirm + auto-cascade rebuild trigger
- New DeleteChartDialog (D2) with name-typed confirmation + atomic per-chart wipe API at DELETE /api/charts/[id]
- New useChartBuildState hook + Brahma lexicon helper (lib/brahma/lexicon.ts) shared with S2
- Build page placeholder routes wired (S2 fills the cockpit)

ACs satisfied:
- AC-1 lexicon enforcement: client-facing strings use Sanskrit+English only
- AC-2 entry paths: Create→Build deep-link + Roster→Build action both land on state-aware /clients/[id]/build
- AC-6 birth-data edit cascades; delete is hard wipeout

Refs WS-1 brief §4.3, predecessor tag legacy-cleanup-arc-complete"

git push origin feature/ws1-drivable-portal
```

Report:
- Commit SHA
- Typecheck delta vs baseline
- AC-1 lexicon grep result
- Any spec items deferred to S2 (e.g., the Build page placeholder)
- Any design-system questions for the native (color tokens used for state chip, etc.)

**STOP. Do NOT open the PR.** S2 + S3 land on the same branch; the PR opens after S3 (or after S2 if S3 is deferred).

---

## Hard stops

- Step 1 reveals the existing `NewClientForm` is fundamentally not extensible (e.g., it's wrapped in a third-party library that doesn't allow new fields cleanly) — halt; report; native + Cowork redesign.
- Step 2 build-state derivation requires a DB schema column that doesn't exist post-Step-0 — halt; surface what's missing.
- Step 5 edit page submission needs a server action API that doesn't exist and Step 0 didn't create — halt; design the API with native before continuing.
- Step 6 delete needs to cascade to a per-chart table whose name isn't predictable from the brahma/* prefix (e.g., a global table with chart_id rows) — halt; list each table needing scoped deletes; native approves the list.
- AC-1 lexicon grep returns hits in non-Pro/non-super-admin code — halt; fix every leak before commit.
- More than 3 attempts on any single component edit.

Begin with Step 1 (read the existing shells). Report at the commit.
