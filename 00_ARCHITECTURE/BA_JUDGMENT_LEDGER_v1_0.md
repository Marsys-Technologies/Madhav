---
artifact: BA_JUDGMENT_LEDGER_v1_0.md
canonical_id: BA_JUDGMENT_LEDGER
version: 1.0
status: LIVE — every ruling by the Ācārya-Pratinidhi logged here; native reviews retrospectively
created: 2026-07-03
governing_charter: 00_ARCHITECTURE/BA_AUTONOMOUS_RUN_CHARTER_v1_0.md §1 (Ācārya-Pratinidhi)
constitution_sources:
  1: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md (W1 seed package — highest authority)
  2: RETRIEVAL_MODERNIZATION_MASTER_PLAN_v1_0.md §3 (Ranking Doctrine + §2.1/§2.2 commitments)
  3: Classical sources in the L0 corpus (cited when ruling)
  4: Mainstream position with 'contested' flag when traditions disagree (L5 adjudicates later)
veto_path: >
  Native reviews retrospectively. Any veto → targeted correction wave, never a blocked run.
  Veto surface: BA_RUN_REPORT_v1_0.md (retrospective review) + this ledger.
---

# BEYOND-ACHARYA JUDGMENT LEDGER

> EVERY ruling by the Ācārya-Pratinidhi agent is recorded here.
> Fields: decision · basis (constitution priority #N) · alternatives_considered · reversibility · consumer

---

## FORMAT

```
### JL-NNN — [Category]: [Short title]
- **Phase:** P[N]
- **Ruling agent:** Ācārya-Pratinidhi
- **Question:** [What judgment was needed]
- **Decision:** [The ruling]
- **Basis:** [Constitution §N — source cited]
- **Alternatives considered:** [What was weighed and why rejected]
- **Reversibility:** [How the native can veto/correct]
- **Consumer:** [Which brief AC / ring gate / downstream asset this feeds]
- **Date:** 2026-07-03
```

---

## RULINGS

*(none yet — ledger initialized; rulings appended as phases execute)*

### Pending judgment queue (pre-P2T)

The following rulings will be needed during P2 prior-tuning (P2T) and must be logged before those
values are frozen:

- **JL-001:** P2T prior convergence — which career prior vector passes the G10-QT rubric
- **JL-002:** P3A L0 seed values — which constants from the W1 seed package get seeded verbatim vs 
  require context-specific annotation
- **JL-003:** P3B formula disposition — any formula component requiring classical adjudication
- **JL-004:** P4 golden answers — Ācārya-Pratinidhi authors Q1–Q9 golden answers for eval corpus
- **JL-005:** P7A E4 ranking — classical completions ranked by leverage × classical weight

### W1-seed §0.2 items — ratified 2026-07-04 (ENDGAME PLAN A1; all four resolved before P3B code freeze)

---

### JL-006 — Formula: bala_gate ratification
- **Phase:** P3B
- **Ruling agent:** Ācārya-Pratinidhi
- **Question:** What is the correct bala_gate implementation for yoga-class signals, and what served state should present-but-enfeebled signals carry?
- **Decision:** `clamp(norm_constituent_shadbala, 0.30, 1.00)` multiplier on yoga-class signals only; served state `present_but_enfeebled` when <0.60. This is a state, never an exclusion — the signal remains in the corpus.
- **Basis:** W1 seed §0.2.2 + §7 A-B (bala-proportionality principle); BPHS bala ratios for yoga strength.
- **Alternatives considered:** Hard exclusion (<0.30 → drop signal) — rejected: loses real but weak yogas. Floor of 0 (no clamp) — rejected: allows near-zero multipliers that collapse mid-tier signals.
- **Reversibility:** formula_version bump + L2 regeneration.
- **Consumer:** P3B `bo_laksana` v2.0 `_compute_salience`; CLAUDECODE_BRIEF_BA_P3B v1.2 Step 1.
- **Date:** 2026-07-04
- **Status:** RATIFIED

---

### JL-007 — Formula: verification_certainty disposition
- **Phase:** P3B
- **Ruling agent:** Ācārya-Pratinidhi
- **Question:** Should `verification_certainty` be rescaled as a salience multiplier (v1 plan) or dropped from the stored formula entirely?
- **Decision:** DELETE the `log(1+corroboration)/log(10)` computation entirely. No rescale replacement. Serve `verification_pass_status` as a separate epistemic dimension in the retrieval envelope (confidence + dissent selection at P4). priors_version=1.0 unchanged (P2 composite had no verification term, so no re-freeze needed).
- **Basis:** Dimension purity — verification certainty is an epistemic qualifier, not a signal-strength multiplier. Inert under percentile-in-class compression. Preserves P2 fidelity (no hidden formula divergence).
- **Alternatives considered:** Rescale to {1.00/0.85/0.60} map — rejected: still conflates epistemic quality with signal salience; P4 verdict object is the right home. Keep log formula with adjusted ceiling — rejected: 0.778 ceiling is the documented top-band strangler (C5 in audit).
- **Reversibility:** formula_version bump + L2 regeneration.
- **Consumer:** P3B `bo_laksana` v2.0; `verification_rescale` column deleted from formula spec; P4 verdict confidence path (JL-007 downstream).
- **Date:** 2026-07-04
- **Status:** RATIFIED

---

### JL-008 — Schema: domain taxonomy
- **Phase:** P3A/B
- **Ruling agent:** Ācārya-Pratinidhi
- **Question:** Is the 12-domain taxonomy in migration 386 sufficient, and does it require changes to the stored L2 salience formula?
- **Decision:** RATIFIED-AS-DRAFTED. The 12-domain taxonomy is sufficient. Domain is query-time only — it does NOT touch the stored L2 salience formula. Already live via migration 386. Not a P3B blocker.
- **Basis:** W1 seed §0.2.1; domain is a retrieval-time filter/facet, not a salience weight input.
- **Alternatives considered:** Finer-grained 18-domain split — deferred to post-P6 based on empirical signal distribution. Domain as salience weight — rejected: query-time facets must not pollute stored signal strength.
- **Reversibility:** Migration + retrieval update (non-breaking; domain column already exists).
- **Consumer:** Retrieval envelope domain parameter; cockpit domain filter; P4 verdict domain attribution.
- **Date:** 2026-07-04
- **Status:** RATIFIED-AS-DRAFTED

---

### JL-009 — Data: event base-rate priors
- **Phase:** P3A → P5B carry-forward
- **Ruling agent:** Ācārya-Pratinidhi
- **Question:** Are the event base-rate priors in `brahma_event_ontology` production-grade, and when do they become a stored formula input requiring native ratification?
- **Decision:** RATIFIED-AS-DRAFTED PLACEHOLDERS. They do NOT touch the L2 stored formula (P3A/B). They first become a stored formula input at P5B (L4 posterior's `base_rate` factor). Carry-forward obligation: surface the age-banded base-rate table to the native for a glance BEFORE P5B freezes anchors (native item-4 protocol). Native confirms/edits → this entry closes. Reversible via ontology upsert + prior_version; L5 re-weights from outcomes.
- **Basis:** W1 seed §0.2.4 (weakest-grounded seeds by design — empirical calibration is L5's job, but the human checkpoint belongs at the layer where they first bite).
- **Alternatives considered:** Freeze silently at current placeholder values — rejected: first stored use without a native glance violates the item-4 human-checkpoint protocol. Ratify at P3A — rejected: they are not a stored input until P5B, so the glance belongs there.
- **Reversibility:** Ontology upsert + prior_version bump; no formula_version change needed.
- **Consumer:** P5B `ph_nimitta` posterior = base_rate × lifts; CLAUDECODE_BRIEF_BA_P5B_PHALA_V2 v1.1 Step 1 gate + exit-gate line.
- **Date:** 2026-07-04
- **Native glance + close (2026-07-07, BA_PHASE4_RUNWAY_PLAN R1.1 — Ācārya-Pratinidhi, native-delegated):** age-banded base-rate table (22 classes × 5 bands) surfaced from `brahma_event_ontology` v1.0. Ruling, four points:
  1. **EDIT — bereavement** age-band weights `0.05/0.15/0.30/0.30/0.30` → **`0.10/0.15/0.30/0.35/0.40`** (rising with elder-cohort mortality). Applied via ontology upsert; `version` 1.0 → **1.1** ontology-wide (migration 421). All other 21 rows ratified as-drafted.
  2. **STRUCTURAL DIRECTIVE — normalization at lookup.** Rows are *relative* weights with inconsistent per-row sums (observed range 0.81–1.30); therefore `ph_nimitta`'s `base_rate` consumption **MUST row-normalize the age-band vector to sum 1.0 at lookup** — this is code, not convention. Obligation: record as a `brahma_formula_constants` note (class=engineering) + a unit test asserting the normalized lookup. **Carried into R2 code churn** (L4 `ph_nimitta`); MUST be live before R4 native L4 anchors consume base_rate (R4 gate: native anchors' base_rate factors trace to R1.1-confirmed values).
  3. **KEEP — nonzero 60+ tails** on `career_entry` (0.01) and `exam_outcome` (0.01): rare-not-impossible doctrine; not zeroed.
  4. **CONFIRM — `separation` 26–40 peak (0.40)** as a conscious ruling on demographic-context basis (not spread later); ledger-noted.
- **Point-2 discharge (2026-07-07, R2.3):** the structural directive is now implemented — `ph_nimitta` consumes `base_rate` as the **row-normalized** age-band prior (services/ph_nimitta/base_rate.py: normalize base_rate_by_age to sum 1.0, select the band containing the anchor's peak_date/window_start vs the native's birth date; age-unknown → 0.20 uniform), replacing the old flat 0.10 placeholder. Recorded as `brahma_formula_constants.ph_nimitta_base_rate_age_normalization` (class=engineering, migration 422); unit test `test_ph_nimitta_base_rate.py` asserts the normalized lookup. Seed `l0_ghatana.py` synced to v1.1 (prevents a re-seed reverting the bereavement edit). R4 gate (native anchors' base_rate trace to R1.1 values) is now satisfiable.
- **Status:** **CLOSED (2026-07-07)** — native glance done, four points recorded, ontology → v1.1; **point-2 implemented in R2.3** (see above). Reversible via ontology upsert + version bump; L5 re-weights from outcomes. `[verify-against: ledger + repo]`

---

### JL-010 — Absorption: karakamsa relationship modeling DEFERRED (ga_structural)
- **Phase:** P3A-absorption-fix (commit 6cddc910)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** How should the new special points (arudha_pada, bhava_arudha, karakamsa_position, swamsa_position) enter ga_structural's house-based special-point relationship builder?
- **Decision:** arudha_pada + bhava_arudha + swamsa_position ADDED (they resolve to a house); karakamsa_position DEFERRED — it is the D9 sign of the Atmakaraka with no D1 house, and is astrologically read by sign (kendras/trikonas from Karakamsa, rasi drishti), not by D1-house aspects. Forcing a house would produce plausible-but-wrong relationships (the silent-error class this program hunts). Follow-up task opened: "Karakamsa/Swamsa Jaimini sign-based relationship pass."
- **Basis:** Constitution §3 (classical: Jaimini Karakamsa is a rasi-framework reading) + the no-silent-fabrication rule.
- **Alternatives considered:** fabricate a D1 house for Karakamsa (rejected — wrong model); drop all four (rejected — three are house-valid and high-value).
- **Reversibility:** the sign-based pass supersedes this deferral when built; no data lost.
- **Consumer:** ga_structural special-point relationships → bo_laksana → L2+.
- **Date:** 2026-07-04
- **Status:** RATIFIED (OPEN — closes when Karakamsa/Swamsa Jaimini sign-based pass is built)

---

### JL-011 — Schema/Extraction: `bg_rules.yoga_canonical_id` deterministic extraction rule
- **Phase:** BA Phase 2.5 (P1 BLOCKER #1 `bg_rules`)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** How should `yoga_canonical_id` be extracted from rule text without fuzzy matching or an LLM (B.10)?
- **Decision:** RATIFIED. (1) Bigram rule for ALL entries — match the adjacent bigram `"<Name> [Yy]oga"`. (2) Bare-name matching restricted to the Tier-1 proper-noun allowlist (29 named yogas: Gajakesari, Neechabhanga, Vipareeta Raja, Ruchaka, Bhadra, Hamsa, Malavya, Sasa, Sunapha, Anapha, Durudhara, Kemadruma, Vesi, Vasi, Ubhayachari, Budha-Aditya, Chandra-Mangala, Kala Sarpa, Guru-Chandala, Saraswati, Amala, Parijata, Adhi, Shankha, Bheri, Mridanga, Parvata, Kahala, Vasumati, Chamara). (3) Hard exclusion list, bigram-only never bare: raja, dhana, arishta, daridra, mala, sarpa, yava, danda, nauka, chatra, gada, hala — these are common-noun components that would over-match if allowed bare. (4) The matched surface form is stored per link; any collision (two distinct canonical ids matching the same span) resolves to NULL + a flag row, never a guess.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J1; B.10 no-fabricated-computation (deterministic pattern match only, no fuzzy/LLM disambiguation).
- **Alternatives considered:** Fuzzy/embedding match against a yoga name table — rejected, non-deterministic and unauditable; bare-name matching for all 29+ names project-wide — rejected, over-matches on common Sanskrit/English nouns (raja, dhana, etc.) producing false positives; collision → best-guess pick — rejected, violates precision-over-recall mandate.
- **Reversibility:** Pure extraction-rule code change; re-derivable any time from rule text, no destructive write.
- **Consumer:** `bg_rules.yoga_canonical_id` → downstream yoga-family linkage (`ga_yoga`, `bo_laksana`).
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-012 — Formula: `ga_yoga.strength` hybrid constituent-bala derivation
- **Phase:** BA Phase 2.5 (P3 J3)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** No yoga-specific strength formula exists in the classical corpus — how should `strength` be populated without fabricating one (B.10)?
- **Decision:** RATIFIED. `strength` = normalized shadbala of the yoga's constituent grahas, stored with `derivation='constituent_bala_v1'` and label `computed_extension` (explicitly marked as an extension, not a classical citation), with a bala_gate citation to the shadbala source. `bhanga_active` is set NULL-with-reason wherever no classical bhanga (cancellation rule) exists for that yoga type — Kemadruma's bhanga logic already lives in the main detection path and is NOT duplicated here.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J3; B.10 (no invented per-yoga formula); JL-006/JL-007 precedent for `computed_extension`-labeled formula components.
- **Alternatives considered:** Invent a yoga-specific weighting formula — rejected, no classical source (B.10 hard rule); leave `strength` NULL for all yogas — rejected, loses genuinely available shadbala signal; duplicate Kemadruma bhanga logic in `ga_yoga` — rejected, would create two divergent sources of truth for the same rule.
- **Reversibility:** `derivation` versioned (`constituent_bala_v1` → v2 if a classical formula is later sourced); no destructive write, per-chart delete-then-insert on rebuild.
- **Consumer:** `ga_yoga.strength`/`bhanga_active` → `bo_laksana` → L2+ yoga synthesis.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-013 — Formula: `bo_cgm_paths.path_strength` = product of constituent edges
- **Phase:** BA Phase 2.5 (P3 J4)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `path_strength` was a flat 0.5 placeholder for every path — what is the correct aggregation of constituent edges' `computed_strength`?
- **Decision:** RATIFIED WITH CORRECTION. `path_strength` = PRODUCT of constituent edges' `computed_strength` (a chain is only as strong as its weakest-compounding link; min() is an acceptable conservative alternative where product underflows). Averaging is explicitly rejected — an average lets one broken edge hide behind strong ones, which is exactly the plausible-but-wrong failure mode this audit hunts.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J4 + §5 (native correction: "accept WITH correction — product not average").
- **Alternatives considered:** Arithmetic mean of edge strengths — REJECTED (native veto: masks weak links); max() of edges — rejected, optimistic-biased, ignores chain fragility; weighted average by edge type — rejected, no classical weighting scheme exists (B.10).
- **Reversibility:** Formula versioned; degeneracy gate added (path_strength must not collapse to a constant across paths); re-derivable on rebuild.
- **Consumer:** `bo_cgm_paths.path_strength` → CGM path ranking → L2+ synthesis, mi_* consumers of CGM.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-014 — Interim tiering: `ka_sangam` relative-percentile basis (DEFERRED recalibration)
- **Phase:** BA Phase 2.5 (P3 J5)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `ka_sangam.convergence_score` sits far below downstream tier thresholds — should v1 weights be recalibrated now?
- **Decision:** RATIFIED-DEFER. Do NOT recalibrate v1 weights now — P5A (strategic track) owns the full recalibration. Interim: tiers computed on a within-chart percentile basis, explicitly flagged `relative_uncalibrated` in the row. The absolute-threshold question (should tiers ever be judged against a fixed score, not just relative rank) is queued as an open question for the P5A brief.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J5; no-fabricated-weighting rule (§0) — recalibrating weights now would be a guess outside this session's scope.
- **Alternatives considered:** Recalibrate weights immediately — rejected, out of scope for this deterministic fix wave and would preempt P5A's dedicated calibration pass; leave tiers on the current absolute (broken) scale — rejected, downstream consumers get a non-functional tier signal; drop tiering entirely until P5A — rejected, removes a partially-useful relative signal.
- **Reversibility:** `relative_uncalibrated` flag removed and tiers recomputed once P5A lands an absolute calibration; fully reversible, no data loss.
- **Consumer:** `ka_sangam` tier column → downstream convergence-window consumers; P5A brief (absolute-threshold question added).
- **Date:** 2026-07-05
- **Status:** RATIFIED-AS-DRAFTED (OPEN — closes at P5A recalibration)

---

### JL-015 — Registry: `ga_structural` count_sql category-ownership single source of truth
- **Phase:** BA Phase 2.5 (P3 J2)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** The hand-maintained count_sql category allow-list has silently drifted twice (migrations 364, 368) — how should categories be derived going forward?
- **Decision:** RATIFIED. Categories are derived from a registered category-ownership table (single source of truth for which categories `ga_structural` owns), retiring the recurring hand-maintenance drift class (M1/drift).
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J2; BA_AUDIT_FIX_PLAN_v1_0.md item 2 recommendation (b).
- **Alternatives considered:** Rely on migration-comment discipline (option a) — rejected, already failed twice; leave as-is — rejected, a third silent-drift incident is a when-not-if.
- **Reversibility:** New registry table, additive migration; count_sql regenerated from it, no destructive change to existing category data.
- **Consumer:** `ga_structural` count_sql / cockpit stats route; `asset_registry` category consistency.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-016 — Serve-time: `ph_muhurta` real tarabala/chandrabala/gochara joins
- **Phase:** BA Phase 2.5 (P3 J6)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `ph_muhurta` hardcodes 0.5 defaults for tarabala/chandrabala/gochara — should these be computed or joined from an existing source?
- **Decision:** RATIFIED. These balas already exist in L1/panchanga — `ph_muhurta` joins them at serve time rather than recomputing or defaulting them.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J6; B.1 facts/interpretation separation (L1 is authoritative for these computed values, L4 references not restates — §N.5).
- **Alternatives considered:** Recompute balas independently inside `ph_muhurta` — rejected, would duplicate L1 computation and risk drift (the exact MSR-drift trap N.5 exists to prevent); keep 0.5 defaults — rejected, flattens the score to a constant (degeneracy).
- **Reversibility:** Serve-time join, no stored duplication; reversible by construction.
- **Consumer:** `ph_muhurta` personalization_score → muhurta recommendation consumers.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-017 — Contamination: `ph_rectification` per-chart TRAINING_EVENTS + chart-attribution check
- **Phase:** BA Phase 2.5 (P1 BLOCKER #11 + P3 J7)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `ph_rectification` hardcodes the native's own 19-event lifelog + natal positions as TRAINING_EVENTS for every chart it scores — how must this be fixed?
- **Decision:** RATIFIED — CONTAMINATION-CLASS. Parameterize TRAINING_EVENTS per-chart (remove the hardcoded Abhisek 19-event lifelog + natal positions from the general path). The fix MUST add a chart-attribution check that FAILS LOUDLY if a chart is scored against another chart's life events — this is not an optional enhancement, it is the fix. The D41 sub-degree scorer (J7 proper) is implemented only AFTER this contamination check lands, never before.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §2 #11 + §4 J7 + §5 (JL-017 contamination-class); B.1 facts/interpretation separation (one chart's events must never silently score another chart).
- **Alternatives considered:** Leave native's events as a documented "default" fallback for other charts — rejected, silently plausible-but-wrong scoring is exactly the failure class this audit exists to catch; fix the scorer (D41) before the contamination gate — rejected per explicit phase ordering in the brief.
- **Reversibility:** Per-chart parameterization; existing scores for other charts were never valid and are cleared on next rebuild (delete-then-insert), not hand-patched.
- **Consumer:** `ph_rectification` D41 scorer; any chart run through rectification.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-018 — Dimension retirement: `mi_pramana` manifestation dimension dropped + renormalized
- **Phase:** BA Phase 2.5 (P3 J8)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `_score_manifestation()` hardcodes `(0.5, None)` for every match — a non-functional 5th dimension. Drop it or fabricate a scorer?
- **Decision:** RATIFIED. Drop the manifestation dimension entirely and renormalize the remaining 4 weights so they sum to 1. The dropped dimension is REGISTERED (not silently deleted) so a future P6 pass (MIMAMSA_V2 S4) can re-add it once a real scorer exists.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §4 J8 + §5 ("register the dropped dimension"); B.10 no-fabricated-computation.
- **Alternatives considered:** Invent a manifestation scoring heuristic to keep 5 dimensions — rejected, no real signal exists behind the hardcoded constant (B.10); silently drop with no registry note — rejected, loses the "P6 needs to re-add this" institutional memory.
- **Reversibility:** Weight renormalization is versioned (`formula_version` bump); dimension re-addable from the registry note without re-deriving from scratch.
- **Consumer:** `mi_pramana` composite score; MIMAMSA_V2 S4 (future P6 item).
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-019 — Safety: `mi_pariksha` negative-control status correction
- **Phase:** BA Phase 2.5 (P1 cheap safety fix, first in sequence)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `mi_pariksha`'s negative-control QA substep is a tautology that can never fail — what should its reported status be?
- **Decision:** RATIFIED. Status corrected to `status='not_implemented'` rather than reporting a passing (but meaningless) QA result — a non-functional negative control must never present as a passing gate.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §2 (J9, cheap safety fix, done first); BA_AUDIT_FIX_PLAN_v1_0.md item 9 (MAJOR, tautological QA).
- **Alternatives considered:** Implement a real negative control immediately — deferred, out of scope for this fix wave's deterministic-fix budget; leave status as a false-passing gate — rejected, actively misleading to anyone reading QA results.
- **Reversibility:** Pure status-field correction; trivially reversible when a real negative control is built.
- **Consumer:** `mi_pariksha` QA substep status; any dashboard/report reading mimamsa QA state.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-020 — Data protection: `mi_abhilekha` clear-protection + REBUILDABLE vs IRREPLACEABLE allowlist classification
- **Phase:** BA Phase 2.5 (P1 cheap safety fix, second in sequence)
- **Ruling agent:** Cowork (delegated Ācārya-Pratinidhi)
- **Question:** `mi_abhilekha`'s per-chart clear destructively wipes the native's real journal answers. What is the correct clear-allowlist classification across the whole platform?
- **Decision:** RATIFIED. `mi_abhilekha` is protected from unscoped/destructive per-chart clear (same pattern as the prior `mi_vistara` fix, JL-precedent in commit e306c475). Beyond this single table, run the full clear-allowlist classification: every table is either REBUILDABLE (writer-derived, safely clearable and regenerated on rebuild) or IRREPLACEABLE (journal answers, LEL intake, prediction outcomes, calibration snapshots, judgment ledgers) — all IRREPLACEABLE tables are protected from per-chart clear.
- **Basis:** CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md §2 (J10) + §4 J9/J10 + §5 ("J10's allowlist classification"); precedent commit e306c475 (`mi_vistara`).
- **Alternatives considered:** Protect only `mi_abhilekha` and stop — rejected, the brief explicitly requires the full-platform classification pass since the same class of bug (unscoped clear on irreplaceable data) was already found twice (`mi_vistara`, `mi_abhilekha`); allow soft-delete/versioned clear for irreplaceable tables instead of a hard block — deferred as a future enhancement, hard-block is the immediate safety fix.
- **Reversibility:** Classification is additive metadata (an `EXPLICIT_CLEAR_OPS`-style allowlist/blocklist); no data touched, purely a guard.
- **Consumer:** Every table's per-chart clear path in the cockpit/orchestrator clear operation; `mi_abhilekha`, `mi_vistara`, and any future L5 table holding irreplaceable data.
- **Date:** 2026-07-05
- **Status:** RATIFIED

---

### JL-021 — Fix directive: `ga_structural` GA8 karaka-web duplicate fact_ids (canonical-school scoping)
- **Phase:** BA Phase-3 (Abhinandan serial-gate fix wave)
- **Ruling agent:** Cowork (strategic track, standing delegation)
- **Question:** The GA8 two-pass integrity gate halts `ga_structural` on duplicate `karaka_web_per_varga` fact_ids for the non-native chart. Four-step directive: (1) DIAGNOSE the colliding rows by diffing payloads to find the missing natural-key field; (2) add it to the key; (3) root-cause `VARGA_MISSING` D30 as its own item; (4) verify migration 416's DAG reorder did not alter ga_structural's read of ga_condition mid-derivation.
- **Decision:** RATIFIED + RESOLVED. Root cause was NOT a missing natural-key field: `ga_sensitive` legitimately emits `karaka_chara_position` for BOTH Jaimini schools (`parashari_rahu_excluded` 7-planet, `kn_rao_rahu_included` 8-planet), and `_build_karaka_web_rows` read all rows unscoped, scrambling two schools into one varga's karaka permutation → colliding fact_ids where the schools agree. Fix: karaka-web reads ONE canonical school (`kn_rao_rahu_included`, the canonical AK) via `AND formula_id = %s`, plus a defensive `dict.fromkeys` dedupe. D30 `VARGA_MISSING` confirmed benign (D30 legitimately absent for this chart, not a bug). Migration 416 reorder verified non-interfering (ga_structural runs strictly after ga_condition; no mid-derivation read hazard). Landed PR #447.
- **Basis:** B.10 no-fabricated-computation (single-school truth, not a fabricated merge); N.5 L1-authority (karaka_web references ga_sensitive's dual-school facts, must not scramble them); live reproduction (14 colliding fact_ids reproduced before any fix).
- **Alternatives considered:** Add school to the natural key so both schools coexist as distinct fact_ids — rejected, karaka_web is per-varga karaka-relationship modeling that must rest on ONE canonical karaka assignment, not a two-school union; dedupe silently without school scoping — rejected, masks which school won and is order-dependent.
- **Reversibility:** Canonical-school constant + versioned query change; cleared on rebuild (delete-then-insert). Dual-school `karaka_chara_position` data in ga_sensitive untouched.
- **Consumer:** `ga_structural` `karaka_web_per_varga`; GA8 two-pass integrity gate.
- **Date:** 2026-07-06
- **Status:** RATIFIED — VALIDATED (run d6ebca1e: 1107 total / 1107 distinct fact_ids, zero dups)

---

### JL-022 — Ownership: avastha fact_categories are `ga_condition`'s sole authority (J2 acceleration)
- **Phase:** BA Phase-3 (Abhinandan serial-gate fix wave)
- **Ruling agent:** Cowork (strategic track, standing delegation)
- **Question:** `ga_condition` and `ga_structural` BOTH delete-then-insert the same avastha `chart_facts` categories (`graha_avastha_lajjitadi`, `graha_avastha_sayanadi`), causing wave-parallel lock contention (the migration-416 root cause). Who OWNS the avastha categories?
- **Decision:** RATIFIED. `ga_condition` OWNS all avastha `fact_categories`. Consumers (incl. `ga_structural`) read them via the DAG edge, NEVER write them. This is the durable fix behind migration 416's interim edge-serialization: accelerate J2 (the per-category ownership registry, precedent JL-015 for ga_structural's count_sql categories) into this fix wave so category ownership is a single source of truth, not an implicit convention. NOTE: implementation must be surgical — ga_structural writes D1 avastha via pyjhora_adapter while ga_condition writes the `_per_varga` variants; the split is per-category, not a blind delete of ga_structural's avastha code.
- **Basis:** B.1 facts/interpretation separation + single-writer-per-category invariant; JL-015 precedent (category-ownership as SSOT); migration 416 root-cause analysis (shared-category delete-then-insert contention).
- **Alternatives considered:** Keep migration 416's DAG-edge serialization as the permanent fix — rejected, it serializes an otherwise-parallel pair to paper over dual-ownership; leave dual ownership and rely on WORKER_LIMIT=1 — rejected, forfeits parallelism permanently and hides the invariant violation.
- **Reversibility:** Additive ownership registry + writer scoping; per-chart categories regenerate on rebuild.
- **Consumer:** `ga_condition` (owner), `ga_structural` (reader); the J2 category-ownership registry; wave-parallel scheduler.
- **Date:** 2026-07-06
- **Status:** RATIFIED — VALIDATED (Option A). PR #450 + migration 418: ga_structural stopped
  emitting graha_avastha_lajjitadi / graha_avastha_sayanadi; ownership reassigned to
  ga_condition (also fixed a pre-existing double-count). Confirmed in parallel run
  d7cddc38: both categories now sourced ONLY from ga_condition
  (`._lajjitadi_from_context` / `._sayanadi_from_degree`); baladi/jagrad/deepta/lifetime
  remain single-writer ga_structural. Full ALL-avastha consolidation (Option B) DEFERRED
  (would change stored values + fact_keys + break a dormant MV, for zero parallel-safety
  benefit). A THIRD ga_structural↔ga_condition dual-write (graha_yuddha) was discovered
  during implementation → the migration-416 DAG edge is intentionally KEPT until a full
  dual-write audit (see JL-026); the parallel restore succeeded with the edge in place.

---

### JL-023 — Contract: per-writer timeout budgets + watchdog + self-test fatality policy
- **Phase:** BA Phase-3 (Abhinandan serial-gate fix wave)
- **Ruling agent:** Cowork (strategic track, standing delegation)
- **Question:** Several writers exceeded the 600s default timeout under load (ga_dashas ~5min, bo_samskara ~8min, ka_dasha_kala self-test). How should per-writer budgets, the watchdog, and self-test failures behave?
- **Decision:** RATIFIED. (a) Per-writer timeout budgets live in `asset_registry` (default 600s; `ga_structural` / `ga_dashas` / `bo_samskara` get 1200–1800s). (b) The watchdog KILLS and FAILS a writer that exceeds its budget — it NEVER hangs the run indefinitely. (c) Writer self-test failures are NON-FATAL (logged, run continues) EXCEPT the two-pass duplicate-fact_id integrity check, which STAYS FATAL (data-integrity gate). (d) `ORCHESTRATOR_WORKER_LIMIT=1` (serial) stays until ONE clean 66/66 serial run on Abhinandan; the parallel restore is its OWN separately-verified step afterward.
- **Basis:** N.2 FROZEN orchestrator contract (orchestrator owns transaction + watchdog, writer never self-manages timeout); IS.8 integrity substrate (integrity gates stay fatal, cosmetic self-tests do not block); operational safety (a hung run is worse than a failed asset).
- **Alternatives considered:** Single global timeout for all writers — rejected, forces the slowest writer's budget on everything or starves it; make all self-tests fatal — rejected, cosmetic self-test flakes would block otherwise-valid builds; make two-pass non-fatal too — rejected, duplicate fact_ids are a hard data-integrity violation (see JL-021).
- **Reversibility:** Registry budget values are data (per-asset UPDATE); watchdog + fatality policy are versioned orchestrator config. Parallel restore is gated behind its own verification.
- **Consumer:** `asset_registry.writer_timeout_seconds` per asset; orchestrator watchdog; every writer's self-test path; the parallel-restore step.
- **Date:** 2026-07-06
- **Status:** RATIFIED — VALIDATED (budgets + watchdog). PR #450 added
  asset_registry.writer_timeout_seconds (default 600; ga_dashas/bo_samskara=1800,
  ga_structural=1200) + per-asset watchdog in runner.execute_dag (kills+fails over budget,
  never hangs). Parallel restore (WORKER_LIMIT=2, 2-CPU job) validated the watchdog live:
  run #1 (8d12cde4) FAILED cleanly when ka_sangam hit 600s (~1.8x parallel inflation of its
  373s serial time) → watchdog evicted+failed it → 25 downstream BLOCKED (correct behaviour,
  no hang). Migration 420 raised ka_sangam+bo_laksana to 1200; re-run (d7cddc38) = clean
  66/66 parallel, 0 errors, ka_sangam 515s. WORKER_LIMIT=2 is now the validated production
  mode (was serial=1 during the fix wave). Self-test non-fatality (part c) was NOT needed —
  no self-test failure occurred once budgets were correct; deferred until evidence demands it.

---

### JL-024 — Operational: rebuild Abhinandan fresh, never restore the snapshot
- **Phase:** BA Phase-3 (Abhinandan serial-gate fix wave)
- **Ruling agent:** Cowork (strategic track, standing delegation)
- **Question:** To recover a clean Abhinandan build after the fix wave, restore Cloud SQL snapshot 1783272757787 or rebuild fresh?
- **Decision:** RATIFIED. Do NOT restore the snapshot — rebuild Abhinandan FRESH through the orchestrator on the fixed HEAD. Snapshot 1783272757787 is disaster-insurance and is never touched/overwritten/restored as a routine recovery path; a fresh rebuild is the canonical proof that the fixed code produces a clean chart from scratch.
- **Basis:** N.3 idempotency (delete-then-insert rebuild REPLACES cleanly); disaster-insurance invariant (the snapshot is a last-resort backup, not a working restore point); a fresh build is the only honest validation that the fixes work end-to-end.
- **Alternatives considered:** Restore snapshot then patch forward — rejected, would validate nothing about the fixed code path and risks mutating the insurance snapshot's role; partial per-asset rebuild — rejected, the gate requires a full clean L1→L5 run.
- **Reversibility:** N/A (directive protects an irreplaceable asset); fresh rebuilds are infinitely repeatable.
- **Consumer:** Every Abhinandan rebuild in this campaign; snapshot 1783272757787 (protected).
- **Date:** 2026-07-06
- **Status:** RATIFIED — HONORED (run d6ebca1e was a fresh rebuild; snapshot never touched)

---

### JL-025 — Documentation: `CURRENT_STATE` append-only changelog at file top
- **Phase:** BA Phase-3 (Abhinandan serial-gate fix wave)
- **Ruling agent:** Cowork (strategic track, standing delegation)
- **Question:** How should this campaign's state be recorded in `CURRENT_STATE_v1_0.md` given it is a large file with prior-session uncommitted edits?
- **Decision:** RATIFIED. Add an APPEND-ONLY changelog entry at the TOP of `CURRENT_STATE_v1_0.md` — do NOT rewrite the file. The BA Phase-3 exit report (`BA_PHASE_3_FIXES_AND_RERUN_REPORT_v1_0.md`) + run ledger §1b remain the detailed record; CURRENT_STATE carries only the pointer.
- **Basis:** B.8 versioning discipline (append-only, no silent mutation of a live state file); ONGOING_HYGIENE_POLICIES §D (SESSION_LOG/state completeness); avoid clobbering another session's uncommitted work.
- **Alternatives considered:** Rewrite the CURRENT_STATE §2 open-items block inline — rejected, risks clobbering prior-session uncommitted edits in a 6000-line file; put the detail in CURRENT_STATE — rejected, duplicates the exit report and violates the "live pointer, not detailed record" role.
- **Reversibility:** Additive changelog entry; trivially editable.
- **Consumer:** `CURRENT_STATE_v1_0.md` top-of-file changelog; any session reading current state.
- **Date:** 2026-07-06
- **Status:** RATIFIED — IN PROGRESS (changelog entry being added this session)

---

### JL-026 — Deferred: full ga_structural↔ga_condition dual-write audit before removing the mig-416 edge
- **Phase:** BA Phase-3 (parallel restore)
- **Ruling agent:** Ācārya-Pratinidhi (in-session judgment under standing delegation)
- **Question:** JL-022 removed the lajjitadi/sayanadi dual-write; can the migration-416
  serializing DAG edge (ga_structural → ga_condition) now be removed to fully restore
  parallelism between the pair?
- **Decision:** DEFERRED — do NOT remove the edge yet. During JL-022 implementation a THIRD
  category written by BOTH writers surfaced: `graha_yuddha` (ga_condition delete-then-inserts
  it in `_build_d1_avastha_rows`; ga_structural writes its richer winner/loser/orb rows, which
  win only because the edge serializes them). Removing the edge without first enumerating the
  COMPLETE set of categories both writers delete-then-insert risks a parallel deadlock on a
  category found only by luck (systematic-debugging: no whack-a-mole). The parallel restore was
  achieved WITH the edge kept — it costs only the one ga_structural/ga_condition overlap while
  every other asset runs parallel. Edge removal is a separate follow-on gated on: (a) a full
  dual-write audit of the two writers' idempotency DELETE category sets, (b) resolving each
  shared category to a single owner, (c) then migration 419 (edge removal) + a verified parallel
  rebuild.
- **Basis:** systematic-debugging (root-cause completeness before structural change); N.2 FROZEN
  orchestrator contract (edges are the safe serialization primitive); B.1 single-writer-per-category.
- **Alternatives considered:** remove the edge now and resolve graha_yuddha alone — rejected, there
  may be further shared categories; keep the edge permanently — rejected, it forfeits the pair's
  parallelism and hides the single-writer-invariant violation (this ruling keeps it OPEN, not
  permanent).
- **Reversibility:** N/A (a deferral); migration 419 is drafted and ready once the audit closes.
- **Consumer:** the follow-on dual-write-audit session; ga_structural + ga_condition; wave-parallel scheduler.
- **Date:** 2026-07-07
- **Audit + resolution (2026-07-07, BA_PHASE4_RUNWAY_PLAN R2.1):** full dual-write audit run (file:line-evidenced). Findings: after JL-022, **`graha_yuddha` was the LAST remaining co-written `chart_facts` category** — ga_structural (`_build_graha_yuddha_rows`, `winner`/`loser`/`orb_deg`, two_pass_verified) and ga_condition (`_build_d1_avastha_rows` → fact_key `opponent`) both delete-then-insert it at identical scope `(chart_id, 'graha_yuddha', ayanamsha_id)`. The mig-416 edge forced ga_structural to run second, so its delete+re-insert **clobbered ga_condition's rows every build — ga_condition's write never survived** (dead write). Resolution (native ruling, "single-writer + remove edge", Option A of the R2.1 fork): (a) removed the graha_yuddha emission from `ga_condition_writer._build_d1_avastha_rows` (kept `_detect_graha_yuddha` for internal ga_condition_composite annotation); ga_structural is now sole authority — **DB-state-preserving** (it already won via clobber). (b) migration **419** removes the `ga_condition` element from `ga_structural.depends_on` (the documented DOWN of mig-416). Verified ga_structural reads NO ga_condition-produced category (it now produces only 4 avastha categories), so dag_edge_guard stays green with the edge gone. Guard test added (`test_ga_condition_jl026_graha_yuddha.py`). Zero co-written categories remain → single-writer-per-category invariant (B.1) restored.
- **Status:** **RESOLVED (2026-07-07)** — audit complete, graha_yuddha single-writer, mig-416 edge removed (mig 419), invariant restored. Winner-rule correctness spun out to **JL-027** (see below). `[verify-against: repo + R3 parallel rebuild]`

---

### JL-027 — Correctness: `graha_yuddha` winner rule is not the true classical rule
- **Phase:** BA Phase-4 runway R2.1 (surfaced by the JL-026 dual-write audit)
- **Ruling agent:** Ācārya-Pratinidhi — **native ruling REQUIRED before R4** (bakes into the native chart)
- **Question:** Graha yuddha (planetary war) winner determination. The audit found the two writers used **contradictory** simplified rules — ga_structural: winner = LOWER ecliptic longitude (`_build_graha_yuddha_rows`); ga_condition (now removed): winner = HIGHER longitude (`_detect_graha_yuddha`). **Neither implements the true classical rule** (winner = the more-northern planet / higher ecliptic latitude — BPHS ch.3), which both self-label as needing Swiss Ephemeris latitude data. JL-026 made ga_structural sole authority, so its "lower-longitude-wins" simplification is what currently ships (and what the native chart would compute at R4). Which rule is authoritative?
- **Decision:** **OPEN — awaiting native/ācārya ruling.** JL-026's single-writer consolidation is orthogonal to and does NOT decide this (it preserved the already-shipping ga_structural value). **Ruling framework (native directive 2026-07-07): CANONICAL-OR-FLOOR.** Before any ruling, the conductor must SURFACE the winner-rule OPTIONS each with its **classical citation** — the criterion, the source text, and the specific verse (e.g. BPHS / Sūrya Siddhānta / Sārāvalī on graha-yuddha jaya-nirṇaya: north/higher-latitude wins; brightness/greater-diameter variants; the "which planet is overcome" śloka). The native then either (a) **picks a cited method** (which ga_structural implements — with the exact citation stored in the row's provenance), or (b) **FLOORS it to NULL + reason** (graha_yuddha winner marked indeterminate with a disclosed reason) when the cited method needs data we lack. **No uncited computable substitute is permitted** — the current longitude proxy (higher/lower longitude wins) is exactly such an uncited substitute and is NOT an eligible option. The true latitude/northern-planet rule, if chosen, is `[EXTERNAL_COMPUTATION_REQUIRED]` (Swiss Ephemeris latitude per graha at chart epoch, B.10 — spec + likely a new L1 fact). **Guardrail:** the native chart must NOT R4-consume graha_yuddha as a load-bearing signal until ruled; if unresolved by R4, floor it (NULL winner + reason) rather than ship the proxy. **Obligation:** conductor surfaces the cited OPTIONS at the next checkpoint (gates R4, not R2).
- **Basis:** J (acharya-grade) + **canonical-or-floor doctrine** (a cited classical method or an honest NULL+reason — never an uncited computable substitute) + B.10 (no fabricated computation — the latitude rule needs real ephemeris data) + the silent-error class this program hunts (two contradictory uncited rules, one silently clobbering the other, was live until R2.1).
- **Reversibility:** ga_structural compute-logic change + optional new L1 latitude fact; re-derivable; no destructive write.
- **Consumer:** `ga_structural._build_graha_yuddha_rows`; downstream graha_yuddha readers (bo_*/ka_* strength/affliction); native chart at R4.
- **Date:** 2026-07-07
- **Native ruling (2026-07-08, BA-R4-WRAP W1→W2 boundary):** **RATIFY OPTION A (Parāśari northern-latitude rule) as the doctrine, FLOOR NOW.** Options surfaced with classical citations in `JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md` (BPHS graha-yuddha śloka + Bṛhat Saṃhitā ch.17 + Sūrya Siddhānta ch.7). Native picked the mainstream Parāśari northern-latitude rule as authoritative, BUT ships the **FLOOR** now (`winner=NULL`, `loser=NULL`, `reason='no_ratified_classical_rule'` on all `graha_yuddha` rows) because implementing A is `[EXTERNAL_COMPUTATION_REQUIRED]` (Swiss Ephemeris ecliptic latitude per graha → new L1 fact + derivation ledger) + owes §5 critical-edition verse verification — neither lands in-session. **The uncited longitude proxy is REMOVED, never shipped.** Option A implementation deferred to R5 (post-runway). The native chart at W4 therefore carries the honest floor, not an uncited winner.
- **Status:** **RULED (2026-07-08) — disposition = "Option A ratified, floored pending data"; FLOOR IMPLEMENTED IN CODE (W2a, PR #459).** `_build_graha_yuddha_rows` now emits winner/loser=NULL + `reason='no_ratified_classical_rule'` (`floored:true`), keeps `orb_deg`; the uncited longitude proxy is REMOVED; `_build_graha_yuddha_per_varga_rows` emits orb only (no winner/loser). Independently verified in code + tests. JL-027 **CLOSES** once the floor is visible in a prod build (first Abhinandan rebuild at W3 shows floored graha_yuddha rows). Option A (Swiss Ephemeris latitude) implementation remains deferred to R5.

---

## RUNNING SUMMARY

| ID | Phase | Category | Status | Reversible? |
|---|---|---|---|---|
| JL-001 | P2 | Prior-tuning | PENDING | Yes — priors_version bump |
| JL-002 | P3A | Seed values | PENDING | Yes — bg_class_priors upsert |
| JL-003 | P3B | Formula | PENDING | Yes — formula_version bump |
| JL-004 | P4 | Golden answers | PENDING | Yes — eval corpus versioned |
| JL-005 | P7A | E4 ranking | PENDING | Yes — P7A close report |
| JL-006 | P3B | Formula: bala_gate | RATIFIED | Yes — formula_version + L2 regen |
| JL-007 | P3B | Formula: verification_certainty | RATIFIED | Yes — formula_version + L2 regen |
| JL-008 | P3A/B | Schema: domain taxonomy | RATIFIED-AS-DRAFTED | Yes — migration + retrieval update |
| JL-009 | P3A→P5B | Data: event base-rate priors | RATIFIED — CLOSED (native glance 2026-07-07; ontology v1.1; ph_nimitta normalize obligation → R2) | Yes — ontology upsert (mig 421) |
| JL-010 | P3A-absorption-fix | Absorption: karakamsa modeling | RATIFIED (OPEN) | Yes — sign-based pass supersedes |
| JL-011 | BA-2.5 P1 | Extraction: bg_rules yoga_canonical_id | RATIFIED | Yes — re-derivable from rule text |
| JL-012 | BA-2.5 P3 | Formula: ga_yoga.strength constituent_bala_v1 | RATIFIED | Yes — derivation versioned |
| JL-013 | BA-2.5 P3 | Formula: bo_cgm_paths.path_strength product | RATIFIED | Yes — formula versioned |
| JL-014 | BA-2.5 P3 | Interim: ka_sangam relative_uncalibrated tiers | RATIFIED-AS-DRAFTED (OPEN) | Yes — supersedes at P5A |
| JL-015 | BA-2.5 P3 | Registry: ga_structural category-ownership table | RATIFIED | Yes — additive migration |
| JL-016 | BA-2.5 P3 | Serve-time: ph_muhurta real bala joins | RATIFIED | Yes — no stored duplication |
| JL-017 | BA-2.5 P1/P3 | Contamination: ph_rectification TRAINING_EVENTS | RATIFIED | Yes — cleared on rebuild |
| JL-018 | BA-2.5 P3 | Dimension retirement: mi_pramana manifestation | RATIFIED | Yes — formula_version + registry note |
| JL-019 | BA-2.5 P1 | Safety: mi_pariksha not_implemented status | RATIFIED | Yes — status-field correction |
| JL-020 | BA-2.5 P1 | Data protection: mi_abhilekha + allowlist | RATIFIED | Yes — additive guard metadata |
| JL-021 | BA Phase-3 | Fix: ga_structural karaka-web canonical school | RATIFIED — VALIDATED | Yes — versioned query + rebuild |
| JL-022 | BA Phase-3 | Ownership: ga_condition owns lajjitadi/sayanadi (Option A / J2) | RATIFIED — VALIDATED | Yes — additive ownership registry |
| JL-023 | BA Phase-3 | Contract: per-writer timeout budgets + watchdog (self-test fatality deferred) | RATIFIED — VALIDATED | Yes — registry data + versioned config |
| JL-024 | BA Phase-3 | Operational: rebuild Abhinandan fresh, never restore snapshot | RATIFIED — HONORED | N/A — protects insurance snapshot |
| JL-025 | BA Phase-3 | Docs: CURRENT_STATE append-only changelog at top | RATIFIED — DONE | Yes — additive changelog entry |
| JL-026 | BA Phase-3 → P4 R2.1 | Audit: ga_structural↔ga_condition dual-write (graha_yuddha) | RESOLVED — single-writer + edge removed (mig 419) | Yes — code + mig 419 DOWN |
| JL-027 | BA Phase-4 R2.1 | Correctness: graha_yuddha winner rule not true classical rule | RULED + FLOOR IMPLEMENTED in code (W2a, PR #459); CLOSES when floor visible in W3 Abhinandan build; Option A impl → R5 | Yes — compute change + optional L1 latitude fact |

---

*JUDGMENT LEDGER v1.0 — initialized 2026-07-03 by CONDUCTOR*
*Append-only. Do not modify prior entries. Ācārya-Pratinidhi appends; native vetos via run report.*
