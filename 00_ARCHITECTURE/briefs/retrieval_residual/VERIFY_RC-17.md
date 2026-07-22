---
artifact: VERIFY_RC-17.md
residual: RC-17 (new — web-door `/api/chat/consult` dasha-anchoring hallucination)
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
role: independent VERIFIER (opus, high effort) — NOT the implementing agent
branch: res/rc02-rc17-web-door-parity-and-dasha-fix
verified_commit: bd2c35e1
date: 2026-07-23
verdict: ACCEPT (code-complete + independently verified; final live post-deploy re-probe
  deploy-gated to Wave R-C — the same accepted carry-condition class as RC-11/CR-118,
  VERIFY_RC-11.md §5, not a shortcut)
---

# VERIFY RC-17 — web-door dasha-anchoring hallucination

## Verdict: ACCEPT

RC-17 is a genuine, independently-confirmed defect; the fix is a faithful port of the
already-accepted `2df42b61` temporal-anchor pattern; the fix's data source is confirmed
populated in production (so the fix is effective, not a silent no-op); regression tests
cover the exact live symptom; tsc + the touched test scope are green. The only unmet
element — a live re-probe of the *deployed fixed* web door — is legitimately deploy-gated
and out of this branch's scope, identical to the carry-condition Wave R-C already accepted
for RC-11.

## (a) Was the hallucination genuinely reproduced/confirmed before the fix?

YES — confirmed by independent live ground-truth verification this session, not merely
trusted from the implementer's transcript.

- **L1 deterministic ground truth (live MCP connector, `ganita_dashas_get`, chart
  `1c826d5a`, as_of 2026-07-23, lahiri_chitrapaksha):** current Mahadasha = **Saturn**
  (2010-04-23 → 2029-04-23); current Antardasha = **Rahu** (2023-12-04 → 2026-10-10),
  `verification_pass_status: two_pass_verified`. → The correct current period is
  **Saturn MD / Rahu AD**. The web synthesis's "Mercury Mahadasha" is therefore
  factually wrong against the deterministic layer — a real hallucination, not a phrasing
  quibble.
- **Orientation block (live `get_chart_orientation` v3, same chart):**
  `chart_header.current_maha_antar = "Saturn MD / Rahu AD"` — exactly the string the
  report says the response's own `data-orientation` block carried, i.e. the response
  contradicted its own grounding data. Confirmed.
- **The "coincidence" note independently corroborated:** the fabricated string
  "Mercury MD / Saturn AD" is exactly the NATIVE chart's (`482012f1`) current period —
  verified live (`ganita_dashas_get`, 482012f1: MD Mercury, AD Saturn 2024-12-08 →
  2027-08-18, citation `L2.Mercury-Saturn`). The report flags this as an unverified
  coincidence and explicitly does NOT claim a causal mechanism — appropriate epistemic
  discipline; not over-claimed.
- Two documented pre-fix live reproductions with query_ids (`05baeb74…` original
  investigation; `86d2f98e…` independent re-repro this session against deployed
  `amjis-web-01103-nq7`). I could not re-fire those exact stale queries (they require a
  Firebase `__session` cookie minted from GCP Secret Manager, infeasible in this
  non-interactive verifier environment, and the deployed service still carries the bug),
  but the underlying factual contradiction they assert is fully verified above.

## (b) Is the fix analogous to commit 2df42b61?

YES — a faithful port, confirmed by diffing both implementations.

- `2df42b61` (W6.3, MCP door) added `formatTemporalAnchor` in `prashna_ask_synthesis.ts`:
  an explicit "today's date + `chart_header.current_maha_antar`, treat as CURRENT"
  anchor, degrading honestly when unresolved.
- RC-17 adds `formatConsultTemporalAnchor` + `buildConsultSystemContent` in
  `run_adapter_dispatch.ts` with the SAME phrasing ("CURRENT period, not upcoming or
  past"; "could not be resolved" on the honest-degrade path — string-identical to the
  reference), the SAME unconditional lead placement ahead of the bundle, and honest
  degradation. Pure functions, no hidden `Date.now()`.
- **Effectiveness check (adversarial — the key failure mode for this class of fix):** the
  fix reads `orientation?.chart_header?.current_maha_antar ?? orientation?.dasha_context?.
  current_maha_antar ?? null`. If `orientation` were unpopulated at this call site the fix
  would silently always take the "unresolved" path and never actually fix the
  hallucination. Verified it is NOT: `ChartOrientation` (`src/lib/retrieval/orientation.ts`)
  defines `chart_header: ChartHeader | null` and `dasha_context.current_maha_antar`; it is
  built by `buildChartOrientation(chartId)` and awaited in `consult/route.ts` (L899)
  BEFORE `runAdapterDispatch` is called (L1118); and my live orientation query proves
  `chart_header.current_maha_antar` is populated ("Saturn MD / Rahu AD") in production. The
  fix will feed the correct anchor to the synthesis model — it is effective.

## (c) Regression test coverage?

YES. `rc17_temporal_anchor.test.ts` — 8 cases, all passing (re-run by this verifier: 8/8).
Includes an explicit guard for the exact live symptom (correct string present AND
`"Mercury MD"` absent), a silent-substitution guard (correct anchor even when the raw
bundle legitimately mentions other historical dasha rows), an honest-degrade guard (no
fabricated `MD / … AD` when null), a purity guard, and a wiring guard proving the anchor
reaches `systemContent` even when all other sections are empty (the prior
collapse-to-`undefined` path). This verifier re-ran the full touched scope
(`rc17_temporal_anchor` + `data_parts` + `no_leakage_consult`): 46/46 pass;
`tsc --noEmit`: exit 0, clean.

## Scope / must_not_touch

Commit bd2c35e1 touches only may_touch paths (platform source + tests + defect register +
`retrieval_residual/` briefs). No FROZEN orchestrator/WriterBase/`*_writers` logic, no
`chart_facts` semantics, no `kala_*`/gochara serving semantics, no D-4b branch, no root
`CLAUDECODE_BRIEF.md`. `run_adapter_dispatch.ts` is serving-pipeline code, not writer-build
logic. CR-125 recorded RESOLVED in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (v3.12), coherent
and cross-linked.

## Residual / carry-condition

The one honestly-unverified element is a live re-probe of the DEPLOYED fixed web door.
This branch is not deployed; batched deploy is a conductor action per brief §I. This is the
identical carry-condition Wave R-C already accepted for RC-11 (VERIFY_RC-11.md §5). RC-17
closes as code-complete; the conductor should, after the batched Wave R-C deploy, re-fire
the identical question at `/api/chat/consult` for chart `1c826d5a` and confirm the synthesis
text no longer contradicts its own `data-orientation` block.
