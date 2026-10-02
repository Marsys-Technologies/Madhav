#!/usr/bin/env python3
"""Check the RETAINED seal brief before anyone approves it and before the sealer is allowed near the database (R12-2).

Inputs (both produced by `gochara_seal_brief_extract.py` from the verifier job's `--brief --brief-chunks` logs, Stream A head `7e81f2870`): the BRIEF FILE — the canonical JSON bytes of the
approval payload `seal_approval_payload/1`, whose sha256 IS the brief digest — and the COMPACT FILE, the job's last output line
`{"brief_bytes", "brief_chunks", "brief_file", "persisted": {brief_id, manifest_id, state_digest}, "sha256", "status": "BRIEFED"}` (design: `design/SEAL_APPROVAL_PAYLOAD_v1_2.md`).
This script — stdlib only, no database — refuses unless:
  * the compact line is a well-formed `BRIEFED` result whose `persisted` receipt is {brief_id: positive integer, manifest_id, state_digest: 64-hex} and whose `brief_bytes` is the
    brief file's length (F-R13-1: `persisted` is the database's own attestation that THIS brief was persisted in `ka_gochara_seal_brief`; the seal's receipt must name a persisted brief);
  * the sha256 of the BRIEF FILE'S BYTES equals the declared digest (transport integrity: a truncated or altered brief fails), and the payload re-encoded here in canonical form is
    byte-for-byte the file (so this script's canonical encoder agrees with the verifier's strict one — a disagreement is a refusal, never a different digest);
  * the persisted receipt names the manifest the payload is for;
  * the payload schema is `seal_approval_payload/1`, the manifest is a `candidate`, the candidate gate has NO violation, and the result policy is the milestone's
    `all_null_candidate/1` (explicitly required — the first 5.0 candidate is all-NULL by design);
  * the chart and generation are the ones the workflow was dispatched for;
  * the payload's sealing commit is EXACTLY the workflow's reviewed revision (the commit the sealing code runs from).
On success it prints the digest (and only the digest) to stdout. Exit 0 ok / 2 refused (the reason on stderr).

The canonical-JSON function below mirrors `services.gochara_kernel.seal_brief.canonical_json` / `window_gate._canon` (sorted keys by code point, no spaces, UTF-8 unescaped,
numbers/decimals as plain text); the tests prove it equal to the sidecar's own wherever that module is importable (the integration ref)."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal

SCHEMA = "seal_approval_payload/1"
POLICY = "all_null_candidate/1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def canon(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, Decimal)):
        return format(v, "f") if isinstance(v, Decimal) else str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canon(v[k]) for k in sorted(v)) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(canon(x) for x in v) + "]"
    raise TypeError(f"no canonical JSON for {type(v).__name__}")


def digest(payload) -> str:
    return hashlib.sha256(canon(payload).encode("utf-8")).hexdigest()


class Refused(Exception):
    pass


def check(raw: bytes, compact: dict, *, chart_id: str, generation: str, sealing_commit: str) -> str:
    if not _SHA.match(sealing_commit or ""):
        raise Refused("the expected sealing commit is not a 40-hex revision")
    if not isinstance(raw, (bytes, bytearray)) or not raw:
        raise Refused("the brief file is empty")
    if (not isinstance(compact, dict) or set(compact) != {"brief_bytes", "brief_chunks", "brief_file", "persisted", "sha256", "status"} or compact.get("status") != "BRIEFED"
            or compact.get("brief_chunks") is not True):
        raise Refused("the compact result is not the verifier's `BRIEFED` line {brief_bytes, brief_chunks, brief_file, persisted, sha256, status}")
    declared = compact["sha256"]
    if not isinstance(declared, str) or not _DIGEST.match(declared):
        raise Refused("the declared digest is not a lowercase 64-hex sha256")
    if isinstance(compact["brief_bytes"], bool) or compact["brief_bytes"] != len(raw):
        raise Refused(f"the compact line says {compact['brief_bytes']!r} brief bytes, the brief file has {len(raw)}")
    got = hashlib.sha256(bytes(raw)).hexdigest()
    if got != declared:
        raise Refused(f"the brief file hashes to {got}, not the declared {declared}: the brief is truncated or altered")
    per = compact["persisted"]
    if (not isinstance(per, dict) or set(per) != {"brief_id", "manifest_id", "state_digest"} or isinstance(per.get("brief_id"), bool)
            or not isinstance(per.get("brief_id"), int) or per["brief_id"] < 1 or not isinstance(per.get("state_digest"), str)
            or not _DIGEST.match(per["state_digest"])):
        raise Refused("the `persisted` receipt is not {brief_id: <positive integer>, manifest_id, state_digest: <64-hex>}: the brief was not persisted by the verifier")
    try:
        p = json.loads(bytes(raw).decode("utf-8"), parse_float=Decimal)
    except (ValueError, UnicodeDecodeError) as exc:
        raise Refused(f"the brief is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(p, dict):
        raise Refused("the brief is not a JSON object")
    try:
        canonical = canon(p).encode("utf-8")
    except TypeError as exc:
        raise Refused(f"the brief carries a value with no canonical form: {exc}") from exc
    if canonical != bytes(raw):
        raise Refused("the brief file is not in canonical form (this script's canonical encoder and the verifier's disagree): refused rather than approved under a digest the two sides would compute differently")
    if per.get("manifest_id") != (p.get("manifest") or {}).get("manifest_id"):
        raise Refused("the persisted receipt names another manifest than the brief's")
    if p.get("schema") != SCHEMA:
        raise Refused(f"unexpected payload schema {p.get('schema')!r}")
    if p.get("chart_id") != chart_id or p.get("generation") != generation:
        raise Refused("the brief is for another chart or generation than the one this run was dispatched for")
    if (p.get("manifest") or {}).get("status") != "candidate":
        raise Refused("the manifest is not a candidate")
    gate = (p.get("candidate_gate") or {}).get("violations")
    if gate != []:
        raise Refused(f"the candidate gate is not clean: {gate!r}")
    if p.get("result_policy") != POLICY:
        raise Refused(f"the result policy is {p.get('result_policy')!r}; this milestone requires {POLICY}")
    code_commit = (p.get("code") or {}).get("sealing_commit")
    if code_commit != sealing_commit:
        raise Refused(f"the brief was produced for sealing revision {code_commit!r}, not this workflow's reviewed revision {sealing_commit}")
    for c in p.get("classes") or []:
        if not c.get("grains"):
            raise Refused(f"class {c.get('event_class')!r} has no persisted verification")
        for g in c["grains"]:
            if g.get("status") != "VERIFIED":
                raise Refused(f"{c.get('event_class')}/{g.get('path_id')}@{g.get('rule_version')} is {g.get('status')!r}, not VERIFIED")
    if not p.get("classes"):
        raise Refused("the brief carries no classes")
    return declared


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief-file", required=True)
    ap.add_argument("--compact-file", required=True)
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--sealing-commit", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.brief_file, "rb") as f:
            raw = f.read()
        with open(a.compact_file, encoding="utf-8") as f:
            compact = json.load(f)
        d = check(raw, compact, chart_id=a.chart_id, generation=a.generation, sealing_commit=a.sealing_commit)
    except (Refused, OSError, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
