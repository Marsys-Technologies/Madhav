-- L2 W5 binding campaign-chart wrapper.
--
-- The unified campaign and frozen definition name one chart. The original
-- l2_w5_mechanical_checks.sql deliberately remains an unchanged all-chart
-- supplementary diagnostic. This wrapper shadows only its unqualified source
-- relations with read-only TEMP VIEWs for the campaign chart, then executes the
-- same eight assertions without rewriting or weakening them.
--
-- Run with psql from the repository root. A writable session is required for
-- TEMP DDL. The explicit transaction always ends in ROLLBACK; production data
-- is read but never persistently mutated.

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP VIEW bodha_anomalies AS
  SELECT * FROM public.bodha_anomalies
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW bodha_msr_signals AS
  SELECT * FROM public.bodha_msr_signals
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW bodha_rm_resonances AS
  SELECT * FROM public.bodha_rm_resonances
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW bodha_triangulation AS
  SELECT * FROM public.bodha_triangulation
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW bodha_grounding_matches AS
  SELECT * FROM public.bodha_grounding_matches
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW chart_facts AS
  SELECT * FROM public.chart_facts
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;
CREATE TEMP VIEW ga_yoga_firings AS
  SELECT * FROM public.ga_yoga_firings
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid;

\i 00_ARCHITECTURE/briefs/nirmana/sessions/l2_scripts/l2_w5_mechanical_checks.sql

ROLLBACK;
