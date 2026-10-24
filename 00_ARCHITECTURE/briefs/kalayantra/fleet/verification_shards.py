#!/usr/bin/env python3
"""The pinned class SHARDS of the Gochara verification job (SR-OD1 R8; RECONCILIATION R-8, SR-R8-SHARDED) and the G-5 capacity arithmetic.

One whole-generation verification execution of the 26 classes cannot fit the verification job's 28,800 s task timeout (PLAN.md 2.5: 1.8-3.8 ks/class + the solver check). The
launch is therefore split into SHARDS: `fleet/VERIFY_SHARDS.json` (schema `ky.verification_shards/1`) pins the partition — shard id -> classes — and is the ONE list both the
rehearsal (`verification_job_dryrun --shard V03`) and the dispatch (`verification_job --shard V03`) read, so they run the same shards. Its sha256 is recorded in every launch record.

  * `load()`           reads and VALIDATES the pinned file (schema, generation, distinct ids, distinct classes, a class in exactly one shard, the declared total);
  * `classes_for(id)`  the classes of one shard (an unknown id refuses);
  * `shard_capacity`   G-5, per shard: measured wall <= wall_fraction x task timeout (null when the wall was not measured: unknown is never green);
  * `projection`       G-5, whole: the measured per-class mean x the pinned class total <= shards x task timeout, and no shard's projected wall over its budget.

The partition's UNION is checked against the manifest's pinned `scored_classes` by the job itself (the aggregate, `numerical_window_gate.generation_verdict`, refuses a class no shard
attested); this module cannot see the database and holds no credential.

  verification_shards.py capacity RECORD.json [RECORD.json ...]   each file holds a `verification_launch` dry-run record (the first JSON line of its output); prints the projection;
  verification_shards.py serial RECORD.json                       the whole-generation dry-run record: SERIAL is the primary path iff its effective wall <= 0.75 x timeout, else SHARDED;
  verification_shards.py overlap RECORD_A.json RECORD_B.json      two shard dry runs launched together: overlap, union wall, speedup (the trial's two-shard overlap measurement)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
SHARDS_PATH = HERE / "VERIFY_SHARDS.json"
SCHEMA = "ky.verification_shards/1"
SHARD_ID = re.compile(r"V[0-9]{2}")
CLASS_NAME = re.compile(r"[a-z][a-z0-9_]{1,59}")


class Refused(RuntimeError):
    pass


def load(path: Path = SHARDS_PATH) -> tuple[dict, str]:
    """(validated document, sha256 of its bytes). Refuses a file that is not the pinned shape; never repairs one."""
    raw = Path(path).read_bytes()
    try:
        doc = json.loads(raw)
    except ValueError:
        raise Refused("VERIFY_SHARDS.json is not JSON") from None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise Refused(f"VERIFY_SHARDS.json: schema is not {SCHEMA}")
    for key in ("task_timeout_s", "classes_total"):
        if not isinstance(doc.get(key), int) or isinstance(doc[key], bool) or doc[key] <= 0:
            raise Refused(f"VERIFY_SHARDS.json: {key} is not a positive integer")
    fraction = doc.get("wall_fraction")
    if not isinstance(fraction, (int, float)) or isinstance(fraction, bool) or not 0 < fraction <= 1:
        raise Refused("VERIFY_SHARDS.json: wall_fraction is not in (0, 1]")
    shards = doc.get("shards")
    if not isinstance(shards, list) or not shards:
        raise Refused("VERIFY_SHARDS.json: no shards")
    ids, seen = [], {}
    for shard in shards:
        sid, classes = (shard.get("id"), shard.get("classes")) if isinstance(shard, dict) else (None, None)
        if not (isinstance(sid, str) and SHARD_ID.fullmatch(sid)):
            raise Refused(f"VERIFY_SHARDS.json: shard id {sid!r} is not V<two digits>")
        if not (isinstance(classes, list) and classes and all(isinstance(c, str) and CLASS_NAME.fullmatch(c) for c in classes) and len(set(classes)) == len(classes)):
            raise Refused(f"VERIFY_SHARDS.json: shard {sid} has no classes, a malformed or a repeated class name")
        ids.append(sid)
        for c in classes:
            if c in seen:
                raise Refused(f"VERIFY_SHARDS.json: class {c} is in shards {seen[c]} and {sid}")
            seen[c] = sid
    if len(set(ids)) != len(ids):
        raise Refused("VERIFY_SHARDS.json: a shard id is repeated")
    if len(seen) != doc["classes_total"]:
        raise Refused(f"VERIFY_SHARDS.json: the shards hold {len(seen)} classes, the file declares {doc['classes_total']}")
    return doc, hashlib.sha256(raw).hexdigest()


def classes_for(shard_id: str, doc: dict) -> list[str]:
    for shard in doc["shards"]:
        if shard["id"] == shard_id:
            return list(shard["classes"])
    raise Refused(f"unknown verification shard {shard_id!r}")


def shard_capacity(wall_s, n_classes: int, doc: dict) -> dict:
    """G-5 for ONE shard: `within_budget` is wall <= wall_fraction x task timeout, or null when the wall was not measured."""
    budget = doc["wall_fraction"] * doc["task_timeout_s"]
    measured = isinstance(wall_s, (int, float)) and not isinstance(wall_s, bool)
    return {"wall_s": wall_s if measured else None, "classes": n_classes, "budget_s": budget,
            "per_class_s": round(wall_s / n_classes, 3) if measured and n_classes else None,
            "within_budget": (wall_s <= budget) if measured else None}


def projection(measured: list[dict], doc: dict) -> dict:
    """G-5 for the whole generation, from the per-shard `shard_capacity` records measured so far. The projected total is the mean measured seconds per class times the pinned class
    total and must be <= shards x task timeout; every shard's projected wall (mean per class x its size) must also be <= its budget. `ok` is null until at least one wall is measured."""
    walls = [m for m in measured if m.get("per_class_s") is not None]
    ceiling = len(doc["shards"]) * doc["task_timeout_s"]
    if not walls:
        return {"ok": None, "measured_shards": 0, "shards": len(doc["shards"]), "ceiling_s": ceiling, "projected_total_s": None, "problems": ["no shard wall measured"]}
    mean = sum(m["wall_s"] for m in walls) / sum(m["classes"] for m in walls)
    total = round(mean * doc["classes_total"], 3)
    budget = doc["wall_fraction"] * doc["task_timeout_s"]
    problems = [f"measured shard with {m['classes']} classes took {m['wall_s']} s, over its budget {budget} s" for m in walls if m["wall_s"] > budget]
    problems += [f"shard {s['id']} projects to {round(mean * len(s['classes']), 3)} s, over its budget {budget} s" for s in doc["shards"] if mean * len(s["classes"]) > budget]
    if total > ceiling:
        problems.append(f"projected total {total} s exceeds shards x timeout {ceiling} s")
    return {"ok": not problems, "measured_shards": len(walls), "shards": len(doc["shards"]), "mean_per_class_s": round(mean, 3), "ceiling_s": ceiling,
            "projected_total_s": total, "problems": problems}


def serial_decision(record: dict, doc: dict) -> dict:
    """B4 (ruling SR-A10-1): the SERIAL single whole-generation execution is the PRIMARY path if its EFFECTIVE wall (the dry run's measured completionTime - startTime of the whole
    26-class `--report-only` execution, certificate verifier included) fits within wall_fraction x the task timeout; the class shards are the FALLBACK. `record` is a whole-generation
    dry-run record (no shard). `path` is 'serial' | 'sharded' | null (wall not measured: unknown is not 'serial')."""
    ran = record.get("report_only_run") or {}
    if record.get("shard"):
        return {"path": None, "reason": "a shard record cannot decide the serial path: run the whole-generation dry run"}
    cap = shard_capacity(ran.get("execution_wall_s"), doc["classes_total"], doc)
    path = None if cap["within_budget"] is None else ("serial" if cap["within_budget"] else "sharded")
    return {"path": path, "capacity": cap}


def overlap(a: dict, b: dict) -> dict:
    """The TWO-SHARD OVERLAP measurement the trial (TR) can run: launch two shards' dry runs at the same time and pass their two dry-run records. From the executions' own start and
    completion times: the overlap in seconds, the union (effective) wall, the sum of the two walls and `speedup` = sum / union (2.0 = fully parallel, 1.0 = they serialised on the chart
    lock). `overlapped` is false when the executions did not run at the same time (nothing is concluded then). Times unread -> null."""
    from datetime import datetime

    def span(record):
        ran = record.get("report_only_run") or {}
        try:
            return tuple(datetime.fromisoformat(ran[k].replace("Z", "+00:00")) for k in ("start_time", "completion_time"))
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
    sa, sb = span(a), span(b)
    if sa is None or sb is None or sa[1] < sa[0] or sb[1] < sb[0]:
        return {"overlapped": None, "overlap_s": None, "union_wall_s": None, "sum_wall_s": None, "speedup": None}
    start, end = min(sa[0], sb[0]), max(sa[1], sb[1])
    inter = (min(sa[1], sb[1]) - max(sa[0], sb[0])).total_seconds()
    walls = [(x[1] - x[0]).total_seconds() for x in (sa, sb)]
    union = (end - start).total_seconds() if inter > 0 else None
    return {"overlapped": inter > 0, "overlap_s": round(max(inter, 0.0), 3), "union_wall_s": union, "sum_wall_s": round(sum(walls), 3),
            "speedup": round(sum(walls) / union, 3) if union else None}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] not in ("capacity", "serial", "overlap") or (argv[0] == "overlap") != (len(argv) == 3) or (argv[0] == "serial" and len(argv) != 2):
        print(__doc__, file=sys.stderr)
        return 2
    doc, digest = load()
    first = lambda name: json.loads(Path(name).read_text().splitlines()[0])  # noqa: E731
    if argv[0] == "serial":
        result = serial_decision(first(argv[1]), doc)
        print(json.dumps({"shards_sha256": digest, **result}, sort_keys=True))
        return 0 if result["path"] else 1
    if argv[0] == "overlap":
        print(json.dumps({"shards_sha256": digest, **overlap(first(argv[1]), first(argv[2]))}, sort_keys=True))
        return 0
    measured = []
    for name in argv[1:]:
        record = json.loads(Path(name).read_text().splitlines()[0])
        ran = record.get("report_only_run") or {}
        shard = record.get("shard") or {}
        measured.append(shard_capacity(ran.get("execution_wall_s"), len(shard.get("classes") or ()), doc))
    result = projection(measured, doc)
    print(json.dumps({"shards_sha256": digest, **result}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
