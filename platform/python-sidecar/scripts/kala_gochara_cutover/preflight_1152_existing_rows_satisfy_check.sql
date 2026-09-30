-- Preflight for migration 1152 (READ ONLY — run against production before
-- applying 1152; the A2.2 review requires proof that existing rows satisfy
-- the new CHECK before it is validated).
--
-- Must return 0 rows. Any row returned is an existing violation of the
-- anti-fabrication invariant exact_crossing = (t_exact IS NOT NULL) and the
-- migration must NOT be applied until the row is understood (fix the data,
-- not the detector — ADK-0026).

SELECT chart_id, generation, contact_id, exact_crossing, t_exact
FROM kala_gochara_contacts
WHERE exact_crossing <> (t_exact IS NOT NULL);
