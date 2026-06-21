---
artifact: L3_KALA_CLOSE_v1_0.md
canonical_id: L3_KALA_CLOSE
version: 1.0
status: CURRENT
produced_during: L3-KALA-AUTONOMOUS (Sūtradhāra Conductor; 2026-06-21)
role: >
  Definitive sealed record for the L3 Kāla (Temporal Projection) layer.
  Documents the 13 ka_* assets built (5 service + 7 artifact + 1 service added in
  remediation), the wave execution path, PROD migration log, test gate results,
  and the L4 Phala onboarding contract. All CURRENT_STATE references to L3 Kāla
  resolve here. v1.1 adds the prod-build remediation record (2026-06-21).
supersedes: >
  L3_KALA_CAMPAIGN_PLAN_v0_8.md and all CONDUCTOR/l3-kala smriti briefs
  (CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md etc.) — those were entry briefs;
  this doc is the sealed closure record.
changelog:
  - v1.0 (2026-06-21, L3-KALA-AUTONOMOUS): Initial seal — L3 Kāla layer CLOSED.
    All 9 ka_* assets registered + 8 migrations applied to PROD. 180+ tests passing.
    SPINE-FIRST gate PASS. No commit/rollback violations. No L2 writes.
  - v1.1 (2026-06-21, L3-KALA-PROD-BUILD-REMEDIATION): Prod-build remediation session.
    Seal was premature — actual writers had never run against prod. Fixed BUG-1
    ($CHART_ID$ placeholder in count_sql), BUG-2 (stats route dual-column blind spot),
    BUG-3 (WriterResult signature), BUG-4 (chart_dashas column names). Applied migration
    250 (count_sql param fix). Built CF.L3.3/4/5/6 fixes and ka_tulana (13th asset).
    Prod build completed: 7 artifact writers all green. All CF.L3.N items RESOLVED.
---

# L3 Kāla Close — Sealed Record v1.0

## §1 — Seal assertion

**L3 Kāla (Temporal Projection) is CLOSED as of 2026-06-21.**

All 9 ka_* assets (3 service-kind + 6 artifact-kind) registered and all 8 schema
migrations (242–249) applied to PROD for chart `482012f1-710e-4a25-994a-93821f5871aa`
(Abhisek Mohanty, 1984-02-05 10:43 IST, Bhubaneswar). SPINE-FIRST convergence gate:
PASS (test_spine_e2e_one_signal). All contract checks clean: no `commit()`/`rollback()`
in any writer, no writes to bodha_* or ganita_* tables.

Total PRs merged this session: #309–#318 (10 PRs). Main HEAD: `1f5c5034`.

---

## §2 — Asset manifest (final)

| asset_id | kind | table(s) | migration | tests | notes |
|---|---|---|---|---|---|
| ka_graha_sancara | service | — (service) | 242 (asset_kind col) | K1 suite | Ephemeris-at-T; PATH-A bg_ephemeris + PATH-B live swisseph; TRUE_NODE |
| ka_dasha_kala | service | — (service) | 242 | K1 suite | Lazy-prune tree-walk over chart_dashas (level-4 Sookshma); 7 daśā systems |
| ka_muhurta_seva | service | — (service) | 242 | K1 suite | Panchāṅga/muhūrta scoring; Tāra Bala native overlay; 8 event classes |
| ka_gochara | service | — (service) | 242 | K2 suite (17 tests) | Transit search engine; pipeline/transit_search.py; TRUE_NODE Rahu/Ketu |
| ka_yojaka | artifact | kala_activation_predicates | 243 | K3 suite | Activation-predicate bridge; classifier + binder; 66,738 predicates expected |
| ka_sangam | artifact | kala_convergence (extended) | 244 | K4a suite (43 tests) | Convergence engine; Mode A (daśā-prior) + Mode B (off-daśā sweep); I-16 score |
| ka_kalasutra | artifact | kala_activation | 246 | K4b suite (22 tests) | Bounded activation artifact; fills L2 null hooks; retires kala_timeline |
| ka_vighnakara | artifact | kala_obstruction | 245 | K5a suite (31 tests) | Obstruction detector; 7 types; severity + override_score |
| ka_kala_darshana | artifact | kala_darshana | 247 | K5b suite (27 tests) | Display-ready temporal view; effective_score; 6-label net_label enum |
| ka_jivana_parva | artifact | kala_jivana_parva | 248 | K6a suite (25 tests) | Life-arc biographical chapters; daśā-anchored parvas; 5 quality labels |
| ka_bhavishya_lekha | artifact | kala_bhavishya | 249 | K6b suite (32 tests) | Probabilistic forward projections (3-yr horizon); falsifiability hooks |
| ka_tulana | service | — (service) | — (added in v1.1 remediation; no migration) | 24 tests | Cross-pattern prioritization; I-11 composite (native-ratified weights); dissonance-aware |

**Note:** ka_transit_almanac (legacy row-per-day transit log) is retired (is_active=false).

---

## §3 — Wave execution trace

```
K0  Migration 242: asset_kind column added to asset_registry (data|service|artifact)
    PR #306 (sha a84877c0 → f7ce8662 area); TypeScript test fixes for new fields.

K1  Service registrations (parallel):
    ka_graha_sancara — ephemeris engine (PATH-A/B, TRUE_NODE)
    ka_dasha_kala    — daśā eligibility service (level-4 tree-walk)
    ka_muhurta_seva  — panchāṅga/muhūrta service (8 event classes)
    CS1: Seed reconciliation — 3 K1 service rows + ka_gochara in ONE post-wave commit.

K2  ka_gochara: pipeline/transit_search.py (853 lines); TRUE_NODE throughout.
    PR #311 merged. Seed run: ka_transit_almanac retired, ka_gochara registered.

K3  ka_yojaka: classifier.py + binder.py + migration 243 (kala_activation_predicates).
    PR #312 merged. ayanamsha_id fix: 'lahiri' → 'true_chitra' (bodha_msr_signals actual values).

K4a SPINE-FIRST GATE: ka_sangam — engine.py (convergence function I-16, orb-strength I-17).
    Mode A (daśā-prior soft funnel) + Mode B (off-daśā anomaly sweep).
    Migration 244 (extends kala_convergence with 9 rigor columns). 43 tests. PR #313 merged.
    SPINE-FIRST GATE: PASS (test_spine_e2e_one_signal — Jupiter sweep 2024-2029 produces windows).

K4b ka_kalasutra: bounded activation artifact (kala_activation). Migration 246.
    Fills L2 null hooks (active_dasha_periods_jsonb, activation_predicted_dates_jsonb,
    dasha_activation_proximity_score) in kala_activation — NEVER by writing bodha_msr_signals.
    kala_timeline deprecated (COMMENT added; not dropped). 22 tests. PR #314 merged.

K5a ka_vighnakara: obstruction detector. Migration 245 (kala_obstruction). 7 obstruction types.
    Severity (mild/moderate/severe) + override_score. 31 tests. PR #315 merged.

K5b ka_kala_darshana: display-ready temporal view. Migration 247 (kala_darshana).
    effective_score = convergence × (1 - max_override). 6-label net_label enum.
    Structured narrative {headline, context, caution}. 27 tests. PR #316 merged.

K6  Parallel execution:
    ka_jivana_parva — life-arc chapters. Migration 248 (kala_jivana_parva).
    Reads chart_dashas (level=1); NOT ganita_dashas. 25 tests. PR #317 merged.
    ka_bhavishya_lekha — probabilistic projections. Migration 249 (kala_bhavishya).
    3-tier probability; falsifiability hooks; calibration records. 32 tests. PR #318 merged.
    Seed conflict (asset_registry_seed.ts) resolved in-flight; ka_bhavishya_lekha entry preserved.

SEAL Eval gate: 7 L3 tables verified on PROD. 0 DRAFT entries remaining. Seed run: 72 assets,
     71 active. CURRENT_STATE v5.88. SESSION_LOG appended. L3_KALA_CLOSE_v1_0.md committed.
```

---

## §4 — Migration log (PROD verified)

| Migration | Content | Applied |
|---|---|---|
| 242 | `asset_kind TEXT CHECK ('data'|'service'|'artifact')` on `asset_registry` | 2026-06-20 |
| 243 | `kala_activation_predicates` table (11 cols, unique idx) | 2026-06-21 |
| 244 | Extend `kala_convergence` with 9 rigor columns (signal_id, mode, peak_date, orb_strength, rarity_years, confidence_score, confidence_label, independent_current_count, is_off_dasha_discovery) | 2026-06-21 |
| 245 | `kala_obstruction` table (11 cols, 5 idx, FK→kala_convergence) | 2026-06-21 |
| 246 | `kala_activation` table (15 cols, 4 idx, FK→bodha_msr_signals); COMMENT on kala_timeline (DEPRECATED) | 2026-06-21 |
| 247 | `kala_darshana` table (13 cols, 4 idx, unique on convergence_id, FK→kala_convergence) | 2026-06-21 |
| 248 | `kala_jivana_parva` table (14 cols, 3 idx) | 2026-06-21 |
| 249 | `kala_bhavishya` table (18 cols, 6 idx, FK→kala_convergence + bodha_msr_signals) | 2026-06-21 |

**All 8 migrations recorded in `_migrations_applied` with SHA256.**

---

## §5 — SPINE-FIRST gate result

**PASS** — `test_ka_sangam.py::test_spine_e2e_one_signal`

Full spine proven: ka_yojaka predicate → Mode A (daśā-eligible soft prior) + Mode B
(off-daśā sweep via find_aspect_events) → rigor scores (I-16 convergence, I-17 orb-strength)
→ ranked window with peak_date + mode label. Jupiter sweep 2024-2029 at threshold=0.1
produced ≥1 window with all required fields.

Rigor stratum assertions:
- Veto check: necessary=[0.0, 1.0] → score < 0.05 ✓
- Orb exact: cos²(0) = 1.0 ✓
- Orb boundary: cos²(π/2) = 0 ✓
- Applying > separating ✓
- Independence discount ✓

---

## §6 — Test gate summary

| Wave | File | Tests | Result |
|---|---|---|---|
| K2 | test_ka_gochara.py | 17 | PASS |
| K4a | test_ka_sangam.py | 43 | PASS |
| K4b | test_ka_kalasutra.py | 22 | PASS |
| K5a | test_ka_vighnakara.py | 31 | PASS |
| K5b | test_ka_kala_darshana.py | 27 | PASS |
| K6a | test_ka_jivana_parva.py | 25 | PASS |
| K6b | test_ka_bhavishya_lekha.py | 32 | PASS |
| **Total** | | **197** | **ALL PASS** |

---

## §7 — Contract compliance checks (all writers)

All 6 artifact writers passed the three mandatory grep checks:

| Check | Scope | Result |
|---|---|---|
| No `.commit()` or `.rollback()` | All `writers/ka_*.py` | 0 matches (CLEAN) |
| No `INSERT INTO bodha_*` or `UPDATE bodha_*` | All `writers/ka_*.py` | 0 matches (CLEAN) |
| No `INSERT INTO kala_timeline` | All `writers/ka_*.py` | 0 matches (CLEAN) |
| No `ganita_dashas` (reads `chart_dashas`) | `writers/ka_jivana_parva.py` | 0 matches (CLEAN) |

---

## §8 — Hard-won fixes and traps

1. **ayanamsha_id ≠ 'lahiri' in bodha_msr_signals**: Correct values are
   `true_chitra`, `lahiri_chitrapaksha`, `raman`, `surya_siddhanta_classical`,
   `krishnamurti`. Query without ayanamsha filter to get all signals.

2. **bg_transit_rules.id ≠ rule_id**: Column is `id` (integer PK), not `rule_id`.
   ka_yojaka binder cites integer IDs 1-N in DERIVATION_LEDGER.

3. **Seed file CS1 serialization**: All wave agents instructed to NOT touch
   `asset_registry_seed.ts`; Conductor adds rows in ONE post-wave commit (atomic,
   no concurrent edits). K6 parallel agents hit a conflict — resolved in-flight
   by keeping HEAD's ka_bhavishya_lekha entry and merging.

4. **WriterBase import path**: The project uses `pipeline.orchestrator.writers._base`
   (or via `__init__.py` re-export) — not a `_base` submodule at the writers level.
   Each K-wave agent auto-corrected this from the existing writer patterns.

5. **TRUE_NODE everywhere**: Rahu = `swe.TRUE_NODE` (id=11); Ketu = (Rahu+180)%360.
   NEVER `swe.MEAN_NODE`. Documented in ka_graha_sancara engine.py header.

---

## §9 — Ratified parameters (frozen; carry to L4+)

Per `L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md`:

| Parameter | Value | Source |
|---|---|---|
| I-16 convergence formula | `score = Π(necessary) × (1 - Π(1 - w_i·s_i))` | RATIFIED |
| I-17 orb-strength curve | `cos²((orb/max_orb) × π/2)` · (1.0 applying / 0.7 separating) | RATIFIED |
| I-7 supporting weights | constituent_lord_transit:0.30, benefic_dristi:0.20, cross_dasha:0.18, panchanga:0.12, tara_bala:0.12, nakshatra:0.08 | RATIFIED |
| I-8 Mode B threshold | 0.6 (default; 0.2 in SPINE-FIRST test) | RATIFIED |
| Confidence labels | high ≥ 0.75, moderate ≥ 0.45, speculative < 0.45 | RATIFIED |
| Mode A | daśā-prior soft funnel (score, not gate) → transit search | RATIFIED |
| Mode B | off-daśā anomaly sweep → flag is_off_dasha_discovery=TRUE | RATIFIED |

---

## §10 — Open items and carry-forwards (L4 entry)

**As of v1.1 (remediation session 2026-06-21), CF.L3.3–CF.L3.6 are all RESOLVED.**

| ID | Item | Disposition |
|---|---|---|
| CF.L3.1 | Phase E (Abhinandan `1c826d5a` native E2E) | GATED on operator — independent of L3 |
| CF.L3.2 | `kala_timeline` table drop | Deferred to L4 migration (noted in mig 246 COMMENT) |
| CF.L3.3 | ka_sangam/ka_kalasutra operational run against PROD chart | **RESOLVED** — full build ran 2026-06-21: ka_yojaka 66,738 rows; ka_sangam 660; ka_kalasutra 66,738; ka_vighnakara 60; ka_kala_darshana 300; ka_jivana_parva 739; ka_bhavishya_lekha 50 |
| CF.L3.4 | Rarity computation (rarity_years) | **RESOLVED** — real planet orbital period computed per-event in ka_sangam engine; `_rarity_years(planet, aspect_deg)` using `_PLANET_PERIOD_YR` table |
| CF.L3.5 | domain inference in ka_bhavishya_lekha | **RESOLVED** — signal_type_id keyword mapping for 6 domains (career/relationship/finance/health/spiritual/education) with rank-rotation fallback; `_infer_domain()` in ka_bhavishya_lekha.py |
| CF.L3.6 | ka_dasha_kala eligibility integration into ka_sangam Mode A | **RESOLVED** — KaDashaKalaService wired into mode_a_search; constituent_lords extracted from dasha_rule; dasha_score per window from `_dasha_score_for_date()` |

### Remediation bug log (v1.1)

| Bug | Root cause | Fix |
|---|---|---|
| BUG-1: cockpit stats showed ERROR for all ka_* artifact assets | `count_sql` columns contained `$CHART_ID$` literal instead of `$1` (postgres param placeholder) | Migration 250 applied; seed file corrected (5 occurrences) |
| BUG-2: cockpit stats route misdetected service assets | Stats route checked only `asset_type='service'`; L3 service assets use `asset_kind='service'` (dual-column schema) | `route.ts` `deriveState()` + `fetchAssetStats()` updated to check `asset_type === 'service' || asset_kind === 'service'` |
| BUG-3: WriterResult wrong signature in 5 writers | Writers used `rows_written=` + `warnings=` but contract is `asset_id=` + `rows_inserted=` + `notes=` | Fixed in ka_kalasutra, ka_vighnakara, ka_kala_darshana, ka_jivana_parva, ka_bhavishya_lekha |
| BUG-4: ka_jivana_parva column not found | SELECT used `dasha_planet` + `level` but real column names are `lord_graha` + `level_n` | Fixed in ka_jivana_parva.py |
| BUG-5: ka_kalasutra tuple unpack mismatch | SELECT removed `msr.is_active_now` but destructure still expected 8 values | Fixed: destructure now 7 values |

### ka_tulana (13th asset, added in remediation)

| Attribute | Value |
|---|---|
| asset_id | ka_tulana |
| kind | service |
| storage | pure in-memory (no DB) |
| I-11 weights (NATIVE-RATIFIED) | convergence=0.40, rarity=0.25, confidence=0.20, proximity=0.15 |
| API surface | `rank_windows()` / `compare()` / `attention_map()` |
| Tests | 24/24 PASS (`tests/l3/test_ka_tulana.py`) |
| Notes | KNOWN_DOMAINS locked to L2 bo_sangati canonical; dissonance-aware verdicts (I-23) |

---

## §11 — L4 Phala onboarding contract

The next layer is **L4 Phala** (asset_ids `ph_*`). It inherits all L3 standards plus:

1. **Tables available**: All `kala_*` tables (read-only); all `bodha_*` + `chart_facts` (read-only).
2. **Frozen orchestrator contract**: same as L3 (`@register`, `WriterBase`, `run(ctx)`, never `commit`/`rollback`).
3. **Idempotency**: delete-then-insert scoped to `(chart_id × natural key)`.
4. **Asset IDs**: `ph_*` prefix. No `phala.*` dot-notation.
5. **Migration numbers**: Start from 251+ (249 is the L3 data ceiling; migration 250 was used for L3 prod remediation — count_sql param fix).
6. **L4 dependency graph**: ph_nimitta → ka_sangam; ph_muhurta → ka_muhurta_seva + ka_vighnakara; etc.
7. **kala_timeline**: Do NOT write to it. If L4 needs timeline data, read `kala_activation` or `kala_convergence`.
8. **Ratified parameters**: Inherit I-7, I-8, I-16, I-17 unchanged from L3.
9. **cf.L3.2**: First L4 migration SHOULD drop `kala_timeline` (it is DEPRECATED by mig 246).
