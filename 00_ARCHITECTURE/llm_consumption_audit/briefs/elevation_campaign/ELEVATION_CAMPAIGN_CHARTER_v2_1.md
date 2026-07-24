---
artifact: ELEVATION_CAMPAIGN_CHARTER (SATYA-KAVACA + PŪRṆA-GRAHAṆA)
canonical_id: ELEVATION_CAMPAIGN_CHARTER
version: 2.1
status: READY-FOR-EXECUTION — governing charter for the 3-stream autonomous overnight elevation run
created: 2026-07-24
v2_1_changelog: >
  Adversarial red-team pass (two independent Opus reviewers, 2026-07-24) found 27 defects in v2.0,
  of which 14 were run-killing. All fixed in place. The material ones: (1) the TCI could be STUBBED,
  making every Ω gate pass on a fake denominator — schema map moved to Phase 0 and a hard TCI sanity
  gate added (§2 Ω1); (2) the flagship acceptance had no defined consumer and was graded by an agent
  holding the answer key — a SEALED EVALUATOR HARNESS is now frozen in Phase 0 (§2 Ω-V);
  (3) Ω3's 100%-accounting CI gate could deadlock all three streams with no authority to relieve it
  — now allowlist-scoped and warn-only outside it; (4) Ω4's criteria were passed by a degenerate
  "always deepdive" classifier — a symmetric narrow-precision criterion was added and the labelled
  set is frozen before the builder is spawned; (5) Ω5's synthesis gate was prose, not enforcement —
  now structural; (6) β's convention change would have left every non-canonical prod chart silently
  wrong — convention tagging + a third-chart check added; (7) MODE 2 had no working-tree isolation,
  no live-implementation signal, an α single-point-of-failure, an unsatisfiable Phase-0 gate, a
  TTL that breaks locks mid-rebuild, and mismatched flag names — §7.5 is rewritten as a binding
  operating protocol; (8) no rollback runbook existed for a FORENSIC failure at 3am (§11.9).
supersedes: >
  ELEVATION_CAMPAIGN_CHARTER_v1_0.md (same day, same session). v1.0 is preserved at
  00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/archive/ELEVATION_CAMPAIGN_CHARTER_v1_0.md.
  Do NOT execute v1.0. TWO material changes: (a) v1.0 inherited EL-04's "≥90% consumption ratio"
  target and treated total consumption as a METRIC — the native's 2026-07-24 directive supersedes
  this: depth is the DEFAULT POSTURE and completeness is a 100%-accounted CONTRACT, specified as
  the new Lane Ω (§2), which is now the campaign's centre of gravity; (b) v1.0's 13 sequential-wave
  lanes are restructured into THREE independently-deployable parallel streams (§4) each running its
  own multi-agent swarm, for ~3x coding velocity.
author: >
  Fable / Opus (Cowork planning session, 2026-07-24) — root-cause pass over ELEVATION_REGISTER v1.1
  (EL-01..EL-61) with live-server corroboration and code-level grounding, for autonomous execution
  by three parallel Claude Code agent swarms on the native's machine.
item_of_record: 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1)
mode: >
  FULLY AUTONOMOUS · overnight · zero human gates · 3 parallel streams · each stream owns its own
  worktrees, branches, commits, PRs, merges, GitHub pushes, deploys and cleanup · Sonnet base with
  Opus step-up · every close Verifier-gated against live production
model_policy: >
  base = SONNET for all builders and mechanical runners. OPUS for: every Meta/Stream Conductor,
  every Verifier, the Native-Proxy, the Goal-Keeper, and the lanes marked [OPUS] (Ω, A, D, D2, F, I).
  Auto-escalate any lane to Opus after 2 failed verify cycles on the same criterion, or whenever
  authoring classical rules / writer mathematics / cross-cutting envelope refactors. No Fable, no
  non-Anthropic models in the dev loop (the standing "no Anthropic models in PRODUCT serving paths"
  constraint is untouched — this is development tooling, not a serving path).
native_rulings (2026-07-24 Cowork session — explicit, binding):
  - Vehicle: Claude Code on the native's machine, overnight, fully autonomous, no human gates.
  - Risk: FULL — production deploys and chart-scoped prod rebuilds authorized.
  - Scope: FULL register, tiered. Native-only items become prepared packets, never skipped.
  - Velocity: three parallel streams, each with its own multi-agent implementation; a conductor
    kickoff spins up its own environments, commits, merges, pushes, deploys, cleans up.
  - DONE requires a dedicated intelligent Verifier agent's independent confirmation.
  - Any question that would otherwise go to the human is answered by the Native-Proxy agent.
  - **THE DEPTH MANDATE (§0) — the single most important requirement of this campaign.**
---

# SATYA-KAVACA + PŪRṆA-GRAHAṆA — Elevation Campaign Charter v2.0

## §0 — THE DEPTH MANDATE (read this first; everything else serves it)

**Native directive, verbatim in substance (2026-07-24):**

> The default is detailed, thorough, comprehensive, extensive, deep-research analysis. The only —
> marginal — exception is a very clearly narrow, pointed question. And the deep research must be
> *truly* deep: for a financial question, **every remotely relevant piece of information about the
> financial domain must be pushed to the LLM before it synthesises.** There is an enormous amount of
> mathematical computation and data that exists and is not being served to the LLM — that is why the
> product is mediocre. It must be truly extensive, without missing a single concept, a single
> pattern, a single chain, a single mathematical computation that is relevant. Every aspect of the
> deep computations we have done must be covered.

**This supersedes EL-04's "≥90%" target.** The contract is:

> **served ∪ explicitly-accounted-for = 100% of the domain-relevant corpus.
> A silent omission is a BUILD FAILURE, not a quality miss.**

### §0.1 — Why v1.0 did not deliver this (honest gap analysis)

v1.0 treated total consumption as a *metric to raise* (consumption-ratio ≥0.9, EL-04's own number).
That is not the mandate. Three specific shortfalls:

1. **Wrong denominator.** v1.0 derived the concept ledger from `census × floors × inventory` — with
   floors as a co-equal source. But floors are hand-curated, so a floor-derived ledger inherits
   every curation blind spot. The native's "~20% unknown-unknown" (EL-01) survives untouched.
2. **Wrong target.** 90% institutionalises a 10% silent shortfall. On a 33-item floor that is three
   missing layers per reading, chosen arbitrarily.
3. **No depth default.** v1.0 never addressed the *routing posture* — whether a question gets deep
   treatment at all. It optimised the depth of the deep path without making the deep path default.

### §0.2 — Live evidence that the mandate is unmet (probed this session, prod, chart 482012f1)

**A. The compiled wealth floor is a curated 33-item subset, not the corpus.**
`plan_retrieval(question="How is my wealth?")` compiles `wealth_deepdive` with **20 acharya_floor +
13 machine_band = 33 primitives**. Against a corpus of hundreds of fact_categories, this is a
worked-example list. Verified omissions in the wealth floor specifically:
- `ashtakavarga_scan` → `ganita_chart_facts_get(category=ashtakavarga)` — **natal AV only. No
  per-varga ashtakavarga**, though `varga_ashtakavarga` rows are live and served for every varga
  (census A.7). This is EL-26's verified gap, now confirmed *at the floor level*.
- `divisional_facts` → **`varga: "D2"` only.** D11 (Labha) — the second classical wealth varga —
  is not in the wealth floor at all. Confirms EL-45 one layer higher than the assessor.
- `special_lagna_read` → **`lagnas: ["indu","sree"]` only.** No other special lagna, no saham.
- **No argala primitive anywhere in the wealth floor** — argala on the 2nd/11th is a load-bearing
  classical wealth layer (EL-38's original complaint) and the planner cannot express it.
- **No dispositor-chain primitive anywhere in the wealth floor** — the single structure the native
  first named in EL-01 as unused-until-asked.
- No cross-ayanamsha axis (EL-27: the word "ayanamsha" appears zero times in the planner registry).

**B. The depth default is literally `standard`, and the authoritative classifier is the weaker one.**
`intent_classify("How is my wealth?")` — the most canonical domain question that exists — returns:
`intent: "unknown"`, `depth: "standard"`, `width: "standard"`, `confidence: 0.2`,
`entitlement: "restricted"`, `fallback_recommended: true`. Meanwhile `plan_retrieval`'s own
*coarse keyword fallback* correctly resolves `intent: wealth_deepdive`, `depth: deepdive`,
`entitlement: native`. So the DR-8 authoritative classifier is strictly worse than the fallback it
was built to replace, and its default posture is `standard` — not `deepdive`. **The native's
"default must be deep" is violated at the first routing decision.**

**C. The completeness receipt is an offer, never a contract (EL-02, now measured).**
The same plan returns `completeness_receipt.coverage: {floor_item_total: 33, served: 0, empty: 29,
dark: 4}` — all 29 "empty" are `pending_execution: live_tool not yet invoked`. Nothing forces
execution; nothing forces the `observations` round-trip; nothing verifies the answer against the
receipt.

**D. A `hard_floor: true` item is currently unreachable.**
`mechanism_read` → `bodha_mechanisms_get` is marked `hard_floor: true` in the wealth machine band.
That tool 500s on every call (EL-37, root cause found — §5.α.B). **The plan mandates a hard floor
item the estate cannot serve** — patterns, chains and mechanisms, the exact things the native named,
are 100% dark today.

**E. Four floor items are dark against OPEN CRs**: `taranga_curve` (CR-66),
`gochara_activation_read` / `gochara_forecast_read` / `election_read` (CR-131).

### §0.3 — The mandate's one real architectural tension, and its resolution

You cannot simultaneously (a) push 100% of the relevant corpus to the LLM and (b) fit a ~25k-token
per-tool-response cap. **The resolution is that these are different budgets:** the cap is
*per response*, the mandate is about *what reaches the model's context*. Therefore:

- **Depth arrives in MORE TURNS, never in less substance** (EL-28's principle, now load-bearing for
  the depth mandate rather than merely for UX).
- **Density engineering is what keeps the turn count sane** — pivoted rows, provenance emitted once,
  a symbol dictionary served once per session, compact numeric arrays. Lane A's budget work is
  therefore *the enabler of total depth*, not its adversary. This reframing is binding on Stream α:
  every byte saved by densification is a byte of additional CONTENT that fits, not a byte saved.
- **A synthesis gate makes the accumulation enforceable** rather than hoped-for (Ω5).

---

## §1 — Kickoff and the three-stream topology

### §1.1 — How the native launches this (one command, one session)

1. Open Claude Code at `/Users/Dev/Vibe-Coding/Apps/Madhav` with bypass permissions, prod
   credentials (gcloud auth, `DATABASE_URL`, GitHub push rights) available.
2. Point it at this charter (root `CLAUDECODE_BRIEF.md` routes here).
3. The **Meta-Conductor** boots, runs Phase 0 (§7), then spawns **three Stream-Conductors** which
   run fully independently. The native sleeps.

*(If the native prefers three terminals, each Stream-Conductor section (§4) is self-contained and can
be launched directly — Phase 0 must still run once, first, in one of them.)*

### §1.2 — The three streams

| Stream | Name | Mission | Primary deploy targets |
|---|---|---|---|
| **α** | **SATYA — Truth & Envelope** | No response lies, starves, hides, or overflows. Every surface works. | `platform` (registry handlers) · `platform-mcp` |
| **β** | **GAṆITA — Compute & Corpus** | Every number is right; every missing computation now exists. | `amjis-sidecar` · pipeline job · prod DB (chart-scoped rebuilds) |
| **γ** | **PŪRṆA — Depth & Intelligence** | Every relevant computed fact, pattern and chain reaches the LLM before synthesis. | `platform-mcp` (new tools + vidhi resources) · `platform` (planner, assessors, ranking) |

**Why this split:** it minimises file collision (each stream owns a disjoint manifest, §4), aligns
with independent deploy targets so streams never queue on each other's releases, and puts the depth
mandate in its own stream with its own conductor so it cannot be starved by defect work.

**Rough weight:** α ≈ 35%, β ≈ 30%, γ ≈ 35% of estimated effort. Streams that finish early pull
from the Meta-Conductor's overflow queue (§7.5) rather than idling.

---

## §2 — LANE Ω [OPUS] · PŪRṆA-GRAHAṆA: the total-consumption engine

*Stream γ. The campaign's centre of gravity. Everything in §0 is delivered here.*

### Ω1 — TCI: the Total Concept Inventory (the correct denominator)

Machine-generated from the **database itself**, never from floors. Enumerate exhaustively:

- every `fact_category` × `fact_subject` family × `fact_key` across all L1 chart_facts;
- every L2 surface: `bodha_msr_signals` signal_type_ids, `bodha_convergence` domains,
  `bodha_cgm_nodes`/`_edges` types, **all 10 `bodha_mechanisms` classes**, discoveries/anomalies,
  contradiction poles, quality/attribution surfaces;
- every L3 kala surface: dasha systems (all, per DR-14) × levels, windows, projections, life-arc,
  yoga-activation, gochara sweeps, muhūrta;
- every L4 phala/prashna surface and every L5 mimamsa/LEL/calibration surface;
- every varga (all 16+), every ayanamsha (all 6), every service-computed asset in
  `catalog_assets_all` (data AND service types, `has_writer` both ways).

Each TCI entry carries: `concept_id · canonical_name · aliases[] · layer · owning_asset ·
serving_tool + args · row_count_per_canonical_chart · is_chain_or_pattern · computed_globally
(bool) · honest_gap_ref (CR/EL if never computed)`.

**Invariant:** the TCI is generated by a script in CI, not hand-maintained. A new category that
lands without a TCI entry fails the build. *Nothing can hide, because the denominator is the corpus.*

**THE TCI MAY NEVER BE STUBBED (v2.1, red-team finding #1 — the highest-probability false-success
path in this campaign).** The TCI is the denominator of every Ω3 sum; a partial TCI makes
`served + accounted = 100%` trivially true, Ω7's dark-corpus report zero, and Ω8's floor coverage
green — the entire mandate passes on a corpus of 40 concepts instead of 800. Therefore:
- α's schema-map generator (C3) is **a Phase-0 deliverable, not a Phase-2 one** — it is mechanical
  and must exist before Ω1 starts.
- **TCI SANITY GATE (hard, blocking):** the generated TCI's distinct-`fact_category` count must be
  **≥ the count of distinct `fact_category` values in production**, asserted by an *independent*
  SQL query written by the Verifier, not by the generator. It must additionally cover ≥1 entry for
  every `bodha_mechanisms` class, every built dasha system, every varga, and every ayanamsha.
- If the sanity gate fails, **Lane Ω is BLOCKED, never stubbed** — γ parks and says so. The general
  §7.2 "build against the contract and stub it" rule **does not apply to Ω1**.

Artifact: `00_ARCHITECTURE/llm_consumption_audit/capability_map/TOTAL_CONCEPT_INVENTORY_v1_0.json`
Generator: `platform/scripts/census/generate_tci.ts` (nightly + pre-deploy).

### Ω2 — Domain relevance mapping, deliberately permissive

Every TCI entry is mapped to one or more domains (wealth, career, marriage/relationship, health,
spirituality, character, progeny, education, property, litigation, longevity, timing, remedial) by
these rules **in precedence order**:

1. **Classical linkage** — a citable rule ties the concept to the domain (`relevance: primary`).
2. **Structural derivation** — house/lord/kāraka/varga chains: e.g. anything touching the 2nd, 11th,
   5th or 9th lords, Dhana kārakas (Jupiter/Venus), D2/D11/Indu, or their dispositor closure is
   wealth (`relevance: structural`).
3. **Existing domain tags** in `bodha_msr_signals` / `bodha_convergence` (`relevance: tagged`).
4. **DEFAULT INCLUDE ON UNCERTAINTY** — if none of the above decides it, the concept enters the
   domain as `relevance: peripheral` rather than being excluded. *The native said "every remotely
   relevant"; ambiguity resolves toward inclusion, always.*

Only two escapes exist, both explicit and both auditable: `domain_agnostic: true` (pure metadata /
provenance rows) and `excluded: {domain, rule_id, reason}` (a NAMED rule excluded it — e.g.
`ga_medical_indications` from a wealth reading). **CI asserts 100% classification coverage: zero
unclassified TCI entries, zero unreasoned exclusions.**

Artifact: `capability_map/DOMAIN_RELEVANCE_MAP_v1_0.json`.

### Ω3 — The Completeness Contract (100%-accounted)

For any domain question, the response must satisfy, mechanically:

```
served + empty_for_this_chart + not_computed_globally + superseded_by_aggregate
      + excluded_by_named_rule  ==  100% of the domain's TCI slice
```

Every non-served concept carries a machine-readable reason code:
- `empty_for_this_chart` — computed globally, zero rows for this chart (honest negative);
- `not_computed_globally` — the honest gap, citing its EL/CR (e.g. sahams pre-β-D2);
- `superseded_by_aggregate` — a denser served surface already carries it, naming which;
- `excluded_by_named_rule` — Ω2's exclusion, naming the rule.

`unaccounted` is not a legal state. A response whose accounting does not sum to 100% **fails the
receipt gate** (Stream α's CI) and cannot ship. This is the mandate as a build invariant.

**Gate scoping (v2.1, red-team finding #4 — this gate could otherwise deadlock the whole run).**
α's K1 receipt gate runs on every merge for all three streams, and §10 forbids anyone from
renegotiating 100% downward. Without scoping, γ sitting at 97% at 04:00 would block α's and β's
merges too, with no agent holding authority to relieve it — a total stall requiring a human.
Therefore the C7 assertion is **allowlist-scoped**:
- γ maintains `ledgers/contracts/C7_ENFORCED_SCOPE.json` — a list of `{tool, domain}` pairs it
  declares ready. **Default: empty.**
- Inside the allowlist the gate is **hard-blocking**. Outside it the gate is **report-only**
  (findings logged to the run ledger, merges proceed).
- The gate is **warn-only in its entirety until `ledgers/contracts/C7.frozen` exists** (authorship
  dependency: α builds the gate, γ authors the invariant).
- The flagship domains (wealth + the second acceptance domain) MUST be in the allowlist before γ
  may signal complete. A γ that cannot get a domain to 100% parks it `PARKED-HONEST` and leaves it
  out of the allowlist — it never lowers the number, and it never blocks its sibling streams.

### Ω4 — Depth-default routing (fixing §0.2.B)

- **`intent_classify` default posture flips to `depth: deepdive`, `width: comprehensive`.**
  `standard` is no longer a default — it must be *earned* by positive narrow-question evidence.
- **Narrow-pointed classification requires ALL of:** a single named entity, a single named
  attribute, no interpretive/evaluative/predictive verb, and no domain word. ("What is my Moon sign"
  qualifies. "How is my Moon" does not — `how` is evaluative. "How is my wealth" does not.)
- **Confidence floor:** a classification below 0.5 routes to DEEP, never to standard. Uncertainty
  resolves toward depth. (Today "How is my wealth?" scores 0.2 and gets `standard` — inverted.)
- **The classifier must not be weaker than the fallback it replaced:** a regression suite of ≥60
  labelled questions (≥4 per domain × narrow/deep) asserts `intent_classify` ≥ `plan_retrieval`'s
  keyword fallback on every item. Any disagreement resolves to the deeper of the two.
- **SYMMETRIC PRECISION CRITERION (v2.1, red-team finding #7).** Every criterion above is passed by
  a degenerate classifier that returns `deepdive` for everything — which would destroy the one
  behaviour §0 explicitly preserves. Therefore the suite contains **≥15 labelled NARROW items, of
  which ≥90% must classify narrow**, alongside the deep-recall requirement. Both must pass.
- **The 60-question labelled set is FROZEN IN PHASE 0, before Ω4's builder is spawned**, and is
  committed read-only. A builder may not author the set that grades it.
- **Even a narrow answer carries `depth_available`** — the pointer to the full dossier.
- `entitlement` defaulting to `restricted` for the native's own charts is a defect on the same
  surface; resolve it in this lane (native charts → `native`).

### Ω5 — Pre-synthesis staging: the gather-then-compose gate

The mechanism that actually gets everything into the model before it speaks.

- **`dossier(domain, chart_id, budget_kb?, cursor?)`** serves the domain's *entire* TCI slice in
  **pages**, each page sized under the caller's per-response cap (Stream α's `budget_kb`).
- Every page carries: `page_n / pages_total`, `cursor`, `coverage_so_far` (Ω3 accounting to date),
  and **`synthesis_gate: BLOCKED | OPEN`**.
- `synthesis_gate` flips to `OPEN` only when the accumulated receipt shows 100% accounting (Ω3).
- The served **`reading_contract`** instructs the consumer, in the response itself: *do not compose
  until `synthesis_gate: OPEN`; the deliverable is the synthesis over the whole, not a narration of
  the parts.* This is EL-29's composition doctrine wired to EL-02's receipt as its gate.
- **THE GATE MUST BE STRUCTURAL, NOT HORTATORY (v2.1, red-team finding #12).** Prose in a payload
  cannot stop a consumer composing after page 1 — and "nothing forces execution" is precisely the
  defect §0.2.C diagnoses. Shipping an instruction-only gate would reproduce the very bug this lane
  exists to fix, while the receipt records it as solved. Therefore: **pages served before
  `synthesis_gate: OPEN` withhold the interpretive surfaces entirely** — no `verdict`, no
  `narration`, no ranked "top findings", no `reading_contract` prose beyond the gate instruction —
  serving data + accounting only. A premature composition is then visibly content-starved rather
  than plausibly complete. Additionally, `retrieval_receipts` records `composed_before_gate` where
  detectable, and K2 grades it.
- The receipt is filed **server-side** (`retrieval_receipts`) so consumption is measured, not hoped
  for — and so Ω7's dark-corpus report has data.
- **Density acceptance criterion (measured, not aspirational):** the full wealth slice of chart
  482012f1 must fit in **≤6 pages at `budget_kb` sized to a 25k-token client, and ≤2 pages at a
  200k-token client**, at 100% accounting. If it does not, the fix is *densification* (Stream α's
  pivot/provenance-once work), never truncation of content.

### Ω6 — Patterns, chains and mechanisms as first-class citizens

The native named these explicitly ("a single pattern, a single chain"). They are TCI entries with
`is_chain_or_pattern: true`, are **mandatory** members of every domain slice they touch, and the
dossier serves the *structures*, not merely their atoms:

all 10 `bodha_mechanisms` classes (convergent dispositor chains, dispositor cycles, house-lordship
cycles, yoga clusters, mutual reception, parivartana chains, stelliums, mutual aspects, aspect
triangles, graha-bhāva affliction) · CGM subgraphs and edges with centrality · full dispositor
closure to its final node · argala/virodha-argala webs · convergence domains · contradiction poles
and their adjudication · discovery/anomaly rows · retrodiction mechanisms · varga-ratification
divergences · sudarshana agreement · bhāvat-bhāvam amplifiers.

**Hard dependency:** this lane cannot deliver until Stream α fixes `bodha_mechanisms_get` (EL-37) —
today a `hard_floor: true` plan item is unreachable (§0.2.D). Contract published in Phase 0 (§7.2).

### Ω7 — The unknown-unknown killer (dark-corpus report)

A standing report, per domain: TCI entries that (a) exist, (b) are non-empty for the chart, and
(c) were NOT served across a defined answer corpus. **This is the direct measurement of the native's
~20% unknown-unknown, and its target is zero.** Ships in the morning report; any non-zero entry
becomes an automatic register item for the next campaign.

**The corpus must be a FROZEN REPLAY SET, not incidental run traffic (v2.1, red-team finding #13).**
`retrieval_receipts` is new in this run; computing the report over whatever the Verifier happened to
call — mostly `dossier` calls that by construction serve everything — makes the report read zero for
the wrong reason and ships an empty artifact as proof the unknown-unknown is solved. Therefore:
**Phase 0 freezes `ledgers/DARK_CORPUS_REPLAY_SET.json` — ≥20 questions per flagship domain spanning
naive, narrow and expert phrasings** — and the report is computed over a **fresh Phase-4 execution**
of that set, through the same sealed evaluator harness as Ω-Verification, never over run traffic.

### Ω8 — Floor reconciliation (the planner catches up to the TCI)

Every domain's compiled floor is regenerated **from** the TCI slice rather than hand-curated:
`ashtakavarga_scan` gains per-varga AV; `divisional_facts` gains every domain-relevant varga (wealth:
D2, D11, D9, D10, D60, Indu); `special_lagna_read` gains the full lagna + saham set; argala,
dispositor-closure, cross-ayanamsha, mechanism and chain primitives are added; every TCI concept in
the slice has a covering primitive or a named exclusion. **CI gate:** floor coverage of its domain's
TCI slice must be 100%-accounted, same rule as Ω3. This subsumes and completes EL-26.

### Ω — Verification (the campaign's flagship acceptance)

**THE SEALED EVALUATOR HARNESS (v2.1, red-team finding #3 — v2.0 had no defined consumer).**
"A naive question returns a complete reading" is meaningless without specifying *who asks*. A
Stream-Verifier holding this charter is the least naive consumer imaginable and can satisfy the
criterion by calling `dossier` directly and inspecting fields — testing the server, not the
routing-and-composition behaviour the mandate is about. Therefore **Phase 0 freezes a sealed
evaluator harness**, committed read-only before any Ω builder is spawned:

- **The consumer** is a FRESH sub-agent with the MCP tools and *nothing else* — a fixed system
  prompt containing **no charter text, no EL vocabulary, no concept names, no mention of dossier or
  Lane Ω**. It receives ONE user turn (e.g. "how is my wealth?") and its full transcript is captured.
- **The grading is mechanical**, not judgemental: the transcript is scored against a **frozen list of
  required `concept_id`s** drawn from the TCI's domain slice (frozen at Phase 0 from the then-current
  TCI, so the builder cannot shrink the target), with a **numeric pass threshold** and per-concept
  hit/miss. Partial mention does not count as a hit — the concept's *substance* must appear.
- **The Verifier reads the score. It never plays the consumer.** A Verifier that answers the
  question itself has invalidated the test.
- The same harness executes the Ω7 replay set (above) and the Ω4 routing suite.

1. A **naive** "how is my wealth?" through the sealed harness — no expert prompting — routes to
   `depth: deepdive` and returns,
   at 100% accounting, a reading that includes: per-varga AV, D2 **and** D11 **and** Indu Lagna,
   argala on 2/11, the full dispositor closure, every mechanism/chain the chart carries, sahams
   (post-β), special lagnas, cross-ayanamsha agreement scores, timing, remedies, contradictions
   with adjudication — composed after the gate opened, not during retrieval.
2. `dark_corpus_report(wealth, 482012f1)` = **zero** unserved non-empty concepts.
3. The session that produced this register (~25 calls, 20+ tools, client-side assembly) is
   reproduced in **≤3 calls** with strictly greater coverage.
4. Repeat on a **second domain** (career or marriage) and on the **second chart** (1c826d5a) —
   proving the mechanism is general, not wealth-tuned or native-tuned.
5. The 60-question routing suite passes: zero deep questions misrouted to standard.

---

## §3 — Root-cause map (the Fable pass over EL-01..61)

Seven clusters. RC-4 is now Lane Ω and Stream γ's spine.

- **RC-1 · Envelope integrity.** §N.6 machinery exists but: fixed-cost generic preambles outrank
  entity payloads (no hardFloor); completeness receipts computed pre-trim and never reconciled
  (✓ over empty); the last-resort string truncator eats honesty fields; enforcement non-uniform
  (68–118KB tools unclamped while a light tool starves); no client budget negotiation; EAV verbose
  by default. → EL-36, 42, 43, 46, 11, 12, 28. **Stream α.**
- **RC-2 · Broken / wrong surfaces.** SQL param-count bug killing the mechanisms layer; facet
  defaults sized for internal dumps; tropical-only ephemeris with tropical-derived nakshatra; mixed
  house-index semantics; null varga houses; a uniform 0.875 placeholder served as fact; two rank
  vocabularies; mixed identifiers. → EL-37, 38, 39, 30, 47, 40, 59, 32. **α (serving) + β (data).**
- **RC-3 · Honesty machinery gaps.** Requested categories dropped without receipts; no concept
  resolver so empty-probe ≠ absent is undecidable; no schema map; no serving-time claim-checker;
  coverage claims without build-coverage attestation. → EL-41, 08, 34, 21, 07, 60b. **α.**
- **RC-4 · Consumption & composition — THE FLAGSHIP.** Twice consumer-verified and now
  planner-verified (§0.2): the corpus is under-DISCOVERED, under-STEERED, under-CONSUMED, composed
  client-side. → EL-01,02,03,04,05,06,14,23,26,27,29,31,44,45,56,61 + **Lane Ω**. **γ.**
- **RC-5 · Deterministic-computation gaps.** Sahams; per-dosha bhanga; muhūrta personal-baseline /
  target-graha / horā; direct panchāṅga; arbitrary-varga snapshots; active-dashas face; remedy
  contraindication verdicts and full catalog; corpus OCR; varga-weighted salience; contradiction
  domain filter. → EL-19, 18, 50, 49, 48, 33, 51, 52, 35, 55, 57. **β + γ.**
- **RC-6 · Calibration-loop closure.** Elections unfilable; LEL empty; stale open predictions;
  build-state truthfulness; ratification debt; timing residuals + CR-131. → EL-53, 54, 58, 24, 25,
  15, 17. **γ + β.**
- **RC-7 · Verification instrumentation.** No call-every-tool smoke gate (a tool was 100% down and
  nobody knew); no uniform-value screen; no budget census; no consumption metric; two-pass grading
  not yet law; four instrumentation tracks uncaptured; precision-class claims unchecked. → EL-04,
  09, 10, 21, 22, 23, 60. **α (serving gates) + γ (battery/consumption).**

**Couplings every stream must respect:**
- EL-27 ↔ EL-56 are ONE mechanism (agreement-scoring); a naive dedup destroys the variation signal.
- Ω6 blocks on α's EL-37 fix; Ω5 blocks on α's `budget_kb`; Ω8 blocks on α's schema map.
- EL-30 / EL-47 / EL-38's house semantics settle ONCE, in β, with one rebuild.
- α's EL-36 fix must land before α's budget-census gate locks numbers in.

---

## §4 — Stream definitions, lane assignment, and file-ownership manifests

**Ownership rule:** a stream may edit only files matching its manifest. A genuine cross-manifest need
goes to the Meta-Conductor, which either grants a scoped exception (recorded) or serialises the two
lanes. **No stream ever edits another's files opportunistically.**

### STREAM α — SATYA (Truth & Envelope)

**Lanes:** A (envelope/budget/receipt-truth) · B (broken surfaces) · H (discovery, schema map,
entity faces, varga snapshots) · K1 (serving-side CI gates).

**Owns:**
```
platform-mcp/src/lib/**                       (response_budget.ts, completeness_receipt.ts, …)
platform-mcp/src/tools/**                     EXCEPT: tools/vidhi/**, tools/muhurta_finder.ts,
                                              tools/dossier.ts and any NEW γ-authored tool
platform-mcp/src/resources/**                 EXCEPT: resources/vidhi/**
platform/src/lib/retrieval/registry/layers/L0_brahmagyan/**   (serving leg only; sidecar route = β)
platform/src/lib/retrieval/registry/layers/L1_ganita/**
platform/src/lib/retrieval/registry/layers/L2_bodha/**        (incl. graha_portrait — γ CONSUMES it
                                              via its exported handler, never edits it)
platform/src/lib/retrieval/registry/layers/register_d*.ts     EXCEPT: register_d8_assess_domain.ts
platform/src/lib/retrieval/registry/descriptor_defaults.ts, envelope.ts, catalog.ts
platform/src/lib/retrieval/address_resolver.ts
.github/workflows/elev-serving-gates.yml      (new)
platform/scripts/census/schema_map*.ts        (α authors; the TCI generator itself is γ's — C3)
```
**Deploys:** `platform` (auto on main) + `platform-mcp` (Cloud Run `amjis-mcp`).

### STREAM β — GAṆITA (Compute & Corpus)

**Lanes:** D (indexing/writer integrity + chart-scoped rebuild) · D2 (sahams + bhanga) ·
C-sidecar (sidereal ephemeris route + panchāṅga compute) · G (remedy engine + corpus OCR) ·
T (timing residuals, gochara env, sweep completion).

**Owns:**
```
platform/python-sidecar/**                    (writers, routes, pipeline, brahmagyan/**)
platform/migrations/**                        (NEW additive migrations only)
platform/src/lib/ganita/**                    (facts_store, forensic_render — writer-adjacent)
scripts/clean_*.py, platform/scripts/audit/**, platform/scripts/bootstrap/**
00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_*.md
```
**Deploys:** `amjis-sidecar` (platform/cloudbuild-sidecar.yaml) · pipeline job (root
cloudbuild.yaml) · prod DB chart-scoped rebuilds via the FROZEN orchestrator.

### STREAM γ — PŪRṆA (Depth & Intelligence)

**Lanes:** **Ω (total consumption — §2)** · I (planner coverage, cross-ayanamsha, dossier,
composition) · E (assessors, verdict layer, ranking, rank vocabulary) · F (muhūrta intelligence,
active-dashas, election filing) · J (calibration lifecycle, LEL intake, ratification packet) ·
K2 (consumption metric + standing battery upgrades).

**Owns:**
```
platform-mcp/src/resources/vidhi/**           (plan_builder, scope_resolver, registry_data, cr_status)
platform-mcp/src/prompts/vidhi_plan.ts
platform-mcp/src/tools/vidhi/**  +  NEW: tools/dossier.ts, tools/intent_classify*.ts
platform-mcp/src/tools/muhurta_finder.ts
platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts
platform/src/lib/retrieval/registry/layers/L3_kala/**, L5_mimamsa/**
platform/src/lib/retrieval/ranking/**         (priors_config.ts)
platform/src/lib/vidhi/**                     (registry_data, cr_status)
platform/scripts/answer_eval.ts
platform/scripts/census/generate_tci.ts       (γ-owned; consumes α's schema_map output per C3)
evals/**, bench/**
00_ARCHITECTURE/llm_consumption_audit/capability_map/**
.github/workflows/elev-depth-gates.yml        (new)
```
**Deploys:** `platform` + `platform-mcp`.

**Shared, edited by NOBODY without Meta-Conductor grant:** `CLAUDE.md`, `CURRENT_STATE_v1_0.md`,
`SESSION_LOG.md`, `CLAUDECODE_BRIEF.md`, the ELEVATION_REGISTER. All close-edits are made by the
Meta-Conductor at Phase 4, once, atomically.

---

## §5 — Grounded defect dossiers

*Every lane runs the same internal gate sequence:* **G0 reproduce** against PROD (not reproducible →
`NOT-REPRODUCED` + probe evidence, stop, no code churn) → **G1 build** in worktree → **G2 test**
(unit + typecheck + regression additions) → **G3 PR → merge → deploy** → **G4 Verifier confirms
against live production, both canonical charts.**
Canonical charts: `482012f1-710e-4a25-994a-93821f5871aa` (primary) and `1c826d5a` (chart-agnostic
check). Never write chart `362f9f17-…` (dead phantom).

### α.A [OPUS] — Envelope & Truth · EL-36, 42, 43, 46, 11, 12, 28

*Evidence (live, this session).* `graha_portrait` platform handler computes its §28.6 completeness
receipt at `L2_bodha/graha_portrait.ts` ~L377–385 — **pre-trim**. The MCP layer prepends a generic
`orientation_context` digest (9,946 MSR signals; entity profiles for SATURN, JUPITER, BHAVA_12,
KETU — *not one Venus row*), then `finalizeMcpBudget` (`platform-mcp/src/lib/response_budget.ts`)
runs: `autoDetectTrimmableSections` declares sections with **no `hardFloor`**, so PASS 2 (L198–203)
floors the entity arrays to 0 while the preamble survives; `truncateLongStringsInPlace` (L365–395)
then cuts `verdict.narration` mid-word; the trim_report trimmed **itself** 6→1 (L310–318).
Live repro: Venus, `include:["position","dignity"]` → `position.rows:[] count:9`;
dignity arrays `[] count:56`; receipt `✓ ✓ 2/2`; `judgment_flags: []`. **65 rows located, 0 served,
receipt says complete.** Separately `ganita_chart_facts_get` 68–84KB, `assess_wealth` 118KB.

*Fix:* (1) **Priority inversion** — entity payload sections declare `hardFloor:true` with real
minKeeps; `orientation_context` becomes first-trimmed (minKeep 0) and `include`-gated on
entity-scoped tools. (2) **Receipt truth** — reconcile the receipt against the post-trim payload; a
section trimmed to zero flips ✓ → **`trimmed_empty`** plus a mandatory `judgment_flags` entry and a
drill pointer; §28.6 gains that fourth state; "✓ over an empty array" becomes a CI-impossible state.
(3) **Honesty-field immunity** — `judgment_flags`, `empty_reason`, `completeness`, `epistemic`,
`coverage`, `trim_report`, `reading_contract` are exempt from string-truncation and PASS-2 zeroing;
a response that cannot fit them sheds rows instead. (4) **Uniform enforcement** — one budget path
for every registered tool with a per-tool `maxKb` ledger in `descriptor_defaults.ts`; explicit
sections + pagination for the heavy tools; default ceiling sized to the smallest real client
(~25k tokens). (5) **`budget_kb` request parameter** (EL-12) honored by the packer + documented
client profiles (Claude Code 200k / 1M / Cowork / product UI) — **this parameter is the interface
Ω5 pages against, and must be published in Phase 0** (§7.2). (6) **Pivot-first defaults** (EL-43):
compact pivoted rows, provenance envelope ONCE per response, symbol dictionary once per session —
*and every byte saved is spent on more content, per §0.3.*

*Verify:* Venus portrait serves ≥9 position + operative dignity rows within budget, narration
intact, receipt truthful; `verbosity:'concise'` sheds preamble not payload; `budget_kb:8` returns an
honest layered digest, never an error; `assess_wealth` within ceiling; full-estate census green;
both charts.

### α.B — Broken serving surfaces · EL-37, 38, 41, 47-serving, 13, +CURRENT_STATE B-1

**EL-37 — root cause FOUND.** `L2_bodha/query_mechanisms.ts`: the handler builds `where` from
filter params (L113–123), then pushes the chain-circuit class array as `classPriorityParam`
into the **same** `params` array (L128–129). `rowsSql`/`facetSql` reference `$N`; the COUNT query
(L159) is `SELECT COUNT(*) … WHERE ${where}` — referencing only filter placeholders — but is
executed with the **full** `params`. With the MCP's default `ayanamsha_id` present: 3 supplied,
2 required. All three run in one `Promise.all`, so the tool 500s on every call.
*Fix:* snapshot `const filterParams = [...params]` **before** the class-array push; run the count
(and any where-only SQL) with `filterParams`. Regression test calling the handler with and without
each filter combination. **Priority: this is a `hard_floor: true` plan item (§0.2.D) and blocks Ω6 —
ship it in α's first merge.**

**EL-38.** `L1_ganita/get_argala.ts` is sane (default 500, cap 2000); the **MCP faceted instrument's**
`limit` default of 25000 over a per-varga × per-sign × per-offset matrix is what times out. Fix:
per-facet sane defaults (≤500) + facet counts + pagination; **serve argala resolved to
houses-from-lagna** (`argala_on_house`, 1-indexed per β's convention ruling) with the raw matrix
behind `shape=matrix`. Sampled rows are all `fact_value_num: 0` — hand the zeros question to β
(a 9-graha Aries-lagna chart cannot have all-zero argala); until β adjudicates, disclose
`all_zero: true` distinctly from unserved.

**EL-41 + B-1.** Every multi-category tool returns a per-requested-category receipt
`{category, status: served|empty_with_reason|unknown_category, count, empty_reason?,
alias_suggestion?}`. No requested category may vanish from the response shape. Apply to the
special-lagnas tool (saham/sensitive_point silently dropped — live repro), to
`phala_predictive_anchors_get` (CURRENT_STATE v6.41 B-1 silent-empty), then sweep every tool taking
`categories[]`. **This receipt shape is Ω3's per-concept accounting primitive — publish it in
Phase 0** (§7.2).

**EL-47 serving leg.** Divisional serving computes `house_from_varga_lagna` server-side (varga lagna
sign → count to graha sign), 1-indexed, convention-labelled. Persistence is β.
**EL-13.** `catalog_version` / `tools_changed_at` on server-info + documented client-restart
limitation; emit `notifications/tools/list_changed` if the SDK supports it.

*Verify:* mechanisms returns rows (or honest empty) on both charts; "argala on H2/H11" answered in
one bounded call; a 3-category call returns 3 receipts; divisional rows carry houses.

### α.H — Discovery, steering, entity faces · EL-31, 48, 34, 08, 07

(1) **`get_database_schema` + `concept_locate`** — one mechanically-generated substrate: every
`fact_category × fact_subjects × fact_keys` with one-line meanings, plus concept aliases seeded from
the Phase-0.7 census matrix (Gulika/Maandi → `sensitive_point_gulika_mandi`, sphuta, panchanga,
mangal). Paginated — no 2000-row alphabetical truncation. **This generator is the seed of Ω1's TCI;
α scaffolds it, γ extends it — contract in Phase 0.** Census-vs-alias CI regression: a new category
without aliases fails.
(2) **Absence Protocol (EL-07):** "not in your data" phrasing requires a concept-resolver MISS; a
category-probe empty must serve *"not found in what I queried"* plus the resolver's suggestion.
Lint over served strings in K1.
(3) **Entity faces (EL-31):** canonical `query_planet(name)` / `query_house(n)` returning ONE
assembled object (sign, house, nakshatra+pada, dignity chain, shadbala, avasthas, aspects in/out,
functional nature, yogas, dispositor); EAV tool descriptions steer to them; `tool_search` ranks
assembled faces above raw EAV for entity-shaped queries.
(4) **EL-48:** `chart_snapshot` gains `vargas: ["D2","D10","D11", …]`, assembled server-side,
budget-layered.

### α.K1 — Serving CI gates · EL-09(part), 21-v1, 60b + RC-7

Built **first** (Phase 0/1) because every stream's Verifier runs on them:
1. **Smoke gate** — call EVERY registered MCP tool with minimal valid args on 482012f1; any
   500/hang fails. *(EL-37 would have been caught on day one.)* Nightly + pre-deploy.
2. **Budget census gate** — worst-case response per tool ≤ its declared ceiling, both charts.
3. **Receipt gate** — per-category receipts present; ✓-over-empty impossible; **Ω3's 100%-accounting
   assertion once γ publishes it**.
4. **Absence-phrasing lint** — ontological-absence claims in served strings must trace to a resolver
   miss.
5. **EL-21 v1 claim-checker** — absence claims + receipt-vs-payload consistency as a response
   post-processor. Phase-2 (phase/timing claim verification against ganita surfaces) is *designed*
   (spec doc) and parked if the window tightens.
6. **EL-60b** — build-coverage attestation on coverage claims (`sweep_coverage: {substeps: n/m,
   span}`) so an honest empty and an unrun sweep are distinguishable.

### β.D [OPUS] — Writer & data integrity + rebuild · EL-30, 40, 47-writer, 38-data

*Evidence.* Arudha `house_d1` behaves 0-indexed under a 1-indexed name: A1 `house_d1=9`
sign=Capricorn (true house from Aries lagna = 10); A7 `house_d1=10` Aquarius (true 11); **A10
`house_d1=12` sign=Aries longitude=0° fits NEITHER convention** → probable cusp/wraparound defect.

*Sequence (internally serial):*
1. **Audit** — mechanical scan of every fact_category carrying a house-semantic field (writer emit
   paths under `python-sidecar/**` + sampled prod rows) → convention table: category × field ×
   observed convention × evidence. The A10/0° anomaly gets an explicit derivation check.
2. **Ruling** — ONE convention: houses are 1–12 from the (varga-appropriate) lagna; signs are 1–12
   Aries-origin; a field named `house_*` may never hold a sign index. Published to α and γ in
   Phase 0 (§7.2) and enforced by α.K1's convention gate.
3. **Writer fixes** — arudha first; then EL-47 (divisional writers persist
   `house_from_varga_lagna`); then **EL-40**: locate the `composite_dispositor_strength` producer
   (`bo_upaya.py` *consumes* it for remedy resonance — EL-59's bogus "rank 5" flows from here);
   audit the formula — real computation → fix and document the formula in `citation_ref`;
   placeholder → implement the documented convergence weight or **withdraw the category and serve
   `null` with reason** (B.10: no placeholder shipped as fact). Same pass screens ALL numeric
   per-entity fields for distinct-count = 1 (becomes α.K1's degenerate-value screen).
4. **Chart-scoped rebuild** — delete-then-insert per §N.3, both canonical charts, via the FROZEN
   orchestrator (new/fixed writers YES; contract changes NO). Dispatch pattern: the existing
   `platform/scripts/dispatch_*_rebuild_job.py` family (run as `python -m scripts.dispatch_<name>`
   from `platform/`; dispatches the Cloud Run job and prints the run_id). Then **downstream
   refresh**: any L2+ signal citing corrected facts (`constituent_facts_array` per §N.5) rebuilt or
   flagged; run the MSR drift check from `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`.
5. **ESTATE SAFETY (v2.1, red-team finding #2 — v2.0 would have left every non-canonical chart
   silently wrong).** β rules ONE convention and rebuilds only the two canonical charts, while α's
   serving-side gate then enforces that convention for **all** charts. Every other prod chart still
   holds legacy rows, now read by code assuming the new semantics — wrong houses served estate-wide,
   undetectable because G4 checks only two charts. **Mandatory mitigation, pick one and record which:**
   (a) persist a per-row `house_convention` tag and have serving NORMALISE BY TAG so legacy rows keep
   reading correctly; or (b) ship the serving-side convention change behind a flag that is ON only
   for rebuilt charts. Either way, **add one non-canonical third chart to every convention G4 check**
   (`catalog_charts_list` → pick any chart that is neither canonical) to prove the estate is safe.
   The same rule applies to EL-47's divisional houses and EL-40's withdrawal.
6. **EL-38 data leg** — adjudicate the all-zero argala matrix; fix the writer and rebuild if wrong.

*Verify:* A1→10, A7→11, A10 resolved with documented derivation; ≥3 distinct dispositor-strength
values across 9 grahas **or** the category is withdrawn-with-reason; divisional houses spot-checked
against sign arithmetic; **FORENSIC 7/7 still PASS**; MSR resolution clean; both charts.

### β.D2 [OPUS] — Gaṇita completions · EL-19, 18

New deterministic writer math; **citations mandatory** (B.3/B.10); Opus authors; no invention.
**Sahams (EL-19):** the classical Tājaka set (Puṇya, Vidyā, Yaśas, Mitra, Māhātmya, Āśā, Samartha,
Bhrātṛ, Gaurava, Pitṛ, Mātṛ, Putra, Āyus, Karma, Roga, Kali, **Dhana** …) from
Tājakanīlakaṇṭhī, day/night formula variants included, written to the `saham` fact_category the
census already probes. **Bhanga (EL-18):** per-dosha cancellation beyond NBRY for the well-attested
set only — Kuja/Manglik cancellation conditions, Kemadruma bhaṅga, Śakaṭa bhaṅga at minimum — each
rule citing chapter-verse (BPHS / Phaladīpikā / Jātaka Pārijāta); doshas without attestable rules
KEEP the honest `bhanga_na_reason`. Both rebuilt chart-scoped, both charts, and served through the
existing surfaces. *Verify:* saham longitudes recompute exactly from L1 inputs; every bhanga verdict
traces to its cited rule; α's EL-41 saham receipt flips `empty_with_reason` → `served`.

### β.C — Sidereal ephemeris & panchāṅga · EL-39, 49

*Evidence.* `L0_brahmagyan/query_planet_position.ts` proxies the sidecar and serves
`ayanamsha_id: "tropical"`; its own description instructs clients to *"subtract Lahiri ayanamsha to
get sidereal"* — institutionalised client-side arithmetic, the exact B.10 exposure. Live: Venus
2026-08-15 → `tropical_longitude: 188.565`, `sign_number: 7` (tropical Libra); sidereal Lahiri =
Virgo (the debilitation that decided the muhūrta reading). **`nakshatra_number: 15` is derived from
the tropical longitude** — wrong under every supported ayanamsha, served unlabelled.
*Fix:* `ayanamsha_id` param defaulting to `lahiri_chitrapaksha` (sidereal-first; `tropical` allowed
explicitly); the sidecar route applies it and returns sidereal longitude/sign/degree/nakshatra/pada
with `tropical_longitude` as a labelled extra; under `tropical`, suppress or explicitly label
nakshatra — never a bare tropical-derived nakshatra. Audit every ephemeris-backed tool for the same
leak (`ref_planet_transit_get`, `ref_aspects_at_time_get`, `ref_ephemeris_year_get`, retrograde).
**EL-49:** first-class `panchanga_get(date, location?)` over `panchanga_daily` + sidecar compute for
missing limbs: five aṅgas + **karaṇa + sunrise/sunset + horā boundaries**, IST-anchored explicit
timestamps. *Verify:* Venus 2026-08-15 → Virgo/Lahiri with correct sidereal nakshatra; **the
birth-date call reproduces the 7 FORENSIC panchāṅga anchors for 1984-02-05 Bhubaneswar (Shukla
Tritiya / Ravivāra / Śiva / Garaja) — a free absolute correctness oracle**; Sep-18-2026 panchāṅga in
one call with sunrise + horā table.

### β.G — Remedies & corpus · EL-51, 52, 35 (supersedes CURRENT_STATE A-5 accept-as-dark)

Full 25-item catalog served chart-scoped with per-class inclusion/exclusion **reasons**; gemstone
contraindication (maraka lordship) computed as a **deterministic verdict per gemstone with
citation** — never prose the consumer must interpret (safety-bearing); `associated_doshas_array` +
INR cost backfilled where catalog data exists, else explicit honest-gap disclosure; **corpus
structuring** — verse ref · cleaned Devanagari · clean translation · tagged prescription, OCR-
confidence scored, low-confidence rows **flagged, never fabricated** — bounded overnight to the
~200 highest-traffic rows (remedy-linked + rule-search top hits), starting with BPHS Ch.47
Venus-maraka; full-corpus pass parked as named follow-up. **EL-35:** framework-tagged one-line
`astrological_significance` on esoteric served fields (22nd drekkāṇa, tāra bala, KP sublords),
sourced from `ref_*` tables and tagged Parāśarī/Jaimini/KP/Tājaka. *Native-Proxy records the A-5
supersession for morning ratification.*

### β.T — Timing residuals · EL-15, 17, CR-131, gochara env [bounded]

With the prod credentials that were the exact blocker in CURRENT_STATE v6.41: fix the gochara
serving tools' `DATABASE_URL` gap; resume `ka_gochara_sweep` for 482012f1 (165/300) to completion or
to a characterised honest failure (the ~6x-not-600x resume reality is known — budget wall-clock
accordingly; if projected completion exceeds the window, dispatch, monitor, record state, park with
an ETA); **EL-17:** re-verify CR-66 phala domain anchors + CR-37 activation dating LIVE *after* β.D's
rebuild; pull the two PRE_DARPANA v2.0 Stage-2 residuals into the register as explicit items.
**Out:** EL-16 / D-6 GOCHARA-SWEEP-2.0 build (staged, native review pending) and the Darpana S3
re-run itself (native-attended). This lane *unblocks* both; it does not perform them. Note that
CR-131 closure directly un-darkens 3 of the 4 dark items in every wealth plan (§0.2.E).

### γ.I [OPUS] — Planner coverage, cross-ayanamsha, dossier, composition · EL-01–06, 14, 23, 26, 27, 29, 56, 61

Executes **on top of Lane Ω's substrate** (§2). Specifics beyond Ω:
- **EL-26 planner-coverage audit** → completed by Ω8 (floors regenerated from the TCI). The verified
  first fixes: a `varga_ashtakavarga` primitive (today's only AV primitive is natal-hardcoded), and
  a dispositor-closure primitive (absent from the wealth floor entirely).
- **EL-27+56 — one mechanism:** a `cross_ayanamsha_variation` primitive family computing
  dignity/vargottama/house-shift deltas across the 6 ayanamshas; **`ayanamsha_agreement: n/6` served
  as a confidence field on each finding**; family-collapse of duplicate discoveries by extending the
  E-6 `family_aggregation` key to include ayanamsha (so agreement compresses, disagreement
  surfaces as a rarity signal). The planner gains ayanamsha as an expressible axis; KP floors default
  to krishnamurti reads.
- **EL-61 `dossier`** — Ω5's paging engine, orchestrating deterministically in-process over existing
  handlers (the `graha_portrait` pattern). **No generative synthesis in the serving path** (B.10).
- **EL-29 composition doctrine** — the served reading form: gestalt/orientation → promise → evidence
  chains → tensions and their adjudication → timing → guidance; emitted as `reading_contract`;
  gated by Ω5's `synthesis_gate`.
- **EL-05 volunteering** — the chart's own top-N laksana/gestalt findings are a mandatory dossier
  section, served unprompted to naive questions.

### γ.E — Assessors, verdict, ranking · EL-44, 45, 55, 57, 59, 20, 32

`register_d8_assess_domain.ts`: (1) **verdict layer** — 3–5 plain-language sentences, every clause
carrying fact_ids, composed by a deterministic template over graded terms (not a generative call);
(2) investigate `composite_score: null` on top signals (uncomputed vs trimmed) and fix; humanise
machine-key text at serve time (`Saturn_in_H7` → "Saturn in the 7th house") via one shared formatter
that is also **EL-32's canonical-output pass** (full uppercase names on OUTPUT, aliases accepted on
INPUT, naming-governance gate extended to served identifiers); dedupe identical lens blocks.
(3) **EL-45** — the `varga_analysis` stub is replaced: `assess_wealth` consumes D2/D11/Indu/per-varga
AV directly. Rule, CI-asserted against Ω2: **no domain assessor may ship a "see other tool" stub for
a layer classical to its own domain.** (4) **EL-55** — a documented varga-weight term in
`ranking/priors_config.ts` (śoḍaśavarga hierarchy; classical viṁśopaka weights as the cited basis),
priors version-bumped, surfaced in `ranking_basis`. (5) **EL-57** — domain filter on the
contradiction surface + honest "no contradictions in this domain" empty. (6) **EL-59/20** — ONE rank
vocabulary: every served rank carries `rank_basis` + population size; arudha/UL (CR-61) and
nakshatra-semantic (CR-64) salience get documented deterministic formulas or ship explicitly
unranked. *No fabricated weights, ever.*

### γ.F [OPUS] — Muhūrta & elections · EL-50, 33, 53

(a) `activity_type` taxonomy extended with `spiritual_initiation`, `remedial_ritual`, `japa_start`,
each with cited rule sets; (b) **the native's own tāra/chandra bala baselines joined** — an adverse
tārā (Vadha/Pratyak) for this Moon **disqualifies or hard-flags** a window, never a silent top rank
(regression: the Aug-26–28 Vadha-tārā window must rank bottom or carry the flag); (c) **`target_graha`
parameter** — windows check the target's transit dignity/combustion/retrogression via β.C's sidereal
service (Venus-debilitated-all-August must surface on every August window for a Venus election);
(d) horā/sub-day resolution with IST-anchored day-explicit timestamps. **EL-33:** first-class
`active_dashas(date|today)` returning L1/L2/L3 lords + exact bounds across **all** built dasha
systems (DR-14). **EL-53:** election output gains `file_as_prediction: true` writing a prospective
row (elected window, predicted quality, scoring factors) closable via `mimamsa_outcome_record` —
elections become the fastest-cycling falsifiable evidence stream the instrument has.

### γ.J — Calibration lifecycle & packets · EL-58, 54, 25, 24

(1) **EL-58** prediction-lifecycle sweep: rows past their window auto-match against LEL; with LEL
empty they move to **`lapsed_unobserved`** (itself calibration data); the 2011-window-open-in-2026
class closes; runs at build-close and on schedule. (2) **EL-54** guided LEL intake surface —
a served checklist of the 3–5 event types retrodiction needs per domain, with an ingest path that
**validates but never invents**; delivered as a morning-ready packet. (3) **EL-25** ratification
packet — every pending item (NATIVE_PROXY_LEDGER through D-4b, battery stamps, Phase-0.7 pin, this
run's proxy ledger) with a recommended disposition each. (4) **EL-24 (bounded)** — `build_run` rows
carry substep denominator + dispatched scope legibly; reaper/self-heal for orphaned runs if the
SARVA-SIDDHI affordance is cheap; **cockpit UI work is out of scope** beyond data fields.
(5) Verify CURRENT_STATE B-2: the Sat-Jupiter Apr–Aug 2027 standing-prediction claim either reaches
a live surface or the reason it cannot is recorded.

### γ.K2 — Consumption metric & battery · EL-04, 10, 22, 23, 06, 09, 60a

Consumption ratio + **Ω3 accounting** + volunteered-findings count as first-class grading dimensions;
**two-pass grading (grader + DB-verifying auditor) codified as LAW** in the battery spec (EL-10);
the four instrumentation tracks (experience, I1–I5, V1–V5, RE1–RE5) captured by the harness (EL-22);
naive-vs-expert benchmark pairs for ≥2 domains (EL-05 n=1 → n≥2); varga-depth probe (EL-06); a
classical-attribution table for karaka/gloss claims (Sun = naisargika soul-kāraka, etc.) checked over
served prose (EL-09, bounded to the register's known instances + ~20 core attributions);
**EL-60a** `reading_notes_get` auto-accretion per domain per session.

---

## §6 — Per-stream swarm roster

**Global (Meta layer, spawned once):**

| Role | Model | Mandate |
|---|---|---|
| **Meta-Conductor** | Opus | Runs Phase 0; spawns the three Stream-Conductors; owns the merge queue, deploy lock, overflow queue, cross-stream arbitration, and the morning report. Writes no feature code. |
| **Native-Proxy** | Opus | §10. Answers every question that would otherwise go to the human, for all three streams. One ledger. |
| **Goal-Keeper** | Sonnet | Watches all three streams against §0/§1; flags scope drift, gold-plating, wrong-problem work; can redirect via a Stream-Conductor. |
| **Integration-Verifier** | Opus | Owns cross-stream correctness: after every merge to main, runs the full smoke + census + regression battery on the integrated head. Distinct from the stream Verifiers. |

**Per stream (×3, identical shape):**

| Role | Model | Mandate |
|---|---|---|
| **Stream-Conductor** | Opus | Owns its lane DAG, worktrees, branches, PRs, its deploy requests to the Meta-Conductor's lock, and its stream ledger. |
| **Lane builders** (3–5 concurrent) | Sonnet, or Opus on `[OPUS]` lanes | One per lane, own worktree, own branch, builds only files in the stream manifest. |
| **Stream-Verifier** | Opus | Independent and adversarial. Owns G0 baselines and G4 confirmations for its stream. **Never verifies code it wrote — it writes none.** |
| **Test-runner** | Sonnet | Mechanical: unit runs, typecheck, smoke/census scripts, probe replays, evidence capture. Keeps Opus verification tokens on judgment, not plumbing. |

**Peak concurrency ≈ 4 + 3×(1 conductor + 4 builders + 1 verifier + 1 runner) = ~25 agents.**

---

## §7 — Phase 0, interface contracts, and the merge/deploy protocol

### §7.1 — Phase 0 (serial, ~45 min, Meta-Conductor, runs ONCE before any fan-out)

1. Run-start snapshot: `git tag elev-v2-run-start` + DB snapshot.
2. Cut the three stream integration branches: `elev/alpha`, `elev/beta`, `elev/gamma` off `main`.
3. **Verifier baseline capture** — the full repro battery (every §5 recipe + the register's own
   corroborated probes + the §0.2 depth probes) against PROD → `ledgers/ELEVATION_V2_BASELINE.md`
   with raw payloads. **No fix may merge before its baseline exists** (before/after must be provable).
4. **Publish the interface contracts (§7.2)** — the single mechanism that lets three streams build
   in parallel without blocking on each other.
5. Scaffold the run ledgers and the shared evidence directory.
6. Spawn the three Stream-Conductors.

### §7.2 — Interface contracts (published Phase 0, frozen for the run)

Each is a TypeScript type + a one-page spec committed to `main` in Phase 0, so a consuming stream
builds against the *contract* while the owning stream builds the *implementation*.

| Contract | Owner | Consumers | Content |
|---|---|---|---|
| **C1 `budget_kb`** | α | γ (Ω5 paging) | Request param name/semantics, response fields `page_n/pages_total/cursor`, per-tool ceiling ledger shape. |
| **C2 category receipt** | α | γ (Ω3), β | `{category, status, count, empty_reason?, alias_suggestion?}` — Ω3's per-concept accounting primitive. |
| **C3 schema-map/TCI seed** | α (generator scaffold) | γ (Ω1 extends it) | Output JSON shape for `fact_category × fact_subjects × fact_keys` + alias table. |
| **C4 house/sign convention** | β | α, γ | The 1–12-from-lagna ruling + field-naming rule; α.K1 enforces it. |
| **C5 sidereal ephemeris** | β | γ (F target-graha checks) | `ayanamsha_id` param + sidereal response shape. |
| **C6 mechanisms availability** | α (EL-37 fix) | γ (Ω6) | Row shape + the guarantee the tool returns 200. **α ships this in its FIRST merge.** |
| **C7 Ω3 accounting assertion** | γ | α (K1 receipt gate) | The 100%-accounting invariant α's CI asserts. Warn-only until `C7.frozen`; allowlist-scoped (§2 Ω3). |
| **C8 handler output shape** | α | γ (dossier orchestration) | **(v2.1, finding #14)** Exported registry-handler signature + post-trim envelope shape: the four receipt states, the pivoted-row shape, the immune honesty-field set. γ's `dossier` orchestrates α's handlers in-process while α rewrites their output all night; without this contract γ builds against a moving target and breaks at DEPLOY-3. Any α change to it is a recorded contract AMENDMENT, not a silent edit. |

**Rule:** a stream blocked on another's *implementation* builds against the contract and stubs the
dependency; it never waits idle and never edits the other's files.
**Exception:** Ω1's TCI may NEVER be stubbed (§2 Ω1) — it blocks instead.

**Contract ownership and timing (v2.1, finding #7 — v2.0's Phase-0 gate was unsatisfiable).**
Phase 0 can only freeze contracts α actually owns. Ownership and deadlines:
- **Phase 0, α-owned and frozen before β/γ start: C1, C2, C3, C6, C8.**
- **β-owned, deadline T0+3h: C4 (house/sign convention), C5 (sidereal shape).**
- **γ-owned, deadline T0+4h: C7 (accounting invariant).**
All live in `ledgers/contracts/CONTRACT_STATUS.md`, one row each:
`contract · owner · status(DRAFT|FROZEN|AMENDED) · path · sha · timestamp`. **Consumers re-read this
file at every phase boundary; an `AMENDED` row is a mandatory rework item, not an advisory.**

### §7.3 — Git, branches, PRs, GitHub

- Lane worktree branches: `elev/<stream>/<lane>-<slug>` (e.g. `elev/alpha/A-envelope`), cut off the
  stream integration branch.
- Lane → **PR into the stream branch**; auto-merged by the Stream-Conductor when: stream-Verifier G4
  passes, CI green, no conflict. Squash merge, message references the EL ids closed.
- Stream branch → **PR into `main`** at each stream milestone; auto-merged via the **merge queue**
  (§7.4). Pushed to GitHub on every merge.
- **Cleanup:** worktree removed and branch deleted immediately after merge. Snapshot tags retained.
  A final Phase-4 sweep asserts zero stray `elev/*` branches and zero orphaned worktrees.

### §7.4 — The merge queue and deploy lock (the only serialisation points)

Development is fully parallel; only two moments serialise, each held for minutes not hours:

- **Merge lock** — a stream requests it, rebases its branch onto current `main`, runs CI + the smoke
  gate, merges, pushes, releases. Conflicts are resolved by the requesting stream (its own files by
  construction; a genuine cross-manifest conflict escalates to the Meta-Conductor).
- **Deploy lock** — per deploy target (`platform`, `platform-mcp`, `amjis-sidecar`, pipeline). Two
  streams never deploy the same service concurrently. After each deploy: revision live check, image
  SHA matches `main`, smoke gate green — *then* the Integration-Verifier runs the integrated battery.
- **Ordering preference** (not a hard barrier): α's C6 + C1 land first because γ consumes them.
  Everything else merges as it becomes ready.

### §7.5 — Launch modes: single-process (default) vs three-process

**MODE 1 — SINGLE KICKOFF (default, and what §7.1–§7.4 assume).** One Claude Code session. The
Meta-Conductor runs Phase 0, then spawns the three Stream-Conductors as sub-agents. The merge queue,
deploy lock and arbitration are all in-process. One ledger, one report.
*Standing obligation in this mode:* the Meta-Conductor must keep its OWN context lean — it delegates
all reading, building and verifying to sub-agents and holds only ledger POINTERS, never payloads.
After every phase boundary it writes `ledgers/META_CONDUCTOR_STATE.md` (phase, per-stream lane
status, merge/deploy lock state, open arbitrations, next action) so the run is resumable from disk
if the session is ever restarted.

**MODE 2 — THREE KICKOFFS (parallel processes). BINDING OPERATING PROTOCOL.**
Three Claude Code sessions, one per stream: ~3× token throughput and crash isolation, at the cost of
file-based coordination. v2.0's sketch of this mode had six run-killing defects; the following rules
are **mandatory and complete** — a stream that cannot satisfy one of them halts rather than improvises.

**M2.0 · WORKING-TREE ISOLATION (finding #1 — catastrophic).** Three Claude Code sessions in ONE
checkout collide on `.git/index.lock`, and one stream's `pull --rebase` moves HEAD under another's
builders mid-edit — producing commits that silently revert merged work, undetectable because each
stream verifies only its own recipes. **Each session runs in its OWN clone:**
`~/madhav-alpha`, `~/madhav-beta`, `~/madhav-gamma`, each cloned from the same origin. Lane worktrees
are cut inside the owning clone. **No two sessions ever share a working tree.**

**M2.1 · SHARED STATE LIVES OUTSIDE ANY CHECKOUT.** Coordination state lives at
`~/elev-v2-shared/` (created by α in Phase 0) — locks, flags, contract status, heartbeats,
integration log, proxy ledgers. Git-tracked ledgers under `00_ARCHITECTURE/.../ledgers/` remain the
durable record, but **mutual exclusion never depends on git.**

**M2.2 · LOCKS: ONE MECHANISM, HEARTBEAT-BASED TTL (findings #4, #5, #11).**
- Acquire with `mkdir ~/elev-v2-shared/locks/<name>` — atomic on the local filesystem, single
  machine, no ambiguity. Write `{stream, pid, intent, acquired_at, heartbeat_at}` INSIDE the
  directory *after* mkdir returns 0. On failure, wait with jittered backoff (5–30s). **Never steal.**
- **The holder rewrites `heartbeat_at` every 2 minutes** for as long as it holds the lock.
- **A lock is breakable only when `heartbeat_at` is >5 minutes stale** (i.e. the holder is dead) —
  never on age. v2.0's 20-minute age TTL would have let a stream legally break a live lock during
  β's multi-hour rebuild or the gochara sweep, causing exactly the concurrent prod write the lock
  exists to prevent.
- Breaking is two-phase: write `<lock>.break_intent`, wait 60s for the holder to bump its heartbeat,
  then break and log to `INTEGRATION_LOG.md`.
- Lock names: `merge` (one global), `deploy-platform`, `deploy-platform-mcp`, `deploy-sidecar`,
  `deploy-pipeline`, `db-rebuild`, and `RESTORE` (§11.9).

**M2.3 · THE MERGE LOCK COVERS THE AUTO-DEPLOY (finding #6).** `platform` auto-deploys on merge to
`main`, so the deploy cannot be serialised separately from the merge. **The merge lock is held
continuously through: rebase → CI green → merge → push → the resulting auto-deploy → revision +
image-SHA check → smoke gate green → integration battery (M2.6) → release.** `platform-mcp` is a
CONTENDED target between α and γ; its explicit deploy takes `deploy-platform-mcp` separately.

**M2.4 · PHASE 0 AND THE START GATE (findings #7, #8).** α runs Phase 0 in this order and writes
`~/elev-v2-shared/PHASE0_COMPLETE.flag` **LAST**, containing a manifest:
```json
{"run_start_tag":"...","db_snapshot_id":"...","baseline_ledger_path":"...","baseline_sha256":"...",
 "contracts":[{"id":"C1","path":"...","sha":"..."}, …C2,C3,C6,C8],
 "sealed_harness_path":"...","routing_suite_path":"...","dark_replay_set_path":"...",
 "overflow_queue_path":"...","branch_heads":{"alpha":"...","beta":"...","gamma":"..."}}
```
β and γ **validate every field** (files exist, shas match, branches resolve) before starting lane
work. **There is no "looks fine, proceed" fallback** — v2.0's version would have let β and γ work
six hours producing legally unmergeable code if α died after cutting branches but before capturing
the baseline. On failure or a 90-minute timeout, β/γ write
`~/elev-v2-shared/PHASE0_TIMEOUT_<stream>.flag` and **abort**. α's error path writes
`PHASE0_FAILED.flag` so siblings fail fast instead of polling into the morning.
Phase 0 additionally freezes, read-only, before any Ω builder exists: the **sealed evaluator
harness** (§2 Ω-V), the **60-item routing suite** (§2 Ω4), the **dark-corpus replay set** (§2 Ω7),
and `OVERFLOW_QUEUE.md`.

**M2.5 · LIVE-IMPLEMENTATION SIGNALS (finding #2 — the flagship-fails-at-dawn path).** A published
contract proves nothing about production. When a stream's Verifier confirms a contract's
implementation live in prod, it writes
`~/elev-v2-shared/implementations/<Cn>.live` = `{contract, deploy_target, revision, image_sha,
prod_probe_payload_ref, verified_at}`. **Hard rule: a consuming lane may not be dispositioned
`VERIFIED-CLOSED` while any contract it consumes lacks a `.live` record** — it is
`PARKED-HONEST (blocked-on-<stream>:<Cn>)`. Consumers poll `implementations/` at every lane boundary
and **re-run any stubbed lane against the live implementation** once it appears. This is what stops
γ self-verifying Ω6 against its own stub of the mechanisms tool.

**M2.6 · THE LOCK HOLDER IS THE INTEGRATION-VERIFIER (finding #9).** §6's global Integration-Verifier
has no owner in Mode 2. Therefore: **before releasing the merge lock, the holder runs the shared
smoke + budget-census + regression battery against the integrated head** and appends the result to
`~/elev-v2-shared/INTEGRATION_LOG.md`. A regression is the merging stream's to revert *before*
release — never the next stream's to discover.

**M2.7 · HEARTBEATS AND CLOSE SUCCESSION (finding #3 — α was a single point of failure).** Every
stream touches `~/elev-v2-shared/heartbeat/<stream>.hb` every 10 minutes. α owns Phase 0, the
Phase-4 acceptance and the Phase-5 close. **If `alpha.hb` is >45 minutes stale AND both sibling
completion flags exist, γ assumes close ownership** (γ built the flagship, so it is the correct
deputy) and performs Phase 4 + Phase 5 itself, noting the succession in the report.

**M2.8 · COMPLETION FLAGS (finding #10).** ASCII names, everywhere, no Greek:
`STREAM_ALPHA_COMPLETE.flag`, `STREAM_BETA_COMPLETE.flag`, `STREAM_GAMMA_COMPLETE.flag`. Each is
JSON: `{lanes_dispositioned:n, parked_blocked_on:[...], flagship_self_verified:bool, ledger_path}`.
**α's wait deadline is T0+11h, not 14h** — §11.5's 14h hard cap must leave Phase 4 (1.5h) and
Phase 5 (45m) their budget. `flagship_self_verified:false` from γ means α proceeds to report the
honest state; it does not retry γ's work.

**M2.9 · NO ARBITRATION; PARK INSTEAD (finding #10 on manifests).** No cross-stream arbiter exists.
A genuine cross-manifest need is parked `PARKED-HONEST` naming the owning stream — never negotiated,
never opportunistically edited. **Because §0's two load-bearing pieces would otherwise be designed to
park, Phase 0 pre-resolves the two known collisions:** `platform-mcp/src/tools/intent_classify*.ts`
is **reassigned to γ** (Ω4 must change it), and C7's CI assertion goes in γ-owned
`.github/workflows/elev-depth-gates.yml` (α scaffolds an include point, never the assertion).

**M2.10 · PER-STREAM PROXY AND GOAL-KEEPER (finding #11).** Each conductor self-proxies per §10 and
writes to its OWN append-only `~/elev-v2-shared/proxy/<stream>.md` (no write contention), merged at
close. **Any proxy ruling touching a published contract must be filed as an AMENDMENT in
`CONTRACT_STATUS.md` and is binding on the other streams.** Each conductor spawns its own Sonnet
Goal-Keeper scoped to its stream. §11.3's retry ladder terminates at `PARKED-HONEST` — never at a
peer stream, which cannot help.

**M2.11 · OVERFLOW.** `OVERFLOW_QUEUE.md` is written by α in Phase 0. A stream that finishes early
claims an item by appending a claim line **under the merge lock**. Never another stream's open lane;
never invented work (§12).

**Choosing:** Mode 1 is simpler to reason about. Mode 2 buys ~3× throughput and crash isolation for
the price of the above protocol plus one wait-and-launch step. **Do not mix modes.** The kickoff
prompts for both live in `briefs/elevation_campaign/KICKOFF_PROMPTS_v2_1.md`.

### §7.6 — Overflow queue

A stream that completes early pulls the next item from the Meta-Conductor's overflow queue — parked
sub-items, the corpus-OCR tail, EL-21 phase-2, additional battery domains — rather than idling.
Never pulls another stream's open lane.

---

## §8 — Execution timeline (projected)

```
PHASE 0   ~45m  serial   Meta-Conductor: snapshot · branches · BASELINE capture · contracts · spawn
PHASE 1   ~3h   ∥∥∥      α: A + B + K1        β: D.audit + C + G        γ: Ω1 + Ω2 + Ω4
                         α ships C6 (EL-37) + C1 (budget_kb) in its first merge
                         → merge-queue → DEPLOY-1 → Integration-Verifier → SNAPSHOT
PHASE 2   ~3h   ∥∥∥      α: H + A-hardening   β: D.fix + rebuild + D2   γ: Ω3 + Ω5 + Ω8 + E
                         → merge-queue → DEPLOY-2 → Integration-Verifier (+FORENSIC 7/7, MSR) → SNAP
PHASE 3   ~3h   ∥∥∥      α: K1 full gates     β: G-corpus + T           γ: Ω6 + Ω7 + I(dossier) + F
                         → merge-queue → DEPLOY-3 → Integration-Verifier → SNAPSHOT
PHASE 4   ~1.5h serial   FLAGSHIP ACCEPTANCE (§2 Ω-Verification, both domains, both charts) ·
                         full battery · regression diff vs baseline · red-team pass ·
                         chart-agnostic + contamination checks · γ.J packets
PHASE 5   ~45m  serial   Meta-Conductor: coverage matrix finalised · register dispositions appended ·
                         CURRENT_STATE + SESSION_LOG close · branch/worktree cleanup · morning report
```
**Projected wall-clock ≈ 12h** with three streams (v1.0's single-stream estimate was 8–11h for
*less* scope — the depth mandate is net-new work; parallelism absorbs it).

---

## §9 — The Verifier protocol (what DONE means)

1. **Baseline before any fix** (§7.1.3). No baseline → no merge.
2. **G0 reproduce-or-reclassify.** A lane's first act is re-running its recipes against prod. Symptom
   absent → `NOT-REPRODUCED`, item closes with **no code churn** (some register symptoms may be
   stale — R5.1-era fixes).
   **EVIDENCE BAR (v2.1, finding #9 — this was the cheapest path to a fake-green matrix).** A
   builder under time pressure could close a large fraction of the register with one probe each,
   especially for size/client-dependent symptoms (EL-36 trimming, EL-42 blowouts, EL-11 caps) that
   simply will not reproduce under a differently-shaped probe. Therefore `NOT-REPRODUCED` requires
   BOTH: (a) a **committed regression test that reproduces the ORIGINAL recipe verbatim** — same
   args, same shape — and passes on the current head; and (b) the **raw payload diff against the
   `elev-v2-run-start` baseline**. Without both, the disposition is `PARKED-HONEST`, not closed.
3. **G4 confirm.** After merge + deploy, the Stream-Verifier independently re-runs the recipes
   against the **live production MCP** — never a worktree, never localhost (the
   `feedback_ac_must_verify_target_environment` scar) — on **both** canonical charts, plus the
   regression battery (baseline diff: nothing that worked got worse), plus the lane's §5 acceptance
   criteria.
4. **Evidence block per EL**, appended to `ledgers/ELEVATION_V2_RUN_LEDGER.md`:
   `{el_id, status, before_payload_ref, after_payload_ref, probes_run, charts, deploy_revision,
   image_sha, verifier_notes}`. **The §15 matrix is updated ONLY by a Verifier.**
   **PHASE-4 REVALIDATION IS MANDATORY (v2.1, finding #8).** Production keeps changing for hours
   after an item closes — all three streams deploy `platform` and `platform-mcp`, so an item closed
   after DEPLOY-1 can be silently broken by DEPLOY-3, and the integration battery checks smoke and
   census, not per-EL acceptance. Therefore **Phase 4 re-runs every `VERIFIED-CLOSED` item's G4
   probe set against the FINAL head**, and any failure is downgraded to `PARKED-HONEST` **before**
   the morning report is written. The recorded `deploy_revision`/`image_sha` is what makes the
   regression traceable.
5. **Integration-Verifier** additionally confirms, on every integrated head: cross-stream regressions
   absent, deploy state correct (revision + image SHA), the smoke/census/receipt gates green.
6. **Four dispositions only:** `VERIFIED-CLOSED` · `PREPARED-FOR-NATIVE` · `NOT-REPRODUCED` ·
   `PARKED-HONEST`. **There is no "passed with caveats"** — a caveat is either a PARKED-HONEST
   residual with live-verified disclosure, or a fail.

---

## §10 — Native-Proxy charter

**MAY, autonomously (every call logged with rationale):** all engineering decisions (design
trade-offs, eliminate/integrate/build-around on legacy code, per-facet defaults, taxonomy naming,
Ω2 relevance-rule authorship); merge-order and lock arbitration; ruling on ambiguous acceptance
criteria in the spirit of §0 + the register's "Expectation violated" fields; **superseding
CURRENT_STATE A-5** (remedy accept-as-dark → β.G repair) and progressing A-6 via β.T; bounded scope
cuts inside a lane (park sub-items as PARKED-HONEST when the window tightens — never silently);
**additive** schema migrations; chart-scoped rebuilds; production deploys; answering any question a
builder would otherwise raise to the human.

**MUST NOT, ever:** fabricate data — life events (EL-54), classical rules or citations (B.10),
translations where OCR confidence is low (flag, never invent); alter the FROZEN orchestrator
contract, the sealed L5 split, the FORENSIC birth anchors, or canonical registries beyond the
declared Phase-5 close-edits; **ratify in the native's name** (every ruling is recorded PROXY-RULED
for morning ratification); destroy data without a current snapshot + a passed reverse-citation
report; expand scope beyond this charter (new campaigns, D-6 build, architecture changes — park and
note); **weaken the §0 mandate** (a 100% accounting requirement may never be renegotiated downward
by a proxy ruling — a lane that cannot meet it parks honest and says so).

**Tie-breaker doctrine, in order:** (1) **truth over coverage** — an honest gap beats a padded
answer; (2) **the depth mandate (§0)** — when in doubt, serve more, account for everything;
(3) the native's stated differentiator: deterministic full-depth consumption; (4) smallest-real-client
UX; (5) classical grounding with citation; (6) reversibility.

---

## §11 — Safety rails

1. **Snapshots** — git tag + DB snapshot at run-start and every phase boundary; automatic, never
   waits. Rollback-and-retry beats compounding corruption.
2. **Rebuild discipline** — chart-scoped delete-then-insert only (§N.3); never a full-DB rebuild;
   FORENSIC 7/7 asserted after every rebuild; sealed tables untouched.
3. **Bounded retries** — MAX 3 remediation cycles per lane-criterion → Opus escalation → 2 more →
   `PARKED-HONEST` with residual + live-verified disclosure. Goal-Keeper watches for thrash.
4. **Reverse-citation before ANY deletion/retirement** — grep the live codebase for citations;
   still-cited targets become keep-or-repoint; report logged.
5. **Budget ceilings** — 14h wall-clock hard cap; 6h per lane; the Brahma-arc spend rails apply.
6. **Deploy hygiene** — per BUILD.md; deploy lock per target; smoke gate before any Verifier probe.
7. **Chart-agnostic + contamination checks every phase** — no native hard-coding in chart-agnostic
   paths; `chart_id` always a parameter; **Ω2's relevance rules must be chart-agnostic** (domain
   rules, never "this chart's" rules).
8. **The one hard floor:** never destroy prod data without a current snapshot and a passed
   reverse-citation report. Schema changes are permitted; unrecoverable data loss is not.

9. **ROLLBACK RUNBOOK (v2.1, finding #5 — v2.0 named rollback but never specified one, and had no
   defined action for a FORENSIC failure at 3am).**
   **Triggers, any one of which fires it:** FORENSIC 7/7 fails after a rebuild · MSR drift
   unresolved after the documented refresh · the smoke gate is red post-deploy and two remediation
   attempts have failed · the integration battery (M2.6) shows a regression the merging stream
   cannot revert cleanly.
   **Procedure:** (1) acquire the global **`RESTORE` lock** — while held, **all merges and all
   deploys across all streams are frozen**; a stream discovering the lock waits, it does not
   proceed. (2) Identify the last good phase snapshot (git tag + DB snapshot). (3) If the fault is
   code: revert the service to the prior Cloud Run revision. If the fault is data: restore the
   chart-scoped rows from the snapshot — **never a whole-DB restore.** (4) Re-run FORENSIC 7/7 and
   the smoke gate to prove the restore landed. (5) Reopen every EL id included in the reverted
   change to `PARKED-HONEST` **in the same commit** (finding #15: a revert silently invalidates
   other streams' verified work otherwise — the merge-lock holder therefore records, per deploy,
   the prior revision AND the exact set of EL ids newly included). (6) Release the lock and log the
   whole sequence to `INTEGRATION_LOG.md`.
   **A failed FORENSIC halts β immediately** — no further writes until the restore is proven.

---

## §12 — Out of scope (explicit, park-and-note)

D-6 GOCHARA-SWEEP-2.0 build (EL-16, staged, native review pending) · the Darpana S3 re-run itself
(native-attended; this run unblocks it, EL-15's verdict stays OPEN) · UCN→UCD retirement ·
cockpit/UI redesign beyond EL-24's data fields · full-corpus OCR beyond β.G's bounded ~200 rows ·
EL-21 claim-checker phase 2 (designed, not built — overflow-queue candidate) · any Macro-Plan
phase-jump · **LEL content entry (native-only — the intake surface is built, the events are not)** ·
A-6 accept-as-dark reversal beyond β.T's re-verification evidence.

## §13 — Prepared-for-native deliverables (the morning desk)

1. **LEL intake packet** (γ.J) — the 30–60-minute guided event-logging surface, ready to run.
2. **Ratification packet** (γ.J) — all pending ratifications incl. this run's
   `NATIVE_PROXY_LEDGER_ELEVATION_V2.md`, one recommended disposition each.
3. **Darpana readiness note** — which held exit-conditions this run closed (mapped to PRE_DARPANA
   v2.0), what remains for the S3 re-run.
4. **Parked-item register** — every PARKED-HONEST residual with bounded-attempt evidence and a sized
   follow-up recommendation.
5. **The dark-corpus report** (Ω7) — per domain, what the instrument computes and still did not
   serve. Target zero; whatever is non-zero is the next campaign's first page.

## §14 — The morning report

`00_ARCHITECTURE/llm_consumption_audit/ELEVATION_V2_RUN_REPORT_v1_0.md`: per-stream and per-phase
outcomes; the §15 matrix final state with per-EL evidence refs; **the §0 mandate scorecard**
(routing-default correctness, Ω3 accounting %, page counts at both client sizes, dark-corpus
counts, the ≤3-call reproduction result, both domains, both charts); every Native-Proxy ruling with
rationale; every rollback/retry; deploy revisions shipped; rebuild scope + FORENSIC/MSR post-checks;
battery + red-team results; branch/worktree cleanup confirmation; budget and wall-clock actuals; the
five §13 packets; and a one-paragraph verdict against §0. CURRENT_STATE §2 + SESSION_LOG updated
atomically; root `CLAUDECODE_BRIEF.md` flipped to COMPLETE only if the close checklist validates.

---

## §15 — Coverage matrix (every EL + every Ω → stream · lane)

| Item | Stream · Lane | Overnight outcome targeted |
|---|---|---|
| **Ω1 TCI** | γ · Ω | Corpus-derived inventory, CI-generated, nothing unlisted |
| **Ω2 relevance map** | γ · Ω | 100% classified, permissive, exclusions named |
| **Ω3 completeness contract** | γ · Ω (+α K1) | 100% accounting or build failure |
| **Ω4 depth default** | γ · Ω | `deepdive` default; 60-question suite green |
| **Ω5 staging gate** | γ · Ω | Paged dossier, `synthesis_gate`, ≤6 pages @25k |
| **Ω6 patterns/chains** | γ · Ω (needs α C6) | All 10 mechanism classes + chains mandatory |
| **Ω7 dark-corpus report** | γ · Ω | Zero unserved non-empty concepts |
| **Ω8 floor reconciliation** | γ · Ω | Floors regenerated from TCI; CI-gated |
| EL-01 concept consumption | γ · Ω+I | 100% accounting verified on 2 domains |
| EL-02 floor as contract | γ · Ω5 | Receipt-gated composition |
| EL-03 concept ledger | γ · Ω1+Ω2 | Superseded by the TCI (stronger denominator) |
| EL-04 consumption metric | γ · Ω3+K2 | Accounting in receipts + battery dimension |
| EL-05 volunteering | γ · I+K2 | Top-N findings unprompted; benchmark pairs |
| EL-06 varga depth | γ · Ω8+E; K2 | Per-varga AV in floors; varga probe |
| EL-07 absence protocol | α · H+K1 | Resolver-gated phrasing + lint |
| EL-08 concept resolver | α · H | `concept_locate` live |
| EL-09 precision class | γ · K2 | Attribution table checked over prose |
| EL-10 two-pass law | γ · K2 (+§9) | Codified; this run executes on it |
| EL-11 client caps | α · A | Census green at smallest-client ceiling |
| EL-12 budget negotiation | α · A (C1) | `budget_kb` live |
| EL-13 catalog caching | α · B | Version field + doc + notify if supported |
| EL-14 server-side completeness | γ · I+Ω5 | Dossier = served product |
| EL-15 S3 unverified | β · T | Unblocked; verdict stays OPEN (§12) |
| EL-16 sweep v1 arch | — | OUT (D-6, native review) |
| EL-17 timing anchors | β · T | Re-verified live post-rebuild |
| EL-18 bhanga | β · D2 | Attested rules computed + cited |
| EL-19 sahams | β · D2 | Tājaka set computed, both charts |
| EL-20 rank residuals | γ · E | Documented formulas or explicitly unranked |
| EL-21 claim-checker | α · K1 (v1) | Absence + receipt classes; phase-2 designed |
| EL-22 four tracks | γ · K2 | Harness captures all four |
| EL-23 battery blind spot | γ · K2 | New grading dimensions |
| EL-24 build-state truth | γ · J (bounded) | Data fields legible; UI parked |
| EL-25 governance debt | γ · J | Ratification packet |
| EL-26 planner coverage | γ · Ω8 | Floors from TCI + varga-AV + dispositor primitives |
| EL-27 cross-ayanamsha | γ · I | Variation family + `ayanamsha_agreement` |
| EL-28 small-context capability | α · A | Named capability; EL-11/12 as its tests |
| EL-29 composition doctrine | γ · I+Ω5 | Served reading structure, gate-fired |
| EL-30 house_d1 semantics | β · D (C4) | Convention ruled, writers fixed, rebuilt |
| EL-31 EAV steering | α · H | Entity endpoints + steering + tool_search rank |
| EL-32 identifiers | γ · E (+α K1) | Canonical on output; gate extended |
| EL-33 active dashas | γ · F | Convenience face, all systems |
| EL-34 schema map | α · H (C3) | `get_database_schema` live, paginated |
| EL-35 inline significance | β · G | Framework-tagged significance strings |
| EL-36 portrait starvation | α · A | Flagship envelope fix + receipt-truth invariant |
| EL-37 mechanisms bind bug | α · B (C6) | Fixed in first merge; smoke-gated forever |
| EL-38 argala | α · B + β · D | Bounded defaults + house-resolved + zeros adjudicated |
| EL-39 tropical-only | β · C (C5) | Sidereal default; FORENSIC panchāṅga oracle |
| EL-40 uniform 0.875 | β · D | Real formula or withdrawn-with-reason |
| EL-41 silent categories | α · B (C2) | Per-category receipts everywhere |
| EL-42 token blowouts | α · A | Uniform budgets; census green |
| EL-43 EAV verbosity | α · A | Pivot-first; savings spent on content (§0.3) |
| EL-44 skeleton verdicts | γ · E | Grounded verdict layer |
| EL-45 wealth varga stub | γ · E+Ω8 | D2/D11/Indu consumed in-tool AND in-floor |
| EL-46 flags trimmed | α · A | Honesty-field immunity |
| EL-47 null varga houses | α · B + β · D | Served + persisted houses |
| EL-48 varga snapshots | α · H | `vargas[]` param |
| EL-49 panchanga_get | β · C | Direct tool: 5 aṅgas + karaṇa + sunrise + horā |
| EL-50 muhūrta gaps | γ · F | 4 sub-gaps closed; Vadha-tārā regression |
| EL-51 remedy completeness | β · G | Full catalog + computed contraindications |
| EL-52 corpus OCR | β · G (bounded) | Decisive passages structured; tail scoped |
| EL-53 election loop | γ · F+J | Elections file as predictions |
| EL-54 LEL backfill | γ · J | Intake packet (native supplies content) |
| EL-55 micro-varga salience | γ · E | Cited varga-weight term |
| EL-56 ayanamsha dedup | γ · I | Family-collapse + agreement (with EL-27) |
| EL-57 contradiction filter | γ · E | Domain-filtered + honest empty |
| EL-58 stale predictions | γ · J | Lifecycle sweep + `lapsed_unobserved` |
| EL-59 rank semantics | γ · E | One vocabulary, basis-labelled |
| EL-60 preserve what worked | γ · K2 (a) + α · K1 (b) | Notes accretion + coverage attestation |
| EL-61 dossier | γ · I+Ω5 | The flagship acceptance |

*Also carried from CURRENT_STATE v6.41:* A-5 → β.G supersession · A-3/CR-131 + gochara env → β.T ·
B-1 silent-empty → α.B · B-2 standing-prediction surfacing → γ.J.

---

*End of ELEVATION_CAMPAIGN_CHARTER v2.0 — authored by Fable/Opus in Cowork, 2026-07-24. Grounded in
same-session live-production probes (graha_portrait starvation with false-✓ receipt · the
query_mechanisms parameter-binding root cause · argala default-limit behaviour · tropical ephemeris
with tropical-derived nakshatra · the 33-item wealth floor with its verified omissions ·
intent_classify's `depth: standard` default at confidence 0.2 · the served:0 completeness receipt ·
the unreachable `hard_floor: true` mechanism item) and in code recon of the working tree at
authoring time. The register accumulates; this charter executes. **The depth mandate (§0) is the
campaign. Nothing closes without the Verifier.**
