---
artifact: SAMAPANA_REPORT (Program Wrap-Up — final open threads — Close Report)
canonical_id: SAMAPANA_REPORT
version: 1.0
status: CLOSED
closed: 2026-07-27
author: Conductor (Sonnet, autonomous session) + 3 Sonnet builders (Track A/B/C) + 1 Opus
  Verifier, per SAMAPANA_BRIEF_v1_0.md
source_documents:
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/samapana/SAMAPANA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_SHESHA_REPORT_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_REPORT_v1_0.md
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (ADDRESSED-v1.2)
production_head_verified: >
  origin/main after PR #824 (9c84ed51), deployed to Cloud Run amjis-mcp revision
  amjis-mcp-00496-x5q, traffic 100% on LATEST (not pinned by name — see §4 incident).
  Independently re-confirmed by the Opus Verifier post-close.
---

# SAMĀPANA — the last threads (Close Report)

## §0 — Outcome in one paragraph

All three genuine threads named in `SAMAPANA_BRIEF_v1_0.md` are closed with evidence. **Track A**
(W7 flagship internal-route defect) is **PARKED-HONEST**: the true root cause — a doubly-wrapped
capability-response envelope, not the routing/auth divergence the standing PŪRṆA-VIRĀMA hypothesis
suspected — is found, fixed, and verified (PR #823); the sealed n=3 harness median moved from 9/13
to 11/13, a real and material improvement, but short of the harness's own ≥12/13 bar, with the
residual precisely named. **Track B** (verbosity/deep-dive contract) is **VERIFIED-FIXED** (PR
#824): the `'exhaustive'` tier, `reading_depth:'deep_dive'` contract, and a live-firing hard-guard
against lossy summary forms all work as specified, plus a genuine independent bug fix
(`bodha_chart_digest_get`'s dead `mode` parameter). **Track C** (hygiene) is **VERIFIED-FIXED** (PR
#822): the Bodha-rebuild-park authorization question is closed as native-verified, and the GA.1-class
stored-vs-live `unresolved_constituent_facts_count` disagreement is eliminated at serve time. All
three PRs merged via PR + auto-merge (no direct push). Deploying surfaced a **real, live production
incident** unrelated to this session's own code: `amjis-mcp` traffic was hard-pinned by revision name
to a stale revision from an earlier session, silently no-op'ing the first two of this campaign's three
deploys despite green CI — found only because this close protocol insists on confirming production
state directly. Corrected via canary-then-cutover to `--to-latest` (tracking the latest revision by
name, not a fixed pin — closing the recurrence path, not just this instance). An Opus Verifier
independently reproduced every claim above against live production before this report was written.
Register → ADDRESSED-v1.2. Worktrees and branches cleaned. Production confirmed == main HEAD
(`9c84ed51`). Wall-clock: within the 3h cap.

---

## §1 — Track A (W7 flagship internal-route defect) — PARKED-HONEST

**Gate status:** NOT parked for lack of log access — this session had confirmed `gcloud logging
read` access to both `amjis-mcp` and `amjis-web` Cloud Run services throughout, so Track A proceeded
under its full method, not the brief's log-gated fallback.

**Root cause found (refutes the standing hypothesis):** the PŪRṆA-VIRĀMA report suspected an
internal-route/auth/context-propagation divergence between `fetchReadingSupplements()`'s internal
capability calls and the "same" calls made via standalone MCP tools. That hypothesis is **refuted**
by direct evidence: calling the identical capability with identical args via `bodha_mechanisms_get`,
`ganita_chart_facts_get`, and `bodha_remedies_get` returned rich data for the same chart throughout —
proving the HTTP round-trip itself was never broken. The real defect: every registry capability
handler (`query_mechanisms.ts`, `chart_facts_query`, `query_remedies`) returns a
`{ content: X, is_error: boolean }` ToolResult-shaped wrapper; `/api/retrieval/capability`'s route
handler passes that whole object through as its own `content` field
(`NextResponse.json({ ok: true, content })`), so `callRegistryCapability`'s return value arrives
**doubly-wrapped**. `registry_bridge.ts`'s `rowsOf()`, `readMechanismsFamily`,
`readDispositorClosureFamily`, and `readRemediesFamily` all read `rows`/`narration`/`prescriptions`
directly off the outer wrapper — one level too shallow, always `undefined` — the exact same bug class
already fixed elsewhere in the same file (`buildDomainReading`'s `data.content ?? data`,
`resolveChartHeader`'s `.content` unwrap) but never applied to these four readers. A second, smaller
bug in the same function: `nakshatra_cross_ayanamsha` rows are stored under
`ayanamsha_id='INVARIANT'` (by design — the value is identical across all 5 sidereal ayanamshas), but
the call was filtering on the domain's own ayanamsha, missing every row.

**Fix (PR #823, merged `afad1f68`):** a shared `unwrapCapabilityContent()` helper, applied in
`rowsOf()`/`readMechanismsFamily`/`readDispositorClosureFamily`/`readRemediesFamily`; an explicit
`ayanamsha_id: 'INVARIANT'` override for the cross-ayanamsha call. Regression test
(`w7_substance_inline.test.ts`) fixed its own mock (it was using the WRONG flat shape for the
internal HTTP response — exactly why the bug shipped with all tests green) and added an explicit
assertion that all 7 previously-empty families now report `served`.

**Live verification (this session, post-deploy, both by direct API call and by the Opus Verifier
independently):** `assess_wealth(482012f1-710e-4a25-994a-93821f5871aa)` now serves **12 of 13**
wealth families with real, substantive content — up from 4/13 pre-fix. The sole non-`served` family,
`contradictions_with_adjudication`, is an honest `empty_for_this_chart` correct-negative ("no
contradictions tagged to this domain... a correct negative, this domain reads as internally
consistent"), not a defect.

**Sealed n=3 harness (unmodified — re-run per the rail, never edited):** three fresh, blind
sub-agent consumers (sealed system prompt per `SEALED_EVALUATOR_HARNESS_v1_0.md`, no charter
vocabulary, single naive turn "How is my wealth?") were dispatched against the live post-deploy
production service. Two of three initial dispatch attempts (and one retry) failed on transient
infrastructure stalls, not task defects; three genuine completed runs were obtained:

| Run | Score | Misses (of 13) |
|---|---|---|
| 1 | 12/13 (92.3%) | `special_lagnas` |
| 2 | 10/13 (76.9%) | `per_varga_ashtakavarga`, `all_chart_mechanisms_and_chains`, `special_lagnas` |
| 3 | 11/13 (84.6%) | `all_chart_mechanisms_and_chains`, `special_lagnas` |

**Median: 11/13 (84.6%)** — up from the pre-fix baseline median of 9/13 (69%), a real and material
improvement with zero regression (every run scored at or above baseline). Short of the harness's own
≥12/13 (92%) pass bar.

**The precise, named residual:** `special_lagnas` was missed in **3 of 3** runs — never surfaced
into the naive consumer's final prose answer, despite being genuinely `served` with real substance
in every raw tool response (`"BHAVA LAGNA in Pisces; GHATI LAGNA in Sagittarius; HORA LAGNA in
Gemini; SREE LAGNA in Libra; VARNADA LAGNA in Cancer"`, verified independently by both the conductor
and the Opus Verifier). This is a **distinct, secondary phenomenon from the code defect Track A
fixed** — a naive LLM consumer's own summarization choice, not a serving-layer gap. The broader
`all_chart_mechanisms_and_chains` concept (the full 123-mechanism count, distinct from the single
highlighted `full_dispositor_closure` chain) was also missed in 2 of 3 runs on the same basis.

**Disposition — PARKED-HONEST (both the conductor and the independent Opus Verifier concur):** the
serving-layer defect is genuinely root-caused, fixed, and verified (12/13 data-layer parity,
independently reproduced twice). The flagship's own acceptance bar — the sealed-harness naive-consumer
median — is not yet met. Per the brief's own instruction: "a real improvement honestly disclosed
beats a forced number." This is that disclosure. **Sized follow-up (if the native wants to close the
remaining gap):** the residual is now a *consumer-surfacing* question, not a *data-serving* question —
worth investigating whether `special_lagnas`' phrasing/ordering within the 40kb-budget-trimmed
response makes it easy for a summarizer to skip (e.g. it currently sits without a numeric "punch"
comparable to argala's net score or the dispositor chain's node count), not a further code fix to the
double-wrap class.

---

## §2 — Track B (verbosity vocabulary + deep-dive contract) — VERIFIED-FIXED

**Built (PR #824, merged `9c84ed51`):**
1. **`'exhaustive'` added to `VERBOSITY_ZOD`** (`'concise' | 'detailed' | 'exhaustive'`). Shares
   `'detailed'`'s byte ceiling exactly (verified: `resolveVerbosityMaxKb`'s `verbosity !== 'concise'`
   branch already covers it, pinned by test) and additionally forces the mandatory B.11 orientation
   pre-fetch to its full form (`response_format:'full'`, `top_k_signals:100` vs the default 10-signal
   digest) via the new `resolveOrientationFetchParams()` helper.
2. **`reading_depth: 'standard' | 'deep_dive'` contract**, threaded through `get_chart_orientation`
   and all four `assess_*` tools (`resolveEffectiveVerbosity()` — `deep_dive` deterministically
   forces `'exhaustive'`, never silently downgraded by a stray `verbosity` also present on the same
   call).
3. **Hard-guard (`guardDeepDiveNotLossy` / `DeepDiveLossyFormError`)** — live-wired into the two real
   lossy forms that exist today (`response_format`/`mode` `'summary'`/`'digest'` on
   `get_chart_orientation`/`bodha_chart_digest_get`); throws on a contradictory deep-dive-plus-lossy-
   form call. Ready to bind a future compact/summary form (Track C's optional item, deferred) without
   modification.
4. **`bodha_chart_digest_get`'s footgun, fixed at the root plus contract-side:** the tool's `mode`
   parameter was independently discovered to be a **dead no-op** — `regAlias`'s generic plumbing
   spread `mode` through under its own literal key, but `query_ucd.ts`'s handler only ever reads
   `response_format` (defaulting to `'summary'` when absent), and no `paramAliases` entry mapped one
   to the other. `bodha_chart_digest_get(mode:'full')` therefore ALWAYS silently served
   `'summary'` before this fix — worse than a footgun-by-default, it was uncorrectable by the caller
   via the documented param at all. Fixed by replacing the generic alias with a bespoke registration
   that wires `mode` → `response_format` correctly AND forces `'full'` under
   `reading_depth:'deep_dive'` regardless of what `mode` is passed. The default itself is left at
   `'summary'` (contract-side fix preferred per the brief, less blast radius) — documented in-code per
   the brief's explicit instruction to record the footgun-nature either way.

**Live verification (Opus Verifier, against deployed production, working around a stale client-side
tool-schema cache):**
- `mode:'full'` now genuinely echoes `response_format:"full"` server-side (previously silently
  ignored).
- `reading_depth:'deep_dive'` on the digest call returned `filters.top_k: 100` (vs `20` on a plain
  call) and `response_format:"full"` — a real behavioral lift, not a flag echo.
- The hard-guard **fired live**: `bodha_chart_digest_get(mode:'summary', reading_depth:'deep_dive')`
  was refused with the exact documented `DeepDiveLossyFormError` message.
- Back-compat: a plain call with no new param is unchanged (`response_format:"summary"`, default
  signal caps) — pinned by 19 new tests plus a full pre/post `git stash` comparison showing the same
  77 pre-existing (unrelated) failures in both runs, zero regressions.

**Disposition — VERIFIED-FIXED.** All four brief §2 acceptance bullets independently confirmed live.
One disclosed limitation: `assess_wealth` itself was not separately re-tested with
`reading_depth:'deep_dive'` by the Verifier (the full payload is large enough to strain a single tool
call) — the shared contract code path is proven live on the digest tool and locked by the merged test
suite, so this is a minor coverage note, not an open question about correctness.

---

## §3 — Track C (hygiene closes) — VERIFIED-FIXED

**1. Bodha-rebuild park closed (docs only, append-only).** The brief's own kickoff text pointed at
"PŪRṆA-VIRĀMA §3 Decision-2" — a section that does not exist there (that report's §3 is "Phase-4
spot-check corroboration"). Track C correctly identified the real location — `SHODHANA_REPORT_v1_0.md`
§3 — and annotated it there instead of inventing a fake section, with a corrective cross-reference
also added to `PURNA_VIRAMA_REPORT_v1_0.md` §9. Confirmed by both the conductor and the Opus Verifier:
`git diff` across all three touched files (`SHODHANA_REPORT_v1_0.md`, `PURNA_VIRAMA_REPORT_v1_0.md`,
the register) shows **pure insertions, zero deletions** (`+8/-0`, `+11/-0`, `+49/-0`). The annotation
states plainly: authorization for a campaign-executed rebuild remains PARKED (that Dvārapāla ruling
stands, unchanged) — this note closes only the separate question of whether the precondition is now
moot, which it is, because a native-executed rebuild (via the Cockpit "Build" button, independently
confirmed in `SHODHANA_SHESHA_REPORT_v1_0.md` §3) has already occurred and been independently
re-verified at ≤0.33% orphan on both canonical charts.

**2. `unresolved_constituent_facts_count` (GA.1 class) — derived live, not deleted.**
`query_quality_scorecard.ts` previously served a stale writer-time DB value verbatim
(`unresolved_constituent_facts_count`) alongside a correct live-derived count under a different field
name (`defect_001.metrics.orphan_refs`) in the SAME response — a disagreement the caller had to know
to resolve. Fixed by overwriting the served field with the live-derived count, eliminating the
disagreement by construction (lower blast radius than a migration, per the brief's explicit "OR").
**Live proof the fix is active (Opus Verifier):** the raw stored DB value for
`synthesis_quality_scorecard.unresolved_constituent_facts_count` on the native's chart is **0**
(stale), while the SERVED value from `bodha_quality_get`/`query_quality_scorecard` is **230** —
exactly matching the live-derived `defect_001.metrics.orphan_refs` (230/71293 ≈ 0.32%). One disclosed
cosmetic residual (non-gating): `defect_001_alert.message`'s prose still narrates "the stored
scorecard field may not reflect this," which is now slightly stale itself since the served field DOES
reflect it — a prose-lag note for a future polish pass, not a functional defect.

**3. (Optional) MC-004/006 guaranteed-fits summary form — deferred, as explicitly permitted.** Track
C's light budget was consumed by items 1-2; deferring avoided any risk of colliding with Track B's
concurrent `registry_bridge.ts` work in a separate worktree. Track B's hard-guard is ready to bind
this form the moment it is built, without modification.

**Disposition — VERIFIED-FIXED** (items 1-2; item 3 explicitly and correctly deferred, not a failure).

---

## §4 — Deploy: a genuine pre-existing incident found and fixed (the stale-pin rail, again)

After PRs #822 and #823 merged, both triggered green `Build & Deploy MCP` CI runs and created real new
Cloud Run revisions (`amjis-mcp-00495-mzg`, then after #824's merge `amjis-mcp-00496-x5q`) — but
`gcloud run services describe amjis-mcp` showed traffic **hard-pinned by revision name** to
`amjis-mcp-00494-ptq`, a revision built from an EARLIER commit (`70f23fe9`, from the prior
ŚODHANA-ŚEṢA close). This is the exact same failure class the ŚODHANA-ŚEṢA close found and (thought
it had) corrected — except that correction itself re-pinned traffic BY REVISION NAME rather than to
`LATEST`, silently reproducing the identical bug for every deploy since. **Concretely: the first two
of this campaign's three merges (#822, #823) never received live production traffic despite fully
green CI**, caught only because this close protocol insists on confirming production state directly
rather than trusting workflow badges.

**Correction:** (1) canary — shifted 10% of real traffic to the new revision; (2) tagged the new
revision (`samapana-verify`) for an isolated direct-URL check; (3) drove a real authenticated MCP
call (`assess_wealth`) directly against the tagged revision's URL and confirmed **12/13 families
served** (proving the Track A fix, not just the deploy pipeline, was live); (4) cut over to 100% via
`gcloud run services update-traffic amjis-mcp --to-latest` — **`--to-latest`, not a revision-name
pin**, so the traffic target tracks whatever Cloud Run considers the latest ready revision going
forward, closing the recurrence path this time rather than reproducing it; (5) removed the temporary
verification tag. Final state, independently re-confirmed by the Opus Verifier: 100% traffic on
`LATEST`, `latestRevision: true`, currently `amjis-mcp-00496-x5q`, built from main HEAD `9c84ed51`.

---

## §5 — Opus Verifier acceptance (independent, live production)

One Opus-model, read-only Verifier (no code-writing tools) reproduced every claim above personally —
reading the actual merged commits (not trusting builder self-reports), calling live production tools
directly, running read-only `git diff`/`gcloud`/DB queries — and returned exactly four dispositions,
no "passed with caveats":

- **Production/deploy state: VERIFIED-FIXED.** LATEST-tracking confirmed, not name-pinned; untouchables
  (`kala_gochara_windows=8345`, `build_substep_progress=364`) confirmed unchanged; root
  `CLAUDECODE_BRIEF.md` confirmed untouched; register confirmed still at ADDRESSED-v1.1 pre-bump (as
  expected — this report and the bump follow the Verifier's pass).
- **Track A: PARKED-HONEST** — concurring independently with the conductor's own disposition and
  rationale (§1 above), including an independent live re-derivation of the 12/13 data-layer parity
  and the `special_lagnas` residual.
- **Track B: VERIFIED-FIXED** — all four acceptance bullets independently reproduced live, including
  triggering the hard-guard's refusal directly.
- **Track C: VERIFIED-FIXED** — independently proved the live-derive fix is active via the
  raw-DB-vs-served-value comparison (0 vs 230), not merely reading the diff.

---

## §6 — Closed program-state table (every campaign, final state)

| Campaign | Final state | Evidence |
|---|---|---|
| Elevation (v2, streams α/β/γ) | VERIFIED-CLOSED | `PURNA_VIRAMA_REPORT_v1_0.md` §1-§3 |
| SATYA-ŚEṢA (W1-W6) | VERIFIED-CLOSED | `PURNA_VIRAMA_REPORT_v1_0.md` §2, §6 |
| PŪRṆA-VIRĀMA (arc close) | CLOSED | `PURNA_VIRAMA_REPORT_v1_0.md` (this report's own predecessor) |
| ŚODHANA (34 MC + 8 WL items) | ADDRESSED-v1 → v1.1 → **v1.2 (this report)** | `SHODHANA_REPORT_v1_0.md`, register changelog |
| ŚODHANA-ŚEṢA (MC-015/MC-029 fast-follow) | CLOSED | `SHODHANA_SHESHA_REPORT_v1_0.md` |
| **SAMĀPANA (this report)** | **CLOSED** | this document |

**After this report, the program has no open campaign.** The instrument's registers (Elevation,
LLM Endpoint Consumption) are each fully dispositioned; production runs main HEAD; the deploy
pipeline's recurring stale-pin failure mode has been corrected at its actual mechanism (name-pin →
LATEST-tracking), not just its latest instance.

---

## §7 — Explicitly deferred (named so they are not silently dropped — brief §4)

1. **`mimamsa_lel_query`'s non-functional `query`/`offset` params** (ŚODHANA T9 bonus finding) —
   awaits its own small investigation ticket. Release condition: none blocking; launchable whenever
   the native chooses.
2. **WL-8 margin/retention native data** — awaits the native supplying figures; not a code item.
   Release condition: native input.
3. **DAG-doc reconciliation to the real ~25-writer roster** — maintainability, not correctness;
   explicitly no longer gates anything (the Bodha-rebuild-park authorization question this precondition
   used to block is now closed per §3 item 1 above). Release condition: none; purely a documentation
   hygiene item for a future session with spare capacity.

None of these three block SAMĀPANA's close.

---

## §8 — Close-protocol checklist

- [x] Track A/B/C each dispositioned with evidence (§1-§3); no item claimed DONE without proof.
- [x] All three PRs (#822, #823, #824) merged via PR + auto-merge, no direct push. Sequential
      `update-branch` calls were required (branch protection requires branches up to date before
      merge) — handled without incident.
- [x] `amjis-mcp` deployed explicitly; a real pre-existing stale-traffic-pin incident found and
      corrected (§4) — production confirmed serving the new revision via a real authenticated call
      BEFORE declaring deploy done, per the standing rail.
- [x] Sealed n=3 harness re-run UNMODIFIED (§1) — median improvement measured and honestly reported,
      not forced to pass.
- [x] One Opus Verifier accepted every item live post-deploy — four dispositions, no "passed with
      caveats" (§5).
- [x] Register annotated ADDRESSED-v1.1 → ADDRESSED-v1.2.
- [x] Worktrees removed (`.worktrees/samapana-trackA/B/C`); local + remote branches
      (`samapana/trackA-w7-internal-route`, `samapana/trackB-verbosity-exhaustive`,
      `samapana/trackC-hygiene-closes`) deleted; temporary Cloud Run verification tag
      (`samapana-verify`) removed.
- [x] Root `CLAUDECODE_BRIEF.md` never touched (confirmed already `COMPLETE` at session start;
      independently re-confirmed untouched by the Opus Verifier).
- [x] Untouchables confirmed intact: `kala_gochara_windows` (8345, unchanged),
      `build_substep_progress` (364, unchanged), sealed evaluator harness (re-run only, never
      modified).
- [x] Production confirmed == main HEAD (`9c84ed51`) by both the conductor and the independent
      Opus Verifier.

---
*SAMĀPANA closes here. Three genuine threads: one root-caused, fixed, and honestly parked against
its own flagship bar with the residual precisely named (a real improvement, not a forced number);
two verified-fixed with live behavioral proof. A live production incident this campaign's own deploy
step surfaced — not created — was found and corrected at its recurring mechanism, not just patched
once more. After this report, the program has no open campaign — only the three named, independently
launchable deferred items above. Truth over completion, all the way through.*
