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
| (pending) | retrieval | W0 S-1..S-5 safety deploy | pending |

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
