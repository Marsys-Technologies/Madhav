-- MODEL of migration 1255 (PR #2962: builder reference-table SELECT grants), applied PER DISPOSABLE DATABASE by the `db` fixture, NOT in the template: production
-- does not have it yet (read live as suvarna_reader 2026-10-02: has_table_privilege('data_plane_l1_owner','public.brahma_yoga_catalog','SELECT') = false), so
-- the replay template stays production-faithful and the executor's STEP 0 precondition is proved by REVOKE-ing these grants (tests/test_prereq_1255.py).
-- Six of the seven reference tables do not exist in the replay (only bg_shashtiamsha_deities does): minimal stand-ins, owned by amjis_app like production's.
CREATE TABLE IF NOT EXISTS public.yoga_family_members (yoga_canonical_id text, family_id text);
CREATE TABLE IF NOT EXISTS public.reference_nakshatra (id integer);
CREATE TABLE IF NOT EXISTS public.reference_nakshatra_pada (id integer);
CREATE TABLE IF NOT EXISTS public.bg_graha_naisargika_friendship (id integer);
CREATE TABLE IF NOT EXISTS public.bg_motion_state_thresholds (id integer);
CREATE TABLE IF NOT EXISTS public.brahma_vichara_constants (id integer);
ALTER TABLE public.yoga_family_members OWNER TO amjis_app;
ALTER TABLE public.reference_nakshatra OWNER TO amjis_app;
ALTER TABLE public.reference_nakshatra_pada OWNER TO amjis_app;
ALTER TABLE public.bg_graha_naisargika_friendship OWNER TO amjis_app;
ALTER TABLE public.bg_motion_state_thresholds OWNER TO amjis_app;
ALTER TABLE public.brahma_vichara_constants OWNER TO amjis_app;
GRANT SELECT ON public.yoga_family_members, public.reference_nakshatra, public.reference_nakshatra_pada, public.bg_shashtiamsha_deities,
  public.bg_graha_naisargika_friendship, public.bg_motion_state_thresholds, public.brahma_vichara_constants TO data_plane_builder;
GRANT SELECT ON public.brahma_yoga_catalog TO data_plane_l1_owner;
