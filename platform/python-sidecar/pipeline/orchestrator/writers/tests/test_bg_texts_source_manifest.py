"""Immutable source-object contract for reproducible bg_texts rebuilds."""
from __future__ import annotations

import base64
import hashlib
import json

import pytest

from brahmagyan.l0_texts import TEXTS
from pipeline.orchestrator.writers.bg_texts import (
    SOURCE_MANIFEST,
    _load_source_manifest,
    _source_object,
    _verify_source_bytes,
)


def test_manifest_bytes_are_hard_bound_to_the_governed_sha(tmp_path):
    changed = dict(SOURCE_MANIFEST)
    changed["chunk_max_chars"] = SOURCE_MANIFEST["chunk_max_chars"] + 1
    changed_path = tmp_path / "changed-manifest.json"
    changed_path.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(ValueError, match="manifest SHA-256 mismatch"):
        _load_source_manifest(changed_path)


def test_manifest_pins_every_canonical_text_and_every_declared_gcs_input():
    objects = SOURCE_MANIFEST["objects"]
    assert SOURCE_MANIFEST["manifest_version"] == "bg-texts-source-manifest-v1"
    assert SOURCE_MANIFEST["embedding_model"] == "text-multilingual-embedding-002"
    assert SOURCE_MANIFEST["embedding_dimensions"] == 768
    assert len(objects) == 20
    assert len({item["gcs_path"] for item in objects}) == 20
    assert {item["text_id"] for item in objects} == {text["text_id"] for text in TEXTS}

    declared_paths = {
        text[key]
        for text in TEXTS
        for key in ("gcs_path", "gcs_path_vol2", "gcs_path_djvu_txt")
        if text.get(key)
    }
    manifest_paths = {item["gcs_path"] for item in objects}
    assert declared_paths <= manifest_paths
    assert (
        "gs://madhav-marsys-sources/L8/classical_texts/source/"
        "sarvartha_chintamani_djvu.txt"
    ) in manifest_paths
    assert all(item["generation"].isdigit() for item in objects)
    assert all(item["md5_base64"] and item["crc32c_base64"] for item in objects)


def test_source_lookup_returns_the_exact_generation_and_rejects_unreviewed_paths():
    source = _source_object(
        "gs://madhav-marsys-sources/L8/classical_texts/source/bphs.pdf"
    )
    assert source["generation"] == "1780939479967058"
    assert source["md5_base64"] == "jQwoy9wzJ/2zc377pHizow=="
    with pytest.raises(ValueError, match="not pinned"):
        _source_object("gs://madhav-marsys-sources/L8/classical_texts/source/unreviewed.pdf")


def test_downloaded_bytes_must_match_the_pinned_md5():
    payload = b"immutable source fixture"
    expected = base64.b64encode(hashlib.md5(payload).digest()).decode("ascii")
    _verify_source_bytes(payload, {"gcs_path": "gs://fixture", "md5_base64": expected})
    with pytest.raises(ValueError, match="MD5 mismatch"):
        _verify_source_bytes(payload + b" drift", {"gcs_path": "gs://fixture", "md5_base64": expected})
