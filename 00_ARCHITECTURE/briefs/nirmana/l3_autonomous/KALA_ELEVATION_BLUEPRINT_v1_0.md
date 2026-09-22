---
artifact: KALA_ELEVATION_BLUEPRINT
canonical_id: KALA_ELEVATION_BLUEPRINT
version: "2.2"
status: PROPOSED_FOR_NATIVE_RULING
date: 2026-09-22
position: >
  The operating blueprint for elevating the Kāla (L3) layer, written UNDER the adopted authorities
  — Product Definition v3.0 (CCD-010), Data-Plane Value Architecture v2.0 (DP-SD-009), the
  Foundation Contract F01–F28, the L3 Kāla Strategy and Execution Brief (DP-SD-017) with its
  amendments (DP-SD-018/019/020/021), the accepted W0 records, and the project-adopted
  autonomous-asset-elevation skill. It integrates what has been MEASURED since those were written
  (the readiness arc, the first real build, the critical review) into one execution-shaped view.
  It supersedes nothing. Where it and an adopted authority differ, the authority wins and this
  document is wrong.
does_not_authorize: any build, migration, grant, evidence event, deployment or code change.
changelog:
  - "2.2 (2026-09-23): §11.15 — the BPHS Ch.29 strike propagates: 39 of 41 vedha-bearing transit rules cite that non-existent gochara chapter, the other 2 cite Phaladīpikā which is not in the admitted corpus, so ZERO vedha rules are corpus-verifiable and the layer has no source-qualified ordinary reference today. Added to §9 as D8."
  - "2.1 (2026-09-23): §11.14 — three defects from the Kshetra packet, all verified here: a wrong classical citation inside an INDEPENDENTLY ACCEPTED W0 record; a coverage gap declaring a table absent that holds 8 live rows; and the stored field being chart-wide where its contract says route-scoped."
  - "2.0 (2026-09-23): §9 rewritten as the native's actual decision queue — it predated every finding of 23 Sep. Adds D6 (node frame + its paired disposition + the two sibling conventions), D7 (M-3 producer shape and owner), and the two items that are cheap and unblock others. The 65.3″ bound is now reproduced by three sessions independently."
  - "1.9 (2026-09-23): the Moshier node bound is 65.3″ over the full 55,152-knot domain — both earlier sparse samples under-reported it (mine by half). Natal-pāda safety is 2.7×, not 'well under'. New rule: a sample is not a bound."
  - "1.8 (2026-09-23): the 14.82″ method gap IS nutation in longitude — verified identical; so the three sessions' figures were one value under two ayanāṃśa conventions, both giving pāda 4. Moshier's true-node error measured at ≤32.5″ (1950–2100), retiring 'unbounded' — and that bound is what makes the natal pāda reportable and the stored-knot pāda not. §11.7 gains two counterexamples."
  - "1.7 (2026-09-23): natal figures corrected by 14.82″ — my manual tropical−ayanāṃśa subtraction disagrees with FLG_SIDEREAL, and L1's stored RAH_MEAN arbitrates for the latter. A THIRD undeclared convention (ayanāṃśa application method). §11.10 refined: the epoch is declared correctly in code, never in the data, and the fix extends the row's existing ayanamsha_id pattern."
  - "1.6 (2026-09-23): §11.9 RETRACTED IN FULL — the 332″ was my own epoch error (knots are noon UT; I differenced against midnight). With set_ephe_path and noon, real Swiss reproduces the stored knots to 0.00″ on 5/5 dates, so store-is-TRUE is EXACT. The pāda claim is RESTORED as measured: natal TRUE 50.0451 = pāda 4, MEAN 49.0289 = pāda 3. New §11.10 records the undeclared epoch convention."
  - "1.5 (2026-09-23): §11.1 — two sessions' local node computations diverge by 332 arcsec, larger than every margin in dispute and enough to flip the natal pāda between pāda 4 and pāda 3. The withdrawal is upheld on stronger grounds; a peer's proposed arithmetic correction is NOT adopted because its figure does not reproduce here. New §11.9 makes local-ephemeris irreproducibility a first-class finding."
  - "1.4 (2026-09-23): §11 — bg_cohort CONFIRMED as a fifth independent TRUE_NODE declaration (my earlier denial was a truncated grep); the directed-aspect item withdrawn — the engine is correct and the gap is a Saṅgam call-site; §3.1 Gochara row corrected (contacts partially kept, qualification absent); new §11.7 gate rule: a Swiss-vs-kernel gate is not a detector where .se1 is absent."
  - "1.3 (2026-09-23): §11 — the pāda-boundary claim is WITHDRAWN as unresolvable on this host (stored value sits 0.0059° from the boundary; local Moshier error ~0.1°); the three node figures in circulation reconciled; the stale KSHETRA brief on main flagged."
  - "1.2 (2026-09-23): §11 rewritten after three-session convergence — the node split is FOUR-way and `ephemeris_daily` stores TRUE node under a mean contract (measured 5/5 dates); the DAR_CLOSE receipt records the mean value the table does not hold; M-3 carries two producer paths and neither unblocks E1/E3 yet; two of this session's own v1.1 claims corrected."
  - "1.1 (2026-09-23): §11 addendum — the node-convention hub defect (mean-node natal vs true-node transit engine; reached and served: 232 rows in the served Gochara generation), the M-3 producer-owner decision the Saṅgam FINAL packet raises, and the shared-branch rule. Body unchanged."
  - "1.0 (2026-09-22): first issue."
---

# Kāla elevation blueprint

**The goal, in the native's words:** a highly enriched, elevated Kāla layer, every asset elevated,
each asset's individuality protected, the assets synergizing to produce the best value for the
user — whose experience is the primary goal — on an environment set up so that both consulting the
layer and building a chart into it are seamless.

**The measure of success, in the product's words:** *"I understand something consequential that I
could not see before. I see the connected basis, the alternatives, the timing where support
permits, and what remains uncertain. I can challenge it, revisit it and tell whether the product
was wrong"* (Product §1). Kāla's share of that is temporal discrimination: *"which enduring
structures are engaged, how and when"* (§3.10).

---

## §1 — The two experiences that define success

Everything below serves two people-facing experiences. Neither is "the asset builds."

### 1.1 Consulting Kāla

Product §9 names the experiences; four are Kāla's:
- **Experience 4 — the temporal landscape.** *"Distinguish enduring structure, active mechanisms,
  overlapping windows, recurrence and possible manifestations. Move between a life chapter and a
  narrow interval without changing evidential identity."*
- **Experience 5 — thoughtful choice comparison.** Nearest vs stronger *"under a named criterion"*
  (§7.1); *"'strongest' is not an unexplained scalar."*
- **Experience 7 — truthful forecast review.** The frozen claim, fit and misfit, no retrospective
  repair.
- **Experience 1 — first encounter.** *"Ask a real question and see what this chart can answer
  now"* — which requires availability signals with detectors behind them (§10.2).

The acceptance baseline is the Strategy's thirteen consumer obligations **L3-Q01–Q13**, frozen
by the Phase 0 session in `KALA_BASELINE_v1_0.md` with today's answers recorded, plus Product
§14's three proving cases and one **ordinary period** — because §9 requires the experience to work
*"for ordinary charts and ordinary periods, not only dramatic named yogas."*

What "elevated" means to the person, concretely, under the native's ruling that assets need not
agree and the LLM reconciles in context: **every reading arrives typed** — which kind of claim
(F04), which methods applied / were inapplicable / found nothing / never ran (F06), which
evidence roots and which independence group (Strategy §3 *Temporal testimony*), whether two
quantities are even comparable (L3-Q05). Three witnesses are distinguishable from one echo. A
"no window" carries its searched horizon, resolution and method coverage (*Search coverage*
object). Chapter → interval keeps the same evidence identities. **No single confidence scalar
stands in for any of that** (Product §5.2). Today, measured: `dissent: []` is hardcoded in seven
served tools; independence is computed and inherited by nothing; hour grain dies at the layer's
front door. That is the distance to close.

### 1.2 Building a chart into Kāla

The person builds a chart through the cockpit. What exists (measured at source):
`POST /api/cockpit/runs` with `scope ∈ {global, layer, asset, asset_set}`; a Kāla-scoped build can
pull its upstream via `computeUpstreamClosure` (`plan.ts:241`); one active run per chart
(`build_runs_one_active_per_chart_idx`); protected assets refuse with *"protected — native override
required"*; progress via `/api/cockpit/sse` emitting `hello`, `run`, `asset`, `line`; the Atlas view
renders eight states — `pending, queued, building, lit, stale, error, incomplete, service_ok` — and
`rows_written`.

Against Product §1.2 (*"progress, cancellation, checkpoints and resumption make deep work
usable"*) and §10.2 (*"availability badges, completion indicators and quality claims need detectors
for the exact claims they make"*), the measured gaps:

| Gap | Evidence | Obligation |
|---|---|---|
| **No cancel, pause or resume** in the runs route | grep of `runs/route.ts` for cancel/pause/resume: empty | §1.2 — a first build of unknown duration (registry claims 24 min; `ka_kshetra` alone measures ~7.5 h) with no way to stop it |
| **No substep-level progress or ETA** | SSE emits only run/asset/line; `build_substep_progress` is read by the watchdog, not streamed | §1.2; the orchestrator already heartbeats substeps — stream them |
| **`rows_written` is shown and is unearned** | `asset_throughput` claims 335,403 for `ka_kalasutra` while the table holds 0 | §10.2 / §N.8 — the badge must come from `count_sql` (cockpit truth) or a generation receipt, never the throughput row |
| **`lit` shown as if complete** | Atlas maps `lit` to done; `lit` = rows present, not accepted | skill profile: *"a row being present or `asset_throughput.state='lit'` is not campaign acceptance"* |
| **No cost visibility** | no per-asset measured cost surfaced; `estimated_seconds` is fiction | F22 "cost visibility"; the Phase 0 cost profile is the source |
| **No honest "cannot build" state** | `ka_kshetra` cannot build (unguarded `phala_rectification` read); four assets sit in `error` with no user-facing reason | §10.2 *"a failure must identify what was and was not established"* |
| **Availability truth for consulting** | five core tables empty for the canonical chart; nothing tells the person Kāla is empty vs Kāla has nothing to say | §10.2; the first-encounter experience |

These are **W0/W1 packets** (§6), owned by the cockpit's owner, not by asset briefs — but every
asset brief must supply what they need: a detector-backed state, a measured cost, an honest
failure reason, and a generation identity the badge can cite.

---

## §2 — Kāla in the six-layer plane: each layer alone, and with Kāla

Every layer has one responsibility (F01) and the value path runs through all six (F02:
*question → concept → rule → fact → structural relationship → temporal mechanism → manifestation
or explicit gap → delivered finding → protected evaluation*). Kāla is the sixth step. What it
receives and owes, with the seams **measured** in this arc:

| Layer | Its own role (VA §6) | Kāla receives | Kāla owes | Measured seam hazards |
|---|---|---|---|---|
| **L0 Brahmagyan** `bg_*` | *"A shared language that can be applied"* — sources, qualified rules, constants, event ontology, the astronomy substrate | `ephemeris_daily` (825,084 rows, 1900–2150) as the *shared global astronomy* (Strategy §5); `bg_transit_rules`, resonance rule capital, `bg_ghatana`, Kota rings, vedha scales | Source-qualification requests where a method is unqualified (e.g. tithi-praveśa `not_in_corpus`; Sarvatobhadra approximation) — DP02 | 22 L0 ancestors frozen only under superseded definitions; none never frozen (R1) |
| **L1 Gaṇita** `ga_*` | *"The reproducible chart, not a bag of placements"* — facts, clocks, conditions, divisions | `chart_facts` (by `fact_id`, F27), `chart_dashas` with `start_iso/end_iso` and `sandhi_flag`, positions, strength, tājaka | Only references back — never a restated value (§N.5) | `date_resolver.py:349` reads `start_date/end_date`, discarding hour grain and sandhi that L1 already holds; `:473` `date.today()` |
| **L2 Bodha** `bo_*` | *"Turn facts into a coherent structural reading"* — mechanisms, signed multidomain relations, contradictions | `bodha_msr_signals` (seven producers), propositions, CGM, the accepted L2 slice `9a5f2f53…`; compiled by Yojaka into predicates | Nothing computational (no L3→L2 edge); Kāla is L2's temporalizer | Five `kala_*` tables `ON DELETE CASCADE` from MSR — already fired once (335,403 + 14,868 rows); 79 predicates dangle; signed multidomain collapses to one `domain` in Sangam and first-domain in the L4 reader; L2 must **publish generations** before W1 |
| **L3 Kāla** `ka_*` | *"Temporalize the same structure"* — applicable clocks, actual contacts, intervals, recurrence, trajectories, comparison, election | its own spine: Yojaka → Sangam → Kalasutra / Vighnakara → Darshana → Jivana / Bhavishya; its frontier; Kshetra's own S0–S8 | — | the seams of §3.3 |
| **L4 Phala** `ph_*` | *"From activation to a discriminating manifestation"* — SEALED | — | `kala_convergence`, `kala_obstruction`, `kala_activation_predicates` to `ph_nimitta`/`ph_pratikara`/`ph_muhurta`; DP09: *activity is not event probability* (U07) | Sealed ⇒ every Kāla change is a **compatibility constraint**; `ph_nimitta:159` reads only the primary domain of Yojaka's map; convergence deletion cascades into L4 via `phala_anchors`; **Kshetra reads `phala_rectification` upward** — contrary to Strategy §6.2 |
| **L5 Mīmāṃsā** `mi_*` | *"Challenge without contaminating the answer"* — frozen claims, evaluation, admitted artifacts | — | stable temporal identities and full consumed content to claim issuance (U10); `mi_bhara` reads `kala_field` | No admissible receipt for `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` (an enum, `evidence-command.ts:50-63`, not schema); knowledge-time must be pinned (F15) |
| **Serving** (Pūrṇa) | The two managed doors and the raw door (VA §8.3) | — | L3-U04/U11 interface packets; the **served-evidence sentinel test** is L3's (Brief §7) | `platform-mcp/src/tools/kala_views/*` is Pūrṇa's; `dissent: []` ×7; mortality exclusion wired into 2 of 9 tools; Sangam's discriminating tier stored, never served; `kala_field*` has no read path at all |

**How a layer works with Kāla, in one sentence each:** L0 supplies the rule and the sky; L1
supplies the exact fact and the exact clock; L2 supplies the *mechanism* — participants, signed
domains, conditions, cancellations; Kāla says *when that mechanism is engaged, by which clock and
contact, with what coverage and what independence*; L4 says what it may mean and what would
falsify it; L5 freezes the claim and later scores it; serving delivers all of it without losing the
decisive low-ranked field. Kāla never invents a fact (F27), never claims a probability (§5.2), never
reads L4 or L5 live (§6.2, F15).

---

## §3 — The value architecture: objects, owners, individuality, synergy

### 3.1 The objects Kāla emits, and who owns each

The Strategy §3 defines the logical objects of the layer. Each has an owning asset; the object
**is** the asset's individuality — the thing no other asset produces.

| Strategy §3 object | Owning asset(s) | State today (measured) |
|---|---|---|
| **Contact** — moving body, target, contact type, orb, applying/separating, station/retrograde, brackets, tolerance, coverage | Gochara family (`ka_gochara`, century, resonance, vedha, moorti) | Partial. `term_breakdown.activity_terms` keeps 25,518 contact records over 380 of 914 served rows, but its only keys are `primitive, transit_planet, target_ref, target_weight, event_datetime_ist, orb_decay, p_i` — **no orb in degrees, no applying/separating, no station/retrograde branch, no bracket or root time, no tolerance, no coverage**, and no record at all on the other 534 rows. The contact is kept; its **qualification** is discarded. |
| **Clock interval** — method, hierarchy, parent, lord, exact start/end, inclusivity, applicability, failure reason | `ka_dasha_kala` (service), `ka_avadhi`, `ka_tithi_pravesha`, `ka_sudarshana_varsha` | tithi-praveśa instants 5.5 h late in production; hour grain lost in `ka_temporal` |
| **Temporal testimony** — roots, method/family, polarity, applicability, support/opposition/silence, **independence group**, uncertainty | `ka_sangam` (+ `ka_vighnakara` for opposition) | independence as a SMALLINT count; roots only in JSONB; no silence, no applicability per method |
| **Engagement route** — binding + necessary/optional temporal clauses, satisfying/failed evidence, enablement/inhibition, alternatives | `ka_sangam`, `ka_kalasutra` | no route field; score cut is a mode filter |
| **Interval / trajectory segment** — onset/peak/decay/recurrence, component witnesses, null states, resolution/error bounds | `ka_kshetra` (+ `ka_taranga`, `ka_kalasutra` recurrence) | the richest object in the layer; 85.7% synthetic baseline; no read path |
| **Search coverage** — requested/completed horizon, partitions, method scope, resolution, exclusions, unsearched regions, completion detector | every search asset | absent as a typed object; `max_windows=8` undisclosed; `LIMIT 750` undisclosed |
| **Comparison / election** — matched candidates, criteria, constraints, dominance, ties, reasons | `ka_tulana`, `ka_muhurta_seva` | `call_priority_ranking` bypasses Tulana; ranking = L2 salience × an orb NULL 99.6% of the time |
| **Publication handoff** — consumed values, versions, coverage, limitations, drills, bridge status | `ka_kala_darshana`, `ka_bhavishya_lekha` | Darshana's cut is a mode filter; Bhavishya 0 rows for the canonical chart |
| **Structural binding** — L2 identities, generation, digest; every participant/domain role, signed relation | `ka_yojaka`, `ka_gochara_resonance` | Yojaka's accepted repair (`7697c43b3`) restored signed/multidomain; consumers still flatten |

### 3.2 Individuality — protected by the object, not by the screen

Each of the 22 keeps the object it owns and the kernel that computes it. VA §10.2: *"Do not delete
an asset because it lacks a current screen or because its name resembles another."* Legitimate
variants stay as **named alternatives** with applicability (sudarśana's three frames are three
testimonies of one root, not three witnesses — A10). Services earn service proof, not invented
rows (A01–A04). The retired sweep is a protected tombstone (H01). An asset's disposition is chosen
at the *component* level — preserve / integrate / enrich-correct / qualify-limit / investigate-
consolidation / historical / retire-after-migration / unresolved-use (Layer contract §6) — never
"keep or delete the asset."

### 3.3 Synergy — the five layer contracts that make individual assets compose

Synergy is not harmonization (dropped by the native; contrary to L3-Q05 *"without a forced
consensus"*). It is the set of contracts that let a reconciling LLM line up, weigh and challenge
readings that legitimately differ. These are **layer-owned packets** (one owner each, W1), not
per-asset work — an asset elevated in isolation that leaves these seams unchanged has not been
elevated synergistically.

1. **The temporal contract** — one interval type, an explicit boundary convention, timezone-
   explicit instants, no `date.today()`, no naive datetime into `timestamptz`, hour grain and
   sandhi preserved from L1. Seam: `services/ka_temporal/date_resolver.py`, already imported by
   five writers — fix once, five inherit. Kills the 5.5-hour defect class.
2. **Typed qualification** — every emitted claim bound to F04 (epistemic class), F06 (per-method
   completeness state), F12 (operator role), the Temporal-testimony independence group, and a
   **comparability flag**. No new scalar. Extends `tier_basis='relative_uncalibrated'`, which the
   layer already stamps honestly.
3. **Co-reference** — the same window and the same structure are addressable across assets, so
   readings can be lined up before they are weighed. The interval type (1) plus stable structural
   identity from Yojaka (DP06 ancestry) supply it.
4. **Inherited independence** — `independent_current_count` becomes a group that *downstream
   inherits* (U02: *"declared lineage groups are bookkeeping, not demonstrated statistical
   independence; another representation of the same origin adds no independent support"*). Today
   zero `ka_*` consumers read it.
5. **Coverage on every result** — the Search-coverage object accompanies every window and every
   no-window, so *"a window just outside a searched partition must not become a universal denial"*
   (L3-Q08).

Plus the **determinism gate** that makes the native's "wipe and rebuild" stance safe: same pinned
dependency vector → same bytes, checked in CI. Today it is violated by `date.today()` and by the
naive-timezone persistence.

### 3.4 Where the consumer questions are unowned

Mapping L3-Q01–Q13 onto §3.1 leaves two questions with **no owning asset**: cross-clock agreement/
disagreement as a first-class output (Q05), and provenance-aware de-correlation (the inverse of
Q02's *"shared-dependence accounting"*). VA §10.3 is explicit that a new capability begins as an
exact contract gap and *"no new writer is assumed necessary."* Both are served by contracts 2 and 4
above once Sangam emits a group and downstream inherits it — the synergy capability, not a new
asset. If a brief concludes otherwise, that is a strategy amendment to raise, not a writer to
create.

---

## §4 — The 22-asset portfolio: how every asset fits

The shape decides how an asset is briefed and packeted (Template v2.0 §3). The wave decides when
its *data* may build (Execution Brief §5). The object decides what it must emit (§3.1). Stages 0–3
of every asset's plan are open **today**; stage 4+ waits on W1.

| Group / shape | Assets | Wave | What "fits seamlessly" means for them |
|---|---|---|---|
| **Frontier** (single, W2-eligible) | `ka_gochara_resonance`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`, `ka_yojaka`, `ka_avadhi` | W2 | Source **already accepted** for eight of these (`47131772b`; Yojaka's later repair `7697c43b3`). Their elevation is qualification (method/source), the temporal contract, and honest coverage. `ka_tithi_pravesha` is the path proof (0.61 s, fix the 5.5 h, source-qualify, freeze). Kota/Tithi/Sudarshana have no proven consumer — a *receiving operator* is owed (A07/A09/A10), not rows. |
| **Services** (single, service proof) | `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana` | W2 pure / W7 data-bound | Service semantics, failure semantics, consumer use — never row floors. `ka_dasha_kala` is the clock authority every interval inherits from; `ka_tulana` must actually be called by ranking (it is not). |
| **Gochara family** (group) | `ka_gochara`, `ka_gochara_v3_century_materialize`, + resonance/vedha/moorti | W3 (century on hold) | The **Contact object**; decide which member owns the served product (serving reads gen 3.0 via the authority pointer; `ka_gochara`'s 2.0 is unserved); the century disposition; fences 1–3; B1 closed first. Brief: `ELEVATION_PROMPT_GOCHARA_FAMILY_v2.md`. |
| **Spine — convergence** (single, chokepoint) | `ka_sangam` | W3 | Temporal testimony + Engagement route; mode-stratified output; inherited independence; June rulings honoured; bidirectional cascade. Brief: `ELEVATION_PROMPT_SANGAM_v2.md`. |
| **Spine — activation/obstruction** (single) | `ka_kalasutra`, `ka_vighnakara`, `ka_taranga` | W4 | All qualified recurrences (no default-eight); a single obstruction root that does not attenuate twice (U03); Taranga's transit term is dead in 91% of domain-scoped rows — qualify or repair. |
| **Spine — publication** (single) | `ka_kala_darshana`, `ka_jivana_parva`, `ka_bhavishya_lekha` | W5–W6 | Darshana's cut is a mode filter; Jivana's `LIMIT 1` unordered; Bhavishya needs its stable-generation packet before rebuild (fence 7; U10). |
| **Kshetra** (staged internal DAG) | `ka_kshetra` (15 tables) | W2–W7 by stage | The Interval/trajectory object; frozen stage plan; qualify the synthetic null; give it a read path; P0→P1/P2/P6 with equivalence; rectification as admitted artifact; populated replacement held until W7. Brief: `ELEVATION_PROMPT_KSHETRA_v2.md`. |
| **Protected retired** | `ka_gochara_sweep` | — | Tombstone; `generation='v1'` never rebuilt, never deleted; B1 exists because a live Clear path reaches it. |

The **critical path** is the spine — Yojaka → Sangam → Kalasutra/Vighnakara → Darshana → Jivana/
Bhavishya — not the frontier. Velocity comes from finishing Sangam's contract early, because seven
assets inherit it (`KALA_EXECUTION_DESIGN_v1_0.md`).

---

## §5 — The environment W0 establishes, and what we do not have

### 5.1 What W0 sets up (running now — the Phase 0/1 session, in its own `p1*` worktrees)

Baseline frozen on L3-Q01–Q13 + §14 + an ordinary period · cost measured on five profiles under
the Strategy §5 benchmark contract · the F12-operator overlay on the existing producer/use map ·
the five Phase-2 decisions prepared · real-DB P0 rehearsals (additive to the accepted fake-based
proofs) · B1 closed (registry truth, `is_active` on Clear, a real guard on `generation='v1'`) ·
three `bg_*` read grants, `phala_rectification` held · an explicit timeout on `data_plane_builder`
· the supervisor's progress detector fixed and an idle backoff added · session posture
(allow/deny scope; forced transcript persistence) · the Nirmāṇa campaign's `cascade_check.sql`
adopted · migration discipline across the two directories (one numeric sequence; L3 at
`platform/migrations/1071+`; `supabase/1035–1036` untouched).

### 5.2 What we already have — do not rebuild

`ephemeris_daily` (825,084 rows, 1900–2150) as the shared astronomy · Swiss `.se1` files with SHA
verification in **both** the serving and build images (`SWE_EPHE_PATH=/app/ephe`) · the 699-field
contract register · the frozen generation/publication/recovery design · accepted P0 · accepted W2
first-frontier source · the W0 benchmark harness (`validate_data_plane_l3_w0_baselines.py`) · the
DHARA numerical contract · `cascade_check.sql`, `egate.sql` (definition-scoped since #2706),
`capsule_audit.sql`, `nrec` · the redactor and disposable-harness pattern · the swarm runtime,
packet schemas and the Nirmāṇa campaign tracker (phase-first, four honest states) · the cockpit's
plan resolver with upstream closure.

### 5.3 The ecosystem gap register — what we lack that would make this simpler, easier, or possible

| # | Gap | Effect | Owner / route | Severity |
|---|---|---|---|---|
| G1 | **Physical L3 generation infrastructure** — design frozen (FOUNDATION_SAFETY §6), not built; zero L1/L2 generations ever opened | Nothing can reach `DATA_ACCEPTED`; cascade and determinism have no substrate | W1; native decision 1 = *release the hold* | BLOCKS stage 4+ |
| G2 | **Production cutover** — DP-SD-020: backup + isolated restore proven, cutover not executed | Holds RI-01 → W1 | administrator authority outside the campaign | BLOCKS W1 |
| G3 | **Disaster recovery** — PITR disabled; no restore drill ever run for `kala_*` | A mutating overnight campaign with no rehearsed way back | native ruling + one drill | BLOCKS unattended mutation |
| G4 | **Local harness fidelity** — the local host has no `.se1` files; the W0 baseline ran on Moshier while production is Swiss-backed | Local numbers are not production numbers; contact geometry differs at the arc-second level | ship the three `.se1` files (GCS bucket exists) into the disposable harness; pin and record | DEGRADES every benchmark |
| G5 | **No cost budget** per chart build; registry estimates are fiction (24 min claimed; ≥ 7.5 h measured) | Cannot promise the person a build time; cannot optimize | Phase 0 cost profile → a budget set *after* measurement (Strategy §5) | DEGRADES build UX |
| G6 | **No cancel / pause / resume; no substep progress; unearned `rows_written`** in the cockpit | §1.2 / §10.2 violated at the person's first touch | cockpit owner; W0/W1 packet (§1.2) | DEGRADES build UX |
| G7 | **No admissible receipts** for `CONSUMER_INTEGRATED` / `VALUE_EVALUATED` | Headline cannot move past `DATA_ACCEPTED` | native decision 2; a `z.enum` member + payload contract, no migration | BLOCKS the headline |
| G8 | **No retrieval capability over `kala_field*`** | The largest asset is unreadable by the product | Kshetra brief → L3-U11 packet → Pūrṇa | BLOCKS Kshetra value |
| G9 | **Unowned capabilities** — cross-clock disagreement; provenance-aware de-correlation | Two L3-Qs unanswerable | synergy contracts 2 + 4 (§3.3) | BLOCKS Q05 |
| G10 | **Source qualification** — tithi-praveśa `not_in_corpus`; Sarvatobhadra unqualified | Cannot reach `DATA_ACCEPTED` without it (F23) | native decision 4; source steward | BLOCKS those assets |
| G11 | **No determinism gate** (`date.today()`; naive-timezone persistence) | "Wipe and rebuild" is unsafe | temporal contract + CI build-twice-diff | BLOCKS rebuild-freely |
| G12 | **Serving is Pūrṇa's** — `kala_views` collides if L3 edits it; `dissent: []` ×7; mortality exclusion on 2 of 9 tools | The last inch fails silently; a binding-boundary gap on live surfaces | L3-U04/U11 interface packets + a priority request to Codex for the safety gap | DEGRADES / safety |
| G13 | **Independent-verifier capacity** — every packet needs a reviewer who is not its author | Builders certifying themselves | one verifier lane reserved per wave (Brief §4) | DEGRADES |
| G14 | **Native decision latency** — five gating decisions + Q1–Q8 | The campaign idles on rulings | the decision sheet with recommendations; rule in one sitting | DEGRADES |
| G15 | **Session isolation** — three brief sessions found writing into foreign worktrees; two drafts leaked to `main` | Shared-write collisions; unattributed publication | one worktree per session, enforced in every prompt | DEGRADES |
| G16 | **Layer-level tracker projection** — the campaign tracker is phase-first; no per-asset L3 lifecycle view per swarm §11 | The native cannot see, at a glance, each asset's state on both ladders | extend the tracker's projection; never `lit` as done; no % without a denominator | NICE-TO-HAVE → DEGRADES at W2+ |
| G17 | **Ordinary-period fixtures** absent | Product §9 untestable | Phase 0 baseline adds one; briefs add per asset | DEGRADES proof |

---

## §6 — The phased plan: W0 environment → W1 takeoff → W8 acceptance

Waves are the Strategy's (§6.4) and the Brief's (§5): eligibility groups, not equal batches. Each
wave names entry, packets, what runs in parallel, exit, and **what the person can now do**.

### W0 — Environment, safety, truth (RUNNING)
**Entry:** DP-SD-017 + W0 records accepted. **Packets:** §5.1, plus the build-UX packets of §1.2
where they are environment (badge truth from `count_sql`/receipts; honest `error` reasons; cost
surfaced). **Parallel:** the three hard-asset briefs (stages 0–2) and the twelve June-brief
reconciliations (Template v2.0) — all in their own worktrees. **Exit:** `KALA_PHASE01_CLOSE_v1_0.md`;
the five decisions ruled; B1 closed; harness carries `.se1` files (G4). **The person can now:** see
honest asset states and a real cost, and cannot delete the protected snapshot by accident.

### W1 — Takeoff: physical upstream truth, plus everything that does not need it
**Entry:** cutover (G2) → RI-01 released → W1 lease. **Packets (held):** materialize/select
L0→L1→L2 in the actual DAG; verify every contributing partition and rich field; L2 **publishes** a
generation; the 79 dangling predicates resolve; L3 head tables (G1) per the frozen design.
**Packets (open now, in parallel):** the five synergy contracts of §3.3 as shared-owner source
packets — temporal contract (`ka_temporal`), typed qualification (a shared emitter + F04/F06/F12
binding), co-reference, inherited independence (Sangam's group field + consumer readers),
coverage object; the determinism gate in CI; the ruled briefs' **stage-3 source packets** for the
three hard assets; the eight frontier source packets already accepted — extend with method
qualification; the interface packets to Pūrṇa (U04/U11) with L3-owned sentinel tests; the
build-UX packets (cancel/pause/resume; substep SSE). **Exit:** accepted immutable dependency
vectors; `PRODUCER_READY` for every W2-eligible asset; contracts 1–5 merged. **The person can
now:** nothing new is served yet — but a build can be stopped, watched at substep grain, and its
badge is true.

### W2 — Frontier data and independent preparation
Resonance; Moorti/Kota/Vedha/Tithi/Sudarshana; Yojaka; Avadhi; the four service proofs; Kshetra
S0 and S2. **Exit:** per-asset `DATA_ACCEPTED` on the accepted vector; each frontier asset bound to
a receiving operator or an explicit *unresolved-use*. **Person:** first typed, coverage-bearing
clock intervals reach `kala_now_get` — with honest "not built" where not built.

### W3 — Temporal search
Gochara v2 (the served-product owner decided); century v3 only after its hold and the
materialization-vs-substrate decision; Sangam on accepted Yojaka + services, emitting mode-
stratified testimony with independence groups; Kshetra S3. **Exit:** full applicable predicate
coverage; exact interval identities; `kala_convergence` bound to an L2 generation both ways.
**Person:** Q02/Q04/Q05 answerable with three witnesses distinguishable from one echo.

### W4 — Activation, obstruction, time series
Kalasutra (all recurrences); Vighnakara (single obstruction root); Taranga (transit term
qualified); Kshetra S1. **Exit:** complete recurrence/opposition proofs; no hidden truncation.
**Person:** "when does this recur" and "what opposes it" carry coverage and roots.

### W5 — Qualified view and field
Darshana (route + coverage, no mode filter); Kshetra S4 with direct S0. **Person:** the temporal
landscape (Experience 4) — chapter → interval with unchanged evidence identity.

### W6 — Chapters, projection, field windows
Jivana Parva; Bhavishya after its stable-generation packet (fence 7; U10); Kshetra S5 with the
null qualified. **Person:** Experience 7 — a forecast that can later be held to account.

### W7 — Coherent layer publication
Kshetra S6 → S6.5 → S8 → complete snapshot; accepted-data Tulana/Muhurta; the atomic layer
manifest; selective invalidation and rollback proven. **Exit:** `LAYER_DATA_ACCEPTED` — every
required active capability accepted; the retired sweep untouched. **Person:** a complete Kāla for
a chart, rebuildable deterministically.

### W8 — Receiving operators and value
L3 retrieval/view adapters and the U01–U11 packets land in Pūrṇa's door; the served-evidence
sentinel passes through budget, ranking, replay; the simpler-baseline comparisons on the frozen
L3-Q baseline; the four §9 experiences walked, including the ordinary period. **Exit:**
`CONSUMER_INTEGRATED` → `DEPLOYED_ACCEPTED` → `VALUE_EVALUATED` where receipts exist (G7); t3
`asset_frozen` under the frozen definition; the headline. **Person:** the promise of §1.

---

## §7 — Execution machinery: how it runs unattended

Reuse the adopted skill's runtime; adapt, do not rebuild (skill: *"do not create a second control
plane"*).

- **Roles:** one conductor; a Native Surrogate for charter-scoped ambiguity (never for the five
  decisions or Q1–Q8 — those are the native's); implementers in isolated worktrees; an
  **independent verifier** who never authored what it verifies; a release lane. Only the verifier
  emits `INDEPENDENTLY_VERIFIED`/`FROZEN` (runtime schemas).
- **Scheduler:** the ready frontier of the open wave; ownership written before mutation; scored by
  correctness risk → critical path → downstream unlock → duration; *"never opens the next layer to
  avoid idleness."*
- **Worktrees:** one per lane, named for its packet, based on `origin/main`; the shared checkout is
  read-only; nothing lives only in a worktree; content presence verified on `main`, never SHA
  ancestry (four instances this session).
- **Cycle contract:** foreground subagents in one message per wave; commit per wave; a cycle is
  complete only with a pushed commit and a rewritten state file; honest stop beats invented
  activity; two identical retries maximum; the supervisor's progress detector counts commits and
  state changes, not file touches.
- **Anti-idle:** the graduated response (refresh → nudge → reconcile → replace → root-cause →
  surrogate → dispatch another critical-path task); merge-queue waits and CI are monitoring
  states, not blockers.
- **Release:** DAG-safe micro-batches through the merge queue; a queued PR locks its branch (push
  elsewhere, don't force); migrations at `platform/migrations/1071+`, both directories checked.
- **Coordination with the other campaigns:** Pūrṇa/Codex owns serving and its PRs — interface
  packets, never edits; the L2 campaign is live — cascade coordination via its own tool and a
  build-order rule until generations exist; the DP-SD-021 platform split stands.
- **Credentials:** never echoed; the redactor before every commit; no rotation (native's decision);
  `WATCHDOG_SECRET` untouched.
- **Tracker:** a deterministic projection of accepted events and live systems — denominator and
  definition, accepted/remaining, wave and ready frontier, each asset on **both** ladders, owners
  and legitimate waits, blockers with exact unblock conditions, main/deployed/production sync;
  *"never `lit` as completion; no percentage when the denominator is unknown."*

---

## §8 — Proof, acceptance, and the headline

Two ladders, both declared per asset (Template v2.0 §0): the data-plane states (Strategy §7) and
the t3 lifecycle events. F13 evidence maturity and F14 delivery are separate; a green test cannot
skip a state; the §8 gate matrix says what each state *may not be claimed from*. Three proof tiers
stay separate (F24). The required proof set is F23 and the Layer contract §9's thirteen tests —
the served-evidence sentinel among them, owned by L3 even though serving is not.

**The headline is two numbers, never one:** `Delivered N/22` (the full target — 0 until G7's
receipts exist) and `Data-accepted N/22`. Both printed on every report, `Delivered` first. Assets
accepted count only under the frozen definition `t3-2026-09-11-8b884eac`.

**What proves the layer is elevated:** the frozen baseline (`KALA_BASELINE_v1_0.md`) re-run after
each wave — same thirteen questions, same three proving cases, same ordinary period — with the
added distinction named, the ablation run, the added error and burden counted (Product §14,
F03). Not row counts. Not agreement counts. Not longer prose.

---

## §9 — Decisions, holds, risks

Rewritten at v2.0: the original predated every finding of 23 September. Ordered by what each
unblocks, not by when it was raised.

### 9.1 The native's decision queue

| # | Decision | Unblocks | Recommendation |
|---|---|---|---|
| **D6** | **Node frame** — mean or true — **and its paired disposition** (§11.2): (a) rebuild `ephemeris_daily` mean, (b) keep true knots and derive mean at read with the disagreement declared per row, (c) mixed-frame per consumer. Rule the **two sibling conventions with it**: the undeclared **epoch** and the undeclared **ayanāṃśa application method** (§11.10–11.12). | Every Kāla rebuild; three critical assets; an L0 repair | Mean frame (it is what L1 stores, F27); **(b)** for the disposition — it never consumes the knot, so it is immune to the §11.13 knife edge; and declare all three conventions on the row, extending the `ayanamsha_id` pattern the table already has |
| **D1** | Release the W1 hold under the frozen generation design | Stage 4+ for all 22 assets | Yes — the design is already accepted at W0; this releases a hold, it does not adopt a design |
| **D7** | **M-3** — the directed contact-event producer: **shape** (Path A, a bounded `transit_search` amendment; or Path B, the Gochara kernel) **and owner** (§11.3) | Saṅgam E1/E3 | Shape is yours; the owner must be named either way. Path B is gated on that brief's own N-5/N-7, so E1/E3 is not unblocked by a proposal |
| **D2** | Receipts for `CONSUMER_INTEGRATED` / `VALUE_EVALUATED` | The headline metric past `DATA_ACCEPTED` | Add the enum member; **no migration needed** |
| **D3** | The three protected classes | Safe rebuild semantics | Confirm: sweep snapshot, issued claims/observations, retained outcomes |
| **D8** | **Corpus admission** — admit Phaladīpikā (± Sārāvalī / Jātaka Pārijāta), or re-grade every gochara-vedha row as cited-outside-admitted-corpus (§11.15) | Any vedha reaching `applied` in **all three** consumers; the vedha half of transit qualification | Rule the uniform `corpus_verifiable` stamp either way — the three streams have already converged on the mechanism, so this is one ruling, not three |
| **D4** | Tithi-praveśa source qualification — **and note this is the path to the layer's FIRST source-qualified ordinary reference**, not one asset's paperwork (§11.15) | That asset's `DATA_ACCEPTED`; the layer's qualification story | Needs a source steward; its own citation reads `not_in_corpus` |
| **D5** | Baseline authority | Proof discipline | L3-Q01–Q13 + the §14 proving set + one ordinary period |

Plus Q1–Q8 of the elevation plan and each brief's own list. Full evidence and options:
`KALA_PHASE2_DECISIONS_v1_0.md`.

**Two items that are cheap and unblock others:** D2 (one enum member) and D3 (a confirmation).
Ruling those two costs little and removes a ceiling and a safety ambiguity from every other lane.

### 9.2 Holds (not decisions — they clear on evidence, not on a ruling)

W1 on the production cutover · century v3 on its BUILD-PROTECTED guard — **and note the guard may be
residue: the stored error predates migration 588's removal of it by two days, and there is currently
no database guard at all** (carried from the Gochara session, unverified here) · Kshetra populated
replacement until W7 · Bhavishya until its W6 packet · RI-01 on production-owner authority.

### 9.3 Risks

An L2 rebuild during the campaign empties five tables again (mitigation: build-order rule +
`cascade_check.sql` until W1) · Pūrṇa and L3 collide on `kala_views` (mitigation: interface packets
only) · decision latency idles the fleet (mitigation: recommendations attached; D2 and D3 are one
sitting) · every cost number is unmeasured until Phase 0.3 lands (mitigation: promise no schedule
before it) · **numerical gates built on unverified backends** — the §11.7 rule and the 65.3″ bound
exist because two sessions nearly anchored a gate on a figure 200× finer than its own reference.

**Resolved since v1.0:** the three brief sessions now work in their own worktrees. One residue: the
Kshetra session's **stale v1.0 brief is still on `main`** under this session's sweep (§11.5) — do not
cite that path until its v4.0 lands.

## §10 — What this blueprint does not establish

It does not establish any asset's Jyotish correctness (the elevation's own work); any cost beyond
the two measured; that the frozen generation design works physically (W1 will); that any
consumer-value distinction exists yet (`VALUE_EVALUATED` is N for all sixteen questions examined);
or that the five decisions will be ruled as recommended. It is the map. The territory is measured
one wave at a time.

---

## §11 — Addendum (v1.2, 2026-09-23): the node-convention split, and M-3

Opened by the Saṅgam session's FINAL packet, corrected and extended by the Gochara and Kshetra
sessions, and re-measured independently here. **Two claims in v1.1 of this section were wrong and
are corrected in §11.4.** Everything below is marked verified-here or carried-unverified.

### 11.1 The node convention is split FOUR ways, and the store disagrees with its own contract

| Surface | Convention | Evidence (verified here unless marked) |
|---|---|---|
| **L1 natal facts** (`ga_positions`) | **MEAN** | `pyjhora_adapter/positions.py:21-22` `_USE_TRUE_NODES = False`, "classical convention"; `:61` passes it. Three further declarations reported by the Gochara session (`vargas.py:21,65`; `_jhora.py:23-55` patching `drik.sidereal_longitude` to `MEAN_NODE`) — *carried, not re-verified here*. |
| **L0 `ephemeris_daily`** (`bg_ephemeris`) | **TRUE — under a "mean" contract** | `brahmagyan/l0_ephemeris.py:77` `{"name":"Rahu","swe_id":11}` commented *"Mean North Node"*; `:289` `swe.calc_ut(jd, 11, ...)`; docstring `:8` "Rahu (mean)". **`swe.MEAN_NODE = 10`, `swe.TRUE_NODE = 11`** — so id 11 is TRUE. Empirically decisive: stored tropical longitude matches Swiss TRUE on **5 of 5 sampled dates** (residual ≤ 0.10°) and MEAN on 0 of 5 (off by up to 1.47°). |
| **Transit engine** `pipeline/transit_search.py` | **TRUE** (correctly labelled) | `:10`, `:64` `"Rahu": 11, # swe.TRUE_NODE` |
| **Legacy `brahmagyan/ganita/l1_positions.py`** | **TRUE** | `:128` `("Rahu", swe.TRUE_NODE)`. Importers confirmed: `l1_dashas`, `l1_strength`, `l1_divisionals`, `l1_sensitive_points`, `l1_panchanga_birth`, `graha_sthana_writer`. **Whether each importer's persisted output actually diverges is UNVERIFIED** — a bounded L1 check, not a claim. |

**The store contradicts its own declared contract.** Migration
`624_nirmana_l0_ephemeris_probe_contract.sql:30` pins `"node_mode": "mean"`. The data is true node.
A contract with no detector that can falsify it is an unearned signal (§N.8) — here it stayed green
for a year over data it never checked.

**And the L0 closure receipt records a value the table does not hold.** `DAR_CLOSE_v1_0.md:20`:
*"ephemeris_daily: Rebuilt with MEAN_NODE Rahu/Ketu; Rahu at 1984-02-05 = 49.04° Taurus/Rohiṇī
(FORENSIC-verified delta 0.01°)."* Measured: stored tropical 73.629058 − ayanāṃśa 23.6349 =
**49.9941° sidereal**; Swiss MEAN for that instant = **49.0405°**. The receipt's 49.04 is *exactly*
the mean value — so it describes an intended computation, not the stored result, and its
"FORENSIC-verified" claim was never compared against the table. **Routed to L0's owner as a
receipt-vs-data discrepancy. No L3 session touches L0.**

**It IS visible in a reading, and the figure is measured.** At the birth instant (1984-02-05
05:13 UT, Lahiri, real Swiss — `retflag 258`, no Moshier bit):

| Convention | Sidereal | Rohiṇī pāda | Margin to the 50.0000° boundary |
|---|---|---|---|
| **MEAN** (analytic; what L1 stores) | 49.033044° | **3** | 3492″ |
| **TRUE** (what the store and the scanner carry) | 50.049248° | **4** | 177″ |

A mean-vs-true ruling therefore **moves this native's Rāhu from Rohiṇī pāda 3 to pāda 4** as a
measured fact. The 177″ margin is an order of magnitude above any plausible ephemeris-version
difference, and the mean figure reproduces L1's own served `RAH_MEAN` (49.0330441°) to **0.00″**.
Instant: 1984-02-05 05:13 UT (10:43 IST), `jd 2445735.717361`. A cited number carries its instant.

**And store-is-TRUE is exact, not statistical.** Computed at **noon UT** — the epoch
`l0_ephemeris.py:164,278` actually uses — with `set_ephe_path('/tmp/se1')`, real Swiss reproduces
the stored knot on **5 of 5 dates to 0.00 arcsec at six decimals**, while mean is 317–5380″ away.
There is no residual to caveat.

### 11.2 The ruling needs a paired disposition, not just a convention

"Rule mean node" is **not** a one-line hub repair, because the store itself is true. Whatever is
ruled, the native must also rule *where the repair lands*:

| Option | What it costs |
|---|---|
| **(a) Rebuild `ephemeris_daily` mean-node** | Matches the DAR receipt's own claim; touches a frozen layer and every downstream consumer of the knots. |
| **(b) Keep the knots TRUE; derive mean Rāhu/Ketu analytically at read time** | Cheap, no L0 rebuild, auditable against Swiss — but store and derivation then disagree by ~1° and that must be **declared per row**, never silent. Recommended by the Gochara session (its N-4a) and the Saṅgam session; **I concur.** |
| **(c) A declared mixed-frame contract per consumer** | Most honest about current reality, most surface area to police. |

Whichever is ruled, the paired obligations are: repair migration 624's probe so it *detects* rather
than declares; correct the `l0_ephemeris.py` comment and docstring; and decide the legacy
`l1_positions` chain separately. Riding with it: the **cusp frame** (L1 stores Placidus; the Saṅgam
plan assumed Śrīpati) — which the Kshetra session confirms does not touch Kshetra (whole-sign
arithmetic only, `writer.py:1783`).

### 11.3 M-3 — two producer paths, and E1/E3 is **not** unblocked by either yet

If the native re-affirms June §4.5 (no ephemeris scan inside Saṅgam; Saṅgam consumes pre-computed
directed contact events; `planet` as a list), a directed contact-event producer becomes an upstream
obligation. Two shapes are now on the table:

- **Path A — a bounded amendment to `transit_search.py`** under one named owner (frame/ayanāṃśa/node
  arguments; directed special-aspect search). Faster; **edits a frozen shared hub**.
- **Path B — a new pure module** (`services/gochara_kernel`), proposed in the Gochara brief v1.2:
  emits directed contact episodes natively (t_in / t_exact / t_out, bracket, tolerance, branch, orb
  + orb_source, plus a Search-coverage row per partition), with frame/ayanāṃśa/node as arguments by
  construction. Edits neither `transit_search.py` nor `ka_dasha_kala` (both in its `must_not_touch`).
  Saṅgam E1/E3 would bind to the kernel; Kshetra S0 could adopt it later without a second amendment.

**Path B's own caveat, stated by its author and carried verbatim:** the kernel becomes a shared hub
the moment two assets bind to it — *"the exact property that made `transit_search` hard to change"* —
so it must carry an additive-only signature rule and a versioned contract from day one. And it
**exists only if the native approves that brief's N-5 (served-product owner) and N-7 (persisted
Contact ledger), both unruled**. If N-7 is refused, the obligation reverts to Path A and still needs
an owner. **Therefore E1/E3 must not be recorded as unblocked by a proposal.**

**The owner is the native's to name.** All three sessions have declined to name it between
themselves — correctly. The native rules shape *and* owner together.

**Directed aspects — an earlier item in this section is WITHDRAWN.** v1.2 recorded a
"directed-aspect gap at the engine, unexercised in served data." Re-verified, none of that holds:
`find_aspect_events` computing `(target_longitude_deg + aspect_deg)` (`transit_search.py:320`) is
**correct** — dṛṣṭi is directional, and a symmetric search would be the defect. The Gochara path
already uses the classical per-graha table: `gochara_grammar/primitives.py:342-343` passes
`SPECIAL_DRISHTI_DEG.get(planet, _DEFAULT_DRISHTI_DEG)` into it (Mars `[90,180,210]`, Jupiter/Rāhu/
Ketu `[120,180,240]`, Saturn `[60,180,270]`, everything else `[180]`, BPHS Ch.26 cited at
`:189-196`). And it **is** exercised: `drishti_contact` appears on 379 of 914 served generation-3.0
rows. My "zero rows carry an asymmetric degree" was measuring `activity_terms`, whose keys are
`primitive, transit_planet, target_ref, target_weight, event_datetime_ist, orb_decay, p_i` — the raw
aspect degree is **not a field it has**. Absence in a field that cannot hold the value is not absence
of the value.

**The real defect is a Saṅgam call-site, not a producer gap:** `services/ka_sangam/engine.py:464-466`
passes the symmetric generic set `[0,60,90,120,180]` for the benefics Jupiter and Venus, where
Jupiter's classical dṛṣṭi is `[120,180,240]`. Attributing this to the Gochara producer would send
the fix to the wrong owner. It belongs in Saṅgam's R-series. (Found by the Gochara session; verified
here.)

### 11.4 Corrections to this session's own v1.1

1. **Kshetra is not a `transit_search` position reader.** v1.1 listed three readers. Verified:
   `services/ka_kshetra/stage0_kinematics.py` imports only the `MEAN_MOTIONS` constant (`:746`) for
   dwell normalisation — **zero** scan/search call-sites — and reads all nine bodies from
   `ephemeris_daily` through its own Hermite spline. Correct position readers of `transit_search`:
   **`ka_gochara/service.py` and `ka_sangam/engine.py`**. Kshetra is an `ephemeris_daily` reader —
   which, per §11.1, still makes it **contract-mean / store-true**, so it is affected, just at a
   different repair site. (Raised by the Kshetra session; its own "Kshetra is mean/mean" conclusion
   is withdrawn by the store measurement.)
2. **The "242 rows" figure was wrong.** It summed two generations and two carriers without a
   generation filter. Correct: **232 of 914** at `g3_utkarsha` via `term_breakdown`, **50 of 87** at
   generation 2.0 via `active_sentences`. Raised by the Gochara session; reconciled here.

### 11.5 The shared branch

`l3/kala-elevation-readiness` is by use the shared L3 documentation branch. Committed docs there are
fine, **staged by name only**; uncommitted work belongs in the authoring session's own worktree.
Verified: the Saṅgam commits swept zero foreign files. The Kshetra session's user has since ruled:
both artifacts moved to `/Users/Dev/madhav-l3/kshetra` on `l3/kshetra-elevation`, and the readiness
worktree is clean again.

**One consequence of this session's own error, flagged for anyone citing it.** `origin/main` carries
`briefs/KSHETRA_ELEVATION_BRIEF_v1_0.md` at that session's **stale v1.0**, swept there by this
session's `git add -A` in `bd1a12e03` (PR #2713). It contains three findings its author has since
withdrawn — including the "Kshetra is mean/mean, already conformant" conclusion that §11.1's store
measurement overturns. Until that session's v4.0 lands as an in-place update, **anyone reading that
path on `main` gets the withdrawn version.** Do not cite it. This is why the staged-by-name rule
exists.

### 11.6 Carried but NOT verified by this session

**`bg_cohort` is CONFIRMED, and my earlier denial was my own measurement error.** Re-grepped
without truncation: `@register("bg_cohort")` at `:470`, `("Rahu", swe.TRUE_NODE)` at `:333`, and the
provenance string *"Lahiri ayanamsha; TRUE_NODE Rahu"* at `:159`; 691 lines, byte-identical to
`origin/main`. My v1.2 statement that the file had neither came from a grep I had piped through
`head -5`, which truncated away everything after line 106 — I then published that absence as a
finding against a peer's correct claim. The peer's own correction also stands and *strengthens* the
finding: `bg_cohort` does **not** import `l1_positions` (`:49`, `:105-106` say it independently
reproduces the formulas), so it is a **fifth independent TRUE_NODE declaration**, not a dependent
one. · Per-importer persisted
divergence in the `l1_positions` chain. · The century BUILD-PROTECTED "residue" timeline (error
stamped 2026-08-21 vs migration 588 applied 2026-08-23). · The 1.933° maximum over 1984–2084. · **No natal Rāhu
`longitude_sidereal` fact row exists** for the canonical chart at `lahiri_chitrapaksha` — so L1's
mean convention is confirmed by declaration and by the DAR arithmetic, not by a stored fact.

### 11.7 A gate rule this week produced: a Swiss-vs-kernel comparison is not a detector here

Raised by the Gochara session, and it generalises the §11.1 caveat. This environment ships no `.se1`
files, so `FLG_SWIEPH` silently falls back to Moshier and returns bit-identical values to a Moshier
call. **Any acceptance gate phrased "our kernel agrees with Swiss to N arcseconds" therefore compares
Moshier with Moshier where `.se1` is absent — it cannot fail, and under §N.8 it is not a detector at
all.** Production does carry real Swiss data (`Dockerfile:24`, `Dockerfile.pipeline:17`,
sha256-verified into `/app/ephe`), so the gate is meaningful there and vacuous here.

**Both backend inferences failed here, in opposite directions.** "Two flags return identical values,
therefore Moshier" was right by luck. "No `.se1` found, therefore Moshier" was right by luck too —
the files existed and the path was simply never set. **Only `retflag` survives both**: read it and
test the MOSEPH bit. Provision and checksum your own `.se1` rather than assuming another session's
copy persists — the one on this host sits under `/tmp`, placed by another session, and may not
survive a reboot.

**Measured over the whole domain, so "unbounded Moshier error" is retired — and so are two sparse
samples of it.** Moshier's true-node error against Swiss, computed at **every** noon knot from
1950-01-01 to 2100-12-31 (**n = 55,152**, `retflag` asserted Swiss on every call): **min −58.1″, max
+65.3″, worst 65.3″ on 1972-11-20.** Two earlier sparse estimates both under-reported it in the same
direction — a five-date sample said 18.1″, my sixteen-date decade sample said 32.5″, the truth is
**65.3″**, half as much again as my figure and over three times the other. **Independently reproduced by three
sessions** — measured by the Gochara session, reproduced here and by the Saṅgam session, each to the
arcsecond and the date.

That bound is what separates a reportable figure from an unreportable one, with the real ratios:

| Quantity | Margin | vs the 65.3″ bound |
|---|---|---|
| Natal pāda (birth instant) | 177.3″ | **2.7× safety — reportable even on Moshier** |
| Stored noon knot | 6.3″ | **10.4× over — not reportable on any backend** |

2.7× is a real margin but a thin one; state it as 2.7×, not as "well under".

**New rule, earned the same way as the other two: a sparse sample is not a bound.** The node's error
oscillates on timescales shorter than a decade, so decade spacing samples it about as badly as five
dates do. Two sessions each produced a confident bound from a sample and both were wrong in the same
direction; only measuring the full domain settled it. This sits beside *"a date is not an epoch"* and
*"a flag is not a backend"*.

**Consequence for the inherited 0.314″ spline figure:** 65.3″ is two orders of magnitude above it.
If the W2G V3 validation ran without `set_ephe_path`, it compared its spline against a reference
~200× coarser than its own claim, and the figure says nothing about Swiss-grade accuracy. Whether
that runner calls `set_ephe_path` is answerable from source and should be answered before 0.314″
anchors any gate. (Raised by the Gochara session.)

**Rule for every numerical acceptance gate in this campaign:** require `.se1` present, verify
`retflag`, and record the file checksums in the evidence, or the result is `NOT_RUN` — never `PASS`. Any inherited
arcsecond-level parity figure whose run environment is not established is `[UNVERIFIED]` until it is.
This is the same defect class as migration 624's probe (§11.1): a check that cannot return false.

### 11.8 Four measurement errors by this session, and the pattern

Recorded because the pattern matters more than the individual slips. (1) v1.1 listed Kshetra as a
`transit_search` position reader — it imports one constant. (2) v1.1's "242 rows" conflated two
generations and two carriers. (3) v1.2 denied `@register`/`TRUE_NODE` in `bg_cohort` from a grep
truncated by `head -5`. (4) v1.2's directed-aspect gap measured a JSON field that cannot hold the
value. All four are the same failure: **asserting from an incomplete read, then publishing the
absence as evidence.** The three asset sessions caught all four. The countermeasure that actually
worked was not care — it was other sessions re-measuring at the authority and saying so.

### 11.9 RETRACTED IN FULL — there was no session disagreement; the 332″ was my own epoch error

v1.5 recorded that two sessions' node computations diverged by 332 arcsec, called it unexplained,
and reasoned the disagreement might invert the pāda finding. **All of that is withdrawn.** Both
peers independently found the cause; verified here:

- **`l0_ephemeris` stores every knot at NOON UT** (`:164` *"Julian Day Number (noon UT)"*, `:278`
  `swe.julday(..., 12.0)`). I differenced against **midnight**. Midnight − noon for the true node on
  that date is **+332.3″** — precisely the "disagreement" I reported. Both hosts agree bit-for-bit
  at the same epoch.
- **This host *does* carry `.se1`** at `/private/tmp/se1`, and the production resolver
  `brahmagyan.l0_ephemeris._resolve_ephe_path()` returns `/tmp/se1` — its own documented
  development/CI candidate. `swisseph` finds them only after `set_ephe_path()`; without that call
  `FLG_SWIEPH` silently returns `retflag 260` (Moshier bit set), with it `retflag 258` — real Swiss.
  My "Moshier fallback" was true of *my calls*, not of *this host*.

Everything v1.5 derived from the phantom divergence is void: the "(A′) peer-offset" row, the claim
that the pāda finding inverts, and "weak evidence my local node is the outlier." Neither session was
an outlier. **§11.7's rule survives with a better detector:** never infer the backend from flags
matching or from `.se1` appearing absent — **read `retflag` and test the MOSEPH bit**, the only
thing a silent fallback cannot fool.

### 11.10 The epoch convention is undeclared too — the other half of the §N.8 finding

`ephemeris_daily` carries neither the node frame nor the knot epoch on the row. The frame is
declared *wrongly* (migration 624 says `"mean"`; the data is true — §11.1). The epoch is not
declared **at all**. That undeclared epoch fooled two independent sessions on one day, produced a
332″ phantom finding that reached v1.5 of this document, and was caught only because a third session
re-derived it from the builder source.

Both belong in one repair: whatever is ruled on the node, `ephemeris_daily` should carry its
**frame and its epoch, each with a detector behind it**, and migration 624's probe should verify
both against the data rather than assert them. A spline built on the wrong epoch assumption is wrong
by half a day — W2G's own validation note puts that at ~6.6° for the Moon.

**One conflation to drop from every sheet, including this one:** the "0.0059° from the boundary"
figure belongs to the **stored noon knot** — a transit sample on the birth date, not the natal
position. It says nothing about the natal pāda, which comes from L1's birth-instant computation
(§11.1). Two different quantities; only the natal one bears on a reading. (Raised by the Kshetra
session.)

### 11.11 A third undeclared convention: how the ayanāṃśa is applied (14.82″)

Found while reconciling a 15″ spread between sessions that was assumed to be a birth-instant
difference. It is not — it is **method**:

| Getting sidereal from Swiss | MEAN at 05:13 UT | vs L1's stored `RAH_MEAN` |
|---|---|---|
| `tropical − get_ayanamsa_ut()` (manual subtraction) | 49.028927° | **off by 14.82″** |
| `FLG_SIDEREAL` (Swiss's own transform) | **49.033044°** | **0.00″** |

**The gap is nutation in longitude, exactly.** Nutation at that instant is **−14.82″**, and the
method gap is **−14.82″** — identical to two decimals. `get_ayanamsa_ut()` returns the *mean*
ayanāṃśa; `FLG_SIDEREAL` applies the *apparent* one, which includes nutation. So the three sessions'
figures were never three measurements — they were **one value under two conventions**, and the
convention split we spent the day documenting reproduced itself inside our own instruments. Both
conventions put Rāhu in pāda 4 (177″ and 162″ margins), so the conclusion is convention-independent.
(Closed by the Gochara session; verified here.)

**L1's stored fact is the arbiter, and it validates `FLG_SIDEREAL`.** My manual subtraction — used
for every sidereal figure this session published before v1.7 — is the one that disagrees with what
L1 actually serves. Both natal figures in §11.1 are corrected accordingly (mean 49.028927 →
49.033044; true 50.045130 → 50.049248; margin 163″ → 177″). The pāda conclusion is unchanged; the
method finding is the durable part.

So three conventions govern a single longitude and **none is recoverable from the data**: the node
frame (declared *wrongly* — §11.1), the epoch (declared correctly in code, never in the row —
§11.10), and now the ayanāṃśa application method (declared nowhere, worth 15″, and silently
divergent between two correct-looking call shapes). Each cost a session an error today.

### 11.12 §11.10 refined, and the fix is smaller than it looks

The Kshetra session's correction, adopted: *"declares neither"* was slightly too strong. Precisely —
**the node frame is declared wrongly in two places** (`624:30` `node_mode="mean"`;
`l0_ephemeris.py:77` comment "Mean North Node"), while **the epoch is declared correctly in exactly
one place a consumer never reads** (`l0_ephemeris.py:164,278`). A reader of `ephemeris_daily` can
recover neither: its columns are `id, date, body, ayanamsha_id, tropical_longitude, latitude,
speed_dps, is_retrograde, sign_number, degree_in_sign, nakshatra_number, source_citation,
computed_at`. `date` carries no time-of-day; `source_citation` is the constant string
*"pyswisseph + Swiss Ephemeris .se1"*.

**And the fix is not new machinery — it is this table's own established pattern.** The row already
carries `ayanamsha_id` (value: `tropical`) precisely to declare a frame. `node_mode`,
`epoch_convention` and the ayanāṃśa application method belong beside it, each with a detector, rather
than in a probe contract that asserts without measuring. §11.10 therefore reads as *"extend the
row's existing frame declaration to the three frames it omits"*, not *"add declaration machinery"* —
which should make it considerably easier to land. (Framing by the Kshetra session.)

**And the consumer cost, in one sentence** (madhav-d9's, adopted): because L1 stores no `RAH_TRUE`,
the true natal value is computed at read time and stored nowhere — so any consumer wanting it
recomputes it and silently inherits its caller's epoch, backend and ayanāṃśa method. Today that is
three ways to be wrong, none of them visible in the data.

### 11.13 The knot and the instant fall on opposite sides of the boundary

Measured on Swiss, the sharpest form of the whole episode: the **stored noon knot** for the birth
date is TRUE 49.998247° → **pāda 3**, while the **birth instant** is 50.049248° → **pāda 4**. Same
body, same day, same backend — opposite sides of a classical boundary, 6″ and 177″ from it
respectively.

That is the argument for a design rule the Gochara family had already reached independently: **solve
at the instant; a stored knot is an interpolation input, never an answer.** It is also why the
knife-edge finding must not be cited against the natal figure (§11.10): the knot's 6″ margin is
smaller than any backend's error, while the instant's 177″ margin is five times larger than the
measured 32.5″ worst case. One is reportable, the other never will be.

### 11.14 Three defects from the Kshetra packet — verified here, one of them governance-level

**(a) A wrong classical citation, carrying an acceptance stamp.** `MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md:207`
states the source-qualified reference is *"the BPHS Ch.29 Sun third-from-Moon favourable transit and
paired ninth-house Vedha case."* Checked in the corpus: **BPHS Volume 1 Chapter 29 is titled
"Bhava Padas"** (`00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt`),
and the whole of Volume 1 contains **2** occurrences of "gochara". There is no gochara chapter there.
Line 39 of that same record lists *"source-qualified Vedha case"* as **INDEPENDENTLY ACCEPTED**.

So a citation naming the wrong text carries an acceptance stamp in a W0 record that the whole
campaign treats as settled. The admitted chain is `bg_phaladeepika_vedha` — **Phaladīpikā** PG353,
ADJUDICATION-11 — a different work entirely. This is the source-qualification discipline failing at
the one place it is supposed to be strongest, and it propagated: the Kshetra session inherited the
phrase verbatim into two documents before catching it. **Routed to the W0 record's owner.** No L3
session edits an accepted W0 record.

**(b) A coverage gap that declares a table absent while it holds live rows.** `stage1_symbolization.py`'s
`latta_coverage()` returns `"not_in_corpus"` with *"No classical latta-kick rule table found in this
codebase."* Live: **`bg_phaladeepika_latta` holds 8 rows.** An unearned signal in the *opposite*
direction from the usual — declaring absence where there is presence — and it suppresses a source
the layer has already admitted. Fix belongs with the comment's owner; the coverage detector should
query rather than assert (the §11.12 pattern again).

**(c) The stored field is chart-wide; its contract says route-scoped.** Verified: `layer0.py:200-201`
states plainly *"Store ALL chart-level vighna instances. Per-class SM-R-7 filtering is Layer 1's
responsibility"*, and the SM-R-7 filter lives in `layer1.py` — a projection that never writes
`kala_field`. The field path passes `obstructions=self.envelopes.obstructions_at(t)` unfiltered
(`stage4_field.py:866-873`), and the null path does the same. So field and null are **mutually
consistent and chart-wide**, and the documented route-scoped contract is what no stored row honours.

Note what the Kshetra session did *not* claim: its reviewer inferred a further consequence — that
`null_p` is biased low by a field/null split — and that session **rejected it** after checking the
fourth site, because there is no split. Contract ≠ behaviour, not field ≠ null. Rejecting a
reviewer's consequence while accepting the finding is the right discipline and worth recording as
such. The native's decision is which semantics governs, gated on a byte-equality test
`field ≡ null ≡ projection` before any `null_p` is served.

### 11.15 The citation strike propagates: the layer has no corpus-verifiable vedha source

Consequence of §11.14(a), raised by the Kshetra session, cross-checked by the Gochara session,
measured independently here against `bg_transit_rules` where `vedha_house IS NOT NULL`:

| Citation | Rules |
|---|---|
| `BPHS Ch.29 (Gochara Phala — Transit Results)` | **39** |
| `Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)` | **2** |

BPHS Volume 1 Chapter 29 is *Bhāva Padas* (§11.14a) — so **39 of 41 vedha rules, 95% of the set,
cite a gochara chapter that does not exist.** The remaining 2 name the right work; the admitted
corpus holds `BPHS · Jaimini_Sutram · KP · KP_Reader` and **no Phaladīpikā** (0 matches under
`SOURCE_DATA`). So after the strike **zero vedha rules are corpus-verifiable.**

Two consequences the native should see plainly:

1. **`FOUNDATION_SAFETY §5:207-209`'s claim does not hold as written.** It names "the existing
   source-qualified ordinary reference" and the thing it names is the wrong chapter. That record's
   41 passing tests (`test_ka_vedha_gochara*.py`) prove geometry and interval behaviour — which is
   **computational correctness, not source qualification** (F24 keeps those tiers separate). A
   correction note belongs on that record; no L3 session edits it silently.
2. **The layer currently has no source-qualified ordinary reference at all.** Not just vedha:
   `ka_tithi_pravesha`'s own citation reads `not_in_corpus`, and Sarvatobhadra is an acknowledged
   approximation. So D4 (tithi-praveśa qualification) is not one asset's paperwork — it is the path
   to the layer's **first** honest source-qualified reference, which changes its priority.

**The three streams have already converged on the mechanism**, which is why this needs ruling once
rather than three times. The producer stamps every `ka_vedha_gochara` row with
`source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}`, `precision_regime ∈
{date_grain, instant_grain}` and **`corpus_verifiable`** (is the cited text actually in the admitted
corpus). Consumer admission is then uniform and mechanical: **F06 `applied` iff `corpus_verifiable`
AND the Vedha geometry conjuncts pass; otherwise `unqualified`.** Today that admits nothing —
house-vedha, sarvatobhadra and laṭṭā all enter unqualified in all three consumers — and the policy
lifts row by row as the stamp flips, with no plan needing re-ruling. This also corrects an
inconsistency the Gochara session caught in Kshetra's earlier draft, where house-vedha was applied
and laṭṭā unqualified on one stated ground.

**The fix is a corpus/L0 decision, not an L3 one** (Gochara's G-9): admit Phaladīpikā — and
Sārāvalī / Jātaka Pārijāta if the non-vedha rows citing them are to stay verse-cited — or re-grade
every gochara-vedha row uniformly as *cited-outside-admitted-corpus*. Routed to the corpus owner.
