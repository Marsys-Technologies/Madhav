---
artifact: L0_BRAHMAGYAN_BUILD_MASTER
canonical_id: L0_BRAHMAGYAN_BUILD_MASTER
version: 2.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE (multi-session execution)
native: Abhisek Mohanty
supersedes: v1.0 (phase β/γ/δ/ε/ζ/η sequencing)
v2_0_changes:
  - Restructured from incremental phases to unified-build campaign
  - One outcome: native presses "Build" at Brahmagyan layer → all 12 L0 assets populated to or beyond design targets
  - Each asset gets a fully-specified brief with classical content embedded inline (no executor judgment calls on data)
  - Author-all-briefs-first model: zero execution until all 15 documents complete
  - Targets are FLOORS, not ceilings — Vimarśaka fails if any writer ships below target
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1 deterministic-only)
predecessor_phases:
  - Phase α — SEALED via PR #225 (12 assets registered, 14 tables provisioned)
  - Phase β — SHIPPED via PR #227 (writer infrastructure + thin bg_reference/bg_ontology slices that DO NOT meet design targets; superseded by v2.0 briefs)
locked_decisions:
  - ZERO LLM use anywhere in L0 construction; embeddings as deterministic transform permitted (Vertex AI text-multilingual-embedding-002, used only by bg_texts)
  - Targets are floors: Vimarśaka fails any asset that ships below target
  - All 15 briefs authored before any execution begins
  - One PR for the entire campaign (orchestrator fixes + 12 writers + integration verification)
  - Native presses "Build" at Brahmagyan layer; orchestrator dispatches in dependency order; all 12 assets transition dormant → building → lit autonomously
---

# L0 Brahmagyan Unified Build Campaign — Master Plan v2.0

## §0 — The outcome we're building toward

**Single click on "Build" at the Brahmagyan layer in cockpit → all 12 L0 assets autonomously populate to or beyond their design-target row counts, deterministically, with full source citation, and the cockpit transitions all 12 tiles from dormant to lit without further native intervention.**

This is the only acceptance criterion that matters. Everything in this master plan + the 14 supporting briefs serves that outcome.

## §1 — Why v2.0 (vs the incremental v1.0)

**v1.0 (Phase α → β → γ → δ → ε → ζ → η)** optimized for incremental review gates between phases. It produced Phase β shipping 102 bg_ontology entries vs the holistic design's 700-1,000 target — an honest scoping failure that v2.0 corrects.

**v2.0** authors EVERY brief before any execution begins. Each brief contains:
- The exact target floor (Vimarśaka fails if writer produces below target)
- Classical content embedded inline (Python data structures the executor copy-pastes, not synthesizes)
- Source citations sourced and verified by Cowork
- FK validation rules
- Asset-specific Vimarśaka checks

This eliminates the failure mode where the executor delivers a thin slice and the brief technically passes.

## §2 — The 12 L0 assets and their targets

These targets are FLOORS. Vimarśaka-Ω fails the entire campaign if any asset is below floor.

| # | Asset | Backing | Target floor | Source category |
|---|---|---|---|---|
| 1 | `bg_ephemeris` | `ephemeris_daily` | 825,084 rows | Algorithmic (Swiss Ephemeris compute; already populated from L0FR) |
| 2 | `bg_reference` | 15 typed tables | ~2,000 rows total across 15 tables | Embedded classical data (BPHS + Saravali + Phaladeepika + Taittiriya Aranyaka) |
| 3 | `bg_texts` | `classical_text_chunks` | 8,193 chunks (13 texts, actual build 2026-06-09; replaces 14,000/15-text projection) | Source PDFs in GCS |
| 4 | `bg_ontology` | `brahma_ontology` | ≥700 entities across 15 classes | Embedded classical data |
| 5 | `bg_text_index` | `classical_text_chunks WHERE topic_tag NOT NULL` | ≥400 distinct topic_tags | Deterministic Python keyword-rule classifier |
| 6 | `bg_rules` | `sutravali_rules` | ≥1,755 rules (3,000 × 8,193/14,000; old floor projected off 14k chunks) | Python regex extraction from bg_texts |
| 7 | `bg_remedies` | `brahma_remedy_corpus` | ≥800 remedies | Embedded classical data (BPHS Ch.91-94 + Phaladeepika Ch.27 + Mantra Mahodadhi + Lal Kitab) |
| 8 | `bg_concordance` | `classical_attributions` | ≥800 chunk-pointer rows | Deterministic Python topic × school matching |
| 9 | `bg_yogas` | `brahma_yoga_catalog` | ≥250 yogas | Embedded classical data (BPHS Ch.30-35 + Saravali + Phaladeepika + Jaimini) |
| 10 | `bg_dasha_systems` | `brahma_dasha_systems` | ≥15 dasha systems | Embedded classical data (BPHS Ch.46-50 + Jaimini) |
| 11 | `bg_doshas` | `brahma_dosha_catalog` | ≥50 doshas | Embedded classical data |
| 12 | `bg_compendium_index` | `brahma_compendium_index` | ≥1,755 index rows (3,000 × 8,193/14,000; Pass B scales with chunk count) | Deterministic Python aggregation over bg_texts |

**Sum target: ~840,000+ rows of source-cited classical content.**

## §3 — Dependency DAG (orchestrator dispatch order)

The orchestrator must execute writers in this order. Within each tier, writers can run in parallel.

```
Tier 0 (no L0 dependencies):
  bg_ephemeris (algorithmic; idempotent re-populate; ~825K rows)
  bg_reference (15 typed tables; pure classical data)
  bg_ontology  (entity vocabulary; pure classical data)

Tier 1 (depends on bg_ontology):
  bg_yogas         (each yoga.canonical_id must exist in bg_ontology)
  bg_dasha_systems (each dasha.canonical_id must exist in bg_ontology)
  bg_doshas        (each dosha.canonical_id must exist in bg_ontology)

Tier 2 (depends on Tier 0 + ingested PDFs):
  bg_texts (ingests 15 PDFs from GCS; produces chunks + embeddings)

Tier 3 (depends on bg_texts):
  bg_text_index (deterministic topic_tag classifier; updates classical_text_chunks.topic_tag column)
  bg_rules      (Python regex extraction over chunks; cross-references bg_yogas / bg_dasha_systems / bg_ontology)
  bg_remedies   (embedded data; some entries cross-reference bg_doshas)

Tier 4 (depends on Tier 3):
  bg_concordance     (per topic × school, store source_chunk_ids[] + rule_ids[])
  bg_compendium_index (per text × chapter + per text × topic_tag aggregations)
```

The orchestrator's layer-level "Build" handler reads this DAG, dispatches Tier 0 writers in parallel, waits for completion, dispatches Tier 1 in parallel, etc.

## §4 — The 15 documents in this campaign

| # | Document | Authoring session | Status |
|---|---|---|---|
| 1 | `L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md` (this file) | Session 1 | THIS DOC |
| 2 | `CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0.md` | Session 1 | **DONE** (native-approved 2026-06-08) |
| 3 | `CLAUDECODE_BRIEF_BG_EPHEMERIS_v1_0.md` | Session 1 | **DONE** (native-approved 2026-06-08) |
| 4 | `CLAUDECODE_BRIEF_BG_REFERENCE_v1_0.md` | Session 2 | **DONE** (2026-06-08) |
| 5 | `CLAUDECODE_BRIEF_BG_ONTOLOGY_v1_0.md` | Session 2 | **DONE** (2026-06-08) |
| 6 | `CLAUDECODE_BRIEF_BG_TEXTS_v1_0.md` | Session 4 | **DONE** (2026-06-08) |
| 7 | `CLAUDECODE_BRIEF_BG_TEXT_INDEX_v1_0.md` | Session 4 | **DONE** (2026-06-08) |
| 8 | `CLAUDECODE_BRIEF_BG_RULES_v1_0.md` | Session 4 | **DONE** (2026-06-08) |
| 9 | `CLAUDECODE_BRIEF_BG_REMEDIES_v1_0.md` | Session 4 | **DONE** (2026-06-08) |
| 10 | `CLAUDECODE_BRIEF_BG_CONCORDANCE_v1_0.md` | Session 5 | **DONE** (2026-06-08) |
| 11 | `CLAUDECODE_BRIEF_BG_YOGAS_v1_0.md` | Session 3 | **DONE** (2026-06-08) |
| 12 | `CLAUDECODE_BRIEF_BG_DASHA_SYSTEMS_v1_0.md` | Session 3 | **DONE** (2026-06-08) |
| 13 | `CLAUDECODE_BRIEF_BG_DOSHAS_v1_0.md` | Session 3 | **DONE** (2026-06-08) |
| 14 | `CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md` | Session 5 | **DONE** (2026-06-08) |
| 15 | `L0_BRAHMAGYAN_INTEGRATION_AND_REBUILD_PROOF_v1_0.md` | Session 5 | **DONE** (2026-06-08) |

**Estimated Cowork session time:** 12-16 hours across 5 sessions.

**Execution model after all 15 are authored:** the executor receives the master plan + 14 briefs as a batch. Worktree `MadhavL0Unified` on branch `feature/l0-unified-build`. Executor implements in tier order (per §3), runs Vimarśaka per asset, runs Vimarśaka-Ω at end, opens ONE PR with everything.

## §5 — Acceptance criteria (Vimarśaka-Ω, final gate)

Vimarśaka-Ω passes only if ALL of the following hold:

1. **Every asset's writer is registered** in `pipeline/orchestrator/writers/`
2. **Every asset's row count ≥ target floor** per §2
3. **Every row has non-NULL source citation** (`source_citation` or `source_chunk_ids[]` or `classical_citations`)
4. **FK integrity holds across all assets:**
   - Every `reference_*.canonical_id` resolves in `brahma_ontology`
   - Every `brahma_yoga_catalog.canonical_id` resolves in `brahma_ontology` (entity_class='yoga')
   - Every `brahma_dosha_catalog.canonical_id` resolves in `brahma_ontology` (entity_class='dosha')
   - Every `brahma_dasha_systems.canonical_id` resolves in `brahma_ontology` (entity_class='dasha_system')
   - Every `sutravali_rules.yoga_canonical_id` (when non-null) resolves in `brahma_yoga_catalog`
   - Every `bg_concordance.source_chunk_ids[]` element resolves in `classical_text_chunks`
   - Every `brahma_compendium_index.text_id` resolves in `classical_texts`; every `topic_id` resolves in `reference_topic_tags`
5. **No duplicate (entity_class, canonical_id) pairs in brahma_ontology**
6. **No data lives in two tables** (single-source-of-truth rule from holistic design §4.2)
7. **Layer-level "Build" click triggers all 12 assets** in dependency order without manual intervention
8. **Cockpit displays all 12 tiles as `lit`** with row counts ≥ floor
9. **Delete-and-rebuild proof:**
   - Native (super_admin) clicks "Clear instrument" at Brahmagyan layer scope → all 12 tables empty
   - Native clicks "Build" at Brahmagyan layer scope → orchestrator runs all 12 writers
   - Post-rebuild row counts match pre-rebuild within ±0.1%; content hashes match per asset

If ANY of these 9 checks fail, the campaign is NOT sealed.

## §6 — What's preserved from v1.0 (don't rebuild what works)

- Phase α's 14 tables and asset_registry entries: keep as-is
- Phase β's writer infrastructure (`WriterBase`, `ContextSpec`, `WriterResult`, `@register`, `discover_all()`): keep as-is
- Phase β's `bg_reference.py` and `bg_ontology.py` writers: REPLACE per Session 2 briefs (current implementations are 88-row / 102-entry slices; v2.0 ships full content)
- All existing migrations 176-179: keep as-is

## §7 — Locked architectural principles (from holistic design v1.1 + Phase β learnings)

| Principle | Implementation note |
|---|---|
| ZERO LLM | Every writer is pure Python. Vertex AI embeddings (deterministic transform) permitted only for bg_texts. |
| Deterministic rebuild | Re-running any writer produces byte-identical row counts and content hashes |
| Source-cited rows | Every row has at least one of: source_citation, source_chunk_ids[], classical_citations |
| FK integrity | Every cross-asset reference resolves; insertion fails if FK is broken |
| Single source of truth | Each fact lives in exactly one table per holistic design §4.2 |
| ON CONFLICT DO NOTHING | All writers use this idempotency pattern (NOT DO UPDATE — Phase β learning) |
| Connection autocommit | asset_runner.py owns transaction boundary; writers use autocommit-mode connections per Phase β fix |
| Global asset throughput updates | Use `WHERE chart_id IS NOT DISTINCT FROM %s` (Phase β residual; fixed in Document 2) |
| Floor is sacred | Vimarśaka FAILS any asset that ships below its target floor. NO ambiguity allowed in brief floor specifications. |

## §8 — Per-asset brief format

Every asset brief (Documents 3-14) follows this structure:

```markdown
§0 — Asset summary (name, target floor, source category)
§1 — Schema reference (the table(s) this writer populates; column-by-column)
§2 — Source classical references (which BPHS chapters / Saravali verses / etc.)
§3 — Embedded classical content (the actual Python data structures the writer uses)
§4 — Writer implementation (the .py file the executor authors verbatim)
§5 — FK validation logic (which other assets must be lit before this one runs)
§6 — Unit tests (specific tests the executor MUST author)
§7 — Vimarśaka check (asset-specific verification logic)
§8 — Hard stops + scope discipline
```

The embedded content in §3 is the work — it's what guarantees the executor produces target-floor data without judgment calls.

## §9 — Workflow

1. Cowork completes Sessions 1-5 (15 documents authored, native reviews each session's output for classical accuracy)
2. Native triggers execution: opens Claude Code, points at the master plan + 14 briefs
3. Executor implements all writers + orchestrator fixes in tier order per §3
4. Executor runs per-asset Vimarśaka checks; halts on any failure
5. Executor runs Vimarśaka-Ω end-to-end after all 12 assets populated
6. If Vimarśaka-Ω PASS → executor commits + opens ONE PR
7. Native verifies merge via `gh pr view N --json mergeCommit` (per [[pr-quality-gate-is-not-a-merge]])
8. Native verifies post-deploy: cockpit shows all 12 lit; clicks "Clear instrument" to trigger delete-and-rebuild proof; verifies bit-for-bit reconstruction

After step 8 PASSES, L0 Brahmagyan is TRULY sealed. Subsequent L1+ phases build on top of it.

> **Expected transient state during executor implementation.** The executor builds in tier order (orchestrator fixes → Tier 0 → Tier 1 → …). Because the orchestrator-fixes commit (Document 2) lands before most writers, a cockpit visit at any point mid-implementation — and at first visit immediately after the PR merges if writers are still landing — will show not-yet-implemented assets in `error` state ("no writer registered"). This is **expected and benign**: every asset transitions to `lit` once its writer commit lands and the build re-runs. Do not treat transient `error` tiles during rollout as a regression. Vimarśaka-Ω (§5) is the only state that matters for seal: all 12 `lit` at floor.

## §10 — Hard stops at the campaign level

These conditions halt the campaign before merge:

- Any writer module fails to register
- Any asset's row count ships below target floor
- Any row has NULL source citation
- Any FK validation produces a missing reference
- Layer-level "Build" click on Brahmagyan triggers anything other than all 12 writers running in dependency order
- Delete-and-rebuild proof produces row count delta > ±0.1% on any asset

## §11 — What this campaign explicitly does NOT do

- Does NOT touch L1-L5 layers
- Does NOT add new L0 assets beyond the 12 locked in v1.0/Phase α
- Does NOT change the cockpit UI beyond what the orchestrator-fixes brief requires
- Does NOT modify the MCP layer, retrieval adapters, or chat surface
- Does NOT touch the Brahma/Cowork/Antigravity workflow infrastructure
- Does NOT alter Phase α's schema (migrations 176-179 stay as-is)
- Does NOT use LLM for any classical content authoring (Cowork writes it; executor copy-pastes)

---

*End of Master Plan v2.0.*
