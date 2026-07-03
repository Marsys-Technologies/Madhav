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

---

## RUNNING SUMMARY

| ID | Phase | Category | Status | Reversible? |
|---|---|---|---|---|
| JL-001 | P2 | Prior-tuning | PENDING | Yes — priors_version bump |
| JL-002 | P3A | Seed values | PENDING | Yes — bg_class_priors upsert |
| JL-003 | P3B | Formula | PENDING | Yes — formula_version bump |
| JL-004 | P4 | Golden answers | PENDING | Yes — eval corpus versioned |
| JL-005 | P7A | E4 ranking | PENDING | Yes — P7A close report |

---

*JUDGMENT LEDGER v1.0 — initialized 2026-07-03 by CONDUCTOR*
*Append-only. Do not modify prior entries. Ācārya-Pratinidhi appends; native vetos via run report.*
