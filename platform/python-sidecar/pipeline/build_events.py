"""
build_events.py — MARSYS-JIS build event emitter
Writes to build_notifications + updates build_steps atomically.
SSE event format matches /api/build/events/[buildId] consumer.

Column mapping (actual DB schema):
  build_steps.row_count        (not rows_written)
  build_steps.completed_at     (not finished_at)
  build_steps.error_msg        (not error_summary)
  build_steps.category         (maps to asset_id/step identifier)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Literal

logger = logging.getLogger(__name__)

EventType = Literal[
    'build_queued', 'build_started', 'step_started', 'step_complete',
    'step_failed', 'build_complete', 'build_failed', 'build_cancelled'
]

StageType = Literal['compute', 'persist', 'verify', 'commit']
StatusType = Literal['started', 'complete', 'failed']


def emit_event(
    conn,
    build_id: str,
    event_type: EventType,
    asset_id: Optional[str] = None,
    ayanamsha_id: Optional[str] = None,
    stage: Optional[StageType] = None,
    status: Optional[StatusType] = None,
    rows_written: int = 0,
    error: Optional[str] = None,
    extra: Optional[dict] = None
) -> Optional[str]:
    """
    Insert a row into build_notifications and return the notif_id.

    Payload follows SSE format expected by /api/build/events/[buildId]:
    {
        "type": event_type,
        "build_id": build_id,
        "asset_id": asset_id,           // null for build-level events
        "ayanamsha_id": ayanamsha_id,   // null for build-level events
        "stage": stage,
        "status": status,
        "rows_written": rows_written,
        "error": error,
        "timestamp": ISO8601,
        ...extra fields
    }

    Non-fatal: if the DB insert fails, logs the error and returns None —
    the calling build pipeline continues uninterrupted.
    """
    payload = {
        "type": event_type,
        "build_id": build_id,
        "asset_id": asset_id,
        "ayanamsha_id": ayanamsha_id,
        "stage": stage,
        "status": status,
        "rows_written": rows_written,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)

    notif_id = None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_notifications (build_id, event_type, payload)
                VALUES (%s, %s, %s)
                RETURNING notif_id
                """,
                (build_id, event_type, json.dumps(payload))
            )
            row = cur.fetchone()
            notif_id = str(row[0]) if row else None
        conn.commit()
        logger.debug(
            "emit_event: %s build=%s asset=%s stage=%s",
            event_type, build_id, asset_id, stage
        )
    except Exception as e:
        logger.error("emit_event failed for build=%s event=%s: %s", build_id, event_type, e)
        # Non-fatal: log but don't raise — build continues even if telemetry fails
        try:
            conn.rollback()
        except Exception:
            pass

    return notif_id


def emit_step_event(
    conn,
    build_id: str,
    asset_id: str,
    ayanamsha_id: str,
    stage: StageType,
    status: StatusType,
    rows_written: int = 0,
    error: Optional[str] = None
) -> None:
    """
    Emit a step-level event AND update the corresponding build_steps row atomically.

    Status→event_type mapping:
      'started'  → 'step_started'
      'complete' → 'step_complete'
      'failed'   → 'step_failed'

    build_steps column mapping (actual schema):
      status='running'    on started
      completed_at=NOW()  on complete/failed
      row_count           (maps to rows_written argument)
      error_msg           (maps to error argument)

    Non-fatal: logs on failure, does not raise.
    """
    event_map: dict = {
        'started': 'step_started',
        'complete': 'step_complete',
        'failed': 'step_failed',
    }
    event_type = event_map.get(status, 'step_started')

    try:
        with conn.cursor() as cur:
            if status == 'started':
                cur.execute(
                    """
                    UPDATE build_steps
                       SET status = 'running',
                           started_at = NOW()
                     WHERE build_id = %s
                       AND category = %s
                       AND ayanamsha_id = %s
                    """,
                    (build_id, asset_id, ayanamsha_id)
                )
            elif status == 'complete':
                cur.execute(
                    """
                    UPDATE build_steps
                       SET status = 'complete',
                           completed_at = NOW(),
                           row_count = %s
                     WHERE build_id = %s
                       AND category = %s
                       AND ayanamsha_id = %s
                    """,
                    (rows_written, build_id, asset_id, ayanamsha_id)
                )
            elif status == 'failed':
                cur.execute(
                    """
                    UPDATE build_steps
                       SET status = 'failed',
                           completed_at = NOW(),
                           error_msg = %s
                     WHERE build_id = %s
                       AND category = %s
                       AND ayanamsha_id = %s
                    """,
                    (error, build_id, asset_id, ayanamsha_id)
                )

            # Emit notification row in the same transaction
            payload = {
                "type": event_type,
                "build_id": build_id,
                "asset_id": asset_id,
                "ayanamsha_id": ayanamsha_id,
                "stage": stage,
                "status": status,
                "rows_written": rows_written,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            cur.execute(
                "INSERT INTO build_notifications (build_id, event_type, payload) VALUES (%s, %s, %s)",
                (build_id, event_type, json.dumps(payload))
            )
        conn.commit()
        logger.debug(
            "emit_step_event: %s build=%s asset=%s ayanamsha=%s stage=%s",
            event_type, build_id, asset_id, ayanamsha_id, stage
        )
    except Exception as e:
        logger.error(
            "emit_step_event failed for build=%s asset=%s ayanamsha=%s: %s",
            build_id, asset_id, ayanamsha_id, e
        )
        try:
            conn.rollback()
        except Exception:
            pass


def format_sse_row(notif_id: str, event_type: str, payload: dict) -> str:
    """
    Format a notification as an SSE (Server-Sent Events) string.

    Returns the standard SSE wire format:
        id: <notif_id>
        event: <event_type>
        data: <json>

    (Trailing double newline separates SSE events per the spec.)
    """
    return f"id: {notif_id}\nevent: {event_type}\ndata: {json.dumps(payload)}\n\n"
