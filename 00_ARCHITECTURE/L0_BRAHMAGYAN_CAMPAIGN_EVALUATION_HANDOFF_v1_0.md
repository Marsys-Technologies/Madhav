---
artifact: L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_HANDOFF
canonical_id: L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_HANDOFF
version: 1.0
status: ACTIVE
authored_by: Cowork (planning) 2026-06-08
purpose: Self-contained handoff document for a NEW Cowork conversation to thoroughly review the 14 L0 Brahmagyan briefs BEFORE the campaign is handed to the executor (Claude Code in Antigravity)
how_to_use: |
  Paste this entire file (or attach it) as the FIRST message to a new Cowork conversation.
  The receiving conversation will have full context to perform a thorough evaluation of all 14 briefs.
  No prior conversation history needed beyond this file.
output_required: A single gap-analysis-and-recommendations report saved to 00_ARCHITECTURE/L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT_v1_0.md
---

# L0 Brahmagyan Campaign — Evaluation Handoff

> **You are the reviewer.** A previous Cowork conversation authored 14 briefs (Documents 2–15) of a unified-build campaign that will, when executed, populate the L0 Brahmagyan layer of MARSYS-JIS to or beyond design-target row counts. Native wants you to evaluate the briefs THOROUGHLY against expectations BEFORE handing them to the executor. Your output is a single gap-analysis-and-recommendations report.

## §0 — What you are NOT doing

- You are NOT executing any brief
- You are NOT modifying any brief (your output is a report; native decides whether to amend briefs based on your findings)
- You are NOT running code, queries against prod, or any I/O beyond reading the briefs and supporting documents
- You are NOT doing acharya-grade classical accuracy review on individual yoga/dosha definitions (that's a separate review pass; this one is about COMPLETENESS, COVERAGE, and STRUCTURAL INTEGRITY)

## §1 — Project context (brief)

**MARSYS-JIS** is an LLM-operated Vedic Jyotish instrument for native Abhisek Mohanty (born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India). The layer architecture is L0 Brahmagyan (foundation; classical knowledge) → L1 Gaṇita (chart facts) → L2 Bodha (intelligence) → L3 Kāla (temporal) → L4 Phala (prediction) → L5 Mīmāṃsā (learning).

**L0 Brahmagyan** holds the foundation: ephemeris, classical text corpus, reference tables, ontology, extracted rules, remedy catalog, yoga/dosha/dasha catalogs, cross-school concordance. It is global (not per-chart); every chart in the system reads from it.

**Phase α** sealed the schema (12 asset_registry rows + 14 backing tables via PR #225). **Phase β** shipped the writer infrastructure + thin slices of bg_reference (88 rows) and bg_ontology (102 entities) via PR #227 — but with KNOWN SCOPE SHORTFALL. This campaign supersedes Phase β with full-content writers.

**The desired outcome (locked):** native presses "Build" at the Brahmagyan layer in cockpit → all 12 L0 assets autonomously populate to or beyond their design-target row counts, deterministically, with full source citation, and the cockpit transitions all 12 tiles from dormant to lit.

## §2 — The 14 briefs you are evaluating

All 14 briefs live in `00_ARCHITECTURE/BRIEFS/`. Read them in this order (it matches the campaign dependency DAG):

| # | Brief | Asset | Target floor | Tier |
|---|---|---|---|---|
| 2 | `CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0.md` | (orchestrator — not an asset) | N/A (gated by Vimarśaka-FIX) | −1 |
| 3 | `CLAUDECODE_BRIEF_BG_EPHEMERIS_v1_0.md` | bg_ephemeris | ≥825,084 rows | 0 |
| 4 | `CLAUDECODE_BRIEF_BG_REFERENCE_v1_0.md` | bg_reference (15 typed tables) | ~2,000 rows total | 0 |
| 5 | `CLAUDECODE_BRIEF_BG_ONTOLOGY_v1_0.md` | bg_ontology | ≥700 entities | 0 |
| 11 | `CLAUDECODE_BRIEF_BG_YOGAS_v1_0.md` | bg_yogas | ≥250 yogas | 1 |
| 12 | `CLAUDECODE_BRIEF_BG_DASHA_SYSTEMS_v1_0.md` | bg_dasha_systems | ≥15 dasha systems | 1 |
| 13 | `CLAUDECODE_BRIEF_BG_DOSHAS_v1_0.md` | bg_doshas | ≥50 doshas | 1 |
| 6 | `CLAUDECODE_BRIEF_BG_TEXTS_v1_0.md` | bg_texts | ≥14,000 chunks (15 texts) | 2 |
| 7 | `CLAUDECODE_BRIEF_BG_TEXT_INDEX_v1_0.md` | bg_text_index | ≥400 distinct topic_tags | 3 |
| 8 | `CLAUDECODE_BRIEF_BG_RULES_v1_0.md` | bg_rules | ≥3,000 rules | 3 |
| 9 | `CLAUDECODE_BRIEF_BG_REMEDIES_v1_0.md` | bg_remedies | ≥800 remedies | 3 |
| 10 | `CLAUDECODE_BRIEF_BG_CONCORDANCE_v1_0.md` | bg_concordance | ≥800 chunk-pointer rows | 4 |
| 14 | `CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md` | bg_compendium_index | ≥3,000 index rows | 4 |
| 15 | `L0_BRAHMAGYAN_INTEGRATION_AND_REBUILD_PROOF_v1_0.md` | (integration + Vimarśaka-Ω) | N/A (campaign seal) | — |

## §3 — Supporting documents you MUST read first

Read these BEFORE the briefs themselves. They define the expectations the briefs must meet.

1. **`00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md`** — campaign master plan. Defines acceptance criteria for the whole campaign, dependency DAG, locked principles.

2. **`00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md`** (v1.1) — the design that the master plan operationalizes. Contains the per-asset target row counts, FK relationships, single-source-of-truth rules.

   > **Important caveat:** the holistic design body (not its frontmatter) still mentions Gemini Flash/Pro in several places. The master plan frontmatter and the v1.1 amendments lock ZERO LLM. When evaluating briefs, treat ZERO LLM as the binding rule; flag any brief that violates it.

3. **`00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF_v1_0.md`** — the handoff document that briefed the previous Cowork conversation on what to author. §5 (asset targets) and §8 (sources by asset) define what the briefs were SUPPOSED to cover.

## §4 — Evaluation framework (the 8 dimensions)

For each brief, evaluate against these 8 dimensions. Score each dimension as PASS / PARTIAL / FAIL with one-line evidence. Native cares MOST about Dimension 1 (data point coverage); that's the primary criterion.

### Dimension 1 — **Data point coverage** (PRIMARY — this is what native called out)

**Question:** does the brief embed (or specify how to deterministically generate) enough source-cited data points to hit OR EXCEED the asset's target floor?

For asset briefs, this means:
- Count the embedded Python data structures / YAML rows / catalog entries in §3 of the brief
- Compare to the target floor from §2 of THIS handoff
- Identify the gap (positive = exceeds target; zero = meets target; negative = falls short)
- For briefs that augment embedded data with corpus extraction (e.g. bg_yogas using inline-embedded entries + Saravali extraction), assess whether the extraction strategy is deterministic, attestation-preserving, and likely to deliver the needed delta

Evidence requirements per brief:
- bg_reference: count rows across the 15 typed tables collectively; floor is ~2,000
- bg_ontology: count entries across the 15 entity classes; floor is 700
- bg_yogas: count yogas in §3; floor is 250
- bg_dasha_systems: count dasha systems in §3; floor is 15
- bg_doshas: count doshas in §3; floor is 50
- bg_remedies: count remedies in §3; floor is 800
- bg_ephemeris: data already in prod; floor is 825,084 (wrapper brief — verify count check exists)
- bg_texts: 15 source PDFs spec'd; floor is 14,000 chunks (verify chunker spec produces enough chunks per PDF)
- bg_text_index: topic_tag rule library size; floor is 400 distinct topic_tags (verify rule library would produce ≥400 distinct tags)
- bg_rules: regex pattern library size; floor is 3,000 rules (verify pattern library × chunk count would yield ≥3,000 rules)
- bg_concordance: topic × school matrix size; floor is 800 chunk-pointer rows
- bg_compendium_index: aggregation row count; floor is 3,000 (verify SQL aggregation logic over bg_texts produces enough rows)

**The HONEST question for each brief:** "if I were the executor, could I deliver the floor JUST FROM what's in this brief without any judgment calls?"

If the answer is no for any brief, that's a Dimension 1 PARTIAL or FAIL.

### Dimension 2 — **Source citation discipline**

Every data point in every brief must trace to a primary classical source (BPHS chapter/verse, Saravali, Phaladeepika, etc.) — NOT to "tradition" or "as known classically" or "interpolated from X."

Evaluate:
- Spot-check 10-20 random data points per content brief (yogas, doshas, dashas, remedies, ontology, reference)
- For each: does the brief cite a specific primary source?
- Are any citations vague ("classical tradition" without chapter/verse)?
- Are any citations fabricated (sources that don't exist OR don't contain the cited content)?

If you cannot verify a citation independently, flag as `UNVERIFIED` rather than FAIL — note for native's separate acharya review.

### Dimension 3 — **Schema accuracy**

Each writer brief specifies columns it INSERTs into. Verify against migrations 176–179 (and 180/181 if added) on `main`:

- Does the brief's INSERT column list match the actual table schema?
- Are NULL constraints honored (every required column gets a value)?
- Are CHECK constraints honored (category enums, etc.)?
- Are ON CONFLICT clauses using the correct unique index columns?

### Dimension 4 — **FK integrity discipline**

Per holistic design §4 and master plan §5, every cross-asset reference must resolve:
- reference_* .canonical_id ⊂ brahma_ontology
- brahma_yoga_catalog.canonical_id ⊂ brahma_ontology (entity_class='yoga')
- brahma_dosha_catalog.canonical_id ⊂ brahma_ontology (entity_class='dosha')
- brahma_dasha_systems.canonical_id ⊂ brahma_ontology (entity_class='dasha_system')
- etc.

Evaluate:
- Does each brief VALIDATE its FK references before INSERT?
- Does each catalog brief (yogas/doshas/dashas) populate its own ontology entries AND pointer rows in the same transaction (per master plan §3 chicken-and-egg resolution)?
- Are any FKs declared but unimplemented?

### Dimension 5 — **Dependency DAG correctness**

Master plan §3 + Document 2 §6 require that each asset's depends_on edges in asset_registry match the DAG.

Evaluate:
- Does each writer brief INCLUDE a migration UPDATE for its asset's depends_on?
- Do the declared dependencies in each brief's frontmatter match the brief's writer code dependencies?
- Are there any unstated dependencies (writer imports something from another asset's writer module without declaring it)?

### Dimension 6 — **Determinism + reproducibility**

Per locked principles, every writer must produce byte-identical output across runs given the same source data.

Evaluate:
- Does every brief specify ON CONFLICT DO NOTHING (not DO UPDATE — Phase β learning)?
- Does every brief avoid timestamp-based content fields (only `computed_at` / `created_at` are allowed to drift)?
- Does any brief introduce non-determinism (random ordering, set iteration without sorting, dict iteration without sorting)?
- For bg_texts: are embeddings the ONLY Vertex AI call (per master plan §7)?

### Dimension 7 — **Vimarśaka check completeness**

Each brief §7 specifies its per-asset Vimarśaka check.

Evaluate:
- Does the check verify row count ≥ floor?
- Does the check verify source_citation NOT NULL on a sample of rows?
- Does the check verify FK integrity?
- Are any checks vacuous (e.g. `assert True`)?
- Does Document 15's Vimarśaka-Ω aggregate all per-asset checks plus the 9 campaign-level acceptance criteria from master plan §5?

### Dimension 8 — **Hard stops + scope discipline**

Each brief §8 declares hard stops and out-of-scope items.

Evaluate:
- Are the hard stops likely to trigger when the brief actually runs (real failure modes), or are they decorative?
- Does any brief silently expand scope (touches files outside its stated surface)?
- Does any brief introduce LLM use anywhere (violates the ZERO LLM lock)?

## §5 — Cross-brief consistency checks

Beyond per-brief evaluation, verify these CROSS-BRIEF properties:

### §5.1 — Asset coverage

All 12 L0 assets from master plan §2 have a brief (12 asset briefs). Confirm.

### §5.2 — Migration numbering

Each brief that authors a migration should claim a unique number. Verify no collisions:
- Document 2's global-index migration was renumbered from 180 to 181 per native's late-conversation note. Confirm the brief uses 181 (not 180).
- Each writer brief's depends_on UPDATE migration claims a number. Verify uniqueness across all 14 briefs.

### §5.3 — Holistic design v1.1 cherry-pick

The holistic design v1.1 lives only on `track/l0-brahmagyan-build` (commit `cc61693c`), not on `main`. Document 2 §2 was supposed to cherry-pick it onto the campaign branch as the first setup step. CONFIRM this is present in Document 2.

### §5.4 — Writer file paths

All writer briefs target `platform/python-sidecar/pipeline/orchestrator/writers/<asset_id>.py`. Verify no brief targets a different path.

### §5.5 — Campaign branch name

Master plan §4 specifies ONE PR for the whole campaign on branch `feature/l0-unified-build`. Verify Document 2 §2 creates this branch and subsequent briefs reference it (not separate feature branches per asset).

### §5.6 — Integration brief (Document 15) coverage

Document 15 is the final Vimarśaka-Ω gate. Verify it:
- Aggregates all 12 per-asset Vimarśaka checks
- Tests the layer-level "Build" click path (the actual outcome native cares about)
- Tests the delete-and-rebuild proof
- Has hard stops that would catch each of the 9 acceptance criteria from master plan §5 failing

## §6 — Output format (the report you save)

Save your findings to `00_ARCHITECTURE/L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT_v1_0.md` with this structure:

```markdown
---
artifact: L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT
version: 1.0
status: REVIEW_COMPLETE
reviewed_by: Cowork (review pass) <date>
reviewed_for: Abhisek Mohanty
---

# L0 Brahmagyan Campaign — Evaluation Report

## §0 — Executive summary

[3-4 sentences. Headline: are the 14 briefs ready for executor handoff, or are there material gaps?]
[State: how many briefs PASS / PARTIAL / FAIL on Dimension 1 (data point coverage).]
[State: any campaign-level red flags (LLM violation, missing cherry-pick, FK chain breaks).]
[Recommendation: PROCEED TO EXECUTOR / AMEND <N> BRIEFS THEN PROCEED / MATERIAL REWORK NEEDED.]

## §1 — Per-brief evaluation matrix

A table with one row per brief × one column per dimension (1-8). Cell values: PASS / PARTIAL / FAIL / N/A. Bold any FAIL.

| Brief | D1 Data | D2 Cite | D3 Schema | D4 FK | D5 DAG | D6 Detrm | D7 Vimar | D8 Stops |
|---|---|---|---|---|---|---|---|---|
| Doc 2 (orch) | N/A | N/A | PASS | N/A | PASS | PASS | PASS | PASS |
| Doc 3 (ephem) | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS |
| Doc 4 (reference) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 5 (ontology) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 11 (yogas) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 12 (dashas) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 13 (doshas) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 6 (texts) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 7 (text_idx) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 8 (rules) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 9 (remedies) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 10 (concord) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 14 (compendium) | ? | ? | ? | ? | ? | ? | ? | ? |
| Doc 15 (integration) | N/A | N/A | N/A | N/A | N/A | N/A | PASS | PASS |

## §2 — Detailed findings per brief

For each brief, one subsection:

### §2.X — Doc N — <asset_id>

**Floor:** <N>. **Embedded count:** <N>. **Gap:** <+N | 0 | -N>.

**Data point coverage (D1):** [explicit count and analysis. If the brief embeds 130 yogas with floor 250, state the strategy for the remaining 120 — is it deterministic corpus extraction from Saravali? Is it identified explicitly with a hard stop if the extraction shortfalls?]

**Citation discipline (D2):** [spot-check results — sampled N citations, M traced to primary sources, K unverified, L vague or fabricated]

**Schema (D3):** [column-list match to migration X; FK columns match]

**FK integrity (D4):** [does this writer validate its FKs before INSERT? does it populate ontology + pointer rows in the same transaction for catalog briefs?]

**DAG (D5):** [depends_on UPDATE migration present? frontmatter dependencies match code dependencies?]

**Determinism (D6):** [ON CONFLICT DO NOTHING confirmed? no LLM use? no non-deterministic iteration?]

**Vimarśaka check (D7):** [check structure summary; verifies floor + citation + FK?]

**Scope discipline (D8):** [hard stops realistic? no scope creep?]

**Material findings (if any):** [bulleted list]

**Recommendation:** [one of: APPROVE / AMEND (with specifics) / REWRITE (with reasons)]

## §3 — Cross-brief findings

### §3.1 — Coverage
[Are all 12 assets covered? Any missing?]

### §3.2 — Migration numbering
[Any collisions? Doc 2 using 181 not 180?]

### §3.3 — Holistic design cherry-pick
[Doc 2 §2 includes the cherry-pick from track/l0-brahmagyan-build cc61693c?]

### §3.4 — File path consistency
[All writers under platform/python-sidecar/pipeline/orchestrator/writers/?]

### §3.5 — Campaign branch
[All briefs reference feature/l0-unified-build?]

### §3.6 — Integration brief completeness
[Document 15 aggregates per-asset checks + tests layer-Build path + tests delete-rebuild proof?]

## §4 — Material gaps requiring amendment before executor handoff

[List concrete, specific changes needed. For each: which brief, what section, what change.]

## §5 — Material gaps that BLOCK executor handoff (if any)

[Anything in §4 that you assess as critical enough that the executor would fail if it ran today. If empty, say so explicitly.]

## §6 — Findings NOT requiring action

[Things you observed that look concerning but on reflection don't need amendment. Documented so native sees you considered them.]

## §7 — Recommendations summary

[3-7 bullet points. Each is concrete and actionable.]

## §8 — Verdict

One of:
- **READY FOR EXECUTOR** — all dimensions PASS or PARTIAL with documented mitigations; no FAILs; no critical gaps
- **READY AFTER AMENDMENTS** — specific list of amendments from §4; executor handoff after those land
- **NOT READY — MATERIAL REWORK** — listed reasons; recommendation on which briefs to rewrite from scratch
```

## §7 — How to do the evaluation efficiently

The 14 briefs are substantial. To stay efficient and avoid token bloat:

1. **Read the three supporting documents first** (§3 of this handoff). Internalize the expectations.
2. **Pass 1 — Read each brief skim-style** (5-10 min per brief, ~2 hours total). Build a mental map of structure + claimed content.
3. **Pass 2 — Per-brief detailed evaluation** against the 8 dimensions. Take notes in the matrix as you go.
4. **Pass 3 — Cross-brief checks** from §5 of this handoff.
5. **Write the report** to the path in §6.

Estimate: **3-5 hours of focused review time** for the full pass. Don't try to do it all in one sitting; stop and resume cleanly between briefs.

## §8 — What "thorough" means here

Native specifically called out:
> "Besides all the matrices that you have mentioned regarding evaluation, my one of the most important aspects is as the 14 briefs or especially the 12 asset briefs have included all the data points that we wanted to collect in each of these assets is an important metric of evaluation."

This is Dimension 1. **Lead with it. Be specific about counts.** "Brief X embeds N entries; floor is M; gap is K" — these are the sentences native wants to read.

If a brief uses corpus extraction or deterministic enumeration to reach the floor (rather than fully inline embedding), that's acceptable IF the extraction is deterministic + attestation-preserving + has a hard stop on shortfall. Don't penalize the strategy; do penalize incomplete spec of the strategy.

## §9 — What to do when you find a problem

For each material gap (a real shortfall in Dimension 1 or any FAIL in any dimension):

1. **Document it precisely** — brief, section, what's wrong, what should be there instead
2. **Recommend a fix** — concrete enough that an amendment session could execute it without further analysis
3. **Don't fix it yourself** — your job is the report; native decides what to amend

## §10 — Tone for the report

- Concise. The report is for native's decision-making, not for archival completeness.
- Specific. Numbers and citations over generalities.
- Honest. If a brief over-promises, say so. If your evaluation has limits ("I cannot verify Saravali Ch.41 V.5 citation without a copy of Saravali"), say so explicitly — don't silently substitute confidence for knowledge.
- Action-oriented. End each finding with what to do about it.

## §11 — When you're done

1. Save the report to `00_ARCHITECTURE/L0_BRAHMAGYAN_CAMPAIGN_EVALUATION_REPORT_v1_0.md`
2. Tell native: "Evaluation complete. Report at <path>. Verdict: <one of the three from §6>. Top 3 findings: <bullets>."
3. STOP. Do not begin amending briefs unless native explicitly asks.

## §12 — Context cross-references (for your reading list)

- Master plan v2.0: `00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md`
- Holistic design v1.1: `00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md` (note caveat in §3 of this handoff)
- Campaign authoring handoff: `00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_CAMPAIGN_HANDOFF_v1_0.md`
- 14 briefs: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_*_v1_0.md` (per §2 of this handoff)
- Migrations: `platform/supabase/migrations/176_*.sql` through `179_*.sql` (defines the 14 backing tables); newer migrations 180+ may be added by Document 2 or writer briefs

## §13 — Memory pointers (load if available)

If these memories exist in your space, they provide useful context:

- `[[deterministic-first-for-data-build]]` — ZERO LLM stance
- `[[l0-phase-alpha-truly-sealed]]` — schema state
- `[[l0-phase-beta-shipped]]` — what shipped before this campaign
- `[[pr-quality-gate-is-not-a-merge]]` — verify merge before "complete" claims
- `[[cockpit-v1-v2-split]]` — cockpit render architecture

If these memories aren't in your space, that's fine — this handoff contains the substantive context.

## §14 — Final note from prior conversation

The prior Cowork conversation authored these 14 briefs over multiple sessions, held the no-fabrication rule above the floor throughout, and explicitly flagged where reaching a floor required corpus extraction supplements (e.g. bg_yogas embedding ~130 yogas inline + extracting from Saravali corpus to reach 250) and where the v1.1 ZERO-LLM rule overrides holistic-design body passages.

Your job is to verify these claims hold up under scrutiny. Native explicitly asked: "as the 14 briefs or especially the 12 asset briefs have included all the data points that we wanted to collect in each of these assets is an important metric of evaluation." Lead with data point coverage. Be specific. Save the report. Stop.

---

*End of evaluation handoff document.*
