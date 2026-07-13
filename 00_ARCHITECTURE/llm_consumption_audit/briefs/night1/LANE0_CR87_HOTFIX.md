---
artifact: NIGHT1_LANE0_CR87_HOTFIX
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L0 — CR-87 hotfix (independent lane; ships regardless of D-1 progress)
depends_on_lanes: NONE (fully parallel; may merge first)
register_rows: CR-87 (CRIT), touches nothing else
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §13 (bug paragraph only)
---

# LANE 0 — De-hardcode native natal constants from shared convergence-engine code (CR-87)

## 0. Why (verbatim from the register — CR-87, CRIT)

> **CRITICAL: one native's natal constants are hardcoded into SHARED convergence-engine code.** `engine.py:253` `_NATIVE_JANMA_NAK_IDX=24` (Purva Bhadrapada); `:1146-1149` Mode-C sade-sati signs Cap/Aqu/Pis for Aquarius Moon; `ka_sangam.py:35-39` `_NATIVE_LOCATION` = Bhubaneswar lat/lon/tz. **Tara-bala (C_tara), sade-sati (Mode C), and panchanga (C_panchanga) currents are therefore computed against chart 482012f1 for EVERY chart** — Abhinandan's and every future native's activation scores are silently wrong.

## 1. Exact scope — files to touch (VERIFIED ground truth, 2026-07-13)

All paths relative to `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/`.

| # | File : line (verified) | Hardcoded constant | What it feeds |
|---|---|---|---|
| 1 | `services/ka_sangam/engine.py:253` | `_NATIVE_JANMA_NAK_IDX: int = 24` | `_tara_score_for_nakshatra` (`:275`), `_c_nakshatra_subsystem`, `_c_tara_bala_for_jd` — the C5/C_tara currents |
| 2 | `services/ka_sangam/engine.py:~1146-1150` | `_SADE_SATI_SIGNS = ('Capricorn', 'Aquarius', 'Pisces')` + `_SADE_SATI_SEVERITY = {'Capricorn': 0.70, 'Aquarius': 1.00, 'Pisces': 0.70}` (comment: "Native Moon sign: Aquarius") | Mode C `mode_c_subsystem_period` sade-sati activation |
| 3 | `pipeline/orchestrator/writers/ka_sangam.py:35-39` | `_NATIVE_LOCATION = {'lat': 20.2961, 'lon': 85.8245, 'tz_offset_minutes': 330}` (Bhubaneswar), used at `:345` and `:364` | panchanga/muhurta currents (C_panchanga) |
| 4 | `pipeline/orchestrator/writers/ka_vighnakara.py:208` | `_NATIVE_LOC = {'lat': 20.2961, 'lon': 85.8245, 'tz_offset_minutes': 330}`, used at `:228`, `:264` | same bug class, found during brief verification — **in scope, same fix** |

**Ground-truth correction you must respect:** `pipeline/orchestrator/writers/ka_kalasutra.py` was named in an earlier scope note but has been **verified clean** (no hardcoded natal constants — read it before believing otherwise; it resolves per-chart via `services.ka_temporal`). Do not "fix" it; do not touch it.

Line numbers may have drifted a few lines by the time you execute. Re-locate each constant with:
```bash
grep -rn "_NATIVE" platform/python-sidecar/services/ka_sangam/ platform/python-sidecar/pipeline/orchestrator/writers/
grep -n "_SADE_SATI_SIGNS" platform/python-sidecar/services/ka_sangam/engine.py
```

## 2. The fix — per-chart resolution from chart data

### 2.1 Design rule

`services/ka_sangam/engine.py` is a **library/service**, not a frozen surface — its function signatures MAY change (the FROZEN thing in this codebase is the orchestrator `WriterBase` contract, which this lane does not touch). The writers (`ka_sangam.py`, `ka_vighnakara.py`) ARE `WriterBase` subclasses — they keep their frozen shape (`run(ctx)`/substeps, `ctx.db_conn`, never commit) and simply pass per-chart values into the engine.

Introduce one explicit context object (or plain keyword parameters — pick whichever is the smaller diff, but be consistent) carrying:

```python
@dataclass
class NativeChartContext:
    janma_nakshatra_idx: int      # 0-based index into _NAKSHATRAS_ORDERED
    moon_sign: str                # e.g. "Aquarius"
    sade_sati_signs: tuple[str, str, str]      # (12th-from-Moon, Moon sign, 2nd-from-Moon)
    sade_sati_severity: dict[str, float]       # {12th: 0.70, moon: 1.00, 2nd: 0.70}
    location: dict                # {'lat': float, 'lon': float, 'tz_offset_minutes': int}
```

- `sade_sati_signs` is DERIVED from `moon_sign` by fixed rule: the sign before the Moon sign, the Moon sign, the sign after (zodiacal order). Severity weights stay the existing literals 0.70/1.00/0.70 — those are doctrine constants, not natal constants; keep them, but key them by derived sign.
- Engine module-level constants `_NATIVE_JANMA_NAK_IDX`, `_SADE_SATI_SIGNS`, `_SADE_SATI_SEVERITY` are **deleted** (not defaulted — a default silently reintroduces the bug). Every engine function that used them takes the context (or the specific value) as a required parameter. If a call site cannot supply the value, that is a loud error, not a fallback to 482012f1's values. (`_AYUR_SIGNS_*` and `_VASTU_SIGNS` in the same block are lagna-relative comments but hardcoded for Aries lagna — 482012f1 AND 1c826d5a are being scored with them today. If the diff is small, derive them from the chart's lagna sign the same way; if it grows the lane, leave them and file the residual in the lane report. Janma-nakshatra, sade-sati, and location are the mandatory three.)

### 2.2 Where the per-chart values come from (B.10 — never invent, always resolve)

In the writers (which hold `ctx.db_conn` + `ctx.config['chart_id']`), resolve once per run:

1. **Janma nakshatra**: the Moon's nakshatra from `chart_facts` (ga_nakshatra / ga_positions families — find the fact with `fact_subject='MOON'` carrying the nakshatra name; grep `chart_facts` categories for `nakshatra` to pick the exact category, e.g. via `SELECT DISTINCT fact_category FROM chart_facts WHERE fact_category ILIKE '%nakshatra%' LIMIT 20`). Map name → index via the engine's existing `_NAK_NAME_TO_IDX`. For 482012f1 the resolved value MUST equal 24 (Purva Bhadrapada) — assert this in the regression test, not in the production path.
2. **Moon sign**: Moon's D1 sign from `chart_facts` (positions/dignity family). 482012f1 → Aquarius.
3. **Birth location**: `ctx.config['birth_params']` (the orchestrator provides it; provider = `pipeline/orchestrator/birth_params.py`, which reads `public.charts` incl. lat/lon/timezone). Only if `birth_params` lacks lat/lon do you fall back to querying `public.charts` directly by `chart_id`. **Never** fall back to Bhubaneswar.
4. If any of the three cannot be resolved → the writer returns a `WriterResult` with an explicit note and **skips the affected currents loudly** (score them 0 with a `source_citation` naming the missing input), or fails the sub-step — pick fail-loud. Do NOT proceed with another chart's constants (that is the exact CR-87 failure mode).

### 2.3 What stays byte-identical

For chart `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek — Moon Purva Bhadrapada idx 24, Moon sign Aquarius, Bhubaneswar 20.2961/85.8245/IST), the resolved per-chart values equal the old hardcoded constants, so **Abhisek's convergence scores must be bit-identical before/after this change**. That equality is the core regression assertion (see §4).

## 3. Tests to add (the 2-chart regression guard — in scope, mandatory)

Location: `platform/python-sidecar/tests/` (follow the style of existing tests there, e.g. `tests/test_contamination_guard.py` which already uses both chart IDs).

1. **Unit — tara**: `_tara_score_for_nakshatra` (new signature) returns different scores for the same transit nakshatra when `janma_nakshatra_idx` differs (e.g. idx 24 vs Abhinandan's janma index — resolve Abhinandan's Moon nakshatra from his chart facts in the test fixture, or hardcode his known value IN THE TEST with a comment citing the fact id you read it from; hardcoding in a test fixture is fine, in engine code it is not).
2. **Unit — sade-sati**: sade-sati signs derived from `moon_sign='Aquarius'` == ('Capricorn','Aquarius','Pisces'); derived from a different Moon sign ≠ that tuple.
3. **Unit — no-constant guard**: `grep`-style assertion (a test that reads the source files) that the strings `_NATIVE_JANMA_NAK_IDX`, `_NATIVE_LOCATION`, `_NATIVE_LOC` no longer exist in `services/ka_sangam/engine.py`, `pipeline/orchestrator/writers/ka_sangam.py`, `pipeline/orchestrator/writers/ka_vighnakara.py`. This is the cheapest permanent tripwire against reintroduction.
4. **Regression — Abhisek unchanged**: for a fixed synthetic predicate set + fixed time window, engine scoring with the resolved 482012f1 context equals scoring with the old constants (capture the old outputs as fixture BEFORE you delete the constants — first commit the fixture, then the fix).
5. **Regression — charts differ**: same synthetic predicate set scored under 482012f1's context vs 1c826d5a-41cb-4450-b4dc-59d440e5f75a's (Abhinandan) context produces **different** tara/sade-sati/panchanga current values wherever their natal inputs differ. "Abhinandan must score differently from Abhisek" — this is a 2-chart correctness guard, NOT population statistics (design §1 explicitly rules it in scope).

These tests must not require a live DB where avoidable — pass contexts directly to engine functions. DB-touching resolution helpers get one integration test if the existing suite has a DB harness; otherwise mock the cursor.

## 4. Acceptance criteria (all must hold)

- [ ] `grep -rn "_NATIVE_JANMA_NAK_IDX\|_NATIVE_LOCATION\|_NATIVE_LOC" platform/python-sidecar/` → **zero hits** outside tests/fixtures/comments describing history.
- [ ] `_SADE_SATI_SIGNS` module constant removed from `engine.py`; sade-sati signs derived from the chart's Moon sign at call time.
- [ ] Writers resolve janma-nakshatra index, Moon sign, and location per-chart from `chart_facts` / `birth_params`; no fallback to any specific native's values anywhere in the production path.
- [ ] All 5 tests of §3 pass; full sidecar suite (`pytest platform/python-sidecar`) has **zero new failures**.
- [ ] For 482012f1: resolved context == (idx 24, Aquarius, Cap/Aqu/Pis, 20.2961/85.8245/330) and engine outputs bit-identical to pre-fix fixture.
- [ ] `ka_kalasutra.py` untouched. Orchestrator core (`pipeline/orchestrator/` outside `writers/ka_sangam.py`, `writers/ka_vighnakara.py`) untouched.

## 5. Known traps (do not reintroduce)

- **CR-87 itself**: any default-parameter value of `24`, `'Aquarius'`, or Bhubaneswar coordinates in engine/writer code IS the bug in a new coat. Required parameters, no natal defaults.
- **B.10 (no fabricated computation)**: nakshatra/sign/location must be read from stored L1 facts or `birth_params` — never recomputed ad hoc in this lane and never guessed.
- **§N.2 frozen contract**: writers keep `run(ctx)` shape, use `ctx.db_conn`, never commit/rollback/close, never write `asset_throughput`. If your fix "needs" a contract change, STOP and report — it doesn't.
- **CR-40/CR-8 (sidecar auth)**: the ephemeris/transit sidecar may be down in your environment. Engine unit tests must not depend on live transit data — that infra fix is an explicitly separate INFRA-PREREQ, not this lane.

## 6. Anti-scope (explicitly NOT this lane)

- Do NOT touch the convergence formula, currents, weights, or `SUPPORTING_WEIGHTS` (CR-88/CR-89 → campaign phase D-3).
- Do NOT build the Three-Lock model, suppression currents, double-transit, or saham currents (D-3).
- Do NOT touch MSR (`bo_laksana.py`), `ga_structural`, `ga_yoga`, or any serving-plane TypeScript.
- Do NOT run chart rebuilds or deploy — the CONDUCTOR owns the rebuild protocol and merge sequence.
- Do NOT modify the frozen orchestrator (`pipeline/orchestrator/` core: `runner.py`, `writers/__init__.py`).

## 7. Done-definition / handback

Branch (worktree) with: engine + 2 writer fixes, 5 tests, pre-fix fixture, all green locally. Report: files changed, the resolved-context code path, test names, and confirmation of the §4 checklist. The verification swarm (see CONDUCTOR.md §4) re-runs the Abhisek-identical + Abhinandan-differs checks after the rebuild.
