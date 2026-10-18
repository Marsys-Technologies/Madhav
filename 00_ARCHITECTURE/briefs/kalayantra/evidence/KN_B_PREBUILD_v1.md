---
artifact: KN_B_PREBUILD
version: "1.1"
status: BUILT_WAITING_ON_GATE
changelog: "1.1 (2026-10-16): PR #3640 non-blocking dispositions; current packet pins/citations and distinguishing admission proof. 1.0: custody, offline reconciliation and sharing-gap reproduction."
---

# KN-B preparation evidence

This bundle prepares KA3B-N1, KA3B-N2 and K5-G1b-N1 under A6 D-40. It does not
restore unavailable originals, register family children, change an accepted parent,
activate a candidate, or complete shared preparation. The D-17 children retain
their original `depends_on` and independent-review gates.

## KA3B-N1: custody with an explicit missing original

[KN_B_PREBUILD_v1.json](KN_B_PREBUILD_v1.json) lists exact local artifact paths and
SHA256 digests. The original builder
`X-20261015T172345Z-prebuild-ka-3b` directory is absent at inspection. Its
`result.json`, interpretations and original per-behavior receipts cannot be
restored from the available inputs; their digest is unknown, not invented.
**Original-builder restoration is left out.** The cockpit must recover the
original artifacts from its own archive if they survive, preserving provenance.

The eight mutations in the `X-20261015T184912Z-review-ka-3b` review are independent
review receipts. They are not original builder receipts or exhaustive proof of
every adapter obligation. The later annual-coverage repair builder's result and
its independent acceptance belong to KA3B-R1, not to the original build.
The CI-repair review at `0947299e4ffbf0931414084bd6cbf501a5dfb8c6` covers only its
stated two-commit delta. No accepted parent is reopened by this custody record.

`kn_b_reconcile.py --verify-custody` verifies available bytes against the pinned
digests and reports the missing original separately. Digest equality establishes
byte custody; the independent reviewer must authenticate authorship, artifact
roles and head/merge mappings. No local path's existence establishes acceptance.

## KA3B-N2: offline reconciliation, separate from closure

The baseline is main commit `ef14167bcc35a321b11d4d189a6b752bf3c658b8`.
`00_ARCHITECTURE/control/kalayantra/plan_model.json:3484` still declares KA-3b as a
branch-merged code item. The parent packet §1/§6 requires an independently
accepted family/wiring join. This preparation leaves that accepted model state
intact. Its D-17 carry-forward children depend on KA-3b and must never be added as
prerequisites of KA-3b, which would create a cycle.

The JSON bundle records the original upstream dependencies (`D-R8`, `J-0m`,
`KA-3a`) and every baseline downstream waiter. Its `children` list is empty:
no actual five-child correspondence or completion receipts were supplied.
The offline checker correctly reports these gaps. It has no tracker import,
write path, stored status, launch step or authority to close an item.

Run from the repository root:

```sh
python3 -B 00_ARCHITECTURE/briefs/kalayantra/evidence/kn_b_reconcile.py \
  --model 00_ARCHITECTURE/control/kalayantra/plan_model.json \
  --evidence 00_ARCHITECTURE/briefs/kalayantra/evidence/KN_B_PREBUILD_v1.json \
  --verify-custody
```

The packet admission checker now admits the preparation packet after refreshing
the three inherited stale source pins (plan model, algorithm elevations and judge
writer), their moved line references and the packet hash. The historical JSON
bundle's source-model hash still identifies its original inspected snapshot.
Admission does not establish child registration, runtime acceptance or activation.

`kn_b_reconcile.py` exit 1 means missing or inconsistent offline evidence; it is expected for this
snapshot. The cockpit supplies an audited proposal/bundle with actual registered
IDs when available. Preserve the pinned baseline dependency/waiter lists when
preparing that proposal. Reconcile all four family roles and independent judge
vedha wiring, their bounded ownership, original edges, exact-head independent
acceptance, reviewed-head-to-squash mapping, required merge-head readback and
existing join declaration. Reject duplicate roles/items, extra unmapped family
or wiring dependencies, mixed family ownership, missing heads/artifacts/digests,
skips, cycles and premature branch-only closure. The baseline source hash in the
bundle identifies the inspected model; it is historical, not a freshness claim.

Each child entry in this **new offline input format** has `role`, actual `item`,
reviewed `head` and a `receipt` path/digest. Its digest-bound receipt contains
`item`, `head`, `verdict`, `author`, `reviewer`, `state`, `merge_sha`,
`readback_required`, and `readback` (`head`, `verdict`) where required. This is a
reviewer's reconciliation bundle, **not an existing tracker receipt API**.
Authenticating the evidence against the real review and tracker remains mandatory;
passing synthetic fixtures never establishes live wiring or parent completion.

Tests are discovered automatically under
`platform/scripts/governance/__tests__/test_ky_kn_b_reconciliation.py` by the
required governance shards (`ci_shard.py`). No explicit workflow path is added.
After PR #3588, `platform/scripts/governance/ci_discovery.py` and
`ci_test_suites.json` supply CI profile discovery as well. The governance shards
discover this test file automatically; no workflow or generated output is edited.

**(I) INTERPRETATION:** pre-build offline custody/reconciliation while preserving
accepted-parent state. Alternative: convert the accepted parent in this child job,
contrary to D-17's carry-forward rule and the cycle constraint.

## K5-G1b-N1: reproduced unfinished integration

The original finding remains observable on main (`34c7e1acb`, PR #3548):

- `platform/python-sidecar/services/ka_kshetra/writer.py:2084` prepares a new
  field accumulator per class.
- `platform/python-sidecar/services/kala_core/measure/field.py:141` constructs
  `FieldPreparation` with class-specific experiment metadata and shared offsets.
- `platform/python-sidecar/services/ka_kshetra/stage5_null.py:348` invokes full
  reference geometry construction for each field draw.
- `platform/python-sidecar/services/kala_core/measure/__init__.py:205` prepares
  the jury's witness segments; `services/ka_sangam/jury/agreement.py:79` consumes
  that separate preparation.

The pinned job-local reproduction uses two classes and three non-identity draws:
two field preparations and six full geometry builds, with the same offsets as the
jury but no consumption of its `Preparation`. Requiring once-per-candidate shared
preparation fails. The artifact paths/digests and the runnable reproducer are in
the JSON custody bundle. This is a small structural observation, not a benchmark.

The tracked `test_g1b_measure.py` additions distinguish the experiments with a real
field: the jury anchor remains fixed while the transit hump shifts; the field
keeps its natal/clock terms. Two class-specific full-reference nulls retain their
own statistics, bitwise maxima and pooled quantiles. Replacing these with a jury
statistic would change the estimand; merely sharing a schedule cannot satisfy
PLAN §6.2(5). No performance, cross-consumer geometry sharing, full candidate
reuse, runtime qualification or scientific PASS is claimed.

**(I) INTERPRETATION:** this item's explicit preparation/carry-forward scope
requires reproducing the integration gap and preserving the reviewed behavior.
Alternative: substitute the jury's conditioned witness geometry for the field's
transit/obstruction geometry. Full once-per-candidate integration remains for the
final jury/field contract and candidate-bound persistence/resume evidence.

All live-admission, protected-window, independent acceptance, readback,
publication and parent-completion prerequisites remain in force. Local fixture
proofs never discharge them. The existing campaign handshake is inherited; this
bundle does not close the campaign.

## PR #3640 non-blocking dispositions (2026-10-16)

The reviewed source is `c89bce40b62bfc07d38c6b30dea51fdd1afb25bb`;
this stacked job starts at its main-merge head
`4cc67f4e12a08608c3fe9f84e2d1fd48dc21ce36` and addresses the four observations in
`X-20261016T152150Z-review2-pb-kn-b/REVIEW.md:21–24`.
Fresh receipts are retained under
`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261016T155640Z-nb-knb/`.

| Finding | Disposition and evidence |
|---|---|
| KA3B-N1 | **No code change:** the original result is still absent at the path pinned in `KN_B_PREBUILD_v1.json:28`; `custody-reconciliation.log` reports `original_builder_available=false` and no available-artifact digest errors. Neither independent reviews nor this job can supply the missing builder's authorship, interpretations or receipts. Keep the null digest; cockpit archive recovery remains owed. |
| KA3B-N2 | **No code/state change:** `plan_model.json:3484–3539` still records branch-merged acceptance, and `KN_B_PREBUILD_v1.json:25` supplies no children. The fresh reconciliation reports the missing parent join and all five correspondences. The synthetic rejection tests continue to enforce independent exact heads, merge/readback mappings, edges, cycles and ownership. Inventing completion data or making the checker green would violate §N.8. Actual registration and authenticated acceptance remain cockpit work. |
| K5-G1b-N1 | **No runtime change:** `shared-preparation-observation.log` again records two preparations and six geometry builds for two classes/three draws. `--require-shared` still fails. `test_g1b_measure.py` verifies fixed jury-anchor conditioning, shifted field transits, retained natal/clock terms, and bitwise class-specific maxima/quantiles. This is evidence of the outstanding integration, not a sharing fix. |
| PBKNB-N1 | **Fixed:** preparation packet v1.2 pins the observed bytes and current source locations; the real admission CLI passes. The job-local admission regression first failed on exactly the three stale pins. `PBKNB-N1-proof.json` records exact pre-change packet bytes in `PBKNB-N1-reverted-tree` (exit 1) and fixed packet bytes in `PBKNB-N1-fixed-tree` (exit 0), with identical current source files in both copies. |

**(I) INTERPRETATION:** use the job's explicit no-code disposition option for the
three evidence/integration observations; do not report their underlying runtime
or cockpit obligations complete. Alternative: treat this review job as proof of
historical authorship, authenticated child acceptance or shared geometry.
The current K5-G1b-N1 brief (`plan_model.json:28016–28032`) explicitly requires
independent reproduction while preserving the reviewed field behavior. Merely
caching offsets would leave repeated geometry work; substituting jury draws
would change the field estimand. The eventual implementation must share
candidate-bound input preparation across the three separately conditioned
experiments and prove content-bound resume (architecture plan §6.2(5,7)); these
receipts confer no performance or runtime-qualification claim. This is a recorded
no-code disposition for this preparation review, not a waiver of that work.

The admission regression is job-local: permanently requiring this historical
packet to match every future plan-model revision would impose a new campaign
freshness gate. Existing reconciliation and field tests remain CI-discovered;
only the packet and this evidence explanation change in the branch.
