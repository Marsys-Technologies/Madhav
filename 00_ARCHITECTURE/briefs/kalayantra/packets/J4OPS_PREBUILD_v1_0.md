---
artifact: J4OPS_PREBUILD
version: "1.1"
status: PREPARATION BUILT — production operation bindings and item completion LEFT OUT
produced_on: 2026-10-16
source_main: ef14167bcc35a321b11d4d189a6b752bf3c658b8
items: [J-4a-a25, J-4b-a55j, J-4c-a55m]
authority: A6 D-40 / SR-A4-01; no production activation
changelog:
  - "1.1 (2026-10-16): clarify R-PBJ4OPS-01 CI-glob proof locators; no executable behavior change."
---

# J4OPS preparation handoff

The local request binder, disabled preparation declarations, read-only SQL bundle
and 4.1 ephemeris preflight change are built for review. **The three operational
items remain left out of completion.** No migration, actual production adapter,
`brief.op`, executor enablement, receipt, step acceptance, protected apply,
credential act, deployment, seal, candidate build or authority flip is supplied.
Missing inputs are listed below. The cockpit must not install a preparation
entry as the production operation that an item's detector requires.

## Prepared interfaces

`platform/scripts/j4ops/operations.json` declares three distinct disabled
preparation entries, phases 6/7/8 and generations 4.1/5.0/5.0, preserving the
original dependency edges and inherited prerequisites. Each `executor_entry`
names the real `platform/scripts/j4ops/prepare.py` and fixed `--item`. The entries
are **not installed** in `fleet/executor_ops.json` or the plan model. They invoke
local preparation only; they allocate no production mutation kind.

The binder accepts these exact fields (no extras or duplicates):

```
schema = ky.j4ops_preparation_request/1
item, phase, operation_id, request_id, reviewed_commit,
chart_id, generation, enabled = false,
inputs = { <each declared name>: { path: <absolute path>, sha256: <64 hex> } }
```

Every named input must exist, be nonempty and match its digest. The declaration
file is itself pinned in the binder. Invoke from the reviewed checkout:

```sh
python3 -B platform/scripts/j4ops/prepare.py \
  --item J-4a-a25 --request-file "$REVIEWED_REQUEST" \
  --request-sha256 "$REVIEWED_REQUEST_FILE_SHA256"
```

The output binds both raw request-file bytes and the canonical complete request,
input bytes, identities, declaration digest and the binder's own hash. It always
says `PREPARATION_ONLY`, `enabled=false`, `dry_run_passed=false`, and
`operation_completed=false`. It validates **binding**, not evidence truth,
independent provenance, a lease or approval. A hash-bound opaque input can still
be invalid evidence. No populated production request or acceptance sample is
checked in, and `--execute` is unsupported.

## Phase 6 / J-4a-a25

**Built:** the exact inline preflight at
`platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh:49`
no longer requires `sefstars.txt` and `seleapsec.txt` for this planetary path.
All three original `.se1` SHA-256 pins remain. The C-library search and later
children use the same `SE_EPHE_PATH` whose bytes are hashed (`:31`, `:54`). The
returned SWIEPH flag is checked at both scored-horizon endpoints and J2000,
including TRUE_NODE to detect the documented lunar fallback (`:85`).

**(I) INTERPRETATION I-J4OPS-1:** the auxiliary-file requirement is obsolete for
this runner's `julday`/`calc_ut` path. The alternative is supplying newly approved
auxiliary inputs; no substitutes were created or fetched. Evidence:
`step06_enumerate_episodes.py:1169` converts the UTC timestamp using `julday`;
`services/gochara_kernel/knots.py:3` identifies its `calc_ut` sidereal path;
`panchang_engine/swiss_backend.py:25` documents the Moon/TRUE_NODE fallback
problem. None of those calculation paths calls `fixstar*` or `utc_to_jd`.
A fresh real-kernel daily probe over all eight persisted bodies and the complete
10,334-day scored horizon plus its end boundary made **82,680** calculations
with SWIEPH and no Moshier. Both auxiliary files are absent. This proves corpus
availability at those samples, not root completeness, scored classes or a build.

**Left out:** the actual candidate launcher/build. The separate century job is
not routinely deployed (`platform/scripts/__tests__/gochara_century_job_wiring.test.ts:6`),
and `platform/scripts/dispatch_a25_v41_candidate_job.py:1` only stages a run.
Do not resurrect a job from the legacy shell's historical header. Obtain the
accepted Q5 single-settled-build/consumed-copy readback and Q6 historical artifact
or explicit superseded disposition first. Q17 Q5/Q6 are at the supplied
`SURROGATE_ANSWER_17.md:21` and `:25`. The current settled run is declared at
`services/gochara_kernel/dasha_settlement.json:12`; historical `75524b3e` is
reference provenance at `services/gochara_rules/permission.py:36`. This job does
not repin either or change the model. A future real launcher also needs the
same-operation rehearsal, source/image/identity bindings, timing projection,
G8 approval, durable no-retry fence and independent terminal candidate readback.

## Phase 7 / J-4b-a55j

**Built:** `platform/scripts/j4ops/provision.sql:4` captures 36 effective privilege
cells: both verifier/sealer roles × both L1 tables × seven privileges, plus the
builder × both verification tables × INSERT/UPDATE/DELETE/TRUNCATE. Missing roles
or relations produce unmeasured NULL cells and refusal. Column-level
INSERT/UPDATE/REFERENCES grants are included in negative checks (`:18`). No
verification-row production write is attempted.

The exact L1 table list is `chart_facts` and `chart_dashas`. The verifier reads
`fact_subject`, `fact_value_num` by `fact_id`
(`services/gochara_kernel/inventory_verifier.py:187`); it reads daśā levels, lords,
intervals and identities (`:526`, `:815`). The SQL content digests consume entire
rows (`platform/migrations/1206_gochara_search_inventory_completeness.sql:256`),
so whole-table SELECT is required. The full inherited 1378 ACL closure remains
separate; this new matrix measures the previously omitted L1 reads and builder
verification-write negatives, not every grant or actual authentication.

**Left out: needs migration number.** The allocation registry supplied to the
job has allocations through 1393 and `next_free: 1394`, with **no J4OPS allocation**.
No number is chosen or migration created. Migration
`1378_gochara_verifier_sealer_inventory_grants.sql:53` explicitly excludes these
L1 reads and notes the ownership-preflight allowlist. The cockpit must allocate a
new migration and coordinate that allowlist before granting anything. Never edit
or reapply applied 1378. Also missing: original A5.5e acceptance, real act-2b
metadata/compensation evidence and the independently read disabled deployed job
definition. Existing definition checking is available in
`platform/scripts/gochara_verification_job_readback.py:81`; a local fixture or
passing parser test is not a deployed resource readback.

## Phase 8 / J-4c-a55m

**Built:** `platform/scripts/j4ops/readback.py` runs only two pinned SQL files.
It forces read-only libpq settings and a single repeatable-read READ ONLY
transaction, verifies database/session read-only identity, checks the reviewed
runner hash before connection, refuses SQL tampering/meta-commands, preserves
raw output, writes `RUNNER_SHA256` and hashes the saved files in
`MANIFEST.sha256`. Existing output directories are never overwritten.

`second_window.sql:4` captures PostgreSQL major version, the complete migration
ledger, Gochara routine definitions, trigger definitions/enabled states, effective
DML held by memberless NOLOGIN roles (excluding implicit table-owner rights,
consistent with the existing orphan audit's scope), and `amjis_app` schema CREATE.
Lists use C collation. A complete nonempty reviewed mirror expectation must be
provided by file plus digest **before connection**. Observations must equal it;
expected dormant-write rows must be empty and schema CREATE false. No expected
production hashes, migration list or golden is guessed from the target.

Prepared readback invocation, for the authorised executor at a later sitting:

```sh
python3 -B platform/scripts/j4ops/readback.py --phase second-window \
  --expect-db "$REVIEWED_DATABASE_NAME" --out "$NEW_EVIDENCE_DIRECTORY" \
  --runner-sha256 "$REVIEWED_RUNNER_SHA256" \
  --expected-file "$REVIEWED_MIRROR_EXPECTATIONS" \
  --expected-sha256 "$REVIEWED_EXPECTATIONS_SHA256"
```

Use `--phase provision` without `--expected-*` for the fixed ACL matrix.
Credentials remain solely in the executor's libpq environment. This job invoked
these interfaces only through the existing guarded local test fixture. A result
`READBACK_MATCHED` means those observations matched; it never means a protected
window, job identity, credential act, equality proof or operation is accepted.

**Left out:** the protected apply adapter/train and authoritative mirror
expectations. This main extract lacks the inherited 1305 snapshot-copy and 1306
G8 migration paths, 1308 near-miss storage, and the inherited 1303 revoke path.
Their accepted successor sources/allocations must come from their owning items;
this job creates no substitutes. Preserve the accepted 1305 → 1306 → 1308 order
and P06b qualification; do not revive historical 1307 merely because an old draft
lists it. Original A5.5e/A5.5l dependencies, the dormant-role revoke sequencing,
real acts 12–14 metadata, configured-but-disabled job readback, measuring-build
golden and unchanged-class inventory remain required. The byte-equality and
non-interference measurement is unrun because those authentic inputs are absent.

The rehearsal's `R-J4-ACCEPT-01` operation-step source-binding defect is also
outside this code change. Its controller fix must be independently accepted
before either operation step can be recorded. These preparation tools do not
emit or feed step receipts and do not bypass that defect.

## Verification, CI and closure

Tests are under `platform/scripts/governance/__tests__/test_j4ops_preparation.py`
and the two sidecar `tests/l3/gochara/test_j4ops_*.py` files. The governance file
is automatically discovered by `ci_shard.py`. The existing DB coverage guard now
expands shell globs and detects a removed selection. The real corpus and DB suites also
run by glob in the existing mandatory A5.3 database job with both REQUIRE flags.

**(I) INTERPRETATION I-J4OPS-2:** use that existing required job's glob selection
because this exact main has neither `ci_test_suites.json` nor `ci_discovery.py`.
Alternative: introduce a new repository-wide discovery framework in this job;
rejected as unrelated infrastructure. No explicit new test filename is added to
`ci.yml`. Migrate this glob into the profile when that framework lands; do not
claim a nonexistent `ci_discovery.py` printed `current`.

**(I) INTERPRETATION I-J4OPS-3:** `done` describes delivery of the allowed local
preparation, with the three full operational items `left_out`. Alternative:
count preparation, opaque file hashes or a code merge as operational completion;
rejected under §N.8 and Q17 Q3/Q7. No dependency or outcome is changed.

Fresh final verification: **40 J4OPS tests, 78 CI-shard tests and 11 targeted
mandatory-DB/AM-10 guards passed, without skips**. Fifteen original-source
reversions/semantic mutations each exit 1; their fixed counterparts exit 0.
The real-library lunar-loss test checks TRUE_NODE after a genuine copied lunar
file disappears after hashing; no simulated coordinates or flags are used.

The job folder retains the exact old-shell reversion proof, semantic mutation
copies, fixed/reverted logs, JUnit XML, real-corpus probe and source index for
review. Transient test directories are removed. Guarded fixtures drop their own
databases; the shared cluster is neither stopped nor reconfigured. The supplied
worktree remains for the cockpit's commit/review. No generated output, lock,
FROZEN file or L0–L2 asset changed. Campaign-level session open/close remains with
the cockpit (charter §8.6); no separate validated session close is claimed.

### R-PBJ4OPS-01 — retained proof clarification

Closure evidence is retained under
`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261016T152605Z-nb-j4ops/`.
Its `builder-result.corrected.json` supersedes only the two CI-glob `copy_path`
entries and their explanatory note in the original builder result. Both entries
now name `revert-proofs/ci-glob-guard-reverted` in the closure job folder.
The original result and review artifacts remain unchanged.

The distinct reverted snapshot contains the exact parent guard from
`ef14167bcc35a321b11d4d189a6b752bf3c658b8`; the fixed snapshot contains the
accepted `43a8f3d7d7a395fd1af7804821c8a11ca7db3494` guard. The named CI-glob
regression fails with an assertion on the former (exit 1) and passes on the
latter (exit 0). `source-index.json` binds the bytes and `proof-runs.json`
records fresh commands and logs.

The review-time observation is not reproducible against the original locator's
current bytes: its ambiguously named `revert-proofs/fixed` directory also
contains the exact parent guard and fails that regression. This closure makes
the retained evidence explicit; no executable code or CI behavior change is
warranted. The three operational items remain outside completion.
