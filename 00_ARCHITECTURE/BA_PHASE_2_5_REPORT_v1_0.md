---
artifact: BA_PHASE_2_5_REPORT_v1_0.md
canonical_id: BA_PHASE_2_5_REPORT
version: 1.0
status: CLOSED
created: 2026-07-05
governing_brief: CLAUDECODE_BRIEF_BA_PHASE_2_5_CONSOLIDATED_v1_0.md
merged_pr: "#433 (audit/ba-full-asset-audit -> main), merge commit c3d4850912ad8a0fb35cf491b12ea4cbd7d322d6"
---

# BA Phase 2.5 (Consolidated) — Exit Report

## §0 — Verdict

**REBUILD-READY: YES (global).**

`python -m pipeline.orchestrator.dag_edge_guard` — re-run against the live post-merge, post-deploy database
via a data-equivalent reconstruction (live `asset_registry` + live `information_schema.tables` fetched by
direct read-only query, fed into the guard's own pure `evaluate()` function together with the actual on-disk
writer source) — reports:

```
checked 91 writer assets
OK — no hard edge-completeness violations
```

Zero SOFT warnings, zero HARD violations, 91/91 writer assets checked (matches the full registered-writer
count exactly — confirms the registry-completeness fixes below left no writer un-registered).

## §1 — Phase 0: land + deploy + verify

| Step | Status |
|---|---|
| Push branch, open PR #433, CI green | DONE — 24 commits, all CI gates passed (Coverage, Governance, ICR, Naming, Planner, Secret Scan, TypeScript x2, Unit Tests, Build Check) |
| Merge → deploy | DONE — merged `c3d48509`; `Deploy to Cloud Run` run `28742543499` succeeded (`Build & Deploy Web`, `Build & Deploy Pipeline Job Image`, `Build & Deploy Sidecar` all green) |
| Migrations 405–413 applied | DONE — confirmed via deploy log: `Applied: 405_bg_remedies_floor_recorrection.sql` through `413_depends_on_derivation_ledger_docs.sql` (9 migrations, all applied in one deploy run) |
| Live verify: `bg_remedies.target_floor` | **266** (was 800) — confirmed live |
| Live verify: `ka_yojaka`/`ka_avadhi`/`ka_taranga`/`mi_darshana` `depends_on` | All corrected live — confirmed via direct query |
| Live verify: `phala_sodhana` CHECK constraint | `phala_sodhana_anomaly_type_check` now includes `'confidence_degenerate'` — confirmed live |
| `dag_edge_guard` exit 0 | **DONE** (see §0) |

The JOB image was rebuilt as part of the same deploy run (`Build & Deploy Pipeline Job Image` job) — writers
run from the merged HEAD.

## §2 — Phase 1: the 9 open code-level BLOCKERs

| # | Item | Outcome | Commit(s) |
|---|---|---|---|
| J9 | `mi_pariksha` neg-control tautology | `status='not_implemented'` — honest status instead of a tautological pass | `904fc190` |
| J10 | `mi_abhilekha` unscoped clear + full allowlist classification | Scoped clear preserving answered rows; same fix applied to a second, previously-undiscovered instance (`mi_bhavisya`/`mimamsa_predictions.outcome_observed`); documented REBUILDABLE vs IRREPLACEABLE classification in `assetClearSpec.ts` | `904fc190` |
| #8 | `ph_nimitta` hardcoded posterior inputs | Wired real `bodha_pratijna` (domain-overlap join) + real `ka_yojaka` (`multi_system_confirmation_count`) inputs; `av_transit_potency` left as documented placeholder (no real scalar source exists — B.10) | `35758d56` |
| #11 | `ph_rectification` TRAINING_EVENTS contamination | JL-017: `NATIVE_CHART_ID` gate — writer now refuses (raises) for any chart other than the native's, rather than silently scoring it against the native's own life events | `26c47a7e` |
| #4 | `ga_sade_sati` unenriched `natal_facts` stub | Real per-chart/per-cycle GA3/GA4/GA6/GA7/GA8 lookups (Lagna-sign yoga-karaka table, Saturn/Moon aspect + parivartana, dispositor strength, tara-bala, argala, dasha-lord-at-phase); 6 inputs left as honest placeholders (no upstream transit-detection engine exists) | `3a488219` |
| #12 | `mi_jivanaghatana` LEL 33/63 unparseable blocks | Root cause confirmed (unquoted colons in narrative prose breaking YAML block-mapping); mechanical content-preserving fix raises parseable blocks 34/63→48/63; proposed diff prepared for native review, canonical `LIFE_EVENT_LOG_v1_2.md` **NOT touched** per hard rule | `5d102fae` |
| #6/#7 | `ka_vighnakara`/`ka_kala_darshana`/`ka_bhavishya_lekha` 0-row + stale `asset_throughput` | New standalone guard (`kala_derivation_completeness_guard.py`) distinguishes legitimate upstream-empty early-returns from genuine derivation gaps; `asset_throughput` drift check added (informational, §N.4) | `29c8594d` |
| #5 | `bo_pramana_mapa`/`bo_samskara` rebuild correctness | Verified: both already fixed at HEAD by prior-session commits (`7295f1ff`, `a8a786a2`) — no further action needed | verified, no new commit |
| #9/#10 | `ph_pratikara`/`ph_phaladesa` freshness | Verified: both already correctly delete-then-insert per chart; no bug found | verified, no new commit |

## §3 — Phase 3: the 10 ratified judgment implementations (J1–J10)

All 10 implemented exactly as ratified (JL-011..020, appended to `BA_JUDGMENT_LEDGER_v1_0.md` in commit `b49b9ad1`):

| Ruling | Implementation | Commit(s) |
|---|---|---|
| J1 | `bg_rules.yoga_canonical_id`: bigram + Tier-1 bare-name + hard-exclusion extraction, collision→NULL+flag. **Bonus catch:** 5 Tier-1 names' naive slugs didn't match the real `brahma_yoga_catalog.canonical_id` — would have silently been discarded downstream; fixed. | `c3a95e6e` |
| J2 | `ga_structural.count_sql` → `fact_category_ownership` registry (single source of truth), retiring the twice-drifted (migrations 364, 368) hand-maintained allow-list. Verified byte-identical row count (98,314) vs. the old query before cutover. | `20b7a40a`, migration 410 |
| J3 | `ga_yoga.strength` = `constituent_bala_v1` (normalized shadbala of constituent grahas); `bhanga_active` NULL-with-documented-reason where no classical bhanga exists; Kemadruma's existing bhanga logic untouched. | `9c00601f`, migration 411 |
| J4 | `bo_cgm_paths.path_strength` = PRODUCT of constituent edges (never average); zero-hop self-ruling chains = 1.0; degeneracy-gate warning added. | `5214a3bd` |
| J5 | `ka_sangam` interim within-chart percentile tier (`confidence_label_relative`, `tier_basis='relative_uncalibrated'`), additive to I-21's absolute `confidence_label` (never replaced); absolute recalibration explicitly deferred to P5A. | `de579c82`, migration 409 |
| J6 | `ph_muhurta` tarabala/chandrabala wired to the real classical formulas already in `panchang_engine/tara_bala.py`; gochara left as documented placeholder (no `kala_gochara` persistence table exists). | `943e9060` |
| J7 | `ph_rectification` D41 bounded extension: antar-dasha (AD) lord double-match scoring, derived closed-form from the two already-documented MD boundaries (zero new facts). Full bhava-cusp/navamsa D41 scoring remains future work (explicitly out of scope, would require new ephemeris computation). | `30f79210` |
| J8 | `mi_pramana` manifestation dimension dropped (no real scorer existed behind it); remaining 4 weights renormalized to sum=1.0; dropped dimension registered (`mi_pramana_dropped_dimensions`) for a future P6 pass. | `4cfd176a`, migration 408 |
| J9 | (see §2) | `904fc190` |
| J10 | (see §2) | `904fc190` |

## §4 — Phase 2: MAJOR fast-follows

| # | Item | Outcome | Commit(s) |
|---|---|---|---|
| #2 | `ga_condition.weak_dasha_periods` permanently NULL | Symmetric fix mirroring `peak_dasha_periods`'s own condition-score threshold logic (inverted for weak); also fixed a structural bug where the natal_facts-style dict was built once outside the per-cycle loop | `aecc4940` |
| #3 | (superseded — see J3 above) | — | `9c00601f` |
| #4 | `bo_upaya.resonance_score_v1` 5 hardcoded 0.0 inputs | 3 of 5 wired to real data (dispositor-chain weakness via `composite_dispositor_strength`, dasha-timing proximity via `chart_dashas`, CGM motif weakness via `bodha_cgm_motifs`); 2 left as honest placeholders (no real source exists) | `f4508330`, migration 412 |
| #8 | `mi_adhilepa` thin/nondeterministic overlay slice | Root cause was worse than described: `WHERE fact_category IN ('graha','yoga')` matched literally zero rows ever (not real category values). Replaced with full per-chart scan + deterministic `ORDER BY fact_id` + Python-side family classification (ashtakavarga/dasha/divisional/yoga/graha-natal) | `bc4d3112` |
| #9 | 11 non-blocking `depends_on` documentation gaps | All addressed: `bo_pratijna`→`bg_ghatana` (`2331adbe`), `ka_yojaka`/`ka_avadhi`/`ka_taranga`/`mi_darshana` via migration 406 (prior session, now applied), `mi_kula`/`mi_pramana`/`mi_gunanaka`/`mi_pariksha`/`mi_jivanaghatana`→`bg_*` (`c9be6466`, migration 413), `bo_upaya`→ real deps (migration 412). `ph_muhurta`→`bg_ghatana` from the original finding could not be confirmed against current source and was omitted rather than asserted unverified. | `2331adbe`, `c9be6466` |
| #10 | `dag_edge_guard.py` false-positive on commented-out reads | Fixed: strips `#`/`--` comments before FROM/JOIN regex matching (previously only applied to `count_sql`, not writer source) | `551f324f` |
| — | Seed/ingestion gaps (`bg_reference` under-floor, `ph_pramana` empty `life_events`) | Per brief instruction, **prepared + flagged for native, not forced.** `bg_reference` is a static global reference table (no per-chart ingestion path to fix); `ph_pramana`'s `life_events` gap depends on the LEL YAML fix (§2 #12) landing first. | not actioned (correctly deferred) |

## §5 — Registry-completeness discovery (unplanned, found during Phase 2/3 work)

Systematic diff of every `@register('...')` asset_id in the writer source tree against
`asset_registry_seed.ts` found **8 real, live, already-`@register`'d writers with zero catalog entry**:
`bg_class_priors`, `bg_formula_constants`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`,
`bo_chart_gestalt`, `ka_avadhi`, `ka_taranga` (in addition to `bo_pratijna`/`bg_ghatana`, found and fixed
first, which is what originally broke CI on this branch). All 8 confirmed to have real live tables with
rows already; a future reseed-from-scratch would have silently dropped every one of them. All 8 now
registered with live-verified row counts and correct `depends_on`. Confirmed via a second diff pass: **zero
registered writers remain unregistered** in the seed catalog.

`bo_chart_gestalt` specifically supersedes a stale comment on the `bo_samvada` seed entry (from migration
326) claiming `bodha_chart_gestalt` "has 0 rows and is never populated" — it is now live and populated (5
rows); the comment went stale specifically because this asset was never registered to track it.

Commits: `2331adbe`, `d854fc39`.

## §6 — Test suite

- Python sidecar full suite: 2,854 tests, 29 pre-existing failures (all confirmed via `git stash` comparison
  to predate this session — 27 are `integration`-marked/`TestProdDB` tests requiring `DATABASE_URL`
  (excluded from CI's actual invocation), 2 are a pre-existing `bg_remedies` corpus data bug (`planet: 'sun'`
  vs `'Sun'`) unrelated to any BA Phase 2.5 scope). **Zero regressions.**
- Frontend (`platform/`) full suite: 5,117 tests passing, 0 failing (one governance gate —
  `AssetRow_CockpitPolishR2.test.tsx`'s hardcoded kala-asset-count — updated 12→14 to reflect the legitimate
  `ka_avadhi`/`ka_taranga` registry-completeness fix; the test's actual governance intent, blocking
  `ka_transit_almanac`'s reappearance, is preserved by its companion assertion).
- CI (PR #433): all gates green — Coverage Gate, Governance Gates (drift/schema/edge/native-literal/py-sidecar),
  ICR PR Gate, Naming Governance Gate, Planner Regression Gate, Secret Scan, TypeScript ×2, Unit Tests, Build Check.

## §7 — Migrations applied this phase (405 already existed from the prior session; 408–413 new)

| # | File | Purpose |
|---|---|---|
| 408 | `408_mi_pramana_drop_manifestation_dimension.sql` | J8 weight renormalization + dropped-dimension registry |
| 409 | `409_kala_convergence_relative_tier.sql` | J5 interim relative-tier columns |
| 410 | `410_ga_structural_category_ownership.sql` | J2 `fact_category_ownership` table + count_sql cutover |
| 411 | `411_ga_yoga_constituent_bala_strength.sql` | J3 strength/derivation/citation columns |
| 412 | `412_bo_upaya_dag_edge_completeness.sql` | #4 fast-follow real depends_on edges |
| 413 | `413_depends_on_derivation_ledger_docs.sql` | #9 consolidated depends_on documentation edges |

All 6 reviewed by the `migration-guard` subagent before merge; 2 blockers caught and fixed pre-merge
(migration 408's non-idempotent citation-string concatenation; migration 410's missing existence guard) —
both now follow the `IF NOT FOUND THEN RAISE EXCEPTION` pattern established by migration 408's own fix.

## §8 — Native-judgment spot-check items (flagged in the governing brief for strategic-track review)

Per the brief's own hand-back instruction, these 3 highest-risk rulings should be spot-checked before the
deferred full rebuild is scheduled:

1. **J1 collisions→NULL**: verified in code (`detect_yoga_reference` returns `yoga_canonical_id=None` +
   `yoga_ambiguous=True` on any 2-distinct-candidate match) and covered by unit tests.
2. **J3 no invented formula**: verified — `constituent_bala_v1` is exactly "mean of normalized
   actual/required-rupa shadbala," the one and only formula permitted by the ruling; no per-yoga weighting.
3. **J4 product-not-average**: verified — `_path_strength()` multiplies constituent edge strengths; unit
   tests explicitly assert a weak edge drags the whole chain down (proving it is not an average that could
   hide a weak link).

## §9 — What was NOT done (correctly, per hard rules)

- No cockpit build/rebuild triggered.
- No per-chart data hand-patched.
- No LEL markdown edit committed (proposed diff only, native sign-off required).
- No fabricated formula/weighting anywhere — every placeholder left honest and documented where no real
  source existed (`av_transit_potency`, 2 of `bo_upaya`'s 5 resonance inputs, `ph_muhurta`'s gochara,
  full D41 bhava-cusp/navamsa scoring).
- `ph_muhurta`→`bg_ghatana` depends_on edge from the original audit finding was NOT asserted (could not be
  confirmed against current source — omitted rather than guessed).
- `mi_pariksha_attribution_weights` (mirrors `mi_pramana_scoring_weights`) intentionally left untouched —
  flagged as a known, deliberate divergence pending a symmetric follow-up, not silently fixed or ignored.

## §10 — Handback

Global `REBUILD-READY = YES`. Hand back to the strategic track for the gate-check + 3-item spot-check above
before scheduling the deferred full Abhinandan rebuild.
