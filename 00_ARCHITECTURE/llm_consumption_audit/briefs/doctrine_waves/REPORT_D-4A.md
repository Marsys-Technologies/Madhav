---
artifact: REPORT_D-4A
type: WAVE CLOSE REPORT
wave: D-4a — Measurement Foundry
status: CLOSED — GATE GREEN 7/7
closed_on: 2026-07-19
conductor: Claude Code (Sonnet 5), fully autonomous per native directive
governing: BRIEF_D4A.md, BIND_D-4A.md, CONDUCTOR_PROTOCOL.md, ESCALATION_POLICY_v1_0.md
---

# REPORT_D-4A — D-4a "Measurement Foundry" Close Report

## §1 — Summary

D-4a ran end-to-end, fully autonomously, per the native's kickoff directive. 6 implementer lanes
(A-0 through A-5) plus 1 docs-only lane (A-6) executed in the declared merge order (A-0 → A-1 ∥ A-2
→ A-3 → A-4 → A-5; A-6 anytime), each in an isolated git worktree, each independently adversarially
verified by a fresh-context Opus verifier before being treated as done, per CONDUCTOR_PROTOCOL's
"unverified = not done" standard. **Gate result: GREEN, 7/7 criteria pass** (full evidence in
BIND_D-4A.md §7 and the live gate-runner pass below). Zero REJECT verdicts. Zero circuit-breaker
trips, including on the wave's highest-stakes check (Lane A-3's mandatory non-contact with the
sealed LEL test split, ≥2020-01-01).

## §2 — Promise ledger (final disposition)

All rows from BIND_D-4A.md §5 — CLOSED:

- [x] A-0: CR-109 fixed (migrations 454/455, `period_windows` cardinality model; full-span
      birth→birth+100y serving; live-verified `kala_activation` 49,705→332,239 rows)
- [x] A-0: CR-110 reproduced and fixed (ayanamsha-scoping bug in `ka_avadhi.py`; Mercury MD
      duplicate row eliminated)
- [x] A-0: CR-111 reproduced and fixed (field-name mismatch in `kala_temporal.ts`'s
      `fetchCapabilityRows`; convergence_count 0→50 live)
- [x] A-0: D-3 per-event artifacts rescued to `artifacts/D-3/`
- [x] A-0: canonical_faces.json +3 tools, census 135→138
- [x] A-1: CR-47 matcher root-cause fixed, DR-13-speced (point/interval/chain, tolerance scaling)
- [x] A-1: LEL schema v2 additive migration (457) applied live
- [x] A-1: 4 native corrections ingested append-only with provenance; #3 (dialogues-2001)
      correctly QUARANTINED, not ingested
- [x] A-1: windfall interval [2010-07→2011-03] applied
- [x] A-1: items #1/#5 arc linkage encoded; #7 onset day-locked to arthroscopy event
- [x] A-1: leverage_index `subject=venus` false-empty FIXED (not deferred)
- [x] A-2: event-class ontology published — extended pre-existing `brahma_event_ontology`
      (migration 388) to 27 classes with full DR-13 shape data, rather than duplicating it
- [x] A-3: shuffled-birth + antiphase controls real (52/52 tests independently re-run and passing)
- [x] A-3: CRPS/log-score implemented, skill formula independently verified correct
- [x] A-3: control-mirroring enforced structurally, live refusal demonstrated
- [x] A-3: sealed LEL test split (≥2020-01-01) — ZERO contact, structurally verified (no
      DB/network/fs access path exists in the harness code A-3 built)
- [x] A-4: prediction store live with claim_shape validation (live adversarial INSERT tests:
      shape-mismatch, missing-falsifier, whitespace-falsifier, filing-method-bypass all rejected)
- [x] A-4: LEL-append→outcome-matching hook demonstrated live against a clearly-marked test fixture
- [x] A-4: 5 falsifier-bearing entries filed incl. the 3 named baseline-arc predictions
- [x] A-4: §11 governance text served in both write-path response payloads, filing_method
      structurally pinned to `explicit_filing_tool` (chat-mining is impossible, not just discouraged)
- [x] A-5: 3 models attempted; pratyantar_lord scored end-to-end, midpoint_triangle/transit_kernel
      honestly reported as gaps (B.10 — no fabricated computation)
- [x] A-5: pre-registration (`03b226f7`) provably precedes scoring (`00d1a9d5`, +3.5min)
- [x] A-5: DR-12-deferral disclaimer embedded in all 4 committed artifact locations
- [x] A-5: doctrinal guardrail swept clean — no ruling-language crossing into DR-12 adjudication
- [x] A-6: DR-14/15/16 registered as DIS.027-029; ARC PLAN status DRAFT→RATIFIED (stale stamp
      corrected, native-confirmed ratified-in-fact 2026-07-19)
- [x] Carried D-2 findings #1 (leverage_index) fixed via A-1; #3 (canonical_faces) fixed via A-0;
      #2 (nodal-exaltation) and #4 (judgment_query oversize) PARKed to D-4b with named ownership
- [x] Anti-gaming pass on all lanes — no gaming signals found
- [x] Gate item 7 ("all prior batteries green") — read per BIND §2 ruling as "no new regression
      since D-3's sealed state"; D-3's own carried RED excluded, correctly not re-litigated

## §3 — Gate runner result (§G, live against deployed connector)

| # | Criterion | Result |
|---|---|---|
| 1 | A-0 live assertions | PASS |
| 2 | Matcher | PASS |
| 3 | Ontology published + consumed | PASS |
| 4 | Controls real, mirroring enforced | PASS |
| 5 | Dry-run complete | PASS |
| 6 | Ledger live | PASS (one verification-method limitation — §11 wire-response not exercised via authenticated HTTP in this non-interactive session; substance independently confirmed via source-trace + DB CHECK constraint) |
| 7 | Findings dispositioned + anti-gaming + no new regression | PASS |

**Overall: GATE GREEN.**

## §4 — Verification summary (per-lane)

| Lane | Verdict | Findings |
|---|---|---|
| A-0 | ACCEPT-WITH-FINDINGS | 2 (rollback-pin staleness, stray comment) — both fixed via follow-up PR #610 + BIND update |
| A-1 | ACCEPT-WITH-FINDINGS | 2 (stale migration-ledger duplicate name; brief-text/data-doc quarantine wording mismatch) — both non-blocking, recorded |
| A-2 | ACCEPT-WITH-FINDINGS | 2 (stale row-count snapshot; cross-lane forward-fix should have re-opened A-2) — both non-blocking, recorded |
| A-3 | ACCEPT (clean) | 0 — highest-stakes check (sealed test-split contact) structurally verified clean |
| A-4 | ACCEPT-WITH-FINDINGS | 2 (demo-script paper-trail gap; §11 wire-response verification-method limitation) — both non-blocking |
| A-5 | ACCEPT (clean) | 0 — doctrinal guardrail (no DR-12 adjudication language) swept clean |

Zero REJECT. Zero circuit-breaker trips. One cross-lane issue (A-1 fixing A-2's broken migration
forward) logged as a defensible, minor lane-isolation deviation, not a defect — see BIND §5b item 8.

## §5 — Deploy record

All merges landed on `main` via PR, CI-gated ("CI — Ganga Quality Gate" + "TAP CI" both required
green), then deployed via `workflow_run`-triggered `deploy.yml`, then live-SHA-verified via
`gcloud run services describe` before proceeding to the next lane. Final live state:

- `amjis-web` @ `86e9954d` (matches `origin/main` HEAD exactly)
- `amjis-sidecar` @ `e995c498` (A-0-fix, last commit touching python-sidecar paths)
- `amjis-mcp` @ `8f3ace37` (A-0's PR #608, last commit touching platform-mcp paths)
- `brahma-build-pipeline-job` @ `e995c498` (matches sidecar — shared image)

Rebuild scope: per BIND §3's re-derived minimal-cascade ruling, D-4a's actual touched surfaces are
L3 `ka_*` serving (A-0) and application tables outside the L0-L5 asset DAG (LEL/ledger/ontology,
A-1 through A-4) — no L1/L2/L4/L5 cascade was required or performed. A-0's own migrations
(454/455) triggered the necessary `kala_activation`/`kala_avadhi` re-materialization as part of its
own migration apply, live-verified (49,705→332,239 rows).

## §6 — Findings requiring future disposition

- Carried D-2 #2 (nodal-exaltation offset surface asymmetry) — owner D-4b.
- Carried D-2 #4 (`judgment_query` oversize baseline) — owner D-4b.
- A-5's diagnostic dry-run surfaced a genuine primary-vs-secondary metric disagreement
  (pratyantar_lord underperforms shuffled-birth control on CRPS/skill in all 5 domains, but
  beats/matches it on legacy hit-rate in 4/5) — this is exactly the kind of signal D-4b's DR-12
  adjudication exists to resolve; NOT resolved or adjudicated here, per explicit lane framing.
- midpoint_triangle and transit_kernel models remain unimplemented (`NotImplementedModelError`) —
  open engineering gap for whoever builds D-5's engine construction or D-4b's full bakeoff.
- A pre-existing orphaned `build_runs` row (`372b5cfa…`, D-3-era crash artifact, state `running`)
  remains untouched in the DB — flagged by A-0, out of scope for any D-4a lane.

## §7 — Git hygiene note (pre-existing gap discovered and corrected this session)

At session open, `docs/D-3-spawn-cycle1` (containing the entire D-3 closeout: DR-13/DIS.026
registration, CR-109/110/111 defect recording, the native date-tightening questionnaire delivery,
`D4_BRIEF_REVISION_INPUTS.md`) had never been merged into `origin/main` — a gap predating this
session. This wave's close commit merges that branch's content into `main` alongside D-4a's own
close artifacts, so the full campaign history (D-3 closeout → D-4a) is now present in `main`'s
ancestry, not stranded on an unmerged feature branch. Separately, the main working-directory
checkout was found mid-session to be shared with an unrelated concurrent campaign ("PG-1",
branch `pg1/wave`) actively in progress — this wave's close artifacts were assembled in a fresh,
isolated worktree specifically to avoid entangling with that concurrent session's uncommitted work.

## §8 — Cleanup verification

All lane worktrees and branches (`wave/D-4a/A-0` through `A-5`, plus `A-0-fix`) removed after
merge. `origin/main` HEAD matches the deployed `amjis-web` SHA. No D-4a-related untracked strays
remain (the 3 D-3-era `dispatch_d3_*.py` scripts are pre-existing D-3 hygiene items, not D-4a's
responsibility, left for a future cleanup pass rather than deleted unilaterally).

## §9 — Next

`current_wave` → D-5 "Gochara-Chitra" (INCOMING). Per CLAUDECODE_BRIEF.md's native_directives,
D-5 opens on the native's own kickoff directive — this session does not open it.
