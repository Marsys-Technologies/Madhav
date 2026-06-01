-- G6: Sankranti table (Sun sign-entry timestamps per ayanamsha)
CREATE TABLE IF NOT EXISTS sankranti_table (
    id BIGSERIAL PRIMARY KEY,
    ayanamsha_id TEXT NOT NULL REFERENCES ayanamsha_registry(ayanamsha_id),
    sign_number INTEGER NOT NULL CHECK (sign_number BETWEEN 1 AND 12),
    sign_name TEXT NOT NULL,
    entry_jd DOUBLE PRECISION NOT NULL,
    entry_date DATE NOT NULL,
    entry_utc TIMESTAMPTZ NOT NULL,
    year INTEGER NOT NULL,
    UNIQUE (ayanamsha_id, sign_number, year)
);

CREATE INDEX IF NOT EXISTS sankranti_ayanamsha_year_idx ON sankranti_table (ayanamsha_id, year);
CREATE INDEX IF NOT EXISTS sankranti_sign_idx ON sankranti_table (sign_name);

-- G21: Saturn sign-changes table (Saturn sign ingresses per ayanamsha)
CREATE TABLE IF NOT EXISTS saturn_sign_changes (
    id BIGSERIAL PRIMARY KEY,
    ayanamsha_id TEXT NOT NULL REFERENCES ayanamsha_registry(ayanamsha_id),
    from_sign_number INTEGER CHECK (from_sign_number BETWEEN 1 AND 12),
    from_sign_name TEXT,
    to_sign_number INTEGER NOT NULL CHECK (to_sign_number BETWEEN 1 AND 12),
    to_sign_name TEXT NOT NULL,
    ingress_jd DOUBLE PRECISION NOT NULL,
    ingress_date DATE NOT NULL,
    ingress_utc TIMESTAMPTZ NOT NULL,
    is_retrograde_ingress BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (ayanamsha_id, ingress_jd)
);

CREATE INDEX IF NOT EXISTS saturn_sign_changes_ayanamsha_idx ON saturn_sign_changes (ayanamsha_id);
CREATE INDEX IF NOT EXISTS saturn_sign_changes_date_idx ON saturn_sign_changes (ingress_date);
