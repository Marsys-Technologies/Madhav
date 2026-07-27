---
artifact: SHODHANA_REPORT (Consumption-Register Remediation Campaign — Close Report)
canonical_id: SHODHANA_REPORT
version: 1.0
status: CLOSED
closed: 2026-07-27
author: Conductor (Opus, autonomous session) + 11 Sonnet/Opus track builders + 2 Dvārapāla decisions
  + 1 Opus Verifier, per SHODHANA_BRIEF_v1_0.md
source_documents:
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md
---

# ŚODHANA — Close Report

## §0 — Outcome in one paragraph

Of the 34 register defects (MC-001..034) plus WL-1..8, **27 are VERIFIED-FIXED on live production**,
3 are VERIFIED-NO-DEFECT (Phase A resolved the dual-surface question and two stale-surface
claims), 9 are legitimately PARKED-HONEST (evidence attached, native authorization or future
scope required), and 2 are FAILED-REOPENED with a precise, narrow root cause each (not vague —
both are one well-scoped fix away from closing). Ten tracks shipped across ten PRs plus one
follow-up plus one P0 hotfix, all merged via PR + auto-merge to protected `main`. Production
(`amjis-mcp`, Cloud Run asia-south1) is confirmed stable and byte-for-byte at `main` HEAD as of
close. One self-inflicted production incident occurred mid-campaign (a crash-loop from a
merge-order interaction between two tracks) — it was caught, mitigated within minutes via
traffic rollback, root-caused, fixed, and verified before this report closes. Two Dvārapāla
decisions were rendered on genuine judgment calls; both are documented below with full rationale.

## §1 — Phase A findings

- **A.1 (dual-surface triage): RESOLVED — no dual-surface problem.** `mcp_server_info` on both
  `marsys-jis-direct` and the `claude.ai MARSYS-JIS` connector returned the *identical*
  `catalog_version` (`catalog-1+t152+r653c2a1a98c8`). Both surfaces are the same live deployment.
  The register/analysis divergence was a `budget_kb` parameter artifact (confirmed live: `dossier`
  at `budget_kb:16` shows 1.9% coverage/6 pages; at larger budgets it hydrates much faster) — not
  two different server builds. MC-018 disposed VERIFIED-NO-DEFECT.
- **A.2 (disposition seed):** Live re-verification before any builder started confirmed MC-001,
  MC-002, MC-004, MC-010, MC-016, MC-021/024, MC-025 all reproduced on current production — none
  were stale-surface artifacts. MC-008/012/013's "empty vargas / expensive dossier" framing was
  reproduced as a real *low-`budget_kb`* economics problem, re-scoped to T5's mandate rather than
  dismissed.
- **A.3 (PV coexistence):** A PŪRṆA-VIRĀMA close-out campaign was genuinely active throughout —
  its own PRs (#792, #796, #798, and later #814) merged into `main` during this campaign's
  runtime. Two Dvārapāla-adjudicated releases governed the interaction with SHODHANA (§3).

## §2 — Tracks and PRs

| Track | Item(s) | PR | Disposition highlights |
|---|---|---|---|
| T1 SATYA-VĀK | MC-010, MC-003, MC-017 | #804 | MC-010/003 fixed; MC-017 correctly PARKED (registry_bridge.ts PV-locked at the time) |
| T2 SETU-BANDHA | MC-001, MC-002, MC-025b | #806 | MC-002/025b fixed; MC-001 honesty-scaffolding shipped, full fix requires a Bodha rebuild — Dvārapāla PARK |
| T3 SAMA-BHĀRA (released mid-campaign) | MC-004/005/006/007/014/019/023 | #811 | hardFloor order fixed, MC-023 dedup fixed, MC-014 defaults fixed; guaranteed-fits `verbosity:summary` param left undone (needed registry_bridge.ts, correctly deferred to avoid colliding with the concurrent MC-017 fix) |
| MC-017 follow-up | MC-017 | #810 | 8 sites relabeled after Dvārapāla cleared registry_bridge.ts; found a bonus root-cause bug (cross-ayanamsha `INVARIANT` vs per-call filter mismatch) |
| T4 PRĀPTI | MC-021/024, MC-032, MC-022, strict schemas | #805 | All 4 items fixed; portal-wide `.strict()` gate shipped via a registration-time wrapper with an exclusion list for T1/T5/T7/T8's tools (to avoid merge conflicts) — **not widened after those tracks merged; open follow-up** |
| T5 PŪRTI | MC-012/028/030/031/033/034, MC-013 | #808 | Compact completeness receipt, reading_checklist, salience boost, KP block, gochara join all fixed; MC-013 (α-blocker) correctly PARKED |
| T6 YOGI-BINDU | MC-029 | #807 | New asset computed correctly (Yogi=Mercury, Avayogi=Mars, exact match, two-pass verified) — **but never actually built into production for either canonical chart; Verifier found 0 live rows. FAILED-REOPENED, see §5.** |
| T7 UPĀYA-ŚODHANA | MC-025a, MC-027 | #809 | MC-027 fully fixed (live-verified: the exact Vadha-tārā window now carries an avoid-note); MC-025a root-caused and improved (spread 0.04→0.096) but honestly short of the >0.15 target — PARKED with cause disclosed, not forced |
| T8 RŪPA-SAṂSKĀRA | MC-011, MC-015, MC-016, MC-026 | #803 | MC-011/016/026 fixed; **MC-015 (discoveries ayanamsha dedup) reproduces live despite the code change — FAILED-REOPENED, see §5** |
| T9 LEKHA-PARĪKṢĀ | WL-7, WL-8 | #801 | Read-only audit; corrected the register's "65 events" to the actual 57, found only loans/debt genuinely missing from WL-7's list, confirmed WL-8 a true gap; bonus finding: `mimamsa_lel_query`'s tag filter appears non-functional |
| P0 hotfix | — | #812 | See §4 |

All ten track PRs plus the follow-up plus the hotfix are merged to `main`. Two PRs (#806, #808)
required real (not mechanical) conflict resolution against sibling tracks that merged first —
both resolutions were verified by running the conflicting tests together, not just by the absence
of merge markers.

## §3 — Dvārapāla decisions

**Decision 1 — T3 release (mid-campaign).** T3 was held per the brief's PV-coexistence rail
(`response_budget.ts` PV-locked pending PV closure). At the point 8/9 other tracks had completed,
Dvārapāla independently verified — not on the Conductor's word — that (a) no PV closure report
exists, but (b) two PV PRs (#796, #798) had already merged and neither touched
`response_budget.ts`/`registry_bridge.ts`/root `CLAUDECODE_BRIEF.md`, and (c) the only PV
artifact anywhere (a locally uncommitted brief-pointer edit) also didn't touch those files.
**Decision: AUTHORIZE T3**, cut from `origin/main` in an isolated worktree, with guardrails
(scope restricted to its stated targets; re-check main before merging; note the rebase
contingency for the native in the PR). T3 shipped as #811. The same clearance also reopened
MC-017, closed via the follow-up PR #810.

**Decision 2 — Bodha rebuild (MC-001).** T2 found the deterministic-remap approach for
`constituent_facts_array` orphaning is genuinely infeasible (the fact_id hash embeds the L1
build_id and is non-invertible; only ~68% recoverable via unreliable string-matching) — the only
real fix is a full Bodha (L2) rebuild. T2 declined to execute this unilaterally and escalated.
Dvārapāla independently verified: a Bodha rebuild is the standard, previously-exercised
orchestrator "Build" path (not novel/risky); grepped every `bo_*.py` writer and confirmed **zero**
touches `kala_gochara_windows` or `build_substep_progress` (L3 vs L2 layer separation holds);
confirmed the operation is idempotent (delete-then-insert per §N.3, re-runnable, not destructive).
**Decision: PARK-HONEST — do not execute this campaign.** Rationale: the operation is DB-safe but
is a live-production write against the native's own actively-used chart, whose true current
writer roster (~25 writers) has silently outgrown the campaign's own governing DAG documentation
— an ambiguous-footprint situation is exactly what this gate exists to catch, and the one thing
that would make *not* rebuilding dangerous (silently serving broken data as trustworthy) was
already closed by T2's freshness-stamp/honest-degraded-status code, shipped in the same PR.
Conditions for a future AUTHORIZE: reconcile the DAG doc to the real writer roster first; measure
the Abhinandan chart's orphan rate independently (not assumed from the native chart's number)
before bundling it into the same authorization; native gives explicit go-ahead.

**Post-close finding relevant to Decision 2:** the Verifier's final pass (§5) found chart
482012f1's orphan rate is now live-measured at **0%** — a chart rebuild occurred on 2026-07-27,
external to this campaign (no SHODHANA agent was given build-trigger access; T2 explicitly
declined and escalated rather than rebuild; the disabled `brahma-conductor.yml` autonomous-build
path rules out an automatic trigger). This rebuild is **partial** — it did not run T6's new
sensitive-point-yogi writer substep, and did not rebuild `ka_kalasutra`/`kala_bhavishya`. MC-001
is therefore disposed VERIFIED-FIXED on live evidence (the orphan gap the register named IS now
closed), while the Dvārapāla PARK on *this campaign executing a rebuild* stands as the correct
record of what SHODHANA itself did and did not authorize.

## §4 — P0 production incident (mid-campaign, self-inflicted, resolved)

**What happened.** After all ten track PRs merged, live verification found `amjis-mcp` in an
active crash-loop: every real (authenticated) MCP request crashed the Node process with
`Error: Tool prashna_ask expected a Zod schema or ToolAnnotations, but received an unrecognized
object`, thrown inside the MCP SDK's `.tool()` registration. Root cause: T4's new
`strict_tool_schema_gate.ts` (portal-wide unknown-param rejection, MC-024) wrapped a tool's raw
zod shape into a constructed `z.object(shape).strict()` and re-passed it through the SDK's
**positional** `.tool(name, desc, schema, cb)` overload — but the deployed SDK version
(`@modelcontextprotocol/sdk` 1.29.0)'s positional-overload parser rejects an already-constructed
schema instance there (it only accepts constructed schemas via the `registerTool(name, {
inputSchema }, cb)` path). Every strict-ified tool would have hit this; `prashna_ask` was simply
the first one reached at request time. Gate-application order between `strict_tool_schema_gate`
and `deprecated_tool_gate` was **not** the cause (verified: both orders throw identically).

**Response timeline.**
1. Discovered during post-merge `mcp_server_info` verification (production returning `Service
   Unavailable`/crash traces).
2. **Immediate mitigation:** Cloud Run traffic rolled back 100% to the last pre-campaign-safe
   revision (`amjis-mcp-00481-psp`) within minutes of discovery. Verified via a real authenticated
   tool call (not just a health check) before considering the rollback successful.
3. Dispatched a dedicated P0 fix agent (Opus) with an explicit requirement to reproduce the crash
   locally against the real SDK before touching code — it did (a minimal repro against the real
   1.29.0 SDK, not a mock), confirmed the bug is fully general (not `scope_tuple`-specific — a
   flat two-field shape crashes identically) and gate-order-independent, and fixed it by rerouting
   the wrap through `registerTool()`'s supported path instead of the broken positional overload.
   `prashna_ask` was **not** added to the gate's exclusion set — the general bug was fixed, not
   band-aided. A regression test drives both real gates against the real SDK with a nested-optional
   shape (mirroring `scope_tuple`) and is proven, via A/B, to fail on the original code and pass on
   the fix. Merged as PR #812.
4. **Verified before full cutover, twice.** A first cutover attempt targeted the wrong revision
   (one built from an earlier, unrelated commit, mistaken for the fix because it was simply the
   newest revision at the time) — the crash reproduced identically. Caught within seconds via the
   same "hit it and check logs" discipline, rolled back again immediately, and the correct
   deploy (matched to PR #812's exact merge commit) was identified and waited for explicitly.
   The genuinely-fixed revision was then canary-tagged, hit with real authenticated production
   calls (confirmed via response metadata correlating to the new build) before any traffic shift,
   then 10%-canaried with real traffic, then fully cut over — each step confirmed clean via logs
   before proceeding to the next.
5. **Final state:** production 100% on the fixed revision, confirmed matching `main` HEAD, clean
   logs, no crash across ~30 live authenticated calls made during verification.

**Lesson for the record:** a portal-wide monkeypatch mechanism (this is now the third one in this
file: profile gate, deprecated-tool gate, strict-schema gate) needs an integration test against
the *real* SDK, not a mocked `server.tool()`, before it ships — the pre-existing
`strict_tool_schema_gate.test.ts` used a mock that could never have caught this, which is why it
shipped. The new regression test closes that gap going forward.

## §5 — Items requiring a fast, narrow follow-up (FAILED-REOPENED)

**MC-015 — `bodha_discoveries_get` ayanamsha-variant dedup does not reproduce on the live,
populated surface.** T8's PR #803 changed `query_discoveries.ts` (+133 lines) and the raw
discoveries count dropped from the register's 1,269, but the Verifier's live test on
`domain=wealth` still shows the same finding (aspect_parashari house 1/4/9) repeated across 4–5
ayanamshas with no `discovery_families`/cross-ayanamsha-agreement-score collapse — the exact
defect the register named. Contrast: MC-026's sibling fix (`kala_projections_get` →
`projection_families`) DOES collapse correctly on its own populated surface, so the pattern is
known-good elsewhere in the same PR; this is a scoped bug in one function, not a design gap.

**MC-029 — Yogi/Avayogi asset never materialized in production for either canonical chart.**
T6's computation is correct (independently reproduced by the Verifier from live Sun/Moon
longitudes: Yogi point 352.351181° → Revatī → Mercury; Avayogi 179.017847° → Chitrā → Mars —
exact match, no forcing) and the two-pass verification and serving code are sound. But the
Verifier found **zero** live rows under the new `sensitive_point_yogi` category on both
482012f1 and 1c826d5a — the writer substep that would populate it has never actually run against
production data for either chart (T6's own verification ran against local/test computation, not
a live orchestrator build). A pre-existing, unrelated writer (`ga_sensitive_writer.py` / GA5)
serves a *different* category (`esoteric_point_yogi`/`esoteric_point_avayogi`) with partial,
inconsistent data (has Yogi=Mercury for 482012f1, no Avayogi; different values for 1c826d5a) —
this older asset should be reconciled or retired once the new one is populated, not left as a
second, disagreeing source. Fix required: trigger a scoped orchestrator run of the
`ga_sensitive_degree` writer substep (NOT a full Bodha/L2 rebuild — this is a contained L1 GA
writer operation, materially smaller in scope and risk than the Dvārapāla-parked Bodha decision
in §3) for both canonical charts, then re-verify live.

Both items are precise and narrow — this is not a vague "needs more work," it is one specific
function (MC-015) and one specific missing build step (MC-029) away from closing.

## §6 — Preserve-list: confirmed intact

`chart_snapshot`, `judgment_query`'s verdict decomposition, `ganita_special_lagnas_get`,
`ganita_av_transit_gating_get`, `kala_windows_get`'s `window_families` dedup,
`ganita_yoga_firings_get`'s `grounds_jsonb`, the gemstone `requires_acharya_review_flag` gating,
and the honesty-field vocabulary (`judgment_flags`, `trim_report`, `n_support`,
`sub_tools_errored`) were all re-tested live post-campaign and confirmed serving exactly as
documented, undegraded by any SHODHANA change.

## §7 — Sealed-harness flagship re-run

n=2 naive-consumer runs against the exact sealed system prompt ("How is my wealth?", chart
482012f1), graded manually against the frozen 13-concept wealth list (`SEALED_EVALUATOR_HARNESS_
v1_0.md`; the existing `evals/k2/consumption_grader.ts`/`evals/r5-w4-full-battery/llm_grader.ts`
scripts were not executed in-session — this grading is a good-faith manual application of the
frozen rule, not a certified re-run of the automated grader, and should be treated accordingly).
Scores: 6/13 (0.46) and 3/13 (0.23), median ≈ 0.35 — below the harness's own 0.90 pass floor.
Two different historical baselines exist for comparison and they disagree: `STREAM_GAMMA_CLOSE_
v1_0.md` records a naive routing-consumer baseline of 2/13; `PURNA_VIRAMA_BRIEF`'s cited "median
≥12/13" reflects a differently-instrumented (dossier-paging) consumer, not this sealed-harness's
naive single-turn prompt. Against the naive baseline (2/13), this campaign shows a real
improvement (0.35 median, no regression); against the ≥12/13 figure, the naive consumer remains
far short — but that regime was never reachable by a single-turn naive prompt in the first place,
which is precisely the MC-028/034 tension this campaign's T5 track named and instrumented
(`reading_checklist`'s `non_exhaustive: salience_sampled` self-disclosure) without forcing every
naive caller through the full completeness contract. **This is not a regression from W7 — it is
the same known ceiling, now honestly disclosed rather than silently hit.**

## §8 — Known open follow-ups (not blocking this close)

- **Strict-schema gate exclusion set** (T4/#805) still excludes T1/T5/T7/T8's tools by name —
  added deliberately to avoid merge conflicts mid-campaign, never widened afterward. A future
  session should extend `STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES` coverage now that all ten tracks
  are merged and the conflict-avoidance reason no longer applies.
- **`mimamsa_lel_query`'s `query`/`offset` params appear non-functional** — flagged by T9 as a
  bonus finding (identical `result_hash` across differing inputs), not one of the 34 register
  items, not investigated further this campaign.
- **T2's DAG-documentation drift** — the real `bo_*` writer roster (~25 writers) has outgrown
  `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md §2`'s documented 14-writer DAG; flagged by Dvārapāla as a
  precondition for any future Bodha-rebuild authorization.
- **`Boot-time pointer validation (SC-17/18/19)`** CI check is red on current `main` — confirmed
  pre-existing (introduced by an unrelated concurrent PV-side commit, #802, not by any SHODHANA
  PR) and not a required branch-protection check; out of this campaign's scope.
- **MC-004/MC-006** — a true guaranteed-fits minimal form for `assess_wealth`/`assess_marriage`
  remains open; the hardFloor/dedup/defaults fixes shipped materially reduce byte cost and fully
  restore verdict-prose integrity, but the largest domain reads can still exceed budget after full
  trim. Closing this fully requires the `verbosity:'summary'` enum addition that both T3 and the
  MC-017 follow-up deliberately deferred to avoid a mid-campaign file collision.

## §9 — Close-protocol checklist

- [x] All PRs merged, `amjis-mcp` deployed, production confirmed == `main` HEAD.
- [x] Worktrees and branches cleaned (see below).
- [x] This report written and merged.
- [x] Register annotated LIVING → ADDRESSED-v1 (append-only; see the register's own changelog).
- [x] PV artifacts confirmed undisturbed: the one file this campaign found in a PV-adjacent state
      (root `CLAUDECODE_BRIEF.md`, uncommitted local edit in the primary checkout) was restored
      to its exact original state after an isolation mishap (§10) revealed it had briefly moved.

## §10 — One process note, for the record

One builder (T1) was, contrary to instruction, allocated the **primary working directory**
rather than an isolated worktree (a fleet-allocation anomaly, not a builder error) — it noticed,
correctly stashed the pre-existing PV work it found there (rather than discarding or committing
over it), and built its actual changes on a proper fresh branch. The Conductor subsequently
restored the primary checkout to its original branch and popped the stash back, verified
byte-identical to the session's opening state. No PV data was lost or altered at any point; this
is recorded because it happened, not because it caused harm.

---
*SHODHANA closes here. Two items (MC-015, MC-029) are reopened with narrow, well-specified fixes
described in §5. One Bodha-rebuild authorization (§3, Decision 2) awaits the native's explicit
go-ahead per the stated conditions. Everything else the register named is either fixed and
live-verified, or honestly parked with its release condition on record.*
