"""Jaimini chara-karaka role vocabulary — single source for the L1 writers.

ga_sensitive OWNS the karaka derivation (``karaka_chara_position``); ga_vargas
READS ga_sensitive's kn_rao assignments and never re-derives them (CLAUDE.md
N.5 — L1 is the authority; N.7 item 3 — no wrapper-local constant may shadow an
L1-computed value). This module holds the *vocabulary* both writers must agree
on (the school identifiers, the rank -> role-name lists, the alias fact_key) and
the ONE reader of ga_sensitive's stored kn_rao assignments that ga_vargas and
ga_dashas share (``fetch_kn_rao_karaka_rows`` + ``kn_rao_graha_by_rank``) with
its single exception class ``KarakaDependencyMissing``. It computes nothing:
every value it returns is a stored ga_sensitive row, or it raises.

Rulings (SS N-69, binding):
  * Headline school = ``kn_rao_rahu_included`` (8 grahas, Rahu reckoned by
    ``30 - (long % 30)``). ``parashari_rahu_excluded`` (7 grahas) stays the
    named variant.
  * 8-scheme role order (BPHS 32.13-17, sourced_ocr_unverified; J1 print-edition
    check pending) = Atma, Amatya, Bhratri, Matri, Pitri, Putra, Gnati, Dara.
  * 7-scheme role order is unchanged (the writer's pre-existing convention: no PITRIKARAKA
    subject; BPHS 32.13-17 note says one school treats Matru and Putra karaka as identical).
  * STRIKARAKA is a labelled ALIAS of the Darakaraka in the 8-scheme (same
    graha). It is emitted as an extra fact_key on the DARAKARAKA subject, never
    as a ninth subject row and never as a STRIKARAKA subject.

ORDERING DEPENDENCY (stated here because the code cannot enforce it): ga_vargas and
ga_dashas must be built AFTER ga_sensitive has been (re)built for the chart. The
ga_sensitive -> ga_vargas / ga_dashas DAG edges exist only in migration 1226, which is
HELD and is not part of the S-L1 integration branch; until it is applied nothing in the
orchestrator orders these assets. The reader therefore carries its own guard: it
refuses (``KarakaDependencyMissing``) unless the stored kn_rao subjects are EXACTLY
``KARAKA_ROLES_8``, so a stale pre-#2878 ga_sensitive generation (STRIKARAKA stored as
an eighth subject, no PITRIKARAKA) is refused rather than silently read.
"""
from __future__ import annotations

from typing import Any, Final, Iterable

KARAKA_SCHOOL_PARASHARI: Final[str] = "parashari_rahu_excluded"
KARAKA_SCHOOL_KN_RAO: Final[str] = "kn_rao_rahu_included"

# Rank (1-based) -> chart_facts.fact_subject for karaka_chara_position.
KARAKA_ROLES_7: Final[tuple[str, ...]] = (
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
    "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA",
)
KARAKA_ROLES_8: Final[tuple[str, ...]] = (
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
    "PITRIKARAKA", "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA",
)

KARAKA_ROLES_BY_SCHOOL: Final[dict[str, tuple[str, ...]]] = {
    KARAKA_SCHOOL_PARASHARI: KARAKA_ROLES_7,
    KARAKA_SCHOOL_KN_RAO: KARAKA_ROLES_8,
}

# STRIKARAKA alias (kn_rao school only): extra fact_key on the DARAKARAKA subject.
KARAKA_ALIAS_SUBJECT: Final[str] = "DARAKARAKA"
KARAKA_ALIAS_FACT_KEY: Final[str] = "strikaraka_alias"
KARAKA_ALIAS_LABEL: Final[str] = "STRIKARAKA"

# Short abbreviations used by ga_vargas (karaka_per_varga subjects), rank order
# of the 8-scheme.
KARAKA_ABBREVIATIONS_8: Final[tuple[str, ...]] = (
    "AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK",
)


# ── The shared reader of ga_sensitive's stored kn_rao assignments ─────────────
# (ga_vargas + ga_dashas). Consolidated from two near-identical loaders; the SQL, the
# pins and the refusal semantics are the ones both writers shipped with.


class KarakaDependencyMissing(RuntimeError):
    """ga_sensitive's kn_rao karaka_chara_position rows are absent or malformed for the
    (chart, ayanamsha) a consumer writer is building. Consumers never recompute karakas.

    ONE class: ga_vargas_writer and ga_dashas_writer both re-export it under this name,
    so ``pytest.raises(<writer>.KarakaDependencyMissing)`` keeps working for either."""


# Pinned on fact_category + fact_key (a closed pair) + the canonical school formula_id,
# with a TOTAL order (fact_subject, fact_key, fact_id: fact_id is the table's primary
# key, so no two rows tie). The order fixes which row a duplicate-refusal message names
# and keeps the pure core a function of the stored SET of rows (CLAUDE.md N.7 item 2).
KARAKA_ROWS_SQL: Final[str] = """
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s
              AND ayanamsha_id = %s
              AND fact_category = 'karaka_chara_position'
              AND fact_key IN ('assigned_graha', 'karaka_rank')
              AND formula_id = %s
            ORDER BY fact_subject, fact_key, fact_id
            """


def fetch_kn_rao_karaka_rows(conn: Any, chart_id: str, ayanamsha_id: str) -> list[tuple[Any, ...]]:
    """The stored (fact_subject, fact_key, fact_value_text, fact_value_num) rows of
    ga_sensitive's kn_rao assignments for one (chart, ayanamsha). Always opened with a
    tuple row factory, whatever the connection's default (the orchestrator's worker
    connections default to dict rows)."""
    import psycopg.rows as _pr

    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(KARAKA_ROWS_SQL, (chart_id, ayanamsha_id, KARAKA_SCHOOL_KN_RAO))
        return cur.fetchall()


def kn_rao_graha_by_rank(
    fetched: Iterable[tuple[Any, ...]],
    chart_id: str,
    ayanamsha_id: str,
    *,
    consumer: str,
    allowed_grahas: Iterable[str] | None = None,
) -> list[str]:
    """Pure core: stored rows -> the graha holding each karaka rank, as a list indexed by
    ``rank - 1`` (rank order = ``KARAKA_ABBREVIATIONS_8`` = ``KARAKA_ROLES_8``).

    Refuses (``KarakaDependencyMissing``, never a default, never a partial map) when: there
    are no rows; an ``assigned_graha`` / ``karaka_rank`` row for a subject is duplicated or
    NULL; the assigned_graha subjects differ from the karaka_rank subjects; the ranks are
    not a permutation of 1..8; the subjects are not exactly ``KARAKA_ROLES_8`` (a pre-#2878
    ga_sensitive generation: STRIKARAKA subject, no PITRIKARAKA); the eight grahas are not
    distinct (or, when ``allowed_grahas`` is given, are not all drawn from it). ``consumer`` ("ga_vargas" /
    "ga_dashas") only names the refusing writer in the message."""
    n_roles = len(KARAKA_ABBREVIATIONS_8)
    where = (
        f"chart_id={chart_id} ayanamsha={ayanamsha_id} "
        f"(ga_sensitive karaka_chara_position, formula_id={KARAKA_SCHOOL_KN_RAO})"
    )
    fetched = list(fetched)
    if not fetched:
        raise KarakaDependencyMissing(
            f"[{consumer}] ga_sensitive dependency missing: no kn_rao karaka_chara_position "
            f"rows for {where}. Build ga_sensitive for this chart first; {consumer} does not "
            f"recompute karakas."
        )
    graha_by_subject: dict[str, str] = {}
    rank_by_subject: dict[str, int] = {}
    for subject, key, text, num in fetched:
        if key == "assigned_graha":
            bucket, value = graha_by_subject, text
        else:  # karaka_rank
            bucket, value = rank_by_subject, (int(num) if num is not None else None)
        if value is None or subject in bucket:
            raise KarakaDependencyMissing(
                f"[{consumer}] malformed ga_sensitive karaka rows ({key} for subject {subject!r} "
                f"is {'duplicated' if value is not None else 'NULL'}) for {where}."
            )
        bucket[subject] = value
    if set(graha_by_subject) != set(rank_by_subject):
        raise KarakaDependencyMissing(
            f"[{consumer}] malformed ga_sensitive karaka rows: assigned_graha subjects "
            f"{sorted(graha_by_subject)} != karaka_rank subjects {sorted(rank_by_subject)} "
            f"for {where}."
        )
    ranks = sorted(rank_by_subject.values())
    if ranks != list(range(1, n_roles + 1)):
        raise KarakaDependencyMissing(
            f"[{consumer}] ga_sensitive kn_rao karaka ranks {ranks} are not a "
            f"1..{n_roles} permutation for {where}."
        )
    expected_subjects = set(KARAKA_ROLES_8)
    if set(graha_by_subject) != expected_subjects:
        raise KarakaDependencyMissing(
            f"[{consumer}] ga_sensitive kn_rao karaka subjects {sorted(graha_by_subject)} are not the "
            f"expected {sorted(expected_subjects)} (missing {sorted(expected_subjects - set(graha_by_subject))}, "
            f"unexpected {sorted(set(graha_by_subject) - expected_subjects)}) for {where}: a stale "
            f"pre-#2878 ga_sensitive generation (STRIKARAKA as an 8th subject, no PITRIKARAKA)? "
            f"Rebuild ga_sensitive for this chart first; {consumer} must be built after ga_sensitive."
        )
    by_rank = {rank: graha_by_subject[subject] for subject, rank in rank_by_subject.items()}
    grahas = [by_rank[rank] for rank in range(1, n_roles + 1)]
    allowed = None if allowed_grahas is None else list(allowed_grahas)
    if len(set(grahas)) != n_roles or (allowed is not None and not set(grahas) <= set(allowed)):
        raise KarakaDependencyMissing(
            f"[{consumer}] ga_sensitive kn_rao karaka assignments {sorted(set(grahas))} are not "
            f"{n_roles} distinct grahas"
            + (f" drawn from {allowed}" if allowed is not None else "")
            + f" for {where}."
        )
    return grahas


# The grahas a stored karaka assignment may name: the seven classical grahas plus Rahu (the 8-scheme's
# Rahu-included reckoning). Shared by every consumer of the stored ga_sensitive assignments so they cannot
# drift: ga_dashas passes its own `_KARAKAS_ACTIVE_GRAHA_ORDER` (same eight grahas; a test pins the equality),
# ga_vargas passes this (TI-ga-vargas-karaka-residual-001, D4: ga_vargas used to accept any stored graha text).
KARAKA_ALLOWED_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Mars", "Mercury", "Saturn", "Jupiter", "Venus", "Moon", "Rahu",
)
