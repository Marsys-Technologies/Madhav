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
