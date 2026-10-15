```json
{"id":"KV3-B-KYGATE",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source under fleet/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§10, §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/schemas/release_receipt.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"whole file","sha256":"b5ad761e61d935c4be8461407195f9f49cb9bc954c11cd41d1780926f0a01618"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kygate.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kygate.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kygate.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; READY_TO_START and OPEN only on fully satisfied fixtures",
"negative_cases":[
"bootstrap-only installation, absent rehearsal, stale tested hashes, missing coverage, changed final manifest: WAIT",
"stale resume, mixed release ids, a surviving global HOLD, each missing field: WAIT",
"a wrong receipt digest or any condition at WAIT: WAIT"]},
"packet_sha256":"1ab7c986ef52bdb5d00c57b8d450e827d91e0a209abbff0c6bfcaf0e48d80555"}
```
# KV3-B-KYGATE: `kygate.sh`

**Pins.** Plan v2.7 @ `e709f60d7`; base = the job header's reviewed B-0c head.

**Owns.** The two `d1_paths`: `kygate.sh` (git mode 100755, `#!/bin/bash`, bash 3.2; logic may be one embedded stdlib `python3 -I -B` program) and its tests. Prohibited: FROZEN paths, every other file.

**Spec (verbatim).**
```excerpt plan §10
`run/RELEASE_RECEIPT.json` (schema `fleet/schemas/release_receipt.json`): one
`release_id`, schema version, digest; every condition binds its evidence to that
release: certification → coordination commit/record id; pins → rebuild producer and run;
regeneration → main commit, generator version, output digest; PR dispositions → an
exhausted paginated API traversal with `{merged|parked|closed, owner, re_entry}`;
coordinator closure → SS's enumerated hand-off records. Missing or inconsistent evidence
is WAIT. Condition 5 has no producer today and stays WAIT until SS publishes it.
```
```excerpt plan §10
Both gate modes also require **final Wave B acceptance** (KT-03): the final
`run/VERSIONS.json` and a final installation receipt binding that manifest, the loaded
tracker revision, B-3's tested component hashes and measured rehearsal results, B-4's
independently accepted coverage and admitted packet hashes, and the validated B-5
governance backfill. `kygate.sh --pre-resume` validates the five release conditions and
that acceptance, and prints `READY_TO_START` only when every prerequisite is satisfied
and the sole missing launch authorisation is the matching N-467 resume record; it
authorises no campaign job. Negative fixtures: bootstrap-only installation, absent
rehearsal, stale tested hashes, missing coverage, changed final manifest.
```
```excerpt plan §10
`run/OWNER_RESUME.json` (binding `N-467`, the release-receipt digest,
`approved_bundle_digest` = the final manifest digest, the deciding identity — owner or
surrogate decision id — and timestamp)
```
```excerpt plan §10
STOP and global HOLD dominate bootstrap and campaign admission;
HOLD_MERGES blocks every queue submission. Negative fixtures: stale resume, mixed
release ids, each surviving hold, each missing field.
```

**Contract.** Usage `kygate.sh` (full gate) | `kygate.sh --pre-resume`; anything else 64. Env as in KV3-B-KYVERSION: `KY_ROOT`, `KY_RUN`, `KY_FLEET`, `KY_SOURCE_REPO`. Writes nothing; no network, database or tracker call (ruling P8: evidence is what the receipt binds); authorises nothing.
Exit 0 = open (full) or `READY_TO_START` (pre-resume); 75 = WAIT (anything missing, inconsistent or unknown). stdout: line 1 exactly `OPEN`, `READY_TO_START` or `WAIT`; then `release_id=`, `release_receipt_digest=`, `final_manifest_digest=` (empty when unknown), `hold_merges=present|absent` and one `reason=<code>: <detail>` line per failed check.
Call form: kyloop.py `verify_launch` (conductor): `self.run_helper("kygate.sh", [], 1800)`; `run_helper` runs `["/bin/bash", str(script), *args]` with that timeout; 0 = open, anything else `gate_not_open`; re-run when the sha256 of OWNER_RESUME.json or RELEASE_RECEIPT.json changes.
Checks:
- R1 `python3 -I -B "$KY_FLEET/kyschema.py" validate "$KY_FLEET/schemas/release_receipt.json" "$KY_RUN/RELEASE_RECEIPT.json"` exits 0.
- R2 `digest` == sha256 of the receipt's canonical JSON without `digest` — INTERPRETATION: canonical as kymanifest.py `canonical`.
- R3 each condition's `release_id` equals the top-level one (`mixed_release_ids`); all five are `SATISFIED`.
- R4 locally observable: `coordination_commit` and `main_commit` are commits in `$KY_SOURCE_REPO`, `main_commit` is contained in `origin/main`, PR numbers are unique; git not answering is WAIT. The other evidence fields are bound by R2, not re-observed: printed as `unobserved=<fields>`.
- A, final Wave B acceptance (receipt and manifest fields as KV3-B-KYVERSION names them; ruling P6: a missing one is WAIT, never a guess): A1 `mode == "final"` (`bootstrap_only_installation`); A2 VERSIONS.json's recomputed digest == its `manifest_sha256` == the receipt's `manifest.manifest_sha256` (`changed_final_manifest`); A3 `rehearsal.results` names a file with its sha256 (`absent_rehearsal`); A4 `rehearsal.tested_components` == the manifest's `components` (`stale_tested_hashes`); A5 `coverage.verdict == "ACCEPTED"`, its file has its sha256, `packets[]` is non-empty (`missing_coverage`); A6 `backfill.validated == true`; A7 `/bin/bash "$KY_FLEET/kyversion.sh"` (pre-resume), or the same with `--expected-manifest-digest <approved_bundle_digest>` (full), exits 0 within 300 s; missing, non-zero or timed out is `final_acceptance_unverified`.
- H `$KY_ROOT/HOLD` is absent (`global_hold`). Ruling P7 (INTERPRETATION): `$KY_RUN/HOLD_MERGES` never closes the gate (it blocks queue submission); only printed.
- N `$KY_RUN/OWNER_RESUME.json`: `binding == "N-467"`; `release_receipt_digest` == R2's digest (`stale_resume`); `approved_bundle_digest` == A2's digest; `decided_by {kind: "owner" | "surrogate_decision", id}`; `ts` (UTC). Each missing field is its own reason. (`binding`, `approved_bundle_digest`: as kyloop.py and test_kyctl.py; the other three names: INTERPRETATION.)
Full gate: `OPEN` iff R, A, H and N hold. `--pre-resume`: `READY_TO_START` iff R, A and H hold and no record satisfying N exists (a satisfying record: `WAIT`, `already_resumed`; a stale or malformed one is reported and does not block).

**Depends on.** Wave 2. KV3-B-KYVERSION (same wave; tests: a recording double): `kyversion.sh`, no argument or `--expected-manifest-digest <d>`, exit 0 = final manifest and receipt valid. Receipt fields: KV3-B-INSTALL (wave 4), B-5. N's names: the writers of OWNER_RESUME.json (veto controller, cockpit `resume`; B-0c part 2).

**Acceptance.** Tests first; temp `KY_ROOT`, `KY_RUN`, `KY_FLEET` (the real kyschema.py and schema copied in) and git repository. Positive: `--pre-resume` prints `READY_TO_START`, exit 0; with a satisfying record the full gate prints `OPEN`, exit 0, and `--pre-resume` says `WAIT`. Each alone gives `WAIT`, exit 75, with its reason: bootstrap-only installation; absent rehearsal; stale tested hashes; missing coverage; changed final manifest; stale resume; mixed release ids; HOLD; each missing resume field; each missing evidence field of each condition; a schema-invalid receipt; a wrong digest (so the B-0c fixture `release_receipt_satisfied.json`, a placeholder digest); each condition at WAIT, condition 5 included; an unknown commit; `main_commit` outside `origin/main`; a duplicate PR; kyversion missing, non-zero or hanging; a full gate without record. HOLD_MERGES present changes no result (`OPEN` stays `OPEN`) and prints `hold_merges=present`. The double's argv is asserted in both modes. No status without its check; unknown is WAIT.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): each command, exit code, summary; branch; pushed 40-hex `head_sha`; `pr_number`.

**Branch and PR.** `kalayantra/kv3-b-kygate`; one PR to main, "KĀLA-YANTRA v3 KV3-B-KYGATE: kygate.sh"; never merged, queued or approved by the job.

**Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets; write a resume record or remove a hold outside a test's temp directory. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
