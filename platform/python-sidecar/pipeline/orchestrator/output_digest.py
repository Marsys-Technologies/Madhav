"""Canonical, content-sensitive output digests for reviewed asset specs.

Specs are migration-owned records, not caller-provided SQL.  This module accepts
only conservative SQL identifiers and composes a fixed SELECT shape; row values
are returned as PostgreSQL JSONB text and hashed without logging their content.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from .provenance import canonical_digest


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_BATCH_SIZE = 512


@dataclass(frozen=True)
class OutputDigestSpec:
    asset_id: str
    spec_sha256: str
    spec: dict[str, Any]


def _identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"output digest spec has invalid {field} identifier")
    return value


def _columns(component: dict[str, Any], field: str) -> list[str]:
    values = component.get(field)
    if not isinstance(values, list) or not values:
        raise ValueError(f"output digest spec component requires non-empty {field}")
    columns = [_identifier(value, field=field) for value in values]
    if len(set(columns)) != len(columns):
        raise ValueError(f"output digest spec component repeats a {field} value")
    return columns


def _validate_spec(asset_id: str, raw: object, expected_sha: object) -> OutputDigestSpec:
    if not isinstance(raw, dict) or raw.get("version") != "nirmana-output-digest-spec-v1":
        raise ValueError("output digest spec has unsupported version")
    actual_sha = canonical_digest(raw)
    if not isinstance(expected_sha, str) or expected_sha != actual_sha:
        raise ValueError("output digest spec SHA does not match canonical content")
    components = raw.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("output digest spec requires components")
    seen_names: set[str] = set()
    seen_relations: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("output digest spec component must be an object")
        name = _identifier(component.get("name"), field="component name")
        relation = _identifier(component.get("relation"), field="relation")
        _columns(component, "key_columns")
        _columns(component, "value_columns")
        if name in seen_names or relation in seen_relations:
            raise ValueError("output digest spec repeats a component")
        seen_names.add(name)
        seen_relations.add(relation)
    return OutputDigestSpec(asset_id=asset_id, spec_sha256=actual_sha, spec=raw)


def load_output_digest_spec(cur, asset_id: str) -> OutputDigestSpec | None:
    """Load one reviewed current spec, rejecting malformed persisted metadata."""
    cur.execute(
        """
        SELECT spec, spec_sha256
          FROM asset_output_digest_specs
         WHERE asset_id = %s AND retired_at IS NULL
        """,
        (asset_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return _validate_spec(asset_id, row.get("spec"), row.get("spec_sha256"))


def _quoted(identifier: str) -> str:
    # `_identifier` admits only lowercase unquoted PostgreSQL identifiers.
    return f'"{identifier}"'


def _component_statement(component: dict[str, Any]) -> str:
    relation = _identifier(component.get("relation"), field="relation")
    key_columns = _columns(component, "key_columns")
    value_columns = _columns(component, "value_columns")
    pairs: list[str] = []
    for column in value_columns:
        pairs.extend([f"'{column}'", f"source.{_quoted(column)}"])
    row_json = f"jsonb_build_object({', '.join(pairs)})::text"
    key_projection = ", ".join(
        f"to_jsonb(source.{_quoted(column)})::text COLLATE \"C\" AS {_quoted(f'__key_{index}')}"
        for index, column in enumerate(key_columns)
    )
    order = ", ".join(
        f"digest_source.{_quoted(f'__key_{index}')} NULLS FIRST"
        for index in range(len(key_columns))
    )
    # PostgreSQL does not expose a SELECT-list alias inside an ORDER BY
    # expression such as `row_json COLLATE "C"`. Materialize the aliases in an
    # inner query first. Key values are normalized to JSON text so ordering is
    # deterministic across database locales and works for non-text key types.
    # `row_json` then provides a deterministic tie-breaker if a reviewed key is
    # accidentally non-unique. The fixed public schema forbids caller-supplied
    # table paths or SQL expressions.
    return (
        "SELECT digest_source.row_json "
        f"FROM (SELECT {row_json} AS row_json, {key_projection} "
        f"FROM public.{_quoted(relation)} AS source) AS digest_source "
        f"ORDER BY {order}, digest_source.row_json COLLATE \"C\""
    )


def compute_output_digest(cur, *, asset_id: str) -> tuple[str | None, str | None]:
    """Stream a reviewed asset's declared rows into a canonical SHA-256.

    Missing specifications deliberately return no digest: callers persist an
    unknown receipt rather than falling back to a run-id or row-count proxy.
    """
    loaded = load_output_digest_spec(cur, asset_id)
    if loaded is None:
        return None, None

    digest = hashlib.sha256()
    digest.update(b"nirmana-output-content-v1\\0")
    digest.update(loaded.spec_sha256.encode("ascii"))
    for component in loaded.spec["components"]:
        name = _identifier(component.get("name"), field="component name")
        digest.update(name.encode("ascii"))
        digest.update(b"\\0")
        cur.execute(_component_statement(component))
        row_count = 0
        while rows := cur.fetchmany(_BATCH_SIZE):
            for row in rows:
                value = row.get("row_json")
                if not isinstance(value, str):
                    raise ValueError("output digest query returned a non-text JSON row")
                encoded = value.encode("utf-8")
                digest.update(len(encoded).to_bytes(8, "big"))
                digest.update(encoded)
                row_count += 1
        digest.update(row_count.to_bytes(8, "big"))
    return digest.hexdigest(), loaded.spec_sha256
