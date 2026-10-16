---
artifact: LANE_SMALLTEST_BINDINGS.md
version: 1.0
status: CANDIDATE — requires independent review and main landing
produced_on: 2026-10-16
changelog: Initial J-1a local dry-run route and six-entry evidence contract.
---

# J-1a lane qualification

The six enabled small-test kinds accept two **top-level request fields** together:

```json
{"dry_run":true,"lane_target":{"host":"127.0.0.1","port":55433,"database":"ky_j1a"}}
```

A lane request also requires `request_id`, the canonical `chart_id`, a full merged
`reviewed_commit`, a timezone-qualified future `expires_at`, and the ordinary
operation identity, requester and argument fields. Request IDs and operation IDs
must be distinct for the six rehearsals and the final readback. Keep the existing
per-kind `args`; never append an `execute`, connection-string or SQL override.
Only explicit loopback names/literals, port 55433, and lowercase `ky_*` database
identifiers are accepted. Extra connection fields, nonlocal/failover hosts,
production database names and an unpaired mode/target are refused.

The executor checks both the entry script and adapter at the merged revision,
exports that revision with read-only `git archive`, and invokes the adapter with
`--dry-run --lane-target <JSON>`. Each child uses the existing P01 CLI with
`--dry-run`; production fixed arguments are never reused for this route. No
production connection, cloud configuration, passfile, service or caller-supplied
libpq setting reaches the child. Explicit connection settings and the actual
server/database/port are checked. Export directories are removed on return.

Existing requests without the selector retain their production arguments,
capabilities, approval/lease/evidence requirements and fence behavior. Lane work
uses the read queue, can run with a retained production fence, and neither takes
nor clears that fence, including after interruption. No kind is enabled or added.

**(I) INTERPRETATION J1A-I1:** a backup dry run is P01's no-effect plan, not a
snapshot or restored backup. Teardown qualifies the initial **empty** lane using
its actual locks, checks, deletes and rollback. Populated scope and execution
continue to require the existing independently accepted production evidence;
this route does not manufacture such acceptance. Alternative: perform backups,
restore databases, stage persistent runs, launch jobs or authorize populated
teardown during qualification; those effects exceed this dry-run task.

**(I) INTERPRETATION J1A-I2:** the existing enabled `readback_sql` kind, with the
same lane selector and `args={}`, is a fixed independent whole-database table
content/sequence measurement. It accepts no SQL file. Alternative: allocate a
new readback kind or forward the production readback environment; both change
interfaces that this task requires preserving.

**(I) INTERPRETATION J1A-I3:** lane metadata requires no production capability,
lease or production acceptance. Existing per-kind requester restrictions still
apply. Both endpoints and every child mode are constrained before execution.
Alternative: require owner/builder/cloud credentials for a local rehearsal;
those credentials are unnecessary and would invalidate credential-free routing.

## Receipts and the singular step evidence

Each completed lane operation emits exactly one `ky.smalltest_lane/1` proof.
The executor refuses success without matching operation/request identity,
request digest, kind, target, revision, entry-script identity, valid content
hashes, unchanged before/after measurements and independent readback. Its wire
receipt copies `request_id`, stores the proof under `lane`, and publishes:

- `request_sha256`: the existing complete-request digest.
- `output_sha256`: the digest of the complete redacted output file.
- `evidence_sha256`: SHA-256 of canonical compact sorted JSON of `lane`.

Lane receipts have neither production `launch` nor production `teardown`
evidence. Backup/restore attestations remain null; `launched` is false.

After all six complete, prepare a separate `readback_sql` lane request with
`args={}` and `lane_receipts=[{"name":"<operation_id>.json","sha256":"<actual receipt-file digest>"}, ...]`.
The six references must name exactly one completed receipt per small-test kind,
all at the same revision and target, with distinct operation/request IDs. Every
receipt byte digest, proof digest, identity and complete output file is checked.
References and symlinks escaping the receipt directory refuse. The final
request's identity must differ from the six source operations.

The executor stages those immutable bytes into the observer's private export;
the observer rechecks them and independently reconnects to the lane. Its current
content/sequence digest must equal the after-digest of **each** rehearsal. The
final proof contains `qualification` (six identity/receipt/output/evidence
bindings) and `qualification_sha256`. Missing, duplicate, changed, cross-lane or
cross-revision evidence fails admission or completion. This final readback's
receipt is the singular evidence artifact covering the complete six-entry set.

An independent verifier must additionally recompute each request hash from its
immutable request, compare each script digest to `git show <reviewed_commit>:<script>`,
verify the actual merged revision, inspect complete outputs and accept the final
receipt-file digest. Only the cockpit controller can publish the canonical
seven-field J-1a step marker required by `plan_model.json`; this adapter does not
publish `MET`, submit requests, approve production work or mark J-1a complete.
For that marker use the **actual final receipt-file SHA-256** as its
`evidence_sha256`, together with the final readback's operation/request IDs and
the actual independent review job. Do not confuse that file digest with the
wire receipt's nested proof digest or hash the step marker itself.

## Candidate qualification versus main qualification

**(I) INTERPRETATION J1A-I4:** this no-commit job can validate exact candidate
source and run the real CLIs locally, but cannot prove uncommitted files exist
at a merged revision. Candidate transport overlays in tests are explicitly
identified. Prepared request files require cockpit rebinding to the reviewed
merged commit and fresh expiry, followed by real executor validation. Alternative:
commit from this job or pretend the starting main includes these files; both
violate the job contract. No operational receipt or campaign marker is earned
by candidate tests alone.

The job's `SUBMIT.md` and preparation utility provide six requests, candidate
validation evidence, fail-closed live validation, and the final readback recipe.
No migration, production connection, cloud action, Git write, or shared campaign
state change is part of this implementation.

## Opened source anchors

- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:327`: common admission and selector hook.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:381`: explicit local endpoint settings.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:397`: merged-source and lane admission.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:446`: six receipt/output byte bindings.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:510`: reviewed source export and isolated invocation.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:540`: measured lane completion contract.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:653`: restart and production-fence separation.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/lane_smalltest.py:33`: separate read-only observer.
- `00_ARCHITECTURE/briefs/kalayantra/fleet/lane_smalltest.py:48`: real P01 CLI dry-run mapping.
- `platform/scripts/v5_small_test_shared.py:423`: local empty-scope exception.
- `platform/scripts/teardown_v5_small_test_job.py:598`: guarded rehearsal hooks, existing transaction retained.
- `00_ARCHITECTURE/control/kalayantra/plan_model.json:18195`: singular canonical step marker.
