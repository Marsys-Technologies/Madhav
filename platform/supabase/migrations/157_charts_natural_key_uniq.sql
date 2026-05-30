-- 157_charts_natural_key_uniq.sql
-- Enforce natural-key uniqueness on charts: same owner cannot create two charts
-- with the same name + birth_date + birth_time + lat/lng (4dp ~= 11m precision).
-- Run AFTER dedupe_charts.ts has cleaned existing duplicates, or the index
-- creation will fail with a uniqueness violation.

BEGIN;

-- Defensive: confirm no duplicates remain before adding the constraint.
DO $$
DECLARE dup_count int;
BEGIN
  SELECT COUNT(*) INTO dup_count
  FROM (
    SELECT 1
    FROM charts
    GROUP BY owner_id, lower(trim(name)), birth_date, birth_time,
             ROUND(birth_lat::numeric, 4), ROUND(birth_lng::numeric, 4)
    HAVING COUNT(*) > 1
  ) d;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'Cannot add unique index: % duplicate natural-key groups remain. Run dedupe_charts.ts first.', dup_count;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS charts_natural_key_uniq
ON charts (
  owner_id,
  lower(trim(name)),
  birth_date,
  birth_time,
  ROUND(birth_lat::numeric, 4),
  ROUND(birth_lng::numeric, 4)
);

COMMENT ON INDEX charts_natural_key_uniq IS
  'Prevents duplicate chart creation per owner. Lat/lng rounded to 4dp (~11m) to absorb float noise.';

COMMIT;
