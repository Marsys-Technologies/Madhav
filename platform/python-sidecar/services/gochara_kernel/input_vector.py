"""The '5.0' input vector (AM-16; Codex round 6, R6) — what identifies the inputs a build CONSUMED.

The manifest's `input_generation_vector` enters the search-input snapshot's `input_digest`
(1206 `ka_gochara_search_input_digest`), so a result-bearing change that does not change the vector
would leave two different builds with ONE identity. The vector therefore carries a versioned key
schema and a canonical serialization, and binds:

  registry          a digest over the SELECTED path, predicate and factor payloads (every column but
                    the enumerated audit fields `created_at`/`sealed_at`), the ORDERED prerequisite
                    memberships, the soft-factor memberships, the applicability declarations (they ride
                    the factor rows' flat `operand_selector`), plus the accounted sealed-version CENSUS
                    — every sealed (path, version) in the registry, bound or not;
  sky_convention    the sky/kala convention id (zodiac, ayanāṃśa, node model, epoch, ...);
  node / ephemeris  the node convention AND the identity of the node-series source actually consumed:
                    the Swiss library version and the sha256 of every `.se1` file in the ephemeris
                    path (a "mean" label does not distinguish two mean-node series);
  orb_policy        BOTH policies: the contact/ADMISSION orb table (it fixes supports) and the
                    ACTIVITY orb (a registry fact — it is inside the registry digest, restated here as
                    the explicit state of each activity_kernel row);
  rulings           the standing rulings and every path's `ruling_ref` the build applies;
  implementation    the source digests of the modules that govern geometry, evaluation and window
                    construction.

Inputs already transitively bound by the snapshot (L1 facts, daśā rows, AV declarations) are NOT
duplicated here. HISTORICAL REPLAY does not call `verify_live`: it checks the ORIGINAL bound vector
stored on its manifest, never a fingerprint of today's catalogue.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Iterable

from panchang_engine.swiss_state import serialized_swiss_state

VECTOR_SCHEMA = "ka_gochara_input_vector/3"
#: R9-1 (steward M20261002T062742-e773): the numeric-result policy the generation is built, verified and gated UNDER is a
#: REQUIRED key of the manifest vector — selected by the manifest, never by a writer constant. `all_null_candidate/1` =
#: every numerical result field NULL for every path/channel (this milestone); `window_qualification/1` = the policy that
#: applies when numbers are enabled.
from .result_policy import (DEFAULT_RESULT_POLICY, POLICY_ALL_NULL, POLICY_QUALIFICATION,  # noqa: E402
                            RESULT_POLICIES)
REGISTRY_DIGEST_SCHEMA = "ka_gochara_registry_digest/1"
STORED_SCOPE = "stored_non_moon"
EXCLUDED_AUDIT_FIELDS = ("created_at", "sealed_at")

_K, _R = "services.gochara_kernel.", "services.gochara_rules."
# Closed module lists: the code that GOVERNS each result-bearing stage. They must COVER the writer's static
# import closure over services.gochara_kernel + services.gochara_rules (tests/l3/gochara/_import_closure —
# a coverage test fails when a module the writer imports is in no list, because editing it would not move
# the vector). Verifiers sit with the stage they verify; nothing here is "optional".
IMPLEMENTATION_MODULES = {
    "geometry": tuple(_K + m for m in (
        "arcs", "boundary_match", "contact_certify", "contact_reconstruct", "contacts", "convention", "episodes", "ids", "knots", "materialise", "record_store",
        "substrate", "targets")),
    "evaluation": tuple(_K + m for m in (
        "chart_context", "coverage", "dasha_read", "evaluator", "input_vector", "input_vector_verifier",
        "inventory", "inventory_store", "inventory_verifier", "ledger", "lifecycle", "native_conn",
        "record_derivation", "record_verifier", "scope_response",
        "rule_registry")) + ("pipeline.orchestrator.writers.ka_gochara_v5",) + tuple(_R + m for m in (
        "admission", "ashtakavarga", "dignity", "drishti", "favourable_houses", "flat_selector", "frames",
        "kernel_factor", "nature", "p6", "permission", "predicates", "records", "registry", "score", "strength",
        "valence", "vedha", "vedha_derive")),
    # R10-4: the VERIFICATION JOB (the library and the operator entry point) is part of the governed implementation identity —
    # the pinned job is part of the trusted system (AM-24 item 4), so a different job is a different manifest vector
    "window": tuple(_K + m for m in ("result_policy", "candidate_boundary", "seal_brief", "seal_flow", "verification_job", "window_gate", "window_store", "window_sweep",
                                     "window_verifier")) + ("pipeline.orchestrator.verification_job", "pipeline.orchestrator.seal_job"),
}

# The L0 authorities a path READS, and which loader reads them (R8-1). `bg_transit_rules` is consumed ONLY
# through Stream B's `vedha_derive.load_pairs` (rows carrying a vedha house — the `favourable` rows, 36 cited
# classical + 6 L0-flagged UNSOURCED node rows; validated and census-checked there), so its identity is that
# loader's `content_digest` — never a selection of this module's own. It is a build dependency ONLY when the
# build actually consumes it (the vedha operand bound — `VEDHA_SOURCE`); an unconsumed authority is not an
# input (`bg_transit_av_gates` would be consumed by P5 only — held by ruling ST-P5-HOLD — so it is not bound).
L0_CONSUMED = {"bg_transit_rules": ("P2", "services.gochara_rules.vedha_derive.load_pairs")}


class InputDrift(RuntimeError):
    """A consumed input no longer matches the vector the build was bound to."""


def canonical_json(obj) -> str:
    """Sorted keys, no whitespace, UTF-8 as-is, no NaN — the same byte rule as the DB's
    `ka_gochara_canonical_json` for the ASCII keys and plain scalars these payloads carry."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── registry ────────────────────────────────────────────────────────────────

def registry_payload(conn, path_refs: Iterable[tuple[str, str]], *,
                     census_override: list | None = None) -> dict:
    """The selected rows, audit fields removed, in a total order. `census_override` is for HISTORICAL
    REPLAY only: the sealed-version census stored on the original vector (every item must still be
    sealed — seals are immutable — but versions sealed LATER do not change a past build's identity)."""
    refs = sorted({(p, v) for p, v in path_refs})
    ids, versions = [p for p, _ in refs], [v for _, v in refs]
    audit = list(EXCLUDED_AUDIT_FIELDS)

    def rows(sql: str, params: tuple) -> list:
        return [r[0] if not isinstance(r, dict) else next(iter(r.values()))
                for r in conn.execute(sql, params).fetchall()]

    sel = "(path_id, rule_version) IN (SELECT * FROM unnest(%s::text[], %s::text[]))"
    paths = rows("SELECT to_jsonb(t) - %s::text[] FROM public.ka_gochara_rule_path t WHERE " + sel
                 + " ORDER BY t.path_id, t.rule_version", (audit, ids, versions))
    prereqs = rows("SELECT to_jsonb(t) FROM public.ka_gochara_rule_path_prerequisite t WHERE " + sel
                   + " ORDER BY t.path_id, t.rule_version, t.ordinal", (ids, versions))
    softs = rows("SELECT to_jsonb(t) FROM public.ka_gochara_rule_path_soft_factor t WHERE " + sel
                 + " ORDER BY t.path_id, t.rule_version, t.factor_id, t.factor_rule_version",
                 (ids, versions))
    pred_refs = sorted({(r["predicate_id"], r["predicate_rule_version"]) for r in prereqs})
    fac_refs = sorted({(r["factor_id"], r["factor_rule_version"]) for r in softs})
    predicates = rows(
        "SELECT to_jsonb(t) - %s::text[] FROM public.ka_gochara_predicate t WHERE (predicate_id,"
        " rule_version) IN (SELECT * FROM unnest(%s::text[], %s::text[]))"
        " ORDER BY t.predicate_id, t.rule_version",
        (audit, [p for p, _ in pred_refs], [v for _, v in pred_refs]))
    factors = rows(
        "SELECT to_jsonb(t) - %s::text[] FROM public.ka_gochara_factor t WHERE (factor_id,"
        " rule_version) IN (SELECT * FROM unnest(%s::text[], %s::text[]))"
        " ORDER BY t.factor_id, t.rule_version",
        (audit, [f for f, _ in fac_refs], [v for _, v in fac_refs]))
    census = [[r[0], r[1]] if not isinstance(r, dict) else [r["path_id"], r["rule_version"]]
              for r in conn.execute("SELECT path_id, rule_version FROM public.ka_gochara_rule_path_seal"
                                    " ORDER BY path_id, rule_version").fetchall()]
    if census_override is not None:
        gone = [c for c in census_override if c not in census]
        if gone:
            raise InputDrift(f"replay: sealed version(s) {gone} recorded on the vector are no longer sealed")
        census = [list(c) for c in census_override]
    missing = [r for r in refs if not any(p["path_id"] == r[0] and p["rule_version"] == r[1] for p in paths)]
    if missing:
        raise InputDrift(f"registry: bound path reference(s) {missing} are not persisted")
    unsealed = [r for r in refs if list(r) not in census]
    if unsealed:
        raise InputDrift(f"registry: bound path reference(s) {unsealed} are not sealed (F3)")
    return {"schema": REGISTRY_DIGEST_SCHEMA, "paths": paths, "prerequisites": prereqs,
            "soft_factors": softs, "predicates": predicates, "factors": factors, "census": census}


def _strip_audit(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in EXCLUDED_AUDIT_FIELDS}


def registry_digest_of(rows: dict) -> str:
    """The registry digest of already-fetched rows, PURE: total order, audit fields stripped — the one
    function the runtime and the frozen vectors share (so a serializer drift fails both)."""
    return _sha(canonical_json(registry_preimage(rows)))


def registry_preimage(rows: dict) -> dict:
    return {"schema": REGISTRY_DIGEST_SCHEMA,
            "paths": [_strip_audit(r) for r in sorted(rows["paths"], key=lambda r: (r["path_id"], r["rule_version"]))],
            "prerequisites": sorted(rows["prerequisites"], key=lambda r: (r["path_id"], r["rule_version"], r["ordinal"])),
            "soft_factors": sorted(rows["soft_factors"], key=lambda r: (
                r["path_id"], r["rule_version"], r["factor_id"], r["factor_rule_version"])),
            "predicates": [_strip_audit(r) for r in sorted(rows["predicates"], key=lambda r: (
                r["predicate_id"], r["rule_version"]))],
            "factors": [_strip_audit(r) for r in sorted(rows["factors"], key=lambda r: (
                r["factor_id"], r["rule_version"]))],
            "census": sorted([list(c) for c in rows["census"]])}


def registry_digest(conn, path_refs: Iterable[tuple[str, str]], *, census_override=None) -> str:
    return registry_digest_of(registry_payload(conn, path_refs, census_override=census_override))


#: the stored ephemeris component's closed key set (AM-16 schema /2)
EPHEMERIS_KEYS = frozenset({"backend", "swe_version", "library_sha256", "platform", "files", "probe_digest"})


def _ephemeris_component(inp: dict) -> dict:
    """AM-16 schema /2 (Stream B's frozen vectors v2): beside the version string and the opened-file digests the
    component binds the LOADED swisseph artifact (`library_sha256`) and the platform — float behaviour is a function
    of the library build and the CPU/libm. Both are REQUIRED: a build that cannot name them is refused upstream."""
    if "ephemeris" in inp:               # already the stored form (`ephemeris_component`) — validated, not rebuilt
        comp = dict(inp["ephemeris"])
        if set(comp) != EPHEMERIS_KEYS:
            raise InputDrift(f"ephemeris component keys {sorted(comp)} != {sorted(EPHEMERIS_KEYS)}")
        return {**comp, "files": dict(sorted(comp["files"].items()))}
    return {"backend": "swieph", "swe_version": inp["swe_version"], "library_sha256": inp["library_sha256"],
            "platform": inp["platform"], "files": dict(sorted(inp["opened_files"].items())),
            "probe_digest": inp["probe_digest"]}


def _require_policy(policy):
    if policy not in RESULT_POLICIES:
        raise InputDrift(f"result_policy {policy!r} is not one of {RESULT_POLICIES}")
    return policy


def assemble_vector(inp: dict) -> dict:
    """The vector from already-obtained inputs, PURE — the single serializer `build_input_vector` and the
    frozen test vectors (`am16_vectors_frozen_v1.json`, literal preimages + expected sha256) both use."""
    return {
        "schema": VECTOR_SCHEMA,
        # AM-14: the machine-readable scope of what this generation STORES — the Moon is the on-demand
        # tier. 1232's completeness function refuses a manifest vector without it, and serving must
        # be able to state it with every answer.
        "stored_scope": inp["stored_scope"],
        # R9-1: the numeric-result policy in force — REQUIRED (no optional form), a named member of RESULT_POLICIES
        "result_policy": _require_policy(inp["result_policy"]),
        "sky_convention": {"id": inp["sky_id"], "content_digest": _sha(canonical_json(inp["sky_vector"]))},
        "registry": {"digest": registry_digest_of(inp["registry"]),
                     "census": sorted([list(c) for c in inp["registry"]["census"]])},
        "node": inp["node"],
        "ephemeris": _ephemeris_component(inp),
        # `l0_rows` (raw rows hashed here — the frozen vectors) and `l0_digests` (an identity already computed by
        # the authority's own loader — production) together; both name the build's CONSUMED authorities only
        "l0": {k: v for k, v in sorted({**{k: _sha(canonical_json(v)) for k, v in inp.get("l0_rows", {}).items()},
                                        **inp.get("l0_digests", {})}.items())},
        "orb_policy": {"admission_digest": _sha(canonical_json(inp["admission_orb"])),
                       "activity": inp["activity_orb"]},
        "rulings_digest": _sha(canonical_json(sorted(inp["rulings"], key=canonical_json))),
        "implementation": {st: _sha(canonical_json(m)) for st, m in sorted(inp["impl_modules"].items())},
    }


# ── node series / ephemeris ──────────────────────────────────────────────────

_FILE_CACHE: dict[tuple, str] = {}


def _file_sha(path: Path) -> str:
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime_ns)
    if key not in _FILE_CACHE:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _FILE_CACHE[key] = h.hexdigest()
    return _FILE_CACHE[key]


@serialized_swiss_state
def probe_opened_files(ephe_path: str, bodies: Iterable[str], jd_lo: float, jd_hi: float) -> dict[str, str]:
    """The `.se1` files the kernel ACTUALLY OPENS for `bodies` over `[jd_lo, jd_hi]` (name → path), read
    from the Swiss library's own record (`swe.get_current_file_data`) — measured on swisseph 2.10.03:
    Sun/Moon/Saturn/MEAN_NODE open sepl_XX + semo_XX and never seas_XX. Probed at both ends and, when
    an opened file's coverage ends inside the range, just past each file-block boundary until the range
    is covered. A probe served by the Moshier fallback (the file absent) is refused."""
    import swisseph as swe
    from .knots import EPHE_FLAGS, GRAHA_TO_SWE
    opened: dict[str, str] = {}
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for body in bodies:
        points = [jd_lo, jd_hi]
        probed: set[float] = set()
        while points:
            jd = points.pop()
            if jd in probed:
                continue
            probed.add(jd)
            swe.close()
            swe.set_ephe_path(ephe_path)
            _xx, retflag = swe.calc_ut(jd, GRAHA_TO_SWE[body], EPHE_FLAGS)
            if not (int(retflag) & 2):
                raise InputDrift(f"ephemeris: {body} at jd {jd} was not served from the .se1 files "
                                 f"(retflag {int(retflag)}) — an opened file is absent")
            for i in range(5):
                path, start, end, _den = swe.get_current_file_data(i)
                if not path:
                    continue
                if not Path(path).is_file():
                    raise InputDrift(f"ephemeris: opened file {path!r} is absent")
                opened[Path(path).name] = path
                if end < jd_hi and end + 1.0 <= jd_hi:
                    points.append(end + 1.0)
    return opened


# The fixed series probe (design/am16_series_equivalence_probe.py): the cheap CONTENT binding of the consumed
# arc/node series — the kernel computes it with pyswisseph, so it is a pure function of (opened file
# contents, library version, flags, instants); `probe_digest` catches library-numerics drift the file hashes
# alone would miss.
PROBE_BODIES = {"Sun": 0, "Moon": 1, "Saturn": 6, "MeanNode": 10}
PROBE_INSTANTS = [(2024, 6, 1, 0.0), (2025, 1, 1, 0.0), (2025, 7, 1, 12.0), (2026, 1, 1, 0.0)]


@serialized_swiss_state
def probe_series_digest(ephe_path: str) -> str:
    import swisseph as swe
    swe.close()
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    rows = []
    for y, m, d, h in PROBE_INSTANTS:
        jd = swe.julday(y, m, d, h)
        for name, body in PROBE_BODIES.items():
            xx, ret = swe.calc_ut(jd, body, flags)
            if not (int(ret) & 2):
                raise InputDrift(f"ephemeris probe: {name} at jd {jd} was not served from the .se1 files")
            rows.append([name, jd, True, [float(v).hex() for v in xx]])
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def ephemeris_identity(ephe_path: str | None, *, bodies: Iterable[str], jd_lo: float, jd_hi: float,
                       files_probe=None, series_probe=None) -> dict:
    """The Swiss library version and the sha256 of the files the kernel OPENS for the consumed bodies and
    range — never "every .se1 present" (a file merely lying in the directory is not an input). No path ⇒
    refused, never recorded as unknown (a vector that cannot distinguish two ephemerides is not an
    identity)."""
    import swisseph as swe
    if not ephe_path:
        raise InputDrift("ephemeris: no ephe_path configured — the node-series identity cannot be bound")
    opened = (files_probe or probe_opened_files)(ephe_path, tuple(bodies), jd_lo, jd_hi)
    if not opened:
        raise InputDrift(f"ephemeris: no .se1 file was opened under {ephe_path!r} — nothing to bind")
    return {"backend": "swieph", "swe_version": swe.version,
            "files": {name: _file_sha(Path(path)) for name, path in sorted(opened.items())},
            "probe_digest": (series_probe or probe_series_digest)(ephe_path),
            "library_sha256": library_artifact_sha(), "platform": platform_identity()}


def ephemeris_component(ephe_path: str | None, bodies: Iterable[str], jd_lo: float, jd_hi: float, *,
                        files_probe=None, series_probe=None) -> dict:
    """The STORED form of the vector's ephemeris component — `{backend, swe_version, library_sha256, platform,
    files{name: sha256 of the files actually opened}, probe_digest}` — as ONE public function (steward
    M20261002T043431-8a08; Stream B's S1-REQ-EPHEMERIS: a '4.1' manifest must record the same component and refuse on a
    Moshier fallback). It REFUSES (InputDrift) without an ephemeris path, when no file was opened, or when a probe was
    not served from the `.se1` files (a Moshier fallback). `build_input_vector` gets its fields from `ephemeris_identity`
    and shapes them with the SAME private shaper, so the two cannot diverge."""
    eph = ephemeris_identity(ephe_path, bodies=tuple(bodies), jd_lo=jd_lo, jd_hi=jd_hi,
                             files_probe=files_probe, series_probe=series_probe)
    return _ephemeris_component({"swe_version": eph["swe_version"], "opened_files": eph["files"],
                                 "probe_digest": eph["probe_digest"], "library_sha256": eph["library_sha256"],
                                 "platform": eph["platform"]})


def library_artifact_sha() -> str:
    """sha256 of the swisseph artifact the import machinery resolves (`importlib.util.find_spec('swisseph').origin` —
    the compiled extension), bound beside the version string: two builds can share a version."""
    import importlib.util
    spec = importlib.util.find_spec("swisseph")
    if spec is None or not spec.origin or not Path(spec.origin).is_file():
        raise InputDrift("ephemeris: the swisseph library has no file to bind (no library identity)")
    return _file_sha(Path(spec.origin))


def platform_identity() -> str:
    """'<system>-<machine>' (e.g. 'Linux-x86_64'): float behaviour is a function of the architecture and libm."""
    import platform
    return f"{platform.system()}-{platform.machine()}"


def node_identity() -> dict:
    from .record_store import KALA_CONVENTION_VECTOR as k
    return {"model": k["node_model"], "source": k["node_source"], "zodiac": k["zodiac"],
            "ayanamsha": k["ayanamsha"]}


# ── policies, rulings, implementation ───────────────────────────────────────

def admission_orb_digest() -> str:
    """The contact/ADMISSION orb: ORB_TABLE and the relation→orb mapping the point solves use."""
    from .convention import ORB_TABLE
    from .record_store import POINT_ORB_SOURCE
    return _sha(canonical_json({"orb_table": ORB_TABLE, "point_orb_source": POINT_ORB_SOURCE}))


def activity_orb_states(conn, path_refs, census_override=None) -> dict:
    """The ACTIVITY orb as the persisted `activity_kernel` rows state it: per row version, the orb
    (omitted when unratified) — restated explicitly so a ratification is visible in the vector
    itself, not only inside the registry digest."""
    out = {}
    for f in registry_payload(conn, path_refs, census_override=census_override)["factors"]:
        if f["factor_id"] == "activity_kernel":
            sel = f["operand_selector"]
            if sel.get("orb_state") == "ratified":
                out[f["rule_version"]] = {"orb_deg": sel["orb_deg"],
                                          "orb_decision_ref": sel.get("orb_decision_ref", "<none>")}
            else:
                out[f["rule_version"]] = sel.get("orb_state", "undeclared")
    return out


def l0_identities(conn, consumed: Iterable[str]) -> dict:
    """{asset_id: content digest of the rows the build CONSUMES} for exactly the L0 authorities named in
    `consumed` (the build's actual consumption — never "every table a path could read"). `bg_transit_rules` is
    read through B's validated loader: an absent table, an empty/incomplete/changed authority, an uncited or
    fabricated row is refused by name; the digest is the loader's own `content_digest` (all 42 consumed rows)."""
    from services.gochara_rules import vedha_derive
    out = {}
    for asset in sorted(set(consumed)):
        if asset not in L0_CONSUMED:
            raise InputDrift(f"l0: {asset!r} is not a known consumed authority (known: {sorted(L0_CONSUMED)})")
        try:
            with conn.transaction():                  # a savepoint: a missing table must not poison the caller
                pairs = vedha_derive.load_pairs(conn.cursor())
        except vedha_derive.VedhaPairsError as exc:
            raise InputDrift(f"l0: {asset} is not the validated authority the pair loader consumes: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - a missing L0 table must name itself, not leak a driver error
            raise InputDrift(f"l0: {asset} is not readable ({type(exc).__name__}) — nothing to bind") from exc
        out[asset] = pairs.content_digest
    return out


def sky_convention_identity(conn, convention_id: str) -> dict:  # noqa: D401
    """The convention's id AND the digest of its stored content (a label alone is not an identity)."""
    row = conn.execute(
        "SELECT to_jsonb(t) - %s::text[] FROM public.ka_gochara_sky_convention t WHERE t.convention_id = %s",
        (list(EXCLUDED_AUDIT_FIELDS), convention_id)).fetchone()
    if row is None:
        raise InputDrift(f"sky convention {convention_id!r} is not persisted — nothing to bind")
    content = row[0] if not isinstance(row, dict) else next(iter(row.values()))
    return {"id": convention_id, "content_digest": _sha(canonical_json(content))}


def rulings_digest(rulings: Iterable[dict]) -> str:
    return _sha(canonical_json(sorted(rulings, key=canonical_json)))


def _module_source_digest(name: str) -> str:
    mod = importlib.import_module(name)
    return _sha(Path(mod.__file__).read_text(encoding="utf-8"))


def implementation_digests(modules: dict | None = None) -> dict:
    mods = modules or IMPLEMENTATION_MODULES
    return {stage: _sha(canonical_json({m: _module_source_digest(m) for m in names}))
            for stage, names in mods.items()}


# ── the vector ───────────────────────────────────────────────────────────────

def consumed_jd_range(horizon=None) -> tuple[float, float]:
    """The CONSUMED julian-day range the ephemeris identity is taken over: the substrate domain every arc is built over,
    widened by the class horizon. One definition — the independent census verifier is GIVEN these numbers."""
    from .substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    lo = min(x for x in (SUBSTRATE_DOMAIN_START, horizon[0] if horizon else None) if x is not None)
    hi = max(x for x in (SUBSTRATE_DOMAIN_END, horizon[1] if horizon else None) if x is not None)
    jd = lambda d: d.timestamp() / 86400.0 + 2440587.5            # noqa: E731
    return jd(lo), jd(hi)


def build_input_vector(conn, *, sky_convention_id: str, ephe_path: str | None,
                       path_refs: Iterable[tuple[str, str]], rulings: Iterable[dict],
                       horizon: tuple | None = None, bodies: Iterable[str] | None = None,
                       files_probe=None, series_probe=None, modules: dict | None = None,
                       l0_consumed: Iterable[str] = (), census_override=None,
                       result_policy: str = DEFAULT_RESULT_POLICY) -> dict:
    """The vector of what this build CONSUMES. `l0_consumed` names the L0 authorities actually read (none ⇒
    none is a dependency); `census_override` (historical replay) restates the ORIGINAL sealed-version census."""
    from .substrate import SUBSTRATE_BODIES, SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    from .convention import ORB_TABLE
    from .record_store import POINT_ORB_SOURCE
    refs = list(path_refs)
    payload = registry_payload(conn, refs, census_override=census_override)
    jd_lo, jd_hi = consumed_jd_range(horizon)
    eph = ephemeris_component(ephe_path, tuple(bodies or SUBSTRATE_BODIES), jd_lo, jd_hi,
                              files_probe=files_probe, series_probe=series_probe)
    sky = sky_convention_identity(conn, sky_convention_id)
    sky_row = conn.execute(
        "SELECT to_jsonb(t) - %s::text[] FROM public.ka_gochara_sky_convention t WHERE t.convention_id = %s",
        (list(EXCLUDED_AUDIT_FIELDS), sky_convention_id)).fetchone()
    sky_vector = sky_row[0] if not isinstance(sky_row, dict) else next(iter(sky_row.values()))
    return assemble_vector({
        "stored_scope": STORED_SCOPE, "result_policy": result_policy,
        "sky_id": sky_convention_id, "sky_vector": sky_vector,
        "registry": payload, "node": node_identity(), "ephemeris": eph,
        "l0_digests": l0_identities(conn, l0_consumed),
        "admission_orb": {"orb_table": ORB_TABLE, "point_orb_source": POINT_ORB_SOURCE},
        "activity_orb": activity_orb_states(conn, refs, census_override=census_override),
        "rulings": list(rulings),
        "impl_modules": _implementation_modules(modules),
    })


def _implementation_modules(modules: dict | None) -> dict:
    mods = modules or IMPLEMENTATION_MODULES
    return {stage: {m: _module_source_digest(m) for m in names} for stage, names in mods.items()}


def diff_vectors(stored: dict, live: dict) -> list[str]:
    """The component paths that differ (empty = identical)."""
    out: list[str] = []

    def walk(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                walk(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}.{k}" if path else k)
        elif a != b:
            out.append(path)
    walk(stored, live, "")
    return out


def verify_replay(conn, stored: dict, path_refs: Iterable[tuple[str, str]], **kw) -> None:
    """HISTORICAL REPLAY checks the ORIGINAL bound inputs, ALL of them (R8-1): the vector is rebuilt from the
    inputs a replay would actually consume — the registry rows over the ORIGINAL references and the ORIGINAL
    census (versions sealed since do not move a past build's identity), the SAME L0 authorities the original
    build consumed (never today's choice), the ephemeris files + runtime library, the sky convention, the
    orb policies, the rulings and the implementation sources — and compared component by component with the
    stored vector. A replay whose ephemeris, L0, implementation or policy inputs are not the original ones is
    refused naming the component: it is a NEW generation, not a replay. `kw` = the same input arguments
    `build_input_vector` takes (sky_convention_id, ephe_path, rulings, …)."""
    if stored.get("schema") != VECTOR_SCHEMA:
        raise InputDrift(f"manifest vector schema {stored.get('schema')!r} != {VECTOR_SCHEMA!r}")
    kw.setdefault("l0_consumed", tuple(stored.get("l0", {})))
    kw.setdefault("result_policy", stored.get("result_policy"))
    replayed = build_input_vector(conn, path_refs=path_refs, census_override=stored["registry"]["census"], **kw)
    diff = diff_vectors(stored, replayed)
    if diff:
        raise InputDrift("replay: the inputs the original build consumed are not the ones available now at: "
                         + ", ".join(diff) + " — a replay must reuse the ORIGINAL ephemeris, L0, implementation "
                         "and policy inputs; anything else is a new generation")


def verify_live(conn, stored: dict, **kw) -> None:
    """A LIVE build consumes today's inputs: they must equal the vector its manifest was bound to — including
    which L0 authorities it consumes (the stored vector's own set, so a manifest never silently grows or loses
    a dependency)."""
    if stored.get("schema") != VECTOR_SCHEMA:
        raise InputDrift(f"manifest vector schema {stored.get('schema')!r} != {VECTOR_SCHEMA!r}")
    kw.setdefault("l0_consumed", tuple(stored.get("l0", {})))
    kw.setdefault("result_policy", stored.get("result_policy"))
    live = build_input_vector(conn, **kw)
    diff = diff_vectors(stored, live)
    if diff:
        raise InputDrift("consumed inputs no longer match the manifest's input vector at: "
                         + ", ".join(diff) + " — a changed input is a NEW generation, never a "
                         "silent continuation")


__all__ = ["EXCLUDED_AUDIT_FIELDS", "IMPLEMENTATION_MODULES", "InputDrift", "REGISTRY_DIGEST_SCHEMA",
           "DEFAULT_RESULT_POLICY", "EPHEMERIS_KEYS", "L0_CONSUMED", "consumed_jd_range", "POLICY_ALL_NULL", "POLICY_QUALIFICATION",
           "RESULT_POLICIES", "VECTOR_SCHEMA", "activity_orb_states", "ephemeris_component", "l0_identities",
           "library_artifact_sha",
           "platform_identity",
           "probe_opened_files", "sky_convention_identity", "admission_orb_digest", "build_input_vector",
           "STORED_SCOPE", "assemble_vector", "canonical_json", "diff_vectors", "ephemeris_identity", "implementation_digests",
           "node_identity", "probe_series_digest", "registry_digest", "registry_digest_of",
           "registry_preimage", "registry_payload", "rulings_digest", "verify_live",
           "verify_replay"]
