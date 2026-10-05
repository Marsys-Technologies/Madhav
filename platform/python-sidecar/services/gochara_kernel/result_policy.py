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

POLICY_ALL_NULL = "all_null_candidate/1"
POLICY_QUALIFICATION = "window_qualification/1"
RESULT_POLICIES = (POLICY_ALL_NULL, POLICY_QUALIFICATION)
DEFAULT_RESULT_POLICY = POLICY_ALL_NULL
#: the named reason every window carries under `all_null_candidate/1`
ALL_NULL_REASON = "all_null_candidate_policy"
#: the numerical RESULT fields the all-NULL policy nulls (the peak instant and the valence are nulled/pinned beside them)
NUMERIC_RESULT_FIELDS = ("score", "evidence_for", "evidence_against", "objective_value", "severity")


class ResultPolicyMissing(RuntimeError):
    """The generation's manifest does not select a result policy (or selects an unknown one): nothing may be drafted,
    verified or gated against a policy that was never bound."""


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
