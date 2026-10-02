"""AM-16 reference MODEL v2 (Stream B) — reconciled with Stream A's implementation (pravaha/a53-am5-inventory @3677cccae,
services/gochara_kernel/input_vector.py). Not production code. It states the NORMATIVE key schema and canonical
serialization and holds the frozen cases. Stdlib only.

  python am16_vectors_model.py                      # run the model's own frozen cases
  python am16_vectors_model.py --cross-check FILE   # FILE = Stream A's input_vector.py: its pure functions must agree byte-for-byte

NORMATIVE SCHEMA  (`vector_schema` = "ka_gochara_input_vector/1"; a nested object, so a refusal NAMES the component that moved)
  schema            "ka_gochara_input_vector/1"
  sky_convention    id AND content digest of the convention vector (a label alone is not an identity)           [amended vs A]
  registry          {digest, census}   digest = sha256(canonical_json(payload)); payload = {schema:"ka_gochara_registry_digest/1",
                    paths, prerequisites, soft_factors, predicates, factors, census} — rows are the full jsonb rows of the SELECTED
                    (path, version)s and the predicates/factors they reference, minus the enumerated audit fields
                    {created_at (predicate, factor, path tables), sealed_at (seal table; never selected)}, in a TOTAL order
                    (path_id,rule_version | …,ordinal | …,factor_id,factor_rule_version); census = every sealed (path, version)
  node              {model, source, zodiac, ayanamsha}  (the node series' file identity is carried by `ephemeris`: MEASURED — a MEAN_NODE sidereal calc opens sepl_XX and semo_XX)
  ephemeris         {backend, swe_version, files} where `files` = the .se1 files the kernel ACTUALLY OPENS for the consumed
                    bodies over the consumed horizon (name -> sha256), never "every .se1 present"                      [amended vs A]
                    (measured on swisseph 2.10.03: Sun/Moon/Saturn/MEAN_NODE open sepl_18.se1 + semo_18.se1 and NEVER seas_18.se1;
                    get_current_file_data(0..4) reports the opened files)
  l0                {asset_id: sha256(canonical_json(consumed rows, total order))} for every L0 table a path reads
                    (bg_transit_rules vedha rows for AM-18; bg_transit_av_gates if consumed)                              [added vs A]
  orb_policy        {admission_digest, activity: {factor row version: <orb | state token>, + orb_decision_ref once ratified}}
  rulings_digest    sha256(canonical_json(sorted(rulings by canonical_json)))
  implementation    {geometry, evaluation, window} = sha256(canonical_json({module: sha256(source text)})) over a module list that
                    must COVER the import closure of the writer from services.gochara_kernel + services.gochara_rules   [coverage test added vs A]
There is no aggregate `identity` field: the manifest stores the whole vector and `diff_vectors` reports the component paths that differ.
"""
import copy, hashlib, json, sys

VECTOR_SCHEMA = "ka_gochara_input_vector/1"
REGISTRY_DIGEST_SCHEMA = "ka_gochara_registry_digest/1"
AUDIT_FIELDS = ("created_at", "sealed_at")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_audit(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in AUDIT_FIELDS}


def registry_digest(p: dict) -> str:
    payload = {"schema": REGISTRY_DIGEST_SCHEMA,
               "paths": [strip_audit(r) for r in sorted(p["paths"], key=lambda r: (r["path_id"], r["rule_version"]))],
               "prerequisites": sorted(p["prerequisites"], key=lambda r: (r["path_id"], r["rule_version"], r["ordinal"])),
               "soft_factors": sorted(p["soft_factors"], key=lambda r: (r["path_id"], r["rule_version"], r["factor_id"], r["factor_rule_version"])),
               "predicates": [strip_audit(r) for r in sorted(p["predicates"], key=lambda r: (r["predicate_id"], r["rule_version"]))],
               "factors": [strip_audit(r) for r in sorted(p["factors"], key=lambda r: (r["factor_id"], r["rule_version"]))],
               "census": sorted([list(c) for c in p["census"]])}
    return sha(canonical_json(payload))


def vector(inp: dict) -> dict:
    return {
        "schema": VECTOR_SCHEMA,
        "sky_convention": {"id": inp["sky_id"], "content_digest": sha(canonical_json(inp["sky_vector"]))},
        "registry": {"digest": registry_digest(inp["registry"]), "census": sorted([list(c) for c in inp["registry"]["census"]])},
        "node": inp["node"],
        "ephemeris": {"backend": "swieph", "swe_version": inp["swe_version"], "files": dict(sorted(inp["opened_files"].items()))},
        "l0": {k: sha(canonical_json(v)) for k, v in sorted(inp["l0_rows"].items())},
        "orb_policy": {"admission_digest": sha(canonical_json(inp["admission_orb"])), "activity": inp["activity_orb"]},
        "rulings_digest": sha(canonical_json(sorted(inp["rulings"], key=canonical_json))),
        "implementation": {st: sha(canonical_json(m)) for st, m in sorted(inp["impl_modules"].items())},
    }


def diff_vectors(a, b, path="") -> list:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff_vectors(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}.{k}" if path else k)
        return out
    return [] if a == b else [path]


def _p(pid, v, **kw): return {"path_id": pid, "rule_version": v, "agent_set": "dusthana", "created_at": "t0", **kw}
BASE = {
    "sky_id": "sky:lahiri_sidereal_v1", "sky_vector": {"zodiac": "sidereal", "ayanamsha": "lahiri", "node_model": "mean"},
    "registry": {
        "paths": [_p("P3", "1.1.0")],
        "prerequisites": [{"path_id": "P3", "rule_version": "1.1.0", "ordinal": 1, "predicate_id": "agent_resolved", "predicate_rule_version": "1.0.0"},
                          {"path_id": "P3", "rule_version": "1.1.0", "ordinal": 2, "predicate_id": "in_house_set", "predicate_rule_version": "1.0.0"}],
        "soft_factors": [{"path_id": "P3", "rule_version": "1.1.0", "factor_id": "activity_kernel", "factor_rule_version": "1.1.0"}],
        "predicates": [{"predicate_id": "agent_resolved", "rule_version": "1.0.0", "created_at": "t0"}, {"predicate_id": "in_house_set", "rule_version": "1.0.0", "created_at": "t0"}],
        "factors": [{"factor_id": "activity_kernel", "rule_version": "1.1.0", "function": "piecewise_step_linear", "created_at": "t0",
                     "operand_selector": {"operand": "geometry:object_kind_dispatch", "span_kinds": ["sign_span", "house_span", "star"],
                                          "orb_state": "unratified_nd_orb_open", "uncovered_state": "unqualified"}}],
        "census": [["P3", "1.0.0"], ["P3", "1.1.0"]],
    },
    "node": {"model": "mean", "source": "swiss_mean_node_flg_sidereal", "zodiac": "sidereal", "ayanamsha": "lahiri"},
    "swe_version": "2.10.03",
    "opened_files": {"sepl_18.se1": "a" * 64, "semo_18.se1": "b" * 64},        # the files the kernel opened for this horizon
    "l0_rows": {"bg_transit_rules": [{"graha": "sun", "house": 4, "rule_type": "vedha", "obstructor_house": 10}]},
    "admission_orb": {"orb_table": {"conjunction": 1.0}, "point_orb_source": "convention"},
    "activity_orb": {"1.1.0": "unratified_nd_orb_open"},
    "rulings": [{"id": "ruling:am13"}, {"id": "ruling:am18"}],
    "impl_modules": {"geometry": {"arcs": "c" * 64}, "evaluation": {"score": "d" * 64, "kernel_factor": "e" * 64}, "window": {"window_sweep": "f" * 64}},
}

# case -> (mutation, MUST the vector change?, component path that must be named)
CASES = {
    "membership_only":        ("soft factor moved to another path", True, "registry.digest"),
    "node_series_only":       ("an OPENED ephemeris file's content differs", True, "ephemeris.files.sepl_18.se1"),
    "window_algorithm_only":  ("window-module source digest bumped", True, "implementation.window"),
    "prerequisite_order_only":("same predicates, ordinals swapped", True, "registry.digest"),
    "census_only":            ("a version sealed that was not before", True, "registry.census"),
    "orb_policy_only":        ("activity orb ratified, with its decision ref", True, "orb_policy.activity.1.1.0"),
    "l0_rows_only":           ("one consumed vedha row differs", True, "l0.bg_transit_rules"),
    "kernel_factor_source":   ("kernel_factor.py source changed (the module A's list omits today)", True, "implementation.evaluation"),
    "audit_field_only":       ("created_at differs", False, None),
    "unopened_file_only":     ("an ephemeris file is present in the directory but NOT opened for this horizon", False, None),
}


def mutate(case):
    d = copy.deepcopy(BASE)
    r = d["registry"]
    if case == "membership_only": r["soft_factors"][0]["path_id"] = "P4"
    elif case == "node_series_only": d["opened_files"]["sepl_18.se1"] = "9" * 64
    elif case == "window_algorithm_only": d["impl_modules"]["window"]["window_sweep"] = "0" * 64
    elif case == "prerequisite_order_only": r["prerequisites"][0]["ordinal"], r["prerequisites"][1]["ordinal"] = 2, 1
    elif case == "census_only": r["census"].append(["P4", "1.0.0"])
    elif case == "orb_policy_only": d["activity_orb"]["1.1.0"] = {"orb_deg": 3.0, "orb_decision_ref": "ruling:nd_orb_x"}
    elif case == "l0_rows_only": d["l0_rows"]["bg_transit_rules"][0]["obstructor_house"] = 9
    elif case == "kernel_factor_source": d["impl_modules"]["evaluation"]["kernel_factor"] = "1" * 64
    elif case == "audit_field_only": r["paths"][0]["created_at"] = "t1"
    elif case == "unopened_file_only": pass                 # the unopened file is not an input to the vector at all
    return d


def run():
    base = vector(BASE)
    table = {"base": sha(canonical_json(base))}
    for c, (_, must, comp) in CASES.items():
        v = vector(mutate(c))
        diff = diff_vectors(base, v)
        assert bool(diff) == must, (c, diff)
        if comp: assert any(x == comp or x.startswith(comp + ".") or comp.startswith(x) for x in diff), (c, comp, diff)
        table[c] = sha(canonical_json(v))
    return table


def cross_check(path):
    """Load Stream A's input_vector.py and prove its pure functions agree with the model byte-for-byte."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("a_input_vector", path); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    probes = [{"b": 1, "a": [1.5, "é", None]}, {"z": {"y": 1.0, "x": 2}}]
    for pr in probes:
        assert A.canonical_json(pr) == canonical_json(pr), pr
    assert A.rulings_digest(BASE["rulings"]) == vector(BASE)["rulings_digest"]

    reg = BASE["registry"]
    class Cur:                                          # a DB stand-in answering A's registry queries from the model's rows
        def __init__(s, rows): s.rows = rows
        def fetchall(s): return s.rows
    class Conn:
        def execute(s, sql, params=()):
            if "ka_gochara_rule_path_prerequisite" in sql: return Cur([(r,) for r in reg["prerequisites"]])
            if "ka_gochara_rule_path_soft_factor" in sql: return Cur([(r,) for r in reg["soft_factors"]])
            if "ka_gochara_predicate" in sql: return Cur([(strip_audit(r),) for r in reg["predicates"]])
            if "ka_gochara_factor" in sql: return Cur([(strip_audit(r),) for r in reg["factors"]])
            if "ka_gochara_rule_path_seal" in sql: return Cur([tuple(c) for c in reg["census"]])
            if "ka_gochara_rule_path t" in sql: return Cur([(strip_audit(r),) for r in reg["paths"]])
            raise AssertionError(sql)
    got = A.registry_digest(Conn(), [("P3", "1.1.0")])
    assert got == vector(BASE)["registry"]["digest"], (got, vector(BASE)["registry"]["digest"])
    assert A.diff_vectors({"a": {"b": 1}}, {"a": {"b": 2}}) == diff_vectors({"a": {"b": 1}}, {"a": {"b": 2}})
    print("CROSS-CHECK OK: canonical_json, rulings_digest, registry_digest (via a stand-in connection) and diff_vectors agree byte-for-byte")


if __name__ == "__main__":
    if "--cross-check" in sys.argv:
        cross_check(sys.argv[sys.argv.index("--cross-check") + 1])
    t = run()
    print(json.dumps(t, indent=2))
    print("OK: every result-bearing component changes the vector AND is named; the audit field and an unopened file do not")
