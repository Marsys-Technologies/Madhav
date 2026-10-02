"""AM-16 reference MODEL (Stream B). Not production code: it defines the canonical serialization and the frozen test
vectors that Stream A's implementation must reproduce byte-for-byte. Stdlib only. Run: python am16_vectors_model.py [--check]"""
import hashlib, json, sys

VECTOR_SCHEMA = 1
AUDIT_FIELDS = {"created_at"}                       # the ONLY enumerated exclusion


def canon(obj) -> bytes:
    """canonical JSON: sorted keys (codepoint), no spaces, UTF-8, no NaN/Inf."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strip_audit(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in AUDIT_FIELDS}


def registry_digest(reg: dict) -> str:
    lines = []
    for kind in ("paths", "predicates", "factors"):
        for row in reg[kind]:
            lines.append(kind + "|" + canon(strip_audit(row)).decode())
    for m in reg["prerequisites"]:                   # ORDERED: ordinal is part of the payload, order is kept
        lines.append("prereq|" + canon(m).decode())
    for m in reg["soft_factors"]:
        lines.append("soft|" + canon(m).decode())
    for a in reg["applicability"]:                   # flat operand_selector declarations
        lines.append("appl|" + canon(a).decode())
    lines.sort()
    return sha("\n".join(lines).encode())


def version_census(reg: dict) -> str:
    return sha(canon(sorted(reg["sealed_versions"], key=lambda x: (x["path"], x["version"]))))


def vector(inp: dict) -> dict:
    v = {
        "vector_schema": VECTOR_SCHEMA,
        "registry_digest": registry_digest(inp["registry"]),
        "registry_version_census": version_census(inp["registry"]),
        "l0_identities": sha(canon(sorted(inp["l0"], key=lambda x: x["asset_id"]))),
        "arc_series_digest": sha(canon(inp["arc_series"])),
        "node_series_digest": sha(canon(inp["node_series"])),
        "admission_orb_policy": inp["admission_orb_policy"],
        "scale_orb_policy": inp["scale_orb_policy"],
        "rulings": sorted(inp["rulings"]),
        "impl_geometry": inp["impl"]["geometry"],
        "impl_evaluation": inp["impl"]["evaluation"],
        "impl_window": inp["impl"]["window"],
    }
    v["identity"] = sha(canon(v))
    return v


BASE = {
    "registry": {
        "paths": [{"path": "P3", "version": "1.1.0", "agent_set": "dusthana", "created_at": "t0"}],
        "predicates": [{"predicate": "in_house_set", "version": "1.0.0"}, {"predicate": "agent_resolved", "version": "1.0.0"}],
        "factors": [{"factor": "activity_kernel", "version": "1.1.0", "function": "piecewise_step_linear"},
                    {"factor": "vedha_attenuation", "version": "1.1.0", "function": "cited_step"}],
        "prerequisites": [{"path": "P3", "version": "1.1.0", "ordinal": 1, "predicate": "agent_resolved", "pversion": "1.0.0"},
                          {"path": "P3", "version": "1.1.0", "ordinal": 2, "predicate": "in_house_set", "pversion": "1.0.0"}],
        "soft_factors": [{"path": "P3", "version": "1.1.0", "factor": "activity_kernel", "fversion": "1.1.0"}],
        "applicability": [{"factor": "activity_kernel", "version": "1.1.0", "applicability_span": "sign_span,house_span,star"}],
        "sealed_versions": [{"path": "P3", "version": "1.0.0", "state": "superseded"}, {"path": "P3", "version": "1.1.0", "state": "included"}],
    },
    "l0": [{"asset_id": "bg_transit_rules", "digest": "a" * 64}, {"asset_id": "bg_transit_av_gates", "digest": "b" * 64}],
    "arc_series": [["2024-01-01T00:00:00Z", 280.5], ["2024-01-02T00:00:00Z", 280.9]],
    "node_series": [["2024-01-01T00:00:00Z", 12.3], ["2024-01-02T00:00:00Z", 12.2]],
    "admission_orb_policy": "ruling:nd_orb_admission_unratified",
    "scale_orb_policy": "ruling:nd_orb_scale_unratified",
    "rulings": ["ruling:am13", "ruling:am18"],
    "impl": {"geometry": "c0ffee1", "evaluation": "c0ffee2", "window": "c0ffee3"},
}


def mutate(case: str) -> dict:
    import copy
    d = copy.deepcopy(BASE)
    if case == "membership_only":                    # a soft factor moved to another path
        d["registry"]["soft_factors"][0]["path"] = "P4"
    elif case == "node_series_only":                 # one node-series row differs
        d["node_series"][1][1] = 12.25
    elif case == "window_algorithm_only":            # implementation identity bumped
        d["impl"]["window"] = "c0ffee4"
    elif case == "prerequisite_order_only":          # ordinals swapped, same members
        p = d["registry"]["prerequisites"]; p[0]["ordinal"], p[1]["ordinal"] = 2, 1
    elif case == "audit_field_only":                 # created_at differs: must NOT change anything
        d["registry"]["paths"][0]["created_at"] = "t1"
    elif case == "census_only":                      # a version sealed differently
        d["registry"]["sealed_versions"][0]["state"] = "included"
    elif case == "orb_policy_only":
        d["scale_orb_policy"] = "ruling:nd_orb_scale_ratified_x"
    return d


CASES = ["base", "membership_only", "node_series_only", "window_algorithm_only", "prerequisite_order_only", "audit_field_only", "census_only", "orb_policy_only"]


def table():
    out = {}
    for c in CASES:
        out[c] = vector(BASE if c == "base" else mutate(c))["identity"]
    return out


if __name__ == "__main__":
    t = table()
    base = t["base"]
    for c in CASES[1:]:
        changed = t[c] != base
        want = c != "audit_field_only"
        assert changed == want, (c, changed)
    print(json.dumps(t, indent=2))
    print("OK: every result-bearing component changes the identity; the enumerated audit field does not")
