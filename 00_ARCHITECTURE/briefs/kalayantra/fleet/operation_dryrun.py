#!/usr/bin/env python3
"""Bounded preparation DRY RUN; performs no DB, cloud or workflow action.

These descriptors do not confer an executor kind or earn dry_run_passed. Real
rollback/rehearsal evidence and child-allocated bindings are phase prerequisites.
See W4_EXECUTOR_BINDINGS.md for source contracts and missing interfaces.
"""
from __future__ import annotations
import argparse
import json

SURFACES = {
    "measuring_dispatch": {
        "args": {"run": "all_classes_full", "classes": "all"}, "caps": ["builder", "gcloud"],
        "runtime_principal": "data_plane_builder", "phase": "J-3a / J-3c",
        "source": "platform/scripts/dispatch_v5_measuring_job.py",
        "blockers": ["independent source review, campaign gate and phase enablement for the disabled measuring kinds",
                     "approved canonical offline input and deployment-faithful builder-role rehearsal",
                     "accepted density/cap projection and Cloud Run timeout readback"]},
    "century_dispatch": {
        "args": {"classes": "all"}, "caps": ["gcloud"], "runtime_principal": "data_plane_builder", "phase": "J-4d / J-4e",
        "source": "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json",
        "blockers": ["allocate final-rules 5.0 launch and dry-run binding through a real child; legacy century entry is 4.1",
                     "P06b qualification, D-G9, measured cap/timeout and D-CLOUD", "confirm whether staging adds builder capability"]},
    "verification_job": {
        "args": {"generation": "5.0"}, "caps": ["gcloud"], "runtime_principal": "gochara_verifier", "phase": "phase 10, after P06b",
        "source": "platform/python-sidecar/pipeline/orchestrator/verification_job.py",
        "blockers": ["allocate reviewed remote job launcher and dry-run kind through a real child",
                     "verify disabled deployed definition, immutable image and verifier-only runtime secret",
                     "report-only is REPORT_ONLY, never VERIFIED or a seal brief"]},
    "protected_apply": {
        "args": {}, "caps": [], "runtime_principal": "protected workflow ownership-admin", "phase": "J-4b-a55j / P06b",
        "source": "platform/scripts/kala_protected_migrations.txt",
        "blockers": ["proposal only: allocate kind, exact migration allowlist/hash and protected workflow through a real child",
                     "inspect applied receipts first; never reapply or edit an applied migration",
                     "human protected-environment approval is an external dependency"]},
    "provision": {
        "args": {}, "caps": [], "runtime_principal": "protected workflow ownership-admin", "phase": "J-4c-a55m",
        "source": ".github/workflows/gochara-role-provisioning-oneshot.yml",
        "blockers": ["proposal only: allocate kind, bounded role/job stage and workflow request through a real child",
                     "verify actual existing roles/grants first; do not rerun one-shot role creation",
                     "human approval; no executor credential grants or secrets access are implied"]},
    "seal": {
        "args": {}, "caps": [], "runtime_principal": "gochara_sealer in protected workflow only", "phase": "J-5s after P06b",
        "source": ".github/workflows/gochara-seal-approved.yml",
        "blockers": ["proposal only: allocate workflow dispatch kind and immutable request contract through a real child",
                     "human gochara-seal approval, exact run/attempt/brief/execution envelope and live gate proof",
                     "verifier and sealer credentials remain exclusively in their own runtime identities"]},
}


def prepare(kind, args):
    if kind not in SURFACES:
        raise ValueError("unallocated preparation surface")
    entry = SURFACES[kind]
    if args != entry["args"]:
        raise ValueError("request must match the bounded arguments exactly; no extra arguments")
    proposal = kind in ("protected_apply", "provision", "seal")
    return dict(schema="ky.operation_preparation/1", kind=kind, status="PREPARATION_ONLY", enabled=False,
                binding_status="PROPOSAL_REQUIRES_CHILD" if proposal else "DISABLED_PENDING_PHASE",
                chart_id="482012f1-710e-4a25-994a-93821f5871aa", generation="5.0", args=dict(args),
                executor_capabilities=list(entry["caps"]), runtime_principal=entry["runtime_principal"],
                enable_at=entry["phase"], source=entry["source"], blockers=list(entry["blockers"]),
                external_human_approval_required=proposal, dry_run_passed=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", required=True, action="store_true")
    parser.add_argument("--kind", required=True, choices=tuple(SURFACES))
    parser.add_argument("--run")
    parser.add_argument("--classes")
    parser.add_argument("--generation")
    args = parser.parse_args(argv)
    request = {key: getattr(args, key) for key in ("run", "classes", "generation") if getattr(args, key) is not None}
    try:
        print(json.dumps(prepare(args.kind, request), sort_keys=True))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
