"""Patches B and C for the L1 data-plane dasha lifecycle functions (migration 1035 lineage): pure text data, no database, no credential.

DRAFT, NEVER APPLIED. Approved as DESIGN by the owner via SS decision N-85 to travel in the SAME single D6 plan as option A (N-84) and F-A2. The combined
executor (d6_dataplane_capture_fa2_exec.py) imports this module; each hunk's old text must occur EXACTLY ONCE in the shipped live definition
(live_defs/<function>.LIVE.sql) and its new text must not already be present (d6_capture_patch_a.apply_hunks). The hunk lists were derived by
make_function_patch.py from the 19-lane rehearsal's patched function texts (rehearsal_inputs/), and a test proves they reproduce those texts byte for byte.

PATCH B  capture_l1_data_plane_dasha_partition(uuid,text,text,integer)
  The ga_dashas `vimshottari` substep has always written the `vimshottari_kp` rows too (1,080 per ayanamsha), inside the vimshottari partition. The
  function scoped the partition to `system_id = <partition system>` only, so completion failed with "dasha partition vimshottari:lahiri reported 10427 rows
  but active build scope has 9347". B introduces `v_systems`: for the partition system `vimshottari` it is {vimshottari, vimshottari_kp}, for any other system
  just that system, and the four places that scope by system (the active-row count, the two sides of the completed-generation replay comparison, and the
  snapshot INSERT) use `system_id = ANY(v_systems)`.

PATCH C  complete_l1_data_plane_partition(uuid,text,text,text,integer)
  The ga_dashas `__concurrency_post_pass__` partition also INSERTS rows (the scope-cap dasha row), which the completion's observed-row count did not see.
  C adds one block: for p_asset_id = 'ga_dashas' and that partition, the observed count also includes the dasha rows first seen in this partition (present in
  l1_data_plane_dasha_snapshots for this partition and in no other partition of the generation).
"""
from __future__ import annotations

PATCH_B_HUNKS = (
    ('B1_declare_v_systems',
     '  v_active_rows INTEGER;\nBEGIN\n',
     '  v_active_rows INTEGER;\n  v_systems TEXT[];\nBEGIN\n'),
    ('B2_v_systems_vimshottari_includes_vimshottari_kp',
     "    v_ayanamsha_id := split_part(p_partition_key, ':', 2);\n    IF v_system_id = '' OR v_ayanamsha_id = '' THEN\n",
     "    v_ayanamsha_id := split_part(p_partition_key, ':', 2);\n    v_systems := CASE WHEN v_system_id = 'vimshottari' THEN ARRAY['vimshottari','vimshottari_kp']::TEXT[] ELSE ARRAY[v_system_id]::TEXT[] END;\n    IF v_system_id = '' OR v_ayanamsha_id = '' THEN\n"),
    ('B3_active_rows_count_uses_v_systems',
     '      AND d.build_id::text = p_generation_id\n      AND d.system_id = v_system_id\n      AND d.ayanamsha_id = v_ayanamsha_id;\n',
     '      AND d.build_id::text = p_generation_id\n      AND d.system_id = ANY(v_systems)\n      AND d.ayanamsha_id = v_ayanamsha_id;\n'),
    ('B4_completed_replay_current_semantics_uses_v_systems',
     "          AND (p_partition_key = '__concurrency_post_pass__' OR (\n            d.system_id = v_system_id AND d.ayanamsha_id = v_ayanamsha_id\n          ))\n",
     "          AND (p_partition_key = '__concurrency_post_pass__' OR (\n            d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id\n          ))\n"),
    ('B5_completed_replay_previous_semantics_uses_v_systems',
     "            AND (p_partition_key = '__concurrency_post_pass__' OR (\n              (s.source_row).system_id = v_system_id\n              AND (s.source_row).ayanamsha_id = v_ayanamsha_id\n",
     "            AND (p_partition_key = '__concurrency_post_pass__' OR (\n              (s.source_row).system_id = ANY(v_systems)\n              AND (s.source_row).ayanamsha_id = v_ayanamsha_id\n"),
    ('B6_snapshot_insert_scope_uses_v_systems',
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\n      d.system_id = v_system_id AND d.ayanamsha_id = v_ayanamsha_id\n    ))\n",
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\n      d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id\n    ))\n"),
)

PATCH_C_HUNKS = (
    ('C1_post_pass_counts_dasha_rows_first_seen_in_this_partition',
     '    ) captured;\n  END IF;\n',
     "    ) captured;\n  END IF;\n  IF p_asset_id = 'ga_dashas' AND p_partition_key = '__concurrency_post_pass__' THEN\n    -- the post-pass partition also INSERTS rows (scope-cap dasha row); count dasha rows first seen in this partition\n    v_observed_rows := v_observed_rows + (\n      SELECT count(*) FROM (\n        SELECT DISTINCT (s.source_row).dasha_row_id\n        FROM public.l1_data_plane_dasha_snapshots s\n        WHERE s.chart_id = p_chart_id AND s.asset_id = p_asset_id\n          AND s.generation_id = p_generation_id AND s.partition_key = p_partition_key\n          AND NOT EXISTS (\n            SELECT 1 FROM public.l1_data_plane_dasha_snapshots t\n            WHERE t.chart_id = p_chart_id AND t.asset_id = p_asset_id\n              AND t.generation_id = p_generation_id AND t.partition_key <> p_partition_key\n              AND (t.source_row).dasha_row_id = (s.source_row).dasha_row_id)\n      ) fresh);\n  END IF;\n"),
)
