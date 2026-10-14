"""The node-series content digest — the fingerprint's `node_series` component (step 3 §4).

A separate module from `services.w2g.node_series` ON PURPOSE: that module sits in the
import closure of the L0 writer `bg_gochara_arcs` (and of ka_gochara's readers), so any
edit to it moves their writer-source digests and forces an L0 pins re-admission. The
overlay writers and the freshness gate import THIS module instead, keeping the digest
surface of step 3 §4 to exactly the two writers whose fingerprints change.

Suvarṇa decision 2026-10-02, node_series_digest_v1: the definition is OWNED BY L0 —
version 1; any change is a v2, never an edit. Copied VERBATIM from the steward's C20
ruling (M20261002T074246-1b3a; step-3 spec §4.2), with the psql bind :'node_mode'
replaced by one %s parameter and nothing else — the label string, column order,
rounding, COLLATE "C" and ORDER BY are exactly hers. A test pins this constant's
sha256 so an accidental edit fails. Semantics: bind 'true' or 'mean';
node_series_digest is NULL when the series is empty (node_series_identity RAISES
then — no silent default).
"""
from __future__ import annotations

from typing import Any

import psycopg.rows

from services.w2g.node_series import SERIES_NODE_MODE, NodeSeriesError

__all__ = ["NODE_SERIES_DIGEST_V1_SQL", "node_series_identity"]

NODE_SERIES_DIGEST_V1_SQL = (
    r"""SELECT count(*) AS n_rows, encode(sha256(convert_to('node_series_digest_v1' || E'\n' || string_agg(concat_ws('|', ayanamsha_id, body, to_char(date,'YYYY-MM-DD'), node_mode, round(tropical_longitude,9)::text, round(speed_dps,9)::text, CASE WHEN is_retrograde THEN '1' ELSE '0' END), E'\n' ORDER BY ayanamsha_id COLLATE "C", body COLLATE "C", date),'UTF8')),'hex') AS node_series_digest FROM public.ephemeris_daily WHERE node_mode = %s AND body IN ('Rahu','Ketu');"""
)


def node_series_identity(conn: Any, mode: str | None = None) -> dict:
    """The fingerprint's `node_series` component: {"mode", "n_rows", "digest"}
    for the pinned series, the digest computed by the L0-owned
    node_series_digest_v1 SQL above (one SQL, one place).

    RAISES NodeSeriesError on a NULL digest (an empty series — never a silent
    default) and on the table being absent. `mode` defaults to the pinned
    SERIES_NODE_MODE; binding 'true' or 'mean' selects the series.
    """
    mode = mode or SERIES_NODE_MODE
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(NODE_SERIES_DIGEST_V1_SQL, (mode,))
            row = cur.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise NodeSeriesError(
            "ephemeris_daily does not exist — the node series is absent; "
            "refusing to fingerprint an absent series"
        ) from exc
    digest = row["node_series_digest"] if row else None
    if digest is None:
        raise NodeSeriesError(
            f"node series empty for node_mode='{mode}' — node_series_digest_v1 "
            "returned a NULL digest; refusing to fingerprint an absent series"
        )
    return {"mode": mode, "n_rows": int(row["n_rows"]), "digest": digest}
