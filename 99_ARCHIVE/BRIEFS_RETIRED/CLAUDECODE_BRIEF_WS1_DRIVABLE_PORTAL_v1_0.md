---
artifact: CLAUDECODE_BRIEF_WS1_DRIVABLE_PORTAL_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS1_DRIVABLE_PORTAL
version: 1.0
status: READY_FOR_EXECUTION (master brief; per-step paste prompts ship alongside)
project_codename: Brahma — WS-1 Drivable + Visible Portal
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code extension running inside Google Antigravity IDE
execution_surface: >
  Claude Code (the extension) in Google Antigravity IDE. CC drives from its integrated bash + file
  tools, rooted at `/Users/Dev/Vibe-Coding/Apps/Madhav`. Front-end work uses CC's installed
  front-end design plugins where applicable (per BRAHMA_BUILD_UX_SPEC §0 "extend the existing
  design system"). Prod DB access via `platform/scripts/start_db_proxy.sh`.
follows: CLAUDECODE_BRIEF_WS0C_2_FINAL_RESIDUALS (sealed at tag `legacy-cleanup-arc-complete`, commit `ccc66c77`)
runs_in_parallel_with:
  - WS-2 (depth build) — different file tree (python-sidecar)
  - WS-3 (Rule Base) — different file tree (sidecar rules)
native_approved: true  # native confirmed 2026-06-04 — "Yes" (start WS-1 next)
context: >
  With the cleanup arc closed, the portal becomes the next focus. Per the BRAHMA_COMPLETION_PLAN WS-1,
  the deliverable is "the portal so the native can drive a build and SEE what's happening at each
  asset." Concrete surfaces are specified in BRAHMA_BUILD_UX_SPEC_v1_0.md. WS-1 executes that spec
  against the existing serve shells, using a state-aware Build page, push/SSE event rail, and an
  Asset Inspector tied to per-asset gate verdicts.
acceptance_criteria:
  - "AC-1: No client-facing surface shows L0..L5 strings, asset codenames, or engine/swarm jargon — Brahma Sanskrit + English lexicon only (BRAHMA_BUILD_UX_SPEC §14.1)"
  - "AC-2: Both entry paths (Create → Build; Roster → Build) land on a correct state-aware S4 (spec §14.2)"
  - "AC-3: The Layer Tower updates live via push/SSE — no manual refresh required (spec §14.3)"
  - "AC-4: An under-volume asset renders amber with the exact shortfall; its layer does not light (spec §14.4)"
  - "AC-5: The Asset Inspector shows data + provenance + gate verdicts + live tool state tested against this build (spec §14.5)"
  - "AC-6: Birth-data edit → single confirm → full-stack rebuild; delete → hard wipeout, no recovery path (spec §14.6)"
  - "AC-7: Consult becomes available at Gaṇita and gains reach as layers verify; offers no ungroundable suggestions (spec §14.7)"
  - "AC-8: Brahmagyan renders as global bedrock for clients and only builds on the admin one-time screen (spec §14.8)"
  - "AC-9: Keyboard / screen-reader accessible; reduced-motion honored; AA contrast in light + dark (spec §14.9)"
  - "AC-10: Migrations 118 / 124 / 125 / 126 / 127 / 133 applied to prod; WS-0C-2 DEFERRED build-system citations now resolve against live schema. (Migration 133 / notification_views added during Step 0 execution — brief author omitted it; CC caught the gap.)"
  - "AC-11: `npm run build` exits 0 — the Turbopack symlink pre-existing blocker is either resolved as part of Step 0.5 OR confirmed isolated to python-sidecar (not web build)"
  - "AC-12: All six load-bearing CI gates green on the WS-1 PR (typecheck, unit-tests, secret-scan, naming-lint, governance-gates, planner-regression)"
may_touch:
  - "platform/src/app/**"
  - "platform/src/components/**"
  - "platform/src/lib/components/**"
  - "platform/src/hooks/**"
  - "platform/src/lib/api/**"  # only the build/consume + new dashboard/cockpit/inspector APIs
  - "platform/src/lib/db/queries/**"  # new queries for build state, pyramid_layers, inspector
  - "platform/supabase/migrations/**"  # NEW migrations for any WS-1 schema additions only; existing ones untouched
  - "platform/python-sidecar/pipeline/build_chart.py"  # build_events emit additions for SSE rail, if needed
  - "platform/python-sidecar/pipeline/dispatcher.py"  # resume/rebuild surface, if needed
must_not_touch:
  - "platform/python-sidecar/brahmagyan/**"   # WS-2 territory
  - "platform/python-sidecar/ganita/**"
  - "platform/python-sidecar/bodha/**"
  - "platform/python-sidecar/kala/**"
  - "platform/python-sidecar/phala/**"
  - "platform/python-sidecar/mimamsa/**"
  - "platform-mcp/**"
  - "01_FACTS_LAYER/**"
  - "00_ARCHITECTURE/**"  # except minor governance pointer updates the brief flags inline
  - ".github/workflows/ci.yml"   # cleanup arc settled these
  - "platform/supabase/migrations/0*.sql"  # historical migrations frozen
project_facts:
  gcp_project: madhav-astrology
  region: asia-south1
  prod_url: madhav.marsys.in
  branch: feature/ws1-drivable-portal
  predecessor_tag: legacy-cleanup-arc-complete
  predecessor_sha: ccc66c77
---

# CLAUDECODE_BRIEF — WS-1 Drivable + Visible Portal

## §1 Mission

Make the portal usable as the chart-building cockpit the native can drive himself. Three deliverables, all per `BRAHMA_BUILD_UX_SPEC_v1_0.md`:

1. **Dashboard + CRUD** — list charts, create one, edit, delete (hard wipeout), Open/Resume affordances.
2. **Layer Tower cockpit + SSE + Asset Inspector** — the centrepiece. Live Brahma-lexicon Layer Tower (Brahmagyan → Mīmāṃsā), push/SSE feed from `build_events`, click-into-asset Inspector showing data + provenance + gate verdict + live tool state.
3. **Progressive Consult + admin Brahmagyan view** — Consult capability gate that lights on Gaṇita; admin one-time Brahmagyan/L0 view at `/admin/foundation` (lower priority — deferrable if S1+S2 take longer than expected).

**Execution context — Claude Code extension in Google Antigravity IDE.** All commands paste-ready. Repo root `/Users/Dev/Vibe-Coding/Apps/Madhav`.

**Branch:** `feature/ws1-drivable-portal` cut from tag `legacy-cleanup-arc-complete` (commit `ccc66c77`). One PR for the whole wave; per-sub-stream commits (S1 / S2 / S3 + Step-0 + Step-0.5).

## §2 Sub-streams + paste-prompt schedule

Four paste prompts ship alongside this brief. Sequential within the wave; do not parallelize:

| Order | Paste prompt | Scope |
|---|---|---|
| **0** | `ANTIGRAVITY_PASTE_WS1_STEP0_MIGRATIONS.md` | Apply migrations 118/124/125/126/127 to prod; verify WS-0C-2 DEFERRED 55-hit residual resolves; commit any code touch-ups |
| **0.5** | `ANTIGRAVITY_PASTE_WS1_STEP0_5_BUILD_BLOCKER.md` | Diagnose + resolve the Turbopack/python-sidecar venv symlink pre-existing AC-3 blocker. Conditional — if `npm run build` for web already works, skip |
| **1** | `ANTIGRAVITY_PASTE_WS1_S1_DASHBOARD_CRUD.md` | Dashboard `ClientRoster`/`ClientCard` Open+Resume + state chip + layer pip rail; `NewClientForm` + ayanamsha-set selector; new edit page; delete dialog (hard wipeout) |
| **2** | `ANTIGRAVITY_PASTE_WS1_S2_COCKPIT_INSPECTOR.md` | Layer Tower component (Brahmagyan→Mīmāṃsā); SSE rail at `/api/build/events/[buildId]`; Asset Inspector panel; build state mapping `pyramid_layers` rows to L0–L5 bands |
| **3** | `ANTIGRAVITY_PASTE_WS1_S3_CONSULT_ADMIN.md` | Progressive Consult capability gate ("Consult now (Gaṇita)" affordance + planner-tool-set hint); admin one-time Brahmagyan view at `/admin/foundation` |

Step 0 ships now alongside this brief. S1 ships now too (it can start the moment Step 0 closes). Steps 0.5 / S2 / S3 paste prompts ship after their predecessors close so the brief can absorb anything CC surfaces along the way.

## §3 Shared rules across the wave

These apply to every paste prompt; do not restate in each.

- **Brahma lexicon enforced externally.** Per spec §0.1 + §14.1, every client-facing string uses Sanskrit + English from the lexicon table (Brahmagyan / Foundation, Gaṇita / Chart Facts, Bodha / Chart Intelligence, Kāla / Temporal, Phala / Prediction, Mīmāṃsā / Learning). L0–L5 strings, A1/A14/MSR codenames, and engine/swarm jargon **never** appear on a client surface. Super-admin/acharya surfaces (Pro DAG, Asset Inspector codename slot) may show internal jargon.
- **Extend the existing design system.** Per spec §0.4, reuse theme tokens, type scale, spacing, `CockpitShell` component family. New components define behavior + states + copy + layout — not new tokens.
- **Honesty over polish.** A thin / under-volume asset shows amber "built but thin" with the exact shortfall; a failed asset shows the failing gate. Never a green that overstates (§0.2).
- **Accessibility from day one.** Keyboard, screen-reader, reduced-motion, AA contrast in light + dark (spec §0.5 + §12).
- **Reverse-citation gate per destructive op** (durable rule). Step 0's migration apply, any file deletes, any env-var removes — gated on grep-verified-dead evidence before action.
- **PR-to-main is human-gated.** CC opens the WS-1 PR after all sub-streams commit; native reviews + merges.

## §4 Per-sub-stream summary

### §4.1 Step 0 — Migrations 118 / 124 / 125 / 126 / 127 / 133

Activates the build orchestrator schema completion the WS-0C-2 PR identified as DEFERRED. After Step 0:
- `builds`, `build_steps`, `build_events`, `build_notifications`, `notification_views`, `engine_versions` tables all exist in prod.
- The 55-hit DEFERRED residual from WS-0C-2 now resolves against a real schema.
- Cockpit SSE wiring (S2) can read from a complete build orchestrator state.

**Note on migration 133.** The initial brief listed only 118/124/125/126/127; during execution CC discovered that `notification_views` lives in migration 133 (`platform/migrations/_archive/133_notification_views.sql`), not in the prescribed five. Migration 133 is pure additive with an FK on `builds` (124, already applied), so it was applied as part of Step 0. The brief is amended in place to reflect this. Lesson: schema-dependency briefs need a "verify each promised table actually lives in the listed migrations" gate during authoring — codified as a small Cowork-side discipline going forward.

CC reads each migration file before applying, runs a dry-run if possible, applies one at a time with verification between each, and confirms post-apply schema. Hard stops on migration failure or schema unexpected-state.

### §4.2 Step 0.5 — Turbopack symlink blocker (conditional)

The build failure has been the same across WS-0B + WS-0C + WS-0C-2 — likely a python-sidecar `.venv` symlink Turbopack chokes on. The diagnostic is: run `npm run build` (web) in isolation; if it succeeds, the blocker is sidecar-only and Step 0.5 is skipped. If web build also fails, CC investigates the Turbopack error, applies the smallest fix that unblocks (likely a `next.config.ts` `experimental.outputFileTracingExcludes` entry or a `.next-ignore` pattern), and confirms `npm run build` exits 0 before S1 begins.

Without a working production build, S1/S2/S3 UI work can't deploy. So this is a real gate, not optional polish.

### §4.3 S1 — Dashboard + CRUD

Per spec §2 (S1 Dashboard), §3 (S2 Create), §4 (S3 Edit), §8 (Dialogs). Touches: `ClientRoster`, `ClientCard`, `NewClientForm`, new `/clients/[id]/edit` page, D1+D2 confirm dialogs, build-state derivation from `pyramid_layers` rows (re-based to L0–L5).

Most of S1 is extension of existing components. The genuinely new pieces are the layer pip rail (6-segment compact tower echo), the edit page (`/clients/[id]/edit`), and the cascade-rebuild confirm + hard-wipeout delete dialogs.

### §4.4 S2 — Cockpit + SSE + Asset Inspector

The centrepiece — the rest of the portal lives or dies by this one. Per spec §5 (Layer Tower), §6 (animation + event binding), §7 (Asset Inspector). Touches: new `LayerTower` component (bottom-up, Brahmagyan as permanent bedrock band, Mīmāṃsā as thin always-active band), re-based `OverallProgress` driving the band states, the SSE consumer hook reading `/api/build/events/[buildId]`, the `AssetInspector` right-panel component, the build-state SQL queries the inspector reads (row counts, sample data, provenance ledger, gate verdict).

S2 is also where DCB-001 (`kala_timeline` psycopg fix) and DCB-004 (`life_events` NOT NULL fix) from the original handoff §8 land — both are cockpit-adjacent one-liners that block clean SSE event emission.

### §4.5 S3 — Progressive Consult + admin Brahmagyan view

Per spec §9 (S6 Consult) + §10 (S7 Brahmagyan admin). Touches: `ConsumeChatV2` capability gate (only offer prompt suggestions the verified-layer tool set can ground), "Consult now (Gaṇita)" affordance on band verify, new `/admin/foundation` route for the one-time Brahmagyan build view.

S3 is deferrable if S1+S2 expand beyond budget. The admin Brahmagyan view in particular is used **once** by the platform owner (you) and never again — the spec marks it as lower priority. If WS-1 closes without S3, we open a small WS-1.5 to land it later.

## §5 Final WS-1 AC sweep (after all sub-streams commit)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# AC-1: lexicon enforcement — no L0–L5 strings client-facing
grep -rEn "\b(L0|L1|L2|L2\.5|L3|L4|L5)\b" platform/src/app platform/src/components \
  --include='*.tsx' 2>/dev/null \
  | grep -vE "(^//|/\*|\* |Pro|ProDAG|admin/)" \
  | head -20
# Expected: empty (or only Pro / super-admin surfaces — those are allowed)

# AC-11: production build clean
cd platform && npm run build 2>&1 | grep -E "(Compiled successfully|Failed to compile)" && cd ..

# AC-2/3/4/5/6/7/8/9: covered by per-sub-stream ACs + the curl smoke

# AC-12: CI green after push
git push origin feature/ws1-drivable-portal
gh pr checks <PR-number>
```

## §6 Commit + PR discipline

- One commit per Step / Sub-stream: Step-0 (migrations), Step-0.5 (build blocker if applicable), S1 (dashboard CRUD), S2 (cockpit + SSE + inspector), S3 (consult + admin if shipped).
- PR opens after the last shipped sub-stream lands. PR body includes:
  - Sub-stream commit list
  - Final AC scorecard (AC-1 through AC-12)
  - Curl smoke results (S2's tower update, S3's consult capability gate)
  - Any UX iteration notes for the design system
- Tag `ws1-drivable-portal-complete` after merge.

## §7 Out of WS-1 scope

| # | Item | Follow-up |
|---|------|-----------|
| 1 | Per-asset volume floors that drive the amber-vs-green gate | WS-2 — WS-1 reads whatever floor each asset's runtime_contract carries; WS-2 declares the actual floors |
| 2 | Rule Base extraction + grounded signals | WS-3 |
| 3 | Phala / Mīmāṃsā writer changes | WS-2 |
| 4 | Relational / Spatial modules | post-single-chart stack per master architecture §I.4 |
| 5 | Real Brahmagyan one-time build (the platform-owner action of bootstrapping L0 + GCP infra for the first time) | WS-1 S3 ships the *view*; the actual bootstrap is a one-off operator step the native runs once |
| 6 | The legacy Turbopack symlink in python-sidecar — if Step 0.5 confirms it's sidecar-only and not blocking web build | Bundler tooling ticket, separate session |

---

*End of CLAUDECODE_BRIEF_WS1_DRIVABLE_PORTAL v1.0. Step 0 + S1 paste prompts ship alongside. Steps 0.5 / S2 / S3 paste prompts authored after Step 0 and S1 close so the brief absorbs in-flight findings.*
