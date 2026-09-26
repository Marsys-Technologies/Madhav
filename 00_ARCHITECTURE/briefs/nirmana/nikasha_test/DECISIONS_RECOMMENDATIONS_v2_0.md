---
artifact: NIKASHA_TEST_DECISIONS_RECOMMENDATIONS
canonical_id: NIKASHA_TEST_DECISIONS_RECOMMENDATIONS
version: "2.0"
status: FINAL — rulings adopted 2026-09-27 under native delegation ("use Fable to reconcile it and freeze it"); DECISIONS_FOR_THE_NATIVE.md carries each ruling verbatim
produced_on: 2026-09-27
campaign_id: nikasha-test
supersedes: DECISIONS_RECOMMENDATIONS_v1_0.md (status → SUPERSEDED, body untouched)
responds_to: DECISIONS_FOR_THE_NATIVE.md (v1.0, six decisions D1–D6)
reconciles: 00_ARCHITECTURE/briefs/reviews/REVIEW_NIKASHA_DECISIONS_RECOMMENDATIONS_v1_0.md (GPT-6 Astra, 2026-09-27; verdict REJECT — D1/D4/D6 REJECT, D2/D3/D5 ACCEPT_WITH_CORRECTIONS; 27 fact checks)
authored_by: Claude Fable session NIKASHA-DECISIONS-FREEZE-20260927
decision_owner: Native (this reconciliation delegated)
evidence_snapshots: >
  Nikaṣa: /Users/Dev/madhav-nikasha @ 857a86c03 (campaign/nikasha-test; PR #2736 OPEN).
  Engine: /Users/Dev/madhav-engine @ 73385d72f (campaign/nirmana-engine; 198 commits ahead of origin/main;
  no PR — `gh pr list --head campaign/nirmana-engine` empty; the worktree now also carries uncommitted B2 work:
  cockpit/stats/route.ts and AssetRow.tsx modified, migration 1096 untracked). Read-only production DB via port 5433
  at DB now() 2026-09-26T20:03Z: asset_throughput.rows_per_second NULL 268/268; build_runs state='failed' with empty
  last_error 288/419 (761 runs); asset_throughput.duration_seconds ABSENT; build_run_assets.blocked_by_asset_id
  ABSENT — nothing from the engine branch is deployed.
changelog:
  - "2.0 (2026-09-27): FINAL. Every review finding re-verified against the cited file:line / commit / code rather than taken on trust. 33 findings (26 numbered + 7 in §4): 31 UPHELD, 2 PARTLY UPHELD (D4.5, D6.5), 0 REBUTTED; all 27 fact-table verdicts confirmed. D1, D4 and D6 rulings rewritten; D2, D3 and D5 corrected in place. Supersedes v1.0."
---

# Rulings on the six decisions — reconciled and final

**Method.** The review's job was to find what is wrong with v1.0; this document's job is to find what is
true. Each of its findings was checked against the file, line, commit or function it cites, in both
worktrees, and against the read-only production DB. A finding is **UPHELD** (folded into the ruling),
**PARTLY UPHELD** (the part that holds is folded, the rest said why not) or **REBUTTED** (evidence
given). Nothing was rebutted. Two findings hold only in part. The rest hold, and several of them
change a ruling materially — D1, D4 and D6 are rewritten; D2, D3 and D5 are corrected in place.

Each decision below gives the **adopted ruling** (verbatim in `DECISIONS_FOR_THE_NATIVE.md`) and the
reconciliation table. Line references are to the snapshots in the frontmatter. `N/` = this worktree's
`00_ARCHITECTURE/briefs/nirmana/`; `E/` = the engine worktree.

---

## D1 · Orchestrator behaviour edits for R34–R38

**Ruling (adopted 2026-09-27):**

> D1 is not a re-authorization. Engine-behaviour work the native authorized to the Nirmāṇa engine
> campaign (2026-09-26) is neither re-authorized nor re-implemented here. R34–R38 are re-owned by a
> requirement-level crosswalk, and every requirement is tracked at five stages — implementation ·
> merge · migration applied · deployed · runtime proof — none of which is satisfied today (production
> read 2026-09-26T20:03Z: 268/268 NULL rates, 288/419 silent failed runs, migrations 1094 and 1095
> absent).
>
> - **R34** = engine A1 (`8edba0533`, CLOSED_ON_BRANCH: the engine times every registered writer
>   itself; migration 1094) **plus** two open residuals: (i) the legacy `ga_writers/_telemetry.py`
>   path — its 8 `ga_*` call sites still write NULL — owned by the asset campaign per engine ruling
>   D-1(b) (`73385d72f`), recorded on R34; (ii) the applicable-path proof below.
> - **R35** = engine A2 (`f4a6f9541`, CLOSED_ON_BRANCH: every asset-terminating path now writes
>   `build_run_assets.error`) **plus** an open run-level residual, new row **R217**:
>   `build_runs.last_error` is still never written by `mark_run_state` (`runner.py:408–425`) on the
>   failed-assets path (:1450), the exception path (:1456) or the writer-gap path (:1240); only
>   `_terminalize_preflight_failure` (:327) and the TypeScript `terminalizeFailedRun` / watchdog CTEs
>   write it. R217 is engine-owned (`runner.py` is engine surface) and is exactly what the 288/419
>   population measures. A2b (`mark_asset_error` empty-exception) stays carried on the engine side.
> - **R36** = engine A3 (`551d5ecad`, CLOSED_ON_BRANCH: a registry divergence fails only the
>   diverged asset; Family A = 2 of the 8 runs) **plus** P2's acceptance (the harness replay of a
>   mid-run registry change, then the same replay against the deployed engine). Family B (6 runs
>   dispatched with no manifest at all) is engine A3b — a different defect, carried separately; the
>   pre-dispatch fault window (engine G-1/G-2) stays carried.
> - **R37** = engine C1, OPEN, not started. `guardian_cleanup` (310 records) and `manual reap` (77)
>   have zero source hits in this repository or in madhav-l3; C1 does not start by assuming the code
>   is here.
> - **R38** = engine B1 (`17e5a1257`, CLOSED_ON_BRANCH: the failure-counting surfaces are certified;
>   migration 1095's disposition backfill was simulated, not applied) **plus** the labelling surfaces
>   B1 expressly did not certify — `PlanTimeline`, `/api/cockpit/runs/[id]/assets`,
>   `ArmillaryGraph.stateColor` and the three unmapped-default sites — which stay with engine B2 and
>   R21.
>
> P1 and P2 are not withdrawn: they become integration-and-acceptance packets (merge → migration →
> deploy → runtime proof), and P1 additionally carries R217. P8 becomes "consume B1 and C1, and hold
> B2/R21's labelling work". No 27 h saving is claimed: P1+P2's 11 h of implementation is replaced by
> R217 (2 h) plus acceptance (≈ 4 h); P8's 16 h is unchanged except that R38's 4 h is covered for the
> counting surfaces only. Engine D-1(b) and D-2(a) are consumed as already ruled in `73385d72f`, not
> re-decided.
>
> The freeze precondition "instrument the builder before the from-scratch run" is met only when, on
> the deployed engine, representative applicable paths (one timed writer build per layer, a zero-row
> completion, a skip after a prior timing, a legacy `ga_*` writer) and representative failure paths (a
> failed asset, a run failed by exception, a mid-run registry change) each pass their named proof —
> not when one non-NULL rate makes 268/268 fall.
>
> Two governance rows are added. **R215**: a campaign checks `CURRENT_STATE` and the sibling
> worktrees for concurrent campaigns on the same surface at session open. **R216**:
> `platform/scripts/governance/asset_census.py` is changed by B1 (`17e5a1257`, +75 lines) and again
> by P4/P6; P4 rebases on B1's diff before any detector change lands, and B1's census tests stay
> green.

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | A2 fixes `build_run_assets.error`; `build_runs.last_error` is still never written on failure | **UPHELD** | `E/…/runner.py:408–425` builds `UPDATE build_runs SET state = %s[, ended_at = NOW()] WHERE id = %s` — no error column; callers :1240, :1450, :1456; only :327 (preflight CTE) writes `last_error`. `A2_before…json:27–41,68–83` counts 301 **asset** rows; `PHASE6_ANALYSIS.md:136` counts 288/419 **runs**; live read 288/419 |
| 2 | R34 partial (8 legacy call sites); "one instrumented build" too weak a freeze test | **UPHELD** | `E/…/ga_writers/_telemetry.py:64–95` docstring: "8 ga_writers/*.py callers … writes NULL"; the 8 importers: ga_dashas, ga_panchanga, ga_positions, ga_strength, ga_sade_sati, ga_sensitive, ga_tajaka, ga_structural; engine D-1 :139–168 lists six NULL sources |
| 3 | A3 fixes Family A only; keep P2 acceptance; A3b separate; G-1/G-2 carried | **UPHELD** | `E/…/engine/STATE.md:57–60` ("A3 as scoped fixes 2 of 8 runs"); `EVENTS.jsonl:41–42` (G-1 not charged, carried) |
| 4 | B1 certifies counting surfaces only; labelling surfaces to B2 | **UPHELD** | `B1_rereview2_20260926T193112Z.md:186–210` ("I do not certify the failure-LABELLING surfaces complete"), C-4 :257–261 |
| 5 | v1.0 stale: B1 "resumes from REJECT" vs its own table; D-1/D-2 already ruled; three not seven call sites; 11 h not 27 h | **UPHELD** | v1.0 :296–297 vs :49; `73385d72f` ("Take both delegated decisions"); `git grep terminalizeFailedRun` → `runs/route.ts:642,712`, `recalibrationEnqueue.ts:189`, watchdog inline CTEs :145/:441 — the "seven" was the A2 commit message's own cross-language path count, repeated by v1.0 unverified; plan :37/:45/:94 |

**What changed from v1.0:** closure by packet → closure by requirement with named residuals; P1/P2
withdrawn → acceptance packets; "one instrumented build" → representative paths and failure paths;
"~27 h removed" → no saving claimed; D-1/D-2 "recommend" → consumed as ruled; +R215, R216, R217.

---

## D2 · Reopen the sealed tiers

**Ruling (adopted 2026-09-27):**

> Three bundled reopens are authorized, one per sealed document, each on a **reviewed row-to-clause
> agenda** that names, for every row, the exact clause and — where the register offers alternative
> remedies — the remedy chosen. Listing a row id does not ratify its register text. The agenda:
>
> - **T1** (product definition): R01 (§2 P23/P24 order), R72 (`review_record` pointer), R76 (field
>   rename to `document_reviews` **and** one glossary line — T1 has no glossary section, so the
>   agenda names where the line lands, recommended §16).
> - **T2** (data plane): R06 (multi-producer clause — §7.1 or §13.3, chosen on the agenda), R73 and
>   R75 (frontmatter counts), R85 (D5 — new **§3.6**, because §3.2 already exists), R88 (§9.2
>   per-layer switch behaviour), R89 (§3.4 carried-by-layer column), R90 (§5 per-layer obligation
>   enumeration), R91 (per-layer entity classes), R119's T2 half (the [TRANSFERS] tag at §13.3 items 1
>   and 6 and on the §12.2/DP rows where a layer plan reads them), and the §7.1 text halves of
>   R181/R186/R198 (per-layer produced/consumed index with edge type and declared-use column).
>   R109's registry columns are P9 data work, not a reopen.
> - **T3** (layer template): R08 (§5.2's "§7" defined; §2.5/§2.7 order), R09 (§2.7 per-asset carriage
>   table), R10 (§1.1 multi-producer inventory, with R06), R65's T3 half (§5.2/changelog check count —
>   "align on nine" or "record the six-plus-three split", chosen on the agenda), R67, R68's T3 half
>   (:359/:520 spelling), R71 (D3's text at §5.4 test 4 **and** §2.2 `measured_by`; R94/R140/R185 close
>   with it), R74 (§5.1 ruling-11 clause), R93 (§3.2 evidence→disposition rule and preserved kernels),
>   R120 (§4.4 role row; R192/R208 close with it), R201 (§2.3 names the source of declared use).
> - **Explicitly deferred to a second reopen round**, after P9's derivability re-run makes their remedy
>   text known: R131 (§0.2 external comparison), R210 (default per-obligation detectors), R214 (§0.3
>   migration-pin location). They stay OPEN; no sealed row is silently outside this ruling.
> - **No reopen needed — proceed now:** R63, R64, R69, R70, R77, R65's tracker-comment half, R68's T4
>   half, R119's T4 §1.2 half.
>
> Rules. (1) The agenda is closed once opened: anything discovered mid-edit becomes a new register row
> for the next round. (2) Before each re-seal, a cross-tier re-render pass greps every count, gate name
> and section number the changed clauses touch — across tiers, instances and the tracker — and fixes
> the echoes in the same commit; this is the cause of C7, not one of its rows. (3) Drafting may start
> anywhere (R71's text first), but re-sealing is parent-before-child — **T1, then T2, then T3** —
> because T3's §0.1 and ownership rows cannot be certified derivable while T2's necessity (§3.6) and
> ownership inputs are unsealed. (4) One version bump per document, after its re-render pass and an
> independent review.

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | v1.0's agenda omits known sealed work: R01; R06, R88–R91; R10, R93, R120/R192, R119/R185 | **UPHELD** | register :96, :106, :115 ("same reopen as R08/R09"), :240–245, :276–277, :352, :359 — all OPEN, all clause-bound; v1.0 listed twelve ids |
| 2 | Assign by edit surface: R08 is §7/order repair, not carriage; R65 spans the tracker; R68 spans T4; R109 is registry metadata; R76 needs a glossary location | **UPHELD** | register :113–114, :172, :175, :183, :266; T1 has no glossary heading (`grep -i glossary` → none) |
| 3 | A closed agenda and "fix the echoes in the same commit" need compatible scope; T3 cannot re-seal before T2's inputs | **UPHELD** | T3 §0.1 :99–112 inherits T2 §2/§3; v1.0's T3→T2→T1 seal order reversed |

**What changed from v1.0:** agenda 12 → 32 named rows plus three explicit deferrals; seal order
reversed to parent-before-child; cross-surface rows split; alternative remedies chosen on the agenda.

---

## D3 · The [TRANSFERS] contradiction (R71)

**Ruling (adopted 2026-09-27):**

> The contradiction is real (T2 §1 :83–85 and §12.2 :614/:621 versus T3 §5.4 test 4 :628 and §2.2
> `measured_by` :278) and it hit **four** layers (R94 L1, R119 L2, R140 L3, R185 L4). It is resolved by
> separating what the data layer owns from what it does not:
>
> - **The data layer must prove retention and hand-off of its assigned presentation fields.** T2 §3.4
>   makes this a data obligation, and it stays binding: every §3.4 field the layer owns is present in
>   its produced contracts, by contract test. "Never a block" never excuses a missing field.
> - **End-to-end Presentation parity and Delivery sentinel remain owned by the receiving plane**
>   ([TRANSFERS], T2 §12.2). Where that owner or its test is not built, the instance records
>   `[TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>` — no pass, and no block
>   on the instance for the transferred part alone. This does not discharge product acceptance. Where
>   the owner can run the test, its result is linked, never inherited as the layer's own acceptance:
>   the existence of a built plane is not an ownership assignment.
>
> Replacement texts, both on the T3 reopen agenda (D2):
>
> T3 §5.4 test 4 → "4. **Presentation fields carried.** Every §3.4 field this layer owns (§2.2) is
> present in its produced contracts — a contract test, run here. End-to-end Presentation parity and
> Delivery sentinel are [TRANSFERS] (Data plane §12.2): where their owner or its test is not built,
> record `[TRANSFERS]-pending` with the obligation, owner and dependency — never a pass, never a block
> on this instance for the transferred part alone, never an invented verdict; where the owner runs it,
> link the result."
>
> T3 §2.2 `measured_by:` → "producer-field carriage test — each §3.4 field this layer owns is present in
> its produced contracts; the presentation-parity test itself (Data plane §12.2) is [TRANSFERS] and is
> linked when its owner runs it, never run as this layer's own acceptance".
>
> The same tag is applied at every inheritance point R119 names (T2 §13.3 items 1 and 6; T4 §1.2), so
> the class is fixed, not one row. R94, R119, R140 and R185 close with R71.

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | The contradiction is real and the line references are correct | **UPHELD** | direct reads of T2 :83–85, :614, :621 and T3 :628 |
| 2 | A built plane is not an ownership assignment; "never a block" must not excuse missing fields; keep the producer-field proof binding | **UPHELD** | T2 §3.4 :178–205 ("a data obligation … sets the acceptance test"); v1.0's "run only where the surface exists in a built plane" re-imports the test the moment a plane exists |
| 3 | §2.2 `measured_by` also demands the parity test; R119 names §13.3 and T4 §1.2; four layers, not three | **UPHELD** | T3 :278; register :246 (L1), :276 (L2), :302 (L3), :352 (L4) |

**What changed from v1.0:** the replacement is no longer test-4-only; the producer-field proof is made
binding; the pending record carries owner and dependency; §2.2, §13.3 and T4 §1.2 are named; four
layers.

---

## D4 · The ledger namespace (R78–R81)

**Ruling (adopted 2026-09-27):**

> **Obligation identity comes first; the id is derived from it.** A gap row is identified by
> `(asset, scope, criterion)`, where `criterion` is an entry in a **declarative criterion registry**
> the census reads (new — today criteria are strings built inline in `asset_census.py:484–560`). Each
> entry carries: gate, check, applicability rule, detector binding or `NONE`, and a revision. The gap
> id is derived — `<asset>-<Gate>.<check>`, the census's existing form, with a scope suffix where
> chart-scoped. Hand-written gap rows use a registered criterion; if the gap has none, the author
> registers one line first. A registered criterion with `detector: NONE` yields `NO_DETECTOR` rows on
> every run — the census's existing `Carr.detector` practice and tier 4's "a gap, never a pass" — which
> is the visible "detector wanted" state. A specific proof is a distinct criterion from its generic
> placeholder (`Carr.D1` ≠ `Carr.detector`; `Completeness.depth.dasha_link` ≠ `Complete.depth`;
> `Earn.service_state` ≠ `Earn.build_record`) and is never merged by family alias.
>
> **History is preserved by an append-only crosswalk, not a blind fold.** `superseded_by` is added to
> the `_schema` (R80). The 30 hand gap rows across the five pilots (ontology 10, rules 8, ephemeris 6,
> panchanga 4, sarvatobhadra 2) are migrated by a reviewed table (R81, re-scoped): each row is
> re-keyed to a registered criterion (its `change`/`owner`/`gate` text carried onto the new row; the
> old id gets `superseded_by`), split, or preserved with a newly registered criterion. T5's group 8 is
> a partial overlap: `bg_panchanga-G01` becomes its own criterion `Earn.service_state` and is never
> folded onto a timing id. The four family aliases (`Vocab.rule1.alias`→`Vocab.alias`,
> `Dens.density_contract`→`Dens.served`, `Carr.D1|D2|D3`→`Carr.detector`, `Completeness.*`→
> `Complete.*`) are crosswalk entries used once in the migration, not a runtime alias table — R79 is
> re-scoped, not withdrawn. Opportunity rows (`-O<n>`) and layer-scope rows (`_layer_all-BT<nn>`) keep
> their hand idioms.
>
> **The census appends measured transitions by deterministic lookup, under closure semantics proven
> before the port lands** (R57 amended): CLOSED only on `PASS` or an explicitly justified `N/A`, never
> on `NOT_GENERIC`, `UNKNOWN`, an errored check or an unmeasured criterion; an `IN_PROGRESS` row
> transitions on `PASS`; a closed row re-opens on regression; a superseded id is never resurrected;
> hand `change`/`owner`/`gate` are carried onto every transition row, never replaced by census
> defaults. The sandbox port (`harness/asset_census_closing.py:649–679`) is not adopted unchanged — it
> fails four of these today. The tracker resolves latest state per identity.
>
> **Scope.** The migration runs on the current ledger as a proof of the mechanism over preserved test
> history; the five pilot briefs are regenerated after freeze (register frontmatter) and are not
> re-keyed by hand — their `G` ids resolve through the crosswalk. Cost: P6's 17 h stands as the floor,
> plus the reviewed migration table (≈ 4 h) and R57's acceptance cases (≈ 4 h).

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | Under (a) the census still appends rows; no human-only closure or §N.8 violation follows | **UPHELD** | `T5_LEDGER_DRIFT.md:102–104`: `emit_gaps` "attach … or append a new hand-style row" — v1.0 misread "stops being a writer" |
| 2 | Criterion-derived ids do not abolish identity work; a crosswalk is needed; "no alias table, ever" not established | **UPHELD** | T5 :38–43, :59–64, :89–94 (`Carr.D1`/`Carr.D3` vs `Carr.detector`; `Completeness.depth.dasha_link` vs `Complete.depth`); census :500–504 |
| 3 | Group 8 is a partial three-way overlap; folding G01 onto a timing id would discharge the service probe | **UPHELD** | T5 :66–73 ("overlap in measurement surface, not in full substance"); v1.0's D6 marked service N/A — the fold would have closed it |
| 4 | 30 hand gap rows across the pilots need a content migration, not a G-counter swap | **UPHELD** | `asset_gaps.jsonl` parsed: 10 / 8 / 6 / 4 / 2 = 30 hand `kind=gap` rows |
| 5 | No declarative criterion list exists; T4 forbids registering a gap without a detector | **PARTLY** | inline `m["…"] = dict(...)` construction confirmed (:484–560) — upheld. But a `NO_DETECTOR` row for a declared, unbound criterion is the census's existing `Carr.detector` practice and T4 :220 ("a gap, never a pass"); the schema's "not registered" rule binds a hand row with no criterion at all, so a registry entry with `detector: NONE` is the honest form, not a forbidden one |
| 6 | The sandbox port closes on `NOT_GENERIC`, ignores `IN_PROGRESS` on PASS, and replaces hand metadata | **UPHELD** | harness :649–679: `failing = v in (FAIL, PARTIAL, NO_DET)` so any other verdict closes; closes only when prior `== "OPEN"`; the CLOSED row is written with `owner="asset_census"`, `change=""`, `gate="this asset's certification"` |

**What changed from v1.0:** the derived-id format survives; everything else is replaced — identity is
defined before the id, a criterion registry replaces "one line to a list that does not exist", the 30
rows are migrated by review, `Earn.service_state` is preserved, R79 is re-scoped rather than
withdrawn, R57's port gains acceptance cases, and the cost is raised honestly.

---

## D5 · The P/V → layer necessity mapping (R85)

**Ruling (adopted 2026-09-27):**

> **The native owns the necessity judgement; the session prepares it; nothing is adopted by silence.**
> The session drafts a candidate necessity matrix as new **T2 §3.6 "Necessity — P/V × layer"** (§3.2
> already exists and is cited widely; nothing is renumbered): P01–P24 and V01–V13 against L0–L5. Each
> affirmative cell names the precise customer distinction lost if the layer is removed, its supporting
> clauses (T1 §2, T2 §2's V-table, §3.1's owned question, the DP contracts), and whether it is a
> **proposed judgement** or **established evidence**; undetermined or disputed cells are marked as
> such, never left blank. T2 §3.1 is cited as support only — a responsibility map is not a necessity
> proof.
>
> The native **affirmatively adopts a named revision** of the matrix, after correcting it, inside the
> T2 reopen (D2); absence of objection is not adoption, and unchanged cells are adopted only by the
> same signature. Tier-3 §0.1's semantics — necessary, not "involved in", not "contributes to" —
> stand unchanged; they are what makes §0.1 falsifiable. Joint dependencies (a need answerable only by
> two layers together) are recorded separately, each with its own counterfactual, as seam
> contributions under §3.5's four seams — there are no automatic adjacent-pair rows; §3.5 defines
> seams, not pairs, and v1.0's examples (L1/L3, L3/L5) were non-adjacent candidates, not derivations.
> Adopted parent mappings are then inherited by the layer instances, which narrow and never invent.
> R85's 12 h stands as documentation mechanics; the native's effort is the review pass over 24 + 13
> rows the campaign priced, not blank-page authorship.

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | §3.1 is a responsibility map, not a necessity proof; "ratifies by exception" is honest only with affirmative adoption | **UPHELD** | T2 :135–144 (columns: owns / hands onward / must not claim); T3 :99–112 ("definitional … cannot be answered without") |
| 2 | v1.0 misstates the original's effort (12 h = documentation mechanics; native does a focused review) | **UPHELD** | `DECISIONS_FOR_THE_NATIVE.md:89–99` |
| 3 | Adjacent-pair rows do not follow from §3.5; both examples are non-adjacent | **UPHELD** | T2 :207–240 — four seams; the ablation harness "holds every asset in place" |
| 4 | P09/P12 sets are candidates; a new §3.2 would collide | **UPHELD** | T1 :164 (P09: prerequisites, formation, exceptions, bhaṅga, expression, routes, window), :167 (P12); T2 :146 "### 3.2 Five edge types" |

**What changed from v1.0:** §3.2 → §3.6; ratify-by-exception → affirmative adoption of a named
revision; adjacent-pair rows dropped for separately-recorded joint dependencies; §3.1 demoted to
support; the effort framing corrected.

---

## D6 · The Earn/Cost verdict scale (R55)

**Ruling (adopted 2026-09-27):**

> **R55 stays OPEN as a detector-design row; the two measurements are separated, not collapsed, and
> neither certifies the whole Earn gate.** `Cost` is not one of the nine gates — `Cost.baseline`
> measures tier 4 §1's build-cost baseline; `Earn.build_record` is one Earn measurement among the
> asset's status/grade claims and never discharges `Earn.service_state` or any other earned-signal
> obligation.
>
> The census (in P4, after R216's rebase on B1's census diff, together with R44/R45/R49):
>
> 1. **Feature-detects the instrument.** `asset_throughput.duration_seconds` absent (migration 1094
>    not applied — true in production today) → both measurements read `NO_DETECTOR — instrument
>    absent (migration 1094)`, scoped to the run; a failed query → `NO_DETECTOR — instrument
>    unreachable`. Neither is `PARTIAL`: nothing was partly measured.
> 2. **Attributes timing to an attempt.** Measurement identity is `(asset, chart scope, latest
>    build_run_assets attempt)`. A duration counts for a build only if its completion write is that
>    attempt's; `last_built_at` alone proves nothing, because skip (`asset_runner.py:985`), probe-green
>    (:1053), error (:587) and start (:1555) all refresh it without touching duration. The census stops
>    taking an unordered last row per asset (:318–323).
> 3. **Grades `Earn.build_record` by cause**, for the latest attempt: a completion write (`lit`,
>    `dormant` or `incomplete`, per migration 1094) with a finite duration → `PASS` — a zero-row
>    completion has a duration and a rate of 0.0, a measured value, never suppressed; healthy
>    non-execution (`skip_no_delta`, probe-green) or a legacy health-probe service with no registered
>    writer → `N/A` with the reason; a completion write reached with no duration → `FAIL` (the legacy
>    `_telemetry` path — R34's residual); an attempt that failed, was orphan-reaped or watchdog-aborted
>    before any completion write → `N/A — failed before completion; see Build.history` (the build
>    failure is Build.history's finding, not a timing defect); a NULL of unknown cause →
>    `NO_DETECTOR — unclassified NULL`, never `PASS`.
> 4. **Grades `Cost.baseline` against a sanctioned baseline.** The baseline is the most recent
>    *measured* completion for the asset at that scope, with provenance (attempt id, age); a healthy
>    skip neither erases a prior baseline nor creates one. With the instrument present and no
>    measured completion on record → `FAIL — no sanctioned baseline build`; the from-scratch run
>    establishes one for every asset.
> 5. **Is tested before adoption** against the engine implementation (`asset_runner.py` at
>    `8edba0533`+, migration 1094): failure, zero rows, skip after a prior timing, probe-green, the
>    legacy `ga_*` path, the absent column, an unknown NULL. It lands when those tests pass — not
>    "before merge" by decree — so the first instrumented build is graded by a tested classifier
>    whenever that build happens.

| # | review finding | verdict | evidence checked |
|---|---|---|---|
| 1 | v1.0's table is not a complete NULL classifier; "writer ran, no rate ⇒ FAIL" misgrades a failed build as a telemetry defect | **UPHELD** | migration 1094 :38–41 (failed / orphan-reaped / watchdog-aborted builds "never reach the completion-write site … NULL by omission"); engine D-1 :139–168 |
| 2 | A zero-row completion has a measured rate 0.0; "definable only when rows_written > 0" is wrong | **UPHELD** | `_compute_duration_and_rate` :708–738: only the duration side guards; `rate = (rows_written or 0) / duration`; 1094 :51–53 |
| 3 | `duration_seconds + last_built_at` cannot prove this build was measured; the census discards chart identity | **UPHELD** | asset_runner :587, :985–987, :1053, :1555/:1563 refresh `last_built_at` and leave duration untouched; census :318–323 keys a dict by `asset_id` with no chart and no order (R44) |
| 4 | Service/skip exceptions are per measurement, not per gate; Earn applies always; Cost is not a gate | **UPHELD** | T4 :226 (Earn "always"), :222–232 (nine gates, no Cost), :140–143 (build-cost baseline under §1); engine D-1 :150–157 (`bg_*` health-probe, no registered writer) |
| 5 | PARTIAL is wrong for an absent instrument; NO_DETECTOR is reasonable only if the absence is detected and scoped; the classifier is unspecified and "before merge" is not a day-one proof | **PARTLY** | `NO_DETECTOR`-today survives — upheld with the feature-detection now specified; "lands before merge = correct on day one" does not survive — it lands when its tests pass |

**What changed from v1.0:** blanket N/A for every non-defect NULL → graded per attempt with failed
builds routed to Build.history; the `rows_written > 0` gate dropped; Earn re-keyed to
`duration + last_built_at` dropped for attempt-linked provenance; instrument feature-detection added;
the cost baseline defined as a sanctioned measured completion; "before merge" dropped.

---

## §3 · The review's fact table — all 27 verdicts confirmed

Every row was re-checked. The eleven **WRONG** verdicts that bear on v1.0 all hold: engine STATE/decisions
are v0.6/v2.0 (not v0.5/v1.3); 198 commits ahead (not 196); three `terminalizeFailedRun` call sites
(not seven); P1+P2 = 11 h (not 27); R08 is §7/order repair (not carriage); four layers hit R71 (not
three); eleven overlap *groups* with group 8 partial (not eleven equivalent pairs); the original priced
12 h of documentation mechanics (not blank-page authorship); T2 §3.2 exists; §3.5 defines four seams,
not pairs; rate is defined at zero rows; D-1/D-2 were ruled and B1 was committed before v1.0's
"mechanical work" section was written. The sixteen **VERIFIED** rows also reproduce, including the live
268/268 and 288/419 figures re-read this session.

## §4 · The seven "missed" items — all upheld, each with a home

| # | item | disposition |
|---|---|---|
| 1 | Two error contracts; the run-level omission must be assigned | → **R217** (engine-owned); P1's proof tests prospective failure paths, not only successful builds |
| 2 | The closure port needs its own acceptance cases before a namespace ruling can close R57/R58 | → D4 ruling, closure-semantics paragraph; R57 amended |
| 3 | A missing historical cost baseline ≠ a healthy present skip; timing at `lit`/`dormant`/`incomplete` is not proof of success | → D6 ruling items 3–4 |
| 4 | `asset_census.py` is a real cross-campaign integration dependency (B1 changed it) | → **R216**; P4 rebases first. `git show --stat 17e5a1257` confirms +75 lines in the census |
| 5 | Historical populations drift; pin every figure to timestamp, table, denominator | every figure in this document carries its source; the live re-read is timestamped by DB `now()` |
| 6 | Branch-state evidence with limits | updated here: no PR for the engine branch (`gh` confirms), Nikaṣa PR #2736 OPEN, engine worktree now carries uncommitted B2 work; deployed revision not verified — the DB read stands in for it |
| 7 | Test artefacts are slated for regeneration | → D4 scope paragraph: migration proof over preserved test history; pilots regenerated, not hand re-keyed |

## §5 · Summary

| D | v1.0 said | final ruling | changed? |
|---|---|---|---|
| D1 | already done elsewhere; withdraw P1/P2; ~27 h saved | requirement-level crosswalk with residuals (R217, legacy path, A3b, B2); P1/P2 = acceptance; no saving claimed; representative-path freeze test | **rewritten** |
| D2 | three reopens, 12 ids, T3→T2→T1 | three reopens, 32 named rows + 3 explicit deferrals, remedies chosen on the agenda, seal T1→T2→T3 | corrected |
| D3 | reword test 4, apply as a class | producer-field proof binding; parity/sentinel [TRANSFERS]-pending with owner + dependency; §5.4, §2.2, §13.3, T4 §1.2; four layers | corrected |
| D4 | census ids as namespace; no alias table; census stays the writer | identity `(asset, scope, registered criterion)` → derived id; reviewed 30-row crosswalk; `Earn.service_state` preserved; closure semantics proven first; R79 re-scoped | **rewritten** |
| D5 | session drafts, native ratifies by exception; new §3.2; pair rows | session drafts §3.6; native affirmatively adopts a named revision; no pair rows; §0.1 semantics stand | corrected |
| D6 | NULL by cause; NO_DETECTOR today; Earn re-keyed to duration+timestamp; before merge | attempt-linked provenance; instrument feature-detection; failed builds → Build.history; zero-row rate kept; sanctioned baseline; tested before adoption | **rewritten** |

## §6 · Mechanical consequences applied this session

- **Register** (`NIKASHA_CHANGE_REGISTER_v2_0.md`): R34, R36 → `CLOSED_ON_BRANCH`; R35, R37, R38
  re-owned with residuals; R217, R215, R216 added (§2.9); R55, R57, R78–R81 re-specified; R71 remedy
  fixed with R94/R119/R140/R185; R85 re-pointed to §3.6; every sealed-tier row annotated with its D2
  reopen or explicit deferral; state vocabulary gains `CLOSED_ON_BRANCH`; counts re-totalled (217).
- **Plan** (`NIKASHA_IMPLEMENTATION_PLAN_v1_0.md`): P1/P2 → acceptance packets (+R217); P4 +R216 and
  the D6 spec; P5 dependencies ruled; P6 rewritten per D4; P7 +R215; P8 → consume B1/C1, hold B2/R21;
  P9's D3/D5 pointers → ruled; coverage check and total (≈ 373 h) updated.
- **Decisions file**: status `RULED 2026-09-27`; each ruling appended verbatim. **v1.0**: SUPERSEDED.
- **Not done here, by design:** the reopens themselves (D2 authorizes; execution is separate work); any
  edit in the engine worktree (read-only) — R217's engine ownership and the R216 dependency must be
  relayed to the engine campaign's STATE by whoever next opens it.

## §7 · Where the native should look personally

1. **R217's owner.** Ruled engine-owned because `runner.py` is engine surface — but the engine campaign
   did not raise it and its STATE was not editable from here. If the native prefers the asset campaign
   or Nikaṣa P1 to carry the two-line fix, only the owner cell changes.
2. **D4's criterion registry** is a new artefact (location chosen by P6). It is the one piece of this
   ruling that adds machinery rather than removing it; the alternative — hand rows with free-text
   criteria — is what produced the 11 overlap groups.
3. **D5's signature** is the only thing that seals §3.6. The session can draft; it cannot adopt.
4. **D6 item 4** grades "instrument present, no measured completion ever" as `FAIL — no sanctioned
   baseline build`. The gap is real and one sanctioned build closes it for every asset; if the native
   would rather see a distinct verdict for "never yet measured", that is a one-word change.
5. **D2's agenda choices** (R06: §7.1 vs §13.3; R65: align on nine vs record the split; R76's glossary
   location) are agenda items, deliberately not decided here.
