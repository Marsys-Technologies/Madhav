#!/usr/bin/env python3
"""probe/show.py — eyeball a probe/out/<turn_id>.json file without reading raw JSON.

Usage:
    python3 platform/scripts/probe/show.py platform/scripts/probe/out/<turn_id>.json
"""
import json
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: show.py <path-to-turn.json>", file=sys.stderr)
        return 2

    with open(sys.argv[1]) as f:
        rec = json.load(f)

    print(f"turn_id:           {rec['turn_id']}")
    print(f"question:          {rec['question']}")
    print(f"chart_id:          {rec['chart_id']} ({'explicit' if rec.get('chart_id_explicit') else 'default (synthetic)'})")
    print(f"conversation_id:   {rec.get('conversation_id')}")
    print(f"assistant_msg_id:  {rec.get('assistant_message_id')}")
    print(f"partial:           {rec['partial']}")
    print(f"terminal_status:   {rec['terminal_status']}")
    if rec.get("error"):
        print(f"error:             {rec['error']}")
    tag = rec.get("harness_tag")
    if tag and tag.get("tagged"):
        tag_status = "tagged"
    elif tag:
        tag_status = f"NOT TAGGED ({tag.get('error')})"
    else:
        tag_status = "NOT TAGGED (no conversation_id)"
    print(f"harness_tag:       {tag_status}")
    print(f"total_ms:          {rec['total_ms']}")
    print(f"event_count:       {rec['event_count']}")
    print()

    print(f"blocks ({len(rec['blocks'])}):")
    if not rec["blocks"]:
        print("  (none)")
    for i, b in enumerate(rec["blocks"]):
        kind = b.get("kind") or "paragraph (unclassified — semantic blocks flag was off, or this is the fallback default)"
        role = f", role={b['role']}" if b.get("role") else ""
        print(f"  [{i}] {b['blockId']}: kind={kind}{role}")
    print()

    events = rec.get("events", [])
    citation_events = [e for e in events if e.get("type") == "citation.define"]
    print(f"citations present: {'yes' if citation_events else 'no'} ({len(citation_events)} citation.define event(s))")

    # The receipt is server-side/persisted-only, never on the SSE wire itself —
    # this file can only report whether a message_id exists to check against
    # (i.e. whether the turn persisted far enough to plausibly have one), not
    # whether a receipt row actually exists. A real yes/no needs a DB read
    # against conversation_messages.metadata_json for assistant_message_id —
    # intentionally left out of this file (show.py has no DB creds by design;
    # ask.ts already does one best-effort DB touch, that's enough surface).
    if rec.get("assistant_message_id"):
        print("receipt present:   unknown from this file alone — assistant_message_id exists, "
              "check conversation_messages.metadata_json->>'acharya_reading_receipt' for it directly")
    else:
        print("receipt present:   no (no assistant_message_id — turn did not persist)")
    print()

    print("prose:")
    print(rec.get("prose") or "(empty)")

    return 1 if rec["partial"] else 0


if __name__ == "__main__":
    sys.exit(main())
