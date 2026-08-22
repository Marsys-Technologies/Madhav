---
artifact: P3F_FLIP_ROLLBACK_PIN
canonical_id: P3F_FLIP_ROLLBACK_PIN
version: 1.1
status: PRE-POSITIONED — the flip (P3-F) has NOT executed. This document is a ready,
  syntax-verified rollback pin authored ahead of the flip per charter §4 Wave P3-4
  precondition 6 ("rollback pin committed BEFORE the flip commit"). Nothing in this
  document has been executed against production; it changes nothing.
role: >
  The un-flip runbook for Paripraśna P3-F (THE FLIP — "default routing everywhere").
  Written by the DEPLOY WARDEN during the P3+P4 overnight autonomous run while the
  flip itself is PARKED (blocked on a placeholder CI-smoke credential, per the run's
  hard-never on credential operations). Read this immediately before the flip merges,
  re-verify the pinned revision fresh (do not trust tonight's snapshot), then treat
  §3 as copy-paste.
supersedes: none — v1.1 corrects v1.0 in place; same document.
changelog:
  - "1.1 (2026-08-22, PARIPRASHNA-P3-P4-OVERNIGHT session, BUILDER lane p3f-pin,
    review-fix pass against a SURVIVES-WITH-FINDINGS verdict on PR #1503) — three
    blocking corrections, all independently re-verified live (read-only `gcloud`) before
    being written: **(1)** the `--set-env-vars` blast-radius claim was factually wrong
    and understated ~4×: corrected `MARSYS_FLAG_PARIPRASHNA_*` count from a miscounted
    13 to the verified 11 (of 15 total `MARSYS_FLAG_*`, of 44 plain-value, of 64 total
    env entries, all re-measured live on `amjis-web-01671-47n`), and re-scoped the
    hazard from '~12 feature flags' to the true casualty class — all 44 plain-value env
    vars including `DB_NAME`/`DB_USER`/`INSTANCE_CONNECTION_NAME`/`NODE_ENV`/`APP_URL`/
    `GCP_PROJECT`/`PYTHON_SIDECAR_URL`/`WATCHDOG_SECRET`/all six `NEXT_PUBLIC_FIREBASE_*`
    — per `gcloud run services update --help`'s own text ('All existing environment
    variables will be removed first'); also resolved the previously-open 'not verified
    whether secrets are affected' worry as a definitive no, via the `--help` synopsis
    showing env-var flags and secret flags as two independent, mutually exclusive
    bracket groups. **(2)** §5.2's functional verification check was demonstrated to be
    green-either-way for PRIMARY specifically (a §N.8 defect): the check reads
    `PARIPRASHNA_ENABLED`, which PRIMARY never changes — verified live that
    `amjis-web-01671-47n`, `amjis-web-02826-huf` (limits canary), and
    `amjis-web-01673-665` (revision serving now) all carry
    `MARSYS_FLAG_PARIPRASHNA_ENABLED=true` — so §5.2 is now scoped explicitly to
    SECONDARY, a 'PRIMARY currently has no functional detector' statement was added, and
    the false foreclosure sentence ('nothing obvious … no plausible looks-green-
    either-way failure mode here') was deleted and replaced with the corrected,
    scope-honest analysis. **(3)** the pinned revision named in §4 was found to be a
    safety regression, not merely stale: production armed
    `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED` tonight (native-authorized, §0 ruling 3)
    after `amjis-web-01671-47n` was captured, and the service has since moved twice
    (through the `limits-canary`-tagged `amjis-web-02826-huf` to the now-serving
    `amjis-web-01673-665`, both confirmed `LIMITS_ENABLED=true` live) — a PRIMARY
    rollback to the literal §4 revision would silently disarm the $2/turn and $40/day
    spend ceilings and per-user rate limits on both doors
    (`platform/src/lib/limits/index.ts:53`) while the operator believes they only undid
    the flip. Fixed by deleting the literal revision name from §4's table (replaced with
    `<read fresh — see §3>`), adding new §4.1 documenting the drift with a live-verified
    table, retracting §4's now-false 'clean single-revision steady state' reassurance,
    and adding a new mandatory rule to §3 PRIMARY: diff the candidate revision's env
    against the currently-serving revision's before shifting traffic, to confirm no
    `MARSYS_FLAG_*` safety flag would be lost. Non-blocking, also fixed: added
    `platform/src/app/clients/[id]/samiksha/page.tsx:27` as a fifth
    `PARIPRASHNA_ENABLED` guard site to §1.1 (SECONDARY also takes down the SAMĪKṢĀ
    review tab); corrected the §1.1 `feature_flags.ts` citation from `169–174` to
    `164–170` (`171–174` is `PARIPRASHNA_LIMITS_ENABLED`'s own comment) and added the
    `default false` line citation (`feature_flags.ts:523`). Nothing in this pass was
    executed against production — all verification was read-only `gcloud describe` /
    `revisions describe` / `--help` plus static code reads in the worktree; no traffic,
    env var, deploy, or credential was touched."
  - "1.0 (2026-08-22, PARIPRASHNA-P3-P4-OVERNIGHT session, DEPLOY WARDEN lane) — first
    generation. Flip mechanism traced from code (feature_flags.ts, pariprashna/page.tsx,
    deploy.yml); PB-4/P3-F design intent traced from
    PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md and
    PARIPRASHNA_ASBUILT_BASELINE_v1_0.md §1. Live revision + traffic split captured from
    `gcloud run services describe amjis-web` at 2026-08-22T22:38:41Z. One unresolved
    ambiguity flagged for human confirmation before the flip merges (§6)."
---

# P3-F Flip — Rollback Pin

## §0 — What this document is, and is not

This is precondition 6 of charter §4 Wave P3-4, discharged in advance: *"rollback pin
committed BEFORE the flip commit — the un-flip is a ready traffic/env command, tested
in syntax, before the flip happens."*

The flip (P3-F) has **not executed**. Tonight it is **parked**: the CI post-deploy
smoke's credential is a one-character placeholder, so the green×7 cadence (precondition
2) cannot start, and provisioning a real credential is a hard-never for this run (§9).
P3-F will most likely execute on a future night, driven by whoever is at the keyboard —
which is exactly why this pin exists now, while there is time to get it right.

Nothing in this document was executed against production. Every `gcloud` command below
was run in a **read-only** form (`describe`, `--help`) to prove syntax and capture the
live baseline; no traffic, env var, or deploy state was touched.

---

## §1 — What the flip actually changes (traced from code, not assumed)

### 1.1 The gating flag that exists today

`PARIPRASHNA_ENABLED` is a `FeatureFlag` (`platform/src/lib/config/feature_flags.ts:164–170`
— corrected citation; `171–174` is the start of `PARIPRASHNA_LIMITS_ENABLED`'s own comment,
a different flag, not this one — default `false` in code at `feature_flags.ts:523`). It is
read via `configService.getFlag('PARIPRASHNA_ENABLED')` and gates whether the new
conversation surface (`/clients/[id]/pariprashna`, `/api/pariprashna`,
`/api/pariprashna/resume`) exists at all for a given deploy:

- `platform/src/app/clients/[id]/pariprashna/page.tsx:42–44` — **the load-bearing guard**:
  ```
  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    redirect(`/clients/${id}/consult`)
  }
  ```
  This check runs **before** any auth resolution (`resolveChartPageAccess` is called on
  line 46, after the flag check) — so the redirect fires unconditionally on flag state,
  for authenticated and unauthenticated requests alike. Verified live tonight (§4).
- `platform/src/app/api/pariprashna/resume/route.ts:80` and
  `platform/src/lib/pariprashna/pipeline/safety_gate.ts:107` carry the same guard on the
  API side.
- `platform/src/app/clients/[id]/samiksha/page.tsx:27` — a **fifth guard site**, added to
  this enumeration in the review-fix pass: the SAMĪKṢĀ review tab is flagged behind the
  same `PARIPRASHNA_ENABLED` check (`if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
  redirect(...) }`, verified live in the current worktree). An operator running the
  SECONDARY rollback (§3) also takes down this tab, not just the conversation surface —
  worth knowing before treating SECONDARY as narrowly scoped to "just the chat page."

Env override mechanism (`platform/src/lib/config/index.ts:14–27`): the `ConfigServiceImpl`
constructor reads `process.env['MARSYS_FLAG_PARIPRASHNA_ENABLED']` **once, at process
construction** — not per-request. This means a Cloud Run env-var change only takes effect
for **new revision instances**; it is not a live in-process toggle. Confirmed live: the
`amjis-web` service's current revision (`amjis-web-01671-47n`) carries
`MARSYS_FLAG_PARIPRASHNA_ENABLED=true` as a real env var on the container spec — set
out-of-band (it is **not** in `.github/workflows/deploy.yml`'s declared `env_vars` block
for the `amjis-web` deploy step, lines 445–459), and it has survived multiple subsequent
CI-driven deploys since (`amjis-web-01218-4ng` through tonight's `amjis-web-01671-47n`),
confirming Cloud Run env vars set outside the CI pipeline are **not** clobbered by later
CI deploys that don't reference them.

### 1.2 What "the flip" (P3-F) is, per the governing plan

Per `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md`
(P3-F lane description): **"PB-4 F-5 steps 1–2: default routing everywhere, flag retained
as the rollback lever, then seven consecutive green smokes."** This is corroborated by
`00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md` §1: *"PB-4 cutover (default flip,
consult retirement, flag deletion): NEVER RUN; consult/consume still the un-gated
default."* — and by `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:3209`:
*"PB-4 PŪRṆATĀ (cutover): NEVER RUN. No default flip, no consult retirement, no flag
deletion, no seven-smoke hold."*

Two things follow directly from this language:

1. **Flag deletion and consult retirement are explicitly OUT OF SCOPE for P3-F.** Those
   are PB-4 F-5 steps 3–4, which the charter assigns to **P4-A** (RETIRE train), gated
   separately on P3-F closing *and* the DD-1 feel-proxy battery going green
   (`PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md` §10.2, row `P4-A`). P3-F itself
   only changes *default routing* — it does not delete `/clients/[id]/consult` or
   `/api/chat/consult`, and it does not remove `PARIPRASHNA_ENABLED`.
2. **The plan's own words name `PARIPRASHNA_ENABLED` as "the rollback lever"** for the
   flip. That is the design intent this pin is built on: because
   `pariprashna/page.tsx:42–44` unconditionally honors this flag ahead of any
   default-routing logic the flip PR adds, flipping the flag back to `false` forces
   **every** path into `/clients/[id]/pariprashna` — however the flip PR gets users
   there (a changed dashboard link, a changed `router.push` target, a new redirect from
   `/consult` itself) — back out to `/clients/[id]/consult`. This makes the flag a
   mechanism-independent kill switch for the flip's user-facing effect, not just one of
   several equally-good options.

### 1.3 The current, hardcoded default-door call sites (what P3-F most likely touches)

As of tonight, the following are the concrete places a fresh session lands on `consult`
by default — the flip's most probable target surface, **not yet changed**:

- `platform/src/components/chat/ConversationSidebar.tsx:153,235` —
  `router.push(\`/clients/${chartId}/consume\`)` (the "new chat" / sidebar entry points).
- `platform/src/components/clients/EditClientForm.tsx:160` —
  `router.push(\`/clients/${chart.id}/nirmana\`)` (post-save landing).
- `platform/src/app/clients/[id]/page.tsx`, `platform/src/app/clients/[id]/panchang/page.tsx`,
  `platform/src/app/panchang/components/{AskMadhavLink,MuhuratResultsList,ActionBar}.tsx` —
  additional `consult`-pointing entry points found by a repo-wide grep for
  `clients/[id]/consult` references (not exhaustively line-cited here — this document
  is the rollback pin, not the flip's own gap enumeration, which is P3-D's DD-24 job).

---

## §2 — Honest gap: the flip's own diff does not exist yet

**I did not find a merged or in-flight PR that implements "default routing everywhere."**
P3-A through P3-E are not yet closed (P3-A/B/C/E are open lanes; P3-D has not started —
see the tracker), and per the phased plan, P3-F is "strictly last and strictly serial."
So there is no code today that changes §1.3's call sites, and no way to cite file:line
for a diff that has not been written.

**What this means for the rollback pin, stated plainly:** §3's PRIMARY rollback (traffic
split back to the pre-flip revision) is valid **regardless of what the eventual flip PR
contains**, because it reverts to the exact pre-flip container image, whatever that
image's routing logic turns out to be. §3's SECONDARY rollback (flip
`PARIPRASHNA_ENABLED` off) is valid **only if the flip PR does not introduce a second,
independent mechanism that bypasses this flag** — see §6 for the one thing a human must
confirm before the flip merges.

---

## §3 — The un-flip commands

Both commands target the **web door** (`amjis-web`), because "default routing" is a
web-UI routing concern; the flip does not touch `amjis-mcp` (the MCP door's `prashna_ask`
tool is not a "default surface" in the redirect sense — no rollback action is needed
there). All commands below use `--region=asia-south1` per the live service's configured
region (confirmed live, §4).

### PRIMARY — traffic-split rollback to the pre-flip revision (no rebuild, no env change)

```
gcloud run services update-traffic amjis-web \
  --to-revisions=<PRE_FLIP_REVISION>=100 \
  --region=asia-south1
```

- **What it does:** shifts 100% of `amjis-web` traffic to the named revision — the exact
  container image and env-var set that was serving immediately before the flip's
  post-shift smoke started. No image rebuild, no new revision created, no CI run. This
  is the same mechanism §5.3's "any red = automatic traffic rollback" already uses for
  every merge tonight — the flip gets no special-cased rollback path, it gets the
  standard one, which is the point.
- **`<PRE_FLIP_REVISION>`:** must be read fresh, at the moment of the flip, from the
  `campaign-coordination` announcement the flip step itself makes before merging
  (RUNBOOK_FLIP.md step 1: *"check what is on main → announce the revision tag"*) —
  **not** copied from §4 below, which is tonight's snapshot and will be stale by the
  time the flip runs on some future night.
- **New rule, added in the review-fix pass, and mandatory, not optional:** before
  shifting traffic to `<PRE_FLIP_REVISION>`, diff that candidate revision's env vars
  against the currently-serving revision's env vars (`gcloud run revisions describe
  <REVISION> --format=json`, both sides) and confirm **no `MARSYS_FLAG_*` safety flag is
  lost** by the rollback. This is not a hypothetical: tonight's own pin candidate,
  `amjis-web-01671-47n`, predates `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED` being armed in
  production (§4.1) — rolling back to it *right now* would silently disarm the $2/turn
  and $40/day spend ceilings and the per-user rate limits on both doors
  (`enforceTurnLimits` short-circuits to allowed when the flag is off —
  `platform/src/lib/limits/index.ts:53`), while the operator believes they only undid the
  flip. A revision can be the correct pre-flip image and still be an unsafe rollback
  target if a safety flag armed since then. This diff step is the check that catches
  that class of failure; skipping it is how a rollback command routes around a safety
  gate by accident.
- **Verified tonight (syntax + resource existence, not executed):**
  - Command shape matches `gcloud run services update-traffic --help`'s own documented
    rollback example verbatim: *"To rollback to revision myservice-cp9kw run: gcloud run
    services update-traffic myservice --to-revisions=myservice-cp9kw=100."*
    **SYNTAX-VERIFIED.**
  - The revision-name pattern is real: `gcloud run revisions list --service=amjis-web
    --region=asia-south1` (read-only, run live tonight) returned 10+ healthy
    (`status.conditions[0].status = True`) revisions, e.g. `amjis-web-01670-v8w`,
    `amjis-web-01669-dtr`, confirming both the naming convention and that Cloud Run
    retains multiple prior revisions rather than pruning aggressively.
    **DRY-RUN-VERIFIED** (resource existence confirmed by a live read, not executed as
    a traffic change).
  - Not verified: whether the *specific* pre-flip revision will still exist, unpruned,
    at actual flip time — that is inherent to "fresh read at the moment," not a gap in
    this pin.

### SECONDARY — flip `PARIPRASHNA_ENABLED` off (the plan's own designed lever)

Use this **only** if the PRIMARY's pre-flip revision has since been superseded by an
unrelated deploy you do not also want to revert (e.g., a P4 filler lane merged and
deployed after the flip, and traffic-rolling-back would also undo that unrelated,
good work). In that case a surgical flag flip undoes only the routing behavior.

```
gcloud run services update amjis-web \
  --region=asia-south1 \
  --update-env-vars=MARSYS_FLAG_PARIPRASHNA_ENABLED=false \
  --no-traffic \
  --tag=rollback-verify
```
then, after the verification in §5 passes against the tagged URL:
```
gcloud run services update-traffic amjis-web \
  --to-latest \
  --region=asia-south1
```

- **What it does:** deploys a new revision — **same container image, only the env var
  changes** — staged at 0% traffic first (mirrors the house no-traffic→smoke→promote
  pattern in `.github/workflows/deploy.yml:427–492`, the A-S8 step), then promotes it.
  This is an **env command that still requires a new revision deploy** — it is not a
  pure traffic command, which is exactly why PRIMARY is listed first. Per precondition
  6's own wording ("a ready traffic/env command"), both forms are anticipated; this is
  the "env" half.
- **`--update-env-vars` (not `--set-env-vars`), deliberately:** `--set-env-vars` replaces
  the **entire** env var set — `gcloud run services update --help` says so in its own
  words, verbatim: *"All existing environment variables will be removed first."* That is
  not a hazard scoped to the Paripraśna feature flags — it is a hazard to **every
  plain-value env var currently live on the service**. Corrected count (confirmed live
  tonight, on `amjis-web-01671-47n`, the exact revision this pin reads elsewhere):
  **64 total env entries** on the container spec, of which **44 are plain-value** and
  **11 are `valueFrom(secretKeyRef)`**. Of the 44 plain-value vars, **15 are
  `MARSYS_FLAG_*`**, and of those, **11 are `MARSYS_FLAG_PARIPRASHNA_*`** — not 13 as an
  earlier pass of this document miscounted. **The real casualty list of a `--set-env-vars`
  call is all 44 plain-value vars**, not ~12 feature flags: `DB_NAME`, `DB_USER`,
  `INSTANCE_CONNECTION_NAME`, `NODE_ENV`, `APP_URL`, `GCP_PROJECT`,
  `PYTHON_SIDECAR_URL`, `WATCHDOG_SECRET`, all six `NEXT_PUBLIC_FIREBASE_*` vars, and the
  rest of the plain-value set alongside the 15 `MARSYS_FLAG_*` vars — none of these are
  declared in `deploy.yml`, meaning they were all set the same out-of-band way and would
  ALL be destroyed by a `--set-env-vars` call that doesn't re-list every one of them
  (production DB connectivity and Firebase auth included, not just feature toggles).
  `--update-env-vars` merges, touching only the one key. **This is a real hazard a tired
  operator could hit under pressure — the entire production `amjis-web` runtime config,
  not a dozen feature flags — flagged here on purpose, and understated by roughly 4× in
  an earlier pass of this document.**
- **Verified tonight (syntax only, not executed):**
  - `gcloud run services update --help` confirms `--update-env-vars=KEY=VALUE,...` and
    `--no-traffic` are both real, independent flags on this command.
    **SYNTAX-VERIFIED.**
  - `MARSYS_FLAG_PARIPRASHNA_ENABLED=true` confirmed present on the live container spec
    tonight via `gcloud run services describe amjis-web --region=asia-south1
    --format=json` (read-only). **DRY-RUN-VERIFIED** (current state read; command not
    executed).
  - **Resolved (was "not verified" in an earlier pass): `--update-env-vars` cannot touch
    secret bindings.** `gcloud run services update --help`'s own command synopsis lists
    the env-var flags and the secret flags as two independent bracketed groups —
    `[--clear-env-vars | --env-vars-file | --set-env-vars | --remove-env-vars
    --update-env-vars]` and, separately, `[--clear-secrets | --set-secrets |
    --remove-secrets --update-secrets]` — confirming they are mutually exclusive flag
    families with no overlap, not merely "should not" affect each other. The service's
    11 `valueFrom(secretKeyRef)` entries (Firebase admin creds, DB password, and the
    provider/internal-token/cron/canary secrets) are addressed only via `--set-secrets`
    / `--update-secrets`, never via `--update-env-vars`. This was confirmed by reading
    the command's own `--help` text, not by executing anything against production — no
    credential operation was needed or performed to resolve it.

---

## §4 — The current known-good pin (captured live tonight, illustrative only)

Read live via `gcloud run services describe amjis-web --region=asia-south1 --format=json`
at **2026-08-22T22:38:41Z** (UTC, `date -u` at the moment of the read):

| Field | Value |
|---|---|
| `status.latestReadyRevisionName` | `<read fresh — see §3>` |
| `status.latestCreatedRevisionName` | `<read fresh — see §3>` |
| `status.traffic` | `[{revisionName: <read fresh — see §3>, percent: 100, latestRevision: true}]` |
| `status.url` | `https://amjis-web-qm256lasva-el.a.run.app` |
| `MARSYS_FLAG_PARIPRASHNA_ENABLED` (live env, current revision) | `true` |
| `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED` (live env, current revision) | **absent** (confirms precondition 3, limits enablement, has not run yet — consistent with tonight's park) |

**The literal revision name is deliberately not printed in this table**, per a
review-fix pass correction: it originally sat here, bordered and copy-paste-ready,
directly beneath the `<PRE_FLIP_REVISION>` placeholder in §3 — exactly the shape a tired
operator skims and pastes, ignoring the prose instruction next to it not to. §4.1 below
records why that would now be actively unsafe, not merely stale.

**This is NOT the pin to use at flip time.** It is captured here only to (a) prove the
read command works and returns exactly the shape §3 depends on, and (b) give the next
reader a concrete floor of what the *shape* of a clean read looks like. Whoever runs
the flip must re-run this exact `describe` command **immediately before merging the flip
PR** and use *that* revision name as `<PRE_FLIP_REVISION>` in §3's PRIMARY command — this
mirrors precondition 5's "lease re-read clean at the moment of the flip merge," applied
to the deploy side of the same flip.

### §4.1 — Revision drift since capture (added in the review-fix pass)

The reassurance this section originally carried — *"the service is in a clean,
single-revision, 100%-traffic steady state, nothing to disentangle"* — is **no longer
true** and has been removed above rather than left to mislead. Re-verified live at
**2026-08-22T23:10:41Z** UTC (`gcloud run services describe amjis-web` +
`gcloud run revisions describe`, both read-only): the pinned revision has moved twice
since tonight's original capture, and production now serves a **tagged** revision, not a
clean single-revision split:

| Revision | Role | `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED` |
|---|---|---|
| `amjis-web-01671-47n` | §4's original captured target (2026-08-22T22:38:41Z) | **absent** |
| `amjis-web-02826-huf` | the limits canary (carries `tag: limits-canary`) | `true` |
| `amjis-web-01673-665` | serving 100% of traffic **now** (after main's own deploy) | `true` |

**This is the concrete case the new §3 PRIMARY rule (the env-diff-before-shifting step)
exists to catch.** `amjis-web-01671-47n` is still a syntactically valid pre-flip image,
but the run enabled `PARIPRASHNA_LIMITS_ENABLED` in production tonight (native-authorized,
§0 ruling 3) *after* that revision was captured. Rolling back to
`amjis-web-01671-47n` now — even though nothing about §3's PRIMARY command changed —
would silently disarm the $2/turn and $40/day pre-dispatch spend ceilings and the
per-user rate limits on both doors (`platform/src/lib/limits/index.ts:53`), on top of
undoing the flip, and an operator watching only §5.1's structural traffic read would see
a clean 100%-on-target result with no indication anything else moved. §3's own
instruction to read `<PRE_FLIP_REVISION>` fresh rather than copy this section is what
already prevents an operator from literally pinning `amjis-web-01671-47n` by name; this
subsection exists so the *reason* that instruction matters is written down where the
next reader can see it, not just asserted.

---

## §5 — How to verify the rollback worked

Cloud Run reporting `traffic: 100%` on the target revision is **necessary but not
sufficient** — per §N.8, a status that only checks "did the API call succeed" rather
than "does the claimed behavior actually hold" is an unearned signal. Two checks, in
order:

**5.1 — Structural (Cloud Run's own declared state):**
```
gcloud run services describe amjis-web --region=asia-south1 \
  --format="value(status.traffic)"
```
Good: shows 100% on the rollback target revision (PRIMARY) or on the new flag-off
revision (SECONDARY). This can fail honestly — if the `update-traffic`/`update` call
errored or partially applied, this read shows a split or the wrong revision, not a
false green.

**5.2 — Functional, SECONDARY ONLY (the actual claim: does routing behavior differ, not
just process state):**

**PRIMARY currently has no functional detector — this is a correction from an earlier
pass of this document, which wrongly implied §5.2 covered both rollback paths.** The
check below distinguishes `PARIPRASHNA_ENABLED=true` from `PARIPRASHNA_ENABLED=false` —
that is SECONDARY's own mechanism, and SECONDARY's alone. PRIMARY does not touch this
flag at all: verified live tonight, `amjis-web-01671-47n` (this pin's §4 pre-flip
snapshot), `amjis-web-02826-huf` (the limits canary), and `amjis-web-01673-665` (the
revision serving production right now) **all carry
`MARSYS_FLAG_PARIPRASHNA_ENABLED=true`** — so a PRIMARY traffic-split rollback moves
traffic between revisions that share the same flag value, and the curl command below
returns the identical `307 → /login` result whether or not PRIMARY ever ran. **Do not use
§5.2 to judge whether a PRIMARY rollback worked.** The honest PRIMARY probe has to target
the flip's own changed surface (§1.3's default-door call sites — e.g. confirm the
dashboard/sidebar entry point the flip PR redirected now lands back on `/consult`), and
cannot be written concretely tonight because that diff does not exist yet (§2). Whoever
runs the flip must derive PRIMARY's functional check from the actual flip PR's diff
before treating §5.1's structural traffic read as sufficient evidence PRIMARY succeeded.

```
curl -sI -m 15 "https://amjis-web-qm256lasva-el.a.run.app/clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/pariprashna"
```
using the **synthetic chart only** (`1c826d5a-41cb-4450-b4dc-59d440e5f75a` — never the
native's real chart `482012f1-…`, per this run's hard-never).

- **Baseline captured live tonight** (flag ON, pre-rollback, current production state):
  `HTTP/2 307`, `location: /login`. This is `pariprashna/page.tsx`'s flag check passing
  (flag `true`) and falling through to the auth guard, which redirects an unauthenticated
  request to `/login` — proving the request reached *past* the flag check.
- **What "good" (SECONDARY rollback succeeded) looks like:** `HTTP/2 307`,
  `location: /clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/consult`. This is the flag
  check itself firing (`pariprashna/page.tsx:42–44`) — it runs **before** the auth guard,
  so this redirect is observable **without any credential**, exactly the kind of
  detector that can fail: if SECONDARY did not actually take effect (stale env var,
  traffic still on the wrong revision, cached process), this command keeps returning
  `location: /login` instead, and the difference is unambiguous, not a matter of
  interpretation.
- **What would make this check silently pass when SECONDARY failed:** nothing obvious
  within SECONDARY's own mechanism — the two locations (`/login` vs `/…/consult`) are
  textually distinct and the check requires no auth. The one real risk internal to
  SECONDARY is checking too early, before the new revision has finished receiving 100%
  traffic (Cloud Run traffic promotion is not instantaneous) — re-run after confirming
  §5.1's traffic split first, not concurrently with it. **An earlier pass of this
  document claimed, in this exact spot, "there's no plausible 'looks green either way'
  failure mode here" — stated without scoping to SECONDARY. That sentence was false as
  written: run this same check against a PRIMARY rollback and it "looks green" (or
  rather, looks like baseline) identically whether PRIMARY succeeded, failed, or was
  never run — because PRIMARY never changes the flag this check reads. That sentence has
  been deleted. A detector earning §N.8's green bar has to be demonstrated incapable of
  passing for the specific claim it is attached to, not merely incapable of passing for
  some mechanism resembling it.**

---

## §6 — One thing a human must confirm before the flip merges

**This is the one ambiguity this pin cannot close on its own, named per the task's own
instruction not to guess past it.**

§3's SECONDARY rollback (flag flip) is only a valid un-flip if the flip PR's
"default routing everywhere" change routes through the **existing**
`PARIPRASHNA_ENABLED` check and nothing else — i.e., it changes *where links point*
(§1.3's call sites), not *whether the pariprashna surface is reachable* (§1.1's guard).
That is what "flag retained as the rollback lever" in the phased plan implies, but since
the flip's diff does not exist yet (§2), nobody has confirmed the actual implementation
will honor that design intent rather than, say, adding a second flag or a
middleware-level rewrite that bypasses `pariprashna/page.tsx` entirely.

**Before the flip PR merges, whoever reviews it must confirm:** the diff does not
introduce a routing path to the Paripraśna surface that skips the
`configService.getFlag('PARIPRASHNA_ENABLED')` check at
`platform/src/app/clients/[id]/pariprashna/page.tsx:42–44` (or its API-route
equivalents). If it does, §3's SECONDARY command in this pin is void and must be
rewritten against the new mechanism before the flip is allowed to merge — this document
should be treated as blocking on that confirmation, not as a formality to skim.

§3's PRIMARY (traffic-split rollback) has no such dependency and remains valid
regardless of how the flip PR is implemented — it is the pin's fallback of last resort
if §6 cannot be confirmed in time.

---

## §7 — The one-line kill criterion

**Run §3's PRIMARY command the moment the post-flip smoke (RUNBOOK_FLIP.md step 2, the
demonstrated-can-fail battery against the live default route) reports red, or the
moment either door's live post-flip probe (RUNBOOK_FLIP.md step 3) shows a user reaching
`/clients/[id]/pariprashna` by default without the safety gate, limits, or receipt
machinery active** — do not wait for a second opinion or a repeat run; per
`RUNBOOK_FLIP.md`'s own failure handling, "post-flip smoke red after auto-rollback →
rollback, then HALT. Do not retry the flip tonight."
