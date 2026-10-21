# SC-1 — the seal controller (PLAN_A10_1 §5; A10.1 B8; O-12 seal approval delegated to the owner surrogate, OWNER-DEPENDENCY-REMOVAL-20261021)

Where it lives: this folder (`fleet/seal_controller.py`, tests `fleet/tests/test_seal_controller.py`, CI suite `governance-tool-tests-shard-5-0`). It supersedes the v1 SEAL-READY
poller, which the cockpit had installed as `fast/seal_controller.py` (v1 INSTALL.md step 1). The cockpit repoints its launchd job at this file (a checkout of main), or copies it
over `fast/seal_controller.py`; the program is stdlib-only, one poll per run, and reads/writes only the paths below. It never connects to a database, never runs `gh` / `gcloud`,
never reads a credential, never approves and never seals.

## The chain (every transition is a detector over evidence; a missing input is an honest status, never an advance)

| Stage reached | Evidence it measures | Not-ready kinds |
|---|---|---|
| `AGGREGATE` | persisted `generation_verdict` PASSED + a `g6` block PASSED; live grain readback (executor `readback_sql`): the included universe is exactly the adopted 26 classes, every grain VERIFIED / `window_qualification/1` / attestation PASSED, one runner commit = the head, live sums = the aggregate; verification receipt COMPLETED/0 bound to the head; INCONSISTENT share ≤ 0.5 % | NO_INPUT, AWAITING_READBACK, NOT_PASSED, REFUSED, STALE_HEAD, DISAGREEMENT, INCONCLUSIVE_OVER_CAP |
| `BRIEF` | `gochara_seal_brief_check.py` exit 0; `gochara_seal_execution_check.py check-envelope` exit 0 for this run / attempt / head / digest / brief id; head is an ancestor of `origin/main`; the brief's numerical verdict = the aggregate; optional quiescence record ACCEPTED with every check true. No brief yet: the exact dispatch command is written to `$OUT/BRIEF_DISPATCH.txt` and the surrogate paged once | AWAITING_BRIEF, REFUSED, STALE_HEAD, DISAGREEMENT, NOT_PASSED |
| `APPROVAL_REQUESTED` | emits once per (generation, head, run, attempt): `$OUT/approval/<gen>/<head12>-r<run>a<attempt>/` with `APPROVAL_BUNDLE.json`, `APPROVE_COMMAND.txt`, `SURROGATE_MESSAGE.txt`, `OWNER_NOTICE.txt`; one `PAGE SEAL-APPROVAL-REQUESTED` line in PAGES.log | AWAITING_APPROVAL; REFUSED if the prepared bundle names another brief digest |
| `APPROVED` | the approval history of this run through `gochara_seal_approval.py` (grammar line, run, attempt, digest, brief id) and the approver is the `gochara-seal` required reviewer | REFUSED (replay, other principal, ambiguity: start a fresh run) |
| `SEALED` | independent `readback_sql` of publication / seal / receipt rows, classified exactly as `gochara_seal_reconcile.classify`; the only success is SEALED naming this run's digest; one `PAGE SEAL-SEALED` | AWAITING_READBACK, AWAITING_SEAL, RETRY_NEEDED (run ended unsuccessfully, nothing sealed: a FRESH run only), HALTED (INCONSISTENT / UNREADABLE / a successful run with nothing sealed: `markers/HALT.<gen>.<head>`, one `PAGE SEAL-HALT`, nothing else is done for that key until a person removes the marker) |

## Inputs
Adopted file (default `/Users/Dev/kalayantra/run/ADOPTED_CENTURY.json`, or `--adopted` / `$SEAL_ADOPTED`; written by the cockpit):
`chart_id`, `generation`, `head`, `verification_operation_id`, `aggregate_file`, `expected_classes` (26 names), `repo` (checkout whose `origin/main` holds the head; the reviewed scripts are read
from its `platform/scripts`, or `scripts_dir`), then once the brief job has run: `brief_run {run_id, attempt}`, `brief_file`, `compact_file`, `envelope_file` (the `seal-brief-<run>-<attempt>`
artifact), and as they appear: `approval_history_file` (the run's `/approvals` JSON), `seal_run_file` (`{run_id, run_attempt, status, conclusion}`), `quiescence_operation_id`,
`expected_approver` (default `amonty84`), `triggering_actor`, `readback_epoch` (bump to ask for a fresh seal readback).

Readbacks: each poll that lacks a receipt writes `$OUT/readback/requests/<op>.json` + `$OUT/readback/sql/<op>.sql`; the cockpit copies them to `run/ops/requests/` and `run/ops/sql/`; the next poll
reads `run/ops/receipts/<op>.json` + `.output.txt`.  A new seal readback is requested whenever the run record, the approval history or `readback_epoch` changes (the op id binds them).

launchd (cockpit's own label): `ProgramArguments` `/opt/homebrew/bin/python3 <checkout>/00_ARCHITECTURE/briefs/kalayantra/fleet/seal_controller.py --out "$OUT" --pages-log fast/PAGES.log`,
`StartInterval` 300, `RunAtLoad`; stdout is one status line; `$OUT/SEAL_CONTROLLER_STATUS.json` carries `stage`, `state`, `kind`, `reason` every poll.  The cockpit session sends the two message texts.

## Interpretations (I) — alternatives in result.json
G-6 is read from the aggregate's `g6` block (R8X's final key is one constant, `G6_KEY`); the 1206 / 1232 / 1306 / near-miss gates are measured by the brief check (candidate gate clean), 1240 by the
live grain readback — the controller does not re-measure them; the brief job is dispatched by a person or the cockpit from the prepared command (no executor kind dispatches `gochara-seal-approved.yml`
and the table is a reviewed file this item does not edit).
