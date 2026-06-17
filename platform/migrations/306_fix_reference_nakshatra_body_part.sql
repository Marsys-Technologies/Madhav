-- Migration 306: REC-004 — Align reference_nakshatra.body_part with bg_nakshatra_medical
-- Authority: bg_nakshatra_medical uses the Ashtanga Hridayam / BPHS Kalanara sequential scheme
--   (Ashwini = feet/knees, Bharani = head, ... per BPHS §Nakshatra Kalanara + Ashtanga Hridayam)
-- reference_nakshatra.body_part was using the rashi-based Kalapurusha sign scheme
--   (Ashwini in Aries = head), which is a different tradition not used medically.
-- Resolution: update reference_nakshatra.body_part to match the Ashtanga Hridayam scheme
--   so both tables agree per nakshatra. Abhijit (nakshatra_id=28) stays NULL — no classical assignment.
-- L2 consumers: use bg_nakshatra_medical for medical body-part; reference_nakshatra.body_part
--   is now consistent with it. The rashi-based assignment was deprecated as non-canonical for this column.

UPDATE reference_nakshatra SET body_part = 'feet/knees'      WHERE nakshatra_id = 1;   -- Ashwini
UPDATE reference_nakshatra SET body_part = 'head'            WHERE nakshatra_id = 2;   -- Bharani
UPDATE reference_nakshatra SET body_part = 'eyes/face'       WHERE nakshatra_id = 3;   -- Krittika
UPDATE reference_nakshatra SET body_part = 'forehead/neck'   WHERE nakshatra_id = 4;   -- Rohini
UPDATE reference_nakshatra SET body_part = 'eyes/eyebrows'   WHERE nakshatra_id = 5;   -- Mrigashira
UPDATE reference_nakshatra SET body_part = 'eyes/mind'       WHERE nakshatra_id = 6;   -- Ardra
UPDATE reference_nakshatra SET body_part = 'ears/chest'      WHERE nakshatra_id = 7;   -- Punarvasu
UPDATE reference_nakshatra SET body_part = 'face/mouth'      WHERE nakshatra_id = 8;   -- Pushya
UPDATE reference_nakshatra SET body_part = 'ears/skin'       WHERE nakshatra_id = 9;   -- Ashlesha
UPDATE reference_nakshatra SET body_part = 'nose'            WHERE nakshatra_id = 10;  -- Magha
UPDATE reference_nakshatra SET body_part = 'right hand'      WHERE nakshatra_id = 11;  -- Purva Phalguni
UPDATE reference_nakshatra SET body_part = 'right side'      WHERE nakshatra_id = 12;  -- Uttara Phalguni
UPDATE reference_nakshatra SET body_part = 'fingers/hands'   WHERE nakshatra_id = 13;  -- Hasta
UPDATE reference_nakshatra SET body_part = 'forehead'        WHERE nakshatra_id = 14;  -- Chitra
UPDATE reference_nakshatra SET body_part = 'chest'           WHERE nakshatra_id = 15;  -- Swati
UPDATE reference_nakshatra SET body_part = 'arms'            WHERE nakshatra_id = 16;  -- Vishakha
UPDATE reference_nakshatra SET body_part = 'abdomen'         WHERE nakshatra_id = 17;  -- Anuradha
UPDATE reference_nakshatra SET body_part = 'right side body' WHERE nakshatra_id = 18;  -- Jyeshtha
UPDATE reference_nakshatra SET body_part = 'feet/hips'       WHERE nakshatra_id = 19;  -- Moola
UPDATE reference_nakshatra SET body_part = 'thighs'          WHERE nakshatra_id = 20;  -- Purva Ashadha
UPDATE reference_nakshatra SET body_part = 'thighs/knees'    WHERE nakshatra_id = 21;  -- Uttara Ashadha
UPDATE reference_nakshatra SET body_part = 'ears'            WHERE nakshatra_id = 22;  -- Shravana
UPDATE reference_nakshatra SET body_part = 'back/knees'      WHERE nakshatra_id = 23;  -- Dhanishtha
UPDATE reference_nakshatra SET body_part = 'right thigh'     WHERE nakshatra_id = 24;  -- Shatabhisha
UPDATE reference_nakshatra SET body_part = 'left side'       WHERE nakshatra_id = 25;  -- Purva Bhadrapada
UPDATE reference_nakshatra SET body_part = 'feet'            WHERE nakshatra_id = 26;  -- Uttara Bhadrapada
UPDATE reference_nakshatra SET body_part = 'feet/abdomen'    WHERE nakshatra_id = 27;  -- Revati
-- nakshatra_id=28 (Abhijit): no classical body-part assignment — remains NULL per brief floor rule

COMMENT ON COLUMN reference_nakshatra.body_part IS
'Body part per Ashtanga Hridayam / BPHS Kalanara sequential scheme (same as bg_nakshatra_medical).
 Abhijit (id=28) is NULL — no classical assignment. Source: Ashtanga Hridayam; BPHS §Nakshatra Kalanara.';
