"""K9-6: real SQL on the suite's guarded, automatically dropped database."""
import os
from pathlib import Path
import shutil
import subprocess


def test_public_views_and_sentinel_on_guarded_postgres(kala_db_dsn):
    root = Path(__file__).resolve().parents[5]
    package = root / 'platform'
    # A single seven-view case starts seven guarded Python SQL transports.
    # Keep its startup allowance separate from the 120s whole-suite bound.
    result = subprocess.run([shutil.which('node'), 'node_modules/vitest/vitest.mjs', 'run', '--no-cache', '--testTimeout=30000',
        'src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts',
        'src/lib/retrieval/registry/layers/L3_kala/published_request.test.ts'],
        cwd=package, env=os.environ | {'KALA_VIEW_FIXTURE_DSN': kala_db_dsn, 'KALA_VIEW_DB_TESTS': '1'},
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'skipped' not in result.stdout, result.stdout
    # Installed SDK shapes and unchanged legacy envelopes run in the MCP
    # package's native Vitest environment; DB discovery owns this gate too.
    result = subprocess.run([shutil.which('node'), 'node_modules/vitest/vitest.mjs', 'run', '--no-cache',
        '--config', 'src/tools/kala_views/registry_alias.vitest.config.ts',
        'src/tools/kala_views/published_request.test.ts',
        'src/tools/kala_views/legacy_alias_golden.test.ts'],
        cwd=root / 'platform-mcp', env=os.environ, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'skipped' not in result.stdout, result.stdout
