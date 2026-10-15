\set QUIET on
\pset format csv
\pset csv_fieldsep '|'
\pset tuples_only on
\pset footer off
BEGIN READ ONLY;
SET LOCAL statement_timeout = '120s';
-- census label_distinct_sql for central_question_jsonb.$.note:
-- SELECT DISTINCT ("central_question_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("central_question_jsonb" IS NOT NULL AND jsonb_typeof("central_question_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'central_question_jsonb.$.note' AS entry, ("central_question_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("central_question_jsonb" IS NOT NULL AND jsonb_typeof("central_question_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- census label_distinct_sql for defining_threads_jsonb.$.note:
-- SELECT DISTINCT ("defining_threads_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("defining_threads_jsonb" IS NOT NULL AND jsonb_typeof("defining_threads_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'defining_threads_jsonb.$.note' AS entry, ("defining_threads_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("defining_threads_jsonb" IS NOT NULL AND jsonb_typeof("defining_threads_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- census label_distinct_sql for headline_jsonb.$.note:
-- SELECT DISTINCT ("headline_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("headline_jsonb" IS NOT NULL AND jsonb_typeof("headline_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'headline_jsonb.$.note' AS entry, ("headline_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("headline_jsonb" IS NOT NULL AND jsonb_typeof("headline_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- census label_distinct_sql for outliers_jsonb.$.note:
-- SELECT DISTINCT ("outliers_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("outliers_jsonb" IS NOT NULL AND jsonb_typeof("outliers_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'outliers_jsonb.$.note' AS entry, ("outliers_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("outliers_jsonb" IS NOT NULL AND jsonb_typeof("outliers_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- census label_distinct_sql for watch_list_jsonb.$.note:
-- SELECT DISTINCT ("watch_list_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("watch_list_jsonb" IS NOT NULL AND jsonb_typeof("watch_list_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'watch_list_jsonb.$.note' AS entry, ("watch_list_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("watch_list_jsonb" IS NOT NULL AND jsonb_typeof("watch_list_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- census label_distinct_sql for zoom_spine_jsonb.$.note:
-- SELECT DISTINCT ("zoom_spine_jsonb"::jsonb #>> '{note}') FROM bodha_chart_gestalt WHERE ("zoom_spine_jsonb" IS NOT NULL AND jsonb_typeof("zoom_spine_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) LIMIT 65
SELECT 'zoom_spine_jsonb.$.note' AS entry, ("zoom_spine_jsonb"::jsonb #>> '{note}') AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE ("zoom_spine_jsonb" IS NOT NULL AND jsonb_typeof("zoom_spine_jsonb"::jsonb #> '{note}') = 'string') AND (("chart_id" = '482012f1-710e-4a25-994a-93821f5871aa')) GROUP BY 1,2 ORDER BY 1,2;
-- rows of the chart in the table
SELECT 'rows' AS entry, count(*)::text AS stored, count(*) AS n FROM bodha_chart_gestalt WHERE "chart_id" = '482012f1-710e-4a25-994a-93821f5871aa';
ROLLBACK;
