# Orchestrator Health Verify + L0 Build-Permission Enforcement (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first + memory `feedback-l0-build-permission-model` + `reference-cockpit-build-executor-gap`.**
Two linked goals: (A) PROVE the global build orchestrator + DAG traversal works correctly end-to-end across
layers; (B) IMPLEMENT the native's L0 authorization rule on the BUILD path (it exists for `clear` but NOT for
`runs` — the build/rebuild endpoint). The earlier "rebuild didn't work" was the executor-dispatch swallow (D1/D2,
already fixed), NOT a DAG bug — confirm that holds, then close the permission gap.

## STANDING RAILS
FROZEN orchestrator contract (HALT if a contract change seems needed — this is an AUTHORIZATION layer in the
route + a plan filter, NOT a writer/orchestrator change); L1-is-authority; endpoint-verify
(`/api/cockpit/stats?chart_id=...`, `/api/cockpit/runs/active?chart_id=...`); only mutate via the documented
routes; surgical migrations if any (≥ next free); branch-complete ≠ prod-true.

---

## PART A — ORCHESTRATOR + DAG HEALTH (verify, don't assume)

The DAG/plan logic (`platform/src/lib/build/plan.ts` `resolveBuildPlan`) is code-correct: topoSort with
cycle-detection, upstream/downstream closures, build/update/rebuild/cascade semantics. VERIFY it still behaves
correctly end-to-end on the live instrument for the native chart 482012f1:

1. **Single-asset rebuild executes** (the earlier failure case): trigger an asset-scope rebuild of a cheap L1
   asset (e.g. `ga_vastu`), confirm via `/api/cockpit/runs/active` it goes `planned → running → complete` with
   `started_at` non-null, and `/api/cockpit/stats` shows `last_built_at` advancing. (This proves D1/D2 holds —
   the dispatch no longer silently swallows.)
2. **Downstream cascade is correct**: rebuild an UPSTREAM asset (e.g. `ga_strength`) and confirm the plan/
   throughput marks its transitive downstream `stale` (per asset_runner's downstream-stale marking), and that a
   subsequent `update` at layer scope picks up exactly those stale assets — no more, no less.
3. **Topo order honored**: confirm a multi-asset plan lists dependencies before dependents (spot-check the plan
   array from `/api/cockpit/runs` response or build_run_assets.position).
4. **Cycle guard**: confirm `topoSort` still throws on a synthetic cycle (unit test exists — run it).
5. Report: does every build dispatched from the cockpit actually EXECUTE now (no `planned` phantoms left)? If any
   run stalls in `planned`, the D1/D2 fix regressed — flag it.

**Do NOT trigger a global or L0 build as part of this** (see Part B — L0 must stay built-once). Use L1 assets.

---

## PART B — L0 BUILD-PERMISSION ENFORCEMENT (NATIVE-LOCKED SPEC — build to exactly this)

**THE LOCKED MODEL (native clarifying-Q answers 2026-06-18 — do NOT re-decide):**
1. **Roles:** only `super_admin` + `client` exist (`db/types.ts: type Role = 'super_admin' | 'client'`).
   **Build the FULL client path NOW** — clients can build L1→L5, fully implemented + tested, even though no
   client users exist yet.
2. **L0 = GLOBAL SINGLETON, global-scope ONLY.** **NO chart_id EVER triggers an L0 build — not clients, not
   super_admin, NOT the native chart 482012f1.** L0 is built once at global scope; EVERY chart (native included)
   CONSUMES it. (This SUPERSEDES the earlier "global + native chart" phrasing — it is global-only for everyone.)
   super_admin builds/rebuilds/clears L0 ONLY at `scope='global'`. A build request that targets an L0/global
   asset with a per-chart intent is invalid regardless of role.
3. **L0-as-prerequisite = the EXISTING DAG dependency rule, NOT a new branch.** A client building an L1 asset
   whose L0 dependency isn't `lit` is already blocked by the orchestrator's dependency-readiness rule ("can't
   build an asset whose deps aren't built"). Do NOT add a parallel "foundation not ready" check — VERIFY the
   existing cross-layer (L1-needs-L0) dependency gate actually fires, and lean on it.
4. **Client "build everything"/global → SILENTLY drop L0/global from the plan**, **NO message, fully invisible**
   (mirror `clear`'s `filterScopeAssets` exactly). The client's L1-L5 per_chart assets build normally.
5. **Backend + UI TOGETHER.**

**CURRENT STATE (code-verified — fix the inconsistency):**
- `clear` + `clear/execute` (`platform/src/app/api/cockpit/clear/*`): ✅ ALREADY correct. Pattern to MIRROR:
  `getUserRole` → `isSuperAdmin` → `allowedScopes = isSuperAdmin?['per_chart','global']:['per_chart']`; reject
  non-super-admin when `scope='layer' && scope_target='brahmagyan'` OR asset is `scope='global'`
  (403 `FORBIDDEN_L0`); `filterScopeAssets` strips disallowed-scope assets from the plan.
- `runs` (`platform/src/app/api/cockpit/runs/route.ts`): ❌ WRONG — gates the WHOLE endpoint on
  `role==='super_admin'` → blocks ALL non-super-admin builds (incl. L1-L5) and has no L0/global guard. **Fix this.**

**THE FIX — port the `clear` authorization model onto the `runs` build path (NOT a contract change):**
1. Replace `requireSuperAdmin()` in `runs/route.ts` with `requireUser()` + `getUserRole()` (any authenticated
   user may POST a build), THEN enforce (mirror `clear`):
   - **L0 layer guard:** non-super-admin + `scope='layer' && scope_target='brahmagyan'` → 403 `FORBIDDEN_L0`.
   - **L0/global asset guard:** non-super-admin + `scope='asset'` where `asset_registry.scope='global'`
     → 403 `FORBIDDEN_L0`.
   - **L0 is global-scope-only for EVERYONE:** an L0/global asset may only be built at `scope='global'`. A build
     whose plan would include an L0/global asset under a per-chart scope is invalid even for super_admin (L0 is a
     singleton — no per-chart L0). In practice: L0/global assets enter a plan ONLY via `scope='global'`; the
     native chart never gets its own L0 build.
   - **Silent L0 drop for non-super-admin global/layer builds:** filter the resolved plan through the same
     allowed-scope logic `filterScopeAssets` uses, so a client's "build global"/"build layer" plan EXCLUDES all
     L0/global assets with NO message and builds only their per_chart L1-L5 assets. A client must never get an
     L0 asset into a `build_run` plan.
   - **Do NOT add a "foundation not ready" check** — rely on the existing DAG dependency-readiness gate (point 3).
2. Apply the SAME guard to any OTHER mutating build route lacking it (audit `refresh` — read-only cache-invalidation,
   confirm it can't trigger an L0 write; pause/resume/stop are run-control, super_admin-only is acceptable).
3. **UI (do in THIS effort — native chose backend+UI together):** hide/disable the L0 Brahma Jñāna layer's
   Build / Rebuild / Clear controls for non-super-admin (the cockpit currently shows them for everyone). Backend
   403 is the real boundary; the UI change removes the "button that 403s." Confirm super_admin still sees all L0
   controls.

**Tests (REQUIRED — security boundary):** add route tests asserting:
- super_admin CAN build L0 at `scope='global'`.
- super_admin building an L0/global asset under a per-chart scope (incl. native 482012f1) → rejected
  (L0 is global-singleton; no per-chart L0 for anyone).
- non-super-admin (`client`) building `scope='layer'/brahmagyan` → 403 FORBIDDEN_L0.
- client building a `scope='global'` asset → 403 FORBIDDEN_L0.
- client building `scope='layer'/ganita` (or bodha…) on their chart → ALLOWED; plan = only per_chart L1-L5,
  ZERO L0/global assets.
- client "build global" → plan SILENTLY EXCLUDES all L0/global assets (NO message), builds only their per_chart
  assets.
- DAG prerequisite: a client L1 build whose L0 dependency is not `lit` is blocked by the existing dependency
  gate (NOT by a bespoke check) — assert the orchestrator refuses it.

---

## DELIVERABLE + VERIFY (paste evidence)
- Part A: the cheap-L1-rebuild executed end-to-end (runs/active planned→running→complete + stats last_built_at
  advanced); cascade-stale correct; topo order honored; cycle guard test green; ZERO `planned` phantoms.
- Part B: `runs` route now enforces the LOCKED L0 model (diff); the security tests above green (incl. the silent
  client-global-drop + the DAG-prerequisite case); UI hides L0 Build/Rebuild/Clear for non-super-admin (super_admin
  still sees them); full suite green; confirm via the endpoints that a super_admin L1 build still works (no
  regression for the native). Paste the test names + the role-matrix result, not "verified".
- FROZEN contract untouched (HALT-flag if it would change); migrations (if any) ledger-reconciled.

**WHY THIS MATTERS NOW:** the rule is currently LATENT (single-native + super-admin-only product) but becomes
load-bearing the instant a second user or a second chart exists ([[project-multichart-platform-rebuild]]) — which
is exactly what full Prashna ("any querent") and the broader instrument need. Closing it now, while the surface
is small, is far cheaper than after multi-chart lands. It also makes the `clear`/`runs` authorization model
CONSISTENT (right now they disagree — a latent-bug smell).
