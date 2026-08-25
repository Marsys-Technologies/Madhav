"""Versioned build receipts and sidecar-owned freshness reconciliation.

This module intentionally owns digest construction and database mutation.  The
Node planner consumes the resulting freshness projection but never hashes Python
source or updates build state while serving a read request.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal


RECEIPT_VERSION = "nirmana-provenance-receipt-v1"
WHOLE_ASSET_PARTITION = "__whole_asset__"
FreshnessState = Literal["fresh", "stale", "unknown"]


def _normalise(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalise(item) for item in value)
    return value


def canonical_digest(value: Any) -> str:
    """SHA-256 of a canonical, versioned JSON value."""
    payload = json.dumps(_normalise(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Receipt:
    asset_id: str
    chart_id: str | None
    partition_key: str
    code_digest: str | None
    config_digest: str | None
    upstream_digest: str | None
    partition_digest: str | None
    output_digest: str | None
    upstream_receipts: list[dict[str, Any]]
    unknown_reasons: tuple[str, ...]
    receipt_version: str = RECEIPT_VERSION

    @property
    def receipt_state(self) -> Literal["proven", "unknown"]:
        return "unknown" if self.unknown_reasons else "proven"


def build_receipt(
    *,
    asset_id: str,
    chart_id: str | None,
    code_digest: str | None,
    config: dict[str, Any],
    upstream_digest: str | None,
    upstream_receipts: list[dict[str, Any]],
    partition_declaration: str | None,
    has_cowriters: bool,
    output_digest: str | None,
) -> Receipt:
    """Build a receipt without guessing a missing partition or output digest."""
    partition_key = partition_declaration or WHOLE_ASSET_PARTITION
    reasons: list[str] = []
    if code_digest is None:
        reasons.append("code_digest_unavailable")
    if upstream_digest is None:
        reasons.append("upstream_digest_unavailable")
    if output_digest is None:
        reasons.append("output_digest_unavailable")
    if has_cowriters and partition_declaration is None:
        reasons.append("partition_undeclared")
    partition_digest = None if has_cowriters and partition_declaration is None else canonical_digest({
        "version": RECEIPT_VERSION,
        "partition_key": partition_key,
    })
    if partition_digest is None:
        reasons.append("partition_digest_unavailable")
    try:
        config_digest = canonical_digest({"version": RECEIPT_VERSION, "config": config})
    except (TypeError, ValueError):
        # Receipt creation must not turn an already successful writer into a
        # false failure merely because a new config value is not serialisable.
        # It is an explicit blocker until the config representation is defined.
        config_digest = None
        reasons.append("config_digest_unavailable")
    return Receipt(
        asset_id=asset_id,
        chart_id=chart_id,
        partition_key=partition_key,
        code_digest=code_digest,
        config_digest=config_digest,
        upstream_digest=upstream_digest,
        partition_digest=partition_digest,
        output_digest=output_digest,
        upstream_receipts=upstream_receipts,
        unknown_reasons=tuple(sorted(set(reasons))),
    )


def classify_receipt(stored: Receipt | None, current: Receipt | None) -> tuple[FreshnessState, list[str]]:
    """Pure, component-wise freshness classification; never mutates on read."""
    if stored is None or current is None:
        return "unknown", ["receipt_missing"]
    if stored.receipt_state == "unknown":
        return "unknown", list(stored.unknown_reasons)
    if current.receipt_state == "unknown":
        return "unknown", list(current.unknown_reasons)
    changed = [
        name for name in ("code_digest", "config_digest", "upstream_digest", "partition_digest", "output_digest")
        if getattr(stored, name) != getattr(current, name)
    ]
    return ("stale", [f"{name}_changed" for name in changed]) if changed else ("fresh", [])


def _registry_partition(cur, asset_id: str) -> tuple[str | None, bool]:
    cur.execute(
        """
        SELECT ar.natural_key_partition,
               EXISTS (
                 SELECT 1 FROM asset_registry peer
                  WHERE peer.target_table IS NOT DISTINCT FROM ar.target_table
                    AND peer.asset_id <> ar.asset_id
                    AND peer.is_active = true
                    AND peer.has_writer = true
               ) AS has_cowriters
          FROM asset_registry ar
         WHERE ar.asset_id = %s
        """,
        (asset_id,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"asset registry row missing for provenance receipt: {asset_id}")
    return row.get("natural_key_partition"), bool(row.get("has_cowriters"))


def _stored_receipt(cur, receipt: Receipt) -> Receipt | None:
    cur.execute(
        """
        SELECT code_digest, config_digest, upstream_digest, partition_digest,
               output_digest, upstream_receipts, unknown_reasons, receipt_version
          FROM asset_provenance_receipts
         WHERE asset_id = %s AND chart_id IS NOT DISTINCT FROM %s AND partition_key = %s
        """,
        (receipt.asset_id, receipt.chart_id, receipt.partition_key),
    )
    old = cur.fetchone()
    stored = None if not old else Receipt(
        asset_id=receipt.asset_id,
        chart_id=receipt.chart_id,
        partition_key=receipt.partition_key,
        code_digest=old.get("code_digest"), config_digest=old.get("config_digest"),
        upstream_digest=old.get("upstream_digest"), partition_digest=old.get("partition_digest"),
        output_digest=old.get("output_digest"), upstream_receipts=list(old.get("upstream_receipts") or []),
        unknown_reasons=tuple(old.get("unknown_reasons") or []),
        receipt_version=old.get("receipt_version") or RECEIPT_VERSION,
    )
    return stored


def _upsert_freshness(
    cur,
    receipt: Receipt,
    freshness: FreshnessState,
    reasons: list[str],
) -> None:
    """Store the sidecar projection only; this never commits a transaction."""
    cur.execute(
        """
        INSERT INTO asset_freshness
          (asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, NOW())
        ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE SET
          freshness_state = EXCLUDED.freshness_state, reasons = EXCLUDED.reasons,
          receipt_version = EXCLUDED.receipt_version, observed_at = EXCLUDED.observed_at
        """,
        (receipt.asset_id, receipt.chart_id, receipt.partition_key, freshness,
         json.dumps(reasons), receipt.receipt_version),
    )


def reconcile_receipt(cur, current: Receipt) -> tuple[FreshnessState, list[str]]:
    """Classify the last successful receipt against current inputs and record it.

    This is the sole sidecar reconciliation path.  It intentionally preserves the
    old receipt while inputs differ: replacing it before a successful writer run
    would let new code/config/upstreams masquerade as having produced old output.
    The caller owns the transaction, so this is idempotent and never mutates on
    a planner read.
    """
    freshness, reasons = classify_receipt(_stored_receipt(cur, current), current)
    _upsert_freshness(cur, current, freshness, reasons)
    return freshness, reasons


def persist_successful_receipt(cur, receipt: Receipt, build_id: str | None) -> tuple[FreshnessState, list[str]]:
    """Atomically replace the receipt after a successful writer execution.

    A success proves its own newly written output; prior input changes must not
    leave the just-produced receipt stale.  Incomplete evidence remains unknown.
    The caller owns the encompassing throughput transaction.
    """
    freshness: FreshnessState = "unknown" if receipt.receipt_state == "unknown" else "fresh"
    reasons = list(receipt.unknown_reasons)
    cur.execute(
        """
        INSERT INTO asset_provenance_receipts
          (asset_id, chart_id, partition_key, receipt_version, code_digest, config_digest,
           upstream_digest, partition_digest, output_digest, upstream_receipts, receipt_state,
           unknown_reasons, observed_at, build_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, NOW(), %s)
        ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE SET
          receipt_version = EXCLUDED.receipt_version, code_digest = EXCLUDED.code_digest,
          config_digest = EXCLUDED.config_digest, upstream_digest = EXCLUDED.upstream_digest,
          partition_digest = EXCLUDED.partition_digest, output_digest = EXCLUDED.output_digest,
          upstream_receipts = EXCLUDED.upstream_receipts, receipt_state = EXCLUDED.receipt_state,
          unknown_reasons = EXCLUDED.unknown_reasons, observed_at = EXCLUDED.observed_at,
          build_id = EXCLUDED.build_id
        """,
        (receipt.asset_id, receipt.chart_id, receipt.partition_key, receipt.receipt_version,
         receipt.code_digest, receipt.config_digest, receipt.upstream_digest, receipt.partition_digest,
         receipt.output_digest, json.dumps(receipt.upstream_receipts), receipt.receipt_state,
         json.dumps(list(receipt.unknown_reasons)), build_id),
    )
    _upsert_freshness(cur, receipt, freshness, reasons)
    return freshness, reasons


def capture_and_persist_receipt(
    cur,
    *,
    asset_id: str,
    chart_id: str | None,
    build_id: str | None,
    code_digest: str | None,
    config: dict[str, Any],
    upstream_digest: str | None,
    upstream_receipts: list[dict[str, Any]],
    output_digest: str | None = None,
) -> tuple[FreshnessState, list[str]]:
    """Construct and persist the sidecar's receipt without committing the caller txn."""
    partition_declaration, has_cowriters = _registry_partition(cur, asset_id)
    receipt = build_receipt(
        asset_id=asset_id, chart_id=chart_id, code_digest=code_digest, config=config,
        upstream_digest=upstream_digest, upstream_receipts=upstream_receipts,
        partition_declaration=partition_declaration, has_cowriters=has_cowriters,
        output_digest=output_digest,
    )
    return persist_successful_receipt(cur, receipt, build_id)
