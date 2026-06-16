---
artifact: CLAUDECODE_BRIEF_L0_L1_CLOSURE_v1_0.md
canonical_id: L0_L1_CLOSURE_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (Chrome-MCP + code-plane forensic read) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, NO human gate between phases (native directive 2026-06-12). Only dependency gates + Tier-3 escalation rails (genuine ambiguity / destructive op / architecture change) pause execution. Native reviews retrospectively via cockpit/Atlas + Smṛti.
data_plane: ALWAYS prod via Cloud SQL proxy (port 5433)
scope_intent: >
  FINISH L0 (Brahmagyan) + L1 (Gaṇita) completely before ANY orchestrator/L2 Bodha (B5) work.
  Native directive 2026-06-16: "address all the pending issues with layer 0 and layer 1 ... progress
  bars are not updating appropriately. Let's fix that first. Also, call out what other shortcomings/
  issues that you see in layer 0 and layer 1." This brief is that closure pass.
governing: MARSYS_CONSOLIDATED_RUNWAY_v1_1 (§1 group D L1-tail) + L0_L1_SENSEMAKING_AUDIT_v1_1 + CLAUDE.md §N
key_finding: >
  The "progress bars not updating" is NOT a server/stats bug — it is the v2 build cockpit's CLIENT-side
  SSE overlay (DataAssetsView.tsx) shadowing the polled /api/cockpit/stats truth. The overlay is
  written on every SSE event but NEVER cleared on terminal state or run-end, and the merge does
  `overlay.state ?? stats.state` so the overlay wins permanently. If the terminal `lit` SSE event is
  missed (the 5s poll/SSE race the code itself flags), the bar freezes on `building`/partial-rows
  forever — even though stats (with the floor-gate fix) now correctly returns `lit`. All prior
  server fixes are real but invisible behind this sticky overlay.
inherited_non_negotiables: >
  deterministic-first; no audience tier ([[feedback-no-audience-tier]]); NO silent drops (errors
  shown/flagged, never hidden); per-chart isolation by chart_id; real fact_id references (never mock);
  count_sql is data-truth (§N.4); floors aspirational (target_floor = achieved after build, NEVER a
  gate); FROZEN orchestrator contract (no orchestrator change); surgical migrations only, FRESH
  unused numbers (we have had 223/227 collisions — check the ledger before picking a number).
---

# L0 + L1 Closure — Fix Brief v1.0

## §0 — How to run this brief
ONE brief, SIX phases (P1 the progress-bar bug → P2–P6 the L0/L1 shortcomings tail). Implement
**phase-by-phase, continuously** — finish a phase, verify it against prod, proceed WITHOUT waiting
for human sign-off. Stop only on a real dependency miss or a Tier-3 event. PR-per-phase is fine if
cleaner; just don't gate on the native between phases.

**The build cockpit being fixed is the one reached from a jātaka's `Nirmāṇa` button:
`/clients/[id]/build` → `CockpitShell` → `DataAssetsView` → `LayerPanel`/`AssetRow`. It is the v2
cockpit; it polls `/api/cockpit/stats` (count_sql) + `/api/cockpit/registry` and overlays SSE. It is
NOT the `/cockpit` governance landing page (that one reads a stale GCS `build-state.json` — out of
scope here, see §7).**

---

## PHASE P1 — Progress bars not updating (the priority fix)

### P1.0 — Live root cause (read before editing)
`platform/src/lib/components/cockpit/v2/DataAssetsView.tsx`:
- `sseOverlay` (a `Map<asset_id, Partial<AssetWithState>>`, line ~58) is **written** on every
  `asset.state_change` (sets `state`) and `asset.progress` (sets `actual_rows`) SSE event
  (handlers lines ~63–90) — and is **NEVER cleared**. There is no `delete`/`clear` anywhere.
- The merge (lines ~110–119) computes
  `state: overlay?.state ?? s?.state ?? 'dormant'` and
  `actual_rows: overlay?.actual_rows ?? s?.actual_rows ?? null`.
  → **the overlay UNCONDITIONALLY shadows the polled `/api/cockpit/stats` value.**
- `run.state_change` (line ~87) only calls `refreshRun()`; it does **not** clear the overlay.

**Consequence:** once an asset gets any SSE event, its overlay entry is permanent. If the terminal
`lit` `state_change` is missed (the code's own comments at lines ~51–52 and ~231 admit the 5s
poll/SSE timing race for fast assets), the bar is frozen on the last thing SSE said — `building` or
a partial `rows_written` — and the corrected polled stats can never re-take it. **This is "the
progress bars don't update."** It is purely client-side; the stats API + deriveState are already
correct after the floor-gate fix.

### P1.1 — FIX: make the SSE overlay terminal-aware (the overlay must yield to polled truth)
The overlay should exist ONLY to show *live in-flight* progress; once an asset reaches a terminal
state or the run ends, the polled `/api/cockpit/stats` (count_sql, authoritative per §N.4) must win.
Implement BOTH clears:

1. **Clear on terminal `asset.state_change`.** In the `asset.state_change` handler, if `e.to_state`
   is terminal (`lit` / `error` / `dormant` — i.e. NOT `building`/`stale`/in-progress), **delete**
   that asset's overlay entry instead of setting it. That hands the asset back to polled stats
   immediately, which now returns the correct `lit`.
   ```ts
   if (e.type === 'asset.state_change') {
     setSseOverlay(prev => {
       const next = new Map(prev)
       const TERMINAL = e.to_state === 'lit' || e.to_state === 'error' || e.to_state === 'dormant'
       if (TERMINAL) next.delete(e.asset_id)          // yield to polled stats (count_sql truth)
       else next.set(e.asset_id, { ...prev.get(e.asset_id), state: e.to_state })
       return next
     })
   }
   ```
2. **Clear ALL overlays on run end.** In `run.state_change`, when `e.state` is terminal
   (`complete`/`failed`/`stopped`/`cancelled` — match the RunState enum), `setSseOverlay(new Map())`
   AND `setSubstepOverlay(new Map())` in addition to `refreshRun()`. After a run ends, the polled
   stats are the single source of truth; no overlay should survive it.
   ```ts
   } else if (e.type === 'run.state_change') {
     refreshRun()
     const RUN_DONE = ['complete','failed','stopped','cancelled'].includes(e.state)
     if (RUN_DONE) { setSseOverlay(new Map()); setSubstepOverlay(new Map()) }
   }
   ```
3. **Safety net — force one stats re-poll on run end** so the cleared overlay is immediately
   backfilled with fresh truth (don't wait up to 30s). `useActiveRun`/`useAssetStats` already exist;
   trigger a refetch of stats when the run transitions to a terminal state (e.g. expose a
   `refetch()` from `useAssetStats` and call it in the `RUN_DONE` branch, or flip the
   `isBuilding=false` path to re-poll once immediately).

### P1.2 — Verify the deriveState floor-gate fix is actually live on this surface
The bars also depend on `/api/cockpit/stats` `deriveState()` returning `lit` for assets with rows>0.
Confirm Fix A from DERIVESTATE_FLOOR_GATE_FIX (rows>0 + not-actively-building → `lit`, floors NEVER
gate) is merged AND deployed to the environment the native views. If migration 231 (reset the 4 bg_
floors to achieved) is not yet applied to prod, apply it (fresh number if 231 is taken — check
ledger).

### P1.3 — Acceptance [verify-against: prod + localhost:3000]
- [ ] On `/clients/[native-id]/build`, every L0 + L1 asset with data shows a filled/`lit` bar — none stuck on `building` or a partial count after a build ends.
- [ ] Force the race: trigger a build, let an asset's terminal SSE event be dropped (or just wait for run end) → the bar still converges to `lit` from polled stats within one poll cycle.
- [ ] `sseOverlay` has zero entries after `run.state_change` terminal; merge falls through to polled stats.
- [ ] No regression to LIVE in-flight progress: during an active build, `building` + climbing `actual_rows` still render from the overlay (the overlay still works *during* the build).
- [ ] L0 reads 12/14 lit, L1 all ga_ lit, on the build cockpit (matching the Atlas/registry).

---

## PHASE P2 — Rahu/Ketu strength + the ga_strength stubs (real L1 silent gaps)
Per L0_L1_SENSEMAKING_AUDIT §2, `ga_strength` has genuine completeness defects (NOT scope choices):
- **Rahu/Ketu get NO strength row at all.** Emit shadbala/AV/vimsopaka for the nodes (or, where a
  classical method genuinely doesn't define a value for the nodes, emit a row flagged
  `not_defined_for_nodes` — NO silent absence).
- **kala-bala hardcoded to daytime** — compute from the actual birth (10:43 IST = day birth for the
  native, but must be derived, not hardcoded, for multi-chart correctness).
- **drik-bala stubbed at 0.375** — implement the real drik-bala (aspectual strength) computation, or
  flag the row as `documented_approximation` with the stub value visible (no silent stub).
- Acceptance [verify-against: prod]: ga_strength returns strength rows for Rahu+Ketu (real or
  flagged); kala-bala derives from birth day/night; drik-bala is computed OR explicitly flagged;
  count_sql reflects the new rows; ga_strength stays `lit`.

## PHASE P3 — KP cuspal significators silent-drop (ga_sensitive, no-silent-drop)
Per RUNWAY D1: KP cuspal significators are **silently dropped** when their source JSON is malformed.
Fix the JSON parse OR store a flagged skip-row (`skipped: malformed_source`) so the drop is VISIBLE,
never silent (B: no silent drops). Acceptance: a malformed-JSON case produces a flagged row or a
logged+surfaced skip, not silent absence; well-formed cases produce the cuspal significators.

## PHASE P4 — Scope-cap sentinels (absence ≠ bug)
Per RUNWAY D3: several L1 scope caps are documented in markdown but have **no DB marker**, so
"missing" is indistinguishable from "intentionally-not-computed." Add an explicit
`intentionally_not_computed` sentinel row (or a registry flag) for each known cap so the cockpit +
the retrieval layer can tell scope-cap from bug:
- Prana dasha (dasha level-5) — not emitted by ga_dashas (documented cap).
- KP dasha levels 6/7 — collapsed (documented cap).
- D81 varga — skipped by ga_vargas (documented cap).
- Outer-planet + per-varga MC floors in ga_vargas — currently floored *silently*; add the flag.
- Lal-Kitab / Nadi sensitive points in ga_sensitive — floored-with-flag already; confirm the flag is queryable.
- Acceptance: each cap has a queryable sentinel; the retrieval layer (Wave 3) can surface
  "intentionally not computed" distinctly from "no data."

## PHASE P5 — `ganita_positions` legacy dual-write deprecation
Per RUNWAY D2: `ga_positions` dual-writes to the legacy `ganita_positions` table (obsolete vs
chart_facts). **This is a destructive-adjacent op — Step 0.5 reverse-citation gate REQUIRED**
([[feedback-destructive-brief-reverse-citation-gate]]): before removing the dual-write or the table,
grep ALL live code (src + python-sidecar + scripts + tests + SQL views) for every reference to
`ganita_positions`; reclassify any with active citations as KEEP-OR-REPOINT. Only after zero live
citations remain, remove the dual-write from `ga_positions` and drop the table via a surgical
migration (fresh number). If ANY live citation exists, repoint it to chart_facts first.
- Acceptance: zero live `ganita_positions` citations remain; dual-write removed; chart_facts is the
  sole positions store; no FORENSIC regression (7/7 still passes); migration has a fresh number.

## PHASE P6 — Cockpit-truth consistency sweep (close the recurring divergence class)
The recurring failure has been prod registry/throughput silently diverging from seed/code intent
(four cycles). After P1–P5, run ONE consistency sweep so all three asset surfaces agree:
- For every L0 (bg_) + L1 (ga_) asset, confirm `/api/cockpit/stats` (count_sql), `/api/cockpit/
  registry`, the build cockpit (`/clients/[id]/build`), and the Atlas all report the SAME state +
  count. Any asset with rows>0 showing `building`/`stale`/`dormant`/`NOT MIGRATED` on ANY surface is
  a divergence to fix at the source (correct count_sql, or reap the orphaned throughput record).
- Confirm the seed-apply hardening (C1: post-apply DB readback + assertions, no silent
  state-mutating rules like the line-1248 auto-deactivate) is in force so this doesn't recur.
- Acceptance [verify-against: prod]: all four surfaces agree per asset; no rows>0 asset shows a
  non-lit state on any surface; seed-apply hardening asserts post-state == intended.

---

## §7 — Out of scope (named so it's not silently skipped)
- **The `/cockpit` governance landing page** (stale GCS `build-state.json`, ~7 weeks old, bucket
  mismatch `madhav-marsys-build-artifacts` vs publisher's `marsys-jis-build-state`). It is a SESSION/
  governance dashboard, not the asset cockpit; the native is looking at the `Nirmāṇa` build cockpit
  (§P1). Decision on whether to revive the GCS publisher vs repoint that page is DEFERRED to the
  native — do NOT touch it in this brief.
- **L2 Bodha / B5 orchestrator build** — explicitly deferred until L0/L1 closure (this brief) lands.
- **Retrievability Wave 3** — the scope-cap sentinels (P4) feed it, but building the retrieval tools
  is its own wave; not here.
- **No ga_structural re-amendment** (complete at 53,953 rows).
- **No new yoga/dosha/remedy corpus authoring** (the bg_ subset gaps are honest scope-curation per
  the audit, resolvable by authoring later — not defects to fix here).

## §8 — The L0/L1 shortcomings, as one list (the native's "call out what else" ask)
For the record, the complete L0/L1 issue inventory from the sense-making audit + runway, with
disposition:
1. **Progress bars sticky-overlay** (P1) — the priority; client-side, now fixed.
2. **Rahu/Ketu no strength; kala-bala daytime-hardcode; drik-bala 0.375 stub** (P2) — real L1 gaps.
3. **KP cuspal significators silent-drop on bad JSON** (P3) — no-silent-drop violation.
4. **Scope caps without DB sentinels** (P4) — Prana dasha, KP 6/7, D81, outer-planet/MC floors.
5. **`ganita_positions` legacy dual-write** (P5) — technical debt, gated reverse-citation removal.
6. **Cockpit-truth divergence class** (P6) — the recurring seed↔prod drift; consistency sweep + hardening.
7. **bg_ corpus subsets** (bg_rules 8.1% yield, bg_yogas 175/250, bg_remedies/concordance partial) —
   NOT defects; honest, flagged scope-curation; resolvable by later authoring; NOT in this brief.
8. **Native-binding** (birth params + FORENSIC gates hardcoded into L1 writers) — fine for the
   single-native phase; must parameterize per chart_id for the multi-chart goal; a later-layer concern.
9. **Concurrent-dasha-lords denormalized jsonb** (ga_dashas) — rebuild drift-risk; watch, not urgent.

---
*End of L0_L1_CLOSURE v1.0. The "bars don't update" bug is the v2 build cockpit's sticky SSE overlay
shadowing the corrected polled stats (DataAssetsView.tsx — overlay never cleared on terminal/run-end).
Fix: terminal-aware overlay (delete on terminal state, clear-all on run-end, force a stats re-poll).
Then close the real L1 tail: Rahu/Ketu strength + ga_strength stubs, KP silent-drop, scope-cap
sentinels, ganita_positions dual-write (reverse-citation-gated), and a cockpit-truth consistency
sweep. The /cockpit governance page + L2 Bodha are explicitly deferred. No ga_structural re-touch.*
