"""WP6 storage/writer layer for the gochara contact ledger.

Implements the WP1_CONTRACTS.md schemas (migration 1072) against a psycopg 3
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
# entry must delete in this dependency order across all three; this module only
# executes the two owned relations (coverage, then contacts).
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
) -> str:
    """WP1 §3.2 contact id (local implementation).

    NOTE: duplicated pending services/gochara_kernel/ids.py (owned by a
    sibling workstream); consolidate once that module lands. The algorithm is
    pinned at WP1_CONTRACTS.md §3.2 so both implementations produce identical
    ids — the §10 identity test enforces it.
    """
    if _ids_contact_id is not None:
        return _ids_contact_id(
            chart_id=chart_id,
            convention_id=convention_id,
            body=body,
            target_type=target_type,
            target_fact_id=target_fact_id,
            target_ref=target_ref,
            relation=relation,
            aspect_deg=aspect_deg,
            t_exact=t_exact,
            method_version=method_version,
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
        "t_exact": _floor_to_minute_utc_iso(t_exact),
        "method_version": str(method_version),
    }
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
    "epistemic_class", "completeness_state", "operator_role", "claim_grain",
    "time_basis", "comparable_with",
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
}


def _manifest_row(conn, chart_id: str, generation: str):
    return conn.execute(
        "SELECT manifest_id, status FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchone()


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
        merged["operator_role"], merged["claim_grain"], merged["time_basis"],
        merged["comparable_with"],
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
                   episodes: list[dict], build_id: str) -> list[str]:
    """Delete-then-insert of the contact ledger, scoped (chart_id, generation).

    Legal ONLY while the generation is a `candidate` (plan §4.7 idempotent
    rebuild); raises PublishedGenerationRefusal if the generation has a
    `published` manifest (N-7 release condition). Requires a candidate manifest
    (publish_candidate) — the manifest id is stored on every row as
    input_generation_vector_id. Returns the ordered contact_id list. Does NOT
    commit: the caller owns the transaction.
    """
    _require_not_published(conn, chart_id, generation, "write_contacts")
    manifest_id = _candidate_manifest_id(conn, chart_id, generation)
    method_version = conn.execute(
        "SELECT method_version FROM kala_gochara_convention WHERE convention_id = %s",
        (convention_id,),
    ).fetchone()[0]
    rows = [
        _normalize_episode(ep, chart_id, generation, convention_id,
                           method_version, manifest_id, build_id)
        for ep in episodes
    ]
    conn.execute(
        "DELETE FROM kala_gochara_contacts WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    )
    _insert_contact_rows(conn, rows)
    return [r[2] for r in rows]


def write_coverage(conn, chart_id: str, generation: str, convention_id: str,
                   partitions: list[dict], build_id: str) -> int:
    """Delete-then-insert of the coverage manifest, scoped (chart_id,
    generation). Same lifecycle rules as write_contacts. Horizon ranges are
    accepted as psycopg Range objects or '[lo,hi)' text and stored as
    tstzrange. Returns the row count written."""
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
    conn.execute(
        "DELETE FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
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
        manifest_id = conn.execute(
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
        ).fetchone()[0]
        return str(manifest_id)
    if row[1] != "candidate":
        raise PublishedGenerationRefusal(
            f"publish_candidate refused: manifest for generation {generation!r} "
            f"has status {row[1]!r}; a rebuild after publication is a NEW "
            f"generation label (plan §4.7)"
        )
    conn.execute(
        """
        UPDATE kala_gochara_publication
        SET convention_id = %s, input_generation_vector = %s,
            ephemeris_backend = %s, horizon = %s::tstzrange,
            row_counts = '{}'::jsonb, content_digest = 'sha256:unpublished-candidate'
        WHERE manifest_id = %s
        """,
        (convention_id, vector, ephem, horizon, row[0]),
    )
    return str(row[0])


def _canonical_row_set(conn, chart_id: str, generation: str) -> str:
    """sha256 over the canonical sorted row content of contacts + coverage —
    the manifest content_digest (plan §4.7)."""
    contact_rows = conn.execute(
        "SELECT row_to_json(c.*) FROM kala_gochara_contacts c "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchall()
    coverage_rows = conn.execute(
        "SELECT row_to_json(c.*) FROM kala_gochara_coverage c "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchall()
    canon = sorted(
        canonical_json(r[0]) for r in list(contact_rows) + list(coverage_rows)
    )
    return sha256_tag(canonical_json(
        {"chart_id": str(chart_id), "generation": generation, "rows": canon}
    ))


def publish(conn, chart_id: str, generation: str) -> str:
    """Transition candidate -> published.

    Computes content_digest (sha256 over the canonical sorted row set) and
    row_counts at the transition; sets published_at. Idempotent on an
    already-published generation. The partial unique index
    kala_gochara_publication_one_published enforces N-10 (one published
    manifest per chart+generation) at the database level.
    """
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] == "published":
        return str(row[0])
    if row[1] != "candidate":
        raise ValueError(
            f"cannot publish generation {generation!r}: manifest status is {row[1]!r}"
        )
    digest = _canonical_row_set(conn, chart_id, generation)
    counts = {
        "contacts": conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts "
            "WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        ).fetchone()[0],
        "coverage": conn.execute(
            "SELECT count(*) FROM kala_gochara_coverage "
            "WHERE chart_id = %s AND generation = %s",
            (chart_id, generation),
        ).fetchone()[0],
        "windows": 0,  # windows are the projection's relation, not WP6-owned
    }
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


def rollback(conn, chart_id: str, generation: str) -> str:
    """Full rollback of a generation: manifest -> rolled_back, rows under own
    (chart_id, generation) scope removed (coverage then contacts, the C-1
    order). The manifest row itself is MARKED, never deleted (plan §4.7 /
    WP1 §5.4: `rolled_back`, not deleted)."""
    row = _manifest_row(conn, chart_id, generation)
    if row is None:
        raise ValueError(f"no manifest for chart {chart_id} generation {generation!r}")
    if row[1] in ("superseded", "rolled_back"):
        raise ValueError(f"cannot rollback generation {generation!r}: status {row[1]!r}")
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
