---
name: pr-description
description: Generate a well-structured PR description for the current branch following Madhav's PR template. Run /run-checks first.
---

## Steps

1. Get the diff summary:
   ```bash
   git log main..HEAD --oneline
   git diff main --stat
   ```

2. Write the PR description using this template:

```markdown
## Summary
- <bullet: what changed and why>
- <bullet>

## Changes
| File | Change |
|---|---|
| `path/to/file` | What changed |

## Test plan
- [ ] ESLint passes
- [ ] TypeScript passes
- [ ] Unit tests pass
- [ ] Manual smoke: <specific route or feature to verify>

## Migration notes
<If migrations included: list them and what they do. Otherwise: None.>

## Acceptance criteria
<List from the brief/CLAUDECODE_BRIEF.md if one exists>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

3. Raise the PR with:
   ```bash
   gh pr create --title "<title>" --body "<description>"
   ```
