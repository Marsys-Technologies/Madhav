# MASTER PLAN — Identity, Promise, and the First True Measurement
**Plan of record · 2026-08-08 · ratified by the native with Fable 5**
**Campaigns: A · ADHIṢṬHĀNA (foundation) → CHECKPOINT → B · PRATIJÑĀ v4 → C · ABHYĀSA (practice)**

---

## 0. Mission and diagnosis in one paragraph

Every defect this arc has surfaced — fourteen named classes across four campaigns — is one
architectural sin at different layers: **derived layers join on free text that no contract
governs, instead of referencing structured identity.** The fix is not another engine patch. It
is: give identity a contract (adoption-measured, not module-measured) · give evidence the right
unit (deduplicated L1 facts via a parsed Identity Index, never signal echoes) · give judgment
structural inputs scored by a bounded classical rubric (saturation impossible by construction;
denial earned by cited configurations, never by affliction volume) · give verification real
data at three tiers (snapshot CI · pre-merge live simulation · post-deploy acceptance) · give
learning a loop that produces a measurement within days (promise-layer scoreboard) while the
temporal skill score accrues power. One human+Fable design checkpoint sits between foundation
and engine — the single highest-leverage process change, because every prior failure shipped
with its design unreviewed.

## 1. Standing rulings that govern (already ratified)

R6 promise-as-modifier · R11 classical per-class significators, citation-backed ·
R12 occurrence separate from condition · R13 NO FITTING to the native's outcomes — absolute ·
R14 measurement discipline (numbered, superseded-with-reason, side-by-side; #1 baseline
permanent) · R15 the 2019 US move counts as both relocation and foreign_settlement ·
R16 every claim scope-stated; every ledger status claim cites its detector query.

**New rulings this plan adds (proposed, to ratify at Campaign A launch):**
- **R17 — Adoption over addition.** Identity work is accepted by REMOVAL counts and adoption
  censuses, never by module existence. A vocabulary module with a dead mirror or surviving
  independent maps is a FAILED deliverable.
- **R18 — Bounded rubric scoring.** All promise grades come from factor rubrics with weights
  summing to 1, factor scores in [0,1] from cited classical bands. No accumulating sums, no
  post-hoc normalization, no distribution-derived thresholds.
- **R19 — L1 stays sealed.** chart_facts rows are never rewritten for identity reasons.
  Convergence comes from producer fixes (forward), the Fact Identity Index (derived), and
  read-time canonicalization. The Index is rebuildable at any time from chart_facts alone.

## 2. Grounding — what exists and is reused (verified 2026-08-08)

| Asset | State | Role in plan |
|---|---|---|
| `brahmagyan/domain_vocabulary.py` (13 domains + 19 synonyms + telemetry) | LIVE, 5 importers | Pattern + module to extend |
| `platform/src/lib/domain_vocabulary.ts` | DEAD (0 importers) | Wire or fold in — adoption debt |
| 4 divergent TS domain vocabularies (synthesis/types, spine/constants, vidhi/scope_classifier, ranking/priors_config) | LIVE, divergent | DELETE in A |
| `valence_doctrine.norm_graha()` | Best Python graha resolver (codes+long+Sanskrit → system A) | PROMOTE to SSoT |
| `address_resolver.grahaCodeOf()` | Best TS resolver (throws on unknown) | PROMOTE to TS anchor |
| 13 Python + 6 TS independent graha maps | LIVE, 3 output systems | Reduce to 1+1 (R17) |
| `ga_condition_writer.py` `.upper()` at :1078/:1104/:1127/:1310/:1334 | The LONG-name producer | One-file fix |
| `brahma_ontology` (entity_class, canonical_id, synonyms[], citation; GIN) | REAL, disconnected | Complete: +varga class, +storage-code synonyms |
| `reference_planets/houses/karakas/vargas` (dignity data, significations, 77 karakas, citations) | REAL, unused by promise engine | Rubric band + karyatva source |
| `brahma_event_ontology.signature_model` (houses/lords/karakas/vargas per class) + `lel_category` | REAL, ignored by v3 | Karyatva source + L6 resolver seed |
| `l0_ghatana.EVENT_CLASSES` (27, Python) | SSoT-ready, no TS mirror | Mirror + FK/CHECK on gochara_resonance_map |
| `judgment_query` structural reads; fact-category-pin lint; census test patterns; `msr_referential_integrity --live` pattern | LIVE | Reader pattern + gate patterns |
| chart_facts: NO varga/house columns; 6 house encodings; 3 varga separators | Sealed, messy | Handled ONCE by the Index parser |
| PRATIJNA_ENGINE_V3_SPEC (karyatva content) + KaryatvaMap registry | Classically sound | Content carried into B1 spec v2 |

## 3. CAMPAIGN A — ADHIṢṬHĀNA (foundation; overnight, 1–2 nights)

Branch `adhisthana/integration`; ledger `00_ARCHITECTURE/briefs/adhisthana/ADHISTHANA_STATE.md`;
same swarm roles/rails (Conductor·Builders≤6·PARĪKṢAKA·ANTARYĀMIN·Gate-Executor), supervisor
loop, lease, R16 discipline throughout.

**Lane A1 — Producer convergence (small, first):** `ga_condition_writer` imports
`PLANET_TO_SUBJECT`; replace the five `.upper()` sites. Also `ga_vargas_writer:3002` floored
bodies. TDD: emitted subjects ∈ system A. (Forward-only; existing rows untouched per R19.)

**Lane A2 — Graha SSoT by promotion:** `brahmagyan/graha_vocabulary.py` created FROM
`norm_graha` (moved, not copied; valence_doctrine imports it back). TS: `grahaCodeOf` declared
canonical; the other 5 TS maps + 12 Python maps become imports or are deleted.
**Acceptance = census counting surviving independent maps: Python 13→1, TS 6→1** (the
domain-census static-scan pattern, extended to graha map shapes).

**Lane A3 — Registry completion:** `brahma_ontology` gains `entity_class='varga'` (from
`l0_reference.VARGAS`, 19 rows + the writers' 30-varga set reconciled, citations kept) and
storage-code synonyms for planets/houses/vargas (`MAR`, `RAH_MEAN`, `HOUSE_07`, `D9`…).
`list_entities.ts` VALID_ENTITY_CLASSES += varga. `ref_entity_resolve('MAR')` must resolve.
Migration is additive-only.

**Lane A4 — Event-class contract:** TS mirror of the 27 ids + parity test (the domain
pattern); FK or CHECK binding `gochara_resonance_map.event_class` (currently a comment);
`lel_event_writer.ts` stale "22 classes" comments fixed.

**Lane A5 — THE FACT IDENTITY INDEX (the keystone):** new derived table
`chart_fact_identity(fact_id PK, chart_id, entity_kind, graha_code, house_num, varga_id,
parse_rule, parsed_from)` built by ONE deterministic parser handling all six house encodings +
three varga separators + both planet naming systems, with per-rule provenance. Rebuildable
idempotently from chart_facts alone (R19). **Acceptance: coverage report per chart — % of
facts carrying each identity dimension, unparsed fact_key/subject shapes enumerated and
classified (identity-bearing vs genuinely identity-free facts like panchanga constants).
Target: >99% of identity-bearing facts parsed; every unparsed shape explained.** PARĪKṢAKA
verifies the parser against the live key inventory, not fixtures.

**Lane A6 — Gates:** (i) registry-parity governance script (constants ↔ brahma_ontology ↔
producers' emitted DISTINCT values; --self-test in CI, --live at deploy gate — the
msr_referential_integrity pattern); (ii) fact_subject well-formedness lint for NEW writer
code; (iii) graha/varga census wired into CI next to the domain census.

**Lane A7 — TS adoption debt:** the four divergent TS domain vocabularies deleted and
call sites migrated to the (now live) TS mirror; parity test now guards a used file.

**Lane A8 — Checkpoint artifacts (Conductor, from live data):**
1. **Factor→Fact Coverage Matrix** — for all 27 classes × karyatva factors: which
   (fact_category, fact_key, Index dimensions) satisfies each factor, verified non-empty per
   chart; gaps named (e.g., "Upapada: arudha_pada facts exist — UL specifically?").
2. **v4 Scoring Rubric Spec draft** — per-factor bands from reference_planets dignity data,
   weights per class from signature_model + citations, denial configurations enumerated with
   citations, occurrence & condition formulas (R12, R18), worked examples for
   marriage/separation/childbirth computed BY HAND on 482012f1's real facts.
Close per §H; RUN-TERMINAL; morning report R16-scoped.

## 4. THE CHECKPOINT (daytime; native + Fable; blocking)

Review the two artifacts. Questions to settle: factor coverage gaps and their dispositions ·
rubric bands and weights (classical soundness, R13 cleanliness) · denial-configuration list ·
the marriage/separation/childbirth hand-worked examples (do the numbers read like astrology?) ·
threshold semantics (what 0.6 occurrence MEANS) · consumer-contract impacts. Output: ratified
rubric spec v1.0 + any new rulings. **No engine code before this gate passes.**

## 5. CAMPAIGN B — PRATIJÑĀ v4 (overnight, 1–2 nights)

**Lane B1 — Chart Reader:** thin selection API over chart_facts × chart_fact_identity
(occupants(h), lord_of(h), graha_state(code), varga_factor(...), arudha(...)) — fact_key-pinned
(passes pin lint), deterministic ORDER BY, returns fact_ids for the B.3 ledger. NO computation
of dignity/strength — selects the L1 facts that already carry them (§N.7).

**Lane B2 — v4 engine:** rubric per ratified spec. Occurrence = Σ(weightᵢ·bandᵢ) with
Σweights=1 (R18) MINUS cited denial-configuration deductions; condition = affliction magnitude
on its own positive [0,10] scale (fixes the structurally-zero defect by design); status
thresholds with a-priori rubric meaning; derivation ledger lists every factor with its
fact_ids, band, weight, citation. Domain fallback only for provisional classes, labelled.

**Lane B3 — Three-tier verification:**
- CI: **real-data snapshot fixture** (one chart's facts+signals+Index exported, versioned,
  refresh procedure documented) + property tests: marriage≠separation with distinct evidence
  sets · childbirth independent of relationship affliction · afflicted-but-present 7H →
  occurrence>0 AND condition>0 · no status monoculture · no grade ≥9.5 without a cited
  maximal configuration · condition_grade nonzero somewhere · every citation resolves ·
  R13 audit (no constant traceable to native outcomes).
- Pre-merge: the offline live simulation harness (repo script) run by Gate-Executor;
  predicted distribution attached to the gate packet.
- Post-deploy: PARĪKṢAKA live acceptance on all three charts.

**Lane B4 — Downstream consumer audit (same campaign, from the traced graph):** ph_nimitta
promise_lift semantics vs new grade scale · ka_yojaka/ka_avadhi/ka_taranga/stage2 readers ·
mi_darshana prose + Mahā-Brief parser/conflict-resolver · query_pratijna envelope. Each
consumer: re-read, adjusted or explicitly confirmed, R16-scoped.

**Lane B5 — Rebuild all three charts** (full DAG, sequential, supervised, M0-style failure
classification first) → zero error/stale per chart, detector-cited.

**Lane B6 — MEASUREMENT #3** (temporal skill, R15 event set, R14 discipline, degenerate-
interval tripwire) — published beside #1 and superseded #2. Underpowered cells stay honest.

**Lane B7 — PROMISE-LAYER SCOREBOARD v0 (new measurement class):** for every chart with
outcome knowledge × every non-provisional class: occurrence-verdict vs lifetime-outcome,
with per-verdict derivation links. Pure measurement (R13: no tuning against it; future tuning
only on held-out charts). **This is the campaign's fast feedback: a validation signal within
days.** Includes THE MARRIAGE ANSWER — v4's honest verdict on 482012f1 marriage, whichever
way it falls, served at its earned tier.

Close: consumer-audit table, both measurements, arc governance (CURRENT_STATE/SESSION_LOG),
red-team with the full 14-class taxonomy + DISTRIBUTION-GATE-BYPASS (new: any grade-emitting
change that reached a gate packet without its live simulation attached).

## 6. CAMPAIGN C — ABHYĀSA (ongoing, daylight-paced)

L6 LEL→event_class resolver on the entity contract + per-class lel_category (ambiguities →
native; feeds scoring only) · power program: LEL expansion mapping more of the 63 events as
classes gain priors/rubrics, Tier-2 charts with consent + outcomes · promise-scoreboard
cadence + first calibration review · N_e Tranche-N stays a native-commissioned research
program (spec stands).

## 7. Success dashboard (all R16 detector-cited)

| Metric | Before | Gate |
|---|---|---|
| Independent graha maps (Py/TS) | 13 / 6 | 1 / 1 |
| Divergent TS domain vocabularies | 4 live + dead mirror | 0; mirror live |
| ref_entity_resolve('MAR') | fails | resolves |
| Identity-bearing facts parsed into Index | 0% | >99%, gaps explained |
| Factor→fact coverage (27 classes) | unknown | matrix complete, gaps dispositioned |
| condition_grade nonzero | impossible | live distribution |
| marriage vs separation evidence sets | identical ×3 versions | distinct, cited |
| Grade distribution | all-denied → all-promised | rubric spread, no monoculture |
| Promise scoreboard | does not exist | v0 published, all charts |
| Temporal measurement | #1 underpowered, #2 invalid | #3 published beside them |

## 8. Risk register

| Risk | Control |
|---|---|
| Adoption stalls again (modules built, call sites not migrated) | R17: acceptance by removal counts; census gates in CI |
| Index parser mis-parses silently | per-rule provenance + coverage report + PARĪKṢAKA vs live key inventory |
| Rubric weights drift toward known outcomes | R13 audit standard; weights cited before hand-worked examples are compared |
| Checkpoint becomes a bottleneck | scoped to 2 artifacts + named questions; single daytime session |
| Consumer breakage from new grade scale | B4 audit in-campaign; three-tier gates before deploy |
| Rebuild failures recur | M0 failure-classification discipline; sequential; supervised polling |
| Everything-promised or everything-denied returns | bounded rubric (R18) + monoculture assertion at all three tiers |

## 9. Timeline (indicative)

Night 1 (A) → Night 2 (A finish, if needed) → Daytime CHECKPOINT → Night 3 (B) → Night 4
(B finish: rebuild + measurements) → C ongoing. Each campaign PARKED-HONEST rather than
stretched; the same kickoff re-pastes to continue.

---

## 10. THE PROOF LADDER (ratified addition, 2026-08-08 — native directive)

**Principle:** after every meaningful stage, ONE end-to-end probe proves the COMPOSITION of
everything built so far, on LIVE data, against a known-answer question — before the next
stage begins. A component's own tests prove the component; only composition probes prove the
system. Every probe is a permanent repo script under `platform/scripts/probes/` (reusable as
regression gates forever), run by the Conductor at the rung and re-run by PARĪKṢAKA at
acceptance. **A lane's merge does not close its rung; the rung closes when its probe is green
on live data. The next stage does not open until the previous rung is closed.** Probe results
(actual output, not summaries) are pasted into the ledger, R16-scoped.

| Rung | After | Probe (live data, known answers) | Green means |
|---|---|---|---|
| P1 | A2+A3 (SSoT + registry) | **Identity round-trip**: for all 9 grahas + LAGNA: `norm_graha('Mars')=='MAR'` == TS `grahaCodeOf` == `ref_entity_resolve('MAR')` → same canonical entity; same for 3 sample houses, 5 vargas, 5 event classes | The identity contract is one contract, both languages, code↔registry |
| P2 | A5 (Fact Identity Index) | **The tracer bullet**: using ONLY Index+chart_facts joins, answer on 482012f1 live: occupants of H7 (D1)? VEN's D9 sign? 7th lord and its house? — cross-checked for internal consistency against `chart_divisionals` direct queries (no-JH-parity rail respected: internal consistency, not external oracle) | The Index turns the substring swamp into correct structural answers |
| P3 | A8 (checkpoint artifacts) | **Hand-worked rubric on live facts**: marriage/separation/childbirth scored BY HAND from P2-retrieved facts — the numbers the checkpoint reviews ARE this probe's output | The future engine's logic produces astrology-shaped numbers before any engine exists |
| P4 | B1 (Reader) | **Reader ≡ tracer**: Reader API answers == P2's answers exactly, plus non-empty fact_id provenance per answer | The Reader is a faithful refactor, not a new source of truth |
| P5 | B2 (engine as library, BEFORE writer plumbing) | **Offline full-grade table**: engine run as a library against live 482012f1 + 1c826d5a → all 27 classes × grades printed; assertions: no monoculture · no saturation · marriage≠separation with distinct evidence · condition>0 somewhere · agreement with P3 hand-worked values within stated tolerance | The engine is correct BEFORE it touches the orchestrator |
| P6 | B2 wired into writer | **Plumbing fidelity**: one orchestrated bo_pratijna run, one chart → DB rows byte-agree with P5's offline table | Integration changed nothing semantically |
| P7 | B4 (consumer audit) | **One-consumer pull-through**: ph_nimitta posterior + mi_darshana sentence regenerated for ONE class on one chart → promise_lift and prose reflect v4 semantics correctly | Downstream reads the new meaning, not the old shape |
| P8 | B5 chart 1 only | **Single-chart full acceptance** on 482012f1 (zero errors, Mahā-Brief spot-read, field regenerated) BEFORE charts 2–3 are attempted | The rebuild recipe works once before it runs thrice |
| P9 | B6/B7 | Measurement tripwires already specced (degenerate-interval stop; scoreboard derivation links resolve) | The measurements measure |

**Cost honesty:** the ladder adds serial probe time between stages (~minutes each; P5/P8 tens
of minutes). It removes the failure mode that has cost three full campaign-nights of rework.
Probes are read-only or single-writer-scoped; none risk production state.

**Failure protocol:** a red probe STOPS the ladder — diagnose at that rung, where the defect
is at most one stage old and its location is unambiguous. This is the entire point: v3's
epsilon-zero defect would have been caught at P5, one night early, in one file.
