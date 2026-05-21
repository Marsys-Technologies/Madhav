#!/usr/bin/env python3
"""
manifest_reader.py — loads CAPABILITY_MANIFEST.json + manifest_overrides.yaml mirror_pairs
and returns a CanonicalArtifacts-compatible object.

Used as the manifest-mode backend for drift_detector.py, schema_validator.py, and
mirror_enforcer.py when their USE_MANIFEST feature flags are active.
"""
from __future__ import annotations

import json
import pathlib
from typing import Dict

import yaml

from _ca_loader import CanonicalArtifacts


MANIFEST_PATH = "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
OVERRIDES_PATH = "00_ARCHITECTURE/manifest_overrides.yaml"

# Short-form aliases: CA §1 uses these IDs; manifest derives file-path-based IDs.
# Mapping: short-form → manifest canonical_id.
_CA_ALIASES: Dict[str, str] = {
    "FORENSIC": "FORENSIC_ASTROLOGICAL_DATA_v8_0",
    "LEL": "LIFE_EVENT_LOG_v1_2",
    "MSR": "MSR_v3_0",
    "UCN": "UCN_v4_0",
    "CDLM": "CDLM_v1_1",
    "RM": "RM_v2_0",
    # CGM already has canonical_id: "CGM" in its frontmatter — no alias needed.
}


def load_manifest_as_ca(repo_root: pathlib.Path) -> CanonicalArtifacts:
    """
    Load CAPABILITY_MANIFEST.json and manifest_overrides.yaml mirror_pairs,
    returning a CanonicalArtifacts object with the same .artifacts / .mirror_pairs
    interface as load_canonical_artifacts().

    artifacts dict keys: canonical_id → row dict with at minimum:
        path, status, version, fingerprint_sha256, layer, expose_to_chat, native_id

    mirror_pairs dict keys: pair_id → row dict with at minimum:
        claude_side, gemini_side, mirror_mode, known_asymmetries, enforcement_rule
    """
    manifest_file = repo_root / MANIFEST_PATH
    raw_text = manifest_file.read_text(encoding="utf-8")
    manifest = json.loads(raw_text)

    artifacts: Dict[str, dict] = {}
    for entry in manifest.get("entries", []):
        canonical_id = entry.get("canonical_id")
        if not canonical_id:
            continue
        artifacts[canonical_id] = {
            "canonical_id": canonical_id,
            "path": entry.get("path", ""),
            "status": entry.get("status", "CURRENT"),
            "version": str(entry.get("version", "")),
            # prefer fingerprint_sha256 (authoritative); fall back to legacy fingerprint field
            "fingerprint_sha256": entry.get("fingerprint_sha256") or entry.get("fingerprint", ""),
            "layer": entry.get("layer", ""),
            "expose_to_chat": entry.get("expose_to_chat", False),
            "native_id": entry.get("native_id", ""),
        }

    # Add short-form alias entries so governance scripts that look up
    # ca.artifacts["MSR"], ca.artifacts["FORENSIC"], etc. resolve correctly.
    for alias, manifest_id in _CA_ALIASES.items():
        if manifest_id in artifacts and alias not in artifacts:
            artifacts[alias] = dict(artifacts[manifest_id])
            artifacts[alias]["canonical_id"] = alias  # expose alias as canonical_id

    # Load mirror_pairs from manifest_overrides.yaml mirror_pairs section.
    mirror_pairs: Dict[str, dict] = {}
    overrides_file = repo_root / OVERRIDES_PATH
    if overrides_file.exists():
        try:
            overrides = yaml.safe_load(overrides_file.read_text(encoding="utf-8")) or {}
            for pair_id, pair_data in (overrides.get("mirror_pairs") or {}).items():
                if isinstance(pair_data, dict):
                    mirror_pairs[pair_id] = dict(pair_data)
                    mirror_pairs[pair_id].setdefault("pair_id", pair_id)
        except Exception as exc:
            import sys
            print(f"[manifest_reader] Warning: could not load mirror_pairs from overrides: {exc}",
                  file=sys.stderr)

    return CanonicalArtifacts(
        path=manifest_file,
        raw_text=raw_text,
        fingerprint_observed="",  # not fingerprinting the manifest itself here
        artifacts=artifacts,
        mirror_pairs=mirror_pairs,
    )
