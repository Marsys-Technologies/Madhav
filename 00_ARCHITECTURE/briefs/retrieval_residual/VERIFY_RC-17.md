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

---

# VERIFY — RC-17 fix-cycle 2 (independent verifier, opus/high, NOT the implementer)

- **branch:** `res/rc17-fixcycle2-still-hallucinating`  **verified_commit:** `4c6c1ade`
- **date:** 2026-07-23
- **verdict:** **ACCEPT-WITH-CAVEATS** — the fix is real, correct in direction,
  broader than its own root-cause narrative, scope-clean, and materially better
  than fix-cycle 1; but it is a probabilistic prompt fix against a
  non-deterministic model, the prior fix-cycle-1 "ACCEPT (code-complete,
  deploy-gated re-probe)" verdict is exactly what let this defect ship, and two
  clean local runs are not proof. The post-deploy production re-probe is
  therefore **NOT an optional carry-forward this time — it is a mandatory close
  gate** (see Caveats).

## Context that governs this verdict

This is the SECOND verification of the same production correctness defect. The
fix-cycle-1 verifier (this same file, above) issued **ACCEPT** with the live
post-deploy re-probe treated as an acceptable Wave-R-C carry-condition. That
deferral is precisely the hole the regression walked through: fix-cycle-1 code
deployed to `main@7dcffa91`, was never fired against the live service before
being marked RESOLVED, and the defect resurfaced in a worse form. I will not
repeat that pattern — the deploy re-probe is escalated from "carry-forward" to
"mandatory gate."

## (a) Tests re-run by this verifier (not trusting the report)

- `rc17_temporal_anchor.test.ts`: **16/16 pass** (re-ran).
- Broader sweep `src/app/api/chat/ src/lib/pipelines/shared/ src/lib/streams/`:
  **125/125 pass** (re-ran).
- `npx tsc --noEmit`: **exit 0** (re-ran).
- Caveat on test *meaning*: every case asserts the prompt STRING changed
  (contains/omits phrases), not that the LLM stops hallucinating. Green here is
  necessary-not-sufficient; 16/16 must not be read as "hallucination eliminated."

## (b) Did the implementer genuinely reproduce the live bug first? — YES, verified

I inspected the raw SSE evidence files directly (scratchpad, not committed):
- `repro_pre_fix2.sse` contains verbatim `TEMPORAL ANCHOR:** As instructed,
  this analysis is based on your current period being **Saturn Mahadasha (MD)`.
  The literal `TEMPORAL ANCHOR:` label exists ONLY in fix-cycle-1's code — this
  is direct proof fix-cycle-1 was deployed and STILL produced the "as
  instructed" hedge (the whole premise of fix-cycle 2 is sound).
- `repro_pre_fix3.sse` contains the flat `CURRENT PERIOD:** Mercury Mahadasha /
  Saturn Antardasha` hallucination; the correct `Saturn MD / Rahu AD` appears
  exactly once (the client-only orientation JSON), never in synthesis prose.
The implementer minted their own path (`scripts/get_session_cookie.mjs` present)
and did not merely trust the conductor's report.

## (c) Does the new wording eliminate the failure mode, or just reduce it? — PARTIAL; root-cause narrative has a hole

Read the before/after anchor directly (diff of `run_adapter_dispatch.ts`). The
fix (1) removes every "treat this as" imperative frame → flat declarative
"verified fact ... NOT a user instruction"; (2) explicitly forbids the observed
hedge phrases; (3) forbids naming any other MD/AD as "actual/real/true"; (4)
renames the echoed `TEMPORAL ANCHOR:` label. Directionally correct and, crucially,
item (3) is broader than pure wording — it targets the structural cause (the
web door dumps a large raw dasha table with historical Mercury-MD-2010-2027 rows
the model latches onto).

**But the stated root cause ("`treat this as` imperative framing") is not
conclusively THE cause:** the MCP door (`prashna_ask_synthesis.ts:294`) uses the
IDENTICAL `treat this as the CURRENT period` wording and is reported (RC-17 doc
§2, corroborated by live MCP) as NOT exhibiting the defect. If that phrase were
the root cause, the MCP twin should fail too. The more likely differentiator is
the web door's contradictory-evidence bundle, which item (3) addresses — so the
fix probably works for the right reason even though the narrative overweights the
wording. This lowers confidence that the wording change alone is decisive.

## (d) Local dev-server evidence real, not fabricated? — YES, verified

`local_repro1.sse` and `local_repro2.sse` both contain
`current Vimshottari dasha period is **Saturn Mahadasha / Rahu Antardasha**`
with ZERO matches for `as instructed|as per your request|confidence note|TEMPORAL
ANCHOR|VERIFIED CHART FACT|actual current`. Files are timestamped 06:57–06:58,
after the pre-fix repros (06:50–06:51) — a coherent reproduce→fix→verify
sequence. Genuine E2E against fixed code, not a unit-test-only claim.

## (e) Can any prompt wording "fully fix" this with confidence? — NO

This is instruction-following behavior on a non-deterministic model
(`gemini-2.5-pro`). Two clean runs is weak statistical evidence: pre-fix the
failure rate was high enough to catch in 2–3 runs, so if the residual rate
merely dropped to (say) 10%, two clean runs would not reveal it. The honest
framing is **"improved, residual risk remains, needs live monitoring
post-deploy,"** NOT a clean fix. The implementer's own §9.7 says as much — I
concur and hold them to it. Ground truth independently confirmed via the live
MCP connector: for chart `1c826d5a` as of 2026-07-23 the L2 period is
`Saturn-Rahu` (Rahu AD 2023-12-04→2026-10-10), so `Mercury MD / Saturn AD` is a
genuine hallucination — and it is the NATIVE's (`482012f1`) own period, i.e. a
cross-chart-shaped wrong answer, which raises the severity.

## (f) Scope / must_not_touch — CLEAN

4 files changed, all within brief §may_touch: `run_adapter_dispatch.ts` +
its test (`platform/**`), `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (defect status),
`RC-17_...v1_0.md` (`retrieval_residual/**`). No FROZEN orchestrator/WriterBase,
no `ga_*/bo_*/ka_*/ph_*/mi_*` writer logic, no `chart_facts` semantics, no
`kala_*`/gochara serving semantics, no D-4b branch, no root `CLAUDECODE_BRIEF.md`.

## Caveats — residual risk + required follow-up (conditions of this ACCEPT)

1. **MANDATORY post-deploy production re-probe (close gate, not carry-forward).**
   After the batched deploy, fire the identical question at the DEPLOYED
   `/api/chat/consult` for `1c826d5a` **multiple times** (≥5, given
   non-determinism and the ~15min cold path) and confirm synthesis names
   `Saturn MD / Rahu AD` with no hedge and no `Mercury`. RC-17 is NOT closed by
   this branch alone — fix-cycle-1's "code-complete ACCEPT" already proved a
   single deferred re-probe is how this defect ships.
2. **Strongly recommend a production-side detector.** `containsRc17HedgePattern`
   exists only in the test file. Given a defect that recurred AFTER an ACCEPT,
   wire an output-side tripwire (that detector or equivalent) into the
   post-stream checks in `runAdapterDispatch` → `judgment_flags`, so a third
   recurrence is caught mechanically rather than by luck. This is the single
   highest-value follow-up; without it "probably fixed" stays unfalsifiable in
   production. (Implementer scoped it out per task instruction — flag it up, do
   not let it drop.)
3. **Two-door parity gap.** The identical `treat this as the CURRENT period`
   wording the fix calls dangerous still lives in the MCP door
   (`prashna_ask_synthesis.ts:294`). Either bring it to parity with the new
   declarative/anti-substitution framing or record why the MCP door is exempt
   (RC-02 territory). Leaving one door hardened and its twin carrying the exact
   phrase is an inconsistency and a latent RC-02 risk.

**Bottom line:** ACCEPT the fix-cycle-2 code as a genuine improvement and merge
it, but RC-17 does not flip to CLOSED until caveat 1 (multi-run post-deploy
re-probe) passes; caveats 2–3 are open follow-ups to record in the ledger.
