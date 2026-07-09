---
canonical_id: R5_1_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md)
program: successor run to R5 (SEALED — R5_RETRIEVAL_3_0_SEAL_v1_0.md). Governing law unchanged:
  RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN v1.6 + R5 seal report §3/§6 punch-list.
head_at_c0: 5c699c75 (docs(r5.1) brief commit; synced to origin via PR #484)
scope: C0 preflight through C5 wrap, per brief phase order (strict, no skipping).
---

# R5.1 RUN LEDGER — MCP-Consume

Append-only. Every phase's close appends here; this document never edits prior entries.

## JL-000 — Scope ruling recorded (native, 2026-07-09)

**Entry:** the native's message dispatching `CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md` constitutes
the scope ruling and ratification-by-kickoff of this brief, per the brief's own frontmatter
`scope_ruling` field: PRIORITIZED = MCP interaction excellence on the two charts (482012f1 Abhisek +
1c826d5a Abhinandan) + acceptance battery. DEFERRED SHELF (explicitly out of scope, do not touch):
portal chat/UI productization, LEL/outcome web UI, Arunima/Kiran chart builds, rate limiting,
branch-graveyard cleanup, frontmatter CI debt, cross-chart pool opening, JL-022 Option B, tool-estate
legacy-name removal.

Execution mode: conductor + Pratinidhi-R grounded on `R5_AUTHORITY_DOSSIER_v1_0.md` (unchanged from
R5). Battery `R5_ANSWER_BATTERY_v1_0.md` remains FROZEN law — regression items only, never
edit/re-grade.

**Basis:** brief frontmatter `scope_ruling` field, v1.0, 2026-07-09.
**Reversibility:** all in-run judgment rulings carry native retrospective veto (brief inherits R5's
Pratinidhi-R protocol).

---

## C0 — PREFLIGHT (self-gating) — CLOSED, no HALT

### Deploy-truth
`amjis-web` latestReadyRevision `amjis-web-00889-9cz` (image `39f981cd…`, HEAD's parent — brief
commit `5c699c75` is docs-only, no redeploy required). `amjis-mcp` latestReadyRevision
`amjis-mcp-00403-c6v` (image `cf8e2186…`, PR #480) — confirmed zero `platform-mcp/**` commits landed
since that SHA. Live `initialize` handshake against the deployed MCP endpoint: HTTP 200, protocol
`2025-11-25`. **PASS.**

Finding: local `main` was 1 commit ahead of `origin/main` (`5c699c75`, docs-only, clean tree).
Direct push rejected by branch protection (4 required status checks). Resolved via PR #484
(`docs/r5-1-brief-sync`), set to auto-merge-squash.

### Migrations reconciliation
`_migrations_applied` = 310 rows; disk = 304 files; 0 on-disk-but-unledgered (no pending gap); 6
ledgered-but-retired-from-disk (pre-`173_drop_legacy_builds.sql` era, expected archival hygiene).
Latest ledgered = `426_build_runs_scope_asset_set.sql`, matches highest on-disk file. **PASS.**

### Canary battery state
Latest FULL battery on disk: `evals/r5-w4-full-battery/results_d5105222.json` (2026-07-08T20:42Z,
SHA `d5105222`, PR #478) — 14/38 pass, the known pre-C1 baseline (flagship instruments oversized —
exactly what C1 exists to fix). No scheduled canary job exists yet (`gcloud scheduler jobs list`
shows no canary-related job) — confirms brief item C5.2 is genuinely open, not silently skipped.
**Accepted as the honest W0 baseline for this run's before/after comparison (brief C4 requires a
token/latency/call-count table vs the W0 baseline — this is that baseline).**

### Test credential
`mcp_api_keys` row `key_id=mcp_prod_tDO7obNw`, `user_uid=probe-service-account`, scopes=['read'],
`revoked_at IS NULL`, `last_used_at=2026-07-08T21:21:42Z`. `chart_grants` confirms `view` permission
on both chart_ids. Live-fired `judgment_query` (career) against prod on both charts via this
credential — both HTTP 200 with full payload. **LIVE, confirmed usable.**

### Chart serving state
Queried `phala_rectification_best.judgment_flags` (authoritative source for
`query_phala_calibration.ts`):

| chart_id | calibration_state | lel_event_count | load_bearing |
|---|---|---|---|
| 482012f1 (native) | calibrated | 57 | true |
| 1c826d5a (Abhinandan) | structural | 0 | false |

Matches expected state exactly. **PASS.**

### C0 verdict
**No HALT condition triggered. Proceed to C1.** Two non-blocking notes carried forward: (1) PR #484
merge to be confirmed before relying on any CI-gated automation; (2) fresh canary run recommended
before C4 grading to timestamp a clean current-state baseline (the d5105222 result stands as the
pre-C1 baseline for the brief's required before/after table).

---

## C1 — UNBLOCK THE FLAGSHIP INSTRUMENTS — CLOSED, deployed, live-verified

### What shipped
New shared, structure-aware response-budget clipper (`platform-mcp/src/lib/response_budget.ts`)
with a real hard-cap fallback tier (asserts final size ≤ ceiling after declared sections are
floored, degrades `trim_report` itself rather than silently passing an over-budget object). v3
envelope (chart_header/verdict/drill_pointers/judgment_flags) is now the MCP-channel default for
`judgment_query`/`graha_portrait`/`pact_query`; `response_format:'legacy'` remains available.
Ceilings: judgment_query ≤12KB, graha_portrait ≤12KB, pact_query ≤8KB, measured on true wire bytes
(dual-output text duplication suppressed for these three tools only via new
`dualOutputBudgeted()` — the general 50KB mechanism used by every other MCP tool is untouched).
Fixed a pre-existing bug found during verification: `registerD10PactCapabilities()` was missing
from the live MCP bootstrap route (`platform/src/app/api/retrieval/capability/route.ts`), making
`pact_query` unreachable (404) over the real MCP path — same bug class as a prior D9 fix.

### Verifier-ring discipline (two independent passes, neither self-graded by the implementer)
- **First independent pass** (commit `624f2934`): FAIL. Found judgment_query/graha_portrait
  structuredContent 1.8–2.7x over ceiling (trimmer didn't cover the actual largest sections —
  `checklist.timing_hooks`, `content.yogas` — and had no hard-cap fallback); `pact_query` 404
  (bootstrap gap); dual-output duplication doubling real wire bytes on top of that. Routed back to
  the implementer as a self-heal, not a HALT (no prod deploy had happened yet, no chart-data write,
  no entitlement regression — none of the brief's halt conditions were triggered).
- **Fix pass** (commit `ece86939`): added the missing trimmable sections, a genuine hard-cap tier,
  `dualOutputBudgeted()`, fixed the D10 bootstrap gap.
- **Second independent pass**: PASS. Real server + real prod DB + real `tools/call` requests via
  the `mcp_prod_tDO7obNw` credential (not mocked). All four gate calls under ceiling on true wire
  bytes; receipt/verdict/drill_pointers intact; pact_query chain-honesty confirmed (real
  `chain_complete` and an honest `chain_pending_activation` halt, no fabrication). Scope check:
  only `response_budget.ts`, `registry_bridge.ts`, `envelope.ts`(+generated mirror), `route.ts`
  touched — must_not_touch (orchestrator/writers/chart-data/salience-constants/LEL) untouched.

### Deploy + live gate check (post-merge, [verify-against: mcp], PR #485, commit `a6ebb75b`)
`gh pr merge 485 --auto --squash` → merged. `Deploy to Cloud Run` workflow green. Confirmed both
`amjis-mcp` (`amjis-mcp-00404-9hk`) and `amjis-web` latest-ready revisions run image tag
`a6ebb75b98e40e879895a4a757a6a7e40fbc89d9` — exact match to the merge commit. Fired real
`tools/call` requests against the deployed prod endpoint (`amjis-mcp-qm256lasva-el.a.run.app/mcp`)
using the `mcp_prod_tDO7obNw` credential:

| Gate call | Wire bytes | Ceiling | Verdict |
|---|---|---|---|
| judgment_query career, native (482012f1) | 12,029 | 12,288 | PASS |
| judgment_query marriage, Abhinandan (1c826d5a) | 11,863 | 12,288 | PASS |
| graha_portrait Saturn, native | 11,550 | 12,288 | PASS |
| pact_query career, native | 7,855 | 8,192 | PASS |

Receipt/verdict/drill_pointers/trim_report all present and correct; `judgment_flags` carried an
honest `bhanga_not_checked` disclosure (not fabricated confirmation); pact_query returned a genuine
4-stage `chain_complete` verdict for career/native. Gate criterion from the brief ("judgment_query
career/native and marriage/Abhinandan round-trip inside the MCP client ceiling with receipt +
verdict + pointers intact; pact_query career/native chains all reachable stages within budget")
**MET, live, on prod.**

### C1 verdict
**CLOSED. No HALT. Proceed to C2.** Worktree `agent-a3a736cd196fbb2e2` / branch
`worktree-agent-a3a736cd196fbb2e2` cleaned up post-merge.

---

## C2 — ANSWER-QUALITY PUNCH ITEMS (the MCP-visible seven) — CLOSED, deployed, live-verified

Executed as three parallel lanes (conductor + worktree + independent-verifier-ring per lane, same
discipline as C1), merged sequentially (PR #487 Lane A, #488 Lane B, #489 Lane C), deployed to prod
at commit `d3fb74fa27beb966b8c14d69069a9b44e057804e` (confirmed: both `amjis-mcp` and `amjis-web`
latest-ready image tags match exactly).

### Lane A (items 1, 2) — PR #487
E-2 freshness contract (`platform/src/lib/retrieval/provenance/freshness_notes.ts`): stale hardcoded
DEFECT-001/signature_tier literals replaced with live-re-derived claims carrying `as_of`/
`expires_on`. E-6 digest family-aggregation (`collapseSignalFamilies()` in `composite_ranker.ts`,
wired into `query_ucd.ts`): same-family tied signals in the top band collapse to one composite row +
`family_member_pointers`. Independent verifier PASS (live server + prod DB, both claims re-derived
correct, no computed value altered, 505/505 tests, typecheck clean).

### Lane B (items 3, 4, 5) — PR #488
Denial ≠ empty: additive `entitlement_denied` envelope state wired into `/api/mcp/primitives`,
`/api/mcp/writes`, `/api/mcp/bundles`. Posterior cardinality + base_rate_source
(`query_predictive_anchors.ts`/`query_predictions.ts`): additive provenance blocks, no computed
value changed. lel_training_matched=0 corroboration (`query_phala_calibration.ts`): serves the
previously-unserved `lel_training_events`/`lel_training_matched` columns with an honest
`lel_match_explanation` distinguishing full corroboration (57) from the firewalled training subset
(36 events, 0 matches). Independent verifier PASS (all three items live-tested against genuinely
ungranted resources / real DB cross-checks; zero entitlement widening; 5235/5235 + 398/509 with 96
pre-existing failures confirmed byte-identical to baseline).

**Significant finding, deliberately not fixed in this run:** `/api/retrieval/capability` — the
actual live path the flagship instruments (`judgment_query`/`graha_portrait`/`pact_query`/
`get_signals`/`query_chart_facts`) use — has no `authorizeChartAccess` check at all, only a shared
service-to-service token. Confirmed independently and reconfirmed in this phase's own live gate
check below (a fabricated/ungranted chart_id via `query_chart_facts` returns `ok:true, facts:[]` —
empty, not denied). Pre-existing, not introduced by this run. Not fixed here — an entitlement-model
change on this shared path has wide blast radius and the brief's own discipline calls for stopping
and reporting rather than guessing on anything affecting who is denied vs granted.
**Recommend a dedicated follow-up session to add the gate — flagged prominently, not buried.**

### Lane C (items 6, 7) — PR #489
JL-027 Option A graha-yuddha (`get_graha_yuddha`): serve-time-only read overlay joining existing
`ephemeris_daily.latitude` against floored `chart_facts.graha_yuddha` rows; Venus-always-wins /
higher-northern-latitude rule; BPHS + Bṛhat Saṃhitā citation; floor preserved where ineligible/
unavailable, longitude-proxy never substituted. chart_snapshot: compact ≤2KB (rendered-text-field)
12-rashi D1 grid from `chart_divisionals`, `include_navamsa` opt-in for D9. Independent verifier
PASS (full MCP round-trip, ephemeris latitude values and chart placements independently re-queried
from the DB, floor-preservation confirmed by reading chart_facts at rest).

### C2 live gate check (post-merge, [verify-against: mcp], deployed prod, both charts)

| Item | Tool (public MCP name) | Result |
|---|---|---|
| 1 — E-2 freshness | `get_chart_quality` | PASS — native chart shows `as_of`/`expires_on`, real 1.1% orphan rate (the "91.5%" string appears only as an explicit historical-baseline comparison, not the current claim) |
| 2 — E-6 aggregation | `get_chart_orientation` (response_format:full) | PASS — `is_family_composite`/`family_member_pointers` present live |
| 3 — Denial ≠ empty | — | **NOT externally reachable.** The fixed routes (`/api/mcp/primitives`, `/api/mcp/writes`, `/api/mcp/bundles`) have no corresponding public tool name in the live `tools/list` (confirmed: no `log_prediction`/`lel_event_record` tool exists publicly; `record_outcome` exists but doesn't require `chart_id`, so it doesn't exercise this path). Fix is correct and independently live-verified by the verifier-ring (against real ungranted resources, via direct route calls with proper internal auth) — but a real MCP chat client cannot currently trigger it. Genuine gap, not concealed. |
| 4 — Posterior provenance | — | **NOT externally reachable.** `query_predictive_anchors`'s capability URI has no public MCP tool wired to it (`phala_anchors_get` is a same-named but functionally distinct sidecar-backed alias that calls `/api/compute/phala/event_anchors`, not this capability). Fix is correct and independently verified (exact DB match, formula check `0.2×1.75×1×1×0.92=0.322`) — but not reachable via any live MCP tool call today. Genuine gap, not concealed. |
| 5 — LEL corroboration | `phala_rectification_get` | PASS — live response carries full `lel_match_explanation` (57 total vs 36 training-subset, 0 matches, criterion explained, leakage-firewall note) |
| 6 — JL-027 graha-yuddha | `get_graha_yuddha` | PASS — native: 0 pairs, honest empty. Abhinandan: VEN_v_MAR resolves winner=VEN across all 5 ayanamshas, BPHS/Bṛhat Saṃhitā citation, floor at rest in `chart_facts` unchanged |
| 7 — chart_snapshot | `chart_snapshot` | PASS — both charts' D1 grids match every documented FORENSIC/battery anchor exactly (native: Sun Cap, Moon Aqu 29°46′/Purva Bhadrapada range, Lagna Ari; Abhinandan: Lagna Ari 1° w/ Rahu 28°18′≈23°32′ range, Moon Gem, Sun+Me Aqu, Ve+Ma Pis, Ju Cap, Sa Sco) |

### C2 verdict
**CLOSED. No HALT.** 5 of 7 items fully confirmed live over the public MCP channel on both charts.
2 items (3, 4) are correctly implemented and independently verified at the code/capability level but
currently unreachable by any live MCP tool call — carried forward to the punch-list as "wire a
public MCP tool to the fixed capability," not re-litigated as incomplete work (the underlying fix is
real and correct; only the tool-registration/exposure step remains). The pre-existing
`/api/retrieval/capability` entitlement-gate gap (found under Lane B) is the single most
consequential finding of this phase and is flagged for dedicated prioritization, not silently
deferred. Proceed to C3.

---

## C3 — FORWARD PANCHANGA (D-8, the one sanctioned data-plane addition) — CLOSED, deployed, live-verified

### What shipped
Migration `platform/supabase/migrations/427_panchanga_daily_reprovision.sql` re-provisions
`panchanga_daily` from a WHERE-FALSE stub view into a real date-keyed table (relkind-guarded
`DROP VIEW`, superset schema serving both existing consumer contracts, indexed, transactional).
**Applied directly to prod pre-merge** (via `scripts/migrate.ts`, per this repo's standing migration
convention — separate from the code-PR pipeline used elsewhere in this run — after a migration-guard
review that caught and fixed a re-run idempotency bug). New deterministic writer
`platform/python-sidecar/scripts/panchanga_daily_writer.py` (Swiss Ephemeris, no LLM) seeded 366 rows
(2026-07-09..2027-07-09) at the native's location default (Bhubaneswar 20.27/85.84).

The actual root-cause bug this phase closed: `_fetch_panchanga_row()` in
`brahmagyan/phala/muhurta.py` queried a nonexistent column, threw, was silently swallowed, and fell
back to hardcoded placeholder values ("Shukla Panchami"/"Hasta"/"Shubha") presented as real data — a
canonical-or-floor (B.10) violation. Fixed; `generate_muhurta_windows()` now skips dates lacking real
coverage and surfaces an honest `empty_reason` instead of fabricating. Also fixed: `query_muhurat`'s
capability mapping (previously pointed at the wrong L0 capability, `query_planet_transit`, entirely
unrelated to muhurta search) and a shape-mismatch bug in the `muhurta_finder` MCP tool
(`tool_name_bridge.ts` wraps every capability result in a generic `ToolBundle`; `muhurta_finder.ts`
was casting the wrapped shape directly instead of unwrapping it, so `.windows` was always
`undefined` → silently fell back to `[]` regardless of real data underneath).

**Scheduled job**: sidecar endpoint `POST /api/compute/panchanga/refresh` + Next.js cron proxy
`/api/admin/cron/refresh-panchanga-daily` shipped and live-tested. Terraform resource
(`infra/scheduler/panchanga_refresh.tf`, monthly) is authored and committed but **NOT applied** — no
agent in this run has cloud infrastructure write access (`terraform apply` requires it). **Flagged
explicitly for a follow-up session with infra access to run `terraform apply` from main** — carried
forward, not silently dropped.

### Verifier-ring discipline — including a genuine false-negative episode, traced and resolved
- **First independent pass**: migration safety PASS (real table confirmed via `relkind`, checksum of
  the applied migration byte-identical to the committed file, row count/date range/location matched
  exactly, astronomical spot-check — `vara` cross-referenced against the true Gregorian weekday for 5
  consecutive seeded dates, all correct). `kala_muhurta_get` live MCP round-trip PASS on both charts.
  This pass also found the `muhurta_finder` shape-mismatch bug (always empty windows) — routed back
  to the implementer as a self-heal, not a HALT.
- **Fix pass**: implementer added a narrow `unwrapMuhurtaFinderResult()` helper; self-reported live
  verification showing 7 real windows on both charts.
- **Second independent pass**: reported a contradictory **FAIL** — claimed `muhurta_finder` still
  returned empty windows and that the `query_muhurat` capability mapping was still wrong. This
  directly conflicted with the fix-pass's own live evidence and with a direct source read.
- **Conductor-level resolution (not delegated)**: read the committed source directly — confirmed the
  capability mapping and the new `L4_phala/query_muhurat.ts` file were genuinely correct and
  registered, contradicting the second verifier's specific claim. Rather than trust either
  self-report, personally stood up a from-scratch live triad (python-sidecar + platform + platform-mcp,
  all from the exact worktree commit, against prod DB via the existing Cloud SQL Auth Proxy) and fired
  real MCP `tools/call` requests directly. Result: genuine, real ranked windows with panchanga
  citations on both charts at 2026-10-09, and honest empty-with-reason at 2028. **The second
  verifier's FAIL was a test-environment setup artifact in its own run (most likely a stale/misrouted
  local server), not a real defect** — settled by first-party evidence, not by picking a side.
  A stray uncommitted `CONDUCTOR_HALT_LOG.md` diff and probe script left behind by that verifier's
  broken run were discarded before merge (not part of the C3 feature).

### Deploy + live gate check (post-merge, [verify-against: mcp], PR #491, commit `bcdfed4544cac51a2dfb0d110a5ce8109c1e19ef`)
Confirmed `amjis-mcp`, `amjis-web`, AND `amjis-sidecar` (three services this time — the sidecar image
changed too) latest-ready image tags all match the merge commit exactly. Live gate check against
deployed prod (`amjis-mcp-qm256lasva-el.a.run.app/mcp`), `muhurta_finder`, action_type marriage,
2026-10-01..2026-10-15 (3 months out):

| Chart | window_count | Verdict |
|---|---|---|
| Native (482012f1) | 7 | PASS — real ranked windows, real panchanga citations (e.g. "panchanga_daily 2026-10-07 (Krishna Dvadashi/Magha/Mercury)... BPHS ch.46 muhurta rules") |
| Abhinandan (1c826d5a) | 7 | PASS — same |

Far-future (2028-06-01..2028-06-15, native, general): `window_count: 0`, honest `empty_reason` in the
provenance envelope, no fabrication. **Gate criterion from the brief ("a muhurta question over MCP
returns ranked windows w/ panchanga basis for a date 3 months out, on both charts") MET, live, on
deployed prod, on the actual flagship tool the brief names.**

### C3 verdict
**CLOSED. No HALT.** One open follow-up carried forward honestly: the monthly-refresh Cloud
Scheduler job needs `terraform apply` by a session with cloud infra write access — the code/config is
ready, the actual cloud resource is not yet provisioned. Proceed to C4.

---

## C4 — THE ACCEPTANCE CEREMONY — GATE NOT MET (honest result; not a HALT)

### Grading-path restoration (the brief's explicit precondition)
Before running anything, the conductor personally verified whether the Gemini/DeepSeek network path
— which the prior R5 run found genuinely unavailable ("no network path to those providers in this
run's environment," R5_RETRIEVAL_3_0_SEAL_v1_0.md §3) — was restorable in this run's environment, per
the brief's explicit instruction ("restore the network path as part of this phase; if genuinely
unrestorable, HALT-and-report, do not self-grade"). Result: **restorable.** Direct `curl` tests
confirmed real network egress to both `generativelanguage.googleapis.com` (403, not a connection
failure — reached the server) and `api.deepseek.com` (401, same). Both API keys exist in GCP Secret
Manager (`DEEPSEEK_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`) and were confirmed live with real
completions (`gemini-2.5-flash` — note `gemini-2.0-flash` is deprecated/404s; `deepseek-chat`).
**The HALT-and-report-if-unrestorable condition does NOT apply — grading is genuinely live.**

### Harness state found and fixed
`evals/r5-w4-full-battery/battery_runner.ts` had never actually called a live LLM for rubric grading
— the "rubric" step was a keyword-regex proxy, and worse, the verdict computation silently *ignored*
rubric-floor outcomes entirely, computing PASS/FAIL from deterministic assertions alone — contrary to
the battery doc's own grading law ("passes only if ALL deterministic assertions hold AND rubric ≥
floor"). New `evals/r5-w4-full-battery/llm_grader.ts` wires real Gemini-primary/DeepSeek-fallback
grading; the verdict bug is fixed. Merged via PR #493 (harness/eval code only, no product code
touched — `git diff main --stat` confirmed scope). **This is the first time this harness has ever
computed a battery verdict against real rubric grading — R5's own "36.8%" headline number was never
actually gated on live LLM grading either.**

### Full run (both charts, live MCP channel, prod)
38-item frozen battery (`R5_ANSWER_BATTERY_v1_0.md` — 38 items, not 40; no regression items have ever
been appended to the frozen doc, noted honestly rather than fabricating some to match the brief's "40"
phrasing). Executed via real `tools/call` JSON-RPC against `amjis-mcp-qm256lasva-el.a.run.app/mcp`
using the `mcp_prod_tDO7obNw` credential — confirmed via transport code inspection, not a DB/sidecar
shortcut. Results: `evals/r5-w4-full-battery/results_bcdfed45.json`.

**Headline: 9/38 = 23.7% overall. Q1/X deterministic classes: 4/16 = 25.0%. Rubric floors: 12/22 met,
9 below floor, 1 (Q7-N-2, a multi-turn drill item) marked INCONCLUSIVE — structurally ungradeable by
this harness, not faked as pass or fail.**

Token/latency/call-count vs W0 baseline (brief-required table): 44 total MCP calls, ~1.07MB total
wire bytes, ~35.0s total MCP latency across all 38 items/both charts (per-tool latency reads faster
than the W0a baseline in `R5_RUN_LEDGER_v1_0.md` P0-iii — consistent with C1's genuine perf wins).
21 Gemini rubric-grading calls, 0 DeepSeek fallbacks needed, ~70.7K tokens in / ~630 out, ~122s total
grading latency (this is new spend — R5 never actually made these calls before).

### Gate assessment — three of four criteria FAIL
| Gate criterion | Required | Actual | Met? |
|---|---|---|---|
| Overall pass rate | ≥90% | 23.7% (9/38) | **NO** |
| Q1/X deterministic | 100% | 25.0% (4/16) | **NO** |
| Every rubric floor met | 100% | 57% (12/21 gradeable) | **NO** |
| Zero regressions vs R5 seal baseline | required | see below | **Qualified YES** |

Regression assessment: raw comparison to R5's headline (36.8%/14 of 38) looks like a drop, but that
number was computed by a harness that never enforced rubric floors — it is not a comparable
apples-to-apples baseline for the same metric. On the narrower, genuinely comparable slice (Q1/X
deterministic assertions, which the old harness DID check honestly), there is no new regression: every
Q1/X item that passed before still passes; X-8 improved (a direct result of C2's freshness fix). No
item that previously passed now fails. **On the metric that's actually comparable, zero regressions
holds. On the metric the brief actually gates (real rubric-inclusive pass rate), this run is the
first honest measurement ever taken — not a regression, a newly-revealed baseline.**

### Failure characterization (28 fails + 1 inconclusive, categorized)
Sampled and root-caused rather than accepted at face value (the prior R5 run had documented harness
false-negative bugs, so a low number was NOT assumed genuine without checking):
- **Genuine content/computation gaps** (not harness bugs): `query_chart_facts` (the tool the Q1 items
  route through) returns raw positional facts (sign/house/nakshatra/degree) but carries **no computed
  dignity/exaltation field at all** — confirmed by fetching the exact Q1-A-2 payload live and finding
  `"sign":"Pisces","house_d1":12` present but no "exalt" anywhere in the response. Live-verified this
  is real, not a regex miss: the field genuinely doesn't exist in this tool's output shape, even
  though the underlying fact (Venus exalted in Pisces) is true and was independently confirmed via
  `chart_snapshot` earlier in this same run (C2/C3).
- **Byte-budget overages on tools C1 never touched**: Q1-N-3/N-4/A-3 exceed their tight ≤1-2KB
  ceilings (2.3-3.5KB) — `query_chart_facts`/`ganita_dashas_get` never received C1's trim discipline
  (C1's scope was explicitly limited to `judgment_query`/`graha_portrait`/`pact_query`). X-3/X-6/X-7
  show far larger overages (127-234KB) on `bodha_signals_get`/`ganita_positions_get` — tools with no
  budget discipline applied anywhere in this run.
- **Real LLM-graded content-quality shortfalls**: several items pass every deterministic assertion but
  score 5-10/15 on rubric (Q3-A-2, Q6-N-1, Q8-N-1, Q8-A-1, Q9-A-1) — genuine depth/quality gaps in
  synthesis, not structural defects.
- **Already-known, already-documented gaps surfacing here too**: X-2 (`denial_not_empty` — the exact
  `/api/retrieval/capability` entitlement-gate finding from C2 Lane B, confirmed here independently by
  the battery itself); X-8 (stale-note residue — mostly fixed by C2's E-2 work, one marker still
  present).

**None of this is a harness false-negative pattern this time** — the conductor specifically checked
the Q1 failures (the most suspicious, since they should trivially pass given C2/C3's own live
verification of the same facts via other tools) and confirmed each is a real, traceable gap: either a
missing computed field, an unbudgeted payload, or genuine content depth. This is the honest signal the
old proxy-grading harness had been masking.

### Why this does not HALT
None of the brief's explicit halt conditions were triggered: no prod deploy broke a previously-green
canary, no chart-data write occurred (confirmed: none of the 38 items call a write tool), no
entitlement was widened (X-2 is a pre-existing gap surfaced, not created). The LLM-grading-
unavailable halt condition specifically does not apply — grading is genuinely live. Per this run's own
established precedent (mirroring R5 Retrieval 3.0's identical handling of a NOT-MET battery gate:
"routes battery shortfalls to the punchlist rather than treating them as run-blocking"), this is
reported honestly and routed to a punch-list rather than triggering an open-ended scope expansion that
would violate the brief's own C1-C3 scope boundaries (fixing all 28 failures would require touching
many tools never authorized in `may_touch` for the specific fixes needed — dignity computation in
`query_chart_facts`, budget discipline on `bodha_signals_get`/`ganita_positions_get`/`ganita_dashas_get`,
and deeper content-quality work — none of which C1/C2/C3 scoped).

### C4 punch-list (carried forward, not blocking this run's close)
1. `query_chart_facts` needs a computed dignity/exaltation field joined into its `about` facet
   response — currently absent entirely, not just under-formatted.
2. Byte-budget discipline (C1's pattern: named trimmable sections + hard-cap fallback + trim_report)
   needs to extend beyond the three C1 tools to at least `query_chart_facts`, `ganita_dashas_get`,
   `bodha_signals_get`, `ganita_positions_get` — the battery shows real overages up to 234KB.
2b. The `/api/retrieval/capability` entitlement-gate gap (first found in C2, independently
   reconfirmed here via X-2) remains the single highest-priority item on the combined punch-list.
3. Several Q3/Q6/Q8/Q9-class items need genuine synthesis-depth work to clear rubric floors — this is
   real content/product work, not a quick fix, and should be scoped as its own dedicated program.
4. A dedicated remediation-and-rerun session against this same harness (now genuinely functional) is
   the correct next step to convert this from NOT MET toward ACCEPTED — this run's C1-C3 scope was
   never sized to close a 38-item full-battery gap in one pass.

### C4 verdict
**GATE NOT MET. Not a HALT.** The battery harness itself is now trustworthy for the first time (real
MCP transport, real LLM rubric grading, a fixed verdict-computation bug) — that is a genuine, durable
improvement this run delivers regardless of the score. The 23.7%/25.0% numbers are an honest,
first-ever real measurement, not a fabricated pass and not smoothed into an implied acceptance. Per
the brief's own gate language ("converts SEALED → ACCEPTED"), this run does **NOT** convert the
program to ACCEPTED — it converts it to "honestly measured, with a real punch-list and a trustworthy
instrument to re-measure against." Proceed to C5 to wrap and report this state accurately; do not seal
this as an acceptance.
