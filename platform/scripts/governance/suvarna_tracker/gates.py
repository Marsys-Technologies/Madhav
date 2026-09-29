"""Centralized fail-closed gate evaluator (F1 — GPT-6 Astra independent review §2).

Before this module, `state.item_status` computed `done_by: 'decision'` and detector-gated status
inline, and one path in the decision branch fell through to `elif last: out["status"] =
last["state"]` — `last` being this *item's own item events*. An authoritative decisions log
supplied but holding no matching `decided` line (absent, delegated, revoked/superseded, or simply
never recorded) landed on that fallback, so an ordinary `kind: item, state: done` event for the
gated item's own id could mark a native gate (e.g. FI-7, J1.6) done with no decision behind it at
all — a forged or merely misrouted item event, never an approving native decision.

This module is the one place that decides a `done_by: 'decision'` or detector-gated item's status
from here on. The rule, in one sentence: **nothing here manufactures 'done' — an item event is
never consulted for a decision gate (only a decision *event*, and only ever as the 'requested'
workflow signal, never as a completion signal), and a detector-gated item is 'done' only when the
detector's own result says so; an item event claiming done while the detector disagrees is a
conflict, never done.**

Decision-gate rules (F1):
- No authoritative record for the decision id (`decisions is not None`, no `latest[dec_id]`, or
  `decisions is None` with no decision *event* at all): `not_started` — never `done`, never driven
  by an item event. (`not_started` lets `state.build_snapshot`'s own dependency-readiness rule turn
  it into `ready`/`waiting`, exactly as before any decision exists — this is not a new "waiting"
  state invented here, it is the same absence-of-information state the pre-fix code left it in.)
- A `requested` decision *event* (no log, or log has no record yet): `running`, "awaiting the
  native" — a workflow signal, never a completion signal.
- `decided` in the log: `done` — *unless* the item pins a `revision` (`item["revision"]`) and the
  decision's own `detail` does not carry a matching `revision=<same>` marker, in which case this is
  `waiting` (decided, but not for the revision this item cares about) — never `done` on a decision
  that was about a different artifact revision.
- `delegated` in the log: `waiting`, naming who it was delegated to — never `done`.
- `revoked` or `superseded` in the log (a later line for the same id undoing an earlier `decided`
  one — `decisions.load_decisions`'s own "latest wins per id" rule): `waiting`, naming what
  happened — never `done`, regardless of what an earlier line once said.
- `decisions is None` (no authoritative log supplied at all): the pre-authoritative-log,
  event-driven contract is kept for backward compatibility (`decided`/`delegated` *decision events*
  read `done`) — but, even in this mode, an *item* event is never consulted (F1's fail-closed rule
  applies unconditionally, not only once a log exists).

Detector-gate rules (unchanged in substance; centralized here per the review's Q21 recommendation):
`done` only when the detector's own result says `done`. An item event can move the shown status to
running/review/blocked/parked/failed, or surface a `conflict` when it claims `done` while the
detector disagrees — it can never itself produce `done` (CLAUDE.md §N.8).
"""
from __future__ import annotations

import re

# The revision marker inside a decision's `detail` text (Strategic Suvarṇa's own recording
# convention for a revision-bound ruling: "... revision=<sha-or-version> ..."). Matched literally,
# never inferred — a decision whose detail happens to contain a bare sha with no `revision=` marker
# does not bind (CLAUDE.md §N.7: no invented judgment from a proxy signal).
_REVISION_RE = re.compile(r"\brevision\s*=\s*(\S+)")


def _decision_revision(detail: str | None) -> str | None:
    """The `revision=<value>` marker's value, or None if the marker is absent. Trailing punctuation
    (a comma or semicolon closing the clause) is stripped so "revision=abc123, also: ..." still
    binds to "abc123"."""
    m = _REVISION_RE.search(detail or "")
    return m.group(1).rstrip(",;") if m else None


def evaluate_decision_gate(item: dict, decisions: dict | None, decision_events: list[dict]) -> dict:
    """`item["done_by"] == "decision"`. `decisions` is the authoritative log
    (`decisions.load_decisions()`'s `{'latest': {id: record}, 'malformed': N}` shape) or `None` for
    the pre-authoritative-log, backward-compatible event-driven contract. `decision_events` is this
    decision id's own *decision* events (never item events — an item event is never passed to or
    consulted by this function, in either mode)."""
    dec_id = item.get("decision", "")
    required_revision = item.get("revision")
    source = "decision:" + (dec_id or "?")
    last_dec_ev = decision_events[-1] if decision_events else None

    if decisions is not None:
        rec = decisions.get("latest", {}).get(dec_id)
        log_state = rec.get("state") if rec else "none"

        if log_state == "decided":
            if required_revision is not None:
                got = _decision_revision(rec.get("detail"))
                if got != required_revision:
                    return {"source": source, "status": "waiting",
                            "detail": f"decided, but for revision {got!r} (this item pins "
                                      f"{required_revision!r}); not authoritative for this item",
                            "evidence": None, "updated_at": rec.get("ts")}
            evidence = f"{rec.get('detail', '')} — {rec.get('source', '')}"
            return {"source": source, "status": "done", "detail": rec.get("detail", ""),
                    "evidence": evidence, "updated_at": rec.get("ts")}

        if log_state == "delegated":
            return {"source": source, "status": "waiting",
                    "detail": f"delegated to {rec.get('delegated_to') or '?'}; not yet decided",
                    "evidence": None, "updated_at": rec.get("ts")}

        if log_state in ("revoked", "superseded"):
            return {"source": source, "status": "waiting",
                    "detail": f"decision {dec_id} was {log_state}: {rec.get('detail', '')}".rstrip(": "),
                    "evidence": None, "updated_at": rec.get("ts")}

        # log_state == "none": no authoritative record. A 'requested' decision *event* is a
        # workflow signal only ("awaiting the native"); anything else — including a stray
        # decided/delegated *event* the log does not corroborate, surfaced separately as a
        # `conflict` row by state.build_snapshot, never used to drive this gate — leaves the item
        # `not_started`, so the ordinary dependency-readiness rule (ready/waiting) applies, exactly
        # as before any decision existed. An item event is never consulted here (F1).
        if last_dec_ev and last_dec_ev.get("state") == "requested":
            return {"source": source, "status": "running", "detail": "awaiting the native",
                    "evidence": None, "updated_at": last_dec_ev.get("ts")}
        return {"source": source, "status": "not_started", "detail": "", "evidence": None}

    # decisions is None: the pre-authoritative-log, backward-compatible event-driven contract —
    # decision *events* only, never item events, in this mode either (F1 is unconditional).
    if last_dec_ev is None:
        return {"source": source, "status": "not_started", "detail": "", "evidence": None}
    st = last_dec_ev["state"]
    if st in ("decided", "delegated"):
        return {"source": source, "status": "done", "detail": last_dec_ev.get("detail", ""),
                "evidence": last_dec_ev.get("detail"), "updated_at": last_dec_ev["ts"]}
    if st == "requested":
        return {"source": source, "status": "running", "detail": "awaiting the native",
                "evidence": None, "updated_at": last_dec_ev["ts"]}
    return {"source": source, "status": "not_started", "detail": "", "evidence": None}


def evaluate_detector_gate(detector_type: str, det_result: dict | None, last_item_event: dict | None) -> dict:
    """`item["detector"]` is set. `det_result` is the live detector's own result (or `None` if not
    yet measured); `last_item_event` is this item's own most recent non-step item event (or `None`).
    `done` is earned only by `det_result["status"] == "done"`."""
    out: dict = {"source": "detector:" + detector_type}
    if det_result is None:
        out.update(status="unknown", detail="not yet measured")
        return out
    out["checked_at"] = det_result["checked_at"]
    out["detail"] = det_result["detail"]
    if det_result.get("progress") is not None:
        out["progress"] = det_result["progress"]
    ds = det_result["status"]
    if ds == "done":
        out["status"] = "done"
        out["evidence"] = det_result["detail"]
    elif ds == "error":
        out["status"] = "unknown"
    elif last_item_event and last_item_event["state"] == "done":
        out.update(status="conflict", detail=f"an event claims done; the detector says: {det_result['detail']}")
    elif last_item_event and last_item_event["state"] in ("running", "review", "blocked", "parked", "failed"):
        out["status"] = last_item_event["state"]
    elif ds in ("running", "blocked"):
        out["status"] = ds
        out["soft"] = True
    return out


def evaluate_gate(item: dict, decisions: dict | None, det_result: dict | None,
                  events: dict | None) -> dict | None:
    """The single entry point `state.item_status` calls for every `done_by: 'decision'` item and
    every detector-gated item. Returns `None` for anything else (a plain `done_by: 'event'` item) —
    the caller keeps its own event-driven logic for those, unchanged.

    `events` is the same shape `events.index_events()` returns (`{'items': {id: [...]},
    'decisions': {id: [...]}, ...}`) — this function derives exactly the events relevant to this
    item's own gate from it (this item's own non-step item events for a detector gate; this
    decision id's own decision events for a decision gate) and never the other kind, in either
    branch — the fail-closed rule this module exists to enforce."""
    ix = events or {}
    if item.get("detector"):
        all_evs = ix.get("items", {}).get(item.get("id"), [])
        evs = [e for e in all_evs if not e.get("step")]
        step_evs = [e for e in all_evs if e.get("step")]
        last = evs[-1] if evs else None
        if last is None and step_evs:
            last = dict(step_evs[-1], state="running")
        return evaluate_detector_gate(item["detector"]["type"], det_result, last)
    if item.get("done_by") == "decision":
        dec_id = item.get("decision", "")
        decision_events = ix.get("decisions", {}).get(dec_id, [])
        return evaluate_decision_gate(item, decisions, decision_events)
    return None
