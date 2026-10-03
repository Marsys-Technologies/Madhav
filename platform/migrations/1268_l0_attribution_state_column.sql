-- 1268_l0_attribution_state_column.sql
--
-- Suvarna Track I, item TI-L0-09 (finding CF-11, SS ruling Q3 of 2026-10-01; number 1268 allocated by SS):
-- "classical_tradition is not provenance" - an explicit, machine-readable attribution state on the four L0
-- catalogues whose citation column carries a placeholder or a refuted citation.
--
--   * ADDS  attribution_state text  (nullable, CHECK IN ('sourced','unsourced','refuted')) to
--       brahma_dosha_catalog   (asset bg_doshas)
--       brahma_yoga_catalog    (asset bg_yogas)
--       brahma_remedy_corpus   (asset bg_remedies)
--       bg_transit_rules       (asset bg_transit_rules)
--   * BACKFILLS only the two states that are token-exact on the stored citation, nothing else:
--       'unsourced'  brahma_dosha_catalog.classical_citations = [{"text_id": "classical_tradition"}]   53 rows
--                    brahma_yoga_catalog  .classical_citations = [{"text_id": "classical_tradition"}]    1 row  (kala_sarpa_yoga)
--                    brahma_remedy_corpus .source_citation     = 'classical tradition (Jyotish)'       101 rows
--                    bg_transit_rules     .classical_citation LIKE 'UNSOURCED %'                         6 rows (node vedha)
--       'refuted'    bg_transit_rules     .classical_citation LIKE 'BPHS Ch.29 (Gochara Phala%'         19 rows
--   * NO CITATION IS CHANGED OR REPLACED (B.10: re-sourcing the 19 refuted rows is the separate research item
--     TI-L0-10), and NO ROW IS EVER MARKED 'sourced' BY THIS FILE (see below).
--
-- CONCERN
--   B.3: no claim rests on "per tradition" without a source. The census reads Ldgr.source_presence PASS on these
--   assets because the citation column is POPULATED (presence, not qualification). Placeholders therefore pass
--   as provenance. SS Q3: "classical_tradition is NOT accepted as provenance: give it an explicit attribution
--   state sourced | unsourced | refuted; neither unsourced nor refuted is a PASS; the 19 refuted BPHS Ch.29 transit
--   citations are marked refuted." CF-11 designs the state as derived by the writer; this migration is the
--   COLUMN half (DDL) plus a mechanical backfill of the token-exact states so the state exists now, before any
--   writer change or rebuild.
--
-- WHAT 'NULL' MEANS (honest null beats an invented judgment, N.7 item 6)
--   NULL = not classified. This file cannot verify that any citation is a real verse (the BPHS "chapter" numbers
--   are PAGE numbers in the served corpus, so a chapter number is not checkable here; see WAVE_PLACEHOLDER_
--   DISPOSITIONS), so it never writes 'sourced'. 'sourced' is for the writers, after a verse-level check. NULL is
--   not a PASS of Ldgr/Carr either. Left NULL on purpose and reported, not decided here:
--     * brahma_remedy_corpus: 3 rows 'Tajaka Neelakanthi, classical tradition, public domain' and 1 row
--       'Tulsidas, Hanuman Chalisa (16th c.); classical tradition' name a text (no locator) - a text-level
--       attribution is not the bare token, Track A rules on it. The 80 in the INDEX is stale: live token-exact
--       count is 101 (+4 named-text rows = 105 containing "classical tradition").
--     * bg_transit_rules: 7 double-gochara rows (ids 133-139, 'Phaladeepika ch.26 §double-gochara ...') cite a
--       section that exists in none of the 16 texts; 2 of them also cite 'BPHS ch.29' (lower case, not the 19).
--       WAVE_PLACEHOLDER_DISPOSITIONS proposes unsourced/refuted for them; CF-11 (SS-decided) names only 19 + 6, so
--       they are NOT classified here. 5 'Phaladeepika Ch.26' chapter-only rows and the 39 page-anchored rows too.
--     * Ketu 12th (favourable) is one of the 19 'refuted' rows; the corpus text contradicts its content as well
--       (acharya check); its row content is NOT changed here.
--
-- DURABILITY WARNING (found by reading the writers; the other half of TI-L0-09 is the writer change)
--   The doshas writer (brahmagyan/l0_doshas.py:1942-1944) and the yogas writer (l0_yogas.py:2244-2249) DELETE the
--   whole catalogue and re-INSERT it; they do not write attribution_state. A rebuild of bg_doshas or bg_yogas
--   therefore RESETS the new column to NULL (honest: unclassified) until the writers derive the state. The remedy
--   writer (ON CONFLICT (remedy_id) DO UPDATE with an explicit column list) and the transit writer (ON CONFLICT ...
--   DO UPDATE, stale-id deletes only) leave the column alone. The writer change edits brahmagyan/l0_*.py, which
--   stales nirmana-writer-digests.json (a #2984 file), so it cannot be a green PR yet. Do NOT rebuild bg_doshas /
--   bg_yogas expecting the state to survive.
--
-- SERVING AND FRESHNESS EFFECT AT APPLY
--   * Touches NO asset_registry column and no asset_freshness row: nirmana_registry_receipt_invalidation does NOT
--     fire. NO asset goes stale. The integrity_check_sql of all four assets hash EXPLICIT column lists that do not
--     include the new column (dosha digest cfb21a53..., yoga digest 4d4cd60f..., remedy summary, transit digests
--     1dbdd265... / e2dafc84...), so they keep reading true; verified on the production mirror.
--   * Served tools: none selects * from these tables (grep of platform/src/lib/retrieval/registry/layers/
--     L0_brahmagyan), so no response shape changes until a reader is taught to select the column.
--   * ALTER TABLE takes ACCESS EXCLUSIVE on each of the four small tables (79/233/341/76 rows) for an instant;
--     SET LOCAL lock_timeout = 5s fails fast. The backfill is five UPDATE statements touching 180 rows.
--
-- GUARDS (every one raises rather than skip; an empty table is skipped with a NOTICE = a fresh bootstrap)
--   Per class: the number of rows matching the token predicate and md5 of their natural keys (as read from
--   production on 2026-10-03) must equal the audited values, else RAISE (re-audit; the rule is token-exact, so a
--   changed set means the audit is stale). Only rows whose attribution_state IS NULL are written, so a state set
--   by anything else is never overwritten; a matching row that ends in a different state fails the post-check.
--   Audited: dosha 53 / 358100cf4f432c341870c93c42a27c09 ; yoga 1 / c59e915521bf783b2cf5b49ae8ce3df0 ;
--   remedy 101 / 018817ba07867f71b90461264e7b6a6d ; transit refuted 19 / b71b9ac6de1c1eda2ae5d96ac6105037 ;
--   transit unsourced 6 / 1656f780bb5ec60b40ad12a77444fd39. People-entered data: none (all four are L0 reference
--   seeds, no LEL / native-entered rows).
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as amjis_app, the OWNER of all four tables (ALTER TABLE ADD COLUMN /
-- ADD CONSTRAINT / COMMENT need ownership, not CREATE on schema public) and the table-level SELECT grants already
-- cover the new column. The only CREATE is CREATE TEMP TABLE ... ON COMMIT DROP (TEMP on the database via PUBLIC,
-- pg_temp, not schema public; the 1219/1226 precedent). No function/trigger/index/permanent table, no GRANT.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS; constraints guarded by a catalog lookup; backfill writes NULL rows only.
--
-- NOT DONE HERE
--   * The writer half of TI-L0-09 (derive sourced/unsourced/refuted in l0_doshas/l0_yogas/l0_remedy_corpus/
--     l0_transit) and the rebuild of the four assets; both wait for #2984 (writer-digest inventory) and SS.
--   * Any 'sourced' state; any citation change; TI-L0-10 re-sourcing; the 7 double-gochara rows; the named-text
--     remedy rows; bg_ontology / bg_reference / bg_muhurta_lattice / bg_vastu_directions placeholder families.
--   * The inspector reading the column (Ldgr/Carr reading of 'unsourced'/'refuted': Track E, CF-07).
--
-- ROLLBACK (ops reference, not executed): ALTER TABLE <each of the four> DROP COLUMN attribution_state;
--   a new reviewed migration against the then-current state; never edit this file after apply.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT 'dosha', attribution_state, count(*) FROM brahma_dosha_catalog GROUP BY 2   -- unsourced 53, NULL 26
--   UNION ALL SELECT 'yoga', attribution_state, count(*) FROM brahma_yoga_catalog GROUP BY 2            -- unsourced 1, NULL 232
--   UNION ALL SELECT 'remedy', attribution_state, count(*) FROM brahma_remedy_corpus GROUP BY 2         -- unsourced 101, NULL 240
--   UNION ALL SELECT 'transit', attribution_state, count(*) FROM bg_transit_rules GROUP BY 2;           -- refuted 19, unsourced 6, NULL 51
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

-- 1. the column, its CHECK and its comment on the four tables
DO $m1268a$
DECLARE
    t text;
    cname text;
BEGIN
    FOREACH t IN ARRAY ARRAY['brahma_dosha_catalog', 'brahma_yoga_catalog', 'brahma_remedy_corpus', 'bg_transit_rules'] LOOP
        IF to_regclass('public.' || t) IS NULL THEN
            RAISE EXCEPTION '1268: table % does not exist', t;
        END IF;
        EXECUTE format('ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS attribution_state text', t);
        cname := t || '_attribution_state_check';
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                        WHERE conrelid = ('public.' || t)::regclass AND conname = cname) THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I CHECK (attribution_state IS NULL OR attribution_state IN (''sourced'', ''unsourced'', ''refuted''))', t, cname);
        END IF;
        EXECUTE format('COMMENT ON COLUMN public.%I.attribution_state IS %L', t,
            'Attribution state of the row''s citation (SS Q3, TI-L0-09). unsourced = the citation is a placeholder token / states no source; refuted = the cited source was checked and does not say it; sourced = a verse-level source was verified (written by the writers only, never by migration 1268). NULL = not classified. Neither unsourced, refuted nor NULL is a PASS of Ldgr/Carr. No citation is changed by this column.');
    END LOOP;
END
$m1268a$;

-- 2. the token-exact backfill, guarded per class
CREATE TEMP TABLE _m1268_classes (
    label        text PRIMARY KEY,
    tbl          text NOT NULL,
    predicate    text NOT NULL,
    key_expr     text NOT NULL,
    order_expr   text NOT NULL,
    want_n       integer NOT NULL,
    want_md5     text NOT NULL,
    want_state   text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1268_classes (label, tbl, predicate, key_expr, order_expr, want_n, want_md5, want_state) VALUES
  ('dosha_placeholder',   'brahma_dosha_catalog', $p$classical_citations = '[{"text_id": "classical_tradition"}]'::jsonb$p$,
   'canonical_id', 'canonical_id COLLATE "C"', 53, '358100cf4f432c341870c93c42a27c09', 'unsourced'),
  ('yoga_placeholder',    'brahma_yoga_catalog',  $p$classical_citations = '[{"text_id": "classical_tradition"}]'::jsonb$p$,
   'canonical_id', 'canonical_id COLLATE "C"', 1, 'c59e915521bf783b2cf5b49ae8ce3df0', 'unsourced'),
  ('remedy_placeholder',  'brahma_remedy_corpus', $p$source_citation = 'classical tradition (Jyotish)'$p$,
   'remedy_id', 'remedy_id COLLATE "C"', 101, '018817ba07867f71b90461264e7b6a6d', 'unsourced'),
  ('transit_refuted',     'bg_transit_rules',     $p$classical_citation LIKE 'BPHS Ch.29 (Gochara Phala%'$p$,
   $p$graha || '/' || rule_type || '/' || primary_house::text$p$, $p$graha COLLATE "C", rule_type COLLATE "C", primary_house$p$,
   19, 'b71b9ac6de1c1eda2ae5d96ac6105037', 'refuted'),
  ('transit_unsourced',   'bg_transit_rules',     $p$classical_citation LIKE 'UNSOURCED %'$p$,
   $p$graha || '/' || rule_type || '/' || primary_house::text$p$, $p$graha COLLATE "C", rule_type COLLATE "C", primary_house$p$,
   6, '1656f780bb5ec60b40ad12a77444fd39', 'unsourced');

DO $m1268b$
DECLARE
    c       record;
    v_n     bigint;
    v_md5   text;
    v_rows  bigint;
    v_bad   bigint;
BEGIN
    FOR c IN SELECT * FROM _m1268_classes ORDER BY label LOOP
        EXECUTE format('SELECT count(*), md5(string_agg(%s, '','' ORDER BY %s)) FROM public.%I WHERE %s',
                       c.key_expr, c.order_expr, c.tbl, c.predicate)
           INTO v_n, v_md5;
        IF v_n = 0 THEN
            RAISE NOTICE '1268: class % matches no row in % (fresh bootstrap?); skipped', c.label, c.tbl;
            CONTINUE;
        END IF;
        IF v_n <> c.want_n OR v_md5 IS DISTINCT FROM c.want_md5 THEN
            RAISE EXCEPTION '1268: class % has drifted from the audited rows (% rows md5 %, audited % rows md5 %); refusing to classify',
                c.label, v_n, v_md5, c.want_n, c.want_md5;
        END IF;

        EXECUTE format('UPDATE public.%I SET attribution_state = %L WHERE (%s) AND attribution_state IS NULL',
                       c.tbl, c.want_state, c.predicate);
        GET DIAGNOSTICS v_rows = ROW_COUNT;
        RAISE NOTICE '1268: class % (%): % rows classified, % already classified', c.label, c.want_state, v_rows, v_n - v_rows;

        -- post-check: every matching row now carries exactly the audited state (a different non-NULL state is drift)
        EXECUTE format('SELECT count(*) FROM public.%I WHERE (%s) AND attribution_state IS DISTINCT FROM %L',
                       c.tbl, c.predicate, c.want_state)
           INTO v_bad;
        IF v_bad <> 0 THEN
            RAISE EXCEPTION '1268: class % has % row(s) whose attribution_state is not %', c.label, v_bad, c.want_state;
        END IF;
    END LOOP;

    -- global post-check: the column and its CHECK exist on all four tables; the backfill wrote no other state
    IF (SELECT count(*) FROM information_schema.columns
         WHERE table_schema = 'public' AND column_name = 'attribution_state' AND data_type = 'text' AND is_nullable = 'YES'
           AND table_name IN ('brahma_dosha_catalog', 'brahma_yoga_catalog', 'brahma_remedy_corpus', 'bg_transit_rules')) <> 4 THEN
        RAISE EXCEPTION '1268: attribution_state is not a nullable text column on all four tables';
    END IF;
    IF (SELECT count(*) FROM pg_constraint
         WHERE conname IN ('brahma_dosha_catalog_attribution_state_check', 'brahma_yoga_catalog_attribution_state_check',
                           'brahma_remedy_corpus_attribution_state_check', 'bg_transit_rules_attribution_state_check')) <> 4 THEN
        RAISE EXCEPTION '1268: the attribution_state CHECK is not present on all four tables';
    END IF;
END
$m1268b$;
