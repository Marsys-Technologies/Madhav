---
artifact: PURNA_VIRAMA_BRIEF (Full-Stop Close-Out Campaign)
canonical_id: PURNA_VIRAMA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION — single-session autonomous swarm; the LAST session of this arc
created: 2026-07-25
author: Fable (Cowork planning session, 2026-07-25)
classification: CLAUDECODE_BRIEF — autonomous swarm close-out (conductor reads this first)
mode: FULLY AUTONOMOUS · one Claude Code session · Conductor (Opus) + parallel Sonnet builders +
  one dedicated Opus Verifier that never builds · no human gates · DONE only on Verifier approval
  against LIVE PRODUCTION · wall-clock cap 6h
mission: >
  Close out EVERYTHING pending across the Elevation Campaign v2.1 → UAT-DARPANA → SATYA-ŚEṢA arc.
  "Closed" means DISPOSITIONED WITH EVIDENCE — VERIFIED-CLOSED where the work is done and proven,
  PARKED-HONEST where it is not — never "green by assumption". The native wakes to ONE consolidated
  report, a clean repo, and a register whose every item carries its final state.
prime_rule: >
  TRUTH OVER COMPLETION. This session's goal is that every thread is DISPOSITIONED, not that every
  thread is green. A PARKED-HONEST with evidence is a legitimate close. Faking green is the only
  failure mode.
governing_docs (read in §A, execute against, never contradict):
  - briefs/satya_shesha/SATYA_SHESHA_BRIEF_v1_0.md (W1–W6 + §1 live baseline + §5 rails)
  - briefs/satya_shesha/SATYA_SHESHA_W7_ADDENDUM_v1_0.md (W7 + the Offer Law + n=3 harness rule)
  - briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md (§9 verification · §15 matrix ·
    §16 CLEANUP — the migrate-first ordering is load-bearing)
  - uat_darpana/FABLE_HANDOFF_SUMMARY.md (the two vetoes + audit-rate finding)
  - ELEVATION_REGISTER_v1_0.md (EL-01..EL-62 — the item-of-record)
---

# PŪRṆA-VIRĀMA — the full stop

## §A — PHASE A: RECONCILE STATE FIRST (mandatory, serial, ~45min)

Nothing executes until reality is established. **The planner's summaries and this brief's own
assumptions are HYPOTHESES; the repo, the ledgers, git history, GitHub PR state, Cloud Run
revisions, and live production are the truth.** Audit, with evidence refs, the state of every
thread below, and write `briefs/close_out/PENDING_MANIFEST.md` — one row per thread:
`thread · expected-by-brief · actual (evidence: commit/PR/revision/probe) · verdict OPEN|DONE|PARTIAL`.

**§A.1 — PRE-RECONCILED PRIORS (native-relayed stream close reports, 2026-07-25).** Treat these as
strong priors to VERIFY cheaply — not re-derive, and not trust blindly either:
- SATYA-ŚEṢA W1–W6: CLOSED (PRs #784/785/787/788/790; report + ledger on main). Expect DONE.
- Stream α: run complete, 4 merges deployed+live-verified, own cleanup done. α ALREADY COMMITTED a
  run report + coverage matrix + flagship grading under 00_ARCHITECTURE/llm_consumption_audit/ —
  T3 must FIND and BUILD ON these, not duplicate them. α's flagship measurement: four fresh naive
  agents, 15–33% vs the ≥90% bar — NOT MET, honestly recorded.
- Stream β: CLOSED, 5/5 lanes dispositioned (amjis-sidecar rev 00912-rv7, commit 8fd9343b).
  VERIFIED-CLOSED incl. EL-30/40/47-writer/18-Manglik/19/39/49/51/17+CR-37 and the EL-15 substrate
  (sweep 303/303; protection ruling held — row count only climbed across 7 dispatches; FORENSIC
  7/7 every time). NOT-REPRODUCED: CR-131 (pre-campaign fix), EL-38 (argala zeros GENUINE — the
  serving disclosure is correct behavior). PARKED: 3 items blocked-on-α-files (α has since closed —
  RE-CHECK whether now unblocked; close if trivial, else re-park with the new evidence), MSR
  cascade + EL-17/CR-66 blocked on NATIVE RULING (route to ratification packet), EL-16/S3 scope.
- Stream γ: CLOSED (7 PRs incl. #780/781/783). Flagship honestly NOT MET (2/13, confirmed
  post-#782). Two process errors disclosed and corrected (Lane E verification delay; J/K2
  verified-but-unmerged, caught by git's branch-delete safety).
- NEW MCP surfaces confirmed live by tool-list observation: dossier, ganita_concept_locate,
  ganita_database_schema_get, ganita_planet_get, mcp_server_info, classical-text tools.
- KNOWN CLEANUP RESIDUE: the ROOT checkout is parked on an UNRELATED session's branch (α correctly
  refused to force-change it). β/γ worktree + elev/* branch state unverified. ~/elev-v2-shared
  still holds un-migrated evidence (STREAM_BETA_COMPLETE.flag, proxy ledgers).
- GOVERNANCE FINDING (raised INDEPENDENTLY by two streams — β's builder re α's relayed autonomy
  claim, and Lane G re the A-5 supersession): relayed authorization is unverifiable in
  agent-to-agent chains. T3 adds a register item: AUTHORITY-BY-ARTIFACT — a relayed "the native
  authorized X" is a pointer, never authority; the receiving agent MUST verify against the
  committed charter/ruling text before acting, exactly as β's builder did. Cite both incidents
  (STREAM_BETA_CLOSE_v1_0.md, proxy/beta.md).

Threads to reconcile (the complete list):
1. **SATYA-ŚEṢA W1–W6** — did the campaign run? Check for its branches/PRs, the ledger
   (`ledgers/SATYA_SHESHA_LEDGER.md`), the report, and LIVE behavior: does
   `ganita_chart_facts_get(keyword="gulika")` still return a bare empty? Does
   `gochara_forecast_get` carry a coverage block? Is `concept_locate` callable over live MCP?
   Is the kala/gochara family within budget? Did EL-62 + the partial-close annotations + the
   EL-24 heartbeat amendment + the 9.58-retirement addendum land in the register/report?
2. **W7 (flagship substance-inline)** — executed or not; if executed, what did the n=3 sealed
   harness score?
3. **Elevation Stream β** — final state of lanes D (indexing/rebuild), D2 (sahams/bhanga),
   C (sidereal/panchāṅga), G (remedies/corpus), T (gochara env + sweep). Check elev/beta branch,
   merged PRs, C4/C5 in CONTRACT_STATUS, implementations/*.live, STREAM_BETA_COMPLETE.flag.
   Probe live where cheap (e.g. `ref_planet_position_get` sidereal? saham category served?).
4. **Elevation Phase 4/5 close** — does `ELEVATION_V2_RUN_REPORT_v1_0.md` exist? Were per-EL
   dispositions appended to the register? Was the §15 matrix finalized? Were the native packets
   (LEL intake, ratification) produced? Was CURRENT_STATE/SESSION_LOG closed for the campaign?
5. **Elevation §16 cleanup** — do `.worktrees/{alpha,beta,gamma}` and `elev/*` branches still
   exist? Is `~/elev-v2-shared/` still holding un-migrated evidence (baseline, ledgers, proxy
   logs, frozen test assets)? Is `gc.auto` still 0? Any open elev PRs? Old flags?
6. **Gochara sweep integrity** — `kala_gochara_windows` count for 482012f1 and
   `build_substep_progress` intact (read-only check; this data is untouchable).
7. **Root CLAUDECODE_BRIEF.md** — currently points to SATYA-ŚEṢA; confirm and note.

**Rule: never redo done work.** A thread the evidence shows DONE gets its evidence ref copied into
the close report and nothing else. A thread PARTIAL gets only its residual executed.

## §B — PHASE B: EXECUTE THE OPEN REMAINDER (parallel tracks; spawn only what the manifest opens)

Conductor spawns one Sonnet builder per OPEN track, fully parallel, disjoint file ownership
(cross-needs → Conductor serializes those two only). The Opus Verifier is spawned at Phase-A end
and G4-verifies each track against LIVE production, BOTH canonical charts
(482012f1-710e-4a25-994a-93821f5871aa, 1c826d5a), per the parent briefs' acceptance lines.

- **T1 — SATYA-ŚEṢA remainder (W1–W6):** execute per its brief §2–§5, exactly, for whichever items
  Phase A found OPEN/PARTIAL. Its §1 baseline probes are re-runnable as the before-payloads.
- **T2 — W7 flagship substance-inline:** execute per the addendum §2, acceptance per its §3 —
  including the **n=3 sealed-harness runs, median ≥12/13, harness UNTOUCHABLE**. If the median
  lands below the bar after a genuine fix cycle (3 retries → Opus escalation → 2 more), the
  disposition is PARKED-HONEST with the actual scores — the number is the finding, never the enemy.
- **T3 — Elevation close-out (docs + verification, no new construction):**
  (a) Phase-4 revalidation — re-run the G4 probe set of every EL previously VERIFIED-CLOSED
  against the CURRENT production head; downgrade any regression to PARKED-HONEST before reporting.
  (b) Finalize the §15 matrix: every EL-01..EL-62 row carries its final disposition + evidence ref
  (β items Phase A found incomplete are PARKED-HONEST with their actual state — **do NOT build β's
  unfinished lanes now**; writer/rebuild work is out of scope for a close-out).
  (c) Append the dispositions to the register (append-only discipline).
  (d) Write `ELEVATION_V2_RUN_REPORT_v1_0.md` (charter §14 shape) from the ledgers — honest
  scorecard, including the flagship trajectory: 2/13 baseline → #782 flat → W7's measured result.
  (e) Assemble the two native packets if missing (LEL intake surface pointer + ratification packet
  listing every PROXY-RULED decision of the whole arc, one recommended disposition each). The
  packet MUST include the decisions the streams explicitly queued to the native: the MSR-cascade
  ruling, EL-17/CR-66, the A-5 supersession review, and the two authorization-chain incidents —
  each with evidence ref + recommended disposition.
  (f) The AUTHORITY-BY-ARTIFACT register item per §A.1, with both incident citations.
- **T4 — §16 cleanup (STRICTLY AFTER T3's evidence needs are known; order is load-bearing):**
  MIGRATE first — everything in `~/elev-v2-shared/` worth keeping (baseline, run ledgers,
  integration log, proxy ledgers, PREFLIGHT/CI-state, contracts, frozen test assets: sealed
  harness, routing suite, dark-corpus replay set → they become STANDING regression assets) into
  `00_ARCHITECTURE/llm_consumption_audit/ledgers/elevation_v2/`, merged to main. ONLY THEN delete:
  the three `.worktrees/*`, every `elev/*` and `satya-shesha/*` branch local+origin once merged,
  stale flags/locks, `~/elev-v2-shared/` itself, any leftover contract stubs. RETAIN all snapshot
  tags + DB snapshots. RESTORE `gc.auto` by UNSETTING it. `git worktree prune` ONLY from
  /Users/Dev/Vibe-Coding/Apps/Madhav. RESTORE THE ROOT CHECKOUT TO MAIN per §A.1 — safely: inspect
  for uncommitted/unpushed work first, stash-and-note or park if found, never force-discard.
  Touch NOTHING this arc did not create (`.claude/worktrees/*`,
  `../madhav-wave-vidhi-purnata`, non-arc branches). Reverse-citation grep before every deletion.

**Standing rails (bind every track):** main is branch-protected — merge ONLY via
`git push origin <branch> → gh pr create --base main → gh pr merge --auto --squash`; hold until
actually merged, 30-min red-check ceiling, release on every exit path; CI (Node 20) is the arbiter;
batch merges per track. `platform` auto-deploys on main; **`amjis-mcp` deploys EXPLICITLY** —
confirm revision + image SHA before any G4 probe. **Serving-side + docs ONLY: no writers, no
migrations, no rebuilds, no touching `kala_gochara_windows` or `build_substep_progress`, no FROZEN
orchestrator, no sealed L5 split, no FORENSIC anchors.** Anything seeming to need those →
PARKED-HONEST. `git tag purna-virama-start` before the first commit. Never weaken an acceptance
criterion or modify a grader to pass — park honest instead. Any question you'd ask a human: answer
it yourself, log the ruling + rationale.

## §C — PHASE C: FINAL VERIFICATION + GOVERNANCE CLOSE (serial, Verifier-led)

1. **Full regression battery** against the final production head: SATYA-ŚEṢA §1's verified-FIXED
   list (mechanisms, gulika category serve, health DOSHA window, tool_search steering) + every
   acceptance line closed in Phase B + the elevation baseline's fixed set. Any failure → reopen,
   fix once, or downgrade honestly.
2. **The consolidated close report** — `briefs/close_out/PURNA_VIRAMA_REPORT_v1_0.md`:
   the Phase-A manifest with final verdicts · per-track dispositions + evidence refs · the flagship
   trajectory with W7's real n=3 scores · the W6 claim-detector dry-run result over the 45 DARPANA
   answers (how many unaudited absence/coverage claims existed — the honest bound on hidden
   S4-05s) · every proxy ruling of this session · deploys shipped (revisions + SHAs) · cleanup
   evidence (§16.6 positive checks: no elev/* branches, clean root on main, migrated ledgers
   readable, gc.auto unset, no open arc PRs) · every PARKED-HONEST residual with its evidence and
   a sized follow-up recommendation · one paragraph: the state of the instrument against the §0
   depth mandate, stated plainly.
3. **Atomic governance close:** CURRENT_STATE §2 updated (arc closed, pointer to the report);
   SESSION_LOG entry; root `CLAUDECODE_BRIEF.md` flipped to **COMPLETE** with a pointer to the
   report — the first COMPLETE flip of this arc, and only if every §16.6-style positive check
   passes. If any check fails, the brief stays ACTIVE and the report says exactly why.
4. **Verifier's final act:** a one-page disposition table — every thread from §A, its final state,
   its evidence. No thread may be absent. Four dispositions only; no "passed with caveats".

---

## §D — KICKOFF PROMPT (paste into Claude Code at /Users/Dev/Vibe-Coding/Apps/Madhav)

```
You are the CONDUCTOR of PŪRṆA-VIRĀMA, the close-out campaign for the entire Elevation →
UAT-DARPANA → SATYA-ŚEṢA arc. FULLY AUTONOMOUS, no human available, no human gates. A dedicated
Opus Verifier that never writes code owns DONE. PRIME RULE: truth over completion — every pending
thread must end DISPOSITIONED WITH EVIDENCE; PARKED-HONEST is a legitimate close; faking green is
the only failure mode.

Read first: 00_ARCHITECTURE/llm_consumption_audit/briefs/close_out/PURNA_VIRAMA_BRIEF_v1_0.md —
then its governing docs list, in order.

PHASE A (serial, do this yourself): reconcile ACTUAL state vs expected for all 7 threads in §A —
git/PR/ledger/Cloud-Run/live-probe evidence, not summaries. Write PENDING_MANIFEST.md. Never redo
done work; execute only what the manifest opens.

PHASE B (parallel): spawn one Sonnet builder per OPEN track (T1 SATYA-ŚEṢA remainder · T2 W7
substance-inline with the UNTOUCHABLE sealed harness at n=3 median ≥12/13 · T3 elevation close-out
docs + Phase-4 revalidation + register dispositions + run report + native packets · T4 §16 cleanup,
MIGRATE-FIRST then delete, prune only from the canonical path, retain all snapshots). Standing
rails: PR+auto-merge only (main is protected), amjis-mcp deploys explicitly, serving-side + docs
only — no writers, no migrations, no rebuilds, kala_gochara_windows and build_substep_progress are
untouchable. git tag purna-virama-start first. Escalate a builder to Opus after 2 failed verify
cycles; park honest after 5.

PHASE C (serial): Verifier runs the full regression battery against the final head, then the
consolidated PURNA_VIRAMA_REPORT_v1_0.md, then the atomic governance close — CURRENT_STATE,
SESSION_LOG, and root CLAUDECODE_BRIEF.md flipped to COMPLETE only if every positive cleanup and
regression check passes. The Verifier's final disposition table must cover every §A thread; four
dispositions only; no "passed with caveats".

Wall-clock cap 6 hours. Any question you would ask a human, answer yourself and log the ruling.
Begin with Phase A.
```

---

*End of PURNA_VIRAMA_BRIEF v1.0. The arc that started with "the product is mediocre because what
is computed is not served" ends here — with every claim it now makes either proven against live
production or honestly marked as not yet true. That is the whole point.*
