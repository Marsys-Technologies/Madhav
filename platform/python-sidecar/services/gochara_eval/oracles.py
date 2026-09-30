"""Oracle-file validation and execution registry (design spec §11.1).

Oracles are DATA, executed by B5.3 (this harness) and A5.5 (the rehearsal).
This module's job is inventory, validation, and a registry of which oracle is
executed where — not rule-layer execution:

  * `fixture_kind: literal` oracles are owned by the rule layer and executed
    in services/gochara_rules' pytest suite;
  * `fixture_kind: executable_at_A5.5` oracles are written as literal-input
    tests at the A5.5 rehearsal (the A5.5 review checks the named mutation
    fails);
  * `constrained_generator` fixtures are rejected by v1_4 (amendment 5) and
    treated as an error here.

Validation enforces the header count rule: oracle_count == len(oracles); a
mismatch is itself a defect.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# fixture_kind → where the oracle is executed (spec §11.1 harness contract).
EXECUTION_SITE = {
    "literal": "gochara_rules_pytest",       # rule layer's pytest suite
    "executable_at_A5.5": "a5_5_rehearsal",  # Stream A writes literal-input test
}

REQUIRED_FIELDS = ("id", "guards", "defects", "given", "when", "then",
                   "mutation_that_must_fail", "fixture_kind")


class OracleFileError(ValueError):
    """Oracle file failed validation (count rule, fields, or fixture kinds)."""


@dataclass
class OracleRecord:
    """Inventory entry: one oracle, its execution site, and its status."""

    oid: str
    fixture_kind: str
    executed_at: str          # gochara_rules_pytest | a5_5_rehearsal
    guards: str
    defects: list[str]
    status: str = "REGISTERED"  # REGISTERED | PASS | FAIL | NOT_RUN (recorded by callers)


@dataclass
class OracleRegistry:
    version: str
    oracle_count: int
    split: dict[str, int]               # fixture_kind -> count
    records: dict[str, OracleRecord] = field(default_factory=dict)

    def record_status(self, oid: str, status: str) -> None:
        if oid not in self.records:
            raise OracleFileError(f"unknown oracle id {oid!r}")
        if status not in ("REGISTERED", "PASS", "FAIL", "NOT_RUN"):
            raise OracleFileError(f"invalid oracle status {status!r}")
        self.records[oid].status = status

    def as_dict(self) -> dict:
        return {"version": self.version, "oracle_count": self.oracle_count,
                "fixture_kind_split": self.split,
                "oracles": {oid: {"fixture_kind": r.fixture_kind,
                                  "executed_at": r.executed_at,
                                  "guards": r.guards, "defects": r.defects,
                                  "status": r.status}
                            for oid, r in self.records.items()}}


def load_oracles(path: str | Path) -> OracleRegistry:
    """Load and validate a GOCHARA_TEST_ORACLES JSON file.

    Enforces: header count rule (oracle_count == len(oracles)), required
    fields per oracle, unique ids, known fixture kinds.
    """
    path = Path(path)
    doc = json.loads(path.read_text())
    oracles = doc.get("oracles")
    if not isinstance(oracles, list):
        raise OracleFileError("oracle file has no oracles list")
    declared = doc.get("oracle_count")
    if declared != len(oracles):
        raise OracleFileError(
            f"count rule violated: header oracle_count={declared} "
            f"!= len(oracles)={len(oracles)} — a mismatch is itself a defect")

    records: dict[str, OracleRecord] = {}
    split: dict[str, int] = {}
    for o in oracles:
        missing = [f for f in REQUIRED_FIELDS if f not in o]
        if missing:
            raise OracleFileError(
                f"oracle {o.get('id')!r} missing required fields {missing}")
        kind = o["fixture_kind"]
        if kind not in EXECUTION_SITE:
            raise OracleFileError(
                f"oracle {o['id']} has unknown fixture_kind {kind!r} "
                "(v1_4 admits only literal / executable_at_A5.5)")
        if o["id"] in records:
            raise OracleFileError(f"duplicate oracle id {o['id']!r}")
        records[o["id"]] = OracleRecord(
            oid=o["id"], fixture_kind=kind, executed_at=EXECUTION_SITE[kind],
            guards=o["guards"], defects=list(o["defects"]))
        split[kind] = split.get(kind, 0) + 1

    return OracleRegistry(version=str(doc.get("version")),
                          oracle_count=declared, split=split, records=records)


def oracle_execution_registry(path: str | Path) -> dict:
    """Convenience: validated file → {oracle_id: execution_site} mapping."""
    reg = load_oracles(path)
    return {oid: r.executed_at for oid, r in reg.records.items()}
