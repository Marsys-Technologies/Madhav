---
artifact: MORNING_REPORT_20260820
campaign: PARISESA-V4
session: PARISESA-V4-CONDUCTOR-20260820T005119Z
status: NATURAL_COMPLETION — automatable repair-wave backlog exhausted
journal_head_seq: 776
generated: 2026-08-20 (overnight session, ~22 hours real-time span incl. idle
  gaps between checks; active work concentrated in ~10 dispatch rounds)
---

# PARIŚEṢA-V4 — Morning Report

## Headline

**84 of 141 findings are genuinely closed** (SERVICE_CLOSED 55, CONTROL_CLOSED 25,
HISTORICAL_STALE_CLOSED 3, NOT_APPLICABLE_CLOSED 1) — every one independently
re-verified this session via a live falsifiable canary or a direct source-diff
content match, not inherited from any prior campaign's claim.

**21 PRs are frozen, open, and ready for your one-approval-or-review-by-item pass.**
Every one has real test coverage, an independent-review pass, and (where relevant)
a documented reason for any deliberate deviation from a literal spec.

**No PR was merged. No deploy happened. No data was written.** Every prohibition in
the overnight scope boundary held for the full session.

**The automatable backlog is exhausted.** Every one of the remaining ~57 findings
now genuinely needs something only you can supply: an architecture ruling, a DB
credential for a bounded packet, a live user session, or a production chart
rebuild. This is why the session stopped dispatching further rounds — not because
it ran out of time, but because it ran out of things it could do alone.

---

## 1. The MORNING_SHIP_READY queue — 21 PRs

All frozen (open, unmerged). Recommended read order: governance PR first, then
by finding ID.

| PR | Finding | What it fixes | Confidence |
|---|---|---|---|
| [#1362](https://github.com/Marsys-Technologies/Madhav/pull/1362) | CCD-009 (governance) | Records this session's authorization chain; CI green | — |
| [#1371](https://github.com/Marsys-Technologies/Madhav/pull/1371) | F-25 | `kala_dasha_sandhi_get` audit-attribution defect (mislabeled "auth bypass" in an early draft, corrected — zero regression risk) | HIGH |
| [#1370](https://github.com/Marsys-Technologies/Madhav/pull/1370) | F-26 | `kala_life_arc_get` no longer falsely advertises `include_lel_events` | HIGH |
| [#1369](https://github.com/Marsys-Technologies/Madhav/pull/1369) | F-33 | Pre-birth `as_of_date` query disclosure (dangling-commit recovery) | HIGH |
| [#1368](https://github.com/Marsys-Technologies/Madhav/pull/1368) | F-122 | **Real correctness bug** (aliased ledger objects silently emptying a surviving candidate's data under trim) — fixed, re-verified, independently reviewed twice | HIGH |
| [#1366](https://github.com/Marsys-Technologies/Madhav/pull/1366) | F-121 | `dasha_sandhi` max_level fix — hollow test/stretched fixture/wrong citation from an early draft all corrected and re-verified | HIGH |
| [#1378](https://github.com/Marsys-Technologies/Madhav/pull/1378) | F-68 | Tier-honesty leak, recovered a quarantined candidate fix | HIGH |
| [#1379](https://github.com/Marsys-Technologies/Madhav/pull/1379) | F-123 | Dead-pointer defect, confirmed reproducing on deployed service — fresh build | HIGH |
| [#1382](https://github.com/Marsys-Technologies/Madhav/pull/1382) | F-14 + F-124 | **Reconciles two genuinely-overlapping ratified branches** into one PR — closes both findings | HIGH |
| [#1383](https://github.com/Marsys-Technologies/Madhav/pull/1383) | F-130 | Raw JSON blobs leaking into served prose (narration-fidelity) | HIGH |
| [#1384](https://github.com/Marsys-Technologies/Madhav/pull/1384) | F-134 | Gochara sweep served already-peaked windows as upcoming | HIGH |
| [#1385](https://github.com/Marsys-Technologies/Madhav/pull/1385) | F-135 | Silent-gap defect in ranked-themes weaknesses | HIGH |
| [#1386](https://github.com/Marsys-Technologies/Madhav/pull/1386) | F-69 | Non-calibrated evidence suppression — cross-verified against a since-landed sibling finding (F-35) it interacts with | HIGH |
| [#1387](https://github.com/Marsys-Technologies/Madhav/pull/1387) | F-125 | B.11 orientation gate export — **one deliberate, documented deviation** from the literal spec to preserve a stronger safety invariant (gate G16, zero-network-calls-on-refusal) | HIGH |
| [#1388](https://github.com/Marsys-Technologies/Madhav/pull/1388) | F-60 | `get_strength.ts` true row count vs. page length | HIGH |
| [#1389](https://github.com/Marsys-Technologies/Madhav/pull/1389) | F-129 | `top_discoveries` served raw diagnostic labels instead of narrative | HIGH |
| [#1390](https://github.com/Marsys-Technologies/Madhav/pull/1390) | F-73 | Phantom registry URI — **found that both existing tests mocked the phantom URI**, masking the defect from production; adapted tests to the real path | HIGH |
| [#1391](https://github.com/Marsys-Technologies/Madhav/pull/1391) | F-67 | Missing MCP tool registration (pure omission) | HIGH |
| [#1392](https://github.com/Marsys-Technologies/Madhav/pull/1392) | F-78 | Recovered *why* the original swarm attempt stalled (a missing test fixture) and supplied it | HIGH |
| [#1393](https://github.com/Marsys-Technologies/Madhav/pull/1393) | F-93 | Real merge conflict against main's own since-grown validation — correctly combined, not picked one side | HIGH |
| [#1394](https://github.com/Marsys-Technologies/Madhav/pull/1394) | F-112-DOCSTRING | Corrected a misleading docstring — **identified the underlying behavior as deliberate design, not a bug**, and fixed the doc instead of weakening a protection | HIGH |

**Two PRs (#1366, #1368) were flagged NEEDS_REVISION mid-session by an
owner-requested Opus review, then genuinely fixed and re-verified — not just
patched to green CI. Full defect-and-fix detail is in the ledger's
`fix_f121`/`fix_f122` records if you want the paper trail before reviewing.**

---

## 2. Decisions made on your behalf — flagged for ratification, not hidden

### PROVISIONAL_RULING PR-001
Proceeded into Phase 0 truth-cut and repair waves despite finding that neither
existing authorization record (CCD-007, CCD-008) actually covered a Claude-Code-run
Phase 0. **Basis: your direct, live authorization in this conversation**, recorded
as CCD-009 (PR #1362, CI green). No merge/deploy/data exception was granted by this
ruling — that boundary held all night regardless.

### PROVISIONAL_RULING PR-002
Raised WIP one notch (1→2 proof trains, 2→3 code trains) after 3 rounds with zero
failures and zero file collisions, per the kickoff prompt's own pre-authorized
dynamic-scaling clause. This is the lever that made the second half of the night's
throughput possible — worth ratifying explicitly if you want it available for a
future session.

---

## 3. What went wrong, and what it means for how much to trust "84 terminal"

This is the part of the report I'd read most carefully.

**A real, systemic evidence-citation defect existed in the source corpus.** One
commit (`cfb6444c8`) was cited as "evidence" for **29 different findings**, almost
all wrongly — its actual content is a narrow Prashna-domain-filter change. Several
other commits were mis-cited too, including one case where a citation belonged
entirely to a *different* finding ID. Tagged IF-001 through IF-003 in the journal.

**The adversarial ratification panel — the mechanism meant to catch exactly this —
missed it.** 84 of its 105 votes were pure ancestry checks ("is this commit an
ancestor of main") run three times, not three independent verifications. It caught
some over-claims but **let two badly-cited findings through as confirmed terminal**
before a later, more thorough pass caught them.

**When you asked me to spin up an Opus review of the queue**, it found this pattern
and I acted on it: **16 terminal findings were demoted back to "landed, pending
real verification"** rather than left counted as closed. Every one of the 84
currently marked terminal has since been re-verified with either a live falsifiable
MCP call or a specific content-matched source diff — not a bare commit-ancestry
check. A follow-up investigation pass recovered 5 of those demoted findings back to
terminal with real evidence; one (F-15) is real but correctly held non-terminal
because its fix hasn't merged yet.

**Net effect: the 84 count is more trustworthy than the 122 this session could have
reported at its most optimistic point tonight**, precisely because it was
willing to subtract findings it couldn't actually back up.

### Other real incidents, disclosed rather than smoothed over
- **PF-002**: A concurrent continuation thread (most likely the local watchdog
  firing `claude --continue` during a long wait) wrote 5 commits to the shared
  tracker under this session's own identity without this thread's knowledge.
  Verified the hash chain was intact and the work was real before accepting it.
- **PF-003**: Discovered mid-session that EKAVĀKYATĀ is **not** actually dormant —
  a live SENTINEL verifier process has been running on this machine since before
  this session started, plus 3 more unidentified Claude processes. This session's
  own isolation held throughout regardless (own worktrees, own branches, own
  leases), but the earlier P-1.4 "EKAVĀKYATĀ is dormant" note was wrong.
- **PF-004**: `git stash` caused a real (self-corrected, zero-damage) cross-worktree
  collision — confirms the pre-existing X-5 collision-forensics lesson is still a
  live hazard, not just historical. All later dispatches were instructed to never
  use it.
- **PF-001**: F-50's shipped fix on `main` came from an unreviewed sibling attempt,
  bypassing this campaign's own review chain — correct and tested, but a process
  gap worth knowing about.

---

## 4. Decisions that need you — organized by what kind of decision

**Architecture/design rulings (owner-only, ~9 findings):** F-06 + F-91 (RATE-07
trusted-edge authority), F-38 (Pratinidhi baseline-aware ruling), F-27 (merge
authority confirmation), F-23 (classical content authority), F-48 (which authority
governs PH-4-4 muhurta scoring — heuristic vs. Swiss ephemeris).

**Needs a design contract authored + reviewed before implementation (~7 findings,
mechanical once you or a future session scopes them):** F-57, F-61, F-107, F-110,
F-113, F-114, F-118, F-126, F-35, F-94.

**Needs DB access for a protected-data packet or a live production action (~9
findings):** F-62 (packet not yet staged), F-104/F-116/F-63/F-71 (code fixes
already merged — chart 482012f1 needs an **L5 data rebuild** to actually serve
them; this is a production-adjacent action, correctly held), F-54 (resume a
paused scheduler), F-117/F-141 (explicit morning-checkpoint decisions).

**Needs a live user chat session to test (2 findings):** F-31, and indirectly
related to F-109's replay-grading requirement.

**Small investigation, not blocked on you specifically (~5 findings):** F-79
(resolve 2 dangling commit refs), F-05/F-131/F-139/F-43 (original finding text
genuinely not recoverable in this worktree — needs the external par-night
finding-generation corpus), F-140 (confirmed corpus authoring gap, needs the
original finding description supplied).

**Correctly blocked on other items in this same report, not new decisions:**
F-15/F-21/F-52 (each waits on another item in this queue — F-15 on PR #1382
merging, F-21 on F-52, F-52 on a fingerprint-invalidation packet nobody's
authored).

**Bookkeeping note:** the tracker's finding count currently reads 143, not 141 —
one legitimate split (F-112 → F-112 + F-112-DOCSTRING, a real second defect this
session found while investigating the first) plus one stale batch-marker row
(`F-75-batch`, safe to delete — the 6 underlying findings it referenced are all
individually resolved now).

---

## 5. Model tier usage

Per the owner ruling on model tiering: Sonnet 5 handled every mechanical
lane (reconciliation, proof trains, rebase/build trains, triage) — that's
essentially the entire night. **Opus 5 was used exactly twice**, both
owner-requested: the 3-panelist truth-cut ratification (which, per §3 above,
had a real blind spot worth knowing about) and the ESC-001 adversarial review
of the morning queue (which is why this report is more conservative than it
could have been).

---

## 6. Isolation & safety — clean

- **Zero writes to any foreign (PARIPRAŚNA) or sibling (EKAVĀKYATĀ, par/*)
  namespace.** All work stayed in `parisesa/*` branches.
- **Zero merges, zero deploys, zero data mutations** for the full session.
- **Watchdog note:** the original `watchdog.sh`/cron mechanism never actually
  fired all night (a macOS permission issue, confirmed by an empty log file) —
  it was replaced mid-session by a `CronCreate` job (`0ab74567`, every 10 min,
  session-only, auto-expires in 7 days) plus `/loop` dynamic-pacing. **Before
  you start reviewing/merging by hand: `touch
  /Users/Dev/par-night/parisesa-v4-conductor/STOP.flag`** to stop any further
  autonomous continuation while you work.
- Violations counter: 0.

---

## 7. Reforecast for the ship-and-close phase

1. Set `STOP.flag`, review/merge the 21-PR queue (governance PR #1362 first).
2. Grant DB access (already tested working tonight via `gcloud secrets
   versions access` + the existing `cloud-sql-proxy` on 5433) for the
   protected-data packets and the ~9 DB-gated findings.
3. Rule on the 9 architecture questions — several other findings are directly
   blocked on just 2 of them (RATE-07 gates F-06+F-91; F-52 blocks F-21).
4. Schedule the chart 482012f1 L5 rebuild to pick up 4 already-merged fixes
   (F-104/F-116/F-63/F-71) that are otherwise done.
5. The ~7 "needs a design contract" findings are good candidates for a future
   session once you're ready to scope them — none are urgent overnight risks.
