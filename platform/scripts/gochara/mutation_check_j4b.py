#!/usr/bin/env python3
"""J4B preparation mutations: copy source under JOB_SCRATCH; never edit the tree.

Run from any directory with --scratch "$JOB_SCRATCH/j4b-mutations". Every case
must pass on the fixed copy and fail on its own mutated copy. No Git writes,
network tools, cluster startup, production access or operation receipts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WINDOW = 'platform/scripts/gochara-window-readbacks.sh'
FN = 'platform/scripts/fn-1235-readbacks.sh'
AUDIT = 'platform/scripts/readbacks/gochara_provisioning_readback.sql'
WINDOW_TEST = 'platform/scripts/__tests__/test_gochara_window_readbacks.py'
FN_TEST = 'platform/scripts/__tests__/test_fn_1235_readbacks.py'
M1204 = 'platform/migrations/1204_gochara_av_qualifier_object_role.sql'
M1378 = 'platform/migrations/1378_gochara_verifier_sealer_inventory_grants.sql'
IAM = 'platform/scripts/data-plane-secret-isolation-preflight.ts'
ROUTE = 'platform/src/app/api/cockpit/refresh/route.ts'


def py(suite, expression):
    return ('python', suite, expression)


def ts(suite, expression=''):
    return ('vitest', suite, expression)


# Exact executable changes, not renamed tests or replacement test expectations.
# The two revert cases are the full production reversions of this job's fixes.
CASES = [
    ('J-4b-pr2817', 'am7-check', M1204, "     'av_qualifier'));", "     'removed_av_qualifier'));",
     ts('tests/unit/migrations/gochara_b6_v15_contract_static.test.ts', 'widens kgrr')),
    ('J-4b-pr2817', 'am7-selector', M1204, "                     'av_qualifier'])", "                     'removed_av_qualifier'])",
     ts('tests/unit/migrations/gochara_b6_v15_contract_static.test.ts', 'selector fold')),
    ('J-4b-pr2817', 'protected-runner', 'platform/scripts/migrate.ts', "  '1204_gochara_av_qualifier_object_role.sql',\n", '',
     ts('tests/unit/migrations/gochara_b6_v15_contract_static.test.ts', 'routine runner refuses')),
    ('J-4b-pr2817', 'protected-deploy-order', '.github/workflows/deploy.yml', 'migrations+=(1204_gochara_av_qualifier_object_role.sql)', ': # omitted 1204',
     ts('tests/unit/migrations/gochara_b6_v15_contract_static.test.ts', 'window applies 1204')),
    ('J-4b-pr2949', 'publication-columns', M1378, '["status","published_at","content_digest","row_counts"]', 'null',
     ts('tests/unit/migrations/gochara_b6_1241_verifier_sealer_grants_static.test.ts', 'COLUMN-LEVEL UPDATE')),
    ('J-4b-pr2949', 'registry-read-grant', M1378, '["ka_gochara_predicate","SELECT",null,"1378"]', '["ka_gochara_predicate","UPDATE",null,"1378"]',
     ts('tests/unit/migrations/gochara_b6_1241_verifier_sealer_grants_static.test.ts', 'v7')),
    ('J-4b-pr3083', 'target-refusal', ROUTE,
     "    if (rows.length === 0) {\n      return NextResponse.json({ error: 'scope_target is not an active asset' }, { status: 400 })\n    }\n", '',
     ts('src/app/api/cockpit/refresh/__tests__/route.authz.test.ts', 'REFUSES')),
    ('J-4b-pr3083', 'active-registry-filter', ROUTE, 'WHERE asset_id=$1 AND is_active = true', 'WHERE asset_id=$1',
     ts('src/app/api/cockpit/refresh/__tests__/route.authz.test.ts', 'ACTIVE asset target')),
    ('J-4b-pr3089', 'readonly-refusal', WINDOW, 'if [ "$ro" != "on" ] || [ "$dro" != "on" ]; then', 'if false; then',
     py(WINDOW_TEST, 'test_readonly_refusal_exit2')),
    ('J-4b-pr3089', 'pinned-sql', WINDOW, 'if [ "$got" != "$pinned" ]; then', 'if false; then',
     py(WINDOW_TEST, 'test_tampered_file_is_refused_before_execution')),
    ('J-4b-pr3089', 'database-identity', WINDOW, 'if [ "$db" != "$EXPECT_DB" ]; then', 'if false; then',
     py(WINDOW_TEST, 'test_expect_db_pass_and_refusal')),
    ('J-4b-pr3089', 'principal-preread', WINDOW, '    run_check check_roles_exist\n', '',
     py(WINDOW_TEST, 'test_pre_train_all_pass')),
    ('J-4b-pr3108', 'ledger-c-sort', WINDOW, '<(LC_ALL=C sort "$OUT/$id-current.out")', '"$OUT/$id-current.out"',
     py(WINDOW_TEST, 'test_ledger_diff_passes_when_the_db_order_is_not_the_c_order')),
    ('J-4b-pr3108', 'runner-digest', WINDOW, 'shasum -a 256 "$0" | awk', 'printf "wrong\\n" | awk',
     py(WINDOW_TEST, 'test_runner_sha256_is_written_into_the_evidence')),
    ('J-4b-pr3114', 'fn-owner', FN, '_expect_row owner "amjis_app" owner', ': # owner check omitted',
     py(FN_TEST, 'test_wrong_owner_stops')),
    ('J-4b-pr3114', 'fn-public', FN, '_expect_row acl_public_entries "0" acl-no-public', ': # public check omitted',
     py(FN_TEST, 'test_public_entry_stops')),
    ('J-4b-pr3114', 'fn-grant-option', FN, '_expect_row acl_non_owner_grant_options "0" acl-no-grant-option', ': # grant option check omitted',
     py(FN_TEST, 'test_grant_option_stops')),
    ('J-4b-pr3114', 'fn-ledger', FN, '_expect_row ledger "$LEDGER_NAME\t$SHA_1235" ledger', ': # ledger check omitted',
     py(FN_TEST, 'test_a_wrong_ledger_sha_stops')),
    ('J-4b-pr3114', 'fn-exact-acl', FN, 'if [ "$got_acl" = "$want_acl" ]; then', 'if true; then',
     py(FN_TEST, 'test_an_extra_grantee_stops')),
    ('J-4b-pr3119', 'firebase-missing', IAM, "if (verifierControlOnly && binding.role === 'roles/firebase.managementServiceAgent')", "if (false && binding.role === 'roles/firebase.managementServiceAgent')",
     ts('tests/unit/data_plane_verifier_secret_isolation.test.ts', 'C53')),
    ('J-4b-pr3119', 'firebase-builder-leak', IAM, "if (verifierControlOnly && binding.role === 'roles/firebase.managementServiceAgent')", "if (binding.role === 'roles/firebase.managementServiceAgent')",
     ts('tests/unit/data_plane_verifier_secret_isolation.test.ts', 'cross-gate')),
    ('J-4b', 'public-original-revert', WINDOW,
     "EXISTS (SELECT 1 FROM aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')",
     "has_function_privilege('PUBLIC', p.oid, 'EXECUTE')",
     py(WINDOW_TEST, 'test_public_execute_query_checks_the_public_acl_without_a_public_role')),
    ('J-4b', 'audit-original-revert', AUDIT, None, None,
     py(WINDOW_TEST, 'test_provisioning_readback_enumerates_every_principal_and_grant')),
    ('J-4b', 'audit-false-green', AUDIT, 'observed IS NOT NULL AND observed = expected AS ok', 'true AS ok',
     py(WINDOW_TEST, 'test_provisioning_readback_refuses_privilege_or_principal_drift')),
]


CASES += [
    ('J-4b-pr2817', 'am7-live-replay', M1204,
     "AND starts_with(m.filename, '1204_')", 'AND false',
     ts('tests/integration/gochara_b6_v15_migrations.db.test.ts', 'replay is BLOCKED')),
    ('J-4b-pr3108', 'holder-c-sort', WINDOW,
     ['run_sql_sorted W2a-recheck', '<(LC_ALL=C sort "$OUT/W2a-recheck.out")'],
     ['run_sql W2a-recheck', '"$OUT/W2a-recheck.out"'],
     py(WINDOW_TEST, 'test_w2a_recheck_passes_when_the_db_order_is_not_the_c_order')),
    ('J-4b-pr3108', 'trigger-c-sort', WINDOW,
     ['run_sql_sorted "W6-$label"', '<(LC_ALL=C sort "$OUT/W6-post.out")'],
     ['run_sql "W6-$label"', '"$OUT/W6-post.out"'],
     py(WINDOW_TEST, 'test_w6_post_passes_when_the_db_order_is_not_the_c_order')),
]


def run(tree, selection, log, temp):
    runner, suite, expression = selection
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(temp))
    temp.mkdir(parents=True, exist_ok=True)
    if runner == 'python':
        cmd = [sys.executable, '-m', 'pytest', suite, '-k', expression, '-q', '-p', 'no:cacheprovider', '--basetemp=' + str(temp / 'pytest')]
        cwd = tree
    else:
        cmd = ['node', 'node_modules/vitest/vitest.mjs', 'run', suite, '--no-cache', '--no-file-parallelism']
        if expression:
            cmd += ['-t', expression]
        cwd = tree / 'platform'
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    output = result.stdout + result.stderr
    log.write_text(output)
    return result.returncode, cmd, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--case', action='append', default=[])
    args = parser.parse_args()
    job = os.environ.get('JOB_SCRATCH')
    if not job or not args.scratch.resolve().is_relative_to(Path(job).resolve()):
        parser.error('--scratch must be inside JOB_SCRATCH')
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=False)
    baseline = scratch / 'fixed-tree'
    baseline.mkdir()
    ignore = shutil.ignore_patterns('node_modules', '.next', '.venv', '__pycache__', '.pytest_cache', '.env*', '*.tsbuildinfo', '*.log')
    shutil.copytree(ROOT / 'platform', baseline / 'platform', ignore=ignore, symlinks=True)
    shutil.copytree(ROOT / '.github', baseline / '.github', ignore=ignore)
    fleet = Path('00_ARCHITECTURE/briefs/kalayantra/fleet')
    (baseline / fleet).mkdir(parents=True)
    shutil.copy2(ROOT / fleet / 'readback_sql.sh', baseline / fleet / 'readback_sql.sh')
    (baseline / 'platform/node_modules').symlink_to((ROOT / 'platform/node_modules').resolve())
    evidence = []
    cases = [case for case in CASES if not args.case or case[1] in args.case]
    if not cases:
        parser.error('no selected cases')
    for item, name, target, old, new, selection in cases:
        fixed_exit, fixed_cmd, _ = run(baseline, selection, scratch / (name + '.fixed.log'), scratch / (name + '-fixed-tmp'))
        if fixed_exit:
            raise RuntimeError(f'{name}: baseline failed; inspect {name}.fixed.log')
        copy = scratch / name
        shutil.copytree(baseline, copy, copy_function=os.link, symlinks=True)
        file = copy / target
        original = file.read_text()
        if old is None:
            file.unlink()
        else:
            replacements = zip(old, new) if isinstance(old, list) else [(old, new)]
            mutated = original
            for before, after in replacements:
                if before not in mutated:
                    raise RuntimeError(f'{name}: mutation target missing')
                mutated = mutated.replace(before, after)
            # Replace the inode so this copy's hardlinks cannot alter the baseline.
            file.unlink()
            file.write_text(mutated)
        revert_exit, test_cmd, output = run(copy, selection, scratch / (name + '.reverted.log'), scratch / (name + '-reverted-tmp'))
        caught = revert_exit != 0 and bool(re.search(r'(FAILED |\d+ failed)', output))
        record = dict(item=item, name=name, target=target, test=test_cmd, fixed_test=fixed_cmd,
                      fixed_exit=fixed_exit, revert_exit=revert_exit, copy_path=str(copy), caught=caught)
        evidence.append(record)
        (scratch / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(f'{"CAUGHT" if caught else "SURVIVED"} {item} {name}: fixed={fixed_exit} reverted={revert_exit}', flush=True)
        if not caught:
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
