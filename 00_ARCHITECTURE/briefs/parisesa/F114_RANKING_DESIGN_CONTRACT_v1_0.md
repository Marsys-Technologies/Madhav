---
canonical_id: F114_RANKING_DESIGN_CONTRACT
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-114
class: CL-10 (jargon / raw-internal leakage into user-facing prose)
authored: 2026-08-21
authored_by: PARIŚEṢA-V4 repair lane (GA-2 design authority)
execution_status: IMPLEMENTED — code repair landed; no production data written
---

# F-114 — the domain-lens ranking contract

## §1 — What this document is

The corpus ledger filed F-114 as design work: *"Needs a precode ranking contract
(question-lens relevance + tie-break rules) authored and reviewed before
implementation."* This document is that contract. It was written **after** the
diagnosis rather than before, because the diagnosis changed the answer: the
ranking contract F-114 asks for already exists in this codebase, fully specified
and classically sourced. What did not exist was its wiring into the surface the
finding names. This is therefore a **wiring repair with a disclosed coverage
contract**, not a from-scratch ranking algorithm — and saying so is the honest
report, not a shortcut.

---

## §2 — Reproduction (live, 2026-08-21, canonical chart `482012f1`)

The finding still reproduces exactly as filed. Measured directly against the
production `bodha_msr_signals` rows for the marriage lens family
(`domains_affected_array && {relationship}`, `lahiri_chitrapaksha`):

| measurement | value |
|---|---|
| family size (`signal_count`) | **3,698** — matches the filed figure exactly |
| top salience value | **2.16108** — matches the filed figure exactly |
| rows tied at 2.16108 | **13** |
| rows tied at 0.82800 | **61** |
| distinct salience values in the served top-10 | **1** |
| distinct source assets in the served top-10 | **1** (`ga_sensitive`) |

The thirteen tied rows are, verbatim: `SAT: sun derived upagraha`, `SAT: upagraha
position` (×2), `SAT: midpoint` (×2), `SAT: saham position` (×2), `SAT: bhrigu
nadi point` (×2), `SAT: graha pada join`, `SAT: graha nakshatra join`, `SAT:
esoteric point shiva`, `SAT: aprakasha position`. Ten of them are what the lens
served. The filed claim is accurate in every particular.

---

## §3 — Diagnosis

### §3.1 Where the order comes from

`bodha_question_lenses.all_relevant_ranked_jsonb.ranked_signals` is written at
**build time** by `bo_drishti.py`. Its entire ranking is one line:

```python
all_signals.sort(key=lambda x: x["salience"], reverse=True)
```

fed by a query ordered `ORDER BY computed_salience DESC NULLS LAST`.

Two independent defects follow:

1. **Non-discriminating.** Every row in the family already matches the domain
   tag — that is what put it in the family. Ranking that set by a *global,
   domain-agnostic* salience does no within-domain discrimination whatsoever. It
   answers "which of these is loudest chart-wide", never "which of these bears on
   marriage".
2. **Not a total order.** With a 13-way exact tie at the head and no tie-break in
   either the SQL or the Python sort, the served top-10 is whatever Postgres'
   physical row order happened to produce. Two rebuilds of the same chart could
   legitimately serve different "top 10 marriage signals" — a reproducibility
   defect independent of the relevance defect.

### §3.2 The candidate that looked like a free fix, and is not

`bodha_msr_signals.domain_salience_jsonb` looks like a per-domain relevance
weight. It is not. Verified across all 3,698 rows of the family:

```
count(*) = 3698 ; rows where domain_salience['relationship']
                  ≠ computed_salience / cardinality(domains_affected_array) = 0
```

It is a **uniform split** of the same global salience. It carries zero
domain-specific information, and ranking on it merely trades the Saturn tie-block
for an equally domain-blind `D108`/`D54` aspect-aggregate tie-block. Recording
this explicitly so no future lane re-proposes it.

### §3.3 The contract that already exists

`platform/src/lib/retrieval/ranking/composite_ranker.ts` implements a fully
specified, classically sourced, domain-aware ranking contract:

```
composite = class_prior
          × topic_relevance      (graha×domain × bhāva×domain × varga-grain)
          × intrinsic_strength   (real L1 śaḍbala + dignity)
          × structural_role      (CGM centrality, class-constant floored)
          × temporal_activation  (current MD/AD lordship)
          × fired_sensitive_degree_boost
final_rank_score = composite × percentile_within_class
                 + 0.001 × salience_norm          (layer 2)
                 + index_tiebreak at 1e9 scale    (layer 3)
```

Its three-layer tail exists *precisely* to guarantee what F-114 says is missing:
no two served positions share a `final_rank_score`. Its domain weights are in
`priors_config.ts` and are sourced, not invented — `GRAHA_DOMAIN_AFFINITY`
(Venus × relationship **1.50**, Saturn × relationship **0.90**) and
`DOMAIN_BHAVA_AFFINITY` (relationship = {7 kalatra **2.20**, 12 śayana-sukha
1.60, 8 māṅgalya 1.50, 4 sukha 1.20}, BPHS Bhāvādhyāya + the four bhāva-trikoṇas).

This ranker is already used by `query_signals`, by `assess_*`'s stage pool, and —
decisively — by the *top-level* `ranked_signals` surface **in the same file** that
serves the degenerate lens array. `query_domain_reading.ts` had even written the
diagnosis into its own comments ("the stored lens ranked_signals sort by a
domain-agnostic global `computed_salience`") without the per-lens array ever
being routed through the fix.

**F-114 is that ranker not being wired into the per-lens surface.**

### §3.4 The trap that makes it more than a one-line wiring change

A ranker can only re-rank what it is given, and the obvious implementation —
re-rank the head of the stored array — would have failed silently. Measured on
the real family:

| row class | count in family | best stored rank |
|---|---|---|
| Venus-bearing rows | 47 | **902** |
| 7th-house rows | 115 | **1,041** |
| any resolvable graha | 404 | 1 |
| any resolvable bhāva | 1,469 | 36 |

Within the top **400** by stored salience there are **zero** Venus rows and
**zero** 7th-house rows. A head-window re-rank of any affordable size would have
produced a perfectly correct ranking of a candidate set that never contained the
domain's own kāraka or kalatra-bhāva — and F-114's actual complaint ("not one
names the 7th lord, Venus, or a marriage yoga") would have survived the fix while
the response claimed to be domain-ranked. That is exactly the §N.8 defect class:
a green signal with no detector behind the claim it asserts.

---

## §4 — The contract, as implemented

**Candidate set** for each lens = `salience-head window ∪ domain-anchor slice`.

1. **Salience-head window** — top `LENS_RERANK_CANDIDATE_SIZE` (400) of the
   lens's stored family, mirroring `DISCRIMINATION_CANDIDATE_SIZE`.
2. **Domain-anchor slice** — one bounded (`300`), salience-ordered query for rows
   naming a graha or bhāva the domain's **own** affinity tables rate above
   neutral, intersected exactly against the lens's stored membership set so a
   lens is never handed a row it does not carry.

The anchor set is produced by `domainAnchorActors(domain)`, a **pure projection**
of `GRAHA_DOMAIN_AFFINITY` + `DOMAIN_BHAVA_AFFINITY`. It is deliberately not a
second hand-maintained list: a separate list can drift from the weights that score
it (the GA.1 registry-disagreement failure mode). For `relationship` it resolves
to grahas {venus, jupiter, moon} and bhāvas {4, 7, 8, 12} — Venus and the 7th
arrive because the ranker's own tables already say they belong, not because this
lane decided marriage means Venus.

**Ranking** = `applyCompositeRanking(candidates, l1ctx, domain)` — the existing
contract, unchanged. No new scoring term was invented for F-114.

**Ordering of the served array**: candidate rows sort by composite rank; rows
outside the candidate set keep their stored relative order and sit strictly below
it. Nothing is filtered out (B.10) — the re-rank **reorders**, and
`ranked_signals_total` still discloses the true family size.

**Receipts** (§N.6 density signalling / §N.8 earned signals). Each lens carries
`ranked_signals_rank_basis` ∈ {`composite_4d_domain_overlay`,
`stored_salience_build_time`} and `ranked_signals_rerank_window`; the response
carries the roll-up plus a prose note naming the anchor actors and the bound. When
the re-rank cannot run — any DB failure, no ranker rows, or a domain with no
overlay (`other`/`general`) — the response reports `stored_salience_build_time`
and explicitly warns the head must **not** be read as "the top N for this domain".
A re-rank that did not happen is never reported as though it had.

**Build-time companion fix.** `bo_drishti.py` now orders totally
(`computed_salience DESC, signal_id ASC`; sort key `(-salience, not in_template,
signal_id)`), `LENS_FORMULA_VERSION` → `drishti_formula_v1.1`. This fixes §3.1
defect 2 (reproducibility) only. It deliberately does **not** attempt domain
discrimination: re-implementing the composite ranker in Python would create a
second, drifting authority over the same judgment (§N.5). The stored order stays
honestly domain-agnostic and the serving layer owns relevance. **This half takes
effect only on the next chart rebuild; the serving fix is effective immediately
and does not depend on it.**

---

## §5 — Evidence

Unit (`query_domain_reading.f114_lens_rank.test.ts`,
`priors_config.f114_anchors.test.ts`), all passing; each assertion mutation-checked
to confirm it fails without the fix:

- the served top-10 no longer shares one salience value or one source asset;
- every served row has a distinct, monotonically decreasing `final_rank_score`;
- a kāraka/7th-house row buried at stored index 415 — outside the 400 window — is
  promoted by the anchor leg to rank 1 (fails without the anchor leg: asserted);
- the full family is still served when the cap allows; nothing is dropped;
- the basis reads `stored_salience_build_time`, honestly, when the re-rank cannot run;
- `domainAnchorActors` never disagrees with the affinity tables it projects.

**Live, against production rows** (canonical chart, real ranker, real L1 context;
the ranker was run over the real candidate set rather than simulated):

| | before | after |
|---|---|---|
| distinct salience values in top-10 | 1 | 5 |
| distinct `final_rank_score` in top-10 | 1 (tied) | 10 |
| `ga_sensitive` rows in top-20 | 20/20 | 9/20 |
| top-20 rows on bhāva 7 | **0** | **6** |
| top-20 rows naming Venus | **0** | **5** |

The post-fix head leads with `bhava significance link: lord placed = kendra_link`,
`conjunction per varga`, and `lord in house per varga: lord placement =
Venus_in_H9` / `Venus_in_H3` — bhāva-lord structure and kāraka placement, in place
of ten indistinguishable Saturn upagraha rows.

---

## §6 — Disclosed limitations (not papered over)

1. **Bounded coverage, not exhaustive.** Both legs are bounded (400 + 300). This
   guarantees the domain's significators are **considered**; it does not guarantee
   every one of 3,698 family members is. The bound is disclosed on the response
   and the whole family stays reachable via `query_signals`. Widening it is a
   cost/coverage dial, not a correctness fix.
2. **The fix ranks the corpus; it does not enrich it.** F-114's phrase "or a
   marriage yoga" is *not* fully discharged here. The corpus's relationship-tagged
   rows on this chart are dominated by `ga_sensitive` point-position and
   `ga_structural` aspect-aggregate signals; whether the MSR build should be
   emitting first-class 7th-lord and marriage-yoga signals into this domain tag at
   all is a **separate, upstream question about `bo_laksana`/MSR coverage**, not a
   ranking question. Ranking cannot surface what was never written. Flagging this
   rather than letting the improved head imply the gap is closed.
3. **`assess_marriage`'s own kernel is a different surface.** F-114's reproducer
   reads `house_analysis.question_lenses[…].all_relevant_ranked_jsonb`, which is
   `query_domain_reading`'s output — the surface repaired here. `assess_marriage`'s
   budget-trimmed kernel verdict was not modified.
4. **Not verified end-to-end through the deployed MCP server.** The serving fix is
   verified by unit test and by running the real ranker over real production rows;
   it is not yet verified through a deployed build of this branch, which requires a
   deploy this lane does not own.

---

## §7 — Files touched

| file | change |
|---|---|
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | per-lens domain-aware re-rank + anchor slice + rank-basis receipts |
| `platform/src/lib/retrieval/ranking/priors_config.ts` | `domainAnchorActors()` — projection of the two affinity tables |
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_drishti.py` | total ordering; `LENS_FORMULA_VERSION` → v1.1 |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/__tests__/query_domain_reading.f114_lens_rank.test.ts` | new regression suite |
| `platform/src/lib/retrieval/ranking/__tests__/priors_config.f114_anchors.test.ts` | new anchor-projection suite |

No migration. No production data written. No PARIPRAŚNA/EKAVĀKYATĀ file touched.
`composite_ranker.ts` — the ranking contract itself — is unmodified.
