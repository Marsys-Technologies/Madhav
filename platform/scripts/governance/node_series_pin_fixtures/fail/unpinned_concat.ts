// FAIL fixture: a '+'-joined string read of ephemeris_daily with no pin.
export const SQL = 'SELECT date, tropical_longitude ' +
  'FROM public.ephemeris_daily ' +
  "WHERE body = $1 ORDER BY date"
