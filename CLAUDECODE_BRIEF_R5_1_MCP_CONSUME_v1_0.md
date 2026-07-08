---
canonical_id: CLAUDECODE_BRIEF_R5_1_MCP_CONSUME
version: 1.0
status: READY-FOR-KICKOFF — fully autonomous, one paste, zero human gates (acceptance read at the end)
created: 2026-07-09
author: Cowork (Beyond-Acharya program) — native-prioritized MCP-consume hardening, sitting 2026-07-09
program: successor run to R5 (SEALED — R5_RETRIEVAL_3_0_SEAL_v1_0.md). Converts "implementation SEALED"
  into "ACCEPTED FOR DAILY USE" for the native's chosen consumption mode: TWO CHARTS
  (482012f1 Abhisek + 1c826d5a Abhinandan), MCP-ONLY. Governing law unchanged:
  RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN v1.6 + R5 seal report §3/§6 punch-list.
scope_ruling (native, 2026-07-09): PRIORITIZED = MCP interaction excellence on the two charts +
  acceptance battery. DEFERRED SHELF (explicitly out of scope; do not touch): portal chat/UI
  productization · LEL/outcome web UI (MCP write tools suffice) · Arunima/Kiran chart builds ·
  rate limiting · branch-graveyard cleanup · frontmatter CI debt · cross-chart pool opening ·
  JL-022 Option B · tool-estate legacy-name removal.
execution_mode: conductor + lanes in isolated worktrees + verifier ring (≠ implementer) +
  Pratinidhi-R grounded on R5_AUTHORITY_DOSSIER_v1_0.md (unchanged) — the proven pattern. Per-phase
  prod deploys, ACs [verify-against: prod | mcp | battery]. Terminal worktree/branch cleanup = exit gate.
battery: R5_ANSWER_BATTERY_v1_0.md remains FROZEN law — add regression items only, never edit/re-grade.
halt_conditions: prod deploy breaks a green canary AND rollback fails · any chart-data write ·
  entitlement regression · else self-heal via Pratinidhi-R; non-blocking findings → punch-list.
may_touch: ["platform/src/lib/retrieval/**", "platform/src/app/api/{retrieval,mcp}/**", "platform-mcp/src/**", "surgical migrations (full-path cited)", "panchanga writer + scheduled job (new, serving-plane)", "python-sidecar serving modules for punch items", "00_ARCHITECTURE run/seal/ledger docs", "scheduled-job config for the canary"]
must_not_touch: ["orchestrator + ALL build writers", "chart data L0–L5 (read-only; panchanga_daily is the ONE sanctioned new data surface — it is date-keyed reference, not chart data)", "salience/priors/formula constants", "LEL rows", "everything on the deferred shelf above"]
---

# BRIEF R5.1 — MCP-CONSUME: from sealed to daily-usable, two charts, one channel

## C0 — PREFLIGHT (self-gating)
Deploy-truth: amjis-mcp + amjis-web revisions == HEAD; migrations dirs reconciled. Canary battery
green (or failures explained against the seal's known state). Test credential live (provisioned in R5
W0a). Confirm both charts' serving state: native calibrated / Abhinandan structural. `git status`
sweep on governing artifacts (commit anything untracked). Open R5_1_RUN_LEDGER; opening JL entry:
native scope ruling 2026-07-09 recorded.

## C1 — UNBLOCK THE FLAGSHIP INSTRUMENTS (the 86KB fix; highest value, do FIRST)
1. **Budget facet + trim discipline on judgment_query / graha_portrait / pact_query.** Default
   response sized for a chat client: ≤12KB judgment/portrait, ≤8KB pact (constants →
   brahma_formula_constants, class=engineering). Mechanics: lean section summaries + drill_pointers
   for depth (pointers ARE the overflow), `include`/`max_signals` honored aggressively, result_clipper
   wired, trim_report on every clip. The full 86KB detail remains reachable — by explicit facets,
   never by default.
2. **v3 envelope becomes the MCP-channel default** (chart_header/verdict/drill_pointers/judgment_flags
   on every response); `response_format:'legacy'` remains available. Flip ONLY after C1.1 verifies
   ≤ ceilings on both charts.
3. Gate `[verify-against: mcp]`: judgment_query(career, native) and (marriage, Abhinandan) round-trip
   INSIDE the MCP client ceiling with receipt + verdict + pointers intact; pact_query(career, native)
   chains all reachable stages within budget.

## C2 — ANSWER-QUALITY PUNCH ITEMS (the MCP-visible seven)
1. **Stale provenance-note literals** → E-2 freshness contract: notes become data w/ as_of/expires_on;
   the DEFECT-001/signature_tier claims re-derived from live counts (post-R4 they are FALSE — fix the
   substance, not just the date).
2. **Digest family-aggregation** (E-6 completion): one composite row per family in the top band —
   kills the dignity-row tie-blocks my closing probe saw; atoms stay reachable via pointers.
3. **Denial ≠ empty**: entitlement denials get their own envelope state, distinct from
   empty-with-reason, on every instrument.
4. **posterior cardinality** + **base_rate_source stamping** (lift_vector provenance) — per seal §6.
5. **lel_training_matched=0 corroboration** — the native's rectification LEL-fit match accounting
   made honest (it validated 10:43; the match counter must say how).
6. **JL-027 Option-A implementation**: graha-yuddha winner by northern latitude from ephemeris
   declination; replaces the floor; derivation ledger + citation; floor stays wherever declination
   is unavailable.
7. **Compact rashi-chart surface**: `chart_snapshot` capability (or facet on chart_query) — D1 (+D9
   on request) as a compact chat-renderable text grid: 12 rashis, occupants w/ degrees, lagna marked,
   ≤2KB. The "show me the chart" answer.
Gate: battery items touching these (Q1/Q2/Q3/X-8 classes) pass deterministically on both charts.

## C3 — FORWARD PANCHANGA (D-8; the one sanctioned data-plane addition)
Re-provision `panchanga_daily` as a real date-keyed table (full path cited; the WHERE-FALSE stub view
replaced); deterministic writer computes tithi/vara/nakshatra/yoga/karana + hora windows for a rolling
+12-month window at the native's location default; scheduled monthly refresh job. kala_muhurta /
muhurta_finder consume it; empty-with-reason remains for dates outside the window.
Gate `[verify-against: mcp]`: a muhurta question over MCP returns ranked windows w/ panchanga basis
for a date 3 months out, on both charts.

## C4 — THE ACCEPTANCE CEREMONY (converts SEALED → ACCEPTED)
Full frozen battery (40 items + R5's added regressions), BOTH charts, executed OVER THE MCP CHANNEL
as a real client: deterministic assertions machine-graded; rubric grading via the product-policy LLM
path (Gemini primary / DeepSeek fallback — restore the network path as part of this phase; if
genuinely unrestorable, HALT-and-report, do not self-grade). **Gate: ≥90% overall · 100% on Q1/X
deterministic classes · every rubric floor met · zero regressions vs the R5 seal baseline.** Publish
per-item scorecard + token/latency/call-count table vs the W0 baseline in the acceptance report.

## C5 — WRAP + OPERATE
1. CURRENT_STATE §2/§3 staleness fixed; this run + acceptance recorded; next-objective = "daily MCP
   usage + deferred shelf".
2. Canary battery → scheduled job (daily, 5 probes, feeds system_health; alert on regression).
3. min-instances=1 retained (native-ratified, $132.71/mo).
4. **MCP USAGE GUIDE** (`00_ARCHITECTURE/MCP_USAGE_GUIDE_v1_0.md`, ~1 page, native-facing): the best
   question patterns per Q-class; how to invoke frames (from-Moon), paradigms (Jaimini/KP), budgets
   (glance/deep); how to read receipts + epistemic grades; how to record a life event and an outcome
   over MCP (lel_event_record / mimamsa_outcome_record) and what recalibration does behind the
   debounce; the two chart ids.
5. Seal: `R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md` (scorecard + honest-gaps + deferred shelf restated) ·
   ledger + SESSION_LOG close · worktrees/branches cleaned (exit gate) · final report to native.

## PHASE ORDER IS STRICT: C0→C1→C2→C3→C4→C5. C4 may not start until C1–C3 are prod-deployed
(the battery must grade the finished instrument, not a moving one).
