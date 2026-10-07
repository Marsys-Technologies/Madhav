# Review packet — the Kāla layer plan set (value review · code architecture plan · per-asset algorithm elevations)

You are an **independent external reviewer** (Codex gpt-6-astra, extra-high reasoning). The native
(Abhisek Mohanty — the chart owner and the ruling authority) has asked for your review of three
documents that together form the plan for elevating the whole Kāla (L3, timing) layer of the Madhav
Jyotiṣa instrument: not three assets this time, but all twenty-two active assets and the seams between
them. The author (Claude Fable 5.1, Claude Code session, 2026-10-06) will reconcile your findings
finding by finding, incorporate what survives verification, and only then will the native rule and
code begin. Your job, in this order:

1. **Break it.** A duplicated computation the plan does not actually remove; a stage boundary that
   leaks; an "elevated algorithm" that is astrologically wrong, uncited, or invents doctrine; a test
   that cannot fail; a code claim that the code does not support; a classical citation the corpus does
   not bear out; a certification mapping the engine's detectors would not actually pass.
2. **Enrich it.** The native's standing question for Kāla: *how can the layer be elevated so that
   every asset, individually and together, delivers the highest value from the temporal plane of this
   data plane, for any chart?* Name what the classical corpus knows about timing that the plan cannot
   express, and what modern method it should use and does not.
3. **Judge the plan as a plan.** Is it buildable in the order given, with the frozen contracts it
   claims to respect, at a cost the native would recognise as efficient? Where would you re-sequence?

**Standard: acharya-grade.** A senior Jyotiṣa ācārya reading your answer should find it at or above
their own level; a senior engineer should find nothing hand-waved; a statistician should find the
measurement honest. Generic astrology is a failure. So is deference. The author's documents are long
and confident; your value is in what they missed or got wrong.

**Native priorities for this plan, verbatim in substance (2026-10-06):**
1. *Value first.* The goal is that the data the layer generates delivers superlative value for the
   temporal plane for any chart. Certification by the Suvarṇa engine is a receipt the layer must earn,
   not the purpose.
2. *Each asset's algorithm elevated at the depth Gochara received* — not only the plumbing. "Individual
   assets, when coming together, can synergistically deliver value much superior."
3. *The assets working individually, synergistically and in an optimised way* — through a pipeline or
   whichever structure delivers the most value; redundancies between Gochara, Kṣetra and Saṅgam "were
   benefiting nobody".
4. *Build and rebuild efficiency*: the code, and the data rebuild when it happens.
5. *Governance and security at the absolute essential minimum.* Do not spend your review on governance
   unless a governance omission would break value, correctness or the build.
6. Data state today is out of scope: L0–L2 are being rebuilt, so everything downstream will be rebuilt.
   Judge the code and the algorithms, not the current rows.

## Ground rules

- **Read-only.** No code changes, builds, migrations, database writes, PRs, config edits, or edits to
  the documents under review. Your final message is your review (see Output).
- **No database access.** Every `[L]` figure in the documents is the author's own read-only
  production measurement, dated in the text; treat it as *attributed* and say so where a conclusion
  depends on it. Do not connect to any database or start any container.
- **Verify, do not trust.** Every `[S]` claim carries a file:line in a named worktree: open it. The
  author's code claims were produced by three bounded read-only code digests; several are strong
  (for example "the clock term is identically zero", "no obstructive primitive is ever built",
  "every contact is measured against 0° Aries") and you should confirm or refute each one in code
  at file:line. Every `[D]` names a text: check it against the OCR corpus under
  `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` in the code worktree (BPHS, Jaimini_Sutram, KP,
  KP_Reader). The *served* corpus (sixteen texts, including Muhūrta Cintāmaṇi, Phaladīpikā,
  Sārāvalī, Horā Sāra, Uttara Kālāmṛta, Tājaka Nīlakaṇṭhī) is a database table you cannot query; the
  author's `[D]` citations to those texts carry the page:chunk locator the project's own text search
  returned on 2026-10-06. You may CONFIRM a citation from the OCR files; you may not claim ABSENCE from
  the served corpus — label such cases `UNVERIFIABLE_HERE` and say what count should be run.
- Treat every `[I]`, `[U]`, `[A]` in the documents as unproven. Where you supply doctrine the author
  lacked, cite text + chapter/verse/page or label it `[P]` honestly. **Never invent a verse.**
- **Do not re-open ruled items.** Suvarṇa F-2 is decided (Saṅgam elevated as the jury stage, option 2;
  Gochara 5.0 the spine; Kṣetra the odds/attention stage). F-3 is N-32 (the eight cascade keys into
  `bodha_msr_signals` dropped; downstream rebuilt in wave order). D-SCOPE (one chart, `482012f1`).
  The Gochara design specs v1.4 are FROZEN with conditions C1–C10; AM-21 part 4 (P1 pratyantar level
  is testimony). The Kṣetra rulings 1–10, B8-4, B8-6, B8-7 stand. The enrichment order ruled
  2026-10-06: repair existing method semantics → period commencement and lord relationships +
  Sudarśana → qualified Tājaka and KP → relatives deferred. Your own prior review of the pipeline
  concept note (K01–K19, A1–F2) and its reconciliation stand as incorporated. Do say explicitly where
  the plan contradicts a ruling, or where a ruling now looks wrong in light of your findings.
- Labels for your own claims: **[D]** doctrine (text named) · **[P]** practice · **[J]** your
  judgment · **[C]** confirmed in code at file:line · **[R]** refuted in code at file:line ·
  **[U]** could not verify · **[M]** method (statistical/measurement) with the reference named.

## Where things are (absolute paths; read them from disk)

The three documents under review live in the author's main checkout, whose *code* is stale
(`campaign/nirmana-autonomous @ badc3f9bc`, 2026-09-09). **Do not read code from that checkout.**
Read code from the `cooperative-racer` worktree, which is `origin/main @ c751f3bd8` (2026-10-04) and is
the revision every `[S]` file:line in the documents refers to. `origin/main` has since moved to
`09fd39b4d` (2026-10-06); the only Kāla-relevant difference the author found is
`pipeline/orchestrator/writers/ka_gochara_v5.py`; the pravaha worktree carries the Gochara campaign's
newer state if you need it.

| What | Path |
|---|---|
| **Document 1 — the layer value review** (evidence base: coverage of the temporal plane, served reality, 25-row disposition register, findings F-L1…F-L22) | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_0.md` — sha256 `ff74f7bb2638aaaaa9bb2662b332ec9025cae9f8d148a6115857244b57b5eec0` |
| **Document 2 — the code architecture and build plan** (one engine: core library, stages, projections, serving plane, rebuild efficiency, certification by construction, dispositions, the three family plans folded item by item in §8.1, packets K0–K9, routed decisions R-1…R-10, questions 1–9) | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_0.md` — sha256 `08784d5095df1d42b581c99aae0d2452151e04166eae23b56839551f061221b0` |
| **Document 3 — the per-asset algorithm elevations** (depth standard §1; corpus check register §2; twenty-one asset cards §3.1–§3.21; algorithm-level findings F-A1…F-A14 §4; card→packet map §5; questions 1–7 §6) | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_0.md` — sha256 `8128e5ff0583ae1d8ac2c55932817aa7ad72eea290302ad499a5bd3f509994e7` |
| **Code on `origin/main` (the writers, services, kernels, serving)** — all `[S]` file:line resolve here | `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/platform/python-sidecar/` (services: `ka_*`, `gochara_kernel`, `gochara_rules`, `gochara_v3`, `gochara_grammar`, `gochara_intensity`, `kala_trigger`, `kala_permission`, `w2g`, `taranga_kernel`, `ka_temporal`, `muhurat`, `panchang_engine`; writers: `pipeline/orchestrator/writers/ka_*.py`; the frozen contract: `pipeline/orchestrator/writers/__init__.py`, `pipeline/orchestrator/asset_runner.py`; `pipeline/transit_search.py`; `brahmagyan/kala/`, `brahmagyan/l0_transit.py`, `brahmagyan/l0_phaladeepika_vedha.py`, `brahmagyan/l0_kota_chakra_rings.py`) · serving: `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/platform/src/lib/retrieval/registry/layers/L3_kala/`, `.../platform-mcp/src/tools/kala_views/`, `.../platform/src/lib/pipeline/compiled_floor_adapter.ts`, `.../platform/scripts/manifest/web_tool_bridge_builder.ts` · the certification engine the plan's §7 maps to: `.../platform/scripts/governance/asset_census.py` (`CRITERION_REGISTRY`), `nikasha_certify.py`, `asset_declarations.json`; `.../00_ARCHITECTURE/control/asset_elevation_tracker.py`, `LEVEL_MAP.json`, `FAMILY_ASSETS.json` · registry seed: `.../platform/scripts/seed/asset_registry_seed.ts` · seeded field weights: `.../platform/supabase/migrations/491_kala_field_weights_seed.sql` |
| The pipeline concept note you reviewed, your review, and the reconciliation (continuity) | `/Users/Dev/madhav-l3/sangam-final/00_ARCHITECTURE/briefs/l3_families/KALA_PIPELINE_CONCEPT_NOTE_v1_1.md`, `…/reviews/ASTRA_REVIEW_KALA_PIPELINE_CONCEPT_v1_0.md`, `…/reviews/RECONCILIATION_KALA_PIPELINE_CONCEPT_v1_0.md` |
| Gochara 5.0 (the judge) — read the latest spec present | `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md` (and `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md`); `…/design/L3_FAMILY_COORDINATION_v1_0.md`; `…/measurement/EVALUATION_PROTOCOL_v2_1.md`, `…/EVENT_REGISTRY_v2_1.md`, `…/BASELINE_3_0_v2_1.md`; the sealed doctrine `…/sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` and your `…/sealed/ASTRA_REVIEW_GOCHARA_ASTRO_v1_0.md`; the registered-writer brief `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md` |
| The three family plans the code plan folds (§8.1) | `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/{GOCHARA_FAMILY_ELEVATION_PLAN_v2_1, GOCHARA_RULING_SHEET_v2_0, KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0, KSHETRA_RULING_SHEET_v1_0, SANGAM_ELEVATION_FINAL_v1_0, SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4, SANGAM_RULING_SHEET_v1_0}.md` and `…/l3_autonomous/KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md`, `…/KALA_IO_USE_MATRIX_v1_0.md` |
| The approved layer strategy and the Suvarṇa campaign documents the plan must fit | `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`; `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_5.md` §1–§2, `…/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md`, `…/l3_recon/{GOCHARA,KSHETRA,SANGAM}_RECON.md` |
| The earlier Kāla vision the plan inherits (for completeness questions) | `/Users/Dev/madhav-l3/sangam-final/00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_SIX_VIEWS_DESIGN_v2_0.md`, `…/KALA_W2_FIELD_DESIGN_v1_0.md` (Kṣetra's science), `…/KALA_TRANSFORMATION_HANDOFF_v1_0.md` |
| Project doctrine the plan must obey | `/Users/Dev/Vibe-Coding/Apps/Madhav/.kilo/worktrees/cooperative-racer/CLAUDE.md` §N.2–§N.8 (frozen writer contract; idempotency; density; narration fidelity; earned signals); `…/00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` §3.10–§3.11, §7, §12 |

## Read in this order

1. Document 2 §0–§2 (the brief and the architecture), then Document 3 §0–§2 (depth standard and
   corpus register), then Document 1 §0 and §3 (what the layer covers and what it serves).
2. Document 3 §3, every card, **with the code open**: for each card confirm or refute the "Today"
   paragraph at file:line, then judge the "Elevated algorithm" as an ācārya and the "Oracles" as an
   engineer. The author's §4 findings F-A1…F-A14 are the claims most worth independent confirmation.
3. Document 2 §3 (the duplication register and the core library), §4 (stage contracts and grains),
   §6 (rebuild efficiency), §7 (certification by construction, mapped to the engine's detectors —
   open `asset_census.py` and judge whether each row would actually read PASS).
4. Document 2 §8 and §8.1 (dispositions and the fold of the three family plans) against the family
   plans themselves: is anything ratified dropped silently or mis-mapped?
5. Document 2 §9–§13 and Document 3 §5–§6 (packets, tests, risks, routed decisions, questions).
6. Only then Document 1 in full, for anything the later documents contradict.

## Questions put to you (answer each; number your answers)

**A. Code truth**
A1. Confirm or refute, at file:line, each of F-A1…F-A14 (Document 3 §4) and F-L19…F-L22 (Document 1
§8). For any you refute, state what the code does instead.
A2. The duplication register (Document 2 §3.1) claims eight ephemeris/transit-scan implementations,
two disagreeing aspect tables, six daśā readers, five promise formulas. Verify the counts and name any
duplicate the author missed or any "duplicate" that is in fact a legitimate variant.
A3. Does `kala_core` as specified (Document 2 §3.2) actually remove each duplicate, or does it move
them? Name any module whose proposed consolidation would change a result the frozen Gochara spec
depends on.

**B. The algorithms, as an ācārya**
B1. For each card in Document 3 §3, does the elevated algorithm follow the cited doctrine, and is any
step an invention presented as classical? Pay particular attention to: 3.1 (competence classes; start
conventions), 3.3 (a promise graph with no scalar strength), 3.4 (six negative-space states), 3.12
(aligning the adapter to the judge's vedha), 3.13 and 3.15 (serving two contested conventions), 3.16
(Sudarśana as a judge method), 3.17 (muhūrta doṣa and parihāra from Muhūrta Cintāmaṇi).
B2. The author claims Muhūrta Cintāmaṇi's cancellation verses (PG26 v. 34, PG67 v. 13, PG110 v. 68,
PG115–116 vv. 88–91) are in the served corpus and were never extracted into `bg_parihara_rules`
(60 rows, all natal scope). The OCR folder lacks that text, so you cannot confirm the pages; judge
instead whether the *rules as stated* are the tradition's and whether applying marriage-chapter
parihāra to other undertakings is defensible.
B3. What does the corpus know about timing that none of the twenty-one cards expresses? Walk the
toolkit: Vimśottarī sub-sub lord relationships; conditional daśās' entry conditions; Nārāyaṇa; the
Kālacakra deha/jīva transitions; Sudarśana's nested periods; Tājaka varṣaphala with Mudda, Muntha,
sahams and the sixteen yogas; praśna as cross-check; gochara to Moon vs lagna vs daśā-lord frames;
aṣṭakavarga śodhya-piṇḍa timing; tārā; eclipses and nodes; Sade-sati; KP; argalā/virodha; Kāla-sarpa;
nāḍī timing. For each: in which stage, with what source status, and whether the plan has a slot for it.
B4. Negative space (3.4): is the six-state typology complete for what the texts say about *when things
do not happen* (bādhaka, māraka, denial yogas, "no result until…")? Is representing a cancelled
obstruction as `obstruction_active` with `cancelled_by` honest, or does it need its own state?
B5. The promise graph (3.3) makes L1 facts plus versioned L0 rules the universe of promise and lets the
L2 reading attach. Is that the right source, and what is lost if the reading's mechanisms are only
attachments?

**C. Structure and synergy**
C1. Is "three foundations, three stages, one negative-space producer, one manifest, projections as
SQL" the right shape for the native's third priority, or would a different structure deliver more
value for the same effort? Give the alternative you would defend.
C2. Projections as pure SQL (Document 2 §4.3): which of the eleven readers carries a distinction that
is *not* derivable from the stages' assertion rows? (Candidates: Jivana Parva's chapter diff; the
recurrence ladder; Taranga's monthly integral; Darshana's net reading.)
C3. The layer-wide three-lineage invalidation (Document 2 §6.2 item 3) relies on the orchestrator's
edge-based staleness over a truthful `depends_on`. Does the frozen runner actually support what the
plan needs, or is a manifest-aware predicate required that the freeze forbids?
C4. The compact field (3.20, Document 2 §6.2 item 4): is the knot set (clock boundaries of non-zero
systems, contact in/out instants, mask edges) sufficient for W2's likelihood, and what byte-equality
sampling would prove it? Is one shift-null per generation over shared segments the same estimand as
W2's per-class dense null?
C5. With the clock term having been zero in every stored field (F-A1), is the Kṣetra ablation
pre-registration (ruling 10) still the right admission test for the forecaster?

**D. Build and rebuild**
D1. Judge the packet order K0–K9 and the parallelism claim. What should move earlier or later, and
what depends on the judge's `'5.0'` landing that the plan says does not?
D2. The plan keeps asset ids and re-shapes tables by strangler columns (R-5). Name the failure modes
for `kala_activation_predicates`, `kala_convergence`, `kala_obstruction`, `kala_field` and the L4/L5
readers of them.
D3. Is the rebuild-cost argument (§6.1–§6.2) sound, and what should the benchmark contract measure
first?

**E. Certification, minimally**
E1. Open `asset_census.py` (`CRITERION_REGISTRY`) and `nikasha_certify.py`: for each of the nine
rows of Document 2 §7, would the described mechanism actually read PASS under the current detector, or
`PARTIAL` / `NO_DETECTOR`? Name any row where the plan's mechanism and the detector disagree.
E2. Is anything in the plan's governance more than the essential minimum the native asked for? Cut it.

**F. Rulings and sequencing**
F1. Where do the three documents contradict a standing ruling, or where does a ruling now look wrong?
F2. Of the ten routed decisions (Document 2 §12) and the plan's own questions (Document 2 §13,
Document 3 §6), give your recommendation on each in one line, and say which can be taken on your
recommendation rather than by the named owner.
F3. In one paragraph: what the native should rule on next, in what order, and what the first packet
to code should be.

## Output (your final message is the review; write no file)

Head your review with a frontmatter block: `artifact: ASTRA_REVIEW_KALA_LAYER_PLAN`,
`version: "1.0"`, `reviewer: "Codex gpt-6-astra — independent read-only review (extra-high
reasoning)"`, `date`, `reviewed_files_sha256` (the three documents; recompute with `shasum -a 256`
and print them), `verdict_per_document` (for each of the three: `PROCEED` | `PROCEED_WITH_AMENDMENTS`
| `REWORK`), `verdict_overall`, `authority: "Review only; authorizes nothing."`.

Then:

1. **Verdict and the five findings that matter most**, in plain prose (the native reads this part).
2. **Findings table** — id · severity (BLOCKING / HIGH / MEDIUM / LOW) · document and section · what ·
   evidence (file:line, text:verse/page, or `[J]`) · what would close it.
3. **Confirmation register for F-A1…F-A14 and F-L19…F-L22** — each `[C]` confirmed at file:line,
   `[R]` refuted with what the code does, or `[U]`.
4. **Answers A1–F3**, numbered, each with its label(s).
5. **The enrichment register** — everything the layer could additionally say about time that the
   cards do not, each with source status, owning stage or asset, the data it needs, and a cost class
   (small / medium / large).
6. **What to cut** — anything in the three documents that costs effort without earning value, and
   any governance beyond the essential minimum.
7. **Doctrine you are confident of and the author lacked**, with citations; and **doctrine you are
   not sure of**, labelled `[P]` or `[U]`, with the count or read that would settle it.
8. **Hashes** — the sha256 of every file you read and relied upon, recomputed.

Be exhaustive where it matters and silent where it does not. Confirmations are cheap; a finding the
author missed is what the native is paying for.
