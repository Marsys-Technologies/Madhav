---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_MUHURTA_SEVA
version: "1.0"
status: ISSUED
date: 2026-09-24
brief_under_review: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_MUHURTA_SEVA_ELEVATION_BRIEF_v1_0.md
reviewed_at_revision: "bf70a3477 (l3/kala-layer-briefs; brief's source_revision 9feac52d7 is an ancestor; `git diff --stat 9feac52d7 HEAD` on the four cited source files is empty)"
reviewer: "Fable 5.1 review agent, fresh context, read-only; no DB, no external service"
method: "every file:line re-read with sed/grep in this worktree; Lane C/D/E/F and the traceability matrix treated as claims, not proof"
---

# Review — `ka_muhurta_seva` elevation brief v1.0

## 1. Verdict

**REWORK.** The brief's consumer map and live-path statement are wrong at source: none of the three served surfaces nor the sealed L4 writer calls `services/ka_muhurta_seva/service.py` — `kala_elect_get`/`muhurta_finder.ts` run on the L4 `brahmagyan/phala/muhurta.py` + `panchanga_daily` path, `routers/muhurta_score.py` and `routers/muhurat.py` call `muhurat.finder` directly, `ph_muhurta.py` uses a proxy formula, and the only `.score()` call in production (`ka_sangam/engine.py:722`) raises on every invocation — so the typed verdict as scoped reaches no served answer, the compatibility anchor is fictional, the genuinely chart-bound default-location hazard lives in `panchanga_daily` (outside `may_touch`) rather than where the brief places it, and the `criterion` vocabulary contradicts blueprint Q7/§12.1 and the sibling Tulana brief.

## 2. Findings

| id | severity | brief's claim (section) | found at source | proposed correction |
|---|---|---|---|---|
| F1 | **BLOCKER** | §2.3 table + "Live-path statement. The service is live on three served surfaces and inside two L3 writers and one sealed L4 writer"; §1 Lane D row "consumers confirmed and widened here [V]" | `elect.ts:62,872` → `handleMuhurtaFinder` → `muhurta_finder.ts:32-34` → `L4_phala/query_muhurat.ts:124` `POST /api/compute/phala/muhurta_finder` → `brahmagyan/phala/muhurta.py:1894`, which imports **neither** `score_muhurat`/`find_muhurat` nor the service (grep: 0 hits) and derives `panchanga_quality` from `panchanga_daily` (`:1317`, `:1329-1330`). `routers/muhurta_score.py:48-50,123` imports `score_muhurat` from `panchang_engine.muhurat`, never `services.ka_muhurta_seva`. `routers/muhurat.py:20,139` calls `muhurat.finder.find_muhurat` directly. `ph_muhurta.py:134-136` `panchanga_score = round(min(1.0, condition*0.8+0.2),4)` with comment "ka_muhurta_seva not available at writer import time", `:160` `source:'ka_muhurta_seva_proxy'`. `ka_vighnakara.py:197-198` instantiates the service, `:613-620` calls `compute_panchang` directly, never `.score`. `ka_sangam.py:40,329` instantiates; `ka_sangam/engine.py:722` is the **only** `.score(` call in non-test code and always raises (`event='general'` ∉ `EVENTS_MVP`; documented `:700-712`). Writer self-test (`writer.py:220-221`) and health probe (`service_probes.py` check block `score_muhurat` direct) also bypass the service. Net: **zero live callers receive a value from `service.py`**. `ka_graha_sancara.py:91` is a comment, not an import. | Rewrite §2.3 with the actual call graph (three engines: `service.py` → `muhurat/finder.py`; `routers/*` → `muhurat/finder.py`; `elect`/`muhurta_finder` → `phala/muhurta.py` on `panchanga_daily`). State per Context §7: "no live value-receiving caller found within scope: `platform/python-sidecar`, `platform/src`, `platform-mcp/src`, tests excluded". Re-scope the delta: either the typed verdict targets `muhurat/finder.py` (outside `may_touch` — needs a fence decision) plus re-pointing `routers/muhurta_score.py`/`routers/muhurat.py` through the service, or the brief states (template §2.5) that nothing new reaches `kala_elect_get`. |
| F2 | MAJOR | §0/§3 "the served `muhurta_score` route then scores chart-less requests at a canonical default location … a general answer wearing a location it did not receive … can never pass as personal"; §4.3 "`elect.ts`/`call_muhurta_score` must pass the chart's location for chart-bound calls" | The route has no chart-bound mode: `MuhurtaScoreRequest` (`routers/muhurta_score.py:61-69`) = `datetime_utc, event_class, ayanamsha_id`; descriptor "Global scope — no chart_id" (`call_service_wrappers.ts:417`), inputs `datetime_utc, event_class, ayanamsha_id?` (`:463`), body `:502`. Default is real and live (`:499`) but declared global on both ends and in the response `note` (`:131-136`). The **chart-bound** served election (`kala_elect_get`) computes pañcāṅga at Bhubaneswar for every chart: `panchanga_daily` is a single-observer table (`scripts/panchanga_daily_writer.py:42-46,205`; migration `427:41-43`) read by `brahmagyan/phala/muhurta.py:1317`. That is the Product §10 / VA §4.4 hazard on a personal surface, and it is outside the brief's `may_touch`. | Keep the route finding but grade it honestly (declared-global, string-typed location — a typing gap, not a masquerade). Move the "personal-looking default location" finding to `panchanga_daily`/`phala/muhurta.py` and raise it as a cross-asset item (L0 reference table + L4 reader), not as this service's fix. State that `call_muhurta_score` has no location input, so "pass the chart's location" is a descriptor/route contract change and must be named as such. |
| F3 | MAJOR | §3 "`find_windows` returns ≤ 10 by that float with no record …"; §2.4 "the composite float … one scalar over three claims"; §4.2 greenfield `MuhurtaVerdict` | `find_muhurat` attaches `_score_breakdown` per window (`muhurat/finder.py:246-255`; `_score_breakdown` `:101-141`) with keys `tithi, nakshatra, vara, yoga, planet` and `tara_bala` **only when `native_chart` is supplied** (`:139-140`); `MuhuratWindow.breakdown` (`panchang_engine/types.py:280`); served by `routers/muhurat.py:44`; registered as `windows[].breakdown` in the W0 field register. "Three claims in one float" is true of `score()` (`:148-196`, `service.py:78-119`) and of the route (`:123-129`); it is not true of `find_windows`, where a per-factor decomposition with a detectable personal-overlay presence already exists. The brief's latent-value register (template §2.1) omits it. | Cite `breakdown` as class-(a) existing capital; define the typed verdict as an extension of it (alias `breakdown.tara_bala` → `personal`, declared mapping); adjust the §4.9 ablation — the `personal` flip is partly observable today as `'tara_bala' in breakdown`. |
| F4 | MAJOR | §4.5, §10.1 `criterion ∈ {nearest_clean, best_scored, robust}` | Blueprint §9 Q7 (`KALA_ELEVATION_BLUEPRINT_v1_0.md:671`) and §12.1 (`:748`) fix `criterion ∈ {nearest, strongest, robust}`; Tulana brief (`KA_TULANA_ELEVATION_BRIEF_v1_0.md:46-47,148-154`) uses the same. Same concept, different spelling — non-conformant under the binding's rule of adoption (`KALA_SYNERGY_BINDING_v1_0.md:19-22`). | Adopt `nearest / strongest / robust`. If "un-vetoed" is a qualifier, carry it as a separate boolean (`vetoed_excluded`), not a fourth name. |
| F5 | MAJOR | §5 "the float stays as `legacy_score` … readers: … `ph_muhurta.py` (sealed L4) — the L4 reader must not change"; §6 E "`ph_muhurta` is the compatibility anchor"; §2.3 row `ph_muhurta.py` reads "score" role `computation` | `ph_muhurta.py:134-136,160` — proxy, never a float from this service (migration `968:76` confirms). Also `ka_vighnakara.py` reads no float (tithi only, `:620-623`). `legacy_score` protects nobody. | Drop `ph_muhurta` and `ka_vighnakara` as float readers. Record separately (L4-owned) that the sealed writer's pañcāṅga term is a proxy that never consulted this service. Keep `legacy_score` only if a real reader is named (`routers/muhurat.py` `score` via the UI hook `useMuhuratFinder.ts:62-73`, and `routers/muhurta_score.py:129`). |
| F6 | MAJOR | §7 Negative row: "invariant: location never defaulted in the service; detector fails when a default location appears in a service call"; Context row: "chart-less route call → `location_used.source='canonical_default'` typed" | `service.py:44-60` already raises on `None`/missing keys — the Negative detector passes today and cannot distinguish old from new (a test that cannot fail). The route never enters the service, so a service-level detector cannot observe the route's default; a typed `location_used` on the route is a route/descriptor change. | Split: (i) service guard → PRESERVE regression test, not a proof of the delta; (ii) route → detector asserts the typed field on the HTTP body of `/api/compute/muhurta_score` **and** on `call_muhurta_score`'s `content`; name the descriptor change. |
| F7 | MAJOR | §7 Delivery row: sentinel `personal.completeness_state='unavailable'` "reaches `kala_elect_get`'s envelope … survives `elect.ts`" | `kala_elect_get` never calls this service (F1) — the sentinel has no path. `elect.ts` already carries a typed personal-overlay state from the phala path: `lane_f.tara_bala_status: 'applied' \| 'unavailable_no_janma_nakshatra'` (`muhurta_finder.ts:333`), `honestEmptyCoverage('tara_bala_personal_star_veto', …)` (`elect.ts:314-317`). Blueprint §12.2 (`:751-763`) has no interface packet for election. | Either write the re-pointing packet in L3-U04/U11 form (obligation + L3-owned sentinel test; guide §7) and add it to §12.2, or restate Delivery against a surface that does consume the service today. |
| F8 | MAJOR | §4.2 `undertaking: Component` — "`applied` for the event's declared constraints, `inapplicable` for constraints the event does not carry" | No per-event constraint set exists: an event selects a quality table and weights (`finder.py:163-166`; `muhurat_weights.yaml` `events:`); the only veto (`_in_inauspicious` `:58-76`) is event-independent. Nothing yields an `undertaking.value` or constraint list. | Mark `undertaking` `unexplored` with the source it needs (DP02), or redefine it as `weight_source` (per-event table + weights version), not a scored component. |
| F9 | MINOR | §2.2 "for chart-less requests uses …" | All the route's requests are chart-less (`routers/muhurta_score.py:61-69`). | Reword: "the route has no chart input; every call is scored at the default". |
| F10 | MINOR | §3 "receives `0.71`" | Service/engine scale is 0..100 (`service.py:101`; `finder.py:150,196`; route `:129`); 0..1 is the phala path (`muhurta_finder.ts:280`). Symptom of F1. | Use the 0..100 scale. |
| F11 | MINOR | §4.6 "`inclusivity='closed_open'`; no `date.today()` (the horizon is the caller's)" | Search horizon is inclusive both ends (`finder.py:216`, `:243 while current <= date_to`); window instants are `sunrise_utc→sunset_utc` (`:250-251`). The served facade defaults the horizon to `new Date()`+90d (`elect.ts:229-232`, Pūrṇa-owned). | Declare `closed_closed` for the horizon today (or state the change); `closed_open` only for window instants if intended; note the served default. |
| F12 | MINOR | §2.1 and §2.5 cite `estimated_seconds: null` | Guide §3 / §11: never cite it (F28). | Delete both mentions; "unmeasured; `KALA_COST_PROFILE_v1_0.md` pending". |
| F13 | MINOR | frontmatter `may_touch` "`platform/python-sidecar/tests/l3/test_ka_muhurta_seva*.py`" | No such file. Existing: `tests/test_ka_muhurta_seva.py`, `tests/l3/test_muhurta_score_sidecar_route.py`. | Correct the paths. |
| F14 | MINOR | §1 "W2 source `47131772b` — four service payload shapes frozen DB-free" [V-implied] | Commit exists ("fix(data-plane): identify L3 frontier writer results"); the "four payload shapes" content was not verifiable from this worktree's tree without reading that commit's diff. | Mark [A] or cite file:line inside the commit. |
| F15 | MINOR | §7 "Revision: YAML weights change → `weight_source` version changes" | `muhurat_weights.yaml:19` carries `Version: 1.0` in a comment only; no version field is loaded (config_loader not read — see §4). | Name a real version surface (hash of the loaded weights dict) or the detector cannot fire. |
| F16 | NOTE | §2.2 "the five CLAUDE.md §B anchors" | CLAUDE.md §B lists seven; writer asserts five (`writer.py:65-69`). | "five of the seven". |
| F17 | NOTE | §4.9 ablation "remove the personal component from the ranking" | Tāra weight is 0.10 of 1.00 (`muhurat_weights.yaml:41,48`); without `native_chart` the vivah maximum is 90/100 — confirms the "silently lower number" (§3) **and** bounds the ablation's power by construction. | State the expected effect size. |
| F18 | NOTE | not in brief | `routers/muhurat.py:34` `tz_offset_minutes: int = Field(330, …)` — a silent IST default on the engine-direct, chart-optional served path (UI hook passes it explicitly, `useMuhuratFinder.ts:71`). | Record in §11 or raise; outside `may_touch`. |
| F19 | NOTE | inherited | Seed `english_description` (`asset_registry_seed.ts:2267`) "Location mandatory — no silent Bhubaneswar default" and descriptor `call_service_wrappers.ts:415-416,489-490` "the same primitive ph_muhurta calls internally" are both false at source (F1, F2, F5). | One catalog-correction line. |
| F20 | NOTE | §7 structure | No "Evaluation-if-governed" row (contract §6 lists eleven); no F24 tier label per row. | Add the row (`not_applicable` with reason is acceptable) and tier labels. |

## 3. Citations verified

Format: citation → resolved? → what is actually there.

**Source (unchanged since 9feac52d7):**
- `services/ka_muhurta_seva/service.py:6` → yes, "never silently assumed".
- `:37-60` `_validate_location` → yes (`:37-60`).
- `:78-85` `score(...) -> float` → yes (`:78-85`); docstring `:86-105`; body `:107-119`.
- `:91-97` optional overlay "un-floor" quote → yes (`:93-96`).
- `:121-150` `find_windows(..., top_n=10)`, "length <= top_n" → yes (`:121-148` signature/doc, `:142`); body to `:169`.
- `:178-207` module-level delegates → yes (`:178-211`).
- `services/ka_muhurta_seva/writer.py:1-25` → yes; anchors `:65-69`; knockout check `:237-273`; `WriterResult(rows_inserted=0)` `:137-142`; note self-test calls `score_muhurat` directly (`:220-221`).
- `routers/muhurta_score.py:35-36` → yes (`:35-39`); `:54` → yes; `:73` → yes; `:131-134` → yes (`:131-136`). Additional: `:48-50` engine-direct imports; `:61-69` request model without location/chart; `:123` score call.
- `platform-mcp/src/tools/kala_views/elect.ts:166` → yes (comment `:165-170`); `:202-203` → yes (janma micro-rule comment); `:226` → yes (`empty_reason?`); `:288-290` → yes (thesis ternary `:286-290`); `:296-299` → yes (falsifier `:296-298`); `:310-335` → yes (`buildCoverage` `:302+`, entries `:310-335`). Additional: `:62,872` `handleMuhurtaFinder`; `:229-232` `defaultDateRange` uses `new Date()`; `:862-869` finder input carries no location.
- `platform/scripts/seed/asset_registry_seed.ts:2268-2276` → yes (`storage_type` `:2268` … `asset_kind` `:2276`); `:2274` `depends_on: ['ka_graha_sancara']` → yes. `asset_id` at `:2263`; description `:2267`.
- `muhurat/finder.py` (not cited by the brief, load-bearing): `:58-76`, `:101-141`, `:148-196`, `:203-261`, `:216`, `:243-255`.
- `panchang_engine/types.py:258-280` `NatalChart`, `MuhuratWindow.breakdown`.
- `panchang_engine/config/muhurat_weights.yaml:12-13,19,22-33,36-49` — sources named as MC/BS/MMP/DP abbreviations in comments; per-family verse citations partial (vivah "MC 3.5", griha_pravesh "MC 4.3", vyapara "MC 5.1", upaya "MC §Upāya; BPHS"); no machine-readable citation field.
- `routers/muhurat.py:20,32-36,44,50-102,113-168`.
- `brahmagyan/phala/muhurta.py:1894,1927,1941` routes; `:1084-1130`; `:1317,1329-1330`; grep for `score_muhurat|muhurat.finder|ka_muhurta_seva|find_muhurat` → 0 hits.
- `L4_phala/query_muhurat.ts:8,124`; `muhurta_finder.ts:32-34,280,333`.
- `call_service_wrappers.ts:405-417,460-469,483-513`.
- `pipeline/orchestrator/writers/ph_muhurta.py:9,134-136,160,565-570`; migration `968:76`.
- `pipeline/orchestrator/writers/ka_vighnakara.py:9,197-200,601-646`.
- `pipeline/orchestrator/writers/ka_sangam.py:40,329-331,654,845-863`; `services/ka_sangam/engine.py:700-735`.
- `pipeline/orchestrator/service_probes.py:975-1010` and check block (engine-direct `score_muhurat`).
- `scripts/panchanga_daily_writer.py:7-8,42-46,205`; `supabase/migrations/427:41-43`.
- `platform/migrations/676_…:1-42` → yes, `depends_on='{}'`, seed deliberately un-synced.
- `platform/src/app/panchang/hooks/useMuhuratFinder.ts:37-41,62-73`.

**Governance:**
- Register §5 `REGISTER:158` → yes, exact row.
- Strategy §6.1 L3-A03 (`:273`) → yes, verbatim. L3-Q10 (`:71`) → yes. §3 Comparison/election (`:97`) "no universal ranking or hidden hard cap" → yes.
- Product §3.11 (`:168-172`) → yes; §10 calendar family (`:365`) → yes; §5.2 (`:220-223`) — the "not substitutes" sentence is at `:223` → yes; P11 (`:79`).
- VA §4.4 (`:152-158`) → yes.
- W0 field register #14 (`:33`; rows `:640-644` + `windows[].breakdown`) → yes.
- Lane D §10 (`:532-566`) → yes, including "not independently re-confirmed beyond that comment" — the brief's "[V]" widening is what this review overturns.
- Lane E Q-K09/K10 (`:232-249`), table (`:348-349`), §5.8 (`:961-967`) → yes. (Lane E cites `REGISTER:156`; the brief's `:158` is the correct line.)
- Lane F P11 (`:157`), orphan U-id (`:164`) → yes.
- DAG reconciliation §2 (`:33`) → yes.
- Blueprint §3.3 (`:222`), §3.5 row 3 (`:319`), §4 (`:391`), §9 Q7 (`:671`), §12.1 (`:748`), §12.2 (`:751-763`, no election packet), §16.2 (`:901`), §17.2 (`:951`) → yes.
- Elevation plan Q7 (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:193`) → yes.
- Commit `47131772b` → exists; content not inspected.
- Tulana brief `criterion` vocabulary (`:46-47,148-154`) → `nearest/strongest/robust`.

## 4. What I could not verify

1. **Live registry state** (`depends_on`, `service_health`, `selftest_detail`, migration 676 applied) — no DB access. The brief's "live `{}`" is taken from migration text only.
2. **Live incidence** of the route default, of `> top_n` candidates, of search latency — no runtime; the brief also does not claim these (correctly).
3. **`config_loader.get_weights_for_event`** — not read; whether a version/hash surface exists for `weight_source` (F15) is unknown.
4. **Commit `47131772b` content** ("four service payload shapes frozen DB-free") — subject line only.
5. **`routers/nirmana_probe.py` body**, `service_manifest.json:658-683`, `producer_editorial_review.ts:371` — only the mapping/list lines were read; they reference the asset, roles not confirmed.
6. **Whether `panchanga_daily`'s single-observer location is disclosed on the `kala_elect_get` envelope** — `elect.ts` was not read end-to-end for a location field; grep found no `lat/lon/location` handling in it (`elect.ts` grep: only `chart_id`).
7. **KALA_DELEGATED_DECISIONS / NATIVE_RULING_SHEET** — grep for `Q7|criterion|muhurta` returned nothing; no prior ruling on the criterion vocabulary found there (the blueprint is the only fixing text).

## 5. Conformance to the binding (B1–B7)

**Conformant names used:** `completeness_state` (values `applied`, `unavailable`, `inapplicable` — within the six), `source_qualification` (`verse_cited / algorithmic_approximation / unsourced`), `epistemic_class`, `operator_role`, `comparable_with` (`self`, `different_convention`), `tier_basis='relative_uncalibrated'`, `claim_grain='date_grain'`, `t_start/t_end` (`timestamptz`), `inclusivity`, `coverage` (name).

**Non-conformant or missing:**
- `criterion` values — `nearest_clean / best_scored` vs the blueprint's `nearest / strongest` (F4). Not a B-row, but the same "one spelling" rule the brief adopts by reference.
- **B5 `coverage` shape** — the binding requires `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}` (`:69`). The brief omits `partitions_searched[]`, `exclusions[]`, `unsearched_regions[]` and adds `candidates_evaluated, vetoed, returned, top_n, truncated`. `vetoed` is `exclusions[]` under another name — alias with a declared mapping; add the three missing fields (empty arrays are honest).
- **"OFFERS … B2 (all)"** overclaims: `corpus_verifiable` and the R-6 four (`activity, valence, applicability, availability`) are not named anywhere in §4.
- **B4 `independence_group`** — absent, although the verdict carries scores; B4's downstream rule (`:63`) binds "any projection carrying a score".
- **B3 `window_ref` / `generation`** — absent; an elected window has no stable id (the served facade uses positional `c${i}`, `elect.ts:895`). A `sha256(event, date, location, weights_version)` per window would satisfy B3.
- **B1 `time_basis`** — not declared (window instants are sunrise/sunset → `event_instant`; the search itself is `date_grain_midpoint`-like). **B1 `resolver`** — not addressed; the engine iterates dates itself (`finder.py:243,257`) rather than importing `services/ka_temporal/date_resolver`.
- New names outside B1–B7 (permitted, but each needs a dossier row per Context §8): `location_used`, `legacy_score`, `weight_source`, `rule_ids`, `vetoes`, `Component.value`, `criterion`.
