---
artifact: CLAUDECODE_BRIEF_L3_KA_DASHA_KALA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_DASHA_KALA
brief_for: ka_dasha_kala — Daśā-kāla / Daśā-eligibility SERVICE (L3 Kāla; the co-equal temporal pillar)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.6 Pillar-1 (daśā co-equal engine, I-3), §5.7.1 (the daśā-from-within plane), §5.7.2 (Mode A daśā SOFT PRIOR), §5.9.1 (lazy pruning tree-walk + interval algebra), §5.7.4 (cross-daśā agreement = amplifier/discovery), §5.10 (ga_dashas chart-bound finite → read as service input)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K1
  blocked_by: [k0_service_asset_type]   # CANONICAL id (collision audit 2026-06-21) — the K0 SERVICE asset-kind gate
  blocks: [ka_sangam, ka_jivana_parva]  # convergence Mode-A prior + the daśā macro-narrative consume this
  may_touch:
    - platform/python-sidecar/services/ka_dasha_kala/**           # NEW service module
    - platform/scripts/temporal/run_dasha_pipeline.py             # READ-ONLY reference (M3 dasha computers)
    - platform/scripts/temporal/compute_vimshottari.py            # READ-ONLY reference
    - platform/scripts/seed/asset_registry_seed.ts                # register the service row
  parallel_safe_with: [ka_graha_sancara, ka_muhurta_seva, ka_yojaka]  # disjoint files (transits vs dashas vs panchanga)
---

# CLAUDECODE BRIEF — ka_dasha_kala (Daśā-eligibility service)

## §0 — What this asset IS
`ka_dasha_kala` (Daśā-kāla, "the time-rulership of the daśā lords") is the **daśā-eligibility SERVICE**:
given a target structural signature and a time horizon, it returns the **scored set of time-intervals
during which the daśā plane makes that signature LIKELY to fire** (Mode A's coarse prior). It is the
**co-equal temporal sub-engine** (plan §5.6 Pillar-1): where `ka_graha_sancara`/`ka_gochara` answer
"the sky from WITHOUT," `ka_dasha_kala` answers "the promise unfolding from WITHIN." It is a SERVICE
(no stored rows) that READS the precomputed `ganita_dashas` timeline.

## §1 — Why it matters / strategic role
- **It does the brutal first cut (plan §5.7.2).** Daśā collapses decades → a handful of month-to-year
  windows via a cheap interval lookup, BEFORE any expensive ephemeris call. It is *why* the funnel is
  tractable.
- **It is a SOFT PRIOR, not a hard gate (plan §5.7.2 — the native's key correction).** It SCORES
  eligibility; it never excludes a moment outright. Mode B (off-daśā discovery) checks daśā via this
  service but is not filtered by it.
- **Cross-daśā agreement is a first-class signal (plan §5.7.4, §5.6).** When MULTIPLE daśā systems
  concur a period is live → confidence AMPLIFIER; when they disagree / only one fires → a DISCOVERY
  flag. This is an independence signal the rigor stratum's C1 (I-22) later consumes.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **TWO daśā tables exist — READ `chart_dashas`, NOT `ganita_dashas` (CONFIRMED by pre-impl audit 2026-06-21):**
  - `ganita_dashas` = the OLDER baseline store, `CHECK (level IN (1,2,3))` → level 3 = **PD only**. Do NOT use as the primary source.
  - **`chart_dashas` = the PRODUCTION writer output** (`ga_dashas_writer.py` writes this), constrained
    `cd_level_n_max4` (migration 211) → **level 4 = Sookshma**. Columns incl. `dasha_system, level_n, lord,
    parent_lord, start_date, end_date, kp_sublevel/kp_sub_lord` (KP carried as a sub-level dimension here).
    **This is the richer, authoritative source — the tree-walk reads `chart_dashas`.**
- **Systems ACTUALLY computed (`ga_dashas_writer.py::SYSTEMS` lines 2356–2359) = 7:** `vimshottari, yogini,
  ashtottari, chara_karaka, naisargika, mudda, kalachakra`. **CONFIRMED 2026-06-21:** the plan's
  "Vimśottarī/Yoginī/Chara/Nārāyaṇa/KP" was inherited from the old M3 prototype — **Nārāyaṇa does NOT exist**
  (no `compute_narayana_system`); **KP is NOT a standalone system** — it is a sub-level dimension under
  Vimśottarī (`kp_sublevel`, `compute_kp_subperiods`). Serve the 7 real systems; KP as Vimśottarī sub-level.
- **The writer produces 35 (system × ayanamsha) chunks + a cross-system concurrency post-pass.** So
  multi-system × multi-ayanamsha data already exists per chart.
- **`parent_lord`** gives the tree structure (MD→AD→PD via parent links); `start_date`/`end_date` give
  the intervals for interval algebra.
- **The M3 computers** (`compute_vimshottari.py`, etc., via `run_dasha_pipeline.py`) are the generators
  if deeper levels are ever needed (§3.4).

## §3 — The build
**3.1 — The lazy pruning tree-walk (plan §5.9.1).** Implement a top-down walk over `ganita_dashas`:
- Start at level 1 (MD). For the target signature, ask: is this MD eligible (its `lord` ∈ the
  signature's {constituent lords ∪ dispositors}, supplied by `ka_yojaka`'s daśā-eligibility predicate)?
- **Prune ineligible MD subtrees entirely** (do not descend their level-2/3 children). Most of the tree
  dies at level 1–2.
- Descend into live branches to the depth the query precision demands (PD for "next opportune window").
- **INTERVAL ALGEBRA, not point sampling:** each row is an interval [start_date, end_date]; the eligible
  set is a UNION of intervals — pure set arithmetic, no time iteration.

**3.2 — Eligibility SCORING (the soft prior).** Score each surviving interval: lord exact-match >
related (dispositor / house-lord) > neutral. Output an `eligibility_score ∈ [0,1]` per interval. This
is the Mode-A prior weight the convergence engine (`ka_sangam`) consumes. **The weights are
native-ratified judgments (plan §5.7.3 / I-7) — propose, do not silently pick.**

**3.3 — Cross-daśā agreement (plan §5.7.4).** For each candidate window, INTERSECT eligibility across
the available systems: agreement count = how many systems independently mark it live. Emit
`cross_dasha_agreement` (count + which systems). High agreement → amplifier; lone-system → a
discovery/anomaly flag for Mode B + the rigor C1 independence model (I-22).

**3.4 — The level-4 (Sookshma) floor + deeper-level policy (CONFIRMED 2026-06-21).** `chart_dashas` stops
at level 4 = **Sookshma** (`cd_level_n_max4`; the writer rail is "ZERO level_n=5"). For "next opportune
window" (days–weeks grain) Sookshma is sufficient. **Level-5 (Prāṇa) is NOT computed by any script and is
forbidden by both storage tables.** Policy (SETTLED): if Prāṇa is ever needed for hour-grain daśā, compute
it **ON DEMAND, IN-MEMORY, NON-PERSISTED** — one proportional subdivision below a level-4 `chart_dashas`
interval, NEVER written (writing would violate `cd_level_n_max4`). Default: serve to Sookshma from
`chart_dashas`; recurse to Prāṇa only inside a narrow surviving window, in memory.

**3.5 — The system set (SETTLED 2026-06-21 — no longer an open task).** The service serves the **7 systems
that exist in `chart_dashas`**: vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra.
Vimśottarī is primary (the canonical "WHEN" of Parāśarī Jyotish); KP is read as a Vimśottarī sub-level
(`kp_sublevel`). **Nārāyaṇa is NOT computed** — if the native ever wants it, that is a separate L1 reopen,
explicitly out of L3 scope. **The campaign plan §5.6/§5.7.4 + §3.1 must be corrected to the 7 actual systems**
(anti-drift plan-maintenance — tracked in the closeout DR1; do as a plan edit, not in this build).

**3.6 — Multi-ayanamsha.** Serve per-ayanamsha (the data is ×5/×ayanamsha already). Agree the ayanamsha
set with `ka_graha_sancara` + `ka_sangam` so all engines align.

## §4 — Asset registration (service-kind)
`ka_dasha_kala`: `asset_kind='service'`, `layer:'kala'`, sanskrit `'Daśā-kāla'`, english `'Daśā service'`,
`count_sql:null`, `target_table:null`, `depends_on:['ga_dashas']`. Self-test: for `482012f1`, query the
active MD/AD/PD at a known date; assert non-empty, interval-valid, multi-system present → service_health.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** the tree-walk prunes an ineligible MD subtree WITHOUT querying its children
   (call-counter / query-log assertion) — proves the §5.9.1 pruning, not a full scan.
2. **[verify: pytest]** interval algebra: the eligible set for a known signature = the correct UNION of
   `ganita_dashas` intervals (no time-iteration; compare to a hand-computed expected set).
3. **[verify: pytest]** eligibility_score ranks exact-lord-match > dispositor > neutral for a constructed case.
4. **[verify: pytest]** cross-daśā agreement returns the correct count + system list for a window where
   ≥2 systems concur (use the native's real ganita_dashas).
5. **[verify: pytest]** the Sookshma floor: a day-grain query returns level-4 (Sookshma) intervals from
   `chart_dashas`; a Prāṇa-grain query triggers the on-demand IN-MEMORY recursion for the narrow window
   only (assert NO level-5 row is ever written — `cd_level_n_max4` is respected).
6. **[verify: psql_prod]** the 7 stored systems are confirmed in `chart_dashas` for `482012f1`; the service
   serves all present systems; KP resolves as a Vimśottarī sub-level (not a separate system).
7. **[verify: curl_prod]** registered service-kind; cockpit health badge; self-test passes.
8. **[plan-sync]** the campaign plan §5.6/§5.7.4 is updated to the 7 ACTUAL systems (anti-drift).
9. **[contract]** no `ctx.db_conn.commit()/.rollback()` in any self-test writer (plan §9).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-dasha-kala
# inspect the stored timeline + systems
psql_prod -c "SELECT dasha_system, level, count(*) FROM ganita_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1,2 ORDER BY 1,2;"
grep -n "SYSTEMS = " platform/python-sidecar/ga_writers/ga_dashas_writer.py
# tests
cd platform/python-sidecar && pytest -q services/ka_dasha_kala -k "dasha_kala or tree_walk or interval"
```
> Branch/merge: Madhav human-gated PR (plan memory two-stream-branch-policy); Conductor stages, master plan gates.

## §7 — Definition of done
- [ ] Lazy pruning tree-walk over ganita_dashas (pruning proven by test).
- [ ] Interval-algebra eligibility set + eligibility_score (soft prior).
- [ ] Cross-daśā agreement signal (amplifier + discovery flag).
- [ ] PD floor + on-demand deeper-level policy.
- [ ] System set reconciled; plan updated to the 7 actual systems.
- [ ] Registered service-kind; cockpit health; self-test green for 482012f1.
- [ ] PR opened with AC evidence.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Promotes daśā from a one-line afterthought to a co-equal engine** — implements the native's
   central §5.6 correction as real machinery: a scored, multi-system, multi-level daśā prior, not "is
   the dasha supportive at T."
2. **Delivers the funnel's brutal first cut as cheap interval algebra** — the lazy pruning tree-walk
   over precomputed intervals is what lets the whole layer search decades without touching the
   ephemeris until the window is narrowed (the §5.9 efficiency law, realized).
3. **Makes cross-daśā agreement a first-class signal** — turning "do multiple daśā systems concur?"
   into both a confidence amplifier AND a discovery/anomaly flag, which is a genuine independence input
   the rigor stratum's correlation-discount (I-22) needs to avoid echo-chamber overconfidence.
4. **Catches two real plan↔code drifts the audit surfaced** — the level-3 (PD) storage floor and the
   7-actual-systems-vs-5-named mismatch — and resolves them WITH an anti-drift plan-sync, so the layer
   is built on what the data actually contains, not what a doc assumed.
5. **Honors services-not-data at the deepest level** — serving stored PD from the table but computing
   Sookshma/Prāṇa on demand only inside survivors, so the daśā engine never re-creates the
   precompute-everything model the layer rejects.

---
*End of CLAUDECODE_BRIEF_L3_KA_DASHA_KALA v1.0.*
