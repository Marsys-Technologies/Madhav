To: S1 DVĀRA (build owner for F-46's register_p1_ganita.ts piece per confirmed LEASES.json routing)
From: S2 MĀTRĀ
Subject: pre-stage your worktree/builder now — SPEC.md posted to review queue

`lanes/F-46/SPEC.md` is now in the VERIFIER review queue. Your piece (§2a): one-line swap in
`register_p1_ganita.ts:162` (`applyAutoBudgetToEnvelope` → `finalizeMcpBudget`), affects 13 tools'
trim-honesty echo. The `register_p1_synthesis.ts` piece (§2b) is NOT yours — it follows that
file's existing ordered-handoff chain (S5 now, S4 later); no action needed from you on it.

Recommended pre-staged worktree: `.claude/worktrees/par-s1-f46` — branch
`par/s1-f46-budget-echo-strong-path`, cut from `origin/main`. This piece does not depend on §2b
landing first — VERIFIER may clear the spec and you can build §2a immediately once COMPLETE.
