"""Helpers for the bg_rule_book tests: build a version pair (manifest + card file) in a tmp dir.

Cards come from the committed FIXTURE (invented prose) or from tests/rulebook/_cards.py.
Nothing here holds a real card, verse, quote, chart value or birth data.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from brahmagyan.l0_rule_book import CARD_FILE_SCHEMA, FIXTURE_MANIFEST, MANIFEST_SCHEMA, redact_card
from services.rulebook.compiler import sha256_hex


def fixture_cards() -> list[dict]:
    manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    doc = json.loads((FIXTURE_MANIFEST.parent / manifest["card_file"]).read_text(encoding="utf-8"))
    return copy.deepcopy(doc["cards"])


def fixture_manifest() -> dict:
    return json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))


def write_version(
    directory: Path,
    version: str,
    full_cards: Iterable[Mapping[str, Any]],
    *,
    withdrawn: Optional[Dict[str, str]] = None,
    attestations: Optional[Dict[str, Mapping[str, Any]]] = None,
    redact: bool = True,
    fixture: bool = False,
) -> Path:
    """Write <directory>/<version>.manifest.json + cards file; returns the manifest path."""
    directory.mkdir(parents=True, exist_ok=True)
    withdrawn = withdrawn or {}
    stored, entries = [], []
    for full in full_cards:
        if redact:
            card, rmap, rat = redact_card(full)
        else:
            card, rmap, rat = copy.deepcopy(dict(full)), [], sha256_hex(full)
        stored.append(card)
        entry = {
            "card_id": card["card_id"],
            "card_sha256": sha256_hex(card),
            "ratification_sha256": rat,
            "redaction_map": rmap,
        }
        if attestations and card["card_id"] in attestations:
            entry["text_attestation"] = attestations[card["card_id"]]
        if card["card_id"] in withdrawn:
            entry["status"] = "withdrawn"
            entry["withdrawn_reason"] = withdrawn[card["card_id"]]
        entries.append(entry)
    card_name = f"{version}.cards.json"
    raw = (json.dumps({"card_file_schema": CARD_FILE_SCHEMA, "rulebook_version": version, "cards": stored},
                      indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    (directory / card_name).write_bytes(raw)
    manifest = {
        "manifest_schema": MANIFEST_SCHEMA,
        "rulebook_version": version,
        "card_file": card_name,
        "card_file_sha256": hashlib.sha256(raw).hexdigest(),
        "change_register_ids": ["TEST-CR-1"],
        "cards": entries,
    }
    if fixture:
        manifest["fixture"] = True
    path = directory / f"{version}.manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
