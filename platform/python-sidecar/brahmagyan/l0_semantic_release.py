"""Version-pinned L0 semantic release and strict Python identity adapter.

The JSON release is the producer authority.  This module derives an efficient
Python adapter from it; it does not create a second lexical authority.  Legacy
``norm_graha`` compatibility is implemented in ``graha_vocabulary.py``.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any


RELEASE_PATH = Path(__file__).with_name("l0_semantic_release_v1.json")


class SemanticReleaseError(ValueError):
    """Base class for fail-closed release/adapter errors."""


class UnknownGrahaIdentity(SemanticReleaseError):
    """Raised when a strict adapter receives an unknown identity."""


class AmbiguousGrahaIdentity(SemanticReleaseError):
    """Raised when an alias names more than one physical identity."""


def _normalise(value: str) -> str:
    return unicodedata.normalize("NFC", str(value)).strip().casefold()


def _digest_payload(release: dict[str, Any]) -> str:
    payload = deepcopy(release)
    payload["content_sha256"] = ""
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load() -> dict[str, Any]:
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    if release.get("schema_version") != "madhav-l0-semantic-release/v1":
        raise SemanticReleaseError("unsupported L0 semantic release schema")
    if release.get("content_sha256") != _digest_payload(release):
        raise SemanticReleaseError("L0 semantic release content digest mismatch")

    identity_ids: set[str] = set()
    codes: set[str] = set()
    aliases: dict[str, str] = {}
    ambiguous = {_normalise(k) for k in release.get("ambiguous_aliases", {})}
    for entity in release.get("entities", []):
        identity_id = entity["identity_id"]
        code = entity["canonical_subject_code"]
        if identity_id in identity_ids or code in codes:
            raise SemanticReleaseError(f"duplicate identity/code in release: {identity_id}/{code}")
        identity_ids.add(identity_id)
        codes.add(code)
        for alias in entity.get("aliases", []):
            key = _normalise(alias)
            if key in ambiguous:
                raise SemanticReleaseError(f"declared ambiguous alias used as direct alias: {alias}")
            prior = aliases.get(key)
            if prior is not None and prior != identity_id:
                raise SemanticReleaseError(f"alias collision in release: {alias}")
            aliases[key] = identity_id
    if not {"RAH_MEAN", "RAH_TRUE", "KET_MEAN", "KET_TRUE"}.issubset(codes):
        raise SemanticReleaseError("mean/true node physical variants are incomplete")
    return release


SEMANTIC_RELEASE: dict[str, Any] = _load()
SEMANTIC_RELEASE_ID: str = SEMANTIC_RELEASE["semantic_release_id"]
SEMANTIC_RELEASE_DIGEST: str = SEMANTIC_RELEASE["content_sha256"]
_BY_ID = {entity["identity_id"]: entity for entity in SEMANTIC_RELEASE["entities"]}
_ALIAS_TO_ID = {
    _normalise(alias): entity["identity_id"]
    for entity in SEMANTIC_RELEASE["entities"]
    for alias in entity["aliases"]
}
_AMBIGUOUS = {
    _normalise(alias): tuple(identity_ids)
    for alias, identity_ids in SEMANTIC_RELEASE["ambiguous_aliases"].items()
}


def resolve_graha_identity(value: str | None) -> dict[str, Any]:
    """Resolve one alias to a copy of its released identity, or fail closed."""
    if value is None or not str(value).strip():
        raise UnknownGrahaIdentity("empty graha identity")
    key = _normalise(str(value))
    if key in _AMBIGUOUS:
        choices = ", ".join(_AMBIGUOUS[key])
        raise AmbiguousGrahaIdentity(f'ambiguous graha identity "{value}": {choices}')
    identity_id = _ALIAS_TO_ID.get(key)
    if identity_id is None:
        raise UnknownGrahaIdentity(f'unknown graha identity "{value}"')
    result = deepcopy(_BY_ID[identity_id])
    result["semantic_release_id"] = SEMANTIC_RELEASE_ID
    result["release_digest"] = SEMANTIC_RELEASE_DIGEST
    return result


def graha_subject_code(value: str | None) -> str:
    """Strict alias-to-subject-code adapter shared with TypeScript semantics."""
    return str(resolve_graha_identity(value)["canonical_subject_code"])


def released_alias_map() -> dict[str, str]:
    """Return a normalized alias-to-code snapshot derived from the release."""
    return {
        alias: str(_BY_ID[identity_id]["canonical_subject_code"])
        for alias, identity_id in _ALIAS_TO_ID.items()
    }


def release_digest_for_test() -> str:
    """Detector hook: recompute the digest rather than trusting its stored value."""
    return _digest_payload(SEMANTIC_RELEASE)
