#!/usr/bin/env bash
# irreplaceable_table_sets.sh — single source of truth for the two irreplaceable
# table sets the G1-E logical export covers.
#
# Sourced by export_irreplaceable_tables.sh and restore_irreplaceable_tables.sh.
# Do not hardcode this list a second time anywhere else — if the schema grows a
# new consent/ledger/conversation table, add it HERE so both the export and the
# DR runbook stay truthful (CLAUDE.md §N.7/§N.8: a claimed backup set with a
# stale table list is exactly the kind of "signal without a detector" this repo
# has been burned by before).
#
# Provenance of this list: platform/supabase/migrations/*.sql +
# platform/migrations/*.sql, cross-checked against the live-writer source
# (grep for INSERT INTO / DROP TABLE) as of 2026-08-19 — see
# 00_ARCHITECTURE/briefs/pariprashna_swarm/G1_E_DURABILITY_DR_RUNBOOK_v1_0.md §2
# for the full reasoning and the tables explicitly EXCLUDED (e.g.
# mcp_predictions — retired in migration 471_retire_mcp_predictions.sql; only
# the inert mcp_predictions_retired_backup remains and is not re-exported here).

# --- Set 1: CONVERSATIONS — the native's/cohort's actual dialogue. Human-authored
# content; nothing external can regenerate a lost turn. ---
CONVERSATIONS_TABLES=(
  conversations
  conversation_messages
  conversation_message_embeddings
  conversation_branches
  conversation_folders
  conversation_folder_members
  conversation_shares
  conversation_summaries
  project_conversations
)

# --- Set 2: LEDGER — consent/audit/prediction-outcome records of real-world
# events and decisions. Not derivable from ephemeris or classical texts; a loss
# here is a loss of history, not of a recomputation. ---
LEDGER_TABLES=(
  # Consent & subject-rights (G1-B, migration 575) — legal/consent state.
  chart_subject_consent
  chart_subject_consent_events
  chart_subject_exclusions
  chart_subject_deletion_disputes
  chart_subject_deletion_tombstones
  # Prediction / outcome / calibration ledger — empirical, accrues from lived
  # reality; this is the substrate the L5 Mimamsa calibration loop depends on.
  brahma_prospective_ledger
  mimamsa_predictions
  mimamsa_calibration
  mimamsa_calibration_snapshot
  mimamsa_intervention_ledger
  mimamsa_adjudication_log
  mcp_prediction_outcomes
  # Audit trail
  audit_log
  audit_events
  admin_audit_log
)

# Tables considered and deliberately left OUT of the irreplaceable sets, with
# why — see the runbook §2.3 for the full table-by-table rationale:
#   - mcp_predictions_retired_backup: dead historical backup of a retired
#     relay table (migration 471). Inert; not worth a recurring export slot.
#   - mimamsa_multipliers, mimamsa_pool_contributions, mimamsa_qa_eval,
#     mimamsa_snapshot_cosign, mimamsa_export_log: L5 structural/derived
#     outputs recomputable from the ledger tables above via a chart rebuild;
#     classified with the "layer tables" bucket (24h RPO/RTO), not here.
#   - chart_grants: access-control state, G1-C concern, not this lane's scope.
