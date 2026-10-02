# VENDORED REFERENCE (test oracle only) - Stream B, PR #2975 branch pravaha/b6-gochara-seal-workflow, platform/scripts/gochara_seal_brief_extract.py;
# the emit side (seal_brief.emit_lines) must agree with its chunk_brief(), and its extract() must reassemble what we print. Refresh from the PR.
#!/usr/bin/env python3
"""Pull the verifier job's `--brief` output out of its Cloud Run execution logs (R12-2: the brief is produced under the VERIFIER's identity, in the Cloud Run job — this
workflow's identity must never hold the verifier's credential, so the logs are the transport).

Input: `gcloud logging read … --format=json` for ONE execution (an array of log entries). Two transports, never mixed (F-R13-2):
  * SINGLE LINE — one entry whose text is the object `{"brief": …, "persisted": …, "sha256": …}` (a brief that fits one Cloud Logging entry, whose documented limit is 256 KiB).
  * CHUNKED — N entries, each the object `{"brief_chunk": {"index": i, "total": N, "sha256": <hex of the WHOLE single-line text>, "data": <a slice of that text>}}`. Entries are
    reassembled by `index` (arrival order is NEVER relied on); it refuses a missing index, a different `total` or `sha256` between chunks, two DIFFERENT chunks with one index
    (an identical repeat — the logging system's at-least-once delivery — is harmless and collapsed), data of the wrong type, and a reassembly whose sha256 differs from the declared one.
    The reassembled text is then exactly what the single-line transport would have carried, and is checked the same way. (The measured size of a full-generation brief is in
    runbook §6; `chunk_brief` below is the reference implementation of the emit side's contract.)
This script only moves bytes: the payload digest and every content check are `gochara_seal_brief_check.py`'s. Exit 0 ok / 2 refused."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

CHUNK_CHARS = 60_000                       # the emit side's slice length (ASCII text: characters = bytes); well under the entry limit even after JSON string escaping


def chunk_brief(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Reference emit: the lines (one per log entry) that carry `text` — the single-line brief — in slices. Sorted keys, no spaces, like the verifier's own print."""
    if not text or size < 1:
        raise ValueError("nothing to chunk")
    whole = hashlib.sha256(text.encode("utf-8")).hexdigest()
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    return [json.dumps({"brief_chunk": {"data": piece, "index": i, "sha256": whole, "total": len(pieces)}}, sort_keys=True, separators=(",", ":"))
            for i, piece in enumerate(pieces)]


def _text_of(e):
    text = e.get("textPayload")
    if text is None and isinstance(e.get("jsonPayload"), dict):
        text = e["jsonPayload"].get("message")
    return text.strip() if isinstance(text, str) else None


def extract(entries) -> str:
    if not isinstance(entries, list):
        raise ValueError("the log export is not a JSON array")
    singles, chunk_lines = [], []
    for e in entries:
        if not isinstance(e, dict):
            continue
        text = _text_of(e)
        if text is None:
            continue
        if text.startswith('{"brief"'):
            singles.append(text)
        elif text.startswith('{"brief_chunk"'):
            chunk_lines.append(text)
    if singles and chunk_lines:
        raise ValueError("the execution's logs carry both a single-line brief and chunks: ambiguous")
    if chunk_lines:
        return _reassemble(chunk_lines)
    if not singles:
        raise ValueError("no log entry carries the brief (the job refused, or produced nothing)")
    if len(set(singles)) != 1:
        raise ValueError("more than one distinct brief in the execution's logs")
    try:
        json.loads(singles[0])
    except ValueError as exc:
        raise ValueError(f"the brief entry is not valid JSON (truncated or split by the logging system): {exc}") from exc
    return singles[0]


def _reassemble(lines) -> str:
    by_index: dict[int, str] = {}
    total = whole = None
    for line in lines:
        try:
            c = json.loads(line)["brief_chunk"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"a brief chunk is not valid JSON: {exc}") from exc
        if (not isinstance(c, dict) or set(c) != {"index", "total", "sha256", "data"} or isinstance(c["index"], bool) or isinstance(c["total"], bool)
                or not isinstance(c["index"], int) or not isinstance(c["total"], int) or not isinstance(c["sha256"], str) or not isinstance(c["data"], str)):
            raise ValueError("a brief chunk is malformed (keys index/total/sha256/data with the right types)")
        if total is None:
            total, whole = c["total"], c["sha256"]
        elif (c["total"], c["sha256"]) != (total, whole):
            raise ValueError("the chunks disagree on the total or on the whole brief's sha256: two different briefs were emitted")
        if not 0 <= c["index"] < total:
            raise ValueError(f"chunk index {c['index']} is outside 0..{total - 1}")
        if c["index"] in by_index and by_index[c["index"]] != c["data"]:
            raise ValueError(f"two different chunks carry index {c['index']}")
        by_index[c["index"]] = c["data"]
    missing = [i for i in range(total) if i not in by_index]
    if missing:
        raise ValueError(f"the brief is incomplete: chunk(s) {missing[:5]} of {total} missing from the execution's logs")
    text = "".join(by_index[i] for i in range(total))
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != whole:
        raise ValueError("the reassembled brief's sha256 is not the one the chunks declare: altered or reordered data")
    try:
        json.loads(text)
    except ValueError as exc:
        raise ValueError(f"the reassembled brief is not valid JSON: {exc}") from exc
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs-file", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.logs_file, encoding="utf-8") as f:
            text = extract(json.load(f))
    except (ValueError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
