---
artifact: P3E_PARK_RECORD
canonical_id: P3E_PARK_RECORD
version: 1.0
status: PARKED — awaiting one operator credential action by the native
lane: P3-E (post-deploy behaviour smoke)
authored: 2026-08-23 (DIAGNOSTICIAN, Paripraśna P3+P4 overnight run)
authority: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §4 / §6 / §9;
  NATIVE-SURROGATE park ruling relayed by the CONDUCTOR 2026-08-23.
---

# P3-E — park record

## 1. State in one line

**The lane's assertion layer is built, proven can-fail per-assertion in real CI, and merged-ready.
Its live transport is blocked by a misconfigured GitHub Actions secret that no agent in this run
may repair. `behaviour-smoke` has never completed a single turn; the green×7 counter stands at
0 and has never started.**

## 2. Root cause (settled, two independent reads agreeing)

`platform/scripts/probe/ask.ts:195` — `const creds = JSON.parse(credsRaw)` inside
`mintSessionCookie` — threw `SyntaxError: No number after minus sign in JSON at position 1` on
every run.

The value handed to it is the GitHub Actions **repo** secret `FIREBASE_ADMIN_CREDENTIALS`.
A shape-only diagnostic (byte length + brace prefix, never content) on CI runs
**32600417256** and **32601926862** reported verbatim:

```
[p3-e-smoke] FIREBASE_ADMIN_CREDENTIALS length=1 chars; does NOT start with '{' (does not look like a JSON object)
```

One character, not starting with `{`. `JSON.parse('-')` reproduces the observed error exactly.
It is not a PEM, not truncated JSON, not base64 — there is no credential material in it at all,
so **no code change in `ask.ts` can accept it**. The CONDUCTOR's independent `gh secret list`
read confirms the secret exists and was created 2026-05-18 and never corrected.

**Why nothing caught it for three months:** no workflow in this repo had ever consumed the
GitHub secret. `deploy.yml` binds the real credential from **Secret Manager**, via Cloud Run's
`--set-secrets FIREBASE_ADMIN_CREDENTIALS=firebase-admin-credentials:1` (deploy.yml:468). The
GitHub secret was write-only dead weight. This workflow is its first consumer.

**Production is unaffected.** Cloud Run reads `firebase-admin-credentials:1` from Secret Manager
directly and always has. Only this new CI smoke consumes the GitHub secret.

**The GCP-side fallback is closed, not merely unused.** `ask.ts`'s `envOrSecret` would fall back
to `gcloud secrets versions access` if the env var were unset — but the CI WIF identity
`github-actions@madhav-astrology.iam.gserviceaccount.com` holds **no** secretmanager role at
either resource or project level (verified read-only 2026-08-23:
`gcloud secrets get-iam-policy firebase-admin-credentials` grants `roles/secretmanager.secretAccessor`
to `938361928218-compute@developer.gserviceaccount.com` only; the project IAM policy grants
`github-actions@` only artifactregistry.writer / cloudsql.client / iam.serviceAccountUser /
run.developer).

## 3. Why this is PARKED and not fixed

Both available repairs are credential operations:

- (a) re-upload the GitHub secret from Secret Manager, or
- (b) grant the CI service account `secretmanager.secretAccessor` on a **production admin
  credential**.

Charter §9 hard-never ("Never destructive migrations, credential operations, or budget
self-raises") and §3.3 MUST-PARK both forbid these to every agent in the run, surrogate included.
The NATIVE-SURROGATE ruled the lane PARKED for the native's morning.

**No assertion was weakened, removed, or loosened to reach a green.** That was the alternative
and it was refused: this smoke stands in front of THE FLIP (P3-F) and, downstream, the
irreversible P4-B retirement deletion. A smoke of unknown sensitivity in front of those is worse
than no smoke.

## 4. The one-command morning action (operator only)

```
gcloud secrets versions access 1 --secret=firebase-admin-credentials --project=madhav-astrology \
  | gh secret set FIREBASE_ADMIN_CREDENTIALS --repo Marsys-Technologies/Madhav
```

Verified read-only 2026-08-23 that the source is sound: `firebase-admin-credentials:1` holds a
2369-byte value beginning with `{` — a real service-account JSON. Its content was never printed,
logged, written to disk, or committed anywhere in this run.

Then:

```
gh workflow run pariprashna-post-deploy-smoke.yml
```

and confirm the `behaviour-smoke` job green before the green×7 cadence is considered started.
The workflow's preflight now shape-checks the secret, so a still-wrong value fails with
`MISCONFIGURED SECRET, not an engine failure` and the repair command inline, rather than an
opaque `JSON.parse` stack trace.

## 5. Resume state

| | |
|---|---|
| Branch | `pariprashna/p3-e` (pushed) |
| PR | [#1494](https://github.com/Marsys-Technologies/Madhav/pull/1494) — OPEN, not merged (INTEGRATOR merges) |
| Green×7 counter | **0. Never started.** |
| Live greens ever produced | **0.** `behaviour-smoke` has never completed a turn. |
| Blocking action | §4 above — native only |
| Next command after the credential lands | `gh workflow run pariprashna-post-deploy-smoke.yml` |
| Downstream | THE FLIP (P3-F) parks; P4-B deletion parks (both gated on green×7) |

## 6. What IS proven, and the exact boundary of the claim

CI run [32602015352](https://github.com/Marsys-Technologies/Madhav/actions/runs/32602015352),
job `Assertion self-test (fixtures, no live turn — NOT countable toward green×7)`: **SUCCESS**.

- **Pass 1 (true-negative):** a REAL captured production turn record (`FIXTURE_GOOD`, from a live
  turn on the synthetic chart `1c826d5a`) passes all 11 assertions.
- **Pass 2 (per-assertion can-fail):** 9 targeted mutations, one per mutable assertion; each made
  its targeted assertion go false while every other assertion held its `FIXTURE_GOOD` value.
  Verbatim: *"SELFTEST PASS — GOOD fixture all-pass, and all 9 targeted mutations produced an
  isolated, legible failure of exactly the assertion they targeted."* Every result carried
  `"targeted_assertion_went_false": true` and `"all_other_assertions_as_expected": true`.
- The one structurally-coupled co-failure (`receipt_define_present` necessarily also takes down
  `facts_consumed_non_empty`, which reads a field inside the receipt payload) is **declared**
  in `EXPECTED_COUPLED_FAILURES` and required to fire, not silently tolerated.
- The selftest is itself demonstrated-can-fail: replacing one mutator with a no-op locally
  produced `"targeted_assertion_went_false": false` → `SELFTEST FAIL`, exit 1.

**The boundary, stated so it cannot become a loophole:** this proves ONLY that the assertion
layer can fail, per-assertion and legibly. It observes nothing about the deployed revision. It
does **not** start the DD-7 / W-1 counter and does **not** count as a green. No green counts
until one real, live, CI-produced `behaviour-smoke` green exists. Its value is that when the
credential lands, the very first live green counts immediately rather than costing another
45-minute cycle to earn its can-fail evidence.

F-N3 stands unamended: every red so far is a transport failure, not a behavioural one.

## 7. Candidate DD entry — "a fact asserted about an unreadable secret"

The P3-E workflow's own original header asserted:

> "FIREBASE_ADMIN_CREDENTIALS + NEXT_PUBLIC_FIREBASE_API_KEY are already-provisioned GitHub
> Actions repo secrets (added 2026-05-18 / earlier) — the exact two values `probe/ask.ts` needs"

That assertion was made about a value its author **could not read** (GitHub secrets are
write-only), and it was **false**. This is CLAUDE.md §N.8's Earned-Signal defect in documentation
form: a confident status claim ("already-provisioned, the exact values needed") with no detector
behind it that could ever have reported false. The correct form of the claim was "the secret
*names* exist; whether they hold usable values is unverified until a job consumes them."

**Generalisation worth registering:** any documentation or code comment asserting the *content* or
*fitness* of a write-only secret is unearned by construction. The only earnable claims are
(a) the secret name exists, and (b) a job that consumed it succeeded. Anything stronger needs a
runtime shape check — which is what this lane's preflight now is.

Corrected in place by commit `535caa34c`: the header now states the observed shape, cites the CI
run that observed it, and says plainly that the job cannot pass until an operator repairs it.
