"""Event emission — Pub/Sub in Phase 4; stdout stub for now.

SAMĀPTI §9.6 / SD-EVENTREG-1 adds a THIRD sink: a durable, queryable register table
(`orchestrator_event_register`), for an allowlisted subset of event types.

Why. SATYA_DIPA_REPORT_v1_0.md §1 is the load-bearing finding: the two sinks below are
transports, not stores. stdout reaches Cloud Logging only on Cloud Run and only for
~30 days (a `--freshness=9999d` probe for "noop_completion" returned ZERO results), and
the Pub/Sub topic's only consumer holds an ephemeral 600-second per-connection
subscription. SATYA-DĪPA's Phase A had to abandon its primary forensic method because
`asset.noop_completion` had no queryable history at all. `persist_event()` below is that
history.

Design contract (see the migration header for the full rationale):

  * ALLOWLISTED, not universal. Only `DEFAULT_DURABLE_EVENT_TYPES` is persisted. The orchestrator
    emits ~12 event types, several per-substep; persisting all of them would make a
    firehose, not a register.
  * WRITTEN ON THE CALLER'S CURSOR, in the same transaction as the state write the event
    describes. A register row therefore exists if and only if that state decision
    actually committed — the register can never claim a rolled-back promotion, nor miss
    a real one. An autonomous side connection would be "more durable" and strictly less
    truthful.
  * SAVEPOINT-GUARDED and NEVER-RAISING. A build must not fail because its audit trail
    failed. If the table is missing (migration not yet applied), or the insert errors for
    any reason, the savepoint is rolled back, the enclosing transaction survives intact,
    and the failure is logged loudly.
  * ADDITIVE. `emit_event(evt)` with no cursor behaves exactly as it always has.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
import uuid

logger = logging.getLogger(__name__)


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)


# ── Durable register (SAMĀPTI §9.6 / SD-EVENTREG-1) ───────────────────────────

#: Event types persisted to `orchestrator_event_register`. The two no-op-completion
#: classes are the brief's explicit requirement. Extend deliberately — every addition
#: is write volume on every build.
DEFAULT_DURABLE_EVENT_TYPES = frozenset({
    "asset.noop_completion",
    "asset.noop_completion_rejected",
})


def _durable_event_types() -> frozenset[str]:
    """Allowlist of persisted event types.

    `ORCHESTRATOR_DURABLE_EVENT_TYPES` (comma-separated) overrides the default, so an
    incident response can widen the register without a code deploy. The empty string
    disables persistence entirely — an explicit, greppable off switch.
    """
    raw = os.environ.get("ORCHESTRATOR_DURABLE_EVENT_TYPES")
    if raw is None:
        return DEFAULT_DURABLE_EVENT_TYPES
    return frozenset(t.strip() for t in raw.split(",") if t.strip())


def _emitter_identity() -> str:
    """Best-effort "who emitted this" string.

    The SATYA-DĪPA Cloud Logging probe could not distinguish "this event never fired on
    Cloud Run" from "it fired and aged out of retention". Recording the emitter removes
    that ambiguity from every future audit.
    """
    for key in ("K_SERVICE", "CLOUD_RUN_JOB", "GAE_SERVICE"):
        v = os.environ.get(key)
        if v:
            job = os.environ.get("CLOUD_RUN_EXECUTION") or os.environ.get("K_REVISION")
            return f"{key.lower()}:{v}" + (f"@{job}" if job else "")
    try:
        return f"host:{socket.gethostname()}"
    except Exception:  # pragma: no cover — gethostname is not expected to fail
        return "host:unknown"


def _coerce_int(value):
    """None-preserving int coercion. A bad value must not cost us the whole row."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


_INSERT_SQL = """
INSERT INTO orchestrator_event_register
    (event_type, chart_id, asset_id, run_id, rows_present, substeps_remaining,
     emitted_by, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
"""


def persist_event(cur, event: dict) -> bool:
    """Persist one allowlisted event to `orchestrator_event_register`.

    Returns True if a row was written, False otherwise (not allowlisted, no cursor, or
    the insert failed). NEVER raises, and never leaves the caller's transaction aborted:
    the insert runs inside its own savepoint.
    """
    if cur is None:
        return False
    event_type = str(event.get("type") or "")
    if not event_type or event_type not in _durable_event_types():
        return False

    def _text(key):
        v = event.get(key)
        return None if v is None else str(v)

    try:
        params = (
            event_type,
            _text("chart_id"),
            _text("asset_id"),
            _text("run_id"),
            _coerce_int(event.get("rows_present")),
            _coerce_int(event.get("substeps_remaining")),
            _emitter_identity(),
            json.dumps(event, cls=_Encoder),
        )
    except Exception as exc:  # pragma: no cover — json.dumps of a build event
        logger.error("[event-register] could not serialise %s: %s", event_type, exc)
        return False

    try:
        cur.execute("SAVEPOINT orchestrator_event_register_persist")
    except Exception as exc:
        # No savepoint means no guarantee we can recover the caller's transaction, so
        # do not attempt the insert at all. Losing an audit row is survivable; aborting
        # a live build transaction to record one is not.
        logger.error(
            "[event-register] could not open savepoint for %s (%s) — skipping persist",
            event_type, exc,
        )
        return False

    try:
        cur.execute(_INSERT_SQL, params)
        cur.execute("RELEASE SAVEPOINT orchestrator_event_register_persist")
        return True
    except Exception as exc:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT orchestrator_event_register_persist")
            cur.execute("RELEASE SAVEPOINT orchestrator_event_register_persist")
        except Exception as rb_exc:  # pragma: no cover — rollback of our own savepoint
            logger.error(
                "[event-register] savepoint rollback ALSO failed after %s: %s",
                exc, rb_exc,
            )
        logger.error(
            "[event-register] failed to persist %s (asset=%s chart=%s run=%s): %s — "
            "the build is unaffected, but this event is NOT in the durable register. "
            "If the table is missing, apply the orchestrator_event_register migration.",
            event_type, event.get("asset_id"), event.get("chart_id"),
            event.get("run_id"), exc,
        )
        return False


# ── Emission ──────────────────────────────────────────────────────────────────

def emit_event(event: dict, cur=None) -> None:
    """Emit an orchestrator event.

    `cur`: the orchestrator's live cursor. When supplied AND the event type is in the
    durable allowlist, the event is ALSO written to `orchestrator_event_register`, in
    the caller's transaction (see module docstring). Omitting it preserves the exact
    pre-SAMĀPTI behaviour — this parameter is purely additive.
    """
    if cur is not None:
        persist_event(cur, event)
    elif str(event.get("type") or "") in _durable_event_types():
        # A durable-class event reached a call site with no cursor. That is a wiring
        # gap, not a data problem: the register will silently under-report unless it is
        # fixed. Say so, loudly, rather than letting the gap be invisible — being
        # invisible is exactly what SD-EVENTREG-1 exists to end.
        logger.warning(
            "[event-register] %s emitted WITHOUT a cursor — not persisted to "
            "orchestrator_event_register (asset=%s chart=%s run=%s). Pass cur= at this "
            "call site.",
            event.get("type"), event.get("asset_id"), event.get("chart_id"),
            event.get("run_id"),
        )

    if os.environ.get("PUBSUB_DISABLED") or not os.environ.get("PUBSUB_TOPIC"):
        print(f"[event] {json.dumps(event, cls=_Encoder)}", flush=True)
        return
    _pubsub_publish(event)


def _pubsub_publish(event: dict) -> None:
    """Fire-and-forget publish to cockpit-events Pub/Sub topic (Phase 4 wired)."""
    try:
        from google.cloud import pubsub_v1

        project = os.environ.get("GCP_PROJECT", "madhav-astrology")
        topic_id = os.environ.get("PUBSUB_TOPIC", "cockpit-events")

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project, topic_id)
        data = json.dumps(event, cls=_Encoder).encode("utf-8")
        attrs = {
            "chart_id": str(event.get("chart_id", "")),
            "type": event["type"],
        }
        future = publisher.publish(topic_path, data, **attrs)
        future.add_done_callback(_on_done)
    except Exception as exc:
        print(f"[pubsub-error] {exc}", file=sys.stderr, flush=True)


def _on_done(future) -> None:
    try:
        future.result(timeout=5)
    except Exception as exc:
        print(f"[pubsub-publish-error] {exc}", file=sys.stderr, flush=True)
