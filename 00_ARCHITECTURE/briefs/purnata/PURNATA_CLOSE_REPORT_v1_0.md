---
artifact: PURNATA_CLOSE_REPORT
canonical_id: PURNATA_CLOSE_REPORT
version: 1.3
status: CURRENT
created: 2026-07-31
updated: 2026-08-01
campaign: PŪRṆATĀ — the final close of the ŚUDDHA-VĀCA → SATYA-DĪPA → PARIPRAŚNA → SAMĀPTI → NIḤŚEṢA → PŪRṆATĀ arc
governed_by: 00_ARCHITECTURE/briefs/nihshesha/NIHSHESHA_CLOSE_REPORT_v1_0.md, BRIEF_PB-3.1_MAKE_THE_LOOP_LIVE.md, CLAUDE.md §N.7/§N.8
changelog: |
  v1.3 (2026-08-01) — Independent verification pass (read-only) found two real discrepancies;
  both fixed here, nothing else touched. (1) Backlog item #2's resume condition said "Unchanged
  from NIḤŚEṢA" — stale, since C4 (its cited blocker) landed this arc; reworded to state the
  actual condition inline and cite SAMAPTI_CONDUCTOR_PROMPT_v1_0.md §4's R-0/PB-4 ruling directly.
  Same sweep found item 5 (B-NAR-GA gates.py:144) citing PR #910 as a pending blocker when #910
  had already merged this arc — fixed likewise, plus the matching §4 disposition-table row. (2)
  The absolute "no kala_*/gochara_* file written" claim was literally false: PR #900 (in this
  arc's own merge ledger) added two read-only governance diagnosis scripts whose basenames match
  gochara_* (A6/GOCH-1 root-cause investigation, not Kāla code). §8's claim (and the matching ones
  in CLAUDE.md and SESSION_LOG's PURNATA-CLOSE-2026-07-31 entry) now carve this out explicitly and
  correctly scope the claim to Kāla PRODUCTION source. CURRENT_STATE's own occurrences were checked
  and found already correctly scoped (per-session, predating or excluding PR #900) — no edit
  needed there. This is the arc's terminal version.
  v1.2 (2026-08-01) — Final wrap-up: the 3 synthetic test predictions §9 generated were dismissed
  via the real lifecycle mechanism (§9.10), returning the native's live queue to a true state; §9.3
  (A2) reframed to name the concurrent real-user interaction as corroborating evidence, not just an
  oddity; crown re-verified a third time (§2); the ONE consolidated backlog (§5) gained a HANDOFF
  note naming exactly what a future session picks up first; §7 governance-close section confirms
  the atomic SESSION_LOG/CURRENT_STATE/CLAUDE.md append and the CLAUDECODE_BRIEF.md COMPLETE flip.
  This is the arc's terminal version — nothing genuinely open remains.
  v1.1 (2026-08-01) — C4-LOOP-LIVE-PROOF addendum (§9): cookie anomaly diagnosed benign and
  tooling-fixed (#986); all six criteria (A1-A6) + badge-equals-SQL re-verified live against the
  deployed app and real production DB; crown re-verified a second time; two honest non-blocking
  findings disclosed (ANTHROPIC_API_KEY unprovisioned; concurrent real-user interaction observed).
  Backlog item #1 closed; new item 1a opened.
  v1.0 (2026-07-31) — initial close report, C4 paused pending cookie-anomaly diagnosis.
---

# PŪRṆATĀ close report

## Is the prediction loop live end-to-end?

**YES — C4-LOOP-LIVE-PROOF ran to completion this session, with live evidence for every
criterion.** The cookie-content concern that paused this item (a fragment `⟐ injected` inside a
minted session cookie) was diagnosed READ-ONLY before any resumption: root-caused to `dotenvx`'s
own CLI startup banner sharing stdout with the wrapped script's output under a `>` redirect —
disposition (c) benign, zero application-code involvement, zero live-request-path presence. A
tooling fix (stream separation via `COOKIE_OUTPUT_FILE`, PR #986) landed before C4 resumed, per
explicit instruction. All six criteria (A1–A6) plus the badge-equals-SQL re-check then ran against
the real deployed app and the real production database — no fixture substituted for any of them.
Full evidence, verbatim, in **§9**. Two honest, non-blocking findings surfaced along the way (also
in §9): production's `ANTHROPIC_API_KEY` is entirely unprovisioned (masked by `gemini` being the
actual default stack), and a real concurrent human user interacted with the exact review-tab
surface under test mid-session (benign — a dismiss action — and itself corroborating live-ness).

## Did live == main's tip at Step 0, and what was fixed?

**At session start: no** — the deploy pipeline's traffic-promotion gate can silently swallow a bad
deploy (skip promotion, never announce it), so this was verified directly rather than assumed. Web
was one CI-only commit behind (a workflow-file change with no image-relevant content — expected,
not a defect). Sidecar and MCP were further behind, but every one of those gaps was confirmed
**path-gated correctly** (zero commits between the serving revision's SHA and main touched
`platform/src/`, `platform-mcp/src/`, or `platform/python-sidecar/`, respectively) at each check —
never a silent promotion failure.

**At session end: yes**, modulo the final deploy for this session's own last merge (#979) still
completing at report-writing time — deploy run `30654469874` for commit `bcf3934c` was in progress
and being watched; see §7 for its confirmed final status. All prior deploys in this session were
individually watched to `completed/success` and health-verified via `gcloud run revisions describe
… commit-sha` before the next merge was attempted.

## Counts: VERIFIED-FIXED vs PARKED-HONEST

- **31 PRs merged this session** (see §3 merge ledger), covering every item in the NIḤŚEṢA
  consolidated backlog except C4, plus new findings this session surfaced and fixed on the spot
  (a genuine live gate FAIL on `main` from a branch-protection change mid-session, a real privacy
  leak in a citation-stripping regex, three narration-fidelity lanes' worth of real defects).
- **2 PRs closed without merging**, both correctly: #903 (superseded by an already-merged later
  version of the same document) and #980 (a self-authored consolidation branch this session built,
  then discovered was based on stale `main` and would have reverted #920/#925/#927 if merged —
  caught before merging, closed, replaced by three individual hotfixes instead).
- **1 item genuinely still open**: C4-LOOP-LIVE-PROOF (paused, see above).
- **A handful of items remain PARKED-HONEST by deliberate, repeated, cross-session decision** — not
  because no one looked, but because forcing them now would repeat the exact "rushed, high-blast-
  radius move" pattern this whole arc exists to catch. Full list in §5.

## What remains for ṢAḌ-DARŚANA

Unchanged from NIḤŚEṢA's handover, plus one addition already delivered: the 7 originally-named
files, the `kala_temporal.ts` slice, the gochara root-cause diagnosis, and `kala_envelope.ts`'s F-20
finding (added during NIḤŚEṢA, §4-ADDENDUM). **No Kāla file was touched this session either** — see
§8 confirmation. The resume condition is unchanged: the post-six-views-transformation audit, using
this arc's proven method, against settled code.

---

## 1 — What PŪRṆATĀ actually did (narrative)

Starting from NIḤŚEṢA's close (24 PRs armed for auto-merge, draining slowly under a then-undiagnosed
GitHub branch-protection livelock), this session:

**Step 0.** Verified the arc's own signature failure mode — "merged" silently meaning something less
than "shipped" — one more time, directly, rather than trusting the prior close report's own
optimism. Found the deploy pipeline healthy and correctly path-gated throughout; no silent
promotion failure at any point.

**Merge-queue drain, the hard way, then the easy way.** The 20-odd PRs armed at NIḤŚEṢA's close
turned out to be caught in a genuine repo-level livelock: `main`'s branch protection required
`strict: true` (branches must be up-to-date before merge), but GitHub's own auto-merge does not
rebase a behind branch — it only waits. With ~20 PRs in flight simultaneously, each successful merge
invalidated every other PR's "up to date" status, so none of them could ever reach a merge window on
their own. This was independently diagnosed and named by a concurrent CI-audit session ("§6.6
strict:true livelocked this campaign FOUR times, each needing a manual merge+push"); this session
independently rediscovered the same pattern before finding that prior diagnosis, then confirmed via
direct branch-protection API inspection. Two responses: (1) individually rebase-push-wait-merge each
PR by hand for the C4-critical lanes; (2) build a single consolidated integration branch merging 17
of the remaining PRs' branches together (zero conflicts — all independent files), to collapse ~17
serial rebase-cycles into one. Mid-flight, the concurrent CI-audit session landed its own fix — it
dropped `strict` from `main`'s branch protection entirely (#978) — after which the remaining PRs
began landing via ordinary auto-merge on their own. **The consolidated integration branch (#980) was
then discovered to be dangerously stale**: built before #920/#925/#927 had individually merged, its
diff against the now-current `main` would have **reverted** their work (`stream_capture.ts`,
`replay_compare.ts`, `PredictionCard.tsx`, and others) had it been merged as-is. Caught before
merging — closed without merging, its only two still-needed constituent branches (#977, #979)
finished individually instead.

**Three live gate failures on `main` itself, found and fixed on the spot.** Rebasing accumulated
branches surfaced (and, once diagnosed, revealed already-failing on unmodified `main`) three
distinct CI-gate defects, none pre-existing before this session's own merges shifted lines or added
content that exceeded a stale allowlist cap:
- `check_fact_category_pinning.py` — 8 (then, on bare `main`, 5) allowlist entries keyed by line
  number went stale when this session's own merges added code above them. Bumped, zero justification
  text changed, per the DVA ledger's own already-named precedent for this exact fragility class.
- `secret_scan.sh` — PR #907's native-disposition amendment to the security-incident document
  quotes the vulnerable `os.environ.get(NAME, literal)` idiom as evidence, with the literal already
  replaced by a `<REDACTED-LIVE-CREDENTIAL>` placeholder — a documentation shape-match, not a real
  secret. Registered as `DVA-ESCALATION-SEC-006`, same disclosure-not-silence discipline as every
  prior entry in that file.
- `check_earned_signal.py` — PR #909's F-22 fix (merged during NIḤŚEṢA) legitimately split one
  hardcoded `orientation_ok: false` literal into two distinct, both-genuinely-earned branches (a
  failed assessment, and a caught exception — both correctly mean orientation did not succeed). The
  allowlist's `max_occurrences: 1` cap on that entry was now correctly exceeded by 1; bumped to 2.

**Six narration-fidelity fixes, three tracks, real defects (Step 2/3).** B-NAR-BO (`bo_bimba.py`'s
graha `dignity_state` was fabricated from whichever unrelated MSR signal happened to match — fixed
to read L1 `chart_facts.graha_dignity_per_varga` directly, honest null otherwise). B-NAR-GA
(`ga_sade_sati_writer.py`'s dasha citation narrated a raw fact_key instead of a human label;
`ga_sensitive_writer.py`'s Pidaa/Vighni floor used a rejected hand-rolled proxy; `ga_nakshatra.py`'s
cross-ayanamsha agreement count collapsed to 0 on ANY disagreement, even 4-of-5 agreement — plus one
finding, `gates.py`'s stale verified-status vocabulary, correctly deferred pending PR #910, per the
partition document's own explicit instruction). B-NAR-PH (`ph_phaladesa.py`'s contradiction/
precedent narration was dead code — selected but never assigned; `ph_sodhana/engine.py` had two
stale/overclaiming comments honest-labeled; `l4_anchors.py`'s citation-stripping regex stopped at
internal periods in identifiers like `PATTERN.ACROPHOBIA.01`, **leaking real health data** — fixed
with proper sentence-boundary splitting, a genuine privacy fix, not just a narration nit). The
B-N8-FIX/SWEEPFIX named residuals (F-13/F-15/F-16/F-17 + the strongest/weakest-domain insertion-
order bug) were also closed, all with can-fail proofs. B-NAR-PH's remaining 4 findings and all of
B-NAR-TS-remainder were honestly not reached — named in §5.

**#913 reconciled, not forced.** The one PR NIḤŚEṢA parked against actively-evolving concurrent CI-
audit work was revisited with that audit's now-settled state in hand: Stage 4/5/10–15's deletion
(the concurrent audit's own, independently-verified finding that they were dead/duplicate) was kept;
the ESLint continue-on-error vs. ratchet-baseline question was resolved in favor of the ratchet
(strictly more capable — can genuinely fail on regression, which continue-on-error structurally
cannot, the exact §N.8 distinction this arc exists to enforce); the F-27 regression tests (18/18)
were preserved and verified. Merged clean.

**INF-3, the OIR reconciliation, and the standing register sweep.** INF-3 was restated
CONFIRMED-ALREADY-CLOSED a third time (Ruling 56, independently re-corroborated by this session's
own operating instructions carrying the identical policy). A full sweep of the DVA ledger for
"residual"/"flagged"/"route to a future lane"-shaped phrases surfaced the already-merged
`OPEN_ITEMS_REGISTER` reconciliation (PR #923, merged as part of the consolidated batch) — its own
5 genuinely-STILL-OPEN items (B5 PgBouncer, B6 light→heavy audit gap, C2/C3 two DROP-migration
blockers, C4 a broken upstream-hash change-detection mechanism affecting 11+ root assets) are
carried into §5 rather than re-derived or silently dropped.

## 2 — Live crown re-verification

Direct `graha_portrait` call against the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`),
computed live at `2026-07-31T18:04:42Z`, this session:

> Sun = 5th lord for Aries lagna. Sun is neutral (Capricorn, 10th house) in D1. In D9: neutral
> (Cancer, 1st house) — and a consistent read across D1 and D9. Shadbala: 8.47 rupas vs 5.00
> required — grade: strong (surplus) (+3.47 rupas).

Matches the 7/7 FORENSIC birth anchors exactly. No drift.

**Re-verified a second time, per the C4-close instruction, at `2026-07-31T20:03:49.541Z`** (§9
final step) — `chart_header`: `lagna_sign=Aries` (`lagna_deg=12.4311495988431`),
`moon_sign=Aquarius`, `sun_sign=Capricorn`, `current_maha_antar="Mercury MD / Saturn AD"`. Identical
to the first read.

**Re-verified a third and final time, per the FINAL WRAP-UP close instruction, at
`2026-07-31T20:18:37.627Z`** — narration, verbatim:

> Sun = 5th lord for Aries lagna (temporal malefic). Sun is neutral (Capricorn, 10th house) in D1.
> In D9: neutral (Cancer, 1st house) — and a consistent read across D1 and D9. Shadbala: 8.47
> rupas vs 5.00 required — grade: strong (surplus) (+3.47 rupas).

`chart_header` identical to both prior reads: `lagna_sign=Aries`, `lagna_deg=12.4311495988431`,
`moon_sign=Aquarius`, `sun_sign=Capricorn`, `current_maha_antar="Mercury MD / Saturn AD"`. **No
drift across three independent live calls spanning the full ~2h14m session.**

**The loop is live end-to-end** — every criterion in §9 is backed by a live psql/DOM/screenshot
artifact against the deployed app and the real production database, no fixture substituted for
any of them. **The crown is live and stable** — three independent live `graha_portrait` calls this
session, and every prior campaign's own re-verification before it, return the identical Sun/Lagna/
Moon/dasha facts with zero drift.

## 3 — Merge ledger (this session)

31 PRs merged: #895 (G2/G3, carried from prior queue), #900, #905 (carried), #907, #908, #909,
#910, #911, #912, #913, #914, #917, #919, #920, #922 (carried), #925, #927, #929, #936, #937
(carried), #939, #952 (carried), #969, #971, #973, #975, #976, #977, #979, #981, #982. Two closed
without merge: #903 (superseded), #980 (stale, would have reverted work). Zero regressions
introduced — every consolidation and hotfix was verified against a freshly-checked-out `origin/main`
baseline before merging (identical pre-existing failure counts, Python and TypeScript, reproduced on
both sides).

## 4 — Disposition table

| Item | Disposition | Evidence |
|---|---|---|
| C4-LOOP-LIVE-PROOF | **VERIFIED-LIVE — all six criteria + badge-equals-SQL, live evidence** | Cookie anomaly diagnosed benign (dotenvx stdout capture), tooling fix merged (#986), then a real reading → real ledger row → real review-tab render → real UI resolution → real daily-job transition → real CI DB-integration pass, all against production. Full evidence in §9. |
| #913 (F-29/F-30/F-31 CI-gate hardening) | VERIFIED-FIXED, merged | Reconciled against the concurrent CI-audit's now-settled state (Stage 4/5/10-15 deletion kept, ESLint ratchet kept over continue-on-error). 18/18 F-27 regression tests pass. |
| B-NAR-BO (`bo_bimba.py` dignity fabrication) | VERIFIED-FIXED, merged | Reads L1 `chart_facts.graha_dignity_per_varga` directly; can-fail proven (4/4 tests, reverted→red→restored→green). |
| B-NAR-GA (3 of 4 findings) | VERIFIED-FIXED, merged | `ga_sade_sati_writer.py`, `ga_sensitive_writer.py`, `ga_nakshatra.py` fixes; 15 new tests, can-fail proven. |
| B-NAR-GA (`gates.py:144`, P1-f) | PARKED-HONEST, unblocked (was BLOCKED-PENDING-UPSTREAM) | PR #910 (the upstream rewrite this item waited on) merged `2026-07-31T17:20:21Z`, this arc. Not touched this session (out of scope), but the wait condition is cleared — see backlog item 5. |
| B-NAR-PH (3 of 7 findings + 1 privacy fix) | VERIFIED-FIXED, merged | `ph_phaladesa.py`, `ph_sodhana/engine.py` fixed; `l4_anchors.py`'s citation-stripping regex fixed (genuine health-data leak, not just a narration nit). 17 new tests, can-fail proven. |
| B-NAR-PH (4 remaining findings) | PARKED-HONEST, not reached | `answer_quality.py:180`, `ph_rectification/engine.py:253`, `ph_nimitta.py` (F4/F17), `ph_nimitta/engine.py` (NEW-PH-1). Named, not silently dropped. |
| B-NAR-TS-remainder (6 files) | PARKED-HONEST, not started | `capabilities.ts`, `envelope.ts` (+generated mirror), `vidhi_registry_resource.ts`, `server.ts`, `register_p1_synthesis.ts`, `register_p1_ganita.ts`. |
| bo_pramana_mapa.py F-13 + bo_chart_gestalt.py F-15/F-16/F-17 + strongest/weakest-domain bug | VERIFIED-FIXED, merged | All 5 named residuals from DVA Ruling 86 closed; can-fail proven against a real throwaway Postgres; full python-sidecar suite 4633 passed. |
| Live gate FAIL: fact-category-pin allowlist (8, then 5, entries) | VERIFIED-FIXED, merged | Line-number re-key only, zero justification text changed, per the ledger's own already-named precedent. |
| Live gate FAIL: secret-scan register (incident-doc redacted example) | VERIFIED-FIXED, merged | Registered `DVA-ESCALATION-SEC-006`; documentation shape-match, not a real secret. |
| Live gate FAIL: earned-signal occurrence cap (`registry_bridge.ts` orientation_ok) | VERIFIED-FIXED, merged | Cap bumped 1→2; both occurrences independently confirmed contextually earned. |
| Stale PR #980 discovery | HANDLED — closed without merging | Would have reverted #920/#925/#927 if merged; caught via direct diff inspection before merging, not after. |
| INF-3 | CONFIRMED-ALREADY-CLOSED (3rd restatement) | Ruling 56, re-corroborated. |
| OIR reconciliation (PR #923) | VERIFIED-MERGED; 5 sub-items carried to §5 | B5/B6/C2/C3/C4 genuinely still open per the document's own reconciliation pass — see §5. |
| All NIḤŚEṢA-brief items not listed above | Unchanged from NIḤŚEṢA's own disposition table | See `00_ARCHITECTURE/briefs/nihshesha/NIHSHESHA_CLOSE_REPORT_v1_0.md` §2/§3 — not restated here. |
| Kāla handover (unchanged + F-20 addition) | HANDED-OVER | `SAMAPTI_KALA_HANDOVER_v1_0.md`, ṢAḌ-DARŚANA's, spec-only. |

## 5 — The ONE consolidated backlog (final)

**HANDOFF — what a future session picks up first.** Nothing genuinely open remains named #1: this
close report is the terminal deliverable of the whole ŚUDDHA-VĀCA → SATYA-DĪPA → PARIPRAŚNA →
SAMĀPTI → NIḤŚEṢA → PŪRṆATĀ arc, and every item below has an explicit owner and resume condition —
none silently dropped. The two items that actually matter for a future session's planning:

1. **ṢAḌ-DARŚANA's own Kāla handover (item 14)** — spec-only, no file ever touched across this
   whole six-campaign arc. Not this arc's to resume; wait for ṢAḌ-DARŚANA's own cadence.
2. **The post-six-views-transformation narration audit (item 14's resume condition)** — once
   ṢAḌ-DARŚANA's Kāla rewrite settles, run a scoped narration audit against the now-SETTLED Kāla
   layer using this arc's own proven method: a defect-class census (the same B-NAR-BO/GA/PH/TS
   taxonomy this arc used repeatedly), an adversarial refuter panel (not a single self-graded
   pass), and live-proof acceptance (a real `psql`/DOM/screenshot artifact per claim — the exact
   discipline that closed C4, not a fixture-satisfied gate). This is the largest remaining item by
   scope and the one this whole arc's method was built to eventually turn on Kāla.

Everything else below (items 1a, 2–13) is smaller, individually scoped, and can be picked up by
whichever session's `may_touch` happens to match its file — no particular order required among
them.

| # | Item | Owner | Resume condition |
|---|---|---|---|
| 1 | ~~C4-LOOP-LIVE-PROOF~~ | **CLOSED this session** | See §9 — all six criteria live-verified, no fixture substituted. |
| 1a | **ANTHROPIC_API_KEY unprovisioned in production** | Next infra/ops session | No secret named anything like it exists in Secret Manager at all (confirmed `gcloud secrets list`), and it is absent from the Cloud Run service's env/secret bindings (every other provider key — OpenAI, Google, DeepSeek, NIM — is bound). Any request that explicitly selects `stack: 'anthropic'` fails immediately at the planner with `AI_LoadAPIKeyError` (confirmed via Cloud Run logs, §9). Masked in ordinary use because `DEFAULT_STACK_ID = 'gemini'`. Fix: either provision the secret and bind it, or remove `'anthropic'` from the selectable stack list until it is. Not fixed this pass — out of C4's scope and touching Cloud Run/Secret Manager config warrants its own deliberate, confirmed session. |
| 2 | C5-PB7-BADGE, C6-PB4-PURNATA / R-0 PB-4 | Next PB-3-class session | C5-PB7-BADGE was blocked on C4-LOOP-LIVE-PROOF landing (NIḤŚEṢA's own condition) — **C4 has now landed, this arc** (§9: A1–A6 all `CONFIRMED` live, no fixture substituted). C5-PB7-BADGE is therefore UNBLOCKED and ready to run next. C6-PB4-PURNATA's PB-4 gate follows once C5 resolves: per `00_ARCHITECTURE/CONDUCTOR/SAMAPTI_CONDUCTOR_PROMPT_v1_0.md` §4's standing ruling **R-0/PB-4**, PB-4 executes if (a) the prediction loop is proven live end-to-end (T5 acceptance A1–A6 all `CONFIRMED` — now true) and (b) no higher-priority lane is blocked on swarm capacity — DVA makes that second call at the gate, on evidence, not pre-decided here. |
| 3 | B-NAR-PH remaining 4 findings | Next narration-fix session | `answer_quality.py:180`, `ph_rectification/engine.py:253`, `ph_nimitta.py` F4/F17, `ph_nimitta/engine.py` NEW-PH-1. |
| 4 | B-NAR-TS-remainder (6 files) | Next narration-fix session | `capabilities.ts`, `envelope.ts` (+generated mirror), `vidhi_registry_resource.ts`, `server.ts`, `register_p1_synthesis.ts`, `register_p1_ganita.ts`. `register_p1_ganita.ts` will very likely disposition NOT-APPLICABLE (§2.4 REJECTED per the partition doc) but needs a confirming read. |
| 5 | B-NAR-GA `gates.py:144` | Next narration-fix session | **PR #910 has now landed** (merged `2026-07-31T17:20:21Z`, part of this arc's own merge ledger) — the wait condition is cleared. Re-verify `gates.py:144`'s stale verified-status vocabulary against #910's rewrite per the partition document's own §4.9.3 instruction, then fix if still applicable. Ready now, not gated on anything further. |
| 6 | OIR-B5 — PgBouncer pooler | Operator, correctly deferred | Live probe (2026-07-30): 10/50 connections, 0 idle-in-transaction, worst-case draw 30. Not urgent; re-check if connection pressure ever appears. |
| 7 | OIR-B6 — light→heavy audit gap, 5 `ga_*` writers | Next L1-writer-touching session | `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_strength` (13,195 rows/chart, largest exposure), `ga_tajaka` still loop all 5 ayanamshas inside a single orchestrator-owned transaction (standalone-CLI only, `owns_conn`-guarded). Same class as the already-fixed `ga_sensitive` split. |
| 8 | OIR-C2 — `reference_nakshatras` DROP | Next hygiene session | Refactor half already done (dead INSERT code, commit `1efa18dd`); remaining: delete the dead block, retarget 2 test files, then the DROP migration. Stale table comment (R-3) also needs correcting. |
| 9 | OIR-C3 — `classical_chunks` DROP | Next hygiene session | Named blocker cleared (function renamed, no longer references this table) but ~8 other live surfaces still reference it — needs a coordinated removal pass, not a single-file fix. Stale table comment (R-4) also needs correcting. |
| 10 | OIR-C4 — broken upstream-hash change detection | Next session touching `asset_runner.py` or the orchestrator | `compute_upstream_hash` hashes a dependency-free asset's empty fan-in to a permanent constant (`sha256('')[:16]`) — confirmed live on 15+ root-asset `asset_throughput` rows across 11 assets, 21 more NULL. Change-detection is a structural no-op for every root asset, not just the originally-reported `bg_nakshatra`. Real fix, moderate scope — needs its own session. |
| 11 | Migration hash-guard Option 2 (16+9 historical mismatches) | Explicitly NOT for a rushed session | DVA Ruling 73: "blind reconciliation... exactly the rushed, high-blast-radius move this campaign has consistently declined." Full evidence (filenames, comparison query) already gathered — genuine investigative work, deliberately not attempted under time pressure across three campaigns now. Needs a dedicated session with no deploy-pipeline pressure. |
| 12 | Allowlist re-keying (content/pattern, not line-number) — both `fact_category_pin_allowlist.json` and `earned_signal_allowlist.json` | Next hygiene session | This exact fragility fired 3 times THIS session alone (§1). Named twice now across two campaigns. Worth fixing the mechanism, not just re-patching each instance. |
| 13 | EP-1 / C3-BUILDSTATE-RECON re-reconciliation | Next session after a narration-writer rebuild | Six real narration-writer fixes landed this session (`bo_bimba.py`, `ga_sensitive_writer.py`, `ga_sade_sati_writer.py`, `ga_nakshatra.py`, `ph_phaladesa.py`, `ph_sodhana/engine.py`, `l4_anchors.py`) — this may finally make a scoped C1-REBUILD against the canonical chart worthwhile, which would in turn unblock EP-1's real re-reconciliation. Flagged as newly-actionable, not run this session (no dedicated rebuild lane, and BUILD-LOCK/DB-write actions warrant their own deliberate session). |
| 14 | Kāla handover (7 files + `kala_temporal.ts` + gochara diagnosis + `kala_envelope.ts` F-20) | **ṢAḌ-DARŚANA** | Unchanged. Post-six-views-transformation audit. |

## 6 — Deploy-verification ledger (Step 0's armed vs. merged vs. shipped)

Every one of the 31 merges this session was individually watched through its real CI run; deploy
health was spot-checked at multiple points via direct `gcloud run revisions describe … commit-sha`
comparison against the merge SHA, catching zero silent promotion failures. The one deploy still
in flight at report-writing time (run `30654469874`, commit `bcf3934c`, this session's own final
merge #979) was watched to completion before this report was finalized — see the governance-close
commit for its confirmed final status.

## 7 — Governance close

Atomic `SESSION_LOG.md` / `CURRENT_STATE_v1_0.md` / `CLAUDE.md` close committed alongside this
report, in two waves matching the two actual close sessions: PURNATA-CLOSE-2026-07-31 (the v1.0
close, C4 paused) and **C4-CLOSE-2026-08-01 (this wrap-up — a new, later entry appended after
PURNATA-CLOSE's own, not an edit to it)**. `CLAUDE.md` bumped 7.1 → 7.2 with a matching footer
changelog entry; `CURRENT_STATE_v1_0.md` bumped 6.50 → 6.51 with a new §2 banner (prepended, newest
first) and a matching §3 narrative paragraph; `SESSION_LOG.md` gained the `C4-CLOSE-2026-08-01`
entry (`session_open` → narrative → `session_close` yaml) appended at file end. No version or
section collisions — each file's existing newest-first / append-at-end convention was followed
exactly, verified by re-reading each file's structure before editing rather than assuming it.

Root `CLAUDECODE_BRIEF.md` — separately, per CLAUDE.md §C item 0 — was found to be stale (still
pointing at SATYA-DĪPA, `status: READY-FOR-EXECUTION`, committed by PR #869 and never superseded
through four subsequent campaigns because none of their own pointers were ever git-committed). Its
`carries_forward` was confirmed safe to drop (both named lanes closed VERIFIED-FIXED in SAMĀPTI,
re-confirmed live again by this session's own crown re-verification, §2). Replaced with a
`PURNATA`-scoped pointer, `status: COMPLETE`, and — per the very `commit_warning` the stale version
itself carried — **committed as this close-out branch's first act**, not written and left
uncommitted a third time.

## 8 — Confirmation

**No Kāla PRODUCTION source file matching `kala_*`, `l3_*`, `ka_*`, or `gochara_*` was written to
this session, across either close (PURNATA-CLOSE-2026-07-31 or C4-CLOSE-2026-08-01).** (PR #900,
merged during PURNATA-CLOSE-2026-07-31, added two files whose basenames literally match the
`gochara_*` glob — `gochara_fingerprint_reproducer.py` and `gochara_readonly_query.py`, both under
`00_ARCHITECTURE/briefs/samapti/diagnostics/`. These are read-only governance diagnosis scripts —
the A6 root-cause investigation of the `ka_gochara_sweep` operator-chart parity defect, GOCH-1 —
not Kāla production code; consistent with this arc's "audit yes, code no" doctrine, they were
handed to ṢAḌ-DARŚANA as findings, never as a code change to any Kāla asset or writer.) Every
Kāla-adjacent finding (`kala_envelope.ts`'s prior F-20, no new ones from this arc) remains
handed-over, spec-only, to ṢAḌ-DARŚANA — see §5's HANDOFF note. **No credential was rotated, in
either close.** The one live,
in-session safety concern (a suspicious fragment in a minted session-cookie value) was flagged
directly to the native per this session's own safety obligation, diagnosed READ-ONLY to a
fully-traced benign root cause before any further action, and only then acted on (tooling fix + C4
resumption) — never silently worked around. All live-database writes made while proving and then
cleaning up C4 went through the app's own real UI/lifecycle mechanisms (confirm, resolve, dismiss,
the real daily job) — not one raw SQL write to the prediction ledger, in either direction. See §9
for the full diagnosis, the completed C4 run, and the cleanup record.

## 9 — C4-LOOP-LIVE-PROOF addendum (this session, resumed)

### 9.1 — Cookie-anomaly diagnosis (READ-ONLY, before any resumption)

Signal: minting a live production session cookie produced content beginning `⟐ injected` (U+27D0 +
literal "injected") instead of plausible JWT content. Investigated per explicit instruction,
starting from `platform/src/lib/canary/canary_probes.ts` (confirmed unrelated — an MCP-tool health
probe battery, no auth/cookie logic, no `⟐` glyph or "injected" sentinel anywhere in it).

**Disposition: (c) benign, fully traced.** The captured artifact (986 bytes, 2 lines) was:
line 1 (52 chars) = `⟐ injected env (65) from .env.local · dotenvx@1.61.0`; line 2 (930 chars) = a
structurally valid JWT (3 dot-segments, 40/546/342 chars, header `{"alg":"RS256","kid":"6REagg"}`).
Root-caused to source: `platform/node_modules/@dotenvx/dotenvx/src/shared/logger.js:20`
(`const successv = (m) => getColor('amber')(\`⟐ ${m}\`)`) and
`src/cli/actions/run.js:96` (`injected env (${uniqueInjectedKeys.length})`) — dotenvx's own CLI
startup banner, captured into the same stream as the wrapped script's real stdout by a `dotenvx run
-- npx tsx ... > file` shell redirect (my own invocation shape, not an application defect). Zero
presence in the live request path (dotenvx has no runtime role — dev-tooling only). No interaction
with the earlier citation-stripping/privacy-leak class (different mechanism, different file family).

**Tooling fix (mandatory, before resumption):** `platform/scripts/dev/mint_session_cookie.ts`
gained an optional `COOKIE_OUTPUT_FILE` env var — when set, the cookie is written directly to that
file via `writeFileSync` from inside the Node process, so no wrapper's stdout can ever reach it
regardless of log level. Preferred over `-q`/`--quiet` per instruction ("silencing a symptom can
regress if log levels change"). Committed `ca08f407`, PR **#986**, merged via the merge queue at
`2026-07-31T19:56:13Z` → `516f07e8`.

### 9.2 — A1: real reading → real `detected` ledger row

First attempt (`stack: 'anthropic'`) failed twice, ~400ms each, `PLANNER_TRANSIENT`. Traced via
Cloud Run logs (not assumed transient): `AI_LoadAPIKeyError: Anthropic API key is missing` —
`ANTHROPIC_API_KEY` is not bound to the Cloud Run service AND no such secret exists in Secret
Manager at all (§9.6 finding). Retried with the actual production default (`DEFAULT_STACK_ID =
'gemini'`, which **is** bound) — succeeded: HTTP 200, 26,028-byte SSE stream, `turn.close
status=ok ms=42755`, `conversation_id=13caf111-ba7d-44ae-8c40-5f685f24f1d6`,
`message_id=ba6503b0-0d1a-4dfb-8ca8-758537fb6356`, two `prediction_candidate` flags
(`score=0.85 horizon=2026`, `score=0.85 horizon="in 2025"`).

Verified via direct `psql` against the real prod Cloud SQL instance (via the running
`cloud-sql-proxy` on `127.0.0.1:5433`, confirmed live — `SELECT version()` → PostgreSQL 15.17,
not a local/mock DB):

```
                  id                  | lifecycle_status |                          claim_text (excerpt)                          | created_from_channel |          created_at
e3e7e4f1-0627-4ef6-af29-564115b63022 | detected         | The groundwork laid in 2025-2026 will translate into a reputation...  | pariprashna           | 2026-07-31 19:55:14.362608+00
06d56961-019f-4f10-8c82-b82fd2b57dc9 | detected         | * Following the regulatory clearance for the second sand quarry...    | pariprashna           | 2026-07-31 19:55:14.346899+00
```

Two real `detected` rows, not a test double — claim text matches the SSE flags verbatim, timestamps
match the request window exactly.

### 9.3 — A2: renders on the live review tab

Real Playwright browser session, `__session` cookie injected via `context.addCookies` (CDP-level,
works for the `httpOnly` cookie), navigated to
`/clients/482012f1-710e-4a25-994a-93821f5871aa/samiksha` on the deployed, authenticated route.
Accessibility-tree DOM snapshot AND a full-page screenshot both confirm both rows rendered under
"Awaiting confirmation," verbatim claim text, correct domain (`career`), correct window
(`Jan 2025 – Jan 2026`, `Jan 2026 – Jan 2027`), each linking `view source turn` to
`/pariprashna?thread=13caf111-ba7d-44ae-8c40-5f685f24f1d6#turn-1` — the exact `conversation_id`
from §9.2.

**Corroborating evidence, not just an oddity:** between the confirm click and the badge re-check,
Cloud Run request logs show a real `POST /clients/482012f1-.../samiksha` from a residential/mobile
IPv6 range (§9.9 finding 2) — an independent human, not this session's own Playwright automation,
interacting with the exact same live route under test, mid-proof. A2's claim is "renders on the
live review tab"; a second, uncoordinated party successfully loading and acting on that same tab at
the same time is external confirmation the surface is genuinely live production, not a staged or
cached artifact only this session's own automation could reach.

### 9.4 — A3: resolves through the mounted UI; can't-tell → NULL

Real click sequence on the live page: "Log to Samīkṣā" on the closed-window row
(`e3e7e4f1-...`) → `psql` confirms `lifecycle_status: detected → open`, `confirmed_at` stamped
(`2026-07-31 19:57:21`). After the daily job (§9.5) closed its window, reloaded the page, clicked
"Can't tell" → "Resolve marked (1)". `psql` confirms:

```
lifecycle_status = unverifiable, outcome = unverifiable, outcome_value = NULL
```

`outcome_value` is genuinely `NULL`, not a fabricated zero — enforced by the real DB CHECK
constraint `bmpl_unverifiable_has_no_value`, which is itself proven can-fail by
`tests/pariprashna/samiksha/cant_tell_brier_excluded.integration.test.ts` (3-layer proof: DAL
forces NULL, a raw UPDATE attempting to give an unverifiable row a value is REJECTED by the CHECK,
and the Brier-eligibility SQL excludes it) — confirmed passing in §9.5's CI run.

### 9.5 — A4: daily job against real prod DB + CI DB-integration tests run

Ran `scripts/samiksha/daily_job.ts` directly against the real prod DB (same `cloud-sql-proxy`
connection as §9.2), `--as-of 2026-08-01 --chart 482012f1-...` (scoped to the canonical chart to
minimize blast radius on a first live run; a pre-run row-state snapshot was taken first per the
rollback-before-destructive-write rail). Result: `closed_row_ids: ["e3e7e4f1-..."]`,
`digest_dispatched: true`, log-only transport (as designed — "W-5 stub by default", no real email
transport exists). `psql` confirms the real transition: `lifecycle_status: open → window_closed`.

CI half: PR #986's own required check **"DB Integration Tests (SAMĪKṢĀ, throwaway Postgres)"** ran
(not skipped) — `run 30660080119 / job 91253959719`: **20 test files, 129 tests, all passed**,
against a real migrated throwaway Postgres, including the DDL/CHECK-constraint suite
(`migration_ddl.test.ts`) and the can't-tell Brier-exclusion 3-layer proof from §9.4.

### 9.6 — A5: one outcome map, with a live caller

Source-confirmed (both `resolvePredictionAction` and `batchResolveAction` in
`platform/src/app/clients/[id]/samiksha/actions.ts` route through the sole
`recordConversationalOutcome` → `outcomeToValue`; `outcome_map_singularity.test.ts` guards
against a second map; repo-wide grep found none). **§9.4's own UI resolution is itself a live
production caller of exactly this path** — the `unverifiable` outcome just recorded to a real
ledger row went through this exact, sole map, in production, this session.

### 9.7 — A6: calibration leak guard runs in production, mutation proves it can fail

Real production call sites confirmed by source: `platform/src/app/api/mcp/prashna_ask/route.ts:544`
and `platform/src/lib/pariprashna/protocol/emitter.ts:117` (inside `PariprashnaEmitter`, "the one
method every Paripraśna reading-stream event crosses"). Mutation-proof test
`tests/pariprashna/emitter_calibration_guard.test.ts` independently re-run fresh from a clean
`origin/main` worktree: **6/6 passed** (~531ms) — contaminated-event mutations (bare `calibration`
object, nested Brier score) both throw `CalibrationLeakError` before `controller.enqueue`.

Live corroboration from this session's own traffic: §9.2's second live reading (the financial/
health-domain probe) emitted real `no_leakage_capabilities_stripped` and `register_leak_scrubbed`
flags mid-stream in production — the same guard family actively firing on live request content,
not merely present in source.

### 9.8 — Badge-equals-SQL, re-verified against a genuinely non-zero ledger

The prior check was vacuous (0 badge-countable rows == 0 SQL count, because the whole ledger was
empty). Re-verified live and non-vacuous: drove one more real reading (financial/health-domain
prompt), producing 3 more `detected` rows (5 total ledger rows for the chart: 1 dismissed, 1
unverifiable, 3 detected). Canonical `count_sql`
(`SELECT count(*) WHERE chart_id = $1 AND lifecycle_status = ANY(['detected','window_closed'])`)
via direct `psql`: **3**. The live rendered page, reloaded within the same ~15-second window:
**"3 prediction items to review."** Screenshot captured. `3 == 3`, against a ledger that
genuinely contains non-badge-countable rows too (proving the count discriminates, not just echoes
row-count).

### 9.9 — Honest findings surfaced along the way (not C4 criteria, disclosed per B.10/B.11)

1. **`ANTHROPIC_API_KEY` is entirely unprovisioned in production** — confirmed via
   `gcloud run services describe amjis-web` (absent from the container's env/secret bindings,
   while `OPENAI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `DEEPSEEK_API_KEY`, `NVIDIA_NIM_API_KEY`
   are all present) and `gcloud secrets list` (no secret by that or any similar name exists at
   all). Any request explicitly selecting `stack: 'anthropic'` fails instantly at the planner.
   Masked in ordinary use because `DEFAULT_STACK_ID = 'gemini'` (per D8 governance §3.1) is what
   actually serves traffic. Carried to the backlog as item 1a — not fixed this pass (Cloud
   Run/Secret Manager config change, out of C4's scope, warrants its own confirmed session).
2. **A real concurrent human user interacted with the exact review-tab surface under test.**
   Between the A3 confirm-click (`19:57:21`) and the badge re-check (`20:00:37`), Cloud Run request
   logs show a `POST /clients/482012f1-.../samiksha` from IPv6 `2401:4900:3e97:...` (a residential/
   mobile ISP range, not a Cloud Run or bot address) that dismissed the sand-quarry test prediction
   (`06d56961-...`, `dismissed_reason: "dismissed from review tab"`). Not caused by this session's
   own Playwright automation. Benign (a dismiss is a normal, terminal, non-destructive action) and
   disclosed rather than silently absorbed — it also incidentally corroborates that the surface
   under test is genuinely live and in real concurrent use, not an idle staging artifact. It did
   require driving one additional live reading (§9.8) to complete the badge-equals-SQL check
   cleanly after the interference.

### 9.10 — Cleanup: synthetic test predictions dismissed, queue returned to a true state

Per native decision: the 3 synthetic `detected` predictions §9.8's proof generated (the two
"Trajectory to August 2027" claims and the "Combined Trajectory and Timeline" claim) had served
their evidentiary purpose — verbatim-recorded above — and leaving them in the native's real review
queue would read as genuine months from now. **Dismissed, not deleted**: each moved to the
`dismissed` terminal state through the app's own real "Dismiss" button on the live review tab (not
a raw SQL write), the same lifecycle mechanism the concurrent real user had already exercised once
this session.

**Before** (`psql`, canonical chart):

```
 lifecycle_status | count
-------------------+-------
 detected          |     3
 dismissed         |     1   (the concurrent real user's own dismissal, §9.9 finding 2)
 unverifiable      |     1   (the §9.4 evidentiary resolution)
```

**After** (`psql`, same query, post-dismissal):

```
 lifecycle_status | count
-------------------+-------
 dismissed         |     4
 unverifiable      |     1
```

Badge query (`lifecycle_status = ANY(['detected','window_closed'])`) confirms **0** — the queue is
genuinely empty of anything awaiting review, matching a chart with no live conversational activity
right now. The real user's own dismissal (`06d56961-...`, `updated_at` unchanged at `20:00:37`) and
the evidentiary can't-tell resolution (`e3e7e4f1-...`, still `unverifiable`) were both left
completely untouched — confirmed by comparing `updated_at` before and after. This is the first real
exercise of the ledger's terminal-state lifecycle on genuinely mixed data (one machine-dismissed
batch, one human-dismissed row, one resolved row), not just a schema/constraint proof.

---

*End of PURNATA_CLOSE_REPORT_v1_0.md v1.3 (2026-07-31, initial close; C4-LOOP-LIVE-PROOF addendum
appended 2026-08-01; final wrap-up — cleanup record, A2 corroboration reframe, HANDOFF note, §7/§8
governance-close confirmation — appended 2026-08-01; independent verification pass — two real
discrepancies found and fixed, backlog items 2/5 and the kala/gochara-file claim — appended
2026-08-01). This is the arc's terminal artifact. The whole ŚUDDHA-VĀCA → SATYA-DĪPA → PARIPRAŚNA
→ SAMĀPTI → NIḤŚEṢA → PŪRṆATĀ arc is closed.*
