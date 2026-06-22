---
artifact: L5_MIMAMSA_VISION_v1_0.md
canonical_id: L5_MIMAMSA_VISION
version: 1.0
status: DRAFT — vision/charter for the L5 Mīmāṃsā campaign (authored before L4 close; ground-truth audit deferred)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The supreme-ambition vision for L5 Mīmāṃsā — what the layer IS and what it CAN BE to add
  maximal value as the apex of the L0→L5 arc. This is a design/charter artifact, authored
  from first principles + the existing architecture substrate (the MACRO_PLAN Learning Layer
  LL.1–LL.10 charter, the L4 D5/D6/D45 falsifiability seam, the LEL ground truth). It does NOT
  depend on ground-truth code reality; the legacy-code audit + implementation plan are a
  SEPARATE downstream step (L5_MIMAMSA_GROUND_AUDIT, deferred until L4 closes).
upstream_substrate:
  - MACRO_PLAN_v2_0.md §"The Learning Layer" + §LL-Appendix.A–D (the LL.1–LL.10 mechanism charter)
  - L4_PHALA_DECISIONS_LEDGER_v1_0.md D5/D6/D7/D45 (the L4/L5 boundary + ph_pramana seam)
  - LIFE_EVENT_LOG_v1_2.md (LEL v1.7, 57 events — the ground truth)
  - L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md (the campaign entry point)
supersedes: nothing (new)
---

# L5 Mīmāṃsā — The Vision

> *Mīmāṃsā* (मीमांसा) — "reasoned investigation; the critical examination by which a doctrine is
> tested." The sixth darśana, the discipline of valid interpretation and proof. Here it names the
> layer that asks the only question the whole instrument exists to answer: **were we right, and how
> do we get righter?**

---

## §1 — The one-sentence charter

**L5 Mīmāṃsā is the layer that closes the loop:** it takes L4 Phala's falsifiable, time-indexed,
probabilistic predictions, confronts them with **lived reality**, **scores** them with deterministic
and auditable calibration math, and feeds **correction signals** back down the stack so the instrument
measurably improves over time — while being ruthlessly honest about the fact that, today, it is
learning from a single life (n=1).

If L0–L4 build *an instrument that makes claims*, L5 is *the instrument that earns the right to be
believed.* It is the difference between astrology-as-assertion and astrology-as-discipline. This is
the layer that fulfills the project's founding promise in `CLAUDE.md §A`:

> "…time-indexed, probabilistic, **calibrated** predictions **testable against lived reality** and
> **correctable from outcomes**."

Every prior layer is a precondition for this one. L5 is where the mission is either kept or broken.

---

## §2 — What L5 IS (the floor) vs what L5 CAN BE (the ceiling)

The 6 registered `mi_*` stubs describe a *floor*: a predictions table, a calibration table, a
multipliers table, a QA-eval table, a held-out event log, an export log. That floor is real and
necessary. But it dramatically undersells the layer. The project already contains — fully authored
in `MACRO_PLAN_v2_0.md` — a **ten-mechanism Learning Layer charter (LL.1–LL.10)** that is the true
ceiling of Mīmāṃsā. The supreme version of L5 is the one that **unifies the 6-asset delivery vehicle
with the 10-mechanism learning charter.**

| | The floor (6 mi_* stubs) | The ceiling (supreme L5) |
|---|---|---|
| **Calibration** | One `mimamsa_calibration` table mapping confidence→outcome | A full **calibration apparatus**: per-signal, per-domain, per-confidence-stratum reliability curves with bootstrapped CIs, Brier/log scores, ECE, and a held-out validity gate |
| **Learning** | One `mimamsa_multipliers` catalog | The **LL.1–LL.10 mechanism suite** (signal-weight, edge-weight, embedding, prompt, ranker, plan, discovery-prior, Bayesian, counterfactual, fine-tune) operating in shadow-mode with promotion gates |
| **Feedback** | Implicit | An **explicit reverse channel** (the D45 PR4 return path) that flows learned priors BACK to damp/boost L4 `ph_nimitta` confidences, L2 signal weights, L2 graph edges — measurably |
| **Honesty** | A held-out flag | A **leakage firewall** + n=1 disclosure regime + the held-out/non-native apparatus that makes "calibration" mean something rather than mean overfitting |
| **Self-examination** | QA-eval runs | The instrument **scoring its own answer quality** (Pramāṇa over the synthesis itself), not just its predictions |
| **Research** | (none) | The **multi-chart pivot** — the apparatus by which the method becomes testable beyond this one native, fulfilling `CLAUDE.md §A`'s "research tool for astrology as a discipline" |

The vision is the right-hand column. The campaign builds toward it in disciplined increments, never
fabricating calibration it hasn't earned.

---

## §3 — The five jobs of Mīmāṃsā (the value pillars)

Everything L5 does decomposes into five jobs. Each is a pillar of "supreme value"; each maps to assets
and to LL mechanisms.

### Pillar 1 — SCORE (Pramāṇa: proof against reality)
Take every due, falsifiable L4 prediction, match it to LEL evidence, and compute a verdict
(`confirmed / denied / partial / pending`) and a calibration score — **deterministically and
reproducibly** (re-running yields identical verdicts; CLAUDE.md B.10/B.11). Produce reliability
curves: when the instrument says "70% confident," is it right ~70% of the time? Per domain, per
signal-family, per confidence tier. This is the heart; without it nothing else is honest.

### Pillar 2 — ATTRIBUTE (Mīmāṃsā: critical examination of misses)
For every miss, run a forensic trace: which signals *should* have fired, which *did*, which *didn't*,
and *why* the prediction failed (LL.9 counterfactual learning). A miss is not a failure to hide — it
is the single richest data point the instrument owns. The attribution registry is what lets L5
improve rather than merely confess.

### Pillar 3 — LEARN (the LL.1–LL.10 suite, in shadow mode)
Convert scores + attributions into **parameter updates** — signal weights (LL.1), graph edges (LL.2),
embedding adapters (LL.3), prompts (LL.4), rankers (LL.5), plan selectors (LL.6), discovery priors
(LL.7), Bayesian posteriors (LL.8), miss-attributions (LL.9), and eventually fine-tunes (LL.10). Every
update is shadow-mode first, requires ≥N independent observations, is auditable/reversible/versioned,
and **modulates classical priors — never overwrites them** (the §LL-Appendix.C binding rules).

### Pillar 4 — FEED BACK (the reverse channel)
The learning is worthless if it stays in L5. The D45 PR4 return channel is the artery: learned priors
flow DOWN to damp or boost L4 `ph_nimitta` confidences, re-weight L2 `bodha_msr_signals`, adjust L2
CGM graph edges, and re-rank retrieval. L5 is the only layer with a *downward* arrow. Making that
arrow real, measurable, and gated is a core deliverable, not an afterthought.

### Pillar 5 — EXAMINE ITSELF (answer-quality + export integrity)
Mīmāṃsā also means examining the *interpretation*, not just the prediction. L5 scores the quality of
the instrument's own synthesis answers (`mi_pariksha`), and keeps an auditable ledger of every export
(`mi_vistara`) so that what leaves the instrument is traceable. This is the epistemic-hygiene pillar —
the instrument holding itself to its own acharya-grade standard (`CLAUDE.md §J`).

---

## §4 — The honesty problem is the whole problem (n=1, leakage, held-out)

L4 deferred ALL scoring to L5 for three reasons (D5), and those three reasons ARE the L5 design
constraints. A supreme L5 is defined by how rigorously it confronts them rather than papering over them.

**4.1 — Thin data (n=1, ~57 events, ~9/domain).** A per-domain reliability curve from 9 points is
noise dressed as rigor. The supreme response is not to fake confidence intervals but to:
- report **n alongside every score**, always, and widen CIs honestly (bootstrap, not asymptotic);
- **pool** where pooling is defensible (cross-domain priors with partial pooling / hierarchical
  shrinkage toward a global rate) rather than pretending each domain is independently estimable;
- declare a **minimum-n gate** below which a stratum reports "insufficient evidence," not a number;
- treat the whole L5 output as **provisional** until the event count grows (the MACRO_PLAN
  80-event second-pass milestone).

**4.2 — Leakage / circularity (the firewall).** The same LEL events ground L2 signals, seed L4
rectification, and were partly disclosed *after* the framework existed. Scoring L5 predictions against
events that shaped the predictors is **circular** — it measures memorization, not foresight. The
supreme response is a **leakage firewall** (mandated by the handoff §6, modeled on `ph_sodhana`'s):
- a strict **held-out partition** (`mi_jivanaghatana` is literally named "Life event log (HELD-OUT)")
  isolated from everything that trained the predictors;
- **provenance tags** on every event: did it shape a predictor? was it disclosed pre- or
  post-framework? Only events that could not have leaked into the predictor are admissible as clean
  calibration evidence;
- **prospective-only scoring as the gold standard** — predictions made BEFORE an event's window, scored
  AFTER. Retrodiction is reported separately and labeled, never blended into the headline score.

**4.3 — Single-subject ceiling (the multi-chart pivot).** Honest cross-validated calibration may be
impossible on one life. The supreme L5 therefore designs — even if it doesn't yet populate — the
**multi-chart apparatus**: the same scoring loop pointed at non-native charts (the project already has
`1c826d5a` Abhinandan staged). This is the bridge from "calibrated for Abhisek" to "a research tool for
astrology as a discipline" (`CLAUDE.md §A`, `MACRO_PLAN` LL.7 cohort mode / M7). L5 builds the *rails*;
populating the cohort is a later macro-phase.

> **Design verdict:** L5's credibility is *inversely* proportional to how much it claims. The supreme
> version makes **fewer, better-defended** calibration claims with n and leakage-status stapled to each,
> and is architecturally ready to make stronger claims the moment the data supports them.

---

## §5 — The 6 mi_* assets, re-envisioned (with the dependency correction)

The 6 registered assets are the right *skeleton*. Two things elevate them to the vision: (a) **fixing
the `depends_on` to point at `phala_*`** (the handoff flags this — a scoring layer that doesn't depend
on what it scores is wrong), and (b) **loading each with its full LL-mechanism ambition.**

| Asset | Sanskrit | Floor role | Supreme role | Consumes | LL mechanisms |
|---|---|---|---|---|---|
| `mi_jivanaghatana` | Jīvanaghaṭanā | LEL held-out event log | The **clean-evidence vault** + provenance/leakage tagging + held-out partition discipline | `life_events`, LEL provenance | — (ground truth) |
| `mi_bhavisya` | Bhaviṣya | Predictions table | The **prediction registry** that mirrors `phala_pramana`'s falsifiers into a scorable ledger, time-indexed, with due/pending lifecycle | **`phala_pramana`**, `phala_anchors`, `phala_phaladesa` | (feeds LL.1/.8/.9) |
| `mi_pramana` | Pramāṇa | Calibration table | The **calibration engine** — reliability curves, Brier/log/ECE, per-stratum, bootstrapped, n-aware, held-out-gated | `mi_bhavisya` + `mi_jivanaghatana` | LL.8 (Bayesian), validity gate |
| `mi_gunanaka` | Guṇānaka | Multipliers catalog | The **learned-weight register** — the shadow-mode home of LL.1–LL.7 modulators with promotion gates + the **reverse channel** out to L4/L2 | `mi_pramana` | LL.1–LL.7 |
| `mi_pariksha` | Parīkṣā | QA-eval runs | The **answer-quality + self-examination** surface — scores the synthesis itself + houses LL.9 miss-attribution + LL.4 prompt scoring | synthesis outputs, miss traces | LL.4, LL.9 |
| `mi_vistara` | Vistāra | Export log | The **export-integrity ledger** — every PDF/JSON/MCP bundle traceable; the audit boundary of what leaves the instrument | export events | — (hygiene) |

**The dependency correction (flagged for native ratification):** `mi_bhavisya` should `depends_on` the
`phala_*` outputs it scores (at minimum `ph_pramana`/`phala_pramana`), NOT only `bo_laksana` /
`ka_kalasutra`. The seed wiring is DRAFT (handoff §2). The corrected DAG:

```
phala_pramana (L4, the falsifiability seam) ─┐
phala_anchors / phala_phaladesa (L4) ────────┼─→ mi_bhavisya ─→ mi_pramana ─→ mi_gunanaka ─→ [reverse channel → L4/L2]
life_events (held-out) → mi_jivanaghatana ───┘                     │
                                                                   └─→ mi_pariksha (self-exam) ; mi_vistara (export ledger)
```

> This DAG is a **vision proposal**, to be reconciled against the live registry + the actual
> `ph_pramana` column contract during the deferred ground-truth audit, then native-ratified.

---

## §6 — The ph_pramana → L5 seam (the contract L5 consumes)

L4's `ph_pramana` was deliberately elevated (D45) from per-row falsifier-stamping into the instrument's
**falsifiability seam**. It hands L5 a clean, uniform interface so L5 never has to reverse-engineer five
inconsistent hook shapes. L5's design honors it exactly:

- **PR1 — one canonical falsifier schema** `{metric, comparison, threshold, observation_window,
  data_source}` that EVERY L4 prediction conforms to. `mi_bhavisya` ingests this verbatim — it is the
  scorable unit.
- **PR2 — the L5 onboarding contract** — `phala_pramana` already defines the exact columns +
  `pending / due / confirmed / denied / partial` semantics `mi_pramana` reads. L5 is the *consumer*;
  L4 (producer) defined the interface. L5 must not redefine it — it fills the outcome hook and computes
  the verdict.
- **PR3 — evaluation-staging** — `ph_pramana` already FLAGS which pending predictions are due
  (`eval_date` past) and have candidate LEL evidence, WITHOUT scoring. L5 picks up exactly at that
  staged boundary and computes the verdict the D5 line forbade L4 from computing.
- **PR4 — the reverse calibration channel** — `ph_pramana` defined the empty return path by which L5's
  eventual priors flow BACK to damp `ph_nimitta` confidences. **Filling this channel is Pillar 4** —
  the single most architecturally valuable thing L5 does, and the proof that the loop actually closes.

> **Hard rule (L-is-authority, `CLAUDE.md §N.5):** L5 references L4 `phala_*` ids and inherits their
> values; it never restates an L4 computed value as its own truth. A verdict cites the `phala_pramana`
> row it scored. Divergence between L5's read and the L4 fact is a halt-worthy bug, not a stored value.

---

## §7 — What L5 leverages (reuse, never rebuild)

L5 sits atop five sealed layers + the parallel subsystems. The supreme L5 is *thin* precisely because
the substrate is so rich — its job is synthesis-and-scoring, not recomputation.

- **L4 Phala** `phala_*` — the predictions scored (`phala_pramana` = primary input; `phala_anchors`,
  `phala_phaladesa`, `phala_muhurta/mitigation/sankrama`, `phala_rectification`).
- **L3 Kāla** `kala_*` — timing context for every prediction window (`kala_convergence` w/ horizon_tier,
  `kala_jivana_parva`, dāśā timeline). Services callable, not re-derived.
- **L2 Bodha** `bodha_*` — the **richest latent substrate**: 66,738 MSR signals + real embeddings,
  1,505 discoveries, the CDLM cross-domain matrix, RM remedies. The reverse channel writes back here.
- **L1 Gaṇita** `chart_facts` (the 7 FORENSIC anchors), `chart_dashas` (536,471), `chart_divisionals`,
  per-subsystem assets. The fact authority every verdict ultimately resolves to.
- **L0 Brahmagyan** `bg_*` — the citation substrate; every scored prediction traces to classical rule.
- **The LEL** (`life_events` / LEL v1.7, 57 events) — the ground truth, with held-out discipline.
- **Retrieval layer** — `L5_mimamsa` retrieval already scaffolds; L5 adds the calibration view to
  the Whole-Chart-Read (B.11).

**Reuse principle (inherited from L4 D10):** READ-asset → CALL-service → recompute-PyJHora-only-if-absent.
L5 should need **zero** new chart computation — it scores what exists. (PyJHora is the sealed engine;
no JH-parity oracle anywhere.)

---

## §8 — The non-negotiable constraints (the rails)

These are inherited and absolute. The vision is bounded by them.

1. **B.10 — canonical chart immutable.** Never auto-mutate `482012f1`. Rectification adoption stays
   native-gated.
2. **Deterministic-first.** All scoring math is Python, deterministic, reproducible, auditable.
   Embeddings (deterministic transforms) are fine. **Generative LLM never computes a calibration
   number** — at most it narrates a fixed, already-computed result at serve time.
3. **No fabricated computation (B.10/B.11).** If a score needs a value not in L1–L4, mark
   `[EXTERNAL_COMPUTATION_REQUIRED]`. Never invent a calibration number.
4. **Floors aspirational, not gates.** `target_floor` = achieved count; integrity is the only hard gate.
5. **No audience tier.** Writers emit all rows; serve-time governs access.
6. **L-is-authority.** L5 references L4/L2 ids; never restates a computed value (`§N.5`).
7. **Held-out sacrosanct + leakage firewall.** The §4 discipline is mandatory, not optional.
8. **Learning-discipline rules #1–#6** (`§LL-Appendix.C`): priors locked / modulate-never-overwrite;
   Bayesian tight priors; ≥N observations; held-out sacrosanct; auditable+reversible+versioned;
   evidence earns the right to modulate.
9. **Model policy.** Gemini/DeepSeek for any instrument LLM call; **Anthropic BANNED**.
10. **Frozen orchestrator contract.** Every `mi_*` writer is a `@register('mi_*')` `WriterBase`
    subclass; never commits `ctx.db_conn`; `rows_inserted` kwarg; `$1` count_sql; delete-then-insert
    idempotency; service dir COPY'd in the pipeline Dockerfile. Contract change → STOP, raise with native.
11. **Whole-Chart-Read (B.11).** Every query routes through L2 synthesis; L5 adds the calibration view.

---

## §9 — Why this is *supreme*, not just complete

A merely-complete L5 lights up 6 cockpit assets and stores some scores. The **supreme** L5 is defined
by four properties no individual astrologer — and no other astrology product — can offer:

1. **It is falsifiable and it knows its own track record.** It can state, with bootstrapped CIs and
   honest n, how often its 70%-confidence claims come true, per domain. Astrology that grades itself.
2. **It closes the loop measurably.** The reverse channel means a miss in 2026 demonstrably changes a
   weight that changes a 2027 prediction — and the change is auditable, reversible, and versioned. The
   instrument is not static; it is *learning*, on the record.
3. **It is honest about n=1 as a feature, not a bug.** The leakage firewall + held-out discipline +
   provisional-validity regime make its modest claims *trustworthy*, which is rarer and more valuable
   than grand claims that are untestable.
4. **It is the seed of a discipline.** The multi-chart rails turn one calibrated life into a method
   that can be validated across many — the project's stated end goal.

This is the layer that lets the instrument say, finally and credibly: *not "the stars say," but "here
is what we predicted, here is what happened, here is how often we are right, and here is how we got
better."*

---

## §10 — Open design decisions for native ratification

These are the vision-level forks to settle before (or at) the implementation-planning session. None
require ground-truth code; all shape the campaign.

| # | Decision | Options | Cowork lean |
|---|---|---|---|
| **V1** | **Scope of the first L5 build** — full LL.1–LL.10 suite vs a disciplined core first | (a) Core first: SCORE + ATTRIBUTE + the reverse-channel rails (LL.1/LL.8/LL.9), defer LL.2–LL.7/LL.10 to shadow-scaffold; (b) full suite now | (a) — earn calibration before automating learning; matches the n=1 risk-aversion stance |
| **V2** | **Dependency correction** — re-point `mi_bhavisya` at `phala_*` | (a) correct now to consume `phala_pramana`; (b) keep seed wiring, bridge in writer | (a) — the DAG should tell the truth |
| **V3** | **Held-out strategy** — how to partition 57 events without starving the score | (a) provenance-based admissibility (clean events only) + prospective-only headline; (b) random 20% hold-out; (c) both, reported separately | (c) — report both, headline the clean/prospective one |
| **V4** | **Reverse channel activation** — does L5 actually write back to L4/L2 in v1, or only stage the writes? | (a) stage-only in v1 (shadow), native-gated promotion; (b) live write-back | (a) — shadow first per learning-discipline; promotion is a native gate |
| **V5** | **Multi-chart rails** — build the apparatus now (empty) or defer entirely | (a) design the schema to be chart-keyed + leave cohort unpopulated; (b) native-only, add multi-chart later | (a) — cheap to design in, expensive to retrofit |
| **V6** | **`mi_pariksha` answer-quality scope** — score predictions only, or also score synthesis answers | (a) predictions only in v1; (b) include synthesis-answer QA + LL.4 prompt scoring | (a) for v1, (b) as the ceiling |
| **V7** | **Calibration metric set** — which scores are headline | Brier, log-loss, ECE, reliability curves, hit-rate-by-tier — pick the canonical few | Reliability curve + Brier + hit-rate-by-tier as headline; log-loss/ECE as diagnostics |

---

## §11 — How this becomes implementation (the handoff to planning)

This vision is deliberately **ground-truth-independent** (per native direction 2026-06-22: plan the
vision now; audit the ground reality after L4 closes). The path to code is:

1. **L4 closes** (parallel native workstream) → its `L4_PHALA_CLOSE_v1_0.md` seals `phala_pramana`'s
   exact column contract.
2. **Ground-truth audit** (`L5_MIMAMSA_GROUND_AUDIT_v1_0.md`, deferred) — the deep per-file audit of
   the ~12 legacy `brahmagyan/mimamsa/` files + 5 `brahma_mimamsa_*` migrations + `tests/l5/` against
   the frozen contract, plus the prod-truth reconciliation (which `mimamsa_*` tables exist/are empty).
   Verdict per file: reference-for-intent / reuse-clean / rewrite. (A pasteable kickoff brief for this
   is authored alongside this vision.)
3. **Reconcile vision ↔ reality** — settle V1–V7, correct the DAG, set the campaign arc (mirror the
   L3/L4 pattern: audit → holistic → per-asset specs → wire to frozen contract → retrieval → clean seal
   with the live-deployment guard).
4. **Build, autonomously**, against the frozen orchestrator contract; **seal against the LIVE prod
   cockpit** (`mimamsa == N lit`), never the branch (the #1 L3/L4 lesson).

---

*End of L5_MIMAMSA_VISION v1.0. The vision: Mīmāṃsā is the loop-closing learning/calibration layer that
scores L4's falsifiable predictions against lived reality, learns from the result, feeds correction back
down the stack, and does so with ruthless honesty about n=1 and leakage. The floor is 6 assets; the
ceiling is the LL.1–LL.10 charter unified with those assets + a reverse channel + a leakage firewall +
multi-chart rails. Supreme = falsifiable, loop-closing, honest, and the seed of a discipline.*
