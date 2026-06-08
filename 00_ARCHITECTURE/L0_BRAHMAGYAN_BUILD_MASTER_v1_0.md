---
artifact: L0_BRAHMAGYAN_BUILD_MASTER
canonical_id: L0_BRAHMAGYAN_BUILD_MASTER
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE (multi-session execution)
native: Abhisek Mohanty
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1 deterministic-only)
predecessor: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0_PHASE_ALPHA_v1_0.md (Phase α — SEALED via PR #225)
scope: Brahma Jñāna build arc — phases β through η (writers + content + rebuild proof)
locked_decisions:
  - ZERO LLM use anywhere in L0 construction; embeddings as deterministic transform permitted
  - bg_concordance is a chunk-pointer index, not stance text; L1+ synthesizes at query time
  - bg_rules.prediction is verbatim verse fragments
  - bg_text_index counts distinct topic_tag values
  - Writer infrastructure (pipeline/orchestrator/writers/) does NOT yet exist; Phase β builds it
---

# L0 Brahma Jñāna — Build Master Plan (Phases β → η)

## §0 — Mission

Take L0 Brahma Jñāna from "12 assets registered + dormant" (post-Phase α) to "12 assets populated + autonomous rebuild verified" (end of Phase η).

Phase α (foundation: asset registration + 14 tables + asset_registry + cockpit tiles) is COMPLETE. Phases β-η populate those 14 tables + prove the orchestrator can rebuild the whole layer from scratch deterministically.

## §1 — Scope ⊕ out-of-scope

**In scope (this master plan):**
- Writer infrastructure (the missing `pipeline/orchestrator/writers/` registration substrate)
- 12 L0 asset writers (per-asset Python writer modules)
- Content authoring for the 12 L0 assets (data lives in the same writer modules where possible, or in `data/` files curated by native)
- Vimarśaka-β through Vimarśaka-η review gates (autonomous reviewers per existing L0FR pattern)
- The autonomous-rebuild proof at η (delete all L0 data, trigger orchestrator, bit-for-bit verify)

**Out of scope (separate workstreams):**
- L1-L5 layers (each gets its own design + build arc later)
- Adding new L0 assets beyond the locked 12
- Performance optimization (separate session if needed)
- UI/UX changes to cockpit (separate session if needed)
- 4 deferred manual-upload texts for Phase δ (Tajaka Neelakanthi, Yavana Jataka, Bhrigu Samhita, Muhurta Chintamani) — native uploads PDFs; brief documents the hook

## §2 — Locked architectural principles (from holistic design v1.1)

| Principle | What it means for this build |
|---|---|
| ZERO LLM | Every writer is pure Python (embeddings permitted as deterministic transform via Vertex AI) |
| Deterministic rebuild | Re-running the same writer against the same source produces byte-identical output (same row counts, same content hashes) |
| Source-cited rows | Every row carries `source_citation` or `source_chunk_ids[]` or `classical_citations` |
| FK integrity | Every `reference_*.canonical_id` must exist in `brahma_ontology`; every chunk_id reference resolves |
| Single source of truth | Each fact in exactly one table (no doctrinal data in ontology; no naming data in reference tables) |
| Don't break what's built | Phase α's 14 tables are immutable schema; writers populate, never alter |
| Embeddings as the only Vertex AI call | text-multilingual-embedding-002 (768-dim); temperature=0 doesn't apply since embeddings aren't generative |

## §3 — Phase arc

```
                Phase α (DONE)
                  Foundation: 12 assets registered, 14 tables in prod
                          ↓
                  Phase β (NEXT)
                  Writer infrastructure + bg_reference writer + bg_ontology writer
                          ↓
                  Vimarśaka-β review
                          ↓
       ┌──────────────────┼──────────────────┐
       │       │          │         │        │
   Phase γ  Phase δ      Phase ε   (parallel-safe)
   yogas+   text         rules+
   dashas+  ingestion+   remedies
   doshas   topic_tag    expansion
       │       │          │         │        │
       └───────┴──────────┴─────────┴────────┘
                          ↓
                  Phase ζ
                  concordance chunk-pointer index + compendium index
                          ↓
                  Vimarśaka-ζ review
                          ↓
                  Phase η
                  delete-and-rebuild proof
                          ↓
                  Vimarśaka-Ω → SEAL
                          ↓
                  L0 Brahma Jñāna TRULY complete
```

## §4 — Per-phase summary

### Phase β — Writer infrastructure + bg_reference + bg_ontology

**Scope:**
- Author `pipeline/orchestrator/writers/__init__.py` with `@register` decorator, auto-discovery, base class `WriterBase`, ContextSpec dataclass
- Author the FIRST writer: `bg_reference.py` populating the 5 typed tables already on main (planets/nakshatras/signs/aspects/vargas). ~88 rows. Source: hand-curated Python data from BPHS Ch.3-7 + Taittiriya Aranyaka per existing seed file's structure.
- Author the SECOND writer: `bg_ontology.py` populating brahma_ontology with ~700-1000 entries (planets, nakshatras, signs, houses, dashas, yogas, doshas, karakas, upagrahas, domains, concepts, aspect_types, remedy_types, schools, texts). Source: hand-curated Python data.
- Both writers register via `@register('bg_reference')` / `@register('bg_ontology')` decorators
- Smoke: trigger cockpit "Build" on each asset → writer runs → asset_throughput shows lit + last_built_at populated
- Vimarśaka-β: 6 programmatic checks (writer registration / row counts / source citation NOT NULL / FK integrity for reference→ontology / deterministic re-run produces same hash / cockpit displays correctly)

**Estimated sessions:** 3-4 (1 infrastructure + 1 bg_reference + 1 bg_ontology + 1 Vimarśaka-β)
**Brief:** authored alongside this master plan as `CLAUDECODE_BRIEF_L0_PHASE_BETA_v1_0.md`

### Phase γ — bg_yogas + bg_dasha_systems + bg_doshas writers + content

**Scope:**
- Three writers, parallel-safe (no inter-dependencies; all depend only on bg_ontology being lit)
- `bg_yogas.py` populating brahma_yoga_catalog with ~250-300 yogas (BPHS Ch.30-35, Saravali, Phaladeepika, Jaimini)
- `bg_dasha_systems.py` populating brahma_dasha_systems with ~15-18 systems (Vimshottari, Yogini, Chara, Ashtottari, Kalachakra, etc.)
- `bg_doshas.py` populating brahma_dosha_catalog with ~50-65 doshas (Manglik, Kala-sarpa, Kemadruma, etc.)
- Each yoga/dosha row cross-references bg_ontology canonical_id; data file lives at `pipeline/orchestrator/writers/data/yogas.py` etc. for separation
- Vimarśaka-γ: FK integrity (every yoga.canonical_id exists in ontology), classical citation completeness, deterministic re-run

**Dependencies:** Phase β complete (writer infrastructure + bg_ontology lit)
**Estimated sessions:** 4-6 (parallel-safe; can run 3 streams concurrently with worktrees)
**Brief:** authored when Phase β closes

### Phase δ — bg_texts (10 missing texts) + topic_tag classifier

**Scope:**
- Ingest 10 missing texts per `L0FR_SOURCE_DATA_v1_0.md §3` (Brihat Jataka, Saravali, Hora Sara, Sarvartha Chintamani, Brihat Samhita, Tajaka Neelakanthi*, Yavana Jataka*, Bhrigu Samhita*, Muhurta Chintamani, Lal Kitab) — *=manual PDF upload by native
- ~6,000 additional chunks → total ~14,500
- Author `bg_text_index.py` writer: deterministic Python keyword-rule topic-tag classifier (NO LLM); for each chunk, match against TOPIC_RULES from `reference_topic_tags`; assign topic_tag or leave NULL
- Realistic topic-tag coverage: ~250-350 distinct tags (deterministic regex catches templated phrasings; novel phrasings get NULL)
- Embeddings via Vertex AI text-multilingual-embedding-002 (deterministic transform; permitted)
- Vimarśaka-δ: chunk count floor (≥14,000), embedding completeness (100% of chunks have embedding), topic_tag coverage ≥250

**Dependencies:** Phase β complete + native has uploaded the 3 manual PDFs to GCS
**Estimated sessions:** 3-5 (mostly sequential per text)
**Brief:** authored when Phase β closes; native uploads PDFs before brief executes

### Phase ε — bg_rules + bg_remedies expansion

**Scope:**
- `bg_rules.py` writer with expanded pattern library (~40-60 regex templates vs current 9). New families: Sanskrit-named, compound antecedent, conjunction, exchange-of-lords, aspect-from-house, yoga-cited, dasha-period, transit, karaka-based, conditional negation
- Re-run extraction against ALL bg_texts chunks (existing 8.4K + 10 new texts from Phase δ); target ~3-5K rules (deterministic-first range; LLM-assisted fallback explicitly NOT used per holistic design v1.1)
- Per-build "missed coverage report" emitted to `/tmp/sutravali_missed_coverage_<date>.md` for native pattern-library iteration
- `bg_remedies.py` writer + YAML hand-curation:
  - Mantra Mahodadhi ingestion (~1,500 verses → ~800-1,000 remedy rows; pre-curated YAML from native)
  - BPHS Ch.91-94 sweep (~100-150 remedy rows)
  - Lal Kitab structured remedies (~300-500 rows)
  - Per-planet × per-category matrix (~500 floor)
  - Total target ~800-1,500 (deterministic-first range)
- Vimarśaka-ε: rule count, remedy count, source citation completeness, FK integrity to ontology, missed-coverage report exists

**Dependencies:** Phase γ complete (yogas/dashas referenced in some rules) + Phase δ complete (more chunks to extract from)
**Estimated sessions:** 5-8 (parallel-safe: rules + remedies)
**Brief:** authored when Phase γ + δ both close

### Phase ζ — bg_concordance chunk-pointer index + bg_compendium_index

**Scope:**
- `bg_concordance.py` writer producing chunk-pointer rows: per (topic_id × school), store source_chunk_ids[] + rule_ids[] + match_method + match_confidence. Per holistic design §3.8, NO stance_text; synthesis at L1+ query time.
- ~200 canonical topics × 5-6 schools = ~1,000 rows
- Match method = keyword OR topic_tag (deterministic; preferred order: topic_tag exact match > keyword set match)
- `bg_compendium_index.py` writer producing ~3,000-4,000 index rows: per-text-per-chapter + per-text-per-topic-tag pointers. summary_text is mechanical first-N-chunks synopsis (NO LLM per holistic design v1.1)
- Vimarśaka-ζ: row counts, FK integrity (all source_chunk_ids resolve in bg_texts), topic coverage across schools, compendium index covers all 15 texts

**Dependencies:** Phase δ complete (topic_tag populated) + Phase ε complete (rules to cross-reference)
**Estimated sessions:** 4-6 (sequential: concordance → compendium)
**Brief:** authored when Phase ε closes

### Phase η — Autonomous rebuild proof

**Scope:**
- Capture pre-rebuild row counts + content hashes per L0 asset
- Native triggers via cockpit "Clear instrument" (super-admin global scope) → all L0 tables TRUNCATEd (per cockpit-clear-fix PR #226 semantics)
- Native triggers via cockpit "Rebuild" → orchestrator runs all 12 L0 writers in dependency order
- After rebuild: re-capture row counts + content hashes
- Verify: bit-for-bit match across all 12 assets (modulo timestamps); cockpit shows all 12 lit with correct counts
- Vimarśaka-Ω: comprehensive seal review — every Phase β-ζ AC re-checked, deterministic-rebuild proof passes, no manual-uploaded PDFs lost in the cycle

**Dependencies:** Phase ζ complete (full L0 populated)
**Estimated sessions:** 1-2 (mostly verification)
**Brief:** authored when Phase ζ closes

## §5 — Vimarśaka review pattern

Each phase ends with an autonomous review agent (per existing L0FR pattern):

| Gate | Agent | Authority | Decision rules |
|---|---|---|---|
| Post-Phase β | Vimarśaka-β | APPROVE / REJECT_WITH_FEEDBACK | Writer registration check, row counts ≥ floor, FK integrity, deterministic re-run, cockpit displays correctly |
| Post-Phase γ | Vimarśaka-γ | Same | FK integrity for yogas/doshas/dashas to ontology, classical citation completeness, deterministic |
| Post-Phase δ | Vimarśaka-δ | Same | Chunk count, embedding completeness, topic_tag coverage |
| Post-Phase ε | Vimarśaka-ε | Same | Rule + remedy counts within deterministic-first ranges, missed-coverage report emitted |
| Post-Phase ζ | Vimarśaka-ζ | Same | Concordance + compendium row counts, FK integrity, topic coverage across schools |
| Pre-seal Phase η | Vimarśaka-Ω | SEAL / DELTA_DEPLOY / ESCALATE | Comprehensive: every prior phase re-verified, rebuild proof passes |

Each Vimarśaka has 3 rework loops before escalating to native. Specs follow `L0FR_VIMARSAKA_SPECS_v1_0.md` pattern.

## §6 — Parallel-safety map

| Phase pair | Parallel-safe? | Why |
|---|---|---|
| β ‖ γ | NO | γ writers depend on bg_ontology being populated (Phase β output) |
| γ ‖ δ | YES | γ writes catalogs (yogas/dashas/doshas); δ writes text chunks; no overlap |
| γ ‖ ε | NO | ε rule extraction may reference yoga/dasha canonical_ids → γ must complete first |
| δ ‖ ε | YES (with caveat) | ε's expanded pattern library can run on existing chunks first, then re-run after δ adds new texts |
| ζ phases | sequential | concordance → compendium |

Recommended parallel execution: γ + δ run in parallel after β closes. ε runs after γ + δ both close. ζ runs after ε.

## §7 — Cost model

LLM cost: $0 (per holistic design v1.1 zero-LLM stance).
Embeddings cost: ~$1-2 across all 14,500 chunks (Vertex AI text-multilingual-embedding-002; one-time per chunk).
Cloud Run compute: ~$10-20 total across all phases.

## §8 — Acceptance criteria summary

| Asset | Phase | Target floor | Phase η rebuild bit-for-bit |
|---|---|---|---|
| bg_ephemeris | (already populated; Phase α structural) | 825,084 rows | YES |
| bg_reference | β | ≥88 rows (5 typed tables) | YES |
| bg_texts | δ | ≥14,000 chunks | YES |
| bg_ontology | β | ≥700 entries | YES |
| bg_text_index | δ | ≥250 distinct topic_tags | YES |
| bg_rules | ε | ≥3,000 rules | YES |
| bg_remedies | ε | ≥800 rows | YES |
| bg_concordance | ζ | ≥800 chunk-pointer rows | YES |
| bg_yogas | γ | ≥250 yogas | YES |
| bg_dasha_systems | γ | ≥15 dasha systems | YES |
| bg_doshas | γ | ≥50 doshas | YES |
| bg_compendium_index | ζ | ≥3,000 index rows | YES |

## §9 — Branch + workflow

- Master tracking branch: `track/l0-brahmagyan-build` (already exists)
- Per-phase execution branches: `feature/l0-phase-beta`, `feature/l0-phase-gamma`, etc.
- After each phase merges to main, Vimarśaka runs against prod
- Worktree-per-phase pattern (pre-create with `git worktree add`)
- Apply the merge-verification discipline from [[feedback_pr_quality_gate_is_not_a_merge]]: after every "PR merged" claim, run `gh pr view N --json mergeCommit -q .mergeCommit.oid` and `git merge-base --is-ancestor <merge-commit-sha> origin/main`

## §10 — Sealing definition (Phase η output)

L0 Brahma Jñāna is TRULY complete when:

1. All 12 assets in cockpit show `lit` state with row counts ≥ floors per §8
2. parity_check.ts passes all FK integrity rules per holistic design §4
3. Native triggers "Clear instrument" (super-admin) → all 12 L0 tables empty
4. Native triggers "Rebuild" → orchestrator runs all 12 writers; cockpit shows building → lit transitions
5. Post-rebuild row counts match pre-rebuild within ±0.1%; content hashes match per asset
6. Vimarśaka-Ω SEAL

After this, L0 is locked. Subsequent expansions (more text patterns, more curated content) are deltas, not rebuild cycles.

## §11 — Brief authoring strategy

This master plan + Phase β executable brief authored together. Phases γ-η briefs authored on demand:
- Phase γ brief: authored when Phase β closes (Vimarśaka-β PASS)
- Phase δ brief: authored when Phase β closes + native confirms PDFs uploaded
- Phase ε brief: authored when Phase γ + δ both close
- Phase ζ brief: authored when Phase ε closes
- Phase η brief: authored when Phase ζ closes

Each phase brief inherits this master plan as parent (referenced in frontmatter).

---

*End of master plan.*
