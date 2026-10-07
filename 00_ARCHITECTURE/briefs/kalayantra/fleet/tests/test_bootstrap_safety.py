"""B-3b executable safety cases for the campaign finalizer and executor."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def test_finalizer_failure_and_acceptance_cases():
    subprocess.run([sys.executable, str(HERE / 'finalizer_cases.py')], check=True, timeout=30)

def test_executor_lock_process_group_and_fence_cases():
    subprocess.run([sys.executable, str(HERE / 'executor_cases.py')], check=True, timeout=30)


def test_local_db_seeds_governed_asset_registry_before_full_migration_runner():
    """A schema-only seed has no registry rows, so migration 1320 must see the governed seed first."""
    helper = HERE.parent / 'local_db.sh'
    source = helper.read_text()

    seed_index = source.index('seed_governed_asset_registry "$url"')
    runner_index = source.index('npx tsx scripts/migrate.ts')

    assert seed_index < runner_index
    assert 'scripts/seed/asset_registry_seed.ts' in source
