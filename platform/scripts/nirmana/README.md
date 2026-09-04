# NIRMĀṆA campaign tooling

Shared, **Conductor-owned** tooling for the NIRMĀṆA v2.1 parallel campaign (charter C5: propose
changes via a `nirmana-adjudication` issue; only the Conductor merges them). Everything here is
strictly read-only — these scripts observe campaign state, they never write an event, never
dispatch a build, and never touch `asset_registry`.

Governing law: `00_ARCHITECTURE/briefs/nirmana/sessions/SESSION_CHARTER_V21.md`.

## `egate.sql` — E-gate batch eligibility (charter C2 + C10)

Answers "which of my layer's assets may enter W4 right now?" in one query, for a whole layer.
**Run it once per loop for your layer — not once per asset** (C10's batch-eligibility variant).

```bash
cd platform
set -a; . ./.env.local; set +a
psql "$DATABASE_URL" -v layer=L2 -f scripts/nirmana/egate.sql   # or -v layer=ALL
```

One row per not-yet-frozen asset, sorted so the actionable ones come first:

| column | meaning |
|---|---|
| `unfrozen_ancestors` | count of the transitive `depends_on` closure (per the FROZEN definition) that lacks an `asset_frozen` event — **C2.1** |
| `w2_analysis`, `w2_verdict` | whether `asset_analysis_accepted` / `optimization_verdict_accepted` are recorded — **C2.2** |
| `gate` | `OPEN-PENDING-PIN` · `BLOCKED-NO-ROUTE` · `BLOCKED-ANCESTORS` |
| `waiting_on` | the specific unfrozen ancestors, so a block is diagnosable without a second query |

### Why the best verdict is `OPEN-PENDING-PIN` and never `OPEN`

The E-gate has **three** conditions. This query establishes two of them. The third — C2.3, that
your analysis generation-pins still match (writer digest + upstream generation) — is a comparison
against pins recorded in your own W1/W2 artifacts, which do not live in this schema. No query
against `nirmana_evidence` can establish it, so this tool does not claim to.

Naming the best outcome `OPEN` would be a status asserting more than its detector measures, which
is precisely the defect §N.8 (Earned-Signal Principle) exists to forbid — and a green that cannot
read false is not a green. Check your pins yourself, then dispatch. On a pin mismatch, C2.3 asks
for a delta re-review first; that is normally minutes, not a redo.

### Reading the output

- `BLOCKED-ANCESTORS` → nothing to do but wait; `waiting_on` names who you are waiting for. Do not
  poll it per-asset — the batch run tells you the moment it clears.
- `BLOCKED-NO-ROUTE` → **this one is yours.** The asset is upstream-clear; what it lacks is your own
  W1 analysis and W2 route decision. Neither is ever gated (C2), so this is always work you can do
  right now.
- `OPEN-PENDING-PIN` → verify pins, claim a run slot on the coordination issue, then dispatch.
