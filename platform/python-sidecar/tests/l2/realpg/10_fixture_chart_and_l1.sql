-- run as superuser: the synthetic chart row (fixture values, no birth data of any real person)
INSERT INTO public.charts(id,name,birth_date,birth_time,birth_place,birth_lat,birth_lng,timezone_id,house_system,native_id,role,chart_type)
VALUES ('11111111-1111-4111-8111-111111111111','fixture','2000-01-01','12:00','fixture',20,85,'Asia/Kolkata','sripathi','fixture','fixture','natal') ON CONFLICT DO NOTHING;
