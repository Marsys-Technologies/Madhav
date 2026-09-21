---
artifact: GOCHARA_FAMILY_ELEVATION_PLAN
version: "0.3"
status: PROPOSAL_FOR_NATIVE_RULING
supersedes: GOCHARA_FAMILY_ELEVATION_PLAN_v0_2.md (retained, SUPERSEDED)
incorporates_review: ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md (verdict PROCEED_WITH_AMENDMENTS; reviewed plan sha256 964b7f9e…)
produced_on: 2026-09-20
produced_by: Claude Code (Fable 5.1)
native_priorities: "1. quality  2. build efficiency  3. the ecosystem matters as much as the asset"
governing_strategy: ../../MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (DP-SD-017)
governing_execution_brief: ../../MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md
evidence: evidence_gochara/ (E1–E8 + OUTPUT_2026-09-20.txt); live aggregates in the review's §B
source_revision: 5d8252dbe (worktree /Users/Dev/madhav-l3/integration, branch codex/madhav-l3-claude-code)
does_not_authorize: >
  Any production code change, build, migration, registry edit, lifecycle change or hold release. The
  2026-08-21 standing order (no gochara re-materialization without fresh authorization) stands.
changelog:
  - "0.3: independent review folded in. Every reviewer counterexample was re-run here first (E8) —
     all reproduce. Withdrawn: 'the right kernel already exists', 'exact on 7 of 8 primitives',
     'take the Moon out of activity', 'one dump is the only copy', the 1.35 h × T cost model, and
     'single-digit minutes' as anything but a hypothesis. Added: convention/time contract, episode-
     primary geometry with resolution-bounded completeness, span-aware legacy algebra, immutable
     publication identity, a minimum L2 structural slice before terminal acceptance, a widened
     consumer/writer inventory incl. cockpit Clear, and a contract-first first slice with stop
     conditions."
  - "0.2: verification pass. 0.1: first proposal."
---

# Gochara family — elevation plan, v0.3

**How to read this.** v0.2 was sent for adversarial review. The reviewer returned *proceed with
amendments* and refuted parts of it with runnable counterexamples. I re-ran every one before
accepting it (`E8`); all hold. This version is the plan **after** that. §1 is the answer, §2 the
decision delta, §3–§6 the amended design and rulings, §7 the work packets, §8 where I still differ
from the reviewer, §9 what remains unknown.

Evidence tags: `[X]` executed here · `[A]` executed or queried by the reviewer, re-run by me where
possible · `[S]` source · `[R]` repo record · `[I]` inference · `[U]` unmeasured.

---

## 1. The answer, restated after review

**Direction unchanged; confidence and sequencing changed.**

- **Keep one accountable Gochara windows asset (`ka_gochara`)**, with its legitimately different
  outputs kept as *named projections beneath it* — event-class vs mechanism; point / era / month /
  day / chain; bounded-progressive vs full horizon; persisted vs on-demand — not flattened into one.
  `ka_gochara_resonance` kept and repaired. Century writer superseded only after the full gate set
  in R1. Sweep stays retired.
- **The native's idea stands** — enumerate events, don't sample a black box. The repeated-search
  waste is real and measured (`E2`,`E4`; reviewer re-measured 64 ms/eval, kakshya 59.7 % of search).
- **But the kernel is not "already built in two halves."** Both halves have correctness defects that
  a frame fix does not cure (§2, D1). And the legacy score is *not* reproducible from a single dated
  event list — some primitives are **residence spans** whose timestamp depends on where the caller
  started looking (§2, D2).
- **Quality first means inputs first.** The two confirmed production-path defects that matter most
  are not speed: the served engine feeds an **uncited fixture approximation** into every score (F15,
  confirmed on the production code path `[A]`), and W2G solves in the **wrong zodiac** (F3,
  confirmed `[X][A]`). Live data corroborates the consequence: all **380** served gen-3.0 rows that
  carry an activity value sit between **0.99964 and 1.0** `[A]`. A faster kernel on unrepaired
  inputs would deliver a more confident wrong answer.

**A correction the native should hear plainly.** I told you the century writer plausibly explains
your ~25 hours. The live record does not support that. Recorded completed executions of the century
writer are **240 s, 613 s and 3,492 s**, and the canonical chart's 270 substeps carry timestamps
spanning about **five hours** `[A]` — none proven to be one cold uninterrupted build. My
`1.35 h × targets` model over-predicts (live classes have 14–40 targets). The ~25–36 h figure in the
repository belongs to the **retired sweep** (35.6 h `[R]`). So: the century build is *hours, not a
day*; it is still far too slow for what it produces; and the real cold number remains **unmeasured**.

---

## 2. Decision delta — what the review changed

| # | v0.2 said | Evidence against | v0.3 position |
|---|---|---|---|
| **D1** | The right kernel exists in two halves (W2G arcs + Kshetra S0); add a frame term. | `[A][X E8]` W2G **merges stations <0.25 d apart** and then finds 1 of 3 real roots; drops a **tangency at the 0°/360° seam**; silently returns `[]` on a derivative-root exception. S0 **emits nothing for a body already inside orb** at horizon start; assigns **noon data to midnight** time (`:659` vs `:501`) — 7.5° for the Moon; passes tropical speeds as sidereal Hermite slopes. L0 negates Ketu's speed though Ketu = Rahu + 180°. | Reuse *ideas and individually verified functions only*. The kernel is new work with its own proofs. §3.1–§3.3. |
| **D2** | λ_v3 is exactly a step function of one dated event list; PoC exact on 7/8 primitives. | `[A][X E8]` Sign-only `drishti_contact` returns a *resident* event stamped at the caller's window start: engine gives activity 0.45, filtered global list gives 0.0. `sign_occupation` in PERMISSION behaves the same way. PoC compared **activity only**, with 3 of 8 primitive families inactive and λ ≡ 0. | The legacy formula is *largely discrete*, but its algebra has **three object kinds — point events, residence spans, interval overlaps** — each with its own boundary rule. Stage E must be span-aware and factor-by-factor. §3.4. |
| **D3** | 0.314″ ⇒ "nothing falls between samples". | `[A]` 0.314″ is a small-sample observation (a few stations/perigees, away from fit edges). A real true-node prograde excursion of 0.048″ yields 3 direct roots; daily knots yield 1. | Positional error and **topological completeness are separate claims**. §3.2. |
| **D4** | "Correct frame" = subtract ayanāṃśa. | `[A][X E8]` The repo's two sidereal conventions (`FLG_SIDEREAL` vs tropical − `get_ayanamsa_ut`) disagree by **−5.5″ to +16.5″** for the Moon. | A **convention vector** is pinned before any oracle comparison. §3.1. |
| **D5** | Take the Moon out of the activity term. | ADJ-14 rejects cost-led amputation and keeps Moon contacts as legitimate on-demand evidence `[R]`. My ablation showed the Moon *dominates*, not that it is *illegitimate*. | **Withdrawn.** Moon geometry and testimony are kept; whether and how it enters a given score is a separate, source-qualified ruling. R4. |
| **D6** | Wire mechanisms, AV gating first. | `[S]` `w21_av_gating.py:126-143` uses the **rule threshold as a proxy for the chart's bindu count**. `ClassContext` lacks the Kota/annual inputs those modules expect. | Operand audit precedes even *testimony-only* admission. "Testimony-only" is not harmless. R5. |
| **D7** | One table + generation `'4.0'` + authority flip is a sound cutover. | `[A]` A rebuild *inside* a served generation mutates authoritative data with no flip; the table stores **dates**, not instants; the arc fingerprint hashes knot **count, not content**, so a same-size upstream correction does not invalidate it. | Immutable **publication identity** distinct from the algorithm label; complete partition manifest incl. valid-empty; exact-time contacts stored separately from day-level windows. §3.6. |
| **D8** | Consumers need almost nothing. | `[A][S]` MCP coverage branch treats `4.0` as v1 and can return `not_covered` before reading rows; `reading_checklist` drops ids/generation/basis and counts a capped set; D8/D9 adapters flatten shape semantics; L5 ledger has no field for contact ids; `engine_tier` is **not wired**; **cockpit Clear is an unlisted destructive writer** with the protection registry now empty. | Consumer and writer inventory widened; receiving work is on the critical path. §5. |
| **D9** | Live cockpit count is another asset's rows. | `[A]` Migration 670 already corrected `count_sql`; `target_table` and the seed remain stale. | Registry reconciliation is broader than one field and is needed **early**, not at cutover. R10. |
| **D10** | One dump is the only v1 recovery. | `[A]` Two retained archive tables exist; together they match **35,620 of 38,287** current v1 ids. `pg_restore -l` is a listing, not a restore. Migration 588 is **applied**; no guard triggers exist. | Neither "one copy" nor "fully recoverable" is true. A real restore drill is a gate. R6. |
| **D11** | Defer L2 binding to phase 2. | Product §12.2 and execution-brief §7 (`L3-SLICE-STRUCTURE-TIME-01`) require the structural join for delivered value. | Reserve fields now **and** deliver a *minimum* L2 structural slice before terminal acceptance. R8. |
| **D12** | First slice WP1+WP2+WP3 on one real chart; all "already authorized". | Execution-brief §3: non-person fixtures first; packet ownership and contract review required. | Contract-first slice on synthetic cases, with stop conditions. §7. |

Reviewer findings that **strengthened** the plan: F3 confirmed; F15 confirmed *on the production code
path* (the engine passes `conn=None` to kakshya even when its context came from a real DB); F17
confirmed applied; F14 corroborated in live served rows; F13 extended — `_eval_single` turns **any
exception into 0.0**, which the `>= 0.0` threshold then certifies as "active".

---

## 3. Amended design

### 3.1 Convention and time contract — before anything else
One pinned vector, carried on every contact and publication: ephemeris source/files/version · time
scale and **noon-UT knot origin** · sidereal method (`FLG_SIDEREAL` *or* tropical − ayanāṃśa — chosen
once, by ruling, since they differ by up to ~16″ `[X]`) · apparent/mean/nutation flags · node type
and Ketu construction · geocentric scope · unwrapping · stored precision · interpolation and slope
policy. *The "independent Swiss oracle" means nothing until both sides request the same quantity.*
This also settles whether a stored speed may serve as a sidereal Hermite slope (it may not without
the frame derivative) — slopes are derived or validated, not assumed.

### 3.2 Geometry: episodes are primary; completeness is resolution-bounded
The object of record is the **contact episode** — the interval a body is within a qualified orb —
not the exact-crossing instant. Exact passes are attributes *inside* an episode. This makes the
kernel robust to the reviewer's sub-arcsecond triple-crossing: root multiplicity at a station changes
the pass count, not the episode. Requirements, each with a fixture:
- no station coalescing; no swallowed solver exceptions — a failure is a **coverage state**, never `[]`;
- explicit ownership of the 0°/360° seam; endpoint and tangent handling;
- **truncated episodes emitted** when a body is inside orb at a horizon edge;
- three distinct outcomes: exact crossing · in-orb closest approach · tangency to the orb boundary;
- solving on an **unwrapped, branch-qualified separation**, so anti-point phantoms are structurally
  impossible rather than merely absent;
- **declared angular resolution ε.** Completeness is claimed only above ε; any contact within ε of a
  station carries `near_station_unresolved` and, where it matters to a consumer, is settled by a
  direct adaptive Swiss solve. Where neither holds: `coverage = not_proved_complete`.
- latitude retained (Kshetra's syzygy path needs it `[A]`); no distance consumer established.

### 3.3 Reuse policy
A low-level pure kernel with a **one-way dependency**: numerical primitives → asset adapters. It
does not import Kshetra S0 (that would invert later into a cycle when S0 adopts the kernel). It may
lift *individually proven* functions from `w2g`/S0 under an explicit inventory with a duplicate-copy
audit entry, or extract them in an owned cross-stream packet. Adoption changes each adopter's digest
closure — accepted and recorded, not claimed away. `transit_search.py` and `ka_dasha_kala` remain
untouched.

### 3.4 Legacy algebra (Stage E), span-aware
Three object kinds with explicit boundary rules: **point events** (±5 d box), **residence spans**
(a state that holds over an interval — sign-only dṛṣṭi, sign occupation, Sade-Sati phase), and
**interval overlaps** (vedha, with its date-rounded convention). Failures and missing inputs are
states, not zeros. Equivalence is proved **factor by factor** on a non-vacuous matrix: every active
primitive, longitude *and* sign-only targets, non-zero permission, changing tara, signed/negative
weights, missing overlays, exceptions, seams, horizon joins. "Bit-identical" and "numerically
equivalent within τ" are separately pre-declared. Known artefacts (`eclipse_degree` window-edge
stamps, anti-point phantoms) are *classified*, never copied into acceptance or silently waived.

### 3.5 Typed testimony — unchanged in intent, stricter in admission
Background period · enabling interval · specific contact · inhibition · modifiers, each with method,
source, citation state, applicability and **evaluated / not-evaluated / inapplicable**. New rule: an
operand is audited for *what it actually is* before it appears as testimony at all (D6).

### 3.6 Identity, storage, publication
- **Contact identity** = normalized physical target + relation + astronomical input identity +
  convention vector + branch/occurrence + method policy. Class membership, weights and L2
  interpretation are **separate, versioned bindings**. Horizon clipping never renames an episode;
  a correction creates a new version without rewriting issued evidence.
- **Exact-time ledger** stored separately from the **day-level windows projection** (the windows
  table holds dates `[S]`).
- **Publication** = immutable build identity ≠ algorithm label; complete partition manifest incl.
  valid-empty partitions; accepted upstream generation vector; atomic switch only to a *complete*
  candidate; readers pin one publication per request. Caches key on **content**, not counts.
- Go-live still uses `kala_gochara_authority` and its **four functional flip gates**
  (`527:98-102` — none is time-based); a soak is supplementary observation, not a gate substitute.

### 3.7 Snapshot vs service — answer stands, claim narrowed
Stored knots + an in-process interpolant still beat both a day-rounded service (F7, confirmed) and a
serial live one. But "exact" becomes: *positional error observed ≤0.314″ on a limited sample
`[R]`; topology guaranteed only above ε; direct Swiss solve where a consumer needs more.* Every
answer declares which it is: snapshot, interpolated, or direct.

---

## 4. Rulings — my recommendation after review

| # | Recommendation | Changed? |
|---|---|---|
| **R1** | One accountable asset under `ka_gochara`, variants preserved as named projections. Retirement of the century writer requires: source-qualified semantics · complete declared coverage incl. valid-empty · delivered consumer identity/precision/counter-evidence · reproducibility · history + rollback · the DP-SD denominator amendment. | amended |
| **R2** | New pure kernel, one-way dependency, no S0 import; adoption-time digest changes recorded. | amended |
| **R3** | Free sub-day *computation*; separate fields for astronomical time+bracket+tolerance, classification certainty, and forecast precision. Retiring the rail is itself a ruling, not a by-product of cheapness. | amended |
| **R4** | **Order reversed to inputs-first.** (1) Remove the fixture kakshya fallback from any production projection — real L1 BPHS Ch.66 boundaries pre-fetched and pinned, else *not evaluated*; preserve missingness; de-duplicate one physical contribution reached via several targets. (2) Produce geometric episodes with **no new interpretive weights**. (3) Compare a qualified contact-interval projection against the legacy boxes, **all bodies retained**. (4) Rule separately on separation scaling, dwell, Moon participation in this score, era construction, real-eclipse effect. *These are method proposals; I no longer claim otherwise.* A continuous score needs its own reference and peak algorithm — Stage E's step proof does not transfer. | **reversed** |
| **R5** | Two-step admission kept, preceded by an **operand audit** per mechanism. Order by verified readiness and user value, not by W-number. W21 is **not** first: it must read real L1 SAV/BAV at the relevant sign and time. No L4/L5 admission or empirical evaluation under an L3 packet. | amended |
| **R6** | Ask the native for a **fresh, explicit ruling** on a (table, generation) policy — migration 588's comment is advice, not standing authority. Before it: map the whole mutation surface (DELETE, UPDATE of generation/chart keys, TRUNCATE, **cockpit Clear**, cascades); a real restore drill covering all 38,287 current v1 rows, content-checked; rollback tested under concurrent reads. | amended |
| **R7** | Moon degree contacts on demand *by default*, persistence decided on measured query/replay/storage. **Never restrict Moon search to windows pre-selected by slow bodies** — that hides Moon-only candidates. | amended |
| **R8** | Reserve binding fields now **and** deliver one minimum L2 structural slice (one qualified structure, its cancellation/eligibility, real target bindings, contacts, three-way negative, managed-consumer evidence) **before terminal acceptance**. Wider Sangam/Kshetra adoption stays separate. | amended |
| **R9** | Register F3; label, don't delete; stop further dispatch **through a governed lifecycle control**, not a note. | agreed |
| **R10** | Reconcile seed · live registry · generated contracts · integrity SQL · coverage logic together, **early** — D1/D3 contracts and benchmark dimensions depend on it, and a reseed could restore the stale value. | amended |

---

## 5. Ecosystem — widened inventory

| Surface | Problem `[A][S]` | Work |
|---|---|---|
| MCP coverage attestation (`register_gochara_windows.ts:963-977`, `:1466-1478`, `:1041`) | unknown generation falls into the retired-sweep branch; can answer `not_covered` before reading windows; intersects *current mutable* resonance targets | publication-bound coverage manifest incl. complete-empty; pinned target universe; test all three tools |
| `reading_checklist.ts:1063-1092` | drops ids, generation, resolution, parents, `peak_basis`; LIMIT 200 → returns 5; counts the capped set | carry evidence; honest returned/available/truncated counts |
| D8/D9 managed synthesis | non-point rows → "era context", dated points → "timing"; finer semantics lost | sentinel replay through retrieval → synthesis → delivery → retained evidence |
| Paripraśna `engine_tier` | **not wired**; no non-test caller | treat as prospective contract, not current protection |
| L5 prospective ledger | no field for contact id, generation or convention | specify the hand-off; receiving-owner amendment — **no claim issuance under this packet** |
| **Cockpit Clear** (`cockpit/clear/execute/route.ts:84-108,156-182`) | derives DELETEs from registry rows; does not exclude retired assets; protection registry empty | review preview + execute together **before any successor write** |
| `w45_post_fit_rebuild.py` | mutates calibration state, can insert prospective rows, top-20 path | inventory mutating behaviour; keep L4/L5 boundaries |
| Kshetra cross-check pin (`writer.py:2313-2375`) | resonance digest from count/max-timestamp/max-id, not content | pin immutable publication/content |
| `permission_curve.py`, W41/W43/W44, census/TCI, authority helpers | direct readers, un-audited | bounded discovery list — *not claimed complete* |

**Ownership.** Stream C leads the numerical work; it is **not** sole authority. Name one integration
owner plus non-overlapping A (resonance, overlays), B (`ka_gochara`, Yojaka, Sangam), C (kernel,
v3, Kshetra) and receiving packets. One build lane, one integrator, hub-freeze and transitive-digest
rules all still bind.

---

## 6. What "done" means here
Campaign D1–D10 unchanged, with the review's sharpening: **D1/D3/D4 contracts come before the
algorithms**, D5's oracle must be convention-matched, D6 benchmarks are *bounded prototype* numbers
until persistence, recovery and one managed consumer exist, and D8/D10 require a real structural
question (product §12.2) to be answered better than today, with identities and negative evidence
preserved end to end.

---

## 7. Work packets

| WP | Work | Exit gate |
|---|---|---|
| **0** | Use the reviewer's live aggregates (re-validate at implementation time). Register — through the authorized owner — F3, F13 (incl. exception→0.0→"active"), F15, F16, F17, the kernel/S0 defects, the convention mismatch, W21's proxy operand, the coverage-branch and Clear hazards. | defects registered; nothing claimed about the historical ≥2-era case beyond "misattributed diagnosis, unreconstructed" |
| **1 — Contracts** *(was the front of WP4)* | Convention/time vector (§3.1); field dossier, grain, natural keys, null semantics (D1); contact and projection identity (§3.6); three-way negative coverage design; input generation vector (D4); reference oracle, tolerances, ownership, file fences, immutable test vector; point-vs-span semantics; event-time vs forecast-precision. Registry reconciliation design (R10). | independently reviewed; native rules the sidereal convention |
| **2 — Synthetic fixture suite** | Deterministic **non-person** cases: close-station cubic, real true-node excursion, seam tangency, start-inside / end-inside episodes, noon conversion, sign-only dṛṣṭi, non-zero permission, missing overlay, exception, negative weights, plateau ties. Factorized scorer oracle, hand-specified. | every case has an expected answer derived without legacy output |
| **3a — Kernel** ‖ **3b — Span-aware legacy algebra** | Independent bounded work. E1 is kept as the *legacy defect reproducer*; the kernel gets its own convention-matched comparison with declared angular, time and coverage tolerances. | 3a: all WP2 geometry fixtures pass; candidate set independently enumerated; no silent drops. 3b: factor-by-factor equivalence on the WP2 matrix; artefacts classified |
| **4 — Decomposed comparison** | oracle → legacy event semantics → successor geometry → projection, on one pre-declared workload. Bounded cold/warm timings with prepare/search/query separated. | every delta classified with input and reference; ids stable under horizon re-partitioning. Output is labelled **producer prototype evidence** — not a century build result, not `DATA_ACCEPTED` |
| **5 — Inputs-first quality repair** (R4.1–R4.2) | fixture-kakshya removal, missingness, physical de-duplication, geometric episodes without new weights | native ruling per change; served-path behaviour matches its documentation (§N.7) |
| **6 — Ledger + publication** | exact-time ledger, windows projection, immutable publication/manifest, content-keyed caches | crash/resume, extension, correction, concurrent-read and rollback tests |
| **7 — Receiving contracts + one L2 structural slice** | §5 surfaces; R8 minimum slice through a managed channel | sentinel field survives retrieval, budget, delivery and replay; a §12.2-style question is answered with preserved identities and three-way negatives |
| **8 — Method rulings** (R4.3–R4.4) and **mechanism admission** (R5) | one PR per method/mechanism; operand audit → testimony → ablation on a non-empty, non-vacuous corpus | native ruling each; new continuous-score reference where applicable |
| **9 — Overlays** | Vedha, Moorti, Kota on the agreed convention; owners in Stream A/B | coverage = requested horizon; Moorti at true ingress with error rate reported; horizon-constant ayanāṃśa error measured |
| **10 — Full benchmark, then cutover** | strategy §5 in full (cold/warm/resume/extension/correction/no-window/dense/rare; wall, CPU, RSS, Swiss-lock, SQL, WAL, recovery, time to first *qualified consumer result*) → R6 policy + restore drill → four functional flip gates → per-chart authority switch | fresh native authorization; rollback proven through the real serving adapters |

**First slice = WP1 → WP2 → (WP3a ‖ WP3b) → WP4.** No production data, no real chart until its gate.

**Stop conditions** (a timing gain overrides none of them): unresolved astronomical convention ·
unknown input masquerading as empty · missed physical topology with no declared fallback · an
unclassified divergence · identity drift under equivalent horizon partitioning · any acceptance
comparison made vacuous by zero permission or absent operands.

---

## 8. Where I still differ from the reviewer — for the native to weigh

1. **Completeness contract.** The reviewer asks for adaptive direct calculation *or* an explicit
   not-proved state wherever daily knots cannot prove topology. I propose the narrower, cheaper
   contract of §3.2: episodes primary, a declared resolution ε, and direct solves only where a
   consumer needs sub-ε truth. A 0.048″ node wobble is physically real and astrologically without
   meaning; it should be *disclosed*, not chased. This is a judgment call and I may be wrong about
   what a future consumer needs.
2. **Urgency of the kakshya fixture.** The reviewer ranks it within a general input-repair packet.
   I would treat it as the single most valuable early fix: it is confirmed on the served path, it is
   the largest contributor to both noise and cost, the engine's own documentation says it does not
   happen, and correcting it needs no new doctrine — only honesty (cited L1 boundaries, or *not
   evaluated*).
3. **Nothing else.** On every other point the reviewer's evidence is better than mine was.

## 9. Still unknown

A cold, uninterrupted, full-workload century build time. The full-century distribution of activity
(the 380 rows are selected peaks, not a time series) and which factor actually selects production
peaks. Whether any older run truly produced multiple era windows. The Moorti misclassification rate.
Ledger storage size. Whether the deployed source equals this revision. A complete reader/writer
inventory. And every method question in R4/R5 — which are the native's to rule, at acharya standard.
