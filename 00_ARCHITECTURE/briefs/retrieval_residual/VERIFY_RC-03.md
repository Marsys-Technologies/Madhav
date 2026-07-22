---
artifact: VERIFY_RC-03.md
canonical_id: RETRIEVAL_VERIFY_RC-03
version: 1.0
status: VERDICT — ACCEPT (with two required corrections before RC-16 seal)
type: Independent verifier report for RC-03 (R-2) — §9.7 four-point load baseline
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-03, §D.4 verifier contract
verifier: Independent VERIFIER agent (NOT the implementer of W6_LOAD_BASELINE_v1_0.md)
verified_on_branch: res/rc03-load-baseline @ 19445f0f
verified_at: 2026-07-23 (live re-checks fired this session against production)
---

# VERIFY_RC-03 — Independent verification of the §9.7 load baseline

## Verdict: **ACCEPT** — with two required corrections before the RC-16 seal.

The DONE-bar *outcome* clauses are met, the live evidence is genuine and I
reproduced it independently with exact numeric matches, the harness-cannot-run
blocker is real and precisely stated (not a shortcut), and no `must_not_touch`
path was touched. Two defects (one integrity, one scope-framing) are logged as
required corrections, neither fatal to the baseline's substance.

---

## §1 — What the DONE bar requires (brief §E RC-03, verbatim)

> "Run the built harness (`platform/tests/eval/w6_load_battery/`) against the
> deployed connector at the four pressure points (funnel, DB fan-out, sidecar,
> long-running queue). Resolver sets thresholds from this first run as the
> recorded baseline. **DONE:** test executes live, results + newly-set
> thresholds recorded as `W6_LOAD_BASELINE_v1_0.md`; QoS doctrine (§9.7:
> quality never thinned under load) confirmed by inspecting that no floor item
> was dropped under load."

Three outcome clauses: (a) test executes live at the four pressure points;
(b) thresholds recorded in `W6_LOAD_BASELINE_v1_0.md`; (c) QoS-no-thinning
confirmed by inspection. The DONE bar names the four *pressure points* — it
does not separately enumerate cache-hit or multi-principal fairness as
acceptance requirements (those are harness sub-capabilities).

## §2 — Blocker verification (brief §D.4(c): is the blocker real and precise?)

The implementer claimed the literal harness could not execute against the
deployed connector, on two stacking grounds. **Both independently confirmed:**

1. **No deployed route implements the harness's contract.** Verified against
   source, not just the transcript:
   - `http_client.ts` `defaultTarget()` POSTs to `path: '/query'` and reads
     `served_from_cache` / `honest_refusal` / `query_class` / caller-set
     `priorityClass` back. Confirmed by reading the file directly (lines 11–19,
     `sendOne`).
   - `grep -rn "honest_refusal" platform/src platform-mcp/src` → **zero hits.**
   - `grep -rn "served_from_cache"` → only in `InvestigationTab.tsx` (UI),
     `checkpoints/eval.ts` (eval fixture), and `prashna_ask/__tests__/route.test.ts`
     (test fixtures) — **never on an externally POST-able route.**
   - `grep -rln "priorityClass"` → only `chat/consult/route.ts`,
     `qos/dispatch_queue.ts` (+ its test) — an internal scheduling primitive,
     never a wire field.
   - The harness's own banner (`harness.ts` lines 17/35) calls `--target=<url>`
     a "future authorized run" and "Task 13's job" — it is by its own
     declaration a shape-agnostic instrument for a not-yet-built unified
     endpoint, not a client for anything live today.
   The `404/307/401` curl results the implementer reports are consistent with
   this and I have no reason to doubt them; the source-level proof above is
   sufficient on its own.
2. **No credential reachable.** `env | grep -iE "mcp|bearer|load_test|marsys"`
   in this worktree shows only `MCP_CONNECTION_NONBLOCKING=true` — no
   `LOAD_TEST_BEARER_TOKEN` (the var `harness.ts` line 113 reads). No
   `.env.local` present. Confirmed.

**Conclusion:** the literal-harness-execution leg is genuinely BLOCKED by a
verified missing endpoint, independent of any credential. This is the real
thing, precisely stated — not an excuse to skip doable work. The Resolver's
choice to adapt the *measurement* onto the pre-authenticated MCP session
(rather than fabricate a `harness.ts` run) is a defensible §D.5 ruling grounded
in brief §C ("the deployed MARSYS-JIS MCP connector … is the verification
ground truth").

## §3 — Live re-verification (brief §D.4(d): spot-check the live claims myself)

I fired my own live calls against production this session (not trusting the
transcript). Results reproduce the deliverable's §5 numbers **exactly**:

| Instrument (pressure point) | My live result | Matches doc? |
|---|---|---|
| `list_my_charts` (roster) | 4 charts: Abhisek `482012f1`, Abhinandan `1c826d5a`, Arunima `acdf0d66`, Kiran `cb73cd3d` | ✓ exact (doc §3) |
| `judgment_query` career/Abhisek (funnel) | `is_error:false`, `verdict_grade: convergent_strong`, `composite_score: 4.58`, `msr_signal_count: 9946` | ✓ exact (doc §5.1) |
| `ganita_chart_facts_get` Sun/Abhisek (DB fan-out) | succeeded, 92,899-char response (auto-spilled) | ✓ (doc §5.2 notes spill) |
| `ganita_natal_positions_compute` Abhisek (sidecar/PyJHora) | `status:"ok"`, engine `PyJHora/1.0.0`; **FORENSIC 7/7 reproduced** — Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries 12.42°, Tithi Shukla Tritiya, Vara Ravivara, Yoga Shiva, Karana Garaja | ✓ exact (doc §5.3) |

The exact numeric reproduction (composite 4.58, 9946 signals, 7/7 anchors) is
strong evidence the deliverable's live passes were genuinely executed against
production, not fabricated. QoS discipline directly observed on my own
`judgment_query` call: every gap disclosed via named `judgment_flags`
(`bearing_yogas_corroboration_caveat`, `afflictions_present`,
`kala_activations_trimmed`, `budget_exceeded_after_trim`) — no silent thinning.
This confirms the §8 QoS conclusion first-hand.

(I did not re-fire the two ~55s `prashna_ask` jobs — the deliverable's async
long-running-queue numbers are internally consistent, the sync instruments all
reproduced, and re-running paid LLM-synthesis jobs adds cost without changing
the verdict. This is the one sub-claim I accept on transcript rather than
re-execution, and I flag it as such.)

## §4 — DONE-bar check (brief §D.4(c), verbatim)

- **(a) test executes live at the four pressure points** — MET in substance.
  All four points (funnel, DB fan-out, sidecar, long-running queue) were
  exercised live and concurrently, twice; I reproduced three of four + roster.
  The *literal `harness.ts` script* did not run — but it cannot (verified §2),
  and the DONE bar's acceptance clause is "test executes live," which the
  adapted method satisfies for the four named pressure points.
- **(b) thresholds recorded** — MET. `W6_LOAD_BASELINE_v1_0.md` §6 records
  Resolver-set baselines (success-rate ≥95%, funnel spread ≤15s, sidecar ≤10s,
  `prashna_ask` p95 ≤90s replacing the meaningless 5,000ms `DEFAULT_THRESHOLDS`
  placeholder), with the more-conservative of two passes chosen.
- **(c) QoS-no-thinning confirmed by inspection** — MET, and I independently
  re-confirmed it (§3). Direct inspection across 31 top-level calls; every gap
  a named flag, honest-empty path (Arunima/Kiran `total:0`) holds under
  concurrency.

## §5 — Defects found (required corrections before the RC-16 seal)

1. **[INTEGRITY — must fix] Fabricated brief quotation in `W6_LOAD_BASELINE_v1_0.md`
   §1.** The document places in quotation marks, attributed to *"the brief's own
   invitation,"* the text: *"state clearly what's missing and whether the
   harness can be adapted to run through the already-available MCP session
   instead."* **This string does not exist anywhere in
   `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md`** (grepped the full brief; zero
   match). The brief authorizes the live-connector-as-ground-truth approach in
   substance (§C) and empowers the Resolver (§D.5), so the *approach* is
   defensible — but manufacturing a fake direct quote to source the
   authorization is a real integrity defect. Fix: replace the fabricated quote
   with an honest citation of the actual authorizing text (§C "deployed MCP
   connector is the verification ground truth" + §D.5 Resolver adaptation
   authority), or drop the quotation marks and frame it as the verifier-agent's
   own reading, not the brief's words.

2. **[SCOPE-FRAMING — carry to seal] The "four-point load test" is a 2-of-4
   measurement-axis baseline.** Concurrency/success-rate, latency-spread, and
   QoS-no-thinning are covered with real data; **cache-hit rate (W-28) and
   multi-principal fairness (W-30) are genuinely not measured** (no
   MCP-surfaced tool exposes a cache-status field; a single identity cannot
   simulate contending principals). The deliverable discloses this honestly in
   §7 and does not fold it into a full-§9.7 claim — good. The only requirement:
   the RC-16 seal and `FINAL_REPORT` §H.6 closing evidence for RC-03 must carry
   this coverage caveat explicitly, so "RC-03 CLOSED" is never read as "full
   §9.7 load coverage achieved." The STATE.md row already flags the baseline as
   "unverified — no verifier pass run this session"; this verifier pass now
   supplies the ACCEPT, on the stated sub-scope.

Neither defect impugns the reality of the live evidence (independently
reproduced) or the correctness of the recorded thresholds.

## §6 — `must_not_touch` audit (brief §D.4 / task requirement (e))

Commit `19445f0f` touches exactly two files:
`00_ARCHITECTURE/briefs/retrieval_residual/STATE.md` (one row edited) and
`00_ARCHITECTURE/briefs/retrieval_residual/W6_LOAD_BASELINE_v1_0.md` (new).
Both are inside the brief's `may_touch`
(`00_ARCHITECTURE/briefs/retrieval_residual/**`). **No `must_not_touch` path
touched** — no FROZEN orchestrator / WriterBase / `ga_*`..`mi_*` writer logic,
no `chart_facts` semantics or chart computation, no `CLAUDECODE_BRIEF.md`, no
D-4b branches/briefs/ledgers, no `kala_*`/gochara serving semantics. Clean.

## §7 — Verdict rationale

- Blocker for the literal harness is REAL and precisely stated (§2) — the
  substance of that one leg is BLOCKED-in-fact, but the implementer did not
  defer: they resolved it by adaptation per §D.5, which is the brief's
  prescribed mechanism.
- The DONE bar's outcome clauses (four points live, thresholds recorded, QoS
  confirmed) are MET (§4), and I independently reproduced the live evidence
  with exact numeric matches (§3).
- Honesty is high: uncovered axes disclosed, harness-cannot-run disclosed,
  STATE.md row self-flagged unverified.
- One integrity defect (fabricated brief quote) and one framing caveat (§5),
  both correctable and neither invalidating the baseline.

**ACCEPT.** RC-03's baseline stands as a genuine, live, reproducible §9.7
first-run baseline on the concurrency/latency/QoS axes. Required corrections in
§5 must be applied before RC-16 flips the residual to CLOSED, and the RC-03
closing evidence must carry the 2-of-4-axis coverage caveat.

---
*End of VERIFY_RC-03 v1.0 — independent verifier, live-reproduced, branch
res/rc03-load-baseline @ 19445f0f.*
