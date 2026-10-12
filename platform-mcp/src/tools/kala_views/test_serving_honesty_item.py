"""Run K7-2's MCP goldens with the package's own Vitest and adapters."""
import pathlib
import shutil
import subprocess


def test_k7_2_native_mcp_honesty_and_legacy_goldens():
    package = pathlib.Path(__file__).resolve().parents[3]
    result = subprocess.run([
        shutil.which("node"), "node_modules/vitest/vitest.mjs", "run",
        "--config", "src/tools/kala_views/registry_alias.vitest.config.ts",
        "src/tools/kala_views/serving_honesty.test.ts",
        "src/tools/kala_views/story.test.ts",
        "src/tools/kala_views/legacy_alias_golden.test.ts",
        "src/tools/kala_views/registry_contract.test.ts",
        "src/__tests__/kala_now_get_c4_narrative.test.ts",
    ], cwd=package, capture_output=True, text=True, timeout=30, check=True)
    assert "5 passed" in result.stdout, result.stdout
