---
artifact: SUVARNA_CAMPAIGN_PLAN
canonical_id: SUVARNA_CAMPAIGN_PLAN
version: "1.3"
status: "DRAFT — for native review (N-1). Review pass 1 folded; pass 2 and the independent review (L.9) still to come."
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
decision_owner: Native (Abhisek Mohanty)
supersedes: "SUVARNA_CAMPAIGN_PLAN_v1_2.md (v1.1 and v1.0 before it). Earlier: succeeds the Nirmāṇa elevation campaign (NIRMANA_SUPERSESSION_RECORD_v1_0.md, PR #2751, merged)."
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
review_disposition: briefs/suvarna/reviews/REVIEW_PASS1_DISPOSITION_v1_0.md
changelog:
  - "1.3 (2026-09-29, review pass 1 and decisions D1–D6 folded): every finding of REVIEW_PASS1_SUBSTANCE (30) and REVIEW_PASS1_CONSISTENCY (44) fixed or dispositioned (REVIEW_PASS1_DISPOSITION_v1_0.md). D1: builds dispatched through POST /api/cockpit/runs by a builder identity with a dispatch-only 'build' grant (new lane E7); L0 waves native-dispatched; deployed SHA read from the Cloud Run job image tag. D2: family assets certified from their own orchestrator-built rebuild plus Suvarṇa's re-measure; excluded from wave completion; their readers wait asset by asset; hand-back rule. D3: new lane E6 (generic gate detectors, coded check→cell rollup, N/A only by declared registry rule, non-gate criteria never block ELEVATED; §1.1(3) amended). D4: 'full-layer rebuild' defined (§1.2); L0 waves take a verified dump and a post-wave diff; N-12 before the first L0 wave. D5: runtime = supervised headless pass loop (L.14), /loop only as an interim to G2 (L.15). D6: suvarna_reader (L.10). One J1 checklist (§4.2) with a detector or a native decision per criterion. A.H waits only for each layer's instance step. Native merge and deploy latency modelled per wave. Stale-certification detection (E5.5). Track E and Track A briefs, the role/prompt sweep and tracker additions listed as launch prerequisites (§5.0b). Estimates reconciled (§5.1 = §6.6). Stale references corrected (PR #2751 merged; charter v1.2; credential; Track F; budget). The 1.2 entry's 'N-19 (charter) drafted' is corrected here: N-19 approved v1.1 the same day, amended to v1.2 (CHARTER-AMEND-A-C)."
  - "1.2 (2026-09-29, native decisions and launch readiness): the three L3 focus families move to three family sessions that each seal a final brief and implement it; Suvarṇa's L3 analysis evaluates their latest versions (N-17). Decisions N-2, N-3, N-6, N-18 approved; F-0 and F-5 decided; F-1–F-4 and F-6 delegated to the family sessions; N-19 (charter) drafted; N-20 added. New §5.0b launch readiness (what must be true before execution starts). The real-time tracker becomes the tracking surface (§9). §3 updated: register tallies repaired (v2.8), the 2026-09-28 Gochara switch and its reversal (ADK-0027), isolation set up."
  - "1.1 (2026-09-28, native review pass 1): the stage sequence becomes parallel tracks with one join. Stage 0 dissolves into first items (hours, not days). The derivability work moves off the engine path into the parallel analysis track, bringing the engine-to-freeze estimate from 240–310 to 90–150 hours. L1–L5 run as dependency waves, not layer gates. New Track F for the L3 focus families (Sangam, Kshetra, Gochara). Companion documents added: execution architecture, L3 focus families, document map, review package."
  - "1.0 (2026-09-28): first full draft. Built on a fact baseline measured the same day (Appendix A)."
---

# Suvarṇa — the data-plane elevation campaign plan

## §0 · Reading guide

### 0.1 · Names

| Name | What it is |
|---|---|
| **Suvarṇa** (सुवर्ण, gold) | The campaign. Elevates every data-plane asset, L0 → L5. |
| **Nikaṣa** (निकष, touchstone) | The engine. The system that tests and certifies an asset: four tiers, inspector, tracker, ledgers, detectors. Under N-2 (decided 2026-09-29) it also takes in the build engine it depends on. |
| **Strategic Suvarṇa** | This session. Plans, discusses, rules, writes briefs, records the native's decisions. Never executes. |
| **Nikaṣa Engine** | The session that builds and freezes the engine (Track E). |
| **Exec Suvarṇa** | The session that runs the elevation (Tracks A, I, B). |
| **L3 Gochara · L3 Saṅgam · L3 Kṣetra** | Three family sessions. Each seals a final brief for its family and implements it (N-17). Not part of the Suvarṇa swarm; not bound by its charter. |

- Suvarṇa is what the touchstone tests. The engine is finished first; the campaign runs on it.
- "Nirmāṇa" now names two things: the superseded elevation campaign, and a still-live build-engine
  branch (`campaign/nirmana-engine`). This plan calls the second one "the build engine" (§5.1, E3).
- **Tracker ids.** Items such as `E5.3` or `B.W0` are ids in `00_ARCHITECTURE/control/suvarna/plan_model.json`;
  decision ids such as `N-12` or `D1` are ids in the decisions log (§8).

### 0.2 · What this document is

- The master plan. It fixes the end state, the standard, the tracks, the gates and the operating model.
- **Companions:** `SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` (v1.3; how it runs, including the tracker, §11, and the runtime, §5.5), `SUVARNA_AUTONOMY_CHARTER_v1_0.md` (v1.3; what the swarm may decide), `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (v1.2; the three L3 families), `SUVARNA_DOCUMENT_MAP_v1_0.md` (every document in the campaign), `D6_SUVARNA_READER_RUNBOOK_v1_0.md` (the read-only login).
- Each track gets its own brief (§5.0b). A brief never contradicts this plan; if it must, the plan is revised first (§10).
- It is written to be reviewed. Every figure has a source in Appendix A.

### 0.3 · How to read it

- §1–§3: where we are going, by what standard, from where.
- §4–§5: the tracks, the join, and what each track contains.
- §6: how the work is run.
- §7–§8: what is outside our hands, and what only the native decides.
- §9–§11: tracking, change control, risks.

---

## §1 · End state

### 1.1 · Asset level

An asset is **ELEVATED** when all four hold:

1. Every core gate its layer requires carries a current `PASS`, or an `N/A` computed from a declared registry rule, in `asset_certs.jsonl` (§2.1).
2. Every asset-specific addition declared for it is certified the same way (§2.3).
3. It has no open `gap` row **on a core gate or a declared addition** in `asset_gaps.jsonl`. Rows on non-gate criteria (Cost, Count, Complete, Reach) are information, re-keyed `kind: info`, and never block ELEVATED (D3).
4. Its disposition is recorded (keep, integrate, enrich, qualify, consolidate, historical, retire, unresolved — tier 4 §0).

- **"Current"** means the certification still matches what it was measured against: the writer's commit (the job image tag of the run), the upstream certification ids, and the row-set fingerprint (§5.4 step 7; E5.5).
- An asset retired or consolidated with a recorded reason also counts as terminal.
- "Frozen by Nirmāṇa" is not elevated. It is a starting point (§3.3).
- The tracker computes ELEVATED exactly as above once E6.3 lands. Until then its `levels_elevated` detector is labelled
  `elevated (proxy)`, and nothing can be certified anyway (certification starts after J1, which requires E6.3).

### 1.2 · Layer level

A layer is **CLOSED** when:

- its layer instance (tier-3 instance) is accepted by the native;
- every active asset in it is ELEVATED or terminally dispositioned;
- a **full-layer rebuild** succeeds under the orchestrator and re-measures clean;
- the native signs the layer close (N-10.L0 … N-10.L5; tracker G3.L0 … G3.L5).

**Full-layer rebuild (D4).** One orchestrator run with `scope=layer, action=rebuild, clear_before=false` over every
active asset of the layer, for the canonical chart (L1+) or globally (L0). It is not a wipe and needs no R3 approval.
- **L1–L5:** it is from scratch for the chart (every writer deletes and re-inserts its own rows on the natural key), so
  it also proves Idem.
- **L0:** upserts never delete, so it cannot prove the absence of orphaned rows. The L0 close proof is: the
  post-rebuild fingerprint equals the pre-rebuild one, or every row in the diff is explained. A fresh build on a scratch
  database compared by fingerprint is an opportunity, not a gate. L0's rebuild is dispatched by the native (D1).
- **L2:** a non-clearing L2 MSR rebuild still cascade-deletes Saṅgam's `kala_convergence` rows through the foreign key.
  It therefore waits for F-3 (charter R1) and is reported to the family (R8).
- **L3:** the family assets are rebuilt by their family sessions (or after a hand-back, by Suvarṇa, §5.3); the
  full-layer rebuild covers the rest, dispatched over the non-family assets only (charter R8), and the layer closes only once the family assets and their L3 readers are
  certified (B.FG, B.FS, B.FK, B.FR.L3).
- **Cost:** one orchestrator run per layer, measured at G2 from the waves; it is a production-visible action with every
  charter §6 precondition.

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
| Open gap rows (core gates and additions) | 799 open rows, before the non-gate rows are re-keyed (E6.4) | 0 |
| Gate cells (9 gates × 127 assets) | 1,143 cells, 0 certified | all PASS or rule-computed N/A |

- **Gate cells are computed, never counted by hand.** One coded rollup (E6.2) turns check results into cells: the
  worst applicable check wins (FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS); a cell is N/A only when every applicable
  check is N/A by a declared registry rule; a gate with no registered check for the layer is NO_DETECTOR, never N/A; a
  criterion with `detector: NONE` can never reach PASS. Cells are versioned with the registry revision.

### 1.5 · Out of scope

- **Astrological correctness.** The data plane is data engineering and computation. Interpretive
  correctness is not a data-plane obligation (native ruling 11, 2026-09-25).
- **The retrieval and conversation planes.** Not built yet. Suvarṇa records what they must inherit; it does not build them.
- **Empirical calibration.** L5 fills its values as outcome data accrues. That is by design, not unfinished work.
- **New assets.** Suvarṇa elevates the existing 127. New assets are proposed through the opportunity register (§2.4) and ruled separately.
- **Other charts** unless N-12 adds them (§8).

---

## §2 · The standard

One elevation definition. A fixed core for every asset. Declared additions where an asset needs more.

### 2.1 · The core: nine gates

| Gate | Plain meaning |
|---|---|
| **Ldgr** — derivation ledger | Every derived value traces to the facts it came from. |
| **Idem** — idempotency | A rebuild replaces its own rows; it never accretes and never silently fails. |
| **Earn** — earned signal | Every status or verdict has a detector behind it that could read false. |
| **Null** — honest null | Where a value cannot be derived, it is null, never an invented default. |
| **Vocab** — vocabulary | Names and terms conform to the project's closed vocabularies. |
| **Carr** — source carriage | Classical sources are carried and reproduced faithfully. |
| **Narr** — narration fidelity | Any generated text restates cited facts; it never re-derives them. |
| **Dens** — serving density | What is served is layered by confidence, never flattened. |
| **Build** — buildability | The orchestrator can dispatch it, and a triggered rebuild produces the right result. |

- **Verdicts** come from a closed set: `PASS · FAIL · PARTIAL · NO_DETECTOR · N/A` (plus `ERRORED` for a failed measurement).
- **Only `PASS` or a rule-computed `N/A` closes a gap.** Anything else keeps it open. This is the lesson of every false closure found so far.
- **N/A is computed, never typed (D3).** A gate that does not apply to a layer (or to assets matching a declared
  column pattern) reads `N/A` because the inspector's registry declares that rule, with the registry's own reason. The
  native rules the applicability rules once per gate (N-22; N-13's write-nothing and update-only cases are part of it).
  No reviewer and no agent types an N/A.
- **A reviewer's opinion is not a detector.** A gate reviewer may reject a measurement; it never authors a PASS or an
  N/A. A PASS record must cite a criterion whose detector is not `NONE` and the census run that produced it (E5.1).
- **Today's gap (measured by D3's review):** the inspector registers no `Null.*` and no `Narr.*` criterion; `Carr.D1–D3`
  have no detector; `Ldgr` measures only that a citation column exists; `Dens.served` is structural. Lane E6 builds the
  generic detectors and the rollup before J1. Per-asset semantic detectors (L0 carriage, narration golden tests,
  declared null reasons) belong to Tracks A and I and gate those assets' ELEVATED; they are not J1 prerequisites.

### 2.2 · Principles every verdict obeys

- **Earned signal.** A status needs a detector that could return false (CLAUDE.md §N.8).
- **Honest null.** "I don't know" beats a plausible default (§N.7).
- **L1 is the authority.** A derived value references its L1 fact; it never restates it (§N.5).
- **Rebuild replaces.** Per-chart delete-then-insert on the natural key for L1+; upsert for L0 (§N.3).
- **Measured, not claimed.** A gap row states what was measured, with what, over which population.

### 2.3 · Asset-specific additions

- **What they are.** Requirements that apply to some assets only. Example: a grounding tier on interpretive signals, but not on ephemeris rows.
- **How they are declared.** In the asset's brief (tier-4 instance), with:
  - the requirement, in one sentence;
  - the detector that measures it;
  - why this asset needs it.
- **Who approves.** The native approves each addition **class** once (N-11). Individual assets then adopt approved classes in their briefs (§5.4 step 1).
- **The rule.** Additions add to the core. They never replace, weaken or waive a core gate.
- **The candidate pool:**

| Candidate class | Source | Would apply to | State |
|---|---|---|---|
| Grounding tier (text-direct / principle-derived / instrument-derived) | Nirmāṇa doctrine D-GROUNDING | interpretive signal classes, yoga and dosha firings, remedies | for N-11 |
| Stored salience with a protected tail | D-SALIENCE | L2 signals and their serving envelopes | for N-11 |
| One temporal voice (a single arbiter per question and range) | D-TIME | L3 temporal engines | for N-11 |
| Every asset has a consumer or a recorded disposition | D-SERVICE | all layers | for N-11 |
| **Null with a reason** (the "reason" half of Null has almost no schema carriage today) | D3 | assets whose brief declares it | **class decided by D3**; adopted per asset |

- These are adopted on their merits, one class at a time. They are not inherited from Nirmāṇa.

### 2.4 · Beyond conformance: the opportunity register

- Tier 4 §9 keeps a second kind of ledger row: `kind: opportunity`.
- It records improvements (a better algorithm, wider coverage, a cheaper build, a new synergy).
- **Opportunities never block elevation.** An asset can be ELEVATED with open opportunities.
- Opportunities are ruled in batches per layer. Adopted ones become work in that layer; the rest are recorded.

---

## §3 · Starting position (measured 2026-09-28, updated 2026-09-29)

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

- **Delta ledger** `asset_gaps.jsonl`: 857 lines. **799 open gaps.** 572 of them sit on Nirmāṇa's kept assets. Some are on non-gate criteria and will be re-keyed `kind: info` (E6.4).
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

Counted from the rows. The header tallies drifted and were repaired on 2026-09-29 (register v2.8); the tracker's detectors check them on every change (FI-3, FI-4).

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

The engine is frozen when five tests pass in production tooling and the freeze-blocking register rows are resolved
(§4.2). Rows that block a layer, degrade or are cosmetic stay open as that layer's work; they block the layer close,
not the freeze. (v1.2 said "every register row closed or explicitly deferred"; that clause is replaced here, because
the 95 layer-blocking rows are by definition layer work, not engine work.)

| Test | Last evaluated (2026-09-26, before waves 1–3) |
|---|---|
| T1 — finds what is there | PARTIAL (sandbox only) |
| T2 — does not invent what isn't there | FAIL (60 disagreements) |
| T3 — a fix closes a row | FAIL in production tooling |
| T4 — works on a layer it wasn't built against | PARTIAL |
| T5 — the pieces agree | FAIL |

- **These have not been re-measured since the three waves of fixes.** Most defects behind T2 and T3 are now closed. A fresh, machine-readable scorecard is the first step of Track E (E1.1).

### 3.6 · The documents

- **Tiers 1–3:** sealed. A reopen agenda is ruled (D2 of the Nikaṣa rulings, 2026-09-27): 32 clause fixes across the three documents (§5.1, E2), plus the derivability mechanisms Track A will harvest (§5.2); both go into one reopen at J1.
- **Tier 4:** draft, pending your acceptance (N-7.T4).
- **L0 layer instance** (v3.0): draft, pending your acceptance (N-7.L0).
- **Asset briefs:** 5 L0 pilots. No other layer has an instance or briefs.

### 3.7 · Where the code is

- **Nikaṣa tooling** lives on `campaign/nikasha-test` (PR #2736). It is **not on `main`**. The PR targets
  `l3/kala-layer-briefs`, not `main`, and adds about 154,000 lines (mostly census artefacts). N-3 (decided) splits it.
- **The build engine** lives on `campaign/nirmana-engine`: about 200 commits not on `main`, no PR.
  - Closed: A1 (timing), A2 (error text), A3 (run-killer), B1 (cascade reporting), B2 (downstream count).
  - Not started: C1 (crash and orphan handling), C2 (stuck states), D1 (the engine judged by the Build gate).
  - Migrations 1094 and 1095 are not in production.
  - Nothing from it is deployed.
- **The build dispatch path** (measured by D1's review): `/api/build/start` is decommissioned; builds are created by
  `POST /api/cockpit/runs`, which needs chart write permission (owner or `super_admin`). Writers run in the Cloud Run job
  `brahma-build-pipeline-job`, whose image tag is the deployed commit.

### 3.8 · Live work elsewhere

- **L3 Gochara workstream** (`l3/gochara-autonomous-wp0-7`, PR #2731 open). It applied a production migration (1150) to `ka_gochara`. On 2026-09-28 it switched the canonical chart to `'4.0'` before the deploy-before-switch directive (F-0) arrived, and reversed it six minutes later; nothing consumed the switched data (ADK-0027). It is rebuilding the full century under `'4.1'`; the native has put its production execution on hold.
- **Three L3 family sessions** (from 2026-09-29): Gochara, Saṅgam and Kṣetra each seal a final brief and implement it (N-17). Saṅgam's session is running.
- **Pūrṇa**, **Jātaka**: separate campaigns with their own migration reservations. They and the families also deploy to `main`.
- **D6** (the read-only login `suvarna_reader`): three production dry runs done, all rolled back; the deploy-gate amendment (PR #2756) merged 2026-09-29; the apply follows its deploy. Until then the Monitor's `credential_readonly` check blocks, which is correct (L.10).

---

## §4 · The shape: parallel tracks, one join, dependency waves

```
NOW ─┬─ TRACK E  Engine: tools · build engine · clause fixes · bo_upaya · landing ·            ─┐
     │           execution tooling (E5) · gate detectors (E6) · build identity (E7)             │
     │                                                                                          │
     ├─ TRACK A  Analysis, all six layers at once (read-only):                                 ├─► JOIN J1
     │           census + layer-instance drafts (tier gaps) → harvest ──────────────────────────│   combined reopen
     │           asset briefs (provisional) · dispositions · fix designs → revalidated after J1 │   + ENGINE FREEZE (native)
     │                                                                                          │
     └─ TRACK F  L3 families: Gochara · Saṅgam · Kṣetra — run by three family sessions,        │
                 unbound by J1; Suvarṇa evaluates, then certifies what they build (D2)         ─┘
                                                                                                │
     TRACK I  Implementation: fixes for every layer, in parallel lanes  ◄───────────────────────┤
              (tier-independent fixes may start before J1; merged-complete only after it)       │
                                                                                                │
     TRACK B  Rebuild and certify: one wave per dependency level, in order  ◄───────────────────┘
              wave n = its fixes merged to main and deployed (native merge) → dispatch → certify
              ├─ family assets and their readers: outside wave completion, certified asset by asset
              ├─ checkpoint G2 after levels 0–2 (the wide top, mostly L0/L1): loop proven, cost measured
              └─ layer closes as each layer's last asset certifies (native, batched)

     CLOSURE  whole-plane re-measure · [TRANSFERS] hand-over · closure report (native)
```

### 4.1 · Why this shape

- **Only data forces order.** Analysis, design and coding do not change data, so they run across every layer at once. Only rebuilding has to follow the dependency map.
- **The engine freezes before anything is certified.** Every wave of fixes so far found at least one path that could close a gap without a real measurement: a failed count query read as "not applicable", never-started build rows counted as runs, `ka_kshetra` passing on a refused rebuild, `bo_upaya` passing on a rebuild that cannot succeed. Certifying before the freeze would bake those in.
- **One reopen, not six.** The clause fixes are already known. The derivability machinery is best discovered by drafting every layer's instance. So Track A harvests what is missing, and both go into one reopen per document at J1. The harvest needs only each layer's census and instance draft, not its briefs.
- **Asset waves, not layer gates.** Many L3 assets need only L0 and L1. They rebuild as soon as those are certified, without waiting for L2.
- **Fix first, walk once.** The dependency map is 27 levels deep and ends in a long thin chain. That chain is the critical path; parallelism cannot shorten it. So every asset's fixes land (merged and deployed) before it is rebuilt, and the chain is walked once (execution architecture §6).
- **L0 still goes first**, because it sits at the top of the map. Its certification is the first proof that the full loop works: find, fix, rebuild, certify. That has never happened yet; there are zero certification records today.

### 4.2 · The gates

| Gate | Passes when | Who rules |
|---|---|---|
| **J1 · Engine freeze** | every item of the J1 checklist below is done | **native** (N-8) |
| **G2 · Loop proven** | dependency levels 0–2 certified (family assets excluded, D2); cost per asset measured; §5.4's lifecycle confirmed or revised | **native** (N-9); a checkpoint, not a stop, unless the native halts |
| **G3.Lx · Layer close** | that layer CLOSED (§1.2) | **native**, batched (N-10.L0 … N-10.L5) |
| **G4 · Campaign complete** | §1.3 | **native** (N-CLOSE) |

**The J1 checklist.** One list, the same in this plan, the tracker (`J1.6` depends on each item) and the Nikaṣa Engine
brief. Each criterion is proven by a detector or by a native decision, never by a typed "done".

| # | Criterion | Tracker item | Proven by |
|---|---|---|---|
| 1 | T1–T5 pass in production tooling on `main` | E1.7 | detector: machine-readable scorecard on `main`, every test PASS |
| 2 | R24 closed (production L3 census R134 and clean re-runs; R40 and R41 are already closed) | E1.8 | detector: register row closed |
| 3 | R39 closed (the engine judged by its own Build checks) | E3.6 | detector: register row closed |
| 4 | R71 closed through the combined reopen | E2.2 | detector: register row closed |
| 5 | R244: the `bo_upaya` fix merged; the row closed, or deferred with withholding until its L2 wave proves it (N-6 still holds: the fix is made now; only the live proof waits, because a live rebuild before J1 would need inputs that cannot be certified before J1) | E4.2 | detector: register row CLOSED, DONE or DEFERRED |
| 6 | No other freeze-blocking row open | J1.R | detector: every BLOCKS_FREEZE row closed (R244 may be DEFERRED) |
| 7 | Combined reopen: each agenda approved and each tier re-sealed, T1 → T2 → T3 | J1.1a–J1.3 | native: N-4.T1–T3, N-5.T1–T3 |
| 8 | Tier 4 accepted; the L0 layer instance accepted | J1.4, J1.5 | native: N-7.T4, N-7.L0 |
| 9 | Build engine landed, its migrations applied, and deployed | E3.2, E3.3, E3.7 | detectors: landing PRs merged; `_migrations_applied` rows 1094, 1095; the job image tag contains the landing |
| 10 | Nikaṣa tools and ledgers on `main`, inspector tests in CI | E4.1, E4.1c | detectors: files on `main`; the CI workflow runs the inspector tests |
| 11 | E5 execution tooling (certification writer, fold script, level-wave script, per-entry fingerprint rotation, stale-certification detector) on `main`, tested and reviewed | E5.1–E5.5 | detector: files on `main` (paths pinned by the Track E brief) |
| 12 | D3 gate detectors: every core gate × layer has an auto-measured detector or a declared N/A rule; rollup coded; ELEVATED exact; non-gate rows re-keyed | E6.3, E6.4, E6.5 | detectors: registry coverage check; files on `main`; no open gap on a non-gate criterion |
| 13 | Build identity (D1) provisioned; the Monitor's builder-scope check green; the level-wave script tested against it; the reader login (D6) applied | E7.3, E5.3, L.10 | detectors: Monitor checks `builder_scope` and `credential_readonly` |
| 14 | Tracks I and B brief approved | J1.0 | native: N-24 |

- **R244 and the J1 loop.** A live `bo_upaya` rebuild is a production build; before J1 no upstream is certified, so
  charter §6 precondition 6 cannot hold. J1 therefore takes the fix (merged, tested on fixtures) and leaves the live
  proof to `bo_upaya`'s own wave (B.U), where R244 closes and the withholding lifts. R246 (E1.6) waits for the merged
  fix, not the live rebuild.

---

## §5 · Track detail

Each track becomes its own brief. Briefs are written in Strategic Suvarṇa and approved by the native (§5.0b).

### 5.0 · First items (hours, not a stage)

| Item | Why | State |
|---|---|---|
| Relay F-0 and R240 to the L3 Gochara workstream (FI-1) | They were changing `ka_gochara` in production | **done** 2026-09-28 (ADK-0027) |
| Merge PR #2751, the Nirmāṇa supersession (FI-2) | A fresh session must find the decision first | **done** 2026-09-29 (merged; decision FI-2) |
| Fix the register's header tallies (FI-3) | They drifted (190 recorded vs 180 counted) | **done** 2026-09-29 (v2.8; detector-checked) |
| Repair the rows that break the register table (FI-4) | Tools misread them | **done** 2026-09-29 |
| Record Suvarṇa in `CURRENT_STATE` on `main` (FI-5) | Same reason as the supersession | **done** (detector) |
| Name the sessions (FI-6) | Strategic Suvarṇa · Nikaṣa Engine · Exec Suvarṇa | **done** |
| Relay to the three family sessions, as a report (FI-8) | D2's certification condition (an orchestrator-run build, not a cutover script); F-3 is recorded `decided` only by Strategic Suvarṇa with the native's words; the census lock and the corrected census command; record the tier-4 template revision each brief follows | open |

### 5.0b · Launch readiness — what must be true before execution starts

Execution starts when the native approves the v1.3 set (N-1, FI-7). The tracker's FI-7 waits for every row marked
**N-1 prerequisite**.

| Item | Tracker | Owner | State (2026-09-29) | N-1 prerequisite |
|---|---|---|---|---|
| This plan (v1.3), charter v1.3, architecture v1.3, focus families v1.2, plan model | L.1, L.8 | Strategic Suvarṇa | this revision | yes (via L.8) |
| Autonomy charter | L.2 | Strategic Suvarṇa | **approved** v1.1 (N-19); amendments A–C → v1.2 (CHARTER-AMEND-A-C); v1.3 folds D1–D5 and corrections, confirmed with N-1 | yes |
| Role prompts (shared rules + 9 roles) | L.3 | Strategic Suvarṇa | **done** (`roles/ROLE_*_v1_0.md`) | — |
| Runbook and start prompts | L.4 | Strategic Suvarṇa | **done** (`SUVARNA_RUNBOOK_v1_0.md`, `prompts/*_START_PROMPT_v1_0.md`) | — |
| Isolation: `/Users/Dev/suvarna`, branches `suvarna/hq`, `suvarna/trunk` | L.5 | Strategic Suvarṇa | **done** | — |
| Monitor: environment checks and repair | L.6 | Strategic Suvarṇa | **done** (8 checks, including `credential_readonly`) | — |
| Read-only credential file (N-20) | L.7d, L.7 | native | **done**: `~/.config/suvarna/pgenv.sh`, mode 600 | — |
| D6 deploy-gate amendment | L.10a | native merges | **done**: PR #2756 merged 2026-09-29 | yes |
| `suvarna_reader` applied; the credential file uses it; Monitor `credential_readonly` ok (D6) | L.10 | native runs the admin script | three production dry runs done (rolled back); apply after #2756 deploys | yes |
| **Track E and Track A briefs:** packet list, write set and boundary per lane; asset-brief approval (§5.4 step 1); pins the detector paths and landing PR numbers the plan model leaves open | L.11 | Strategic Suvarṇa | to write | yes |
| **Role, prompt, runbook and review-package sweep** to the v1.3 set (every pass-1 finding deferred there, REVIEW_PASS1_DISPOSITION) | L.12 | Strategic Suvarṇa | to do | yes |
| **Tracker additions:** the v1.3 detector types, family-aware `levels_elevated`, the hq commit lock | L.13 | Strategic Suvarṇa | to build | yes |
| **Interim runtime safeguards (D5a):** stateless Conductor passes, permission allowlist (`dontAsk`, never bypass), watchdog alerting, power and OS-restart settings | L.15 | Strategic Suvarṇa | to build | yes |
| **Durable runtime (D5b):** supervised headless `claude -p` pass loop | L.14 | Strategic Suvarṇa | to build | no: needed before B.W1 (after G2) |
| Budget ceilings (N-15) | — | native | **decided: none**; spend is reported | — |
| Two or three review passes of the plan set | L.8 | Strategic Suvarṇa | pass 1 folded (this revision); pass 2 next | yes |
| Independent third-party review, findings folded | L.9 | GPT-6 Astra, extra-high (INDEPENDENT-REVIEWER) | after L.8, L.11, L.12 | yes |

- **No session starts before N-1** (ENGINE-EARLY-START), including the Nikaṣa Engine session.
- **Track I and B brief** is written after J1's design inputs exist and approved before J1 (J1.0, N-24).

### 5.1 · Track E — the engine (session "Nikaṣa Engine")

Seven lanes, running in parallel within the caps. Lanes branch from the track's source branch (arch §12.2).

**E1 · Tooling.**
1. **Measure before changing.** Re-run T1–T5 on today's tooling and publish a machine-readable scorecard (E1.1).
2. **Close the remaining tooling rows:**
   - detector gaps R245, R248, R249, R250 (E1.2);
   - provenance: R226 (`--live` re-derive-and-diff), R228 (stale source references), R229 (unowned tables) (E1.3);
   - ledger identity: R251 (the rest of the crosswalk) (E1.4);
   - R24: the production L3 census (R134) and clean re-runs after the fixes (E1.8);
   - waiting on others: R55 (needs migration 1094, E1.5) and R246 (needs the merged `bo_upaya` fix, E1.6).
3. **Prove it again.** Re-run T1–T5 on `main` (E1.7).
- **Rough size:** 30–50 hours.

**E2 · The clause fixes.**
- The 32 rows the D2 Nikaṣa ruling already agreed, drafted per document and held for the combined reopen at J1 (E2.1).
- R71 (the `[TRANSFERS]` contradiction) closes through that reopen (E2.2).
- **Rough size:** 20–30 hours.

**E3 · The build engine.**
- Bring the `campaign/nirmana-engine` work under this track (N-2, decided).
- Land it: split into reviewable PRs to `main` (the Track E brief pins their numbers), review, the native merges, deploy (E3.2, E3.7).
- Apply and verify migrations 1094 and 1095 (E3.3).
- Finish the carried items: A2b, A3b, R217 (E3.4).
- C1 (crash and orphan handling) and C2 (stuck states): **not required for the freeze.** They reduce noise, so they run alongside Track B (E3.5).
- D1/P10 (R39): the engine judged by its own Build checks, last (E3.6).
- **Rough size:** 40–70 hours to the freeze (raised from 30–50: about 200 commits have never been reviewed); C1 and C2 afterwards.

**E4 · Landing and the `bo_upaya` fix.**
- Split PR #2736 into code and evidence PRs, retarget both to `main`, and add the inspector's tests to CI (N-3; E4.1, E4.1c).
- **Ledger cut-over (E4.3):** freeze folds on `campaign/nikasha-test` at a named cut; land the ledgers last; check line
  count and md5 equal across the old and new locations; re-point the tracker's `NIKASHA_ROOT` in one step.
- Fix `bo_upaya` as a sanctioned writer exception (N-6: fix now): about half a day. The fix is merged and tested on
  fixtures here (E4.2); the live proof comes in its L2 wave (B.U).
- **Rough size:** 10–20 hours.

**E5 · Execution tooling.** Nothing exists yet for:
- **E5.1** writing certification records to `asset_certs.jsonl` (reviewed, idempotent on a copy first; §6.3). Each
  record carries what it was measured against: the run's job image tag, the writer file hashes, the upstream
  certification ids, the row-set fingerprint, and the census run id. A PASS must cite a criterion whose detector is not
  `NONE`.
- **E5.2** the fold script (register row states, ledger emit with the withholding list, computed tallies, fingerprints, drift).
- **E5.3** the level-wave script: dispatch through the builder identity (`suvarna-build`, E7); read the job image tag
  and the deployed web SHA (`suvarna-build --preflight`); re-check the writer file hashes at dispatch; read-only check of
  the orchestrator's per-chart lock; for an L0 wave, the pre-wave dump, its verification, the post-wave diff and the
  measured impact statement (§6.4b); verify once how staleness propagates on a global (no-chart) run, and record which
  case holds. Tested against the builder identity.
- **E5.4** per-entry manifest fingerprint rotation (`manifest_fingerprint.py` restamps only the root).
- **E5.5** the stale-certification detector: a certification whose recorded writer hash, upstream certification ids or
  row-set fingerprint no longer match is invalidated, and the asset returns to re-measure (§5.4 step 7).
- **Rough size:** 30–50 hours (was 15–25; D1, D4 and stale-certification detection added).

**E6 · Gate detectors (D3).**
- **E6.1** Applicability per criterion (`layers:` and optional column pattern), so N/A is computed from the registry;
  the native rules the per-gate rules once (N-22). Generic detectors: Null (schema defaults, writer literal fallbacks,
  constant columns; never PASS alone), Dens (declared contract **and** a tier or confidence column in the served select;
  structural, and says so), Ldgr (L0 source presence; L1 computation provenance; L2+ constituent resolution generalised
  from `msr_referential_integrity.py`), Carr per layer (L1 = the existing verification tier), `Earn.literal_lint`
  (`check_earned_signal.py`) and a real `Earn.service_state`. The three existing narration lints wired in as Narr.
- **E6.2** the check → cell rollup, in code (§1.4).
- **E6.3** ELEVATED computed exactly as §1.1, on `main` (the Nikaṣa tracker's function; the Suvarṇa tracker calls it);
  the dependency-level map and the family set (`FAMILY_ASSETS.json`, with the readers) snapshotted and versioned at J1;
  wave ranges derived from the snapshot; a cycle is an error.
- **E6.4** non-gate criteria (Cost, Count, Complete, Reach) re-keyed to `kind: info` by a reviewed, idempotent ledger
  migration (the R81 pattern); `Complete.depth`'s never-populated columns feed the Null detector as evidence.
- **E6.5** the registry coverage check (the J1 criterion): for every core gate and every layer, an auto-measured
  detector or a declared N/A rule; no required core-gate criterion with `detector: NONE`.
- **Rough size:** 50–90 hours. **Not included:** per-asset semantic detectors (about 60 assets × 1–3 h = 60–180 h),
  which belong to Tracks A and I.

**E7 · Build identity (D1).**
- **E7.1** a small auth PR (security-reviewed): `chart_grants.permission` also allows `'build'`; a build grant
  satisfies dispatch on `POST /api/cockpit/runs` and nothing else; `clear_before`, the clear routes, `layer=brahmagyan`
  and every other chart stay forbidden to it (tests prove each); plus an authenticated
  `GET /api/cockpit/runs/preflight` returning `{job_image_tag, deployed_sha}`. The native merges; it deploys.
- **E7.2** the native provisions the builder: one service account (`profiles` role `guest`, status `active`), one grant
  row `(482012f1…, builder, 'build')`, its secret in `~/.config/suvarna/builder.env` (mode 600), and the
  `~/.config/suvarna/bin/suvarna-build` script (mode 700) that prints only `{run_id, plan, asset_count, job_image_tag}`.
- **E7.3** the Monitor's `builder_scope` check (profile guest and active; grants exactly `{(482012f1,'build')}`) green.
- **L0 waves are dispatched by the native** from the cockpit, at the Build operator's parked request with the
  pre-check, dump and impact statement attached. The builder never holds `super_admin`.
- **Rough size:** 8–15 hours, plus the native's merge and provisioning.

- **Track E total to the freeze: roughly 190–325 hours of agent effort** (E1 30–50 · E2 20–30 · E3 40–70 · E4 10–20 ·
  E5 30–50 · E6 50–90 · E7 8–15), split across parallel lanes. Native and deploy latency is on top (§6.6). The
  derivability work sits in Track A; it is not removed, only taken off the engine's path.

### 5.2 · Track A — analysis, all layers at once (session "Exec Suvarṇa")

Read-only. Runs across all six layers from day one (after N-1).

For each layer, three tracker items:
1. **A.Lxi — census and layer-instance draft.** A fresh census with today's inspector, provisional until J1. A draft
   instance derived from the tiers and the census. Wherever the tiers do not supply what the draft needs, record it as a
   **tier gap**. Do not invent. **This is all the harvest (A.H) and J1 wait for.**
2. **A.Lx — asset briefs, dispositions, fix designs.** One provisional brief per asset (gap rows, proposed additions
   with their detectors, opportunities), a disposition per asset (keep, fix, enrich, consolidate, retire), and fix designs
   marked **tier-independent** (can be built before J1) or **tier-dependent** (waits for the reopen).
3. **A.Lxr — revalidation after J1.** Re-measure with the frozen inspector; revalidate each brief against the re-sealed
   tiers and the frozen registry; for L3, map the family briefs onto the post-J1 tier-4 template (they were sealed on the
   draft template).

**L3's evaluation of the family briefs is part of A.L3, off the J1 path.**

**What it feeds:** the tier-gap harvest → the combined reopen at J1; fix designs → Track I.

- **Rough size:** the derivability work priced at about 157 hours in the register; briefs about 127 × 1–2 h ≈ 130–250 h;
  revalidation about 30–65 h; per-asset semantic detectors 60–180 h (shared with Track I). Spread across up to six
  analysts, with the Architect on the derivability mechanisms. Re-estimated after the first layer's drafts.

### 5.3 · Track F — the L3 focus families

Gochara, Saṅgam and Kṣetra get dedicated algorithm and enrichment work, beyond conformance to the nine gates.

- **Run by three family sessions (N-17, 2026-09-29).** L3 Gochara, L3 Saṅgam and L3 Kṣetra each verify their family's state, bring its rulings to the native (Saṅgam: F-2, F-3, F-6; Kṣetra: F-1, F-4), write a final brief on the tier-4 template, have it independently reviewed, get it sealed by the native, and implement it. They are **not** gated by J1 and may change production while Suvarṇa waves run. Start prompts: `prompts/L3_{GOCHARA,SANGAM,KSHETRA}_FINAL_BRIEF_PROMPT_v1_0.md`.
- **Suvarṇa does not change their code or data** (charter R8). Its L3 analysis evaluates their latest briefs and re-measures their assets independently. Their claims are evidence, not verdicts.
- **How a family asset is certified (D2).** The family's own orchestrator rebuild counts as the Build exercise, **only if** it was an orchestrator run on the canonical chart whose substep plan completed; a hand-run cutover script does not count. Suvarṇa's independent re-measure then writes the certification (B.FG, B.FS, B.FK). No Gochara certification before F3.G.
- **Waves and families (D2).** The family set (charter R8) and the assets that read it (16 readers measured, 3 of them family assets themselves) live in one versioned file, `FAMILY_ASSETS.json`, frozen at J1 (E6.3). Family assets and their readers are **excluded from every wave's completion**: a wave completes without them. Each reader waits asset by asset for its family input to be certified, shows `waiting_on_family`, and is certified under B.FR.L3, B.FR.L4 or B.FR.L5. So B.W0 and G2 never wait on a family session.
- **Two couplings still bind Suvarṇa:** Saṅgam and Kṣetra rebuild only on Gochara's new generation; and **no L2 MSR asset is rebuilt until F-3 (the cascade lock) has a `decided` line in the decisions log** (F3.LOCK; delegated is not decided). Strategic Suvarṇa records it with the native's words, superseding the delegation; the family session never records it. D2 steers F-3 toward a foreign-key change that removes the cascade: a sequencing rule would force a Saṅgam rebuild after every later L2 rebuild. Either way, Saṅgam is certified only after the L2 chain is certified (B.FS waits for B.W2).
- **Hand-back (D2).** When a family session closes, the native records a hand-back decision (HB-G, HB-S, HB-K) that moves that family's assets out of the R8 set, with the family's rebuild runbook attached. From then on they are ordinary Suvarṇa assets. Until then, a rebuild a family asset needs (for example after an upstream change) is parked with lead time by the Steward.
- **Kṣetra is on the L5 critical path.** `mi_bhara` and `mi_sankalpa` read it; Kṣetra is 5–9 weeks from a correct, published field. The native either accepts that, or dispositions those two readers `qualify` pending Kṣetra — a recorded, reversible disposition, never an N/A on Build (N-21).
- **The families report to the tracker** under items F1.G/F1.S/F1.K (sealed briefs) and F3.G/F3.S/F3.K (implemented).
- **Background:** `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (v1.2) reconciles each family's state and prices "fully enriched".

### 5.4 · The per-asset lifecycle (Tracks I and B)

1. **Brief approved:** disposition, fixes, any asset-specific additions. **Who approves:** the Steward, when the
   disposition is keep, fix, enrich or qualify and every addition belongs to a class the native approved (N-11) — charter
   G16, proposed with this revision; the native, batched per layer, for retire, consolidate, historical, any output
   change (charter R5) and any addition outside an approved class. Until G16 is approved, the native approves every brief.
2. **Implement** in a lane: writer, migration or registry change, with a failing-first test. This is the first stage allowed to change writers.
3. **Gate review,** then merge to `suvarna/trunk`.
4. **Land:** the wave's fixes go to `main` in one PR per wave group, which the native merges; the deploy follows (B.W0M … B.W5M).
5. **Wait for the wave:** every upstream asset certified and current, every asset at this level merged and deployed.
6. **Rebuild** in that level's wave, through the orchestrator (the native dispatches L0 waves).
7. **Re-measure and certify.** Gap rows close only on PASS or rule-computed N/A. Certification records are written. The tracker marks the asset ELEVATED.
8. **If something upstream changes later** (including a family session's or another workstream's change), the
   stale-certification detector (E5.5) invalidates the certification; Exec Suvarṇa re-measures the asset and rebuilds
   it only if its output changed. For a family asset before its hand-back, the Steward parks the rebuild for the family.

**Nirmāṇa's kept assets** enter at step 1 with their current state; their open gaps are the starting delta.

**What each layer brings:**

| Layer | Known specifics |
|---|---|
| L0 | Global, no chart. Top of the map. The first certifications. Waves native-dispatched with a dump and diff (§6.4b). |
| L1 | Chart-scoped. Canonical chart only, unless N-12 adds others (ruled before the first L0 wave). |
| L2 | `bo_upaya`'s live proof (B.U). Six chart-conditional rebuilds (R243) are recorded as such. The L2 MSR waves wait for F-3 (F3.LOCK). |
| L3 | The three families are owned by their family sessions; Suvarṇa evaluates and certifies them (§5.3). Six tables empty for the canonical chart. `kala_field` holds 10.98 million rows, so the heaviest census and rebuild costs are here. |
| L4 | Nothing kept from Nirmāṇa. Three assets record 139 rows written against 4 present. |
| L5 | Calibration fills over time by design. `lel_events` has no writer (R236). `mi_bhara`, `mi_sankalpa` wait on Kṣetra (N-21). |

### 5.5 · Closure

- Whole-plane re-measure against all 1,143 gate cells.
- Hand every `[TRANSFERS]` obligation to its owning plane, as recorded pending work.
- Retire leftover artefacts, such as the dead `build_dependencies` table (R219).
- Closure report. **The native accepts it.**

---

## §6 · Operating model

### 6.1 · Sessions and flow

```
Strategic Suvarṇa ──brief──► native approves ──► Nikaṣa Engine / Exec Suvarṇa
      ▲                                                  │
      └──────────── report, findings, open questions ◄───┘
```

- **Strategic Suvarṇa** writes every brief, prepares every native decision, records the native's rulings in the decisions log, and folds strategy changes into this plan.
- **Execution sessions** run packets: build → report → gate review → corrections → fold. They never change this plan; they raise findings.
- A new session is opened only when a track needs its own context. The plan names it first. The three L3 family sessions are the first such case (§5.3).
- **Isolation.** The campaign runs in its own folder (`/Users/Dev/suvarna/`), on its own branches (`suvarna/hq`, `suvarna/trunk`, lane branches), with its own hold switch. Other campaigns continue untouched. Details: execution architecture §2.

### 6.2 · Roles and models

The full swarm is in the execution architecture (§3). In short:

- **Opus 5.5** where judgement decides the outcome: conductor, steward (delegated decisions), architect (algorithms and derivability), gate reviewers.
- **Sonnet 5** for volume: analysts and builders.
- **Scripts** for bookkeeping: tallies, folds, dispatch, monitoring.
- **Effort:** medium by default; high only for algorithm design, high-risk reviews, reopen drafting, the Steward's rulings, and writer or ledger changes; low for mechanical roles. The execution architecture §3.1 names the same set.
- **Independent reviewers** (GPT-6 Astra or Kimi) for plans, track briefs and rulings.
- **A delegated decider** (Fable) only when the native delegates a named decision.

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

- **Code changes:** through PRs to `main`, with review and CI. The native merges.
- **Schema and data changes:** through migrations only, applied by the deploy pipeline and verified against the live database afterwards.
- **Builds:** through the orchestrator only, dispatched by the builder identity (D1, E7) for the canonical chart, without `clear_before`. Never by hand-written SQL. L0 waves are dispatched by the native.
- **Credentials:** agents read production only as `suvarna_reader` (D6). The builder credential is the one permitted non-read credential, used only through `suvarna-build`. Any other privileged credential needs a named native approval.
- **Each track brief (§5.0b) and each asset brief states its write boundary.** Anything outside it is a stop condition.

**6.4b · L0 wave safety (D4).** L0 tables are global: an L0 wave changes the inputs of every chart, while only the
canonical chart's L1+ is rebuilt. So every L0 wave:
- takes a `pg_dump --format=custom` of each affected L0 table first (about 1.08 GB for all 37 today), verified by
  `pg_restore --list` (the table list equals the affected set) and by row counts equal to the pre-wave fingerprint; if
  the dump cannot be made or verified, the wave does not run (fail closed, park);
- states its impact, measured not asserted: the L0 assets whose output changed, and per other chart the downstream
  assets flipped to stale (or, if a global run does not propagate staleness, the computed downstream closure); today the
  other charts with L1+ rows are `1c826d5a` and `cb73cd3d`;
- after the wave, files a row-level diff on the natural keys (read-only, both directions);
- reversal: hold; the native chooses a surgical revert migration generated from the diff (preferred) or a restore from
  the dump. Both are native-run. The dump is purged after the level certifies and the diff is filed.
- N-12 is decided before the first L0 wave (B.N12).

### 6.5 · Environment (operational lessons)

- **Database access.** Start the Cloud SQL proxy on 5433. Use `~/.config/suvarna/pgenv.sh` (N-20), which logs in as `suvarna_reader` once D6 is applied. Never call `gcloud` per command (it hangs).
- **Power.** Long runs need the machine plugged in with the lid open and automatic OS restarts off. Every stall so far traced to sleep.
- **Census runs.** One census at a time across every session, the families included, through the lock:
  `python -m suvarna_tracker.census_lock --emit -- <census command>` (exit 75 means another census holds it).
- **Worktrees.** One per lane (arch §12.2). Never work in the main checkout, which carries other campaigns' uncommitted state, and never in another campaign's checkout.

### 6.6 · Effort and cost

- **Track E to the freeze:** roughly 190–325 hours of agent effort, E5, E6 and E7 included, across parallel lanes (§5.1).
- **Launch items:** L.11–L.15 roughly 25–45 hours (track briefs, sweep, tracker additions, runtime).
- **Track A:** about 157 hours of derivability work, 130–250 hours of briefs, 30–65 hours of revalidation, spread across up to six analysts; re-estimated after the first layer.
- **Track F:** priced in the L3 focus-families document; spent by the family sessions, not by Suvarṇa.
- **Tracks I and B:** order of hundreds of agent-hours (10²–10³), including 60–180 hours of per-asset semantic detectors; no defensible figure until G2 measures cost per asset.
- **Native and deploy latency, separate from agent hours:** each PR to `main` waits for the native's merge, then a deploy (about 15–30 minutes each). Before J1: the Track E landing PRs (E3, E4, E7), about 6–10 merges. In Track B: one merged-and-deployed PR per wave (6 waves) plus L0 waves the native dispatches. Every native decision adds its own latency; the Steward requests each one with lead time (charter §7).
- **Hours are agent effort, not calendar time.** Parallel lanes compress the calendar; the build chain does not compress (execution architecture §6).
- **Review effort is on top:** one gate review per packet, deeper for high-risk packets.

### 6.7 · Runtime (D5)

- **Interim, from launch to G2:** `/loop` in the two execution sessions, re-armed by the native each week (its
  scheduled tasks expire after 7 days), with the L.15 safeguards in place.
- **Durable, before B.W1:** the Conductor runs as a supervised headless loop of stateless passes
  (`claude -p` with the Conductor prompt and `--permission-mode dontAsk` against an explicit allowlist; never a bypass
  mode). Each pass reads the role files, the queue and the decisions log, and commits the queue before it ends. The
  Monitor's watchdog relaunches a stalled pass (heartbeat older than three loop intervals; at most three restarts an
  hour, then the hold and a park). Sessions roll over on a pass count or context threshold. Lane agents run as separate
  processes in their own worktrees. A usage-limit pause is read and waited out, never restart-looped; whether to bill the
  runner by API key is a native decision (N-23). Details: execution architecture §5.5.

---

## §7 · Dependencies outside the plan

| Dependency | Owner | Needed by | Status | Action |
|---|---|---|---|---|
| Build engine landed and deployed | Nikaṣa Engine (N-2) | J1 | about 200 commits, no PR | E3 |
| Migrations 1094, 1095 in production | deploy pipeline | R55, R38 | not applied | E3 |
| `bo_upaya` fix (restore the delete) | Suvarṇa, Track E (N-6: fix now) | R246; the withholding | direction ruled, handoff written | E4 |
| C1 crash and orphan handling | build engine | clean build-history verdicts | not started | E3 |
| `suvarna_reader` (D6) | native (admin script) | every read; J1 | gate amendment merged (#2756); apply next | L.10 |
| Builder identity (D1) | native merges E7.1, provisions E7.2 | Track B | not started | E7 |
| L3 family sessions (Gochara, Saṅgam, Kṣetra) | their own sessions (N-17) | L3 evaluation; family certification; L2 MSR rebuilds (F-3) | briefs being written; Gochara production on hold | they report to the tracker; Suvarṇa never changes their assets |
| Migration numbers | Pūrṇa, Jātaka and L3 hold reserved ranges | every migration | Suvarṇa has no range | reserve one number at a time (arch §12.5) |

**Coordination rule with live workstreams:** before Suvarṇa touches an asset another live workstream is changing, the two agree who owns that asset for the period (a lease, arch §12.4). Findings go both ways. The rule is recorded in the track brief. The family sessions are not bound to notify Suvarṇa of their changes; the pre-wave fingerprint and the stale-certification detector are the tripwires.

---

## §8 · Native decision points

In the order they are needed. **Status is read from the authoritative decisions log**
(`$SUVARNA_HOME/run/DECISIONS.jsonl`, written only through `python -m suvarna_tracker.decide` by Strategic Suvarṇa or
the Steward; the committed `control/suvarna/state/DECISIONS.jsonl` is a mirror) as of 2026-09-29. `delegated` is not
decided.

| ID | Decision | When | Recommendation | Status |
|---|---|---|---|---|
| N-1 | Approve the v1.3 plan set (including the charter v1.3 changes and the track briefs) | after §5.0b | — | open: requested |
| N-2 | Fold the build-engine work into the Nikaṣa Engine session | now | Yes | **decided: yes** |
| N-3 | Landing approach for PR #2736: split into code and evidence, retarget to `main` | now | Yes | **decided: yes** |
| N-4.T1–T3 | Approve each reopen agenda: T1, then T2, then T3 | E2, three times | Review each as presented | open |
| N-5.T1–T3 | Sign each re-seal | after each agenda | — | open |
| N-6 | `bo_upaya`: fix now (Track E), or defer to L2 | now | Fix now | **decided: fix now** (live proof in its wave, §4.2) |
| N-7.T4 · N-7.L0 | Accept tier 4 · accept the L0 instance | end of E2 | — | open |
| N-8 | Engine freeze | J1 | — | open |
| N-9 | G2: L0 pilot results and rollout pace | G2 | — | open |
| N-10.L0–L5 | Accept each layer instance; sign each layer close | per layer, batched | — | open |
| N-11 | Approve asset-specific addition classes (§2.3) | before L2 briefs, at the latest | Decide per class | open |
| N-12 | Certify the canonical chart only, or several; confirm none of the 7 charts is an external user's | **before the first L0 wave** (D4) | Canonical only; other charts recorded "served from stale L0 inputs" (§6.4b) | open |
| N-13 | N/A for "writes nothing to its own table" and "update-only" assets (R247) | with N-22 | Rule it as registry rules | open |
| N-14 | Data findings with owners outside the inspector: `lel_events` (R236), `build_dependencies` (R219), `ka_gochara` registry (R240) | per layer | — | open; R240 sits with L3 Gochara |
| N-15 | Pace and budget ceilings | before launch | — | **decided: no ceilings**; spend metered and reported |
| N-16 | Nirmāṇa's database record: leave it reading "frozen", or supersede it with the privileged control writer | any time | Leave it | open |
| N-17 | Track F: how Suvarṇa relates to the L3 families | now | Family sessions own them; Suvarṇa evaluates | **decided** |
| N-18 | Isolation: dedicated folder and branch model | now | Yes | **decided: yes**; set up 2026-09-29 |
| N-19 | Approve the autonomy charter | before execution | — | **decided: approved** v1.1; amended to v1.2 by CHARTER-AMEND-A-C; v1.3 changes confirmed with N-1 |
| N-20 | Where the read-only database credential lives | before launch | — | **decided:** `~/.config/suvarna/pgenv.sh`, mode 600 |
| N-21 | Kṣetra on the L5 critical path: accept, or disposition `mi_bhara`, `mi_sankalpa` `qualify` pending Kṣetra | before L5 briefs | — | open (new, D2) |
| N-22 | Per-gate applicability rules (N/A by layer or column pattern), ruled once per gate | before E6.5 | Start from D3's proposed defaults | open (new, D3) |
| N-23 | Headless runner billing: subscription windows, or an API key | before L.14 | — | open (new, D5) |
| N-24 | Approve the Tracks I and B brief | before J1 | — | open (new) |
| HB-G · HB-S · HB-K | Hand a closed family's assets back to Suvarṇa (out of the R8 set), with its rebuild runbook | when each family session closes | — | open (new, D2) |
| N-CLOSE | Accept the closure report | end | — | open |
| F-0 | Gochara: deploy before switching authority | now | Yes | **decided: yes** (ADK-0027) |
| F-5 | Gochara: served horizon | — | — | **decided: full century** (by F-0) |
| F-2, F-3, F-6 | Saṅgam: keep or retire into `kala_field`; the cascade lock; Mode D | before Saṅgam design | F-3: a foreign-key change (D2) | **delegated** to L3 Saṅgam; the native seals; Strategic Suvarṇa records `decided`. F-3 gates L2 MSR rebuilds |
| F-1, F-4 | Kṣetra: W7 or interim clear; 6 classes or more | before Kṣetra rebuild | — | **delegated** to L3 Kṣetra; the native seals |

**Decided outside the numbered list** (all in the log):

| ID | What was decided | Where it lands |
|---|---|---|
| NIRMANA-SUPERSESSION | Nirmāṇa set aside; succeeded by Suvarṇa on the Nikaṣa engine; 98 kept assets | §3.3 |
| FI-2 | Merge PR #2751 | §5.0 |
| CHARTER-AMEND-A-C | Charter v1.2: L0 global build under G13; per-layer idempotency; pre-wave fingerprints and a reserved undo | charter |
| INDEPENDENT-REVIEWER | L.9 by GPT-6 Astra at extra-high effort | §5.0b |
| ENGINE-EARLY-START | No session, the Nikaṣa Engine included, before N-1 | §5.0b |
| D1 | Build identity: dispatch-only 'build' grant; L0 native-dispatched; deployed SHA from the job image tag | §5.1 E7, §6.4, charter G13 |
| D2 | Family certification; exclusion from wave completion; R8 staleness exemption; hand-back; Kṣetra on the L5 path | §5.3, charter R8 |
| D3 | Gate detectors and rollup as J1 prerequisites; N/A by registry rule; non-gate criteria never block ELEVATED | §1.1, §2.1, §5.1 E6, charter P6 |
| D4 | L0 dump and diff; measured impact; N-12 before the first L0 wave; full-layer rebuild defined | §1.2, §6.4b |
| D5 | Durable runtime = supervised headless pass loop; `/loop` only as an interim to G2 | §6.7 |
| D6 | Read-only login `suvarna_reader`, set up by a native-run admin script; Monitor verifies continuously | §3.8, L.10 |

---

## §9 · Tracking

**The live view is the real-time tracker** (execution architecture §11): the plan model (`00_ARCHITECTURE/control/suvarna/plan_model.json`), an append-only event log every role writes to as things happen, the decisions log every native gate reads, and detectors that decide "done" wherever a check exists. It shows what runs in parallel and in sequence, where we are, what is next, what waits on the native, and the measures below, within about a second of a change. The plan model changes with this plan, in the same commit.

- **Native gates** (`done_by: decision`) are done only when the decisions log has a `decided` line for their id. A
  `delegated` line shows as waiting. A decision event that disagrees with the log shows as a conflict.
- **Detector types added for v1.3** (arch §11.7) are built by L.13 before launch. A detector whose expected input does
  not exist yet reads pending; one that cannot measure reads unknown; neither is ever done.

**Weekly scorecard** (from the tracker and ledgers, never typed by hand):

- assets ELEVATED, per layer (exact after E6.3; labelled proxy before);
- certification records, and certifications invalidated as stale;
- open gap rows, by gate and layer;
- open register rows, by severity;
- T1–T5 status (until J1);
- effort spent against estimate, per track; native latency per merge and decision.

**Per-track burn-down** of its own rows and gates.

**Every scorecard figure names its query**, so anyone can re-run it.

---

## §10 · Adapting the plan

- **Findings change briefs, not the plan**, unless they change a track, a gate, the standard or the end state.
- **What triggers a plan revision:**
  - a track's estimate misses by more than half;
  - a gate criterion proves unmeasurable;
  - a new class of defect appears;
  - a native decision changes scope.
- **How:** Strategic Suvarṇa drafts the change with a changelog entry, and changes `plan_model.json` in the same commit. The native approves it. The version bumps.
- **Stop rule:** an execution session that finds the plan wrong stops that packet and reports. It does not improvise.

---

## §11 · Risks

| Risk | Signal | Mitigation |
|---|---|---|
| The engine stage never ends | E2 or E6 keeps growing | Closed agendas; derivability harvested in parallel (Track A); one J1 checklist (§4.2); per-asset detectors kept out of J1. |
| Another false pass | a gap closes, then the asset fails | Only PASS or rule-computed N/A closes; reviewers never author a PASS; R246 detector; mutation-proven tests; gate reviews. |
| A stale certification | an upstream or family change after certification | Certification records carry what they were measured against; E5.5 invalidates on mismatch; pre-wave fingerprints. |
| Collision with live workstreams | two sessions change one asset | Coordination rule (§7); leases; check live work at every session start. |
| Native latency on the critical path | merges or decisions wait days | One PR per wave group; decisions requested with lead time and batched; latency shown on the scorecard. |
| L0 wave harms other charts | other charts serve data derived from changed L0 | Dump, diff and measured impact per L0 wave; native-dispatched; N-12 first (§6.4b). |
| Register drift | tallies disagree with rows | Computed tallies; detectors FI-3, FI-4. |
| Environment fragility | stalls, dropped connections | §6.5 rules; Monitor. |
| The runtime dies while the native is away | no Conductor heartbeat | Stateless passes; watchdog relaunch; hold and park (§6.7). |
| Review fatigue | gates accept quickly | Fresh reviewer per packet; independent reviewers for plans and rulings. |
| Scope creep from opportunities | layers slow down | Opportunities never block; ruled in batches. |
| Implementation larger than expected | measured cost per asset high at G2 | Re-estimate at G2 from measured data; the native sets the pace. |
| A production-visible action on a stale authorization | an agent acts on an older approval after a newer directive (the 2026-09-28 Gochara switch) | One authoritative decisions log outside git; re-read at the moment of action; named preconditions (charter §2, §6); reversal is the safe direction. |
| The live view drifts from work owned elsewhere | the tracker shows a family session's item out of date | The family prompts require them to report to the tracker; detectors read committed refs where possible. |
| L2 and L3 collide through the cascade lock | an L2 MSR rebuild wipes Saṅgam, or is refused by it | No L2 MSR rebuild before F-3 is `decided` (charter R1); Saṅgam certified only after the L2 chain. |

---

## Appendix A · Fact baseline (2026-09-28, updated 2026-09-29) and sources

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
| Freeze blockers open | R24, R39, R71, R244 (R40, R41 closed) | same |
| Freeze tests | as §3.5 | `nikasha_test/PHASE6_ANALYSIS.md` §6.5 |
| Build engine | about 200 commits not on `main`; no PR | `git rev-list --count origin/main..campaign/nirmana-engine`; `gh pr list` |
| Last Nirmāṇa commit | `badc3f9bc`, 2026-09-09 | `campaign/nirmana-autonomous` |
| L3 Gochara | migration 1150 applied to production 2026-09-28 | `l3/gochara-autonomous-wp0-7` log |
| Register tallies repaired | v2.8, 252 rows, 180 open | `NIKASHA_CHANGE_REGISTER_v2_0.md` @ `2a78ec64d`; tracker detectors `register_tally_consistent`, `register_wellformed` |
| Gochara switch and reversal | 19:22:58 → 19:29 UTC 2026-09-28; no consumer | ADK-0027 (`33b725778`); Gochara session's read-only check |
| Build dispatch route; deployed SHA for writers | `POST /api/cockpit/runs`; Cloud Run job image tag | FABLE_REVIEW_D1_D5 §D1 (`cockpit/runs/route.ts`, `jobs.ts:getJobImageTag`, `deploy.yml`) |
| Family positions in the level map | `ka_gochara_resonance`, `ka_vedha_gochara` level 1; `ka_gochara` 5; `ka_kshetra` 12; `ka_sangam` 13; 16 readers | FABLE_REVIEW_D1_D5 §D2 (live registry, 2026-09-29) |
| L0 dump size | 37 tables, about 1,080 MB | FABLE_REVIEW_D1_D5 §D4 (`pg_total_relation_size`) |
| PR #2751, PR #2756 | merged 2026-09-29 10:21Z, 15:29Z | `gh pr view` |

## Appendix B · Glossary

- **Asset** — one registered data-plane unit with a writer or a declared kind (127 active).
- **Gate** — one of the nine core checks (§2.1).
- **Gap row** — an open shortfall in the delta ledger, stating what was measured and what is required.
- **Certification record** — a verdict per gate per asset in the certification ledger, with what it was measured against.
- **Layer instance** — the tier-3 document for one layer.
- **Asset brief** — the tier-4 document for one asset.
- **Emit** — the inspector writing its measurements into the delta ledger.
- **Withholding list** — gap closures an emit must not write until a named condition holds.
- **Family set** — the L3 family assets under charter R8, and their readers, frozen in one versioned file at J1.
- **Full-layer rebuild** — §1.2.
- **Builder identity** — the dispatch-only account that creates non-clearing builds for the canonical chart (D1).
- **[TRANSFERS]** — an obligation that belongs to a plane not yet built.
