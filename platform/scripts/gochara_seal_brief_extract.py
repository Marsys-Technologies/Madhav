#!/usr/bin/env python3
"""Pull the verifier job's `--brief` output out of its Cloud Run execution logs (R12-2: the brief is produced under the VERIFIER's identity, in the Cloud Run job — this
workflow's identity must never hold the verifier's credential, so the logs are the transport).

Stream A's `--brief` output (always chunked since head a289b38eb) (F-R13-2; the brief is ~255 KB at 26 classes, beyond a log entry): N chunk lines, then ONE compact result line, one JSON object each —
    {"b64": <base64 of the i-th slice>, "brief_chunk": i, "of": N, "sha256": <digest of the WHOLE brief bytes>}
    {"brief_bytes": <int>, "brief_chunks": true, "brief_file": null, "persisted": {brief_id, manifest_id, state_digest}, "sha256": <digest>, "status": "BRIEFED"}
The brief is the CANONICAL JSON of the approval payload; its sha256 IS the brief digest. This script reassembles it from the execution's `gcloud logging read … --format=json`
export (an array of log entries) and writes TWO files: the brief bytes (`--out-brief`) and the compact line (`--out-compact`). It refuses: no compact line, more than one distinct
compact line, a compact line that is not `status: BRIEFED` (a `REFUSED`/`ERROR` result is reported by name), a missing chunk index, two DIFFERENT chunks with one index (an identical
repeat — at-least-once delivery — is collapsed), chunks that disagree on `of` or `sha256`, an undecodable slice, a reassembly whose sha256 or length differs from what the compact line
declares, and chunks that the compact line does not announce. Arrival order is never relied on. It only moves bytes: every CONTENT check is `gochara_seal_brief_check.py`'s.
Exit 0 ok / 2 refused."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys

_HEX = re.compile(r"[0-9a-f]{64}")
_COMPACT_KEYS = {"brief_bytes", "brief_chunks", "brief_file", "persisted", "sha256", "status"}
_CHUNK_KEYS = {"b64", "brief_chunk", "of", "sha256"}
CHUNK_RAW_BYTES = 48 * 1024


def _object_of(e):
    """The JSON object one log entry carries, or None for a line that is not ours. Cloud Run PARSES a JSON object printed on stdout into the entry's ROOT `jsonPayload` (R13-1 —
    the representation the real logs have); `jsonPayload.message` (a string holding the object) and `textPayload` (the object as text) are accepted as FALLBACKS and go through the
    SAME strict validation as the root form. Log LABELS and resource fields are never consulted: they are not producer attestation (see runbook §6)."""
    jp = e.get("jsonPayload")
    if isinstance(jp, dict):
        if "brief_chunk" in jp or "status" in jp:
            return jp
        text = jp.get("message")
    else:
        text = e.get("textPayload")
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text.startswith("{"):
        return None
    try:
        doc = json.loads(text)
    except ValueError:
        return None                                                        # a log line that is not ours (a library message) — ignored; ours are validated below
    return doc if isinstance(doc, dict) else None


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def extract(entries) -> tuple[bytes, dict]:
    """(brief bytes, compact result) from the execution's log entries."""
    if not isinstance(entries, list):
        raise ValueError("the log export is not a JSON array")
    chunks: dict[int, dict] = {}
    compacts: list[dict] = []
    for e in entries:
        doc = _object_of(e) if isinstance(e, dict) else None
        if doc is None:
            continue
        if "brief_chunk" in doc:
            if set(doc) != _CHUNK_KEYS or not _is_int(doc["brief_chunk"]) or not _is_int(doc["of"]) or not isinstance(doc["sha256"], str) or not isinstance(doc["b64"], str):
                raise ValueError("a brief chunk is malformed (keys b64/brief_chunk/of/sha256 with the right types)")
            if doc["brief_chunk"] in chunks and chunks[doc["brief_chunk"]] != doc:
                raise ValueError(f"two different chunks carry index {doc['brief_chunk']}")
            chunks[doc["brief_chunk"]] = doc
        elif doc.get("status") in ("REFUSED", "ERROR"):
            raise ValueError(f"the verification job did not produce a brief: status {doc.get('status')!r}, code {doc.get('code')!r}: {str(doc.get('detail'))[:300]}")
        elif doc.get("status") == "BRIEFED":
            if doc not in compacts:
                compacts.append(doc)
    if not compacts:
        raise ValueError("no compact `BRIEFED` result line in the execution's logs (the job refused, produced nothing, or its output was cut)")
    if len(compacts) > 1:
        raise ValueError("more than one distinct `BRIEFED` result line in the execution's logs")
    c = compacts[0]
    if set(c) != _COMPACT_KEYS or not _is_int(c["brief_bytes"]) or c["brief_bytes"] < 1 or not isinstance(c["sha256"], str) or not _HEX.fullmatch(c["sha256"]) or not isinstance(c["persisted"], dict):
        raise ValueError("the compact result line is malformed (keys brief_bytes/brief_chunks/brief_file/persisted/sha256/status)")
    if c["brief_chunks"] is not True:
        raise ValueError("the compact line does not announce chunks (`brief_chunks` is not true): the brief is not in the logs")
    if not chunks:
        raise ValueError("the compact line announces chunks but none are in the execution's logs")
    total, whole = None, None
    for i in sorted(chunks):
        d = chunks[i]
        if total is None:
            total, whole = d["of"], d["sha256"]
        elif (d["of"], d["sha256"]) != (total, whole):
            raise ValueError("the chunks disagree on the total or on the whole brief's sha256: two different briefs were emitted")
    if total < 1 or sorted(chunks) != list(range(total)):
        missing = [i for i in range(max(total, 0)) if i not in chunks]
        raise ValueError(f"the brief is incomplete or has foreign chunks: chunk(s) {missing[:5]} of {total} missing or an index outside 0..{total - 1}")
    try:
        raw = b"".join(base64.b64decode(chunks[i]["b64"], validate=True) for i in range(total))
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"a brief chunk is not valid base64: {exc}") from exc
    got = hashlib.sha256(raw).hexdigest()
    if got != whole or whole != c["sha256"]:
        raise ValueError("the reassembled brief's sha256 is not the one the chunks and the compact line declare: altered, reordered or mixed data")
    if len(raw) != c["brief_bytes"]:
        raise ValueError(f"the reassembled brief is {len(raw)} bytes, the compact line says {c['brief_bytes']}")
    return raw, c


def chunk_lines(raw: bytes, digest: str, chunk_bytes: int = CHUNK_RAW_BYTES) -> list[str]:
    """Reference emit — what Stream A's `seal_brief.brief_chunk_lines` prints (canonical JSON, sorted keys, no spaces); used by the tests."""
    parts = [raw[i:i + chunk_bytes] for i in range(0, len(raw), chunk_bytes)] or [b""]
    return [json.dumps({"b64": base64.b64encode(p).decode("ascii"), "brief_chunk": i, "of": len(parts), "sha256": digest}, sort_keys=True, separators=(",", ":"))
            for i, p in enumerate(parts)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs-file", required=True)
    ap.add_argument("--out-brief", required=True)
    ap.add_argument("--out-compact", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.logs_file, encoding="utf-8") as f:
            raw, compact = extract(json.load(f))
    except (ValueError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out_brief, "wb") as f:
        f.write(raw)
    with open(a.out_compact, "w", encoding="utf-8") as f:
        json.dump(compact, f, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
