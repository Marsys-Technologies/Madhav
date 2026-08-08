"""
services/ka_kshetra/cohort_client.py — Lane D's rarity/cohort interface.

KALA_W2_FIELD_DESIGN_v1_0.md §6.3 (item 15 "Rarity axis from cohort"),
CORRECTED 2026-07-30 (ADJUDICATION-1, ANTARYĀMIN) against the REAL schema —
this module reads that corrected section, not the section's original
(fictional) three-table draft. The real substrate is TWO tables:

  bg_synthetic_cohort     (migration 472) — one row per synthetic chart,
                          `positions` JSONB blob, N=10,000, no cohort_id/
                          cohort_version column (a single global cohort).
  bg_synthetic_cohort_md  (migration 484) — age-interval Vimśottarī MD-lord
                          CHAIN, ~10 rows per chart, joined by synthetic_id.

ONE function is exposed: `cohort_base_rate()`. Everything else in this module
is a private implementation detail of that one call.

Binding behaviour rules (§6.3, verbatim in substance):
  1. matched_by=None -> the GLOBAL rate: one aggregate scan of
     bg_synthetic_cohort using the whitelisted containment predicate.
     matched=False, fallback_reason=None. Honest-null rows for the keyed
     graha are excluded from the denominator and reported in
     n_excluded_honest_null.
  2. matched_by given -> filtered by the containment predicate for every
     non-md_lord key, joined to bg_synthetic_cohort_md on synthetic_id with
     the half-open age-interval predicate for md_lord. If the matched
     denominator n_total < 200, FALL BACK to the global rate: matched=False,
     fallback_reason='matched_subcohort_too_small (n=<n>)'.
  3. feature_key not in the closed whitelist -> p=None,
     fallback_reason='feature_not_in_cohort'.
  4. Minimum viable cohort: n_total >= 10_000 (the GLOBAL
     `SELECT count(*) FROM bg_synthetic_cohort`, never the matched
     denominator). Below it, EVERY call returns p=None,
     fallback_reason='cohort_below_minimum (n=<n>)'.
  5. cohort_version (a content fingerprint, since there is no cohort_version
     column) is pinned into the field hash (§7.4) by the caller; this module
     only computes and reports it.

Three additional fallback reasons the real schema adds (each an honest null,
never a substituted default): `md_chain_not_built`,
`md_match_requires_reference_age`, `cohort_heterogeneous`.

Closed whitelist, closed on purpose (§6.3): `feature_key` arrives as a raw
string from a caller. An open path-builder over that string would be a SQL-
injection surface, so every accepted key is resolved through
`_resolve_feature()` against a fixed map before it ever reaches a query —
anything else returns `feature_not_in_cohort` rather than building a query
from an unrecognised string.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import psycopg2.extras

from brahmagyan.graha_vocabulary import to_title

# ── The closed whitelist (§6.3's table) ──────────────────────────────────────

# The ten stored `positions` keys, lower-case caller spelling -> stored
# capitalization (`bg_synthetic_cohort.positions` is case-sensitive per the
# design doc: "Sun, Moon, ..., Lagna").
# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets).
_GRAHA_CAP: dict[str, str] = {
    name: to_title(name)
    for name in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu", "lagna")
}

# suffix -> (json_field, value_kind). value_kind governs casting of the
# caller-supplied feature_value into the two forms the query needs: a
# JSON-typed literal for `@>` containment and a text literal for `->>`
# extraction (the "typing trap" §6.3 calls out by name).
_SUFFIX_FIELD: dict[str, tuple[str, str]] = {
    "_sign": ("sign_id", "int"),
    "_nakshatra": ("nakshatra_id", "int"),
    "_pada": ("nakshatra_pada", "int"),
    "_retrograde": ("is_retrograde", "bool"),
}

MIN_VIABLE_COHORT_N = 10_000
MIN_MATCHED_SUBCOHORT_N = 200

_MD_LORDS = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
})

_DAYS_PER_JULIAN_YEAR = 365.2425  # matches dashas.py's own last-row fallback (§6.3)


@dataclass(frozen=True)
class CohortRate:
    """The one return type of `cohort_base_rate()`. See module docstring."""

    p: float | None          # base rate in [0,1]; None => not computable, see fallback_reason
    n: int                   # matching charts (numerator)
    n_total: int             # denominator actually used
    cohort_version: str      # content fingerprint (§6.3) -- not a column; pinned into §7.4
    matched: bool            # True => the matched sub-cohort (E7.3) was actually used
    fallback_reason: str | None
    n_excluded_honest_null: int = 0   # rows whose keyed graha object is JSON null
    feature_expr: str | None = None   # the resolved JSONB path -- auditability, served with the row


def _resolve_feature(feature_key: str) -> tuple[str, str, str] | None:
    """
    Resolve `feature_key` against the closed whitelist.

    Returns (graha_cap, json_field, value_kind) or None if `feature_key` is
    not in the whitelist. `lagna_sign` / `lagna_nakshatra` / `moon_nakshatra`
    are not special-cased: they fall out of the same general
    `<graha><suffix>` pattern applied to `lagna` and `moon` like any other
    graha (the design doc's table lists them as worked examples of the
    general rule, not as a separate rule).
    """
    for lower, cap in _GRAHA_CAP.items():
        if not feature_key.startswith(lower):
            continue
        suffix = feature_key[len(lower):]
        field_kind = _SUFFIX_FIELD.get(suffix)
        if field_kind is not None:
            return (cap, field_kind[0], field_kind[1])
    return None


def _cast_value(value: str | int | bool, value_kind: str) -> tuple[Any, str]:
    """Return (json_value, text_value) for containment vs extraction forms."""
    if value_kind == "bool":
        b = value if isinstance(value, bool) else str(value).strip().lower() in ("true", "1", "t")
        return (b, "true" if b else "false")
    # int (sign_id / nakshatra_id / nakshatra_pada)
    i = int(value)
    return (i, str(i))


@dataclass(frozen=True)
class _CohortMeta:
    n_total: int
    n_sampling_methods: int
    sampling_method: str | None
    ayanamsha_key: str | None
    positions_digest: str | None
    md_rows: int
    chain_version: str | None
    n_chain_versions: int
    cohort_version: str


def _compute_cohort_meta(conn: Any) -> _CohortMeta:
    """
    The content-fingerprint query pair from §6.3 ("what identifies a cohort
    version now"). Run once per caller/build and memoized by the caller if
    it calls `cohort_base_rate` many times in one build (this module does not
    cache internally -- memoization is the field-build's job, not a hidden
    global here).
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT count(*)                        AS n_total,
                   count(DISTINCT sampling_method)  AS n_sampling_methods,
                   min(sampling_method)             AS sampling_method,
                   min(ayanamsha_key)                AS ayanamsha_key,
                   md5(string_agg(synthetic_id::text || ':' || positions::text, ','
                                  ORDER BY synthetic_id)) AS positions_digest
            FROM   bg_synthetic_cohort
            """
        )
        row = cur.fetchone()
        cur.execute(
            """
            SELECT count(*) AS md_rows, min(chain_version) AS chain_version,
                   count(DISTINCT chain_version) AS n_chain_versions
            FROM   bg_synthetic_cohort_md
            """
        )
        row2 = cur.fetchone()

    payload = {
        "n_total": row["n_total"],
        "sampling_method": row["sampling_method"],
        "ayanamsha_key": row["ayanamsha_key"],
        "positions_digest": row["positions_digest"],
        "md_rows": row2["md_rows"],
        "chain_version": row2["chain_version"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return _CohortMeta(
        n_total=row["n_total"],
        n_sampling_methods=row["n_sampling_methods"],
        sampling_method=row["sampling_method"],
        ayanamsha_key=row["ayanamsha_key"],
        positions_digest=row["positions_digest"],
        md_rows=row2["md_rows"],
        chain_version=row2["chain_version"],
        n_chain_versions=row2["n_chain_versions"],
        cohort_version=f"bgc_{digest}",
    )


def _null_safety_clause(grahas: set[str], alias: str = "c") -> list[str]:
    """One `jsonb_typeof(...) = 'object'` clause per referenced graha object.

    §6.3's honest-null exclusion, applied to EVERY graha referenced by the
    query (the queried feature's own graha AND any graha named in
    matched_by) -- a failed Ascendant (or any graha object) is `unknown`,
    never `different` (§N.7 item 6), so a row with a null object for any
    referenced graha is excluded from the denominator entirely rather than
    scored as a non-match.
    """
    return [f"jsonb_typeof({alias}.positions -> '{g}') = 'object'" for g in sorted(grahas)]


def _run_count(conn: Any, sql: str, params: dict[str, Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def cohort_base_rate(
    feature_key: str,
    feature_value: str | int | bool,
    matched_by: dict[str, str | int] | None = None,
    native_age_at_reference_years: float | None = None,
    conn: Any = None,
) -> CohortRate:
    """
    The ONE function Lane D calls (§6.3). See module docstring for the five
    binding behaviour rules this implements.
    """
    if conn is None:
        raise ValueError("cohort_base_rate() requires a live conn -- never mocked (§ campaign rail)")

    meta = _compute_cohort_meta(conn)

    # ── universal gate 1: cohort heterogeneity (§6.3, "every call") ─────────
    if meta.n_sampling_methods > 1 or meta.n_chain_versions > 1:
        return CohortRate(
            p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
            matched=False, fallback_reason="cohort_heterogeneous",
        )

    # ── universal gate 2: minimum viable cohort (§6.3 rule 4, "every call") ─
    if meta.n_total < MIN_VIABLE_COHORT_N:
        return CohortRate(
            p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
            matched=False, fallback_reason=f"cohort_below_minimum (n={meta.n_total})",
        )

    # ── feature_key whitelist resolution (§6.3 rule 3) ──────────────────────
    resolved = _resolve_feature(feature_key)
    if resolved is None:
        return CohortRate(
            p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
            matched=False, fallback_reason="feature_not_in_cohort",
        )
    graha_cap, json_field, value_kind = resolved
    json_value, text_value = _cast_value(feature_value, value_kind)
    feature_expr = f"positions->'{graha_cap}'->>'{json_field}'"
    feature_json = {graha_cap: {json_field: json_value}}

    # ── matched_by validation (md_lord requires a reference age; requires
    #    the MD chain to actually be built) — §6.3 rule 2 / added fallbacks ──
    md_lord: str | None = None
    non_md_matched: dict[str, str | int] = {}
    if matched_by:
        for key, val in matched_by.items():
            if key == "md_lord":
                md_lord = str(val)
            else:
                non_md_matched[key] = val

    if md_lord is not None and native_age_at_reference_years is None:
        return CohortRate(
            p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
            matched=False, fallback_reason="md_match_requires_reference_age",
            feature_expr=feature_expr,
        )
    if md_lord is not None and meta.md_rows == 0:
        return CohortRate(
            p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
            matched=False, fallback_reason="md_chain_not_built",
            feature_expr=feature_expr,
        )

    # Resolve every non-md matched_by key into a merged-by-graha containment
    # object (§6.3: "the non-md matched_by keys, as ONE object").
    match_json: dict[str, dict[str, Any]] = {}
    referenced_grahas: set[str] = {graha_cap}
    for key, val in non_md_matched.items():
        r = _resolve_feature(key)
        if r is None:
            # A caller-supplied matched_by key outside the whitelist is the
            # same "not extractable" situation as the primary feature_key.
            return CohortRate(
                p=None, n=0, n_total=meta.n_total, cohort_version=meta.cohort_version,
                matched=False, fallback_reason="feature_not_in_cohort",
                feature_expr=feature_expr,
            )
        m_graha, m_field, m_kind = r
        m_json_value, _ = _cast_value(val, m_kind)
        match_json.setdefault(m_graha, {})[m_field] = m_json_value
        referenced_grahas.add(m_graha)

    null_clause = _null_safety_clause(referenced_grahas)

    if not matched_by:
        # ── rule 1: the global rate ─────────────────────────────────────────
        where = null_clause[:]
        params: dict[str, Any] = {}
        denom_sql = f"SELECT count(*) FROM bg_synthetic_cohort c WHERE {' AND '.join(where)}"
        n_total_used = _run_count(conn, denom_sql, params)

        where_num = where + ["c.positions @> %(feature_json)s::jsonb"]
        params_num = {"feature_json": json.dumps(feature_json)}
        num_sql = f"SELECT count(*) FROM bg_synthetic_cohort c WHERE {' AND '.join(where_num)}"
        n = _run_count(conn, num_sql, params_num)

        n_excluded = meta.n_total - n_total_used
        p = (n / n_total_used) if n_total_used > 0 else None
        return CohortRate(
            p=p, n=n, n_total=n_total_used, cohort_version=meta.cohort_version,
            matched=False, fallback_reason=None,
            n_excluded_honest_null=n_excluded, feature_expr=feature_expr,
        )

    # ── rule 2: matched sub-cohort ───────────────────────────────────────────
    joins = ""
    where = null_clause[:]
    params = {}
    if md_lord is not None:
        joins = "JOIN bg_synthetic_cohort_md m ON m.synthetic_id = c.synthetic_id"
        where += ["m.md_lord = %(md_lord)s", "%(ref_age)s >= m.start_age_years", "%(ref_age)s < m.end_age_years"]
        params["md_lord"] = md_lord
        params["ref_age"] = native_age_at_reference_years
    if match_json:
        where.append("c.positions @> %(match_json)s::jsonb")
        params["match_json"] = json.dumps(match_json)

    denom_sql = f"SELECT count(*) FROM bg_synthetic_cohort c {joins} WHERE {' AND '.join(where)}"
    matched_n_total = _run_count(conn, denom_sql, params)

    if matched_n_total < MIN_MATCHED_SUBCOHORT_N:
        fallback = cohort_base_rate(
            feature_key, feature_value, matched_by=None,
            native_age_at_reference_years=None, conn=conn,
        )
        return CohortRate(
            p=fallback.p, n=fallback.n, n_total=fallback.n_total,
            cohort_version=fallback.cohort_version, matched=False,
            fallback_reason=f"matched_subcohort_too_small (n={matched_n_total})",
            n_excluded_honest_null=fallback.n_excluded_honest_null,
            feature_expr=feature_expr,
        )

    where_num = where + ["c.positions @> %(feature_json)s::jsonb"]
    params_num = dict(params)
    params_num["feature_json"] = json.dumps(feature_json)
    num_sql = f"SELECT count(*) FROM bg_synthetic_cohort c {joins} WHERE {' AND '.join(where_num)}"
    n = _run_count(conn, num_sql, params_num)

    n_excluded = meta.n_total - matched_n_total  # approximate: rows outside the matched population
    p = (n / matched_n_total) if matched_n_total > 0 else None
    return CohortRate(
        p=p, n=n, n_total=matched_n_total, cohort_version=meta.cohort_version,
        matched=True, fallback_reason=None,
        n_excluded_honest_null=n_excluded, feature_expr=feature_expr,
    )
