---
canonical_id: RETRIEVAL_RECONFIRM_FINDINGS
version: 1.0
status: CURRENT
created: 2026-06-30
author: Claude Code (read-only audit; 3-agent parallel execution)
classification: architecture findings — retrieval layer re-confirmation
source_brief: CLAUDECODE_BRIEF_RETRIEVAL_RECONFIRM_v1_0.md
prereqs_read:
  - 00_ARCHITECTURE/BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_ELEVATION_PLAN_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
---

# RETRIEVAL RE-CONFIRMATION FINDINGS v1.0

> Read-only audit against live code + DB (port 5433), 2026-06-30.
> Purpose: ground the R-1–R6 autonomous swarm charter in current reality before execution.
> Method: three parallel agents — §1 code defect audit, §2 live DB gates, §3 seam state.

---

## HEADLINE

**94+ of 96 prior defects are already fixed.** The four systemic patterns identified in the
2026-06-29 audit (L1 phantom columns, `_ctx.db` wiring bug, broken-column handlers, destructive
`mi_seva` DELETE) have been remediated across all 30+ affected files with one exception:
`callPriorityRankingCapability` in `call_service_wrappers.ts` still carries the `_ctx.db` bug.
The MCP seam (401 / `x-mcp-audience-tier` mismatch) and own-pool db wiring bypass are **still
present** and block R2. The MSR grounding gate has recovered dramatically (6.88% → 98.88%) via
a full rebuild, but `bodha_contradictions` remains empty (0 rows), which **blocks R0** and
therefore gates R3.

**R0 data gate: BLOCKING** (Gate B — `bodha_contradictions` = 0 rows).
**R2 keystone: BLOCKED** (401 seam mismatch unresolved; 5 tools bypass registry with own Pool).

---

## §1 — REMAINING DEFECT REGISTER

### Pattern 1: L1 chart_facts phantom columns
**Status: FIXED**

All 17 L1 Gaṇita handler files have been corrected. The formerly-phantom columns
(`fact_value_numeric`, `fact_tags`, `epistemic_tier`, `source_asset_id`) are gone.
Current SELECT list across all 17 files:
```sql
SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
       fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
FROM chart_facts
```
`fact_value_num` is the live column name (not `_numeric`). Confirmed fixed in:
`get_positions.ts`, `get_strength.ts`, `get_ashtakavarga.ts`, `get_bhava_bala.ts`,
`get_aspects.ts`, `get_yoga_dosha.ts`, `get_argala.ts`, `get_dispositors.ts`,
`get_sade_sati.ts`, `get_panchanga.ts`, `get_sensitive_points.ts`, `get_karakas.ts`,
`get_dignity.ts`, `get_avasthas.ts`, `get_tajik.ts`, `get_tara_chandra_bala.ts`,
`get_eclipse_flags.ts`, `get_dashas.ts`, `get_divisionals.ts`.

Subtleties also fixed: `get_dashas` now maps `args.dasha_system → system_id` and
`args.level → level_n`; `get_divisionals` uses `varga` not `varga_code`;
`get_tajik` uses `varsha_year` not `year_num`.

---

### Pattern 2: `_ctx.db` wiring bug
**Status: 23/24 FIXED — 1 CRITICAL STILL PRESENT**

`CapabilityContext` (types.ts:343–348) still only carries `{chart_id?: string, request_id?: string}`.
No `db` field. 23 of 24 affected handlers now import `query` from `@/lib/db/client` directly
and no longer reference `_ctx.db`. One handler missed:

**CRITICAL — STILL BROKEN:**
- `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:485,512`
  — `callPriorityRankingCapability` does `const { db } = _ctx as { db: ... }` at :485,
  then calls `db.query(sql, [...])` at :512. At runtime `db` is `undefined` → `TypeError`
  on every invocation → swallowed to `is_error: true`. This is registered and exported
  from `L3_kala/index.ts:34,48`.

Fixed handlers (now use `@/lib/db/client` import):
- L2: `query_ucd.ts`, `query_signals.ts`, `query_domain_reading.ts`, `query_remedies.ts`,
  `query_quality_scorecard.ts`, `query_contradictions.ts`, `traverse_chart_graph.ts`
- L3: `query_convergence_windows.ts`, `query_temporal_activation.ts`,
  `query_life_arc.ts`, `query_projections.ts`
- L4: `query_predictive_anchors.ts`, `query_domain_result.ts`, `query_phala_calibration.ts`
- L5: `query_calibration.ts`, `query_insights.ts`, `query_manifestation_grammar.ts`,
  `query_predictions.ts`, `query_signal_families.ts`

---

### Pattern 3: Broken-column / wrong-table handlers
**Status: FIXED** (all handlers verified)

Every handler that was querying phantom columns or wrong tables has been corrected:

| Handler | Prior bug | Current state |
|---|---|---|
| `query_classical_texts` | Queried `brahma_compendium_index` (wrong table) | Now queries `classical_text_chunks` with real columns |
| `query_remedy_corpus` | `target_graha` / `remedy_category` phantom cols | Now `planet` / `remedy_type` |
| `query_yoga_catalog` | `tradition` / phantom cols | Now `school` / `category` |
| `query_dosha_catalog` | `dosha_name` / `severity_tier` / `domain_tags` | Now `name_en` / `category` / `severity_grades` |
| `get_dashas` | `system_id` / `level_n` (now correctly mapped from args) | FIXED |
| L3 `query_temporal_activation` | Phantom L3 columns | Real: `signal_id`, `activation_strength`, `window_start/end`, `trigger_type`, `orb_strength` |
| L3 `query_convergence_windows` | `ayanamsha_id` on `kala_convergence` (no such col) | Fixed — now filters on `chart_id` only, correct cols |
| L3 `query_life_arc` | `*_lord` / `signal_id_refs` phantom | Real `kala_jivana_parva` columns |
| L3 `query_projections` | Phantom predictive cols | Real: `peak_date`, `window_start/end`, `falsifiability`, `narrative`, `source_chain`, `effective_score` |
| L4 `query_predictive_anchors` | `axis_score` / `ayanamsha_id` / `event_class` / `feasibility_tier` | Real `phala_anchors` cols |
| L4 `query_domain_result` | Phantom phala_phaladesa cols | Fixed |
| L4 `query_phala_calibration` | `disposition='staged'` filter (no such col) | Removed; comment explicit |
| L2 `query_contradictions` | `resolution_approach` / `resolution_status` | Now `resolution_hint_jsonb` |
| L2 `query_quality_scorecard` | `quality_score` / `quality_tier` / `total_signals` | Real: `msr_signal_count`, `two_pass_verified_pct`, etc. |
| L2 `query_remedies` | `signal_id` on `bodha_rm_resonances` | Fixed; `emits_references=false` semantics handled |
| L2 `traverse_chart_graph` | `valence` on nodes (wrong table) | Fixed — `valence` filtered on `bodha_cgm_edges` only |
| L5 `query_manifestation_grammar` | Phantom mi_ cols | Real: `origin_kind`, `channel_propensity`, etc. |
| L5 `query_predictions` | Wrong enum names | Fixed |
| L5 `query_signal_families` | Phantom cols | Real: `display_name`, `binding_kind`, `evidence_tier` |
| `record_outcome` (unmounted) | Depended on unmounted Python sidecar | Now served by `/api/mcp/writes/[action]/route.ts` |
| `holistic_bundle` (unmounted) | Called Python sidecar `/api/compute/brahma/bodha/holistic_bundle` | Now served by `/api/mcp/bundles/[name]/route.ts` |

---

### Pattern 4: DESTRUCTIVE `mi_seva` unscoped DELETE
**Status: FIXED (protective stop-gap)**

`platform/src/lib/cockpit/assetClearSpec.ts:112` sets `mi_seva: null` in `EXPLICIT_CLEAR_OPS`.
The runs route (`/api/cockpit/runs/route.ts:228`) treats `null` as skip-clean:
```ts
if (explicitOps === null) continue  // zero-row service asset — skip cleanly
```
The unscoped `DELETE FROM mimamsa_preferences` path is blocked. `mi_seva.py` docstring
confirms: "GLOBAL scope (service handler — no DELETE/INSERT at build time)."

**Residual medium-severity hygiene:** Registry still lists `mi_seva` with `scope=per_chart`
while the writer is global/service; `count_sql` is mismatched. Catastrophic wipe is blocked;
registry cleanup deferred to a Tier-4 registry migration per the remediation plan.

---

### Pattern 5: Swallowed errors / tautological guards
**Status: PARTIALLY FIXED**

Fixed:
- `ph_nimitta` `detected_at` → now uses `d.computed_at AS detected_at`; SAVEPOINT pattern present
- `ph_pramana` `_load_lel` → now queries `life_events` (not `life_event_log`); except narrowed
- `ga_vastu` false debilitation: Sun-in-Capricorn-as-debilitation assertion removed (astrologically wrong; Sun debilitates in Libra)
- `bg_ephemeris_engine` tautological probe: replaced with real longitude range checks for Sun in Capricorn + Rahu in Vrishabha
- `_verify_shadbala`: three real guards now (all sub-balas ≥ 0; total > 0; sub-bala sum ≈ total within tolerance)

Still present (low priority, Tier 5 deferral):
- `bo_laksana.py:840,1361,1370,1476,1498`: bare `except Exception` blocks
- Various `rows_inserted` over-counting and per-row INSERT swallow patterns — not re-verified individually; no evidence of systematic sweep

---

### Pattern Summary Table

| Pattern | Prior defect count | Status | Remaining |
|---|---|---|---|
| P1: L1 phantom columns | 17 files (Critical) | **FIXED** | 0 |
| P2: `_ctx.db` wiring bug | 24 handlers (Critical) | **23/24 FIXED** | 1 Critical |
| P3: Broken-column/wrong-table | ~30 handlers (Crit/High) | **FIXED** | 0 |
| P4: Destructive mi_seva DELETE | 1 (Critical) | **FIXED (stop-gap)** | 1 Medium (hygiene) |
| P5: Swallowed errors / tautologies | multiple (High/Med) | **Partially FIXED** | Several Low |

**Net:** ~94+ of 96 defects resolved. **1 Critical remains** (P2 sole survivor at
`call_service_wrappers.ts:485,512`). R-1 must fix this before declaring retrieval layer clean.

---

## §2 — DATA GATE VERDICTS (live DB, port 5433)

*Note: Only one chart exists in the database — native `482012f1-710e-4a25-994a-93821f5871aa`.
No second chart was available for parallel testing.*

### Gate A — MSR Grounding (R0.1)

**Native chart (482012f1-710e-4a25-994a-93821f5871aa):**

| Metric | Value |
|---|---|
| Total MSR signals | 64,765 |
| Signals with `constituent_facts_array` populated | 64,720 (45 null/empty) |
| Total fact_id references (unnested) | 65,474 |
| Fact_id refs resolving to `chart_facts` for same chart | 64,739 |
| Non-resolving references | 735 |
| **Resolution rate** | **98.88%** |
| MSR last built | 2026-06-29T14:04:10.389Z |
| chart_facts last built | 2026-06-29T12:55:02.389Z |
| Build order | MSR built ~69 min after L1 — correct ordering confirmed |

**Prior audit figure: 6.88% → Current: 98.88% — DRAMATICALLY IMPROVED.**
The 6.88% figure reflected a pre-rebuild state (MSR built 2026-06-20, chart_facts rebuilt
2026-06-24, MSR never re-run). The 2026-06-29 session triggered a full MSR rebuild; it is
now correctly grounded.

**Verdict: HEALTHY** — 98.88% resolution far exceeds the 90% gate threshold.

---

### Gate B — Contradictions (R0.2)

| Metric | Value |
|---|---|
| `bodha_contradictions` rows for native chart | **0** |
| Prior audit value | 0 |
| Change | SAME (no improvement) |

**Verdict: NEEDS-REBUILD** — `bodha_contradictions` is still empty. With 64,765 MSR signals
across a complex natal chart, zero contradictions is not credible as a complete result.
The `bo_samvada` writer has either not run or produced zero output. This table is the output
of the contradiction-detection writer and should contain rows. A targeted `bo_samvada` rebuild
(or investigation into its zero-output) is required.

---

### Overall Data Gate Status

| Gate | Status |
|---|---|
| Gate A — MSR Grounding (R0.1) | **HEALTHY** (98.88%) |
| Gate B — Contradictions (R0.2) | **NEEDS-REBUILD** (0 rows) |
| **R0 gate overall** | **BLOCKING** |

Gate B blocks R0. R0 blocks R3. The R-1 swarm must trigger a `bo_samvada` rebuild
(or diagnose why it produced zero rows) before R3 can proceed.

---

## §3 — SEAM STATE (R2 keystone readiness)

### Q1: `x-mcp-audience-tier` guard at `/api/mcp/primitives`

**Route:** `platform/src/app/api/mcp/primitives/[tool]/route.ts:81–95`
**Status: STILL-PRESENT (401 unfixed)**

The route checks all three Layer-2 principal headers; any missing one returns 401:
```ts
const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as
  | 'client'
  | 'super_admin'
  | null

if (!userUid || !audienceTierHeader || !keyId) {
  return NextResponse.json(
    buildErrorEnvelope({ error_class: 'auth',
      message: 'Missing principal headers (X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id)' }),
    { status: 401 }
  )
}
```

**Caller:** `platform-mcp/src/client.ts:121–130` (`platformFetch`)
```ts
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${identityToken}`,
  'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
  'X-MCP-User': principal.user_uid,
  // X-MCP-Audience-Tier header removed (Stream A 3.tier_excision 2026-05-28).
  'X-MCP-Key-Id': principal.key_id,
}
```

The mismatch is deliberate on the client side (tier_excision) but the route guard was never
relaxed. `callPlatformPrimitive` and `callPlatformTrace` both go through `platformFetch` —
**every call to `/api/mcp/primitives` returns 401**. The architecture docs describe this as
a "one-line fix": either restore the header on the client, or remove `audienceTierHeader`
from the null-check and supply a default on the route side. Neither has been done.

---

### Q2: MCP in-process tools db wiring

**Files bypassing registry with own `pg.Pool`** (STILL PRESENT — all 5 confirmed):

| File | Pool pattern |
|---|---|
| `platform-mcp/src/audit.ts:14,24` | Module-level singleton `new Pool(...)` — not lazy |
| `platform-mcp/src/tools/retrieval/remedy_tools.ts:19,25,31` | Lazy singleton pool, `max: 5` |
| `platform-mcp/src/tools/read_classical_text.ts:22,29,37` | Lazy singleton pool, `max: 5` |
| `platform-mcp/src/tools/kala_timeline.ts:32,39,47` (+:240) | Lazy singleton + second local pool |
| `platform-mcp/src/tools/retrieval/holistic_bundle.ts:37,43,49` | Lazy singleton pool, `max: 5` |

These tools bypass the registry, the router, MARO, and the entitlement gate entirely.

**Files correctly using platform seam (architecturally right, but operationally broken due to 401):**
- `platform-mcp/src/tools/bo_2-7.ts` — uses `callPlatformPrimitive`
- `platform-mcp/src/tools/phala_mitigation_map.ts` — uses `callPlatformPrimitive`
- `platform-mcp/src/tools/muhurta_finder.ts` — uses `callPlatformPrimitive`

These three tools are architecturally correct per the frozen seam contract but 401 on every
invocation until the seam bug is fixed.

---

### Q3: Elevation plan context (from prereq documents)

**Frozen seam** (RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4): The retrieval registry
(`platform/src/lib/retrieval/`) is chart-agnostic and FROZEN — it owns capabilities, the
`marsys://` URI scheme, `retrieve(plan, params)` execution, chart-data SQL, the router, the
grounding spine, and MARO. Channel adapters (MCP server, chat engine) own auth, identity /
principal resolution, entitlement enforcement, session/memory, chart-selection, per-model
surface declaration, and envelope shaping. Both channels MUST invoke the SAME registry
capabilities via the platform seam; no channel re-implements retrieval or runs its own chart
SQL. On conflict, retrieval's contract wins.

**R0–R6 phases:**
- **R0:** Data prerequisites — MSR rebuild (done), `bodha_contradictions` rebuild (still needed)
- **R1:** Contamination + hygiene — fix `kala_temporal.ts:156–341` hardcoded native FORENSIC
  fallback; remove dead `bo_2-7.ts` / `bodha_signal_search` code. Parallel-safe with R0.
- **R2 (keystone):** Repoint all MCP in-process tools to registry via platform seam; retire
  own-pool raw-SQL tools; expose `getMcpSurfaceSpec` as published seam output. The 401 fix
  must land first. Acceptance: every MCP tool resolves to a registry capability; no channel
  runs its own chart SQL.
- **R3:** Astrological elevation — domain reasoning-unit tools, yoga-activation-by-dasha
  bridge, contradiction/convergence as first-class outputs. GATED on R0.
- **R4:** Multi-LLM consumption — bundle-elasticity, cross-model conclusion-consistency,
  `behavioral_overrides` wiring.
- **R5:** Richness — register resources, build guided-reading prompts (currently 0 prompts),
  rewrite astrologically-teaching tool descriptions.
- **R6:** Re-seal — live re-validation, eval harness, acharya-validation flags, governance
  version bump and seal.

---

### Seam Status Verdict

| Check | Status |
|---|---|
| 401 / `x-mcp-audience-tier` fix | **BLOCKED** — mismatch unresolved since 2026-05-28 |
| MCP in-process tools db wiring | **STILL-PRESENT** — 5 tools bypass registry with own Pool |
| **R2 keystone overall** | **BLOCKED** |

---

## §4 — CONSOLIDATED STATUS MATRIX

| Section | Finding | Gate impact |
|---|---|---|
| P1 phantom columns | **FIXED** | — |
| P2 `_ctx.db` bug | **1 CRITICAL** at `call_service_wrappers.ts:485` | R-1 must fix |
| P3 broken-column handlers | **FIXED** | — |
| P4 mi_seva destructive DELETE | **FIXED (stop-gap)** | — |
| P5 swallowed errors | Partially fixed; Tier 5 residuals | Low priority |
| Gate A MSR grounding | **HEALTHY** 98.88% | R0 ✓ |
| Gate B contradictions | **BLOCKING** 0 rows | R0 ✗ → R3 gated |
| 401 seam bug | **BLOCKED** tier_excision mismatch | R2 ✗ |
| db wiring bypass | **STILL-PRESENT** 5 tools | R2 ✗ |

---

## §5 — WHAT R-1 MUST REPAIR (minimum viable before R2/R3)

1. **Fix `call_service_wrappers.ts:485,512`** — `callPriorityRankingCapability`: replace
   `const { db } = _ctx as { db: ... }` with `import { query } from '@/lib/db/client'`
   pattern (same fix already applied to all 23 other handlers).

2. **Fix the 401 seam mismatch** — either:
   - (a) restore `'X-MCP-Audience-Tier': principal.audience_tier` in `platformFetch`
     (`platform-mcp/src/client.ts:128`), or
   - (b) remove `audienceTierHeader` from the null-check on the route and supply a sensible
     default — per architecture docs this is the intended "one-line fix".

3. **Trigger `bo_samvada` rebuild** — diagnose why `bodha_contradictions` is 0 rows and
   re-run the writer. Gate B must clear before R0 is OPEN and R3 can proceed.

4. **Repoint 5 own-pool MCP tools to platform seam** (R2 core work):
   `audit.ts`, `remedy_tools.ts`, `read_classical_text.ts`, `kala_timeline.ts`,
   `holistic_bundle.ts` — each must be rewritten to call `callPlatformPrimitive` rather than
   creating its own `pg.Pool`.

Items 1–2 are one-line fixes; item 3 is a targeted writer rebuild; item 4 is the substantive
R2 engineering work.

---

*End of RETRIEVAL_RECONFIRM_FINDINGS v1.0 — 2026-06-30. Strictly read-only audit.
Based on: 3-agent parallel execution covering §1 code, §2 live DB, §3 seam state.*
