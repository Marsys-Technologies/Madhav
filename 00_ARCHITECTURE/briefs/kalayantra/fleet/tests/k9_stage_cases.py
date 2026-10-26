"""Shared fixtures for the K9-4b `k9_rebuild_stage` admission tests: an executor-shaped ops folder with ACCEPTED readbacks of the policy's fixed queries."""
import datetime as dt
import hashlib
import json

import k9_stage_policy as policy

RUN = "6f1d3c1e-0000-4000-8000-000000000001"
NATAL = "7377833e-5d3b-4e70-8bef-1318904f470e"
ARGS = {"assets": "ka_yojaka,ka_sangam", "run-id": RUN, "natal-build": NATAL, "expected-head": "g-0"}
ABSENT = {"build_runs_for_run_id": 0, "candidates_for_run_id": 0, "open_rebuild_runs": 0, "building_candidates": 0}


def iso(seconds=0):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def absence_evidence(run_id=RUN, **over):
    return {"schema": policy.ABSENCE_SCHEMA, "chart_id": policy.CANONICAL_CHART, "run_id": run_id, "measured_at": iso(-60), **ABSENT, **over}


def exposure_evidence(run_id=RUN, head="g-0", **over):
    doc = {"schema": policy.EXPOSURE_SCHEMA, "chart_id": policy.CANONICAL_CHART, "run_id": run_id, "measured_at": iso(-60), "head_generation": head,
           "target_generation": "candidate:" + run_id, "grain_rows": 0, "partition_rows": {t: 0 for t in policy.PARTITIONED_TABLES}}
    doc.update(over)
    return doc


class Ops:
    """A run/ops folder (receipts, done, acceptance) and the same `accepted_readback` bar the executor applies: COMPLETED exit 0, output digest, an ACCEPTED post record."""

    def __init__(self, root):
        self.root = root
        for d in ("receipts", "done", "acceptance"):
            (root / d).mkdir(parents=True, exist_ok=True)

    def readback(self, oid, evidence, query, *, item="K9-4b", accepted=True, sql_sha=None, kind="readback_sql"):
        """Archive one readback_sql the way the executor would have, return the `{name, sha256}` citation of its receipt."""
        request = {"operation_id": oid, "kind": kind, "item_id": item, "idempotency_key": "k-" + oid, "requested_by": "sutradhara", "kyd": "kyd-1",
                   "args": {"sql_file": f"run/ops/sql/{oid}.sql", "sql-sha256": sql_sha or policy.sql_sha256(query)}}
        (self.root / "done" / f"{oid}.json").write_text(json.dumps(request))
        output = "evidence\n" + json.dumps(evidence) + "\n"
        (self.root / "receipts" / f"{oid}.output.txt").write_text(output)
        record = {"operation_id": oid, "kind": kind, "status": "COMPLETED", "exit_code": 0, "output_sha256": sha(output), "request_sha256": sha(json.dumps(request, sort_keys=True))}
        body = json.dumps(record, indent=1).encode()
        (self.root / "receipts" / f"{oid}.json").write_bytes(body)
        if accepted:
            (self.root / "acceptance" / f"{oid}.post.json").write_text(json.dumps({"result": "ACCEPTED", "operation_id": oid, "by": "v1", "request_sha256": record["request_sha256"]}))
        return {"name": f"{oid}.json", "sha256": sha(body)}

    def accepted_readback(self, readback_id, kind):
        record = json.loads((self.root / "receipts" / f"{readback_id}.json").read_text())
        body = (self.root / "receipts" / f"{readback_id}.output.txt").read_bytes()
        accepted = json.loads((self.root / "acceptance" / f"{readback_id}.post.json").read_text())
        if record.get("kind") == kind and record.get("status") == "COMPLETED" and record.get("exit_code") == 0 and sha(body) == record.get("output_sha256") and accepted.get("result") == "ACCEPTED":
            return record, body
        return None

    def request(self, run_id=RUN, absence=None, exposure=None, **over):
        """A `k9_rebuild_stage` request carrying a fresh, accepted absence and exposure readback of the policy's fixed queries (each overridable)."""
        absence = absence_evidence(run_id) if absence is None else absence
        exposure = exposure_evidence(run_id) if exposure is None else exposure
        req = {"operation_id": "stage-1", "kind": "k9_rebuild_stage", "item_id": "K9-4b", "args": {**ARGS, "run-id": run_id}}
        req["absence_readback"] = self.readback("rb-absence", absence, policy.absence_sql(run_id))
        req["exposure_readback"] = self.readback("rb-exposure", exposure, policy.exposure_sql(run_id))
        req.update(over)
        return req
