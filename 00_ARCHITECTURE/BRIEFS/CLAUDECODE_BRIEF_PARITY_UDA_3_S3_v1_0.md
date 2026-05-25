---
session_id: UDA-3-S3
phase: UDA-3
title: "Planner prompt R-NRM.1 rule + Gemini mirror"
status: pending
---

# UDA-3-S3: Planner Prompt R-NRM.1

## Goal
Add the R-NRM.1 normalization rule to the PLANNER_PROMPT and update the Gemini mirror.

## Steps

1. Find the active PLANNER_PROMPT file:
   ```bash
   ls platform/src/lib/planner/PLANNER_PROMPT*.md | tail -1
   ```

2. Add rule R-NRM.1 to the rules section:
   ```
   R-NRM.1 — Canonical tool names: When a tool exists in both portal and MCP with different names,
   the portal planner uses the canonical portal name; the MCP consumer uses the MCP name.
   Both names are declared in CAPABILITY_MANIFEST alias_names[]. Do not invent names not in
   the INTERFACE_NORMALIZATION_REGISTER.
   ```

3. Increment the PLANNER_PROMPT version in frontmatter by 0.1.

4. Update `.geminirules` (MP.1 mirror): add equivalent R-NRM.1 rule in the Gemini rules section.

5. Commit:
   ```bash
   git add platform/src/lib/planner/PLANNER_PROMPT*.md .geminirules
   git commit -m "governance(uda3): UDA-3-S3 — planner R-NRM.1 + .geminirules mirror"
   ```

## Acceptance criteria
- PLANNER_PROMPT contains R-NRM.1
- .geminirules contains equivalent R-NRM.1
- Version in PLANNER_PROMPT frontmatter incremented
