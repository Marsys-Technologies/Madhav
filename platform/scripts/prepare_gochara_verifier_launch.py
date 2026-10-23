#!/usr/bin/env python3
"""Prepare J-5s's disabled full-generation verifier launch from supplied readbacks.

No cloud/DB client, credential, allocation, dispatch or acceptance operation.
This descriptor is review input. G8 and a reviewed executor child must still
bind the real launch, executed resource and independent SQL/verdict evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

import gochara_verification_job_readback as readback

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
IMAGE_REPO = 'asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline'
SERVICE_ACCOUNT = 'gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com'
SECRET_NAME = 'gochara-verifier-db-url'
CLOUDSQL_INSTANCE = 'madhav-astrology:asia-south1:amjis-postgres'
Refused = readback.Refused


def document_digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def prepare(definition, *, reviewed_commit, image_digest, v2_job=None):
    problems = readback.check(definition, image_repo=IMAGE_REPO, image_digest=image_digest,
        service_account=SERVICE_ACCOUNT, runner_commit=reviewed_commit, secret_name=SECRET_NAME,
        cloudsql_instance=CLOUDSQL_INSTANCE, timeout_seconds=28800, memory='4Gi', cpu='1', v2_job=v2_job)
    if problems:
        raise Refused('verifier definition refused: ' + '; '.join(problems))
    expected_args = ['--chart', CHART, '--generation', '5.0']
    return dict(schema='ky.j5s_verifier_launch_preparation/1', status='PREPARATION_ONLY',
        enabled=False, dry_run_passed=False, production_allocation=None,
        runtime_principal='gochara_verifier', service_account=SERVICE_ACCOUNT,
        reviewed_commit=reviewed_commit, image_digest=image_digest,
        definition_sha256=document_digest(definition),
        v2_definition_sha256=None if v2_job is None else document_digest(v2_job),
        expected_args=expected_args,
        argv=['gcloud', 'run', 'jobs', 'execute', 'gochara-verification-job', '--project',
              'madhav-astrology', '--region', 'asia-south1', '--args=' + ','.join(expected_args),
              '--async', '--format=value(metadata.name)'],
        activation_requires=['P06b', 'campaign-coordination', 'backup_restore_verified', 'dry_run_passed',
            'one_build_slot', 'independent_pre_acceptance', 'reviewed_launcher_allocation'],
        completion_requires=['executor_receipt', 'executed_resource_readback',
            'full_manifest_all_included_grains_verified', 'approval_bound_seal',
            'independent_readback_sql_same_manifest_execution_run_attempt', 'independent_verdict'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--job-file', required=True)
    parser.add_argument('--v2-job-file')
    parser.add_argument('--reviewed-commit', required=True)
    parser.add_argument('--image-digest', required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.job_file, encoding='utf-8') as handle:
            definition = json.load(handle)
        v2_job = None
        if args.v2_job_file:
            with open(args.v2_job_file, encoding='utf-8') as handle:
                v2_job = json.load(handle)
        result = prepare(definition, reviewed_commit=args.reviewed_commit,
                         image_digest=args.image_digest, v2_job=v2_job)
    except (Refused, OSError, ValueError, TypeError, KeyError):
        # Never echo a malformed supplied document: it may contain a credential.
        print('verifier launch preparation refused: invalid definition or binding', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
