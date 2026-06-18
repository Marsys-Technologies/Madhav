---
name: session-close
description: Emit and validate the SESSION_CLOSE artifact per CLAUDE.md §H and SESSION_CLOSE_TEMPLATE_v1_0.md. Run at end of every substantive session.
---

## Steps

1. Read `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` to get the current close schema.

2. Emit the SESSION_CLOSE block with all required fields filled:
   - `session_id`, `step_completed`, `artifacts_produced`, `may_touch_actual`, `must_not_touch_respected`
   - `drift_detector_run`, `schema_validator_run`, `red_team_due`, `red_team_discharged`
   - `current_state_updated`, `session_log_appended`

3. Run schema validation (verify the flag exists first):
   ```bash
   python3 platform/scripts/governance/schema_validator.py --help 2>&1 | grep -i session
   # If --session-close flag exists, run it:
   python3 platform/scripts/governance/schema_validator.py --session-close
   # If not, skip this step — validator may not have this mode yet
   ```

4. If validation passes, append the session block to `00_ARCHITECTURE/SESSION_LOG.md`.

5. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 with the new position.

6. Set `status: COMPLETE` in `CLAUDECODE_BRIEF.md` if one exists at project root.
