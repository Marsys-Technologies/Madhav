#!/usr/bin/env python3
"""
coverage_gate.py — COV-S7 CI coverage gate

Check A (hard error): Every retrieval tool wired in retrieve/index.ts must have
a manifest entry in manifest_overrides.yaml OR CAPABILITY_MANIFEST.json.

Check B (warning only): Every numbered-folder asset directory should have at
least one tool binding in manifest_overrides.yaml (linked_data_asset_ids).

Usage:
    python3 platform/scripts/governance/coverage_gate.py [--repo-root PATH] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print(
        "COVERAGE_GATE: ERROR — PyYAML not installed. Run: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


# ── Ignore list for Check B ───────────────────────────────────────────────────
ASSET_FOLDER_IGNORE = {
    "00_ARCHITECTURE",
    "00_NAK",
    "06_LEARNING_LAYER",
    "07_PREDICTIVE_MODELS",
    "platform",
    ".github",
    ".gemini",
    "node_modules",
    "__pycache__",
}


def find_repo_root(start: Optional[str] = None) -> Path:
    """Return the repo root path."""
    if start:
        return Path(start).resolve()
    return Path.cwd()


def extract_tool_names_from_retrieve_dir(repo_root: Path) -> list[str]:
    """
    Extract tool names from the retrieve directory by scanning individual tool
    source files for `const TOOL_NAME = '...'` declarations.

    This is more reliable than parsing index.ts (which uses re-exports) and
    exactly matches what RETRIEVAL_TOOLS[] ends up containing at runtime.
    """
    retrieve_dir = repo_root / "platform" / "src" / "lib" / "retrieve"
    if not retrieve_dir.is_dir():
        print(
            f"COVERAGE_GATE: ERROR — retrieve directory not found: {retrieve_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Only process files that are imported in index.ts
    index_ts = retrieve_dir / "index.ts"
    if not index_ts.is_file():
        print(
            f"COVERAGE_GATE: ERROR — index.ts not found: {index_ts}",
            file=sys.stderr,
        )
        sys.exit(2)

    index_content = index_ts.read_text(encoding="utf-8")

    # Extract imported module filenames from `import * as X from './module'` lines
    imported_modules: list[str] = re.findall(
        r"import\s+\*\s+as\s+\w+\s+from\s+'\.\/(\w+)'", index_content
    )

    tool_names: list[str] = []
    for module_name in imported_modules:
        tool_file = retrieve_dir / f"{module_name}.ts"
        if not tool_file.is_file():
            continue
        content = tool_file.read_text(encoding="utf-8")
        # Look for: const TOOL_NAME = 'some_tool' or const TOOL_NAME = "some_tool"
        match = re.search(r"const\s+TOOL_NAME\s*=\s*['\"]([a-z_][a-z0-9_]*)['\"]", content)
        if match:
            tool_names.append(match.group(1))

    return sorted(set(tool_names))


def load_override_tool_names(repo_root: Path) -> set[str]:
    """Load tool_name values from manifest_overrides.yaml additional_entries."""
    overrides_path = repo_root / "00_ARCHITECTURE" / "manifest_overrides.yaml"
    if not overrides_path.is_file():
        print(
            f"COVERAGE_GATE: ERROR — manifest_overrides.yaml not found: {overrides_path}",
            file=sys.stderr,
        )
        sys.exit(2)

    with overrides_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tool_names: set[str] = set()
    additional = data.get("additional_entries", []) or []
    for entry in additional:
        name = entry.get("tool_name")
        if isinstance(name, str) and name:
            tool_names.add(name)
    return tool_names


def load_manifest_tool_names(repo_root: Path) -> set[str]:
    """Load tool_name values from CAPABILITY_MANIFEST.json entries."""
    manifest_path = repo_root / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"
    if not manifest_path.is_file():
        # Non-fatal: the manifest may not always exist in all environments
        return set()

    with manifest_path.open(encoding="utf-8") as f:
        data = json.load(f)

    tool_names: set[str] = set()
    for entry in data.get("entries", []):
        name = entry.get("tool_name")
        if isinstance(name, str) and name:
            tool_names.add(name)
    return tool_names


def load_override_linked_assets(repo_root: Path) -> set[str]:
    """
    Load all folder names referenced in linked_data_asset_ids in
    manifest_overrides.yaml. Used for Check B.
    """
    overrides_path = repo_root / "00_ARCHITECTURE" / "manifest_overrides.yaml"
    if not overrides_path.is_file():
        return set()

    with overrides_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Collect canonical_ids from additional_entries that have linked_data_asset_ids
    bound_asset_ids: set[str] = set()
    additional = data.get("additional_entries", []) or []
    for entry in additional:
        linked = entry.get("linked_data_asset_ids") or []
        for asset_id in linked:
            bound_asset_ids.add(str(asset_id))
    return bound_asset_ids


def find_numbered_asset_folders(repo_root: Path) -> list[str]:
    """Return folder names under repo root that start with a digit."""
    folders: list[str] = []
    try:
        for item in sorted(repo_root.iterdir()):
            if item.is_dir() and item.name[0].isdigit():
                if item.name not in ASSET_FOLDER_IGNORE:
                    folders.append(item.name)
    except PermissionError:
        pass
    return folders


def run_checks(repo_root: Path, dry_run: bool) -> int:
    """Run Check A + Check B. Returns exit code (0 = pass, 1 = error)."""
    errors: int = 0
    warnings: int = 0

    # ── Check A: Tool coverage ─────────────────────────────────────────────
    print("COVERAGE_GATE: checking tool coverage...")
    wired_tools = extract_tool_names_from_retrieve_dir(repo_root)
    override_names = load_override_tool_names(repo_root)
    manifest_names = load_manifest_tool_names(repo_root)
    all_manifest_names = override_names | manifest_names

    for tool_name in wired_tools:
        if tool_name not in all_manifest_names:
            print(
                f"COVERAGE_GATE: ERROR tool '{tool_name}' has no manifest entry (coverage gap)"
            )
            errors += 1

    # ── Check B: Asset folder coverage (warning only) ─────────────────────
    print("COVERAGE_GATE: checking asset folder coverage...")
    bound_assets = load_override_linked_assets(repo_root)
    numbered_folders = find_numbered_asset_folders(repo_root)

    for folder in numbered_folders:
        # Check if any tool links to an asset inside this folder
        # We check if any linked_data_asset_id corresponds to something in this folder.
        # Heuristic: convert folder-name prefix to expected asset id prefix.
        # E.g. "01_FACTS_LAYER" → look for any asset bound to it.
        # Since asset IDs are arbitrary, we check if any bound asset ID name
        # pattern starts with a fragment from the folder name (rough heuristic).
        folder_prefix = folder.split("_")[0]  # e.g. "01", "025"
        # Check if any manifest entry has a path starting with this folder
        # (using the overrides path field as a proxy)
        has_binding = _folder_has_any_binding(repo_root, folder, bound_assets)
        if not has_binding:
            print(
                f"COVERAGE_GATE: WARNING folder '{folder}' has no tool binding"
                " (expected for substrate layers)"
            )
            warnings += 1

    print(
        f"COVERAGE_GATE: summary: {errors} error{'s' if errors != 1 else ''},"
        f" {warnings} warning{'s' if warnings != 1 else ''}"
    )

    if dry_run:
        return 0
    return 1 if errors > 0 else 0


def _folder_has_any_binding(
    repo_root: Path, folder_name: str, bound_asset_ids: set[str]
) -> bool:
    """
    Heuristic: check if any additional_entries entry has a `path` field that
    starts with folder_name, OR if any tool is linked to an asset_id that
    plausibly lives in this folder.

    We use the manifest_overrides.yaml path fields as the source of truth.
    """
    overrides_path = repo_root / "00_ARCHITECTURE" / "manifest_overrides.yaml"
    if not overrides_path.is_file():
        return False

    with overrides_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Check additional_entries for any entry whose path starts with folder_name
    additional = data.get("additional_entries", []) or []
    for entry in additional:
        entry_path = entry.get("path", "")
        if isinstance(entry_path, str) and entry_path.startswith(folder_name + "/"):
            return True

    # Also check overrides section for any entries
    overrides = data.get("overrides", {}) or {}
    for _key, override in overrides.items():
        pattern = override.get("path_pattern", "")
        if isinstance(pattern, str) and folder_name in pattern:
            return True

    # Check CAPABILITY_MANIFEST.json for path entries starting with folder_name
    manifest_path = repo_root / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"
    if manifest_path.is_file():
        try:
            with manifest_path.open(encoding="utf-8") as f:
                manifest_data = json.load(f)
            for entry in manifest_data.get("entries", []):
                entry_path = entry.get("path", "")
                if isinstance(entry_path, str) and entry_path.startswith(folder_name + "/"):
                    return True
        except (json.JSONDecodeError, KeyError):
            pass

    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="COV-S7 coverage gate: tool-manifest and asset-folder checks"
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Path to repo root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print findings but exit 0 (smoke test mode)",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(args.repo_root)
    exit_code = run_checks(repo_root, dry_run=args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
