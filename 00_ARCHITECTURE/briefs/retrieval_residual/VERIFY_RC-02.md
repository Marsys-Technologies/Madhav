---
artifact: VERIFY_RC-02.md
residual: RC-02 (§H.1 crit-6 — live two-door parity, `/api/chat/consult` vs `prashna_ask`)
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
role: independent VERIFIER (opus, high effort) — NOT the implementing agent
branch: res/rc02-rc17-web-door-parity-and-dasha-fix
verified_commit: bd2c35e1
date: 2026-07-23
verdict: DOES-NOT-CLOSE on its literal DONE bar — but the specific defect it targeted
  (Part B, gate-flag disclosure gap) is genuinely FIXED, and the remaining gap is HONESTLY
  disclosed as a genuine architectural difference, NOT glossed over. RC-02 should close ONLY
  via a Resolver-dispositioned narrowing of its DONE bar (or WONTFIX-with-rationale for the
  receipt-schema-unification gap). Recommend Resolver ruling.
---

# VERIFY RC-02 — two-door parity

## Verdict: OPEN, honestly — Part B fix ACCEPTED, full parity correctly NOT claimed

The brief's literal DONE bar (§E RC-02) is: *"the two responses carry the same floor item
set + same gate flags."* That bar is NOT fully met. The implementer does not claim it is —
the report's frontmatter verdict is "STILL OPEN, but substantively improved and honestly
re-scoped," and §6 explicitly recommends a Resolver ruling rather than asserting closure.
This verifier confirms that disposition is honest and correct, and that the one component
that WAS in-scope to fix is genuinely fixed.

## Part B (gate-flag disclosure) — ACCEPTED

The concrete defect the v1 investigation surfaced was that the web door had NO
`judgment_flags` concept at all — the NO-LEAKAGE strip fired live but was only
`console.warn`'d, never disclosed to the caller, while `prashna_ask` surfaces
`no_leakage_capabilities_stripped` directly. The fix:

- adds `JudgmentFlagsPartSchema` + `judgmentFlagsPart()` to `data_parts.ts` and the
  `DataPartSchema` union;
- builds a `judgmentFlags: string[]` at the NO-LEAKAGE strip site in `consult/route.ts`,
  pushing the **literal same** flag string `no_leakage_capabilities_stripped` whenever the
  strip actually fires;
- emits a `data-judgment-flags` SSE event unconditionally (even empty — per §N.6 honest-
  empty discipline), threaded through `runAdapterDispatch` ctx.

**Genuineness check (not trusted from prose):** re-ran `no_leakage_consult.test.ts` — the
new case exercises the REAL, unmocked `filterLeakedCapabilities` (only the registry lookup
is a one-entry fixture with `calibration_context_only: true`, which the real filter reads)
and asserts `ctx.judgmentFlags` handed to `runAdapterDispatch` contains
`no_leakage_capabilities_stripped`. Passes. This proves the actual wiring, not a stand-in.
The additive web-only `citation_gate_warn`/`citation_gate_error` flags are honestly
disclosed as door-2-specific, NOT claimed as cross-door vocabulary overlap. `tsc`: clean.

## Same-floor-item-set / receipt parity — NOT achieved, honestly disclosed

The two receipts remain vocabulary-disjoint: MCP `prashna_ask` is tool-name-keyed
(`unresolved_tools`/`tools_dispatched`), web `/api/chat/consult` is floor-primitive-keyed
(`floor_item_id`). A literal set-equality diff is not well-formed without a translation
layer that does not exist, and the task was explicitly instructed NOT to unify the receipt
schemas. The report names this plainly (§5, §6) as a genuine architectural difference
tracked in part by RC-10's namespace gap — it is NOT glossed over. This is the correct
honest posture, not a false-closure.

## On the before/after floor numbers (2/16 → 8/16)

I could NOT independently re-measure the web-door floor coverage: it requires a live
Firebase `__session` cookie minted from GCP Secret Manager credentials, which is infeasible
in this non-interactive verifier environment. **However, this does not weaken the verdict,
because the numbers are not load-bearing for closure** — the report does not claim RC-02
closes on them. They are honestly framed (attributed to already-merged RC-11, not this
session's own work; remaining `empty` items attributed to `web_namespace_gap` tracked by
RC-10, not dispatch failures). I flag the numbers as UNVERIFIED-BY-THIS-VERIFIER but
NON-BLOCKING; the conductor's post-deploy Wave R-C re-probe should confirm ≥8/16 served as
the report recommends. Ledger STATE.md correctly still shows RC-02 as OPEN;
RESOLVER_RULINGS.md carries no RC-02 ruling yet — consistent with the report's
"recommend a Resolver ruling" disposition.

## Recommended disposition (brief §D.5)

RC-02 should NOT be marked CLOSED on its literal original bar. It should close via a
Native-Proxy Resolver ruling that either (a) narrows the DONE bar to "same gate vocabulary
for shared conditions [DONE] + floor coverage measured and non-regressing [pending live
re-probe]," treating full receipt-schema unification as out-of-scope; or (b) records a
formal WONTFIX-with-rationale for the schema-unification architectural gap, citing the
brief's own "Do NOT attempt to unify the receipt SCHEMA" instruction. Either is a legitimate
brief §D.5 path; a silent close or a false-parity claim is not. This verifier ACCEPTS the
report as the honest evidence base for that ruling.

## Scope / must_not_touch

Commit bd2c35e1 touches only may_touch paths (see VERIFY_RC-17.md). No FROZEN
orchestrator/writer logic, no `chart_facts` semantics, no `kala_*`/gochara, no D-4b, no root
`CLAUDECODE_BRIEF.md`. The two receipt schemas were deliberately left un-unified per the
task's explicit instruction.
