---
artifact: GOCHARA_FAMILY_ELEVATION_PLAN
version: "1.0"
status: NATIVE_RATIFIED_PLAN
supersedes: GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md (retained, SUPERSEDED)
review_of_record: ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md (independent, verdict PROCEED_WITH_AMENDMENTS)
ratified_on: 2026-09-22
superseded_in_part_by: >
  GOCHARA_FAMILY_ELEVATION_BRIEF_v1_0.md (2026-09-22) proposes superseding D-2's SEQUENCE only —
  close the Clear deletion path first, then grant, then restore drill, then guard — because the
  drill cannot run (no SELECT for data_plane_builder on its own recovery source) and the deletion
  path is live and ordinary-user-reachable. PENDING the native's N-1 ruling; until then this
  file's D-2 stands as ratified. All other D/R decisions here are carried forward unchanged.
  RESOLVED 2026-09-23: N-1 APPROVED by the native (GOCHARA_RULING_SHEET_v1_0.md §1) — D-2's sequence is
  amended as proposed; D-2's substance stands. This plan is superseded in full by
  GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (NATIVE_RATIFIED_PLAN), which carries D-1..D-3 and R1–R10 verbatim.
ratified_by: "Native (Abhisek Mohanty) — three decisions D-1/D-2/D-3 explicit; R1–R10 under standing 'go with your recommendation'"
produced_by: Claude Code
native_priorities: "1. quality  2. build efficiency  3. the ecosystem matters as much as the asset"
governing_strategy: ../../MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (DP-SD-017)
governing_execution_brief: ../../MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md
campaign_plan: ../MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md
product_parent: ../../../../MADHAV_PRODUCT_DEFINITION_v3_0.md
evidence: evidence_gochara/ (E1–E8 + OUTPUT_2026-09-20.txt); live aggregates in the review §B
source_revision: 5d8252dbe (worktree /Users/Dev/madhav-l3/integration, branch codex/madhav-l3-claude-code)
does_not_authorize: >
  This plan is ratified as a PLAN. It does not authorize a production build, migration, registry
  edit, lifecycle change, deployment or release of the century hold. The 2026-08-21 standing order
  (no gochara re-materialization without fresh explicit authorization) remains in force and is
  discharged only at WP10. WP1–WP4 are local/synthetic work under execution-brief §3.
changelog:
  - "1.0 (2026-09-22): native ratification. D-1 sidereal convention = Swiss sidereal mode (Lahiri).
     D-2 guard = restore drill then generation-keyed guard on v1 + cockpit Clear fix. D-3 scoring =
     split: six honesty fixes pre-approved, four method calls deferred to evidence. R1–R10 as
     amended in v0.3 stand. Decision ledger §1 is now the authority for what is and is not settled."
  - "0.3: independent review folded in. 0.2: verification pass. 0.1: first proposal."
---

# Gochara family — ratified elevation plan

This is the complete plan for `ka_gochara`, `ka_gochara_resonance`,
`ka_gochara_v3_century_materialize` and `ka_gochara_sweep`, after one verification pass and one
independent adversarial review. §1 states exactly what is settled and what is not. §2–§6 are the
subject, evidence and design. §7–§9 are the work. §10–§12 are risk, governance and the honest
residue.

Evidence tags: `[X]` executed in this work (`evidence_gochara/`) · `[A]` executed or queried by the
independent reviewer, re-run here where possible (`E8`) · `[S]` source at the pinned revision ·
`[R]` repository record · `[I]` inference · `[U]` unmeasured.

---

## 1. Decision ledger

### 1.1 Closed by explicit native ruling, 2026-09-22

**D-1 — Sidereal convention: Swiss Ephemeris's own sidereal mode, Lahiri/Chitrapakṣa.**
The ayanāṃśa was never in question; Lahiri is already canonical and is the Indian national standard.
What was in question is *how* it is applied, because the repository contains two methods that
disagree by up to ~16.5″ `[X]`. The cause is nutation: the second method subtracts a smooth
ayanāṃśa from an apparent (nutating) tropical longitude. Removing nutation closes the gap to
0.0000″ on every date tested `[X]`. Therefore:
- The pinned convention for all Gochara geometry is Swiss sidereal mode (`FLG_SIDEREAL`, `SIDM_LAHIRI`).
- The kernel reproduces it from stored `ephemeris_daily` knots by removing nutation before
  subtracting the ayanāṃśa, so no L0 change and no new ephemeris pass is required.
- 13 modules already use this method, including `transit_search.py`, `bg_sky_calendar`,
  `panchang_engine` and `ka_sangam` `[S]`.
- **Disclosed consequence, not a Gochara change:** L1 natal longitudes are computed as
  tropical − ayanāṃśa without removing nutation (`brahmagyan/ganita/l1_positions.py:118`) `[S]`, so
  they carry ~14.85″ ≈ 0.0041° on the native's birth date `[X]` — astrologically negligible, and
  about three hours of timing for Saturn. L1 is sealed and remains the authority (§N.5). This is
  registered as a disclosed finding and routed to L1's owner. It is **not** repaired here.

**D-2 — Guard policy: prove the backup, then a generation-keyed guard.** In order:
1. Restore the 2026-08-23 dump into a disposable database and verify all 38,287 `v1` rows return
   with content integrity — not a `pg_restore -l` listing, an actual restore.
2. Only then add a guard keyed on **(table, generation)** protecting `generation='v1'` only, so the
   successor's own writes are never blocked — the exact failure that caused migration 588's removal
   `[R]`, and the form migration 588's own note recommends.
3. Fix `cockpit/clear/execute/route.ts` so retired assets and protected generations are excluded;
   review its preview and execute paths together `[A][S]`.
4. Map the whole mutation surface first: DELETE, UPDATE of generation/chart keys, TRUNCATE (which
   cannot inspect per-row generation), cascades, and the Clear route.
This partially reverses the 2026-08-23 instruction, knowingly and in the narrow form that
instruction's own migration proposed. Live state confirms the exposure: migration 588 applied
2026-08-23 05:33 UTC, no protection triggers exist, `build_protected_assets` empty, and the retained
archives match only **35,620 of 38,287** current `v1` ids `[A]`.

**D-3 — Scoring-method process: split.** Six honesty fixes are pre-approved now; four method
questions are deferred to a ruling with comparison evidence in front of the native. The full lists
are §9.1 and §9.2. The distinction is the load-bearing one: a honesty fix makes the code do what it
already claims; a method call changes what the astrology asserts.

### 1.2 Closed under the standing instruction ("go with your recommendation")

R1–R10 as amended in v0.3 stand as ratified. In brief: one accountable windows asset under
`ka_gochara` with legitimate variants preserved as *named projections*, and a full gate set before
the century writer is retired (R1); a new pure kernel with a one-way dependency, no Kshetra import
(R2); sub-day computation free with claims still governed and precision fields separated (R3);
inputs-first ordering (R4); two-step mechanism admission preceded by an operand audit, and W21 *not*
first (R5); R6 superseded by D-2; Moon on demand with full-interval search (R7); binding fields
reserved now plus a minimum L2 structural slice before terminal acceptance (R8); register the frame
defect, label rather than delete, stop dispatch through a governed control (R9); registry
reconciliation early, not at cutover (R10).

### 1.3 Open by design — the native's own deferral under D-3

These are **not** oversights. D-3 routes each to a ruling with evidence, at WP8.

| id | Question | Evidence that will be put in front of you |
|---|---|---|
| **M-1** | Should a transit count *while within orb*, scaled by actual separation, instead of only when an exact crossing fell within ±5 days? | Side-by-side projection on a real corpus vs the legacy boxes, all bodies retained |
| **M-2** | Should slow and stationary passages weigh more (dwell weighting)? | Ablation with and without dwell on matched questions |
| **M-3** | How does the Moon participate in *this score*? (It stays in the evidence either way.) | Body-specific projections, source-qualified, with ADJ-14's standing position stated |
| **M-4** | Which of the eight unwired mechanisms enter scoring, and in what order? | Per-mechanism operand audit, then non-vacuous ablation on a non-empty corpus |

### 1.4 Open — not mine to close

| id | Item | Owner |
|---|---|---|
| **G-1** | Strategy amendment for the asset-denominator change R1 implies (22 active identities) | Native + strategy owner, as a DP-SD entry |
| **G-2** | Q3 "what counts as an independent witness" — cross-asset (Sangam, Sudarśana); blocks M-4's annual-stack item | Native; campaign plan §5 Q3 |
| **G-3** | Q8 cross-asset truncation policy — Gochara's own share is settled by honesty fix H-5, the other six assets are not | Native; campaign plan §5 Q8 |
| **G-4** | L1 natal nutation offset (D-1's disclosed consequence) | L1 owner; disclosed, not repaired here |
| **G-5** | Method qualification for provisional ontology signature models — five classes named in source `[A]` | L0 authority; never invented in L3 |

### 1.5 Open — needs measurement, not a ruling

Cold full-workload century build time `[U]` · full-century activity distribution and which factor
actually selects production peaks `[U]` · Moorti misclassification rate `[U]` · ledger storage size
`[U]` · whether any older run truly produced multiple era windows `[U]` · a complete reader/writer
inventory `[U]` · whether the deployed source equals this revision `[U]`.

**Answer to "is everything closed?" — no, and it should not be.** Three decisions are closed, R1–R10
stand, four method calls are deliberately deferred by your own instruction, five items belong to
other owners, and seven need measurement. WP1–WP4 do not depend on any open item.

---

## 2. What Gochara is for

Product v3.0 §3.10 `[S]`: *"Distinguish a background period, enabling interval, specific contact,
inhibiting condition, recurrence and inferred manifestation. A transit coincidence is not a complete
activation mechanism. A precise astronomical timestamp does not confer equivalent precision on a
forecast. … Moving from a long chapter to a short interval must preserve the same evidence
identities. … The search horizon, resolution and method coverage bound any 'no eligible window'
conclusion."*

**True value — ownable, exact, affordable.** The *contact layer of time*: for this chart's own
qualified structures, which body touches which target, by which relation, from when to when, how
closely, in which branch (direct / retrograde / stationary), under which convention, with what
searched coverage — stably identified, so that a life chapter, an interval and an instant all cite
the same evidence. These are strategy §3's **Contact** and **Search coverage** objects.

**Wishful value — what a single λ implies today.** One scalar,
PROMISE × PERMISSION × activity × modifiers × gates, labelled by a *generic* event class. It
multiplies together precisely the things the product definition orders kept apart, and it is not a
probability (strategy §2). It stays, as one *named, versioned projection* among several — not as the
asset's identity.

---

## 3. The family as it stands

### 3.1 Which asset writes what — the seed/strategy contradiction, resolved

| Asset | Code writes `[S]` | Registry says `[S]` | Status |
|---|---|---|---|
| `ka_gochara` | **only** `kala_gochara_windows_v2`, generation `'2.0'` (`writers/ka_gochara.py:120`) | seed: `kala_gochara_windows`; `count_sql` corrected to `_v2`/`2.0` by migration 670, but `target_table` still stale `[A]` | CURRENT; wrong zodiac (F3) |
| `ka_gochara_v3_century_materialize` | **both** `_v2` (`'g3_utkarsha'`) and `kala_gochara_windows` (`'3.0'`) | seed counts the *staging* copy (`LIKE 'g3_%'`) | CURRENT, **ON HOLD** |
| `ka_gochara_sweep` | retired; `kala_gochara_windows`, `'v1'` — **no registered writer exists** `[R]` | RETIRED | protected history, unrebuildable |
| `ka_gochara_resonance` | `gochara_resonance_map` | consistent | CURRENT |

Live population `[A]`: `v1` 16,297 canonical / 38,287 across 3 charts · `3.0` 914 / 1,830 across 2 ·
`2.0` 87 / 163 · `g3_utkarsha` 914 / 1,830. Both canonical charts' authority = `'3.0'`; no authority
row ever pointed at `'2.0'`, which is why F3's harm is contained.

### 3.2 Four private engines answer "when does a body reach a degree" `[S]`

| Engine | Method | Frame | Consumers |
|---|---|---|---|
| `pipeline/transit_search.py` | 0.5–1 d stepping on live Swiss + bisection | sidereal (flag) | v1, v3, Sangam, Kshetra S0, Taranga, frozen L0 `bg_sky_calendar` |
| `services/w2g` + `bg_gochara_arcs` | monotone-arc index + bisection on cubic spline | **tropical, unconverted** | `ka_gochara` |
| `ka_kshetra/stage0_kinematics.py` | Hermite + Brent 1e-6 d; episodes; dwell weight | sidereal (subtraction) | Kshetra |
| `bg_sky_calendar` writer | reuses the scan; real Swiss eclipse functions | Lahiri | L0 |

### 3.3 Recorded cost `[R][A]`

Retired sweep **35.6 h**; `ka_gochara` **6.5 h**; `ka_kshetra` 33.8 h. The century writer has **no
clean full-build measurement**: recorded completed executions of **240 s, 613 s and 3,492 s**, and
the canonical chart's 270 substeps carry timestamps spanning about **five hours** — none proven to be
one cold uninterrupted build `[A]`. PK-R-12 formally retired its "≤15–20 min" target as never-derived
`[R]`. **The ~25–36 h figure in the repository belongs to the retired sweep.** The century build is
hours, not a day — still far too slow for what it produces, and the true cold number is `[U]`.

---

## 4. Findings register

Status after verification and independent review. Full detail in v0.2 §5 and the review §A.

| id | Finding | Status |
|---|---|---|
| **F1** | Evaluation cost is ~92 % repeated event search; **64 ms per evaluation at 2 targets** | `[X]`, re-measured `[A]`. The `1.35 h × targets` model is **withdrawn** — live classes carry 14–40 targets, and the arithmetic over-predicts |
| **F2** | The legacy score is *largely* discrete — but it has **three object kinds**: point events (±5 d box), **residence spans**, interval overlaps. A single dated event list is *not* sufficient | `[X]` for the box algebra; **corrected** by `[A][X E8]`: sign-only dṛṣṭi returns a resident event stamped at the caller's window start (engine 0.45 vs filtered list 0.0). `sign_occupation` in PERMISSION behaves the same |
| **F3** | W2G solves **sidereal targets against tropical arcs** — Saturn 763 d, Jupiter 349 d, Mars 33 d from the true contact | **CONFIRMED** `[X][A]` |
| **F4** | The kernel is **not** two correct halves. W2G merges stations <0.25 d apart (finds 1 of 3 real roots), drops a 0°/360° seam tangency, swallows derivative-root exceptions as `[]`. Kshetra S0 emits nothing for a body already inside orb at horizon start, assigns noon data to midnight (`:659` vs `:501` — 7.5° for the Moon), and passes tropical speeds as sidereal slopes | **REFUTED as stated in v0.2**; defects confirmed `[A][X E8]`. A real true-node prograde excursion of 0.0477″ gives 3 direct roots and 1 from daily knots `[A]` |
| **F5** | Vedha overlay covers −60/+400 d; `quality_gates` falls back to 1.0, so "not evaluated" reads as "clear" | CONFIRMED `[S][A]` |
| **F6** | Moorti grades a whole sign-stay by the Moon's nakshatra on the *ingress date*, where its own rule says the *ingress moment*; also subtracts one reference-date ayanāṃśa across the horizon | CONFIRMED `[S][A]`; error rate `[U]` |
| **F7** | `ka_graha_sancara` PATH-A answers any instant with that day's noon position; the date cache is consulted before the `force_live` decision | CONFIRMED `[S][A]` |
| **F8** | Eight of ten W2x mechanisms are not called by the engine — but the *admitted register* is a different ten (includes W27a/b/c, excludes W30), so **nine** admitted entries are unwired; and `ClassContext` lacks the Kota/annual inputs those modules need | **PARTLY** — "cited, coded, tested, ready to wire" was too strong `[A]` |
| **F9** | Resonance targets come from a generic ontology + L1, with **no L2 structural input**; a lord qualifier such as `afflicted` is stripped; `setdefault` keeps only the first source root; 508 of 765 live rows are flagged uncited | CONFIRMED and **widened** `[A]` |
| **F10** | Registry mis-attribution | **PARTLY** — migration 670 already fixed `count_sql`; `target_table`, the seed and the century's staging count remain inconsistent `[A]` |
| **F11** | `peak_date`'s `LAMBDA_V3_ARGMAX` claims a located extremum it may not have | PARTLY — the concern stands; causal attribution to tara is **not** established (the fixture had λ ≡ 0) `[A]` |
| **F12** | Tangency produces no event; the shortest-arc function emits anti-point phantoms — **11 of 202** sentences | CONFIRMED computationally `[X]`; the "opposite of classical weighting" claim needs a source-qualified rule `[A]` |
| **F13** | `lambda_thresh=0.0` with `>=` makes every sample "active"; a λ ≡ 0 range still yields one era window. **Extended:** `_eval_single` converts *any exception* to 0.0, which the threshold then certifies as active | CONFIRMED and extended `[X][A]`. The requested-vs-completed horizon is also imprecise (2027-01-01 requested → 2026-12-31 returned) |
| **F14** | The contact signal is saturated: fixture 0.9940–1.000; **live, all 380 served rows carrying an activity value sit between 0.99964844 and 1.0** | CONFIRMED in populated served rows `[X][A]`. These are selected peaks, not a time series; "at all times" and the tara-causation claim are **withdrawn** |
| **F15** | The served engine feeds an **uncited `equal_eighths_fixture_approximation`** into every score — 147 of 202 sentences, ~59 % of search cost — and it happens **even when the context came from a real database**, because the engine passes `conn=None` unconditionally, contradicting its own docstring | **CONFIRMED on the production code path** `[X][A]` |
| **F16** | `eclipse_degree` stamps events at the caller's search-window edge | CONFIRMED `[X]` |
| **F17** | The `v1` corpus has **no database guard**: migration 588 applied, no triggers, registry empty. **Corrected:** two archive tables exist but match only 35,620 of 38,287 ids; the dump has never been restore-tested | CONFIRMED and corrected `[A]` |
| **PoC** | One gather + closed form reproduces the engine's **activity** on 319/360 instants to <1e-9, max diff 2.14e-4 | **PARTLY** — 3 of 8 primitive families were inactive and λ ≡ 0, so "exact on 7 of 8 primitives" is **withdrawn**. Speedup is 22.8× end-to-end / 4,657× query-only on the reviewer's hardware `[A]` |

---

## 5. Target design

### 5.1 Convention and time contract — first, and pinned (D-1)
One vector, carried on every contact and every publication: ephemeris source / files / version ·
time scale and **noon-UT knot origin** · **Swiss sidereal mode, Lahiri** · apparent/mean and
nutation handling · node type and Ketu construction · geocentric scope · unwrapping policy · stored
precision · interpolation and slope policy. Slopes are **derived or validated**, never assumed from
a stored tropical speed (the frame derivative is missing, and L0 negates Ketu's speed although
Ketu = Rahu + 180° `[A]`). No oracle comparison means anything until both sides request the same
quantity.

### 5.2 Geometry: the episode is the object of record
A **contact episode** is the interval a body is within a qualified orb. Exact passes are attributes
*inside* it. This survives the sub-arcsecond triple-crossing case: root multiplicity at a station
changes the pass count, not the episode. Requirements, each with a fixture:
- no station coalescing; **no swallowed solver exception** — a failure is a coverage state, never `[]`;
- explicit ownership of the 0°/360° seam, endpoints and tangents;
- **truncated episodes emitted** when a body is inside orb at a horizon edge;
- three distinct outcomes: exact crossing · in-orb closest approach · tangency to the orb boundary;
- solving on an **unwrapped, branch-qualified separation**, so anti-point phantoms are structurally
  impossible rather than merely unobserved;
- **declared angular resolution ε.** Completeness is claimed only above ε; a contact within ε of a
  station carries `near_station_unresolved` and is settled by a direct adaptive Swiss solve where a
  consumer needs it. Where neither holds: `coverage = not_proved_complete`;
- latitude retained (Kshetra's syzygy path needs it `[A]`); no distance consumer established.

### 5.3 Reuse policy (R2)
A low-level pure kernel, **one-way dependency**: numerical primitives → asset adapters. It does not
import Kshetra S0 (that inverts into a cycle when S0 later adopts the kernel). It may lift
*individually proven* functions from `w2g`/S0 under an explicit inventory with a duplicate-copy audit
entry, or extract them in an owned cross-stream packet. Adoption changes each adopter's digest
closure — recorded, not claimed away. `transit_search.py` and `ka_dasha_kala` are never edited.

### 5.4 Legacy algebra, span-aware (Stage E)
Three object kinds with explicit boundary rules: **point events**, **residence spans** (sign-only
dṛṣṭi, sign occupation, Sade-Sati phase), **interval overlaps** (vedha, with its date-rounding).
Failures and missing inputs are states, not zeros. Equivalence is proved **factor by factor** on a
non-vacuous matrix: every active primitive, longitude *and* sign-only targets, non-zero permission,
changing tara, signed and negative weights, missing overlays, exceptions, seams, horizon joins.
"Bit-identical" and "numerically equivalent within τ" are separately pre-declared. Known artefacts
(F12, F16) are *classified*, never copied into acceptance nor silently waived.

### 5.5 Typed testimony, never pre-multiplied
Background period (daśā stack per system, with applicability) · enabling interval (slow-body sign
occupation, Sade-Sati phase, AV state) · specific contact (the ledger) · inhibition (vedha, per
school, signed, de-duplicated against Vighnakara per L3-U03) · modifiers (tara, Moorti, Kota, annual
stack, real eclipses, nodal dṛṣṭi). Each carries method, source, citation state, applicability and
**evaluated / not-evaluated / inapplicable**. An operand is audited for *what it actually is* before
it appears as testimony at all (R5).

### 5.6 Identity, storage, publication
- **Contact identity** = normalized physical target + relation + astronomical input identity +
  convention vector + branch/occurrence + method policy. Class membership, weights and L2
  interpretation are **separate versioned bindings**. Horizon clipping never renames an episode; a
  correction creates a new version without rewriting issued evidence.
- **Exact-time ledger** stored separately from the **day-level windows projection** — the windows
  table holds dates `[S]`, so it cannot carry instants, brackets and tolerances.
- **Publication** = an immutable build identity **distinct from the algorithm label**; a complete
  partition manifest including valid-empty partitions; the accepted upstream generation vector; an
  atomic switch only to a *complete* candidate; readers pin one publication per request. Caches key
  on **content**, not row counts (the arc fingerprint currently hashes knot count `[A]`).
- Go-live uses `kala_gochara_authority` and its **four functional flip gates** (`527:98-102`, none
  time-based `[A]`). A soak period is supplementary observation, never a gate substitute.

### 5.7 Snapshot or exact service — the answer, with the claim narrowed
Stored knots plus an in-process interpolant beat both a day-rounded service (F7) and a serial live
one. But "exact" now means: positional error observed ≤0.314″ on a limited sample `[R]`; topology
guaranteed only above ε; direct Swiss solve where a consumer needs more. Every answer declares which
it is — snapshot, interpolated, or directly computed.

---

## 6. Disposition per asset

| Asset | Disposition | Preserved | Gate |
|---|---|---|---|
| `ka_gochara_sweep` | **Stay retired.** Rows remain in place under D-2's guard | the `v1` corpus as validation capital | restore drill proven before any successor write |
| `ka_gochara_resonance` | **Retain and repair** — keep target predicates, all source roots, qualifiers, citation status; reserve L2 binding fields (R8) | 8 target types, citation discipline | per-asset acceptance; G-5 routed to L0 |
| `ka_gochara` | **Retain the id as the single windows authority; replace the implementation.** Variants survive as *named projections*, not flattened | arc index, fingerprinting, horizon attestation, protection rails | R1's full gate set |
| `ka_gochara_v3_century_materialize` | **Supersede after migration** — its engine becomes the successor's scoring. The hold closes **by delivery**, not deferral | λ_v3, signed channels, hierarchy, chain rows, vocabularies, scoring signature, the mechanism corpus | R1 gates + G-1 amendment |
| `ka_graha_sancara` | **Repair F7** in its own packet; declare snapshot / interpolated / direct | Swiss state safety, PATH-B | Stream A/C packet |
| `bg_gochara_arcs`, `bg_sky_calendar` (L0) | **Reuse as optional optimisation only**, content-keyed; frozen L0 untouched | everything | kernel must match the in-memory path exactly |

---

## 7. The ecosystem

### 7.1 Upstream readiness

| Upstream | State for this use | Gap → owner |
|---|---|---|
| L0 `ephemeris_daily` | **Ready** — 0.314″ on a limited sample `[R]` | none; conventions are load-bearing (D-1) |
| L0 `bg_gochara_arcs` | Optional; tropical-only; fingerprint hashes counts not content `[A]` | content-keyed cache in the successor |
| L0 `bg_sky_calendar` | Ready for real eclipses, stations, Jup–Sat | none needed now |
| L0 `brahma_event_ontology` | **Partly** — five classes explicitly provisional `[A]` | G-5 → L0; never invented in L3 |
| L0 rules, AV gates, moorti table, vedha scale | usable, cited | executable-coverage map → L0 |
| L1 natal, `chart_dashas`, AV, Sade-Sati, yoga firings, **kakshya boundaries** | **Ready** — and the cited BPHS Ch.66 boundaries are exactly what H-1 needs | pin the generation vector (D4); G-4 disclosed |
| L2 Bodha mechanisms | Ready upstream, **unused here** (F9) | R8 minimum slice |
| L3 Vedha, Moorti | **not century-ready** (F5, F6) | WP9 |
| L3 Kota, Tithi-praveśa, Sudarśana | built; consumers coded, unwired (F8) | M-4, gated on G-2 for the annual stack |

### 7.2 Downstream — what must change `[A][S]`

| Surface | Problem | Work |
|---|---|---|
| MCP coverage attestation (`register_gochara_windows.ts:963-977`, `:1466-1478`, `:1041`) | an unknown generation falls into the **retired-sweep branch**; can answer `not_covered` before reading windows; intersects *current mutable* resonance targets | publication-bound coverage manifest incl. complete-empty; pinned target universe; all three tools tested |
| `reading_checklist.ts:1063-1092` | drops ids, generation, resolution, parents, `peak_basis`; `LIMIT 200` then returns 5; counts the capped set | carry evidence; honest returned / available / truncated counts |
| D8/D9 managed synthesis | non-point rows → "era context", dated points → "timing"; finer semantics lost | sentinel replay through retrieval → synthesis → delivery → retained evidence |
| Paripraśna `engine_tier` | **not wired**; no non-test caller `[A]` | prospective contract, not current protection |
| L5 prospective ledger | no field for contact id, generation or convention | specify the hand-off; receiving-owner amendment — no claim issuance under this packet |
| **cockpit Clear** (`clear/execute/route.ts:84-108,156-182`) | derives DELETEs from registry rows; does not exclude retired assets; protection registry empty | **D-2 item 3**, before any successor write |
| `w45_post_fit_rebuild.py` | mutates calibration state, can insert prospective rows, top-20 path | inventory mutating behaviour; keep L4/L5 boundaries |
| Kshetra cross-check pin (`writer.py:2313-2375`) | resonance digest from count / max-timestamp / max-id, not content | pin immutable publication content |
| `permission_curve.py`, W41/W43/W44, census/TCI, authority helpers | direct readers, un-audited | bounded discovery list — **not** claimed complete |

### 7.3 Synergy — one geometry, many readers

| Consumer | Today | With the ledger |
|---|---|---|
| `ka_sangam` (7 of 21 assets depend on it) | private live scan per predicate and mode; hidden caps | reads identified contacts; savings fund *full* predicate coverage (strategy P4) |
| `ka_kshetra` S0 | private Hermite/Brent pass | adopts the kernel — one computation, two consumers |
| Vedha / Moorti / Kota | rolling day-grade scans on a day-rounded service | century-complete interval joins; Moorti at the true ingress instant |
| `ka_kalasutra`, `ka_vighnakara`, `ka_taranga` | inherit Sangam's geometry and caps | inherit complete recurrence |
| `ka_muhurta_seva`, `ka_tulana` | separate election path | Moon-scale drill-down from the same kernel; matched candidates carry contact ids |
| L4 Phala, L5 ledger, `judgment_query`, Paripraśna | read windows | same schema plus stable evidence ids from chapter → interval → instant |

Edge typing per strategy §6.3: the kernel is a **shared definition/service** edge, not a build
dependency, so it adds no serial ordering. The ledger is a computation edge for Gochara and a
candidate one for Sangam and Kshetra. Legacy Gochara rows remain a **validation** edge for Kshetra.
No L3→L4/L5→L3 cycle is introduced.

### 7.4 Campaign machinery `[S][R]`
Campaign `t3-2026-09-11-8b884eac`; Accepted **0/22**. The successor spans Stream B (`ka_gochara`) and
Stream C (century, `w2g`, `gochara_v3`) and touches Stream A (resonance) — **Stream C leads the
numerical work; one named integration owner is required, and Stream C is not sole authority.**
`asset_analysis_accepted` and `optimization_verdict_accepted` are never gated, so WP1's contract work
can start now. One build lane, requested never self-dispatched. Every L3 source PR shifts
`layers.L3.writer_inventory_sha256`; one integrator re-pins. Generated artifacts are regenerated,
never hand-edited. Migration range 1070–1119. Known external blocker: the `data_plane_builder` grant
on `asset_registry` (STATE.md N1-C; migration 1070 deployed for it `[R]`) — WP1–WP9 do not need it.

---

## 8. Work packets

Authority: **A** = local source, tests, fixtures, disposable DB (execution-brief §3) · **N** = needs
a native method ruling · **P** = needs production build authority and the hold release.

| WP | Work | Class | Exit gate |
|---|---|---|---|
| **0** | Register through the authorized owner: F3, F13 (incl. exception→0.0→"active"), F15, F16, F17, the F4 kernel/S0 defects, the D-1 convention finding and G-4, W21's proxy operand, the coverage-branch and cockpit-Clear hazards. Adopt the reviewer's live aggregates, re-validating at implementation time | A | defects registered; **no claim** about the historical ≥2-era case beyond "misattributed diagnosis, unreconstructed" |
| **1** | **Contracts.** D-1 convention vector; field dossier, grain, natural keys, null semantics (D1); contact and projection identity (§5.6); three-way negative coverage design; input generation vector (D4); reference oracle, tolerances, ownership, file fences, immutable test vector; point-vs-span semantics; event-time vs forecast precision; registry reconciliation design (R10) | A | independently reviewed; convention pinned per D-1 |
| **2** | **Synthetic fixture suite, non-person first.** close-station cubic · real true-node excursion · seam tangency · start-inside and end-inside episodes · noon/midnight conversion · sign-only dṛṣṭi · non-zero permission · missing overlay · solver exception · negative weights · plateau ties. Plus a hand-specified factorized scorer oracle | A | every case has an expected answer derived **without** legacy output |
| **3a** | **Kernel** (§5.2–§5.3) | A | all WP2 geometry fixtures pass; candidate set independently enumerated; no silent drops; E1 retained as the *legacy defect reproducer*, with a separate convention-matched successor comparison at declared angular/time/coverage tolerances |
| **3b** | **Span-aware legacy algebra** (§5.4) — runs in parallel with 3a | A | factor-by-factor equivalence on the WP2 matrix; artefacts classified |
| **4** | **Decomposed comparison:** oracle → legacy event semantics → successor geometry → projection, on one pre-declared workload. Bounded cold/warm timings with prepare / search / query separated | A | every delta classified with its input and reference; ids stable under horizon re-partitioning. Labelled **producer prototype evidence** — not a century build result, not `DATA_ACCEPTED` |
| **5** | **Honesty fixes H-1…H-6** (§9.1) | A (pre-approved) | served-path behaviour matches its own documentation (§N.7); golden values per fix |
| **6** | **Ledger + publication** (§5.6) | A design / N schema | crash, resume, horizon extension, upstream correction, concurrent read and rollback tests |
| **7** | **Receiving contracts + minimum L2 structural slice** (§7.2, R8) | A / N | a sentinel field survives retrieval, budget, delivery and replay; a product §12.2-style question answered with preserved identities and three-way negatives |
| **8** | **Method rulings M-1…M-4** — one PR each, with comparison evidence | **N** per item | native ruling each; new continuous-score reference and peak algorithm where applicable; non-vacuous ablation on a non-empty corpus |
| **9** | **Overlays on the kernel** — Vedha, Moorti, Kota; owners in Stream A/B | A / N for Moorti method | coverage = requested horizon; Moorti compared at true ingress vs day-grade with the error rate reported; horizon-constant ayanāṃśa error measured |
| **10** | **Full benchmark, then cutover.** Strategy §5 in full → D-2 restore drill and guard → four functional flip gates → per-chart authority switch → soak → second chart → supersede century | **P** | fresh native authorization; rollback proven **through the real serving adapters** |

**First slice = WP1 → WP2 → (WP3a ‖ WP3b) → WP4.** No production data and no real chart until its own
gate. **Critical path:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 10, with 8 and 9 joining after 5.

**Stop conditions** — a timing gain overrides none of them: unresolved astronomical convention ·
unknown input masquerading as empty · missed physical topology with no declared fallback · an
unclassified divergence · identity drift under equivalent horizon partitioning · any acceptance
comparison made vacuous by zero permission or absent operands.

**Mapping to the campaign's ten dimensions.** D1/D2/D3 → WP1 (moved *before* the algorithms). D4 →
generation-vector pinning in WP1. D5 → Swiss as the convention-matched geometry oracle (WP3a) plus a
hand-specified step-function reference for scoring (WP2/3b) — **not** old-output parity, because the
old output is artefactual in places. D6 → WP4 bounded prototype, then WP10 full benchmark; no reduced
cap, horizon or resolution ever counts as a speedup. D7 → D-2 plus WP6/WP10. D8 → WP7. D9 → WP10.
D10 → does a product §12.2 question get a better-discriminated answer than today's windows?

---

## 9. The scoring split (D-3)

### 9.1 Pre-approved honesty fixes — no doctrine, WP5

| id | Fix | Why it is not a method change |
|---|---|---|
| **H-1** | Stop using the uncited `equal_eighths_fixture_approximation`. Use the real cited **BPHS Ch.66** kakshya boundaries from L1, pre-fetched and pinned; where absent, emit **not evaluated** | The engine's own docstring already says this primitive is skipped on this path. F15 shows it runs. Highest-value single fix: largest contributor to both noise and cost |
| **H-2** | A solver or evaluation exception must never become `0.0` | F13: a caught exception currently becomes a zero score that the `>= 0.0` threshold then certifies as "active" |
| **H-3** | An era window must not be declared over a range where the score is zero; report requested vs completed horizon exactly | F13 |
| **H-4** | Replace `eclipse_degree`'s window-edge timestamps with real eclipse times from L0. **Timing only** — any change to eclipse *weight* is M-4 | F16: the current timestamp is an artefact of where the caller looked |
| **H-5** | Remove the hidden cap of 3 peaks per class per decade. Store all admitted peaks; trim at serve time under §N.6 budgets | A cap indistinguishable from a true absence destroys the coverage contract. Settles Gochara's share of G-3 |
| **H-6** | Count one physical contribution once, even when several targets or rules reach it | Duplicate representation is not independent evidence (strategy L3-U02) |

### 9.2 Deferred method calls — WP8, evidence first
M-1 contact-interval activity · M-2 dwell weighting · M-3 the Moon's participation in this score ·
M-4 which mechanisms enter scoring and in what order. Each arrives as a side-by-side comparison on a
real corpus with its ablation, and each is ruled separately. **M-3 note:** the Moon stays in the
evidence under every option; ADJ-14 rejects cost-led amputation of bodies `[R]`, and my earlier
recommendation to remove it from the activity term is withdrawn. **M-4 note:** the annual-stack item
is gated on G-2.

---

## 10. Risk register

| Risk | Guard |
|---|---|
| A faster kernel delivers a **more confident wrong answer** | H-1…H-6 land before any new projection is served; WP5 precedes WP6/WP7 |
| Stage E certifies equivalence against an artefactual oracle | Acceptance is against Swiss (convention-matched) and a hand-specified reference; artefacts classified, never inherited |
| Tiny positional residual hides a wrong **number of roots** | Episode-primary geometry + declared ε + `near_station_unresolved` + adaptive direct solve |
| The oracle compares different Swiss flags, or noon data at midnight | D-1 convention vector pinned in WP1; explicit fixtures in WP2 |
| A cached arc set survives a same-size upstream correction | content-keyed caches (§5.6) |
| A residence span is replaced by a point event; an inactive factor makes a test look equivalent | span-aware algebra (§5.4); non-vacuous matrix |
| Unqualified operands become persuasive testimony | operand audit before even testimony-only admission (R5); W21 not first |
| A mis-scoped delete destroys the `v1` corpus | D-2: restore drill, then generation-keyed guard, plus the cockpit Clear fix |
| A rebuild mutates an authoritative generation in place | immutable publication identity distinct from the label; atomic switch to a complete candidate only |
| Correct new rows lose meaning on delivery | WP7 before promotion; coverage branch, checklist, D8/D9, budgets, identity propagation |
| Terminal retirement before the structural question can be answered | R8 minimum L2 slice is a precondition of terminal acceptance |
| This becomes a fourth parallel engine | explicit strangler order: successor → Sangam → Kshetra S0 → Taranga; `transit_search.py` retires when its last importer leaves |
| Cross-stream collision or digest churn | one integration owner; kernel lands unimported first; one integrator re-pins |
| Findings don't hold at production target counts | WP1 measures the real target composition first; saturation and cost both worsen with more targets, so the direction is safe, the magnitude is not |

---

## 11. Authority and what this plan does not do

Ratified as a **plan**. It authorizes no production build, migration, registry edit, lifecycle
change, deployment or hold release. The 2026-08-21 standing order stands and is discharged only at
WP10, with fresh authorization. WP1–WP5 are local and synthetic under execution-brief §3, and still
require named packet ownership and contract review. The L2 cross-layer delete guard is never
disabled. `ka_gochara_sweep` remains retired and unrebuildable. No L4/L5 model admission, claim
issuance or empirical evaluation occurs under any L3 packet here. G-1's strategy amendment is a
prerequisite of R1's consolidation, not a by-product of it.

## 12. Honest residue

Everything in §1.5, plus: the reviewer's live aggregates were read at one moment on 2026-09-20 and
are not a platform-wide audit; my executed results used a 2-target fixture with no database, so
production weights and target composition are unmeasured; the complete reader/writer inventory is a
bounded discovery list; and the four method questions in §9.2 are genuinely open, by the native's own
ruling, until evidence is put in front of him.
