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
