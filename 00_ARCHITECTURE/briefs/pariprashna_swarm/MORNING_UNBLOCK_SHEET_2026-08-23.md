# MORNING UNBLOCK SHEET — Paripraśna P3+P4 overnight run, 2026-08-23

**Read this first. It is one page and it is the whole point of the night.**

The run reached **end state 5 (PARTIAL, CLEAN)**. THE FLIP did not fire. It did not fire for exactly
one reason, and that reason takes about a minute to fix.

---

## The one thing blocking everything

The GitHub Actions repo secret **`FIREBASE_ADMIN_CREDENTIALS` contains a single character: `-`.**

It was created 2026-05-18 and never corrected. Confirmed three independent ways: the P3-E workflow's
own shape diagnostic (`length=1 chars; does NOT start with '{'`), the exact `JSON.parse` error it
produces (`No number after minus sign in JSON at position 1`, reproducible with
`node -e 'JSON.parse("-")'`), and `gh secret list`.

**Consequence:** `platform/scripts/probe/ask.ts` dies in `mintSessionCookie` before it can
authenticate, so the post-deploy behaviour smoke has **never completed a single turn**. Every red it
has ever produced is a transport failure with **zero behaviour assertions evaluated** — which is why
none of them was banked as can-fail evidence.

**Why the whole night hangs off it:** the smoke's green×7 counter gates *two* things — THE FLIP (§4
Wave P3-4 precondition 2) and the **irreversible P4-B deletion** (§10.3 DD-4 precondition 2). No
counter, no flip; no flip, no retirement train, and P4-E and P4-F never open either.

**Production is unaffected.** Cloud Run binds `firebase-admin-credentials:1` from Secret Manager
directly. Only the CI smoke consumes the GitHub secret.

### Why no agent fixed it

Every available repair is a credential operation — a §9 hard-never and a §3.3 MUST-PARK for this run.
The NATIVE-SURROGATE parked it deliberately rather than reaching for it (ledger **D-006**), and
recorded that it is *your* decision, not its own.

---

## Your options — narrower one first, neither chosen for you

**Option A (recommended by the surrogate, not decided).** Upload the value that already exists in
Secret Manager into the GitHub repo secret. No rotation, no new material, no IAM change — the same
credential Cloud Run already runs on, made visible to CI.

```bash
gcloud secrets versions access 1 --secret=firebase-admin-credentials \
  | gh secret set FIREBASE_ADMIN_CREDENTIALS --repo Marsys-Technologies/Madhav
```

*Verified by the run, metadata only — no secret value was read, printed, or stored anywhere:*
`gcloud secrets list` confirms **`firebase-admin-credentials` exists** (created 2026-04-25T17:42:45)
and `gcloud secrets versions list` confirms **version `1` is `enabled`** (2026-04-25T17:42:52). So the
command above names a real secret and a real, live version. **The run did not execute it** — that is
the credential operation it was forbidden to perform, and it is deliberately left for you.

**Option B (wider — flagged as the worse choice, but yours to weigh).** Grant the CI Workload
Identity service account `roles/secretmanager.secretAccessor` on `firebase-admin-credentials` and add
a `google-github-actions/auth` step, so `ask.ts`'s existing Secret Manager fallback resolves in CI.
This **permanently broadens which principal can read a production admin credential.**

**Option A-prime (a diagnosis, not a recommendation — but you should know it exists).** The
placeholder is strictly *worse* than an absent secret. `ask.ts:160-170`:

```ts
const fromEnv = process.env[envVar]
if (fromEnv) return fromEnv                      // '-' is truthy, so this returns '-'
console.error(`[ask] ${envVar} not set — fetching Secret Manager:${secretName} ...`)
```

**The one-character value short-circuits the Secret Manager fallback that was designed to save this
exact case.** That is why production is fine (it binds `firebase-admin-credentials:1` directly and
never consults the GitHub secret) and CI is not. So *deleting* the GitHub secret would let `ask.ts`
fall through to `gcloud secrets versions access latest`. Whether that then succeeds depends on the CI
identity holding `roles/secretmanager.secretAccessor`, which the run believes it does **not** — the
run read the workflow's assertion of the IAM policy but did not independently re-read the live policy.
**Offered so you can check it in one command, not as a recommended path.**

---

## After you unblock it — the sequence, in order

```bash
# 1. Prove the smoke can now complete a turn. One run, watch it go green.
gh workflow run "Paripraśna Post-Deploy Behaviour Smoke (P3-E / PB-4 F-6)"
gh run watch "$(gh run list --workflow='Paripraśna Post-Deploy Behaviour Smoke (P3-E / PB-4 F-6)' \
  --limit 1 --json databaseId --jq '.[0].databaseId')"

# 2. Start the cadence. Seven consecutive greens, 45 minutes apart. ~4.5-5.25 hours.
#    The counter is read from CI history at the moment of the flip commit — never from a document.
```

**Then the flip's remaining preconditions.** The run drove these from six down toward one so that this
is all that is left:

| # | Precondition | State this morning |
|---|---|---|
| 1 | P3-A/B/C/D/E closed with DD-21 artifacts | **partial** — see the report's lane table |
| 2 | green×7 on the cadence, CI history the declarer | **BLOCKED — this sheet** |
| 3 | limits enabled and verified live | see surrogate ruling on `PARIPRASHNA_LIMITS_ENABLED` |
| 4 | three independent refuters clear flip readiness | not yet run — needs 1 and 2 first |
| 5 | lease re-read clean at the flip merge | trivial, do it at the moment |
| 6 | rollback pin committed **before** the flip commit | **pre-positioned overnight** — `P3F_FLIP_ROLLBACK_PIN_v1_0.md` |

---

## Three rules the run bound itself to, which still bind after you unblock it

These are recorded so that a tired morning does not undo a careful night.

1. **The 45-minute cadence may not be compressed.** Not by shorter intervals, not by concurrent
   dispatches, not to beat a deadline. The smoke samples the deployed revision *across time*; seven
   rapid-fire runs against one warm instance are **one observation wearing seven hats**, and they
   would miss exactly the intermittent and warm-up-dependent regressions the cadence exists to catch.
2. **No substitute for green×7 is acceptable** — not a smoke with the failing assertion removed, not
   a locally-run green, not a manually-attested one, not the existing reds re-read as evidence. The
   same counter gates a code-tree deletion.
3. **Any red resets the counter to zero** (W-1), including a red later understood to be unrelated.

---

## Before you roll anything back — the pin's recorded revision is stale

`P3F_FLIP_ROLLBACK_PIN_v1_0.md` records **`amjis-web-01671-47n`** as the known-good rollback target.
**That revision predates the limits enable.** The serving revision moved twice overnight:

```
amjis-web-01671-47n   <- the pin's recorded value (PRE-limits)
amjis-web-02826-huf   <- the limits canary this run shifted to
amjis-web-01673-665   <- serving now, after main's own deploy
```

**Rolling back to `01671-47n` would un-flip AND silently disarm the spend caps** — reverting a
native-authorized change nobody asked to revert. The pin correctly labels its value *"illustrative
only, re-read fresh at flip time"*, and that instruction is what saves it — but read the live value,
do not read the page:

```bash
gcloud run services describe amjis-web --region=asia-south1 \
  --format='value(status.traffic[0].revisionName)'
```

Verified good as of this writing: `amjis-web-01673-665` serves 100%, carries
`MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED=true`, and survived a real deploy from `main`.

---

## The other thing that needs your decision today

**Migrations 588 and 589 are applied to the production database with no rows in
`_migrations_applied`.** Both sit untracked in the shared checkout. They are NIRMĀṆA ELEVATION's
work, carrying the header *"Native instruction, 2026-08-23"*, and they **removed per-asset build
protection triggers** — 589 exists because 588's own `DROP FUNCTION` statements were, by its own
admission, *"guessed from the trigger names, not read from migrations 540/566"* and no-oped.

The run **did not touch them** — reconciling another campaign's audit trail is outside its authority
(ledger **D-009**). It took exactly one precaution: a byte-preserving read-only copy to
`/Users/Dev/pariprashna_night/run/salvage/`, with sha256 recorded, so a routine `git clean` cannot
destroy the only record of SQL whose effect is live.

**Check NIRMĀṆA's own record first** — it may already own this disposition. If it does not:

```bash
psql "$DATABASE_URL" -c \
  "SELECT id, filename, applied_at FROM _migrations_applied WHERE filename LIKE '58%' ORDER BY id;"
```

Then decide, and this is the part no command can make for you: **backfill the two rows** (which
asserts they went through the tracked path — they did not), **or record them as out-of-band operator
changes** pointing at the campaign that made them. The second is the honest option.

---

## Work that deliberately did NOT reach `main` — where to find it

Two lanes were parked on rulings, so their branches carry real artifacts that are **not** on `main`.
They are pushed and safe; you just won't find them by looking at `main`.

**`pariprashna/p4-h`** (PR #1496, parked) carries:
- **DD-28 / DD-29 / DD-30** in the swarm register — the two turn writers replacing `metadata_json`
  wholesale; `writeConversationMessages` reporting `verified: true` while destroying it; and the
  dedicated-`conversation_disputes`-table design note (recorded, **explicitly not built** — your call).
- **A quarantined regression test that already reads red**,
  `feedback_dispute_survives_turn.db.test.ts`, `it.skip` with the blocker named in its skip reason.
  Un-skip it, fix the two writers to merge rather than replace `metadata_json`, and it goes green.
  **The detector exists before the fix does — which is the order this campaign kept getting backwards.**

Because those three DD numbers live on a branch, **the run's own governance write started at DD-31**
to avoid colliding with them. **Do not renumber them when you merge that branch.**

**`pariprashna/p4-g`** (PR #1500, parked) carries the server half of the window-opening ask — a
DB-verified fire guard, deterministic composition, and a working SSE event — with three findings on
the PR: the write-time re-verification is weaker than the read-time one (a not-yet-closed window was
recorded as `happened`), the ask re-fires every turn with no exit, and **the dispute answer reaches
nothing at all**. Its flag ships OFF, so none of this is live.

*Resume commands for both are in the decision ledger.*

---

*Every claim on this page was verified by the run, not assumed. Where something was not verified, the
morning report says so in the same sentence as the claim.*
