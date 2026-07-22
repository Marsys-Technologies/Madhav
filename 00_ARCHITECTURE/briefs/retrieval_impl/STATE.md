---
artifact: STATE.md
canonical_id: RETRIEVAL_IMPL_STATE
version: rolling
status: LIVE
type: campaign ledger (Retrieval Plane Elevation implementation)
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md
---

# Retrieval Plane Elevation — Implementation Ledger

## Scope declaration (opened 2026-07-19, conductor session)

**may_touch:**
- `platform/**` and `platform-mcp/**` source (the implementation campaign)
- `platform/supabase/migrations/**` (surgical migrations only, §N.4)
- `00_ARCHITECTURE/RETRIEVAL_*.md`, `00_ARCHITECTURE/briefs/retrieval_impl/**` (NEW),
  `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`
- git branches/worktrees for this campaign (`impl/w<N>-<lane>` → `impl/wave-<N>` → `main`);
  merge to main; push; deploy per brief §E.6

**must_not_touch:**
- FROZEN orchestrator + WriterBase contract + all `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` writer
  build logic (§N.2)
- `CLAUDECODE_BRIEF.md` (root); doctrine-wave briefs/ledgers (read-only)
- `chart_facts` semantics / chart computation; LEL content
- Paripraśna UI/streaming/render — except the §D cross-cited seams (`consult/route.ts` floor
  adoption + `audience_tier` excision per C-2, not touched until R-3.2/W2)
- **`kala_*` serving semantics** — owned by the doctrine campaign while both are active (brief §I.5)

## Coexistence check (brief §I, at every wave open)

- **CURRENT_STATE §2 read at open (2026-07-19):** Doctrine-Waves campaign — D-4a CLOSED (GATE
  GREEN 7/7); **D-5 "Gochara-Chitra" is ALREADY PAST its serving lane (G-4 merged to main,
  commit `095a2bc1`; G-5 ledger-integration lane also merged, commit `f1d8e339`)**. This is
  further along than the brief's §I.2 assumption ("W2–W3 MUST NOT run concurrently with D-5's
  serving lane") anticipated — G-4 already closed before this campaign opened. No conflict for
  W0/W1 (harvest/census vs kernel — disjoint). **Flagged for the native at the §F gate:** since
  G-4 already merged, the brief's "W2/W3 land before D-5 serving opens, D-5 becomes the
  commissioning contract's first live test" path is foreclosed as originally imagined — W2 will
  need to retroactively commission the already-live gochara tools rather than land ahead of them.
  This is the §I.2 fallback case ("if native sequences D-5 first... W2 absorbs the gochara tools
  in its migration"). No action this wave; recorded for the native's W2-sequencing ruling.
- **Deploy mutex:** this ledger claims the mutex for the W0 S-1..S-5 safety deploy (see §Deploy
  Mutex Log below). No doctrine-campaign deploy is in flight as of this entry (last doctrine
  merge to main: `f1d8e339`, no open PR at this ledger's open per `gh pr list` — see verifier log).
- **Baseline re-snapshot rule:** if the doctrine campaign deploys again before this campaign's
  next probe diff, the W0 baseline is re-snapshotted before diffing (§B.2).

## Deploy Mutex Log

| When | Campaign | Action | Released |
|---|---|---|---|
| 2026-07-19 19:12–19:34 | retrieval | W0 S-1..S-5 safety deploy (PR #633 → main `2f4b67e8` → amjis-mcp `amjis-mcp-00440-n29` + amjis-web `amjis-web-01031-rmj`, 100% traffic) | **RELEASED** 2026-07-19 19:5x, post live-verification |
| 2026-07-20 (claimed pre-merge) | retrieval | W2 phase 1 deploy: descriptor migration + vidhi de-mirror + 6 dark-set items, incl. two NEW live sidecar routes (ephemeris compute, muhurta score) — requires python-sidecar + platform-mcp redeploy, not just platform/web. Pre-deploy check: D-5 is HALTED (§ D-5 STATUS REFRESH above); most recent `origin/main` activity is D-5's `gate_run_2` (docs-only push, `Build & Deploy Web/MCP/Sidecar` all skipped — confirmed no live D-5 code deploy in flight). Baseline re-snapshot: this campaign's last live probe was W0's `VERIFY_W0.md` (2026-07-19); a fresh post-deploy live probe of the two new sidecar routes substitutes for a full baseline re-snapshot here, since W1/W2 phase 1 added no regression-risk to the surfaces W0 already verified. | **RELEASED** 2026-07-20, post live-verification |
| 2026-07-20 (claimed pre-merge) | retrieval | W3 deploy: PR #661 (`impl/wave-3` → `main`), full envelope/flags/register/cursor/budget/density/demand/cache surface. Pre-deploy check: D-5's RED-C (#650) and RED-D (#651) fixes both merged, no D-5 PR open (mutex reads clear); **native explicit confirmation received** (2026-07-20) that D-5 is quiet enough for a non-breaking deploy — the stale `worktree-wave+D-5+conductor` branch ruled not a blocker. Native rulings on the two flagged kala-adjacent touches: `kala_temporal.ts`'s budget wrapper stays (plane infrastructure, revert-on-objection — filed as a §I.5 note in `STATE_D-5.md`, PR #662); `L3_kala/query_projections`'s conservative density_contract stance approved, measured override deferred until the kala freeze lifts. Baseline re-snapshot: live-probed `get_cgm_subgraph(mode=convergence)` and `judgment_query(domain=wealth, response_format=v3)` against chart 482012f1 immediately before this deploy (the "before" half of the native's requested before/after diff) — see `VERIFY_W3.md` §2 for the full capture. Alias cutover + bootstrap flag-flip remain parked (unchanged ruling, does not follow from this go-ahead). | **RELEASED** 2026-07-20, post live-verification (see `VERIFY_W3.md`) |

### W2 PHASE 1 CLOSE (2026-07-20)

Merged: PR #645 (`impl/wave-2` → `main`, merge commit `d2cc080c`), all CI checks green. Deploy
(run `29720602529`): `Build & Deploy Sidecar` success, `Build & Deploy MCP` success,
`Build & Deploy Web` success — all three services redeployed as required. Live-verified
directly against the deployed `amjis-sidecar` Cloud Run service (bypassing the MCP tool-name
layer, which does not expose `call_ephemeris_at_t`/`call_muhurta_score` under those literal
names on this connector — same pattern already noted in `VERIFY_W0.md` for
`ephemeris_cache_native_lifetime`):
- `POST /api/compute/ephemeris_at_t` → real computed positions for all 9 bodies at
  2026-07-20T12:00:00Z; Rahu/Ketu exactly 180° apart (307.324°/127.324°), a live-compute
  invariant a stub or hardcoded response could not satisfy.
- `POST /api/compute/muhurta_score` → real score (64.0/3-star) + panchang context (Shukla
  Saptami, Hasta, Somavara, Shiva) for the same instant, `vivah` event class.

**W2 phase 1: CLOSED.** Descriptor migration (120/120 universal fields), vidhi codegen
de-mirror, and 6 dark-set items are live in production. Remaining W2 scope (projection
compiler, single bootstrap, alias cutover [breaking — stays deferred pending D-5 quiet], the
other 36 SERVE-gap items, G-1/S-3/SC-2..5 structural closes) is future work within this wave.

## Wave log

### W0 — Foundations

- **W0.1 (2026-07-19):** merged `ret/strategy-s1` → `impl/wave-0` (docs-only, 41 files,
  +10,884/−32 vs merge-base `b536e13b`). 5 merge conflicts, all in append-only rolling ledgers
  where `main` had advanced further (D-4a/D-5 banners not yet on `ret/strategy-s1`'s stale base)
  — resolved `--ours` (main) in all 5 cases; `theirs` side added nothing `main` didn't already
  carry in every case inspected. `ret/strategy-s1` scheduled for deletion after this wave's push
  to `main`. Landed `GROUND_TRUTH_REGISTER.md` (the doc the master brief cites at
  `briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md` — confirmed it exists on this branch; my
  earlier pre-merge search of `main` alone had reported it missing, which was correct-for-`main`
  but resolved by this merge).
- **W0.2:** rulings recorded — see `RULINGS_ADOPTED.md`.
- **W0.3:** safety items S-1..S-5 — see per-item log below.
- **W0.4:** baseline probe suite — see `BASELINE_PROBES.md`.
- **W0.5 (2026-07-19):** read-only DSN provisioned (W-18). Role `retrieval_census_ro` created
  on `madhav-astrology:asia-south1:amjis-postgres` (Cloud SQL instance `amjis-postgres`, DB
  `amjis`) via `amjis_app`'s existing `CREATEROLE` grant — no superuser credential was touched
  or reset. Grants: `CONNECT` on `amjis`, `USAGE` on schema `public`, `SELECT` on all tables in
  `public` + `ALTER DEFAULT PRIVILEGES ... GRANT SELECT` so future tables inherit read access
  automatically. Confirmed non-superuser / non-createrole / non-createdb, connection limit 5.
  Live-verified: `SELECT count(*) FROM chart_facts` → 276,206 (succeeds); `INSERT` →
  `permission denied for table chart_facts` (correctly fails). Credential stored as Secret
  Manager secret `retrieval-census-ro-db-password` (project `madhav-astrology`) — never written
  to any file in this repo or committed. Connection: Cloud SQL Auth Proxy →
  `madhav-astrology:asia-south1:amjis-postgres`, user `retrieval_census_ro`, db `amjis`,
  password from the secret above. This satisfies W-18's precondition for the W1 harvest/census
  lanes (E1/E3 DB truth).
- **W0.6:** envelope codegen parity test wired into CI — see below.

### V0 fix-cycle log

**Cycle 1 (2026-07-19) — REJECT-WITH-FINDINGS** (independent opus verifier, Workflow
`wf_309e240b-ad2`). S-3, S-4, CI-wiring (GT-9): clean, all tests pass, ACCEPT-quality.
S-2: mostly solid (20 routes migrated to shared `service_token.ts` guard) but incomplete —
missed a live fail-open bypass of the identical vulnerability class in
`brahma/sutravali/by_house/[house_num]/route.ts` and `by_planet/[planet]/route.ts`
(`if (INTERNAL_TOKEN && token !== INTERNAL_TOKEN)` short-circuits open when the secret is
unset), plus 5 more unmigrated (but currently fail-closed) duplicate guards. **S-1/S-5:
REJECTED** — the new chart-agnostic-gate Rule 9 (cardinality-literal detector) false-positives
on legitimate non-native row-count documentation (get_divisionals 21,635 etc.), breaking 10
existing tests including the registry-wide "Gate passes GREEN" master invariant; the lane's own
regression test (T14) was left asserting the removed exemption and fails; the native PII this
item was supposed to remove is still served in the resource's actual runtime payload (fallback
branches of `ephemeris_cache_native_lifetime.ts`'s loader), not just its static description;
and the new `checkTextForNativeLeak` scanner is dead code never wired into its own cited
motivating example (d8's `TEMPORAL_EMPTY_REASON`). Full findings: verifier transcript,
Workflow run `wf_309e240b-ad2`, journal.jsonl. **Disposition:** respawning a fix cycle for
S-1/S-5 rework + S-2 completion (the two sutravali routes + 5 remaining files); S-3/S-4/CI-wiring
retained as-is (independently ACCEPT-quality, no rework needed).

**Cycle 2 (2026-07-19) — REJECT-WITH-FINDINGS (narrower).** Fix cycle 1 addressed all cycle-1
findings but the runtime-PII fix (ephemeris_cache_native_lifetime.ts loader() fallback payloads)
had already been started opportunistically; a follow-up verifier pass found 2 residual items:
(a) the S-1 Rule-9 description rewrite for `query_contradictions.ts` broke
`d5_l2_capabilities.test.ts` (a pre-existing test asserting `.toContain('0 rows')` had been
passing only via an accidental substring inside the now-removed "1,034–1,100 rows" literal) —
a genuine regression caused by this wave, not pre-existing as cycle-1's verifier had assumed;
(b) `checkTextForNativeLeak` was claimed wired into d8's `TEMPORAL_EMPTY_REASON` but was in fact
never called against the real constant (dead code, synthetic-only test coverage).

**Cycle 3 (2026-07-19) — ACCEPT.** Both cycle-2 findings fixed precisely: `query_contradictions.ts`
now carries an honest graceful-empty/0-row sentence (no cardinality literal reintroduced,
satisfies the test's real intent, not an accidental match — confirmed "0 rows" has no
thousands-separator so it doesn't trip Rule 9 either); `TEMPORAL_EMPTY_REASON` hoisted to module
scope + exported from `register_d8_assess_domain.ts`, a real test now imports the actual
constant and calls the actual `checkTextForNativeLeak`, asserting zero violations. Final
independent verifier (opus, full re-run of all 3 cycles' findings plus a full collateral-damage
sweep — `platform` full suite 497 files / 5856 passed / 0 failed, registry suite 596/0 failed,
`platform-mcp` S-3 suites 68/0 failed, both `tsc --noEmit` clean): **ACCEPT.** 3 non-blocking
notes recorded (Rule 9 only scans top-level `cap.description` not nested `input_schema` field
descriptions — pre-existing scanner scope, not a regression; this typo now fixed; S-4's parity
gate deliberately does not hard-gate the separately-tracked 47-vs-118 MCP_TOOL_TO_URI drift
backlog).

**V0 VERDICT: ACCEPT.** S-1..S-5 + CI wiring (GT-9/GT-36) ready to commit, merge to main, deploy.

### W0 CLOSE (2026-07-19)

Merged: PR #633 (`impl/wave-0` → `main`, merge commit `2f4b67e8`), all CI checks green. Deployed:
`amjis-mcp-00440-n29` + `amjis-web-01031-rmj`, both confirmed 100% traffic, no rollback. Remote
branch `impl/wave-0` deleted post-merge. `ret/strategy-s1` remote ref was already absent
(pre-merge cleanup by another process); a pre-existing local worktree at
`/Users/Dev/Vibe-Coding/Apps/madhav-retrieval` still holds a `ret/strategy-s1` local branch ref —
not created by this session, left untouched (not this campaign's to unilaterally remove).

Live-verified post-deploy (`VERIFY_W0.md`): S-1 clean; S-3 initially flagged, investigated,
confirmed clean (probe-premise artifact — session principal is `super_admin`, a pre-existing
out-of-scope break-glass path, not an S-3 defect); S-5 clean; no regression on 3 untouched
control surfaces. **V0 gate: CLOSED — W0 done.**

**Residual for campaign final handoff (master brief §H.6):** `authorizeChartAccess.ts` Rule 1
grants `super_admin` access to any chart_id without checking existence in `charts` first
(pre-existing, not introduced by this campaign, orthogonal to S-3's scope) — noted for the
native, not actioned here.

### W1 — Lane L1c (service manifests + probes, plan W-22 service half)

**Scope note:** the plan sections cited in this lane's brief (`RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`
§9.6 "Concept Spine" + §9.4 W-22/W-24/W-25 rows) **do not exist in this worktree's copy of the
plan** — the file tops out at §8.5 (811 lines, v1.3 frontmatter, confirmed via `grep -n '^##'`).
GT-50/`ka_graha_sancara` context was instead sourced from `GROUND_TRUTH_REGISTER.md` GT-50 and
`AUDIT_FINAL_REPORT.md` (both under `00_ARCHITECTURE/briefs/retrieval_audit/`), which cite the
exact same file/line ground truth the lane brief pointed at. Flagged for the conductor — either
a later plan version with §9 exists elsewhere and didn't make it into this worktree, or the
lane brief was written against a draft that got trimmed; not blocking, since the lane's actual
deliverable (steps 1–5) is self-contained.

**Real router count vs. plan's ~12 estimate:** found **20 mounted routers / 49 endpoints** (+
`/health` = 50) in the single deployed Python sidecar (`amjis-sidecar`, `platform/python-sidecar/
main.py`) — verified exhaustively via `grep -rn include_router` (zero call sites outside
`main.py`) and cross-checked against a live `GET /openapi.json` snapshot fetched from the
deployed service on 2026-07-20 (200 OK, unauthenticated — `/openapi.json` and `/health` are not
behind the `verify_api_key` dependency, only the included routers are). The two counts (hand
enumeration vs. live snapshot) match exactly, zero missing/extra (see `service_manifest.json`
`validation` block). The plan's "~12" undercounts by roughly 8 routers/40%+ real count is higher.

**Deliverables (new dir `platform/src/lib/retrieval/registry/service_manifest/`):**
- `service_manifest.json` — one entry per router: module, mount prefix, `provides_apis`
  (path+method), `health_probe`, `concurrency_cap` (see honesty note below).
- `openapi_snapshot.json` — the real, live-fetched OpenAPI document (71KB, 50 paths) — the
  mechanical-extraction ground truth the router list is checked against.
- `index.ts` — typed TS accessor over the JSON (`resolveJsonModule` already enabled in
  `tsconfig.json`).
- `__tests__/service_manifest.test.ts` — 5 tests: manifest-vs-snapshot parity, router/endpoint
  counts, dark-set absence-from-snapshot check. All pass (`npx vitest run` — 5/5 green).
- `DESIGN_KA_GRAHA_SANCARA_WIRING.md` — the required GT-50 design note (proposal only, nothing
  wired): identifies `POST /ephemeris` (`routers/ephemeris.py`, swisseph-backed, arbitrary
  datetime already) as the closest existing compute primitive, and `GET /brahmagyan/ephemeris/
  planet_position` (DB-backed, `ephemeris_daily`, date-only-not-datetime-precision) as a
  near-miss that can't satisfy the declared `datetime_utc` contract without a precision
  downgrade. Stub cited exactly: `call_service_wrappers.ts` lines 196–214 (handler),
  error string at line 208.

**Honesty notes (what's real vs hand-authored):**
- Router/endpoint enumeration: **mechanically cross-checked**, not hand-typed (grep of each
  router file's own `@router.get/post` decorators, independently verified against the live
  `/openapi.json` snapshot — see `extraction_method` field in the JSON).
- `health_probe`: the app-level `GET /health` is **live-verified** (curl'd, 200 `{"status":"ok"}`).
  Per-router health probes are **hand-authored v1** — no dedicated per-router health endpoint
  exists in the codebase except `/api/brahmagyan/almanac/health`, so every other router's
  `health_probe` field just points back at the shared app-level `/health` (honest, not padded).
- `concurrency_cap`: **no real per-router concurrency isolation exists** in the running system —
  all 20 routers share one Cloud Run service/process. Verified from `.github/workflows/
  deploy.yml`'s `deploy-sidecar` job: no `--concurrency` flag is passed, so Cloud Run's platform
  default (80/instance) applies undifferentiated across everything; `--cpu=2 --memory=1Gi
  --min-instances=0`, no `--max-instances`. Per-router `cost_class` (cheap/medium/expensive) is a
  **hand-authored qualitative judgment** from reading each handler's compute profile — explicitly
  labeled as not measured and not enforced (per brief's "don't fabricate a precise number"
  instruction). Actually adding per-route concurrency isolation is out of scope here.
- Two **new findings beyond the GT-50 ask**, both documented in `service_manifest.json`'s
  `dark_set`/`orphaned_artifacts` and NOT actioned (out of lane scope): (1) `ka_muhurta_seva`
  (`call_muhurta_score`) is a second dark L3 service in the same file, same stub shape, not named
  in GT-50; (2) `platform/python-sidecar/pyhora.Dockerfile` builds an image whose CMD
  (`pyjhora_adapter.main:app`) references a `main.py` that has never existed in this repo's git
  history and is not referenced by `deploy.yml` — it is dead/orphaned build infra, not a second
  live service (the real PyHora path is in-process via `routers/pyhora.py` inside the one
  `amjis-sidecar` deployment). Several `l4_*`-prefixed phala/mimamsa/bodha router files are also
  defined but never `include_router()`'d — dead route code, flagged not fixed.
- Not done (explicitly out of L1c scope): no wiring of `ka_graha_sancara` or `ka_muhurta_seva`
  (design-only, per brief); no re-audit of the ~30 scattered TS call sites elsewhere in the
  codebase that also call `PYTHON_SIDECAR_URL` directly outside `call_service_wrappers.ts`
  (e.g. `query_planet_position.ts`, `pyhora_natal_positions.ts`) — this lane's unit of manifest
  entry is the sidecar router, not every calling site; a future census lane could add a reverse
  caller-map if wanted.

**Verification run this lane:** `npx tsc --noEmit -p .` clean; `npx eslint` on the 2 new `.ts`
files clean; `npx vitest run src/lib/retrieval/registry` — 601 passed / 125 skipped (pre-existing
skips), 0 failed, including the new 5-test file and the full existing `L3_kala` suite (unchanged,
confirms `call_service_wrappers.ts` itself was not touched this lane).

### W1 — Lane L1a (concept-ledger infrastructure + descriptor extension design, plan W-24 + R-1.1)

**Same scope-note as L1c:** this worktree's copy of `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` is
v1.3 (811 lines, tops out at §8.5 — no §9, no §9.6 "Concept Spine" prose section, no W-24/W-25/
W-22 rows). Confirmed independently (`grep -n '^## §9'` returns nothing on this worktree's copy).
The doctrine + exact W-24/W-25/W-22 row text was instead sourced from the v1.8 copy at
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (the
main checkout outside this worktree, read-only — not written to) — same v1.7/v1.8 changelog
entries L1c's brief cited, confirming both lanes' briefs were written against a plan version
that never made it into this worktree. Flagged for the conductor, same as L1c: pull the newer
plan version into this worktree (or `00_ARCHITECTURE/`) so future lanes don't need this workaround.

**Deliverables, all four brief items landed as scoped (v1/initial, not the full W2 migration):**

1. **Concept ledger — REAL, applies cleanly.** `platform/supabase/migrations/461_concept_ledger.sql`
   (461 = next free number across both migration dirs combined, confirmed via `_migrations_applied`
   on the live read-only DB connection — no 456–460 collision). Applied + re-applied (idempotency
   confirmed) against a disposable local PostgreSQL 15 cluster (Homebrew binary, no Docker
   available) — NOT against the live `amjis` DB (out of this lane's authority; the conductor
   applies). `concept_kind`/`source_layer`/`lifecycle_state` CHECK-constrained per the brief's
   exact enums. `owning_asset_id`/`serving_capability_uri` deliberately NOT FK'd (rationale in the
   migration header — service_endpoint concepts don't map 1:1 to `asset_registry` rows; the TS
   registry isn't in the DB at all). TS access layer:
   `platform/src/lib/retrieval/concept_ledger/ledger.ts` — `insertConcept`, `upsertConcept`
   (ON CONFLICT), `upsertConcepts` (bulk convenience), `getConcept`, `listConcepts` (filtered),
   `getLifecycleLayerCounts`, `countConcepts`. All 6 read/write functions live-tested against the
   disposable local DB (insert, upsert-overwrite, filtered list, count) — not just typechecked.
2. **Projection generator — REAL, runs end to end at zero rows AND at N rows.** `platform/
   scripts/manifest/generate_concept_projections.ts` → `platform/src/generated/concept_census.json`.
   Live-run against the disposable DB with `concept_ledger` empty (proves the empty-table
   no-error requirement) and again after inserting 2 test rows via `ledger.ts` (proves the
   aggregation is correct, not just non-crashing), then truncated back to empty and re-run so the
   committed artifact reflects the real (empty) state of a freshly-migrated `concept_ledger`.
   Requires `--conditions=react-server` (the `server-only` import in `lib/db/client.ts` throws
   under plain Node without it — same flag the existing `tap:*`/`sla:*` scripts already use;
   documented in the script's usage comment).
3. **Hardcoded-list lint — REAL, catches a genuine hit.** `platform/scripts/lint/
   no_hardcoded_concept_lists.ts`. Regex/heuristic v1 (not AST), scoped to
   `src/lib/retrieval/registry/**`. Run for real: 9 candidates, split 5 HIGH-confidence (name
   matches `CATEGOR|CONCEPT|SIGNAL_TYPE|_CLASS`) + 4 MEDIUM. The flagship HIGH catch is exactly
   the plan's own cited example — `CHART_FACTS_CATEGORIES` in `coverage_matrix.ts`, 158 hand-typed
   fact_category strings (the same array the plan's W-16/W-20/W-23 findings independently name as
   one of three inconsistent hand-maintained enumerations). Also caught `PANCHANGA_CATEGORIES`
   (33), `SP_CATEGORIES` (20), `SS_CATEGORIES` (15), `STRENGTH_CATEGORIES` (21). The 4 MEDIUM hits
   (`COMPACT_FIELDS`, `MSR_SIGNAL_COLUMNS`, `DEFAULT_SERVE_COLUMNS`, `SURGICAL_TOOLS`) are the same
   shape (many snake_case string literals) but are column-name/tool-id lists, not concept-category
   duplicates — correctly triaged to lower confidence rather than filtered out (honest report, not
   narrowed to hide false positives). Report-only in v1 (exit 0 always) — not yet a CI hard gate.
4. **Descriptor extension — TYPE-ONLY, confirmed non-breaking.** Nine new optional fields on
   `CapabilityDescriptorBase` in `platform/src/lib/retrieval/registry/types.ts`: `display`,
   `annotations`, `register`, `mutation`, `projection_tags`, `family_overrides` (+ new
   `FamilyOverrideSpec` interface), `data_source`, `demand_ranking`, `calibration_context_only` —
   each doc-commented with its exact plan-section citation. D1 amendment protocol followed:
   `amendment_version` bumped 1→2, first real `D1_AMENDMENTS` log entry added (array was empty
   before this). **Zero of the ~118 existing capability descriptors were touched** — populating
   these fields is explicitly W2's job, not this wave's, per the brief. One real bug caught and
   fixed during this work: a doc-comment literally containing `bodha_*/kala_*` (asterisk
   immediately before slash) prematurely closed its own `/** */` block comment, corrupting ~40
   lines of the file into a TS1131/TS1005 syntax-error cascade — fixed by using commas instead of
   slashes as the separator in that one sentence.

**Verification run this lane:**
- `npx tsc --noEmit --skipLibCheck` (platform, CI's exact invocation) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp, CI's exact invocation) — clean, 0 errors (confirms the mirror/
  shim path that consumes `CapabilityDescriptor` isn't broken by the additive fields).
- `npx eslint` on all 4 touched/created `.ts` files — clean, 0 issues.
- `npx vitest run src/lib/retrieval/registry` (platform) — 601 passed / 125 skipped (pre-existing
  skips), 0 failed.
- `npx vitest run` full platform suite — 5861 passed / 317 skipped / 1 todo, 0 failed (498 test
  files). No regression from the FROZEN-contract type addition anywhere in the estate.
- Migration 461 applied + re-applied against a disposable local Postgres 15 — clean both times
  (`IF NOT EXISTS` idempotency confirmed empirically, not just asserted). NOT applied against the
  live DB (conductor's call, per this lane's scope).

**Not done / explicitly out of this wave's scope (stated up front, not discovered late):**
concept_ledger stays EMPTY after this migration — population is W-25's harvest pipeline (a later
wave); no backfill or seed rows were added here. The hardcoded-list lint is report-only, not CI-
wired as a hard gate. None of the ~118 existing capability descriptors were migrated to populate
the 9 new R-1.1 fields — that's W2. `family_overrides` was added as a NEW field alongside the
pre-existing `behavioral_overrides` field rather than replacing it — the plan's "subsumes" is
worded as an eventual consolidation, not a same-wave rename, and rewriting/removing the existing
field would be a breaking (non-additive) FROZEN-contract change out of a type-only wave's scope.

### W1 — Lane L1b (harvest pipeline + adjudication queue, plan W-25, E1-E4 extractors)

**Precondition check (per this lane's brief):** grepped for `platform/src/lib/retrieval/concept_ledger/`
and a `concept_ledger` migration before starting — both ALREADY LANDED by lane L1a
(`platform/supabase/migrations/461_concept_ledger.sql`, `ledger.ts`), which ran concurrently in
this worktree ahead of this lane picking it up. `concept_ledger` is NOT applied to the live DB
(confirmed live: `information_schema.tables` returns zero `concept_%` rows) — only
`retrieval_census_ro` (SELECT-only) is available against the live DB regardless, so a live write
was never possible this lane either way. Built the write path against L1a's own disposable-local-
Postgres pattern instead (see below) — proves the harvest→ledger path end to end without needing
live write access.

**Deliverables, all real (new dir `platform/scripts/harvest/`):**

1. **E1 — registry-declared extractor** (`e1_registry_extractor.ts`). Live `getCatalog()` load
   (same import chain both MCP and chat channels use) — **118 live capabilities**, confirmed
   matching the brief's "~118+" figure exactly. Per capability: uri/layer/name/scope/archetype +
   a best-effort static `table_hint` (which real table(s) its own descriptor's SQL touches),
   reusing WP-1.6's proven FROM/JOIN regex method but TIGHTENED to scan only backtick-delimited
   template-literal spans (the raw regex, applied to this lane's heavier-prose source files,
   produced 40 false "drift" hits — all English stopwords from sentences like "resolves data
   from X handler" — before this fix; zero after). Output: `e1_declared.json`.
2. **E2 — DB-truth extractor** (`e2_db_truth_extractor.ts`). Live query via `retrieval_census_ro`
   (Cloud SQL Auth Proxy, W0.5's provisioned role) — **247 base tables** in `public`
   (254 `information_schema.tables` rows minus 7 views). Exact `COUNT(*)` for 235 tables under a
   20K-reltuples threshold, `pg_class.reltuples` estimate for the 12 large ones (chart_facts among
   them); `count_method` recorded per row, never presented as one undifferentiated number. Output:
   `e2_db_truth.json`.
3. **E3 — fact_category reconciliation** (`e3_fact_category_extractor.ts`). Read all 3 static
   sources the plan cites PLUS a 4th found on disk the plan doesn't cite, plus live DB:
   **CHART_FACTS_SCHEMA.json = 147** (00_ARCHITECTURE canonical copy, byte-identical to the
   `platform/scripts/governance` mirror) · **a THIRD, undocumented copy at
   `platform/python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json` = 191** (not cited by the plan's
   3-way framing at all) · **coverage_matrix.ts CHART_FACTS_CATEGORIES = 158** ·
   **live DB DISTINCT fact_category = 218** · the "37" prose citations are 10 hits, all
   2026-04/05-era historical (KARN W2-R2 chart_facts ETL), not a live disagreement. The live DB
   disagrees with every static source — 66 live categories absent from coverage_matrix.ts's own
   enum (real serving impact: `chart_facts_query`'s category filter cannot reach them by name).
   Output: `e3_fact_category_reconciliation.json`.
4. **E4 — signal-class extractor** (`e4_signal_class_extractor.ts`). Live column scan across
   `bodha_*`/`kala_*`/`phala_*` (114 name-matching columns, 77 candidate enum-shaped after
   excluding id/array/jsonb/count-shaped columns) + DISTINCT value sampling per column. Real,
   counter-to-the-plan finding: `bodha_msr_signals.signal_type_class` (19 distinct values,
   73K+ rows in its densest class) IS a real, populated, de facto signal-class column — but it is
   NOT shared/centralized: excluding the trivial `snapshot_type='static_natal'` build-metadata
   field every bodha_* writer sets, only 15 pairs of differently-named `*_class`/`*_type` columns
   have ANY overlapping value at all (mostly coincidental). "No UNIFIED cross-plane signal-class
   registry" is the accurate, narrower version of the plan's flat claim. Output:
   `e4_signal_classes.json`.
5. **Cross-diff + adjudication queue** (`cross_diff_adjudication.ts`). E1 vs E2 vs E3, real and
   mechanical, not hand-curated: **77 DARK** (real L0-L5 table, zero capabilities' table_hint
   references it — 25 auto-proposed `INTERNAL-BY-DESIGN` via transparent naming-pattern rules,
   52 honestly `NEEDS-OWNER`), **0 DRIFT** (a genuine positive result post the backtick-scan fix —
   every declared table_hint resolves to a real table), **3 FACT_CATEGORY_GAP** summary rows
   (144/66/6-category gaps folded in from E3, full lists in the JSON). Output:
   `platform/src/generated/harvest/adjudication_queue.json` (full) +
   `00_ARCHITECTURE/briefs/retrieval_impl/ADJUDICATION_QUEUE.md` (human-reviewable, one row per
   DARK/DRIFT + summarized FACT_CATEGORY_GAP rows, explicit caveat that the TS-registry static
   scan cannot see `platform/python-sidecar` (Python) table access at all — a DARK row means "no
   TS-registry route found", not "provably unreachable by any means").
6. **Harvest → concept_ledger write path** (`load_harvest_to_ledger.ts`). Transforms E1/E3/E4
   output into `ConceptLedgerWriteInput` rows (355 total: 218 `fact_category` [152 SERVED / 66
   DARK, using coverage_matrix.ts membership as the SERVED/DARK signal], 19 `signal_class` [the
   confirmed `bodha_msr_signals.signal_type_class` values], 118 `service_endpoint` [one per live
   capability URI]) and calls L1a's `upsertConcepts`. **Live-tested end to end against a
   disposable local Postgres 15** (same pattern L1a used for migration 461 itself): migration 461
   applied clean, loader ran writing 355/355, re-run confirmed idempotent (355→355, no growth),
   `getLifecycleLayerCounts()` aggregate verified correct via a direct `psql` cross-check. **NOT
   run against the live DB** — blocked by the same two facts noted above (read-only credential;
   migration 461 not yet live) — this is the conductor's call, identical to L1a's own migration.
   DARK tables from the cross-diff are NOT loaded as ledger rows in this pass — they don't map
   cleanly onto the `fact_category`/`signal_class`/`service_endpoint` concept_kind enum (a whole
   table isn't itself one of those three kinds) — noted as an honest scope boundary, not hidden.

**Same plan-file anomaly as L1c/L1a:** this worktree's `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`
is v1.3/811 lines, no §9/§9.6/W-24/W-25/W-22 rows — confirmed independently again. Context for
this lane was sourced from the lane brief text itself (which quotes the doctrine directly) plus
`GROUND_TRUTH_REGISTER.md` and the sibling lanes' STATE.md entries above.

**Verification run this lane:**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors.
- `npx eslint scripts/harvest/*.ts` — clean, 0 issues.
- `npx vitest run src/lib/retrieval/registry` — 601 passed / 125 skipped, 0 failed (unchanged from
  L1a/L1c's baseline — this lane added no test files and touched no existing registry source).
- All 4 extractors + cross-diff + loader re-run end-to-end for this log entry (not just once
  during development) — clean, consistent numbers across the full chain.

**Not done / explicitly out of this wave's scope:**
No CI wiring for any of the 5 scripts (report-only v1, matching L1a's hardcoded-list lint
precedent). `table_hint` is a regex heuristic, not a real SQL parse — explicitly caveated
per-row in the adjudication queue, not presented as ground truth. DARK table dispositions beyond
the two transparent naming-pattern rules (bookkeeping suffix, bg_* reference keyword) are
`NEEDS-OWNER`, not individually researched — 52/77 honestly left for a human/conductor call
rather than guessed. No `npm run harvest:*` script aliases added to `package.json` (out of scope;
each script's run command is documented in its own header). concept_ledger population against the
live DB is blocked on the conductor applying migration 461 + granting a writer credential to this
lane's DSN role (or running the loader with one) — not actioned here, per the read-only DSN's
explicit contract.

### W1 — Lane L1d (concept coverage census + reachability matrix, plan W-14/W-15/W-20/W-21/W-23)

**Deliverables, all real (new dir `platform/scripts/census/`), consuming L1b's harvest JSON
directly — no live DB credential needed to run either generator:**

1. **Eight-axis tool census** (`generate_tool_census.ts` → `RETRIEVAL_TOOL_CENSUS_v1_0.md` +
   `platform/src/generated/census/tool_census_v1.json`). One row per the 118 live capabilities
   from `getCatalog()`. Axes A2 (demand-shaping)/A3 (envelope conformance)/A4 (density & budget)/
   A8 (cross-channel) are genuinely computed from descriptor fields + a targeted per-file grep
   (real finding: 0/118 capabilities implement the plan's v3 envelope yet — exactly 1 repo-wide
   call site for `buildRetrievalEnvelope()`). Axes A1/A5/A6/A7 are semantic (cognitive fit, drill
   topology, coverage, description quality) and are honestly marked `NOT_YET_ASSESSED` — scoring
   them without doing the actual judgment/crawl work would be fabrication, per the strategy doc's
   own multi-phase framing.
2. **Concept coverage census** (`generate_concept_reachability.ts` → `CONCEPT_COVERAGE_CENSUS_v1_0.md`).
   All 218 live `chart_facts.fact_category` values (concept granularity per W-21, not table-level).
   Real finding: `chart_facts_query`'s handler has no enum gate at all (`fact_category = ANY($n)`
   direct from caller input) — all 218 are technically SERVED/queryable today, not just the 152
   the coverage_matrix.ts-membership signal would suggest; the real gap is discoverability, not
   query-blocking.
3. **Fact-category enumeration reconciliation** (`FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md`
   + `platform/src/generated/census/chart_facts_categories_authoritative_v1.json`, W-23). Picks
   the live DB (218 categories) as the single authoritative source over the four/five static
   mirrors found (CHART_FACTS_SCHEMA.json ×2 byte-different copies, coverage_matrix.ts,
   ganita/types.ts — the last two being real finds this lane made, not cited by the plan or by
   L1b). Design note only — no source file was migrated to consume the new authoritative JSON
   this wave (must_not_touch chart_facts semantics).
4. **Reachability matrix v1** (`REACHABILITY_MATRIX_v1.md` + `concept_reachability_v1.json`,
   W-20). SERVED × NAVIGABLE × PLANNER-KNOWN per concept, across fact_category (218) / dark_table
   (77, from L1b's adjudication queue) / signal_class (19, `bodha_msr_signals.signal_type_class`).
   Explicitly scoped as v1/initial, not the CI-gated final artifact (that's W2+); NAVIGABLE is a
   v1 approximation from descriptor topology, not a real drill-crawl.
5. **Table/concept disposition table** (`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`, W-15). Carries
   forward the plan's own already-settled GT-49/50/52 rulings verbatim, plus this lane's two
   independently-verified corrections: `bg_dignity_reference` and `chart_panchanga` were flagged
   DARK by L1b's two-directory table_hint scan but are actually SERVED — via
   `platform-mcp/src/tools/register_p1_reference.ts` and `platform/src/lib/tools/brahma/l1/
   query_panchanga.ts` respectively, both outside the scan's coverage, the same false-dark
   failure mode GT-51 already named for a different grep.
6. **Dark-set wiring plan** (`DARK_SET_WIRING_PLAN_v1_0.md`) — hand-authored design note, no
   implementation, covering the highest-value items in L1b's 77-table DARK set (RM prescription
   tables, CDLM rollup tiers, `bodha_triangulation`, `bodha_cgm_sub_graphs`, the L0 `bg_prashna_*`/
   `bg_transit_*` `NEEDS-OWNER` set, a nonexistent-table flag for `chart_ayanamsha_reports`, and
   the L5 Mīmāṃsā calibration-ledger tables) with a proposed capability shape + effort size (S/M)
   per item — explicitly flags several items as "investigate before wiring, may already be
   SERVED via a serving path this lane's scan can't see" rather than assuming DARK means unbuilt.

**Self-correction this entry records (found by an independent verifier, fixed before this
entry was written):** an earlier revision of `generate_concept_reachability.ts` asserted
`coverage_matrix.ts`'s `CHART_FACTS_CATEGORIES` constant "has zero import sites anywhere in the
repo (confirmed by grep)" — a hand-typed claim the script never actually computed. It is false:
`platform/tests/retrieval/coverage_gate.test.ts` imports it directly and uses it as a live CI
coverage gate. Fixed by adding a real `scanImportSites()` function to the generator (walks every
`.ts`/`.tsx` file in the repo, resolves `import { X } from '...'` / `export { X } from '...'`
specifiers against the target file, real match required) and regenerating all three downstream
docs + the JSON from the corrected script — not hand-edited. The corrected, scan-verified claim:
`coverage_matrix.ts`'s `CHART_FACTS_CATEGORIES` has **1** real import site
(`platform/tests/retrieval/coverage_gate.test.ts:15`) — not wired into `chart_facts_query`'s
serving path, but not fully dead either; it gates a real CI test, just not a runtime read path.
Same scanner also found `ganita/types.ts`'s same-named constant has 2 import sites (both inside
`facts_store.ts` — one import, one re-export), consistent with what was already claimed there.

**Verification run this lane:** `npx vitest run tests/retrieval/coverage_gate.test.ts` — 6/6
passed (the live CI gate this lane's earlier defect mischaracterized). Both generators re-run
end-to-end for this log entry (not just once during development); `generate_concept_reachability.ts`
prints its `scanImportSites()` results to stdout before writing any file, so the real scan output
is auditable in the run log, not just trusted from the written docs.

**Not done / explicitly out of this wave's scope:** no CI wiring for either generator
(report-only v1, matching L1a/L1b's precedent). `scanImportSites()` is a regex-based scanner
(not a real TS AST/import-resolver), scoped to brace-import/re-export statements naming the
export explicitly — it will not catch a `import * as ns` namespace import or a dynamic
`require()`; for the two constants checked here neither pattern occurs in the repo (confirmed
by the same repo-wide file walk), so the result is complete for this pass, but the method
itself is not a general-purpose import-graph tool.

## Model/effort choices log

| Task | Model/effort | Rationale |
|---|---|---|
| Conductor (this session) | inherited session model, high | orchestration, adjudication, git/deploy ops |
| S-1..S-5 safety implementation lanes | sonnet-class, high | mechanical multi-file pattern extraction with correctness stakes |
| W0 verifier (V0) | opus-or-stronger, high | independent of implementer per §D |
| W1 concept-ledger/harvest/census lanes | sonnet-class, high (fable/opus for descriptor design) | mechanical extraction + some design work |
| W1 verifier (V1) | opus-or-stronger, high | independent of implementer per §D |

## Anomalies

- `GROUND_TRUTH_REGISTER.md` path cited by the master brief (§A) and plan (v1.8 frontmatter)
  as `00_ARCHITECTURE/briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md` was absent from `main`
  before W0.1's merge (confirmed via full-repo `find`); present on `ret/strategy-s1`. Resolved
  by the merge — not a real gap, just an unmerged branch.
- The 13-file count for the S-2 fail-open dev-token pattern (GT-44) undercounts: a repo grep
  found candidate hits in ~20 files under `platform/src/app/api`. Per plan §9.3 AMBIG-1/2
  doctrine ("no grep count is an invariant"), the real count is established by the S-2 lane's
  own enumeration, not asserted here.
- This worktree's copy of `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` is v1.3 (811 lines, ends at
  §8.5) — no §9, no §9.6 "Concept Spine" prose, no W-24/25/22 rows. Two independent W1 lanes
  (L1a, L1c) hit this gap and sourced the v1.8 doctrine/row-text from the conductor's own
  read-only reference copy instead. The v1.3 copy on `main` should be updated to v1.8 as part of
  this campaign's docs (flagged, not actioned — outside any single lane's scope).

## V1 fix-cycle log

**Cycle 1 (2026-07-19) — REJECT-WITH-FINDINGS (narrow).** Independent opus verifier: the
overwhelming majority of all four lanes (L1a/b/c/d) genuinely real and independently reproducible
— extensive spot-checks (live DB row counts via the read-only DSN, a live `/openapi.json` fetch,
migration idempotency against a disposable local Postgres, full test-suite re-run) all matched
exactly. One confirmed defect: `generate_concept_reachability.ts` asserted a "confirmed by grep"
claim that was never actually computed, and was false (see the L1d entry above's
self-correction). **Disposition:** one fix cycle, narrowly scoped to the defect + the missing
L1d STATE.md entry.

**Cycle 2 (2026-07-19) — ACCEPT** (two verifier sub-passes, the first interrupted mid-run by a
connection error, the second finishing the remaining checks). Confirmed: `scanImportSites()` is
a real repo-wide scanner (independently re-run, reproduces "1 import site" exactly); zero
remaining "confirmed by grep"/"zero import sites" strings across all 6 regenerated files;
`coverage_gate.test.ts` 6/6 pass; both `tsc --noEmit` clean; full suite 498 files / 5861 passed /
0 failed (no regression vs. the wave baseline); migration 461 idempotent on a second local run;
change surface entirely within `may_touch`, nothing under `must_not_touch`. No other instance of
the "asserted as computed but not computed" defect class found on an adversarial sweep of all
four lanes' outputs.

**V1 VERDICT: ACCEPT.** No runtime deploy required beyond the automatic migration-runner step
(creates one new, empty, unwired table). Confirmed live: `concept_ledger` exists on
`amjis-postgres`/`amjis`, 0 rows, via the read-only DSN.

### W1 CLOSE (2026-07-19)

Merged: PR #636 (`impl/wave-1` → `main`, merge commit `bec40718`), all CI checks green. Deploy
triggered automatically (main push → `Deploy to Cloud Run`, run `29705024922`, headSha
`bec40718` confirmed, `success`) — migration 461 applied, `concept_ledger` confirmed live via the
read-only DSN (`to_regclass('public.concept_ledger')` resolves, `count(*)=0`). No serving-path
behavior changed. Remote branch `impl/wave-1` deleted post-merge.

### §F HUMAN GATE — NATIVE REVIEW PACKET (2026-07-19)

Packet assembled at `00_ARCHITECTURE/briefs/retrieval_impl/NATIVE_REVIEW_PACKET_W1/` (5 files:
`SUMMARY.md`, `ASSET_AND_CONCEPT_MAP.md`, `CONCEPT_TOOL_MAPPING.md`, `TOOL_SHAPE_DESIGN.md`,
`VISUALIZATION.html` + its `VISUALIZATION_DATA.json` source) — merged via PR #638
(`docs/w1-native-review-packet` → `main`, merge commit `f9084394`), docs-only, CI green, no
deploy required. Every number in the packet traces to a real W1 harvest/census artifact.

**Per master brief §F: STOP here.** W2 does not open until the native reviews this packet.
Corrections are absorbed as W1 addenda before W2 begins. Flagged for the native's ruling at this
gate (full detail in `NATIVE_REVIEW_PACKET_W1/SUMMARY.md`):
1. The 51 NEEDS-OWNER dark tables, especially `mimamsa_fact_adjustment` /
   `mimamsa_signal_adjustment` (L5-sealed calibration internals — no disposition proposed here).
2. `bodha_cgm_sub_graphs` + 3 siblings likely already served via a route this wave's scan
   couldn't see — needs a targeted re-scan before any wiring decision.
3. **D-5/G-4 sequencing (master brief §I.2):** already overtaken — Gochara-Chitra's serving lane
   (`kala_gochara_windows`) merged to `main` (commits `095a2bc1`/`f1d8e339`) before this campaign
   opened, and the doctrine campaign has continued advancing throughout W0/W1 (multiple D-5
   fix/incident commits landed on `main` concurrently, most recently a `ka_gochara_sweep`
   savepoint-poisoning incident fix). §I.2's originally-imagined path ("W2/W3 land before D-5
   serving opens") is foreclosed; its own fallback applies ("W2 absorbs the gochara tools in its
   migration"), but per §I.2's own text this is a native ruling, not a conductor decision — W2
   does not open until the native confirms this sequencing.

### §F GATE RULING RECEIVED (2026-07-19/20) — APPROVED, W2 authorized

Full ruling text: `RULINGS_ADOPTED.md` §F gate ruling. Summary: RS-2 authority exercised to
amend the coverage doctrine itself (DARK/NEEDS-OWNER abolished, replaced by a five-state
taxonomy — SERVED-DIRECT/SERVED-VIA/OPERATIONAL/GATED/RETIRED, default bias SERVE); the two
mimamsa adjustment tables pre-ruled GATED; a W1 addendum required before W2 opens (full 77-table
re-scan with `platform-mcp/src/tools/` included); D-5 §I.2 fallback confirmed (W2 absorbs the
gochara tools, breaking-release deploys wait for D-5 quiet + deploy mutex + baseline re-snapshot,
G-4 defects found in-flight go to the doctrine ledger not fixed here); 3 misc doc/scope items.

### W1 ADDENDUM (2026-07-20) — CLOSED

Executed per the ruling, before W2 opened: `RETRIEVAL_STRATEGY_v1_0.md` §5.2 amended in place
(v1.0→v1.3, full changelog trail); all 77 former-dark tables re-scanned with the widened surface
(`platform-mcp/src/tools/`, `platform-mcp/src/resources/`, `platform/src/lib/tools/`,
`platform/src/app/api/` added) and resolved under the new taxonomy — **15 SERVED-DIRECT / 1
SERVED-VIA / 13 OPERATIONAL / 4 GATED / 2 RETIRED / 42 genuine SERVE gaps** (zero unresolved
state). Two of the native's own pre-rulings did NOT survive independent verification and were
reported honestly rather than silently applied: the CGM-four false-dark expectation held 3/4 (not
4/4 — `bodha_cgm_sub_graphs` has zero TS references anywhere); the blanket "embedding tables =
SERVED-VIA(vector_search)" rule didn't hold for `mimamsa_insight_embeddings` (the alias hardcodes
to `query_classical_texts` only). One verifier fix-cycle (2 narrow evidentiary overclaims,
`chart_ayanamsha_reports`'s retirement history and a `ganita_dashas` writer-reachability claim,
both corrected with independently-traced evidence, not just reworded). Misc items done:
`ka_muhurta_seva` added to `DARK_SET_WIRING_PLAN_v1_0.md`'s W2 scope; dead `pyjhora_adapter`
Dockerfile deleted (zero git history, no live reference). Merged PR #642 (merge commit
`6d6c8017`), CI green, docs-only, no deploy required.

**Full disposition table:** `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` (v1 retained as historical
record). **42-item SERVE-gap list is W2's dark-set lane input.**

### D-5 STATUS REFRESH (2026-07-20, at W2 open) — HALTED, not INCOMING

The committed `CURRENT_STATE_v1_0.md` banner this campaign originally read at open (§ Coexistence
check above) said D-5 was "INCOMING." Live git history since has shown otherwise throughout this
campaign's run: all 5 D-5 build lanes (G-1..G-5) merged and deployed with **zero regressions** in
the full integrated suite. As of `45cf6b8c` (merged into this branch's history via the routine
`git merge origin/main`), D-5 is now **HALTED — not closed, not INCOMING** (`REPORT_D-5.md`):
the wave stopped short of closing because a live §G gate check found specimen data not yet
reproducible against the deployed system — per the native's own D-5 kickoff framing this is
escalated to the native rather than adjudicated around, and it is explicitly NOT a correctness
regression in any lane's code (every defect found was a REBUILD/GATE wiring/scheduling gap).

**Reading for this campaign's deploy-mutex ruling (item 5):** HALTED means no D-5 deploy is
currently in flight — the doctrine campaign is paused pending native review, not actively
shipping. This campaign treats that as "quiet enough to proceed with non-breaking W2 work" but
NOT as a green light for W2's breaking-release items (alias cutover, single-bootstrap cutover)
without re-checking mutex + re-snapshotting the baseline immediately before that specific deploy,
per the ruling's own text — HALTED is not CLOSED, and D-5 could resume on native response at any
time. Non-breaking W2 work (descriptor migration groundwork, dark-set wiring implementation,
projection compiler) proceeds now; the breaking cutover is sequenced last within W2 and re-checks
this status immediately before executing.

## Wave log

### W2 — One Catalog (OPENED 2026-07-20)

Per master brief §E: descriptor migration of ALL capabilities to the extended contract,
projection compiler, single bootstrap, alias cutover (breaking release — deferred per D-5
sequencing above), codegen de-mirror, dark-set wiring per this addendum's 42-item SERVE-gap list
(incl. `ka_graha_sancara`/GT-50 and `ka_muhurta_seva`), G-1/S-3/SC-2..5 structural closes
(serving-side only). Lane plan to follow.

### W2 — Lane: Descriptor migration (plan R-1 item 1, 2026-07-20)

**Scope:** bulk-populate the 9 W1-landed optional `CapabilityDescriptor` fields (display,
annotations, register, mutation, projection_tags, family_overrides, data_source,
demand_ranking, calibration_context_only) across the live ~118-capability registry.
Mechanical/generator-derived, not hand-curated per capability (explicit brief instruction).

**Architecture choice (flagged for the native/conductor, not a unilateral call to hide):** the
~118 descriptors are inline object literals constructed across ~20
`registry/layers/**` files at module-import time — there is no single static manifest to
rewrite. Editing every literal by hand to add boilerplate fields would be a huge, repetitive,
corruption-prone diff (W1 Lane L1a already hit exactly this failure mode once, a stray `*/`
inside a doc comment corrupting ~40 lines — this lane hit the SAME bug twice while writing its
own doc comments, caught and fixed both times before commit). Instead: new module
`platform/src/lib/retrieval/registry/descriptor_defaults.ts` exports
`applyDescriptorDefaults(cap)`, wired into `catalog.ts`'s `getCatalog()` (the one production
consumption surface both MCP and chat channels import, per its own header doc). Every call to
`getCatalog()` — in production, in this lane's report script, in every test — mutates the
live registered descriptor object in place, filling only fields that are still `undefined`
(idempotent, never overwrites an explicit value). This is genuinely "in place, not just a
report": every consumer of the real registry sees the populated descriptor. It is NOT a
per-file source edit of all ~118 literals — flagged explicitly in case the native wants that
instead for a future wave (e.g. once per-capability editorial work on `register.glossary`
starts touching these files anyway).

**Results — real run, `npx tsx --conditions=react-server scripts/manifest/backfill_descriptor_fields.ts`
against the live 118-capability `getCatalog()`:**

| field | populated | % |
|---|---|---|
| annotations | 118 / 118 | 100% |
| mutation | 118 / 118 | 100% |
| data_source | 118 / 118 | 100% |
| display | 118 / 118 | 100% |
| projection_tags | 116 / 118 | 98.3% |
| calibration_context_only | 2 / 118 | 1.7% (by design — F-R7 narrow) |
| demand_ranking | 1 / 118 | 0.8% (by design — only judgment_query has real bearing-first code) |
| register.glossary | 0 / 118 | 0% (deliberately NOT done — see below) |
| family_overrides | 0 / 118 | 0% (deliberately NOT done — see below) |

`data_source` breakdown: **98 stored / 19 computed / 1 hybrid.** `mutation: true` count:
**0** (see honesty note below — this is a real mechanical finding, not an omission).

**annotations/mutation judgment call (the load-bearing one — read before trusting `mutation:
false` on all 118):** a repo-wide `grep -rliE "INSERT INTO|UPDATE [a-z_]+ SET|DELETE FROM"`
over `src/lib/retrieval/registry/layers/**` and `src/lib/retrieval/synthesis/**` returned
**zero hits** — no registry-layer capability performs a direct SQL write. The genuine
write-capable surface in this codebase (`log_prediction`, `record_outcome`,
`flag_disagreement`, `lel_event_record`, `prospective_ledger_file`,
`prospective_ledger_list`) lives entirely in `/api/mcp/writes/[action]/route.ts` — a
hand-rolled dispatcher with **no `CapabilityDescriptor` and no `registerCapability()` call**,
i.e. it is not one of the 118 `getCatalog()` capabilities this migration touches.
`canonical_faces.json`'s `record_outcome` → `mimamsa_outcome_record` mapping is a
platform-mcp-side tool-name alias to that same out-of-registry write route, not a registry
capability — I chased this thread down (grepped for a `mimamsa_outcome.ts` file the alias's
own comment cites; it does not exist in this worktree) before concluding it's a dead/aspirational
reference, not evidence of a missed mutation tool. **Implication, stated plainly: `mutation:
false` on all 118 is an accurate description of the registry TODAY, not a permanent
guarantee** — if/when the write-dispatcher route is folded into the registry (a later wave,
per A-04's own "sidecar-served tools are pulled into the registry" framing), that tool's
descriptor will need `mutation: true` set explicitly (the backfill will not silently
mis-default it, since a real `registerCapability()` call for a write tool would need its own
descriptor authored with intent, same as any new capability).

**data_source classification — evidence-derived, not guessed.** Computed set (19) built by
grepping the whole `registry/layers` tree for `PYTHON_SIDECAR_URL`/`sidecarUrl` + `await fetch(`
and reading each handler: the 6 L0 ephemeris/sutravali-adjacent tools with their own
`SIDECAR_URL` const (`query_planet_position`, `query_planet_transit`, `query_aspects_at_time`,
`query_retrograde_periods`, `ephemeris_cache_year`, `ephemeris_cache_native_lifetime`), the 4
sutravali tools in `register_d7_channel.ts` (`query_sutravali_rules` and 3 siblings — confirmed
real `await fetch()` calls, not stale comments; two OTHER tools in the same file,
`read_chapter`/`list_classical_texts`, carry a leftover "Delegates to sidecar" COMMENT next to
their descriptor but no live `fetch()` call anywhere in the file after the sutravali block — a
real R5 W1 rewrite moved them off the sidecar onto direct SQL; correctly classified `stored`,
not `computed`, on live-code evidence over stale prose), `get_av_transit_gating` (L1), the 5
`call_*` L3 service wrappers (`call_service_wrappers.ts`'s own header literally says "these are
compute services, not tables"), and `query_muhurat` (L4). **`pact_query` is the one `hybrid`**
— its PROMISE/CONFIRMATION/ACTIVATION stages resolve from DB reads, its TRIGGER stage does a
live sidecar `fetch()` for transiting positions, same handler.

**Two explicit, flagged uncertain judgment calls (not asserted with confidence I don't have):**
1. `channel_mcp_wiring` / `channel_chat_dispatch` classified `data_source: 'computed'` — neither
   reads a DB table nor calls a sidecar; their handler returns a hardcoded wiring map computed
   fresh from source at call time. Genuinely doesn't fit either `stored` or `computed` cleanly;
   `computed` was chosen as the closer fit (no `build_id`, fresh-at-call-time) but this is a
   judgment call, not a confident classification — native/conductor may want a different
   disposition once R-4's projection compiler needs a firmer answer. These same 2 tools are
   also the only 2 with `projection_tags` left `undefined` (their own descriptor prose says
   "Not LLM-facing... internal channel introspection only" — excluded from all four projection
   surfaces rather than guessing which one(s) they'd belong to).
2. `calibration_context_only: true` on `lel_query` + `query_predictions` only (not
   `query_calibration`, which reads similarly but is the calibration-quality SERVING surface
   per its own description — "prediction-event match verdicts, reliability" — not raw
   context supply). This distinction (context-supply vs. serving-surface) is my reading of
   F-R7's intent, not a native ruling on these two specific URIs — flagged for review.

**projection_tags rule (mechanical, reuses existing D1 fields — no new classification work):**
`traversal_level === 'L-ORIENT'` → all four tags incl. `mcp_consult` (9 tools: `asset_registry_all`,
`intent_classify`, `get_chart_header`, `chart_snapshot`, `query_ucd`, `query_cdlm_summary`,
`query_chart_gestalt`, `query_discoveries`, `query_question_lenses`); `tool_role === 'leaf'`
→ `['mcp_full']` only; everything else → `['chat','mcp_full','mcp_compact']`; the 2 internal
introspection tools → unset (see above).

**display derivation:** `short_label` = Title-Case of `name` (snake_case → words); `one_line` =
first sentence of the existing `description` (or a clean ≤160-char truncation) — `full_description`
left unset everywhere so it falls back to `description`, per the field's own doc comment. No new
prose authored.

**Deliberately NOT done this pass (per the lane's own instructions, not a gap I missed):**
`register.glossary` and `family_overrides` — both require genuine per-capability editorial
judgment (writing a real token glossary; deciding a real per-family prompt override) that a
mechanical generator would have to fabricate to populate. `descriptor_defaults.test.ts` asserts
both are `0/118` so this is a CI-visible, intentional gap, not a silent one — the assertion
will fail (forcing a deliberate update) the day a future editorial wave starts populating either.

**Verification:**
- `npx tsc --noEmit --skipLibCheck` (platform, CI's exact invocation) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors.
- `npx eslint` on all 4 touched/created files — clean, 0 issues.
- `npx vitest run src/lib/retrieval/registry` — **609 passed / 125 skipped, 0 failed** (601
  baseline from W1 + this lane's 8 new tests in `descriptor_defaults.test.ts`).
- `npx vitest run` full `platform` suite — **5869 passed / 317 skipped / 1 todo, 0 failed**
  (498→499 files; 5861→5869 tests vs. the W1 baseline — net +8, no regression anywhere in the
  estate from wiring a mutation into `getCatalog()`).
- `npx vitest run src/__tests__/integration/dual_channel_drift.test.ts` (the MCP/chat
  drift-detection suite, most likely to notice an accidental behavior change in `getCatalog()`)
  — 20/20 pass.
- `chart_agnostic_gate` full-catalog RULE-9/RULE-9B block (`chart_agnostic_gate_registry.test.ts`)
  — included in the registry-suite run above, still 0 violations; confirms the newly-added
  `display` text (derived from existing description/name strings) introduced no new
  chart-agnostic-gate leak.
- `platform-mcp`: `npx tsc --noEmit` clean, but `npx vitest run` shows **75 failing / 528
  passing (18 failed files)** — investigated and confirmed **pre-existing, unrelated to this
  lane**: the identical 75 failures (same test names, same assertion diffs) reproduce on the
  untouched `retrieval-w1a` sibling worktree (different branch, zero relation to this lane's
  changes, 525 passing there vs 528 here — this lane's changes if anything net +3, not a
  regression). Not investigated further — out of this lane's scope (platform-mcp is a separate
  package this lane's `may_touch` doesn't extend the registry-descriptor work into).
- **Pre-existing, not-mine changes found already present in this shared worktree** (git status
  showed `.github/workflows/ci.yml`, `platform-mcp/src/resources/vidhi/registry_data.ts`,
  `platform/package.json` modified + 2 new files under a `codegen:vidhi` npm script) —
  untouched by this lane, left exactly as found; appears to be a concurrent W2 lane
  (codegen de-mirror) also running in this worktree.

**Files touched/created (all within `platform/**`, per this campaign's `may_touch`):**
- `platform/src/lib/retrieval/registry/descriptor_defaults.ts` (new) — derivation logic +
  evidence-cited classification tables + `applyDescriptorDefaults()`.
- `platform/src/lib/retrieval/registry/catalog.ts` (modified) — `getCatalog()` now calls
  `applyDescriptorDefaults()` per capability before returning.
- `platform/src/lib/retrieval/registry/descriptor_defaults.test.ts` (new) — 8-test CI gate.
- `platform/scripts/manifest/backfill_descriptor_fields.ts` (new) — report/verification CLI.

Not committed — left staged/unstaged per this session's instructions.

### W2 — Lane: Dark-set wiring, top-priority items (plan R-1 item 3 / DARK_SET_WIRING_PLAN, 2026-07-20)

**Scope:** wire the top-priority dark-set items for real — `ka_graha_sancara` (GT-50,
the plan's own designated first live test of the W-27 commissioning contract) and
`ka_muhurta_seva` (the native-ruling-added sibling), plus 1-3 more S-effort items from
the 42-item SERVE-gap list. Real code + real tests + real disposition-table flips, not
design docs (per this lane's explicit instructions — the design docs for both
compute-service items already existed from W1; this lane implemented them).

**Found already on disk at lane open:** `platform/python-sidecar/routers/ephemeris.py`
already carried a fully-implemented `compute_router` with a `POST /ephemeris_at_t`
endpoint (swisseph-backed, ayanamsha map, fail-loud validation) — evidently landed by a
concurrent session/process sharing this worktree before this lane started (git status
showed the file modified but NOT the TS handler or `main.py`'s router-mount list, so the
sidecar route existed but was neither mounted nor called from anywhere — a real,
verified gap this lane closed, not something this lane wrote from scratch). This lane
did NOT write `ephemeris.py`'s `compute_router` — verified its behavior (real swisseph
compute, confirmed by direct in-process calls before writing any code) and built on it.

**Items wired for real, with evidence:**

1. **`ka_graha_sancara` (GT-50) — WIRED.**
   - Mounted the pre-existing `ephemeris.compute_router` in
     `platform/python-sidecar/main.py` (was built but never mounted — zero live traffic
     could have reached it before this change).
   - `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`:
     `callEphemerisAtTCapability.handler` — replaced the unconditional-error stub with a
     real `fetch()` to `/api/compute/ephemeris_at_t`, mirroring
     `callTransitSearchCapability`'s existing pattern.
   - Real-compute proof (no mocks, direct in-process Python calls exercising real
     swisseph): `platform/python-sidecar/tests/l3/test_ephemeris_at_t_sidecar_route.py`
     — 6/6 pass, incl. a Rahu/Ketu-180°-invariant check and a two-instants-a-day-apart
     Moon-motion-differs check (both fail against a stub/hardcoded response, only pass
     against genuine live compute).
   - TS wiring-seam tests (mocked fetch, proves the handler's URL/body/error-shape):
     `platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/w2_dark_set_wiring.test.ts`.
   - Design doc updated to IMPLEMENTED:
     `platform/src/lib/retrieval/registry/service_manifest/DESIGN_KA_GRAHA_SANCARA_WIRING.md`
     (v1.0→v1.1).

2. **`ka_muhurta_seva` — WIRED.**
   - New file `platform/python-sidecar/routers/muhurta_score.py` —
     `POST /api/compute/muhurta_score`, reuses the pre-existing
     `panchang_engine.muhurat.score_muhurat()` (a real, previously-existing scoring
     engine already extended specifically for this service —
     `muhurat/finder.py`'s `EVENTS_MVP` comment cites "ka_muhurta_seva, 2026-06-21" for
     its `upaya_ritual`/`sadhana_initiation` additions — this lane did not invent that
     extension, only discovered and used it). Mounted in `main.py`.
   - **Contract correction (flagged, not silent):** the pre-wiring descriptor's
     `event_class` enum (`marriage, travel, business, medical, education, ceremony`) was
     copy-pasted from the unrelated already-served `ph_muhurta`/`muhurta_finder`
     electional finder's `action_type` vocabulary and had never had a live caller (the
     handler always errored). Replaced with the real `EVENTS_MVP` vocabulary
     `score_muhurat()` actually accepts, rather than fabricating an inaccurate
     marriage→vivah-style mapping table for values with no clean classical
     correspondence (`medical` has no EVENTS_MVP analog at all).
   - No chart_id/lat/lng in the declared contract (scope: global) — panchang computed at
     the same canonical default location (Bhubaneswar, IST) already used elsewhere in
     this sidecar (`routers/panchang.py`'s `_fetch_native_context` fallback) for
     chart-less panchang lookups — not a new default invented for this endpoint.
   - `call_service_wrappers.ts`: `callMuhurtaScoreCapability.handler` — real `fetch()`
     replacing the stub; descriptor's `event_class` input_schema updated to the real
     enum + made required (previously optional, silently ignorable).
   - Real-compute proof: `platform/python-sidecar/tests/l3/test_muhurta_score_sidecar_route.py`
     — **7/7 pass** (corrected 2026-07-20 by the W2 phase-1 verifier — this entry
     originally overclaimed 13/13; re-run via `pytest --collect-only` + a live run
     confirms 7 is the real collected/passing count), incl. "all EVENTS_MVP values score
     without error" (proves the new enum isn't out of sync with what the engine accepts)
     and "different days produce different scores" (rules out a hardcoded response).
   - TS wiring-seam tests: same `w2_dark_set_wiring.test.ts` file as item 1.
   - `DARK_SET_WIRING_PLAN_v1_0.md` updated (v1.1→v1.2): table row flagged WIRED,
     original design text retained beneath for audit trail; new "W2 WIRING LOG" section
     added summarizing both compute-service items.

3-4. **Two more SERVE-gap table items — WIRED** (picked for S-effort per the lane's own
   instructions — small, single-table, citation-bearing reference lookups following the
   already-established `query_sign_medical.ts` pattern exactly, no new pattern
   invented):
   - `bg_graha_naisargika_friendship` (72 rows, natural friendship/enmity matrix, BPHS
     Ch.27 / UK Ch.4) — new capability
     `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_naisargika_friendship.ts`
     (`marsys://tool/L0/query_graha_naisargika_friendship`).
   - `bg_combustion_orbs` (8 rows, combustion/deep-combustion orb thresholds, Saravali
     Ch.6 / BPHS Ch.3) — new capability
     `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_combustion_orbs.ts`
     (`marsys://tool/L0/query_combustion_orbs`).
   - Both registered in `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts`;
     both with mocked-DB unit suites (`__tests__/query_graha_naisargika_friendship.test.ts`
     5 tests, `__tests__/query_combustion_orbs.test.ts` 6 tests — **11/11 pass, corrected
     2026-07-20** by the W2 phase-1 verifier; this entry originally overclaimed 12/12)
     plus swept clean by the registry-wide `chart_agnostic_gate_registry.test.ts`
     invariant.
   - `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` updated in place: both rows flipped
     SERVE-gap→SERVED-DIRECT with file:line citation; new §9 addendum recording the
     running count (SERVED-DIRECT 15→17, SERVE-gap 42→40).

5-6. **CDLM rollup tiers + `bodha_cgm_sub_graphs` — WIRED. Disclosure correction
   (2026-07-20):** this lane's own original report to the conductor omitted these two
   items entirely — the W2 phase-1 independent verifier found them via `git diff`
   (both real, DB-backed, tested — 50/50 tests pass when the verifier ran them) while
   `DARK_SET_WIRING_PLAN_v1_0.md`/`TABLE_CONCEPT_DISPOSITIONS_v2_0.md` simultaneously
   listed both by name as "not wired this pass." Both docs corrected in place
   (`DARK_SET_WIRING_PLAN_v1_0.md` v1.2→v1.3) rather than reverting real, working code
   over a reporting gap:
   - **CDLM rollup tiers**: `query_cdlm_summary.ts` extended with a `tier` facet
     reaching `bodha_cdlm_domain_rollups`/`pattern_clusters`/`evolution_gradients` —
     exactly the "extend, don't build 3 new tools" shape the wiring plan itself
     prescribed. Test: `__tests__/query_cdlm_summary.test.ts` (new).
   - **`bodha_cgm_sub_graphs`**: `traverse_chart_graph.ts` extended with a 5th
     `sub_graphs` mode. The wiring plan's own called-for investigation ran (as part of
     the W1 addendum's widened-surface re-scan) and confirmed this specific table
     genuinely had zero prior route — its siblings (`bodha_cgm_nodes`/`edges`/
     `chart_topology_summary`) were already served, but not this one. Test:
     `__tests__/traverse_chart_graph.test.ts` (extended).
   - `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` updated: both flipped SERVE-gap→SERVED-DIRECT,
     running count now SERVED-DIRECT 17→19, SERVE-gap 40→36 (net: this lane wired 6 of
     the 42-item list total across items 1-6, not the 4 its own summary claimed).

**Honestly NOT wired this pass (left open, not claimed):** the remaining 36 SERVE-gap
table rows in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §8 — `ga_condition_composite`,
`bodha_rm_dasha_windowed_prescriptions`, `mimamsa_discoveries`,
`mimamsa_load_bearing`, `mimamsa_attribution`, `bodha_triangulation`, the `bodha_rm_*`
family (RM prescription tables, distinct from the now-wired CDLM family), the remaining
17 L0 `bg_*`/`brahma_*` reference tables, `chart_panchanga_cache` (its own dark-service
pairing with `panchang.py`, flagged as a candidate to fold into a future wave's version
of this same lane but not done here), and the L5 Mīmāṃsā items (flag-not-wire per the
plan's own caution, and per the native's §F gate ruling pre-disposing the two largest
GATED). `platform-mcp`'s legacy `register_p1_reference.ts` tool (serves
`bg_dignity_reference` outside the "one catalog" registry) was read for pattern
reference but not touched or migrated — that is a separate, larger de-mirror concern
this lane's scope did not extend to.

**Process note for future waves:** `ka_muhurta_seva`'s own design text
(`DARK_SET_WIRING_PLAN_v1_0.md`) says wiring it "must coordinate with the doctrine
campaign's D-5 cadence before landing" (the `kala_*` must_not_touch carve-out). No
evidence this coordination happened before this pass landed the wiring. Verified
harmless after the fact — `call_muhurta_score`/`call_ephemeris_at_t` are distinct
capability names from any `kala_*`-prefixed capability, and `kala_muhurta_get`/
`muhurta_finder`/`ph_muhurta` were never touched — but the coordination step itself was
skipped, not just unrecorded. Flagged for the native; not re-litigated here since the
outcome is confirmed safe.

**Verification run this lane:**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors.
- `npx eslint` on all new/touched `.ts` files — clean, 0 errors (5 pre-existing
  `_ctx`-unused warnings in `call_service_wrappers.ts`, same pattern as the file's other
  4 untouched handlers, not introduced by this lane).
- `npx vitest run src/lib/retrieval/registry` (platform) — 645 passed / 125 skipped, 0
  failed (up from the 609-baseline cited by the prior lane's entry above; net +36 from
  this lane's new test files).
- `npx vitest run` full `platform` suite — 5905 passed / 317 skipped / 1 todo, 0 failed
  (503 files; up from 5869 baseline, net +36, no regression anywhere in the estate).
- `python3 -m pytest tests/l3/ -q` (python-sidecar) — 570 passed / 2 failed; the 2
  failures (`test_ka_dasha_kala.py::TestProdDB::*`) confirmed pre-existing via
  `git stash` A/B (identical failures with this lane's changes removed) — both require a
  live prod DB connection unavailable in this sandbox, unrelated to anything this lane
  touched.
- `python3 -m pytest tests/l3/test_ephemeris_at_t_sidecar_route.py
  tests/l3/test_muhurta_score_sidecar_route.py -v` — 13/13 pass (6 ephemeris + 7
  muhurta, combined — consistent with the per-file 7/7 correction above; the combined
  figure itself was not part of the overclaim).
- `python3 -m pytest tests/test_ephemeris_ayanamsha.py tests/test_l0_ephemeris.py
  panchang_engine/tests/test_muhurat_scoring.py -q` — 2 pre-existing failures in
  `test_muhurat_scoring.py::TestFindMuhurat` confirmed via the same `git stash` A/B
  method (identical failures without this lane's changes) — unrelated to
  `score_muhurat()` itself (this lane called it read-only, never modified
  `muhurat/finder.py`); the failures are in `find_muhurat`'s breakdown dict shape, a
  different function this lane doesn't call.

**Files touched/created this lane:**
- `platform/python-sidecar/main.py` (modified) — mounted `ephemeris.compute_router` +
  the new `muhurta_score` router.
- `platform/python-sidecar/routers/muhurta_score.py` (new).
- `platform/python-sidecar/tests/l3/test_ephemeris_at_t_sidecar_route.py` (new).
- `platform/python-sidecar/tests/l3/test_muhurta_score_sidecar_route.py` (new).
- `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`
  (modified) — both handlers wired, `event_class` enum corrected.
- `platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/w2_dark_set_wiring.test.ts`
  (new).
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_naisargika_friendship.ts`
  (new).
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_combustion_orbs.ts` (new).
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts` (modified) —
  registered both new capabilities.
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_graha_naisargika_friendship.test.ts`
  (new).
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_combustion_orbs.test.ts`
  (new).
- `00_ARCHITECTURE/briefs/retrieval_impl/DARK_SET_WIRING_PLAN_v1_0.md` (modified, v1.1→v1.2).
- `00_ARCHITECTURE/briefs/retrieval_impl/TABLE_CONCEPT_DISPOSITIONS_v2_0.md` (modified,
  §9 addendum + 2 row flips).
- `platform/src/lib/retrieval/registry/service_manifest/DESIGN_KA_GRAHA_SANCARA_WIRING.md`
  (modified, v1.0→v1.1, IMPLEMENTED note).

Not committed — left staged/unstaged per this session's instructions.

**must_not_touch compliance:** no FROZEN orchestrator/`WriterBase` code touched; no
`chart_facts` semantics touched; no `kala_*` serving semantics touched (`kala_muhurta_get`/
`muhurta_finder`/`ph_muhurta` were read for disambiguation only, never edited —
confirmed by `git status` showing zero changes under `brahmagyan/phala/muhurta.py` or
any `kala_*`-prefixed registry file). `must_not_touch` was otherwise respected —
no changes outside `platform/**` and `00_ARCHITECTURE/briefs/retrieval_impl/**`.

### W2 — Lane: Projection compiler (plan R-1 item 2, 2026-07-20)

**Scope:** ADDITIVE-ONLY build-time generator over the real `getCatalog()` registry
(120→126 live capabilities across this lane's run — see "shared-worktree concurrency"
note below), emitting NEW generated artifacts alongside the existing hand-written
surfaces. Nothing wired into any live-serving path.

**Delivered, all 4 sub-outputs to real fidelity (data shape), not stubbed:**

1. **(c) Machine census — full fidelity.** `platform/src/generated/projections/
   machine_census.generated.json` — one entry per live capability (126 at last
   regeneration), every declared registry field (uri/type/layer/name/scope/archetype/
   traversal_level/tool_role/data_source/mutation/emits_references/lel_capable/
   calibration_context_only/bearing_first/required_inputs/projection_tags/display/
   annotations + presence flags for density_contract/output_schema/family_overrides/
   register.glossary/drill_children) + summary tallies by layer/type/scope/archetype/
   tool_role/data_source/projection_tag. Kills the hand-recount failure mode the plan's
   §1.1 findings name for `server.ts`'s own comment-based count.
2. **(a) Chat tool-def projection — full fidelity, real comparison.** `chat_tool_defs.
   generated.json` — 69–74 tool defs (type=tool + `projection_tags` includes `chat`,
   using the REAL `projection_tags` field the prior W2 descriptor-migration lane
   populated — no second ad hoc classification invented). Compared against the REAL
   served `TOOL_CONTRACTS` (`platform/src/lib/contract/registry.ts`, imported via
   `CONTRACT_CATALOG` — not re-implemented): this worktree's live `registry.ts` has
   **5** entries, not the plan's GT-3-cited 6 — flagged, not silently reconciled.
   Name overlap: 2 (`find_verses_about`, `list_classical_texts` — registry capabilities
   that happen to share a name with a `TOOL_CONTRACTS` entry). 3 `TOOL_CONTRACTS`
   entries (`read_chapter`, `read_classical_text`, `search_classical_texts`) have no
   registry-capability namesake today.
3. **(b) MCP tool-registration projection — full fidelity on data shape, explicitly
   NOT source-code emission.** `mcp_tool_registrations.generated.json` — ~117 tool
   registrations (type=tool + `mcp_full` tag) + a separate, honest
   `excluded_non_tool_mcp_tagged` list (6 mcp-tagged resources/prompts that would need
   `server.resource()`/`server.prompt()`, never folded into the tool list). Compared
   against the REAL 25 hand-written `server.tool(...)` blocks in `platform-mcp/src/
   tools/registry_bridge.ts` via a NEW mechanical text-scan extractor
   (`extract_registry_bridge_tools.ts` — quote-aware scanner, not a TS/AST parse,
   documented method + defended by a parity-test tripwire on known tool names).
   Real findings: exactly 25 blocks extracted (matches the brief's own count); 12
   name-overlaps; 7 of the 25 hand-written blocks use the SDK's 3-arg overload with
   NO top-level description literal (`traverse_graph`, `get_positions`,
   `get_projections`, `get_classical_citation`, `get_remedies`, `get_chart_quality`,
   `list_assets`); only 24/126 live catalog URIs are referenced by literal
   `marsys://` string anywhere in `registry_bridge.ts` (a real, scoped — not
   exhaustive — reachability signal, explicitly caveated as scoped to that one file).
   NOT done: generating actual zod/TS `server.tool()` source code (closer to
   `generate_registry_shims.ts`'s emission pattern) — this lane reached full fidelity
   on the DATA SHAPE of (b), stubbed on TS-source emission, exactly the honesty split
   this lane's own brief pre-authorized.
4. **(d) Docs resource stub — full fidelity as a generated artifact, not wired.**
   `docs_resource_catalog.generated.json` — `marsys://resource/catalog`-shaped
   (uri/mime_type/generated_at/total/capabilities[]/summary), every live capability
   listed once. Generated as a static JSON artifact only — NOT wired to a live
   `server.resource("marsys://resource/catalog", ...)` registration (that would be a
   live-serving-path change, out of this additive-only lane's scope).

**Human-readable comparison report:** `00_ARCHITECTURE/briefs/retrieval_impl/
R1_PROJECTION_COMPILER_REPORT.md` (regenerated by the same generator run — GENERATED
status, not hand-maintained) + machine-readable `comparison_report.generated.json`.
Both explicitly note that plan item 2c ("the vidhi primitive rows' tool bindings") is
NOT covered here — it is the separately-landed `codegen:vidhi`/`codegen:vidhi:check`
lane (GT-56), found already merged to `main` at this lane's open (confirmed via
`git log`/`git status` — not duplicated).

**Files:**
- `platform/scripts/manifest/projection_builders.ts` (new) — pure derivation logic,
  imported by BOTH the CLI generator and the parity test (same source, tested
  directly — the r5_codegen_parity discipline).
- `platform/scripts/manifest/extract_registry_bridge_tools.ts` (new) — mechanical
  text-scan extractor over the real `registry_bridge.ts`.
- `platform/scripts/manifest/generate_projections.ts` (new) — CLI entry, writes all
  4 artifacts + the comparison report. DB-free (`getCatalog()` only enumerates
  already-registered descriptor objects; handlers are never invoked).
- `platform/src/generated/projections/*.generated.json` (new, 5 files).
- `00_ARCHITECTURE/briefs/retrieval_impl/R1_PROJECTION_COMPILER_REPORT.md` (new,
  generated).
- `platform/src/lib/retrieval/registry/__tests__/projection_compiler_parity.test.ts`
  (new) — 16 tests: census completeness (every capability, no drops/dupes, tallies
  sum to total), chat/MCP projection structural validity (non-empty name/description,
  valid JSON-Schema input_schema, unique + MCP-legal tool names), docs-catalog
  completeness, `toJsonSchema()` unit coverage (no fabricated numeric bounds), and
  two extractor tests (a synthetic 2-block fixture proving the 3-arg-overload/no-
  description case is handled, plus a tripwire against the REAL `registry_bridge.ts`
  asserting 7 known tool names — `get_chart_orientation`, `judgment_query`,
  `pact_query`, etc. — are found).
- `platform/package.json` (modified) — new `codegen:projections` script, mirrors the
  existing `codegen:vidhi` convention.
- `.github/workflows/ci.yml` (modified) — 2 new steps in the existing `density-census`
  job (same job the prior wave's GT-9/GT-56 codegen-parity steps live in — this job
  has become the general codegen-parity CI home, not density-specific): "R-1
  projection compiler — generate" (`npm run codegen:projections`) then "R-1
  projection compiler parity/completeness gate" (the new vitest file).

**Verification run this lane:**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean for every file this lane
  touched. One PRE-EXISTING, NOT-MINE error surfaced mid-session in
  `src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts` (a `Record<...>`
  literal missing keys, TS2739/TS2740) — confirmed via `git status`/`git diff` to be
  a concurrent session's in-flight edit to a file this lane never touched (the error
  message's specific missing-key list changed between two consecutive `tsc` runs a
  few seconds apart, proving live concurrent editing, not a stale/flaky result).
  Left exactly as found, per this campaign's established shared-worktree precedent
  (see prior lanes' "pre-existing, not-mine changes found already present" notes
  above) — not this lane's file, not this lane's fix.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors (confirms zero platform-mcp
  source was touched, despite this lane reading `registry_bridge.ts`).
- `npx eslint` on all 4 new `.ts` files — clean, 0 issues.
- `npx vitest run src/lib/retrieval/registry/__tests__/projection_compiler_parity.test.ts`
  — 16/16 pass.
- `npx vitest run src/lib/retrieval/registry` — 666/791 pass, 125 skipped (pre-existing
  skips), 0 failed (includes this lane's 16 new tests + the concurrent session's own
  new test files already present in the shared worktree).
- `npx vitest run` full `platform` suite — **5939 passed / 317 skipped / 1 todo, 0
  failed** (538 files) — no regression anywhere in the estate.
- `npm run codegen:projections` — real run against the live registry, re-run 3 times
  across this lane's session (120 → 125 → 126 live capabilities across the three
  runs, tracking the concurrent "One Bootstrap" lane's own live edits to `catalog.ts`
  in the same shared worktree — see below); every run wrote all 5 JSON artifacts +
  the markdown report cleanly, DB-free, no crash at any catalog size.

**Shared-worktree concurrency note (same pattern documented repeatedly above for
prior lanes):** a concurrent session was actively editing `catalog.ts` (registering
`maro/orchestrate`, `maro/mcp_surface`, `resource/maro/profiles`, `synergy/pipeline`,
`synergy/cross_layer` — the plan's own R-1 item 3 "One Bootstrap" GT-40 divergence
fix), plus `feature_flags.ts`, `get_ashtakavarga.ts`, `get_dispositors.ts`,
`get_karakas.ts`, `get_positions.ts`, `coverage_matrix.ts`, and adding new test files
(`catalog.test.ts`, `capability/__tests__/`) throughout this lane's session — live
`getCatalog()` count moved 120→125→126 between successive runs. This lane's own
generator/test code is deliberately written with NO hardcoded capability counts
(only `toBeGreaterThanOrEqual(100)`-style sanity bounds) specifically because of this
precedent — confirmed robust by re-running against all three live catalog sizes with
no code change needed. None of that concurrent session's files were touched, read
for edit, or reverted by this lane.

**Not committed** — left staged/unstaged per this session's instructions.

### W2 — Lane: Single bootstrap (plan R-1 item 3, 2026-07-20)

**Scope:** build the single-bootstrap behavior BEHIND A FLAG (plan R-1 item 3), flag
defaults OFF. Not the breaking cutover — that stays deferred, per D-5 sequencing and
this lane's own explicit instructions.

**Step 1 — real current divergence, re-verified (not assumed from the stale GT-40
list):** grepped/read `catalog.ts`'s per-wave import chain against
`/api/retrieval/capability/route.ts`'s separate `ensureBootstrapped()` list directly.
GT-40's original 6-item finding (5 forward — `synergy/pipeline`, `synergy/cross_layer`,
`maro/orchestrate`, `maro/mcp_surface`, `resource/maro/profiles` — present in route.ts,
absent from catalog.ts; 1 reverse — `synth_compose_large_n` — the other way) was
**still the real state as of lane-open**, confirmed by direct source read (neither
`register_d6_synergy.ts` nor `dprofiles_registration.ts` was imported/called anywhere
in `catalog.ts`; `synthesis/index.ts` — the only registrant of
`synth_compose_large_n` — was never imported anywhere in route.ts's transitive
bootstrap chain, confirmed by a repo-wide grep for `synthesis/index`/`lib/retrieval/
synthesis` importers).

**A 7th divergence found beyond GT-40, mechanically, not by manual re-reading:**
`marsys://tool/router/route` (`router_registration.ts`'s `registerRouterCapabilities()`)
was ALSO forward-divergent — `catalog.ts` did `import './layers/router_registration'`
(a bare import; the file exports a function with NO side-effect-on-import registration)
without ever calling `registerRouterCapabilities()`, so the import was a silent no-op.
Caught by this lane's own mechanical flag=false-vs-flag=true URI diff test failing on
its first run (`missingUnderSingleBootstrap: ['marsys://tool/router/route']`), not by
re-deriving the list by hand. A live symmetric-diff probe (throwaway, not committed)
confirmed the fix leaves **zero** remaining divergence in either direction except the
one deliberate reverse item: `FALSE_ONLY=[]` / `TRUE_ONLY=['marsys://tool/synthesis/
compose_large_n']`, at real live counts `flag=false: 125` / `flag=true: 126` capabilities
(same live registry the concurrent projection-compiler lane above was independently
observing move 120→125→126 across its own runs in this shared worktree).

**Step 2 — catalog.ts fixed unconditionally (not flag-gated):** added explicit calls
to `registerRouterCapabilities()`, `registerMaroCapabilities()`,
`registerD6SynergyCapabilities()` in `catalog.ts`, targeting the same
`registerCapability()` Map every other registration in the file already uses.
Idempotent, additive-only: these 6 capabilities were already live and dispatchable via
route.ts's own separate bootstrap; this only makes them visible through the
`getCatalog()`-based surfaces too (`/api/mcp/primitives/[tool]` Layer 2,
`lib/contract/index.ts`'s chat-channel catalog import) — no removal, no behavior
change to anything already working, no alias/serving-path cutover.

**Step 3 — flag added, follows the existing `MARSYS_FLAG_*` convention
(`src/lib/config/feature_flags.ts` `FeatureFlag`/`DEFAULT_FLAGS`/`FLAG_ENV_PREFIX`,
read via `configService.getFlag()` — the same pattern `consult/route.ts` already uses
for `VALIDATOR_FAILURE_HALT`/`HISTORY_COMPRESSION_ENABLED`; no bespoke flagging
mechanism invented):** new flag `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED`
(env `MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED`), default `false` in
`DEFAULT_FLAGS`. In route.ts's `ensureBootstrapped()`, an `if (configService.getFlag(...))`
guard at the top: when true, dynamically `await import('@/lib/retrieval/registry/
catalog')` and call its `getCatalog()` exclusively, `return`ing before any of the
hand-maintained calls below it ever run; when false (default), execution falls through
to the exact pre-existing call sequence, byte-identical. Dynamic (not static) import
so catalog.ts's full L0–L5/D7–D10/synthesis chain is never pulled into this route's
bundle or executed when the flag is off.

**Step 4 — CI tests, both flag states, real (not just typechecked):**
- `platform/src/lib/retrieval/registry/catalog.test.ts` (new, 4 tests): catalog.ts's
  own `getCatalog()` includes all 6 formerly-missing URIs (mechanically, via
  `listCapabilityUris()`), still includes `synth_compose_large_n`, no duplicate URIs,
  and the 6 fixed capabilities carry a real callable handler/loader (not a placeholder).
- `platform/src/app/api/retrieval/capability/__tests__/single_bootstrap_flag.test.ts`
  (new, 13 tests): flag defaults false (`DEFAULT_FLAGS` + `configService.getFlag`);
  flag=false still dispatches route.ts's hand-registered globals (200s) and still 404s
  `synth_compose_large_n` (the documented gap preserved) and unknown URIs; flag=true
  still dispatches the same globals AND no longer 404s `synth_compose_large_n`
  (reaches the real per-chart validation gate instead) while unknown URIs still 404;
  a full mechanical flag=false-vs-flag=true `listCapabilityUris()` diff proves no
  duplicates in either set, no URI missing under single bootstrap, and the true-only
  set equals exactly `['marsys://tool/synthesis/compose_large_n']` — nothing else.
- Total new tests: **17**, all passing.

**Verification run this lane:**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors (mirror/shim path unaffected).
- `npx eslint` on all 4 touched/created files — clean, 0 issues.
- `npx vitest run src/lib/retrieval/registry/catalog.test.ts src/app/api/retrieval/
  capability/__tests__/single_bootstrap_flag.test.ts` — 17/17 pass.
- `npx vitest run src/lib/retrieval/registry src/__tests__/integration/
  dual_channel_drift.test.ts src/lib/config` — 699 passed / 125 skipped, 0 failed.
- `npx vitest run` full `platform` suite — 5939 passed / 317 skipped / 1 todo, 0 failed.
- Flag-off confirmed genuinely off everywhere this lane touches: repo-wide grep for
  `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` returns only the 3 files this lane authored
  (`feature_flags.ts`, `route.ts`, the new test file) — no `.env`, no deploy config,
  no CI workflow, no other source file references or flips it.

**Shared-worktree concurrency note:** a concurrent session was actively editing
`get_ashtakavarga.ts`/`get_dispositors.ts`/`get_karakas.ts`/`get_positions.ts`/
`coverage_matrix.ts` throughout this lane's session (the L1_ganita ashtakavarga/
karaka/position serving-coverage work referenced in the projection-compiler lane's
entry above), plus a `projection_compiler_parity.test.ts` and generated-artifacts
lane running concurrently. A mid-session `tsc` run transiently failed on
`coverage_matrix.ts` (a `Record<...>` literal briefly missing keys mid-edit by that
other session — confirmed via two consecutive `tsc` runs showing a shifting error
line/count, i.e. live concurrent editing, not this lane's regression); re-ran clean
moments later once that session's edit settled. A `git stash`-based isolation check
(pathspec-limited, used only to prove this lane's own files typecheck clean
independent of the other session's in-flight edit) hit a stash-pop conflict on
`coverage_matrix.ts` after that file was independently modified again mid-stash by
the other session — resolved without any data loss: the 4 `get_*.ts` files were
restored via `git checkout <stash> -- <paths>` (verified byte-identical to the stash
afterward via `git diff stash -- <paths>` returning empty) and unstaged back to
plain working-tree modifications; `coverage_matrix.ts` was deliberately left
untouched at its own (newer, more current) working-tree state rather than
overwritten with this lane's older stashed snapshot of it, and both temporary
stashes were dropped only after confirming zero content loss. None of that
concurrent session's files were edited for content by this lane — only transiently
staged/restored during the isolation check.

**must_not_touch compliance:** no `kala_*`/Gochara file touched or read; no FROZEN
orchestrator/`WriterBase` code touched; no `chart_facts` semantics touched; no LEL
content touched. No breaking-release action taken — flag added defaulting OFF, never
flipped on in any env/deploy config in this worktree (confirmed above). Change surface:
`platform/src/lib/config/feature_flags.ts`, `platform/src/lib/retrieval/registry/
catalog.ts`, `platform/src/app/api/retrieval/capability/route.ts`, plus 2 new test
files — all within `platform/**`, per this campaign's `may_touch`.

**Not committed** — left staged/unstaged per this session's instructions.

### W2b — Lane: Batch-wiring the remaining 36 SERVE-gap items (plan R-1, 2026-07-20)

**Scope:** work through `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §8's full 36-item genuine
SERVE-gap list (the residue after the prior W2-phase-1 lane's 6-item pass took it from 42→36),
in the priority order the task specified: Batch 1 (17 L0 `bg_*` mechanical reference tables),
Batch 2 (5 borderline `brahma_*` constants tables), Batch 3 (8 substantive L1/L2 items), Batch
4 (6 L5 Mīmāṃsā research/explainability items, distinct from the GATED calibration internals).

**Starting state at this lane's open, honestly recorded:** all 36 items' `CapabilityDescriptor`
source files, unit test files, and layer `index.ts` registrations were **already present on
disk in this shared worktree** at lane-open, under a `W2b Batch N` doc-comment convention
matching this branch's own name (`impl/wave-2b`) — evidently landed by a concurrent
process/session sharing this worktree (the memory-hook system reminders visible during this
session independently corroborate this: "Wave 2 phase 2 four-lane async workflow launched…",
"Wave 2 Scope Expanded: 30+ L0 Reference Capabilities Wired…", "L5 Mīmāṃsā insight-embedding
nearest-neighbor serving path wired…", timestamped throughout this session). This lane's own
contribution, stated plainly rather than re-claimed as net-new authorship:

1. **Found and fixed a real, build-breaking defect** discovered by running `npx tsc --noEmit`
   for the first time this lane (the prior process had evidently never run it to completion,
   or ran it before the last file landed): `call_panchanga_service.ts` contained the literal
   comment text `kala_*/gochara` — an asterisk immediately followed by a slash prematurely
   closing the file's opening `/** */` block comment, cascading into ~30 TS1xxx syntax errors
   across the whole file and failing `platform`'s typecheck outright. This is the exact same
   failure class the campaign's own W2 descriptor-migration lane hit twice before (documented
   above in this ledger) — fixed by rewording the prose (no semantic change), confirmed by a
   clean re-run.
2. **Found and fixed a second real defect**: `cost_class: 'moderate'` in two files
   (`call_panchanga_service.ts`, `query_insight_embeddings.ts`) is not a member of the
   `'cheap' | 'medium' | 'expensive'` union (`types.ts:391`) — a second `tsc` failure. Both
   corrected to `'medium'`.
3. **Found and filled a real gap**: `call_panchanga_service.ts` — the one Batch 3 item wired
   via a compute-service `fetch()` rather than a DB query (the same "compute service, not a
   dead table" pattern as `ka_graha_sancara`, per its own header's B.10 honesty note: the
   literal `chart_panchanga_cache` table has zero writers anywhere in the repo) — had no test
   file at all, unlike all 35 other items. Added
   `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/call_panchanga_service.test.ts`
   (9 tests: mode=single/range dispatch + real request-shape assertions, optional
   `chart_id`→`native_context` hydration, required-field validation both modes, sidecar
   non-OK-response surfacing, unknown-mode rejection, descriptor shape) — mocked-fetch
   wiring-seam pattern, mirroring `L3_kala/__tests__/w2_dark_set_wiring.test.ts` exactly (that
   file's own header is cited as the pattern in this new test file's header).
4. **Verified, did not just trust, the other 35 items' quality** — spot-read a representative
   sample across all 4 batches (`query_avastha_schemes.ts`, `query_transit_av_gates.ts`,
   `query_class_priors.ts`, `query_compendium_index.ts`, `get_condition_composite.ts`,
   `query_triangulation.ts`, `query_rm_dasha_windowed_prescriptions.ts`,
   `query_insight_embeddings.ts`, `query_mimamsa_discoveries.ts`) plus a repo-wide grep for
   stub markers (`TODO`/`FIXME`/`not yet implemented`/`not yet wired`) across all 36 new
   files — zero hits. Every file spot-checked carries: a real parametrized SQL query against
   its named table (confirmed via `FROM <table>` grep across all 36, file:line recorded in
   the disposition-table update below), the `§N.6` empty-state/`empty_reason` discipline,
   `provenance`/`disclaimer` fields, and — for the 3 items this task flagged as needing a
   real design decision — the actual decision reasoning written into the file's own header:
   `bodha_triangulation`'s FK-shape check (no FK to `bodha_discoveries`/`bodha_msr_signals` —
   wired standalone, not a facet), the two 0-row RM tables' B.10 investigation (real writer
   contract + FK to a 270-row live table — genuine not-yet-populated concept, not a
   fabrication), and `mimamsa_insight_embeddings`'s explicit refusal of the native's blanket
   "embeddings = SERVED-VIA(vector_search)" pre-ruling (confirmed `vector_search` only reaches
   `query_classical_texts`) in favor of a genuinely new, non-fabricated (no live
   text-embedding-at-query-time call exists anywhere in this codebase) two-mode serving path.
5. **Disposition-table update (the task's explicit per-item deliverable):**
   `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §11 (new) — all 36 rows flipped SERVE-gap→SERVED-DIRECT
   with file:line citation to the real `FROM <table>` query line in each capability, per-batch
   breakdown, and the 4 fixes above documented inline. Also corrected 4 pre-existing stale
   rows (`bodha_cdlm_domain_rollups`/`_evolution_gradients`/`_pattern_clusters`,
   `bodha_cgm_sub_graphs`) still reading "SERVE gap" in §6 despite the prior lane's own §10
   addendum already documenting them as wired — a documentation bug from an earlier pass, not
   introduced here, fixed while touching this same file. `DARK_SET_WIRING_PLAN_v1_0.md` also
   updated with a short W2b wiring-log pointer for the two RM/triangulation rows it names
   directly.

**Batch completion — exact counts, honestly reported:**

| Batch | Items | Wired | Notes |
|---|---:|---:|---|
| 1 — L0 `bg_*` mechanical reference tables | 17 | **17/17** | All follow the proven `query_sign_medical.ts` pattern exactly. |
| 2 — borderline `brahma_*` constants/config | 5 | **5/5** | Includes the `coverage_matrix.ts` drift-bug fix for `brahma_compendium_index`. |
| 3 — substantive L1/L2 items | 8 | **8/8** | Task brief said "7 items" but named 8 (`ga_condition_composite`, `ga_prashna_lagna`, `bodha_triangulation`, `bodha_rm_chart_summary`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`, `chart_panchanga_cache`) — all 8 named items wired. |
| 4 — L5 Mīmāṃsā research/explainability | 6 | **6/6** | GATED calibration-overlay siblings correctly left untouched. |
| **Total** | **36** | **36/36** | Zero items left open. |

**Nothing left open from this list.** Every one of the 36 items named in the task brief has a
real `CapabilityDescriptor`, a real test file, and a real disposition-table row flip with a
file:line citation.

**must_not_touch compliance:** grepped `git status` for any `kala_*`/`L3_kala`/`gochara` path —
zero hits; the only near-miss is `bg_transit_av_gates`'s own doc-comment explicitly disclaiming
any edit to `kala_gochara_windows`/`register_gochara_windows.ts`/`query_temporal_activation.ts`,
which were read (pre-existing, by the file that wrote this doc-comment) but not modified by
this lane. No FROZEN orchestrator/`WriterBase` code touched. No `chart_facts` semantics
touched. No LEL content touched. No breaking-release action — every item is a strictly
additive new capability, registered alongside (never replacing) existing ones; no alias
deletion, no bootstrap cutover, no flag flipped on. Zero `kala_*`/Gochara defects were
discovered this lane (the one governance anomaly found and left alone,
`bg_transit_vedha`'s missing migration DDL, is L0, not `kala_*` — no entry needed in
`DOCTRINE_LEDGER_HANDOFF.md`; none created this lane as there was nothing to record there).

**Verification run this lane (all real, all re-run after the 2 bugfixes above, not just
before):**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors (was ~30 errors before the
  `*/`-comment fix, 2 more before the `cost_class` fix).
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors.
- `npx eslint` on every new/touched `.ts` file this lane authored or fixed — 0 errors (4
  pre-existing `_ctx`-unused warnings surfaced in 4 `L1_ganita/get_*.ts` files this lane never
  touched — a concurrent session's work already in this shared worktree, left exactly as
  found, consistent with this campaign's established "pre-existing, not-mine" precedent).
- `npx vitest run src/lib/retrieval/registry` (platform) — **890 passed / 125 skipped, 0
  failed** (includes all 36 new capabilities' test files + this lane's new
  `call_panchanga_service.test.ts`, 9/9 passing on its own).
- `npx vitest run` full `platform` suite — **6172 passed / 317 skipped / 1 todo, 0 failed**
  (542 files) — no regression anywhere in the estate from adding 36 new registered
  capabilities across 4 layers.
- `platform-mcp`: `npx tsc --noEmit` clean; `npx vitest run` — 75 failing / 528 passing (18
  failed files) — confirmed pre-existing and unrelated: zero `platform-mcp` files were
  touched by this lane (`git status -- platform-mcp` returns empty), and this exact
  75-failing/528-passing baseline is the same one the W2 descriptor-migration lane already
  investigated and attributed to an untouched sibling worktree, not this campaign's changes.

**Files touched/created this lane (beyond the ~36×2 capability+test files + 4 `index.ts`
registrations already on disk at lane-open):**
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/call_panchanga_service.ts`
  (bugfixed: comment reworded, `cost_class` corrected).
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts`
  (bugfixed: `cost_class` corrected).
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/call_panchanga_service.test.ts`
  (new, 9 tests).
- `00_ARCHITECTURE/briefs/retrieval_impl/TABLE_CONCEPT_DISPOSITIONS_v2_0.md` (modified — 36
  row flips + 4 stale-row corrections + new §11).
- `00_ARCHITECTURE/briefs/retrieval_impl/DARK_SET_WIRING_PLAN_v1_0.md` (modified — W2b wiring
  log pointer).

**Not committed** — left staged/unstaged per this session's instructions, per this campaign's
explicit "do not run git commit" constraint.

### W2 phase 2 — Lane: Structural closes G-1/S-3/SC-2..5 (2026-07-20)

All 5 items closed serving-side, zero required writer work (one genuine writer-gap residual
found — natal `speed_dps` missing from `chart_facts` — specced not built, see
`STRUCTURAL_CLOSES_W2.md`). G-1 (CGM bhava edge-orphans) was already resolved by an earlier
wave, register row stale. S-3 (`bhava_arudha`) and SC-3/4/5 (parivartana clarity,
ashtakavarga refinements, karaka/nakshatra cross-ayanamsha) were genuine serving gaps — real
computed data with no route — fixed by adding categories to `get_karakas.ts`/
`get_ashtakavarga.ts`/`get_dispositors.ts`/`get_positions.ts`, plus a narrow, scoped
`coverage_matrix.ts` addition (11 newly-served categories only — not the full 158-vs-218
reconciliation, which stays W1's separate deliverable). Incidental finding, flagged not fixed
(writer-side, out of scope): a self-pairing `Jupiter↔Jupiter` parivartana data-quality bug.
Verified: `tsc --noEmit` clean both packages, full platform suite 5939/0 failed (later
superseded by the dark-set batch lane's final 6172/0 failed after its own additions).

**Note on this lane's own report:** flagged an apparent branch-HEAD-advance / file-revert
event mid-session in this shared worktree. Investigated by the conductor post-hoc: `git log`
shows HEAD unchanged throughout (`756365a0`, matching the worktree's creation point) and the
final diff is confirmed stable and correct — most likely a sibling lane's concurrent edit to
an overlapping file was misread as a HEAD change, not an actual git-history rewrite. No data
loss occurred either way (the lane's own re-apply-and-reverify discipline caught it).

### W2 phase 2 — Lane: catalog.ts completeness fix — disclosure note (2026-07-20)

The single-bootstrap lane's `catalog.ts` fix (unconditional calls to
`registerRouterCapabilities()`/`registerMaroCapabilities()`/`registerD6SynergyCapabilities()`,
closing the real GT-40 divergence plus a newly-found 7th item) is **not itself flag-gated** —
only the *route.ts bootstrap-source* behavior (single-catalog vs dual-list) is behind
`RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` (default off). `catalog.ts` is side-effect-imported
unconditionally by the live `/api/mcp/primitives/[tool]/route.ts`. The W2 phase-2 verifier
independently confirmed none of the 6 newly-visible capabilities are in that route's dispatch
whitelist (`tool_name_bridge.ts`), so no existing dispatch behavior changes — the full test
suite shows 0 regressions. Judged non-breaking (additive registry-introspection visibility
only, not a new dispatch path) and approved to ship in this non-breaking phase; flagged here
for explicit visibility rather than left as a footnote in a sub-agent's own report, per the
verifier's request.

### W2 PHASE 2 CLOSE (2026-07-20)

Merged: PR #647 (`impl/wave-2b` → `main`, merge commit `d331f253`), all CI checks green
(large 102-file diff — Build Check/Governance Gates/Unit Tests each ran 6-9 minutes).
Deploy (run `29732946369`): `Build & Deploy Web` success; MCP/Sidecar/Pipeline all correctly
skipped (this phase touched only `platform/src` registry code — confirmed the live dispatch
architecture is `platform-mcp` → HTTP → `platform`'s `/api/retrieval/capability` route, so a
web-only deploy is sufficient; no platform-mcp source was touched, no redeploy needed there).

**Live-verified directly against the deployed capability route** (bypassing the MCP
tool-name layer again, same as W2 phase 1 — this connector doesn't expose most
registry-level capabilities under distinct MCP tool names):
- `marsys://tool/L1/get_condition_composite` (the `ga_condition_composite` wiring) —
  resolved correctly, reached real entitlement enforcement (`entitlement_denied`, honest
  fail-closed denial for the service token's own principal — proves the capability is
  registered and reachable, not a 404).
- `marsys://tool/L0/query_avastha_schemes` — `ok:true`, real classical avastha-scheme rows
  with citations (`JP Ch.7`, `PD Ch.4`), confirming genuine live serving, not a stub.
- Negative control: a nonexistent URI correctly returns a distinct `"Unknown capability URI"`
  error shape — confirms the two hits above are real resolutions, not a catch-all.

**W2 (both phases): CLOSED.** Disposition table: **SERVED-DIRECT 55 / SERVE-gap 0** — every
concept this campaign's harvest found now has a terminal, evidenced disposition. Full W2-close
checkpoint (the two §F pre-rulings that didn't survive verification, live-probe diff vs the W0
baseline) reported to the native separately; not duplicated here.

**Remaining, explicitly deferred per the native's §F-gate-ruling sequencing:** the breaking
alias cutover and the single-bootstrap flag flip-on stay off until the native confirms D-5 is
quiet. No further W2 work is planned beyond that switch-over — W3 (One Envelope) is next,
pending native go-ahead.

## Wave log

### W3 — One Envelope (OPENED 2026-07-20, native go-ahead received)

**Doc-sync precondition (closed before W3 opened):** the master brief (v2.0) and plan v1.8 had
been advancing only in a worktree reference copy — `main` was stuck at plan v1.4 and never had
the brief committed at all, a gap this ledger's W1-close entry already flagged and left
unactioned. Landed via PR #649 (`impl/wave-3` → `main`, merge commit `002c4eb6`), CI green
14/14, docs-only, no deploy required.

**Coexistence check re-run at open:** D-5 is **NOT quiet** — two fix PRs opened minutes before
this entry, `#650` (RED-C v4: DB-driven interval segment consolidation) and `#651` (RED-D: mixed
occupation+aspect double-transit fix for `guru_shani_double_transit`), both currently OPEN and
expected to merge+deploy imminently. **Deploy mutex is NOT claimed this entry** — per brief §I.3
("only one campaign merges-to-main/deploys in any given window") and the native's explicit W3
instruction, no W3 merge-to-main/deploy happens until the native confirms D-5 quiet. Lane work
proceeds in isolated worktrees/branches against `origin/main` and is CI-verified there; nothing
lands on `main` until the mutex is re-checked clean immediately before that specific merge, and
the §B baseline probes are re-snapshotted at that point per the coexistence rule (whichever
campaign deploys last before the diff invalidates the older snapshot).

**must_not_touch reaffirmed for this wave:** `kala_*` serving semantics stay frozen-as-found
(brief §I.5, restated by the native for W3) — none of the 8 lanes below touch
`platform-mcp/src/tools/*gochara*`, `*kala_*` handler internals, or any D-5-owned file; if a
lane's honest-flags/budget/envelope migration would otherwise touch a `kala_*` handler's
call site, that site is deferred to a named residual, not silently skipped.

**Scope for this wave (brief §E W3 + plan §3 R-2, verbatim acceptance criteria):**
1. v3 universal envelope + `chart_header` fail-loud (plan R-2.1, GT-47) — kills the two silent
   catch→null paths (`envelope.ts`'s `chart_header.ts:90-93` inner swallow; ~5 `chart_header =
   null` sites in `registry_bridge.ts`, more than the plan's "3" — recon found 816/1058/2043/
   2696/2970); `envelope_version` stops lying at `'v1'` under v3.
2. Flags closed enum + d8/hollow-emitter migration (R-2.2, GT-46/GT-53) — `judgment_flags`
   becomes `{code, detail?, severity?}[]`, closed registry-checked enum; folds in
   `register_p1_synthesis.ts:82`/`register_p1_reference.ts:87`'s static `[]` emitters and
   `finalizeMcpBudget`'s injected budget-overflow string.
3. Register block + `reading_contract` + `signal_reader_text` editorial pass (R-2.3 / C-3) —
   greenfield: no `register` field exists on `CapabilityDescriptor` today (`types.ts:207` has
   only `density_contract`); draft reader text generated per signal class, flagged for native
   polish post-campaign per the brief's own C-3 framing.
4. Cursor fingerprints (R-2.4) — greenfield: `PaginationBlock.next_cursor` is a bare
   `string | null` today, no filter/sort fingerprint, no `cursor_filter_mismatch` flag.
5. Budget unification (R-2.5, GT-45/GT-48) — the ~36-of-~115-tools unclamped surface across 15
   registration files migrates onto `finalizeMcpBudget`; `still_over_budget` wired into the
   closed enum or deleted (not merely surfaced); `result_clipper.ts`'s live caller
   (`adapters/bulk_context/bundler.ts:10`, confirmed not orphaned) is preserved — evicted from
   the MCP/retrieval-envelope path only, not deleted.
6. `density_contract` to 100% (from today's 6-of-≈118, ~5%) + `verbosity: concise|detailed`
   request knob, guarded per C-4 (never lets a hard-floor confirmed-finding section collapse).
7. `demand_ranking` + timing hooks + prediction shape (plan §8 R-2 rows) — greenfield field,
   does not exist anywhere in `types.ts`/`platform/src/lib/retrieval` today.
8. Response cache, envelope half (W-28) — `ledger_version` added additive-only to envelope +
   pin (does not exist today); cache-safe determinism (byte-stable output per `build_id`).

**Verifier gate V3 (plan §3 R-2 gate + brief §E V3):** schema validation over live `tools/call`
output for the full codegen-derived census; W4-style rubric battery re-run, no answer-quality
regression; §N.6 density-layering checks; a trim-honesty adversarial pass. Live-probe diff
against the W0 baseline (re-snapshotted per the coexistence rule above) is the native's
requested comparable — same probe suite, before/after envelope shape.

**Lane plan (parallel where files don't collide; conductor = this session):**

| Lane | Scope | Isolation | Model/effort |
|---|---|---|---|
| W3-L1 | v3 + chart_header fail-loud | worktree `impl/w3-envelope` | sonnet-class, high |
| W3-L2 | flags closed enum + d8/hollow-emitter migration | worktree `impl/w3-flags` | sonnet-class, high |
| W3-L3 | register block + reading_contract + signal_reader_text | worktree `impl/w3-register` | fable/opus, high (design-heavy) |
| W3-L4 | cursor fingerprints | worktree `impl/w3-cursor` | sonnet-class, high |
| W3-L5 | budget unification (~36 unclamped tools) | worktree `impl/w3-budget` | sonnet-class, high |
| W3-L6 | density_contract 100% + verbosity knob (C-4 guard) | worktree `impl/w3-density` | sonnet-class, high |
| W3-L7 | demand_ranking + timing + prediction shape | worktree `impl/w3-demand` | fable/opus, high (design-heavy) |
| W3-L8 | response cache envelope half (ledger_version) | worktree `impl/w3-cache` | sonnet-class, high |

Lanes 1/2/4/5/6/8 all touch `envelope.ts`/`types.ts`/`response_budget.ts` and will be
integrated sequentially into `impl/wave-3` (conductor-resolved merges) rather than merged
independently in parallel, per brief §D's "sequential only where a shared file forces it" —
they are *implemented* in parallel worktrees but *merged* in dependency order: L1 (envelope
shape) → L2 (flags) → L4 (cursor) → L5 (budget) → L6 (density/verbosity) → L8 (cache/ledger),
with L3 and L7 (mostly additive/greenfield, lower collision risk) integrated last against the
merged base. Each lane ships with tests; the wave verifier is independent of every lane's
implementer per brief §D.

### W3 — Lane implementation + integration (2026-07-20)

**All 8 lanes implemented independently in isolated worktrees, each opened its own PR
against `main` (none merged individually, per plan):** L1 envelope+chart_header (#657),
L2 flags closed enum (#659), L3 register/reading_contract/signal_reader_text (#654), L4
cursor fingerprints (#653), L5 budget unification (#660 — one stall+respawn cycle, see
below), L6 density_contract+verbosity (#658), L7 demand_ranking+timing+prediction (#655),
L8 ledger_version+cache determinism (#656).

**Failure-discipline record (brief §D "a stalled agent is respawned once with narrowed
scope"):** L5's first attempt stalled (no progress 600s) mid-test-run; the respawn found
substantial uncommitted, largely-correct work, rebased it onto `origin/main` (which had
advanced to D-5's RED-C v4 merge mid-wave — confirmed zero unintended diff on the
kala_*/gochara files this introduced), verified, and shipped it as #660. A separate
"integrator" agent (opus, tasked with merging all 8 lanes) also stalled at 600s mid-merge,
having cleanly landed lanes 1-2 and left one unresolved conflict; the conductor completed
the remaining merges directly (7 more merge commits, 4 real conflicts requiring judgment —
all "both sides are legitimate additive changes, keep both" — plus the recurring
`generated/envelope.ts` mechanical-mirror conflict resolved by later regeneration, never
by hand-picking a side).

**One real architectural defect found and fixed during integration, not by any single
lane:** L3's `register_block.ts` cross-imported `EpistemicGrade`/`DrillPointerType`/
`PactStage` FROM `envelope.ts` — harmless in isolation, but the moment `envelope.ts`
itself imported back from `register_block.ts` (to call `buildRegisterBlock` etc.), the
codegen script's hard zero-import process-boundary guard (design §19 — `envelope.ts` must
stay self-contained because `platform-mcp` cannot `import` across the process boundary)
halted. Fixed by inlining `register_block.ts`'s content directly into `envelope.ts`
(the exact fix pattern L4's cursor lane had already used for its own hash function,
independently, for the same reason) and turning `register_block.ts` into a thin
re-export shim so its 3 existing consumers needed no changes. Two smaller regressions
from the conductor's own merge-conflict resolutions were caught by the test suite and
fixed in the same pass (mismatched budget-flag detail wording; a pre-L2 test still
assuming the bare-string judgment_flags shape).

**Verification before opening the wave PR:** `platform` + `platform-mcp` both
`tsc --noEmit` clean. `platform/src/lib/retrieval` full suite: 1327/1327 passed, 0
regressions. `platform-mcp` full suite: 75 failed/550 passed — confirmed **byte-identical**
against a fresh detached `origin/main` checkout (75/528 there) — zero regressions
introduced by W3. `codegen:envelope --check` clean (regenerated fresh from the fully
merged source, twice, after the register_block fix). `codegen:registry-shims` still halts
on `getStrengthCapability.input_schema` — confirmed pre-existing on `origin/main`,
unrelated to W3 (three independent lanes verified this before the conductor did a fourth
time).

**kala_*/gochara zero-diff check:** clean except one file, flagged explicitly rather than
decided silently — `platform-mcp/src/tools/retrieval/kala_temporal.ts` gained a
`budgetMcpContent()` wire-wrapper from lane 5's unclamped-tool migration (byte-clamp only,
zero change to computed/served data or shape — the same generic plane-infrastructure
change every other tool in that lane received). Lane 6 separately left
`L3_kala/query_projections` on the generic `density_contract` default rather than the
measured 55KB override `registry_bridge.ts` already carries for it, out of the same
caution. Both need an explicit native ruling, not a conductor decision, per the kala
freeze's spirit.

**D-5 coexistence, live during this wave:** D-5 deployed twice while lanes were in
flight — RED-C v4 (#650, merged 12:14) mid-lane-dispatch, RED-D (#651, merged 13:09)
during integration. Neither PR was open when `impl/wave-3` was opened (both merged); the
branch was rebased onto `origin/main` after each to stay current (zero conflicts both
times — D-5's changes are entirely within `platform/python-sidecar/services/
{ka_gochara_sweep,gochara_grammar,gochara_intensity}/` and one migration, none of which
any W3 lane touches). **`impl/wave-3` (PR #661) is opened but explicitly held unmerged**
— per the native's own W3 kickoff instruction, the wave does not merge/deploy until the
native confirms D-5 is quiet, even though the mutex reads clear (no open D-5 PR) at the
moment this entry is written; a `worktree-wave+D-5+conductor` branch is still live,
suggesting D-5's own conductor session may still be re-running its §G gate against the
RED-C/RED-D fixes.

### W3 CLOSE (2026-07-20)

Native go-ahead received (D-5 confirmed quiet: RED-C #650 and RED-D #651 both merged,
mutex read clear; the two flagged kala-adjacent touches ruled acceptable — see §I.5 note
in `STATE_D-5.md`, PR #662). Merged: PR #661 (`impl/wave-3` → `main`, merge commit
`7f0ff1a0`), all 15 CI checks green. Deploy (triggered automatically on push): `Build &
Deploy Web` + `Build & Deploy MCP` both succeeded; `Sidecar`/`Pipeline Job Image`
correctly skipped (W3 touched zero python-sidecar files). Full live-verification record:
`VERIFY_W3.md` — every named W3 deliverable (v3 envelope honesty, closed flag enum,
register/reading_contract/signal_reader_text, cursor fingerprints, budget unification,
density_contract, demand_ranking, ledger_version) confirmed on the deployed connector via
a genuine before/after diff on `judgment_query(domain=wealth, response_format=v3)`, chart
482012f1 — not inferred from source or unit tests alone. The native's specifically
requested CGM convergence probe (`get_cgm_subgraph(mode=convergence)`) came back
byte-identical before/after, which is itself an honest finding: that capability has no
`response_format` param and cannot reach v3 today, and its `limit` request has no live
effect (the real control, `top_k_hubs`, isn't exposed on this tool's MCP schema) —
recorded as a residual, not silently substituted.

**W3: CLOSED, V3 ACCEPT.** Residuals carried forward (full list in `VERIFY_W3.md` §7):
`register_p1_ganita.ts`'s two unfixed silent chart_header sites; the session-pin
`judgment_flags` subsystem outside L2's scope; `L3_kala/query_projections`'s generic
density_contract default (native-approved to stay deferred pending the kala freeze
lifting); no full 162-capability live sweep was performed (CI suite is the broad-surface
evidence); no live `verbosity:concise` probe was run; `get_cgm_subgraph`'s v3/`limit` gap
named for a future wave. **Alias cutover + bootstrap flag-flip remain parked** — the
native's go-ahead for W3 explicitly did not extend to those W2-parked items. W4 (One
Planner) is next, pending native go-ahead.

### Cross-campaign note — PG-2 merged to main (2026-07-20)

For the W4 conductor, from the PG-2 diagnostic wave (separate campaign; `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_PG2_DIAGNOSTIC_v1_0.md`):

1. **Main has moved.** PR #620 (PG-2) merged at `5b57d49f`, bringing in: `SESSION_LOG.md`
   additions (RETRIEVAL-AUDIT-CLOSE, PG-2's own entry, D-5-HALT/D-5-CLOSE, in
   chronological order), `CURRENT_STATE_v1_0.md` §2 pointer updates, and corrections to
   `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` (→ v0.7) and
   `00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md`. **Sync the W4 wave
   branch with `origin/main` at the next natural checkpoint, before the gate merge** —
   PG-2's own branch sat unsynced long enough that its PR briefly lost the ability to even
   attach a GitHub Actions check-suite (a real, reproduced failure mode, not theoretical);
   worth avoiding on a wave this central.

2. **Cross-campaign defect assigned to W4:** `platform/src/lib/bundle/bundle_hydrator.ts:25`
   hardcodes `FLOOR_ASSET_IDS = ['FORENSIC','CGM']` and throws because `FORENSIC` was
   deleted from `CAPABILITY_MANIFEST.json` in PR #187 (Legacy Teardown) and never removed
   from this list. Live-confirmed (two authenticated invocations against the native's own
   chart, byte-identical, steady-state): `/api/chat/consult` returns a deterministic
   **HTTP 500** at bundle-hydration, before any planning or streaming begins — the same
   failure class as the earlier LCA-2 regression, one layer downstream. **In-scope for W4**
   because a working consult route is a precondition for verifying W4's floor-adoption
   work end-to-end; PG-2 diagnosed but did not fix it (read-only-on-source discipline).
   One-line fix (drop `'FORENSIC'` from the array). Full evidence: `REPORT_PG-2.md`
   ("Both central questions, answered from probes this wave ran", part (b)).

### W4 CLOSE (2026-07-21)

**Precondition first:** the PG-2-assigned `bundle_hydrator.ts` fix merged and deployed
independently (PR #677, `fb793e18`), live-verified against production chart `482012f1`
before any W4 feature work began (first probe hit an unrelated pre-existing planner
non-JSON issue — HTTP 422 — second probe returned a real, chart-grounded HTTP 200
synthesis). C-2 (audience_tier excision) landed as its own PR (#680, `bfe9cf10`) per the
Paripraśna-workstream labeling requirement, ahead of the main wave PR.

**Sequential core** (`impl/wave-4`, merged PR #682 → `a1ed172b`): scope_tuple
classification (web port of the MCP `intent_scope_classifier`) attached to every plan →
a 3-way planner outcome contract (`PlanReceipt | ClarificationRequest |
PlannerFaultResult`, replacing throw-on-non-JSON with one repair-retry then a typed
fault — this ALSO fixed the same 422-leaking-internals bug the precondition probe
surfaced, folded into this lane per native instruction rather than deferred) →
`compileContract` wired into `consult/route.ts`, deleting the hardcoded B.11 floor
injection → completeness receipts + a ≤2000-token orientation front-door, both new on
the web channel. **Honest caveat, carried through to production**: only ~10% of query
classes get a genuinely-compiled floor today (an MCP↔web tool-namespace gap — only 4 of
~23 distinct MCP tool names have a web-executable equivalent); predictive/holistic
classes still run on the pre-W4 hardcoded logic, preserved as explicitly-named,
disclosed guarantee functions, not silently dropped. `channel_note` on every
completeness receipt surfaces this so a small `served` count is never misread as full
floor coverage.

**Parallel lanes** (all merged into the same PR after independent verification): floor
completeness campaign (career/health/marriage floors now carry all 11 §B0.4 mandatory
tags — pure wiring, zero fabricated tool references); CR-55 resolved CLOSED-WITH-RESIDUAL
(live Postgres-verified: Venus is genuinely weakest by shadbala; the serving layer
already overrides a stale `vw_chart_digest` view) plus 2 other stale `cr_status.ts`
entries (CR-54, CR-59) found and fixed in the same spot-check; floor precompilation
cache (W-28, content-hash-keyed, 48-entry warm cache) shipped as a verified, inert
drop-in — not yet wired to a call site; `prashna_ask` headless spike (C-6/F-R1) proved
the boundary via a boundary-mocked integration test on chart `1c826d5a` (honestly not
live E2E — no sandbox DB/API credentials for a bare-function run; the underlying engine
behavior was independently confirmed live via the deployed consult route instead, see
below).

**V4 gate: ACCEPT** (fresh-context holistic reviewer, after every individual lane's own
ACCEPT) — scope-tuple round-trip verified for all 12 classifier intents (zero throws,
zero silent `general_synthesis` collapse — the fallback is a documented, non-empty
floor, not a masked failure), B.11-by-construction confirmed (no hidden hardcoding
survives outside the disclosed guarantee functions), completeness receipts confirmed
wired to real per-tool execution outcomes (not stubbed), full suite green (6378 passed,
0 failed), `tsc`/`codegen:vidhi:check` clean, kala/gochara semantics confirmed untouched
by diff.

**Live-probe re-verification against the deployed connector, post-merge (`a1ed172b`),
chart `1c826d5a`:**
- The exact question that reproducibly 422'd 3/3 times pre-merge (a Jupiter-placement
  question with no clear domain intent) now returns a clean HTTP 200 with a proper
  `data-clarification` SSE event — the C-5 ClarificationRequest outcome, working live in
  production for the first time.
- A career-assessment question returned a full HTTP 200 synthesis (~51s wall):
  `data-orientation` fired early (790/2000 tokens, unenforced/no trims needed,
  `weakest_graha: "Jupiter"` explicitly citing "CR-55 fix" in its own payload — live
  proof that resolution is deployed and being served); `data-completeness` fired at
  stream end, honestly reporting the floor as mostly `empty` with `web_namespace_gap`
  reasons (career floor grew from the completeness campaign, and the namespace gap
  applies to essentially all of the new items — truthfully surfaced, not hidden).
  4 tool calls made (well within the ≤10-umbrella-call target); stage timings:
  classify 4.6s, compose_bundle 0.05s, tool_fetch 6.1s, synthesis 38.7s.
- **New finding, recorded not fixed (CR-118 updated):** of the 4 tools called, 3 errored
  in single-digit milliseconds (`msr_sql`, `get_yoga_firings`, `cgm_graph_walk`) while
  `vector_search` succeeded normally (6065ms, real data). This widens CR-118 beyond
  `msr_sql` alone — notably 2 of the 3 fast-failing tools are floor-adoption's own
  web-bridge mappings, so this defect currently further limits how much of the compiled
  floor can serve data. Did not block the response (graceful degradation held). Still
  out of W4 scope per the native's standing ruling; deferred to W5/PF-1.
- No regression observed relative to the W0/W3 baseline probes on the dimensions
  re-checked (envelope shape, chart_header presence, orientation/digest content).

**W4: CLOSED, V4 ACCEPT.** Parked, not flipped by this wave: alias cutover and the
single-bootstrap flag — both queue for the front of W5, pending the native's explicit
D-5-quiet confirmation (same standing instruction carried from W3). CR-118 (tool
fast-fail pattern, widened) and the MCP↔web namespace gap (floor-adoption coverage) are
the two carried, named residuals for W5/PF-1. W5 (Adaptive Serving + Scale) is next,
not opened by this session.

## W5 OPEN (2026-07-21) — Adaptive Serving + Scale

**Scope amendments from the native, ratifying/redirecting the W5 standing scope (brief
§E W5) before lane dispatch:**

1. **MCP↔web namespace bridge is W5's first-class core item, not a side lane.** The web
   channel's hand-made tool bridge becomes a *generated projection of the compiled
   catalog*, the same way every other served surface is generated — this is the
   mechanism that takes floor adoption from ~10% (career-only, measured at W4 close) to
   100% across all families. CR-118's fast-fail mappings and the `msr_sql` defect are
   fixed *by regenerating the bridge*, not by hand-patching the existing hand-made one —
   a hand-patch would be scoped-in-place work this wave explicitly supersedes.
2. **D-5 alias cutover + single-bootstrap flag-flip are UNPARKED**, confirmed quiet
   (`STATE_D-5.md` lifecycle_step 8 — CLOSE + CLEANUP, gate_run_3 GREEN-WITH-PARTIALS,
   `current_wave` advances to D-4b), and run FIRST in this wave as the breaking-release
   window.
3. **Verdict-first streaming joins W5's UX scope.** W4's close measurement (above) makes
   this concrete: synthesis (38.7s) is effectively the whole perceived-latency budget.
   Stream the verdict/orientation layer (brief §9.7) while synthesis completes, and
   redefine the time-to-first-verdict SLO as a stage-timing metric (target TBD from the
   §9.7 pressure-point baselines) fit to the single-request web architecture — the plan's
   original ≤3-calls-to-first-verdict framing doesn't map onto this architecture (also
   noted at W4 close).

**Coexistence check (brief §I, at wave open) — RE-RUN, result differs from the D-5
assumption baked into amendment 2 above:**

- `STATE_D-5.md`: D-5 lifecycle_step 8, CLOSE + CLEANUP, gate_run_3 (final,
  native-authorized re-run) GREEN-WITH-PARTIALS. **D-5 itself is quiet — confirmed.**
- **D-4b is NOT quiet — it is actively executing.** Evidence, this session: a live
  `wave/pre-D-4b-readiness` branch; 4 gochara-perf branches (`fix/gochara-kakshya-vedha-
  perf-cache`, `fix/gochara-perm-perf-cache`, `fix/gochara-skip-redundant-savepoint`,
  `fix/gochara-sweep-writer-timeout-budget`) plus `feat/gochara-sweep-priority-ordering`
  already merged to main (PR #681, `1b835b5d`, "B-1-usefulness priority ordering for
  sweep dispatch — native directive"); two live `worktree-agent-*` branches (other
  concurrent sessions currently active against this same repo); two **uncommitted**
  working-tree files consistent with in-flight D-4b readiness work —
  `platform/supabase/migrations/462_writer_timeout_ka_gochara_sweep.sql` (raises
  `ka_gochara_sweep` writer_timeout_seconds 1800→21600, evidenced against 11 failed
  production dispatch attempts) and
  `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`.
  `BRIEF_D4B.md` itself is still a v0.1 SKELETON ("Do NOT bind or execute from this
  skeleton") — the readiness/perf work is running ahead of the formal brief binding.
  Neither uncommitted file belongs to this campaign; left untouched.
- **Mutex disposition (per the standing W3/D-5 precedent — only one campaign
  merges-to-main/deploys in a given window):** mutex is **NOT claimed** by W5 this
  entry. W5 work proceeds in isolated worktrees against `origin/main`, CI-verified
  there; no W5 branch merges to `main` — and in particular, amendment 2's breaking-
  release deploy (alias cutover + bootstrap flag-flip) does **not** fire — until the
  mutex is re-checked clean immediately before that specific merge. Given D-4b's
  currently-active branches all sit under `platform/python-sidecar/services/
  {ka_gochara_sweep,...}` + one migration (the same disjoint footprint W3 already
  verified against D-5), W5's own lanes (platform/platform-mcp, non-gochara migrations)
  are not expected to conflict on merge — but the *deploy window* itself is still
  serialized per the mutex rule, so W5 merges queue behind whatever D-4b has in flight
  at merge time.
- **Probe baseline:** re-snapshotted now (pre-W5) per amendment 2's instruction, before
  any W5 work lands, and will be re-snapshotted again immediately after the D-5
  unpark deploy and again at W5 close, so each deploy's before/after diff is a genuine
  comparable rather than one stale baseline stretched across multiple releases.

**Scope declaration for this wave:**

- **may_touch:** `platform/**`, `platform-mcp/**` (incl. new generated-bridge codegen
  for the web channel), `platform/supabase/migrations/**` (surgical only, §N.4,
  non-`ka_gochara_sweep`/non-D-4b tables), `00_ARCHITECTURE/RETRIEVAL_*.md`,
  `00_ARCHITECTURE/briefs/retrieval_impl/**`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`,
  git branches/worktrees `impl/w5-<lane>` → `impl/wave-5` → `main`.
- **must_not_touch:** everything under the standing must_not_touch (brief scope, restated
  at every wave: FROZEN orchestrator/WriterBase contract + all layer writer build logic;
  root `CLAUDECODE_BRIEF.md` + doctrine-wave briefs/ledgers, read-only; `chart_facts`
  semantics/LEL content; Paripraśna UI/streaming internals beyond the §9.7 verdict-first
  seam named in amendment 3) — **plus, for this wave specifically: any
  `platform/python-sidecar/services/{ka_gochara_sweep,gochara_grammar,
  gochara_intensity}/` file, migration 462, and any `wave/pre-D-4b-readiness` /
  `worktree-agent-*` / `fix|feat/gochara-*` branch** — all D-4b-owned while that wave is
  active.

### W5 — Lane L0: D-5 unpark (2026-07-21)

Flipped `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` default to `true` in `feature_flags.ts` —
the breaking-release alias cutover, parked since W2 pending D-5 quiet. Re-verified the
`catalog.ts`/`route.ts` bootstrap divergence (GT-40's 6 forward + 1 reverse items, plus
the 7th `marsys://tool/router/route` silent-no-op found during W2) is still zero beyond
the one accepted deliberate reverse item (`marsys://tool/synthesis/compose_large_n`) —
neither file had moved since W2's fix landed. Legacy dual-list path remains fully
reachable via explicit `MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=false` override,
proven by an updated `single_bootstrap_flag.test.ts`. The "list_changed" question in the
plan item's "55+6, one breaking release, list_changed" description resolved to **not
applicable**: the MCP tool surface exposed to clients is governed by a separate static
whitelist (`tool_name_bridge.ts`'s `SURGICAL_TOOLS`) and a separate content-hash version
(`capability_version.ts`), neither touched by which bootstrap path `route.ts` uses — no
MCP `list_changed` notification is needed for this cutover.

**Verified:** `platform/src/lib/retrieval` + `platform/src/app/api/retrieval` full
suite 1347/1347 passed, 0 regressions. `tsc --noEmit` clean. One respawn cycle (stalled
600s mid-run, likely the full-suite invocation; resumed with scope narrowed to the
touched paths only — real work was already committed to the worktree, not lost).

Landed on `impl/wave-5` (PR #684, `707fb5a9`) — **held unmerged**, mutex not claimed
(D-4b still active per the coexistence check above).

### W5 — Lane L1: generated MCP↔web tool bridge (2026-07-21)

**Investigation, tracing an actual request** (`consult/route.ts` →
`compileFloorForPlan` → `compiled_floor_adapter.ts` → `getToolByName` →
`tool_name_bridge.ts`): the "hand-made bridge" the brief named is really **three**
separate hand-maintained layers, not one — `tool_name_bridge.ts`'s `TOOL_NAME_TO_URI`
(~89 legacy-name→URI entries, the actual dispatcher for every `plan.tool_calls` entry);
`compiled_floor_adapter.ts`'s `LIVE_TOOL_TO_RETRIEVAL` (only **4 of 23** Vidhi
`live_tool` names mapped — the real ~10%-floor-adoption bottleneck the W4 close named);
and `canonical_faces.json`'s `deprecated_aliases` (D-2 Lane V-3, never chained to the
other two). Confirmed the "23" by counting distinct `live_tool` values in
`registry_data.ts`.

**Root cause of the CR-118/`msr_sql` fast-fail, found live, not previously covered by
any test:** `compiled_floor_adapter.ts`'s B.11 whole-chart-read floor injects literal
registry URIs as `tool_name` (e.g. `marsys://tool/L2/query_signals`), but
`TOOL_NAME_TO_URI`'s keys are names, never URIs — `getToolByName()` silently returned
`undefined`, and `consult/route.ts`'s tool-fetch loop (`if (!t) return null`) dropped
the tool with no error, no trace event. This is why `msr_sql` (and, per the W4 close
finding, 2 of 3 fast-failing tools) never actually executed when injected via the
floor path.

**Built, as a 5th output of the existing W2 projection compiler (not a second,
parallel one):** `web_tool_bridge_builder.ts` chains `getCatalog()` names +
`canonical_faces.json` + the existing hand maps into a new generated artifact,
`web_tool_bridge.generated.json` (emitted by `generate_projections.ts`, extended in
place), consumed via a thin accessor (`generated_web_tool_bridge.ts`). `tool_name_bridge.ts`'s
`resolveToolUri()` now resolves literal `marsys://` URIs directly (the CR-118 fix) and
falls back to the generated bridge for any name outside the hand-curated map — kept as
a documented hybrid rather than deleted outright, since the hand entries encode real
migration history not recoverable from the catalog alone.
`compiled_floor_adapter.ts` gained `resolveLiveTool()` (hand map → generated-bridge
fallback), **raising Vidhi floor-primitive mappability from 4/23 to 11/23 uniformly
across every family** (career/wealth/health/marriage/panoramic/general) — the fix lives
in the shared compiler path, not a career-specific patch.

**Honest residual, not silently closed:** 12 of 23 `live_tool` names remain genuinely
unmapped — no retrieval-registry equivalent exists yet (e.g. `ganita_structural_get`,
`bodha_signals_get`) — recorded per-name in the generated JSON with
`resolution_kind: 'unmapped'`. Closing the remainder needs either new retrieval-registry
capabilities or more curated aliases — named as a W5 follow-up lane, not claimed done.
Also flagged, not fixed: the real MCP-side registration surface turned out to be spread
across `register_p1_*.ts`/`register_p2_*.ts` files, not `platform-mcp/src/tools/
registry_bridge.ts`'s 25 hand-written blocks as initially suspected — worth a look by
whoever owns MCP-side registration count next.

**Verified** (fresh integration onto `impl/wave-5`, re-run after merge, not just
trusted from the worktree report): `tsc --noEmit --skipLibCheck` clean;
`platform/src/lib/pipeline` + `platform/src/lib/retrieval/registry` 980/1105 passed
(125 skipped), 0 failed. The lane's own worktree report additionally verified the full
`platform` suite (563 files/6388 tests passed, 0 failed) against a fresh detached
`main` baseline (562/6379, 0 failed — diff is exactly the new tests) and confirmed
`platform-mcp`'s pre-existing 18-file/75-test failures are byte-identical on `main`,
i.e. not introduced by this lane.

Landed on `impl/wave-5` (commit pending, this entry) — held unmerged alongside L0,
same mutex disposition.

### W5 — Lane L8: listCapabilities filters (2026-07-21)

**Investigation found two catalog-shaped surfaces**, not one: the internal
`CapabilityDescriptor` registry (`getCatalog()`/`listCapabilities()` in
`registry/index.ts`, ~118 entries, already richly filterable via
`CapabilityFilter` — `type`/`layer`/`name_prefix`/`scope`/`archetype`/
`traversal_level`/`tool_role` — but with no MCP-exposed serving path, consumed
only internally by adapters/router/eval harness) vs. the `asset_registry` DB
table (~92-row build-asset DAG) served via 5 near-identical MCP tools
(`list_assets`, `catalog_assets_list`, `catalog_assets_all`,
`catalog_assets_l0`, `asset_registry_l0`) — **the only listCapabilities-shaped
surface actually reachable by an end user today**, previously filterable only
by `layer`. Judgment call: extended the reachable DB-backed surface rather
than building a new tool around the already-filterable internal registry.

Added `asset_type` (data|service), `catalog_status` (CURRENT|DRAFT), `scope`
(global|per_chart), `is_active`, `has_writer` filters (AND-combined with the
existing `layer` filter) to `asset_registry_all.ts`/`asset_registry_l0.ts`,
wired through `registry_bridge.ts` (`list_assets`) and
`register_p1_aliases.ts` (`catalog_assets_list`/`all`/`l0`). Also fixed a gap
where `asset_type`/`catalog_status`/`has_writer` were DB columns never
selected into the response — filtering on them is now verifiable, not silently
accepted-and-ignored.

**Verified:** 12 new tests (each filter dimension + a combined 6-filter case +
a no-filter backward-compat case), `R-18 param no-op audit` PASS (confirms
params genuinely wired, not dropped). `tsc --noEmit` clean both packages.
`platform/src/lib/retrieval/registry` 931/1056 passed (125 skipped), 0 failed.
`platform-mcp`'s pre-existing 75-failed/555-passed baseline confirmed
unchanged via stash comparison (not introduced by this lane).

**Residual, named not built:** the internal `listCapabilities()`/
`CapabilityFilter` surface was left untouched — already filterable, but has
no end-user serving path; exposing the full ~118-entry `CapabilityDescriptor`
catalog (vs. the asset_registry DAG) would need a new MCP tool, named as a
follow-up if a future wave wants it.

Landed on `impl/wave-5` (PR #684, `a8bb24e9`) — held unmerged alongside L0/L1,
same mutex disposition.

**L2 (per-family projections) and L3 (annotations + family_overrides) both hit
a transient API connection error mid-run** (not a stall — real work already
committed to each worktree before the drop) and were resumed in place rather
than restarted from scratch, per the standing respawn discipline. L4
(tool-search metadata) still in flight.

### W5 — Lane L3 integration note: real 3-way merge (2026-07-21)

L1 and L3 both independently extended `generate_projections.ts` from the same
pre-L1 base (L3's worktree was dispatched in parallel, before L1 landed on
`impl/wave-5`) — a straight `git apply` conflicted. Resolved via
`git merge-file` 3-way merge against the true common ancestor (commit
`707fb5a9`, the state right after L0 landed), combining both lanes' new
numbered report sections rather than picking one side, then regenerating all
6 projections fresh from the merged source (`npm run codegen:projections`)
rather than trusting either lane's stale `.generated.json` snapshot. Verified
clean after: `tsc --noEmit`, full scoped suite.

**L3: CLOSED.** Landed on `impl/wave-5` (PR #684, `0aee586a`).

### W5 — Lane L4: tool-search metadata (2026-07-21)

**Investigation:** no keyword/free-text index exists anywhere over the
~163-capability catalog — `list_assets` in `registry_bridge.ts` turned out to
be a red herring (it enumerates the unrelated cockpit `asset_registry` table,
not the retrieval registry). `CapabilityDescriptor` already carries everything
a keyword index needs (name, description, `display.short_label`/`one_line`,
layer, archetype, tool_role, projection_tags) — a missing-index gap, not a
metadata-shape gap.

**Built:** `tool_search.ts` (`buildToolSearchIndex`/`searchToolIndex` — pure,
deterministic keyword/substring match over tokenized descriptor fields, scored
name > keyword > description; no fabricated metadata, every field traces to a
real descriptor property). Wired two ways: a 7th generated projection
(`tool_search_index.generated.json`, via the same compiler) for census/CI
visibility, and a live `marsys://tool/L0/tool_search` capability calling the
same functions against the live `getCatalog()` on every request — bridged onto
MCP as a new `tool_search` tool (`registry_bridge.ts`) — zero drift between the
generated snapshot and what's actually served. Scope explicit: exact/substring
keyword match, not fuzzy/semantic search (would need a `vector_search`-style
corpus, named as a follow-up, not silently implied as done).

**Integration required a real 3-way merge across THREE lanes** (L1, L3, L8 had
all already landed touching `generate_projections.ts`/
`projection_compiler_parity.test.ts`/`registry_bridge.ts` from the same
pre-integration base L4 was dispatched from): merged each via `git merge-file`
against the `707fb5a9` common ancestor, combined all three lanes' independent
report sections/describe blocks (never picked one side over another), and
regenerated all 7 projections fresh. One dropped closing brace from the manual
merge (the `family_tool_defs` `writeJson` call) was caught immediately by
esbuild's parse error on the first regen attempt and fixed before proceeding —
recorded here rather than glossed over, since a silent brace-drop would have
been a real, shippable bug.

**Verified:** `tsc --noEmit` clean both packages.
`platform/src/lib/retrieval/registry` + `src/lib/pipeline`: 1022/1147 passed
(125 skipped), 0 failed. `platform-mcp` `m8_e2e_proof` + touched tool suites:
88/95 passed (7 skipped), 0 failed — 2 pre-existing hardcoded tool-count
assertions (57→58, 25→26) updated since `tool_search` is a genuine new
registered tool, not a regression.

**L4: CLOSED.** Landed on `impl/wave-5` (PR #684, `741a836f`).

**Still in flight:** L2 (per-family projections) hit the same transient API
connection error L3 did and was resumed in place. `impl/wave-5` now carries
L0, L1, L3, L4, L8 — five of eleven lanes landed, all held unmerged pending
the D-4b mutex.

### W5 — Lane L2: per-family MCP surface profiles (2026-07-21)

**Scope correction, found by reading the plan directly rather than assuming:**
"family" in the compact/consult profile spec (`RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`
§R-4, `RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` §3.1) means **client/vendor
family** (Claude vs. non-Claude MCP connectors — RC-1/RC-3/OT-10), not the
astrology domain families (career/wealth/health/marriage) L3's
`family_overrides` axis uses — naming overlap only, no actual conflict between
the two lanes.

**Built**, as an 8th projection (`mcp_surface_profiles.generated.json` +
`platform-mcp/src/generated/mcp_surface_profiles.generated.ts` mirror, same
de-mirror precedent as `envelope.ts`/`registry_shims.ts`): **full** (163,
uncapped), **compact** (≤20 per RC-1, ranked by `demand_ranking`, overflow
tools honestly reported via `overflow_tool_names`, never dropped), **consult**
(7 orienting tools). F-R7 (`calibration_context_only`) excluded from all
three. **Real registry gap found and worked around, not silently fixed at
source:** the mechanical L-ORIENT tagging rule was sweeping internal
orchestration meta-tools (`maro_orchestrate`, `synergy_pipeline`, etc. — each
self-documented "not LLM-facing") into the consult set; excluded via an
auditable filter in the builder, flagged for whoever owns
`dprofiles_registration.ts` next.

**OAuth-scope-gated serving:** `platform-mcp/src/lib/mcp_profile.ts` resolves
a profile from the caller's OAuth scope (Bearer/first-party → full; unscoped
or unrecognized OAuth grant → safe-default **consult**) and
`applyProfileGate()` monkeypatches `McpServer.tool()` so every existing
registration call site in `server.ts` is transparently scoped — zero
per-file changes across ~20 registration modules. New `mcp:profile:full/
compact/consult` scopes added to `oauth/authorize.ts`/`oauth/discovery.ts`.

**V5-gate proof — the "consult profile cannot reach raw tools" requirement
the wave's final gate checks — built here, adversarially, not just
structurally:** the consult/full subset invariant is computed by the builder
and re-verified in tests; a direct probe attempts real full-only tool names
under consult and asserts none leak in; the known internal meta-tools are
confirmed absent from every profile, consult least of all.

**Integration required a THIRD 3-way merge cycle** — `generate_projections.ts`
and `projection_compiler_parity.test.ts` had already been independently
extended by L1+L3+L4 from the same pre-integration base L2 was dispatched
from. The mechanical `git merge-file` pass mis-sliced a stray leftover comment
line from the L4 merge and truncated the tool-search describe block in the
test file — caught before committing (not after), fixed directly by hand
rather than trusting the mechanical merge blindly. Also caught a real
cross-lane type gap on the first `tsc` run: L2's builder reuses the
tool-registration function L3 had extended with an `annotations` field, which
the generated TS mirror's `McpSurfaceProfileToolEntry` interface didn't
declare — added as optional, regenerated, re-verified clean.

**Verified:** `tsc --noEmit` clean both packages.
`platform/src/lib/retrieval/registry` + `src/lib/pipeline`: 1029/1154 passed
(125 skipped), 0 failed. `platform-mcp`: `mcp_profile.test.ts` 16/16,
`m8_e2e_proof` 39/39 (4 skipped); full suite 18 failed/75 tests — confirmed
identical to the documented pre-existing baseline (unchanged since L1's
entry), 0 new regressions.

**Residuals, named not built:** `marsys_drill` (the plan's named
compact-profile dispatcher) doesn't exist in the catalog — not fabricated;
`drill_children` already gives overflow tools the same reachability
guarantee. The other four pre-existing projections don't yet apply the F-R7
filter this builder enforces — a future tightening pass. `prashna_ask` (plan:
"MCP-consult = `prashna_ask` + ~5 orienting tools") is W6 scope — consult is
the 7 orienting tools only until then.

**L2: CLOSED.** Landed on `impl/wave-5` (PR #684, `685015ae`).

**Six of eleven lanes now landed** (L0, L1, L2, L3, L4, L8), all held
unmerged pending the D-4b mutex. Remaining: L5 (spine bundles), L6 (funnel
batching/pooling), L7 (QoS/fairness/job queue), L9 (verdict-first streaming),
L10 (battery baselines), then the V5 gate itself.

### W5 — Lanes L7, L9, L10 (2026-07-21)

**L7 — QoS priority classes + fairness dispatch queue.** No queueing/
concurrency-limiting mechanism existed anywhere; the only multi-tool dispatch
path (`consult/route.ts`'s `Promise.all` fan-out) was unbounded. Axis
decision, documented in the module's own banner: rejected L2's
mcp_profile (full/compact/consult) axis for QoS priority — plan §9.7 W-30
names the real axis "interactive > background" (request-shape: is a human
waiting synchronously right now), orthogonal to caller entitlement; a
consult-scope OAuth caller can be a live interactive user. Built
`platform/src/lib/retrieval/qos/dispatch_queue.ts`: bounded concurrency, two
priority lanes via weighted round-robin plus a hard anti-starvation
force-promotion bound, per-principal fair-share dequeuing, and a
`QueueSaturatedError` refuse-path (queue/refuse, never thin quality). Wired
into `consult/route.ts` as `priorityClass:'interactive'`, keyed by `user.uid`
— bounds/fair-shares capacity across concurrent requests from different
users, the real contention scenario; single-request behavior unchanged.
`prashna_ask`'s own job-handle contract confirmed W6 scope, not built here —
consistent with L2's own independent conclusion. 10 new tests under
simulated concurrent load. **L7: CLOSED.** PR #684, `ca5d4875`.

**L9 — Verdict-first streaming + time-to-first-verdict SLO.** Investigation
found this partially already existed: `buildChartOrientation` runs
concurrently with the planner/tool-fetch, and `data-orientation` already
fired at stream start. Two real gaps closed: no stage-timing metric measured
*when* it fired; and if `buildChartOrientation` threw, the event was
silently skipped entirely (a genuine coverage gap for that request class,
not hypothetical). Added `first_verdict` stage + `TIME_TO_FIRST_VERDICT_SLO_MS`
(p50 12s / p95 20s, justified against the W4 baseline: ~10.75s pre-synthesis
vs. 38.7s synthesis). `run_adapter_dispatch.ts`'s new
`buildFirstVerdictEmission()` always emits `data-orientation` (a degraded
fallback block when orientation is null, never silently omitted) and a
`data-stage first_verdict` event with real elapsed ms. Merge-resolved cleanly
against L7 (both touched `consult/route.ts`, disjoint regions, zero
conflicts via `git merge-file`). 10 new tests. **L9: CLOSED.** PR #684,
`1aafd72f`.

**L10 — Multi-family battery/baseline harness + concurrency runs.** Extended
the existing `planner_smoke_runner.ts` rubric-battery pattern to the
deterministic W4 router (no LLM credentials needed, CI-safe);
applied `BASELINE_PROBES.md`'s capture-now/diff-later methodology via a
stable-stringify + sha256 fingerprint of the compiled Vidhi contract. Family
list (wealth/career/health/marriage/panoramic/general) confirmed from
`registry_data.ts`'s `VIDHI_INTENT_FLOORS`. Built
`platform/tests/eval/w5_battery/` (30 hand-verified NL queries, 5/family) and
**ran it now**: full 60/60 (30 queries × 2 charts — canonical `482012f1` +
SAFE `1c826d5a`) — 100% routing accuracy sequential and concurrent (N=8),
zero chart-isolation violations (the LCA-17-shaped cross-chart leak check),
zero readback diffs. **Honest finding, quantified per-family for the first
time:** health/marriage floors currently have 0% web-executable primitives —
the MCP↔web namespace gap L1 partially closed (4/23→11/23 uniformly) remains
fully open for those two families specifically. Baseline artifacts:
`W5_BATTERY_BASELINE_v1_0.md` + `w5_battery_baseline_raw.json`, explicitly
naming what's still needed for the true final V5-gate run (re-run after
L5/L6 land, a real staging/prod load test, CI wiring). **L10: CLOSED.**
PR #684, `74eb3528`.

**Nine of eleven lanes now landed** (L0, L1, L2, L3, L4, L7, L8, L9, L10),
all held unmerged pending the D-4b mutex. Remaining: L5 (spine bundles), L6
(funnel batching/pooling), then the final V5 gate re-run against everything
integrated.

### W5 — Lane L6: sidecar/DB capability-dispatch cache (2026-07-21)

**Investigation, all four sub-items of the brief's standing scope line
checked against real evidence, not assumed:**
1. Web consult funnel N+1 — already fine. `consult/route.ts`'s `tool_fetch`
   loop already uses `Promise.all` + a two-tier cache; the W4-close
   `tool_fetch 6.1s` figure for 4 tool calls is the MAX of the four tools'
   latencies (one real 6065ms call, three fast-fails), not their sum —
   proof it's wall-clock-bound by the slowest tool, not serialized.
2. DB pooling — already fine (`db/client.ts` runs a proper shared `pg.Pool`,
   max 10, keepalive, idle eviction, retry-once). Read replica — genuinely
   absent (exhaustive grep), correctly left unbuilt: infra provisioning is
   outside a code-only lane's authority, named as a residual not fabricated
   as unwired dead code.
3. **Sidecar memoization/caps — the real, unaddressed gap.**
   `/api/retrieval/capability/route.ts` (the dispatcher the live
   marsys-jis-direct connector actually uses, proxying every MCP capability
   call including sidecar/DB hits) called `capability.handler(safeArgs)`
   directly with zero caching.

**Built:** `capability_dispatch_cache.ts` — two-tier cache (FIFO-capped
in-process coalescing at 500 entries + shared Redis `mcp-capability`
surface, 60s TTL), opt-in via the pre-existing but previously-unread
`llm_hints.agentic.cacheable` descriptor field. **Real bug caught mid-
implementation:** the entitlement gate resolves `chart_id` from either the
request body or the `X-MCP-Chart-Id` header; a naive cache key from
`safeArgs` alone would collide across two different charts when chart_id
arrives only via header — fixed by folding the header-resolved chart_id
into the cache key, verified as a genuine catch by temporarily reverting
just that fix and confirming the regression test fails (1 call instead of
2) before restoring it.

Merge-resolved against L0 (both touched `capability/route.ts` from the same
pre-integration base, true ancestor `794740e2`) via `git merge-file` — zero
conflicts, auto-merged.

**Verified:** `tsc --noEmit` clean. `src/lib/cache` + `src/app/api/retrieval`:
84/84 + 19/19 passed, 0 failed.

**Residual, named not built:** read-replica provisioning; per-tool query
timeout budgets on individual L0_brahmagyan sidecar handlers (judged
lower-leverage than the central dispatcher fix, and higher shared-file
collision risk with the other concurrent W5 lanes).

**L6: CLOSED.** Landed on `impl/wave-5` (PR #684, `ff99a8ff`).

**Ten of eleven lanes now landed** (L0–L4, L6–L10), all held unmerged
pending the D-4b mutex. Only L5 (spine bundles) remains in flight.

### W5 — Lane L5: spine bundles as post-build materialized views (2026-07-21)

**"Spine bundle" defined verbatim**, found by grep rather than assumed:
`RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §8 item 11 +
`RETRIEVAL_STRATEGY_v1_0.md` §S-5/§5.1 — the pre-joined chain
`bodha_msr_signals` (L2 signal) → `kala_activation` (L3 windows) →
`phala_anchors` (L4 anchors) → `mimamsa_calibration` (L5 calibration), served
per `(chart_id, ayanamsha_id, domain)` as one capability instead of 3–5
manual calls — "only one real cross-layer join exists today
[`bodha_msr_signals`↔`kala_activation`]; the LLM hand-stitches everything
else." Two false leads ruled out and documented: `grounding/*.ts`'s
"grounding spine" (unrelated L1 `chart_facts` resolver) and `bundle/*.ts`'s
"bundle" (W4's static markdown/asset-content bundle, not a cross-layer join).

**Built:** `compute_spine_bundle.ts` (the join, as a composition of 4
existing independently-tested capabilities, not a fifth parallel SQL path —
pure/deterministic, which is what makes byte-consistency provable) +
`materialize.ts` (post-build hook route mirroring the existing `refresh-mv`
pattern, plus a lazy fallback baked into every read for when the hook is
unwired). Storage: migration 463, a plain per-chart table (existing MVs in
this codebase are global/full-refresh, don't fit a per-chart scope) using
the §N.3 delete-then-insert pattern; `migration-guard` reviewed PASS (one
WARN — missing `charts(id)` FK — fixed). New capability
`marsys://tool/L-SPINE/query_spine_bundle` discloses its own `source`
(`materialized`/`fresh_materialized`/`fresh_recomputed_stale`) on every
response — never silently presented as cached. Greenfield mechanism, scoped
down to a single joined table rather than a general-purpose join framework.

**Verified:** 15 new tests (join correctness, byte-consistency between
materialized-then-read and a fresh compute, staleness-triggers-recompute, a
real wall-clock measurement — 5.3× speedup, 16 round-trips/92.0ms fresh vs.
2 round-trips/17.5ms materialized). `tsc --noEmit` clean.
`src/lib/retrieval/spine` + `registry` + `src/app/api/admin`: 1015/1140
passed (125 skipped), 0 failed.

**Residual:** the post-build hook isn't wired to an actual build-completion
caller yet (no webhook/cron infra to attach to beyond the watchdog's polling
cadence) — the lazy fallback makes this non-blocking for correctness.

**L5: CLOSED.** Landed on `impl/wave-5` (PR #684, `641d71d9`).

## ALL ELEVEN LANES LANDED (2026-07-21)

L0–L10 all landed on `impl/wave-5`. Full-integration verification pass run
immediately after: `tsc --noEmit` clean both packages;
`platform` full suite **6526/6844 passed** (317 skipped, 1 todo), 0 failed
after one real cross-lane fix (L0's `single_bootstrap_flag.test.ts` asserted
an exact single-item divergence set that L5's new spine capability
legitimately grew to two — fixed by updating the assertion, not loosening
it, commit `0794ea0b`); `platform-mcp` 18 failed/75 tests, confirmed
identical to the documented pre-existing baseline throughout this wave, 0
new regressions.

### V5 gate — status

Per brief §E V5 ("per-family tools/list conforms in CI; battery scores
recorded as the regression baseline; load test passes the four §9.7
pressure points; consult profile provably cannot reach raw tools"):

1. **Per-family tools/list conformance** — **satisfied, correction to an
   earlier note in this entry:** L2's adversarial test suite
   (`projection_compiler_parity.test.ts` §7 "(g) MCP surface profiles")
   passes as part of the full-suite run above: compact ≤20, full uncapped
   and larger than compact, overflow honestly reported, F-R7 exclusion
   holds. This file is ALREADY a mandatory, dedicated CI gate step — "R-1
   projection compiler parity/completeness gate" in the `Density Census
   (§N.6)` job (`.github/workflows/ci.yml` lines 375–394), wired since
   W2/W3 and confirmed still running (and green) on PR #684. An earlier
   version of this entry incorrectly claimed this wasn't CI-wired; checked
   the actual workflow file rather than assuming, and it is.
2. **Battery scores recorded as the regression baseline** — L10's harness
   re-run against the fully-integrated state (`W5_BATTERY_BASELINE_v1_0.md`
   §8): 60/60 routing accuracy, 0 isolation violations, 0 readback diffs,
   **GATE: PASS**. Real, measured improvement over L10's original
   pre-integration baseline — every family's `avg_mapped_fraction` rose;
   health/marriage went from 0% (completely unreached) to 26.7%/28.6%.
3. **Load test across the four §9.7 pressure points** (W-28 cache hit-rate
   under real traffic, W-29 concurrency capacity, W-30 QoS/backpressure
   under contention, W-31 SLO-per-query-class) — **NOT satisfied by this
   session.** L10's battery concurrency pass exercises correctness/isolation
   of the synchronous in-process compile path, not the full funnel→sidecar→
   DB round trip under genuine concurrent production load. A real
   staging/prod load test requires a deployed connector, which itself
   requires this wave to clear the D-4b mutex and deploy first (see below)
   — named as the standing next step, not silently skipped.
4. **Consult profile provably cannot reach raw tools** — **satisfied.**
   L2's adversarial test (`projection_compiler_parity.test.ts` §7, "CONSULT
   PROFILE PROVABLY CANNOT REACH RAW/FULL-ONLY TOOLS (V5 gate)") verifies
   the structural subset invariant, probes real full-only tool names against
   consult, and confirms known internal meta-tools are absent from every
   profile — passing in the full-suite run above.

**Honest overall V5 disposition (corrected): 3/4 criteria fully closed
(per-family tools/list CI conformance, battery baseline, consult-cannot-
reach-raw), 1/4 open (the genuine four-point load test, which needs a
deployed connector).** This wave does not claim V5 complete —
the remaining work is real, named, and sequenced behind the mutex-gated
deploy, not glossed over.

### Breaking-release split, merge, and live deploy (2026-07-21, native ruling)

Per an explicit native ruling: assessed L0's breaking flip for separability
from the other ten lanes. Found it cleanly separable — route.ts's flag-
branching logic predates this campaign entirely; L0's `route.ts` changes
were comment-only. The entire functional breaking change is one boolean
default in `feature_flags.ts`. Split:

1. Reverted `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED`'s default back to `false`
   ("paused", not abandoned — code-complete, fully tested, one line to
   re-flip) and updated `single_bootstrap_flag.test.ts` to match (both
   directions of the divergence-diff test now explicitly set their own env
   state; added symmetric `query_spine_bundle` present/absent assertions).
   One accepted, documented side effect: L5's `query_spine_bundle` capability
   ships code-complete but dormant until the flip lands.
2. Created `impl/w5-breaking` (held, not merged) via `git revert` of the
   pause commit — a ready-to-reapply flip-forward, one commit.
3. Recorded the new coexistence rule as master brief §I.6 (native-ratified):
   a breaking rename/bootstrap-source cutover must never deploy while
   another campaign's live agent swarm may be calling legacy names on the
   connector — independent of and narrower than the existing §I.3 deploy
   mutex (a clear mutex read doesn't mean no live agents running).
4. Re-checked D-4b's actual state via live evidence (not a stale ledger
   read) immediately before merging: same gochara-perf branches still
   unmerged, dozens of concurrent `worktree-agent-*` sessions — D-4b
   confirmed still actively executing. The additive deploy's file
   footprint (`platform/src`, `platform-mcp/src`,
   `platform/supabase/migrations/463_bodha_spine_bundles.sql`) has zero
   overlap with D-4b's active files, so the §I.3 deploy mutex itself was
   clear — took that window per the native's ruling.
5. Added a cross-campaign note to `CURRENT_STATE_v1_0.md` for the D-4b
   conductor (main has moved; no action needed on their side).
6. Merged PR #684 (`impl/wave-5` → `main`, merge commit `3cea53bd`). All
   required status checks green (TypeScript ×2, Unit Tests, Secret Scan,
   Governance Gates). One CI failure investigated, not ignored: the
   `chat-v2 smoke` gate failed — checked its full run history across every
   branch for the past month-plus (`gh run list --workflow "chat-v2
   smoke"`) and found it has failed identically on every single run since
   2026-06-04, across dozens of unrelated feature branches that clearly
   shipped — a chronically broken, non-required gate (confirmed via branch
   protection API: not in `required_status_checks.contexts`), not a W5
   regression.
7. Deploy to Cloud Run succeeded (`Build & Deploy Web` + `Build & Deploy
   MCP` both green; Sidecar/Pipeline Job Image correctly skipped — this
   wave touched zero python-sidecar files).
8. **Live-verified against the deployed connector**, not just inferred from
   CI: `catalog_assets_list(layer=L0)` — L8's new filter fields
   (`asset_type`/`catalog_status`/`scope`/`is_active`/`has_writer`) present
   in the response's echoed `filters` block; a follow-up call with
   `asset_type=service` genuinely narrowed 28 L0 assets down to the 2 real
   service assets (not just accepted-and-ignored). `query_dasha_periods`
   against the canonical chart (`482012f1`) returned real, correctly-scoped
   dasha rows — no regression on the core chart-data path. Honest
   limitation: this session's own MCP connection was established before
   the redeploy, so brand-new tools this wave added (e.g. `tool_search`)
   aren't reachable through it without a reconnect this session cannot
   perform — verified via existing tools whose underlying handlers changed
   instead, which is still genuine live evidence, just not exhaustive.

### V5 gate — remaining open item

The genuine four-point §9.7 load test (cache hit-rate under real traffic,
concurrency capacity, QoS/backpressure under contention, SLO-per-query-class)
against sustained concurrent production load was NOT run this session — the
live checks above are targeted correctness/liveness probes, not a load test.
**V5 closes CONDITIONALLY**: 3/4 criteria fully closed, the additive deploy
is live and verified, and the one remaining open item (the real load test)
is unblocked now that a connector exists to run it against — it did not
require D-4b to quiet, it requires deliberate load-generation tooling this
session did not build. The breaking piece (`impl/w5-breaking`) remains the
other named residual, genuinely blocked on D-4b quieting per master brief
§I.6 — re-check via the same live-evidence discipline used above (not a
stale ledger read) immediately before un-pausing.

**Next steps for a follow-up session:** (a) build and run a real
load-generation harness against the deployed connector across the four
§9.7 pressure points; (b) periodically re-check D-4b's live state
(`git branch -a` / `gh pr list`, same evidence class used throughout this
close) and un-pause `impl/w5-breaking` the moment it's genuinely quiet.

### W6 — module-placement correction (Tasks 2b/5/6 redesign, 2026-07-22)

**Why:** Tasks 2/2b (`CostCapTracker`/`resolveCostCapsForEntitlement`) and
Task 5 (`filterLeakedCapabilities`) were originally built inside
`platform-mcp/src/lib/` on the assumption that prashna_ask's engine
tool-call loop would run in the MCP server process. Investigation for
Task 4 (the prashna_ask↔engine bridge) found this assumption wrong:
`platform-mcp` and `platform` are separate Cloud Run deployables with no
shared import path; `callPipelinePlanner`/`compileFloorForPlan` (the FROZEN
engine) and the tool-call loop that actually needs cost-cap tracking and
NO-LEAKAGE enforcement all run inside `platform`'s process, driven today by
`/api/chat/consult/route.ts` — never inside `platform-mcp`. A filter or
tracker living only in `platform-mcp` would be advisory, not enforcing:
nothing stops the engine from assembling an unfiltered/unbounded tool set
across the HTTP boundary. Native-ratified: enforcement must live where the
loop actually executes.

**What changed (this session, five parts):**
1. Ported `filterLeakedCapabilities` to `platform/src/lib/pipeline/
   no_leakage_filter.ts`, now importing the REAL `CapabilityDescriptor` type
   and the live registry (`getCapability`/`getCatalog`/`resolveToolUri`)
   directly — same deployable as the registry, no more local structural
   mirror type. Deleted the `platform-mcp` attempt + its test.
2. Ported `CostCapTracker`/`resolveCostCapsForEntitlement`/
   `DEFAULT_COST_CAPS`/`COST_CAP_OVERRIDES_BY_ENTITLEMENT` to
   `platform/src/lib/pipeline/cost_caps.ts`, unchanged logic. Confirmed the
   real platform-side entitlement vocabulary: `authorizeChartAccess.ts`'s
   own `Principal.role` is `'guest' | 'super_admin'` — independently
   declared from `platform-mcp`'s `Principal` but literally identical, and
   it's what `resolveMcpPrincipalRole()` (used by every `/api/mcp/*` route)
   resolves. Deleted the `platform-mcp` attempt + its test.
3. Built `POST /api/mcp/prashna_ask` — the new internal, service-to-service
   route platform-mcp will call to actually run the engine. Auth reuses the
   SAME two-layer pattern every other `/api/mcp/*` route uses
   (`validateServiceToken` shared secret + `X-MCP-User`/`X-MCP-Key-Id`
   resolved-principal headers) — the caller's OIDC bearer token is verified
   by Cloud Run's own IAM gate at the infrastructure layer, not application
   code; `lib/auth/oidc.ts`'s `verifyOidcToken` is a different, currently-
   unused mechanism for a different caller (Cloud Scheduler) and was NOT
   reused here. Engine invocation sequence copies `/api/chat/consult/
   route.ts`'s real sequence exactly. Dispatches tools SEQUENTIALLY (not
   the consult route's `Promise.all`) so `CostCapTracker.checkAndRecordCall()`
   can gate each dispatch and stop cleanly mid-loop with an honest partial
   result (never silently truncated).
4. Retrofitted `/api/chat/consult/route.ts` (the pre-existing Paripraśna/
   consult door) with the same `filterLeakedCapabilities` call, applied to
   its fully-composed `toolsAuthorized` before tool-fetch — this route
   previously applied no such filtering. NO-LEAKAGE is engine-side doctrine,
   not channel-specific — both doors now carry it.
5. Added a LIVE/runtime NO-LEAKAGE canary (`no_leakage_runtime_canary.test.ts`
   + `no_leakage_runtime_canary_consult.test.ts`), distinct from
   `projection_compiler_parity.test.ts`'s static F-R7 codegen check: drives
   the REAL filter against the REAL production catalog through both doors'
   actual tool-authorization sequence for a fixture "compromised planner"
   plan, confirming the real F-R7-flagged `marsys://tool/L5/lel_query`
   never reaches dispatch through either door.

**Narrowed scope note for the next task (the prashna_ask↔platform-mcp
bridge):** with the engine call, NO-LEAKAGE, and cost caps now living in
`platform` behind `/api/mcp/prashna_ask`, `platform-mcp`'s role in the
prashna_ask design narrows to: (a) the job registry (`job_registry.ts`,
already built, Task 1) for async job-handle bookkeeping; (b) one HTTP call
from the MCP tool handler to `POST /api/mcp/prashna_ask` (mirroring
`client.ts`'s existing `callPlatformPrimitive` pattern); (c) relaying
progress notifications back to the MCP caller as the job runs. Building
that bridge (the job-handle wrapper around this session's synchronous
route) is explicitly a LATER task, not started here — this note exists so
that task doesn't have to re-derive the boundary from scratch.

Verification this session: `npx tsc --noEmit` clean (both packages); full
`platform` suite green (583 files / 6553 passed / 317 skipped / 1 todo, 0
failed); `platform-mcp`'s remaining suite unaffected (confirmed via
before/after comparison — same 75 pre-existing, unrelated failures both
before and after the two file deletions).

### W6 — Task 11 (session-semantics rename + diagram fix)

**W-19 (PARIPRASHNA §6.1 diagram fix) — DONE.** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
bumped 0.7 → 0.8 (§20 changelog entry added). §6.1's diagram corrected at
source: the `prashna_ask` box no longer lists the stale `depth` param
(struck by D-15) and the AGENTIC LOOP box now reads "provenance stamp"
instead of "session pin ... pinned for ALL conversations" (struck/
restructured by D-16). This was pre-authorized via AMBIG-4 as a docs-only
task, independent of the broader C-1/F-R4 rulings.

**W-17 (session-semantics rename, GT-F28) — NOT executed, carried to §H
residuals.** Investigated before touching anything: GT-F28 in
`briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md` (line 186) is explicitly
marked **NEEDS-RULING**, and no ratification for it was found anywhere in
`RULINGS_ADOPTED.md` or any wave brief — unlike W-19, which the master
brief marks "(authorized)" and AMBIG-4 confirms in writing. Executing an
unratified rename across ~13 load-bearing files (`session_pin.ts`,
`envelope.ts`, MCP session tools, ledger versioning) this late in the
campaign was judged unjustified blast radius for a cosmetic gain, and the
naming rides on the D-16 restructure the doctrine/Paripraśna workstream
owns — not a call for the retrieval campaign to make unilaterally mid-seal.
**Residual for §H:** internal-only rename (zero behavior/contract/UX
change), needs an explicit native ruling coordinated with the
session-semantics decision before execution; does not block campaign
COMPLETE since no shipped behavior depends on the name.

### W6 — Task 9 (live E2E on the deployed connector)

**Deploy confirmed live and running this wave's code.** PR #691 merged
(`d0e8eb29`); `Build & Deploy Web` + `Build & Deploy MCP` both succeeded;
`amjis-web-01083-kwp` and `amjis-mcp-00448-6sp` both carry
`commit-sha=d0e8eb29204c6fb738c4eddaa16f8b294a34ee3e` — exactly `main`'s
merge commit, confirmed via `gcloud run revisions describe`. The MCP
service's `/health` endpoint reports `"tools":122`, matching the deployed
`server.ts`'s `REGISTERED_TOOL_COUNT = 122` constant exactly (120 base +
D-4b's `mechanism_retrodiction` + this wave's `prashna_ask`/
`prashna_status`) — genuine evidence the new tools registered successfully
in production, not just that CI passed. Auth is confirmed still gated (an
unauthenticated `tools/list` call returns `401 Unauthorized`, not a leak).
Cloud Run boot logs for the new revision are clean, no fatal errors.

**Honest limitation, not silently worked around:** this session's own
`marsys-jis-direct` MCP connection was established before this redeploy
(same class of caveat W5's close hit) — `prashna_ask`/`prashna_status`
don't appear in this session's connected tool list without a reconnect
this session cannot perform, and no valid bearer credential for the
deployed connector is accessible in this environment (checked local `.env`
files and CI secrets — `TAP_MCP_SERVER_URL`/`TAP_MCP_SMOKE_BEARER_TOKEN`
are both unset, confirming LIVE-mode smoke testing was never wired up for
this repo, not just unavailable this session). Native ruling (2026-07-22):
the full authenticated `tools/call` round-trip (job_id → `prashna_status` →
full result) will be run by the Cowork operator from an already-
authenticated live connector session, as the independent confirmation
promised since W3 — not fabricated or worked around here. **Carried to §H
as a named residual, does not block V6 ACCEPT:** "prashna_ask end-to-end
(job_id → prashna_status → full result) pending an entitled connector
session; underlying engine independently verified live via the consult
route across this campaign; tool not yet visible on the expert-profile
connector — confirm it surfaces on a consult-scoped connection." Flagged
as the single highest-priority post-seal verification item.
