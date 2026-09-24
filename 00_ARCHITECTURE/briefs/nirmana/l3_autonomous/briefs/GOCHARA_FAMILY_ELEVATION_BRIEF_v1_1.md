---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: GOCHARA_FAMILY_ELEVATION_BRIEF
version: "1.1"
status: SUPERSEDED
superseded_by: GOCHARA_FAMILY_ELEVATION_BRIEF_v1_2.md  # v2 template group shape; adds served-owner (N-5), Contact persistence (N-7), overlays, walkthrough
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 2ea6becd… (CURRENT_STATE §1)"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["ka_gochara", "ka_gochara_resonance", "ka_gochara_v3_century_materialize", "ka_gochara_sweep (protected-retired, no producer row)", "L3-U04/U11 packets P-1..P-3", "L3-U02 obligation V-1 (Sangam-owned)"]
goal_objective: "Make the Gochara family's served contact evidence honest and discriminating — cited operands, F06 completeness states, one witness per physical contact — on a kernel that solves contacts instead of sampling them; reach PRODUCER_READY without a production build."
source_revision: "origin/main c58e86662e692e678f64934f1689ccaa0fdcd7d7 (2026-09-22); evidence scripts executed in worktree madhav-l3/integration @ 5d8252dbe; accepted W2 content (47131772b) verified present on main by content"
live_measurement: "2026-09-22, Cloud SQL madhav-astrology:asia-south1:amjis-postgres via cloud-sql-proxy 127.0.0.1:5433, role amjis_app, transaction_read_only=on. Catalog and aggregates only; no private narrative rows; no write attempted. Queries in Appendix B."
accepted_upstream_contract: "the nine blobs in MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md §1; W2 first-frontier source packet 47131772b (SOURCE_PACKET_ACCEPTED); physical W1 HELD"
implementation_owner: "<unassigned — one writer; Stream C proposed as numerical lead, not sole authority>"
independent_review_owner: "<unassigned — not the author>"
release_authority: "NONE"
may_touch:
  - platform/python-sidecar/services/gochara_kernel/**            # NEW pure module, unimported until adopted
  - platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py
  - platform/python-sidecar/services/ka_gochara_resonance/writer.py
  - platform/python-sidecar/services/gochara_v3/{engine,interval_solver,threshold,resolution_hierarchy}.py   # honesty fixes H-1..H-6 only
  - platform/python-sidecar/tests/l3/**
  - "kala_gochara_windows_v2 WHERE generation='2.0'; kala_gochara_v2_build_state WHERE generation='2.0'; gochara_resonance_map (per-chart partition)"
must_not_touch:
  - platform-mcp/src/tools/kala_views/**
  - platform-mcp/src/tools/retrieval/register_gochara_windows.ts     # Pūrṇa-owned; interface packets only
  - applied migrations 1033–1070; supabase/migrations/1035,1036
  - .github/workflows/deploy.yml
  - "kala_gochara_windows WHERE generation='v1'"                     # protected-retired snapshot
  - "kala_gochara_windows WHERE generation='3.0'; kala_gochara_windows_v2 WHERE generation LIKE 'g3_%'"   # century's partitions, its hold stands
  - platform/python-sidecar/pipeline/transit_search.py; services/ka_dasha_kala/**   # frozen digest closures
  - platform/scripts/seed/asset_registry_seed.ts                      # cross-campaign shared; target_table HELD (CURRENT_STATE §4.1:133)
  - services/ka_kshetra/**; services/ka_sangam/**                     # sibling owners
target_state_data_plane: "PRODUCER_READY (Strategy §7). DATA_ACCEPTED requires physical W1 — HELD."
target_state_campaign: "t3-2026-09-11-8b884eac: no event today for any Kāla asset. This brief can earn asset_analysis_accepted (never gated); nothing beyond."
wave: "W3 (Strategy §6.4) for ka_gochara; W2 for ka_gochara_resonance (accepted source, physical held); century: W3 after its hold"
depends_on_phase_1: "1.1 close B1 (is_active on Clear; registry truth; real guard on generation='v1'); 1.2 SELECT grant on kala_gochara_windows_archive_20260805 for the restore identity"
supersedes: GOCHARA_FAMILY_ELEVATION_BRIEF_v1_0.md (retained, SUPERSEDED — Strategy §6.4 shape; pre-W0-delta)
carries_forward: GOCHARA_FAMILY_ELEVATION_PLAN_v1_0.md D-1, D-3, R1–R10 (D-2 sequence re-ruled here as N-1)
---

# Gochara family — asset/interface execution brief

Observation labels (Layer contract §4): `SRC` direct_source_read · `MEAS` generated_measurement
(`briefs/evidence_gochara/E1–E8`, `OUTPUT_2026-09-20.txt`) · `RUN` runtime_observation — **re-measured
live 2026-09-22 against production, read-only** (Appendix B); `RUN-inh` marks a value still
inherited from ASTRA_REVIEW_GOCHARA_PLAN_v0_2 §B or the readiness arc · `RCPT` historical_receipt · `INF` inference.

## 1. Admission and exact authority
Header above. Not executable until the native approves and the execution task opens a bounded goal.
Proposes only the semantic delta in §4; infers no authority from code, migrations, tests or holds.

## 2. Current-state evidence (cite, do not restate)

**Identity and registry.** Field-register census #4 `ka_gochara` → `kala_gochara_windows_v2` (gen 2)
+ `kala_gochara_v2_build_state`; #5 `ka_gochara_resonance` → `gochara_resonance_map`; #6 century →
`_v2` staging (gen 3) + `kala_gochara_windows` protected production (gen 3) + shared build state;
#20 `ka_vedha_gochara`. **This is the identity answer; T5 "Tension 1" is closed there** — the
"which instrument is authoritative" question in v1.0 §4 is withdrawn. `ka_gochara_sweep` is a
tombstone with no producer row ("Protected-retired exclusion"). Contribution register §5 rows
138–141, 144. Strategy rows L3-A05, A13, A14, H01. W0 disposition: CURRENT_STATE §4.1:125,128,
133–135 — `ka_gochara` *"after resonance; seed target mismatch held"*; century *"specific hold;
protected v1 coexistence required"*; Vedha *"first frontier; close hidden edge"*.

**The registry `target_table` mismatch is HELD, not discovered.** CURRENT_STATE §4.1:133; Lane C
A.1/F2 (`ka_gochara.py:120,336,362` `SRC`). The seed lives in `asset_registry_seed.ts`, a shared
cross-campaign file; REDIRECT_002 §2 assigns finding and stating its release condition to Phase 1.1.
Migration 670 §4 already corrected `count_sql`; 1018 pins the digest to `_v2`/`2.0` `SRC`.

**Files.** `writers/ka_gochara.py`; `services/w2g/{arcs,crossings,solver,materialize,db_source,tiers}.py`;
`services/ka_gochara_resonance/writer.py`; `writers/ka_gochara_v3_century_materialize.py`;
`services/gochara_v3/**` (8,441 LOC non-test `MEAS`); `services/ka_gochara/service.py`
(`GocharaTransitService` — live compute over `pipeline/transit_search.py`, **no table**, `SRC`).

**Algorithm, in one line each.** `ka_gochara`: arc-solved contact instants (`bg_gochara_arcs` ×
resonance targets) scored by v1 `compute_lambda_e`, ±3-year progressive horizon disclosed in
`horizon_status` (L3-A13 asks this be *preserved as bounded coverage*). Century: weekly-grid sampling
of λ_v3 + bisection + 50-sample peak + ±7 d day-refine, 270 substeps `SRC`. Resonance: ontology +
L1 facts → targets, 27 classes; **W2 accepted source requires a non-empty candidate for all 27 before
chart-wide replacement** (on main by content: `writer.py:518-549` `SRC`).

**Consumers, with search boundary** (`platform/`, `platform-mcp/`, non-test):
- `kala_gochara_windows` gen `3.0` → MCP `register_gochara_windows.ts` (authority-filtered),
  `reading_checklist.ts`, D8/D9 adapters, Kshetra stage-4 cross-check `SRC`; authority = `'3.0'`
  both canonical charts `RUN`.
- **`kala_gochara_windows_v2` gen `2.0` — real consumers:** `scripts/w2g_equivalence_report.py`
  (validation) only. The register's receiver claim "gochara service; MCP register_gochara_windows"
  (rows 57–79) is **not borne out**: the service reads no table and the MCP tool never names `_v2`
  `SRC`. Disposition **`UNRESOLVED_USE`** pending register amendment; no live serving caller found
  within scope.
- **Sangam reads the Gochara *service*, not the materialization** (`writers/ka_sangam.py:36`;
  CURRENT_STATE §4.1:135) — the declared edge `ka_sangam → ka_gochara` is undemonstrated as a
  materialization edge. **Sangam reads `kala_vedha_gochara` undeclared** (`ka_sangam/engine.py:73`;
  seed `depends_on` omits it `SRC`; §4.1:128). Both closures are Sangam-owned (W0_DELTA_SANGAM item 1);
  carried here as obligation **V-1**, §5.
- Century declared inputs Kota/Tithi: **proposed use, not consumption** — `ClassContext.fetch` reads
  vedha, moorti, AV gates, Sade-Sati only `SRC`; §4.1:134; Strategy §6.3.

**Generations.** No L1/L2 head ever opened `RUN`; design frozen (FOUNDATION_SAFETY §6), physical W1
held (§8 item 2). Live `RUN`: `kala_gochara_windows` 40,117 = **38,287 `v1`** (3 charts, 6 classes) + **1,830 `3.0`**
(2 charts, 27 classes); `kala_gochara_windows_v2` 1,993 = **163 `2.0`** (2 charts, 13 classes) +
**1,830 `g3_utkarsha`**. Authority `'3.0'` on both canonical charts.

**Cost.** Unit costs only: 64 ms/evaluation at 2 targets, ~92 % repeated search; 0.013 ms/instant
closed-form once events are known `MEAS`. Century executions `RUN`: three `complete` rows at **239.7 s / 613.5 s / 3,491.6 s**; the canonical
chart holds **270/270** distinct substeps accumulated over a **5.02 h** span (2026-08-11
17:17→22:18Z) across attempts, so the longest single completed execution is **58.2 min** and no
cold-from-empty full build is proven. The ~25–36 h figure belongs to the retired sweep (35.6 h `RCPT`). Full
profiles: cite `KALA_COST_PROFILE_v1_0.md` when it lands; never `estimated_seconds`.

**Ladders.** Data-plane: `PLAN_REVIEWED` reached by this document. t3: **no event**.

### What is new since W0 (live-path stated for each)
- **B1** — Clear route resolves a spec by `EXPLICIT_CLEAR_OPS` → **`count_sql`** → `target_table`
  (`execute/route.ts:160-182`; `assetClearSpec.ts:29-46` prefix-swap keeps the WHERE) `SRC`. No gochara
  entry in `EXPLICIT_CLEAR_OPS`. So `ka_gochara_sweep.count_sql` derives to
  `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'` — exactly the protected
  rows (Lane C F1). `ka_gochara`'s derives to `_v2`/`2.0`; its stale `target_table` is **unreachable**
  while `count_sql` is non-null. **Re-measured live:** `ka_gochara.count_sql` is the `_v2`/`'2.0'` form;
  `ka_gochara_sweep` is `is_active=false, catalog_status='RETIRED'` with `count_sql` scoped to
  `generation='v1'`; `amjis_app` holds DELETE on `kala_gochara_windows`. **Lane C F1 is the
  mechanism; the readiness package §B1 "excluding retired assets would not fix it" does not hold** —
  a lifecycle filter removes the only asset whose clear spec resolves onto the protected partition. Live path:
  deployed endpoint, `allowedScopes=['per_chart']` for non-admins (`clear/route.ts:93`) — reachable by
  construction; invocation history `UNKNOWN`. **Phase 1.1 dependency.**
- **B2** — `execute/route.ts:95-96` cites a migration-540 guard; 588 dropped all three triggers and
  functions and emptied `build_protected_assets` (on main; applied 2026-08-23 `RUN`; Lane C F3).
  W0 fence 2 / W0_DELTA item 3 state the 566 guard *"is working; it is not yours to weaken."*
  **Live-refuted 2026-09-22:** zero non-internal triggers on any `kala_*` table, zero
  `kala_gochara_windows_protect*` functions, `build_protected_assets` = 0 rows. Decisive ordering —
  the century's stored `last_error` "RaiseException: BUILD-PROTECTED…" is stamped
  **2026-08-21T13:37:44Z** while `588_remove_asset_build_protection.sql` applied
  **2026-08-23T05:33:15Z**: the message predates the guard's removal by two days and is a residue,
  not live enforcement. Nothing is weakened here; protection must be *created* (Phase 1.1).
- **B3** — **live-confirmed:** `data_plane_builder` has `SELECT=false` on *both* recovery sources
  (`kala_gochara_windows_archive_20260805`, `kala_gochara_windows__ssv_20260728c`) while holding
  `DELETE=true` on `kala_gochara_windows` — the identity that can destroy the corpus cannot read its
  own recovery source. Archive union covers **35,620 of 38,287** `v1` ids (2,667 uncovered); the dump
  has never been restore-tested. **Phase 1.2 dependency.**
- **B5** — `ka_gochara.py:268` falls back to `date.today()`; `w2g/materialize.py:140` forbids exactly
  this `SRC`. Horizon moves with the clock → non-deterministic rebuild; defeats the 1018 digest `INF`.
  Context §4 defect class, in this family.

## 3. The failure — one falsifiable problem

| Field | Content |
|---|---|
| Observed | The served v3 engine calls `kakshya_cell_crossing(..., conn=None)` unconditionally, even when its `ClassContext` came from a real DB; the primitive then emits `equal_eighths_fixture_approximation` events (`uncited_extension=True`, default strength 0.5) that enter `_compute_activity_v3`. Fixture: **147/202** activity sentences, **59 %** of evaluation cost; activity sits in [0.9940, 1.0]. Live: all **380** served gen-3.0 rows carrying an activity value lie in [0.99964844, 1.0]. |
| Evidence | `engine.py:1063-1112,1133-1137`; `primitives.py:664-719` `SRC`; `E3`,`E4` `MEAS`; review §A F15 `RUN` |
| Expected contract | F04 (source testimony ≠ computed fact); F06 (`unqualified` must not read as `applied`); Strategy §3 Temporal testimony (exact evidence roots); CLAUDE §N.7 item 4 (docstring says skipped — it runs) |
| Defect class | **unqualified** + **detector mismatch** |
| Impact | L3-Q01/Q02 lose their distinction: every window is ≈ equally "active", so nearest-vs-stronger and now-vs-background collapse; served windows are daśā windows modulated by tara `INF` |
| Non-claim | Does not establish the full-century distribution (380 rows are selected peaks), nor which factor selects production peaks, nor any doctrinal claim about kakshya |

Ranked secondaries (skill §5 order): F3 wrong-zodiac contacts in `ka_gochara` — Saturn 763 d, Jupiter
349 d, Mars 33 d from the true contact `MEAS`, **not served** (authority `'3.0'`), latent; F13
`lambda_thresh=0.0` with `>=` and exception→`0.0`→"active" (`:1940`; `threshold.py:393`;
`interval_solver.py:116-136`); B5 non-determinism.

## 4. Semantic change and expected distinction

**Smallest sufficient delta, in order.** (i) Inputs honest: H-1…H-6 (D-3 pre-approved). (ii) Frame
and determinism: D-1 convention, B5 removed. (iii) Geometry: a pure kernel that solves **contact
episodes** on sidereal arcs instead of sampling λ. (iv) Typed testimony with F06 states and an
`independence_group`. (v) Windows unchanged in shape and key; instants live in a separate ledger.

**L3-Q served** (context §2; no local portfolio): **Q08** primary and currently failing — *searched
horizon, resolution, method/target coverage, unavailable inputs* become expressible; proof: *a window
just outside a searched partition must not become a universal denial* (three-way negative). **Q01/Q02**
primary — contacts discriminate again; proofs per Strategy §2. **Q03** contributing only until R8's L2
binding; **Q05/Q09/Q10** contributing via `comparable_with`, D-1, Moon drill-down.

**Typed qualification — no scalar.** Every row/testimony carries `epistemic_class` (F04:
`computed_fact` for geometry; `qualified_rule` for cited gates; `interpretive_inference` for graded
projections), `completeness_state` (F06 six states; `unavailable` where an overlay does not cover the
span — the F5 case; `unqualified` for fixture/provisional operands; **no 1.0/0.0/empty fallback**),
`operator_role` (F12), Strategy §3 Temporal testimony incl. **silence** and **independence_group**,
and `comparable_with` (λ_v3 ≠ λ_e ≠ Sangam ICC). Extends `ka_taranga`'s `tier_basis` discipline.
v1.0's `precision_class` is re-expressed as `time_basis` + `bracket_days` + `tolerance_arcsec` +
`claim_grain` — qualification, not confidence.

**DP07/DP08 fields present:** instant with bracket/tolerance, timezone-explicit (UTC) noon-knot origin,
horizon requested/completed, geometry branch, recurrence via stable `contact_id`; structural identity
reserved (R8), applicable clocks from L1, enabling/inhibiting as separate testimony, coverage/gap.

**Time discipline.** D-1: Swiss sidereal mode, Lahiri (the two repo methods differ by nutation, up to
16.5″ `MEAS`). No `date.today()` (B5); `DATE` columns unchanged, so no naive-`timestamptz` path.
Node model: **N-4** — Gochara inherits L1's (`l1_positions.py:128` TRUE_NODE `SRC`) read from a
`fact_id`; the L0/L1-vs-DAR (MEAN, FORENSIC 49.04°) drift is routed to L1's owner (v1.0 §14).

**Old vs new.** Positive: a within-orb slow contact yields an episode with `exact_crossing` true/false,
not a ±5 d box. Negative: no L1 kakshya boundary → `unqualified`, not a 0.5-strength event. Boundary:
seam tangency at 0°/360° and start-inside episodes emitted (both dropped today `MEAS E8`). Missing:
overlay gap → `unavailable`, not gate 1.0. Duplicated: one physical contact via three targets → one
witness, `independence_group` shared.

**Baseline** (Execution Brief §1): today's authority-`3.0` windows for the same chart, class,
horizon, evidence budget. **Value metric:** three-way negative correctness; nearest-vs-stronger
discrimination on `KALA_BASELINE_v1_0.md` questions. **Ablation:** remove `independence_group` → agreement
counts inflate; remove F06 states → "unavailable" reads as "clear" again.

**Deferred method calls (D-3):** M-1 contact-interval activity (= June brief I-17), M-2 dwell, M-3 Moon
participation (ADJ-14 keeps Moon evidence), M-4 mechanism wiring (operand audit first; W21 substitutes
`min_sav_score` for bindus `SRC`). Each is a native ruling with side-by-side evidence, not this delta.

**Century (Strategy §5, no deferral):** the **qualified compact substrate** — the contact-episode
ledger, complete for the declared body set and horizon at a declared resolution ε, with
`near_station_unresolved` above ε — and windows as its **refinement projection**, preserving natural
key, parent ids and both table roles (P3). This is its *method* disposition (**N-3**); its lifecycle
disposition and hold stand; no retirement proposed.

## 5. Preservation, migration, history and rollback

| Component | Disposition | Preserved |
|---|---|---|
| `ka_gochara_sweep` rows (`v1`) | `PRESERVE` / `HISTORICAL_RESTRICTED` | all; outside every generation and delete scope (FOUNDATION_SAFETY §6.7) |
| `ka_gochara_resonance` | `ENRICH_CORRECT` | 8 target types, citation flags, W2 27-class gate; **fix** first-root-only `setdefault` and stripped `afflicted` qualifier `RUN`; reserve L2 columns |
| `ka_gochara` writer | `ENRICH_CORRECT` | ±3 y horizon *as disclosed bounded coverage* (L3-A13), fingerprinting, `horizon_status`; **replace** tropical-arc join, `date.today()` |
| `w2g` arc index, Kshetra S0 physics | `INTEGRATE` into the kernel by proven function, one-way dependency, no S0 import; S0 defects (station coalescing, seam, start-inside, noon/midnight `MEAS E8`) **not** imported |
| century engine (λ_v3, hierarchy, chains, vocabularies, mechanisms) | `PRESERVE` now; `INVESTIGATE_CONSOLIDATION` under R1's full gate set + G-1 amendment | everything; both table roles |
| `_v2` gen `2.0` rows | `UNRESOLVED_USE` | register amendment before any disposition |
| `GocharaTransitService` | `PRESERVE` | Sangam's actual input; candidate later adopter of the kernel |

**Protected classes:** `v1` snapshot; issued claims (F17/U10); Bhavishya outcomes. **Fences** 1–3
binding: every DELETE/UPSERT carries chart + event_class + generation (+ era/resolution for v3); one
writer, one publication owner. **Cascade:** none of this family's tables is an FK cascade source
(CURRENT_STATE §4.2); non-FK referrers — Kshetra stage-4 cross-check, Gochara fact/source/parent
structures — pinned by publication content, not `max(id)`.

**Generation binding.** Under the frozen design (§6 items 1–4): input vector = L0 knots/arcs/rules +
L1 facts/dashas/AV/Sade-Sati/kakshya + resonance partition; empty partition is an explicit result;
candidate ≠ selected head; rollback re-points the head. **If physical generations are not available at
execution:** pin by content digest over the same relations and label the manifest `content_pin`; no
fall-through to mutable `public` rows either way. Serving cutover per chart via `kala_gochara_authority`
and its four functional gates (527:98-102 `RUN`); soak is observation only.

**History/rollback (N-1 — re-rules v1.0 D-2's sequence):** (a) Phase 1.1 closes the deletion path —
lifecycle filter on both Clear registry queries plus the B2 comment — needing no data move or grant;
(b) Phase 1.2 grants the archive SELECT; (c) restore drill covering all 38,287 rows, content-checked;
(d) a guard keyed on **(table, generation)** for `'v1'` — and `'3.0'` under the writer that produces
it — never `asset_id` (Defect D-02 shape). Any migration authors at `platform/migrations/1071+`
(REDIRECT_002 §4). **Retirement forbidden** until successor, caller migration, provenance transfer and
reversible rollback are proved and separately authorized (contract §5).

**Interface obligations (Pūrṇa-owned code; L3-owned tests):**
**P-1** coverage attestation routes an unknown generation to the retired-sweep branch and can answer
`not_covered` before reading rows; intersects mutable resonance (`register_gochara_windows.ts:963-977,
1466-1478,1041` `SRC`) → resolve against the publication manifest incl. complete-empty.
**P-2** `reading_checklist.ts:1063-1092` drops ids/generation/basis, caps 200, returns 5, counts the
cap → honest returned/available/truncated. **P-3** L5 prospective ledger lacks `contact_id`/generation
fields → hand-off specified; no claim issuance here. **V-1** (L3-U02, Sangam-owned): declare
`ka_vedha_gochara` as a `counterevidence` computation edge; re-type `ka_sangam → ka_gochara` as a
service edge; this brief supplies the register rows and the sentinel, Sangam supplies the fix.

## 6. Focused proof matrix (fixture boundary: synthetic non-person cases; disposable DB; no live chart until its gate)

| Proof | Test · expected · detector |
|---|---|
| Positive | Cubic with stations 1.4/1.6, target 100°, orb 1° → **3** roots; seam `[357.75,359.75,359.75,357.75]` target 0° → ≥1 contact; start-inside orbit → 1 truncated episode. Detector: `E8` re-run returns 1 / 0 / `[]` on the legacy path today `MEAS`. |
| Negative | Chart lacking L1 kakshya boundaries → `completeness_state='unqualified'`, zero kakshya sentences; overlay gap → `unavailable`. Detector: fixture that today yields 147 fixture sentences / gate 1.0. |
| Relevant influence | Move one natal target by 1° → only that target's episodes shift; others byte-identical. |
| Irrelevant control | Shuffle resonance row order / target list → identical rows and ids (guards #2527's class). |
| Duplication | Same physical contact via 3 targets → one `independence_group`, activity unchanged vs 1 target. Detector: today's noisy-OR triples it. |
| Context/missingness | Wrong chart, wrong ayanāṃśa, wrong generation → reject/isolate; `applied` / `inapplicable` / `unavailable` / `unqualified` / `unexplored` distinct in output, never a 0. |
| Boundary/precision | Horizon end on a partition seam → same `contact_id` both sides; kernel vs Swiss under the **same** flags (D-1) within declared ε; near-station contact carries `near_station_unresolved`. |
| Delivery | Sentinel in `independence_group` of a low-ranked row survives P-1/P-2 paths to the saved result (test L3-owned; NOT_RUN until Pūrṇa lands). |
| Revision | Change an L1 kakshya boundary → new generation, old consumed generation preserved, head re-point back works. Rebuild same inputs on two dates → byte-equal (kills B5). |
| Value | `KALA_BASELINE_v1_0.md` Q08 questions: today's answer vs new three-way negative; Q02 nearest-vs-stronger with named criterion. Tier `EXPLANATORY_DISCRIMINATIVE_VALUE`, separate from correctness. |
| Evaluation | `not_applicable` — no empirical outcome claim; L5 not opened. |

Tiers kept separate (F24). Planned ≠ passed (F23). Every row's detector must be able to return false.

## 7. Implementation and review discipline
One writer surface (isolated worktree off `main`); no concurrent mutation of shared refs. Order: WP1
contracts (convention vector, field dossier, identity, coverage design) → WP2 synthetic suite → WP3a
kernel ‖ WP3b span-aware legacy algebra (point events / residence spans / interval overlaps — a single
dated event list is **not** sufficient `MEAS E8` sign-only dṛṣṭi) → WP4 decomposed comparison +
bounded timings → WP5 H-1…H-6 → WP6 ledger/publication → WP7 P-1..P-3 + minimum L2 slice (R8) →
WP8 M-1..M-4 rulings → WP9 overlays → WP10 full benchmark and cutover (**P** authority). Absent
authority is `NOT_RUN`. Stop conditions: unresolved convention · unknown-as-empty · missed topology
without declared fallback · unclassified divergence · id drift across partitions · vacuous comparison.

## 8. Terminal evidence packet (what execution will return)
Approved brief + upstream pin; commits and files; old/new examples per §4; preservation/generation/
rollback evidence incl. the drill; raw commands per §6 row; reviewer identity and findings; state
reached — **`PRODUCER_READY` at most** — and unreached (`DATA_ACCEPTED` needs W1; `CONSUMER_INTEGRATED`
/`VALUE_EVALUATED` have no admissible event type, native decision 2); residual risks and decisions
returned; confirmation that `v1`, `'3.0'`, `kala_views/`, the seed, `transit_search.py` were not touched.

**Decisions returned to the native.** **N-1** re-sequence D-2 (§5). **N-2** withdrawn — identity is
settled by census #4/#6. **N-3** century method disposition = compact substrate (§4). **N-4** node
convention inherits L1; L0/L1-vs-DAR drift routed to L1. Deferred: M-1..M-4. Not decided here: the
five Phase-2 decisions; any retirement; any guard weakening; `convergence_commit`; orchestrator contract.

---

## Appendix — analysis lenses A–J

**A Identity/intent.** Chart-derived data assets (#4, #6) + one T0 target asset (#5) + one tombstone;
epistemic type deterministic derivation (geometry) with an interpretive projection (λ). Purpose: the
contact layer of time (Product §3.10). Disposition: `ENRICH_CORRECT` now; consolidation later under R1.
**B Inputs/DAG.** Declared vs actual: Kota/Tithi→century proposed not read; Sangam→`ka_gochara`
service not materialization; Sangam→Vedha undeclared; `bg_gochara_arcs` optional, content-keyed. Fan-out:
resonance→3. Shared writes: fences 1–3. No cycle introduced; kernel is a shared-definition edge.
**C Correctness.** Invariants: λ ∈ [0,1]; activity noisy-OR; episode count ≥ pass count. Detectors that
fail today: E1 (frame), E3/E4 (fixture operand), E5 (era=range), E8 (stations, seam, start-inside).
Convention pinned (D-1). Precision claims bounded by ε; `0.314″` is a sample, not a bound.
**D Data sufficiency.** 765 targets / 27 classes on the canonical chart, **14–40 per class, mean 28.3**, 508 uncited,
31 negative-weight `RUN`; five provisional
ontology classes → L0 owner (G-5). Enrichment sought: L2 structural binding (R8); no row-count goals.
**E Consumers/reuse.** Real readers listed in §2; `_v2` gen-2.0 `UNRESOLVED_USE`; four private transit
engines → one kernel by strangler order (successor → Sangam → Kshetra S0 → Taranga); `transit_search.py`
retires only when its last importer leaves.
**F AI/product readiness.** Density: P-1/P-2 packets; catalogue-vs-confirmed guarded by F06; narration
reads cited facts (§N.7); empty/partial states explicit. Retrieval keys: `contact_id`, generation.
**G Build efficiency.** Measured hotspot: repeated per-evaluation search (92 %), kakshya 59 % `MEAS`.
Candidate: solve-once kernel + closed-form projection (0.013 ms/instant `MEAS`). Target: **not stated**
until `KALA_COST_PROFILE_v1_0.md`; output-identity method = WP4 decomposed comparison.
**H Reliability.** Idempotency per fences 1–3; resume via fingerprints (content-keyed, fixing 1018's
B5 exposure); timeout from measured work only; integrity = 670 conjuncts + digest 1018; recovery
requires B3 closed; boundary: `data_plane_builder` grants.
**I Change packet.** May/must-not-touch in header; migrations at 1071+; wave W3; DAG order WP1→WP10;
rollback by head re-point and authority flip-back through real adapters.
**J Final evidence.** Baseline `KALA_BASELINE_v1_0.md`; commits; review verdict; **no** deployed revision,
rebuild receipt or freeze claimed by this brief.

---

## Appendix B — live measurement record, 2026-09-22

Instance `madhav-astrology:asia-south1:amjis-postgres` (Cloud SQL, POSTGRES_15) via
`cloud-sql-proxy 127.0.0.1:5433`; role `amjis_app`, `transaction_read_only=on`
(`rolconfig`: `statement_timeout=1800s`, `idle_in_transaction_session_timeout=600s`). Catalog,
privilege and aggregate reads only; no private narrative row read; no write attempted; no build,
migration or campaign event. Reproducible read-only by any authorized operator.

| # | Question | Measured result |
|---|---|---|
| 1 | Session identity/mode | `amjis_app` · db `amjis` · `transaction_read_only=on` |
| 2 | `asset_registry` rows `ka_gochara%` | `ka_gochara` CURRENT/active, `target_table='kala_gochara_windows'` (stale), `count_sql`→`_v2 … generation='2.0'`, floor 83 · `ka_gochara_sweep` **RETIRED, is_active=false**, `count_sql`→`kala_gochara_windows … generation='v1'`, floor 16297, `superseded_by='ka_gochara'`, `data_disposition='RETAINED_AS_CAPITAL'` · century `target_table='kala_gochara_windows_v2'`, `count_sql`→`_v2 … LIKE 'g3_%'`, floor 914 · resonance floor 762 |
| 3 | Protection state | non-internal triggers on `kala_*` = **0**; `kala_gochara_windows_protect*` functions = **0**; `build_protected_assets` = **0** rows |
| 4 | Migration order | 540 applied 2026-08-06 · 566 applied 2026-08-10 · **588 applied 2026-08-23T05:33:15Z** |
| 5 | Row census | `kala_gochara_windows`: `v1` 38,287 (3 charts, 6 classes), `3.0` 1,830 (2 charts, 27 classes) · `_v2`: `2.0` 163 (2 charts, 13 classes), `g3_utkarsha` 1,830 |
| 6 | Serving authority | both canonical charts `'3.0'` (flipped 2026-08-11) — no `'2.0'` row is served |
| 7 | Recovery coverage | archive ∪ ssv covers **35,620 / 38,287** `v1` ids; **2,667 uncovered** |
| 8 | Privileges | `data_plane_builder`: archive SELECT **false**, ssv SELECT **false**, `kala_gochara_windows` SELECT true / **DELETE true** · `amjis_app` DELETE on `kala_gochara_windows` **true** · `retrieval_census_ro` SELECT true |
| 9 | Resonance targets (canonical chart) | 765 across 27 classes; **14–40 per class, mean 28.3**; 508 uncited; 31 negative weight |
| 10 | Century runtime | `complete` at 239.7 s / 613.5 s / **3,491.6 s**; substeps **270/270**, span 5.02 h across attempts |
| 11 | Throughput states | `ka_gochara` lit (87 / 76 rows) · resonance lit (765 / 753 / 77) · sweep **error "no writer registered"** (the non-rebuild detector, working) · century **error, `last_error` "BUILD-PROTECTED…" stamped 2026-08-21**, i.e. two days before 588 dropped the guard |

**What this changed in the brief.** B1's mechanism, B2's refutation and B3's asymmetry move from
source-derived to live-confirmed; the population, target-composition and century-runtime figures are
now measured rather than inherited. **No finding was reversed by measurement.** Still not measured:
whether the Clear path has ever been invoked (no audit trail queried), the full-century activity
distribution, and any value/consumer claim.
