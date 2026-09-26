---
artifact: NIKASHA_CHANGE_REGISTER
canonical_id: NIKASHA_CHANGE_REGISTER
version: "1.0"
status: LIVING
produced_on: 2026-09-26
decision_owner: Native
system_name: "Nikaṣa (निकष) — the touchstone: the stone gold is rubbed against to test whether it is what it claims to be. Chosen because the system's one rule is that a claim carries a detector that could return false."
role: >
  The register of every change the Nikaṣa system needs before it is frozen and run from scratch,
  L0 through L5. Native instruction 2026-09-26: test the system first, register what must change,
  fix it, freeze it, then run it for real — inspecting and fixing layer by layer as we go.
what_nikasha_is: >
  The product definition (tier 1) · the data plane value architecture (tier 2) · the layer
  definition-and-strategy template (tier 3) · the asset elevation template (tier 4) · the inspector
  (asset_census.py) · the delta ledger (asset_gaps.jsonl) · the certification ledger
  (asset_certs.jsonl) · the tracker (asset_elevation_tracker.py) · the governance detectors that
  feed them (drift_detector, manifest_fingerprint, check_migration_ledger_vs_production) · and the
  decision sheets that record the native's rulings over all of it.
what_is_a_test_artefact: >
  The L0 instance v3.0, the five pilot briefs, and today's ledger rows are the TEST RUN of Nikaṣa,
  not its production output. When the system is frozen they are regenerated from it, not kept.
---

# Nikaṣa — change register

**The system is tested before it is trusted.** One run over one layer found defects in the system at
every level — a detector in a sealed document that failed on correct data, a template row no instance
could fill, an inspector with four bugs of its own, a ledger that could not tell a gap from an
improvement. That is the signal to test the method before applying it five more times, not to apply
it and fix the same things five times over.

## 1 · How Nikaṣa is tested — five tests, in plain terms

| test | the question | how it is run | state today |
|---|---|---|---|
| **T1 · Finds what is there** | when a defect exists, does the inspector report it? | plant a known defect in a copy of the data (a duplicate key, an empty alias set, an unregistered writer) and confirm the census fails the right check | **partly proven** — every census failure so far was independently confirmed by hand; no *planted* defect has been run yet |
| **T2 · Does not invent what isn't** | when an asset is fine, does the inspector say so? | run the census against known-good assets and confirm zero false failures | **proven by failure, then fixed** — four false positives found and removed today (docstring regex, framework file, line-split registry, padding bug). Needs a clean re-run to confirm none remain |
| **T3 · A fix closes a row** | after a repair, does the ledger row close by measurement, and the tracker move? | fix one small gap, re-run the census, confirm the row flips to CLOSED and `0/360` becomes `1/360` | **NEVER RUN.** The single most important untested path. Nothing has been closed yet. |
| **T4 · Works on a layer it wasn't built against** | is the system generic or secretly L0-shaped? | run the census on L1 and read what breaks | **never run** — census is written layer-generic; unexercised |
| **T5 · The pieces agree** | do the four documents, tracker, ledger and inspector say the same counts, names and vocabularies? | drift detector + a consistency pass over gate names, counts, criteria strings | **partly proven** — drift detector clean on fingerprints; gate names aligned today (`Carr`, nine gates); criteria strings between hand rows and census rows not yet reconciled |

**Freeze criterion:** all five tests pass, and every register item below is closed or explicitly deferred
with a reason. Then Nikaṣa is sealed (a fifth seal beside the four) and the real run begins at L0.

## 2 · The register

State ∈ `OPEN` · `DONE` · `DEFERRED (reason)`. Each row names the artefact, the change, the test or event
that surfaced it, and the state.

### 2.1 · Tier 1 — product definition

| # | change | surfaced by | state |
|---|---|---|---|
| R01 | P24 printed before P23 in the §2 needs table | data plane review | OPEN — cosmetic, native's call |
| R02 | Domain correctness row names where it is discharged (above the plane) | decision 11 | DONE |

### 2.2 · Tier 2 — data plane

| # | change | surfaced by | state |
|---|---|---|---|
| R03 | §4.1 rule 1 detector tests the authority's *declared* key, not `canonical_id` alone | pilot 1 → decision 16 (reopen) | DONE |
| R04 | §1 plane boundary: retrieval and conversation planes not built; obligations marked [TRANSFERS] | review fold | DONE |
| R05 | §3.5 synergy term, §12.2 synergy row, §13.3 item 1b | review fold | DONE |
| R06 | Multi-producer shared tables (one table, several writers, e.g. `brahma_ontology` with four) have no expression anywhere in the contract vocabulary | pilot 1, C-10 | **OPEN** — needs a clause in §7.1 or §13.3: a shared table declares its producers and each producer's `count_sql` is scoped to its own rows |

### 2.3 · Tier 3 — layer template

| # | change | surfaced by | state |
|---|---|---|---|
| R07 | Ninth gate `Build`, 9 × 129 scope, gate map row | decision 17 (reopen) | DONE |
| R08 | §5.2 cites a "§7" the template never defines; §2.5 is ordered after §2.7 | L0 instance C-7 | **OPEN** — reopen needed: define the corrections section, fix the order |
| R09 | §2.7 assigns the carriage check (a/b/c) at layer scope only; no instance can fill the per-asset row 13 | pilots 1–4, C-9 (confirmed four times) | **OPEN** — reopen: §2.7 gains a per-asset assignment table, or the template states the brief author chooses and records why |
| R10 | §1.1 inventory cannot express a shared table with several producers | pilot 1, C-10 | **OPEN** — same reopen as R08/R09 |
| R11 | "Seven always + two conditional" wording and the inherits line say nine | decision 17 | DONE |

### 2.4 · Tier 4 — asset template

| # | change | surfaced by | state |
|---|---|---|---|
| R12 | `Dom` → `Carr`; thirteen inherited rows; pilot clause; §9 opportunity register; §1.1/§1.2 censuses | rulings 9/11, native review | DONE |
| R13 | `Build` gate §4.2: scenario-aware, nine checks, boundary rule, blocking radius | decision 17 + native context | DONE |
| R14 | §1's storage bullets assume a table; a service fills them with N/As — say so explicitly | pilot 4 | **OPEN** |
| R15 | A rule for hand-written vs machine-written rows: everything measurable belongs to the inspector; a hand-written row (opportunity, disposition, judgement) carries the census run id it was judged against | native's staleness hypothesis, tested below (§3) | **OPEN** |
| R16 | Row 13 chooser rule (pending R09's resolution in the layer template) | C-9 | OPEN |

### 2.5 · The inspector — `asset_census.py`

| # | change | surfaced by | state |
|---|---|---|---|
| R17 | Registry read via `json_agg`, not line-oriented | first run (52 assets from 40) | DONE |
| R18 | Code scans on the AST, framework file excluded, both-entry-points is a note | first run (false positives) | DONE |
| R19 | Build history checks 7–9 from `build_runs` / `build_run_assets` | native's build context | DONE |
| R20 | **Follow writer delegation into the seeder** so `Idem.pattern` resolves PASS/FAIL instead of PARTIAL for 27 assets | first run | **OPEN** — highest-value inspector fix |
| R21 | Blocking radius per asset from the DAG, attached to every `Build` gap as severity | triage | **OPEN** |
| R22 | Width universes: read a declared universe from the registry or the layer instance where one exists, instead of always `NOT_GENERIC` | pilots | **OPEN** — needs a place to *declare* universes first (R06-adjacent) |
| R23 | Field-level reachability census over capability modules (fields selected vs columns built) | pilots 1–3 | **OPEN** |
| R24 | Exercised on L1–L5 (T4) | — | **OPEN** |
| R25 | A `--plant` mode for T1: inject a known defect into a scratch copy and assert detection | — | **DONE** (nikasha_test/harness/plant.py, 17 plants; T1_RESULTS.md) |
| R26 | Emits `kind: opportunity` rows? No — opportunities are judgement, never machine-emitted. Recorded so nobody adds it | — | DONE (by rule) |
| R40 | `Vocab.identity`'s `count(DISTINCT (chart_id,event_class,segment_index))` does not scale to the estate's largest table (kala_field, 10.3M rows) and exceeds the hardcoded 180s psql timeout (line 95), making the L3 and `--layer all` census unrunnable on production. Ground truth measured by hand: duplicates = 0 in 47s. Fix: sample-aware or indexed duplicate count, and a configurable timeout | nikasha-test P2 T2 sweep | OPEN |
| R41 | No per-check fault isolation: one check raising (timeout, missing relation) aborts the ENTIRE layer census instead of degrading that check's verdict to UNKNOWN for that asset. The census must catch per-check exceptions and record them as measured-but-errored | nikasha-test P2 T2 sweep (L3 + all killed) | OPEN |
| R42 | `Build.completion` emits `N/A "no count_sql"` although `count_sql` is non-null layer-wide, and on multi-table assets it compares the registry `count_sql` result against itself (mi_kula: count_sql 15 vs live 11 scored PASS) | nikasha-test P2 handverify L1/L2/L4/L5 | OPEN |
| R43 | `Build.registered` misses writers that register via `@register(ASSET_ID)` constant indirection (mi_bhara, mi_sankalpa) and writers living in package directories (ph_rectification) — layer registered-id counts read wrong (L4 8 vs 9; L5 12 vs 14). Fix per §7: resolve module-level constants, walk package `__init__.py` | nikasha-test P2 handverify L4/L5 | OPEN |
| R44 | `Earn.build_record` / `Cost.baseline` quote non-latest `asset_throughput` rows — must select the latest row per asset (`DISTINCT ON (asset_id) … ORDER BY ended_at DESC`) | nikasha-test P2 handverify L1/L2/L4/L5 | OPEN |
| R45 | `Build.dep_liveness` reports "all lit" while ignoring dependencies whose last run is stale-only (L2) — stale deps must surface as PARTIAL, not PASS | nikasha-test P2 handverify L2 | OPEN |
| R46 | View assets are scored against stub `count_sql` (`SELECT 0`): bo_samvada reads live_rows 0 while the view actually returns 15 rows — count_sql for a view must count the view, not a constant | nikasha-test P2 handverify L2 | OPEN |
| R47 | Census JSON output path is hardcoded to `00_ARCHITECTURE/control/asset_census.json`: a census run against the sandbox silently overwrites the production census artifact. Output path must be a flag, or include the target DB identity in the document | nikasha-test P1 fidelity (sandbox run overwrote the prod file; restored from git) | OPEN |
| R48 | `Count.floor` is entirely absent from the L3 census although 20/23 L3 assets declare `target_floor` in the registry — the check has a coverage gap (layer-dependent emission), not just wrong verdicts | nikasha-test P2 handverify L3 | OPEN |
| R49 | `Build.history`'s "most recent run error" text quotes a non-latest error (ka_avadhi, ka_kshetra) — same latest-row bug class as R44, in `build_run_assets` reads | nikasha-test P2 handverify L3 | OPEN |
| R50 | `Build.exercised` run count off by one (L1 ga_dashas: census 108, actual 107 from `build_run_assets ⋈ build_runs`) | nikasha-test P2 handverify L1 | OPEN |
| R51 | `Dens.served`'s measured module list mis-attributes serving modules (L4: query_predictive_anchors.ts wrongly included for ph_pramana/ph_sodhana; index.ts for ph_rectification/ph_suddha_sodhana) — verdicts unaffected, evidence wrong | nikasha-test P2 handverify L4 | OPEN |
| R52 | `Build.completion` inverted: emptying a table whose build record agrees with the emptiness flips the check FAIL→**PASS** (planted TRUNCATE of bg_muhurta_lattice read "live=0 and rows_written=0 — consistent"). It is a rows_written↔live consistency test, not a non-emptiness test — destroying data makes the asset look healthy | nikasha-test P2 T1 plant build_completion_truncate | OPEN |
| R53 | `Build.target`'s FAIL branch is dead code: `asset_registry.asset_kind` is NOT NULL with CHECK(data\|service\|artifact), so the only expressible target-table loss degrades PASS→N/A, never FAIL | nikasha-test P2 T1 plant build_target_null | OPEN |
| R54 | `Vocab.alias` verdict saturates: no synonyms-bearing asset is PASS anywhere, so emptying all 662 alias sets moved the measured value 79/741→741/741 empty while the verdict stayed FAIL→FAIL — severity is invisible at verdict level | nikasha-test P2 T1 plant vocab_alias | OPEN |
| R55 | `Earn.build_record` ≡ `Cost.baseline` are one detector (both read `asset_throughput.rows_per_second`), and constant-FAIL wherever rows_per_second is unset (the entire sandbox) — they provide no independent signal and only the sensitivity direction is plantable | nikasha-test P2 T1 plant earn_cost_signal | OPEN |
| R56 | `Count.floor`/`Build.completion` silently absent (no verdict emitted) on assets whose `count_sql` is parameterized or multi-table — 57 assets on L1/L2/L4/L5. The differential reimplementation finds real breaches the inspector never reports (ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510) | nikasha-test P2 T1 differential | OPEN |
| R57 | **The closure loop is impossible in the stock tooling** (the campaign's headline finding): (a) `emit_gaps` only appends OPEN rows and skips any existing id — no CLOSED path; (b) the tracker reads gap state per row, so even an appended CLOSED row would not close the earlier OPEN one; (c) both hardcode `00_ARCHITECTURE/control/` (same class as R47). **Fixed during campaign** in scratch copies `harness/asset_census_closing.py` + `harness/tracker_sandbox.py`: append-only CLOSED/RE-OPENED rows keyed by deterministic gap_id, last-wins-per-gap_id in the tracker, `NIKASHA_CONTROL_DIR` redirection. Production adoption = port those three changes (~70 lines total) | nikasha-test P3 T3 | OPEN (fix proven in sandbox; not yet ported to the real tools) |
| R58 | Hand-written gap rows (bg_ontology-G01…G10, _layer_all-BT03, …) carry no deterministic `<asset>-<criterion>` id and no runnable detector binding, so no measurement can ever close them — they are permanent OPEN rows unless manually edited, which breaks the append-only ledger | nikasha-test P3 T3 | OPEN |
| R59 | `Ashtanga Hridayam` is cited by 27/27 bg_nakshatra_medical rows but is not admitted in `brahma_ontology` entity_class='text' (15 members) — found by the first real D1 detector (harness/sandbox_control/detectors/bg_nakshatra_medical_D1.py), which FAILED before the fix, proving it can fail | nikasha-test P3 T3 | OPEN (fixed in sandbox; production fix = admit the text row) |
| R60 | `Ldgr.source_presence`'s citation-column list (`source_citation`, `source_text_id`, `classical_citations`, `citation_ref`) misses the singular `classical_citation` — bg_nakshatra_medical gets no Ldgr check at all despite a fully-populated citation column | nikasha-test P3 T3 | OPEN |
| R61 | Registry repairs cascade: fixing `has_writer=false`→true for bg_nakshatra_medical immediately opened a NEW measured gap (`Build.exercised` — writer never dispatched). Closure tooling must expect cascades; the T3 loop handled it by actually running the writer in the sandbox | nikasha-test P3 T3 | OPEN (behaviour correct; recorded as a loop-design fact) |
| R62 | A census run against a sampled sandbox emits prod-scale `Count.floor` rows (bg_cohort, bg_ephemeris, bg_muhurta_lattice appended by the T3 run) — floors are declared for production scale; emit-gaps needs target-awareness (or floors a scope) so sandbox runs don't pollute the ledger | nikasha-test P3 T3 | OPEN |

### 2.5a · T5 consistency findings (Phase 5 — nikasha_test/consistency/T5_VOCABULARY.md, T5_LEDGER_DRIFT.md)

| # | change | surfaced by | state |
|---|---|---|---|
| R63 | T4 §4 says "the eight gates" in 4 places (lines 13, 210, 213, 498) while its own table lists nine (Build added by ruling 17) — replace with "the nine gates" | nikasha-test P5 T5 | OPEN |
| R64 | T4 §4.2 heading "the six checks" → "the nine checks" (the body already counts nine) | nikasha-test P5 T5 | OPEN |
| R65 | Build check-count disagreement: T3 §5.2/changelog and the tracker GATES comment say "six static checks"; T4 §4.2 lists nine. Align on nine, or explicitly record "T3 names the six static checks; T4 adds three run-record checks" | nikasha-test P5 T5 | OPEN |
| R66 | asset_elevation_tracker.py:43 comment "Eight, not thirty-three" → "Nine, not thirty-three" | nikasha-test P5 T5 | OPEN |
| R67 | T3 §5.4 test 5: "§5.2's eight-row map" → "§5.2's nine-row map" (the map has nine rows) | nikasha-test P5 T5 | OPEN |
| R68 | Verdict spelling drift: T3 :359 and :520 use `NO DETECTOR` (space); T4 :278 uses bare `NA` — normalize to the closed set `NO_DETECTOR` / `N/A` that ledgers, tracker, census already use | nikasha-test P5 T5 | OPEN |
| R69 | L0 v3.0 self-contradiction: "0/320 gates" at lines 146, 522, 613, 730 vs 360 at line 612 — replace the four stale figures with 0/360 | nikasha-test P5 T5 | OPEN |
| R70 | L0 v3.0 §1.1/§9 status figures no longer reproduce (doc: 40 NO_BRIEF / 30 gap rows; measured 2026-09-26: 40 GAPS_REGISTERED / 243 gap + 19 opportunity rows) — restate or date-stamp as pre-census-emission | nikasha-test P5 T5 | OPEN |
| R71 | **[TRANSFERS] contradiction**: T2 §1 (:83-85, "a layer plan does not inherit it as its own work") + §12.2 (:614, Presentation parity [TRANSFERS]) vs T3 §5.4 test 4 (:628, "Presentation parity holds for the layer's served surface") — reword T3 test 4 to carry parity as a named [TRANSFERS] row, or un-mark it in T2 | nikasha-test P5 T5 | OPEN |
| R72 | T1 frontmatter `review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md` — the file does not exist anywhere; "11 MAJOR + 14 MINOR, all folded" unverifiable. Locate/restore or correct the pointer | nikasha-test P5 T5 | OPEN |
| R73 | T2 frontmatter document_reviews misstates the v3.0 review as "2 BLOCKER + 10 MAJOR + 11 MINOR"; the file measures 2+9+10 = 21 findings (matches the FINAL review's own line 8). Correct the counts | nikasha-test P5 T5 | OPEN |
| R74 | "Ten obligations": T3 §5.1 lists ten with no reason for omitting Domain correctness; T1 §14 has 11 rows; only T2 §13.3 carries the reconciliation. Add the ruling-11 clause to T3 §5.1 | nikasha-test P5 T5 | OPEN |
| R75 | T2 changelog item (f) says "§13.3 is nine elements"; §13.3 says and has "Ten elements" (1, 1a, 1b, 2–8). Fix the changelog or annotate 1b's later addition | nikasha-test P5 T5 | OPEN |
| R76 | "Review record" names four different artefact patterns across tiers (`review_record` T1 / `source_review_record` + `document_reviews` + `review_backing` T2 / `*_VALIDATION_AND_REVIEW_RECORD` layer instances). Rename T1's field to `document_reviews` and add one glossary line fixing the four names | nikasha-test P5 T5 | OPEN |
| R77 | All five L0 pilot briefs carry eight gates, no Build row (`## §4 · The eight gates`, 8 rows each) while tracker REQUIRED_GATES demands nine — on pilot refresh, add the Build row per pilot and recompute N/A counts ("six of nine" for BG_PANCHANGA :20) | nikasha-test P5 T5 | OPEN |
| R78 | Same check, two criterion strings: hand rows `bg_ontology-G02`/`bg_ephemeris-G03` vs census rows `bg_ontology-Earn.build_record`/`bg_ephemeris-Earn.build_record` — one criterion-string authority (census string + merged hand `measured:` clause), withdraw the duplicate ids | nikasha-test P5 T5 | OPEN |
| R79 | Census emit_gaps dedupe is by id only — add a substance key (asset, criterion-family) with alias resolution (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`, `Carr.D1\|D2\|D3`≡`Carr.detector`, `Completeness.*`≡`Complete.*`); skip or attach when a hand row covers the substance | nikasha-test P5 T5 (R28 scope) | OPEN |
| R80 | asset_gaps.jsonl `_schema`: add `superseded_by` so folding a duplicate sets it on the thinner row while the ledger stays append-only | nikasha-test P5 T5 (R28 scope) | OPEN |
| R81 | Ledger cleanup: 11 hand↔census overlap pairs measured in T5_LEDGER_DRIFT.md §A (bg_ontology G02/G07/G10/G05, bg_ephemeris G03/G05/G02, bg_panchanga G01(partial)/G02, bg_rules G03/G06) — fold each census row's `measured:` reading into the hand row's `what`, mark the census row `superseded_by` the hand id | nikasha-test P5 T5 (R28 scope) | OPEN |
| R82 | CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: rotate fingerprint_sha256 to 244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f and update last_verified_*; also fix the L0 manifest note's stale "REVISED_PENDING_REVIEW" prose | nikasha-test P5 T5 (drift_detector HIGH, confirmed) | OPEN |
| R83 | drift_detector schema_db_unreachable LOWs (psql auth failure on 127.0.0.1:5433): run the schema checks against a reachable DB or mark them NOT_MEASURED — an unreachable instrument must not masquerade as a passing or a noise finding | nikasha-test P5 T5 | OPEN |
| R84 | T5 NOT_MEASURED set (needs production registry/run tables at analysis time): 129 total assets L1–L5; 776 build runs; 5-of-40 never run; 13 errored/aborted; 21 skip_no_delta; catalog_status split (bg_vidhi_floors DRAFT claim) | nikasha-test P5 T5 | OPEN (measure in P6 §6.7) |

### 2.6 · The ledgers and the tracker

| # | change | surfaced by | state |
|---|---|---|---|
| R27 | `asset_gaps.jsonl` gains `kind`; states reused; tracker filters on kind | native decision | DONE |
| R28 | Reconcile the ~6 hand-written rows that overlap census rows in substance (e.g. `bg_ontology-G02` vs `bg_ontology-Earn.build_record`) into one namespace | census emission | **OPEN** |
| R29 | Hand-written rows carry `census_run_id` (see R15) | R15 | **OPEN** |
| R30 | Tracker reads the census JSON for measured values, not only the ledgers, so "measured" and "registered" cannot disagree | — | **OPEN** |
| R31 | Tracker's `SHAPE` markers and the asset template §2 list must be the same list, generated from one source | — | **OPEN** |
| R32 | `asset_certs.jsonl` `verified_by` per ruling 9 | ruling 9 | DONE |
| R33 | **T3 has never run**: no row has ever been closed by a passing detector, so the closure path (census → CLOSED → cert record → tracker increments) is unproven | — | **CLOSED** (nikasha-test P3: loop proven end-to-end in sandbox — bg_nakshatra_medical GAPS_REGISTERED→ELEVATED→(regression)→ELEVATED; required the R57 tooling fix; harness/T3_CLOSURE_LOOP.md) |

### 2.7 · The build system — orchestrator, sequenced with the layers

The orchestrator's **contract** is frozen and stays frozen: 129 writers plug into it, and elevating the
engine never changes the shape of the socket. What can change is the engine's own behaviour — how it
records, how it recovers, how it schedules. Timing, per the native's framing that the elevated builder
must work seamlessly once the assets are elevated:

| # | change | class | when | state |
|---|---|---|---|---|
| R34 | Record `rows_per_second` and duration in `asset_throughput` — the 80 L0 rows, and the same in every layer | **instrumentation** | **before the from-scratch run** — the run rebuilds every asset through the builder; without a rate there is no cost baseline to judge any improvement against. Native: "the first one is absolutely correct" | OPEN — native-authorized, orchestrator change |
| R35 | Record error text on every failure — the 307 silent failures (13% of the record, 82 assets) | **instrumentation** | **before the from-scratch run** — a rebuild that fails silently cannot be diagnosed | OPEN |
| R36 | A registry change mid-run must not abort every asset in the run (18 assets, 8 runs; a 10-asset L0 run aborted in full on 09-04) | **behaviour** | **before the from-scratch run** — it would abort our own elevation runs | OPEN |
| R37 | Crash / orphan / guardian-reap stability (543 records, 24%) | **behaviour / infra** | **in parallel with layer elevation**, not gating it — but every `Build.history` verdict is read against this noise until it falls | OPEN |
| R38 | Cascade: a blocked asset is not a failed asset; report cascades as one root with N blocked, not N failures | **reporting** | with R21 | OPEN |
| R39 | The builder's own elevation plan, driven by the `Build` gate's nine checks, frozen **after** the asset contract is frozen | **plan** | last | OPEN |

**The sequencing rule in one line:** instrument the builder first (R34, R35), remove the run-killer (R36),
then elevate the layers while the builder's behaviour is fixed alongside (R37, R38), and freeze the
builder's plan last (R39) — because "seamless" is defined by the assets' contract, and that has to stop
moving before the engine is tuned to it.

## 3 · The native's staleness hypothesis, tested

**Hypothesis:** the ledger does not go stale, because the inspector runs, writes the ledger, and the
work proceeds immediately, with no other process changing the data in between; today's drift happened
only because the system itself was being built.

**Result: correct for everything the inspector measures, with one qualification.**

- Every measured row is *regenerated* on each run — deterministic ids, idempotent emission — so it is
  never remembered, only re-read. A measured row cannot go stale; it can only be re-measured.
- The one-operator, sequential discipline holds: nothing writes production between a run and the action
  on it. Today's drift (fingerprints, registry rows) was the system being built, as the native said.
- **The qualification:** hand-written rows — opportunities, dispositions, judgements — are written once
  and are not regenerated. Those *can* drift from the measurements they were judged against. The fix is
  R15/R29: a hand-written row carries the census run id it was judged against, so a later run can flag
  "judged against an older measurement." With that, the hypothesis holds in full.
- My earlier "an inspection list nobody acts on goes stale" was really about *authoring effort* — writing
  35 detailed briefs about assets whose shared defects we were about to fix. With the inspector doing the
  measuring, that cost is small, and the concern dissolves.

## 4 · The two decisions, recorded

- **Instrumentation of the builder (R34): native said yes.** Orchestrator change, native-authorized,
  sequenced before the from-scratch run.
- **Build-system stability (R37): timed, not deferred.** Runs in parallel with layer elevation, never
  gating it, and read as noise on `Build.history` until it falls. The builder's *plan* freezes last (R39).
