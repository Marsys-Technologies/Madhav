---
phase: A.3
title: Environment Variables Audit
status: COMPLETE
executed_at: 2026-04-28
executor: Claude Code (Sonnet 4.6)
verdict: AMBER — 3 silent-failure risks found; 2 minor gaps
addenda:
  - date: 2026-08-23
    by: "Nirmāṇa KĀRAKA-M0-T59 (Standing Queue SQ-23, from ADHIKĀRIN D-49 / PARĪKṢAKA V-28 residual R-28.1)"
    what: "Added IMPORT_ONLY to the matrix and Addendum A3.4. The April 2026 audit's own scope, verdict and findings A3.1–A3.3 are UNCHANGED — this is an append, not a re-audit."
---

# A.3 — Environment Variables Audit

## Full Matrix

| Env Var | Code reads? | .env.example | .env.local | Prod (Cloud Run) | Finding |
|---|---|---|---|---|---|
| ANTHROPIC_API_KEY | ✅ | ✅ | ✅ | ✅ (secret) | OK |
| BUILD_STATE_GCS_BASE | ✅ | ❌ | ❌ | ❌ | ⚠️ Uses code fallback default |
| DATABASE_URL | ✅ | ✅ | ✅ | ❌ | OK (prod uses DB_USER+DB_PASSWORD+INSTANCE) |
| DB_NAME | ✅ | ✅ | ✅ | ✅ | OK |
| DB_PASSWORD | ✅ | ✅ | ❌ | ✅ (secret) | ⚠️ Not standalone in .env.local; dev reads it embedded in DATABASE_URL |
| DB_USER | ✅ | ✅ | ✅ | ✅ | OK |
| DEEPSEEK_API_KEY | ✅ | ✅ | ✅ | ✅ (secret) | OK |
| FIREBASE_ADMIN_CREDENTIALS | ✅ | ✅ | ✅ | ✅ (secret) | OK |
| GCP_PROJECT | ✅ | ✅ | ✅ | ✅ | OK |
| GCS_BUCKET_CHAT_ATTACHMENTS | ✅ | ❌ | ❌ | ✅ | ❌ **DEV GAP** — runtime failure if storage called in dev |
| GCS_BUCKET_CHART_DOCUMENTS | ✅ | ❌ | ❌ | ✅ | ❌ **DEV GAP** — runtime failure if storage called in dev |
| GOOGLE_GENERATIVE_AI_API_KEY | ✅ (via AI SDK) | ✅ | ✅ | ✅ (secret) | OK |
| IMPORT_ONLY | ✅ (2 CI gate CLIs) | ❌ **must stay absent** | ❌ **must stay absent** | ❌ **must stay absent** | ⚠️ **CI-only opt-out sentinel, added 2026-08-23 — see Addendum A3.4.** Set only in-process by two vitest files. Setting it in any ambient environment silences both gates |
| INSTANCE_CONNECTION_NAME | ✅ | ✅ | ✅ | ✅ | OK |
| NEXT_PUBLIC_FIREBASE_* (6 vars) | ✅ | ✅ | ✅ | ✅ | OK |
| NEXT_PUBLIC_SIDECAR_URL | ✅ | ❌ | ❌ | ❌ | ⚠️ Code defaults to `http://localhost:8000` — acceptable for dev; prod uses PYTHON_SIDECAR_URL (server-side only) |
| NODE_ENV | ✅ | — | — | ✅ | OK (set by framework) |
| OPENAI_API_KEY | ✅ (via @ai-sdk/openai) | ✅ | ❌ | ❌ | ❌ Missing — panel mode blocked (see A.1) |
| PYTHON_SIDECAR_API_KEY | ✅ | ✅ | ✅ | ✅ (secret) | OK |
| PYTHON_SIDECAR_URL | ✅ | ❌ | ✅ | ✅ | OK |
| SIDECAR_API_KEY | ✅ | ❌ | ❌ | ❌ | ❌ **SILENT BUG** — see below |
| SUPER_ADMIN_EMAIL | ✅ | ✅ | ✅ | ✅ (secret) | OK |
| VERTEX_AI_LOCATION | ✅ | ❌ | ✅ | ❌ | ⚠️ Prod defaults to us-central1; instance is asia-south1 |

## Critical Findings

### FINDING A3.1 — SIDECAR_API_KEY (SILENT BUG, MEDIUM PRIORITY)
**File:** `platform/src/lib/rag/routerClient.ts:29`, `retrieveClient.ts:30`, `synthesizeClient.ts:34`

Code reads `process.env.SIDECAR_API_KEY` (without `PYTHON_` prefix) with `?? ""` fallback. This is a **different key name** from `PYTHON_SIDECAR_API_KEY` which is what the sidecar checks.

Result: rag pipeline clients (`routerClient`, `retrieveClient`, `synthesizeClient`) make all requests to the Python sidecar **without authentication** (`x-api-key` header is empty string → header omitted). The sidecar may accept unauthenticated requests in dev, masking the bug. In prod, unauthenticated sidecar calls fail or bypass auth.

**Fix:** Either rename env var in .env.local + prod to `SIDECAR_API_KEY`, or align the code to read `PYTHON_SIDECAR_API_KEY` consistently. The latter is preferred (avoids a new env var in prod).

### FINDING A3.2 — GCS_BUCKET_* missing from dev (LOW-MEDIUM PRIORITY)
Code at `platform/src/lib/storage/client.ts:11,15` uses `process.env.GCS_BUCKET_CHAT_ATTACHMENTS!` with non-null assertion. In dev, this is `undefined` — any call to `getChatAttachmentsBucket()` or `getChartDocumentsBucket()` will throw.

**Fix:** Add to `.env.local` and `.env.example`:
```
GCS_BUCKET_CHAT_ATTACHMENTS=madhav-astrology-chat-attachments
GCS_BUCKET_CHART_DOCUMENTS=madhav-astrology-chart-documents
```

### FINDING A3.3 — VERTEX_AI_LOCATION not in prod (LOW PRIORITY)
Prod Cloud Run env does not set `VERTEX_AI_LOCATION`. Code at `vector_search.ts` reads this var; if absent, Vertex AI client may default to `us-central1` instead of `asia-south1` where the instance lives. Higher latency.

**Fix:** Add `VERTEX_AI_LOCATION=asia-south1` to Cloud Run service env (or set as secret).

## Deprecated vars present in .env.local
- `ASTROLOGER_EMAIL` — in .env.local but not in .env.example or code; likely remnant from earlier phase. Low priority cleanup.

---

# Addendum A3.4 — `IMPORT_ONLY` (added 2026-08-23, after the A.3 audit closed)

> **Provenance.** Nirmāṇa autonomous campaign, work-queue item `M0-T59`, Standing Queue `SQ-23`.
> The variable was introduced by `M0-T50` (commit `666cdc3f7`) under ADHIKĀRIN ruling `D-49`,
> repairing PARĪKṢAKA residual `R-28.1` from verdict `V-28`; the repair was certified at `V-36`.
> `M0-T50` named `IMPORT_ONLY` "a brand new env contract with no prior art" and flagged its own
> absence from this file as a loose end. This addendum closes that.
>
> **This addendum documents. It does not detect.** See §A3.4.6 — nothing in CI reads this file.

## A3.4.1 — What it is

`IMPORT_ONLY` is a **CI-only, test-only opt-out sentinel**. It is not an application variable. It
is never set in `.env.example`, `.env.local`, Cloud Run, Terraform, or any GitHub Actions workflow,
and it must stay that way (§A3.4.5, INV-1).

Its sole function is to let a test file `import` a CI gate module for its exported pure functions
**without the module's CLI firing on import**.

| | |
|---|---|
| **Meaning of `'1'`** | *Do not run the CLI.* The module is being loaded for its exports only. |
| **Meaning of anything else** | *Run the CLI.* Unset, `''`, `'0'`, `'true'`, `'yes'` — all run it. |
| **Comparison** | Strict string equality against `'1'`: `process.env.IMPORT_ONLY !== '1'`. There is no truthiness coercion, no `'0'`/`'false'` parsing, and no shared helper. |
| **Default when unset** | **RUN.** This is the entire point of the contract — see §A3.4.3. |

## A3.4.2 — What sets it and what reads it (measured 2026-08-23, not assumed)

```
$ git grep -l 'IMPORT_ONLY' -- .                     # tracked files, whole repo
platform/scripts/__tests__/dispatch_gate.test.ts
platform/scripts/__tests__/verify_migrations_deployed.test.ts
platform/scripts/ci/dispatch_gate.ts
platform/scripts/ci/verify_migrations_deployed.ts
(+ 00_ARCHITECTURE/autonomy/state/*.jsonl and 00_ARCHITECTURE/control/nirmana_tracker.html —
   Nirmāṇa campaign bookkeeping, not code)

$ grep -rln 'IMPORT_ONLY' --include='.env*' --include='*.yml' --include='*.yaml' --include='*.tf' .
(no matches — nothing in .github/, no env file, no Terraform)
```

**Readers — exactly two, both entrypoint guards on CI gate CLIs:**

| File | Line | Guard |
|---|---|---|
| `platform/scripts/ci/dispatch_gate.ts` | 193 | `if (process.env.IMPORT_ONLY !== '1') { main() }` |
| `platform/scripts/ci/verify_migrations_deployed.ts` | 252 | `if (process.env.IMPORT_ONLY !== '1') { main() }` |

**Setters — exactly two, both in-process, in the test files that import those modules:**

| File | Line | How |
|---|---|---|
| `platform/scripts/__tests__/dispatch_gate.test.ts` | 12–14 | `vi.hoisted(() => { process.env.IMPORT_ONLY = '1' })` |
| `platform/scripts/__tests__/verify_migrations_deployed.test.ts` | 33–35 | `vi.hoisted(() => { process.env.IMPORT_ONLY = '1' })` |

`vi.hoisted` is required, not stylistic: vitest lifts it above the static `import` block, so the
sentinel is set *before* the gate module is evaluated. A plain top-level assignment would run after
the import and be too late. (§A3.4.7 records the open question about this.)

**Three places deliberately *clear* it**, because those cases spawn the real CLI as a child process
and `{ ...process.env }` would otherwise hand the parent's opt-out to the child:

- `dispatch_gate.test.ts:249` — `runGate({ NODE_ENV: 'test', IMPORT_ONLY: '' })`
- `verify_migrations_deployed.test.ts:279` and `:327` — same pattern

## A3.4.3 — Why a gate's entrypoint is keyed on an explicit opt-out, not on `NODE_ENV`

This is the load-bearing part of the contract and the part most likely to be "tidied" away by a
future editor who recognises the `NODE_ENV !== 'test'` idiom and does not recognise why it is absent.

**What it replaced.** Both files previously ended with:

```ts
if (process.env.NODE_ENV !== 'test') { main() }
```

That makes **non-execution the default** in any environment that happens to export `NODE_ENV=test`.
`.github/workflows/ci.yml` already sets job-level `NODE_ENV: test` on three jobs — `unit-tests`
(line 137), `db-integration-tests` (219) and `planner-regression` (410) — and those jobs are the
natural home for a check like these. PARĪKṢAKA ran the consequence directly at `V-28`:

```
$ DATABASE_URL=… NODE_ENV=test npx tsx scripts/ci/verify_migrations_deployed.ts
exit 0 — no stdout, no stderr
```

A migration-drift gate returning green without ever comparing disk against `_migrations_applied`
is CLAUDE.md §N.8's exact defect: a signal with no detector behind it, and nothing saying so. The
trap was pre-laid at the destination and would have armed itself the moment someone did the obvious
right thing.

**Why not `NODE_ENV`, stated as a principle.** `NODE_ENV` is set *incidentally*, by frameworks and
CI, for reasons that have nothing to do with these gates. A gate must never be silenced as a side
effect of an unrelated decision. `IMPORT_ONLY` exists for exactly one purpose and is set by exactly
one kind of caller, so silencing a gate becomes a deliberate, greppable act.

**Why not the `isDirectEntrypoint()` idiom this same campaign used elsewhere.** This is the
asymmetry, and it is intentional:

| Module | Hazard | Safe default | Guard |
|---|---|---|---|
| `scripts/migrate.ts` | **Running** when it should not — it mutates production on import | DO NOT RUN | `isDirectEntrypoint(import.meta.url, process.argv[1])` (M0-T11, finding F-2 / ruling D-9) |
| `scripts/seed/asset_registry_seed.ts` | same | DO NOT RUN | same idiom (M0-T15) |
| `scripts/ci/dispatch_gate.ts` | **Failing to run** — a gate that does not run reports a pass nothing checked | **RUN** | `IMPORT_ONLY !== '1'` (M0-T50) |
| `scripts/ci/verify_migrations_deployed.ts` | same | **RUN** | same (M0-T50) |

A mutating script and a gate have *opposite* hazard directions, so they get opposite defaults. An
entrypoint check is **silent whenever the module is loaded any way other than directly** — which is
precisely the silent-pass class this repair removes, merely re-keyed from an env var onto the load
path. This campaign had already twice repaired an entrypoint guard that resolved wrongly, so using
one on a gate would have reintroduced the defect in a new costume. PARĪKṢAKA attacked this argument
at `V-36` angle A5 expecting it to be the weaker choice and concluded it is not.

**Direction of change.** Strengthening: something that silently passed now runs; nothing that failed
now passes. The behavioural evidence PARĪKṢAKA re-ran itself at `V-36` (six cases, its own runs):

| Invocation | Exit | Bytes of output |
|---|---|---|
| `dispatch_gate`, `NODE_ENV=test`, must-BLOCK input | 1 | 983 (`::error title=Manual dispatch blocked`) |
| same, plus `IMPORT_ONLY=1` | 0 | 0 |
| `dispatch_gate`, must-ALLOW input | 0 | 137 (`[dispatch-gate] ci-green: …`) |
| `verify_migrations_deployed`, `NODE_ENV=test`, unreachable DB | 2 | 854 (`NOT CHECKABLE`) |
| same, plus `IMPORT_ONLY=1` | 0 | 0 |

Note the third row: an **earned** exit 0 is distinguishable from a **silent** one by its output.
That property is what the old guard destroyed.

## A3.4.4 — Operator rules

1. **Never set `IMPORT_ONLY` in an environment.** Not in `.env.example`, `.env.local`, a Cloud Run
   service, Terraform, a `Dockerfile`, or a workflow's `env:` block at any level. Setting it
   ambiently silences both gates everywhere, by exactly the route `NODE_ENV` used to.
2. **Setting it is in-process and per-caller.** A test that needs the pure exports sets it in
   `vi.hoisted` before its imports. Nothing else should ever set it.
3. **Clear it for child processes.** Any code that spawns one of these CLIs from a process that set
   the sentinel must pass `IMPORT_ONLY: ''` in the child env, or the child inherits the opt-out and
   the assertion tests nothing.
4. **If you add a third CI gate CLI, use this contract, not `NODE_ENV` and not `isDirectEntrypoint`**
   — and add it to §A3.4.2's reader table.
5. **A worker or a mutating script is not a gate.** Its safe default is DO NOT RUN and it should use
   `isDirectEntrypoint()`. `platform/scripts/pariprashna/ledger_writer_worker.ts` **was repaired to
   `isDirectEntrypoint()` by M0-T60 (commit `27769a74e`, SQ-24), not to `IMPORT_ONLY`** — and the
   re-derivation is why. M0-T60 measured the old guard wrong in *both* directions: under
   `NODE_ENV=test` a direct run exited 0 with zero bytes (a silent no-op a scheduler records as
   success), and a **side-effect `import` ran `main()`**, opened the pool holding the system's only
   `role_ledger_write` credential, and `process.exit(1)` killed the importer. `IMPORT_ONLY` — whose
   safe default is RUN on any load — would have closed the first and left the second wide open.
   The hazard, not the shape of the neighbouring fix, decides which contract applies.
   *(Corrected 2026-08-23 by SŪTRADHĀRA under M0-T60 finding F-1: this rule was written by M0-T59
   while the file was still unrepaired, and M0-T60 was fenced out of this file to protect that
   landing, so it routed rather than fixed. Superseded text, verbatim: "…`:159` still carries the
   `NODE_ENV !== 'test'` form and is a known open item (M0-T50 routed it to the conductor unfixed;
   its direction analysis is genuinely different and was deliberately not decided in passing)."
   Not certified by its author — I16.)*

## A3.4.5 — The invariants this contract implies, and which of them have a detector

Stated per CLAUDE.md §N.8: a claim without a detector behind it is null, not green.

| # | Invariant | Detector | Status |
|---|---|---|---|
| INV-1 | No `.env*` file, workflow, Terraform file or container image sets `IMPORT_ONLY` | **NONE** | ⚠️ **Convention only.** `grep -rn IMPORT_ONLY .github/` returns nothing *today* — a measurement with a short shelf life. Nothing would report it if a future workflow set it, and both gates would go quiet by a different route. Recorded as `V-36` finding **F-I**; the recommended fix is a greppable CI assertion that no workflow sets `IMPORT_ONLY` at job or step level, of the same shape as `migration_number_guard`. **Not yet built — deliberately not built by M0-T59, which documented the contract and does not certify its own work.** |
| INV-2 | Both gates RUN by default, and refuse a silent pass under `NODE_ENV=test` | **YES** | ✅ Four subprocess tests, paired per file: `dispatch_gate.test.ts` — *"CAN-FAIL: under NODE_ENV=test with no opt-out, a blocked dispatch still exits 1 and says why"* and *"the explicit IMPORT_ONLY=1 opt-out still suppresses the CLI"*; the same pair in `verify_migrations_deployed.test.ts`. They spawn the real script rather than importing it. Reverting either guard to the `NODE_ENV` form, or flipping its polarity, fails the first of each pair. |
| INV-3 | INV-2's tests actually run in CI | **YES** | ✅ Both files resolve into the default `node` vitest project (`platform/vitest.config.ts` — that project declares no `include`, so vitest's default glob picks up `scripts/__tests__/*.test.ts`; confirmed with `npx vitest list --project node`), and `ci.yml`'s **Unit Tests** job runs `npm test`. Note the useful irony: that job sets job-level `NODE_ENV: test`, so the detector for the defect runs inside the very condition that used to trigger it. |
| INV-4 | This document stays true as the contract changes | **NONE** | ⚠️ See §A3.4.6. |

## A3.4.6 — Does any CI check assert this matrix? No.

Searched 2026-08-23, and the answer is stated here rather than left implied:

- `grep -rn 'A3_env_matrix'` over the repo returns only `platform/scripts/audit/.audit_state.json`
  (which records the A.3 phase as COMPLETE and points at this file as its report),
  `platform/scripts/audit/MASTER_AUDIT_REPORT.md`, two archived briefs under `99_ARCHIVE/`, one
  prose mention in `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/STATE_D-3.md`
  ("… + A3_env_matrix (OK all envs) …"), and Nirmāṇa campaign state. Every one of those is prose or
  bookkeeping. **No workflow, no script, no test, no governance tool reads it.**
- It is **not** registered in `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, so `drift_detector.py`
  and `schema_validator.py` do not cover it either.
- No script anywhere parses `platform/scripts/audit/A*.md`.

This file is a **point-in-time audit report** (`status: COMPLETE`, `executed_at: 2026-04-28`), not a
living registry with a validator. That is why the frontmatter above records an `addenda` entry
rather than re-opening the audit: appending here is honest, but it buys documentation, not
enforcement. **INV-4 has no detector, and this sentence is the disclosure of that fact rather than a
plan to leave it unfixed** — see §A3.4.5 INV-1 for the shape of the cheap fix.

## A3.4.7 — Open question, recorded not resolved

`M0-T50` raised this against its own work and did **not** claim per-file `vi.hoisted` was the right
trade:

> `vi.hoisted`'s correctness depends on vitest lifting it above the static imports. It demonstrably
> works, but a future editor moving it below the import block, or replacing it with a plain
> assignment, would fire `main()` on import. A config-level `env` entry might be sturdier.

What can be said without deciding it:

- The dependency is on a **documented** vitest guarantee, not an accident of ordering.
- The failure mode is **asymmetric** between the two files (read from source; not executed as a
  test): if the hoist were broken, `verify_migrations_deployed.ts`'s `main()` would attempt a DB
  connection and `process.exit(2)` during test collection — loud. `dispatch_gate.ts`'s `main()`
  with no `GATE_EVENT_NAME` takes the `not-a-dispatch` branch, which is `allowed: true` and only
  `console.log`s — quiet. So one half would announce the regression and the other would not.
- A vitest config-level `env` entry would set the sentinel for **every** test in the project, making
  "silenced" the ambient default across the whole suite and across every child process the suite
  spawns — the same broad-ambient shape the `NODE_ENV` repair existed to remove. That is a real
  argument *for* per-file, not against it.
- A third option neither has: **extract the pure functions into their own module** that the CLI
  imports, so tests import the pure module and never load the CLI. No env contract needed at all.
  This is a mechanism change, is out of `SQ-23`'s scope, and is recorded as a view, not a decision.

Routed to the conductor by `M0-T59`; not decided here, and the mechanism was not touched.
