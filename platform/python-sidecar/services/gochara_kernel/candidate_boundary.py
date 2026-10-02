"""The ONE explicit CANDIDATE BOUNDARY of a governed ('5.x') generation (Codex round 12, R12-1) — shared by the approval brief, the
publication content digest and the sealing recompute, so the three can never disagree about what "the candidate" is.

COVERED (identity-bound; any change moves the approval digest):
  * the seven governed output tables — every column but `created_at` (seal_brief.OUTPUT_TABLES);
  * the BUILD coverage partitions of the generation (`kala_gochara_coverage`, kinds `body_target` / `event_class`): resolution, target
    counts, resolution-state counts, unavailable-input declarations, unsearched reason, horizons, build id — every column but
    `created_at` (the table's `computed_at` stamp is part of the candidate: a rebuild is a different candidate);
  * the manifest's identity: manifest id, writer asset, convention, horizon, input-generation vector (digest) AND the ephemeris backend;
  * the exact `content_digest` that PUBLICATION will store (`publication_content_digest` — the same function `ledger.publish` calls);
  * the attestations as stored, the runner/code identity, the migration-ledger evidence;
  * the legacy projection relations for the generation: NONE may exist (`kala_gochara_contacts`, `kala_gochara_windows` — the '5.0'
    writer writes none), enforced by a gate arm, the job and the brief.

NOT COVERED (stated, not implied):
  * on-demand Moon receipts (coverage kinds `moon_on_demand` / `bodies_on_demand`, AM-4): written at QUERY time, deliberately outside
    build identity — and outside the publication digest (this module's kinds are what `ledger._canonical_row_set` uses for a governed
    generation);
  * global physical objects and contact identities, which the covered rows REFERENCE: they are global and insert-only (the database
    refuses their update), so binding the references while relying on that immutability is the defensible boundary;
  * sky events: global, enrichable, and not consumed by the P1–P4 candidate verification path;
  * `created_at` (an audit stamp): the claim is about semantic candidate identity, not every possible byte difference."""
from __future__ import annotations

import hashlib

#: coverage partitions that are part of the BUILD (and of the publication digest) of a governed generation
BUILD_COVERAGE_KINDS = ("body_target", "event_class")
#: AM-4: query-time receipts, deliberately NOT build identity
EXCLUDED_ON_DEMAND_KINDS = ("moon_on_demand", "bodies_on_demand")
LEGACY_PROJECTION_TABLES = ("kala_gochara_contacts", "kala_gochara_windows")

NOT_COVERED = (
    "on-demand Moon receipts (coverage kinds moon_on_demand / bodies_on_demand; AM-4: query-time, outside build identity and the publication digest)",
    "global physical objects and contact identities, covered by reference (global, insert-only: the database refuses their update)",
    "sky events (global, enrichable; not consumed by the P1–P4 candidate verification path)",
    "created_at audit stamps (the claim is semantic candidate identity, not every possible byte difference)",
)


def is_governed(generation: str) -> bool:
    try:
        return int(str(generation).split(".", 1)[0]) >= 5
    except ValueError:
        return False


def _rows(conn, sql, params=()):
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(sql, params).fetchall()]


def coverage_identity(conn, chart_id: str, generation: str) -> dict:
    """The BUILD coverage partitions of the generation, every column but `created_at`, one canonical line per row."""
    h, n = hashlib.sha256(), 0
    for (line,) in _rows(
            conn, "SELECT j::text FROM (SELECT to_jsonb(c) - 'created_at' AS j FROM public.kala_gochara_coverage c"
                  " WHERE c.chart_id = %s AND c.generation = %s AND c.partition_kind = ANY(%s)) x ORDER BY j::text",
            (chart_id, generation, list(BUILD_COVERAGE_KINDS))):
        h.update(line.encode("utf-8"))
        h.update(b"\n")
        n += 1
    return {"kinds": list(BUILD_COVERAGE_KINDS), "rows": n, "sha256": h.hexdigest()}


def legacy_projection_counts(conn, chart_id: str, generation: str) -> dict[str, int]:
    """Rows of the legacy projection relations for the generation (0 when a relation does not exist)."""
    out = {}
    for t in LEGACY_PROJECTION_TABLES:
        if not _rows(conn, "SELECT to_regclass(%s) IS NOT NULL", (f"public.{t}",))[0][0]:
            out[t] = 0
            continue
        out[t] = _rows(conn, f"SELECT count(*) FROM public.{t} WHERE chart_id = %s AND generation = %s",
                       (chart_id, generation))[0][0]
    return out


def publication_content_digest(conn, chart_id: str, generation: str) -> str:
    """The `content_digest` that `ledger.publish` WILL store for this generation — the same function, so the approval binds it."""
    from .ledger import _canonical_row_set
    return _canonical_row_set(conn, chart_id, generation)


def boundary_statement() -> dict:
    return {"covered": ["governed output tables (every column but created_at)", "build coverage partitions",
                        "manifest identity incl. writer asset and ephemeris backend", "the publication content digest",
                        "attestations, runner/code identity, migration-ledger evidence",
                        "legacy projection relations: none may exist"],
            "not_covered": list(NOT_COVERED), "build_coverage_kinds": list(BUILD_COVERAGE_KINDS),
            "excluded_on_demand_kinds": list(EXCLUDED_ON_DEMAND_KINDS)}


__all__ = ["BUILD_COVERAGE_KINDS", "EXCLUDED_ON_DEMAND_KINDS", "LEGACY_PROJECTION_TABLES", "NOT_COVERED", "boundary_statement",
           "coverage_identity", "is_governed", "legacy_projection_counts", "publication_content_digest"]
