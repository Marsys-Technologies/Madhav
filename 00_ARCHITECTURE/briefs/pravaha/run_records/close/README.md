---
artifact: PRAVAHA_CLOSE_PREPARATION
version: "1.0"
status: BUILT_WAITING_ON_GATE
changelog: "1.0 (2026-10-16): A6 D-40 J8 offline tooling/templates; no activation."
---

# J8 close preparation

This folder prepares **J-8, J-8-b63, J-8-j3 and J-8a**. It does not complete them.
The CLI uses only explicitly supplied local files. It has no tracker mutation,
database, Git, network, production, or subprocess interface. Nothing in this
pre-build updates CURRENT_STATE, SESSION_LOG, the tracker model or its events.
No migration, ephemeris computation or database suite is needed.

## Authority and scope

- Root `CLAUDE.md` §I and §N.8: preserve facts and earned signals.
- `00_ARCHITECTURE/control/pravaha/plan_model.json:1410`: B6.3 retains
  A6.2, A6.3, B6.1 and B6.2; `:1452`: J3 retains B6.3.
- The inherited plan is preserved in
  `../2026-10-06/worktree_modified/PRAVAHA_CAMPAIGN_PLAN_v1_0.md:190`
  (B6.3), `:197` (J3), and `:246` (§9: historical tracker read-only).
- `00_ARCHITECTURE/control/kalayantra/plan_model.json:20204` (J-8a),
  `:20244` (J-8), `:26650` (J-8-b63), and `:26768` (J-8-j3): existing
  dependencies, typed artifact acceptance and phase-12 residuals are retained.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:94`
  (§2.3) preserves live run material for J-8a; `:341` (§14) describes the
  separate KĀLA-YANTRA final close.
- `SURROGATE_ANSWER_17.md` Q9, cited in the items' real briefs: Tier-2 is
  off the flip critical path. Non-entry needs an explicit disposition; B6.3,
  J3, J-8a and J-8 remain post-flip campaign-close work.

(I) INTERPRETATION: template generation uses filenames ending in `.template.json`
and `PRAVAHA_CLOSE_REPORT_DRAFT_v1_0.md`, outside the existing detector targets.
Generating a final-named file now would risk an early file-existence signal.
The final `PRAVAHA_CLOSE_REPORT_v1_0.md`, `J8A_PRAVAHA_FINAL.json` and residual
`J-8-b63.json` / `J-8-j3.json` are deliberately absent. Their generation and
controller publication remain later, independently accepted work.

## Prepare an offline review packet

Use the independently accepted J-0 disposition bytes supplied by the controller.
The example only writes into an explicit new directory inside the job folder:

```sh
python3 -B platform/scripts/governance/pravaha_close.py prepare \
  --disposition /Users/Dev/kalayantra/run/J0_DISPOSITION.json \
  --campaign-model 00_ARCHITECTURE/control/kalayantra/plan_model.json \
  --pravaha-model 00_ARCHITECTURE/control/pravaha/plan_model.json \
  --out-dir "$JOB_SCRATCH/j8-draft"
```

Outputs: one report draft, `close_rows.template.json`, and four item templates.
Every PR/state disposition gets its own row; proposals such as keep or salvage
never supply a final state. All input SHA-256 pins are included. Each template
keeps the current dependency list, the original B6.3/J3 lineage where applicable,
and empty prerequisite-evidence references. The template schema is a working
aid, **not a new controller receipt schema**. It must never be passed off as
`ky.accept/1`, a guarded completion proof or an independent artifact verdict.

Edit the row working aid with real final states and evidence references, then:

```sh
python3 -B platform/scripts/governance/pravaha_close.py check-rows \
  --rows "$JOB_SCRATCH/j8-draft/close_rows.template.json" \
  --disposition /Users/Dev/kalayantra/run/J0_DISPOSITION.json \
  --campaign-model 00_ARCHITECTURE/control/kalayantra/plan_model.json \
  --pravaha-model 00_ARCHITECTURE/control/pravaha/plan_model.json
```

Use the same arguments with `render` to print an updated Markdown draft to
stdout. Rendering stays DRAFT even if every row is filled. `check-rows` rejects
missing, extra or duplicate rows, changed proposals, drifted input hashes,
nonterminal final states and blank evidence. It checks presence of evidence
references, not their truth; the reviewer must open them and bind their digests.

(I) INTERPRETATION: `done`, `not_applicable` and `superseded` are report labels,
not tracker transitions. An exception needs its reason and decision reference.
The alternative of treating parked/deferred/keep as terminal would fabricate
completion. Explicit Tier-2 non-entry remains a gap and never bypasses strict
original or current dependencies. Decisions and operational holds from the
accepted J-0 inventory also belong in the report's decisions/gaps section;
the PR/state row table alone does not establish their resolution.

## Prepare and verify an archive candidate

The controller first arranges a stable final capture of the **original Pravāha
tracker**, with an observed live `pravaha status` containing no nonterminal
item. Do not use a KĀLA-YANTRA snapshot or a stale CLI fallback as that proof.
The tool measures the exported snapshot against the supplied original model.
All model items must be covered exactly once; done/not_applicable are the only
terminal tracker labels, and a done item retains its strict dependency checks.
A missing reason/evidence, inconsistent dependency list, open dependency,
malformed/truncated log, mismatched event count/tail or model-error/restored
snapshot refuses the candidate **before creating the output directory**.
Historical tick errors remain in the archived snapshot for review; the tool
does not require them to be erased to make a terminal export archivable.

```sh
python3 -B platform/scripts/governance/pravaha_close.py archive-candidate \
  --pravaha-model "$JOB_SCRATCH/final-capture/plan_model.json" \
  --events "$JOB_SCRATCH/final-capture/EVENTS.jsonl" \
  --snapshot "$JOB_SCRATCH/final-capture/snapshot.json" \
  --material runner-B.log="$JOB_SCRATCH/final-capture/runner-B.log" \
  --material EVENTS-backup.jsonl="$JOB_SCRATCH/final-capture/EVENTS-backup.jsonl" \
  --out-dir "$JOB_SCRATCH/j8-archive-candidate"

python3 -B platform/scripts/governance/pravaha_close.py verify-archive \
  --archive-dir "$JOB_SCRATCH/j8-archive-candidate"
```

`--material NAME=PATH` is repeatable. Select all required runner logs, backups
and other run material explicitly from the reviewed capture inventory; the tool
does not sweep a live directory. See the bootstrap item's original preservation
list at `00_ARCHITECTURE/control/kalayantra/plan_model.json:910`. Never include
credentials or the two secret-scan-excluded files. Final EVENTS/snapshot/model
and selected materials are copied byte-for-byte; the candidate manifest records
each SHA-256 and byte count. Existing output directories are refused. Archive
verification recomputes every listed hash and rechecks the exported tracker.
Keep the independently reviewed manifest digest outside the archive: replacing
both a file and its local manifest cannot be detected by a self-check alone.

(I) INTERPRETATION: these checks measure supplied exports and archive integrity.
They do not prove detector semantics, live freshness, completeness of selected
run material, live read-only enforcement or independent acceptance. Accordingly
`run_material_inventory_complete`, `live_read_only` and `independent_acceptance`
remain null. The alternative of deriving these claims from a checksum or a
local exit code violates §N.8.

## Deferred close execution and acceptance

1. Earn J-0 / J-0m, V-J6 and every item-specific prerequisite at the original
   phase. Obtain real retirement, admitted Tier-2 or explicit non-entry, and L5
   hand-off evidence. A code merge is never a substitute for these artifacts.
2. Resolve all remaining original items through Pravāha's governed tracker.
   Preserve histories and explicit gaps; do not write fabricated done events to
   get an empty status list. Keep B6.3's CURRENT_STATE/SESSION_LOG/validated
   SESSION_CLOSE lineage and J3's B6.3 dependency.
3. Coordinate the staged report/governance updates and tracker-close capture.
   **There is a sequencing constraint:** J-8a precedes J-8-b63 in the current
   model, while a fully terminal original snapshot includes B6.3 and J3.
   (I) INTERPRETATION: pre-close drafts/captures may precede finalization, but a
   final archive check exempts neither row. The alternative of dropping B6.3/J3
   would hide the cycle. The cockpit must supply the governed staging/evidence
   ordering before any final J-8a assertion; this pre-build grants no edge waiver.
4. Leave the historical dashboard available and prove real mutation attempts
   are refused at every active write path. The existing HTTP server describes
   itself as read-only (`pravaha_tracker/server.py:11`), but CLI transitions
   append events (`pravaha_tracker/cli.py:174`, `:212`, `:295`). A dashboard,
   HOLD marker or file chmod alone is not proof of complete write refusal.
   This job neither invents nor activates a tracker read-only switch. The
   controller needs an authorized enforcement mechanism and independent negative
   tests against the actual write paths before it can earn this requirement.
5. Independently review the exact final archive/report bytes and their SHA-256.
   Use the existing typed artifact rule
   `v_artifact_digest_reviewer_not_author`; bind every dependency and required
   step. B6.3 and J3 need their own phase-12 independent artifact acceptances.
   Complete the controller-owned final evidence only after those gates, with
   real CURRENT_STATE and SESSION_LOG diffs and validated governance close.

Tests live at `platform/scripts/governance/__tests__/test_pravaha_close.py` and
are automatically included by the existing `ci_shard.py` discovery convention.
The job's mutation copies/logs and result remain in its job folder for review.
