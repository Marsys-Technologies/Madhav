# PR Triage Executions — V1.3 Production Activation
<!-- generated: 2026-06-05 -->

| PR # | Title (short) | Disposition | Action Taken | Result |
|------|---------------|-------------|--------------|--------|
| #205 | BO-2-7 provenance_envelope fix | CLOSE_STALE | `gh pr close 205 --comment "..."` | CLOSED — fully superseded by commit 3428045c on main |
| #204 | BO-2-6 provenance_envelope fix | CLOSE_STALE | `gh pr close 204 --comment "..."` | CLOSED — fully superseded by commit 3428045c on main |
| #203 | BO-2-5 provenance_envelope fix | CLOSE_STALE | `gh pr close 203 --comment "..."` | CLOSED — fully superseded by commit 3428045c on main |
| #202 | BO-2-8 Gate-1 pass | CLOSE_STALE | `gh pr close 202 --comment "..."` | CLOSED — fully superseded by commit 3428045c on main |
| #201 | BO-2-4 Gate-1 pass | CLOSE_STALE | `gh pr close 201 --comment "..."` | CLOSED — fully superseded by commit 3428045c on main |
| #170 | FAIL — A3+A4+A5 build blocked | CLOSE_STALE | `gh pr close 170 --comment "..."` | CLOSED — operator run log artifact; title starts with FAIL; CI fixes superseded by ws arc |
| #206 | ws0b: legacy code cluster purge | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: platform/src/lib/observatory/capability_telemetry.ts deleted in HEAD vs modified in branch; rebase aborted |
| #199 | GA-1-6 sensitive_points | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: 00_ARCHITECTURE/CONDUCTOR/brahma/smriti/build_state.yaml content conflict; rebase aborted |
| #198 | GA-1-3 ganita.divisionals D9 fix | MERGE_WITH_REBASE | `gh pr merge 198 --rebase --admin` | MERGED — merged at 2026-06-05T15:38:55Z |
| #197 | GA-1-1 ganita.engine ayanamsa fix | MERGE_WITH_REBASE | `gh pr merge 197 --rebase --admin` | MERGED — merged at 2026-06-05T15:39:07Z |
| #196 | BG-0-7 brahmagyan.concordance | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: platform-mcp/src/server.ts content conflict; rebase aborted |
| #195 | BG-0-8 brahmagyan.almanac | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: brahmagyan/__init__.py add/add + main.py content conflict; rebase aborted |
| #194 | BG-0-1 brahmagyan.ephemeris | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: platform-mcp/src/server.ts content conflict; rebase aborted |
| #193 | BG-0-3 brahmagyan.texts | MERGE_WITH_REBASE | `gh pr merge 193 --rebase --admin` | MERGED — merged at 2026-06-05T15:39:16Z |
| #191 | GA-1-7 chart_panchanga pipeline writer | MERGE_WITH_REBASE | `gh pr merge 191 --rebase --admin` | MERGED — merged at 2026-06-05T15:39:25Z |
| #190 | BG-0-2 brahmagyan.reference | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: platform-mcp/src/server.ts content + pipeline/__init__.py add/add; rebase aborted |
| #189 | GA-1-8 platform/src/lib/ganita/ facts_store | MERGE_WITH_REBASE | `gh pr merge 189 --rebase --admin` | MERGED — merged at 2026-06-05T15:39:34Z |
| #185 | fix(docker): libgl1-mesa-glx → libgl1 Bookworm | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: vargas_writer.py modify/delete + task_route.test.ts content + CockpitShell.tsx add/add; rebase aborted |
| #183 | fix(pariksha): P0 security+schema+cockpit+D1 | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: vargas_writer.py modify/delete + task_route.test.ts content + CockpitShell.tsx add/add; rebase aborted |
| #180 | fix(cockpit+pipeline): mount v2 + SSE + IAM | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: deploy.yml content + infra/cloud_tasks/main.tf modify/delete + build_chart.py modify/delete + build/page.tsx content; rebase aborted |
| #179 | fix(cleanup): post-arc eight-item hygiene | MERGE_WITH_REBASE | Test rebase onto main | KEEP_OPEN — CONFLICT: deploy.yml content + .gitignore content + dashas_writer.py modify/delete + NewClientForm.tsx content; rebase aborted |

## Summary

- **CLOSE_STALE**: 6/6 closed successfully (#205, #204, #203, #202, #201, #170)
- **MERGE_NOW**: 0 PRs in this category
- **MERGE_WITH_REBASE — MERGED**: 5 PRs (#198, #197, #193, #191, #189)
- **MERGE_WITH_REBASE — KEEP_OPEN (conflict)**: 10 PRs (#206, #199, #196, #195, #194, #190, #185, #183, #180, #179)

## KEEP_OPEN conflict notes

All KEEP_OPEN PRs failed automated rebase due to real merge conflicts. Common conflict sites:
- `platform-mcp/src/server.ts` — ws3 (#210) already rewrote this file; blocks #196, #194, #190
- `platform/python-sidecar/brahmagyan/__init__.py` / `main.py` — ws2 (#211) already wired these; blocks #195
- `platform/src/components/cockpit/CockpitShell.tsx` — ws1 (#209) already restructured; blocks #185, #183
- `platform/python-sidecar/pipeline/writers/vargas_writer.py` — deleted in main (ws arc), modified in branches; blocks #185, #183
- `.github/workflows/deploy.yml` — ws arc changes; blocks #180, #179
- `00_ARCHITECTURE/CONDUCTOR/brahma/smriti/build_state.yaml` — concurrent smriti writes; blocks #199
- `platform/src/lib/observatory/capability_telemetry.ts` — deleted in main, modified in ws0b; blocks #206

These PRs require manual conflict resolution before they can be merged.
