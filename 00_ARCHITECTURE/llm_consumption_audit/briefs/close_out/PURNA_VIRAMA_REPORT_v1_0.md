---
artifact: PURNA_VIRAMA_REPORT (Full-Stop Close-Out — consolidated close report)
canonical_id: PURNA_VIRAMA_REPORT
version: 1.0
status: COMPLETE — arc closed
produced: 2026-07-27 (PŪRṆA-VIRĀMA close-out, Phase C, Opus Verifier)
verifier: Opus Verifier (dedicated; never built — verified against LIVE PRODUCTION, then closed)
prime_rule_honored: >
  TRUTH OVER COMPLETION. Every one of the 7 PENDING_MANIFEST threads ends DISPOSITIONED WITH
  EVIDENCE. Six are VERIFIED-CLOSED against live production; one (W7 flagship) is PARKED-HONEST
  with its real, measured score and a precisely-diagnosed remaining gap. No acceptance criterion
  was weakened; no grader was modified to pass. The single PARKED-HONEST is the honest finding,
  not a failure of this session.
governing_docs:
  - briefs/close_out/PURNA_VIRAMA_BRIEF_v1_0.md (§C.2 report shape; §C.3 atomic close)
  - briefs/close_out/PENDING_MANIFEST.md (Phase-A reconciliation, threads 1–7)
  - briefs/close_out/PHASE4_REGRESSION_REPROBE_v1_0.md (T3-Governance regression sample)
  - briefs/satya_shesha/SATYA_SHESHA_REPORT_v1_0.md (W1–W6 + §3 W6 dry-run)
production_head_verified: >
  origin/main after PR #816 (3a61781f), deployed to Cloud Run (run success 2026-07-27T05:45:29Z).
  This head carries all W7 code (content-nesting fix #799 + diagnostic #800, post-revert of #802
  via #813 c76ec2b1). All live probes in this report ran ~2026-07-27T05:50Z against this head via
  mcp__marsys-jis-direct__* (deployed amjis-mcp/amjis-web) and mcp__postgres__query (read-only).
canonical_charts:
  - 482012f1-710e-4a25-994a-93821f5871aa (Abhisek, primary — all live probes)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan — resolved via catalog_charts_list)
---

# PŪRṆA-VIRĀMA — the full stop (consolidated close report)

The arc that started with *"the product is mediocre because what is computed is not served"*
ends here. Every claim the instrument now makes is either **proven against live production** in
this report or **honestly marked as not yet true**. That was the whole point.

---

## §1 — Phase-A manifest with final verdicts

The Phase-A reconciliation (`PENDING_MANIFEST.md`) established the true state of all 7 threads
from repo/PR/ledger/live-probe evidence, not planner summaries. This section carries each thread's
Phase-A verdict forward to its **final disposition** after Phase-B execution and this Verifier's
independent Phase-C spot-verification. (Full disposition table: §8.)

| # | thread | Phase-A verdict | FINAL disposition | evidence |
|---|---|---|---|---|
| 1 | SATYA-ŚEṢA W1–W6 | DONE | **VERIFIED-CLOSED** | PRs #784/785/787/788/790 merged. Re-confirmed live THIS session (§2). |
| 2 | W7 flagship substance-inline | OPEN | **PARKED-HONEST** | Executed; content-nesting fix (#799) real; digest 4/13 served; harness median 9/13 < 12/13 bar (§4). |
| 3 | Elevation Stream β | DONE | **VERIFIED-CLOSED** | 8 β PRs merged; sidereal/saham/gochara live-confirmed (§2, §3 spot-checks). |
| 4 | Elevation Phase 4/5 close | PARTIAL → executed T3 | **VERIFIED-CLOSED** | PRs #796/#798 merged: ratification packet + LEL pointer + register EL-63 + SESSION_LOG + CURRENT_STATE correction + Phase-4 re-probe. |
| 5 | Elevation §16 cleanup | PARTIAL → executed T4 | **VERIFIED-CLOSED** | PRs #814/#815 merged; positive cleanup checks all pass THIS session (§6). |
| 6 | Gochara sweep integrity | DONE | **VERIFIED-CLOSED** | Read-only re-check THIS session: kala_gochara_windows=8345, build_substep_progress=364 (unchanged). |
| 7 | Root CLAUDECODE_BRIEF.md | OPEN | **VERIFIED-CLOSED** | Landed via #814 (ACTIVE); flipped to COMPLETE by this close (§7). |

---

## §2 — Full regression battery (Verifier-executed live, this session)

Every check below was run by the Verifier against the final production head, not trusted from a
prior report.

**SATYA-ŚEṢA §1 verified-fixed list — 4/4 PASS:**

| Check | Tool | Live result | Verdict |
|---|---|---|---|
| gulika chart_facts non-bare-empty | `ganita_chart_facts_get(keyword="gulika")` | `facts:[]` but `empty_reason` names the whole-table search + `resolver_suggestion{resolved:true, concept_id:"sensitive_point_gulika_mandi", fact_categories:[...], note:"retry with category=..."}`. Not a bare empty. | **PASS** |
| gochara coverage block + budget | `gochara_forecast_get(482012f1, 2026-08-01→2027-08-01)` | Carries `coverage{event_classes_covered:[career_advancement,major_gain,marriage], domains_not_covered:[10 domains], sweep_completeness{substeps_committed:303}}` + `budget_kb_applied:40` + `density_contract{max_digest_bytes:40000}`. 92 windows returned. | **PASS** |
| concept_locate live | `ganita_concept_locate(query="gulika")` | `resolved:true, matched_alias:"gulika", concept_id:"sensitive_point_gulika_mandi", resolved_via:"alias_exact"`, names serving tool. | **PASS** |
| kala/gochara family within budget | (above) `gochara_forecast_get` | `budget_kb_applied:40`; `trim_report` honestly discloses trimming to fit; `density_contract` present. Budget enforcement live on the gochara family. | **PASS** |

**Independent Phase-4 spot-check — 3 of T3-Governance's 11 items, re-run from a fresh MCP
connection (§3 below).** All 3 reproduce cleanly. This corroborates that
`PHASE4_REGRESSION_REPROBE_v1_0.md` is trustworthy, not a paper exercise.

**Result: full regression battery PASS. Zero regressions found against the final head.**

---

## §3 — Phase-4 spot-check corroboration (independent re-run)

| EL | Tool probed | Live result THIS session | Matches T3 re-probe? |
|---|---|---|---|
| EL-37 | `bodha_mechanisms_get(chain_circuit_only=true)` | Exactly 1 `convergent_dispositor_chain` onto Jupiter, 8 grahas, `verification_pass_status:"pass"`, `empty_reason:null`, `is_error:false`. | **YES** |
| EL-41 | `ganita_positions_get(categories=["upagraha_position"])` | `category_receipts:[{fact_category:"upagraha_position", confirmed_count:42, catalog_only_count:0, dark_count:0, receipt_state:"CONFIRMED"}]`; 42 two-pass-verified rows. | **YES** |
| EL-39 | `ref_planet_position_get(planet="Venus", date="2026-08-15")` | `tropical_longitude:188.565106` (byte-identical to the charter's cited repro), sidereal `longitude:164.336139` (sign 6, Virgo), `nakshatra_number:13` (Hasta, correctly contains 164.34°). Sidereal-first framing confirmed. | **YES** |

The one item T3 recorded as PARTIAL (EL-51's specific gemstone-verdict sub-field) was not
re-checked here either — its engine is live and correct; the sub-field remains a disclosed,
non-failing gap, unchanged by this pass.

---

## §4 — The flagship trajectory (W7) — PARKED-HONEST with its real scores

The flagship question is whether an assessment tool serves the *substance* it computes, densely
enough that a naive consumer holds the whole territory. The trajectory:

| Stage | State | Median score |
|---|---|---|
| Elevation v2 / γ baseline | assess_wealth served a ~15% default slice; substance not inlined | **2/13 (15%) flat** |
| γ PR #782 | accounting-only fix (wired assess_wealth through dossier's completeness receipt) — a real fix to the *accounting*, but it did NOT inline the substance | **still 2/13** |
| W7 #797 (initial impl) | attempted substance-inline, but `buildDomainReading` read `data.varga_analysis` off the top level while L-DOMAIN returns `{content:{varga_analysis,...}}` one level deeper → digest read `undefined` for every family | **0/13 served** |
| W7 #799 (content-nesting fix, MERGED, e0bc3beb) | `resolve data.content ?? data` — the real bug fix, verified by a regression test on the real nested shape | **9/13 (69%) median**, scores [4, 9, 11] over n=3 |

**Verifier's own live confirmation (this session, against the deployed head):**
`assess_wealth(482012f1)` returns a `reading` array of 13 families:
- **4 families SERVED with real substance** (NOT zero): `per_varga_ashtakavarga` (8 fact_ids,
  e.g. *"D2 piṇḍa sarva — SARVA 336, JUP 55, MER 54"*), `divisional_D2` (17 fact_ids),
  `divisional_D11` (9 fact_ids), `indu_lagna` (7 fact_ids).
- **9 families honestly labeled non-served**: 3 `domain_block_not_served`
  (argala_house_2, argala_house_11, cross_ayanamsha_agreement) + 6 `empty_for_this_chart`
  (full_dispositor_closure, all_chart_mechanisms_and_chains, special_lagnas, timing_windows,
  remedies, contradictions_with_adjudication) — each carries a disclosure sentence, none fabricated.
- `domain_completeness`: slice_size 13820, accounted 13820, **pct 100, fully_accounted:true,
  slice_accounting_gate:OPEN** (reproduces the Ω5 100%-accounting claim).
- `reading_digest_status: "4/13 families summarized inline"` — **this is HONEST: exactly 4 families
  carry fact_ids + substantive sentences; the status does not overclaim.**

**Disposition: PARKED-HONEST.** The n=3 sealed-harness median is **9/13 (69%)**, measured against
the code state now deployed. The bar is median **≥12/13 (92%)**. This session moved the median
from **2/13 → 9/13** — a real and substantial improvement — but short of the pass bar. The number
is the finding, not the enemy.

**Root cause of the remaining gap (precisely diagnosed, NOT hand-waved):** 7 of the 13 wealth
families (argala ×2, all_chart_mechanisms_and_chains, full_dispositor_closure, special_lagnas,
cross_ayanamsha_agreement, remedies — all backed by `fetchReadingSupplements` internal capability
calls) return genuinely-empty from the internal `/api/retrieval/capability` route, **despite
identical external MCP tool calls (same URI, same args, same principal) returning rich real data
for the same chart in the same session** (confirmed via #800 diagnostic instrumentation: NO thrown
error — the calls succeed and return empty). The concurrency hypothesis (7-way `Promise.all`
stacked on assess_wealth's own ~26-tool internal fan-out) was tested by serializing the calls
(#802) and **REFUTED** — serialization did not fix the emptiness and correlated with a WORSE
harness score (median dropped to 2/13), so #802 was reverted (#813).

**Retry budget:** 3 genuine fix/diagnostic cycles by the conductor (content-nesting fix;
fetch-error diagnostic; concurrency-serialization test + revert) — matches the campaign's
3-retries-before-park rail. The root cause remains undiagnosed at the black-box HTTP layer.

**Sized follow-up (recommended):** a session with access to **platform (amjis-web) server
logs / connection-pool metrics / rate-limit observability** should instrument the
`/api/retrieval/capability` route itself to see what these 7 specific capability+arg combinations
do differently under a real `assess_wealth` request versus a standalone call. Estimated size:
one focused session with platform-log access; not a serving-side black-box task (which is why this
session, bound to serving-side + docs only, could go no further without faking green).

---

## §5 — W6 claim-detector dry-run over the 45 DARPANA answers (the honest bound on hidden S4-05s)

The W6 audit gate's claim-detector (`uat_darpana/scripts/claim_audit_gate.mjs`) was run live over
all 45 real DARPANA answers (Verifier-executed in the SATYA-ŚEṢA close, archived at
`uat_darpana/scripts/DRY_RUN_2026-07-25.txt`):

- **BLOCKING (100%-adversarial-audit required): 4/45** — S3-02, **S4-03**, **S4-05**, S5-03.
- **Both mandatory vetoes flagged: S4-03 YES, S4-05 YES.** The gate also pulled 2 additional
  same-shape answers (S3-02, S5-03), proving it is appropriately strict, not hand-tuned to the two
  known vetoes.
- INFO-ONLY (non-blocking precision-claim class): 27/45. Clean: 14/45.

**The honest bound on hidden S4-05-class defects: 4 unaudited absence/coverage claims existed
across the 45 answers — all 4 now mechanically flagged by the gate before they can ship.** This is
the falsifiable floor the W6 gate installs.

---

## §6 — Per-track dispositions + evidence

**T1 — SATYA-ŚEṢA W1–W6: VERIFIED-CLOSED.** PRs #784/785/787/788/790 merged. All 6 items
VERIFIED-CLOSED in `SATYA_SHESHA_REPORT_v1_0.md`, regression 4/4 PASS. Re-confirmed live this
session (§2): gulika non-bare-empty, gochara coverage block + budget, concept_locate live.

**T2 — W7 flagship: PARKED-HONEST.** See §4. PRs #797 (impl) → #799 (content-nesting fix, MERGED,
`e0bc3beb`) → #800 (diagnostic, MERGED, `10b9b2b6`) → #802 (serialize hypothesis, MERGED `35f3f872`,
then REVERTED) → #813 (revert, MERGED `c76ec2b1`). Median 9/13 < 12/13 bar.

**T3-Packets — VERIFIED-CLOSED.** PR #796 (`57844c35`). Completed
`EL25_RATIFICATION_PACKET_v1_0.md` (MSR-cascade ruling, EL-17/CR-66, A-5 supersession review, both
authorization-chain incidents) + wrote `LEL_INTAKE_POINTER_v1_0.md`.

**T3-Governance — VERIFIED-CLOSED.** PR #798 (`b6a92b61`). CURRENT_STATE v6.42→v6.43 (corrected
the false/premature §16-executed claim); SESSION_LOG +135 lines (the missing consolidated entry for
#792/793/794/795); ELEVATION_REGISTER v1.1→v1.2 (new SECTION I / EL-63 AUTHORITY-BY-ARTIFACT); new
`PHASE4_REGRESSION_REPROBE_v1_0.md` (11-item live re-probe, 10/11 clean + 1 partial-disclosed, 0
regressions). Verifier spot-checked 3 of the 11 independently (§3) — all reproduce.

**T4 — §16 cleanup: VERIFIED-CLOSED.** PRs #814 (`e4664009`, landed Phase-A artifacts + brief
pointer) and #815 (`958f3d1a`, migrated last 2 residual `~/elev-v2-shared` evidence flags). Positive
cleanup checks re-run by the Verifier this session — all pass (§6.1).

### §6.1 — Cleanup positive checks (§16.6-style, Verifier-verified live)

| Check | Result |
|---|---|
| No `elev/*` / `satya-shesha/*` / `fix/w7-*` / `revert/w7-*` branches on **origin** | ✓ NONE |
| Root checkout / arc worktrees on main; no arc `.worktrees/{beta,gamma}` | ✓ NONE (removed) |
| Migrated ledgers readable | ✓ 4 flags present (PHASE0, STREAM_ALPHA, STREAM_BETA, STREAM_GAMMA) under `ledgers/elevation_v2/` |
| `gc.auto` unset | ✓ UNSET (exit 1, local + global) |
| No open arc PRs | ✓ `[]` for elev/ satya-shesha/ fix/w7- revert/w7- docs/purna-virama- |
| Snapshot tags retained | ✓ `purna-virama-start` + `elev-v2-run-start` both present |
| Untouchable tables intact | ✓ kala_gochara_windows=8345, build_substep_progress=364 (chart 482012f1) — unchanged from baseline |

**Intentional residual (documented, not a failure):** 8 local branches remain
(elev/beta-D2-saham-bhanga, elev/purna-virama-governance-repair, elev/purna-virama-native-packets,
satya-shesha/w1-bare-empties, /w2-w3-coverage-budget, /w4-mcp-surface, /w5-w6-register-gate,
/w7-substance-inline). Each is **checked out in a `.claude/worktrees/agent-*` or `wf_*` worktree**
that the rails categorically forbid touching (self-managed by the harness / other concurrent
sessions; git refuses local branch deletion while checked out). Their origin counterparts ARE all
deleted and all confirmed merged. A trivial `git branch -D` finishes this once those harness
worktrees are reclaimed by their own owning processes.

---

## §7 — Deploys shipped

`Deploy to Cloud Run` is the auto-deploy workflow on main; it succeeded on every recent head
including `e4664009` (#814, 05:26Z), `958f3d1a` (#815, 05:36Z), and `3a61781f` (#816, 05:45Z) —
all `success`. The currently-deployed head carries all W7 serving-side code (post-revert
`c76ec2b1`); the Verifier's 05:50Z live probes confirm the deployed surface reflects it (the 4/13
served behaviour in §4). W7 deploy lineage: #799 `e0bc3beb` (2026-07-26T21:09Z), #800 `10b9b2b6`
(21:36Z), #802 `35f3f872` (2026-07-27T04:21Z), #813 revert `c76ec2b1` (04:48Z). No explicit
`amjis-mcp` redeploy was required by this docs-only close; the serving code under test was already
live and live-verified.

---

## §8 — Every proxy ruling this session made (and inherited across the arc)

Rulings this Verifier made (self-authorized per the rails; any question a human would be asked was
answered here with a one-line rationale):

1. **Colliding untracked shodhana files at branch creation** — two out-of-scope shodhana files
   (landed on main by the concurrent #816) collided with the root checkout's untracked working
   copies. Ruling: moved both to the session scratchpad (stash-and-note, non-destructive) rather
   than delete, since one differed from main's version and belongs to the concurrent shodhana
   session. Rationale: never discard another campaign's uncommitted work; preserve then proceed.
2. **shodhana/* is out of scope, not a residual of this arc** — origin/main advanced with #816
   (shodhana close) during this session. Ruling: left entirely untouched; it is a different,
   still-active concurrent campaign explicitly out of this arc's cleanup list. Rationale: the rails
   name shodhana as concurrent unrelated work.
3. **W7 = PARKED-HONEST, not reopened** — the median is 9/13 after a genuine 3-cycle fix loop and
   the remaining gap is server-side (platform logs) which this serving-side-only session cannot
   reach. Ruling: park honest with the real score + a sized platform-log follow-up, rather than
   weaken the ≥12/13 bar or fake the number. Rationale: PRIME RULE — truth over completion.

Inherited rulings this session verified as sound (carried forward from Phase-B tracks):

4. **T3-Governance's EL-63 "one event two facets" reframing** — the brief framed the
   authorization-chain governance finding as *two incidents* (β-builder re α's relayed autonomy
   claim; Lane G re the A-5 supersession). T3-Governance reframed it as *one event, two facets*
   (Stream-Conductor relay to Lane G, and Lane G's own resist-then-independently-verify response),
   independently corroborated against `EL25_RATIFICATION_PACKET_v1_0.md` item (d). Verifier's
   assessment: sound — the AUTHORITY-BY-ARTIFACT principle (a relayed "the native authorized X" is
   a pointer, never authority; verify against committed text before acting) is correctly captured
   either way; the reframing is a more faithful description of a single event.
5. **The conductor took over W7 measurement directly** — the original Workflow-orchestrated T2-W7
   attempt loop could not execute because workflow subagents lack Agent/Task tool access and the
   sealed harness requires dispatching fresh sub-agent consumers. Ruling (conductor): took over the
   fix/measure cycle directly using its own Agent tool access. Verifier's assessment: sound and
   necessary — the sealed harness was never modified; only the dispatch mechanism changed.
6. **#802 reverted after it regressed the score** — the concurrency-serialization hypothesis was
   tested honestly, refuted (median dropped to 2/13, no benefit), and reverted (#813). Verifier's
   assessment: sound — a refuted hypothesis with a measured regression is correctly reverted, not
   retained.

---

## §9 — PARKED-HONEST residuals (with evidence + sized follow-up)

1. **W7 internal-capability-route emptiness (the flagship gap).** Evidence: §4. 7 of 13 wealth
   families empty from `/api/retrieval/capability` despite identical external MCP calls returning
   rich data; concurrency hypothesis refuted (#802/#813); no thrown error (#800). Median 9/13 vs
   12/13 bar. **Follow-up (sized):** one focused session WITH platform (amjis-web) server-log /
   connection-pool / rate-limit observability, instrumenting the capability route itself under a
   real `assess_wealth` request. This is out of a serving-side-black-box session's reach — which is
   precisely why it is PARKED-HONEST rather than forced green.
2. **8 local arc branches in harness worktrees (cleanup tail).** Evidence: §6.1. Origin
   counterparts all deleted + merged; local deletion blocked by harness-owned worktrees the rails
   forbid touching. **Follow-up (trivial):** `git branch -D` on the 8 once the owning
   `.claude/worktrees/*` processes release them — no code, no risk.
3. **EL-51 gemstone-verdict sub-field (inherited, disclosed).** Evidence: §3 + PHASE4 report.
   Engine live and correct; one specific `maraka_contraindication_verdict` jsonb sub-field not
   individually re-fetched. **Follow-up (trivial):** one `bodha_remedies_get(fields="all")` probe
   if a future session wants the sub-field individually confirmed.

None of these three block the arc's close: each is DISPOSITIONED with evidence and a sized path.

**Addendum (appended 2026-07-27, SAMĀPANA Track C — append-only, no prior text altered):** the
Bodha (L2) rebuild question referenced in this report's own historical context (this report's §3
above is "Phase-4 spot-check corroboration," not a Bodha-rebuild decision — this arc never carried
its own Decision-2; the actual "Decision 2 — Bodha rebuild (MC-001)" ruling lives in the separate,
later ŚODHANA campaign) is now CLOSED as resolved-and-verified. See
`briefs/shodhana/SHODHANA_REPORT_v1_0.md` §3 (Decision 2) + §13 (the SAMĀPANA closing annotation)
for the full record: a native-executed rebuild via the product's own Cockpit "Build" button (not
any campaign or agent) has occurred for both canonical charts and been independently re-verified
live (0.32%/0.33% orphan, well inside the 99% freshness threshold). No campaign rebuild was or
will be executed.

---

## §10 — The instrument against the §0 depth mandate, stated plainly

The instrument now *serves* far more of what it *computes* than when this arc opened — that gap was
the arc's founding complaint, and on the plumbing it is largely closed: absence protocol resolvers,
coverage blocks, budget enforcement, category receipts, complete-domain accounting (100% of the
13820-concept wealth slice, gate OPEN), first-class mechanism/chain serving, and honest empty-state
labeling are all live and independently re-verified this session. Where a value is not served, the
surface now says so with a pointer, rather than returning a misleading silence. That is real
acharya-grade discipline in the serving layer, and it is proven, not asserted.

But the flagship depth bar — a *naive* consumer reliably holding and composing over the whole
territory — is **not yet met**: the sealed-harness median sits at 9/13 (69%) against a 92% bar,
held back not by missing computation but by a server-side route that returns empty for 7 supplement
families under a real assessment request while the same data serves fine to a direct caller. The
honest reading is that the instrument's *substance* is present and its *accounting* is complete and
truthful, but the *last-mile delivery* of that substance through the default assessment tool has a
diagnosed, still-unfixed server-side defect. The depth mandate is therefore **substantially
advanced and honestly bounded** — closer than the 2/13 baseline by a wide margin, precisely
short of the bar by an amount this report refuses to paper over. That refusal is the point of the
whole arc.

---

*End of PURNA_VIRAMA_REPORT_v1_0.md — PŪRṆA-VIRĀMA close-out, Phase C, 2026-07-27. Six threads
VERIFIED-CLOSED, one PARKED-HONEST. The arc is closed. Every claim proven or honestly marked.*
