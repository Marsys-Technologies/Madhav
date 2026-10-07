---
artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER
version: "1.1"
verdict: REWORK
blocking_count: 3
reviewed_commit: faee6cc91
review_date: 2026-10-06
review_mode: read-only
---

## 1. Verdict

**REWORK — do not launch this revision.**  
Three blockers remain: the bootstrap command path, unrestricted `psql` input, and incomplete executor authorization.  
The supervisor’s initial pool gates work: `v2` and all six implementation workers stay idle.  
The 135-item graph is acyclic and JOIN-ALL covers every pre-close item, but completion semantics and several ownership/dependency edges need correction.  
Apply KZ-01–KZ-03 before launch; the HIGH findings require first-day repair before their affected operations become eligible.

## 2. Part 1 table

Paths below are relative to the repository:

- **CH**: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md`
- **OS**: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md`
- **KICK**: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_KICKOFF_PROMPT_v1_0.md`
- **F/**: `00_ARCHITECTURE/briefs/kalayantra/fleet/`
- **P/**: `00_ARCHITECTURE/briefs/kalayantra/prompts/`
- **M**: `00_ARCHITECTURE/control/kalayantra/plan_model.json`
- **T/**: `platform/scripts/governance/pravaha_tracker/`
- **PLAN**: `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md`

All line references identify **faee6cc91**, not subsequent workspace changes.

| Finding | Status | Evidence | What remains |
|---|---|---|---|
| KY-01 | **CLOSED** | CH:12–17; F/verify_specs.sh; bundled specification bytes match all five charter SHA-256 pins. | Nothing from the original missing-specification finding. |
| KY-02 | **CLOSED** | CH:159,166; M:334–416; F/kalayantra_fleet.sh:208–213; P/SUTRADHARA.md:21–25. | Atomic claims are deliberately deferred behind B-1c/B-2; only single-actor bootstrap streams run beforehand. Bootstrap command compatibility is separately defective under KY-05. |
| KY-03 | **PARTLY** | CH:160–162 specifies guarded completion; T/state.py:71–101 still gives detectors precedence; M:351–355,398–401; P/PARIKSAKA.md:15,26. | Bootstrap still relies on the old tracker, and the future completion contract does not distinguish code heads from review/artifact hashes or identify who completes N/V-owned items. KZ-01, KZ-05. |
| KY-04 | **PARTLY** | F/kalayantra_fleet.sh:160–166 scrubs lane environments; CH:332 discloses same-account access; F/executor.py:118–120; F/readback_sql.sh:15–21. | Executor children inherit both privileged connection variables, and agent-authored SQL reaches `psql`’s command interpreter. KZ-02. |
| KY-05 | **OPEN** | KICK:35,49; CH:229; P/ADHIKARIN.md:9; P/SUTRADHARA.md:17; P/PARIKSAKA.md:11; T/cli.py:179–190,272–287. | Detached preflight fails; `audit`, `verdict`, and `send --to V` are unavailable before the upgrade. No operative bootstrap exception bridges these commands. KZ-01. |
| KY-06 | **PARTLY** | CH:91–104; M:3291–3884 establishes the revised small-test/measuring/full-build sequence. | Approved-path ordering is repaired. A refused prerequisite becomes `not_applicable`, but ordinary descendants can then become READY without the prerequisite’s output. KZ-06. |
| KY-07 | **CLOSED** | OS:45; P/ADHIKARIN.md:20; M:4012–4034. | G6 requires passing endpoints and the other flip conditions. Settled failure/insufficient evidence is refused; it cannot authorize the flip. |
| KY-08 | **CLOSED** | M:3884–3919,3948–3980,4034–4071. | Seal detection now uses the seal function and returns qualifying rows; publication detection checks authority and published state. J-6m owns the replacement authority CHECK migration before D-FLIP. Live SQL execution remains unverified. |
| KY-09 | **PARTLY** | M:4656–4814,5034–5244; PLAN:299–363. | No pre-close item is outside JOIN-ALL. Coverage declarations nevertheless omit explicit judge certification ownership, understate contract-phase write ownership, and make promised Tulana/second-writer results optional. KZ-06, KZ-07. |
| KY-10 | **PARTLY** | CH:254–269,286–287,333; P/SUTRADHARA.md:36. | Expand/contract and post-deploy verification are specified. The explicit ordinary-merge lease exemption still permits concurrent automatic deployments. KZ-11. |
| KY-11 | **PARTLY** | F/executor.py:47–50,81–144,169–186; F/executor_ops.json:4–19. | A concrete executor exists and checks merged ancestry/requester labels. Its lease, approval binding, lifecycle, full-layer operation mapping, and complete readback delivery remain defective. KZ-02–KZ-04, KZ-08. |

## 3. Findings

### KZ-01 — BLOCKING — Bootstrap invokes capabilities it is supposed to build

**Evidence:** KICK:35,49,52; CH:229; P/SUTRADHARA.md:9,17–24; P/ADHIKARIN.md:9–11; P/PARIKSAKA.md:11,17; T/cli.py:179–190,272–287.

**Defect:** The three active lanes follow commands that the frozen tracker cannot execute, without a complete pre-B-2 exception. A healthy existing tracker also bypasses installation, so kickoff does not establish that `ky`, its snapshot, and the selected model belong together.

**Failure and launch trace:**

1. In the specified zsh environment, the first literal failure is KICK:35: `${!v:-}` produces `bad substitution`. Running that block in Bash avoids only this failure.
2. Specification pins match. `preflight.sh bootstrap` repairs/checks campaign dependencies but does not supply the missing tracker capabilities.
3. `install_tracker.sh` correctly copies a package snapshot and creates `ky`/`kybrief`; its bootstrap receipt deliberately permits `audit_ok: false`. Therefore that receipt cannot authorize the normal lane protocol.
4. With the supplied pool files, `up` snapshots the fleet scripts, double-forks lane supervisors, acquires lane locks, and leaves `v2`/`k1`–`k6` sleeping before `run_cycle`. `reserve_cycle` reserves starts under its lock before execution; `env -i` omits production credentials; the Python controller gives Codex a process group and enforces its time limit. These are substantive repairs.
5. An active detached lane following CH §5 next runs `ky preflight`; the old branch-pattern check rejects `HEAD` with exit 4. Its written instruction is to fix preflight before proceeding, while the missing capability is precisely B-1b.
6. If S interprets its bootstrap paragraph as overriding preflight, N still calls unsupported `ky audit`; S later calls unsupported `ky send --to V`; V calls unsupported `ky verdict`.
7. After B-2, `preflight.sh launch` legitimately requires working `audit`. B-6 also requires the executor, its merged operations table, and a completed readback, so an absent executor blocks B-3/B-7 and **all K work**, contrary to KICK:52.

**Exact replacements:**

Replace KICK:35 with:

```bash
for v in DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL PGPASSWORD; do
  [ -n "$(printenv "$v")" ] && echo "SET: $v"
done
echo "secret check done"
```

Replace KICK:49 with:

> 4. **Tracker.** Run `bash $F/install_tracker.sh --gov "$KY_ROOT/wt/campaign/platform/scripts/governance"` and require its ACCEPTED installation receipt. Verify the receipt identifies this selected package, its snapshot hash and this campaign's model. Then require live health without model errors and `ky status` showing the model's item count. A healthy HTTP endpoint alone never substitutes for this installation check. `audit_ok: false` is permitted only during the explicit pre-B-2 bootstrap protocol below.

Replace KICK:52 with:

> 7. **Executor.** Require a CAPABILITIES.json timestamp less than ten minutes old and `pgenv: true`. `ops_table_on_main: false` is permitted before B-1. Missing builder/owner capabilities are recorded and block their production consumers; an absent executor or missing read-only capability stops this kickoff, because B-6 and hence B-7 depend on them. Do not start the executor from this session.

Insert after CH:166, and reference this paragraph immediately before “Each cycle” in all three bootstrap role prompts:

> **Pre-B-2 bootstrap protocol — overrides §5 and the role prompts until B-2 is accepted.** Only S, N and v1 act. Check `$KY_ROOT/HOLD` and `STOP_$KY_LANE` directly; inspect live health and the declared worktree directly. Do not call `ky preflight`, `claim`, `audit`, `verdict`, `unblock`, `decide --outcome`, or stream-to-stream `send`. Use only the old `start`, `step`, `review`, `status`, `next`, `note`, `report` and `inbox` commands with their existing syntax. Defer campaign decisions until B-2.
>
> S is the only bootstrap integration writer; N writes only its B-5 branch. Each author writes `run/bootstrap/<ID>.request.json` containing item ID, branch, exact head and requested checks. v1 polls these files each cycle and writes `run/bootstrap/<ID>.<head>.verdict.json` containing the same identity, ACCEPTED/REJECTED, commands/results and evidence hashes. A changed head requires another verdict. Old detector-derived DONE states are advisory and cannot authorize a merge.
>
> B-1c runs the new package against temporary fixture event logs through an explicit PYTHONPATH pointing to the reviewed candidate checkout; it does not replace the running package. S queues B-1 only after B-4, B-3b and B-5 are independently evidenced and v1 accepts the final integrated PR head. B-2 installs the merged package, validates its receipt and audit, and imports the independently checked bootstrap receipts through the new guarded completion path. Only then do the ordinary commands apply and the verifier pool rise to two.

Also add `B-3b` to B-1’s `depends_on`, and `B-4` to B-1b, B-3b and B-5’s `depends_on`.

---

### KZ-02 — BLOCKING — Readback SQL can execute shell commands inside the credential-bearing executor

**Evidence:** F/readback_sql.sh:15–21; F/executor.py:118–120; F/executor_ops.json:4–5.

**Defect:** The write-verb grep does not reject `psql` commands such as `\!`, `\i` or `\connect`, and resolving only the parent directory leaves leaf symlinks unchecked. The child also inherits `KY_BUILDER_DATABASE_URL` and `KY_OWNER_DATABASE_URL`, so this enabled readback operation defeats the intended credential boundary.

**Failure:** A readback file can execute a local command or escape the intended connection/transaction; the SQL `READ ONLY` transaction does not constrain the `psql` client.

**Exact replacements:**

Replace F/executor.py:118 with:

```python
env = {
    k: v for k, v in os.environ.items()
    if k in {
        "HOME", "PATH", "LANG", "LC_ALL", "TZ", "TMPDIR",
        "CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS",
    }
}
```

Retain lines 119–121 so only the selected operation receives its required `DATABASE_URL`.

Replace F/readback_sql.sh:15–21 with:

```bash
unset DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL
source /Users/Dev/.config/pravaha/pgenv.sh
exec "$KY_ROOT/venv/bin/python" - "$KY_ROOT" "$SQL" <<'PY'
import csv
import pathlib
import re
import sys
import psycopg

root = pathlib.Path(sys.argv[1]).resolve()
base = (root / "run/ops/sql").resolve(strict=True)
path = pathlib.Path(sys.argv[2])
if not path.is_absolute():
    path = root / path
path = path.resolve(strict=True)
if not path.is_relative_to(base) or path.suffix != ".sql":
    raise SystemExit("SQL file must resolve beneath run/ops/sql")
sql = path.read_text()
if not re.match(r"\s*(SELECT|WITH)\b", sql, re.I):
    raise SystemExit("one SELECT/WITH statement required")

# Extended-query preparation rejects multiple SQL statements.
# No psql client commands, includes, shell escapes or reconnections exist.
with psycopg.connect("") as conn:
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '14min'")
        cur.execute(sql, prepare=True)
        if cur.description is None:
            raise SystemExit("query did not return rows")
        out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        out.writerow([column.name for column in cur.description])
        for row in cur:
            out.writerow(row)
PY
```

Insert the same `unset DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL` before line 11’s fixed migration-query branch sources pgenv.

Add to B-1c’s acceptance cases:

> Readback rejects a leaf symlink escaping run/ops/sql, multiple SQL statements, `\!`, `\i` and `\connect`; the readback child environment contains neither privileged connection variable. A permitted SELECT still returns its complete rows.

---

### KZ-03 — BLOCKING — Production approval is neither a live lease check nor approval of the actual request

**Evidence:** F/executor.py:44–45,66–69,95–109,179–186; P/PARIKSAKA.md:16.

**Defect:** A lease ID appearing anywhere on a line without `RELEASED` is accepted even when expired or conflicting, while the approval check examines only result, operation ID, verifier label and commit. Arguments can change after approval, missing checklist/backup/dry-run evidence is accepted, and authorization is checked before queuing rather than immediately before execution.

**Failure:** Once an operation is enabled, the frozen controller can start an unapproved target or start after its lease expires; the promised refusal in P/PARIKSAKA.md:16 is false.

**Exact replacements:**

Replace `sync()` with:

```python
def sync() -> None:
    p = git("fetch", "-q", "origin", "main", "campaign-coordination")
    if p.returncode:
        raise RuntimeError("cannot refresh authoritative refs")
```

Replace `lease_live()` with:

```python
def lease_live(lease_id: str) -> bool:
    if not SAFE_ID.fullmatch(lease_id):
        return False
    if git("fetch", "-q", "origin", "campaign-coordination").returncode:
        return False
    p = git("show", f"origin/campaign-coordination:{COORD_PATH}", timeout=30)
    if p.returncode:
        return False
    section = p.stdout.split("## 1.", 1)
    if len(section) != 2:
        return False
    section = section[1].split("## 2.", 1)[0]
    active = []
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [s.strip() for s in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        status = cells[5].replace("*", "").strip()
        if not re.match(r"^ACTIVE(?:\s|$)", status):
            continue
        try:
            expiry = dt.datetime.strptime(cells[4][:16], "%Y-%m-%d %H:%M").replace(tzinfo=ist)
        except ValueError:
            return False
        if expiry > dt.datetime.now(dt.timezone.utc):
            active.append(cells[0])
    return active == [lease_id]
```

Add `hashlib` to the imports and add:

```python
def request_digest(req: dict) -> str:
    bound = {k: v for k, v in req.items() if k != "acceptance_receipt"}
    data = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

def utc_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)
```

Immediately after the existing acceptance-commit comparison, insert:

```python
        try:
            current = dt.datetime.now(dt.timezone.utc)
            issued = utc_time(a["ts"])
            expires = utc_time(req["expires_at"])
            if not issued <= current < expires or (current - issued).total_seconds() > 900:
                return "approval expired or not yet valid"
        except (KeyError, TypeError, ValueError):
            return "valid approval timestamp and request expiry required"
        if a.get("request_sha256") != request_digest(req):
            return "approval does not bind the complete request"

        kind = req["kind"]
        required = []
        if kind != "backup_snapshot":
            required.append("backup_taken")
        if kind not in ("backup_snapshot", "backup_restore_verify"):
            required.append("restore_verified")
        if kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun"):
            required.append("dry_run_passed")
            if any(a.get("rows", {}).get(k) is not True for k in ("2", "3", "7", "9", "11")):
                return "required pre-acceptance rows are not all true"
        if any(a.get("checks", {}).get(k) is not True for k in required):
            return "required backup/restore/dry-run attestation missing"
```

Change `validate`’s signature to accept `reserved: bool = False`, and change its final idempotency check to:

```python
    if not reserved and seen(req["idempotency_key"]):
        return "idempotency key already used"
```

At the beginning of `run_one`’s `try` block, before `execute`, insert:

```python
        if (KY_ROOT / "HOLD").exists():
            receipt(req, "REFUSED", "HOLD set before execution")
            return
        sync()
        current_table = load_table()
        if current_table is None or current_table.get(req["kind"]) != op:
            receipt(req, "REFUSED", "operation definition changed before execution")
            return
        why = validate(req, current_table, capabilities(True), reserved=True)
        if why:
            receipt(req, "REFUSED", why)
            return
```

Replace P/PARIKSAKA.md:16’s approval schema description with:

> The receipt binds the complete request, excluding only `acceptance_receipt`, using SHA-256 of sorted compact JSON. It contains `request_sha256`, `ts`, `rows` with string keys `"2"`, `"3"`, `"7"`, `"9"`, `"11"`, and `checks` containing `backup_taken`, `restore_verified`, `dry_run_passed`; every applicable field is the Boolean true, supported by cited receipt paths and hashes. The request carries a timezone-qualified `expires_at`. Backup creation does not require its own future backup; restore verification requires the backup; a dry run requires backup and restore verification; a mutating operation additionally requires its passed dry run and all five checklist rows. Re-approve any changed request.

This replacement also removes the existing circular requirement that the first backup already have backup/restore/dry-run evidence.

---

### KZ-04 — HIGH — Executor restart and timeout do not preserve the single production slot

**Evidence:** F/executor.py:128,141–169,182–186; F/executor.sh:16–18.

**Defect:** `subprocess.run(timeout=...)` does not terminate an operation’s entire process group, and restart marks requests INTERRUPTED without preventing another production operation. One thread serializes local command invocations, not Cloud Run jobs that continue after a dispatch command returns.

**Failure:** An interrupted or detached job can overlap the next production operation; duplicate executor starts also have only a racy `pgrep` guard.

**Exact replacements:**

Add `fcntl` and `signal` to executor imports. After directory creation in `main`, insert:

```python
    instance_lock = (OPS / "executor.lock").open("a+")
    try:
        fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    fence = OPS / "PRODUCTION_PENDING.json"
    interrupted = sorted(f.name for f in INFLIGHT.glob("*.json"))
    if interrupted:
        fence.write_text(json.dumps({"interrupted": interrupted, "ts": now()}))
```

Before processing the request directory each loop, insert:

```python
        if (KY_ROOT / "HOLD").exists():
            time.sleep(10)
            continue
```

Immediately before `mark_seen`, insert:

```python
            if table[req["kind"]].get("production"):
                if fence.exists():
                    continue
                fence.write_text(json.dumps({
                    "operation_id": req["operation_id"],
                    "request_sha256": request_digest(req),
                    "ts": now(),
                }))
```

Add this helper and replace both operation `subprocess.run(...)` calls with `run_group(argv, cwd, env, timeout)`:

```python
def run_group(argv, cwd, env, timeout):
    p = subprocess.Popen(
        argv, cwd=str(cwd), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    try:
        out, err = p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(argv, p.returncode, out, err)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.communicate()
```

Append to P/ADHIKARIN.md:18:

> The executor retains `run/ops/PRODUCTION_PENDING.json` after every production invocation, including success, failure and interruption. N may remove it only after V records a request-bound quiescence receipt proving all corresponding local processes, remote jobs and database work terminal or absent; process exit alone is insufficient. Reconcile every request listed by an interrupted fence. Readback operations remain available while this fence blocks further production operations. Never remove a human HOLD to perform this reconciliation.

Add these cases to B-3b’s brief before its acceptance: two executor starts yield one controller; a child survives its parent unless the group guard is active; a dispatch returning while its remote job runs retains the slot; restart does not release the slot.

---

### KZ-05 — HIGH — Guarded completion has no coherent rule for artifacts, squash merges or N/V-owned work

**Evidence:** CH:160–162; M:385,1059–1085,1943–1966,4874–4930; P/PARIKSAKA.md:15,26; P/ADHIKARIN.md:35.

**Defect:** The proposed guard universally requires a verdict for a “merged head,” although packet exits use a 64-character review hash and operational items have no PR head. N and V are forbidden to mark anything done, no automatic transition is specified, and `V-<PACKET>` produces nonexistent `V-K0A`/`V-K3B` IDs.

**Failure:** The new tracker either strands valid operational/review work or weakens its guard until a matching string in a file completes it.

**Exact replacement for CH:161:**

> **Guarded completion has typed evidence.** Code items require an independent ACCEPTED verdict on the exact PR head and a recorded GitHub merge result mapping that head to the actual squash/merge commit; a post-deploy verdict binds the deployed merge commit. Artifact and operational items require a typed artifact digest or operation/request identity, their declared evidence schema, completed steps, eligible dependencies and independent acceptance; they do not require a fictional Git commit. S invokes the guarded `done` transition for N/V-owned items after their independent acceptance. N never self-verifies its operation. A packet item consumes the independent reviewer’s verdict and review SHA-256; V records that result without becoming its author. Detector matches are necessary evidence inputs, never sufficient completion conditions.

Replace P/PARIKSAKA.md:15’s `ky verdict V-<PACKET>...` instruction with:

> Look up the exact item ID and verdict-file path from the model. In particular, file `K0A.VERDICT.json` belongs to `V-K0a`, and `K3B.VERDICT.json` belongs to `V-K3b`. Record an artifact verdict with the review SHA-256, review path, independent reviewer identity and resolved finding references; do not pass a review hash as a Git head.

Append these exact B-1b acceptance cases:

```text
test_squash_merge_maps_reviewed_pr_head_to_merge_commit
test_operational_item_completes_without_a_fictional_git_head
test_conductor_can_guardedly_complete_independently_accepted_n_or_v_item
test_packet_ids_are_model_ids_not_uppercased_labels
test_packet_json_rejects_accepted_with_open_blockers
test_packet_json_rejects_missing_review_or_changed_review_digest
test_branch_file_marker_alone_cannot_complete_bootstrap
```

For packet JSON, require parsed fields rather than the regex alone: `result == "ACCEPTED"`, `blocking_open == 0`, existing review file with matching SHA-256, matching packet identity, and current accepted scope.

The six `executor_ops.json` regexes themselves are syntactically sound: each is false in this revision and becomes true when its named entry is enabled. Their weakness is sufficiency, not escaping. The two database queries correctly return zero rows on a false condition; their results still need request/generation evidence under this typed completion contract.

---

### KZ-06 — HIGH — `not_applicable` enables consumers that require missing output

**Evidence:** M:385,1501–1536,2448–2504,3323–3484,4034–4246,4409–4451,4594–4626; CH:40–48,162,214.

**Defect:** READY accepts every dependency that is either done or `not_applicable`, but only directly outcome-gated items acquire `not_applicable`. Thus refused D-FLIP skips J-6 while making its live-readback consumer J-6l eligible, and refused D-TEARDOWN can similarly expose teardown/measuring descendants without a run.

**Failure:** The refused branch attempts impossible work or stalls instead of reaching an honest partial close; optional flags can additionally conceal missing promised Tulana and second-writer retirement work.

**Exact replacement for the first three sentences of M:B-1b `brief.notes`, and the corresponding CH:162 contract:**

> Ordinary executable items require every dependency DONE. If a dependency becomes `not_applicable`, an executable consumer also becomes `not_applicable`, preserving the originating decision and missing-output reason. Only items explicitly declaring `accepts_not_applicable_dependencies: true` may become READY from terminal skipped dependencies; these are joins, independent reviews, certification/disposition reports and close reports, whose acceptance must enumerate the gaps. A required decision approved at the named outcome permits work; a final different outcome or a not-applicable decision skips it. Deferred and insufficient_evidence remain OPEN and never become terminal merely because time passes.

Set `accepts_not_applicable_dependencies: true` on the `V-*` items, `JOIN-ALL`, the K8 mapping/report items, K9-5 and C-1–C-4. Set `mandatory: true` on **K7-4 and KR-2**; their refusal remains permitted but becomes a declared campaign gap.

Add these B-1b tests:

```text
test_refused_flip_skips_live_readback_and_full_rebuild
test_refused_teardown_skips_dispatch_teardown_and_measuring_descendants
test_report_join_accepts_skips_and_lists_originating_gaps
test_open_optional_decision_does_not_satisfy_join_all
test_refused_promised_tulana_or_second_writer_retirement_forces_partial_close
```

The resulting required behavior is:

| Decision | Approved | Refused | Open/deferred |
|---|---|---|---|
| D-FLIP | J-6, live/soak, subsequent production path may proceed. | Dependent execution is skipped; mandatory Gochara/layer gaps force CLOSED-PARTIAL. | Dependent path and JOIN-ALL wait. |
| D-TEARDOWN | Small tests may start. | If recorded despite N’s policy, the whole dependent execution chain skips and closure is partial. | Small tests wait; no dispatch. |
| D-VC | D-G2 becomes eligible after its other prerequisites. | G2 branch skips; G1 remains independently valid. | JOIN-ALL waits. |
| D-COMPACT | K5-2b may install the compact representation. | Dense representation remains; the optional replacement skips. | JOIN-ALL waits. |
| D-G2 | K5-3 may run. | G1 remains; optional G2 skips. | JOIN-ALL waits. |
| D-T2 | J-7 may run. | Optional T2 work skips. | JOIN-ALL waits. |
| D-R6 / D-KR | Promised comparator/retirement proceeds. | Mandatory skipped result is a gap; partial close only. | JOIN-ALL waits. |

`mandatory: false` must not itself make an unresolved decision or item terminal.

---

### KZ-07 — HIGH — Coverage is connected but several results lack the necessary owner or predecessor

**Evidence:** M:1501–1533,1647–1750,2155–2200,2893–2925,4489–4515,4556–4592,5034–5220; PLAN:299–363.

**Defect:** K7-4 reads the K4-2b shim without depending on it, G1 consumes adapters without waiting for their implementation, and adapter work can begin before J-0m establishes shared-file ownership. The coverage block also substitutes implementation items for judge certification and names legacy contract work outside KR-1’s write-set.

**Failure:** Work can start against missing interfaces or overlapping files; the final census can precede retirement changes; JOIN-ALL can close without an explicit judge mapping or the promised legacy dispositions.

**Exact model edits:**

Append the following dependencies, retaining existing ones:

```json
{
  "K7-4": ["K4-2b"],
  "K5-G1a": ["KA-3a", "KA-3b"],
  "KA-3a": ["J-0m"],
  "KA-3b": ["J-0m"],
  "K8-KA": ["K7-4", "J-5s"],
  "K9-5": ["KR-1", "KR-2"]
}
```

These additions are acyclic.

Append to K8-KA’s title:

> ; explicit certification mapping for ka_gochara_v5, using the sealed-generation evidence and the current criterion-registry revision

Append `K8-KA` to `coverage.assets_and_legacy_code.ka_gochara_v5`.

Append to KR-1’s `brief.owns`:

```text
platform/python-sidecar/services/ka_kshetra/** — contracted internal vedha/murti path only
platform/python-sidecar/services/gochara_intensity/**
platform/python-sidecar/services/w2g/**
platform/python-sidecar/services/ka_temporal/**
platform/python-sidecar/pipeline/transit_search.py
```

Append to KR-1’s `brief.notes`:

> Each child implements the exact retain/move/delete disposition in PLAN §8. It must name the replacement and importer migration; transit_search remains an ad-hoc service and its second formula is renamed/cited or removed as specified. The ka_temporal date/as_of path delegates to the core clocks. No legacy directory is treated as disposed merely because another item cites PLAN §8.

K3-2 → V-K3b → K8-K3 is correctly connected. K9-4a also correctly requires approved D-FLIP; neither edge needs reversal.

---

### KZ-08 — HIGH — The executor contract conflates Gochara publication with full-layer publication and truncates evidence exports

**Evidence:** F/executor_ops.json:14–19; F/executor.py:71–77; M:1913–1941,4376–4407,4453–4487; PLAN:238–247.

**Defect:** K9-4b uses `verification_job` and `publish_head`, but those entries are owned and enabled for Gochara verification/authority switching rather than the layer-wide candidate publication protocol. K3-2’s real-data export can also exceed the sole retained output, `stdout_tail`, which silently discards everything before the last 20,000 characters.

**Failure:** K9 may verify/publish the wrong authority surface, while a partial export is mistaken for the complete sealed-data qualification input.

**Exact replacements:**

Add these disabled entries to `executor_ops.json`:

```json
"layer_verify": {
  "enabled": false,
  "needs": "builder",
  "script": "TO_BE_SET_BY_K9-3",
  "fixed_args": [],
  "allowed_args": ["run-id", "generation"],
  "production": true,
  "enabled_by": "K9-3"
},
"layer_publish": {
  "enabled": false,
  "needs": "builder",
  "script": "TO_BE_SET_BY_K9-3",
  "fixed_args": [],
  "allowed_args": ["run-id", "generation", "expected-head"],
  "production": true,
  "enabled_by": "K9-3"
},
"layer_rollback": {
  "enabled": false,
  "needs": "builder",
  "script": "TO_BE_SET_BY_K9-3",
  "fixed_args": [],
  "allowed_args": ["generation", "expected-head"],
  "production": true,
  "enabled_by": "K9-3"
}
```

Replace K9-4b’s `brief.op` with:

```json
["readback_sql", "layer_verify", "layer_publish", "readback_sql"]
```

Append to K9-3’s brief:

> Land and qualify the three layer operations separately from Gochara authority operations. Verification covers every candidate writer; publication uses compare-and-swap against expected-head; rollback restores the previous layer head. Enable only after the absent candidate, failed verification and stale expected-head cases are refused.

In `receipt()`, before writing its JSON, add:

```python
    if out:
        body = redact(out)
        output_path = REC / f"{name}.output.txt"
        output_path.write_text(body)
        r["output_file"] = str(output_path)
        r["output_sha256"] = hashlib.sha256(body.encode()).hexdigest()
        r["output_bytes"] = len(body.encode())
```

Append to K3-2’s acceptance:

> Consume the complete output artifact, verify its receipt hash and expected row count, and reject a tail-only export.

---

### KZ-09 — HIGH — The finalizer cannot establish the promised shutdown

**Evidence:** F/finalize.sh:10–32; CH:44,320,328; M:4874–4930; P/PARIKSAKA.md:17.

**Defect:** After its timeout the finalizer still attempts worktree removal and writes a receipt whose zero-process count explicitly excludes the running `v1`; C-3’s detector ignores busy lanes and retained dirty worktrees. No subsequent actor removes `v1`’s worktree or produces a receipt after it stops.

**Failure:** The fifth definition-of-done line is either falsely marked MET or permanently unachievable.

**Exact replacement for CH:320’s finalizer description and the C-3/C-4 brief notes:**

> Finalization has two phases. C-3 drains every lane except v1, proves their locks released, refuses to remove any busy or dirty worktree, and writes `run/DRAIN_RECEIPT.json`; a timeout or removal failure is a failed drain, never an accepted receipt. C-3 completes only from an accepted drain receipt.
>
> v1 performs C-4’s independent review against the drain and close evidence, writes `run/reviews/FINAL_REVIEW.json` and `run/FINAL_MESSAGE_DRAFT.md`, then writes STOP_v1 and exits. It does not claim the physical shutdown line MET while still running.
>
> The external finalizer remains alive, waits for v1’s supervisor lock and process group to disappear, removes its clean worktree, verifies all ten lane worktrees absent and all ten lane process groups stopped, and only then writes `run/FINAL_RECEIPT.json`. Dirty or busy state is preserved and reported as failure. The final receipt contains `result`, all ten lane states, worktrees remaining and any failures.
>
> The tracker’s guarded C-4 completion consumes both the independently accepted FINAL_REVIEW.json and the accepted physical FINAL_RECEIPT.json. The external finalizer materializes FINAL_MESSAGE.md from the reviewed draft and the measured shutdown facts without changing any substantive reviewer verdict. Campaign checkout, branches and evidence remain.

Change C-3’s detector path to `run/DRAIN_RECEIPT.json`; require parsed `result == "ACCEPTED"`. C-4 requires both final artifacts under KZ-05’s typed evidence contract.

Append to B-3b’s brief:

> Implement this two-phase finalizer and test busy-lock timeout, dirty worktree, removal failure, v1 still running and v1 successfully stopped; only the last case may produce an accepted physical final receipt.

---

### KZ-10 — HIGH — An existing or partially restored rehearsal database is accepted without validation

**Evidence:** F/local_db.sh:39–59; KICK:50; F/preflight.sh:41–42.

**Defect:** Schema and ledger restore errors are discarded, and the next invocation treats database existence as success. The automatic `seed` fallback also sources production connection settings from an agent-run path despite the declared executor/operator boundary.

**Failure:** A failed first attempt becomes an “exists” success on retry; tests and migration rehearsal then run against an incomplete fixture.

**Exact replacements:**

Replace local_db.sh:39 with:

```bash
[ -s "$D/prod_schema.sql" ] && [ -s "$D/migrations_applied_data.sql" ] || {
  echo "operator-provided schema seed missing; refusing agent-side production access"
  return 1
}
```

Replace lines 45–47 with:

```bash
"${PSQL[@]}" -d "$db" -v ON_ERROR_STOP=1 -q -f "$D/prod_schema.sql" \
  > "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || return 1
"${PSQL[@]}" -d "$db" -v ON_ERROR_STOP=1 -q -f "$D/migrations_applied_data.sql" \
  >> "$KY_ROOT/run/local_db_${lane}_schema.log" 2>&1 || return 1
local rc=0
( cd "$REPO/platform" && DATABASE_URL="$url" npx tsx scripts/migrate.ts ) \
  > "$KY_ROOT/run/local_db_${lane}_runner.log" 2>&1 || rc=$?
```

Replace the existing-database success branch at line 59 with:

```bash
echo "ky_$2 exists but has not been validated by this invocation; run the governed reset/revalidation step"
exit 1
```

Replace KICK:50’s acceptance sentence with:

> Every lane must return READY after successful restore, migration runner and assertions, or a separately verified receipt binding that lane database to the current seed and migration set. `exists` alone is never accepted. Seed creation is an operator prerequisite; kickoff never sources pgenv.

The existing-database branch can regain reuse only when B-3b implements and verifies that bound receipt.

---

### KZ-11 — HIGH — Ordinary automatic deployments still bypass the shared lease

**Evidence:** CH:254,286–287,324,333; P/SUTRADHARA.md:36; `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`:48–55.

**Defect:** CH:333 expressly exempts ordinary merges despite acknowledging deployment on every merge. Compatibility preserves reader behavior but does not reserve the shared deployment/rebuild window.

**Failure:** A runtime PR can deploy while another campaign owns the production lease.

**Exact replacement for CH:333:**

> **Deploy on merge.** Any merge that triggers a production deployment is production-adjacent, including ordinary runtime and migration PRs. S must hold an unexpired shared deploy/rebuild lease from queue admission through deployment and required readback. A documentation-only PR is exempt only when its deployment trigger is demonstrably skipped. Compatibility acceptance and lease ownership are separate requirements.

Replace P/SUTRADHARA.md:36’s parenthetical condition with:

> `(merge triggers production deployment ⇒ exclusive lease live through deployment/readback)`

---

### KZ-12 — MEDIUM — Precheck can miss both the item’s tests and forbidden-directory changes

**Evidence:** F/precheck.sh:53–60,71–72; P/KARAKA.md:12–13; P/PARIKSAKA.md:11.

**Defect:** Neither role sets `KY_ITEM` before precheck, so the documented item manifest can be ignored. The forbidden-path regex anchors directory alternatives immediately after their trailing slash, so it does not match files inside those directories.

**Failure:** A code item can report PRECHECK GREEN without its manifest tests and with a change inside a forbidden subtree.

**Exact replacements:**

Immediately before invoking precheck in both role prompts, insert:

```bash
export KY_ITEM="<exact model item ID being checked>"
```

Replace precheck.sh:71–72 with:

```bash
WF='\.github/workflows/.*|'
[ "${KY_ITEM:-}" = "K0a-0" ] && WF=''
echo "$CHANGED" | grep -qE \
'^(CLAUDECODE_BRIEF\.md|CLAUDE\.md|\.codex/.*|'"$WF"'platform/src/lib/retrieval/registry/knowledge/.*|00_ARCHITECTURE/briefs/(nirmana|suvarna|sampurti|purna_anvesana)/.*|platform/python-sidecar/pipeline/orchestrator/(asset_runner|runner|staleness)\.py|platform/python-sidecar/pipeline/orchestrator/writers/__init__\.py)$' \
  && fail "diff touches a frozen or forbidden path" \
  || ok "no frozen/forbidden paths"
```

Replace line 60’s warning-only branch with:

```bash
else
  if echo "$CHANGED" | grep -qE '\.(py|ts|tsx|sql|sh)$|^\.github/workflows/'; then
    fail "code item has no explicit test manifest; set KY_ITEM or TESTS"
  fi
fi
```

---

### KZ-13 — MEDIUM — Several multi-part implementations still lack the promised split instruction

**Evidence:** M:876–924,968–1016,1351–1387,1564–1608,1690–1750,2014–2049,2200–2246,2354–2389,3219–3260.

**Defect:** These briefs combine multiple independent implementations, migrations and qualification work without “S splits,” despite the one-cycle rule. The existing split instruction applies only to flagged items, so a worker can legitimately claim the entire package.

**Failure:** A 90-minute cycle ends with a partially implemented multi-surface item and an ambiguous resumption boundary.

**Exact replacement:** Append the following text to `brief.notes` for **K0a-1, K0a-3, K7-1a, KA-1, KA-3b, K4-2a, K5-G1b, K5-2 and J-0**:

> S splits this item before any claim into independently reviewable children, each with one implementation or evidence deliverable, an explicit write-set, tests and a detector. The parent becomes a join; existing downstream items continue to depend on the parent. No child may combine multiple adapter families or both a schema/protocol implementation and its full runtime qualification.

## 4. What you could not verify

- No build, test suite, database connection, migration, fleet launch, executor launch, deployment or production readback was run. Runtime behavior described above is static execution reasoning, except the isolated zsh substitution check and read-only model/hash calculations.
- Specification hashes, graph connectivity/acyclicity, model IDs and detector regex behavior were checked. Database-query schema compatibility, real seal state, credentials, privileges, installed profiles, Docker fixtures, launchd state and current remote leases remain unverified.
- The `origin/main` table boundary and private-worktree ancestry check are present. Actual operation scripts, verifier/sealer authority, restored backups and cloud-job termination cannot be qualified while their operations remain disabled or unimplemented.
- The workspace advanced beyond faee6cc91 during the review. Later changes were excluded; this verdict does not review the newer HEAD.
- The enforced filesystem sandbox permits reads only, so this review is supplied inline rather than saved to `reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_1.md`.