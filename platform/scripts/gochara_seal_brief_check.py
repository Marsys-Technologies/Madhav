#!/usr/bin/env python3
"""Check the RETAINED seal brief before anyone approves it and before the sealer is allowed near the database (R12-2).

Inputs (both produced by `gochara_seal_brief_extract.py` from the verifier job's `--brief` logs, Stream A head `a289b38eb`): the BRIEF FILE — the canonical JSON bytes of the
approval payload `seal_approval_payload/1`, whose sha256 IS the brief digest — and the COMPACT FILE, the job's last output line
`{"brief_bytes", "brief_chunks", "brief_file", "contract_version": "seal_brief_transport/1", "persisted": {brief_id, manifest_id, state_digest}, "producer": {commit, execution_id, image_digest},
"sha256", "status": "BRIEFED"}` (design: `design/SEAL_APPROVAL_PAYLOAD_v1_2.md`).
This script — stdlib only, no database — refuses unless:
  * the compact line is a well-formed `BRIEFED` result of contract `seal_brief_transport/1` (unknown or missing = refused) whose `producer` names the commit that produced the brief — it must be the
    sealing commit — the immutable image digest and the execution, and whose `persisted` receipt is {brief_id: positive integer, manifest_id, state_digest: 64-hex} and whose `brief_bytes` is the
    brief file's length (F-R13-1: `persisted` is the database's own attestation that THIS brief was persisted in `ka_gochara_seal_brief`; the seal's receipt must name a persisted brief);
  * the sha256 of the BRIEF FILE'S BYTES equals the declared digest (transport integrity: a truncated or altered brief fails), and the payload re-encoded here in canonical form is
    byte-for-byte the file (so this script's canonical encoder agrees with the verifier's strict one — a disagreement is a refusal, never a different digest);
  * the persisted receipt names the manifest the payload is for;
  * the payload schema is `seal_approval_payload/1`, the manifest is a `candidate`, the candidate gate has NO violation, and the result policy is one of the two NAMED
    policies: `all_null_candidate/1`, or `window_qualification/1` (OD-1, SR-OD1-NUMERICAL) — the latter only when the brief states the frozen qualification table the
    manifest binds and it is this script's OWN literal of that table (`QUALIFICATION_TABLE_BINDING`; a test asserts it equals the sidecar's) and agrees with the code's;
  * under `window_qualification/1` the brief's `numerical_window_gate` verdict is PASSED for the frozen table, every window is counted numbered or blank-with-a-reason-code (honest nulls
    are disclosed, never a refusal by themselves) and the per-grain attestations inside the brief's own `attestations` agree with that summary; the all-NULL brief carries none;
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
POLICY_QUALIFICATION = "window_qualification/1"
ACCEPTED_POLICIES = (POLICY, POLICY_QUALIFICATION)
#: this script's OWN literal of the frozen `window_qualification/1` table binding (stdlib only: nothing imported from the sidecar)
QUALIFICATION_TABLE_BINDING = {"schema": "window_qualification_table/2", "digest": "f2c831a46c32ddb534cb07443e798f6c0fdce448c1b191570565f698ff5de3a9"}
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
FULL_GENERATION = "5.0"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_SHA = re.compile(r"[0-9a-f]{40}")


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


def _inventory_attests_class(payload: dict, cls: dict) -> bool:
    """An empty window-grain set still requires the matching independent inventory.

    The combined candidate gate checks that every INCLUDED grain is verified;
    excluded/computed-empty paths require no invented window attestation.
    """
    digest = cls.get("inventory_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False
    try:
        rows = [json.loads(raw) for raw in
                (payload.get("attestations") or {}).get("ka_gochara_search_inventory_verification", [])]
    except (ValueError, TypeError):
        return False
    mine = [row for row in rows if isinstance(row, dict) and
            (row.get("chart_id"), row.get("generation"), row.get("event_class")) ==
            (payload.get("chart_id"), payload.get("generation"), cls.get("event_class"))]
    return bool(mine) and all(row.get("rederived_inventory_digest") == digest for row in mine)



NUMERICAL_GATE_SCHEMA = "numerical_window_gate/1"
RETIRED_SWITCH_REASON = "dynamic_objective_solver_guarantee_not_available"      # this script's own literal (window_qualification_table/2 retired the dynamic switch)
INCONCLUSIVE_CAP_PER_MILLE = 5          # R-6: the share of windows that may be demoted (0.5 %); this script keeps its own literal (a test compares it with the gate's)


def _count(value, what):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise Refused(f"the numerical-window gate's {what} is {value!r}, not a non-negative integer")
    return value


def check_numerical_gate(p: dict) -> None:
    """OD-1: a `window_qualification/1` brief is approvable only with the NUMERICAL-WINDOW GATE's verdict PASSED, naming the frozen table, with every window counted either
    numbered or blank-with-a-reason (honest nulls are disclosed, never a refusal by themselves), and with the per-grain attestations the verifier persisted — in the brief's own
    `attestations` — agreeing with that summary. The all-NULL brief carries none."""
    gate = p.get("numerical_window_gate")
    if p["result_policy"] != POLICY_QUALIFICATION:
        if gate is not None:
            raise Refused(f"the brief carries a numerical-window gate under {p['result_policy']}")
        return
    if not isinstance(gate, dict) or gate.get("schema") != NUMERICAL_GATE_SCHEMA:
        raise Refused(f"the {POLICY_QUALIFICATION} brief carries no {NUMERICAL_GATE_SCHEMA} verdict")
    if gate.get("status") != "PASSED" or gate.get("problems") != []:
        raise Refused(f"the numerical-window gate is {gate.get('status')!r} ({gate.get('problems')!r}), not PASSED: numbers are sealed only when the independent job re-derived them")
    if gate.get("policy") != POLICY_QUALIFICATION or gate.get("table") != QUALIFICATION_TABLE_BINDING:
        raise Refused(f"the numerical-window gate names policy {gate.get('policy')!r} / table {gate.get('table')!r}, not the frozen {QUALIFICATION_TABLE_BINDING!r}")
    windows, numbered, blank = (_count(gate.get(k), k) for k in ("windows", "numbered_windows", "blank_windows"))
    if numbered + blank != windows:
        raise Refused(f"the numerical-window gate counts {numbered} numbered + {blank} blank windows but {windows} in all")
    honest = gate.get("honest_nulls")
    if not isinstance(honest, list):
        raise Refused("the numerical-window gate lists no honest nulls (an empty list is `[]`)")
    for h in honest:
        if not (isinstance(h, dict) and isinstance(h.get("reason"), str) and h["reason"] and isinstance(h.get("group"), str) and h["group"]
                and isinstance(h.get("path_id"), str)):
            raise Refused(f"an honest null carries no reason code / group: {h!r}")
    if sum(_count(h.get("windows"), "honest-null windows") for h in honest) != blank:
        raise Refused(f"the honest nulls account for {sum(h['windows'] for h in honest)} blank windows, the gate counts {blank}: a blank window has no reason")
    if any(h["reason"] == RETIRED_SWITCH_REASON for h in honest):
        raise Refused(f"an honest null carries the retired reason {RETIRED_SWITCH_REASON!r}: those windows were built without the solver the bound table requires")
    # S3: the blank windows are also counted per GRAIN (class x path x version) and reason, and those counts must account for every blank window
    by_grain = gate.get("honest_nulls_by_grain")
    if not isinstance(by_grain, list):
        raise Refused("the numerical-window gate lists no per-grain honest nulls (an empty list is `[]`)")
    for h in by_grain:
        if not (isinstance(h, dict) and all(isinstance(h.get(k), str) and h[k] for k in ("event_class", "path_id", "rule_version", "reason", "group"))):
            raise Refused(f"a per-grain honest null carries no class / path / version / reason / group: {h!r}")
    if sum(_count(h.get("windows"), "per-grain honest-null windows") for h in by_grain) != blank:
        raise Refused(f"the per-grain honest nulls account for {sum(h['windows'] for h in by_grain)} blank windows, the gate counts {blank}")
    rows = (p.get("attestations") or {}).get("ka_gochara_eval_window_verification")
    if not isinstance(rows, list):
        raise Refused("the brief carries no persisted window-verification rows to check the numerical-window gate against")
    # R-6: the windows the verifier could not settle are DEMOTED to a named blank and capped at 0.5 % of all windows; the gate summary, the persisted attestations and the
    # honest nulls must agree on them, and the cap is re-checked here (a brief that claims PASSED above the cap is refused)
    demoted = _count(gate.get("demoted_windows"), "demoted_windows")
    by_reason = gate.get("demoted_by_reason")
    if not isinstance(by_reason, dict) or sum(_count(v, "demoted windows of a reason") for v in by_reason.values()) != demoted:
        raise Refused(f"the numerical-window gate says {demoted} windows are demoted but its reasons account for {by_reason!r}")
    if demoted * 1000 > windows * INCONCLUSIVE_CAP_PER_MILLE:
        raise Refused(f"{demoted} of {windows} windows are demoted to a named blank: above the {INCONCLUSIVE_CAP_PER_MILLE / 10:g} % cap")
    for reason, n in by_reason.items():
        if sum(h["windows"] for h in honest if h["reason"] == reason) < n:
            raise Refused(f"the {n} windows demoted under {reason!r} are not all disclosed among the honest nulls")
    seen_windows = seen_numbered = seen_demoted = 0
    for line in rows:
        try:
            att = (json.loads(line).get("runner_identity") or {}).get("numerical_window_gate")
        except (TypeError, ValueError, AttributeError) as exc:
            raise Refused(f"a persisted window-verification row is not readable JSON: {exc}") from exc
        if not isinstance(att, dict) or att.get("status") != "PASSED" or att.get("table") != QUALIFICATION_TABLE_BINDING:
            raise Refused(f"a persisted window-verification row carries no PASSED attestation of the frozen table: {att!r}")
        seen_windows += _count(att.get("windows"), "attested windows")
        seen_numbered += _count(att.get("numbered"), "attested numbered windows")
        seen_demoted += sum(_count(v, "attested demoted windows") for v in (att.get("demoted") or {}).values())
    if (seen_windows, seen_numbered, seen_demoted) != (windows, numbered, demoted):
        raise Refused(f"the persisted attestations count {seen_numbered} numbered of {seen_windows} windows with {seen_demoted} demoted; the gate summary says "
                      f"{numbered} of {windows} with {demoted}")


def check(raw: bytes, compact: dict, *, chart_id: str, generation: str, sealing_commit: str) -> str:
    # P08 is the first full candidate's approval path. A caller's expectation
    # cannot authorize a test slice, another chart, or comma-separated overrides.
    if chart_id != CANONICAL_CHART or generation != FULL_GENERATION:
        raise Refused("this seal requires the canonical chart and full generation 5.0")
    if not _SHA.fullmatch(sealing_commit or ""):
        raise Refused("the expected sealing commit is not a 40-hex revision")
    if not isinstance(raw, (bytes, bytearray)) or not raw:
        raise Refused("the brief file is empty")
    if (not isinstance(compact, dict) or set(compact) != {"brief_bytes", "brief_chunks", "brief_file", "contract_version", "persisted", "producer", "sha256", "status"}
            or compact.get("status") != "BRIEFED" or compact.get("brief_chunks") is not True):
        raise Refused("the compact result is not the verifier's `BRIEFED` line {brief_bytes, brief_chunks, brief_file, contract_version, persisted, producer, sha256, status}")
    if compact.get("contract_version") != "seal_brief_transport/1":
        raise Refused(f"the transport contract is {compact.get('contract_version')!r}, not 'seal_brief_transport/1'")
    prod = compact["producer"]
    if (not isinstance(prod, dict) or set(prod) != {"commit", "execution_id", "image_digest"} or not all(isinstance(prod[k], str) and prod[k].strip() for k in prod)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", prod["image_digest"])):
        raise Refused("the `producer` is not {commit, execution_id, image_digest: sha256:<64-hex>}: a brief of unknown producer is refused")
    if prod["commit"] != sealing_commit:
        raise Refused(f"the brief was produced by code at commit {prod['commit']!r}, not this workflow's reviewed revision {sealing_commit}")
    declared = compact["sha256"]
    if not isinstance(declared, str) or not _DIGEST.fullmatch(declared):
        raise Refused("the declared digest is not a lowercase 64-hex sha256")
    if isinstance(compact["brief_bytes"], bool) or compact["brief_bytes"] != len(raw):
        raise Refused(f"the compact line says {compact['brief_bytes']!r} brief bytes, the brief file has {len(raw)}")
    got = hashlib.sha256(bytes(raw)).hexdigest()
    if got != declared:
        raise Refused(f"the brief file hashes to {got}, not the declared {declared}: the brief is truncated or altered")
    per = compact["persisted"]
    if (not isinstance(per, dict) or set(per) != {"brief_id", "manifest_id", "state_digest"} or isinstance(per.get("brief_id"), bool)
            or not isinstance(per.get("brief_id"), int) or per["brief_id"] < 1 or not isinstance(per.get("state_digest"), str)
            or not _DIGEST.fullmatch(per["state_digest"])):
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
    if p.get("result_policy") not in ACCEPTED_POLICIES:
        raise Refused(f"the result policy is {p.get('result_policy')!r}; this milestone requires {POLICY} or {POLICY_QUALIFICATION} (with its frozen table bound)")
    table = p.get("qualification_table")
    if p["result_policy"] == POLICY_QUALIFICATION:
        if table != {"bound": QUALIFICATION_TABLE_BINDING, "implemented": QUALIFICATION_TABLE_BINDING, "agrees": True}:
            raise Refused(f"the brief's qualification table {table!r} is not the frozen {QUALIFICATION_TABLE_BINDING!r} bound by the manifest and implemented by the code")
    elif table is not None:
        raise Refused(f"the brief carries a qualification table under {p['result_policy']}")
    check_numerical_gate(p)
    code_commit = (p.get("code") or {}).get("sealing_commit")
    if code_commit != sealing_commit:
        raise Refused(f"the brief was produced for sealing revision {code_commit!r}, not this workflow's reviewed revision {sealing_commit}")
    for c in p.get("classes") or []:
        if not c.get("grains") and not _inventory_attests_class(p, c):
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
