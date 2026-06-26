-- Migration 354: mi_seva_abhilekha — service assets (preferences + journal)
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_preferences (
  user_id     text        NOT NULL,
  channel_id  text        NOT NULL,
  saved_state text        NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_preferences_user_id
  ON mimamsa_preferences (user_id);

CREATE TABLE IF NOT EXISTS mimamsa_journal (
  chart_id           uuid        NOT NULL,
  journal_id         text        NOT NULL,
  prediction_id      text        NOT NULL,
  prompt_shown       text        NOT NULL,
  native_answer      text,
  answered_at        timestamptz,
  resulting_event_id text,
  provenance_tag     text        NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, journal_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_journal_chart_id
  ON mimamsa_journal (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_journal_prediction
  ON mimamsa_journal (chart_id, prediction_id);

COMMIT;
