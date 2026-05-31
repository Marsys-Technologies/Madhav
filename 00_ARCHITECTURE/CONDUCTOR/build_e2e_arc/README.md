# build_e2e_arc — operator quick reference

This arc autonomously ships the four code streams needed for a guest to
click "New Client" in the MARSYS portal, fill the form, click "Build",
and watch their chart compute live in the cockpit — with the resulting
data queryable via `/consume`.

Target end-state: every commit to main auto-deploys + auto-migrates +
auto-IaC-applies + auto-smokes. The only manual operator action after
this arc lands is clicking Build for your own chart.

## What to paste, where

| # | What | Where |
|---|---|---|
| 1 | `CONDUCTOR_PROMPT_v1_0.md` | Fresh Antigravity Claude Code window opened anywhere in the repo |
| 2 | `kickoffs/KICKOFF_STREAM_A.md` | Antigravity window opened in `/Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI` |
| 3 | `kickoffs/KICKOFF_STREAM_B.md` | Antigravity window opened in `/Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing` |
| 4 | `kickoffs/KICKOFF_STREAM_C.md` | Antigravity window opened in `/Users/Dev/Vibe-Coding/Apps/MadhavVisualV2` |
| 5 | `kickoffs/KICKOFF_STREAM_D.md` | Antigravity window opened in `/Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish` |

The Conductor (paste #1) does §1 pre-flight smoke, then §2 worktree
creation, then §3-§4 prints the 4 kickoffs to its own console, then stops.
You copy each printed block into its corresponding window.

## Architecture in one diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Operator pastes Conductor prompt (window 0)                    │
│      │                                                          │
│      ├─ §1 pre-flight smoke against prod                        │
│      ├─ §2 setup_streams.sh creates 4 worktrees                 │
│      ├─ §3 seeds CLAIM_LEDGER                                   │
│      └─ §4 prints 4 kickoffs                                    │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼ operator pastes 4 kickoffs into 4 windows
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Window 1 (A) │ │ Window 2 (B) │ │ Window 3 (C) │ │ Window 4 (D) │
│ Hardening+CI │ │ Data plumb.  │ │ Visual v2    │ │ Funnel       │
│ 9 sessions   │ │ 7 sessions   │ │ 9 sessions   │ │ 6 sessions   │
│              │ │              │ │              │ │              │
│ Walk queue → │ │ Walk queue → │ │ Walk queue → │ │ Walk queue → │
│ claim+exec → │ │ claim+exec → │ │ claim+exec → │ │ claim+exec → │
│ cherry-pick  │ │ cherry-pick  │ │ cherry-pick  │ │ cherry-pick  │
│  to main →   │ │  to main →   │ │  to main →   │ │  to main →   │
│ auto-deploy  │ │ auto-deploy  │ │ auto-deploy  │ │ auto-deploy  │
│ via .yml     │ │ via .yml     │ │ via .yml     │ │ via .yml     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │                │                │                │
        └────────────────┴────────────────┴────────────────┘
                                   │
                                   ▼
            CLAIM_LEDGER.yaml (race-resolved via git push)
                                   │
                                   ▼
                        main branch (auto-deploys)
                                   │
                                   ▼
      Operator opens cockpit and clicks Build (only manual step)
                                   │
                                   ▼
                    Native chart computes live
```

## File inventory

```
00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/
├── README.md                        ← you are here
├── CONDUCTOR_PROMPT_v1_0.md         ← paste #1
├── STREAM_COORDINATION_v1_0.md      ← stream agents read this every session
├── session_queue.yaml                ← 28 sessions across A/B/C/D
├── CLAIM_LEDGER.yaml                 ← atomic work-stealing
├── VISUAL_CONTRACT_v2.md             ← native-approved visual spec (Stream C reads)
├── setup_streams.sh                  ← worktree creation
├── briefs/
│   ├── STREAM_A_HARDENING_CI_v1_0.md
│   ├── STREAM_B_DATA_PLUMBING_v1_0.md
│   ├── STREAM_C_VISUAL_V2_v1_0.md
│   └── STREAM_D_FUNNEL_POLISH_v1_0.md
└── kickoffs/
    ├── KICKOFF_STREAM_A.md           ← paste #2
    ├── KICKOFF_STREAM_B.md           ← paste #3
    ├── KICKOFF_STREAM_C.md           ← paste #4
    └── KICKOFF_STREAM_D.md           ← paste #5
```

## What's automated vs. what's manual

| Step | Automated by | Manual? |
|---|---|---|
| Code authoring | Stream agents | No |
| Commits + cherry-picks to main | Stream agents | No |
| CI auto-fix (5 attempts) | Stream agents | No |
| Production deploy on main push | GitHub Actions (after A-S8 lands) | No |
| Production DB migrations | GitHub Actions (migrate.ts) | No |
| Cloud Run IaC apply | GitHub Actions (terraform apply) | No |
| Post-deploy smoke + traffic flip | GitHub Actions | No |
| Native chart build trigger | YOU click Build in cockpit | YES |
| Reviewing PRs | YOU optionally watch as they merge | YES (optional) |

## When something goes wrong

- Stream halt → check CLAIM_LEDGER.yaml `halted[]` for reason
- CI red ignored → check CLAIM_LEDGER.yaml `ci_red_ignored[]`
- Auto-deploy failure → GitHub Actions logs + Cloud Run revision pinned to prior
- Conductor failed pre-flight → fix the blocker, re-paste the Conductor prompt; it's idempotent

## Estimated wall-clock

- Conductor + pre-flight: ~20 min
- 4 streams in parallel: ~90-150 min (longest stream sets pace)
- Auto-deploy chain runs continuously as streams cherry-pick
- Total: ~3 hours from paste-1 to "click Build and watch it work"
