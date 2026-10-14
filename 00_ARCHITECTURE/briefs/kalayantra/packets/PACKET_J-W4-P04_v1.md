---
artifact: PACKET_J-W4-P04_v1
version: "1.0"
status: PREPARED_OFFLINE — source landing proposed; operational J-4a acceptance unearned
produced_on: 2026-10-15
changelog: "v1.0: carry PRs 2903/3116, preserve all port oracles, strengthen R4, record residual dispositions."
---

# P04 — settled-L1 intake and repin

One proposed landing for code children `J-4a-pr2903` and `J-4a-pr3116`. KEEP both heads: 5a46c9c97e61e86dde56c3608032431b9a9ff0e0 and 936f4fc5093cae31fe6aebdd0ae4b0e391d1a1d3. Exact case/fixture inventory: supplied `PORT_MANIFEST.json`; review: supplied `SURROGATE_ANSWER_17.md:13-23` (Q2/Q3). PR bodies were read; both have empty review/comment arrays. No review-thread decision omitted.

## Source scope and oracles

Owns:
- `platform/python-sidecar/scripts/gochara/repin_dasha_contract.py`
- `platform/python-sidecar/scripts/gochara/settled1_intake_check.py`
- `platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_tool.py`
- `platform/python-sidecar/tests/l3/gochara_rules/test_c50_settled1_intake.py`
- this packet brief (Q7 residual evidence path for all three residuals).

All 75 AM-10 and 11 C50 test declarations, their parametrizations and assertions are carried. The referenced chat fixture `platform/tests/fixtures/chat-v2/streaming-chunks/mixed.json` was already byte-identical at SHA-256 f6334c55e5c7074345bcc8973cbdcb2d8547f164d8397172b1cc006e7a8c0d5c; no duplicate/churn introduced. AM-10 implementation is byte-identical to its manifest head. One synthetic AM-10 replacement timestamp changed 09:13:56 → 09:13:57 because current permission.py already contains 09:13:56; all rewrite/keep assertions remain. This changes test data, not an L1 fact.

C50's inherited R4 compared only the set of fact IDs. It now compares subject→fact_id mappings and requires ten distinct nonempty IDs (`settled1_intake_check.py:169`; new parametrized oracle `test_c50_settled1_intake.py:137`). Swapping two subjects' IDs or collapsing both captures to one ID must STOP, even when the ID sets are unchanged. Two observed RED assertions before this change; GREEN after; reverting to the inherited detector kills both tests. No foundational values are recomputed.

AM-10 capture is read-only, snapshot-bound, rolled back and closed; `--apply` edits local source only after its existing mechanical guards, evidence and literal rulings. Local application is preparation; it grants no production release. The historical full-shape checks are retained; a real mismatch must STOP, not be weakened. No writer, orchestrator, authority flip, migration or L0–L2 asset changes.

## Settlement reconciliation and A5.5k

Issued settlement authority: commit `2051951aaa3f4e1b6a55d728f703bc074daf11ef`, `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md:9207`:

```
L1_SETTLED v1 utc=2026-10-07T22:18:24Z pos_build=ca17639b dash_build=ca17639b natal_fp=7e4278be vim13_fp=ee2e8bc7 vim13_rows=1040 dash_all_fp=ea7611f7
```

Full run identity: `ca17639b-f3cf-42c7-9866-0a61f3855802`. Same source:9209-9211 says ga_dashas rebuilt and legacy `75524b3e` is unreadable; it reports a timed-out digest comparison, not a successful retake. This is an issued notice, not our production readback. The settled record is also on `origin/kalayantra/j-4p:platform/python-sidecar/services/gochara_kernel/dasha_settlement.json:4-25`; its brief `PACKET_J-4p_v1.md:36-43` keeps historical reference labels separate from the runtime pin. `DASHA_TABLE_CONTRACT_v1_0.md:64,67` requires deliberate settlement pinning; unchanged row IDs alone prove neither build nor tier equality.

`J-4a-a55k`: upstream-release prerequisite recorded from issued `SUVARNA-L0L2-CLOSE-REV30-20261013`. Coordination at the same commit:9343-9350 records owner closure at 77/82 (strict 13/82), PR #3483 and uncertified assets; we do not relabel that as all-assets certification. Archived receipt: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/RELEASE_RECEIPT.final.json:2-23` binds certification and the full rebuild UUID. All five receipt conditions were inspected as SATISFIED. This records the external dependency's issued disposition; a code merge is not its detector.

Q5 readback NOT PERFORMED: this offline job cannot connect to production. Exactly one live settled candidate, legacy-row presence/absence and consumed-copy identity/status still require the cockpit's guarded receipt. Do not edit the stale J-4a detector merely to make a regex green. This landing does not modify J-4p's runtime pin or claim live repin acceptance.

## Historical residual dispositions (Q6)

`J-4a-a25` / A2.5: **superseded by the 5.0 settled baseline — explicit surrogate disposition, not done**.

`J-4a-a26` / A2.6: **superseded by the 5.0 settled baseline — explicit surrogate disposition, not done**.

The available archived sitting record `00_ARCHITECTURE/briefs/pravaha/run_records/2026-10-06/sitting-20261003/RESUME_NOTES.md:47` marks A2.5 parked; the plan at `worktree_modified/PRAVAHA_CAMPAIGN_PLAN_v1_0.md:146-147,183` declares obligations, not completion receipts. No attributable 4.1 build/evidence/baseline completion receipt was found in supplied repository archives and prefetched packet inputs. Neither repin code nor measuring evidence is substituted. B5.4's independent baseline dependency remains intact.

(I) INTERPRETATION I-P04-1: this is an offline source-preparation landing. Issued settlement/release artifacts support a recorded prerequisite, but never replace Q5 live single-build/consumed-copy readback; J-4a aggregate acceptance remains unearned.

(I) INTERPRETATION I-P04-2: receipt absence is scoped to the available supplied archives, not a claim that no receipt exists anywhere. Apply Q6's explicit superseded disposition; the cockpit may instead bind a subsequently located genuine historical artifact.

(I) INTERPRETATION I-P04-3: allocate this new brief as the residual evidence path under Q7. Register that exact path and typed disposition/detector in the cockpit-owned model; this job does not change tracker/model authority.

## Verification and review contract

All relevant non-DB tests: 479 passed, 4 DB tests deferred to CI, 8 inherited expected failures (named in PACKET_REPORT.md). New P04 tests: 116 passed and 2 DB cases deferred. Twelve semantic mutations were killed by assertion failures. Generator passed with all four aggregates current; no generated bytes changed. Temporary dependency and TMPDIR links removed. Long job TMPDIR hit the Unix socket path-length limit first; a short temporary link inside this worktree pointed to the same allowed job scratch, then was removed.

The independent packet verdict must enumerate both code child IDs at the exact reviewed SHA, with required CI/DB oracles green. Historical residual dispositions and issued A5.5k evidence are separate from that code verdict. The cockpit must attach Q5 readback and reconcile its legacy detector; no operation child or full J-4a join is certified here.
