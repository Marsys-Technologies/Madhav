"""WP6 storage/writer layer for the gochara contact ledger.

Implements the WP1_CONTRACTS.md schemas (migration 1081, formerly 1076) against a psycopg 3
connection: convention registration, contact-ledger writes, coverage writes,
publication lifecycle (candidate -> published -> superseded/rolled_back), and
the C-1-ordered Clear operation.

Authority:
  - GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4.3 (ledger), §4.4 (coverage),
    §4.7 (publication; the writer refuses delete-then-insert against a
    `published` generation), §5.5 (input generation vector), §6.4 (Clear;
    F-24 — a Clear must leave ZERO rows in the owned relations).
  - WP1_CONTRACTS.md §1.1 (convention id), §3.2 (contact_id serialization),
    §5.4 (lifecycle).
  - GOCHARA_RULING_SHEET_v1_0.md N-7 (conditions incl. the publish-refusal),
    N-10 (publication generation '4.0', manifest).

Pure SQL, no ORM. All write entry points expect the caller to hold the
transaction (they do not COMMIT themselves), so a crash mid-write rolls back
the whole generation-scoped write — the WP6 crash/resume test depends on it.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone

try:  # a sibling workstream owns services/gochara_kernel/ids.py
    from .ids import contact_id as _ids_contact_id  # type: ignore
except ImportError:  # ids.py not present in this checkout -> local fallback
    _ids_contact_id = None

# C-1 clear order for the cockpit owner (plan §6.3/§6.4). `kala_gochara_windows`
# is NOT this family's relation at WP6 — it is listed here because the cockpit
# entry must delete in this dependency order across all three. This module
# executes the windows delete only in one place: clear_windows_on_reversal(),
# the guarded K3-F2 reversal cleanup (ADK-0024 §2); rollback()/clear_generation()
# touch only the two owned relations (coverage, then contacts).
CLEAR_OP_ORDER = (
    "kala_gochara_coverage",
    "kala_gochara_contacts",
    "kala_gochara_windows",  # cockpit-owned; not executed by this writer
)

OWNED_RELATIONS = CLEAR_OP_ORDER[:2]

# The canonical WP1 §1.1 vector a registration probe must describe.
CANONICAL_VECTOR_KEYS = (
    "zodiac",
    "ayanamsha",
    "sidereal_method",
    "node_model",
    "node_source",
    "epoch_convention",
    "time_scale",
    "house_system",
    "ephemeris_mode",
)


class TestSlicePublicationRefusal(Exception):
    """A TEST SLICE candidate (stored_scope = 'test_slice' / a test_slice component in its input vector) may never be published.
    Raised by `publish` itself — independent of the seal flow, which only refuses when a seal exists (Codex P1 on PR 3110: the builder
    holds UPDATE on the publication table and `publish` flipped candidate -> published without reading the vector)."""
    __test__ = False                       # not a pytest class


class PublishedGenerationRefusal(Exception):
    """Raised by any write/delete operation targeting a `published` generation.

    N-7 condition / plan §4.7: a published generation is immutable; a rebuild
    after publication is a NEW generation label, never an in-place refill.
    """


# ── canonical serialization helpers ──────────────────────────────────────────


def canonical_json(payload: dict) -> str:
    """WP1 §1.1/§3.2 canonical serialization: sorted keys, compact separators."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_tag(canonical: str) -> str:
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def convention_id_for(vector: dict) -> str:
    """WP1 §1.1: sha256 over the canonical vector (ephemeris_backend excluded)."""
    missing = [k for k in CANONICAL_VECTOR_KEYS if k not in vector]
    if missing:
        raise ValueError(f"convention vector missing keys: {missing}")
    canonical = canonical_json({k: vector[k] for k in CANONICAL_VECTOR_KEYS})
    return sha256_tag(canonical)


def _floor_to_minute_utc_iso(t: datetime) -> str:
    """WP1 §3.2: floor to the 60 s boundary, render UTC ISO-8601 …T…:00Z.

    Floor (not round) so the id never changes under a ±30 s jitter and
    re-partitioning a horizon differently cannot move an id across a minute
    boundary.
    """
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    epoch = math.floor(t.timestamp())
    floored = epoch - (epoch % 60)
    return datetime.fromtimestamp(floored, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")


def compute_contact_id(
    *,
    chart_id: str,
    convention_id: str,
    body: str,
    target_type: str,
    target_fact_id,
    target_ref: str,
    relation: str,
    aspect_deg,
    t_exact: datetime,
    method_version: str,
    t_in: datetime | None = None,
) -> str:
    """WP1 §3.2 contact id (local implementation).

    NOTE: duplicated pending services/gochara_kernel/ids.py (owned by a
    sibling workstream); consolidate once that module lands. The algorithm is
    pinned at WP1_CONTRACTS.md §3.2 so both implementations produce identical
    ids — the §10 identity test enforces it. A no-exact (N3 truncated) row
    passes t_exact=None WITH t_in set: identity floors t_in, marked as a
    substitution in the payload so it cannot collide with an exact contact.
    """
    if _ids_contact_id is not None:
        t_exact_jd = None
        if t_exact is not None:
            t_exact_jd = t_exact.timestamp() / 86400.0 + 2440587.5
        t_fallback_jd = None
        if t_in is not None:
            t_fallback_jd = t_in.timestamp() / 86400.0 + 2440587.5
        return _ids_contact_id(
            chart_id=chart_id,
            convention_id=convention_id,
            body=body,
            target_type=target_type,
            target_fact_id=target_fact_id,
            target_ref=target_ref,
            relation=relation,
            aspect_deg=aspect_deg,
            t_exact_jd=t_exact_jd,
            method_version=method_version,
            t_fallback_jd=t_fallback_jd,
        )
    aspect = 0.0 if aspect_deg is None else float(aspect_deg)
    payload = {
        "chart_id": str(chart_id).lower(),
        "convention_id": str(convention_id),
        "body": str(body),
        "target_kind": str(target_type),
        "target_identity": (
            "fact:" + str(target_fact_id) if target_fact_id is not None
            else "ref:" + str(target_ref)
        ),
        "relation": str(relation),
        "aspect_deg": round(aspect % 360.0, 4),
        "method_version": str(method_version),
    }
    if t_exact is None:
        if t_in is None:
            raise ValueError(
                "compute_contact_id for a no-exact episode needs t_in")
        payload["t_exact"] = None
        payload["t_in"] = _floor_to_minute_utc_iso(t_in)
    else:
        payload["t_exact"] = _floor_to_minute_utc_iso(t_exact)
    return sha256_tag(canonical_json(payload))


def reference_digest(rows: list[dict]) -> str:
    """WP1 §5.3 content digest for a small reference table (e.g. the 75
    bg_transit_rules / 8 bg_transit_av_gates rows): sha256 over the canonical
    serialization of the row set, order-independent (rows sorted by their own
    canonical form). A row count cannot catch an in-place edit of a threshold
    row — a content digest can."""
    canon = sorted(canonical_json(r) for r in rows)
    return sha256_tag(canonical_json({"rows": canon}))


# ── internal helpers ─────────────────────────────────────────────────────────

_CONTACT_COLUMNS = (
    "chart_id", "generation", "contact_id", "independence_group",
    "body", "relation", "aspect_deg", "target_type", "target_ref",
    "target_fact_id", "target_resolution_state", "target_longitude_deg",
    "t_in", "t_exact", "t_out", "bracket_seconds", "tolerance_arcsec",
    "truncated_at_horizon", "branch", "station_flag", "exact_crossing",
    "orb_max_deg", "orb_source", "dwell_days",
    "epistemic_class", "completeness_state", "operator_role",
    "precision_regime", "time_basis", "comparable_with", "inclusivity",
    "tier_basis",
    "convention_id", "ephemeris_backend", "evidence_fact_ids",
    "classical_citation", "uncited_extension", "corpus_verifiable",
    "input_generation_vector_id", "build_id", "computed_at",
)

_COVERAGE_COLUMNS = (
    "chart_id", "generation", "partition_kind", "partition_key",
    "convention_id", "requested_horizon", "completed_horizon", "resolution",
    "relations_searched", "targets_requested", "targets_resolved",
    "targets_unresolved", "target_resolution_state_counts",
    "unavailable_inputs", "unsearched_reason", "build_id", "computed_at",
)

_EPISODE_DEFAULTS = {
    "aspect_deg": 0,
    "target_fact_id": None,
    "target_longitude_deg": None,
    "truncated_at_horizon": None,
    "station_flag": False,
    "exact_crossing": True,
    "dwell_days": None,
    "epidence_fact_ids": None,  # guard against a common typo, see below
    "evidence_fact_ids": [],
    "classical_citation": None,
    "uncited_extension": False,
    "corpus_verifiable": None,
    "inclusivity": "closed_closed",
    "tier_basis": "relative_uncalibrated",
}


def _scalar(row):
    """One-column SELECT result on EITHER row shape (ASTRA A2.5 A1: the
    governed runner's connection is dict_row; standalone CLIs and the
    disposable fixtures use tuple rows — both are accepted)."""
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def _manifest_row(conn, chart_id: str, generation: str):
    """SELECT manifest_id, status — returned as a (manifest_id, status)
    TUPLE on either connection row shape (A1: the runner passes dict rows;
    every caller below stays positional against this normalised shape)."""
    row = conn.execute(
        "SELECT manifest_id, status FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchone()
    if isinstance(row, dict):
        return (row["manifest_id"], row["status"])
    return row


def _require_not_published(conn, chart_id: str, generation: str, op: str) -> None:
    """N-7 / plan §4.7: refuse any row-mutating op against a published
    generation. The caller's transaction should then be rolled back (or the
    exception propagates before any DML in simpler flows)."""
    row = _manifest_row(conn, chart_id, generation)
    if row is not None and row[1] == "published":
        raise PublishedGenerationRefusal(
            f"{op} refused: generation {generation!r} for chart {chart_id} is "
            f"published (manifest {row[0]}). A rebuild after publication is a NEW "
            f"generation label (plan §4.7, N-7); rolled-back generations must be "
            f"rebuilt under a new label."
        )


def _candidate_manifest_id(conn, chart_id: str, generation: str):
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(
            f"no manifest for chart {chart_id} generation {generation!r}: create a "
            f"candidate with publish_candidate() before writing ledger rows"
        )
    if row[1] != "candidate":
        raise PublishedGenerationRefusal(
            f"writes refused: manifest for generation {generation!r} has status "
            f"{row[1]!r}, not 'candidate'"
        )
    return row[0]


def _normalize_episode(ep: dict, chart_id: str, generation: str,
                       convention_id: str, method_version: str,
                       manifest_id, build_id: str) -> tuple:
    merged = dict(_EPISODE_DEFAULTS)
    merged.update(ep)
    if merged.get("epidence_fact_ids") is not None and "evidence_fact_ids" not in ep:
        raise ValueError("episode key 'epidence_fact_ids' looks like a typo of 'evidence_fact_ids'")
    merged.pop("epidence_fact_ids", None)
    if "method_version" in ep:
        method_version = ep["method_version"]
    # near_station rows with an unresolved station carry the honest state
    # (WP1 §3.1: unqualified propagated from near_station_unresolved).
    if merged.get("station_unresolved") and merged.get("completeness_state") != "unqualified":
        raise ValueError(
            "near-station rows with an unresolved station must carry "
            "completeness_state='unqualified' (WP1_CONTRACTS.md §3.1)"
        )
    merged.pop("station_unresolved", None)
    # B1 (KALA_SYNERGY_BINDING v2.3): served instants are timestamptz UTC, never
    # naive — "a row ... with a naive instant is rejected at write".
    for _key in ("t_in", "t_exact", "t_out"):
        _v = merged.get(_key)
        if isinstance(_v, datetime) and _v.tzinfo is None:
            raise ValueError(
                f"episode {_key} is a naive datetime; served instants must be "
                "tz-aware (B1: never a naive date as the served value — rejected "
                "at write)"
            )
    contact_id = compute_contact_id(
        chart_id=chart_id,
        convention_id=convention_id,
        body=merged["body"],
        target_type=merged["target_type"],
        target_fact_id=merged.get("target_fact_id"),
        target_ref=merged["target_ref"],
        relation=merged["relation"],
        aspect_deg=merged.get("aspect_deg"),
        t_exact=merged["t_exact"],
        method_version=method_version,
        t_in=merged["t_in"],
    )
    computed_at = merged.get("computed_at")
    ephem_backend = merged.get("ephemeris_backend")
    return (
        chart_id, generation, contact_id, merged["independence_group"],
        merged["body"], merged["relation"], merged.get("aspect_deg"),
        merged["target_type"], merged["target_ref"],
        merged.get("target_fact_id"),
        merged["target_resolution_state"],
        merged.get("target_longitude_deg"),
        merged["t_in"], merged["t_exact"], merged["t_out"],
        merged["bracket_seconds"], merged["tolerance_arcsec"],
        merged.get("truncated_at_horizon"),
        merged["branch"], merged["station_flag"], merged["exact_crossing"],
        merged["orb_max_deg"], merged["orb_source"], merged.get("dwell_days"),
        merged["epistemic_class"], merged["completeness_state"],
        merged["operator_role"], merged["precision_regime"],
        merged["time_basis"], merged["comparable_with"], merged["inclusivity"],
        merged["tier_basis"],
        convention_id,
        canonical_json(ephem_backend) if isinstance(ephem_backend, dict) else ephem_backend,
        canonical_json(merged["evidence_fact_ids"]),
        merged.get("classical_citation"),
        merged["uncited_extension"],
        merged.get("corpus_verifiable"),
        manifest_id,
        build_id,
        computed_at or datetime.now(timezone.utc),
    )


def _insert_contact_rows(conn, rows: list[tuple]) -> None:
    if not rows:
        return
    cols = ", ".join(_CONTACT_COLUMNS)
    placeholders = ", ".join(["%s"] * len(_CONTACT_COLUMNS))
    with conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO kala_gochara_contacts ({cols}) VALUES ({placeholders})",
            rows,
        )


# ── public API ───────────────────────────────────────────────────────────────


def register_convention(conn, vector: dict, probe: dict,
                        se1_checksums: dict | None = None) -> str:
    """Register (idempotently) one convention row; returns convention_id.

    `vector` — the nine canonical WP1 §1.1 fields (ephemeris_backend is
    deliberately NOT hashed into the id). `probe` — {ephemeris_backend,
    retflag} recorded FROM the probe calc's returned retflag (F-14: never
    from the requested flag). Insert-only at the SQL level (trigger); a
    tolerance or method change registers a NEW row (N-7 condition).
    """
    cid = convention_id_for(vector)
    conn.execute(
        """
        INSERT INTO kala_gochara_convention (
          convention_id, zodiac, ayanamsha, sidereal_method, node_model,
          node_source, epoch_convention, time_scale, house_system,
          ephemeris_mode, ephemeris_backend, probe_retflag, se1_checksums,
          method_version
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (convention_id) DO NOTHING
        """,
        (
            cid,
            vector["zodiac"], vector["ayanamsha"], vector["sidereal_method"],
            vector["node_model"], vector["node_source"],
            vector["epoch_convention"], vector["time_scale"],
            vector["house_system"], vector["ephemeris_mode"],
            probe.get("ephemeris_backend"), probe.get("retflag"),
            canonical_json(se1_checksums) if isinstance(se1_checksums, dict) else se1_checksums,
            vector["method_version"],
        ),
    )
    return cid


def write_contacts(conn, chart_id: str, generation: str, convention_id: str,
                   episodes: list[dict], build_id: str,
                   bodies: list[str] | None = None) -> list[str]:
    """Delete-then-insert of the contact ledger, scoped (chart_id, generation).

    Legal ONLY while the generation is a `candidate` (plan §4.7 idempotent
    rebuild); raises PublishedGenerationRefusal if the generation has a
    `published` manifest (N-7 release condition). Requires a candidate manifest
    (publish_candidate) — the manifest id is stored on every row as
    input_generation_vector_id. Returns the ordered contact_id list. Does NOT
    commit: the caller owns the transaction.

    `bodies` (default None — behaviour byte-identical to the original) narrows
    the DELETE to the named bodies, for per-body idempotent substeps of a
    chunked candidate build (A2.5): re-running one body's substep replaces
    exactly that body's rows and no other's. Every episode in the payload
    must belong to one of the named bodies — a mismatch refuses honestly.
    """
    _require_not_published(conn, chart_id, generation, "write_contacts")
    manifest_id = _candidate_manifest_id(conn, chart_id, generation)
    method_version = _scalar(conn.execute(
        "SELECT method_version FROM kala_gochara_convention WHERE convention_id = %s",
        (convention_id,),
    ).fetchone())
    rows = [
        _normalize_episode(ep, chart_id, generation, convention_id,
                           method_version, manifest_id, build_id)
        for ep in episodes
    ]
    if bodies is None:
        conn.execute(
            "DELETE FROM kala_gochara_contacts WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        )
    else:
        scope = {str(b) for b in bodies}
        foreign = sorted({str(r[4]) for r in rows} - scope)  # r[4] = body
        if foreign:
            raise ValueError(
                f"write_contacts bodies-scope violation: payload carries bodies "
                f"{foreign} outside the declared substep scope {sorted(scope)} — "
                "a body-scoped substep may only replace its own rows")
        conn.execute(
            "DELETE FROM kala_gochara_contacts"
            " WHERE chart_id = %s AND generation = %s AND body = ANY(%s)",
            (chart_id, generation, sorted(scope)),
        )
    _insert_contact_rows(conn, rows)
    return [r[2] for r in rows]


def write_coverage(conn, chart_id: str, generation: str, convention_id: str,
                   partitions: list[dict], build_id: str,
                   bodies: list[str] | None = None) -> int:
    """Delete-then-insert of the coverage manifest, scoped (chart_id,
    generation). Same lifecycle rules as write_contacts. Horizon ranges are
    accepted as psycopg Range objects or '[lo,hi)' text and stored as
    tstzrange. Returns the row count written.

    `bodies` (default None — behaviour byte-identical to the original) narrows
    the DELETE to partitions whose key begins '<body>:' (the enumerator's
    per-body partition_key convention), for per-body idempotent substeps
    (A2.5). Every supplied partition must match the scope — a mismatch
    refuses honestly."""
    _require_not_published(conn, chart_id, generation, "write_coverage")
    _candidate_manifest_id(conn, chart_id, generation)
    rows = []
    for p in partitions:
        state_counts = p["target_resolution_state_counts"]
        resolved = state_counts.get("resolved", 0)
        unresolved = (
            state_counts.get("unavailable", 0) + state_counts.get("unqualified", 0)
        )
        rows.append((
            chart_id, generation, p["partition_kind"], p["partition_key"],
            convention_id, p["requested_horizon"], p["completed_horizon"],
            p["resolution"], list(p["relations_searched"]),
            p["targets_requested"], resolved, unresolved,
            canonical_json(state_counts),
            canonical_json(p.get("unavailable_inputs") or {}),
            p.get("unsearched_reason"),
            build_id,
            p.get("computed_at") or datetime.now(timezone.utc),
        ))
    if bodies is None:
        conn.execute(
            "DELETE FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        )
    else:
        scope = sorted({str(b).lower() for b in bodies})
        foreign = sorted({str(r[3]) for r in rows  # r[3] = partition_key
                          if r[3].split(":", 1)[0].lower() not in scope})
        if foreign:
            raise ValueError(
                f"write_coverage bodies-scope violation: partitions {foreign} "
                f"outside the declared substep scope {scope} — a body-scoped "
                "substep may only replace its own partitions")
        conn.execute(
            "DELETE FROM kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND lower(split_part(partition_key, ':', 1)) = ANY(%s)",
            (chart_id, generation, scope),
        )
    if rows:
        cols = ", ".join(_COVERAGE_COLUMNS)
        placeholders = ", ".join(["%s"] * len(_COVERAGE_COLUMNS))
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO kala_gochara_coverage ({cols}) VALUES ({placeholders})",
                rows,
            )
    return len(rows)


def publish_candidate(conn, chart_id: str, generation: str, convention_id: str,
                      input_generation_vector: dict, ephemeris_backend: dict,
                      horizon, writer_asset_id: str = "ka_gochara") -> str:
    """Create (or, while `candidate`, replace) the manifest for a generation.

    A rebuild while candidate replaces the candidate row IN PLACE (same
    manifest_id, delete-then-insert semantics at the row level, plan §4.7);
    a manifest already `published`/`superseded`/`rolled_back` refuses.
    content_digest/row_counts are recomputed by publish(). Returns manifest_id.
    """
    row = _manifest_row(conn, chart_id, generation)
    ephem = canonical_json(ephemeris_backend) if isinstance(ephemeris_backend, dict) else ephemeris_backend
    vector = canonical_json(input_generation_vector) if isinstance(input_generation_vector, dict) else input_generation_vector
    if row is None:
        manifest_id = _scalar(conn.execute(
            """
            INSERT INTO kala_gochara_publication (
              chart_id, generation, writer_asset_id, convention_id,
              input_generation_vector, ephemeris_backend, horizon,
              row_counts, content_digest, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s::tstzrange, '{}'::jsonb,
                      'sha256:unpublished-candidate', 'candidate')
            RETURNING manifest_id
            """,
            (chart_id, generation, writer_asset_id, convention_id,
             vector, ephem, horizon),
        ).fetchone())
        return str(manifest_id)
    if row[1] != "candidate":
        raise PublishedGenerationRefusal(
            f"publish_candidate refused: manifest for generation {generation!r} "
            f"has status {row[1]!r}; a rebuild after publication is a NEW "
            f"generation label (plan §4.7)"
        )
    # The replace is CONDITIONAL on the row still being a candidate (Codex round 4 follow-up (d)): between the status read above and this
    # UPDATE a publish can flip the row, and an unconditional UPDATE would then rewrite the input vector of a PUBLISHED manifest (a stale
    # caller could even stamp it as a test slice). The draft database CHECK (PR 3140) refuses a published slice stamp; this makes the
    # rewrite of any non-candidate vector impossible from the writer's own path.
    replaced = conn.execute(
        """
        UPDATE kala_gochara_publication
        SET convention_id = %s, input_generation_vector = %s,
            ephemeris_backend = %s, horizon = %s::tstzrange,
            row_counts = '{}'::jsonb, content_digest = 'sha256:unpublished-candidate'
        WHERE manifest_id = %s AND status = 'candidate'
        """,
        (convention_id, vector, ephem, horizon, row[0]),
    )
    if getattr(replaced, "rowcount", None) == 0:
        raise PublishedGenerationRefusal(
            f"publish_candidate refused: the manifest for generation {generation!r} was no longer a candidate when it was replaced "
            "(it changed status after it was read — a stale caller); nothing was rewritten"
        )
    return str(row[0])


def _candidate_boundary():
    """The sibling `candidate_boundary` module. The a25 candidate writer loads this file BY PATH (no parent package), where a relative import
    cannot resolve — so fall back to loading the sibling file the same way (the writer's `_load_module` precedent). In a package context the
    ordinary relative import is used, so there is still exactly one module object there."""
    try:
        from . import candidate_boundary as cb  # type: ignore
        return cb
    except ImportError:
        import importlib.util
        import sys
        from pathlib import Path
        name = "gochara_ledger_bypath_candidate_boundary"
        cached = sys.modules.get(name)
        if cached is not None:
            return cached
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("candidate_boundary.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module


def _canonical_row_set(conn, chart_id: str, generation: str) -> str:
    """sha256 over the canonical sorted row content of contacts + coverage —
    the manifest content_digest (plan §4.7)."""
    contact_rows = conn.execute(
        "SELECT row_to_json(c.*) FROM kala_gochara_contacts c "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchall()
    # R12-1: the publication boundary is the CANDIDATE boundary (`candidate_boundary`): for a governed (5.x) generation the
    # on-demand Moon receipts (AM-4: written at query time) are NOT part of the published content — the approval binds exactly
    # what this digest covers. Legacy (pre-5) generations keep every coverage row.
    cb = _candidate_boundary()
    EXCLUDED_ON_DEMAND_KINDS, is_governed = cb.EXCLUDED_ON_DEMAND_KINDS, cb.is_governed
    if is_governed(generation):
        coverage_rows = conn.execute(
            "SELECT row_to_json(c.*) FROM kala_gochara_coverage c "
            "WHERE chart_id = %s AND generation = %s AND partition_kind <> ALL(%s)",
            (chart_id, generation, list(EXCLUDED_ON_DEMAND_KINDS)),
        ).fetchall()
    else:
        coverage_rows = conn.execute(
            "SELECT row_to_json(c.*) FROM kala_gochara_coverage c "
            "WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        ).fetchall()
    canon = sorted(
        canonical_json(_scalar(r)) for r in list(contact_rows) + list(coverage_rows)
    )
    return sha256_tag(canonical_json(
        {"chart_id": str(chart_id), "generation": generation, "rows": canon}
    ))


def _refuse_test_slice(conn, manifest_id, generation: str) -> None:
    """Refuse, by name, to publish a manifest whose input vector says it is a TEST SLICE (either marker is enough: the scope word
    or the component). Read from the stored row itself, never from a caller's say-so."""
    row = conn.execute("SELECT input_generation_vector FROM kala_gochara_publication WHERE manifest_id = %s",
                       (manifest_id,)).fetchone()
    vector = (row.get("input_generation_vector") if isinstance(row, dict) else row[0]) if row is not None else None
    if isinstance(vector, str):
        import json as _json
        vector = _json.loads(vector)
    if isinstance(vector, dict) and (vector.get("stored_scope") == "test_slice" or "test_slice" in vector):
        raise TestSlicePublicationRefusal(
            f"publish refused: the manifest of generation {generation!r} is a TEST SLICE (stored_scope="
            f"{vector.get('stored_scope')!r}, test_slice component {'present' if 'test_slice' in vector else 'absent'}) — a "
            "small-test candidate is unsealable and unpublishable by construction; run the full build under a real manifest")


def _take_chart_lock(conn, chart_id: str) -> None:
    """The established chart TRANSACTION lock (`ka_gochara_lock_chart`, migration 1153) — the one every Gochara writer, including
    the manifest substep that replaces a candidate's input vector, takes before it touches the chart. Taken only where the function
    exists (ledger-only fixtures do not carry it)."""
    probe = conn.execute("SELECT to_regprocedure('public.ka_gochara_lock_chart(uuid)') IS NOT NULL").fetchone()
    if probe is not None and _scalar(probe):
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (str(chart_id),))


def publish(conn, chart_id: str, generation: str) -> str:
    """Transition candidate -> published.

    Computes content_digest (sha256 over the canonical sorted row set) and
    row_counts at the transition; sets published_at. Idempotent on an
    already-published generation. The partial unique index
    kala_gochara_publication_one_published enforces N-10 (one published
    manifest per chart+generation) at the database level.

    GOVERNED generations (5.x, `candidate_boundary.is_governed`) are published ATOMICALLY against a concurrent rebuild (Codex rounds
    3 and 4 on PR 3110): the Gochara-5 chart transaction lock (`ka_gochara_lock_chart`, migration 1153) is taken BEFORE the first
    read, and the flip itself is CONDITIONAL — still a candidate, no `test_slice` scope word, no `test_slice` component — refusing
    by name when it updates no row. LEGACY generations (3.x, 4.x) behave EXACTLY as before for every chart: no lock (the Gochara-5
    lock function refuses any chart but the canonical one, and a legacy flip of another chart must not start failing), no slice
    check, the original unconditional flip.

    TRANSACTIONS. For a governed generation the lock and the flip run inside `conn.transaction()`. That block BEGINs and COMMITS
    when it is entered on an IDLE connection (autocommit, or no transaction open yet) — the commit covers this publish only — and is
    a SAVEPOINT when the connection is already inside a transaction, which is the case for both production callers: `seal_flow`
    (inside its seal transaction, under the seal locks, so nothing stays published if its later checks refuse) and `step08_flip`
    (autocommit=False, earlier statements already issued). A caller that wants publish and its next statement to commit together
    must already be inside a transaction.

    The unconditional database-level guarantee (a CHECK refusing `published` for a slice-stamped vector, and the builder's UPDATE
    grant from migration 1216) is a migration for a later protected window (draft PR 3140)."""
    if not _candidate_boundary().is_governed(generation):
        return _publish(conn, chart_id, generation, governed=False)
    transaction = getattr(conn, "transaction", None)
    if transaction is None:                               # a ledger-only fake without transactions
        return _publish(conn, chart_id, generation, governed=True)
    with transaction():
        return _publish(conn, chart_id, generation, governed=True)


def _publish(conn, chart_id: str, generation: str, *, governed: bool) -> str:
    if governed:
        _take_chart_lock(conn, chart_id)
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] == "published":
        return str(row[0])
    if row[1] != "candidate":
        raise ValueError(
            f"cannot publish generation {generation!r}: manifest status is {row[1]!r}"
        )
    if governed:
        _refuse_test_slice(conn, row[0], generation)
    digest = _canonical_row_set(conn, chart_id, generation)
    counts = {
        "contacts": _scalar(conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts "
            "WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        ).fetchone()),
        "coverage": _scalar(conn.execute(
            "SELECT count(*) FROM kala_gochara_coverage "
            "WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        ).fetchone()),
        "windows": (
            # Honest count of the projection's relation when it exists
            # (kala_gochara_windows is not WP6-owned; 0 when the table is
            # absent, e.g. in ledger-only fixtures).
            _scalar(conn.execute(
                "SELECT count(*) FROM kala_gochara_windows "
                "WHERE chart_id = %s AND generation = %s",
                (chart_id, generation),
            ).fetchone())
            if _scalar(conn.execute(
                "SELECT to_regclass('kala_gochara_windows') IS NOT NULL"
            ).fetchone())
            else 0
        ),
    }
    if not governed:
        # LEGACY (3.x / 4.x): the original flip, unchanged
        conn.execute(
            """
            UPDATE kala_gochara_publication
            SET status = 'published', published_at = now(),
                content_digest = %s, row_counts = %s::jsonb
            WHERE manifest_id = %s
            """,
            (digest, canonical_json(counts), row[0]),
        )
        return str(row[0])
    flipped = conn.execute(
        """
        UPDATE kala_gochara_publication
        SET status = 'published', published_at = now(),
            content_digest = %s, row_counts = %s::jsonb
        WHERE manifest_id = %s AND status = 'candidate'
          AND COALESCE(input_generation_vector->>'stored_scope', '') <> 'test_slice'
          AND NOT COALESCE(input_generation_vector ? 'test_slice', false)
        """,
        (digest, canonical_json(counts), row[0]),
    )
    if getattr(flipped, "rowcount", None) == 0:
        # the row changed after it was read (or the checks above were bypassed): say WHICH, by name
        _refuse_test_slice(conn, row[0], generation)
        raise PublishedGenerationRefusal(
            f"publish refused: the manifest of generation {generation!r} was no longer an unstamped candidate when it was flipped "
            "(it changed concurrently); nothing was published")
    return str(row[0])


def supersede(conn, chart_id: str, generation: str) -> str:
    """Transition published -> superseded (a later generation took over)."""
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] != "published":
        raise ValueError(f"cannot supersede generation {generation!r}: status {row[1]!r}")
    conn.execute(
        "UPDATE kala_gochara_publication SET status = 'superseded', "
        "superseded_at = now() WHERE manifest_id = %s",
        (row[0],),
    )
    return str(row[0])


def _generation_sealed(conn, chart_id: str, generation: str) -> bool:
    """Does a seal row exist for the generation? (False where the seal relation does not exist — ledger-only fixtures.)"""
    if not _scalar(conn.execute("SELECT to_regclass('public.ka_gochara_generation_seal') IS NOT NULL").fetchone()):
        return False
    return bool(_scalar(conn.execute(
        "SELECT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s)",
        (chart_id, generation)).fetchone()))


def rollback(conn, chart_id: str, generation: str) -> str:
    """Full rollback of a generation: manifest -> rolled_back, rows under own
    (chart_id, generation) scope removed (coverage then contacts, the C-1
    order). The manifest row itself is MARKED, never deleted (plan §4.7 /
    WP1 §5.4: `rolled_back`, not deleted).

    A SEALED generation is never row-deleted (its rows are the attested candidate — R14-2): the explicit sealed route is a METADATA-ONLY
    WITHDRAWAL — the manifest goes `published` -> `rolled_back` (1240's sealed-lifecycle whitelist) and every attested row, the seal and the
    approval receipt stay exactly as they were. A sealed generation that is not `published` (e.g. already superseded) is refused by name."""
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] in ("superseded", "rolled_back"):
        raise ValueError(f"cannot rollback generation {generation!r}: status {row[1]!r}")
    if _generation_sealed(conn, chart_id, generation):
        if row[1] != "published":
            raise ValueError(f"cannot withdraw sealed generation {generation!r}: status {row[1]!r} (a sealed generation is withdrawn only from 'published')")
    else:
        _delete_generation_rows(conn, chart_id, generation)
    conn.execute(
        "UPDATE kala_gochara_publication SET status = 'rolled_back' "
        "WHERE manifest_id = %s",
        (row[0],),
    )
    return str(row[0])


def _delete_generation_rows(conn, chart_id: str, generation: str) -> None:
    """C-1 dependency order over the OWNED relations: coverage, then contacts.
    `kala_gochara_windows` is the cockpit/projection owner's relation and is
    deliberately not touched here (see CLEAR_OP_ORDER)."""
    conn.execute(
        "DELETE FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    )
    conn.execute(
        "DELETE FROM kala_gochara_contacts WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    )


def clear_windows_on_reversal(conn, chart_id: str, generation: str) -> int:
    """Scoped delete of the reversed chart's kala_gochara_windows rows
    (K3-F2 / ADK-0024 §2). Without this, `step08_flip.py --reverse` leaves
    orphan '4.0' windows whose coverage rows and candidate manifest are gone
    — re-pinned conjuncts (a) and (f) then read the post-reversal state as
    permanently RED.

    Explicit, scoped op — the same statement as
    EXPLICIT_CLEAR_OPS['ka_gochara'][2]
    (`DELETE FROM kala_gochara_windows WHERE chart_id AND generation='4.0'`),
    here parameterized by the reversed generation.

    HARD GUARD (the ruling's condition): refuses unless
      * the generation is a candidate-family generation — 'v1' and '3.0' are
        untouchable here regardless of any other state; and
      * the manifest exists with status 'candidate' or 'rolled_back' (a
        published generation is the live or most-recent authority — its
        windows are the served rows); and
      * the generation is NOT the chart's currently served authority
        (kala_gochara_authority). Reverse authority FIRST, windows cleanup
        SECOND — a cleanup that can fire on a live authority is a guard
        bypass.

    Returns the number of window rows deleted."""
    if generation in ("v1", "3.0"):
        raise PublishedGenerationRefusal(
            f"clear_windows_on_reversal refused: generation {generation!r} is "
            "a prior served generation, not a candidate — 'v1'/'3.0' windows "
            "are untouchable on the reversal path")
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] not in ("candidate", "rolled_back"):
        raise PublishedGenerationRefusal(
            f"clear_windows_on_reversal refused: manifest for generation "
            f"{generation!r} has status {row[1]!r}, not 'candidate'/'rolled_back' "
            "— a published generation's windows are the served rows")
    auth = conn.execute(
        "SELECT authoritative_generation FROM kala_gochara_authority "
        "WHERE chart_id = %s",
        (chart_id,),
    ).fetchone()
    if auth is not None and auth[0] == generation:
        raise PublishedGenerationRefusal(
            f"clear_windows_on_reversal refused: generation {generation!r} is "
            f"the chart's SERVED authority — reverse authority first "
            "(step08_flip.py --reverse), then clean up windows")
    cur = conn.execute(
        "DELETE FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    )
    return cur.rowcount


def clear_generation(conn, chart_id: str, generation: str) -> str:
    """C-1 Clear (plan §6.4, F-24): leaves ZERO rows in the owned relations.

    Deletes coverage then contacts (CLEAR_OP_ORDER[:2]; the windows DELETE is
    the cockpit owner's op), and marks the manifest `rolled_back` so no
    candidate/published state survives. REFUSES when the generation is
    `published` (a Clear whose target is published must go through the
    release-authority rollback path, plan §6.4) — and refuses a second Clear
    of an already-cleared generation.
    """
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] == "published":
        raise PublishedGenerationRefusal(
            f"clear_generation refused: generation {generation!r} is published; "
            f"clearing a published generation is the release authority's "
            f"rollback path (plan §6.4), not the cockpit Clear"
        )
    if row[1] != "candidate":
        raise ValueError(f"cannot clear generation {generation!r}: status {row[1]!r}")
    _delete_generation_rows(conn, chart_id, generation)
    conn.execute(
        "UPDATE kala_gochara_publication SET status = 'rolled_back' "
        "WHERE manifest_id = %s",
        (row[0],),
    )
    return str(row[0])
