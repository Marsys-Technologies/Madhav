---
artifact: CLAUDECODE_BRIEF_MCPT_V32_HAIKU_TIER_NOTE.md
session: MCPT-V32-HAIKU-TIER-NOTE
workstream: MCPT v3.2 Quality Tightening (post-close documentation note)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav)
estimated_duration: 5 minutes
cost: free (docs-only)
---

# Claude Code Brief — MCPT v3.2 Haiku-Tier Framing Note

## Scope

MCPT v3.2 only. Single docs change: append a framing note to `MCPT_V32_CLOSE.md` explaining why the routing eval result of 29/30 (96.7%) is a Haiku-tier floor, not a ceiling, and why no further description tuning is recommended without real production routing data.

**In scope:**
- `MCPT_V32_CLOSE.md` (wherever it lives — root or `00_ARCHITECTURE/`)

**Out of scope:**
- Tool descriptions (no code change).
- Re-running R3 with Sonnet/Opus (would require harness change — not in this scope).
- Any other file. Anything other than `MCPT_V32_CLOSE.md` must remain untouched.
- `PROBE_anthropic_tools_forwarding.test.ts`, `evals/mcp-routing/results_b9f372a3.json`, or any other untracked items in working tree.

## Preconditions

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD                    # main
git status --porcelain | head                      # may have known untracked items; those stay
git pull --ff-only origin main

# Locate the close file
ls MCPT_V32_CLOSE.md 2>/dev/null || ls 00_ARCHITECTURE/MCPT_V32_CLOSE.md 2>/dev/null
```

If neither location has the file, STOP and report — close file should exist post-merge.

## Step 1 — Append the framing section

Append to the end of `MCPT_V32_CLOSE.md` (whichever path resolves):

```markdown
## Routing Eval Framing — Why 29/30 Is the Haiku Floor, Not the Ceiling

The MCPT v3.2 routing-accuracy eval (R3) was measured against `claude-haiku-4-5`, the smallest model in the Anthropic family. The final result of 29/30 (96.7%) clears the ≥80% absolute acceptance target with margin. The one persistent failure (`chart_summary_d9_request`, prompt: "Give me my D9 chart") returned `no_tool_call` across three independent runs, including after the post-merge DESC_TUNE (commit `1868ce31`) added explicit "navamsa" and "D9" mentions to the `chart_summary` description.

### Why we are not chasing the remaining 3.3pp

1. **The failure is at the model-inference layer, not the description layer.** The description already says "FIRST CALL when interpreting any chart end-to-end" and now explicitly names "navamsa" and "D9". Three runs returning the same failure means it is a deterministic Haiku tendency, not random noise. Further description tuning would be tuning the wrong dial.

2. **Haiku is not the production consumer.** The MCP server is consumed primarily by Claude Code in Antigravity, Claude Desktop, and Cowork. Those clients run Sonnet 4.6 or Opus 4.7, both materially stronger at tool-calling discipline than Haiku. The real-world routing on the same prompt is very likely correct on those tiers but is currently untested.

3. **The 29/30 number is therefore a floor, not the operating ceiling.** Production routing accuracy is probably higher and would require a separate eval run against Sonnet/Opus to measure. That eval is not part of MCPT v3.2 scope.

### What would change this position

- Real production data (from `query_trace_steps` or `tool_execution_log`) showing the same `no_tool_call` pattern at scale with Sonnet/Opus consumers. If that emerges, open a follow-up to either:
  - Add explicit example invocations to the `chart_summary` description, or
  - Tune the system prompt at the consumer side (out of MCP server scope), or
  - Accept and widen the eval's `acceptable_alternatives` to include `no_tool_call` for this specific prompt.

- A planned cross-tier routing eval that re-runs R3 against Sonnet 4.6 and Opus 4.7 to establish the per-tier accuracy curve. Not committed; would be a separate brief.

### Net

MCPT v3.2 closes at 96.7% Haiku-floor with the documented limitation. The DESC_TUNE was the right move (it lifted 28/30 → 29/30) and no further tuning is recommended until production routing data warrants it.
```

## Step 2 — Commit and push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Stage ONLY the close file
git add MCPT_V32_CLOSE.md
# OR: git add 00_ARCHITECTURE/MCPT_V32_CLOSE.md  (depending on location)

# Verify staging — must be exactly 1 file
git diff --cached --name-only
# Expected: just MCPT_V32_CLOSE.md (with appropriate path). NOTHING ELSE.

git commit -m "docs(mcpt-v32): document Haiku-tier framing for 29/30 routing eval result

Adds a 'Routing Eval Framing' section to MCPT_V32_CLOSE.md explaining why
29/30 (96.7%) is the Haiku-floor measurement, not the production ceiling.
The remaining persistent failure (chart_summary_d9_request) is a
deterministic Haiku tool-calling tendency. Production consumers
(Claude Code in Antigravity, Claude Desktop, Cowork) run Sonnet 4.6 /
Opus 4.7 which are stronger at tool-call discipline; the real-world
routing accuracy on this prompt is likely higher but untested.

No code or description change. Documentation only. MCPT v3.2 stays
closed at 29/30 ≥ 80% target.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

## Acceptance — done when

- [ ] `MCPT_V32_CLOSE.md` has the new "Routing Eval Framing" section.
- [ ] Commit pushed to origin main.
- [ ] Nothing else was modified, staged, or committed in this session.
- [ ] Native has been notified with the commit SHA.

## Final report

1. **Commit SHA** of the docs change.
2. **Path** of the close file that was updated (root or 00_ARCHITECTURE/).
3. **Confirmation** that no other files were touched (`git status --porcelain` post-commit shows the same untracked items as pre-session and nothing else).

## Failure modes

| Failure | Action |
|---|---|
| `MCPT_V32_CLOSE.md` doesn't exist anywhere | STOP. Report. The close file should exist after the merge — its absence means something earlier didn't happen as expected |
| Anything outside `MCPT_V32_CLOSE.md` ends up in staging | STOP. Unstage. Investigate |
| `git push` rejected | Pull first (`git pull --ff-only origin main`), re-push. Surface any new merge conflicts to native |

## Out of scope

- Touching any tool description.
- Touching CLAUDE.md, .geminirules.
- Re-running R3 with Sonnet/Opus (that is the planned follow-up, not this brief).
- Modifying `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md` (already updated in the verification commit).
- Any file under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`.
- Other-stream artifacts (PROBE test, legacy logs).
