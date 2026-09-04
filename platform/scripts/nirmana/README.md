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

## `nrec` — evidence-submission helper (charter C8.2; ruling on issue #1716)

Submits one campaign evidence/definition command to the executor route **with the correct service
account, and refuses to send it with the wrong one.**

```bash
platform/scripts/nirmana/nrec --as verifier --file capsule.json
platform/scripts/nirmana/nrec --as executor --file analysis_accepted.json
cat cmd.json | platform/scripts/nirmana/nrec --as executor
platform/scripts/nirmana/nrec --as verifier --file capsule.json --dry-run   # decide only; mint nothing, send nothing
```

Requires `jq`, `curl`, and a `gcloud` session holding `serviceAccountTokenCreator` on the two
campaign service accounts.

### The identity split it enforces

The campaign enforces implementer ≠ certifier at two layers — the HTTP route
(`requiredPrincipalFor`, `nirmana-elevation-executor/route.ts`) and the DB trigger
(`nirmana_elevation_guard_server_reconstructed_insert`). Both make the same split:

| `source_kind` | identity | events |
|---|---|---|
| `server_reconstructed` | **verifier** SA | `integrity_verified`, `asset_frozen`, `probe_accepted`, `stage_transition_accepted`, `foundation_lane_accepted` |
| anything else | **executor** SA | `asset_analysis_accepted`, `optimization_verdict_accepted`, `implementation_accepted`, `build_run_authorized`, `accepted_rebuild_observed`, `producer_covered`, `static_accepted`, `source_accepted`, `empty_accepted`, `retired_with_disposition` |

Five sessions need this mechanism ~110 more times. Each inlining its own `gcloud`+`curl` is five
chances to blur that split — which is hard-floor territory, not a style question.

### Two design decisions to know before editing this script

1. **The required identity is derived from the submitted `source_kind`, never from a hardcoded
   `event_type` list.** That is how `route.ts` does it, and its own comment says why: checking the
   actual `source_kind` "keeps this in sync with that schema by construction". A list here would be
   a fourth copy of the split, free to drift from the other three. **Do not add one** — the table
   above is documentation, not the implementation.
2. **`--as` is required and is *checked*, not inferred.** The helper could silently pick the right
   identity from the body, and that is exactly what it must not do. The caller declares which hat it
   is wearing; the helper refuses a mismatch. A helper that quietly corrects you teaches nothing,
   and would let a session mint a verifier capsule for work it had just implemented without ever
   noticing it had crossed the line. On refusal it exits **2** and explains which rule was broken.

### `--include-email` is not optional, and the failure is silent

`nrec` always passes it. Without it the minted JWT carries no `email` claim at all,
`verifyOidcToken()` returns null on `if (!payload?.email)`, and the route answers **403** —
indistinguishable from a wrong or expired token unless you already know to look. This cost a
previous session real time; it is recorded in `CAMPAIGN_STATE.md` (2026-09-01) and is why the flag
is hardcoded here rather than left to each caller.

### Exit codes

| code | meaning |
|---|---|
| 0 | accepted (HTTP 2xx), or a clean `--dry-run` |
| 1 | usage error, token minting failed, or the route rejected the body |
| 2 | **identity mismatch — refused before minting any token or sending anything** |

A **409** is surfaced with a note rather than treated as a plain failure: it means the event already
exists, which is usually correct idempotent behaviour. Check the ledger before re-submitting.
