---
artifact: L4_PHALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md
canonical_id: L4_PHALA_AUTONOMOUS_EXECUTION_PLAN
version: 1.0
status: AUTHORED — the autonomous execution plan for the L4 Phala swarm
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
parent_plan: 00_ARCHITECTURE/L4_PHALA_CAMPAIGN_PLAN_v1_0.md
governs: 00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml
role: >
  The end-to-end autonomous execution plan for L4 Phala. Reuses AUTONOMY_RESILIENCE_PATTERN +
  BUILD_GUARANTOR_SWARM_CHARTER (do not reinvent). Contains the closing-review gap analysis,
  the retrieval-tool plan, the wave sequence, the cross-cutting gates, and the HARD seal gate.
---

# L4 Phala — Autonomous Execution Plan v1.0

## §1 — Inputs (read in order)
1. `L4_PHALA_AUDIT_v1_0.md` — the code-verified reality + the three handoff corrections.
2. `L4_PHALA_CAMPAIGN_PLAN_v1_0.md` — the 6-asset design + DAG + ratify gates.
3. The 6 per-asset briefs: `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L4_PH_*.md`.
4. `L3_KALA_CLOSE_v1_0.md §9` (ratified params, inherited) + `§11` (onboarding contract).
5. `00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml` — the wave queue (walk top-to-bottom).
6. Framework (reuse): `AUTONOMY_RESILIENCE_PATTERN_v1_0.md`, `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`.

## §2 — Pre-fan-out (the Conductor does these ONCE before any agent spawns)
- **PRE-1 — prod==main gate.** Confirm `origin/main` HEAD == deployed Cloud Run revision; L3
  migrations applied on prod (`kala_*` tables present, ka_* assets lit). HARD — do not proceed if red.
- **PRE-2 — pre-allocate migrations (THE TWO-174 TRAP).** Confirm the global max migration number
  across **BOTH** `platform/migrations/` AND `platform/supabase/migrations/` (expect 329).
  Pre-allocate L4 numbers **330–335** in DAG order, ALL in `platform/supabase/migrations/`:
  330 phala_anchors (+ DROP kala_timeline, CF.L3.2) · 331 phala_muhurta · 332 phala_mitigation ·
  333 phala_rectification · 334 phala_rectification_best · 335 phala_outlook. HARD.
- **PRE-3 — pin ratified params read-only.** I-7/I-8/I-11/I-16/I-17 are RATIFIED (L3_KALA_CLOSE §9).
  Any "re-pick a weight" impulse = STUB+log (canonical-or-floor rule), NEVER a native halt.
- **PRE-4 — register ph_phaladesa.** Add the 6th asset row to `asset_registry_seed.ts` (brief §4).

## §3 — Wave sequence
```
P1  ph_nimitta — SPINE-FIRST HARD GATE.
    Prove ONE anchor end-to-end (real ka_sangam window → calibrated anchor → falsifier →
    cites real convergence_id+signal_id → anti-drift clean) BEFORE P2 dispatches.
    NATIVE-RATIFY: G-LADDER (the f(convergence_score) confidence mapping) — HALT for sign-off.

P2  (parallel, disjoint files) ph_muhurta · ph_pratikara
    Both blocked_by ph_nimitta (spine); parallel_safe_with each other.

P3  ph_sodhana — PyJHora-computed rectification.
    NATIVE-RATIFY: G-RECT (PyJHora compute_ascendant as rectification oracle) — HALT.
    If withheld → scored-framework fallback (does NOT block the layer).

P4  ph_suddha_sodhana — argmax over ph_sodhana; holdout verification state (not used in selection).

P5  ph_phaladesa — composite dossier (reads P1–P4 + ka_tulana). B.11 GATE: must compose all sub-assets.

SEAL  (§6)
```

## §4 — Closing review: gap analysis (the holistic step-back)
Reviewing the 6-asset set as a whole, against "what must the applied-prediction layer deliver":

1. **Coverage is complete for the consumer question-space.** Anchors (what/when/falsifier),
   muhūrta (when-should-I), mitigation (what-to-do-about-adversity), rectification (is the chart even
   right), and the composite dossier (the one read). No obvious applied product is missing.
2. **No calibration leak into L4.** Verified: `ph_suddha_sodhana` reports verification STATE but does
   NOT calibrate; `ph_nimitta` emits falsifiers but does not score itself. Calibration stays L5. Clean.
3. **The cross-links are real, not decorative.** ph_pratikara can borrow ph_muhurta's best start
   dates for remedy timing; ph_phaladesa prioritizes via ka_tulana; ph_sodhana's Lagna verdict
   conditions every house-placement-dependent anchor. These are noted in the briefs.
4. **One watch item — Lagna-conditioning order.** ph_nimitta's house-based domain mapping assumes the
   sealed Aries Lagna (FORENSIC 7/7). ph_sodhana could in principle revise it. RESOLUTION: ph_sodhana
   is a SEPARATE hypothesis product; it does NOT mutate the canonical chart (B.10 — no chart rewrite
   without native + version bump). If rectification ever overturns Aries, that is a native-gated
   re-derivation event, not an automatic L4 cascade. Documented so the swarm does not "helpfully" rewire.
5. **Floors-aspirational confirmed everywhere** — every brief sets `target_floor` = achieved count
   post-build; none fabricates rows. ph_muhurta/ph_phaladesa are horizon-derived (representative count).
6. **Legacy disposition is clean** — the harvest manifest (AUDIT §4) is mapped per asset; the legacy
   `l4_*.py` / `brahma_phala_*.sql` / `platform-mcp/phala_*.ts` are reference-only and should be
   tombstoned (not deleted in this build — a separate cleanup, to avoid a destructive-brief reverse-
   citation miss). Note for a follow-up: confirm nothing live imports the legacy modules before removal.

## §5 — Retrieval (how the instrument serves L4 outputs)
L4 serves through the existing retrieval-layer registry (tools/resources/prompts; no tier gating;
all route through the Whole-Chart-Read protocol — L2 synthesis first). New tools to register:

| Tool | Reads | Returns |
|---|---|---|
| `query_phala_anchors(chart_id, window, domain?, min_confidence?)` | phala_anchors | calibrated anchors + falsifiers in window |
| `find_phala_muhurta(chart_id, action_class, window)` | phala_muhurta | ranked auspicious windows, danger-demoted |
| `query_phala_mitigation(chart_id, window)` | phala_mitigation | timed remedies (begin_by) for active obstructions |
| `query_rectification(chart_id)` | phala_rectification_best | the chosen Lagna + confidence + verification state |
| `phala_outlook(chart_id, horizon)` | phala_outlook | the B.11 composite dossier (headline + actionables) |

Each tool reads stored `phala_*` rows (no recompute at serve time). The dossier tool is the primary
native-facing surface. Retrieval registration is a thin post-build wave (P6, optional within this
campaign or a fast follow); it does not gate the seal.

## §6 — The SEAL (autonomous, AI-assessed) — with the HARD visual gate
1. **HARD VISUAL COCKPIT GATE (the #1 L3 lesson — burned ~4×).** Confirm the deployed Cloud Run
   revision == the merge SHA; load the LIVE cockpit Phala panel; confirm **SIX assets lit** with real
   non-zero counts and **zero error/missing_table**. A green `/api/cockpit/stats`, a swarm "SEALED"
   report, or a correct fix on an unmerged branch are ALL false positives. Verify the VISUAL surface
   (prod AND localhost), not just the JSON.
2. Anti-drift final audit: grep every ph_* writer → zero non-phala writes, zero `.commit()/.rollback()`;
   all derivation ledgers resolve to real ka_*/bo_*/ga_* ids.
3. PROD-VERIFY every AC against prod (Cloud SQL Auth Proxy), not a worktree DB. FORENSIC 7/7 holds.
4. Promote all ph_* DRAFT→CURRENT. Set every `target_floor` = achieved count.
5. Author `L4_PHALA_CLOSE_v1_0.md` (+ the L5 Mīmāṃsā onboarding contract). Update `CURRENT_STATE` +
   `SESSION_LOG`. Merge to main + push (CI-green is a gate). Vimarśaka final audit (temporal +
   anti-drift). Log to `00_ARCHITECTURE/CONDUCTOR/l4-phala/smriti/`.

## §7 — Cross-cutting gates (every asset)
- **Frozen contract:** grep the writer for `ctx.db_conn.commit()/.rollback()` → MUST be ZERO.
  `WriterResult(asset_id=, rows_inserted=)` — note `rows_inserted` (L3 BUG-3).
- **Anti-drift:** references kala_*/bodha_*/ga_* ids + L1 fact_ids; never restates; ZERO writes outside `phala_*`.
- **PROD-VERIFY:** ACs verify against prod, not a worktree DB (Brahma V1.3 lesson).
- **count_sql:** `$1` binding (never `$$CHART_ID$$` — L3 BUG-1).
- **FORENSIC:** the 7 birth anchors hold; only chart `482012f1`.
- **Model policy:** Gemini/DeepSeek (Anthropic banned unless native asks).
- **Native input:** Tier-3 catastrophic-budget ceiling + the two NATIVE-RATIFY gates (G-LADDER, G-RECT)
  ONLY (async, resumable). Nothing else pauses.

---
*End of L4_PHALA_AUTONOMOUS_EXECUTION_PLAN v1.0. Closing review + retrieval + waves + the HARD visual seal gate.*
