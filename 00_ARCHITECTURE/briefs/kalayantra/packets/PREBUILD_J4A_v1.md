---
artifact: PREBUILD_J4A
version: "1.0"
status: PREPARED_OFFLINE — code children already on main; operational acceptance waiting on gate
produced_on: 2026-10-16
changelog: "v1.0: verify P04 on current main, rerun inherited oracles and twelve semantic reversions, enumerate the four remaining evidence obligations."
---

# J4A — phase 6 preparation (A6 D-40)

This is the lane 2 handoff for `J-4a`, `J-4a-pr2903`, `J-4a-pr3116`,
`J-4a-a25`, `J-4a-a26`, and `J-4a-a55k`. Verification base:
`a3ccc8ade9715ad02d69add40071f29cf29687df` (`origin/main` at job start).
P04 merge `9e7b2a227c4c86ed67607809aca2935a1a584be7` is an ancestor of that
base. Both inherited implementations and both test modules are byte-identical
to current main. The two old source heads were available locally and audited;
no fetch or duplicate port was needed.

Only this handoff is added. Scope excludes runtime source, settlement authority,
writers, L0–L2, migrations, generated aggregates, control-plane state, and live
receipt paths. No aggregate or digest lock needs regeneration.

## Per-item disposition

| Item | Preparation outcome | Evidence still needed for campaign acceptance |
|---|---|---|
| `J-4a-pr2903` | `already_on_main`: P04 absorbed inherited PR #2903; AM-10 source and oracles verified locally. | Authentic independent acceptance enumerating this exact child, exact reviewed/admitted-head CI with its ported oracles, and applicable deployed-source containment. |
| `J-4a-pr3116` | `already_on_main`: P04 absorbed inherited PR #3116; C50 source and oracles verified locally. | The same child-specific independent acceptance and exact-head CI/containment requirements; local builder verification supplies neither receipt. |
| `J-4a` | `left_out`: final prerequisite acceptance requires a guarded production readback. | Q17 Q5 single-build/consumed-copy/legacy reconciliation, final-build decision acceptance, all original dependencies, and SHA-256-bound independent acceptance for `settled_build_reconciliation`. |
| `J-4a-a25` | `left_out`: an actual candidate-only 4.1 build cannot be performed by this offline job. | Attributable historical operation/build receipt or the cockpit's governed Q6 disposition. A 5.0 build or P04 merge does not satisfy A2.5. |
| `J-4a-a26` | `left_out`: the 4.1 evidence obligation depends on A2.5. | Attributable Link-2/gates/PRAMĀṆIN/benchmark artifact and independent acceptance, or the cockpit's governed Q6 disposition. B5.4 retains its independent baseline dependency. |
| `J-4a-a55k` | `left_out`: issued upstream release evidence exists; consumed-copy acceptance remains outstanding. | Independently accepted upstream release and consumed-copy evidence bound to this item/step, with the original dependencies preserved. |

The four expected evidence files were absent at inspection:
`/Users/Dev/kalayantra/run/J4A_PREREQUISITE.json`,
`/Users/Dev/kalayantra/run/ops/receipts/J-4a-a25.json`,
`/Users/Dev/kalayantra/run/residuals/J-4a-a26.json`, and
`/Users/Dev/kalayantra/run/residuals/J-4a-a55k.json`.
These are observations about the named paths, not a search of every archive.
This job has no write authority to those locations.

## Gate handoff — prepared, not executed

The issued line and full run are already governed in
`platform/python-sidecar/services/gochara_kernel/dasha_settlement.json:4`
and `:12`: `ca17639b-f3cf-42c7-9866-0a61f3855802`, for chart
`482012f1-710e-4a25-994a-93821f5871aa`. The loader at
`services/gochara_kernel/dasha_read.py:71` validates that record. Historical
`75524b3e-102a-43ec-8cee-3f57fee752c3` is explicitly reference provenance at
`services/gochara_rules/permission.py:36`; it is not a replacement live pin.
Paths in this paragraph are relative to `platform/python-sidecar` after the
first full path.

Q17 Q5 (`SURROGATE_ANSWER_17.md:21–23`, supplied job input) requires the guarded
executor's production readback before acceptance. The cockpit must obtain and
independently accept evidence showing:

1. Exactly one settled L1 candidate for the governed full run and canonical
   chart; zero or two candidates stop P04 and require the Suvarṇa/owner ruling.
2. No non-terminal canonical-chart build run, and live `ga_positions` and
   `ga_dashas` build identities equal to the posted settlement.
3. Whether legacy `75524b3e` rows still exist, and the actual consumed-copy
   identity, content binding, and status under the exact reviewed J-4p/P04
   read contract. Issued notices and local fixture rows do not measure this.
4. A SHA-256-bound independent acceptance receipt for each applicable item
   and step, preserving original dependencies and subsequent-rebuild
   staleness discipline. Detector/model reconciliation follows the accepted
   readback; changing a regex does not earn a pin.

P04 already records these limits at `PACKET_J-W4-P04_v1.md:33–43`.
Its `:41` cites issued release `SUVARNA-L0L2-CLOSE-REV30-20261013` and the
archived `fast/RELEASE_RECEIPT.final.json`. This job re-read that archive:
its five condition statuses say SATISFIED. That historical record is not a
fresh production observation or consumed-copy acceptance.

Q17 Q6 (`SURROGATE_ANSWER_17.md:25–27`) supplies a disposition when genuine
historical receipts cannot be found. P04 `:47–51` already records A2.5/A2.6 as
“superseded by the 5.0 settled baseline — explicit surrogate disposition, not
done.” The supplied item descriptions still call Q6 owner-open. The cockpit
must reconcile that declaration through its governed acceptance process;
this handoff changes no dependency, outcome, or tracker detector. A genuine
historical receipt may instead be bound if subsequently located.

## Local verification

The inherited heads were checked against the supplied `PORT_MANIFEST.json`:
PR #2903 at `5a46c9c97e61e86dde56c3608032431b9a9ff0e0`, PR #3116 at
`936f4fc5093cae31fe6aebdd0ae4b0e391d1a1d3`. All 75 AM-10 and 11 C50 inherited
test declarations remain present, with no per-test assertion-count decreases.
This structural audit supplements execution; it does not claim AST identity.

Fresh execution from `platform/python-sidecar`:

```sh
python3 -B -m pytest tests/l3/gochara_rules/test_am10_repin_tool.py \
  tests/l3/gochara_rules/test_c50_settled1_intake.py -q -p no:cacheprovider \
  --basetemp="$JOB_SCRATCH/tmp/ported"
```

Result: **159 passed**, including both guarded AM-10 database cases. Environment:
`KALA_REQUIRE_DB=1`, `KALA_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres`,
`GOCHARA_REQUIRE_DB=1`,
`GOCHARA_A51_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55433/gochara_a51_test`,
`SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`, `PYTHONDONTWRITEBYTECODE=1`, and
`TMPDIR=$JOB_SCRATCH/tmp`. Each fixture created and dropped its own isolated
database. The shared cluster was not stopped or reconfigured.

Static CI guard command from repository root:
`python3 -B -m pytest platform/scripts/governance/__tests__/test_ci_changes.py -q -k am10 -p no:cacheprovider`
with its basetemp inside the job folder: **7 passed, 118 deselected**.
AM-10 already runs in the mandatory DB command (`.github/workflows/ci.yml:1701–1723`);
C50 is collected by the existing sharded `pytest tests/` command (`:2436`).
No CI path entry or workflow change is needed.

Twelve isolated source reversions were executed in job-folder tree copies.
Each produced assertion failures with exit 1; its fixed-tree counterpart
passed with exit 0, with no setup errors or skips:

| Existing behavior | Failing assertions after reversion |
|---|---:|
| AM-10 historical acquisition, including both real DB cases | 3 |
| AM-10 single-build refusal | 1 |
| AM-10 complete mechanical preflight | 1 |
| AM-10 full-precision boundary measurement/capture | 2 |
| AM-10 snapshot stability with rollback/close | 1 |
| AM-10 local independent verifier-pin update | 1 |
| C50 governed chart/full-run authority | 8 |
| C50 one-sided window clipping | 4 |
| C50 rebuilt reference rows matched by structure | 1 |
| C50 distinct per-subject natal identities | 2 |
| C50 lord/count refusal | 2 |
| C50 expected-shift refusal | 2 |

Evidence is retained under the supplied job folder
`X-20261016T073511Z-pb-j4a`: `source-evidence.json`, `port-audit.json`,
`ported-tests.log/xml`, `ci-static.log`, `mutation-proofs.json`,
`verify_mutations.py`, and `revert-proofs/`. These verify already-merged
behavior; no new production finding is claimed fixed.

An initial overbroad CI-classifier run was terminated after identifying that
its unrelated fixture tests invoke Git-writing commands in job scratch.
That selection violated the job's Git-write restriction. It is excluded from
passing verification; the subsequent seven-test selection uses only static
CI guards. The working-copy branch/index were not changed by those fixtures.

## Interpretations and closure boundary

(I) INTERPRETATION I-J4A-1: `built` in the job result means the two code children
are already built on main and were locally reverified. `done` means this
preparation/handoff is complete. Neither word supplies independent review,
CI admission, production activation, or aggregate J-4a acceptance. Alternative:
duplicate the absorbed ports; rejected because the intended code is present.

(I) INTERPRETATION I-J4A-2: production-only and external-acceptance obligations
are left out under this job's pre-build instruction. Alternative: emit pending
receipts at the detector paths; rejected because placeholders could be mistaken
for earned evidence and those paths are outside the job's write boundary.

The campaign-level session protocol remains with the cockpit (charter
`KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:295,302`). No separate validated
SESSION_CLOSE is claimed. Transient test directories are removed; proof copies
and logs remain for independent review. The supplied worktree remains for the
cockpit to commit and land. No production operation was performed.
