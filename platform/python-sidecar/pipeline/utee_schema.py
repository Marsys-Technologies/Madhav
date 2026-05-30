"""
UTEE (Unified Temporal Event Envelope) canonical column registry.
All temporal event tables must have these columns.
Used by migration validator and UTEE-S3 view builder.

Stream D — UTEE-S1 [BUILD-ORCH-STREAM-D-UTEE-S1]
Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C
"""

# Core UTEE columns shared by all 7 temporal event tables.
# Values are the expected SQL type string (informational; actual types are
# enforced by the DB migration, not here).
UTEE_COLUMNS: dict[str, str] = {
    # Core temporal window
    "event_iso": "TIMESTAMPTZ",
    "event_window_start_iso": "TIMESTAMPTZ",
    "event_window_end_iso": "TIMESTAMPTZ",
    # Severity
    "severity_normalized_0_1": "NUMERIC",
    "severity_decomposition_jsonb": "JSONB",
    # Confidence
    "confidence_normalized_0_1": "NUMERIC",
    "confidence_class": "TEXT",
    # Outcome ontology
    "expected_outcome_class": "TEXT",
    "outcome_ontology_class": "TEXT",
    "outcome_ontology_definition_jsonb": "JSONB",
    # Falsifiability
    "falsifiability_statement": "TEXT",
    "falsifier_date_iso": "TIMESTAMPTZ",
    # Cross-ayanamsha
    "cross_ayanamsha_stability_score": "NUMERIC",
    # Tradition variants
    "per_tradition_variant_jsonb": "JSONB",
    # Bridge FKs (common to all)
    "inside_a15_cluster_ids_array": "UUID[]",
    "associated_synchronicity_ids_array": "UUID[]",
    # Rendering
    "channel_render_priority_jsonb": "JSONB",
    # M6 calibration
    "m6_outcome_tracking_placeholder_jsonb": "JSONB",
}

# Canonical mapping from asset ID to table name.
UTEE_TABLES: dict[str, str] = {
    "A15": "l1_time_synchronicity",
    "A16": "l1_phase_locked_anchors",
    "A18": "l1_vedha_extended",
    "A19": "l1_bhrigu_bindu_transits",
    "A20": "l1_tajik_varsha_year_lords",
    "A21": "l1_graha_aspects_lifetime",
    "A22": "l1_varsha_digest",
}

# Per-table additional UTEE columns beyond the core set above.
# These are table-specific bridge arrays or embedding columns.
UTEE_EXTRA_COLUMNS: dict[str, list[str]] = {
    "l1_time_synchronicity": [
        "feeder_event_ids_array",
    ],
    "l1_phase_locked_anchors": [
        "mitigated_by_vedha_ids_array",
        "seeded_by_bhrigu_hit_ids_array",
        "varsha_year_lord_context_id",
        "feeder_event_kinds_array",
        "feeder_event_ids_array",
    ],
    "l1_vedha_extended": [
        "applicable_tradition_ids_array",
        "active_during_a15_cluster_ids_array",
        "mitigates_anchor_ids_array",
        "temporal_event_embedding_vec",
    ],
    "l1_bhrigu_bindu_transits": [
        "seeds_anchor_ids_array",
        "amplifies_event_ids_array",
        "temporal_event_embedding_vec",
    ],
    "l1_tajik_varsha_year_lords": [
        "seeds_anchor_ids_array",
        "amplifies_event_ids_array",
        "temporal_event_embedding_vec",
    ],
    "l1_graha_aspects_lifetime": [
        "seeds_anchor_ids_array",
        "temporal_event_embedding_vec",
    ],
    "l1_varsha_digest": [
        "seeds_anchor_ids_array",
        "amplifies_event_ids_array",
        "temporal_event_embedding_vec",
    ],
}


def all_columns_for_table(table_name: str) -> list[str]:
    """Return sorted list of all UTEE columns (core + extra) for a given table."""
    core = list(UTEE_COLUMNS.keys())
    extra = UTEE_EXTRA_COLUMNS.get(table_name, [])
    return sorted(set(core + extra))


def table_for_asset(asset_id: str) -> str:
    """Return the table name for a given asset ID (e.g. 'A15')."""
    if asset_id not in UTEE_TABLES:
        raise KeyError(f"Unknown UTEE asset id: {asset_id!r}. Valid: {list(UTEE_TABLES)}")
    return UTEE_TABLES[asset_id]
