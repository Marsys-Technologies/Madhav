---
artifact: MADHAV_L3_BRANCH_TRIAGE_DISPOSITION
version: "1.0"
status: RECORDED
prepared_on: 2026-09-20
prepared_by: "L3 Kāla autonomous conductor (Claude Code, Sonnet 5), Packet D7"
ground_truth_as_of: "2026-09-20 02:40 IST, git ls-remote --heads origin"
supersedes: none
related:
  - MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md (Appendix B — the classification scheme this
    record implements)
  - MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md §3
changelog:
  - "1.0: First disposition pass over the ~113 unmerged L3-related branches on origin, per
    Appendix B of the dual-campaign plan. Read-only classification; no branch deleted."
---

# L3 branch triage — disposition record (D7)

Read-only classification of every unmerged `codex/*` branch touching L3 territory, per the
classes in `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` Appendix B. **No branch is deleted by
this record** — a disposition record is the deliverable; deletion is a separate, later,
explicitly-authorized act (per the execution package §7 anti-stall rules and §3 Wave D
instructions).

## Class B-1 — preserved data-plane packets (8 branches, LOCAL-ONLY until Packet A1)

All 8 pushed to origin unchanged by Packet A1 (2026-09-20, verified 9/9 SHA match). Per-packet
disposition tracked by Wave D packets D1–D6 in `MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE_v1_0.md`
§3, dispatched separately as implementer subagents this session:

| Branch | SHA | Disposition |
|---|---|---|
| `codex/l3-kshetra-p0` | `50d7a917b` | → Packet D1 (Kshetra P0 safety), IN PROGRESS this session |
| `codex/l3-kshetra-p0-correction` | `9e350fe91` | → Packet D1, same lane |
| `codex/l3-kshetra-w0-preservation` | `018dc89e4` | → Packet D1, same lane |
| `codex/l3-dhara-correction` | `b6dccff06` | → Packet D3 (folded into D1's lane — same files) |
| `codex/l3-bhavishya-p0` | `d801b8aa7` | → Packet D2 (Bhavishya P0), IN PROGRESS this session |
| `codex/data-plane-l3-yojaka` | `7697c43b3` | → Packet D4 (Yojaka preservation), IN PROGRESS this session |
| `codex/l3-w0-field-contract` | `c728f1327` | → Packet D5 (W0 field register), IN PROGRESS this session |
| `codex/l3-u05-registry` | `01a64ca53` | → Packet D6 (U05 registry), IN PROGRESS this session |

## Class B-2 — strategy branch (LOCAL-ONLY until Packet A1)

| Branch | SHA | Disposition |
|---|---|---|
| `codex/madhav-data-plane-strategy` | `2438b579f` | Pushed unchanged by Packet A1. **Extract-never-merge** — carries 25 commits / 627 stale runtime-source files. The four governing documents it carries were extracted onto `main` via Packet B1 (PR #2692). This branch itself stays open and untouched as a preservation copy; do not merge it, do not delete it. |

## Class B-3 — delivery-repair leftovers (4 branches)

| Branch | SHA | Disposition |
|---|---|---|
| `codex/madhav-data-plane-l3-closure` | `8a7bbeca0` | Superseded by merged #2656/#2670/#2673/#2684 (delivery gate now closed by Codex). PR #2655 (this branch) is **already CLOSED** — verified via `gh pr view 2655`, no action needed. Retire (leave branch as historical, do not delete tonight). |
| `codex/madhav-data-plane-l3-isolation-admin-env-fix` | `906d30fdd` | Superseded by the same delivery-gate closure chain. Retire. |
| `codex/madhav-data-plane-l3-isolation-region-fix` | `5ea884232` | Superseded, same reason. Retire. |
| `codex/madhav-data-plane-l3-pgcrypto-successor` | `238226ea6` | Superseded by #2656 (pgcrypto provision landed in the protected cutover). Retire. |

## Class B-4 — old-fleet heartbeat noise (36 branches, `codex/nirmana-l3-heartbeat-idle-*`)

Verified count: **36** (dual-campaign plan estimated 37; live count is 36 — the plan's own
figure was an estimate, not a discrepancy requiring investigation). All are heartbeat/state
branches from the pre-2026-09-15 old fleet with no data-plane content. **Bulk disposition: retire
in one record, no per-branch review.** None inspected individually; if a future packet needs one
by exact SHA, re-open it then.

## Class B-5 — old-fleet finding fixes, pre-2026-09-15 (63 branches, `codex/nirmana-l3-{f,n1,n3,n4,n5,n6,w1..w5,state}-*`)

Verified count: **63** (dual-campaign plan estimated ~66; close enough — both are estimates over
a moving branch set, not a material discrepancy). Sampled 8 branches' last-commit timestamps:
all fall 2026-09-06 10:05–22:35 IST, confirming they predate the 2026-09-15 strategy cutover that
this campaign's governing plan is built on. **Bulk disposition:
`SUPERSEDED_BY_STRATEGY_2026-09-15`, one record, no per-branch review.** Re-open individually only
if a future Phase-2/W2+ packet cites one by exact SHA (per the dual-campaign plan's own
instruction).

## Summary

| Class | Count | Action taken this session |
|---|---|---|
| B-1 preserved packets | 8 | Dispatched to Wave D implementer packets D1–D6 |
| B-2 strategy branch | 1 | Docs extracted (Packet B1); branch left untouched |
| B-3 delivery-repair leftovers | 4 | Confirmed superseded; PR #2655 confirmed already closed; no deletion |
| B-4 heartbeat-idle | 36 | Bulk-classified, no deletion |
| B-5 old-fleet finding fixes | 63 | Bulk-classified, no deletion |
| **Total classified** | **112** | plus the 9 A1-preserved branches (counted separately, now on origin) |

No branch was deleted, force-pushed, or reset by this record. Deletion of classes B-3/B-4/B-5 is
a separate act requiring explicit native authorization (per the execution package's forbidden
list §7.1: "Force-push, delete a branch... you did not create tonight").
