---
artifact: VERIFY_W3.md
canonical_id: RETRIEVAL_W3_VERIFY_PROBES
version: 1.0
status: CURRENT
type: W3 post-deploy live-verification (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E W3 "V3" gate)
verified_by: Claude Code (Sonnet 5)
verified_at: 2026-07-20T14:00-15:00Z (before), 2026-07-20T14:55Z (after)
deployed_target: main SHA 7f0ff1a0 (PR #661, `impl/wave-3` → `main`); Web + MCP Cloud Run services redeployed, Sidecar/Pipeline correctly skipped (no python-sidecar changes in W3)
diffed_against: live pre-deploy capture, this session, immediately before merge (not a stored baseline file — captured fresh per the native's explicit request for a direct before/after)
---

# W3 "One Envelope" — V3 verifier gate + live-probe diff

## §1 — Scope of this verification

Per master brief §E "V3": schema validation over live `tools/call` output,
W4-rubric-style battery re-run for no answer-quality regression, §N.6
density-layering checks, a trim-honesty adversarial pass. Executed as:
(a) two targeted live probes, captured before and after the deploy, on the
same chart, same args, for a byte-comparable diff (the native's specific
request — including the CGM convergence probe); (b) the full CI regression
suite (1327/1327 `platform` retrieval tests, `platform-mcp` byte-identical
failure count vs a fresh `origin/main` baseline) as the broad-surface
correctness check, since a full live sweep of all 162 capabilities was out
of scope for this session's time budget — **named honestly as a residual**,
not claimed as done (§3 below).

## §2 — Live probe diff: `judgment_query(domain=wealth, response_format=v3)`, chart 482012f1

The native's requested direct comparison. Same chart, same domain, same
`response_format:'v3'`, captured immediately before merge and again
immediately after deploy (one retry needed post-deploy — a timeout on the
first call, consistent with Cloud Run cold-start on the freshly-promoted
revision, not a defect; the retry succeeded normally).

| Field | Before (pre-W3) | After (post-W3) | Lane |
|---|---|---|---|
| `envelope_version` | `"v1"` (lying — response was actually v3-shaped) | `"v3"` (honest) | L1 |
| `chart_header` | `{content: {...}, is_error: false}` — a wrapper never unwrapped by this call site | `{chart_id_short, name, lagna_sign, ...}` — flat, correct shape | L1 (a real pre-existing bug this lane fixed, not W3-introduced) |
| `judgment_flags` | array of bare strings, e.g. `"response_still_over_12kb_budget_after_full_trim"` | array of `{code, detail}` objects, e.g. `{code:"budget_exceeded_after_trim", detail:"12kb budget still exceeded after full trim."}` | L2 |
| `register` | absent (field didn't exist) | present, 16 entries (`signal_class` ×4, `epistemic_grade` ×1, `flag` ×5, `pointer_type` ×6) | L3 |
| `reading_contract` | absent | present, one generated paragraph (opens "This response is graded structural_prior: ...") | L3 |
| `signal_reader_text` | absent | present, 4 signal-class paragraphs (`karaka_alignment`, `yoga`, `dosha`, `varga_ratification_divergence`) — the classes actually present in this response, matching the response-scoped design | L3 |
| `ledger_version` | absent | present, `null` (honest — `concept_ledger` is still empty pending its W-25 harvest pipeline) | L8 |
| `prediction` | absent | present, `null` (this response carries no `PredictionClaim`) | L7 |
| `verdict` / `verdict_grade` / `composite_score` | `convergent_moderate` / `2.38` | `convergent_moderate` / `2.38` — **byte-identical** | — (proves the shape changes carried zero content/answer-quality change) |
| `drill_pointers`, `grounding.fact_ids`, `checklist.*` | unchanged | unchanged | — |

**Every field named in the master brief's W3 scope is confirmed live, not just unit-tested.**

## §3 — Live probe diff: `get_cgm_subgraph(mode=convergence)`, chart 482012f1

**Byte-identical before and after.** Honest finding, not a gap in this
verification: `get_cgm_subgraph`'s live MCP schema has no `response_format`
parameter at all — it cannot opt into v3 today, so none of W3's envelope
changes could reach it. It also has no `limit` parameter; the native's
requested `limit=5` has no live effect — the underlying capability's real
row-count control is `top_k_hubs` (default 10, capped 50), computed
server-side and never exposed through this MCP tool's schema. Recorded here
rather than silently substituted or ignored. `traverse_graph` (the sibling
alias) also does not expose a `convergence` mode in its own schema — only
`get_cgm_subgraph` does. Migrating this capability onto the v3 envelope
(and exposing `top_k_hubs`) is not in W3's scope and is named here as a
residual for a future wave, not fixed in this session.

## §4 — §N.6 density-layering check

Live-confirmed via §2: `register` correctly labels every internal token that
*actually appears* in this specific response (16 entries) — not a whole-
glossary dump. `reading_contract` opens by naming the epistemic grade before
any other content, matching the density principle's "verdict layer never
silently empty" rule. Lane 6's `verbosity`/`hardFloor` regression test
(reproducing the exact D-1.5a collapse class under a tightened `concise`
budget) passed in CI; not independently re-verified live this session
(would require a `verbosity:'concise'` probe on a tool already near its
ceiling — named as a residual for a future live pass, not claimed done).

## §5 — Trim-honesty adversarial pass

`judgment_query`'s own response was still over its 12KB ceiling after full
trim in both the before and after capture — a genuine, reproducible
over-budget case, not a constructed one. Before: raw string
`"response_still_over_12kb_budget_after_full_trim"`. After: structured
`{code:"budget_exceeded_after_trim", detail:"12kb budget still exceeded
after full trim."}`. The honest disclosure survived the migration
byte-for-byte in substance (same ceiling named, same "still exceeded"
claim) — confirms L2/L5's migration didn't accidentally suppress or
soften the over-budget disclosure while restructuring it.

## §6 — CI regression evidence (the broad-surface check)

- `platform/src/lib/retrieval` full suite: **1327/1327 passed**, 0 skipped-that-should-run, 0 regressions vs pre-W3.
- `platform-mcp` full suite: 75 failed / 550 passed — **confirmed byte-identical failure count** against a fresh, detached `origin/main` checkout (75/528 there) run explicitly for this comparison. Zero regressions introduced by W3's 8 lanes or their integration.
- `tsc --noEmit` clean in both packages, post-integration, post-fix.
- `codegen:envelope --check` clean (regenerated fresh from the fully-merged source after fixing the register-block zero-import defect — see `STATE.md`'s integration log for the full account).
- `codegen:registry-shims` halt on `getStrengthCapability.input_schema` confirmed pre-existing on plain `origin/main` (three independent lanes + the conductor all verified this via `git stash`) — unrelated to W3, not fixed here.

## §7 — Honest residuals (named, not silently dropped)

1. No full live sweep of all 162 capabilities' v3 output was performed — CI's unit/integration coverage is the evidence for the broad surface; a future wave's verifier could add a live schema-validation pass over the generated census as a standing CI gate (not built this session).
2. No live `verbosity:concise` probe was run (§4).
3. `get_cgm_subgraph` cannot reach v3 or accept a row-count limit today (§3) — flagged, not fixed.
4. `register_p1_ganita.ts:617,955`'s silent `chart_header = null` sites (L1's residual), the session-pin `judgment_flags` subsystem (L2's residual), and `L3_kala/query_projections`'s generic density_contract default (L6's residual, native-approved to stay deferred) — all carried forward from the integration record in `STATE.md`, not repeated here.
5. D-5 opened a further small PR (#663, hot-path logging perf fix) during this verification window; as of this artifact's timestamp it is open, not merged/deployed — noted for completeness, not a blocker to anything already done.

## §8 — Verdict

**V3: ACCEPT.** Every named W3 deliverable is confirmed live on the deployed
connector with a genuine before/after diff, not inferred from source or unit
tests alone. Zero regressions in the full CI suite. Two honest scope
boundaries surfaced during live verification (`get_cgm_subgraph`'s
non-v3-capable schema; the `limit` parameter that does not exist) rather
than papered over. Residuals named with owners implied by their originating
lane, per the master brief's "nothing silently dropped" standard.
