---
artifact: SAMAPANA_BRIEF (Program Wrap-Up — final open threads)
canonical_id: SAMAPANA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-27
author: Fable (Cowork planning session), closing the Elevation → UAT-DARPANA → SATYA-ŚEṢA →
  PŪRṆA-VIRĀMA → ŚODHANA → ŚODHANA-ŚEṢA arc
mode: >
  FULLY AUTONOMOUS · ONE Conductor (Sonnet) + up to two Sonnet builders (Opus only after 2
  failed verify cycles, or for Track A's log-diagnosis if it turns cross-layer) + ONE Opus
  Verifier that never writes code · no human gates · PR + auto-merge only · explicit deploy ·
  wall-clock cap 3h · truth over completion.
supersedes_open_items_from:
  - briefs/shodhana/SHODHANA_REPORT_v1_0.md §8 (deferred list)
  - briefs/shodhana/SHODHANA_SHESHA_REPORT_v1_0.md (residuals)
  - briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md (W7 PARKED-HONEST)
gate: >
  Track A REQUIRES platform-log / Cloud-Run-log read access to the amjis-mcp service (internal
  capability-route request tracing). If the executing session lacks it, Track A PARKS-HONEST with
  its hypothesis intact and Tracks B/C proceed independently — do NOT guess at the log evidence.
---

# SAMĀPANA — the last threads

## §0 — State of the program (the one paragraph a future session reads first)

The full arc is closed and live-verified: Elevation register CLOSED, LLM-consumption register
ADDRESSED-v1.1, root CLAUDECODE_BRIEF COMPLETE, production == main HEAD (`3a0a58d0` at
ŚODHANA-ŚEṢA close). Bodha (L2) has been rebuilt by the native for both canonical charts and
INDEPENDENTLY VERIFIED here (2026-07-27): DEFECT-001 orphan rate 0.3% on both (482012f1:
230/71293; 1c826d5a: 234/71750), two-pass ~81%, citation 100%, zero authority/narration traps,
Yogi/Avayogi live and arithmetic-exact — so the parked Bodha-rebuild authorization is CLOSED as
resolved-and-verified, NOT executed by any campaign. Three genuine threads remain, scoped below.
This brief closes them; after it, the program has no open campaign.

## §1 — Track A: W7 flagship final gap (the one substantive defect left)

**State (from PŪRṆA-VIRĀMA):** the W7 substance-inline digest was fixed from a real 0/13 bug
(digest reading response data one level too shallow) to a genuine n=3 sealed-harness median of
**9/13 (69%)**, short of the 12/13 bar. The remaining gap is precisely diagnosed but unproven:
**7 of 13 families serve empty via the internal capability route, while identical EXTERNAL tool
calls return real data for those same families.** A concurrency hypothesis was tested and made it
worse (regressed to 2/13) — correctly reverted. The residual is a routing/context defect in the
internal capability-invocation path, needing request-trace logs to localize.

**Method (log-gated — see frontmatter):**
1. Reproduce the 9/13 live; capture which 7 families are empty (likely the lower-Ω2-tier families
   the digest composes last).
2. With platform-log access: trace ONE internal capability-route call for an empty family vs the
   equivalent external call for the same family — the divergence point (auth/context propagation,
   a dropped chart_id/ayanamsha in the internal envelope, a swallowed error, or a
   budget-trim-before-compose on the internal path) is the bug.
3. Fix at the cause; add a regression test that drives the internal route for a known-populated
   family and asserts parity with the external call. Re-run n=3 sealed harness (UNMODIFIED
   harness — rail).
**Acceptance (Verifier, live):** internal-route families reach parity with external for the same
chart; n=3 median improves materially above 9/13 with NO regression; if the 12/13 bar is still not
reached, PARK-HONEST with the new median and the residual named — a real improvement honestly
disclosed beats a forced number (this is the W7 pattern already on record).
**If no log access:** PARK-HONEST immediately with the hypothesis above; do not fabricate trace
evidence. Flag that a session with amjis-mcp Cloud-Run log access is the precondition.

## §2 — Track B: verbosity vocabulary + the beyond-acharya reading contract

**State (verified in code + live, 2026-07-27):** "verbosity" is TWO knobs and they are conflated:
- `verbosity: 'concise' | 'detailed'` (registry_bridge.ts `VERBOSITY_ZOD`, L386;
  `resolveVerbosityMaxKb` L382) — a BYTE-CEILING, not a summarizer. `'detailed'` (default) is
  already the maximal/full form; `'concise'` only tightens size and never drops hardFloored
  findings. NO lossy behavior here.
- `response_format: 'full' | 'summary' | 'digest'` on `bodha_chart_digest_get` / get_signals
  (registry_bridge.ts ~L1651-1694) — **defaults to `'summary'` (top-10 signals)**, and this IS a
  genuine content reduction. `bodha_chart_digest_get` is the MANDATORY first call of every reading
  (B.11), so today every reading opens with a 10-signal digest unless overridden to `'full'`.
- The MC-004/006 `verbosity: 'summary'` "guaranteed-fits" projection referenced in the ŚODHANA
  brief was NEVER BUILT and was only ever a FLOOR for file-access-less endpoints.

**The native's directive:** a beyond-acharya-grade deep dive must be ELABORATE/maximal, never
summary. Implement as:
1. **Add a named maximal tier.** Extend `VERBOSITY_ZOD` to `'concise' | 'detailed' | 'exhaustive'`
   (`'exhaustive'` = `'detailed'` ceiling AND opts every digest/signal sub-call to its full form —
   `response_format:'full'`, `bodha_chart_digest_get mode:'full'`, get_signals full). Back-compat:
   `'detailed'` and omitted unchanged byte-for-byte.
2. **A deep-dive reading contract binds to maximal by NAME.** A single `reading_depth:
   'standard' | 'deep_dive'` (or reuse T5's reading_checklist context) that, when `deep_dive`,
   deterministically sets `verbosity:'exhaustive'` + `response_format:'full'` + digest `mode:'full'`
   + drives the dossier to 100% — so a caller requests depth once, not four flags.
3. **Hard-guard the lossy forms from deep dives.** IF the MC-004/006 guaranteed-fits summary form
   is ever built (Track C optionally builds it), it MUST refuse to apply when `reading_depth =
   deep_dive` (assert in code + test). A deep dive can never be silently summarized.
4. **Flip the sharp edge:** `bodha_chart_digest_get`'s default-`'summary'` is a footgun for the
   mandatory first call. EITHER change the default to `'full'` for that tool, OR make the deep-dive
   contract's first call always pass `'full'`. Prefer the contract-side fix (less blast radius);
   document the default's footgun-nature either way.
**Acceptance (Verifier, live):** a `reading_depth:deep_dive` call to assess_wealth + the mandatory
digest returns the full signal set (not top-10) and the widest ceiling; `'exhaustive'` is a live
enum value; a deep-dive call cannot be routed through any summary form (test proves refusal);
`'concise'`/`'detailed'` behavior byte-identical to today (no regression on the existing knob).

## §3 — Track C: hygiene closes

1. **Close the Bodha-rebuild park (docs only).** Annotate PŪRṆA-VIRĀMA §3 Decision-2 and the
   register: authorization CLOSED — native-executed rebuild, independently verified 0.3% orphan on
   both charts (evidence: build_ids 27de8de4 / 2962fb9d, scored 2026-07-27 03:54 / 2026-07-26
   07:47). No campaign rebuild was or will be executed. The DAG-doc-drift precondition is now moot
   for authorization purposes (still worth reconciling for future maintainability — note, don't
   gate).
2. **Delete-or-derive `unresolved_constituent_facts_count` (GA.1 class).** The stored scorecard
   field reads 0 while live orphan is 0.3% — a stored-vs-live disagreement the alert already
   discloses. Per ŚODHANA T2's own recommendation: remove the stored field OR always derive it
   live at serve time. One-line-class fix; kill the disagreement, not just this instance.
3. **(Optional, if Track B lands with budget) the MC-004/006 guaranteed-fits summary form** — a
   `reading_depth:'compact'` projection (prose + verdicts + top-N grounded signals, hard-capped
   under the MCP envelope) for file-access-less endpoints, built WITH the §2.3 deep-dive guard
   from the start. If budget is tight, defer and note — this is a nice-to-have floor, not a defect.

## §4 — Explicitly deferred (named so they are not silently dropped, NOT in scope here)
- `mimamsa_lel_query`'s non-functional `query`/`offset` params (ŚODHANA T9 bonus finding) — a new
  investigation, its own small ticket.
- WL-8 margin/retention native data — awaits the native supplying figures; not a code item.
- DAG-doc reconciliation to the real ~25-writer roster — maintainability, not correctness; no
  longer gates anything now that the Bodha park is closed.

## §5 — Rails
Parent SHODHANA_BRIEF §5 rails apply verbatim: untouchables (kala_gochara_windows data,
build_substep_progress, sealed evaluator harness — Track A re-runs it, never modifies it);
PR + auto-merge only (main protected); explicit amjis-mcp deploy using the merged-main →
real-authenticated-verify → canary → cutover discipline (the ŚODHANA-ŚEṢA stale-pinned-traffic
rail is now standing — verify production serves the NEW revision with a real authenticated call
before declaring deploy done); preserve-list regression check post-merge; no fabrication.

## §6 — Close
Nothing DONE until the Opus Verifier accepts live post-deploy (four dispositions, no "passed with
caveats"). Close artifact: `SAMAPANA_REPORT_v1_0.md` — Track A/B/C dispositions, the closed
program-state table (every campaign + its final state), and the two remaining deferred items (§4)
with their release conditions. Register → ADDRESSED-v1.2. Worktrees/branches cleaned, production
== main confirmed. After this report, the program has no open campaign — only the two §4 tickets,
each independently launchable when the native chooses.

## §D — Kickoff prompt (single paste)

```
You are the CONDUCTOR of SAMĀPANA (program wrap-up), FULLY AUTONOMOUS. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/samapana/SAMAPANA_BRIEF_v1_0.md — this brief;
    §5 rails bind you;
(2) briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md §3 (Decision 2) + the W7 PARKED-HONEST section;
(3) briefs/shodhana/SHODHANA_SHESHA_REPORT_v1_0.md (residuals) + SHODHANA_REPORT_v1_0.md §8.
Track A (W7 internal-route diagnosis) REQUIRES amjis-mcp Cloud-Run log access — if this session
lacks it, PARK Track A honest with its hypothesis and run Tracks B/C only; do NOT fabricate trace
evidence. Track B (verbosity: add 'exhaustive' tier + a reading_depth:deep_dive contract that
binds maximal + hard-guards deep dives from any summary form + fixes bodha_chart_digest_get's
default-'summary' footgun) and Track C (close the Bodha-rebuild park as native-verified; delete-
or-derive the stored unresolved_constituent_facts_count GA.1 field) proceed in parallel Sonnet
builders in .worktrees/samapana-*. Opus only after 2 failed verify cycles or for Track A's log
diagnosis. ONE Opus Verifier accepts every item live post-deploy — four dispositions, no "passed
with caveats". PR + auto-merge only; deploy amjis-mcp explicitly and CONFIRM production serves the
new revision via a real authenticated call before declaring deploy done (the stale-pin rail).
Untouchables: kala_gochara_windows data, build_substep_progress, the sealed evaluator harness
(Track A re-runs, never modifies it). Never touch root CLAUDECODE_BRIEF.md. Wall-clock cap 3h.
Close with SAMAPANA_REPORT_v1_0.md, register annotated ADDRESSED-v1.2, worktrees cleaned,
production == main. Truth over completion. Begin.
```

---
*After SAMĀPANA the ledger reads: everything the two registers named is fixed-and-verified or
honestly parked with a release condition; Bodha is rebuilt and verified; deep dives are maximal
by contract, never summarized; and the only open tickets are two the native can pick up at will.*
