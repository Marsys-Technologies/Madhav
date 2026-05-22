---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S6_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.1.0-S6
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
depends_on: [v3.1.0-S2, v3.1.0-S3, v3.1.0-S4, v3.1.0-S5]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Foundation sealing + merge to feature/mcpt-final + flag flip + governance updates
requires_human_approval: false
---

# v3.1.0-S6 — Foundation Sealing + Merge to FINAL

You are a Claude Code sub-agent on WT-A. Closes v3.1.0 (foundation). Tier-conditioned `house-rules` content is finalized; feature flag flipped; canonical artifacts registered; mirror surfaces updated; `feature/mcpt-foundation` merged into `feature/mcpt-final`.

Read: parent brief §4 / v3.1.0-S6; `MCP_ARCH_v3_PROPOSAL §13`; `CLAUDE.md §E` (concurrent workstream pattern); `00_ARCHITECTURE/MCP_TRANSFORMATION_PLAN_v1_0.md §7` (merge protocol).

## §1 — Scope

1. Finalize tier-conditioned `house-rules` content (S3 authored initial; S6 finalizes per S4 audit findings + per integration testing).
2. Flip `MARSYS_FLAG_MCP_V3_ENABLED` default to `true`.
3. Update canonical artifacts: `CANONICAL_ARTIFACTS_v1_0.md §1`, `CAPABILITY_MANIFEST.json`, `CLAUDE.md §E`.
4. Author sealing artifact `MCPT_V310_CLOSE.md`.
5. Update mirror surfaces `.geminirules` + `.gemini/project_state.md` (MP.1 / MP.2 adapted parity).
6. Merge `feature/mcpt-foundation` → `feature/mcpt-final` per `MCP_TRANSFORMATION_PLAN §7`.
7. Append SESSION_LOG.
8. Update CURRENT_STATE state pointer.

## §2 — Files in scope

```
platform-mcp/src/resources/house_rules_variants/*.md                     # finalize content
platform/src/lib/feature_flags.ts                                        # MARSYS_FLAG_MCP_V3_ENABLED → true
00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md                              # register v3 artifacts
00_ARCHITECTURE/CAPABILITY_MANIFEST.json
00_ARCHITECTURE/MCPT_V310_CLOSE.md                                       # NEW sealing artifact
00_ARCHITECTURE/SESSION_LOG.md                                           # append
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                                    # state pointer
.geminirules                                                             # MP.1 mirror
.gemini/project_state.md                                                 # MP.2 mirror
CLAUDE.md                                                                # §E concurrent workstream entry
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md                 # flip status to COMPLETE (if all sub-phases done)
```

## §3 — Files NOT in scope

```
platform/src/app/consume/**, platform/src/app/api/chat/**                # web /consume untouched
platform/src/lib/prompts/templates/shared.ts                             # F.6 still out
```

## §4 — Merge protocol

Per `MCP_TRANSFORMATION_PLAN §7`. After local sealing commits:

```bash
git fetch origin feature/mcpt-final
git rebase origin/feature/mcpt-final
ls platform/supabase/migrations/ | sort -n | uniq -d   # must return empty
cd platform-mcp && npm test
cd ../platform && npm test
git checkout feature/mcpt-final
git merge --no-ff feature/mcpt-foundation -m "MCPT v3.1.0: foundation seal → final"
git push origin feature/mcpt-final
```

## §5 — Acceptance criteria (AC.S6.1 through AC.S6.10)

Per parent brief §4 / v3.1.0-S6.

## §6 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  test -f 00_ARCHITECTURE/MCPT_V310_CLOSE.md && \
  grep -q "MARSYS_FLAG_MCP_V3_ENABLED.*true" platform/src/lib/feature_flags.ts && \
  grep -q "MCPT_V310_CLOSE" 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md && \
  grep -q "MCP Transformation" CLAUDE.md && \
  git log --oneline feature/mcpt-final -1 | grep -q "MCPT v3.1.0" && \
  cd platform && npm test 2>&1 | tail -5
```

## §7 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_CLOSE.md`. Comprehensive: per-sub-phase AC evidence table, residual risks, v3.2 entry conditions, mirror-propagation evidence (`.geminirules` + `.gemini/project_state.md` diffs attached), red-team scheduling note for v3.4-S2.

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S6_v1_0.md.*
