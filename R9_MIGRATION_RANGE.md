# R9 Migration Range

R9 reserves migration numbers **110–119** for its schema changes.

| File | Purpose |
|------|---------|
| 110_add_projects_abstraction.sql | projects, project_files, project_conversations tables |
| 111_add_conversation_message_embeddings.sql | vector embeddings table (R9-S2) |
| 112_add_personas.sql | personas table (R9-S3) |
| 113–119 | reserved for R9 follow-up sessions |

## Rationale

Main branch highest observed migration at R9 worktree creation: `060_panchanga_daily.sql`.
R8 has reserved a contiguous block above 60. R9 picks 110+ (≥50 above 60) to avoid
collision when the merge-train rebase lands R8 migrations first.

**Merge-trainer note:** If R8 migrations land at numbers that conflict with 110+, renumber
R9 migrations accordingly before completing the rebase. The `110_` prefix is a placeholder;
what matters is that R9's numbers are strictly greater than the highest R8 migration number
after rebase.

Authored: 2026-05-20 (R9 worktree setup)
