"""Deterministic L1 row ids (N-143 option A): one shared helper, one namespace.

A row id that is random per build orphans every downstream citation of it the next
time the owning writer rebuilds (L2 constituent ids, Gochara ``consumed_dasha_row_ids``).
Both L1 surrogate-id tables that L2/L3 cite are therefore keyed by NATURAL KEY ONLY:

* ``chart_divisionals.id`` -- UUID5 over the table's own unique key
  ``chart_divisionals_unique_idx`` (chart_id, graha, ayanamsha_id, varga,
  fact_category, fact_key, fact_subject), declared NULLS NOT DISTINCT.
* ``chart_dashas.dasha_row_id`` -- already UUID5 since S-L1 (#2984): the writer's
  ``stabilize_hierarchical_uuids`` post-pass (kind ``dasha_interval``, parent id chained
  parent-before-child, no build_id, no verification tier). This module exposes the
  identity-field tuple as ONE constant so the writer-independent tests and the offline
  production replay use exactly the production derivation.

Namespace: the L1 namespace of ``data_plane_contracts.stable_uuid`` (UUID5 over
canonical JSON of ``[kind, *parts]``). NULL parts stay JSON ``null`` (distinct from
``""``), which matches ``NULLS NOT DISTINCT`` -- the DB treats NULL and '' as different
keys for divisionals, so folding NULL to '' there would manufacture a collision the
database does not have. (For chart_dashas the unique index uses COALESCE(kp_sublevel,'')
so NULL and '' are the same key there; the writer only ever emits NULL.)

Never add ``build_id``, ``verification_pass_status`` or any value column to an identity.
"""
from __future__ import annotations

from typing import Any, Mapping

from ga_writers.data_plane_contracts import stable_uuid

DIVISIONAL_ID_KIND = "chart_divisional"
DIVISIONAL_KEY_COLUMNS = (
    "chart_id", "graha", "ayanamsha_id", "varga",
    "fact_category", "fact_key", "fact_subject",
)

DASHA_ID_KIND = "dasha_interval"
DASHA_IDENTITY_FIELDS = (
    "chart_id", "ayanamsha_id", "system_id", "level_n",
    "lord_graha", "start_iso", "end_iso", "kp_sublevel",
    "kp_sub_lord", "kp_sub_sub_lord",
)


def divisional_row_id(
    chart_id: Any, graha: Any, ayanamsha_id: Any, varga: Any,
    fact_category: Any, fact_key: Any, fact_subject: Any,
) -> str:
    """UUID5 of one chart_divisionals natural key. Build/tier independent."""
    return stable_uuid(
        DIVISIONAL_ID_KIND,
        str(chart_id) if chart_id is not None else None,
        graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject,
    )


def divisional_row_id_for(row: Mapping[str, Any]) -> str:
    """Same id from a writer row dict (keys = DIVISIONAL_KEY_COLUMNS)."""
    return divisional_row_id(*(row.get(c) for c in DIVISIONAL_KEY_COLUMNS))


def assign_divisional_row_ids(rows: list[dict]) -> list[dict]:
    """Stamp ``row['id']`` on every row (in place) and return the list."""
    for row in rows:
        row["id"] = divisional_row_id_for(row)
    return rows
