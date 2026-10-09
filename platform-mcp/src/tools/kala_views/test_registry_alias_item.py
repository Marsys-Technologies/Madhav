"""Run the MCP item tests in their native package from the normal item precheck."""
import pathlib
import shutil
import subprocess


def test_k7_native_mcp_contract_and_legacy_goldens():
    package = pathlib.Path(__file__).resolve().parents[3]
    result = subprocess.run([
        shutil.which("node"), "node_modules/vitest/vitest.mjs", "run",
        "--config", "src/tools/kala_views/registry_alias.vitest.config.ts",
        "src/tools/kala_views/registry_alias.test.ts",
        "src/tools/kala_views/legacy_alias_golden.test.ts",
        "src/tools/kala_views/registry_contract.test.ts",
    ], cwd=package, capture_output=True, text=True, timeout=30, check=True)
    assert "3 passed" in result.stdout, result.stdout
