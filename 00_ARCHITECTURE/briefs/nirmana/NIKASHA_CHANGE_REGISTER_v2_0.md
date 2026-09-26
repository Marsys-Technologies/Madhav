---
artifact: NIKASHA_CHANGE_REGISTER
canonical_id: NIKASHA_CHANGE_REGISTER
version: "2.0"
status: LIVING
supersedes: NIKASHA_CHANGE_REGISTER_v1_0.md
produced_on: 2026-09-26
decision_owner: Native
system_name: "Nikaṣa (निकष) — the touchstone: the stone gold is rubbed against to test whether it is what it claims to be. Chosen because the system's one rule is that a claim carries a detector that could return false."
role: >
  The register of every change the Nikaṣa system needs before it is frozen and run from scratch,
  L0 through L5. v2.0 carries every v1.0 row forward unchanged (except the recorded R84 measurement
  update) and adds the 130 invention rows surfaced by the Phase-4 derivability pass (fresh-reader
  derivation of layer instances and asset briefs from tiers 1–4 + census only), each with severity,
  dependency and effort columns new in this version.
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

# Nikaṣa — change register v2.0

**The system is tested before it is trusted.** v2.0 folds in Phase 4's derivability test: a reader
with only the four tiers and the census was asked to derive each layer's instance skeleton and two
asset briefs per layer. Every place the reader had to invent content the documents did not provide
is a register row here (R85–R214), quoted against the clause that failed to provide it.

## 0 · Index

**Total rows: 214** (R01–R84 carried from v1.0; R85–R214 added in v2.0 from P4 derivations).

### 0.1 · Count by state

| state | count |
|---|---|
| OPEN | 197 |
| DONE | 15 |
| CLOSED | 1 |
| MEASURED in P6 | 1 |

### 0.2 · Count by severity

| severity | count | meaning |
|---|---|---|
| BLOCKS_FREEZE | 12 | freeze criterion cannot be met while open (closure loop, gate integrity, silent coverage, contradictions) |
| BLOCKS_LAYER | 107 | a layer instance/brief cannot be derived from the tiers without inventing content |
| DEGRADES | 83 | system runs but evidence/verdicts are wrong, incomplete, or misleading |
| COSMETIC | 12 | wording, ordering, stale figures; no measurement impact |

### 0.3 · Where the rows live

| section | rows | surface |
|---|---|---|
| 2.1 | R01–R02 | tier 1 — product definition |
| 2.2 | R03–R06 | tier 2 — data plane |
| 2.3 | R07–R11 | tier 3 — layer template |
| 2.4 | R12–R16 | tier 4 — asset template |
| 2.5 | R17–R26, R40–R62 | inspector — asset_census.py |
| 2.5a | R63–R84 | T5 consistency findings |
| 2.6 | R27–R33 | ledgers and tracker |
| 2.7 | R34–R39 | build system |
| 2.8 | R85–R214 | P4 derivability inventions, by layer (L1 R85–R99 · L2 R100–R129 · L3 R130–R178 · L4 R179–R196 · L5 R197–R214) |

## 1 · How Nikaṣa is tested — five tests, in plain terms

| test | the question | how it is run | state today |
|---|---|---|---|
| **T1 · Finds what is there** | when a defect exists, does the inspector report it? | plant a known defect in a copy of the data and confirm the census fails the right check | **proven** — 17 plants, detected (nikasha_test/harness/T1_RESULTS.md); differential found real breaches the inspector misses (R56) |
| **T2 · Does not invent what isn't** | when an asset is fine, does the inspector say so? | run the census against known-good assets and confirm zero false failures | **proven after fixes** — four false positives removed; sweep handverify clean except inspector-side defects now registered (R40–R51) |
| **T3 · A fix closes a row** | after a repair, does the ledger row close by measurement, and the tracker move? | fix one small gap, re-run the census, confirm the row flips CLOSED and the tracker moves | **proven in sandbox** (nikasha_test/harness/T3_CLOSURE_LOOP.md); production tooling port = R57 (OPEN) |
| **T4 · Works on a layer it wasn't built against** | is the system generic or secretly L0-shaped? | run the census on L1–L5 and read what breaks | **run** — census executed on L1–L5; defects registered (R40–R51 etc.); R24 tracks the exercise |
| **T5 · The pieces agree** | do the four documents, tracker, ledger and inspector say the same counts, names and vocabularies? | drift detector + consistency pass over gate names, counts, criteria strings | **run** — 22 findings registered (R63–R84); R84 measured in P6 |

**Freeze criterion:** all five tests pass in production tooling, and every register item below is
closed or explicitly deferred with a reason. Then Nikaṣa is sealed and the real run begins at L0.

## 2 · The register

State ∈ `OPEN` · `DONE` · `CLOSED` · `MEASURED in P6` · `DEFERRED (reason)`.
Severity ∈ `BLOCKS_FREEZE` · `BLOCKS_LAYER` · `DEGRADES` · `COSMETIC`. Effort in hours, honestly
calibrated against the evidence files (small text fixes 0.5–2h; inspector detector changes 2–8h;
tooling ports ~4h; doc-structural mappings 8–24h). Rows that share one fix carry the full effort on
the primary row and `depends_on` the primary with transcription-only effort on the rest.

### 2.1 · Tier 1 — product definition

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R01 | P24 printed before P23 in the §2 needs table | data plane review | COSMETIC | — | 0.5 | OPEN — cosmetic, native's call |
| R02 | Domain correctness row names where it is discharged (above the plane) | decision 11 | DEGRADES | — | 1 | DONE |

### 2.2 · Tier 2 — data plane

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R03 | §4.1 rule 1 detector tests the authority's *declared* key, not `canonical_id` alone | pilot 1 → decision 16 (reopen) | BLOCKS_LAYER | — | 2 | DONE |
| R04 | §1 plane boundary: retrieval and conversation planes not built; obligations marked [TRANSFERS] | review fold | DEGRADES | — | 2 | DONE |
| R05 | §3.5 synergy term, §12.2 synergy row, §13.3 item 1b | review fold | DEGRADES | — | 1 | DONE |
| R06 | Multi-producer shared tables (one table, several writers, e.g. `brahma_ontology` with four) have no expression anywhere in the contract vocabulary | pilot 1, C-10 | BLOCKS_LAYER | — | 8 | **OPEN** — needs a clause in §7.1 or §13.3: a shared table declares its producers and each producer's `count_sql` is scoped to its own rows. CONFIRMED L1/L2/L3/L5 in P4 (R95, R103, R136, R205); refuted for L4 |

### 2.3 · Tier 3 — layer template

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R07 | Ninth gate `Build`, 9 × 129 scope, gate map row | decision 17 (reopen) | BLOCKS_LAYER | — | 2 | DONE |
| R08 | §5.2 cites a "§7" the template never defines; §2.5 is ordered after §2.7 | L0 instance C-7 | DEGRADES | — | 2 | **OPEN** — reopen needed: define the corrections section, fix the order |
| R09 | §2.7 assigns the carriage check (a/b/c) at layer scope only; no instance can fill the per-asset row 13 | pilots 1–4, C-9 (confirmed four times) | BLOCKS_LAYER | R08 | 6 | **OPEN** — reopen: §2.7 gains a per-asset assignment table, or the template states the brief author chooses and records why. CONFIRMED on L1–L5 in P4 (R92, R112, R144, R190, R204) |
| R10 | §1.1 inventory cannot express a shared table with several producers | pilot 1, C-10 | BLOCKS_LAYER | R06 | 4 | **OPEN** — same reopen as R08/R09 |
| R11 | "Seven always + two conditional" wording and the inherits line say nine | decision 17 | COSMETIC | — | 0.5 | DONE |

### 2.4 · Tier 4 — asset template

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R12 | `Dom` → `Carr`; thirteen inherited rows; pilot clause; §9 opportunity register; §1.1/§1.2 censuses | rulings 9/11, native review | DEGRADES | — | 2 | DONE |
| R13 | `Build` gate §4.2: scenario-aware, nine checks, boundary rule, blocking radius | decision 17 + native context | BLOCKS_LAYER | R07 | 4 | DONE |
| R14 | §1's storage bullets assume a table; a service fills them with N/As — say so explicitly | pilot 4 | DEGRADES | — | 1 | **OPEN** — extended by P4: service-shaped rows needed across §0/§1/§3/§4/§6 (R97, R125, R165–R167, R171, R173, R175–R177, R196, R211, R212) |
| R15 | A rule for hand-written vs machine-written rows: everything measurable belongs to the inspector; a hand-written row (opportunity, disposition, judgement) carries the census run id it was judged against | native's staleness hypothesis, tested below (§3) | DEGRADES | R29 | 3 | **OPEN** |
| R16 | Row 13 chooser rule (pending R09's resolution in the layer template) | C-9 | BLOCKS_LAYER | R09 | 2 | OPEN |

### 2.5 · The inspector — `asset_census.py`

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R17 | Registry read via `json_agg`, not line-oriented | first run (52 assets from 40) | DEGRADES | — | 2 | DONE |
| R18 | Code scans on the AST, framework file excluded, both-entry-points is a note | first run (false positives) | DEGRADES | — | 3 | DONE |
| R19 | Build history checks 7–9 from `build_runs` / `build_run_assets` | native's build context | DEGRADES | — | 3 | DONE |
| R20 | **Follow writer delegation into the seeder** so `Idem.pattern` resolves PASS/FAIL instead of PARTIAL for 27 assets | first run | BLOCKS_LAYER | — | 6 | **OPEN** — highest-value inspector fix; confirmed load-bearing on L2 (R127) |
| R21 | Blocking radius per asset from the DAG, attached to every `Build` gap as severity | triage | DEGRADES | — | 4 | **OPEN** |
| R22 | Width universes: read a declared universe from the registry or the layer instance where one exists, instead of always `NOT_GENERIC` | pilots | BLOCKS_LAYER | R06 | 6 | **OPEN** — needs a place to *declare* universes first (R06-adjacent); confirmed layer-wide on L1–L3 in P4 (R90, R110, R123) |
| R23 | Field-level reachability census over capability modules (fields selected vs columns built) | pilots 1–3 | DEGRADES | — | 8 | **OPEN** |
| R24 | Exercised on L1–L5 (T4) | — | BLOCKS_FREEZE | — | 4 | **OPEN** — census executed L1–L5 during campaign; remaining: production L3 census (R134) and clean re-runs after fixes |
| R25 | A `--plant` mode for T1: inject a known defect into a scratch copy and assert detection | — | DEGRADES | — | 4 | **DONE** (nikasha_test/harness/plant.py, 17 plants; T1_RESULTS.md) |
| R26 | Emits `kind: opportunity` rows? No — opportunities are judgement, never machine-emitted. Recorded so nobody adds it | — | COSMETIC | — | 0 | DONE (by rule) |
| R40 | `Vocab.identity`'s `count(DISTINCT (chart_id,event_class,segment_index))` does not scale to the estate's largest table (kala_field, 10.3M rows) and exceeds the hardcoded 180s psql timeout (line 95), making the L3 and `--layer all` census unrunnable on production. Ground truth measured by hand: duplicates = 0 in 47s. Fix: sample-aware or indexed duplicate count, and a configurable timeout | nikasha-test P2 T2 sweep | BLOCKS_LAYER | — | 4 | OPEN |
| R41 | No per-check fault isolation: one check raising (timeout, missing relation) aborts the ENTIRE layer census instead of degrading that check's verdict to UNKNOWN for that asset. The census must catch per-check exceptions and record them as measured-but-errored | nikasha-test P2 T2 sweep (L3 + all killed) | BLOCKS_FREEZE | — | 6 | OPEN |
| R42 | `Build.completion` emits `N/A "no count_sql"` although `count_sql` is non-null layer-wide, and on multi-table assets it compares the registry `count_sql` result against itself (mi_kula: count_sql 15 vs live 11 scored PASS) | nikasha-test P2 handverify L1/L2/L4/L5 | BLOCKS_FREEZE | R41 | 4 | OPEN |
| R43 | `Build.registered` misses writers that register via `@register(ASSET_ID)` constant indirection (mi_bhara, mi_sankalpa) and writers living in package directories (ph_rectification) — layer registered-id counts read wrong (L4 8 vs 9; L5 12 vs 14). Fix per §7: resolve module-level constants, walk package `__init__.py` | nikasha-test P2 handverify L4/L5 | BLOCKS_LAYER | R41 | 4 | OPEN |
| R44 | `Earn.build_record` / `Cost.baseline` quote non-latest `asset_throughput` rows — must select the latest row per asset (`DISTINCT ON (asset_id) … ORDER BY ended_at DESC`) | nikasha-test P2 handverify L1/L2/L4/L5 | DEGRADES | — | 2 | OPEN |
| R45 | `Build.dep_liveness` reports "all lit" while ignoring dependencies whose last run is stale-only (L2) — stale deps must surface as PARTIAL, not PASS | nikasha-test P2 handverify L2 | DEGRADES | R44 | 2 | OPEN |
| R46 | View assets are scored against stub `count_sql` (`SELECT 0`): bo_samvada reads live_rows 0 while the view actually returns 15 rows — count_sql for a view must count the view, not a constant | nikasha-test P2 handverify L2 | DEGRADES | — | 2 | OPEN |
| R47 | Census JSON output path is hardcoded to `00_ARCHITECTURE/control/asset_census.json`: a census run against the sandbox silently overwrites the production census artifact. Output path must be a flag, or include the target DB identity in the document | nikasha-test P1 fidelity (sandbox run overwrote the prod file; restored from git) | BLOCKS_LAYER | — | 2 | OPEN |
| R48 | `Count.floor` is entirely absent from the L3 census although 20/23 L3 assets declare `target_floor` in the registry — the check has a coverage gap (layer-dependent emission), not just wrong verdicts | nikasha-test P2 handverify L3 | BLOCKS_LAYER | R41 | 3 | OPEN |
| R49 | `Build.history`'s "most recent run error" text quotes a non-latest error (ka_avadhi, ka_kshetra) — same latest-row bug class as R44, in `build_run_assets` reads | nikasha-test P2 handverify L3 | DEGRADES | R44 | 1 | OPEN |
| R50 | `Build.exercised` run count off by one (L1 ga_dashas: census 108, actual 107 from `build_run_assets ⋈ build_runs`) | nikasha-test P2 handverify L1 | COSMETIC | — | 1 | OPEN |
| R51 | `Dens.served`'s measured module list mis-attributes serving modules (L4: query_predictive_anchors.ts wrongly included for ph_pramana/ph_sodhana; index.ts for ph_rectification/ph_suddha_sodhana) — verdicts unaffected, evidence wrong | nikasha-test P2 handverify L4 | COSMETIC | — | 2 | OPEN |
| R52 | `Build.completion` inverted: emptying a table whose build record agrees with the emptiness flips the check FAIL→**PASS** (planted TRUNCATE of bg_muhurta_lattice read "live=0 and rows_written=0 — consistent"). It is a rows_written↔live consistency test, not a non-emptiness test — destroying data makes the asset look healthy | nikasha-test P2 T1 plant build_completion_truncate | BLOCKS_FREEZE | R42 | 3 | OPEN |
| R53 | `Build.target`'s FAIL branch is dead code: `asset_registry.asset_kind` is NOT NULL with CHECK(data\|service\|artifact), so the only expressible target-table loss degrades PASS→N/A, never FAIL | nikasha-test P2 T1 plant build_target_null | DEGRADES | — | 2 | OPEN |
| R54 | `Vocab.alias` verdict saturates: no synonyms-bearing asset is PASS anywhere, so emptying all 662 alias sets moved the measured value 79/741→741/741 empty while the verdict stayed FAIL→FAIL — severity is invisible at verdict level | nikasha-test P2 T1 plant vocab_alias | DEGRADES | — | 2 | OPEN |
| R55 | `Earn.build_record` ≡ `Cost.baseline` are one detector (both read `asset_throughput.rows_per_second`), and constant-FAIL wherever rows_per_second is unset (the entire sandbox) — they provide no independent signal and only the sensitivity direction is plantable | nikasha-test P2 T1 plant earn_cost_signal | DEGRADES | R34 | 2 | OPEN |
| R56 | `Count.floor`/`Build.completion` silently absent (no verdict emitted) on assets whose `count_sql` is parameterized or multi-table — 57 assets on L1/L2/L4/L5. The differential reimplementation finds real breaches the inspector never reports (ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510) | nikasha-test P2 T1 differential | BLOCKS_FREEZE | R41 | 6 | OPEN |
| R57 | **The closure loop is impossible in the stock tooling** (the campaign's headline finding): (a) `emit_gaps` only appends OPEN rows and skips any existing id — no CLOSED path; (b) the tracker reads gap state per row, so even an appended CLOSED row would not close the earlier OPEN one; (c) both hardcode `00_ARCHITECTURE/control/` (same class as R47). **Fixed during campaign** in scratch copies `harness/asset_census_closing.py` + `harness/tracker_sandbox.py`: append-only CLOSED/RE-OPENED rows keyed by deterministic gap_id, last-wins-per-gap_id in the tracker, `NIKASHA_CONTROL_DIR` redirection. Production adoption = port those three changes (~70 lines total) | nikasha-test P3 T3 | BLOCKS_FREEZE | — | 4 | OPEN (fix proven in sandbox; not yet ported to the real tools) |
| R58 | Hand-written gap rows (bg_ontology-G01…G10, _layer_all-BT03, …) carry no deterministic `<asset>-<criterion>` id and no runnable detector binding, so no measurement can ever close them — they are permanent OPEN rows unless manually edited, which breaks the append-only ledger | nikasha-test P3 T3 | BLOCKS_FREEZE | R57 | 8 | OPEN |
| R59 | `Ashtanga Hridayam` is cited by 27/27 bg_nakshatra_medical rows but is not admitted in `brahma_ontology` entity_class='text' (15 members) — found by the first real D1 detector (harness/sandbox_control/detectors/bg_nakshatra_medical_D1.py), which FAILED before the fix, proving it can fail | nikasha-test P3 T3 | BLOCKS_LAYER | — | 1 | OPEN (fixed in sandbox; production fix = admit the text row) |
| R60 | `Ldgr.source_presence`'s citation-column list (`source_citation`, `source_text_id`, `classical_citations`, `citation_ref`) misses the singular `classical_citation` — bg_nakshatra_medical gets no Ldgr check at all despite a fully-populated citation column | nikasha-test P3 T3 | DEGRADES | — | 1 | OPEN |
| R61 | Registry repairs cascade: fixing `has_writer=false`→true for bg_nakshatra_medical immediately opened a NEW measured gap (`Build.exercised` — writer never dispatched). Closure tooling must expect cascades; the T3 loop handled it by actually running the writer in the sandbox | nikasha-test P3 T3 | COSMETIC | — | 0.5 | OPEN (behaviour correct; recorded as a loop-design fact) |
| R62 | A census run against a sampled sandbox emits prod-scale `Count.floor` rows (bg_cohort, bg_ephemeris, bg_muhurta_lattice appended by the T3 run) — floors are declared for production scale; emit-gaps needs target-awareness (or floors a scope) so sandbox runs don't pollute the ledger | nikasha-test P3 T3 | DEGRADES | R57 | 2 | OPEN |

### 2.5a · T5 consistency findings (Phase 5 — nikasha_test/consistency/T5_VOCABULARY.md, T5_LEDGER_DRIFT.md)

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R63 | T4 §4 says "the eight gates" in 4 places (lines 13, 210, 213, 498) while its own table lists nine (Build added by ruling 17) — replace with "the nine gates" | nikasha-test P5 T5 | BLOCKS_LAYER | — | 0.5 | OPEN |
| R64 | T4 §4.2 heading "the six checks" → "the nine checks" (the body already counts nine) | nikasha-test P5 T5 | BLOCKS_LAYER | — | 0.5 | OPEN |
| R65 | Build check-count disagreement: T3 §5.2/changelog and the tracker GATES comment say "six static checks"; T4 §4.2 lists nine. Align on nine, or explicitly record "T3 names the six static checks; T4 adds three run-record checks" | nikasha-test P5 T5 | BLOCKS_LAYER | R64 | 1 | OPEN |
| R66 | asset_elevation_tracker.py:43 comment "Eight, not thirty-three" → "Nine, not thirty-three" | nikasha-test P5 T5 | BLOCKS_LAYER | R63 | 0.5 | OPEN |
| R67 | T3 §5.4 test 5: "§5.2's eight-row map" → "§5.2's nine-row map" (the map has nine rows) | nikasha-test P5 T5 | BLOCKS_LAYER | R65 | 0.5 | OPEN |
| R68 | Verdict spelling drift: T3 :359 and :520 use `NO DETECTOR` (space); T4 :278 uses bare `NA` — normalize to the closed set `NO_DETECTOR` / `N/A` that ledgers, tracker, census already use | nikasha-test P5 T5 | DEGRADES | — | 1 | OPEN |
| R69 | L0 v3.0 self-contradiction: "0/320 gates" at lines 146, 522, 613, 730 vs 360 at line 612 — replace the four stale figures with 0/360 | nikasha-test P5 T5 | DEGRADES | — | 0.5 | OPEN |
| R70 | L0 v3.0 §1.1/§9 status figures no longer reproduce (doc: 40 NO_BRIEF / 30 gap rows; measured 2026-09-26: 40 GAPS_REGISTERED / 243 gap + 19 opportunity rows) — restate or date-stamp as pre-census-emission | nikasha-test P5 T5 | DEGRADES | — | 1 | OPEN |
| R71 | **[TRANSFERS] contradiction**: T2 §1 (:83-85, "a layer plan does not inherit it as its own work") + §12.2 (:614, Presentation parity [TRANSFERS]) vs T3 §5.4 test 4 (:628, "Presentation parity holds for the layer's served surface") — reword T3 test 4 to carry parity as a named [TRANSFERS] row, or un-mark it in T2 | nikasha-test P5 T5 | BLOCKS_FREEZE | — | 2 | OPEN — P4 confirmed three layers hit this (R94, R119, R140, R185) |
| R72 | T1 frontmatter `review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md` — the file does not exist anywhere; "11 MAJOR + 14 MINOR, all folded" unverifiable. Locate/restore or correct the pointer | nikasha-test P5 T5 | DEGRADES | — | 2 | OPEN |
| R73 | T2 frontmatter document_reviews misstates the v3.0 review as "2 BLOCKER + 10 MAJOR + 11 MINOR"; the file measures 2+9+10 = 21 findings (matches the FINAL review's own line 8). Correct the counts | nikasha-test P5 T5 | COSMETIC | — | 0.5 | OPEN |
| R74 | "Ten obligations": T3 §5.1 lists ten with no reason for omitting Domain correctness; T1 §14 has 11 rows; only T2 §13.3 carries the reconciliation. Add the ruling-11 clause to T3 §5.1 | nikasha-test P5 T5 | DEGRADES | — | 1 | OPEN |
| R75 | T2 changelog item (f) says "§13.3 is nine elements"; §13.3 says and has "Ten elements" (1, 1a, 1b, 2–8). Fix the changelog or annotate 1b's later addition | nikasha-test P5 T5 | COSMETIC | — | 0.5 | OPEN |
| R76 | "Review record" names four different artefact patterns across tiers (`review_record` T1 / `source_review_record` + `document_reviews` + `review_backing` T2 / `*_VALIDATION_AND_REVIEW_RECORD` layer instances). Rename T1's field to `document_reviews` and add one glossary line fixing the four names | nikasha-test P5 T5 | DEGRADES | — | 2 | OPEN |
| R77 | All five L0 pilot briefs carry eight gates, no Build row (`## §4 · The eight gates`, 8 rows each) while tracker REQUIRED_GATES demands nine — on pilot refresh, add the Build row per pilot and recompute N/A counts ("six of nine" for BG_PANCHANGA :20) | nikasha-test P5 T5 | BLOCKS_LAYER | — | 3 | OPEN |
| R78 | Same check, two criterion strings: hand rows `bg_ontology-G02`/`bg_ephemeris-G03` vs census rows `bg_ontology-Earn.build_record`/`bg_ephemeris-Earn.build_record` — one criterion-string authority (census string + merged hand `measured:` clause), withdraw the duplicate ids | nikasha-test P5 T5 | DEGRADES | R79 | 2 | OPEN |
| R79 | Census emit_gaps dedupe is by id only — add a substance key (asset, criterion-family) with alias resolution (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`, `Carr.D1\|D2\|D3`≡`Carr.detector`, `Completeness.*`≡`Complete.*`); skip or attach when a hand row covers the substance | nikasha-test P5 T5 (R28 scope) | DEGRADES | R80 | 4 | OPEN |
| R80 | asset_gaps.jsonl `_schema`: add `superseded_by` so folding a duplicate sets it on the thinner row while the ledger stays append-only | nikasha-test P5 T5 (R28 scope) | DEGRADES | R57 | 2 | OPEN |
| R81 | Ledger cleanup: 11 hand↔census overlap pairs measured in T5_LEDGER_DRIFT.md §A (bg_ontology G02/G07/G10/G05, bg_ephemeris G03/G05/G02, bg_panchanga G01(partial)/G02, bg_rules G03/G06) — fold each census row's `measured:` reading into the hand row's `what`, mark the census row `superseded_by` the hand id | nikasha-test P5 T5 (R28 scope) | DEGRADES | R78, R80 | 4 | OPEN |
| R82 | CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: rotate fingerprint_sha256 to 244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f and update last_verified_*; also fix the L0 manifest note's stale "REVISED_PENDING_REVIEW" prose | nikasha-test P5 T5 (drift_detector HIGH, confirmed) | DEGRADES | — | 0.5 | OPEN |
| R83 | drift_detector schema_db_unreachable LOWs (psql auth failure on 127.0.0.1:5433): run the schema checks against a reachable DB or mark them NOT_MEASURED — an unreachable instrument must not masquerade as a passing or a noise finding | nikasha-test P5 T5 | DEGRADES | — | 1 | OPEN |
| R84 | T5 NOT_MEASURED set (needs production registry/run tables at analysis time): 129 total assets L1–L5; 776 build runs; 5-of-40 never run; 13 errored/aborted; 21 skip_no_delta; catalog_status split (bg_vidhi_floors DRAFT claim) | nikasha-test P5 T5 | BLOCKS_LAYER | — | 2 | MEASURED in P6 — 129 assets confirmed; build_runs 762 (doc 776 — drift); 5/40 L0 never run, 13/40 errored-or-aborted confirmed; skip_no_delta 17 assets/61 rows (doc 21 — drift); bg_vidhi_floors sole DRAFT confirmed; asset_throughput.rows_per_second NULL 268/268; 288/419 failed runs carry no error text |

### 2.6 · The ledgers and the tracker

| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R27 | `asset_gaps.jsonl` gains `kind`; states reused; tracker filters on kind | native decision | DEGRADES | — | 2 | DONE |
| R28 | Reconcile the ~6 hand-written rows that overlap census rows in substance (e.g. `bg_ontology-G02` vs `bg_ontology-Earn.build_record`) into one namespace | census emission | DEGRADES | R79, R80 | 4 | **OPEN** — scope measured in T5 (R78–R81) |
| R29 | Hand-written rows carry `census_run_id` (see R15) | R15 | DEGRADES | R15 | 2 | **OPEN** |
| R30 | Tracker reads the census JSON for measured values, not only the ledgers, so "measured" and "registered" cannot disagree | — | BLOCKS_LAYER | R57 | 4 | **OPEN** |
| R31 | Tracker's `SHAPE` markers and the asset template §2 list must be the same list, generated from one source | — | DEGRADES | — | 2 | **OPEN** |
| R32 | `asset_certs.jsonl` `verified_by` per ruling 9 | ruling 9 | COSMETIC | — | 0.5 | DONE |
| R33 | **T3 has never run**: no row has ever been closed by a passing detector, so the closure path (census → CLOSED → cert record → tracker increments) is unproven | — | BLOCKS_FREEZE | R57 | 0 | **CLOSED** (nikasha-test P3: loop proven end-to-end in sandbox — bg_nakshatra_medical GAPS_REGISTERED→ELEVATED→(regression)→ELEVATED; required the R57 tooling fix; harness/T3_CLOSURE_LOOP.md) |

### 2.7 · The build system — orchestrator, sequenced with the layers

The orchestrator's **contract** is frozen and stays frozen: 129 writers plug into it, and elevating the
engine never changes the shape of the socket. What can change is the engine's own behaviour — how it
records, how it recovers, how it schedules. Timing, per the native's framing that the elevated builder
must work seamlessly once the assets are elevated:

| # | change | class | when | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|---|
| R34 | Record `rows_per_second` and duration in `asset_throughput` — the 80 L0 rows, and the same in every layer | **instrumentation** | **before the from-scratch run** — the run rebuilds every asset through the builder; without a rate there is no cost baseline to judge any improvement against. Native: "the first one is absolutely correct" | BLOCKS_FREEZE | — | 4 | OPEN — native-authorized, orchestrator change. P6 confirms urgency: rows_per_second NULL 268/268 (R84) |
| R35 | Record error text on every failure — the 307 silent failures (13% of the record, 82 assets) | **instrumentation** | **before the from-scratch run** — a rebuild that fails silently cannot be diagnosed | BLOCKS_LAYER | — | 3 | OPEN — P6 measurement: 288/419 failed runs carry no error text (R84) |
| R36 | A registry change mid-run must not abort every asset in the run (18 assets, 8 runs; a 10-asset L0 run aborted in full on 09-04) | **behaviour** | **before the from-scratch run** — it would abort our own elevation runs | BLOCKS_FREEZE | — | 4 | OPEN |
| R37 | Crash / orphan / guardian-reap stability (543 records, 24%) | **behaviour / infra** | **in parallel with layer elevation**, not gating it — but every `Build.history` verdict is read against this noise until it falls | DEGRADES | — | 12 | OPEN |
| R38 | Cascade: a blocked asset is not a failed asset; report cascades as one root with N blocked, not N failures | **reporting** | with R21 | DEGRADES | R21 | 4 | OPEN |
| R39 | The builder's own elevation plan, driven by the `Build` gate's nine checks, frozen **after** the asset contract is frozen | **plan** | last | BLOCKS_FREEZE | R13 | 8 | OPEN |

**The sequencing rule in one line:** instrument the builder first (R34, R35), remove the run-killer (R36),
then elevate the layers while the builder's behaviour is fixed alongside (R37, R38), and freeze the
builder's plan last (R39) — because "seamless" is defined by the assets' contract, and that has to stop
moving before the engine is tuned to it.

### 2.8 · P4 derivability inventions (Phase 4 — nikasha_test/derivations/L1..L5_INVENTIONS.md)

One row per invention recorded by the fresh-reader derivations. `surfaced by` = nikasha-test P4
derivability \<layer\>. Text = what had to be invented, the template clause quoted verbatim, and the
proposed fix. All OPEN. Where one fix serves many rows, the primary row carries the effort and the
rest `depends_on` it.

#### 2.8.1 · L1 (15 rows — source file footer claims 17; INV-L1-09/-15 folded/unused, see §5)

| # | change (what → clause → proposed) | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R85 | Per-layer necessity set over P01–P24/V01–V13 (which rows cannot be answered without L1). Clause (T3 §0.1): "List the P-needs and V-journeys for which this layer is **necessary** — not "involved in", not "contributes to", but *cannot be answered without*." → Add to T2 §3.1 (or T1 §11) a per-layer "necessary for P/V" column derived from the DP-contract ↔ P/V mapping; a layer instance then narrows, never invents | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 12 | OPEN |
| R86 | Seed and migration-pin DAG readings; census emits only the live-registry view. Clause (T3 §0.3): "measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" → Extend the census with `depends_on` as read from (a) registry seed, (b) migration pin, (c) live asset_registry; emit the disagreement set per asset | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 6 | OPEN |
| R87 | Deployed-vs-current-code half of the three-way baseline, per asset. Clause (T3 §1.1): "whether current code on any live head differs from what is deployed" → Census gains a per-asset field: deployed schema hash vs newest live-head writer hash, with the commits named | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 6 | OPEN |
| R88 | L1's life-event switch behaviour (what a computation layer emits when the switch is OFF). Clause (T3 §2.1): "The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild." → State in T2 §9.2, per layer: L1 computes identically under both states; the switch binds consumers (L2+), not the fact layer; detector: birth-fact immutability per (chart_id, input revision) | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 3 | OPEN |
| R89 | Assignment of §3.4 presentation rows to layers (T2 maps fields→contracts, never rows→layers). Clause (T2 §13.3 item 6): "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" → Add to T2 §3.4 a "carried by layer" column per row (conventions → L1 via DP01/DP03; intermediate quantities → L1 via DP03/DP04; dignity components → L1 via DP04; method/school, passed clauses, competing readings, typed chains, clock rows → L0/L2/L3 as named) | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 8 | OPEN |
| R90 | Enumerated list of coverage obligations L1 owns (Product §3 names substance, not owned obligations; width NOT_GENERIC on all 19). Clause (T3 §2.4): "Which of the product's coverage obligations this layer owns, with prerequisites, variants, exceptions, negative cases and uncertainty. Each ends in one of the five states." → Data plane §5 gains a per-layer obligation enumeration; the inspector declares each asset's universe so width is measurable | nikasha-test P4 derivability L1 | BLOCKS_LAYER | R22 | 6 | OPEN |
| R91 | Which of the sixteen entity classes L1 emits/accepts; the per-class independent-map census (`local_map_candidates: -1`). Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts; for each, whether every name resolves through the controlled set … how many independent maps the layer's code carries (permitted: one)" → Census emits per-class alias coverage and the map census per class; T2 names each layer's emitted/accepted classes | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 6 | OPEN |
| R92 | Per-asset named Jyotish concepts with the carriage check each invites. **C-9 CONFIRMED for L1** (Carr.detector NO_DETECTOR ×19). Clause (T3 §4.4): "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" → The layer instance carries, per asset, a (concept, check ∈ {D1,D2,D3}) pair; proposed L1 default: pure-computation D3, classical-clause restatement D1, dual-authority D2 — instance content, not left to brief authors | nikasha-test P4 derivability L1 | BLOCKS_LAYER | R09 | 1 | OPEN |
| R93 | Per-asset disposition (P/I/E/Q/C/H/R/U) and the preserved kernel; no rule maps census evidence to a disposition. Clause (T3 §4.4): "- its disposition and its "must add" list (3.2, 3.3) … - **the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" → T3 §3.2 gains an evidence→disposition decision rule (e.g. exercised + served + history FAIL ⇒ E; exercised + 0 rows + 0 modules ⇒ U pending §0.1); §3.2 names each preserved kernel explicitly (table span/key, algorithm, conventions) | nikasha-test P4 derivability L1 | BLOCKS_LAYER | — | 6 | OPEN |
| R94 | Whether the presentation-parity acceptance test is the layer plan's own work (§12.2 [TRANSFERS] vs T3 §5.4 test 4). Clauses (T2 §1): "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work." vs (T3 §5.4): "4. **Presentation parity** holds for the layer's served surface." → T3 §5.4 test 4 gains: "run where the surface exists; where the owning plane is not built, record [TRANSFERS]-pending — never a pass, never a block" | nikasha-test P4 derivability L1 | BLOCKS_LAYER | R71 | 1 | OPEN |
| R95 | Ownership/counting/idempotency rules for one table with several producers (`chart_facts` ← 7 L1 writers; identical 421,096-row figure under each). **C-10/R06/R10 CONFIRMED for L1.** Clause (T3 §1.1): "For each: target table(s) — a **set**, not one pointer, for multi-table assets — row counts in production, columns, contract fields live, last build, and whether current code on any live head differs from what is deployed." → Inverse rule: where several assets share a target, the layer plan names the table's counting owner, scopes count_sql per producer key, and bars any writer's Build check 6 from answering for the whole table | nikasha-test P4 derivability L1 | BLOCKS_LAYER | R06 | 2 | OPEN |
| R96 | The shared-table natural key for L1's delete-then-insert convention (`chart_facts` keyed on fact_id, 7 writers; ga_nakshatra carries ON CONFLICT — census Idem PARTIAL). Clause (T4, L1 row): "`Idem` is delete-then-insert on chart × natural key; the load-bearing rule is "consumers refer to L1 facts, they do not recompute them"" → Define per shared table: natural key = (chart_id, ayanamsha_id, fact-type/producer scope); each writer's delete scopes to its own fact-type set; state the scope set in the layer plan | nikasha-test P4 derivability L1 | DEGRADES | R95 | 2 | OPEN |
| R97 | The `kind` of a writer-backed data asset with no declared target_table (ga_strength, ga_structural — Build.target N/A). Clause (T4 §0): "kind: data \| service (no table by design) \| multi-table \| rider (producer_covered) \| static (migration-seeded)" → Add `kind: data (target set undeclared)` as a defect-kind, or require check 3 to FAIL (not N/A) when asset_kind=data, has_writer=true, target_table=null | nikasha-test P4 derivability L1 | DEGRADES | R14 | 2 | OPEN |
| R98 | The declared universe for a varṣaphala year-lord computation (charts × years × lord-set); census NOT_GENERIC. Clause (T4 §1.1): "Declare the universe first, from a source or from the ontology: how many instances the concept has … and which dimensions each instance should carry." → The layer instance §2.4 names each asset's universe source (ontology class or text); the asset brief cites it, never declares it ad hoc | nikasha-test P4 derivability L1 | DEGRADES | R22, R90 | 2 | OPEN |
| R99 | The verdict for an EMPTY data table with state=lit, rows_written=0 (ga_prashna: 51 runs, 0 rows, 0 modules — the uncovered third case). Clause (T4 §4.2 check 6): "**completion honesty** \| the build record agrees with the live count. `rows_written = 0` against a populated table is a status with no measurement behind it, and for a service it is indistinguishable from a writer that produced nothing" → Check 6 gains: for a data asset, rows_written=0 with 0 live rows is PARTIAL unless the layer plan declares the asset empty-by-design; "empty by design" is a layer-instance claim with its own detector | nikasha-test P4 derivability L1 | BLOCKS_LAYER | R52 | 2 | OPEN |

#### 2.8.2 · L2 (30 rows)

| # | change (what → clause → proposed) | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R100 | (I-01) P-needs/V-journeys L2 is necessary for; tiers assign none to any layer. Clause (T3 §0.1): "List the P-needs and V-journeys for which this layer is **necessary** …" → T2 gains a layer × P/V necessity table; skeleton then narrows, never assigns | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R101 | (I-02) The §0.2 paragraph "what it computes that existing software does not" for L2. Clause (T3 §0.2): "In one paragraph: the distinctions this layer makes **earnable** that were not earnable before it. Name what it computes that existing software does not, and what it hands the reasoning layer to read across it." → T2 §6.3's Bodha narrative promoted to canonical content the instance quotes | nikasha-test P4 derivability L2 | DEGRADES | — | 4 | OPEN |
| R102 | (I-03) Three-source dependency reconciliation; census reads the live registry only, emits edge counts not edge lists. Clause (T3 §0.3): "measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" → Census emits per-asset `depends_on` edge lists plus a seed/pin/live three-way diff per layer | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R86 | 0.5 | OPEN |
| R103 | (I-04) Shared table with SEVEN registered L2 producers (`bodha_msr_signals`, each credited with all 150,724 rows / 85 columns). **C-10/R06/R10 CONFIRMED for L2.** Clause (T3 §1.1): "For each: target table(s) — a **set**, not one pointer, for multi-table assets — row counts in production, columns, contract fields live, last build" → R06's proposal confirmed sufficient, plus: two assets sharing one writer file must declare the split | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R06 | 1 | OPEN |
| R104 | (I-05) "Deployed vs current code" half of the three-way baseline. Clause (T3 §1.1): "whether current code on any live head differs from what is deployed" → Census gains a deployed-vs-head diff (schema fingerprint + writer file hash per asset) | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R87 | 0.5 | OPEN |
| R105 | (I-06) L2's synergistic term has no harness and no synergy binding; without it the 1.5 shortfall (elevation delta) is uncomputable. Clauses (T3 §1.3/§1.5): "the layer's synergy binding if one exists"; "Record the synergistic term as a fraction of the total **only where an ablation harness exists to produce it** … Do not invent a fraction to fill the field." → T3 prescribes a minimum synergy harness per chart-product layer (seam-by-seam measurement per §1.5, mandatory content, named instrument) | nikasha-test P4 derivability L2 | DEGRADES | — | 16 | OPEN |
| R106 | (I-07) Consumer-verified evidence states (consumed / traceably transformed / value-evaluated). Clause (T3 §1.4): "measured_by: for each produced contract, its position on source-present → qualified → consumed → traceably transformed → served → value evaluated, verified at the consumer" → A consumer-side probe per produced DP contract (a query at the L3/inquiry reader confirming the fields it actually read) | nikasha-test P4 derivability L2 | DEGRADES | — | 8 | OPEN |
| R107 | (I-08) L2's life-event-switch behaviour and storage separation. Clause (T3 §2.1 inherits): "Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)" → T2 §9.2 gains a per-layer switch-behaviour table (six rows), or T3 §2.1 states the instance defines it under named constraints | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R88 | 0.5 | OPEN |
| R108 | (I-09) Which §3.4 presentation rows L2 carries. Clause (T2 §13.3 item 6): "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" → T2 §3.4's field→contract table gains a third column: carrying layer | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R89 | 0.5 | OPEN |
| R109 | (I-10) Per-asset mapping to DP contracts with declared use; "declared use" exists nowhere as data. Clause (T3 §2.3): "Every consumed input declares its use — calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation, evaluation. **A citation with no declared use is not a contract.**" → The registry gains `produces_contracts` / `consumes_contracts` columns per asset; the census reports them | nikasha-test P4 derivability L2 | BLOCKS_LAYER | — | 8 | OPEN |
| R110 | (I-11) Which product §3/§5 coverage obligations L2 owns (Complete.width NOT_GENERIC 23/23). Clause (T3 §2.4): "Which of the product's coverage obligations this layer owns, with prerequisites, variants, exceptions, negative cases and uncertainty." → T2 §5's domain obligations carry an owner-layer column (joins R22) | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R90 | 0.5 | OPEN |
| R111 | (I-12) Which of the sixteen entity classes L2 emits/accepts; per-class map census (`local_map_candidates: -1`). Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts … (permitted: one)" → T2 §4.1 or the registry assigns entity classes per layer; the inspector's map census is implemented (replace −1) | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R91 | 0.5 | OPEN |
| R112 | (I-13) Per-asset carriage-check assignment. **C-9/R09 CONFIRMED for L2** (Carr.detector NO_DETECTOR 23/23). Clauses (T3 §2.7, §4.4): "For each obligation the layer owns (§2.4), state which of a–c applies, the detector, and its current result"; "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites" → R09's proposal stands, confirmed on a second layer | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R113 | (I-14) The intra-layer topological order and the "CURRENT frozen definition revision" for gate scoping. Clause (T3 §2.5): "measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision" → The census emits the edge list it already resolves, and names the frozen definition revision it evaluated against | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R86 | 3 | OPEN |
| R114 | (I-15) Narrowing §0.1's P/V rows per asset. Clause (T3 §4.4): "the P-needs and V-journeys the asset serves (from 0.1, narrowed)" → Resolved transitively by R85's fix | nikasha-test P4 derivability L2 | DEGRADES | R85 | 0.5 | OPEN |
| R115 | (I-16) Per-asset dispositions and must-add lists require Part-1 measurements that are unmeasured/unmeasurable (I-06). Clauses (T3 §4.4, §3.2): "its disposition and its 'must add' list (3.2, 3.3)"; "For every asset and service in 1.1, one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" → A minimum Part-1 measurement floor below which dispositions are recorded U (unresolved) by rule, not by author choice | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R93 | 1 | OPEN |
| R116 | (I-17) The per-asset preserved kernel; sourced "(from 3.2)" which is itself underivable. Clause (T3 §4.4): "**the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" → T4 §0.1 row 12 re-sourced: the kernel is declared in the registry per asset (grain + upsert/delete key + immutable columns); the instance reads it | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R93 | 2 | OPEN |
| R117 | (I-18) A detector per correctness rule — none exists for any L2 rule. Clause (T3 §2.1): "measured_by: a detector per rule, named here, that can report the rule violated … **For each rule, the detector.** A rule with no detector is a wish." → A detector registry per layer-rule (even if every entry opens as NO_DETECTOR, the template already scores that honestly) | nikasha-test P4 derivability L2 | DEGRADES | — | 8 | OPEN |
| R118 | (I-19) Per-asset weighting of L2's two scored obligations (row provided at layer altitude only). Clause (T3 §4.4): "the ten obligations it is scored on (from 0.2)" → Acceptable as-is if the template says layer-uniform scoring is the default; today neither permitted nor forbidden | nikasha-test P4 derivability L2 | COSMETIC | — | 0.5 | OPEN |
| R119 | (I-20) [TRANSFERS] material embedded without the mark at the point of obligation (§13.3 items 1 and 6, template §2.2 measured_by, T4 §1.2). Clause (T2 §1): "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work." → Every §13.3 item, DP contract row and §12.2 row carries its [TRANSFERS] tag at the point where a layer plan reads it, not only where it is defined | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R71 | 3 | OPEN |
| R120 | (I-21) The `role` field value ("neither") — no tier assigns manifestation/temporal/neither per asset. Clause (T4 §0): "role: manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" → Layer §4.4 gains the per-asset role assignment it is cited as sourcing | nikasha-test P4 derivability L2 | DEGRADES | — | 2 | OPEN |
| R121 | (I-22) The asset-purpose paragraph beyond one derivable line. Clause (T4 §0.2): "written so a reader who knows the product but not this asset can say why removing it would cost something" → The registry carries a one-line purpose per asset (it has catalog_status; purpose is the missing twin) | nikasha-test P4 derivability L2 | COSMETIC | — | 2 | OPEN |
| R122 | (I-23) Declared-vs-actual consumer comparison; no grep population over readers. Clause (T4 §1): "Consumers, declared vs actual: `depends_on` edges in; code that actually reads it, writer-side and serving-side, grep population stated. **The gap between the two is a finding, not a footnote**" → The inspector emits both edge directions and a code-reader census per asset | nikasha-test P4 derivability L2 | DEGRADES | — | 6 | OPEN |
| R123 | (I-24) The declared universe the width census divides by (23/23 NOT_GENERIC). Clause (T4 §1.1): "Declare the universe first, from a source or from the ontology"; census: "no declared universe for this asset — declaring one is the first width gap" → R22's fix, confirmed needed layer-wide on L2: a registry/instance field for the declared universe | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R22 | 2 | OPEN |
| R124 | (I-25) The testable content of "interpretive fidelity" for the asset. Clauses (T4 §3; T1 §11): "what satisfied means for this asset specifically" → Layer §3.1 carries a per-obligation test template the brief instantiates | nikasha-test P4 derivability L2 | DEGRADES | — | 4 | OPEN |
| R125 | (I-26) The `kind` value for a view-target asset (bo_samvada) — the closed list has no place for it. Clause (T4 §0): "kind: data \| service \| multi-table \| rider \| static" → The kind vocabulary gains `view` (projection over other assets' tables; idempotency and count checks re-scoped) — extends R14's service clause | nikasha-test P4 derivability L2 | DEGRADES | R14 | 2 | OPEN |
| R126 | (I-27) Whether the asset is empty-by-design or populated (live_rows 0 via stub count_sql vs Complete.depth 15). Clause (T4 §1): "rows by the asset's own `count_sql` (the cockpit instrument), floor, delta; … whether `count_sql` and `target_table` are truthful" → R46's fix (count the view), plus the inspector flags stub count_sql (`SELECT 0`) as a finding class of its own | nikasha-test P4 derivability L2 | DEGRADES | R46 | 1 | OPEN |
| R127 | (I-28) What the writer actually builds (the view, or a table it reads) — Idem.pattern PARTIAL "likely delegates". Clause (T4 §1): "Producer: writer module and `@register` id · or the asset it rides on · or 'static, migration N' · or 'service'" → R20's fix (follow delegation into the seeder), confirmed load-bearing for L2's three delegating writers (bo_bimba, bo_pramana_mapa, bo_samvada) | nikasha-test P4 derivability L2 | DEGRADES | R20 | 0.5 | OPEN |
| R128 | (I-29) Ldgr and Vocab verdicts missing entirely for a view asset (Vocab 22/23, Ldgr 16/23) — silently exempted instead of N/A-with-reason. Clause (T4 §4): "A conditional gate that does not apply is disposed of with an explicit `N/A` and one line of reason. It is never silently dropped." → The inspector emits every gate row for every asset, N/A-with-reason included (a missing row is a harness bug, not a verdict) | nikasha-test P4 derivability L2 | BLOCKS_LAYER | R48 | 3 | OPEN |
| R129 | (I-30) The testable content of "completeness" for a digest: a view-vs-source parity check no template defines. Clauses (T4 §3 + T3 §2.4 five-states rule) → For `kind: view` assets, §3 specialises completeness as a parity query between the view and its source tables | nikasha-test P4 derivability L2 | DEGRADES | R125 | 4 | OPEN |

#### 2.8.3 · L3 (49 rows)

| # | change (what → clause → proposed) | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R130 | Per-layer P-need/V-journey assignment (only P24/V13 anchored via DP08). Clause (T3 §0.1): "List the P-needs and V-journeys for which this layer is **necessary**" → Add to data plane §13.3 item 1: a P/V-to-layer necessity table, one row per layer, sealed | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R131 | "What it computes that existing software does not". Clause (T3 §0.2): "Name what it computes that existing software does not, and what it hands the reasoning layer to read across." → Drop the external-comparison demand from the template, or supply a named comparison baseline per layer | nikasha-test P4 derivability L3 | DEGRADES | R101 | 1 | OPEN |
| R132 | Seed + migration-pin reconciliation sources. Clause (T3 §0.3): "registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" → Extend asset_census.py to emit the seed and pin reads per layer | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R86 | 0.5 | OPEN |
| R133 | Edge type per edge. Clause (T3 §0.3): "Receives from: upstream layers, by edge type, by DP contract." → Add `edge_type` to the registry schema and census output | nikasha-test P4 derivability L3 | DEGRADES | — | 3 | OPEN |
| R134 | Production row counts via own count_sql — the census is sandbox; live_rows null ×23; L3_prod_20260926.json missing (only its log). Clause (T3 §1.1): "the production probe (asset_elevation_tracker.py --layer <L> --env-file)" → The L3 production census must exist | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R47, R40 | 2 | OPEN |
| R135 | Floor and delta-per-floor per asset. Clause (T4 §1, inherited by §1.1): "rows by the asset's own `count_sql` (the cockpit instrument), floor, delta" → Census must emit floor and Δ per asset | nikasha-test P4 derivability L3 | DEGRADES | R48 | 2 | OPEN |
| R136 | Shared-table multi-producer model — kala_gochara_windows produced by ka_gochara (CURRENT) and ka_gochara_sweep (RETIRED), each credited with the same 40,117 rows. **C-10/R06/R10 CONFIRMED for L3.** Clause (T3 §1.1): "For each: target table(s) — a **set**, not one pointer, for multi-table assets" → Registry needs producer partition keys; census must scope count_sql per producer | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R06 | 0.5 | OPEN |
| R137 | Per-rule detectors, incl. the L3 switch rule. Clause (T3 §2.1): "**For each rule, the detector.** A rule with no detector is a wish." → Template §2.1 names the detector per §8.1 row, at least by class (schema scan / writer-source scan) | nikasha-test P4 derivability L3 | DEGRADES | R117 | 0.5 | OPEN |
| R138 | L3-specific switch ON/OFF behaviour and storage separation. Clause (T3 §2.1): "The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild." → Data plane §9.2 must carry a per-layer switch table; L3's row absent from the tier summary | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R88 | 0.5 | OPEN |
| R139 | Full set of §3.4 presentation rows L3 carries. Clause (T2 §13.3 item 6): "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" → §3.4's carriage mapping is row→DP-contract; add row→layer assignment | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R89 | 0.5 | OPEN |
| R140 | Ownership of Presentation parity — [TRANSFERS] in T2 yet a layer acceptance test in T3. Clauses (T2 §1) vs (T3 §5.4 test 4): "Presentation parity holds for the layer's served surface" → Resolve: either §5.4 test 4 reads "holds, where the layer is the owner" or §12.2's row loses [TRANSFERS] | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R71 | 0.5 | OPEN |
| R141 | Per-contract fields/grain/identity and declared use per consumed input. Clause (T3 §2.3): "Every consumed input declares its use … **A citation with no declared use is not a contract.**" → Census must emit field-level producer/consumer verification, or §2.3 is unfalsifiable as specified | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R109 | 0.5 | OPEN |
| R142 | Five-state coverage verdicts per obligation. Clause (T3 §2.4): "per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank" → No instrument maps assets to these states; add a coverage census check per §5 obligation | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R90 | 3 | OPEN |
| R143 | Which of the sixteen entity classes L3 emits/accepts (local_map_candidates = -1). Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts" → T2 §13.3 item 1a must pre-assign classes per layer | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R91 | 0.5 | OPEN |
| R144 | Per-asset carriage check assignment. **C-9/R09 CONFIRMED for L3** (Carr.detector NO_DETECTOR 23/23). Clause (T3 §4.4): "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" → §2.7 must assign a/b/c per asset, not per obligation | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R145 | Topological order + cross-layer gate state under a frozen definition revision — no frozen L3 definition revision exists; the clause is unsatisfiable before the instance exists (circular). Clause (T3 §2.5): "cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision" | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R113 | 2 | OPEN |
| R146 | Three-way baseline per asset — census reads no current code and no deployed production for L3. Clause (T3 §4.1): "State the three-way baseline per asset: **deployed** … **current code** … **target**" → Add a code-head read to the census | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R87 | 0.5 | OPEN |
| R147 | Dispositions and must-add lists. Clause (T3 §3.2): "one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" → Expected: Part 3 is authored strategy; recorded because §4.4 promises the brief author inherits it, and a skeleton derivation cannot | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R93 | 0.5 | OPEN |
| R148 | Preserved kernel per asset. Clause (T3 §4.4): "**the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" → No tier text or census field defines any kernel; needs a per-asset registry field or a §3.2 rule for deriving it | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R116 | 0.5 | OPEN |
| R149 | (B r1) P/V set beyond P24/V13 for ka_kalasutra → as R130 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R150 | (B r3) Switch behaviour + detector for ka_kalasutra. Clause (T3 §2.1): "The life-event switch: what this layer may do when ON, what it emits when OFF" → as R138 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R88 | 0.5 | OPEN |
| R151 | (B r4) Field-level presentation mapping. Clause (T2 §13.3 item 6) → as R139 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R89 | 0.5 | OPEN |
| R152 | (B r5) Per-asset (not per-layer) contract production + declared use. Clause (T3 §2.3): "for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends" → Layer instance carries a per-asset contract matrix; currently unspecified who assigns DP08 to ka_kalasutra vs ka_sangam | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R109 | 2 | OPEN |
| R153 | (B r6) Five-state coverage verdicts. Clause (T3 §2.4): "the five states, never a blank" → as R142 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R142 | 0.5 | OPEN |
| R154 | (B r7) Topological position + three-way baseline. Clause (T3 §4.1): "State the three-way baseline per asset: deployed … current code … target" → as R146 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R87 | 0.5 | OPEN |
| R155 | (B r8) Disposition + must-add. Clause (T3 §3.2) → as R147 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R93 | 0.5 | OPEN |
| R156 | (B r10) Synergy seam membership. Clause (T3 §1.3 inherits): "the layer's synergy binding if one exists" → No L3 seam list exists; the inherits clause itself presumes an artefact no tier produces | nikasha-test P4 derivability L3 | DEGRADES | R105 | 2 | OPEN |
| R157 | (B r11) Consumer-verified evidence state. Clause (T3 §1.4): "verified at the consumer, not asserted by the producer" → Census never queries consumers; add a consumer-side probe | nikasha-test P4 derivability L3 | DEGRADES | R106 | 0.5 | OPEN |
| R158 | (B r12) Preserved kernel. Clause (T3 §4.4) → as R148 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R116 | 0.5 | OPEN |
| R159 | (B r13) Concepts + carriage check (author chose D3). **C-9/R09 CONFIRMED (5th).** Clause (T3 §4.4): "the domain detector each invites" | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R160 | (B §1) Actual-consumer grep census. Clause (T4 §1): "code that actually reads it, writer-side and serving-side, grep population stated" → Census does not run it; required per brief | nikasha-test P4 derivability L3 | DEGRADES | R122 | 0.5 | OPEN |
| R161 | (B §4) Any verdict for the Null gate. Clause (T4 §4): "**Null** honest null … an underivable value is emitted as null, not as a plausible default" → The inspector runs no Null check — add it to asset_census.py | nikasha-test P4 derivability L3 | DEGRADES | — | 4 | OPEN |
| R162 | (B §5) Ledger gap rows (ids, owners) when the ledger holds no rows for the asset. Clause (T4 §5): "This section is those rows for this asset, in the ledger's own fields … rendered, never retyped" → "rendered, never retyped" is unsatisfiable when the ledger holds no rows; the clause needs a first-registration path | nikasha-test P4 derivability L3 | DEGRADES | R58 | 2 | OPEN |
| R163 | (B §6) may_touch / must_not_touch globs. Clause (T4 §6): "may_touch:      <exact globs>" → Expected authored content; logged because no census field supports it | nikasha-test P4 derivability L3 | COSMETIC | — | 0.5 | OPEN |
| R164 | (C r1) P/V set beyond P24/V13 for ka_dasha_kala → as R130 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R165 | (C r3) Switch behaviour + detector for a service. Clause (T3 §2.1): "For each rule, the detector. A rule with no detector is a wish." → as R138, service-shaped | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R88, R14 | 0.5 | OPEN |
| R166 | (C r4) Service output fields carrying the temporal presentation row. Clause (T2 §13.3 item 6) → as R139, plus: define "field" for a service | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R89, R14 | 1 | OPEN |
| R167 | (C r5) How a service "produces" a DP contract. Clause (T3 §2.3): "Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation)" → The row shape presumes a table; add a service contract shape | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R109, R14 | 2 | OPEN |
| R168 | (C r6) Five-state coverage verdicts. Clause (T3 §2.4): "the five states, never a blank" → as R142 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R142 | 0.5 | OPEN |
| R169 | (C r7) Topological position + baseline. Clause (T3 §4.1): "State the three-way baseline per asset" → as R146 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R87 | 0.5 | OPEN |
| R170 | (C r8) Disposition + must-add. Clause (T3 §3.2) → as R147 | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R93 | 0.5 | OPEN |
| R171 | (C r9) What "ablate one" means for a table-less service. Clause (T3 §1.2): "the reading with it against the reading without it" → Define the removal procedure for a service (deregister? fence endpoint?) | nikasha-test P4 derivability L3 | DEGRADES | R105, R14 | 2 | OPEN |
| R172 | (C r11) Consumer-verified evidence state. Clause (T3 §1.4): "verified at the consumer, not asserted by the producer" → as R157 | nikasha-test P4 derivability L3 | DEGRADES | R106 | 0.5 | OPEN |
| R173 | (C r12) Preserved kernel of a service (behaviour, not rows). Clause (T3 §4.4) → as R148, plus a service-kernel definition | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R116, R14 | 1 | OPEN |
| R174 | (C r13) Concepts + carriage check (author chose D3). **C-9/R09 CONFIRMED (6th).** Clause (T3 §4.4): "the domain detector each invites" | nikasha-test P4 derivability L3 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R175 | (C §1) Service descriptor (endpoint, signature) the word "service" must carry. Clause (T4 §1 producer bullet): "or 'service'" → T4 §1 names the kind and specifies nothing it must disclose | nikasha-test P4 derivability L3 | DEGRADES | R14 | 2 | OPEN |
| R176 | (C §1.1) Completeness question for a row-less asset. Clause (T4 §1.1): "a census against a DECLARED universe" → Undefined for services; pilot 4's N/A convention was also invented there | nikasha-test P4 derivability L3 | DEGRADES | R14, R22 | 1 | OPEN |
| R177 | (C §4) Vocabulary test for a service's output. Clause (T4 §4 Vocab row): "one canonical id per thing, one closed alias set" → Gate is table-oriented; no service output-vocabulary check exists | nikasha-test P4 derivability L3 | DEGRADES | R14 | 2 | OPEN |
| R178 | (C §5) Ledger gap rows (ids, owners). Clause (T4 §5): "rendered, never retyped" → as R162 | nikasha-test P4 derivability L3 | DEGRADES | R162 | 0.5 | OPEN |

#### 2.8.4 · L4 (18 rows)

| # | change (what → clause → proposed) | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R179 | The P-need/V-journey rows L4 is necessary for, and the loss-distinction per row. Clause (T3 §0.1): "inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)" → Add to T2 §13.3 (or a new §13.4): a per-layer assignment table mapping each P01–P24 need and V01–V13 journey to the layer(s) necessary for it, so 0.1 is a lookup, not a judgement | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R180 | The "what it computes that existing software does not" claim. Clause (T3 §0.2) → T2 §6.5 (Phala narrative) should state the distinct-from-existing-software claim explicitly per layer | nikasha-test P4 derivability L4 | DEGRADES | R101 | 1 | OPEN |
| R181 | Which DP contracts L4 produces (vs consumes), and the edge type of each L4 edge. Clause (T3 §0.3): "- **Receives from:** upstream layers, by edge type, by DP contract.\n- **Hands onward to:** downstream layers, by edge type, by DP contract." → T2 §7.1 gains a per-layer rollup: contracts produced and consumed, each with its §3.2 edge type | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R109 | 0.5 | OPEN |
| R182 | Per-asset "current code on any live head differs from deployed" and the residual/shared/historical kind classification. Clause (T3 §1.1): "For each: target table(s) — a **set**, not one pointer … and whether current code on any live head differs from what is deployed." → Name the instrument (a git-head scan + registry field for kind) in §1.1's measured_by, and have the census emit both | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R87 | 0.5 | OPEN |
| R183 | A named detector per correctness rule (e.g. "L4 must not rewrite the original forecast"). Clause (T3 §2.1): "**For each rule, the detector.** A rule with no detector is a wish." → T3 §2.1 should state, per layer, which existing detector discharges the layer's §8.1 row (for L4: the DP15a emission-freeze check), or record NO_DETECTOR explicitly as the expected fill | nikasha-test P4 derivability L4 | DEGRADES | R117 | 0.5 | OPEN |
| R184 | Which §3.4 presentation rows L4 carries and which fields it hands onward. Clause (T2 §13.3 item 6) → T2 §3.4 gains a sixth column assigning each presentation row to its carrying layer(s) | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R89 | 0.5 | OPEN |
| R185 | Whether the presentation-parity test is L4's own work, given [TRANSFERS]. Clause (T3 §2.2): "measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, identical finding / confidence / uncertainty" → T3 §2.2 must carry the [TRANSFERS] marking: the layer states the fields it carries; the parity test belongs to the retrieval/conversation plane's artefact | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R71 | 0.5 | OPEN |
| R186 | The declared use of every consumed contract. Clause (T3 §2.3): "Every consumed input declares its use … **A citation with no declared use is not a contract.**" → T2 §7.1 gains a declared-use column per contract, so instances inherit rather than assign | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R109 | 0.5 | OPEN |
| R187 | Which product coverage obligations L4 owns. Clause (T3 §2.4) → T2 §5 gains a per-layer ownership column; layer instances also declare each asset's width universe (feeds R22) | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R90 | 0.5 | OPEN |
| R188 | A topological order and the frozen definition revision for egate scoping. Clause (T3 §2.5): "measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision" → Depends on the 0.3 three-source reconciliation; the census should emit the reconciled DAG and the revision id | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R113 | 0.5 | OPEN |
| R189 | Which of the sixteen entity classes L4 emits or accepts. Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts; for each, whether every name resolves through the controlled set" → T2 §4.1 gains a layer × entity-class matrix (emit / accept / untouched) | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R91 | 0.5 | OPEN |
| R190 | Per-asset carriage check and per-asset Jyotish concepts. **C-9/R09 CONFIRMED for L4** (Carr.detector NO_DETECTOR on all 9 L4 assets). Clauses (T3 §2.7, §4.4) → Per R09's proposed reopen: §2.7 gains a per-asset assignment table, or the template states the brief author chooses and records why | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R191 | L4's switch behaviour; per-asset dispositions; per-asset preserved kernels (§4.4 rows 3, 8, 12). Clauses (T3 §4.4): "- its correctness rules and switch behaviour (2.1)"; "- its disposition and its \"must add\" list (3.2, 3.3)"; "**the preserved kernel** … (from 3.2)" → Rows 8/12 transitively blocked by the absent ablation harness; the template should state the fallback fill ("harness absent — disposition provisional") so it is recorded, not invented. Switch behaviour needs one sentence per layer in T2 §9.2 | nikasha-test P4 derivability L4 | BLOCKS_LAYER | R93, R88 | 1 | OPEN |
| R192 | (PH_MUHURTA §0) role: manifestation. Clause (T4 §0): "role:             manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" → §4.4's thirteen rows contain no role row; either add row 14 (role per asset) to T3 §4.4 or drop the "# from layer §4.4" citation | nikasha-test P4 derivability L4 | DEGRADES | R120 | 0.5 | OPEN |
| R193 | (PH_MUHURTA §4) The Null-gate verdict — the inspector runs no Null check. Clause (T4 §4): "\| **Null** · honest null \| always \| an underivable value is emitted as null, not as a plausible default (§N.7 item 6) \| \| \| \|" → The inspector gains a Null check (e.g. default-valued columns vs null proportion), or the gate map states the detector is per-asset and the brief must name it | nikasha-test P4 derivability L4 | DEGRADES | R161 | 0.5 | OPEN |
| R194 | (both briefs §4) The Narr-gate applicability reading. Clause (T4 §4): "\| **Narr** · narration fidelity \| if it emits prose \| prose restates cited facts and never re-derives them (§N.7) \| \| \| \|" → The census should emit "emits prose: yes/no" per asset so the N/A-with-reason is measured, not inspected by hand | nikasha-test P4 derivability L4 | DEGRADES | — | 2 | OPEN |
| R195 | (both briefs §5) gap_id namespace and owner values for ledger rows. Clause (T4 §5): "`asset · gap_id · kind · criterion · what · change · detector · owner · gate · state · ts`" → State the gap_id allocation rule (per-layer prefix? next-free integer?) in T4 §5 or the ledger _schema line | nikasha-test P4 derivability L4 | DEGRADES | R58, R162 | 1 | OPEN |
| R196 | (PH_RECTIFICATION §0) A kind value for "writer exists but is packaged (__init__.py) and invisible to the inspector". Clause (T4 §0): "kind: data \| service \| multi-table \| rider \| static" → Primarily an inspector defect: the registered check must search writer packages (R43); if packaged writers remain legal, add a kind value or a writer_shape field | nikasha-test P4 derivability L4 | DEGRADES | R43, R14 | 1 | OPEN |

#### 2.8.5 · L5 (18 rows)

| # | change (what → clause → proposed) | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R197 | Per-layer P/V necessity assignment (no parent maps P01–P24/V01–V13 to layers). Clause (T3 §0.1): "List the P-needs and V-journeys for which this layer is **necessary** …" → T2 §11 or §13.3 item 1 gains a per-layer P/V necessity column, so §0.1 is a lookup, not an authorship | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R85 | 0.5 | OPEN |
| R198 | Per-layer produced/consumed DP-contract assignment assembled by reader. Clause (T2 §13.3 item 6): "Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests" → T2 §7.1 gains a per-layer produced/consumed index, or §13.3 item 6 names where that index lives | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R109 | 0.5 | OPEN |
| R199 | Per-layer switch ON/OFF emission semantics. Clause (T3 §2.1): "what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild" → T2 §9.2 gains a per-layer switch-behaviour table (may-do ON / emits OFF / storage separation) for L0–L5 | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R88 | 0.5 | OPEN |
| R200 | Which §3.4 presentation rows L5 carries (assignment exists nowhere; §3.4 rows are all chart-rendering fields — a chart-product-shaped requirement an evaluation layer cannot satisfy or vacuously passes). Clause (T2 §13.3 item 6) → T2 §3.4 gains a layer column assigning each row to its carrier layers, with an explicit rule for layers that carry none | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R89 | 0.5 | OPEN |
| R201 | Declared use per consumed contract. Clause (T3 §2.3): "Every consumed input declares its use … **A citation with no declared use is not a contract.**" → T3 §2.3 names the source of declared uses (a per-contract use registry, or the census), so the instance transcribes rather than invents | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R109 | 0.5 | OPEN |
| R202 | Per-layer split of the product's §5 coverage obligations. Clause (T3 §2.4): "Which of the product's coverage obligations this layer owns …" → T2 §5 gains an ownership matrix (obligation × layer, with the halving rule L0's instance used: meaning-half vs chart-half) | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R90 | 0.5 | OPEN |
| R203 | Which of the sixteen entity classes L5 emits or accepts. Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts" → T3 §2.6 names the instrument (a class census over the layer's writers and capability modules) and where its result is stored | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R91 | 0.5 | OPEN |
| R204 | Per-asset carriage-check assignment. **C-9/R09 CONFIRMED FOR L5** (Carr.detector NO_DETECTOR 14/14). Clause (T3 §4.4): "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" → Land R09 as registered; also fix the stale word "domain detector" → "carriage check" (pre-ruling-11 vocabulary) | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R09 | 0.5 | OPEN |
| R205 | Shared-table/multi-producer expression. **C-10/R06/R10 CONFIRMED FOR L5** (mi_bhara → kala_field_skill, ka_-prefixed, keyed (id)). Clause (T3 §1.1): "For each: target table(s) — a **set**, not one pointer, for multi-table assets" → Land R06: "a shared table declares its producers and each producer's `count_sql` is scoped to its own rows" | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R06 | 0.5 | OPEN |
| R206 | Ablation/synergy harness — recorded absent, not invented. Clause (T3 §1.5): "Record the synergistic term as a fraction of the total **only where an ablation harness exists to produce it**." → No text change needed; the harness is a work packet (mirrors L0 W-L0-7). Recorded for completeness | nikasha-test P4 derivability L5 | DEGRADES | R105 | 1 | OPEN |
| R207 | §4.4 rows 7/8/12: three-way baseline current-code read, dispositions, preserved kernels. Clause (T3 §4.4): "its position in the order and its three-way baseline (4.1) · its disposition and its 'must add' list (3.2, 3.3) · **the preserved kernel**" → Template should state the minimum instrument set an instance must run before §4.4 is writable (ablation harness, three-head code read, disposition register) so an unwritable §4.4 fails loudly at the instance, not silently at the brief | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R93, R87 | 1 | OPEN |
| R208 | (MI_KULA §0) role (manifestation/temporal/neither) not assigned per L5 asset. Clause (T4 §0): "role: … # from layer §4.4" → T3 §4.4 gains a fourteenth row (asset role), or T4 §0 states the author assigns it and records why | nikasha-test P4 derivability L5 | DEGRADES | R120 | 0.5 | OPEN |
| R209 | (MI_KULA §0.1 rows 1,3,4,5,6,8,12,13) Eight inheritance rows unfillable from tiers+census. Clause (T4 §0.1): "**A row you cannot fill is a defect in the layer instance — raise it there and stop; do not invent it here.**" → Rows collapse to the skeleton-level fixes (R85, R89, R90, R09, R116); no tier-4 change needed once tier 2/3 land | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R85, R89, R90, R09, R116 | 0.5 | OPEN |
| R210 | (MI_KULA §3) No detector for the layer's own scored obligation (predictive performance). Clause (T4 §3): "\| obligation \| what satisfied means for this asset specifically \| detector (named here, run in §4) \|" → T2/3 should name the per-obligation default detectors (as §2.7 does for carriage) so a layer scored on predictive performance is not NO_DETECTOR by construction | nikasha-test P4 derivability L5 | DEGRADES | R117 | 1 | OPEN |
| R211 | (MI_BHARA §0) `registry-orphan` kind — declared writer, no code; the five-kind vocabulary cannot express it. Clause (T4 §0): "kind: data \| service \| multi-table \| rider \| static" → T4 §0's kind set gains a sixth value or an explicit rule that a declared-but-absent writer is `data` plus a Build gap (extends R14's service-kind note) | nikasha-test P4 derivability L5 | DEGRADES | R14 | 1 | OPEN |
| R212 | (MI_BHARA §1) Producer line has no alternative for declared-but-absent writer. Clause (T4 §1): "**Producer:** writer module and `@register` id · or the asset it rides on · or "static, migration N" · or "service"." → State that a registry/code disagreement is reported, not forced into one of the four shapes | nikasha-test P4 derivability L5 | DEGRADES | R14, R211 | 0.5 | OPEN |
| R213 | (MI_BHARA §6/§4-Vocab) Idempotency/keying convention for non-chart-scoped L5 assets (declared key (id)). Clause (T4 §6): "**Idempotency** — the layer's convention: L0 `ON CONFLICT` upsert; L1+ delete-then-insert scoped to `(chart_id × natural key)`." → T4 §6 gains the third case: "L5 global/shared resources: delete-then-insert (or upsert) scoped to the declared key alone, without chart_id; the scope is stated per asset in §0" | nikasha-test P4 derivability L5 | DEGRADES | R96 | 1 | OPEN |
| R214 | Migration-pin source unavailable to the derivation; three-source reconciliation impossible from template-permitted inputs. Clause (T3 §0.3): "measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" → T3 names the migration pin's location (or the census as its reader) so "three sources" is runnable, or relaxes the requirement to "available sources, absence recorded" | nikasha-test P4 derivability L5 | BLOCKS_LAYER | R86 | 0.5 | OPEN |

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

## 5 · Source-count reconciliation notes (v2.0 assembly record)

- Campaign brief §5 Phase 6.2 expected per-layer invention counts of L1 17 / L2 30 / L3 49 / L4 17 /
  L5 17 (total 130). Measured by counting `INVENTION` lines in the source files on 2026-09-26:
  **L1 15 · L2 30 · L3 49 · L4 18 · L5 18 = 130**. The total matches; the per-layer split in the brief
  does not. L1's own footer claims "17 inventions total" while listing 15 (INV-L1-09 and INV-L1-15
  were folded into other rows / observations and carry no INVENTION line). L4 and L5 carry 18 each
  with no count footer. All 130 actual rows are registered (R85–R214); no source line was dropped.
- v1.0 rows R01–R84 carried forward verbatim in substance; states preserved as recorded in v1.0
  except R84, updated to MEASURED in P6 per campaign measurement (text appended, not replaced).
- L4's derivation file additionally records C-10/R06/R10 **REFUTED for L4** (9 distinct target
  tables; each ph_* table's inserts match only its own writer) — noted on R06, not a separate row.
