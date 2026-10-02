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

VECTOR_SCHEMA = "ka_gochara_input_vector/1"
REGISTRY_DIGEST_SCHEMA = "ka_gochara_registry_digest/1"
EXCLUDED_AUDIT_FIELDS = ("created_at", "sealed_at")

# Closed module lists: the code that GOVERNS each result-bearing stage.
IMPLEMENTATION_MODULES = {
    "geometry": ("services.gochara_kernel.arcs", "services.gochara_kernel.episodes",
                 "services.gochara_kernel.contacts", "services.gochara_kernel.materialise",
                 "services.gochara_kernel.targets", "services.gochara_kernel.knots",
                 "services.gochara_kernel.convention", "services.gochara_kernel.record_store"),
    "evaluation": ("services.gochara_kernel.evaluator", "services.gochara_rules.score",
                   "services.gochara_rules.valence", "services.gochara_rules.admission",
                   "services.gochara_rules.favourable_houses", "services.gochara_rules.drishti",
                   "services.gochara_rules.registry", "services.gochara_rules.predicates"),
    "window": ("services.gochara_kernel.window_sweep", "services.gochara_kernel.window_store"),
}


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


def registry_digest(conn, path_refs: Iterable[tuple[str, str]], *, census_override=None) -> str:
    return _sha(canonical_json(registry_payload(conn, path_refs, census_override=census_override)))


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


def ephemeris_identity(ephe_path: str | None) -> dict:
    """The Swiss library version and the sha256 of every `.se1` in the consumed ephemeris path. No
    path ⇒ the identity cannot be bound: refused, never recorded as 'unknown' (a vector that cannot
    distinguish two ephemerides is not an identity)."""
    import swisseph as swe
    if not ephe_path:
        raise InputDrift("ephemeris: no ephe_path configured — the node-series identity cannot be bound")
    files = sorted(Path(ephe_path).glob("*.se1"))
    if not files:
        raise InputDrift(f"ephemeris: no .se1 files under {ephe_path!r} — nothing to bind")
    return {"backend": "swieph", "swe_version": swe.version,
            "files": {f.name: _file_sha(f) for f in files}}


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


def activity_orb_states(conn, path_refs) -> dict:
    """The ACTIVITY orb as the persisted `activity_kernel` rows state it: per row version, the orb
    (omitted when unratified) — restated explicitly so a ratification is visible in the vector
    itself, not only inside the registry digest."""
    out = {}
    for f in registry_payload(conn, path_refs)["factors"]:
        if f["factor_id"] == "activity_kernel":
            sel = f["operand_selector"]
            out[f["rule_version"]] = (sel["angular_orb_deg"] if sel.get("angular_orb_state") == "ratified"
                                      else sel.get("angular_orb_state", "undeclared"))
    return out


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

def build_input_vector(conn, *, sky_convention_id: str, ephe_path: str | None,
                       path_refs: Iterable[tuple[str, str]], rulings: Iterable[dict],
                       modules: dict | None = None) -> dict:
    refs = list(path_refs)
    payload = registry_payload(conn, refs)
    return {
        "schema": VECTOR_SCHEMA,
        "sky_convention": sky_convention_id,
        "registry": {"digest": _sha(canonical_json(payload)), "census": payload["census"]},
        "node": node_identity(),
        "ephemeris": ephemeris_identity(ephe_path),
        "orb_policy": {"admission_digest": admission_orb_digest(),
                       "activity": activity_orb_states(conn, refs)},
        "rulings_digest": rulings_digest(rulings),
        "implementation": implementation_digests(modules),
    }


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


def verify_replay(conn, stored: dict, path_refs: Iterable[tuple[str, str]]) -> None:
    """HISTORICAL REPLAY checks the ORIGINAL bound inputs: the registry digest recomputed over the
    ORIGINAL references and the ORIGINAL census — never a fingerprint of today's catalogue (versions
    sealed since do not move a past build's identity)."""
    if stored.get("schema") != VECTOR_SCHEMA:
        raise InputDrift(f"manifest vector schema {stored.get('schema')!r} != {VECTOR_SCHEMA!r}")
    got = registry_digest(conn, path_refs, census_override=stored["registry"]["census"])
    if got != stored["registry"]["digest"]:
        raise InputDrift(f"replay: the registry rows the original build consumed changed "
                         f"({got} != {stored['registry']['digest']})")


def verify_live(conn, stored: dict, **kw) -> None:
    """A LIVE build consumes today's inputs: they must equal the vector its manifest was bound to."""
    if stored.get("schema") != VECTOR_SCHEMA:
        raise InputDrift(f"manifest vector schema {stored.get('schema')!r} != {VECTOR_SCHEMA!r}")
    live = build_input_vector(conn, **kw)
    diff = diff_vectors(stored, live)
    if diff:
        raise InputDrift("consumed inputs no longer match the manifest's input vector at: "
                         + ", ".join(diff) + " — a changed input is a NEW generation, never a "
                         "silent continuation")


__all__ = ["EXCLUDED_AUDIT_FIELDS", "IMPLEMENTATION_MODULES", "InputDrift", "REGISTRY_DIGEST_SCHEMA",
           "VECTOR_SCHEMA", "activity_orb_states", "admission_orb_digest", "build_input_vector",
           "canonical_json", "diff_vectors", "ephemeris_identity", "implementation_digests",
           "node_identity", "registry_digest", "registry_payload", "rulings_digest", "verify_live",
           "verify_replay"]
