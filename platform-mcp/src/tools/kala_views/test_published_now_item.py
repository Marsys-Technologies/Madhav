"""K7-3 published-state preparation: native MCP boundary plus legacy goldens."""
import pathlib
import shutil
import subprocess


def test_k7_3_published_now_and_unchanged_legacy_requests():
    package = pathlib.Path(__file__).resolve().parents[3]
    result = subprocess.run([
        shutil.which("node"), "node_modules/vitest/vitest.mjs", "run",
        "--config", "src/tools/kala_views/registry_alias.vitest.config.ts",
        "src/tools/kala_views/published_now.test.ts",
        "src/tools/kala_views/published_now_sql.test.ts",
        "src/tools/kala_views/serving_honesty.test.ts",
        "src/tools/kala_views/legacy_alias_golden.test.ts",
        "src/tools/kala_views/registry_contract.test.ts",
        "src/__tests__/kala_now_get_c4_narrative.test.ts",
    ], cwd=package, capture_output=True, text=True, timeout=30, check=True)
    assert "6 passed" in result.stdout, result.stdout
