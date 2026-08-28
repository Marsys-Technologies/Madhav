---
artifact: S5_UNEXECUTED_SCENARIOS_DISPOSITION
version: "1.0"
status: SCOPE-CHANGE REQUESTS FOR CONVERGENCE — proposals only, nothing
  executed autonomously. Builds directly on S5_CONVERGENCE_HANDOFF_v1_0.md
  §2's "Non-executed / not claimed" table (the only existing enumeration —
  the 45-scenario denominator itself was never canonically itemized, which
  that handoff already names as a governance gap, not invented here).
stream_id: S5
date: 2026-08-29
---

# S5 — Disposition proposals for the unexecuted §9 battery items

The 45-scenario denominator was frozen as a bare integer at session open
with no itemized enumeration (`work_started` payload, ledger_seq 65 —
`scope_scenario_ids` is empty). There is therefore no canonical numbered
list to check items 38–45 off against; what follows is the honest content
gap against test plan §9, carried forward from the prior wrap-up session's
own table and updated with two re-proofs obtained this pass.

## Updated since the handoff (2 of 7 areas partially or fully closed)

| Area | Prior state | This pass |
|---|---|---|
| LIVE re-proof of #1631 (V3-E-019 timeline) | Merged, not yet re-proven live | **DONE.** `GET /clients/1c826d5a.../timeline`: authenticated view-grantee → 200 (over-denial bug fixed, confirmed live); unauthenticated → 307/login. See task 2 of this pass. |
| LIVE re-proof of #1630 (V3-E-020 chart_facts scoping) | Merged, not yet re-proven live | **PARTIALLY DONE, new finding.** Unauthenticated `GET /api/assets/1c826d5a.../ga_chart_facts` → 401 (auth gate confirmed firing). Authenticated → **500**, not 200: the fixed query's `WHERE chart_id = $1 AND category = $2` references a column, `category`, that **does not exist** on `chart_facts` — the live schema's actual column is `fact_category` (confirmed via `information_schema.columns`). This is NOT a regression introduced by #1630 — the route was already confirmed broken against the post-rebuild schema before this fix (its own V3-E-010 verifier said so), and #1630 correctly fixed the chart-scoping half without touching the pre-existing column-name break. Net effect is fail-closed-safe (500, no data returned, to authorized and unauthorized callers alike) but the endpoint remains non-functional. **New disposition proposal: file a fresh, narrowly-scoped fix (`fact_category` rename in this one query) as its own PR — small, mechanical, zero authorization-logic risk.** |

## Remaining gaps — disposition proposals

| # | Area (test plan §9) | Why not executed | Proposed disposition |
|---|---|---|---|
| 1 | Question-borne + retrieved-content prompt injection, plan-closure, tool-sequence anomaly, cross-chart exfiltration via the door | A real exfiltration probe risks reading the native's real chart content mid-attempt — charter-forbidden. No synthetic-only corpus built for this class. | **NEEDS INFRA** (a synthetic-chart injection/exfiltration fixture corpus, built once, reusable every session) — NOT real-chart auth; this is buildable entirely on the synthetic chart and should not wait for a native decision. Propose: a follow-on lane builds ~10-15 synthetic-chart injection probes mirroring the existing hard-stop corpus pattern. |
| 2 | B-007 destructive-path LIVE denial proof (`cockpit/clear/execute`) against a real irreversible delete | The only live target with real build state is the native's chart; a synthetic-chart equivalent was never built (no populated build state to destructively clear on 1c826d5a in a meaningful way). | **DESTRUCTIVE + NEEDS INFRA.** Two paths: (a) build a disposable, fully-built THIRD synthetic chart specifically for destructive-probe testing, so a real clear/execute can run without touching 1c826d5a (used for everything else) or the native's chart — needs a native/integrator decision to provision one; (b) accept the existing DENY-only proof (attacker gets 403, verified in the merged B-007 PR's own TDD) as sufficient and never attempt a live destructive execute at all, closing this permanently as "proven at the unit/integration rung, LIVE rung deliberately never attempted for a destructive path" — the safer default. **Recommend (b)** — the risk of a live destructive test outweighs the marginal evidentiary gain over the existing TDD proof. |
| 3 | Consent-absent / minor / withdrawal / deletion workflow, end to end, live | Surface confirmed present and correctly shaped (hash chain + append-only trigger via the INTEGRATION-rung `consent.db.test.ts` suite, 14/14 passing against a scratch DB) but the real `chart_subject_consent`/`chart_subject_consent_events` tables hold **0 rows in production** — nothing to exercise live. | **NEEDS SEEDED ROWS.** Manufacturing consent/deletion events against production to make a live test pass would itself be exactly the kind of fabrication this campaign polices against. Propose: this stays at INTEGRATION rung permanently until the FIRST real consent event occurs organically in production (e.g. an actual minor-exclusion or withdrawal request) — at which point a live re-proof becomes possible without fabrication. Not a gap to close by force. |
| 4 | Rate + spend limits on both doors, live | Not executed — would require sending enough real traffic to trip a live limit, which either costs real spend or risks tripping a limit that affects other concurrent streams/sessions sharing the same deployed service. | **NEEDS INFRA** (a dedicated, budget-capped load lane, ideally coordinated with S6 which owns performance/load testing generally — this is squarely adjacent to S6's territory). Propose: refer to S6/convergence rather than S5 attempting it solo; S5's existing INTEGRATION-rung tests (112 passing rate-limit unit tests, confirmed in the originating session) stand as the interim evidence. |
| 5 | Provider (LLM) data-posture / zero-retention checks | No code-level control found in `platform/src/lib/llm`; this is very likely a contractual/account-level setting outside this codebase's visibility. | **NEEDS INFRA** in the sense of "needs an answer from outside the repo" — not a test-writing gap. Propose: this is a documentation/confirmation ask for the native or the account owner (confirm Anthropic/OpenAI/Gemini enterprise data-retention terms are in force), not an engineering task for any stream. |
| 6 | Crash-consistent persistence, replay, semantic-hash parity, schema compatibility | Not executed this campaign by S5; this is closer to S4's pipeline-correctness territory (door parity, replay fixtures) than S5's core mandate, and S5's own restore-drill (already executed, `S5-SC-05`) covered the durability/backup half of this concern. | **NEEDS INFRA + is a referral.** Propose: refer the pipeline-replay/semantic-hash-parity half to S4 (already scoped there per the elevation crosswalk); S5's own restore-drill result stands as this stream's contribution to the persistence half. |

## Bottom line for convergence

Of the original 7-area gap list: **2 areas advanced this pass** (one fully
re-proven live, one partially — auth confirmed, a real but pre-existing,
non-security functional bug found and scoped for a small follow-on fix).
Of the remaining 5: **1 is a recommended permanent non-action** (item 2,
destructive-path LIVE proof — the TDD/unit proof already in hand is judged
sufficient and safer than a live destructive test), **1 self-resolves
organically** (item 3, consent workflow — waits for real data, not forced),
**1 is a pure external/contractual question** (item 5, provider posture),
and **2 are genuine build-more-infra asks**, one of which (item 4, rate/
spend load testing) is better owned by S6 than re-attempted by S5.

None of these are S5 blockers in the sense E-001 and B-002 are — none gate
`S5:remediation` or any frozen plan entry. They are coverage-completeness
items for convergence to prioritize or explicitly park.
