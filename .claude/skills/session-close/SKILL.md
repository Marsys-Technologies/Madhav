---
name: session-close
description: Prepare and validate the SESSION_CLOSE checklist for a formal governance session or chartered campaign close.
---

## Steps

1. Follow root `CLAUDE.md` §C and §G / §H, the owning campaign charter, and the current `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md`. Establish which session or campaign owns the close, the work order and its lease.

2. Save the `session_close` YAML using the template's actual fields. Record observed checks, changes, work-order outcome and verified lease release. Prepare the matching `session_open` YAML when the scope cross-check applies. Keep reports in the assigned evidence location.

3. Validate the saved checklist from the repository root. Set the variables to the actual checklist, matching open YAML and report paths.
   ```bash
   python3 platform/scripts/governance/schema_validator.py \
     --close-checklist "$close_checklist" \
     --session-open-for-close "$session_open" \
     --json-path "$validation_json" \
     --report-path "$validation_report"
   ```

   Include the open YAML for the scope cross-check when applicable. If validation fails or the validator is unavailable, leave the close pending and record the failing fields or missing evidence.

4. After successful validation, append the open block, session body and close block as one entry to `00_ARCHITECTURE/SESSION_LOG.md` through the owning campaign's coordination path.

5. Apply any assigned state or work-order transition. A root `CLAUDECODE_BRIEF.md` applies only when it names this session or worktree and is active under §C. Mark it complete only when its own completion criteria and write authority are satisfied.
