---
artifact: SUVARNA_CAMPAIGN_PLAN
canonical_id: SUVARNA_CAMPAIGN_PLAN
version: "1.0"
status: DRAFT — for native review (several review rounds expected before any execution)
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
decision_owner: Native (Abhisek Mohanty)
supersedes: nothing directly. Succeeds the Nirmāṇa elevation campaign (see NIRMANA_SUPERSESSION_RECORD_v1_0.md, PR #2751).
inherits:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                                  # tier 1 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md         # tier 2 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md        # tier 3 (sealed)
  - 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md                      # tier 4 (draft, pending acceptance)
uses: >
  The Nikaṣa engine as it stands on branch campaign/nikasha-test (PR #2736): the inspector
  (asset_census.py), tracker (asset_elevation_tracker.py), catalog provenance (catalog_provenance.py),
  the delta ledger (asset_gaps.jsonl), the certification ledger (asset_certs.jsonl), the change
  register (NIKASHA_CHANGE_REGISTER_v2_0.md) and the implementation plan (NIKASHA_IMPLEMENTATION_PLAN_v1_0.md).
changelog:
  - "1.0 (2026-09-28): first full draft. Built on a fact baseline measured the same day (Appendix A)."
---

# Suvarṇa — the data-plane elevation campaign plan

## §0 · Reading guide

### 0.1 · Names

| Name | What it is |
|---|---|
| **Suvarṇa** (सुवर्ण, gold) | The campaign. Elevates every data-plane asset, L0 → L5. |
| **Nikaṣa** (निकष, touchstone) | The engine. The system that tests and certifies an asset: four tiers, inspector, tracker, ledgers, detectors. If decision N-2 is approved, it also takes in the build engine it depends on. |
| **Strategic Suvarṇa** | This session. Plans, discusses, rules, writes briefs. Never executes. |
| **Nikaṣa Engine** | The session that builds and freezes the engine (Stage 1). |
| **Exec Suvarṇa** | The session that runs the elevation (Stages 2–4). |

- Suvarṇa is what the touchstone tests. The engine is finished first; the campaign runs on it.
- "Nirmāṇa" now names two things: the superseded elevation campaign, and a still-live build-engine
  branch (`campaign/nirmana-engine`). This plan calls the second one "the build engine" (§5.1, E3).

### 0.2 · What this document is

- The master plan. It fixes the end state, the standard, the stages, the gates and the operating model.
- Each stage gets its own brief later. A brief never contradicts this plan; if it must, the plan is revised first (§10).
- It is written to be reviewed. Every figure has a source in Appendix A.

### 0.3 · How to read it

- §1–§3: where we are going, by what standard, from where.
- §4–§5: the stages and what each contains.
- §6: how the work is run.
- §7–§8: what is outside our hands, and what only the native decides.
- §9–§11: tracking, change control, risks.

---

## §1 · End state

### 1.1 · Asset level

An asset is **ELEVATED** when all four hold:

1. Every core gate its layer requires carries a current `PASS` or a justified `N/A` in `asset_certs.jsonl` (§2.1).
2. Every asset-specific addition declared for it is certified the same way (§2.3).
3. It has no open `gap` row in `asset_gaps.jsonl`.
4. Its disposition is recorded (keep, integrate, enrich, qualify, consolidate, historical, retire, unresolved — tier 4 §0).

- An asset retired or consolidated with a recorded reason also counts as terminal.
- "Frozen by Nirmāṇa" is not elevated. It is a starting point (§3.3).

### 1.2 · Layer level

A layer is **CLOSED** when:

- its layer instance (tier-3 instance) is accepted by the native;
- every active asset in it is ELEVATED or terminally dispositioned;
- a from-scratch rebuild of the layer succeeds under the orchestrator and re-measures clean;
- the native signs the layer close.

### 1.3 · Campaign level

Suvarṇa is **COMPLETE** when:

- all six layers are CLOSED;
- every `[TRANSFERS]` obligation (work that belongs to the retrieval or conversation planes) is recorded as pending with its owner;
- the closure report is accepted by the native.

### 1.4 · How we will know

| Measure | Today | End |
|---|---|---|
| Assets ELEVATED | 0 of 127 | 127 of 127, or terminally dispositioned |
| Certification records | 0 | one per required gate per asset |
| Open gap rows | 799 | 0 |
| Gate cells (9 gates × 127 assets) | 1,143 cells, 0 certified | all PASS or justified N/A |

### 1.5 · Out of scope

- **Astrological correctness.** The data plane is data engineering and computation. Interpretive
  correctness is not a data-plane obligation (native ruling 11, 2026-09-25).
- **The retrieval and conversation planes.** Not built yet. Suvarṇa records what they must inherit; it does not build them.
- **Empirical calibration.** L5 fills its values as outcome data accrues. That is by design, not unfinished work.
- **New assets.** Suvarṇa elevates the existing 127. New assets are proposed through the opportunity register (§2.4) and ruled separately.

---

## §2 · The standard

One elevation definition. A fixed core for every asset. Declared additions where an asset needs more.

### 2.1 · The core: nine gates

| Gate | Plain meaning |
|---|---|
| **Ldgr** — derivation ledger | Every derived value traces to the facts it came from. |
| **Idem** — idempotency | A rebuild replaces its own rows; it never accretes and never silently fails. |
| **Earn** — earned signal | Every status or verdict has a detector behind it that could read false. |
| **Null** — honest null | Where a value cannot be derived, it is null with a reason, never an invented default. |
| **Vocab** — vocabulary | Names and terms conform to the project's closed vocabularies. |
| **Carr** — source carriage | Classical sources are carried and reproduced faithfully. |
| **Narr** — narration fidelity | Any generated text restates cited facts; it never re-derives them. |
| **Dens** — serving density | What is served is layered by confidence, never flattened. |
| **Build** — buildability | The orchestrator can dispatch it, and a triggered rebuild produces the right result. |

- **Verdicts** come from a closed set: `PASS · FAIL · PARTIAL · NO_DETECTOR · N/A` (plus `ERRORED` for a failed measurement).
- **Only `PASS` or a justified `N/A` closes a gap.** Anything else keeps it open. This is the lesson of every false closure found so far.
- **A core gate that does not apply** reads `N/A` with a written reason. Never a silent skip.

### 2.2 · Principles every verdict obeys

- **Earned signal.** A status needs a detector that could return false (CLAUDE.md §N.8).
- **Honest null.** "I don't know" beats a plausible default (§N.7).
- **L1 is the authority.** A derived value references its L1 fact; it never restates it (§N.5).
- **Rebuild replaces.** Per-chart delete-then-insert on the natural key (§N.3).
- **Measured, not claimed.** A gap row states what was measured, with what, over which population.

### 2.3 · Asset-specific additions

- **What they are.** Requirements that apply to some assets only. Example: a grounding tier on interpretive signals, but not on ephemeris rows.
- **How they are declared.** In the asset's brief (tier-4 instance), with:
  - the requirement, in one sentence;
  - the detector that measures it;
  - why this asset needs it.
- **Who approves.** The native approves each addition **class** once (for example "grounding tier for interpretive L2 classes"). Individual assets then adopt the approved classes without a new ruling.
- **The rule.** Additions add to the core. They never replace, weaken or waive a core gate.
- **The candidate pool.** Four classes are proposed now (decision N-11):

| Candidate class | Source | Would apply to |
|---|---|---|
| Grounding tier (text-direct / principle-derived / instrument-derived) | Nirmāṇa doctrine D-GROUNDING | interpretive signal classes, yoga and dosha firings, remedies |
| Stored salience with a protected tail | D-SALIENCE | L2 signals and their serving envelopes |
| One temporal voice (a single arbiter per question and range) | D-TIME | L3 temporal engines |
| Every asset has a consumer or a recorded disposition | D-SERVICE | all layers |

- These are adopted on their merits, one class at a time. They are not inherited from Nirmāṇa.

### 2.4 · Beyond conformance: the opportunity register

- Tier 4 §9 keeps a second kind of ledger row: `kind: opportunity`.
- It records improvements (a better algorithm, wider coverage, a cheaper build, a new synergy).
- **Opportunities never block elevation.** An asset can be ELEVATED with open opportunities.
- Opportunities are ruled in batches per layer. Adopted ones become work in that layer; the rest are recorded.

---

## §3 · Starting position (measured 2026-09-28)

### 3.1 · Assets

| Layer | Active assets | Frozen by Nirmāṇa (kept) |
|---|---|---|
| L0 Brahmagyan | 40 | 40 |
| L1 Gaṇita | 19 | 19 |
| L2 Bodha | 23 | 22 |
| L3 Kāla | 21 | 12 (13 frozen; `ka_gochara_sweep` since retired) |
| L4 Phala | 9 | 0 |
| L5 Mīmāṃsā | 15 | 4 |
| **Total** | **127** | **97 active** |

### 3.2 · Ledgers

- **Delta ledger** `asset_gaps.jsonl`: 857 lines. **799 open gaps.** 572 of them sit on Nirmāṇa's kept assets.
- **Certification ledger** `asset_certs.jsonl`: header only. **Zero certifications.**
- **Production ledger write history:** one first emit (2026-09-27, 567 gaps opened, none closed) and one crosswalk fold (2026-09-28, R81).

### 3.3 · What Nirmāṇa left

- 98 freezes. 97 of the 98 assets have at least one open Nikaṣa gap.
- 72 of the 98 were frozen under Nirmāṇa's first definition, which Nirmāṇa itself replaced three times.
- The code and data improvements are live in production. They are kept. Nothing is reverted.
- Known defects on kept assets (full list in the supersession record §2.2):
  - `bo_upaya` cannot rebuild on any chart (R244);
  - six L2 assets rebuild only on the canonical chart (R243);
  - `ka_gochara`'s registry names the wrong table (R240);
  - `lel_events` has no writer (R236).

### 3.4 · The change register

Measured by counting rows, not by the header tally (which has drifted; see Stage 0).

| | Rows |
|---|---|
| Total | 252 |
| Open | 180 |
| — blocking the engine freeze | 4 (R24, R39, R71, R244) |
| — blocking a layer | 95 |
| — degrading | 71 |
| — cosmetic | 10 |
| Closed, done, closed-on-branch, measured | 70 |
| Partial | 2 (R81, R99) |

### 3.5 · The engine's own test (freeze criterion)

The engine is frozen when five tests pass in production tooling and every register row is closed or explicitly deferred.

| Test | Last evaluated (2026-09-26, before waves 1–3) |
|---|---|
| T1 — finds what is there | PARTIAL (sandbox only) |
| T2 — does not invent what isn't there | FAIL (60 disagreements) |
| T3 — a fix closes a row | FAIL in production tooling |
| T4 — works on a layer it wasn't built against | PARTIAL |
| T5 — the pieces agree | FAIL |

- **These have not been re-measured since the three waves of fixes.** Most defects behind T2 and T3 are now closed. A fresh scorecard is the first step of Stage 1.

### 3.6 · The documents

- **Tiers 1–3:** sealed. A reopen agenda is ruled (D2, 2026-09-27): 32 clause fixes across the three documents, plus the derivability mechanisms (§5.1, E2).
- **Tier 4:** draft, pending your acceptance.
- **L0 layer instance** (v3.0): draft, pending your acceptance.
- **Asset briefs:** 5 L0 pilots. No other layer has an instance or briefs.

### 3.7 · Where the code is

- **Nikaṣa tooling** lives on `campaign/nikasha-test` (PR #2736). It is **not on `main`**. The PR targets
  `l3/kala-layer-briefs`, not `main`, and adds about 154,000 lines (mostly census artefacts).
- **The build engine** lives on `campaign/nirmana-engine`: 200 commits not on `main`, no PR.
  - Closed: A1 (timing), A2 (error text), A3 (run-killer), B1 (cascade reporting), B2 (downstream count).
  - Not started: C1 (crash and orphan handling), C2 (stuck states), D1 (the engine judged by the Build gate).
  - Migrations 1094 and 1095 are not in production.
  - Nothing from it is deployed.

### 3.8 · Live work elsewhere

- **L3 Gochara workstream** (`l3/gochara-autonomous-wp0-7`). Active today. It applied a production migration (1150) to `ka_gochara`, which is a Suvarṇa L3 asset.
- **Pūrṇa**, **Jātaka**: separate campaigns with their own migration reservations.

---

## §4 · Stages and gates

```
 STAGE 0  Baseline governance ──────────────── gate G0 ─┐
                                                          │
 STAGE 1  Nikaṣa Engine                                  │
          E1 Tooling ──┐                                  │
          E2 Doctrine ─┼── gate G1: ENGINE FREEZE ◄───────┘
          E3 Build ────┤        (native ruling)
          E4 Landing ──┘
                          │
 STAGE 2  Suvarṇa L0 pilot ── gate G2: rollout go/no-go
                          │
 STAGE 3  Suvarṇa L1 → L2 → L3 → L4 → L5
          (each layer closes at its gate G3.Lx)
                          │
 STAGE 4  Closure ─────── gate G4: campaign complete
```

### 4.1 · Why this order

- **Engine before campaign.** Elevating with an unfinished inspector is how false passes get through. Every wave so far found at least one path that could close a gap without a real measurement: a failed count query read as "not applicable", never-started build rows counted as runs, `ka_kshetra` passing on a refused rebuild, `bo_upaya` passing on a rebuild that cannot succeed.
- **Doctrine inside the engine stage.** Test T5 ("the pieces agree") cannot pass while the sealed tiers contradict each other. So the reopen is part of finishing the engine, not a separate campaign.
- **L0 alone first.** It is the reference layer: no chart scope, upstream of everything, all 40 assets kept, 5 pilot briefs already exist. It proves the whole loop at the lowest risk and gives a measured cost per asset.
- **Layers in order after that.** Each layer feeds the next. Improving an upstream layer after a downstream one is elevated invalidates the downstream work.

### 4.2 · The gates

| Gate | Passes when | Who rules |
|---|---|---|
| **G0** | Stage 0 items done (§5.0) | executor; native informed |
| **G1** Engine freeze | T1–T5 pass in production tooling on `main`; the four freeze blockers closed or explicitly deferred with a written reason; the build engine deployed; tier 4 and the L0 instance accepted | **native** |
| **G2** Rollout go | L0 CLOSED (§1.2); per-asset cost measured; the per-layer lifecycle (§5.3) confirmed or revised from L0's lessons | **native** |
| **G3.Lx** Layer close | that layer CLOSED (§1.2) | **native** |
| **G4** Campaign complete | §1.3 | **native** |

---

## §5 · Stage detail

Each stage below becomes its own brief before execution. The briefs are written here, in Strategic Suvarṇa.

### 5.0 · Stage 0 — Baseline governance (days)

Small, mechanical, and all done from this session or with minimal execution.

| Item | Why |
|---|---|
| Merge PR #2751 (Nirmāṇa supersession record) | A fresh session must find the decision first. |
| Correct the register's header tallies, and make them computed rather than typed | The tally already drifted (190 vs 180 open). A typed total is a claim, not a measurement. |
| Repair three register rows that break the table (R244, R246 extra column; R99 embedded pipe) | Tools that read the table misread them. |
| Record Suvarṇa and this plan in `CURRENT_STATE` | Same reason as the first row. |
| Relay R240 (`ka_gochara` registry/table mismatch) to the L3 Gochara workstream | They are changing `ka_gochara` in production now. |
| Name the three sessions | Strategic Suvarṇa, Nikaṣa Engine, Exec Suvarṇa. |

**G0 passes** when all six are done.

### 5.1 · Stage 1 — Nikaṣa Engine (session "Nikaṣa Engine")

Four workstreams. E1, E2 and E3 run in parallel. E4 runs throughout.

#### E1 · Tooling — inspector, tracker, provenance, ledgers

**Step 1: measure before changing.** Re-run T1–T5 on today's tooling. Publish a scorecard. Every later item is justified against it.

**Step 2: close the remaining tooling rows.**

| Group | Rows | Note |
|---|---|---|
| Detector gaps | R245 (remaining blind spots), R248 (latent hand/machine collision), R249 (empty-by-design vs broken), R250 (unverified label), R223-class timeout edges | none live today; each lands with a failing-first test |
| Data provenance | R226 (`--live` re-derive-and-diff), R229 (27 unowned tables), R228 (12 stale source references) | R226 must exist before retrieval code reads the provenance file |
| Ledger identity | R251 (the rest of the crosswalk: 19 pilot rows, 42 unregistered criteria) | extends the wave-3 fold |
| Waiting on others | R55 (needs migration 1094 deployed), R246 (needs the `bo_upaya` fix first) | sequenced by ruling |
| Width universes | R22 (needs R06 from the reopen) | depends on E2 |

**Step 3: prove it again.** Re-run T1–T5. Expect PASS on T1–T4. T5 waits on E2.

- **Rough size:** 40–60 hours, from the register's own pricing plus the rows added since.

#### E2 · Doctrine — reopen and re-seal the tiers

**Why it is in the engine stage:** T5 fails while the tiers contradict each other (R71), and every layer instance would otherwise invent content the tiers do not supply (the 130 invention rows found on 2026-09-26).

**The agenda has two parts:**

1. **Clause fixes** (D2 ruling, 32 rows). Stale counts, a missing review record, the [TRANSFERS] contradiction (R71), verdict spelling, the ruling-11 clause, and others. All already written.
2. **Derivability mechanisms** (the C8 cluster, about 20 primary rows). Missing tier-level machinery that every layer instance needs:

| Row | Mechanism |
|---|---|
| R06, R10 | how a table with several producers is counted and owned |
| R08, R09, R16 | per-asset carriage-check assignment |
| R86 | reconciling the dependency graph across seed, migration pin and live registry |
| R88 | per-layer switch behaviour |
| R89 | which layer carries each presentation field |
| R90 | per-layer ownership of coverage obligations |
| R91 | which entity classes each layer emits and accepts |
| R93 | the rule from evidence to disposition, and preserved kernels |
| R101 | per-layer narrative content |
| R105 | a minimum synergy / ablation harness |
| R221 | re-scoping tier-3 §0.1 to the catalog-provenance model (D5 rev. 2.1) |

- About 97 further "transcription" rows close with their primaries. They are verified when each layer instance is derived (Stage 3), not before.

**The procedure, one document at a time, in the order T1 → T2 → T3:**

1. Strategic Suvarṇa prepares the closed agenda for that document from the register.
2. **The native approves the agenda.** Nothing outside it is edited.
3. A builder applies it in one pass.
4. A fresh reviewer runs the cross-tier re-render check: every count, gate name and section reference the edit touched is checked across all tiers, the instances and the tracker.
5. **The native signs the re-seal.** The version bumps once.

**After the three re-seals:**

- Refresh tier 4 against the re-sealed tiers. **The native accepts it.**
- Refresh the L0 instance. **The native accepts it.**
- Regenerate the five L0 pilot briefs from the accepted versions.

- **Rough size:** 160–190 hours. The largest part of Stage 1. Most of it is derivability mechanisms, not clause edits.

#### E3 · The build engine

The inspector judges what the orchestrator builds. The from-scratch runs in Stages 2–3 need the build engine's fixes live.

| Item | Why |
|---|---|
| Decide ownership: fold the `campaign/nirmana-engine` work into the Nikaṣa Engine session (decision N-2) | With Nirmāṇa off, the build engine has no running campaign. |
| Land it: PR to `main`, review, deploy | 200 commits, none live. Timing, error text, run-killer and cascade fixes do nothing until deployed. |
| Apply and verify migrations 1094 (duration column) and 1095 (cascade backfill) | R55 and R38 wait on them. |
| Finish the carried items: A2b, A3b, R217 (run-level error text) | Silent failures remain otherwise. |
| C1 crash, orphan and reap; C2 stuck states | Noise in every build-history verdict until done. |
| D1 / P10: the engine judged by the Build gate's own checks (R39) | Last, by design: it only makes sense once the asset contract stops moving. |

- **Rough size:** 40–60 hours, most of it C1 and landing.

#### E4 · Landing — one branch of record

- **Today nothing Nikaṣa built is on `main`.** A fresh checkout does not have the inspector.
- **Proposed approach (decision N-3):**
  1. Split PR #2736 into a code PR (tooling, tests, ledgers) and an evidence PR (census artefacts, reports).
  2. Retarget both to `main`.
  3. Add the inspector's test suites to CI.
- After landing, every Nikaṣa change goes to `main` in small PRs.

#### Gate G1 · Engine freeze

Passes when:

1. T1–T5 pass in production tooling on `main`;
2. R24, R39 and R71 are closed;
3. R244 (`bo_upaya`) is closed, or deferred with its withholding procedure in force (decision N-6);
4. the build engine is deployed and its migrations verified;
5. tier 4 and the L0 instance are accepted.

**The native rules the freeze.**

- **Stage 1 total, rough:** 240–310 hours. It will be re-estimated after E1's first scorecard.

### 5.2 · Stage 2 — Suvarṇa L0 pilot (session "Exec Suvarṇa")

**Goal:** prove the whole elevation loop end to end on one layer, and measure what it costs.

**Steps:**

1. Run the per-layer lifecycle (§5.3) on all 40 L0 assets.
2. Rebuild L0 from scratch under the frozen engine. Re-measure. Every gap either closes or is explained.
3. Write the first real certification records.
4. Measure the effort per asset by kind (untouched, small fix, writer change, retire).
5. Write the L0 close report, and the lessons that revise §5.3.

**What makes L0 the right pilot:**

- no chart scope (one reference build, not one per chart);
- every downstream layer depends on it;
- all 40 assets were kept from Nirmāṇa;
- five briefs already exist.

**Gate G2** passes when L0 is CLOSED and the per-asset cost is measured. The native decides the rollout pace from that measurement.

### 5.3 · Stage 3 — the per-layer lifecycle (L1 → L5)

The same seven steps for every layer.

1. **Derive the layer instance** from the re-sealed tiers and the census. No invented content. Any gap is a tier defect, raised back to Strategic Suvarṇa. **The native accepts the instance.**
2. **Write one brief per asset** (tier-4 instance). It holds the census-emitted gap rows, the proposed asset-specific additions and the opportunity rows.
3. **Decide a disposition per asset.** Keep as is, fix, enrich, consolidate, retire.
4. **Implement.** Writer, migration and registry changes. This is the first stage allowed to change writers.
5. **Rebuild** through the orchestrator. Never by hand.
6. **Re-measure and certify.** The inspector re-emits; gap rows close only on PASS or justified N/A; certification records are written; the tracker marks ELEVATED.
7. **Close the layer.** From-scratch rebuild, clean re-measure, close report. **The native signs.**

**Pace rules:**

- Layers close strictly in order.
- **Bounded pipelining.** While layer N is in steps 4–7, layer N+1 may run steps 1–2 (read-only). Layer N+1's step 4 waits for layer N's close.
- **Nirmāṇa's kept assets** enter at step 2 with their current state. Their existing gap rows are the starting delta.

**What each layer brings:**

| Layer | Known specifics |
|---|---|
| L1 Gaṇita | Chart-scoped. The census measures one chart; decide whether elevation certifies one chart or several (decision N-12). |
| L2 Bodha | `bo_upaya`'s fix lands here if not earlier. Six chart-conditional rebuilds (R243) are recorded as such. 8 "writes nothing to its own table" assets need an N/A policy (R247). |
| L3 Kāla | Coordinate with the live Gochara workstream (§7). `ka_kshetra` refuses to rebuild a populated chart. Six tables are empty for the canonical chart. `kala_field` holds 10.98 million rows; census and rebuild costs are highest here. |
| L4 Phala | Nothing kept from Nirmāṇa. Three assets record 139 rows written against 4 present. |
| L5 Mīmāṃsā | Calibration fills over time by design. `lel_events` has no writer (R236). |

- **Stage 3 size:** unknown until L0 is measured. It is estimated at gate G2, not guessed now.

### 5.4 · Stage 4 — Closure

- Whole-plane re-measure against all 1,143 gate cells.
- Hand every `[TRANSFERS]` obligation to its owning plane, as recorded pending work.
- Retire leftover artefacts (dead tables such as `build_dependencies`, R219).
- Closure report. **The native accepts it.**

---

## §6 · Operating model

### 6.1 · Sessions and flow

```
Strategic Suvarṇa ──brief──► native approves ──► Nikaṣa Engine / Exec Suvarṇa
      ▲                                                  │
      └──────────── report, findings, open questions ◄───┘
```

- **Strategic Suvarṇa** writes every brief, prepares every native decision and folds strategy changes into this plan.
- **Execution sessions** run packets: build → report → gate review → corrections → fold. They never change this plan; they raise findings.
- A new session is opened only when a stage or workstream needs its own context. The plan names it first.

### 6.2 · Roles and models

| Role | Model | Rule |
|---|---|---|
| Builder | Sonnet by default; Opus for high-risk packets (ledger writes, reopens, writer changes) | Implements one packet. Never reviews its own work. |
| Gate reviewer | Opus, fresh context, read-only | Tries to break the claim. Rules ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT. |
| Independent strategic reviewer | GPT-6 Astra or Kimi | Reviews plans, briefs and rulings before the native sees them. |
| Delegated decider | Fable, only when the native delegates a named decision | Its ruling is recorded as delegated and shown to the native. |

### 6.3 · Discipline (lessons already paid for)

- **Packet, gate, fold.** No packet folds into the register without a gate verdict.
- **Proof that could fail.** Every change lands with a test that fails without it, plus a recorded mutation run.
- **Commits.** One row per commit. `git commit -- <paths>` only. Never `add -A`, never `--amend` on shared branches.
- **Fingerprints last.** Rotate after the final edit, then verify manifest and drift.
- **Ledgers.**
  - Written only by `--emit-gaps`, or by a reviewed migration script proven idempotent on a copy first.
  - Every emit uses the current withholding list (today: `bo_upaya-Idem.pattern`).
- **Register tallies are computed, never typed.**
- **Scratch files** go in a per-packet subfolder.

### 6.4 · Write authority (new in Suvarṇa)

Nikaṣa only read production. Suvarṇa changes writers and rebuilds assets.

- **Code changes:** through PRs to `main`, with review and CI.
- **Schema and data changes:** through migrations only, applied by the deploy pipeline and verified against the live database afterwards.
- **Builds:** through the orchestrator only. Never by hand-written SQL.
- **Privileged credentials** (control writers, admin roles): never used by an execution session without a named native approval.
- **Each stage brief states its write boundary.** Anything outside it is a stop condition.

### 6.5 · Environment (operational lessons)

- **Database access.** Start the Cloud SQL proxy on 5433. Use the pre-resolved read-only environment file. Never call `gcloud` per command (it hangs).
- **Power.** Long runs need the machine plugged in with the lid open. Every stall so far traced to sleep.
- **Census runs.** Run full six-layer census runs alone. Concurrent runs exhausted the connection pool once.
- **Worktrees.** One per session. Never work in the main checkout, which carries other campaigns' uncommitted state.

### 6.6 · Effort and cost

- Stage 1: 240–310 hours of build effort, rough (§5.1).
- Stages 2–4: estimated at gate G2 from L0's measured cost.
- Review effort is on top: about one gate review per packet, and more for high-risk packets.

---

## §7 · Dependencies outside the plan

| Dependency | Owner | Needed by | Status | Action |
|---|---|---|---|---|
| Build engine landed and deployed | Nikaṣa Engine, if N-2 is approved | G1 | 200 commits, no PR | E3 |
| Migrations 1094, 1095 in production | deploy pipeline | R55, R38 | not applied | E3 |
| `bo_upaya` fix (restore the delete) | L2 writer owner; with Nirmāṇa off, Suvarṇa L2 by default | R246; lifting the withholding | direction ruled, handoff written | N-6 |
| C1 crash and orphan handling | build engine | clean build-history verdicts | not started | E3 |
| L3 Gochara workstream | its own sessions | Suvarṇa L3 | active; changing `ka_gochara` | coordination rule (below) |
| Migration number ranges | Pūrṇa, Jātaka, L3 | every migration | reserved ranges exist | check reservations before numbering |

**Coordination rule with live workstreams:** before Suvarṇa touches an asset another live workstream is changing, the two agree who owns that asset for the period. Findings go both ways. The rule is recorded in the stage brief.

---

## §8 · Native decision points

In the order they are needed.

| ID | Decision | When | Recommendation |
|---|---|---|---|
| N-1 | Approve this plan (after review rounds) | now | — |
| N-2 | Fold the build-engine work (`campaign/nirmana-engine`) into the Nikaṣa Engine session | Stage 1 start | Yes. It has no running campaign, and the engine freeze depends on it. |
| N-3 | Landing approach for PR #2736: split into code and evidence, retarget to `main` | Stage 1 start | Yes. |
| N-4 | Approve each reopen agenda: T1, then T2, then T3 | E2, three times | Review each as presented. |
| N-5 | Sign each re-seal | E2, three times | — |
| N-6 | `bo_upaya`: fix in Stage 1 as a sanctioned writer exception, or defer to Suvarṇa L2 with the withholding in force | Stage 1 | Fix in Stage 1. Half a day, and it unblocks R246 and ends the withholding. |
| N-7 | Accept tier 4; accept the L0 instance | end of E2 | — |
| N-8 | Engine freeze | G1 | — |
| N-9 | L0 pilot results and rollout pace | G2 | — |
| N-10 | Accept each layer instance; sign each layer close | Stage 3, per layer | — |
| N-11 | Approve asset-specific addition classes (§2.3) | before L2, at the latest | Decide per class. |
| N-12 | Elevation certifies the canonical chart only, or several charts | before L1 | Canonical chart first; multi-chart as a recorded addition. |
| N-13 | N/A policy for "writes nothing to its own table" and "update-only" assets (R247) | before L2 | — |
| N-14 | Data findings with owners outside the inspector: `lel_events` (R236), `build_dependencies` (R219), `ka_gochara` registry (R240) | per layer | — |
| N-15 | Pace and budget: model routing, review depth, spend ceiling | Stage 1 start | — |
| N-16 | Nirmāṇa's database record: leave it reading "frozen", or supersede it with the privileged control writer | any time | Leave it. The decision is recorded in governance. |

---

## §9 · Tracking

**Weekly scorecard** (from the tracker and ledgers, never typed by hand):

- assets ELEVATED, per layer;
- certification records;
- open gap rows, by gate and layer;
- open register rows, by severity;
- T1–T5 status (Stage 1);
- effort spent against estimate, per stage.

**Per-stage burn-down** of its own rows and gates.

**Every scorecard figure names its query**, so anyone can re-run it.

---

## §10 · Adapting the plan

- **Findings change briefs, not the plan**, unless they change a stage, a gate, the standard or the end state.
- **What triggers a plan revision:**
  - a stage's estimate misses by more than half;
  - a gate criterion proves unmeasurable;
  - a new class of defect appears;
  - a native decision changes scope.
- **How:** Strategic Suvarṇa drafts the change with a changelog entry. The native approves it. The version bumps.
- **Stop rule:** an execution session that finds the plan wrong stops that packet and reports. It does not improvise.

---

## §11 · Risks

| Risk | Signal | Mitigation |
|---|---|---|
| The engine stage never ends | E2 keeps growing | Closed agendas; transcription rows deferred to Stage 3; freeze criterion fixed in §4.2. |
| Another false pass | a gap closes, then the asset fails | Only PASS or justified N/A closes; R246 detector; mutation-proven tests; gate reviews. |
| Collision with live workstreams | two sessions change one asset | Coordination rule (§7); check live work at every session start. |
| Register drift | tallies disagree with rows | Computed tallies (Stage 0). |
| Environment fragility | stalls, dropped connections | §6.5 rules. |
| Review fatigue | gates accept quickly | Fresh reviewer per packet; independent reviewers for plans and rulings. |
| Scope creep from opportunities | layers slow down | Opportunities never block; ruled in batches. |
| Stage 3 larger than expected | L0 cost per asset high | Estimate at G2 from measured data; the native sets the pace. |

---

## Appendix A · Fact baseline (2026-09-28) and sources

| Fact | Value | Source |
|---|---|---|
| Active assets | 127 | `asset_registry` where `is_active and dead_flag is not true`, grouped by layer |
| Nirmāṇa freezes | 98 (97 active) | `nirmana_evidence.nirmana_elevation_campaign_events`, `event_type='asset_frozen'`, latest per asset |
| Freezes under definition t0 | 72 of 98 | same query, by `definition_revision` |
| Delta ledger lines | 857 | `asset_gaps.jsonl` on `campaign/nikasha-test` (md5 `f6b1d3c5…`) |
| Open gaps | 799 | last state per `gap_id`, state OPEN or RE-OPENED, `kind=gap`, not superseded |
| Open gaps on kept assets | 572, across 97 of 98 assets | same, joined to the freeze list |
| Certifications | 0 | `asset_certs.jsonl` holds only its header |
| Register rows | 252; 180 open | rows counted by status cell (not the header tally) |
| Freeze blockers open | R24, R39, R71, R244 | same |
| Freeze tests | as §3.5 | `nikasha_test/PHASE6_ANALYSIS.md` §6.5 |
| Build engine | 200 commits not on `main`; no PR | `git rev-list --count origin/main..campaign/nirmana-engine`; `gh pr list` |
| Last Nirmāṇa commit | `badc3f9bc`, 2026-09-09 | `campaign/nirmana-autonomous` |
| L3 Gochara | migration 1150 applied to production 2026-09-28 | `l3/gochara-autonomous-wp0-7` log |

## Appendix B · Glossary

- **Asset** — one registered data-plane unit with a writer or a declared kind (127 active).
- **Gate** — one of the nine core checks (§2.1).
- **Gap row** — an open shortfall in the delta ledger, stating what was measured and what is required.
- **Certification record** — a verdict per gate per asset in the certification ledger.
- **Layer instance** — the tier-3 document for one layer.
- **Asset brief** — the tier-4 document for one asset.
- **Emit** — the inspector writing its measurements into the delta ledger.
- **Withholding list** — gap closures an emit must not write until a named condition holds.
- **[TRANSFERS]** — an obligation that belongs to a plane not yet built.
