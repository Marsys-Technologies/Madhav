#!/usr/bin/env python3
"""Pull the verifier job's `--brief` output out of its Cloud Run execution logs (R12-2: the brief is produced under the VERIFIER's identity, in the Cloud Run job — this
workflow's identity must never hold the verifier's credential, so the logs are the transport).

Input: `gcloud logging read … --format=json` for ONE execution (an array of log entries, oldest first). The `--brief` mode prints exactly one line, a JSON object
`{"brief": …, "sha256": …}`. This script requires EXACTLY ONE entry whose text is such an object and that parses as JSON; it refuses otherwise — including when the object was
split across several log entries (then the digest could not match, and the chunked-emit mode must be used instead: a fail-closed transport, never a guess). The digest is
re-verified by `gochara_seal_brief_check.py` next; this script only moves bytes. Exit 0 ok / 2 refused."""
from __future__ import annotations

import argparse
import json
import sys


def extract(entries) -> str:
    if not isinstance(entries, list):
        raise ValueError("the log export is not a JSON array")
    hits = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        text = e.get("textPayload")
        if text is None and isinstance(e.get("jsonPayload"), dict):
            text = e["jsonPayload"].get("message")
        if isinstance(text, str) and text.lstrip().startswith('{"brief"'):
            hits.append(text.strip())
    if not hits:
        raise ValueError("no log entry carries the brief (the job refused, produced nothing, or split it across entries — use the chunked emit mode)")
    if len(set(hits)) != 1:
        raise ValueError("more than one distinct brief in the execution's logs")
    try:
        json.loads(hits[0])
    except ValueError as exc:
        raise ValueError(f"the brief entry is not valid JSON (truncated or split by the logging system): {exc}") from exc
    return hits[0]


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
