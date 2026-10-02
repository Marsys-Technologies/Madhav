-- PENDING (Stream B owns the migration): the builder privileges the registered '5.0' writer's REPLACE and FINALISE paths
-- need on the record tables, which no applied or reviewed grant migration gives it (1216 grants SELECT, INSERT only and
-- says "replacement is impossible by design"; the writer delete-then-inserts a class/grain per AM-3 and finalises
-- results/admission states). Derived by running the complete builder flow (twice, so the rebuild path fires) as the
-- restricted builder on the faithful mirror and recording every statement against has_table_privilege — see the
-- R9-4 report. Column-level UPDATE: only the columns the writer sets (the 1155 write guard bounds the rest).
GRANT DELETE ON public.ka_gochara_relationship_record, public.ka_gochara_contact TO data_plane_builder;
GRANT UPDATE (admission_state) ON public.ka_gochara_relationship_record TO data_plane_builder;
GRANT UPDATE (result) ON public.ka_gochara_record_prerequisite TO data_plane_builder;
