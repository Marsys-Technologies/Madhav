#!/usr/bin/env python3
"""Check the RETAINED seal brief before anyone approves it and before the sealer is allowed near the database (R12-2).

The brief is the verifier job's `--brief` output: one JSON object `{"brief": <canonical complete approval payload>, "persisted": {brief_id, manifest_id, state_digest}, "sha256": <its digest>}`
(design: `design/SEAL_APPROVAL_PAYLOAD_v1_1.md`, `seal_approval_payload/1`; the shape is Stream A's `verification_job.main`, proven against the REAL output by the round-trip test on the integration ref). This script — stdlib only, no database — refuses unless:
  * the file parses and carries a well-formed 64-hex digest;
  * the digest RECOMPUTED here over the canonical payload equals the declared one (a truncated or altered brief fails: transport integrity);
  * the payload schema is `seal_approval_payload/1`, the manifest is a `candidate`, the candidate gate has NO violation, and the result policy is the milestone's
    `all_null_candidate/1` (explicitly required — the first 5.0 candidate is all-NULL by design);
  * the chart and generation are the ones the workflow was dispatched for;
  * the payload's sealing commit is EXACTLY the workflow's reviewed revision (the commit the sealing code runs from).
On success it prints the digest (and only the digest) to stdout. Exit 0 ok / 2 refused (the reason on stderr).

The canonical-JSON function below mirrors `services.gochara_kernel.window_gate._canon` (sorted keys by code point, no spaces, UTF-8 unescaped, numbers/decimals as text);
`tests/test_gochara_seal_approval_scripts.py` proves it equal to `seal_brief.payload_digest` wherever that module is importable."""
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


def check(text: str, *, chart_id: str, generation: str, sealing_commit: str) -> str:
    if not _SHA.match(sealing_commit or ""):
        raise Refused("the expected sealing commit is not a 40-hex revision")
    try:
        doc = json.loads(text, parse_float=Decimal)
    except ValueError as exc:
        raise Refused(f"the brief is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict) or set(doc) != {"brief", "sha256", "persisted"} or not isinstance(doc.get("brief"), dict):
        raise Refused("the brief must be exactly {brief: <payload>, persisted: <receipt of the persistence>, sha256: <digest>} (the verifier's --brief output)")
    declared = doc["sha256"]
    if not isinstance(declared, str) or not _DIGEST.match(declared):
        raise Refused("the declared digest is not a lowercase 64-hex sha256")
    p = doc["brief"]
    # F-R13-1: the verifier's `--brief` prints `persisted` = {brief_id, manifest_id, state_digest}, the database's own attestation that THIS brief was persisted in
    # `ka_gochara_seal_brief` (the receipt must name a persisted brief). It is not part of the digest; it is REQUIRED (a brief that was not persisted cannot be sealed) and must name
    # the manifest the payload is for.
    per = doc["persisted"]
    if (not isinstance(per, dict) or set(per) != {"brief_id", "manifest_id", "state_digest"} or isinstance(per.get("brief_id"), bool)
            or not isinstance(per.get("brief_id"), int) or per["brief_id"] < 1 or not isinstance(per.get("state_digest"), str)
            or not _DIGEST.match(per["state_digest"])):
        raise Refused("the `persisted` receipt is not {brief_id: <positive integer>, manifest_id, state_digest: <64-hex>}: the brief was not persisted by the verifier")
    if per.get("manifest_id") != (p.get("manifest") or {}).get("manifest_id"):
        raise Refused("the persisted receipt names another manifest than the brief's")
    got = digest(p)
    if got != declared:
        raise Refused(f"the payload hashes to {got}, not the declared {declared}: the brief is truncated or altered")
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
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--sealing-commit", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.brief_file, encoding="utf-8") as f:
            d = check(f.read(), chart_id=a.chart_id, generation=a.generation, sealing_commit=a.sealing_commit)
    except (Refused, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
