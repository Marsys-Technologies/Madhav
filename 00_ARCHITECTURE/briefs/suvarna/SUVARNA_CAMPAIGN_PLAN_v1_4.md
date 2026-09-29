---
artifact: SUVARNA_CAMPAIGN_PLAN
canonical_id: SUVARNA_CAMPAIGN_PLAN
version: "1.4"
status: "DRAFT — for native review (N-1). Review passes 1 and 2 folded; the independent review (L.9) still to come."
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
decision_owner: Native (Abhisek Mohanty)
supersedes: "SUVARNA_CAMPAIGN_PLAN_v1_3.md (v1.2, v1.1 and v1.0 before it). Earlier: succeeds the Nirmāṇa elevation campaign (NIRMANA_SUPERSESSION_RECORD_v1_0.md, PR #2751, merged)."
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
review_disposition:
  - briefs/suvarna/reviews/REVIEW_PASS1_DISPOSITION_v1_0.md
  - briefs/suvarna/reviews/REVIEW_PASS2_DISPOSITION_v1_0.md
changelog:
  - "1.4 (2026-09-29, review pass 2 folded: REVIEW_PASS2_DISPOSITION_v1_0.md, 70 findings). D6 recorded as applied (L.10 done). Deadlocks removed: E4.1 no longer needs the ledgers (E4.3 lands them and is a J1 input); N-10.Lx split into instance acceptance (N-10.Lx.i, before the layer's waves; the PROVISIONAL banner lifts there) and close (N-10.Lx.c); L0 revalidated before N-7.L0 (A.L0v). One branch rule: every lane whose output reaches main branches from suvarna/trunk (main plus accepted packets, synced from main every pass); source branches are read or cherry-picked with -x; #2736 is not retargeted; landing PRs come from landing branches cut from origin/main (§6.4). Folds before the cut-over are pushed as fast-forwards to campaign/nikasha-test, which the tracker reads as origin/campaign/nikasha-test (§5.1 E4). F-3 now means the cascade is removed from all eight ON DELETE CASCADE foreign keys into bodha_msr_signals (measured: kala_convergence, kala_darshana, kala_bhavishya, kala_activation, kala_obstruction, bodha_signal_embeddings, bodha_contradictions ×2); wave 0 holds two MSR writers, so G2 waits for F-3 and for a detector that sees the foreign keys changed (F3.FK). Deploy checks are git ancestry, never equality. Waves depend on per-wave fix items derived from the level map (I.W0–I.W5), so L2 and L5 fixes gate W0, W1 and W3; L0's four levels are four native dispatches (B.L0.0–B.L0.3); lel_events gets a disposition before W0 (N-14.R236). The tracker's exact-ELEVATED switch is its own item (E6.3t). builder_scope is measured by the authenticated preflight, not by the reader. Track I starts at N-24, before J1, lane to trunk only. Census gains an --assets filter (E1.9). Pre-J1 wave rehearsal off production and an L0 dump rehearsal (E5.6, E5.7); serving canary in E5.3. Reopen agendas approved together; re-seals stay ordered. Isolation (proposed, N-25): the swarm as a separate macOS user with its own settings and GitHub identity, branch protection on main, the decisions log read-only to the swarm; launch items L.16a/L.16b/L.16d/L.16g gate FI-7. Build-engine facts corrected (10 engine commits; migrations 1094–1096 inside L3's range: N-26). Review package marked stale; L.12r rebuilds it before L.9."
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
- **Companions:** `SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` (v1.4; how it runs, including isolation, §2.4, the runtime, §5.5, and the tracker, §11), `SUVARNA_AUTONOMY_CHARTER_v1_0.md` (v1.4; what the swarm may decide), `tracks/TRACK_E_BRIEF_v1_0.md` and `tracks/TRACK_A_BRIEF_v1_0.md` (v1.1; packets and write boundaries), `SUVARNA_RUNBOOK_v1_0.md` (v1.2), `roles/ROLE_*_v1_0.md` and `prompts/*_v1_0.md` (v1.2), `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (v1.3; the three L3 families), `SUVARNA_DOCUMENT_MAP_v1_0.md` (v1.2; every document in the campaign), `D6_SUVARNA_READER_RUNBOOK_v1_0.md` (v1.3; the read-only login, applied).
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
   "Keep with fix designs" is `keep`; there is no separate "fix" disposition.

- **"Current"** means the certification still matches what it was measured against: the writer's commit (the job image tag of the run), the upstream certification ids, and the row-set fingerprint (§5.4 step 7; E5.5).
- An asset retired or consolidated with a recorded reason also counts as terminal; the exact function (E6.3) honours
  terminal dispositions, so a retired asset never blocks a wave.
- "Frozen by Nirmāṇa" is not elevated. It is a starting point (§3.3).
- **The tracker computes ELEVATED only through the exact function** (E6.3), called at the committed ref once E6.3t
  switches it. Until then every `levels_elevated` and `assets_elevated` detector reads **unknown**, never done: the
  one-certificate proxy is not a completion signal (§N.8). Nothing can be certified before J1 anyway.

### 1.2 · Layer level

A layer is **CLOSED** when:

- its layer instance (tier-3 instance) is accepted by the native **before the layer's first wave** (N-7.L0 for L0;
  N-10.L1.i … N-10.L5.i; tracker J1.5, A.L1a … A.L5a). Acceptance lifts the PROVISIONAL banner from the layer's
  revalidated briefs; nothing in the layer is certified before it;
- every active asset in it is ELEVATED or terminally dispositioned;
- a **full-layer rebuild** succeeds under the orchestrator and re-measures clean;
- the native signs the layer close (N-10.L0.c … N-10.L5.c; tracker G3.L0 … G3.L5).

**Full-layer rebuild (D4).** One orchestrator run with `action=rebuild, clear_before=false` over every active asset
of the layer (`scope=layer`; for L3 an asset list, below), for the canonical chart (L1+) or globally (L0). It is not a
wipe and needs no R3 approval.
- **L1–L5:** it is from scratch for the chart (every writer deletes and re-inserts its own rows on the natural key), so
  it also proves Idem.
- **L0:** upserts never delete, so it cannot prove the absence of orphaned rows. The L0 close proof is: the
  post-rebuild fingerprint equals the pre-rebuild one, or every row in the diff is explained. A fresh build on a scratch
  database compared by fingerprint is an opportunity, not a gate. L0's rebuild is dispatched by the native (D1).
- **L2:** any rebuild of an MSR writer deletes `bodha_msr_signals` rows, which today cascade into seven tables (§5.3).
  It therefore waits until F-3 is decided **and** the cascade detector reads done (F3.LOCK, F3.FK; charter R1).
- **L3:** the family assets are rebuilt by their family sessions (or after a hand-back, by Suvarṇa, §5.3). The
  full-layer rebuild is an **asset-list run** (`scope=assets`) over L3 minus `FAMILY_ASSETS.json`, never `scope=layer`
  (which would include the family writers, R8); E7.1's build grant must allow that scope. The layer closes only once
  the family assets and their L3 readers are certified (B.FG, B.FS, B.FK, B.FR.L3).
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
- **"Required, per-asset detector pending."** A required criterion whose detector is per-asset (today `Carr.D1–D3`) is
  declared that way in the registry. Its cells read `NO_DETECTOR`, which blocks ELEVATED, until the asset's own
  detector lands (Track I). The J1 coverage check (E6.5) counts such a declaration as covered; it never makes the
  criterion optional or N/A. After J1 the registry changes only by a versioned revision the native approves.

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

- **Tiers 1–3:** sealed. A reopen agenda is ruled (D2 of the Nikaṣa rulings, 2026-09-27): about 32 clause fixes across the three documents (Track E §6 lists 31; E2.1 reconciles the count), plus the derivability mechanisms Track A will harvest (§5.2); both go into one reopen at J1.
- **Tier 4:** draft, pending your acceptance (N-7.T4).
- **L0 layer instance** (v3.0): draft, pending your acceptance (N-7.L0).
- **Asset briefs:** 5 L0 pilots. No other layer has an instance or briefs.

### 3.7 · Where the code is

- **Nikaṣa tooling** lives on `campaign/nikasha-test` (PR #2736). It is **not on `main`**, and neither are the tier
  documents, the L0 instance and the pilot briefs. The PR targets `l3/kala-layer-briefs`, not `main`, and adds about
  154,000 lines (mostly census artefacts). N-3 (decided) splits it; the split is built as fresh branches from `main`,
  and #2736 stays open until the native closes it (Track E §4).
- **The build engine** lives on `campaign/nirmana-engine`: 200 commits ahead of `main`, of which **10 are the
  engine's** (`d9dab8ad2…e5dd65b8f`, measured by the Track E brief §3.1); the rest are L3 readiness documents and Saṅgam
  stage 3, which travel under the Saṅgam session. No PR.
  - Closed: A1 (timing), A2 (error text), A3 (run-killer), B1 (cascade reporting), B2 (downstream count).
  - Not started: C1 (crash and orphan handling), C2 (stuck states), D1 (the engine judged by the Build gate).
  - Migrations 1094, 1095 and 1096 are not in production, and sit inside L3 Kāla's reserved range 1070–1119
    (renumbering at landing: N-26).
  - Nothing from it is deployed.
- **The build dispatch path** (measured by D1's review): `/api/build/start` is decommissioned; builds are created by
  `POST /api/cockpit/runs`, which needs chart write permission (owner or `super_admin`). Writers run in the Cloud Run job
  `brahma-build-pipeline-job`, whose image tag is the deployed commit.

### 3.8 · Live work elsewhere

- **L3 Gochara workstream** (`l3/gochara-autonomous-wp0-7`, PR #2731 open). It applied a production migration (1150) to `ka_gochara`. On 2026-09-28 it switched the canonical chart to `'4.0'` before the deploy-before-switch directive (F-0) arrived, and reversed it six minutes later; nothing consumed the switched data (ADK-0027). It is rebuilding the full century under `'4.1'`; the native has put its production execution on hold.
- **Three L3 family sessions** (from 2026-09-29): Gochara, Saṅgam and Kṣetra each seal a final brief and implement it (N-17). Saṅgam's session is running.
- **Pūrṇa**, **Jātaka**: separate campaigns with their own migration reservations. They and the families also deploy to `main`.
- **D6** (the read-only login `suvarna_reader`): **applied 2026-09-29** (plan hash `31e035f7…`, commit `21637553c`).
  The credential file logs in as the reader; the data-plane gate passes as the reader; the Monitor reads 8/8 OK (L.10).
- **Permissions today (measured 2026-09-29).** The native's user-level Claude Code settings default to
  `bypassPermissions` and allow `Bash(*)`, `Edit(**)`, `Write(**)`, `mcp__github__*` and `mcp__postgres__*`; the
  repo's committed `.claude/settings.json` allows `git push*`, `gh pr *`, `gh api *` and sourcing
  `/Users/Dev/madhav-l3/dbenv.sh` and `dbenv_builder.sh` (both world-readable). Any process running as the native can
  append to the decisions log. So an allowlist alone bounds nothing; isolation is a launch item (§5.0b, N-25).

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
     TRACK I  Implementation: fixes for every wave, in parallel lanes  ◄────────────────────────┤
              (starts at N-24: tier-independent fixes to trunk before J1; nothing to main)      │
                                                                                                │
     TRACK B  Rebuild and certify: one wave per dependency level, in order  ◄───────────────────┘
              wave n = its fixes merged to main and deployed (native merge) → dispatch → certify
              ├─ family assets and their readers: outside wave completion, certified asset by asset
              ├─ W0 needs F-3 decided and the cascade removed (it holds two MSR writers)
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
| **G2 · Loop proven** | dependency levels 0–2 certified (family assets excluded, D2; needs F-3 and F3.FK, §5.3); cost per asset measured; §5.4's lifecycle confirmed or revised | **native** (N-9); a checkpoint, not a stop, unless the native halts |
| **G3.Lx · Layer close** | that layer CLOSED (§1.2) | **native**, batched (N-10.L0 … N-10.L5) |
| **G4 · Campaign complete** | §1.3 | **native** (N-CLOSE) |

**The J1 checklist.** One list, the same in this plan, the tracker (`J1.6` depends on each item) and the Nikaṣa Engine
brief. Each criterion is proven by a detector or by a native decision, never by a typed "done".

| # | Criterion | Tracker item | Proven by |
|---|---|---|---|
| 1 | T1–T5 pass in production tooling on `main` | E1.7 | detector: the scorecard on `main`, produced by the committed generator (hash-checked), every test's verdict PASS, its inspector commit an ancestor of `main` |
| 2 | R24 closed (production L3 census R134 and clean re-runs; R40 and R41 are already closed) | E1.8 | detector: register row closed |
| 3 | R39 closed: the census's Build-gate checks, run on `main` after E3.7 against the engine's own claims, all PASS, recorded in the scorecard (`engine_build_checks`) | E3.6 | detector: register row closed |
| 4 | R71 closed through the combined reopen | E2.2 | detector: register row closed |
| 5 | R244: the `bo_upaya` fix merged (its source-order test on `main`); the row closed, or deferred with withholding until its L2 wave proves it (N-6 still holds: the fix is made now; only the live proof waits, because a live rebuild before J1 would need inputs that cannot be certified before J1) | E4.2, E4.2r | detectors: the test file on `main`; register row CLOSED, DONE or DEFERRED |
| 6 | No other freeze-blocking row open | J1.R | detector: R24, R39, R71, R244 all present and closed (R244 may be DEFERRED); a missing row is an error, never clean |
| 7 | Combined reopen: the three agendas approved together, each tier re-sealed in order T1 → T2 → T3 | J1.1a–J1.3 | native: N-4.T1–T3, N-5.T1–T3 |
| 8 | Tier 4 accepted; the L0 layer instance, revalidated against the re-sealed tiers, accepted | J1.4, A.L0v, J1.5 | native: N-7.T4, N-7.L0 |
| 9 | Build engine landed, its migrations applied, and deployed | E3.2, E3.3, E3.7 | detectors: landing PRs merged; `_migrations_applied` rows for the numbers N-26 fixes (1094–1096 today); the landing merges are ancestors of the job image's commit |
| 10 | Nikaṣa tools and register on `main`, inspector tests in CI; ledgers cut over | E4.1, E4.1c, E4.3 | detectors: files on `main`; the CI workflow runs the inspector tests; both ledgers on `main` (md5 evidence at the cut) |
| 11 | Execution tooling (certification writer, fold script, level-wave script with serving canary, per-entry fingerprint rotation, stale-certification detector, census `--assets`) on `main`, tested and reviewed | E5.1–E5.5, E1.9 | detectors: files on `main` (paths pinned by the Track E brief) |
| 12 | D3 gate detectors: every core gate × layer has an auto-measured detector, a declared N/A rule, or a "required, per-asset detector pending" declaration (§2.1); rollup coded; ELEVATED exact; non-gate rows re-keyed | E6.3, E6.4, E6.5 | detectors: the committed registry-coverage report; files on `main`; no open gap on a non-gate criterion |
| 13 | Build identity (D1) provisioned; the Monitor's builder-scope check green (measured through the authenticated preflight); the level-wave script tested against it; the reader login (D6) applied | E7.3, E5.3, L.10 | detectors: Monitor checks `builder_scope` and `credential_readonly` |
| 14 | Tracks I and B brief approved | J1.0 | native: N-24 |
| 15 | One end-to-end wave rehearsed off production; an L0 dump of every L0 table made and verified as the reader | E5.6, E5.7 | evidence events (a rehearsal cannot be detected on production) |
| 16 | The Suvarṇa tracker reads ELEVATED only from the exact function | E6.3t | evidence event with the tracker commit and its test |

- **R244 and the J1 loop.** A live `bo_upaya` rebuild is a production build; before J1 no upstream is certified, so
  charter §6 precondition 6 cannot hold. J1 therefore takes the fix (merged, tested on fixtures) and leaves the live
  proof to `bo_upaya`'s own wave (B.U), where R244 closes and the withholding lifts. R246 (E1.6) waits for the merged
  fix, not the live rebuild.
- **Rows 15 and 16 are new in v1.4** (review pass 2): the first find → fix → rebuild → certify loop is rehearsed off
  production before it runs on the served chart, and ELEVATED is never a proxy once certification can start.

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
| Name the sessions (FI-6) | Strategic Suvarṇa · Exec Suvarṇa (the Nikaṣa Engine session is named at its own start, CLAUDE.md §G) | **done** for the two that exist (listed as "Strategy - Suvarna", "Execution - Suvarna") |
| Relay to the three family sessions, as a report (FI-8) | D2's certification condition (an orchestrator-run build, not a cutover script); rulings and brief seals are recorded only by Strategic Suvarṇa (the sessions emit `requested` and `review`, never `decided` or a sealed `done`); the census lock, the corrected census command and an absolute evidence folder; the tier-4 template revision; F-3 now means the cascade is removed from all eight foreign keys (§5.3) | **blocked**: the prompts are at v1.2 and the notice at v1.1; the native pastes the notice into each session; done when each session acknowledges (an FI-8 note from `l3-gochara`, `l3-sangam`, `l3-kshetra`). An N-1 prerequisite |

### 5.0b · Launch readiness — what must be true before execution starts

Execution starts when the native approves the v1.4 set (N-1, FI-7). The tracker's FI-7 waits for every row marked
**N-1 prerequisite**. States are read from the event log (2026-09-29).

| Item | Tracker | Owner | State (2026-09-29) | N-1 prerequisite |
|---|---|---|---|---|
| This plan (v1.4), charter v1.4, architecture v1.4, focus families v1.3, plan model | L.1, L.8 | Strategic Suvarṇa | this revision | yes (via L.8) |
| Autonomy charter | L.2 | Strategic Suvarṇa | **approved** v1.1 (N-19); amendments A–C → v1.2 (CHARTER-AMEND-A-C); v1.3–v1.4 changes (D1–D5, review folds, G16, the isolation design) confirmed with N-1 | yes |
| Role prompts (shared rules + 9 roles) | L.3 | Strategic Suvarṇa | **done**; swept to v1.1 (L.12) and v1.2 (this revision) | — |
| Runbook and start prompts | L.4 | Strategic Suvarṇa | **done**; runbook v1.2, prompts v1.2 | — |
| Folders and branches: `/Users/Dev/suvarna`, `suvarna/hq`, `suvarna/trunk` | L.5 | Strategic Suvarṇa | **done** | — |
| Monitor: environment checks and repair | L.6 | Strategic Suvarṇa | **done** (8 checks, including `credential_readonly`) | — |
| Read-only credential file (N-20) | L.7d, L.7 | native | **done**: `~/.config/suvarna/pgenv.sh`, mode 600 | — |
| D6 deploy-gate amendment | L.10a | native merges | **done**: PR #2756 merged 2026-09-29 | yes |
| `suvarna_reader` applied; the credential file uses it; Monitor `credential_readonly` ok (D6) | L.10 | native ran the admin script | **done** 2026-09-29 (plan `31e035f7…`; 0 write paths; data-plane gate passes as the reader; Monitor 8/8; `21637553c`) | yes |
| Track E and Track A briefs | L.11 | Strategic Suvarṇa | **done** (`21637553c`); v1.1 in this revision | yes |
| Role, prompt and runbook sweep to the v1.3 set | L.12 | Strategic Suvarṇa | **done** (`21637553c`; family prompts `8b0cd1b79`); the review package was not rebuilt, so that part moved to L.12r | yes |
| **Review package and bundle** rebuilt for the v1.4 set (`SUVARNA_REVIEW_PACKAGE_v1_0.md` is stale: v1.0, points at plan v1.1) | L.12r | Strategic Suvarṇa | to do | yes (L.9 waits for it) |
| Tracker additions: the v1.3 detector types, family-aware `levels_elevated`, the hq commit lock | L.13 | Strategic Suvarṇa | **done** (`4cef1a958`, 260 tests); the v1.4 code changes are listed as CODE items in REVIEW_PASS2_DISPOSITION | yes |
| **Tracker and Monitor run from committed code** in the hq worktree, reading `NIKASHA_REF=origin/campaign/nikasha-test`; Strategic Suvarṇa restarts them after each plan merge into hq | L.17 | Strategic Suvarṇa | to do | yes |
| **Interim runtime safeguards (D5a):** stateless Conductor passes (10-minute `/loop` interval; each pass reads `snapshot.json` and the event tail), the Suvarṇa settings file (`dontAsk`, allow-list, explicit denies, hold-guard hook; never bypass), the lane launcher, watchdog alerting, power and OS-restart settings | L.15 | Strategic Suvarṇa | to build | yes |
| **Isolation decision** (N-25): run the swarm as a separate macOS user (arch §2.4) | L.16d | native | proposed | yes |
| **Isolation in place:** per N-25, the separate user with no read access to the native's credentials; or, if declined, the fallback hardening (arch §2.4); either way `chmod 600` on the two `dbenv` files and the Monitor's `isolation` check green | L.16a | native sets up; Strategic Suvarṇa verifies | to do | yes |
| **Swarm GitHub identity:** its own token; can push branches and open PRs; a merge attempt is refused | L.16g | native | to do | yes |
| **Branch protection on `main`:** a pull request with the native's approving review; only the native may bypass | L.16b | native | to do | yes |
| **Durable runtime (D5b):** supervised headless `claude -p` pass loop | L.14 | Strategic Suvarṇa | to build | no: needed before B.W1 (after G2) |
| Budget ceilings (N-15) | — | native | **decided: none**; spend is reported | — |
| Review passes of the plan set | L.8 | Strategic Suvarṇa | passes 1 and 2 folded (this revision) | yes |
| Independent third-party review, findings folded | L.9 | GPT-6 Astra, extra-high (INDEPENDENT-REVIEWER) | after L.8, L.11, L.12, L.12r | yes |
| Relay to the family sessions acknowledged | FI-8 | Strategic Suvarṇa, native pastes | blocked (§5.0) | yes |

- **No session starts before N-1** (ENGINE-EARLY-START), including the Nikaṣa Engine session.
- **Tracks I and B brief:** drafted by Strategic Suvarṇa once L0's fix designs exist (J1.0d, after A.L0) and approved
  by the native (J1.0, N-24). **Track I starts at N-24**, not at J1 (§5.4).

### 5.1 · Track E — the engine (session "Nikaṣa Engine")

Seven lanes, running in parallel within the caps. **Every lane whose output reaches `main` branches from
`suvarna/trunk`** (arch §12.2); `campaign/nikasha-test` and `campaign/nirmana-engine` are read with `git show` or
cherry-picked with `-x`, never branched from, because both sit on `l3/kala-layer-briefs` and carry ~190 foreign commits,
Saṅgam family code among them. The one exception is a fold lane before the cut-over (E4.3), which is never PR-bound.

**E1 · Tooling.**
1. **Measure before changing.** Re-run T1–T5 on today's tooling and publish a machine-readable scorecard (E1.1).
2. **Close the remaining tooling rows:**
   - detector gaps R245, R248, R249, R250 (E1.2);
   - provenance: R226 (`--live` re-derive-and-diff), R228 (stale source references), R229 (unowned tables) (E1.3);
   - ledger identity: R251 (the rest of the crosswalk) (E1.4);
   - R24: the production L3 census (R134) and clean re-runs after the fixes (E1.8);
   - waiting on others: R55 (needs migration 1094, E1.5) and R246 (needs the merged `bo_upaya` fix, E1.6);
   - **census `--assets` filter** for the census and the emit, so a level wave re-measures only its assets (E1.9).
3. **Prove it again.** Re-run T1–T5 on `main` (E1.7), with the scorecard written by a committed generator.
- **Rough size:** 30–50 hours.

**E2 · The clause fixes.**
- The rows the D2 Nikaṣa ruling already agreed (32 by the ruling; Track E §6 lists 31, and E2.1 reports the
  reconciled count), drafted per document and held for the combined reopen at J1 (E2.1).
- R71 (the `[TRANSFERS]` contradiction) closes through that reopen (E2.2).
- **Rough size:** 20–30 hours.

**E3 · The build engine.**
- Bring the `campaign/nirmana-engine` work under this track (N-2, decided).
- Land its 10 engine commits: cherry-picked with `-x` onto lanes from `suvarna/trunk`, as the reviewable PRs the Track
  E brief pins; review; the native merges; deploy (E3.2, E3.7).
- Migrations 1094–1096: renumber at landing or keep, per N-26 (they sit in L3's reserved range); apply and verify
  (E3.3).
- Finish the carried items: A2b, A3b, R217 (E3.4).
- C1 (crash and orphan handling) and C2 (stuck states): **not required for the freeze.** They reduce noise, so they run alongside Track B (E3.5).
- D1/P10 (R39): the census's Build-gate checks, run on `main` after E3.7 against the engine's own claims (run-level
  states, error text, cascade reporting), all PASS and recorded in the scorecard; a plan document alone does not close
  it (E3.6).
- **Rough size:** 40–70 hours to the freeze; may land lower (10 reviewed commits, not 200): re-estimated after E3.2.
  C1 and C2 afterwards.

**E4 · Landing and the `bo_upaya` fix.**
- Split PR #2736 into a code PR and an evidence PR (the register v2.8, the tiers, the L0 instance and pilots), **built
  as fresh branches from `suvarna/trunk`**, not by retargeting #2736, which stays open until the native closes it; add
  the inspector's tests to CI (N-3; E4.1, E4.1c). E4.1-build-001 goes first: E1, E5 and E6 lanes build on it.
- **Folds before the cut-over.** Register folds are made by the Nikaṣa Engine Scribe on a fold lane cut from
  `origin/campaign/nikasha-test` and **pushed to it as a fast-forward** (`git push origin
  suvarna/lane/<qid>:campaign/nikasha-test`; never forced; a rejected push means re-cut the lane from the new tip and
  redo the fold). The tracker reads the register at `NIKASHA_REF=origin/campaign/nikasha-test` (L.17), so a pushed fold
  is visible at once. `/Users/Dev/madhav-nikasha` is never touched. **No ledger emits before E5.2 lands**: nothing
  certifies before J1, so pre-E5.2 folds change register rows only.
- **Ledger cut-over (E4.3):** folds stop on `campaign/nikasha-test` at a named cut; the ledgers land on `main` last;
  line count and md5 of both ledgers **and the register** are equal across the old and new locations (recorded as
  evidence); then Strategic Suvarṇa re-points `NIKASHA_REF` to `origin/suvarna/trunk` in one step, and folds resume on
  lanes from `suvarna/trunk`. E4.3 is a J1 input; E4.1 does not wait for the ledgers.
- Fix `bo_upaya` as a sanctioned writer exception (N-6: fix now): about half a day. The fix and its source-order test
  are merged (E4.2) and R244 is set CLOSED or DEFERRED with withholding (E4.2r); the live proof comes in its L2 wave
  (B.U).
- **Rough size:** 10–20 hours.

**E5 · Execution tooling.** Nothing exists yet for:
- **E5.1** writing certification records to `asset_certs.jsonl` (reviewed, idempotent on a copy first; §6.3). Each
  record carries what it was measured against: the run's job image tag, the writer file hashes, the upstream
  certification ids, the row-set fingerprint, and the census run id. A PASS must cite a criterion whose detector is not
  `NONE`.
- **E5.2** the fold script (register row states, ledger emit with the withholding list, computed tallies, fingerprints, drift).
- **E5.3** the level-wave script: dispatch through the builder identity (`suvarna-build`, E7); read the job image's
  commit and the deployed web SHA (`suvarna-build --preflight`) and require the landing merge to be an **ancestor** of
  each (`git merge-base --is-ancestor`, after a fetch), never equal to it; re-check the writer file hashes at that
  deployed commit; read-only check of the orchestrator's per-chart lock; for an L0 wave, the pre-wave dump, its
  verification, the post-wave diff and the measured impact statement (§6.4b); a **serving canary**: golden reads of the
  served MCP tools for `482012f1` before and after each wave, whose difference outside the wave's declared output
  changes triggers the stated reversal; verify once how staleness propagates on a global (no-chart) run, and record
  which case holds. Tested against the builder identity.
- **E5.4** per-entry manifest fingerprint rotation (`manifest_fingerprint.py` restamps only the root).
- **E5.5** the stale-certification detector: a certification whose recorded writer hash, upstream certification ids or
  row-set fingerprint no longer match is invalidated, and the asset returns to re-measure (§5.4 step 7).
- **E5.6** one end-to-end wave rehearsed **off production** (a scratch database restored from a verified dump, or a
  scratch chart that nothing serves): find → fix → rebuild → certify, with E5.1–E5.5 and the canary, before the first
  production wave.
- **E5.7** a read-only `pg_dump` of every L0 table as `suvarna_reader`, verified by `pg_restore --list` and row counts
  (D6's column-level grants may break it; if they do, the fix is a D6 amendment or a native-run dump, decided before
  B.W0).
- **Rough size:** 40–65 hours (was 30–50; the canary and the two rehearsals added).

**E6 · Gate detectors (D3).**
- **E6.1** Applicability per criterion (`layers:` and optional column pattern), so N/A is computed from the registry;
  the native rules the per-gate rules once (N-22). Generic detectors: Null (schema defaults, writer literal fallbacks,
  constant columns; never PASS alone), Dens (declared contract **and** a tier or confidence column in the served select;
  structural, and says so), Ldgr (L0 source presence; L1 computation provenance; L2+ constituent resolution generalised
  from `msr_referential_integrity.py`), Carr per layer (L1 = the existing verification tier), `Earn.literal_lint`
  (`check_earned_signal.py`) and a real `Earn.service_state`. The three existing narration lints wired in as Narr.
- **E6.2** the check → cell rollup, in code (§1.4).
- **E6.3** ELEVATED computed exactly as §1.1, terminal dispositions included, on `main` (the Nikaṣa tracker's
  function); the dependency-level map and the family set (`00_ARCHITECTURE/control/FAMILY_ASSETS.json`, with the
  readers; keys pinned in Track E §8) snapshotted and versioned at J1; wave ranges derived from the snapshot; a cycle
  is an error.
- **E6.3t** the Suvarṇa tracker calls that function at the committed ref and drops its proxy (Strategic Suvarṇa owns
  the tracker code; a J1 input).
- **E6.4** non-gate criteria (Cost, Count, Complete, Reach) re-keyed to `kind: info` by a reviewed, idempotent ledger
  migration (the R81 pattern); `Complete.depth`'s never-populated columns feed the Null detector as evidence.
- **E6.5** the registry coverage check (the J1 criterion): `asset_census.py --registry-check` writes
  `00_ARCHITECTURE/control/registry_coverage_report.json` (schema in Track E §8), committed on `main`: for every core
  gate and every layer, an auto-measured detector, a declared N/A rule, or a "required, per-asset detector pending"
  declaration (§2.1); no required core-gate criterion with a bare `detector: NONE`.
- **Rough size:** 50–90 hours. **Not included:** per-asset semantic detectors (about 60 assets × 1–3 h = 60–180 h),
  which belong to Tracks A and I.

**E7 · Build identity (D1).**
- **E7.1** a small auth PR (security-reviewed): `chart_grants.permission` also allows `'build'`; a build grant
  satisfies dispatch on `POST /api/cockpit/runs` (layer or asset-list scope, for L3's close, §1.2) and nothing else;
  `clear_before`, the clear routes, `layer=brahmagyan` and every other chart stay forbidden to it (tests prove each);
  plus an authenticated `GET /api/cockpit/runs/preflight` returning `{job_image_tag, job_sha, deployed_sha, builder:
  {principal_id, role, status, grants}}`, the builder's own scope as the server sees it. The native merges; it deploys.
- **E7.2** the native provisions the builder: one service account (`profiles` role `guest`, status `active`), one grant
  row `(482012f1…, builder, 'build')`, its secret in `~/.config/suvarna/builder.env` (mode 600), and the
  `~/.config/suvarna/bin/suvarna-build` script (mode 700; interface pinned in Track E §8) that prints only
  `{run_id, plan, asset_count, job_image_tag}`. The native records the provisioning evidence (an admin read of the
  profile and its grants) in `$SUVARNA_HOME/run/builder_identity.json`.
- **E7.3** the Monitor's `builder_scope` check green. It reads the scope from `suvarna-build --preflight` (the
  `suvarna_reader` login cannot read `chart_grants.permission` or `profiles`, D6): role `guest`, status `active`,
  grants exactly `{(482012f1,'build')}`, matching `builder_identity.json`. The check's code goes to
  `strategy/suvarna-plan` (tracker code has one owner, arch §12.12) and runs once hq takes it.
- **L0 waves are dispatched by the native** from the cockpit, at the Build operator's parked request with the
  pre-check, dump and impact statement attached. The builder never holds `super_admin`.
- **Rough size:** 8–15 hours, plus the native's merge and provisioning.

- **Track E total to the freeze: roughly 200–340 hours of agent effort** (E1 30–50 · E2 20–30 · E3 40–70 · E4 10–20 ·
  E5 40–65 · E6 50–90 · E7 8–15), split across parallel lanes. Native and deploy latency is on top (§6.6). The
  derivability work sits in Track A; it is not removed, only taken off the engine's path.

### 5.2 · Track A — analysis, all layers at once (session "Exec Suvarṇa")

Read-only. Runs across all six layers from day one (after N-1).

For each layer, three tracker items:
1. **A.Lxi — census and layer-instance draft.** A fresh census with today's inspector, provisional until J1. A draft
   instance derived from the tiers and the census. Wherever the tiers do not supply what the draft needs, record it as a
   **tier gap**. Do not invent. **This is all the harvest (A.H) and J1 wait for.**
2. **A.Lx — asset briefs, dispositions, fix designs.** One provisional brief per asset (gap rows, proposed additions
   with their detectors, opportunities), a disposition per asset from the tier-4 list (keep, integrate, enrich, qualify,
   consolidate, historical, retire, unresolved; "keep with fix designs" is `keep`), and fix designs marked
   **tier-independent** (can be built before J1) or **tier-dependent** (waits for the reopen).
3. **A.Lxr — revalidation after J1.** Re-measure with the frozen inspector; revalidate each brief against the re-sealed
   tiers and the frozen registry. Then the native accepts the layer instance (**A.Lxa**, N-10.Lx.i; L0 at J1.5 after
   **A.L0v**, its revalidation against the re-sealed tiers), which lifts the PROVISIONAL banner.

**L3's evaluation of the family briefs is its own item, A.L3f, off the J1 path** (it also maps the family briefs onto
the post-J1 tier-4 template); B.FG, B.FS and B.FK wait for it.

**What it feeds:** the tier-gap harvest → the combined reopen at J1; fix designs → Track I.

- **Rough size:** the derivability work priced at about 157 hours in the register; briefs about 122 × 1–2 h ≈ 130–250 h
  (127 less the 5 family assets, which are evaluated, not briefed);
  revalidation about 30–65 h; per-asset semantic detectors 60–180 h (shared with Track I). Spread across up to six
  analysts, with the Architect on the derivability mechanisms. Re-estimated after the first layer's drafts.

### 5.3 · Track F — the L3 focus families

Gochara, Saṅgam and Kṣetra get dedicated algorithm and enrichment work, beyond conformance to the nine gates.

- **Run by three family sessions (N-17, 2026-09-29).** L3 Gochara, L3 Saṅgam and L3 Kṣetra each verify their family's state, bring its rulings to the native (Saṅgam: F-2, F-3, F-6; Kṣetra: F-1, F-4), write a final brief on the tier-4 template, have it independently reviewed, get it sealed by the native, and implement it. They are **not** gated by J1 and may change production while Suvarṇa waves run. Start prompts: `prompts/L3_{GOCHARA,SANGAM,KSHETRA}_FINAL_BRIEF_PROMPT_v1_0.md`.
- **Suvarṇa does not change their code or data** (charter R8). Its L3 analysis evaluates their latest briefs and re-measures their assets independently. Their claims are evidence, not verdicts.
- **How a family asset is certified (D2).** The family's own orchestrator rebuild counts as the Build exercise, **only if** it was an orchestrator run on the canonical chart whose substep plan completed; a hand-run cutover script does not count. Suvarṇa's independent re-measure then writes the certification (B.FG, B.FS, B.FK). No Gochara certification before F3.G.
- **Waves and families (D2).** The family set (charter R8) and the assets that read it (16 readers measured, 3 of them family assets themselves) live in one versioned file, `00_ARCHITECTURE/control/FAMILY_ASSETS.json`, frozen at J1 (E6.3). Family assets and their readers are **excluded from every wave's completion**: a wave completes without them. Each reader waits asset by asset for its family input to be certified; the tracker shows it as `blocked` with detail `waiting_on_family: <asset>` (ROLE_CONDUCTOR step 7), and it is certified under B.FR.L3, B.FR.L4 or B.FR.L5. No wave waits on a family's own build.
- **The cascade, measured 2026-09-29** (`pg_constraint`, read-only as `suvarna_reader`): eight foreign keys into
  `bodha_msr_signals(signal_id)` are `ON DELETE CASCADE`: from `kala_convergence` (Saṅgam, family), `kala_darshana`,
  `kala_bhavishya`, `kala_activation`, `kala_obstruction` (non-family L3), `bodha_signal_embeddings` and
  `bodha_contradictions` (two keys) (L2). Seven L2 writers have `bodha_msr_signals` as their registry target:
  `bo_sudarshana` (level 1) and `bo_vargottama_dhana` (2) in **wave 0**; `bo_special_lagna` (3), `bo_arudha` and
  `bo_nakshatra_semantic` (4) in wave 1; `bo_laksana` (6) and `bo_laksana_rerank` (9) in wave 2 (A.L2i measures the
  full set from the writers, arch §12.9). Every one of their rebuilds today deletes rows in all seven tables, family
  and non-family alike.
- **F-3 therefore means "cascade removed"**: a migration that leaves no `ON DELETE CASCADE` foreign key into
  `bodha_msr_signals`. Its replacement must not refuse the L2 delete-then-insert (a `RESTRICT` or `NO ACTION` key would,
  R243); dropping the keys and checking referential integrity by detector (`msr_referential_integrity.py`) is the
  expected shape. The native seals F-3 on the Saṅgam session's recommendation; the `decided` line names who lands the
  migration (the `kala_convergence` key is family schema, R8). Strategic Suvarṇa records it.
- **Two couplings bind Suvarṇa:** Saṅgam and Kṣetra rebuild only on Gochara's new generation; and **no L2 MSR asset is
  rebuilt until F-3 is `decided` (F3.LOCK) and the cascade detector reads done (F3.FK: no `ON DELETE CASCADE` key into
  `bodha_msr_signals` in production)**. A decision without the applied migration still cascades. Because wave 0 holds
  two MSR writers, **B.W0 and G2 wait for F3.LOCK and F3.FK**; this is accepted explicitly (the alternative, putting
  every victim table in the same wave under R3 with a snapshot and native approval on every L2 wave, is worse). Saṅgam
  is still certified only after its L2 upstreams are (B.FS waits for B.W2).
- **Hand-back (D2).** When a family session closes, the native records a hand-back decision (HB-G, HB-S, HB-K) that moves that family's assets out of the R8 set, with the family's rebuild runbook attached. From then on they are ordinary Suvarṇa assets. Until then, a rebuild a family asset needs (for example after an upstream change) is parked with lead time by the Steward.
- **Kṣetra is on the L5 critical path.** `mi_bhara` and `mi_sankalpa` read it; Kṣetra is 5–9 weeks from a correct, published field. The native either accepts that, or dispositions those two readers `qualify` pending Kṣetra — a recorded, reversible disposition, never an N/A on Build (N-21).
- **The families report to the tracker** under items F1.G/F1.S/F1.K and F3.G/F3.S/F3.K. A family's own event is not a
  decision: F1.x reads done only when Strategic Suvarṇa records the native's seal (SEAL-G, SEAL-S, SEAL-K).
- **Background:** `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (v1.3) reconciles each family's state and prices "fully enriched".

### 5.4 · The per-asset lifecycle (Tracks I and B)

1. **Brief approved:** disposition, fixes, any asset-specific additions. **Who approves:** the Steward, when the
   disposition is keep (with or without fix designs), enrich or qualify and every addition belongs to a class the
   native approved (N-11) — charter G16, decided with N-1; the native, batched per layer, for retire, consolidate,
   historical, integrate, unresolved, any output change (charter R5) and any addition outside an approved class. Until
   G16 is approved, the native approves every brief. Before J1 the approval is provisional and covers only
   tier-independent designs; full approval follows A.Lxr and the layer's instance acceptance (A.Lxa).
2. **Implement** in a lane: writer, migration or registry change, with a failing-first test. This is the first stage
   allowed to change writers. **Track I starts at N-24** (the Tracks I and B brief), which may come before J1; before J1
   it builds only tier-independent designs of provisionally approved briefs, merged to `suvarna/trunk`, with nothing
   opened to `main` until J1.
3. **Gate review,** then merge to `suvarna/trunk`.
4. **Land:** the wave's fixes go to `main` in one PR per wave group, from a landing branch cut from `origin/main`
   (§6.4), which the native merges; the deploy follows (B.W0M … B.W5M). A wave's fixes are every Track I item for an
   asset in its level range (I.W0 … I.W5, derived from the J1 level map), whatever the asset's layer.
5. **Wait for the wave:** every upstream asset certified and current, every asset at this level merged and deployed
   (the landing merge an ancestor of the deployed commit).
6. **Rebuild** in that level's wave, through the orchestrator (the native dispatches L0 waves).
7. **Re-measure and certify.** Gap rows close only on PASS or rule-computed N/A. Certification records are written. The tracker marks the asset ELEVATED.
8. **If something upstream changes later** (including a family session's or another workstream's change), the
   stale-certification detector (E5.5) invalidates the certification; Exec Suvarṇa re-measures the asset and rebuilds
   it only if its output changed. For a family asset before its hand-back, the Steward parks the rebuild for the family.

**Nirmāṇa's kept assets** enter at step 1 with their current state; their open gaps are the starting delta.

**What each layer brings:**

| Layer | Known specifics |
|---|---|
| L0 | Global, no chart. Top of the map, but spread over four levels (24, 11, 4 and 1 assets at levels 0–3; `bg_concordance` at level 3 sits in W1): four native dispatches, B.L0.0 … B.L0.3, each with its own dump and diff (§6.4b). The first certifications. |
| L1 | Chart-scoped. Canonical chart only, unless N-12 adds others (ruled before the first L0 wave). |
| L2 | `bo_upaya`'s live proof (B.U, level 11). Six chart-conditional rebuilds (R243) are recorded as such. Every wave holding an MSR writer (W0, W1, W2) waits for F3.LOCK and F3.FK. |
| L3 | The three families are owned by their family sessions; Suvarṇa evaluates and certifies them (§5.3). Six tables empty for the canonical chart. `kala_field` holds 10.98 million rows, so the heaviest census and rebuild costs are here. |
| L4 | Nothing kept from Nirmāṇa. Three assets record 139 rows written against 4 present. |
| L5 | Calibration fills over time by design. Three L5 assets sit in W0 (`lel_events`, `mi_vistara`, `mi_jivanaghatana`), one in W1 (`mi_kula`), two in W3. `lel_events` has no writer (R236): its disposition (N-14.R236) is ruled before W0 (B.N14), or it could never read ELEVATED and W0 would never close. `mi_bhara`, `mi_sankalpa` wait on Kṣetra (N-21). |

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
- **Isolation.** The campaign runs in its own folder (`/Users/Dev/suvarna/`), on its own branches (`suvarna/hq`, `suvarna/trunk`, lane branches), with its own hold switch. Other campaigns continue untouched. **Proposed (N-25):** the swarm also runs as its own macOS user with its own settings and GitHub identity, so the boundary is held by the OS and GitHub, not by prompt text. Details: execution architecture §2, §2.4.

### 6.2 · Roles and models

The full swarm is in the execution architecture (§3). In short:

- **Opus 5.5** where judgement decides the outcome: conductor, steward (delegated decisions), architect (algorithms and derivability), gate reviewers.
- **Sonnet 5** for volume: analysts and builders.
- **Scripts** for bookkeeping: tallies, folds, dispatch, monitoring.
- **Effort:** medium by default; high only for algorithm design, high-risk reviews (gate reviews of writer, ledger, auth, reopen and algorithm packets), reopen drafting, the Steward's classifications, and writer or ledger changes; low for mechanical roles. The execution architecture §3.1 and §3.3 name the same set.
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

- **Code changes:** through PRs to `main`, with review and CI. The native merges. **Branches:** lanes branch from
  `suvarna/trunk` (= `main` plus accepted packets; the Conductor merges `origin/main` into it every pass). A PR to
  `main` comes from a landing branch `suvarna/land/<group>` cut from `origin/main`, into which the group's accepted lane
  branches are merged; a packet whose trunk ancestor is not yet on `main` lands in the same or a later group. Source
  branches (`campaign/nikasha-test`, `campaign/nirmana-engine`) are never a base for anything bound for `main`.
- **Deployed means contains:** the landing merge is an ancestor of the deployed commit (`git merge-base
  --is-ancestor`), and the writer files at the deployed commit hash to the packet's recorded values. Other workstreams
  deploy to `main` too, so equality is never the test.
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
- **One native dispatch per L0 level** (levels 0, 1, 2 in W0; level 3, `bg_concordance`, in W1): B.L0.0 … B.L0.3. The
  level-3 asset is split out of W1's normal dispatch and parked for the native like the others. The Steward batches
  the four requests so the native's presence is asked for as few times as the certifications allow.

### 6.5 · Environment (operational lessons)

- **Database access.** Start the Cloud SQL proxy on 5433. Use `~/.config/suvarna/pgenv.sh` (N-20), which logs in as `suvarna_reader` (D6, applied 2026-09-29). Never call `gcloud` per command (it hangs).
- **Power.** Long runs need the machine plugged in with the lid open and automatic OS restarts off. Every stall so far traced to sleep.
- **Census runs.** One census at a time across every session, the families included, through the lock:
  `python -m suvarna_tracker.census_lock --emit -- <census command>` (exit 75 means another census holds it).
- **Worktrees.** One per lane (arch §12.2). Never work in the main checkout, which carries other campaigns' uncommitted state, and never in another campaign's checkout.

### 6.6 · Effort and cost

- **Track E to the freeze:** roughly 200–340 hours of agent effort, E5, E6 and E7 included, across parallel lanes (§5.1).
- **Launch items:** L.11–L.17 roughly 30–55 hours (track briefs, sweeps, tracker additions and the v1.4 code items, runtime, review package); the isolation set-up (L.16a/b/g) is mostly the native's, about half a day.
- **Track A:** about 157 hours of derivability work, 130–250 hours of briefs, 30–65 hours of revalidation, spread across up to six analysts; re-estimated after the first layer.
- **Track F:** priced in the L3 focus-families document; spent by the family sessions, not by Suvarṇa.
- **Tracks I and B:** order of hundreds of agent-hours (10²–10³), including 60–180 hours of per-asset semantic detectors; no defensible figure until G2 measures cost per asset.
- **Native and deploy latency, separate from agent hours:** each PR to `main` waits for the native's merge, then a deploy (about 15–30 minutes each). Before J1: about 11–14 merges (Track E §9: E3 ×3–4, E4 ×4, E7 ×1, E3.4 ×1, E1/E5/E6 grouped ×2–3), plus the F-3 migration. In Track B: one merged-and-deployed PR per wave (6 waves) plus four L0 level dispatches the native makes (B.L0.0–B.L0.3). The reopen's three agendas are approved together; only the three re-seals are serial. Every native decision adds its own latency; the Steward requests each one with lead time (charter §7).
- **Hours are agent effort, not calendar time.** Parallel lanes compress the calendar; the build chain does not compress (execution architecture §6).
- **Review effort is on top:** one gate review per packet, deeper for high-risk packets.

### 6.7 · Runtime (D5)

- **Interim, from launch to G2:** `/loop 10m` in the two execution sessions (a fixed interval, never self-paced),
  re-armed by the native each week (its scheduled tasks expire after 7 days), with the L.15 safeguards in place.
- **Durable, before B.W1:** the Conductor runs as a supervised headless loop of stateless passes
  (`claude -p` with the Conductor prompt, `--permission-mode dontAsk` and the Suvarṇa settings file; never a bypass
  mode). Each pass reads its role files, its queue, the decisions log, the tracker's `snapshot.json` and the event log
  **only from its last committed offset** (not the whole log), and commits the queue and the offset before it ends. The
  Monitor's watchdog relaunches a stalled pass (heartbeat older than three loop intervals; at most three restarts an
  hour, then the hold and a park). Sessions roll over on a pass count or context threshold. Lane agents run as separate
  processes in their own worktrees, started only through the lane launcher (`python3 -m suvarna_tracker.lane_launch`,
  which fixes the settings file and `dontAsk`). A usage-limit pause is read and waited out, never restart-looped;
  whether to bill the runner by API key is a native decision (N-23). Details: execution architecture §5.5.

---

## §7 · Dependencies outside the plan

| Dependency | Owner | Needed by | Status | Action |
|---|---|---|---|---|
| Build engine landed and deployed | Nikaṣa Engine (N-2) | J1 | 10 engine commits (of 200 ahead of `main`), no PR | E3 |
| Migrations 1094–1096 in production | deploy pipeline | R55, R38 | not applied; inside L3's reserved range (N-26) | E3 |
| The F-3 foreign-key migration (cascade removed) | per the F-3 `decided` line | W0 and every L2 MSR wave (F3.FK) | not written | F-3 |
| `bo_upaya` fix (restore the delete) | Suvarṇa, Track E (N-6: fix now) | R246; the withholding | direction ruled, handoff written | E4 |
| C1 crash and orphan handling | build engine | clean build-history verdicts | not started | E3 |
| `suvarna_reader` (D6) | native (admin script) | every read; J1 | **applied** 2026-09-29 | L.10 (done) |
| Swarm isolation: OS user, GitHub identity, branch protection (N-25) | native | N-1 | proposed | L.16a, L.16g, L.16b |
| Builder identity (D1) | native merges E7.1, provisions E7.2 | Track B | not started | E7 |
| L3 family sessions (Gochara, Saṅgam, Kṣetra) | their own sessions (N-17) | L3 evaluation; family certification; L2 MSR rebuilds (F-3) | briefs being written; Gochara production on hold | they report to the tracker; Suvarṇa never changes their assets |
| Migration numbers | Pūrṇa, Jātaka and L3 hold reserved ranges | every migration | Suvarṇa has no range | reserve one number at a time (arch §12.5) |

**Coordination rule with live workstreams:** before Suvarṇa touches an asset another live workstream is changing, the two agree who owns that asset for the period (a lease, arch §12.4). Findings go both ways. The rule is recorded in the track brief. The family sessions are not bound to notify Suvarṇa of their changes; the pre-wave fingerprint and the stale-certification detector are the tripwires.

---

## §8 · Native decision points

In the order they are needed. **Status is read from the authoritative decisions log**
(`$SUVARNA_HOME/run/DECISIONS.jsonl`, written only through `python -m suvarna_tracker.decide`; from v1.4 only by
Strategic Suvarṇa with the native present, charter §2; the committed `control/suvarna/state/DECISIONS.jsonl` on
`suvarna/hq` is a mirror) as of 2026-09-29. `delegated` is not decided.

| ID | Decision | When | Recommendation | Status |
|---|---|---|---|---|
| N-1 | Approve the v1.4 plan set (including the charter v1.3–v1.4 changes, the track briefs, and **G16 yes or no**) | after §5.0b | Approve, with G16 | open: requested |
| N-25 | Isolation: run the swarm as a separate macOS user with its own settings, GitHub identity and read-only view of the decisions log; `chmod 600` the two `dbenv` files; branch protection on `main` (arch §2.4) | before N-1 | Yes to all three | open (new, review pass 2) |
| N-26 | Build-engine migrations 1094–1096 sit in L3's reserved range 1070–1119: renumber at landing to freshly reserved numbers, or have the L3 range owner confirm them | before E3.2's PRs open | Renumber (legal: never applied) | open (new, Track E §3.3) |
| N-14.R236 | `lel_events` (no writer): a declared no-writer asset whose Build and Idem cells are N/A by a registry rule (with N-13/N-22), or give it a writer in Track I | before W0 (B.N14) | Declared no-writer, by registry rule | open (new) |
| N-2 | Fold the build-engine work into the Nikaṣa Engine session | now | Yes | **decided: yes** |
| N-3 | Landing approach for PR #2736: split into code and evidence, retarget to `main` | now | Yes | **decided: yes**; carried out as fresh branches from `main`, #2736 left open for the native to close (§5.1 E4) |
| N-4.T1–T3 | Approve the three reopen agendas, together | once E2.1 and A.H are done | Review as presented, as one batch | open |
| N-5.T1–T3 | Sign each re-seal, in order T1 → T2 → T3 | after the redlines | — | open |
| N-6 | `bo_upaya`: fix now (Track E), or defer to L2 | now | Fix now | **decided: fix now** (live proof in its wave, §4.2) |
| N-7.T4 · N-7.L0 | Accept tier 4 · accept the L0 instance (revalidated against the re-sealed tiers, A.L0v) | end of E2 | — | open |
| N-8 | Engine freeze | J1 | — | open |
| N-9 | G2: L0 pilot results and rollout pace | G2 | — | open |
| N-10.L1.i–L5.i | Accept each layer instance (after its revalidation; lifts the PROVISIONAL banner) | before the layer's first wave | — | open |
| N-10.L0.c–L5.c | Sign each layer close (L0's instance was accepted at N-7.L0) | per layer, batched | — | open |
| N-11 | Approve asset-specific addition classes (§2.3) | before L2 briefs, at the latest | Decide per class | open |
| N-12 | Certify the canonical chart only, or several; confirm none of the 7 charts is an external user's | **before the first L0 wave** (D4) | Canonical only; other charts recorded "served from stale L0 inputs" (§6.4b) | open |
| N-13 | N/A for "writes nothing to its own table" and "update-only" assets (R247) | with N-22 | Rule it as registry rules | open |
| N-14 | Data findings with owners outside the inspector: `build_dependencies` (R219), `ka_gochara` registry (R240); `lel_events` (R236) is split out as N-14.R236 | per layer | — | open; R240 sits with L3 Gochara |
| N-15 | Pace and budget ceilings | before launch | — | **decided: no ceilings**; spend metered and reported |
| N-16 | Nirmāṇa's database record: leave it reading "frozen", or supersede it with the privileged control writer | any time | Leave it | open |
| N-17 | Track F: how Suvarṇa relates to the L3 families | now | Family sessions own them; Suvarṇa evaluates | **decided** |
| N-18 | Isolation: dedicated folder and branch model | now | Yes | **decided: yes**; set up 2026-09-29 |
| N-19 | Approve the autonomy charter | before execution | — | **decided: approved** v1.1; amended to v1.2 by CHARTER-AMEND-A-C; v1.3–v1.4 changes confirmed with N-1 |
| N-20 | Where the read-only database credential lives | before launch | — | **decided:** `~/.config/suvarna/pgenv.sh`, mode 600 |
| N-21 | Kṣetra on the L5 critical path: accept, or disposition `mi_bhara`, `mi_sankalpa` `qualify` pending Kṣetra | before L5 briefs | — | open (new, D2) |
| N-22 | Per-gate applicability rules (N/A by layer or column pattern), ruled once per gate | before E6.5 | Start from D3's proposed defaults | open (new, D3) |
| N-23 | Headless runner billing: subscription windows, or an API key | before L.14 | — | open (new, D5) |
| N-24 | Approve the Tracks I and B brief | before J1 | — | open (new) |
| HB-G · HB-S · HB-K | Hand a closed family's assets back to Suvarṇa (out of the R8 set), with its rebuild runbook | when each family session closes | — | open (new, D2) |
| SEAL-G · SEAL-S · SEAL-K | Seal each family's final brief (recorded by Strategic Suvarṇa; closes F1.G, F1.S, F1.K) | when each brief is ready | — | open (new) |
| N-CLOSE | Accept the closure report | end | — | open |
| F-0 | Gochara: deploy before switching authority | now | Yes | **decided: yes** (ADK-0027) |
| F-5 | Gochara: served horizon | — | — | **decided: full century** (by F-0) |
| F-2, F-3, F-6 | Saṅgam: keep or retire into `kala_field`; the cascade lock; Mode D | F-3 before wave 0 | F-3: remove the cascade from all eight foreign keys into `bodha_msr_signals` (§5.3) | **delegated** to L3 Saṅgam; the native seals; Strategic Suvarṇa records `decided`. F-3 and its applied migration (F3.FK) gate every wave with an L2 MSR writer, W0 included |
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
| D6 | Read-only login `suvarna_reader`, set up by a native-run admin script; Monitor verifies continuously (applied 2026-09-29) | §3.8, L.10 |

---

## §9 · Tracking

**The live view is the real-time tracker** (execution architecture §11): the plan model (`00_ARCHITECTURE/control/suvarna/plan_model.json`), an append-only event log every role writes to as things happen, the decisions log every native gate reads, and detectors that decide "done" wherever a check exists. It shows what runs in parallel and in sequence, where we are, what is next, what waits on the native, and the measures below, within about a second of a change. The plan model changes with this plan, in the same commit.

- **Native gates** (`done_by: decision`) are done only when the decisions log has a `decided` line for their id. A
  `delegated` line shows as waiting. A decision event that disagrees with the log shows as a conflict.
- **Detector types** (arch §11.7): the v1.3 types are built (L.13); the v1.4 changes and new types (`fk_no_cascade`,
  `acks_from`, `main_protected`, ancestry in the deploy checks, head-ref resolution) are code items listed in
  REVIEW_PASS2_DISPOSITION. A detector whose expected input does not exist yet reads pending; one that cannot measure,
  or whose spec is still empty (`pinned_by`), reads unknown; none is ever done.

**Weekly scorecard** (from the tracker and ledgers, never typed by hand):

- assets ELEVATED, per layer (from the exact function after E6.3t; unknown before);
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
| L2 and L3 collide through the cascade lock | an L2 MSR rebuild wipes Saṅgam and four non-family L3 tables and two L2 tables, or is refused by them | No L2 MSR rebuild before F-3 is `decided` **and** F3.FK sees no cascading key (charter R1); Saṅgam certified only after its L2 upstreams. |
| The swarm acts outside its grant | a merge, a foreign credential, a forged decision | Separate OS user, own GitHub identity, branch protection on `main`, decisions log read-only to the swarm (N-25, arch §2.4); explicit deny rules and the hold-guard hook as a second line; the Monitor's `isolation` and decision-writer checks. |
| The first loop fails on the served chart | a wave breaks what production serves | Wave rehearsal off production (E5.6); serving canary per wave (E5.3); L0 dump rehearsal (E5.7). |

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
| Build engine | 200 commits ahead of `main`, 10 of them the engine's; no PR | `git rev-list --count origin/main..campaign/nirmana-engine`; `origin/l3/kala-layer-briefs..campaign/nirmana-engine` (Track E §3.1); `gh pr list` |
| Cascade into `bodha_msr_signals` | 8 `ON DELETE CASCADE` keys from 7 tables; 7 writers with that registry target (2 in W0, 3 in W1, 2 in W2) | `pg_constraint` where `confrelid = 'bodha_msr_signals'::regclass` and `confdeltype = 'c'`; `asset_registry.target_table` (2026-09-29, as `suvarna_reader`) |
| Wave composition | W0 (levels 0–2): 39 L0, 12 L1, 2 L2, 9 L3, 3 L5 · W1: 1 L0, 7 L1, 3 L2, 1 L3, 1 L5 · W2: 14 L2 · W3: 4 L2, 11 L3, 2 L5 · W4: 9 L4 · W5: 9 L5; L0 by level 24/11/4/1 | `detectors.dag_levels` algorithm over `asset_registry.depends_on` (2026-09-29) |
| Permissions in force | user settings `bypassPermissions` with `Bash(*)`, `Edit(**)`, `Write(**)`, `mcp__github__*`, `mcp__postgres__*`; repo settings allow `git push*`, `gh pr *`, `gh api *`, sourcing the two `dbenv` files (mode 644) | `~/.claude/settings.json`, `.claude/settings.json` (verified by Strategic Suvarṇa and review pass 2) |
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
