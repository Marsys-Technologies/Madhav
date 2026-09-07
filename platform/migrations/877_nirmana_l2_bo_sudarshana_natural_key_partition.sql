-- 877_nirmana_l2_bo_sudarshana_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L2 (Bodha) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- bo_sudarshana is L2's frontier canary (its sole ancestor, ga_positions,
-- froze 2026-09-07T08:45:00Z, opening this asset's E-gate). `bodha_msr_signals`
-- is shared by seven active L2 writers (bo_laksana, bo_laksana_rerank,
-- bo_special_lagna, bo_sudarshana, bo_arudha, bo_nakshatra_semantic,
-- bo_vargottama_dhana) -- provenance.py's `has_cowriters` check is true for
-- all seven, so each needs its own `natural_key_partition` describing the
-- slice it actually owns, mirroring the ga_* precedent set by migrations
-- 868-874 (adjudication #2180): without it, DEP-ASSERT reads
-- `freshness_state='unknown'` (reason `partition_undeclared`) forever,
-- regardless of a successful build.
--
-- bo_sudarshana's own ownership, verified directly against
-- sudarshana_emitter.py's actual row-construction source (not assumed from
-- asset_registry's count_sql, which records what is SERVED/counted, not
-- necessarily the writer's own full claim): a single module-level constant
-- `SIGNAL_TYPE_CLASS = "sudarshana_agreement"` (line 47), consumed at
-- exactly one row-construction site, `build_signal_row` (line 199, dict key
-- at line 299). No other function in the file references `signal_type_class`
-- or constructs a `bodha_msr_signals` row. Confirmed no overlap: the value
-- is already visible as a distinct `signal_type_class` in the live table
-- (135 rows, canonical chart, from the prior pre-W3 build) with no other
-- co-writer using it.
--
-- Only bo_sudarshana is authored here -- it is the only one of the seven
-- co-writers whose own E-gate is open right now. The other six are left for
-- their own follow-up migrations when each reaches its own frontier, per
-- the ga_positions precedent's own stated reasoning (avoid collapsing
-- several writers' provenance into one rushed guess).

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class = sudarshana_agreement'
 WHERE asset_id = 'bo_sudarshana'
   AND natural_key_partition IS NULL;
