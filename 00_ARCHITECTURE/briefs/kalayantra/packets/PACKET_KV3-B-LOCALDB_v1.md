```json
{"id":"KV3-B-LOCALDB",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§3; §4a.2; §5 Slot DBs; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"KU-02","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/local_db.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_local_db.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_local_db.py -q -p no:cacheprovider",
"expected_result":"exit 0; hermetic: no container or database started",
"negative_cases":[
"1320: runner refuses on a registry seed lacking bg_transit_rules: FAILED, never READY",
"registry seed missing or empty: db FAILED, seed fails",
"wrong mount (anonymous volume, out-of-root bind): up exit 2, check exit 1",
"stale READY receipt: check exit 1",
"ownership conflict: db/reset exit 2; close keeps the other session's database",
"stop without removal: close still owed, exit 0 only once absence is observed",
"S empty, `..`, slash or quote: exit 2, nothing called",
"label owner closes first, the other second: container and storage absent",
"close, no container: exit 0",
"close, incompatible container: no stop, rm, rename call",
"close, unmarked database: exit 1",
"real settings path opened: suite fails"]},
"packet_sha256":"377cc19cc482366ffff64e5948b054b8d7b0b7e9aa8299488a7486e30abfc4dc"}
```
**Pins** Plan v2.7 at e709f60d7; base = the reviewed B-0c head (job header).

**Owns** The two `d1_paths`. Prohibited: `executor_ops.json`; FROZEN paths.

**Spec** (verbatim)
```excerpt plan §5
**Slot DBs** `ky_b1..b6`, `ky_v1..v4` on `ky-pg:55433` via the repository `local_db.sh`
  (registry-inclusive seed; mandatory schema/ledger/registry hashes in each slot
  receipt), supported throughout DB guards, preflight, model worktree/branch
  authorisation, executor and cleanup. Negative fixture: the 1320 prerequisite failure
  and a missing registry are detected.
```
```excerpt plan §4a.2
Test databases are bound to their originating session
   and cleaned up on its termination, including crashes (KU-02); closing a cockpit neither
   adopts nor deletes another session's databases.
```
KU-02, verbatim (label `local-db`):
```text
Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.

Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.
```

**Contract** `bash local_db.sh <command>`. Exit 0 ok or READY; 1 FAILED or not verified; 2 refused, nothing changed; 64 usage. S: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else exit 2 before any docker, psql or filesystem call. R = `realpath($KY_SCRATCH)`.
- `slots`: one per line, `b1..bN` then `v1..vM`; N, M: integers in `$KY_RUN/KY_WORKERS`, `$KY_RUN/KY_VERIFIERS`, each 1–8. Missing, unreadable, out of range: exit 1, no output.
- `up --session S`: container `ky-pg`, image `pgvector/pgvector:pg16`, labels `campaign=kalayantra`, `ky.session=S`, published `127.0.0.1:${KY_PG_PORT:-55433}:5432`, PGDATA bind-mounted from `R/db/S/pgdata`. An existing `ky-pg` is reused only if image, `campaign` label, port and a bind mount inside R match; else reported, no stop, rm or rename, exit 2.
- `db <slot> --session S`: creates or re-validates `ky_<slot>`, marked `COMMENT 'ky.session=S'`. READY only when: slot configured; `$KY_RUN/schema/{prod_schema.sql,migrations_applied_data.sql,asset_registry_data.sql}` non-empty; restore errors = today's expected set; the migration runner (`npx tsx scripts/migrate.ts` in `$KY_SOURCE_REPO/platform`, `MIGRATE_APPLY_PROTECTED=1`) exits 0; today's count floors hold; mount and session marks verify. An existing database is trusted only with a READY receipt of the same session, container id and seed hashes; else FAILED.
- `reset <slot> --session S`: drop and recreate, S's own databases only.
- `check <slot>`: read-only; exit 0 only if the receipt is READY and, observed now, container id, mount (a bind inside R), the three seed hashes and the database's session mark equal it; else `ky_<slot> STALE: <reason>`, exit 1.
- `close --session S` (INTERPRETATION of KU-02 "session ownership") prints `close session=S dropped=<n> container=<c>`; in order. No `ky-pg`: c `absent`, exit 0. One `up` would not reuse: reported, no stop, rm or rename; `incompatible`, exit 0. An unmarked non-system database is foreign: no removal, no hand-over; `unmarked_database`, exit 1. Else drops S's databases and receipts; no other session's database remains: removes the container and the resolved direct child of `R/db` holding its bind mount, whatever its label (`removed`); else both pass to a remaining session T, recorded atomically in `$KY_RUN/local_db/container.json` as `{"owner": T, "storage": <absolute path>, "from": S}` (`handed_over`); docker, server and directory observed again: exit 0 = S's databases gone and the container removed or handed over on record; else 1 (also S's label on a container with no record).
- `down`: stops the container only; never a cleanup.
- `seed`: operator or executor only (refused if KY_LANE, KY_ITEM or JOB_SCRATCH is set); writes the three files to `$KY_RUN/schema/`; a missing or empty registry dump fails it. Runs as a lone copy (executor.py: `bash <copy> seed`).

Receipt `$KY_RUN/local_db/<slot>.json` (atomic; removed before a restore starts): `{"schema":"ky.slot_db/1","slot","database","result":"READY|FAILED","reason","session_id","container":{"name","id","image","port"},"mount_source","seed":{"schema_sha256","ledger_sha256","registry_sha256"},"runner_rc","tables","kala_tables","ledger","unexpected_restore_errors","tools","ts"}`.

Environment: KY_RUN (default `$KY_ROOT/run`); KY_SCRATCH (required, absolute, existing); KY_SOURCE_REPO (replaces KY_REPO; default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`). Test overrides (absolute paths): KY_DOCKER, KY_PSQL, KY_PG_DUMP, KY_NPX (paths in the receipt's `tools`); KY_PGENV (seed's settings file; tests only: exit 2 if KY_RUN is `/Users/Dev/kalayantra/run`). Logs: `$KY_SCRATCH/db/`.

Plan §3 (no job holds DATABASE_URL): nothing exported; no connection string or password printed; `DATABASE_URL`/`PGPASSWORD` only for the script's own children; no `url` command.

INTERPRETATION: (1) slot counts are read (plan `b1..b6`, `v1..v4` = §4's maxima); (2) session = `--session`, the role-lock owner's `session_or_run_id`; (3) the seed stays in `$KY_RUN/schema/` (§5: DB dumps under KY_SCRATCH).

**Depends on** Wave 1; nothing.

**Acceptance** Tests first. Fakes via the overrides, a fake settings file; call log read. Shows the negative cases and: a hand-over: exit 0, the record; `up`, `close` on an incompatible container: no stop, rm, rename; an unconfigured slot, a missing pool file: refused; a configured slot, complete seed: READY; no output holds a password or URL. READY, STALE and close's exit 0 each come from an observation in that invocation; unobservable = FAILED or exit 1, never ok.

**Evidence** `result.json` (BS-16): each command, exit code, summary; skips named; pushed `head_sha`.

**Branch and PR** `kalayantra/kv3-b-localdb`; one PR to main, "KĀLA-YANTRA v3 KV3-B-LOCALDB: local_db.sh slot databases"; never merged by the job (hold).

**Do not** edit outside Owns; run real docker, psql, pg_dump, the runner or the network; touch the existing `ky-pg`; rebase or force-push; read credentials or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
