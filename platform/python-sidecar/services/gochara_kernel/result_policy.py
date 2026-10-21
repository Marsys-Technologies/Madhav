"""The numeric-RESULT policy a generation is built, verified and gated under (Codex round 9, R9-1).

Two named policies; the generation's MANIFEST selects one (the `result_policy` key of the input vector, schema /3) and
nothing downstream holds its own constant:

  `all_null_candidate/1`   this milestone. EVERY numerical result field of EVERY window — score, evidence_for,
                           evidence_against, objective_value, severity — is NULL for every path and every channel
                           composition (constant and empty-sum objectives included: "dynamic solving disabled" is not
                           "all NULL"), the peak is absent and the valence `unqualified`. Geometry, supports,
                           identifiers, memberships and the accounting counts stay populated. A window that carries a
                           number while this policy is in force is refused by the verifier and by the candidate gate.
  `window_qualification/1` the policy that applies when numbers are ENABLED: the frozen qualification table documented in
                           `window_sweep.draft_windows` (and re-implemented independently in `window_verifier`).

The independent verifier and the SQL gate keep their OWN copies of these literals (independence); tests assert equality.
"""
from __future__ import annotations

import hashlib
import json

POLICY_ALL_NULL = "all_null_candidate/1"
POLICY_QUALIFICATION = "window_qualification/1"
RESULT_POLICIES = (POLICY_ALL_NULL, POLICY_QUALIFICATION)
DEFAULT_RESULT_POLICY = POLICY_ALL_NULL
#: the named reason every window carries under `all_null_candidate/1`
ALL_NULL_REASON = "all_null_candidate_policy"
#: the numerical RESULT fields the all-NULL policy nulls (the peak instant and the valence are nulled/pinned beside them)
NUMERIC_RESULT_FIELDS = ("score", "evidence_for", "evidence_against", "objective_value", "severity")


#: OD-1 (SR-OD1-NUMERICAL): the FROZEN `window_qualification/1` table, as data. It is the specification `window_sweep.draft_windows` implements and
#: `window_verifier` re-implements independently; its digest is BOUND in the manifest's input vector (`qualification_table`) whenever the generation's
#: policy is `window_qualification/1`, so a generation drafted under one table can never be verified, briefed or sealed under another. Editing a rule here
#: moves the digest — a new table is a new generation, never a silent continuation.
QUALIFICATION_TABLE_SCHEMA = "window_qualification_table/1"
DYNAMIC_SWITCH_REASON = "dynamic_objective_solver_guarantee_not_available"
QUALIFICATION_TABLE = {
    "schema": QUALIFICATION_TABLE_SCHEMA,
    "policy": POLICY_QUALIFICATION,
    "result_fields": ["peak_instant", "score", "evidence_for", "evidence_against", "outcome_valence_for_native"],
    "severity": "always NULL (ruled)",
    "objective": {"P4": "max-min of the two agents' activity", "other_paths": "evidence_for = sum over roots of the per-root max for-channel value"},
    "rules": [
        {"n": 1, "when": "an unqualified member whose channel is for or unknown",
         "then": "objective unqualified: peak, score, evidence_for, evidence_against NULL; reason = the first unresolved reason, sorted"},
        {"n": 2, "when": "a qualified function-valued member",
         "then": f"unqualified under {DYNAMIC_SWITCH_REASON} (the named switch)"},
        {"n": 3, "when": "otherwise",
         "then": "objective determined (an against-only population has the identically-zero objective, earliest maximum = component start); peak and evidence_for stored"},
        {"n": 4, "when": "score",
         "then": "the max live record product at the peak over all live members of any channel (P4: the max-min value); NULL when a live member at the peak is unqualified"},
        {"n": 5, "when": "evidence_against",
         "then": "the per-instant against reduction at the peak; NULL iff the path cannot evaluate it or a live unqualified against/unknown-channel member could feed it"},
    ],
    "valence": "stored outcome_valence_for_native from the window's evidence; `unqualified` whenever the objective is unqualified",
}


def qualification_table_digest(table: dict | None = None) -> str:
    """sha256 over the canonical JSON (sorted keys, no spaces) of the frozen table."""
    return hashlib.sha256(json.dumps(QUALIFICATION_TABLE if table is None else table, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def qualification_table_component(policy: str) -> dict | None:
    """The manifest-vector component binding the table: present ONLY under `window_qualification/1` (an all-NULL vector stays byte-identical to the
    vectors sealed before this component existed)."""
    if policy != POLICY_QUALIFICATION:
        return None
    return {"schema": QUALIFICATION_TABLE_SCHEMA, "digest": qualification_table_digest()}


class ResultPolicyMissing(RuntimeError):
    """The generation's manifest does not select a result policy (or selects an unknown one): nothing may be drafted,
    verified or gated against a policy that was never bound."""


class QualificationTableMismatch(RuntimeError):
    """The manifest's bound qualification table is absent, unexpected or not the table this code implements: the generation was drafted under another
    table (or none), so it can be neither verified, briefed nor sealed here."""


def table_problem(vector: dict | None) -> str | None:
    """Why the stored vector's table binding is wrong (None = right): under `window_qualification/1` the vector must carry exactly this code's table
    component; under `all_null_candidate/1` it must carry none."""
    if not isinstance(vector, dict):
        return "no manifest vector"
    policy, bound = vector.get("result_policy"), vector.get("qualification_table")
    want = qualification_table_component(policy) if policy in RESULT_POLICIES else None
    if bound == want:
        return None
    return (f"the manifest vector binds qualification_table {bound!r} under {policy!r}; this code implements {want!r}")


def manifest_policy(conn, chart_id: str, generation: str) -> str:
    """The policy the generation's MANIFEST selected — read back from the stored input vector, never a constant."""
    row = conn.execute(
        "SELECT input_generation_vector -> 'result_policy' FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    value = None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])
    if isinstance(value, str) and value.startswith('"'):          # a jsonb string read as text
        import json as _json
        value = _json.loads(value)
    if value not in RESULT_POLICIES:
        raise ResultPolicyMissing(
            f"generation {generation}: the manifest vector selects result_policy {value!r}, not one of {RESULT_POLICIES}")
    return value


def manifest_vector(conn, chart_id: str, generation: str) -> dict | None:
    """The generation's stored manifest input vector (parsed), or None."""
    row = conn.execute(
        "SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
        (chart_id, generation)).fetchone()
    value = None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])
    return None if value is None else json.loads(value)


def require_bound_table(conn, chart_id: str, generation: str) -> str:
    """The manifest's policy, after proving its table binding is this code's (raises `QualificationTableMismatch`)."""
    policy = manifest_policy(conn, chart_id, generation)
    why = table_problem(manifest_vector(conn, chart_id, generation))
    if why is not None:
        raise QualificationTableMismatch(f"generation {generation}: {why}")
    return policy
