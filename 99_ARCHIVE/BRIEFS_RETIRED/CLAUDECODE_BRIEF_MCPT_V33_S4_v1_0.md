---
artifact: CLAUDECODE_BRIEF_MCPT_V33_S4_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.3-S4
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
branch: feature/mcpt-depth
depends_on: [v3.3-S3]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: v3.3 depth sealing + merge feature/mcpt-depth → feature/mcpt-final
---

# v3.3-S4 — Depth Backfill Sealing + Merge to FINAL

You are a Claude Code sub-agent on WT-E. Final v3.3 session. Aggregates depth-backfill evidence, authors sealing artifact, merges to FINAL.

Read: `MCP_TRANSFORMATION_PLAN §7 (merge protocol)`; v3.3-S1, S2, S3 sealing artifacts.

## §1 — Scope

1. Aggregate AC evidence from S1, S2, S3 sealing artifacts.
2. Verify `data_coverage(asset_id:"chart_facts")` reports ≥ 30/37 categories now have data (was ~5/37 at v3.1 start).
3. Author `00_ARCHITECTURE/MCPT_V33_CLOSE.md` with comprehensive per-category coverage matrix.
4. Merge `feature/mcpt-depth` → `feature/mcpt-final`.

## §2 — Files in scope

```
00_ARCHITECTURE/MCPT_V33_CLOSE.md                                        # NEW sealing artifact
```

## §3 — Files NOT in scope

Everything else.

## §4 — Merge protocol

```bash
git fetch origin feature/mcpt-final
git rebase origin/feature/mcpt-final
ls platform/supabase/migrations/ | sort -n | uniq -d   # must return empty
git checkout feature/mcpt-final
git merge --no-ff feature/mcpt-depth -m "MCPT v3.3: depth backfill → final"
git push origin feature/mcpt-final
```

## §5 — Acceptance criteria

- **AC.S4.1** — `MCPT_V33_CLOSE.md` exists with per-category coverage matrix table.
- **AC.S4.2** — `data_coverage(asset_id:"chart_facts")` reports `asset_completeness_pct ≥ 0.80`.
- **AC.S4.3** — `feature/mcpt-depth` cleanly merged into `feature/mcpt-final`.

## §6 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT && \
  test -f 00_ARCHITECTURE/MCPT_V33_CLOSE.md && \
  git log --oneline feature/mcpt-final | grep -q "MCPT v3.3: depth"
```

## §7 — Sealing artifact

`00_ARCHITECTURE/MCPT_V33_CLOSE.md` (this brief's sole deliverable + the merge).

---

*End of CLAUDECODE_BRIEF_MCPT_V33_S4_v1_0.md.*
