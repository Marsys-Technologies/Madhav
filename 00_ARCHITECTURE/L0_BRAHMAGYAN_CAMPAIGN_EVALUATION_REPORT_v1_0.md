---
artifact: L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT
canonical_id: L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT
version: 1.0
status: REVIEW_COMPLETE
reviewed_by: Cowork (review pass) 2026-06-08
reviewed_for: Abhisek Mohanty
inputs_read:
  - L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
  - L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF_v1_0.md
  - L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1, from track/l0-brahmagyan-build @ cc61693c)
  - migrations 176/177/178/179/180
  - all 14 briefs (Docs 2-15)
  - brahma_ontology live writer (l0_ontology.py)
---

# L0 Brahmagyan Campaign — Evaluation Report

## §0 — Executive summary

The 14 briefs are **structurally excellent** — orchestration, FK discipline, the DAG, determinism, ZERO-LLM compliance, the Vimarśaka gate stack, and the delete-and-rebuild proof are all well-designed and internally consistent. The campaign mechanism will work. **But on Dimension 1 — the one native called out as most important — the briefs do NOT yet embed enough data to deterministically hit floor without executor judgment.** They embed the data for the *small* assets fully (dashas 18/15 ✓) and the *aggregation/extraction* assets are deterministic-by-construction, but the three biggest **embedded-content catalogs under-deliver inline rows and lean on "executor completes the classical enumeration" completion-notes** — exactly the Phase-β failure mode v2.0 was written to eliminate.

**Dimension 1 (data point coverage):** of the 12 asset briefs — **PASS: 4** (bg_ephemeris, bg_texts, bg_dasha_systems, bg_text_index — the last three with documented corpus/PDF dependencies), **PARTIAL: 7** (bg_reference, bg_ontology, bg_yogas, bg_doshas, bg_rules, bg_remedies, bg_concordance/bg_compendium aggregation-floors-unproven), **FAIL: 0 outright, but bg_yogas is PARTIAL bordering FAIL** (25 yogas embedded inline vs a 250 floor; the "~130 core" is mostly enumerated-in-comments, the other ~120 is runtime corpus extraction).

**Campaign-level red flags:** none fatal. ZERO-LLM lock is honored in every brief (each explicitly supersedes the v1.0/holistic-design-body LLM passages). The cherry-pick (Doc 2 §2), branch name, and file paths are correct. **Two concrete defects:** (1) a real **schema-accuracy gap** — Docs 5/11/12/13 hardcode `ON CONFLICT (canonical_id)` and the field name `name_en`, but the live `brahma_ontology` writer uses `ON CONFLICT (entity_class, canonical_id)` and columns `canonical_name_en`/`canonical_name_sa`; (2) **migration-number under-reservation** — 8 writer briefs each need a `depends_on` UPDATE migration but only Doc 2 (181) and Doc 14 ("182+") name a number, leaving 6+ unreserved.

**Recommendation: READY AFTER AMENDMENTS.** The mechanism is sound and most assets are fine. Three content briefs (yogas, doshas, reference) need their inline data substantially completed *in the brief* before handoff, plus the two concrete defects above fixed. If native is comfortable trusting the executor to transcribe fixed classical enumerations (Nabhasa families, Kala-Sarpa variants, BPHS Ch.66 bindu tables) under the existing hard-stops, the bar drops to "amend the schema + migration defects only" — but that re-admits the exact judgment-call risk native asked to eliminate.

---

## §1 — Per-brief evaluation matrix

| Brief | D1 Data | D2 Cite | D3 Schema | D4 FK | D5 DAG | D6 Detrm | D7 Vimar | D8 Stops |
|---|---|---|---|---|---|---|---|---|
| Doc 2 (orch) | N/A | N/A | PASS | N/A | PASS | PASS | PASS | PASS |
| Doc 3 (ephem) | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS |
| Doc 4 (reference) | **PARTIAL** | PARTIAL | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 5 (ontology) | **PARTIAL** | PASS | **PARTIAL** | PASS | PASS | PASS | PASS | PASS |
| Doc 11 (yogas) | **PARTIAL→FAIL** | PARTIAL | **PARTIAL** | PASS | PASS | PASS | PASS | PASS |
| Doc 12 (dashas) | PASS | PASS | **PARTIAL** | PASS | PASS | PASS | PASS | PASS |
| Doc 13 (doshas) | **PARTIAL** | PARTIAL | **PARTIAL** | PASS | PASS | PASS | PASS | PASS |
| Doc 6 (texts) | PASS¹ | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 7 (text_idx) | PASS¹ | N/A | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 8 (rules) | **PARTIAL** | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 9 (remedies) | **PARTIAL** | PARTIAL | PARTIAL | PASS | PASS | PASS | PARTIAL | PASS |
| Doc 10 (concord) | PARTIAL¹ | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 14 (compendium) | PARTIAL¹ | N/A | PASS | PASS | PASS | PASS | PASS | PASS |
| Doc 15 (integration) | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS |

¹ Floor is *emergent* (depends on corpus completeness incl. 3 manual-upload PDFs); brief handles the gap with CONDITIONAL-PASS + operator action, which is acceptable but means "floor at first build" is not guaranteed by the brief alone.

---

## §2 — Detailed findings per brief

### §2.1 — Doc 2 — orchestrator fixes

**Data point coverage (D1):** N/A (infrastructure). **Schema (D3):** PASS — migration 181 reserved correctly (not 180); the `IS NOT DISTINCT FROM` + null-aware `ON CONFLICT` plumbing is exactly right for the global-asset NULL-chart_id problem. **DAG (D5):** PASS — the `resolveBuildPlan` topo-test (§6) is the right regression guard, and the §6 note correctly warns that migration 179 only encodes 4 edges and each writer brief must add its own. **Determinism (D6):** PASS. **Vimarśaka (D7):** PASS — Vimarśaka-FIX is 6 concrete checks, none vacuous. **Stops (D8):** PASS — the four hard stops are real failure modes.

**Material findings:** The cherry-pick of the holistic design from `track/l0-brahmagyan-build` is present and guarded (`test -f … || exit 1`). The end-to-end proof (§8) correctly anticipates the 10 not-yet-built assets going to `error` and isolates the success criterion to bg_reference + bg_ontology lighting via the orchestrator.

**Recommendation:** APPROVE.

### §2.2 — Doc 3 — bg_ephemeris

**Floor:** 825,084. **Embedded count:** N/A (algorithmic). **Gap:** 0 (data already in prod).

**D1:** PASS — count-first wrapper, no recompute when floor met, real rebuild path for the delete-rebuild proof. **D7:** PASS — the per-asset check verifies rows ≥ floor, null citation/ayanamsha = 0, AND the FORENSIC native-birth-date Sun row (1984-02-05). Good grounding. **D8:** PASS — engine is read-only; date-range/ayanamsha lock honored.

**Recommendation:** APPROVE.

### §2.3 — Doc 4 — bg_reference

**Floor (this writer's 12 substantive tables):** ≥1,450 (the brief's own stated own-floor is ≥1,225). **Embedded fully-inline count:** ~73 rows (houses 12 + strength_systems ~35 + upagrahas ~11 + chara/sthira-planet karakas 15). **Gap to floor: ~−1,150 rows are NOT inline.**

**D1 — PARTIAL.** Breakdown of how the floor is reached:
- **Truly copy-paste-ready inline:** reference_houses (12, full), reference_strength_systems (~35, full), reference_upagrahas (~11, full), karakas chara+sthira-planet (15, full). ≈ 73 rows.
- **Generated deterministically (acceptable):** reference_topic_tags (≥450) via planet×house / lord×house / domain cross-products — genuinely deterministic, the dimensions are fully specified, low risk. This is the largest single contributor and it IS sound.
- **"Family + completion-note" (executor must author the body):** reference_constants (≥200 — only ~12 spelled out; family (h), ~84 Ashtakavarga bindu rows, is "executor transcribes BPHS Ch.66 verbatim, or pulls from ingested chunks"), reference_glossary (≥350 — ~80 representative terms listed, "executor completes each family from named sources"), sthira_house karakas (≥55 — only 8 spelled out, rest in a comment).

So ~73 inline + ~450 deterministically-generated = ~523 rows the brief actually guarantees; the remaining ~700+ (constants body, glossary body, sthira-house karakas) depend on the executor completing fixed-but-not-embedded classical tables. The hard stops (§8) say "ship what is attested, report shortfall, do not fabricate" — which protects integrity but means the floor is **not guaranteed by the brief content alone.**

**D2 — PARTIAL.** Citations are present on every inline row and trace to specific BPHS chapters (Ch.7, Ch.27, Ch.26, Ch.66-72). UNVERIFIED note: several strength-system virupa max values and the Saptavargaja dignity points (Moolatrikona 45 / own 30 / etc.) are standard but I cannot independently confirm each against BPHS Ch.27 without the text — flag for native's separate acharya pass. No fabricated citations found.

**D3 — PASS.** INSERT column lists match migration 178 CHECK vocabularies (house `category` enum, strength `category` enum, karaka_type enum). topic_tags-exempt-from-source_citation correctly noted (the column doesn't exist).

**D4 — PASS.** `depends_on=[bg_ontology]` UPDATE present; the ontology-keyed FK validation (planet/sign/karaka/upagraha ids ⊂ brahma_ontology) is specified; the pointer-table ownership split (yogas/doshas/dashas pointers owned by the catalog writers) is correct and resolves the chicken-and-egg.

**D6 — PASS.** ON CONFLICT DO NOTHING throughout. **D7/D8 — PASS.**

**Material findings:**
- The ~700-row inline gap (constants body, glossary body, sthira-house karakas) is the same class of risk that produced Phase β's 102-vs-700 shortfall, softened here by hard stops.
- reference_constants family (h) has a Tier-ordering subtlety: it may need the BPHS chunks (Tier 2 bg_texts) if the bindu tables aren't embedded — so bg_reference's constants step could need a re-run after bg_texts. The brief flags this but it complicates the "Tier 0, runs first" placement.

**Recommendation:** AMEND — embed the reference_constants family-(h) bindu tables, the reference_glossary ≥350 terms, and the ≥55 sthira-house karaka rows *inline* (they are fixed classical tables; Cowork should author them, per the campaign's own cardinal principle "Cowork writes it; executor copy-pastes"). Until then this is the second-largest inline gap after yogas.

### §2.4 — Doc 5 — bg_ontology

**Floor (own classes):** ≥380. **Embedded fully-inline count:** ~59 new (upagraha 11 + aspect_type 13 + remedy_type 12 + school 8 + text 15) + ~62 KEPT existing (planets/nakshatras/signs/houses). **Gap:** the ≥70 karaka, ≥40 domain, ≥150 concept classes are NOT inline.

**D1 — PARTIAL.** The 5 fully-inline new classes (~59 rows) are clean and complete. But the three largest classes are completion-noted:
- karaka (≥70) — "author one `_e('karaka',…)` per reference_karakas id" — i.e. ids come from Doc 4 §3.3, which is itself partially-inline. Coupled risk.
- domain (≥40) — ~40 names listed in a comment, "author from the explicit lists below."
- concept (≥150) — ~80 concept names listed in comments across families, "continue to ≥150 from the standard concept vocabulary."

These are real classical names (very low fabrication risk — the bar is "is this a real named concept"), so the integrity risk is low, but the brief still defers ~260 of the 380 own-floor rows to executor enumeration rather than embedding them.

**D2 — PASS.** Names/synonyms sourced from the texts that name the entities; no doctrinal claims to mis-cite.

**D3 — PARTIAL (concrete defect).** The live `brahma_ontology` writer (`l0_ontology.py`) uses columns `canonical_name_en` / `canonical_name_sa` and `ON CONFLICT (entity_class, canonical_id) DO NOTHING` (composite arbiter). The brief's §1 schema block correctly shows `canonical_name_en`, but: (a) its prose and the `_e(...)` example signature say `name_en`/`name_sa`; (b) §0.1's cross-brief idempotency contract and Docs 11/12/13 all specify `ON CONFLICT (canonical_id)` — which will **not match** the live composite unique index unless `canonical_id` alone is also a PK/unique. Doc 5 §1 hedges ("If a UNIQUE(entity_class, canonical_id) … exists, the ON CONFLICT target must match it") — but the catalog briefs do NOT carry that hedge; they hardcode `(canonical_id)`. This must be reconciled to one arbiter before handoff or the catalog ontology inserts may raise.

**D4/D5/D6/D7/D8 — PASS.** The "catalogs own their entity-class rows in the same transaction" contract is the correct resolution of the FK direction; the description-is-one-line tests (no doctrinal leakage) are good.

**Material findings:**
- Schema column-name + ON CONFLICT arbiter mismatch (above) — affects Docs 5, 11, 12, 13.
- ~260 own-floor rows (karaka/domain/concept bodies) deferred to executor enumeration.

**Recommendation:** AMEND — (1) fix the schema field names + ON CONFLICT arbiter to match the live table across Docs 5/11/12/13; (2) embed the karaka/domain/concept names inline (low effort, eliminates the deferral).

### §2.5 — Doc 11 — bg_yogas  ⚠ HIGHEST-PRIORITY FINDING

**Floor:** 250. **Embedded fully-inline yoga dicts:** **25** (verified by counting `"canonical_id":"` occurrences). **Claimed "authored canonical core":** ~130. **Gap: the brief embeds 25 yogas inline against a 250 floor.**

**D1 — PARTIAL bordering FAIL.** This is the asset native singled out, and it is the weakest on the metric native cares most about. The 250 floor is reached from:
1. **"Authored canonical core (~130)"** — but only **25** are actually authored inline (PMP 5, lunar/solar 6, named-combination ~7, Nabhasa 1, raja/dhana/viparita 6). The other ~105 are named in comments: "author the remaining named combination yogas… chandra_mangala, budha_aditya, parvata, kalanidhi…", "musala, nala… gada, sakata… (Akriti ~20)… (Sankhya 7)", "continue the raja/dhana/viparita families." Each of these requires the executor to author `formation_rule_jsonb` + `formation_text` + `significations_text` + citations — that is **doctrinal authoring, not transcription**, despite the brief framing it as "mechanical transcription of a fixed enumeration." The Nabhasa *names* are fixed; their formation geometries and significations are not trivially copy-pasteable.
2. **Corpus extraction (~120+)** from Saravali/BPHS/Phaladeepika chunks via regex, with `formation_rule_jsonb={"needs_structuring":true}` placeholder rows. Deterministic and chunk-cited (good), but (a) depends on bg_texts incl. the manual-upload Saravali PDF, and (b) produces structurally-thin rows (raw clause, not a matchable pattern).

So the brief guarantees ~25 fully-formed yogas inline; the path to 250 runs through executor authoring (~105) + runtime extraction (~120). This is precisely the "thin brief, executor fills the gap" failure mode the master plan §1 says v2.0 exists to prevent: *"Classical content embedded inline (Python data structures the executor copy-pastes, not synthesizes)."*

**D2 — PARTIAL.** The 25 inline yogas cite BPHS Ch.75/30/36-41, Phaladeepika Ch.6-7, Saravali. Some citations are loose (`{"text_id":"classical_tradition"}` for Chatussagara, Viparita trio) — acceptable as "tradition" flags but not chapter/verse. The ~105 commented yogas have no citations yet (they don't exist yet).

**D3 — PARTIAL.** brahma_yoga_catalog INSERT matches migration 176 (category CHECK ∈ 6 values honored; non-PMP→'other'). BUT the ontology insert rides the same `ON CONFLICT (canonical_id)` defect as Doc 5 (§2.4).

**D4 — PASS.** The catalog-first → ontology(`yoga`) → reference_yogas pointer ordering is correct; `depends_on=[bg_ontology,bg_texts]` UPDATE specified (extends migration 179's `[bg_ontology]`). **D6 — PASS** (ON CONFLICT DO NOTHING; deterministic). **D7 — PASS** (rejects below-250, no padding). **D8 — PASS** (hard stop on shortfall is explicit and correct).

**Material findings:**
- **25 inline vs 250 floor is the single biggest Dimension-1 gap in the campaign.** Even granting the corpus-extraction path, the brief should embed the ~130 "core" in full (the campaign's own promise), not 25 + comments.
- The `needs_structuring=true` extraction rows are floor-valid but pattern-match-useless; they inflate the count toward 250 without delivering the structured `formation_rule_jsonb` the holistic design §3.9 specifies as the point of the catalog.

**Recommendation:** REWRITE §3 (and §3.9 framing). Cowork should embed the full ~130-yoga core inline with complete `formation_rule_jsonb` + significations + citations — this is the highest-value authoring work in the whole campaign and is the asset native flagged. Treat corpus extraction as a *supplement above 130*, not a *crutch to reach 130*. If the full 250 cannot be embedded, embed the ~130 core fully and document the extraction supplement as the honest path to 250 with a hard stop — but 25 inline is not acceptable for "the largest content catalog."

### §2.6 — Doc 12 — bg_dasha_systems

**Floor:** 15. **Embedded fully-inline count:** **18** (verified). **Gap: +3 (exceeds floor).**

**D1 — PASS.** This is the model the whole campaign aspires to: 18 complete dasha-system dicts, every field populated (sequence_jsonb, computation_method, computation_pseudocode, conditions_for_use, citations, python_impl_module), copy-paste-ready. Vimshottari/Yogini/Ashtottari cycle-totals are unit-tested against `total_cycle_years`.

**D2 — PASS.** Each cites BPHS Ch.46-50 or Jaimini Ch.1. UNVERIFIED: the conditional-dasha applicability rules (Shodashottari, Dwadashottari paksha/lagna conditions) and some sequence values are standard but I can't confirm each against BPHS Ch.48 without the text — flag for acharya pass. The brief itself says "if a sequence value disagrees with ingested BPHS chunks, the chunk wins" — good humility.

**D3 — PARTIAL.** Same ontology `ON CONFLICT (canonical_id)` + `canonical_name_en` arbiter question as Doc 5; otherwise the catalog INSERT matches migration 176 exactly (base_unit CHECK ∈ {nakshatra_lord,sign_lord,special} honored).

**D4/D5/D6/D7/D8 — PASS.**

**Recommendation:** APPROVE (after the shared ontology-schema fix from §2.4). This brief is exemplary on Dimension 1.

### §2.7 — Doc 13 — bg_doshas

**Floor:** 50. **Embedded fully-inline dosha dicts:** **18** (verified). **Claimed:** ~58. **Gap: 18 inline vs 50 floor; ~37 named-but-not-inline.**

**D1 — PARTIAL.** Better than yogas, worse than dashas. The ~37 non-inline rows are:
- 11 more Kala-Sarpa variants — **genuinely mechanical** (each is `{rahu_house:N, ketu_house:N+6}` + a one-line effect, all given in the comment). Low risk; ~trivially completable.
- ~5 more Ashtakoota compatibility doshas (yoni, vashya, tara, varna, graha_maitri) — need formation rules authored.
- ~4 arishta members (gandanta, shrapit, etc.) — need formation rules authored.

So ~18 inline + ~11 trivially-mechanical (Kala Sarpa) = ~29 reliably deliverable; the remaining ~9 need real authoring to clear 50. The 12-Kala-Sarpa-variant unit test (§6 check 5) is a nice guard. Hard stop on padding is explicit.

**D2 — PARTIAL.** Many doshas cite `{"text_id":"classical_tradition"}` rather than a chapter/verse (Kala Sarpa, Vish, Punarphoo, Sade Sati, compatibility doshas). This is honest — these doshas are genuinely tradition rather than single-text — but it means D2 is "tradition-attested" not "primary-source-cited" for a large fraction. Flag for native: is "classical_tradition" an acceptable citation value, or must every dosha trace to a named text? The campaign's stated D2 rule ("NOT 'tradition'") would mark these as gaps.

**D3 — PARTIAL** (shared ontology arbiter issue). Catalog INSERT matches migration 176 (category CHECK ∈ 5 values; `associated_remedies` seeded `[]` correctly deferred to Tier 3).

**D4/D5/D6/D7/D8 — PASS.**

**Recommendation:** AMEND — embed the ~9 non-mechanical doshas (Ashtakoota + arishta) inline; the 11 Kala-Sarpa variants can stay as the mechanical completion they are. Decide the `classical_tradition` citation policy (affects ~half the rows).

### §2.8 — Doc 6 — bg_texts

**Floor:** ≥14,000 chunks. **Embedded count:** N/A (PDFs, not inline). **Gap:** existing 8,432 + 10 new texts (~8,200 expected) ≈ 16,600 *potential*, minus ~1,300 chunks behind 3 manual-upload PDFs.

**D1 — PASS (with operator dependency).** The chunk floor is reachable: the per-text expected counts (Saravali ~1,800, Brihat Samhita ~2,000, etc.) sum well past 14,000. The 3 manual-upload texts (Tajaka Neelakanthi, Yavana Jataka, Bhrigu Samhita, ~1,300 chunks) are handled with `AWAITING_MANUAL_UPLOAD` + CONDITIONAL-APPROVE — correct and honest. **The campaign cannot reach full floor on first build until native uploads 3 PDFs** — this is the one hard operator prerequisite and it's correctly surfaced.

**D2/D3/D6 — PASS.** Idempotent on content_sha256; embeddings (the only permitted non-determinism) pinned to a fixed model version. **D8 — PASS.** The `bphs_jaimini` vs `jaimini_sutram` text_id reconciliation is flagged honestly.

**Recommendation:** APPROVE. Native action item: confirm the 3 manual PDFs are in GCS (or accept CONDITIONAL seal + later re-build).

### §2.9 — Doc 7 — bg_text_index

**Floor:** ≥400 distinct topic_tags. **D1 — PASS.** Deterministic keyword-rule classifier; the bulk of rules (planet×house 108, lordship 144) are code-generated from PLANETS×HOUSES, and the tag set is exactly `reference_topic_tags` (≥450 from Doc 4). ZERO LLM — explicitly removes the v1.0 Gemini classifier (correctly follows v1.1 over the holistic-design body). Floor depends on (a) Doc 4's topic_tags existing and (b) corpus coverage; CONDITIONAL if corpus incomplete. **D3/D4/D6/D7/D8 — PASS.** depends_on `[bg_texts,bg_reference]` UPDATE specified.

**Recommendation:** APPROVE.

### §2.10 — Doc 8 — bg_rules

**Floor:** ≥3,000 rules. Existing ~1,213. **D1 — PARTIAL.** Strategy is sound (deterministic regex pattern library over the 15-text corpus, quality-gated, ZERO LLM with v1.0 Gemini extraction explicitly superseded). But: (a) the pattern library is specified as "~50 templates" with only ~12 shown and "continue to ~50"; (b) the 3,000 floor is **emergent** — the brief does not demonstrate that ~50 patterns × chunk-count × the ≥0.6 quality gate yields ≥3,000. It is plausible (1,213 existing + 10 new texts + richer patterns) but unproven, and depends on the manual-PDF corpus. Hard stop correctly forbids loosening the quality gate to pad; CONDITIONAL if corpus incomplete.

**D2 — PASS** (rules cite text_id+verse_ref+chunk). **D3 — PASS** (matches migration 081+177; deterministic rule_id computed in Python, not the random default — correct for rebuild). **D4/D5/D6/D7/D8 — PASS.** depends_on `[bg_texts,bg_ontology,bg_yogas,bg_dasha_systems]` specified.

**Recommendation:** AMEND (light) — specify the remaining ~38 patterns (or state a defensible patterns×coverage estimate showing 3,000 is reachable). The quality-gate discipline is good; the floor justification is thin.

### §2.11 — Doc 9 — bg_remedies

**Floor:** ≥800 live remedies. Existing ~200. **D1 — PARTIAL (with a real accounting risk).** Three sources: matrix (~300, only the Saturn cell shown — 8 planets' cells are "executor fills from the standard table"), dosha-linked (~100), corpus sweep (~400). **The accounting risk:** the corpus-sweep ~400 rows are written with `scaffold_status='review'` for native promotion (§3.3), but the floor (and Vimarśaka §7) counts `scaffold_status='live'`. If the ~400 sweep rows sit in 'review', only ~400 (matrix + dosha-linked) are auto-live — **below the 800 live floor at build time**, requiring a native promotion step before the asset can pass. This isn't surfaced as a hard stop.

**D2 — PARTIAL** (navagraha mantras/gemstones cite BPHS Ch.91-94; many matrix cells will be "classical tradition"). **D3 — PARTIAL** — the `remedy_type` vocabulary reconciliation (`fasting`→`vrata`, `ritual`→`puja`) is required and flagged but not yet done; the brief defers it to the executor. **D7 — PARTIAL** — the live-vs-review floor accounting (above) makes the §7 "≥800 live" check potentially unsatisfiable autonomously.

**D4/D5/D6/D8 — PASS** (tantric careful-inclusion gate enforced; ZERO LLM with v1.0 scaffolder superseded).

**Recommendation:** AMEND — (1) resolve the live-vs-review accounting: either auto-promote unambiguous sweep matches to 'live', or lower the auto-live floor and make the 'review' backlog an explicit native action with its own count; (2) embed the 9-planet × category matrix fully inline (it's a "standard table every textbook agrees on" — so Cowork should author it, not defer); (3) author the remedy_type mapping in the brief.

### §2.12 — Doc 10 — bg_concordance

**Floor:** ≥800 chunk-pointer rows (~200 topics × 4-6 schools). **D1 — PARTIAL (emergent floor).** Pure deterministic topic×school chunk-grouping over the corpus — no embedded data needed, correct by construction. But the 800 floor is emergent from corpus coverage: it holds only if ~200 topics each have chunks across ≥4 schools, which depends on the full 15-text corpus (incl. manual PDFs). CONDITIONAL handling present. Correctly implements the v1.1 chunk-pointer model (NO stance_text — matches migration 177 schema exactly; the v1.0 LLM stance-generation is removed). **D2/D3/D4/D5/D6/D7/D8 — PASS.** Schema check confirms the v177 shape (source_chunk_ids BIGINT[], uq_topic_school), not the v158 MSR shape. depends_on `[bg_texts,bg_text_index,bg_reference,bg_rules]` specified.

**Recommendation:** APPROVE (the emergent-floor risk is inherent to a pointer index and correctly CONDITIONAL-gated).

### §2.13 — Doc 14 — bg_compendium_index

**Floor:** ≥3,000 rows. **D1 — PARTIAL (emergent floor).** Pure SQL aggregation: Pass A per-text-chapter (~300) + Pass B per-text-topic (~3,000-4,000). Deterministic, ZERO LLM (summary_text = mechanical first-N-chunks concat; v1.0 Gemini summaries removed). The 3,000 floor depends on Pass B, which depends on bg_text_index having populated `topic_tag` on enough chunks across enough texts — emergent, CONDITIONAL-gated. The brief correctly adds a dedup unique index for idempotency (its own migration, "182+"). **D3/D4/D5/D6/D7/D8 — PASS.** Correctly notes migration 176 created the columns WITHOUT the FK constraints and enforces resolution in code.

**Recommendation:** APPROVE.

### §2.14 — Doc 15 — integration + Vimarśaka-Ω

**D7 — PASS.** Vimarśaka-Ω aggregates all 9 master-plan §5 acceptance criteria as programmatic checks (Ω.1-Ω.9), each returns (ok,message), none vacuous. It folds in the per-asset floors (FLOORS dict matches the briefs), the full FK set (Ω.4 a-f), single-source-of-truth (Ω.6), the layer-Build topo-dispatch (Ω.7, reusing Doc 2's fixture extended to 12), the lit-at-floor cockpit check (Ω.8), and the delete-and-rebuild bit-for-bit proof (Ω.9 + the §3 runbook). **D8 — PASS.** The §4 DAG-completeness check (assert all depends_on edges present before Ω.7) is the right guard against the migration-179-only-4-edges gap. The CONDITIONAL-on-manual-PDFs allowance is consistently applied.

**Material findings:**
- Ω.2's FLOORS dict uses `bg_reference:1450` and `bg_ontology:700` — consistent with the briefs' full-table floors (good), though those full-table floors are only reached after the catalog writers add pointer/entity rows (correctly Tier-ordered).
- The rebuild proof correctly handles the bg_ephemeris special case (multi-minute rebuild) and the embedding-determinism subtlety (hash content_sha256 set, not raw floats).

**Recommendation:** APPROVE. This is the strongest brief in the set.

---

## §3 — Cross-brief findings

### §3.1 — Coverage
All 12 L0 assets have a dedicated brief (Docs 3,4,5,6,7,8,9,10,11,12,13,14). Doc 2 (orchestrator) + Doc 15 (integration) complete the 14. **No asset missing.** ✓

### §3.2 — Migration numbering
- Doc 2 correctly claims **181** (not 180 — 180 is `180_bg_reference_count_sql_fix.sql`, present at HEAD). ✓
- Doc 14 claims "182+ / next free number" for its dedup index. ✓
- **Defect:** the 8 other writer briefs (4,7,8,9,10,11,12,13) each require an `asset_registry SET depends_on` UPDATE migration, but **none reserves an explicit number.** They say "this brief's migration adds it." With Doc 2=181 and Doc 14=182, that leaves 6+ depends_on-UPDATE migrations unallocated. Doc 2 §5.1 anticipates this ("re-confirm the ceiling… use the next integer"), so the executor *can* sequence them — but in a single-PR campaign authored across worktrees this is a real collision risk. **Recommend:** the master plan (or an amendment) should pre-assign migration numbers 181-190 to specific briefs.
- Note: a DIFFERENT brief on disk, `CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING`, claims 187 and `CLAUDECODE_BRIEF_BRANCH_SWEEP` claims 188 — these are OTHER workstreams, not part of this campaign, but they confirm the 181-190 band is contested across concurrent work. Pre-assignment matters.

### §3.3 — Holistic design cherry-pick
Doc 2 §2 cherry-picks `00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md` from `track/l0-brahmagyan-build` with a `test -f … || exit 1` guard. ✓ Confirmed the file exists at `cc61693c` on that branch and is NOT on main.

### §3.4 — File path consistency
All 12 writers target `platform/python-sidecar/pipeline/orchestrator/writers/bg_<asset>.py` (briefs write it relative to python-sidecar as `pipeline/orchestrator/writers/bg_*.py` — same path). Data modules go to `brahmagyan/l0_*.py`. ✓ No brief targets a divergent path.

### §3.5 — Campaign branch
Master plan §4 mandates ONE PR on `feature/l0-unified-build`. Doc 2 creates it; Doc 15 commits/pushes to it. The 12 writer briefs reference no branch (correct — they're all committed to the one campaign branch). No competing per-asset feature branches. ✓

### §3.6 — Integration brief completeness
Doc 15 aggregates all 12 per-asset Vimarśaka checks (Ω.2/Ω.3 fold in each brief's §7), tests the layer-Build click path (Ω.7 + the §3 runbook's actual `POST /api/cockpit/runs` with `scope:'layer'`), and tests delete-and-rebuild (Ω.9 + §3 runbook + snapshot/compare scripts). Hard stops catch each of the 9 ACs. ✓ Fully covers §5.6 of the handoff.

---

## §4 — Material gaps requiring amendment before executor handoff

1. **Doc 11 (yogas) §3 — embed the full ~130-yoga core inline.** Currently 25 yogas are authored inline against a 250 floor; ~105 "core" yogas are named-in-comments and ~120 rely on runtime corpus extraction. Cowork should author the full ~130 core (formation_rule_jsonb + significations + citations) in the brief. This is the highest-value fix and addresses native's primary concern directly. *(Brief Doc 11, §3.1-§3.5.)*

2. **Doc 4 (reference) §3.3/§3.5/§3.7 — embed the deferred classical tables inline.** reference_constants family (h) Ashtakavarga bindu tables (~84 rows), reference_glossary (~270 of 350 terms), and ≥55 sthira-house karakas are named-in-comments. These are fixed classical tables; per the campaign's own principle, Cowork authors them. *(Brief Doc 4, §3.3, §3.5, §3.7.)*

3. **Docs 5/11/12/13 — reconcile the brahma_ontology schema.** Live table uses columns `canonical_name_en`/`canonical_name_sa` and `ON CONFLICT (entity_class, canonical_id)`. The briefs variously say `name_en`/`name_sa` and `ON CONFLICT (canonical_id)`. Pick the live arbiter and field names; correct every ontology INSERT in Docs 5, 11, 12, 13. *(Or: confirm `canonical_id` is independently unique and the composite is redundant — verify against live `\d brahma_ontology` first.)*

4. **Doc 9 (remedies) §3.3/§7 — fix the live-vs-review floor accounting.** Corpus-sweep rows are written `scaffold_status='review'` but the floor counts `'live'`. Either auto-promote unambiguous matches to 'live', or restate the auto-live floor + make the review backlog an explicit native action. Also embed the 9-planet remedy matrix inline and author the remedy_type mapping. *(Brief Doc 9, §3.1, §3.3, §5, §7.)*

5. **Doc 13 (doshas) §3 — embed the ~9 non-mechanical doshas inline** (Ashtakoota: yoni/vashya/tara/varna/graha_maitri; arishta members). The 11 Kala-Sarpa variants can remain the mechanical completion they are. Decide the `classical_tradition` citation policy. *(Brief Doc 13, §3.)*

6. **Doc 8 (rules) §3 — specify the remaining ~38 patterns or justify the 3,000 floor.** The pattern library is "~50 templates" with ~12 shown; the 3,000 floor is emergent and unproven. *(Brief Doc 8, §3.)*

7. **Migration numbering — pre-assign 181-190** to the specific briefs that author migrations (Doc 2=181 fixed; then reference/text_index/rules/remedies/concordance/yogas/dashas/doshas depends_on UPDATEs + Doc 14 dedup index). *(Master plan §4 or an amendment.)*

8. **Citation policy (D2) decision** — across Docs 11/13/9, a meaningful fraction of rows cite `classical_tradition` rather than chapter/verse. The campaign's stated D2 rule forbids "tradition." Native should rule: accept `classical_tradition` as a valid citation value for genuinely tradition-rooted items (Kala-Sarpa, Sade-Sati, compatibility doshas), or require every row to trace to a named text. This is a policy call, not a defect — but it changes whether several briefs' D2 reads PASS or PARTIAL.

---

## §5 — Material gaps that BLOCK executor handoff (if any)

**One conditional blocker and one hard prerequisite:**

- **CONDITIONAL BLOCKER — Doc 11 yogas inline data (§4 item 1).** If native's bar is the master-plan promise ("embedded inline, copy-pasted not synthesized") and the metric native flagged ("did the briefs include all the data points we wanted to collect"), then 25 inline yogas against a 250 floor is a fail of that bar, and the executor running today would deliver a thin yoga catalog padded with `needs_structuring=true` extraction rows — a quieter repeat of the Phase-β shortfall. **This blocks "press Build → acharya-grade yoga catalog" but does NOT block "press Build → 12 tiles light at floor"** (the extraction path will reach 250 rows, just thin ones). Native must decide which outcome is the bar.

- **HARD PREREQUISITE (not a brief defect) — 3 manual-upload PDFs.** bg_texts/text_index/rules/concordance/compendium cannot reach full floor until Tajaka Neelakanthi, Yavana Jataka, and Bhrigu Samhita PDFs are in GCS. The briefs correctly CONDITIONAL-gate this, but the campaign cannot fully seal on first build without the uploads. This is an operator action native already owns.

Beyond those, **nothing in the campaign mechanism (orchestrator, DAG, FK, determinism, Vimarśaka, rebuild proof) blocks handoff.** The schema-reconciliation (§4 item 3) would cause runtime INSERT errors if unfixed, but it's a one-line-per-brief fix, not a rework.

---

## §6 — Findings NOT requiring action

- **Holistic-design-body LLM references.** The v1.1 body (§3.3, §3.6-3.8, §3.12, §7, $150-300 budget) still describes Gemini Flash/Pro. Every brief explicitly supersedes these and follows the v1.1 ZERO-LLM frontmatter lock. The schema (migrations 176/177) bakes in ZERO-LLM (no derived_by/llm_prompt_hash columns). **No action — the briefs handle it correctly;** the stale body is a documentation-hygiene item for a later holistic-design v1.2, not a campaign blocker.

- **Holistic-design floors vs master-plan floors.** The design body says concordance "~200 topics / 800-1,200 rows", compendium "3,000-5,000", yogas "250-350". The master-plan/brief floors (800, 3,000, 250) sit at the low end of those ranges — consistent, not contradictory. No action.

- **bg_reference Tier-0 vs constants-needs-Tier-2 subtlety.** reference_constants family (h) may need bg_texts chunks if not embedded. If §4 item 2 is done (embed the bindu tables), this evaporates. Tracked under item 2; no separate action.

- **`bphs_jaimini` vs `jaimini_sutram` text_id.** Doc 6 flags it and offers two clean resolutions. Executor-resolvable; no pre-handoff action.

- **bg_ephemeris in the rebuild proof.** Doc 15 §3 correctly raises whether to include the 825K-row ephemeris in the clear-and-rebuild (multi-minute recompute) and defers to native. Sensible; no action until native chooses.

---

## §7 — Recommendations summary

1. **Author the full ~130-yoga core inline in Doc 11** before handoff — this is the single highest-value amendment and directly answers native's primary concern. Demote corpus extraction to a supplement above 130, not the path to it.
2. **Embed the deferred classical tables inline in Doc 4** (Ashtakavarga bindu tables, glossary, sthira-house karakas) and **the 9-planet remedy matrix in Doc 9** — the campaign's own cardinal principle is "Cowork writes it; executor copy-pastes," and these are fixed tables, not judgment calls.
3. **Reconcile the brahma_ontology schema** (column names + `ON CONFLICT` arbiter) across Docs 5/11/12/13 against the live `l0_ontology.py` — verify with `\d brahma_ontology` first; this is a runtime-error risk if unfixed.
4. **Fix the bg_remedies live-vs-review floor accounting** (Doc 9) so the ≥800-live floor is autonomously reachable, and embed the remedy_type mapping.
5. **Pre-assign migration numbers 181-190** to the specific briefs authoring migrations, to remove the single-PR collision risk.
6. **Make a citation-policy call** on `classical_tradition` as a valid D2 citation value (affects Docs 11/13/9).
7. **Confirm the 3 manual-upload PDFs** are in GCS, or accept a CONDITIONAL seal with a post-upload re-build (Doc 6/15 already support this).

Briefs that need **no content amendment** (mechanism + data both sound): Doc 2, Doc 3, Doc 6, Doc 7, Doc 10, Doc 12, Doc 14, Doc 15. Briefs needing amendment: Doc 4, Doc 5, Doc 8, Doc 9, Doc 11, Doc 13.

---

## §8 — Verdict

**READY AFTER AMENDMENTS.**

The campaign architecture is genuinely strong — orchestration, dependency DAG, FK discipline, determinism, ZERO-LLM compliance, the Vimarśaka-Ω gate, and the delete-and-rebuild proof are all well-built and would deliver the "press Build → 12 tiles light, deterministically, rebuildably" outcome. Docs 2, 3, 6, 7, 10, 12, 14, 15 are handoff-ready.

But on **Dimension 1 — the metric native explicitly prioritized** — three content briefs (yogas most acutely, then reference and remedies) embed materially fewer data points inline than their floors require, and lean on "the executor completes the fixed classical enumeration" — the exact Phase-β failure mode v2.0 was authored to eliminate. The yogas brief embeds **25 of a 250 floor inline**; that is the finding native most needs to see.

**Recommended path:** amend the 6 briefs per §4 (with items 1-3 being the load-bearing ones), make the two policy calls (citation, manual-PDF timing), then hand off. If native instead chooses to trust the executor to transcribe the fixed classical enumerations under the existing hard-stops, the campaign can ship with only the schema (§4.3) and migration-numbering (§4.7) defects fixed — but that re-accepts the judgment-call risk the unified-build model was designed to remove, and the yoga/reference catalogs will likely land thinner and less structured than the holistic design intends.

---

*End of L0 Brahmagyan Campaign Evaluation Report v1.0.*
