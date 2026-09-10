---
version: "1.0"
status: CURRENT
produced_by: parishkara/mr-30
produced_on: 2026-08-10
---

# MR-30 Worktree Cleanup Report

PARIṢKĀRA MR-30 secondary task: salvage-check and remove stale GOCHARA-UTKARṢA
builder worktrees.

## Pre-cleanup inventory (25 utk-w* worktrees)

| Worktree | Branch | Tip SHA | Clean? | Content status |
|---|---|---|---|---|
| utk-w21 | gochara3/w21 | d582c909e | clean | W2.1 — merged to sampurti/integration (#1159) |
| utk-w22 | gochara3/w22 | aee3d1103 | clean | W2.2 — merged to sampurti/integration (#1162) |
| utk-w23 | gochara3/w23 | 0eed04990 | clean | W2.3 — merged to sampurti/integration (#1160) |
| utk-w24 | gochara3/w24 | 8c9358839 | clean | W2.4 — DIRECTLY in main (non-squash merge, #1163) |
| utk-w25 | gochara3/w25 | 774224b82 | clean | W2.5 — merged to sampurti/integration (#1161) |
| utk-w26 | gochara3/w26 | 7ab916760 | clean | W2.6 — merged to sampurti/integration (#1164) |
| utk-w27 | gochara3/w27 | ca7862e99 | clean | W2.7 — merged to sampurti/integration (#1165) |
| utk-w28 | gochara3/w28 | 28ef1042c | clean | W2.8 — merged to sampurti/integration (#1166) |
| utk-w29 | gochara3/w29 | ef0fd6374 | clean | W2.9 — merged to sampurti/integration (#1167) |
| utk-w31 | gochara3/w31 | 0c28856ae | clean | W3.1 — merged to sampurti/integration (#1168) |
| utk-w32 | gochara3/w32 | 393adb6a1 | clean | W3.2 — merged to sampurti/integration (#1169) |
| utk-w33 | gochara3/w33 | f8e162040 | clean | W3.3 — merged to sampurti/integration (#1170) |
| utk-w34 | gochara3/w34 | afe249905 | clean | W3.4 — merged to sampurti/integration (#1171) |
| utk-w41 | gochara3/w41 | e28d19d3e | clean | W4.1 — merged to sampurti/integration (#1174) |
| utk-w42 | gochara3/w42 | 638958fa7 | clean | W4.2 — merged to sampurti/integration (#1173) |
| utk-w43 | gochara3/w43 | 32ee0ecef | clean | W4.3 — merged to sampurti/integration (#1176) |
| utk-w44 | gochara3/w44 | 1bbd2824d | clean | W4.4 — merged to sampurti/integration (#1178) |
| utk-w45 | gochara3/w45 | 32a617e18 | clean | W4.5 — merged to sampurti/integration (#1179) |
| utk-w46 | gochara3/w46 | 281756cea | clean | W4.6 — merged to sampurti/integration (#1177) |
| utk-w51 | gochara3/w51 | d4d39d28c | clean | W5.1 — merged to sampurti/integration (#1184) |
| utk-w52 | gochara3/w52 | 5e63e45cc | clean | W5.2 — merged to sampurti/integration (#1181) |
| utk-w53 | gochara3/w53 | 6471a6cc4 | clean | W5.3 — merged to sampurti/integration (#1182) |
| utk-w54 | gochara3/w54 | c50a90dbe | clean | W5.4 — merged to sampurti/integration (#1183) |
| utk-w61 | gochara3/w61 | 43458c812 | **DIRTY** | W6.1 — 3 uncommitted files (see below) |
| utk-w64 | gochara3/w64 | a7d9a9b69 | clean | W6.4 — merged to sampurti/integration (#1192) |

## utk-w61 dirty state (UNSALVAGED — not removed)

`git status --short` at time of MR-30 audit:
```
?? platform/scripts/dispatch_utkarsha_w63_authority_flip_abhinandan.py
?? platform/scripts/dispatch_utkarsha_w63_rollback_abhinandan.py
?? platform/scripts/probe_utkarsha_w63_e2e_abhinandan.py
```

These are the W6.3 operational scripts (Abhinandan-specific one-offs) that were
the source material for MR-30's generalized tooling. They were never committed
to git in utk-w61. MR-30 commits generalized versions of these scripts to
`platform/scripts/gochara/` (flip_authority.py, rollback_authority.py,
probe_gochara.py), which satisfies MR-08's closure gate.

utk-w61 itself is **not removed** because it has uncommitted changes (the three
untracked files). The worktree is retained at `/Users/Dev/Vibe-Coding/Apps/utk-w61`
pending a decision on whether the chart-specific scripts should be preserved or
discarded. The source material is fully captured by this report; the generalized
versions are in git.

## Actions taken

- **REMOVED (24 worktrees):** utk-w21 through utk-w29, utk-w31 through utk-w34,
  utk-w41 through utk-w46, utk-w51 through utk-w54, utk-w64.
  Method: `git worktree remove <path>` followed by `git branch -D gochara3/w<N>`.
  utk-w24's branch was deleted with `git branch -d` (confirmed in main, so -d
  sufficed). All others required `-D` because squash merges into sampurti/
  integration mean the branch tip is not a direct ancestor of local main (the
  merge commits in integration carry the content but not the exact SHA).

- **RETAINED (1 worktree):** utk-w61 at `/Users/Dev/Vibe-Coding/Apps/utk-w61` —
  UNSALVAGED, has uncommitted changes (3 untracked files listed above).

## Post-cleanup worktree list (utk-w* entries)

After cleanup, `git worktree list` shows no utk-w* entries except utk-w61:
```
/Users/Dev/Vibe-Coding/Apps/utk-w61   43458c812 [gochara3/w61]
```

## v2_materialize filename note

No scripts with `v2_materialize` in the filename exist in
`platform/scripts/`. The only file bearing that string is
`platform/python-sidecar/scripts/run_ka_gochara_v2_materialize.py` (the
direct-invocation runner for the GOCHARA-2.0 writer). Its docstring was
updated in this MR-30 commit to reflect the W6.4 UTK-R2 rename.
