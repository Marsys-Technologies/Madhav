# P1 Takeover onboarding

Start from the P0 branch/PR evidence, then create an approved P1 runtime outside the repo.
Never copy historical assurance heartbeat files into it.

```sh
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/cli.py --runtime "$TRACKER_RUNTIME" provision-credentials
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/cli.py --runtime "$TRACKER_RUNTIME" projection
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/cli.py --runtime "$TRACKER_RUNTIME" verify
```

Before recording P1 work, verify replay is `ok: true`, inspect rejected events, enroll a
real phase lead/verifier/integrator identity through the approved deployment process, and
replace the local-proof credential issuer before any non-loopback deployment. Retrieve only
the owning actor's runtime token (for example, `jq -r '.tokens.lead-p1'
"$TRACKER_RUNTIME/local-credentials.json"`) and record a P1 `work_started` event with
branch, worktree, baseline SHA, model/reasoning configuration, assignment, ceiling, any
recorded cost, an optional validated `participants` roster (registered known roles must match
their exact role and stream eligibility; unregistered contributors are explicitly
`SPECIALIST`, with role/state/assignment/model/reasoning configuration), and evidence links. Do not submit
percentages. A stream lead supplies only its own stream sequence; verification and completion
require the independent verifier then integrator. After every stream finding is triaged, the
surrogate must record one frozen `remediation_plan` (including `[]` where none is required)
before remediation work can earn credit.
