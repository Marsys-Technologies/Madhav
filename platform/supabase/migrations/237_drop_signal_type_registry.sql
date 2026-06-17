-- 237_drop_signal_type_registry.sql
-- G52 signal_type_registry eliminated per native directive 2026-06-16.
-- The predicate-firing registry model is DROPPED entirely; bo_laksana uses the
-- projection model (ga_structural enumeration → signal_type_id derived from
-- fact_category, NOT looked up in a registry).
--
-- This migration is a safety net for any dev environment that applied migration
-- 226 before this elimination. On prod, migration 223 already retired the table
-- and migration 226 was never applied, so this is effectively a no-op on prod.
-- Migration 226's CREATE TABLE block for signal_type_registry has been removed
-- from that file (it was unapplied; the removal prevents re-creation on fresh
-- deployments).

DROP TABLE IF EXISTS signal_type_registry CASCADE;
