---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: GOCHARA_FAMILY_ELEVATION_BRIEF
version: "1.2"
status: SUPERSEDED
superseded_by: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md (consolidated this brief; ratified 2026-09-23 per GOCHARA_RULING_SHEET_v1_0.md). Retained as the measurement record for Appendices B–E."
instantiates: KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md (group shape) via ELEVATION_PROMPT_GOCHARA_FAMILY_v2.md; stages 0–2
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 2ea6becd… (CURRENT_STATE §1)"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["ka_gochara_resonance", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_vedha_gochara", "ka_moorti_nirnaya", "ka_kota_chakra (proposed-use member)", "ka_gochara_sweep (protected history, no producer row)", "L3-U11 packets P-1..P-3", "L3-U02 obligation V-1 (Sangam-owned)", "service contract S-1 (owed to Sangam)"]
goal_objective: "Make this family the layer's contact geometry in fact: persist the Strategy §3 Contact object it currently computes and discards, serve one honestly-owned generation, replace sampling with solving under P3's equivalence contract, and reach PRODUCER_READY without a production build."
source_revision: "origin/main c58e86662e692e678f64934f1689ccaa0fdcd7d7; readiness tip 86ee604ea; evidence scripts executed @ 5d8252dbe; W2 47131772b present on main by content"
accepted_upstream_contract: "CURRENT_STATE §1 nine blobs; W2 first-frontier source packet (SOURCE_PACKET_ACCEPTED, incl. resonance 27-class completeness gate writer.py:518-549); physical W1 HELD"
live_measurement: "2026-09-22, amjis-postgres via cloud-sql-proxy, role amjis_app, transaction_read_only=on; catalog/privilege/aggregates only; Appendix B"
implementation_owner: "<unassigned — one writer per packet; see §G>"
independent_review_owner: "<unassigned — not the author>"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/gochara_kernel/** (NEW, unimported until adopted)", "pipeline/orchestrator/writers/ka_gochara.py", "services/ka_gochara_resonance/writer.py", "services/ka_vedha_gochara/**", "services/ka_moorti_nirnaya/**", "services/gochara_v3/{engine,interval_solver,threshold,resolution_hierarchy}.py (H-1..H-6 only)", "services/ka_gochara/service.py (S-1 only)", "tests/l3/**", "kala_gochara_windows_v2 WHERE generation='2.0'; kala_gochara_v2_build_state WHERE generation='2.0'; gochara_resonance_map; kala_vedha_gochara; kala_moorti_nirnaya (per-chart partitions)", "a NEW contact-ledger relation owned by ka_gochara (decision N-7)"]
must_not_touch: ["platform-mcp/src/tools/kala_views/**", "platform-mcp/src/tools/retrieval/register_gochara_windows.ts", "applied migrations 1033–1070; supabase/migrations/1035,1036", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "kala_gochara_windows WHERE generation='3.0'; kala_gochara_windows_v2 WHERE generation LIKE 'g3_%' (century partitions; hold stands)", "pipeline/transit_search.py; services/ka_dasha_kala/**", "platform/scripts/seed/asset_registry_seed.ts (cross-campaign; HELD)", "services/ka_kshetra/**; services/ka_sangam/**; services/ka_kota_chakra/** (sibling/A-stream owners)"]
target_state_data_plane: "PRODUCER_READY. DATA_ACCEPTED needs physical W1 — HELD."
target_state_campaign: "t3-2026-09-11-8b884eac: no event today; this brief can earn asset_analysis_accepted only."
wave: "W2 resonance/Vedha/Moorti (source accepted, physical held) · W3 ka_gochara · W3-after-hold century"
depends_on_phase_1: ["1.1 close B1 (is_active on Clear; registry truth; real guard on generation='v1')", "1.2 SELECT grant on the two v1 archives for the restore identity"]
supersedes: GOCHARA_FAMILY_ELEVATION_BRIEF_v1_1.md (retained, SUPERSEDED — single-asset shape; pre-v2 template)
carries_forward: PLAN_v1_0 D-1, D-3, R1–R10; BRIEF_v1_1 §2 corrections (B1 mechanism, B2 residue, B3 asymmetry, B5), all now live-confirmed
worktree_note: "This file is untracked in /Users/Dev/madhav-l3/integration (branch codex/madhav-l3-claude-code). Per INTEGRATOR_VERIFICATION_LOG 2026-09-22 18:15, brief sessions should publish from their own worktree/PR; nothing here has been git-added."
---

# Gochara family — group elevation brief (stages 0–2)

Labels: `SRC` direct source read · `MEAS` generated measurement (`evidence_gochara/E1–E8`) · `RUN`
live runtime observation, 2026-09-22 (Appendix B) · `RCPT` historical receipt · `INF` inference.

## 1. Admission and exact authority
Header above. Executable only after native approval and a bounded execution goal. Proposes the §4
delta only. Infers no authority from code, migrations, tests, holds or the template.

## 2. Stage 0 — reconcile (cite; deltas only)

**Established at W0 — inherited.** Census #4 `ka_gochara` → `kala_gochara_windows_v2` (gen 2) +
build state; #5 resonance → `gochara_resonance_map`; #6 century → `_v2` staging (gen 3) +
`kala_gochara_windows` protected production (gen 3) + shared build state; #11 Kota; #13 Moorti; #20
Vedha; sweep = tombstone ("Protected-retired exclusion"). Fences 1–3 binding. Contribution register
§5 rows 138–144. Strategy rows A05/A06/A07/A08/A13/A14/H01; §3 Contact and Search-coverage objects;
§5 P3. CURRENT_STATE §4.1: resonance *first frontier*; Vedha *first frontier; close hidden edge*;
Moorti *first frontier*; Kota *preserve; integration decision owed* (declared, not read); `ka_gochara`
*after resonance; seed target mismatch held* (:133 — **held, not discovered**; seed is a cross-campaign
shared file, REDIRECT_002 §2); century *specific hold; protected v1 coexistence required*. W2 source
accepted (`47131772b` on main by content), including the 27-class completeness gate.

**Deltas since W0, each live-path stated.**
- **B1** Clear route: spec precedence `EXPLICIT_CLEAR_OPS` → `count_sql` → `target_table`
  (`execute/route.ts:160-182`; prefix-swap keeps WHERE, `assetClearSpec.ts:29-46`) `SRC`. Live
  `RUN`: `ka_gochara_sweep` is `is_active=false, RETIRED`, `count_sql … generation='v1'`;
  `ka_gochara.count_sql` is `_v2 … '2.0'`; `amjis_app` holds DELETE on `kala_gochara_windows`. So the
  live deletion of the 38,287 protected rows runs through the **sweep's own `count_sql`** (Lane C F1);
  a lifecycle filter closes it; `ka_gochara`'s stale `target_table` is unreachable while `count_sql`
  is non-null. Reachable by any chart owner (`clear/route.ts:93`); invocation history `UNKNOWN`.
  **Phase 1.1 dependency.**
- **B2/B4** — the prompt and W0 fence 2 say *"migration 566's BUILD-PROTECTED guard — working, not
  yours to weaken."* **Live-refuted `RUN`:** 0 non-internal triggers on any `kala_*` table, 0
  `kala_gochara_windows_protect*` functions, `build_protected_assets` = 0 rows; 588 applied
  **2026-08-23T05:33Z**; the century's stored `last_error "BUILD-PROTECTED…"` is stamped
  **2026-08-21T13:37Z** — two days *before* the guard was dropped. It is a residue. **Nothing is
  weakened here; the guard must be created** (Phase 1.1, keyed on (table, generation), never
  `asset_id` — Defect D-02's shape, 588's own header).
- **B3** `RUN`: `data_plane_builder` SELECT=false on both v1 archives, DELETE=true on
  `kala_gochara_windows`; archives cover 35,620/38,287 ids. **Phase 1.2 dependency.**
- **B5** `ka_gochara.py:268` `date.today()` fallback defeats `w2g/materialize.py:140`'s discipline
  `SRC` → horizon moves with the clock; breaks the 1018 digest `INF`.
- **Consumers, measured.** `kala_gochara_windows` gen `3.0` (914 canonical / 1,830 total) is what the
  three tools, `reading_checklist`, D8/D9 and Kshetra stage-4 read, via authority `'3.0'` `RUN`.
  `_v2` gen `2.0` (87 / 163): **only** `scripts/w2g_equivalence_report.py` reads it `SRC`; the
  register's "gochara service; MCP" receiver claim is unsupported — the service reads no table, the MCP
  tool never names `_v2`. `UNRESOLVED_USE`. Sangam calls the **service** (`find_aspects`,
  `find_eclipse_proximity`; and `search_long_horizon` *bypassing* the service, `engine.py:1383`) and
  reads `kala_vedha_gochara` directly (`ka_sangam.py:1060`), undeclared in its `depends_on` `SRC`.
  Kota/Tithi→century: `ClassContext.fetch` reads vedha, moorti, AV gates, Sade-Sati only `SRC`.
- **Overlays, measured `RUN`:** Vedha 177 rows, Moorti 71, Kota 585 on the canonical chart, all
  spanning **2026-07-08 → 2027-10-11** — the rolling −60/+400 d window = **1.26 %** of the served
  century (1984–2084). Outside it the century's `quality_gates` is 1.0 and Moorti is absent.

**Ladders.** Data-plane `PLAN_REVIEWED` by this document. t3: no event.

## G. Group layer (template §3)

| Member | Packet | Writer / publication owner | Owned partition | Fence |
|---|---|---|---|---|
| `ka_gochara_resonance` | **G-R** (own) | resonance writer | `gochara_resonance_map` per chart | W2 27-class gate |
| `ka_gochara` + kernel + contact ledger | **G-W** (own) | `ka_gochara` writer | `_v2` `'2.0'` today; **new production generation** + contact ledger after N-5/N-7 | fences 1, 3; generation-keyed DML only |
| `ka_vedha_gochara`, `ka_moorti_nirnaya` | **G-O** (shared overlay packet) | each its own writer; one packet owner | own tables, per chart | none shared |
| `ka_kota_chakra` | proposed-use; **not** briefed here (Stream A) | — | — | — |
| century | **held**; engine donated to G-W | century writer (untouched) | `'3.0'` prod + `g3_*` staging | fences 1–3; hold |
| sweep | protected history | none | `v1` | Phase 1.1 guard |

**Served product owner (decision N-5).** Today: the product reads `'3.0'` = the **held** century
writer; the W2-eligible `ka_gochara` produces `'2.0'` that **nothing serves**. Proposal: **`ka_gochara`
owns the served product.** It already is the registry's authority (`sweep.superseded_by='ka_gochara'`
`RUN`), it is active and W2-eligible, and the century's engine (λ_v3, hierarchy, chains,
vocabularies) migrates into it as the scoring projection. It writes a **new generation into
`kala_gochara_windows` beside `v1` and `3.0`**; `'3.0'` stays selectable for rollback; `g3_*` staging
is preserved as calibration corpus. Century lifecycle stays held → `INVESTIGATE_CONSOLIDATION` → only
`RETIRE_AFTER_MIGRATION` under R1's full gate set and a Strategy denominator amendment.
**Post-elevation meaning of `authoritative_generation`:** a pointer to an **immutable publication**
(label + manifest id), flipped only under 527's four functional gates; never a mutable label a rebuild
can refill in place. Alternatives weighed: (B) century keeps ownership — but it is held, its build is
the expensive one, and it would leave the W2 member producing unserved rows indefinitely; (C) both
write the served table — two writers on one relation is fence 2's own hazard.

## 3. The failure — one falsifiable problem (the family's)

| Field | Content |
|---|---|
| Observed | The product's only contact engine keeps no **qualified** contact — and on 534 of 914 served rows, none at all. **Corrected 2026-09-23** (v1.2 said "keeps no contacts", which was too strong): the dedicated field is empty on every served gen-`3.0` row (914/914 `active_sentences = '[]'`), **but `term_breakdown.activity_terms` does carry partial contact records on 380 of 914 rows — 25,518 records, each with `primitive`, `transit_planet`, `target_ref`, `event_datetime_ist`, `orb_decay`, `p_i`** `RUN`. What is absent is the Contact object's *qualification*: no orb in degrees, no applying/separating, no station/retrograde branch, no bracket or root time, no tolerance, no coverage — and no record whatever on the remaining 534 rows. Also: the v1 corpus carried them on 16,276/16,297 rows with keys `primitive, transit_planet, secondary_planet, target_type, target_ref, event_datetime_ist, fact_ids, classical_citation, uncited_extension` `RUN`. Both windows tables hold **zero** Contact-object geometry: no orb, applying/separating, station/retrograde branch, bracket, root time, tolerance or coverage — 33/34 columns, all `DATE`-grain `RUN`. Contacts are computed in `_gather_sentences_no_db` and discarded before persistence `SRC`. |
| Evidence | `information_schema` `RUN`; `engine.py:1063-1137` `SRC`; Appendix B rows 12–14 |
| Expected contract | Strategy §3 **Contact** + **Search coverage**; VA §6.4 chain *raw motion → chart-relative contacts → activation → convergence → publication*; Product §3.10 "actual contacts, intervals, recurrence"; F04/F06 |
| Defect class | **computed-but-discarded** (register class *b*) — and a **generation regression**: `3.0` dropped what `v1` served |
| Impact | L3-Q01/Q02/Q08 cannot be answered from served data: no contact identity to cite, no coverage to bound "none found". Concretely (§4.5): in an ordinary quarter **0 of 22** served rows is a timing window; for **13 of 27 classes — including marriage, career_advancement, illness_acute, surgery, childbirth — no timing window exists anywhere in the century** `RUN`. |
| Non-claim | Not a claim about the full-century λ distribution, doctrinal validity, or causation; not a claim that v1's sentences were *correct*, only that they existed. |

Ranked secondaries: F15 fixture kakshya on the served path (147/202 sentences, 59 % cost `MEAS`;
activity [0.99964844, 1.0] on all 380 served rows with a value `RUN`) · F3 wrong-zodiac `ka_gochara`
contacts (Saturn 763 d `MEAS`; unserved) · F13 `lambda_thresh=0.0`/`>=`/exception→0.0 · B5.

## 4. Stage 1 — the value, and the semantic delta

### 4.1 Which L3-Q, which distinction, which baseline, which ablation
**Q08** (primary, failing): *searched horizon, resolution, method/target coverage, unavailable inputs*
— proof: a window just outside a searched partition is not a universal denial. **Q01/Q02** (primary):
which exact contact, from when to when, nearest vs stronger under a named criterion. **Q05/Q09/Q10**
contributing via `comparable_with`, D-1 convention, Moon drill-down. **Q03** only after R8's L2 slice.
**Distinction earned (Product §1.3):** the person can distinguish *"no qualified contact in the
searched horizon"* from *"outside the horizon"* from *"method never ran"*, and can see *which* body
touched *which* natal point *when* — today none of the three is expressible. **Simpler baseline:**
today's authority-`3.0` windows, same chart/class/horizon/budget. **Ablation:** remove
`independence_group` → agreement inflates; remove F06 states → "unavailable" reads as "clear" again;
remove the ledger → Q01 collapses back to a decade envelope.

### 4.2 Latent-value register (template 2.1)

| # | Field / computation | Class | Consumer unlocked | Fix |
|---|---|---|---|---|
| L1 | contact instants + bodies + targets (`ConfigurationSentence`) | **(b)** computed, discarded | Q01/Q02; Sangam; Kshetra; L5 ids | persist the Contact object (N-7) |
| L2 | v1 `active_sentences` (partial contact identity) | **(a)** persisted in `v1`, absent in served `3.0` | same | generation regression reversed by L1 |
| L3 | orb, applying/separating, branch, bracket, tolerance | **(c)** genuine gap — never computed to persistence | Q02 "nearest vs stronger" by *named* criterion | kernel emits episodes |
| L4 | Search coverage (requested/completed horizon, resolution, tiers, unsearched) | **(c)** gap | Q08 | coverage manifest per partition |
| L5 | kakshya boundaries | **(d)** available in L1 (BPHS Ch.66), fixture used instead | honesty of activity | H-1 |
| L6 | Vedha/Moorti/Kota beyond ±460 d | **(c)** gap + **(d)** day-grade | century-wide gates; Moorti at true ingress | G-O on the kernel |
| L7 | resonance source roots beyond the first; `afflicted` qualifier | **(b)** discarded (`setdefault`, parse strip) `RUN` | Kshetra A05; testimony roots | G-R fix |
| L8 | `MAX_PEAKS_PER_ERA_WINDOW=3`; era = whole decade | **(a)** truncated before persistence | Q02 | H-3, H-5 |
| L9 | Kota rings (585 rows) | **(d)** unqualified for v3 use (`w25` not wired; operand audit owed) | M-4 | proposed-use, gated |
| L10 | month/day tiers for point classes | **(c)** by design: 13 classes envelope-only `RUN` | Q01/Q02 for the most-asked classes | kernel + M-1 ruling |

VA §10.3's offensive question: which *missing* thing unlocks a new capability? **Stable contact
identity across chapter → interval → instant** (Product §9 exp. 4) — nothing else in the layer can
supply it; Sangam's independence problem (U02) and L5's frozen-claim identity (U10) both need it.

### 4.3 Target-state design (template 2.2) — the ideal Contact producer vs the register
Ideal: per chart, per (body × target × relation), an **episode** — `t_in / t_exact-or-closest /
t_out` with bracket and tolerance, `exact_crossing`, branch (direct/retro/station), orb + `orb_source`,
dwell, convention vector, `contact_id`, evidence roots (L1 `fact_id`s), F04/F06/F12 + Temporal
testimony + `comparable_with`, and a **coverage** row per partition. Actual register rows 57–79:
23 DATE-grain interpretive fields, none of the above. The ranked gap = L1→L4 in §4.2.

### 4.4 Efficiency with quality (template 2.3) — P3 and the century decision
**Hotspot, measured:** 64 ms/evaluation at 2 targets, ~92 % repeated per-instant search; 1.7×10⁵
evaluations/chart (270 substeps × ≈620) `MEAS`; `ClassContext.fetch` ×270 `SRC`. Live classes carry
14–40 targets (mean 28.3) `RUN`. Closed-form evaluation once events are known: 0.013 ms/instant
`MEAS`. Longest single completed century execution **58.2 min**; 270/270 substeps over a 5.02 h span
across attempts `RUN`.
**P3 equivalence contract (Strategy §5):** *unique target-specification events over absolute intervals
plus boundary halos* ← the kernel solves each (body, target, relation) **once per chart**, class-
independent, on sidereal arcs under D-1; *chart/common and class-specific context* ← global sky
(no per-chart copies) + per-chart ledger + per-class projection; *time-indexed clocks* ← daśā/AV/
Sade-Sati as interval sets, not per-instant scans; *batched hierarchy writes* ← projection writes
per class. **Equivalence:** no missing narrow/station/retrograde events — episodes primary, no
station coalescing, seam owned, declared ε with `near_station_unresolved` + direct solve where a
consumer needs it; complete boundary joins — truncated episodes emitted at horizon edges; parent ids
and both table roles preserved; no chart-bound reuse across subjects (ledger keyed by chart). Same
finite-value policy, floats, ties. **Output-identity method:** Stage E (span-aware: point events /
residence spans / interval overlaps — a single dated event list is *not* sufficient, `E8`) reproduces
the legacy algebra factor-by-factor before Stage M changes anything. **No cap or coarser grid is a
speedup.** Target figure deliberately unstated until `KALA_COST_PROFILE_v1_0.md`.
**Century (N-6):** *qualified compact substrate with explicit refinement semantics* — the ledger,
complete for the declared bodies/horizon at declared ε; windows as its refinement projection. Coarse-
to-fine is admitted only with the candidate-coverage argument (arc decomposition brackets every root
of a continuous series; ε bounds what daily knots can prove) and the exact-refinement contract (direct
Swiss solve on request). Every no-window result carries the Search-coverage object.

### 4.5 Consumer walkthrough (template 2.5) — `gochara_forecast_get`, canonical chart
Tool: `SELECT … FROM kala_gochara_windows WHERE authority-generation … ORDER BY window_start,
signed_intensity DESC LIMIT 100`; each row gets `resolution_disclosure`; page carries
`context_only_rows_in_page`; `coverage` is category coverage only `SRC`.
**Ordinary period, 2027-03-01 → 2027-05-31 `RUN`:** 22 rows across 22 classes — 9 `era` (3,647-day
spans) and 13 `point_class_context_envelope` (3,647-day spans); `is_timing_window=false` on **all 22**;
`signed_intensity` 0.20–0.60; zero month/day rows. What reaches synthesis: *"22 of 22 served rows are
context, not timing windows"* and nothing a person can act on or compare. What reaches it after
elevation: for each class, the actual episodes in the quarter (or an explicit `unexplored`/
`inapplicable`), each with body, target, instant, orb, branch and coverage.
**Dramatic period, marriage 2013 `RUN`:** `3.0` serves **one** row — a 2004→2014 envelope, peak
2012-01-17, `is_timing_window=false`. `v1` served **52** daily rows across 2013 with contact sentences
(the 2.0 design's "both 2013 marriage peaks incl. the double-transit" specimen `RCPT`). The cutover to
`3.0` *removed* the specimen from what the product reads. After elevation: the 2013 episodes with
their contacts, the double-transit as one `independence_group`, and a coverage row saying the year was
searched.
**Century-wide `RUN`:** 9 classes have month/day tiers, 5 have chain milestones, **13 have only
envelopes** — marriage, career_advancement, illness_acute, surgery, childbirth, romantic_start,
property_acquisition, career_entry, exam_outcome, travel_event, bereavement, birth_anchor,
achievement_recognition. The honest current answer to Product §7.1's "compare closest and later
windows" for those classes is: *there are none to compare.* This is not plumbing; it is the product's
timing capability for its most-asked questions.

### 4.6 Synergy (template 2.4) — owes / receives, with F12 roles
**Owes.** Sangam **S-1** service contract (`computation`): `find_aspects` / `find_eclipse_proximity`
/ long-horizon search returning episodes with grain, coverage and ids — today Sangam bypasses the
service for long horizons `SRC`. Sangam/Kshetra **contact ids** (`computation`) so independence and
replay hold (U02). Kshetra **resonance without first-root loss** (`relevance_navigation`; A05).
Vighnakara/TRIGGER **one obstruction root** (`counterevidence`; A08) — Vedha carries
`independence_group` so the same window never attenuates twice. The three tools **one honestly-owned
generation** (`computation`) — N-5. **Receives.** Resonance targets from L0–L2 rule capital
(`relevance_navigation`; 508/765 uncited — carried as F06 `unqualified`, not hidden). Moorti's
±460 d day-grade coverage (`applicability`) — **never silently century-complete** (A06); G-O extends
it on the kernel. AV gates, Sade-Sati, daśā from L1 (`applicability`). Kota (`counterevidence`) —
proposed-use only. **Seams where meaning dies today:** contact → `active_sentences=[]`; overlay
coverage 1.26 % → gate 1.0; first-root `setdefault`; the ±5 d box erasing applying/separating;
the decade envelope erasing Q02.

### 4.7 Typed qualification, time and knowledge-time (template 2.6)
No confidence/salience scalar. Every row: `epistemic_class` (F04), `completeness_state` (F06 six
states; no 1.0/0/empty fallback), `operator_role` (F12), Temporal testimony incl. silence and
`independence_group`, `comparable_with`; `time_basis` + `bracket_days` + `tolerance_arcsec` +
`claim_grain` (qualification, not confidence); and **`ephemeris_backend`** (`swieph` + the three
`.se1` checksums, or `moshier`) — two contacts computed under different backends are not comparable,
and a `tolerance_arcsec` quoted against a Moshier oracle is not a tolerance against Swiss
(Appendix D). D-1 Swiss sidereal mode; N-4 node from L1 `fact_id`.
No `date.today()`; instants UTC; `DATE` projections stay `DATE`. Event time (contact), knowledge time
(input generation vector), publication time (manifest) pinned separately. No live L4/L5 read;
rectification only as an admitted immutable artifact (Strategy §6.2). Deferred method calls M-1
(= June I-17), M-2, M-3 (Moon evidence retained, ADJ-14), M-4 (operand audit first; `w21` proxies
bindus `SRC`) — each a native ruling with evidence.

## 5. Preservation, migration, history, rollback

| Component | Disposition | Preserved / changed |
|---|---|---|
| sweep `v1` rows | `PRESERVE` / `HISTORICAL_RESTRICTED` | untouched; outside every generation and delete scope |
| resonance | `ENRICH_CORRECT` | keep 8 target types, citation flags, 27-class gate; fix first-root loss and stripped qualifier; reserve L2 columns |
| `ka_gochara` | `ENRICH_CORRECT` → served owner (N-5) | keep ±3 y *as disclosed bounded coverage* (A13), fingerprints, horizon attestation; replace tropical join (F3), `date.today()`; add ledger partition (N-7) |
| kernel (new module) | `INTEGRATE` proven functions from `w2g`/S0; one-way dependency; S0's defects not imported (`E8`) | — |
| Vedha, Moorti | `ENRICH_CORRECT` | schools/roots/citations kept; horizon → build horizon; Moorti at true ingress (F6); F06 states |
| Kota | `PRESERVE`; proposed-use | Stream A; M-4 gate |
| century engine | `PRESERVE` now → `INVESTIGATE_CONSOLIDATION` | λ_v3, hierarchy, chains, vocabularies, both table roles |
| `_v2` `'2.0'` rows | `UNRESOLVED_USE` | register amendment |
| `GocharaTransitService` | `ENRICH_CORRECT` (S-1) | later kernel adopter |

Protected classes: `v1`; issued claims (F17/U10); Bhavishya outcomes. Fences 1–3: every DML carries
chart + event_class + generation (+ era/resolution for v3); one writer/publisher per packet.
Cascade: none of this family's relations is an FK cascade source (CURRENT_STATE §4.2); non-FK
referrers (Kshetra stage-4, Gochara parent ids) pinned by publication content. Generation binding per
FOUNDATION_SAFETY §6 items 1–4; empty partition explicit; candidate ≠ selected; rollback = head
re-point; if physical generations are unavailable at execution, a `content_pin` manifest over the same
relations, never mutable `public` fall-through. **History (N-1):** (a) Phase 1.1 closes the path,
(b) 1.2 grants, (c) restore drill of all 38,287 rows content-checked, (d) (table, generation) guard for
`'v1'` and `'3.0'`. Migrations at `platform/migrations/1071+`. Retirement forbidden until successor,
caller migration, provenance transfer and reversible rollback are proved and separately authorized.
**Interface packets (Pūrṇa code, L3 tests):** P-1 coverage attestation routes an unknown generation to
the retired-sweep branch (`:963-977`) → resolve against the publication manifest; P-2
`reading_checklist.ts:1063-1092` drops ids/basis and counts a capped page; P-3 L5 ledger lacks
`contact_id`; **V-1** Sangam declares Vedha (`counterevidence`) and re-types `→ka_gochara` as service.

## 6. Focused proof matrix (synthetic non-person cases; disposable DB; no live chart before its gate)

| Proof | Test · expected · detector |
|---|---|
| Positive | station-pair cubic → 3 roots; seam tangency → ≥1 episode; start-inside → truncated episode (today 1 / 0 / `[]`, `E8`) |
| Negative | no L1 kakshya row → `unqualified`, 0 fixture sentences; overlay gap → `unavailable` (today 147 sentences / gate 1.0) |
| Relevant influence | move one natal target 1° → only its episodes shift |
| Irrelevant control | shuffle resonance/target order → identical rows and `contact_id`s |
| Duplication | one physical contact via 3 targets → one `independence_group`; activity unchanged |
| Context/missingness | wrong chart/ayanāṃśa/generation → reject; six F06 states distinct, never 0 |
| Boundary/precision | partition seam → same `contact_id`; kernel vs Swiss under identical flags within ε; near-station flagged. **Gate condition (Appendix D): must run where `.se1` is present, recording backend + file checksums — on Moshier this comparison cannot fail and is not a detector (§N.8); such a run is `NOT_RUN`, not PASS** |
| Delivery | sentinel in `independence_group` of a low-ranked row survives P-1/P-2 to the saved result (NOT_RUN until Pūrṇa lands) |
| Revision | change a kakshya boundary → new generation, old preserved, head re-point back; same inputs on two dates → byte-equal (kills B5) |
| Value | `KALA_BASELINE_v1_0.md` Q08/Q02 questions vs today's envelopes; ordinary-quarter and marriage-2013 walkthroughs re-run — `EXPLANATORY_DISCRIMINATIVE_VALUE` |
| Evaluation | `not_applicable` — no empirical claim; L5 not opened |

## 7. Implementation and review discipline
One writer surface per packet in its own worktree off `main` (the integrator log's finding applies to
this file too — nothing here is `git add`ed). Order: contracts → synthetic suite → kernel ‖ span-aware
legacy algebra → decomposed comparison + bounded timings → H-1..H-6 → ledger/publication → P-1..P-3 +
minimum L2 slice → M-1..M-4 rulings → G-O overlays → full benchmark and cutover (**P** authority).
Absent authority is `NOT_RUN`. Stop conditions: unresolved convention · unknown-as-empty · missed
topology without declared fallback · unclassified divergence · id drift across partitions · vacuous
comparison. Migrations only at `platform/migrations/1071+`, both directories checked.

## 8. Terminal packet and decisions returned

Execution returns: approved brief and upstream pin; commits/files; old/new examples (§4.5 re-run);
preservation/generation/rollback evidence incl. the drill; raw commands per §6; reviewer findings;
**state reached `PRODUCER_READY` at most**; unreached states; residuals; confirmation that `v1`,
`'3.0'`, `kala_views/`, the seed and `transit_search.py` were untouched.

**Decisions for the native.**
- **N-5 served-product owner:** `ka_gochara`, new generation beside `v1`/`3.0`; `authoritative_generation`
  becomes an immutable-publication pointer under 527's four gates. *(§G)*
- **N-6 century:** qualified compact substrate + refinement; hold stands; no retirement now. *(§4.4)*
- **N-7 Contact object:** **persist** as a new ledger partition on the existing owner `ka_gochara`
  (VA §10.3: no new writer), exact-instant grain, served on demand for Moon-scale. Rationale: identity
  and replay for Sangam/Kshetra/L5 need persistence; `active_sentences` was the partial persistence
  `3.0` dropped. Alternative — on-demand from the service only — loses ids, replay and U10.
- **N-8 Kota/Tithi edges:** Kota stays **proposed-use** (module `w25` exists; operand audit owed —
  M-4); Tithi's declared century edge is **retired as an edge** (no consumer coded, method
  unadjudicated, A09) pending its own ruling — an edge disposition, not an asset one.
- **N-9 registry-hold release condition:** (i) Phase 1.1 `is_active` filter landed, so `target_table`
  can never again be a delete target; (ii) seed correction PR co-owned with the shared-file owner;
  (iii) an integrity conjunct that fails when `target_table` disagrees with `count_sql`'s relation.
- **N-1** re-sequence D-2 (§5).
- **N-4 node convention — CORRECTED 2026-09-23, and its cost is larger than v1.2 stated.** v1.2 said
  "inherit L1's, which is TRUE_NODE (`l1_positions.py:128`)". **That was wrong**: `l1_positions.py`
  is not the path behind the served natal facts. The registered writer `ga_positions` →
  `ga_writers/ga_positions_writer.py:31` → `pyjhora_adapter.compute`, and `pyjhora_adapter/_jhora.py:23-55`
  patches `drik.sidereal_longitude` to `_swe.MEAN_NODE` for all ayanāṃśas `SRC`. **Served L1 natal is
  MEAN node** — as the Saṅgam session's M-1d states, and as DAR's ruling intends. Corrected on their
  evidence; credit to `madhav-d9`. **But four surfaces disagree, not two** (Appendix C), and the one
  that matters to this family is `ephemeris_daily`: **the live L0 knots are TRUE node** `RUN`. So
  "inherit L1 (mean)" is *not* free for the kernel — it requires either an L0 ephemeris disposition
  or an explicitly declared mixed-frame contract. **Recommendation unchanged in direction, sharpened
  in scope:** rule mean node (L1 + DAR + FORENSIC agree), and pair the ruling with N-4a below.
- **N-4a (new, consequence of N-4):** the node ruling is not a Gochara preference — it is a repair for
  **every** reader of `transit_search.py` (Gochara, Saṅgam, Kshetra S0, Taranga, frozen L0
  `bg_sky_calendar`) **and** for `ephemeris_daily` itself. Decide the disposition for the stored L0
  knots: (a) rebuild `ephemeris_daily` mean-node — matches DAR's receipt but touches a frozen layer and
  every downstream consumer; (b) keep the knots true-node and have the kernel derive mean-node Rahu/Ketu
  analytically at read time — cheap, no L0 rebuild, but the store and the derivation then disagree by
  ~1° and that must be declared, not silent; (c) declare a mixed-frame contract per consumer. **My
  recommendation: (b)**, because the mean node is an analytic quantity that needs no ephemeris pass, it
  leaves the frozen layer untouched, and the derivation is auditable against Swiss. Route the L0 receipt
  discrepancy (Appendix C row 4) to L0's owner either way.
- Deferred with evidence: M-1..M-4. Not decided: the five Phase-2 decisions; any retirement; any guard
  weakening; `convergence_commit`; orchestrator contract.

**What changed vs v1.2 (2026-09-23, on the Saṅgam session's evidence):** N-4 corrected — served L1
natal is mean node, not true; new N-4a and Appendix C; the L0 receipt discrepancy routed to L0.
**What changed vs v1.1 (evidence required it):** group shape and served-owner decision (N-5) added;
Contact-object persistence (N-7) added; overlays G-O brought into scope; the 1.26 % overlay coverage
and the 13 envelope-only classes are new measured facts; v1.1's identity dispute stays withdrawn.

---

## Appendix A — lenses A–J (per member; `n/a` with reason)

| Lens | resonance (G-R) | `ka_gochara` + kernel (G-W) | Vedha / Moorti (G-O) | century | sweep |
|---|---|---|---|---|---|
| A identity | chart-derived, deterministic derivation; T0 targets | chart-derived; deterministic geometry + interpretive projection; served owner (N-5) | chart-derived qualified rules; overlays | chart-derived; held | tombstone |
| B DAG | in: L0 rules + L1 facts; out→3 | in: resonance, L0 knots/arcs, L1; out→tools, Sangam (via S-1), Kshetra | in: L1 + ephemeris; out→century, Sangam (V-1), tools | in: resonance, Vedha, Moorti (not Kota/Tithi) | none |
| C correctness | first-root loss; stripped qualifier | F3 frame; B5; kernel invariants vs Swiss under D-1; ε bound | day-grade vs ingress moment (F6); one reference-date ayanāṃśa | F13/F15; era=decade; 3-peak cap | n/a |
| D data | 765/27; 508 uncited → `unqualified` | zero Contact geometry (§3); L1–L4 | 1.26 % of century | 13 classes envelope-only | n/a |
| E consumers | 3 writers | `'2.0'` `UNRESOLVED_USE`; served owner post-N-5 | century + Sangam (undeclared) | tools via `'3.0'` | validation only |
| F AI readiness | citation flags served | P-1/P-2/P-3; F06 states; density via disclosure | `query_*` projections | disclosure honest (`E8`-verified branch) | n/a |
| G efficiency | n/a (cheap) | P3 hotspot; kernel; no target until profile | horizon extension cheap on kernel | 58.2 min longest run; held | n/a |
| H reliability | W2 27-class gate | fences 1,3; content-keyed fingerprints; guard (N-1) | per-chart DELETE/INSERT | fences 1–3; hold | Phase 1.1 guard |
| I packet | own PR | own PR + ledger migration ≥1071 | one overlay PR | none | none |
| J evidence | §6 rows | §6 rows + §4.5 re-run | coverage = horizon; ingress error rate | none claimed | none |

## Appendix B — live measurement record (2026-09-22, `amjis_app`, read-only)

| # | Question | Result |
|---|---|---|
| 1–11 | as BRIEF_v1_1 App. B | registry rows; 0 triggers/0 functions/0 protected rows; 588 applied 08-23 after the 08-21 error; row census; authority `'3.0'`×2; archive coverage 35,620/38,287; privileges; 765 targets, 14–40/class; century runs 239.7/613.5/3,491.6 s, 270/270 over 5.02 h |
| 12 | Windows tables' columns | 34 / 33 columns; `window_start/window_end/peak_date` **DATE**; no orb, branch, bracket, tolerance, coverage |
| 13 | `active_sentences` by generation (canonical) | `3.0`: **914/914 `'[]'`** · `v1`: 16,276 populated, 21 empty |
| 14 | v1 sentence keys | primitive, transit_planet, secondary_planet, target_type, target_ref, event_datetime_ist, fact_ids, classical_citation, uncited_extension |
| 15 | Overlay coverage (canonical) | Vedha 177 · Moorti 71 · Kota 585 rows; all 2026-07-08 → 2027-10-11 (≈460 d = 1.26 % of 1984–2084) |
| 16 | Served `3.0` shape census | interval/era 90 (3,647-d spans) · interval/month 267 · interval/day 267 · chain 160 · envelope 130 (3,647-d spans) |
| 17 | Ordinary quarter 2027-03→05 | 22 rows / 22 classes: 9 era + 13 envelope; 0 month/day; SI 0.20–0.60; `is_timing_window=false` ×22 (per `deriveResolutionDisclosure` branches, `SRC`) |
| 18 | Marriage touching 2013 | `3.0`: 1 envelope row 2004→2014, peak 2012-01-17 · `v1`: 52 daily rows, peaks 2013-01-01 → 2013-12-30 |
| 19 | Timing capability by class | month/day: 9 classes · chain: 5 · **envelope-only: 13** (incl. marriage, career_advancement, illness_acute, surgery, childbirth) |
| 20 | Forecast tool | `ORDER BY window_start, signed_intensity DESC LIMIT` default 100 (max 500); no budget trim inside `computeGocharaForecast`; `GENUINE_PEAK_BASES = {gochara_lambda_v3_argmax}` |

Still unmeasured: Clear-route invocation history; full-century activity distribution; Moorti
ingress misclassification rate; ledger storage size; any value/consumer claim.

---

## Appendix D — ephemeris backend: a qualification on this family's own oracle (2026-09-23)

**CORRECTED 2026-09-23 — this appendix's central factual claim was wrong.** v1.2 stated "no `.se1`
file exists in this worktree or the usual system paths" and concluded all geometry evidence ran on
Moshier. **The files are present**, at `/private/tmp/se1` (placed 2026-09-22 17:20): `sepl_18.se1`
sha256 `ca1393ce…` — **the exact checksum `Dockerfile.pipeline:22` verifies** — plus `semo_18.se1`
`1ca07bd6…`, `seas_18.se1` `a2cd8fc3…`, `sefstars.txt`, `seleapsec.txt` `MEAS`. The error was
procedural and worth naming: I quoted `pipeline/transit_search.py:187-200`'s candidate list — which
names **`/tmp/se1`** explicitly — then checked five *other* paths and not that one. Found by the
Kshetra session, verified by `madhav-d9` and `madhav-fc`, re-verified here.

**What is true instead.** Without `swe.set_ephe_path`, `FLG_SWIEPH` silently falls back:
`retflag 260` (bit 4 = Moshier). With `swe.set_ephe_path('/private/tmp/se1')`: **`retflag 258`** =
SWIEPH|SPEED, no Moshier bit `MEAS`. So the geometry evidence *was* Moshier — that conclusion held —
but because the path was never set, not because the data was missing. **The fix is one call, and
every gate in §6 is satisfiable on this host today.** The deployed images carry the same files at
`/app/ephe` (`Dockerfile:24`, `Dockerfile.pipeline:17`) `SRC`.

**Two results this unlocks, both previously impossible.**
1. **The store is true-node to zero residual.** Stored `ephemeris_daily` knot 73.629058 vs Swiss TRUE
   at 12:00 UT = **73.629058, diff 0.000″** `MEAS`. My earlier "0.005° residual" was *exactly* the
   Moshier error. Independently, `madhav-fc` re-ran its five dates at noon on Swiss and its true-side
   residuals collapsed from ≤0.104° to **0.000″ on 5 of 5** at six decimals. Store-is-TRUE no longer
   needs the separation ratio — it is exact. This also shows the L0 build ran with the Swiss files,
   making `l0_ephemeris.py:290`'s "mean North Node" comment over `calc_ut(jd, 11, …)` a definitive
   comment-vs-code defect (§N.7), not an ambiguity.
2. **Moshier's true-node error is bounded — at 65.3″, not 18″.** Three sparse samples disagreed
   (mine −16.7″/+18.1″ on 5 dates; `madhav-fc` −32.5″/+19.4″ on 16), so I measured **every noon knot
   1950-01-01→2100-12-31, n = 55,152** on real Swiss (`retflag & 2` asserted per call): Moshier − Swiss
   ranges **−65.3″ to +58.1″, |max| 65.3″ on 1972-11-20** `MEAS`. Both sparse samples were subsets and
   both under-reported — **a sparse sample of an oscillating error is not a bound.** Still far below
   the ~0.1° (360″) feared, so "unbounded Moshier error" is retired; but the asymmetry that matters is
   now **2.7× under the 177″ natal-pāda margin and 10.4× over the 6.3″ stored-knot margin.** The
   birth-instant pāda is reportable even on Moshier; the stored-knot pāda is not on any backend.

**Three consequences for this plan.**
1. **The geometry gate was not a detector.** §6's boundary/precision row and §4.4's output-identity
   method both compare "kernel vs Swiss under identical flags". Run without `.se1` that is
   **Moshier against Moshier** — it cannot fail (§N.8). Gate condition added above: the comparison
   runs where `.se1` is present and records backend plus checksums; otherwise `NOT_RUN`.
2. **The convention vector gains `ephemeris_backend`** (§4.7), because comparability and
   `tolerance_arcsec` both depend on it.
3. **Inherited accuracy figures — still `[U]`, for a narrower reason.** The W2G V3 spline result
   (worst case 0.314″) was measured "against direct Swiss Ephemeris calls". The files existing does
   not establish that V3's run *set the path*, and an unset path yields Moshier silently — exactly
   the trap this appendix fell into. The figure remains **`[U]`**, but the question is now "does the
   V3 runner call `set_ephe_path`?" — answerable from source, not by re-measurement. Stakes are
   real: at a 65.3″ Moshier bound, a Moshier-validated "0.314″" would have measured the spline
   against a reference **200× coarser than the claim** — the figure would say nothing about
   Swiss-grade accuracy at all. That is why the source question must be answered before 0.314″
   anchors any gate.

**Backend detector — use `retflag`, not flag comparison.** `swe.calc_ut` returns `(xx, retflag)`;
`retflag & 1` = JPL, `& 2` = Swiss files, `& 4` = Moshier. Measured here: requesting `FLG_SWIEPH`
returns **retflag 260** (= 256 | 4) → **Moshier actually used** `MEAS`. v1.2 inferred the fallback
from `FLG_SWIEPH` and `FLG_MOSEPH` agreeing; `retflag` *proves* it and is the only detector a silent
fallback cannot fool. **The WP3a gate reads `retflag` and records it**, not the requested flag — and since the files are
present, the gate is satisfiable here today: set the path, assert `retflag & 2`, exit `NOT_RUN` on
`retflag & 4`, print the three checksums. Adopted by `madhav-fc` as blueprint §11.7's rule and by
`madhav-d9` as Saṅgam suite S8 v2.1. **Never infer the backend from two flags agreeing or from
`.se1` appearing absent** — both inferences failed here, in opposite directions.

**Epoch discipline — a unit error that cost two sessions a day (2026-09-23).** The strategic session
reported a 332.3″ cross-session disagreement on the same body and date, and drew from it that the
node figures were irreproducible and that a claim inverted. Resolved by measurement: **there is no
disagreement.** Both hosts are pyswisseph 2.10.03 on Moshier and return the *identical* value to
0.00″ at the same instant. The 332.3″ was **midnight (00:00 UT) versus noon (12:00 UT)** — the true
node moves −0.178 to −0.190°/day here, so half a day is ≈0.09°, which is 332.3″ exactly. **Noon is
the correct epoch:** `l0_ephemeris` computes every stored knot at `swe.julday(y, m, d, 12.0)`, and
W2G's spline validation states the rule in terms ("KNOT ABSCISSA: NOON UT … a midnight-knot spline is
wrong by half a day"). So the stored-vs-recomputation residual of **16.7″** at noon stands, and 349″
is what the same comparison yields under an epoch mismatch. Measured epoch artefact on six dates
1950–2100: −37.5″ to +332.3″ `MEAS` — the same order as the 0.104° maximum residual the strategic
session reported across five dates, so that residual set is likely epoch-contaminated and should be
re-run at noon (doing so should *strengthen* the store-is-TRUE conclusion, since the mean-side
separation of 0.95–1.47° is 10–14× larger and unaffected).
**Consequence for this brief's own contract:** `epoch_convention` (noon-UT knot abscissa) joins the
convention vector beside `ephemeris_backend`, and any cross-source geometry comparison must state the
instant, not only the date. A date is not an epoch.

**Not established.** Whether the W2G V3 runner calls `set_ephe_path` (a source question now, not a
measurement one); whether any production build has run with `/app/ephe` unpopulated; whether
`/private/tmp/se1` is durable or a scratch artefact of another session — it sits under `/tmp`, so any
gate depending on it must provision its own copy rather than assume this one survives.

---

## Appendix E — directed special aspects: exercised, not missing (2026-09-23)

The strategic session raised the directed-aspect question as *"real at the engine and currently
unexercised in served data"*, suggesting this family record it as a producer gap. **Verified here, and
it is neither.**

- The **classical asymmetric table exists and is correct**: `gochara_grammar/primitives.py:189-196`
  `SPECIAL_DRISHTI_DEG` — Mars `[90,180,210]` (4th/7th/8th), Jupiter `[120,180,240]` (5th/7th/9th),
  Saturn `[60,180,270]` (3rd/7th/10th), Rāhu/Ketu as Jupiter; every other graha `[180]`. BPHS Ch.26
  cited in place `SRC`.
- The **engine is directional by construction**: `find_aspect_events` computes
  `target = (target_longitude_deg + aspect_deg) % 360` (`transit_search.py:320`) with no negation —
  which is *correct* for dṛṣṭi, since dṛṣṭi is directional. There is no engine defect to close.
- **This family's path already passes the asymmetric table**: `drishti_contact` sets
  `aspect_degrees = SPECIAL_DRISHTI_DEG.get(planet, _DEFAULT_DRISHTI_DEG)` and hands it to
  `find_aspect_events` `SRC`.
- **It is exercised in served data**: `drishti_contact` appears in `term_breakdown.activity_terms`
  on **379 of 914** served gen-3.0 rows, with Mars, Jupiter, Mercury and Moon among the transit
  planets `RUN`.
- **Why it looked unexercised:** `activity_terms` stores the primitive name, planet, target ref,
  instant and orb decay — **never the raw aspect degree**. So "zero served rows carry 210/240/270" is
  an artefact of the storage format, not evidence of non-exercise. Absence in a field that never holds
  the value is not absence of the value — the same error class this campaign has been correcting all
  week.

**Where the real gap is:** at `ka_sangam`'s own call site, which passes a symmetric generic set
`[0,60,90,120,180]` (`ka_sangam/engine.py:464`) instead of the per-graha classical table. That is a
**Saṅgam call-site defect, not a shared-engine defect and not this family's producer gap.** Recorded
here so it is attributed correctly; the fix belongs to Saṅgam's R-series.

---

## Appendix C — the node convention is a four-way split (2026-09-23)

Raised by the Saṅgam session's cross-stream item M-1d; verified here at source and live. It
**corrects v1.2's N-4** and enlarges it.

| # | Surface | Node model | Evidence |
|---|---|---|---|
| 1 | **Served L1 natal position facts** — `ga_positions` (registered) → `ga_positions_writer.py:31` → `pyjhora_adapter.compute` | **MEAN** | three independent declarations, all `SRC`: `pyjhora_adapter/positions.py:21-22` `_USE_TRUE_NODES = False` ("classical convention") passed at `:61`; `vargas.py:21,65` the same, so **divisionals are mean-node too**; and `_jhora.py:23-55` patches `drik.sidereal_longitude` → `_swe.MEAN_NODE` for all ayanāṃśas |
| 2 | **Live L0 `ephemeris_daily`** — the knots this family's kernel reads | **TRUE** | stored Rahu 1984-02-05 tropical **73.629058** `RUN`; Swiss TRUE 73.633696 (Δ 0.005°), MEAN 72.648878 (Δ 0.980°) `MEAS`. Code agrees: `l0_ephemeris.py:290` calls `swe.calc_ut(jd, 11, …)` — id 11 is TRUE (MEAN is 10) — while its own comment says "mean North Node" |
| 3 | `pipeline/transit_search.py` — Gochara v1/v3, Saṅgam, Kshetra S0, Taranga, frozen L0 `bg_sky_calendar` | **TRUE** | `:10` docstring, `:64` `"Rahu": 11` `SRC` |
| 4 | `brahmagyan/ganita/l1_positions.py` and its six importers (`l1_dashas`, `l1_strength`, `l1_divisionals`, `l1_sensitive_points`, `l1_panchanga_birth`, `graha_sthana_writer`) | **TRUE** | `l1_positions.py:128` `SRC` |
| 5 | **`bg_cohort`** — a registered L0 writer seeding the ~10,000-row synthetic reference population used for rarity | **TRUE** | `bg_cohort.py:333` `("Rahu", swe.TRUE_NODE)`, `:159` docstring, `@register("bg_cohort")` at `:470` on `class BgCohortWriter(WriterBase)` — verified in this worktree **and on `origin/main`, byte-identical (691 lines, zero diff)** `SRC`. **Corrected wording 2026-09-23:** v1.2 listed this under l1_positions' *importers*; it is not one. Its seven `l1_positions` mentions are all prose (`:49` "instead of importing", `:105-106` "independently reproduced here") — so it is an **independent fifth declaration** of TRUE_NODE, which strengthens the finding rather than weakening it. Correction prompted by the strategic session, whose own read reported no `@register` and no `TRUE_NODE` in this file; that read does not reproduce here on either branch |

**Blast radius inside this family, measured 2026-09-23 `RUN`** (raised by the strategic session;
its served-generation figure reproduces exactly here):

| Surface | Node-bearing rows | Field carrying the node evidence |
|---|---|---|
| `gochara_resonance_map`, canonical chart | **40 of 765** targets are Rahu/Ketu, across **9** event classes | `target_ref` |
| `kala_gochara_windows` gen **3.0** (served), canonical | **232 of 914** | `term_breakdown` (`active_sentences` is `'[]'` on all 914 — the two findings are complementary, not in conflict) |
| `kala_gochara_windows_v2` gen `2.0`, canonical | **50 of 87** | `active_sentences` |
| `kala_gochara_windows_v2` gen `g3_utkarsha`, canonical | **232 of 914** | `term_breakdown` |
| `kala_gochara_windows` gen **`v1`** (protected), canonical | **6,225 of 16,297** | `active_sentences` |

The last row is a preservation consideration for the hub ruling, not just a repair cost: a node change
alters how any successor compares against the protected v1 benchmark. *Predicate note:* these use a
case-insensitive text match over the JSON, so they over-count relative to a strict `transit_planet`
match; the strategic session's `_v2` figure (242) does not reproduce on my predicate (I measure 50 at
gen 2.0 and 232 at `g3_utkarsha` for this chart) — a predicate/scope difference to reconcile, not an
error either way. Divergence magnitude: **max 1.933°** over 1984–2084 on weekly samples `MEAS`
(the strategic session states ~1.7°); **1.021°** at the native's birth instant.

**What this changes.** (i) v1.2's N-4 premise was wrong — corrected above. (ii) **DAR's receipt does not
match the live table:** `DAR_CLOSE_v1_0.md:20` records *"ephemeris_daily: Rebuilt with MEAN_NODE
Rahu/Ketu; Rahu at 1984-02-05 = 49.04° … FORENSIC-verified delta 0.01°"*; the live stored value is
**49.99° sidereal**, ~0.96° away, and is true-node `RUN`. Either the rebuild did not land as recorded
or the code changed after it. **This is an L0 receipt-vs-data discrepancy, routed to L0's owner; it is
not a Gochara finding to fix.** (iii) Row 4 is new to both streams: a second true-node chain exists
*inside* brahmagyan/ganita and in a registered L0 writer. Scope limit, stated honestly: I verified the
imports and that each importer references Rahu (`l1_dashas` 11 refs, `bg_cohort` 12) — I did **not**
verify that each importer's persisted output diverges. That is a bounded L1/L0 check, not a claim.
(iv) **The ruling is reading-visible, and now MEASURED on real Swiss — the withdrawal below is
SUPERSEDED (2026-09-23).** With the production ephemeris files loaded (Appendix D), at the birth
instant 05:13 UT under Lahiri: **TRUE → Rohiṇī pāda 4, MEAN → pāda 3.** The two node models straddle
the boundary, so the ruling changes a reading, not only code. `retflag 258` = SWIEPH, no Moshier bit.

**Three sessions, three figures, one convention — reconciled exactly `MEAS`:**

| Source | natal TRUE (sidereal) | margin to 50.0000° | convention |
|---|---|---|---|
| this session | **50.049248°** | 177.3″ | `FLG_SIDEREAL` (apparent, includes nutation) |
| `madhav-fc` | **50.045130°** | 162.5″ | tropical − `get_ayanamsa_ut` |
| Kshetra session | 50.0451° | ~162″ | same as `madhav-fc` |

The gap is **14.82″**, and nutation in longitude at that instant is **−14.82″** — identical `MEAS`.
So the three figures are one figure under two conventions: **the same L1-vs-scanner split this
appendix documents, reproduced inside our own measurements.** Both land in pāda 4 (177″ and 162″
margins), so the conclusion is convention-independent — but it is the cleanest possible argument for
D-1: pin the convention or three careful sessions get three numbers. MEAN is 49.033044° under either,
equalling L1's `RAH_MEAN` fact `c520713087b97470` to six decimals.

Provenance for the true side, since no `RAH_TRUE` fact exists: SWIEPH, `/tmp/se1` (`sepl_18.se1`
sha256 `ca1393ce…`, matching `Dockerfile.pipeline:22`), Lahiri, 05:13 UT, `FLG_SIDEREAL` — an
**author computation with stated provenance, explicitly not an L1 fact**; if it ever bears on a
reading, L1 should serve it. *The class-level text below is retained as the record of why it was
withdrawn while the backend was unknown.*

**[SUPERSEDED] The ruling is reading-visible, stated at class level — the specific pāda assignment is
withdrawn.** A ~1° mean-vs-true shift against 3°20′ pādas can move a pāda, so the node ruling changes
what a reading says, not only what the code does. That is the claim; it needs no sub-arcminute figure
to stand.
**Why the specific figure is withdrawn (raised by the strategic session, and I agree).** Both hosts
reproduce the same numbers — mine 50.054°/49.033°, theirs 50.0502°/49.0289° at the birth instant,
TRUE in pāda 4 and MEAN in pāda 3 — but **no `.se1` file exists on either host**, so every local
"Swiss" true-node figure is a Moshier fallback of unbounded error (Appendix D). The margin from TRUE
to the 50.0000° boundary is **3.26′ (196″)**, and the best date-specific estimate of backend
divergence on 1984-02-05 is the stored-knot-vs-local-recomputation residual, **16.7″** `MEAS` —
about a 12× margin, so the assignment is *probably* right. But "probably, on an unbounded error" is
not a figure to put in front of the native, and the class-level statement above loses nothing the
ruling needs. Re-measurable in the deployed image, which carries the `.se1` files; not here.
**The MEAN side needs no computation at all — cite the L1 fact (§N.5).** Both of us computed it;
neither of us should have. L1 already serves it, and the subject name encodes the convention:
`chart_facts` subject **`RAH_MEAN`** (there is **no `RAH_TRUE` subject** — L1 serves *only* the mean
node, which settles "which does L1 store" structurally rather than by inference) `RUN`:

| fact_id | key | value |
|---|---|---|
| `c520713087b97470` | `longitude_sidereal` | **49.0330441002811°** (matches my own computation to 10 dp) |
| `67f32a2ca86253de` | `nakshatra` | **Rohiṇī** |
| `060bb63b81a073bb` | `pada` | **3** |

`near_nakshatra_boundary_flag = false`; `source_calculation = pyjhora_adapter.positions/pyjhora/1.0.0`
— which ties the served fact to the mean-node adapter chain in row 1. Ketu: `KET_MEAN` 229.033044°,
Jyeṣṭhā pāda 1. **Honest tier:** `verification_pass_status = 'single'` — a permitted tier (§N.4, S7
ruling) meaning nothing double-checked it, not a two-pass verification. So the mean-side pāda is
**citable, 0.97° clear of the boundary, and requires no ephemeris and no derivation**; only the TRUE
side is undetermined on this host, and it has no L1 fact to cite. Credit: `madhav-d9` for finding the
served fact; this is the §N.5-correct form and it supersedes both of our computations.

**The knife edge — measured on Swiss, and correctly scoped: it is a TRANSIT sample, not the natal
position.** Supersedes the Moshier-era version below. On real Swiss the stored noon knot for
1984-02-05 is TRUE **49.998247°** → pāda **3**, just **6.3″** below the boundary, while the same body
at the birth instant is 50.049248° → pāda **4** `MEAS`. **Scope correction (raised by the Kshetra
session via `madhav-fc`, and right):** that knot is a *transit sample that happens to fall on the
birth date*, not a candidate for the natal position — so it **does not bear on the natal pāda** and
must not be cited as a reason to doubt it. What it is: a real hazard for any consumer that reads a
stored knot as an answer, since the knot and the instant fall on opposite sides of a classical
boundary. That makes it the strongest available argument for this family's core design choice —
**the kernel solves at the instant; a knot is an interpolation input, never an answer** — and it
sharpens N-4a(b), since the analytic mean-node derivation never consumes the knot at all.

**[SUPERSEDED, Moshier-era] A sharper hazard the strategic session's measurement surfaced — the *stored* value is on a knife edge.** The
`ephemeris_daily` knot for 1984-02-05, converted to Lahiri sidereal, is **49.9941°** — just
**0.0059° (21″)** below the same pāda boundary, and that is the value Kāla engines actually consume.
21″ is *smaller* than the 16.7″-scale backend divergence on that date, so **the consumed value's pāda
is genuinely indeterminate from this host** and would flip under a backend change. This matters to
N-4a: it is an argument *for* option (b), not against it, because the mean node is analytic by
construction (mean elements, no ephemeris file) and therefore **does not consume the knot at all** —
deriving mean at read time is immune to this knife edge, while any consumer that wants the stored
TRUE value inherits it.
