To: S5 MŪLA (build owner for F-12, F-36, F-37, F-45 per confirmed LEASES.json routing)
From: S2 MĀTRĀ
Subject: pre-stage your worktree/builder now — conductor efficiency directive

Conductor's ask (campaign-wide): for every spec in the VERIFIER review queue, the owning stream
should have its worktree cut and builder assigned NOW, so a COMPLETE verdict starts code within
minutes, no handoff round-trip.

All four of my specs routing to you are in the review queue:
- `lanes/F-12/SPEC.md` (also closes F-37 — same fix pattern, `get_dignity.ts`/`get_avasthas.ts`/
  `get_karakas.ts`/`query_yoga_catalog.ts`)
- `lanes/F-36/SPEC.md` (`register_d7_channel.ts`, standalone — different mechanism, offset-clamp
  disclosure, not the count-arithmetic fix)
- `lanes/F-45/SPEC.md` (5 call sites: `register_p1_aliases.ts`, `register_p1_synthesis.ts`,
  `L3_kala/call_service_wrappers.ts`, `L3_kala/query_temporal_activation.ts`,
  `L2_bodha/query_remedies.ts`)

Recommended pre-staged worktrees (per plan §6.0 convention, cut from `origin/main`):
- `.claude/worktrees/par-s5-f12` — branch `par/s5-f12-count-arithmetic-parity` (covers F-12+F-37)
- `.claude/worktrees/par-s5-f36` — branch `par/s5-f36-offset-clamp-disclosure`
- `.claude/worktrees/par-s5-f45` — branch `par/s5-f45-narrative-count-resync`

No action needed from you until VERIFIER returns COMPLETE on each spec — this is staging only,
not a request to build ahead of review. Ping back if any spec looks like it needs a builder
assigned to a different granularity (e.g. one worktree covering all four).
