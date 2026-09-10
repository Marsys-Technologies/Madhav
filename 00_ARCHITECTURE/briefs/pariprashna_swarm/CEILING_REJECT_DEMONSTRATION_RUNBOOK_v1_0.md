---
artifact: CEILING_REJECT_DEMONSTRATION_RUNBOOK
canonical_id: PARIPRASHNA_CEILING_REJECT_RUNBOOK
version: 1.0
status: READY TO RUN — requires a supervised session; deliberately NOT executed autonomously
authored: 2026-08-23, pre-Phase-5 closeout
gates: P3-F (THE FLIP) precondition 3 — "limits live AND the ceiling reject demonstration performed"
---

# Ceiling reject demonstration — runbook

## Why this is a runbook and not a completed item

This is a **P3-F flip precondition** that has never been run. The closeout run proved everything it
could prove without deploying, and parked the live half deliberately. Both halves are stated here so
the reader can see exactly where the line falls.

### What IS proven, and how

**The refusal path works, and its detectors can fail.** `enforce_turn_limits.test.ts` was run and
mutated: neutralising the refusal (`if (!spend.allowed)` → `if (false && !spend.allowed)`) turned
exactly **three** tests red —

- `refuses the same turn once the flag is flipped on — proving the flag is the only difference`
- `per-turn ceiling breach`
- `daily ceiling breach, on the MCP door`

— while the other **seven** stayed green. Targeted, not blanket. Reverted clean afterward.

This upgrades the completeness audit's *"the refusal path is unexercised"*: it **is** exercised, and
its detectors are real. What has never happened is a **live** observation on a deployed revision.

### What is NOT proven

A real HTTP turn against a real deployed revision receiving a real `429` /
`LIMIT_SPEND_CEILING_EXCEEDED`, followed by a normal turn succeeding.

## Why the closeout run did not do it

Not cost, and not permission — **blast radius**.

The demonstration needs `MARSYS_SPEND_CEILING_PER_TURN_USD` set to something tiny. The only way to
get an env var onto a Cloud Run revision is `gcloud run deploy`, and **that mutates the service
template even with `--no-traffic`**. Every subsequent revision then inherits it.

That is not hypothetical. Earlier the same night, a flag-off probe used `--update-env-vars` and
mutated the template; revisions `01683`–`01689` all inherited `MARSYS_FLAG_PARIPRASHNA_ENABLED=false`
and **Paripraśna was disabled in production for roughly 80 minutes**. The failure mode here is worse:
a template carrying a near-zero per-turn ceiling would refuse **every production turn**, and the
symptom (`429` on everything) looks like an outage, not a config error.

**It is also not blocking anything.** The flip is time-gated on DD-7 green×7 regardless, and that
clock restarts after #1515 (see below). Nothing waits on this.

## The cheap-and-safe property, worth knowing before you run it

`checkSpendCeilings` compares a **projection** computed *before* dispatch:

```ts
if (projected !== null && projected > SPEND_CEILING_PER_TURN_USD) { … refuse … }
```

So the refusal fires **pre-dispatch**. The demonstration costs **no LLM spend at all** — you are not
buying $40 of turns to trip a $40 ceiling. Set the ceiling below the projection and the very first
turn is refused before any provider call.

The ceilings are already env-overridable, and the code says why:

```ts
/** NCD-8: $2 per turn. Env override exists for staging drills, not for production relaxation. */
export const SPEND_CEILING_PER_TURN_USD = Number(process.env.MARSYS_SPEND_CEILING_PER_TURN_USD ?? '2')
export const SPEND_CEILING_PER_DAY_USD  = Number(process.env.MARSYS_SPEND_CEILING_PER_DAY_USD  ?? '40')
```

**A staging drill is exactly what this is.** The override exists for it.

## Procedure

Run supervised. Steps 1 and 5 are the ones that matter; do not skip 5 even if 4 fails.

**1 — Record the current template, so restoration is a fact and not a memory.**

```bash
gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --format=json > /tmp/amjis-web-template-before.json
grep -c MARSYS_FLAG /tmp/amjis-web-template-before.json   # expect 16
```

**2 — Deploy the drill revision, no traffic, tagged.**

```bash
gcloud run deploy amjis-web \
  --region asia-south1 --project madhav-astrology \
  --image asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:$(git rev-parse origin/main) \
  --no-traffic --tag ceiling-drill \
  --update-env-vars MARSYS_SPEND_CEILING_PER_TURN_USD=0.0001
```

**3 — Drive a synthetic turn at the tagged URL.** Synthetic chart only — never `482012f1-…`.

```bash
# the tagged URL is printed by step 2; it looks like
#   https://ceiling-drill---amjis-web-<hash>-el.a.run.app
npx tsx platform/scripts/probe/ask.ts --base-url <tagged-url> --chart-id <synthetic>
```

**Expect:** HTTP `429`, body code `LIMIT_SPEND_CEILING_EXCEEDED`, and a message naming the ceiling.
**Record the actual response, not a paraphrase.**

**4 — Prove it is the ceiling and not a coincidence.** Redeploy the same tag with the ceiling back at
`2`, drive the same turn, observe it succeed. A refusal that cannot be turned off is not evidence
the ceiling caused it.

**5 — Restore the template, and verify by reading it back.**

```bash
gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
  --remove-env-vars MARSYS_SPEND_CEILING_PER_TURN_USD

gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --format=json > /tmp/amjis-web-template-after.json
diff <(jq -S '.spec.template.spec.containers[0].env' /tmp/amjis-web-template-before.json) \
     <(jq -S '.spec.template.spec.containers[0].env' /tmp/amjis-web-template-after.json) \
  && echo "TEMPLATE RESTORED — byte-identical env"
```

**Then verify by effect, not by inspection:** drive one normal turn against the **production** URL
and confirm it succeeds. The 80-minute incident above was invisible to a watchdog that checked
`/login=200` but never the thing it had itself changed.

**6 — Delete the drill revision** once the receipt is recorded.

## Recording the result

The demonstration is not done when it works — it is done when the evidence is in the repo. Land the
actual request/response pair (both the refused turn and the succeeding one) under
`00_ARCHITECTURE/briefs/pariprashna_swarm/dd1_evidence/` or a sibling path that is **not**
gitignored. MATERIAL-6 exists because a proof was written to an ignored directory and survived only
in one local worktree.
