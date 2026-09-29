---
artifact: SUVARNA_CAMPAIGN_PLAN
canonical_id: SUVARNA_CAMPAIGN_PLAN
version: "1.2"
status: DRAFT — for native review (several review rounds expected before any execution)
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
decision_owner: Native (Abhisek Mohanty)
supersedes: "SUVARNA_CAMPAIGN_PLAN_v1_1.md (v1.0 before it). Earlier: succeeds the Nirmāṇa elevation campaign (see NIRMANA_SUPERSESSION_RECORD_v1_0.md, PR #2751)."
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
| **Nikaṣa** (निकष, touchstone) | The engine. The system that tests and certifies an asset: four tiers, inspector, tracker, ledgers, detectors. If decision N-2 is approved, it also takes in the build engine it depends on. |
| **Strategic Suvarṇa** | This session. Plans, discusses, rules, writes briefs. Never executes. |
| **Nikaṣa Engine** | The session that builds and freezes the engine (Track E). |
| **Exec Suvarṇa** | The session that runs the elevation (Tracks A, I, B). |
| **L3 Gochara · L3 Saṅgam · L3 Kṣetra** | Three family sessions. Each seals a final brief for its family and implements it (N-17). Not part of the Suvarṇa swarm; not bound by its charter. |

- Suvarṇa is what the touchstone tests. The engine is finished first; the campaign runs on it.
- "Nirmāṇa" now names two things: the superseded elevation campaign, and a still-live build-engine
  branch (`campaign/nirmana-engine`). This plan calls the second one "the build engine" (§5.1, E3).

### 0.2 · What this document is

- The master plan. It fixes the end state, the standard, the tracks, the gates and the operating model.
- **Companions:** `SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` (how it runs, including the real-time tracker, §11), `SUVARNA_AUTONOMY_CHARTER_v1_0.md` (what the swarm may decide), `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (the three L3 families), `SUVARNA_DOCUMENT_MAP_v1_0.md` (every document in the campaign).
- Each stage gets its own brief later. A brief never contradicts this plan; if it must, the plan is revised first (§10).
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

Counted from the rows. The header tallies drifted and were repaired on 2026-09-29 (register v2.8); the tracker's detectors now check them on every change.

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

- **These have not been re-measured since the three waves of fixes.** Most defects behind T2 and T3 are now closed. A fresh scorecard is the first step of Track E.

### 3.6 · The documents

- **Tiers 1–3:** sealed. A reopen agenda is ruled (D2, 2026-09-27): 32 clause fixes across the three documents (§5.1, E2), plus the derivability mechanisms Track A will harvest (§5.2); both go into one reopen at J1.
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

- **L3 Gochara workstream** (`l3/gochara-autonomous-wp0-7`). It applied a production migration (1150) to `ka_gochara`. On 2026-09-28 it switched the canonical chart to `'4.0'` before the deploy-before-switch directive (F-0) arrived, and reversed it six minutes later; nothing consumed the switched data (ADK-0027). It now rebuilds on the full century under `'4.1'`; the native has put its execution on hold.
- **Three L3 family sessions** (from 2026-09-29): Gochara, Saṅgam and Kṣetra each seal a final brief and implement it (N-17).
- **Pūrṇa**, **Jātaka**: separate campaigns with their own migration reservations.

---

## §4 · The shape: parallel tracks, one join, dependency waves

```
NOW ─┬─ TRACK E  Engine: tools · build engine · 32 clause fixes · bo_upaya · landing ─────┐
     │                                                                                    │
     ├─ TRACK A  Analysis, all six layers at once (read-only):                           ├─► JOIN J1
     │           census · layer-instance drafts · asset briefs · dispositions · fix       │   one combined reopen
     │           designs · harvest of what the tiers are missing                          │   (clause fixes + derivability)
     │                                                                                    │   + ENGINE FREEZE (native)
     └─ TRACK F  L3 focus families: Gochara · Saṅgam · Kṣetra — run by three family       │
                 sessions (sealed brief, then implementation); Suvarṇa evaluates  ─────────┘
                                                                                          │
     TRACK I  Implementation: fixes for every layer, in parallel lanes  ◄─────────────────┤
              (tier-independent fixes may start before J1; certified only after it)       │
                                                                                          │
     TRACK B  Rebuild and certify: one wave per dependency level, in order,  ◄────────────┘
              the moment a level's fixes are merged and its inputs are certified
              ├─ checkpoint G2 after levels 0–2 (the wide top, mostly L0/L1): loop proven, cost measured
              └─ layer closes as each layer's last asset certifies (native, batched)

     CLOSURE  whole-plane re-measure · [TRANSFERS] hand-over · closure report (native)
```

### 4.1 · Why this shape

- **Only data forces order.** Analysis, design and coding do not change data, so they run across every layer at once. Only rebuilding has to follow the dependency map.
- **The engine freezes before anything is certified.** Every wave of fixes so far found at least one path that could close a gap without a real measurement: a failed count query read as "not applicable", never-started build rows counted as runs, `ka_kshetra` passing on a refused rebuild, `bo_upaya` passing on a rebuild that cannot succeed. Certifying before the freeze would bake those in.
- **One reopen, not six.** The clause fixes are already known. The derivability machinery is best discovered by drafting every layer's instance. So Track A harvests what is missing, and both go into one reopen per document at J1.
- **Asset waves, not layer gates.** Many L3 assets need only L0 and L1. They rebuild as soon as those are certified, without waiting for L2.
- **Fix first, walk once.** The dependency map is 27 levels deep and ends in a long thin chain. That chain is the critical path; parallelism cannot shorten it. So every asset's fixes land before it is rebuilt, and the chain is walked once (execution architecture §6).
- **L0 still goes first**, because it sits at the top of the map. Its certification is the first proof that the full loop works: find, fix, rebuild, certify. That has never happened yet; there are zero certification records today.

### 4.2 · The gates

| Gate | Passes when | Who rules |
|---|---|---|
| **J1 · Engine freeze** | T1–T5 pass in production tooling on `main`; the combined reopen is re-sealed (T1 → T2 → T3); tier 4 and the L0 instance are accepted; R24, R39 and R71 closed; R244 closed or deferred with withholding (N-6); the build engine deployed and its migrations verified | **native** |
| **G2 · Loop proven** | dependency levels 0–2 certified; cost per asset measured; §5.4's lifecycle confirmed or revised | **native**; a checkpoint, not a stop, unless the native halts |
| **G3.Lx · Layer close** | that layer CLOSED (§1.2) | **native**, batched |
| **G4 · Campaign complete** | §1.3 | **native** |

---

## §5 · Track detail

Each track becomes its own brief before execution. Briefs are written here, in Strategic Suvarṇa.

### 5.0 · First items (hours, not a stage)

These are small and run first, alongside everything else.

| Item | Why | Effort |
|---|---|---|
| Relay F-0 and R240 to the L3 Gochara workstream | They were changing `ka_gochara` in production | **done** 2026-09-28 (ADK-0027) |
| Merge PR #2751 (Nirmāṇa supersession) | A fresh session must find the decision first | open; the native merges |
| Fix the register's header tallies | They drifted (190 recorded vs 180 counted) | **done** 2026-09-29 (v2.8; detector-checked) |
| Repair the rows that break the register table (R244, R246; R99 was well-formed) | Tools misread them | **done** 2026-09-29 |
| Record Suvarṇa and this plan in `CURRENT_STATE` | Same reason as the supersession | after PR #2751 |
| Name the sessions | Strategic Suvarṇa · Nikaṣa Engine · Exec Suvarṇa | **done** |

### 5.0b · Launch readiness — what must be true before execution starts

Execution starts when the native approves this plan (N-1). Before that:

| Item | Owner | State (2026-09-29) |
|---|---|---|
| This plan brought up to date (v1.2) | Strategic Suvarṇa | this document |
| Autonomy charter drafted | Strategic Suvarṇa | drafted (v1.1); approval is N-19 |
| Role prompts for the swarm, each reporting to the tracker | Strategic Suvarṇa | after the charter |
| Runbook, and start prompts for Exec Suvarṇa and Nikaṣa Engine | Strategic Suvarṇa | after the role prompts |
| Isolation: `/Users/Dev/suvarna`, branches `suvarna/hq` and `suvarna/trunk` | Strategic Suvarṇa | **done** |
| Monitor: environment checks and repair | Strategic Suvarṇa | **done** (`suvarna_tracker.monitor`) |
| Permanent read-only database credential | native decided (N-20) | **done**: `~/.config/suvarna/pgenv.sh`, mode 600 |
| Budget ceilings (N-15) | native | **decided: none**; spend is reported |
| Two or three review passes of the plan set | Strategic Suvarṇa | after the documents |
| Independent third-party review, findings folded | reviewer (GPT-6 Astra recommended) | after the review passes |

- **The Nikaṣa Engine session may start before N-1** once its start prompt and the charter exist, if the native agrees: Track E is the longest stretch before the freeze and changes nothing another track depends on.

### 5.1 · Track E — the engine (session "Nikaṣa Engine")

Four workstreams, running in parallel.

**E1 · Tooling.**
1. **Measure before changing.** Re-run T1–T5 on today's tooling and publish the scorecard.
2. **Close the remaining tooling rows:**
   - detector gaps R245, R248, R249, R250;
   - provenance: R226 (`--live` re-derive-and-diff), R228 (stale source references), R229 (unowned tables);
   - ledger identity: R251 (the rest of the crosswalk);
   - waiting on others: R55 (needs migration 1094) and R246 (needs the `bo_upaya` fix).
3. **Prove it again.** Re-run T1–T5.
- **Rough size:** 30–50 hours.

**E2 · The clause fixes.**
- The 32 rows the D2 ruling already agreed, drafted per document and held for the combined reopen at J1.
- **Rough size:** 20–30 hours.

**E3 · The build engine.**
- Bring the `campaign/nirmana-engine` work under this track (N-2, approved 2026-09-29).
- Land it: PR to `main`, review, deploy.
- Apply and verify migrations 1094 and 1095.
- Finish the carried items: A2b, A3b, R217.
- C1 (crash and orphan handling) and C2 (stuck states): **not required for the freeze.** They reduce noise, so they run alongside Track B.
- D1/P10 (R39): the engine judged by its own Build checks, last.
- **Rough size:** 30–50 hours to the freeze; C1 and C2 afterwards.

**E4 · Landing and the `bo_upaya` fix.**
- Split PR #2736 into code and evidence PRs, retarget both to `main`, and add the inspector's tests to CI (N-3, approved).
- Fix `bo_upaya` as a sanctioned writer exception (N-6: fix now, approved): about half a day. It unblocks R246, `ka_kshetra` (which reads from it) and the end of the withholding.
- **Rough size:** 10–20 hours.

- **Track E total to the freeze: roughly 90–150 hours of agent effort**, split across parallel lanes. The derivability work moves to Track A (below); it is not removed, only taken off the engine's path.

### 5.2 · Track A — analysis, all layers at once (session "Exec Suvarṇa")

Read-only. Runs across all six layers from day one.

For each layer:
1. **Fresh census** with today's inspector. Provisional until J1; re-measured after it.
2. **Layer-instance draft**, derived from the tiers and the census. Wherever the tiers do not supply what the draft needs, record it as a **tier gap**. Do not invent.
3. **Asset briefs**, one per asset, with gap rows, proposed additions and opportunities.
4. **A disposition per asset:** keep, fix, enrich, consolidate, retire.
5. **Fix designs,** each marked **tier-independent** (can be built before J1) or **tier-dependent** (waits for the reopen).

**Order inside the track:** tier gaps first, so J1 is not delayed; asset briefs second.

**What it feeds:**
- the tier-gap harvest → the combined reopen at J1;
- fix designs → Track I.

- **Rough size:** the derivability work priced at about 157 hours in the register, plus briefs for 127 assets. Spread across up to six parallel analysts, with the Architect on the derivability mechanisms. Re-estimated after the first layer's drafts.

### 5.3 · Track F — the L3 focus families

Gochara, Saṅgam and Kṣetra get dedicated algorithm and enrichment work, beyond conformance to the nine gates.

- **Run by three family sessions (N-17, 2026-09-29).** L3 Gochara, L3 Saṅgam and L3 Kṣetra each verify their family's state, bring its rulings to the native (Saṅgam: F-2, F-3, F-6; Kṣetra: F-1, F-4), write a final brief on the tier-4 template, have it independently reviewed, get it sealed by the native, and implement it. Start prompts: `prompts/L3_{GOCHARA,SANGAM,KSHETRA}_FINAL_BRIEF_PROMPT_v1_0.md`.
- **Suvarṇa does not change their code or data.** Its L3 analysis (Track A) evaluates their latest briefs and re-measures their assets independently with the inspector. Their claims are evidence, not verdicts.
- **Two links still bind Suvarṇa:** Saṅgam and Kṣetra rebuild only on Gochara's new generation; and **no L2 MSR asset is rebuilt until F-3 (the cascade lock) is sealed.**
- **The families report to the tracker** under items F1.G/F1.S/F1.K (sealed briefs) and F3.G/F3.S/F3.K (implemented).
- **Background:** `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` reconciles each family's current state and prices "fully enriched".

### 5.4 · The per-asset lifecycle (Tracks I and B)

1. **Brief approved:** disposition, fixes, any asset-specific additions.
2. **Implement** in a lane: writer, migration or registry change, with a failing-first test. This is the first stage allowed to change writers.
3. **Gate review,** then merge to `suvarna/trunk`.
4. **Wait for the wave:** every upstream asset certified, and every asset at this level merged.
5. **Rebuild** in that level's wave, through the orchestrator.
6. **Re-measure and certify.** Gap rows close only on PASS or justified N/A. Certification records are written. The tracker marks the asset ELEVATED.
7. **If something upstream changes later,** this asset is re-measured, and rebuilt only if its output changed.

**Nirmāṇa's kept assets** enter at step 1 with their current state; their open gaps are the starting delta.

**What each layer brings:**

| Layer | Known specifics |
|---|---|
| L0 | Global, no chart. Top of the map. The first certifications. |
| L1 | Chart-scoped. Canonical chart first (N-12). |
| L2 | `bo_upaya`'s fix, if not already done in Track E. Six chart-conditional rebuilds (R243) are recorded as such. N/A policy for "writes nothing to its own table" assets (N-13). |
| L3 | The three focus families are owned by their family sessions; Suvarṇa evaluates them. Six tables empty for the canonical chart. `kala_field` holds 10.98 million rows, so the heaviest census and rebuild costs are here. |
| L4 | Nothing kept from Nirmāṇa. Three assets record 139 rows written against 4 present. |
| L5 | Calibration fills over time by design. `lel_events` has no writer (R236). |

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

- **Strategic Suvarṇa** writes every brief, prepares every native decision and folds strategy changes into this plan.
- **Execution sessions** run packets: build → report → gate review → corrections → fold. They never change this plan; they raise findings.
- A new session is opened only when a track needs its own context. The plan names it first. The three L3 family sessions are the first such case (§5.3).
- **Isolation.** The campaign runs in its own folder (`/Users/Dev/suvarna/`), on its own branches (`suvarna/hq`, `suvarna/trunk`, lane branches), with its own hold switch. Other campaigns continue untouched. Details: execution architecture §2.

### 6.2 · Roles and models

The full swarm is in the execution architecture (§3). In short:

- **Opus 5.5** where judgement decides the outcome: conductor, steward (delegated decisions), architect (algorithms and derivability), gate reviewers.
- **Sonnet 5** for volume: analysts and builders.
- **Scripts** for bookkeeping: tallies, folds, dispatch, monitoring.
- **Effort:** medium by default; high only for algorithm design, high-risk reviews and reopen drafting; low for mechanical roles.
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

- **Track E to the freeze:** roughly 90–150 hours of agent effort, across parallel lanes (§5.1).
- **Track A:** about 157 hours of derivability work plus briefs for 127 assets, spread across up to six analysts; re-estimated after the first layer.
- **Track F:** priced in the L3 focus-families document; spent by the family sessions, not by Suvarṇa.
- **Tracks I and B:** estimated at G2 from measured cost per asset.
- **Hours are agent effort, not calendar time.** Parallel lanes compress the calendar; the build chain does not compress (execution architecture §6).
- **Review effort is on top:** one gate review per packet, deeper for high-risk packets.

---

## §7 · Dependencies outside the plan

| Dependency | Owner | Needed by | Status | Action |
|---|---|---|---|---|
| Build engine landed and deployed | Nikaṣa Engine, if N-2 is approved | J1 | 200 commits, no PR | E3 |
| Migrations 1094, 1095 in production | deploy pipeline | R55, R38 | not applied | E3 |
| `bo_upaya` fix (restore the delete) | Suvarṇa, Track E (N-6: fix now) | R246; lifting the withholding | direction ruled, handoff written | E4 |
| C1 crash and orphan handling | build engine | clean build-history verdicts | not started | E3 |
| L3 family sessions (Gochara, Saṅgam, Kṣetra) | their own sessions (N-17) | Suvarṇa L3 evaluation; L2 MSR rebuilds (F-3) | briefs being written; Gochara execution on hold | they report to the tracker; Suvarṇa never changes their assets |
| Migration number ranges | Pūrṇa, Jātaka, L3 | every migration | reserved ranges exist | check reservations before numbering |

**Coordination rule with live workstreams:** before Suvarṇa touches an asset another live workstream is changing, the two agree who owns that asset for the period. Findings go both ways. The rule is recorded in the stage brief.

---

## §8 · Native decision points

In the order they are needed. Status as of 2026-09-29; the live record is the decisions log (`hq/00_ARCHITECTURE/control/suvarna/state/DECISIONS.jsonl`) and the tracker.

| ID | Decision | When | Recommendation | Status |
|---|---|---|---|---|
| N-1 | Approve this plan (after review rounds) | after §5.0b | — | open: the native is reviewing |
| N-2 | Fold the build-engine work (`campaign/nirmana-engine`) into the Nikaṣa Engine session | now | Yes | **decided: yes** (2026-09-29) |
| N-3 | Landing approach for PR #2736: split into code and evidence, retarget to `main` | now | Yes | **decided: yes** |
| N-4 | Approve each reopen agenda: T1, then T2, then T3 | E2, three times | Review each as presented | open |
| N-5 | Sign each re-seal | E2, three times | — | open |
| N-6 | `bo_upaya`: fix now (Track E) as a sanctioned writer exception, or defer to L2 | now | Fix now | **decided: fix now** |
| N-7 | Accept tier 4; accept the L0 instance | end of E2 | — | open |
| N-8 | Engine freeze | J1 | — | open |
| N-9 | L0 pilot results and rollout pace | G2 | — | open |
| N-10 | Accept each layer instance; sign each layer close | per layer, batched | — | open |
| N-11 | Approve asset-specific addition classes (§2.3) | before L2, at the latest | Decide per class | open |
| N-12 | Elevation certifies the canonical chart only, or several charts | before L1 | Canonical chart first; multi-chart as a recorded addition | open |
| N-13 | N/A policy for "writes nothing to its own table" and "update-only" assets (R247) | before L2 | — | open |
| N-14 | Data findings with owners outside the inspector: `lel_events` (R236), `build_dependencies` (R219), `ka_gochara` registry (R240) | per layer | — | open; R240 now sits with L3 Gochara |
| N-15 | Pace and budget: model routing, review depth, spend ceiling per stage and track | before launch | Ceilings per track, reviewed weekly | **decided: no ceilings**; spend metered and reported |
| N-16 | Nirmāṇa's database record: leave it reading "frozen", or supersede it with the privileged control writer | any time | Leave it | open |
| N-17 | Track F: how Suvarṇa relates to the L3 families | now | — | **decided:** three family sessions own them; Suvarṇa evaluates (§5.3) |
| N-18 | Isolation: dedicated folder and branch model | now | Yes | **decided: yes**; set up 2026-09-29 |
| N-19 | Approve the autonomy charter | before execution | Review the draft | **requested**: draft v1.1 ready |
| N-20 | Where the permanent read-only database credential lives | before launch | A file outside every repository (mode 600) | **decided:** `~/.config/suvarna/pgenv.sh`, set up 2026-09-29 |
| F-0 | Gochara: deploy before switching authority | now | Yes | **decided: yes** (ADK-0027) |
| F-5 | Gochara: served horizon | — | — | **decided: full century** (by F-0) |
| F-2, F-3, F-6 | Saṅgam: keep or retire into `kala_field`; the cascade lock; Mode D | before Saṅgam design | — | **delegated** to L3 Saṅgam; the native seals. F-3 gates L2 MSR rebuilds |
| F-1, F-4 | Kṣetra: W7 or interim clear; 6 classes or more | before Kṣetra rebuild | — | **delegated** to L3 Kṣetra; the native seals |

---

## §9 · Tracking

**The live view is the real-time tracker** (execution architecture §11): the plan model (`00_ARCHITECTURE/control/suvarna/plan_model.json`), an append-only event log every role writes to as things happen, and detectors that decide "done" wherever a check exists. It shows what runs in parallel and in sequence, where we are, what is next, what waits on the native, and the measures below, within about a second of a change. The plan model changes with this plan, in the same commit.

**Weekly scorecard** (from the tracker and ledgers, never typed by hand):

- assets ELEVATED, per layer;
- certification records;
- open gap rows, by gate and layer;
- open register rows, by severity;
- T1–T5 status (until J1);
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
| The engine stage never ends | E2 keeps growing | Closed agendas; derivability harvested in parallel (Track A); transcription rows close as each layer instance is derived; freeze criterion fixed in §4.2. |
| Another false pass | a gap closes, then the asset fails | Only PASS or justified N/A closes; R246 detector; mutation-proven tests; gate reviews. |
| Collision with live workstreams | two sessions change one asset | Coordination rule (§7); check live work at every session start. |
| Register drift | tallies disagree with rows | Computed tallies (§5.0). |
| Environment fragility | stalls, dropped connections | §6.5 rules. |
| Review fatigue | gates accept quickly | Fresh reviewer per packet; independent reviewers for plans and rulings. |
| Scope creep from opportunities | layers slow down | Opportunities never block; ruled in batches. |
| Implementation larger than expected | measured cost per asset high at G2 | Re-estimate at G2 from measured data; the native sets the pace. |
| A production-visible action on a stale authorization | an agent acts on an older approval after a newer directive (the 2026-09-28 Gochara switch) | Charter §2 and §6: newest decision wins unread; decisions log re-read at the moment of action; named preconditions; reversal is the safe direction. |
| The live view drifts from work owned elsewhere | the tracker shows a family session's item out of date | The family prompts require them to report to the tracker; detectors read their commits where possible. |
| L2 and L3 collide through the cascade lock | an L2 MSR rebuild wipes Saṅgam, or is refused by it | No L2 MSR rebuild before F-3 is sealed (charter R1). |

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
| Register tallies repaired | v2.8, 252 rows, 180 open | `NIKASHA_CHANGE_REGISTER_v2_0.md` @ `2a78ec64d`; tracker detectors `register_tally_consistent`, `register_wellformed` |
| Gochara switch and reversal | 19:22:58 → 19:29 UTC 2026-09-28; no consumer | ADK-0027 (`33b725778`); Gochara session's read-only check |

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
