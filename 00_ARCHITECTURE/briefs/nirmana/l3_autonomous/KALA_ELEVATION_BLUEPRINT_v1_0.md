---
artifact: KALA_ELEVATION_BLUEPRINT
canonical_id: KALA_ELEVATION_BLUEPRINT
version: "1.5"
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

**Decisions (the native's, gating stage 4+):** D1 release the W1 hold under the frozen generation
design · D2 receipts for the two missing states (an enum member; no migration) · D3 the three
protected classes · D4 tithi-praveśa source qualification · D5 baseline authority — all in
`KALA_PHASE2_DECISIONS_v1_0.md`; plus Q1–Q8 of the elevation plan and each brief's own list.

**Holds (not decisions):** W1 on the cutover; century v3 on its BUILD-PROTECTED guard; Kshetra
populated replacement until W7; Bhavishya until its W6 packet; RI-01 on production-owner authority.

**Risks:** an L2 rebuild during the campaign empties five tables again (mitigation: build-order rule
+ `cascade_check.sql` until W1); Pūrṇa and L3 collide on `kala_views` (mitigation: interface packets
only); the three brief sessions write into foreign worktrees (found; fix in §7); decision latency
idles the fleet (mitigation: recommendations attached, one sitting); every cost number is
unmeasured until Phase 0.3 lands (mitigation: no schedule promised before it).

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

**Is it visible in a reading? The class yes; the specific claim NO — withdrawn.** Three figures
have circulated between the sessions and they were measuring three different things. Reconciled:

| Quantity | Sidereal (Lahiri) | Rohiṇī pāda |
|---|---|---|
| Swiss TRUE recomputed at the birth instant (05:13 UT) | 50.0502° | 4 |
| Swiss MEAN recomputed at the birth instant | 49.0289° | 3 |
| **The stored `ephemeris_daily` knot** (00:00 UT), converted | **49.9941°** | 3 |

So mean-vs-true does move a pāda *when recomputed* — but the **stored** value, which is what Kāla
actually consumes, sits **0.0059° from the pāda-3/4 boundary**, while this host's ephemeris error is
~0.1° (no `.se1` files locally → Moshier fallback; the build image ships Swiss files). **The margin
is sixteen times smaller than the measurement error, so the pāda assignment for the stored value is
not resolvable here and must not be put to the native as measured.** It needs a run against the
production ephemeris. The *general* point stands and is enough: a ~1° shift against 3°20′ pādas can
move a pāda, so the ruling is reading-visible in class. Maximum divergence ~1.9° over 1984–2084
(Gochara session, not recomputed here).

Note this cuts the other way too: my five-date residuals of ≤0.10° against TRUE are themselves
partly Moshier error. The discrimination survives it easily — ~0.1° from true versus 0.95–1.47° from
mean is tenfold to two-hundredfold — but no sub-0.1° claim from this host is safe. **See §11.9: the
local ephemeris is worse than "imprecise", it is not reproducible between sessions.**

**Reach, measured for the canonical chart:** 40 of 765 `gochara_resonance_map` targets are
Rāhu/Ketu across 9 event classes · **232 of 914** served generation-3.0 rows carry node contacts
(carrier: `term_breakdown`; `active_sentences` is `[]` on all 914) · **50 of 87** generation-2.0
rows in `_v2` (carrier: `active_sentences`) · `kala_convergence` 0 (table empty for this chart) ·
**6,225 of 16,297 protected v1 rows** carry node contacts — so a node change also alters how any
successor compares against the protected benchmark.

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

**Rule for every numerical acceptance gate in this campaign:** require `.se1` present and record the
file checksums in the evidence, or the result is `NOT_RUN` — never `PASS`. Any inherited
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

### 11.9 The local ephemeris is not reproducible between sessions — and that settles the pāda question

The Gochara session proposed a correction to §11.1's margin arithmetic: that on 1984-02-05 the
stored-vs-recomputed residual is 0.0046° (16.7″), so the natal margin is ~12× the error rather than
inside it. **That correction is not adopted, because its underlying figure does not reproduce on this
host** — and chasing why produced a better finding than either of us had.

Measured here, explicitly: `SWE_EPHE_PATH` is unset; `FLG_SWIEPH` returns `FLG_MOSEPH`, and
`FLG_SWIEPH` and `FLG_MOSEPH` give bit-identical results — Moshier fallback confirmed. True-node at
the 1984-02-05 knot: **73.725995°**. The peer reports **73.633696°** for the same body, same date.
**The two sessions differ by 0.0923° = 332 arcsec**, and neither of us can presently account for it.

That divergence is larger than every margin in dispute, and it is decisive in both directions:

| Quantity | Sidereal | Pāda | Margin to the 50.0000° boundary |
|---|---|---|---|
| **(B)** the **stored** knot, converted — what Kāla consumes | 49.9941° | 3 | **21″** |
| (B′) my recomputation at the same knot | 50.0911° | **4** | 328″ |
| (B″) the peer's figure at the same knot | 49.9988° | 3 | **4″** |
| **(A)** my recomputation at the birth instant | 50.0502° | **4** | 181″ |
| (A′) the same, carrying the peer's 332″ offset | 49.9579° | **3** | 152″ |
| MEAN at the birth instant (analytic, no ephemeris file) | 49.0289° | 3 | 3496″ |

**The withdrawn claim was not merely unproven — under the peer's own numbers it inverts.** Their
withdrawn assertion was TRUE → pāda 4; carry their offset to the birth instant and true-node Rāhu
lands in **pāda 3**, the same pāda as mean, and the "ruling moves a pāda" argument disappears
entirely. So the withdrawal stands on stronger grounds than the ones either of us first gave: not
"the margin is smaller than the error", but **"two sessions cannot agree on the value to within four
times the margin, and the disagreement flips the answer."**

Two consequences beyond this one figure:

1. **Every local geometry figure produced by any session in this campaign inherits an unexplained
   332″ session-to-session divergence** until the cause is found. Prime suspects: a pyswisseph
   version difference in the Moshier node routine, or a `calc` / `calc_ut` (ET vs UT) mix-up. This is
   a bounded diagnostic, and it should be run before any numerical acceptance gate is designed — it
   is the precondition for §11.7's rule, not a footnote to it.
2. **The stored production value is 16.7″ from the peer's figure and 349″ from mine** — so
   production, which builds with real `.se1` files, is far closer to the peer's computation. That is
   weak evidence that my local Moshier node is the outlier, and it is the reason §11.1's
   store-is-TRUE conclusion is stated on the **tenfold-to-two-hundredfold separation** rather than
   on any single residual.

**What this does NOT weaken:** the store-is-TRUE finding. 0.005–0.104° from true against 0.95–1.47°
from mean survives a 0.09° uncertainty with room to spare, and the peer agrees the conclusion should
stand firmly. Only sub-0.1° claims need the caveat.

**And it sharpens the disposition choice in §11.2.** The mean node is analytic — mean elements, no
ephemeris file — so option (b), *keep the true knots and derive mean at read time*, **never consumes
the knot** and is therefore immune to this knife edge entirely. Only consumers wanting the stored
true value inherit the irreproducibility. That is a substantive argument for (b) that neither the
cost table nor the frozen-layer argument captures. (Raised by the Gochara session from this
session's measurement; verified here.)
