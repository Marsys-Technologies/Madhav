---
artifact: GOCHARA_FAMILY_ELEVATION_PLAN
canonical_id: GOCHARA_FAMILY_ELEVATION_PLAN
version: "2.0"
status: SUPERSEDED
superseded_by: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (2026-09-23) — the Kimi K3 review (KIMI_K3_REVIEW_GOCHARA_v1_0.md) reconciled in KIMI_RECONCILIATION_GOCHARA_v1_0.md; this file is retained as the reviewed text"
intended_use: "The final Gochara-family plan for the L3 (Kāla) elevation. Becomes FINAL on (a) reconciliation of the Kimi K3 review (KIMI_K3_REVIEW_GOCHARA_v1_0.md) and (b) the native's rulings on §1.3."
supersedes: "GOCHARA_FAMILY_ELEVATION_PLAN_v1_0.md (NATIVE_RATIFIED_PLAN — its D-1/D-2/D-3 and R1–R10 are carried here VERBATIM in force; this document consolidates, it does not re-open them) · GOCHARA_FAMILY_ELEVATION_BRIEF_v1_2.md (consolidated; retained as the measurement record for Appendices B–E cited below)"
review_of_record: "ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md (independent, PROCEED_WITH_AMENDMENTS, folded in at v0.3/v1.0) · Kimi K3 max-effort review: PENDING at this version"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
governing_strategy: ../../MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md
campaign_plan: ../MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md
product_parent: ../../../../MADHAV_PRODUCT_DEFINITION_v3_0.md
asset_or_interface_ids: ["ka_gochara_resonance", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_vedha_gochara", "ka_moorti_nirnaya", "ka_kota_chakra (proposed-use)", "ka_gochara_sweep (protected history)", "GocharaTransitService (S-1)", "L3-U11 packets P-1..P-4", "L3-U02 V-1 (Saṅgam-owned)", "K-1 (Kṣetra-owned)"]
source_revision: "origin/main c58e86662e692e678f64934f1689ccaa0fdcd7d7; worktree /Users/Dev/madhav-l3/integration (codex/madhav-l3-claude-code); evidence_gochara/E1–E8 @ 5d8252dbe; kernel spike 2026-09-23 on the same worktree"
live_measurement: "2026-09-22 and 2026-09-23, amjis-postgres via cloud-sql-proxy, role amjis_app, transaction_read_only=on; catalog, privilege and aggregate reads only; no private narrative row printed"
native_priorities: "1. quality of what the asset delivers  2. build efficiency  3. the ecosystem matters as much as the asset"
implementation_owner: "<unassigned — the native assigns; one writer surface per packet>"
independent_review_owner: "<unassigned — not the author>"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/gochara_kernel/** (NEW, unimported until adopted)", "pipeline/orchestrator/writers/ka_gochara.py", "services/ka_gochara_resonance/writer.py", "services/gochara_intensity/enrichment.py (target resolution only)", "services/ka_vedha_gochara/**", "services/ka_moorti_nirnaya/**", "services/gochara_v3/{engine,interval_solver,threshold,resolution_hierarchy}.py (H-1..H-6 only)", "services/ka_gochara/service.py (S-1 only)", "tests/l3/**", "NEW relations: kala_gochara_contacts, kala_gochara_coverage, kala_gochara_publication (migrations ≥1075)", "kala_gochara_windows WHERE generation='4.0' (NEW publication generation, this writer's own)", "kala_gochara_windows_v2 WHERE generation='2.0'; kala_gochara_v2_build_state WHERE generation='2.0'", "gochara_resonance_map; kala_vedha_gochara; kala_moorti_nirnaya (per-chart partitions)"]
must_not_touch: ["platform-mcp/src/tools/kala_views/**", "platform-mcp/src/tools/retrieval/register_gochara_windows.ts (packet P-1 is OWED to its owner, not written here)", "platform/src/lib/retrieval/registry/layers/reading_checklist.ts (P-2 owed)", "applied migrations 1033–1070; supabase/migrations/1035,1036", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1' (protected history; untouchable)", "kala_gochara_windows WHERE generation='3.0'; kala_gochara_windows_v2 WHERE generation LIKE 'g3_%' (century; hold stands)", "pipeline/transit_search.py; brahmagyan/l0_ephemeris.py; services/ka_dasha_kala/**", "platform/scripts/seed/asset_registry_seed.ts (cross-campaign; HELD — registry changes go by migration, N-9)", "services/ka_kshetra/**; services/ka_sangam/**; services/ka_kota_chakra/** (sibling owners)", "kala_gochara_authority (flipped only under 527's four gates at WP10, by the release authority)"]
does_not_authorize: "A production build, migration, registry edit, lifecycle change, deployment, guard weakening, asset retirement, or release of the century hold. The 2026-08-21 standing order (no gochara re-materialization without fresh explicit authorization) remains in force and is discharged only at WP10. WP1–WP7 are local/synthetic work under execution-brief §3."
changelog:
  - "2.0a (2026-09-23, after the Kimi K3 launch — additive; Kimi reviewed the pre-2.0a text): four items from the Kṣetra session's reviewed packet folded in and verified here: N-4a placement rule (L0-owned mean-node derivation; row-level node_mode/epoch declaration); F-13 correction (Kṣetra S0 is a knot consumer, not a scanner consumer); F-23/G-8 false BPHS Ch.29 citation at L0 bg_transit_rules (corpus-verified: Ch.29 = Bhāva Padas; BPHS has no gochara chapter; Phaladīpikā Ch.26 co-citation stands); N-10/P-1d/K-1 removal of the 'v1' COALESCE fall-through (absent authority = unpublished)."
  - "2.0 (2026-09-23): FINAL-candidate consolidation. New since v1.0/brief v1.2: §5 verified upstream contracts incl. the per-target-type TARGET RESOLUTION CONTRACT (§5.3) with three new resonance findings (F-19 negative-result sensitive_degree targets 154/176; F-20 arudha longitude is a sign-cusp placeholder; F-21 two yoga ids with no live firing row, 54 rows); §6 verified downstream contracts with file:line for every reader and the exact registry/digest/Clear re-pins; §4.7 publication model (N-10: generation '4.0' + kala_gochara_publication manifest; authority evidence_ref = manifest id, no change to 527's table); N-11 disposition of _v2 '2.0'; K-1 Kṣetra hidden edge (registry depends_on lacks ka_gochara while stage4_field.py:1384 reads the served table and writer.py:952/1063 pins rows by id); M-5/M-6 new deferred method calls; Appendix C kernel spike on real Swiss files (retflag 258). Carries D-1..D-3, R1–R10, H-1..H-6, M-1..M-4, N-1, N-4/N-4a, N-5..N-9 unchanged."
  - "1.0 (2026-09-22): native ratification of D-1/D-2/D-3; R1–R10 under standing instruction. Brief v1.0→v1.2 (2026-09-22/23): group shape, N-5..N-9, node four-way split, ephemeris backend/epoch corrections."
---

# Gochara family — final elevation plan (v2.0)

**Evidence labels.** `[X]` executed in this work (`evidence_gochara/E1–E8`, `OUTPUT_2026-09-20.txt`; Appendix C kernel spike) · `[L]` live measurement, dated (Appendix A) · `[S]` source read at the pinned revision, `file:line` · `[R]` repository record · `[I]` inference · `[U]` unmeasured. A number without a label is a proposal, not a fact.

**How to read this in ten lines.** The product's transit engine today serves a century of *envelopes* — decade-wide bands with no record of which planet touched which natal point when (§3, F-01). The contacts are computed and thrown away. This plan keeps the family's astrology (resonance targets, the λ_v3 scoring projection, Vedha/Moorti overlays, the protected v1 history) and changes the *machinery*: a small deterministic kernel solves every (body × target × relation) contact once per chart on Swiss sidereal arcs, persists it as a first-class Contact object with orb, branch, bracket and coverage, and the existing scoring becomes a projection over that ledger instead of a per-instant search. `ka_gochara` becomes the honest owner of the served product under a new immutable publication generation beside `v1` and `3.0`; the century writer stays held and donates its engine; nothing is retired. Every upstream input and every downstream reader has been read at source and measured live; the changes each one needs are listed with file and line (§5, §6). The build that today takes hours becomes minutes, but no cap, coarser grid or narrower horizon is accepted as a speedup (§4.5, Strategy §5). Three decisions are already ratified (D-1..D-3), ten under the standing instruction (R1–R10), eleven are proposed here for the native (§1.3), six method calls are deliberately deferred to evidence (§8.2).

---

## 1. Decision ledger (consolidated)

### 1.1 Closed by explicit native ruling, 2026-09-22 (carried verbatim from PLAN v1.0 §1.1)

- **D-1 — Sidereal convention:** Swiss Ephemeris's own sidereal mode (`FLG_SIDEREAL`, `SIDM_LAHIRI`) for all Gochara geometry. The two in-repo methods differ by nutation, up to ~16.5″ `[X]`; removing nutation closes the gap to 0.0000″ `[X]`. Every stored contact carries its convention vector (§4.1). Consequence G-4 (L1 natal nutation offset) disclosed, not repaired here.
- **D-2 — Guard policy:** prove the backup (real restore of all 38,287 `v1` rows into a disposable DB, content-checked), then a guard keyed on **(table, generation)** protecting `'v1'` only, then fix the cockpit Clear route, after mapping the full mutation surface. **Sequence amendment N-1 (proposed, §1.3):** close the live deletion path *first*, then grant, then drill, then guard — because the drill cannot run today (F-05) and the path is ordinary-user-reachable (F-03).
- **D-3 — Scoring process, split:** six honesty fixes H-1..H-6 pre-approved (§8.1); method calls M-1..M-4 deferred to rulings with comparison evidence (§8.2). The load-bearing distinction: an honesty fix makes the code do what it already claims; a method call changes what the astrology asserts.

### 1.2 Closed under the standing instruction ("go with your recommendation") — R1–R10 stand

One accountable windows asset under `ka_gochara`, variants as named projections, full gate set before any century retirement (R1) · new pure kernel, one-way dependency, no Kṣetra import (R2) · sub-day computation free, claim grain governed, precision fields separated (R3) · inputs-first ordering (R4) · two-step mechanism admission after an operand audit, W21 not first (R5) · R6 superseded by D-2 · Moon on demand with full-interval search (R7) · binding fields reserved now plus a minimum L2 structural slice before terminal acceptance (R8) · register the frame defect, label rather than delete, dispatch through a governed control (R9) · registry reconciliation early, not at cutover (R10).

### 1.3 Proposed for the native's ruling in this document

| id | Decision | Recommendation | Where |
|---|---|---|---|
| **N-1** | Re-sequence D-2 | close Clear path → grant → drill → guard | §9 step 0–3 |
| **N-4** | Node convention for Gochara geometry | **mean node** — served L1 natal is mean (`RAH_MEAN`/`KET_MEAN`, `c520713087b97470`), DAR and FORENSIC agree | §4.1, brief v1.2 App. C |
| **N-4a** | Disposition of the TRUE-node L0 knots (`ephemeris_daily`) that the kernel reads | **(b)** keep the knots; mean-node Rāhu/Ketu derived analytically at read time by **one implementation owned by L0's ephemeris service** (never a consumer-side copy — that would be a §N.5 shadow), with `node_mode` and `epoch_convention` declared on the `ephemeris_daily` row beside `ayanamsha_id` (additive migration, no rebuild); consumers (this kernel, Kṣetra, Saṅgam) call it and record the result in their convention vector. Placement rule adopted from the Kṣetra session's reviewed packet (2026-09-23) and verified as necessary here. Route the L0 receipt discrepancy (G-6) to L0's owner | §4.1, §5.1 |
| **N-5** | Who owns the served product | **`ka_gochara`**, writing a new generation into `kala_gochara_windows` beside `v1`/`3.0`; century held, engine donated | §2.2 |
| **N-6** | Century disposition | qualified compact substrate + refinement projection; hold stands; no retirement now | §4.5 |
| **N-7** | Contact object | **persist** as `kala_gochara_contacts`, owned by `ka_gochara`, exact-instant grain | §4.3 |
| **N-8** | Kota / Tithi edges | Kota stays proposed-use (M-4 operand audit first); Tithi's declared century edge retired *as an edge* | §5.4 |
| **N-9** | Registry-hold release condition | (i) Clear `is_active` filter landed; (ii) seed correction co-owned; (iii) integrity conjunct failing when `target_table` ≠ `count_sql` relation | §6.3 |
| **N-10** *(new)* | Publication generation label and manifest | label **`'4.0'`** in `kala_gochara_windows`; a `kala_gochara_publication` manifest row per (chart, generation); authority flip writes the manifest id into `kala_gochara_authority.evidence_ref` (existing column; 527's table unchanged). **Authority owner named:** `ka_gochara` publishes candidates; the release authority flips. **And the `COALESCE(…, 'v1')` fall-through is removed from every reader** (`register_gochara_windows.ts:641-643`, `stage4_field.py:1384-1389`): an absent authority row means **`unpublished`**, served as a coverage object, never a silent `'v1'` default — Strategy §4 step 3's forbidden pattern, flagged by the Kṣetra session's review; adopted here as P-1d and K-1 | §4.7, §6.2 |
| **N-11** *(new)* | `kala_gochara_windows_v2` generation `'2.0'` rows (87 canonical / 163 total, unserved) | PRESERVE through WP10; at WP10 delete under the writer's own §N.3 scope once `'4.0'` is verified (they are regenerable, fingerprinted, and served by nothing) — alternative: keep as `HISTORICAL_RESTRICTED` | §6.3 |
| **N-12** *(new)* | Resonance target corrections that remove or re-type existing target rows (F-19, F-20, F-21) | treat as **honesty fixes** (the targets claim a sensitivity the cited fact denies), pre-approvable under D-3's own distinction; the *enrichment* of new target classes (E-1) stays a method call (M-6) | §5.3 |

### 1.4 Deferred by design — method calls with evidence first (D-3)

M-1 contact-interval activity · M-2 dwell weighting · M-3 the Moon's participation in the score (Moon stays in the evidence under every option, ADJ-14) · M-4 which mechanisms enter scoring and in what order (operand audit first; annual-stack item gated on G-2) · **M-5** *(new)* anchoring of sign-level targets (bhava, arudha, mechanism_node): whole-sign residence span vs bhāva-madhya / cusp point — shared question with Saṅgam's M-1a; until ruled, sign-level targets are **interval** objects, never point contacts · **M-6** *(new)* admission of new target classes with real degrees that L1 already serves but resonance never targets (special lagnas, nakṣatra pādas, Gulika/Māndi, Prāṇapada, bhāva-ārūḍhas; §5.3 E-1) — classical basis per class before any row is emitted.

### 1.5 Not mine to close

G-1 strategy denominator amendment for R1 (native + strategy owner) · G-2 Q3 independent-witness definition (blocks M-4's annual-stack item) · G-3 Q8 cross-asset truncation policy (Gochara's share settled by H-5) · G-4 L1 natal nutation offset (L1 owner) · G-5 provisional ontology signature models (L0) · **G-6** *(new)* L0 `ephemeris_daily` receipt-vs-data discrepancy: `DAR_CLOSE_v1_0.md:20` records a MEAN-node rebuild (Rāhu 49.04°) but the live store is TRUE node to 0.000″ `[L]`, and `l0_ephemeris.py:290` calls `calc_ut(jd, 11, …)` (TRUE) under a "mean" comment `[S]` (L0 owner) · **G-7** *(new)* Saṅgam's own call site passes a symmetric aspect set `[0,60,90,120,180]` (`ka_sangam/engine.py:464`) instead of the per-graha classical table that this family's path already uses `[S]` (Saṅgam R-series) · **G-8** *(new)* strike the "BPHS Ch.29" half of the citation on `bg_transit_rules` (F-23) at L0; note that no `bg_phaladeepika_vedha` relation exists live — the writer file of that name registers `bg_vedha_malefic_scale` and `bg_phaladeepika_latta` only `[S][L]` — so any "admitted source chain" must name `bg_transit_rules` (Phaladīpikā Ch.26 co-citation) until L0 lands a dedicated relation (L0 owner). Raised by the Kṣetra session; verified in the corpus here · **G-9** *(new)* admit Phaladīpikā (Sastri 1950 translation is the edition `bg_transit_rules` cites) — and, if the rows are to stay verse-cited, Sārāvalī and Jātaka Pārijāta — to `SOURCE_DATA/classical_texts/`, or else re-grade every gochara-vedha row as `cited_outside_admitted_corpus` uniformly across the three consumers (corpus/L0 owner).

### 1.6 Needs measurement, not a ruling

Cold full-workload century build time `[U]` (native reports 20–25 h; longest single completed run 58.2 min, 270/270 substeps over a 5.02 h span across attempts `[L]`) · full-century λ distribution `[U]` · Moorti ingress misclassification rate `[U]` · contact-ledger storage size (estimate §4.3) `[U]` · Clear-route invocation history `[U]` · whether the W2G V3 runner calls `set_ephe_path` (source question; brief App. D) `[U]` · whether any production build ever ran with `/app/ephe` unpopulated `[U]`.

---

## 2. The family as it stands, and what we keep

### 2.1 Members, tables, generations, readers — measured `[L][S]`

| Member | Writer (registered) | Writes | Rows (canonical / total) | Who reads it today |
|---|---|---|---|---|
| `ka_gochara_resonance` | `services/ka_gochara_resonance/writer.py` | `gochara_resonance_map` (8 target types, 27 classes; 27-class completeness gate `:518-549`) | 765 / — (14–40 per class, mean 28.3) | `ka_gochara`, century, Kṣetra (declared) |
| `ka_gochara` | `pipeline/orchestrator/writers/ka_gochara.py` (`TABLE` `:120` = `_v2`) | `kala_gochara_windows_v2` generation `'2.0'` + `kala_gochara_v2_build_state` (`:438-458`) | 87 / 163 | **nothing served** — only `scripts/w2g_equivalence_report.py` `[S]`; registry `target_table` says `kala_gochara_windows` (the held seed mismatch) |
| `ka_gochara_v3_century_materialize` | `…/ka_gochara_v3_century_materialize.py` (`GENERATION_V3` `:354`, `GENERATION_PROD` `:360`, `TABLE` `:482`, `PROD_TABLE` `:487`) | `_v2` `g3_utkarsha` (staging) **and** `kala_gochara_windows` `'3.0'` (production) | 914 / 1,830 (`3.0`) | **the product**: three MCP tools, `reading_checklist`, D8/D9, Kṣetra stage 4 — all via `kala_gochara_authority = '3.0'` |
| `ka_gochara_sweep` | none (`@register` removed at migration 563) | `kala_gochara_windows` `'v1'` | 16,297 / 38,287 (3 charts) | validation benchmark only; `is_active=false`, `superseded_by='ka_gochara'`, `data_disposition='RETAINED_AS_CAPITAL'` |
| `ka_vedha_gochara` | `services/ka_vedha_gochara/` | `kala_vedha_gochara` | 177 | century (`context.py:449`), Saṅgam (`ka_sangam.py:1060`, **undeclared**) |
| `ka_moorti_nirnaya` | `services/ka_moorti_nirnaya/` | `kala_moorti_nirnaya` | 71 | century (`context.py:510`) |
| `ka_kota_chakra` | Stream A | `kala_kota_chakra` | 585 | declared as century input; **not read** by `ClassContext.fetch` `[S]` |
| `GocharaTransitService` | not an asset | no table; live compute over `transit_search.py` | — | Saṅgam (`engine.py:464` `find_aspects`; `:1383` bypasses it for long horizons) |

Overlays span **2026-07-08 → 2027-10-11** on the canonical chart — the rolling −60/+400 d window, 1.26 % of the served century; outside it the century's `quality_gates` is 1.0 and Moorti is absent `[L]`.

### 2.2 What we keep, and what happens to the rest (decision N-5, N-6)

- **Kept as the served owner: `ka_gochara`.** It is already the registry's authority (`sweep.superseded_by='ka_gochara'`), active, W2-eligible, and its registry `target_table` already names the production relation. After elevation it writes: the contact ledger (§4.3), the coverage manifest (§4.4), and the windows projection into `kala_gochara_windows` under generation `'4.0'` (§4.7). It stops writing `'2.0'`.
- **Kept as the astrology: the century engine.** λ_v3 = PROMISE × PERMISSION × activity × tārā × w30 × quality_gates, the resolution hierarchy, chains and vocabularies migrate into `ka_gochara` as the scoring projection over the ledger. The century **writer** stays held, untouched, with `'3.0'` selectable for rollback and `g3_*` staging preserved as calibration corpus. Lifecycle: `PRESERVE` → `INVESTIGATE_CONSOLIDATION` → only `RETIRE_AFTER_MIGRATION` under R1's full gate set and a Strategy denominator amendment (G-1).
- **Kept, corrected: resonance, Vedha, Moorti** (`ENRICH_CORRECT`, §5.3, §5.4).
- **Kept, untouched: `v1`** (protected history; Phase 1.1 guard) and **Kota** (proposed-use, M-4).
- **Adopted, not imported: the proven arc/solver functions** of `services/w2g/` and Kṣetra S0, re-homed in a new `services/gochara_kernel/` with a one-way dependency (R2); S0's known defects are not imported (`E8`).
- **Nothing is retired.**

---

## 3. Findings register (consolidated; each names its fix)

| id | Finding | Class | Evidence | Fixed by |
|---|---|---|---|---|
| **F-01** | Served rows carry **no qualified contact**: `active_sentences='[]'` on 914/914 gen-`3.0` rows; `term_breakdown.activity_terms` holds 25,518 partial records on 380/914 rows (primitive, planet, target_ref, instant, orb_decay, p_i) but no orb in degrees, applying/separating, branch, bracket, root time, tolerance or coverage; 534 rows carry nothing. Both windows tables: 33/34 columns, all `DATE` grain. Contacts are computed in `_gather_sentences_no_db` (`engine.py:1063-1137`) and discarded | computed-but-discarded (register *b*); generation regression vs `v1` (16,276/16,297 rows carried sentences) | `[L]` App. B 12–14 `[S]` | N-7, WP6 |
| **F-02** | **13 of 27 classes have no timing window anywhere in the century** (marriage, career_advancement, illness_acute, surgery, childbirth, …); an ordinary quarter (2027-03→05) serves 22 rows, all `is_timing_window=false`; marriage 2013 = one 2004→2014 envelope where `v1` served 52 daily rows | product capability gap | `[L]` App. B 16–19 | kernel + M-1 |
| **F-03** | Cockpit Clear can delete the 38,287 protected `v1` rows through the retired sweep's own `count_sql` (precedence `EXPLICIT_CLEAR_OPS` → `count_sql` prefix-swap → `target_table`; no `is_active` filter; any chart owner; `execute/route.ts:160-182`, `assetClearSpec.ts:29-46`, `clear/route.ts:93,114-117`) | live hazard (B1) | `[S][L]` | Phase 1.1, N-1 |
| **F-04** | No protection exists: migration 588 dropped all three triggers and emptied `build_protected_assets` (applied 2026-08-23T05:33Z); the century's stored `last_error "BUILD-PROTECTED…"` is dated 2026-08-21 — residue. The prompt's "migration 566's guard — working" is live-refuted | stale premise (B2/B4) | `[L]` | D-2 step 2 |
| **F-05** | Restore identity `data_plane_builder` has no SELECT on either `v1` archive; archives cover 35,620/38,287 ids | drill blocker (B3) | `[L]` | Phase 1.2 |
| **F-06** | `ka_gochara.py:268` `date.today()` fallback moves the ±3 y horizon with the clock; breaks 1018's digest determinism | non-reproducible build (B5) | `[S]` | WP1 (kills at kernel adoption) |
| **F-07** | **Frame defect (F3):** `bg_gochara_arcs` is built on `tropical_longitude` (`w2g/db_source.py:35,80,178`; `ayanamsha_id='tropical'`), then joined to sidereal natal targets — Saturn contact error up to 763 d | wrong zodiac | `[X]` E1 | kernel (D-1) |
| **F-08** | λ_v3 is a step function on the served path; `lambda_thresh=0.0` with `>=` certifies 0.0 as active; `_eval_single` exception → 0.0 → "active" (F13) | honesty | `[X]` E2/E6 `[S]` | H-2, H-3 |
| **F-09** | `kakshya_cell_crossing` runs on the served path with `conn=None` → `equal_eighths_fixture_approximation` (`primitives.py:664-719`); 147/202 sentences, 59 % of cost; served activity ∈ [0.99964844, 1.0] on all 380 rows with a value (F15) | fixture on served path | `[X]` E3/E4 `[L]` | H-1 |
| **F-10** | Era window = whole decade range; `MAX_PEAKS_PER_ERA_WINDOW=3` truncates before persistence | truncation as absence | `[X]` E5 `[S]` | H-3, H-5 |
| **F-11** | Overlay coverage 1.26 % of century silently reads as `quality_gates=1.0` outside it (A06) | unknown-as-clear | `[L]` | G-O on kernel; F06 states |
| **F-12** | Resonance keeps only the first source root (`setdefault`) and strips the `afflicted` qualifier | discarded (register *b*) | `[L]` | G-R |
| **F-13** | Node convention is a **four-way split**: served L1 natal = MEAN (`pyjhora_adapter`), L0 `ephemeris_daily` = TRUE (stored = Swiss TRUE noon to 0.000″), `transit_search.py` = TRUE, `l1_positions.py` + six importers = TRUE, `bg_cohort` = TRUE (independent). **Correction to brief v1.2 N-4a's reader list (2026-09-23, raised by the Kṣetra session, verified here):** Kṣetra S0 does **not** read `transit_search.py` — it consumes `ephemeris_daily` knots directly and only the `MEAN_MOTIONS` constant (`stage0_kinematics.py:747`) `[S]`; it is a knot consumer, not a scanner consumer. Blast radius: 40/765 targets, 232/914 served rows, 6,225/16,297 `v1` rows; max divergence 1.933°, 1.021° at birth; TRUE→Rohiṇī pāda 4 vs MEAN→pāda 3 at the birth instant on real Swiss | convention | `[L][S][X]` brief App. C | N-4/N-4a; G-6 |
| **F-14** | Ephemeris backend is silent: without `set_ephe_path`, `FLG_SWIEPH` returns `retflag 260` (Moshier); with `/private/tmp/se1` (checksums = `Dockerfile.pipeline:22`), `258`. Moshier true-node error bounded −65.3″..+58.1″ over 55,152 noon knots. A "kernel vs Swiss" gate run on Moshier is Moshier-vs-Moshier and cannot fail | vacuous detector (§N.8) | `[X]` brief App. D | §10 gate condition; `ephemeris_backend` in convention vector |
| **F-15** | Epoch: stored knots are noon UT; a midnight comparison shows a spurious 332.3″ | unit error | `[X]` | `epoch_convention` in convention vector |
| **F-16** | `_v2` `'2.0'` is `UNRESOLVED_USE`: register claims "gochara service; MCP" receivers; neither reads it | register drift | `[S]` | N-11 |
| **F-17** | Saṅgam reads `kala_vedha_gochara` (`ka_sangam.py:1060`) with no `depends_on` edge (`[L]` registry) | hidden edge | `[S][L]` | V-1 |
| **F-18** *(new)* | **Kṣetra hidden edge:** `stage4_field.py:1373-1389` reads `kala_gochara_windows` via the authority filter and `writer.py:952,1063` stores `source_table='kala_gochara_windows', source_pk=id`; registry `depends_on` lists `ka_gochara_resonance` but **not** `ka_gochara` | hidden edge; consumer pinned by row id | `[S][L]` | K-1; §9 cutover note |
| **F-19** *(new)* | **154 of 176 `sensitive_degree` targets cite a NEGATIVE check result** (`not_gandanta` 44, `mrityu_bhaga not_fired` 44, `not_pushkara` 40, `kartari none` 26): `_FETCH_SENSITIVE_FACTS_SQL` (`writer.py:380-385`) selects by subject and key with no value filter. Only 22 rows (papa/śubha kartari, pushkara) cite a positive condition — and those are properties of a graha's degree, not separate points | ungrounded target (B.10, §N.7 item 6) | `[L][S]` App. A 24 | N-12 (G-R) |
| **F-20** *(new)* | **`arudha_pada.longitude_sidereal` is a sign-cusp placeholder** — every value is 30·(sign−1) (270.0000, 0.0000, 60.0000 …) `[L]`. Resolving arudha targets "to degree" would fabricate exact contacts at cusps | B.10 hazard | `[L]` App. A 25 | §5.3: arudha = **sign-level** target (M-5) |
| **F-21** *(new)* | **2 of 13 `yoga_constituent` ids (`ardhachandra`, `chatra`; 54 rows) have no `ga_yoga_firings` row for this chart under ANY ayanāṃśa today** `[L]`, although the fetch filters `fired=true` (`writer.py:394-407`) — the referent existed at the resonance build of 2026-09-10 and has since been dropped by an L1 rebuild | dangling L1 reference (§N.5); input-generation drift | `[L]` App. A 26 | §5.5 input vector; N-12 |
| **F-22** | Directed special aspects are exercised (`drishti_contact` on 379/914 rows) — not a producer gap; the only defect is Saṅgam's call site | attribution | `[L][S]` brief App. E | G-7 |
| **F-23** *(new)* | **False classical citation at L0:** `bg_transit_rules.classical_citation` reads "BPHS Ch.29 (Gochara Phala — Transit Results)" on all 41 vedha-checkable rules and on others `[L]`; in the Santhanam corpus Chapter 29 is **Bhāva Padas** and BPHS has no gochara chapter (2 incidental mentions in vol. 1, 0 in vol. 2) `[R]`. The co-citation Phaladīpikā Ch.26 (Gochara Vedha) is the real source and stands, so the rows are mis-cited, not uncited. The Vedha writer's docstrings repeat it (`ka_vedha_gochara/logic.py:13,:105`, `writer.py:30`) `[S]`; migration 266's header carries the same line | narration fidelity (§N.7) | `[L][R][S]` | G-8 (L0 table); G-O (writer text) |

---

## 4. Target design

### 4.1 Convention vector — pinned first (D-1, N-4, F-14, F-15)

Every ledger row, coverage row and publication manifest carries, by reference to one `convention_id`: `zodiac=sidereal` · `ayanamsha=lahiri_chitrapaksha` · `sidereal_method=swe_flg_sidereal` (D-1) · `node_model=mean` with `node_source=analytic_from_true_knots` (N-4a(b); L0-owned derivation, §1.3) · `epoch_convention=noon_ut_knot_abscissa` · `ephemeris_backend={swieph, sepl_18.se1 ca1393ce…, semo_18.se1 1ca07bd6…, seas_18.se1 a2cd8fc3…}` or `moshier` — recorded from `retflag`, never from the requested flag · `time_scale=UT→TT via swe.deltat` · `house_system=whole_sign` for sign-level targets. Two rows with different convention ids are **not comparable** and no tolerance is quoted across them.

### 4.2 The kernel — episodes, not samples (R2, R3; Appendix C)

`services/gochara_kernel/` (new, pure, unimported until adopted): (i) **arcs** — monotone-arc index over a cubic spline on the noon-UT knots of `ephemeris_daily`, converted per D-1 to sidereal *before* arc-building (fixes F-07); direction, wrap and station structure explicit; **no station coalescing** (`STATION_MERGE_DAYS` is not carried over); (ii) **contacts** — for each (body, target longitude, relation ∈ {conjunction, dṛṣṭi at the per-graha classical angles `SPECIAL_DRISHTI_DEG`, sign-ingress, nakṣatra-ingress, kakṣyā-cell crossing, return}) bracket every root from the arc index, then refine by direct Swiss bisection at the instant; (iii) **episodes** — for each root, `t_in / t_exact / t_out` at a declared orb, `branch ∈ {direct, retrograde, station}`, dwell, `exact_crossing`, truncation at horizon edges (start-inside and end-inside episodes emitted, not dropped); (iv) **residence spans** for sign-level targets (M-5 interval objects); (v) declared ε: `tolerance_arcsec` + `bracket_seconds` per row; `near_station_unresolved` flagged where the spline cannot certify a root count. Moon: same kernel, on demand (R7), not persisted by default.

**Feasibility evidence (Appendix C, real Swiss files, `retflag 258`):** stored knots reproduce Swiss to 0.002″; every kernel contact matched a direct Swiss root-solve (Mars→Venus 2012-12-04/2014-11-13 within 0.85″/0.54″; Saturn 2019-01-17 within 0.90″; Saturn's 270° dṛṣṭi triple pass 2010-11-16 / 2011-04-12 R / 2011-08-11 all ≤0.96″; Moon 2027-03-03/03-30 within ~1.5 s); negative control (Saturn/Jupiter 2011–15) 0/0 spurious. Closed-form evaluation once events are known: 0.013 ms/instant vs 64 ms/evaluation today `[X]`.

### 4.3 The Contact ledger — `kala_gochara_contacts` (N-7)

One row per episode, per chart, per generation. Natural key `(chart_id, generation, contact_id)`; `contact_id` = SHA-256 over (chart_id, convention_id, body, target_kind, target_fact_id-or-ref, relation, aspect_deg, round(t_exact, 60 s)) — stable under horizon re-partitioning (§10 identity test).

| Group | Fields |
|---|---|
| identity | `chart_id`, `generation`, `contact_id`, `independence_group` (one physical contact reached via several targets/rules — H-6) |
| geometry | `body`, `relation`, `aspect_deg`, `target_type`, `target_ref`, `target_fact_id` (L1 `chart_facts.fact_id` or NULL), `target_resolution_state` (§5.3), `target_longitude_deg` (reference copy; L1 is authority, §N.5) |
| time | `t_in`, `t_exact`, `t_out` (`timestamptz`, UTC), `bracket_seconds`, `tolerance_arcsec`, `truncated_at_horizon ∈ {start,end,NULL}` |
| motion | `branch`, `station_flag`, `exact_crossing`, `orb_max_deg`, `orb_source`, `dwell_days` |
| qualification (F04/F06/F12) | `epistemic_class`, `completeness_state`, `operator_role`, `claim_grain`, `time_basis`, `comparable_with` |
| provenance | `convention_id`, `ephemeris_backend`, `evidence_fact_ids jsonb`, `classical_citation`, `uncited_extension`, `input_generation_vector_id`, `build_id`, `computed_at` |

Size estimate `[I]`: slow bodies produce O(10²) episodes per target per century; with ~450 degree-resolvable targets (§5.3) and 6 non-Moon bodies, ~2–5 × 10⁵ rows per chart at ~400 B → 100–200 MB per chart before Moon; measured at WP4, never assumed. Moon on demand keeps the default ledger bounded.

### 4.4 The Search-coverage manifest — `kala_gochara_coverage`

One row per (chart, generation, partition = body × target_type, or event_class for the projection): `requested_horizon`, `completed_horizon`, `resolution`/ε, `relations_searched`, `targets_requested`, `targets_resolved`, `targets_unresolved` (with `target_resolution_state` counts), `unavailable_inputs jsonb` (e.g. overlay absent beyond ±460 d), `unsearched_reason`. Every no-window and no-contact answer served carries this object (Strategy §3 Search coverage; L3-Q08).

### 4.5 The projection — scoring over the ledger (N-6; efficiency with quality)

λ_v3 keeps its factor algebra; each factor becomes a lookup over interval sets: activity from episodes (M-1 decides in-orb scaling; until then the legacy ±5 d box is reproduced *span-aware*, `E8`), PROMISE/PERMISSION from per-class context fetched **once per chart** (not ×270), tārā/w30/quality_gates from L1 facts and overlays as interval sets, daśā/AV/Sade-Sati as interval sets. Windows are a **refinement projection** of the ledger: era → month → day rows are written from episodes, with `parent_window_id` preserved, both table roles preserved, all admitted peaks stored (H-5) and trimmed only at serve time. **Equivalence contract (Strategy §5 P3):** no missing narrow/station/retrograde events; complete boundary joins; no chart-bound reuse across subjects; same finite-value policy. **No cap, coarser grid or narrower horizon is a speedup.** Target figure deliberately unstated until `KALA_COST_PROFILE_v1_0.md` measures it at WP4.

### 4.6 Identity and honesty across the chain

`contact_id` (ledger) → `window_id` + `parent_window_id` (projection) → publication `manifest_id`. Every window row lists the `contact_id`s it rests on in `active_sentences` (restoring the field `3.0` emptied, now with ids). A `completeness_state` of `unqualified` / `unavailable` / `unexplored` is stored, never a 0.0 or an empty list standing in for it (F06; §N.7 item 6).

### 4.7 Publication and generation model (N-10)

- `ka_gochara` writes to `kala_gochara_windows` under generation **`'4.0'`**, plus the two new relations, all scoped by (chart_id × generation) for §N.3 delete-then-insert.
- A **`kala_gochara_publication`** row per (chart_id, generation): `manifest_id uuid`, `writer_asset_id`, `convention_id`, `input_generation_vector jsonb` (§5.5), `ephemeris_backend jsonb`, `horizon`, `row_counts jsonb` (contacts/coverage/windows), `content_digest`, `published_at`, `superseded_at`, `status ∈ {candidate, published, superseded, rolled_back}`. A generation is **immutable once `published`**: a rebuild produces a new candidate under the same label only while `candidate`; after publication a rebuild is a new label (`'4.1'`, …).
- **Authority** (`kala_gochara_authority`, migration 527) is flipped only at WP10 under 527's four functional gates, writing `evidence_ref = manifest_id`. No schema change to 527's table. Rollback = re-point to `'3.0'` (its rows are never touched) and mark the `'4.0'` manifest `rolled_back`.
- **Why `'4.0'` and not a `g4_*` label:** the serving code routes `g3_*` and `'3.0'` to the century writer's provenance and substep history (`register_gochara_windows.ts:586,966,977`); a `g4_` prefix would not match either branch and a bare `'4.0'` falls through to the **v1** branch — both wrong. P-1 (§6.2) adds the explicit `'4.0'` branch; the label choice makes that branch a one-line, unambiguous addition.

### 4.8 Typed qualification, time and knowledge-time

No confidence/salience scalar. F04 epistemic class, F06 six completeness states, F12 operator role, Temporal testimony incl. silence and `independence_group`, `comparable_with`. Event time (contact instant), knowledge time (input generation vector), publication time (manifest) pinned separately. No `date.today()`; instants UTC; `DATE` projections stay `DATE`. No live L4/L5 read; rectification only as an admitted immutable artifact.

---

## 5. Upstream contracts — verified at source and live

### 5.1 L0 substrate `[L][S]`

| Input | Relation | Live census | Read by kernel as | Contract / trap |
|---|---|---|---|---|
| Daily ephemeris | `ephemeris_daily` (`bg_ephemeris`) | 825,084 rows, 9 bodies, 1900-01-01 → 2150-12-31; noon-UT knots; `tropical_longitude`; nodes TRUE (stored = Swiss TRUE to 0.000″) | knots → D-1 sidereal conversion → arcs; Rāhu/Ketu **derived mean** analytically (N-4a(b)), declared | epoch = noon UT (F-15); backend recorded from `retflag` (F-14); G-6 routed to L0 |
| Arc index | `bg_gochara_arcs` (`bg_gochara_arcs`) — 33,933 arcs, 9 bodies, columns `substrate_version, body, arc_index, start_jd, end_jd, start/end_lon_unwrapped_deg, lon_lo/hi_deg, direction, wrap_index, arc_fingerprint, engine_version, ayanamsha_id, build_id` | `ayanamsha_id='tropical'` on every row | **not consumed** by the kernel (F-07); kernel builds sidereal arcs itself; the L0 asset is left as is — its disposition is L0's | R9: register, label, do not delete |
| Sky calendar | `bg_sky_calendar` 31,081 rows (frozen L0; TRUE node via `transit_search.py`) | — | not consumed | listed for N-4a blast radius only |
| Transit rules | `bg_transit_rules` 75 rows | mechanism_node targets and Vedha house rules | via resonance and Vedha; unchanged | `integrity_check_sql` (c) already asserts resolvability |
| AV gates | `bg_transit_av_gates` 8 rows | PERMISSION factor (`context.py:355`) | interval set per class | unchanged |
| Malefic scale, latta, grid | `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_sarvatobhadra_grid` | Vedha inputs | unchanged | Vedha's own integrity contract covers them |

### 5.2 L1 inputs (canonical chart, Lahiri) `[L]`

| Input | `chart_facts` category / relation | Census | Used for |
|---|---|---|---|
| Natal positions | `graha_position` (10 subjects incl. `LAGNA`, `RAH_MEAN`, `KET_MEAN`; keys `longitude_sidereal, sign, house_d1, pada, nakshatra, …`) | 10 × up to 8 keys | degree targets (karaka, dasha_lord_portfolio, lord, yoga constituents, positive sensitive checks) |
| Sign attributes | `graha_sign_attributes` (`sign_num`, `degree_in_sign`) | 20 | whole-sign house offset for bhava / lord / mechanism_node (same convention `enrichment.py` uses) |
| Kakṣyā boundaries | `ashtakavarga_kakshya_boundary` | 120 rows, 3 keys | H-1: real BPHS Ch.66 boundaries replace the fixture |
| Aṣṭakavarga | `ashtakavarga_*` | 9,880 rows, 21 keys | PERMISSION / AV threshold (M-4 operand audit for w21) |
| Sade-Sati | `sade_sati_*` | 4,492 rows, 41 keys | quality gate as interval set (no `chart_sade_sati` table exists) |
| Daśās | `chart_dashas` | 483,870 rows | dasha_lord_portfolio targets (`system_id='vimshottari', level_n=1`, `writer.py:409-414`); clocks as interval sets |
| Yoga firings | `ga_yoga_firings` (`fired, constituent_fact_ids, constituent_planets, constituent_houses, is_partial, bhanga_active`) | 11 of 13 targeted ids present | yoga_constituent resolution (§5.3) |
| Point classes with real degrees | `arudha_pada` 19 subj (cusp placeholder, F-20), `bhava_arudha` 14, `special_lagna` 7, `nakshatra_pada_sensitive` 4, `sensitive_point_gulika_mandi` 2, `esoteric_point_pranapada_sphuta` 1 — each with `longitude_sidereal` | — | E-1 enrichment candidates (M-6); **not** targeted by resonance today except arudha |

### 5.3 Target-resolution contract — the part that decides what the kernel can honestly solve

Today `enrichment.py` resolves degrees only for `karaka`/`dasha_lord_portfolio` and a sign for `bhava` (`:41-79`); **609 of 765 targets (79.6 %) reach the engine without a degree** `[L]`. The contract below states, per type, what the kernel receives, from which L1 row, and what state a row gets when it cannot be resolved. Rows are counted on the canonical chart `[L]`.

| target_type | rows | today | resolution rule (deterministic; cite both facts) | object kind | unresolvable → `target_resolution_state` |
|---|---|---|---|---|---|
| `karaka` | 44 | degree | `graha_position[subject=graha].longitude_sidereal`; Rāhu/Ketu → `RAH_MEAN`/`KET_MEAN` (N-4) | point | `unavailable` if the fact is absent |
| `dasha_lord_portfolio` | 44 | degree | same as karaka | point | same |
| `lord` (`1L`…`12L`) | 52 | none | house N sign = whole-sign offset from `LAGNA` `graha_sign_attributes.sign_num`; sign → lord by the fixed classical rulership table (L0 reference row cited); lord → its `graha_position` row | point | `unqualified` (rulership row missing) |
| `bhava` (`1`…`12`) | 68 | sign | whole-sign span from `LAGNA`; **no point is invented** from a cusp (`bhava_cusps` exists — using it is M-5) | **interval** (residence) | n/a |
| `mechanism_node` (`jupiter:double_transit:h11`) | 93 | via w-modules | graha + rule + house → house sign span; relation = sign-ingress / residence | **interval** | `unqualified` if the rule's operand is not wired (M-4) |
| `arudha` (fact_id of the `sign` row) | 68 | none | sibling `arudha_pada[subject].longitude_sidereal` **is a cusp placeholder (F-20)** → treat as the sign span of `fact_value_text`; a degree-level ārūḍha is M-5/M-6 | **interval** | n/a |
| `yoga_constituent` (yoga id) | 220 | none | `ga_yoga_firings[fired=true].constituent_fact_ids` → each constituent `graha_position` row; one `independence_group` per yoga (H-6); `bhanga_active=true` (`neecha_bhanga_raja_yoga`) carried as a qualifier, not a weight | point(s) | **166 rows resolvable (11 ids); 54 rows (`ardhachandra`, `chatra`) `unavailable` today (F-21)** |
| `sensitive_degree` (fact_id into `sensitive_degree_check`) | 176 | none | the check row has **no longitude**; the sensitivity is a property of its subject graha's degree → resolve to that graha's `graha_position` row **only when the check is positive** (`papa_kartari`, `shubha_kartari`, `pushkara`: 22 rows) and merge into the graha's own `independence_group`; **154 rows cite a negative result and must not be targets (F-19)** | point (qualifier) | negative-result rows: removed at G-R (N-12); if retained pending ruling, `inapplicable` |

**Consequence for scope:** after this contract, point-resolvable targets are 44 + 44 + 52 + 166 + 22 = **328 rows**, interval targets 68 + 93 + 68 = **229**, and **208 rows are honest nulls** (154 negative-result + 54 dangling) that today masquerade as targets the engine "evaluated". This is the single largest quality lever in the family after F-01 itself, and it is upstream of the kernel — WP1 pins it, G-R lands it.

**Resonance corrections (G-R packet), pre-approvable as honesty fixes under N-12:** R-1 value-filter `_FETCH_SENSITIVE_FACTS_SQL` to positive results and re-type as a graha-degree qualifier; R-2 arudha typed as sign-level; R-3 yoga targets re-validated against live `ga_yoga_firings` at build and pinned in the input generation vector; R-4 lord resolution as above; R-5 first-root retention and `afflicted` qualifier (F-12); R-6 `target_resolution_state` column on `gochara_resonance_map` (migration ≥1071) so the honest null is stored, not inferred. **Enrichment candidates (E-1, gated on M-6):** special lagnas (7), nakṣatra pādas (4), Gulika/Māndi (2), Prāṇapada (1), bhāva-ārūḍhas (14) — all carry real `longitude_sidereal` today; none may be emitted without a per-class classical basis and a ruling.

### 5.4 Overlays and the proposed-use member

Vedha (177), Moorti (71): `ENRICH_CORRECT` on the kernel — coverage becomes the requested horizon (not ±460 d, F-11); Moorti graded at the true ingress instant (F6 in v1.0) with the day-grade error rate reported; F06 states where an overlay is absent; `independence_group` on Vedha so one obstruction root attenuates once (A08). **Shared-consumer contract (three readers: century, Saṅgam, Kṣetra; agreed with the Kṣetra session 2026-09-23):** every Vedha row carries (i) `source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}` derived from its own `classical_citation` / `grid_basis` / `uncited_extension` — house_vedha rows are verse-cited via `bg_transit_rules` + Phaladīpikā Ch.26 (F-23 strikes only the BPHS half); sarvatobhadra rows are `algorithmic_approximation` exactly when `grid_basis` says so (the registry integrity conjunct (a) already enforces the pairing); latta rows restate `bg_phaladeepika_latta` verbatim (conjunct (g)) and are verse-cited except the disclosed Ketu gap — so a consumer that treats latta as `unqualified` is applying its own admission policy, which the field makes explicit rather than hidden; and (ii) `precision_regime = 'date_grain'` until kernel-based ingress instants land, then `'instant_grain'` — so the DATE-grain seam is stamped on the row, not inferred by each reader; and (iii) `corpus_verifiable` (boolean): whether the cited text is in the admitted corpus `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` — today that directory holds **BPHS, Jaimini Sūtram, KP and KP Reader only** `[R]`, so **no gochara-vedha source is corpus-verifiable**: Phaladīpikā Ch.26 (the surviving citation on every house-vedha rule), Sārāvalī Ch.28 and Jātaka Pārijāta are cited on `bg_transit_rules` rows but not admitted, and BPHS has no gochara chapter (F-23). A consumer policy that admits house-vedha as `applied` while holding latta `unqualified` for non-admission is therefore inconsistent unless it says why; the field makes the policy checkable. Routed as G-9. **Cross-stream consequence (Kṣetra plan v1.4, Saṅgam sheet, this family — aligned 2026-09-23):** a gochara-vedha row is F06 `applied` for any consumer iff `corpus_verifiable=true` AND its geometry passes the Vedha integrity conjuncts; today every such row is therefore `unqualified` in all three consumers, verse-cited or not (computational correctness ≠ source qualification; §N.4's verification triad needs the classical-rule half from an admitted source). This does not block WP1–WP9; it bounds what `quality_gates` may claim until G-9 flips the stamp row by row, and it means the layer's transit-qualification reference in FOUNDATION_SAFETY §5:207-209 (the struck BPHS Ch.29 reading) currently has no corpus-verifiable vedha reference — routed by the Kṣetra session to the strategic session as a W0 record consequence. Kota (585): `PRESERVE`; `w25` exists but is not wired; operand audit (M-4) before any use. Tithi: the century's declared `ka_tithi_pravesha` edge has no reader in `ClassContext.fetch` `[S]` — retired as an edge (N-8), not as an asset.

### 5.5 Input generation vector (F-21's lesson)

Every publication pins: resonance `computed_at` + row count; `ga_yoga_firings` build id; `chart_facts` build ids for the categories in §5.2; `ephemeris_daily` `substrate_version`; overlay build ids; `bg_transit_rules`/`bg_transit_av_gates` counts; the convention id. A rebuild whose vector differs from the published one is a **new candidate**, never an in-place refill (§4.7). The dangling-yoga case (F-21) is exactly the drift this vector makes visible.

---

## 6. Downstream contracts — verified at source, with what each must change

### 6.1 Reader inventory `[S][L]`

| Reader | Where | Reads today | After `'4.0'` publication | Change owed |
|---|---|---|---|---|
| `gochara_forecast_get`, `gochara_activation_get`, `gochara_election_avoidance_get` | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` | `kala_gochara_windows` filtered by `AUTHORITATIVE_GENERATION_FILTER` (`:641-643`, COALESCE default `'v1'`); `ROW_COLUMNS` `:600-612` (incl. `active_sentences`, `term_breakdown`, `generation`, `resolution`, `parent_window_id`) | filter works unchanged; **`buildSourceCitation` (`:573-598`) has branches only for `'3.0'` and `g3_*` — `'4.0'` falls to the v1 branch and returns false provenance** | **P-1a** |
| coverage attestation | same file, `computeGocharaCoverage` `:926-1000` — `isV3Authority = authGen === '3.0' \|\| startsWith('g3_')` `:966`; substep asset `'ka_gochara_v3_century_materialize'` vs `'ka_gochara_sweep'` `:977`; key split `'::'` vs `':year:'` | for `'4.0'` → **false** → reads the RETIRED sweep's substep history → misreports coverage | **P-1b**: route `'4.0'` to `asset_id='ka_gochara'`, key format declared by the writer, and prefer the `kala_gochara_coverage` manifest when present |
| `deriveResolutionDisclosure` `:419`, `GENUINE_PEAK_BASES` `:372` | same | `peak_basis ∈ {gochara_lambda_v3_argmax}` | projection keeps the same `peak_basis` vocabulary (`peak_basis_vocab.py`) so disclosure stays honest; a new basis needs the mirror update | **P-1c** (only if a new basis is introduced) |
| `reading_checklist.ts` `fetchGocharaSweep` `:1011` → `:1063-1092` | `platform/src/lib/retrieval/registry/layers/` | authority-filtered; drops ids/basis; counts a capped page | needs `contact_id`s and `completeness_state` carried through | **P-2** |
| D8 assess-domain, D9 judgment | `register_d8_assess_domain.ts`, `register_d9_judgment.ts` | via `fetchGocharaSweep` | inherit P-2 | — |
| Kṣetra stage 4 | `services/ka_kshetra/stage4_field.py:1373-1389`; `writer.py:952,1063` | authority-filtered read; provenance edge `source_table='kala_gochara_windows', source_pk=id` | on next Kṣetra build reads `'4.0'` rows; existing `kala_field` edges keep pointing at `'3.0'` ids, which persist | **K-1**: declare `→ka_gochara`; pin edges by `(generation, id)` or `contact_id` |
| Saṅgam | `services/ka_sangam/engine.py:464` (service), `:1363,:1383` (bypass), `ka_sangam.py:1037-1060` (Vedha) | service + direct Vedha read | S-1 gives episodes with grain, coverage, ids; Vedha edge declared | **S-1** (this family owes), **V-1** (Saṅgam owes), G-7 |
| L5 ledger | `mi_*` | no `contact_id` anywhere `[S]` | needs `contact_id` for frozen-claim identity (U10) | **P-3** |
| Contact ledger consumers | none yet | — | a read capability over `kala_gochara_contacts` + `kala_gochara_coverage` (density-layered per §N.6, `hardFloor` on confirmed episodes) | **P-4** (new; serving-stream owned) |
| Cockpit stats / Clear | `asset_registry.count_sql`; `clear/execute/route.ts:160-182` | `_v2 '2.0'` | derived DELETE follows `count_sql` → after re-pin, `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'` — generation-keyed, correct; `clear_tables` NULL today: set to the three owned relations so the ledger/coverage are cleared with the windows | §6.3 |

### 6.2 Interface packets (owed; not written here)

- **P-1** (`register_gochara_windows.ts`): (a) explicit `'4.0'` branch in `buildSourceCitation` naming `ka_gochara` + kernel + λ_v3 projection + generation; (b) `computeGocharaCoverage` routes `'4.0'` to `asset_id='ka_gochara'` and reads `kala_gochara_coverage` when present; (c) `peak_basis` vocabulary mirror if extended; (d) remove the `'v1'` COALESCE default — absent authority row → `unpublished` coverage object (N-10). Test: a `'4.0'` authority chart returns provenance naming `ka_gochara` and a coverage object equal to the manifest.
- **P-2** (`reading_checklist.ts`): carry `contact_id`s, `completeness_state`, `peak_basis` through the capped page; count confirmed vs context rows separately (§N.6).
- **P-3** (L5): `contact_id` on the prediction/claim ledger.
- **P-4** (serving): contact-ledger and coverage read capability with `density_contract` declared.
- **S-1** (this family → Saṅgam): `GocharaTransitService.find_aspects` / `find_eclipse_proximity` / long-horizon search return kernel episodes with grain, coverage and `contact_id`; Saṅgam stops bypassing the service.
- **V-1** (Saṅgam): declare `→ka_vedha_gochara` (`counterevidence`) and re-type `→ka_gochara` as service. **K-1** (Kṣetra): declare `→ka_gochara` and — per the Kṣetra packet (2026-09-23) — `→ka_vedha_gochara`, which Kṣetra will consume after one cross-check generation; remove its own `'v1'` fall-through. G-O therefore gains two consumers (Kṣetra, Saṅgam) and its F06 states and `independence_group` become load-bearing for three streams.

### 6.3 Registry re-pin list (migration ≥1071; R10 early, N-9 release condition)

| Row / field | Today `[L]` | After |
|---|---|---|
| `ka_gochara.target_table` | `kala_gochara_windows` (already the production relation — the "mismatch" resolves itself under N-5) | unchanged |
| `ka_gochara.count_sql` | `… kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'` | `… kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'` |
| `ka_gochara.clear_tables` | NULL | `[kala_gochara_windows, kala_gochara_contacts, kala_gochara_coverage]` (each cleared by the same generation-keyed scope) |
| `ka_gochara.integrity_check_sql` conjuncts (a)–(h) | all scoped to `_v2 '2.0'`; (f) asserts `'2.0'` never appears in `kala_gochara_windows`; (h) v1 hard-floor per chart | re-scope (a)–(e),(g) to `'4.0'` + the two new relations; **(f) becomes:** `'4.0'` rows exist only with a `published`/`candidate` manifest, and no `'2.0'` row ever appears in production; **(h) kept verbatim** (v1 floor); add (i) every window's `active_sentences` ids resolve in `kala_gochara_contacts`; (j) `target_table` relation = `count_sql` relation (N-9 iii) |
| `ka_gochara.depends_on` | `[bg_gochara_arcs, ka_gochara_resonance]` | `[bg_ephemeris, ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya, ga_positions, ga_dashas, ga_yoga]` (kernel reads knots, not the tropical arcs) |
| `ka_gochara.target_floor` | 83 | achieved count after WP10, never before (§N.4) |
| `ka_gochara.has_substeps` | true | true; substep key format declared for P-1b |
| digest spec 1018 (`where_equals generation='2.0'`) | pins `_v2 '2.0'` | new spec for `'4.0'` on the three relations; 1018 retained for the `'2.0'` residue until N-11 |
| `ka_gochara_sweep` | `is_active=false`, `count_sql … 'v1'` | unchanged; Phase 1.1 makes `is_active=false` rows unreachable by Clear |
| century row | `count_sql g3_%`, `target_table _v2`, depends_on incl. `ka_kota_chakra`, `ka_tithi_pravesha` | unchanged (hold); Tithi edge retirement (N-8) recorded, not applied |
| `ka_sangam.depends_on` | lacks `ka_vedha_gochara` | V-1 (Saṅgam's migration) |
| `ka_kshetra.depends_on` | lacks `ka_gochara` | K-1 (Kṣetra's migration) |

### 6.4 Cockpit Clear — what changes and what does not

Phase 1.1 lands the `is_active` filter and the (table, generation) guard for `'v1'` and `'3.0'`. This family's own Clear becomes correct by construction once `count_sql` is re-pinned: the derived statement is generation-keyed. `EXPLICIT_CLEAR_OPS` has no `ka_gochara` entry today (`assetClearSpec.ts:52`) and needs none unless a JOIN enters `count_sql` — it must not.

---

## 7. Work packets (revised; authority A = local/synthetic, N = native ruling, P = production authority)

| WP | Work | Auth | Exit gate |
|---|---|---|---|
| **0** | Register through the authorized owner: F-01..F-22 (this table), G-6/G-7 routed; adopt live aggregates, re-validate at implementation | A | registered; no claim about the historical ≥2-era case |
| **1** | **Contracts.** Convention vector (§4.1) · **target-resolution contract (§5.3) with per-type golden cases** · ledger/coverage/publication schemas (§4.3–4.4, 4.7) · `contact_id` derivation · input generation vector (§5.5) · registry re-pin design (§6.3) · reference oracle, tolerances, file fences, immutable test vector · point-vs-span semantics (M-5 interim) | A | independently reviewed; convention pinned; every target type has a stated resolution or state |
| **2** | **Synthetic fixture suite, non-person first.** close-station cubic · true-node excursion · seam tangency · start/end-inside episodes · noon/midnight conversion · per-graha dṛṣṭi angles · negative-result sensitive check (must produce no target) · cusp-placeholder arudha (must produce no point contact) · dangling yoga id (must produce `unavailable`) · missing overlay · solver exception · plateau ties; hand-specified factorized scorer oracle | A | every case has an expected answer derived without legacy output |
| **3a** | **Kernel** (§4.2) | A | WP2 geometry fixtures pass; candidate set independently enumerated; kernel-vs-Swiss within declared ε **on SWIEPH with checksums recorded (F-14 gate)**; E1 retained as the legacy defect reproducer |
| **3b** | **Span-aware legacy algebra** (parallel with 3a) | A | factor-by-factor equivalence on the WP2 matrix; artefacts classified |
| **3c** *(new)* | **Resonance corrections R-1..R-6 (G-R)** | A (N-12) | F-19/F-20/F-21 fixtures pass; 27-class gate still passes; `target_resolution_state` populated; 508 uncited rows still carried as `unqualified` |
| **4** | **Decomposed comparison** oracle → legacy semantics → kernel → projection on one pre-declared workload; bounded cold/warm timings, prepare/search/query separated | A | every delta classified; ids stable under horizon re-partitioning; labelled *producer prototype evidence* |
| **5** | **Honesty fixes H-1..H-6** (§8.1) | A | served-path behaviour matches its documentation; golden values per fix |
| **6** | **Ledger + coverage + publication** (§4.3, 4.4, 4.7); crash, resume, horizon extension, upstream correction, concurrent read, rollback tests | A design / N schema | all six tests pass on a disposable DB; storage measured |
| **7** | **Receiving contracts P-1..P-4, S-1, K-1/V-1 + minimum L2 slice (R8)** | A / owners | a sentinel `independence_group` on a low-ranked row survives retrieval, budget, delivery and replay; a Product §12.2 question answered with preserved identities and three-way negatives |
| **8** | **Method rulings M-1..M-6** — one PR each with comparison evidence | **N** | native ruling each; non-vacuous ablation on a non-empty corpus |
| **9** | **Overlays on the kernel** (G-O); Kota after M-4 | A / N | coverage = requested horizon; Moorti ingress error rate reported |
| **10** | **Full benchmark, then cutover** (§9): Strategy §5 in full → Phase 1.1/1.2 → drill → guard → registry re-pin → candidate `'4.0'` build on the canonical chart → four functional flip gates → authority flip with manifest → soak → second chart (`1c826d5a`) → N-11 disposition | **P** | fresh native authorization; rollback proven through the real serving adapters |

**First slice:** WP1 → WP2 → (WP3a ‖ WP3b ‖ WP3c) → WP4. **Critical path:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 10; 8 and 9 join after 5. No production data and no real chart before its own gate. **Stop conditions** (a timing gain overrides none): unresolved convention · unknown-as-empty · missed topology without declared fallback · unclassified divergence · id drift across partitions · vacuous comparison (Moshier-vs-Moshier, zero permission, absent operands) · a target resolved to a degree its cited fact does not carry.

---

## 8. The scoring split (D-3) — carried

### 8.1 Pre-approved honesty fixes (WP5)
**H-1** real BPHS Ch.66 kakṣyā boundaries from L1 (`ashtakavarga_kakshya_boundary`, 120 rows), pinned; absent → not evaluated · **H-2** an exception never becomes 0.0 · **H-3** no era window over a zero-score range; requested vs completed horizon reported exactly · **H-4** real eclipse instants from L0 replace window-edge timestamps (timing only) · **H-5** remove the 3-peaks-per-decade cap; trim at serve time under §N.6 · **H-6** one physical contribution counted once (`independence_group`).

### 8.2 Deferred method calls (WP8)
M-1 … M-4 as in v1.0 §9.2, plus M-5 (sign-level target anchoring) and M-6 (new target-class admission) from §1.4.

---

## 9. Migration, cutover, rollback — the ordered runbook

| Step | Action | Gate / evidence | Reversal |
|---|---|---|---|
| 0 | **Phase 1.1** — Clear route excludes `is_active=false` assets and protected generations; stale migration-540 comment removed (`clear/route.ts:95-96`) | route test: sweep row unreachable by any principal | revert PR |
| 1 | **Phase 1.2** — SELECT on both `v1` archives for `data_plane_builder` | privilege listed | REVOKE |
| 2 | **Restore drill** — 2026-08-23 dump into a disposable DB; all 38,287 `v1` rows content-checked, not `pg_restore -l` | row-by-row digest equality; archive gap (2,667 uncovered ids) recorded | none needed |
| 3 | **Guard** — trigger keyed on (table, generation) for `'v1'` and `'3.0'` on `kala_gochara_windows`; never `asset_id`-keyed; `build_protected_assets` re-seeded | attempted DELETE/UPDATE/TRUNCATE tests fail loudly; `'4.0'` writes pass | DROP trigger (recorded) |
| 4 | **Schema** — migrations ≥1075: `kala_gochara_contacts`, `kala_gochara_coverage`, `kala_gochara_publication`, `gochara_resonance_map.target_resolution_state`; both migration directories checked; applied-state verified, never assumed (§N.4) | `information_schema` diff | down-migrations included |
| 5 | **Registry re-pin** (§6.3) by migration, with the N-9 integrity conjunct | `count_sql` relation = `target_table`; cockpit stats read the new count | reverse migration |
| 6 | **Candidate build** — `ka_gochara` on the canonical chart writes `'4.0'` as `candidate`; `'3.0'` untouched; authority still `'3.0'` | integrity contract green; row counts in manifest; storage measured | delete candidate under own scope |
| 7 | **Four functional flip gates** (527): provenance (P-1a) · coverage (P-1b) · disclosure (`deriveResolutionDisclosure`) · rollback-through-adapters rehearsal | each a test against the deployed tools | — |
| 8 | **Flip** — `authoritative_generation='4.0'`, `evidence_ref=manifest_id`, manifest `published` | walkthroughs §3 F-02 re-run: ordinary quarter and marriage 2013 now show episodes with contacts and coverage | re-point to `'3.0'`; manifest `rolled_back` |
| 9 | **Soak**, then second chart `1c826d5a` (its own birth epoch — the century's #2534 defect must not recur: birth from `ctx.config['birth_params']`) | integrity green on both charts | as step 8 |
| 10 | **N-11** disposition of `_v2 '2.0'`; digest 1018 retired or re-pointed | native ruling recorded | — |

**Kṣetra note (F-18):** existing `kala_field` provenance edges point at `'3.0'` row ids, which persist; Kṣetra's next build reads `'4.0'`. K-1 pins edges by `(generation, id)` so a later `'3.0'` disposition cannot orphan them.

---

## 10. Proof matrix (synthetic non-person cases; disposable DB; no live chart before its gate)

| Proof | Test · expected · detector |
|---|---|
| Positive | station-pair cubic → 3 roots; seam tangency → ≥1 episode; start-inside → truncated episode (today 1 / 0 / `[]`, `E8`) |
| Negative | no L1 kakṣyā row → `unqualified`, 0 fixture sentences; overlay gap → `unavailable`; negative-result sensitive check → no target; dangling yoga id → `unavailable`; cusp-placeholder arudha → no point contact |
| Relevant influence | move one natal target 1° → only its episodes shift |
| Irrelevant control | shuffle resonance/target order → identical rows and `contact_id`s (1018's own #2527 class) |
| Duplication | one physical contact via 3 targets → one `independence_group`; activity unchanged |
| Context / missingness | wrong chart/ayanāṃśa/generation/convention → reject; six F06 states distinct, never 0 |
| Boundary / precision | partition seam → same `contact_id`; kernel vs Swiss under identical flags within ε — **runs only where `retflag & 2`; records backend + three checksums; on `retflag & 4` the run is `NOT_RUN`, not PASS** |
| Ecosystem | `'4.0'` authority → P-1a provenance names `ka_gochara`; P-1b coverage equals manifest; cockpit count equals `count_sql`; derived Clear statement is generation-keyed; guard rejects `'v1'`/`'3.0'` DML; Kṣetra read returns `'4.0'` rows; Saṅgam S-1 returns episodes with ids |
| Delivery | sentinel in `independence_group` of a low-ranked row survives P-1/P-2 to the saved result (NOT_RUN until Pūrṇa lands) |
| Revision | change a kakṣyā boundary → new candidate, old preserved, head re-point back; same inputs on two dates → byte-equal (kills F-06) |
| Value | `KALA_BASELINE_v1_0.md` Q08/Q02 questions vs today's envelopes; ordinary-quarter and marriage-2013 walkthroughs re-run — `EXPLANATORY_DISCRIMINATIVE_VALUE` |
| Evaluation | `not_applicable` — no empirical claim; L5 not opened |

---

## 11. Risk register

| Risk | Likelihood / impact | Mitigation |
|---|---|---|
| Ledger size exceeds budget with Moon | medium / medium | Moon on demand (R7); measure at WP4; partition by generation |
| A hidden reader of `'3.0'` row ids breaks at flip | low / high | F-18 found one (Kṣetra); `'3.0'` rows never deleted; K-1 pins by generation |
| Serving falls to v1 provenance for `'4.0'` | certain without P-1 / high | P-1a is a flip gate |
| Coverage attestation reads retired sweep substeps | certain without P-1b / high | P-1b is a flip gate |
| Moshier-vs-Moshier gate passes vacuously | high on an unprovisioned host / high | F-14 gate condition; checksums recorded |
| Node ruling changes a reading (pāda 3 vs 4) | certain / medium | N-4 ruled once, declared in convention vector; blast radius measured |
| Resonance corrections shrink the target set and someone reads it as "lost coverage" | medium / medium | R-6 stores the honest null; coverage manifest reports `targets_unresolved` |
| Clear path deletes `v1` before Phase 1.1 lands | low per day / catastrophic | N-1 orders it first; the guard follows |
| Method calls stall the kernel | medium / low | kernel and ledger are method-neutral; M-1..M-6 change only the projection |
| Second-chart epoch bug recurs | medium / high | birth from `ctx.config`; integrity (a)-class conjunct on the new relations |

---

## 12. Authority, and what this plan does not do

Proposes the §4–§9 delta only. Infers no authority from code, migrations, tests, holds or templates. Executable only after the native's rulings on §1.3 and a bounded execution goal; WP10 needs fresh production authorization and the hold release. Never weakens a guard; retires nothing; touches no `kala_views/`, no `register_gochara_windows.ts`, no `transit_search.py`, no seed file, no `v1` or `'3.0'` row. Implementation and review owners are the native's to assign.

## 13. Honest residue

Unmeasured items in §1.6. Not established: whether the W2G V3 "0.314″" figure was measured on Swiss or Moshier (source question) · whether `/private/tmp/se1` is durable (any gate provisions its own copy) · full-century λ distribution · the exact ledger size · whether the 2 dangling yoga ids ever fired under Lahiri or were dropped by a later L1 rebuild (either way F-21 stands). Not claimed: doctrinal validity of any target, causation, or that `v1`'s sentences were *correct* — only that they existed and `3.0` dropped them. **Artifact locations:** `KALA_COST_PROFILE_v1_0.md` (status PARTIAL_INCOMPLETE per its own header) and `KALA_BASELINE_v1_0.md` are cited by name; today they exist only in the `setup` worktree (`/Users/Dev/madhav-l3/setup/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/`) and are on neither `main` nor `l3/kala-elevation-readiness` `[R]` — WP4 and the §10 value row depend on them landing.

---

## Appendix A — live measurement index (2026-09-22/23, `amjis_app`, read-only)

Rows 1–20 as brief v1.2 App. B (registry, guards, censuses, overlays, tools). New:

| # | Question | Result |
|---|---|---|
| 21 | L0 census | `ephemeris_daily` 825,084 / 9 bodies / 1900-01-01→2150-12-31; `bg_gochara_arcs` 33,933 (all `ayanamsha_id='tropical'`); `bg_sky_calendar` 31,081; `bg_transit_rules` 75; `bg_transit_av_gates` 8 |
| 22 | L1 census (canonical, Lahiri) | kakṣyā boundaries 120; AV facts 9,880; Sade-Sati 4,492 (41 keys); `chart_dashas` 483,870; `graha_position` 10 subjects; `arudha_pada` 19; `bhava_arudha` 14; `special_lagna` 7; `nakshatra_pada_sensitive` 4; Gulika/Māndi 2; Prāṇapada 1; `yoga_label` 7 |
| 23 | Resonance targets by type | yoga_constituent 220 (13 ids, all uncited) · sensitive_degree 176 (36 fact ids, uncited) · mechanism_node 93 (46 refs) · arudha 68 (12) · bhava 68 (12) · lord 52 (12) · karaka 44 (9) · dasha_lord_portfolio 44 (9) |
| 24 | sensitive_degree referents | `not_gandanta` 44 rows / `kartari none` 26 / `mrityu_bhaga not_fired` 44 / `not_pushkara` 40 → **154 negative**; `papa_kartari` 7, `shubha_kartari` 11, `pushkara` 4 → 22 positive |
| 25 | arudha referents | 12 `sign` facts; sibling `longitude_sidereal` = 0/30/60/90/120/150/270/300 exactly (sign cusps) |
| 26 | yoga referents vs `ga_yoga_firings` | 11 ids fired under Lahiri, 1–7 constituent facts each; `ardhachandra`, `chatra` (27 rows each) — no row under any ayanāṃśa |
| 27 | Registry rows (family) | `ka_gochara`: `target_table=kala_gochara_windows`, `count_sql=_v2 '2.0'`, `clear_tables=NULL`, `depends_on=[bg_gochara_arcs, ka_gochara_resonance]`, floor 83; century floor 914; sweep `RETAINED_AS_CAPITAL`, floor 16,297; `ka_sangam.depends_on` lacks Vedha; `ka_kshetra.depends_on` lacks `ka_gochara` |
| 28 | `kala_gochara_authority` columns | `chart_id, authoritative_generation, flipped_at, flipped_by, evidence_ref` (N-10 uses `evidence_ref`) |
| 29 | Windows column diff | production has one extra column, `continuity_state`; `_v2` 33 columns |

## Appendix B — file/line index (pinned revision)

`ka_gochara.py` `:120` TABLE, `:268` today(), `:336` DELETE, `:362` generation, `:438-458` build-state upsert · century `:354/:360/:482/:487` · resonance `writer.py` `:293-314` builders, `:380-414` fetch SQL, `:518-549` gate · `enrichment.py` `:41-79` coverage docstring · `gochara_v3/engine.py` `:821` activity, `:1063-1137` sentences · `primitives.py` `:189-196` dṛṣṭi table, `:664-719` fixture · `w2g/db_source.py` `:35,:80,:178` tropical · `context.py` `:289,:355,:405,:449,:510,:553` · `stage4_field.py` `:1373-1389`; Kṣetra `writer.py` `:952,:1063` · `ka_sangam/engine.py` `:464,:1363,:1383`; `ka_sangam.py` `:1037-1060` · `register_gochara_windows.ts` `:372,:419,:573-598,:600-612,:641-643,:926-1000 (:963-977)` · `reading_checklist.ts` `:1011,:1063-1092` · `clear/route.ts` `:93,:95-96,:114-117`; `execute/route.ts` `:160-182`; `assetClearSpec.ts` `:29-46,:52` · `l0_ephemeris.py` `:290` · `transit_search.py` `:10,:64,:187-200,:320` · `pyjhora_adapter/positions.py` `:21-22`, `_jhora.py` `:23-55` · `bg_cohort.py` `:159,:333,:470` · migrations 460, 527, 540, 542, 556, 563, 564, 566, 568, 588, 670, 1018; new ≥1071 · `Dockerfile:24`, `Dockerfile.pipeline:17,22`.

## Appendix C — kernel spike record (2026-09-23, scratch; not committed)

Setup: pyswisseph 2.10.03; `swe.set_ephe_path('/private/tmp/se1')`; `retflag 258` asserted per call; knots at `swe.julday(y,m,d,12.0)`; `sid = (calc_ut tropical − get_ayanamsa_ut) % 360` for the knot conversion (the D-1 production path uses `FLG_SIDEREAL`; the two differ by nutation, ≤16.5″, and the spike's residuals are quoted against the same convention it used); `build_arcs` + `find_contacts` from `services/w2g` re-homed; oracle = direct Swiss bisection at the instant.

| Case | Kernel | Oracle Δ |
|---|---|---|
| stored knots vs Swiss (12 rows) | — | 0.002″ |
| Mars → natal Venus | 2012-12-04, 2014-11-13 | −26.6 s / 0.85″; −17.3 s / 0.54″ |
| Saturn → target | 2019-01-17 | −185.6 s / 0.90″ |
| Saturn 270° dṛṣṭi (triple, incl. retrograde) | 2010-11-16, 2011-04-12 R, 2011-08-11 | all ≤0.96″ |
| Moon → target | 2027-03-03, 2027-03-30 | ~1.5 s |
| Negative control Saturn/Jupiter 2011–15 | 0 contacts | 0 spurious |

All passes matched, none spurious, retrograde and directed cases exercised. This is *producer prototype evidence* (WP3a precursor), not a build result.
