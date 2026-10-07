---
artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER
version: "1.2"
verdict: LAUNCH-WITH-FIXES
blocking_count: 1
reviewed_commit: 8f5bcaf89
review_date: 2026-10-06
review_mode: read-only
---

## 1. Verdict

**LAUNCH-WITH-FIXES — the unpatched head is not cleared.**
Apply **KW-01 before launch**; resolve **KW-02 and KW-03 on day one**, before their affected acceptance gates.
Ten KZ findings are CLOSED; three are PARTLY. No redesign is required.
The three-hour approval amendment is sound; the restore-error amendment is not sound as implemented.
This is static confirmation, not a runtime launch certificate.

## 2. Part 1 table

References are relative to `/Users/Dev/kalayantra/wt/campaign`, at **8f5bcaf89**. **F/** = `00_ARCHITECTURE/briefs/kalayantra/fleet/`; **P/** = its sibling `prompts/`; **CH** = `KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md`; **KICK** = `KALAYANTRA_KICKOFF_PROMPT_v1_0.md`; **M** = `00_ARCHITECTURE/control/kalayantra/plan_model.json`.

“CLOSED” for B-1b requirements means the execution design is repaired; their implementation remains gated by B-1c/B-2.

| Finding | Status | Evidence and conclusion |
|---|---|---|
| KZ-01 — bootstrap | **PARTLY** | KICK:35–38,52,55; CH:169–171; P/SUTRADHARA.md:9–27 establish the bootstrap exception, installation and file handoffs. M:585,589 and P/PARIKSAKA.md:21 retain incompatible handoff names. **KW-01.** |
| KZ-02 — SQL/client escape and credentials | **CLOSED** | F/readback_sql.sh:12–38 resolves the leaf, uses a driver and prepared statement, and sets read-only mode. F/executor.py:185–188 supplies only the selected connection. The identified client-command route is removed. |
| KZ-03 — production authorization | **CLOSED** | F/executor.py:80–108,138–163,214–224 checks exclusive unexpired lease, complete request digest, timestamps, attestations and execution-time authorization. **Three hours is sound** because request expiry and the freshly checked lease remain additional bounds. Per-kind rows are sound; unfinished definitions remain disabled at F/executor_ops.json:8–23. |
| KZ-04 — production slot | **CLOSED** | F/executor.py:168–178,238–269 provides process-group cleanup, instance locking and a retained fence. P/ADHIKARIN.md:22 requires request-bound quiescence before releasing it. |
| KZ-05 — typed completion | **CLOSED** | CH:162; M:394–408; P/PARIKSAKA.md:19 distinguish PR head/merge mapping, artifact digest and operation identity, and assign N/V completion to S. Finalizer integration remains under KW-03. |
| KZ-06 — skipped dependencies | **CLOSED** | CH:163; M:401–408; M:1782–1800,4916–4925 retain mandatory Tulana/retirement obligations. The 28 explicit exceptions are present. Static propagation reproduces D-FLIP’s **11 skipped items, ten mandatory gaps**, with partial close reachable. |
| KZ-07 — ownership/dependencies | **CLOSED** | M:1782–1800,1928–2024,2448 onward,3194–3228,4803 onward,4892–4912 contains the requested edges, judge certification ownership and legacy dispositions. The graph remains acyclic. |
| KZ-08 — layer operations/output | **CLOSED** | F/executor_ops.json:21–23; M:4719,4792–4796 separate layer publication from Gochara authority. F/executor.py:116–118 preserves complete redacted output with its hash. |
| KZ-09 — finalization | **PARTLY** | F/finalize.sh:30–65 and CH:328 implement two phases, but P/PARIKSAKA.md:21 still writes different files; the finalizer accepts any non-`MISSING` review result. **KW-03.** |
| KZ-10 — rehearsal database | **PARTLY** | F/local_db.sh:28,43,56–75 removes automatic lane-side seeding and reruns assertions. However, lines 49–50 discard restore exits, line 55 allows arbitrary `planner_*` errors, and line 64 labels an existing database with the current seed hash without checking its provenance. **The amendment reopens the defect as implemented; KW-02.** |
| KZ-11 — deployment lease | **CLOSED** | CH:341; P/SUTRADHARA.md:44,48 require a lease through deploying merges and readback, including ordinary runtime PRs. |
| KZ-12 — precheck | **CLOSED** | F/precheck.sh:58–68,80–82 requires a manifest for code changes and matches forbidden-directory descendants. P/KARAKA.md:13 and P/PARIKSAKA.md:15 export `KY_ITEM`. |
| KZ-13 — splitting | **CLOSED** | M:1090–1110,1273–1293 supplies the two joins; M:1666,1890,2024,2344,2540,2684,3567 contains the seven remaining split instructions. |

## 3. Findings

### KW-01 — BLOCKING — Bootstrap acceptance still names an unwritten file

**Evidence:** M:539,549,585,589; P/SUTRADHARA.md:24–25; P/PARIKSAKA.md:7,21.

**Defect:** B-1p produces `run/bootstrap/B-1.request.json`, but B-1v’s required comparison still reads `B1_PR.json`. The verifier’s ordinary-cycle paragraph additionally sends its verdict to `run/verdicts/B-1.VERDICT.json`, whereas the conductor and detector consume `run/bootstrap/B-1.verdict.json`.

**Failure and launch trace:**

- **Steps 0–2:** the zsh substitution defect is gone; all five specification hashes match. Bootstrap preflight includes smoke, installation is unconditional, and absent/stale executor capability evidence stops launch. Database readiness can nevertheless be falsely accepted under KW-02.
- **Steps 3–5:** `wanted` clamps the pools correctly; the supplied `0/1` values start only S, N and v1. `lane_env`, `ensure_shell_home` and the generated profile establish the intended environment/startup configuration. Dry-run replaces the model command; it cannot establish model readiness. `quota_error_in` now examines only failed, non-timeout cycles’ last 40 lines, although that remains a text heuristic.
- **Initial cycles:** S can work B-4/B-1b/B-3b, N can work B-5, and v1 can answer B-1c using the old tracker’s supported commands. **The first unsatisfiable bootstrap acceptance instruction is B-1v’s read of `B1_PR.json`**—for example, `cat "$KY_ROOT/run/B1_PR.json"`—because the specified producer never creates it. An agent must improvise around the contradiction to finish.

**Exact replacement:**

In **M:585,589** and the **B-1v clause of P/PARIKSAKA.md:21**, replace:

```text
B1_PR.json
```

with:

```text
/Users/Dev/kalayantra/run/bootstrap/B-1.request.json
```

In that verifier clause, replace:

```text
run/verdicts/B-1.VERDICT.json
```

with:

```text
run/bootstrap/B-1.verdict.json
```

Replace M:585’s entire test string with:

> The verdict head equals both the head in `/Users/Dev/kalayantra/run/bootstrap/B-1.request.json` and the current GitHub head of that request’s PR; write `/Users/Dev/kalayantra/run/bootstrap/B-1.verdict.json` and its `<head>`-named archival copy. Any mismatch refuses acceptance.

### KW-02 — HIGH — Restore validation still accepts unproved fixtures

**Evidence:** F/local_db.sh:49–68,75; CH:277.

**Defect:** The claimed nine-error allow-list is actually three broad regex alternatives, and restore process failures are discarded. Revalidation also writes the current schema hash onto an existing database without proving that database was restored from that schema and ledger.

**Failure:** A connection failure, missing restore log, additional missing planner object, or changed seed can escape the intended provenance check while coarse table-count assertions remain satisfied.

**Exact replacement:**

At **F/local_db.sh:49–50**, replace each trailing `|| true` with `|| return 1`.

Before database creation at **line 44**, insert:

```bash
rm -f "$KY_ROOT/run/local_db/$lane.json"
```

Replace **line 51** with:

```bash
validate "$lane" restored
```

Delete **line 55**. Replace **line 63** with this exact diagnostic check—the approved nine messages, including their multiplicities:

```bash
unexpected="$(/opt/homebrew/bin/python3 - \
  "$KY_ROOT/run/local_db_${lane}_schema.log" <<'PY'
import collections, pathlib, re, sys

text = pathlib.Path(sys.argv[1]).read_text()
actual = collections.Counter(
    m.group(1).strip()
    for line in text.splitlines()
    if (m := re.search(r"\b(ERROR|FATAL|PANIC):\s*(.*)$", line))
    for m in [re.match(r"(.*)", m.group(1) + ": " + m.group(2))]
)
expected = collections.Counter({
    'ERROR: schema "public" already exists': 1,
    'ERROR: type "public.planner_managed_prashna_jobs" does not exist': 6,
    'ERROR: type "public.planner_inquiry_lifecycles" does not exist': 2,
})
print(0 if actual == expected else 1)
PY
)" || return 1
```

At the beginning of `validate`, after its local declarations, insert:

```bash
seed_sha="$(shasum -a 256 "$D/prod_schema.sql" \
  "$D/migrations_applied_data.sql" | shasum -a 256 | cut -d' ' -f1)" \
  || return 1

if [ "${2:-}" != restored ]; then
  /opt/homebrew/bin/python3 - "$KY_ROOT/run/local_db/$lane.json" \
    "$lane" "$seed_sha" <<'PY'
import json, sys

try:
    r = json.load(open(sys.argv[1]))
    ok = (r.get("result") == "READY"
          and r.get("lane") == sys.argv[2]
          and r.get("seed_sha256") == sys.argv[3])
except (OSError, ValueError):
    ok = False
if not ok:
    raise SystemExit("FAILED: restore provenance missing or changed; governed reset required")
PY
  [ $? -eq 0 ] || return 1
fi
```

Remove line 64’s old `seed_sha=…` assignment, retaining `mkdir`. In line 67’s receipt format, replace `seed_sha256_16` with `seed_sha256`.

Existing receipts require one governed restore with the corrected helper; they cannot be retroactively relabelled as proven.

### KW-03 — HIGH — The final-review producer and shutdown consumer still disagree

**Evidence:** P/PARIKSAKA.md:21; F/finalize.sh:45–64; M:5240–5269.

**Defect:** The verifier still writes `FINAL.VERDICT.json` and `FINAL_MESSAGE.md`, while the finalizer waits for `FINAL_REVIEW.json` and consumes `FINAL_MESSAGE_DRAFT.md`. Even if the filenames are repaired, `review != MISSING` accepts `REJECTED`, and ignored guarded-completion failures can leave the tracker stranded after its writers stop.

**Failure:** Finalization times out despite a completed review, or reports success without accepted final evidence and completed tracker transitions.

**Exact replacement:**

Replace the **C-4 clause in P/PARIKSAKA.md:21** with:

> Independently inspect an accepted `run/DRAIN_RECEIPT.json` as soon as it appears, even while C-4 is waiting, and record C-3’s typed artifact acceptance. Once C-3 completes, perform the final independent review; write `run/reviews/FINAL_REVIEW.json` with `result: ACCEPTED|REJECTED`, `by: v1`, the current drain file’s `drain_sha256`, the review path/hash and five MET/NOT MET findings, and write `run/FINAL_MESSAGE_DRAFT.md`. ACCEPTED means the report accurately represents its evidence and gaps; physical shutdown remains pending. Record the typed review evidence for C-4, then touch `/Users/Dev/kalayantra/run/STOP_v1` and exit. The finalizer alone writes the physical receipt and `FINAL_MESSAGE.md`.

Delete **F/finalize.sh:45**. Immediately before line 48 insert `c3_done=0`; replace its loop body with:

```bash
  if [ "$c3_done" -eq 0 ]; then
    KY_STREAM=S "$KY_ROOT/bin/ky" done C-3 \
      --evidence "$RUN/DRAIN_RECEIPT.json; independent artifact acceptance" \
      && c3_done=1
  fi
  if [ "$c3_done" -eq 1 ] &&
     [ -s "$RUN/reviews/FINAL_REVIEW.json" ] && lock_free v1; then
    break
  fi
  sleep "$POLL_S"
```

Replace **lines 51–53** with:

```bash
review="$("$PY" - "$RUN" <<'PY'
import hashlib, json, pathlib, sys

root = pathlib.Path(sys.argv[1])
try:
    r = json.loads((root / "reviews/FINAL_REVIEW.json").read_text())
    digest = hashlib.sha256((root / "DRAIN_RECEIPT.json").read_bytes()).hexdigest()
    accepted = (r.get("result") == "ACCEPTED"
                and r.get("by") == "v1"
                and r.get("drain_sha256") == digest)
except (OSError, ValueError):
    accepted = False
print("ACCEPTED" if accepted else "MISSING_OR_REJECTED")
PY
)"
```

Replace **line 57** with:

```bash
[ "$c3_done" -eq 1 ] && [ "${remaining:-0}" = 0 ] &&
[ -z "$left" ] && [ "$review" = ACCEPTED ] &&
[ -s "$RUN/FINAL_MESSAGE_DRAFT.md" ] || ok=0
```

Replace **line 64** with:

```bash
if [ "$ok" -eq 1 ]; then
  KY_STREAM=S "$KY_ROOT/bin/ky" done C-4 \
    --evidence "$RUN/FINAL_RECEIPT.json; $RUN/reviews/FINAL_REVIEW.json" \
    || exit 1
fi
```

Append to **M:C-4 `brief.notes`**:

> Guarded completion requires both the independently accepted, current-drain-bound final review and the accepted physical shutdown receipt. A regex match in the physical receipt alone cannot complete C-4.

## 4. What I could not verify

- No build, test suite, database connection, fleet/smoke execution, migration, deployment or remote lease refresh was performed. The reported runtime test counts remain author claims.
- Read-only calculations confirmed all five specification pins, 143 unique items, acyclicity, complete JOIN-ALL coverage and the stated refusal propagation. The new `join` and control-plane behavior remains B-1b implementation work.
- **A deterministic credential/personal-tool route remains:** lanes retain the operator’s `HOME`, `CODEX_HOME` and full disk access. They can deliberately read the known credential/configuration files or launch Codex without the generated profile. This is the explicitly accepted same-account residual in CH:340, not a newly reopened blocker; smoke does not prove its absence.
- The checkout remained clean at `8f5bcaf89676ffc506af4c3e67aff5dfb62a55d8`. Filesystem permissions prevented saving a review file; this inline artifact is the review.