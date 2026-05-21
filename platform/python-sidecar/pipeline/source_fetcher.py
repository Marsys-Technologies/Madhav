"""
pipeline.source_fetcher — Fetch source assets from GCS to a temp directory.
Phase 14B.

Each asset is written to <temp_dir>/<asset.path> so that chunkers can be
called with temp_dir as repo_root and their hardcoded SOURCE_FILE paths resolve.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from google.cloud import storage

logger = logging.getLogger(__name__)


def fetch_asset(
    bucket_name: str,
    asset_path: str,
    dest_root: str,
) -> tuple[str, str]:
    """
    Download one asset from GCS to <dest_root>/<asset_path>.
    asset_path is the relative path (e.g. '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md').
    GCS object key mirrors the asset_path under the bucket root.

    Returns (local_abs_path, sha256_hex).
    """
    client = storage.Client()
    # GCS key: the asset path relative to bucket root, with subdir prefix matching GCS layout
    gcs_key = _asset_path_to_gcs_key(asset_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_key)

    dest_path = Path(dest_root) / asset_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    raw_bytes = blob.download_as_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    dest_path.write_bytes(raw_bytes)

    logger.debug("Fetched gs://%s/%s → %s (sha256=%s...)", bucket_name, gcs_key, dest_path, sha256[:16])
    return str(dest_path), sha256


def _asset_path_to_gcs_key(asset_path: str) -> str:
    """
    Map filesystem asset path to GCS object key.

    GCS bucket layout (from Phase 14A):
      L1/facts/     ← 01_FACTS_LAYER/ assets (non-SOURCES)
      L1/sources/   ← 01_FACTS_LAYER/SOURCES/ assets
      L2_5/         ← 025_HOLISTIC_SYNTHESIS/ assets
      L3/registers/ ← 035_DISCOVERY_LAYER/REGISTERS/ assets

    This function maps local path → GCS key.
    """
    p = asset_path.replace("\\", "/")
    if p.startswith("01_FACTS_LAYER/SOURCES/") or p.startswith("01_FACTS_LAYER/sources/"):
        return "L1/sources/" + Path(p).name
    elif p.startswith("01_FACTS_LAYER/"):
        return "L1/facts/" + Path(p).name
    elif p.startswith("025_HOLISTIC_SYNTHESIS/"):
        return "L2_5/" + Path(p).name
    elif p.startswith("035_DISCOVERY_LAYER/REGISTERS/") or p.startswith("035_DISCOVERY_LAYER/registers/"):
        return "L3/registers/" + Path(p).name
    else:
        return p


def fetch_all_assets(
    bucket_name: str,
    assets: list[dict],
    chunker_paths: set[str],
    workspace_root: str = "/app",
) -> tuple[str, dict[str, str]]:
    """
    Fetch all assets that have a registered chunker into workspace_root.

    workspace_root mirrors the repo root layout (WORKDIR in container).
    Validators using Path(__file__).parent^5 will resolve to workspace_root
    when rag/ is placed at workspace_root/platform/python-sidecar/rag/.

    Returns (workspace_root, {asset_path: sha256}).
    """
    sha256_map: dict[str, str] = {}

    for asset in assets:
        path = asset["path"]
        if path not in chunker_paths:
            logger.info("Skipping %s — no registered chunker", path)
            continue
        try:
            _, sha256 = fetch_asset(bucket_name, path, workspace_root)
            sha256_map[path] = sha256
            logger.info("Fetched %s (sha256=%s...)", path, sha256[:16])
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", path, exc)
            raise RuntimeError(f"Source fetch failed for {path}: {exc}") from exc

    logger.info("Fetched %d assets to workspace %s", len(sha256_map), workspace_root)
    return workspace_root, sha256_map
