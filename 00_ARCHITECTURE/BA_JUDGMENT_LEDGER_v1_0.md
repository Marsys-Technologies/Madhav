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
- **Status:** RATIFIED-AS-DRAFTED (OPEN — closes at P5B anchor freeze after native glance)

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
| JL-009 | P3A→P5B | Data: event base-rate priors | RATIFIED-AS-DRAFTED (OPEN) | Yes — ontology upsert |

---

*JUDGMENT LEDGER v1.0 — initialized 2026-07-03 by CONDUCTOR*
*Append-only. Do not modify prior entries. Ācārya-Pratinidhi appends; native vetos via run report.*
