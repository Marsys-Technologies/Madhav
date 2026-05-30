"""
Tool manifest for UTEE-S4 temporal event tools — for CAPABILITY_MANIFEST registration.
6 tools backed by vw_temporal_unified_lattice (META-ζ surface).
UTEE-S4 [BUILD-ORCH-STREAM-D-UTEE-S4]
Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §3.C
"""

TEMPORAL_EVENT_TOOLS = [
    {
        "tool_id": "query_temporal_events_in_range",
        "display_name": "Temporal Events in Date Range",
        "asset_id": "META-ζ",
        "description": (
            "Returns all temporal events (A15-A22) in a date range for a chart in "
            "unified UTEE shape. Use for 'what happens between dates X and Y?' queries. "
            "Covers time-synchronicity windows (A15), phase-locked anchors (A16), "
            "vedha obstructions (A18), Bhrigu Bindu transits (A19), "
            "Tajik varsha year-lords (A20), graha aspect exactitudes (A21), "
            "and per-year digest rows (A22)."
        ),
        "input_schema": {
            "chart_id": "UUID",
            "ayanamsha_id": "TEXT",
            "start_iso": "ISO8601",
            "end_iso": "ISO8601",
            "source_asset_filter": "TEXT?  -- one of A15/A16/A18/A19/A20/A21/A22",
            "severity_min": "FLOAT?  -- 0.0-1.0",
            "confidence_min": "FLOAT?  -- 0.0-1.0",
            "limit": "INT?  -- default 200",
        },
        "output_schema": "List[UTEE_envelope]",
        "channels": ["chat", "report", "visual", "dashboard"],
        "tiers": ["client", "acharya", "super_admin"],
    },
    {
        "tool_id": "query_temporal_events_next",
        "display_name": "Next Temporal Events",
        "asset_id": "META-ζ",
        "description": (
            "Returns the next N temporal events from a given date across all temporal "
            "sources (A15-A22) for a chart. Use for 'what are the next upcoming events?' "
            "queries, upcoming dasha changes, transit peaks, and convergence windows."
        ),
        "input_schema": {
            "chart_id": "UUID",
            "ayanamsha_id": "TEXT",
            "from_date": "ISO8601",
            "source_asset_filter": "TEXT?  -- one of A15/A16/A18/A19/A20/A21/A22",
            "limit": "INT?  -- default 10",
        },
        "output_schema": "List[UTEE_envelope]",
        "channels": ["chat", "dashboard"],
        "tiers": ["client", "acharya", "super_admin"],
    },
    {
        "tool_id": "query_temporal_events_within_a15_cluster",
        "display_name": "Events Within A15 Convergence Cluster",
        "asset_id": "META-ζ",
        "description": (
            "Returns all temporal events that belong to a specific A15 time-synchronicity "
            "convergence cluster. Use to explore the full event landscape within a known "
            "multi-system convergence window — surfaces anchors, transits, aspects, and "
            "vedha rows that co-occur in that cluster. Results ordered by severity."
        ),
        "input_schema": {
            "cluster_id": "UUID  -- A15 convergence cluster ID (inside_a15_cluster_ids_array key)",
            "limit": "INT?  -- default 100",
        },
        "output_schema": "List[UTEE_envelope]",
        "channels": ["chat", "report"],
        "tiers": ["acharya", "super_admin"],
    },
    {
        "tool_id": "query_temporal_events_seeded_by",
        "display_name": "Events Seeded By This Event",
        "asset_id": "META-ζ",
        "description": (
            "Returns A16 phase-locked anchors (and other events) seeded by a specific "
            "Bhrigu Bindu transit (A19) or Tajik varsha year-lord (A20). Use to trace "
            "causal chains: which anchors were crystallized by a given transit hit or "
            "year-lord activation? Results ordered chronologically."
        ),
        "input_schema": {
            "seed_event_id": "UUID  -- A19 transit_id or A20 varsha_id (as TEXT from source_row_id)",
            "limit": "INT?  -- default 50",
        },
        "output_schema": "List[UTEE_envelope]",
        "channels": ["chat", "report"],
        "tiers": ["acharya", "super_admin"],
    },
    {
        "tool_id": "query_temporal_events_mitigated_by",
        "display_name": "Events Mitigated By This Vedha",
        "asset_id": "META-ζ",
        "description": (
            "Returns A16 phase-locked anchors that are mitigated or modified by a specific "
            "A18 vedha obstruction. Use to identify which predicted anchors are softened, "
            "inverted, or cancelled by an active vedha. Results ordered by severity "
            "(highest-impact anchors first)."
        ),
        "input_schema": {
            "vedha_id": "UUID  -- A18 vedha_id (as TEXT from source_row_id)",
            "limit": "INT?  -- default 50",
        },
        "output_schema": "List[UTEE_envelope]",
        "channels": ["chat", "report"],
        "tiers": ["acharya", "super_admin"],
    },
    {
        "tool_id": "query_temporal_event_peers",
        "display_name": "Cross-Chart Temporal Event Peers",
        "asset_id": "META-ζ",
        "description": (
            "Returns similar temporal events from other charts (cross-chart cohort). "
            "Primary mode: embedding-vector cosine similarity via pgvector (requires "
            "temporal_event_embedding_vec to be populated by the UTEE backfill step). "
            "Fallback mode (when embedding is NULL): same source_asset + matching "
            "expected_outcome_class, ordered by severity proximity. "
            "Use for research comparisons and multi-chart pattern discovery."
        ),
        "input_schema": {
            "chart_id": "UUID",
            "ayanamsha_id": "TEXT",
            "source_asset": "TEXT  -- asset tag e.g. 'A19'",
            "source_row_id": "TEXT  -- PK of the reference event row",
            "top_k": "INT?  -- default 10",
        },
        "output_schema": "List[UTEE_envelope]  -- includes 'distance' field in embedding mode",
        "channels": ["report"],
        "tiers": ["acharya", "super_admin"],
    },
]
