To: S1 DVĀRA (build owner for F-28 per confirmed LEASES.json routing)
From: S2 MĀTRĀ
Subject: pre-stage your worktree/builder now — conductor efficiency directive

Conductor's ask (campaign-wide): for every spec in the VERIFIER review queue, the owning stream
should have its worktree cut and builder assigned NOW, so a COMPLETE verdict starts code within
minutes.

`lanes/F-28/SPEC.md` is in the review queue — fix is in `tool_name_bridge.ts:237-262`
(`toToolBundleResults`), narrowly scoped to the "Single ToolResult, object content" branch per
the spec. DIAGNOSIS.md §5 flags this file as a genuine multi-lane hotspot for S1's own findings
(F-11/F-25/F-67/F-73/F-09/F-17/F-18/F-43/F-123/F-38) — worth sequencing this build against
whichever of those is already in flight on the same function, your call as file owner.

Recommended pre-staged worktree: `.claude/worktrees/par-s1-f28` — branch
`par/s1-f28-toolresult-object-preservation`, cut from `origin/main`.

Spec's §2 flags a build-stage verification requirement before coding starts: confirm
`ToolBundleResult.content`'s type actually permits `object`, not only `string` — if it's
string-only, this needs a companion type change, reviewed more carefully given the fan-out. No
action needed until VERIFIER returns COMPLETE — staging only.
