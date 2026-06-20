---
artifact: BODHA_BUILD_CONTEXT_HANDOFF_v2_0.md
canonical_id: BODHA_BUILD_CONTEXT_HANDOFF
version: 2.0
status: CURRENT
authored_by: Cowork 2026-06-19
supersedes_as_entry_point: BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md (v1.0 still valid for §2-§6; this doc updates the STALE parts + adds the post-rebuild reality)
purpose: >
  SELF-CONTAINED entry point for a FRESH Cowork conversation that will author the build specs for
  every L2 Bodha asset. Read THIS doc first, then the canonical docs it cites — you need no prior
  conversation history. It carries: the now-COMPLETE foundation Bodha sits on (post-2026-06-19
  ga_structural v2.0 rebuild + PR #301 merge), the locked L1↔L2 architecture, the design philosophy,
  the 8-asset DAG + spec→table map, every locked decision, the anti-drift traps, and the first move.
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
---

# L2 Bodha — Build Context Handoff v2.0 (post-foundation-seal entry point)

## §0 — How to use this doc (read order)

You are in a fresh Cowork conversation whose job is to **author the build specs for each L2 Bodha
asset** (Cowork = plan/author; Claude Code in Antigravity = execute — never write code here, only
pasteable briefs/specs). Read in this order:

1. **THIS doc** — the current reality + what changed since the v1.0 handoff.
2. `00_ARCHITECTURE/BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md` — the prior handoff. **§2 (locked L1↔L2
   architecture), §3 (design philosophy), §4 (8-asset DAG + spec→table map), §5 (locked decisions),
   §6 (the two traps) are ALL STILL AUTHORITATIVE — read them.** Its §1 (ga_structural keystone) and
   §7 (prod baseline) are STALE — THIS doc §2 + §4 replace them.
3. `00_ARCHITECTURE/L2_BODHA_MASTER_PLAN_v3_0.md` — the dual-capture model + phase plan (L1-E → B1 →
   B2 fan-out → B3 → B4 → B5 → B6 eval-gate). The build sequence.
4. `00_ARCHITECTURE/L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0.md` — the per-asset Asset↔Table↔Brief map (which
   spec, which `bodha_*` tables, which depends_on, which brief to author per asset).
5. **Always verify live state from `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` + `git log origin/main` +
   the prod DB, NOT from any frozen doc** (this one included). The seed→prod path has diverged before.

**Standing project rule:** Cowork plans; Claude Code in Antigravity executes. Every output of the new
conversation must be a pasteable brief or a committed `.md` spec — never chat bullets the user must
translate. Data plane is ALWAYS prod via the Cloud SQL proxy (port 5433); localhost is code-plane only.

---

## §1 — WHAT CHANGED since the v1.0 handoff (the delta — this is why v2.0 exists)

The v1.0 handoff was authored 2026-06-16. Between then and 2026-06-19, a full session rebuilt the
keystone and merged the foundation. The new conversation MUST know this, because the v1.0 §1 describes
a ga_structural that no longer exists:

- **ga_structural was REBUILT to v2.0** (build_id `a712b250`, **106,103 rows**, 72 categories, FORENSIC
  7/7). The v1.0 handoff describes the *prior* 77,821-row build — that number and its category list are
  STALE. See §2 below for the current keystone reality.
- **PR #301 MERGED to main** (HEAD `e6be443e`, 2026-06-19). It carries: ga_structural v2.0, the L0
  build-permission model (guest builds L1-L5, L0 super_admin-global-only), the auth `guest` role fix
  (canonical non-admin role = `guest`, NOT `client` — "client" is a chart SUBJECT, not a user role),
  Prashna L1 activation, the pre-L2 foundation close-out, and cockpit cosmetic fixes.
- **Migrations through ~324 are on main** (311–324 landed this session: ga_structural floors/count_sql,
  ga_prashna, cockpit cosmetics, auth). VERIFY the exact max migration on prod before authoring any new one.
- **A pre-L2 hygiene pass ran** — working tree clean; off-disk stash work salvaged to
  `recovery/pre-l2-stash-salvage`; 5 agent worktrees removed. The 6 `feature/subsystem-*` worktrees
  REMAIN (the 7-subsystem program, gated behind L2 — not Bodha's concern now).
- **Every pre-L2 gate is CLEARED.** ga_structural is L1-authority-clean (all refs resolve), graph-theoretic
  layer present and per-varga, contradiction_pair de-inflated, no silent drops, all designed Phase-3
  categories populated-or-documented. Bodha opens on a verified hub.

---

## §2 — THE KEYSTONE (UPDATED): ga_structural v2.0 — what Bodha actually reads now

**This REPLACES v1.0 handoff §1.** `ga_structural` is the complete deterministic relational fabric and
the single most important input to Bodha. Current reality (build `a712b250`, verified
`GA_STRUCTURAL_REBUILD_VERIFY_v2_0.md`):

- **106,103 rows, 72 fact_categories, all 30 vargas × 5 ayanamshas**, Rahu/Ketu in every loop. Every
  relationship recomputed from each varga's OWN computed positions (degree-based, uniform).
- **Graph-theoretic layer present + per-varga** (this was the big v2.0 fix — the old build had it D1-only
  or dropped): `graha_centrality`, `dispositor_tree`, `chart_cluster`, `chart_center_of_gravity`,
  `convergence_count`, `karaka_bhava_concordance` — all now per-varga. Plus `significator_path`
  (BFS on dispositor graph), `virupa_drishti` (continuous graded aspect strength), `sambandha_grade`,
  `bhava_significance_link`, `net_argala_per_varga` — all across 30 vargas.
- **L1-AUTHORITY storage location (CRITICAL for Bodha):** constituent fact_id references live in
  **`fact_value_jsonb["constituent_fact_ids"]`**, NOT in a `constituent_facts_array` column — that
  column DOES NOT EXIST in chart_facts (`_CF_INSERT_COLS` excludes it; a prior version silently dropped
  refs written to it). **Any Bodha writer that reads ga_structural's references MUST read them from
  `fact_value_jsonb.constituent_fact_ids`.** They are real, resolvable fact_ids (verified to JOIN to
  source rows). This is the anti-drift spine (Trap 1) — Bodha references, never restates.
- **Modeling-assumption flag:** graha_yuddha + combustion are computed in varga space and carry
  `value_jsonb["varga_assumption"]` — they are structurally consistent but classically these are
  physical-sky phenomena; Bodha/serve-time should respect the flag (these rows carry no classical
  authority for non-D1 vargas).
- **Retrieval nuance (UNCHANGED from v1.0, still true):** "all of D1's structural facts" = base
  categories ∪ the D1 slice of `_per_varga` categories. A query filtering only `%_per_varga` UNDER-COUNTS
  D1. Bodha's projection must union both.
- **Disambiguation (UNCHANGED):** every row is fully qualified by varga + sign + ayanamsha + houses/
  degrees. The same graha-pair in D1 vs D9 are DISTINCT rows.
- **Known follow-on (does NOT block Bodha, but Bodha should be aware):** `vimsopaka_bala_per_graha` +
  `graha_saptavargaja_bala_component` reference the source via `constituent_fact_ids` pointing at
  `chart_divisionals` row UUIDs (fixed this session). If a Bodha asset reads vimsopaka, those resolve.

**The dual-capture consequence for bo_laksana:** MSR projects the WHOLE of L1 — ga_structural's relational
surface AND the individual L1 value-assets at native grain (so both the relationship value and each fact's
individuality are captured). See L2_BODHA_MASTER_PLAN_v3_0 §2-§3. One-surface is NOT a goal.

---

## §3 — The Bodha design philosophy (UNCHANGED — read v1.0 §3 + the memory)

Authoritative source: v1.0 handoff §3 + memory `feedback-l2-bodha-design-philosophy`. In brief (do not
treat this summary as the spec — read the source):
- **L2 = deterministic leverage over L1 atoms.** Within-chart structural statistics only (cross-chart → L5).
- **Convergence + contradiction are first-class.** "Rich pre-computed relational INGREDIENTS; the LLM
  synthesizes at query-time" — Bodha does NOT pre-answer questions; it assembles the deterministic
  ingredients an LLM composes from at serve-time.
- **Every judgment is a versioned deterministic formula.** No human/LLM judgment in which signals fire or
  how strong. No narrative in the asset (interpretation is serve-time only).
- **The graph is where to invest hardest** (CGM — bo_bimba nodes + bo_karanajala edges).
- **Three-tier relational boundary (memory `feedback-three-tier-relational-boundary`):** 1 entity no
  meaning → L1 value-asset; 2+ entities + fixed rule + NO life-meaning → ga_structural; 2+ entities +
  LIFE-MEANING/domain/salience → L2 MSR. The line is "fact vs meaning," not "simple vs complex." Bodha is
  where meaning is assigned to ga_structural's meaning-free relationships.

---

## §4 — The 8-asset DAG + spec→table map (UPDATED prod baseline)

Authoritative per-asset map: `L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0.md`. The 8 `bo_` assets (asset-id grain;
one writer may populate many `bodha_*` tables, like ga_dashas):

| asset | sanskrit | what | depends_on | build batch |
|---|---|---|---|---|
| `bo_laksana` | Lakṣaṇa | MSR signal store (`bodha_msr_signals`) — projects WHOLE of L1 | `['ga_structural','bg_rules']` | **Batch 1 (root, first)** |
| `bo_sangati` | Saṅgati | CDLM domain links (`bodha_cdlm_cells` + rollups/clusters/gradients) | `['bo_laksana']` | Batch 2 |
| `bo_bimba` | Bimba | CGM nodes (`bodha_cgm_nodes` — centrality/pagerank/768-vec) | `['bo_laksana']` | Batch 2 |
| `bo_karanajala` | Kāraṇajāla | CGM edges (`bodha_cgm_edges` + sub_graphs/motifs/paths/contradictions) | `['bo_laksana']` | Batch 2 (deepest) |
| `bo_samskara` | Saṃskāra | signal embeddings (`bodha_signal_embeddings`, Vertex AI 768-dim) | `['bo_laksana']` | Batch 2 |
| `bo_upaya` | Upāya | RM remediation (owns `bodha_rm_resonances` + 5 tables, 6 traditions × 18 cats) | `['bo_laksana','bo_sangati']` | Batch 3 |
| `bo_samvada` | Saṃvāda | UCD digest — **Option A read-side view** (`vw_chart_digest` + `query_ucd`), NOT a writer | `['bo_laksana']` | Batch 2 (read-tool spec, not writer) |
| `bo_pramana_mapa` | Pramāṇa-māpā | synthesis-quality scorecard (global, `synthesis_quality_scorecard`) | `[]` | Batch 3 |

**Build sequence (L2_BODHA_MASTER_PLAN_v3_0 §9):** L1-E (already done — ga_structural v2.0 IS the L1-E
enrichment) → **B1 `bo_laksana`** (must pass B1.4+B1.5 before fan-out) → B2 fan-out (sangati, bimba,
karanajala, samskara, + samvada read-tool) → B3 (upaya, pramana_mapa) → B5 orchestrator+cockpit+retrieval
tools → B6 semantic-completeness eval harness (GATES the seal).

**2 seed fixes PENDING (verify on prod, apply before/with the relevant batch)** — per
`L2_BODHA_ASSET_TABLE_BRIEF_MAP §2` + `CLAUDECODE_BRIEF_BODHA_P0E_SEED_CORRECTION`:
1. `bo_upaya` seed → re-point to OWN `bodha_rm_resonances` (primary) + summed count_sql across 6 tables.
2. `bo_samvada` seed → clear off `bodha_rm_resonances`; set to UCD/Option-A (view, no per-chart table).
**VERIFY whether these were already applied** (check the seed on main + prod) before re-authoring.

**Prod-verify before building (the seed→prod path has diverged before):** confirm the `bodha_*` spec
tables exist at full schema (migrations 224/226/230 + any later) and that main == prod. Use
`/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa` (underscore param) for asset state.

---

## §5 — Locked decisions + traps (UNCHANGED — read v1.0 §5 + §6, do NOT relitigate)

All of v1.0 handoff §5 (locked decisions 1–8) and §6 (the two traps) STILL HOLD verbatim. The load-bearing ones:
- Table naming `bodha_*`; LOCKED A10–A14 rich multi-table specs win over the coarse 8-row seed; `bo_samvada`
  = Option A read-side; Phase-0 = REPOINT-NOT-DROP (reverse-citation check before retiring any legacy
  table — `bodha_signals` has a live reader in `consult/route.ts`); **G52 predicate registry ELIMINATED**
  (do NOT build signal_type_registry as a prerequisite); no audience tier; deterministic-first (Python over
  LLM; embeddings OK, generative-LLM-for-curation NOT).
- **Trap 1 (anti-drift spine):** an L2 signal NEVER restates an L1 computed value — it REFERENCES the L1
  `fact_id` (now in `fact_value_jsonb.constituent_fact_ids`, see §2) and inherits L1's value. Derivation
  disagreeing with the cited L1 fact = HALT, it's a bug. FORENSIC-anchored signals inherit L1 values
  (Muntha = Libra/7H/Venus, never re-derived).
- **Trap 2:** no human/LLM judgment leaks into which signals fire or their strength — versioned
  deterministic formulas only; no narrative in the asset.
- **FROZEN orchestrator contract:** every Bodha writer is a `@register('bo_*')` WriterBase subclass on
  `ctx.db_conn` (never commits/closes), never writes asset_throughput, gets chart_id+birth_params from
  ctx.config. If a writer SEEMS to need a contract change → STOP and raise with the native.

---

## §6 — The first move + what "authoring the specs" means

The new conversation's deliverable is **a per-asset build spec/brief for each `bo_` asset**, authored in
dependency order, each pasteable to Claude Code in Antigravity. Concretely:

1. **Open with B1 `bo_laksana`** — the MSR projection of the whole of L1 (ga_structural v2.0 relational
   surface ∪ individual L1 value-assets at native grain). This is the root; everything else depends on it.
   The existing `CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0.md` + `CLAUDECODE_BRIEF_BODHA_B1_v1_0.md`
   are PRIOR drafts — reconcile them against the NEW ga_structural v2.0 reality (the 106,103-row,
   jsonb-fact_id, graph-theoretic-present hub) before finalizing. The projection must union base ∪
   D1-per_varga and read refs from `fact_value_jsonb.constituent_fact_ids`.
2. **Then B2 fan-out specs** (sangati/CDLM, bimba+karanajala/CGM graph — invest hardest here, samskara/
   embeddings, samvada/UCD read-tool).
3. **Then B3** (upaya/RM, pramana_mapa/scorecard).
4. Each spec: the `bodha_*` table schema(s) it populates, the deterministic formulas (versioned), the
   constituent_fact_id references it carries, its place in the DAG, and its verification (per-category /
   resolution / acharya checks — NOT raw counts).
5. **B6 eval harness gates the seal** — semantic completeness, not per-table coverage. L2 is not "done"
   until B6 passes.

**Verification discipline (carry this in — it's the lesson of the whole L0/L1/ga_structural arc):** verify
against PROD + per-category evidence + acharya correctness, NOT "tests pass" and NOT raw row counts. A
higher number with spurious/missing rows is worse than a correct smaller one. Every "complete" claim gets
checked against the actual data before it's believed.

---

## §7 — Canonical docs to load in the new conversation (the full set)

Foundation/context: `BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md` (§2-§6), this doc (v2.0).
Plan: `L2_BODHA_MASTER_PLAN_v3_0.md`, `L2_BODHA_BUILD_CAMPAIGN_v1_0.md`, `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md`.
Per-asset map: `L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0.md`.
Architecture/decisions: `L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md`, `L2_5_STRUCTURED_LAYER_v1_0.md`.
Keystone proof: `GA_STRUCTURAL_REBUILD_VERIFY_v2_0.md` (what ga_structural actually contains now).
Prior B1 drafts (reconcile, don't blindly reuse): `CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0.md`,
`CLAUDECODE_BRIEF_BODHA_B1_v1_0.md`, `CLAUDECODE_BRIEF_BODHA_L1E_GA_STRUCTURAL_ENRICHMENT_v1_0.md`.
Traps: `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`, `MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`.
Live state (ALWAYS): `CURRENT_STATE_v1_0.md` + `git log origin/main` + prod DB via the proxy.

*End BODHA_BUILD_CONTEXT_HANDOFF_v2_0 — hand this to the new Cowork conversation as the entry point. It
points to the authoritative docs and carries the post-2026-06-19 reality those docs predate.*
