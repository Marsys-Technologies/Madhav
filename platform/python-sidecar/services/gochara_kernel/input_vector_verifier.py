"""Independent derivation of the '5.0' input vector's components (R6 registry; R8-1 the rest).

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


# ── R8-1: the other components, each derived a way that shares no code with the builder ────────────────────

_SKY_AUDIT = ["created_at", "sealed_at"]
#: the verifier's OWN statement of the node identity (it is told it, not handed the builder's output)
_NODE = {"model": "mean", "source": "swiss_mean_node_flg_sidereal", "zodiac": "sidereal", "ayanamsha": "lahiri_chitrapaksha"}


def sql_l0_digest(conn) -> str:
    """The identity of the vedha authority the pair loader consumes, derived entirely in Postgres: every row
    carrying a vedha house (the loader's own selection — the `favourable` rows, node rows included), normalised
    to [graha(lower, trimmed), primary_house, vedha_house, citation, rule_type] in a total order, through the
    database's canonical JSON + sha256. Equals `VedhaPairs.content_digest`; an empty table is refused."""
    row = conn.execute(
        "SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(COALESCE(jsonb_agg("
        "  jsonb_build_array(lower(btrim(graha)), primary_house, vedha_house,"
        "                    COALESCE(classical_citation, ''), COALESCE(rule_type, ''))"
        "  ORDER BY lower(btrim(graha)), primary_house, vedha_house, COALESCE(classical_citation, ''),"
        "           COALESCE(rule_type, '')), '[]'::jsonb))), count(*)"
        " FROM public.bg_transit_rules WHERE vedha_house IS NOT NULL").fetchone()
    digest, n = tuple(row.values()) if isinstance(row, dict) else (row[0], row[1])
    if not n:
        raise RuntimeError("l0: bg_transit_rules has no vedha rows — nothing to derive an identity from")
    return digest


def sql_sky_convention_digest(conn, convention_id: str) -> str:
    row = conn.execute(
        "SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(to_jsonb(t) - %s::text[]))"
        " FROM public.ka_gochara_sky_convention t WHERE t.convention_id = %s", (_SKY_AUDIT, convention_id)).fetchone()
    if row is None:
        raise RuntimeError(f"sky convention {convention_id!r} is not persisted")
    return row[0] if not isinstance(row, dict) else next(iter(row.values()))


def _sha256_file(path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_platform() -> str:
    import platform
    return f"{platform.system()}-{platform.machine()}"


def runtime_library_digest() -> str:
    """sha256 of the swisseph extension file the interpreter would LOAD — located by the import machinery's own
    spec, not by the builder's helper."""
    import importlib.util
    spec = importlib.util.find_spec("swisseph")
    if spec is None or not spec.origin or not spec.has_location:
        raise RuntimeError("swisseph has no loadable file — no runtime identity to derive")
    return _sha256_file(spec.origin)


def module_digests(modules: dict) -> dict:
    """{stage: sha256(canonical JSON {module: sha256(source text)})} — each module located by the import
    machinery (`find_spec`), read and hashed here; the module LISTS are the governing-code closure the AST
    coverage test checks against the writer's real imports."""
    import hashlib
    import importlib.util
    import json as _json
    out = {}
    for stage, names in sorted(modules.items()):
        per = {}
        for name in names:
            spec = importlib.util.find_spec(name)
            if spec is None or not spec.origin:
                raise RuntimeError(f"implementation: {name} cannot be located")
            per[name] = hashlib.sha256(open(spec.origin, encoding="utf-8").read().encode("utf-8")).hexdigest()
        out[stage] = hashlib.sha256(_json.dumps(per, sort_keys=True, separators=(",", ":"),
                                                 ensure_ascii=False).encode("utf-8")).hexdigest()
    return out


# ── R9-3: the consumed ephemeris identity, derived by THIS verifier's own probing ─────────────────────────────

#: the verifier's OWN statement of the bodies the sky substrate consumes (Swiss ids) and of the fixed series probe — its
#: own literals, never the builder's tables (a test asserts they describe the same thing on the real files)
_OWN_BODIES = {"Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4, "Jupiter": 5, "Saturn": 6, "MeanNode": 10}
_PROBE_BODIES = {"Sun": 0, "Moon": 1, "Saturn": 6, "MeanNode": 10}
_PROBE_INSTANTS = [(2024, 6, 1, 0.0), (2025, 1, 1, 0.0), (2025, 7, 1, 12.0), (2026, 1, 1, 0.0)]
_CENSUS_STEP_DAYS = 120.0                                  # finer than a file block (≥ 20 y): every file the range needs
_KNOWN_SCHEMA = "ka_gochara_input_vector/3"
_KNOWN_SCOPES = ("stored_non_moon",)
_KNOWN_POLICIES = ("all_null_candidate/1", "window_qualification/1")


def derive_opened_file_census(ephe_path: str, jd_lo: float, jd_hi: float, *, bodies=None) -> dict:
    """{file name: sha256} of the `.se1` files the Swiss library OPENS for the consumed bodies over [jd_lo, jd_hi],
    established HERE: this verifier's own sampling (every `_CENSUS_STEP_DAYS` days plus both ends, for every body of its
    own list) read back from the library's own record. A call served by the Moshier fallback (a file absent) is refused —
    the census is never taken from the stored vector."""
    from panchang_engine.swiss_state import serialized_swiss_state

    @serialized_swiss_state
    def _probe():
        import swisseph as swe
        from pathlib import Path
        swe.close()
        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        names: dict[str, str] = {}
        points = [jd_lo + k * _CENSUS_STEP_DAYS for k in range(int((jd_hi - jd_lo) // _CENSUS_STEP_DAYS) + 1)] + [jd_hi]
        for body_id in (bodies or _OWN_BODIES).values():
            for jd in points:
                _xx, ret = swe.calc_ut(min(jd, jd_hi), body_id, flags)
                if not (int(ret) & 2):
                    raise RuntimeError(f"ephemeris census: body {body_id} at jd {jd} was not served from the .se1 files")
                for i in range(5):
                    path, _a, _b, _d = swe.get_current_file_data(i)
                    if path and Path(path).is_file():
                        names[Path(path).name] = path
        return names
    return {n: _sha256_file(p) for n, p in sorted(_probe().items())}


def derive_series_probe_digest(ephe_path: str) -> str:
    """The cheap content binding of the consumed series, computed by this verifier's own copy of the probe definition."""
    import hashlib
    import json as _json
    from panchang_engine.swiss_state import serialized_swiss_state

    @serialized_swiss_state
    def _probe():
        import swisseph as swe
        swe.close()
        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        rows = []
        for y, m, d, h in _PROBE_INSTANTS:
            jd = swe.julday(y, m, d, h)
            for name, body in _PROBE_BODIES.items():
                xx, ret = swe.calc_ut(jd, body, flags)
                if not (int(ret) & 2):
                    raise RuntimeError(f"ephemeris probe: {name} at jd {jd} was not served from the .se1 files")
                rows.append([name, jd, True, [float(v).hex() for v in xx]])
        return hashlib.sha256(_json.dumps(rows, separators=(",", ":")).encode()).hexdigest()
    return _probe()


def derive_backend_and_version(ephe_path: str) -> tuple[str, str]:
    """('swieph', swe.version): the backend is derived by a probe that must be served from the `.se1` files."""
    from panchang_engine.swiss_state import serialized_swiss_state

    @serialized_swiss_state
    def _probe():
        import swisseph as swe
        swe.close()
        swe.set_ephe_path(ephe_path)
        _xx, ret = swe.calc_ut(2460000.5, 0, swe.FLG_SWIEPH)
        return ("swieph" if int(ret) & 2 else "moshier"), swe.version
    return _probe()


#: components of the vector this verifier does NOT derive independently — named, so a pass is never read as covering
#: them: the orb tables and the rulings list live in builder code (bound, not re-derived); the SPAN the ephemeris census
#: was taken over is supplied by the caller; and the SEMANTICS of the schema, scope and result-policy tokens (the
#: verifier checks each is a NAMED member of its own vocabulary — it cannot derive what the name means to a consumer)
NOT_INDEPENDENTLY_DERIVED = ("orb_policy", "rulings_digest", "consumed_range", "schema_semantics", "scope_semantics",
                             "result_policy_semantics")


def verify_inputs(conn, stored: dict, *, ephe_path: str, modules: dict, path_refs=None, census=None,
                  jd_range=None, census_probe=None, series_probe=None, backend_probe=None) -> dict:
    """Independently re-derive every component of the stored vector that CAN be derived without the builder's
    code, and refuse any disagreement by name. Returns {"derived": [...components], "not_derived": [...]}.
    `census` (replay) restates the original sealed-version census for the registry component."""
    problems: list[str] = []

    def check(name, derived, bound):
        if derived != bound:
            problems.append(f"{name}: independently derived {derived!r} != bound {bound!r}")

    derived = []
    if path_refs is not None:
        check("registry.digest", sql_registry_digest(conn, path_refs, census), stored["registry"]["digest"])
        derived.append("registry")
    # L0: ONLY the authorities the manifest says it consumes (an unconsumed authority is not an input)
    for asset in sorted(stored.get("l0", {})):
        if asset != "bg_transit_rules":
            problems.append(f"l0.{asset}: no independent derivation exists for this authority")
            continue
        check(f"l0.{asset}", sql_l0_digest(conn), stored["l0"][asset])
    derived.append("l0")
    check("sky_convention.content_digest", sql_sky_convention_digest(conn, stored["sky_convention"]["id"]),
          stored["sky_convention"]["content_digest"])
    derived.append("sky_convention")
    from pathlib import Path
    for name, bound in sorted(stored["ephemeris"]["files"].items()):
        f = Path(ephe_path) / name
        check(f"ephemeris.files.{name}", _sha256_file(f) if f.is_file() else "<absent>", bound)
    derived.append("ephemeris.files")
    # R9-3: the census itself (WHICH files the consumed bodies and range open), the backend, the library version and the
    # series probe are established by this verifier's own probing — not read back from the stored vector
    not_derived = list(NOT_INDEPENDENTLY_DERIVED)
    if jd_range is not None:
        census_now = (census_probe or derive_opened_file_census)(ephe_path, jd_range[0], jd_range[1])
        check("ephemeris.census", dict(sorted(census_now.items())), dict(sorted(stored["ephemeris"]["files"].items())))
        derived.append("ephemeris.census")
    else:
        not_derived.append("ephemeris.census")        # no span supplied: the census cannot be established — named, not silent
    backend, version = (backend_probe or derive_backend_and_version)(ephe_path)
    check("ephemeris.backend", backend, stored["ephemeris"].get("backend"))
    check("ephemeris.swe_version", version, stored["ephemeris"].get("swe_version"))
    derived += ["ephemeris.backend", "ephemeris.version"]
    check("ephemeris.probe_digest", (series_probe or derive_series_probe_digest)(ephe_path),
          stored["ephemeris"].get("probe_digest"))
    derived.append("ephemeris.probe")
    # the schema, scope and policy are NAMED members of this verifier's own vocabularies (their semantics are not derived)
    for key, known, got in (("schema", (_KNOWN_SCHEMA,), stored.get("schema")),
                            ("stored_scope", _KNOWN_SCOPES, stored.get("stored_scope")),
                            ("result_policy", _KNOWN_POLICIES, stored.get("result_policy"))):
        if got not in known:
            problems.append(f"{key}: {got!r} is not a named member of {known}")
        derived.append(key)
    for key in ("library_sha256", "platform"):
        if key not in stored["ephemeris"]:
            problems.append(f"ephemeris.{key}: the vector binds no library identity (schema /2 requires it)")
    if "library_sha256" in stored["ephemeris"]:
        check("ephemeris.library_sha256", runtime_library_digest(), stored["ephemeris"]["library_sha256"])
    if "platform" in stored["ephemeris"]:
        check("ephemeris.platform", runtime_platform(), stored["ephemeris"]["platform"])
    derived.append("ephemeris.library")
    check("node", _NODE, stored["node"])
    derived.append("node")
    check("implementation", module_digests(modules), stored["implementation"])
    derived.append("implementation")
    if problems:
        raise RuntimeError("input vector: the independent derivation DISAGREES — " + "; ".join(problems))
    return {"derived": derived, "not_derived": not_derived}


__all__ = ["NOT_INDEPENDENTLY_DERIVED", "derive_backend_and_version", "derive_opened_file_census",
           "derive_series_probe_digest", "module_digests", "runtime_library_digest", "runtime_platform", "sql_l0_digest",
           "sql_registry_digest", "sql_sky_convention_digest", "verify_inputs", "verify_registry_digest"]
