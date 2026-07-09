---
canonical_id: R5_1_MCP_CONSUME_ACCEPTANCE
version: 1.0
status: SEALED — honest result; program status is "hardened, deployed, partially verified" NOT
  "fully ACCEPTED" (C4 acceptance gate NOT MET)
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md)
program: successor run to R5 (SEALED — R5_RETRIEVAL_3_0_SEAL_v1_0.md)
full_run_ledger: 00_ARCHITECTURE/R5_1_RUN_LEDGER_v1_0.md (append-only, full per-phase detail)
---

# R5.1 MCP-CONSUME — ACCEPTANCE REPORT

## §1 — What this run was

A fully autonomous, five-phase run (C0 preflight → C1 flagship-instrument unblock → C2 seven
answer-quality punch items → C3 forward panchanga data plane → C4 acceptance ceremony → C5 wrap)
converting R5 Retrieval 3.0's SEALED implementation toward daily MCP usability for the native's
two charts (482012f1 Abhisek, 1c826d5a Abhinandan). Native scope ruling: MCP interaction excellence
+ acceptance battery, prioritized; portal/UI productization, rate limiting, cross-chart pool
opening, and several other items explicitly deferred (see brief frontmatter `scope_ruling`).

Every code-shipping phase (C1, C2, C3) followed a conductor + isolated-worktree + independent-
verifier-ring discipline: an implementer agent proposes a change in an isolated git worktree, a
SEPARATE agent independently re-verifies it live against real prod data before merge, and only
verified work reaches a PR. Where a first verification pass found real problems (C1's initial
trim implementation, C3's `muhurta_finder` bug), the run self-healed via a fix-and-reverify cycle
rather than shipping on a false pass. One genuine conflicting-verifier-reports episode occurred in
C3 and was resolved by direct conductor-level live testing rather than trusting either side's
self-report — documented in full in the run ledger.

**This report gives the honest headline result. It does not round up. Where a gate was not met,
that is stated plainly.**

## §2 — What shipped, deployed, and live-verified on prod

| Phase | What | Verification |
|---|---|---|
| C1 | Budget/trim discipline + hard-cap fallback + v3-envelope-default on `judgment_query`/`graha_portrait`/`pact_query` (12KB/12KB/8KB real wire-byte ceilings) | Two independent Ring-2 passes (first FAIL → self-heal → second PASS); live-confirmed on deployed prod, both charts |
| C2 | E-2 freshness contract, E-6 digest aggregation, entitlement-denial envelope, posterior provenance, LEL-match corroboration, JL-027 graha-yuddha declination winner, `chart_snapshot` | 3 independently-verified lanes; 5/7 items confirmed live over the public MCP channel (2 correct but not yet tool-wired — see §4) |
| C3 | `panchanga_daily` real date-keyed table (migration applied to prod), deterministic writer, `muhurta_finder` root-cause fix (was fabricating placeholder data on a bug — now genuinely computes or honestly floors) | Independently verified (migration checksum/astronomical spot-check) + conductor-personal live re-test after a false-negative episode; confirmed on deployed prod, both charts |

All three phases are live on prod (`amjis-mcp`, `amjis-web`, `amjis-sidecar` all confirmed running the exact merge-commit images). No chart data was written. No entitlement was widened. `min-instances=1` retained on both services throughout ($132.71/mo, native-ratified, unchanged).

## §3 — C4: the acceptance ceremony — GATE NOT MET

Per the brief, C4 required restoring the Gemini/DeepSeek rubric-grading network path (found
genuinely unavailable in R5's environment) before grading could proceed at all — with an explicit
instruction to HALT-and-report rather than self-grade if unrestorable. **This path was confirmed
restorable** (both providers live-tested with real credentials, real completions returned) and
used for real grading — this is the first time this battery has ever been graded against a real
LLM rather than a keyword-regex proxy. A pre-existing harness bug (verdict computation silently
ignoring rubric-floor outcomes) was found and fixed in the same pass.

**Result: 9/38 items pass (23.7%; gate requires ≥90%). Q1/X deterministic classes: 4/16 (25.0%;
gate requires 100%). Rubric floors: 12/21 gradeable items met their floor (57%; gate requires
100%).**

This was investigated, not accepted at face value — the failures were root-caused rather than
assumed to be harness noise (the prior R5 run had documented genuine harness false-negatives, so
this was checked for specifically). Findings:
- A genuine, traceable content gap: `query_chart_facts` (the tool most Q1 items route through)
  returns raw positional facts but carries **no computed dignity/exaltation field** — confirmed by
  fetching the exact failing payload live and finding the underlying fact true (independently
  confirmed via `chart_snapshot` earlier in this run) but simply not present in this tool's shape.
- Byte-budget overages on tools C1's trim discipline never touched (`query_chart_facts`,
  `ganita_dashas_get` in the 2-4KB range; `bodha_signals_get`/`ganita_positions_get` up to 234KB).
- Real LLM-graded content-quality shortfalls on several Q3/Q6/Q8/Q9 items (rubric scores 5-10/15
  on structurally-complete responses) — genuine synthesis-depth gaps, not defects.
- The already-known C2 finding (entitlement-denial clarity on the flagship path) surfacing again
  independently via item X-2.

**This is not a harness false-negative pattern.** The instrument itself has real, identified gaps
beyond what C1-C3 scoped to fix.

**Zero regressions, qualified:** on the narrow slice that both the old and new harness measure
comparably (Q1/X deterministic assertions), nothing that passed before now fails, and one item
(X-8) improved directly from C2's work. On the metric the brief actually gates (real rubric-
inclusive pass rate), this run is the *first honest measurement ever taken* — R5's own 36.8%
headline was never computed against live rubric grading either, so this is not a comparable
regression, it is a newly-revealed baseline.

**This does not constitute a HALT.** None of the brief's halt conditions were triggered (no
broken canary, no chart-data write, no entitlement widened, and the LLM-grading-unavailable
condition specifically does not apply since grading is genuinely live). Per this run's own
precedent — mirroring how R5 itself handled its own not-met battery gate — this is reported
honestly and routed to a punch-list rather than triggering unscoped remediation work.

Full per-item scorecard, deterministic-assertion detail, rubric scores, and the
token/latency/call-count table vs the W0 baseline: `evals/r5-w4-full-battery/results_bcdfed45.json`
and `00_ARCHITECTURE/R5_1_RUN_LEDGER_v1_0.md` §C4.

## §4 — Honest gaps carried to the punch-list

1. **`/api/retrieval/capability` has no entitlement check at all** on the path the flagship
   instruments actually use (`judgment_query`/`graha_portrait`/`pact_query`/`get_signals`/
   `query_chart_facts`) — found in C2, independently reconfirmed by the C4 battery itself (item
   X-2). Pre-existing, not introduced this run. Highest-priority carry-forward.
2. `query_chart_facts` needs a computed dignity/exaltation field — currently absent entirely.
3. Byte-budget discipline (C1's pattern) needs to extend beyond the three C1 tools to at least
   `query_chart_facts`, `ganita_dashas_get`, `bodha_signals_get`, `ganita_positions_get`.
4. Several Q3/Q6/Q8/Q9-class items need genuine synthesis-depth work to clear rubric floors — a
   dedicated content program, not a quick fix.
5. Two C2 fixes (denial-envelope routes, posterior-provenance capability) are correct but not yet
   wired to a public MCP tool name — the fix works, a client just can't reach it yet.
6. The monthly panchanga-refresh Cloud Scheduler job (C3) is coded and tested but its Terraform
   resource needs `terraform apply` by a session with cloud infra write access.
7. This deferred shelf from the brief's own scope ruling remains open: portal chat/UI
   productization, LEL/outcome web UI, Arunima/Kiran chart builds, rate limiting, branch-graveyard
   cleanup, frontmatter CI debt, cross-chart pool opening, JL-022 Option B, tool-estate legacy-name
   removal.
8. A dedicated C4-remediation-and-rerun session is the correct next step — the battery harness is
   now genuinely trustworthy (real MCP transport, real LLM grading, fixed verdict logic) and ready
   to re-measure against once items 1-4 above see real work.

## §5 — Program status

**C1, C2, C3: shipped, deployed to prod, independently verified live on both charts.** These are
real, durable improvements — the flagship instruments are now genuinely usable over a real MCP
chat client within budget, seven answer-quality defects are fixed (five confirmed live, two
correct-but-unwired), and forward panchanga/muhurta search works end-to-end with honest
empty-with-reason behavior.

**C4: the acceptance gate is NOT MET.** The program does not convert from "SEALED" (R5's own prior
seal) to "ACCEPTED" per this brief's own definition of that word. It is more honestly described as
**"hardened and deployed, first-time-honestly-measured, with a real and identified punch-list."**
This is a genuine, non-trivial finding, not a technicality — the underlying instrument needs more
work before it should be represented as broadly reliable for unmoderated daily use across the full
query taxonomy, even though the three specific things this run set out to fix (flagship-instrument
budget, seven punch items, forward panchanga) are genuinely fixed and verified.

No fabricated computation, grade, or coverage number appears anywhere in this run's artifact
trail. Every claim in this report is either directly live-verified against deployed prod or
explicitly marked as a gap.
