
CREATE TABLE IF NOT EXISTS weather_avg (
    id  SERIAL PRIMARY KEY,
    ides bigint,
    idmun bigint,
    nes text,
    nmun text,
    avg_temp double precision,
    avg_prec double precision,
    inserted_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS weather_data_mun (
    id  SERIAL PRIMARY KEY,
    ides bigint,
    idmun bigint,
    value bigint,
    nes text,
    nmun text,
    avg_temp double precision,
    avg_prec double precision,
    inserted_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS weather_current (
    id  SERIAL PRIMARY KEY,
    ides bigint,
    idmun bigint,
    value bigint,
    nes text,
    nmun text,
    avg_temp double precision,
    avg_prec double precision,
    inserted_at timestamp with time zone
);