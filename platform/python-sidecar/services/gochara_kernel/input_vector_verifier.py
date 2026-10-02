"""Independent derivation of the registry component of the '5.0' input vector (R6).

The builder (`input_vector.registry_payload`) fetches typed rows and canonicalises them in Python.
This verifier derives the SAME digest a different way — entirely inside Postgres, with the
database's own canonical JSON and sha256 (migration 1206's `ka_gochara_canonical_json` /
`ka_gochara_sha256_hex`) over `to_jsonb` of the rows — and imports nothing from the builder. Two
derivations that share no code agreeing on the bytes is the check; one that cannot (a value rendered
differently, a field the builder dropped or kept) fails the build.

The verifier is told its own selection rules and the enumerated audit fields; it is not handed the
builder's output.
"""
from __future__ import annotations

_AUDIT = ["created_at", "sealed_at"]
_SCHEMA = "ka_gochara_registry_digest/1"


def sql_registry_digest(conn, path_refs, census=None) -> str:
    """`census` (replay only): the original census to restate instead of reading today's seals."""
    import json as _json
    refs = sorted({(p, v) for p, v in path_refs})
    ids, versions = [p for p, _ in refs], [v for _, v in refs]
    row = conn.execute("""
        WITH sel AS (SELECT * FROM unnest(%(ids)s::text[], %(vers)s::text[]) AS s(p, v)),
        pre AS (SELECT t.* FROM public.ka_gochara_rule_path_prerequisite t
                  JOIN sel ON (t.path_id, t.rule_version) = (sel.p, sel.v)),
        sf AS (SELECT t.* FROM public.ka_gochara_rule_path_soft_factor t
                  JOIN sel ON (t.path_id, t.rule_version) = (sel.p, sel.v))
        SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(jsonb_build_object(
          'schema', %(schema)s::text,
          'paths', (SELECT COALESCE(jsonb_agg(to_jsonb(t) - %(audit)s::text[]
                       ORDER BY t.path_id, t.rule_version), '[]'::jsonb)
                    FROM public.ka_gochara_rule_path t JOIN sel ON (t.path_id, t.rule_version) = (sel.p, sel.v)),
          'prerequisites', (SELECT COALESCE(jsonb_agg(to_jsonb(pre) ORDER BY pre.path_id, pre.rule_version,
                       pre.ordinal), '[]'::jsonb) FROM pre),
          'soft_factors', (SELECT COALESCE(jsonb_agg(to_jsonb(sf) ORDER BY sf.path_id, sf.rule_version,
                       sf.factor_id, sf.factor_rule_version), '[]'::jsonb) FROM sf),
          'predicates', (SELECT COALESCE(jsonb_agg(to_jsonb(t) - %(audit)s::text[]
                       ORDER BY t.predicate_id, t.rule_version), '[]'::jsonb)
                    FROM public.ka_gochara_predicate t
                    WHERE (t.predicate_id, t.rule_version) IN
                          (SELECT predicate_id, predicate_rule_version FROM pre)),
          'factors', (SELECT COALESCE(jsonb_agg(to_jsonb(t) - %(audit)s::text[]
                       ORDER BY t.factor_id, t.rule_version), '[]'::jsonb)
                    FROM public.ka_gochara_factor t
                    WHERE (t.factor_id, t.rule_version) IN
                          (SELECT factor_id, factor_rule_version FROM sf)),
          'census', COALESCE(%(census)s::jsonb, (SELECT COALESCE(jsonb_agg(jsonb_build_array(s.path_id,
                       s.rule_version) ORDER BY s.path_id, s.rule_version), '[]'::jsonb)
                    FROM public.ka_gochara_rule_path_seal s))
        )))
    """, {"ids": ids, "vers": versions, "schema": _SCHEMA, "audit": _AUDIT,
          "census": None if census is None else _json.dumps(census)}).fetchone()
    return row[0] if not isinstance(row, dict) else next(iter(row.values()))


def verify_registry_digest(conn, path_refs, stored_digest: str, census=None) -> None:
    derived = sql_registry_digest(conn, path_refs, census)
    if derived != stored_digest:
        raise RuntimeError(
            f"input vector: the independent (SQL) derivation of the registry digest {derived} "
            f"DISAGREES with the vector's {stored_digest} — a value rendered or selected differently "
            "by the two derivations; the build fails rather than bind an unverified identity")


__all__ = ["sql_registry_digest", "verify_registry_digest"]
