---
artifact: L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF
canonical_id: L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF
version: 1.0
status: ACTIVE
authored_by: Cowork (planning) 2026-06-08
purpose: Self-contained handoff document for a NEW Cowork conversation to take over authoring the 14 remaining L0 Brahmagyan briefs
how_to_use: |
  Paste this entire file (or attach it) as the FIRST message to a new Cowork conversation.
  The receiving conversation will have full context to begin authoring Session 1 of the 5-session brief campaign.
  No prior conversation history needed beyond this file.
---

# L0 Brahmagyan Unified Build Campaign — Handoff to New Conversation

> **This document is the complete context handoff.** The new Cowork conversation reading this should have everything needed to begin authoring the 14 remaining L0 Brahmagyan briefs without referencing prior conversation history.

## §0 — How to use this document (Cowork instructions for the new conversation)

You are continuing work that began in a previous conversation. The previous conversation closed because token budget was getting heavy. Your job:

1. Read this entire document carefully (it's self-contained — no prior conversation history available)
2. Read the 3 referenced artifacts on disk (paths in §3)
3. Confirm with native that you understand the mission and the campaign structure
4. Begin Session 1 of the 5-session brief-authoring campaign per §6

**Critical constraint:** native does NOT want execution to start until ALL 14 briefs are authored. You are in planning mode. The executor (Claude Code in Antigravity IDE) runs AFTER you finish all 5 cowork sessions.

**Critical principle:** when authoring asset briefs, embed the actual classical content (Python data structures with verified BPHS/Saravali/Phaladeepika/etc. citations) directly in the brief. Do NOT defer content authoring to the executor. The previous conversation's failure mode was authoring thin briefs where the executor delivered 102 ontology entries vs a 700+ target. Avoid that.

## §1 — Mission

The outcome native wants:

> **Single click on "Build" at the Brahmagyan layer in cockpit → all 12 L0 assets autonomously populate to or beyond their design-target row counts, deterministically, with full source citation, and the cockpit transitions all 12 tiles from dormant to lit without further native intervention.**

This is the only acceptance criterion that matters. Everything serves that outcome.

To make it true, four things must hold after all briefs execute:

1. A writer exists and is registered for every one of the 12 L0 assets
2. Every writer produces output that meets or exceeds the design target row counts
3. The orchestrator executes writers in correct dependency order
4. The orchestrator-side bugs are fixed (notably: `chart_id IS NOT DISTINCT FROM` for global assets)

## §2 — Project context

**Project:** MARSYS-JIS — an LLM-operated Vedic Jyotish (astrology) instrument for native Abhisek Mohanty (birth: 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India).

**Layer architecture:** L0 Brahmagyan (foundation; global classical knowledge) → L1 Gaṇita → L2 Bodha → L3 Kāla → L4 Phala → L5 Mīmāṃsā. Each layer reads from the layers below.

**L0's role:** the classical knowledge foundation. Global (not per-chart). Every chart in the system reads from L0 when synthesizing answers. L0 contains: ephemeris data, classical text corpora (BPHS, Saravali, Phaladeepika, Jaimini, Tajaka, etc.), reference tables (planets, nakshatras, signs, etc.), ontology vocabulary, extracted classical rules, remedy catalog, yoga/dosha/dasha catalogs, cross-school concordance.

**Quality bar:** acharya-grade. From CLAUDE.md §J: "an independent senior Jyotish acharya reviewing this corpus should reach one of: 'this is my own level', 'this is above my own level', or 'this reveals things I wouldn't have seen on first pass'. Nothing less."

## §3 — Existing artifacts you must read

These three files on disk contain everything you need to know about the design state:

1. **`00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md`** (v1.1) — the L0 holistic design with 12 assets, per-asset target row counts, FK relationships, single-source-of-truth rules. This is the authoritative design document. Read entirely.

2. **`00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md`** — the master plan for the unified-build campaign that supersedes the prior incremental phase model. Authored in the previous conversation; lists all 15 documents in the campaign and the dependency DAG. Read entirely.

3. **`00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0_PHASE_BETA_v1_0.md`** — the prior phase β brief which shipped via PR #227. Status: COMPLETE but with KNOWN SCOPE SHORTFALL (delivered 88 bg_reference rows vs 2,000 target; 102 bg_ontology entries vs 700-1,000 target). The new campaign in v2.0 supersedes this with full-content writers. Read frontmatter + scope sections to understand what was shipped.

Additional context worth reading:

4. **`platform/python-sidecar/pipeline/orchestrator/writers/__init__.py`** — the writer registration substrate (`@register`, `WriterBase`, `ContextSpec`, `WriterResult`, `discover_all()`). Authored in Phase β. Keep as-is in this campaign; subsequent writers register against it.

5. **`platform/python-sidecar/brahmagyan/l0_reference.py` and `l0_ontology.py`** — the current Phase β data sources. They contain partial data that v2.0 briefs will REPLACE with full target-floor content.

## §4 — Current production state

**Cloud Run:** `amjis-web-00544-bjz` or later (PR #227 deployed earlier today).

**Main HEAD:** `db6cc7f3` (PR #226 cockpit polish round) plus PR #227 (Phase β writer infrastructure + thin writers).

**Database (prod):**
- 12 L0 asset_registry rows registered (per Phase α, PR #225)
- 14 L0 backing tables exist (5 reference_* + 10 reference_* new + 4 brahma_* content + brahma_ontology + brahma_remedy_corpus + sutravali_rules + classical_attributions + brahma_compendium_index + classical_text_chunks + ephemeris_daily)
- bg_ephemeris: 825,084 rows from prior L0FR work (already populated)
- bg_reference: 88 rows (5 typed tables; Phase β slice — needs full content per v2.0)
- bg_ontology: 102 entries (Phase β slice — needs full content per v2.0)
- Other 9 assets: dormant / 0 rows

**Open known issues:**
- `asset_runner.py:run_asset()` uses `WHERE chart_id = %s` for asset_throughput updates; SQL equality doesn't match NULL, so global L0 assets' state never transitions to 'lit' via the normal orchestrator path. Phase β residual. **Must be fixed in orchestrator-fixes brief (Document 2 in §6 below).**

## §5 — The 12 L0 assets and their target floors

Targets are FLOORS. Vimarśaka-Ω fails the campaign if any writer ships below target.

| # | Asset | Backing | Target floor | Source category |
|---|---|---|---|---|
| 1 | `bg_ephemeris` | `ephemeris_daily` | 825,084 rows | Algorithmic (Swiss Ephemeris compute; already populated; brief is wrapper-only) |
| 2 | `bg_reference` | 15 typed reference_* tables | ~2,000 rows total | Embedded classical data (BPHS Ch.3/4/6/7/26 + Saravali + Phaladeepika + Taittiriya Aranyaka) |
| 3 | `bg_texts` | `classical_text_chunks` | ≥14,000 chunks (15 texts) | Source PDFs in GCS |
| 4 | `bg_ontology` | `brahma_ontology` | ≥700 entities across 15 entity classes | Embedded classical data |
| 5 | `bg_text_index` | filtered `classical_text_chunks` | ≥400 distinct topic_tags | Deterministic Python keyword-rule classifier |
| 6 | `bg_rules` | `sutravali_rules` | ≥3,000 rules | Python regex extraction from bg_texts |
| 7 | `bg_remedies` | `brahma_remedy_corpus` | ≥800 remedies | Embedded classical data (BPHS Ch.91-94 + Phaladeepika Ch.27 + Mantra Mahodadhi + Lal Kitab) |
| 8 | `bg_concordance` | `classical_attributions` | ≥800 chunk-pointer rows | Deterministic Python topic × school matching |
| 9 | `bg_yogas` | `brahma_yoga_catalog` | ≥250 yogas | Embedded classical data (BPHS Ch.30-35 + Saravali + Phaladeepika + Jaimini) |
| 10 | `bg_dasha_systems` | `brahma_dasha_systems` | ≥15 dasha systems | Embedded classical data (BPHS Ch.46-50 + Jaimini Ch.1) |
| 11 | `bg_doshas` | `brahma_dosha_catalog` | ≥50 doshas | Embedded classical data |
| 12 | `bg_compendium_index` | `brahma_compendium_index` | ≥3,000 index rows | Deterministic Python aggregation over bg_texts |

Sum target: ~840,000+ rows of source-cited classical content.

## §6 — The 15 documents in this campaign + authoring sessions

You are authoring documents 2-15 (Document 1, the master plan v2.0, was authored in the prior conversation and exists on disk).

Sessions are sequenced based on dependencies between briefs. Native reviews each session's output for classical accuracy before next session begins.

### Session 1 (continue from prior conversation; 2 docs remaining)
- ✓ Document 1: `L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md` (DONE in prior conversation)
- ☐ Document 2: `CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0.md` (fixes asset_runner.py NULL bug + writer discovery + layer-level build semantics)
- ☐ Document 3: `CLAUDECODE_BRIEF_BG_EPHEMERIS_v1_0.md` (wrapper writer; data already exists)

### Session 2 (largest content sessions)
- ☐ Document 4: `CLAUDECODE_BRIEF_BG_REFERENCE_v1_0.md` (~2,000 rows across 15 typed tables; full Python data embedded)
- ☐ Document 5: `CLAUDECODE_BRIEF_BG_ONTOLOGY_v1_0.md` (~700-1,000 entities across 15 classes; full Python data embedded)

### Session 3 (catalog briefs)
- ☐ Document 11: `CLAUDECODE_BRIEF_BG_YOGAS_v1_0.md` (~250 yogas with formation rules + significations + classical citations)
- ☐ Document 12: `CLAUDECODE_BRIEF_BG_DASHA_SYSTEMS_v1_0.md` (~15-18 dasha systems with sequence + computation method)
- ☐ Document 13: `CLAUDECODE_BRIEF_BG_DOSHAS_v1_0.md` (~50-65 doshas with formation + cancellation conditions)

### Session 4 (text-dependent briefs)
- ☐ Document 6: `CLAUDECODE_BRIEF_BG_TEXTS_v1_0.md` (ingest 15 PDFs from GCS; chunking + embeddings)
- ☐ Document 7: `CLAUDECODE_BRIEF_BG_TEXT_INDEX_v1_0.md` (topic_tag classifier; ~500 canonical topic tags)
- ☐ Document 8: `CLAUDECODE_BRIEF_BG_RULES_v1_0.md` (regex extractor with ~50 patterns covering Sanskrit/English templated phrasings)
- ☐ Document 9: `CLAUDECODE_BRIEF_BG_REMEDIES_v1_0.md` (~800-1,500 remedies; embedded YAML data)

### Session 5 (closing briefs)
- ☐ Document 10: `CLAUDECODE_BRIEF_BG_CONCORDANCE_v1_0.md` (chunk-pointer index; 200 topics × 5 schools)
- ☐ Document 14: `CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md` (per-text-chapter + per-text-topic aggregations)
- ☐ Document 15: `L0_BRAHMAGYAN_INTEGRATION_AND_REBUILD_PROOF_v1_0.md` (Vimarśaka-Ω; layer-level Build click test; delete-and-rebuild bit-for-bit proof)

**Estimated total Cowork session time:** 12-16 hours across 5 sessions. Sessions 2 and 4 are the largest.

## §7 — Format spec for asset briefs (Documents 3-14)

Every asset brief MUST follow this structure:

```markdown
---
artifact: CLAUDECODE_BRIEF_BG_<ASSET>_v1_0
canonical_id: L0_BG_<ASSET>_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_<asset> writer
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: <N rows>  # Vimarśaka fails if writer ships below this
dependencies: [bg_ontology, bg_texts, ...]  # which other assets must be lit before this writer runs
llm_cost: $0 (or "embeddings only" for bg_texts)
---

# bg_<asset> — Writer Brief

## §0 — Asset summary
- Asset ID: bg_<asset>
- Backing table(s): <list>
- Target floor: <N rows>
- Source category: <embedded data | source PDFs | algorithmic | deterministic extraction>

## §1 — Schema reference
[Column-by-column spec of the backing table(s). Reference the actual CREATE TABLE statements from migrations 176-179.]

## §2 — Classical source references
[Which BPHS chapters, Saravali verses, Phaladeepika sections, etc. The classical literature this asset draws from.]

## §3 — Embedded classical content
[The actual Python data structures the writer uses. For yogas brief: ~250 yoga entries with canonical_id, name_sa, name_en, formation_rule_jsonb, significations_text, classical_citations, source_chunk_ids[], school, etc.]

This section is the WORK. It guarantees the executor produces target-floor data without judgment calls.

## §4 — Writer implementation
[The exact Python file path and class definition the executor authors. Includes @register decorator, run() method, FK validation, ON CONFLICT DO NOTHING idempotency.]

## §5 — FK validation logic
[Which other assets must be lit. Which canonical_ids must resolve. Which rows reject if FK is broken.]

## §6 — Unit tests
[Specific pytest tests the executor MUST author. Idempotency test, FK integrity test, row-count-meets-floor test.]

## §7 — Vimarśaka check (asset-specific)
[Programmatic checks: row count ≥ floor, source citation NOT NULL, FK integrity. Returns APPROVE / REJECT.]

## §8 — Hard stops + scope discipline
[What halts the writer. What's out of scope.]
```

## §8 — Sources for embedded classical content (by asset)

Wherever you embed classical data in §3 of a brief, you MUST cite to a primary classical source. Here's the source library by asset:

| Asset | Primary sources | Notes |
|---|---|---|
| bg_reference (planets) | BPHS Ch.3 (Grahana-svarupa-adhyaya), BPHS Ch.4 (Graha-mitra-adhyaya), BPHS Ch.27 (Karaka-adhyaya) | 9 grahas + 2 nodes (Rahu/Ketu); exaltation/debilitation/mooltrikona/own_signs/karak_domains/dasha_years |
| bg_reference (nakshatras) | BPHS Ch.4 + Taittiriya Aranyaka | 27 nakshatras with deity/ruler/pada_lords/nature/guna |
| bg_reference (signs) | BPHS Ch.6 (Rasi-svarupa-adhyaya) | 12 signs with element/mode/lord/exaltation_graha/debilitation_graha |
| bg_reference (aspects) | BPHS Ch.26 (Drishti-phala-adhyaya) | Natural aspects + Parashari special aspects (Mars 4/7/8, Jupiter 5/7/9, Saturn 3/7/10) + Jaimini sign aspects |
| bg_reference (vargas) | BPHS Ch.7 (Shodasha-varga-adhyaya) | 16 divisional charts with divisors + computation methods |
| bg_reference (houses) | BPHS Ch.7 + Phaladeepika Ch.4 | 12 bhavas with karakas + classical doctrine + kendra/trikona/dusthana classification |
| bg_reference (strength_systems) | BPHS Ch.27 (Karaka-adhyaya) + Mantreswara Phaladeepika | Shadbala (6 strength sources × 9 grahas) + Ashtakavarga (8 tables × 12 signs) + Bhava-bala |
| bg_reference (karakas) | BPHS Ch.27 + Jaimini Ch.1 | Sthira karakas (per house) + Chara karakas (Atma/Amatya/Bhratri/Matri/Putra/Jnati/Dara/Stri) |
| bg_reference (upagrahas) | BPHS Ch.3 | Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indra-chapa, Upaketu + computation rules |
| bg_reference (constants) | BPHS various | Vimshopaka points per varga, ashtakavarga bindus, shadbala max values, dignity degrees |
| bg_reference (topic_tags) | Authored by Cowork from corpus analysis | Canonical vocabulary for text classification — saturn_7th_marriage, vimshottari_dasha_rules, etc. |
| bg_reference (glossary) | Phaladeepika + BPHS + Saravali | Technical Jyotish terms — drishti, kendra, trikona, hora, drekkana, etc. |
| bg_ontology | All of the above + composite vocabulary | Entity vocabulary + synonyms (canonical_id + name_en + name_sa + synonyms[] + one_line_description) |
| bg_yogas | BPHS Ch.30-35 (Yogadhyaya), Saravali Ch.34-50 (extensive yoga catalog ~120 yogas), Phaladeepika Ch.7, Jaimini Ch.2-3 | ~250 yogas across: raja, dhana, pancha_mahapurusha (5 main + variants), aristha, sannyasa, other. Each has formation_rule_jsonb (structured: requires planets in specific houses/aspects), significations_text, cancellation_conditions, classical_citations |
| bg_dasha_systems | BPHS Ch.46 (Vimshottari), Ch.47-50 (Yogini, Ashtottari, Kalachakra, etc.), Jaimini Ch.1 (Chara Dasha) | Vimshottari, Yogini, Chara (Jaimini), Ashtottari, Kalachakra, Shoola, Shashti-hayani, Dwadasottari, Panchottari, Shatabdika, Chaturshiti-Sama, Dwisaptati-Sama, Sthira, Tara, Yogardha, etc. (~15-18 systems) |
| bg_doshas | BPHS various + classical tradition | Manglik (Kuja), Kala-sarpa, Kala-amrita, Kemadruma, Pitru, Gana (8-fold), Nadi (3-fold), Bhakoot (compatibility), Daridra, Vish (Visha), Mrityu, Sade-sati, Dhaiya, Punarphoo, etc. (~50-65) |
| bg_remedies | BPHS Ch.91-94 (Upayadhyaya), Phaladeepika Ch.27, Mantra Mahodadhi (16th c.), Lal Kitab (Goel) | ~800-1500 remedies across: mantra, yantra, gemstone, charity (dāna), vrata (fasting), puja, tantric (with careful-inclusion gate per L0FR_SOURCE_DATA v1.0 §168-181), ayurvedic, vastu, behavioral |
| bg_concordance | Cowork authors ~200 canonical topics; deterministic chunk matching against bg_texts | Per (topic_id × school) row: source_chunk_ids[] + rule_ids[] + match_method (keyword/topic_tag) + match_confidence. NO stance_text per holistic design v1.1 §3.8 |
| bg_compendium_index | Mechanical aggregation; per-text-chapter + per-text-topic-tag | ~3000-5000 rows. summary_text is first-N-chunks synopsis (NO LLM) |
| bg_texts | 15 PDFs in GCS bucket; chunker authored in prior Stream C work | ~14,500 chunks across BPHS, Phaladeepika, Jataka Parijata, Uttara Kalamrita, Jaimini Sutram (already ingested) + Brihat Jataka, Saravali, Hora Sara, Sarvartha Chintamani, Brihat Samhita, Tajaka Neelakanthi, Yavana Jataka, Bhrigu Samhita, Muhurta Chintamani, Lal Kitab (to ingest). Embeddings via Vertex AI text-multilingual-embedding-002. |

## §9 — Locked architectural principles (don't violate)

| Principle | Implementation note |
|---|---|
| ZERO LLM | Every writer is pure Python. Vertex AI embeddings (deterministic transform) permitted only for bg_texts. |
| Deterministic rebuild | Re-running any writer produces byte-identical row counts and content hashes |
| Source-cited rows | Every row has at least one of: `source_citation` text field, `source_chunk_ids[]` array, `classical_citations` jsonb |
| FK integrity | Every cross-asset reference resolves; insertion fails if FK is broken |
| Single source of truth | Each fact lives in exactly one table per holistic design §4.2 — ontology stores names + synonyms ONLY (one-line description for typing disambiguation); doctrinal data lives in reference_* tables or per-asset catalogs (yoga/dosha/dasha) |
| ON CONFLICT DO NOTHING | All writers use this idempotency pattern; NOT DO UPDATE (Phase β learning) |
| Connection autocommit | `asset_runner.py` owns transaction boundary; writers use autocommit-mode connections |
| Global asset throughput | Use `WHERE chart_id IS NOT DISTINCT FROM %s` (Phase β residual being fixed in orchestrator brief) |
| Floor is sacred | Vimarśaka FAILS any asset that ships below target floor. No exceptions, no waivers in briefs. |

## §10 — Acceptance criteria for the whole campaign (Vimarśaka-Ω, final gate)

After the executor runs all 14 briefs (+ master plan), Vimarśaka-Ω passes only if ALL of these hold:

1. Every asset's writer is registered in `pipeline/orchestrator/writers/`
2. Every asset's row count ≥ target floor per §5
3. Every row has non-NULL source citation
4. FK integrity holds across all 12 assets:
   - reference_*.canonical_id ⊂ brahma_ontology
   - brahma_yoga_catalog.canonical_id ⊂ brahma_ontology (entity_class='yoga')
   - brahma_dosha_catalog.canonical_id ⊂ brahma_ontology (entity_class='dosha')
   - brahma_dasha_systems.canonical_id ⊂ brahma_ontology (entity_class='dasha_system')
   - sutravali_rules.yoga_canonical_id ⊂ brahma_yoga_catalog (when non-null)
   - classical_attributions.source_chunk_ids[] ⊂ classical_text_chunks
   - brahma_compendium_index.text_id ⊂ classical_texts
   - brahma_compendium_index.topic_id ⊂ reference_topic_tags
5. No duplicate (entity_class, canonical_id) in brahma_ontology
6. No data lives in two tables (single-source-of-truth rule)
7. Layer-level "Build" click triggers all 12 assets in dependency order without manual intervention
8. Cockpit shows all 12 tiles as `lit` with row counts ≥ floor
9. Delete-and-rebuild proof:
   - Native (super_admin) clicks "Clear instrument" at Brahmagyan layer scope → all 12 tables empty
   - Native clicks "Build" at Brahmagyan layer scope → orchestrator runs all 12 writers
   - Post-rebuild row counts match pre-rebuild within ±0.1%; content hashes match per asset

If ANY check fails, the campaign is NOT sealed.

## §11 — Operational notes for the new conversation

### Tool access
- File tools (Read, Write, Edit) — author briefs to `00_ARCHITECTURE/BRIEFS/` and the master plan to `00_ARCHITECTURE/`
- Bash — read existing files, run grep, verify content via the local repo

### Authoring rhythm
- Each session, confirm to native what documents you're about to author (per §6 sequencing)
- Author them one at a time, save after each
- After saving, briefly summarize what you authored (so native can review for classical accuracy)
- Halt session when token budget gets to ~150K (avoid the slowdown that caused this handoff)

### When stuck on classical content
- Reference BPHS chapter+verse numbers in source_citation strings
- For yogas/doshas: cite the specific verse range where the yoga/dosha is defined
- For dasha systems: cite the chapter; computation rules go in computation_pseudocode field
- When you can't find a primary classical source for a piece of content, FLAG it to native (don't fabricate citations)

### Hard stops for the cowork conversation
- Native asks you to halt and resume in another session → save current work, summarize, halt cleanly
- A classical content question requires acharya-level judgment → surface to native; don't guess
- An asset's structural design (table schema) conflicts with existing migration → halt; the schema is locked

### After all 15 docs authored
- Notify native: "Campaign briefs complete. Ready to hand off to executor (Claude Code in Antigravity IDE)."
- Native opens Claude Code; drops master plan + 14 briefs as one batch
- Executor implements in dependency order per §3 of master plan
- ONE PR contains everything; native verifies merge via `gh pr view N --json mergeCommit`

## §12 — What to do FIRST in the new conversation

1. Read this entire handoff document
2. Read the three referenced artifacts on disk (§3 numbered list)
3. Confirm to native: "I've read the handoff and the three artifacts. Ready to author Session 1 (Documents 2 and 3). Beginning now."
4. Author Document 2 (`CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0.md`)
5. Author Document 3 (`CLAUDECODE_BRIEF_BG_EPHEMERIS_v1_0.md`)
6. Present both to native for review
7. Suggest pacing for Session 2 timing

## §13 — Memory references the new conversation should consult

The following memories should be loaded if available in the new conversation's space:

- `[[deterministic-first-for-data-build]]` — zero-LLM stance for L0 construction
- `[[pyjhora-is-the-engine]]` — PyJHora is L1+ chart calc engine (not L0)
- `[[no-audience-tier]]` — audience tier eliminated (no client/acharya/super_admin gating in L0)
- `[[pr-quality-gate-is-not-a-merge]]` — verify every PR claim via `gh pr view --json mergeCommit`
- `[[feedback-phase-sealed-needs-merge-verification]]` — companion to above
- `[[cockpit-v1-v2-split]]` — cockpit renders v2 via DataAssetsView; reads sanskrit_name/english_name from /api/cockpit/registry
- `[[l0-phase-alpha-truly-sealed]]` — Phase α SEALED state with 14 tables + 12 asset_registry rows
- `[[l0-phase-beta-shipped]]` — what shipped in Phase β + the chart_id NULL residual to fix
- `[[cockpit-clear-fix-shipped]]` — clear button role-based semantics (super_admin can clear L0)
- `[[cockpit-polish-round-shipped]]` — RefreshIconButton + defensive JSON parse + layer-grouped modal

If these memories aren't in the new conversation's space, that's OK — this document contains the substantive context. The memories are convenience pointers.

## §14 — Closing notes from the prior conversation

What native articulated as the "outcome":
> "I am going to wipe out the data that is in the reference library and the ontology. I'm going to wipe it out. What I need you to do is create a brief, create a master plan for the entire layer zero and a supporting brief for each of the assets of layer 0 that is Brahma Gyan individually... Brahmagyan, you need to in a very structured proper manner set up the entire layer for autonomous build with orchestrator. The briefs will be available... Then Brahma Gyan is going to build, implement all the briefs, deploy them and everything that is required so that I can press build and all data can will be populated in the data stores. As per the target so the briefs need to be prepared to that detail that we exceed these targets. Can you think through this and make this work? I need the outcome. I'm open to your suggestion of how we can restructure or reinvent or change this but the outcome is what I want."

What was decided in the prior conversation:
- Restructure from incremental phase model (v1.0) to unified-build campaign (v2.0)
- Cowork embeds classical content directly in each brief (not deferred to executor)
- Author ALL 15 briefs first, then executor runs them in one batch
- Floor targets are sacred (Vimarśaka fails any below-floor writer)

What was authored in the prior conversation before this handoff:
- `L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md` (Document 1)

What remains for the new conversation:
- Documents 2 through 15 (14 briefs)
- 5 sessions estimated, ~12-16 hours total Cowork session time
- Native reviews each session output for classical accuracy

---

**Native:** when you paste this into the new Cowork conversation, the first thing the conversation will do is read this document, read the three referenced artifacts on disk, and confirm understanding before authoring Session 1's two documents.

*End of handoff document.*
